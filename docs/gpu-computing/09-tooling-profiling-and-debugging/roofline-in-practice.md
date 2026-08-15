---
id: roofline-in-practice
title: Roofline Analysis in Practice
sidebar_label: Roofline in Practice
sidebar_position: 6
tags: [gpu, cuda, tooling, roofline]
---

# Roofline Analysis in Practice

[Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) builds the model from datasheet peaks and a paper estimate of FLOPs and bytes — a first-order filter you can apply before a kernel even runs. This page replaces every number in that estimate with one measured from a real execution: the FLOPs a kernel actually issued, the bytes it actually moved, and the roofs the hardware actually achieves rather than what its spec sheet claims.

## From counters to a point

Four Nsight Compute counters and one arithmetic step turn a profiled kernel into a single roofline point. FLOPs come from the `smsp__sass_thread_inst_executed_op_*_pred_on.sum` family — `_fadd_`, `_fmul_`, and `_ffma_` for the three floating-point instruction classes, counted only for predicated-on (actually executing) threads. A fused multiply-add does two FLOPs in one instruction, so the combination is:

```text
FLOPs = fadd_count + fmul_count + 2 x ffma_count
```

Dropping the factor of two on the FMA term is the single most common mistake in a hand-rolled roofline calculation — it silently halves every intensity and throughput number for any kernel that uses FMA, which is nearly all of them. Bytes moved come from `dram__bytes.sum`, total DRAM traffic in both directions for the kernel's duration — reads and writes together, matching the "bytes moved from DRAM" definition the conceptual model uses. Arithmetic intensity is their ratio, and achieved performance is FLOPs divided by the kernel's measured duration:

```text
AI            = FLOPs / dram__bytes.sum
achieved FLOP/s = FLOPs / kernel duration
```

Kernel duration here should come from the same profiled run the FLOP and byte counters came from, not a separately timed run — mixing a profiled counter with a wall-clock duration from an unprofiled run conflates two different executions of the kernel.

## Getting the machine's roofs

The compute roof is the device's peak FLOP/s from its spec sheet — the number [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) already uses for the ridge-point calculation, and there's little to measure here beyond picking the right precision (FP32, FP64, or tensor-core throughput, whichever the kernel actually issues). The bandwidth roof is different: use *measured* bandwidth from a small streaming kernel (a plain copy or SAXPY, timed the same way this kernel was), not the datasheet's headline bandwidth number. Datasheet bandwidth assumes ideal, back-to-back, fully coalesced access to every DRAM channel simultaneously — real kernels, including a simple streaming one, land measurably below it because of refresh cycles, ECC overhead where enabled, and imperfect channel utilization. Placing a kernel's point against a roof it's mathematically impossible to reach makes every kernel look worse than it is and can hide real headroom; placing it against the bandwidth a streaming kernel actually achieves on the same GPU gives a roof the kernel being analyzed could realistically approach.

## Placing the kernel

With AI and achieved FLOP/s from [From counters to a point](#from-counters-to-a-point) and both roofs from [Getting the machine's roofs](#getting-the-machines-roofs), the point is `(AI, achieved FLOP/s)` on the same log-log axes the conceptual model plots. Where it lands relative to the two roofline segments is the whole diagnosis:

| Where the point lands | What it means | Next move |
|---|---|---|
| Under the diagonal (bandwidth-bound, below achievable) | The kernel is memory-bound and isn't even hitting the bandwidth a streaming kernel gets on this GPU | Improve coalescing or add reuse — the gap to the diagonal itself is wasted bytes, not a compute problem |
| On the diagonal | The kernel is bandwidth-bound and already moving bytes as efficiently as this GPU allows | Raise arithmetic intensity by tiling or fusing — more bytes reused per load, not faster loads |
| Under the horizontal roof | The kernel has enough intensity to be compute-bound but isn't reaching peak compute throughput | Improve instruction mix, reduce non-arithmetic overhead, or move eligible work onto tensor cores |
| On the roof | The kernel is at the compute ceiling for this precision | Stop — the only way past this point is a different algorithm, a lower precision, or different hardware |

## Reading the position

A point under the diagonal and a point on the diagonal require different fixes even though both are "memory-bound" in the coarse sense [Memory-Bound vs Compute-Bound](../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md) uses — the diagonal position tells you whether the kernel's actual problem is wasted bytes (fixable with coalescing) or fundamental intensity (fixable only by restructuring the algorithm to reuse more). A point far below both roofs, with plenty of intensity and plenty of headroom under the bandwidth line too, is the latency-bound case the plain roofline model can't diagnose on its own — that's a signal to go back to [Metrics That Matter](./metrics-that-matter.md)'s occupancy and stall-reason metrics rather than trying to read more out of the roofline plot than it contains.

## The hierarchical roofline

The two-roof picture above treats "bytes moved" as DRAM traffic only, which is the right question for a kernel that hasn't been tiled yet but stops being the interesting question once it has. Adding a second pair of roofs — one built from L2 bandwidth and `dram__bytes.sum` replaced by L2 traffic, another from L1 bandwidth and L1 traffic — turns the single plot into a hierarchical roofline with one point per memory level the kernel actually touches. The reason this matters: tiling is supposed to move traffic off DRAM and onto faster, closer levels, and the DRAM-only roofline can't show whether that actually happened — a kernel's DRAM-level point moving right (higher intensity, less DRAM traffic per FLOP) after adding shared-memory tiling, as in [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md), is exactly what the hierarchical view is built to confirm, while the L1 and L2 points show whether the traffic that left DRAM actually landed on-chip or just moved to a slower intermediate level instead.

:::note[The GUI does this automatically]
Nsight Compute's roofline chart, available with `--set full` (see [Nsight Compute](./nsight-compute.md)), computes and plots exactly this — hierarchical roofs and all — without any of the manual counter arithmetic above. The manual recipe on this page matters when the number needs to go into a script, a CI gate, or a report generated on a platform without the GUI available; reach for `--set full` first when a human is going to read the result interactively.
:::

## See also

- [Metrics That Matter](./metrics-that-matter.md) — the individual counters this page's recipe combines into a single point.
- [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) — the conceptual model and paper estimate this page replaces with measured numbers.
- [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) — the tiling technique the hierarchical roofline is used to verify.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
