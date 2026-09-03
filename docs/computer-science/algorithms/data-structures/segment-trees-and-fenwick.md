---
id: segment-trees-and-fenwick
title: Segment Trees & Fenwick Trees
sidebar_label: Segment Trees & Fenwick
sidebar_position: 11
tags: [computer-science, algorithms, data-structures, segment-tree, fenwick-tree, binary-indexed-tree]
---

# Segment Trees & Fenwick Trees

[Prefix sums](../problem-solving-patterns/prefix-sums-and-difference-arrays.md) answer range-sum
queries in $O(1)$, but only for a static array — changing one element means rebuilding every prefix
sum after it, an $O(n)$ update. The problem these two structures solve is "range query *and* point
update, both fast" — a combination a plain array or a prefix-sum table cannot give at the same time.

Both get there the same way: precompute partial answers over ranges, arranged so that any query range
decomposes into a small number of precomputed pieces, and any update touches only the pieces that
cover the changed index. A **segment tree** makes this explicit as a binary tree — each node owns a
contiguous range, the root owns the whole array, and every internal node's range is the union of its
two children's. A **Fenwick tree** (binary indexed tree, BIT) gets the same $O(\log n)$ bounds with a
single flat array and no explicit tree at all, at the cost of being far less general — it handles
prefix-sum-like queries only, where a segment tree handles any associative, invertible-or-not
combining operation (sum, min, max, gcd).

Neither structure earns its complexity for a problem that never updates: use prefix sums instead and
call it $O(1)$ per query. These are for a *sequence* of interleaved range queries and point updates on
the same array.

:::info[Prerequisites]
Comfortable with [prefix sums](../problem-solving-patterns/prefix-sums-and-difference-arrays.md) as
the static-array baseline these structures generalise, and with
[trees](./trees.md) as a recursive parent/child structure.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Segment / range** | The contiguous slice `[lo, hi]` a tree node is responsible for |
| **Range query** | Combine the array's values over `[l, r]` using the tree's operation (sum, min, ...) |
| **Point update** | Change one array element and fix every node whose range contains it |
| **Lazy propagation** | Defer a pending range update at a node until a query actually descends into it |
| **`i & -i`** (lowbit) | Isolates the lowest set bit of `i` — the size of the range Fenwick index `i` owns |
| **1-indexing (Fenwick)** | Fenwick trees index from 1; `i & -i` on index 0 is 0 and breaks the traversal |

## Mechanism

Both structures traced over the same array, `a = [3, 1, 4, 1, 5, 9, 2, 6]` (indices 0–7), with the
operations `sum(2, 5)`, then `update(3, 10)` (index 3's value 1 becomes 10), then re-query `sum(2, 5)`.

### Segment tree: the recursive split

<Figure src="/img/cs/algorithms/segment-tree.png"
        alt="A binary tree over seven elementary intervals P1 through P7, red circles for internal nodes and blue squares for leaves, with intervals S1 through S6 annotated at the highest nodes whose combined range fully covers each interval"
        caption="The classical (interval-stabbing) segment tree: each interval S1–S6 is stored at the small number of canonical nodes that exactly cover it, so a query touches O(log n) nodes regardless of how many intervals overlap there. The array-range-sum segment tree traced below is the same recursive-split idea specialised to array positions instead of arbitrary intervals."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Segment_tree.svg"
        license="CC BY-SA 4.0" />

A sum segment tree stores `node[v] = sum(lo(v), hi(v))`. Building recurses: a leaf's sum is its one
element; an internal node's sum is its children's sum added together — the same "combine two halves"
shape as mergesort, but the *tree itself* persists instead of being thrown away after one pass.

```text
build over [3, 1, 4, 1, 5, 9, 2, 6]:

                         [0,7]=31
                 [0,3]=9              [4,7]=22
             [0,1]=4     [2,3]=5   [4,5]=14   [6,7]=8
            [0]=3 [1]=1 [2]=4 [3]=1 [4]=5 [5]=9 [6]=2 [7]=6

sum(2, 5): decomposes into [2,3]=5 and [4,5]=14 — two nodes, no leaf touched individually
         → 5 + 14 = 19

update(3, 10): a[3] changes 1 → 10. Every ancestor of leaf [3] is refreshed bottom-up:
  [2,3]: 4+1=5  → 4+10=14
  [0,3]: 4+5=9  → 4+14=18
  [0,7]: 9+22=31 → 18+22=40
  ([4,7] and everything under it is untouched — [3] is not in its range)

sum(2, 5) again: [2,3]=14 and [4,5]=14 → 28  (was 19, +9 matches the value change 10−1)
```

`sum(2, 5)` touches exactly the two nodes whose ranges tile `[2, 5]` with no overlap and no gaps — that
tiling into $O(\log n)$ pieces, never more, is the structural guarantee a segment tree gives for *any*
query range (CLRS 4th ed., §14.3 covers the closely related interval trees; the range-decomposition
argument here follows the standard competitive-programming construction, e.g. Halim & Halim,
*Competitive Programming*, 4th ed., §2.5).

### Fenwick tree: index arithmetic instead of pointers

A Fenwick tree stores the same information with no explicit tree and no pointers — one flat array,
1-indexed, where `tree[i]` covers the range `(i - lowbit(i), i]`. `lowbit(i) = i & -i` isolates the
lowest set bit: in two's-complement, `-i` is `~i + 1`, so every bit of `i` below its lowest set bit is
flipped from 0 to 1 in `~i` and then carried back to 0 by the `+1`, while the lowest set bit itself and
everything above it survive the flip — `i & -i` keeps exactly that one bit. For `i = 12 = 0b1100`,
`-12 = 0b...110100`, and `12 & -12 = 0b0100 = 4`.

<Figure src="/img/cs/algorithms/fenwick-tree.png"
        alt="A Fenwick tree over 8 elements: eight range bars stacked by length, tree[1] through tree[7] covering short ranges at the bottom and tree[8] covering the whole array at top, with an arrow tracing update(3) climbing from tree[3] to tree[4] to tree[8]"
        caption="Index i owns the range (i − lowbit(i), i]. update(3) climbs by repeatedly adding lowbit: 3 → 4 → 8, touching exactly the ancestors whose range contains index 3." />

```text
update(index 3, +9):  # 1-indexed Fenwick position 4 = array index 3, delta = 10 - 1 = +9
  i=4:  4 & -4 = 4  → tree[4] += 9,  i becomes 4+4=8
  i=8:  8 & -8 = 8  → tree[8] += 9,  i becomes 8+8=16, stop (>8)
  (tree[1..3], tree[5..7] untouched — none of their ranges contain position 4)

query(prefix sum up to position 5, i.e. array index 4):
  i=5:  5 & -5 = 1  → add tree[5], i becomes 5-1=4
  i=4:  4 & -4 = 4  → add tree[4], i becomes 4-4=0, stop
  prefix(5) = tree[5] + tree[4]

sum(2, 5) [array indices] = prefix(6) - prefix(2), each computed by the same climb-down-by-lowbit loop
```

Update climbs *up* by repeatedly adding `lowbit(i)`; a prefix query climbs *down* by repeatedly
subtracting it. Both loops run at most $O(\log n)$ times because each step clears at least one more
bit of `i` (Fenwick's original note: P. M. Fenwick, "A New Data Structure for Cumulative Frequency
Tables," *Software: Practice and Experience* 24(3), 1994).

### Lazy propagation

A segment tree's point update touches $O(\log n)$ nodes because only one leaf changes. A **range**
update — "add 5 to every element in `[2, 6]`" — naively touches every leaf in that range, $O(n)$ in the
worst case. **Lazy propagation** fixes this by stamping the update on the $O(\log n)$ nodes that
exactly tile `[2, 6]` and recording a *pending* delta on each, instead of pushing it down to every
leaf immediately. A later query that needs to descend past a node with a pending delta pushes it one
level down first — so the cost is paid only by queries that actually need to see inside that
subtree, not upfront. This section names lazy propagation and states what it buys — $O(\log n)$ range
updates as well as range queries — without deriving the push-down bookkeeping in full; see the
references for the complete construction.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
class SegmentTree:
    """Sum segment tree, 0-indexed, no lazy propagation (point updates only)."""

    def __init__(self, data):
        self.n = len(data)
        self.tree = [0] * (2 * self.n)
        self.tree[self.n:] = data
        for i in range(self.n - 1, 0, -1):        # build bottom-up: O(n)
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def update(self, i, value):
        i += self.n
        self.tree[i] = value
        while i > 1:                               # O(log n): one hop per level
            i //= 2
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def query(self, left, right):                  # sum over [left, right), half-open
        result, left, right = 0, left + self.n, right + self.n
        while left < right:                         # O(log n)
            if left & 1:
                result += self.tree[left]
                left += 1
            if right & 1:
                right -= 1
                result += self.tree[right]
            left //= 2
            right //= 2
        return result


class Fenwick:
    """1-indexed binary indexed tree over n elements, all zero initially."""

    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, i, delta):                        # i is 1-indexed
        while i <= self.n:                           # O(log n)
            self.tree[i] += delta
            i += i & (-i)

    def prefix_sum(self, i):                         # sum of positions 1..i
        total = 0
        while i > 0:                                 # O(log n)
            total += self.tree[i]
            i -= i & (-i)
        return total

    def range_sum(self, left, right):                # 1-indexed, inclusive
        return self.prefix_sum(right) - self.prefix_sum(left - 1)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <vector>

class SegmentTree {                                  // iterative, 0-indexed, sum, point update
public:
    explicit SegmentTree(const std::vector<int>& data) : n_(data.size()), tree_(2 * n_) {
        for (int i = 0; i < n_; ++i) tree_[n_ + i] = data[i];
        for (int i = n_ - 1; i > 0; --i) tree_[i] = tree_[2 * i] + tree_[2 * i + 1];
    }
    void update(int i, int value) {
        i += n_;
        tree_[i] = value;
        for (i /= 2; i >= 1; i /= 2) tree_[i] = tree_[2 * i] + tree_[2 * i + 1];
    }
    long long query(int left, int right) {            // [left, right)
        long long result = 0;
        for (left += n_, right += n_; left < right; left /= 2, right /= 2) {
            if (left & 1) result += tree_[left++];
            if (right & 1) result += tree_[--right];
        }
        return result;
    }
private:
    int n_;
    std::vector<long long> tree_;
};

class Fenwick {                                       // 1-indexed
public:
    explicit Fenwick(int n) : n_(n), tree_(n + 1, 0) {}
    void add(int i, long long delta) {
        for (; i <= n_; i += i & (-i)) tree_[i] += delta;
    }
    long long prefix_sum(int i) {
        long long total = 0;
        for (; i > 0; i -= i & (-i)) total += tree_[i];
        return total;
    }
    long long range_sum(int left, int right) { return prefix_sum(right) - prefix_sum(left - 1); }
private:
    int n_;
    std::vector<long long> tree_;
};
```

</TabItem>
</Tabs>

## Practical Usage

```python showLineNumbers
a = [3, 1, 4, 1, 5, 9, 2, 6]

seg = SegmentTree(a)
assert seg.query(2, 6) == 19            # sum(2, 5) inclusive == query(2, 6) half-open
seg.update(3, 10)                       # a[3]: 1 -> 10
assert seg.query(2, 6) == 28            # 19 + (10 - 1)

fen = Fenwick(len(a))
for i, v in enumerate(a, start=1):      # Fenwick is 1-indexed
    fen.add(i, v)
assert fen.range_sum(3, 6) == 19        # positions 3..6 == array indices 2..5
fen.add(4, 9)                           # array index 3 (position 4): +9, matching 1 -> 10
assert fen.range_sum(3, 6) == 28
```

- **Neither language ships either structure.** As with union-find, this is code you write, because the combining operation (sum, min, max, xor, gcd) is problem-specific; C++'s `<numeric>` `std::partial_sum` covers only the static prefix-sum case.
- **Order statistics.** A Fenwick tree over a "count of values ≤ x" array answers "how many inserted values are ≤ x" as a prefix sum, and "what is the k-th smallest value" via a binary search over the tree itself.
- **Range-minimum/maximum queries (RMQ).** A segment tree generalises directly by swapping `+` for `min`/`max`; a Fenwick tree cannot do plain RMQ because `min` has no inverse — no subtraction undoes a min the way it undoes a sum.
- **Competitive programming judges** (Codeforces, AtCoder) treat both as standard library knowledge — neither has a canonical open-source implementation worth depending on for a one-off problem.

## Edge Cases & Pitfalls

- **0-indexing a Fenwick tree.** `i & -i` on `i = 0` is `0`, so both the update and query loops either
  never execute or loop forever depending on the loop condition. Fenwick trees are 1-indexed by
  construction; convert array index `k` to Fenwick position `k + 1` at every call site.
- **Off-by-one in half-open vs. inclusive ranges.** The segment tree implementation above takes
  half-open `[left, right)`; the Fenwick wrapper takes inclusive `[left, right]`. Mixing the two
  conventions in one codebase is the single most common bug in either structure — pick one and wrap
  the other to match.
- **Using a Fenwick tree for a non-invertible operation.** `range_sum` works because
  `prefix_sum(r) - prefix_sum(l-1)` undoes the combination. There is no analogous subtraction for
  `min`, `max`, or `gcd` — those need either a segment tree or two Fenwick trees plus extra bookkeeping
  (sparse-table-style tricks), not the plain BIT above.
- **Forgetting to push down lazy state before reading it.** A range-update segment tree that checks a
  node's stored value without first pushing its pending delta to children returns a stale answer for
  any query that needed to descend past that node.
- **Rebuilding from scratch on every update.** Both structures exist specifically so that a *single*
  point change costs $O(\log n)$, not $O(n)$. Recomputing prefix sums after every update — the naive
  fallback — throws away the entire reason to use either structure.

## Comparisons

| | Segment tree | Fenwick tree | Prefix sums |
|---|---|---|---|
| Range query, sum (worst) | $O(\log n)$ | $O(\log n)$ | $O(1)$ |
| Point update (worst) | $O(\log n)$ | $O(\log n)$ | $O(n)$ — rebuild the suffix |
| Range update with lazy propagation (worst) | $O(\log n)$ | Needs a second BIT trick | $O(n)$ |
| Supported operations | Any associative op: sum, min, max, gcd, xor | Only invertible ops: sum, xor | Sum only |
| Memory | $O(n)$, roughly $4n$ node slots as commonly implemented | $O(n)$, exactly one array | $O(n)$ |
| Code size | Larger — explicit tree, optional lazy layer | A dozen lines, no pointers | Trivial |

Reach for a Fenwick tree first when the operation is sum-like and the problem is competitive-style —
less code, same bound. Reach for a segment tree when the operation isn't invertible, or when a query
needs more than a single number back (e.g. "the index of the minimum," not just its value).

## Recall

<Recall
  invariant="A segment tree node's range is the union of its children's; a Fenwick index i owns exactly the range (i − lowbit(i), i]. Either way, any query range decomposes into O(log n) precomputed pieces."
  costs={[
    ["range query, either structure (worst)", "O(log n)"],
    ["point update, either structure (worst)", "O(log n)"],
    ["range update with lazy propagation (worst)", "O(log n), segment tree only"],
    ["build from n elements (worst)", "O(n)"],
    ["static range sum, no updates (worst)", "O(1) with prefix sums — no tree needed"],
  ]}
  reachFor="Range queries interleaved with point (or range) updates on the same array — a segment tree for any associative combiner, a Fenwick tree specifically for sums or other invertible operations."
  trap="Reaching for a Fenwick tree for range-minimum queries — min has no inverse, so prefix(r) − prefix(l−1) does not give a range answer the way it does for sum."
/>

## References

- P. M. Fenwick, "A New Data Structure for Cumulative Frequency Tables," *Software: Practice and
  Experience* 24(3), 1994 — the original binary indexed tree, including the `i & -i` traversal derived
  above.
- Halim, S. & Halim, F., *Competitive Programming*, 4th ed., §2.5 "Segment Tree" and §2.5 "Fenwick
  Tree" — the standard competitive-programming construction this page's implementations follow,
  including the iterative (pointerless) segment tree layout.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §14.3 "Interval trees" —
  the closest CLRS analogue: an augmented balanced tree answering range-overlap queries in
  $O(\log n)$, via the same "decompose into a small number of precomputed pieces" idea.

## Related Pages

- [Prefix Sums & Difference Arrays](../problem-solving-patterns/prefix-sums-and-difference-arrays.md) —
  the $O(1)$-query, $O(n)$-update baseline these structures generalise for interleaved updates.
- [Trees & Binary Search Trees](./trees.md) — the recursive vocabulary a segment tree specialises.
- [Balanced Trees](./balanced-trees.md) — height guarantees for search trees, contrasted with a segment
  tree's height, which is fixed by array size rather than balanced dynamically.
- [Cheat Sheet](./cheat-sheet.md) — the full operation-cost matrix across every structure in this
  folder.
