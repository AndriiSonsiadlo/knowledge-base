---
id: error-diagnostics
title: Error diagnostics
sidebar_label: Diagnostics
sidebar_position: 2
tags: [c++, fmt, errors, diagnostics]
---

# Error diagnostics

fmt's errors arrive in two flavours: a wall of template output at compile time, and a
`fmt::format_error` thrown at runtime — and both are readable once you know where to look instead of
reading them top to bottom.

## fmt::format_error

`fmt::format_error` (derived from `std::runtime_error`) is thrown for a bad runtime format string
(missing/extra braces, unknown argument index), a spec that doesn't apply to the argument's type when
the check couldn't happen at compile time, or an out-of-range positional index.

```cpp showLineNumbers
try {
    fmt::format(fmt::runtime(user_template), value);
} catch (const fmt::format_error& e) {
    log_error("bad format string: {}", e.what());
}
```

## Reading a compile-time failure

Compiler output for a failed compile-time check is dominated by template instantiation noise, but
fmt's own diagnostic text is in there — search for a line containing "invalid format string" or "not
formattable" rather than reading from the top.

```
error: call to consteval function 'fmt::format_string<...>::format_string<char [12]>' is not a constant expression
note: invalid format specifier for argument 0: expected floating-point type
  ... (many more lines of template instantiation) ...
```

The `note:` line with the actual complaint is the one worth reading; everything above and below it is
the compiler explaining how it got there.

## The "no formatter" error

The most common compile-time failure by far: a type with no `formatter<T>` specialization and no
ostream bridge applied.

```
error: static assertion failed: Cannot format an argument. To make type T formattable provide a
formatter<T> specialization
```

Two fixes: write a real [formatter specialization](../03-formatting-custom-types/formatter-specialization.md),
or, if the type already has `operator<<`, wrap it in
[`fmt::streamed`](../03-formatting-custom-types/ostream-fallback-formatting.md) as a quicker stopgap.

## Common causes table

| Symptom | Cause | Fix |
|---|---|---|
| "unmatched `{`" or similar | An unescaped brace in the literal text | Double it: `{{` / `}}` |
| "cannot switch from automatic to manual argument indexing" | Mixed `{}` and `{0}` in one string | Pick one indexing style per string |
| "invalid format specifier" | Spec doesn't apply to the argument's type | Check [Type-specific presentation](../02-format-spec-mini-language/type-specific-presentation.md) |
| "Cannot format an argument" | No `formatter<T>`, no ostream bridge | Add a formatter or `fmt::streamed` |
| Check doesn't fire on a custom type | `formatter<T>::parse` isn't `constexpr` | Make `parse` `constexpr` |
| Runtime `fmt::format_error` on a variable string | A `std::string` used directly as the format string | Wrap in `fmt::runtime(...)` |

## Assertions and hardening

`FMT_ASSERT` guards internal preconditions inside fmt's own implementation. In release builds
(`NDEBUG`), assertion checks are typically compiled out for performance, the same trade-off as
`assert` in the standard library.

:::danger[Do not rely on a format-string error being caught in release — validate untrusted strings before formatting]
A malformed or malicious runtime format string that would trip an assertion in a debug build may
instead produce undefined behavior in a release build if the corresponding check was compiled out.
Never pass untrusted input as the format string itself; validate it, or better, don't let it be the
format string at all — pass it as an *argument* to a trusted template string instead.
:::

## See also

- <Icon icon="lucide:shield-check" inline /> [Compile-time format string checking](./compile-time-format-string-checking.md) — how these errors are caught before they become runtime ones.
- <Icon icon="lucide:type" inline /> [Format strings and arguments](../01-basics/format-strings-and-arguments.md) — the syntax rules these errors are enforcing.
- <Icon icon="lucide:triangle-alert" inline /> [Common pitfalls](../06-performance-and-best-practices/common-pitfalls.md) — the broader checklist these symptoms belong to.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
