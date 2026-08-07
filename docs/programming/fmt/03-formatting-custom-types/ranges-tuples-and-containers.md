---
id: ranges-tuples-and-containers
title: Ranges, tuples and containers
sidebar_label: Ranges
sidebar_position: 3
tags: [c++, fmt, custom-types, ranges]
---

# Ranges, tuples and containers

Printing a container is the single most common debugging need in C++, and it's the one thing the
standard library never made easy — `std::cout << vec` doesn't compile without writing your own loop.
`fmt/ranges.h` makes it one call.

## fmt/ranges.h

```cpp showLineNumbers
#include <fmt/ranges.h>

fmt::print("{}\n", std::vector{1, 2, 3});                 // [1, 2, 3]
fmt::print("{}\n", std::map<std::string, int>{{"a", 1}}); // {"a": 1}
fmt::print("{}\n", std::vector<std::vector<int>>{{1, 2}, {3}}); // [[1, 2], [3]]
```

Sequence containers print bracket-wrapped and comma-separated; associative containers print as
brace-wrapped `key: value` pairs; nesting works automatically because each element is formatted with
the same machinery, recursively.

## Tuples and pairs

```cpp
fmt::print("{}\n", std::make_pair(1, "a"));         // (1, "a")
fmt::print("{}\n", std::make_tuple(1, 2.5, "x"));   // (1, 2.5, "x")
```

`std::pair` inside a map prints the same way a directly-formatted pair would — no special-casing
needed.

## fmt::join

`fmt::join` gives you a custom separator instead of the default `, `, and applies a spec to every
element rather than the container as a whole.

```cpp showLineNumbers
fmt::print("{}\n", fmt::join(v, " | "));                     // 1 | 2 | 3
fmt::print("{}\n", fmt::format("{:.2f}", fmt::join(v, ", "))); // 1.50, 2.75, 3.00
```

## Lifetime of join

:::danger[fmt::join stores references — never return or store the result of fmt::join; format it immediately]
```cpp
auto bad() { return fmt::join(local_vector, ", "); }  // dangling — local_vector is destroyed
std::string good() { return fmt::format("{}", fmt::join(local_vector, ", ")); }  // fine
```
`fmt::join` wraps a reference to the range, not a copy. It's meant to be consumed inline by a
`fmt::format`/`fmt::print` call and nothing else — see
[Common pitfalls](../06-performance-and-best-practices/common-pitfalls.md) for the general pattern
this belongs to.
:::

## Element specs

The spec after the colon applies to each *element*, not the container as a whole — `{:.2f}` on a
`std::vector<double>` formats every element with two decimal places; there is no separate spec for
the brackets or separators.

## Strings inside containers

:::note[Container elements of string type are printed quoted — use fmt::join if you want them raw]
```cpp
fmt::print("{}\n", std::vector<std::string>{"a", "b"});  // ["a", "b"]
fmt::print("{}\n", fmt::join(std::vector<std::string>{"a", "b"}, ", "));  // a, b
```
Newer fmt escapes and quotes string elements inside a container by default (the same debug
presentation as `{:?}`), which is unambiguous for logging but not what you want if you're building a
plain comma-separated value list — use `fmt::join` for that instead.
:::

## Your own range types

Any type with `begin`/`end` iterators satisfying the range concept is formatted automatically once
`<fmt/ranges.h>` is included — no extra work needed. A type that is *not* a range (a scalar wrapper,
say) needs its own [formatter specialization](./formatter-specialization.md) instead.

## See also

- <Icon icon="lucide:shapes" inline /> [formatter specialization](./formatter-specialization.md) — what a non-range custom type needs instead.
- <Icon icon="lucide:clock" inline /> [Chrono and time formatting](./chrono-and-time-formatting.md) — the other major `fmt/*.h` extension header.
- <Icon icon="lucide:triangle-alert" inline /> [Common pitfalls](../06-performance-and-best-practices/common-pitfalls.md) — the lifetime hazard shared by `fmt::join` and friends.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
