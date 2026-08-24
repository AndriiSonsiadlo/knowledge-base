---
id: choosing-a-sort
title: Choosing a Sort
sidebar_label: Choosing a Sort
sidebar_position: 7
tags: [computer-science, algorithms, sorting, timsort, introsort, pdqsort]
---

# Choosing a Sort


In almost every situation the correct answer is **call your language's built-in sort**. Those
implementations are hybrids refined over decades, and they beat hand-written sorts on nearly every
input. This page is about knowing what you are calling, and recognising the rare cases where the
default is wrong.

## What the standard libraries actually do

| Language | Function | Algorithm | Stable |
|---|---|---|---|
| Python | `sorted`, `list.sort` | **Timsort** | Yes |
| Java | `Arrays.sort` (objects), `Collections.sort` | Timsort | Yes |
| Java | `Arrays.sort` (primitives) | Dual-pivot quicksort | No |
| C++ | `std::sort` | **Introsort** | No |
| C++ | `std::stable_sort` | Mergesort (or in-place mergesort if memory is tight) | Yes |
| Rust | `sort` | Timsort-derived | Yes |
| Rust | `sort_unstable` | **pdqsort** (pattern-defeating quicksort) | No |
| Go | `slices.Sort` | pdqsort | No |
| Go | `slices.SortStable` | Insertion sort + symmerge | Yes |
| C | `qsort` | Implementation-defined; usually a quicksort hybrid | No |

Three designs cover almost all of that table.

### Timsort — adaptive mergesort

Invented by Tim Peters for Python in 2002, and since adopted by Java, Android, Rust and V8. The
premise is that **real data is rarely random**: it arrives partly ordered, appended to, or
concatenated from sorted pieces.

Timsort scans for existing sorted **runs**, extends short ones using
[insertion sort](./insertion-sort.md), and then merges runs under rules that keep the merge tree
balanced. On already-sorted input it finds one run and finishes in O(n).

| Property | Value |
|---|---|
| Best case | **O(n)** — already sorted, or a handful of runs |
| Worst case | O(n log n) |
| Space | O(n) |
| Stable | Yes |

### Introsort — quicksort that cannot degrade

C++'s `std::sort`. Runs [quicksort](./quicksort.md), but:

- switches to [insertion sort](./insertion-sort.md) for ranges below ~16 elements;
- switches to [heapsort](./heapsort.md) when recursion exceeds `2·log₂ n` levels.

The depth limit is what removes quicksort's O(n²) worst case, without slowing the common path.

### pdqsort — pattern-defeating quicksort

Rust's `sort_unstable` and Go's `slices.Sort`. Introsort plus pattern detection: it recognises
already-sorted and reverse-sorted runs, uses three-way partitioning when duplicates are common, and
breaks up adversarial patterns by shuffling deterministically when partitions come out badly. The
result is O(n) on several common shapes while keeping introsort's guarantees.

## How to Choose

```mermaid
flowchart TD
    A["Need to sort"] --> B{"Does equal-element order matter?"}
    B -->|Yes| C["Use the stable sort:<br/>sorted / stable_sort / SortStable"]
    B -->|No| D{"Does it fit in memory?"}
    D -->|No| E["External mergesort —<br/>or let the database do it"]
    D -->|Yes| F{"Are keys small bounded integers?"}
    F -->|Yes| G["Counting or radix sort — O(n)"]
    F -->|No| H["Built-in unstable sort:<br/>std::sort / sort_unstable"]
```

| Situation | Use |
|---|---|
| Anything, by default | The built-in sort |
| Sorting by a secondary key after a primary | A **stable** sort |
| Hard real-time or adversarial input | [Heapsort](./heapsort.md) or introsort — bounded worst case |
| Data larger than RAM | External [mergesort](./mergesort.md) |
| Integer keys in a small known range | Counting sort — O(n + k) |
| Fixed-width keys (integers, dates, strings) | Radix sort — O(nw) |
| Fewer than ~16 elements | [Insertion sort](./insertion-sort.md) |
| Only need the top k | A [heap](../data-structures/heaps.md) — O(n + k log n) |
| Only need the median or k-th element | Quickselect — O(n) average |

:::tip[Sort keys, not records]
When elements are large, sorting them directly copies a lot of bytes per move. Sort an array of
indices or pointers using the record as the comparison key, then permute once at the end. This is
also how you sort the same data by several different keys without duplicating it.

The related trick is the **decorate-sort-undecorate** pattern — Python's `key=` argument does exactly
this, computing each key once instead of on every comparison.
:::

## Edge Cases & Pitfalls

:::danger[An inconsistent comparator is undefined behaviour, not a wrong answer]
Comparison sorts require a **strict weak ordering**: if `a < b` then not `b < a`, comparison must be
transitive, and equivalence must be transitive too. Violating it — `return a.score >= b.score`
instead of `>`, or a comparator using a mutable field — does not merely produce a wrongly-ordered
list. In C++ it is undefined behaviour and routinely reads out of bounds; Java throws
`IllegalArgumentException: Comparison method violates its general contract!`, but only sometimes,
depending on input size.

Write `<`, never `<=`, in a comparator.
:::

- **Comparing floats with NaN breaks the ordering**, since every comparison with NaN is false. Filter
  or handle NaN explicitly.
- **Sorting a mostly-sorted list with an unstable sort still costs O(n log n)** in introsort or
  pdqsort's non-detected cases. Timsort is the one that exploits it fully.
- **`sort()` mutates, `sorted()` copies** in Python. The same distinction is `sort` vs. `to_vec` then
  sort in Rust; picking the wrong one is a silent aliasing bug.
- **Do not write your own sort for production.** The cases you will get wrong — equal keys, depth
  limits, comparator contracts — are exactly the ones these implementations spent years on.

## References

- Peters, T., [Timsort description](https://github.com/python/cpython/blob/main/Objects/listsort.txt) — the original design notes, and an unusually readable engineering document.
- Musser, D. (1997), ["Introspective Sorting and Selection Algorithms"](https://www.cs.rpi.edu/~musser/gp/introsort.ps) — introsort.
- Peters, O. (2021), [pdqsort](https://github.com/orlp/pdqsort) — the pattern-defeating quicksort implementation and its rationale.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.5 — "Sorting Applications", on choosing among sorts in practice.

## Related Pages

- [Sorting Algorithms — Overview](./intro.md) — the comparison table for all six algorithms.
- [Complexity & Analysis](../complexity/intro.md) — including why O(n) sorts need assumptions about the keys.
- [Heaps & Priority Queues](../data-structures/heaps.md) — for the top-k and median cases above.
