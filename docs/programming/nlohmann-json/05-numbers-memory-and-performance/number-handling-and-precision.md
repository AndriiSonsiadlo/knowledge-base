---
id: number-handling-and-precision
title: Number handling and precision
sidebar_label: Numbers
sidebar_position: 1
tags: [c++, nlohmann-json, numbers, precision]
---

# Number handling and precision

JSON has exactly one number type — an arbitrary-precision decimal, syntactically. C++ has several,
each with a bounded range and its own precision characteristics. The mapping between them is where
this library's silent data loss lives, and it's worth understanding before it surprises you in
production.

## Three internal number types

| `value_t` | Default C++ type | Chosen when |
|---|---|---|
| `number_integer_t` | `int64_t` | The literal has no `.`/`e` and fits in a signed 64-bit range |
| `number_unsigned_t` | `uint64_t` | The literal has no `.`/`e`, is non-negative, and exceeds the signed 64-bit range |
| `number_float_t` | `double` | The literal has a `.` or exponent, or an integer literal that doesn't fit either integer type |

## Parse-time type selection

```cpp showLineNumbers
for (auto text : {"1", "-1", "1.0", "1e2"}) {
    json j = json::parse(text);
    std::cout << text << " -> " << j.type_name() << "\n";
}
// 1   -> number
// -1  -> number
// 1.0 -> number
// 1e2 -> number
```

`type_name()` reports `"number"` for all three internal kinds — the distinction only shows up via
`is_number_integer()` / `is_number_unsigned()` / `is_number_float()`. `1` and `1.0` end up in
different internal storage (`number_integer_t` vs `number_float_t`) despite `json::parse("1") ==
json::parse("1.0")` evaluating to `true`, because equality compares numeric value, not storage kind.

## Integers that don't fit

:::danger[Integers beyond int64_t/uint64_t silently become double]
A JSON integer literal larger than `UINT64_MAX` (about 1.8 × 10^19) has nowhere left to go in the
default `basic_json` — the parser falls back to storing it as `number_float_t`, silently losing
precision in the process:

```cpp
json j = json::parse("18446744073709551616");  // 2^64, one past uint64_t's max
// stored as a double — the exact integer value is now unrecoverable
```

There's no warning and no exception; `j.dump()` will print *a* number, just not necessarily the one
that was in the input. If a field might legitimately carry integers beyond 64 bits (large IDs from
some external system, arbitrary-precision computation results), don't trust round-tripping through
`json` — see "Big numbers" below.
:::

## Float round-tripping

Floating-point values dump using a shortest-round-trip algorithm, so `json::parse(j.dump()) == j`
holds for ordinary finite doubles. `NaN` and `Inf` are the exception:

:::danger[NaN and Inf dump as null]
JSON's grammar has no representation for `NaN` or infinity — there's no token for it. `dump()`
handles both by emitting `null` instead of throwing, which means a document containing `NaN` or
`Inf` does **not** round-trip: parsing the dumped output back gives you `null`, not the original
value. If a computed value might be `NaN`/`Inf` and that distinction matters downstream, check for
it and encode it explicitly (a string sentinel, a separate boolean flag) before it reaches `dump()`.
:::

## Customising the number types

`basic_json`'s template parameter list includes `NumberIntegerType`, `NumberUnsignedType`, and
`NumberFloatType` — instantiating your own alias lets you widen (or narrow) any of the three
independently, for example using `long double` instead of `double` where the platform supports
meaningfully more precision. See
[Custom allocators and JSON types](./custom-allocators-and-json-types.md) for the full parameter
list and a worked custom instantiation.

## Big numbers

For values that need more range or precision than any of the three number kinds can hold — 128-bit
IDs, arbitrary-precision decimals, currency amounts where floating-point rounding is unacceptable —
the practical answer isn't a wider number type, it's not using JSON's number type at all: store the
value as a JSON string and convert on the way in and out with a custom `adl_serializer`. See
[adl_serializer and template types](../03-custom-type-conversion/adl_serializer-and-templates.md)
for the pattern.

## See also

- <Icon icon="lucide:sliders" inline /> [Custom allocators and JSON types](./custom-allocators-and-json-types.md) — widening the number types via `basic_json`'s template parameters.
- <Icon icon="lucide:printer" inline /> [Serialization and dumping](../01-basics/serialization-and-dumping.md) — where the round-trip guarantees (and their exceptions) come from.
- <Icon icon="lucide:git-merge" inline /> [Merging and comparison](../02-accessing-and-modifying/merging-and-comparison.md) — how numeric equality is defined across the three storage kinds.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
