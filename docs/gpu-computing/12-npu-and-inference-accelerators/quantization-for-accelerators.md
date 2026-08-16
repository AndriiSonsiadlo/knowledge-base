---
id: quantization-for-accelerators
title: Quantization for Accelerators
sidebar_label: Quantization
sidebar_position: 6
tags: [gpu, npu, quantization, int8]
---

# Quantization for Accelerators

An NPU's MAC array (see [What Is an NPU?](./what-is-an-npu.md)) is built around integer arithmetic first and floating point second, if at all. Getting a model onto that hardware efficiently means converting its weights and activations from floating point into integers in a way that a fixed set of scale and offset numbers can undo well enough that the model still works. That conversion — quantization — is a distinct engineering discipline from anything in ordinary model training, with its own vocabulary, its own failure modes, and its own tooling, and this page is that vocabulary.

## Why accelerators want integers

The case for quantization is a hardware argument before it is an ML argument. An INT8 multiply-accumulate unit is smaller and cheaper in silicon than an FP16 one, so a fixed die area packs more INT8 MACs than FP16 ones, and more MACs per cycle is more throughput. INT8 weights also take a quarter of the memory of FP32 weights and half of FP16 — and most inference workloads, especially at batch size 1 on an edge device, are memory-bandwidth bound rather than compute bound, so cutting the bytes that have to move is most of the win before a single extra MAC has fired. Quantization is therefore not a compression trick applied after the fact; it is close to the reason fixed-function inference silicon looks the way it does.

## The affine mapping

Every common quantization scheme is a variant of the same affine map between a real value `x` and its quantized integer representation `q`:

```text
q = round(x / s) + z
x ≈ s × (q − z)
```

`s` is the **scale** — a positive real number giving the size of one integer step in real units — and `z` is the **zero-point**, the integer that real value `0.0` maps to. The two directions are inverses of each other up to the `round()` used to go forward, which is why the reverse direction only recovers `x` approximately: quantization is inherently lossy, and `s` and `z` are exactly the two numbers a quantized accelerator carries around per tensor (or per channel) to make the mapping usable. **Symmetric quantization** forces `z = 0`, so the map reduces to `q = round(x / s)` and `x ≈ s × q` — real `0.0` always maps to integer `0` exactly, at the cost of wasting range if the real distribution isn't centered on zero.

## Symmetric versus asymmetric

| | Symmetric | Asymmetric |
|---|---|---|
| Zero-point `z` | Fixed at `0` | Any integer in the quantized range |
| Hardware cost | Cheaper — no zero-point offset to add back after every MAC | More expensive — the offset term has to be folded into the accumulation |
| Typical use | Weights, which are usually roughly zero-centered | Activations, especially after ReLU where the distribution is one-sided |
| Accuracy on skewed distributions | Poor — wastes representable range on values that don't occur | Good — the integer range can be shifted to cover exactly where the real values live |

Weights are quantized symmetrically almost everywhere because the extra hardware cost of a nonzero `z` buys little: weight distributions cluster around zero and a fixed `z = 0` rarely wastes much range. Activations, particularly the output of a ReLU or similar one-sided nonlinearity, are often quantized asymmetrically because forcing `z = 0` on a distribution that never goes negative wastes roughly half the integer range on values that never occur.

## Per-tensor versus per-channel

A quantization scheme can use one `(s, z)` pair for an entire tensor (per-tensor) or one pair per output channel of a weight tensor (per-channel). Per-channel is the standard choice for weights because different output channels of the same convolution or linear layer can have dynamic ranges that differ by orders of magnitude — a single per-tensor scale has to accommodate the widest channel, which quantizes every narrower channel far too coarsely. Per-channel quantization for activations is far less common, and often unsupported in hardware outright, because activation channels are the *reduction* dimension the MAC array sums over — giving each one a different scale would require rescaling mid-accumulation, which the fixed-function datapath isn't built to do.

## PTQ and QAT

| | Post-training quantization (PTQ) | Quantization-aware training (QAT) |
|---|---|---|
| Effort | Low — a calibration pass over the existing trained model | High — requires re-running (part of) training with fake-quantized ops in the graph |
| Data needed | A few hundred unlabeled representative samples | The original (or a substantial subset of the) labeled training set |
| Typical accuracy recovery | Good at INT8 for most CNNs and many transformers; degrades on models sensitive to activation outliers | Best available — the model learns weights that are robust to the rounding it will see at inference |
| When it's the right call | Default first attempt; always try this before reaching for QAT | PTQ's accuracy loss is unacceptable, or the target precision is aggressive (INT4, very low-bit) |

PTQ is the default because it is cheap: point a calibration pass at the trained model, compute scales, and evaluate. QAT is reached for only when PTQ's accuracy loss doesn't clear the bar, because it costs a full or partial retraining loop and requires access to labeled data that PTQ doesn't need.

## Calibration

PTQ needs to observe representative activation ranges before it can pick scales, and that observation is calibration: running a few hundred representative input samples through the model in floating point and recording the activation distribution at each tensor that will be quantized. A few hundred samples is usually enough to characterize a distribution's shape without needing anything close to the full dataset. What differs across calibration runs is the **range estimator** used to turn the observed distribution into a scale:

- **Min/max** — use the observed minimum and maximum directly. Simple and unbiased, but a single outlier activation blows up the range and coarsens every other value's quantization step.
- **Percentile** — clip to, say, the 99.99th percentile instead of the true max. Matters most on models with rare but extreme activation outliers, where min/max would otherwise sacrifice precision for the entire tensor to accommodate one spike.
- **Entropy / KL divergence** — choose the clipping range that minimizes the information lost between the real and quantized distributions, rather than a fixed percentile. Matters most when the "right" clipping point isn't a clean percentile and needs to be found per tensor.

## FP8 and INT4

FP8 and INT4 sit below INT8 on the precision ladder and need their own conventions. FP8 comes in two encodings, distinguished by how the 8 bits split between exponent and mantissa: **E4M3** (4 exponent bits, 3 mantissa bits) is the convention for weights and activations, trading some dynamic range for the precision that forward-pass values need; **E5M2** (5 exponent bits, 2 mantissa bits) is the convention for gradients, which need the wider dynamic range more than they need mantissa precision. As [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md) covers, FP8 tensor-core support arrived with Ada Lovelace and Hopper (4th-generation tensor cores); INT4 support is older, arriving with Turing's 2nd-generation tensor cores. INT4's usable range is narrow enough that a single scale per tensor is rarely workable — INT4 schemes are almost always **group-wise**, applying a separate scale to each small group of, say, 32 or 64 weights along a channel, trading a little extra metadata for enough precision to keep INT4 usable at all.

## Accuracy budgets

Every precision decision on this page is really a trade against an accuracy budget: how much task accuracy loss is tolerable for how much speed and memory gained. INT8 with per-channel weight quantization and good calibration typically costs a fraction of a percentage point on well-behaved CNNs; INT4 and aggressive PTQ can cost several points on models sensitive to outliers, particularly some transformer architectures, and may need QAT or per-group scaling to recover. There is no fixed number to target — it depends on the model, the task, and what accuracy loss the deployment can absorb — which is exactly why held-out validation, not calibration-set validation, is the only way to know where a given configuration actually lands.

:::warning[Validate on held-out data, not the calibration set]
A quantized model that looks fine on the samples used for calibration and then fails in production is the standard failure mode of quantization work. Calibration data tells the calibrator what ranges to expect; it says nothing about generalization. Always measure quantized accuracy on a held-out evaluation set that played no role in calibration before deciding a quantization configuration is acceptable.
:::

It is worth being precise about a vocabulary collision: [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) covers mixed-precision *training* — running fp16/bf16 forward and backward passes with an fp32 master copy of the weights, using loss scaling to avoid underflow. That is a different problem from the post-training *quantization* this page describes, even though both use words like "scale" and both reduce numeric precision. Mixed-precision training keeps the model trainable in reduced precision while an fp32 master copy absorbs the small updates; quantization for accelerators freezes a trained model's weights and activations into low-bit integers (or FP8) for inference and never trains against them unless QAT is specifically in use. Knowing both vocabularies helps, but conflating the two techniques leads to wrong assumptions about what each one costs and buys.

## See also

- [TensorRT](./tensorrt.md) — the tool that turns a quantized ONNX graph into a deployable engine, including INT8 calibration and Q/DQ node handling.
- [Deploying to Accelerators](./deploying-to-accelerators.md) — where quantization fits in the broader deployment workflow.
- [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) — the training-time counterpart to this page; different problem, overlapping vocabulary.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
