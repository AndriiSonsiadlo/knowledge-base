---
id: multimodal-vision-language
title: Multimodal Vision-Language Models
sidebar_label: Multimodal Vision-Language
sidebar_position: 11
tags: [computer-vision, clip, multimodal, embeddings]
---

# Multimodal Vision-Language Models

An image and the sentence describing it are, on the surface, completely different kinds of data — a grid of pixels versus a sequence of tokens. CLIP's contribution was to train both an image encoder and a text encoder so that matching pairs land in the *same* embedding space, close together — and the moment that works, classification becomes a search problem, with no fixed label set required.

:::info[Key idea]
Train an image encoder and a text encoder so that matching pairs land close together, and you get open-vocabulary classification for free.
:::

## The shared-embedding-space idea

Rather than training separate systems for "understand images" and "understand text," train two encoders — one per modality — projected into a *shared* vector space, where semantic similarity between an image and a caption corresponds directly to geometric proximity between their embeddings.

## CLIP: dual encoders, contrastive training

An image encoder ([Vision Transformers](./vision-transformers.md) or a CNN) and a text encoder ([Transformer Variants](../03-sequence-and-nlp/transformer-variants.md)'s encoder family) are trained jointly on a large corpus of (image, caption) pairs scraped from the web, using a contrastive objective directly extending [Self-Supervised Vision](./self-supervised-vision.md)'s contrastive approach — but here the positive pair is an image and *its actual caption*, rather than two augmented views of the same image.

## The symmetric contrastive loss

$$
L = \frac{1}{2}\Big(L_{\text{image} \to \text{text}} + L_{\text{text} \to \text{image}}\Big)
$$

For a batch of $N$ (image, text) pairs, each image should match its own caption more than any of the other $N-1$ captions in the batch, *and* each caption should match its own image more than any other image — the loss is computed and averaged in both directions.

## Zero-shot classification via text prompts

CLIP's most striking capability: to classify an image among a set of candidate classes, embed the image once, embed each class name as a short text prompt (e.g. "a photo of a {class}"), and pick whichever class's text embedding is closest to the image embedding — no classification head was ever trained, and the class set can be entirely new at inference time, unconstrained by whatever classes appeared during CLIP's own training.

| Symbol | Meaning |
|---|---|
| $(I_i, T_i)$ | the $i$-th image-text pair in a batch |
| $\text{sim}(I_i, T_j)$ | cosine similarity between image $i$'s and text $j$'s embeddings |

## Prompt-template sensitivity

Zero-shot accuracy can vary noticeably depending on the exact wording of the text prompt used — "a photo of a {class}" versus just "{class}" versus "a picture of a {class}" can produce meaningfully different classification accuracy on the same task, an odd but well-documented sensitivity that makes prompt engineering relevant even for this non-generative use case.

## Image and text retrieval

The same shared embedding space supports search in either direction: given a text query, retrieve the most similar images (embed the query, find nearest image embeddings); given an image query, retrieve the most similar captions or documents — the foundation of modern multimodal search systems.

## What CLIP is measurably bad at

Documented, consistent weaknesses: **counting** (distinguishing "two dogs" from "three dogs" reliably), **spatial relations** ("the cat is to the left of the dog" vs. to the right), **fine-grained categories** (distinguishing closely related species or product variants that differ in subtle visual detail), and **rendered text** (reading and understanding text that appears within the image itself) — these gaps stem from the contrastive, whole-image-to-whole-caption training objective, which doesn't specifically supervise these fine-grained relational or compositional properties.

## CLIP embeddings as a component

Beyond direct zero-shot classification, CLIP's embeddings are widely reused as a fixed feature extractor within larger systems — as the vision encoder feeding into a multimodal language model, or as the similarity measure guiding [Diffusion Models](../05-generative-models/diffusion-models.md)'s text-conditioned image generation.

## Captioning and visual question answering, briefly

Generative multimodal tasks (produce a caption, answer a question about an image) require an architecture that can *generate* text conditioned on visual input, not just measure similarity — typically built by feeding CLIP-style (or similar) visual features into a language model's cross-attention or input sequence, extending [Seq2Seq and Encoder-Decoder](../03-sequence-and-nlp/seq2seq-and-encoder-decoder.md)'s conditioning pattern to a visual "source."

## Modern vision-language models, at a high level

Current systems increasingly integrate visual and textual processing more tightly than CLIP's separate-encoders-plus-contrastive-loss design — feeding visual features directly into a large language model's token stream, letting the same attention mechanism reason jointly over both modalities rather than only comparing pre-computed embeddings.

## Connecting to retrieval material

CLIP-style embeddings are one instance of the broader embedding-based retrieval pattern covered from the text side in [Word Embeddings](../03-sequence-and-nlp/word-embeddings.md) and applied throughout the LangChain reference's retrieval-augmented generation material — the same "embed, then find nearest neighbours" pattern, extended across modalities.

## Code: zero-shot classification, retrieval, prompt-template sensitivity

```python title="multimodal_demo.py"
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

rng = np.random.default_rng(0)
img_array = rng.integers(0, 256, size=(224, 224, 3), dtype=np.uint8)
image = Image.fromarray(img_array, mode="RGB")

# --- Zero-shot classification ---
candidate_labels = ["a photo of a cat", "a photo of a dog", "a photo of a car", "a photo of a tree"]
inputs = processor(text=candidate_labels, images=image, return_tensors="pt", padding=True)
with torch.no_grad():
    outputs = model(**inputs)
probs = outputs.logits_per_image.softmax(dim=1)
for label, prob in zip(candidate_labels, probs[0]):
    print(f"{label:25s}: {prob.item():.4f}")

# --- Retrieval: rank captions against the image ---
captions = ["a serene mountain landscape", "a busy city street at night", "a close-up of a flower"]
inputs = processor(text=captions, images=image, return_tensors="pt", padding=True)
with torch.no_grad():
    outputs = model(**inputs)
ranking = outputs.logits_per_image.softmax(dim=1)[0]
ranked_indices = ranking.argsort(descending=True)
print("\ncaptions ranked by similarity to the image:")
for idx in ranked_indices:
    print(f"  {captions[idx]}: {ranking[idx].item():.4f}")

# --- Prompt-template sensitivity ---
templates = ["{}", "a photo of a {}", "a picture of a {}"]
class_name = "cat"
for template in templates:
    text = template.format(class_name)
    inputs = processor(text=[text], images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        score = model(**inputs).logits_per_image.item()
    print(f"template {template!r:20s} -> score: {score:.3f}")
```

## See also

- [Vision Transformers](./vision-transformers.md) — a common choice of image encoder in models like CLIP.
- [Word Embeddings](../03-sequence-and-nlp/word-embeddings.md) — the text-side embedding concept this page extends across modalities.
