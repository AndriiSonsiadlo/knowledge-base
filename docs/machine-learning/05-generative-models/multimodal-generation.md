---
id: multimodal-generation
title: Multimodal Generation
sidebar_label: Multimodal Generation
sidebar_position: 10
tags: [generative, multimodal, text-to-image]
---

# Multimodal Generation

How does a sentence become an image? Not through one monolithic model — a text-to-image system is three separately-motivated trained components, wired together, and most of what a system can and can't do is a direct consequence of how they're joined.

:::info[Key idea]
Text-to-image systems are three trained components wired together - a text encoder, a conditional generator, and a decoder - and most behaviour comes from how they are joined.
:::

## The full text-to-image stack, component by component

**Text encoder**: turns the prompt into a sequence of embeddings. **Conditional generator**: a diffusion (or flow-matching) model, conditioned on those embeddings via cross-attention, that produces a latent representation. **Decoder**: turns that latent back into pixels — typically a [Variational Autoencoders](./variational-autoencoders.md)-style decoder, as in [DDPM Sampling and Guidance](./ddpm-sampling-and-guidance.md)'s latent-diffusion setup. Every stage is trained (or at least fine-tuned) somewhat independently, and the seams between them are where most system-level behaviour lives.

## The text encoder, and why the choice of encoder bounds prompt understanding

A weak or narrowly-trained text encoder caps what the whole system can ever understand about a prompt, regardless of how good the generator is downstream — the encoder's own training data and objective (e.g. CLIP-style contrastive image-text alignment, versus a general-purpose language model) directly determine what kinds of language the system can meaningfully condition on: compositional structure, counting, negation, and spatial relations are all bounded first by what the text encoder itself represents.

## Cross-attention as the conditioning mechanism

Exactly [DDPM Sampling and Guidance](./ddpm-sampling-and-guidance.md)'s cross-attention: image features act as queries, text token embeddings act as keys and values, letting each spatial region of the generated image attend to whichever words are most relevant to it — the mechanism that lets a prompt influence *where* things appear, not just *that* they appear.

## The latent space and its decoder

Running generation in a compressed latent space (rather than raw pixels) is a computational choice, not a semantic one — the decoder's job is purely to map that latent back to pixels faithfully; it carries no responsibility for interpreting the prompt, which happens entirely upstream in the conditional generator.

## What the guidance scale does to the output, revisited concretely

Recall from [DDPM Sampling and Guidance](./ddpm-sampling-and-guidance.md): the classifier-free guidance scale $w$ trades prompt fidelity against diversity. Concretely, in text-to-image systems this shows up as: too low, and the output barely reflects the prompt; too high, and outputs become oversaturated, over-sharpened, and start looking similar to each other across different random seeds.

## Prompt sensitivity as a property of the encoder

Two prompts that a human would consider paraphrases of each other can produce noticeably different images if the text encoder embeds them differently — prompt sensitivity is fundamentally a statement about the text encoder's representation geometry, not a mysterious property of the generator.

## Negative prompts

As in [DDPM Sampling and Guidance](./ddpm-sampling-and-guidance.md): the same guidance extrapolation, applied with the unconditional term replaced by a conditional prediction on the content to be avoided, steering generation away from specific concepts using the identical mechanism used to steer toward the main prompt.

## Known failure modes: text rendering, counting, spatial relations, compositional binding

**Text rendering**: rendering legible words inside a generated image is a distinct, historically hard sub-problem — the model must reproduce exact glyph shapes, something diffusion training rarely supervises directly. **Counting**: "three apples" often does not reliably produce exactly three — the training data and objective provide no explicit counting supervision. **Spatial relations**: "the cat to the left of the dog" is frequently violated, since cross-attention provides no hard spatial-binding guarantee. **Compositional binding**: with multiple objects and attributes ("a red cube and a blue sphere"), attributes can bleed across objects ("a blue cube and a red sphere") — cross-attention has no built-in mechanism enforcing which attribute belongs to which object.

## Image-to-video and audio generation at a high level

The same core recipe (a generator trained on a diffusion or flow-matching objective, conditioned via cross-attention on another modality's embeddings) extends to video (with an added temporal dimension and consistency constraints across frames) and audio (operating over a spectrogram or waveform-latent representation instead of an image latent) — the architectural pattern generalises further than the modality-specific details might suggest.

## Autoregressive multimodal models as the alternative architecture

An entirely different route: treat image (or audio) patches as tokens in a sequence, and generate them autoregressively with a standard next-token-prediction language model ([Language Modeling Basics](../03-sequence-and-nlp/language-modeling-basics.md)'s chain rule, applied to visual tokens) — trading diffusion's iterative refinement for the same sequential generation process used for text, at the cost of the sequential (rather than parallel-per-step) generation this implies.

## The practical evaluation problem

There is no ground-truth "correct" image for a given prompt, so evaluating a text-to-image system inherits every difficulty from [Evaluating Generative Models](./evaluating-generative-models.md) plus an additional one specific to this setting: measuring *prompt alignment* itself (whether the generated image actually matches what was asked for), which automatic metrics like CLIP score only approximate.

## Code: a small class-conditional generator demonstrating the conditioning mechanism end to end

```python title="multimodal_generation_demo.py"
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

T = 200
betas = torch.linspace(1e-4, 0.02, T)
alphas = 1 - betas
alpha_bars = torch.cumprod(alphas, dim=0)
num_classes = 10  # a stand-in "vocabulary" for the conditioning signal, in place of a full text encoder

class ConditionalDenoiser(nn.Module):
    def __init__(self, time_dim=32, cond_dim=32):
        super().__init__()
        self.time_embed = nn.Embedding(T, time_dim)
        self.cond_embed = nn.Embedding(num_classes + 1, cond_dim)  # +1 for the "no condition" token
        self.net = nn.Sequential(
            nn.Flatten(), nn.Linear(784 + time_dim + cond_dim, 256), nn.ReLU(),
            nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 784),
        )

    def forward(self, x, t, cond):
        h = torch.cat([x.flatten(1), self.time_embed(t), self.cond_embed(cond)], dim=1)
        return self.net(h).view(-1, 1, 28, 28)

model = ConditionalDenoiser()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
null_cond = num_classes

# --- Toy training loop: condition = digit class, standing in for a text prompt embedding ---
x0_batch = torch.rand(64, 1, 28, 28)      # placeholder batch (swap in a real DataLoader in practice)
cond_batch = torch.randint(0, num_classes, (64,))
for step in range(200):
    drop_mask = torch.rand(64) < 0.1      # random conditioning dropout, enabling classifier-free guidance
    cond_input = torch.where(drop_mask, torch.full_like(cond_batch, null_cond), cond_batch)
    t = torch.randint(0, T, (64,))
    noise = torch.randn_like(x0_batch)
    ab = alpha_bars[t].view(-1, 1, 1, 1)
    xt = ab.sqrt() * x0_batch + (1 - ab).sqrt() * noise
    pred_noise = model(xt, t, cond_input)
    loss = nn.functional.mse_loss(pred_noise, noise)
    optimizer.zero_grad(); loss.backward(); optimizer.step()

@torch.no_grad()
def sample(model, cond_value, guidance_scale=3.0, n=4):
    x = torch.randn(n, 1, 28, 28)
    cond = torch.full((n,), cond_value, dtype=torch.long)
    null = torch.full((n,), null_cond, dtype=torch.long)
    for t in reversed(range(T)):
        t_batch = torch.full((n,), t, dtype=torch.long)
        eps = model(x, t_batch, null) + guidance_scale * (model(x, t_batch, cond) - model(x, t_batch, null))
        alpha_t, alpha_bar_t = alphas[t], alpha_bars[t]
        noise = torch.randn_like(x) if t > 0 else torch.zeros_like(x)
        x = (1 / alpha_t.sqrt()) * (x - (1 - alpha_t) / (1 - alpha_bar_t).sqrt() * eps) + betas[t].sqrt() * noise
    return x

fig, axes = plt.subplots(1, 5, figsize=(15, 3))
for cond_value in range(5):
    samples = sample(model, cond_value)
    axes[cond_value].imshow(samples[0, 0].clamp(0, 1), cmap="gray")
    axes[cond_value].set_title(f"condition = {cond_value}")
    axes[cond_value].axis("off")
plt.savefig("conditional_generation_demo.png")
```

## See also

- [DDPM Sampling and Guidance](./ddpm-sampling-and-guidance.md) — the guidance and cross-attention mechanisms this page applies to a richer conditioning signal.
- [Multimodal Vision-Language](../04-computer-vision/multimodal-vision-language.md) — the vision-language encoders that typically supply the text embeddings.
