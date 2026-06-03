---
id: language-modeling-basics
title: Language Modeling Basics
sidebar_label: Language Modeling Basics
sidebar_position: 3
tags: [nlp, language-modeling, perplexity, ngram]
---

# Language Modeling Basics

Every generative model in this section — from a bigram model to GPT — is doing the same thing: predicting the next token given everything before it. That single objective, applied one token at a time, is the entire engine behind modern text generation; everything else in this section is about how to do that prediction better.

:::info[Key idea]
A language model is a probability distribution over sequences, and every generative model here is the chain rule applied one token at a time.
:::

## The chain-rule factorisation

$$
P(w_1, \ldots, w_n) = \prod_{t=1}^n P(w_t \mid w_1, \ldots, w_{t-1})
$$

Any joint probability over a sequence decomposes exactly into a product of conditional next-token probabilities — this is not an approximation, it's the chain rule of probability from [Probability and Distributions](../00-foundations/probability-and-distributions.md), and it's what turns "model a whole sentence" into "model one next-token prediction, applied repeatedly."

## n-gram models and the Markov assumption

Modelling $P(w_t \mid w_1, \ldots, w_{t-1})$ exactly requires exponentially many parameters as context grows. n-gram models simplify with a **Markov assumption**: the next word depends only on the previous $n-1$ words, not the entire history — $P(w_t \mid w_{t-n+1}, \ldots, w_{t-1})$, estimated directly from corpus counts.

## Sparsity and smoothing

Most possible $n$-word sequences never appear in any training corpus, however large — a naive count-based estimate assigns zero probability to any unseen sequence, which is catastrophic (one unseen bigram makes the entire sentence's probability zero). **Smoothing** techniques redistribute some probability mass to unseen sequences: add-$k$ smoothing (a simple pseudo-count), backoff (fall back to a shorter n-gram when the longer one is unseen), Kneser-Ney (a more sophisticated, empirically strong backoff/interpolation scheme).

## Why n-grams hit a wall

Even with smoothing, n-gram models cannot capture dependencies longer than $n-1$ words, and the parameter count still grows exponentially with $n$ — practical n-gram models rarely exceed $n=5$, far short of the long-range context real language often requires.

## Neural language models

Replace the fixed-window n-gram lookup table with a neural network — first feedforward, then [Recurrent Neural Networks](./recurrent-neural-networks.md) (unbounded context in principle), and ultimately [Transformer Architecture](./transformer-architecture.md) (unbounded context with full parallelism) — each step removing more of the n-gram model's structural limitations.

## The causal (autoregressive) objective

Training a language model means maximising $\prod_t P(w_t \mid w_{<t})$ over a training corpus — equivalently, minimising the negative log-likelihood, which is exactly the cross-entropy loss from [Loss Functions](../00-foundations/loss-functions.md) applied at every position in the sequence.

## Teacher forcing vs. autoregressive generation, and the exposure-bias gap

**During training**, the model predicts each next token given the *true* preceding tokens from the training data (teacher forcing) — even if the model's own previous prediction was wrong, it sees the correct history for predicting the next one. **During inference**, the model must feed its *own* generated tokens back in as the context for the next prediction, since there's no ground truth to consult. This mismatch — trained on true history, deployed on its own possibly-flawed history — is called **exposure bias**, and is one reason generated text can drift into increasingly poor quality across a long generation, compounding early errors.

## Perplexity, defined and interpreted

$$
\text{Perplexity} = \exp\left(-\frac{1}{n}\sum_{t=1}^n \log P(w_t \mid w_{<t})\right)
$$

Exactly the exponentiated cross-entropy from [Information Theory](../00-foundations/information-theory.md) (using natural log here rather than log base 2, so exponentiated with $e$ rather than $2$). A perplexity of 20 means: on average, the model was as uncertain about the next token as if it were choosing uniformly among 20 equally likely options — lower perplexity means better predictions.

| Symbol | Meaning |
|---|---|
| $P(w_t \mid w_{<t})$ | the model's predicted probability of the true next token, given history |
| $n$ | sequence length |

## What perplexity does not measure

Perplexity says nothing about whether generated text is *coherent*, *factually accurate*, *helpful*, or *safe* — it's purely a measure of how well the model predicted the specific held-out text it was evaluated on. Two models with identical perplexity can differ substantially in how useful or trustworthy their actual generations are — [Evaluating Language Models](./evaluating-language-models.md) covers the fuller evaluation picture.

## Bits per character

$\log_2$-based cross-entropy divided by the average number of characters per token, giving a metric comparable across different tokenisers with different vocabulary sizes — perplexity values are not directly comparable between models using different tokenisation schemes, but bits-per-character often is.

## Code: bigram model with smoothing, then a real model's perplexity

```python title="language_modeling_demo.py"
from collections import defaultdict, Counter
import numpy as np

corpus = "the cat sat on the mat the dog sat on the rug the cat and dog are friends the cat likes the dog".split()

bigram_counts = defaultdict(Counter)
unigram_counts = Counter(corpus)
for i in range(len(corpus) - 1):
    bigram_counts[corpus[i]][corpus[i+1]] += 1

vocab = list(set(corpus))
V = len(vocab)
k = 1  # add-k smoothing

def bigram_prob(w1, w2):
    return (bigram_counts[w1][w2] + k) / (unigram_counts[w1] + k * V)

def generate(start_word, length=10, rng=None):
    rng = rng or np.random.default_rng(0)
    words = [start_word]
    for _ in range(length - 1):
        probs = np.array([bigram_prob(words[-1], w) for w in vocab])
        probs /= probs.sum()
        words.append(rng.choice(vocab, p=probs))
    return " ".join(words)

print("generated text:", generate("the"))

def perplexity(text_tokens):
    log_prob_sum = sum(np.log(bigram_prob(text_tokens[i], text_tokens[i+1])) for i in range(len(text_tokens)-1))
    return np.exp(-log_prob_sum / (len(text_tokens) - 1))

print("bigram model perplexity on training text:", perplexity(corpus))

# --- distilgpt2 perplexity, for contrast ---
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
model = AutoModelForCausalLM.from_pretrained("distilgpt2")

def gpt2_perplexity(text):
    ids = tokenizer(text, return_tensors="pt").input_ids
    with torch.no_grad():
        loss = model(ids, labels=ids).loss  # cross-entropy loss, averaged per token
    return torch.exp(loss).item()

print("distilgpt2 perplexity:", gpt2_perplexity("The cat sat on the mat."))
```

## See also

- [Information Theory](../00-foundations/information-theory.md) — the entropy/cross-entropy machinery perplexity is built from.
- [Decoding Strategies](./decoding-strategies.md) — turning next-token probabilities into actual generated text.
