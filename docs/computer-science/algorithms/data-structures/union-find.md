---
id: union-find
title: Union-Find (Disjoint Set Union)
sidebar_label: Union-Find
sidebar_position: 9
tags: [computer-science, algorithms, data-structures, union-find, graphs]
---

# Union-Find (Disjoint Set Union)

Some problems never ask *what* is in a group. They ask only whether two things have ended up in the
same one: are these two computers on the same network segment, do these two pixels belong to the same
blob, would adding this edge close a cycle. Union-find is the structure for exactly that question, and
it is fast because it refuses to answer any other.

The representation is a **forest**. Every element points at a parent; an element that points at itself
is a **root**, and the root *is* the name of its set. `find(x)` walks the parent pointers to the root.
Two elements are in the same set precisely when that walk ends in the same place. `union(a, b)` finds
both roots and makes one point at the other — one pointer write, and two sets are one.

The tree's *shape* carries no meaning at all. It is not a hierarchy, nothing was "contained in"
anything, and the child-parent relation records only the accident of which union happened first. That
is what licenses the second optimisation: since the shape means nothing, you are free to flatten it
whenever you like. Every `find` may re-point every node it passes straight at the root, and the
structure is unchanged as far as any caller can tell — only faster. A structure whose shape is
meaningless is a structure you can aggressively destroy in your own favour.

:::info[Prerequisites]
Comfortable with [trees](./trees.md) as a parent-pointer structure, and with
[graphs](./graphs.md) as vertices plus edges.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Parent array** | `parent[x]` is x's parent; `parent[x] == x` means x is a root |
| **Representative (root)** | The single element that names a set. Arbitrary, and it changes as sets merge |
| **`find(x)`** | Walk to the root of x's tree — the set-identity query |
| **`union(a, b)`** | Attach one root under the other. **Roots**, never `a` and `b` themselves |
| **Union by rank** | Attach the shorter tree under the taller. `rank` is an upper bound on height, not the exact height |
| **Union by size** | Attach the smaller tree under the larger. Same asymptotics; `size` is also useful data |
| **Path compression** | During `find`, re-point every node on the walk directly at the root |
| **α(n)** | The inverse Ackermann function — below 5 for any n that fits in the observable universe |

The two optimisations attack different halves of the same problem. Union by rank stops tall trees from
being *built*; path compression flattens the ones that were. Either alone leaves a per-operation cost
of O(log n) — balanced linking in the **worst case**, because a tree of rank k can still have height
k (Sedgewick & Wayne, 4th ed., §1.5, Proposition H proves the lg n depth bound for union by *size*;
union by rank gives the same bound); path compression alone **amortized**, because linking a large
tree under a small root keeps rebuilding depth faster than compression flattens it (Tarjan & van
Leeuwen, 1984). Together they give the amortized α(n) bound proved in CLRS 4th ed. §19.4.

## Mechanism

Two views of the same three unions. The left pair is what the caller believes it has — a partition
into disjoint sets. The right pair is what is actually in memory: a forest, and the compression that
follows a `find`.

<Figure src="/img/cs/algorithms/dsu-disjoint-sets-init.png"
        alt="Eight numbered circles, each alone, representing eight singleton sets"
        caption="The starting partition: every element is its own set, and its own root."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Dsu_disjoint_sets_init.svg"
        license="CC BY-SA 3.0" />

<Figure src="/img/cs/algorithms/dsu-disjoint-sets-final.png"
        alt="The same eight elements enclosed in three rounded outlines: one containing 1 2 5 6 8, one containing 3 4, and one containing 7"
        caption="After some unions: three sets. This is the abstraction — membership, with no order and no shape."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Dsu_disjoint_sets_final.svg"
        license="CC BY-SA 3.0" />

<Figure src="/img/cs/algorithms/dsu-forest.png"
        alt="Two forests over the elements 0 to 5. On the left, 1 and 2 point at root 0 and 3 points at 2; 4 and 5 stand alone. On the right, 1, 2 and 3 all point directly at 0."
        caption="The representation. Roots are shaded; arrows are parent pointers. find(3) walks 3 → 2 → 0 once, then re-points 3 straight at the root so the next walk is a single hop." />

Traced over `0..5`, with the operations `union(0,1) union(2,3) union(1,3) find(0) find(3)`:

```text
union over 0..5, operations: union(0,1) union(2,3) union(1,3) find(0) find(3)

  op            parent array            forest
  start         [0, 1, 2, 3, 4, 5]      six singletons
  union(0,1)    [0, 0, 2, 3, 4, 5]      1's root now 0
  union(2,3)    [0, 0, 2, 2, 4, 5]      3's root now 2
  union(1,3)    [0, 0, 0, 2, 4, 5]      find(1)=0, find(3)=2 → 2's root now 0
  find(0)       [0, 0, 0, 2, 4, 5]      already a root, no change
  find(3)       [0, 0, 0, 0, 4, 5]      path compression: 3 re-parented straight to 0
```

Note that `union(1,3)` writes `parent[2]`, not `parent[3]`. Nothing in the array records that the
caller ever named 1 and 3 — only that their sets merged.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
class DSU:
    """Disjoint set union with union by rank and full path compression."""

    def __init__(self, n):
        self.parent = list(range(n))   # every element is its own root
        self.rank = [0] * n            # upper bound on tree height, not exact
        self.components = n            # O(1) worst case per union

    def find(self, x):
        root = x
        while self.parent[root] != root:   # first pass: locate the root
            root = self.parent[root]
        while self.parent[x] != root:      # second pass: re-point the whole path
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                   # already together — the cycle test
        if self.rank[ra] < self.rank[rb]:  # attach the shorter tree under the taller
            ra, rb = rb, ra
        self.parent[rb] = ra               # a root is written, never `a` or `b`
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1             # height grows only on a tie
        self.components -= 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <numeric>
#include <vector>

struct DSU {                                    // `union` is a keyword: name it `unite`
    std::vector<int> parent, rank_;
    int components;

    explicit DSU(int n) : parent(n), rank_(n, 0), components(n) {
        std::iota(parent.begin(), parent.end(), 0);
    }

    int find(int x) {                           // path halving: one pass, same bound
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];      // point at the grandparent, then step
            x = parent[x];
        }
        return x;
    }

    bool unite(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra == rb) return false;             // already together — the cycle test
        if (rank_[ra] < rank_[rb]) std::swap(ra, rb);
        parent[rb] = ra;                        // a root is written, never `a` or `b`
        if (rank_[ra] == rank_[rb]) ++rank_[ra];
        --components;
        return true;
    }

    bool connected(int a, int b) { return find(a) == find(b); }
};
```

</TabItem>
</Tabs>

Note that `find` is not read-only: it rewrites the parent array. That matters if you ever share a DSU
across threads, and it is why a `const` `find` is not offered above.

## Practical Usage

Neither language ships one. There is no disjoint-set type in the Python standard library and none in
the C++ standard library, so this is a structure you write — which is part of why it is worth knowing
by heart. (Boost provides `boost::disjoint_sets`, and SciPy provides `scipy.cluster.hierarchy.DisjointSet`;
both are third-party dependencies.)

Where it earns its place:

- **Kruskal's minimum spanning tree.** Sort the edges by weight and take each one whose endpoints are
  not already connected. The DSU *is* the cycle test, and it is what makes the algorithm O(E log E) worst
  case rather than a worst-case O(VE) — see CLRS 4th ed. §21.2 and Sedgewick & Wayne §4.3.
- **Connected components.** Union every edge, then `components` is the answer in O(1) worst case. Compare
  with a [traversal](../graph-algorithms/traversal.md), which needs a full O(V + E) worst-case pass per batch.
- **Cycle detection in an undirected graph.** `union(u, v)` returning `False` means the edge closes a
  cycle. This does *not* work for directed graphs — direction is exactly the information the structure
  discards.
- **Dynamic connectivity in a grid.** Flood-fill problems where cells switch on over time: index each
  cell as `row * width + col`, union it with each already-on neighbour. Percolation (Sedgewick & Wayne
  §1.5) is the canonical example.
- **Equivalence classes generally.** Merging duplicate account records, unifying type variables in a
  type checker, grouping equal-valued keys.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def kruskal(n, edges):
    """edges: (weight, u, v). Returns the total weight of a minimum spanning tree."""
    dsu, total = DSU(n), 0
    for weight, u, v in sorted(edges):       # O(E log E) worst case — the sort dominates
        if dsu.union(u, v):                  # False means it would close a cycle
            total += weight
    return total


# A B C D E F as 0..5
GRAPH = [(4, 0, 1), (2, 0, 2), (1, 1, 2), (5, 1, 3), (8, 2, 3),
         (10, 2, 4), (2, 3, 4), (6, 3, 5), (3, 4, 5)]

d = DSU(6)
d.union(0, 1); d.union(2, 3); d.union(1, 3)
assert d.parent == [0, 0, 0, 2, 4, 5]    # exactly the traced array, 3 not yet compressed
assert d.find(1) == d.find(3)            # merged through their roots
assert d.parent[3] == 0                  # that find() re-pointed 3 straight at the root
assert d.find(4) != d.find(0)            # 4 was never touched
assert d.components == 3                 # {0,1,2,3}, {4}, {5}
assert kruskal(6, GRAPH) == 13           # B–C, A–C, D–E, E–F, B–D
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
struct Edge { int weight, u, v; };

long long kruskal(int n, std::vector<Edge> edges) {
    std::sort(edges.begin(), edges.end(),
              [](const Edge& a, const Edge& b) { return a.weight < b.weight; });
    DSU dsu(n);
    long long total = 0;
    for (const Edge& e : edges)
        if (dsu.unite(e.u, e.v)) total += e.weight;   // false → would close a cycle
    return total;
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Uniting the elements instead of the roots.** `parent[b] = a` rather than `parent[find(b)] = find(a)`
  compiles, runs, and is wrong. The symptom is nasty: everything looks fine for a while, then sets
  silently stop merging, because you have re-parented a node that already had a parent and orphaned an
  entire subtree from the merge. Any `union` that does not call `find` twice first is a bug.
- **Recursive `find` blowing the stack.** The one-line recursive version is elegant, but before any
  compression happens a degenerate chain is n deep. CPython's limit on interpreter stack depth is
  settable via [`sys.setrecursionlimit`](https://docs.python.org/3/library/sys.html#sys.setrecursionlimit);
  the docs do not fix a default, and on CPython 3.14 `sys.getrecursionlimit()` returns 1000. A DSU over
  a few thousand elements can therefore raise `RecursionError` on a bad input distribution. Both
  implementations above are iterative for this reason.
- **Deletion is not supported.** Sets merge and never split. Removing an element, or undoing a union,
  requires a different structure (a union-find with rollback, which forgoes path compression so that
  each union writes exactly one array cell that can be replayed backwards). If the problem splits
  groups, this is the wrong structure — consider processing the operations in reverse so that splits
  become merges.
- **`rank` is not height after compression.** Compression shortens trees without decrementing any rank,
  so `rank` drifts above the true height. That is harmless — it is used only as a tie-breaker, and the
  CLRS §19.4 analysis assumes exactly this.
- **Non-integer elements.** The parent array is indexed by integer. Map your keys to `0..n-1` first
  (a dict, or `enumerate`); a dict-of-parents works too but pays hashing on every step of every walk.

## Comparisons

| | Union-find | [BFS/DFS flood fill](../graph-algorithms/traversal.md) | Hash map of set IDs |
|---|---|---|---|
| Model | Incremental — edges arrive over time | Offline — the whole graph must be known | Incremental |
| Merge two groups | O(α(n)) amortized | n/a | O(n) worst — relabel the smaller set |
| "Same group?" query | O(α(n)) amortized | O(V + E) worst, per traversal | O(1) average |
| Enumerate a group's members | O(n) worst — a full scan | O(size) worst | O(size) worst |
| Split a group | Not supported | Recompute, O(V + E) worst | O(size) worst |
| Memory | One or two int arrays | Visited array plus a frontier | One entry per element |

Union-find wins when connectivity queries are interleaved with edge insertions. A traversal wins when
the graph is fixed and you also need to *walk* it — distances, paths, or the members of a component.
The hash-map-of-IDs approach is only competitive with the "small-to-large" merging trick, and even
then it is O(n log n) worst case overall, against union-find's near-linear.

## Recall

<Recall
  invariant="Each set is a tree whose root is the set's name; find(x) returns that root, and two elements are connected exactly when their roots match."
  costs={[
    ["find / union, both optimisations (amortized)", "O(α(n))"],
    ["find / union, union by rank only (worst)", "O(log n)"],
    ["find / union, no optimisation (worst)", "O(n)"],
    ["build over n singletons (worst)", "O(n)"],
    ["count components (worst)", "O(1) with a counter"],
  ]}
  reachFor="The question is 'are these two things in the same group?' and groups only ever merge, never split."
  trap="Union by size or rank without path compression still gives O(log n); path compression without union by rank does too. You need both to get α(n) — and union must join roots, never the two elements directly."
/>

## References

- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.5 "Case Study: Union-Find" — the definitive
  introduction, developing quick-find → quick-union → weighted quick-union with doubling-test
  measurements for each, plus the percolation application.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 19 "Data Structures for
  Disjoint Sets" — the forest representation in §19.3 and the amortized O(m α(n)) proof in §19.4.
- R. E. Tarjan, "Efficiency of a Good But Not Linear Set Union Algorithm", *JACM* 22(2), 1975 — where
  the inverse-Ackermann bound comes from.
- R. E. Tarjan & J. van Leeuwen, "Worst-case Analysis of Set Union Algorithms", *JACM* 31(2), 1984 —
  the case-by-case analysis showing what each optimisation is worth on its own.

## Related Pages

- [Trees](./trees.md) — the parent-pointer representation, used here without any of the ordering.
- [Graphs](./graphs.md) — where the edges being unioned come from.
- [Graph Traversal](../graph-algorithms/traversal.md) — the offline alternative for connectivity.
- [Big-O Notation](../complexity/big-o-notation.md) — what "amortized α(n)" is claiming, and what it is not.
