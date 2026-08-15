---
id: curse-of-dimensionality
title: Curse of Dimensionality
sidebar_label: Curse of Dimensionality
sidebar_position: 17
tags: [foundations, theory, dimensionality]
---

# Curse of Dimensionality

Geometric intuitions built in two or three dimensions stop being true once you have two hundred features. As dimension grows, volume concentrates in the corners, distances between points converge toward a single value, and "nearest neighbour" stops meaning much of anything.

:::info[Key idea]
As dimensions grow, volume concentrates in the corners, all distances converge, and "nearest neighbour" stops meaning anything.
:::

<Figure
  src="/img/ml/foundations/curse-of-dimensionality.png"
  alt="Left: the ratio of farthest to nearest distance collapsing as dimensions rise. Right: the fraction of a cube near its centre falling exponentially"
  caption="As dimensions grow, all pairwise distances converge — so 'nearest neighbour' stops being meaningful — and the volume of a cube flees to its corners, leaving the centre essentially empty."
/>

## Data sparsity grows exponentially with dimension

To cover a $d$-dimensional space at the same density as a 1-D line covered with 10 points, you'd need $10^d$ points. At $d = 2$ that's 100 points; at $d = 20$ it's $10^{20}$ — no realistic dataset comes close. Any fixed-size dataset becomes exponentially sparser as dimension grows, and "nearby" points in high dimensions are, in practice, still very far apart.

## Distance concentration

As dimension grows, the ratio between the farthest and nearest neighbour's distance to a query point tends toward 1 — every point becomes roughly equidistant from every other point. This is devastating for any method (like [k-NN](../01-classical-ml/k-nearest-neighbors.md)) that relies on "close" points being meaningfully closer than "far" ones.

## Volume of a hypersphere vs. its bounding cube

The ratio of a unit hypersphere's volume to its bounding hypercube's volume shrinks toward zero as dimension increases — almost all of a high-dimensional cube's volume sits in its corners, far from the centre, which is deeply counter-intuitive if your geometric instinct comes from 2-D and 3-D shapes.

$$
\frac{V_{\text{sphere}}(d)}{V_{\text{cube}}(d)} = \frac{\pi^{d/2}}{2^d \, \Gamma(d/2 + 1)}
$$

| Symbol | Meaning |
|---|---|
| $d$ | number of dimensions |
| $\Gamma$ | the gamma function, generalising factorial to non-integers |

## Which algorithms suffer, which resist

- **Suffers most**: k-NN, kernel methods relying on distance ([Kernel Methods](../01-classical-ml/kernel-methods.md)), any density estimation technique.
- **Resists**: tree-based methods (split on one feature at a time, largely dimension-agnostic), and deep neural networks — because real high-dimensional data (images, text) typically lies near a much lower-dimensional manifold within the ambient space, and networks can learn that manifold.

## The manifold hypothesis

Real-world high-dimensional data (a photo has millions of pixel-dimensions) is not spread uniformly through that space — it lies on or near a much lower-dimensional curved surface (a manifold) within it. A network doesn't need to cope with the full ambient dimensionality; it only needs to model the manifold, which is why deep learning works at all on inputs where the curse would otherwise be crippling.

## Mitigations

- Feature selection — reduce $d$ directly ([Data Preprocessing and Features](./data-preprocessing-and-features.md)).
- Dimensionality reduction — project onto a lower-dimensional subspace ([PCA and SVD](../01-classical-ml/pca-and-svd.md)).
- Better distance metrics — some (like cosine similarity on normalised vectors) degrade less severely than raw Euclidean distance.
- More data — doesn't fix the exponential sparsity, but helps proportionally.

## Implication for embeddings

Embedding spaces in [Word Embeddings](../03-sequence-and-nlp/word-embeddings.md) are deliberately kept at a modest dimensionality (hundreds, not millions) precisely so that distance-based operations (cosine similarity, nearest-neighbour retrieval) remain meaningful — an embedding space with too many dimensions would suffer exactly the concentration problem described above.

## Code: pairwise distances collapsing as dimension grows

```python title="curse_of_dimensionality_demo.py"
import numpy as np

rng = np.random.default_rng(0)

print("dimension | min dist | max dist | ratio (max/min)")
for d in [2, 10, 100, 1000]:
    points = rng.uniform(0, 1, size=(500, d))
    query = rng.uniform(0, 1, size=d)
    dists = np.linalg.norm(points - query, axis=1)
    ratio = dists.max() / dists.min()
    print(f"{d:9d} | {dists.min():.4f}  | {dists.max():.4f}  | {ratio:.4f}")

# --- Sphere/cube volume ratio ---
from math import gamma, pi

def sphere_cube_ratio(d):
    return (pi ** (d / 2)) / (2 ** d * gamma(d / 2 + 1))

for d in [2, 5, 10, 20, 50]:
    print(f"d={d:3d}: sphere/cube volume ratio = {sphere_cube_ratio(d):.6e}")
```

The max/min distance ratio collapses toward 1 as $d$ grows from 2 to 1000 — direct numerical proof that "nearest" stops being a meaningful concept in high dimensions, and the sphere/cube ratio shrinks toward zero just as fast.

## See also

- [Linear Algebra](./linear-algebra.md) — the vector-space notation this page's geometry is built on.
- [Data Preprocessing and Features](./data-preprocessing-and-features.md) — feature selection as one direct mitigation.
