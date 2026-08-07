---
id: basic-formatting
title: Basic formatting
sidebar_label: Basic formatting
sidebar_position: 3
tags: [c++, spdlog, basics, formatting, fmt]
---

# Basic formatting

spdlog's format strings are fmt's format strings — the same `{}` mini-language, with the same
compile-time-checkable syntax, whether you knew that or not when you wrote your first
`spdlog::info("{}", x)`.

## Replacement fields

```cpp showLineNumbers
spdlog::info("connected to {}", host);              // positional, implicit
spdlog::info("{1} before {0}", "second", "first");   // explicit index: "first before second"
spdlog::info("retry {:>4}/{}", attempt, max_attempts); // right-aligned, width 4
spdlog::info("elapsed: {:.3f}s", elapsed_seconds);    // fixed, 3 decimal places
```

`{}` consumes the next argument in order; `{N}` picks argument `N` explicitly, useful when the same
value appears more than once. The `:` introduces a format spec — alignment, width, precision, and
type presentation, all inherited directly from fmt.

## Why not printf or streams

| | printf | iostreams | spdlog/fmt |
|---|---|---|---|
| Type safety | None — mismatched `%d`/`%s` is UB | Compile-time via overloads | Compile-time checkable |
| Extensibility | None | `operator<<` overload | `fmt::formatter<T>` specialization |
| Throughput | Fast, but locale/format-string parsing per call | Slow — virtual dispatch, locale checks | Fastest of the three in benchmarks |
| Translation-friendliness | `{0}`-style reordering not portable | Awkward — order is call order | `{1} {0}` reordering built in |

## Formatting your own types

Two ways to make a custom type loggable. Preferred: specialize `fmt::formatter<T>`.

```cpp showLineNumbers title="point_formatter.hpp"
struct Point { int x, y; };

template <>
struct fmt::formatter<Point> : fmt::formatter<std::string> {
    auto format(const Point& p, format_context& ctx) const {
        return fmt::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};

// spdlog::info("cursor at {}", Point{3, 7});   // -> "cursor at (3, 7)"
```

If the type already has `operator<<(std::ostream&, const T&)`, `#include "spdlog/fmt/ostr.h"` makes
it loggable without writing a formatter — slower than a native specialization, but zero extra code
for types you don't own.

## Argument evaluation

Arguments to `spdlog::info(...)` and friends are evaluated whether or not the level is enabled — the
level check happens, but by the time it does, the arguments have often already been computed as part
of building the call.

:::danger[An expensive argument still costs you at a disabled level]
```cpp
spdlog::debug("state: {}", expensive_serialize(state));  // expensive_serialize() runs
                                                           // even if debug is disabled
```
If an argument is genuinely expensive to compute, guard it explicitly or use the `SPDLOG_*` macros
with a low `SPDLOG_ACTIVE_LEVEL` — see
[Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) for the
version that removes both the call and the argument evaluation entirely.
:::

## Escaping braces

Literal `{` and `}` in a message need doubling: `{{` and `}}`.

:::note[A user-supplied string used as a format string is a bug]
```cpp
spdlog::info(user_input);              // wrong: user_input is parsed as a format string
spdlog::info("{}", user_input);        // right: user_input is just an argument
```
The first form lets a user-controlled string containing `{}` crash or misbehave your logging. Always
pass untrusted text as an argument, never as the format string itself.
:::

## See also

- <Icon icon="lucide:rocket" inline /> [Quick start](./quick-start.md) — formatting in a complete program.
- <Icon icon="lucide:type" inline /> [Pattern flags](../04-formatting-and-patterns/pattern-flags.md) — formatting the line *around* the message, not just the message.
- <Icon icon="lucide:compass" inline /> [Design philosophy](../00-overview/design-philosophy.md) — why fmt over printf/iostreams in the first place.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
