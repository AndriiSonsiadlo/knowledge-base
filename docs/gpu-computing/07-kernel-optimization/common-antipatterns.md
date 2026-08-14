---
id: common-antipatterns
title: Common Antipatterns
sidebar_label: Antipatterns
sidebar_position: 11
tags: [gpu, cuda, optimization, antipatterns]
---

# Common Antipatterns

The rest of this section explains how to do things correctly; this page is the shorter list of specific ways not to. Each entry names a symptom, the mechanism that causes it, and the fix — a checklist to scan before believing a benchmark or a kernel is done, not a tutorial.

## Optimizing before profiling

**Symptom:** effort spent on a change that doesn't move the runtime.
**Mechanism:** tuning based on what "looks slow" in the source rather than what a profiler shows the kernel is actually waiting on.
**Fix:** [The Optimization Workflow](./the-optimization-workflow.md) — measure, classify the limiter, fix that limiter only.

## Synchronizing in the hot loop

**Symptom:** a kernel that should overlap with other work instead runs at host-launch speed.
**Mechanism:** calling `cudaDeviceSynchronize()` after every iteration forces the host to wait for the GPU on every pass, destroying overlap between launches.

```cpp showLineNumbers
for (int i = 0; i < n; ++i) {
    kernel<<<grid, block>>>(d_data, i);
    CUDA_CHECK(cudaDeviceSynchronize());   // stalls the host every iteration
}
```

**Fix:** use CUDA events to time or order work, or a single synchronize after the whole loop, not one per iteration.

## Allocating inside the loop

**Symptom:** a loop that's correct but far slower than its arithmetic would suggest.
**Mechanism:** `cudaMalloc`/`cudaFree` each implicitly synchronize the device; paying that cost every iteration is invisible in a single call and expensive over many.
**Fix:** `cudaMallocAsync`/`cudaFreeAsync` with a memory pool, see [Memory Allocation APIs](../06-cuda-runtime-and-apis/memory-allocation-apis.md).

## Host–device ping-pong

**Symptom:** a loop with GPU work in it runs no faster than doing the same work on the CPU.
**Mechanism:** copying a scalar back to the host to make a decision every step forces a round trip and a synchronization on every iteration, serializing what should be an overlapped pipeline.
**Fix:** keep the decision on the device — a device-side reduction or predicate, not a host-side branch on a copied-back value.

## Pageable memory in an async pipeline

**Symptom:** `cudaMemcpyAsync` calls that should overlap with kernels instead block the host, one after another.
**Mechanism:** pageable host memory can't be transferred by DMA directly; the driver silently stages it through an internal pinned buffer, which makes the "asynchronous" copy synchronous from the host's point of view.
**Fix:** allocate the host buffer with `cudaMallocHost` (or `cudaHostRegister` an existing one) so it's pinned.

## `printf` in kernels

**Symptom:** a kernel that appears to run correctly, but far slower than a build without the debug output, and the slowdown itself gets misattributed to something else.
**Mechanism:** device-side `printf` serializes through an internal device buffer that every printing thread contends for, which can change the very timing being measured.
**Fix:** fine for one-off debugging; strip it before benchmarking or shipping a release build.

## Benchmarking without warm-up

**Symptom:** the first timed iteration is dramatically slower than the rest, skewing an average or a single-shot measurement.
**Mechanism:** the first launch pays JIT compilation (if no matching SASS is in the fatbinary), context creation, and clocks that haven't yet ramped up to their sustained boost state.
**Fix:** run and discard several iterations before starting the timed region; see [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md).

## Benchmarking code the compiler deleted

**Symptom:** a kernel change measures as implausibly, impossibly fast.
**Mechanism:** if a kernel's output is never read by anything, the compiler is free to eliminate the computation that produced it entirely — the benchmark is timing an empty kernel.

```cpp showLineNumbers
__global__ void wasted(float* in, int n) {
    float acc = 0.0f;
    for (int i = 0; i < n; ++i) acc += in[i];   // acc is never written anywhere — may vanish
}
```

**Fix:** write the result to a device array or a `volatile` sink that the compiler can't prove is unused.

## Chasing occupancy on a memory-bound kernel

**Symptom:** raising occupancy (more resident warps, smaller blocks) doesn't move the runtime.
**Mechanism:** occupancy hides latency by giving the scheduler more warps to switch to; it does nothing when the ceiling is DRAM bandwidth itself rather than warp supply.
**Fix:** confirm the limiter before tuning occupancy — see [Occupancy Tuning](./occupancy-tuning.md).

## Assuming warp-synchronous execution

**Symptom:** code that relies on threads within a warp implicitly staying in lockstep without an explicit sync, and that broke on newer hardware.
**Mechanism:** independent thread scheduling since CC 7.0 (Volta) means threads in a warp are no longer guaranteed to execute in lockstep even for straight-line code; only explicit `__syncwarp()` or the `_sync` primitives guarantee convergence.
**Fix:** use the `_sync`-suffixed warp primitives and an explicit mask; see [Independent Thread Scheduling](../05-execution-and-synchronization/independent-thread-scheduling.md).

## See also

- [The Optimization Workflow](./the-optimization-workflow.md) — the measure-classify-fix loop this checklist's first entry points back to.
- [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) — the full treatment of warm-up, iteration count, and measurement noise.
- [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) — what `CUDA_CHECK` does with the status these calls return.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
