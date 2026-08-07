---
id: design-philosophy
title: Design philosophy
sidebar_label: Design philosophy
sidebar_position: 3
tags: [c++, nlohmann-json, design, philosophy, stl]
---

# Design philosophy

The project's own README states its goals plainly: intuitive syntax, trivial integration, and
serious testing. Each of those is a real design choice, not a slogan, and each one trades something
away to get it.

## "Intuitive syntax" means implicit conversions

Reading a string field out of a `json` object looks like reading a string out of anything else:

```cpp
json j = {{"name", "ada"}};
std::string s = j["name"];   // implicit conversion, no get<T>() in sight
```

That works because `json` defines an implicit conversion operator template that calls `get<T>()`
internally, deduced from the type you're assigning into.

:::danger[Implicit conversion is a footgun]
The conversion is a template deduced from the *target* of the assignment, and C++ overload
resolution doesn't always have an unambiguous target to deduce from. `auto s = j["name"];` does not
give you a `std::string` — it gives you a `json`, because `auto` has nothing to deduce the
conversion against. Passing a `json` directly to an overloaded function can pick the wrong overload
for the same reason. The explicit form, `j["name"].get<std::string>()`, always does what it says
and is the safer default in anything other than a direct, typed assignment. See
[Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md) for
the full set of extraction methods and when each is appropriate.
:::

## STL-like semantics

`json` is a value type: copying it deep-copies the whole document, `operator==` compares by value
recursively, and it composes with STL algorithms the same way a `std::vector` or `std::map` does.
There's no reference-counted sharing under the hood and no copy-on-write — a `json j2 = j1;`
duplicates every string, array, and object in `j1`.

| STL concept | nlohmann/json equivalent |
|---|---|
| Value semantics, deep copy on assignment | `json` copy constructor / `operator=` |
| `std::map`-style keyed access | `operator[](key)`, `.at(key)`, `.find(key)` |
| `std::vector`-style indexed access | `operator[](index)`, `.at(index)`, `.push_back()` |
| Range-based iteration | `begin()`/`end()`, range-for, `.items()` |
| Structural equality | `operator==` / `operator!=` |
| Ordering (for use in ordered containers) | `operator<` (orders by `value_t` first, then value) |

## basic_json is a template

`json` isn't a concrete class — it's an alias, `using json = basic_json<>;`, for a class template
with ten parameters covering the object type, array type, string type, number types, allocator, and
serializer. The default instantiation uses `std::map` for objects (so keys come out sorted
alphabetically on iteration, regardless of insertion order) and `std::vector`, `std::string`, and
the usual built-in number types for everything else.

The library ships one alternative instantiation out of the box, `ordered_json`, which swaps in an
insertion-order-preserving map. Reaching further than that — a different map implementation, a
custom allocator, a `long double` for floats — means instantiating `basic_json` yourself. See
[Custom allocators and JSON types](../05-numbers-memory-and-performance/custom-allocators-and-json-types.md)
for the full parameter list and worked examples.

## The cost of the design

All of this convenience lives in one header of roughly 25,000 lines of heavily templated C++. That
has two concrete costs: every translation unit that includes `json.hpp` pays a real compile-time
tax, and the resulting object code — while it strips down reasonably well with LTO — is larger than
a hand-rolled parser would produce for the same functionality.

:::tip[Use json_fwd.hpp in headers]
If a header only needs to name `nlohmann::json` as a type — a member, a parameter — include
`<nlohmann/json_fwd.hpp>` instead of the full header, and push the full include down into the `.cpp`
file that actually calls methods on it. This is the single biggest lever for keeping build times
sane in a project with many headers touching JSON types.
:::

## See also

- <Icon icon="lucide:book-open" inline /> [What is nlohmann/json?](./what-is-nlohmann-json.md) — the problem this design was built to solve.
- <Icon icon="lucide:scale" inline /> [Comparison with alternatives](./comparison-with-alternatives.md) — how these trade-offs compare to other libraries' choices.
- <Icon icon="lucide:box" inline /> [The JSON value type](../01-basics/the-json-value-type.md) — what `basic_json` actually stores at runtime.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
