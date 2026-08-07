---
id: type-specific-presentation
title: Type-specific presentation
sidebar_label: Presentation types
sidebar_position: 4
tags: [c++, fmt, format-spec, presentation]
---

# Type-specific presentation

The final character of a spec picks a presentation, and the legal set of characters depends on the
argument's type — this is the page you actually look things up on while writing a format string.

## Integers

| Type char | Meaning | Example (`255`) |
|---|---|---|
| `d` (default) | Decimal | `255` |
| `b` / `B` | Binary, lowercase/uppercase prefix with `#` | `11111111` |
| `o` | Octal | `377` |
| `x` / `X` | Hex, lowercase/uppercase digits | `ff` / `FF` |
| `c` | Interpret as a character code | `ÿ` |

## Floating point

| Type char | Meaning | Example (`1234.5`) |
|---|---|---|
| `f` / `F` | Fixed notation | `1234.500000` |
| `e` / `E` | Scientific notation | `1.234500e+03` |
| `g` / `G` | Shortest of fixed/scientific for the given precision | `1234.5` |
| `a` / `A` | Hexadecimal floating point | `0x1.348p+10` |
| (default) | Shortest round-trip representation | `1234.5` |

## Strings and chars

`s` is the default, unquoted presentation. `?` is the debug/escaped presentation: it wraps the string
in quotes and escapes control characters and non-printable bytes.

:::tip[The debug presentation prints an escaped, quoted string — the right thing for logging user input]
```cpp
fmt::format("{:?}", "line1\nline2");  // "\"line1\\nline2\""
```
When logging a value that might contain newlines, tabs, or other control characters, `{:?}` makes the
boundaries of the string unambiguous in a log line — you can tell where it starts and ends and see
embedded whitespace instead of it silently reformatting your log output.
:::

## bool

`s` (the default) prints `true`/`false`. `d` treats the `bool` as an integer and prints `1`/`0`.

## Pointers

`p` is the only presentation for pointers, and it requires the argument to already be a `const
void*` — a typed pointer must be cast explicitly first (`static_cast<const void*>(ptr)`).

## Mismatches

:::danger[A presentation type that doesn't apply to the argument is a compile-time error with a checked format string, and a fmt::format_error at runtime otherwise]
`{:x}` on a `std::string`, or `{:f}` on a `bool`, is rejected the same way any other spec/type
mismatch is. See [Error diagnostics](../04-compile-time-checks/error-diagnostics.md) for how to read
the error either way it surfaces.
:::

## See also

- <Icon icon="lucide:braces" inline /> [Format spec syntax](./format-spec-syntax.md) — where the type character sits in the full grammar.
- <Icon icon="lucide:hash" inline /> [Sign and numeric precision](./sign-and-numeric-precision.md) — sign and precision, which combine with these presentations.
- <Icon icon="lucide:shapes" inline /> [formatter specialization](../03-formatting-custom-types/formatter-specialization.md) — defining your own presentation letters for a custom type.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
