---
id: backtracking
title: Backtracking
sidebar_label: Backtracking
sidebar_position: 5
tags: [computer-science, algorithms, patterns, backtracking, recursion]
---

# Backtracking

Backtracking searches a space of candidate solutions by building them one choice at a time, and
abandoning a partial candidate the moment it cannot possibly lead to a valid one. It is
[depth-first search](../graph-algorithms/traversal.md) over an implicit tree of choices, with pruning.

The pruning is the entire point. Without it this is brute force; with a good constraint check it can
reduce a space of $10^{20}$ candidates to a few thousand actually explored.

## Core Concepts

| Term | Meaning |
|---|---|
| **Choice** | A decision at the current step — which value, which position, which branch |
| **Constraint** | A rule the partial solution must satisfy |
| **Goal** | The condition marking a complete solution |
| **Pruning** | Abandoning a branch once it cannot satisfy the constraints |
| **Undo** | Restoring state when returning from a branch — the "backtrack" |

## Mechanism

Every backtracking algorithm has the same shape:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def backtrack(state, choices):
    if is_goal(state):
        record(state)
        return
    for choice in choices:
        if not is_valid(state, choice):
            continue                    # prune: this branch cannot work
        apply(state, choice)            # make the choice
        backtrack(state, next_choices)  # recurse
        undo(state, choice)             # UNDO — the defining step
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
// illustrative skeleton — State/Choices are placeholders, not real types
void backtrack(State& state, const Choices& choices) {
    if (is_goal(state)) {
        record(state);
        return;
    }
    for (const auto& choice : choices) {
        if (!is_valid(state, choice)) continue;   // prune: this branch cannot work
        apply(state, choice);                     // make the choice
        backtrack(state, next_choices);           // recurse
        undo(state, choice);                      // UNDO — the defining step
    }
}
```

</TabItem>
</Tabs>

The `undo` is what distinguishes backtracking from ordinary recursion. Because the state is shared
and mutated in place, each branch must leave it exactly as it found it.

### N-queens

Place N queens on an N×N board so none attack another.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def solve_n_queens(n):
    solutions = []
    cols, diag, anti = set(), set(), set()
    placement = []

    def place(row):
        if row == n:
            solutions.append(list(placement))
            return
        for col in range(n):
            # Two queens share a diagonal iff row-col matches; an anti-diagonal iff row+col does
            if col in cols or (row - col) in diag or (row + col) in anti:
                continue                                     # prune
            cols.add(col); diag.add(row - col); anti.add(row + col)
            placement.append(col)

            place(row + 1)

            placement.pop()                                  # undo
            cols.remove(col); diag.remove(row - col); anti.remove(row + col)

    place(0)
    return solutions


assert len(solve_n_queens(4)) == 2
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <unordered_set>
#include <vector>

std::vector<std::vector<int>> solve_n_queens(int n) {
    std::vector<std::vector<int>> solutions;
    std::unordered_set<int> cols, diag, anti;
    std::vector<int> placement;

    auto place = [&](int row, auto&& self) -> void {
        if (row == n) {
            solutions.push_back(placement);
            return;
        }
        for (int col = 0; col < n; ++col) {
            // Two queens share a diagonal iff row-col matches; an anti-diagonal iff row+col does
            if (cols.count(col) || diag.count(row - col) || anti.count(row + col))
                continue;                                    // prune
            cols.insert(col); diag.insert(row - col); anti.insert(row + col);
            placement.push_back(col);

            self(row + 1, self);

            placement.pop_back();                            // undo
            cols.erase(col); diag.erase(row - col); anti.erase(row + col);
        }
    };

    place(0, place);
    return solutions;
}
```

</TabItem>
</Tabs>

Traced for n = 4, one row at a time, columns tried left to right — `x` marks a column pruned before a
queen is ever placed there, i.e. before any recursive call happens:

```text
row0: col0 ok -> [0]
row1: col0 x(col) col1 x(diag) col2 ok -> [0,2]
row2: col0 x(col) col1 x(anti) col2 x(col) col3 x(diag) -- dead end, BACKTRACK to row1

row1: col3 ok -> [0,3]
row2: col0 x(col) col1 ok -> [0,3,1]
row3: col0 x(col) col1 x(col) col2 x(diag) col3 x(col) -- dead end, BACKTRACK to row2
row2: no more columns -- BACKTRACK to row1
row1: no more columns -- BACKTRACK to row0

row0: col1 ok -> [1]
row1: col0 x(anti) col1 x(col) col2 x(diag) col3 ok -> [1,3]
row2: col0 ok -> [1,3,0]
row3: col0 x(col) col1 x(col) col2 ok -> [1,3,0,2]   row == 4: SOLUTION

columns [1, 3, 0, 2]:
. Q . .
. . . Q
Q . . .
. . Q .
```

Two backtracks — undoing row1 once and row2 once — are all it costs to find this solution. Every `x`
is a branch pruning removed *before* recursing into it, which is the entire difference from brute
force: brute force would generate all $4^4 = 256$ row/column combinations and validate each completed
board, where backtracking rejects a partial board the instant it conflicts. The three sets keep each
check $O(1)$ instead of a full board rescan, which is what makes even n = 8 instant — strip the
pruning check out and `place` degenerates into generating and validating every arrangement, brute
force wearing recursion as a costume.

### Permutations and subsets

The two most common shapes, worth recognising:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def permutations(items):
    result, current, used = [], [], [False] * len(items)

    def build():
        if len(current) == len(items):
            result.append(list(current))       # copy — `current` keeps mutating
            return
        for i, x in enumerate(items):
            if used[i]:
                continue
            used[i] = True; current.append(x)
            build()
            current.pop(); used[i] = False     # undo
    build()
    return result

def subsets(items):
    result, current = [], []

    def build(i):
        if i == len(items):
            result.append(list(current))
            return
        build(i + 1)                            # exclude items[i]
        current.append(items[i])
        build(i + 1)                            # include items[i]
        current.pop()                           # undo
    build(0)
    return result
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
std::vector<std::vector<int>> permutations(const std::vector<int>& items) {
    std::vector<std::vector<int>> result;
    std::vector<int> current;
    std::vector<bool> used(items.size(), false);

    auto build = [&](auto&& self) -> void {
        if (current.size() == items.size()) {
            result.push_back(current);          // copy — current keeps mutating
            return;
        }
        for (std::size_t i = 0; i < items.size(); ++i) {
            if (used[i]) continue;
            used[i] = true; current.push_back(items[i]);
            self(self);
            current.pop_back(); used[i] = false;    // undo
        }
    };
    build(build);
    return result;
}

// subsets() follows the same shape as permutations() above, with the loop over
// remaining items replaced by one binary choice per item — include, or don't —
// so it is left in Python only; see the Python tab for the full body.
```

</TabItem>
</Tabs>

Permutations are $O(n!)$ and subsets $O(2^n)$ — both unavoidable, since that is how many outputs there
are. Backtracking does not make these problems cheap; it makes *constrained* versions cheap, where
pruning removes most branches.

## Practical Usage

| Problem | Choice per step | Pruning rule |
|---|---|---|
| N-queens | Column for this row | No shared column or diagonal |
| Sudoku | Digit for this cell | Not already in the row, column or box |
| Maze solving | Direction to move | Not a wall, not already visited |
| Word search in a grid | Adjacent cell | Matches the next character |
| Subset sum | Include or exclude | Running sum ≤ target |
| Graph colouring | Colour for this vertex | Differs from every coloured neighbour |
| Regular-expression matching | Consume or skip | Pattern still able to match |
| Constraint solvers, SAT | Variable assignment | No clause falsified |

:::tip[Order your choices to prune early]
Trying the most constrained option first prunes far more of the tree — filling the Sudoku cell with
the fewest legal digits, rather than the next cell in reading order, is the difference between
milliseconds and minutes. This is the **most-constrained-variable heuristic**, the single
highest-value improvement to almost any backtracking search.
:::

## Edge Cases & Pitfalls

:::danger[Forgetting to undo corrupts every later branch]
The `undo` step must reverse *everything* the branch changed — a missed `pop()`, an unreleased set
entry, or a mutated field leaks into sibling branches and produces missing or duplicated solutions
rather than a crash. Keep the mutation and its undo adjacent in the source so the pairing stays
visible, or pass immutable state down instead of mutating shared state — simpler, at the cost of
copying.
:::

- **Appending the working state instead of a copy.** `result.append(current)` stores a reference that
  keeps mutating; every entry ends up identical (usually empty). Always `list(current)`.
- **No pruning means brute force.** If `is_valid` always returns true, every branch is generated and
  only rejected afterward — the exact shape traced above, minus the `x` marks. Check that the
  constraint actually eliminates branches before recursing, not after.
- **Recursion depth equals solution length, and the exponential worst case is inherent.** Deep
  searches need an explicit stack; no pruning makes an NP-hard search polynomial. Beyond a certain
  size, reach for approximation, [dynamic programming](./dynamic-programming.md) if subproblems
  overlap, or a dedicated solver.
- **Finding *one* solution vs. *all*.** Return early for one; the difference is often orders of
  magnitude.

## Comparisons

| | Backtracking | [DP](./dynamic-programming.md) | [Greedy](./greedy-algorithms.md) |
|---|---|---|---|
| Explores | All branches, pruned | All subproblems, memoised | One path |
| Memory | $O(depth)$ | $O(states)$ | $O(1)$ |
| Complexity | Exponential, pruned | Polynomial | $O(n \log n)$ |
| Use when | The state space is too large to tabulate | Subproblems overlap | The greedy choice is provably safe |
| Returns | All solutions, or the best | The optimal value | One answer |

## Recall

<Recall
  invariant="A branch is abandoned the moment it cannot possibly reach a valid solution, before recursing into it — the pruning check, not the recursion, is what separates this from brute force enumeration."
  costs={[
    ["4-queens, pruned (worst, this trace)", "24 column checks"],
    ["n-queens, unpruned brute force (worst)", "O(n^n)"],
    ["permutations of n items (worst)", "O(n!)"],
    ["subsets of n items (worst)", "O(2^n)"],
    ["undo per branch (worst)", "O(1) amortized per mutated field"],
  ]}
  reachFor="The problem asks for all (or one) valid configuration built from a sequence of choices, and a partial choice can be checked for validity before the whole configuration is built."
  trap="Writing `is_valid` but never actually calling it before recursing — that turns backtracking into generate-then-filter, which explores the entire space brute force would and validates it only at the leaves."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 34–35 — NP-completeness and approximation, the context in which backtracking is usually the practical answer.
- Knuth, D., *The Art of Computer Programming*, Vol. 4B, §7.2.2 — backtracking in depth, including dancing links for exact-cover problems.

### Books & Videos

- Knuth, D., ["Dancing Links"](https://arxiv.org/abs/cs/0011047) — Algorithm X for exact cover, and the fastest known Sudoku solver.

## Related Pages

- [Traversal: BFS & DFS](../graph-algorithms/traversal.md) — backtracking is DFS over an implicit tree.
- [Dynamic Programming](./dynamic-programming.md) — the alternative when subproblems overlap.
- [Stacks & Queues](../data-structures/stacks-and-queues.md) — the call stack doing the bookkeeping here.
