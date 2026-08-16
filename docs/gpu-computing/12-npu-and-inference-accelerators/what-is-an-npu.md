---
id: what-is-an-npu
title: What Is an NPU?
sidebar_label: What Is an NPU?
sidebar_position: 1
tags: [gpu, npu, accelerators, architecture]
---

# What Is an NPU?

Every accelerator in this section so far has been a variation on "more programmable cores, running in parallel." An NPU (neural processing unit) is a different move entirely: instead of adding parallel general-purpose lanes, it removes almost all of the general-purpose machinery and replaces it with a dataflow of multiply-accumulate (MAC) cells wired specifically for tensor arithmetic. [CPU vs GPU vs NPU](../00-overview/cpu-vs-gpu-vs-npu.md) already introduced this as the third design point; this page works through what that design point actually buys and what it costs.

The short version: an NPU spends almost all of its silicon area on MAC hardware and on-chip weight storage, and almost none on instruction fetch, branch prediction, out-of-order scheduling, or general-purpose memory access. That is a bet that the workload is a fixed, quantized tensor graph known ahead of time — and when the bet is right, the payoff in energy per operation is large.

## The design point

A CPU core devotes most of its transistor budget to figuring out *what* to execute next: branch predictors, reorder buffers, register renaming, speculative execution. A GPU's SM keeps some of that per-thread cleverness but amortizes it across a warp, spending its budget on many parallel ALUs instead. An NPU goes further still: there is no per-instruction fetch/decode/schedule loop at all for the accelerated region. A compiler works out the entire schedule — which MAC cell does what, in which cycle, reading from which buffer — ahead of time, and the hardware just executes that fixed plan.

The consequence is that an NPU's die is dominated by two things: a grid of MAC cells (see [Systolic Arrays and Dataflow](./systolic-arrays-and-dataflow.md) for how that grid is organized) and an on-chip scratchpad sized to hold as many weights and activations as possible without touching DRAM. Control logic, which on a CPU or GPU is a large and power-hungry part of the die, shrinks to a small compiled schedule sequencer.

## Fixed function versus programmable

"Fixed function" does not mean the NPU only ever runs one model — it means the *set of operations* it can execute is fixed by the hardware, and the compiler's job is to map a graph onto that fixed set, not to synthesize arbitrary new operations. A GPU, by contrast, is fully programmable at the instruction level: you can write a kernel that does something the hardware designer never anticipated, and it will run, just possibly slowly. An NPU cannot do that at all — an operation it does not implement in hardware simply does not run on it.

| | GPU (SIMT) | NPU (fixed-function) |
|---|---|---|
| Unit of work | Warp of 32 threads, arbitrary kernel code | Tile of a tensor, moving through a fixed MAC array |
| Control flow support | Full — branches, loops, data-dependent indexing | Little to none inside the accelerated graph; the schedule is compiled ahead of time |
| Precision support | FP64 down to FP4 depending on generation, via tensor cores | INT8/INT4 primarily; FP16/BF16 on larger parts, FP32 rare |
| Memory model | Hardware caches plus an explicit, programmer-managed scratchpad | A single compiler-managed on-chip buffer; no general cache hierarchy |
| Programming interface | CUDA C++/HIP/SYCL — write arbitrary kernels | A graph compiler (Core ML, QNN, TensorRT, XLA, ...) maps a fixed operator set onto the hardware |
| Energy per MAC | Higher — pays for scheduling flexibility and a general memory path | Lower — the entire design is optimized around this one number |

## Energy per operation

The reason NPUs exist at all is the last row of that table. Moving an operand into a register, decoding an instruction, and arbitrating a cache access all cost energy that has nothing to do with the multiply-accumulate itself — and on a general-purpose core, that overhead can dominate the actual arithmetic. An NPU removes almost all of it: a MAC cell in a systolic array receives its operand from a neighboring cell, not from a general load path, and there is no per-operation instruction to fetch or decode. Stripping that overhead is what buys roughly an order of magnitude in energy per MAC over a general-purpose core doing the same arithmetic — state the direction with confidence, but treat any specific joules-per-MAC figure as vendor- and process-node-specific, worth citing from a datasheet rather than repeating from memory.

That energy budget is the whole reason a phone or laptop ships an NPU next to a perfectly capable GPU: running a always-on wake-word or camera model on the GPU at the power that would take is not an option on a battery, but the same model on a fixed-function engine is.

## What an NPU is bad at

The same design point that buys energy efficiency rules out entire categories of work. Anything with data-dependent control flow inside the hot loop — a search, a tree traversal, an RNN with a runtime-varying trip count — has nowhere to go on hardware built around a statically compiled schedule. Anything that needs full floating-point range and precision, like most training workloads, fights a MAC array built for INT8/INT4. And anything whose shape changes at runtime is a problem, because the compiled schedule assumes fixed tensor shapes; a genuinely dynamic shape either forces a fallback or a recompilation, neither of which the NPU is built to absorb gracefully.

## The operator-coverage problem

This is the practical heart of using an NPU, and it is where most real deployments live or die. An NPU implements a fixed operator set decided at hardware design time. A model graph that uses an operation outside that set — an unusual activation function, a custom normalization, an op the compiler's pattern matcher just doesn't recognize — cannot run on the NPU at all for that portion of the graph. The runtime falls back to the CPU or GPU for the unsupported op, and that fallback is not free: it typically means a layout conversion at each boundary where the graph crosses from NPU-native tensor layout to CPU/GPU-native layout, and back again on the way out.

The result is genuinely counterintuitive: a model with one unsupported op buried in the middle of an otherwise NPU-friendly graph can run *slower* than the same model never touching the NPU at all, because the accelerated segments save less time than the fallback round trips cost. Checking operator coverage before deployment, not after, is therefore the single highest-leverage step in getting an NPU to actually help.

:::warning[Fallback cost is not a rounding error]
A single unsupported operator does not just skip acceleration for that op — it forces a partition boundary, with a layout conversion into and out of the fallback device on every crossing. On a graph with several small unsupported ops scattered through it, those round trips can consume more time than the NPU saves on the rest of the graph, making the "accelerated" model slower than running it entirely on the CPU or GPU. See [Deploying to Accelerators](./deploying-to-accelerators.md) for how to find these boundaries before they show up as a regression in production.
:::

## See also

- [Systolic Arrays and Dataflow](./systolic-arrays-and-dataflow.md) — the MAC-array mechanism this page describes at a high level.
- [Edge NPUs](./edge-npus.md) — how this design point looks across specific mobile and embedded vendors.
- [CPU vs GPU vs NPU](../00-overview/cpu-vs-gpu-vs-npu.md) — the three-way comparison this page's design-point argument extends.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
