---
id: metrics-that-matter
title: Metrics That Matter
sidebar_label: Metrics That Matter
sidebar_position: 5
tags: [gpu, cuda, tooling, metrics]
---

# Metrics That Matter

[Nsight Compute](./nsight-compute.md) organizes hundreds of hardware counters into sections; Speed of Light tells you whether a kernel is memory-bound, compute-bound, or latency-bound, but not which specific resource inside that category is the bottleneck. This page is the metric-by-metric reference for answering that second question — the counters worth reading once Speed of Light has pointed at a direction, what a good value looks like, and what to change when it isn't.

## The short list

Eight metrics cover the great majority of kernels. Each entry below gives the exact Nsight Compute metric name, what it measures, the direction that's good, and the lever to pull when it isn't.

## Achieved occupancy

`sm__warps_active.avg.pct_of_peak_sustained_active` reports the average number of resident warps per SM as a percentage of the hardware maximum, sampled across the kernel's actual run rather than computed from the register/shared-memory/thread-slot limits the way theoretical occupancy is. High is good only insofar as the kernel has latency to hide — see [Metrics that mislead](#metrics-that-mislead) below for the case where a high number means nothing. If it's low and the kernel is latency-bound (plenty of stall cycles, no other roofs in the way), the fix is the same lever set as [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md): fewer registers per thread via `__launch_bounds__`, less shared memory per block, or a different block size.

## DRAM throughput

`dram__throughput.avg.pct_of_peak_sustained_elapsed` is achieved HBM bandwidth as a percentage of the device's peak. For a memory-bound kernel this is close to the actual ceiling — a number well below 100% with Speed of Light already showing memory-bound means bytes are being wasted somewhere between the warp's request and DRAM, not that more bandwidth is available to chase. The fix is reducing bytes moved: better coalescing, vectorized loads, or more on-chip reuse via [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) — not raising occupancy, which [Common Antipatterns](../07-kernel-optimization/common-antipatterns.md) already calls out as ineffective once DRAM itself is the ceiling.

## Compute (SM) throughput

`sm__throughput.avg.pct_of_peak_sustained_elapsed` is the compute-side counterpart, issued-instruction throughput as a percentage of the SM's peak. High alongside low DRAM throughput confirms compute-bound; both low with neither near its roof is the latency-bound case Speed of Light can only hint at and this metric, paired with achieved occupancy, confirms. If it's the limiter, the fix is instruction-level: fewer wasted instructions (redundant address arithmetic, avoidable type conversions), a cheaper instruction mix, or moving eligible work onto tensor cores.

## L2 hit rate

`lts__t_sector_hit_rate.pct` is the fraction of L2 requests served from cache rather than forwarded to DRAM. A low hit rate on a kernel that should have reuse — a stencil, a tiled matmul's boundary tiles, anything with a working set that should fit in the tens of megabytes modern L2 offers — means the access pattern is defeating the cache, often through poor locality between successive thread blocks. A low hit rate on a kernel with genuinely no reuse (streaming SAXPY) is expected and not a problem to chase. The fix, when it is a problem, is reordering work so blocks that touch the same data run closer together in time, or explicit shared-memory reuse that removes the traffic from the L2 path entirely.

## Global load efficiency

Not a single metric but a ratio: `l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum` divided by `l1tex__t_requests_pipe_lsu_mem_global_op_ld.sum` gives sectors touched per load request. A warp's coalesced 32-bit load ideally touches the minimum number of 32-byte sectors the access pattern requires; a ratio much higher than that minimum means the warp's addresses are scattered across more cache lines than necessary, and DRAM traffic is inflated accordingly. This is the same coalescing efficiency [Nsight Compute](./nsight-compute.md)'s Memory Workload Analysis section surfaces as a chart — the two named metrics here are what that chart is built from. The fix is the memory-access-pattern work in [Memory Access Optimization](../07-kernel-optimization/memory-access-optimization.md): align accesses, use vectorized loads, or restructure indexing so consecutive threads touch consecutive addresses.

## Shared-memory bank conflicts

`l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` and `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_st.sum` count shared-memory load and store accesses, respectively, that serialized because multiple threads in a warp addressed the same bank — read both; a kernel can conflict on one direction and not the other. Zero or near-zero on each is the target; any sustained nonzero count on a kernel that uses shared memory heavily is worth chasing, because a conflict serializes what should be a single-cycle broadcast into multiple cycles. [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md)'s `TILE + 1` padding is the standard fix for the column-read pattern that causes this most often; the general fix is changing the stride between threads' addresses so it's no longer a multiple of the bank count.

## Warp stall reasons

`smsp__average_warps_issue_stalled_*_per_issue_active.ratio` is a family of metrics, one per stall reason (`long_scoreboard` for a memory dependency, `barrier` for `__syncthreads()`, `short_scoreboard` for a shared-memory or fixed-latency dependency, and several more), each reporting the average number of warps stalled for that specific reason per active issue cycle. There's no single "good" value — this family exists to break down *why* a low compute-throughput, low-occupancy kernel is idle, not to be read in isolation. Whichever stall reason dominates points directly at the fix: `smsp__average_warps_issue_stalled_long_scoreboard_per_issue_active.ratio` dominant means go back to the DRAM-throughput and coalescing metrics above; `smsp__average_warps_issue_stalled_barrier_per_issue_active.ratio` dominant means threads within a block are imbalanced across a `__syncthreads()`; `smsp__average_warps_issue_stalled_short_scoreboard_per_issue_active.ratio` dominant often means a dependent-instruction chain that more ILP (see the high-ILP case in [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md)) or more resident warps could hide.

## Register spills

Not a single Nsight counter but two things read together: `local_load`/`local_store` traffic (nonzero means the kernel is spilling), and the stack-frame size `nvcc -Xptxas -v` reports at compile time. A spill means the compiler couldn't fit a thread's live values in the register budget and pushed the excess to local memory, which physically lives in DRAM — a spill is real, extra DRAM traffic hiding behind what looks like ordinary register usage. Good is zero; any nonzero local-memory traffic on a kernel that wasn't intentionally register-capped with `__launch_bounds__` is worth investigating. The fix is reducing live state per thread (fewer simultaneous accumulators, smaller unroll factor) or, if the spill was self-inflicted by a `__launch_bounds__` register cap set too aggressively, relaxing that cap — see the tradeoff in [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md).

## Metrics that mislead

Three ways to read a correct number and draw the wrong conclusion. **Theoretical occupancy quoted without achieved occupancy** — theoretical occupancy is a ceiling computed from register/shared-memory/thread-slot limits before the kernel ever runs; it says nothing about whether that many warps were actually resident in practice, and a large gap between the two (see the tip in [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md)) usually means load imbalance, not a resource limit worth tuning. **Instructions-per-cycle without knowing the limiter** — a high IPC looks like a healthy, busy kernel, but IPC counts *any* issued instruction, including address arithmetic and predicated-off work; a kernel can have high IPC while still being memory-bound, because the instructions being issued quickly aren't the ones that determine the runtime. **Any percentage measured on a kernel too short to be sampled reliably** — Nsight Compute's counters are collected over the kernel's actual execution window, and a kernel lasting only a handful of microseconds gives the sampling hardware too few cycles to produce a stable percentage; a metric that jumps between runs on the same input is usually this, not a real change in behavior.

:::tip[Read Speed of Light first]
Read Speed of Light first and let it choose which of these to look at — collecting everything on a big kernel is slow (see [Nsight Compute](./nsight-compute.md)'s section-set cost warning) and rarely informative when most of what it collects doesn't apply to the bottleneck this kernel actually has.
:::

## See also

- [Nsight Compute](./nsight-compute.md) — the tool these metrics come from and the Speed of Light classification that picks which ones to read.
- [Roofline in Practice](./roofline-in-practice.md) — turning the FLOP and byte counters from this page into a single measured point.
- [Memory-Bound vs Compute-Bound](../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md) — the classification these metrics provide the evidence for.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
