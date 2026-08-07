---
id: format-strings-and-arguments
title: Format strings and arguments
sidebar_label: Format strings
sidebar_position: 1
tags: [c++, fmt, basics, format-strings]
---

# Format strings and arguments

A format string is a template with holes in it. Everything else in fmt — the spec grammar, custom
formatters, compile-time checks — is about what you're allowed to write inside a hole, and where the
result ends up going.

## Replacement fields

`{}` consumes the next argument in order. `{0}`, `{1}`, ... pick an argument by explicit index.
`{:spec}` attaches a format spec to either form.

```cpp
fmt::format("{} + {} = {}", 2, 3, 5);       // "2 + 3 = 5"
fmt::format("{0} + {1} = {0}", "no", "wait"); // "no + wait = no"
fmt::format("{:.2f}", 3.14159);              // "3.14"
```

## Escaping

To print a literal brace, double it: `{{` produces `{` and `}}` produces `}`.

```cpp
fmt::format("{{{}}}", 42);  // "{42}"
```

## Automatic vs manual indexing

A single format string must use either automatic (`{}`) or manual (`{0}`, `{1}`) indexing
throughout — not both.

:::danger[Mixing automatic and manual indexing in one format string is an error — fmt rejects it]
```cpp
fmt::format("{} and {1}", a, b);  // compile-time error: cannot switch from automatic to manual
```
Pick one style per string. This is deliberate: mixing them makes it ambiguous which argument index
the automatic field would land on.
:::

## Argument types

fmt formats these out of the box, with no extra header beyond `<fmt/format.h>`:

| Type | Default output |
|---|---|
| Integers (`int`, `long`, `unsigned`, ...) | Decimal |
| Floating point (`float`, `double`) | Shortest round-trip representation |
| `bool` | `true` / `false` |
| `char` | The character itself |
| `const char*`, `std::string`, `std::string_view` | The text, unquoted |
| `void*` | `0x` + hex address |

:::danger[Formatting a raw pointer other than void* requires an explicit cast — fmt will not silently print an address]
```cpp
int* p = &x;
fmt::format("{}", p);                             // compile-time error
fmt::format("{}", static_cast<void*>(p));          // "0x7ffee3a1c04c"
```
This is intentional — printing an arbitrary typed pointer's address is rarely what you meant, and fmt
would rather force the cast than guess.
:::

## What happens on a mismatch

If the format string is a compile-time-checked literal, a spec that doesn't apply to its argument's
type is a compile error — you find out before the code ships. If the string is a runtime string (see
below), the same mismatch throws `fmt::format_error` instead. See
[Compile-time format string checking](../04-compile-time-checks/compile-time-format-string-checking.md)
for exactly which cases are checked and when.

## Runtime format strings

`fmt::runtime("...")` explicitly opts a string out of compile-time checking — needed whenever the
format string itself is not a literal known at compile time, such as one loaded from a config file or
constructed at runtime.

:::danger[A user-supplied string must go through fmt::runtime and should never be trusted as a format string]
Passing untrusted input as the *format string* (as opposed to an *argument*) lets that input control
which arguments get read and how — at best a crash, at worst information disclosure. Validate or
whitelist runtime format strings before formatting with them, the same way you'd treat any other
input from outside your trust boundary.
:::

## See also

- <Icon icon="lucide:list-ordered" inline /> [The format function family](./the-format-function-family.md) — where the formatted result actually goes.
- <Icon icon="lucide:tag" inline /> [Positional and named arguments](./positional-and-named-arguments.md) — reordering and naming the holes.
- <Icon icon="lucide:ruler" inline /> [Format spec syntax](../02-format-spec-mini-language/format-spec-syntax.md) — everything that can follow the `:`.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
