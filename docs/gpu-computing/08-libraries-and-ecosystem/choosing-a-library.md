---
id: choosing-a-library
title: Choosing a Library Over a Kernel
sidebar_label: Choosing a Library
sidebar_position: 1
tags: [gpu, cuda, libraries, decision-guide]
---

# Choosing a Library Over a Kernel

NVIDIA's math libraries are tuned per architecture by engineers with access to the SASS scheduler, the microarchitecture team, and hardware that hasn't shipped yet. A hand-written GEMM that reaches 60% of cuBLAS's throughput on the same shapes is, realistically, a good hand-written GEMM — the remaining 40% is instruction scheduling, tile-size search, and register allocation tuned per compute capability by people who do nothing else. [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) makes this same point about `wmma` kernels specifically; this page generalizes it to the whole library landscape and gives a rule for when to reach for one, and when not to.

## The default answer is a library

For any operation with a well-known name — matrix multiply, convolution, FFT, sort, a sparse matrix-vector product — the default answer is to call a library, not to write a kernel. This isn't a cop-out; it's an admission that the search space these libraries cover (tile sizes, instruction shapes, memory layouts, precision modes, all cross-multiplied by every architecture NVIDIA still supports) is too large for one engineer to explore in the time it takes to ship a feature. Writing the kernel yourself only pays off when the operation, the fusion, or the shape falls outside what the library was built to cover.

## What a library gives you that you cannot easily rebuild

A tuned library encodes three things that are each individually expensive to reproduce: per-architecture kernel selection (cuBLAS ships dozens of GEMM kernels per precision and picks among them at call time based on the actual shape), correctness across edge cases (empty matrices, extreme aspect ratios, misaligned pointers — all handled, all tested), and forward compatibility (a new architecture typically means a driver and library update, not a rewrite of application code). None of these are algorithmic secrets — they're the product of sustained engineering investment applied to one narrow problem, which is exactly the kind of investment that doesn't scale down to a single kernel in an application codebase.

## When a hand-written kernel wins

Three situations genuinely favor a custom kernel over a library call:

- **No library equivalent exists.** A custom activation function fused with a domain-specific data layout, or a numerical method specific to one research codebase, has no cuBLAS or cuDNN entry point to call — there is nothing to reach for.
- **The library cannot express the fusion.** An elementwise chain wrapped around a reduction — normalize, then scale by a per-row statistic, then apply a nonlinearity, all in one pass — often has no single library call that expresses it, because the library's API is built around a fixed set of named operations, not arbitrary graphs of them. This is the gap [Triton](./triton.md) exists to fill.
- **The shape or dtype the library handles badly.** Very small matrices (a batch of 8x8 GEMMs) or very skewed ones (a 4096x4 matrix multiply) pay proportionally more overhead per call and often fall back to a generic, unoptimized path inside the library, because the library's tuning effort concentrates on the shapes real workloads actually use. A hand-tuned kernel for one specific small, awkward shape can beat a general-purpose library call on exactly that shape.

## The decision table

| Need | Reach for | Why |
|---|---|---|
| Dense linear algebra (GEMM, GEMV, factorizations) | cuBLAS / cuBLASLt | Broadest tuning coverage, per-shape kernel selection |
| Convolution and attention | cuDNN | Descriptor-driven algorithm search and fused engines |
| Custom GEMM shapes and epilogues | CUTLASS | Template-level control without hand-writing PTX |
| Sort, scan, reduce | CUB, Thrust | Warp/block-level primitives (CUB) or host-callable algorithms (Thrust) over the same tuned building blocks |
| FFT | cuFFT | Plan-based, batch-aware transform library |
| Sparse linear algebra | cuSPARSE | Generic sparse formats (CSR, COO) with tuned SpMV/SpMM |
| Random numbers | cuRAND | Host and device generation APIs, multiple RNG algorithms |
| Multi-GPU collectives | NCCL | Topology-aware all-reduce, broadcast, and all-gather |
| Fused elementwise around a reduction | Triton | Expresses the fusion no fixed-API library covers |

:::tip[The composition rule]
Use CUB inside your own kernel when you need a tuned block- or warp-level primitive as a building block. Use Thrust when you want to call an algorithm from host code without writing a kernel at all. Reach for CUTLASS when you need to own the GEMM — a custom epilogue, an unusual data layout, a shape cuBLAS handles poorly. Reach for cuBLAS when you don't need to own it. The four aren't competitors; they're different layers of the same stack, and a real codebase typically uses more than one.
:::

## Layering

These libraries stack, and it helps to see the stack rather than treat each as a standalone choice. CUB provides warp- and block-level primitives (sort, scan, reduce) as C++ templates meant to be called *from inside a kernel you're writing*. Thrust sits one layer up, wrapping similar algorithms behind an STL-like, host-callable interface — call `thrust::sort` and never write a kernel at all. CUTLASS occupies a different axis: it's not a general-purpose primitive library but a template library specifically for building GEMM and convolution kernels, letting you own the top-level structure (tiling, epilogue, data type) while it generates the tuned inner loop. cuBLAS sits above all of them as the fully pre-built, call-and-go answer for the shapes it covers well. Moving down this stack — cuBLAS to CUTLASS to CUB to a fully hand-written kernel — trades tuning effort you don't have to do for control you didn't have before; each step down is worth taking only when the step above has already been ruled out.

## See also

- [cuBLAS](./cublas.md) — the default answer for dense linear algebra, including the GEMM shape most kernels compare themselves against.
- [CUB](./cub.md) — the warp/block-level primitives layer this page's composition rule builds on.
- [CUTLASS](./cutlass.md) — where to go once you need to own the GEMM.
- [Triton](./triton.md) — the fusion escape hatch for elementwise chains around a reduction.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
