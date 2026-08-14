---
id: block-synchronization
title: Block Synchronization
sidebar_label: Block Synchronization
sidebar_position: 4
tags: [gpu, cuda, synchronization, syncthreads]
---

# Block Synchronization

The warp-level tools covered so far — divergence handling, independent thread scheduling, the shuffle and vote intrinsics — all operate within a single warp of 32 threads. Most kernels that use shared memory need something coarser: a guarantee that every thread in the whole block, potentially many warps, has reached a point and that everything they wrote before that point is visible to everything they read after it. That guarantee is `__syncthreads()`, and getting its rules exactly right is what stands between a working tiled kernel and one that hangs or reads garbage on some inputs and not others.

## What `__syncthreads` guarantees

`__syncthreads()` gives two guarantees at once, and both matter:

1. **Execution barrier** — no thread in the block proceeds past the call until every thread in the block has reached it.
2. **Memory barrier** — all shared-memory and global-memory writes issued by any thread in the block before the call are visible to all threads in the block after the call.

The second guarantee is the one that's easy to forget. Without it, threads reaching the barrier at the same *time* wouldn't guarantee they see the same *data* — a write from one thread could still be sitting in a store buffer or cache line invisible to a read from another thread, barrier or no barrier. `__syncthreads()` closes both gaps together, which is exactly why it's the standard way to make a tile-load-then-compute pattern safe.

## The divergence rule

`__syncthreads()` has one hard rule: **every thread in the block must reach the same `__syncthreads()` call.** If any thread takes a path that skips it — because it returned early, or because it's inside a conditional block that some threads don't enter — the threads that do reach it wait for arrivals that will never come. This is undefined behavior, not a partial or degraded barrier: on real hardware it typically manifests as a hang, but the standard makes no promise about what happens instead of a hang, so it can just as easily produce silently wrong results.

```cpp showLineNumbers
// WRONG — threads with i >= n never reach the barrier
if (i < n) {
    tile[threadIdx.x] = in[i];
    __syncthreads();
}

// RIGHT — barrier is unconditional
tile[threadIdx.x] = (i < n) ? in[i] : 0.0f;
__syncthreads();
```

The fix is the same shape every time: move the barrier itself outside any conditional that isn't guaranteed uniform across the whole block, and push whatever bounds-checking is needed into the value being written instead of into whether the write (and the barrier after it) happens at all.

## The variants

Three variants combine the barrier with a whole-block reduction of a per-thread predicate, all computed as part of the same synchronization point rather than as a separate step after it:

| Variant | What it returns | Use |
|---|---|---|
| `__syncthreads_count(predicate)` | Number of threads in the block for which `predicate` was nonzero. | Counting how many threads in a tile satisfy some condition, e.g. how many elements passed a filter. |
| `__syncthreads_and(predicate)` | Nonzero only if `predicate` was true for every thread in the block. | A block-wide "did everyone succeed" check, e.g. all threads validated their input. |
| `__syncthreads_or(predicate)` | Nonzero if `predicate` was true for any thread in the block. | A block-wide "did anyone find something" check, e.g. early-exit search. |

All three share `__syncthreads()`'s divergence rule: every thread in the block must reach the call, even though what each thread passes as `predicate` can differ.

## `__syncwarp`

`__syncwarp(mask)` is the warp-scope counterpart introduced in [Independent Thread Scheduling](./independent-thread-scheduling.md): it barriers and fences only the lanes named in `mask`, not the whole block, which makes it cheaper and appropriate when code only needs to reconverge a warp rather than the entire block — for instance, after warp-level shared-memory traffic that didn't go through a `_sync` intrinsic. Reach for `__syncthreads()` when the guarantee needs to span multiple warps; reach for `__syncwarp()` when it doesn't, since a block-wide barrier makes every other warp in the block wait for no reason.

## Common deadlocks

Beyond the conditional-barrier pattern above, the same divergence rule bites in a few recurring shapes: a `__syncthreads()` inside a loop whose trip count differs per thread (some threads finish the loop and move on while others are still iterating and waiting at the barrier inside it); a `__syncthreads()` after a `return` that only some threads take; and a `__syncthreads()` inside an `if (threadIdx.x < activeCount)` guard where `activeCount` is less than the full block size. All three are the same underlying mistake — a barrier reachable by a strict subset of the block — wearing different syntax.

:::tip[Let the tools catch this for you]
Divergent-barrier bugs are notoriously input-dependent — a kernel can pass every test with a block size that happens to avoid the bad path and then hang the first time it doesn't. `compute-sanitizer --tool synccheck` detects divergent `__syncthreads()`/`__syncwarp()` calls directly instead of relying on noticing a hang. See [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md).
:::

## See also

- [Cooperative Groups](./cooperative-groups.md) — a higher-level, composable API that wraps block- and warp-level barriers like this page's.
- [Shared Memory](../04-cuda-memory-model/shared-memory.md) — the memory space most `__syncthreads()` calls exist to protect.
- [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md) — `synccheck` and the rest of the sanitizer toolkit.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
