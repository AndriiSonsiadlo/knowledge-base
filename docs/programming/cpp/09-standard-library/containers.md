---
id: containers
title: STL Containers
sidebar_label: Containers
sidebar_position: 1
tags: [c++, stl, containers, vector, map, unordered-map, iterator-invalidation, complexity]
---

# Standard Library Containers

A **container** owns a collection of objects, manages their storage, and exposes them through
[iterators](./iterators.md) so that [algorithms](./algorithms.md) can work on any of them. The
library offers three families that differ in *how elements are found*: by position (sequence),
by ordering of keys (ordered associative), or by hash of keys (unordered associative). Choosing a
container is choosing which operations are cheap, and which iterators and references survive a
modification. This page is the canonical home for the containers, their complexity guarantees and
their invalidation rules. Allocator customisation is on [Allocators](./allocators.md).

**Prerequisites:** [Class templates](../08-templates-and-metaprogramming/class-templates.md),
[copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md),
[unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md) (for owning element
types).

<Diagram title="The container families" accent="blue">
  <DiagramRow>
    <DiagramGroup label="Sequence (by position)">
      <DiagramNode title="vector, array">contiguous</DiagramNode>
      <DiagramNode title="deque">chunked</DiagramNode>
      <DiagramNode title="list, forward_list">nodes</DiagramNode>
    </DiagramGroup>
    <DiagramGroup label="Associative (by key)">
      <DiagramNode title="set, map">ordered, tree-like</DiagramNode>
      <DiagramNode title="unordered_set, unordered_map">hashed buckets</DiagramNode>
    </DiagramGroup>
    <DiagramGroup label="Adapters">
      <DiagramNode title="stack, queue, priority_queue">restrict another container</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

## What every container promises

- Elements are stored **by value**: the container copies or moves them in and destroys them
  when removed or when the container dies. Store `std::unique_ptr<T>` for ownership of
  polymorphic or immovable objects.
- Element types must meet the requirements of the operations you call (for example `push_back(const T&)`
  needs `CopyInsertable`). Since C++17, `vector`, `list` and `forward_list` may be instantiated
  with an incomplete type as long as it is complete before any member is used.
- `size()`, `empty()`, `begin()/end()`, `swap` and `clear()` exist everywhere (`forward_list` has no
  `size()`). `swap` is constant time for everything except `std::array`, and no `swap` invalidates
  iterators, pointers or references to elements; they follow the elements into the other container
  (`end()` may be invalidated).
- `emplace`-style functions construct the element in place from constructor arguments instead of
  moving a temporary.

## Sequence containers

| Container | Header | Storage | Notes |
|---|---|---|---|
| `std::vector<T>` | `<vector>` | one contiguous heap block | the default choice |
| `std::array<T, N>` | `<array>` | inline, fixed size | aggregate; no heap allocation |
| `std::deque<T>` | `<deque>` | fixed-size blocks plus a map of block pointers | O(1) at both ends, indexable |
| `std::list<T>` | `<list>` | one node per element, doubly linked | O(1) splice, stable iterators |
| `std::forward_list<T>` | `<forward_list>` | one node per element, singly linked | no `size()`, no `push_back` |
| `std::inplace_vector<T, N>` *(C++26)* | `<inplace_vector>` | inline, capacity fixed at compile time | dynamic size, no allocation |

### `vector`

Contiguous storage makes `vector` the fastest container for traversal because the CPU prefetcher
and cache see sequential addresses. It distinguishes **size** (elements alive) from **capacity**
(elements that fit before reallocation). When `push_back` exceeds the capacity, the vector
allocates a bigger block, moves (or copies) the elements across, and frees the old block. The
growth factor is not specified by the standard (libstdc++ doubles, MSVC grows by 1.5x); only the
amortized-constant bound is guaranteed.

```cpp title="vector-capacity.cpp" showLineNumbers
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(100);                       // capacity() >= 100, size() still 0
    const int* before = v.data();
    for (int i = 0; i < 100; ++i) v.push_back(i);   // never reallocates
    std::cout << (v.data() == before) << ' ' << v.size() << '\n';

    v.shrink_to_fit();                    // a non-binding request to drop spare capacity
    std::vector<int> big(1000, 7);        // 1000 elements, all 7
    std::vector<int> two{1000, 7};        // braces pick the initializer_list: 2 elements
    std::cout << big.size() << ' ' << two.size() << '\n';
}
```

```text
1 100
1000 2
```

Two traps in that snippet. `reserve` is what makes the pointer stable: without it a reallocation
would move the elements. And `vector<int>(1000, 7)` versus `vector<int>{1000, 7}` differ because
list-initialization prefers the `initializer_list` constructor (see
[uniform initialization](../05-memory-and-object-lifetime/initialization/uniform-initialization.md)).

`std::vector<bool>` is a specialization that packs bits and returns a proxy from `operator[]`. It
is not a container of `bool` in the usual sense (you cannot take `bool&` from it). Use
`std::vector<char>`, `std::bitset` or `std::deque<bool>` when you need real references.

### `array`, `deque`, `list`, `forward_list`

`std::array<T, N>` is a thin wrapper over `T[N]` that adds the container interface and value
semantics (copyable, comparable, no decay to a pointer). It is an aggregate, so
`std::array<int, 3> a{1, 2, 3}` works, and `std::to_array` *(C++20)* deduces `N`.

`deque` keeps elements in fixed-size blocks, so growing at either end never moves existing
elements, and `operator[]` costs a little more than `vector`'s because of the two-level lookup. The
block size is implementation-defined (libstdc++ uses 512-byte blocks; libc++ uses larger ones).

`list` and `forward_list` allocate a node per element. Their selling point is not "fast insertion":
it is that **insertion, erasure and `splice` never move elements and never invalidate other
iterators**, and `splice`, `merge`, `reverse` and `remove` relink nodes. Searching a list is still
linear, and each step chases a pointer, so a `vector` often beats a `list` even for middle
insertion on small to medium sizes. Measure before choosing a list for speed.

## Ordered associative containers

`std::set<K>`, `std::map<K, V>`, `std::multiset<K>` and `std::multimap<K, V>` keep keys sorted by a
comparator (`std::less<K>` by default) and require it to be a **strict weak ordering**. Two keys
are *equivalent* when neither compares less than the other; `==` is never used. The standard
requires logarithmic lookup, insertion and erasure, which in practice means a red-black tree
(libstdc++, libc++ and MSVC all use one, though the standard does not name it). Iteration visits
keys in order, and `lower_bound`/`upper_bound`/`equal_range` give range queries.

```cpp title="map-api.cpp" showLineNumbers
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> age;

    age["Alice"] = 30;                          // operator[] inserts a default value first
    age.insert({"Bob", 25});                    // no-op if the key exists
    auto [it, inserted] = age.try_emplace("Bob", 99);   // C++17: does not touch an existing value
    age.insert_or_assign("Carol", 41);          // C++17: assigns if present

    std::cout << inserted << ' ' << it->second << '\n';     // 0 25
    std::cout << age.contains("Dave") << '\n';              // C++20
    std::cout << age.size() << '\n';                        // 3

    if (age.count("Dave") == 0 && age.at("Alice") == 30)    // at() throws std::out_of_range
        std::cout << "no Dave\n";
    age["Dave"];                                // oops: operator[] on a read just inserted Dave
    std::cout << age.size() << '\n';            // 4

    for (const auto& [name, years] : age)       // in key order
        std::cout << name << '=' << years << ' ';
    std::cout << '\n';
}
```

```text
0 25
0
3
no Dave
4
Alice=30 Bob=25 Carol=41 Dave=0 
```

- `operator[]` requires `V` to be default-constructible and always inserts when the key is absent;
  use `find`, `contains` *(C++20)* or `at` to read.
- `try_emplace` and `insert_or_assign` *(C++17)* avoid constructing the value when the key exists,
  and are the clear replacements for `operator[]` plus assignment and for `insert` of a pair.
- **Heterogeneous lookup** *(C++14)*: with a transparent comparator such as `std::less<>` the
  ordered containers accept `find`, `count`, `lower_bound` and so on with a type other than the key,
  so `std::map<std::string, int, std::less<>>` can be queried with a `std::string_view` without
  building a `std::string`. The unordered containers gained the same for `find`, `count`, `contains`
  and `equal_range` in C++20 (transparent hash and equality).
- **Node handles** *(C++17)*: `extract(key)` detaches a node without copying or moving the element,
  so you can change a `const` key, or move the node to another container with `insert(std::move(nh))`.
  `merge` transfers all nodes whose keys are not yet present.

### `flat_map`, `flat_set` *(C++23)*

`std::flat_map` and `std::flat_set` (and the `flat_multi*` variants) are adapters that keep keys and
values in sorted contiguous containers (a `vector` by default). Lookup is a binary search with good
cache behaviour; insertion and erasure are linear because elements shift. They suit read-mostly
data. Library support is recent (libstdc++ ships them with GCC 15 in `-std=c++23`); check your
standard library before relying on them. Iterators and references are invalidated like the
underlying vectors.

## Unordered associative containers

`std::unordered_set`, `unordered_map` and their `multi` variants hash the key into one of a number of
**buckets**; elements in the same bucket are searched linearly. Lookup, insertion and erasure are
**average constant, worst case linear** (the worst case is all keys colliding). Iteration order is
unspecified and can change after any insertion that triggers a rehash. The standard's interface
(bucket access, `bucket_count`, `max_load_factor`, references staying valid across rehash) forces
a chained hash table; open-addressing tables such as `absl::flat_hash_map` are not conforming
replacements.

The container **rehashes** when `size() > bucket_count() * max_load_factor()` (the default maximum
load factor is 1.0). `reserve(n)` sizes the table up front so that `n` insertions cannot rehash.

A custom key type needs a hash and an equality, passed as template arguments or via a `std::hash`
specialization. Equal keys must have equal hashes.

```cpp title="unordered-key.cpp" showLineNumbers
#include <cstddef>
#include <functional>
#include <iostream>
#include <unordered_map>

struct Point {
    int x, y;
    bool operator==(const Point&) const = default;      // C++20
};

struct PointHash {
    std::size_t operator()(const Point& p) const noexcept {
        std::size_t h = std::hash<int>{}(p.x);
        // boost-style combine; the constant is the 64-bit golden ratio fraction
        return h ^ (std::hash<int>{}(p.y) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2));
    }
};

int main() {
    std::unordered_map<Point, const char*, PointHash> names;
    names.reserve(8);
    names[{0, 0}] = "origin";
    names[{1, 2}] = "p";
    std::cout << names.at({1, 2}) << ' ' << names.contains({3, 3}) << '\n';
}
```

```text
p 0
```

A hash like `x ^ y` maps `{1, 2}` and `{2, 1}` to the same bucket, so combine the fields with
something that is not symmetric.

## Container adapters

`std::stack`, `std::queue` and `std::priority_queue` do not have iterators. They wrap an underlying
sequence container (`deque` by default; `vector` for `priority_queue`) and expose only the
restricted operations. `priority_queue<T>` is a max-heap built with `std::push_heap` and
`pop_heap`: `top()` is constant time, `push` and `pop` are logarithmic. For a min-heap use
`std::priority_queue<T, std::vector<T>, std::greater<T>>`. There is no way to iterate or to
change a priority in place. Since C++23, `stack`, `queue` and `priority_queue` can be
constructed from an iterator pair or a range (`std::from_range`).

## Complexity and invalidation

The tables restate the guarantees the standard gives (n is the number of elements). "Amortized"
means averaged over a sequence of operations, not per call.

| Operation | `vector` | `deque` | `list` | `forward_list` | `map`/`set` | `unordered_*` |
|---|---|---|---|---|---|---|
| Access by index | O(1) | O(1) | n/a | n/a | n/a | n/a |
| `push_back` / `pop_back` | O(1) amortized / O(1) | O(1) | O(1) | n/a | n/a | n/a |
| Insert/erase at front | O(n) | O(1) | O(1) | O(1) | n/a | n/a |
| Insert/erase in the middle | O(n) | O(n) | O(1) given position | O(1) given position | n/a | n/a |
| Find by key | n/a | n/a | n/a | n/a | O(log n) | O(1) average, O(n) worst |
| Insert/erase by key | n/a | n/a | n/a | n/a | O(log n) | O(1) average, O(n) worst |
| `size()` | O(1) | O(1) | O(1) (since C++11) | none | O(1) | O(1) |

(`vector::pop_back` is O(1); `push_back` is amortized O(1). Ordered `insert` with a correct hint
is amortized O(1) when the element goes right before the hint, since C++11.)

**Invalidation** is the rule that bites. A modification invalidates an iterator, pointer or
reference when it can no longer be used (using it is undefined behavior; see
[undefined behavior](../10-error-handling-and-safety/06-undefined-behavior.md)):

| Container | Insertion | Erasure |
|---|---|---|
| `vector` | If the new size exceeds capacity: **all**. Otherwise only those at or after the insertion point (including `end()`) | Those at or after the erased element (including `end()`) |
| `deque` | In the middle: **all** iterators and references. At either end: all iterators, but **references to elements stay valid** | In the middle: all. At either end: only the erased elements (and `end()` when erasing at the back) |
| `list`, `forward_list` | None | Only the erased elements |
| `map`, `set` (and multi) | None | Only the erased elements |
| `unordered_*` | If a **rehash** occurs: all iterators, but pointers and references to elements stay valid. Otherwise none | Only the erased elements |
| `array` | n/a | n/a (iterators stay valid; `swap` swaps elements, so they point to different values afterwards) |

`reserve` on a `vector` or `unordered_*` follows the same rule as insertion: if it reallocates
(or rehashes), the invalidation applies. `clear()` invalidates everything.

A typical bug, and the erase idiom that avoids it:

```cpp title="erase.cpp" showLineNumbers
#include <iostream>
#include <list>
#include <map>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6};
    // WRONG: for (auto it = v.begin(); it != v.end(); ++it) if (*it % 2 == 0) v.erase(it);
    //        erase invalidates `it`, and ++it afterwards is undefined behavior.
    std::erase_if(v, [](int x) { return x % 2 == 0; });      // C++20, returns count removed

    std::map<int, char> m{{1, 'a'}, {2, 'b'}, {3, 'c'}};
    for (auto it = m.begin(); it != m.end();) {              // erase returns the next iterator
        if (it->first == 2) it = m.erase(it);
        else ++it;
    }
    for (int x : v) std::cout << x << ' ';
    std::cout << m.size() << '\n';
}
```

```text
1 3 5 2
```

Before C++20 the vector idiom was `v.erase(std::remove_if(...), v.end())` (see
[algorithms](./algorithms.md)).

## Choosing a container

1. Start with `std::vector`. Contiguity and cache behaviour beat the asymptotics for all but large
   or unusual workloads.
2. Fixed size known at compile time: `std::array`.
3. You need both ends, or stable references while pushing at the ends: `std::deque`.
4. You need iterators and references to survive arbitrary insertion and erasure, or `splice`:
   `std::list`.
5. Lookup by key: `unordered_map` when order does not matter, `map` when you need ordering, range
   queries, or deterministic iteration. `flat_map` *(C++23)* for read-mostly data.

## Related

- [Iterators](./iterators.md): the iterator categories behind these operations
- [Algorithms](./algorithms.md): `erase`/`remove`, `sort`, `lower_bound` over containers
- [Allocators](./allocators.md): the second template parameter, and `std::pmr` containers
- [Strings](./strings.md): `std::basic_string` is a container too, with its own invalidation notes
- [Move semantics](../07-classes-and-oop/copy-and-move-semantics.md): why `noexcept` move matters for `vector` growth

## References

- [Containers library, cppreference](https://en.cppreference.com/w/cpp/container)
- ISO C++ [container.requirements] and the per-container clauses of [containers]
