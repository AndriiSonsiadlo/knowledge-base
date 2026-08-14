---
id: bank-conflicts
title: Shared Memory Bank Conflicts
sidebar_label: Bank Conflicts
sidebar_position: 4
tags: [gpu, cuda, memory, bank-conflicts]
---

# Shared Memory Bank Conflicts

Shared memory earns its speed by serving a whole warp in one cycle, but that promise depends on the warp's 32 addresses landing in 32 different pieces of hardware. When they don't, shared memory — normally close behind register speed — degrades to a fraction of it, and the kernel doesn't fail, it just quietly runs slower with no compiler warning to explain why.

## 32 banks

Shared memory is physically organized into **32 banks**, each 4 bytes wide, interleaved across consecutive addresses: bank = `(address / 4) % 32`. This layout exists so that 32 threads accessing 32 consecutive 4-byte words each land in a different bank and can all be serviced in the same cycle — the shared-memory analog of a coalesced global access, though the mechanism (banks, not sectors) is different, per the [glossary entry](../00-overview/glossary.md#bank-conflict).

## What counts as a conflict

Threads in a warp hitting **distinct banks** are serviced in one cycle, no matter how those addresses are otherwise scattered within the 32-bank space. Threads hitting **distinct addresses within the same bank** cannot be serviced together: N threads colliding on one bank serialize into N sequential cycles, one address at a time. This is a **bank conflict**, and the [glossary](../00-overview/glossary.md#bank-conflict) entry for it applies the term specifically to this same-bank, different-address case.

## The broadcast exception

There's one collision that isn't a conflict at all: if every thread in the warp reads the exact **same address**, the hardware detects it and serves all 32 threads from a single fetch in one cycle — a **broadcast**, not a conflict. The distinction is address, not bank: same bank, same address is free; same bank, different addresses is N-way serialized.

## The padding fix

The canonical conflict shows up in a shared-memory tile accessed column-wise. Take a square tile:

```cpp
__shared__ float tile[32][32];
```

`tile` is laid out row-major, so `tile[row][col]` is at offset `row * 32 + col` (in words). Reading `tile[threadIdx.x][k]` for a fixed `k` across a warp — a column read, with `threadIdx.x` selecting the row — means thread `t`'s address is `t * 32 + k`. Bank is `(t * 32 + k) / 4 % 32`; since `32` is a multiple of `32`, every thread's `t * 32` term contributes a multiple of 32 to the address, and dividing by 4 and reducing mod 32 collapses that whole term to the same bank for every `t`. All 32 threads land in bank `(k / 4) % 32` — a full 32-way conflict, serializing what should be one cycle into 32.

Padding the row by one extra word breaks the arithmetic:

```cpp
__shared__ float tile[32][33];
```

Now `tile[row][col]` is at offset `row * 33 + col`. Thread `t`'s address for the same column read is `t * 33 + k`. Because 33 is not a multiple of 32, each successive `t` shifts the bank by one relative to the last (`33 mod 32 == 1`), so 32 threads land in 32 distinct banks — the conflict is gone, at the cost of one wasted word per row (32 × 4 bytes of padding per tile).

## Swizzling

Padding wastes shared memory — one word per row, which adds up when shared memory is the binding occupancy limiter. An **XOR swizzle** achieves the same bank-spreading effect without allocating any extra space, by permuting the column index instead of shifting the row stride:

```cpp
// column index swizzled instead of padded
int col = threadIdx.x ^ threadIdx.y;
```

Indexing `tile[threadIdx.y][col]` into an *unpadded* `` `tile[32][32]` `` with this swizzled column spreads a warp's accesses across distinct banks the same way padding does, but keeps every row exactly 32 words wide. The tradeoff is complexity: the swizzle function has to be inverted consistently everywhere the tile is written and read, whereas padding only changes a declaration. Reach for swizzling specifically when shared memory is the occupancy limiter and the wasted padding column would drop a block below the next occupancy tier; otherwise padding is simpler and just as fast.

## Measuring conflicts

:::tip[Nsight Compute reports conflicts directly]
The `l1tex__data_bank_conflicts_pipe_lsu_mem_shared` metric counts shared-memory bank conflicts directly. A nonzero value on a tiled kernel almost always means a missing pad (or a swizzle that isn't actually spreading banks the way it's meant to) — check the tile's declared stride before looking anywhere else.
:::

## See also

- [Shared Memory](./shared-memory.md) — allocation and the synchronization rule bank conflicts assume is already in place.
- [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) — applying the padded-tile pattern in a full tiled kernel.
- [Matrix Transpose](../13-applied-kernels-and-patterns/matrix-transpose.md) — the canonical kernel where a column-wise shared-memory read causes this exact conflict.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
