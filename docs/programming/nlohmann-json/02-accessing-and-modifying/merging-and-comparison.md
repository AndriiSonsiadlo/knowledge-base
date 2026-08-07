---
id: merging-and-comparison
title: Merging and comparison
sidebar_label: Merging
sidebar_position: 5
tags: [c++, nlohmann-json, merge, comparison]
---

# Merging and comparison

"Combine two documents" turns out to mean three different, non-interchangeable operations in this
library, and picking the wrong one silently produces the wrong document rather than failing loudly.

## update()

`update()` performs a shallow key overwrite: keys present in the argument overwrite keys in the
receiver, keys only in the receiver are left alone, and (since 3.10) an optional second argument
enables recursive merging into nested objects instead of overwriting them wholesale.

```cpp
json base = {{"a", 1}, {"b", {{"x", 1}, {"y", 2}}}};
json patch = {{"b", {{"y", 99}}}, {"c", 3}};

base.update(patch);                 // shallow: base["b"] is REPLACED entirely by patch["b"]
// base == {"a":1, "b":{"y":99}, "c":3}   — base["b"]["x"] is gone

base.update(patch, /* recursive */ true);
// base["b"] is merged key-by-key instead of replaced
```

## merge_patch() (RFC 7386)

`merge_patch()` is a standardized recursive merge where a `null` value in the patch explicitly
*deletes* the corresponding key from the target — a semantic `update()` doesn't have:

```json
// target:  {"a": 1, "b": {"x": 1, "y": 2}}
// patch:   {"b": {"y": null}, "c": 3}
// result:  {"a": 1, "b": {"x": 1}, "c": 3}
```

```cpp
json result = target.merge_patch(patch);
```

## Comparison table

| | `update()` | `merge_patch()` | `patch()` |
|---|---|---|---|
| Recursion | Optional (3rd-party flag arg) | Always, into nested objects | N/A — applies discrete ops |
| Null handling | A `null` value is stored as-is | A `null` value **deletes** the key | Depends on the individual `op` |
| Input format | Another `json` object | Another `json` object (RFC 7386 shape) | A JSON Patch array (RFC 6902) |
| Typical use | Overlaying config defaults | Applying a partial update from a client | Precise, auditable, ordered edits |

## Equality and ordering

`operator==` compares two `json` values structurally: same type, same contents, recursively for
objects and arrays. The one caveat is numbers — `json(1) == json(1.0)` is `true`, because equality
compares numeric *value*, not which of the three number storage kinds each side happens to use.

`operator<` orders values first by `value_t` (so, for example, all numbers sort before all strings,
regardless of content) and then by value within the same type — this ordering exists mainly so
`json` can be used as a key in ordered containers like `std::set<json>`, not as a meaningful
domain ordering.

:::note[Object key order never affects equality]
Two objects with the same keys and values but inserted in a different order compare equal —
equality is defined over the set of key-value pairs, not the iteration order, regardless of whether
you're using `json` or `ordered_json`.
:::

## Discarded values

A `value_t::discarded` value — the marker `json::parse` returns when `allow_exceptions = false` and
parsing fails — participates in comparisons too, but its semantics changed in 3.11.

:::note[Version caveat: discarded-value comparison changed in 3.11]
Before 3.11, a discarded value compared equal to itself and to nothing else, inconsistently with how
other values behave. 3.11 tightened this; if your code depends on the pre-3.11 behaviour, define
`JSON_USE_LEGACY_DISCARDED_VALUE_COMPARISON` before including the header. New code shouldn't rely on
comparing discarded values at all — check `.is_discarded()` explicitly instead.
:::

## See also

- <Icon icon="lucide:map-pin" inline /> [JSON Pointer and JSON Patch](./json-pointer-and-patch.md) — `patch()` and `diff()`, referenced in the comparison table above.
- <Icon icon="lucide:pointer" inline /> [Element access](./element-access.md) — reading individual keys instead of merging whole documents.
- <Icon icon="lucide:box" inline /> [The JSON value type](../01-basics/the-json-value-type.md) — the `value_t` ordering `operator<` relies on.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
