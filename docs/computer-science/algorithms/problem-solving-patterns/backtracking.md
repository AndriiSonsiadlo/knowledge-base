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
reduce a space of 10²⁰ candidates to a few thousand actually explored.

## Core Concepts

| Term | Meaning |
|---|---|
| **Choice** | A decision at the current step — which value, which position, which branch |
| **Constraint** | A rule the partial solution must satisfy |
| **Goal** | The condition marking a complete solution |
| **Pruning** | Abandoning a branch once it cannot satisfy the constraints |
| **Undo** | Restoring state when returning from a branch — the "backtrack" |

## Architecture / Mechanism

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
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
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

The three sets are what make this fast. Checking conflicts in O(1) rather than rescanning the board
turns an impractical search into one that solves n = 8 instantly. **The quality of the pruning check
determines whether backtracking is usable at all.**

Placing one queen per row is itself a form of pruning — it removes every arrangement with two queens
in a row from consideration without ever generating one, cutting the space from C(64, 8) ≈ 4.4
billion to 8⁸ ≈ 16.7 million before any constraint check runs.

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

std::vector<std::vector<int>> subsets(const std::vector<int>& items) {
    std::vector<std::vector<int>> result;
    std::vector<int> current;

    auto build = [&](std::size_t i, auto&& self) -> void {
        if (i == items.size()) {
            result.push_back(current);
            return;
        }
        self(i + 1, self);                      // exclude items[i]
        current.push_back(items[i]);
        self(i + 1, self);                      // include items[i]
        current.pop_back();                     // undo
    };
    build(0, build);
    return result;
}
```

</TabItem>
</Tabs>

Permutations are O(n!) and subsets O(2ⁿ) — both unavoidable, since that is how many outputs there
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
Trying the most constrained option first prunes far more of the tree. In Sudoku, filling the cell
with the fewest legal digits (rather than the next cell in reading order) is the difference between
milliseconds and minutes.

This is the **most-constrained-variable heuristic**, and it is the single highest-value improvement
to almost any backtracking search.
:::

## Edge Cases & Pitfalls

:::danger[Forgetting to undo corrupts every later branch]
The `undo` step must reverse *everything* the branch changed. A missed `pop()`, an unreleased set
entry, or a mutated field leaks into sibling branches, and the result is missing or duplicated
solutions rather than a crash.

Two defences: keep the mutation and its undo adjacent in the source so the pairing is visible, or
pass immutable state down instead of mutating shared state — simpler and much harder to get wrong,
at the cost of copying.
:::

- **Appending the working state instead of a copy.** `result.append(current)` stores a reference that
  keeps mutating; every entry ends up identical (usually empty). Always `list(current)`.
- **No pruning means brute force.** If `is_valid` always returns true, you are enumerating the whole
  space. Check that the constraint actually eliminates branches.
- **Recursion depth.** Depth equals solution length; deep searches need an explicit stack.
- **Exponential worst case is inherent.** Backtracking finds optimal answers to NP-hard problems, but
  no pruning makes the worst case polynomial. Beyond a certain size you need approximation,
  [dynamic programming](./dynamic-programming.md) if subproblems overlap, or a dedicated solver.
- **Finding *one* solution vs. *all*.** Return early for one; the difference is often orders of
  magnitude.

## Comparisons

| | Backtracking | [DP](./dynamic-programming.md) | [Greedy](./greedy-algorithms.md) |
|---|---|---|---|
| Explores | All branches, pruned | All subproblems, memoised | One path |
| Memory | O(depth) | O(states) | O(1) |
| Complexity | Exponential, pruned | Polynomial | O(n log n) |
| Use when | The state space is too large to tabulate | Subproblems overlap | The greedy choice is provably safe |
| Returns | All solutions, or the best | The optimal value | One answer |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 34–35 — NP-completeness and approximation, the context in which backtracking is usually the practical answer.
- Knuth, D., *The Art of Computer Programming*, Vol. 4B, §7.2.2 — backtracking in depth, including dancing links for exact-cover problems.

### Books & Videos

- Knuth, D., ["Dancing Links"](https://arxiv.org/abs/cs/0011047) — Algorithm X for exact cover, and the fastest known Sudoku solver.

## Related Pages

- [Traversal: BFS & DFS](../graph-algorithms/traversal.md) — backtracking is DFS over an implicit tree.
- [Dynamic Programming](./dynamic-programming.md) — the alternative when subproblems overlap.
- [Stacks & Queues](../data-structures/stacks-and-queues.md) — the call stack doing the bookkeeping here.
