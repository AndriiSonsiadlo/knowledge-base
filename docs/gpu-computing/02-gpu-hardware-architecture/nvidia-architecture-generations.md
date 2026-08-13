---
id: nvidia-architecture-generations
title: NVIDIA Architecture Generations
sidebar_label: Architecture Generations
sidebar_position: 8
tags: [gpu, hardware, nvidia, generations]
---

# NVIDIA Architecture Generations

Marketing names like "Ampere" or "Hopper" map to a compute capability number, and that number — not the marketing name — is what actually gates whether a piece of code compiles or runs. This page walks the generations that matter for code written today, listing only what each one added that changes what you can write or how you must write it, and closes with the canonical table this section's other pages point back at whenever they gate a feature behind a specific compute capability.

## Volta (CC 7.0)

Volta introduced **independent thread scheduling**: threads within a warp gained their own program counter and call stack, so divergent branches no longer forced strict lockstep reconvergence at every divergence point the way pre-Volta hardware did. This is why warp-level intrinsics changed shape at the same time — `__shfl_sync`, `__ballot_sync`, `__syncwarp`, and the rest of the `_sync` family exist specifically to let a kernel explicitly state which threads it expects to participate, since independent scheduling means the hardware can no longer assume "the whole warp" without being told. Volta also shipped the first generation of tensor cores (FP16, covered in [Tensor Cores](./tensor-cores.md)).

## Turing (CC 7.5)

Turing's architecturally significant addition was 2nd-generation tensor cores gaining **INT8 and INT4** precision, aimed squarely at quantized-inference throughput rather than training. Code targeting Turing that wants that throughput has to be written against those integer precisions explicitly — nothing about existing FP16 kernels picks them up automatically.

## Ampere (CC 8.0 / 8.6)

Ampere is where several features programmers actually reach for landed at once: **asynchronous copy** (`cuda::memcpy_async` and the `cp.async` PTX instruction it lowers to) lets a thread issue a global-to-shared-memory copy without occupying a register or blocking on the data's arrival, freeing up latency-hiding opportunities that pre-Ampere code had to get from occupancy alone. Ampere also added **BF16** arithmetic and **TF32** as a tensor-core-only reduced-precision mode that ordinary FP32-typed matrix code can opt into for a throughput gain with reduced mantissa precision, plus **structured (2:4) sparsity** support in the tensor cores. Separately, Ampere gave programmers explicit **L2 residency control** — the ability to designate a region of global memory as persisting preferentially in L2 via an access-policy window, rather than leaving residency entirely to the hardware's replacement policy.

## Ada Lovelace (CC 8.9)

Ada's headline change for programmers is **FP8** support in its 4th-generation tensor cores, carried over from the datacenter-focused Hopper generation into the consumer/workstation product line. Code that wants FP8 throughput on Ada has to be written for it explicitly, the same way Turing's INT8 required explicit targeting.

## Hopper (CC 9.0)

Hopper changes the programming model more than any generation since Volta. **Thread block clusters** add a level above the block in the execution hierarchy — a cluster of blocks that are guaranteed to run concurrently on SMs within the same GPC and can synchronize with each other, covered in [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md). That guarantee is what makes **distributed shared memory** (DSMEM) possible: a thread in one block within a cluster can directly address another block's shared memory over the cluster's dedicated fabric, something no earlier generation permits. Hopper also introduces the **Tensor Memory Accelerator** (TMA), a dedicated hardware unit that executes bulk asynchronous global-to-shared (and shared-to-global) copies — including multi-dimensional tensor tiles — without occupying a thread's registers the way `cuda::memcpy_async` does, freeing threads to do other work while the copy is in flight. Feeding tensor cores from TMA-staged shared memory is what `wgmma` — warp-group-wide MMA, operating across 128 threads rather than one warp's 32 — is built around, replacing the per-warp `wmma` fragment model for Hopper's highest-throughput path.

## Blackwell (CC 10.x / 12.x)

Blackwell's 5th-generation tensor cores add **FP4 and FP6** precisions, using microscaled formats designed for inference-scale throughput at the lowest practical precision, alongside further changes to the tensor-memory path built on top of Hopper's TMA/`wgmma` foundation. As with earlier narrow-precision additions, reaching FP4/FP6 requires code (or a library) written specifically against Blackwell's tensor-core generation — it is not something an FP8 Hopper kernel gets for free by recompiling.

## What actually changed for programmers

Every feature above is gated by compute capability at compile time — targeting a lower `sm_XX` than a feature requires produces code that simply doesn't use it, not code that fails at runtime. [Compute Capability](./compute-capability.md) covers how that gating is expressed on the `nvcc` command line. This table is the canonical reference the rest of this knowledge base's `:::note[Requires CC X.Y]` callouts point back at:

| Feature | Requires CC |
| --- | --- |
| Independent thread scheduling | 7.0 |
| `__shfl_sync`-family warp intrinsics required (non-`_sync` forms removed) | 7.0 |
| 1st-gen tensor cores (FP16) | 7.0 |
| INT8 / INT4 tensor cores | 7.5 |
| BF16 arithmetic | 8.0 |
| TF32 tensor cores | 8.0 |
| Structured (2:4) sparsity | 8.0 |
| `cuda::memcpy_async` / `cp.async` | 8.0 |
| L2 residency control (access-policy window) | 8.0 |
| FP8 tensor cores | 8.9 |
| Thread block clusters | 9.0 |
| Distributed shared memory (DSMEM) | 9.0 |
| Tensor Memory Accelerator (TMA) | 9.0 |
| `wgmma` warp-group MMA | 9.0 |
| FP4 / FP6 tensor cores | 10.0 |

## See also

- [Compute Capability](./compute-capability.md) — how the CC numbers in the table above turn into `nvcc` flags and which SASS a binary actually ships.
- [Tensor Cores](./tensor-cores.md) — the precision-by-generation table this page's tensor-core rows summarize, expanded with eligibility and throughput detail.
- [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) — the Hopper-generation execution-hierarchy addition this page introduces.
- [Asynchronous Data Movement](../04-cuda-memory-model/asynchronous-data-movement.md) — `cuda::memcpy_async` and TMA covered as memory-model features rather than generational trivia.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
