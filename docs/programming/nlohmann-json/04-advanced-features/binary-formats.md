---
id: binary-formats
title: Binary formats
sidebar_label: Binary formats
sidebar_position: 2
tags: [c++, nlohmann-json, cbor, messagepack, bson]
---

# Binary formats

CBOR, MessagePack, BSON, UBJSON, and BJData all describe the same data model JSON does — the same
nulls, booleans, numbers, strings, arrays, and objects — just encoded as bytes instead of text.
When the JSON text overhead (quoting, whitespace, decimal number formatting) is the actual cost
you're paying, one of these is usually the fix, and nlohmann/json round-trips through all of them
using the same `json` value.

## The formats

| Format | to_/from_ | Typical size vs JSON | Notable feature |
|---|---|---|---|
| CBOR | `to_cbor` / `from_cbor` | ~10-30% smaller | RFC 8949 standard, tag support for extended types |
| MessagePack | `to_msgpack` / `from_msgpack` | ~15-30% smaller | Wide cross-language tooling and library support |
| BSON | `to_bson` / `from_bson` | Varies, often larger for small docs | MongoDB's native wire format |
| UBJSON | `to_ubjson` / `from_ubjson` | ~10-25% smaller | Optional "optimized container" mode for homogeneous arrays |
| BJData | `to_bjdata` / `from_bjdata` | Similar to UBJSON | UBJSON-compatible extension with added numeric types |

## Round-tripping

Every format follows the same shape — a `to_*` free function producing a `std::vector<uint8_t>`,
and a matching `from_*` consuming one:

```cpp showLineNumbers
json j = {{"name", "ada"}, {"age", 36}};

std::vector<uint8_t> encoded = json::to_cbor(j);
json decoded = json::from_cbor(encoded);

assert(decoded == j);
```

Swapping `cbor` for `msgpack`, `bson`, `ubjson`, or `bjdata` in both calls is the entire difference
between formats — the rest of your code doesn't change.

## The binary value type

None of these formats are pure supersets of JSON — CBOR, MessagePack, and friends can natively
represent raw byte strings, which JSON has no syntax for at all. Round-tripping a byte string
through one of these formats produces a `json` value of type `value_t::binary`, constructed
explicitly via `json::binary(...)` and optionally tagged with a subtype number.

:::danger[dump() throws on a binary value]
A `json` holding a `value_t::binary` value has no JSON text representation — calling `.dump()` on it
(or on any structure containing it) throws `type_error`. If a document might contain binary values,
either keep it in one of the binary formats end-to-end, or convert the binary payload to a JSON-safe
encoding (base64, hex) before mixing it into a document you intend to `dump()`.
:::

## Format-specific gotchas

- **BSON** requires the top-level value to be an object — `to_bson` on a `json` array or scalar
  throws — and it rejects certain key shapes MongoDB's format doesn't support (keys can't contain
  a literal `\0`, for instance).
- **UBJSON**'s "optimized container" mode (enabled via a `to_ubjson` parameter) can significantly
  shrink homogeneous arrays by writing the element type and count once instead of per-element, but
  it only kicks in when every element in the array is actually the same type.
- **CBOR** tag handling on read is limited to what the library recognizes; unrecognized tags on
  decode are generally passed through as best-effort rather than causing a hard failure, so don't
  assume an unfamiliar CBOR document round-trips losslessly through `from_cbor`/`to_cbor` if it uses
  tags the library doesn't specifically understand.

## Choosing one

:::note[Default to CBOR unless something on the wire demands otherwise]
CBOR is an RFC standard (8949), supports tagged/extended types cleanly, and has broad tooling
support across languages — it's a safe default when you control both ends of the wire. Reach for
MessagePack if you're integrating with a system that already speaks it, and for BSON specifically
when the destination is MongoDB. UBJSON/BJData are narrower niches, useful mainly when you need their
specific optimized-container behavior for numeric-heavy arrays.
:::

## See also

- <Icon icon="lucide:printer" inline /> [Serialization and dumping](../01-basics/serialization-and-dumping.md) — the text-based counterpart to these formats.
- <Icon icon="lucide:radio" inline /> [The SAX interface](./sax-interface.md) — parsing these formats without building a DOM.
- <Icon icon="lucide:gauge" inline /> [Performance and best practices](../05-numbers-memory-and-performance/performance-and-best-practices.md) — using a binary format as a parse-side optimization.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
