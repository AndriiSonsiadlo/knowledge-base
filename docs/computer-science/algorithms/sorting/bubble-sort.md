---
id: bubble-sort
title: Bubble Sort
sidebar_label: Bubble Sort
sidebar_position: 1
tags: [computer-science, algorithms, sorting, bubble-sort]
---

# Bubble Sort

Bubble sort repeatedly walks the array comparing adjacent pairs and swapping them when they are out
of order. Each pass carries the largest remaining element to the end — it "bubbles up" — so after `k`
passes the last `k` elements are final.

The right way to see why it costs what it costs is through **inversions**: a pair of positions `(i, j)`
with `i < j` but `a[i] > a[j]`. A swap of adjacent elements can only ever remove **exactly one**
inversion — the one between the two elements just swapped — because every other pair's relative order
is untouched by an adjacent swap. The array is sorted exactly when it has zero inversions, so bubble
sort's total number of swaps *is* the number of inversions in the input. A reverse-sorted array of
length n has every pair inverted — `n(n−1)/2` of them — which is both bubble sort's worst-case swap
count and, not coincidentally, its worst-case comparison count.

That framing is also the honest verdict on the algorithm: it is the textbook's simplest illustration
of an invariant ("after pass k, the last k elements are sorted"), and nobody should ship it. Every
other quadratic sort in this section beats it on the same input, for the same asymptotic class, by a
real constant factor.

<Figure src="/img/cs/algorithms/bubble-sort.gif"
        alt="Animation of bars of varying heights being sorted by bubble sort, with adjacent bars repeatedly compared and swapped so the tallest bar migrates to the right end on each pass"
        caption="Each pass sweeps left to right, swapping neighbours. The largest unsorted element reaches its final position at the end of every pass."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Sorting_bubblesort_anim.gif"
        license="CC BY-SA 3.0" />

## Core Concepts

| Term | Meaning |
|---|---|
| **Inversion** | A pair `(i, j)`, `i < j`, with `a[i] > a[j]` — two elements in the wrong relative order |
| Best case | $O(n)$ — one pass over already-sorted data (zero inversions), with the early exit |
| Average | $O(n^2)$ — a random permutation has $Θ(n^2)$ inversions |
| Worst case | $O(n^2)$ — reverse-sorted input has the maximum possible `n(n−1)/2` inversions |
| Space | $O(1)$ — sorts in place |
| Stable | Yes — only strictly out-of-order neighbours are swapped, so equal keys are never exchanged |
| Adaptive | Yes, with the early-exit optimisation |

## Mechanism

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <utility>
#include <vector>

void bubble_sort(std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    for (int i = 0; i < n - 1; ++i) {
        bool swapped = false;
        // After i passes the last i elements are already in place
        for (int j = 0; j < n - 1 - i; ++j) {
            if (a[j] > a[j + 1]) {
                std::swap(a[j], a[j + 1]);
                swapped = true;
            }
        }
        if (!swapped) break;      // a clean pass means the list is sorted
    }
}
```

</TabItem>
</Tabs>

Two details separate the textbook version from the naive one:

- **`n - 1 - i`** — the tail is already sorted, so re-scanning it is wasted work. Without this the
  algorithm does the same number of comparisons regardless of progress.
- **`swapped`** — a pass with no swaps proves the list has zero inversions left, giving the $O(n)$ best
  case. Without it, bubble sort is $O(n^2)$ even on sorted input, because it keeps making full passes
  it no longer needs.

Tracing `[5, 1, 8, 3]` — three inversions to start: `(0,1)=(5,1)`, `(0,3)=(5,3)`, `(2,3)=(8,3)`.
Every other pair is already in order — `(1,3)` is not inverted since `1 < 3` — so bubble sort makes
exactly three swaps before it can finish:

| Pass | Comparisons (adjacent pairs) | Swaps this pass | Result | Inversions remaining |
|---|---|---|---|---|
| start | — | — | `[5, 1, 8, 3]` | 3 |
| 1 | (5,1) swap, (5,8) no, (8,3) swap | 2 | `[1, 5, 3, 8]` | 1 |
| 2 | (1,5) no, (5,3) swap | 1 | `[1, 3, 5, 8]` | 0 |
| 3 | (1,3) no, (3,5) no → no swaps, exit | 0 | `[1, 3, 5, 8]` | 0 |

Each swap removed exactly the one inversion between the two elements it touched — pass 1's first swap
fixed `(5,1)`, its second fixed `(8,3)`, and pass 2's swap fixed `(5,3)`. Three inversions, three
swaps, and the third pass runs only to confirm there is nothing left to do.

## Practical Usage

There is no production context where bubble sort is the right call — it is included here for the
invariant it teaches, not for a call site. The one place the *inversion-counting* idea earns its keep
directly is outside sorting altogether: counting inversions with a modified mergesort runs in
$O(n \log n)$ and is the standard way to measure "how far from sorted" a sequence is (CLRS 4th ed.,
Problem 2-4), which is the same quantity [insertion sort's](./insertion-sort.md) adaptive cost is
built around.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# checked on the traced input: 3 inversions in, 3 swaps to sort
assert bubble_sort([5, 1, 8, 3]) == [1, 3, 5, 8]
assert bubble_sort([1, 2, 3]) == [1, 2, 3]          # zero inversions, one pass, no swaps
assert bubble_sort([]) == []
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    std::vector<int> a{5, 1, 8, 3};
    bubble_sort(a);
    assert((a == std::vector<int>{1, 3, 5, 8}));
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

:::warning[Do not use this in production code]
Bubble sort is not merely asymptotically poor — it is the *slowest* of the quadratic sorts by a
constant factor too, because it performs roughly as many swaps as it has inversions, while
[insertion sort](./insertion-sort.md) performs exactly the same number of **shifts** — but a shift is
one write, where bubble sort's swap is conventionally three (temp = a; a = b; b = temp, or an XOR-swap
of similar cost). On nearly-sorted data insertion sort matches its $O(n)$ best case while being faster
everywhere else, and on random data it does a fraction of the total writes for an identical number of
inversions resolved.

There is no input distribution on which bubble sort is the right choice. If you want a simple sort
for small arrays, use insertion sort.
:::

- **Omitting the early exit** is common in textbook versions and removes the only case where the
  algorithm looks respectable — without it, sorted input still costs the full `n(n−1)/2` comparisons.
- **The `n - 1 - i` bound is easy to get wrong**, and the off-by-one produces an out-of-range access
  on the last pass rather than a wrong answer, which at least fails loudly.
- **Confusing "number of passes" with "number of swaps".** The loop runs at most `n − 1` passes, but
  the *swap* count is exactly the inversion count — on an input with few inversions, most passes do
  little or no work even before the early exit triggers on the first fully clean one.

## Comparisons

| | Bubble | [Selection](./selection-sort.md) | [Insertion](./insertion-sort.md) |
|---|---|---|---|
| Comparisons (worst) | $O(n^2)$ | $O(n^2)$ always | $O(n^2)$, $O(n)$ if nearly sorted |
| Swaps / writes (worst) | $O(n^2)$ — one swap (≈3 writes) per inversion | **$O(n)$** — exactly n − 1 writes | $O(n^2)$ shifts, but few if nearly sorted |
| Best case | $O(n)$ | $O(n^2)$ | $O(n)$ |
| Stable | Yes | No | Yes |
| Worth using | No | When writes are expensive | Yes, for small or nearly-sorted input |

## Recall

<Recall
  invariant="Each adjacent swap removes exactly one inversion, so the total number of swaps over the whole sort equals the number of inversions in the input — zero for sorted data, n(n−1)/2 for reverse-sorted data."
  costs={[
    ["comparisons (best, sorted input)", "O(n)"],
    ["comparisons (worst, reverse-sorted)", "O(n^2)"],
    ["swaps, all passes (worst)", "O(n^2), exactly n(n-1)/2"],
    ["extra space (worst)", "O(1)"],
  ]}
  reachFor="Nowhere in production — reach for insertion sort instead. This page exists to teach the inversion-counting argument that also explains insertion sort's adaptivity."
  trap="Omitting the early-exit `swapped` flag: without it, already-sorted input still costs the full O(n^2) comparisons, destroying the one case where bubble sort looks reasonable."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Problem 2-2 (bubble sort
  itself, notably not presented as a taught algorithm) and Problem 2-4 (formal definition of inversions
  and an $O(n \log n)$ counting algorithm via mergesort).
- Knuth, *The Art of Computer Programming*, Vol. 3, §5.2.2 — "the bubble sort seems to have nothing to
  recommend it, except a catchy name", plus the exact expected-inversions analysis for a random
  permutation.

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — step through bubble sort against the others on the same input.

## Related Pages

- [Insertion Sort](./insertion-sort.md) — the quadratic sort that is actually worth using, and whose
  adaptive cost is the same inversion count computed here.
- [Selection Sort](./selection-sort.md) — the other elementary sort, distinguished instead by its
  minimal write count.
- [Choosing a Sort](./choosing-a-sort.md) — what production implementations really do.
