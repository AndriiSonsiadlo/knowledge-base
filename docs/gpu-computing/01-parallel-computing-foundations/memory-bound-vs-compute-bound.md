---
id: memory-bound-vs-compute-bound
title: Memory-Bound vs Compute-Bound
sidebar_label: Memory vs Compute Bound
sidebar_position: 5
tags: [gpu, parallelism, bandwidth, performance]
---

# Memory-Bound vs Compute-Bound

Knowing a kernel's arithmetic intensity puts it on the roofline plot in theory; knowing whether it is actually memory-bound or compute-bound in practice requires measuring the running kernel, because achieved bandwidth and achieved compute throughput are never the datasheet peaks the paper estimate assumed. This page turns the roofline classification from [Arithmetic Intensity and the Roofline Model](./arithmetic-intensity-and-roofline.md) into a concrete diagnostic you run against a profiler, and adds the case the roofline model doesn't represent at all.

## How to tell which you are

Two profiler metrics settle the question directly: how close the memory system is running to its peak, and how close the compute pipelines are running to theirs. If one is high and the other low, the high one is your limiter. If both are low, neither hardware limit is binding — something else is stalling the kernel. If both are high, the kernel is already using the hardware well and further gains require a genuinely different approach, not tuning.

| Symptom | Likely limiter | First thing to try |
|---|---|---|
| High DRAM throughput, low SM busy | Memory-bound | Reduce bytes moved: improve coalescing, increase reuse, use a narrower data type |
| High SM busy, low DRAM throughput | Compute-bound | Reduce instruction count or improve instruction-level parallelism; consider tensor cores if applicable |
| Both low | Latency-bound (see below) | Raise occupancy or increase independent work per thread |
| Both high | Neither — kernel is near the roofline | Change algorithm or precision; incremental tuning has little left to give |

## Why most kernels are memory-bound

The ridge point computed in [Arithmetic Intensity and the Roofline Model](./arithmetic-intensity-and-roofline.md) — around 20 FLOP/byte for an H100 SXM in FP32 — sets a high bar, and most real kernels don't clear it. Elementwise operations, reductions, transposes, sparse operations, and even a well-tiled SGEMM in FP32 (≈8 FLOP/byte, computed on that same page) fall short of it. This isn't a sign of badly written kernels; it reflects how much peak compute throughput has grown relative to peak bandwidth across GPU generations — FLOPS have scaled faster than bytes/second, pushing the ridge point steadily rightward and pulling more of the kernel population onto the memory-bound side of it with each generation. Tensor-core paths push the effective compute peak even higher for the operations that can use them, widening the gap further for anything that can't.

Use Nsight Compute's actual metric names when reading a profile rather than eyeballing a "% of peak" summary bar — the two that matter here are `dram__throughput.avg.pct_of_peak_sustained_elapsed` (DRAM bandwidth utilization) and `sm__throughput.avg.pct_of_peak_sustained_elapsed` (SM compute utilization). Both are covered with their full context, related sub-metrics, and how to read them in the Nsight Compute UI in [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).

## What each diagnosis implies

A memory-bound diagnosis (high `dram__throughput...`, low `sm__throughput...`) means the fix lives in the memory system, not the math: check coalescing first, since uncoalesced access patterns can cost an order of magnitude of effective bandwidth on their own; then look at whether data reused across threads can move into shared memory instead of hitting DRAM repeatedly; then check whether a narrower type (FP16, INT8, or a packed format) can carry the same information in fewer bytes. None of this touches the arithmetic — a memory-bound kernel can have its floating-point instructions rewritten to be twice as clever and finish in exactly the same time, because arithmetic was never the bottleneck.

A compute-bound diagnosis (high `sm__throughput...`, low `dram__throughput...`) means the opposite set of levers apply: reduce instruction count, check whether the kernel is leaving throughput on the table by not using tensor cores for an operation that maps onto them, check the mix of FP32/FP64/special-function-unit instructions for one that's disproportionately expensive, and check for warp divergence eating issue slots (see [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md)). Buying more memory bandwidth would do nothing for this kernel; it was never waiting on DRAM.

## The third case: latency-bound

Both metrics low is the case the roofline model has no axis for, because roofline assumes the kernel is at least *trying* to run at either the compute or bandwidth ceiling and only asks which one binds. A kernel can fail to approach either ceiling for a reason that has nothing to do with how much arithmetic or bandwidth it needs per byte: too few threads, or too few resident warps, to keep the pipeline supplied with ready work. That's an occupancy and latency-hiding problem, not a roofline problem — see [Latency, Throughput, and Latency Hiding](./latency-throughput-and-hiding.md) for the mechanism and [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) for the fix. Symptoms include a grid too small to fill the device, a kernel with heavy register or shared-memory usage per thread limiting resident warps, or a dependency chain within each thread long enough that there simply isn't enough independent work to overlap with a stall.

:::tip["Both low" is the most common and most misdiagnosed case]
It's tempting to read low DRAM and low SM utilization as "the kernel is fine, it's just small" and move on. More often it means occupancy is too low to hide latency, and the fix — more resident warps, more independent work per thread, a bigger launch — is straightforward once you recognize the pattern instead of assuming the profiler numbers are simply uninteresting.
:::

## See also

- [Arithmetic Intensity and the Roofline Model](./arithmetic-intensity-and-roofline.md) — the paper estimate this page turns into a measured diagnosis.
- [The Optimization Workflow](../07-kernel-optimization/the-optimization-workflow.md) — where this diagnosis fits into the broader tuning loop.
- [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md) — the full Nsight Compute metric reference, including both metrics named above.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
