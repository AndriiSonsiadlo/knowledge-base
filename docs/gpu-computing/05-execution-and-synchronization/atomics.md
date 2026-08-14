---
id: atomics
title: Atomic Operations
sidebar_label: Atomics
sidebar_position: 6
tags: [gpu, cuda, atomics, contention]
---

# Atomic Operations

Some updates can't wait for a barrier — a histogram bin, a running total, a lock-free counter — because the threads touching the same location aren't at a point where `__syncthreads()` or a group `sync()` even applies; they need the read-modify-write itself to be indivisible. Atomics provide that: a hardware-guaranteed sequence of read, modify, and write on a single memory location that no other thread's atomic on the same location can interleave with. What atomics don't provide is speed for free — how many threads target the *same* address, not how many threads issue atomics in total, is what determines whether that guarantee is nearly free or a serialization bottleneck.

## What atomics guarantee

An atomic operation on a given address completes as an indivisible unit with respect to every other atomic operation on that same address: no other thread's atomic read-modify-write on that address can be interleaved partway through. This is a guarantee about that one address, not about memory ordering more broadly — an atomic doesn't imply a fence over other, unrelated memory locations. For the broader question of when a non-atomic write becomes visible to another thread, see [Memory Consistency and Fences](../04-cuda-memory-model/memory-consistency-and-fences.md).

## Global versus shared

Atomics work on both global and shared memory, and the same address-level guarantee applies to each: `atomicAdd(&globalCounter, 1)` and `atomicAdd(&sharedCounter, 1)` are both indivisible with respect to other atomics on that same location. The practical difference is latency and blast radius. A shared-memory atomic only contends with the other threads in the same block and rides on-chip memory, so it is far cheaper than a global atomic, which contends with every thread in the grid and round-trips through device memory (or an L2 cache line). That gap is the entire reason [Privatization](#privatization) below is the standard fix for grid-wide contention: do the contended part in shared memory, where contention is cheap, and pay the expensive global atomic only once per block.

## Supported types

| Built-in | Types | Notes |
|---|---|---|
| `atomicAdd` | `int`, `unsigned int`, `unsigned long long`, `float`, `double`, `__half2` | `double` requires compute capability 6.0 or newer. |
| `atomicMin` / `atomicMax` | `int`, `unsigned int`, `unsigned long long` | No native `float`/`double` overload — see `atomicCAS` below. |
| `atomicCAS` | `int`, `unsigned int`, `unsigned long long`, `unsigned short` | Compare-and-swap; the general-purpose escape hatch. |
| `atomicExch` | `int`, `unsigned int`, `unsigned long long`, `float` | Unconditional swap, returns the old value. |
| `atomicAnd` / `atomicOr` / `atomicXor` | `int`, `unsigned int`, `unsigned long long` | Bitwise; no floating-point equivalent. |

:::note[`double` atomicAdd needs CC 6.0+]
`atomicAdd` for `double` is only available on compute capability 6.0 (Pascal) and newer; earlier architectures support it only for `int`, `unsigned int`, `unsigned long long`, and `float`. See [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) for how to check what a target GPU supports.
:::

## Contention

This is the page's core performance model, and it is precise, not a rule of thumb: atomics to the *same address* serialize, because the indivisibility guarantee above means only one of them can be in flight at a time. If 32 threads in a warp issue `atomicAdd` to one shared address, the hardware executes those 32 read-modify-writes one after another — roughly a 32x slowdown on that single instruction compared to an uncontended access. If those same 32 threads instead target 32 distinct addresses, there is no ordering constraint between them at all, and the operation is close to free — limited by ordinary memory bandwidth, not by serialization.

The practical consequence: atomics are not inherently slow, contention is. A histogram over a huge key space where collisions are rare can be nearly as fast as a plain write; a histogram over a handful of hot bins where every thread in a warp lands on the same one or two bins pays the full serialization cost every warp, every time.

## `atomicCAS` for everything else

`atomicCAS(address, compare, val)` atomically compares `*address` to `compare` and, if they match, writes `val`; either way it returns the previous value of `*address`. Because it's the one operation that reports whether it "won," it's the building block for implementing any atomic operation the hardware doesn't provide natively — a compare-and-swap retry loop that keeps proposing a new value until nobody else changed the address out from under it in the meantime.

```cpp showLineNumbers
__device__ float atomicMaxFloat(float* addr, float value) {
    int* iaddr = reinterpret_cast<int*>(addr);
    int old = *iaddr, assumed;
    do {
        assumed = old;
        const float cur = __int_as_float(assumed);
        if (cur >= value) break;
        old = atomicCAS(iaddr, assumed, __float_as_int(value));
    } while (assumed != old);
    return __int_as_float(old);
}
```

:::warning[Only correct for non-negative floats]
This loop reinterprets the `float` bits as an `int` and compares them as integers, which only orders the same way as the floats themselves when both are non-negative — IEEE-754's sign bit inverts the integer ordering for negative values, so a negative `cur` can compare as "greater" in integer terms while being smaller as a float, or vice versa. Do not use this version on data that can be negative; it needs a different bit-manipulation (typically flipping the sign bit or all bits depending on sign before the integer comparison) to stay correct across the full float range.
:::

## Privatization

The standard fix for a hot global address is to stop contending on it in the first place: give each block its own private, cheap-to-contend copy, accumulate into that copy with `__shared__` memory atomics, and only reduce down to the expensive global atomic once per block instead of once per thread.

```cpp showLineNumbers
__global__ void histPrivatized(const int* data, int n, int* globalHist, int nBins) {
    extern __shared__ int localHist[];   // one private histogram per block
    for (int b = threadIdx.x; b < nBins; b += blockDim.x) localHist[b] = 0;
    __syncthreads();

    for (int i = blockIdx.x * blockDim.x + threadIdx.x; i < n; i += gridDim.x * blockDim.x) {
        atomicAdd(&localHist[data[i]], 1);   // cheap: contends only within the block
    }
    __syncthreads();

    for (int b = threadIdx.x; b < nBins; b += blockDim.x) {
        if (localHist[b] != 0) atomicAdd(&globalHist[b], localHist[b]);   // one global atomic per bin per block
    }
}
```

This turns a grid-wide contention problem into a per-block one, where shared-memory atomics are cheap, and collapses the expensive global step to at most one atomic per bin per block rather than one per input element. [Histogram](../13-applied-kernels-and-patterns/histogram.md) works through this pattern as a complete applied kernel. On compute capability 9.0 and newer, thread block clusters can go a step further and share the private accumulator across a cluster instead of a single block — see [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) for that cluster-level histogram.

## See also

- [Memory Consistency and Fences](../04-cuda-memory-model/memory-consistency-and-fences.md) — what atomics do and don't guarantee about ordering of other memory.
- [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) — cluster-level privatization on CC 9.0+.
- [Histogram](../13-applied-kernels-and-patterns/histogram.md) — the full privatized-histogram kernel this page's example is drawn from.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
