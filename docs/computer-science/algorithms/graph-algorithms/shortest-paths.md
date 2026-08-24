---
id: shortest-paths
title: Shortest Paths
sidebar_label: Shortest Paths
sidebar_position: 2
tags: [computer-science, algorithms, graphs, dijkstra, bellman-ford]
---

# Shortest Paths


"Shortest" means fewest edges on an unweighted graph and lowest total weight on a weighted one, and
the two need different algorithms. Which one you need is decided by two questions: are the edges
weighted, and can any weight be negative?

## Choosing

| Situation | Algorithm | Complexity |
|---|---|---|
| Unweighted graph | [BFS](./traversal.md) | O(V + E) |
| Non-negative weights, one source | **Dijkstra's** | O((V + E) log V) |
| Negative weights allowed, one source | **Bellman–Ford** | O(V·E) |
| All pairs, dense graph | Floyd–Warshall | O(V³) |
| Non-negative weights, one target known | A* with an admissible heuristic | Depends on the heuristic |

## Architecture / Mechanism

### Dijkstra's algorithm

Repeatedly finalise the nearest unfinalised vertex, then relax its outgoing edges. A
[priority queue](../data-structures/heaps.md) supplies "nearest" in O(log V), which is where the log
factor comes from.

<Figure src="/img/cs/algorithms/dijkstra.gif"
        alt="Animation of Dijkstra's algorithm on a weighted graph of six vertices, with tentative distances starting at infinity and being progressively lowered as each nearest vertex is finalised"
        caption="Tentative distances start at ∞ and fall as shorter routes are discovered. Each step permanently fixes the nearest remaining vertex — once fixed, it is never revisited."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Dijkstra_Animation.gif"
        license="Public domain" />

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

The `done` check implements **lazy deletion**: `heapq` cannot decrease an existing entry's key, so
the code pushes a new one and ignores the outdated copy when it surfaces. This is the standard
workaround, it keeps the complexity correct, and it is simpler than maintaining an indexed heap.

:::danger[Dijkstra's is wrong on negative weights — silently]
The algorithm assumes that once a vertex is finalised, no shorter route to it can exist, because
every remaining path is at least as long. A negative edge breaks that assumption: a longer-looking
route can later become shorter.

Consider A→B = 5, A→C = 6, C→B = −4. Dijkstra's finalises B at 5, then discovers A→C→B costs 2 — but
B is already done and never updated. There is no error and no warning; the returned distance is
simply wrong. If any weight can be negative, use Bellman–Ford.
:::

### Bellman–Ford

Relax **every** edge, V−1 times. Slower, but it makes no assumption about sign, and it can detect
negative cycles:

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

The V−1 bound is the whole proof: a shortest path visits each vertex at most once, so it has at most
V−1 edges, and each pass extends every path by at least one edge.

**Negative cycles** make "shortest path" meaningless — you can loop forever, getting cheaper each
time. Detecting them is a feature, not a limitation: it is how currency-arbitrage detection works,
with edge weights set to the negative logarithm of exchange rates.

### A\*: Dijkstra's with a hint

When you want the path to *one* target rather than to everything, A\* orders the queue by
`distance so far + estimated distance remaining`. With an **admissible** heuristic — one that never
overestimates — it returns the true shortest path while exploring far fewer vertices.

```python showLineNumbers
priority = dist[node] + heuristic(node, goal)   # the only change from Dijkstra's
```

For map routing, straight-line distance is the standard admissible heuristic. A heuristic of zero
turns A\* back into Dijkstra's exactly.

## Practical Usage

| Domain | Vertices | Weights |
|---|---|---|
| Navigation | Intersections | Travel time — the reason A\* dominates here |
| [Network routing](../../computer-networks/network-layer-and-routing.md) | Routers | Link cost — OSPF is Dijkstra's, RIP is Bellman–Ford |
| Game AI pathfinding | Grid cells or waypoints | Movement cost |
| Currency arbitrage | Currencies | −log(exchange rate) — a negative cycle is a profit |
| Project scheduling | Tasks | Duration, often negated to find the longest path |

## Edge Cases & Pitfalls

- **Unreachable vertices** stay at infinity. Decide whether that is an error or an expected result.
- **Reconstructing the path** needs the `prev` map, followed backwards from the goal and reversed.
  Returning distances alone is a common oversight.
- **Ties in the priority queue** compare the second tuple element. If nodes are not orderable, insert
  a counter — the same hazard described on the [heaps page](../data-structures/heaps.md).
- **Dijkstra's on a dense graph** is O(V²) with a simple array and O((V+E) log V) with a heap; the
  array version is actually faster when E approaches V².
- **An inadmissible A\* heuristic** returns paths quickly and they are not necessarily shortest. That
  is a legitimate trade for games, and a bug for navigation.

## Comparisons

| | BFS | Dijkstra's | Bellman–Ford | Floyd–Warshall |
|---|---|---|---|---|
| Weights | None | Non-negative | **Any** | Any |
| Sources | One | One | One | **All pairs** |
| Complexity | O(V + E) | O((V + E) log V) | O(V·E) | O(V³) |
| Detects negative cycles | — | No | **Yes** | Yes |
| Best for | Unweighted | The usual case | Negative weights | Small dense graphs |

## References

- Dijkstra, E.W. (1959), "A note on two problems in connexion with graphs", *Numerische Mathematik* — the original two-page paper.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 24–25 — single-source and all-pairs shortest paths, with correctness proofs.
- Hart, Nilsson & Raphael (1968), "A Formal Basis for the Heuristic Determination of Minimum Cost Paths" — the A\* paper.

### Books & Videos

- [VisuAlgo — Shortest Paths](https://visualgo.net/en/sssp) — run Dijkstra's and Bellman–Ford on the same graph, including one with negative edges.

## Related Pages

- [Traversal: BFS & DFS](./traversal.md) — BFS as the unweighted special case.
- [Heaps & Priority Queues](../data-structures/heaps.md) — the structure Dijkstra's complexity depends on.
- [Network Layer & Routing](../../computer-networks/network-layer-and-routing.md) — these algorithms in production.
