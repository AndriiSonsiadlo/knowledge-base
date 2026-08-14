---
id: asynchronous-data-movement
title: Asynchronous Data Movement
sidebar_label: Async Data Movement
sidebar_position: 10
tags: [gpu, cuda, memory, memcpy-async]
---

# Asynchronous Data Movement

The classic tiled kernel loop looks like `load → __syncthreads() → compute → __syncthreads()`: every thread loads its piece of the next tile into shared memory, the block waits for everyone to finish loading, the block computes on the tile, and waits again before the next iteration can safely overwrite it. That structure is correct, but it wastes the SM twice over — the memory system sits idle for the entire compute phase, and the ALUs sit idle for the entire load phase, because loading and computing are forced to alternate rather than overlap. Asynchronous copy breaks that alternation: while stage *i* computes, stage *i+1*'s load can already be in flight.

## Why the copy should not block

A synchronous load — an ordinary assignment from a global-memory pointer into a shared-memory array — occupies a thread for the whole round trip: the thread issues the load, stalls until the data arrives, and only then can it do anything else, including help copy the *next* tile. `cuda::memcpy_async` (and its Cooperative Groups form, `cg::memcpy_async`) issues the copy and returns immediately, leaving the thread free to do other work — most usefully, computing on a tile that already finished loading in a previous iteration — while the copy engine moves the new tile's bytes in the background.

:::note[Genuinely asynchronous from CC 8.0+]
`cuda::memcpy_async` compiles and runs on older hardware too, but only from compute capability 8.0 (Ampere) onward does the copy actually bypass the SM's register file and execute asynchronously in dedicated hardware. Below CC 8.0, the same API call still works, but the underlying implementation degrades to a synchronous copy through registers — correct, but none of the overlap this page describes. Check [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) before assuming the asynchronous path is active.
:::

## `cuda::memcpy_async`

At its simplest, `cuda::memcpy_async` takes a destination, a source, a byte count, and a synchronization object — a `cuda::barrier` or a `cuda::pipeline` — that tracks when the copy has completed. The call itself doesn't block; completion is observed later, by waiting on that synchronization object rather than on the copy call.

## Barriers and pipelines

A `cuda::barrier` is the simpler of the two: threads arrive at it, and it completes once every expected thread (and every async copy registered against it) has arrived, much like `__syncthreads()` but able to also track outstanding asynchronous copies as first-class participants. `cuda::pipeline` builds a producer/consumer protocol on top of that idea, explicitly staged: `producer_acquire()` reserves a stage, `producer_commit()` marks a batch of async copies into that stage as submitted, `consumer_wait()` blocks until that stage's copies have actually landed, and `consumer_release()` frees the stage for reuse. The pipeline is what makes multi-stage double buffering expressible without hand-rolling the bookkeeping around a raw barrier.

## Double buffering

A two-stage pipeline keeps one tile loading while the previous tile is being computed on, cycling between two shared-memory buffers:

```cpp showLineNumbers
#include <cuda/pipeline>
#include <cooperative_groups.h>
namespace cg = cooperative_groups;

__global__ void pipelined(const float* g_in, float* g_out, int nTiles) {
    __shared__ float tile[2][256];
    auto block = cg::this_thread_block();
    constexpr size_t stages = 2;
    __shared__ cuda::pipeline_shared_state<cuda::thread_scope_block, stages> pss;
    auto pipe = cuda::make_pipeline(block, &pss);

    pipe.producer_acquire();
    cuda::memcpy_async(block, tile[0], g_in, sizeof(float) * 256, pipe);
    pipe.producer_commit();

    for (int t = 0; t < nTiles; ++t) {
        const int cur = t % stages, nxt = (t + 1) % stages;
        if (t + 1 < nTiles) {
            pipe.producer_acquire();
            cuda::memcpy_async(block, tile[nxt], g_in + (t + 1) * 256,
                               sizeof(float) * 256, pipe);
            pipe.producer_commit();
        }
        pipe.consumer_wait();
        // ... compute on tile[cur] ...
        pipe.consumer_release();
    }
    (void)g_out;
}
```

Before the loop starts, stage 0's copy is issued so there's already work in flight when the loop body runs. Each iteration issues the *next* stage's copy — if there is one — before waiting for the *current* stage, so the load for iteration `t + 1` overlaps with the compute for iteration `t` instead of following it.

## The Tensor Memory Accelerator

The Tensor Memory Accelerator (TMA) is a further step past `memcpy_async`: instead of many threads cooperatively copying a tile element by element, a single thread issues one instruction describing a whole multi-dimensional tile transfer — shape, strides, and source location encoded in a tensor map — and dedicated hardware executes the entire copy, including address generation, without occupying the rest of the block's threads or its address-generation units at all. It's driven through `cuda::device::experimental::cp_async_bulk_tensor_*` directly, or, more commonly, through a library like CUTLASS that generates the tensor-map setup and the TMA calls for you.

:::note[Requires CC 9.0+]
The Tensor Memory Accelerator is a Hopper-and-later feature. Check [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) before targeting it directly.
:::

## Alignment requirements

`memcpy_async` reaches its fastest hardware-accelerated path only when the copy is 16-byte aligned on both source and destination and moves elements of 4, 8, or 16 bytes. A copy that doesn't meet those conditions still compiles and still runs correctly, but silently falls back to a slower element-by-element path instead of the bulk-transfer path — there's no error or warning, just lost throughput, so alignment is worth checking explicitly rather than assumed.

## See also

- [Pinned Memory and Host Transfers](./pinned-memory-and-transfers.md) — the host-side asynchronous transfer this page's device-side pattern parallels.
- [Software Pipelining](../07-kernel-optimization/software-pipelining.md) — the double-buffering skeleton above, applied and tuned as a full optimization technique.
- [CUTLASS](../08-libraries-and-ecosystem/cutlass.md) — where TMA tensor-map setup is generated rather than hand-written.
- [NVIDIA Architecture Generations](../02-gpu-hardware-architecture/nvidia-architecture-generations.md) — where Ampere and Hopper sit relative to the CC 8.0/9.0 floors this page depends on.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
