---
id: ranges
title: Ranges Library
sidebar_label: Ranges
sidebar_position: 4
tags: [c++, c++20, c++23, ranges, views, pipelines, lazy-evaluation, projections, sentinels]
---

# Ranges Library

A **range** is anything you can iterate with `begin()` and `end()`. C++20 turns that informal
idea into concepts, adds algorithms that take the whole range instead of an iterator pair, and adds
**views**: lazy, non-owning adaptors that you chain with `|` to build a pipeline without writing
intermediate containers. This page is the canonical home for `<ranges>`, `std::ranges::` algorithms,
and the C++23 additions. The underlying iterator machinery is on [Iterators](./iterators.md) and
the classic iterator-pair algorithms are on [Algorithms](./algorithms.md).

**Prerequisites:** [Iterators](./iterators.md), [Algorithms](./algorithms.md),
[concepts](../08-templates-and-metaprogramming/concepts-and-requires.md),
[lambdas](../07-classes-and-oop/lambdas.md).

## Range concepts

`std::ranges::range<R>` holds when `std::ranges::begin(r)` and `std::ranges::end(r)` are valid. The
end may be a [sentinel](./iterators.md#sentinels-c20) of a different type than the iterator. Refinements
mirror the iterator categories: `input_range`, `forward_range`, `bidirectional_range`,
`random_access_range`, `contiguous_range`. Orthogonal ones:

| Concept | Meaning |
|---|---|
| `sized_range` | `ranges::size(r)` is available in O(1) |
| `common_range` | iterator and sentinel have the same type (needed to call legacy iterator-pair APIs) |
| `view` | cheap to copy/move (O(1)), and non-owning in the typical case |
| `borrowed_range` | iterators stay valid after the range object dies (`string_view`, `span`, `subrange`) |

`std::ranges::begin`/`end`/`size`/`empty`/`data` are customization point objects: they work on
containers, C arrays and anything with member or free `begin`/`end`.

## Range algorithms

`std::ranges::sort`, `find`, `copy`, `count_if` and so on live in `<algorithm>` and mirror the classic
ones, with three differences:

1. They take a range (`std::ranges::sort(v)`) or an iterator/sentinel pair.
2. They accept **projections**: a callable applied to each element before the comparison or predicate.
3. They are constrained with concepts, so misuse fails with a readable "constraint not satisfied"
   message rather than deep template errors, and they are function objects, so ADL does not apply.

They return richer results (for example `ranges::find` returns an iterator, and `ranges::copy`
returns `{in, out}`), and passing a temporary range to an algorithm that returns an iterator yields
`std::ranges::dangling` instead of a dangling iterator, unless the range is a `borrowed_range`.

```cpp title="projection.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

struct Person { std::string name; int age; };

int main() {
    std::vector<Person> p{{"Ann", 30}, {"Bob", 25}, {"Cy", 41}};

    std::ranges::sort(p, std::less{}, &Person::age);         // projection: member pointer
    auto it = std::ranges::find(p, "Cy", &Person::name);     // compares p[i].name == "Cy"

    for (const auto& x : p) std::cout << x.name << ' ';
    std::cout << '\n' << (it != p.end() ? it->age : -1) << '\n';
}
```

```text
Bob Ann Cy 
41
```

The projection changes what is compared, not what is moved: the elements stay whole `Person`s.

## Views

A **view** describes a transformation of another range and does nothing until you iterate it. It
stores the underlying range by reference or by cheap copy, so building a view does not
copy elements. Elements are produced on demand, one at a time, as you pull from the end of the pipeline.

<Diagram title="A lazy pipeline: one element flows through at a time" accent="blue">
  <DiagramRow>
    <DiagramNode title="vector">1 2 3 4 5 6</DiagramNode>
    <DiagramArrow direction="right" label="filter: even" />
    <DiagramNode title="filter view" accent>no storage</DiagramNode>
    <DiagramArrow direction="right" label="transform: x*x" />
    <DiagramNode title="transform view" accent>no storage</DiagramNode>
    <DiagramArrow direction="right" label="for loop pulls" />
    <DiagramNode title="4, 16, 36" />
  </DiagramRow>
</Diagram>

```cpp title="pipeline.cpp" showLineNumbers
#include <iostream>
#include <ranges>
#include <vector>

namespace rv = std::views;       // std::views is an alias for std::ranges::views

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6};

    auto squares = v | rv::filter([](int x) { return x % 2 == 0; })
                     | rv::transform([](int x) { return x * x; });

    for (int x : squares) std::cout << x << ' ';
    std::cout << '\n';

    for (int x : rv::iota(1) | rv::take(5)) std::cout << x << ' ';   // infinite, cut by take
    std::cout << '\n';
}
```

```text
4 16 36 
1 2 3 4 5 
```

### The standard views

| Adaptor (`std::views::`) | Produces | Since |
|---|---|---|
| `all`, `ref_view`, `owning_view` | view of a whole range | C++20 (`owning_view`: C++20, P2415) |
| `filter(pred)` | elements satisfying `pred` | C++20 |
| `transform(f)` | `f(element)` | C++20 |
| `take(n)`, `take_while(p)`, `drop(n)`, `drop_while(p)` | prefix / suffix | C++20 |
| `reverse` | reversed (bidirectional input) | C++20 |
| `elements<N>`, `keys`, `values` | N-th tuple member (map keys/values) | C++20 |
| `split(delim)`, `lazy_split`, `join` | split into subranges / flatten | C++20 |
| `common` | adapts to equal iterator and sentinel types | C++20 |
| `counted(it, n)`, `subrange` | a window from an iterator and a count | C++20 |
| `iota(a[, b])`, `empty<T>`, `single(x)` | factories (no underlying range) | C++20 |
| `istream_view<T>` | values read from a stream | C++20 |
| `zip`, `zip_transform`, `enumerate`, `adjacent`, `pairwise`, `chunk`, `slide`, `stride`, `chunk_by`, `cartesian_product`, `join_with`, `repeat`, `as_rvalue`, `as_const` | tuples of neighbours or parallel ranges, windows, strides, and so on | C++23 |

`std::ranges::to<Container>()` *(C++23)* is the terminal step that materializes a pipeline:

```cpp title="to-and-zip.cpp"
// compile: g++ -std=c++23
#include <iostream>
#include <map>
#include <ranges>
#include <string>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 4, 5, 6};
    auto evens = v | std::views::filter([](int x) { return x % 2 == 0; })
                   | std::ranges::to<std::vector>();           // C++23

    std::vector<std::string> names{"a", "b", "c"};
    for (auto [i, s] : std::views::enumerate(names))           // C++23
        std::cout << i << s << ' ';
    for (auto [x, y] : std::views::zip(v, names))              // C++23, stops at the shorter
        std::cout << x << y << ' ';
    std::cout << evens.size() << '\n';
}
```

```text
0a 1b 2c 1a 2b 3c 3
```

These C++23 pieces were compiled here with g++ 15.2 and clang++ 21.1 (using libstdc++) at `-std=c++23`. Older
libraries lack some of them; test the feature-test macros (`__cpp_lib_ranges_to_container`,
`__cpp_lib_ranges_zip`, `__cpp_lib_ranges_enumerate`) before relying on them.

## Laziness, caching and lifetime

Lazy has consequences you need to know:

- **Evaluation happens on every traversal.** Iterating a `transform` view twice calls the function
  twice per element. Materialize with `ranges::to` (or a loop) if the work is expensive or has side effects.
- **`filter` caches `begin()`.** The first call to `begin()` scans to the first match and stores
  it, so `filter` is not a `const`-iterable view. Modifying an element through the view so that it
  no longer satisfies the predicate is undefined behavior. `drop_while` caches in the same way. Do
  not take a `filter` view by `const&`: take it by value or by forwarding reference.
- **Views do not own.** A view over a vector that is destroyed, reallocated or resized dangles, the
  same hazard as [`string_view`](./strings.md) or [`span`](./containers.md#complexity-and-invalidation).
  A pipeline that starts from an rvalue container is a different case: since P2415 (applied to
  C++20), `views::all` wraps an rvalue container in an `owning_view`, which moves the container
  into the view, while an lvalue becomes a `ref_view`. The returned view is then self-contained.
```cpp title="dangling.cpp"
// fragment: what not to do (needs <ranges> and <vector>)
auto bad() {
    std::vector<int> v{1, 2, 3};
    return v | std::views::transform([](int x) { return x + 1; });   // refers to v, which is destroyed
}
```

- **Modifying a pipeline's source while iterating it** follows the container invalidation rules
  ([Containers](./containers.md#complexity-and-invalidation)).

## Writing your own range

A class with `begin()` and `end()` is already a range. To make it work with `|` and the view
concepts, derive from `std::ranges::view_interface` and make it cheap to copy. Since C++23
`std::generator` (`<generator>`) is the easiest way to produce a lazy range with
[coroutines](../11-concurrency-and-memory-model/09-coroutines.md).

## When to use which

- Use `std::ranges::` algorithms in new C++20 code for the call syntax, projections and diagnostics.
- Use views to express "filter then map then take" and iterate it once. Use a plain loop or an
  algorithm when the pipeline is traversed repeatedly or when debugging matters.
- Pass ranges as `std::ranges::input_range auto&&` (or constrained templates), and use `std::span`
  for contiguous data, rather than taking `const std::vector<T>&`.
- There is no free lunch in speed: pipelines of simple views are usually inlined well by optimizers,
  but this depends on the compiler, and some adaptors (`join`, `split`, `filter`) add overhead.
  Measure before assuming.

## Related

- [Iterators](./iterators.md): iterator categories, sentinels, and `iter_value_t`
- [Algorithms](./algorithms.md): the classic algorithms the `ranges::` versions mirror
- [Concepts and requires](../08-templates-and-metaprogramming/concepts-and-requires.md): how `std::ranges::range` and friends are written
- [Strings](./strings.md): `string_view`, a borrowed range, and `views::split` on text

## References

- [Ranges library, cppreference](https://en.cppreference.com/w/cpp/ranges)
- ISO C++ [ranges]
