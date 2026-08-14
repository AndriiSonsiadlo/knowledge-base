---
id: shared-memory
title: Shared Memory
sidebar_label: Shared Memory
sidebar_position: 3
tags: [gpu, cuda, memory, shared-memory]
---

# Shared Memory

Global memory is fast in aggregate but every access still pays a round trip through the memory system; when several threads in a block need the same piece of data, or a thread needs to hand a value to another thread in the same block, routing through global memory to do it wastes bandwidth on traffic that never needed to leave the chip. Shared memory exists for exactly that: a small, explicitly-managed, on-chip scratchpad that every thread in a block can read and write, fast enough to use as a staging area rather than just a cache.

## Two roles: scratchpad and channel

Shared memory does two distinct jobs, and most uses are one or the other. As a **scratchpad**, a block stages a tile of global data into shared memory once, then every thread in the block reuses it many times — the classic case is a tiled matrix multiply, where each element loaded from global memory would otherwise be re-read by every thread that needs it. As a **channel**, shared memory is how threads in a block communicate with each other directly — one thread writes a value another thread reads, without going through global memory at all, as in a block-wide reduction.

## Static allocation

The simplest form declares a fixed-size array with the `__shared__` qualifier, sized at compile time:

```cpp
__shared__ float tile[32][33];
```

Every block that runs this kernel gets its own instance of `tile`, sized and typed exactly as declared — no runtime configuration needed.

## Dynamic allocation

When the size isn't known until launch time, declare an unsized `extern` array and pass the byte size as the kernel launch's third `<<<...>>>` parameter:

```cpp
extern __shared__ float buf[];
```

```cpp
kernel<<<g, b, bytes>>>();
```

The kernel indexes into `buf` using sizes it computes itself (from a kernel argument, for example) — the compiler has no idea how large the array actually is at compile time, only that `bytes` bytes of shared memory are reserved for it per block at launch.

## The L1 carveout

[Cache Hierarchy](../02-gpu-hardware-architecture/cache-hierarchy.md) covers that L1 and shared memory share the same physical SRAM since Volta, split by a configurable carveout rather than being separate pools. `cudaFuncSetCacheConfig` (per-kernel) lets you bias that split toward more shared memory or more L1 cache, and `cudaFuncAttributePreferredSharedMemoryCarveout` (used with `cudaFuncSetAttribute`) sets the preferred split as a percentage. The trade is direct: more shared memory raises the ceiling on how much a block can stage on-chip, or how many blocks with a given shared-memory footprint can be resident at once; more L1 helps kernels that lean on the cache for irregular global-memory reuse instead. Neither setting is a hard guarantee — the driver treats it as a preference against a fixed total pool size.

## Opting into more than 48 KB

The historical static default caps a single kernel's shared memory usage at 48 KB; using more requires an explicit opt-in, and it's easy to get wrong by forgetting one of the two steps:

```cpp showLineNumbers
CUDA_CHECK(cudaFuncSetAttribute(
    myKernel, cudaFuncAttributeMaxDynamicSharedMemorySize, 65536));
myKernel<<<blocks, threads, 65536>>>(/* ... */);
```

The `cudaFuncSetAttribute` call raises the *permitted* maximum for this kernel; the launch's third `<<<...>>>` argument still has to actually request that much, and both numbers have to match what the kernel's own indexing expects. See [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) for what `CUDA_CHECK` does with the status this call returns.

:::note[Opt-in ceiling is compute-capability-dependent]
The maximum dynamic shared memory a kernel can request past the 48 KB default varies by compute capability — see [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) before assuming a number here transfers to a different generation.
:::

:::warning[Shared memory is per-block, uninitialized, and caps occupancy]
Shared memory is not zero-initialized — reading a location a block hasn't written yet reads garbage. And because shared memory is allocated per resident block, its size directly caps how many blocks can occupy one SM simultaneously: a block requesting 48 KB of shared memory on an SM with 164 KB usable can have at most 3 blocks resident, regardless of how cheap the kernel is on registers or thread slots. See [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) for how this limiter interacts with the other two.
:::

## The lifetime rule

Within a block, one thread's write to shared memory is only guaranteed visible to another thread after both have passed a `__syncthreads()` barrier — the hardware does not guarantee any ordering between threads' shared-memory writes and other threads' reads of the same location without one. A kernel that writes into shared memory and reads a location another thread wrote, without a synchronization point between the two, has a race whether or not it happens to produce the right answer on a given run. [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md) covers `__syncthreads()` and its Cooperative Groups equivalents in full.

## See also

- [Shared Memory Bank Conflicts](./bank-conflicts.md) — the access-pattern rule that governs how fast shared memory actually is.
- [Distributed Shared Memory](./distributed-shared-memory.md) — extending shared-memory visibility across a thread block cluster.
- [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md) — `__syncthreads()` and the lifetime rule in full.
- [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) — using shared memory as a scratchpad in a real kernel.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
