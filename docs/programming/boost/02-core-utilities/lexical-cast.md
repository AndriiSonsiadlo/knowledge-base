---
id: lexical-cast
title: Boost.LexicalCast
sidebar_label: Boost.LexicalCast
sidebar_position: 7
tags: [ c++, boost, conversion, strings ]
---

# Boost.LexicalCast

`boost::lexical_cast<T>(source)` converts between text and almost any type with a single, uniform
syntax. It is the convenient middle ground between the verbose `std::stringstream` dance and the
fast-but-fiddly low-level conversion functions: one expression turns a string into a number, a number
into a string, or one streamable type into another.

:::info The appeal
Before C++11 gave us `std::stoi` / `std::to_string`, and before C++17 added `std::from_chars`,
converting `"42"` to an `int` meant building a `stringstream`, shifting the value in, checking failure
bits, and shifting it out. `lexical_cast` collapses all of that into one readable call.
:::

## Basic conversions

```cpp showLineNumbers title="lexical_basics.cpp"
#include <boost/lexical_cast.hpp>
#include <string>
#include <iostream>

int main() {
    int    n = boost::lexical_cast<int>("42");        // string  -> int
    double d = boost::lexical_cast<double>("3.14");   // string  -> double
    std::string s = boost::lexical_cast<std::string>(255); // int -> string

    std::cout << n << " " << d << " " << s << "\n";
}
```

Any type that supports `operator>>` and `operator<<` works, which means it composes with your own
streamable types for free.

## Error handling with bad_lexical_cast

Unlike `atoi` (which silently returns `0`) or `std::stringstream` (which quietly sets a failbit),
`lexical_cast` **throws** `boost::bad_lexical_cast` when the source does not represent a valid target
value. This makes failures impossible to ignore.

```cpp showLineNumbers title="lexical_errors.cpp"
#include <boost/lexical_cast.hpp>
#include <iostream>

int main() {
    try {
        int n = boost::lexical_cast<int>("not a number");
        (void)n;
    } catch (const boost::bad_lexical_cast& e) {
        std::cerr << "conversion failed: " << e.what() << "\n";
    }
}
```

:::warning Strictness can surprise you
`lexical_cast<int>("42 ")` (trailing space) and `lexical_cast<int>("3.14")` (fractional text into an
`int`) both **throw** — the entire string must be a valid representation of the target. That strictness
is usually a feature, but it means `lexical_cast` is not a tolerant parser. If you need to skip
whitespace or accept partial input, use a real parser.
:::

## Performance: where it sits

`lexical_cast` is *much* faster than a naive `stringstream` (it avoids the locale and allocation
overhead of constructing a stream each time, using optimised internal paths for built-in types). But it
is still generally **slower** than the dedicated C++11/17 facilities, because it carries a more generic
machine and goes through stream-style formatting semantics for many types.

| Tool | Speed | Safety | Generality |
|------|-------|--------|-------------|
| `std::stringstream` | slowest | failbit (easy to ignore) | any streamable type |
| `boost::lexical_cast` | medium | throws on failure | any streamable type |
| `std::to_string` / `std::stoi` | fast | `stoi` throws; `to_string` fixed format | numbers only |
| `std::to_chars` / `std::from_chars` | fastest | error code, no throw, no alloc | numbers only |

```cpp showLineNumbers title="from_chars.cpp"
#include <charconv>
#include <string_view>
#include <system_error>

// The C++17 high-performance path: no allocation, no locale, no exceptions.
bool parse_int(std::string_view sv, int& out) {
    auto [ptr, ec] = std::from_chars(sv.data(), sv.data() + sv.size(), out);
    return ec == std::errc{} && ptr == sv.data() + sv.size();
}
```

## Pitfalls: locale and precision

:::danger Locale dependence
`lexical_cast` historically honours stream formatting rules, so a locale that uses a comma as the
decimal separator can change how `"3,14"` versus `"3.14"` is interpreted, and grouping separators can
break round-trips. For data interchange (config files, network protocols, JSON), this locale sensitivity
is a real hazard. `std::from_chars` / `std::to_chars` are deliberately **locale-independent** and are the
safer choice for serialised data.
:::

A second trap is **floating-point precision**: converting a `double` to a string and back must preserve
the exact value, and the default formatting may not round-trip cleanly across all implementations and
versions. When exact round-tripping matters, prefer `std::to_chars` with the shortest-round-trip
algorithm.

```cpp showLineNumbers
#include <boost/lexical_cast.hpp>
#include <string>

// Round-trip a double. Usually fine, but precision/locale can bite —
// for exact round-tripping prefer std::to_chars.
double x = 0.1 + 0.2;
std::string text = boost::lexical_cast<std::string>(x);
double back = boost::lexical_cast<double>(text);
```

## When to prefer which

:::tip Recommendation
- Reach for **`lexical_cast`** for quick, readable, low-volume conversions — CLI arguments, log
  formatting, glue code — especially when you value the throw-on-failure behaviour and the uniform
  syntax across types.
- Use **`std::to_chars` / `std::from_chars`** (C++17) on hot paths and for any **serialised or
  interchange data**, where speed, no allocation, and locale-independence are essential.
- Use **`std::to_string` / `std::stoi`** family for simple number/string work when you are on C++11+
  and do not need the fastest path.

See [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) for the broader "Boost first,
then `std`" picture.
:::

## See also

- <Icon icon="lucide:type" inline /> [Boost.Utility](./boost-utility.md) — `string_view` and other text primitives.
- <Icon icon="lucide:boxes" inline /> [Boost.Variant](./boost-variant.md) — converting the scalar leaves of a variant to and from text.
- <Icon icon="lucide:puzzle" inline /> [Boost.Optional](./boost-optional.md) — modelling a conversion that may legitimately fail without throwing.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — choosing Boost versus `std`.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
