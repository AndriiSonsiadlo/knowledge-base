---
id: memory-allocation-apis
title: Memory Allocation APIs
sidebar_label: Allocation APIs
sidebar_position: 3
tags: [gpu, cuda, runtime, allocation]
---

# Memory Allocation APIs

`cudaMalloc` is the allocator every earlier example reached for, and for a program that allocates once at startup and frees once at exit, it's the right tool. It stops being the right tool the moment allocation moves inside a loop, because `cudaMalloc` and `cudaFree` are synchronizing, device-wide operations — they can take tens of microseconds each, which is invisible in a single call and devastating when it happens every iteration of a hot loop. The APIs on this page exist to give allocation a shape that matches how a program actually uses memory: padded for coalescing, ordered in a stream, pooled, or — rarely — managed as raw virtual address space.

## `cudaMalloc` and its cost

`cudaMalloc(&ptr, bytes)` and `cudaFree(ptr)` each implicitly synchronize the device: every kernel and copy already in flight has to complete (or at least reach a driver-visible checkpoint) before the call returns. That cost is easy to miss in a benchmark that allocates its working set once, and easy to reintroduce by accident in code that allocates scratch space inside a per-iteration or per-batch loop. Allocating inside a hot loop is a common and largely invisible performance bug — the program is still correct, just quietly paying a device-wide stall on every pass.

## Pitched allocations

A 2D array allocated as one flat `cudaMalloc`'d block has rows that start at arbitrary byte offsets, which can misalign later rows for coalesced access even when the first row is aligned. `cudaMallocPitch` pads each row up to a driver-chosen alignment so every row start is aligned the same way, and returns that row stride — the **pitch**, in bytes — alongside the pointer:

```cpp showLineNumbers
float* d_a;
size_t pitch;
CUDA_CHECK(cudaMallocPitch(&d_a, &pitch, width * sizeof(float), height));
CUDA_CHECK(cudaMemcpy2D(d_a, pitch, h_a, width * sizeof(float),
                         width * sizeof(float), height, cudaMemcpyHostToDevice));
```

Indexing into a pitched allocation from a kernel uses the returned pitch, not `width`, to compute a row's start:

```cpp
T* rowPtr = (T*)((char*)d_a + row * pitch);
T value = rowPtr[col];   // equivalent to: *(T*)((char*)d_a + row * pitch + col * sizeof(T))
```

`cudaMemcpy2D` is the matching copy function — it takes source and destination pitches separately, so a pitched device allocation and an unpitched host array copy correctly in one call instead of one row at a time.

## Stream-ordered allocation

`cudaMallocAsync` / `cudaFreeAsync` are the modern answer to the synchronization cost above: allocation and deallocation become stream-ordered operations, queued and executed in issue order alongside the kernels and copies around them, instead of blocking the whole device.

```cpp showLineNumbers
cudaStream_t s;
CUDA_CHECK(cudaStreamCreate(&s));

float* d = nullptr;
CUDA_CHECK(cudaMallocAsync(&d, bytes, s));   // ordered in the stream, from a pool
myKernel<<<grid, block, 0, s>>>(d);
CUDA_CHECK(cudaFreeAsync(d, s));             // returns to the pool, no device sync
```

Both calls draw from a **memory pool** attached to the stream's device rather than going straight to the driver: `cudaFreeAsync` returns memory to the pool for reuse instead of releasing it back to the OS, so a steady-state loop that allocates and frees the same sizes repeatedly stops paying allocation cost almost entirely after the first few iterations. `cudaMemPoolSetAttribute` with `cudaMemPoolAttrReleaseThreshold` controls how much freed memory the pool is allowed to hold onto before it starts actually releasing it back to the driver, trading memory footprint against how often the pool has to grow again later.

## Memory pools

The pool behind `cudaMallocAsync` is itself an object — `cudaMemPool_t` — that can be created explicitly with `cudaMemPoolCreate`, shared across streams, or configured for peer-device access, rather than always using the implicit default pool a device gets automatically. Most code never needs to touch a pool explicitly; it's there for cases that need finer control over release thresholds, sharing a pool across multiple streams deliberately, or exporting pool memory for interprocess use.

## The virtual memory management API

The driver-API VMM functions (`cuMemCreate`, `cuMemAddressReserve`, `cuMemMap`) separate the two things `cudaMalloc` bundles together: reserving virtual address space and backing it with physical memory. That separation lets an allocation *grow* by mapping additional physical pages onto address space reserved past its current end, without copying the existing data to a larger buffer the way growing a `cudaMalloc` region requires. It's a driver-API facility, and most application code never needs it — it exists for allocator and framework authors building their own growable buffers or fine-grained memory-sharing schemes on top of CUDA.

## Choosing

| Situation | Use |
| --- | --- |
| Allocate once at startup, free at shutdown | `cudaMalloc` / `cudaFree` |
| 2D array accessed row-by-row on the device | `cudaMallocPitch` + `cudaMemcpy2D` |
| Allocate/free repeatedly inside a loop or per-iteration workload | `cudaMallocAsync` / `cudaFreeAsync` |
| Need to tune how much freed memory a pool retains | `cudaMemPoolSetAttribute` on the pool |
| A buffer that needs to grow without copying, or explicit physical/virtual separation | The VMM API (`cuMemCreate` / `cuMemAddressReserve` / `cuMemMap`) |

## See also

- [Streams and Concurrency](./streams-and-concurrency.md) — the stream ordering that `cudaMallocAsync` and `cudaFreeAsync` participate in.
- [Unified Memory](../04-cuda-memory-model/unified-memory.md) — `cudaMallocManaged`, the other allocator this page's decision table doesn't cover.
- [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md) — the host-side allocation APIs that pair with these device-side ones.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
