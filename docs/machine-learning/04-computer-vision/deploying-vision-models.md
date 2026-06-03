---
id: deploying-vision-models
title: Deploying Vision Models
sidebar_label: Deploying Vision Models
sidebar_position: 13
tags: [computer-vision, deployment, inference, optimization]
---

# Deploying Vision Models

The model scores 95% accuracy in the notebook — and returns nonsense in production. This is one of the most common, most preventable failure modes in applied vision, and it's almost never the model's fault: it's a mismatch between how the training pipeline preprocessed images and how the serving pipeline does.

:::info[Key idea]
Training/serving preprocessing parity is the most common vision production bug, and it fails silently.
:::

## The five classic production failures

All five were introduced individually in [Images as Tensors](./images-as-tensors.md); production is where they actually bite. **Preprocessing mismatch**: different resize/crop logic between training and serving. **Colour-order swap**: an OpenCV-loaded (BGR) image served to a model trained on RGB, or vice versa. **Normalisation drift**: different mean/std constants used at training vs. serving time. **Resize-mode difference**: a different interpolation method, or aspect-ratio handling, between the two pipelines. **EXIF rotation**: one pipeline respects EXIF orientation metadata, the other doesn't. Every one of these produces plausible-looking, non-crashing, silently wrong predictions.

## Pinning the exact preprocessing alongside the weights

The fix: package the exact preprocessing configuration (resize size, interpolation mode, normalisation constants, colour order) *together with* the model weights, as a single versioned artefact — see [Model Registry and Packaging](../07-production-mlops/model-registry-and-packaging.md) — so the serving code loads and applies the identical transform the training code used, by construction, rather than by separately-maintained (and inevitably drifting) implementations.

## Export formats

**TorchScript**: PyTorch's own format for serialising a model (including its computation graph) for deployment outside a full Python environment. **ONNX** (Open Neural Network Exchange): a framework-agnostic format, letting a model trained in one framework run in a different inference runtime — broadens deployment options, particularly for non-Python serving environments.

## Quantisation for vision, with the accuracy cost measured

From [GPU Training and Mixed Precision](../02-deep-learning/gpu-training-and-mixed-precision.md)'s precision discussion, applied specifically to inference: **dynamic quantisation** converts weights to lower precision at load time, activations computed in the original precision at runtime. **Static quantisation** quantises both weights and activations ahead of time, using a calibration dataset to determine appropriate quantisation ranges — faster than dynamic, but requires that calibration step. **Quantisation-aware training** simulates quantisation *during* training itself, letting the model adapt to the precision loss — generally the smallest accuracy cost of the three, at the highest implementation effort.

## Pruning and distillation, briefly

**Pruning**: remove weights (or whole channels/filters) below some importance threshold, producing a smaller, sparser model — structured pruning (removing whole channels) translates to real speedups on standard hardware more reliably than unstructured pruning (removing individual weights), which often needs specialised sparse-computation support to realise its theoretical savings. **Distillation**: train a smaller "student" model to mimic a larger "teacher" model's outputs — the general technique covered fully in [Inference Optimization](../07-production-mlops/inference-optimization.md).

## Batching and dynamic shapes

Serving multiple requests together as a batch improves GPU utilisation (the same [GPU Training and Mixed Precision](../02-deep-learning/gpu-training-and-mixed-precision.md) throughput argument, applied at inference) but requires either padding variable-sized inputs to a common shape or a serving framework that explicitly supports dynamic batch shapes.

## Latency budgeting

$$
T_{\text{total}} = T_{\text{preprocess}} + T_{\text{inference}} + T_{\text{postprocess}}
$$

Measuring each stage *separately* (rather than only the end-to-end time) reveals where optimisation effort actually pays off — preprocessing (image decode, resize) is frequently a larger fraction of total latency than the model's own forward pass, and optimising the model alone leaves that cost untouched.

| Symbol | Meaning |
|---|---|
| $T_{\text{preprocess}}, T_{\text{inference}}, T_{\text{postprocess}}$ | time spent in each serving stage |

## Edge deployment constraints

On-device inference (mobile, embedded, IoT) faces hard constraints absent from server deployment: limited memory (ruling out large models entirely), limited or absent GPU acceleration, power/battery budget, and often no network connectivity to fall back on a server call — [CNN Architectures](./cnn-architectures.md)'s MobileNet/EfficientNet families exist specifically to fit within these constraints.

## Monitoring a deployed vision model

Beyond generic service metrics ([Monitoring and Observability](../07-production-mlops/monitoring-and-observability.md)): track the *distribution* of input images over time (average brightness, resolution, aspect ratio) to catch upstream data pipeline changes, and track prediction confidence distribution to catch a model quietly becoming less certain — a leading indicator of drift, often visible before accuracy itself can be measured (since ground truth for live traffic frequently arrives late or not at all).

## Pre-deployment checklist

1. Verify preprocessing produces byte-identical output between training and serving code paths, on the same input.
2. Confirm colour order (RGB vs. BGR) explicitly, not by assumption.
3. Measure latency per stage (preprocess/inference/postprocess), not just end-to-end.
4. Verify quantised (or otherwise optimised) model accuracy against the full-precision baseline on a held-out set.
5. Confirm EXIF orientation handling matches between training data preparation and the live serving path.

## Code: export, quantise, and a preprocessing-parity test that catches a mismatch

```python title="deploying_vision_models_demo.py"
import time
import torch
from torchvision import models
import numpy as np

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.eval()
dummy_input = torch.randn(1, 3, 224, 224)

# --- Export to TorchScript and ONNX, verify identical outputs ---
traced = torch.jit.trace(model, dummy_input)
torch.onnx.export(model, dummy_input, "resnet18.onnx", input_names=["input"], output_names=["output"])

with torch.no_grad():
    original_output = model(dummy_input)
    traced_output = traced(dummy_input)
print("original vs traced max difference:", (original_output - traced_output).abs().max().item())

# --- Dynamic quantisation: accuracy and latency before/after ---
quantized_model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)

def measure(m, n_runs=20):
    with torch.no_grad():
        start = time.perf_counter()
        for _ in range(n_runs):
            m(dummy_input)
        return (time.perf_counter() - start) / n_runs

orig_time, quant_time = measure(model), measure(quantized_model)
with torch.no_grad():
    orig_out, quant_out = model(dummy_input), quantized_model(dummy_input)
print(f"\noriginal:  {orig_time*1000:.2f}ms/call")
print(f"quantized: {quant_time*1000:.2f}ms/call")
print("output difference (accuracy cost):", (orig_out - quant_out).abs().max().item())

# --- Preprocessing-parity test, catching a deliberate resize-mode mismatch ---
def training_preprocess(img_array):
    import torch.nn.functional as F
    t = torch.tensor(img_array).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    return F.interpolate(t, size=(224, 224), mode="bilinear", align_corners=False)

def serving_preprocess_BUGGY(img_array):
    import torch.nn.functional as F
    t = torch.tensor(img_array).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    return F.interpolate(t, size=(224, 224), mode="nearest")  # wrong interpolation mode

rng = np.random.default_rng(0)
img_array = rng.integers(0, 256, size=(300, 300, 3), dtype=np.uint8)
train_tensor = training_preprocess(img_array)
serve_tensor = serving_preprocess_BUGGY(img_array)
parity_diff = (train_tensor - serve_tensor).abs().max().item()
print(f"\npreprocessing parity check: max difference = {parity_diff:.4f}")
assert parity_diff < 1e-6, "PREPROCESSING MISMATCH DETECTED - training and serving disagree"
```

The final assertion is deliberately written to fail here, catching the injected resize-mode bug exactly the way a real pre-deployment parity test should.

## See also

- [Transfer Learning for Vision](./transfer-learning-for-vision.md) — where the model being deployed typically comes from.
- [Images as Tensors](./images-as-tensors.md) — the preprocessing conventions this page's parity check enforces.
