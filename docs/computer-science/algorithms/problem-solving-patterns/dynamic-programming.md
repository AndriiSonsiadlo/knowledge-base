---
id: dynamic-programming
title: Dynamic Programming
sidebar_label: Dynamic Programming
sidebar_position: 4
tags: [computer-science, algorithms, patterns, dynamic-programming, memoization]
---

# Dynamic Programming


Dynamic programming applies when a problem has **overlapping subproblems** — the same sub-computation
arising many times across a recursion. Solving each one once and reusing the answer converts
exponential work into polynomial.

The name is historical and unhelpful; Richard Bellman chose it in the 1950s partly because it sounded
impressive to a research sponsor. Read it as "careful recursion with a cache".

## Core Concepts

Two conditions, both required:

| Property | Meaning |
|---|---|
| **Overlapping subproblems** | The same subproblem recurs. This distinguishes DP from [divide and conquer](./divide-and-conquer.md) |
| **Optimal substructure** | An optimal solution is built from optimal solutions to subproblems |

And two ways to implement it:

| | Top-down (memoisation) | Bottom-up (tabulation) |
|---|---|---|
| Structure | Recursion + a cache | Iteration over a table |
| Computes | Only reachable subproblems | All subproblems |
| Order | Implicit, from the recursion | You must choose a valid order |
| Stack | $O(depth)$ — can overflow | None |
| Easier to | **Write**, from the recurrence | **Optimise for space** |

## Mechanism

### The same problem, three ways

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# 1. Naive recursion — O(2ⁿ). fib(n-1) and fib(n-2) recompute the same values.
def fib_naive(n):
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)

# 2. Top-down: identical logic, plus a cache — O(n)
from functools import lru_cache

@lru_cache(maxsize=None)
def fib_memo(n):
    return n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)

# 3. Bottom-up: fill a table in dependency order — O(n) time, O(1) space
def fib_table(n):
    prev, cur = 0, 1
    for _ in range(n):
        prev, cur = cur, prev + cur
    return prev
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// 1. Naive recursion — O(2ⁿ). fib(n-1) and fib(n-2) recompute the same values.
long long fib_naive(int n) {
    return n < 2 ? n : fib_naive(n - 1) + fib_naive(n - 2);
}

// 2. Top-down: identical logic, plus a cache — O(n)
long long fib_memo(int n) {
    static std::unordered_map<int, long long> cache;
    if (n < 2) return n;
    auto it = cache.find(n);
    if (it != cache.end()) return it->second;
    return cache[n] = fib_memo(n - 1) + fib_memo(n - 2);
}

// 3. Bottom-up: fill a table in dependency order — O(n) time, O(1) space
long long fib_table(int n) {
    long long prev = 0, cur = 1;
    for (int i = 0; i < n; ++i) {
        long long next = prev + cur;
        prev = cur;
        cur = next;
    }
    return prev;
}
```

</TabItem>
</Tabs>

The third version is what the second becomes once you notice only two entries are ever needed. That
progression — recurrence, memoise, tabulate, shrink the table — is the standard workflow.

### The workflow, on a real problem

**0/1 knapsack**: choose items with weights and values, maximising value within a capacity, taking
each item at most once. [Greedy by value-per-weight fails here](./greedy-algorithms.md).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def knapsack(weights, values, capacity):
    n = len(weights)
    # dp[i][c] = best value using the first i items within capacity c
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]                      # skip item i
            if w <= c:                                   # or take it, if it fits
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)
    return dp[n][capacity]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int knapsack(const std::vector<int>& weights, const std::vector<int>& values, int capacity) {
    int n = static_cast<int>(weights.size());
    // dp[i][c] = best value using the first i items within capacity c
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));

    for (int i = 1; i <= n; ++i) {
        int w = weights[i - 1], v = values[i - 1];
        for (int c = 0; c <= capacity; ++c) {
            dp[i][c] = dp[i - 1][c];                    // skip item i
            if (w <= c)                                 // or take it, if it fits
                dp[i][c] = std::max(dp[i][c], dp[i - 1][c - w] + v);
        }
    }
    return dp[n][capacity];
}
```

</TabItem>
</Tabs>

Each cell depends only on the previous row, so one row suffices — provided you iterate capacity
**downward**, so that each item is used at most once:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def knapsack_1d(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):     # DOWNWARD — reversing this allows reuse
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int knapsack_1d(const std::vector<int>& weights, const std::vector<int>& values, int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    for (std::size_t i = 0; i < weights.size(); ++i) {
        int w = weights[i], v = values[i];
        for (int c = capacity; c >= w; --c)     // DOWNWARD — reversing this allows reuse
            dp[c] = std::max(dp[c], dp[c - w] + v);
    }
    return dp[capacity];
}
```

</TabItem>
</Tabs>

:::warning[The iteration direction encodes the problem]
Iterating capacity downward gives **0/1 knapsack** — each item usable once. Iterating *upward* gives
**unbounded knapsack** — each item usable any number of times, because `dp[c - w]` may already
include the current item.

The two problems differ by the direction of one loop. This is the most common DP bug, and it produces
a valid-looking answer to the wrong question.
:::

### Defining the state

Most of the difficulty is choosing what the table indexes. Ask:

1. **What does one cell mean?** State it as a sentence — "the best value using the first i items
   within capacity c". If you cannot, the state is wrong.
2. **What is the recurrence?** How does a cell follow from smaller ones?
3. **What are the base cases?**
4. **In what order can cells be filled** so dependencies are ready?

## Practical Usage

| Problem | State | Complexity |
|---|---|---|
| Fibonacci | `dp[i]` = i-th number | $O(n)$ |
| Climbing stairs, coin change (count ways) | `dp[i]` = ways to reach i | $O(n \cdot k)$ |
| Coin change (fewest coins) | `dp[i]` = fewest coins for amount i | $O(n \cdot k)$ |
| 0/1 knapsack | `dp[i][c]` | $O(n \cdot capacity)$ |
| Longest common subsequence | `dp[i][j]` = LCS of prefixes | $O(n \cdot m)$ |
| Edit distance (Levenshtein) | `dp[i][j]` = edits between prefixes | $O(n \cdot m)$ |
| Longest increasing subsequence | `dp[i]` = best ending at i | $O(n^2)$, or $O(n \log n)$ with binary search |
| Matrix chain multiplication | `dp[i][j]` = best cost for the range | $O(n^3)$ |

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Edit distance — the engine behind spell-checkers and `diff`
def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i                     # delete all of a's prefix
    for j in range(n + 1):
        dp[0][j] = j                     # insert all of b's prefix

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]              # free match
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],         # delete
                                   dp[i][j - 1],         # insert
                                   dp[i - 1][j - 1])     # substitute
    return dp[m][n]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Edit distance — the engine behind spell-checkers and `diff`
int edit_distance(std::string_view a, std::string_view b) {
    int m = static_cast<int>(a.size()), n = static_cast<int>(b.size());
    std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));
    for (int i = 0; i <= m; ++i) dp[i][0] = i;      // delete all of a's prefix
    for (int j = 0; j <= n; ++j) dp[0][j] = j;      // insert all of b's prefix

    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            if (a[i - 1] == b[j - 1])
                dp[i][j] = dp[i - 1][j - 1];                   // free match
            else
                dp[i][j] = 1 + std::min({dp[i - 1][j],         // delete
                                         dp[i][j - 1],         // insert
                                         dp[i - 1][j - 1]});   // substitute
        }
    }
    return dp[m][n];
}
```

</TabItem>
</Tabs>

:::tip[Start top-down]
Write the naive recursion first and confirm it is correct. Then add `@lru_cache` — often the entire
optimisation. Convert to a table only if you need the space saving or hit a recursion limit. Trying
to write the tabulated version directly, before the recurrence is settled, is how most DP attempts
stall.
:::

## Edge Cases & Pitfalls

- **`@lru_cache` requires hashable arguments.** Lists must become tuples. It also holds references
  forever with `maxsize=None`, which leaks on long-running processes.
- **Mutable default arguments as caches** (`def f(n, memo={})`) share state across calls — a real bug
  when the cache depends on other inputs.
- **Filling the table in the wrong order** reads cells that are still zero. Bottom-up requires an
  order respecting every dependency — effectively a
  [topological sort](../graph-algorithms/topological-sort.md) of the state graph.
- **Reconstructing the solution, not just its value**, needs either a parent table or a backward walk
  through the finished table. Most implementations return only the optimum and then need rewriting.
- **Pseudo-polynomial complexity.** Knapsack's $O(n \cdot capacity)$ is polynomial in the *value* of the
  capacity but exponential in the number of bits used to write it — which is why knapsack is still
  NP-hard despite the DP solution.
- **Memory can be the binding constraint.** An $O(n \cdot m)$ table for two 100,000-character strings is
  $10^{10}$ cells. Use the rolling-row trick, or Hirschberg's algorithm for linear space.

## Comparisons

| | DP | [Greedy](./greedy-algorithms.md) | [Divide & conquer](./divide-and-conquer.md) | [Backtracking](./backtracking.md) |
|---|---|---|---|---|
| Subproblems | Overlapping | — | **Independent** | Overlapping or not |
| Choices considered | All | One | All | All, pruned |
| Guarantees optimum | Yes | Only with a proof | Yes | Yes |
| Typical cost | Polynomial | $O(n \log n)$ | $O(n \log n)$ | Exponential |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 15 — dynamic programming, with rod-cutting, matrix chains and LCS developed in full.
- Bellman, R. (1957), *Dynamic Programming* — the original, and the source of the name.
- Kleinberg & Tardos, *Algorithm Design*, Ch. 6 — an unusually clear treatment of choosing the state.

### Books & Videos

- [Erik Demaine, MIT 6.006 — Dynamic Programming lectures](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) — the "five easy steps" framing for defining state.

## Related Pages

- [Greedy Algorithms](./greedy-algorithms.md) — the cheaper approach, when its extra condition holds.
- [Divide & Conquer](./divide-and-conquer.md) — the same recursion without the overlap.
- [Backtracking](./backtracking.md) — for when the state space is too large to tabulate.
