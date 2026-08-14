---
id: grid-wide-synchronization
title: Grid-Wide Synchronization
sidebar_label: Grid-Wide Sync
sidebar_position: 7
tags: [gpu, cuda, synchronization, cooperative-groups]
---

# Grid-Wide Synchronization

`__syncthreads()` barriers a block; `cluster.sync()` barriers a cluster; neither reaches every block in a grid. Some algorithms genuinely need that — a multi-pass iterative solver that must finish writing generation *N* everywhere before any block reads generation *N* for generation *N+1*, for instance — and the usual answer, launching a second kernel between the passes, has real cost when the intermediate state is large and expensive to leave and re-establish. Grid-wide synchronization exists for that case, but it is not simply "a bigger `__syncthreads()`": it comes with a hardware constraint that shapes the whole launch around it.

## Why blocks cannot normally sync

An ordinary `<<<grid, block>>>` launch makes no promise that every block is running at the same time. The GPU schedules blocks onto SMs as capacity frees up, and a grid can easily contain far more blocks than can be resident simultaneously — later blocks start only as earlier ones finish. A barrier across blocks that aren't all resident is unsatisfiable: a block waiting at the barrier for a block that hasn't even been scheduled yet would wait forever. That's why there is no plain intrinsic for "wait for the whole grid" the way `__syncthreads()` waits for the whole block — the scheduling model doesn't support it by default.

## Cooperative launch

A *cooperative launch*, via `cudaLaunchCooperativeKernel`, changes that guarantee: it tells the driver the kernel needs every block resident at once, and the driver refuses to launch more blocks than the device can run concurrently. In exchange for that constraint, the kernel gets access to a real grid-wide barrier through `cg::this_grid()`.

## `grid.sync()`

Inside a cooperatively-launched kernel, `cg::this_grid()` returns a `grid_group`, and `grid.sync()` is the barrier: no thread in any block proceeds past the call until every thread in every block of the grid has reached it, with the same execution-and-memory-barrier guarantee `__syncthreads()` gives at block scope, just extended to the entire launch.

```cpp showLineNumbers
__global__ void myCoopKernel(float* d_data, int n) {
    namespace cg = cooperative_groups;
    cg::grid_group grid = cg::this_grid();

    // ... pass 1 over d_data ...
    grid.sync();
    // ... pass 2, safe to read what every block wrote in pass 1 ...
}
```

The launch itself has an unusual shape compared to `<<<grid, block>>>`, because the grid size can't just be "however many blocks the problem wants" — it has to be sized to what the device can actually run at once:

```cpp showLineNumbers
void* args[] = { &d_data, &n };
int blocksPerSm = 0;
CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(
    &blocksPerSm, myCoopKernel, threads, 0));
int smCount = 0;
CUDA_CHECK(cudaDeviceGetAttribute(&smCount, cudaDevAttrMultiProcessorCount, 0));
dim3 grid(smCount * blocksPerSm), block(threads);
CUDA_CHECK(cudaLaunchCooperativeKernel(
    (void*)myCoopKernel, grid, block, args));
```

See [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) for what `CUDA_CHECK` does.

## The occupancy constraint

`grid.sync()` is sound only *because* every block in the launch is resident on an SM simultaneously — that's the property that makes "wait for everyone" answerable instead of a hang. That property doesn't happen automatically; it's exactly why the launch above queries `cudaOccupancyMaxActiveBlocksPerMultiprocessor` instead of picking a grid size from the problem size the way an ordinary kernel would. `blocksPerSm * smCount` is the largest grid the device can actually run all at once given this kernel's register and shared-memory usage per block; launching anything larger with `cudaLaunchCooperativeKernel` fails outright rather than silently under-syncing. If your problem is bigger than that grid, the kernel has to grid-stride internally — it cannot simply ask for more blocks the way a non-cooperative kernel can.

## When a second kernel is better

:::tip[Two launches are usually cheaper than the constraint]
A second kernel launch costs on the order of a few microseconds and imposes no occupancy cap at all — the runtime is free to schedule however many blocks the problem actually needs, in whatever order. A cooperative launch is worth its constraint only when the kernel needs to keep substantial state resident in registers or shared memory *across* the barrier, so that tearing it down and rebuilding it in a second kernel would be more expensive than the launch itself. For workloads that are mostly about avoiding launch overhead rather than preserving live state, [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) cuts that overhead directly without requiring a grid-wide barrier at all.
:::

:::note[`cluster.sync()` is the cheaper middle ground]
On compute capability 9.0 and newer, a thread block cluster's `cluster.sync()` synchronizes a smaller group of blocks — one cluster's worth — without needing a full cooperative launch or occupying the entire device. When the coordination only needs to span a handful of blocks rather than the whole grid, a cluster is usually the better fit. See [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) and [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).
:::

## See also

- [Cooperative Groups](./cooperative-groups.md) — the `grid_group` and `cluster_group` API this page's barrier is built on.
- [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) — the CC 9.0+ cluster hierarchy and its own, cheaper `sync()`.
- [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) — cutting launch overhead without a grid-wide barrier.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
