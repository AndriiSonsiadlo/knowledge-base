---
id: memory-buffer-and-buffered-output
title: memory_buffer and buffered output
sidebar_label: memory_buffer
sidebar_position: 2
tags: [c++, fmt, advanced, buffers, allocation]
---

# memory_buffer and buffered output

`fmt::memory_buffer` is the container fmt itself uses internally to build formatted output — a small
inline buffer that lives on the stack and only reaches for the heap once the output outgrows it.

## What it is

`fmt::memory_buffer` is `basic_memory_buffer<char, 500>`: 500 bytes of inline storage, growing onto
the heap for anything larger, exactly like a small-string-optimized string but without `std::string`'s
null-termination guarantee.

```cpp showLineNumbers
fmt::memory_buffer buf;
fmt::format_to(std::back_inserter(buf), "{}: {}", key, value);
send(fd, buf.data(), buf.size());
```

## Not null-terminated

:::danger[memory_buffer::data() is not null-terminated — pass data() and size() together, or call fmt::to_string(buf)]
```cpp
write(fd, buf.data(), buf.size());   // correct — explicit length
puts(buf.data());                     // wrong — reads past the end looking for '\0'
std::string s = fmt::to_string(buf);  // correct — produces a proper null-terminated std::string
```
:::

## Choosing the inline size

`fmt::basic_memory_buffer<char, N>` lets you pick the inline capacity for a known-small message,
trading stack space for fewer heap allocations.

| Inline size | Stack cost | Allocates when |
|---|---|---|
| Default (500) | 500 bytes | Output exceeds 500 bytes |
| `128` (a typical log line) | 128 bytes | Output exceeds 128 bytes |
| `16` (a short status code) | 16 bytes | Output exceeds 16 bytes |

Size it to comfortably cover your typical output, not your worst case — an occasional heap allocation
for a long outlier is cheaper than reserving kilobytes of stack for every call.

## Reuse across calls

Calling `buf.clear()` between iterations of a loop reuses the same allocation (if the buffer already
grew onto the heap) instead of allocating fresh every time.

```cpp showLineNumbers title="log_loop.cpp"
fmt::memory_buffer buf;
for (const auto& entry : entries) {
    buf.clear();
    fmt::format_to(std::back_inserter(buf), "{}: {}\n", entry.key, entry.value);
    write_out(buf.data(), buf.size());
}
```

## Handing it to an API

Depending on what the consumer expects: `fmt::to_string(buf)` for a `std::string`,
`std::string_view(buf.data(), buf.size())` for a non-owning view, or `write(fd, buf.data(),
buf.size())` for a raw byte-oriented API.

## When not to bother

:::tip[If you are formatting once per HTTP request, fmt::format is fine — memory_buffer is for the inner loop]
The allocation `fmt::format` performs is a rounding error next to the cost of handling an HTTP
request. `memory_buffer`'s value shows up when you're formatting thousands or millions of times per
second — see
[Performance characteristics](../06-performance-and-best-practices/performance-characteristics.md)
for where allocation actually costs you and where it doesn't.
:::

## See also

- <Icon icon="lucide:arrow-right" inline /> [Output iterators and format_to](./output-iterators-and-format_to.md) — the general mechanism `memory_buffer` plugs into.
- <Icon icon="lucide:gauge" inline /> [Performance characteristics](../06-performance-and-best-practices/performance-characteristics.md) — when this optimization is and isn't worth reaching for.
- <Icon icon="lucide:list-ordered" inline /> [The format function family](../01-basics/the-format-function-family.md) — the full set of entry points `memory_buffer` complements.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
