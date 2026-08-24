---
id: traversal
title: "Traversal: BFS & DFS"
sidebar_label: "Traversal: BFS & DFS"
sidebar_position: 1
tags: [computer-science, algorithms, graphs, bfs, dfs]
---

# Traversal: BFS & DFS


Breadth-first and depth-first search both visit every vertex reachable from a start point, in
O(V + E), using the same loop. They differ in one line — whether the frontier is a queue or a stack —
and that single difference determines the order, the memory profile, and which problems each can
solve.

## Core Concepts

| | Breadth-first (BFS) | Depth-first (DFS) |
|---|---|---|
| Frontier | **Queue** (FIFO) | **Stack** (LIFO), or recursion |
| Explores | All vertices at distance k before k+1 | One branch fully, then backtracks |
| Memory | O(width of the graph) | O(depth of the graph) |
| Finds shortest paths | **Yes** (unweighted) | No |
| Natural for | Distance, levels, nearest match | Cycles, ordering, connectivity, backtracking |

<Figure src="/img/cs/algorithms/bfs-order.png"
        alt="A tree with twelve nodes numbered in breadth-first order: the root is 1, its three children are 2, 3 and 4, and the numbering continues level by level"
        caption="Breadth-first order. The root is 1, then every node at depth 1, then every node at depth 2 — the numbering sweeps across each level before descending."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Breadth-first-tree.svg"
        license="CC BY 3.0" />

<Figure src="/img/cs/algorithms/dfs-order.png"
        alt="The same twelve-node tree numbered in depth-first order: the root is 1, its first child 2, that child's first child 3, and the numbering descends as far as possible before backtracking"
        caption="Depth-first order on the same tree. The numbering dives to a leaf before returning to explore the root's remaining children."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Depth-first-tree.svg"
        license="CC BY-SA 3.0" />

## Architecture / Mechanism

```python showLineNumbers
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()          # FIFO — the oldest frontier vertex
        yield node
        for nb in graph[node]:
            if nb not in visited:
                visited.add(nb)         # mark on ENQUEUE, not on dequeue
                queue.append(nb)

def dfs(graph, start):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()              # LIFO — the newest frontier vertex
        if node in visited:
            continue
        visited.add(node)
        yield node
        for nb in reversed(graph[node]):
            if nb not in visited:
                stack.append(nb)

def dfs_recursive(graph, node, visited=None):
    visited = visited if visited is not None else set()
    visited.add(node)
    yield node
    for nb in graph[node]:
        if nb not in visited:
            yield from dfs_recursive(graph, nb, visited)
```

:::danger[Mark vertices visited when you enqueue, not when you dequeue]
In BFS, marking on dequeue lets a vertex enter the queue several times before it is first processed —
once per neighbour that reaches it. On a dense graph the queue can grow to O(E), and the shortest-path
distances computed from it may be wrong.

DFS is the opposite: because a vertex can legitimately be pushed several times before being popped,
the iterative version must check `visited` again *after* popping, as above. The two algorithms have
genuinely different bookkeeping, and copying one's structure to the other is a common bug.
:::

### BFS computes shortest paths; DFS does not

BFS processes vertices in non-decreasing distance from the start, so the first time it reaches a
vertex is necessarily by a path with the fewest edges. Recording distance and predecessor as you go
gives the path itself:

```python showLineNumbers
def shortest_path(graph, start, goal):
    prev = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == goal:
            path = []
            while node is not None:
                path.append(node)
                node = prev[node]
            return path[::-1]
        for nb in graph[node]:
            if nb not in prev:
                prev[nb] = node
                queue.append(nb)
    return None                         # goal unreachable
```

DFS can reach the goal by an arbitrarily long detour, because it commits to a branch before
considering alternatives. It answers "is there a path", never "what is the shortest path".

## Practical Usage

| Problem | Use | Why |
|---|---|---|
| Fewest moves in a puzzle, degrees of separation | BFS | Shortest path in edges |
| Web crawling by link depth | BFS | Naturally bounded by level |
| Cycle detection | DFS | A back edge to a vertex still on the stack is a cycle |
| [Topological sort](./topological-sort.md) | DFS | Post-order reversed gives the ordering |
| Connected components | Either | Loop over vertices, traverse from each unvisited one |
| Maze solving, N-queens, sudoku | DFS | Backtracking is depth-first by nature |
| Flood fill | Either | DFS is shorter; BFS avoids deep recursion |
| Bipartiteness check | BFS | Two-colour by level |

```python showLineNumbers
# Connected components — the pattern for any "do it for the whole graph" question
def components(graph):
    seen, groups = set(), []
    for v in graph:                     # every vertex, not just one start point
        if v not in seen:
            group = list(bfs(graph, v))
            seen.update(group)
            groups.append(group)
    return groups
```

### Cycle detection needs three states, not two

For a directed graph, "visited" is insufficient — you must distinguish a vertex still being explored
from one already finished:

```python showLineNumbers
WHITE, GREY, BLACK = 0, 1, 2            # unvisited, on the stack, finished

def has_cycle(graph):
    colour = {v: WHITE for v in graph}

    def visit(v):
        colour[v] = GREY
        for nb in graph[v]:
            if colour[nb] == GREY:      # back edge to an ancestor → cycle
                return True
            if colour[nb] == WHITE and visit(nb):
                return True
        colour[v] = BLACK               # fully explored
        return False

    return any(colour[v] == WHITE and visit(v) for v in graph)
```

Reaching a **BLACK** vertex is fine — it means the graph reconverges, not that it loops. Only a
**GREY** vertex, still on the current path, indicates a cycle. Treating both as "visited" reports
cycles in perfectly acyclic diamond-shaped graphs.

## Edge Cases & Pitfalls

- **Forgetting `visited` entirely** loops forever on any cyclic graph. This is the difference between
  graph traversal and tree traversal — trees cannot loop, graphs can.
- **Recursive DFS overflows the stack** on deep graphs; Python's default limit is around 1000 frames.
  Use the iterative form for untrusted or large input.
- **DFS visit order depends on neighbour order.** Iterative DFS with `stack.pop()` visits the *last*
  neighbour first, which is why the code above reverses the list to match the recursive version.
- **Disconnected graphs** need the outer loop shown in `components`; a single traversal reaches one
  component only.
- **BFS memory is the graph's width**, which on a broad graph can exceed DFS's depth substantially —
  the opposite of the usual assumption.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §22.2–22.3 — BFS and DFS with the white/grey/black colouring and the classification of edges.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §4.1 — undirected graphs, with both traversals implemented and applied.

### Books & Videos

- [VisuAlgo — Graph Traversal](https://visualgo.net/en/dfsbfs) — run both on the same graph and watch the frontier evolve.

## Related Pages

- [Shortest Paths](./shortest-paths.md) — what BFS becomes once edges have weights.
- [Topological Sort](./topological-sort.md) — DFS post-order put to work.
- [Stacks & Queues](../data-structures/stacks-and-queues.md) — the one-line difference between the two.
