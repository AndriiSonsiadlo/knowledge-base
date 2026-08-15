---
id: transformer-architecture
title: Transformer Architecture
sidebar_label: Transformer Architecture
sidebar_position: 8
tags: [nlp, transformer, architecture]
---

# Transformer Architecture

The 2017 paper that introduced the transformer had a blunt thesis: attention was the useful part of the encoder-decoder architecture, so delete everything else. No recurrence, no convolution — just attention and simple feedforward layers, stacked. Removing the sequential dependency of recurrence is what turned scale from a research curiosity into an engineering problem that money and hardware could actually solve.

:::info[Key idea]
Removing recurrence makes every position computable in parallel, which is what turned scale from a research problem into an engineering one.
:::

<Figure
  src="/img/ml/nlp/transformer-block.png"
  alt="Post-LN and pre-LN transformer blocks side by side, showing LayerNorm after the residual add versus before the sublayer"
  caption="The 2017 paper put LayerNorm after the residual add; every modern model puts it before. Pre-LN leaves a clean identity path from input to output, which is why it trains without the warmup schedule Post-LN requires."
/>

## The motivation: recurrence blocks parallelism

[Recurrent Neural Networks](./recurrent-neural-networks.md)'s hidden state $h_t$ requires $h_{t-1}$ to already exist — an inherently sequential dependency chain that no amount of extra hardware can shortcut. Self-attention (from [Attention Mechanism](./attention-mechanism.md)) computes every position's output from the *whole* sequence simultaneously, with no such dependency — every position's attention computation can run in parallel on modern hardware.

## The encoder block

Each encoder layer: multi-head self-attention (see [Self-Attention in Depth](./self-attention-in-depth.md)), a residual connection ([Skip Connections and Depth](../02-deep-learning/skip-connections-and-depth.md)) plus layer normalisation ([Normalization Layers](../02-deep-learning/normalization-layers.md)), then a position-wise feed-forward network, another residual connection plus normalisation.

## The decoder block

Each decoder layer adds a third component beyond the encoder's two: **masked self-attention** (attending only to earlier positions in the output, enforcing the autoregressive constraint), **cross-attention** (queries from the decoder, keys/values from the encoder's output — the direct architectural descendant of [Attention Mechanism](./attention-mechanism.md)'s original mechanism), and a feed-forward network — each wrapped in its own residual-plus-normalisation.

## The causal mask, and why it's required

At training time, the decoder sees the *entire* target sequence at once (for parallelism) — but at position $t$, it must only be allowed to attend to positions $\le t$, or it could trivially "cheat" by looking at the very token it's supposed to be predicting. The causal mask sets attention scores for all future positions to $-\infty$ before the softmax, so their attention weight becomes exactly zero.

## The position-wise feed-forward network

$$
\text{FFN}(x) = W_2 \, g(W_1 x + b_1) + b_2
$$

Applied identically and independently to each position — no interaction between positions happens in this sub-layer (that's entirely attention's job). Typically expands to a much larger intermediate dimension (e.g. $4\times$ the model dimension) before projecting back down, and holds the majority of a transformer's total parameters.

## Pre-norm vs. post-norm

As covered in [Normalization Layers](../02-deep-learning/normalization-layers.md), modern transformers overwhelmingly use pre-norm (normalise before each sub-layer, with an unmodified residual stream carrying through) rather than the original paper's post-norm — pre-norm trains substantially more reliably at depth, without requiring the careful warmup schedule post-norm needs to avoid early divergence.

## The full data path for one token

Token id → embedding lookup → add positional encoding ([Positional Encodings](./positional-encodings.md)) → through $N$ encoder (or decoder) layers, each applying self-attention then feed-forward, both wrapped in residual+norm → final layer normalisation → (for a language model) a linear projection to vocabulary size, followed by softmax to produce next-token probabilities.

## Parameter count accounting

For a model dimension $d$, feed-forward dimension $4d$, and $h$ attention heads: attention's $Q, K, V, O$ projections contribute roughly $4d^2$ parameters per layer; the feed-forward network contributes roughly $2 \times d \times 4d = 8d^2$ parameters per layer — the feed-forward block alone typically accounts for close to two-thirds of a transformer layer's parameters.

| Symbol | Meaning |
|---|---|
| $d$ (or $d_{\text{model}}$) | the model's hidden/embedding dimension |
| $N$ | number of encoder or decoder layers |
| $h$ | number of attention heads |
| $n$ | sequence length |

## The O(n²) cost in sequence length

Self-attention computes a score between every pair of positions — $n^2$ scores for a sequence of length $n$, and correspondingly $O(n^2 d)$ compute and $O(n^2)$ memory for the attention matrix itself. This quadratic scaling is the direct reason context-window length is expensive to extend, and motivates the efficient-attention variants covered in [Self-Attention in Depth](./self-attention-in-depth.md).

## What the transformer removed that we sometimes miss

Recurrence gave RNNs a built-in **inductive bias** toward sequential/local structure, learned "for free" without needing data to teach it — transformers have no such built-in bias and must learn positional/sequential structure entirely from data and the positional encoding scheme, which is part of why transformers typically need more training data to reach comparable performance on small-data tasks. Recurrence also naturally supports true streaming (processing one token at a time with $O(1)$ state) in a way a full-context-attending transformer does not, without extra machinery like the KV caching covered in [Self-Attention in Depth](./self-attention-in-depth.md).

## Code: an encoder block from scratch, verified against nn.TransformerEncoderLayer

```python title="transformer_block_demo.py"
import torch
import torch.nn as nn

class TransformerEncoderBlockFromScratch(nn.Module):
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(nn.Linear(d_model, d_ff), nn.GELU(), nn.Linear(d_ff, d_model))
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        # pre-norm: normalise before the sub-layer, residual stream stays unmodified
        attn_out, _ = self.attn(self.norm1(x), self.norm1(x), self.norm1(x))
        x = x + attn_out
        x = x + self.ffn(self.norm2(x))
        return x

torch.manual_seed(0)
d_model, n_heads, d_ff, seq_len, batch = 64, 8, 256, 10, 4
x = torch.randn(batch, seq_len, d_model)

block = TransformerEncoderBlockFromScratch(d_model, n_heads, d_ff)
output = block(x)
print("from-scratch block output shape:", output.shape)

# --- Compare parameter count against the built-in layer ---
builtin = nn.TransformerEncoderLayer(d_model, n_heads, d_ff, batch_first=True, norm_first=True)
n_params_scratch = sum(p.numel() for p in block.parameters())
n_params_builtin = sum(p.numel() for p in builtin.parameters())
print(f"from-scratch params: {n_params_scratch}, built-in params: {n_params_builtin}")

# --- Parameter breakdown per sub-layer ---
attn_params = sum(p.numel() for p in block.attn.parameters())
ffn_params = sum(p.numel() for p in block.ffn.parameters())
print(f"attention params: {attn_params}, feed-forward params: {ffn_params}"
      f" (ratio: {ffn_params/attn_params:.2f}x)")
```

## See also

- [Attention Mechanism](./attention-mechanism.md) — the operation this entire architecture is built from.
- [Self-Attention in Depth](./self-attention-in-depth.md) — multi-head attention, masking, and the O(n²) cost examined closely.
- [Positional Encodings](./positional-encodings.md) — how position is injected, since attention itself carries no notion of order.
