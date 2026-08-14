---
id: warp-level-primitives
title: Warp-Level Primitives
sidebar_label: Warp Primitives
sidebar_position: 3
tags: [gpu, cuda, warps, shuffle]
---

# Warp-Level Primitives

[Independent Thread Scheduling](./independent-thread-scheduling.md) explained why lockstep-dependent, `volatile`-based tricks for exchanging data within a warp no longer work, and why the fix is a family of intrinsics that carry explicit synchronization and an explicit participant mask. This page is that family: the shuffle intrinsics for moving values directly between lanes' registers, the vote intrinsics for asking a yes/no question of the whole warp, and the canonical reduction pattern built from them.

## The shuffle family

The shuffle intrinsics exchange a value directly between two lanes' registers — no shared memory, no round trip through memory at all — which makes them both faster and safer than a shared-memory exchange for anything that stays within a single warp.

| Intrinsic | Lane-selection rule | Typical use |
|---|---|---|
| `__shfl_sync(mask, val, srcLane)` | Every participating lane reads `val` from exactly `srcLane`. | Broadcasting one lane's value to the rest of the warp. |
| `__shfl_up_sync(mask, val, delta)` | Each lane reads `val` from `lane - delta`. | Inclusive/exclusive prefix-sum (scan) within a warp. |
| `__shfl_down_sync(mask, val, delta)` | Each lane reads `val` from `lane + delta`. | Tree-style reduction, halving the active distance each step. |
| `__shfl_xor_sync(mask, val, laneMask)` | Each lane reads `val` from `lane XOR laneMask`. | Butterfly-pattern reduction or exchange, e.g. across warp halves. |

All four require `mask` to name every lane that calls them, for exactly the reason [Independent Thread Scheduling](./independent-thread-scheduling.md) describes: it is a promise of convergence, not a filter.

## Vote intrinsics

The vote intrinsics turn a per-lane boolean into a warp-wide answer:

- `__all_sync(mask, predicate)` returns true only if `predicate` is true for every participating lane.
- `__any_sync(mask, predicate)` returns true if `predicate` is true for at least one participating lane.
- `__ballot_sync(mask, predicate)` returns a 32-bit value with one bit per lane, set wherever that lane's `predicate` was true — the full result, rather than `__all_sync`/`__any_sync`'s single collapsed bit.

Combining `__ballot_sync` with `__popc` (population count — number of set bits) is the standard idiom for "how many lanes matched":

```cpp showLineNumbers
unsigned mask = __activemask();
int matched = __popc(__ballot_sync(mask, value > threshold));
// matched == number of participating lanes where value > threshold
```

## `__activemask` and `__match_any_sync`

`__activemask()` returns the mask of lanes that are currently converged and executing the call — it doesn't take a mask argument, it produces one. That makes it tempting to use as a default whenever the "right" mask isn't obvious, but it answers a different question than the one that usually matters: it reports which lanes *happen to be* converged at this point, not which lanes the algorithm *needs* to participate. If a caller depends on `__activemask()` and the compiler or a future divergent code path changes which lanes are converged there, the operation silently changes meaning with it. It's the correct tool only when "whichever lanes are here right now" is genuinely the intended semantics, such as warp-aggregating a global-memory operation opportunistically. For anything where a specific set of lanes must all be present, pass an explicit, algorithm-derived mask instead.

`__match_any_sync(mask, value)` groups the participating lanes by equal `value`, returning to each lane a bitmask of the other lanes in its own group. Its one great use is conflict-free aggregation of atomics: instead of every lane with the same key issuing a separate `atomicAdd`, the lanes sharing a key elect one representative (typically the lowest set bit in the returned mask) to combine their contributions with `__shfl`-family intrinsics and issue a single atomic for the whole group — a **warp-aggregated atomic**, which turns up to 32 device-memory atomics into one.

## A warp reduction

The shuffle-down pattern generalizes into the canonical warp-level sum reduction — a tree reduction expressed entirely in registers, no shared memory and no barrier required, because `__shfl_down_sync` synchronizes the exchange itself:

```cpp showLineNumbers
__inline__ __device__ float warpReduceSum(float val) {
    for (int offset = warpSize / 2; offset > 0; offset >>= 1)
        val += __shfl_down_sync(0xffffffff, val, offset);
    return val;   // lane 0 holds the total
}
```

Each iteration halves the active distance: lane `L` adds in the value from lane `L + offset`, so after `log2(warpSize)` steps every value has been folded into lane 0. [Reductions and Scans](./reductions-and-scans.md) builds the block-and-grid-level reduction on top of exactly this function.

:::warning[`0xffffffff` assumes full convergence]
`0xffffffff` — all 32 lanes — is only the correct mask when the calling warp is known to be fully converged at that point, such as at kernel entry before any divergent branch. Inside code that may have diverged, pass `__activemask()` instead of a hardcoded full mask, so the reduction only demands participation from lanes that are actually still around. But treat `__activemask()` as a fallback, not a habit: it reports what *is* converged, not what the algorithm *should* require, so reusing it everywhere can silently paper over a bug where fewer lanes participate than the algorithm actually intends.
:::

## Masks in divergent code

Inside a branch that only some of a warp's lanes take, the correct mask is whatever subset of lanes are known to have taken that branch together — often exactly `__activemask()` if the branch condition is what caused the divergence, since every lane still executing at that point took this side. The failure mode to watch for is reusing a mask computed *before* a divergent branch on code that runs *after* it: the set of live lanes can have changed, and a stale mask naming a lane that is no longer there is undefined behavior, not a harmless no-op, exactly as [Independent Thread Scheduling](./independent-thread-scheduling.md) describes.

## See also

- [Independent Thread Scheduling](./independent-thread-scheduling.md) — why the mask argument exists and what it promises the hardware.
- [Reductions and Scans](./reductions-and-scans.md) — building block- and grid-level reductions on top of `warpReduceSum`.
- [Cooperative Groups](./cooperative-groups.md) — a higher-level API that wraps warp-level tiles and their masks.
- [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md) — a full applied kernel built around this page's reduction.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
