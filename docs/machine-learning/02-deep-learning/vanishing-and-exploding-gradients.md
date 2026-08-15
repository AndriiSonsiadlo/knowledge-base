---
id: vanishing-and-exploding-gradients
title: Vanishing and Exploding Gradients
sidebar_label: Vanishing & Exploding Gradients
sidebar_position: 10
tags: [deep-learning, gradients, training, debugging]
---

# Vanishing and Exploding Gradients

For two decades, networks deeper than a handful of layers simply refused to train — not because the architecture was wrong, but because the gradient signal reaching the earliest layers had either shrunk to numerical zero or grown to numerical infinity by the time it arrived there. Understanding exactly why this happens is what makes the fixes (initialisation, activations, normalisation, residual connections) make sense as one coherent story rather than a grab-bag of tricks.

:::info[Key idea]
Gradients are products of many terms — anything consistently below one vanishes, anything consistently above one explodes, and both fail silently.
:::

<Figure
  src="/img/ml/deep/weight-init-and-gradient-flow.png"
  alt="Gradient magnitude across layers under vanishing, healthy and exploding regimes on a log scale"
  caption="Gradients are a product of per-layer Jacobians, so any consistent deviation from 1.0 compounds geometrically. The right-hand panel is the whole problem: ×0.6 per layer leaves the early layers with nothing to learn from."
/>

## The product-of-Jacobians view

[Backpropagation](./backpropagation.md)'s delta recursion, $\delta^{[l]} = (W^{[l+1]\top}\delta^{[l+1]}) \odot g'(z^{[l]})$, applied repeatedly across $L$ layers, means the gradient reaching layer 1 is (roughly) a product of $L$ Jacobian-like terms, one per layer. Multiplying many numbers together: if each factor is reliably less than 1, the product shrinks exponentially with depth; if each factor is reliably greater than 1, the product grows exponentially.

## Vanishing: symptoms

Early layers' weights barely change during training (their gradients are near zero); the loss plateaus almost immediately and stays flat; deeper layers may still be learning while shallow ones are effectively frozen.

## Exploding: symptoms

The loss suddenly becomes `NaN` or `inf`; training that was progressing normally abruptly diverges; loss values oscillate wildly rather than decreasing.

## The role of the activation derivative

From [Activation Functions](./activation-functions.md): sigmoid's derivative maxes out at 0.25, tanh's at 1.0 — but both shrink toward zero away from the origin (saturation). Every layer using a saturating activation multiplies the backward gradient by a factor that's often well below 1, compounding across depth.

## The role of weight scale

If weight matrices consistently have a spectral radius (largest eigenvalue magnitude) below 1, repeated multiplication by them shrinks the gradient; above 1, it grows. This is exactly why [Weight Initialization](./weight-initialization.md) targets a specific variance — too small triggers vanishing, too large triggers exploding, independent of the activation function's own contribution.

## Why recurrent networks suffer most

A recurrent network ([Recurrent Neural Networks](../03-sequence-and-nlp/recurrent-neural-networks.md)) reuses the *identical* weight matrix at every timestep, so the product-of-Jacobians argument applies not across different layers with potentially different scales, but across the *same* matrix repeated many times — any deviation from spectral radius exactly 1 compounds multiplicatively across the sequence length, which is often far longer than a typical feedforward network's depth.

## The fixes, in order of impact

1. **Initialisation** ([Weight Initialization](./weight-initialization.md)) — start with a variance that neither shrinks nor grows the signal.
2. **ReLU-family activations** ([Activation Functions](./activation-functions.md)) — non-saturating on the positive side, derivative exactly 1 there rather than shrinking.
3. **Normalisation layers** ([Normalization Layers](./normalization-layers.md)) — actively re-stabilise the activation distribution at every layer, reducing sensitivity to any single upstream cause.
4. **Residual connections** ([Skip Connections and Depth](./skip-connections-and-depth.md)) — give the gradient an additive path that bypasses the multiplicative chain entirely.
5. **Gradient clipping** — a direct, blunt fix for exploding gradients specifically (caps the gradient norm before the optimiser step), doesn't address vanishing.

## Measuring it directly: per-layer gradient norms

$$
\|\nabla_{W^{[l]}} L\|_2 \text{, plotted against } l
$$

A healthy network shows gradient norms of roughly similar magnitude across all layers. A collapsing curve (norms shrinking by orders of magnitude from output to input layers) diagnoses vanishing directly; a curve exploding toward the input diagnoses the opposite.

## Diagnosis table

| Symptom | Likely cause | First fix to try |
|---|---|---|
| Loss flat from the start, early-layer weights unchanged | vanishing | switch to ReLU/He init |
| Loss becomes NaN suddenly | exploding | gradient clipping |
| Loss flat despite ReLU + good init | possibly still vanishing in a very deep net | add normalisation layers, residual connections |
| Recurrent model specifically fails to learn long-range dependencies | vanishing, compounded by sequence length | switch to LSTM/GRU, or use attention instead |

## Code: 20-layer sigmoid net collapsing, He+ReLU surviving, clipping an explosion

```python title="vanishing_exploding_demo.py"
import numpy as np

def sigmoid(z): return 1 / (1 + np.exp(-z))
def sigmoid_grad(a): return a * (1 - a)
def relu(z): return np.maximum(0, z)
def relu_grad(a): return (a > 0).astype(float)

def build_and_backprop(depth, width, activation, init_scale, X, y):
    if activation == "sigmoid":
        act, act_grad = sigmoid, sigmoid_grad
    else:
        act, act_grad = relu, relu_grad
    Ws = [np.random.default_rng(l).normal(scale=init_scale, size=(width, width)) for l in range(depth)]
    activations = [X]
    a = X
    for W in Ws:
        a = act(a @ W)
        activations.append(a)
    delta = (activations[-1] - y) * act_grad(activations[-1])
    grad_norms = []
    for l in reversed(range(depth)):
        grad_W = activations[l].T @ delta / len(X)
        grad_norms.append(np.linalg.norm(grad_W))
        delta = (delta @ Ws[l].T) * act_grad(activations[l])
    return list(reversed(grad_norms))  # input-to-output order

rng = np.random.default_rng(0)
X = rng.normal(size=(64, 50))
y = rng.normal(size=(64, 50))

sigmoid_norms = build_and_backprop(20, 50, "sigmoid", init_scale=1.0, X=X, y=y)
he_relu_norms = build_and_backprop(20, 50, "relu", init_scale=np.sqrt(2/50), X=X, y=y)

print("layer | sigmoid grad norm | He+ReLU grad norm")
for i, (s, h) in enumerate(zip(sigmoid_norms, he_relu_norms)):
    print(f"{i:5d} | {s:17.2e} | {h:17.2e}")

# --- Gradient clipping applied to an exploding case ---
exploding_grad = np.array([50.0, -80.0, 200.0])
max_norm = 5.0
norm = np.linalg.norm(exploding_grad)
clipped = exploding_grad * (max_norm / norm) if norm > max_norm else exploding_grad
print(f"\noriginal grad norm: {norm:.1f}, clipped grad norm: {np.linalg.norm(clipped):.1f}")
```

The sigmoid network's gradient norms should collapse by many orders of magnitude from the output layer to the input layer; the He+ReLU network's norms should stay far more comparable across all 20 layers — direct numerical confirmation of the vanishing-gradient argument.

## See also

- [Backpropagation](./backpropagation.md) — the delta recursion whose repeated multiplication causes this.
- [Skip Connections and Depth](./skip-connections-and-depth.md) — the architectural fix that solved this most decisively.
