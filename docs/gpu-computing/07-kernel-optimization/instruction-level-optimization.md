---
id: instruction-level-optimization
title: Instruction-Level Optimization
sidebar_label: Instruction-Level
sidebar_position: 5
tags: [gpu, cuda, optimization, ilp]
---

# Instruction-Level Optimization

[Occupancy Tuning](./occupancy-tuning.md) showed that giving a thread several independent accumulators can substitute for occupancy — the scheduler fills a dependent chain's latency with another chain's independent work instead of waiting on another resident warp. This page generalizes that idea beyond hiding latency for its own sake: instruction-level parallelism, loop unrolling, cheaper instruction choices, and avoiding instruction sequences the hardware doesn't handle well are all ways to make the instructions a thread already issues cost less or overlap better, independent of how many warps are resident.

## ILP and independent work

A dependent chain of fused multiply-adds — each one needing the previous result — can only issue as fast as the FMA pipeline's latency allows, regardless of how many warps are resident, because the *next* instruction in that chain has nowhere to go until the current one retires. Splitting the same total work across independent accumulators removes that dependency: the scheduler can have several FMA chains in flight from a single warp, each covering the others' latency.

```cpp showLineNumbers
// Single accumulator: every FMA depends on the previous one.
// The pipeline can't start FMA[k+1] until FMA[k] has retired.
__global__ void reduceOneAcc(const float* a, const float* b, float* out, int n) {
    int i = (blockIdx.x * blockDim.x + threadIdx.x) * 4;
    float acc = 0.0f;
    for (int k = 0; k < 4; k++) {
        acc += a[i + k] * b[i + k];
    }
    out[blockIdx.x * blockDim.x + threadIdx.x] = acc;
}

// Four independent accumulators: no accumulator depends on another,
// so the scheduler can issue all four FMA chains back-to-back,
// hiding each one's latency behind the others.
__global__ void reduceFourAcc(const float* a, const float* b, float* out, int n) {
    int i = (blockIdx.x * blockDim.x + threadIdx.x) * 4;
    float acc0 = 0.0f, acc1 = 0.0f, acc2 = 0.0f, acc3 = 0.0f;
    acc0 += a[i + 0] * b[i + 0];
    acc1 += a[i + 1] * b[i + 1];
    acc2 += a[i + 2] * b[i + 2];
    acc3 += a[i + 3] * b[i + 3];
    out[blockIdx.x * blockDim.x + threadIdx.x] = acc0 + acc1 + acc2 + acc3;
}
```

`reduceFourAcc` does the same arithmetic as `reduceOneAcc`, but the four accumulators have no data dependency on each other, so the scheduler can keep several FMAs in flight from the *same* warp rather than needing another resident warp to fill the gap. This is the same substitution [Occupancy Tuning](./occupancy-tuning.md) demonstrates with its two-accumulator dot-product kernel — more independent work per thread standing in for more resident warps.

## Loop unrolling

`#pragma unroll` (full unroll) and `#pragma unroll N` (unroll by a factor of `N`) ask the compiler to replicate a loop body instead of branching back, which removes loop-overhead instructions and, more importantly, exposes more independent work per iteration for the scheduler and register allocator to overlap — unrolling is often what turns a dependent loop into something that behaves like the multi-accumulator case above.

```cpp showLineNumbers
#pragma unroll
for (int k = 0; k < 4; k++) {
    acc += a[i + k] * b[i + k];
}

#pragma unroll 8
for (int k = 0; k < n; k++) {
    sum += data[k] * weights[k];
}
```

Unrolling isn't free: each replicated iteration needs its own live values, so register pressure per thread rises, which can lower occupancy or force spills, and a fully unrolled large loop bloats the instruction footprint enough to pressure the I-cache. `nvcc` already unrolls loops with a small, compile-time-constant trip count on its own — a fixed `for (int k = 0; k < 4; k++)` rarely needs the pragma. The pragma earns its place on loops whose trip count is not a small compile-time constant, or where the default unroll factor isn't the one that measures best.

## Intrinsics versus precise math

CUDA ships fast approximate intrinsics alongside the precise (and slower) standard-library math functions. Each trades some accuracy for throughput; how much depends on the function.

| Intrinsic | What it replaces | Speed/accuracy character |
| --- | --- | --- |
| `__fdividef(x, y)` | `x / y` | Single-instruction-class division; measurably less accurate near the extremes of the exponent range than IEEE division. |
| `__sinf(x)` | `sinf(x)` | Fast polynomial approximation; accuracy degrades as `|x|` grows, so it's a poor fit for arguments far from the origin. |
| `__expf(x)` | `expf(x)` | Fast approximate exponential; noticeably lower accuracy than the precise version, exact ULP bound not fixed across toolkit versions — check the CUDA Math API guide for the version in use. |
| `__logf(x)` | `logf(x)` | Fast approximate logarithm; same caveat as `__expf` — meaningfully less accurate, particular figure not stable across releases. |
| `rsqrtf(x)` | `1.0f / sqrtf(x)` | Reciprocal square root has a dedicated fast hardware path; among the intrinsics here it's the one whose fast form is closest in accuracy to its precise counterpart. |

:::note[ULP figures]
Exact ULP error bounds for these intrinsics are published per CUDA toolkit version in NVIDIA's Math API documentation and shift between releases; treat the "speed/accuracy character" column above as the qualitative shape — division and the transcendentals trade real accuracy for speed, `rsqrtf` trades comparatively little — rather than a citable number, and check the toolkit's own tables before relying on a specific bound.
:::

The right default is selective, not global: use an intrinsic where a kernel has already been shown to be numerically tolerant of it — inside a normalization step feeding a later clamp, say — and leave the precise version everywhere accuracy hasn't been checked. Applying them everywhere via a global flag is a different, blunter tool, covered next.

## `--use_fast_math`

`--use_fast_math` is a single `nvcc` flag that bundles several of the choices above into one blanket switch: it turns on FP contraction of separate multiply and add operations into fused FMAs more aggressively, enables flush-to-zero for denormals, substitutes the fast intrinsic (`__sinf`, `__expf`, `__fdividef`, ...) for the precise standard-library call at every call site, and sets `--prec-div=false` and `--prec-sqrt=false` so ordinary `/` and `sqrtf` use the reduced-precision hardware paths instead of the IEEE-correct ones.

:::warning[It changes results]
`--use_fast_math` is not a free performance switch — it changes the numerical output of the program, sometimes enough to fail a downstream tolerance check that passed before. Never enable it silently on numerical code; treat it the same as any other precision decision, verified against the accuracy the caller actually needs, not flipped on project-wide because a benchmark got faster.
:::

## Integer division and modulo

32-bit integer division and modulo are not single instructions on the GPU — the hardware has no integer divide unit, so `nvcc` expands `/` and `%` on `int`/`unsigned` into a multi-instruction sequence, which is expensive relative to almost any other arithmetic in a kernel. When the divisor is a compile-time or loop-invariant power of two, a mask or shift does the same job in one instruction:

```cpp showLineNumbers
// Precondition: n is a power of two.
int q = i / n;          // ->  int q = i >> log2n;
int r = i % n;           // ->  int r = i & (n - 1);
```

The `& (n - 1)` substitution is only correct when `n` is a power of two — for any other divisor it computes a different value, not an approximation of the modulo. When the divisor is loop-invariant but not a power of two, hoisting a precomputed reciprocal and multiplying instead of dividing inside the loop is the usual alternative, trading one division outside the loop for a multiply on every iteration inside it.

:::tip[Check the SASS, not the source]
Whether the compiler already turned a division into a shift, whether a `#pragma unroll` actually unrolled, and whether independent accumulators stayed independent after register allocation are all facts about the generated SASS, not the C++ source — the compiler is free to make any of these transformations on its own, or fail to. See [PTX and Inline Assembly](./ptx-and-inline-assembly.md) for reading that output directly.
:::

## FMA and contraction

By default (without `--use_fast_math`), `nvcc` still contracts a separate multiply and add — `a * b + c` written as two operations in source — into a single fused multiply-add when it is safe to do so, because FMA is both faster (one instruction instead of two) and more accurate (one rounding step instead of two) than the un-fused sequence. This makes FMA one of the rare optimizations that costs nothing to enable; it's on by default, and turning it off (`-fmad=false`) is a debugging tool for isolating a numerical discrepancy against a non-fused reference, not something a performance-tuned kernel wants disabled.

## See also

- [Occupancy Tuning](./occupancy-tuning.md) — ILP as a counterweight to occupancy, with the two-accumulator case this page generalizes.
- [PTX and Inline Assembly](./ptx-and-inline-assembly.md) — reading the SASS this page's tips point back to.
- [Nsight Compute](../09-tooling-profiling-and-debugging/nsight-compute.md) — profiling a kernel to find whether it's actually instruction-issue bound before spending time on any of this.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
