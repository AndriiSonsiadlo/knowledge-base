---
id: custom-allocators-and-json-types
title: Custom allocators and JSON types
sidebar_label: Custom types
sidebar_position: 2
tags: [c++, nlohmann-json, allocators, basic-json]
---

# Custom allocators and JSON types

`json` isn't a concrete class — it's `using json = basic_json<>;`, one particular instantiation of
a ten-parameter class template. Every default you've relied on so far (sorted object keys,
`std::string`, `int64_t`) is a template default, and changing the instantiation is how you reach for
something else without leaving the library.

## The basic_json parameter list

```cpp showLineNumbers
template <
    template <typename U, typename V, typename... Args> class ObjectType = std::map,
    template <typename U, typename... Args> class ArrayType = std::vector,
    class StringType = std::string,
    class BooleanType = bool,
    class NumberIntegerType = std::int64_t,
    class NumberUnsignedType = std::uint64_t,
    class NumberFloatType = double,
    template <typename U> class AllocatorType = std::allocator,
    template <typename T, typename SFINAE = void> class JSONSerializer = adl_serializer,
    class BinaryType = std::vector<std::uint8_t>
>
class basic_json;

using json = nlohmann::basic_json<>;   // every parameter left at its default
```

Every parameter you've used so far — the map for objects, the vector for arrays, `int64_t` for
signed numbers — is one of these defaults. `ordered_json` is the library's own example of overriding
just one.

## Ready-made alternatives

| Alias | ObjectType | Key order | Lookup |
|---|---|---|---|
| `json` | `std::map` | Sorted by key | `O(log n)` |
| `ordered_json` | `nlohmann::ordered_map` (insertion-order vector-backed) | Insertion order | `O(n)` linear scan |

`ordered_json` trades lookup speed for insertion-order iteration — worth it whenever the output
needs to match a human-authored or externally-specified key order, not worth it for a hot lookup
path over a large object.

## Rolling your own

Any `ObjectType` that models enough of `std::map`'s interface (constructible, `operator[]`,
iteration, `find`) can stand in for it — for example, a sorted-vector-backed map for better cache
locality on small objects:

```cpp showLineNumbers title="my_json.hpp"
template <typename K, typename V, typename... Args>
using SortedVectorMap = /* your own std::map-compatible adaptor over a sorted std::vector */;

using compact_json = nlohmann::basic_json<
    SortedVectorMap,       // ObjectType
    std::vector,            // ArrayType
    std::string,             // StringType
    bool,                     // BooleanType
    std::int64_t,              // NumberIntegerType
    std::uint64_t,               // NumberUnsignedType
    double,                        // NumberFloatType
    std::allocator,                  // AllocatorType
    nlohmann::adl_serializer            // JSONSerializer
>;
```

The constraint is entirely structural — `basic_json` doesn't check against a named concept, it just
instantiates as if `ObjectType` were `std::map`, so anything that supports the same operations
compiles.

## Custom allocators

`AllocatorType` is where you'd expect to plug in an arena or pool allocator, and it's used — but
only for the containers `basic_json` itself constructs (the object map's nodes, the array vector,
the string buffer for each string value). It doesn't intercept every allocation the library makes
internally.

:::note[The allocator parameter doesn't give full arena control]
Internal strings and map nodes dominate a typical document's allocation count, and `AllocatorType`
does cover those. But it's not a hook into *every* allocation the library performs, and depending on
`StringType`/`ObjectType` choices, some allocations may happen through paths the custom allocator
never sees. If you need genuinely total control over where every byte comes from, budget time to
verify the specific allocation pattern for your instantiation rather than assuming the parameter is
a complete guarantee.
:::

## Costs

Each distinct `basic_json` instantiation is its own class, generated fresh by the compiler — the
same template-instantiation cost multiplied by however many distinct instantiations your project
uses.

:::danger[Different basic_json instantiations don't implicitly convert]
`json` and `ordered_json` are two unrelated types as far as the compiler is concerned — there's no
implicit conversion between them (you convert explicitly by round-tripping through `dump()`/`parse()`
or by constructing one from the other's elements). Mixing instantiations across a codebase means
every boundary between them needs an explicit, deliberate conversion; it isn't free the way passing
a `json` around normally is.
:::

## See also

- <Icon icon="lucide:sigma" inline /> [Number handling and precision](./number-handling-and-precision.md) — the `NumberIntegerType`/`NumberUnsignedType`/`NumberFloatType` parameters in practice.
- <Icon icon="lucide:gauge" inline /> [Performance and best practices](./performance-and-best-practices.md) — where a custom instantiation actually pays off.
- <Icon icon="lucide:box" inline /> [The JSON value type](../01-basics/the-json-value-type.md) — `json` vs `ordered_json` from the value-type side.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
