---
id: quicksort
title: Quicksort
sidebar_label: Quicksort
sidebar_position: 5
tags: [computer-science, algorithms, sorting, quicksort, divide-and-conquer]
---

# Quicksort


Quicksort picks an element as the **pivot**, rearranges the array so that everything smaller sits to
its left and everything larger to its right, then recurses on both sides. After partitioning, the
pivot is already in its final position and never moves again.

It is the mirror image of [mergesort](./mergesort.md): mergesort splits trivially and does its work
while combining, quicksort does its work while splitting and combines trivially. In practice
quicksort is usually the faster of the two, despite a worst case that is quadratic.

<Figure src="/img/cs/algorithms/quicksort-diagram.png"
        alt="A diagram of quicksort partitioning the list 3 7 8 5 2 1 9 5 4 around the pivot 4, moving smaller elements left and larger right, then recursing into each side until sorted"
        caption="Partitioning around the pivot 4. Once the pivot lands between the two groups it is in its final position; the algorithm then repeats on each side independently."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Quicksort-diagram.svg"
        license="Public domain" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | $O(n \log n)$ — balanced partitions |
| Average | $O(n \log n)$ |
| Worst case | **$O(n^2)$** — maximally unbalanced partitions |
| Space | $O(\log n)$ — recursion stack only |
| Stable | No |
| Adaptive | No (though [pdqsort](./choosing-a-sort.md) makes it partly so) |
| In place | **Yes** |

## Mechanism

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def quicksort(a, lo=0, hi=None):
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return a
    p = partition(a, lo, hi)
    quicksort(a, lo, p - 1)      # the pivot at p is already final
    quicksort(a, p + 1, hi)
    return a

def partition(a, lo, hi):
    """Lomuto scheme: pivot is the last element."""
    pivot = a[hi]
    i = lo                        # boundary of the "smaller than pivot" region
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]     # put the pivot between the two regions
    return i
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Lomuto scheme: pivot is the last element.
int partition(std::vector<int>& a, int lo, int hi) {
    int pivot = a[hi];
    int i = lo;                       // boundary of the "smaller than pivot" region
    for (int j = lo; j < hi; ++j) {
        if (a[j] < pivot) {
            std::swap(a[i], a[j]);
            ++i;
        }
    }
    std::swap(a[i], a[hi]);           // put the pivot between the two regions
    return i;
}

void quicksort(std::vector<int>& a, int lo, int hi) {
    if (lo >= hi) return;
    int p = partition(a, lo, hi);
    quicksort(a, lo, p - 1);          // the pivot at p is already final
    quicksort(a, p + 1, hi);
}

void quicksort(std::vector<int>& a) {
    quicksort(a, 0, static_cast<int>(a.size()) - 1);
}
```

</TabItem>
</Tabs>

<Figure src="/img/cs/algorithms/quicksort.gif"
        alt="Animation of quicksort on a set of bars, with a pivot chosen and elements swapped around it, then the same process repeating on each side"
        caption="Each pass partitions a region around one pivot. The recursion narrows until every region is a single element."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Sorting_quicksort_anim.gif"
        license="CC BY-SA 3.0" />

### Why it beats mergesort in practice despite equal complexity

- **In place.** No $O(n)$ buffer, and no allocation in the hot path.
- **Excellent locality.** Partitioning is two sequential scans converging on each other, which the
  [prefetcher](../../memory-hierarchy/cpu-caches.md) handles perfectly. Mergesort's merges are also
  sequential but write to a separate buffer, doubling memory traffic.
- **Tight inner loop.** A comparison, a conditional swap, and a pointer bump.

### The pivot choice is the whole game

The partition is balanced only if the pivot is near the median. Choosing badly gives partitions of
size 0 and n−1, which makes the recursion n levels deep and the cost $O(n^2)$.

| Pivot strategy | Worst case triggered by | Verdict |
|---|---|---|
| First or last element | **Already-sorted input** | Dangerous — the most common real input |
| Random element | Nothing predictable | Good; $O(n^2)$ becomes vanishingly unlikely |
| Median of three (first, middle, last) | Crafted "median-of-3 killer" inputs | Standard practice; cheap and effective |
| True median (median-of-medians) | Nothing — $O(n \log n)$ guaranteed | Too slow in practice |

:::danger[Naive quicksort is quadratic on sorted input]
Picking the first or last element as pivot means an already-sorted array partitions into an empty
side and everything else, every time — n levels of recursion, $O(n^2)$ comparisons, and $O(n)$ stack
depth, which on a large array is a stack overflow rather than merely slow.

Sorted or nearly-sorted input is extremely common. Never ship a quicksort with a fixed pivot
position; randomise it or use median-of-three.
:::

### Hoare partitioning

The Lomuto scheme above is easier to read, but Hoare's original does about three times fewer swaps
and handles duplicate-heavy input better:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def hoare_partition(a, lo, hi):
    pivot = a[(lo + hi) // 2]
    i, j = lo - 1, hi + 1
    while True:
        i += 1
        while a[i] < pivot:
            i += 1
        j -= 1
        while a[j] > pivot:
            j -= 1
        if i >= j:
            return j                  # note: returns a split point, not a pivot index
        a[i], a[j] = a[j], a[i]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int hoare_partition(std::vector<int>& a, int lo, int hi) {
    int pivot = a[lo + (hi - lo) / 2];
    int i = lo - 1, j = hi + 1;
    for (;;) {
        do { ++i; } while (a[i] < pivot);
        do { --j; } while (a[j] > pivot);
        if (i >= j) return j;         // note: returns a split point, not a pivot index
        std::swap(a[i], a[j]);
    }
}
```

</TabItem>
</Tabs>

Note the different contract — it returns a boundary, so the recursion becomes
`quicksort(a, lo, j)` and `quicksort(a, j + 1, hi)`, with no element excluded. Mixing up the two
schemes' contracts is a classic source of infinite recursion.

## Practical Usage

Production quicksorts are always hybrids:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def introsort(a, lo, hi, depth_budget):
    if hi - lo < 16:
        insertion_sort_range(a, lo, hi)          # small ranges: insertion sort wins
    elif depth_budget == 0:
        heapsort_range(a, lo, hi)                # too deep: bail out to a guaranteed O(n log n)
    else:
        p = partition(a, lo, hi)
        introsort(a, lo, p - 1, depth_budget - 1)
        introsort(a, p + 1, hi, depth_budget - 1)

# Entry point: budget of 2·log₂(n) partitions before giving up on quicksort
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
void introsort(std::vector<int>& a, int lo, int hi, int depth_budget) {
    if (hi - lo < 16) {
        insertion_sort_range(a, lo, hi);            // small ranges: insertion sort wins
    } else if (depth_budget == 0) {
        heapsort_range(a, lo, hi);                  // too deep: bail out to a guaranteed O(n log n)
    } else {
        int p = partition(a, lo, hi);
        introsort(a, lo, p - 1, depth_budget - 1);
        introsort(a, p + 1, hi, depth_budget - 1);
    }
}

// Entry point: budget of 2·log₂(n) partitions before giving up on quicksort
void introsort(std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    introsort(a, 0, n - 1, 2 * std::bit_width(static_cast<unsigned>(n)));
}
```

</TabItem>
</Tabs>

**Introsort** — this exact structure — is what C++'s `std::sort` uses. It keeps quicksort's speed
while making the $O(n^2)$ worst case unreachable, because exceeding the depth budget hands the range to
[heapsort](./heapsort.md).

Also worth knowing: **three-way partitioning** (into `< pivot`, `== pivot`, `> pivot`) turns arrays
with many duplicate keys from a weakness into an $O(n)$ best case. Without it, equal keys pile up on
one side.

## Edge Cases & Pitfalls

- **Tail-recursion on the larger side risks stack overflow.** Recurse into the *smaller* partition
  and loop on the larger, bounding stack depth to $O(\log n)$ even in the worst case.
- **`(lo + hi) // 2` can overflow** in fixed-width integer languages. Use `lo + (hi - lo) // 2`.
- **Quicksort is not stable**, and cannot cheaply be made so — partitioning moves elements across
  long distances. If stability matters, use [mergesort](./mergesort.md).
- **Many equal elements degrade two-way partitioning** to $O(n^2)$ in some schemes. Use three-way.

## Comparisons

| | Quicksort | [Mergesort](./mergesort.md) | [Heapsort](./heapsort.md) |
|---|---|---|---|
| Typical speed | **Fastest** | Good | Slowest |
| Worst case | $O(n^2)$ | $O(n \log n)$ | $O(n \log n)$ |
| Space | $O(\log n)$ | $O(n)$ | **$O(1)$** |
| Stable | No | **Yes** | No |
| Used by | C++ `std::sort`, Rust `sort_unstable` | Java objects, Python (as Timsort) | Introsort's fallback |

## References

- Hoare, C.A.R. (1961), "Algorithm 64: Quicksort", *Communications of the ACM* — the original.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 7 — quicksort, randomised quicksort, and the average-case analysis.
- Musser, D. (1997), ["Introspective Sorting and Selection Algorithms"](https://www.cs.rpi.edu/~musser/gp/introsort.ps) — the paper introducing introsort.

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — try it on sorted input with a first-element pivot to see the worst case appear.

## Related Pages

- [Mergesort](./mergesort.md) — the stable, guaranteed-$O(n \log n)$ counterpart.
- [Heapsort](./heapsort.md) — introsort's escape hatch.
- [Choosing a Sort](./choosing-a-sort.md) — what standard libraries actually ship.
