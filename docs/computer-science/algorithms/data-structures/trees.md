---
id: trees
title: Trees & Binary Search Trees
sidebar_label: Trees & BSTs
sidebar_position: 5
tags: [computer-science, algorithms, data-structures, tree, bst]
---

# Trees & Binary Search Trees


A tree is a set of nodes where each node has one parent (except the root) and no cycles. That single
constraint is what makes trees useful: it guarantees exactly one path between any two nodes, so
"where is X" and "how do I get to X" have unique answers.

A **binary search tree** adds an ordering invariant on top, and that invariant is what turns a tree
into a searchable structure.

## Core Concepts

| Term | Meaning |
|---|---|
| **Root** | The single node with no parent |
| **Leaf** | A node with no children |
| **Height** | Longest root-to-leaf path, in edges. Determines every operation's cost |
| **Depth** | Distance from the root to a given node |
| **Binary tree** | Each node has at most two children |
| **Complete** | Every level full except possibly the last, filled left to right |
| **Balanced** | Height stays $O(\log n)$ as nodes are added — see [Balanced Trees](./balanced-trees.md) |

## Architecture / Mechanism

### The BST invariant

For every node: **everything in the left subtree is smaller, everything in the right subtree is
larger.**

<Figure src="/img/cs/algorithms/binary-search-tree.png"
        alt="A binary search tree rooted at 8, with 3 and 10 as its children; 3 has children 1 and 6; 6 has children 4 and 7; 10 has right child 14, which has left child 13"
        caption="Every value left of 8 is below it, every value right of it is above — and the same holds recursively at 3, at 6, and at every other node."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Binary_search_tree.svg"
        license="Public domain" />

That invariant makes search a sequence of one-way decisions. Looking for 7: at 8 go left, at 3 go
right, at 6 go right, found — three comparisons instead of nine.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def search(node, key):
    while node:
        if key == node.value:
            return node
        node = node.left if key < node.value else node.right
    return None

def insert(node, key):
    if node is None:
        return Node(key)
    if key < node.value:
        node.left = insert(node.left, key)
    elif key > node.value:
        node.right = insert(node.right, key)
    return node          # equal keys ignored; a real implementation decides a policy
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
struct Node {
    int value;
    Node* left = nullptr;
    Node* right = nullptr;
};

Node* search(Node* node, int key) {
    while (node) {
        if (key == node->value) return node;
        node = key < node->value ? node->left : node->right;
    }
    return nullptr;
}

Node* insert(Node* node, int key) {
    if (!node) return new Node{key};
    if (key < node->value)      node->left  = insert(node->left, key);
    else if (key > node->value) node->right = insert(node->right, key);
    return node;        // equal keys ignored; a real implementation decides a policy
}
```

</TabItem>
</Tabs>

Both are $O(\text{height})$. The entire question is therefore what the height is.

### Deletion, and the one case that is awkward

Removing a node with zero or one child is a splice. Removing a node with **two** children cannot be —
neither child can take its place without violating the invariant. The fix is to replace the value with
its **in-order successor** (the smallest value in the right subtree), then delete that successor,
which by construction has at most one child:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def delete(node, key):
    if node is None:
        return None
    if key < node.value:
        node.left = delete(node.left, key)
    elif key > node.value:
        node.right = delete(node.right, key)
    else:
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left
        succ = node.right                    # smallest value greater than node
        while succ.left:
            succ = succ.left
        node.value = succ.value
        node.right = delete(node.right, succ.value)
    return node
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
Node* remove(Node* node, int key) {          // named remove — delete is a keyword
    if (!node) return nullptr;
    if (key < node->value) {
        node->left = remove(node->left, key);
    } else if (key > node->value) {
        node->right = remove(node->right, key);
    } else {
        if (!node->left)  { Node* r = node->right; delete node; return r; }
        if (!node->right) { Node* l = node->left;  delete node; return l; }
        Node* succ = node->right;                // smallest value greater than node
        while (succ->left) succ = succ->left;
        node->value = succ->value;
        node->right = remove(node->right, succ->value);
    }
    return node;
}
```

</TabItem>
</Tabs>

### Traversals

| Order | Visits | Produces | Used for |
|---|---|---|---|
| **In-order** | left, node, right | **Sorted sequence** — for a BST | Iterating in key order |
| **Pre-order** | node, left, right | Root first | Copying/serialising a tree |
| **Post-order** | left, right, node | Children before parents | Freeing memory, evaluating expressions |
| **Level-order** | Breadth-first by depth | Row by row | Printing, shortest path in an unweighted tree |

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def in_order(node):
    if node:
        yield from in_order(node.left)
        yield node.value                  # sorted output for a BST
        yield from in_order(node.right)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
void in_order(Node* node, std::vector<int>& out) {
    if (!node) return;
    in_order(node->left, out);
    out.push_back(node->value);          // sorted output for a BST
    in_order(node->right, out);
}
```

</TabItem>
</Tabs>

In-order traversal of a BST yielding sorted output is not a coincidence — it is the invariant
restated. It also gives a neat correctness check: if an in-order walk is not sorted, the tree is not
a valid BST.

## Edge Cases & Pitfalls

:::danger[An unbalanced BST is a linked list wearing a costume]
Insert 1, 2, 3, 4, 5 into a plain BST in that order and every node becomes the right child of the
previous one. Height is n, and every operation is $O(n)$ — with worse constants than an actual
[linked list](./linked-lists.md), because each node also carries an unused pointer.

Sorted or nearly-sorted insertion order is not an unusual case; it is one of the most common ways
real data arrives. This is the entire reason [balanced trees](./balanced-trees.md) exist, and why you
should almost never use a hand-rolled plain BST in production code.
:::

- **Recursive traversal is $O(height)$ in stack space.** On a degenerate tree that is $O(n)$ frames and a
  possible stack overflow. Use an explicit stack for untrusted input.
- **Duplicate keys need an explicit policy** — reject, count, or keep a list per node. Silently
  dropping them (as the `insert` above does) is a decision, so make it deliberately.
- **`validate_bst` by checking each node against its children is wrong.** The invariant is about
  entire subtrees, not immediate children; the correct check passes a `(min, max)` range down.

## Comparisons

| | BST (unbalanced) | [Balanced BST](./balanced-trees.md) | [Hash table](./hash-tables.md) |
|---|---|---|---|
| Search / insert / delete | $O(\log n)$ avg, $O(n)$ worst | $O(\log n)$ guaranteed | $O(1)$ expected |
| Sorted iteration | Yes | Yes | No |
| Range queries, min/max | Yes | Yes | No |
| Worst case | Degenerate | Bounded | $O(n)$ |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 12 — binary search trees, including the expected-height analysis for random insertion order.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §3.2 — BSTs with a full implementation and empirical measurements.

### Books & Videos

- [VisuAlgo — Binary Search Tree](https://visualgo.net/en/bst) — step through insertion, deletion and the successor case interactively.

## Related Pages

- [Balanced Trees](./balanced-trees.md) — how AVL, red-black and B-trees keep the height logarithmic.
- [Heaps & Priority Queues](./heaps.md) — a different tree invariant, for a different question.
- [Indexing & Storage Engines](../../databases/indexing-and-storage-engines.md) — B-trees in the setting that motivated them.
