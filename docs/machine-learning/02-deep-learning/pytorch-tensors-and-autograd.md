---
id: pytorch-tensors-and-autograd
title: PyTorch Tensors and Autograd
sidebar_label: PyTorch Tensors & Autograd
sidebar_position: 12
tags: [deep-learning, pytorch, autograd, tensors]
---

# PyTorch Tensors and Autograd

Every gradient in the previous eleven pages was derived and coded by hand. From here on, a framework does that work — but only because it implements exactly the mechanism [Backpropagation](./backpropagation.md) already described: recording a computational graph as operations run, then walking it backward. Autograd is the manual backward pass, automated and generalised to arbitrary graphs.

:::info[Key idea]
Autograd records the operations you perform on tensors and replays that tape backwards — it is the manual backward pass, automated.
:::

## Tensors vs. NumPy arrays

A PyTorch `Tensor` looks and behaves almost identically to a NumPy array (same indexing, broadcasting, most of the same operations) with two additions: it can live on a GPU (`device`), and it can track the operations applied to it for automatic differentiation.

## dtype, device, shape

Every tensor has a `dtype` (`float32` by default for most training), a `device` (`cpu` or `cuda:0`), and a `shape` — operations between tensors on different devices raise an error, a common early bug when mixing CPU-loaded data with a GPU-resident model.

## requires_grad and the graph it builds

Setting `requires_grad=True` on a tensor tells PyTorch to track every subsequent operation involving it, building the computational graph from [Forward Pass and Computational Graphs](./forward-pass-and-computational-graphs.md) automatically and dynamically as the code executes.

## .backward() and .grad

Calling `.backward()` on a scalar tensor (typically the loss) walks the recorded graph backward, computing $\partial(\text{that scalar})/\partial x$ for every tensor `x` with `requires_grad=True`, and accumulates the result into `x.grad`.

## Why gradients accumulate, and zero_grad()

As covered in [Backpropagation](./backpropagation.md), `.grad` *adds* to its existing value rather than replacing it on every `.backward()` call — call `optimizer.zero_grad()` (or `tensor.grad = None`) before each new backward pass, or gradients from the previous step silently contaminate the current one.

## torch.no_grad() and inference mode

Wrapping code in `with torch.no_grad():` disables graph tracking entirely — necessary at inference/evaluation time, since building a graph that will never be backpropagated through wastes memory and computation for no benefit.

## detach()

Returns a new tensor sharing the same data but disconnected from the computational graph — useful when you need a tensor's *value* without wanting gradients to flow back through it (e.g. logging a metric, or stopping gradient flow to part of a larger model deliberately).

## Leaf vs. non-leaf tensors

A **leaf** tensor is one created directly by the user (not the result of an operation on other tracked tensors) — model parameters are leaves. A **non-leaf** tensor is the result of some operation on tracked tensors — intermediate activations are non-leaves, and by default their `.grad` is not retained after `.backward()` (only leaves' gradients are kept, since that's what the optimiser needs).

## nn.Module: parameters, forward, and registration

Subclassing `nn.Module` and assigning submodules/parameters as attributes automatically registers them, so `model.parameters()` finds every learnable tensor in the whole model tree without manual bookkeeping — this registration is what lets a single `optimizer = Adam(model.parameters())` call see every parameter in an arbitrarily nested architecture.

## nn.Sequential

For a simple feedforward stack, `nn.Sequential(layer1, layer2, ...)` avoids writing an explicit `forward` method — each layer's output feeds directly into the next, in the order listed.

## Reimplementing the backprop page's network, in ~15 lines

The entire hand-derived forward/backward pass from [Backpropagation](./backpropagation.md) collapses to a few lines, because autograd handles every derivative automatically — see the code block below.

## Reading a shape error message

PyTorch's shape-mismatch errors name the exact operation and the exact conflicting shapes (e.g. `mat1 and mat2 shapes cannot be multiplied (32x10 and 20x5)`) — the shape-bookkeeping discipline from [Forward Pass and Computational Graphs](./forward-pass-and-computational-graphs.md) is exactly what lets you read such a message and immediately locate which layer's dimensions don't line up.

## Code: tensor basics, autograd verified against the hand-derived gradient, nn.Module

```python title="pytorch_autograd_demo.py"
import torch
import torch.nn as nn

# --- Tensor basics ---
x = torch.tensor([2.0, 3.0], requires_grad=True)
y = (x[0] + x[1]) * x[0]
y.backward()
print("autograd gradient:", x.grad)  # should match [2*x0+x1, x0] = [7, 2]

# --- Verify against the hand-derived analytic gradient from Calculus and Gradients ---
def analytic_grad(x_vals):
    return torch.tensor([2 * x_vals[0] + x_vals[1], x_vals[0]])
print("hand-derived gradient:", analytic_grad(x.detach()))

# --- The backprop page's 2-layer network, reimplemented ---
class TwoLayerNet(nn.Module):
    def __init__(self, n_in, n_hidden, n_out):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.fc2 = nn.Linear(n_hidden, n_out)

    def forward(self, x):
        h = torch.sigmoid(self.fc1(x))
        return torch.sigmoid(self.fc2(h))

torch.manual_seed(0)
net = TwoLayerNet(5, 8, 1)
X = torch.randn(200, 5)
y_target = (X.sum(dim=1, keepdim=True) > 0).float()

optimizer = torch.optim.SGD(net.parameters(), lr=1.0)
for step in range(2000):
    optimizer.zero_grad()  # required - grads accumulate otherwise
    pred = net(X)
    loss = ((pred - y_target) ** 2).mean()
    loss.backward()
    optimizer.step()
    if step % 1000 == 0:
        print(f"step {step}: loss={loss.item():.4f}")

# --- The missing zero_grad() bug, demonstrated ---
net2 = TwoLayerNet(5, 8, 1)
optimizer2 = torch.optim.SGD(net2.parameters(), lr=1.0)
losses_no_zero_grad = []
for step in range(50):
    pred = net2(X)
    loss = ((pred - y_target) ** 2).mean()
    loss.backward()  # missing optimizer2.zero_grad() before this
    optimizer2.step()
    losses_no_zero_grad.append(loss.item())
print("\nwithout zero_grad(), loss over first 5 steps:", [f"{l:.3f}" for l in losses_no_zero_grad[:5]],
      "\n  <- gradients accumulate across steps, producing an incorrect, growing effective update")
```

## See also

- [Backpropagation](./backpropagation.md) — the manual algorithm autograd automates and generalises.
- [Training Loop Anatomy](./training-loop-anatomy.md) — the standard structure every PyTorch training script follows.
