---
id: minimum-spanning-trees
title: Minimum Spanning Trees
sidebar_label: Minimum Spanning Trees
sidebar_position: 5
tags: [computer-science, algorithms, graphs, mst, kruskal, prim]
---

# Minimum Spanning Trees

Given a connected, undirected, weighted graph, a spanning tree picks exactly `V - 1` edges that keep
every vertex reachable with no cycle. Many spanning trees usually exist; a **minimum** spanning tree
(MST) is one whose edge weights sum to the least possible total. This is the network-design question
in its purest form — wire together a set of sites for the least total cable, pipe, or track — and it
is one of the rare optimization problems where the greedy answer is provably the exact answer, not an
approximation.

Two greedy strategies solve it, and they differ in which direction they grow the tree from. **Kruskal's
algorithm** looks at the whole edge list at once, sorted cheapest first, and accepts an edge unless it
would close a cycle — a global, edge-centric sweep. **Prim's algorithm** grows a single tree outward
from one vertex, at each step crossing its current boundary at the cheapest available edge — a local,
vertex-centric expansion. Both are correct for the same underlying reason, not by coincidence, and
that reason is worth stating once rather than re-deriving twice.

That reason is the **cut property**: partition the vertices into any two nonempty groups, and the
*minimum-weight edge crossing that partition* belongs to some MST. Kruskal's sorted sweep and Prim's
frontier expansion are both just repeatedly finding a cut and taking its cheapest crossing edge — they
merely choose *which* cut to look at in different orders.

## Core Concepts

| Term | Meaning |
|---|---|
| **Cut** | Any partition of the vertices into two nonempty sets. An edge "crosses" the cut if its endpoints are on opposite sides |
| **Cut property** | The minimum-weight edge crossing any cut is in *some* MST — the theorem both algorithms lean on (CLRS 4th ed., Thm 21.1) |
| **Safe edge** | An edge that provably belongs to some MST given what has been built so far — what the cut property certifies |
| **Frontier** | Prim's boundary: edges from the tree built so far to vertices not yet in it |
| **Light edge** | The minimum-weight edge crossing a particular cut — the one the cut property says is safe |

## Mechanism

### Kruskal's algorithm: sort, then union-find

<Figure src="/img/cs/algorithms/mst-kruskal.gif"
        alt="Animation of Kruskal's algorithm growing a minimum spanning forest by repeatedly adding the cheapest edge that does not close a cycle"
        caption="Edges are tried cheapest first. Each accepted edge joins two separate components; each rejected one would have closed a cycle inside a component already connected."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:MST_kruskal_en.gif"
        license="CC BY-SA 3.0" />

Sort every edge once, then walk the sorted list, using [union-find](../data-structures/union-find.md)
exactly as in [cycle detection](./cycle-detection.md#undirected-graphs-union-find) to reject any edge
whose endpoints are already connected:

```text
shared graph, edges sorted by weight ascending (ties broken alphabetically):
  B-C 1, A-C 2, D-E 2, E-F 3, A-B 4, B-D 5, D-F 6, C-D 8, C-E 10

  edge    accept?   reason
  B-C 1   accept    B, C in separate components -> {B,C}
  A-C 2   accept    A alone, C in {B,C}          -> {A,B,C}
  D-E 2   accept    D, E in separate components  -> {D,E}
  E-F 3   accept    F alone, E in {D,E}          -> {D,E,F}
  A-B 4   reject    A and B already both in {A,B,C}: closes a cycle
  B-D 5   accept    {A,B,C} and {D,E,F} merge     -> {A,B,C,D,E,F}
                     5 edges accepted = V-1: MST complete, remaining edges unneeded
```

Total weight 1 + 2 + 2 + 3 + 5 = **13**.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def kruskal_mst(n, edges):
    """edges: [(u, v, w), ...] over vertices 0..n-1. Returns (mst_edges, total_weight)."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]      # path halving
            x = parent[x]
        return x

    mst, total = [], 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            mst.append((u, v, w))
            total += w
    return mst, total
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <numeric>
#include <tuple>
#include <vector>

using Edge = std::tuple<int, int, int>;   // u, v, weight

std::pair<std::vector<Edge>, int> kruskal_mst(int n, std::vector<Edge> edges) {
    std::vector<int> parent(n);
    std::iota(parent.begin(), parent.end(), 0);
    auto find = [&](int x) {
        while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; }
        return x;
    };

    std::sort(edges.begin(), edges.end(),
              [](const Edge& a, const Edge& b) { return std::get<2>(a) < std::get<2>(b); });

    std::vector<Edge> mst;
    int total = 0;
    for (const auto& [u, v, w] : edges) {
        int ru = find(u), rv = find(v);
        if (ru != rv) {
            parent[ru] = rv;
            mst.push_back({u, v, w});
            total += w;
        }
    }
    return {mst, total};
}
```

</TabItem>
</Tabs>

### Prim's algorithm: a heap over the frontier

<Figure src="/img/cs/algorithms/mst-prim.gif"
        alt="Animation of Prim's algorithm growing a single tree outward from a start vertex, always adding the cheapest edge leaving the tree built so far"
        caption="Prim keeps exactly one growing tree and always crosses its current frontier at the cheapest available edge — the frontier is a priority queue, not the whole edge list."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:PrimAlgDemo.gif"
        license="CC BY-SA 4.0" />

Starting from `A`, the frontier is every edge from a vertex already in the tree to one that is not,
held in a [min-heap](../data-structures/heaps.md) so the cheapest is always on top:

```text
start = A. tree = {A}. frontier (min-heap by weight) seeded from A's edges: A-C 2, A-B 4

  pop      in tree already?   action                              tree
  A-C 2    no                 accept, push C's edges (C-B 1, C-D 8, C-E 10)   {A,C}
  C-B 1    no                 accept, push B's edges (B-D 5)                  {A,C,B}
  C-B 1    (B already popped once above; duplicate heap entries are just skipped)
  B-D 5    no                 accept, push D's edges (D-E 2, D-F 6)           {A,C,B,D}
  D-E 2    no                 accept, push E's edges (E-F 3)                  {A,C,B,D,E}
  D-F 6    -- skipped: F not yet reached by the cheaper E-F 3, popped next --
  E-F 3    no                 accept                                          {A,C,B,D,E,F}
```

Total weight 2 + 1 + 5 + 2 + 3 = **13** — the same weight Kruskal found, and in fact the same five
edges, since this graph's MST happens to be unique.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import heapq

def prim_mst(n, adj, start=0):
    """adj: {u: [(v, w), ...]}. Returns (mst_edges, total_weight)."""
    visited = [False] * n
    visited[start] = True
    frontier = [(w, start, v) for v, w in adj[start]]
    heapq.heapify(frontier)

    mst, total = [], 0
    while frontier and len(mst) < n - 1:
        w, u, v = heapq.heappop(frontier)
        if visited[v]:
            continue                            # a stale, already-superseded frontier entry
        visited[v] = True
        mst.append((u, v, w))
        total += w
        for nv, nw in adj[v]:
            if not visited[nv]:
                heapq.heappush(frontier, (nw, v, nv))
    return mst, total
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <queue>

using AdjList = std::vector<std::vector<std::pair<int, int>>>;   // adj[u] = {(v, w), ...}

std::pair<std::vector<Edge>, int> prim_mst(int n, const AdjList& adj, int start = 0) {
    std::vector<bool> visited(n, false);
    visited[start] = true;
    using Item = std::tuple<int, int, int>;                       // weight, from, to
    std::priority_queue<Item, std::vector<Item>, std::greater<>> frontier;
    for (auto [v, w] : adj[start]) frontier.push({w, start, v});

    std::vector<Edge> mst;
    int total = 0;
    while (!frontier.empty() && static_cast<int>(mst.size()) < n - 1) {
        auto [w, u, v] = frontier.top();
        frontier.pop();
        if (visited[v]) continue;               // stale entry
        visited[v] = true;
        mst.push_back({u, v, w});
        total += w;
        for (auto [nv, nw] : adj[v])
            if (!visited[nv]) frontier.push({nw, v, nv});
    }
    return {mst, total};
}
```

</TabItem>
</Tabs>

Neither algorithm removes stale frontier entries when a vertex is reached more cheaply later — it is
cheaper to leave them and skip them on pop (`if visited[v]: continue`) than to search the heap for an
entry to delete, since binary heaps have no efficient decrease-key.

## Practical Usage

- **`scipy.sparse.csgraph.minimum_spanning_tree`** implements Kruskal's algorithm over a sparse
  adjacency matrix and returns the MST as another sparse matrix — see
  [the SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.minimum_spanning_tree.html)
  for the exact input format (an upper-triangular or symmetric weight matrix).
- **C++ Boost Graph Library**'s `boost::kruskal_minimum_spanning_tree` and
  `boost::prim_minimum_spanning_tree` are the standard choices when the graph is already a
  `boost::adjacency_list`; the standard library itself has no MST algorithm.
- **Network design** is the textbook application: minimum cable length connecting offices, minimum
  pipe length connecting reservoirs — anywhere "connect everything, minimize total cost" is literal,
  not a metaphor.
- **Clustering.** Removing the `k - 1` most expensive edges from an MST splits the graph into exactly
  `k` clusters, each internally connected by cheap edges — single-linkage clustering is MST computation
  followed by this cut.

```python showLineNumbers
# vertices 0..5 = A..F; edges as (u, v, weight) both ways implied
edges = [(0,1,4), (0,2,2), (1,2,1), (1,3,5), (2,3,8), (2,4,10), (3,4,2), (3,5,6), (4,5,3)]
mst, total = kruskal_mst(6, edges)
assert total == 13
assert sorted(mst) == [(0, 2, 2), (1, 2, 1), (1, 3, 5), (3, 4, 2), (4, 5, 3)]

adj = {i: [] for i in range(6)}
for u, v, w in edges:
    adj[u].append((v, w))
    adj[v].append((u, w))
prim_mst_edges, prim_total = prim_mst(6, adj, start=0)
assert prim_total == 13                             # same weight as Kruskal, as the cut property guarantees
```

## Edge Cases & Pitfalls

- **Disconnected graphs have no spanning tree.** Kruskal terminates having accepted fewer than
  `V - 1` edges; Prim's frontier empties before every vertex is reached. Check the edge count (or
  visited count) before trusting the result — neither algorithm raises on its own.
- **Negative weights are fine.** Unlike shortest-path algorithms, MST correctness never assumes
  non-negative weights; the cut property holds regardless of sign.
- **Equal weights mean multiple correct MSTs.** Both algorithms are then correct but may disagree
  with each other, or with a different tie-breaking rule, on *which* MST — only the total weight is
  guaranteed to match. This graph has no weight ties among the accepted edges, so its MST is unique.
- **Prim needs a starting vertex; Kruskal does not.** Prim's result is the same total weight from any
  start (only the traversal order differs), but a bug that reseeds the frontier incorrectly on restart
  can silently produce a spanning forest instead of a tree.
- **Directed graphs need a different algorithm** (minimum arborescence / Chu-Liu-Edmonds) — Kruskal
  and Prim both assume that crossing a cut in either direction costs the same.

## Comparisons

| | Best for | Time (worst) | Structure needed | Notes |
|---|---|---|---|---|
| **Kruskal** | Sparse graphs, edges already listed | O(E log E) | Flat edge list + union-find | Dominated by the one sort |
| **Prim (binary heap)** | Dense graphs, adjacency already built | O(E log V) | Adjacency list + heap | Never sorts the whole edge set |
| Prim (array, no heap) | Very dense graphs | O(V²) | Adjacency matrix | Beats the heap version when E is close to V² |

Kruskal wins when the graph arrives as a flat edge list and is sparse — the sort dominates, and E log
E is small. Prim wins when the graph is already an adjacency list and dense, since it never needs the
full sorted edge order, only the current frontier's minimum; the array-based (heapless) variant of
Prim is actually faster still on the densest graphs, because E log V's log factor stops paying for
itself once E approaches V² (Sedgewick & Wayne 4th ed., §4.3, gives the crossover analysis in detail).

## Recall

<Recall
  invariant="The cut property: for any partition of the vertices into two nonempty sets, the minimum-weight edge crossing that cut belongs to some MST. Kruskal and Prim both just apply this to a different sequence of cuts."
  costs={[
    ["Kruskal, sort + union-find (worst)", "O(E log E)"],
    ["Prim, binary heap (worst)", "O(E log V)"],
    ["Prim, adjacency matrix, no heap (worst)", "O(V²)"],
    ["union-find per edge, amortized", "O(α(V))"],
  ]}
  reachFor="Connect every vertex in a weighted undirected graph for the least total edge weight — network design, single-linkage clustering, approximating TSP's lower bound."
  trap="Assuming Prim needs to see the whole edge list up front the way Kruskal does. Prim only ever looks at the current frontier; feeding it a sorted edge list first is wasted work Kruskal already does instead."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 21 — the cut property
  (Thm 21.1), Kruskal's and Prim's algorithms, and their correctness proofs from the same theorem.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §4.3 "Minimum Spanning Trees" — both algorithms measured
  against each other, plus the array-vs-heap crossover for Prim on dense graphs.
- J. B. Kruskal, "On the Shortest Spanning Subtree of a Graph...", *Proc. AMS* 7(1), 1956 — the
  original paper.
- R. C. Prim, "Shortest Connection Networks and Some Generalizations", *Bell System Technical
  Journal* 36(6), 1957 — the original paper, framed as a telephone-network cost problem.
- [SciPy `csgraph.minimum_spanning_tree` documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.minimum_spanning_tree.html)
  — the stdlib-adjacent implementation most Python code actually calls.

## Related Pages

- [Union-Find](../data-structures/union-find.md) — the cycle test Kruskal runs on every candidate edge.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the frontier structure Prim pops from.
- [Cycle Detection](./cycle-detection.md) — the same union-find check, applied here to reject an edge instead of report a cycle.
- [Shortest Paths](./shortest-paths.md) — Prim and Dijkstra share a frontier-and-heap shape but optimize different quantities: total tree weight versus per-vertex distance from a source.
