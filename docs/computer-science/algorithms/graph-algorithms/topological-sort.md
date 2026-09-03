---
id: topological-sort
title: Topological Sort
sidebar_label: Topological Sort
sidebar_position: 3
tags: [computer-science, algorithms, graphs, dag, topological-sort]
---

# Topological Sort

A topological sort orders the vertices of a **directed acyclic graph** so every edge points forward —
if A must happen before B, A appears earlier. It is the algorithm behind build systems, package
managers, task schedulers and spreadsheet recalculation, all facing the same question: *given these
dependencies, what order can I do the work in?*

<Figure src="/img/cs/algorithms/topological-order.png"
        alt="A directed acyclic graph drawn so that every arrow points from left to right, with no arrow doubling back"
        caption="The same DAG laid out in topological order. Every arrow points forward — that layout existing at all is exactly what acyclicity guarantees."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Topological_Ordering.svg"
        license="CC0" />

## Core Concepts

| Term | Meaning |
|---|---|
| **DAG** | Directed acyclic graph — the precondition; a cycle makes ordering impossible |
| **In-degree** | Number of incoming edges; in-degree 0 means no unmet prerequisites |
| **Valid orderings** | Usually many — the algorithms find *a* valid order, not *the* order |

:::info[A cycle is not a failure mode — it is the answer]
If the graph has a cycle, no valid ordering exists, and both algorithms below detect it — often the
more useful output: "circular dependency between A, B and C" is exactly what a build tool needs to report.
:::

The [shared directed graph](./intro.md#the-shared-example-graphs) is not a DAG — `C->A` and `F->D`
each close a cycle, matching the two [SCCs](./strongly-connected-components.md) `{A,B,C}`/`{D,E,F}`.
The traces below remove both edges: `A->B, B->C, B->D, D->E, E->F`, which is acyclic.

## Mechanism

### Kahn's algorithm (BFS-based)

Repeatedly output a vertex with no remaining prerequisites, then remove its edges:

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
#include <algorithm>
#include <deque>
#include <stdexcept>
#include <unordered_map>
#include <vector>

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

The final length check is the cycle detection: vertices inside a cycle always have an unsatisfied prerequisite, so they never enter the queue.

#### Worked trace: Kahn's on the DAG

In-degrees start at `A`=0, `B`=1, `C`=1, `D`=1, `E`=1, `F`=1 — only `A` has no prerequisites.

```text
step   pop   order so far      in-degree[A,B,C,D,E,F]   queue after      note
1      A     [A]               0, 0, 1, 1, 1, 1          [B]              A->B: B's in-degree 1->0
2      B     [A,B]             0, 0, 0, 0, 1, 1          [C,D]            B->C, B->D both hit 0
3      C     [A,B,C]           0, 0, 0, 0, 1, 1          [D]              C has no outgoing edges
4      D     [A,B,C,D]         0, 0, 0, 0, 0, 1          [E]              D->E: E's in-degree 1->0
5      E     [A,B,C,D,E]       0, 0, 0, 0, 0, 0          [F]              E->F: F's in-degree 1->0
6      F     [A,B,C,D,E,F]     0, 0, 0, 0, 0, 0          []               done, 6 == |V|
```

Output length 6 equals the vertex count, so `A, B, C, D, E, F` is confirmed valid.

**Without removing the back edges** (`C->A`, `F->D` present), every vertex starts with an
unsatisfied prerequisite — in-degrees `A`=1, `B`=1, `C`=1, `D`=2, `E`=1, `F`=1 — so the initial queue
is **empty** and the algorithm halts immediately with zero output: `0 != 6` reports the cycle.

### DFS-based

Run [DFS](./traversal.md) and prepend each vertex as it *finishes* — after everything it depends on
has — so the reversed finishing order is a topological order:

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

#### Worked trace: DFS post-order on the same DAG

Visiting unvisited vertices and each one's neighbours in edge-list order (`B`'s neighbours: `C`, `D`):

```text
visit(A): grey. visit(B): grey. visit(C): grey, no neighbours, black, post-order [C].
          visit(D): grey. visit(E): grey. visit(F): grey, no neighbours, black, post-order [C,F].
          E: black, post-order [C,F,E]. D: black, post-order [C,F,E,D].
B: black, post-order [C,F,E,D,B]. A: black, post-order [C,F,E,D,B,A].
```

Post-order: `C, F, E, D, B, A`. Reversed: `A, B, D, E, F, C` — different from Kahn's
`A, B, C, D, E, F`, and both correct: `C`'s only constraint is coming after `B`.

| | Kahn's | DFS-based |
|---|---|---|
| Traversal, recursion | Breadth-first, none | Depth-first, O(V) stack |
| Cycle detection | Output shorter than vertex count | A GREY vertex revisited |
| Ordering control | Swap the queue for a [heap](../data-structures/heaps.md) for a deterministic order | Fixed by the traversal |

Kahn's is usually preferable — iterative, single-comparison cycle detection, and it extends
naturally to the parallel case below.

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Everything at the same "level" has no dependencies between its members, so it runs in parallel.
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

# the shared directed graph with both back edges removed (the DAG traced above)
dag = {"A": ["B"], "B": ["C", "D"], "C": [], "D": ["E"], "E": ["F"], "F": []}
assert topological_sort(dag) == ["A", "B", "C", "D", "E", "F"]      # Kahn's, matches the trace
assert topological_sort_dfs(dag) == ["A", "B", "D", "E", "F", "C"]  # DFS post-order, matches the trace

cyclic = {"A": ["B"], "B": ["C", "D"], "C": ["A"], "D": ["E"], "E": ["F"], "F": ["D"]}
try:
    topological_sort(cyclic)
    assert False, "should have raised on the cycle"
except ValueError:
    pass
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Everything at the same "level" has no dependencies between its members, so it runs in parallel.
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

This is what `make -j` does: compute the dependency levels, then run each level's tasks in parallel.
The batch count is the graph's **critical path length** — a hard floor on build time no matter how
many cores you add, the same argument as [Amdahl's law](../../cpu-architecture/multicore-and-parallelism.md).

| Domain | Vertices | Edge means |
|---|---|---|
| Build systems (`make`, Bazel), CI pipelines | Targets, jobs | "must be built/complete before" |
| Package managers (`apt`, `pip`, `cargo`) | Packages | "depends on" |
| Spreadsheets, compilers | Cells, instructions | "is referenced by" / data dependency |
| Course planning | Courses | "is a prerequisite for" |

## Edge Cases & Pitfalls

- **Edge direction is the most common bug** — getting "depends on" versus "is depended on by" wrong
  produces a perfectly plausible, exactly backwards order.
- **Isolated vertices belong in the output** — initialise them in `in_degree` even with no edges.
- **Vertices appearing only as targets** may be missing from `graph`'s keys (`KeyError`); build the
  vertex set from both endpoints of every edge.
- **The result is not unique** — assert the *constraints*, not one specific order, or use a heap for
  a deterministic tiebreak. DFS recursion depth is O(V); use Kahn's for large graphs.

## Recall

<Recall
  invariant="A vertex can be output only once every predecessor already has been — Kahn's enforces this via in-degree reaching 0, DFS-based via reversing the finish order, so a vertex finishes only after everything it depends on already has."
  costs={[
    ["Kahn's, adjacency list (worst)", "O(V + E)"],
    ["DFS-based (worst)", "O(V + E)"],
    ["DFS recursion depth (worst)", "O(V)"],
    ["parallel batches, critical path", "O(V + E)"],
  ]}
  reachFor="Any dependency graph that must become a linear order — build systems, package installs, spreadsheet recalculation, course prerequisites."
  trap="Reversing the meaning of an edge ('depends on' versus 'is depended on by') produces a plausible, exactly backwards order with no error raised."
/>

## References

- Kahn, A.B. (1962), "Topological sorting of large networks", *Communications of the ACM* — the original.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §22.4 — DFS-based topological sort, with the proof that reverse finishing order is valid.
- [VisuAlgo — Topological Sort](https://visualgo.net/en/dfsbfs) — both algorithms, on an editable graph.

## Related Pages

- [Graph Algorithms — Overview](./intro.md) — the shared directed graph this page's traces run on.
- [Traversal: BFS & DFS](./traversal.md) — both algorithms are traversals with extra bookkeeping.
- [Cycle Detection](./cycle-detection.md) — the three-colour DFS behind the DFS-based cycle case.
- [Strongly Connected Components](./strongly-connected-components.md) — the two SCCs the shared graph's back edges create.
- [Multicore & Parallelism](../../cpu-architecture/multicore-and-parallelism.md) — the critical-path limit on parallel builds.
