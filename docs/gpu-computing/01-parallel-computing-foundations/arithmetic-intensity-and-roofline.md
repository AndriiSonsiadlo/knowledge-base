---
id: arithmetic-intensity-and-roofline
title: Arithmetic Intensity and the Roofline Model
sidebar_label: Roofline Model
sidebar_position: 4
tags: [gpu, parallelism, roofline, performance]
---

# Arithmetic Intensity and the Roofline Model

Every kernel is limited by one of two things before it is limited by anything else: how fast the device can do arithmetic, or how fast the device can move bytes from DRAM. Which one applies is a property of the kernel's own math, computable on paper before you write a line of CUDA, and it determines almost everything about how you should spend optimization effort afterward. The roofline model is the tool that turns "which one applies" into a single number you can compute and a single plot you can place it on.

## Arithmetic intensity

**Arithmetic intensity (AI)** is the ratio of floating-point operations performed to bytes moved from DRAM to perform them:

```text
AI = FLOPs / bytes moved from DRAM
```

"Bytes moved from DRAM" means exactly that — traffic that actually crosses to or from device memory, not total memory accesses. A value reused from a register, from shared memory, or from cache never touches this count; only the (ideally minimized) traffic that reaches HBM does. That distinction is what makes AI a property of the algorithm *and* how well it's implemented, not of the math alone — the same computation can have very different AI depending on how much reuse the implementation manages to keep on-chip.

### SAXPY

`y[i] = a * x[i] + y[i]` performs one multiply and one add per element — 2 FLOPs. Each element requires reading `x[i]` and the old `y[i]`, then writing the new `y[i]`: three memory operations per element. Using double-precision (8-byte) elements — the classic case most often cited in roofline literature as "DAXPY" — that's:

```text
FLOPs        = 2
bytes moved  = 3 elements x 8 bytes = 24 bytes
AI           = 2 / 24 ≈ 0.083 FLOP/byte
```

(Single-precision SAXPY halves the byte count to 12, doubling the intensity to ≈0.167 FLOP/byte — still deep in memory-bound territory either way.) SAXPY is the textbook example of a kernel where arithmetic is nearly irrelevant: it does almost no computation per byte, so its performance is set entirely by DRAM bandwidth.

### A 3-point stencil

`out[i] = c0*in[i-1] + c1*in[i] + c2*in[i+1]` performs 3 multiplies and 2 adds — 5 FLOPs per output element. What counts as "bytes moved" depends on how much reuse the implementation captures. With no reuse at all — every input reloaded from DRAM for every output that touches it, single-precision, 4-byte elements — each output costs 3 reads plus 1 write:

```text
FLOPs        = 5
bytes moved  = 4 elements x 4 bytes = 16 bytes
AI           = 5 / 16 ≈ 0.31 FLOP/byte
```

But each interior input value is read by three different outputs (`in[i]` feeds `out[i-1]`, `out[i]`, and `out[i+1]`). A shared-memory implementation that caches the input tile on-chip and reuses it across neighbors amortizes that 3x redundancy down to roughly one read and one write per output:

```text
FLOPs        = 5
bytes moved  = 2 elements x 4 bytes = 8 bytes
AI           = 5 / 8 ≈ 0.63 FLOP/byte
```

Same math, same output — nearly double the arithmetic intensity, purely from an implementation choice about what stays on-chip. This is exactly the kind of reuse the roofline model can't see from the source code alone; it has to be measured (see [Limits of the model](#limits-of-the-model) below).

### A tiled SGEMM, tile size 32

Shared-memory-tiled matrix multiply loads a `T x T` tile of each input matrix into shared memory once per phase and reuses each loaded element across `T` multiply-add pairs before moving to the next phase. Per phase, a `T x T` thread block loads `2 * T^2` elements (the two tiles) and performs `T^3` multiply-add pairs — `2 * T^3` FLOPs:

```text
FLOPs        = 2 * T^3
bytes moved  = 2 * T^2 elements x 4 bytes = 8 * T^2 bytes
AI           = (2 * T^3) / (8 * T^2) = T / 4
```

For `T = 32`:

```text
AI = 32 / 4 = 8 FLOP/byte
```

Tiling turns a naive matmul's AI of about 0.25 FLOP/byte (2 FLOPs per multiply-add against 8 bytes for two un-cached loads) into roughly 8 FLOP/byte just by reusing each shared-memory tile 32 times before discarding it — and production kernels (cuBLAS, CUTLASS) push this further still with register-level micro-tiling on top of the shared-memory tile, routinely reaching well into the tens of FLOP/byte. Larger tiles raise AI, at the cost of shared memory and register pressure that can lower occupancy — the tradeoff [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) covers directly.

## The roofline

Plot achievable performance (GFLOPS on the y-axis) against arithmetic intensity (FLOP/byte on the x-axis), both on log scales. Two hardware limits bound every point a kernel can occupy: a horizontal line at the device's peak compute throughput, and a diagonal line of slope 1 (in log-log space) representing peak memory bandwidth — performance equal to `AI x peak bandwidth`, since a kernel that hasn't yet reached the compute ceiling is limited purely by how fast bytes arrive. The two lines meet at a single point; below and to the left of it, the diagonal (memory) line is the binding constraint, and no amount of extra compute throughput would help. Above and to the right, the horizontal (compute) line binds, and no amount of extra bandwidth would help. A kernel's *achieved* performance is plotted as a single point at its measured AI; where that point sits relative to the two lines — and relative to the roofline's peak, not the axis origin — is the entire diagnosis.

## The ridge point

The **ridge point** is where the two lines meet: the arithmetic intensity at which a kernel transitions from memory-bound to compute-bound, assuming it could achieve peak performance in both dimensions:

```text
ridge point = peak FLOPS / peak bandwidth
```

For an NVIDIA H100 SXM (Hopper, compute capability 9.0), with roughly 67 TFLOPS FP32 peak and roughly 3.35 TB/s of HBM3 bandwidth:

```text
ridge point = 67,000 GFLOPS / 3,350 GB/s ≈ 20 FLOP/byte
```

A kernel needs about 20 FLOPs of useful work per byte loaded before FP32 arithmetic throughput becomes the limiting resource on this GPU. All three worked kernels above — SAXPY at ≈0.08–0.17, the stencil at ≈0.31–0.63, even the tiled SGEMM at ≈8 — sit to the left of that ridge point on FP32 hardware: every one of them is memory-bound in this precision. This is not unusual; the ridge point on modern GPUs is high enough, and most real kernels' AI low enough, that memory-bound is the default expectation rather than the exception (see [Memory-Bound vs Compute-Bound](./memory-bound-vs-compute-bound.md)).

## Classifying a kernel before you touch it

The workflow the numbers above support: compute AI from the algorithm on paper, compare it against the target GPU's ridge point, and let that comparison decide where optimization effort goes *before* profiling confirms it. AI well below the ridge point means the kernel is fundamentally memory-bound — no amount of arithmetic optimization (fewer instructions, faster math, better instruction-level parallelism) moves its ceiling; only reducing bytes moved (better coalescing, more reuse, lower-precision storage) does. AI near or above the ridge point means the opposite: arithmetic efficiency, occupancy, and instruction throughput are worth tuning, because bandwidth is already not the constraint. This paper estimate is a starting hypothesis, not a verdict — the measured version, using actual achieved bandwidth and actual achieved FLOPS rather than datasheet peaks, is covered in [Roofline Analysis in Practice](../09-tooling-profiling-and-debugging/roofline-in-practice.md).

:::warning[What the model can't see]
The roofline model has three blind spots worth remembering before you trust it too far. It says nothing about **latency-bound** kernels — a kernel with plenty of arithmetic intensity but too little parallelism to keep the pipeline full can sit far below both roofs, for a reason the model doesn't represent at all (see [Memory-Bound vs Compute-Bound](./memory-bound-vs-compute-bound.md), which covers this as a third case alongside memory- and compute-bound). It can't see **cache reuse** — the stencil example above showed the same algorithm's AI nearly doubling purely from an implementation detail invisible in the FLOP count; the model only reflects reuse you've already achieved and measured, not reuse that's theoretically possible. And it ignores **instruction mix** — a kernel dominated by integer address arithmetic, special-function unit transcendentals, or a mix of precisions doesn't have a single "peak FLOPS" the simple horizontal line can represent accurately.
:::

## Limits of the model

None of this makes the model wrong to use — it makes it a first-order filter, not a final answer. Use it to decide, in minutes and without touching a profiler, whether an optimization campaign should target bytes moved or instructions issued. Use the tools in [Tooling, Profiling, and Debugging](../09-tooling-profiling-and-debugging/roofline-in-practice.md) to replace the paper estimate with a measured one once the kernel exists.

## See also

- [Memory-Bound vs Compute-Bound](./memory-bound-vs-compute-bound.md) — turning the ridge-point comparison into a concrete diagnostic procedure with real profiler metrics.
- [Latency, Throughput, and Latency Hiding](./latency-throughput-and-hiding.md) — why a kernel can miss both roofs entirely, and what to check first.
- [Roofline Analysis in Practice](../09-tooling-profiling-and-debugging/roofline-in-practice.md) — the measured version of this model, built from real profiler output instead of datasheet peaks.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
