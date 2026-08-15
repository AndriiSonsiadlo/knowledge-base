---
id: benchmarking-methodology
title: Benchmarking Methodology
sidebar_label: Benchmarking
sidebar_position: 7
tags: [gpu, cuda, tooling, benchmarking]
---

# Benchmarking Methodology

A benchmark number is easy to produce and easy to produce wrong — every one of the six mistakes below yields a plausible-looking result that is actually measuring something other than the kernel's real performance. This page collects the mechanism behind each mistake and the specific fix, then closes with a checklist meant to be followed literally, not read once and approximated.

## Warm-up

The first launch of a kernel pays costs that no later launch repeats: JIT compilation if no matching SASS shipped in the binary, CUDA context creation, and cold caches with nothing yet resident. [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md)'s timing pattern already puts an untimed launch before the timed region for exactly this reason. The fix is to discard at least the first few iterations — one warm-up launch covers JIT and context creation, but clocks can take noticeably longer to ramp from idle to sustained boost, so a run that starts timing immediately after a single warm-up launch can still be measuring partial clock ramp rather than steady state.

## Locking clocks

GPUs boost above their base clock opportunistically and throttle back down under sustained thermal or power load, which means a kernel run for a long duration can measure slower per-iteration than the same kernel run briefly — not because the work changed, but because the clock did. `nvidia-smi -lgc <freq>` locks the SM clock to a fixed frequency for the duration of the benchmark, removing boost-then-throttle drift as a variable; `nvidia-smi -q -d CLOCK` reports the current clock state and, critically, the active throttle reasons, so a benchmark that looks unexpectedly slow can be checked against whether the GPU was thermally or power throttled during the run rather than blaming the kernel.

:::warning[Unlocked-clock results don't compare]
A result measured with clocks left to boost and throttle freely is a snapshot of that specific run's thermal and power history, not a property of the kernel — it isn't comparable across separate runs on the same machine, let alone across different machines or GPUs. Lock clocks with `nvidia-smi -lgc` before any benchmark whose number is going to be compared against another number.
:::

## Repetition and variance

A single timed iteration, or even a bare mean over several, is vulnerable to one outlier — a scheduler hiccup, a stray interrupt, a moment of clock throttling — pulling the reported number away from what the kernel actually does on a typical run. Report the median and interquartile range across many repetitions instead: the median is insensitive to a single extreme outlier in a way a mean isn't, and the interquartile range communicates how much the result actually varies, which a single number never can.

## Timing correctly

Time with CUDA events around a loop of iterations, exactly as [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md) derives — not a host wall-clock timer wrapped around the launch, which measures how long the asynchronous launch call took to enqueue rather than how long the kernel took to run. The same page's warning applies directly here: an event-timed interval reflects whatever else is queued in the same stream and the clock-boost ramp of a cold GPU, both of which the warm-up and clock-locking steps above are meant to remove before this measurement is trusted.

## Defeating dead-code elimination

If a kernel's result is never read by anything the compiler can see, `ptxas` is free to delete the computation that produced it — [Common Antipatterns](../07-kernel-optimization/common-antipatterns.md) shows exactly this happening to an unused accumulator, and the symptom is a benchmark that reports implausibly, impossibly fast timing because it's timing an empty kernel. Guarantee the result is live by writing it to a device array the host later reads back, or to a `volatile` sink the compiler can't prove is dead:

```cpp showLineNumbers
__global__ void kernel(const float* in, float* out, int n) {
    float acc = 0.0f;
    for (int i = 0; i < n; ++i) acc += in[i];
    out[blockIdx.x * blockDim.x + threadIdx.x] = acc;   // real write — nothing to eliminate
}
```

## Reporting honestly

A number without context is not a result. Always state the GPU model, driver version, CUDA toolkit version, problem size, data type, whether clocks were locked (and to what frequency), and how many iterations were timed. A "2x speedup" claim with no baseline description attached could mean anything from a genuine algorithmic improvement to an unlocked-clock artifact or a different problem size entirely — the reader has no way to tell without the surrounding facts, and reconstructing them later from memory is far harder than recording them at measurement time.

:::tip[Report against a hardware ceiling too]
A raw number only means something to a reader who happens to own the same GPU. Report against a hardware ceiling as well — effective bandwidth as a fraction of the peak measured in [Roofline in Practice](./roofline-in-practice.md), or kernel time as a multiple of a reference implementation's (cuBLAS for GEMM, for instance) — so the result communicates something even to a reader who has never seen your specific hardware.
:::

## A checklist

Each item is meant to be verifiable against the benchmark as run, not a matter of judgment — the applied-kernel pages that measure a kernel's performance follow this list directly.

1. Discarded at least the first few iterations as warm-up before starting the timed region.
2. Locked SM clocks with `nvidia-smi -lgc` and confirmed no active throttle reason with `nvidia-smi -q -d CLOCK`.
3. Timed with CUDA events around a loop of many iterations, not a host wall-clock timer around a single launch.
4. Repeated the timed run enough times to report a median and an interquartile range, not a single number or a bare mean.
5. Verified the benchmarked computation's result is written somewhere the compiler can't prove is unused.
6. Reported GPU model, driver version, CUDA version, problem size, data type, clock-lock state, and iteration count alongside the number.
7. Reported the number against a hardware ceiling (peak bandwidth, a reference-library baseline) as well as in absolute terms.

## See also

- [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md) — the CUDA-event timing pattern this page's warm-up and timing steps build on.
- [Common Antipatterns](../07-kernel-optimization/common-antipatterns.md) — the antipattern list this page's warm-up and dead-code sections match against a real symptom.
- [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md) — an applied kernel measured using this checklist.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
