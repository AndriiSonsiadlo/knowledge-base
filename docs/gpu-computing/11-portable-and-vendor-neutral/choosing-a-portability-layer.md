---
id: choosing-a-portability-layer
title: Choosing a Portability Layer
sidebar_label: Choosing a Layer
sidebar_position: 9
tags: [gpu, portability, decision-guide]
---

# Choosing a Portability Layer

Every page in this folder makes its own case, and none of them tells you which one to actually pick — that decision depends on facts about your project that no single page can know. This page collects those facts into four questions, a decision table built from them, and one default answer for the common case of not having a second target yet.

## The four questions

Answer these before comparing options, because each one eliminates a chunk of the table on its own:

1. **Which hardware must this run on?** NVIDIA only, NVIDIA plus one other vendor, a browser, or a fixed embedded target all point at different answers before performance enters the conversation at all.
2. **What language does the team already write?** A C++ team and a Python/PyTorch team face a different cost to adopt any given layer, independent of the layer's technical merits.
3. **How close to peak hardware performance must this actually get?** A data-movement or orchestration path tolerates a generic backend fine; a kernel that dominates the runtime does not, per [The Portability Problem](./the-portability-problem.md).
4. **Does it need to interoperate with graphics or a browser?** If a compute result feeds a render pass or has to run in a tab, that constraint dominates every other consideration — see [Vulkan and DirectX Compute](./vulkan-and-directx-compute.md) and [WebGPU](./webgpu.md).

## The decision table

| Option | Targets | Language | Effort to port from CUDA | Performance ceiling | Ecosystem |
|---|---|---|---|---|---|
| CUDA | NVIDIA only | CUDA C++ | — (native) | Highest, by construction | Deepest: cuBLAS/cuDNN/CUTLASS, every framework upstreams first |
| HIP | NVIDIA + AMD | C++, near-identical to CUDA | Low — `hipify` handles API calls | Near-native on AMD once rungs 3–4 are addressed | Mature on AMD; rocBLAS/MIOpen track cuBLAS/cuDNN with a lag |
| SYCL | NVIDIA + AMD + Intel | Standard C++, single-source | Moderate — rewrite around queues, no mechanical tool | Backend-dependent; best on Intel, solid on the others via plugins | Growing; strongest where Intel invests (oneAPI, DPC++) |
| OpenCL | Broadest driver support | C dialect, separate-source | Moderate–high — different memory and compilation model | Below CUDA/HIP; vendor driver quality varies | Mature but not growing; strongest in embedded/FPGA niches |
| OpenMP/OpenACC offload | NVIDIA + AMD + Intel (via compiler support) | Existing Fortran/C/C++ plus pragmas | Low for compute-bound loops, high for anything irregular | Below hand-written kernels; compiler-dependent | Strong in traditional HPC, weak in ML |
| Vulkan/DirectX compute | Broadest GPU driver support | GLSL/HLSL plus C++/C# host code | High — different object model entirely | High when tuned, but ceremony discourages tuning | Deep for graphics; sparse for pure compute |
| Metal | Apple only | MSL (C++14 dialect) plus Swift/Objective-C/C++ host | High — different API and memory model | High on Apple silicon specifically, via unified memory | Mature for Apple's own stack (MPS, Core ML); nowhere else |
| WebGPU | Anywhere a browser or `wgpu`/Dawn runs | WGSL | High — smallest, most restricted shader language here | Lowest ceiling of this table, by design (sandbox limits) | Young but growing; the only browser-native option |
| Triton | NVIDIA, growing AMD support | Python, compiled to a kernel | Low for the kernels it targets (matmul-like, tile-based) | Near-hand-tuned for the patterns it's designed around | Strong and growing fast inside PyTorch's compiler stack |

Reading down the "effort to port from CUDA" column repeats the same lesson [The Portability Problem](./the-portability-problem.md) makes at length: API-level effort is low almost everywhere, and the real cost is always in the rows that table doesn't have columns for — warp intrinsics, tuning, and library maturity.

## By target hardware

The four-questions framing collapses fastest when the first question already has a near-unique answer:

| If you must run on | Choose |
|---|---|
| NVIDIA only | CUDA |
| NVIDIA + AMD | HIP |
| NVIDIA + AMD + Intel | SYCL |
| Apple | Metal |
| A browser | WebGPU |
| Anything with a compute-capable driver, no other constraint | Vulkan or OpenCL |
| Existing Fortran/C++ HPC code | OpenMP offload |

## By team and language

A Python-first ML team already routes almost everything through PyTorch or JAX, and for that team the practical "portability layer" is the framework's own backend selection (CUDA, ROCm, MPS, XLA) plus Triton for hand-written kernels — none of the C++ options in the table above are usually the right first move. A C++ team with existing CUDA code faces the opposite calculus: HIP and SYCL are both live options, and the choice between them tracks the hardware question above more than anything about the team itself.

## Ecosystem maturity

The library column in the decision table is where "portable" quietly stops meaning "as fast." A layer's API coverage is rarely the bottleneck — its library maturity is. rocBLAS and MIOpen are real, tested, and used in production, but they still trail cuBLAS and cuDNN's tuning depth on the newest architectures; SYCL's library story is younger still outside Intel's own hardware. None of that is a reason to avoid these layers — it's a reason to benchmark the specific operations your workload depends on, on the specific hardware you'll actually deploy to, rather than trusting a portability claim on a vendor's landing page.

## The pragmatic default

Write CUDA. Keep the algorithm and the host-side structure free of CUDA-specific assumptions where that costs nothing — avoid hardcoding a warp size of 32 in code that doesn't need to, keep tuning constants in one place instead of scattered through the kernel — and port with HIP the day a second vendor becomes a real, funded requirement rather than a hypothetical one. Adopting a portability layer before a second target exists usually costs more than it saves: it's ongoing tax paid against a backend nobody runs, for optionality that [Ecosystem maturity](#ecosystem-maturity) above says you'll still have to re-benchmark from scratch the day you actually need it. This is the same position [The Accelerator Landscape](../00-overview/the-accelerator-landscape.md) takes about CUDA's central role in the ecosystem — restated here as the actionable version of that observation.

:::warning["Supports NVIDIA" means very different things]
A portability layer's documentation claiming it "supports NVIDIA" can mean anything from a first-class, continuously-tested backend to a community-maintained plugin that hasn't been exercised against a recent CUDA release. Check the project's CI matrix — which backends are actually built and tested on every commit — not the marketing page, before assuming a listed backend is production-ready.
:::

## See also

- [The Portability Problem](./the-portability-problem.md) — why source and functional portability are solved and performance portability isn't, which is the premise this page's table depends on.
- [HIP and ROCm](./hip-and-rocm.md) — the near-mechanical translation path this page's default recommends reaching for second.
- [SYCL and oneAPI](./sycl-and-oneapi.md) — the single-source alternative, and home of the canonical CUDA/SYCL/OpenCL terminology table.
- [The Accelerator Landscape](../00-overview/the-accelerator-landscape.md) — the hardware survey this page's decision table turns into an actionable choice.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
