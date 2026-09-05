---
id: recursion-memoization-tabulation
title: Recursion, Memoization & Tabulation
sidebar_label: Recursion → Memoization → Tabulation
sidebar_position: 10
tags: [computer-science, algorithms, patterns, dynamic-programming, recursion]
---

# Recursion, Memoization & Tabulation

[Dynamic Programming](./dynamic-programming.md) names the *idea* — overlapping subproblems plus
optimal substructure — but says little about the mechanical journey from a first working solution to
a fast one. That journey has four fixed stops, always in the same order, and each stop is a small,
almost mechanical edit to the previous one. Skipping a stop is how most DP attempts either stall on a
recurrence nobody has verified, or ship a table nobody can explain.

This page walks all four stops on **one** problem, so the edits are visible rather than asserted: plain
recursion, the same recursion with a cache bolted on, the same recurrence read as a fill order over a
table, and finally the table collapsed to the one row it actually needs. Nothing about the *logic*
changes across the four forms — only how the answers to subproblems are stored and in what order they
are computed. Treat the first form as the specification and every later form as a re-implementation
that must agree with it on every input, which is exactly how you should test them.

## Core Concepts

| Term | Meaning |
|---|---|
| **State** | What one subproblem needs to know — here, "which items are still available" and "how much capacity is left" |
| **Recurrence** | How a state's answer follows from smaller states — take the current item or skip it |
| **Memoization** | Top-down: recurse normally, but cache each state's answer the first time it is computed |
| **Tabulation** | Bottom-up: fill every state's slot in an order that guarantees its dependencies are already filled |
| **Rolling array** | A tabulation whose recurrence only ever looks at the *previous* row, so only one row needs to exist in memory |

## Mechanism

The running example is 0/1 knapsack: items `(w=1, v=1)`, `(w=3, v=4)`, `(w=4, v=5)`, `(w=5, v=7)`,
capacity 7 — each item taken at most once, maximise total value without exceeding capacity. Index items
`1..4` in that order. Every form below computes the same function: `best(i, c)` = the best value
achievable using only the first `i` items within capacity `c`, with the recurrence

```
best(i, c) = best(i-1, c)                                  if item i does not fit (w_i > c)
best(i, c) = max(best(i-1, c), best(i-1, c - w_i) + v_i)    otherwise
best(0, c) = 0 for every c
```

### Form 1 — plain recursion

`best(i, c)` calls itself twice per item, and the two branches share subproblems: `best(2, 4)` is asked
for both by the "skip item 3" branch and, separately, by parts of the "take item 3" branch lower in the
tree. Nothing remembers that `best(2, 4)` was already answered, so it is recomputed from scratch every
time it recurs — the definition of overlapping subproblems, and the reason this form is exponential:
`T(n) = 2·T(n-1) + O(1)`, so `O(2^n)` calls in the worst case, independent of the capacity.

### Form 2 — memoized recursion

Identical logic, plus a cache keyed on `(i, c)`. The first call for a given `(i, c)` does the work and
stores the answer; every later call for the same pair returns the stored value in O(1). Since there are
only `n · capacity` distinct `(i, c)` pairs and each is computed once, the cost drops to
`O(n · capacity)` time and `O(n · capacity)` space for the cache — plus `O(n)` recursion-stack depth,
which the next two forms remove entirely.

### Form 3 — bottom-up tabulation

The memoized version computes states in whatever order the recursion happens to visit them. Tabulation
instead reads the recurrence as a dependency graph — row `i` needs only row `i-1` — and fills a 2-D
table `dp[i][c]` explicitly in increasing `i`, increasing `c`, so every dependency is already filled
when it is read. Same `O(n · capacity)` time, same `O(n · capacity)` space for the table, but zero
recursion stack — this is a plain nested loop.

<Figure src="/img/cs/algorithms/dp-fill-order.png"
        alt="A 5-row by 8-column DP grid for the knapsack problem, cells shaded from light to dark by the order they are filled — row by row, left to right within a row — with the two rows that make up the rolling-array window outlined"
        caption="Every cell only ever reads from the row directly above it, so the fill order (light to dark) never needs a cell that is not ready yet. The outlined pair of rows is the whole working set a rolling array needs at once."
        source="Generated for this page" href="" license="" />

Traced cell by cell for the first two items (row 0 is the base case, all zero by definition):

```text
capacity c:        0    1    2    3    4    5    6    7

row 0 (0 items):    0    0    0    0    0    0    0    0

row 1 (item 1, w=1,v=1)
  c=0: w=1 > 0, can't fit          -> dp[1][0] = dp[0][0]           = 0
  c=1: fits, max(skip, take)       -> dp[1][1] = max(0, dp[0][0]+1) = 1
  c=2..7: same as c=1 (w=1 always fits, dp[0][*] is always 0)
row 1:               0    1    1    1    1    1    1    1

row 2 (item 2, w=3,v=4)
  c=0,1,2: w=3 doesn't fit         -> dp[2][c] = dp[1][c]           = 0, 1, 1
  c=3: fits    -> dp[2][3] = max(dp[1][3], dp[1][0]+4) = max(1, 4) = 4
  c=4: fits    -> dp[2][4] = max(dp[1][4], dp[1][1]+4) = max(1, 5) = 5
  c=5: fits    -> dp[2][5] = max(dp[1][5], dp[1][2]+4) = max(1, 5) = 5
  c=6: fits    -> dp[2][6] = max(dp[1][6], dp[1][3]+4) = max(1, 5) = 5
  c=7: fits    -> dp[2][7] = max(dp[1][7], dp[1][4]+4) = max(1, 5) = 5
row 2:               0    1    1    4    5    5    5    5

(row 3, item 3 w=4,v=5): 0  1  1  4  5  6  6  9
(row 4, item 4 w=5,v=7): 0  1  1  4  5  7  8  9

answer: dp[4][7] = 9

tracing the answer back — at each row, "did taking this item improve the cell?":
  dp[4][7]=9 came from dp[3][7]=9 (equal to skipping)         -> item 4 NOT taken
  dp[3][7]=9 came from dp[2][3]+5=9 (better than dp[2][7]=5)  -> item 3 TAKEN,  move to column 7-4=3
  dp[2][3]=4 came from dp[1][0]+4=4 (better than dp[1][3]=1)  -> item 2 TAKEN,  move to column 3-3=0
  dp[1][0]=0 (item 1 does not fit in capacity 0)              -> item 1 not taken
  chosen items: {2, 3} -> weight 3+4=7, value 4+5=9  ✓ exactly fills the capacity
```

### Form 4 — rolling array

Every cell of row `i` reads only row `i-1`, never row `i-2` or earlier, and never another cell of its
own row in the *forward* direction. Collapsing to one 1-D array `dp[c]` and updating it **in place**
reproduces the same table, provided the capacity loop runs **downward** for each item — the same
direction rule as in [Dynamic Programming](./dynamic-programming.md#the-workflow-on-a-real-problem).
Downward means `dp[c - w]` on the right of an assignment still holds *last item's* value when it is
read, because the cell at the lower index has not been touched yet this pass. Space drops from
`O(n · capacity)` to `O(capacity)`; time is unchanged at `O(n · capacity)`.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
from functools import lru_cache

ITEMS = [(1, 1), (3, 4), (4, 5), (5, 7)]   # (weight, value)
CAPACITY = 7


# Form 1: plain recursion — O(2^n) calls, no memory of repeated states
def knapsack_naive(i, c):
    if i == 0:
        return 0
    w, v = ITEMS[i - 1]
    best = knapsack_naive(i - 1, c)                       # skip item i
    if w <= c:
        best = max(best, knapsack_naive(i - 1, c - w) + v)  # or take it
    return best


# Form 2: memoized recursion — same logic, O(n * capacity) calls
@lru_cache(maxsize=None)
def knapsack_memo(i, c):
    if i == 0:
        return 0
    w, v = ITEMS[i - 1]
    best = knapsack_memo(i - 1, c)
    if w <= c:
        best = max(best, knapsack_memo(i - 1, c - w) + v)
    return best


# Form 3: bottom-up table — same recurrence, filled by explicit loops
def knapsack_table(items, capacity):
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = items[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)
    return dp


# Form 4: rolling array — one row, capacity iterated DOWNWARD
def knapsack_rolling(items, capacity):
    dp = [0] * (capacity + 1)
    for w, v in items:
        for c in range(capacity, w - 1, -1):    # downward: dp[c - w] is still last item's value
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


# all four forms must agree — the traced answer is 9 (items with weight 3 and weight 4)
assert knapsack_naive(len(ITEMS), CAPACITY) == 9
assert knapsack_memo(len(ITEMS), CAPACITY) == 9
assert knapsack_table(ITEMS, CAPACITY)[len(ITEMS)][CAPACITY] == 9
assert knapsack_rolling(ITEMS, CAPACITY) == 9
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <cassert>
#include <unordered_map>
#include <vector>

using Item = std::pair<int, int>;   // (weight, value)
const std::vector<Item> ITEMS = {{1, 1}, {3, 4}, {4, 5}, {5, 7}};
constexpr int CAPACITY = 7;

// Form 1: plain recursion — O(2^n) calls
int knapsack_naive(int i, int c) {
    if (i == 0) return 0;
    auto [w, v] = ITEMS[i - 1];
    int best = knapsack_naive(i - 1, c);
    if (w <= c) best = std::max(best, knapsack_naive(i - 1, c - w) + v);
    return best;
}

// Form 2: memoized recursion — same logic, O(n * capacity) distinct calls
int knapsack_memo(int i, int c, std::unordered_map<long long, int>& cache) {
    if (i == 0) return 0;
    long long key = static_cast<long long>(i) * 100000 + c;
    if (auto it = cache.find(key); it != cache.end()) return it->second;
    auto [w, v] = ITEMS[i - 1];
    int best = knapsack_memo(i - 1, c, cache);
    if (w <= c) best = std::max(best, knapsack_memo(i - 1, c - w, cache) + v);
    return cache[key] = best;
}

// Form 3: bottom-up table
std::vector<std::vector<int>> knapsack_table(const std::vector<Item>& items, int capacity) {
    int n = static_cast<int>(items.size());
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));
    for (int i = 1; i <= n; ++i) {
        auto [w, v] = items[i - 1];
        for (int c = 0; c <= capacity; ++c) {
            dp[i][c] = dp[i - 1][c];
            if (w <= c) dp[i][c] = std::max(dp[i][c], dp[i - 1][c - w] + v);
        }
    }
    return dp;
}

// Form 4: rolling array — capacity iterated DOWNWARD
int knapsack_rolling(const std::vector<Item>& items, int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    for (auto [w, v] : items) {
        for (int c = capacity; c >= w; --c)
            dp[c] = std::max(dp[c], dp[c - w] + v);
    }
    return dp[capacity];
}
```

</TabItem>
</Tabs>

## Practical Usage

**Write form 1 first, always.** It is the specification: the shortest possible statement of the
recurrence, with nothing to get wrong except the recurrence itself. Confirm it on a small case by hand
— the trace above — before optimising anything.

**Add memoization (form 2) next, not a table.** In Python, `@lru_cache` turns a correct recursion into
an efficient one in one line, with no change to the control flow, and Python's own docs describe it as
caching up to `maxsize` "most recent calls" using the arguments as a key — [`functools.lru_cache`
docs](https://docs.python.org/3/library/functools.html#functools.lru_cache). This is almost always
the right place to stop for a one-off script or a competitive-programming submission: the complexity is
already optimal, and the code is closest to the mathematical recurrence, which is what gets debugged
when the answer is wrong.

**Move to tabulation (form 3) only when memoization is not good enough** — a recursion-depth limit
(CPython's default is 1000, raised with `sys.setrecursionlimit`, but that trades one failure mode for a
real C-stack overflow), a language or embedded environment without automatic memoization, or a
requirement to reason about worst-case stack usage. Tabulation is strictly more mechanical to write
once the state and recurrence are settled, and strictly easier to hand-optimize for space, because the
dependency structure between rows is explicit in the loop instead of implicit in the call graph.

**Collapse to a rolling array (form 4) last, and only under memory pressure**, because it is the form
most likely to hide a bug: getting the iteration direction wrong silently computes a *different*,
still-plausible-looking problem (unbounded knapsack instead of 0/1 — see
[Dynamic Programming](./dynamic-programming.md)) rather than crashing. Keep form 3 around as the
oracle to test form 4 against on the same inputs.

## Edge Cases & Pitfalls

- **Skipping straight to tabulation.** Without form 1 to check against, an off-by-one in the loop
  bounds produces a table that looks plausible and is wrong. Always derive the table from a verified
  recursion.
- **`lru_cache` needs hashable arguments.** A list or a mutable container as a memoization key raises
  `TypeError: unhashable type`; convert to a tuple first.
- **The rolling array's direction bug.** Iterating capacity upward while collapsing to one row lets
  `dp[c - w]` already include the *current* item, silently switching the problem to unbounded
  knapsack. The symptom is a table that fills without error and returns a value that is too large.
- **Reconstructing the choice, not just the value.** All four forms above return `best(n, capacity)`
  alone. Recovering *which* items were chosen — the traceback shown above — needs either the full 2-D
  table (form 3, not form 4) or a parallel table of "did taking the item at this cell win?" decisions,
  because the rolling array has already overwritten the earlier rows.
- **Recursion-limit crashes reading as logic bugs.** A correct form-2 recursion that blows past
  `sys.setrecursionlimit` on a large input looks, from the traceback, like something is wrong with the
  algorithm. It is a stack-depth problem; convert to form 3.

## Comparisons

| | Form 1: recursion | Form 2: memoized | Form 3: tabulated | Form 4: rolling |
|---|---|---|---|---|
| Time (worst) | O(2^n) | O(n · capacity) | O(n · capacity) | O(n · capacity) |
| Extra space (worst) | O(n) stack | O(n · capacity) cache + O(n) stack | O(n · capacity) table | O(capacity) |
| Computes | Only reachable states | Only reachable states | Every state | Every state |
| Easiest to verify against the recurrence | Yes | Yes (same code) | No — loop bounds can hide bugs | No — direction can hide bugs |
| Reconstructs the chosen items | Yes, directly | Yes, directly | Yes, from the full table | No — earlier rows are gone |

## Recall

<Recall
  invariant="All four forms compute the identical function best(i, c); only the storage (call stack, cache, table, single row) and the order of computation change between them."
  costs={[
    ["plain recursion on n items (worst)", "O(2^n)"],
    ["memoized recursion, n items x capacity (worst)", "O(n * capacity)"],
    ["bottom-up table, n items x capacity (worst)", "O(n * capacity) time, O(n * capacity) space"],
    ["rolling array, n items x capacity (worst)", "O(n * capacity) time, O(capacity) space"],
  ]}
  reachFor="A DP recurrence you have just derived and have not yet trusted — write the recursion first, then decide how far along this chain the real constraints force you to go."
  trap="Collapsing to a rolling array by iterating the capacity loop upward instead of downward — it still runs and still returns a number, just the answer to unbounded knapsack instead of 0/1 knapsack."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 15 — the general
  memoization-vs-tabulation framing, with the 0/1 knapsack developed as a worked example.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §6.4 — dynamic programming presented explicitly as
  "top-down" versus "bottom-up" implementations of one recurrence.
- [`functools.lru_cache`](https://docs.python.org/3/library/functools.html#functools.lru_cache) —
  CPython docs; the caching behaviour and the `maxsize` parameter used for form 2.
- [`sys.setrecursionlimit`](https://docs.python.org/3/library/sys.html#sys.setrecursionlimit) — CPython
  docs; the default depth (1000) and the underlying C-stack risk of raising it.

## Related Pages

- [Dynamic Programming](./dynamic-programming.md) — the overlapping-subproblems condition this whole
  chain of forms exists to exploit, and the iteration-direction rule referenced above.
- [Divide & Conquer](./divide-and-conquer.md) — the same recursive shape without overlap, so no
  memoization ever helps.
- [Top-K & Streaming](./top-k-and-streaming.md) — a different constraint, bounded memory, that likewise
  forces a choice between several correct algorithms.
- [Cheat Sheet](./cheat-sheet.md) — where this pattern sits relative to the other eleven in this folder.
