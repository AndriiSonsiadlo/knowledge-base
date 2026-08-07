---
id: what-is-fmt
title: What is fmt?
sidebar_label: What is fmt
sidebar_position: 1
tags: [c++, fmt, overview, introduction]
---

# What is fmt?

C++ had two bad options for turning values into text: `printf`, which is fast and terse but
type-unsafe and impossible to extend to your own types, and iostreams, which are safe and
extensible but verbose, slow, and painful to read at the call site. fmt is the third option — a
library that took the good parts of both and threw away the rest — and it won hard enough that its
design became C++20's `std::format`.

## The core idea

A format string is a small template with holes in it. Each `{}` is a replacement field, filled in
order by the arguments that follow. Arguments are passed by reference and type-erased internally, so
`fmt::format` doesn't have to instantiate a separate template for every combination of argument
types at every call site — the format string is parsed once, at compile time when it's a literal.

```cpp
#include <fmt/format.h>

std::string greeting = fmt::format("Hello, {}! You are {} years old.", name, age);
fmt::print("{} scored {:.1f} out of {}\n", player, score, max_score);
fmt::print("{0} likes {1}, and {1} likes {0} back\n", alice, bob);
```

## What you get

- **Type safety** — the compiler knows the type of every argument; there is no `%d`/`%lld` mismatch
  that silently reads garbage off the stack.
- **Extensibility** — any type gets first-class formatting support by specializing
  `fmt::formatter<T>`, spec grammar included.
- **Positional and named arguments** — reorder or reuse arguments without touching the call site,
  which matters the moment a string gets translated.
- **`std::chrono` and range support** — durations, time points, containers, tuples and pairs format
  out of the box once you include the right header.
- **Color and text styles** — terminal color is a formatting concern in fmt, not a pile of pasted
  ANSI escape codes.
- **No allocation for small outputs** — short results are formatted into inline stack storage; a
  `std::string` is only allocated when the output actually needs one.

## Where it lives

fmt's functionality is split across headers so you only pay for what you include.

| Header | Brings in | Cost |
|---|---|---|
| `<fmt/base.h>` | `fmt::format_string`, the lightweight declarations | Cheapest — safe to include broadly |
| `<fmt/format.h>` | `fmt::format`, `fmt::print`, `fmt::format_to`, floating-point formatting | The header most code actually needs |
| `<fmt/ranges.h>` | Formatting for containers, tuples, pairs, `fmt::join` | Pulls in `<fmt/format.h>` |
| `<fmt/chrono.h>` | Formatting for `std::chrono` durations and time points | Pulls in `<fmt/format.h>` |
| `<fmt/color.h>` | `fmt::color`, `fmt::emphasis`, `fmt::styled` | Pulls in `<fmt/format.h>` |

:::note[Header names shifted around fmt 10/11 — check the version you are on]
Older code often includes `<fmt/core.h>` where current code includes `<fmt/base.h>`. Both exist in
recent releases for compatibility, but new code should prefer `<fmt/base.h>` and only reach for
`<fmt/format.h>` where the heavier functionality is actually used.
:::

## A first taste

```cpp showLineNumbers title="hello_fmt.cpp"
#include <fmt/format.h>

int main() {
    // Aligned, precision-controlled output straight to stdout.
    fmt::print("{:<10}{:>8.2f}\n", "total:", 42.5);

    // Building a string instead of printing it directly.
    std::string report = fmt::format("{} rows in {:.3f}s", row_count, elapsed_seconds);
    log(report);
}
```

## See also

- <Icon icon="lucide:git-branch" inline /> [Relationship to std::format](./relationship-to-std-format.md) — how fmt and the standard library facility relate, and which to reach for.
- <Icon icon="lucide:download" inline /> [Installation and integration](./installation-and-integration.md) — header-only vs compiled, CMake, vcpkg, Conan.
- <Icon icon="lucide:scale" inline /> [Comparison with printf and iostreams](./comparison-with-printf-and-iostreams.md) — what fmt actually fixes about the two incumbents.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
