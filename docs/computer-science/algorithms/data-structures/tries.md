---
id: tries
title: Tries (Prefix Trees)
sidebar_label: Tries
sidebar_position: 10
tags: [computer-science, algorithms, data-structures, tries, strings]
---

# Tries (Prefix Trees)

A hash set answers "is this exact string in the set?" and nothing else. It cannot answer "what strings
start with `ca`?" without scanning every entry, because hashing deliberately destroys any relationship
between a string and its prefixes — that is the whole point of a good hash function. A trie is the
structure built for the opposite trade: it throws away the O(1) whole-string lookup and gets, in
return, every prefix operation for free.

The idea is to stop storing *strings* and start storing *paths*. Every node is one character position;
following edges from the root spells out a string one character at a time. Two words that share a
prefix share the path down to where they diverge — `cat` and `car` are the same three nodes and then
split at the fourth. Nothing is duplicated for the shared part, and that sharing is also what makes
prefix queries cheap: walking to the node for `ca` visits every word that starts with `ca` in one
traversal, because they all pass through it on the way down.

A node's only real job is to answer one question — "given the next character, which child do I go
to?" — but *how* it answers it is where the design space lives. That single choice, covered below,
determines whether a trie feels memory-hungry or featherlight.

## Core Concepts

| Term | Meaning |
|---|---|
| **Node** | One character position on some path from the root; not itself a full key |
| **Root** | The empty-string node — every key's path starts here |
| **Child map** | The node's answer to "which child for character c?" — array, hash map, or sorted list |
| **End-of-word marker** | A flag on the node reached after the last character of an inserted key |
| **Prefix** | Any path from the root; a key is a prefix that is also marked end-of-word |
| **Radix / compressed trie** | A trie where chains of single-child nodes are collapsed into one edge labelled with a substring |

A node with no children and no end marker simply does not exist — a trie only ever materialises the
nodes some inserted key actually needs.

## Mechanism

<Figure src="/img/cs/algorithms/trie.png"
        alt="A trie over the keys A, to, tea, ted, ten, i, in and inn, with each end-of-key node carrying a blue stored value; the 't' branch shares one path down to 'te' before splitting into tea, ted and ten"
        caption="A trie used as a map: each end-of-key node (the deepest circle on its path) carries a stored value in blue. 'tea', 'ted' and 'ten' all reuse the same root → t → te path and diverge only at their last character."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Trie_example.svg"
        license="Public domain" />

Traced over `insert("cat")`, `insert("car")`, `insert("card")`, then `starts_with("ca")`:

```text
insert "cat":              insert "car":               insert "card":
root                       root                        root
 └─c                        └─c                          └─c
    └─a                        └─a                          └─a
       └─t*                       ├─t*                         ├─t*
                                   └─r*                         └─r*
                                                                    └─d*
new nodes: c, a, t(*)       new nodes: r(*)             new nodes: d(*)
                             (c, a are reused —          (c, a, r are reused —
                              already on the path)        already on the path)

* marks is_end = True

starts_with("ca"): walk root → c → a — 2 steps, found the node, stop.
No character of "cat", "car" or "card" beyond index 2 is touched.
Every word reachable below this node (cat, car, card) is a completion of "ca".
```

Only three character-steps of work locate the prefix node no matter how many words hang below it —
the cost of a prefix query is the length of the *prefix*, never the number or length of the matches.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self):
        self.children = {}      # hash map: pays only for children that exist
        self.is_end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:                          # O(L), L = len(word)
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def _walk(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def search(self, word):                      # exact-key membership
        node = self._walk(word)
        return node is not None and node.is_end

    def starts_with(self, prefix):                # prefix existence
        return self._walk(prefix) is not None
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <array>
#include <memory>
#include <string>

struct TrieNode {
    std::array<std::unique_ptr<TrieNode>, 26> children{};  // fixed 26 slots, lowercase a-z
    bool is_end = false;
};

class Trie {
public:
    void insert(const std::string& word) {
        TrieNode* node = &root_;
        for (char c : word) {                     // O(L), L = word.size()
            int i = c - 'a';
            if (!node->children[i]) node->children[i] = std::make_unique<TrieNode>();
            node = node->children[i].get();
        }
        node->is_end = true;
    }

    const TrieNode* walk(const std::string& prefix) const {
        const TrieNode* node = &root_;
        for (char c : prefix) {
            int i = c - 'a';
            if (!node->children[i]) return nullptr;
            node = node->children[i].get();
        }
        return node;
    }

    bool search(const std::string& word) const {
        auto* n = walk(word);
        return n && n->is_end;
    }

    bool starts_with(const std::string& prefix) const { return walk(prefix) != nullptr; }

private:
    TrieNode root_;
};
```

</TabItem>
</Tabs>

### Node layouts: three ways to answer "which child for c?"

The child-lookup structure is the only real design decision in a trie; everything else follows from it.

| Layout | Memory per node | Child lookup | Child insert | Best when |
|---|---|---|---|---|
| **Array of 26** (or of the alphabet size) | Fixed $26 \times 8$ bytes = 208 bytes on a 64-bit build, whether the node has 1 child or 26 | $O(1)$ | $O(1)$ | Small, fixed alphabet; nodes are usually well-branched (dictionary words) |
| **Hash map** | Proportional to children actually present; a Python `dict` grows in amortized $O(1)$ per insert (Python docs, [`dict`](https://docs.python.org/3/library/stdtypes.html#dict)) | $O(1)$ average | $O(1)$ amortized | Large or unknown alphabet (Unicode), sparse branching |
| **Sorted list of children** | Compact — one entry per child, no wasted slots | $O(\log k)$ via binary search, k = number of children at that node | $O(k)$ worst, to keep the list sorted | Memory-constrained, few children per node, built once and rarely mutated |

The array layout trades memory for guaranteed $O(1)$: a trie of short English words has thousands of
nodes with only 1–2 children each, and every one of them still pays for 26 pointer slots. The hash-map
layout is what the Python implementation above uses, and it is the right default whenever the alphabet
is large (Unicode text) or the branching factor is unpredictable.

### Cost versus a hash set of whole words

A `set` of complete strings gives $O(L)$ average-case membership — computing the hash still touches
every character — so exact-match cost is the same order as a trie's. The difference is everything
else:

- **Prefix queries.** "Every key starting with `pre`" costs $O(|pre|)$ to locate the node in a trie,
  then $O(m)$ to enumerate $m$ matches. In a hash set it costs $O(n \cdot L)$ — scan every one of the
  $n$ entries and check each prefix — because hashing threw away exactly the locality a trie keeps
  (Sedgewick & Wayne, 4th ed., §5.2).
- **Memory.** A trie is smaller than a hash set when keys share a lot of structure — a dictionary of
  English words, a filesystem's paths — because shared prefixes are stored once. It is larger when
  keys share little (random tokens, hashes), because per-node overhead is paid on every character
  regardless of sharing.
- **Ordered iteration.** Walking a trie in a fixed child order (say, alphabetical) yields keys in
  sorted order for free. A hash set's iteration order carries no such guarantee.

### Autocomplete

Locate the prefix node in $O(|prefix|)$, then depth-first from there, collecting every node with
`is_end` set:

```python showLineNumbers
# doc:no-run
def autocomplete(trie, prefix, limit=10):
    node = trie._walk(prefix)
    if node is None:
        return []
    results = []

    def dfs(node, path):
        if len(results) >= limit:
            return
        if node.is_end:
            results.append(prefix + path)
        for ch, child in node.children.items():
            dfs(child, path + ch)

    dfs(node, "")
    return results
```

Cost is $O(|prefix|)$ to find the node plus $O(k)$ for the subtree actually visited, where $k$ is
bounded by `limit` once enough matches are found — never the size of the whole trie.

### Radix / compressed tries

A trie built over sparse keys — file paths, IP prefixes, UUIDs — spends most of its nodes on chains
with exactly one child: `/usr/local/bin` is fifteen single-child nodes before the path ever branches.
A **radix trie** (also called a Patricia trie) collapses each such chain into a single edge labelled
with the whole substring, so a chain of $k$ single-child nodes becomes one edge and one node. Lookup
now compares substrings instead of single characters, but the node count drops to roughly the number
of *branch points* rather than the number of characters stored — the original construction is due to
D. R. Morrison, "PATRICIA — Practical Algorithm To Retrieve Information Coded in Alphanumeric",
*JACM* 15(4), 1968. Compressed tries are named, not derived here, because the mechanism — the
representation is described above, but the incremental-edge-splitting insert algorithm that keeps a
radix trie compressed as new keys arrive is its own structure; see the reference for the full
construction. IP routers use exactly this structure (longest-prefix match over CIDR blocks), and it is
why the term "radix tree" appears throughout networking code.

## Practical Usage

Neither Python nor C++ ships a trie type — like union-find, it is a structure you write, because the
right node layout depends on the alphabet and access pattern. Where it is worth building:

- **Autocomplete and typeahead.** Search-bar suggestions, IDE symbol completion: the prefix-then-DFS
  pattern above, usually with an early cutoff at a handful of results.
- **Spell-checking and dictionary lookup.** `search` for exact membership, plus `starts_with` to prune
  a search early — no point continuing down a branch that cannot complete to any real word.
- **IP routing tables.** Longest-prefix match over CIDR blocks is a lookup on a compressed (radix)
  trie keyed on address bits rather than characters.
- **T9-style predictive text and word games.** Any problem that asks "which words are consistent with
  this partial input" is a prefix query.

```python showLineNumbers
trie = Trie()
for word in ("cat", "car", "card"):
    trie.insert(word)

assert trie.search("cat") and trie.search("car") and trie.search("card")
assert not trie.search("ca")             # "ca" is a prefix, never inserted as its own key
assert trie.starts_with("ca")            # but the prefix path does exist
assert not trie.starts_with("do")        # no path at all for an unrelated prefix
assert trie._walk("ca") is trie.root.children["c"].children["a"]   # the shared c -> a path
```

`collections.defaultdict` (Python docs,
[`collections.defaultdict`](https://docs.python.org/3/library/collections.html#collections.defaultdict))
is a common shortcut for the node's child map — `defaultdict(TrieNode)` avoids the explicit
`setdefault` call above, at the cost of silently creating a node on every failed lookup, which is
wrong for `search` and `starts_with` (they must not mutate the trie). That is exactly why the
implementation above uses plain `dict` with `setdefault` only in `insert`.

## Edge Cases & Pitfalls

- **Confusing "prefix exists" with "word exists."** `starts_with("ca")` is true after inserting `cat`,
  but `search("ca")` is false unless `"ca"` was itself inserted as a key. The `is_end` flag is what
  distinguishes a key from a mere waypoint on the way to one.
- **`defaultdict`-as-children on a read path.** Using a `defaultdict` for `children` makes `search` and
  `starts_with` mutate the trie on a miss — every failed lookup permanently adds empty nodes. Use plain
  `dict` and check membership explicitly, or a `defaultdict` only inside `insert`.
- **Deleting a key without pruning.** Clearing `is_end` on the last node of a deleted key leaves every
  now-useless ancestor node in place if nothing else uses them. A correct delete walks back up
  (recursively, or with a stack of visited nodes) and removes each node that has no children and is
  not itself an end marker.
- **Fixed alphabet arrays over Unicode text.** An array-of-26 node silently corrupts on any input
  outside `a`-`z` (out-of-bounds index, or worse, silent wraparound in unchecked code). Anything beyond
  a small fixed alphabet needs the hash-map layout.
- **Case and normalization.** `"Cat"` and `"cat"` are different paths unless the caller normalizes case
  before inserting — a trie enforces no equivalence the input didn't already have.

## Comparisons

| | Trie | Hash set of strings | Sorted array of strings |
|---|---|---|---|
| Exact membership | $O(L)$ average | $O(L)$ average | $O(L \log n)$ worst — binary search, L per comparison |
| Prefix query ("starts with") | $O(|prefix|)$ to locate, then $O(m)$ for m matches | $O(n \cdot L)$ worst — full scan | $O(L \log n)$ to find the range, then $O(m)$ |
| Sorted iteration | Free — walk children in order | Not supported | Already sorted |
| Memory | Shared prefixes stored once; per-node overhead otherwise | One hash-table slot per string | One slot per string, no overhead per character |
| Insert | $O(L)$ | $O(L)$ amortized | $O(n)$ — must keep the array sorted |

A trie wins the moment prefix or "starts with" queries matter at all; a hash set is smaller and no
slower for pure exact-match workloads with little shared structure between keys.

## Recall

<Recall
  invariant="A path from the root spells out a string one character per edge; two keys share a node exactly as far as they share a prefix, and a node is a key only if its is_end flag is set."
  costs={[
    ["insert / search / starts_with (average)", "O(L), L = key length"],
    ["array-of-26 child lookup (worst)", "O(1)"],
    ["hash-map child lookup (average)", "O(1)"],
    ["autocomplete after locating the prefix (worst)", "O(k) for k results returned"],
    ["prefix scan on a hash set of n words (worst)", "O(n · L)"],
  ]}
  reachFor="The problem is about prefixes, not just exact keys — autocomplete, spell-check, longest-prefix routing, or 'which of these strings start with...'."
  trap="Checking search() when starts_with() is what was meant (or vice versa) — the is_end flag is the only thing that tells a real key apart from a waypoint on the way to one."
/>

## References

- Sedgewick & Wayne, *Algorithms*, 4th ed., §5.2 "Tries" — R-way tries, ternary search tries, and the
  memory-per-node trade-offs across layouts, with the prefix-query cost argument used above.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed. — tries are not a dedicated
  chapter in CLRS; the closest formal treatment is the string-matching chapter's discussion of
  suffix structures (Ch. 32), which builds on the same path-per-character idea.
- D. R. Morrison, "PATRICIA — Practical Algorithm To Retrieve Information Coded in Alphanumeric,"
  *Journal of the ACM* 15(4), 1968 — the original compressed (radix) trie.
- Python documentation, [`dict`](https://docs.python.org/3/library/stdtypes.html#dict) and
  [`collections.defaultdict`](https://docs.python.org/3/library/collections.html#collections.defaultdict) —
  the amortized-O(1) hash map used for the child-map layout above.

## Related Pages

- [Hash Tables](./hash-tables.md) — the structure a trie is usually compared against, and the source of
  the child-map layout's amortized cost.
- [Segment Trees and Fenwick Trees](./segment-trees-and-fenwick.md) — another tree shaped entirely by
  the query it answers, rather than by the data's natural order.
- [Strings & Text: KMP and the Z-Algorithm](../strings-and-text/kmp-and-z-algorithm.md) — pattern
  matching within one text, versus a trie's multi-key prefix search.
- [Trees & Binary Search Trees](./trees.md) — the general tree vocabulary (node, root, child) a trie
  specialises for one purpose.
