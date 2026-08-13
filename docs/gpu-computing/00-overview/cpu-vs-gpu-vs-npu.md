---
id: cpu-vs-gpu-vs-npu
title: CPU vs GPU vs NPU
sidebar_label: CPU vs GPU vs NPU
sidebar_position: 2
tags: [gpu, overview, npu, comparison]
---

# CPU vs GPU vs NPU

A modern laptop, phone, or server node contains all three of these, and they are not three points on a speed scale. They are three different answers to the question "how much of this chip should be general-purpose?" The CPU keeps every option open and pays for it in area and energy. The GPU gives up per-thread cleverness to buy arithmetic width, but stays fully programmable — you can still write an arbitrary kernel. The NPU gives up general programmability as well, hard-wiring a small set of tensor operations at fixed precisions, and gets back an energy-per-operation figure neither of the others can approach.

The consequence is that "which is fastest" is the wrong framing. Each is fastest on the workload shaped like the assumptions baked into its silicon, and each degrades sharply — often to *worse than the CPU* — when the workload violates them. This page is about recognising the shape of a workload before you pick hardware for it.

## Three design points

**The CPU is a latency machine.** It is optimised to finish one dependent instruction chain as quickly as possible, using out-of-order execution, speculation, and a deep cache hierarchy to keep a small number of threads moving through irregular, branchy code. Nothing about a CPU assumes your work is parallel; it assumes it is *unpredictable*. For how that machinery works, see [Superscalar and Out-of-Order Execution](../../computer-science/cpu-architecture/superscalar-and-out-of-order-execution.md).

**The GPU is a throughput machine.** It assumes thousands of independent work items and applies the same instruction across a warp of 32 threads at a time, hiding memory latency by keeping many warps resident and switching between them for free. It remains a general-purpose processor — you write arbitrary C++ that runs on it — but the model only performs when your problem supplies the parallelism it assumes.

**The NPU is a dataflow machine.** It is built around a systolic array or comparable fixed dataflow that streams weights and activations through a grid of multiply-accumulate units, typically at INT8, INT4, or FP8, with an on-chip scratchpad and a compiler that schedules the whole graph ahead of time. It has no warps, no dynamic scheduling, and often no meaningful floating-point path. What it has is MACs per watt.

That last point is the one to internalise. **An NPU trades programmability for energy per MAC.** It is why every recent phone SoC ships one — a phone cannot afford to run a vision or language model on its GPU at the power that would take, but it can afford the same model on a fixed-function engine drawing a fraction of it. And it is why the same design decision produces the NPU's characteristic failure mode: an operator the hardware does not implement, or a tensor shape the compiler cannot tile, does not run slowly on the NPU — it **falls back to the CPU**, complete with a round trip through the graph partitioner. One unsupported layer in the middle of a network can produce more fallback overhead than the accelerated layers saved. Deploying to an NPU is therefore mostly an exercise in checking operator coverage, not in tuning; see [What Is an NPU](../12-npu-and-inference-accelerators/what-is-an-npu.md).

## Control logic and flexibility

The three differ most in what happens when the code does something unexpected.

On a CPU, an unpredictable branch costs a mispredict penalty of roughly 15–20 cycles and execution continues. On a GPU, a branch where some threads in a warp go one way and some the other causes both paths to be executed in sequence with the inactive threads masked off — the cost is the *sum* of the paths, not the max. From compute capability 7.0 (Volta) onward, independent thread scheduling lets threads in a warp maintain separate program counters, which makes some previously-illegal patterns correct, but it does not make divergence free; the throughput cost stays. See [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md).

On an NPU there is frequently no data-dependent control flow at all inside the accelerated region. The graph is compiled to a static schedule; conditionals, dynamic shapes, and loops with runtime trip counts either get lowered into something the hardware can express or force a partition boundary. This is why NPUs excel at a fixed convolutional or transformer inference graph and are useless for anything resembling general computation.

## Parallelism and memory

The unit of parallelism differs, and it determines the granularity at which you have to think.

A CPU's unit is the SIMD lane inside a thread — 8 FP32 lanes for AVX2, 16 for AVX-512 — with thread-level parallelism layered on top by the OS scheduler. A GPU's unit is the warp: 32 threads issuing in lockstep, grouped into blocks that share a scratchpad, grouped into a grid. An NPU's unit is a tile of a tensor, sized to the physical dimensions of the MAC array.

Memory follows the same pattern. The CPU has a hardware-managed cache hierarchy that you influence only indirectly through access order. The GPU has caches *and* a software-managed scratchpad, shared memory, that you allocate and populate explicitly — it is fast, small, and one of the main levers of kernel optimization. The NPU typically has no cache hierarchy at all, just an explicitly-managed on-chip buffer whose contents the compiler decides at build time.

| | CPU | GPU | NPU |
|---|---|---|---|
| Execution model | Out-of-order superscalar, speculative, few threads | SIMT — warps of 32 threads, in-order issue, massive oversubscription | Fixed dataflow through a MAC array, statically scheduled by a compiler |
| Unit of parallelism | SIMD lane within a thread (AVX2 8×FP32, AVX-512 16×FP32) | Warp of 32 threads; blocks and grids above it | Tile of a tensor, sized to the array dimensions |
| Typical precisions | FP64, FP32, some BF16/INT8 via extensions | FP64/FP32/TF32/BF16/FP16/FP8 on tensor cores; FP4 on Blackwell | INT8 and INT4 primarily; FP16/FP8 on larger parts; FP32 rare or absent |
| Memory system | Hardware-managed L1/L2/L3, ~100 GB/s class DRAM per socket | HBM or GDDR at ~1–8 TB/s, plus explicit per-block shared memory | Small on-chip SRAM buffer, compiler-managed; often shares system DRAM |
| Programmability | Anything — arbitrary code, any language | Arbitrary kernels in CUDA C++/HIP/SYCL, with a parallel structure imposed | Only what the compiler supports; unsupported ops fall back to CPU |
| Best-fit workload | Branchy, serial, latency-sensitive, irregular data structures | Large regular data-parallel work: dense linear algebra, training, simulation | A fixed quantized inference graph running continuously at low power |
| Worst-fit workload | Bulk dense arithmetic over millions of elements | Small problems, deep dependency chains, per-iteration host round trips | Anything dynamic, high-precision, or using an unimplemented operator |

:::tip[Triage rule]
Branchy and serial → CPU. Large, regular, data-parallel → GPU. A fixed quantized inference graph that must run at low power → NPU. If a workload does not clearly fall into one of those three, it usually belongs on the CPU until profiling proves otherwise.
:::

## Which workloads land where

Compilers, parsers, business logic, database query planning, OS work, and anything dominated by pointer chasing belong on the CPU — not as a fallback, but because branch prediction and large private caches are genuinely the right hardware for them.

Neural network *training* belongs on the GPU essentially without exception. Training needs FP32/BF16 range, backward passes, dynamic graphs, and frequent changes to the model code; NPUs implement none of that well. So do dense linear algebra, FFTs, ray tracing, molecular dynamics, and Monte Carlo — anything with enough independent work to fill the machine and enough arithmetic per byte to be worth the transfer.

Inference splits by deployment. A batched server workload with a large model stays on the GPU, where memory bandwidth and tensor-core throughput dominate. A single-stream, always-on model on a phone, camera, or laptop — wake-word detection, background blur, on-device transcription, small quantized language models — goes to the NPU, because the constraint there is milliwatts, not milliseconds. See [Edge NPUs](../12-npu-and-inference-accelerators/edge-npus.md).

## Where they overlap

The boundaries are softer than the table suggests, and getting softer.

GPUs absorbed the NPU's job partially: tensor cores are themselves fixed-function matrix units bolted into a programmable machine, and NVIDIA ships a genuine fixed-function inference engine (the DLA) alongside the SMs on Jetson parts. CPUs absorbed some of it too — Arm's SME and Intel's AMX add matrix instructions directly to the core, which makes small-batch inference on the CPU more competitive than it used to be. Meanwhile NPUs keep growing programmable escape hatches, because operator coverage is their binding constraint and vendors would rather add a small DSP than lose a model to CPU fallback.

Integrated designs blur it further. On Apple silicon, on a Snapdragon SoC, and on NVIDIA's Jetson and Grace-Hopper parts, CPU, GPU, and accelerator share one physical memory, which removes the transfer cost that dominates discrete-GPU decision-making. On those systems the choice between engines is about energy and operator support rather than about who owns the data — a genuinely different calculus from a PCIe-attached datacenter GPU.

## See also

- [Why GPUs Exist](./why-gpus-exist.md) — the transistor-budget argument this page extends to a third design point.
- [The Accelerator Landscape](./the-accelerator-landscape.md) — who ships which of these, and the software stack each implies.
- [What Is an NPU](../12-npu-and-inference-accelerators/what-is-an-npu.md) — the dataflow architecture and its operator-coverage problem in full.
- [Superscalar and Out-of-Order Execution](../../computer-science/cpu-architecture/superscalar-and-out-of-order-execution.md) — the CPU-side machinery a GPU deliberately omits.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
