---
id: events-and-timing
title: Events and Timing
sidebar_label: Events & Timing
sidebar_position: 5
tags: [gpu, cuda, runtime, timing]
---

# Events and Timing

A `cudaEvent_t` is a marker that can be dropped into a stream and later queried, waited on, or used to measure elapsed time between two points — it's the mechanism behind both accurate kernel timing and dependencies between streams that don't require the host to get involved. Both uses matter here: naive host-clock timing of GPU work produces numbers that look plausible and are wrong, and coordinating streams without a host round-trip is what makes the concurrency from [Streams and Concurrency](./streams-and-concurrency.md) composable into a real pipeline. See [Error Handling and Checking](./error-handling.md) for what `CUDA_CHECK` does with the status these calls return.

## Events as markers

`cudaEventCreate` allocates an event; `cudaEventRecord(event, stream)` inserts it into a stream at the point in the queue where it was issued — the event becomes "occurred" only once every operation issued into that stream before it has completed. `cudaEventQuery` checks non-blockingly whether it has occurred yet, and `cudaEventSynchronize` blocks the host until it has.

## Timing a kernel correctly

This is the pattern the rest of this section refers back to:

```cpp showLineNumbers
cudaEvent_t start, stop;
CUDA_CHECK(cudaEventCreate(&start));
CUDA_CHECK(cudaEventCreate(&stop));

myKernel<<<grid, block>>>(/* ... */);        // warm-up: JIT, cache, clocks
CUDA_CHECK(cudaDeviceSynchronize());

CUDA_CHECK(cudaEventRecord(start));
for (int i = 0; i < iters; ++i) myKernel<<<grid, block>>>(/* ... */);
CUDA_CHECK(cudaEventRecord(stop));
CUDA_CHECK(cudaEventSynchronize(stop));

float ms = 0.0f;
CUDA_CHECK(cudaEventElapsedTime(&ms, start, stop));
printf("%.3f ms/iter\n", ms / iters);
```

Three details make this correct rather than merely plausible: the untimed warm-up launch pays for JIT compilation, cache population, and clock ramp-up before the clock starts; the timed region runs several iterations rather than one, so per-launch overhead and jitter average out; and `cudaEventElapsedTime` measures GPU-side time between the two markers, not host wall-clock time around the launches.

## Cross-stream dependencies

An event recorded in one stream can be waited on from another with `cudaStreamWaitEvent`, making stream B's next operation wait for stream A to reach the recorded point — without the host synchronizing anything:

```cpp showLineNumbers
cudaEvent_t ready;
CUDA_CHECK(cudaEventCreate(&ready));

producerKernel<<<grid, block, 0, streamA>>>(/* ... */);
CUDA_CHECK(cudaEventRecord(ready, streamA));

CUDA_CHECK(cudaStreamWaitEvent(streamB, ready, 0));
consumerKernel<<<grid, block, 0, streamB>>>(/* ... */);
```

`consumerKernel` won't start until `producerKernel` has completed, but the host issues both launches without blocking on either — this is how a dependency graph between streams gets expressed without a host-side `cudaDeviceSynchronize` collapsing all the concurrency the streams exist to provide.

## Why wall-clock timing lies

A kernel launch is asynchronous: the host call returns as soon as the launch is enqueued, not when the kernel finishes running. Wrapping a host timer (`std::chrono`, `clock()`) directly around a launch measures how long it took to *enqueue* the work, which is usually a few microseconds regardless of what the kernel actually does — the number looks like a measurement and is really just launch overhead. Getting a real duration from host timers requires forcing a synchronization point (`cudaDeviceSynchronize`) before stopping the clock, and even then the result includes host-side scheduling noise that event timing avoids by measuring entirely on the GPU's own clock.

## Polling versus blocking

`cudaEventSynchronize` blocks the calling host thread until the event occurs; by default that block spins, consuming a CPU core, which minimizes wake-up latency at the cost of burning cycles the thread could otherwise yield. `cudaEventCreateWithFlags(&e, cudaEventBlockingSync)` trades that spin for a real OS-level wait, giving the CPU back to other work at the cost of slightly higher wake-up latency once the event occurs.

:::note[Cheaper events for pure dependencies]
An event used only for `cudaStreamWaitEvent`-style dependencies, never for timing, should be created with `cudaEventCreateWithFlags(&e, cudaEventDisableTiming)` — timing support has bookkeeping cost the driver can skip when nothing ever calls `cudaEventElapsedTime` on it. `cudaEventBlockingSync` (above) is a separate, orthogonal flag for how the host waits, not for whether the event supports timing.
:::

:::warning[Event timing still measures the queue, not just the kernel]
An event-timed interval includes any queueing delay if other work is already sitting in the same stream ahead of the timed launches — the numbers reflect what the stream actually did, not an isolated kernel in a vacuum. GPU clocks also boost gradually after idle periods, so the first few timed iterations of a "cold" run can run measurably slower than steady state and skew an average taken too early. [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) covers isolating a kernel's own cost and handling clock-boost warm-up properly.
:::

## See also

- [Streams and Concurrency](./streams-and-concurrency.md) — the stream ordering that events mark points within.
- [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) — turning this page's timing pattern into a repeatable, trustworthy benchmark.
- [The Optimization Workflow](../07-kernel-optimization/the-optimization-workflow.md) — where kernel timing fits into deciding what to optimize next.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
