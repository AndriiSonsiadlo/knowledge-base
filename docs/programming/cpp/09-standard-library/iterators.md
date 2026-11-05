---
id: iterators
title: Iterators
sidebar_label: Iterators
sidebar_position: 2
tags: [c++, stl, iterators, iterator-categories, reverse-iterator, sentinel, iterator-traits, concepts]
---

# Iterators

An **iterator** is an object that refers to an element of a sequence and can be moved to the next
one. It generalizes a pointer: `*it` reads the element, `++it` advances, and `it == end` tells you
when to stop. Containers hand out iterators, algorithms consume them, and neither needs to know
about the other. That separation is the design of the whole standard library, and this page is
the canonical home for iterator categories, the operations on iterators, and writing your own.
The per-container rules for *when* iterators become invalid are in
[Containers](./containers.md#complexity-and-invalidation).

**Prerequisites:** [Pointers](../06-pointers-references-and-smart-pointers/raw-pointers.md),
[pointer arithmetic](../06-pointers-references-and-smart-pointers/pointer-arithmetic.md),
[operator overloading](../02-language-fundamentals/operators/operator-overloading.md).

## Half-open ranges

A sequence is described by two iterators, `[first, last)`: `first` refers to the first element and
`last` to the position **one past the last**. The range is empty when `first == last`, and its
length is `last - first` when that is available. This convention lets "not found" be `last`, lets
empty ranges need no special case, and is what every algorithm and `begin()`/`end()` pair uses.

- Dereferencing `end()` is undefined behavior (it refers to no element).
- Incrementing past `end()`, or decrementing `begin()`, is undefined behavior.
- Comparing iterators into **different** containers is undefined behavior (except for value-initialized
  forward iterators, see below).

```cpp title="loop.cpp" showLineNumbers
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30};
    for (auto it = v.begin(); it != v.end(); ++it)   // prefer != to <: works for every category
        std::cout << *it << ' ';
    std::cout << '\n';
}
```

```text
10 20 30
```

A range-based `for (x : v)` is exactly this loop. Since C++17 the compiler calls `begin()` and `end()`
once and the two results may have different types, which is what allows [sentinels](#sentinels-c20)
(see also [loops](../02-language-fundamentals/control-flow/loops.md)).

## Iterator categories

Categories say which operations an iterator supports, and therefore which algorithms can use it.
They form a hierarchy: each adds to the one before.

<Diagram title="Iterator category hierarchy" caption="Output is a separate branch: it only writes. Contiguous refines random access." accent="blue">
  <DiagramRow>
    <DiagramNode title="Input">read once, single pass</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Forward">multi-pass</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Bidirectional">also <code>--</code></DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Random access">also <code>+n</code>, <code>[]</code>, <code>&lt;</code></DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Contiguous" accent>elements adjacent in memory</DiagramNode>
  </DiagramRow>
</Diagram>

| Category | Extra guarantee | Typical source |
|---|---|---|
| Input | one pass; `*it` may be read once after each `++`; copies may not be independently usable | `std::istream_iterator` |
| Output | write `*it = x` then `++it`, alternating | `std::ostream_iterator`, `std::back_inserter` |
| Forward | multi-pass: copy it, advance both, both still valid and equal | `std::forward_list`, `unordered_*` |
| Bidirectional | `--it` | `std::list`, `set`, `map` |
| Random access | `it + n`, `it - n`, `it[n]`, `<`, `it2 - it1` in O(1) | `std::deque` |
| Contiguous *(C++17 requirement; tag and concept in C++20)* | element addresses are `&*it + n`, adjacent in memory | `std::vector`, `std::array`, `std::string`, pointers |

Multi-pass is the property algorithms like `std::adjacent_find` or `std::is_sorted` rely on, and
the one a single-pass input stream cannot give.

### Legacy tags and C++20 concepts

Before C++20 an iterator announced its category through `std::iterator_traits<It>::iterator_category`,
which is one of the tag types `std::input_iterator_tag`, `output_iterator_tag`, `forward_iterator_tag`,
`bidirectional_iterator_tag`, `random_access_iterator_tag` (and `contiguous_iterator_tag`, *C++20*).
Algorithms dispatch on the tag. C++20 adds **concepts** that check the operations themselves:
`std::input_iterator`, `output_iterator<T>`, `forward_iterator`, `bidirectional_iterator`,
`random_access_iterator`, `contiguous_iterator`, all in `<iterator>`. The C++20 category is
`iterator_concept` (if the type defines it) and may be stronger than the legacy tag. For example,
`std::ranges::views::iota`'s iterators satisfy `random_access_iterator` but their legacy
`iterator_category` is only `input_iterator_tag`, because their `operator*` returns a prvalue, which
the legacy forward requirement (a real reference) cannot allow. Use the concepts in new code
(they are what the [ranges](./ranges.md) library requires).

## Operations on iterators

`<iterator>` provides helpers that work on any category and use the fastest available operation:

| Function | Meaning | Cost |
|---|---|---|
| `std::advance(it, n)` | move `it` by `n` in place | O(1) random access; O(n) otherwise (`n < 0` needs bidirectional) |
| `std::distance(a, b)` | number of steps from `a` to `b` | O(1) random access; O(n) otherwise |
| `std::next(it, n = 1)` | returns a copy advanced by `n` (C++11) | as `advance` |
| `std::prev(it, n = 1)` | returns a copy moved back by `n` (C++11) | as `advance`, bidirectional |

Algorithms assume you can reach `last` from `first`; `std::distance(b, a)` with `a` before `b` on a
non-random-access iterator is undefined behavior. `std::next` does not check against `end()`
either, so `std::next(v.begin(), 5)` on a three-element vector is undefined behavior.

```cpp title="operations.cpp" showLineNumbers
#include <forward_list>
#include <iostream>
#include <iterator>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5};
    auto it = std::next(v.begin(), 2);                 // like v.begin() + 2
    std::cout << *it << ' ' << std::distance(v.begin(), it) << '\n';

    std::forward_list<int> f{1, 2, 3, 4, 5};
    auto jt = f.begin();
    std::advance(jt, 3);                               // walks 3 nodes: O(n)
    std::cout << *jt << '\n';
}
```

```text
3 2
4
```

## `const_iterator` and reverse iterators

Every container has `iterator` and `const_iterator`; `cbegin()`/`cend()` always return the latter,
which lets you read but not modify elements. A `const` container's `begin()` returns a
`const_iterator` too. Convert `iterator` to `const_iterator` implicitly, never the reverse. The keys of `set` and
`map` are always `const`, so even their `iterator` cannot modify a key.

`std::reverse_iterator<It>` wraps a bidirectional iterator and walks backwards; `rbegin()`/`rend()`
return one. It stores the underlying iterator `base()` that is **one past** the element it refers to,
and `*rit` is `*std::prev(rit.base())`. The off-by-one matters when you convert back:

```cpp title="reverse.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <iterator>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5};
    auto r = std::find(v.rbegin(), v.rend(), 4);        // searches from the back
    std::cout << *r << ' ' << *r.base() << '\n';        // base() is one element after
    v.erase(std::prev(r.base()));                       // erase the element r refers to
    for (int x : v) std::cout << x << ' ';
    std::cout << '\n';
}
```

```text
4 5
1 2 3 5 
```

## Adaptor iterators

These adaptors and stream iterators turn an assignment (or a read) into an operation on a container or stream.
Each is created with a helper function (or by CTAD since C++17).

| Iterator | `*it = x` does | Needs |
|---|---|---|
| `std::back_inserter(c)` | `c.push_back(x)` | `push_back` |
| `std::front_inserter(c)` | `c.push_front(x)` | `push_front` (`list`, `deque`, `forward_list`) |
| `std::inserter(c, pos)` | `c.insert(pos, x)`, then advances | `insert` (works for sets) |
| `std::ostream_iterator<T>(os, sep)` | `os << x << sep` | an output stream |
| `std::istream_iterator<T>(is)` | (input) reads `T` on each `++` | `>>`; default-constructed one is the end |
| `std::move_iterator` *(C++11)* | (input side) `*it` yields an rvalue | wraps another iterator |

`back_inserter` is how an algorithm writes into a container that is not big enough yet:
`std::copy` assigns, it does not grow the destination.

```cpp title="inserters.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <iterator>
#include <sstream>
#include <vector>

int main() {
    std::istringstream in("3 1 4 1 5");
    std::vector<int> v;
    std::copy(std::istream_iterator<int>(in), std::istream_iterator<int>(),
              std::back_inserter(v));                       // grows v as needed
    std::copy(v.begin(), v.end(), std::ostream_iterator<int>(std::cout, " "));
    std::cout << '\n';
}
```

```text
3 1 4 1 5 
```

## `iterator_traits`

`std::iterator_traits<It>` exposes five member types: `difference_type`, `value_type`, `pointer`,
`reference` and `iterator_category`. It works for pointers (`int*` is random access, and
contiguous in C++20) and for any class that defines the five member typedefs. Generic code uses
it to name the element type of an arbitrary iterator. Since C++20, the preferred spellings are
`std::iter_value_t<It>`, `std::iter_reference_t<It>` and `std::iter_difference_t<It>`.

## Writing an iterator

A class counts as a forward iterator if it supports the operations in the table above and is
default-constructible and equality-comparable. This example is a read-only forward iterator over
the integers `[0, n)`. In C++20, defining `operator==` is enough (`!=` is rewritten), and
`iterator_concept` tells the concepts what you mean, while `value_type` and `difference_type` are
required.

```cpp title="count-iterator.cpp" showLineNumbers
#include <cstddef>
#include <iostream>
#include <iterator>

class CountIter {
public:
    using iterator_concept  = std::forward_iterator_tag;   // what the C++20 concepts see
    using iterator_category = std::input_iterator_tag;     // what legacy code sees: operator* returns a prvalue
    using value_type        = int;
    using difference_type   = std::ptrdiff_t;

    CountIter() = default;
    explicit CountIter(int v) : v_(v) {}

    int operator*() const { return v_; }
    CountIter& operator++() { ++v_; return *this; }
    CountIter operator++(int) { auto t = *this; ++v_; return t; }
    bool operator==(const CountIter&) const = default;   // C++20: also gives !=

private:
    int v_ = 0;
};

static_assert(std::forward_iterator<CountIter>);

struct Count {
    int n;
    CountIter begin() const { return CountIter(0); }
    CountIter end() const { return CountIter(n); }
};

int main() {
    for (int i : Count{5}) std::cout << i << ' ';
    std::cout << '\n';
}
```

```text
0 1 2 3 4 
```

(Because `operator*` returns a prvalue, the type is a legacy input iterator but a C++20 forward
iterator, exactly like `views::iota`'s. Return a real reference to stored elements if you need it to be a
legacy forward iterator too.)
Deriving from `std::iterator` is deprecated since C++17: define
the five typedefs yourself.

### Sentinels *(C++20)*

The C++20 iterator concepts do not require the end of a range to be an iterator at all: it can be
any **sentinel** type `S` where `it == s` is valid (`std::sentinel_for<S, It>`). A sentinel can
mean "stop at the null terminator" or "stop after n elements" without storing an end position
(`std::default_sentinel` is the standard placeholder). Only the C++20 `std::ranges` algorithms
and range-for accept mixed iterator/sentinel pairs; the classic `std::sort(first, last)` requires
both arguments to have the same type (`std::common_iterator` bridges the gap). See [Ranges](./ranges.md).

## Common mistakes

- **Using an invalidated iterator.** See the [invalidation table](./containers.md#complexity-and-invalidation);
  `erase` returns the next valid iterator, use it.
- **Dereferencing `end()`**, for example after a failed `find`. Compare against `end()` first.
- **Mixing containers**: `std::copy(a.begin(), b.end(), out)` is undefined behavior.
- **Writing past a destination**: `std::copy(src.begin(), src.end(), dst.begin())` with an empty
  `dst` overwrites memory that does not exist. Resize `dst` or use `back_inserter`.
- **Relying on `<` for iterators**: only random access iterators have it. Use `!=`.
- **Value-initialized iterators**: since C++14, two value-initialized forward iterators of the same type
  compare equal, otherwise a default-constructed iterator holds an unspecified value.

## Related

- [Containers](./containers.md): which iterator each container provides, and when they are invalidated
- [Algorithms](./algorithms.md): the iterator-pair algorithms that use these categories
- [Ranges](./ranges.md): C++20 views and range algorithms built on iterators and sentinels
- [Pointer arithmetic](../06-pointers-references-and-smart-pointers/pointer-arithmetic.md): raw pointers are contiguous iterators

## References

- [Iterator library, cppreference](https://en.cppreference.com/w/cpp/iterator)
- ISO C++ [iterator.requirements], [iterator.concepts]
