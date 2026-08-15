---
id: content-based-and-hybrid
title: Content-Based and Hybrid Recommenders
sidebar_label: Content-Based & Hybrid
sidebar_position: 3
tags: [recommender-systems, content-based, hybrid, two-tower, embeddings]
---

# Content-Based and Hybrid Recommenders

Collaborative filtering cannot recommend an item nobody has touched. Content-based filtering can, because it looks at what the item *is* rather than who engaged with it — and every production system ends up combining the two.

:::info[Key idea]
Content-based methods match item attributes against a profile of what the user has liked before, so a brand-new item is recommendable on day one. The price is over-specialisation: they can only ever suggest more of the same. Hybrids exist because each approach fails exactly where the other works.
:::

## Content-based filtering

Represent each item as a feature vector, build a user profile from the items they engaged with, and rank by similarity.

| Item type | Representation |
|---|---|
| Text (articles, descriptions) | TF-IDF, or [sentence embeddings](../03-sequence-and-nlp/word-embeddings.md) |
| Structured (genre, brand, price) | One-hot / numeric features |
| Images | CNN or [ViT](../04-computer-vision/vision-transformers.md) embeddings |
| Audio | Spectrogram embeddings |
| Mixed | Concatenated, or a learned multimodal encoder |

The user profile is usually a weighted average of the vectors of items they liked — recency-weighted, since taste drifts.

### Strengths and the one big weakness

| Strengths | Weaknesses |
|---|---|
| Handles new items immediately | **Over-specialisation** — no serendipity |
| Works for a single user with no community | Needs good item features |
| Explanations are natural ("because it's sci-fi") | Cannot learn quality, only similarity |
| No popularity bias | New *users* still cold |

Over-specialisation is the defining flaw. A user who watched three documentaries gets documentaries forever; the system has no mechanism to discover that documentary-watchers also enjoy something entirely unrelated. Collaborative filtering finds exactly those non-obvious connections — which is why the combination is so much stronger than either.

Note also that content-based methods solve the new-*item* problem but **not** the new-*user* problem: with no interaction history there is no profile to build.

## Hybridisation strategies

| Strategy | How | Notes |
|---|---|---|
| **Weighted** | Score = α·CF + (1−α)·CB | Simplest; tune α, or vary it by data availability |
| **Switching** | Use CB when interactions are few, CF once they accumulate | Explicit cold-start handling |
| **Cascade** | CF ranks, CB breaks ties (or vice versa) | Cheap |
| **Feature augmentation** | One model's output becomes the other's input | Effective, harder to debug |
| **Feature combination** | One model over both interaction and content features | **What modern systems do** |

The last row is where the field landed. Rather than maintaining two systems and blending them, put user features, item content features, and interaction-derived features into a single gradient-boosted or neural ranker. Cold start then handles itself: a new item simply has null interaction features and non-null content features, and the model has learned what to do with that.

## Two-tower models

The dominant neural architecture for candidate generation:

- A **user tower** encodes user features and history into a vector.
- An **item tower** encodes item content features into a vector in the same space.
- Affinity is their dot product, trained with a contrastive or softmax objective over sampled negatives.

The reason it dominates is operational rather than statistical. Because the two towers are independent until the final dot product, item embeddings can be computed **offline** for the whole catalogue and indexed for approximate nearest-neighbour search. At request time you encode the user once and run an ANN query — millions of candidates in single-digit milliseconds.

A model that lets user and item features interact early (a "cross" architecture) is more expressive but must score every candidate individually, so it can only be afforded at the ranking stage on a few hundred items. That asymmetry is precisely what produces the [two-stage pipeline](./the-recommendation-problem.md).

:::tip[Negative sampling is where two-tower models are won or lost]
With only positives observed, you must supply negatives. In-batch negatives (treat other items in the batch as negatives) are nearly free but are sampled by popularity, which biases the model against popular items — usually corrected with a `logQ` popularity correction. Hard negatives (plausible but not interacted) improve quality markedly and destabilise training if overused. This choice affects results more than the architecture does.
:::

## Sequential and session-based recommendation

Order carries information that a bag of interactions loses: someone who just bought a phone wants a case, not another phone. Sequential recommenders treat a user's history as a sequence and predict the next item — the same framing as [language modelling](../03-sequence-and-nlp/language-modeling-basics.md), with items in place of tokens.

| Model | Approach |
|---|---|
| GRU4Rec | RNN over the session |
| SASRec | Self-attention, unidirectional |
| BERT4Rec | Bidirectional, masked-item objective |

Session-based recommendation matters especially where users are anonymous — most e-commerce traffic — because there is no long-term profile to fall back on, only the current session.

## Knowledge-based and constraint-based

For rare, high-value purchases — houses, cars, insurance — nobody has a useful interaction history, and item similarity is not the point. These systems query requirements explicitly and filter by constraints. Not machine learning at all in many cases, and the right answer when purchases are infrequent enough that behavioural data never accumulates.

## Code: content-based profiles and a weighted hybrid

```python title="content_hybrid.py"
import numpy as np


def tfidf(docs, vocab=None):
    """Minimal TF-IDF over whitespace-tokenised documents."""
    tokens = [d.lower().split() for d in docs]
    vocab = vocab or sorted({t for doc in tokens for t in doc})
    index = {t: i for i, t in enumerate(vocab)}

    tf = np.zeros((len(docs), len(vocab)))
    for r, doc in enumerate(tokens):
        for t in doc:
            tf[r, index[t]] += 1
    tf /= np.maximum(tf.sum(axis=1, keepdims=True), 1)

    df = (tf > 0).sum(axis=0)
    idf = np.log((1 + len(docs)) / (1 + df)) + 1
    return tf * idf, vocab


def l2_normalise(M):
    return M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-9)


def build_user_profile(item_vectors, liked_indices, weights=None):
    """Weighted average of the items a user engaged with."""
    if len(liked_indices) == 0:
        return np.zeros(item_vectors.shape[1])
    weights = np.ones(len(liked_indices)) if weights is None else np.asarray(weights)
    profile = (item_vectors[liked_indices] * weights[:, None]).sum(axis=0) / weights.sum()
    return profile / max(np.linalg.norm(profile), 1e-9)


def hybrid_scores(cf_scores, cb_scores, alpha):
    """Blend after rank-normalising, since the two scales are unrelated."""
    def rank_norm(s):
        order = np.argsort(np.argsort(s))
        return order / max(len(s) - 1, 1)
    return alpha * rank_norm(cf_scores) + (1 - alpha) * rank_norm(cb_scores)


if __name__ == "__main__":
    catalogue = [
        "space opera science fiction adventure",
        "hard science fiction space exploration",
        "romantic comedy light hearted",
        "romance drama emotional",
        "science documentary space telescope",     # a brand-new item, no interactions
        "action thriller spy adventure",
    ]
    titles = ["Space Opera", "Hard SF", "Rom-Com", "Romance Drama",
              "Space Doc (NEW)", "Spy Thriller"]

    V, _ = tfidf(catalogue)
    V = l2_normalise(V)

    liked = [0, 1]                                   # user enjoys the two SF films
    profile = build_user_profile(V, liked)
    cb = V @ profile

    # A collaborative signal that cannot score the new item at all.
    cf = np.array([0.82, 0.75, 0.30, 0.22, 0.0, 0.55])

    print(f"{'item':<18}{'CB':>7}{'CF':>7}{'hybrid':>9}")
    blend = hybrid_scores(cf, cb, alpha=0.6)
    for i, name in enumerate(titles):
        seen = " (already seen)" if i in liked else ""
        print(f"{name:<18}{cb[i]:>7.3f}{cf[i]:>7.2f}{blend[i]:>9.3f}{seen}")

    ranked = [i for i in np.argsort(-blend) if i not in liked]
    print(f"\nrecommended: {titles[ranked[0]]}")
    print("The new item gets a real score from content alone — CF assigns it 0.0.")
```

The rank-normalisation in `hybrid_scores` is not incidental: a cosine similarity in [0, 1] and a factorisation score on a 1–5 rating scale cannot be added directly, and blending raw scores is a common source of a hybrid that is worse than either component.

## See also

- [Collaborative Filtering](./collaborative-filtering.md) — the half this page complements.
- [The Recommendation Problem](./the-recommendation-problem.md) — why the two-stage pipeline exists.
- [Word Embeddings](../03-sequence-and-nlp/word-embeddings.md) — the representations content-based methods lean on.
