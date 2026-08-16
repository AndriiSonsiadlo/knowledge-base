---
id: jetson-and-dla
title: NVIDIA Jetson and DLA
sidebar_label: Jetson & DLA
sidebar_position: 5
tags: [gpu, npu, jetson, dla]
---

# NVIDIA Jetson and DLA

Jetson is not a scaled-down GPU with different rules — it is a full CUDA-capable GPU on the same die as an Arm CPU, so everything in folders 03 through 07 of this section applies to it directly: the same programming model, the same memory hierarchy concepts, the same kernel-optimization techniques. What earns Jetson its own page is three differences that change decisions rather than change the programming model: memory is physically shared between CPU and GPU, the power envelope is fixed and small, and a second, fixed-function inference engine — the DLA — sits alongside the GPU on the same package.

## The Jetson platform

A Jetson module packages an Arm CPU, an NVIDIA GPU built from the same SM architecture used in desktop and datacenter parts, and supporting silicon like the DLA and video codecs, all sharing one physical memory pool and one power budget. Because the GPU is architecturally the same family as a desktop card, code written and tuned against [Kernel Optimization](../07-kernel-optimization/the-optimization-workflow.md) or [CUDA Runtime and APIs](../06-cuda-runtime-and-apis/error-handling.md) transfers to Jetson largely unchanged — the differences that matter are platform-level, not programming-model-level.

## Unified memory

This is the single most commonly mis-transferred piece of desktop CUDA knowledge, so it is worth stating plainly: on Jetson, `cudaMallocManaged` allocations need no migration, because there is only one physical memory for CPU and GPU to share in the first place. The whole class of performance trap [Unified Memory](../04-cuda-memory-model/unified-memory.md) warns about on a discrete GPU — page faults triggering an actual copy across a PCIe bus, oversubscription forcing eviction — mostly does not apply on Jetson, because there is no second physical memory to migrate to or from. That does not mean memory allocation stops mattering entirely: pinned or mapped allocation still affects cache coherence traffic between the CPU and GPU caches, so an allocation strategy tuned purely for "avoid migration" on a discrete card is solving a problem Jetson doesn't have while potentially missing the coherence-traffic problem it does have.

## The Deep Learning Accelerator

The DLA is a fixed-function inference engine physically present on many Jetson parts alongside the GPU, and it is reached exclusively through TensorRT rather than through CUDA directly. TensorRT's builder API lets you assign individual layers to it: `config->setDeviceType(layer, DeviceType::kDLA)` marks a layer to run on the DLA instead of the GPU, provided that layer's operation and precision (DLA supports FP16 and INT8) are among the subset TensorRT knows how to lower onto DLA hardware. Layers the DLA doesn't support fall back to the GPU automatically within the same TensorRT engine, the same operator-coverage pattern [What Is an NPU](./what-is-an-npu.md) describes generically, just resolved within a single compiled engine instead of across separate runtimes.

The DLA's value is not raw throughput — the GPU is faster at the same arithmetic in most cases — it's concurrency. Running inference on the DLA leaves the GPU entirely free for other work: rendering, a second model, or additional GPU-side inference, running at the same time as the DLA handles its share of the graph. That makes it most useful in workloads that need to run more than one thing on the SoC simultaneously, such as a perception pipeline where one model runs on the DLA while the GPU is busy with a different stage.

## Power modes and clocks

Jetson's power envelope is fixed by the module and by the active power mode, and both the CPU and GPU clock ranges available to you depend on which mode is selected. `nvpmodel -m <n>` selects one of the module's predefined power/clock profiles — different Jetson modules expose different modes and mode numbers, so `<n>` is board-specific, not a universal value. Within whatever envelope `nvpmodel` selects, clocks still float dynamically under the default DVFS governor; `jetson_clocks` pins CPU, GPU, and memory clocks to the maximum values permitted by the current power mode and disables that dynamic scaling, giving a fixed, repeatable clock state instead of one that ramps and throttles under load.

:::warning[Unfixed power mode makes benchmarks irreproducible]
Running a benchmark without first fixing the power mode with `nvpmodel -m <n>` and locking clocks with `jetson_clocks` means the numbers you get depend on whatever DVFS state the board happened to be in when the run started — a run right after boot and a run after the board has been under load for an hour can differ substantially with identical code. This is the Jetson-specific instance of the general rule in [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md): control the variables you're not trying to measure. On Jetson, power mode and clock state are two of them.
:::

## Thermal limits

Many Jetson modules ship in passively cooled carrier boards, with no fan actively removing heat. Under sustained load, the SoC's temperature rises until thermal throttling kicks in and clocks drop below whatever `jetson_clocks` pinned them to, regardless of the selected power mode.

:::note[Measure sustained throughput, not burst throughput]
A short benchmark run on a passively cooled module can finish before thermal throttling has time to engage, reporting a number the board cannot actually sustain. Burst throughput over a few seconds and sustained throughput over several minutes of continuous load can differ substantially on a module without active cooling. Measure over minutes when the deployment target is passively cooled, not seconds, or the number you report will not match production behavior.
:::

## Developing for Jetson

Day-to-day CUDA development on Jetson looks like desktop CUDA development — the same compiler, the same profiling tools, the same kernel code — with the platform-level differences above layered on top as things to account for rather than a different API to learn. The practical workflow is usually: develop and iterate against the GPU directly using ordinary CUDA tooling, then move latency-tolerant, precision-flexible layers of an inference graph onto the DLA through TensorRT once the model is otherwise working, so the DLA's concurrency benefit is captured without giving up the GPU as the primary, more flexible development target.

## See also

- [TensorRT](./tensorrt.md) — the builder API that DLA layer assignment goes through.
- [Unified Memory](../04-cuda-memory-model/unified-memory.md) — the desktop performance traps that mostly don't apply on Jetson's shared memory.
- [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) — the general reproducibility rules this page's power-mode warning is an instance of.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
