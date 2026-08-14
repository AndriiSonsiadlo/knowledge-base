---
id: programming-tensor-cores
title: Programming Tensor Cores
sidebar_label: Programming Tensor Cores
sidebar_position: 8
tags: [gpu, cuda, optimization, tensor-cores]
---

# Programming Tensor Cores

[Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md) laid out what tensor cores are and what makes a kernel eligible to reach them; this page is about actually writing code that does — the `wmma` warp-level API, the two facts about it that trip almost everyone up the first time, and why the code you write here is closer to a teaching exercise than to what a shipped GEMM looks like.

:::note[Hardware and precision requirements]
Which precisions are available at all depends on the generation running the kernel — see [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md) for the per-generation precision table rather than having it repeated here.
:::

## What you are programming

Ordinary CUDA C++ addresses one thread at a time; `wmma` addresses one *warp* at a time, cooperating on one small matrix tile. There is no per-thread tensor-core operation — the primitive the hardware exposes is a warp-wide instruction, and the `wmma` API's job is to give that instruction a C++-shaped interface: load a tile into a warp-owned fragment, multiply-accumulate two fragments into a third, and store the result back out.

## The `wmma` API

```cpp showLineNumbers
#include <mma.h>
using namespace nvcuda;

// One 16x16x16 FP16 tile product, accumulated in FP32.
__global__ void wmmaTile(const half* A, const half* B, float* C, int N) {
    wmma::fragment<wmma::matrix_a, 16, 16, 16, half, wmma::row_major> aFrag;
    wmma::fragment<wmma::matrix_b, 16, 16, 16, half, wmma::col_major> bFrag;
    wmma::fragment<wmma::accumulator, 16, 16, 16, float> cFrag;

    wmma::fill_fragment(cFrag, 0.0f);
    wmma::load_matrix_sync(aFrag, A, N);
    wmma::load_matrix_sync(bFrag, B, N);
    wmma::mma_sync(cFrag, aFrag, bFrag, cFrag);
    wmma::store_matrix_sync(C, cFrag, N, wmma::mem_row_major);
}
```

`fill_fragment` zero-initializes the accumulator, the two `load_matrix_sync` calls bring a 16x16 tile of `A` and `B` from global memory into the `A`/`B` fragments (with a leading dimension of `N`, the source matrix's row stride), `mma_sync` performs the tile's multiply-accumulate in hardware, and `store_matrix_sync` writes the accumulator fragment back out. This is the exact tile shape and fragment set [Matrix Multiply with Tensor Cores](../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md) builds a full, blocked GEMM kernel from.

## Fragment layouts

The two facts about this API that catch people the first time:

- A `wmma::fragment` is **warp-owned**, not thread-owned. All 32 threads of the warp cooperate to hold one tile's worth of elements across their combined register state, and the mapping from a specific matrix element to a specific lane and register is deliberately unspecified — it can differ by architecture and instruction shape. Code must not assume which lane holds which element; anything that needs to touch individual elements has to go through the fragment API (`load_matrix_sync`, `store_matrix_sync`, or the `.x[i]` accessor for elementwise fragment ops), never a hand-derived index.
- Every `wmma` call — `load_matrix_sync`, `mma_sync`, `store_matrix_sync` — is **warp-collective**: all 32 lanes must execute it together, with the same arguments, for the result to be defined. That means a `wmma` call must never sit inside code where lanes of the warp have diverged — the same divergence cost model from [Reducing Divergence](./reducing-divergence.md) applies, except here divergence doesn't just cost more, it makes the operation's result undefined for whichever lanes fell out of the collective call.

## Precision and accumulators

The default and most common configuration is low-precision inputs — FP16 or BF16 — multiplied with an FP32 accumulator, exactly as `wmmaTile` above declares it; this is what keeps accumulated error bounded across a long reduction dimension even though the inputs themselves are narrow. TF32 is a drop-in alternative for code that's already using FP32 source types: it gives FP32's range with a reduced mantissa, and reaching it is a matter of the math mode rather than a source-level type change. FP8 (Ada Lovelace and Hopper) and the FP4/FP6 microscaled formats (Blackwell) go further still, but they need explicit scaling factors alongside the data to keep the reduced range usable — precision this low isn't a transparent drop-in the way TF32 is.

## `mma` PTX intrinsics

`wmma` is a C++ convenience layer sitting on top of a lower level: the `mma` PTX instruction family, and on Hopper (CC 9.0+) the warp-group-wide `wgmma` instructions. That lower layer exposes tile shapes and asynchronous execution that `wmma` cannot reach — `wgmma` in particular operates across a warp group rather than a single warp and can be fed directly from shared memory via the Tensor Memory Accelerator, overlapping the load with the multiply-accumulate in a way the synchronous `wmma` calls above don't. This is exactly why library kernels (CUTLASS, cuBLAS) reach for `mma`/`wgmma` directly rather than stopping at `wmma` — the extra shapes and asynchrony are where the additional performance comes from, at the cost of considerably more code to manage it correctly.

## Why CUTLASS usually wins

:::tip[Write one to learn it, ship a library for production]
A hand-written `wmma` GEMM, tiled and tuned by hand, typically reaches only a fraction of what cuBLAS achieves on the same hardware — cuBLAS and CUTLASS encode tile-size search, pipelining, and instruction-shape choices across generations that take real engineering time to reproduce by hand. Writing a `wmma` kernel is worth doing to understand how the machine actually works; shipping one to production is rarely worth it once [CUTLASS](../08-libraries-and-ecosystem/cutlass.md) or cuBLAS already covers the shape you need.
:::

## See also

- [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md) — the hardware model and per-generation precision table this page programs against.
- [Software Pipelining](./software-pipelining.md) — overlapping the loads `wmma` needs with the compute of the previous tile.
- [CUTLASS](../08-libraries-and-ecosystem/cutlass.md) — the template library that generates tuned tensor-core kernels from these same primitives.
- [Matrix Multiply with Tensor Cores](../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md) — the full blocked GEMM built from the `wmmaTile` fragment example above.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
