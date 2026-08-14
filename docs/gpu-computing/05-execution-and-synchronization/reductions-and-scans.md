---
id: reductions-and-scans
title: Reductions and Scans
sidebar_label: Reductions & Scans
sidebar_position: 8
tags: [gpu, cuda, reduction, scan]
---

# Reductions and Scans

Summing an array, finding its maximum, counting matches — these collapse many values into one, and doing it efficiently on a GPU means combining values in parallel at every level of the hierarchy rather than serializing down to one thread. [Warp-Level Primitives](./warp-level-primitives.md) already built the innermost piece, `warpReduceSum`; this page builds outward from it — warp to block to grid — and then covers the related but distinct problem of a *scan*, where every intermediate result is wanted, not just the final one.

## The shape of the problem

A reduction combines `N` values into one using an associative operator, and the parallel strategy is always the same shape at every scale: pairs (or larger groups) combine simultaneously, halving the number of live values each step, until one remains. What differs between warp, block, and grid scale is the mechanism available for threads to exchange values — register shuffles within a warp, shared memory within a block, global memory (or a second kernel) across a grid — and each mechanism has a different cost, which is why the three scales use three different techniques instead of one that's reused unchanged.

## Warp reduction

`warpReduceSum`, from [Warp-Level Primitives](./warp-level-primitives.md), is the innermost building block: a tree reduction across a warp's 32 lanes using `__shfl_down_sync`, entirely in registers, no shared memory or barrier needed.

```cpp showLineNumbers
__inline__ __device__ float warpReduceSum(float val) {
    for (int offset = warpSize / 2; offset > 0; offset >>= 1)
        val += __shfl_down_sync(0xffffffff, val, offset);
    return val;   // lane 0 holds the total
}
```

## Block reduction

A block is many warps, and warp reduction alone only collapses each warp to its own lane-0 total — those per-warp totals still need to be combined. `blockReduceSum` does that in two stages: reduce every warp with `warpReduceSum`, stash each warp's total in shared memory, then have the first warp reduce those stashed totals the same way.

```cpp showLineNumbers
__inline__ __device__ float blockReduceSum(float val) {
    static __shared__ float shared[32];       // one slot per warp
    const int lane = threadIdx.x % warpSize;
    const int wid  = threadIdx.x / warpSize;

    val = warpReduceSum(val);                 // reduce within each warp
    if (lane == 0) shared[wid] = val;
    __syncthreads();

    val = (threadIdx.x < blockDim.x / warpSize) ? shared[lane] : 0.0f;
    if (wid == 0) val = warpReduceSum(val);   // reduce the warp totals
    return val;                               // thread 0 holds the block total
}
```

`shared` is sized for 32 warps — 1024 threads, the maximum block size — regardless of the actual block size, so it's always large enough. The `__syncthreads()` between the two stages is load-bearing for the same reason [Block Synchronization](./block-synchronization.md) describes generally: every warp's total must actually be written to `shared` before warp 0 reads any of it. `blockReduceSum` assumes a 1-D block (so `lane` and `wid` are the true lane and warp id) and full convergence at entry, since it inherits the `0xffffffff` mask from `warpReduceSum`.

## The two-phase grid reduction

Reducing across an entire grid means combining values that live in different blocks, which — outside a cooperative launch — can't rely on any barrier spanning the whole grid. The standard pattern sidesteps that instead of fighting it: kernel 1 has each block reduce its own slice down to one value with `blockReduceSum` and writes that one value out; kernel 2 launches (typically as a single block) and reduces those per-block partial results down to the final answer.

This beats reaching for a grid-wide barrier in [Grid-Wide Synchronization](./grid-wide-synchronization.md) for most reduction sizes for the same reason that page's own verdict favors two launches: a second kernel costs a few microseconds and has no occupancy cap, while a cooperative launch caps the first kernel's grid at whatever fits resident on the device at once. A reduction is exactly the case where nothing needs to stay resident across the boundary — the only thing that crosses from kernel 1 to kernel 2 is the small array of partial sums — so the cooperative launch's constraint buys nothing here.

## Scan

A scan (prefix sum) asks a related but different question: instead of one final total, it produces, for every position `i`, the reduction of all elements up to `i` — an *inclusive* scan includes element `i` itself, an *exclusive* scan stops just before it. Every prefix is an output, not just the last one, which changes the algorithm shape even though the same associative-combining idea is underneath.

Two classic parallel scan algorithms trade work for depth differently: Hillis-Steele does `log2(N)` steps but `O(N log N)` total work, favoring latency on wide, shallow hardware; Blelloch does two `O(N)`-work passes (an up-sweep building partial sums, a down-sweep distributing them back out) for less total work at the cost of twice the passes. [Prefix Sum (Scan)](../13-applied-kernels-and-patterns/prefix-sum.md) works through both in full, including the block- and grid-level composition this page's reduction pattern generalizes to.

## Use CUB in production

:::tip[Write your own to learn it, ship CUB]
`cub::BlockReduce` and `cub::DeviceScan` implement exactly the patterns on this page — and the harder variants, like segmented and multi-dimensional reductions — tuned per architecture, handling edge cases like non-power-of-two block sizes that a hand-rolled version like `blockReduceSum` doesn't bother with. They are faster than almost any hand-written version and get faster on new hardware without you changing anything. Writing your own reduction, as above, is worth doing once to understand the machine; shipping a hand-rolled one in production code is usually leaving performance on the table for no benefit. See [CUB](../08-libraries-and-ecosystem/cub.md).
:::

## See also

- [Warp-Level Primitives](./warp-level-primitives.md) — `warpReduceSum`, the innermost building block this page composes upward from.
- [Cooperative Groups](./cooperative-groups.md) — `cg::reduce` and `cg::inclusive_scan` as a higher-level alternative to hand-written loops.
- [CUB](../08-libraries-and-ecosystem/cub.md) — production-grade, architecture-tuned reductions and scans.
- [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md) — a full applied kernel built around `blockReduceSum`.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
