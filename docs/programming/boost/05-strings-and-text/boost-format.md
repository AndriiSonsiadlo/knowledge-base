---
id: boost-format
title: Boost.Format
sidebar_label: Boost.Format
sidebar_position: 2
tags: [c++, boost, strings, format, printf]
---

# Boost.Format

`boost::format` gives you **type-safe, positional string formatting** using a `printf`-inspired
syntax. Unlike `printf`, it catches type mismatches at run time instead of silently producing
garbage, and unlike manual `ostringstream` chaining, it keeps the format string readable. It was
the go-to formatting tool in C++ until `std::format` arrived in C++20.

:::info The problem it solves
`printf` is concise but unsafe — pass a `double` where it expects `int` and you get undefined
behaviour. `ostringstream` is safe but verbose — building a formatted message means chaining
`<<` with manipulators. `boost::format` combines the readability of a format string with the
type safety of streams.
:::

## Basic usage

The format string uses `%N%` positional placeholders (one-indexed):

```cpp showLineNumbers title="basic.cpp"
#include <boost/format.hpp>
#include <iostream>
#include <string>

int main() {
    std::string msg = (boost::format("Hello, %1%! You have %2% messages.") 
                       % "Alice" % 42).str();
    std::cout << msg << "\n";
    // Hello, Alice! You have 42 messages.
}
```

Each `%` operator feeds the next argument; `.str()` extracts the result as a `std::string`.
You can also stream directly:

```cpp showLineNumbers
std::cout << boost::format("(%1%, %2%)") % 3.14 % 2.72 << "\n";
// (3.14, 2.72)
```

## Positional reuse

Because placeholders are numbered, you can reuse and reorder them:

```cpp showLineNumbers title="positional.cpp"
#include <boost/format.hpp>
#include <iostream>

int main() {
    auto fmt = boost::format("%1% said: '%2%'. Yes, %1% really said that.")
               % "Bob" % "hello";
    std::cout << fmt << "\n";
    // Bob said: 'hello'. Yes, Bob really said that.
}
```

This is impossible with `printf` and awkward with `ostringstream`.

## Printf-style format specifiers

Boost.Format also accepts classic `printf` specifiers for width, precision, and fill:

```cpp showLineNumbers title="specifiers.cpp"
#include <boost/format.hpp>
#include <iostream>

int main() {
    // Fixed-width columns
    std::cout << boost::format("%-20s %10.2f\n") % "Widget" % 19.99;
    std::cout << boost::format("%-20s %10.2f\n") % "Gadget" % 149.50;
    // Widget                   19.99
    // Gadget                  149.50

    // Hex, zero-padded
    std::cout << boost::format("0x%08x") % 255 << "\n";
    // 0x000000ff
}
```

:::warning Mixing positional and printf-style placeholders
You can use `%1%` positional syntax or `%s`/`%d` printf syntax, but do not mix both in one
format string. Pick one style per call.
:::

## Error handling

Boost.Format validates argument count and throws on mismatch:

```cpp showLineNumbers title="errors.cpp"
#include <boost/format.hpp>
#include <iostream>

int main() {
    try {
        // Too few arguments — throws on .str()
        auto s = (boost::format("%1% and %2%") % "only-one").str();
    } catch (const boost::io::too_few_args& e) {
        std::cout << "Error: " << e.what() << "\n";
    }
}
```

| Exception | Cause |
|-----------|-------|
| `too_few_args` | Fewer `%` arguments than placeholders |
| `too_many_args` | More `%` arguments than placeholders |
| `bad_format_string` | Malformed format specifier |

## Boost.Format versus std::format versus printf

| Feature | `printf` | `boost::format` | `std::format` (C++20) |
|---------|----------|------------------|-----------------------|
| Type safe | no | yes (runtime) | yes (compile-time) |
| Positional args | POSIX extension (`%1$s`) | `%1%` | `{0}` |
| Extensible to user types | no | yes (via `operator<<`) | yes (via `std::formatter`) |
| Compile-time checks | no | no | yes |
| Header | `<cstdio>` | `<boost/format.hpp>` | `<format>` |
| Performance | fast | moderate | fast |

:::note Which to choose
On C++20 and later, prefer `std::format` — it is faster, catches errors at compile time, and
needs no dependency. Boost.Format remains useful on pre-C++20 toolchains or when you need its
`%N%` positional syntax in existing codebases. See
[Boost and the standard](../00-overview/boost-and-the-standard.md).
:::

## Reusable format objects

A `boost::format` object can be bound to a format string once and reused:

```cpp showLineNumbers title="reuse.cpp"
#include <boost/format.hpp>
#include <iostream>

int main() {
    boost::format row("| %-15s | %6d | %8.2f |");
    std::cout << (row % "Apples" % 120 % 1.50) << "\n";
    row.clear();  // reset for reuse
    std::cout << (row % "Bananas" % 45 % 0.75) << "\n";
}
```

Call `.clear()` between uses to reset the argument state without reparsing the format string.

## See also

- <Icon icon="lucide:type" inline /> [Boost.StringAlgo](./string-algo.md) — string manipulation without formatting.
- <Icon icon="lucide:scissors" inline /> [Boost.Tokenizer](./boost-tokenizer.md) — parsing strings into parts.
- <Icon icon="lucide:arrow-left-right" inline /> [lexical_cast](../02-core-utilities/lexical-cast.md) — simple value-to-string and back.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::format` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
