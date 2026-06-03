---
id: debugging-neural-networks
title: Debugging Neural Networks
sidebar_label: Debugging Neural Networks
sidebar_position: 17
tags: [deep-learning, debugging, training, diagnostics]
---

# Debugging Neural Networks

The loss isn't going down, and unlike a typical software bug, there's no stack trace pointing at the problem — the model runs, produces numbers, and those numbers are simply wrong in a way Python's error messages have nothing to say about. The fix is to debug in a fixed order, because each step rules out an entire category of causes before moving to the next.

:::info[Key idea]
Debug in a fixed order — shapes, then overfit-one-batch, then learning rate, then data — because each step rules out a whole class of causes.
:::

## The ordered checklist, and why order matters

Each step below assumes the previous ones passed. Skipping ahead means a real bug in an earlier layer can masquerade as a symptom the later step is looking for — chasing a learning-rate problem when the actual bug is a data-loading error wastes time solving the wrong thing.

## Step 1: shapes and dtypes

Print (or assert) the shape and dtype of every tensor at every stage of the forward pass. The overwhelming majority of "the model isn't learning" reports trace back to a silent shape mismatch that broadcast into something *syntactically* valid but *semantically* wrong — see [Linear Algebra](../00-foundations/linear-algebra.md)'s broadcasting bug and [Forward Pass and Computational Graphs](./forward-pass-and-computational-graphs.md)'s shape-assertion habit.

## Step 2: overfit a single batch to zero loss

Take one small batch (8–16 examples), disable any regularisation (dropout, weight decay), and train on *just that batch*, repeatedly, for many steps. A correctly-implemented model and loss should be able to drive the loss to near-zero on this tiny, memorisable batch. **If it cannot, the bug is in the model or the loss function, not the data or the learning rate** — this single test rules out an enormous space of possible causes in one shot.

## Step 3: learning-rate sanity

Once the model can overfit one batch, run the LR range test from [Learning Rate Schedules](./learning-rate-schedules.md) on the full dataset — a learning rate that's wildly wrong (too high or too low) is the next most common cause of a model that trains on one batch but fails to converge on the full dataset.

## Step 4: inspect the data you are actually feeding

Render or print several *actual* batches right before they enter the model — not the raw data on disk, but the tensor after every transform has been applied. Misaligned labels, an image displayed with the wrong colour channel order, or text tokenised incorrectly are all invisible unless you look at exactly what the model sees, not what you assume it sees.

## Step 5: gradient norms per layer

Log $\|\nabla_{W^{[l]}} L\|$ for every layer during a few training steps — vanishing or exploding norms (see [Vanishing and Exploding Gradients](./vanishing-and-exploding-gradients.md)) are visible directly in this log, well before the loss curve itself makes the problem obvious.

## Step 6: label and target alignment

Confirm the loss function's expected input format actually matches what the model outputs and what the labels represent — a shockingly common bug is passing raw logits to a loss expecting probabilities (or vice versa), or having a label encoding off by one class index.

## The loss-curve catalogue

| Pattern | Likely cause |
|---|---|
| Flat from the very first step | learning rate far too low, or a genuine implementation bug (check step 2) |
| Spikes upward occasionally, then recovers | learning rate slightly too high, or a rare batch with extreme values — try gradient clipping |
| Diverges (grows without bound) | learning rate far too high, or an exploding-gradient case |
| Noisy, no clear downward trend | learning rate too high for the batch size, or batch size too small |
| Train loss decreasing, validation loss flat or rising from early on | overfitting, or a train/validation data mismatch — check step 4 on both splits |

## NaN hunting

Common sources, roughly in order of frequency: `log(0)` from a probability that reached exactly zero (add a small epsilon, or use the numerically-stable log-softmax rather than log(softmax(...))); division by a variance that reached zero; exploding gradients (see [Vanishing and Exploding Gradients](./vanishing-and-exploding-gradients.md)); and occasionally a genuinely bad input value (an unhandled `inf` or `NaN` already present in the raw data, silently propagated forward).

## Reproducibility while debugging

Fix all random seeds during debugging (see [Reproducibility](../07-production-mlops/reproducibility.md)) — chasing an intermittent-looking bug that's actually just run-to-run randomness wastes enormous time; a fixed seed makes a bug either reliably reproduce or reliably disappear, which is itself useful diagnostic information.

## The tools

**Forward/backward hooks**: attach functions that fire automatically when a specific layer's forward or backward pass runs, letting you inspect activations/gradients without modifying the model's `forward` method. **Model summaries** (e.g. `torchinfo`): print every layer's output shape and parameter count in one pass, catching shape issues before training even starts. **The profiler**: identifies which specific operations consume the most time or memory, useful for the performance side of debugging covered in [GPU Training and Mixed Precision](./gpu-training-and-mixed-precision.md).

## Code: overfit-one-batch as a reusable function, hooks, and reproducing broken curves

```python title="debugging_demo.py"
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

def overfit_one_batch(model, x, y, loss_fn, steps=200, lr=0.01):
    """The single most useful debugging test: can this model memorise 16 examples?"""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    for step in range(steps):
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
    final_loss = loss.item()
    print(f"overfit-one-batch final loss: {final_loss:.6f} ({'PASS' if final_loss < 0.01 else 'FAIL - bug in model/loss'})")
    return final_loss

torch.manual_seed(0)
model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 1))
x, y = torch.randn(16, 10), torch.randn(16, 1)
overfit_one_batch(model, x, y, nn.MSELoss())

# --- Forward hook logging per-layer activation statistics ---
def make_hook(name):
    def hook(module, input, output):
        print(f"{name}: output mean={output.mean().item():.4f}, std={output.std().item():.4f}")
    return hook

for name, layer in model.named_children():
    layer.register_forward_hook(make_hook(name))
_ = model(x[:2])

# --- Reproducing broken loss curves on purpose, for the catalogue above ---
def train_and_get_losses(lr, steps=100, inject_nan_step=None):
    m = nn.Linear(10, 1)
    opt = torch.optim.SGD(m.parameters(), lr=lr)
    losses = []
    for step in range(steps):
        opt.zero_grad()
        pred = m(x)
        if inject_nan_step and step == inject_nan_step:
            pred = pred * float("inf")  # deliberately trigger NaN propagation
        loss = ((pred - y) ** 2).mean()
        loss.backward()
        opt.step()
        losses.append(loss.item())
    return losses

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(train_and_get_losses(lr=1e-6)); axes[0].set_title("flat (lr too low)")
axes[1].plot(train_and_get_losses(lr=5.0)); axes[1].set_title("diverging (lr too high)")
axes[2].plot(train_and_get_losses(lr=0.01, inject_nan_step=50)); axes[2].set_title("NaN injected at step 50")
plt.savefig("loss_curve_catalogue.png")
```

## See also

- [Training Loop Anatomy](./training-loop-anatomy.md) — the six classic bugs this systematic process is designed to catch.
- [Vanishing and Exploding Gradients](./vanishing-and-exploding-gradients.md) — the gradient-norm measurement this page's step 5 relies on.
