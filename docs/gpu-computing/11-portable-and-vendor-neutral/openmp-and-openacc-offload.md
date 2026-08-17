---
id: openmp-and-openacc-offload
title: OpenMP and OpenACC Offload
sidebar_label: OpenMP & OpenACC
sidebar_position: 5
tags: [gpu, openmp, openacc, directives]
---

# OpenMP and OpenACC Offload

Every portability layer covered so far in this folder still asks for a rewrite: HIP wants CUDA calls translated, SYCL wants kernels re-expressed as lambdas passed to a queue. Directive-based offload takes a different bet — annotate the loop nest you already have, keep one source file that still compiles and runs correctly on the CPU with the annotations ignored, and get working GPU code without restructuring the algorithm. That pitch is genuinely attractive for porting a large, already-correct codebase; it is a worse fit for the few kernels where every last percent of throughput matters, and this page is honest about where that line falls.

## Directive-based offload

OpenMP's `target` pragmas and OpenACC's `acc` pragmas both work the same way: they sit above an existing loop as comments-that-aren't-comments, telling a directive-aware compiler to generate device code for that loop while a directive-unaware compiler (or the same compiler with offload disabled) just skips them and compiles the loop for the CPU as always. One source, two possible destinations, selected by a compiler flag rather than a different file.

## The OpenMP target constructs

The OpenMP offload stack is a set of directives that compose, each one adding a level of parallelism, and it reads clearly once taken apart level by level:

- `target` moves execution of the following block to the device — without it, nothing offloads.
- `teams` creates a league of thread teams on the device, each with its own set of threads — the OpenMP analog of a CUDA grid of blocks.
- `distribute` splits the loop's iterations across those teams, one chunk per team.
- `parallel for simd` further splits each team's chunk across the team's threads, and asks each thread to additionally vectorize its share with SIMD.

Combined into the form actually written in practice:

```cpp showLineNumbers
#pragma omp target teams distribute parallel for simd \
        map(to: x[0:n]) map(tofrom: y[0:n])
for (int i = 0; i < n; ++i)
    y[i] = a * x[i] + y[i];
```

This one pragma is doing everything CUDA's `<<<blocks, threads>>>` launch plus the `map` clauses' explicit copies do, but as a single line above an otherwise ordinary `for` loop.

## Data clauses

The data-mapping clauses are where a directive port's performance actually gets decided. `map(to: ...)` copies data to the device at region entry and does not copy it back; `map(from: ...)` allocates on the device without copying in and copies back at region exit; `map(tofrom: ...)` does both; `map(alloc: ...)` allocates device space with no copy in either direction, for scratch arrays a kernel never needs initialized from the host. `#pragma omp target data` opens a region that hoists these mappings above a loop (or a sequence of loops), so an array mapped once at the top of a multi-kernel pipeline is not re-copied at every individual `target` construct inside it.

:::warning[The default mapping copies on every construct entry and exit]
Without an enclosing `target data` region, each `target` construct maps its data independently — meaning an array touched by ten kernels in a loop gets copied to the device and back ten times instead of once. This is the single most common reason a directive port runs slower than the original CPU code: the compute itself offloaded correctly, but the transfer cost that pinned-memory streaming and kernel fusion would normally amortize is instead paid on every single construct.
:::

## OpenACC

OpenACC predates the relevant parts of the OpenMP target model and takes the same directive-over-a-loop approach with its own pragma vocabulary:

```cpp showLineNumbers
#pragma acc parallel loop copyin(x[0:n]) copyout(y[0:n])
for (int i = 0; i < n; ++i)
    y[i] = a * x[i] + y[i];
```

`copyin`/`copyout` are OpenACC's direct equivalents of `map(to:)`/`map(from:)`, and its parallelism hierarchy is named `gang`/`worker`/`vector` — roughly the same three levels OpenMP splits into `teams`/`distribute`/`simd`, under different names. OpenACC was founded in 2011 by Cray, CAPS, NVIDIA, and PGI; PGI was later acquired by NVIDIA and its compiler became NVIDIA's HPC SDK, which is where OpenACC's NVIDIA-centric reputation today mostly comes from. It has a particularly strong position in Fortran HPC, where a large fraction of existing scientific codebases still live and where OpenACC compiler support has historically been ahead of OpenMP's.

## The incremental-porting appeal

The honest case for either standard is incremental porting: a large legacy codebase — often decades old, often Fortran or C, often too large to justify a from-scratch CUDA or SYCL rewrite — gets GPU-enabled one loop nest at a time. Each annotated loop is tested independently, the rest of the program is untouched, and the single source still builds for CPU-only environments where no GPU is available. That property — one source, works everywhere, incrementally improvable — is worth more for a large application than for a small, performance-critical kernel.

## The ceiling

What directive-based offload does not give up control of GPU architecture for: there is no explicit control of shared memory or LDS tiling, no warp/wavefront-level shuffle or vote intrinsics, no manual occupancy tuning. The compiler makes those decisions on the programmer's behalf from the directive's hints, which means a directive-generated kernel typically reaches only a fraction of what a hand-tuned kernel achieves on the same hardware — the exact gap depends on the kernel and isn't a number this page will invent. That makes directive-based offload the right tool for porting a large legacy codebase where most loops are not the bottleneck, and the wrong tool for the hot kernel that is.

:::tip[Build and check the offload actually happened]
Build with `nvc++ -mp=gpu` (NVIDIA's HPC SDK) or `clang -fopenmp -fopenmp-targets=nvptx64-nvidia-cuda` (LLVM/Clang), and check the compiler's offload remarks. A loop that silently falls back to host execution — because of an unsupported construct, an unmappable data type, or a dependency the compiler couldn't prove safe to parallelize — still compiles and runs, just entirely on the CPU, and without checking the remarks that failure is invisible until someone notices the GPU was never busy.
:::

## See also

- [SYCL and oneAPI](./sycl-and-oneapi.md) — the single-source C++ alternative for when directive-based offload's ceiling is reached.
- [Choosing a Portability Layer](./choosing-a-portability-layer.md) — where directive-based offload fits against HIP, SYCL, and OpenCL for a given project.
- [Shared-Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) — the kind of explicit control this page's "ceiling" section means a directive can't reach.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
