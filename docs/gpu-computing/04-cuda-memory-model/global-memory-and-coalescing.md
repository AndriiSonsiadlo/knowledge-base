---
id: global-memory-and-coalescing
title: Global Memory and Coalescing
sidebar_label: Global Memory & Coalescing
sidebar_position: 2
tags: [gpu, cuda, memory, coalescing]
---

# Global Memory and Coalescing

[Thread Indexing](../03-cuda-programming-model/thread-indexing.md) establishes that the fastest-varying array index should track `threadIdx.x`, so that adjacent threads in a warp touch adjacent addresses. This page is the mechanism that makes that rule matter: how the hardware actually turns a warp's 32 addresses into memory transactions, and why the difference between "adjacent" and "scattered" can be an 8x difference in delivered bandwidth for the exact same amount of useful data.

## Transactions and sectors

[Cache Hierarchy](../02-gpu-hardware-architecture/cache-hierarchy.md) already lays out the mechanical fact this page builds on: global memory is fetched in **32-byte sectors**, four of which make up a 128-byte line, and a memory transaction only pulls in the sectors a warp's addresses actually touch. A warp issues one memory instruction on behalf of all 32 of its threads at once, and the hardware coalesces those 32 addresses into the minimum number of sector fetches that cover them.

The best case: 32 threads accessing 32 consecutive 4-byte values (a `float` array with `data[i]`, `i` running one-per-thread) span exactly 128 bytes, which is exactly four 32-byte sectors — one fully-utilized transaction, 128 bytes fetched for 128 bytes used.

The worst case that still touches every element: a stride of 32 floats between threads means each thread lands in a different 128-byte line entirely, and each of those 32 separate transactions only has one thread's 4 bytes of useful data in it, but the hardware still fetches a whole 32-byte sector per access. That's 32 sectors — 1024 bytes moved — to deliver the same 128 bytes of useful data a coalesced access delivers in four sectors. **8x waste**, exactly the ratio [Cache Hierarchy](../02-gpu-hardware-architecture/cache-hierarchy.md) states for the single-sector-per-line case, scaled up across the whole warp.

## What coalescing means

**Coalescing** is the property that a warp's 32 addresses fall into the fewest possible sectors — see the [glossary entry](../00-overview/glossary.md#coalescing) for the exact wording this section uses throughout. In practice this almost always means: consecutive threads (by `threadIdx.x`) read or write consecutive addresses, with no gaps and no reordering. The kernel below is the coalesced baseline:

```cpp showLineNumbers
__global__ void coalesced_copy(const float* in, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        out[i] = in[i];
    }
}
```

## Strided access

Introducing a stride between threads' addresses is the single most common way a ported or naively-transposed kernel loses most of its bandwidth:

```cpp showLineNumbers
__global__ void strided_copy(const float* in, float* out, int n, int stride) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int idx = i * stride;
    if (idx < n) {
        out[idx] = in[idx];
    }
}
```

With `stride == 1` this is the coalesced case above. With `stride == 32`, each thread's 4-byte access lands in its own sector, and the warp touches 32 sectors to move 128 useful bytes — the 8x-waste arithmetic worked out above.

## Scattered access

A stride is a regular pattern; scattered access — indices computed from a hash, a gather index, or another data-dependent lookup — is the irregular version of the same problem:

```cpp showLineNumbers
__global__ void gather_copy(const float* in, float* out, const int* idx, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        out[i] = in[idx[i]];  // idx[i] can land anywhere
    }
}
```

`out[i]` here is still coalesced (`i` is contiguous), but the read from `in[idx[i]]` can touch up to 32 distinct sectors per warp in the worst case, with no way to fix it in the access pattern alone — the fix, when there is one, is usually to sort or bucket the indices ahead of time so nearby threads read nearby addresses.

## Array of structs versus struct of arrays

The same coalescing rule explains why array-of-structs (AoS) layouts are frequently slower than struct-of-arrays (SoA) for GPU kernels that only touch one or two fields per element.

```cpp
struct ParticleAoS {
    float x, y, z, mass;
};

struct ParticlesSoA {
    float* x;
    float* y;
    float* z;
    float* mass;
};
```

```cpp showLineNumbers
// AoS: a warp updating only x scatters across 16-byte strides
__global__ void update_x_aos(ParticleAoS* p, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        p[i].x += 1.0f;  // consecutive threads are 16 bytes apart
    }
}

// SoA: a warp updating only x is a fully coalesced contiguous access
__global__ void update_x_soa(ParticlesSoA p, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        p.x[i] += 1.0f;  // consecutive threads are 4 bytes apart
    }
}
```

In `update_x_aos`, consecutive threads' `x` fields are 16 bytes apart (the size of `ParticleAoS`), so a warp's 32 accesses to `x` alone span 512 bytes and touch far more sectors than the 128 bytes of `x` data actually needed. `update_x_soa` puts every thread's `x` value contiguously, so the same warp coalesces into the minimum sector count. AoS still wins when a kernel touches *all* fields of an element together per thread; SoA wins whenever different threads or different kernels touch different fields independently.

| Pattern | Sectors per warp | Useful bytes | Efficiency |
|---|---|---|---|
| Coalesced (`stride == 1`) | 4 | 128 | 100% |
| Strided (`stride == 32`) | 32 | 128 | 12.5% |
| AoS, single-field update | up to 32 | 128 | as low as 12.5% |
| SoA, single-field update | 4 | 128 | 100% |

## Vectorized loads

When each thread needs multiple consecutive elements anyway, issuing one wide load instead of several narrow ones cuts instruction count and can improve achieved bandwidth:

```cpp showLineNumbers
__global__ void vectorized_copy(const float4* in, float4* out, int n4) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n4) {
        out[i] = in[i];  // one 16-byte transaction per thread
    }
}
```

`` `float4` `` loads require the pointer to be 16-byte aligned. `cudaMalloc` guarantees 256-byte alignment for the base pointer it returns, but an *offset* into that allocation — for example casting `base + 3` to `` `float4*` `` — does not necessarily preserve 16-byte alignment, and a misaligned vector load is either slower or outright illegal depending on the architecture. Check alignment at the point of the cast, not just at the allocation.

:::tip[Check the sector-fetch metric directly]
Nsight Compute's `l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum` metric reports sectors fetched per global load request — comparing it against the theoretical minimum (four sectors per fully-coalesced warp of 4-byte accesses) tells you directly how much of your bandwidth a given kernel is wasting. See [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).
:::

## See also

- [Memory Spaces Overview](./memory-spaces-overview.md) — where global memory sits among the other five spaces.
- [Shared Memory Bank Conflicts](./bank-conflicts.md) — the analogous, but different, access-pattern rule for on-chip shared memory.
- [Memory Access Optimization](../07-kernel-optimization/memory-access-optimization.md) — applying coalescing analysis to a real kernel.
- [Matrix Transpose](../13-applied-kernels-and-patterns/matrix-transpose.md) — the canonical kernel where naive global-memory access is uncoalesced on one side.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
