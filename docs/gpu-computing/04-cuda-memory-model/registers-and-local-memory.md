---
id: registers-and-local-memory
title: Registers and Local Memory
sidebar_label: Registers & Local Memory
sidebar_position: 5
tags: [gpu, cuda, memory, registers]
---

# Registers and Local Memory

[The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) covers how a kernel's register usage feeds directly into the occupancy calculation. This page is the other side of that same fact: what registers actually hold, what forces a value out of the register file and into memory instead, and how to tell when that's happened to your kernel.

## Registers are allocated per thread, statically

`ptxas`, the backend that turns PTX into SASS, fixes the register count a kernel needs per thread at compile time — this is a static property of the compiled kernel, not something that varies at runtime based on input or launch configuration. The runtime then multiplies that fixed per-thread count by the threads-per-block the kernel is launched with to determine how much of the SM's register file one block consumes, which is the register-limited term in the occupancy calculation [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) works through in full. There is no dynamic register allocation on the GPU the way a CPU might spill and refill across calls — a thread either has enough registers for its live values for its entire lifetime, or the compiler has already decided, at compile time, that some of those values live somewhere else.

## What spills

A **spill** is the compiler placing a value that source code treats as an ordinary local variable into local memory instead of a register, because the register file doesn't have room. Two things force this. The ordinary case is simply too many live values at once — a kernel with a lot of unrolled work or many simultaneously-live temporaries can exceed whatever register budget the compiler is targeting. The less obvious case, and often the more surprising one: a local array indexed with a non-constant index cannot live in registers at all, regardless of how small it is, because registers have no addressing mode — the compiler can't generate "read register number `i`" for a runtime-variable `i`.

```cpp
__global__ void bad_local_array(float* out, int n, int k) {
    float scratch[8];
    for (int i = 0; i < 8; i++) {
        scratch[i] = i * 1.0f;
    }
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        out[idx] = scratch[k % 8];  // k is not a compile-time constant
    }
}
```

`scratch[k % 8]` forces the whole `scratch` array to local memory even though it's only 8 floats — the index `k % 8` isn't known at compile time, so there's no register the compiler can statically assign to "the element `scratch` currently needs." A loop with a compile-time-constant, fully-unrolled index into the same array would instead keep every element in its own register.

## Detecting spills

```bash
nvcc -O2 -arch=sm_80 -Xptxas -v -c kernel.cu
```

```text
ptxas info    : Used 72 registers, 96 bytes cumulative stack size, 380 bytes cmem[0]
```

The `-Xptxas -v` flag reports register usage per kernel at compile time; a nonzero **stack size** in that output is the compile-time spill signal — local memory is implemented as a per-thread stack, so any nonzero figure there means the compiler put something in local memory. At runtime, Nsight Compute's `local_load` and `local_store` counters are the corresponding signal: nonzero values mean the kernel is actually issuing loads and stores against local memory while it runs.

## Controlling register usage

Two levers force a lower register count per thread, and they're not equivalent. `-maxrregcount` is a translation-unit-wide `nvcc` flag — it caps every kernel compiled in that file, whether or not that's what you want for each of them. `__launch_bounds__` is a per-kernel annotation that travels with the kernel's own source, so it stays correct if the kernel is moved to a different file or compiled alongside kernels with different register needs:

```cpp
__global__ void __launch_bounds__(256, 4) myKernel(/* ... */) { /* ... */ }
```

This tells the compiler the kernel will be launched with at most 256 threads/block and that it should target enough register frugality to keep at least 4 blocks resident per SM, and the compiler is free to spill to meet that target if it can't fit otherwise. Prefer `__launch_bounds__` over `-maxrregcount` for exactly that reason: it expresses the constraint at the kernel that actually has it, instead of blanket-capping every kernel in the compilation unit.

:::warning[Cutting registers to raise occupancy can cost more than it gains]
Capping registers to raise occupancy trades a fast register access for an L1-or-worse local-memory access whenever the cap forces a spill the kernel wouldn't otherwise have. [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) covers this same tradeoff from the occupancy side — read that warning before reaching for either lever here, and measure both the occupancy change and the actual runtime, not just one.
:::

## When spilling is fine

A handful of spilled registers is not automatically a problem — a kernel that's compute-bound, or one where the spilled values are touched rarely relative to the kernel's other work, can absorb a small amount of local-memory traffic without it becoming the bottleneck. The `local_load`/`local_store` counters and the kernel's actual measured runtime are what settle the question, not the presence of a nonzero stack-size line on its own.

## See also

- [Memory Spaces Overview](./memory-spaces-overview.md) — where registers and local memory sit relative to the other four spaces.
- [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) — the occupancy calculation that register usage per thread feeds into.
- [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) — the practical tradeoffs between raising occupancy and avoiding spills, in a full kernel-tuning workflow.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
