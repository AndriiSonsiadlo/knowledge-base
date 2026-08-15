---
id: distributed-training
title: Distributed Training
sidebar_label: Distributed Training
sidebar_position: 16
tags: [deep-learning, distributed, ddp, fsdp, scaling]
---

# Distributed Training

One GPU stops being enough for three distinct reasons — training is too slow, the model doesn't fit in memory, or the batch size that would actually converge well doesn't fit either — and each has a genuinely different fix. Reaching for the wrong one wastes both engineering effort and compute budget.

:::info[Key idea]
Pick the parallelism that matches your bottleneck — data parallel when the dataset is the problem, model parallel when the model does not fit.
:::

<Figure
  src="/img/ml/deep/parallelism-strategies.png"
  alt="Data parallelism replicating the model across GPUs, pipeline parallelism splitting it by layer, and tensor parallelism splitting individual matrices"
  caption="Three ways to split training across devices. Data parallel is the simplest and the default; the other two exist for when the model itself no longer fits on one GPU, and both pay for it in communication."
/>

## The three bottlenecks

**Too slow**: the model fits fine on one GPU, but training would take too long — the fix is more GPUs doing the same work in parallel (data parallelism). **Model too large**: the model's parameters, gradients, and optimiser state don't fit in one GPU's memory at all — the fix is splitting the model itself across GPUs (model parallelism). **Batch too small**: memory constraints force an uncomfortably small per-GPU batch — multiple GPUs can combine into a larger effective batch even if each individually stays small.

## Data parallelism

Replicate the *entire* model on every GPU; split each batch across GPUs; each GPU computes gradients on its shard independently; synchronise (average) gradients across all GPUs before each update, so every replica stays identical.

## DataParallel vs. DistributedDataParallel

`DataParallel` (single-process, multi-GPU) is simpler to set up but suffers from a Python GIL bottleneck and uneven GPU load (one GPU gathers all outputs) — deprecated in practice in favour of `DistributedDataParallel` (one process per GPU, communicating via a proper distributed backend), which scales far better and is the standard choice for any serious multi-GPU training today.

## The all-reduce gradient synchronisation step

After each GPU computes its local gradients, an **all-reduce** operation sums (and averages) them across all participating GPUs, and every GPU ends the operation holding the identical averaged result — implemented efficiently as a ring or tree communication pattern rather than a naive gather-to-one-then-broadcast, which would bottleneck on a single GPU's bandwidth.

## DistributedSampler and the duplicate-data bug

Without a `DistributedSampler`, every GPU's DataLoader would independently shuffle and iterate the *full* dataset — meaning each GPU effectively re-processes all the data every epoch instead of its own shard, silently multiplying both training time and (through correlated redundant gradients) potentially destabilising convergence. `DistributedSampler` partitions the dataset so each GPU sees a distinct, non-overlapping shard per epoch.

## Scaling the learning rate with effective batch size

If $N$ GPUs each process a batch of size $B$, the *effective* batch size is $NB$ — the linear scaling rule suggests multiplying the single-GPU learning rate by roughly $N$ as well, since a larger batch produces a lower-variance gradient estimate that can tolerate (and typically benefits from) a proportionally larger step; this is almost always paired with the warmup schedule from [Learning Rate Schedules](./learning-rate-schedules.md) to avoid early instability at the larger effective rate.

| Symbol | Meaning |
|---|---|
| $N$ | number of GPUs (or processes) |
| $B$ | per-GPU batch size |
| $NB$ | effective batch size across all GPUs |

## Model parallelism: pipeline and tensor

**Pipeline parallelism**: split the model's *layers* across GPUs — GPU 1 holds layers 1–10, GPU 2 holds layers 11–20, and activations flow between GPUs like an assembly line (with "bubble" idle time to manage). **Tensor parallelism**: split individual *operations* (e.g. one very large matrix multiply) across GPUs, each computing a portion of a single layer's computation — used when even one layer is too large for one GPU.

## ZeRO/FSDP: sharding parameters, gradients, optimizer states

Rather than replicating the *entire* model on every GPU (as in plain data parallelism), ZeRO (Zero Redundancy Optimizer) and FSDP (Fully Sharded Data Parallel) shard the parameters, gradients, and optimiser states themselves across GPUs — each GPU holds only a fraction of each, gathering the pieces it needs just before they're used and releasing them afterward. This lets significantly larger models train with data-parallel-style simplicity, at the cost of additional communication for the gather/release steps.

## Communication cost as the real ceiling

Every synchronisation step (all-reduce, parameter gathering) requires network communication between GPUs, and network bandwidth is almost always far slower than a GPU's internal memory bandwidth — beyond some point, adding more GPUs increases communication overhead faster than it increases useful compute, which is why distributed training scaling is sublinear in practice, not the naive "N GPUs = N times faster" intuition.

## When distributed training is not worth the complexity

If a single GPU (or a single machine's GPUs via simple `DataParallel`-style setups) can complete training in an acceptable time and the model comfortably fits in memory, the added complexity, debugging difficulty, and communication overhead of full distributed training frequently aren't worth it — reach for it when the bottleneck genuinely requires it, not by default.

## Selection table

| Bottleneck | Reach for |
|---|---|
| Training too slow, model fits fine | DistributedDataParallel |
| Model too large for one GPU | pipeline or tensor parallelism, or FSDP |
| Need a larger effective batch, memory-constrained per GPU | gradient accumulation (single GPU) or data parallelism (multi-GPU) |
| Very large model, want data-parallel-style simplicity | FSDP / ZeRO |

## Code: minimal single-node multi-GPU DDP script

```python title="ddp_train.py"
"""
Launch with: torchrun --nproc_per_node=NUM_GPUS ddp_train.py
Annotated to be readable without access to multiple GPUs.
"""
import os
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import TensorDataset, DataLoader, DistributedSampler

def main():
    dist.init_process_group(backend="nccl")  # or "gloo" for CPU-only testing
    rank = dist.get_rank()
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)

    model = nn.Sequential(nn.Linear(20, 64), nn.ReLU(), nn.Linear(64, 1)).to(local_rank)
    model = DDP(model, device_ids=[local_rank])
    optimizer = torch.optim.Adam(model.parameters())

    X = torch.randn(10000, 20)
    y = torch.randn(10000, 1)
    dataset = TensorDataset(X, y)
    sampler = DistributedSampler(dataset)  # each rank sees a distinct shard, no duplication
    loader = DataLoader(dataset, batch_size=64, sampler=sampler)

    for epoch in range(5):
        sampler.set_epoch(epoch)  # reshuffles differently each epoch across all ranks
        for x_batch, y_batch in loader:
            x_batch, y_batch = x_batch.to(local_rank), y_batch.to(local_rank)
            optimizer.zero_grad()
            loss = ((model(x_batch) - y_batch) ** 2).mean()
            loss.backward()  # DDP automatically all-reduces gradients here
            optimizer.step()

        if rank == 0:  # checkpoint only from rank 0, avoiding redundant writes
            torch.save(model.module.state_dict(), "checkpoint.pt")

    dist.destroy_process_group()

if __name__ == "__main__":
    main()
```

## See also

- [GPU Training and Mixed Precision](./gpu-training-and-mixed-precision.md) — single-GPU efficiency, the prerequisite before scaling out.
- [Model Capacity and Scaling](./model-capacity-and-scaling.md) — the compute/data/parameter trade-offs distributed training exists to serve.
