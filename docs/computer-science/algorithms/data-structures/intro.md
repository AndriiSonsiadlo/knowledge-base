---
id: data-structures-intro
title: Data Structures — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, data-structures]
---

# Data Structures — Overview

A data structure is a decision about **which operations you want to be cheap**. There is no structure
that makes everything fast; each one buys speed on some operations by giving it up on others, and
picking well means knowing which operations your code actually performs most.

Every page in this folder answers the same question from a different direction — "what am I doing to
this collection most often, and what does that cost?" — for one specific shape of data.

## In This Section

- **[Arrays & Dynamic Arrays](./arrays.md)** — contiguous memory, $O(1)$ indexing, and the amortized cost of growth.
- **[Linked Lists](./linked-lists.md)** — $O(1)$ splicing, and why they lose to arrays more often than textbooks suggest.
- **[Stacks & Queues](./stacks-and-queues.md)** — restricted access disciplines, LIFO and FIFO.
- **[Hash Tables](./hash-tables.md)** — expected $O(1)$ lookup, collisions, and load factor.
- **[Trees & Binary Search Trees](./trees.md)** — hierarchical structure and ordered traversal.
- **[Balanced Trees](./balanced-trees.md)** — AVL, red-black and B-trees: keeping depth logarithmic.
- **[Heaps & Priority Queues](./heaps.md)** — cheap access to the smallest or largest element.
- **[Graphs](./graphs.md)** — representing arbitrary relationships, and the cost of each representation.
- **[Union-Find](./union-find.md)** — "are these two things in the same group?", with groups that only merge.
- **[Tries](./tries.md)** — keying by position instead of by comparison, for prefix queries.
- **[Segment Trees & Fenwick Trees](./segment-trees-and-fenwick.md)** — range queries and range updates in $O(\log n)$.
- **[Deques & Ring Buffers](./deques-and-ring-buffers.md)** — $O(1)$ at both ends, and the fixed-capacity variant that never allocates.
- **[Probabilistic Data Structures](./probabilistic-structures.md)** — trading a small, bounded error for sublinear space.
- **[LRU & LFU Caches](./lru-and-lfu-caches.md)** — the hash-table-plus-list pattern that makes eviction $O(1)$.
- **[Cheat Sheet](./cheat-sheet.md)** — every bound in this folder on one page, for lookup rather than learning.

## Complexity at a Glance

Average case, with worst case in parentheses where it differs materially:

| Structure | Access | Search | Insert | Delete | Space |
|---|---|---|---|---|---|
| Array | $O(1)$ | $O(n)$ | $O(n)$ | $O(n)$ | $O(n)$ |
| Dynamic array | $O(1)$ | $O(n)$ | $O(1)$ amortized at end | $O(n)$ | $O(n)$ |
| Singly linked list | $O(n)$ | $O(n)$ | $O(1)$ at a known position | $O(1)$ at a known position | $O(n)$ |
| Stack / Queue | $O(n)$ | $O(n)$ | $O(1)$ | $O(1)$ | $O(n)$ |
| Hash table | — | $O(1)$ avg ($O(n)$ worst) | $O(1)$ avg ($O(n)$ worst) | $O(1)$ avg ($O(n)$ worst) | $O(n)$ |
| Binary search tree | $O(\log n)$ avg ($O(n)$ worst) | $O(\log n)$ avg ($O(n)$ worst) | $O(\log n)$ avg ($O(n)$ worst) | $O(\log n)$ avg ($O(n)$ worst) | $O(n)$ |
| Balanced BST | $O(\log n)$ worst | $O(\log n)$ worst | $O(\log n)$ worst | $O(\log n)$ worst | $O(n)$ |
| Binary heap | $O(1)$ worst for min/max | $O(n)$ worst | $O(\log n)$ worst | $O(\log n)$ worst | $O(n)$ |
| Union-find (both optimisations) | n/a | $O(\alpha(n))$ amortized | n/a | n/a | $O(n)$ |

:::warning[This table lies by omission]
It counts *operations*, treating every memory access as equally expensive. On real hardware they are
not: a sequential array scan can outrun a linked-list traversal of the same length by an order of
magnitude, because one prefetches perfectly and the other chases pointers into
[cache](../../memory-hierarchy/cpu-caches.md) misses. Use the table to rule structures out, then
measure. The worked trace below makes that gap concrete for one workload.
:::

## How to Choose

| If you mostly… | Use | Because |
|---|---|---|
| Index by position, iterate in order | Dynamic array | $O(1)$ worst-case access, contiguous and cache-friendly |
| Look things up by key, order doesn't matter | Hash table | $O(1)$ expected lookup, no ordering maintained |
| Need keys in sorted order, or range queries | Balanced BST | $O(\log n)$ worst case with ordered traversal |
| Repeatedly take the smallest/largest | Heap | $O(1)$ worst-case peek, $O(\log n)$ worst-case extract |
| Insert and remove at both ends only | [Deque](./deques-and-ring-buffers.md) | $O(1)$ worst case at either end |
| Ask "same group?" as edges arrive over time | [Union-find](./union-find.md) | $O(\alpha(n))$ amortized, far cheaper than a traversal per query |
| Match or answer queries on prefixes of strings | [Trie](./tries.md) | Cost is key length, not collection size |
| Answer range-sum/range-min queries with updates | [Segment tree / Fenwick](./segment-trees-and-fenwick.md) | $O(\log n)$ worst case for both query and update |
| Need an approximate answer over huge or streaming data | [Probabilistic structure](./probabilistic-structures.md) | Sublinear space, for a bounded error rate |
| Model relationships between entities | Graph | Everything else here is a special case of this |

## Mechanism

### One workload, three structures: 1,000 lookups

Suppose a collection already holds `n = 10,000` items, none of them ordered by key, and the workload
is 1,000 lookups by value. This is deliberately the least favorable case for each structure — no
sorting to exploit, no cache warmed by a prior pass — to expose what "worst case" versus "expected
case" actually costs in aggregate:

```text
1,000 lookups against n = 10,000 already-stored items, unsorted, worst-case placement of the target

structure          cost per lookup         total work                     why
unsorted array     O(n) worst              1,000 × 10,000 = 10,000,000    every miss scans the whole array;
                                            comparisons                    prefetched, so each comparison is
                                                                           ~1 ns on modern hardware
singly linked list O(n) worst              1,000 × 10,000 = 10,000,000    the same comparison count, but each
                                            comparisons                    step is a pointer-chasing dependent
                                                                           load — no prefetch, ~50-100 ns each
                                                                           on a cache miss
hash table         O(1) expected,          ~1,000 × (1 / (1 - α)) probes  expected probes under uniform
                   O(n) worst              ≈ 3,000 at α = 0.66            hashing is 1/(1-α) for open
                                                                           addressing (CLRS 4th ed. §11.4,
                                                                           Theorem 11.6); degrades to the
                                                                           array's O(n) if every key collides
```

The array and the list do an *identical* number of comparisons — the asymptotic bound is the same
$O(n)$ per lookup for both. What differs is the wall-clock cost of each comparison: the array's scan is
a sequence of independent, prefetchable loads, while the list's traversal is a chain of dependent loads
that the CPU cannot start until the previous one lands. On real hardware the array search of ten
thousand elements can finish before the linked-list search has resolved a tenth of its pointer chases,
even though both perform the same 10,000,000 comparisons over the full workload. The hash table wins
this workload by a different mechanism entirely — it does not compare against most of the collection at
all, expected case.

None of this makes the array or the list a bad structure; it makes them the wrong structure for
*this* workload. A workload of 1,000 *insertions at the front*, or 1,000 *sequential scans*, would
rank these three differently — which is the entire argument for reading the rest of this folder rather
than defaulting to one structure everywhere.

The sixteen pages that follow each fix one axis of this trade-off in a different way: some change what
is stored (a count instead of a value, in
[probabilistic structures](./probabilistic-structures.md)), some change where comparisons happen (by
position instead of by value, in [tries](./tries.md)), and some change which operations share memory
(a hash table plus a linked list, in [LRU & LFU caches](./lru-and-lfu-caches.md)). None of them is a
free upgrade over the ones before it — every page ends with a Comparisons table naming exactly what it
gives up.

## Recall

<Recall
  invariant="No structure is uniformly fast; each one is a bet that a particular access pattern will dominate, paid for by making the opposite pattern expensive."
  costs={[
    ["array/list lookup by value, no order (worst)", "O(n)"],
    ["hash table lookup by key (expected)", "O(1)"],
    ["hash table lookup by key (worst, all keys collide)", "O(n)"],
    ["balanced BST lookup (worst)", "O(log n)"],
    ["union-find same-group query, both optimisations (amortized)", "O(α(n))"],
  ]}
  reachFor="You are choosing a structure before writing any code, and want to know which operations the choice makes cheap and which it makes expensive."
  trap="Comparing structures by asymptotic bound alone and ignoring the constant factor — an O(n) array scan and an O(n) linked-list traversal do the same number of comparisons but can differ by an order of magnitude in wall-clock time, because one is prefetchable and the other is not."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 10 ("Elementary Data
  Structures") and §11.4 ("Open addressing") — the probe-count analysis behind the 1/(1-α) figure used
  in the trace above.
- Sedgewick & Wayne, *Algorithms*, 4th ed., Ch. 1 and 3 — arrays, linked lists, and the ordered/unordered
  symbol-table implementations this folder builds on throughout.

## Related Pages

- [Complexity & Analysis](../complexity/intro.md) — the vocabulary the tables above are written in.
- [Memory Hierarchy & RAM](../../memory-hierarchy/intro.md) — why the constant factors diverge so sharply from the operation counts.
