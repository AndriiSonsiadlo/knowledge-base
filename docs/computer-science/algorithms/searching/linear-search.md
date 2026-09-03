---
id: linear-search
title: Linear Search
sidebar_label: Linear Search
sidebar_position: 1
tags: [computer-science, algorithms, searching, linear-search]
---

# Linear Search

Linear search examines each element in turn until it finds what it is looking for or runs out. It is
the only search that works on **any** sequence with no preconditions whatsoever — unsorted, singly
linked, streamed, or generated lazily.

Its reputation as the naive option is only half deserved. On small inputs it is genuinely the fastest
option available, for reasons that have nothing to do with complexity.

## Core Concepts

| Property | Value |
|---|---|
| Best case | $O(1)$ — the target is first |
| Average | $O(n/2)$ → $O(n)$ |
| Worst case | $O(n)$ — last, or absent |
| Space | $O(1)$ |
| Requires | Nothing — not even random access |
| Works on | Arrays, linked lists, streams, generators, any iterable |

## Mechanism

Scanning `[5, 1, 8, 3]` for two different targets shows both outcomes — a hit partway through, and an
exhaustive miss:

```text
items = [5, 1, 8, 3]

search for 8:
  i=0  items[0]=5  5 != 8, continue
  i=1  items[1]=1  1 != 8, continue
  i=2  items[2]=8  8 == 8, return 2

search for 7:
  i=0  items[0]=5  5 != 7, continue
  i=1  items[1]=1  1 != 7, continue
  i=2  items[2]=8  8 != 7, continue
  i=3  items[3]=3  3 != 7, continue
  i=4  past the end, return -1
```

The hit terminates after 3 comparisons — it never has to look at the whole array. The miss is the true
worst case: every element is examined exactly once before the loop can conclude the target is absent.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def linear_search(items, target):
    for i, x in enumerate(items):
        if x == target:
            return i
    return -1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cstddef>
#include <vector>

int linear_search(const std::vector<int>& items, int target) {
    for (std::size_t i = 0; i < items.size(); ++i)
        if (items[i] == target) return static_cast<int>(i);
    return -1;
}
```

</TabItem>
</Tabs>

There is nothing more to the algorithm. What is worth noting is the generalisation: because it never
assumes an ordering, the comparison can be **any predicate**, not just equality.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# doc:no-run
# Binary search cannot do this — there is no ordering to exploit
first_error = next((r for r in records if r.status >= 500), None)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
// Binary search cannot do this — there is no ordering to exploit
auto first_error = std::find_if(records.begin(), records.end(),
                                 [](const Record& r) { return r.status >= 500; });
// first_error == records.end() when no record matches
```

</TabItem>
</Tabs>

That is the real dividing line between the two searches. [Binary search](./binary-search.md) needs a
property that partitions the sequence monotonically; linear search needs nothing.

## Practical Usage

:::tip[Linear search wins on small arrays, and by more than you would expect]
Below roughly 50–100 elements, a linear scan typically beats a binary search on real hardware. Three
reasons, none of them visible in the complexity:

- **Sequential access.** The scan walks contiguous memory, so the
  [prefetcher](../../memory-hierarchy/cpu-caches.md) has the next cache line ready before it is
  asked. Binary search jumps to the middle, then a quarter, then an eighth — each a likely cache
  miss.
- **Branch prediction.** The loop's "keep going" branch is taken almost every iteration and predicts
  nearly perfectly. Binary search's "go left or right" is close to random and mispredicts about half
  the time, costing 10–20 cycles each.
- **No setup.** No index arithmetic, no bounds juggling.

This is exactly why hybrid sorts fall back to [insertion sort](../sorting/insertion-sort.md) at small
sizes, and why hash table implementations scan short chains rather than indexing them.
:::

Where linear search is the right choice regardless of size:

- **The data is unsorted and used once.** Sorting to search once is strictly worse.
- **The predicate is not an ordering.** "First record matching this regex" has no sorted form.
- **The sequence is not random-access** — a [linked list](../data-structures/linked-lists.md) or a
  stream. Binary search on a linked list would cost $O(n)$ per probe, making it *worse* than scanning.
- **The data does not exist yet.** Searching a generator or a network stream as it arrives.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Sentinel search: remove the bounds check by guaranteeing a match
def sentinel_search(a, target):
    last = a[-1]
    a[-1] = target                  # the scan is now guaranteed to terminate
    i = 0
    while a[i] != target:
        i += 1
    a[-1] = last
    return i if i < len(a) - 1 or last == target else -1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Sentinel search: remove the bounds check by guaranteeing a match
int sentinel_search(std::vector<int>& a, int target) {
    int n = static_cast<int>(a.size());
    int last = a[n - 1];
    a[n - 1] = target;              // the scan is now guaranteed to terminate
    int i = 0;
    while (a[i] != target) ++i;
    a[n - 1] = last;
    return (i < n - 1 || last == target) ? i : -1;
}
```

</TabItem>
</Tabs>

The sentinel trick removes one comparison per iteration. It is a genuine micro-optimisation in tight
C loops and a curiosity everywhere else — modern compilers and branch predictors have largely erased
the gain, and it mutates the array, which rules it out for shared or immutable data.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# both functions, checked on the traced input
assert linear_search([5, 1, 8, 3], 8) == 2     # hit at index 2, 3 comparisons
assert linear_search([5, 1, 8, 3], 7) == -1    # miss: all 4 elements examined
assert sentinel_search([5, 1, 8, 3], 8) == 2
assert sentinel_search([5, 1, 8, 3], 7) == -1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert(linear_search({5, 1, 8, 3}, 8) == 2);
    assert(linear_search({5, 1, 8, 3}, 7) == -1);
    std::vector<int> a{5, 1, 8, 3};
    assert(sentinel_search(a, 8) == 2);
    std::vector<int> b{5, 1, 8, 3};
    assert(sentinel_search(b, 7) == -1);
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Returning `0` for "not found"** collides with a valid index. Return `-1`, `None`, or an optional
  type — and be consistent across the codebase.
- **Repeated linear searches inside a loop** silently make the enclosing algorithm $O(n^2)$. This is the
  single most common cause of accidental quadratic behaviour, and the fix is almost always a
  [hash table](../data-structures/hash-tables.md) — see the `two_sum` example there.
- **`in` on a list is $O(n)$**; on a set or dict it is $O(1)$. In Python they look identical at the call
  site, which is what makes the mistake easy.
- **Duplicates.** Decide whether you want the first match, the last, or all of them.

## Comparisons

| | Linear | [Binary](./binary-search.md) | [Hash](../data-structures/hash-tables.md) |
|---|---|---|---|
| Per lookup | $O(n)$ | $O(\log n)$ | $O(1)$ expected |
| Preparation | None | Sort: $O(n \log n)$ | Build: $O(n)$ |
| Requires sorted data | No | **Yes** | No |
| Requires random access | No | **Yes** | No |
| Arbitrary predicates | **Yes** | Only monotonic ones | Exact keys only |
| Best for | Small, unsorted, or one-shot | Many lookups, static sorted data | Many lookups by exact key |

## Recall

<Recall
  invariant="Linear search assumes nothing about ordering — it can run on any iterable and test any predicate, which is exactly what binary search cannot do."
  costs={[
    ["best case", "O(1)"],
    ["average case", "O(n)"],
    ["worst case", "O(n)"],
    ["extra space", "O(1)"],
  ]}
  reachFor="Unsorted or one-shot data, a predicate that is not an ordering, or a sequence without random access (a linked list or a stream)."
  trap="Running a linear search inside a loop, once per outer iteration, silently turns an O(n) algorithm into O(n^2) — the classic accidental-quadratic bug."
/>

## References

- Knuth, *The Art of Computer Programming*, Vol. 3, 2nd ed., §6.1 — "Sequential Searching", including the sentinel variant and its analysis.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed. — linear search appears as Exercise 2.1-3, with its loop invariant.

## Related Pages

- [Binary Search](./binary-search.md) — the logarithmic alternative, and what it demands in return.
- [Hash Tables](../data-structures/hash-tables.md) — the usual fix when a linear search sits inside a loop.
- [CPU Caches](../../memory-hierarchy/cpu-caches.md) — why the constant factors favour scanning at small sizes.
