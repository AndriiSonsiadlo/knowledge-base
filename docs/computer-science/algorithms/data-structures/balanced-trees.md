---
id: balanced-trees
title: Balanced Trees
sidebar_label: Balanced Trees
sidebar_position: 6
tags: [computer-science, algorithms, data-structures, avl, red-black-tree, b-tree, trie]
---

# Balanced Trees


A [binary search tree](./trees.md) is $O(\log n)$ only while it stays short, and nothing in the plain
insertion algorithm keeps it short. A **self-balancing** tree restores a height bound after every
modification, converting the average case into a guarantee.

The mechanism is always the same: detect that the invariant broke, then apply local **rotations** —
constant-time pointer rearrangements that change the shape without changing the in-order sequence.

## Core Concepts

| Structure | Balance invariant | Height bound | Typical use |
|---|---|---|---|
| **AVL tree** | Subtree heights differ by ≤ 1 at every node | ≤ 1.44 log₂ n | Read-heavy workloads |
| **Red-black tree** | No red node has a red child; equal black-depth on all paths | ≤ 2 log₂ n | Language library maps/sets |
| **B-tree / B+ tree** | All leaves at the same depth; nodes hold many keys | log_B n | Databases, filesystems |
| **Trie** | Not a search tree — position encodes the key | Length of the key | Prefix queries, autocomplete |

## Mechanism

### Rotations

A rotation swaps a parent and child while re-parenting one subtree, preserving the BST ordering:

```text
      y                               x
     / \        right rotation       / \
    x   C       ───────────────>    A   y
   / \          <───────────────       / \
  A   B          left rotation        B   C

In-order before:  A x B y C
In-order after:   A x B y C      (identical — only the shape changed)
```

<Figure src="/img/cs/algorithms/avl-rotation.gif"
        alt="Animation of an AVL tree: nodes are inserted, the tree becomes unbalanced, and rotations restore the height difference to at most one"
        caption="An AVL tree rebalancing as values are inserted. Each insertion may trigger one or two rotations, and the tree never gets taller than it must."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:AVL_Tree_Example.gif"
        license="CC BY-SA 4.0" />

### AVL vs. red-black: the same idea, differently tuned

AVL keeps a strict bound (heights differ by at most 1) and so stays shorter, giving faster lookups.
Red-black permits a looser bound and so rebalances less, giving faster insertion and deletion.

<Figure src="/img/cs/algorithms/red-black-tree.png"
        alt="A red-black tree with nodes coloured red and black, black leaf sentinels at the bottom, and every root-to-leaf path passing through the same number of black nodes"
        caption="A red-black tree. The colours are one bit per node, and the two rules they encode are enough to guarantee the longest path is at most twice the shortest."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Red-black_tree_example.svg"
        license="CC BY-SA 3.0" />

| | AVL | Red-black |
|---|---|---|
| Height | ≤ 1.44 log₂ n — shorter | ≤ 2 log₂ n |
| Lookup | Faster | Slightly slower |
| Insert / delete | More rotations | Fewer rotations |
| Rotations per delete | $O(\log n)$ | ≤ 3 |
| Used by | Some in-memory indexes | C++ `map`/`set`, Java `TreeMap`, Linux CFS scheduler, `epoll` |

Red-black won the standard-library slot almost everywhere, because mixed read/write workloads are the
common case and its worst-case deletion cost is a small constant.

### B-trees: balanced for disks, not for RAM

Binary trees ask one question per node. When a node lives on
[storage](../../storage/intro.md) and reading it costs an entire 4–16 KB page, that is a catastrophic
ratio — you fetch 16 KB to learn one bit of information.

A **B-tree** sizes each node to one page and stores hundreds of keys in it, so a single I/O narrows
the search hundreds of ways instead of two:

<Figure src="/img/cs/databases/b-tree.png"
        alt="A B-tree with a root node containing the keys 7 and 16 and three child pointers, leading to leaves containing 1,2,5,6 then 9,12 then 18,21"
        caption="High fan-out is the point. With ~400 keys per node, three levels index 64 million entries — three disk reads for any lookup."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:B-tree.svg"
        license="CC BY-SA 3.0" />

**B+ trees**, the variant databases actually use, additionally keep all values in the leaves and link
the leaves together, making a range scan a sequential walk rather than a repeated root-down descent.

### Tries: keyed by position, not by comparison

A trie stores keys along the *path* rather than in the nodes, so no key comparison happens at all —
lookup cost depends on key length, not on how many keys are stored:

<Figure src="/img/cs/algorithms/trie.png"
        alt="A trie whose edges are labelled with letters, spelling to, tea, ted, ten, A, in and inn along root-to-node paths, with values attached to the nodes that end a word"
        caption="Edges carry the characters; a node's path from the root *is* its key. Every word sharing a prefix shares the nodes for it."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Trie_example.svg"
        license="Public domain" />

This makes prefix operations — autocomplete, longest-prefix IP routing, dictionary matching —
natural, which no comparison tree or [hash table](./hash-tables.md) offers. The cost is memory: a
naive trie allocates a child array per node, which is why practical implementations use compressed
forms (radix trees, and the [Patricia tries](https://en.wikipedia.org/wiki/Radix_tree) inside kernel
routing tables).

## Practical Usage

| Language | Ordered map | Underlying structure |
|---|---|---|
| C++ | `std::map`, `std::set` | Red-black tree |
| Java | `TreeMap`, `TreeSet` | Red-black tree |
| Python | *(none built in)* | Use `sortedcontainers`, or keep a sorted list + `bisect` |
| Rust | `BTreeMap`, `BTreeSet` | B-tree — chosen for cache behaviour, in memory |
| Go | *(none built in)* | Sort a slice, or use a third-party tree |

:::tip[Rust's choice is the interesting one]
`BTreeMap` uses a B-tree in **memory**, not on disk, for exactly the reason B-trees were invented —
just one level down the hierarchy. Here the "page" is a
[cache line](../../memory-hierarchy/cpu-caches.md), and packing many keys into one node means one
cache miss narrows the search many ways instead of two. The same argument, applied to a different
boundary.
:::

## Edge Cases & Pitfalls

- **Do not implement one unless you must.** Red-black deletion has many cases and is genuinely easy
  to get subtly wrong. Every mainstream standard library ships a correct one.
- **A balanced tree is not a hash table.** If you never need ordering, ranges or a worst-case bound,
  a [hash table](./hash-tables.md) is faster and simpler.
- **Tries can use far more memory than expected.** One child pointer per alphabet symbol per node
  adds up quickly; measure before choosing one over a hash table for plain exact-match lookup.
- **"Balanced" bounds height, not shape.** Two trees holding the same keys can differ completely in
  structure depending on insertion order; only the height bound is guaranteed.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 13 (red-black trees) and Ch. 18 (B-trees).
- Adelson-Velsky & Landis (1962) — the original AVL paper, and the first self-balancing BST.
- [Rust `BTreeMap` documentation](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html) — the standard library's rationale for B-trees in memory.

### Books & Videos

- [VisuAlgo — AVL and Red-Black Trees](https://visualgo.net/en/bst) — watch rotations happen step by step.

## Related Pages

- [Trees & Binary Search Trees](./trees.md) — the unbalanced base case and why it degenerates.
- [Hash Tables](./hash-tables.md) — the unordered alternative.
- [Indexing & Storage Engines](../../databases/indexing-and-storage-engines.md) — B+ trees under real query loads.
