---
id: greedy-algorithms
title: Greedy Algorithms
sidebar_label: Greedy Algorithms
sidebar_position: 3
tags: [computer-science, algorithms, patterns, greedy]
---

# Greedy Algorithms


A greedy algorithm makes the choice that looks best right now and never reconsiders it. When that
works it is the cheapest strategy available — usually one sorted pass, $O(n \log n)$ or better, with no
recursion and no table.

When it does not work, it produces a plausible answer that is quietly wrong. The difficulty of greedy
algorithms is never the code; it is establishing that the local choice is safe.

## Core Concepts

Two properties must hold for a greedy algorithm to be correct:

| Property | Meaning |
|---|---|
| **Greedy choice property** | A globally optimal solution can be reached by making the locally optimal choice at each step |
| **Optimal substructure** | An optimal solution contains optimal solutions to its subproblems |

The second is shared with [dynamic programming](./dynamic-programming.md). The first is what
separates them: greedy commits to one choice, DP considers all of them. If the greedy choice property
does not hold, greedy is simply wrong and DP is the fallback.

## Architecture / Mechanism

### Where greedy works: interval scheduling

Given intervals with start and end times, select the largest number that do not overlap.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def max_non_overlapping(intervals):
    intervals.sort(key=lambda iv: iv[1])        # sort by EARLIEST END TIME
    count, last_end = 0, float("-inf")
    for start, end in intervals:
        if start >= last_end:
            count += 1
            last_end = end
    return count
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int max_non_overlapping(std::vector<std::pair<int, int>>& intervals) {
    std::sort(intervals.begin(), intervals.end(),
              [](const auto& a, const auto& b) { return a.second < b.second; });  // EARLIEST END TIME
    int count = 0;
    int last_end = std::numeric_limits<int>::min();
    for (auto [start, end] : intervals) {
        if (start >= last_end) {
            ++count;
            last_end = end;
        }
    }
    return count;
}
```

</TabItem>
</Tabs>

**Why this is correct**, argued properly: let *g* be the interval with the earliest end time, and let
*O* be any optimal solution. If *O* contains *g*, done. If not, let *f* be the first interval in *O*.
Since *g* ends no later than *f*, swapping *f* for *g* in *O* cannot overlap anything that followed
*f* — so the swap yields a solution of the same size that does contain *g*. The greedy choice is
therefore never worse. Induct.

That argument — an **exchange argument** — is what a greedy proof looks like. Note that greedily
choosing the *shortest* interval, or the *earliest-starting* one, both fail, and only the proof tells
you which criterion is the right one.

### Where greedy fails: making change

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def change_greedy(coins, amount):
    coins = sorted(coins, reverse=True)
    used = []
    for c in coins:
        while amount >= c:
            used.append(c)
            amount -= c
    return used if amount == 0 else None
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
std::optional<std::vector<int>> change_greedy(std::vector<int> coins, int amount) {
    std::sort(coins.begin(), coins.end(), std::greater<>{});
    std::vector<int> used;
    for (int c : coins) {
        while (amount >= c) {
            used.push_back(c);
            amount -= c;
        }
    }
    if (amount != 0) return std::nullopt;
    return used;
}
```

</TabItem>
</Tabs>

With coins `[1, 5, 10, 25]` this is optimal for every amount. With `[1, 3, 4]` and a target of 6, it
takes 4 + 1 + 1 = **three** coins, while the optimum is 3 + 3 = **two**.

The algorithm is not buggy — the greedy choice property simply does not hold for arbitrary coin sets.
Correct change-making for general denominations needs
[dynamic programming](./dynamic-programming.md). This is the pattern's characteristic failure: the
same code is correct on one input set and wrong on another, and nothing distinguishes them at
runtime.

## Practical Usage

| Problem | Greedy criterion | Correct? |
|---|---|---|
| Interval scheduling | Earliest end time | **Yes** — exchange argument above |
| [Huffman coding](https://en.wikipedia.org/wiki/Huffman_coding) | Merge the two least frequent | **Yes** |
| Dijkstra's algorithm | Nearest unfinalised vertex | **Yes**, for non-negative weights |
| Minimum spanning tree (Kruskal, Prim) | Cheapest safe edge | **Yes** |
| Fractional knapsack | Highest value per unit weight | **Yes** |
| **0/1 knapsack** | Highest value per unit weight | **No** — needs DP |
| **Coin change**, general denominations | Largest coin first | **No** — needs DP |
| **Travelling salesman** | Nearest unvisited city | **No** — a heuristic, not an optimum |

:::info[Dijkstra's algorithm is a greedy algorithm]
It repeatedly finalises the nearest unfinalised vertex and never revisits it — a textbook greedy
commitment. Its correctness rests on all weights being non-negative, which guarantees no later path
can be shorter. Allow a negative edge and the greedy choice property fails, which is exactly why
[Dijkstra's is wrong on negative weights](../graph-algorithms/shortest-paths.md) and Bellman–Ford
exists.
:::

## Edge Cases & Pitfalls

:::danger[Passing tests is not a proof]
The typical greedy failure is a solution that is correct on every example you tried and wrong on a
case you did not think of — off by one coin, one interval, one unit of value. There is no crash and
no exception.

Before shipping a greedy algorithm, either find the exchange argument, or find a counterexample. If
you can do neither, assume it is wrong and use [dynamic programming](./dynamic-programming.md), which
is slower but does not require the proof.
:::

- **The sort key *is* the algorithm.** Interval scheduling by earliest end time is optimal; by
  earliest start or shortest duration it is not. Getting the criterion wrong produces a working
  program with wrong output.
- **"Greedy" describes strategy, not quality.** A greedy heuristic for an NP-hard problem (nearest
  neighbour for TSP) is a legitimate approximation — just do not describe its output as optimal.
- **Fractional and 0/1 knapsack differ entirely.** Being able to take *part* of an item is what makes
  the greedy choice safe; forbid it and the property vanishes.
- **Ties may need a rule.** When two options look equally good, an arbitrary choice can break the
  exchange argument. Check whether your proof survives ties.

## Comparisons

| | Greedy | [Dynamic programming](./dynamic-programming.md) | [Backtracking](./backtracking.md) |
|---|---|---|---|
| Choices per step | One, committed | All, memoised | All, with pruning |
| Typical complexity | $O(n \log n)$ | $O(n \cdot states)$ | Exponential, pruned |
| Guarantees optimum | Only with a proof | Yes | Yes |
| Memory | $O(1)$ | $O(states)$ | $O(depth)$ |
| Fails by | Returning a wrong answer silently | Being slow or memory-hungry | Taking too long |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 16 — greedy algorithms, the greedy-choice property, and matroid theory as the general condition for greedy correctness.
- Kleinberg & Tardos, *Algorithm Design*, Ch. 4 — the clearest treatment of exchange arguments, with several worked proofs.

### Books & Videos

- Kleinberg & Tardos, *Algorithm Design*, §4.1 — interval scheduling, proved exactly as above.

## Related Pages

- [Dynamic Programming](./dynamic-programming.md) — the fallback when the greedy choice property fails.
- [Shortest Paths](../graph-algorithms/shortest-paths.md) — Dijkstra's, and the precise condition its greediness depends on.
- [Divide & Conquer](./divide-and-conquer.md) — the other pattern relying on optimal substructure.
