---
id: thread-block-clusters
title: Thread Block Clusters
sidebar_label: Thread Block Clusters
sidebar_position: 6
tags: [gpu, cuda, clusters, hopper]
---

# Thread Block Clusters

Blocks are independent by design: no portable synchronization between them, no shared on-chip memory, and no guarantee two blocks even run at the same time. That independence is what lets a kernel scale from a laptop GPU to a data-center one, but it also means algorithms that need a *little* cross-block cooperation — a bit more shared memory than one block's SM can hold, or a barrier across a handful of blocks — have nowhere to turn. A thread block cluster relaxes exactly that restriction, for a small group of blocks the hardware guarantees will be co-resident on the same GPU Processing Cluster (GPC) at the same time.

## Why a level between grid and block

A cluster sits between the grid and the block in the hierarchy shown in [Threads, Blocks, and Grids](./threads-blocks-and-grids.md): the grid still contains many blocks, but those blocks are now grouped into clusters, and every block in a cluster is guaranteed to launch on the same GPC, co-resident with the rest of its cluster. That guarantee is the whole point — it is what makes distributed shared memory and cluster-wide barriers possible, neither of which the plain grid-of-blocks model can offer.

:::note[Requires CC 9.0+]
Thread block clusters are a Hopper-and-later feature. Check [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) before relying on them.
:::

## Declaring a cluster

The simplest way to launch a cluster is to fix its dimensions at compile time with the `__cluster_dims__` attribute on the kernel itself:

```cpp showLineNumbers
// Form 1: compile-time cluster dimensions
__global__ void __cluster_dims__(2, 1, 1) kernel_a(float* out) {
    namespace cg = cooperative_groups;
    cg::cluster_group cluster = cg::this_cluster();
    cluster.sync();
    // ...
}
```

`kernel_a` is still launched with the ordinary `<<<grid, block>>>` syntax; `__cluster_dims__(2, 1, 1)` fixes the cluster shape to 2 blocks along x, so the grid's block count must be a multiple of 2.

## Launching with `cudaLaunchKernelEx`

When the cluster dimensions need to vary at runtime — chosen from `cudaOccupancyMaxPotentialClusterSize`, for instance — use `cudaLaunchKernelEx` with a `cudaLaunchAttributeClusterDimension` attribute instead of a compile-time attribute on the kernel:

```cpp showLineNumbers
// Form 2: runtime cluster dimensions
cudaLaunchConfig_t config = {};
config.gridDim = dim3(numBlocks, 1, 1);
config.blockDim = dim3(256, 1, 1);

cudaLaunchAttribute attrs[1];
attrs[0].id = cudaLaunchAttributeClusterDimension;
attrs[0].val.clusterDim.x = 2;
attrs[0].val.clusterDim.y = 1;
attrs[0].val.clusterDim.z = 1;
config.attrs = attrs;
config.numAttrs = 1;

CUDA_CHECK(cudaLaunchKernelEx(&config, kernel_b, d_out));
```

`CUDA_CHECK` is the return-code wrapper introduced in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md); every launch in this section that can fail should be wrapped in it.

## Guaranteed co-residency

The guarantee a cluster provides is narrow but load-bearing: every block named in the cluster is resident on the same GPC before any of them starts running, so a block can assume its cluster-mates are already scheduled rather than racing to launch them. This is what makes it safe to reach into another block's shared memory — covered in [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) — instead of routing everything through global memory the way non-cluster blocks must.

## Cluster synchronization

Cooperative Groups exposes the cluster as `cg::cluster_group`, obtained with `cg::this_cluster()` as in the snippet above. `cluster.sync()` is a barrier across every block in the cluster — the cluster-scoped analogue of `__syncthreads()` inside a block — and it is the mechanism that makes it safe to assume every block's contribution to distributed shared memory is visible before continuing. [Cooperative Groups](../05-execution-and-synchronization/cooperative-groups.md) covers the rest of the API this type belongs to.

## Sizing and portability

The portable maximum is 8 blocks per cluster — any kernel that only ever asks for up to 8 will run on every CC 9.0+ GPU. Larger cluster sizes are hardware- and configuration-dependent and must be queried, not assumed; `cudaOccupancyMaxPotentialClusterSize` returns the actual ceiling for a given kernel and launch configuration rather than a number baked into the source.

:::warning[Clusters are not backward compatible]
A kernel launched with a non-trivial cluster size fails outright on pre-Hopper hardware — there is no silent fallback to non-clustered execution. Guard the launch with a `cudaDeviceProp::major` check (9 or higher) before choosing a cluster path, or ship two versions of the kernel and select between them at runtime.
:::

## See also

- [Threads, Blocks, and Grids](./threads-blocks-and-grids.md) — where clusters sit in the full hierarchy.
- [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) — what co-residency actually buys a cluster.
- [Cooperative Groups](../05-execution-and-synchronization/cooperative-groups.md) — the `cg::cluster_group` API in full.
- [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) — checking whether a target GPU supports clusters.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
