---
id: warps-and-schedulers
title: Warps and Warp Schedulers
sidebar_label: Warps & Schedulers
sidebar_position: 3
tags: [gpu, hardware, warps, scheduling]
---

# Warps and Warp Schedulers

Every SIMT behavior that looks unusual coming from CPU threading — coalescing, divergence, the fact that occupancy is measured in resident warps rather than resident threads — traces back to one hardware fact: the GPU does not issue instructions per thread, it issues them per warp, 32 threads at a time, from a single warp scheduler per sub-partition. This page is about that scheduler: what it decides among, how fast it can issue, and how to read its behavior back out of a profiler.

## Why 32

A warp is a fixed group of 32 threads that a sub-partition's scheduler tracks and issues instructions to as a unit — one instruction, one program counter (subject to independent thread scheduling, below), all 32 lanes in that sub-partition executing it together. 32 is not a tunable parameter; it has been the warp size on every NVIDIA architecture to date, and it sets the SIMT granularity everything else in the programming model is built on: coalescing is about whether a warp's 32 addresses land in few transactions or many, divergence is about a warp's 32 threads disagreeing on which branch to take, and warp-level primitives like `__shfl_sync` operate across exactly this group. From compute capability 7.0 (Volta) onward, independent thread scheduling lets the 32 threads of a diverged warp track separate program counters instead of using an explicit reconvergence stack, which improves correctness and composability of divergent code, but it does not change the underlying cost model: the hardware still issues one instruction to the warp at a time, so a diverged warp still pays for each branch path it executes. [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) covers the mechanics and the cost model in full.

## Eligible, stalled, and selected

At any cycle, every warp resident in a sub-partition is in one of a few states from the scheduler's point of view. A warp is **eligible** if its next instruction's operands are ready and the functional unit it needs is free; among the eligible warps, the scheduler **selects** exactly one (two, with dual issue — see below) to actually issue that cycle. A warp that is not eligible — waiting on a memory request, a barrier, or a dependent register from an earlier long-latency instruction — is **stalled**. This eligible/stalled/selected distinction is the mechanism latency hiding runs on: as described in [Latency, Throughput, and Latency Hiding](../01-parallel-computing-foundations/latency-throughput-and-hiding.md), a stalled warp costs nothing as long as some other resident warp in the same sub-partition is eligible, because switching which warp is selected has zero overhead — every resident warp's registers already live in the register file, so there is nothing to save or restore.

## Issue rate and dual issue

Each sub-partition's scheduler issues at most one instruction per warp per cycle, but on architectures with dual-issue capability it can issue two independent instructions from the same selected warp in one cycle if they target different functional units and have no dependency between them (for example an FP32 op and a memory op). Dual issue increases throughput per scheduler without changing the eligible/stalled/selected model above — it is still one scheduler picking from the same pool of resident warps, just able to keep more of the SM's functional units busy per cycle when the instruction mix cooperates.

## Scheduling as the latency-hiding mechanism

The scheduler does no prediction, no reordering across warps, and no speculation — it is a purely reactive picker among whatever is eligible right now. That simplicity is what makes it fast enough to make a selection every cycle, and it is precisely why occupancy matters: with only a handful of resident warps, there are cycles where none of them happen to be eligible and the scheduler has nothing to select, exposing the stall as lost throughput. With enough resident warps, there is almost always at least one eligible warp to select on any given cycle, and the latency of any individual stalled warp is fully hidden behind the others' progress. [Register File and Occupancy](./register-file-and-occupancy.md) covers what limits how many warps can be resident in the first place.

## Stall reasons you will actually see

Nsight Compute reports, for a profiled kernel, the fraction of cycles each warp spent in each stall reason — this is the most direct way to see the eligible/stalled distinction above turned into concrete numbers.

| Stall reason | What it means |
|---|---|
| `stall_long_scoreboard` | Waiting on a long-latency global or local memory operation to complete. |
| `stall_short_scoreboard` | Waiting on a shorter-latency MIO operation, typically shared memory. |
| `stall_barrier` | Waiting at a `__syncthreads()` (or similar) barrier for other threads in the block to arrive. |
| `stall_not_selected` | Eligible to issue, but a different warp was selected instead. |
| `stall_wait` | Waiting on a fixed-latency dependency, such as a short arithmetic pipeline, to clear. |

These are covered in depth, with how to read them from an actual profile, in [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).

:::tip[A high `stall_not_selected` is a good sign]
`stall_not_selected` means the warp was ready to go but the scheduler chose a different eligible warp instead — the opposite of a warp with nothing to do. A kernel with a high proportion of `stall_not_selected` cycles has more eligible warps than the scheduler can issue in a given cycle, which is exactly the surplus of parallelism that latency hiding needs. If you're chasing performance, `stall_long_scoreboard` and `stall_barrier` are the stall reasons worth reducing; a high `stall_not_selected` fraction is evidence occupancy is already doing its job.
:::

## See also

- [Register File and Occupancy](./register-file-and-occupancy.md) — what determines how many warps are resident for the scheduler to pick among.
- [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) — the full cost model for divergent warps and independent thread scheduling.
- [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md) — reading stall-reason breakdowns from an actual Nsight Compute profile.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
