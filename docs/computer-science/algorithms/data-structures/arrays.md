---
id: arrays
title: Arrays & Dynamic Arrays
sidebar_label: Arrays & Dynamic Arrays
sidebar_position: 1
tags: [computer-science, algorithms, data-structures, arrays]
---

# Arrays & Dynamic Arrays

## Overview

An array is a block of contiguous memory holding equally-sized elements. That one property gives it
everything else: because element `i` lives at `base + i × element_size`, indexing is a single
multiply-and-add — genuinely O(1), with no search involved.

It is also the reason arrays are the default choice far more often than their complexity table
suggests. Contiguity is exactly what the [memory hierarchy](../../memory-hierarchy/cpu-caches.md) is
built to reward.

## Core Concepts

| Term | Meaning |
|---|---|
| **Static array** | Fixed capacity, decided at creation. C's `int a[100]`, Java's `new int[100]`. |
| **Dynamic array** | Grows as needed by reallocating. Python `list`, C++ `std::vector`, Java `ArrayList`, Go slice. |
| **Capacity vs. size** | Capacity is how many elements fit before reallocating; size is how many are actually stored. |
| **Row-major / column-major** | For 2-D arrays, whether consecutive memory holds a row or a column. C and Python are row-major; Fortran and MATLAB are column-major. |

## Architecture / Mechanism

### Why indexing is O(1)

```text
int array of 4-byte elements, base address 0x1000

index:      0        1        2        3        4
address: 0x1000   0x1004   0x1008   0x100C   0x1010
              └── address = 0x1000 + index × 4 ──┘
```

No traversal, no comparison — arithmetic. This also means an array must know its element size at
compile time, which is why an array of *objects* in most managed languages is really an array of
references, with the objects themselves scattered across the heap.

### Growth: how a dynamic array stays amortized O(1)

Appending is cheap until capacity is exhausted, at which point the whole buffer is reallocated and
copied:

```python showLineNumbers
# Conceptually, what append does
def append(self, value):
    if self.size == self.capacity:
        self.capacity = max(1, self.capacity * 2)   # the factor matters
        new_buffer = allocate(self.capacity)
        copy(self.buffer, new_buffer, self.size)    # O(n), but rare
        self.buffer = new_buffer
    self.buffer[self.size] = value
    self.size += 1
```

Doubling means resizes happen at sizes 1, 2, 4, 8, …, n, copying fewer than `2n` elements in total
across n appends — **O(1) amortized**. Growing by a fixed amount instead (say +10 each time) makes
resizes just as frequent as the array grows, giving O(n) amortized per append.

| Language | Growth factor |
|---|---|
| C++ `std::vector` (libstdc++, libc++) | 2× |
| Java `ArrayList` | 1.5× |
| Python `list` | ~1.125× plus a constant (a gentler curve, tuned for memory) |
| Go slices | 2× while small, tapering toward 1.25× for large slices |

:::info[Why not always 2×?]
A growth factor of 2 can never reuse the memory it previously freed — the sum of all earlier blocks
is always just short of the next request. Factors below the golden ratio (~1.618) eventually allow
the allocator to reuse that freed space, which is the argument for 1.5×. It is a memory-fragmentation
trade, not a speed one.
:::

## Practical Usage

```python showLineNumbers
# Reserve capacity when the final size is known — avoids repeated reallocation
result = [None] * n          # Python: allocate once
# C++: v.reserve(n);   Java: new ArrayList<>(n);   Go: make([]int, 0, n)

# Iterate in memory order. This nesting is right for row-major languages:
for row in range(rows):
    for col in range(cols):
        total += matrix[row][col]      # consecutive addresses

# Reversing the loops touches memory with a stride of `cols` elements,
# wasting most of every cache line fetched — often several times slower
# on large matrices for identical arithmetic.
```

Removing from the middle of an array is O(n) because everything after the gap shifts down. When
order does not matter, swapping the last element into the hole makes it O(1):

```python showLineNumbers
def remove_unordered(items, i):
    items[i] = items[-1]     # overwrite the hole with the last element
    items.pop()              # then drop the (now duplicated) tail
```

## Edge Cases & Pitfalls

:::danger[Holding a pointer across a growth is a use-after-free]
In C++, any operation that may reallocate a `vector` — `push_back`, `insert`, `resize` — invalidates
every pointer, reference and iterator into it. The classic bug:

```cpp showLineNumbers
std::vector<int> v = {1, 2, 3};
int& first = v[0];
v.push_back(4);        // may reallocate; `first` now dangles
first = 99;            // undefined behaviour
```

Python and Java are safe from this specific fault because their elements are references and the GC
tracks them, but the equivalent logical bug — caching an index that a later removal invalidates —
survives in every language.
:::

- **Two-dimensional does not mean contiguous.** `int**` in C, or a Python list of lists, is an array
  of pointers to separately-allocated rows. Only a true `int[N][M]` (or NumPy array) is one flat
  block, and only that one gets the cache behaviour described above.
- **Insertion at the front is O(n)** for a dynamic array. If you need it often, use a
  [deque](./stacks-and-queues.md), not a list.
- **`list.pop(0)` in Python is O(n)**, and inside a loop it silently turns a linear algorithm
  quadratic — `collections.deque.popleft()` is the O(1) form.

## Comparisons

| | Array | [Linked list](./linked-lists.md) |
|---|---|---|
| Index access | O(1) | O(n) |
| Insert/delete at a known position | O(n) | O(1) |
| Memory per element | Element only | Element + one or two pointers |
| Locality | Contiguous — prefetches perfectly | Scattered — a cache miss per node |
| Realistic verdict | The default | Only when splicing dominates and you already hold the node |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 16 — amortized analysis, including the table-doubling argument in full.
- [CPython list implementation notes](https://github.com/python/cpython/blob/main/Objects/listobject.c) — the actual over-allocation formula, in the source.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 — resizing arrays and the amortized cost analysis.

## Related Pages

- [Linked Lists](./linked-lists.md) — the contrasting layout, and when it actually wins.
- [Common Complexities](../complexity/common-complexities.md) — where the amortized-O(1) argument is developed.
- [CPU Caches](../../memory-hierarchy/cpu-caches.md) — why contiguity is worth so much more than the operation counts imply.
