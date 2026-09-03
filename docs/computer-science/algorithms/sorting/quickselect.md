---
id: quickselect
title: Quickselect
sidebar_label: Quickselect
sidebar_position: 8
tags: [computer-science, algorithms, sorting, selection, quickselect, median-of-medians]
---

# Quickselect

Finding the k-th smallest element does not require sorting the whole array. Sorting throws away no
information at all — every element's rank relative to every other becomes known — but a "find the
median" or "find the 90th percentile" query only ever asks about one rank. Quickselect answers exactly
that question, using [quicksort](./quicksort.md)'s partition step but throwing away the side of the
partition that cannot contain the answer, instead of recursing into both.

The result is an algorithm with the same worst-case pathology as quicksort — a bad pivot sequence
still degrades it to O(n²) — but an average case that is not O(n log n), it is **O(n)**. That
difference is not a rounding error: quicksort must still recurse into both halves to place every
element, while quickselect only ever recurses into the one half that contains the k-th element, and
each level of that recursion does geometrically less work than the one before.

:::info[Prerequisites]
Requires [quicksort](./quicksort.md)'s partition step — this page reuses it rather than re-deriving
it. Comfortable with recurrence relations helps for the average-case argument below.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **k-th smallest** | The element that would sit at index `k` (0-indexed) if the array were sorted |
| **Partition** | Rearranges the array around a pivot so everything ≤ pivot is left of it, everything > pivot is right — same operation as quicksort's |
| **Selection** | The general problem name: finding an order statistic without fully sorting |
| **Median of medians** | A pivot-selection scheme that guarantees O(n) worst case, at a large constant-factor cost |
| **`nth_element`** | C++'s standard-library selection algorithm — a partial ordering around one position, not a full sort |

## Mechanism

Quickselect partitions exactly as quicksort does, then looks at where the pivot landed relative to
`k`: if the pivot's final index equals `k`, that value *is* the answer. If the pivot landed to the
right of `k`, the answer is somewhere in the left partition and the right partition is discarded
entirely — no recursive call into it, not even to look. Symmetrically for the pivot landing left of
`k`. Unlike quicksort, at most one recursive call happens per level.

<Figure src="/img/cs/algorithms/quickselect-shrink.png"
        alt="Three panels of the same 8-element array: level 0 with the whole array searched and a pivot marked, level 1 with only indices 0 through 2 searched and the rest greyed out as discarded, and level 2 with a single surviving index marked as the answer"
        caption="Finding the 3rd smallest of [5, 1, 8, 3, 9, 2, 7, 4]. Each level partitions only the still-active region and discards the other side outright — the searched region roughly halves per level, which is the geometric-series argument behind the average O(n) bound." />

```text
find the 3rd smallest (0-indexed k=2) of [5, 1, 8, 3, 9, 2, 7, 4]

level 0: arr = [5, 1, 8, 3, 9, 2, 7, 4], range [0, 7], pivot = arr[7] = 4
  partition (Lomuto, pivot last) -> [1, 3, 2, 4, 9, 8, 7, 5]
  pivot's final index = 3
  3 > k=2  -> answer is left of the pivot; discard indices [4, 7] entirely, recurse on [0, 2]

level 1: arr[0..2] = [1, 3, 2], range [0, 2], pivot = arr[2] = 2
  partition -> [1, 2, 3]  (only this sub-range changes; full array now [1, 2, 3, 4, 9, 8, 7, 5])
  pivot's final index = 1
  1 < k=2  -> answer is right of the pivot; discard index [0, 1], recurse on [2, 2]

level 2: range [2, 2] is a single element: arr[2] = 3
  return 3   -- the 3rd smallest, confirmed by the fully sorted array [1,2,3,4,5,7,8,9]
```

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def partition(a, lo, hi):
    """Lomuto partition: pivot is a[hi]. Returns the pivot's final index."""
    pivot = a[hi]
    i = lo - 1
    for j in range(lo, hi):
        if a[j] <= pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[i + 1], a[hi] = a[hi], a[i + 1]
    return i + 1


def quickselect(a, k, lo=0, hi=None):
    """The k-th smallest element (0-indexed) of a[lo..hi], via one-sided recursion."""
    if hi is None:
        hi = len(a) - 1
    while True:                                # iterative: only one side ever recurses
        if lo == hi:
            return a[lo]
        p = partition(a, lo, hi)
        if p == k:
            return a[p]
        elif p > k:
            hi = p - 1                          # discard the right side outright
        else:
            lo = p + 1                          # discard the left side outright
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <utility>
#include <vector>

int partition(std::vector<int>& a, int lo, int hi) {
    int pivot = a[hi];
    int i = lo - 1;
    for (int j = lo; j < hi; ++j) {
        if (a[j] <= pivot) std::swap(a[++i], a[j]);
    }
    std::swap(a[i + 1], a[hi]);
    return i + 1;
}

int quickselect(std::vector<int>& a, int k, int lo, int hi) {
    while (true) {
        if (lo == hi) return a[lo];
        int p = partition(a, lo, hi);
        if (p == k) return a[p];
        else if (p > k) hi = p - 1;
        else lo = p + 1;
    }
}
```

</TabItem>
</Tabs>

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# checked on the traced input: 3rd smallest (0-indexed k=2) of [5, 1, 8, 3, 9, 2, 7, 4]
assert quickselect([5, 1, 8, 3, 9, 2, 7, 4], 2) == 3
assert quickselect([5, 1, 8, 3, 9, 2, 7, 4], 0) == 1     # the minimum
assert quickselect([5, 1, 8, 3, 9, 2, 7, 4], 7) == 9     # the maximum
assert quickselect([4], 0) == 4                           # single element, no partition needed
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    std::vector<int> a1 = {5, 1, 8, 3, 9, 2, 7, 4};
    assert(quickselect(a1, 2, 0, 7) == 3);
    std::vector<int> a2 = {5, 1, 8, 3, 9, 2, 7, 4};
    assert(quickselect(a2, 0, 0, 7) == 1);
    std::vector<int> a3 = {4};
    assert(quickselect(a3, 0, 0, 0) == 4);
}
```

</TabItem>
</Tabs>

### Why the average case is O(n), not O(n log n)

Quicksort's recurrence is `T(n) = T(left) + T(right) + O(n)` — both sides are paid for. Quickselect's
recurrence is `T(n) = T(max(left, right)) + O(n)` — only one side is ever paid for, because the other
is discarded without a call. With a random pivot, the expected size of the recursed-into side is at
most `3n/4` (the same "middle half" argument as in quicksort's average-case analysis), so the expected
total work follows a geometric series:

```text
T(n) ≤ cn + T(3n/4) ≤ cn + c(3n/4) + T(9n/16) ≤ cn (1 + 3/4 + (3/4)² + (3/4)³ + …) = cn · 4 = O(n)
```

The partition-and-discard work at each level shrinks by a constant factor (roughly `3/4` per level, on
expectation), so the series converges to a constant multiple of the *first* term — the total is
dominated by the first partition, not by how many levels there are. This is the same style of argument
CLRS 4th ed. §9.2 formalises rigorously (with an indicator-variable expectation, not the sketch above)
for its randomized `SELECT`.

## Practical Usage

- **C++ `std::nth_element`** ([cppreference](https://en.cppreference.com/w/cpp/algorithm/nth_element))
  is quickselect in the standard library: it partially reorders a range so the element at the given
  position is the one that would be there in a fully sorted range, and every element before it is ≤
  every element after it — but neither side is otherwise sorted. The standard specifies its complexity
  as "linear on average" ([`[alg.nth.element]`](https://eel.is/c++draft/alg.nth.element)); libstdc++
  and libc++ both implement introselect (quickselect that falls back to median-of-medians on excessive
  recursion depth) to bound the worst case, the same idea introsort applies to quicksort — see
  [Choosing a Sort](./choosing-a-sort.md).
- **Python has no `nth_element`.** `heapq.nsmallest(k, iterable)` and `heapq.nlargest` solve a related
  but different problem — the k smallest/largest values *in order* — using a heap, in
  O(n log k) ([Python docs](https://docs.python.org/3/library/heapq.html#heapq.nsmallest)), not
  O(n). For a single unordered k-th value, `sorted(a)[k]` is the simple correct answer at O(n log n);
  hand-rolled quickselect only pays off when the O(n) vs O(n log n) gap matters at your data size.
- **Streaming or unknown-size input.** Neither quickselect nor `nth_element` applies without the whole
  array in memory; a running k-th-order-statistic over a stream is a different problem (reservoir
  sampling or a bounded heap), not covered here.

## Edge Cases & Pitfalls

- **Off-by-one between "k-th smallest" and "index k".** "The 3rd smallest" is index 2 in a 0-indexed
  array. Every call site needs to fix this convention once, in one place, rather than re-deriving it
  per call.
- **Adversarial input against a fixed pivot rule.** Exactly like quicksort: choosing `a[hi]` as the
  pivot on an already-sorted or reverse-sorted array makes every partition maximally unbalanced,
  degrading to **O(n²) worst case**. A random pivot (swap a random element into `a[hi]` before
  partitioning) defeats an adversary that only sees the algorithm, not its random seed.
- **Recursing into both sides "to be safe".** This silently turns quickselect back into a selection via
  quicksort — correct, but throws away the entire performance argument. The one-sided recursion is not
  an optimization detail, it is the whole point of the algorithm.
- **Duplicate-heavy arrays.** The Lomuto scheme above places all elements ≤ pivot on the pivot's side,
  so an array of mostly-equal values partitions unevenly on every call (`p` stays near `hi`) — a
  three-way (Dutch national flag) partition to segregate `<`, `==`, and `>` avoids the degradation, the
  same fix quicksort uses for duplicate-heavy data.

## Comparisons

| | Best | Average | Worst | Space | Notes |
|---|---|---|---|---|---|
| **Quickselect** | O(n) | O(n) | O(n²) | O(1) auxiliary (in-place partition) | The default answer; worst case needs an adversarial pivot sequence |
| Median of medians (deterministic pivot) | O(n) | O(n) | **O(n)** | O(n) auxiliary for the grouping | Guaranteed worst case, at 4-10× quickselect's real-world constant |
| Sort then index (`sorted(a)[k]`) | O(n log n) | O(n log n) | O(n log n) | O(n) | Simplest correct answer; wins when several different `k` are needed from the same array |
| Heap of size k (`heapq.nsmallest`) | O(n) | O(n log k) | O(n log k) | O(k) | Wins when `k` is small and fixed, or the input is a stream |

**Median of medians** guarantees O(n) worst case by choosing a pivot that is provably "good enough":
split the array into groups of 5, find each group's median (a fixed O(1) operation per group), then
recursively find the median *of those medians* and use it as the pivot. That pivot is guaranteed to be
greater than at least 30% and less than at least 30% of all elements, which bounds the recursion depth
and gives the recurrence `T(n) ≤ T(n/5) + T(7n/10) + O(n)` — CLRS 4th ed. §9.3 works through why the
two fractions sum to less than 1, which is exactly what makes the recursion terminate in linear total
work.

**Nobody uses it in practice** because the constant factor is large — grouping into fives, finding
each group's median, and recursing on the medians costs several times what a random-pivot quickselect
costs on ordinary data, for a worst-case guarantee that ordinary data essentially never triggers.
Randomized quickselect combined with introselect's depth-limited fallback (switch to a guaranteed-O(n)
method only if the recursion goes suspiciously deep) gets the same worst-case safety at a cost paid
only on the inputs that need it.

## Recall

<Recall
  invariant="Quickselect partitions like quicksort but recurses into only the side that can contain the k-th element — the other side's sort order is never resolved, which is what turns O(n log n) into O(n)."
  costs={[
    ["quickselect, random pivot (average)", "O(n)"],
    ["quickselect, adversarial pivot sequence (worst)", "O(n²)"],
    ["median-of-medians pivot selection (worst)", "O(n)"],
    ["`std::nth_element` (average, per the C++ standard)", "O(n)"],
    ["`heapq.nsmallest(k, a)` (worst)", "O(n log k)"],
  ]}
  reachFor="One order statistic — a median, a percentile, a top-k cutoff — from an array already in memory, where a full sort would do strictly more work than the question asked for."
  trap="Recursing into both partitions instead of just the one containing k. It still produces the right answer, but it silently regresses the algorithm to quicksort's O(n log n) average case and defeats the entire reason to use quickselect."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §9.2 (randomized `SELECT`
  and its expected linear-time proof), §9.3 (`SELECT` in worst-case linear time — median of medians).
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.5 "Quicksort" closing exercises — selection as a
  quicksort variant, and the partial-ordering guarantee it leaves behind.
- [`std::nth_element` — cppreference](https://en.cppreference.com/w/cpp/algorithm/nth_element) — the
  exact partial-ordering postcondition and the "linear on average" complexity note.
- [`[alg.nth.element]`, ISO C++ working draft](https://eel.is/c++draft/alg.nth.element) — the
  standard's own complexity wording for `nth_element`.
- [`heapq.nsmallest` — Python docs](https://docs.python.org/3/library/heapq.html#heapq.nsmallest) —
  the heap-based k-smallest-in-order routine and its O(n log k) note.

## Related Pages

- [Quicksort](./quicksort.md) — the partition step quickselect reuses, and the same adversarial-input
  weakness both algorithms share.
- [Choosing a Sort](./choosing-a-sort.md) — introselect's depth-limited fallback, the same defensive
  trick introsort applies to quicksort itself.
- [Heaps](../data-structures/heaps.md) — the structure behind `heapq.nsmallest`'s O(n log k) alternative
  when only a small, ordered top-k is needed.
- [Recurrences & the Master Theorem](../complexity/recurrences-and-master-theorem.md) — the general
  tool the geometric-series argument above is a specific instance of.
