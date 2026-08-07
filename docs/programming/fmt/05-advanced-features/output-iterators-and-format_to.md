---
id: output-iterators-and-format-to
title: Output iterators and format_to
sidebar_label: format_to
sidebar_position: 1
tags: [c++, fmt, advanced, output-iterators]
---

# Output iterators and format_to

`fmt::format` allocates a `std::string` that you often immediately throw away — append it to
something, write it to a socket, discard everything but its length. `format_to` writes straight into
whatever destination you already have, skipping that throwaway allocation.

## The signature

```cpp
template <typename OutputIt, typename... T>
OutputIt format_to(OutputIt out, format_string<T...> fmt, T&&... args);
```

It returns the iterator advanced past the last character written — useful for chaining several
`format_to` calls into the same destination.

## Appending to a string

```cpp showLineNumbers
std::string s;
fmt::format_to(std::back_inserter(s), "{}", x);
```

`std::back_inserter` is the most common destination: fmt appends through it exactly like any other
output iterator, so `s` grows the same way `push_back` would grow it.

```cpp showLineNumbers
std::string msg;
fmt::format_to(std::back_inserter(msg), "[{}] ", timestamp);
fmt::format_to(std::back_inserter(msg), "{}: ", level);
fmt::format_to(std::back_inserter(msg), "{}\n", body);
```

## Writing into a fixed array

`fmt::format_to_n` bounds the write to a fixed-size buffer and reports how much *would* have been
written, so you can detect truncation.

```cpp showLineNumbers title="fixed_buffer.cpp"
char buf[64];
auto result = fmt::format_to_n(buf, sizeof(buf) - 1, "{}: {}", key, value);
size_t written = std::min(result.size, sizeof(buf) - 1);
buf[written] = '\0';   // format_to_n never does this for you
if (result.size > sizeof(buf) - 1) {
    // the message was truncated — result.size is the length it needed
}
```

:::danger[format_to_n does not null-terminate — write the terminator yourself]
`format_to_n` treats the buffer as a plain character range, not a C string. Forgetting the manual
null terminator (as in the buffer size reserved above) is a classic off-by-one into undefined
behavior on whatever reads the buffer next.
:::

## Sizing first

`fmt::formatted_size` measures the output length without producing it, letting you allocate exactly
once instead of letting a growing buffer reallocate as it goes.

```cpp
size_t n = fmt::formatted_size("{}: {}", key, value);
std::string s(n, '\0');
fmt::format_to(s.data(), "{}: {}", key, value);
```

## Any output iterator

`format_to` works with anything satisfying the output iterator concept: `std::back_inserter` on a
`std::vector<char>`, `std::ostream_iterator<char>`, or a custom iterator whose `operator*` and
`operator++` write to a socket, a ring buffer, or a memory-mapped file.

## Comparison table

| | format | format_to | format_to_n | print |
|---|---|---|---|---|
| Allocation | Always (new string) | Depends on the iterator | Never | Never |
| Bounds | Unbounded | Unbounded (destination's responsibility) | Bounded, reports overflow | Unbounded |
| Return value | The `std::string` | The output iterator | Iterator + would-be size | `void` |
| Typical use | One-off string building | Appending into an existing buffer/container | Fixed-size buffers, no allocation allowed | Direct output to a stream |

## See also

- <Icon icon="lucide:database" inline /> [memory_buffer and buffered output](./memory-buffer-and-buffered-output.md) — fmt's own low-allocation destination for `format_to`.
- <Icon icon="lucide:list-ordered" inline /> [The format function family](../01-basics/the-format-function-family.md) — where `format_to` sits among the other entry points.
- <Icon icon="lucide:gauge" inline /> [Performance characteristics](../06-performance-and-best-practices/performance-characteristics.md) — why skipping the allocation matters on a hot path.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
