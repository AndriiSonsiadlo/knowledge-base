---
id: ostream-fallback-formatting
title: ostream fallback formatting
sidebar_label: ostream bridge
sidebar_position: 2
tags: [c++, fmt, custom-types, ostream]
---

# ostream fallback formatting

A codebase with hundreds of `operator<<` overloads doesn't need rewriting to adopt fmt. The ostream
bridge is the migration path, not the destination — it lets fmt format anything that already streams,
today, so the rest of the migration can happen incrementally.

## Using it

```cpp showLineNumbers
#include <fmt/ostream.h>

struct Money { long cents; };
std::ostream& operator<<(std::ostream& os, const Money& m) {
    return os << "$" << (m.cents / 100) << "." << (m.cents % 100);
}

fmt::print("Total: {}\n", fmt::streamed(Money{1050}));  // "Total: $10.50"
```

`fmt::streamed(value)` wraps `value` so fmt routes it through its existing `operator<<`.

## The version caveat

:::note[Older fmt formatted ostream-able types implicitly; modern fmt requires fmt::streamed or an explicit formatter — check your version before assuming]
Earlier fmt releases would fall back to `operator<<` automatically for any type with no
`formatter<T>`. Current fmt requires either an explicit `formatter<T>` or a wrap in
`fmt::streamed`, specifically to avoid silently paying the stream cost when you didn't mean to. Code
written against an older fmt tutorial may assume the implicit behavior — verify against your actual
version before relying on it.
:::

## The cost

| | `formatter<T>` | ostream bridge |
|---|---|---|
| Speed | Fast — writes fmt's buffer directly | Slower — goes through an intermediate `std::ostream` |
| Spec support | Full mini-language, or a custom one | Width/alignment only, applied to the whole stream result |
| Compile time | One template per type | Reuses the type's existing `operator<<` — nothing new to compile |
| Effort | Requires writing `parse`/`format` | Zero — works with code that already exists |

## Direction of travel

:::tip[Use the bridge to migrate, then write a real formatter for the types formatted in hot paths]
The bridge is the right tool for the long tail of types formatted once, in error messages or
diagnostics, where the cost of an intermediate stream doesn't matter. For types formatted in a hot
loop, replace the bridge call with a proper
[formatter specialization](./formatter-specialization.md) once you've confirmed it's worth the code.
:::

## Interaction with std::format

:::note[std::format has no ostream bridge — code relying on it will not port]
`std::format` requires an explicit `std::formatter<T>` specialization for every type; there's no
equivalent to `fmt::streamed`. Code that leans on the ostream bridge is fmt-specific and needs real
formatters written before it can move to `std::format`. See
[Migration between fmt and std::format](../06-performance-and-best-practices/migration-from-std-format.md).
:::

## See also

- <Icon icon="lucide:shapes" inline /> [formatter specialization](./formatter-specialization.md) — the real, faster alternative once a type is worth it.
- <Icon icon="lucide:arrow-left-right" inline /> [Migration between fmt and std::format](../06-performance-and-best-practices/migration-from-std-format.md) — why this bridge doesn't carry over.
- <Icon icon="lucide:scale" inline /> [Comparison with printf and iostreams](../00-overview/comparison-with-printf-and-iostreams.md) — the broader context for why iostreams are slower.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
