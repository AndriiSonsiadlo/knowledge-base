---
id: positional-encodings
title: Positional Encodings
sidebar_label: Positional Encodings
sidebar_position: 10
tags: [nlp, transformer, positional-encoding, rope]
---

# Positional Encodings

Attention computes a weighted average over a set of positions — and a set has no order. Shuffle the words in a sentence before feeding them to a raw self-attention layer, and the output is mathematically identical, permuted the same way. Every scheme on this page exists to inject the one piece of information attention structurally cannot supply on its own: where each token sits.

:::info[Key idea]
Attention is order-blind — shuffle the input and the output is identical, so position must be injected explicitly, and how you inject it decides whether the model can extrapolate past its training length.
:::

<Figure
  src="/img/ml/nlp/positional-encoding.png"
  alt="A sinusoidal positional encoding heatmap, individual dimension waves at different frequencies, and a position-similarity matrix"
  caption="Self-attention is permutation-invariant, so position has to be injected. Each dimension is a wave of a different frequency; the similarity matrix on the right shows the payoff — the encoding of two positions depends on the distance between them."
/>

## The permutation-equivariance proof

Scaled dot-product attention (from [Attention Mechanism](./attention-mechanism.md)) computes scores and a weighted sum purely from the *set* of $Q, K, V$ vectors — permuting the input rows permutes the output rows identically, with no other change. Formally, attention is a **permutation-equivariant** function: $f(\text{permute}(x)) = \text{permute}(f(x))$. Without an explicit positional signal, "the cat sat on the mat" and "mat the sat on cat the" would produce identical (permuted) representations.

## Sinusoidal encodings

$$
PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d}}\right), \qquad PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d}}\right)
$$

A fixed (not learned) vector added to each token's embedding, encoding its position via a set of sine/cosine waves at different frequencies. The frequency ladder (from very slow-varying to very fast-varying across the embedding dimensions) means nearby positions produce similar, gradually-diverging encodings, while an elegant identity ($\sin(a+b)$ expands in terms of $\sin(a), \cos(a)$) means the encoding of any relative offset is a fixed linear function of the encodings themselves — the original justification for choosing sinusoids specifically.

## Learned absolute embeddings

Instead of a fixed formula, learn a lookup table of position embeddings directly (one vector per position index, up to some maximum), trained just like any other parameter. Simpler than the sinusoidal formula, but has a **hard length ceiling** — position 5001 has no learned embedding at all if the table was only trained up to position 5000, unlike the sinusoidal formula, which is defined for any position.

## Relative position encodings

Rather than encoding each token's *absolute* position, encode the *relative offset* between a query and key position directly inside the attention computation itself — better matches the intuition that "two words next to each other" should be treated similarly regardless of whether that pair occurs at the start or the end of a long document.

## RoPE: rotating query and key vectors

**Rotary Position Embedding** applies a position-dependent rotation to the query and key vectors before computing their dot product, rather than adding a separate positional vector to the embedding. The key property: rotating both $q$ and $k$ by their respective positions means their dot product, after rotation, depends *only on the relative distance* $(pos_q - pos_k)$ between them, not on either absolute position — proven directly by the rotation's algebraic properties, and confirmed numerically in the code below.

| Symbol | Meaning |
|---|---|
| $pos$ | absolute token position in the sequence |
| $i$ | dimension index within the encoding vector |
| $\theta$ | RoPE's rotation angle, a function of position and dimension |

## ALiBi: a linear distance penalty

Rather than modifying $Q$ or $K$ at all, **ALiBi** (Attention with Linear Biases) adds a penalty directly to the raw attention *scores*, proportional to the distance between query and key positions — closer positions get less penalty, farther positions get more, biasing attention toward locality without any explicit positional embedding.

## What each scheme can and cannot do for length extrapolation

Sinusoidal and learned-absolute encodings both struggle to generalise to sequence lengths substantially longer than seen during training — sinusoidal *can* in principle (the formula is defined at any position) but empirically often degrades; learned-absolute simply has no representation past its trained maximum. RoPE and ALiBi, by encoding *relative* rather than absolute position, tend to extrapolate to longer sequences noticeably better, though neither is a complete solution on its own.

## Context-window extension methods

**Position interpolation**: rather than extrapolating to unseen positions, rescale (compress) position indices so a longer sequence maps into the *same* range of positions the model was originally trained on — trading some resolution for staying within the trained distribution. **NTK-aware scaling**: a refinement adjusting RoPE's frequency base specifically to preserve high-frequency (fine-grained, local) information while still extending the effective range — both are post-hoc techniques applied to extend an already-trained model's usable context length without full retraining.

## Comparison table

| Scheme | Extrapolation | Extra compute | Adoption |
|---|---|---|---|
| Sinusoidal | Weak in practice | none | mostly historical (original transformer) |
| Learned absolute | None past trained max | none | BERT-family |
| RoPE | Good, especially with extension methods | modest (rotation per layer) | most modern LLMs |
| ALiBi | Good | minimal (a score bias) | some modern LLMs |

## Code: sinusoidal heatmap, RoPE's relative-distance property, a permutation test

```python title="positional_encodings_demo.py"
import numpy as np
import matplotlib.pyplot as plt

def sinusoidal_encoding(max_pos, d):
    pos = np.arange(max_pos)[:, None]
    i = np.arange(d)[None, :]
    angle_rates = 1 / (10000 ** (2 * (i // 2) / d))
    angles = pos * angle_rates
    encoding = np.zeros((max_pos, d))
    encoding[:, 0::2] = np.sin(angles[:, 0::2])
    encoding[:, 1::2] = np.cos(angles[:, 1::2])
    return encoding

pe = sinusoidal_encoding(max_pos=100, d=64)
plt.figure(figsize=(8, 4))
plt.imshow(pe.T, aspect="auto", cmap="RdBu")
plt.xlabel("position"); plt.ylabel("encoding dimension")
plt.savefig("sinusoidal_heatmap.png")

# --- RoPE: verify the dot product depends only on relative offset ---
def rope_rotate(x, pos, theta_base=10000):
    d = len(x)
    rotated = x.copy()
    for i in range(0, d, 2):
        theta = pos / (theta_base ** (i / d))
        cos, sin = np.cos(theta), np.sin(theta)
        rotated[i], rotated[i+1] = x[i]*cos - x[i+1]*sin, x[i]*sin + x[i+1]*cos
    return rotated

rng = np.random.default_rng(0)
q, k = rng.normal(size=8), rng.normal(size=8)

for offset in [3]:  # fixed relative offset, tested at different absolute positions
    for pos_q in [5, 20, 50]:
        pos_k = pos_q - offset
        q_rot = rope_rotate(q, pos_q)
        k_rot = rope_rotate(k, pos_k)
        dot = q_rot @ k_rot
        print(f"pos_q={pos_q}, pos_k={pos_k} (offset={offset}): dot product = {dot:.4f}")
print("-> dot product stays constant across different absolute positions at the same relative offset")

# --- Permutation test: attention without positional info is order-invariant ---
def softmax(z): return np.exp(z - z.max()) / np.exp(z - z.max()).sum()
def simple_attention(X):
    scores = X @ X.T
    weights = np.array([softmax(row) for row in scores])
    return weights @ X

X = rng.normal(size=(5, 8))
perm = rng.permutation(5)
out1 = simple_attention(X)
out2 = simple_attention(X[perm])
print("\nunpermuted output[0]:", out1[0].round(3))
print("permuted output at matching original index:", out2[np.argsort(perm)][0].round(3))
print("-> identical (up to floating point), confirming order-blindness without positional info")
```

## See also

- [Self-Attention in Depth](./self-attention-in-depth.md) — the operation this page's encodings are injected into.
- [Transformer Variants](./transformer-variants.md) — which positional scheme different model families adopted.
