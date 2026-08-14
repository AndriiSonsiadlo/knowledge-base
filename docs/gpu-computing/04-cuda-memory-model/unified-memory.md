---
id: unified-memory
title: Unified Memory
sidebar_label: Unified Memory
sidebar_position: 7
tags: [gpu, cuda, memory, unified-memory]
---

# Unified Memory

Every allocation covered so far draws a hard line between host and device memory: a pointer is valid on one side or the other, and moving data across the line is an explicit `cudaMemcpy` the programmer writes and pays for. Unified Memory erases that line for the source code — one pointer, usable from both host and device — while the underlying hardware and driver still have to physically move bytes between two separate memory systems whenever the data is touched from the "wrong" side. Understanding *when* that migration happens, and how to steer it, is the difference between Unified Memory being a convenience and Unified Memory being a performance trap.

## One pointer, two memories

`cudaMallocManaged` replaces the `cudaMalloc`-plus-two-`cudaMemcpy` pattern from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) with a single allocation that both host and device code can dereference directly:

```cpp showLineNumbers
float *x, *y;
CUDA_CHECK(cudaMallocManaged(&x, bytes));
CUDA_CHECK(cudaMallocManaged(&y, bytes));

for (int i = 0; i < n; ++i) { x[i] = 1.0f; y[i] = 2.0f; }   // host writes directly

saxpy<<<blocks, threads>>>(n, 2.0f, x, y);
CUDA_CHECK(cudaDeviceSynchronize());

printf("y[0] = %f\n", y[0]);   // host reads directly, no cudaMemcpy

CUDA_CHECK(cudaFree(x));
CUDA_CHECK(cudaFree(y));
```

The two `cudaMemcpy` calls are gone entirely — the host writes `x` and `y` directly, the kernel reads and writes the same pointers, and the host reads the result back through that same pointer after synchronizing. Nothing in the kernel changes; `saxpy` never knew its pointers came from `cudaMallocManaged` instead of `cudaMalloc`. See [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) for what `CUDA_CHECK` does with the status these calls return.

## Page migration

Removing the explicit copies doesn't remove the physical data movement — it moves the decision of *when* to migrate from the programmer to the driver, triggered by a page fault. The mechanism works at page granularity: when the GPU executes an instruction that touches a virtual address not currently resident in device memory, that access faults, the driver migrates the containing page (or a batch of adjacent pages) from host to device, and the instruction retries. The same happens in reverse when the host touches a page currently resident on the device. A kernel that is the first to touch a freshly allocated managed buffer therefore pays a fault storm at the start of its run — potentially thousands of page faults serialized against the very kernel that's supposed to be using the data — before settling into steady-state execution.

## Prefetching

`cudaMemPrefetchAsync` sidesteps the fault storm by moving pages proactively, before the kernel that needs them runs:

```cpp showLineNumbers
CUDA_CHECK(cudaMemPrefetchAsync(x, bytes, deviceId, stream));
CUDA_CHECK(cudaMemPrefetchAsync(y, bytes, deviceId, stream));
saxpy<<<blocks, threads, 0, stream>>>(n, 2.0f, x, y);
```

Passing `cudaCpuDeviceId` as the destination prefetches back to host memory instead. A prefetch is still a migration — the bytes still cross the interconnect — but it happens as one bulk asynchronous transfer issued ahead of time rather than as thousands of small fault-driven ones interleaved with kernel execution.

## Advising the driver

`cudaMemAdvise` doesn't move data itself; it tells the driver how a range is *going to be used*, so the driver can pick a better migration policy the next time a fault (or prefetch) touches it:

- `cudaMemAdviseSetReadMostly` — the range is read far more than it's written; the driver keeps a read-only replica on multiple devices instead of migrating and invalidating on every access.
- `cudaMemAdviseSetPreferredLocation` — pins the *preferred* residency for a range to a given device; the driver still migrates on demand but tries to move pages back rather than leaving them wherever they last faulted.
- `cudaMemAdviseSetAccessedBy` — declares that a device will access the range without necessarily migrating it there, establishing a mapping so those accesses don't have to fault at all (at the cost of possibly slower remote access instead of a fast local one).

## Oversubscription

Because Unified Memory allocations aren't required to fit in device memory all at once, a managed allocation can be larger than the GPU's physical memory — the driver evicts and migrates pages on demand, using device memory as a working set rather than a hard ceiling. This lets an algorithm work on a dataset larger than the GPU, at the cost of the same page-fault traffic described above whenever the working set doesn't fit.

## The performance traps

:::warning[A host loop between kernel launches ping-pongs every page]
The classic mistake is a host loop that reads or writes a managed buffer between kernel launches without prefetching it back first:

```cpp
for (int iter = 0; iter < n_iters; ++iter) {
    kernel<<<blocks, threads>>>(data);
    CUDA_CHECK(cudaDeviceSynchronize());
    data[0] = check_value(data);   // host touches managed memory — faults it back
}
```

Every iteration, the kernel's first touch faults the buffer to the device, and the host's touch afterward faults it straight back — the full page set migrates twice per iteration even though most of it never actually changed. The fix is to prefetch explicitly around each side of the loop instead of letting faults drive the migration:

```cpp
for (int iter = 0; iter < n_iters; ++iter) {
    kernel<<<blocks, threads, 0, stream>>>(data);
    CUDA_CHECK(cudaMemPrefetchAsync(data, bytes, cudaCpuDeviceId, stream));
    CUDA_CHECK(cudaStreamSynchronize(stream));
    data[0] = check_value(data);
    CUDA_CHECK(cudaMemPrefetchAsync(data, bytes, deviceId, stream));
}
```
:::

:::note[Behaviour differs by platform]
On systems with hardware-coherent memory — Grace-Hopper's NVLink-C2C, and Pascal-and-later GPUs on Linux with Heterogeneous Memory Management (HMM) — migration happens at page granularity as described above, and host and device can even hold pages of the same allocation concurrently under coherent access. On Windows under WDDM, Unified Memory has no such fine-grained coherence: the driver migrates an *entire* allocation as one unit on first touch from either side, so a managed buffer behaves closer to an automatically-copied `cudaMalloc` region than a true demand-paged one. Don't assume page-granularity behavior transfers across platforms.
:::

## See also

- [Pinned Memory and Host Transfers](./pinned-memory-and-transfers.md) — the explicit-copy alternative, and where "asynchronous" actually means asynchronous.
- [Memory Spaces Overview](./memory-spaces-overview.md) — how managed memory relates to the other five spaces.
- [Memory Allocation APIs](../06-cuda-runtime-and-apis/memory-allocation-apis.md) — `cudaMallocManaged` alongside the other allocation functions.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
