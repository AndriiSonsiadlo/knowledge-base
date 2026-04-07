---
id: boost-variant
title: Boost.Variant
sidebar_label: Boost.Variant
sidebar_position: 5
tags: [ c++, boost, variant, union ]
---

# Boost.Variant

`boost::variant<T1, T2, ...>` is a **type-safe, discriminated union**: a single object that holds a
value of exactly one of a fixed list of types, and always knows which one it currently holds. It is the
type-safe replacement for raw `union` and for the "tagged struct" idiom, and it directly inspired
C++17's `std::variant`.

:::info Variant versus union
A C `union` overlaps several types in one storage slot but tracks *nothing* — read the wrong member and
you get undefined behaviour. A `variant` adds the missing discriminator and enforces correct access,
running constructors and destructors properly for non-trivial types like `std::string`.
:::

## Declaring and assigning

```cpp showLineNumbers title="variant_basics.cpp"
#include <boost/variant.hpp>
#include <string>
#include <iostream>

int main() {
    boost::variant<int, double, std::string> v;

    v = 42;                 // now holds int
    v = 3.14;               // now holds double
    v = std::string("hi");  // now holds std::string

    std::cout << "type index: " << v.which() << "\n";  // 0, 1, or 2
}
```

`which()` returns the zero-based index of the currently held alternative — useful for logging, but not
the idiomatic way to *use* the value.

## Visitation: the idiomatic access

The preferred way to operate on a variant is a **visitor** — a callable with an overload per
alternative — applied with `boost::apply_visitor`. Deriving from `boost::static_visitor<R>` declares the
common return type `R`.

```cpp showLineNumbers title="visit.cpp"
#include <boost/variant.hpp>
#include <string>
#include <iostream>

struct Printer : boost::static_visitor<void> {
    void operator()(int i)                const { std::cout << "int "    << i << "\n"; }
    void operator()(double d)             const { std::cout << "double " << d << "\n"; }
    void operator()(const std::string& s) const { std::cout << "string " << s << "\n"; }
};

int main() {
    boost::variant<int, double, std::string> v = std::string("hello");
    boost::apply_visitor(Printer{}, v);   // dispatches to the right overload
}
```

:::tip Visitors are compile-time exhaustive
If you add a new alternative to the variant and forget to handle it in the visitor, the code fails to
compile. That is a feature: the compiler reminds you of every place that must be updated. Prefer
visitation over chains of `get<T>` checks for exactly this reason.
:::

## Direct access with get

When you already know (or want to test) the active type, `boost::get<T>` retrieves it. The pointer
overload is the safe, branchless way to probe.

```cpp showLineNumbers
#include <boost/variant.hpp>
#include <string>

void use(boost::variant<int, std::string>& v) {
    if (int* p = boost::get<int>(&v)) {   // pointer form: nullptr if wrong type
        *p += 1;
    }
    // Reference form throws boost::bad_get if the type does not match:
    // int& r = boost::get<int>(v);
}
```

## Recursive variants

Some data is naturally recursive — JSON, expression trees, S-expressions. A variant cannot contain
*itself* by value (infinite size), so Boost provides `boost::make_recursive_variant` and the
`recursive_variant_` placeholder to break the cycle.

```cpp showLineNumbers title="json_tree.cpp"
#include <boost/variant.hpp>
#include <vector>
#include <map>
#include <string>

// A toy JSON value: scalar, array of values, or object of name to value.
using Json = boost::make_recursive_variant<
    std::nullptr_t,
    double,
    std::string,
    std::vector<boost::recursive_variant_>,
    std::map<std::string, boost::recursive_variant_>
>::type;

int main() {
    Json doc = std::vector<Json>{ 1.0, std::string("two"), nullptr };
    (void)doc;
}
```

:::note Why this is hard without help
`boost::variant<X, std::vector<...self...>>` would need to know its own size to lay out the vector
element type, which is circular. The recursive machinery introduces an indirection so the type can
refer to itself safely.
:::

## The never-empty guarantee

`boost::variant` promises it is **never empty**: it always holds a valid value of one of its
alternatives. Maintaining that during assignment is genuinely hard — if constructing the new value
throws *after* the old one was destroyed, what is left? Boost upholds the guarantee with a hidden
heap-backed "temporary backup" trick, which costs an occasional allocation.

:::warning The hidden cost of never-empty
To keep the guarantee, `boost::variant` may allocate on the heap during a throwing assignment, and its
double-buffering can make it larger and slower than you expect. This is the main motivation for its
successor, described below.
:::

## Boost.Variant versus std::variant versus variant2

C++17 standardised the idea as `std::variant`, but with a different bargain: it can become
**valueless by exception** (an empty-ish error state) rather than allocating to stay full.
Boost later introduced **Boost.Variant2** (`boost::variant2::variant`), which gives you the *never-empty*
guarantee **without** the heap allocation, plus better performance — it is widely regarded as the modern
successor.

| Aspect | `boost::variant` | `std::variant` (C++17) | `boost::variant2` |
|--------|------------------|------------------------|--------------------|
| Header | `<boost/variant.hpp>` | `<variant>` | `<boost/variant2/variant.hpp>` |
| Never-empty | yes (may allocate) | no (`valueless_by_exception`) | yes (no allocation) |
| Visitation | `apply_visitor` | `std::visit` | `visit` |
| Access | `get<T>`, `get_if` | `std::get`, `get_if` | `get<T>`, `get_if` |
| Performance | heaviest | light | light |

:::tip Which variant to use
For new code on C++17+, `std::variant` is the default — standard, light, no dependency. If you
specifically need the never-empty guarantee without the standard's allocation-free-but-emptyable
trade-off, prefer **Boost.Variant2**. Reach for the original `boost::variant` mainly for legacy code or
recursive-variant ergonomics. See [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md).
:::

## See also

- <Icon icon="lucide:puzzle" inline /> [Boost.Any](./boost-any.md) — type erasure when the set of types is *open*, not fixed.
- <Icon icon="lucide:boxes" inline /> [Boost.Optional](./boost-optional.md) — the special two-state case of "value or nothing".
- <Icon icon="lucide:type" inline /> [Boost.LexicalCast](./lexical-cast.md) — converting the scalar leaves of a variant tree to and from text.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::variant` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
