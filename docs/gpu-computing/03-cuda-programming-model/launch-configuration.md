---
id: launch-configuration
title: Choosing a Launch Configuration
sidebar_label: Launch Configuration
sidebar_position: 5
tags: [gpu, cuda, occupancy, launch]
---

# Choosing a Launch Configuration

`<<<blocks, threads>>>` looks like two arbitrary integers, but each one is a real decision with hardware consequences: block size determines how a block's resources are packed into an SM's fixed budgets, and grid size determines how evenly the total work spreads across the GPU's SMs. Picking both well is mostly a matter of a few rules of thumb plus one API that does the hardware-limit arithmetic for you.

## What you are actually choosing

Block size sets how many threads share an SM's register file and shared-memory pool per resident block — the exact tradeoff worked through in [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md). Grid size sets how many blocks exist in total, which — for a one-thread-per-element launch — is a function of the data size, and — for a grid-stride kernel — is a free parameter you get to choose independently of the data size.

## Block size

A few rules, each with a hardware reason behind it:

- **A multiple of 32.** Threads execute in warps of 32; a block size that isn't a multiple of 32 wastes lanes in its last warp on every block.
- **At least 64.** Sub-partitions within an SM need enough resident warps to hide latency; a block much smaller than 64 threads under-fills them even when several blocks are resident.
- **Rarely above 512.** Larger blocks consume more of the register file and shared-memory pool per block, which caps how many blocks can be resident simultaneously — and very large blocks also amplify the **tail effect** described below, since a single unfinished block occupies proportionally more of an SM's capacity.

256 is a common starting point that satisfies all three without being an actual rule.

## Grid size

For a one-thread-per-element launch, grid size follows directly from the data: `blocks = (n + threads - 1) / threads`, the ceiling division from [Your First Kernel](./your-first-kernel.md). For a grid-stride kernel, grid size is instead chosen for occupancy, independent of `n` — see below.

## The occupancy API

`cudaOccupancyMaxPotentialBlockSize` computes a block size that maximizes occupancy for a given kernel, using the kernel's actual register and shared-memory usage rather than a guess:

```cpp showLineNumbers
int blockSize = 0, minGridSize = 0;
CUDA_CHECK(cudaOccupancyMaxPotentialBlockSize(
    &minGridSize, &blockSize, saxpy_gs, 0, 0));
int gridSize = (n + blockSize - 1) / blockSize;
```

(`CUDA_CHECK` wraps a CUDA API call and aborts with a diagnostic on failure — defined in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md).) `minGridSize` is the smallest grid that keeps the whole device busy at that block size; for a one-thread-per-element kernel, `gridSize` above still needs to cover `n`, so the ceiling division against `blockSize` remains necessary.

## When 256 is not the answer

For a grid-stride kernel, sizing the grid for `n` at all is the wrong move — the point of the grid-stride loop is that the kernel doesn't care how many blocks it got. Instead, size the grid for occupancy directly: either take `minGridSize` from `cudaOccupancyMaxPotentialBlockSize` above, or compute `SM count × blocks per SM` by hand, where the SM count comes from:

```cpp
int smCount = 0;
CUDA_CHECK(cudaDeviceGetAttribute(&smCount, cudaDevAttrMultiProcessorCount, dev));
```

and blocks-per-SM is whatever `cudaOccupancyMaxActiveBlocksPerMultiprocessor` reports for the chosen block size — the same minimum-of-three-limiters calculation covered in [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md).

:::warning[The tail effect]
When the grid size isn't a clean multiple of the SM count, the last wave of blocks can leave most SMs idle waiting for a few stragglers to finish — a grid of 33 blocks on a 32-SM-wide machine launches a full wave of 32, then a second wave of just 1, and that second wave still costs close to as much wall-clock time as the first because every other SM sits idle waiting for it. The practical cost is nearly double the runtime of a grid of exactly 32, not the roughly 3% more work 33 vs. 32 blocks would suggest.
:::

:::tip[Measure]
`cudaOccupancyMaxPotentialBlockSize` optimizes occupancy, and occupancy is a proxy for performance, not the objective itself — a compute-bound kernel can be fastest at a block size the occupancy API wouldn't pick, per [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md#why-maximum-occupancy-is-not-the-goal). Treat the API's output as a well-informed starting point, then measure actual runtime across a few candidate block sizes; see [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) for the systematic version of this process.
:::

## See also

- [Thread Indexing](./thread-indexing.md) — the grid-stride loop this page's occupancy-based grid sizing is built for.
- [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md) — the hardware-limit calculation the occupancy API performs under the hood.
- [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) — measuring across candidate configurations instead of trusting the occupancy API's pick alone.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
