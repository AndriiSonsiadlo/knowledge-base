---
id: attention-mechanism
title: Attention Mechanism
sidebar_label: Attention Mechanism
sidebar_position: 7
tags: [nlp, attention, architecture]
---

# Attention Mechanism

Instead of compressing the entire input into one fixed vector and hoping nothing important got lost, attention lets the decoder look back at every encoder position directly, every time it generates a token, and decide for itself which parts of the input actually matter right now. It's a differentiable lookup — a weighted average, where the weights are learned rather than fixed.

:::info[Key idea]
Attention is a differentiable lookup — a weighted average of values, where the weights come from how well a query matches each key.
:::

## The bottleneck problem, restated

[Seq2Seq and Encoder-Decoder](./seq2seq-and-encoder-decoder.md)'s decoder only ever sees the encoder's *final* hidden state — every intermediate hidden state, computed at real cost during encoding, is simply discarded.

## The fix: keep every encoder state

Instead of discarding intermediate states, keep all of them: $h_1, \ldots, h_T$ for a $T$-length input. The decoder can then, at each generation step, compute a fresh, targeted summary of these states rather than relying on one fixed summary computed once.

## Alignment scores and softmax weights

At each decoder step, compute a scalar **alignment score** between the decoder's current state and *each* encoder state, then normalise these scores with softmax into a probability distribution — the **attention weights**.

## The context vector as a weighted sum

$$
c_t = \sum_{i=1}^T \alpha_{t,i} h_i, \qquad \alpha_{t,i} = \frac{\exp(\text{score}(s_t, h_i))}{\sum_j \exp(\text{score}(s_t, h_j))}
$$

A *new* context vector is computed at every decoder step $t$, as a weighted combination of *all* encoder states — replacing [Seq2Seq and Encoder-Decoder](./seq2seq-and-encoder-decoder.md)'s single, fixed, information-lossy context vector with one recomputed fresh each step, drawing whatever information is currently relevant.

## Additive (Bahdanau) vs. multiplicative (Luong) attention

**Additive attention** computes the score with a small feedforward network: $\text{score}(s, h) = v^\top \tanh(W_1 s + W_2 h)$. **Multiplicative attention** uses a simpler dot product (optionally through a learned matrix): $\text{score}(s, h) = s^\top W h$ — computationally cheaper, and the form that generalises directly into the scaled dot-product attention below.

## The query/key/value framing

Reframe the components in more general terms: the decoder's current state is a **query** (what am I looking for), each encoder state serves as both a **key** (what does this position offer, for matching against the query) and a **value** (the actual content retrieved if this position is attended to). This framing generalises attention beyond the encoder-decoder setting entirely — it's what [Self-Attention in Depth](./self-attention-in-depth.md) and every transformer layer are built from.

## Scaled dot-product attention

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

| Symbol | Meaning |
|---|---|
| $Q, K, V$ | query, key, and value matrices |
| $d_k$ | dimensionality of the key vectors |
| $\alpha_{t,i}$ | attention weight from decoder step $t$ to encoder position $i$ |

## Why the √d_k divisor exists

As $d_k$ grows, the dot product $q \cdot k$ (a sum of $d_k$ roughly-independent terms) grows in variance proportionally to $d_k$ — large-magnitude scores push softmax into a near-one-hot, saturated regime with vanishingly small gradients almost everywhere except the single largest score. Dividing by $\sqrt{d_k}$ rescales the scores back to unit-ish variance regardless of dimensionality, keeping softmax in a well-behaved, gradient-friendly regime.

## Attention as soft dictionary lookup

A regular Python dictionary lookup is a *hard* match — the exact key or nothing. Attention is the differentiable, soft generalisation: instead of one exact key matching, every key contributes to the result in proportion to how well it matches the query, and this entire process is differentiable end to end, allowing gradient-based training of what to attend to.

## Self-attention, introduced

If the queries, keys, *and* values all come from the *same* sequence (rather than queries from a decoder and keys/values from an encoder), the mechanism is called **self-attention** — every position in a sequence can attend to every other position in that same sequence, which is the operation [Transformer Architecture](./transformer-architecture.md) builds its entire encoder and decoder stacks from.

## What attention weights do and do not tell you

Attention weights are often shown as evidence of "what the model is looking at," and they do provide a genuine, inspectable signal — but treating them as a complete, reliable explanation of the model's reasoning is contested: several studies have found that attention weights can be manipulated (or simply differ) while the model's final output stays essentially unchanged, suggesting attention alone doesn't fully determine — or fully explain — the computation.

## Code: scaled dot-product attention from scratch, and the scaling effect

```python title="attention_demo.py"
import numpy as np

def softmax(z, axis=-1):
    exp = np.exp(z - z.max(axis=axis, keepdims=True))
    return exp / exp.sum(axis=axis, keepdims=True)

def scaled_dot_product_attention(Q, K, V):
    d_k = K.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)
    weights = softmax(scores)
    return weights @ V, weights

rng = np.random.default_rng(0)
seq_len, d_k, d_v = 5, 8, 6
Q = rng.normal(size=(seq_len, d_k))
K = rng.normal(size=(seq_len, d_k))
V = rng.normal(size=(seq_len, d_v))

output, weights = scaled_dot_product_attention(Q, K, V)
print("attention weight matrix (rows sum to 1):")
print(np.round(weights, 3))
print("row sums:", weights.sum(axis=1))

# --- Demonstrating why the sqrt(d_k) scaling matters ---
def unscaled_attention(Q, K, V):
    scores = Q @ K.T  # no division by sqrt(d_k)
    weights = softmax(scores)
    return weights @ V, weights

print("\nas d_k grows, unscaled softmax saturates toward one-hot:")
for d_k_test in [4, 64, 512]:
    Q_test = rng.normal(size=(1, d_k_test))
    K_test = rng.normal(size=(5, d_k_test))
    V_test = rng.normal(size=(5, 3))
    _, w_unscaled = unscaled_attention(Q_test, K_test, V_test)
    _, w_scaled = scaled_dot_product_attention(Q_test, K_test, V_test)
    print(f"d_k={d_k_test:4d}: unscaled max weight={w_unscaled.max():.4f}, scaled max weight={w_scaled.max():.4f}")
```

The unscaled max attention weight should climb toward 1.0 (near one-hot, saturated) as $d_k$ grows, while the scaled version stays comparatively moderate — the $\sqrt{d_k}$ divisor's effect, shown numerically.

## See also

- [Seq2Seq and Encoder-Decoder](./seq2seq-and-encoder-decoder.md) — the fixed-context-vector bottleneck this mechanism was invented to fix.
- [Transformer Architecture](./transformer-architecture.md) — the architecture built entirely from this operation, with recurrence removed.
