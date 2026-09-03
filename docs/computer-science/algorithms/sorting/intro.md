---
id: sorting-intro
title: Sorting Algorithms — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, sorting]
---

# Sorting Algorithms — Overview

Sorting is the most-studied problem in the field, and not because arranging things in order is
especially useful on its own. It is studied because it is the smallest problem where every major
algorithmic idea shows up in a form you can hold in your head: incremental construction, divide and
conquer, using a data structure to do the work, and the difference between average and worst case.

You will almost never write one. You will constantly need to know which one your language calls, and
why it made that choice.

## What "sorted" buys you, and what it costs

An unsorted collection of n items answers "is x present?" in $O(n)$ — you have to look at everything,
because any unexamined element might be the one you want. A **sorted** collection answers the same
question in $O(\log n)$ via [binary search](../searching/binary-search.md), because each comparison
eliminates half of what remains. That is the entire economic case for sorting: it turns every future
search from linear into logarithmic.

It is not free. Getting to sorted costs $O(n \log n)$ at best for a comparison-based sort — see
[the lower bound](#the-lower-bound) below — so sorting is a trade of one upfront $O(n \log n)$ payment
for many cheap $O(\log n)$ searches afterward. Sort once and search once, and you have done strictly
more work than a single $O(n)$ linear scan would have cost. Sort once and search **m** times, and the
trade wins as soon as `n log n + m log n < mn` — which for any real m greater than a small constant is
almost immediately. This is why a database builds an index (a sorted structure, or a
[hash table](../data-structures/hash-tables.md) with a different trade) once and reuses it for millions
of lookups, rather than scanning the table fresh every time. It is also why sorting data you will only
ever scan once, or search zero times, is pure waste — the upfront cost is real and it does not pay for
itself without repeated reads.

## In This Section

**The quadratic sorts** — simple, in-place, and genuinely useful at small sizes:

- **[Overview](./intro.md)** — this page: what sorting buys you, the lower bound, and the map below.
- **[Bubble Sort](./bubble-sort.md)** — the one everybody learns and nobody should use; kept for the inversion-counting argument it teaches.
- **[Selection Sort](./selection-sort.md)** — minimises writes to exactly n − 1, at the cost of never finishing early.
- **[Insertion Sort](./insertion-sort.md)** — the one that is actually used, as the base case inside faster sorts.

**The efficient comparison sorts** — $O(n \log n)$, and the basis of every real implementation:

- **[Mergesort](./mergesort.md)** — stable, predictable, needs $O(n)$ extra space.
- **[Quicksort](./quicksort.md)** — in place and usually fastest, with a quadratic worst case.
- **[Heapsort](./heapsort.md)** — worst-case $O(n \log n)$ in place, but poor cache locality.

**Sorts that escape the comparison bound**, by exploiting something known about the keys:

- **[Counting, Radix & Bucket Sort](./counting-radix-bucket-sort.md)** — $O(n)$ for bounded-range or fixed-width keys.

**Related problems that do not need a full sort:**

- **[Quickselect](./quickselect.md)** — the k-th smallest element in $O(n)$ average, without sorting anything.
- **[External & Parallel Sorting](./external-and-parallel-sorting.md)** — sorting data larger than memory, or across many cores.

**Then the decision itself:**

- **[Choosing a Sort](./choosing-a-sort.md)** — what real standard libraries do (Timsort, introsort, pdqsort), and why.
- **[Cheat Sheet](./cheat-sheet.md)** — every bound in this folder on one page, for lookup rather than learning.

## At a Glance

| Algorithm | Best | Average | Worst | Space | Stable | Adaptive |
|---|---|---|---|---|---|---|
| [Bubble](./bubble-sort.md) | $O(n)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | Yes | Yes |
| [Selection](./selection-sort.md) | $O(n^2)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | No | No |
| [Insertion](./insertion-sort.md) | $O(n)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | Yes | Yes |
| [Mergesort](./mergesort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n \log n)$ | $O(n)$ | Yes | No |
| [Quicksort](./quicksort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n^2)$ | $O(\log n)$ | No | No |
| [Heapsort](./heapsort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n \log n)$ | $O(1)$ | No | No |
| [Counting/Radix](./counting-radix-bucket-sort.md) | $O(n + k)$ | $O(n + k)$ | $O(n + k)$ | $O(n + k)$ | Yes | No |

Two columns there matter more than most treatments admit:

- **Stable** — equal elements keep their original relative order. This is what lets you sort by one
  key, then another, and have the first act as a tie-breaker. Losing stability silently changes
  results in ways tests rarely catch.
- **Adaptive** — runs faster on data that is already partly ordered. Real data very often is, and
  this is why [Timsort](./choosing-a-sort.md) exists.

## The Lower Bound

No comparison-based sort can beat **$Ω(n \log n)$** in the worst case. The argument is short: there are
`n!` possible orderings, each comparison yields one bit, and distinguishing `n!` cases needs at least
$\log_2(n!) \approx n \log_2 n$ bits.

This bounds a *model*, not the problem. Counting sort, radix sort and bucket sort look at the values
themselves rather than only comparing them, and reach $O(n)$ — by assuming the keys are integers in a
bounded range, or fixed-width. Every escape from the bound is paid for with an assumption about the
data. See [Counting, Radix & Bucket Sort](./counting-radix-bucket-sort.md) for the mechanism.

## Mechanism

### Tracing one input through the whole folder

Every page in this folder that sorts a small array traces the same input, `[5, 1, 8, 3]`, so the
algorithms are directly comparable rather than each defining its own example:

```text
input = [5, 1, 8, 3]     (3 inversions: (5,1), (5,3), (8,3))

bubble sort:     3 swaps, one per inversion, 3 passes (the last confirms no swaps remain)
selection sort:  3 swaps, one per round, regardless of which inversions they resolve
insertion sort:  shifts proportional to inversions per new key: 1 shift, 0 shifts, 2 shifts
mergesort:       splits to [5,1] and [8,3], merges each half, then merges [1,5] and [3,8]
quicksort:       Lomuto partition on pivot 3 places it at index 1: [1, 3, 8, 5], recurse on [8,5]
heapsort:        heapify to [8,3,5,1], then extract-max repeatedly: 8, then 5, then 3, then 1
result:          [1, 3, 5, 8]
```

Every algorithm reaches the same four-element output; what differs is which resource each one spends
to get there — comparisons, swaps, or extra memory — and that is exactly what each page's own trace,
Core Concepts table, and Recall card make precise.

Reading the folder in position order tells one continuous story: bubble and selection sort establish
the quadratic baseline and its two failure modes (too many swaps, or no early exit); insertion sort
shows that the *same* asymptotic class can still be the right practical choice at small n; mergesort
and quicksort show the two ways to apply divide-and-conquer to the same problem; heapsort shows a data
structure substituted in for a linear scan; counting/radix/bucket sort show what happens when the
comparison model is abandoned outright; and quickselect and external sorting show that "sort
everything" is itself often more work than the problem actually requires.

## Recall

<Recall
  invariant="Sorting trades one upfront O(n log n) comparison-based cost for turning every future search from O(n) into O(log n) — a trade that only pays off if the data is searched more than roughly log n times afterward."
  costs={[
    ["comparison-sort lower bound (worst)", "O(n log n)"],
    ["linear scan of unsorted data, per search", "O(n)"],
    ["binary search of sorted data, per search", "O(log n)"],
    ["bounded-key sorts (counting/radix, worst)", "O(n + k)"],
  ]}
  reachFor="You are about to search the same collection more than a handful of times, or you need a total order for its own sake (deduplication, merging, reporting)."
  trap="Sorting data that will only be scanned once. The O(n log n) upfront cost is real; a single linear pass over unsorted data is strictly cheaper than sorting it first and then scanning once."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 8 ("Sorting in Linear
  Time") — the decision-tree lower bound proof, and the linear-time sorts that sidestep it.
- Sedgewick & Wayne, *Algorithms*, 4th ed., Ch. 2 ("Sorting") — the elementary and efficient sorts
  covered in this folder, measured against each other empirically.

## Related Pages

- [Complexity & Analysis](../complexity/intro.md) — where the lower-bound argument is developed.
- [Divide & Conquer](../problem-solving-patterns/divide-and-conquer.md) — the pattern behind mergesort and quicksort.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the structure heapsort is built on.
- [Binary Search](../searching/binary-search.md) — the $O(\log n)$ payoff that sorting exists to enable.
