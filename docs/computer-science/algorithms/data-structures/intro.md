---
id: data-structures-intro
title: Data Structures — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, data-structures]
---

# Data Structures — Overview

## Overview

A data structure is a decision about **which operations you want to be cheap**. There is no structure
that makes everything fast; each one buys speed on some operations by giving it up on others, and
picking well means knowing which operations your code actually performs most.

## In This Section

- **[Arrays & Dynamic Arrays](./arrays.md)** — contiguous memory, O(1) indexing, and the amortized cost of growth.
- **[Linked Lists](./linked-lists.md)** — O(1) splicing, and why they lose to arrays more often than textbooks suggest.
- **[Stacks & Queues](./stacks-and-queues.md)** — restricted access disciplines, LIFO and FIFO.
- **[Hash Tables](./hash-tables.md)** — expected O(1) lookup, collisions, and load factor.
- **[Trees & Binary Search Trees](./trees.md)** — hierarchical structure and ordered traversal.
- **[Balanced Trees](./balanced-trees.md)** — AVL, red-black, B-trees, tries: keeping depth logarithmic.
- **[Heaps & Priority Queues](./heaps.md)** — cheap access to the smallest or largest element.
- **[Graphs](./graphs.md)** — representing arbitrary relationships, and the cost of each representation.

## Complexity at a Glance

Average case, with worst case in parentheses where it differs materially:

| Structure | Access | Search | Insert | Delete | Space |
|---|---|---|---|---|---|
| Array | O(1) | O(n) | O(n) | O(n) | O(n) |
| Dynamic array | O(1) | O(n) | O(1) amortized at end | O(n) | O(n) |
| Singly linked list | O(n) | O(n) | O(1) at a known position | O(1) at a known position | O(n) |
| Stack / Queue | O(n) | O(n) | O(1) | O(1) | O(n) |
| Hash table | — | O(1) (O(n)) | O(1) (O(n)) | O(1) (O(n)) | O(n) |
| Binary search tree | O(log n) (O(n)) | O(log n) (O(n)) | O(log n) (O(n)) | O(log n) (O(n)) | O(n) |
| Balanced BST | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Binary heap | O(1) for min/max | O(n) | O(log n) | O(log n) | O(n) |

:::warning[This table lies by omission]
It counts *operations*, treating every memory access as equally expensive. On real hardware they are
not: a sequential array scan can outrun a linked-list traversal of the same length by an order of
magnitude, because one prefetches perfectly and the other chases pointers into
[cache](../../memory-hierarchy/cpu-caches.md) misses. Use the table to rule structures out, then
measure.
:::

## How to Choose

| If you mostly… | Use | Because |
|---|---|---|
| Index by position, iterate in order | Dynamic array | O(1) access, contiguous and cache-friendly |
| Look things up by key | Hash table | Expected O(1), no ordering maintained |
| Need keys in sorted order, or range queries | Balanced BST | O(log n) with ordered traversal |
| Repeatedly take the smallest/largest | Heap | O(1) peek, O(log n) extract |
| Insert and remove at both ends | Deque | O(1) at either end |
| Model relationships between entities | Graph | Everything else is a special case of this |

## Related Pages

- [Complexity & Analysis](../complexity/intro.md) — the vocabulary the table above is written in.
- [Memory Hierarchy & RAM](../../memory-hierarchy/intro.md) — why the constant factors diverge so sharply from the table.
