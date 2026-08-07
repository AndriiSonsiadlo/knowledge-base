---
id: the-format-function-family
title: The format function family
sidebar_label: Function family
sidebar_position: 2
tags: [c++, fmt, basics, api]
---

# The format function family

One formatting engine, several entry points that differ only in *where the characters land* — pick
the right one by destination, not by taste.

## The family

| Function | Writes to | Returns | Allocates |
|---|---|---|---|
| `fmt::format` | New `std::string` | The string | Yes, unless small-string-optimized |
| `fmt::print` | `stdout` | `void` | No |
| `fmt::print(FILE*, ...)` | Given C stream | `void` | No |
| `fmt::format_to` | Any output iterator | The iterator, past the last char | Depends on the iterator |
| `fmt::format_to_n` | Fixed-size buffer | Iterator + count that would have been written | No |
| `fmt::formatted_size` | Nothing | The size the output would need | No |
| `fmt::vformat` / `fmt::vformat_to` | String / iterator | Same as `format`/`format_to` | Same as `format`/`format_to` |

## format

The simple case: build a `std::string` and hand it back.

```cpp
std::string s = fmt::format("{}={}", key, value);
```

## print

Writes directly to a stream with no intermediate string allocation.

:::tip[fmt::print is faster than std::cout with fmt::format — it skips the string]
`fmt::print("{}\n", x)` formats straight into the destination's buffer. `` std::cout << fmt::format("{}\n", x) `` allocates a `std::string`, then copies it into the stream. If the only thing
you were going to do with the formatted string is print it, use `fmt::print`.
:::

## format_to

Appends through an output iterator instead of returning a fresh string — useful when you're building
up a larger buffer piece by piece.

```cpp showLineNumbers
std::string out;
fmt::format_to(std::back_inserter(out), "[{}] ", timestamp);
fmt::format_to(std::back_inserter(out), "{}: {}\n", level, message);
```

See [Output iterators and format_to](../05-advanced-features/output-iterators-and-format_to.md) for
the full range of iterators this works with, including fixed buffers and custom sinks.

## format_to_n

Writes into a fixed-size buffer, stopping at the bound, and reports both the iterator and the total
size the write *would* have needed.

:::danger[format_to_n truncates and reports the size it would have needed — check the returned size before trusting the buffer]
```cpp
char buf[16];
auto result = fmt::format_to_n(buf, sizeof(buf), "{}", long_string);
if (result.size > sizeof(buf)) {
    // truncated — buf holds only the first sizeof(buf) characters
}
```
:::

## formatted_size

Measures the output length without producing it, so you can allocate exactly once and then format
directly into that allocation instead of letting `format`/`format_to` grow a buffer incrementally.

```cpp
size_t n = fmt::formatted_size("{}", value);
std::string s(n, '\0');
fmt::format_to(s.data(), "{}", value);
```

## vformat and type erasure

`fmt::vformat`/`fmt::vformat_to` take a type-erased argument list built with
`fmt::make_format_args`, rather than a variadic parameter pack. They exist so a function can accept
"a format string and some arguments" without instantiating a fresh template for every distinct
combination of argument types at every call site — useful in a logging wrapper that's included
everywhere. The cost is a lifetime caveat: the erased argument list only refers to its arguments, so
it must not outlive the call that consumes it. See
[Common pitfalls](../06-performance-and-best-practices/common-pitfalls.md) for the failure mode.

## See also

- <Icon icon="lucide:type" inline /> [Format strings and arguments](./format-strings-and-arguments.md) — what goes inside the holes these functions fill.
- <Icon icon="lucide:arrow-right" inline /> [Output iterators and format_to](../05-advanced-features/output-iterators-and-format_to.md) — the full detail on `format_to` destinations.
- <Icon icon="lucide:database" inline /> [memory_buffer and buffered output](../05-advanced-features/memory-buffer-and-buffered-output.md) — fmt's own low-allocation buffer type.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
