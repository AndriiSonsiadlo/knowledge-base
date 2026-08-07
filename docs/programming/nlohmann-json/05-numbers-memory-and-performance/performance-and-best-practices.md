---
id: performance-and-best-practices
title: Performance and best practices
sidebar_label: Performance
sidebar_position: 3
tags: [c++, nlohmann-json, performance, best-practices]
---

# Performance and best practices

The library's defaults are tuned for ergonomics, not throughput, and most of the performance
problems people run into aren't the parser being slow — they're copies the value-semantics API
makes easy to write without noticing.

## Where the time goes

- **Parse** is allocation-heavy: every string, array, and object node in the document is a
  separate heap allocation, so parse time scales with document *structure*, not just byte count.
- **Access** is map lookups: `operator[]`/`.at()` on the default `json` walks a `std::map`, an
  `O(log n)` string comparison per level of nesting.
- **Dump** is string building: every value gets formatted and appended, with the shortest-round-trip
  float algorithm adding measurable cost for number-heavy documents.

## Avoiding copies

| Pattern | Copies | Better |
|---|---|---|
| `for (auto el : j)` | Copies every element | `for (auto& el : j)` — bind by reference |
| `j.get<std::string>()` in a hot loop | Copies the string out every call | `j.get_ref<const std::string&>()` — no copy, if lifetime allows |
| Passing `json` by value into a function | Deep-copies the whole document | Pass `const json&` unless the function needs to own a copy |

## Building large structures

Growing a `json` array via repeated `operator[]` assignment and via `push_back`/`emplace_back` are
not equivalent in cost — `operator[]` on an index past the current size resizes and fills every
intermediate slot with `null`, which for sequential growth means the array is repeatedly resized and
re-nulled rather than simply appended to:

```cpp showLineNumbers
json arr = json::array();

// slower: each iteration risks a resize-and-fill, and relies on
// sequential indices matching the array's current size exactly
for (int i = 0; i < 10000; ++i) {
    arr[i] = i;
}

// faster: push_back / emplace_back grow the underlying vector the
// same way std::vector::push_back does, with the same amortized cost
for (int i = 0; i < 10000; ++i) {
    arr.push_back(i);
}
```

## Parse-side wins

- Parse from a contiguous in-memory buffer (a `std::string` or `std::vector<uint8_t>`) rather than
  an `istream` where avoidable — stream-based parsing goes through an extra layer of buffering the
  library has to manage itself.
- Skip DOM construction entirely with the [SAX interface](../04-advanced-features/sax-interface.md)
  when you only need a subset of a large document.
- Put a [binary format](../04-advanced-features/binary-formats.md) on the wire instead of JSON text
  when both ends are under your control — decoding CBOR or MessagePack skips the text-tokenization
  step entirely.

## Compile-time cost

Every translation unit that includes the full `<nlohmann/json.hpp>` pays a real compile-time cost
for its ~25,000 lines of templates. Use `<nlohmann/json_fwd.hpp>` in headers that only name the
type, and keep the full header included in as few `.cpp` files as practical — the same discipline
covered in [Installation and integration](../00-overview/installation-and-integration.md).

## Pitfalls checklist

- Accidental auto-vivification from `operator[]` on a non-const object — see
  [Element access](../02-accessing-and-modifying/element-access.md).
- Iterating an object with a plain range-for and expecting key-value pairs instead of values only —
  see [Iterating JSON](../02-accessing-and-modifying/iterating-json.md).
- Relying on the implicit conversion operator in an ambiguous context (`auto`, overload resolution)
  — see [Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md).
- Assuming `NaN`/`Inf` round-trip through `dump()`/`parse()` — see
  [Number handling and precision](./number-handling-and-precision.md).
- Assuming integers beyond `int64_t`/`uint64_t` round-trip losslessly — see
  [Number handling and precision](./number-handling-and-precision.md).
- Holding a `get_ref`/`get_ptr` past the lifetime of the source `json` — see
  [Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md).
- Assuming key order is preserved without switching to `ordered_json` — see
  [Custom allocators and JSON types](./custom-allocators-and-json-types.md).

## When to switch libraries

:::note[If the profile is dominated by parse throughput, no tuning here beats simdjson]
Every technique on this page reduces overhead within nlohmann/json's own design — none of them
change the fact that it builds a fully allocated DOM. If a profile shows parse time as the actual
bottleneck at scale, that's a sign the workload has outgrown what this library optimizes for; see
[Comparison with alternatives](../00-overview/comparison-with-alternatives.md) for what to reach for
instead.
:::

## See also

- <Icon icon="lucide:radio" inline /> [The SAX interface](../04-advanced-features/sax-interface.md) — skipping DOM construction for large documents.
- <Icon icon="lucide:sliders" inline /> [Custom allocators and JSON types](./custom-allocators-and-json-types.md) — instantiation-level tuning beyond the defaults.
- <Icon icon="lucide:scale" inline /> [Comparison with alternatives](../00-overview/comparison-with-alternatives.md) — when to stop tuning and switch libraries.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
