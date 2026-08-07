---
id: sign-and-numeric-precision
title: Sign and numeric precision
sidebar_label: Sign and precision
sidebar_position: 3
tags: [c++, fmt, format-spec, numbers]
---

# Sign and numeric precision

Sign and precision are where formatted numbers stop being an aesthetic choice and start being a
correctness one — a truncated price or a missing minus sign is a bug, not a style preference.

## Sign

| Spec | `42` | `-42` | Meaning |
|---|---|---|---|
| `-` (default) | `42` | `-42` | Sign only on negative numbers |
| `+` | `+42` | `-42` | Always show a sign |
| ` ` (space) | ` 42` | `-42` | Space reserved for positive numbers, aligning with negatives |

## The alternate form

The `#` flag changes the presentation of the value itself, not just its padding:

- Integers get their base prefix: `0x`/`0X` for hex, `0b`/`0B` for binary, `0o` for octal.
- Floats always show a decimal point, even with zero fractional digits (`{:#.0f}` on `5.0` gives
  `5.`, not `5`).

## Zero padding

`{:08}` zero-pads to a width of 8, and the padding is sign-aware — the zeros go between the sign and
the first digit, not before it.

:::danger[Zero-padding and an explicit fill/align cannot both apply — the explicit one wins]
```cpp
fmt::format("{:08}", -42);      // "-0000042" — zero padding, sign-aware
fmt::format("{:*>8}", -42);     // "*****-42" — explicit fill/align, zeros not implied
```
`0` is shorthand for "zero-fill, sign-aware pad." Writing an explicit fill character and alignment
overrides it entirely rather than combining with it.
:::

## Precision on floats

`.N` with `f`, `e`, or `g` controls decimal places differently per presentation:

| Spec | `3.14159` |
|---|---|
| `{:.2f}` | `3.14` |
| `{:.2e}` | `3.14e0` |
| `{:.2g}` | `3.1` |
| `{}` | `3.14159` (shortest round-trip) |

## Precision on strings

For strings, `.N` truncates to at most `N` characters instead of controlling decimal places.

:::tip[A precision spec bounds a string in a fixed column]
```cpp
fmt::format("{:.5}", "a very long string");  // "a ver"
```
Combine with a width to build a fixed-width, always-truncated column — see
[Alignment, fill and width](./alignment-fill-and-width.md) for the layout half.
:::

## Default float output

:::note[fmt's default float output round-trips exactly — printf's %g does not]
With no explicit precision, fmt prints the shortest decimal representation that reads back to the
exact same `double`. `printf`'s `%g` truncates to a fixed number of significant digits by default and
can lose precision silently.
:::

## Special values

`nan`, `inf`, and `-inf` print as those literal words. The sign spec still applies to `inf`: `{:+}`
on positive infinity prints `+inf`. `nan` has no sign to apply regardless of the sign spec.

## See also

- <Icon icon="lucide:list" inline /> [Type-specific presentation](./type-specific-presentation.md) — the presentation types precision and sign apply to.
- <Icon icon="lucide:braces" inline /> [Format spec syntax](./format-spec-syntax.md) — where sign and precision sit in the full grammar.
- <Icon icon="lucide:globe" inline /> [Numeric grouping and locales](./numeric-grouping-and-locales.md) — the `L` flag that sits right after precision.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
