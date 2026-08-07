---
id: chrono-and-time-formatting
title: Chrono and time formatting
sidebar_label: Chrono
sidebar_position: 4
tags: [c++, fmt, custom-types, chrono, time]
---

# Chrono and time formatting

`std::chrono` types carry their units in the type system — a `std::chrono::milliseconds` knows it's
milliseconds — and `fmt/chrono.h` is what turns that into readable output without a round-trip
through `std::tm` and `strftime`.

## Durations

```cpp
#include <fmt/chrono.h>

fmt::print("{}\n", std::chrono::milliseconds(1500));  // 1500ms
fmt::print("{}\n", std::chrono::seconds(90));          // 90s
```

| Duration | Suffix |
|---|---|
| `std::chrono::nanoseconds` | `ns` |
| `std::chrono::microseconds` | `us` |
| `std::chrono::milliseconds` | `ms` |
| `std::chrono::seconds` | `s` |
| `std::chrono::minutes` | `min` |
| `std::chrono::hours` | `h` |

## strftime-style specs

A `strftime`-derived spec after the colon controls the presentation, and it applies to durations,
time points, and calendar types alike.

```cpp showLineNumbers title="timestamp.cpp"
auto now = std::chrono::system_clock::now();
fmt::print("{:%Y-%m-%d %H:%M:%S}\n", now);   // 2026-08-07 14:32:05
fmt::print("{:%H:%M}\n", now);                // 14:32
```

## The flag table

| Flag | Meaning |
|---|---|
| `%Y` | 4-digit year |
| `%m` | Month, zero-padded (01-12) |
| `%d` | Day of month, zero-padded (01-31) |
| `%H` | Hour, 24h, zero-padded |
| `%M` | Minute, zero-padded |
| `%S` | Second, zero-padded (with sub-second precision if requested) |
| `%F` | Equivalent to `%Y-%m-%d` |
| `%T` | Equivalent to `%H:%M:%S` |
| `%z` | UTC offset |
| `%Z` | Time zone abbreviation |
| `%j` | Day of year, zero-padded |
| `%p` | AM/PM designator |

## Sub-second precision

`%S` on a duration whose period is finer than a second includes the fractional part automatically;
`.N` after the spec controls how many fractional digits are shown, the same as float precision
elsewhere in the mini-language.

```cpp
fmt::print("{:%S}\n", std::chrono::milliseconds(1234));  // 01.234
```

## Time zones

:::danger[system_clock::time_point formats as UTC — there is no implicit local-time conversion]
`fmt::format("{:%H:%M}", std::chrono::system_clock::now())` prints the UTC wall-clock time, not the
local one. Nothing about a bare `time_point` implies a time zone; fmt formats the value it was given.
:::

For local or named-zone output, convert to a C++20 `std::chrono::zoned_time` first — fmt formats
`zoned_time` with the zone's offset and abbreviation applied, using the same spec letters.

## Cost

Chrono formatting is markedly heavier than integer or float formatting: it involves calendar
arithmetic, not just digit conversion.

:::tip[In a hot logging path, format the timestamp once per line, not once per field]
If a log line has a timestamp plus several other chrono-derived fields, compute and format the
timestamp string once and reuse it, rather than re-deriving it (and re-paying the calendar
arithmetic) per field. See
[Performance characteristics](../06-performance-and-best-practices/performance-characteristics.md)
for where this cost sits relative to the rest of fmt.
:::

## See also

- <Icon icon="lucide:shapes" inline /> [formatter specialization](./formatter-specialization.md) — how chrono's own formatters are built, as a model for your own time-like types.
- <Icon icon="lucide:list" inline /> [Ranges, tuples and containers](./ranges-tuples-and-containers.md) — the other major `fmt/*.h` extension header.
- <Icon icon="lucide:braces" inline /> [Format spec syntax](../02-format-spec-mini-language/format-spec-syntax.md) — how the `%`-flags interact with the general grammar.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
