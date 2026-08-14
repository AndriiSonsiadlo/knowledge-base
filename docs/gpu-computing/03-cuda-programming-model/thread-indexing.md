---
id: thread-indexing
title: Thread Indexing
sidebar_label: Thread Indexing
sidebar_position: 4
tags: [gpu, cuda, indexing, grid-stride]
---

# Thread Indexing

Every thread in a kernel runs the same code, so the only thing that makes it operate on *its* piece of the data rather than every thread's piece is the index it computes from its own position in the grid. Getting that formula right — and guarding it correctly — is the one piece of CUDA arithmetic that shows up in essentially every kernel, from SAXPY to the applied kernels later in this section.

## The 1-D formula

```cpp
int i = blockIdx.x * blockDim.x + threadIdx.x;
if (i < n) {
    // ... use data[i]
}
```

`blockIdx.x * blockDim.x` is the starting offset of this thread's block within the grid; adding `threadIdx.x` gives this thread's own position within the block, and the sum is the thread's global position in the flattened 1-D index space. The `if (i < n)` guard is required whenever the launch's total thread count doesn't divide evenly into `n`, which — because block counts are computed with ceiling division — is the common case.

## 2-D and 3-D

```cpp
int col = blockIdx.x * blockDim.x + threadIdx.x;
int row = blockIdx.y * blockDim.y + threadIdx.y;
if (col < width && row < height) {
    // ... use data[row * width + col]
}
```

```cpp
int x = blockIdx.x * blockDim.x + threadIdx.x;
int y = blockIdx.y * blockDim.y + threadIdx.y;
int z = blockIdx.z * blockDim.z + threadIdx.z;
if (x < width && y < height && z < depth) {
    // ... use data[(z * height + y) * width + x]
}
```

Each dimension applies the same 1-D formula independently, and each dimension needs its own bounds guard — a 2-D or 3-D launch is still ceiling-divided per axis, so out-of-range threads can occur on any axis independently of the others.

## Bounds guards

The guard exists because the launch configuration is chosen for convenient block sizes (multiples of 32, see [Choosing a Launch Configuration](./launch-configuration.md)), not for exact divisibility into the problem size. Skipping it doesn't usually crash — it silently reads or writes past the end of an array, corrupting unrelated memory or producing wrong answers that only show up for certain input sizes.

## Grid-stride loops

The formulas above assume the launch has exactly one thread per data element. A **grid-stride loop** removes that assumption: instead of one thread touching one element and then exiting, each thread starts at its global index and walks forward by the total number of threads in the grid, looping until it runs off the end of the data.

```cpp showLineNumbers
__global__ void saxpy_gs(int n, float a, const float* x, float* y) {
    for (int i = blockIdx.x * blockDim.x + threadIdx.x;
         i < n;
         i += blockDim.x * gridDim.x) {
        y[i] = a * x[i] + y[i];
    }
}
```

This decouples the kernel from the data size: the grid can be sized for occupancy — enough blocks to keep the SMs full — rather than for `n`, and the same kernel and the same launch configuration handle any `n`, from a few elements to far more than the grid has threads for.

:::tip[Prefer grid-stride loops by default]
Beyond decoupling grid size from data size, a grid-stride kernel is also easier to debug: launching it as `<<<1, 1>>>` still produces a correct (if slow) result, because the loop just does all the work sequentially in that one thread — useful for isolating a correctness bug from a scheduling or occupancy one.
:::

## Row-major indexing and pitch

`data[row * width + col]` assumes **row-major** layout — elements of a row are contiguous in memory, and moving to the next row means jumping `width` elements. That layout choice interacts directly with performance: within a warp, threads differ by `threadIdx.x` (the fastest-varying index in a typical 2-D launch), so making `col` — the fastest-varying array index — track `threadIdx.x` means adjacent threads in a warp touch adjacent memory addresses. If `row` were made the fastest-varying index instead, adjacent threads in a warp would stride by `width` elements per access, scattering the warp's requests across memory instead of letting them coalesce into one. [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) covers what coalescing actually buys and how to spot an access pattern that defeats it.

## See also

- [Threads, Blocks, and Grids](./threads-blocks-and-grids.md) — the hierarchy these formulas index into.
- [Choosing a Launch Configuration](./launch-configuration.md) — sizing the grid this indexing scheme runs over.
- [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) — why the fastest-varying index should map to `threadIdx.x`.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
