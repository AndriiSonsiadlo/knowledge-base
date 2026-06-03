---
id: training-loop-anatomy
title: Training Loop Anatomy
sidebar_label: Training Loop Anatomy
sidebar_position: 14
tags: [deep-learning, pytorch, training, loop]
---

# Training Loop Anatomy

Every deep learning project, regardless of architecture or task, runs the same twenty-odd lines at its core: forward, compute loss, zero the gradients, backward, step. That order is not negotiable — get it wrong and training either does nothing or does something subtly incorrect, and both failure modes tend to fail quietly rather than crash loudly.

:::info[Key idea]
Forward, loss, zero_grad, backward, step — in that order, every time, and the order is not negotiable.
:::

## The canonical loop

```
for epoch in range(num_epochs):
    model.train()
    for x, y in train_loader:
        optimizer.zero_grad()
        pred = model(x)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
```

Zero the gradients *before* the backward pass (not after) — because [PyTorch Tensors and Autograd](./pytorch-tensors-and-autograd.md)'s `.backward()` accumulates into whatever `.grad` currently holds.

## model.train() vs. model.eval()

These calls don't run any computation themselves — they set a flag that changes the behaviour of specific layers. [Normalization Layers](./normalization-layers.md)'s BatchNorm switches between batch statistics (train) and running statistics (eval); [Regularization in Deep Nets](./regularization-in-deep-nets.md)'s dropout switches between masking activations (train) and passing them through unmodified (eval). Forgetting to call `.eval()` before validation silently leaves both of these in training-mode behaviour during evaluation.

## The validation loop and torch.no_grad()

```
model.eval()
with torch.no_grad():
    for x, y in val_loader:
        pred = model(x)
        val_loss += loss_fn(pred, y).item()
```

`torch.no_grad()` disables graph tracking for the whole block, saving memory and computation that would otherwise be wasted building a graph nothing will ever call `.backward()` on.

## Metric accumulation done right

Averaging per-batch metrics naively (`sum(batch_metrics) / len(batches)`) is subtly wrong when the final batch has fewer examples than the rest (a common consequence of `drop_last=False`) — the correct accumulation weights each batch's contribution by its actual example count: `sum(batch_metric * batch_size) / total_examples`.

## Checkpointing: what to save

A checkpoint that saves only `model.state_dict()` cannot correctly resume training — resuming also needs the **optimizer** state (momentum buffers, Adam's moment estimates), the **scheduler** state (where in the learning-rate schedule training was), the **epoch** number, and ideally the **RNG state** (for exact reproducibility, see [Reproducibility](../07-production-mlops/reproducibility.md)).

## Resuming correctly

Load all of the above back in, and resume the epoch counter from where it left off — resuming from epoch 0 with a restored model but a fresh optimizer effectively discards the optimizer's accumulated momentum, causing a discontinuity in training dynamics right at the resume point.

## Early stopping

Track validation loss across epochs; if it hasn't improved for a set number of epochs (`patience`), stop training and restore the checkpoint from the best epoch, not the most recent one.

## Gradient accumulation for large effective batch sizes

When a desired batch size doesn't fit in GPU memory, split it into smaller "micro-batches," accumulate their gradients (call `.backward()` on each without an intervening `zero_grad()` or `step()`), and only call `optimizer.step()` once every $k$ micro-batches — mathematically equivalent to training with a $k\times$ larger batch, at the cost of $k\times$ more forward/backward passes per effective step.

## Gradient clipping placement

Clip gradients (`torch.nn.utils.clip_grad_norm_`) *after* `.backward()` but *before* `optimizer.step()` — clipping before the backward pass would have nothing to clip yet, and clipping after the step would be too late to affect that step's update.

## Logging what matters

At minimum: training loss per step or epoch, validation loss/metric per epoch, learning rate (to catch scheduler bugs), and gradient norms (to catch the vanishing/exploding symptoms from [Vanishing and Exploding Gradients](./vanishing-and-exploding-gradients.md)) — logging only the loss hides most of the useful diagnostic signal.

## The six classic bugs

| Bug | Symptom |
|---|---|
| Missing `zero_grad()` | loss decreases erratically, or the effective learning rate seems to grow over time |
| Forgetting `model.eval()` before validation | validation metrics fluctuate oddly, especially with BatchNorm/dropout |
| Loss computed on the wrong axis/dimension | loss is a suspicious constant, or shapes silently broadcast incorrectly |
| Shuffling validation data every epoch | can't directly compare validation metrics across epochs when doing error analysis |
| Evaluating under `torch.no_grad()`-less code paths meant for training | unnecessary memory use, occasionally a crash on large validation sets |
| Saving only `model.state_dict()` | resumed training discards optimizer momentum, causing a training discontinuity |

## Code: a complete training script with checkpointing and early stopping

```python title="training_loop_demo.py"
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

torch.manual_seed(0)
X = torch.randn(1000, 10)
y = (X.sum(dim=1) > 0).float().unsqueeze(1)
train_ds, val_ds = TensorDataset(X[:800], y[:800]), TensorDataset(X[800:], y[800:])
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)  # never shuffle validation

model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.BCELoss()

best_val_loss, patience, patience_counter = float("inf"), 5, 0

for epoch in range(50):
    model.train()
    train_loss_sum, train_n = 0.0, 0
    for x, y_batch in train_loader:
        optimizer.zero_grad()
        pred = model(x)
        loss = loss_fn(pred, y_batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)  # after backward, before step
        optimizer.step()
        train_loss_sum += loss.item() * len(x)  # weighted by batch size
        train_n += len(x)

    model.eval()
    val_loss_sum, val_n = 0.0, 0
    with torch.no_grad():
        for x, y_batch in val_loader:
            pred = model(x)
            val_loss_sum += loss_fn(pred, y_batch).item() * len(x)
            val_n += len(x)
    val_loss = val_loss_sum / val_n

    if val_loss < best_val_loss:
        best_val_loss, patience_counter = val_loss, 0
        torch.save({
            "epoch": epoch, "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(), "val_loss": val_loss,
        }, "best_checkpoint.pt")
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"early stopping at epoch {epoch}, best val_loss={best_val_loss:.4f}")
            break

    if epoch % 10 == 0:
        print(f"epoch {epoch}: train_loss={train_loss_sum/train_n:.4f}  val_loss={val_loss:.4f}")
```

## See also

- [PyTorch Tensors and Autograd](./pytorch-tensors-and-autograd.md) — the `.backward()`/`.grad` mechanics this loop relies on.
- [Debugging Neural Networks](./debugging-neural-networks.md) — the systematic process for when this loop doesn't produce a decreasing loss.
