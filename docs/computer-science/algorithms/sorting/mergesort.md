---
id: mergesort
title: Mergesort
sidebar_label: Mergesort
sidebar_position: 4
tags: [computer-science, algorithms, sorting, mergesort, divide-and-conquer]
---

# Mergesort


Mergesort splits the array in half, sorts each half recursively, and merges the two sorted halves
back together. The insight is that **merging two already-sorted sequences is linear** — you compare
their two front elements and take the smaller, repeatedly.

Splitting costs nothing and produces log n levels; merging costs O(n) per level. Hence O(n log n),
on every input, with no worst case to worry about.

<Figure src="/img/cs/algorithms/mergesort-diagram.png"
        alt="A diagram of mergesort on the list 38, 27, 43, 3, 9, 82, 10: red arrows split it down to single elements, then green arrows merge pairs back upward into progressively longer sorted runs"
        caption="Splitting down (red) does no comparisons at all. All the work is in merging back up (green), where each level touches every element exactly once."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Merge_sort_algorithm_diagram.svg"
        license="Public domain" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | O(n log n) |
| Average | O(n log n) |
| Worst case | **O(n log n)** — guaranteed |
| Space | O(n) — the merge buffer |
| Stable | **Yes** |
| Adaptive | No, in the classic form (but see [Timsort](./choosing-a-sort.md)) |
| Parallelises | Well — the two halves are independent |

## Architecture / Mechanism

```python showLineNumbers
def merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left = merge_sort(a[:mid])          # sort each half
    right = merge_sort(a[mid:])
    return merge(left, right)

def merge(left, right):
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:         # <= keeps the sort stable
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])                # one side is exhausted; append the rest
    out.extend(right[j:])
    return out
```

<Figure src="/img/cs/algorithms/mergesort.gif"
        alt="Animation of mergesort on a set of bars, showing adjacent runs being merged into progressively longer sorted runs until the whole array is ordered"
        caption="Runs double in length at each level: 1, 2, 4, 8… The array is sorted after log₂ n merge passes."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Merge-sort-example-300px.gif"
        license="CC BY-SA 3.0" />

### Why the complexity is exactly O(n log n)

The recursion halves the input, so it has `log₂ n` levels. Every level merges a total of n elements,
regardless of how they are distributed across subarrays. Work per level is therefore Θ(n), and the
total is Θ(n log n) — with no dependence on the data, which is why best, average and worst are all
the same.

### Stability comes from one character

`left[i] <= right[j]` takes from the **left** run when elements compare equal. Since the left run
holds elements that came earlier in the original array, equal elements keep their original order.
Change it to `<` and the merge takes from the right on ties, silently destroying stability.

## Practical Usage

Mergesort is the right choice when:

- **Stability is required** — sorting by a secondary key after a primary one.
- **Worst-case guarantees matter** — real-time or adversarial contexts where
  [quicksort's](./quicksort.md) O(n²) is unacceptable.
- **The data does not fit in memory.** External mergesort reads sorted runs from disk and merges them
  with sequential I/O, which is the one access pattern [storage](../../storage/intro.md) is good at.
  This is how databases sort tables larger than RAM.
- **You are sorting a [linked list](../data-structures/linked-lists.md).** Merging lists needs only
  pointer rewiring — O(1) extra space, no random access required. This is the one case where
  mergesort is *better* on a list than on an array.
- **You want to parallelise.** The two recursive calls share nothing.

```python showLineNumbers
# Bottom-up mergesort — no recursion, same complexity
def merge_sort_iterative(a):
    width = 1
    while width < len(a):
        for i in range(0, len(a), 2 * width):
            a[i:i + 2 * width] = merge(a[i:i + width], a[i + width:i + 2 * width])
        width *= 2
    return a
```

## Edge Cases & Pitfalls

:::warning[The O(n) space is the real cost]
Mergesort cannot merge in place efficiently. Naive in-place merge algorithms exist but are either
O(n²) or have constant factors bad enough to erase the benefit. For a large array this means a second
buffer the same size — which can be the deciding factor on memory-constrained systems, and is the
main reason [quicksort](./quicksort.md) is preferred for in-memory array sorting.

A good implementation allocates **one** scratch buffer up front and reuses it, rather than allocating
per merge as the readable version above does.
:::

- **Slicing allocates.** The Python above creates new lists at every level — clear, but it does
  roughly O(n log n) allocation. Production code passes indices into a single shared buffer.
- **`<` instead of `<=`** in the merge silently loses stability.
- **Recursion depth is O(log n)**, which is safe — unlike quicksort's worst case.

## Comparisons

| | Mergesort | [Quicksort](./quicksort.md) | [Heapsort](./heapsort.md) |
|---|---|---|---|
| Worst case | **O(n log n)** | O(n²) | **O(n log n)** |
| Space | O(n) | O(log n) | **O(1)** |
| Stable | **Yes** | No | No |
| Locality | Good — sequential merges | **Excellent** | Poor — jumps around |
| Typical speed on arrays | Good | **Fastest** | Slowest of the three |
| Linked lists | **Ideal** | Awkward | Impractical |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §2.3 — mergesort, and the recurrence-tree analysis of its complexity.
- Knuth, *The Art of Computer Programming*, Vol. 3, §5.2.4 — merging and external sorting, including multiway merges.

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — watch the merge levels build up.

## Related Pages

- [Quicksort](./quicksort.md) — the in-place alternative with a worse worst case.
- [Divide & Conquer](../problem-solving-patterns/divide-and-conquer.md) — the general pattern this instantiates.
- [Choosing a Sort](./choosing-a-sort.md) — Timsort, which is an adaptive mergesort.
