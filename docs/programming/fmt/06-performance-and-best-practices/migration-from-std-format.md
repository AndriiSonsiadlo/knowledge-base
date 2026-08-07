---
id: migration-from-std-format
title: Migration between fmt and std::format
sidebar_label: Migration
sidebar_position: 3
tags: [c++, fmt, migration, std-format]
---

# Migration between fmt and std::format

The two APIs are close enough that migration is mostly mechanical in either direction — the
interesting part is the short list of things that don't port.

## Mechanical mapping

| fmt | std | Notes |
|---|---|---|
| `fmt::format` | `std::format` | Same signature, same spec grammar |
| `fmt::format_to` | `std::format_to` | Same signature |
| `fmt::format_to_n` | `std::format_to_n` | Same signature |
| `fmt::formatted_size` | `std::formatted_size` | Same signature |
| `fmt::print` | `std::print` | `std::print` needs C++23, not just C++20 |
| `fmt::formatter<T>` | `std::formatter<T>` | Same `parse`/`format` shape, different namespace |
| `fmt::runtime` | `std::runtime_format` | Same purpose, different name |

## What does not port from fmt to std

- **Named arguments** — see [Positional and named arguments](../01-basics/positional-and-named-arguments.md); `std::format` has no equivalent syntax.
- **`fmt::join`** — see [Ranges, tuples and containers](../03-formatting-custom-types/ranges-tuples-and-containers.md); the standard's built-in range formatting covers some of the same ground but is less flexible about separators and per-element specs.
- **Color and styles** — see [Color and text styles](../05-advanced-features/color-and-text-styles.md); no standard equivalent exists.
- **The ostream bridge** — see [ostream fallback formatting](../03-formatting-custom-types/ostream-fallback-formatting.md); `std::format` requires a real `std::formatter<T>` for every type.
- **`FMT_STRING`** — not needed for `std::format`, since C++20's `consteval` checking is unconditional there.
- **Printing to a `FILE*`** — `fmt::print(FILE*, ...)` has no standard counterpart; `std::print` targets a `std::ostream`/`stdout` only.

## What does not port from std to fmt

Very little. Code written against `std::format` moves to fmt by changing the header and namespace —
`std::format` becomes `fmt::format`, `<format>` becomes `<fmt/format.h>` — with no feature gap in that
direction, since fmt is a superset in practice.

## Code that compiles against both

An alias header lets application code call one name and pick the backend behind a feature-test macro.

```cpp showLineNumbers title="format_compat.hpp"
#if defined(__cpp_lib_format)
    #include <format>
    namespace fmtc = std;
#else
    #include <fmt/format.h>
    namespace fmtc = fmt;
#endif
```

Only the common subset — `fmtc::format`, `fmtc::format_to`, and so on — is usable through an alias
like this; reaching for a fmt-only feature breaks portability to the `std` branch immediately.

## Custom formatters

A `formatter<T>` written for one is nearly source-compatible with the other — the `parse`/`format`
signatures match closely; only the namespace differs.

:::tip[Write the formatter body once and specialize both templates from a shared implementation]
```cpp
struct point_formatter_impl {
    constexpr auto parse(auto& ctx) { return ctx.begin(); }
    auto format(const Point& p, auto& ctx) const {
        return fmt::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};
template <> struct fmt::formatter<Point> : point_formatter_impl {};
template <> struct std::formatter<Point> : point_formatter_impl {};
```
:::

## Which to prefer

:::note[Use std::format when your minimum toolchain supports it and you need nothing on the fmt-only list; otherwise use fmt and don't feel bad about it]
`std::format` wins on "one fewer dependency" alone when it's available and sufficient. The moment you
need named arguments, `fmt::join`, color output, or support for a toolchain without `std::format`,
reach for fmt — it's the reference implementation, not a downgrade. See
[Relationship to std::format](../00-overview/relationship-to-std-format.md) for the full comparison.
:::

## See also

- <Icon icon="lucide:git-branch" inline /> [Relationship to std::format](../00-overview/relationship-to-std-format.md) — the lineage and feature comparison behind this migration guide.
- <Icon icon="lucide:triangle-alert" inline /> [Common pitfalls](./common-pitfalls.md) — pitfalls that apply on both sides of a migration.
- <Icon icon="lucide:shapes" inline /> [formatter specialization](../03-formatting-custom-types/formatter-specialization.md) — the full detail behind the shared-implementation pattern above.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
