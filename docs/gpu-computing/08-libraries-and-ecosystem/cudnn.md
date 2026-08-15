---
id: cudnn
title: cuDNN
sidebar_label: cuDNN
sidebar_position: 3
tags: [gpu, cuda, libraries, cudnn]
---

# cuDNN

cuDNN is NVIDIA's library of tuned primitives for deep learning: convolution, pooling, normalization, attention, and the fused combinations of those that a training or inference framework needs on every forward and backward pass. Almost nobody calls it directly — PyTorch and TensorFlow both sit on top of it — but the API's organizing idea, the descriptor model, explains behavior that's otherwise mysterious from inside a framework: why the first iteration on a new input shape is slow, why results can differ slightly between runs, and why changing a batch size can suddenly change performance by more than the batch size alone would predict.

## What cuDNN covers

The library spans the operations that dominate a deep learning model's runtime: convolution (forward and both backward passes — with respect to input and to weights), pooling, batch and layer normalization, activation functions, softmax, RNN cells, and — since more recent releases — the fused attention kernels behind scaled dot-product attention. Each is exposed through the same descriptor-driven pattern rather than a bespoke API per operation.

## The descriptor model

cuDNN's organizing idea is declarative description followed by plan selection. Instead of calling a convolution function with raw pointers and dimensions, code first builds descriptors — `cudnnTensorDescriptor_t` for each tensor's shape, strides, and data type; `cudnnFilterDescriptor_t` for the convolution weights; `cudnnConvolutionDescriptor_t` for padding, stride, dilation, and group count — that together describe the problem completely, without committing to how it will be computed. Only after the shape is fully described does cuDNN choose an actual algorithm to run it. This separation between *describing* the problem and *selecting* a plan for it is what makes algorithm autotuning possible: cuDNN can benchmark several candidate implementations against the same descriptors and keep whichever wins, something that isn't possible with an API that hands the implementation raw pointers and expects it to just compute the answer.

## Algorithm selection and workspaces

Two APIs pick a convolution algorithm for a fully described problem, and they trade off differently. `cudnnFindConvolutionForwardAlgorithm` is empirical: it actually runs several candidate algorithms against the given descriptors and timing them, then returns the fastest — accurate, but it costs real GPU time up front. `cudnnGetConvolutionForwardAlgorithm_v7` is heuristic: it returns a ranked list of algorithms based on internal cost models and past benchmarking data, without executing anything, so it's essentially free but less precisely tuned to the exact hardware and shape at hand.

Whichever algorithm is chosen, most of them need a workspace buffer — device memory used as scratch space during the convolution, sized by the algorithm and returned alongside it. The caller is responsible for allocating that workspace and passing it into the actual convolution call; a workspace budget of zero silently rules out the fastest algorithms, which is why frameworks expose a workspace limit as a tunable.

:::tip[This is exactly what `torch.backends.cudnn.benchmark = True` toggles]
Setting that flag tells PyTorch to call the empirical, `cudnnFindConvolutionForwardAlgorithm`-style search the first time it sees a given input shape, cache the winning algorithm, and reuse it on every subsequent call with that same shape. That's why the first iteration after a shape change is measurably slower than the rest — it's paying the benchmarking cost the flag enables — and why the benefit disappears (or turns into a net loss) on a workload whose shapes vary every iteration, since the cache never gets to pay off.
:::

## The graph API

cuDNN 8 introduced the graph API as the library's current direction: instead of calling one fixed function per operation, the caller assembles a small operation graph — a convolution feeding into a bias add feeding into an activation, say — and cuDNN selects a **fused engine** that executes the whole graph as one kernel where possible. This is how `conv + bias + activation` becomes a single kernel launch instead of three separate ones, each with its own read and write of the intermediate tensor; it's the same fusion motivation that makes `cublasLt` epilogues worth having in [cuBLAS](./cublas.md), applied to the much larger operation set cuDNN covers.

## Where it sits under a framework

:::note[Most readers meet cuDNN through PyTorch or TensorFlow, and that's fine]
Very little application code calls cuDNN's C API directly — frameworks wrap it, choose algorithms on your behalf, and manage descriptors internally. The value of knowing the descriptor-and-plan model isn't writing raw cuDNN calls; it's diagnosing framework-level symptoms that only make sense in terms of it — a shape-dependent performance cliff (a new input shape triggering a fresh, uncached algorithm search), or a run that isn't bit-for-bit reproducible even with the same seed (see below).
:::

:::warning[Non-determinism]
Some cuDNN algorithms — certain backward-convolution implementations in particular — use atomic operations to accumulate results from multiple thread blocks, and the order those atomics land in is not fixed run to run. That makes those algorithms fast but not bitwise reproducible: the same inputs can produce results that differ in the last few bits of precision between two runs. cuDNN and the frameworks built on it expose a deterministic mode that restricts algorithm selection to reproducible implementations, trading some throughput for a guarantee that repeated runs match exactly — worth enabling when debugging a training divergence, not worth leaving on by default in production.
:::

## See also

- [cuBLAS](./cublas.md) — the dense-linear-algebra counterpart to cuDNN's deep-learning primitives, with its own fused-epilogue layer in `cublasLt`.
- [TensorRT](../12-npu-and-inference-accelerators/tensorrt.md) — the inference-time compiler that takes graph-level fusion further than cuDNN's graph API alone.
- [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) — the framework-level view of the algorithm selection and precision behavior this page explains from underneath.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
