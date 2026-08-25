---
id: divide-and-conquer
title: Divide & Conquer
sidebar_label: Divide & Conquer
sidebar_position: 2
tags: [computer-science, algorithms, patterns, divide-and-conquer, recursion]
---

# Divide & Conquer


Divide and conquer breaks a problem into independent subproblems of the same kind, solves those
recursively, and combines the results. The leverage comes from the subproblems being **independent** —
no shared state, no communication — which is also what makes the pattern parallelise so naturally.

Three steps, always: **divide**, **conquer**, **combine**. Which step does the real work varies, and
that variation is what distinguishes [mergesort](../sorting/mergesort.md) from
[quicksort](../sorting/quicksort.md).

## Core Concepts

| Algorithm | Divide | Conquer | Combine |
|---|---|---|---|
| [Mergesort](../sorting/mergesort.md) | Trivial — split in half | Sort each half | **Merge — O(n)** |
| [Quicksort](../sorting/quicksort.md) | **Partition — O(n)** | Sort each side | Trivial — nothing to do |
| [Binary search](../searching/binary-search.md) | Compare to the midpoint | One side only | Trivial |
| Karatsuba multiplication | Split the digits | 3 subproducts | Shift and add |
| Strassen's matrix multiply | Split into quadrants | 7 subproducts | Add submatrices |

Mergesort and quicksort are exact mirrors: one does its work combining, the other dividing. Binary
search is the degenerate case that discards a subproblem instead of solving it, which is why it is
logarithmic rather than linear.

## Architecture / Mechanism

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def divide_and_conquer(problem):
    if is_small_enough(problem):
        return solve_directly(problem)          # base case
    subproblems = divide(problem)
    results = [divide_and_conquer(p) for p in subproblems]
    return combine(results)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
Result divide_and_conquer(const Problem& problem) {
    if (is_small_enough(problem))
        return solve_directly(problem);          // base case
    std::vector<Result> results;
    for (const auto& p : divide(problem))
        results.push_back(divide_and_conquer(p));
    return combine(results);
}
```

</TabItem>
</Tabs>

### The Master Theorem

For a recurrence `T(n) = a·T(n/b) + f(n)` — *a* subproblems, each of size *n/b*, plus *f(n)* work to
divide and combine — compare `f(n)` against `n^(log_b a)`:

| Case | Condition | Result |
|---|---|---|
| 1 | `f(n)` grows **slower** | T(n) = Θ(n^(log_b a)) — the leaves dominate |
| 2 | `f(n)` grows **at the same rate** | T(n) = Θ(n^(log_b a) · log n) — every level costs the same |
| 3 | `f(n)` grows **faster** | T(n) = Θ(f(n)) — the root dominates |

Worked examples:

| Recurrence | Algorithm | a, b, f(n) | Result |
|---|---|---|---|
| T(n) = 2T(n/2) + O(n) | Mergesort | 2, 2, n | n^1 = n, case 2 → **Θ(n log n)** |
| T(n) = T(n/2) + O(1) | Binary search | 1, 2, 1 | n^0 = 1, case 2 → **Θ(log n)** |
| T(n) = 2T(n/2) + O(1) | Tree traversal | 2, 2, 1 | n^1 vs 1, case 1 → **Θ(n)** |
| T(n) = 7T(n/2) + O(n²) | Strassen's | 7, 2, n² | n^2.81, case 1 → **Θ(n^2.81)** |
| T(n) = 3T(n/2) + O(n) | Karatsuba | 3, 2, n | n^1.58, case 1 → **Θ(n^1.58)** |

The last two are the interesting ones: both beat the obvious algorithm purely by **reducing the
number of subproblems** — Karatsuba does 3 multiplications where the schoolbook method does 4,
Strassen 7 where the naive method does 8. Neither changes the subproblem size; the win is entirely in
*a*.

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Maximum subarray, divide and conquer — O(n log n)
# (Kadane's algorithm solves this in O(n); this version shows the pattern.)
def max_subarray(a, lo, hi):
    if lo == hi:
        return a[lo]
    mid = (lo + hi) // 2
    left = max_subarray(a, lo, mid)             # entirely in the left half
    right = max_subarray(a, mid + 1, hi)        # entirely in the right half

    # The third case: crossing the midpoint. This is the "combine" step.
    best_left, total = float("-inf"), 0
    for i in range(mid, lo - 1, -1):
        total += a[i]
        best_left = max(best_left, total)
    best_right, total = float("-inf"), 0
    for i in range(mid + 1, hi + 1):
        total += a[i]
        best_right = max(best_right, total)

    return max(left, right, best_left + best_right)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Maximum subarray, divide and conquer — O(n log n)
// (Kadane's algorithm solves this in O(n); this version shows the pattern.)
int max_subarray(const std::vector<int>& a, int lo, int hi) {
    if (lo == hi) return a[lo];
    int mid = lo + (hi - lo) / 2;
    int left  = max_subarray(a, lo, mid);           // entirely in the left half
    int right = max_subarray(a, mid + 1, hi);       // entirely in the right half

    // The third case: crossing the midpoint. This is the "combine" step.
    int best_left = std::numeric_limits<int>::min(), total = 0;
    for (int i = mid; i >= lo; --i) {
        total += a[i];
        best_left = std::max(best_left, total);
    }
    int best_right = std::numeric_limits<int>::min();
    total = 0;
    for (int i = mid + 1; i <= hi; ++i) {
        total += a[i];
        best_right = std::max(best_right, total);
    }

    return std::max({left, right, best_left + best_right});
}
```

</TabItem>
</Tabs>

Where the pattern shows up beyond sorting:

- **Parallel processing.** MapReduce is divide and conquer with the subproblems distributed across
  machines; the independence of subproblems is exactly what makes the distribution safe.
- **Fast Fourier Transform** — O(n log n) instead of O(n²), by splitting into even and odd indices.
- **Closest pair of points** — O(n log n) instead of the O(n²) of checking all pairs.
- **Quickselect** — quicksort that recurses into only one side, giving O(n) average for the k-th
  smallest element.
- **[Binary search](../searching/binary-search.md)** and every balanced-tree operation.

## Edge Cases & Pitfalls

:::warning[Divide and conquer requires *independent* subproblems]
When subproblems overlap — the same sub-computation appearing in several branches — plain recursion
recomputes it exponentially often. Naive Fibonacci is the standard demonstration: `fib(n-1)` and
`fib(n-2)` share almost all their work, and the runtime is O(2ⁿ) for an O(n) problem.

Overlapping subproblems mean you want [dynamic programming](./dynamic-programming.md), which is
precisely divide and conquer plus memoisation.
:::

- **The base case must be reachable.** A "divide" that can produce an empty or full-size subproblem
  recurses forever. Quicksort's `mid + 1` and `mid - 1` exist for exactly this reason.
- **Recursion depth is O(log n) when balanced and O(n) when not.** Unbalanced quicksort overflows the
  stack rather than merely running slowly.
- **Switch to an iterative algorithm at small sizes.** Recursion overhead dominates below ~16
  elements, which is why production sorts fall back to
  [insertion sort](../sorting/insertion-sort.md).
- **The Master Theorem does not cover everything** — it requires subproblems of equal size and
  well-behaved `f(n)`. Unequal splits need the Akra–Bazzi method or a recursion tree.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 4 — divide and conquer, the substitution and recursion-tree methods, and the Master Theorem with proof.
- Karatsuba, A. (1962) — the multiplication algorithm that first beat the schoolbook O(n²) bound.
- Strassen, V. (1969), "Gaussian elimination is not optimal" — the matrix-multiplication result.

### Books & Videos

- Bentley, J., *Programming Pearls*, Ch. 8 — the maximum-subarray problem worked through four algorithms, including the divide-and-conquer one above.

## Related Pages

- [Mergesort](../sorting/mergesort.md) and [Quicksort](../sorting/quicksort.md) — the two canonical instances.
- [Dynamic Programming](./dynamic-programming.md) — what to use when subproblems overlap.
- [Complexity & Analysis](../complexity/intro.md) — for reading the recurrences above.
