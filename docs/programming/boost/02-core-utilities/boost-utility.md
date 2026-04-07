---
id: boost-utility
title: Boost.Utility
sidebar_label: Boost.Utility
sidebar_position: 2
tags: [ c++, boost, utility ]
---

# Boost.Utility

Boost.Utility is one of the oldest corners of Boost: a historical collection of miscellaneous
small helpers that predate [Boost.Core](./boost-core.md). Over time many of its pieces were either
absorbed into Core or standardised into `std`, so today Utility is best understood as a *grab-bag with
a long memory* — useful classics still live here, and a lot of Boost code includes it out of habit.

:::info Historical role
Before Boost had a dedicated "Core" library, Utility was where tiny shared helpers went. As the
dependency-hygiene story improved, the truly fundamental pieces (`addressof`, `ref`, `noncopyable`)
migrated to Core. Utility kept the more specialised odds and ends described below.
:::

## base-from-member: initialise a base from your own member

A subtle C++ ordering problem: base classes are constructed *before* members, so you cannot normally
pass one of your own members to a base-class constructor. `boost::base_from_member` solves it by
turning the would-be member into a base that is constructed first.

```cpp showLineNumbers title="base_from_member_demo.cpp"
#include <boost/utility/base_from_member.hpp>
#include <streambuf>
#include <ostream>

// We want to own a streambuf AND pass it to the ostream base.
class device_stream
    : private boost::base_from_member<std::filebuf>  // constructed first
    , public std::ostream
{
    using buf_base = boost::base_from_member<std::filebuf>;
public:
    device_stream()
        : buf_base()                      // member-as-base built first
        , std::ostream(&this->member) {}  // now safe to pass to the base
};
```

This is a niche but genuinely useful idiom when wrapping legacy stream or buffer types.

### next and prior: iterator arithmetic without mutation

`boost::next(it)` and `boost::prior(it)` return advanced copies of an iterator, leaving the original
untouched — handy before C++11 gave us `std::next` / `std::prev`.

```cpp showLineNumbers
#include <boost/next_prior.hpp>
#include <list>

int main() {
    std::list<int> l{1, 2, 3, 4};
    auto second = boost::next(l.begin());   // points at 2
    auto last   = boost::prior(l.end());    // points at 4
    (void)second; (void)last;
}
```

:::note Standardised
`std::next` and `std::prev` (C++11, in `<iterator>`) supersede these. Prefer them in new code.
:::

### value_init: guaranteed value-initialisation

`boost::value_initialized<T>` wraps a `T` and value-initialises it, dodging the historical pitfalls of
"does `T x;` zero-init or not?" for templates and aggregates.

```cpp showLineNumbers
#include <boost/utility/value_init.hpp>

template <class T>
T zeroed() {
    boost::value_initialized<T> v;   // T() semantics, reliably
    return boost::get(v);
}
```

### BOOST_BINARY: binary literals before C++14

Long before C++14 added `0b1010` literals, `BOOST_BINARY` let you write binary constants by grouping
bits in token chunks.

```cpp showLineNumbers
#include <boost/utility/binary.hpp>

unsigned mask = BOOST_BINARY(1010 0101);  // == 0xA5
```

On C++14 and later, prefer the native `0b10100101` literal.

### string_view: a non-owning string reference

`boost::string_view` (and `boost::string_ref`) is a non-owning view over a character range — the model
that C++17 standardised as `std::string_view`. Use it to accept "any string-like thing" without copying
or templating.

```cpp showLineNumbers
#include <boost/utility/string_view.hpp>

bool starts_with(boost::string_view s, boost::string_view prefix) {
    return s.size() >= prefix.size() &&
           s.substr(0, prefix.size()) == prefix;
}
```

:::tip Prefer std::string_view
On C++17+, `std::string_view` is the right choice. Boost's version exists for older toolchains and for
code already inside the Boost dependency graph.
:::

### result_of and declval-style helpers

`boost::result_of<F(Args...)>::type` computes the return type of invoking `F` with `Args...` — a
metaprogramming staple from the era before `decltype` was universal. Boost also exposes
`declval`-style helpers for forming unevaluated expressions in type traits.

```cpp showLineNumbers
#include <boost/utility/result_of.hpp>

template <class F>
auto apply_to_zero(F f) -> typename boost::result_of<F(int)>::type {
    return f(0);
}
```

`std::result_of` was deprecated and removed in favour of `std::invoke_result` (C++17); on modern
toolchains use `decltype` / `std::invoke_result_t` directly.

### compressed_pair: empty base optimisation

`boost::compressed_pair<First, Second>` stores two values but applies the **empty base optimisation
(EBO)**: if one type is empty (a stateless comparator, allocator, or deleter), it occupies *zero*
extra bytes instead of the one byte a normal member would cost.

```cpp showLineNumbers title="compressed_pair_demo.cpp"
#include <boost/compressed_pair.hpp>
#include <iostream>

struct EmptyCmp {};  // stateless functor: sizeof == 1 on its own

int main() {
    boost::compressed_pair<int, EmptyCmp> p;
    // sizeof(p) == sizeof(int): the empty type was folded away.
    std::cout << sizeof(p) << " vs " << (sizeof(int) + sizeof(EmptyCmp)) << "\n";
}
```

This is exactly the technique standard containers use internally to make `std::vector` carry a
stateless allocator for free. It is the most enduringly useful piece of Boost.Utility, often pulled in
by container and smart-pointer implementations.

:::info Why EBO matters
Without compression, every empty helper object would bloat each element by at least one byte (and often
more after alignment). In a container holding millions of nodes, that adds up. EBO via base-class
layout makes "policy" types truly free.
:::

## What survives, what to prefer instead

| Utility piece | Status today | Prefer |
|---------------|--------------|--------|
| `base_from_member` | still useful | Boost.Utility |
| `next` / `prior` | superseded | `std::next` / `std::prev` |
| `value_initialized` | niche | usually `T{}` |
| `BOOST_BINARY` | superseded | `0b...` literal (C++14) |
| `string_view` | superseded | `std::string_view` (C++17) |
| `result_of` | removed from `std` | `std::invoke_result_t` (C++17) |
| `compressed_pair` | still useful | Boost.Utility (no `std` equivalent) |

## See also

- <Icon icon="lucide:wrench" inline /> [Boost.Core](./boost-core.md) — where the most fundamental helpers now live.
- <Icon icon="lucide:type" inline /> [Boost.LexicalCast](./lexical-cast.md) — text/value conversion built atop these primitives.
- <Icon icon="lucide:memory-stick" inline /> [Smart Pointers Overview](../03-smart-pointers-and-memory/smart-ptr-overview.md) — a heavy user of `compressed_pair`.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — what graduated into `std`.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
