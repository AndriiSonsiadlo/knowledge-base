---
id: boost-container
title: Boost.Container
sidebar_label: Boost.Container
sidebar_position: 1
tags: [c++, boost, containers, container]
---

# Boost.Container

`Boost.Container` provides **STL-compatible containers** that go beyond what the standard library
ships. The API mirrors `std::vector`, `std::map`, and friends, so switching is usually a drop-in
rename — but the implementations add features the standard either cannot guarantee or does not offer
at all: incomplete-type support, `stable_vector`, `flat_map`/`flat_set`, `small_vector`,
`static_vector`, and a scoped-allocator model that propagates allocators to nested containers.

:::info The problem it solves
Standard containers are deliberately minimal — the committee specifies *interfaces*, not
implementation strategies. If you need a vector that never invalidates pointers on growth, a sorted
flat container backed by a contiguous array, or a small-buffer-optimised vector that avoids the heap
for short sequences, the standard has no answer. `Boost.Container` fills every one of those gaps
with battle-tested, allocator-aware implementations.
:::

## Containers with incomplete types

Standard containers require `T` to be a complete type at the point of instantiation. Boost relaxes
this, which lets you build recursive data structures naturally:

```cpp showLineNumbers title="recursive_tree.cpp"
#include <boost/container/vector.hpp>

struct TreeNode {
    int value;
    boost::container::vector<TreeNode> children;  // TreeNode is incomplete here — OK
};

int main() {
    TreeNode root{1, {}};
    root.children.push_back({2, {}});
    root.children.push_back({3, {{4, {}}}});
}
```

:::warning std::vector and incomplete types
Some standard library implementations happen to accept incomplete types, but the standard does **not**
guarantee it. Relying on that is undefined behaviour. `boost::container::vector` guarantees it.
:::

## stable_vector — pointer stability on growth

`boost::container::stable_vector<T>` provides the interface of `std::vector` but guarantees that
**references and iterators to existing elements are never invalidated** by insertions or erasures
(except for the erased element). Internally it uses an indirection layer — each element is
heap-allocated, but indexed contiguously.

```cpp showLineNumbers title="stable_vector.cpp"
#include <boost/container/stable_vector.hpp>
#include <cassert>

int main() {
    boost::container::stable_vector<int> sv = {10, 20, 30};
    int& ref = sv[1];
    sv.push_back(40);   // reallocation may happen internally
    assert(ref == 20);   // reference is still valid
}
```

## flat_map and flat_set — sorted, contiguous storage

These are **associative containers backed by a sorted vector** rather than a tree. Lookups are
binary-search (`O(log n)`), iteration is cache-friendly, and memory overhead per element is near
zero. The trade-off: insertion into the middle is `O(n)`.

```cpp showLineNumbers title="flat_map.cpp"
#include <boost/container/flat_map.hpp>
#include <string>
#include <iostream>

int main() {
    boost::container::flat_map<int, std::string> fm;
    fm.emplace(3, "three");
    fm.emplace(1, "one");
    fm.emplace(2, "two");

    for (auto& [k, v] : fm)
        std::cout << k << " -> " << v << "\n";  // prints in sorted order
}
```

:::tip When to prefer flat containers
Use `flat_map`/`flat_set` when the container is **built once and queried many times** (lookup
tables, configuration maps, static dictionaries). The contiguous memory layout gives much better
cache performance than `std::map`'s node-based tree. C++23 adopted `std::flat_map` — the Boost
version works on C++11 and later.
:::

## small_vector — small-buffer optimisation

`boost::container::small_vector<T, N>` stores up to `N` elements in-place (on the stack or inside
the object) and only allocates from the heap when the size exceeds `N`. This eliminates allocation
overhead for the common case where sequences are short.

```cpp showLineNumbers title="small_vector.cpp"
#include <boost/container/small_vector.hpp>

void process(boost::container::small_vector<int, 8>& data) {
    // up to 8 ints live inline — no heap allocation
    data.push_back(42);
}

int main() {
    boost::container::small_vector<int, 8> sv = {1, 2, 3};
    process(sv);  // still inline
}
```

## static_vector — fixed capacity, no heap ever

`boost::container::static_vector<T, N>` is a vector with a **compile-time maximum capacity**. It
never allocates from the heap — all storage is embedded. Exceeding the capacity is a precondition
violation (undefined behaviour in release, assertion in debug).

```cpp showLineNumbers title="static_vector.cpp"
#include <boost/container/static_vector.hpp>

int main() {
    boost::container::static_vector<double, 4> sv;
    sv.push_back(1.0);
    sv.push_back(2.0);
    sv.push_back(3.0);
    sv.push_back(4.0);
    // sv.push_back(5.0);  // precondition violation — capacity is 4
}
```

:::danger Do not exceed the capacity of static_vector
Unlike `std::vector`, `static_vector` will **not** grow. Pushing beyond capacity is undefined
behaviour (or an assertion failure in debug builds). Always check `size() < capacity()` or design
your logic so overflow is impossible.
:::

## Boost.Container versus std containers

| Feature | `boost::container` | `std` containers |
|---------|-------------------|------------------|
| Incomplete-type support | guaranteed | not guaranteed |
| `stable_vector` | yes | no equivalent |
| `flat_map` / `flat_set` | yes (C++03+) | `std::flat_map` (C++23) |
| `small_vector` | yes | no equivalent |
| `static_vector` | yes | no equivalent |
| Scoped allocator propagation | built-in | `std::scoped_allocator_adaptor` |
| API compatibility | mirrors `std` | — |

## See also

- <Icon icon="lucide:boxes" inline /> [Boost.Intrusive](./boost-intrusive.md) — containers where hooks live inside the objects.
- <Icon icon="lucide:repeat" inline /> [Boost.CircularBuffer](./boost-circular-buffer.md) — fixed-capacity ring buffer.
- <Icon icon="lucide:search" inline /> [Boost.Unordered](./boost-unordered.md) — high-performance hash containers.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — lineage of `std::flat_map` and others.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
