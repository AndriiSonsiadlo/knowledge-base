---
id: cheat-sheet
title: Sorting Cheat Sheet
sidebar_label: Cheat Sheet
sidebar_position: 11
tags: [computer-science, algorithms, sorting, cheat-sheet]
---

# Sorting Cheat Sheet

This page is a reference, not a tutorial — each algorithm's own page derives the bound it gets here.
Every complexity below names its case (best / average / worst); the full argument for each lives on
that algorithm's own page, alongside its worked trace.

## Complexity and property matrix

| Algorithm | Best | Average | Worst | Space | Stable | In-place |
|---|---|---|---|---|---|---|
| [Bubble Sort](./bubble-sort.md) | $O(n)$ (already sorted, with an early-exit flag) | $O(n^2)$ | $O(n^2)$ | $O(1)$ | Yes | Yes |
| [Selection Sort](./selection-sort.md) | $O(n^2)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | No (naive swap-based form) | Yes |
| [Insertion Sort](./insertion-sort.md) | $O(n)$ (already sorted) | $O(n^2)$ | $O(n^2)$ | $O(1)$ | Yes | Yes |
| [Mergesort](./mergesort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n \log n)$ | $O(n)$ | Yes | No |
| [Quicksort](./quicksort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n^2)$ | $O(\log n)$ average (call stack) | No (standard partition schemes) | Yes |
| [Heapsort](./heapsort.md) | $O(n \log n)$ | $O(n \log n)$ | $O(n \log n)$ | $O(1)$ | No | Yes |
| [Counting Sort](./counting-radix-bucket-sort.md) | $O(n+k)$ | $O(n+k)$ | $O(n+k)$ | $O(n+k)$ | Yes | No |
| [LSD Radix Sort](./counting-radix-bucket-sort.md) | $O(d(n+r))$ | $O(d(n+r))$ | $O(d(n+r))$ | $O(n+r)$ | Yes | No |
| [Bucket Sort](./counting-radix-bucket-sort.md) | $O(n)$ | $O(n)$ expected, uniform keys | $O(n^2)$ | $O(n)$ | Depends on the per-bucket sort | No |

`k` is the counting-sort key range, `d` the number of digits, and `r` the radix (buckets per digit) in
the radix-sort row — see [Counting, Radix & Bucket Sort](./counting-radix-bucket-sort.md) for where
those variables come from. Every row above is a *comparison-based* claim except the last three, which
sidestep the Ω(n log n) comparison-sort lower bound entirely by assuming something about the keys
beyond "they support `<`" — a bounded range, a fixed digit width, or a known distribution.

## "What do you know about the input?" → reach for…

```mermaid
flowchart TD
    A["What do you actually know about the data?"] --> B{"Is the data too large\nto fit in memory?"}
    B -->|Yes| EXT["External merge sort\n(run generation + k-way merge)"]
    B -->|No| C{"Are the keys integers in a\nknown, small bounded range?"}
    C -->|Yes| CNT["Counting Sort"]
    C -->|No| D{"Fixed-width keys (IDs, bytes),\nor floats known to be ~uniform?"}
    D -->|Fixed-width digits| RDX["Radix Sort"]
    D -->|Uniform over an interval| BKT["Bucket Sort"]
    D -->|No| E{"Do you need one order\nstatistic, not a full sort?"}
    E -->|Yes| QS["Quickselect"]
    E -->|No| F{"Must equal keys keep their\nrelative input order (stability)?"}
    F -->|Yes, and memory for O(n) extra is fine| MRG["Mergesort"]
    F -->|No, and worst case must be guaranteed| HP["Heapsort"]
    F -->|No, average speed matters most| G{"Is the array nearly sorted,\nor is n tiny (< ~20)?"}
    G -->|Yes| INS["Insertion Sort"]
    G -->|No| QCK["Quicksort (or your language's hybrid built-in)"]
```

Two notes on reading this flow: "call your language's built-in sort" is almost always the right
terminal answer in practice — see [Choosing a Sort](./choosing-a-sort.md) for what Timsort, introsort,
and pdqsort actually are — and this flow exists for the case where you are implementing the sort
yourself, or need to justify which guarantee a system depends on. And the branches are not mutually
exclusive in a real system: a database might run counting sort on a bounded categorical column while
falling back to a comparison sort for a free-text one, in the same query.

## When the comparison-sort floor does not apply

Every algorithm in the matrix down through Heapsort is bound below by Ω(n log n) comparisons in the
worst case — a consequence of the decision-tree argument: any comparison sort correct on all `n!`
orderings of `n` distinct elements must have at least `n!` leaves in its decision tree, and a binary
tree needs height ≥ log₂(n!) = Ω(n log n) to have that many leaves (CLRS 4th ed. §8.1). Counting sort,
radix sort, and bucket sort are not exceptions to that bound — they simply do not decide order by
comparison at all, so the bound never applies to them in the first place. That is also exactly why they
each require an assumption the comparison sorts do not: a bounded key range, a fixed digit count, or a
known distribution. Violate the assumption (unbounded 64-bit keys for counting sort, a wildly skewed
distribution for bucket sort) and there is no fallback guarantee — the algorithm either stops applying
or degrades, as detailed on [Counting, Radix & Bucket Sort](./counting-radix-bucket-sort.md).

## Recall

<Recall
  invariant="Every sort in this folder trades away something to buy a guarantee: comparison sorts trade time for a Ω(n log n) worst case that holds for any comparable key, while counting/radix/bucket sort trade generality — a bounded range, fixed digits, or a known distribution — for O(n)-shaped time that a pure comparison sort can never reach."
  costs={[
    ["mergesort, guaranteed (worst)", "O(n log n)"],
    ["quicksort, expected (average)", "O(n log n)"],
    ["quicksort, adversarial pivot sequence (worst)", "O(n²)"],
    ["counting/radix/bucket sort under their assumptions (worst or expected, see matrix)", "O(n) shaped"],
    ["quickselect, one order statistic (average)", "O(n)"],
  ]}
  reachFor="A quick lookup while choosing an algorithm for a new problem, or checking a claimed complexity, rather than a first read on any one sort."
  trap="Assuming a faster-looking average case (quicksort, bucket sort) is safe without checking what triggers its worst case — an adversarial or already-sorted input for quicksort, a skewed distribution for bucket sort."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §8.1 (the comparison-sort
  lower bound), Ch. 2 (insertion sort, merge sort), Ch. 6-7 (heapsort, quicksort), §8.2-8.4
  (counting, radix, bucket sort) — the chapters this page's matrix summarises.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.1-2.5 (elementary sorts through quicksort) and §5.1
  (radix sorts) — the empirical comparisons this cheat sheet's decision flow follows.

## Related Pages

- [Choosing a Sort](./choosing-a-sort.md) — why "call the standard library" beats every row in the
  matrix above in nearly every real program, and what those library sorts actually are.
- [Counting, Radix & Bucket Sort](./counting-radix-bucket-sort.md) — the three non-comparison rows,
  their assumptions, and what happens when an assumption is violated.
- [Quickselect](./quickselect.md) — the O(n) answer when the question is one order statistic, not a
  full ordering.
- [Complexity Cheat Sheet](../complexity/cheat-sheet.md) — the growth-rate table this page's Big-O
  notation assumes.
