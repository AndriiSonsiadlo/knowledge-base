---
id: compute-capability
title: Compute Capability
sidebar_label: Compute Capability
sidebar_position: 9
tags: [gpu, hardware, compute-capability, nvcc]
---

# Compute Capability

Compute capability is the single number that determines what a piece of CUDA code can assume about the GPU it runs on — which instructions exist, which tensor-core precisions are available, how big a thread block cluster can be. Getting the build flags around it wrong is one of the most common ways a CUDA binary that worked on the machine it was built on fails, silently or loudly, on someone else's GPU.

## What the number gates

Every feature enumerated in the closing table of [NVIDIA Architecture Generations](./nvidia-architecture-generations.md#what-actually-changed-for-programmers) — independent thread scheduling, a given tensor-core precision, thread block clusters, TMA — is available only on GPUs at or above the compute capability that introduced it. The compiler uses the target compute capability to decide which instructions it's allowed to emit; a kernel using `wgmma` compiled for CC 8.0 simply won't compile, because that instruction doesn't exist at CC 8.0. Compute capability is a property of the GPU (queryable at runtime via `cudaGetDeviceProperties`), and it is entirely distinct from the CUDA *toolkit* version used to compile — a recent toolkit can still target an old compute capability, and an old toolkit cannot target a compute capability newer than it knows about.

## Virtual and real architectures

`nvcc` actually deals with two different notions of "architecture," and conflating them is the single most common source of confusion here:

- A **virtual architecture**, named `compute_XX` (e.g. `compute_80`), describes a set of *features* — it is the target for compiling CUDA C++ down to **PTX**, an intermediate, architecture-independent assembly that is not yet tied to any specific chip's instruction encoding.
- A **real architecture**, named `sm_XX` (e.g. `sm_90`), describes an actual chip's instruction set — it is the target for compiling (either directly from CUDA C++, or from PTX) down to **SASS**, the real machine code that GPU actually executes.

PTX compiled for a given `compute_XX` can be JIT-compiled by the driver into SASS for any `sm_XX` that is the same or newer, because PTX deliberately stays forward-compatible; SASS compiled for a specific `sm_XX` runs only on that generation (and, for most generations, is not guaranteed to run on a different one at all, forward or backward).

## `-arch`, `-code`, and `-gencode`

A single `nvcc` invocation can embed multiple SASS images for different real architectures, plus one PTX image, all in the same binary — the driver picks whichever embedded SASS matches the GPU it's running on, and falls back to JIT-compiling the embedded PTX if no matching SASS is present. `-gencode arch=compute_XX,code=sm_YY` (with `XX` and `YY` typically equal) produces one such SASS image; a `-gencode` entry with `code=compute_XX` instead of `code=sm_XX` embeds PTX rather than SASS.

```bash
# SASS for Ampere and Hopper, plus PTX for future JIT
nvcc -gencode arch=compute_80,code=sm_80 \
     -gencode arch=compute_90,code=sm_90 \
     -gencode arch=compute_90,code=compute_90 \
     kernel.cu -o kernel
```

This produces a binary with SASS for CC 8.0 and CC 9.0 GPUs (fast, no JIT needed), plus a CC-9.0-generation PTX image the driver can JIT-compile for any GPU newer than 9.0 that this build never explicitly targeted.

## Forward compatibility and JIT

The trailing PTX entry is what makes a binary built today still run — after a JIT step — on a GPU released after the binary was compiled. Without it, a binary containing only SASS images has no code path for a newer architecture at all: the driver has nothing it can either run directly or JIT-compile, since JIT only works from PTX.

:::warning[Shipping SASS only breaks on newer GPUs]
A binary built with only `-gencode arch=compute_90,code=sm_90` (no accompanying `code=compute_90` PTX entry) will fail to launch on any GPU newer than what was explicitly targeted, with an error like `no kernel image is available for execution on the device`. The trailing `-gencode arch=compute_90,code=compute_90` line in the snippet above is exactly what prevents this — it embeds PTX the driver can JIT-compile for architectures the binary's author never built for.
:::

:::note[The JIT cache hides the recompilation cost after the first run]
JIT-compiling embedded PTX to SASS at load time is slow relative to loading pre-built SASS directly — noticeable as extra startup latency the first time a JIT-only code path runs on a given GPU. The driver caches the JIT-compiled result on disk (controlled by the `CUDA_CACHE_PATH` environment variable, with a default location and size cap) so that latency is paid once per GPU/driver/binary combination, not on every process launch. Clearing that cache, or running on a system where it isn't writable, brings the JIT cost back on every run.
:::

## What to ship

For a binary distributed to users with unknown hardware, the practical pattern is the one in the snippet above: embed SASS for every real architecture you can reasonably test against and expect your users to have, and always add a trailing PTX entry for the newest architecture you targeted, so a GPU released after your build still runs via JIT instead of failing outright. For an internal or single-machine build where the exact target GPU is known, it's simplest to compile SASS for that one `sm_XX` only and skip the PTX fallback — there's nothing to be forward-compatible with.

## See also

- [NVIDIA Architecture Generations](./nvidia-architecture-generations.md) — the canonical `| Feature | Requires CC |` table that decides which `compute_XX`/`sm_XX` values a build actually needs.
- [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md) — how `nvcc`'s split compilation into host and device code fits around the PTX/SASS pipeline described here.
- [Building CUDA with CMake](../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md) — expressing `-gencode` flags through `CMAKE_CUDA_ARCHITECTURES` instead of raw `nvcc` invocations.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
