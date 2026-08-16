---
id: tensorrt
title: TensorRT
sidebar_label: TensorRT
sidebar_position: 7
tags: [gpu, npu, tensorrt, inference]
---

# TensorRT

The central fact to hold onto about TensorRT is that it is a *compiler*, not a runtime library you call into layer by layer. Given a model graph and the exact shapes, precisions, and target GPU you tell it about, it benchmarks candidate kernel implementations for every layer, picks the fastest ones for that specific hardware, fuses what it can, and emits a serialized **engine** — a compiled artifact, not a portable model file. That one fact explains everything else on this page: why building an engine is slow (it is a search over kernel candidates, not a translation), why the resulting engine is fast (every layer runs the kernel TensorRT found to be fastest on that GPU, for those shapes), and why the engine does not travel to a different GPU, a different TensorRT version, or often even a different driver.

## Build time versus run time

TensorRT's workflow splits cleanly into two phases with very different cost profiles. **Build time** takes a model description (most commonly ONNX), a target precision, and a range of input shapes, and produces an engine — this can take anywhere from seconds to tens of minutes, because the builder is timing multiple kernel implementations per layer against real hardware to pick winners. **Run time** loads that already-compiled engine and executes it — no search, no kernel selection, just the fixed plan the builder already worked out, which is why inference through a TensorRT engine has near-zero per-layer dispatch overhead compared to a graph interpreted layer by layer.

## Building an engine

`trtexec`, TensorRT's command-line tool, is how most people should build their first engine before reaching for the C++ or Python builder API directly:

```bash showLineNumbers
trtexec --onnx=model.onnx --saveEngine=model.plan \
        --fp16 --memPoolSize=workspace:4096 \
        --minShapes=input:1x3x224x224 \
        --optShapes=input:8x3x224x224 \
        --maxShapes=input:32x3x224x224
```

`--onnx` gives the source graph and `--saveEngine` names the output `.plan` file. `--fp16` requests half-precision kernels wherever TensorRT judges them safe. `--memPoolSize=workspace:4096` bounds the scratch memory (in MB by default) the builder's kernel search is allowed to use — a tighter budget can rule out an otherwise-faster kernel that needs more workspace than it's given, so this is a real accuracy-of-search knob, not just a memory cap. `--minShapes`/`--optShapes`/`--maxShapes`, each in `name:dimensions` form, are covered next.

## Precision modes

TensorRT can build an engine at several precisions, and mixing them per layer is normal rather than exceptional:

| Mode | Requirement | Notes |
|---|---|---|
| FP32 | None | The safe default; slowest, highest accuracy fidelity. |
| FP16 | `--fp16`; GPU with FP16 tensor-core or fast FP16 support | Usually the first thing to try — large speedup, small accuracy risk for most CNN and transformer workloads. |
| INT8 | `--int8`, plus either a calibration pass or Q/DQ (quantize/dequantize) nodes already baked into the ONNX graph | See [Quantization for Accelerators](./quantization-for-accelerators.md) for what those Q/DQ nodes encode. |
| FP8 | `--fp8`; GPU with FP8 tensor-core support (Ada Lovelace, Hopper and newer) | Newer than INT8 support; check the target GPU generation before committing to it. |

`--best` tells the builder to try every precision it has enabled for each layer and pick whichever is fastest without breaching an accuracy constraint, rather than forcing one precision uniformly across the whole graph — useful for exploration, though a manually chosen precision plan is usually more predictable for a production build.

## Dynamic shapes and optimization profiles

A TensorRT engine built for a single fixed input shape can only run that shape. **Optimization profiles** are the mechanism for supporting a range of shapes in one engine: `--minShapes`, `--optShapes`, and `--maxShapes` define the minimum, optimum, and maximum bound for each dynamic input dimension, and the builder selects and tunes kernels specifically for the *opt* shape while guaranteeing correctness (not peak performance) across the full min-to-max range. An engine can hold several profiles, switched at run time, rather than being limited to one.

:::tip[Narrow profiles beat one wide profile]
A single profile spanning batch 1 to 128 gives worse performance at both ends of that range than two narrower profiles — say, one tuned around batch 1–8 and another around batch 32–128 — because the builder can only tune kernels for one opt shape per profile, and a shape far from that opt point runs on a kernel selection that wasn't chosen with it in mind. If the deployment's batch sizes cluster into distinct regimes, build a profile per regime instead of one profile covering all of them.
:::

## Layer fusion

Part of what the builder does during the kernel search is fuse adjacent layers into single kernels wherever the pattern is recognized — the canonical example is folding a convolution, its bias add, and its following activation function into one fused kernel, avoiding two round trips to memory that separate kernels would each pay. The builder also chooses tensor layouts (which memory ordering of a tensor's dimensions is fastest for the kernels it picked) independently per tensor, sometimes inserting layout-conversion nodes that have no counterpart in the original graph at all. The practical consequence: an engine's internal layer names and structure, visible through TensorRT's engine-inspection tools, generally no longer correspond one-to-one with the layer names in the source ONNX graph, because fusion has merged several ONNX nodes into one TensorRT layer.

## Plugins

Not every operation a model graph might contain has a native TensorRT layer implementation. **Plugins** are the escape hatch: `IPluginV3` (the interface TensorRT 10 and later use; the older `IPluginV2DynamicExt` interface it replaced is deprecated as of TensorRT 10 and removed entirely in TensorRT 11) lets you register a custom layer implementation that the builder can insert wherever the unsupported op appears in the graph. Concretely, a plugin is a CUDA kernel — you are writing device code, defining its input/output shapes, and telling the builder how to schedule it into the compiled engine, which means the material in folders 03 through 07 of this section is the actual prerequisite for writing one, not this page.

## Engine portability

An engine is not a portable artifact in the way an ONNX file is. It is tied to the TensorRT version that built it, to the specific GPU architecture the kernel search ran against, and frequently to the exact driver version installed at build time — any of those changing can make a `.plan` file fail to load, or load and silently run a fallback path slower than the one it was built for.

:::warning[Build on the target, don't ship a `.plan` built elsewhere]
Because an engine is pinned to the TensorRT version, GPU architecture, and often the driver it was built against, the safe pattern is to build the engine on the actual deployment target, or inside a container that exactly matches the deployment environment — never to build once on a development machine and ship the resulting `.plan` file to a different machine or GPU generation. [Jetson and DLA](./jetson-and-dla.md) is the concrete case of this: an engine built off-device for a Jetson target should still be built inside a matching JetPack/TensorRT container, not cross-shipped from a desktop build.
:::

## See also

- [ONNX and ONNX Runtime](./onnx-and-runtimes.md) — the exchange format TensorRT engines are usually built from.
- [Quantization for Accelerators](./quantization-for-accelerators.md) — the INT8/FP8 vocabulary behind this page's precision modes.
- [Jetson and DLA](./jetson-and-dla.md) — TensorRT's role assigning layers to Jetson's DLA alongside its GPU.
- [Deploying to Accelerators](./deploying-to-accelerators.md) — where engine building fits in a full deployment pipeline.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
