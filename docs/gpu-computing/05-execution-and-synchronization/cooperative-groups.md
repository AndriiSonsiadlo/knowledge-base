---
id: cooperative-groups
title: Cooperative Groups
sidebar_label: Cooperative Groups
sidebar_position: 5
tags: [gpu, cuda, cooperative-groups, synchronization]
---

# Cooperative Groups

[Warp-Level Primitives](./warp-level-primitives.md) and [Block Synchronization](./block-synchronization.md) both work, but both lean on implicit context: a hardcoded `0xffffffff` mask that assumes full convergence, a `__syncthreads()` whose "everyone" is whatever the block happens to be, a warp size baked into the loop bound. Cooperative Groups replaces that implicit context with an explicit object. Instead of reasoning about "the warp" or "the block" as an ambient fact, you hold a group value with a well-defined `size()`, `thread_rank()`, `sync()`, and shuffle operations — the same operations, but scoped to a group you can name, pass to a function, and partition further. That explicitness is exactly what makes group-based code robust to independent thread scheduling: there is no implicit lockstep assumption left to break, because every operation states which threads it applies to.

## The idea

A *group* is a handle to a set of cooperating threads, obtained rather than assumed. `cg::this_thread_block()` gives you the whole block; partitioning it gives you smaller groups; a grid-wide or cluster-wide launch gives you larger ones. Every group type exposes the same small interface — `size()`, `thread_rank()`, `sync()` — so code written against a group works whether that group turns out to be a 32-lane tile or a multi-block grid. This is the payoff: the tiled-partition reduction below is not a smaller version of `warpReduceSum`, it is *the same kind of operation* expressed through the group API, and it composes with block- and grid-level groups the same way.

## `thread_block`

```cpp showLineNumbers
#include <cooperative_groups.h>
namespace cg = cooperative_groups;

__global__ void example() {
    cg::thread_block block = cg::this_thread_block();
    int rank = block.thread_rank();   // equivalent to a flattened threadIdx
    block.sync();                     // equivalent to __syncthreads()
}
```

`block.sync()` is `__syncthreads()` under another name — same execution barrier, same memory barrier, same divergence rule from [Block Synchronization](./block-synchronization.md): every thread in the block must reach it. Cooperative Groups doesn't change that rule; it gives you a handle you can pass into a function that needs to synchronize its caller's block without that function having to know it's a block, specifically, rather than some other group.

## Tiled partitions

`cg::tiled_partition<N>` splits a `thread_block` into fixed-size subgroups, most commonly 32-wide tiles that line up with a warp. A tile obtained this way carries the same guarantees as the group it was partitioned from — its `sync()` and shuffle operations are scoped to exactly its members, with no separate mask argument to get wrong:

```cpp showLineNumbers
#include <cooperative_groups.h>
#include <cooperative_groups/reduce.h>
namespace cg = cooperative_groups;

__device__ float tileReduceSum(float val) {
    auto block = cg::this_thread_block();
    auto tile  = cg::tiled_partition<32>(block);
    return cg::reduce(tile, val, cg::plus<float>());
}
```

Contrast this with `warpReduceSum` from [Warp-Level Primitives](./warp-level-primitives.md): that version is a hand-written loop over `__shfl_down_sync` with an explicit `0xffffffff` mask that is only correct because the caller guarantees full warp convergence at the call site. `tileReduceSum` needs no such promise from its caller — `tile`'s membership was established when it was partitioned, `cg::reduce` uses it internally, and the mask never appears in your code at all.

## `coalesced_group`

A `thread_block_tile<N>` assumes all `N` lanes are present. When a group's membership instead depends on runtime control flow — for example, only the threads that took one side of a branch — `cg::coalesced_threads()` captures exactly the currently-converged threads as a `coalesced_group`, the group-API equivalent of `__activemask()`. Like `__activemask()`, it answers "who is here right now," not "who the algorithm needs," so it carries the same caveat as `__activemask()` in [Warp-Level Primitives](./warp-level-primitives.md): reach for it when "whichever threads happen to be converged" is the actual intended semantics, such as opportunistically aggregating an atomic, not as a default replacement for a group whose membership should be fixed by the algorithm.

## `grid_group` and `cluster_group`

Two further group types extend the same interface beyond a single block:

- `grid_group`, obtained with `cg::this_grid()`, spans every thread in the launch. Its `sync()` is a grid-wide barrier — see [Grid-Wide Synchronization](./grid-wide-synchronization.md) for what that costs and requires.
- `cluster_group`, obtained with `cg::this_cluster()`, spans a thread block cluster and can synchronize and address shared memory across the blocks in it, as covered in [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md).

:::note[Launch and hardware requirements]
`grid_group::sync()` only works if the kernel was launched with `cudaLaunchCooperativeKernel` (a *cooperative launch*) — an ordinary `<<<grid, block>>>` launch does not provide the guarantee `grid.sync()` needs. `cluster_group` requires compute capability 9.0 or newer. See [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) for how to check what a target GPU supports.
:::

| Group type | Scope | How to obtain it | Cost of `sync()` |
|---|---|---|---|
| `thread_block_tile<N>` | Fixed-size subset of a warp (commonly 32) | `cg::tiled_partition<N>(block)` | Cheapest — register-level shuffle synchronization, no memory traffic. |
| `coalesced_group` | Whatever threads are currently converged | `cg::coalesced_threads()` | Same as a tile of that size; membership, not cost, is the difference. |
| `thread_block` | All threads in one block | `cg::this_thread_block()` | Same as `__syncthreads()` — a block-wide barrier and memory fence. |
| `cluster_group` | All threads in a thread block cluster | `cg::this_cluster()` | More expensive than a block barrier; cheaper than a grid barrier — see [Grid-Wide Synchronization](./grid-wide-synchronization.md). |
| `grid_group` | Every thread in the launch | `cg::this_grid()` (requires cooperative launch) | Most expensive — bounded by the slowest SM and capped by device occupancy. |

:::tip[Prefer the library reduction]
`cg::reduce` and `cg::inclusive_scan` compile down to the same shuffle sequences you would write by hand — there is no performance tax for using them — and they are correct by construction across every group type, including ones whose membership isn't a full warp. Prefer them to a hand-rolled loop unless you have a specific reason to write your own.
:::

## Why this replaces hand-rolled idioms

The pattern across [Independent Thread Scheduling](./independent-thread-scheduling.md), [Warp-Level Primitives](./warp-level-primitives.md), and [Block Synchronization](./block-synchronization.md) is the same each time: a hand-rolled idiom relies on an implicit, ambient fact — lockstep execution, a full-warp mask, "the whole block" — and breaks or silently produces wrong results when that fact stops holding. Cooperative Groups doesn't add new hardware capability over the raw intrinsics; a `tiled_partition<32>` reduction and a hand-written `__shfl_down_sync` loop compile to essentially the same instructions. What it adds is that the assumption becomes a value you can see, pass around, and partition, instead of a convention you have to remember and get right at every call site. That is why it is the modern default and the raw intrinsics are the layer underneath it, not a competing approach.

## See also

- [Warp-Level Primitives](./warp-level-primitives.md) — the raw shuffle and vote intrinsics that Cooperative Groups wraps.
- [Grid-Wide Synchronization](./grid-wide-synchronization.md) — what `grid_group::sync()` costs and the cooperative-launch requirement behind it.
- [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) — `cluster_group` and the CC 9.0+ hardware it depends on.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
