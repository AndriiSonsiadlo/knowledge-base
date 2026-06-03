---
id: backpropagation
title: Backpropagation
sidebar_label: Backpropagation
sidebar_position: 3
tags: [deep-learning, training, calculus, backpropagation]
---

# Backpropagation

Every parameter in a deep network needs its own gradient, and a network can have millions of them. Backpropagation is the algorithm that computes every single one, applying the chain rule from [Calculus and Gradients](../00-foundations/calculus-and-gradients.md) systematically backwards through the computational graph — at roughly the same cost as one forward pass. That efficiency is the entire reason deep learning became computationally feasible.

:::info[Key idea]
One backward sweep computes every parameter's gradient at roughly the cost of one forward pass — that efficiency is the entire reason deep learning is feasible.
:::

## The goal

For every weight matrix $W^{[l]}$ and bias $b^{[l]}$ in the network, compute $\partial L / \partial W^{[l]}$ and $\partial L / \partial b^{[l]}$, needed by [Gradient Descent](../00-foundations/gradient-descent.md)'s update rule.

## The chain rule, in vector form

$$
\frac{\partial L}{\partial x} = \left(\frac{\partial z}{\partial x}\right)^\top \frac{\partial L}{\partial z}
$$

Exactly the vector chain rule from [Calculus and Gradients](../00-foundations/calculus-and-gradients.md), applied at every edge of the [computational graph](./forward-pass-and-computational-graphs.md).

## Local gradients per operation

Each operation in the graph (matrix multiply, add, activation) has a simple local derivative. The chain rule composes these local derivatives across the whole graph — backpropagation never needs to derive one giant expression for the whole network; it only needs each operation's own small, local derivative.

## The backward pass through one layer, derived

Define $\delta^{[l]} = \partial L / \partial z^{[l]}$ — the gradient of the loss with respect to layer $l$'s pre-activation. For the output layer:

$$
\delta^{[L]} = \nabla_a L \odot g'(z^{[L]})
$$

For every earlier layer, the error propagates backward through the next layer's weights:

$$
\delta^{[l]} = \left(W^{[l+1]\top} \delta^{[l+1]}\right) \odot g'(z^{[l]})
$$

And the actual parameter gradients:

$$
\frac{\partial L}{\partial W^{[l]}} = \delta^{[l]} a^{[l-1]\top}, \qquad \frac{\partial L}{\partial b^{[l]}} = \delta^{[l]}
$$

| Symbol | Meaning |
|---|---|
| $\delta^{[l]}$ | error signal at layer $l$: $\partial L / \partial z^{[l]}$ |
| $\odot$ | elementwise (Hadamard) product |
| $g'$ | derivative of the activation function |
| $\nabla_a L$ | gradient of the loss with respect to the network's final output |

## Generalising to L layers, and the delta recursion

Compute $\delta^{[L]}$ first, then apply the recursion above to get $\delta^{[L-1]}, \delta^{[L-2]}, \ldots, \delta^{[1]}$, one layer at a time, moving backward through the network — hence "back"-propagation. Each layer's parameter gradients are extracted directly from its $\delta$ as soon as it's computed.

## Vectorised implementation over a batch

For a batch of $B$ examples, every quantity above gains a batch dimension, and the parameter gradients are summed (or averaged) across the batch: $\partial L/\partial W^{[l]} = \frac{1}{B}\sum_i \delta_i^{[l]} a_i^{[l-1]\top}$, implemented as a single matrix multiplication rather than a loop over examples.

## Why gradients are accumulated, not overwritten

In frameworks like PyTorch, calling `.backward()` *adds* to existing `.grad` values rather than replacing them — this supports gradient accumulation across multiple batches (useful when a desired batch size doesn't fit in memory) but means `zero_grad()` must be called before every new backward pass, or gradients from the previous step silently contaminate the current one — see [Training Loop Anatomy](./training-loop-anatomy.md)'s bug catalogue.

## Gradient checking as the only honest verification

Reuse the `gradient_check` helper from [Calculus and Gradients](../00-foundations/calculus-and-gradients.md): compare the analytic gradient computed by backpropagation against a numerical finite-difference approximation. This is the standard way to verify a hand-written backward pass is actually correct — the code below does exactly that.

## Computational cost: forward vs. backward

The backward pass costs roughly the same as the forward pass — each operation's local gradient computation is comparable in cost to the operation itself. This is why training (forward + backward + update) costs roughly 2-3x a single forward pass, not more.

## What autodiff does that this manual derivation does not

Everything above was derived by hand for a specific fully-connected architecture. Real frameworks implement this generically: every primitive operation (matrix multiply, add, sigmoid, convolution, ...) registers its own local backward rule once, and the framework composes them automatically for *any* graph built from those primitives — see [PyTorch Tensors and Autograd](./pytorch-tensors-and-autograd.md), which cashes in everything derived on this page.

## Code: a complete 2-layer network, trained, with a gradient check

```python title="backprop_two_layer_net.py"
import numpy as np
from sklearn.datasets import make_classification

def sigmoid(z): return 1 / (1 + np.exp(-z))
def sigmoid_grad(a): return a * (1 - a)  # a is already sigmoid(z)

class TwoLayerNet:
    def __init__(self, n_in, n_hidden, n_out, rng):
        self.W1 = rng.normal(scale=0.5, size=(n_in, n_hidden))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(scale=0.5, size=(n_hidden, n_out))
        self.b2 = np.zeros(n_out)

    def forward(self, X):
        self.a0 = X
        self.z1 = X @ self.W1 + self.b1
        self.a1 = sigmoid(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = sigmoid(self.z2)
        return self.a2

    def backward(self, y):
        m = y.shape[0]
        delta2 = (self.a2 - y) * sigmoid_grad(self.a2)  # dL/dz2, for MSE loss
        dW2 = self.a1.T @ delta2 / m
        db2 = delta2.mean(axis=0)
        delta1 = (delta2 @ self.W2.T) * sigmoid_grad(self.a1)
        dW1 = self.a0.T @ delta1 / m
        db1 = delta1.mean(axis=0)
        return dW1, db1, dW2, db2

    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]

rng = np.random.default_rng(0)
X, y = make_classification(n_samples=200, n_features=5, random_state=0)
y = y.reshape(-1, 1).astype(float)
X = (X - X.mean(0)) / X.std(0)

net = TwoLayerNet(5, 8, 1, rng)
lr = 1.0
for step in range(3000):
    pred = net.forward(X)
    loss = np.mean((pred - y) ** 2)
    dW1, db1, dW2, db2 = net.backward(y)
    net.W1 -= lr * dW1; net.b1 -= lr * db1
    net.W2 -= lr * dW2; net.b2 -= lr * db2
    if step % 1000 == 0:
        print(f"step {step}: loss={loss:.4f}")

# --- Gradient check on W2, reusing the finite-difference method ---
def loss_fn(W2_flat):
    net.W2 = W2_flat.reshape(net.W2.shape)
    pred = net.forward(X)
    return np.mean((pred - y) ** 2)

W2_orig = net.W2.copy()
analytic = net.backward(y)[2].ravel()
eps = 1e-5
numerical = np.zeros_like(net.W2.ravel())
flat = net.W2.ravel().copy()
for i in range(len(flat)):
    flat[i] += eps; loss_plus = loss_fn(flat)
    flat[i] -= 2*eps; loss_minus = loss_fn(flat)
    flat[i] += eps
    numerical[i] = (loss_plus - loss_minus) / (2 * eps)
net.W2 = W2_orig
rel_error = np.linalg.norm(analytic - numerical) / (np.linalg.norm(analytic) + np.linalg.norm(numerical) + 1e-12)
print(f"gradient check relative error: {rel_error:.2e}  (should be very small)")
```

## See also

- [Calculus and Gradients](../00-foundations/calculus-and-gradients.md) — the chain rule and gradient-check helper this page applies.
- [Vanishing and Exploding Gradients](./vanishing-and-exploding-gradients.md) — what happens when this backward product is repeated across many layers.
