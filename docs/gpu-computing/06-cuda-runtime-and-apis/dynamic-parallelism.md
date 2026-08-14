---
id: dynamic-parallelism
title: Dynamic Parallelism
sidebar_label: Dynamic Parallelism
sidebar_position: 7
tags: [gpu, cuda, runtime, dynamic-parallelism]
---

# Dynamic Parallelism

Most kernels launch from the host with a grid size chosen before any device-side work has happened, which is a poor fit for problems whose parallelism is only known once the GPU has started computing — a mesh that needs refining only in some regions, a tree whose branching factor varies by node, a search whose frontier grows unpredictably. Dynamic parallelism lets a kernel launch further kernels directly from the device, so the grid for the next phase can be sized from data the first phase just produced, without a round-trip through the host.

## Launching from the device

A device-side launch uses the same `<<<>>>` syntax as a host launch, from inside `__global__` code, and requires compiling with `-rdc=true` (relocatable device code) — see [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md) for what that flag changes about compilation. A parent thread that decides its tile needs finer-grained work can launch a child grid sized for exactly that tile:

```cpp showLineNumbers
__global__ void refineTile(float* data, int tileId) {
    if (needsRefinement(data, tileId)) {
        dim3 childGrid(subTileCount(tileId));
        dim3 childBlock(256);
        refineTile<<<childGrid, childBlock>>>(data, tileId);
    }
}
```

Only the tiles that actually need it spawn child grids; a tile that's already coarse enough does nothing further. This is the shape of problem dynamic parallelism is for: irregular, data-dependent subdivision that a fixed host-launched grid can't express without either over-provisioning or a host round-trip per level.

## CDP2 semantics

CUDA 12 and later use **CDP2**, and its synchronization model is stricter than older material describes. In CDP2, a parent grid **cannot** synchronize on its children with a device-side `cudaDeviceSynchronize()` — that API is removed from device code entirely, not merely discouraged. Any tutorial that shows a kernel calling `cudaDeviceSynchronize()` on itself to wait for child grids predates CDP2 and no longer compiles as written.

Child work is guaranteed complete only in two situations: when the parent grid itself completes (the runtime guarantees all of a grid's child launches finish before the parent grid is considered done), or through an explicit stream/event mechanism at the parent's tail — a child launched into a named stream, with an event recorded after it, that a later part of the same grid or a subsequent kernel waits on. There is no in-kernel blocking wait for "my children are done" anymore; the dependency has to be expressed structurally, the same way host-side stream and event dependencies are (see [Events and Timing](./events-and-timing.md)).

## What it costs

A device-side launch is not free, and it is not as cheap as the 3–10 µs of a host launch (see [CUDA Graphs](./cuda-graphs.md) for that figure) — each one carries meaningfully higher overhead, because the launch is issued and tracked by device-side runtime machinery rather than the host driver. `-rdc=true` also disables some cross-function optimizations the compiler can otherwise perform when everything is inlined into a single compilation unit. The runtime additionally reserves a fixed pool of device memory up front for pending child-grid launches; a program that launches far more concurrently pending children than that pool was sized for will fail to launch rather than queue indefinitely.

## Depth and resource limits

:::warning[Unbounded recursion exhausts the launch-depth limit]
A kernel that launches itself with no termination condition, or whose recursion depth depends on unvalidated input, can exceed the device's maximum nesting depth and fail. Cap recursion depth explicitly and size the pending-launch pool (`cudaDeviceSetLimit(cudaLimitDevRuntimePendingLaunchCount, ...)`) for the actual worst case rather than relying on defaults.
:::

## When it is the wrong tool

:::tip[Usually a host-side restructuring is simpler and faster]
A grid-stride loop with a device-side work queue, a persistent kernel that pulls new work items from a queue without ever exiting, or simply two host-launched kernels separated by a compacted work list are all usually simpler to reason about and cheaper than device-side launches. Reach for dynamic parallelism only when the child work is genuinely data-dependent, large enough to amortize the higher per-launch cost, and irregular enough that none of those alternatives fit naturally.
:::

## See also

- [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md) — what `-rdc=true` changes and why device-side launches require it.
- [CUDA Graphs](./cuda-graphs.md) — the other tool for cutting launch overhead, for topologies known ahead of time instead of discovered on the device.
- [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) — reducing launch count by restructuring instead of by launching from the device.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
