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

Searching `[1, 3, 5, 8]` for a value that is present, then one that is absent, shows both outcomes of
the exact-match loop below — tracking `lo`, `mid`, and `hi` at the start of each iteration:

```text
a = [1, 3, 5, 8]   (indices 0, 1, 2, 3)

search for 5:
  lo=0  hi=3  mid=1  a[1]=3 < 5  -> lo = mid+1 = 2
  lo=2  hi=3  mid=2  a[2]=5 == 5 -> return 2

search for 4:
  lo=0  hi=3  mid=1  a[1]=3 < 4  -> lo = mid+1 = 2
  lo=2  hi=3  mid=2  a[2]=5 > 4  -> hi = mid-1 = 1
  lo=2  hi=1  lo > hi, loop ends -> return -1
```

Finding 5 takes two probes because the second one lands exactly on the target. Looking for 4 — a value
that would sit between indices 1 and 2 — narrows the range until `lo` crosses `hi`, which is exactly
the termination condition proving no such index exists.

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
#include <cassert>
#include <cstddef>
#include <vector>

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
| `lo + (hi - lo) // 2` | `(lo + hi) // 2` overflows for large arrays in fixed-width integer languages — see [Integers & Two's Complement](../../bit-manipulation/integers-and-twos-complement.md) for why `lo + hi` can exceed the type's range while neither `lo` nor `hi` does. This was the JDK bug. |
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
first position where a predicate becomes true. There are exactly four boundary variants anyone ever
needs, and they are all **one template**:

```text
lo, hi = 0, len(a)                  # half-open: hi is one past the end
while lo < hi:
    mid = lo + (hi - lo) // 2
    if <predicate>(a[mid]):
        hi = mid                    # a[mid] already satisfies it — it or something left of it is the answer
    else:
        lo = mid + 1
return lo                           # first index where <predicate> holds, or len(a) if none does
```

The predicate and what you do with the returned `lo` are the *only* things that change:

| Variant | Predicate `<predicate>(a[mid])` | Answer |
|---|---|---|
| First index `>= target` (`lower_bound`) | `a[mid] >= target` | `lo` |
| First index `> target` (`upper_bound`) | `a[mid] > target` | `lo` |
| Last index `< target` | `a[mid] >= target` | `lo - 1` |
| Last index `<= target` | `a[mid] > target` | `lo - 1` |

The "last" variants are not separate loops — they are the "first" loop's answer, one position to the
left, because "the last index where the predicate is false" is one less than "the first index where it
is true." This is what makes the half-open template worth memorising over the inclusive-bounds one:
every boundary question reduces to picking a predicate and, optionally, subtracting one.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def first_true(a, predicate):
    """Index of the first element for which predicate(a[i]) is True. len(a) if none."""
    lo, hi = 0, len(a)              # half-open: hi is one past the end
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if predicate(a[mid]):
            hi = mid                # a[mid] already satisfies it
        else:
            lo = mid + 1
    return lo


def lower_bound(a, target):
    return first_true(a, lambda v: v >= target)


def upper_bound(a, target):
    return first_true(a, lambda v: v > target)


def last_less_than(a, target):
    return lower_bound(a, target) - 1


def last_less_or_equal(a, target):
    return upper_bound(a, target) - 1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
template <typename Pred>
std::size_t first_true(const std::vector<int>& a, Pred predicate) {
    std::size_t lo = 0, hi = a.size();       // half-open: hi is one past the end
    while (lo < hi) {
        std::size_t mid = lo + (hi - lo) / 2;
        if (predicate(a[mid])) hi = mid;     // a[mid] already satisfies it
        else                   lo = mid + 1;
    }
    return lo;
}

std::size_t lower_bound_impl(const std::vector<int>& a, int target) {
    return first_true(a, [target](int v) { return v >= target; });
}

std::size_t upper_bound_impl(const std::vector<int>& a, int target) {
    return first_true(a, [target](int v) { return v > target; });
}
```

</TabItem>
</Tabs>

From `lower_bound` everything else follows: `a[i] == target` tests membership, `upper_bound - lower_bound`
counts occurrences, and the returned index is exactly where an insert would preserve order.

### Binary searching an answer, not an array

The same half-open template applies to any **monotonic predicate** — any question whose answer, once
true, stays true — even when the "array" is a range of candidate answers that is never materialised,
such as "smallest capacity that ships all packages within `days`." See
[Binary Search on the Answer](./binary-search-on-answer.md) for the full pattern: rate problems, the
floating-point variant, and its stopping rule.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# all four boundary variants, checked on the traced input
assert binary_search([1, 3, 5, 8], 5) == 2      # the traced hit
assert binary_search([1, 3, 5, 8], 4) == -1     # the traced miss
assert lower_bound([1, 3, 5, 8], 5) == 2
assert upper_bound([1, 3, 5, 8], 5) == 3
assert last_less_than([1, 3, 5, 8], 5) == 1     # index of 3
assert last_less_or_equal([1, 3, 5, 8], 5) == 2 # index of 5 itself
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert((binary_search({1, 3, 5, 8}, 5) == 2));
    assert((binary_search({1, 3, 5, 8}, 4) == -1));
    assert((lower_bound_impl({1, 3, 5, 8}, 5) == 2));
    assert((upper_bound_impl({1, 3, 5, 8}, 5) == 3));
}
```

</TabItem>
</Tabs>

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# doc:no-run
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
// doc:no-run
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

## Recall

<Recall
  invariant="Every boundary variant (first >=, first >, last <, last <=) is the same half-open template — lo, hi = 0, len(a); shrink toward the first index where a predicate holds — differing only in the predicate and whether you subtract one from lo."
  costs={[
    ["best case", "O(1)"],
    ["average / worst case", "O(log n)"],
    ["comparisons, worst case", "floor(log2 n) + 1"],
    ["extra space (iterative / recursive)", "O(1) / O(log n)"],
  ]}
  reachFor="Sorted, random-access data queried many times — or any monotonic predicate over a range of candidate answers, not just an array."
  trap="`(lo + hi) // 2` overflows in fixed-width integer languages; use `lo + (hi - lo) // 2`. This exact bug shipped in the JDK for nine years."
/>

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
