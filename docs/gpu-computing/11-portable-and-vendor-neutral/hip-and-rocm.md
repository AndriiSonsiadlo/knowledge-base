---
id: hip-and-rocm
title: HIP and ROCm
sidebar_label: HIP & ROCm
sidebar_position: 2
tags: [gpu, hip, rocm, amd]
---

# HIP and ROCm

HIP (Heterogeneous-compute Interface for Portability) is AMD's answer to a specific problem: CUDA's API surface is good, and rewriting it from scratch to target AMD hardware would waste that. HIP is deliberately near-identical to the CUDA runtime API in names, signatures, and semantics, compiles with AMD's `hipcc` for AMD GPUs, and also compiles unchanged on top of the real CUDA runtime for NVIDIA GPUs — one source, two backends. ROCm is the software stack HIP sits inside: driver, compiler, runtime, and the library ecosystem that gives HIP something to link against.

## HIP as a near-CUDA API

The design goal shows up directly in a side-by-side of the calls a typical CUDA program makes:

| CUDA | HIP | Notes |
|---|---|---|
| `cudaMalloc` | `hipMalloc` | Same signature, same semantics. |
| `cudaMemcpy` | `hipMemcpy` | Same signature; same set of `hipMemcpyKind` directions. |
| `<<<grid, block>>>` | `hipLaunchKernelGGL(...)` | `<<<grid, block>>>` also works directly in HIP — `hipLaunchKernelGGL` exists for code paths that can't use the triple-chevron syntax (e.g. some older compilers or generic launch wrappers). |
| `__syncthreads` | `__syncthreads` | Identical name and behavior. |
| `cudaStream_t` | `hipStream_t` | Same role: an ordered queue of device work. |

That table is the entire mental model for a first pass: most of a CUDA program's runtime-API surface has a HIP call with the same name, minus the `cuda` prefix swapped for `hip`.

## Porting with `hipify`

AMD ships two tools that automate the mechanical part of that swap. `hipify-perl` is a Perl script that does pattern-based text substitution — fast, dependency-light, good for a first pass over a large codebase. `hipify-clang` parses the code with clang and rewrites it using the actual AST, which handles cases `hipify-perl`'s regex substitution gets wrong (macros, templates, less common API spellings).

```bash
hipify-perl saxpy.cu > saxpy.hip.cpp
hipify-clang saxpy.cu -- -I/usr/local/cuda/include
```

Both tools translate API calls, not intent. They rename `cudaMalloc` to `hipMalloc` and `<<<>>>` launches into HIP form; they do nothing about a hardcoded warp size, a `wmma` tensor-core call, or a tuning constant chosen for an NVIDIA SM. Mechanical translation gets a codebase to compile and often to run — it does not get it to run *well*, which is the point [The Portability Problem](./the-portability-problem.md) makes about API translation being the easy rung of the ladder.

## The ROCm stack

Above the HIP runtime, ROCm provides library counterparts to CUDA's ecosystem, so a port doesn't stop at the kernel level:

| CUDA library | ROCm equivalent | Domain |
|---|---|---|
| cuBLAS | rocBLAS / hipBLAS | Dense linear algebra |
| cuDNN | MIOpen | Deep learning primitives |
| CUB | hipCUB / rocPRIM | Block/warp-level parallel primitives |
| Thrust | rocThrust | STL-style parallel algorithms |
| NCCL | RCCL | Multi-GPU collective communication |
| cuFFT | rocFFT | Fast Fourier transforms |

`hipBLAS` and `hipCUB` are thin marshalling layers that can dispatch to either rocBLAS/rocPRIM (on AMD) or the real cuBLAS/CUB (on NVIDIA) — the same source-portability trick HIP itself uses, one level up the stack.

## AMD hardware differences

Past the API layer, a handful of real hardware differences are what actually break a naively-ported kernel:

- **Wavefront size 64 on CDNA, 32 on RDNA.** CUDA's warp is fixed at 32; AMD's wavefront is 64 lanes wide on CDNA (datacenter) parts and 32 on RDNA (consumer) parts. Any kernel with a hardcoded `32`, a `0xffffffff` lane mask, or a warp-shuffle reduction that assumes exactly 32 lanes participate is silently wrong on CDNA. The fix is to read the portable `warpSize` value rather than hardcoding it, and to size any lane mask off `__ballot`'s actual return type instead of assuming 32 bits.
- **LDS instead of shared memory.** AMD calls on-chip scratchpad memory Local Data Share (LDS) rather than shared memory, and its size and bank behavior differ from an NVIDIA SM's shared memory — a tile size tuned for one does not necessarily fit or avoid bank conflicts on the other.
- **Matrix cores, not `wmma`-compatible.** AMD's matrix cores use their own MFMA (matrix-fused-multiply-add) instructions with a different programming interface than CUDA's `wmma` API — a tensor-core kernel does not port by renaming types; it needs a rewrite against AMD's matrix intrinsics.
- **CDNA versus RDNA are different products.** CDNA targets datacenter compute (no display output, larger wavefronts, matrix cores); RDNA targets consumer graphics and gaming. Code tuned against one AMD architecture is not automatically well-tuned against the other, the same way Ampere-tuned CUDA isn't automatically well-tuned for Hopper.

:::warning[`__ballot` returns a 64-bit mask on CDNA]
HIP's `__ballot` returns `uint64_t`, not the 32-bit value CUDA's `__ballot_sync` returns, because a CDNA wavefront has up to 64 lanes to report. Code that stores the result in a 32-bit variable, or that assumes the CUDA convention of a 32-bit population count, silently drops the top half of the lanes on CDNA — a correctness bug with no compiler warning.
:::

## Where the port breaks

The pattern across all of the above is the same: `hipify` and the API-correspondence table handle the mechanical rename cleanly, and everything that breaks afterward is a hardware assumption baked into the original CUDA code, not a missing HIP feature. A port that only exercises the tools in this section and never runs on real AMD hardware has achieved source portability and nothing more.

:::tip[Building and targeting]
Compile HIP code with `hipcc`, and target a specific architecture with `--offload-arch=gfx90a` (that value being MI200-series CDNA silicon, for example). `rocminfo` reports the installed GPU's architecture name, which is exactly the string `--offload-arch` expects.
:::

## See also

- [The Portability Problem](./the-portability-problem.md) — why API translation is the easy rung and hardware assumptions are the hard one.
- [SYCL and oneAPI](./sycl-and-oneapi.md) — the vendor-neutral alternative that also targets AMD, via a different single-source model.
- [Warp-Level Primitives](../05-execution-and-synchronization/warp-level-primitives.md) — the CUDA-side shuffle and vote intrinsics whose lane-count assumptions this page's wavefront-64 warning is about.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
