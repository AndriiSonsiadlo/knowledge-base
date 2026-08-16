---
id: openvino
title: OpenVINO
sidebar_label: OpenVINO
sidebar_position: 9
tags: [gpu, npu, openvino, intel]
---

# OpenVINO

Most of the deployment stacks in this folder are strongest on hardware from one vendor, and OpenVINO's vendor is Intel. If the deployment target is an Intel CPU, an Intel integrated GPU, or the NPU built into a recent Intel Core Ultra laptop chip, OpenVINO is usually the toolkit that gets the most performance out of that hardware with the least fighting — it is Intel's own inference stack, tuned against Intel's own silicon, and it is the natural first thing to reach for once the deployment machine is known to be an Intel client device.

## What OpenVINO is for

OpenVINO takes a trained model from a training framework, converts it into a form its runtime can execute, and dispatches that execution across whichever Intel devices are present on the machine — CPU, integrated GPU, and NPU, in any combination. It is not a training framework and not a general-purpose tensor library; its whole job is the last mile between "a model that trains" and "a model that runs efficiently on the box it's being shipped to." That framing matters for scoping expectations: reach for OpenVINO when the target is known and Intel, not as a portable, vendor-neutral default the way [ONNX and ONNX Runtime](./onnx-and-runtimes.md) can be.

## Model conversion and the IR

OpenVINO's native format is the **IR** (Intermediate Representation): a pair of files, a `.xml` describing the model's topology and an accompanying `.bin` holding the weights. The current entry points for producing an IR are the `ovc` command-line tool and the `openvino.convert_model` Python function — both wrap the same conversion logic, `ovc` for a one-line CLI conversion and `openvino.convert_model` for cases that need Python-side control over inputs, such as PyTorch models, which only convert through the Python API. The older `mo` (Model Optimizer) command line tool that predates `ovc` is gone from current OpenVINO releases; documentation or tutorials that still reference `mo` are describing a retired tool.

It is worth being explicit that converting to IR is an optimization, not a requirement: OpenVINO's runtime reads ONNX files directly, and a model already in `.onnx` form can be handed straight to the OpenVINO runtime — including through [ONNX Runtime's OpenVINO execution provider](./onnx-and-runtimes.md), which wraps this same toolkit — without a conversion step at all. Converting to IR ahead of time buys IR-specific graph optimizations and skips ONNX-to-IR translation at load time, which matters for a model loaded repeatedly, but it is a performance decision, not a prerequisite for running the model on OpenVINO.

```bash
ovc model.onnx --output_model model
```

That single line reads `model.onnx` and writes `model.xml` and `model.bin` next to it, using default conversion settings. `openvino.convert_model` covers the same ground from Python, and is the only supported path for frameworks `ovc` cannot ingest directly, PyTorch chief among them — the function traces or scripts the model itself rather than parsing an already-exported file, so there is no separate export step to keep in sync with the conversion step.

## Device plugins

OpenVINO's runtime exposes the hardware it can target as named **device plugins**, and a running application selects one by name when it compiles a model:

| Plugin | Targets |
|---|---|
| `CPU` | Any x86 CPU; the universal fallback, available even without Intel-specific hardware |
| `GPU` | Intel integrated (and some discrete) GPUs |
| `NPU` | The NPU built into recent Intel Core Ultra laptop chips |

Each plugin is a separate backend with its own operator coverage and its own compiled representation of the model — the same operator-coverage caveat that applies to every NPU in this folder (see [What Is an NPU?](./what-is-an-npu.md)) applies to the `NPU` plugin here specifically, and a model with an operator the `NPU` plugin doesn't implement needs the same coverage check before deployment that any other fixed-function accelerator needs. Selecting a plugin is a one-line call — `core.compile_model(model, "GPU")` compiles for the integrated GPU, `"NPU"` for the NPU — and the same compiled-model object is what an application runs inference through regardless of which plugin ended up handling it, which is what makes swapping devices during development mostly a matter of changing that one string.

## AUTO, HETERO, and MULTI

Above the concrete device plugins sit three **virtual devices** that change how a model is mapped onto the hardware present, and their names are close enough to be worth pinning down precisely:

- **`AUTO`** inspects the available devices and picks one automatically, and it can start returning inference results from a fast-to-compile device like `CPU` while a slower-to-compile but faster-to-run device such as `GPU` finishes compiling in the background — so the application isn't stuck waiting on the best device's compile time before it can do any work at all.
- **`HETERO`** splits a single model across more than one device by operator support: OpenVINO queries which device supports which operation, partitions the graph along those lines, and runs each partition on the device assigned to it, connected by intermediate tensors.
- **`MULTI`** ran inference requests for one model across several devices simultaneously to raise throughput. It is now a deprecated legacy mode — its functionality has been folded into `AUTO`'s `CUMULATIVE_THROUGHPUT` performance hint, which loads the model onto every available candidate device and distributes requests across them the same way `MULTI` did. New code should reach for `AUTO` with that hint rather than naming `MULTI` directly.

:::tip[Throughput beats single-stream tuning on CPU and iGPU]
On CPU and integrated GPU specifically, running multiple inference requests concurrently in throughput mode — `ov::hint::PerformanceMode::THROUGHPUT` — extracts more total performance than almost any amount of tuning a single inference stream. That is because a single request rarely saturates all the execution resources these devices have; stacking requests fills the gaps. Latency mode (`ov::hint::PerformanceMode::LATENCY`) is a genuinely different configuration, optimized for the time-to-first-result of one request rather than aggregate volume, and picking the wrong one for the workload's actual goal is a common source of disappointing benchmarks.
:::

## Quantization with NNCF

OpenVINO's quantization tooling is **NNCF** (Neural Network Compression Framework), which covers both post-training quantization and quantization-aware training against OpenVINO, PyTorch, TensorFlow, and ONNX models. NNCF is where the vocabulary from [Quantization for Accelerators](./quantization-for-accelerators.md) — calibration, PTQ versus QAT, per-channel scales — becomes concrete API calls rather than theory; this page doesn't restate that vocabulary, only where it plugs in. In practice, NNCF's PTQ path takes a trained model plus a small calibration dataset and produces a quantized IR ready for the `CPU` or `NPU` plugin, both of which lean heavily on INT8 execution for their throughput.

## Where it fits

OpenVINO earns its place specifically on Intel client hardware — the combination of CPU, integrated GPU, and NPU that ships in a laptop or desktop, where its device plugins and virtual devices exist to exploit exactly that combination together. It is not the tool to reach for on an NVIDIA GPU (that's [TensorRT](./tensorrt.md)), on Apple silicon (that's Core ML), or on a mobile NPU from another vendor (see [Edge NPUs](./edge-npus.md)). Where it competes directly with [ONNX and ONNX Runtime](./onnx-and-runtimes.md) is in how you reach it: OpenVINO's own runtime and Python API is the deeper, more configurable path, while ORT's OpenVINO execution provider gives up some of that configurability for a single API surface that also covers non-Intel hardware through other execution providers.

## See also

- [ONNX and ONNX Runtime](./onnx-and-runtimes.md) — the execution-provider path into this same toolkit, and the vendor-neutral alternative when the target isn't fixed to Intel.
- [Edge NPUs](./edge-npus.md) — how Intel's laptop NPU compares to other vendors' fixed-function NPUs.
- [Quantization for Accelerators](./quantization-for-accelerators.md) — the PTQ/QAT vocabulary NNCF implements.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
