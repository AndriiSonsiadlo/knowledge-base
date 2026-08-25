---
id: heapsort
title: Heapsort
sidebar_label: Heapsort
sidebar_position: 6
tags: [computer-science, algorithms, sorting, heapsort, heap]
---

# Heapsort


Heapsort is [selection sort](./selection-sort.md) with a better way of selecting. Selection sort scans
the unsorted region to find its maximum in O(n); heapsort keeps that region as a
[heap](../data-structures/heaps.md) so the maximum is at the root and extraction costs O(log n).
That single substitution converts O(n²) into O(n log n).

Its distinguishing property is the combination no other common sort offers: **O(n log n) worst case
in O(1) space**. [Mergesort](./mergesort.md) needs a buffer; [quicksort](./quicksort.md) has a
quadratic worst case; heapsort has neither problem.

<Figure src="/img/cs/algorithms/heapsort.gif"
        alt="Animation of heapsort: the bars are first rearranged into a heap, then the largest is repeatedly swapped to the end and the heap restored over the shrinking remainder"
        caption="Two phases. First the array becomes a heap; then the root is repeatedly swapped to the end, shrinking the heap and growing the sorted tail."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Sorting_heapsort_anim.gif"
        license="CC BY-SA 3.0" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | O(n log n) |
| Average | O(n log n) |
| Worst case | **O(n log n)** — guaranteed |
| Space | **O(1)** — genuinely in place, no recursion |
| Stable | No |
| Adaptive | No — sorted input costs the same as random |

## Architecture / Mechanism

The array is used as both the heap and the output. The heap occupies a shrinking prefix; the sorted
result grows as a suffix behind it.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def heapsort(a):
    n = len(a)

    # Phase 1: build a max-heap in place — O(n), not O(n log n)
    for i in range(n // 2 - 1, -1, -1):
        sift_down(a, i, n)

    # Phase 2: repeatedly move the max to the end and shrink the heap
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]     # largest element to its final position
        sift_down(a, 0, end)            # restore the heap over the remaining prefix
    return a

def sift_down(a, i, size):
    while True:
        largest = i
        for child in (2 * i + 1, 2 * i + 2):
            if child < size and a[child] > a[largest]:
                largest = child
        if largest == i:
            return
        a[i], a[largest] = a[largest], a[i]
        i = largest
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
void sift_down(std::vector<int>& a, int i, int size) {
    for (;;) {
        int largest = i;
        for (int child : {2 * i + 1, 2 * i + 2})
            if (child < size && a[child] > a[largest]) largest = child;
        if (largest == i) return;
        std::swap(a[i], a[largest]);
        i = largest;
    }
}

void heapsort(std::vector<int>& a) {
    int n = static_cast<int>(a.size());

    // Phase 1: build a max-heap in place — O(n), not O(n log n)
    for (int i = n / 2 - 1; i >= 0; --i)
        sift_down(a, i, n);

    // Phase 2: repeatedly move the max to the end and shrink the heap
    for (int end = n - 1; end > 0; --end) {
        std::swap(a[0], a[end]);        // largest element to its final position
        sift_down(a, 0, end);           // restore the heap over the remaining prefix
    }
}
```

</TabItem>
</Tabs>

Phase 1 is O(n) — see the [heaps page](../data-structures/heaps.md) for why building a heap is linear
rather than n log n. Phase 2 does n extractions at O(log n) each, so it dominates: **O(n log n)**
overall.

Using a **max**-heap rather than a min-heap is what makes the sort ascending: the largest element is
swapped to the *end*, and each subsequent one lands just before it.

## Practical Usage

Heapsort is rarely the top-level choice, but it occupies two important roles:

- **The safety net in introsort.** C++'s `std::sort` runs quicksort, and switches to heapsort when
  recursion exceeds `2·log₂ n` levels. This makes the worst case O(n log n) without giving up
  quicksort's speed on typical input. Heapsort is chosen for the fallback precisely because it needs
  no extra memory and has no bad case of its own.
- **Memory-constrained and real-time systems.** Embedded and kernel contexts where an O(n) allocation
  is unacceptable and an O(n²) tail is unacceptable. The Linux kernel's `sort()` is a heapsort.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Partial sorting: the top k without sorting everything — O(n + k log n)
import heapq
def top_k(items, k):
    heap = list(items)
    heapq.heapify(heap)                       # O(n)
    return [heapq.heappop(heap) for _ in range(k)]   # k × O(log n)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Partial sorting: the top k without sorting everything — O(n + k log n)
std::vector<int> top_k(std::vector<int> items, int k) {
    std::priority_queue<int, std::vector<int>, std::greater<>>
        heap(std::greater<>{}, std::move(items));          // heapify: O(n)
    std::vector<int> out;
    for (int i = 0; i < k && !heap.empty(); ++i) {         // k x O(log n)
        out.push_back(heap.top());
        heap.pop();
    }
    return out;
}
```

</TabItem>
</Tabs>

Stopping phase 2 after k extractions gives the k largest elements in O(n + k log n) — better than a
full sort when k is small, which is the same argument behind `heapq.nlargest`.

## Edge Cases & Pitfalls

:::warning[Heapsort is the slowest O(n log n) sort in practice]
Its complexity is excellent and its constant factor is not. `sift_down` jumps between indices `i`,
`2i+1` and `2i+2` — locations that grow exponentially far apart, so each level of a sift is a fresh
[cache miss](../../memory-hierarchy/cpu-caches.md). Quicksort's partition scans memory sequentially
and mergesort's merges are also sequential; heapsort's access pattern is nearly the worst possible.

On typical in-memory arrays it commonly runs 2–3× slower than quicksort despite identical asymptotic
complexity. Choose it for its guarantees, not for its speed.
:::

- **`n // 2 - 1` is the last internal node.** Starting the build loop anywhere else either wastes
  work on leaves or leaves part of the heap unbuilt.
- **`sift_down` must be bounded by `size`, not `len(a)`** — otherwise phase 2 sifts back into the
  already-sorted suffix and corrupts it.
- **It is not stable**, and equal elements are reordered by the long-distance swaps.
- **A min-heap sorts descending.** If you want ascending output, build a max-heap.

## Comparisons

| | Heapsort | [Quicksort](./quicksort.md) | [Mergesort](./mergesort.md) | [Selection](./selection-sort.md) |
|---|---|---|---|---|
| Worst case | **O(n log n)** | O(n²) | **O(n log n)** | O(n²) |
| Space | **O(1)** | O(log n) | O(n) | O(1) |
| Stable | No | No | **Yes** | No |
| Locality | **Poor** | Excellent | Good | Good |
| Typical speed | Slowest of the three | **Fastest** | Good | Very slow |
| Choose when | Guarantees + no memory | Default for arrays | Stability or external sort | Writes are costly |

## References

- Williams, J.W.J. (1964), "Algorithm 232: Heapsort", *Communications of the ACM* — the original, which introduced the heap along with it.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 6 — heapsort with the O(n) build-heap proof.
- [Linux kernel `lib/sort.c`](https://github.com/torvalds/linux/blob/master/lib/sort.c) — a production heapsort, with comments on why it was chosen.

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — the two phases are much clearer watched than read.

## Related Pages

- [Heaps & Priority Queues](../data-structures/heaps.md) — the structure this is built on.
- [Selection Sort](./selection-sort.md) — the same algorithm with a linear scan instead of a heap.
- [Choosing a Sort](./choosing-a-sort.md) — introsort, where heapsort is the fallback.
