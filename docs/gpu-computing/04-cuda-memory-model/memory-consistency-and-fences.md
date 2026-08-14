---
id: memory-consistency-and-fences
title: Memory Consistency and Fences
sidebar_label: Consistency & Fences
sidebar_position: 11
tags: [gpu, cuda, memory, atomics]
---

# Memory Consistency and Fences

Every earlier page in this section has quietly leaned on one synchronization primitive or another — `__syncthreads()`, a `cluster.sync()`, a pipeline's `consumer_wait()` — to make writes from one thread visible to reads from another. This page states the rule underneath all of them explicitly: CUDA's memory model is weakly ordered, and without an explicit fence or atomic, there is no guarantee about *when*, or even *whether*, one thread's writes become visible to another thread at all. Getting this wrong doesn't usually crash a kernel; it produces a result that's correct most of the time and silently wrong occasionally, which is far worse.

## The default is weak

Without synchronization, the compiler and the hardware are both free to reorder, delay, or cache a thread's memory operations in ways invisible to that thread itself but very visible to any other thread trying to observe them. Thread A writing `data = 42` followed by `flag = 1` gives no guarantee that thread B, spinning on `flag`, sees `data`'s new value the moment it sees `flag`'s — the two writes can become visible to B in either order, or with an arbitrary delay between them, unless something explicitly forbids that.

## Fences

A memory fence doesn't transfer data or synchronize threads the way a barrier does; it orders one thread's own prior memory operations relative to its later ones, as observed by other threads within a given scope.

| Fence | Scope |
|---|---|
| `__threadfence_block()` | orders memory operations as seen by other threads in the same block |
| `__threadfence()` | orders memory operations as seen by other threads on the same device |
| `__threadfence_system()` | orders memory operations as seen by the host and by peer GPUs, in addition to the calling device |

Wider scope costs more: `__threadfence_system()` has to make a write visible all the way out to the host and other GPUs, which is a materially more expensive operation than `__threadfence_block()` making it visible only within the issuing block.

## `volatile` is not a fence

`volatile` has exactly one effect: it prevents the compiler from caching a value in a register across accesses, forcing every read and write to actually touch memory instead of reusing a stale register copy. That's all it does — it says nothing about ordering relative to *other* threads' accesses, and it provides no synchronization whatsoever.

:::warning[Pre-Volta `volatile` warp tricks are broken today]
Older code sometimes used `volatile` on shared-memory arrays to implement warp-synchronous reduction without explicit synchronization, relying on the (then-true) assumption that a warp's threads executed in lockstep so a `volatile` write was "immediately" visible to the rest of the warp on the next instruction. Independent thread scheduling from Volta onward removed that lockstep guarantee, so this pattern is a data race on all current hardware, `volatile` or not — it may still appear to work by luck, which makes it worse, not better. The fix is `__shfl_sync` and the other `_sync` warp intrinsics, which carry explicit synchronization built in; see [Warp-Level Primitives](../05-execution-and-synchronization/warp-level-primitives.md).
:::

## Scoped atomics

`cuda::atomic<T, Scope>` combines an atomic read-modify-write or load/store with an explicit memory order, and the scope determines how far the ordering guarantee reaches — block, device, or system, the same three scopes the fence family uses:

```cpp showLineNumbers
#include <cuda/atomic>

__device__ cuda::atomic<int, cuda::thread_scope_device> flag{0};

// producer
data[0] = 42;
flag.store(1, cuda::memory_order_release);

// consumer
while (flag.load(cuda::memory_order_acquire) != 1) { /* spin */ }
int v = data[0];   // guaranteed to see 42
```

The release store on `flag` guarantees that `data[0] = 42` — everything the producer wrote *before* the release — is visible to any thread that observes the corresponding acquire load returning `1`. That pairing, release-then-acquire on the same atomic, is what makes `data[0]` guaranteed-visible to the consumer; without it, `data[0] = 42` and `flag.store(1)` (or `flag.load()` and reading `data[0]`) could be reordered relative to each other from the other thread's point of view.

## Putting it together

| I want to... | Use |
|---|---|
| Publish data to the rest of my block | `__syncthreads()` |
| Publish data to the rest of the device | a release atomic (`cuda::thread_scope_device`), or `__threadfence()` paired with a flag |
| Publish data to the host | `__threadfence_system()` plus a system-scope atomic (`cuda::thread_scope_system`) |

## See also

- [Asynchronous Data Movement](./asynchronous-data-movement.md) — the `cuda::pipeline`/`cuda::barrier` synchronization objects that build on these same ordering guarantees.
- [Atomics](../05-execution-and-synchronization/atomics.md) — the full atomic-operation API this page's scoped example draws from.
- [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md) — `__syncthreads()` in full, the block-scope entry in the table above.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
