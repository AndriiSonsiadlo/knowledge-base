---
id: graph-algorithms-intro
title: Graph Algorithms — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, graphs]
---

# Graph Algorithms — Overview


Once a problem is expressed as a [graph](../data-structures/graphs.md), a small set of algorithms
answers most of the questions worth asking about it: what is reachable, what is closest, and in what
order can things be done. Recognising that a problem *is* a graph problem is usually harder than
running the algorithm afterwards.

## In This Section

- **[Traversal: BFS & DFS](./traversal.md)** — the two ways to visit every reachable vertex, and why
  the choice of queue or stack changes everything downstream.
- **[Shortest Paths](./shortest-paths.md)** — BFS for unweighted graphs, Dijkstra's for non-negative
  weights, Bellman–Ford when weights can be negative.
- **[Topological Sort](./topological-sort.md)** — ordering a DAG so every dependency comes first.

## Choosing an Algorithm

| Question | Algorithm | Complexity |
|---|---|---|
| Is B reachable from A? | BFS or DFS | O(V + E) |
| Fewest **edges** from A to B? | BFS | O(V + E) |
| Cheapest path, non-negative weights? | Dijkstra's | O((V + E) log V) |
| Cheapest path, negative weights allowed? | Bellman–Ford | O(V·E) |
| Cheapest paths between *all* pairs? | Floyd–Warshall | O(V³) |
| A valid order respecting dependencies? | Topological sort | O(V + E) |
| Does the graph contain a cycle? | DFS, or a failed topological sort | O(V + E) |
| Which vertices form connected groups? | BFS or DFS from each unvisited vertex | O(V + E) |

:::warning[Use BFS, not Dijkstra's, on unweighted graphs]
When every edge costs the same, BFS already finds shortest paths — in O(V + E), with no priority
queue. Reaching for Dijkstra's adds a log factor and considerable machinery for no benefit. Treat
"all weights equal" as a special case worth checking for.
:::

## The Shared Skeleton

Nearly every algorithm here is the same loop with a different container and a different bookkeeping
rule:

```python showLineNumbers
def traverse(graph, start):
    frontier = container([start])       # stack → DFS, queue → BFS, heap → Dijkstra's
    visited = {start}
    while frontier:
        node = frontier.take()          # pop / popleft / heappop
        process(node)
        for neighbour in graph[node]:
            if neighbour not in visited:
                visited.add(neighbour)
                frontier.add(neighbour)
```

Swapping a stack for a queue turns depth-first into breadth-first. Swapping the queue for a
[priority queue](../data-structures/heaps.md) keyed by distance turns BFS into Dijkstra's. The
differences between these algorithms are smaller than their reputations suggest.

## Related Pages

- [Graphs](../data-structures/graphs.md) — representations, and the terminology used throughout.
- [Stacks & Queues](../data-structures/stacks-and-queues.md) — the containers that decide the traversal order.
- [Network Layer & Routing](../../computer-networks/network-layer-and-routing.md) — shortest-path algorithms running on the actual internet.
