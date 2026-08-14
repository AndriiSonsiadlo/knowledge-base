---
id: common-complexities
title: Common Complexities
sidebar_label: Common Complexities
sidebar_position: 2
tags: [computer-science, algorithms, complexity, amortized, space-complexity]
---

# Common Complexities

## Overview

In practice you meet perhaps eight growth classes. Recognising which one a piece of code falls into —
and, more usefully, recognising the *problem shape* that produces each — is most of what complexity
analysis is for day to day.

## Core Concepts

| Class | Name | Produced by | Example |
|---|---|---|---|
| **O(1)** | Constant | Direct addressing; a fixed amount of work | Array index, hash lookup, stack push |
| **O(log n)** | Logarithmic | Halving the search space each step | [Binary search](../searching/binary-search.md), balanced-tree lookup |
| **O(n)** | Linear | Looking at each element a fixed number of times | Sum, max, [linear search](../searching/linear-search.md) |
| **O(n log n)** | Linearithmic | Divide-and-conquer with linear merging | [Mergesort](../sorting/mergesort.md), [heapsort](../sorting/heapsort.md), FFT |
| **O(n²)** | Quadratic | Every pair; nested passes over the input | [Bubble](../sorting/bubble-sort.md)/[insertion sort](../sorting/insertion-sort.md), naive duplicate check |
| **O(n³)** | Cubic | Every triple | Naive matrix multiply, Floyd–Warshall |
| **O(2ⁿ)** | Exponential | Every subset | Naive subset-sum, unmemoized Fibonacci |
| **O(n!)** | Factorial | Every ordering | Brute-force travelling salesman, permutation generation |

:::tip[The shape usually tells you the class]
"For each element, do a fixed thing" → linear. "For each pair" → quadratic. "Halve it each time" →
logarithmic. "Try every subset" → exponential. "Try every ordering" → factorial. Reading the problem
statement often gives you the exponent before you write any code.
:::

## Architecture / Mechanism

### The linearithmic barrier

`O(n log n)` shows up constantly, and not by accident: **comparison-based sorting cannot do better**.
Any algorithm that only compares elements must distinguish between all `n!` possible orderings, and a
binary comparison yields one bit, so it needs at least `log₂(n!) ≈ n log₂ n − 1.44n` comparisons.

That is a proof about a *model*, not about sorting itself. Algorithms that inspect the values rather
than only comparing them — counting sort, radix sort, bucket sort — escape it and reach `O(n)`, at
the price of assuming something about the keys (bounded range, fixed width).

### Amortized complexity

Some operations are usually cheap and occasionally expensive, in a pattern where the expensive cases
pay for themselves. A **dynamic array** (`list`, `vector`, `ArrayList`) is the canonical example:

```python showLineNumbers
# Appending is O(1) — until capacity runs out
items = []
for i in range(n):
    items.append(i)   # occasionally: allocate a bigger buffer, copy everything
```

Doubling the capacity when it fills means a resize at sizes 1, 2, 4, 8, …, n, copying
`1 + 2 + 4 + … + n < 2n` elements in total across the whole run. Spread across n appends, that is
**O(1) amortized** — a bound on the average cost per operation over any sequence, not a probabilistic
claim.

:::warning[Amortized O(1) still means one operation can be O(n)]
For throughput this is fine. For **latency** it is not: a single append can trigger a full copy, and
in a real-time or interactive path that tail is exactly what you will be judged on. If p99 latency
matters, either reserve capacity up front (`list` has no API for this in Python, but `vector::reserve`
and `ArrayList(int)` do) or use a structure with worst-case rather than amortized guarantees.
:::

The growth *factor* matters too. Doubling gives amortized O(1); growing by a fixed **amount** each
time gives amortized O(n), because resizes stop getting rarer as the array grows.

### Space complexity

The same notation applies to memory, and the number that matters is usually **auxiliary** space —
extra space beyond the input itself.

| Algorithm | Time | Auxiliary space | Note |
|---|---|---|---|
| [Insertion sort](../sorting/insertion-sort.md) | O(n²) | O(1) | Sorts in place |
| [Heapsort](../sorting/heapsort.md) | O(n log n) | O(1) | In place, and worst-case guaranteed |
| [Quicksort](../sorting/quicksort.md) | O(n log n) avg | O(log n) | Recursion stack only |
| [Mergesort](../sorting/mergesort.md) | O(n log n) | O(n) | Needs a full second buffer |
| Counting sort | O(n + k) | O(k) | k = range of key values |

Recursion is the space cost people most often forget: every pending call holds a stack frame, so a
recursion of depth n costs O(n) memory even when it allocates nothing itself. That is why an
unbalanced quicksort risks a stack overflow rather than merely being slow.

## Practical Usage

Rough guidance on what is tractable, assuming ~10⁸–10⁹ simple operations per second:

| Input size | What is comfortably affordable |
|---|---|
| n ≤ 10 | Anything, including O(n!) |
| n ≤ 25 | O(2ⁿ) |
| n ≤ 500 | O(n³) |
| n ≤ 10,000 | O(n²) |
| n ≤ 10,000,000 | O(n log n) |
| n > 10,000,000 | O(n) or O(log n) — and start caring about memory bandwidth |

## Edge Cases & Pitfalls

- **O(1) is not a promise of speed.** A hash lookup that computes a cryptographic digest is O(1) and
  slower than scanning a ten-element array.
- **The constant can dominate at realistic sizes.** Strassen's matrix multiplication is
  asymptotically better than the naive O(n³) and loses on small matrices; galactic algorithms take
  this to its absurd conclusion, beating everything asymptotically at input sizes exceeding the
  number of atoms in the universe.
- **Memory access is not O(1) on real hardware.** The model assumes uniform-cost memory. Actual
  machines have a [cache hierarchy](../../memory-hierarchy/cpu-caches.md) spanning two orders of
  magnitude in latency, which is why a "worse" algorithm with sequential access often wins.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* — Ch. 8 for the comparison-sort lower bound, Ch. 16 for amortized analysis (aggregate, accounting and potential methods).
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.4 — "Analysis of Algorithms", with empirical measurement alongside the theory.

### Books & Videos

- [Big-O Cheat Sheet](https://www.bigocheatsheet.com/) — time and space complexity tables for the standard structures and sorts.

## Related Pages

- [Big-O Notation](./big-o-notation.md) — what the notation formally asserts.
- [Choosing a Sort](../sorting/choosing-a-sort.md) — these trade-offs applied to one concrete decision.
- [Arrays & Dynamic Arrays](../data-structures/arrays.md) — where the amortized-doubling argument comes from.
