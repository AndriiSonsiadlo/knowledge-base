---
id: a-star-and-heuristic-search
title: A* & Heuristic Search
sidebar_label: A* & Heuristic Search
sidebar_position: 9
tags: [computer-science, algorithms, graphs, a-star, heuristics, pathfinding]
---

# A* & Heuristic Search

Dijkstra's algorithm finds the shortest path to *every* vertex by always expanding the closest
unfinished one, with no idea which direction the actual target lies in. When only one destination
matters, that is wasted effort: a search radiating outward in a wrong direction explores just as
eagerly as one radiating toward the goal. **A\*** fixes this with a single change — order the frontier
not by distance-so-far alone, but by distance-so-far *plus an estimate of the distance remaining*. A
good estimate biases the search toward the goal without giving up Dijkstra's guarantee of finding the
true shortest path, provided the estimate obeys one rule.

That rule is what separates "A\* usually works" from "A\* is provably correct." An estimate that never
overestimates the true remaining cost is called **admissible**, and admissibility is exactly the
condition under which A\* is guaranteed to return an optimal path. Get the estimate wrong in the
optimistic direction — underestimate — and the search merely explores more nodes than necessary before
still finding the right answer. Get it wrong in the other direction — overestimate — and A\* can commit
to a real target before ever considering a cheaper route, returning a path that is wrong, not just slow.

:::info[Prerequisites]
[Shortest Paths](./shortest-paths.md) for Dijkstra's algorithm, which A\* is a direct modification of —
this page assumes that mechanism and focuses on the heuristic itself.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **`g(n)`** | The known cost of the best path found so far from the start to node `n` — exactly Dijkstra's tentative distance |
| **`h(n)`** | The heuristic: an *estimate* of the cost remaining from `n` to the goal |
| **`f(n) = g(n) + h(n)`** | The priority A\* pops by — estimated total cost of a path through `n` |
| **Admissible** | `h(n)` never exceeds the true cheapest cost from `n` to the goal, for every `n`. Guarantees an optimal path is found |
| **Consistent** | `h(n) ≤ cost(n, n') + h(n')` for every edge `(n, n')`, and `h(goal) = 0`. Guarantees `f` never decreases along any path, which lets a popped node be closed forever without ever needing to reopen it |
| **Manhattan distance** | `|x1−x2| + |y1−y2|` — admissible and exact for grid movement restricted to 4 directions |
| **Euclidean distance** | `sqrt((x1−x2)² + (y1−y2)²)` — admissible for any movement model, including diagonals, but looser (a weaker lower bound) on a 4-directional grid |

## Mechanism

<Figure src="/img/cs/algorithms/astar-progress-animation.gif"
        alt="Animation of A* search expanding outward from a start cell toward a goal, showing the frontier biased toward the target rather than spreading uniformly"
        caption="The frontier stretches toward the goal instead of spreading as a uniform circle the way Dijkstra's would — the heuristic is doing exactly that work, and nothing else."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Astar_progress_animation.gif"
        license="CC BY 3.0" />

### Grid pathfinding, expansion by expansion

Trace input — an 8-cell grid, 2 rows by 4 columns, one wall, start `S = (0,0)`, goal `G = (1,3)`,
4-directional movement at cost 1 per step, Manhattan heuristic to `G`:

```text
grid (W = wall):
  (0,0) (0,1)  W   (0,3)
  (1,0) (1,1) (1,2) (1,3)=G

h(r,c) = |r-1| + |c-3|     (Manhattan distance to G)

expansion   node    g   h   f    action
1           (0,0)    0   4   4   start; push neighbours (0,1) and (1,0)
2           (0,1)    1   3   4   push (1,1); (0,2) is a wall, skipped
3           (1,0)    1   3   4   only neighbour (1,1) already queued at the same g — no new push
4           (1,1)    2   2   4   push (1,2)
5           (1,2)    3   1   4   push (1,3)
6           (1,3)    4   0   4   goal reached — done
```

`f` stays exactly 4 at every expansion, because this heuristic is exact along the path actually taken:
the wall never forces a detour longer than the unobstructed Manhattan distance, since an alternate
monotonic route around it (through row 1) still costs 4. Ties in `f` are broken by row then column, so
`(0,1)` (row 0) is expanded before `(1,0)` (row 1) at step 2 — an arbitrary but fixed rule, needed
because a heap with no tie-break can pop either one first and still be correct, just in a different
order.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import heapq

def a_star(start, goal, neighbours, heuristic):
    """neighbours(node) -> [(next_node, cost), ...]. Returns (path, cost) or (None, inf)."""
    open_heap = [(heuristic(start), start)]
    g = {start: 0}
    parent = {start: None}
    closed = set()

    while open_heap:
        _, node = heapq.heappop(open_heap)
        if node in closed:
            continue                              # stale entry, safe to skip: h is consistent
        if node == goal:
            path = []
            while node is not None:
                path.append(node)
                node = parent[node]
            return list(reversed(path)), g[goal]
        closed.add(node)
        for nxt, cost in neighbours(node):
            candidate = g[node] + cost
            if nxt not in g or candidate < g[nxt]:
                g[nxt] = candidate
                parent[nxt] = node
                heapq.heappush(open_heap, (candidate + heuristic(nxt), nxt))
    return None, float("inf")


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <cassert>
#include <cmath>
#include <functional>
#include <optional>
#include <queue>
#include <unordered_map>
#include <vector>

using Node = std::pair<int, int>;
struct NodeHash { std::size_t operator()(const Node& n) const {
    return std::hash<long long>()((static_cast<long long>(n.first) << 32) ^ n.second);
}};

int manhattan(Node a, Node b) { return std::abs(a.first - b.first) + std::abs(a.second - b.second); }

std::optional<std::vector<Node>> a_star(
    Node start, Node goal,
    const std::function<std::vector<std::pair<Node, int>>(Node)>& neighbours,
    const std::function<int(Node)>& heuristic) {
    using Entry = std::pair<int, Node>;                     // (f, node)
    std::priority_queue<Entry, std::vector<Entry>, std::greater<>> open;
    open.push({heuristic(start), start});
    std::unordered_map<Node, int, NodeHash> g{{start, 0}};
    std::unordered_map<Node, Node, NodeHash> parent;
    std::unordered_map<Node, bool, NodeHash> closed;

    while (!open.empty()) {
        auto [f, node] = open.top(); open.pop();
        if (closed[node]) continue;
        if (node == goal) {
            std::vector<Node> path{node};
            while (parent.count(path.back())) path.push_back(parent[path.back()]);
            std::reverse(path.begin(), path.end());
            return path;
        }
        closed[node] = true;
        for (auto [nxt, cost] : neighbours(node)) {
            int candidate = g[node] + cost;
            if (!g.count(nxt) || candidate < g[nxt]) {
                g[nxt] = candidate;
                parent[nxt] = node;
                open.push({candidate + heuristic(nxt), nxt});
            }
        }
    }
    return std::nullopt;
}
```

</TabItem>
</Tabs>

### Degrading gracefully, and degrading badly

Setting `h(n) = 0` for every node makes `f(n) = g(n)` always — A\* becomes **exactly** Dijkstra's
algorithm, expanding purely by distance-so-far with no notion of a target direction. This is a graceful
degradation: correctness is untouched, only the "focus toward the goal" speedup is lost.

An **inadmissible** heuristic degrades differently. Consider `S`, `A`, `B`, `G` with edges
`S–A` (1), `A–G` (2), `S–B` (1), `B–G` (1) — the true shortest path is `S-B-G`, cost 2. Give `A` the
admissible, exact heuristic `h(A) = 0` is too pessimistic to matter here; instead overestimate at `B`:
`h(B) = 3`, when the true remaining cost from `B` is only 1.

```text
open = {S: g=0}                       pop S, push A (g=1,h=0,f=1), B (g=1,h=3,f=4)
open = {A: f=1, B: f=4}               pop A (lowest f), push G via A (g=3,h=0,f=3)
open = {B: f=4, G: f=3}               pop G (lowest f) -- G is the goal, search stops

returned path: S-A-G, cost 3.  B, holding the true shortest route (cost 2), is never expanded.
```

The search terminated the instant a *path to the goal* reached the front of the queue, without ever
verifying no cheaper path was still pending — because `h(B) = 3` made `B`'s estimated total cost look
worse than a route that was actually worse. This is the concrete cost of admissibility: without it,
A\* can return a confidently wrong answer, with no signal that anything went wrong.

## Practical Usage

- **Game and robotics pathfinding.** A\* over a grid or navigation mesh is the default for
  point-to-point movement; Manhattan or octile (diagonal-aware) heuristics dominate grid games,
  Euclidean distance dominates free-space robotics.
- **`networkx.algorithms.shortest_paths.astar_path`** takes a `heuristic` callable directly — see the
  [NetworkX documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.astar.astar_path.html),
  which explicitly notes the heuristic must be admissible for the result to be guaranteed shortest.
- **Map routing** typically uses straight-line (great-circle) distance, scaled by the fastest possible
  travel speed on any road, to stay admissible even though real routes rarely travel in a straight line.
- **Heuristic weighting (`w · h(n)`, `w > 1`)** trades optimality for speed deliberately — a common,
  named technique (weighted A\*) for time-constrained pathfinding where a near-optimal path found fast
  beats an optimal one found too late; this intentionally reintroduces the inadmissibility failure mode
  above, as an accepted trade rather than a bug.

```python showLineNumbers
grid = {(0,0), (0,1), (0,3), (1,0), (1,1), (1,2), (1,3)}   # (0,2) is a wall, excluded

def grid_neighbours(node):
    r, c = node
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nxt = (r+dr, c+dc)
        if nxt in grid:
            yield (nxt, 1)

path, cost = a_star((0,0), (1,3), lambda n: list(grid_neighbours(n)), lambda n: manhattan(n, (1,3)))
assert cost == 4
assert path == [(0,0), (0,1), (1,1), (1,2), (1,3)]          # the traced expansion order's route

zero_h_path, zero_h_cost = a_star((0,0), (1,3), lambda n: list(grid_neighbours(n)), lambda n: 0)
assert zero_h_cost == cost                                  # h=0 still finds the optimum -- it's Dijkstra's
```

## Edge Cases & Pitfalls

- **An inconsistent-but-admissible heuristic** does not break optimality outright, but it does break
  the "close a node forever once popped" shortcut used above: without consistency, a cheaper path to an
  already-closed node can appear later, and a naive implementation that never reopens closed nodes can
  still return a suboptimal path even though `h` never overestimated anything. Reopening nodes when a
  cheaper `g` is found restores correctness at the cost of extra work.
- **Ties broken by `h` instead of insertion order** can make the search behave more like greedy
  best-first search — fast, but with no guarantee at all, since it stops weighing `g` sensibly once two
  nodes tie on `f`.
- **A heuristic that is expensive to compute** can make each expansion slower than the nodes it saves —
  Euclidean distance with a `sqrt` call is measurably slower than Manhattan distance per call; on a grid
  with 4-directional movement, Manhattan is both cheaper *and* tighter, so there is no trade-off to make.
- **Forgetting `h(goal) = 0`.** If the heuristic does not vanish at the goal itself, the goal's own `f`
  is inflated and the search can report a cost that does not match the path actually returned.

## Comparisons

| | Explores | Optimal? | Needs |
|---|---|---|---|
| Dijkstra's | Uniformly outward by `g` | Yes | Nothing beyond edge weights |
| **A\*, admissible `h`** | Biased toward the goal | **Yes** | An admissible heuristic |
| A\*, inadmissible `h` | Biased, sometimes wrongly | **No** | — |
| Greedy best-first | Purely by `h`, ignores `g` | No | A heuristic, admissible or not |
| Weighted A\* (`w·h`, `w>1`) | More biased than plain A\* | No (bounded suboptimality) | An admissible base heuristic |

A\* with an admissible heuristic strictly dominates Dijkstra's for single-target search: it never
explores more nodes, and with any real signal about the goal's direction it explores far fewer. Greedy
best-first is faster still but abandons the optimality guarantee entirely, since it never weighs the
cost already paid.

## Recall

<Recall
  invariant="A* orders its frontier by g(n) + h(n); if h never overestimates the true remaining cost (admissible), the first time the goal is popped, its path is optimal — exactly Dijkstra's guarantee, extended by a lower-bound estimate."
  costs={[
    ["A* with an admissible heuristic (worst)", "O((V + E) log V)"],
    ["A* with h = 0 (worst)", "O((V + E) log V) — identical to Dijkstra's"],
    ["heuristic evaluation, Manhattan distance", "O(1)"],
    ["heuristic evaluation, Euclidean distance", "O(1), one sqrt"],
  ]}
  reachFor="One specific target, a graph large enough that exploring it uniformly is wasteful, and a way to estimate remaining distance that never overestimates."
  trap="An inadmissible heuristic doesn't just slow A* down — it can make the search commit to and return a genuinely wrong, non-shortest path, with no error or warning that this happened."
/>

## References

- Hart, P. E., Nilsson, N. J. & Raphael, B., "A Formal Basis for the Heuristic Determination of Minimum
  Cost Paths", *IEEE Trans. SSC* 4(2), 1968 — the original A\* paper and its admissibility-implies-optimality proof.
- S. Russell & P. Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed., §3.5–3.6 — consistency,
  the closed-list argument for never reopening a consistent-heuristic search, and weighted A\*.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 24 — Dijkstra's
  algorithm and its $O((V+E)\log V)$ bound, which A\* inherits unchanged in the worst case.
- [NetworkX `astar_path` documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.astar.astar_path.html)
  — the library call, with an explicit note on the admissibility requirement.

## Related Pages

- [Shortest Paths](./shortest-paths.md) — Dijkstra's algorithm, which this page's mechanism directly extends.
- [Traversal: BFS & DFS](./traversal.md) — BFS as the unweighted, heuristic-free special case of shortest-path search.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the frontier structure both Dijkstra's and A\* pop from.
- [Cheat Sheet](./cheat-sheet.md) — where A\* sits among every other graph algorithm in this folder.
