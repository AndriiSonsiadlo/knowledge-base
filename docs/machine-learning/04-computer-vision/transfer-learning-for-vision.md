---
id: transfer-learning-for-vision
title: Transfer Learning for Vision
sidebar_label: Transfer Learning for Vision
sidebar_position: 6
tags: [computer-vision, transfer-learning, finetuning]
---

# Transfer Learning for Vision

Almost nobody trains a vision model from scratch anymore, and there's a good structural reason: the early layers of any CNN trained on natural images learn something close to universal — edges, colours, simple textures — regardless of what specific objects the model was ultimately trained to recognise. That generic foundation is exactly what transfer learning reuses.

:::info[Key idea]
Early layers learn generic edges and textures that transfer across almost any image task — only the later layers are task-specific.
:::

## What pretrained features actually contain, layer by layer

Early layers: edge detectors, colour blobs, simple textures — visibly similar across almost any CNN trained on natural images, regardless of the final task. Middle layers: more complex textures, simple parts (eyes, wheels, wood grain). Late layers: increasingly abstract, task-specific combinations closely tied to the original training objective (e.g. "this pattern predicts golden retriever"). Transfer learning works because the early and middle layers' generic features are useful for a very wide range of downstream tasks, even ones the original model never saw.

## Feature extraction: freeze, train a new head

Freeze every pretrained layer's weights entirely; replace the final classification layer with a new one sized for the target task's number of classes; train *only* that new layer. Cheap, fast, and works reasonably well when the target task is visually similar to the original pretraining data.

## Fine-tuning: unfreeze progressively

Rather than keeping the entire backbone frozen, unfreeze some or all of it and continue training at a low learning rate — lets the pretrained features adapt somewhat to the target task's specifics, generally outperforming pure feature extraction when enough target-task data is available to support it without overfitting.

## Which layers to unfreeze, and in what order

A common practice: start by fine-tuning only the last few layers (closest to the task-specific end), and progressively unfreeze earlier layers if more adaptation is needed and enough data supports it — unfreezing the *earliest* layers first risks destroying the generic, broadly-useful features those layers hold before the later layers have had a chance to adapt around them.

## Learning rates: small for the backbone, larger for the head

The new task head starts from random initialisation and needs to learn quickly; the pretrained backbone already encodes useful information and should only be nudged gently — using the same learning rate for both risks either training the head too slowly or destroying the backbone's pretrained knowledge too quickly, the same discriminative-learning-rate principle from [Finetuning and Instruction Tuning](../03-sequence-and-nlp/finetuning-and-instruction-tuning.md).

## BatchNorm statistics during fine-tuning, and the classic bug

[Normalization Layers](../02-deep-learning/normalization-layers.md)'s BatchNorm behaves differently in train vs. eval mode. A classic transfer-learning bug: leaving BatchNorm layers in **train mode** while otherwise freezing the backbone means their running statistics keep updating based on the new (possibly small, possibly differently-distributed) target-task batches — this can silently corrupt the very statistics that made the pretrained features good in the first place, even though the *weights* were correctly frozen.

## How much data justifies full fine-tuning

Feature extraction alone is often sufficient (and safer against overfitting) with only a few hundred target-task examples; full fine-tuning of most or all layers generally needs at least low thousands of examples to avoid quickly overfitting the far larger number of unfrozen parameters — a rough rule of thumb, not a hard boundary, and worth verifying empirically per task.

## Domain gap: when ImageNet features do not transfer well

Pretrained-on-natural-photos features transfer well to other natural-photo tasks, but transfer considerably less well to domains with fundamentally different visual statistics — medical imaging (X-rays, MRIs), satellite imagery, or microscopy, where the textures, structures, and relevant visual cues differ substantially from anything in typical pretraining data. In these cases, domain-specific pretrained backbones (where available) or a greater reliance on full fine-tuning (rather than feature extraction) tend to perform meaningfully better.

## Self-supervised pretrained backbones as an alternative

[Self-Supervised Vision](./self-supervised-vision.md)-pretrained backbones (trained without any labels at all, on potentially domain-relevant unlabelled images) can be a stronger starting point than a supervised ImageNet backbone specifically when the target domain diverges substantially from natural photos and some in-domain unlabelled data is available.

## Decision table

| Dataset size | Domain similarity to pretraining | Reach for |
|---|---|---|
| Small (hundreds) | similar | feature extraction |
| Small (hundreds) | different | feature extraction, or domain-specific pretrained weights if available |
| Large (thousands+) | similar | fine-tuning, most or all layers |
| Large (thousands+) | different | full fine-tuning, or self-supervised pretraining on in-domain data first |

## Code: frozen vs. fine-tuned, early-layer filters visualised

```python title="transfer_learning_demo.py"
import torch
import torch.nn as nn
from torchvision import models
import matplotlib.pyplot as plt
import time

def make_model(num_classes, freeze_backbone):
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)  # new head, always trainable
    return model

torch.manual_seed(0)
X = torch.randn(64, 3, 64, 64)
y = torch.randint(0, 5, (64,))

results = {}
for label, freeze in [("frozen backbone", True), ("fine-tuned backbone", False)]:
    model = make_model(num_classes=5, freeze_backbone=freeze)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=0.001)
    start = time.perf_counter()
    for _ in range(5):
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(model(X), y)
        loss.backward(); optimizer.step()
    elapsed = time.perf_counter() - start
    print(f"{label:22s}: {trainable:,}/{total:,} trainable params, {elapsed:.3f}s for 5 steps")

# --- Visualise early-layer filters ---
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
first_conv_weights = model.conv1.weight.data  # shape (64, 3, 7, 7)
fig, axes = plt.subplots(4, 8, figsize=(12, 6))
for i, ax in enumerate(axes.flat):
    filt = first_conv_weights[i].permute(1, 2, 0)
    filt = (filt - filt.min()) / (filt.max() - filt.min())
    ax.imshow(filt); ax.axis("off")
plt.savefig("pretrained_filters.png")
```

## See also

- [CNN Architectures](./cnn-architectures.md) — the pretrained backbones this page reuses.
- [Data Augmentation](./data-augmentation.md) — commonly combined with fine-tuning to further reduce overfitting risk on small target datasets.
