---
id: binary-search
title: Binary Search
sidebar_label: Binary Search
sidebar_position: 2
tags: [computer-science, algorithms, searching, binary-search]
---

# Binary Search


Binary search compares the target against the middle element of a **sorted** array and discards half
the remaining range at every step. Twenty steps suffice for a million elements; thirty for a billion.

It is also famously difficult to write correctly. Jon Bentley reported that 90% of professional
programmers failed to produce a correct version given several hours, and the implementation in the
JDK carried an overflow bug from 1997 until 2006. The idea is simple; the boundary conditions are
not.

<Figure src="/img/cs/algorithms/binary-search.png"
        alt="A sorted array of seventeen values with arrows showing a search narrowing from the middle element 14 to 6, then to 8, then arriving at 7"
        caption="Searching for 7. Each probe eliminates half of what remains: 17 candidates, then 8, then 3, then 1 — four comparisons instead of seventeen."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Binary_Search_Depiction.svg"
        license="CC BY-SA 4.0" />

## Core Concepts

| Property | Value |
|---|---|
| Best case | $O(1)$ — the target is the first midpoint |
| Average / worst | $O(\log n)$ |
| Space | $O(1)$ iterative, $O(\log n)$ recursive |
| **Requires** | Sorted data **and** $O(1)$ random access |
| Comparisons | ⌊log₂ n⌋ + 1 in the worst case |

## Mechanism

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def binary_search(a, target):
    lo, hi = 0, len(a) - 1          # inclusive bounds
    while lo <= hi:                 # <= because lo == hi is a valid range of one
        mid = lo + (hi - lo) // 2   # overflow-safe midpoint
        if a[mid] == target:
            return mid
        if a[mid] < target:
            lo = mid + 1            # +1: mid is excluded, guaranteeing progress
        else:
            hi = mid - 1
    return -1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int binary_search(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;   // inclusive bounds
    while (lo <= hi) {                  // <= because lo == hi is a valid range of one
        int mid = lo + (hi - lo) / 2;   // overflow-safe midpoint
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;   // +1: mid is excluded, guaranteeing progress
        else                 hi = mid - 1;
    }
    return -1;
}
```

</TabItem>
</Tabs>

Every line above is where implementations go wrong:

| Detail | Why it matters |
|---|---|
| `lo + (hi - lo) // 2` | `(lo + hi) // 2` overflows for large arrays in fixed-width integer languages. This was the JDK bug. |
| `while lo <= hi` | With inclusive bounds, `lo == hi` still holds one unchecked element. `<` skips it. |
| `mid + 1` / `mid - 1` | Assigning `lo = mid` when `lo == mid` loops forever. The ±1 guarantees the range shrinks. |

:::tip[Pick one convention and never mix them]
Inclusive bounds (`hi = len - 1`, `while lo <= hi`, `hi = mid - 1`) and half-open bounds
(`hi = len`, `while lo < hi`, `hi = mid`) are both correct. Bugs come from combining halves of the
two. The half-open form generalises better to the boundary-finding variants below, which is why
`bisect` and `lower_bound` use it.
:::

### The variant that matters more: finding a boundary

Exact-match search is the least useful form. Far more often you want the **insertion point** — the
first position where a predicate becomes true. This version never terminates early, always converges
on a boundary, and handles duplicates and absent values uniformly:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def lower_bound(a, target):
    """Index of the first element >= target. Returns len(a) if none."""
    lo, hi = 0, len(a)              # half-open: hi is one past the end
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid                # no -1: mid may itself be the answer
    return lo
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Index of the first element >= target. Returns a.size() if there is none.
std::size_t lower_bound(const std::vector<int>& a, int target) {
    std::size_t lo = 0, hi = a.size();       // half-open: hi is one past the end
    while (lo < hi) {
        std::size_t mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1;
        else                 hi = mid;       // no -1: mid may itself be the answer
    }
    return lo;
}
```

</TabItem>
</Tabs>

From `lower_bound` everything else follows: `a[i] == target` tests membership, `upper_bound - lower_bound`
counts occurrences, and the returned index is exactly where an insert would preserve order.

### Binary searching an answer, not an array

The technique applies to any **monotonic predicate** — any question whose answer, once true, stays
true. The "array" can be a range of candidate answers that is never materialised:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Smallest capacity that ships all packages within `days`
def min_capacity(weights, days):
    def feasible(cap):              # monotonic: if cap works, cap+1 works
        needed, load = 1, 0
        for w in weights:
            if load + w > cap:
                needed, load = needed + 1, 0
            load += w
        return needed <= days

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Smallest capacity that ships all packages within `days`
int min_capacity(const std::vector<int>& weights, int days) {
    auto feasible = [&](int cap) {           // monotonic: if cap works, cap+1 works
        int needed = 1, load = 0;
        for (int w : weights) {
            if (load + w > cap) { ++needed; load = 0; }
            load += w;
        }
        return needed <= days;
    };

    int lo = *std::max_element(weights.begin(), weights.end());
    int hi = std::accumulate(weights.begin(), weights.end(), 0);
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (feasible(mid)) hi = mid;
        else               lo = mid + 1;
    }
    return lo;
}
```

</TabItem>
</Tabs>

This "binary search on the answer" pattern turns an optimisation problem into $O(\log(\text{range}))$ feasibility
checks, and it is one of the highest-value techniques in competitive programming and in real capacity
planning alike.

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import bisect

i = bisect.bisect_left(a, x)         # lower_bound — first index where a[i] >= x
j = bisect.bisect_right(a, x)        # upper_bound — first index where a[i] > x
count = j - i                        # occurrences of x
found = i < len(a) and a[i] == x     # membership test

bisect.insort(a, x)                  # insert, keeping the list sorted (O(n) for the shift)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
auto i = std::lower_bound(a.begin(), a.end(), x);   // first position with *i >= x
auto j = std::upper_bound(a.begin(), a.end(), x);   // first position with *j > x
auto count = j - i;                                 // occurrences of x
bool found = std::binary_search(a.begin(), a.end(), x);    // membership test

a.insert(std::lower_bound(a.begin(), a.end(), x), x);      // insert, keeping it sorted (O(n) for the shift)
```

</TabItem>
</Tabs>

Equivalents elsewhere: C++ `std::lower_bound`/`upper_bound`/`equal_range`, Java
`Arrays.binarySearch` (which returns `-(insertion point) - 1` when absent), Rust
`slice::binary_search` (returning `Result<usize, usize>` — the cleanest of these designs).

## Edge Cases & Pitfalls

:::danger[Binary search on unsorted data does not fail — it returns garbage]
There is no check and no error. It silently returns a wrong index or "not found" for a value that is
present, and the bug survives testing because it is data-dependent. If a sort was supposed to happen
earlier and did not, this is where it surfaces — as a wrong answer, far from the cause.
:::

- **`(lo + hi) // 2` overflow** — real in C, C++, Java and Rust. Python's unbounded integers make it
  safe there, which is why the habit does not transfer.
- **Which duplicate you get is unspecified** for exact-match search. Use `lower_bound`/`upper_bound`
  when it matters.
- **Binary search on a [linked list](../data-structures/linked-lists.md) is pointless** — reaching
  the midpoint is $O(n)$, making the whole search $O(n \log n)$, worse than a plain scan.
- **Below ~50 elements a [linear scan](./linear-search.md) is usually faster** on real hardware, for
  cache and branch-prediction reasons.
- **Floating-point ranges never converge with `lo < hi`.** Iterate a fixed number of times (100 is
  ample) or compare against an epsilon.

## Comparisons

| | Binary search | [Linear search](./linear-search.md) | [Hash table](../data-structures/hash-tables.md) |
|---|---|---|---|
| Per lookup | $O(\log n)$ | $O(n)$ | $O(1)$ expected |
| Sorted input needed | **Yes** | No | No |
| Random access needed | **Yes** | No | No |
| Range / nearest-match queries | **Yes** | No | No |
| Insertion into the structure | $O(n)$ | $O(1)$ at the end | $O(1)$ |

## References

- Bentley, J., *Programming Pearls*, Ch. 4 — the correctness argument, and the source of the "90% get it wrong" figure.
- Bloch, J. (2006), ["Extra, Extra — Read All About It: Nearly All Binary Searches and Mergesorts are Broken"](https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/) — the JDK overflow bug.
- Knuth, *The Art of Computer Programming*, Vol. 3, §6.2.1 — binary search and its variants in full.

### Books & Videos

- [Python `bisect` documentation](https://docs.python.org/3/library/bisect.html) — includes recipes for the boundary variants above.

## Related Pages

- [Linear Search](./linear-search.md) — the no-preconditions alternative.
- [Sorting Algorithms](../sorting/intro.md) — the prerequisite step.
- [Balanced Trees](../data-structures/balanced-trees.md) — binary search made incrementally updatable.
