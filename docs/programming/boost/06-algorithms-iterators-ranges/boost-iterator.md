---
id: boost-iterator
title: Boost.Iterator
sidebar_label: Boost.Iterator
sidebar_position: 3
tags: [c++, boost, iterator, adaptor, facade]
---

# Boost.Iterator

`Boost.Iterator` provides tools for **building and adapting iterators** without the boilerplate that
the standard iterator interface demands. Its two core pieces are `iterator_facade` — which generates
a complete iterator from a handful of primitives — and `iterator_adaptor` — which wraps an existing
iterator and overrides specific operations.

:::info The problem it solves
Writing a correct STL iterator by hand means implementing five nested types, up to seven operators,
and getting the const/non-const interplay right. A single oversight causes hard-to-diagnose
compilation failures. `iterator_facade` reduces this to three or four simple functions; the library
synthesises the rest.
:::

## iterator_facade: build a custom iterator

You inherit from `iterator_facade` and supply a few core operations. The library generates all the
operators (`++`, `--`, `*`, `->`, `==`, `!=`, `<`, `+=`, ...) from those primitives.

```cpp showLineNumbers title="node_iterator.cpp"
#include <boost/iterator/iterator_facade.hpp>
#include <iostream>

struct Node {
    int value;
    Node* next;
};

class NodeIterator
    : public boost::iterator_facade<NodeIterator, int, boost::forward_traversal_tag>
{
public:
    NodeIterator() : node_(nullptr) {}
    explicit NodeIterator(Node* n) : node_(n) {}

private:
    friend class boost::iterator_core_access;

    void increment()             { node_ = node_->next; }
    bool equal(const NodeIterator& other) const { return node_ == other.node_; }
    int& dereference() const     { return node_->value; }

    Node* node_;
};

int main() {
    Node c{3, nullptr};
    Node b{2, &c};
    Node a{1, &b};

    for (NodeIterator it(&a); it != NodeIterator(); ++it) {
        std::cout << *it << " ";  // 1 2 3
    }
    std::cout << "\n";
}
```

The three functions — `increment`, `equal`, `dereference` — are all you need for a forward iterator.
Add `decrement` for bidirectional, plus `advance` and `distance_to` for random access.

:::tip Traversal tags
Boost.Iterator uses its own traversal tag hierarchy (`incrementable`, `single_pass`, `forward`,
`bidirectional`, `random_access`) that is finer-grained than the standard iterator categories. The
library maps them to `std::iterator_traits` categories automatically.
:::

## iterator_adaptor: wrap and customise

When you want to modify the behaviour of an existing iterator — skip certain elements, transform
values, change traversal — `iterator_adaptor` lets you override just the parts that differ:

```cpp showLineNumbers title="stride_iterator.cpp"
#include <boost/iterator/iterator_adaptor.hpp>
#include <vector>
#include <iostream>

template <typename BaseIter>
class StrideIterator
    : public boost::iterator_adaptor<StrideIterator<BaseIter>, BaseIter>
{
public:
    StrideIterator(BaseIter it, int stride)
        : StrideIterator::iterator_adaptor_(it), stride_(stride) {}

private:
    friend class boost::iterator_core_access;
    void increment() { std::advance(this->base_reference(), stride_); }
    int stride_;
};

int main() {
    std::vector<int> v{0, 1, 2, 3, 4, 5, 6, 7, 8, 9};

    StrideIterator begin(v.begin(), 3);
    StrideIterator end(v.end(), 3);

    for (auto it = begin; it.base() < end.base(); ++it) {
        std::cout << *it << " ";  // 0 3 6 9
    }
    std::cout << "\n";
}
```

## Ready-made iterator adaptors

Boost.Iterator ships several commonly needed adaptors out of the box:

| Adaptor | Purpose | Example use |
|---------|---------|-------------|
| `counting_iterator` | Generates integers: 0, 1, 2, ... | Loop without a container |
| `transform_iterator` | Applies a function on dereference | Read-only projection |
| `filter_iterator` | Skips elements that fail a predicate | Iterate matching items |
| `zip_iterator` | Iterates multiple ranges in lockstep | Parallel traversal |
| `reverse_iterator` | Reverses traversal direction | Backward iteration |
| `indirect_iterator` | Dereferences through pointers | Iterate `vector<T*>` as `T&` |

```cpp showLineNumbers title="counting_zip.cpp"
#include <boost/iterator/counting_iterator.hpp>
#include <boost/iterator/transform_iterator.hpp>
#include <vector>
#include <iostream>

int main() {
    // counting_iterator: generate integers without a container
    boost::counting_iterator<int> from(0), to(5);
    for (auto it = from; it != to; ++it) {
        std::cout << *it << " ";  // 0 1 2 3 4
    }
    std::cout << "\n";

    // transform_iterator: project on the fly
    std::vector<int> v{1, 2, 3, 4};
    auto square = [](int n) { return n * n; };
    auto begin = boost::make_transform_iterator(v.begin(), square);
    auto end   = boost::make_transform_iterator(v.end(), square);
    for (auto it = begin; it != end; ++it) {
        std::cout << *it << " ";  // 1 4 9 16
    }
    std::cout << "\n";
}
```

## filter_iterator

Wraps an existing iterator and skips elements that do not satisfy a predicate:

```cpp showLineNumbers title="filter_iter.cpp"
#include <boost/iterator/filter_iterator.hpp>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6, 7, 8};
    auto is_even = [](int n) { return n % 2 == 0; };

    auto begin = boost::make_filter_iterator(is_even, v.begin(), v.end());
    auto end   = boost::make_filter_iterator(is_even, v.end(), v.end());

    for (auto it = begin; it != end; ++it) {
        std::cout << *it << " ";  // 2 4 6 8
    }
    std::cout << "\n";
}
```

:::warning filter_iterator needs the end
`make_filter_iterator` requires the **end** iterator as a third argument so it knows where to stop
skipping. Forgetting it is a compilation error — not a silent bug.
:::

## See also

- <Icon icon="lucide:repeat" inline /> [Boost.Range](./boost-range.md) — range adaptors built on top of these iterators.
- <Icon icon="lucide:search" inline /> [Boost.Algorithm](./boost-algorithm.md) — algorithms that consume iterators.
- <Icon icon="lucide:archive" inline /> [BOOST_FOREACH](./boost-foreach.md) — legacy iteration macro.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
