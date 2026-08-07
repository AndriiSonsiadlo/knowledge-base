---
id: compile-time-format-string-checking
title: Compile-time format string checking
sidebar_label: Compile-time checks
sidebar_position: 1
tags: [c++, fmt, compile-time, safety]
---

# Compile-time format string checking

The whole point of replacing `printf` is that a wrong format string shouldn't be a runtime surprise.
fmt turns it into a compile error whenever the string is a literal — no `printf`-style silent
undefined behavior, and no `fmt::format_error` thrown three weeks into production.

## How it works today

On C++20, `fmt::format` and friends take a `fmt::format_string<Args...>`, a type whose constructor is
`consteval` and validates the string against the argument types at compile time. A string literal is
checked with no extra syntax required.

```cpp showLineNumbers
fmt::format("{:d}", "not a number");
// error: invalid format specifier for argument of type 'const char*'
// caught before the program ever runs
```

## FMT_STRING

`FMT_STRING(s)` is the pre-C++20 macro that forces the same checking on standards where the language
doesn't yet support `consteval`.

:::note[FMT_STRING is only needed on older standards — on C++20 the plain call is already checked]
```cpp
fmt::format(FMT_STRING("{}"), x);  // needed pre-C++20
fmt::format("{}", x);              // already checked on C++20 and later
```
Wrapping every literal in `FMT_STRING` on a C++20 codebase is harmless but unnecessary.
:::

## Opting out

`fmt::runtime(s)` explicitly marks a string as not known at compile time, opting out of the check.

:::danger[fmt::runtime moves the error to runtime as a thrown fmt::format_error — catch it or validate the string first]
```cpp
std::string user_template = load_from_config();
fmt::format(fmt::runtime(user_template), x);  // any mismatch throws fmt::format_error
```
Once a string goes through `fmt::runtime`, every guarantee the compiler was giving you is gone —
you're back to needing a try/catch (or upstream validation) the way you would with any other runtime
input.
:::

## What is and isn't checked

| Case | Checked | When it fails |
|---|---|---|
| String literal, argument types known | Yes, at compile time | Compile error |
| `fmt::runtime("...")` | No | Throws `fmt::format_error` at the call |
| `fmt::vformat` / `fmt::vformat_to` | No — type-erased args bypass the check | Throws `fmt::format_error` at the call |
| Custom `formatter<T>` with a `constexpr` `parse` | Yes | Compile error |
| Custom `formatter<T>` with a non-`constexpr` `parse` | No | Throws `fmt::format_error` at the call |

## Making your formatter checkable

For the compile-time check to reach a custom type's own spec grammar, that type's
`formatter<T>::parse` must itself be `constexpr`. See
[formatter specialization](../03-formatting-custom-types/formatter-specialization.md) for what a
`parse` implementation looks like — most straightforward implementations are already `constexpr`
without extra effort.

## Compile-time cost

:::note[Checking happens per call site — it is a real compile-time cost, and it is worth it]
Every checked format call re-validates the string against the argument types at that specific call
site. On a translation unit with hundreds of format calls, this adds up. See
[Header-only vs compiled mode](../06-performance-and-best-practices/header-only-vs-compiled-mode.md)
for the broader picture of fmt's compile-time footprint and how to keep it under control.
:::

## See also

- <Icon icon="lucide:bug" inline /> [Error diagnostics](./error-diagnostics.md) — reading the errors this checking produces.
- <Icon icon="lucide:type" inline /> [Format strings and arguments](../01-basics/format-strings-and-arguments.md) — the basics this checking sits on top of.
- <Icon icon="lucide:shapes" inline /> [formatter specialization](../03-formatting-custom-types/formatter-specialization.md) — making a custom type's spec checkable.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
