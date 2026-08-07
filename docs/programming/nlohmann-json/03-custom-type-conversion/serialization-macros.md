---
id: serialization-macros
title: Serialization macros
sidebar_label: Macros
sidebar_position: 2
tags: [c++, nlohmann-json, custom-types, macros]
---

# Serialization macros

Writing `to_json`/`from_json` by hand for a plain data struct is mostly boilerplate — list the
fields once and get both directions. The library's macros generate exactly that, and the four
variants differ in where they're placed and what happens when a key is missing on parse.

## The four macros

| Macro | Placed | Needs private access | Missing key on parse |
|---|---|---|---|
| `NLOHMANN_DEFINE_TYPE_INTRUSIVE` | Inside the class body | Yes | Throws `out_of_range` |
| `NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE` | At namespace scope, outside the class | No | Throws `out_of_range` |
| `NLOHMANN_DEFINE_TYPE_INTRUSIVE_WITH_DEFAULT` | Inside the class body | Yes | Keeps the default-constructed value |
| `NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT` | At namespace scope, outside the class | No | Keeps the default-constructed value |

## Intrusive

```cpp showLineNumbers
struct Point {
    int x;
    int y;

    NLOHMANN_DEFINE_TYPE_INTRUSIVE(Point, x, y)
};
```

Because the macro expands inside the class body, it can reach private members directly — useful if
`x`/`y` aren't public and you'd rather not expose them just to serialize the type.

## Non-intrusive

```cpp
struct Point {
    int x;
    int y;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Point, x, y)
```

The macro call sits at namespace scope, in the same namespace as `Point` (the same ADL requirement
as hand-written `to_json`/`from_json`), and only reaches members `Point` already exposes publicly.

## The _WITH_DEFAULT variants

:::tip[Use _WITH_DEFAULT for config structs]
The plain macros throw `out_of_range` the moment any listed field is missing from the input — fine
for strict data contracts, painful for a config struct where most fields should have sensible
defaults. The `_WITH_DEFAULT` variants instead leave a missing field at whatever the struct's own
default member initializer (or default constructor) set it to, so parsing a partial config document
against a struct with `int timeout = 30;` just keeps `30` rather than throwing.
:::

## Limits

The macros cover the common case — a flat list of public members that maps directly onto JSON keys
— and stop there. They don't support inheritance (base class members aren't picked up), field
renaming (the JSON key is always the C++ member name), `std::optional` special-casing (a missing
optional field still follows the same throw-or-default rule as any other field), and there's a
practical cap on how many members a single macro invocation can list.

:::note[Hand-write when you need renaming or versioning]
The moment a field needs a different JSON name than its C++ member name, or a document needs to
support multiple schema versions, the macros don't have a knob for that — drop down to
[to_json and from_json](./to_json-and-from_json.md) written by hand, which is exactly what the
macros expand into anyway.
:::

## Enums

`NLOHMANN_JSON_SERIALIZE_ENUM` maps an enum to and from a set of JSON values via an explicit table:

```cpp
enum class Color { Red, Green, Blue };

NLOHMANN_JSON_SERIALIZE_ENUM(Color, {
    {Color::Red, "red"},
    {Color::Green, "green"},
    {Color::Blue, "blue"},
})
```

:::danger[An unmatched value silently maps to the first pair]
If a JSON string doesn't match any entry in the table, `from_json` doesn't throw — it silently
resolves to the *first* enumerator listed. `json("purple").get<Color>()` quietly becomes
`Color::Red` rather than failing. List a deliberate "unknown" sentinel as the first pair if you want
unmatched values to be at least distinguishable from a real `Red`, and never rely on the first entry
being a safe default by accident.
:::

## See also

- <Icon icon="lucide:shuffle" inline /> [to_json and from_json](./to_json-and-from_json.md) — what these macros expand into.
- <Icon icon="lucide:layers" inline /> [adl_serializer and template types](./adl_serializer-and-templates.md) — for types the macros can't cover.
- <Icon icon="lucide:printer" inline /> [Serialization and dumping](../01-basics/serialization-and-dumping.md) — what happens after `to_json` runs.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
