---
id: selection-sort
title: Selection Sort
sidebar_label: Selection Sort
sidebar_position: 2
tags: [computer-science, algorithms, sorting, selection-sort]
---

# Selection Sort


Selection sort divides the array into a sorted prefix and an unsorted remainder. Each round it scans
the remainder for the smallest element and swaps it into place at the boundary.

It has one genuinely distinguishing property: it performs exactly **n − 1 swaps**, the minimum
possible for a sort that moves elements individually. Everything else about it is unremarkable.

<Figure src="/img/cs/algorithms/selection-sort.gif"
        alt="Animation of selection sort: a marker scans the unsorted portion to find the smallest bar, which is then swapped into the boundary position, growing the sorted region one element at a time"
        caption="Each round scans the whole remaining region for the minimum, then performs a single swap. The sorted prefix grows by exactly one element per round."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Selection-Sort-Animation.gif"
        license="CC BY-SA 3.0" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | $O(n^2)$ — no early exit is possible |
| Average | $O(n^2)$ |
| Worst case | $O(n^2)$ |
| Space | $O(1)$ |
| Stable | No (in the standard swap-based form) |
| Adaptive | No — sorted input costs exactly as much as random input |
| Swaps | **$O(n)$** — exactly n − 1 |

## Mechanism

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def selection_sort(a):
    n = len(a)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):        # scan the unsorted remainder
            if a[j] < a[smallest]:
                smallest = j
        if smallest != i:
            a[i], a[smallest] = a[smallest], a[i]    # one swap per round
    return a
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
void selection_sort(std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    for (int i = 0; i < n - 1; ++i) {
        int smallest = i;
        for (int j = i + 1; j < n; ++j)          // scan the unsorted remainder
            if (a[j] < a[smallest]) smallest = j;
        if (smallest != i)
            std::swap(a[i], a[smallest]);        // one swap per round
    }
}
```

</TabItem>
</Tabs>

The comparison count is fixed at `n(n−1)/2` regardless of input — the inner loop always runs to the
end, because you cannot know an element is the minimum until you have seen every candidate. This is
why there is no best case and no adaptivity.

Tracing `[5, 1, 4, 2]`:

| Round | Minimum found | Swap | Result |
|---|---|---|---|
| 1 | 1 at index 1 | 5 ↔ 1 | `[1, 5, 4, 2]` |
| 2 | 2 at index 3 | 5 ↔ 2 | `[1, 2, 4, 5]` |
| 3 | 4 at index 2 | none | `[1, 2, 4, 5]` |

### Why it is not stable

Swapping a distant minimum into position jumps it over intervening elements, which can reorder equal
values. With `[2a, 2b, 1]`, the first round swaps `1` with `2a`, giving `[1, 2b, 2a]` — the two `2`s
have exchanged their original order.

Stability is recoverable by shifting the intervening block instead of swapping, but that costs $O(n)$
writes per round and forfeits the algorithm's only advantage.

## Practical Usage

The reason to choose selection sort is when **writes are far more expensive than reads**:

- **EEPROM and flash memory** have limited erase/write endurance and slow writes, while reads are
  cheap. See [SSDs & NAND Flash](../../storage/ssd-and-nand-flash.md) — minimising writes is the
  whole design pressure there.
- **Very large records with small keys**, where each move copies a lot of bytes. Though in that case
  the better answer is usually to sort an array of indices or pointers instead, and permute once.

That is a narrow niche, and it is the entire case for this algorithm.

## Edge Cases & Pitfalls

- **No early exit exists.** Adding a "did anything change?" check does nothing, because the inner
  scan is unconditional. Sorted input costs full price.
- **Assuming it is stable** because it looks like it should be. It is not, and the failure appears
  only when sorting by a secondary key.
- **Selection sort and [heapsort](./heapsort.md) are the same idea.** Both repeatedly extract the
  extreme from the unsorted region; heapsort just uses a [heap](../data-structures/heaps.md) to find
  it in $O(\log n)$ instead of $O(n)$, which is exactly what converts $O(n^2)$ into $O(n \log n)$.

## Comparisons

| | Selection | [Bubble](./bubble-sort.md) | [Insertion](./insertion-sort.md) |
|---|---|---|---|
| Comparisons | n(n−1)/2 always | $O(n^2)$, $O(n)$ if sorted | $O(n^2)$, $O(n)$ if nearly sorted |
| Writes | **n − 1 swaps** | $O(n^2)$ | $O(n^2)$ |
| Best case | $O(n^2)$ | $O(n)$ | $O(n)$ |
| Stable | No | Yes | Yes |
| Choose when | Writes dominate cost | Never | Small or nearly-sorted input |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* — selection sort appears as Exercise 2.2-2, including the question of why the loop runs to n − 1 rather than n.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.1 — elementary sorts, with the write-count comparison made explicitly.

### Books & Videos

- [VisuAlgo — Sorting](https://visualgo.net/en/sorting) — compare the swap counts against the other elementary sorts on identical input.

## Related Pages

- [Heapsort](./heapsort.md) — selection sort with a heap doing the selection.
- [Insertion Sort](./insertion-sort.md) — the elementary sort to reach for by default.
