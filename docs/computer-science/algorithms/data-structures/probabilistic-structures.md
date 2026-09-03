---
id: probabilistic-structures
title: Probabilistic Data Structures
sidebar_label: Probabilistic Structures
sidebar_position: 13
tags: [computer-science, algorithms, data-structures, bloom-filter, count-min-sketch, hyperloglog, skip-list]
---

# Probabilistic Data Structures

Every structure so far in this section answers its question exactly, at the cost of storing enough
information to do so. A [hash set](./hash-tables.md) of a billion strings needs memory proportional to
a billion strings. Probabilistic structures make a different trade: allow a small, quantifiable chance
of a wrong answer, and get memory *sublinear* in the data — often by one or two orders of magnitude —
or a query cost that no exact structure can match.

The trade is never unconditional. Each structure below fixes the *kind* of error it will tolerate
(a false positive here, an approximation error there) and the exact probability or bound is a formula
in terms of the memory given to it — not a vague "usually close enough," but a number computed before
the structure is even built. Knowing which error each one accepts, and refusing the ones it does not,
is the entire skill in choosing one.

A **Bloom filter** answers set membership and can false-positive but never false-negative. A
**count-min sketch** answers frequency counts and can only overestimate. **HyperLogLog** answers
distinct-count and is off by a small percentage in either direction. A **skip list** is the odd one
out — it answers ordered-map queries exactly, using randomness only to keep itself balanced without
the rotation bookkeeping a [balanced tree](./balanced-trees.md) needs.

## Core Concepts

| Term | Meaning |
|---|---|
| **False positive** | "Yes, it's a member" when it is not — the error a Bloom filter accepts |
| **False negative** | "No, it's not a member" when it is — a Bloom filter *never* does this |
| **Hash function, k of them** | A Bloom filter uses k independent hash functions per element |
| **Sketch** | A fixed-size summary that approximates a statistic (count, cardinality) over a stream |
| **Cardinality** | The number of *distinct* elements — what HyperLogLog estimates |
| **Skip list level** | A tier of "express lane" pointers; higher levels skip more nodes, chosen randomly |

## Mechanism

### Bloom filter: the false-positive formula, worked on 16 bits

A Bloom filter is `m` bits, all initially 0, plus `k` independent hash functions. `insert(x)` sets bit
`h_i(x) mod m` to 1 for each of the `k` hashes. `query(x)` reports "possibly present" if every one of
those `k` bits is 1, and "definitely absent" the moment any one of them is 0 — a bit can only ever be
set by an insert, never cleared, so a false *negative* is structurally impossible; the only way to be
wrong is for *other* elements' insertions to have coincidentally already set all `k` bits some element
never touched.

Traced on a 16-bit filter, $k = 2$ hash functions, inserting `"cat"` and `"dog"`, then querying `"cow"`:

```text
m = 16 bits, k = 2, bits indexed 0..15, all start at 0

insert("cat"): h1("cat")=3,  h2("cat")=11   -> set bits 3, 11
  bits: 0000 0001 0000 0010   (bit 3 and bit 11 now 1)

insert("dog"): h1("dog")=7,  h2("dog")=11   -> set bits 7, 11 (11 already set)
  bits: 0000 0001 0001 0010   (bit 7 now also 1)

query("cow"):  h1("cow")=3,  h2("cow")=7
  bit 3 is 1 (set by "cat"), bit 7 is 1 (set by "dog") -> BOTH set
  filter reports "possibly present" — a FALSE POSITIVE: "cow" was never inserted.
  It happened because "cat" and "dog" together, by coincidence, set exactly
  the two bits "cow" would have needed.
```

The false-positive probability, for `n` inserted elements, `m` bits and `k` hash functions, assuming
independent uniform hashing:

$$p \approx \left(1 - e^{-kn/m}\right)^k$$

Rewritten in bits-per-element $b = m/n$, this is minimised at $k = (\ln 2) \cdot b \approx 0.693b$ —
more hash functions help up to a point, then start hurting because each additional hash sets more bits
faster than it rules out more false candidates.

<Figure src="/img/cs/algorithms/bloom-false-positive-rate.png"
        alt="Log-scale line chart of Bloom filter false-positive rate against bits per element, for k = 3, 5 and 7 hash functions; all three curves fall steeply, crossing near 8 bits per element, with k = 7 lowest at high bits-per-element and k = 3 lowest at low bits-per-element"
        caption="More hash functions (higher k) only pay off once there is enough memory per element to support them — at low bits-per-element, fewer hashes (k = 3) actually gives a lower false-positive rate." />

### Count-min sketch: frequency counts that only overestimate

A count-min sketch is a 2D array of `d` rows by `w` columns, each row with its own independent hash
function. `add(x)` increments `sketch[i][h_i(x)]` for every row `i`. `estimate(x)` returns the
**minimum** across the `d` cells `x` hashes to — taking the minimum is what makes the sketch
overestimate-only: any single row's count for `x` may be inflated by hash collisions with other
elements, but the true count is a lower bound on every row's cell, so the minimum across independent
rows is the tightest available bound, never below the truth. This is the same shape of trade as a
Bloom filter (multiple independent hashes, one structure shared by everything hashed into it) applied
to counting instead of membership.

### HyperLogLog, in outline

Counting *distinct* elements exactly needs to remember every element seen — no way around it without
approximation. HyperLogLog's insight: hash each element to a uniform random bit string, and the
position of that string's *leftmost 1-bit* has a distribution that depends only on how many distinct
values have been hashed — seeing a hash with 20 leading zeros before its first 1-bit is unlikely
unless roughly $2^{20}$ distinct values have been tried. Splitting the hash space into thousands of
independent buckets and averaging each bucket's maximum leftmost-1-bit position (harmonic-mean
averaged, to control variance) turns that single noisy signal into an estimate accurate to roughly 2%
using a few kilobytes, regardless of whether the true cardinality is a thousand or a billion (Flajolet
et al., "HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm," 2007). This
page states the mechanism's shape and its accuracy bound without deriving the bias-correction constant
the original paper works out in full.

### Skip lists

A skip list is a sorted linked list with extra "express lane" pointers layered on top, chosen
randomly: each node gets a level $\geq 1$ by a coin-flip process (level $k$ with probability
$2^{-k}$), and a node at level $k$ has forward pointers at every level up to $k$. Searching starts at
the top level, moves forward while the next node's key is still less than the target, and drops down a
level whenever moving forward would overshoot — the same doubling structure that gives a balanced
binary search tree its $O(\log n)$ height, but assembled by chance instead of by rotations. The
expected search cost is $O(\log n)$; a run of unlucky coin flips can degrade this, but that is a
probability-bounded tail, not a guaranteed worst case the way an unbalanced BST's $O(n)$ chain is
(Pugh, "Skip Lists: A Probabilistic Alternative to Balanced Trees," 1990).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import hashlib


class BloomFilter:
    def __init__(self, size_bits, k):
        self.size = size_bits
        self.k = k
        self.bits = 0                              # one Python int used as a bit array

    def _hashes(self, item):
        for i in range(self.k):
            digest = hashlib.sha256(f"{i}:{item}".encode()).digest()
            yield int.from_bytes(digest, "big") % self.size

    def add(self, item):
        for h in self._hashes(item):
            self.bits |= (1 << h)

    def __contains__(self, item):                  # "possibly present" or "definitely absent"
        return all(self.bits & (1 << h) for h in self._hashes(item))


class CountMinSketch:
    def __init__(self, width, depth):
        self.width, self.depth = width, depth
        self.table = [[0] * width for _ in range(depth)]

    def _hash(self, row, item):
        digest = hashlib.sha256(f"{row}:{item}".encode()).digest()
        return int.from_bytes(digest, "big") % self.width

    def add(self, item, count=1):
        for row in range(self.depth):
            self.table[row][self._hash(row, item)] += count

    def estimate(self, item):
        return min(self.table[row][self._hash(row, item)] for row in range(self.depth))
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <bitset>
#include <functional>
#include <string>
#include <vector>

template <std::size_t Bits>
class BloomFilter {
public:
    explicit BloomFilter(int k) : k_(k) {}

    void add(const std::string& item) {
        for (int i = 0; i < k_; ++i) bits_.set(hash(i, item));
    }

    bool maybe_contains(const std::string& item) const {   // never a false negative
        for (int i = 0; i < k_; ++i)
            if (!bits_.test(hash(i, item))) return false;
        return true;
    }

private:
    std::size_t hash(int salt, const std::string& item) const {
        return std::hash<std::string>{}(std::to_string(salt) + item) % Bits;
    }
    std::bitset<Bits> bits_;
    int k_;
};
```

</TabItem>
</Tabs>

## Practical Usage

```python showLineNumbers
bf = BloomFilter(size_bits=16, k=2)

# reproduce the traced example with hashes pinned to match the worked trace above
class PinnedBloom(BloomFilter):
    _table = {("cat", 0): 3, ("cat", 1): 11, ("dog", 0): 7, ("dog", 1): 11,
              ("cow", 0): 3, ("cow", 1): 7, ("fox", 0): 0, ("fox", 1): 1}
    def _hashes(self, item):
        for i in range(self.k):
            yield self._table[(item, i)]

pb = PinnedBloom(size_bits=16, k=2)
pb.add("cat")
pb.add("dog")
assert "cat" in pb and "dog" in pb          # true positives
assert "cow" in pb                          # the false positive traced above
assert "fox" not in pb                      # bits 3/7/11 don't cover fox's hashes here

cms = CountMinSketch(width=64, depth=4)
for word in ["a", "b", "a", "c", "a", "b"]:
    cms.add(word)
assert cms.estimate("a") >= 3               # true count is 3; sketch never underestimates
assert cms.estimate("z") >= 0               # never negative, may overestimate an unseen key
```

- **Bloom filters gate expensive lookups.** Databases (Cassandra, HBase, Postgres extensions) and CDN
  edge caches check a Bloom filter before an expensive disk read or origin fetch — a "definitely
  absent" answer skips the read entirely, and the rare false positive costs one wasted read, not a
  wrong answer.
- **Count-min sketches back "heavy hitters" queries.** Network traffic analysis and streaming
  analytics use them to answer "top-k most frequent items" over a stream too large to store exactly.
- **HyperLogLog powers `COUNT(DISTINCT ...)` at scale.** Redis's `PFADD`/`PFCOUNT`, and BigQuery's
  `APPROX_COUNT_DISTINCT`, are HyperLogLog under the hood — exact distinct-count over billions of rows
  is not memory-feasible, and callers who ask for it are usually fine with 2% error.
- **Skip lists back real ordered-map implementations.** Redis's sorted set (`ZSET`) is a skip list
  precisely because concurrent insert is simpler to implement correctly with random levels than with
  rotation-based rebalancing — no cited claim of a skip list being asymptotically superior to a
  balanced tree, only that its probabilistic balancing is easier to get right under concurrent access.

## Edge Cases & Pitfalls

- **Treating a Bloom filter's "yes" as certain.** "Possibly present" is not "present" — code that skips
  a real membership check after a Bloom filter says yes silently accepts the false-positive rate as a
  correctness bound, which it usually is not meant to be.
- **Not sizing `m` and `k` for the actual `n`.** A Bloom filter sized for 1,000 elements and then filled
  with 100,000 saturates — nearly every bit sets to 1, and the false-positive rate approaches 1
  regardless of `k`. Size $m$ from the target false-positive rate and expected $n$ *before* filling it.
- **No deletion, ever, from a plain Bloom filter.** Clearing a bit because one element that set it was
  removed can un-set a bit another still-present element also depends on — a Bloom filter supports
  insert and query only. Deletion needs a counting Bloom filter (small counters instead of bits),
  which trades more memory for that one extra operation.
- **Reporting a HyperLogLog or count-min estimate as exact.** Both carry a stated error bound; treating
  their output as ground truth in a context that needs exactness (billing, auditing) is a
  category error, not a tuning problem.
- **Assuming a skip list's O(log n) is a hard worst case.** It is an expectation over the random level
  assignment. Pathologically unlucky coin flips (astronomically unlikely, but not impossible) degrade
  a search toward $O(n)$ — the same caveat that applies to randomized quicksort's pivot choice.

## Comparisons

| | Bloom filter | Count-min sketch | HyperLogLog | Skip list |
|---|---|---|---|---|
| Answers | Set membership | Item frequency | Distinct count | Ordered map (exact) |
| Error direction | False positive only | Overestimate only | Either direction, ~2% | None — exact |
| Memory vs. exact structure | Orders of magnitude smaller | Orders of magnitude smaller | Kilobytes for billions of items | Comparable to a balanced tree |
| Deletion | Not supported (plain form) | Not supported (plain form) | Not supported | $O(\log n)$ expected |
| Typical use | Skip an expensive lookup | Streaming top-k / heavy hitters | `COUNT(DISTINCT ...)` at scale | Concurrent ordered sets (Redis `ZSET`) |

## Recall

<Recall
  invariant="Each structure fixes a specific error it accepts — false positive, overestimate, or bounded percentage — as a formula in its own memory budget, and never errs in any other direction. A skip list alone trades no correctness, only guaranteed balance, for randomness."
  costs={[
    ["Bloom filter insert / query (worst)", "O(k), k = number of hash functions"],
    ["Bloom filter false-positive rate", "p ≈ (1 − e^(−kn/m))^k — a formula, not an estimate"],
    ["count-min sketch add / estimate (worst)", "O(d), d = number of rows"],
    ["HyperLogLog add / estimate (worst)", "O(1) amortized"],
    ["skip list search / insert / delete (expected)", "O(log n)"],
  ]}
  reachFor="Membership, frequency, or cardinality over data too large to store exactly, where a small quantified error rate is acceptable in exchange for sublinear memory."
  trap="Treating a Bloom filter's positive answer as certain, or reporting a HyperLogLog/count-min estimate as an exact count — both structures document their error bound precisely so it is never mistaken for zero."
/>

## References

- B. H. Bloom, "Space/Time Trade-offs in Hash Coding with Allowable Errors," *Communications of the
  ACM* 13(7), 1970 — the original Bloom filter and the false-positive-rate derivation used above.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §11.5 "Exercises" briefly
  poses Bloom filters as an exercise on hashing; the full development here follows Bloom's original
  paper and Broder & Mitzenmacher's survey below, not CLRS's main text.
- A. Broder & M. Mitzenmacher, "Network Applications of Bloom Filters: A Survey," *Internet
  Mathematics* 1(4), 2004 — count-min-adjacent variants and the standard $k = (\ln 2) m/n$ optimum.
- P. Flajolet, É. Fusy, O. Gandouet & F. Meunier, "HyperLogLog: the analysis of a near-optimal
  cardinality estimation algorithm," *AOFA*, 2007 — the leftmost-1-bit estimator and its bias
  correction, outlined but not derived above.
- W. Pugh, "Skip Lists: A Probabilistic Alternative to Balanced Trees," *Communications of the ACM*
  33(6), 1990 — the randomized-level construction and its expected $O(\log n)$ bound.

## Related Pages

- [Hash Tables](./hash-tables.md) — the exact structure a Bloom filter trades correctness for memory
  against, and the source of the independent-hash-function assumption used in the false-positive
  formula.
- [Balanced Trees](./balanced-trees.md) — the rotation-based alternative to a skip list's randomized
  balancing, with the same $O(\log n)$ expected/guaranteed operations.
- [Union-Find](./union-find.md) — another structure that gives up a general capability (splitting sets)
  for speed on the one operation it keeps.
- [Cheat Sheet](./cheat-sheet.md) — the full operation-cost matrix across every structure in this
  folder.
