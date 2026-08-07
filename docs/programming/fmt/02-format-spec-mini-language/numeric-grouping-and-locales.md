---
id: numeric-grouping-and-locales
title: Numeric grouping and locales
sidebar_label: Locales
sidebar_position: 5
tags: [c++, fmt, format-spec, locale]
---

# Numeric grouping and locales

fmt is locale-independent by default, and that is a feature, not an oversight — you opt in to
locale-dependent output exactly where a human is going to read it, and nowhere else.

## The locale specifier

The `L` flag applies the active locale's digit grouping and decimal separator to a number.

```cpp showLineNumbers
fmt::format(std::locale("en_US.UTF-8"), "{:L}", 1234567);   // "1,234,567"
fmt::format(std::locale("de_DE.UTF-8"), "{:L}", 1234567.5);  // "1.234.567,5"
```

## Default is locale-independent

:::tip[Locale-independence by default is why fmt output is safe to write to files, wire formats and logs]
`fmt::format("{}", 1234567)` always produces `1234567`, regardless of what locale the process has set
globally. That's exactly what you want for anything machine-read back later — a CSV column, a JSON
number, a log line a parser scans.
:::

## The trap

:::danger[A global locale change silently alters every locale-aware format — including one in a file your parser reads back]
`std::locale::global(...)` affects every subsequent `{:L}` format in the process. A library that
changes the global locale for its own reasons can silently break formatting elsewhere in the same
binary that happens to use `L`. Prefer passing an explicit `std::locale` to the call site over relying
on whatever the global locale happens to be.
:::

## Comparison table

| | printf | iostreams | fmt |
|---|---|---|---|
| Default locale sensitivity | Locale-dependent (`printf` respects the C locale) | Locale-dependent (stream's imbued locale) | Locale-independent |
| Opting in | `setlocale` — process-global | `stream.imbue(locale)` — per stream | `{:L}` with an explicit or global `std::locale` — per call |
| Opting out | Reset with `setlocale(LC_ALL, "C")` | `stream.imbue(std::locale::classic())` | Default behavior — nothing to opt out of |

## Availability

Locale support lives behind `<fmt/format.h>` and pulls in `<locale>`. Embedded and other
size-constrained builds sometimes disable full locale support and fall back to a compile-time-fixed
thousands separator via `FMT_STATIC_THOUSANDS_SEPARATOR`.

:::note[Check whether your target even has locale support before relying on the L specifier]
Some embedded toolchains ship a minimal C library without locale facilities at all. If `{:L}` is load
bearing, confirm it on the actual target toolchain, not just on desktop.
:::

## See also

- <Icon icon="lucide:hash" inline /> [Sign and numeric precision](./sign-and-numeric-precision.md) — the numeric formatting `L` builds on.
- <Icon icon="lucide:braces" inline /> [Format spec syntax](./format-spec-syntax.md) — where `L` sits in the full grammar.
- <Icon icon="lucide:languages" inline /> [Unicode and encoding notes](../05-advanced-features/unicode-and-encoding-notes.md) — the other place locale-adjacent surprises show up.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
