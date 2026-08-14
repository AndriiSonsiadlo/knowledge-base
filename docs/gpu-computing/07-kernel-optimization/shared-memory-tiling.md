---
id: shared-memory-tiling
title: Shared Memory Tiling
sidebar_label: Shared Memory Tiling
sidebar_position: 4
tags: [gpu, cuda, optimization, tiling]
---

# Shared Memory Tiling

[Memory Access Optimization](./memory-access-optimization.md) stops once accesses are coalesced and vectorized, because coalescing only fixes how efficiently a kernel fetches the bytes it asks for — it does nothing about a kernel that asks DRAM for the same bytes over and over. Shared-memory tiling attacks that second problem directly: load each piece of data into on-chip shared memory once, then let every thread that needs it read it from there instead of going back to DRAM. This page derives why that reuse matters arithmetically and builds the tiled kernel that makes it concrete.

## The reuse argument

Arithmetic intensity — FLOPs per byte moved — is what decides whether a kernel is memory-bound, per [Memory-Bound vs Compute-Bound](../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md). A naive SGEMM (`C = A * B` for `N x N` matrices, no reuse) computes one output element as a dot product of length `N`: `N` multiply-adds, so `2N` FLOPs, against `2N` elements read from global memory (`N` from a row of `A`, `N` from a column of `B`). At 4 bytes per FP32 element, that's `2N` elements × 4 bytes = `8N` bytes moved for `2N` FLOPs:

```text
intensity = 2N FLOPs / 8N bytes = 0.25 FLOP/byte
```

0.25 FLOP/byte is far below the ridge point of any modern GPU, which is exactly why naive SGEMM is memory-bound rather than compute-bound. A `TILE x TILE` tiled version changes the picture by loading each element into shared memory once and reusing it `TILE` times from there before it's evicted — every element read from DRAM now backs `TILE` multiply-adds instead of one, so intensity scales by the same factor:

```text
tiled intensity = 0.25 FLOP/byte x TILE = 0.25 x 32 = 8 FLOP/byte  (TILE = 32)
```

That 8 FLOP/byte figure is the same well-tiled-SGEMM number [Memory-Bound vs Compute-Bound](../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md) cites as still short of an H100's roofline ridge point — tiling is a large, necessary improvement over the naive kernel, not a complete escape from being memory-bound at FP32.

## The naive kernel

The unreused baseline this page improves on:

```cpp showLineNumbers
__global__ void sgemmNaive(int N, const float* A, const float* B, float* C) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    float acc = 0.0f;
    for (int k = 0; k < N; ++k) {
        acc += A[row * N + k] * B[k * N + col];   // each element re-read from DRAM by every row/column that needs it
    }
    C[row * N + col] = acc;
}
```

Every thread computing an output element re-reads an entire row of `A` and an entire column of `B` from global memory, and neighboring threads in the same block re-read most of that same data independently — nothing is shared on-chip.

## The tiled kernel

Loading a `TILE x TILE` block of `A` and `B` into shared memory once per tile, then having every thread in the block reuse those tiles for `TILE` multiply-adds, is the fix:

```cpp showLineNumbers title="sgemm_tiled.cu"
#define TILE 32

__global__ void sgemmTiled(int N, const float* __restrict__ A,
                           const float* __restrict__ B, float* __restrict__ C) {
    __shared__ float As[TILE][TILE + 1];   // +1 removes the bank conflict
    __shared__ float Bs[TILE][TILE + 1];

    const int row = blockIdx.y * TILE + threadIdx.y;
    const int col = blockIdx.x * TILE + threadIdx.x;
    float acc = 0.0f;

    for (int t = 0; t < N / TILE; ++t) {
        As[threadIdx.y][threadIdx.x] = A[row * N + t * TILE + threadIdx.x];
        Bs[threadIdx.y][threadIdx.x] = B[(t * TILE + threadIdx.y) * N + col];
        __syncthreads();

        for (int k = 0; k < TILE; ++k)
            acc += As[threadIdx.y][k] * Bs[k][threadIdx.x];
        __syncthreads();
    }
    C[row * N + col] = acc;
}
```

This assumes `N` is evenly divisible by `TILE`, so the tile loop covers the whole matrix with no partial final tile — a general kernel needs boundary handling for the remainder, which [Matrix Multiply](../13-applied-kernels-and-patterns/matrix-multiply.md) adds along with register tiling, building on this exact kernel name and tile size. The first `__syncthreads()` ensures the whole tile has finished loading before any thread starts reading it back for the multiply-add; the second ensures every thread is done reading the current tile before the next iteration overwrites it.

## Choosing a tile size

`TILE` trades reuse against shared-memory pressure and blocks/SM, not a free parameter to maximize:

| Tile size | Reuse per element | Shared memory / block (2 tiles, FP32) | Effect on occupancy |
|---|---|---|---|
| 16 | 16x | 16 x 16 x 2 x 4 bytes x 2 = 4 KB (plus padding) | Lower reuse, but leaves more shared-memory budget for other resident blocks |
| 32 | 32x | 32 x 33 x 2 x 4 bytes x 2 ≈ 16.9 KB | Higher reuse, but a larger per-block shared-memory footprint can cut blocks/SM, per the shared-memory limiter in [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) |

A larger tile raises arithmetic intensity linearly but consumes shared memory quadratically (`TILE x TILE` elements per matrix), so past some point a bigger tile actually lowers occupancy enough to hurt overall throughput even though intensity keeps climbing — the tile size that maximizes measured throughput is rarely the largest one that fits.

:::note[Why `TILE + 1`]
`As` and `Bs` are declared `[TILE][TILE + 1]` rather than `[TILE][TILE]`. The inner loop above reads `As[threadIdx.y][k]` and `Bs[k][threadIdx.x]` — a column-wise read of `Bs` across the warp — which, on an unpadded `[TILE][TILE]` layout with `TILE` a multiple of 32, lands every thread in the same shared-memory bank and serializes the read. Padding each row by one extra word breaks that alignment and spreads the accesses across distinct banks at the cost of one wasted word per row. See [Shared Memory Bank Conflicts](../04-cuda-memory-model/bank-conflicts.md) for the full derivation of why `+1` specifically fixes it.
:::

## What tiling does not fix

Tiling only helps a kernel that has reuse to exploit in the first place. A kernel like SAXPY (`y = a*x + y`), where every element is read once and never revisited, has nothing to tile — there's no second access to serve from shared memory, so moving the data through shared memory first would only add overhead. And even for a kernel that does have reuse, the tiled kernel above still has the memory system idle during the compute phase of every tile: the two `__syncthreads()` calls per iteration force the whole block to wait for the slowest thread at both the load boundary and the compute boundary, and no `A`/`B` data is being fetched from DRAM while `acc` is being accumulated inside the `k` loop. The next step is overlapping that idle DRAM time with compute from a different tile — see [Software Pipelining](./software-pipelining.md).

## See also

- [Memory Access Optimization](./memory-access-optimization.md) — the coalescing and vectorization ceiling this page's reuse argument builds on.
- [Software Pipelining](./software-pipelining.md) — overlapping the load and compute phases this kernel still serializes with `__syncthreads()`.
- [Shared Memory Bank Conflicts](../04-cuda-memory-model/bank-conflicts.md) — the full derivation behind the `TILE + 1` padding used above.
- [Matrix Multiply](../13-applied-kernels-and-patterns/matrix-multiply.md) — extends `sgemmTiled` with register tiling and general-`N` boundary handling.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
