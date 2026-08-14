---
id: kernel-fusion-and-launch-overhead
title: Kernel Fusion and Launch Overhead
sidebar_label: Fusion & Launch Overhead
sidebar_position: 7
tags: [gpu, cuda, optimization, fusion]
---

# Kernel Fusion and Launch Overhead

Every kernel launch has a fixed cost — driver overhead to enqueue it, and a round trip through global memory for its inputs and outputs — that has nothing to do with how much useful arithmetic the kernel does. A chain of small, bandwidth-bound elementwise kernels can spend more of its wall-clock time paying that fixed cost, repeatedly, than doing the actual computation, which is what makes fusing them into a single launch — or avoiding the separate launches altogether — a real optimization rather than a stylistic preference.

## The cost of a launch

A kernel launch is not free even when it does almost no work: the driver has to enqueue the launch, and every kernel in a chain that reads its input from global memory and writes its output back to global memory pays that traffic regardless of how little arithmetic sits in between. For a chain of purely elementwise, memory-bound kernels, this launch and traffic overhead can dominate the actual computation.

## Fusing elementwise chains

Consider three elementwise kernels chained back to back — say, a scale, a bias add, and an activation — each reading the full array from global memory and writing it back:

```cpp showLineNumbers
// Three separate launches: the array is read and written three times.
__global__ void scaleKernel(float* x, float s, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) x[i] *= s;
}
__global__ void biasKernel(float* x, float b, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) x[i] += b;
}
__global__ void reluKernel(float* x, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) x[i] = fmaxf(x[i], 0.0f);
}
```

Each of the three launches reads and writes the whole array, for six total passes over `n` elements' worth of memory traffic. Fused into one kernel, the array is read once, held in a register for the whole chain, and written once:

```cpp showLineNumbers
// One launch: the array is read once and written once.
__global__ void scaleBiasReluFused(float* x, float s, float b, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    float v = x[i] * s + b;
    x[i] = fmaxf(v, 0.0f);
}
```

For a chain that is bandwidth-bound — which elementwise chains like this almost always are, since the arithmetic per element is trivial next to a global-memory round trip — going from three read-write passes to one is close to a 3x reduction in traffic, and correspondingly close to a 3x speedup on the memory-bound portion of the runtime. The exact multiplier depends on how much of the original runtime was actually spent on memory traffic versus fixed launch overhead and any non-elementwise work, but the direction and the mechanism — fewer trips through global memory and fewer launches — hold on any generation.

## When fusion hurts

Fusion is not free. A fused kernel's register footprint is the union of everything the separate kernels used, which can push a kernel that used to run at reasonable occupancy into spilling to local memory, or force the compiler to cap occupancy just to keep it within the register budget — the same tradeoff [Occupancy Tuning](./occupancy-tuning.md) covers for `__launch_bounds__`. Fusion can also hurt when it combines a memory-bound stage with a compute-bound one: run separately, each kernel is tuned to its own bottleneck, but fused, the memory-bound part idles the ALUs while it waits on DRAM and the compute-bound part idles the memory system while it computes, and neither resource is as well-served as it would be running on its own.

## Persistent kernels

An alternative to fusing at the kernel-launch level is not to re-launch at all: a **persistent kernel** launches one grid sized to exactly fill the device (one block per SM, or close to it) and has that grid loop internally over a work queue, pulling new work items until the queue is empty, instead of the host launching a fresh kernel per unit of work. This avoids launch overhead entirely after the first launch, and lets state that would otherwise have to round-trip through global memory between launches stay resident in registers or shared memory across iterations of the loop. The price is that the grid's size and shape are fixed for the whole run — there's no automatic load balancing across a changing number of blocks, since there's only ever one wave of blocks, and it caps occupancy at whatever fits on the SM alongside everything else the persistent kernel is holding onto.

## The alternatives

:::tip[Check whether the framework already fuses]
Before hand-writing a fused kernel, check whether the layer above CUDA already does it. `torch.compile`/Inductor and Triton both generate fused elementwise kernels automatically from a sequence of framework operations, and hand-fusing something they already fuse is wasted effort. See [Triton](../08-libraries-and-ecosystem/triton.md) and [Compiler Stacks](../12-npu-and-inference-accelerators/compiler-stacks.md).
:::

When the kernels genuinely can't be fused — because they're structurally different, not just adjacent elementwise passes — but launch overhead between them is still the problem, [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) is the answer: it captures the whole sequence of launches once and replays them as a single graph submission, removing the per-launch driver overhead without requiring the kernels themselves to become one kernel.

## See also

- [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) — removing launch overhead between kernels that can't be fused.
- [Triton](../08-libraries-and-ecosystem/triton.md) — a compiler that generates fused elementwise kernels automatically.
- [Softmax and LayerNorm](../13-applied-kernels-and-patterns/softmax-and-layernorm.md) — a worked kernel where fusing several elementwise/reduction stages is the whole point.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
