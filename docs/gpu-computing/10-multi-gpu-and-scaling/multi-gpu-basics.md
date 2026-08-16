---
id: multi-gpu-basics
title: Multi-GPU Basics
sidebar_label: Multi-GPU Basics
sidebar_position: 1
tags: [gpu, cuda, multi-gpu, scaling]
---

# Multi-GPU Basics

A workload that outgrows one GPU's memory or compute budget needs a second one, and every choice from there — how many processes, how work gets split, where the time actually goes — follows from a small set of rules about how CUDA treats "current device" as thread-local state. Get the discipline wrong and the symptom is rarely a crash; it's silent misallocation onto the wrong device or serialized work that looks like it should overlap.

## Two process models

There are two ways to structure a multi-GPU program: one process that touches every device, or one process per device coordinating through a communication library.

| | One process, many devices | One process per device |
|---|---|---|
| Code complexity | Lower — one address space, explicit `cudaSetDevice` calls | Higher — needs a launcher and inter-process coordination |
| NCCL support | Works, but less common in practice | First-class — this is what NCCL and `torchrun`/`mpirun` are built around |
| Fault isolation | None — one device's sticky error takes down the whole process | Per-process — one rank's context corruption doesn't kill the others |
| Memory per process | Host-side bookkeeping for every device's allocations at once | Only its own device's allocations |
| Typical use | Small utilities, quick multi-GPU scripts, single-node data prep | Training at any real scale |

One process per device, with NCCL for communication and a launcher such as `torchrun` or `mpirun` to start and coordinate the ranks, is the standard for training. It gives fault isolation, maps naturally onto multi-node clusters, and is what every framework's distributed data-parallel path assumes.

## Device switching

The single-process model still shows up for smaller jobs, and its correctness rests entirely on `cudaSetDevice` discipline: every stream, allocation, and launch belongs to whichever device was current when it was created, and nothing about the API stops you from issuing a call against the wrong one.

```cpp showLineNumbers
for (int d = 0; d < nDevices; ++d) {
    CUDA_CHECK(cudaSetDevice(d));
    CUDA_CHECK(cudaMemcpyAsync(d_in[d], h_in + d * chunk, bytes,
                               cudaMemcpyHostToDevice, stream[d]));
    myKernel<<<grid, block, 0, stream[d]>>>(d_in[d], d_out[d], chunk);
}
for (int d = 0; d < nDevices; ++d) {
    CUDA_CHECK(cudaSetDevice(d));
    CUDA_CHECK(cudaStreamSynchronize(stream[d]));
}
```

The first loop issues every device's work without waiting for any of it — that's what makes the devices actually run concurrently. The second loop re-selects each device before synchronizing its stream, which looks redundant but isn't optional.

:::warning[A stream belongs to the device that was current when it was created]
Using a stream while a different device is current is an error, not a fallback to the stream's owning device. The second loop above sets the device again before each `cudaStreamSynchronize` for exactly this reason — skipping it and synchronizing all streams back to back under whatever device happened to be current last is a common source of `cudaErrorInvalidResourceHandle`.
:::

## Per-device streams

Each device needs at least one stream of its own; sharing a single `cudaStream_t` across devices isn't possible; a stream is created against whichever device is current at creation time and stays tied to it for its lifetime. The pattern above — one stream per device, indexed the same way as the device loop — is the simplest structure that keeps that binding straight.

## Partitioning work

How a problem splits across devices depends on what it needs from its neighbors. Contiguous chunks — device `d` owns elements `[d * chunk, (d + 1) * chunk)` — are the default for streaming, embarrassingly parallel work, because each device's slice is a single contiguous host-side range that copies cleanly. Interleaved partitioning — device `d` owns every `n`-th element — trades that simplicity for better load balance when the work per element varies unpredictably across the range. Stencil and convolution kernels add a third concern on top of either scheme: each device needs a halo of its neighbors' boundary elements to compute its own edge correctly, which turns partitioning into a communication problem, not just a division problem. See [Stencil and Convolution](../13-applied-kernels-and-patterns/stencil-and-convolution.md) for the halo-exchange pattern itself.

## Where the time actually goes

:::tip[Track scaling efficiency, not raw throughput]
Raw throughput going up with more GPUs feels like success even when it shouldn't. Scaling efficiency — throughput at `N` GPUs divided by `N` times single-GPU throughput — is the number that actually tells you whether adding hardware is paying for itself. Anything below roughly 80% at small scale (2–4 devices) means communication is already dominating, and it only gets worse as `N` grows; that's the point to go measure the interconnect and the collective pattern, not to add more GPUs.
:::

## See also

- [Peer-to-Peer Access and NVLink](./peer-to-peer-and-nvlink.md) — the direct device-to-device transfers this page's copies fall back to host staging without.
- [Data, Model, Pipeline, and Tensor Parallelism](./parallelism-strategies.md) — how these process models scale up into real training strategies.
- [Device Management](../06-cuda-runtime-and-apis/device-management.md) — the thread-local current-device state this whole page is built on.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
