---
id: pinned-memory-and-transfers
title: Pinned Memory and Host Transfers
sidebar_label: Pinned Memory
sidebar_position: 8
tags: [gpu, cuda, memory, transfers]
---

# Pinned Memory and Host Transfers

The SAXPY program in [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) paid three costs without the source code drawing attention to any of them: two host-to-device copies, one kernel launch, and one device-to-host copy, all running one after another on the default stream. The launch was already asynchronous — it returned before the kernel necessarily started. The copies were not, and there's a mechanical reason why: ordinary `malloc`'d host memory is pageable, and pageable memory cannot be the source or destination of an asynchronous transfer. Pinned memory removes that restriction, and once transfers are asynchronous, they can be scheduled to overlap with compute instead of paying for it serially.

## Pageable versus pinned

Regular host memory, from `malloc` or `new`, is pageable — the operating system is free to move it between physical RAM and disk (swap) at any time. The GPU's DMA engine can't safely target a pageable address directly, because the page it points at might move mid-transfer. So a pageable `cudaMemcpy` is actually two copies: the driver first copies the data into a temporary pinned staging buffer it maintains internally, then DMAs from that staging buffer to the device. That staging copy happens on the CPU, runs synchronously, and is why a pageable `cudaMemcpy` blocks the calling thread and cannot be issued asynchronously — there's a CPU-side copy in the critical path that has to complete before the DMA can even start.

Pinned (page-locked) memory removes the OS's ability to move the pages, so the DMA engine can transfer directly to or from it, with no staging copy and no CPU involvement beyond issuing the request. That's what makes `cudaMemcpyAsync` genuinely asynchronous: with a pinned source or destination, the call only enqueues the transfer and returns.

## Allocating pinned memory

Three ways to get pinned host memory, depending on whether the buffer is new or already exists:

- `cudaMallocHost(&ptr, bytes)` — allocates a new pinned buffer directly; the simplest form, roughly a pinned drop-in for `malloc`.
- `cudaHostAlloc(&ptr, bytes, flags)` — the same allocation, with flags controlling additional behavior (below).
- `cudaHostRegister(ptr, bytes, flags)` — pins an *existing* pageable allocation in place, useful when the buffer's lifetime is owned by code that can't be changed to allocate pinned memory directly.

`cudaHostAlloc`'s flags:

- `cudaHostAllocPortable` — the pinned allocation is pinned with respect to *every* CUDA context/device in the process, not just the one that allocated it; needed in multi-GPU code that shares a host buffer across devices.
- `cudaHostAllocMapped` — maps the allocation into the device's address space too, enabling zero-copy access (below).
- `cudaHostAllocWriteCombined` — allocates with a write-combined cache policy, which speeds up the host's sequential writes and the PCIe transfer, but makes host *reads* from that memory much slower; only use it for buffers the host writes once and never reads back.

## Zero-copy and mapped memory

Memory allocated with `cudaHostAllocMapped` gets a device-side pointer (via `cudaHostGetDevicePointer`) that a kernel can dereference directly, reading and writing host memory over PCIe on every access instead of through an explicit `cudaMemcpy` beforehand. This is zero-copy access: no bulk transfer, no device-resident copy of the data at all. It trades transfer bandwidth for latency-hidden convenience, and it's the right tool only when a kernel touches a small fraction of a large buffer, or touches it exactly once — a kernel that reads the same location repeatedly is far better served by copying the data to device memory once and reading it from there.

## Overlapping transfer with compute

This is the payoff the rest of the page has been building toward: split the problem into chunks, one CUDA stream per chunk, and issue each chunk's H2D copy, kernel launch, and D2H copy on its own stream. Because the copies are asynchronous, the driver can overlap chunk *i*'s transfer with chunk *i-1*'s kernel execution instead of running everything back-to-back.

```cpp showLineNumbers
const int nStreams = 4;
cudaStream_t stream[nStreams];
for (int i = 0; i < nStreams; ++i) CUDA_CHECK(cudaStreamCreate(&stream[i]));

const int chunk = n / nStreams;
for (int i = 0; i < nStreams; ++i) {
    const int off = i * chunk;
    CUDA_CHECK(cudaMemcpyAsync(d_x + off, h_x + off, chunk * sizeof(float),
                               cudaMemcpyHostToDevice, stream[i]));
    saxpy<<<(chunk + 255) / 256, 256, 0, stream[i]>>>(chunk, 2.0f, d_x + off, d_y + off);
    CUDA_CHECK(cudaMemcpyAsync(h_y + off, d_y + off, chunk * sizeof(float),
                               cudaMemcpyDeviceToHost, stream[i]));
}
for (int i = 0; i < nStreams; ++i) CUDA_CHECK(cudaStreamSynchronize(stream[i]));
```

`h_x` and `h_y` **must** be pinned — allocated with `cudaMallocHost` or `cudaHostAlloc`, not plain `malloc` — for these `cudaMemcpyAsync` calls to actually run asynchronously; pass a pageable pointer here and the call silently falls back to synchronous behavior, and the overlap this whole pattern exists to create never happens. [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md) covers how the driver schedules work across streams to make the overlap in this pattern real. See [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) for what `CUDA_CHECK` does with the status these calls return.

:::warning[Pinned memory is a scarce, shared resource]
Page-locked memory can't be swapped out, so every byte pinned is a byte permanently unavailable to the rest of the operating system, including other processes. Pinning a large fraction of host RAM starves the system of pageable memory it needs for everything else, degrading overall responsiveness even while the CUDA program itself runs faster. Pin only the buffers actually involved in transfers, sized to what the transfer pattern needs, not the whole dataset by default.
:::

## Measuring PCIe throughput

Bandwidth claims are only meaningful measured, not assumed. The standard recipe times a large `cudaMemcpyAsync` between a pair of `cudaEvent_t` markers recorded immediately before and after the call, then computes bytes transferred divided by elapsed time; [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md) covers the event API this relies on and the pitfalls of timing GPU work from the host clock instead. A well-configured host (pinned buffers, a direct PCIe or NVLink path, no contending traffic) should reach roughly 85–90% of the link's theoretical peak bandwidth; consistently landing well below that is a sign the buffer isn't actually pinned, the transfer is too small to amortize per-call overhead, or something else on the link is competing for it.

## See also

- [Unified Memory](./unified-memory.md) — the implicit-migration alternative to explicit pinned transfers.
- [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md) — how streams actually schedule the overlap this page's pattern depends on.
- [When Not to Use a GPU](../00-overview/when-not-to-use-a-gpu.md) — when transfer cost alone rules out offloading a workload at all.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
