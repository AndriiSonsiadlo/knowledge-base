---
id: error-handling
title: Error Handling and Checking
sidebar_label: Error Handling
sidebar_position: 8
tags: [gpu, cuda, runtime, error-handling]
---

# Error Handling and Checking

A CUDA API call that fails almost never fails where the mistake happened. Because most of the runtime is asynchronous, a kernel launch or a copy can return immediately with `cudaSuccess` on the host side while the actual work — and the actual error, if there is one — hasn't executed on the GPU yet. Unchecked, that error surfaces as a failure on some unrelated call several lines or several function calls later, which is why every other page in this section wraps runtime calls in a checking macro rather than trusting a bare return value.

## Errors are asynchronous

A host thread that calls a kernel launch or an async memcpy gets control back as soon as the operation is enqueued, not once it has run. The return value of the launch itself can only report enqueue-time problems — an invalid configuration, say — not anything that goes wrong once the kernel is actually executing on the GPU. Finding out about an in-kernel error means checking again after the work has had a chance to run, which is the whole reason `cudaGetLastError` and `cudaDeviceSynchronize` both matter below.

## Sticky and non-sticky errors

Not every error behaves the same way once it happens. A **non-sticky** error — `cudaErrorInvalidValue` from passing a bad argument, for instance — is a normal, recoverable return value: calling `cudaGetLastError` reads and clears it, and the context is otherwise fine to keep using. A **sticky** error — an illegal memory access or an out-of-bounds write inside a kernel — corrupts the CUDA context itself: every subsequent runtime call fails, no matter how unrelated it looks, and the only way out is for the process to exit and start a fresh context. This distinction is why "my code fails at some later, completely unrelated call" is a common symptom — the real failure was upstream, non-sticky checking was skipped at the point it happened, and by the time an error was finally noticed the context was already sticky-broken and reporting failures everywhere.

## The `CUDA_CHECK` macro

Every other page in this section calls a macro named `CUDA_CHECK` around runtime API calls without redefining it. This is that definition:

```cpp showLineNumbers title="cuda_check.h"
#pragma once
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>

#define CUDA_CHECK(call)                                                    \
    do {                                                                    \
        cudaError_t err_ = (call);                                          \
        if (err_ != cudaSuccess) {                                          \
            std::fprintf(stderr, "CUDA error %s at %s:%d: %s\n",            \
                         cudaGetErrorName(err_), __FILE__, __LINE__,        \
                         cudaGetErrorString(err_));                         \
            std::exit(EXIT_FAILURE);                                        \
        }                                                                   \
    } while (0)
```

This macro is used unqualified on every other page in this section: wherever a code example elsewhere writes `CUDA_CHECK(some_call(...))`, it means exactly this — evaluate the call, and if it didn't return `cudaSuccess`, print the error name, the file and line, and the human-readable message, then exit. It deliberately exits rather than trying to continue, because a sticky error has already made continuing meaningless, and a non-sticky one is still a bug worth stopping for rather than papering over.

## Checking after a launch

`CUDA_CHECK` alone doesn't cover a kernel launch, because `<<<>>>` returns nothing for the macro to inspect. Catching launch problems takes two separate calls afterward:

```cpp showLineNumbers
myKernel<<<grid, block>>>(/* ... */);
CUDA_CHECK(cudaGetLastError());        // catches launch-configuration errors
CUDA_CHECK(cudaDeviceSynchronize());   // catches errors raised during execution
```

`cudaGetLastError()` picks up problems the driver could detect immediately — an invalid grid or block configuration, for instance — without waiting for the kernel to actually run. `cudaDeviceSynchronize()` blocks until the kernel has finished and surfaces anything that went wrong during execution, such as an illegal address.

:::warning[`cudaDeviceSynchronize()` here is a debug-build measure]
Synchronizing after every launch to check for errors is correct and useful while debugging, but it forces the host to wait for the GPU at every single launch, destroying the overlap and concurrency that [Streams and Concurrency](./streams-and-concurrency.md) exists to provide. Leaving this pattern in a hot loop in production code will measurably hurt throughput. Check `cudaGetLastError()` freely — it doesn't synchronize — and reserve `cudaDeviceSynchronize()` checks for debug builds or infrequent checkpoints.
:::

## Making a bug reproducible

:::tip[`CUDA_LAUNCH_BLOCKING=1`, then `compute-sanitizer`]
Setting the environment variable `CUDA_LAUNCH_BLOCKING=1` makes every kernel launch synchronous, so an error is reported at the launch that actually caused it instead of at some later call after the context has already gone sticky. Use it only while debugging — it serializes everything and is far too slow for normal runs. Once the failing launch is pinned down, `compute-sanitizer` gives the actual diagnosis — the specific thread, address, and access type behind an illegal access — rather than just its location. See [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md).
:::

## See also

- [Device Management](./device-management.md) — the device and context state a sticky error corrupts.
- [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md) — diagnosing what a caught error actually points to.
- [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) — the launch syntax `cudaGetLastError` checks after.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
