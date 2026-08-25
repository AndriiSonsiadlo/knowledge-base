---
id: graphs
title: Graphs
sidebar_label: Graphs
sidebar_position: 8
tags: [computer-science, algorithms, data-structures, graph]
---

# Graphs


A graph is a set of **vertices** and a set of **edges** connecting them. That is nearly no structure
at all, which is precisely why it models so much: road networks, social connections, package
dependencies, web links, state machines, and the call graph of the program you are reading this in.

Trees and linked lists are special cases — a tree is a connected graph with no cycles, a linked list
a tree where every node has one child.

<Figure src="/img/cs/algorithms/undirected-graph.png"
        alt="Six numbered vertices connected by undirected edges, with vertex 6 attached to the rest by a single edge and vertices 1, 2 and 5 forming a triangle"
        caption="An undirected graph on six vertices. Note vertex 6 hanging off a single edge — removing it disconnects the graph, which makes it a bridge."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:6n-graf.svg"
        license="Public domain" />

## Core Concepts

| Term | Meaning |
|---|---|
| **Vertex (node)** | An entity |
| **Edge** | A relationship between two vertices |
| **Directed / undirected** | Whether edges have a direction (follower vs. friendship) |
| **Weighted** | Edges carry a cost — distance, latency, price |
| **Degree** | Number of edges at a vertex (in-degree/out-degree when directed) |
| **Path** | A sequence of vertices joined by edges |
| **Cycle** | A path returning to its start |
| **Connected** | Every vertex reachable from every other |
| **DAG** | Directed acyclic graph — directed, no cycles |
| **Dense / sparse** | E close to V² / E close to V |

### DAGs deserve their own line

<Figure src="/img/cs/algorithms/dag.png"
        alt="A directed acyclic graph: several vertices joined by arrows, with no sequence of arrows leading back to a vertex already visited"
        caption="A DAG. Because no path returns to where it started, the vertices can always be laid out so that every arrow points forward — that ordering is a topological sort."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Directed_acyclic_graph_2.svg"
        license="Public domain" />

Acyclicity is what makes dependency resolution, build systems, task scheduling and spreadsheet
recalculation possible: it guarantees a valid order exists. A cycle in any of those is precisely the
error condition ("circular dependency"). See
[Topological Sort](../graph-algorithms/topological-sort.md).

## Architecture / Mechanism

### The two representations

**Adjacency list** — each vertex stores its neighbours:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
graph = {
    1: [2, 5],
    2: [1, 3, 5],
    3: [2, 4],
    4: [3, 5, 6],
    5: [1, 2, 4],
    6: [4],
}
# Weighted: store (neighbour, weight) pairs
weighted = {1: [(2, 7), (5, 3)], ...}
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
std::unordered_map<int, std::vector<int>> graph{
    {1, {2, 5}},
    {2, {1, 3, 5}},
    {3, {2, 4}},
    {4, {3, 5, 6}},
    {5, {1, 2, 4}},
    {6, {4}},
};
// Weighted: store (neighbour, weight) pairs
std::unordered_map<int, std::vector<std::pair<int, int>>> weighted{
    {1, {{2, 7}, {5, 3}}},
    // ...
};
```

</TabItem>
</Tabs>

**Adjacency matrix** — a V×V grid where `m[i][j]` marks an edge:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
#      1  2  3  4  5  6
m = [[0, 1, 0, 0, 1, 0],   # 1
     [1, 0, 1, 0, 1, 0],   # 2
     [0, 1, 0, 1, 0, 0],   # 3
     [0, 0, 1, 0, 1, 1],   # 4
     [1, 1, 0, 1, 0, 0],   # 5
     [0, 0, 0, 1, 0, 0]]   # 6
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
//                                    1  2  3  4  5  6
std::array<std::array<int, 6>, 6> m{{{0, 1, 0, 0, 1, 0},    // 1
                                     {1, 0, 1, 0, 1, 0},    // 2
                                     {0, 1, 0, 1, 0, 0},    // 3
                                     {0, 0, 1, 0, 1, 1},    // 4
                                     {1, 1, 0, 1, 0, 0},    // 5
                                     {0, 0, 0, 1, 0, 0}}};  // 6
```

</TabItem>
</Tabs>

| | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | O(V + E) | O(V²) |
| Is there an edge u→v? | O(degree(u)) | **O(1)** |
| Iterate u's neighbours | O(degree(u)) | O(V) — scans empty cells too |
| Add an edge | O(1) | O(1) |
| Best for | **Sparse graphs** — nearly all real ones | Dense graphs; matrix algorithms |

:::tip[Default to the adjacency list]
Real graphs are overwhelmingly sparse. A social network with a million users and a hundred friends
each has 10⁸ edges — an adjacency list holds that comfortably, while the matrix needs 10¹² cells,
99.99% of them zero. Reach for a matrix only when the graph is genuinely dense, or when an algorithm
wants matrix form (Floyd–Warshall, spectral methods).
:::

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
from collections import defaultdict

# Building an undirected graph from an edge list
graph = defaultdict(list)
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)      # omit this line for a directed graph

# Degree of a vertex
len(graph[v])
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Building an undirected graph from an edge list
std::unordered_map<int, std::vector<int>> graph;
for (auto [u, v] : edges) {
    graph[u].push_back(v);
    graph[v].push_back(u);      // omit this line for a directed graph
}

// Degree of a vertex
graph[v].size();
```

</TabItem>
</Tabs>

| Domain | Vertices | Edges | Question asked |
|---|---|---|---|
| Maps / navigation | Intersections | Roads, weighted by time | [Shortest path](../graph-algorithms/shortest-paths.md) |
| Social networks | People | Friendships / follows | Degrees of separation, communities |
| Package managers | Packages | "depends on" | [Topological order](../graph-algorithms/topological-sort.md), cycle detection |
| Compilers | Basic blocks | Control flow | Reachability, dominance, dead code |
| Networks | Routers | Links, weighted by cost | [Routing](../../computer-networks/network-layer-and-routing.md) |
| Web search | Pages | Hyperlinks | PageRank |

## Edge Cases & Pitfalls

- **Forgetting the reverse edge** builds a directed graph when you wanted an undirected one, and the
  bug surfaces much later as an unreachable vertex.
- **Not tracking visited vertices** turns any traversal of a cyclic graph into an infinite loop. This
  is the difference between graph traversal and tree traversal, and the most common graph bug there
  is.
- **Disconnected graphs.** A traversal from one vertex reaches only its component. Finding all
  components means looping over every vertex and starting a traversal from each unvisited one.
- **Self-loops and parallel edges** break assumptions in hand-written algorithms. Decide whether your
  representation permits them.
- **Vertex identity.** Using mutable objects as vertex keys in a dict has the same hazard described
  under [hash tables](./hash-tables.md); integer or string IDs are safer.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §22.1 — graph representations and their trade-offs.
- Sedgewick & Wayne, *Algorithms*, 4th ed., Ch. 4 — "Graphs", covering undirected, directed, weighted and shortest-path graphs in turn.

### Books & Videos

- [VisuAlgo — Graph Structures](https://visualgo.net/en/graphds) — build graphs and switch representations interactively.

## Related Pages

- [Traversal: BFS & DFS](../graph-algorithms/traversal.md) — the two ways to walk a graph.
- [Shortest Paths](../graph-algorithms/shortest-paths.md) — Dijkstra's and Bellman–Ford.
- [Topological Sort](../graph-algorithms/topological-sort.md) — ordering a DAG.
