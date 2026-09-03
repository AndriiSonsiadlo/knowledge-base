---
id: shortest-paths
title: Shortest Paths
sidebar_label: Shortest Paths
sidebar_position: 2
tags: [computer-science, algorithms, graphs, dijkstra, bellman-ford]
---

# Shortest Paths

"Shortest" means fewest edges on an unweighted graph and lowest total weight on a weighted one, and
the two need different algorithms — which one is decided by two questions: are the edges weighted,
and can any weight be negative?

## Choosing

| Situation | Algorithm | Complexity |
|---|---|---|
| Unweighted graph | [BFS](./traversal.md) | $O(V + E)$ |
| Non-negative weights, one source | **Dijkstra's** | $O((V + E) \log V)$ |
| Negative weights allowed, one source | **Bellman–Ford** | $O(V \cdot E)$ |
| All pairs, dense graph | Floyd–Warshall | $O(V^3)$ |
| Non-negative weights, one target known | A* with an admissible heuristic | Depends on heuristic |

## Mechanism

### Dijkstra's algorithm

Repeatedly finalise the nearest unfinalised vertex, then relax its outgoing edges. A
[priority queue](../data-structures/heaps.md) supplies "nearest" in $O(\log V)$, which is where the log
factor comes from.

<Figure src="/img/cs/algorithms/dijkstra.gif"
        alt="Animation of Dijkstra's algorithm on a weighted graph of six vertices, with tentative distances starting at infinity and being progressively lowered as each nearest vertex is finalised"
        caption="Tentative distances start at ∞ and fall as shorter routes are discovered. Each step permanently fixes the nearest remaining vertex — once fixed, it is never revisited."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Dijkstra_Animation.gif"
        license="Public domain" />

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import heapq

def dijkstra(graph, start):
    """graph: {node: [(neighbour, weight), ...]} with all weights >= 0."""
    dist = {start: 0}
    prev = {start: None}
    pq = [(0, start)]                       # (distance, node)
    done = set()

    while pq:
        d, node = heapq.heappop(pq)
        if node in done:                    # a stale entry — skip it
            continue
        done.add(node)                      # dist[node] is now final

        for nb, weight in graph[node]:
            candidate = d + weight
            if candidate < dist.get(nb, float("inf")):
                dist[nb] = candidate
                prev[nb] = node
                heapq.heappush(pq, (candidate, nb))   # lazy deletion
    return dist, prev
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <limits>
#include <queue>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// graph: node -> [(neighbour, weight), ...] with all weights >= 0.
using Graph = std::unordered_map<int, std::vector<std::pair<int, int>>>;

struct Paths {
    std::unordered_map<int, int> dist;
    std::unordered_map<int, int> prev;
};

Paths dijkstra(const Graph& graph, int start) {
    Paths out{{{start, 0}}, {}};
    using Entry = std::pair<int, int>;                      // (distance, node)
    std::priority_queue<Entry, std::vector<Entry>, std::greater<>> pq;
    pq.push({0, start});
    std::unordered_set<int> done;

    while (!pq.empty()) {
        auto [d, node] = pq.top();
        pq.pop();
        if (done.count(node)) continue;                     // a stale entry — skip it
        done.insert(node);                                  // dist[node] is now final

        for (auto [nb, weight] : graph.at(node)) {
            int candidate = d + weight;
            auto it = out.dist.find(nb);
            if (it == out.dist.end() || candidate < it->second) {
                out.dist[nb] = candidate;
                out.prev[nb] = node;
                pq.push({candidate, nb});                   // lazy deletion
            }
        }
    }
    return out;
}
```

</TabItem>
</Tabs>

The `done` check implements **lazy deletion**: `heapq` cannot decrease an existing entry's key, so
the code pushes a new one and ignores the outdated copy when it surfaces. This is the standard
workaround, it keeps the complexity correct, and it is simpler than maintaining an indexed heap.

### Worked trace: Dijkstra's from A

Run on the [shared weighted graph](./intro.md#the-shared-example-graphs). Each row is one real pop
(stale entries — an earlier, more expensive copy of an already-finalised vertex — are noted but
change nothing):

```text
pop      done so far      dist[A,B,C,D,E,F]              frontier after (stale entries dropped)
A (0)    {A}              0, 4, 2, inf, inf, inf         [(2,C),(4,B)]
C (2)    {A,C}            0, 3, 2, 10, 12, inf           [(3,B),(10,D),(12,E)]     -- (4,B) now stale
B (3)    {A,C,B}          0, 3, 2, 8, 12, inf            [(8,D),(12,E)]           -- (4,B),(10,D) stale
D (8)    {A,C,B,D}        0, 3, 2, 8, 10, 14             [(10,E),(14,F)]          -- (10,D),(12,E) stale
E (10)   {A,C,B,D,E}      0, 3, 2, 8, 10, 13             [(13,F)]                 -- (12,E),(14,F) stale
F (13)   {A,C,B,D,E,F}    0, 3, 2, 8, 10, 13             []                       -- (14,F) popped, also stale
```

Final distances from `A`: `B`=3 via `A->C->B` (cheaper than the direct edge's 4), `C`=2, `D`=8 via
`A->C->B->D`, `E`=10, `F`=13, in increasing-distance pop order `A, C, B, D, E, F` — no path still in
the queue can ever beat one already popped, since every edge weight is non-negative.

:::danger[Dijkstra's is wrong on negative weights — silently]
A negative edge breaks the "never gets shorter" assumption: A→B=5, A→C=6, C→B=−4 finalises B at 5,
then discovers A→C→B costs 2 — but B is already done and never updated. No error, no warning; the
distance is simply wrong. If any weight can be negative, use Bellman–Ford.
:::

### Bellman–Ford

Relax **every** edge, V−1 times. Slower, but it makes no assumption about sign, and it can detect
negative cycles:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def bellman_ford(vertices, edges, start):
    """edges: [(u, v, weight), ...]; weights may be negative."""
    dist = {v: float("inf") for v in vertices}
    dist[start] = 0

    for _ in range(len(vertices) - 1):       # any shortest path has ≤ V−1 edges
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:                      # early exit once stable
            break

    for u, v, w in edges:                    # a further improvement means a negative cycle
        if dist[u] + w < dist[v]:
            raise ValueError("negative cycle reachable from start")
    return dist
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
struct Edge { int u, v, w; };                               // weights may be negative

std::unordered_map<int, long long> bellman_ford(
        const std::vector<int>& vertices, const std::vector<Edge>& edges, int start) {
    constexpr long long INF = std::numeric_limits<long long>::max() / 4;
    std::unordered_map<int, long long> dist;
    for (int v : vertices) dist[v] = INF;
    dist[start] = 0;

    for (std::size_t i = 1; i < vertices.size(); ++i) {     // any shortest path has ≤ V−1 edges
        bool changed = false;
        for (const auto& [u, v, w] : edges) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                changed = true;
            }
        }
        if (!changed) break;                                // early exit once stable
    }

    for (const auto& [u, v, w] : edges)                     // a further improvement means a negative cycle
        if (dist[u] + w < dist[v])
            throw std::runtime_error("negative cycle reachable from start");
    return dist;
}
```

</TabItem>
</Tabs>

The V−1 bound is the whole proof: a shortest path visits each vertex at most once, so it has at most
V−1 edges, and each pass extends every path by at least one edge. **Negative cycles** make "shortest
path" meaningless — you can loop forever, getting cheaper each time — and detecting them is a
feature: it is how currency-arbitrage detection works, with weights set to −log(exchange rate).

### Floyd–Warshall: every pair at once

Running Dijkstra's or Bellman–Ford from every vertex answers "all pairs" too, but Floyd–Warshall
often wins on dense graphs by asking, for each pair `(i, j)`: does routing through `k` shorten the
known path? Trying every `k` as an intermediate, in order, is the whole algorithm:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def floyd_warshall(n, edges):
    """edges: [(u, v, weight), ...]; weights may be negative, but not a negative cycle."""
    INF = float("inf")
    dist = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)

    for k in range(n):                          # k is the newly-allowed intermediate vertex
        for i in range(n):
            for j in range(n):
                through_k = dist[i][k] + dist[k][j]
                if through_k < dist[i][j]:
                    dist[i][j] = through_k
    return dist

# vertices 0..5 = A..F; the shared weighted graph, both directions
graph = {0:[(1,4),(2,2)], 1:[(0,4),(2,1),(3,5)], 2:[(0,2),(1,1),(3,8),(4,10)],
         3:[(1,5),(2,8),(4,2),(5,6)], 4:[(2,10),(3,2),(5,3)], 5:[(3,6),(4,3)]}
expected = [0, 3, 2, 8, 10, 13]                          # the traced distances from A
dist, _ = dijkstra(graph, 0)
assert [dist[v] for v in range(6)] == expected

edges = [(u, v, w) for u in graph for v, w in graph[u]]  # flatten, already both directions
assert [bellman_ford(range(6), edges, 0)[v] for v in range(6)] == expected
assert floyd_warshall(6, edges)[0] == expected           # row 0 (from A) agrees with both above
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
using Matrix = std::vector<std::vector<long long>>;

Matrix floyd_warshall(int n, const std::vector<std::tuple<int, int, int>>& edges) {
    constexpr long long INF = std::numeric_limits<long long>::max() / 4;
    Matrix dist(n, std::vector<long long>(n, INF));
    for (int i = 0; i < n; ++i) dist[i][i] = 0;
    for (const auto& [u, v, w] : edges) dist[u][v] = std::min(dist[u][v], (long long)w);

    for (int k = 0; k < n; ++k)                  // k is the newly-allowed intermediate vertex
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j) {
                long long through_k = dist[i][k] + dist[k][j];
                if (through_k < dist[i][j]) dist[i][j] = through_k;
            }
    return dist;
}
```

</TabItem>
</Tabs>

The `k` loop **must** be outermost, per the DP recurrence `dp[k][i][j] = min(dp[k-1][i][j],
dp[k-1][i][k] + dp[k-1][k][j])` — swapping `k` for `i` still compiles and terminates, but silently
computes the wrong answer for some pairs. A negative cycle shows up afterwards as `dist[i][i] < 0`.

### A\*: Dijkstra's with a hint

For a path to *one* target, A\* orders the queue by `dist[node] + heuristic(node, goal)` instead of
`dist[node]` alone. An **admissible** heuristic (never overestimates) still returns the true shortest
path while exploring far fewer vertices; zero turns A\* back into Dijkstra's exactly — see
[A\* & Heuristic Search](./a-star-and-heuristic-search.md) for the implementation.

## Practical Usage

| Domain | Vertices | Weights |
|---|---|---|
| Navigation | Intersections | Travel time — the reason A\* dominates here |
| [Network routing](../../computer-networks/network-layer-and-routing.md) | Routers | Link cost — OSPF is Dijkstra's, RIP is Bellman–Ford |
| Game AI pathfinding | Grid cells or waypoints | Movement cost |

## Edge Cases & Pitfalls

- **Unreachable vertices** stay at infinity — decide whether that is an error or an expected result.
- **Reconstructing the path** needs the `prev` map, followed backwards from the goal and reversed — returning distances alone is a common oversight.
- **Ties in the priority queue** compare the second tuple element — insert a counter if nodes are not
  orderable, the same hazard as on the [heaps page](../data-structures/heaps.md).
- **Dijkstra's on a dense graph** is $O(V^2)$ with a plain array, beating the heap's $O((V+E)\log V)$
  once E approaches $V^2$.
- **An inadmissible A\* heuristic** returns fast paths that are not necessarily shortest — fine for games, a bug for navigation.

## Comparisons

| | BFS | Dijkstra's | Bellman–Ford | Floyd–Warshall |
|---|---|---|---|---|
| Weights, sources, best for | None, one, unweighted | Non-negative, one, usual case | **Any**, one, cycle check | Any, **all pairs**, small dense |

## Recall

<Recall
  invariant="Once Dijkstra's pops a vertex, its distance is final — no cheaper route can appear later, because every remaining path in the queue is already at least as long. Negative weights break this; Bellman-Ford and Floyd-Warshall never assume it."
  costs={[
    ["Dijkstra's, binary heap (worst)", "O((V + E) log V)"],
    ["Bellman-Ford (worst)", "O(V * E)"],
    ["Floyd-Warshall, all pairs (worst)", "O(V^3)"],
    ["path reconstruction from prev", "O(path length)"],
  ]}
  reachFor="Non-negative weights and one source: Dijkstra's. Negative weights allowed: Bellman-Ford. Every pair, dense graph: Floyd-Warshall."
  trap="Running Dijkstra's on a graph that turns out to have a negative edge — it returns a wrong distance with no error, no exception, and no warning."
/>

## References

- Dijkstra, E.W. (1959), "A note on two problems in connexion with graphs", *Numerische Mathematik* — the original two-page paper.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 24–25 — single-source and all-pairs shortest paths, including Floyd-Warshall's DP formulation and correctness proof.
- Hart, Nilsson & Raphael (1968), "A Formal Basis for the Heuristic Determination of Minimum Cost Paths" — the A\* paper.
- [VisuAlgo — Shortest Paths](https://visualgo.net/en/sssp) — run Dijkstra's and Bellman–Ford on the same graph, including one with negative edges.

## Related Pages

- [Graph Algorithms — Overview](./intro.md) — the shared weighted graph this page's trace runs on.
- [Traversal: BFS & DFS](./traversal.md) — BFS as the unweighted special case.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the structure Dijkstra's complexity depends on.
- [Network Layer & Routing](../../computer-networks/network-layer-and-routing.md) — these algorithms in production.
