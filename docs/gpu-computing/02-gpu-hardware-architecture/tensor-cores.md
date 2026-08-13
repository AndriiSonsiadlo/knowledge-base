---
id: tensor-cores
title: Tensor Cores
sidebar_label: Tensor Cores
sidebar_position: 7
tags: [gpu, hardware, tensor-cores, mma]
---

# Tensor Cores

A CUDA core executes one scalar fused-multiply-add per thread per cycle. A tensor core executes an entire small matrix-multiply-accumulate in hardware, cooperatively across a warp, in roughly the same number of cycles — which is why a kernel that reaches them can be an order of magnitude faster than the same arithmetic done on CUDA cores, and why so much of applied deep-learning performance work is really about getting a kernel *eligible* for tensor cores rather than about tuning ordinary FP32 code.

## The MMA primitive

Every tensor-core operation, across every generation, boils down to the same primitive: `D = A * B + C`, where `A`, `B`, `C`, and `D` are small, fixed-shape matrix tiles (rather than the single scalars a CUDA core's FMA operates on). A warp of 32 threads issues this as one instruction, with the threads collectively supplying and receiving the tile's elements according to a fixed fragment layout the hardware defines. Because the multiply-accumulate over an entire tile happens in dedicated hardware rather than as a sequence of scalar FMAs, tensor cores deliver far higher FLOPs per cycle for matrix-shaped work than the SM's ordinary FP32/INT32 lanes can — at the cost of only being usable when the computation is actually shaped like a matrix multiply of a size the hardware supports.

## Precisions by generation

| Generation | Introduced precisions | Notes |
| --- | --- | --- |
| Volta (CC 7.0) | FP16 (FP32 accumulate) | 1st-generation tensor cores; the first hardware MMA path at all. |
| Turing (CC 7.5) | INT8, INT4 | 2nd generation; adds quantized-inference precisions on top of Volta's FP16. |
| Ampere (CC 8.0 / 8.6) | BF16, TF32, structured sparsity | 3rd generation; TF32 lets ordinary FP32-typed code opt into tensor cores with reduced mantissa precision; 2:4 structured sparsity roughly doubles throughput on eligible weights. |
| Ada Lovelace (CC 8.9) | FP8 | 4th generation (Ada variant); FP8 halves storage and roughly doubles throughput again versus FP16/BF16. |
| Hopper (CC 9.0) | FP8 (TMA-fed, `wgmma`) | 4th generation (Hopper variant); adds warp-group-wide `wgmma` instructions fed directly from shared memory via the Tensor Memory Accelerator, rather than per-warp fragments loaded through registers. |
| Blackwell (CC 10.x / 12.x) | FP4, FP6 | 5th generation; narrower microscaled formats for inference-scale throughput, alongside further tensor-memory changes over Hopper. |

## Throughput versus CUDA cores

The gap between tensor-core and CUDA-core throughput widens at lower precision. On an H100 SXM (Hopper, CC 9.0), CUDA-core FP32 throughput is roughly 67 TFLOPS (the figure used throughout this section's roofline discussion); dense tensor-core throughput on the same die is roughly 990 TFLOPS at FP16/BF16 and roughly 1980 TFLOPS at FP8 (both figures from NVIDIA's H100 datasheet, dense — i.e. without the roughly 2x further multiplier structured sparsity can add). That is close to a 15x gap at FP16 and a 30x gap at FP8, entirely from routing the same arithmetic through dedicated matrix-multiply hardware instead of the SM's general-purpose lanes.

## What makes a kernel eligible

Reaching a tensor core is not automatic just because a kernel does matrix multiplication — three concrete conditions have to hold:

- **Shape**: the operation's tile dimensions must match one of the fixed shapes the hardware's MMA instruction supports (for example, a `16x16x16` or `16x8x16` tile, depending on generation and precision) — an arbitrary matrix shape has to be decomposed into tiles of a supported size before it can be issued as MMA instructions.
- **Fragment layout**: operands must already be arranged in the specific per-thread (or, since Hopper's `wgmma`, per-warp-group) fragment layout the instruction expects — this is exactly what `wmma::load_matrix_sync` and its higher-level library equivalents exist to produce; simply having data in a shared-memory tile of the right shape is not sufficient without the right layout.
- **Accumulator precision**: the accumulator (`C`/`D` above) is usually kept at FP32 even when the inputs `A`/`B` are a narrower type like FP16, BF16, or FP8 — this is what keeps reduction error bounded across a long `K` dimension despite low-precision inputs, and it means a "FP16 tensor-core kernel" is really FP16-in, FP32-accumulate, not FP16 throughout.

## How you actually reach them

Three layers exist between "wanting tensor cores" and having them: the CUDA C++ `wmma` warp-level API (and, on Hopper, `wgmma`/`mma.sync` at the PTX level) for hand-written kernels; CUTLASS as a template library that generates tuned tensor-core GEMMs and convolutions from those same primitives; and cuBLAS/cuDNN as pre-built, pre-tuned libraries that route eligible calls through tensor cores automatically. [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) covers writing to the `wmma`/`wgmma` layer directly.

:::tip[Reach for the library first]
The overwhelming majority of code that benefits from tensor cores should get there through cuBLAS, cuDNN, or CUTLASS, not by hand-writing `wmma` fragments. Those libraries already encode the shape, layout, and scheduling tricks that make a tensor-core kernel actually fast; hand-written `wmma` is worth it mainly for a custom fused operation a library doesn't already provide. See [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) for when hand-written code is the right call.
:::

## See also

- [NVIDIA Architecture Generations](./nvidia-architecture-generations.md) — the per-generation feature table this page's precision table is drawn from.
- [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) — writing `wmma`/`wgmma` code directly, and when that's the right layer to work at.
- [CUTLASS](../08-libraries-and-ecosystem/cutlass.md) — the template library that generates tuned tensor-core kernels from these same primitives.
- [Matrix Multiply with Tensor Cores](../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md) — this page's eligibility conditions applied to a full worked kernel.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
