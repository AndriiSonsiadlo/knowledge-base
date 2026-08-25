---
id: topological-sort
title: Topological Sort
sidebar_label: Topological Sort
sidebar_position: 3
tags: [computer-science, algorithms, graphs, dag, topological-sort]
---

# Topological Sort


A topological sort orders the vertices of a **directed acyclic graph** so that every edge points
forward — if A must happen before B, A appears earlier. It is the algorithm behind build systems,
package managers, task schedulers and spreadsheet recalculation, all of which face the same question:
*given these dependencies, what order can I do the work in?*

<Figure src="/img/cs/algorithms/topological-order.png"
        alt="A directed acyclic graph drawn so that every arrow points from left to right, with no arrow doubling back"
        caption="The same DAG laid out in topological order. Every arrow points forward — that layout existing at all is exactly what acyclicity guarantees."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Topological_Ordering.svg"
        license="CC0" />

## Core Concepts

| Term | Meaning |
|---|---|
| **DAG** | Directed acyclic graph — the precondition. A cycle makes ordering impossible |
| **In-degree** | Number of incoming edges; a vertex with in-degree 0 has no unmet prerequisites |
| **Valid orderings** | Usually many. The algorithms find *a* valid order, not *the* order |

:::info[A cycle is not a failure mode — it is the answer]
If the graph has a cycle, no valid ordering exists, and both algorithms below detect it. That
detection is often the more useful output: "circular dependency between A, B and C" is precisely what
a package manager or build tool needs to report.
:::

## Architecture / Mechanism

### Kahn's algorithm (BFS-based)

Repeatedly take a vertex with no remaining prerequisites, output it, and remove its edges:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
from collections import deque

def topological_sort(graph):
    """graph: {node: [dependents...]}, an edge u -> v meaning u must come before v."""
    in_degree = {v: 0 for v in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] += 1

    queue = deque(v for v, d in in_degree.items() if d == 0)
    order = []

    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            in_degree[v] -= 1           # u is done; one prerequisite satisfied
            if in_degree[v] == 0:
                queue.append(v)

    if len(order) != len(graph):        # some vertices never reached in-degree 0
        raise ValueError("graph contains a cycle")
    return order
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// graph: u -> [dependents...], an edge u -> v meaning u must come before v.
using Graph = std::unordered_map<int, std::vector<int>>;

std::vector<int> topological_sort(const Graph& graph) {
    std::unordered_map<int, int> in_degree;
    for (const auto& [u, outs] : graph) {
        in_degree.try_emplace(u, 0);
        for (int v : outs) ++in_degree[v];
    }

    std::deque<int> queue;
    for (const auto& [v, d] : in_degree)
        if (d == 0) queue.push_back(v);

    std::vector<int> order;
    while (!queue.empty()) {
        int u = queue.front();
        queue.pop_front();
        order.push_back(u);
        for (int v : graph.at(u))
            if (--in_degree[v] == 0)        // u is done; one prerequisite satisfied
                queue.push_back(v);
    }

    if (order.size() != graph.size())       // some vertices never reached in-degree 0
        throw std::runtime_error("graph contains a cycle");
    return order;
}
```

</TabItem>
</Tabs>

The final length check is the cycle detection: vertices inside a cycle always have at least one
unsatisfied prerequisite, so they never enter the queue.

### DFS-based

Run [depth-first search](./traversal.md) and prepend each vertex as it *finishes*. A vertex finishes
only after everything it depends on has, so the reversed finishing order is a topological order:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def topological_sort_dfs(graph):
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {v: WHITE for v in graph}
    order = []

    def visit(u):
        if colour[u] == GREY:
            raise ValueError("graph contains a cycle")
        if colour[u] == BLACK:
            return
        colour[u] = GREY
        for v in graph[u]:
            visit(v)
        colour[u] = BLACK
        order.append(u)                 # post-order: appended after all descendants

    for v in graph:
        visit(v)
    return order[::-1]                  # reverse the finishing order
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
enum Colour { WHITE, GREY, BLACK };

std::vector<int> topological_sort_dfs(const Graph& graph) {
    std::unordered_map<int, Colour> colour;
    for (const auto& [v, outs] : graph) colour[v] = WHITE;
    std::vector<int> order;

    auto visit = [&](int u, auto&& self) -> void {
        if (colour[u] == GREY) throw std::runtime_error("graph contains a cycle");
        if (colour[u] == BLACK) return;
        colour[u] = GREY;
        for (int v : graph.at(u)) self(v, self);
        colour[u] = BLACK;
        order.push_back(u);                 // post-order: pushed after all descendants
    };

    for (const auto& [v, outs] : graph) visit(v, visit);
    std::reverse(order.begin(), order.end());   // reverse the finishing order
    return order;
}
```

</TabItem>
</Tabs>

| | Kahn's | DFS-based |
|---|---|---|
| Traversal | Breadth-first | Depth-first |
| Cycle detection | Output shorter than vertex count | A GREY vertex revisited |
| Recursion | None | Yes — stack depth O(V) |
| Ordering control | Swap the queue for a [heap](../data-structures/heaps.md) to get a deterministic or prioritised order | Fixed by the traversal |
| Natural extension | Level-by-level parallel scheduling | — |

Kahn's is usually preferable: it is iterative, its cycle detection is a single comparison, and it
extends naturally to the parallel case below.

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Everything at the same "level" has no dependencies between its members,
# so each level can be executed in parallel.
def parallel_batches(graph):
    in_degree = {v: 0 for v in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] += 1

    ready = [v for v, d in in_degree.items() if d == 0]
    batches = []
    while ready:
        batches.append(ready)                # this whole batch can run concurrently
        nxt = []
        for u in ready:
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    nxt.append(v)
        ready = nxt
    return batches
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Everything at the same "level" has no dependencies between its members,
// so each level can be executed in parallel.
std::vector<std::vector<int>> parallel_batches(const Graph& graph) {
    std::unordered_map<int, int> in_degree;
    for (const auto& [u, outs] : graph) {
        in_degree.try_emplace(u, 0);
        for (int v : outs) ++in_degree[v];
    }

    std::vector<int> ready;
    for (const auto& [v, d] : in_degree)
        if (d == 0) ready.push_back(v);

    std::vector<std::vector<int>> batches;
    while (!ready.empty()) {
        batches.push_back(ready);           // this whole batch can run concurrently
        std::vector<int> next;
        for (int u : ready)
            for (int v : graph.at(u))
                if (--in_degree[v] == 0) next.push_back(v);
        ready = std::move(next);
    }
    return batches;
}
```

</TabItem>
</Tabs>

This is what `make -j` and modern build systems do: compute the dependency levels, then run each
level's tasks in parallel. The number of batches is the graph's **critical path length**, and it is a
hard floor on build time no matter how many cores you add — the same argument as
[Amdahl's law](../../cpu-architecture/multicore-and-parallelism.md).

| Domain | Vertices | Edge means |
|---|---|---|
| Build systems (`make`, Bazel) | Targets | "must be built before" |
| Package managers (`apt`, `pip`, `cargo`) | Packages | "depends on" |
| Spreadsheets | Cells | "is referenced by" |
| Course planning | Courses | "is a prerequisite for" |
| Task runners, CI pipelines | Jobs | "must complete before" |
| Compilers | Instructions | Data dependency — used for scheduling |

## Edge Cases & Pitfalls

- **Edge direction is the most common bug.** Decide whether your map means "depends on" or "is
  depended on by" — reversing it produces a perfectly plausible, exactly backwards order.
- **Isolated vertices belong in the output.** A package with no dependencies still needs installing;
  make sure it is initialised in `in_degree`.
- **Vertices appearing only as targets** may be missing from `graph`'s keys, causing a `KeyError`.
  Build the vertex set from both endpoints of every edge.
- **The result is not unique.** Tests asserting one specific order will break when the iteration
  order changes. Assert the *constraints* — that each vertex precedes its dependents — or use a heap
  for a deterministic order.
- **DFS recursion depth** is O(V); use Kahn's for large graphs.

## References

- Kahn, A.B. (1962), "Topological sorting of large networks", *Communications of the ACM* — the original.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §22.4 — the DFS-based version, with the proof that reverse finishing order is a valid ordering.

### Books & Videos

- [VisuAlgo — Topological Sort](https://visualgo.net/en/dfsbfs) — both algorithms, on a graph you can edit.

## Related Pages

- [Traversal: BFS & DFS](./traversal.md) — both algorithms are traversals with extra bookkeeping.
- [Graphs](../data-structures/graphs.md) — DAGs and why acyclicity matters.
- [Multicore & Parallelism](../../cpu-architecture/multicore-and-parallelism.md) — the critical-path limit on parallel builds.
