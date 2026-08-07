---
id: format-spec-syntax
title: Format spec syntax
sidebar_label: Spec syntax
sidebar_position: 1
tags: [c++, fmt, format-spec, grammar]
---

# Format spec syntax

Everything after the `:` in a replacement field is one small grammar. Learn it once and it applies to
every type fmt knows how to format, including your own — a custom `formatter<T>` parses the same
mini-language.

## The grammar

```
[[fill]align][sign][#][0][width][.precision][L][type]
```

Every component is optional, and the ones present must appear in this order. An empty spec (`{}`)
just means "default presentation for this type."

## Component table

| Component | Values | Meaning | Page |
|---|---|---|---|
| `fill` + `align` | any char + `<` `>` `^` `=` | Pad character and alignment direction | [Alignment, fill and width](./alignment-fill-and-width.md) |
| `sign` | `-` `+` space | Which numbers get an explicit sign character | [Sign and numeric precision](./sign-and-numeric-precision.md) |
| `#` | present or absent | Alternate form: `0x`/`0b`/`0o` prefixes, always-a-decimal-point | [Sign and numeric precision](./sign-and-numeric-precision.md) |
| `0` | present or absent | Zero-pad to `width`, sign-aware | [Sign and numeric precision](./sign-and-numeric-precision.md) |
| `width` | integer or `{}` | Minimum field width | [Alignment, fill and width](./alignment-fill-and-width.md) |
| `.precision` | integer or `{}` | Decimal places (floats) or max length (strings) | [Sign and numeric precision](./sign-and-numeric-precision.md) |
| `L` | present or absent | Apply the active locale's grouping/decimal separator | [Numeric grouping and locales](./numeric-grouping-and-locales.md) |
| `type` | `d` `x` `f` `s` `?` ... | Presentation for this argument's type | [Type-specific presentation](./type-specific-presentation.md) |

## Reading a spec

```cpp showLineNumbers
fmt::format("{:*^12}", "hi");     // "*****hi*****"  — fill '*', center, width 12
fmt::format("{:+.3e}", 1234.5);   // "+1.235e+03"    — always sign, 3-digit precision, scientific
fmt::format("{:#010x}", 255);     // "0x000000ff"    — alternate form, zero-pad, width 10, hex
```

Reading `{:*^12}` component by component: fill is `*`, align is `^` (center), width is `12`, no
sign/precision/type given, so the type defaults to the argument's own default (string, unquoted).
`{:+.3e}` has no fill/align, sign is `+` (always shown), precision `3`, type `e` (scientific).
`{:#010x}` has the alternate form flag, zero-padding, width `10`, type `x` (lowercase hex) — the `#`
and `0x` prefix are what the `#` flag adds.

## Dynamic width and precision

Width and precision can come from an argument instead of being written literally, using a nested
`{}`. This is how you build a table with column widths computed at runtime.

```cpp
int width = 12;
fmt::format("{:{}}", "hi", width);        // width from the next argument
fmt::format("{:.{}}", 3.14159, 2);        // precision from the next argument: "3.14"
```

## Where the spec is parsed

The text after the `:` is handed to `formatter<T>::parse` for the argument's type — which is exactly
why a custom type can accept its own spec letters instead of being limited to the built-in grammar.
See [formatter specialization](../03-formatting-custom-types/formatter-specialization.md) for how
`parse` consumes this text.

## See also

- <Icon icon="lucide:move-horizontal" inline /> [Alignment, fill and width](./alignment-fill-and-width.md) — the layout half of the grammar.
- <Icon icon="lucide:list" inline /> [Type-specific presentation](./type-specific-presentation.md) — the reference table for the final `type` character.
- <Icon icon="lucide:type" inline /> [Format strings and arguments](../01-basics/format-strings-and-arguments.md) — the replacement fields this spec attaches to.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
