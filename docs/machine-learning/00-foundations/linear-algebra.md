---
id: linear-algebra
title: Linear Algebra for ML
sidebar_label: Linear Algebra
sidebar_position: 4
tags: [foundations, math, linear-algebra]
---

# Linear Algebra for ML

A layer in a neural network, a linear regression model, and a batch of predictions being computed all at once are the same operation: multiply a matrix by a vector (or another matrix). Nearly every piece of notation in this knowledge base is linear algebra, so this page fixes the vocabulary once.

:::info[Key idea]
A layer, a linear model, and a batch of predictions are all the same operation — $Xw$.
:::

## Vectors and vector spaces

A vector $x \in \mathbb{R}^d$ is an ordered list of $d$ numbers. Geometrically, it's a point (or an arrow from the origin) in $d$-dimensional space. A dataset of $n$ examples, each with $d$ features, is stored as a matrix $X \in \mathbb{R}^{n \times d}$ — one row per example.

## Matrices as linear maps

A matrix $W \in \mathbb{R}^{d \times k}$ is a function: it takes a vector in $\mathbb{R}^d$ and produces a vector in $\mathbb{R}^k$ via $y = W^\top x$ (or $y = Xw$ when $X$ is a batch of row-vectors and $w$ a single weight vector). This is "linear" because $W(x_1 + x_2) = Wx_1 + Wx_2$ — no bending, no thresholds, just scaling and combining.

## Matrix multiplication as composition

Multiplying matrices $AB$ means: apply $B$'s transformation, then apply $A$'s. Order matters — $AB \neq BA$ in general — because composing "rotate then scale" is not the same as "scale then rotate."

## Shapes and broadcasting

The single biggest source of bugs in this entire field is a shape mismatch. For $y = Xw$: if $X$ is $(n, d)$ and $w$ is $(d,)$, the output $y$ is $(n,)$ — one prediction per row. Broadcasting lets NumPy/PyTorch apply an operation between arrays of different shapes by implicitly repeating the smaller one along missing dimensions, but it fails silently when shapes are *compatible but wrong* — e.g. adding a $(n,)$ vector to a $(n, 1)$ column produces an $(n, n)$ matrix by accident, not an error.

## Transpose, inverse, pseudo-inverse

- **Transpose** $X^\top$ flips rows and columns: $(X^\top)_{ij} = X_{ji}$.
- **Inverse** $A^{-1}$ satisfies $AA^{-1} = I$ — only exists for square, full-rank matrices.
- **Pseudo-inverse** $X^+ = (X^\top X)^{-1}X^\top$ generalises "inverse" to non-square matrices, and is exactly the closed-form solution to least squares (see [Linear Regression](../01-classical-ml/linear-regression.md)).

## Norms

| Norm | Formula | Use |
|---|---|---|
| $L_1$ | $\|x\|_1 = \sum_i \lvert x_i \rvert$ | sparsity-inducing penalties (Lasso) |
| $L_2$ | $\|x\|_2 = \sqrt{\sum_i x_i^2}$ | Euclidean distance, weight decay |
| Frobenius | $\|A\|_F = \sqrt{\sum_{ij} A_{ij}^2}$ | matrix version of $L_2$ |

## Dot product as similarity

$x \cdot y = \sum_i x_i y_i = \|x\|\|y\|\cos\theta$. Two vectors pointing the same direction have a large positive dot product; orthogonal vectors have zero; opposite vectors are negative. This is why cosine similarity (dot product normalised by magnitude) is the default similarity measure for embeddings throughout [Sequences & NLP](../03-sequence-and-nlp/word-embeddings.md).

## Eigenvectors and eigenvalues

For a square matrix $A$, an eigenvector $v$ satisfies $Av = \lambda v$ — applying $A$ to $v$ only scales it, never rotates it. $\lambda$ is the corresponding eigenvalue. Geometrically, eigenvectors are the axes a transformation stretches along without turning.

| Symbol | Meaning |
|---|---|
| $A$ | a square matrix (a linear transformation) |
| $v$ | an eigenvector of $A$ |
| $\lambda$ | the eigenvalue: how much $A$ scales along $v$ |

## SVD, stated

Every matrix $X$ (not just square ones) factors as $X = U\Sigma V^\top$, where $U, V$ are orthogonal and $\Sigma$ is diagonal with non-negative entries (singular values). This is the machinery behind [PCA and SVD](../01-classical-ml/pca-and-svd.md) — proved out there in full.

## Why GPUs make this fast

Matrix multiplication decomposes into millions of independent multiply-accumulate operations that can run in parallel — exactly what GPUs are built for. A neural network forward pass is a sequence of matrix multiplications, which is why the entire deep learning revolution rode on hardware originally built for rendering graphics.

## Code: a linear layer by hand, and a broadcasting bug

```python title="linear_algebra_shapes.py"
import numpy as np

n, d, k = 5, 3, 2          # 5 examples, 3 input features, 2 output units
X = np.random.randn(n, d)   # shape (5, 3)
W = np.random.randn(d, k)   # shape (3, 2)
b = np.random.randn(k)      # shape (2,)

Y = X @ W + b                # (5,3) @ (3,2) -> (5,2), then broadcast +(2,)
assert Y.shape == (n, k)
print("linear layer output shape:", Y.shape)

# --- The classic broadcasting bug ---
predictions = np.random.randn(n)        # shape (5,)  -- one prediction per row
targets = np.random.randn(n, 1)         # shape (5,1) -- accidentally a column vector

wrong = predictions - targets           # broadcasts to (5,5) instead of (5,) !
print("buggy shape (should be (5,), is):", wrong.shape)

correct = predictions - targets.squeeze()
print("fixed shape:", correct.shape)

# --- Eigenvalues ---
A = np.array([[2.0, 0.0], [0.0, 3.0]])
eigenvalues, eigenvectors = np.linalg.eig(A)
print("eigenvalues:", eigenvalues)
```

The buggy block is not a crash — it silently produces a $(5,5)$ matrix of pairwise differences instead of the $(5,)$ vector of per-example residuals you wanted, and every downstream computation is now wrong without raising an error.

## See also

- [Calculus and Gradients](./calculus-and-gradients.md) — the derivative machinery built on top of this notation.
- [Curse of Dimensionality](./curse-of-dimensionality.md) — what happens to these geometric intuitions as $d$ grows large.
