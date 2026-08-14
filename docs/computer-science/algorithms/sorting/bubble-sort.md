---
id: bubble-sort
title: Bubble Sort
sidebar_label: Bubble Sort
sidebar_position: 1
tags: [computer-science, algorithms, sorting, bubble-sort]
---

# Bubble Sort

## Overview

Bubble sort repeatedly walks the list comparing adjacent pairs and swapping them when they are out of
order. Each pass carries the largest remaining element to the end — it "bubbles up" — so after `k`
passes the last `k` elements are final.

It is the simplest sort to explain and the least useful one to run. Its value is pedagogical: it
makes the idea of an invariant ("after pass k, the tail is sorted") completely visible.

<Figure src="/img/cs/algorithms/bubble-sort.gif"
        alt="Animation of bars of varying heights being sorted by bubble sort, with adjacent bars repeatedly compared and swapped so the tallest bar migrates to the right end on each pass"
        caption="Each pass sweeps left to right, swapping neighbours. The largest unsorted element reaches its final position at the end of every pass."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Sorting_bubblesort_anim.gif"
        license="CC BY-SA 3.0" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | O(n) — one pass over already-sorted data, with the early exit |
| Average | O(n²) |
| Worst case | O(n²) — reverse-sorted input |
| Space | O(1) — sorts in place |
| Stable | Yes — only strictly out-of-order neighbours are swapped |
| Adaptive | Yes, with the early-exit optimisation |

## Architecture / Mechanism

```python showLineNumbers
def bubble_sort(a):
    n = len(a)
    for i in range(n - 1):
        swapped = False
        # After i passes the last i elements are already in place
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:      # a clean pass means the list is sorted
            break
    return a
```

Two details separate the textbook version from the naive one:

- **`n - 1 - i`** — the tail is already sorted, so re-scanning it is wasted work. Without this the
  algorithm does the same number of comparisons regardless of progress.
- **`swapped`** — a pass with no swaps proves the list is ordered, giving the O(n) best case. Without
  it, bubble sort is O(n²) even on sorted input.

Tracing `[5, 1, 4, 2]`:

| Pass | Comparisons | Result |
|---|---|---|
| 1 | (5,1) swap, (5,4) swap, (5,2) swap | `[1, 4, 2, 5]` |
| 2 | (1,4) no, (4,2) swap | `[1, 2, 4, 5]` |
| 3 | (1,2) no, no swaps → exit | `[1, 2, 4, 5]` |

## Edge Cases & Pitfalls

:::warning[Do not use this in production code]
Bubble sort is not merely asymptotically poor — it is the *slowest* of the quadratic sorts by a
constant factor too, because it performs far more swaps than
[insertion](./insertion-sort.md) or [selection](./selection-sort.md) sort for the same input. On
nearly-sorted data insertion sort matches its O(n) best case while being faster everywhere else, and
on random data it does a fraction of the writes.

There is no input distribution on which bubble sort is the right choice. If you want a simple sort
for small arrays, use insertion sort.
:::

- **Omitting the early exit** is common in textbook versions and removes the only case where the
  algorithm looks respectable.
- **The `n - 1 - i` bound is easy to get wrong**, and the off-by-one produces an out-of-range access
  on the last pass rather than a wrong answer, which at least fails loudly.

## Comparisons

| | Bubble | [Selection](./selection-sort.md) | [Insertion](./insertion-sort.md) |
|---|---|---|---|
| Comparisons | O(n²) | O(n²) always | O(n²), O(n) if nearly sorted |
| Swaps / writes | O(n²) — the most | **O(n)** — the fewest | O(n²), but few if nearly sorted |
| Best case | O(n) | O(n²) | O(n) |
| Stable | Yes | No | Yes |
| Worth using | No | When writes are expensive | Yes, for small or nearly-sorted input |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* — bubble sort appears as Problem 2-2, notably not as a presented algorithm.
- Knuth, *The Art of Computer Programming*, Vol. 3, §5.2.2 — "the bubble sort seems to have nothing to recommend it, except a catchy name".

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — step through bubble sort against the others on the same input.

## Related Pages

- [Insertion Sort](./insertion-sort.md) — the quadratic sort that is actually worth using.
- [Choosing a Sort](./choosing-a-sort.md) — what production implementations really do.
