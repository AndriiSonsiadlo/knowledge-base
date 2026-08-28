---
id: common-complexities
title: Common Complexities
sidebar_label: Common Complexities
sidebar_position: 2
tags: [computer-science, algorithms, complexity, growth-classes]
---

# Common Complexities

In practice you meet perhaps eight growth classes. Recognising which one a piece of code falls into —
and, more usefully, recognising the *problem shape* that produces each — is most of what complexity
analysis is for day to day.

The classes below are ordered by growth rate, each with one named, real algorithm rather than an
invented example, because the named algorithm is what makes the class memorable and gives it a case to
reason about (see [Big-O Notation](./big-o-notation.md) for what "case" and "O" formally mean).

## Core Concepts

### $O(1)$ — Constant

Direct addressing: reading `a[i]` from an array, or a hash table lookup, cost the same regardless of
how large the collection is. Array indexing is $O(1)$ worst case, arithmetic on a known offset; hash
lookup is $O(1)$ **average** case and $O(n)$ **worst** case, since a pathological set of keys can collide
into one bucket.

### $O(\log n)$ — Logarithmic

[Binary search](../searching/binary-search.md) over sorted data: each comparison discards half of what
remains, so the number of comparisons is worst-case $O(\log n)$. Balanced binary search tree operations
(insert, find, delete) share the same bound because the tree's height is kept $O(\log n)$.

### $O(n)$ — Linear

A single pass that looks at each element a fixed number of times: summing an array, finding its
maximum, or [linear search](../searching/linear-search.md) through unsorted data — $O(n)$ worst case,
since nothing rules out the target being last or absent.

### $O(n \log n)$ — Linearithmic

Divide-and-conquer with linear work to combine the halves: [mergesort](../sorting/mergesort.md) and
[heapsort](../sorting/heapsort.md) are both $Θ(n \log n)$ worst case. So is any comparison-based sort, for
a reason worth stating precisely — see below.

### $O(n^2)$ — Quadratic

Every pair: [bubble sort](../sorting/bubble-sort.md) and
[insertion sort](../sorting/insertion-sort.md) compare or shift adjacent pairs in the worst case, and a
naive duplicate check compares every element against every other. $O(n^2)$ worst case for all three.

### $O(n^3)$ — Cubic

Every triple: the textbook triple-nested matrix multiplication and the Floyd–Warshall all-pairs
shortest-path algorithm both do $O(n^3)$ worst-case work, one multiply-add or relaxation per triple of
indices.

### $O(2^n)$ — Exponential

Every subset: the naive recursive solution to subset-sum tries all $2^n$ subsets, and unmemoized recursive
Fibonacci recomputes the same subtree exponentially many times — both $O(2^n)$ worst case.

### $O(n!)$ — Factorial

Every ordering: brute-force travelling salesman and plain permutation generation both enumerate all $n!$
orderings of the input, worst case, best case and average case alike — there is no shortcut input.

:::tip[The shape usually tells you the class]
"For each element, do a fixed thing" → linear. "For each pair" → quadratic. "Halve it each time" →
logarithmic. "Try every subset" → exponential. "Try every ordering" → factorial. Reading the problem
statement often gives the exponent before any code is written.
:::

## Mechanism

### The linearithmic barrier

$O(n \log n)$ shows up constantly, and not by accident: **comparison-based sorting cannot do better**.
Any algorithm that only compares elements must distinguish between all `n!` possible orderings, and a
binary comparison yields one bit, so it needs at least $\log_2(n!) \approx n \log_2 n - 1.44n$ comparisons worst
case (Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 8, "Sorting in
Linear Time" — the decision-tree argument).

That is a proof about a *model*, not about sorting itself. Algorithms that inspect the values rather
than only comparing them — counting sort, radix sort, bucket sort — escape it and reach $O(n)$ worst
case, at the price of assuming something about the keys (bounded range, fixed width).

### Wall-clock cost at n = 10⁶

At roughly one billion simple operations per second, fixing n = 10⁶ across the classes above:

| Class | Operations at n = 10⁶ | Wall-clock time |
|---|---|---|
| O(1) | 1 | negligible |
| O(log n) | ~20 | negligible |
| O(n) | 1,000,000 | ~1 ms |
| O(n log n) | ~20,000,000 | ~20 ms |
| O(n²) | 10¹² | ~17 minutes |
| O(n³) | 10¹⁸ | ~32 years |
| O(2ⁿ) | 2¹,⁰⁰⁰,⁰⁰⁰ | unreachable — more operations than atoms in the observable universe |

The $O(n \log n)$ row worked out, so the rest of the table can be redone by hand:

```text
n = 1,000,000
log₂(1,000,000) ≈ 19.93   →  round to 20

operations ≈ n · log₂ n
           ≈ 1,000,000 × 20
           = 20,000,000

time ≈ operations / (10⁹ operations per second)
     ≈ 20,000,000 / 1,000,000,000
     ≈ 0.02 s  =  20 ms
```

The same recipe gives every other row: for O(n²), `operations = n² = 10¹²`, divided by 10⁹ gives 1,000
seconds, which is where the ~17-minute figure comes from.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import math


def estimate_seconds(n, class_name, ops_per_sec=1_000_000_000):
    """Reproduce one row of the table above from its growth class."""
    if class_name == "n":
        ops = n
    elif class_name == "n log n":
        ops = n * math.log2(n)
    elif class_name == "n^2":
        ops = n**2
    else:
        raise ValueError(class_name)
    return ops / ops_per_sec


assert round(estimate_seconds(1_000_000, "n log n"), 2) == 0.02   # matches the worked row above
assert estimate_seconds(1_000_000, "n") < estimate_seconds(1_000_000, "n^2")
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cmath>

double estimate_seconds_n_log_n(long long n, double ops_per_sec = 1e9) {
    double ops = static_cast<double>(n) * std::log2(static_cast<double>(n));
    return ops / ops_per_sec;
}
```

</TabItem>
</Tabs>

## Practical Usage

Rough guidance on what is tractable, assuming ~$10^8$–$10^9$ simple operations per second, worst case
unless noted:

| Input size | What is comfortably affordable |
|---|---|
| n ≤ 10 | Anything, including $O(n!)$ |
| n ≤ 25 | $O(2^n)$ |
| n ≤ 500 | $O(n^3)$ |
| n ≤ 10,000 | $O(n^2)$ |
| n ≤ 10,000,000 | $O(n \log n)$ |
| n > 10,000,000 | $O(n)$ or $O(\log n)$ — and start caring about memory bandwidth |

Two growth classes get their own page, because there is more to say about each than fits a single
table row: [Amortized Analysis](./amortized-analysis.md) covers operations that are usually O(1) and
occasionally O(n), such as a dynamic array's `append`; [Space Complexity](./space-complexity.md) covers
the same asymptotic language applied to memory rather than time, including the stack cost recursion
hides.

## Edge Cases & Pitfalls

- **$O(1)$ is not a promise of speed.** A hash lookup that computes a cryptographic digest is $O(1)$
  average case and slower in practice than scanning a ten-element array.
- **The constant can dominate at realistic sizes.** Strassen's matrix multiplication is
  asymptotically better than the naive $O(n^3)$ worst case and loses on small matrices; galactic
  algorithms take this to its absurd conclusion, beating everything asymptotically at input sizes
  exceeding the number of atoms in the universe.
- **Memory access is not $O(1)$ on real hardware.** The model assumes uniform-cost memory. Actual
  machines have a [cache hierarchy](../../memory-hierarchy/cpu-caches.md) spanning two orders of
  magnitude in latency, which is why a "worse" algorithm with sequential access often wins at n where
  the table above says it should lose.
- **The named algorithm is not the only route to its class.** Several unrelated algorithms share a
  growth class for different reasons — mergesort and heapsort are both Θ(n log n) worst case, but
  their mechanisms (recursive merge versus heap extraction) share nothing. The class predicts cost,
  not implementation.

## Comparisons

| Class | Beats O(n²) when | Loses to O(n²) when |
|---|---|---|
| O(n log n) | n is large enough that the log factor is cheap next to a full quadratic sweep | n is tiny and the constant behind O(n log n) (recursion, merging) outweighs a simple double loop |
| O(n) (counting/radix sort) | The keys are bounded-range integers, so comparisons can be skipped entirely | The key range k is itself large — cost is O(n + k), and a huge k defeats the point |
| O(2ⁿ) (exact, exponential) | n is small enough that exactness matters more than speed (n ≤ ~25) | n grows past a few dozen — an O(n²) approximation usually beats an exact exponential algorithm that never finishes |

## Recall

<Recall
  invariant="The growth class is a property of the problem shape, not of any single implementation — 'for each pair' is quadratic no matter which language writes the nested loop."
  costs={[
    ["array index / hash lookup (average)", "O(1)"],
    ["binary search over sorted data (worst)", "O(log n)"],
    ["single pass over the input (worst)", "O(n)"],
    ["comparison sort — mergesort, heapsort (worst)", "O(n log n)"],
    ["nested pass over every pair (worst)", "O(n²)"],
    ["every subset / every ordering (worst)", "O(2ⁿ) / O(n!)"],
  ]}
  reachFor="Recognising the class a piece of code falls into before running it, or the problem shape ('for each pair', 'try every subset') that predicts the class before any code is written."
  trap="Quoting a bound with no case attached — insertion sort is O(n) only on an already-sorted input; its worst case is O(n²), and the two get conflated constantly."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 8 — "Sorting in Linear
  Time", the comparison-sort decision-tree lower bound and the counting/radix/bucket sorts that escape
  it.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.4 — "Analysis of Algorithms", with empirical measurement
  (the doubling ratio test) alongside the theory.

## Related Pages

- [Big-O Notation](./big-o-notation.md) — what the notation formally asserts, and the case each bound
  above is stated in.
- [Amortized Analysis](./amortized-analysis.md) — bounds that are cheap on average over a sequence of
  operations, not on every single call.
- [Space Complexity](./space-complexity.md) — the same growth classes applied to memory.
- [Choosing a Sort](../sorting/choosing-a-sort.md) — these trade-offs applied to one concrete decision.
