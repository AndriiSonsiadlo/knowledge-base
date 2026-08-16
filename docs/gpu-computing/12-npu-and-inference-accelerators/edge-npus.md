---
id: edge-npus
title: Edge NPUs
sidebar_label: Edge NPUs
sidebar_position: 4
tags: [gpu, npu, edge, mobile]
---

# Edge NPUs

"NPU" on a phone, laptop, or camera SoC does not name one architecture — it names a family of fixed-function inference engines from different vendors, each with its own SDK, its own supported precisions, and its own idea of how much of the operator set it covers. [What Is an NPU](./what-is-an-npu.md) covered why this class of hardware exists at all; this page is the vendor-by-vendor reference for the ones you're actually likely to target.

## What "edge NPU" covers

The term spans a wide range of silicon: Apple's Neural Engine on a phone or laptop SoC, Qualcomm's Hexagon on Snapdragon, Arm's Ethos-U on a microcontroller-class embedded part, and the newer Intel and AMD NPUs built into recent laptop chips. They share the fixed-function, compiler-scheduled design point from [What Is an NPU](./what-is-an-npu.md), but they differ enough in SDK, precision support, and operator coverage that "targets the NPU" is not a portable claim across vendors — code and models written for one rarely run unmodified on another.

## Apple Neural Engine

The Apple Neural Engine (ANE) ships in every recent iPhone, iPad, and Apple silicon Mac. There is no direct API for it at all — as [Metal and Apple Silicon](../11-portable-and-vendor-neutral/metal-and-apple-silicon.md) covers, the only path to the ANE is through Core ML, and Core ML's partitioner decides, operation by operation, whether a given piece of a model runs on the ANE, the GPU, or the CPU. You cannot force a specific layer onto it. Its main limitation follows directly from that: because placement is entirely out of your control and the operator set it accelerates isn't documented in detail, "my model supports the ANE" only means Core ML's partitioner *can* place some operations there, not that it will place most of the model there in practice.

## Qualcomm Hexagon

Qualcomm's Hexagon NPU is reached through the Qualcomm AI Engine Direct SDK, commonly called the QNN SDK, which builds a QNN graph from a model and dispatches it to a hardware backend — the NPU (referred to in Qualcomm's docs as the HTP), GPU, or CPU. In practice most users don't call QNN directly: ONNX Runtime's QNN execution provider and LiteRT (the current name for what shipped as TensorFlow Lite) both target Hexagon through the same underlying SDK, so a model already exported to ONNX or LiteRT format can reach the NPU without touching Qualcomm's API surface at all. Supported precisions center on INT8, with INT16 and FP16 available on newer Hexagon generations for operators sensitive to quantization error. The main limitation is the same operator-coverage story as any NPU: an op QNN doesn't implement forces a partition boundary back to CPU or GPU.

## Arm Ethos-U

Ethos-U is a different class of device entirely — a microNPU meant for Cortex-M microcontrollers, not phone or laptop SoCs. It is INT8-only in practice (8-bit or 16-bit signed operands are what the hardware accelerates; anything else doesn't run on it), and the entry point is TensorFlow Lite for Microcontrollers (TFLite Micro) combined with the Vela compiler. Vela takes an already-INT8-quantized `.tflite` model and rewrites the operators Ethos-U supports into a single custom Ethos-U operator, leaving unsupported operators untouched to run on the Cortex-M core itself via optimized CMSIS-NN kernels. The operator set Vela can map is small by design, and the whole model must be compiled ahead of time on a workstation — there is no on-device compilation or dynamic graph loading, which is the tradeoff for running inference in kilobytes of SRAM instead of gigabytes of DRAM.

## Laptop NPUs

Intel AI Boost and AMD XDNA are the NPUs built into recent Intel Core Ultra and AMD Ryzen AI laptop chips. Neither is meant to be programmed directly by most application code; the path in is through OpenVINO (Intel's own toolkit, and generally the best-performing route on Intel NPUs specifically), DirectML (Microsoft's hardware-abstraction API, with NPU support added as of DirectML 1.13 alongside ONNX Runtime 1.17), or ONNX Runtime's OpenVINO execution provider. These parts are positioned for sustained, low-power, always-on inference — background blur, voice detection, small local language models — rather than for winning a peak-throughput benchmark against the same laptop's GPU.

| NPU | SDK | Precisions | Typical use |
|---|---|---|---|
| Apple Neural Engine | Core ML only (no direct API) | INT8, FP16 | On-device vision/ML on iOS, iPadOS, macOS |
| Qualcomm Hexagon | QNN SDK / AI Engine Direct; also ONNX Runtime QNN EP, LiteRT | INT8 primary, INT16/FP16 on newer parts | Android and Windows-on-Snapdragon inference |
| Arm Ethos-U | TFLite Micro + Vela compiler | INT8 (8/16-bit signed) | Always-on microcontroller-class inference |
| Intel AI Boost / AMD XDNA | OpenVINO, DirectML, ONNX Runtime | INT8, FP16 | Sustained low-power inference on AI PCs |

## The common constraints

Across every vendor above, the same handful of constraints show up, because they all follow from the same fixed-function design point: precision is INT8 first, with INT4 or FP16 available on some parts and full FP32 essentially never; the operator set is fixed and smaller than what a GPU or CPU backend supports, so coverage has to be checked per model; compilation happens ahead of time rather than at load time, which means a model has to be exported and compiled for the specific target before it can run; tensor shapes are static, so a model with variable-length input needs padding or bucketing the same way [Google TPU](./google-tpu.md)'s shape-polymorphism problem does; and on-chip memory is small, which caps how large a model can run entirely on the NPU before it has to spill to system memory or partition across devices.

:::tip[Target the execution provider, not the native SDK]
For nearly all application code, the right way to reach an edge NPU is through ONNX Runtime or LiteRT with the vendor's execution provider — QNN EP for Hexagon, the OpenVINO EP for Intel, and so on — rather than calling QNN, Core ML, or a vendor SDK directly. The execution provider already handles graph partitioning, fallback, and format conversion; drop to the native SDK only when you need something the execution provider doesn't expose. See [ONNX and ONNX Runtime](./onnx-and-runtimes.md) for how that routing actually works.
:::

## See also

- [What Is an NPU](./what-is-an-npu.md) — the fixed-function design point every vendor here implements differently.
- [ONNX and ONNX Runtime](./onnx-and-runtimes.md) — the execution-provider model this page's tip points to.
- [OpenVINO](./openvino.md) — Intel's toolkit in depth, including its NPU plugin.
- [Metal and Apple Silicon](../11-portable-and-vendor-neutral/metal-and-apple-silicon.md) — Metal, MPS, and the Neural Engine's place alongside them.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
