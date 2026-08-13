---
id: flynn-taxonomy-simd-simt
title: SIMD, SIMT, and Flynn's Taxonomy
sidebar_label: SIMD, SIMT, Flynn
sidebar_position: 1
tags: [gpu, parallelism, simt, simd]
---

# SIMD, SIMT, and Flynn's Taxonomy

Every processor design answers two questions: how many instruction streams does it execute, and how many data streams does each instruction touch. Those two answers are the whole of Flynn's taxonomy, and they matter here because "GPU" is not a single point on that map — a GPU's arithmetic units are driven by an execution model, SIMT, that is easy to mistake for ordinary SIMD vectorization and behaves differently in exactly the cases that matter for correctness and performance.

Getting SIMT right early pays off for the rest of this section and the next: every later discussion of divergence, occupancy, and warp-level primitives assumes you already have the model in your head, not the CPU-vectorization model it superficially resembles.

## Flynn's four categories

Flynn's taxonomy (1966) classifies a machine by instruction and data stream count:

- **SISD** — single instruction, single data. One ALU executing one instruction on one datum at a time. An ordinary scalar CPU core running unvectorized code.
- **SIMD** — single instruction, multiple data. One instruction stream, but each instruction operates on a fixed-width vector of data lanes simultaneously. CPU vector extensions (SSE, AVX, AVX-512, ARM SVE) live here.
- **MISD** — multiple instructions, single data. Rare outside fault-tolerant systems that run several independent computations on the same input and vote on the result.
- **MIMD** — multiple instructions, multiple data. Independent processors each running their own instruction stream on their own data. A multi-core CPU, or a cluster of nodes, is MIMD at the coarse grain.

A GPU's streaming multiprocessors are MIMD with respect to each other — different SMs run different blocks, possibly from different kernels — but within an SM, the warp scheduler issues one instruction per cycle to a group of 32 threads. That inner layer is neither classic SIMD nor classic MIMD. NVIDIA calls it **SIMT**: single instruction, multiple threads.

## SIMD: one instruction, one register width

In SIMD, the vector width is a hardware fact baked into the instruction set, and the compiler or programmer must make it explicit. An AVX2 loop processes 8 `float`s per instruction because a YMM register is 256 bits wide; the code has to be written, or auto-vectorized, around that number. There is no per-lane control flow — a masked SIMD instruction (as in AVX-512 or SVE) can *disable* lanes for one instruction, but there is still exactly one program counter and one instruction stream driving the whole vector. If different lanes logically need different code paths, the programmer computes both paths and masks the result; the hardware has no other option.

## SIMT: one instruction, many threads

SIMT keeps the same underlying idea — one instruction, many ALUs — but changes what the "many" are built from. A CUDA thread is a full logical thread: it has its own program counter (independent thread scheduling, compute capability 7.0 and later), its own register file allocation, and its own local memory. The hardware groups 32 threads into a **warp** and, on hardware without independent scheduling or in the common case where a warp's threads agree on the next instruction, issues that one instruction to all 32 lanes in a cycle. The vector width — 32 — is a hardware constant, but it is not something the kernel source code names the way an AVX intrinsic names its register width; the kernel is written as if each thread were independent, and the warp grouping is implicit.

That independence has a real consequence: a warp's threads *can* take different branches. When they do, the hardware serializes the divergent paths — each path executes with the threads that didn't take it masked off — rather than refusing to compile, or requiring the programmer to hand-write a mask. Correctness is preserved either way; only throughput suffers, since a fully divergent warp burns 32 execution slots to do the work of one path taken by one thread. From compute capability 7.0 onward (Volta and later), each thread even has an independent program counter and call stack, which allows fine-grained interleaving between diverged paths — including cases, like producer-consumer patterns within a warp, that would deadlock on older SIMT hardware. It does not remove the masking cost; it only makes divergent code more expressive.

```cpp showLineNumbers
// AVX2: 8-wide, explicit vector width, explicit masking for anything conditional.
void saxpy_avx2(int n, float a, const float *x, float *y) {
    __m256 va = _mm256_set1_ps(a);
    for (int i = 0; i < n; i += 8) {
        __m256 vx = _mm256_loadu_ps(x + i);
        __m256 vy = _mm256_loadu_ps(y + i);
        vy = _mm256_fmadd_ps(va, vx, vy);
        _mm256_storeu_ps(y + i, vy);
    }
}

// CUDA: no vector width in sight — "width" is the block/grid launch shape.
__global__ void saxpy_cuda(int n, float a, const float *x, float *y) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        y[i] = a * x[i] + y[i];   // one thread, one element, no manual masking
    }
}
```

The AVX version names its width in every intrinsic (`_mm256_*`, 8 lanes) and manually walks the loop in strides of that width. The CUDA version has no width in the kernel body at all — the launch configuration (`blocks, threads`, covered in [The Host–Device Model](./the-host-device-model.md)) decides how many threads exist, and the 32-wide grouping into warps is a hardware detail the source never names.

:::note[A "CUDA core" is a lane, not a core]
Marketing material and even some NVIDIA documentation calls the FP32 ALUs inside an SM "CUDA cores." Architecturally they are SIMT lanes: 32 of them execute in lockstep as a warp, driven by a shared instruction fetch/decode, much closer to an AVX lane than to an independent CPU core. See [Warps and Warp Schedulers](../02-gpu-hardware-architecture/warps-and-schedulers.md) for how the scheduler actually drives them.
:::

## Why the distinction changes how you write code

If you think of a GPU kernel as "SIMD with a friendlier syntax," two mistakes follow. First, you'll assume branches are as free as they are with masked AVX-512 predication — they aren't; every taken path costs real cycles across the whole warp, so divergence is a performance bug, not just a masking detail. Second, you'll under-provision parallelism: SIMD hardware wants a vector-width multiple of work items and stops scaling once you supply that; SIMT hardware wants many more warps resident than can issue in a given cycle, because the surplus is what the scheduler hides memory latency behind (see [Latency, Throughput, and Latency Hiding](./latency-throughput-and-hiding.md)). Writing CUDA well means keeping both facts in view at once: at the warp level you are effectively writing 32-wide SIMD and divergence is real, but at the kernel level you are supplying thousands of independent threads, not one long vectorized loop.

## See also

- [Parallel Patterns](./parallel-patterns.md) — the algorithmic shapes that map cleanly onto the SIMT model.
- [Warps and Warp Schedulers](../02-gpu-hardware-architecture/warps-and-schedulers.md) — how the hardware actually groups and issues threads.
- [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) — the mechanics and cost of the masking described above.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
