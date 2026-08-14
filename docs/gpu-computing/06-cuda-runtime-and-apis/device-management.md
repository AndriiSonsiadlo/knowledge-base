---
id: device-management
title: Device Management
sidebar_label: Device Management
sidebar_position: 2
tags: [gpu, cuda, runtime, devices]
---

# Device Management

A host process can see more than one GPU, and CUDA never guesses which one a call should target — it operates against whichever device is *current* on the calling thread, a piece of state the program has to set itself. Getting this wrong doesn't usually crash; it silently allocates memory or launches kernels on the wrong GPU, or leaves a multi-threaded program with each thread quietly disagreeing about which device it's using. See [Error Handling and Checking](./error-handling.md) for what `CUDA_CHECK` does with the status these calls return.

## Enumerating devices

`cudaGetDeviceCount` and `cudaGetDeviceProperties` are the starting point for any program that needs to know what hardware it's running on before making decisions:

```cpp showLineNumbers
int count = 0;
CUDA_CHECK(cudaGetDeviceCount(&count));
for (int d = 0; d < count; ++d) {
    cudaDeviceProp p{};
    CUDA_CHECK(cudaGetDeviceProperties(&p, d));
    printf("%d: %s  CC %d.%d  SMs %d  global %.1f GiB  shared/SM %zu KiB\n",
           d, p.name, p.major, p.minor, p.multiProcessorCount,
           p.totalGlobalMem / 1073741824.0,
           p.sharedMemPerMultiprocessor / 1024);
}
```

## `cudaDeviceProp`

`cudaDeviceProp` carries dozens of fields; most programs only ever consult a handful of them to make a decision:

| Field | Decision it informs |
| --- | --- |
| `major` / `minor` | Compute capability — whether the binary has a matching SASS image, and which instructions/features are available. |
| `multiProcessorCount` | How many SMs to size a grid against, for occupancy-driven launch configuration. |
| `maxThreadsPerBlock` | The hard ceiling on block size for a launch configuration. |
| `sharedMemPerBlock` | How much shared memory a single block can request before the launch fails. |
| `regsPerBlock` | Register budget that, combined with per-thread register usage, caps occupancy. |
| `warpSize` | Almost always 32, but code that hard-codes it instead of reading it isn't portable to a hypothetical future value. |
| `memoryBusWidth` | Part of the peak-bandwidth calculation used to judge whether a kernel is memory-bound. |
| `memoryClockRate` | The other half of the peak-bandwidth calculation. |
| `l2CacheSize` | Whether a working set is likely to fit in L2 versus spill to global memory on every pass. |
| `concurrentKernels` | Whether the device can run multiple kernels from different streams simultaneously at all. |
| `unifiedAddressing` | Whether host and device pointers share one address space (required for several Unified Memory and peer-access features). |

## Selecting a device

`cudaSetDevice(d)` makes device `d` current for the calling thread; every subsequent runtime call that doesn't take an explicit device argument — allocation, launch, stream creation — operates against it. `cudaGetDevice(&d)` reads back whichever device is current.

## Per-thread device state

`cudaSetDevice` sets **thread-local** state, not process-global state. In a multi-threaded program, every host thread that touches the GPU has to call `cudaSetDevice` itself — setting it on one thread has no effect on any other. This also governs allocations: memory returned by `cudaMalloc` (or its stream-ordered relatives) belongs to whichever device was current *at the moment of the allocation call*, and using it from a different device without peer access configured is an error, not a fallback.

## Resetting

`cudaDeviceReset()` tears down the current device's primary context: every allocation, stream, event, and module associated with it is destroyed, and the device returns to an uninitialized state.

:::warning[`cudaDeviceReset()` is a teardown, not a checkpoint]
It belongs at the very end of a program — and in profiling runs, where it also makes sure the profiler's buffered data gets flushed before the process exits — never inside a loop or between phases of ongoing work. Calling it mid-program destroys every live allocation and forces the next CUDA call to re-pay the initialization cost of a fresh primary context.
:::

:::tip[`CUDA_VISIBLE_DEVICES` renumbers devices per process]
Setting the `CUDA_VISIBLE_DEVICES` environment variable restricts and renumbers the devices a process can see — device 0 inside the process might be physical GPU 3 on the machine. It's the cleanest way to pin a job to a specific GPU without touching its source code, and it's how most cluster schedulers isolate jobs from each other on a shared multi-GPU host. See [GPU Clusters and Schedulers](../10-multi-gpu-and-scaling/clusters-and-schedulers.md).
:::

## See also

- [Runtime API vs Driver API](./runtime-vs-driver-api.md) — the primary context this page's per-device state lives inside.
- [MPS and MIG](./mps-and-mig.md) — sharing or partitioning a single physical GPU across processes.
- [Multi-GPU Basics](../10-multi-gpu-and-scaling/multi-gpu-basics.md) — coordinating work across more than one device selected this way.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
