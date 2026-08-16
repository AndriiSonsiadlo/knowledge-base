---
id: onnx-and-runtimes
title: ONNX and ONNX Runtime
sidebar_label: ONNX & Runtimes
sidebar_position: 8
tags: [gpu, npu, onnx, inference]
---

# ONNX and ONNX Runtime

Getting a model off a training framework and onto an arbitrary piece of inference hardware needs a common description both sides agree on. ONNX is that description: a standardized, framework-neutral way to write down a model graph so that PyTorch, and separately TensorRT, and separately a phone's NPU compiler, can all read the same file and agree on what it means. What actually executes that file is a different question, and conflating the two is the single most common confusion this page exists to clear up.

## The exchange format

ONNX itself is a specification and a protobuf serialization: a graph of typed tensors connected by versioned operators, plus enough metadata (shapes, data types, initializers) to describe a model's structure and weights without any code. It is not a runtime — an `.onnx` file does not know how to execute itself, any more than a `.json` schema knows how to run a server. ONNX's job stops at describing the graph faithfully; something else has to consume it.

## Opsets

Every ONNX operator is versioned, and a model's **opset version** is the compatibility axis that governs whether a given operator's *definition* — not just its name — matches between the exporter that wrote the graph and the runtime that reads it. An exporter (say, PyTorch's `torch.onnx.export`) targets a specific opset when it writes a graph; a runtime supports a range of opsets it knows how to execute. When those don't overlap for a given operator, the most common outcome in practice is an "unsupported operator" or "unsupported opset version" error — which is misleading, because the operator itself is usually implemented; the runtime just doesn't have that revision of its definition. Most of what look like missing-feature errors during export are actually opset mismatches, and are fixed by changing the exporter's target opset, not by rewriting the model.

## ONNX Runtime

ONNX Runtime (ORT), maintained by Microsoft, is the dominant engine that consumes ONNX graphs and executes them — one implementation among several ONNX-consuming runtimes, but the one most deployments default to. It loads a graph, runs a set of graph-level optimizations, partitions the graph across whichever hardware backends are available, and executes it, exposing the same session API regardless of which hardware ends up doing the work underneath.

## Execution providers

ORT's hardware abstraction is the **execution provider (EP)**: a pluggable backend that claims some subset of a graph's nodes and executes them on specific hardware. A single inference session can use several EPs at once, each handling the nodes it supports.

| Execution provider | Target hardware | Maturity |
|---|---|---|
| CPU | Any CPU | Always available; the universal fallback every ORT build ships with. |
| CUDA | NVIDIA GPUs | Mature, widely used in production. |
| TensorRT | NVIDIA GPUs, via a TensorRT-compiled engine | Mature for supported ops; fastest NVIDIA path when the whole graph is TensorRT-eligible, at the cost of TensorRT's own build-time compilation. |
| DirectML | Any DirectX 12 GPU on Windows | Mature on Windows; the vendor-agnostic way to reach NVIDIA/AMD/Intel GPUs from one EP. |
| CoreML | Apple silicon (GPU/Neural Engine) | Mature on macOS/iOS; the standard path to Apple's Neural Engine from ORT. |
| QNN | Qualcomm Hexagon NPUs (Snapdragon) | Actively developed; operator coverage narrower than CPU/CUDA, growing quickly. |
| OpenVINO | Intel CPUs, integrated GPUs, and VPUs | Mature on Intel hardware; see [OpenVINO](./openvino.md) for the toolkit ORT is wrapping here. |
| ROCm | AMD GPUs | Functional, less mature than CUDA; coverage and tuning lag the NVIDIA path. |

EPs are registered with a session in priority order, and ORT assigns each graph node to the highest-priority EP that claims support for it.

## Provider fallback

Priority-ordered assignment is also where performance quietly leaks away. If a node in the graph isn't supported by the top-priority EP, ORT falls back to the next EP in the list — commonly all the way down to CPU — for that one node, then hands control back to the higher-priority EP for the next supported node. Each such handoff is a graph partition boundary, and each boundary means a memory transfer: data has to move from the accelerator's memory space to host memory for the CPU fallback node, then back again for the next accelerated segment. A graph with several small unsupported nodes scattered through it can spend more time on these transfers than the accelerated segments ever save — the same operator-coverage failure mode [What Is an NPU?](./what-is-an-npu.md) describes generically, here made concrete as an EP priority list.

The way to find these boundaries is not to guess from throughput numbers but to look at the actual partitioning. Setting `sess_options.log_severity_level = 0` (verbose) before creating the session makes ORT log, per node, which EP it was assigned to — the concrete way to see "this op landed on CPUExecutionProvider" rather than inferring it from a suspiciously slow run. `sess_options.enable_profiling = True` is the complementary tool: it produces a JSON trace of per-operator timings that, read alongside the verbose EP-assignment log, shows exactly where time is going and which nodes triggered a fallback.

:::warning[Check node assignment before trusting "runs on the NPU"]
A model reported as "running on the NPU" or "running on the GPU" may in fact be running mostly on that device with several nodes silently falling back to the CPU, each fallback costing a memory transfer in and out. Enable verbose logging or profiling and check the actual per-node provider assignment before treating a deployment's hardware target as confirmed — a plausible-sounding claim about where a model runs is not the same as verified node assignment.
:::

## Graph optimizations

Independent of which EP eventually runs a node, ORT applies its own graph-level optimizations before partitioning: constant folding, redundant node elimination, and operator fusion (for example, folding a MatMul and its following Add into a single fused node), organized into basic, extended, and layout-optimization levels that run in that order. These optimizations reduce the graph ORT actually hands to the EPs, which in turn changes what "the graph" even means when comparing node counts against the original ONNX file.

## Exporting cleanly

A model that exports without errors is not the same as a model that exports *well* for accelerator deployment. A few habits keep the exported graph deployment-friendly: prefer operations that constant-fold rather than leaving computable-at-export-time values as runtime ops; avoid data-dependent control flow (a loop or branch whose trip count or condition depends on tensor values) since most accelerator backends, including TensorRT and most NPUs, need statically known control flow; prefer static input shapes over dynamic ones wherever the deployment target requires them, since dynamic-shape support varies sharply across EPs and hardware; and validate the exported graph's numerical output against the original framework on real inputs before spending any effort optimizing it further — an export bug caught after optimization is much harder to isolate than one caught immediately after export.

## See also

- [TensorRT](./tensorrt.md) — the compiler behind ORT's TensorRT execution provider, and the deeper option when a graph is fully TensorRT-eligible.
- [OpenVINO](./openvino.md) — the toolkit underlying ORT's OpenVINO execution provider on Intel hardware.
- [Edge NPUs](./edge-npus.md) — the mobile/embedded NPU vendors QNN and CoreML are reaching in the table above.
- [Deploying to Accelerators](./deploying-to-accelerators.md) — where export and EP selection fit into a full deployment workflow.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
