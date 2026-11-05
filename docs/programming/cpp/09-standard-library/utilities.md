---
id: utilities
title: Utility Library (pair, tuple, optional, variant, any)
sidebar_label: Utilities
sidebar_position: 6
tags: [c++, utilities, pair, tuple, optional, variant, any, structured-bindings, reference-wrapper, exchange]
---

# Utility Library (pair, tuple, optional, variant, any)

Small vocabulary types let a function say what it returns without a custom struct or a sentinel
value: two values (`pair`), several (`tuple`), maybe one (`optional`), one of several types
(`variant`), or anything (`any`). They are value types that live inside the object, mostly with no
heap allocation, and they appear in the signatures of the rest of the library
([`map`](./containers.md) elements are `pair`s, for example). This page is the canonical home
for them and for a few helpers (`reference_wrapper`, `exchange`). `std::function` is a
type-erased callable and is covered by [type erasure](../13-idioms-and-design/06-type-erasure.md);
`std::expected` is covered with [error codes](../10-error-handling-and-safety/03-error-codes.md);
`std::move` and `std::forward` are explained under [value categories](../03-types-and-values/value-categories/lvalues-rvalues.md)
and [reference collapsing](../03-types-and-values/value-categories/reference-collapsing.md).

**Prerequisites:** [Class templates](../08-templates-and-metaprogramming/class-templates.md),
[variadic templates](../08-templates-and-metaprogramming/variadic-templates.md) (for `tuple`),
[copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## `std::pair` and `std::tuple`

`std::pair<A, B>` has public members `first` and `second`. `std::tuple<Ts...>` generalizes it to any
number of elements, accessed by `std::get<I>(t)` or `std::get<T>(t)` (the type form requires the type
to occur once). Both have `==`, `<`, and (C++20) `<=>` that compare lexicographically, which makes
`std::tie(a.x, a.y) < std::tie(b.x, b.y)` a short way to write a multi-field comparator.

```cpp title="pair-tuple.cpp" showLineNumbers
#include <iostream>
#include <map>
#include <string>
#include <tuple>

std::tuple<int, std::string, double> record() { return {7, "seven", 7.5}; }

int main() {
    std::pair<std::string, int> p{"x", 1};                  // C++17 CTAD also allows std::pair p{"x", 1}
    auto [name, id, score] = record();                      // C++17 structured bindings
    std::cout << p.first << ' ' << name << id << ' ' << score << '\n';

    int a = 0; std::string s;
    std::tie(a, s, std::ignore) = record();                 // assign into existing variables
    std::cout << a << s << '\n';

    std::map<std::string, int> m{{"k", 1}};
    for (const auto& [k, v] : m) std::cout << k << v << '\n';   // map elements are pair<const K, V>

    auto t = std::tuple_cat(std::make_tuple(1), std::make_tuple('c'));
    std::cout << std::tuple_size_v<decltype(t)> << ' '
              << std::apply([](int i, char c) { return i + c; }, t) << '\n';   // C++17
}
```

```text
x 7seven 7.5
7seven
k1
2 100
```

- Structured bindings copy or reference according to the declaration: `auto [a, b] = t;` copies the
  tuple, `auto& [a, b] = t;` binds references into it.
- `std::make_pair` and `std::make_tuple` decay their arguments and unwrap `std::reference_wrapper`;
  `std::forward_as_tuple` builds a tuple of references for forwarding, and `std::tie` a tuple of
  lvalue references.
- `std::get` and `std::tuple_size` are what make structured bindings work for user-defined types: specialize
  `tuple_size`, `tuple_element` and provide `get`.
- A named struct with `x` and `y` members documents intent better in an interface than `.first` and `.second`.
- Prefer `emplace`/`try_emplace` to constructing `pair<const K, V>` temporaries when inserting into maps.

## `std::optional<T>` *(C++17)*

An `optional<T>` is either empty (`std::nullopt`) or contains a `T` stored **inside the optional**
(no heap allocation), so `sizeof(optional<T>)` is about `sizeof(T)` plus a flag, rounded for
alignment. It models "may not have a value" without pointers or magic values like `-1`.

```cpp title="optional.cpp" showLineNumbers
#include <charconv>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>

std::optional<int> parse(std::string_view s) {
    int v = 0;
    auto [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
    if (ec != std::errc{} || p != s.data() + s.size()) return std::nullopt;
    return v;
}

int main() {
    for (std::string_view s : {"42", "4x"}) {
        if (auto v = parse(s))                         // explicit operator bool: has a value?
            std::cout << "ok " << *v << '\n';
        else
            std::cout << "bad " << s << '\n';
    }
    std::cout << parse("oops").value_or(-1) << '\n';
}
```

```text
ok 42
bad 4x
-1
```

- `*opt` and `opt->` do **not** check, and are undefined behavior on an empty optional;
  `opt.value()` throws `std::bad_optional_access`. Check with `has_value()` / `if (opt)`.
- `value_or(x)` returns a copy of the contained value or `x`.
- `emplace(args...)` constructs in place, `reset()` destroys the value, and `optional<T&>` is not
  allowed in C++17/20 (C++26 adds it; use `std::reference_wrapper<T>` or a pointer before that).
- C++23 added monadic operations: `and_then`, `transform`, `or_else`.
- Comparison: an empty optional is less than any value; two empty optionals are equal.
- Do not use `optional<bool>`/`optional<int>` in conditions without `has_value()`:
  `if (opt)` tests presence and not the value.

## `std::variant<Ts...>` *(C++17)*

A **type-safe union**: at any time a `variant` holds exactly one value of one of its alternative
types, plus an index recording which. It is stored inline, with `sizeof` of the largest alternative
plus the index (rounded up). It is the tool for a closed set of alternatives that don't share an
interface, for example an AST node or a message type, in contrast to
[virtual functions](../07-classes-and-oop/virtual-functions.md) for an open set.

```cpp title="variant.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <variant>

template <class... Fs> struct overloaded : Fs... { using Fs::operator()...; };
template <class... Fs> overloaded(Fs...) -> overloaded<Fs...>;   // needed before C++20

int main() {
    std::variant<int, double, std::string> v = 42;           // holds int, index 0
    v = std::string("hi");                                   // now index 2

    std::visit(overloaded{
        [](int i)                { std::cout << "int " << i << '\n'; },
        [](double d)             { std::cout << "double " << d << '\n'; },
        [](const std::string& s) { std::cout << "string " << s << '\n'; },
    }, v);                                                   // missing a case: compile error

    std::cout << v.index() << ' ' << std::holds_alternative<std::string>(v) << '\n';
    if (auto* s = std::get_if<std::string>(&v)) std::cout << s->size() << '\n';  // pointer or null
    try { (void)std::get<int>(v); } catch (const std::bad_variant_access&) { std::cout << "wrong type\n"; }
}
```

```text
string hi
2 1
2
wrong type
```

- A default-constructed `variant` holds its **first** alternative, which must therefore be
  default-constructible; use `std::monostate` as the first alternative to get an "empty" state.
- `std::visit` forces you to handle every alternative at compile time, which is the main advantage over a
  `switch` on a tag you maintain by hand. The visitor must return the same type for all alternatives.
- `std::get<T>(v)` throws `std::bad_variant_access` on a mismatch; `std::get_if<T>(&v)` returns a pointer or `nullptr`.
- **`valueless_by_exception`**: if constructing the new alternative during assignment throws, the variant
  can end up holding nothing (`v.valueless_by_exception()` is `true`, `index()` is `variant_npos`). It is
  rare when the alternatives have `noexcept` moves.
- Alternatives are distinct *types*: `variant<int, int>` is allowed but awkward to use (access by index).
  Conversions can surprise: `variant<bool, std::string> v = "text";` selected `bool` (a pointer-to-bool
  conversion) in the original C++17 wording. P0608 narrowed the converting constructor and is
  applied to C++17 by current compilers, so it now selects `std::string` (checked with g++ 15 and clang++ 21 at `-std=c++17`).

## `std::any` *(C++17)*

`std::any` holds a copy of **any copyable** value, found again by exact type with `std::any_cast<T>`:

```cpp title="any.cpp" showLineNumbers
#include <any>
#include <iostream>
#include <string>

int main() {
    std::any a = 42;
    a = std::string("text");
    std::cout << a.type().name() << '\n' << std::any_cast<std::string>(a).size() << '\n';
    if (auto* p = std::any_cast<int>(&a)) std::cout << *p; else std::cout << "not an int\n";
    try { std::any_cast<int>(a); } catch (const std::bad_any_cast&) { std::cout << "bad cast\n"; }
}
```

The type name printed by `a.type().name()` is implementation-specific (mangled on GCC and Clang),
so the output of this program is not shown. The other lines print `4`, `not an int` and `bad cast`.

`any` uses type erasure: small values may be stored inline (implementation-defined), larger ones are
heap-allocated, and cast checks cost a type comparison. The cast must match the stored type
**exactly** (`any_cast<long>` of an `int` fails). Reach for `variant` when the set of types is
known, and for a template or virtual interface when behaviour is shared. `any` is for
genuinely open-ended storage such as property bags.

## `std::reference_wrapper` and `std::exchange`

`std::reference_wrapper<T>` (`std::ref(x)`, `std::cref(x)`) is a copyable, assignable object that
holds a reference. It exists to put references where the library would otherwise copy:
`std::vector<std::reference_wrapper<T>>`, passing `std::ref(x)` through `std::thread` or `std::bind`
arguments, or keeping a predicate by reference in an algorithm.

`std::exchange(obj, new)` *(C++14)* assigns `new` to `obj` and returns the old value. Its main use is
writing a move constructor or `reset`:

```cpp title="exchange.cpp" showLineNumbers
#include <iostream>
#include <utility>

struct Handle {
    int fd;
    explicit Handle(int f) : fd(f) {}
    Handle(Handle&& o) noexcept : fd(std::exchange(o.fd, -1)) {}   // take it, leave -1 behind
};

int main() {
    Handle a(5);
    Handle b(std::move(a));
    std::cout << a.fd << ' ' << b.fd << '\n';
}
```

```text
-1 5
```

## Related

- [Containers](./containers.md): `map` elements are `pair`s; node handles and `try_emplace`
- [Type erasure](../13-idioms-and-design/06-type-erasure.md): how `std::function` and `std::any` store arbitrary types
- [Error codes](../10-error-handling-and-safety/03-error-codes.md): `std::expected<T, E>`, the optional with an error
- [Lambdas](../07-classes-and-oop/lambdas.md): the visitors passed to `std::visit`
- [Strings](./strings.md): `string_view`, which often replaces `optional<std::string>` parameters

## References

- [Utility library, cppreference](https://en.cppreference.com/w/cpp/utility)
- [`std::variant`, cppreference](https://en.cppreference.com/w/cpp/utility/variant)
- ISO C++ [utilities]
