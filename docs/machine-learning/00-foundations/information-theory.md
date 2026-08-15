---
id: information-theory
title: Information Theory
sidebar_label: Information Theory
sidebar_position: 8
tags: [foundations, math, information-theory, entropy]
---

# Information Theory

Cross-entropy is the default classification loss for a precise reason: it measures how many extra bits you waste describing reality with the wrong distribution, and minimising it means matching the truth. This page builds entropy, cross-entropy, and KL divergence from scratch so that reason stops being a slogan and becomes a derivation.

:::info[Key idea]
Cross-entropy is the average number of bits you waste by encoding reality with the wrong distribution; minimising it means matching the truth.
:::

<Figure
  src="/img/ml/foundations/information-theory.png"
  alt="Binary entropy peaking at p equals one half, surprisal rising as probability falls, and two bar distributions illustrating KL divergence"
  caption="Entropy is maximised by maximum uncertainty; surprisal makes rare events expensive to encode. KL divergence measures the extra bits spent coding the true distribution P with the model's Q — which is exactly what cross-entropy loss minimises."
/>

## Information content of an event

An event that's certain to happen tells you nothing when it occurs; an event that's rare and surprising tells you a lot. Information content formalises "surprise":

$$
I(x) = -\log_2 p(x)
$$

A probability-1 event has $I(x) = 0$ bits of information; a probability-0.5 event (a fair coin flip) carries exactly 1 bit.

## Entropy

Entropy is the *expected* information content — the average surprise, in bits, of a distribution:

$$
H(p) = -\sum_x p(x) \log_2 p(x)
$$

A fair coin ($p=0.5$) has entropy $H = 1$ bit — maximum uncertainty for a binary variable. A biased coin ($p=0.9$) has lower entropy (~0.47 bits) — you're less surprised on average because you can already guess the likely outcome.

## Cross-entropy

Cross-entropy measures the average number of bits needed to encode data from true distribution $p$ using a code optimised for a *different* distribution $q$:

$$
H(p, q) = -\sum_x p(x) \log_2 q(x)
$$

If $q = p$, cross-entropy equals entropy — the minimum possible. Any mismatch between $q$ and $p$ adds extra bits.

## KL divergence

The Kullback-Leibler divergence measures exactly that extra cost — how much worse $q$ is than the true $p$:

$$
D_{KL}(p \parallel q) = \sum_x p(x) \log_2 \frac{p(x)}{q(x)} = H(p, q) - H(p)
$$

$D_{KL}(p \parallel q) \geq 0$ always, and equals zero only when $q = p$. It is **not symmetric** — $D_{KL}(p \parallel q) \neq D_{KL}(q \parallel p)$ in general, because "the extra cost of using $q$ when the truth is $p$" is a different question from "the extra cost of using $p$ when the truth is $q$."

## The decomposition

$$
H(p, q) = H(p) + D_{KL}(p \parallel q)
$$

Cross-entropy splits into an irreducible part (the entropy of the true distribution — you can never do better than this) and a reducible part (the KL divergence — the model's error). **Training a classifier by minimising cross-entropy is equivalent to minimising KL divergence, because $H(p)$ is fixed by the data and doesn't depend on the model at all.**

| Symbol | Meaning |
|---|---|
| $H(p)$ | entropy of the true distribution |
| $H(p, q)$ | cross-entropy between true $p$ and model $q$ |
| $D_{KL}(p \parallel q)$ | KL divergence — how much worse $q$ is than $p$ |

## Mutual information

$$
I(X; Y) = D_{KL}\big(p(x,y) \parallel p(x)p(y)\big)
$$

Measures how much knowing $Y$ reduces uncertainty about $X$ (and vice versa) — zero exactly when $X, Y$ are independent.

## Perplexity

$$
\text{Perplexity} = 2^{H(p,q)}
$$

Exponentiated cross-entropy, used throughout [Language Modeling Basics](../03-sequence-and-nlp/language-modeling-basics.md). A perplexity of 20 means the model is, on average, as uncertain as if it were choosing uniformly among 20 equally likely options.

## Where each shows up

- Cross-entropy: the default classification loss ([Loss Functions](./loss-functions.md)).
- KL divergence: the regulariser in a VAE's ELBO ([Variational Autoencoders](../05-generative-models/variational-autoencoders.md)), the constraint in TRPO/PPO ([PPO and Trust Regions](../06-reinforcement-learning/ppo-and-trust-regions.md)).
- Entropy: exploration bonuses in policy gradient methods, dropout's information-theoretic framing.
- Perplexity: language model evaluation.

## Code: entropy, KL, and the asymmetry, from scratch

```python title="information_theory_demo.py"
import numpy as np

def entropy(p):
    p = np.asarray(p)
    p = p[p > 0]  # 0 * log(0) := 0
    return -np.sum(p * np.log2(p))

def cross_entropy(p, q):
    p, q = np.asarray(p), np.asarray(q)
    mask = p > 0
    return -np.sum(p[mask] * np.log2(q[mask]))

def kl_divergence(p, q):
    return cross_entropy(p, q) - entropy(p)

p = np.array([0.7, 0.2, 0.1])
q = np.array([0.4, 0.3, 0.3])

print("H(p) =", entropy(p))
print("H(p,q) =", cross_entropy(p, q))
print("D_KL(p||q) =", kl_divergence(p, q))
print("D_KL(q||p) =", kl_divergence(q, p), "  <- different from D_KL(p||q), confirming asymmetry")

# --- Cross-entropy loss on a batch of softmax outputs ---
def softmax(logits):
    exp = np.exp(logits - logits.max(axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)

logits = np.array([[2.0, 1.0, 0.1], [0.5, 2.5, 0.3]])
true_labels = np.array([0, 1])  # class indices
probs = softmax(logits)
batch_ce = -np.log(probs[np.arange(len(true_labels)), true_labels]).mean()
print("batch cross-entropy loss:", batch_ce)
```

## See also

- [Loss Functions](./loss-functions.md) — cross-entropy as a trainable objective.
- [Statistics and Estimation](./statistics-and-estimation.md) — the MLE connection that makes cross-entropy the "correct" loss under a categorical noise model.
