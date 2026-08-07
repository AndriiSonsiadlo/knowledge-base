---
id: performance-characteristics
title: Performance characteristics
sidebar_label: Performance
sidebar_position: 1
tags: [c++, fmt, performance, benchmarks]
---

# Performance characteristics

fmt is fast for structural reasons, not micro-optimizations — knowing which ones lets you tell when
you're paying for something you didn't actually need.

## Where the speed comes from

- **Format string parsed at compile time** — for a literal, the spec grammar is validated and largely
  resolved before the program runs, so there's no runtime string-scanning overhead per call.
- **No virtual dispatch per argument** — arguments are handled through templates and type erasure at
  the call boundary, not through a chain of virtual `operator<<` calls the way iostreams work.
- **No locale lookup by default** — see [Numeric grouping and locales](../02-format-spec-mini-language/numeric-grouping-and-locales.md); the common case skips the locale machinery entirely.
- **Small-buffer output** — short results are built in inline stack storage, avoiding a heap
  allocation for the common case of a short formatted string.
- **Dragonbox-class float formatting** — fmt uses a fast shortest-round-trip float-to-string
  algorithm, markedly quicker than the naive `sprintf`-style approach.
- **No per-argument allocation** — arguments are passed by reference and type-erased once per call,
  not boxed individually.

## Rough shape of the numbers

| Operation | sprintf | iostreams | fmt | std::format |
|---|---|---|---|---|
| Format an int | Baseline | Slower | Faster than sprintf | Close to fmt, implementation-dependent |
| Format a float | Baseline | Slower | Faster than sprintf | Close to fmt, implementation-dependent |
| Format a string | Baseline | Slower | Comparable to sprintf | Close to fmt |

:::note[Treat published formatting benchmarks as directional — measure on your compiler, standard library and workload before acting on them]
The relative ordering above (fmt and `std::format` both ahead of iostreams, fmt at or ahead of
`sprintf`) is consistently reproduced across published benchmarks, but exact multipliers depend
heavily on compiler, standard library implementation, and optimization flags. Don't act on a number
you haven't reproduced on your own build.
:::

## Binary size

fmt is usually smaller than iostreams-based formatting in the same codebase, because it avoids
instantiating a templated stream `operator<<` per formatted type across every translation unit that
uses it. Whether that advantage is fully realized depends on the build mode — see
[Header-only vs compiled mode](./header-only-vs-compiled-mode.md) for how compiled mode avoids
duplicating the implementation across translation units.

## What actually costs you

| Pattern | Cost | Cheaper alternative |
|---|---|---|
| `std::cout << fmt::format(...)` | An allocation you then copy into the stream | `fmt::print(...)` writes directly |
| Formatting into a discarded `std::string` | An allocation for a value nobody keeps | `fmt::format_to` into a reused buffer |
| Chrono formatting in an inner loop | Calendar arithmetic, heavier than integer formatting | Format the timestamp once per line, reuse it |
| Locale-aware output (`{:L}`) | Locale lookup and grouping logic | Skip `L` unless the output is actually locale-sensitive |
| Constructing a fresh `memory_buffer` per call in a hot loop | Repeated setup, possibly repeated heap growth | Reuse one buffer and `clear()` it between iterations |

## Measuring

Format the same payload many times in a loop against a no-op baseline (a loop that does the same
argument setup but skips the format call) to isolate formatting cost from everything else in the
benchmark. Compile-time cost is a separate axis entirely and should be measured separately — see
[Header-only vs compiled mode](./header-only-vs-compiled-mode.md).

## See also

- <Icon icon="lucide:triangle-alert" inline /> [Common pitfalls](./common-pitfalls.md) — the mistakes that erase these performance advantages.
- <Icon icon="lucide:database" inline /> [memory_buffer and buffered output](../05-advanced-features/memory-buffer-and-buffered-output.md) — the low-allocation buffer behind several of the "cheaper alternative" entries above.
- <Icon icon="lucide:arrow-right" inline /> [Output iterators and format_to](../05-advanced-features/output-iterators-and-format_to.md) — avoiding the throwaway-string pattern.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
