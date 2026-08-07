---
id: common-pitfalls
title: Common pitfalls
sidebar_label: Pitfalls
sidebar_position: 4
tags: [c++, fmt, pitfalls, lifetime]
---

# Common pitfalls

Nearly every fmt bug that reaches production is a lifetime bug or a
format-string-from-a-variable bug. This page is the checklist to run a diff against before it ships.

## Dangling references in argument stores

:::danger[fmt::arg, fmt::join and dynamic_format_arg_store hold references — formatting them after the referenced object dies is undefined]
```cpp
auto bad() {
    std::vector<int> local = {1, 2, 3};
    return fmt::join(local, ",");   // dangling: local is destroyed on return
}

std::string good() {
    std::vector<int> local = {1, 2, 3};
    return fmt::format("{}", fmt::join(local, ","));  // formatted before local goes away
}
```
:::

## Returning format args

:::danger[Never store the result of fmt::make_format_args beyond the call it feeds]
The same reference-holding hazard applies to the type-erased argument list `vformat` consumes — it's
a view over its arguments, not an owning container, and outlives them only by accident.
:::

## A variable used as a format string

The compile-time check only applies to literals. A `std::string` used directly as a format string
needs [`fmt::runtime`](../04-compile-time-checks/compile-time-format-string-checking.md), and
untrusted input must never be used as the format string itself — only ever as an argument.

## Mixed automatic and manual indexing

`fmt::format("{} and {1}", a, b)` is rejected — a single format string commits to either `{}` or
`{N}` throughout. See [Format strings and arguments](../01-basics/format-strings-and-arguments.md).

## Width does not truncate

`{:5}` pads a short value up to width 5; it never cuts a longer value down. See
[Alignment, fill and width](../02-format-spec-mini-language/alignment-fill-and-width.md) for the
precision-based alternative that does truncate.

## format_to_n does not null-terminate

Writing into a fixed buffer with `format_to_n` and then treating it as a C string without adding the
terminator yourself is a read past the end. See
[Output iterators and format_to](../05-advanced-features/output-iterators-and-format_to.md).

## memory_buffer::data() is not null-terminated

The same hazard, one level down — `fmt::memory_buffer` is a plain character range, not a C string.
See [memory_buffer and buffered output](../05-advanced-features/memory-buffer-and-buffered-output.md).

## Color codes in redirected output

Color/style escape codes land literally in a file or pipe unless you check whether the destination is
a terminal first. See [Color and text styles](../05-advanced-features/color-and-text-styles.md).

## Two fmt versions in one binary

A project linking its own fmt alongside spdlog's vendored copy (without `SPDLOG_FMT_EXTERNAL`) has two
independent symbol sets for the same names — an ODR violation. See
[Installation and integration](../00-overview/installation-and-integration.md).

## Non-const formatter::format

A `formatter<T>::format` that isn't marked `const` compiles fine until someone formats a `const T&`,
at which point it fails to compile at the call site. See
[formatter specialization](../03-formatting-custom-types/formatter-specialization.md).

## Checklist

- Never let `fmt::arg`, `fmt::join`, or a `dynamic_format_arg_store` outlive the call that consumes them.
- Never store the result of `fmt::make_format_args` past the call it feeds.
- Wrap variable format strings in `fmt::runtime`, and never use untrusted input as a format string.
- Never mix automatic (`{}`) and manual (`{N}`) indexing in one string.
- Use precision, not width, to truncate a string.
- Null-terminate manually after `format_to_n` if the buffer is treated as a C string.
- Use `fmt::to_string(buf)` or pass `data()`+`size()` together for a `memory_buffer`, never `data()` alone.
- Check for a TTY before emitting color codes.
- Keep exactly one fmt implementation linked into a binary — set `SPDLOG_FMT_EXTERNAL` if spdlog is present.
- Mark every `formatter<T>::format` `const`.

## See also

- <Icon icon="lucide:gauge" inline /> [Performance characteristics](./performance-characteristics.md) — the throughput side of getting fmt usage right.
- <Icon icon="lucide:arrow-left-right" inline /> [Migration between fmt and std::format](./migration-from-std-format.md) — pitfalls that matter most when moving between the two.
- <Icon icon="lucide:bug" inline /> [Error diagnostics](../04-compile-time-checks/error-diagnostics.md) — reading the error each of these produces when it's caught.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
