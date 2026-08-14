---
id: occupancy-tuning
title: Occupancy Tuning
sidebar_label: Occupancy Tuning
sidebar_position: 2
tags: [gpu, cuda, optimization, occupancy]
---

# Occupancy Tuning

[The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) derives occupancy as a fixed calculation against three hardware limits — registers, shared memory, and block/thread slots — and works a full example through all three. This page is the tuning counterpart: given that calculation, which levers actually move it, what raising occupancy buys in practice, and — just as important — where it stops buying anything at all.

## What occupancy buys

Occupancy is the supply of independent warps available to hide latency, nothing more. It doesn't make a kernel's instructions execute faster and it doesn't reduce the bytes moved; it only determines how much stall time — from a memory fetch, a dependent instruction, a `__syncthreads` — the scheduler has other ready warps available to cover instead of leaving the pipeline idle. A kernel that has no stalls to hide, because it is already compute-bound and issuing instructions back-to-back, gets nothing from more occupancy.

## Computing it

The three limiters from [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) — registers/thread, shared memory/block, and thread/block slots — come from the compiler and the launch configuration, not from guessing. `nvcc -Xptxas -v` reports the register and shared-memory usage the compiler actually settled on for a given kernel. The block below is representative sample output, not a real captured compile — it illustrates the fields to read and the shared-memory figure (8448 bytes) matches the padded `sgemmTiled` tile arrays worked out in [Shared Memory Tiling](./shared-memory-tiling.md), but the register count is illustrative; compile the kernel yourself to get the number that applies to your toolchain and target architecture:

```text
ptxas info    : Compiling entry function '_Z10sgemmTiled...' for 'sm_80'
ptxas info    : Function properties for _Z10sgemmTiled...
    0 bytes stack frame, 0 bytes spill stores, 0 bytes spill loads
ptxas info    : Used 64 registers, 8448 bytes smem, 400 bytes cmem[0]
```

Feed `64` registers/thread and `8448` bytes shared memory/block, along with the launch's threads/block, into the same register / shared-memory / thread-slot minimum from [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) — or let `cudaOccupancyMaxActiveBlocksPerMultiprocessor` do it — to get blocks/SM and, from that, achieved theoretical occupancy.

## `__launch_bounds__`

`__launch_bounds__(maxThreadsPerBlock, minBlocksPerMultiprocessor)` is a contract with `ptxas`, not a runtime setting: it tells the compiler the largest block size the kernel will ever be launched with and the minimum number of blocks per SM the caller wants resident, and `ptxas` caps the registers it allocates per thread so that many blocks actually fit. Without the annotation, the compiler is free to use as many registers as it finds useful for scheduling instructions; with it, register count becomes a budget the compiler must live inside.

```cpp showLineNumbers
__global__ void __launch_bounds__(1024, 2) sgemmTiled(int N, const float* __restrict__ A,
                                                       const float* __restrict__ B, float* __restrict__ C) {
    // kernel body unchanged
}
```

The same kind of `-Xptxas -v` output shows the effect directly — the pair below is, again, representative rather than a captured compile, illustrating the register count dropping once the annotation caps the budget; compare your own before/after output the same way:

```text
// without __launch_bounds__
ptxas info    : Used 64 registers, 8448 bytes smem, 400 bytes cmem[0]

// with __launch_bounds__(1024, 2)
ptxas info    : Used 32 registers, 8448 bytes smem, 400 bytes cmem[0]
```

Forcing registers down this way is the same lever [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) warns about: if the kernel's live values don't actually fit in the new budget, the excess spills to local memory, and a spill is real DRAM traffic that can cost more than the extra occupancy buys back.

## The point where it stops helping

Occupancy has diminishing, then zero, returns. Past a certain point the memory system itself — not the warp supply — becomes the limit: more resident warps just means more requests queued behind the same DRAM and L2 bandwidth, with no more throughput to show for it. Volkov's original occupancy study (Better Performance at Lower Occupancy, 2010), run on a GT200-generation Tesla GPU (compute capability 1.3), found many memory-bound kernels saturating and stopping improvement past roughly 50% occupancy. The mechanism — a saturated memory pipeline stops caring how many warps are queued behind it — is architecture-independent, but the specific 50% figure is that generation's number, not a guarantee for current hardware; treat it as the shape of the curve (diminishing returns well before 100%) rather than a universal threshold, and confirm the actual saturation point for a given kernel and GPU with a profiler sweep across block counts.

## High-ILP, low-occupancy kernels

Occupancy is one way to hide latency; giving each thread more independent work in flight is another, and Volkov's counter-case shows the second can beat the first. A kernel where each thread carries several independent accumulators has multiple non-dependent operations the scheduler can issue back-to-back from a *single* warp, without needing another resident warp to fill the gap — instruction-level parallelism substituting for warp-level parallelism. On the GT200-generation hardware Volkov measured, a version with several independent accumulators per thread at roughly 25% occupancy outperformed a version tuned for maximum occupancy, because the low-occupancy version had enough independent work per thread to keep the pipeline busy on its own.

```cpp showLineNumbers
__global__ void dotAccum2(const float* a, const float* b, float* out, int n) {
    int i = (blockIdx.x * blockDim.x + threadIdx.x) * 2;
    float acc0 = 0.0f, acc1 = 0.0f;   // two independent accumulators: no dependency between them
    for (int k = 0; k < n; k += 2) {
        acc0 += a[i + k] * b[i + k];
        acc1 += a[i + k + 1] * b[i + k + 1];
    }
    out[i / 2] = acc0 + acc1;
}
```

`acc0` and `acc1` have no data dependency on each other, so the scheduler can have both chains of multiply-adds in flight at once from the same warp, covering the latency of one accumulator's dependent chain with the other's independent work — the same effect extra resident warps would otherwise be needed for.

:::tip[Achieved vs theoretical occupancy]
Nsight Compute reports *achieved* occupancy alongside the *theoretical* occupancy computed from the register/shared-memory/thread-slot limits. A large gap between them usually means load imbalance across blocks or a tail effect — some SMs running out of work before others — rather than a register or shared-memory problem, and no amount of `__launch_bounds__` tuning fixes an imbalance problem.
:::

## See also

- [The Optimization Workflow](./the-optimization-workflow.md) — where raising occupancy fits as the latency-bound branch of the tuning loop.
- [Instruction-Level Optimization](./instruction-level-optimization.md) — the high-ILP approach generalized beyond the two-accumulator example here.
- [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) — the three-limiter calculation this page tunes against.
- [Registers and Local Memory](../04-cuda-memory-model/registers-and-local-memory.md) — what a spill costs when `__launch_bounds__` overcommits the register budget.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
