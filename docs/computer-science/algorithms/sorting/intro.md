---
id: sorting-intro
title: Sorting Algorithms — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, sorting]
---

# Sorting Algorithms — Overview

## Overview

Sorting is the most-studied problem in the field, and not because arranging things in order is
especially useful on its own. It is studied because it is the smallest problem where every major
algorithmic idea shows up in a form you can hold in your head: incremental construction, divide and
conquer, using a data structure to do the work, and the difference between average and worst case.

You will almost never write one. You will constantly need to know which one your language calls, and
why it made that choice.

## In This Section

**The quadratic sorts** — simple, in-place, and genuinely useful at small sizes:

- **[Bubble Sort](./bubble-sort.md)** — the one everybody learns and nobody should use.
- **[Selection Sort](./selection-sort.md)** — minimises writes, at the cost of never finishing early.
- **[Insertion Sort](./insertion-sort.md)** — the one that is actually used, inside faster sorts.

**The efficient sorts** — O(n log n), and the basis of every real implementation:

- **[Mergesort](./mergesort.md)** — stable, predictable, needs O(n) extra space.
- **[Quicksort](./quicksort.md)** — in place and usually fastest, with a quadratic worst case.
- **[Heapsort](./heapsort.md)** — worst-case O(n log n) in place, but poor locality.

**Then the decision itself:**

- **[Choosing a Sort](./choosing-a-sort.md)** — what real standard libraries do, and why.

## At a Glance

| Algorithm | Best | Average | Worst | Space | Stable | Adaptive |
|---|---|---|---|---|---|---|
| [Bubble](./bubble-sort.md) | O(n) | O(n²) | O(n²) | O(1) | Yes | Yes |
| [Selection](./selection-sort.md) | O(n²) | O(n²) | O(n²) | O(1) | No | No |
| [Insertion](./insertion-sort.md) | O(n) | O(n²) | O(n²) | O(1) | Yes | Yes |
| [Mergesort](./mergesort.md) | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes | No |
| [Quicksort](./quicksort.md) | O(n log n) | O(n log n) | O(n²) | O(log n) | No | No |
| [Heapsort](./heapsort.md) | O(n log n) | O(n log n) | O(n log n) | O(1) | No | No |

Two columns there matter more than most treatments admit:

- **Stable** — equal elements keep their original relative order. This is what lets you sort by one
  key, then another, and have the first act as a tie-breaker. Losing stability silently changes
  results in ways tests rarely catch.
- **Adaptive** — runs faster on data that is already partly ordered. Real data very often is, and
  this is why [Timsort](./choosing-a-sort.md) exists.

## The Lower Bound

No comparison-based sort can beat **Ω(n log n)** in the worst case. The argument is short: there are
`n!` possible orderings, each comparison yields one bit, and distinguishing `n!` cases needs at least
`log₂(n!) ≈ n log₂ n` bits.

This bounds a *model*, not the problem. Counting sort, radix sort and bucket sort look at the values
themselves rather than only comparing them, and reach O(n) — by assuming the keys are integers in a
bounded range, or fixed-width. Every escape from the bound is paid for with an assumption about the
data.

## Related Pages

- [Complexity & Analysis](../complexity/intro.md) — where the lower-bound argument is developed.
- [Divide & Conquer](../problem-solving-patterns/divide-and-conquer.md) — the pattern behind mergesort and quicksort.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the structure heapsort is built on.
