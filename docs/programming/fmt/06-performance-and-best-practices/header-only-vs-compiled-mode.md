---
id: header-only-vs-compiled-mode
title: Header-only vs compiled mode
sidebar_label: Build modes
sidebar_position: 2
tags: [c++, fmt, build, compile-time]
---

# Header-only vs compiled mode

fmt's runtime cost is settled — it's fast, and that doesn't change based on how you build it. Its
compile-time cost is the one thing you still choose, and the choice is a single CMake target.

## The two modes

```cmake showLineNumbers title="CMakeLists.txt"
# Compiled: implementation built once into a library, linked by every TU.
find_package(fmt REQUIRED)
target_link_libraries(app PRIVATE fmt::fmt)

# Header-only: no build step, no link step, reinstantiated in every TU.
find_package(fmt REQUIRED)
target_link_libraries(app PRIVATE fmt::fmt-header-only)
```

`FMT_HEADER_ONLY` defined before including fmt's headers achieves the same thing without CMake, for
projects that vendor fmt directly.

## Comparison table

| | Header-only | Compiled |
|---|---|---|
| Compile time per TU | Higher — reinstantiated in every TU that formats anything | Lower — implementation built once |
| Link step | None | Requires linking `fmt::fmt` |
| Binary size | Larger as usage spreads across more TUs | Smaller — one implementation, shared |
| Ease of vendoring | Trivial — copy headers, no build step | Needs a build step or package manager |
| ABI stability across fmt versions | N/A — always rebuilt from source | A compiled fmt has an ABI surface that can shift between versions |

## Why compiled is usually right

With compiled mode, fmt's heavier internals (float formatting, the compile-time-checked machinery's
runtime fallback path) are instantiated once, in fmt's own translation units, instead of once per TU
that includes `<fmt/format.h>`.

:::tip[Default to the compiled library in any project with more than a handful of translation units]
Below a handful of TUs the difference is negligible either way, and header-only avoids a build step.
Past that, header-only compile time scales with translation-unit count, and the gap widens fast on a
project of real size.
:::

## Reducing instantiations

Keep the lightweight `<fmt/base.h>` in your own widely-included headers, and only reach for the heavy
`<fmt/format.h>` in the `.cpp` files that actually format something — this limits how many TUs pay
the parsing/instantiation cost of the full header at all. For code that's included very broadly (a
logging macro used everywhere, say), routing calls through the type-erased
[`vformat`](../01-basics/the-format-function-family.md) path avoids instantiating a fresh template
per call site.

## ODR hazards

:::danger[FMT_HEADER_ONLY defined in some TUs and not others is an ODR violation — set it project-wide or not at all]
If one translation unit defines `FMT_HEADER_ONLY` and another links against the compiled
`fmt::fmt` without it, the two disagree about symbol linkage for the same names. This is undefined
behavior at link or runtime, not a guaranteed error — pick one mode for the whole project and set it
consistently, ideally as a single CMake target everything links.
:::

The same hazard shows up with a vendored fmt inside spdlog running alongside your own external fmt —
see [Installation and integration](../00-overview/installation-and-integration.md) for the
`SPDLOG_FMT_EXTERNAL` fix.

## Measuring the difference

Build the same project in both modes and compare wall-clock build time (a clean build, not an
incremental one, since incremental builds hide the per-TU cost).

:::note[The gap grows with translation-unit count, not with call-site count]
A project with a hundred format calls in five files sees a small header-only penalty. The same
hundred calls spread across a hundred files sees a much larger one — the cost tracks how many times
fmt's implementation gets reinstantiated, which is a function of TU count, not call count.
:::

## See also

- <Icon icon="lucide:gauge" inline /> [Performance characteristics](./performance-characteristics.md) — the runtime side of fmt's cost, which build mode does not affect.
- <Icon icon="lucide:download" inline /> [Installation and integration](../00-overview/installation-and-integration.md) — the CMake setup this choice fits into, and the spdlog ODR case.
- <Icon icon="lucide:shield-check" inline /> [Compile-time format string checking](../04-compile-time-checks/compile-time-format-string-checking.md) — the other major contributor to per-call compile cost.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
