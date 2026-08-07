---
id: serialization-and-dumping
title: Serialization and dumping
sidebar_label: Serialization
sidebar_position: 4
tags: [c++, nlohmann-json, serialization, dump]
---

# Serialization and dumping

`dump()` is the inverse of `parse()` — it turns a `json` value back into text — and its defaults
are chosen for machines rather than humans: compact, no indentation, non-ASCII bytes passed
through as UTF-8 rather than escaped.

## dump() and its parameters

The full signature is:

```cpp
std::string dump(int indent = -1,
                  char indent_char = ' ',
                  bool ensure_ascii = false,
                  error_handler_t error_handler = error_handler_t::strict) const;
```

```cpp
json j = {{"name", "ada"}, {"skills", {"math", "engines"}}};

j.dump();          // compact — no indent argument
j.dump(2);          // pretty-printed, 2-space indent
j.dump(4, ' ', true);  // 4-space indent, non-ASCII escaped as \uXXXX
```

```json
{"name":"ada","skills":["math","engines"]}
```

```json
{
  "name": "ada",
  "skills": [
    "math",
    "engines"
  ]
}
```

## Streaming out

`operator<<` writes a `json` to any `std::ostream`, and combining it with `std::setw` triggers
pretty-printing the same way an explicit `dump(n)` would:

```cpp
std::cout << j;                    // compact, same as j.dump()
std::cout << std::setw(4) << j;    // pretty-printed with 4-space indent
```

:::tip[std::setw is how you pretty-print to a stream]
`std::setw` is normally a field-width manipulator for numeric/string output; nlohmann/json
repurposes it here specifically for `json`'s stream `operator<<` to mean "indent width." It only
affects the next `<<` of a `json` value — it doesn't linger on the stream the way it would for other
types.
:::

## Invalid UTF-8

JSON text is required to be valid UTF-8. If a `json` string was populated from a source that wasn't
— a legacy Latin-1 file, corrupted input, a buggy upstream service — dumping it has to decide what
to do with the invalid bytes, controlled by the `error_handler` parameter:

- `error_handler_t::strict` (the default) throws `type_error.316`.
- `error_handler_t::replace` substitutes the Unicode replacement character (`U+FFFD`) for each
  invalid sequence and continues.
- `error_handler_t::ignore` drops the invalid bytes silently and continues.

:::danger[Don't silently swallow invalid UTF-8 by default]
`replace` and `ignore` are useful escape hatches for genuinely best-effort output, but reaching for
them as a way to avoid handling the `type_error.316` exception hides a real data-quality problem —
a string that isn't valid UTF-8 got into your `json` document somewhere upstream, and dumping is
just the first place that becomes visible. Validate or transcode at the boundary where the data
enters the system instead of at the boundary where it leaves.
:::

## Number round-tripping

Floating-point numbers are dumped using a shortest-round-trip algorithm: the printed decimal is the
shortest string that, when parsed back, produces the exact same `double`. That means `dump()` won't
necessarily print a number the way you'd naively expect (`0.1` prints as `0.1`, not
`0.1000000000000000055511151231257827021181583404541015625`), but it does guarantee that
`json::parse(j.dump()) == j` holds for the numeric fields. See
[Number handling and precision](../05-numbers-memory-and-performance/number-handling-and-precision.md)
for the cases — very large integers, `NaN`/`Inf` — where round-tripping breaks down.

## See also

- <Icon icon="lucide:file-json" inline /> [Parsing JSON](./parsing-json.md) — the operation this one inverts.
- <Icon icon="lucide:box" inline /> [The JSON value type](./the-json-value-type.md) — what's actually being serialized.
- <Icon icon="lucide:binary" inline /> [Binary formats](../04-advanced-features/binary-formats.md) — serializing to CBOR/MessagePack/BSON instead of text.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
