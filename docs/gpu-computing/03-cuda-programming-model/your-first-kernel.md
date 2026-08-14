---
id: your-first-kernel
title: Your First Kernel
sidebar_label: Your First Kernel
sidebar_position: 2
tags: [gpu, cuda, kernel, tutorial]
---

# Your First Kernel

Every CUDA program, no matter how large, is built from the same five moves: allocate device memory, copy input in, launch a kernel, copy output back, free what was allocated. SAXPY — `y = a*x + y`, scalar-times-vector-plus-vector — is small enough to show all five in one file without anything else getting in the way. The rest of this page walks the same file section by section.

## The program

```cpp showLineNumbers title="saxpy.cu"
#include <cstdio>

__global__ void saxpy(int n, float a, const float* x, float* y) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) y[i] = a * x[i] + y[i];
}

int main() {
    const int n = 1 << 20;
    const size_t bytes = n * sizeof(float);

    float* h_x = (float*)malloc(bytes);
    float* h_y = (float*)malloc(bytes);
    for (int i = 0; i < n; ++i) { h_x[i] = 1.0f; h_y[i] = 2.0f; }

    float *d_x, *d_y;
    cudaMalloc(&d_x, bytes);
    cudaMalloc(&d_y, bytes);
    cudaMemcpy(d_x, h_x, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_y, h_y, bytes, cudaMemcpyHostToDevice);

    const int threads = 256;
    const int blocks = (n + threads - 1) / threads;
    saxpy<<<blocks, threads>>>(n, 2.0f, d_x, d_y);

    cudaMemcpy(h_y, d_y, bytes, cudaMemcpyDeviceToHost);
    printf("y[0] = %f\n", h_y[0]);   // expect 4.0

    cudaFree(d_x); cudaFree(d_y);
    free(h_x); free(h_y);
    return 0;
}
```

## Allocating on the device

`cudaMalloc(&d_x, bytes)` reserves `bytes` of device memory and writes the device pointer into `d_x`. That pointer lives in the device's own address space — per [The Host–Device Model](../01-parallel-computing-foundations/the-host-device-model.md), it is not valid to dereference from host code, only to pass into a kernel launch or another CUDA API call.

## Copying in

`cudaMemcpy(d_x, h_x, bytes, cudaMemcpyHostToDevice)` moves the input arrays across PCIe (or NVLink) into the allocations just made. This call, on the default stream with unpinned host memory, blocks the host until the copy finishes — it is not the asynchronous, overlappable path described in the host–device model; that requires pinned memory and an explicit stream.

## Launching

`saxpy<<<blocks, threads>>>(n, 2.0f, d_x, d_y)` enqueues `blocks` blocks of `threads` threads each. The launch returns to host code immediately, before the kernel necessarily starts — launching is itself asynchronous, same as the copies would be on a non-default stream. Inside the kernel, `i = blockIdx.x * blockDim.x + threadIdx.x` computes each thread's unique position in the flattened 1-D index space; [Thread Indexing](./thread-indexing.md) covers this formula and its 2-D/3-D generalizations in full.

:::note[The ceiling-division and the bounds guard are a pair]
`(n + threads - 1) / threads` rounds the block count *up* so that every element gets a thread, which necessarily means the last block can have threads with `i >= n`. The `if (i < n)` guard inside the kernel is what keeps those extra threads from writing past the end of the array. Dropping either half — launching too few blocks, or launching enough but skipping the guard — is the most common first bug in a CUDA program.
:::

## Copying back and freeing

`cudaMemcpy(h_y, d_y, bytes, cudaMemcpyDeviceToHost)` blocks until the kernel has finished and the result has been copied back to host memory — a `cudaMemcpy` implicitly waits on all prior work on that stream. `cudaFree` and `free` release the device and host allocations respectively; each side manages its own memory independently, per the host–device model.

## Compiling and running

```bash
nvcc -O2 -arch=sm_80 saxpy.cu -o saxpy
```

`-arch=sm_80` tells `nvcc` which compute capability to generate code for — Ampere in this case. Running the resulting binary should print `y[0] = 4.000000`, matching `2.0 * 1.0 + 2.0`.

:::warning[This program checks no return codes]
Every CUDA API call here — `cudaMalloc`, `cudaMemcpy`, the kernel launch itself — can fail, and none of the failures are checked. That's fine for a first example, but every later page in this section uses `CUDA_CHECK(...)`, a wrapper macro defined in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md), and real code should too: an unchecked `cudaMalloc` failure surfaces later as a silent wrong answer or a segfault, far from where the actual problem occurred.
:::

## What just happened

Strip away the mechanics and this program paid three costs to do one add-and-multiply per element: two host-to-device copies (`x` and `y` in), one kernel launch, and one device-to-host copy (`y` out). For 2²⁰ floats, the copies move far more bytes across PCIe than the kernel does arithmetic on-chip — this is the shape of nearly every simple CUDA program, and it's also why transfer cost, not compute, dominates small or one-shot GPU workloads. [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md) covers how to make those copies faster and, eventually, overlap them with compute instead of paying for them serially.

## See also

- [Threads, Blocks, and Grids](./threads-blocks-and-grids.md) — the hierarchy `<<<blocks, threads>>>` launches into.
- [Thread Indexing](./thread-indexing.md) — the index formula this kernel used, generalized to 2-D and 3-D.
- [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) — the `CUDA_CHECK` macro every later example uses instead of ignoring return codes.
- [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md) — this same kernel revisited as a worked optimization example.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
