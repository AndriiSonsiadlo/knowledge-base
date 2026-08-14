---
id: independent-thread-scheduling
title: Independent Thread Scheduling
sidebar_label: Independent Thread Scheduling
sidebar_position: 2
tags: [gpu, cuda, warps, volta]
---

# Independent Thread Scheduling

[Warp Execution and Divergence](./warp-execution-and-divergence.md) described divergence as a cost model: a warp pays for every path its lanes take. Before Volta, divergence was also a *scheduling* model with sharp edges — the hardware tracked one program counter per warp using an explicit reconvergence stack, and code that assumed lockstep execution within a warp could rely on undocumented but consistent scheduling behavior. Volta replaced that mechanism, and the change is why so many older warp-synchronous idioms are now silently broken rather than merely non-portable.

## Before Volta

Pre-Volta hardware gave each warp a single program counter and a hardware call/branch stack. When a warp diverged, the stack recorded the not-taken path to resume later; the warp ran one side to completion (or to the next reconvergence point the compiler inserted), then popped the stack and ran the other side. Threads within a diverged warp had no individual notion of "where they are" — the warp as a whole was always at one point in the code. Programmers exploited this: because a warp's 32 threads were known to advance through unconverged code in fixed lockstep between divergence points, code could skip explicit synchronization within a warp and still behave predictably, provided nothing broke that lockstep assumption.

:::note[CC 7.0+]
Everything below — per-thread program counters, the breakage of lockstep-dependent code, and the requirement that warp intrinsics take an explicit mask — describes behavior from compute capability 7.0 (Volta) onward. See [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) for how to check what a target GPU supports. Pre-Volta behavior above is historical context only; it does not apply to any GPU built since 2017.
:::

## Per-thread program counters

From Volta onward, each thread in a warp gets its own program counter and call stack, not just the warp as a whole. This is **independent thread scheduling**: the hardware can interleave execution between diverged paths at fine granularity, scheduling individual threads (or groups of threads within the warp) rather than committing to run one whole side of a branch before the other. The warp still issues one instruction per cycle to whichever subset of lanes shares the next program counter — [Warp Execution and Divergence](./warp-execution-and-divergence.md)'s cost model is unchanged — but the hardware no longer guarantees any particular interleaving order between diverged threads, and it no longer automatically reconverges lanes just because they happen to reach the same address.

## What broke

Independent thread scheduling removed the lockstep guarantee that pre-Volta warp-synchronous code depended on. Code that relied on "thread N's write is visible to thread N+16 by the very next line, because the warp executes in lockstep" no longer has that guarantee — the two threads may not even be at the same instruction at the same time anymore. [Memory Consistency and Fences](../04-cuda-memory-model/memory-consistency-and-fences.md) makes the same point from the memory-ordering side: `volatile` never provided synchronization, it only forced a read or write to touch memory instead of a cached register, and pre-Volta code got away with treating a `volatile` write as "instantly visible to the rest of the warp" purely because the scheduler happened to keep everyone in lockstep. That assumption is gone.

```cpp showLineNumbers
// BROKEN on CC 7.0+ — do not use. Historical example only.
__device__ int warpReduceOld(volatile int* s, int lane) {
    if (lane < 16) s[lane] += s[lane + 16];
    if (lane <  8) s[lane] += s[lane +  8];   // no guarantee the previous line
    if (lane <  4) s[lane] += s[lane +  4];   // has completed across the warp
    // ...
    return s[0];
}
```

This pattern is a data race on every current GPU, `volatile` or not, and the fact that it can still appear to produce correct results some of the time — because independent thread scheduling doesn't reorder things *maximally*, just without a guarantee — makes it more dangerous, not less. The fix is the `_sync` family of warp intrinsics, which carry explicit synchronization and an explicit participant list built in:

```cpp showLineNumbers
__inline__ __device__ int warpReduceCorrect(int val, int lane) {
    for (int offset = 16; offset > 0; offset >>= 1) {
        val += __shfl_down_sync(0xffffffff, val, offset);
    }
    return val;   // lane 0 holds the total
}
```

[Warp-Level Primitives](./warp-level-primitives.md) covers `__shfl_down_sync` and the rest of the shuffle family in full, including the canonical `warpReduceSum` this pattern builds toward.

## Why every intrinsic now takes a mask

Every `_sync` intrinsic — `__shfl_sync`, `__ballot_sync`, `__all_sync`, and the rest — takes a 32-bit mask as its first argument, and that mask is not decoration. It names exactly the set of lanes that must participate in the operation, and by passing it the programmer is *asserting* that those lanes are converged at that point and will actually reach that instruction. The hardware does not verify this assertion; it trusts it. Passing a mask that includes a lane that never arrives, or excludes a lane that does, is undefined behavior — not a no-op, not a partial result, undefined behavior, up to and including a hang, because the hardware may wait for participants that never show up.

:::warning[The mask is a promise, not a filter]
`__shfl_sync(mask, ...)` does not silently skip lanes outside `mask` the way, say, a predicated load skips out-of-bounds threads. It requires every lane named in `mask` to actually execute that call. Get the mask wrong and the failure mode is undefined behavior, most often a deadlock or garbage data that only shows up under some inputs.
:::

## Reconvergence is not automatic

Because independent thread scheduling lets diverged threads make progress independently, the hardware is under no obligation to bring them back together at any particular point just because they've reached the same address in the program — it may, opportunistically, but nothing in the programming model guarantees it. If code needs a warp's lanes to actually be reconverged — for instance, before reading a value another lane just wrote to shared memory without going through a `_sync` intrinsic — it has to say so explicitly with `__syncwarp(mask)`. `__syncwarp` is the warp-scope analog of `__syncthreads()`: it blocks the calling thread until every thread named in `mask` has reached the same `__syncwarp` call, and it acts as a memory fence for shared and global memory as seen by that mask's lanes. Unlike the shuffle and vote intrinsics, `__syncwarp` doesn't move data — it just forces the reconvergence point that used to be implicit before Volta to become explicit again.

## See also

- [Warp-Level Primitives](./warp-level-primitives.md) — the full `_sync` intrinsic family and the canonical warp reduction this page's fix builds toward.
- [Warp Execution and Divergence](./warp-execution-and-divergence.md) — the cost model that independent thread scheduling does not change.
- [Memory Consistency and Fences](../04-cuda-memory-model/memory-consistency-and-fences.md) — why `volatile` never provided synchronization, from the memory-ordering side of this same story.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
