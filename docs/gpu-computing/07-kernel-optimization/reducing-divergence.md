---
id: reducing-divergence
title: Reducing Divergence
sidebar_label: Reducing Divergence
sidebar_position: 6
tags: [gpu, cuda, optimization, divergence]
---

# Reducing Divergence

[Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) established the cost model: a warp pays for *every* path its 32 lanes collectively take, sequentially, so a branch only costs extra when lanes within the same warp disagree. This page is the applied counterpart — given that rule, what actually removes the cost in real kernels.

## Only intra-warp divergence costs

Restating the rule this page builds on: divergence cost comes from disagreement *within* a warp, not from having a branch in the source or from different warps taking different paths from each other. A kernel can be full of `if` statements and pay nothing for them, provided every warp's 32 lanes always agree on which side they take.

## Restructuring branches

The most direct fix is changing which threads land in which warp so that a branch condition becomes warp-uniform instead of per-thread. `if (i % 2)` sends alternating lanes of every warp down opposite paths — the worst case, since every warp splits roughly 16/16 — while a condition based on `i / 32` sends entire warps down one path or the other.

```cpp showLineNumbers
// Divergent: i % 2 alternates every lane within a warp.
// Every warp splits ~16/16 and pays for both paths.
__global__ void byParity(float* data, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    if (i % 2) {
        data[i] = pathA(data[i]);
    } else {
        data[i] = pathB(data[i]);
    }
}

// Warp-uniform: i / 32 is the warp index, constant across all 32
// lanes of a given warp (since blockDim.x is a multiple of 32).
// Each warp takes one side or the other, never both.
__global__ void byWarp(float* data, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    if ((i / 32) % 2) {
        data[i] = pathA(data[i]);
    } else {
        data[i] = pathB(data[i]);
    }
}
```

`byWarp` still has a branch in the source and still sends different warps down different paths — but within any single warp, every lane agrees, so that warp executes its chosen path at full width with nothing masked off.

## Predication

Below a size threshold, the compiler doesn't emit a branch at all: a short `if` body compiles to a **predicated** instruction sequence, where every lane executes the instruction but a per-lane predicate register decides whether the result is actually committed. The instruction shape this produces looks like:

```text
@!P0 FADD R1, R2, R3;
```

`P0` is the branch condition per lane; the instruction issues for every lane in the warp regardless of the predicate, but only writes back where the predicate allows it. Because there's no branch instruction and no reconvergence point, a two- or three-instruction `if` handled this way costs the same whether the warp's lanes agree on the condition or not — the divergence cost model doesn't apply, because there was never a branch to diverge on. `nvcc`/`ptxas` makes this call automatically based on the size of the branch body; it isn't something source code requests directly, only something the SASS reveals after the fact — see [PTX and Inline Assembly](./ptx-and-inline-assembly.md).

## Sorting and binning work

For a kernel that dispatches to several different work types — a mesh with multiple element kinds, a graph with variable-degree nodes — the fix is a preliminary pass that sorts or bins indices by type before the expensive kernel runs, so each warp's lane range is (mostly) one type. The expensive kernel then indexes through the compacted, sorted array instead of the original one, and its per-type branch becomes warp-uniform the same way `i / 32` was above.

```cpp showLineNumbers
// binIndices has grouped all type-A indices before all type-B indices.
// A warp reading a contiguous slice of it sees (almost) one type only.
__global__ void processBinned(const int* binIndices, const int* type,
                               float* data, int n) {
    int slot = blockIdx.x * blockDim.x + threadIdx.x;
    if (slot >= n) return;
    int i = binIndices[slot];
    if (type[i] == TYPE_A) {
        data[i] = pathA(data[i]);
    } else {
        data[i] = pathB(data[i]);
    }
}
```

The branch itself hasn't moved — `processBinned` still has an `if` — but because `binIndices` grouped same-type work together, most warps now see a uniform `type[i]` across all 32 lanes, and only the warps straddling a type boundary still pay the divergent cost.

## Warp-uniform conditions

Two conditions are warp-uniform for free, without any restructuring, because of how indices map to warps: branching on `blockIdx.x` (every lane in a warp shares a block) and branching on `threadIdx.x / 32` (the warp index, given a 1-D block whose extent is a multiple of 32). Restructuring work — as in the two sections above — is really just finding ways to make the condition that actually matters reduce to one of these two shapes.

:::warning[Branchless tricks aren't automatically a win]
Rewriting a divergent `if`/`else` as branch-free arithmetic — `select`, a multiply by a 0/1 mask, `min`/`max` chains — removes the divergence, but every lane now executes *both* sides unconditionally, every time. If the branch the trick replaces was short enough that the compiler would have predicated it for free (see above), the branchless rewrite can cost more than the branch it removed. Measure before and after; don't assume branch-free is faster.
:::

## See also

- [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) — the cost model this page applies.
- [Instruction-Level Optimization](./instruction-level-optimization.md) — reading the SASS to confirm what actually got predicated or unrolled.
- [Sparse Matrix-Vector Multiply](../13-applied-kernels-and-patterns/sparse-matrix-vector.md) — a kernel where row-length variation makes binning workers by row length a real, applied case of this page's pattern.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
