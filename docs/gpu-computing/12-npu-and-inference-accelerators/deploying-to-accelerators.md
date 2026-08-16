---
id: deploying-to-accelerators
title: Deploying to Accelerators
sidebar_label: Deploying
sidebar_position: 11
tags: [gpu, npu, deployment, inference]
---

# Deploying to Accelerators

Every other page in this folder covers one piece of the deployment problem in depth — a device family, a runtime, a compiler, a quantization technique. This page is the one that ties them together into an order of operations: which decisions to make first, what to check before committing to a target, and what to verify before calling a deployment done. It is deliberately a procedure rather than a survey — the pages it links to already carry the depth, and repeating that depth here would only get it out of sync with the pages that own it.

## Choosing a target

The deployment environment usually narrows the choice of stack to one or two realistic options before any benchmarking happens, because the constraint that matters most — what hardware the model actually runs on — is usually fixed by the product, not chosen freely:

| Constraint | Target | Stack |
|---|---|---|
| Server, throughput-focused, NVIDIA GPUs | NVIDIA GPU | [TensorRT](./tensorrt.md) |
| Server with mixed or unknown hardware | Whatever's available | [ONNX Runtime](./onnx-and-runtimes.md) with execution providers |
| Intel client (laptop/desktop CPU, iGPU, NPU) | Intel client hardware | [OpenVINO](./openvino.md) |
| Apple client (iPhone, iPad, Mac) | Apple silicon | Core ML |
| Android / Qualcomm | Snapdragon Hexagon NPU | LiteRT or ONNX Runtime + the QNN execution provider |
| Microcontroller-class embedded | Arm Cortex-M + Ethos-U | TFLite Micro + Ethos-U (see [Edge NPUs](./edge-npus.md)) |
| Large-scale training or serving on Google Cloud | TPU | XLA (see [Google TPU](./google-tpu.md)) |

Picking a row in that table is the first real decision, and it should happen before any model-specific optimization work, because the rest of this page's steps depend on which stack is in play.

## Checking operator coverage first

[What Is an NPU?](./what-is-an-npu.md) already makes the underlying argument: a fixed-function accelerator implements a fixed operator set, and an unsupported operator forces a fallback whose layout-conversion cost can outweigh whatever the accelerated portion of the graph saved. The practical consequence for a deployment procedure is that operator coverage has to be checked *before* committing engineering time to a target, not discovered after the model is already exported and integrated. The concrete steps are the same across nearly every stack in the table above: export the model to ONNX, run the target's own compatibility or partitioning check against that ONNX graph — ORT's session creation with verbose EP logging (see [ONNX and ONNX Runtime](./onnx-and-runtimes.md)), OpenVINO's `query_model`, TensorRT's `trtexec` with `--onnx` and no build flags to see what parses — and read off the list of nodes the target can't place natively.

Doing this first, before any other optimization work, is plainly the single highest-leverage step in the whole procedure: a model with a handful of unsupported operators scattered through it is often faster to fix by replacing those operators with supported equivalents than to discover after weeks of integration work that the "accelerated" deployment barely beats the CPU baseline.

## Validating accuracy after quantization

Quantization work should follow the vocabulary and workflow in [Quantization for Accelerators](./quantization-for-accelerators.md) — this page adds only the validation discipline around it, not the technique itself. Two things matter for a deployment procedure specifically. First, the metric: compare the quantized model against the original, full-precision model on a held-out evaluation set using the actual task metric (classification accuracy, mAP, WER, whatever the model is graded on in production), not just the tensor-level mean squared error between quantized and unquantized outputs. A quantized model can have a deceptively small MSE against the original and still cross a decision boundary often enough to fail the task metric, or the reverse — a larger MSE that never changes an output decision. Second, the order of operations: define an acceptable accuracy budget — how many points of the task metric the deployment can afford to lose — *before* quantizing, not after looking at the number a particular quantization configuration happened to produce. Setting the bar after seeing the result invites rationalizing whatever number came out; setting it first turns validation into a pass/fail check against a target chosen for the right reasons.

## Latency, throughput, and batching

Batching improves throughput and worsens tail latency, and a deployment procedure has to pick a side of that tradeoff deliberately rather than default into one. Larger batches let an accelerator amortize per-launch overhead and keep more of its execution units busy per unit of wall-clock time, which raises aggregate throughput — but every request in a batch has to wait for the whole batch to be ready before any of them get a result, which raises the tail latency any individual request experiences. Serving stacks that sit in front of a model (ORT's server-side batching, Triton Inference Server, and similar) commonly implement **dynamic batching**: accumulate incoming requests for a short window or until a batch fills, then run them together, trading a small amount of added latency for a throughput gain that scales with how many requests land in that window. On an NPU specifically, this tradeoff can be less negotiable than it looks: many NPU toolchains compile the model for a fixed batch size ahead of time (the same static-shape constraint [Edge NPUs](./edge-npus.md) describes for edge NPUs generally), so batch size is a compile-time decision baked into the deployed artifact, not a runtime knob that can be tuned after the fact.

## Fallback paths

An accelerator target is not guaranteed to be present, free, or working at the moment inference actually needs to happen — it can be absent on some fraction of deployed devices, busy serving another process, or the specific model can simply fail to compile for that target because of an operator or shape it doesn't support. Every one of those is a normal operating condition, not an edge case, and a deployment that only has a happy path for "the accelerator is there and it works" will fail in production the first time reality diverges from that assumption. The fix is structural: a CPU execution path has to exist for every model shipped to an accelerated target, and that CPU path has to be exercised in testing, not just present in the code and assumed to work. [ONNX and ONNX Runtime](./onnx-and-runtimes.md)'s provider fallback and [OpenVINO](./openvino.md)'s `AUTO` device both build a version of this in at the framework level, but a deployment relying entirely on framework-level fallback still needs to verify, deliberately, that the fallback path produces correct output and acceptable (even if degraded) performance — not just that it doesn't crash.

## A deployment checklist

The steps above, in the order they should happen, verifiable one at a time:

1. Pick a target from the table above based on the actual deployment hardware, not the hardware that happens to be available for development.
2. Export the model to the target's exchange format (ONNX, in most cases) and run the target's operator-coverage or partitioning check before writing any integration code.
3. Fix or route around unsupported operators found in step 2, and re-check coverage until the unsupported set is small and understood.
4. If quantizing, set an accuracy budget against the task metric first, then quantize, then measure against that budget on held-out data — never on the calibration set.
5. Decide latency versus throughput deliberately: pick a batching strategy (fixed, dynamic, or none) that matches the actual serving requirement, and confirm whether the target compiles batch size in ahead of time.
6. Build and test a CPU fallback path explicitly — don't assume framework-level fallback is correct and performant without exercising it.
7. Re-validate accuracy and performance on the actual target hardware, not a development proxy, before calling the deployment done.

## See also

- [What Is an NPU?](./what-is-an-npu.md) — the operator-coverage argument this page's checklist builds on.
- [TensorRT](./tensorrt.md) — the deep option for the NVIDIA-GPU row of the target-selection table.
- [ONNX and ONNX Runtime](./onnx-and-runtimes.md) — export format and execution-provider fallback in depth.
- [Quantization for Accelerators](./quantization-for-accelerators.md) — the quantization vocabulary and technique this page's validation step assumes.
- [Compiler Stacks: XLA, TVM, MLIR](./compiler-stacks.md) — the compiler layer underneath several rows of the target-selection table.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
