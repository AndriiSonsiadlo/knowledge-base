---
id: datasets-and-dataloaders
title: Datasets and DataLoaders
sidebar_label: Datasets & DataLoaders
sidebar_position: 13
tags: [deep-learning, pytorch, data, dataloader]
---

# Datasets and DataLoaders

A GPU can process a batch of data in milliseconds — and then sit idle for seconds waiting for the next batch to be loaded and preprocessed from disk. The input pipeline is where a surprising fraction of real training time actually goes, and getting it wrong silently turns an expensive GPU into an expensive way to wait for a CPU.

:::info[Key idea]
The Dataset says how to get one example; the DataLoader says how to get a batch of them efficiently, in parallel, forever.
:::

## Dataset: __len__ and __getitem__

A PyTorch `Dataset` subclass implements exactly two methods: `__len__` (how many examples exist) and `__getitem__(idx)` (return the example at that index, typically `(features, label)`). Everything else — batching, shuffling, parallel loading — is the `DataLoader`'s job, not the `Dataset`'s.

## Map-style vs. iterable-style

**Map-style** datasets (the default, implementing `__getitem__`) support random access by index — the standard choice when the full dataset fits in accessible storage. **Iterable-style** datasets implement `__iter__` instead, yielding examples in sequence without requiring indexed access — necessary for data streamed from a source too large or too dynamic to index directly (a live feed, a dataset larger than local disk).

## DataLoader: the key arguments

- `batch_size`: examples per batch.
- `shuffle`: randomise example order each epoch (essential for training, must be `False` for validation/test to keep results comparable across runs).
- `num_workers`: number of background processes prefetching and preprocessing data in parallel with the main training loop.
- `pin_memory`: allocates batches in page-locked memory, speeding up the CPU-to-GPU transfer.
- `drop_last`: whether to drop a final, incomplete batch (matters when batch size affects an operation like BatchNorm).

## collate_fn, and when you must write one

The default `collate_fn` stacks a list of `__getitem__` outputs into a batched tensor, which requires every example to already be the same shape. For variable-length data (text sequences, unpadded audio), a custom `collate_fn` is required to pad each batch to a common length *before* stacking — without one, the default collation simply errors on shape mismatch.

## Transforms, and applying them per sample

Transforms (resizing, normalisation, augmentation) are typically applied inside `__getitem__`, one example at a time, right before that example is returned — this naturally works with the parallel `num_workers`, since each worker process applies transforms independently without any shared-state coordination needed.

## Train vs. validation transforms

Augmentation (random crop, flip, colour jitter — see [Data Augmentation](../04-computer-vision/data-augmentation.md)) belongs only in the *training* dataset's transform pipeline. Applying random augmentation to validation or test data introduces noise into the very numbers used to judge the model, making evaluation non-reproducible run to run.

## Samplers, including weighted sampling

A `Sampler` controls *which* indices get drawn and in what order — the default is either sequential or shuffled, but a `WeightedRandomSampler` can oversample a rare class directly at the data-loading level, an alternative to loss-level class weighting from [Imbalanced Data](../01-classical-ml/imbalanced-data.md).

## Reproducibility: seeding workers

Each `num_workers` process gets its own random state — if not explicitly seeded (via a `worker_init_fn`), different runs of "the same" training script can see different augmentation randomness per worker, undermining exact reproducibility even when the main process's seed is fixed (see [Reproducibility](../07-production-mlops/reproducibility.md)).

## Diagnosing an input-bound training loop

If GPU utilisation (checked via `nvidia-smi` or a profiler) sits well below 100% during training, the bottleneck is very likely the data pipeline, not the model — the fix is almost always increasing `num_workers`, adding `pin_memory=True`, or simplifying expensive per-example transforms, not changing anything about the model itself.

## Memory-mapped and streaming datasets

For datasets too large to fit in RAM, memory-mapped files (loading only the requested slice from disk on demand) or fully streaming iterable datasets (never materialising the whole dataset at once) let training proceed without requiring the entire dataset to be resident in memory simultaneously.

## Code: custom Dataset, custom collate_fn, num_workers timing

```python title="datasets_dataloaders_demo.py"
import time
import torch
from torch.utils.data import Dataset, DataLoader

class SyntheticSequenceDataset(Dataset):
    """Variable-length sequences - requires a custom collate_fn."""
    def __init__(self, n_samples=500):
        self.data = [torch.randn(torch.randint(5, 20, (1,)).item(), 8) for _ in range(n_samples)]
        self.labels = torch.randint(0, 2, (n_samples,))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

def pad_collate(batch):
    sequences, labels = zip(*batch)
    max_len = max(seq.shape[0] for seq in sequences)
    padded = torch.zeros(len(sequences), max_len, sequences[0].shape[1])
    for i, seq in enumerate(sequences):
        padded[i, :seq.shape[0]] = seq
    return padded, torch.stack(labels)

dataset = SyntheticSequenceDataset()
loader = DataLoader(dataset, batch_size=16, shuffle=True, collate_fn=pad_collate)
batch_x, batch_y = next(iter(loader))
print("padded batch shape (variable-length sequences, now uniform):", batch_x.shape)

# --- Timing comparison: num_workers=0 vs a parallel loader ---
class SlowDataset(Dataset):
    """Simulates an expensive per-example transform (e.g. image decode + augment)."""
    def __len__(self): return 200
    def __getitem__(self, idx):
        time.sleep(0.005)  # simulate real I/O + transform cost
        return torch.randn(3, 64, 64), 0

for num_workers in [0, 4]:
    slow_loader = DataLoader(SlowDataset(), batch_size=16, num_workers=num_workers)
    start = time.perf_counter()
    for _ in slow_loader:
        pass
    elapsed = time.perf_counter() - start
    print(f"num_workers={num_workers}: {elapsed:.2f}s total")
```

`num_workers=0` should take noticeably longer than `num_workers=4` on the artificially slowed dataset — the input-bound scenario, reproduced directly, and fixed by parallel loading.

## See also

- [Training Loop Anatomy](./training-loop-anatomy.md) — where the DataLoader plugs into the full training loop.
- [Data Preprocessing and Features](../00-foundations/data-preprocessing-and-features.md) — the transform logic typically applied inside `__getitem__`.
