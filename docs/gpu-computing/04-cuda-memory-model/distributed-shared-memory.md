---
id: distributed-shared-memory
title: Distributed Shared Memory
sidebar_label: Distributed Shared Memory
sidebar_position: 9
tags: [gpu, cuda, memory, clusters]
---

# Distributed Shared Memory

[Shared Memory](./shared-memory.md) is scoped to a single block: fast, but invisible to every other block, even one running concurrently on the same SM. [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) exist precisely to relax that boundary — a cluster's blocks are guaranteed co-resident on the same GPC, and that guarantee is what makes it safe for one block to read and write another block's shared memory directly. Distributed shared memory (DSMEM) is that capability: the cluster's combined on-chip shared memory, addressable across block boundaries, without routing through global memory at all.

:::note[Requires CC 9.0+]
Distributed shared memory depends on thread block clusters, which are a Hopper-and-later feature — see [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) and check [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) before relying on it.
:::

## Shared memory across a cluster

Every block in a cluster still allocates and owns its own `__shared__` region exactly as it would outside a cluster — DSMEM doesn't create a new pool, it exposes the *union* of the cluster's per-block shared-memory regions to every block in the cluster. A block accessing its own shared memory does so exactly as before; accessing another block's requires an explicit address translation, because a raw shared-memory pointer is only ever valid within the block that allocated it.

## Mapping another block's shared memory

`cluster.map_shared_rank(addr, rank)`, from Cooperative Groups' `cg::cluster_group`, takes a pointer into *this* block's shared memory and the rank of another block in the cluster, and returns a pointer usable to access that *other* block's shared memory at the corresponding address. The mapping only works because every block in the cluster declares the same shared-memory layout — `map_shared_rank` translates the address, it doesn't look anything up by name.

## The cluster histogram

A histogram with more bins than fit in one block's shared memory is the canonical case for DSMEM: partition the bins across the cluster's blocks, have each block own a private slice, and let any thread in the cluster reach into the block that owns the bin it needs to increment.

```cpp showLineNumbers title="cluster_histogram.cu"
#include <cooperative_groups.h>
namespace cg = cooperative_groups;

__global__ void __cluster_dims__(2, 1, 1)
clusterHist(int* bins, const int* input, int n, int binsPerBlock) {
    extern __shared__ int smem[];
    cg::cluster_group cluster = cg::this_cluster();
    const unsigned rank = cluster.block_rank();

    for (int i = threadIdx.x; i < binsPerBlock; i += blockDim.x) smem[i] = 0;
    cluster.sync();

    for (int i = blockIdx.x * blockDim.x + threadIdx.x;
         i < n; i += blockDim.x * gridDim.x) {
        const int bin = input[i];
        const int owner = bin / binsPerBlock;         // which block owns this bin
        int* dst = cluster.map_shared_rank(smem, owner);
        atomicAdd(&dst[bin % binsPerBlock], 1);       // DSMEM atomic
    }
    cluster.sync();

    for (int i = threadIdx.x; i < binsPerBlock; i += blockDim.x)
        atomicAdd(&bins[rank * binsPerBlock + i], smem[i]);
}
```

This kernel assumes the total bin count equals `cluster.num_blocks() * binsPerBlock` exactly — a smaller total leaves `owner` and `map_shared_rank` reaching past the cluster's blocks, and a larger one drops the excess bins on the floor. Each block zeroes its own slice of `smem`, the first `cluster.sync()` guarantees every block's zeroing is visible before any block starts accumulating into it, every thread computes which block owns the bin it just read and does an `atomicAdd` through the mapped pointer for that block, the second `cluster.sync()` guarantees every cluster-wide contribution has landed before any block flushes its slice to global memory, and only then does each block add its own privatized bins into the final `bins` array.

## When it beats global atomics

Without a cluster, a histogram too large for one block's shared memory has exactly one fallback: atomics straight into global memory, contended across every block in the grid simultaneously. A cluster changes the arithmetic — instead of one grid-wide global-memory hot spot per bin, the bins are partitioned across `nBlocks` blocks, each privatizing its own slice on-chip. With the 48 KB-per-block shared-memory budget this example assumes, a cluster of `nBlocks` blocks makes `nBlocks × 48 KB` of privatized bin storage available on-chip in aggregate — atomics inside that footprint stay on-chip and contend only within the cluster, not across the whole grid.

:::warning[Missing a `cluster.sync()` is a silent race, not a crash]
`cluster.sync()` is required both **before** and **after** the DSMEM phase: the one before guarantees every block's zeroing is visible to every other block before any cross-block atomic touches it, and the one after guarantees every cross-block atomic has landed before any block reads its slice back out. Drop either barrier and the kernel still runs, still produces output, and usually produces the *wrong* output only some of the time — it's a data race, not a fault, and it won't reliably reproduce from run to run. `compute-sanitizer --tool racecheck` catches this class of bug; a kernel that touches distributed shared memory is exactly the kind of code worth running it against.
:::

## Constraints

A pointer returned by `map_shared_rank` is only valid for the lifetime of the cluster that produced it — using it after the cluster (or the owning block) has exited is undefined behavior, same as dereferencing any other shared-memory pointer after its block has retired. And only shared memory is mappable this way: there is no equivalent for reaching into another block's registers or local memory, both of which remain strictly private to the thread that owns them.

## See also

- [Shared Memory](./shared-memory.md) — the per-block scratchpad DSMEM extends across a cluster.
- [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) — the co-residency guarantee that makes DSMEM possible.
- [Histogram](../13-applied-kernels-and-patterns/histogram.md) — this kernel worked through as a full applied pattern.
- [Atomics](../05-execution-and-synchronization/atomics.md) — the `atomicAdd` semantics this kernel relies on, on-chip and off.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
