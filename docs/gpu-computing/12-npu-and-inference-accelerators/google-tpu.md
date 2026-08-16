---
id: google-tpu
title: Google TPU
sidebar_label: Google TPU
sidebar_position: 3
tags: [gpu, npu, tpu, xla]
---

# Google TPU

The Tensor Processing Unit is what happens when the weight-stationary systolic array from [Systolic Arrays and Dataflow](./systolic-arrays-and-dataflow.md) is scaled up to a datacenter training and inference accelerator, with a compiler stack and an interconnect built around it from the start. It is worth its own page separately from the general dataflow discussion because using a TPU well means accepting a programming model that looks nothing like CUDA: you do not write kernels for it at all.

## The MXU

The core of a TPU chip is the Matrix Multiply Unit (MXU): a large, weight-stationary systolic array that performs matrix multiplication and accumulation in hardware, the same mechanism [Systolic Arrays and Dataflow](./systolic-arrays-and-dataflow.md) describes generically. The consequence for anyone writing a model is direct: the array has fixed physical dimensions, and a matmul whose shapes do not evenly fill those dimensions wastes the unfilled portion of every cycle it runs. This is why TPU performance guidance is so consistently about shapes — pad batch and feature dimensions to a multiple of the MXU's tile size — rather than about anything resembling manual kernel tuning. Getting shapes tile-aligned is close to the entire optimization story at the model-code level.

## Memory

A TPU chip pairs its MXU with high-bandwidth memory (HBM) and a compiler-managed on-chip scratchpad that holds the weights and activations currently streaming through the array, the same on-chip-buffer pattern [What Is an NPU](./what-is-an-npu.md) describes as the second half of an NPU's die budget. There is no programmer-visible cache hierarchy to reason about the way there is on a GPU with L1/L2 and shared memory — the compiler decides what stays resident in the scratchpad and when it gets evicted, as part of compiling the whole computation graph ahead of time.

## Pods and the interconnect

Individual TPU chips are connected by dedicated, high-speed inter-chip links arranged in a toroidal mesh — a 2-D torus on earlier generations, a 3-D torus on more recent ones — rather than through a general datacenter network switch. Every chip in the mesh talks directly to its immediate neighbors, and the torus topology means there is no single central switch that all-reduce traffic has to funnel through. That shape suits the collective operations distributed training actually performs: an all-reduce across a torus can route along multiple neighbor-to-neighbor paths simultaneously, instead of every chip contending for one shared uplink the way a star or fat-tree network would force. A "pod" is a large number of chips wired this way, presented to software as something closer to a single very large accelerator than a cluster of independent nodes.

## XLA is the only entry point

The most important thing to internalize about TPU programming is what you do not do: you do not write TPU kernels. You write a model in JAX or in PyTorch through PyTorch/XLA, XLA (Accelerated Linear Algebra) compiles the resulting computation graph to the MXU and the rest of the chip, and your control over what the hardware actually does is exercised through graph structure and tensor shapes, not through anything resembling `<<<grid, block>>>` launch parameters or a hand-written kernel. Pallas exists as an escape hatch for genuinely custom kernels XLA's fusion and scheduling do not handle well, in the same spirit as writing raw `wmma`/`wgmma` code instead of relying on cuBLAS — but it is a niche tool for the cases the compiler doesn't already cover well, not the default way of using the chip.

| | TPU | NVIDIA GPU |
|---|---|---|
| Programming model | JAX / PyTorch-XLA graph compiled by XLA | CUDA C++/HIP/SYCL kernels, or a framework backend calling cuBLAS/cuDNN |
| Kernel-level control | Little; Pallas for custom kernels as an exception, not the norm | Full — `wmma`/`wgmma`, CUTLASS, hand-written PTX all available |
| Ecosystem | Strong inside Google Cloud and JAX/PyTorch-XLA; smaller outside it | Broadest ecosystem of any accelerator — every major framework, library, and profiler targets it first |
| Sparse/irregular workloads | Weak fit — the compiled, statically shaped graph model resists irregularity | Comparatively strong — dynamic control flow and irregular memory access are native to SIMT |
| Availability | Google Cloud only | Every major cloud, on-prem, and desktop |

## TPU versus GPU

The practical decision is less about peak throughput than about how well your workload matches a statically compiled graph. Large, regular, matmul-dominated training runs with stable shapes — the classic large-language-model pretraining case — are exactly what XLA and the MXU are built for, and TPUs are highly competitive there. Anything with dynamic shapes, sparse or data-dependent computation, or a need for hand-tuned custom kernels fits the GPU's programming model far more naturally, because CUDA gives you the escape hatch of arbitrary code where XLA gives you Pallas as a narrow exception.

:::warning[Shape polymorphism recompiles the graph]
XLA compiles a specialized program for each distinct combination of input shapes it sees. A model with variable sequence lengths — natural-language input that isn't padded to a fixed length, for instance — can trigger a fresh compilation on every new shape it encounters, and compilation is not cheap; a training or serving loop that keeps hitting new shapes can spend more wall-clock time compiling than executing. The standard fix is shape bucketing: pad or group inputs into a small, fixed set of shapes so XLA compiles once per bucket instead of once per input.
:::

## See also

- [Systolic Arrays and Dataflow](./systolic-arrays-and-dataflow.md) — the weight-stationary mechanism the MXU implements at scale.
- [Compiler Stacks: XLA, TVM, MLIR](./compiler-stacks.md) — XLA's compilation pipeline in more depth.
- [The Accelerator Landscape](../00-overview/the-accelerator-landscape.md) — where TPUs sit among the other vendors' stacks.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
