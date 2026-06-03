---
id: self-supervised-vision
title: Self-Supervised Vision
sidebar_label: Self-Supervised Vision
sidebar_position: 10
tags: [computer-vision, self-supervised, contrastive]
---

# Self-Supervised Vision

Labelled image data is expensive; unlabelled photos are nearly free. Self-supervised vision learns useful visual features from the unlabelled kind alone, by manufacturing a training signal directly from the image itself — the vision-side counterpart to [Pretraining Objectives](../03-sequence-and-nlp/pretraining-objectives.md)'s masked and causal language modelling.

:::info[Key idea]
Build a pretext task where the supervision comes from the image itself - two views of the same photo should embed to the same place.
:::

## Why labels are the bottleneck

ImageNet-scale labelled datasets required enormous human annotation effort; most real-world image data (web photos, video frames, sensor feeds) has no labels at all and never will, at any practical scale — self-supervised methods exist specifically to extract value from this much larger unlabelled pool.

## Early pretext tasks, and why they underperformed

**Rotation prediction**: rotate an image by a random multiple of 90° and predict the rotation applied. **Jigsaw**: shuffle image patches and predict the correct arrangement. **Colourisation**: predict colour from a greyscale input. All manufacture a supervised-looking task from unlabelled images — but empirically, features learned this way transferred noticeably worse to downstream tasks than the contrastive methods that followed, likely because these specific pretext tasks don't force the model to learn features that are actually invariant to the visual changes that matter for recognition.

## Contrastive learning: positives from augmentation, negatives from the batch

Take one image, apply two different random augmentations ([Data Augmentation](./data-augmentation.md)) to produce two "views" of the same underlying content — these two views form a **positive pair** (should embed close together). Every other image in the training batch (and its own augmented views) forms **negative pairs** (should embed far apart) — the model learns to be invariant to augmentation while remaining discriminative between genuinely different images.

## SimCLR: the recipe, and the outsized role of augmentation

SimCLR popularised this recipe directly, and a striking empirical finding accompanied it: the specific *combination* of augmentations used (crop + colour jitter proved particularly important) mattered enormously to the quality of the resulting features — augmentation choice here isn't a minor implementation detail, it's close to the central design decision.

## The InfoNCE loss

$$
L = -\log \frac{\exp(\text{sim}(z_i, z_j) / \tau)}{\sum_{k=1}^{2N} \mathbb{1}_{[k \ne i]} \exp(\text{sim}(z_i, z_k) / \tau)}
$$

Pulls the positive pair $(z_i, z_j)$'s similarity up while pushing down similarity against every negative in the batch, with temperature $\tau$ controlling how sharply the model distinguishes close from distant negatives.

| Symbol | Meaning |
|---|---|
| $z_i, z_j$ | embeddings of two augmented views of the same image (a positive pair) |
| $\tau$ | temperature, controlling the sharpness of the similarity distribution |
| $N$ | batch size (so $2N$ total views per batch, two per image) |

## The large-batch problem

InfoNCE's negatives come from the *current batch* — a small batch provides few negative examples, weakening the contrastive signal. Effective SimCLR-style training historically required very large batch sizes (thousands of images) to provide enough negatives, a substantial computational and memory cost.

## MoCo and the momentum queue

Addresses the large-batch requirement differently: maintain a large queue of *past* embeddings (computed by a slowly-updating "momentum" copy of the encoder) as a persistent, large pool of negatives — decouples negative-pool size from batch size, achieving strong contrastive learning without requiring an enormous batch.

## BYOL and DINO: no negatives at all

A striking later development: BYOL and DINO train successfully with **no negative pairs whatsoever** — only positive pairs, pushed together, with no explicit pressure pushing anything apart. The obvious risk is **representation collapse** (every input mapping to the identical, trivial output, which would trivially satisfy "positives are close together"); these methods avoid collapse through specific architectural asymmetries (a momentum-updated target network, stop-gradient on one branch) rather than through negative examples.

## Masked autoencoders, the vision analogue of masked language modelling

Rather than contrasting augmented views, **MAE** masks out a large fraction of an image's patches (often 75% or more) and trains the model to reconstruct the missing pixels from the remaining visible patches — directly parallel to [Pretraining Objectives](../03-sequence-and-nlp/pretraining-objectives.md)'s masked language modelling, applied to [Vision Transformers](./vision-transformers.md)'s patch sequence instead of a token sequence.

## Evaluating a self-supervised backbone

**Linear probe**: freeze the pretrained backbone entirely, train only a linear classifier on top, and measure accuracy — a direct measure of how linearly-separable the learned features already are, without any further backbone adaptation. **k-NN evaluation**: classify test images by [k-Nearest Neighbors](../01-classical-ml/k-nearest-neighbors.md) directly in the frozen embedding space, with no trained classifier at all — an even more direct test of embedding quality.

## When to reach for this over ImageNet weights

When labelled data for the target domain is scarce but *unlabelled* in-domain data is abundant (satellite imagery, medical scans, a specific product catalogue) — self-supervised pretraining on that in-domain unlabelled data can produce a stronger starting point than a generic ImageNet-supervised backbone, exactly the domain-gap scenario flagged in [Transfer Learning for Vision](./transfer-learning-for-vision.md).

## Code: NT-Xent from scratch, a minimal SimCLR step, linear-probe comparison

```python title="self_supervised_vision_demo.py"
import torch
import torch.nn as nn
import torch.nn.functional as F

def nt_xent_loss(z1, z2, temperature=0.5):
    z = torch.cat([z1, z2], dim=0)
    z = F.normalize(z, dim=1)
    sim = z @ z.T / temperature
    n = z1.shape[0]
    labels = torch.cat([torch.arange(n, 2*n), torch.arange(0, n)])  # each sample's positive partner
    mask = torch.eye(2*n, dtype=torch.bool)
    sim.masked_fill_(mask, float("-inf"))  # exclude self-similarity
    return F.cross_entropy(sim, labels)

torch.manual_seed(0)
z1 = F.normalize(torch.randn(8, 16), dim=1)
z2 = z1 + torch.randn(8, 16) * 0.1  # near-identical positives, sanity check
loss = nt_xent_loss(z1, z2)
print(f"NT-Xent loss on near-identical positive pairs: {loss.item():.4f} (should be low)")

random_z2 = F.normalize(torch.randn(8, 16), dim=1)
random_loss = nt_xent_loss(z1, random_z2)
print(f"NT-Xent loss with random (non-matching) pairs: {random_loss.item():.4f} (should be higher)")

# --- Minimal SimCLR-style training step ---
encoder = nn.Sequential(nn.Flatten(), nn.Linear(3*32*32, 64), nn.ReLU(), nn.Linear(64, 32))
optimizer = torch.optim.Adam(encoder.parameters(), lr=0.001)

images = torch.randn(16, 3, 32, 32)
view1 = images + torch.randn_like(images) * 0.1
view2 = images + torch.randn_like(images) * 0.1

for step in range(50):
    optimizer.zero_grad()
    z1, z2 = encoder(view1), encoder(view2)
    loss = nt_xent_loss(z1, z2)
    loss.backward(); optimizer.step()
print(f"\nfinal contrastive training loss: {loss.item():.4f}")

# --- Linear probe: frozen features vs random-init features ---
labels = torch.randint(0, 5, (16,))
probe = nn.Linear(32, 5)
probe_optimizer = torch.optim.Adam(probe.parameters(), lr=0.01)
with torch.no_grad():
    features = encoder(images)
for _ in range(100):
    probe_optimizer.zero_grad()
    loss = F.cross_entropy(probe(features), labels)
    loss.backward(); probe_optimizer.step()
print(f"linear probe final loss on trained features: {loss.item():.4f}")
```

## See also

- [Data Augmentation](./data-augmentation.md) — the augmentation choices that directly determine contrastive learning quality.
- [Pretraining Objectives](../03-sequence-and-nlp/pretraining-objectives.md) — the NLP-side masked and contrastive objectives this page's methods parallel.
