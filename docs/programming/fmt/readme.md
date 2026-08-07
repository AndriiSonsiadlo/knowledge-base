---
title: Overview of fmt
sidebar_label: Overview
sidebar_position: 1
tags: [c++, fmt]
---

# fmt Knowledge Base

fmt is a fast, type-safe formatting library with Python-style replacement fields — `{}` holes in a
string, filled by arguments checked at compile time wherever possible. It is not just "a formatting
library": it is the reference implementation that P0645 turned into C++20's `std::format`, and it
still ships features the standard hasn't caught up with, from named arguments to color output to
support on toolchains that don't have `std::format` at all.

:::info[How this is organised]
Roughly outside-in: **Overview → Basics** get you formatting strings today; the **Format spec
mini-language** is the reference you keep coming back to for every `{:...}` you write; **Custom
types** and **Compile-time checks** are what you need to use fmt across a real codebase instead of
just in a script; **Advanced features** and **Performance** are the allocation- and
throughput-sensitive corners you reach for once fmt is on a hot path.
:::

## Sections

|   | Section | What it covers |
|---|---------|----------------|
| <Icon icon="lucide:book-open" inline /> | [Overview](./00-overview/what-is-fmt.md) | What it is, installing it, its relationship to `std::format`, why not `printf` |
| <Icon icon="lucide:wrench" inline /> | [Basics](./01-basics/format-strings-and-arguments.md) | Replacement fields, the `format`/`print`/`format_to` family, named arguments |
| <Icon icon="lucide:ruler" inline /> | [Format Spec Mini-Language](./02-format-spec-mini-language/format-spec-syntax.md) | The full spec grammar: fill, align, sign, width, precision, type, locale |
| <Icon icon="lucide:shapes" inline /> | [Formatting Custom Types](./03-formatting-custom-types/formatter-specialization.md) | `fmt::formatter<T>`, the ostream bridge, ranges, `std::chrono` |
| <Icon icon="lucide:shield-check" inline /> | [Compile-Time Checks](./04-compile-time-checks/compile-time-format-string-checking.md) | `FMT_STRING`, `consteval` checking, reading the errors |
| <Icon icon="lucide:layers" inline /> | [Advanced Features](./05-advanced-features/output-iterators-and-format_to.md) | `format_to`, `memory_buffer`, color and styles, Unicode |
| <Icon icon="lucide:gauge" inline /> | [Performance & Best Practices](./06-performance-and-best-practices/performance-characteristics.md) | Where the speed comes from, build modes, migration, pitfalls |

## Suggested reading paths

```mermaid
flowchart LR
    O[Overview] --> B[Basics]
    B --> S[Format Spec]
    S --> C[Custom Types]
    C --> CT[Compile-Time Checks]
    S --> A[Advanced]
    A --> P[Performance]
```

- <Icon icon="lucide:rocket" inline /> **Coming from printf:** [Comparison with printf](./00-overview/comparison-with-printf-and-iostreams.md) → [Format strings](./01-basics/format-strings-and-arguments.md) → [Format spec syntax](./02-format-spec-mini-language/format-spec-syntax.md).
- <Icon icon="lucide:shapes" inline /> **Formatting your own types:** [formatter specialization](./03-formatting-custom-types/formatter-specialization.md) → [Ranges](./03-formatting-custom-types/ranges-tuples-and-containers.md) → [Compile-time checks](./04-compile-time-checks/compile-time-format-string-checking.md).
- <Icon icon="lucide:gauge" inline /> **Chasing allocations:** [format_to](./05-advanced-features/output-iterators-and-format_to.md) → [memory_buffer](./05-advanced-features/memory-buffer-and-buffered-output.md) → [Performance characteristics](./06-performance-and-best-practices/performance-characteristics.md).

## Quick reference

```cpp showLineNumbers title="the 90% of the API"
#include <fmt/format.h>
#include <fmt/ranges.h>

std::string s = fmt::format("{} scored {:.1f}", name, score);
fmt::print("{:>10} | {:<10}\n", left, right);          // aligned columns
fmt::print(stderr, "error: {}\n", msg);

fmt::memory_buffer buf;                                // no std::string allocation
fmt::format_to(std::back_inserter(buf), "{:08.3f}", x);

fmt::print("{}\n", std::vector{1, 2, 3});              // [1, 2, 3] via fmt/ranges.h
fmt::print("{}\n", fmt::join(v, ", "));                // 1, 2, 3
```

| Want | Spec |
|---|---|
| Right-align in 10 | `{:>10}` |
| Zero-pad to 8 | `{:08}` |
| 3 decimal places | `{:.3f}` |
| Hex, with `0x` | `{:#x}` |
| Binary | `{:b}` |
| Thousands separators | `{:L}` |
| Escape a brace | `{{` |
| Named argument | `fmt::format("{n}", fmt::arg("n", x))` |
