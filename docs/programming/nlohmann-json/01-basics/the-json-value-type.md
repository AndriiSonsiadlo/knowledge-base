---
id: the-json-value-type
title: The JSON value type
sidebar_label: The value type
sidebar_position: 3
tags: [c++, nlohmann-json, value-type, basics]
---

# The JSON value type

`json` is one C++ type that behaves like several types at runtime — a tagged union with container
semantics layered on top. Every operation on it starts by asking, implicitly or explicitly, "what
kind of value is this right now?"

## The value types

| `value_t` | JSON type | Default C++ storage |
|---|---|---|
| `null` | `null` | (no payload) |
| `boolean` | `true` / `false` | `bool` |
| `number_integer` | number | `int64_t` |
| `number_unsigned` | number | `uint64_t` |
| `number_float` | number | `double` |
| `string` | string | `std::string` |
| `array` | array | `std::vector<json>` |
| `object` | object | `std::map<std::string, json>` |
| `binary` | (no JSON equivalent) | `std::vector<uint8_t>` with an optional subtype |
| `discarded` | (parse failure marker) | — |

`number_integer`, `number_unsigned`, and `number_float` are three distinct internal states even
though JSON itself has only one number type — see
[Number handling and precision](../05-numbers-memory-and-performance/number-handling-and-precision.md)
for how the parser picks between them.

## The type state machine

A default-constructed `json` starts as `null`, and its type is decided the first time it's used —
after that, most operations are only legal if they match the current type.

```mermaid
flowchart LR
    N[null] -->|"j[\"k\"] = ..."| O[object]
    N -->|push_back / j[0] = ...| A[array]
    N -->|j = 42| I[number]
    N -->|j = \"s\"| S[string]
    O -.->|push_back on an object| E1[type_error]
    A -.->|j[\"k\"] on an array| E2[type_error]
    I -.->|j.push_back on a number| E3[type_error]
```

A `null` value is permissive — assigning a key into it turns it into an object, calling
`push_back` on it turns it into an array — but once it has committed to a type, operations that only
make sense for a different type throw `type_error` rather than silently coercing.

## Inspecting the type

`j.type()` returns the `value_t` enum value directly; `j.type_name()` returns a short string
(`"object"`, `"array"`, `"number"`, …); and the `is_*()` family of predicates (`is_object()`,
`is_array()`, `is_number()`, `is_null()`, and more specific variants like `is_number_integer()`)
covers the common checks without needing the enum at all. See
[Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md) for
the full predicate list and how they interact with extraction.

## json vs ordered_json vs custom basic_json

| | `json` | `ordered_json` | custom `basic_json` |
|---|---|---|---|
| Key order | Sorted (via `std::map`) | Insertion order | Whatever `ObjectType` provides |
| Lookup cost | `O(log n)` | `O(n)` (linear scan) | Depends on `ObjectType` |
| When to reach for it | Default — machine-to-machine JSON | Human-diffable / order-sensitive output | Custom allocator, non-standard containers |

See [Custom allocators and JSON types](../05-numbers-memory-and-performance/custom-allocators-and-json-types.md)
for how `basic_json`'s ten template parameters let you go further than `ordered_json`.

## The binary value type

`value_t::binary` doesn't come from JSON text at all — plain JSON has no way to represent raw
bytes — it only appears when round-tripping through a binary format like CBOR or MessagePack that
supports a native byte-string type. See
[Binary formats](../04-advanced-features/binary-formats.md) for how it's produced and consumed.

## See also

- <Icon icon="lucide:plus" inline /> [Creating JSON values](./creating-json-values.md) — building values of each type.
- <Icon icon="lucide:file-json" inline /> [Parsing JSON](./parsing-json.md) — how parsed text maps onto these types.
- <Icon icon="lucide:check-circle" inline /> [Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md) — inspecting and extracting typed values.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
