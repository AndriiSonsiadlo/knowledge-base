---
id: the-host-device-model
title: The Host–Device Model
sidebar_label: Host–Device Model
sidebar_position: 7
tags: [gpu, parallelism, offload, memory]
---

# The Host–Device Model

Before any of the CUDA syntax in the next section makes sense, one structural fact has to be settled: a discrete GPU is a separate computer. It has its own memory, its own processors, and no automatic view of what the CPU is doing — every byte the GPU touches had to arrive there deliberately, and every result has to leave the same way. This page names that structure once, independent of any specific API, so that the CUDA-specific mechanics in [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) land on a model you already have rather than a pile of new syntax to memorize.

## Two machines, two address spaces

The **host** is the CPU and its system memory; the **device** is the GPU and its own on-board memory (device DRAM, typically HBM on data-center parts or GDDR on consumer ones). A pointer valid in one address space is not automatically valid in the other — a host pointer dereferenced on the device, or vice versa, is undefined behavior unless the memory was specifically set up to be visible from both (unified memory, covered below). This is the single most common source of a new CUDA programmer's first segfault: passing a `malloc`'d host pointer straight into a kernel launch.

Because the two machines have separate memory, they also have separate allocators and separate lifetimes — device memory is allocated and freed with its own API calls, independent of the host's, and a device allocation persists until explicitly freed or the process exits, regardless of what the host does with its own memory in the meantime.

## The offload cycle

The canonical shape of GPU work is a three-step cycle: copy input data from host to device, run computation on the device, copy results back. Each arrow below is a real, non-free operation — the middle step can loop many times (many kernels, or one kernel launched repeatedly) before the final copy back, and the more iterations that happen before the H2D/D2H copies are needed again, the more the fixed cost of those copies is amortized (see the transfer-dominated-workload arithmetic in [When Not to Use a GPU](../00-overview/when-not-to-use-a-gpu.md)).

```mermaid
flowchart LR
  H["Host memory"] -->|"H2D copy"| D["Device memory"]
  D -->|"kernel reads/writes"| D
  D -->|"D2H copy"| H
```

Every stage in that diagram is asynchronous with respect to the host by default, which is the next point worth making explicit.

## Asynchrony is the default

A kernel launch returns to the host code immediately, before the kernel has run, or even necessarily started — the launch only enqueues work onto a stream. The same is true of a copy issued on a stream with pinned host memory. This is a deliberate design choice: the host is a separate machine free to keep working — queuing the next kernel, preparing the next batch of data, servicing other logic — while the device works through what's already been handed to it. The host only blocks when something explicitly makes it wait: a synchronous (default-stream, unpinned) memory copy, an explicit `cudaDeviceSynchronize()`, or a query on an event or stream that hasn't completed yet.

Treating this as an afterthought is exactly the mistake worked through in [When Not to Use a GPU](../00-overview/when-not-to-use-a-gpu.md): a full-device synchronize inserted into a hot loop turns a pipeline that should overlap transfer, compute, and host-side work into one that serializes all three, and the launch and copy overhead that asynchrony was supposed to hide becomes fully exposed instead. Streams and events, covered in [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md), are the mechanism for expressing "these can overlap" and "this must wait for that" without collapsing everything into one synchronous line.

## The same model in HIP, SYCL, and OpenCL

The host/device split, the explicit-copy-or-offload cycle, and asynchronous-by-default queuing are not CUDA-specific; every major GPU programming model expresses the same structure with different names for the same four concepts:

| Concept | CUDA | HIP | SYCL | OpenCL |
|---|---|---|---|---|
| Device | Device (GPU) | Device (GPU) | Device | Device |
| Queue / stream | Stream | Stream | Queue | Command queue |
| Kernel | `__global__` function | `__global__` function | Kernel lambda / functor | Kernel function |
| Device allocation | `cudaMalloc` | `hipMalloc` | USM `malloc_device` / buffer | `clCreateBuffer` |
| Explicit copy | `cudaMemcpy` (or async, on a stream) | `hipMemcpy` | `queue.memcpy` / buffer accessor | `clEnqueueWriteBuffer` / `clEnqueueReadBuffer` |

Learning the model once here, rather than as "how CUDA happens to work," is what makes [The Portability Problem](../11-portable-and-vendor-neutral/the-portability-problem.md) legible later — porting between these APIs is largely a matter of translating names for the same five rows, not relearning the structure underneath them.

:::note[Unified memory blurs the split, not the cost]
Unified memory (CUDA) and shared virtual memory (SYCL, OpenCL 2.0+) let the same pointer be dereferenced from host and device code, with the runtime migrating pages on demand instead of requiring an explicit `cudaMemcpy`-style call. That removes the *address-space* split — one pointer, valid everywhere — but not the underlying transfer cost: data still has to physically move across PCIe or NVLink the first time each side touches it, and a poorly-behaved access pattern can trigger migration traffic that's harder to see and reason about than an explicit copy would have been. See [Unified Memory](../04-cuda-memory-model/unified-memory.md) for how the automatic migration actually works and when it's a net win.
:::

## See also

- [Latency, Throughput, and Latency Hiding](./latency-throughput-and-hiding.md) — why the device side of this model needs so many concurrent threads once work reaches it.
- [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) — this same offload cycle, written out in actual CUDA syntax.
- [The Portability Problem](../11-portable-and-vendor-neutral/the-portability-problem.md) — what changes, and what doesn't, when this model is expressed in a vendor-neutral API.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
