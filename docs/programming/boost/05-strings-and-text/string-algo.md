---
id: string-algo
title: Boost.StringAlgo
sidebar_label: Boost.StringAlgo
sidebar_position: 1
tags: [c++, boost, strings, algorithm]
---

# Boost.StringAlgo

`boost::algorithm::string` is a collection of **generic string algorithms** — case conversion,
trimming, finding, replacing, splitting, joining, and predicates — that work on any range of
characters, not just `std::string`. It fills the gap left by the standard library, which has
surprisingly few ready-made string utilities.

:::info The problem it solves
The C++ standard library gives you `std::string` but almost no algorithms that operate on it.
Want to trim whitespace, split on a delimiter, or check if a string starts with a prefix? Before
C++20 you had to write it yourself, reach for C functions, or add Boost.StringAlgo.
:::

## Case conversion

The `to_upper` and `to_lower` family modifies in place; `to_upper_copy` and `to_lower_copy`
return a new string.

```cpp showLineNumbers title="case.cpp"
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <string>

int main() {
    std::string s = "Hello, Boost!";
    boost::to_upper(s);                      // modifies in place
    std::cout << s << "\n";                  // HELLO, BOOST!

    std::string lower = boost::to_lower_copy(s); // returns a copy
    std::cout << lower << "\n";              // hello, boost!
}
```

## Trimming

Remove leading, trailing, or both kinds of whitespace (or characters matching a predicate):

```cpp showLineNumbers title="trim.cpp"
#include <boost/algorithm/string.hpp>
#include <string>

int main() {
    std::string s = "   padded   ";
    boost::trim(s);           // "padded"
    boost::trim_left(s);      // left only
    boost::trim_right(s);     // right only

    std::string digits = "00042";
    boost::trim_left_if(digits, boost::is_any_of("0")); // "42"
}
```

## Predicates

Quick boolean checks without writing loops:

```cpp showLineNumbers title="predicates.cpp"
#include <boost/algorithm/string.hpp>
#include <cassert>
#include <string>

int main() {
    std::string path = "/usr/local/bin/app";

    assert(boost::starts_with(path, "/usr"));
    assert(boost::ends_with(path, "app"));
    assert(boost::contains(path, "local"));
    assert(boost::iequals("Boost", "boost"));   // case-insensitive
}
```

:::tip C++20 added `starts_with` and `ends_with`
`std::string::starts_with` and `ends_with` arrived in C++20. If your toolchain supports them,
prefer the standard versions for those two. Boost.StringAlgo still wins for `contains`,
`iequals`, `all`, and the rest.
:::

## Splitting and joining

```cpp showLineNumbers title="split_join.cpp"
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::string csv = "one,,two,three";
    std::vector<std::string> parts;

    // Split, keeping empty tokens
    boost::split(parts, csv, boost::is_any_of(","));
    // parts: {"one", "", "two", "three"}

    // Split, compressing adjacent delimiters
    boost::split(parts, csv, boost::is_any_of(","), boost::token_compress_on);
    // parts: {"one", "two", "three"}

    // Join back
    std::string joined = boost::join(parts, " | ");
    std::cout << joined << "\n";   // one | two | three
}
```

## Find and replace

```cpp showLineNumbers title="replace.cpp"
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <string>

int main() {
    std::string s = "the quick brown fox jumps over the lazy dog";

    boost::replace_first(s, "the", "a");
    // "a quick brown fox jumps over the lazy dog"

    boost::replace_all(s, " ", "_");
    // "a_quick_brown_fox_jumps_over_the_lazy_dog"

    boost::erase_all(s, "_");
    // "aquickbrownfoxjumpsoverthelazydog"

    std::string t = "Hello World";
    boost::ireplace_first(t, "hello", "Hi");  // case-insensitive
    std::cout << t << "\n";                   // Hi World
}
```

## Working with ranges, not just strings

Every algorithm in the library is templated on a *range* concept, so it works with any container
of characters — `std::string`, `std::string_view`, `std::vector<char>`, even iterator pairs.

```cpp showLineNumbers title="range.cpp"
#include <boost/algorithm/string.hpp>
#include <string_view>
#include <cassert>

int main() {
    std::string_view sv = "  hello  ";
    auto trimmed = boost::trim_copy(std::string(sv));
    assert(trimmed == "hello");
}
```

## Quick reference

| Task | Function | In-place variant |
|------|----------|-----------------|
| Uppercase | `to_upper_copy` | `to_upper` |
| Lowercase | `to_lower_copy` | `to_lower` |
| Trim both | `trim_copy` | `trim` |
| Starts with | `starts_with` | -- |
| Contains | `contains` | -- |
| Split | `split` | -- |
| Join | `join` | -- |
| Replace first | `replace_first_copy` | `replace_first` |
| Replace all | `replace_all_copy` | `replace_all` |
| Erase all | `erase_all_copy` | `erase_all` |

:::note Naming convention
Functions ending in `_copy` return a new string; the bare name modifies the argument in place.
Functions prefixed with `i` (like `ifind_first`, `ireplace_all`) are case-insensitive.
:::

## See also

- <Icon icon="lucide:type" inline /> [Boost.Format](./boost-format.md) — type-safe string formatting.
- <Icon icon="lucide:scissors" inline /> [Boost.Tokenizer](./boost-tokenizer.md) — iterator-based token splitting.
- <Icon icon="lucide:regex" inline /> [Boost.Regex](./boost-regex.md) — when simple find/replace is not enough.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — which string utilities made it into `std`.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
