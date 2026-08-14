---
id: cuda-graphs
title: CUDA Graphs
sidebar_label: CUDA Graphs
sidebar_position: 6
tags: [gpu, cuda, runtime, graphs]
---

# CUDA Graphs

A single kernel launch costs the CPU roughly 3–10 µs of driver-side work, independent of how much the kernel actually does. A pipeline that issues 50 small kernels per iteration can spend more time launching work than the GPU spends computing it, and [Streams and Concurrency](./streams-and-concurrency.md) doesn't fix that — streams reorder and overlap launches, they don't reduce their count. A CUDA graph captures a whole sequence of operations once and replays it as a single launch, collapsing 50 dispatches into one.

## The launch-overhead problem

Every `<<<>>>` launch and every `cudaMemcpyAsync` call goes through the same host-side path: the driver validates arguments, builds a command, and pushes it onto a queue, and that fixed cost is paid on every single call regardless of how small the kernel is. For a pipeline made of many short kernels — a common shape in iterative solvers, small-tile image pipelines, and per-layer inference — that per-launch overhead can dominate the actual GPU time. A graph turns the whole sequence into a single node the driver has already validated, so replaying it pays that overhead once, not once per operation per iteration.

## Stream capture

Stream capture is the path most code should take, because it requires no restructuring — the same sequence of launches that already runs correctly on a stream is simply recorded instead of executed immediately:

```cpp showLineNumbers
cudaGraph_t graph;
cudaGraphExec_t exec;
cudaStream_t s;
CUDA_CHECK(cudaStreamCreate(&s));

CUDA_CHECK(cudaStreamBeginCapture(s, cudaStreamCaptureModeGlobal));
for (int i = 0; i < 50; ++i) smallKernel<<<grid, block, 0, s>>>(d_data, i);
CUDA_CHECK(cudaStreamEndCapture(s, &graph));

CUDA_CHECK(cudaGraphInstantiate(&exec, graph, nullptr, nullptr, 0));
for (int step = 0; step < steps; ++step)
    CUDA_CHECK(cudaGraphLaunch(exec, s));      // one launch replaces 50
CUDA_CHECK(cudaStreamSynchronize(s));
```

Between `cudaStreamBeginCapture` and `cudaStreamEndCapture`, nothing issued to `s` actually runs — the driver records the operations and their dependencies as a `cudaGraph_t` instead. `cudaGraphInstantiate` turns that recording into an executable `cudaGraphExec_t`, and every `cudaGraphLaunch` after that replays the entire 50-kernel sequence as one host call.

## Explicit construction

`cudaGraphAddKernelNode`, `cudaGraphAddMemcpyNode`, and their siblings build a `cudaGraph_t` directly, node by node, with explicit `cudaGraphAddDependencies` edges between them, instead of recording an existing stream sequence. This is more code than capture, so it's worth reaching for only when the topology is known ahead of time and isn't naturally expressible as a linear stream of launches — a DAG with branches and fan-in that capture's linear recording can't represent cleanly, or a graph built once by a library and reused across many callers that never run the equivalent stream sequence themselves.

## Instantiate once, launch many

`cudaGraphInstantiate` is the expensive step — it validates the whole graph and prepares the device-side representation the driver actually launches from. That cost is meant to be paid once. When only argument values change between iterations, not the graph's topology, `cudaGraphExecKernelNodeSetParams` updates a node's parameters on an already-instantiated `cudaGraphExec_t` directly, and `cudaGraphExecUpdate` does the same at the whole-graph level by diffing a freshly captured or built `cudaGraph_t` against the existing `cudaGraphExec_t` and patching only what changed. Both are far cheaper than instantiating from scratch every iteration.

## Updating a graph

A typical loop captures or builds the graph once, instantiates once, and then alternates between updating node parameters and launching:

```cpp showLineNumbers
for (int step = 0; step < steps; ++step) {
    CUDA_CHECK(cudaGraphExecKernelNodeSetParams(exec, node, &newParams));
    CUDA_CHECK(cudaGraphLaunch(exec, s));
}
CUDA_CHECK(cudaStreamSynchronize(s));
```

If the update fails — because the new node's type or resource usage isn't compatible with the instantiated graph — `cudaGraphExecUpdate` reports that explicitly, and the fallback is to destroy and re-instantiate.

:::warning[Capture forbids synchronous calls inside the captured region]
Anything that implicitly or explicitly synchronizes with the host — `cudaMalloc`, the synchronous form of `cudaMemcpy`, `cudaStreamSynchronize` on the stream being captured, or querying an event's status — is not capturable. Issuing one between `cudaStreamBeginCapture` and `cudaStreamEndCapture` turns the capture itself into an error rather than silently working. Allocate and query before capture starts, or move allocation to `cudaMallocAsync` (see [Memory Allocation APIs](./memory-allocation-apis.md)), which is capture-safe.
:::

## Where graphs pay off

:::tip[Graphs help when kernels are short and numerous, not when one dominates]
The saving is proportional to how much launch overhead the sequence was paying relative to its GPU time. A pipeline of many microsecond-scale kernels can see a large reduction in wall-clock time; a pipeline built around one kernel that already runs for milliseconds gains almost nothing, because launch overhead was never the bottleneck. Measure with [Nsight Systems](../09-tooling-profiling-and-debugging/nsight-systems.md) before adopting graphs — the CPU-side gaps between kernels in the timeline are the signal that a graph will actually help.
:::

## See also

- [Streams and Concurrency](./streams-and-concurrency.md) — the stream model that capture records into a graph.
- [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) — the other way to attack launch overhead, by reducing kernel count instead of launch count.
- [Nsight Systems](../09-tooling-profiling-and-debugging/nsight-systems.md) — where to confirm launch overhead is actually the bottleneck before adopting graphs.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
