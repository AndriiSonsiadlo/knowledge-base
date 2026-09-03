---
id: hash-tables
title: Hash Tables
sidebar_label: Hash Tables
sidebar_position: 4
tags: [computer-science, algorithms, data-structures, hash-table, hashing]
---

# Hash Tables

A hash table turns a key into an array index by running it through a **hash function**, then reads or
writes that slot directly. Because indexing an array is $O(1)$, lookup by arbitrary key becomes $O(1)$
too — which is a genuinely surprising result, and the reason `dict`, `HashMap`, `unordered_map` and
`Object` are the most-used structures in programming.

<Figure src="/img/cs/algorithms/hash-table.png"
        alt="Three name keys on the left, each connected through a hash function box to a numbered bucket on the right holding the corresponding phone number"
        caption="The hash function maps a key directly to a bucket index. No search takes place — the key's own content computes its location."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Hash_table_3_1_1_0_1_0_0_SP.svg"
        license="CC BY-SA 3.0" />

## Core Concepts

| Term | Meaning |
|---|---|
| **Hash function** | Maps a key to an integer, ideally spreading keys uniformly across the range |
| **Bucket / slot** | One entry in the backing array |
| **Collision** | Two distinct keys hashing to the same bucket — unavoidable, and the whole design problem |
| **Load factor (α)** | `entries / buckets`. The single number governing performance |
| **Rehashing** | Allocating a larger array and reinserting everything, when α grows too large |

## Mechanism

### Collisions are not an edge case

With more possible keys than buckets, collisions are guaranteed by pigeonhole. They arrive far
earlier than intuition suggests: by the birthday paradox, 23 keys in 365 buckets already collide with
probability > 50%.

<Figure src="/img/cs/algorithms/hash-collision.png"
        alt="Four name keys mapped through a hash function to numbered slots, with two of them — highlighted in red — arriving at the same slot 02"
        caption="Two different keys, one bucket. Everything below is about what to do at this moment."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Hash_table_4_1_1_0_0_1_0_LL.svg"
        license="Public domain" />

### The two resolution strategies

**Separate chaining** — each bucket holds a container (classically a
[linked list](./linked-lists.md), sometimes a tree) of all entries that landed there:

```text
bucket 01 -> ("Lisa Smith", 521-8976)
bucket 02 -> ("John Smith", 521-1234) -> ("Sandra Dee", 521-9655)
bucket 03 -> (empty)
```

**Open addressing** — everything lives in the array itself, and a collision probes for another free
slot by a fixed rule (linear probing: try the next slot; quadratic; double hashing):

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def insert_linear_probe(table, key, value):
    i = hash(key) % len(table)
    while table[i] is not None and table[i][0] != key:
        i = (i + 1) % len(table)     # walk forward until a free slot
    table[i] = (key, value)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cstddef>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

template <typename Key, typename Value>
struct Slot { bool used = false; Key key; Value value; };

template <typename Key, typename Value>
void insert_linear_probe(std::vector<Slot<Key, Value>>& table, const Key& key, const Value& value) {
    std::size_t i = std::hash<Key>{}(key) % table.size();
    while (table[i].used && table[i].key != key)
        i = (i + 1) % table.size();      // walk forward until a free slot
    table[i] = {true, key, value};
}
```

</TabItem>
</Tabs>

| | Separate chaining | Open addressing |
|---|---|---|
| Load factor tolerated | > 1 works, degrades gracefully | Must stay below ~0.7, collapses near 1.0 |
| Memory | Pointer per entry, plus nodes | No per-entry overhead, but empty slots |
| Cache behaviour | Poor — chains chase pointers | Excellent — probes are sequential |
| Deletion | Simple: unlink | Awkward: needs tombstones |
| Used by | Java `HashMap`, older C++ `unordered_map` | Python `dict`, Rust `HashMap`, Go maps, Swift |

Most modern implementations chose open addressing, and the reason is the cache column.

### Four keys, eight buckets, one collision — traced

Insert `"cat"`, `"dog"`, `"bird"`, `"ant"` into an 8-bucket table (indices 0–7), using a hash function
that happens to send both `"cat"` and `"dog"` to bucket 3 — the collision the design has to handle:

```text
key      hash(key) % 8    bucket

"cat"    3                3   -> empty, insert directly
"dog"    3                3   -> occupied by "cat" — COLLISION
"bird"   5                5   -> empty, insert directly
"ant"    0                0   -> empty, insert directly

separate chaining, after all four inserts:
  bucket 0 -> ("ant", …)
  bucket 3 -> ("cat", …) -> ("dog", …)      # chain of length 2 — the collision
  bucket 5 -> ("bird", …)
  (buckets 1, 2, 4, 6, 7 empty)

open addressing (linear probing), after all four inserts:
  bucket 0 -> ("ant", …)
  bucket 3 -> ("cat", …)                     # got its home slot first
  bucket 4 -> ("dog", …)                     # probed forward from 3, found 4 free
  bucket 5 -> ("bird", …)
  (buckets 1, 2, 6, 7 empty)
```

Both strategies store the same four entries; they disagree only about where `"dog"` ends up. Chaining
leaves it in a 2-element list still addressed by bucket 3; open addressing physically relocates it to
the first free slot found by the probe sequence. Looking `"dog"` up afterwards costs one extra
comparison either way — a linked-list traversal of length 2, or one extra probe — the case that
distinguishes $O(1)$ **average** from the $O(1)$ **best case** ("cat", "ant", "bird" all found in one
step).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def insert_chained(table, key, value, bucket_of):
    table[bucket_of(key)].append((key, value))     # append to that bucket's list

def insert_linear_probe_full(table, key, value, bucket_of):
    i = bucket_of(key)
    while table[i] is not None:
        i = (i + 1) % len(table)
    table[i] = (key, value)

def bucket_of(key):   # a hash function stubbed to reproduce the trace above
    return {"cat": 3, "dog": 3, "bird": 5, "ant": 0}[key]

chained = [[] for _ in range(8)]
for k in ("cat", "dog", "bird", "ant"):
    insert_chained(chained, k, True, bucket_of)
assert chained[3] == [("cat", True), ("dog", True)]   # the chain the collision produced
assert chained[0] == [("ant", True)]

probed = [None] * 8
for k in ("cat", "dog", "bird", "ant"):
    insert_linear_probe_full(probed, k, True, bucket_of)
assert probed[3] == ("cat", True)
assert probed[4] == ("dog", True)      # probed forward one slot past the collision
assert probed[5] == ("bird", True)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <array>
#include <optional>
#include <string>
#include <utility>
#include <vector>

int bucket_of(const std::string& key) {
    if (key == "cat" || key == "dog") return 3;
    if (key == "bird") return 5;
    return 0;   // "ant"
}

void insert_chained(std::array<std::vector<std::string>, 8>& table, const std::string& key) {
    table[bucket_of(key)].push_back(key);
}

void insert_linear_probe(std::array<std::optional<std::string>, 8>& table, const std::string& key) {
    int i = bucket_of(key);
    while (table[i].has_value()) i = (i + 1) % 8;
    table[i] = key;
}
```

</TabItem>
</Tabs>

### Load factor is the dial that controls everything

<Figure src="/img/cs/algorithms/hash-table-load-factor.png"
        alt="Average cache misses per lookup plotted against load factor: chaining rises gently and almost linearly, while linear probing stays lower until about 0.8 and then climbs almost vertically"
        caption="Linear probing is cheaper than chaining across most of the range — until roughly α = 0.8, where clustering takes over and the cost explodes."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Hash_table_average_insertion_time.png"
        license="Public domain" />

This curve is why implementations rehash. When α crosses a threshold (0.75 in Java, ~0.66 in Python,
0.875 in Rust's hashbrown), the table allocates a larger array — usually double — and reinserts every
entry. Rehashing is $O(n)$, but it happens rarely enough to be **$O(1)$ amortized**, by the same
doubling argument as [dynamic arrays](./arrays.md).

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Pre-size when the count is known, to avoid repeated rehashing
seen = dict()                      # Python: no capacity argument
# Java:  new HashMap<>(expectedSize / 0.75f + 1)
# C++:   m.reserve(expectedSize)
# Go:    make(map[string]int, expectedSize)

# The classic use: turning a nested scan into a single pass
def two_sum(nums, target):
    seen = {}                      # value -> index
    for i, x in enumerate(nums):
        if target - x in seen:     # O(1) instead of an inner loop
            return seen[target - x], i
        seen[x] = i
    return None
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
// Pre-size when the count is known, to avoid repeated rehashing
std::unordered_map<std::string, int> seen;
seen.reserve(expected_size);        // max_load_factor defaults to 1.0
```

```cpp showLineNumbers
// The classic use: turning a nested scan into a single pass
std::optional<std::pair<int, int>> two_sum(const std::vector<int>& nums, int target) {
    std::unordered_map<int, int> seen;              // value -> index
    for (int i = 0; i < static_cast<int>(nums.size()); ++i) {
        auto it = seen.find(target - nums[i]);      // O(1) instead of an inner loop
        if (it != seen.end()) return std::pair{it->second, i};
        seen[nums[i]] = i;
    }
    return std::nullopt;
}
```

</TabItem>
</Tabs>

That rewrite — replacing an $O(n^2)$ nested scan with an $O(n)$ pass and a hash table — is the single most
common application of the structure, and worth recognising on sight.

## Edge Cases & Pitfalls

:::danger[Mutating a key after insertion loses the entry]
An entry's bucket is determined by the key's hash at insertion time. Mutate the key and its hash
changes, but the entry does not move — so the table now looks in the wrong bucket, and the entry is
unreachable while still consuming space.

Python and Rust prevent this structurally by requiring keys to be immutable/hashable. Java does not:
a mutable object used as a `HashMap` key, mutated afterwards, is a silent and genuinely hard-to-find
leak. Use immutable keys.
:::

- **`equals` and `hashCode` must agree.** Two keys that compare equal must hash equally, or lookups
  fail unpredictably. Overriding one without the other is the classic Java bug; the same contract
  exists as `__eq__`/`__hash__` in Python and `Eq`/`Hash` in Rust.
- **Worst case is $O(n)$.** If every key collides, the table degenerates to a linear scan. Java 8+
  converts long chains to red-black trees, capping degradation at $O(\log n)$.
- **Hash-flooding is a real attack.** An attacker who can predict your hash function can force
  collisions deliberately and turn an $O(1)$ endpoint into $O(n)$ — a denial of service from ordinary
  traffic. This is why Python, Rust and others use randomly seeded hashing (SipHash) by default.
  Never use a fast non-cryptographic hash on attacker-controlled keys without a per-process seed.
- **Iteration order is not insertion order** in general. Python's `dict` has guaranteed insertion
  order since 3.7 and Go deliberately randomises it; do not rely on either unless the language
  promises it.

## Comparisons

| | Hash table | [Balanced BST](./balanced-trees.md) |
|---|---|---|
| Lookup | $O(1)$ expected | $O(\log n)$ guaranteed |
| Worst case | $O(n)$ ($O(\log n)$ if treeified) | $O(\log n)$ |
| Ordering | None | Sorted |
| Range queries, min/max, successor | Not supported | Natural |
| Memory | Empty slots or chain overhead | Two pointers per node |
| Choose it when | You look up exact keys | You need order, ranges, or worst-case bounds |

## Recall

<Recall
  invariant="A hash function maps a key to a bucket index; two distinct keys mapping to the same bucket is a collision, resolved by chaining or by probing for another slot."
  costs={[
    ["lookup / insert / delete (expected)", "O(1)"],
    ["lookup / insert / delete, worst case", "O(n)"],
    ["rehash when load factor crosses the threshold (amortized)", "O(1)"],
    ["rehash itself, one occurrence (worst)", "O(n)"],
  ]}
  reachFor="You look things up by an arbitrary key and never need sorted order or range queries."
  trap="Mutating a key after it is inserted — the entry's bucket was fixed by the key's hash at insertion time, so the table now looks in the wrong bucket and the entry becomes silently unreachable."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 11 — hash tables, chaining, open addressing, and universal hashing.
- [CPython dict design notes](https://github.com/python/cpython/blob/main/Objects/dictobject.c) — the compact, insertion-ordered open-addressing design used since 3.6.
- Crosby & Wallach, ["Denial of Service via Algorithmic Complexity Attacks"](https://www.usenix.org/legacy/events/sec03/tech/full_papers/crosby/crosby.pdf) — the paper that made hash-flooding a mainstream concern.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §3.4 — hash tables with both collision strategies implemented and measured.

## Related Pages

- [Arrays & Dynamic Arrays](./arrays.md) — the backing store, and the source of the amortized-rehash argument.
- [Balanced Trees](./balanced-trees.md) — the ordered alternative.
- [Searching Algorithms](../searching/intro.md) — where hashing sits among the ways to find things.
