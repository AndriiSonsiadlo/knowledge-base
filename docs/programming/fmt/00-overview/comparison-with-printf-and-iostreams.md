---
id: comparison-with-printf-and-iostreams
title: Comparison with printf and iostreams
sidebar_label: vs printf/iostreams
sidebar_position: 4
tags: [c++, fmt, comparison, printf, iostreams]
---

# Comparison with printf and iostreams

The two incumbents fail in opposite directions — `printf` trades safety for speed and brevity,
iostreams trade speed and brevity for safety — and fmt was designed by looking at exactly those two
failure modes and refusing both trade-offs.

## printf

```cpp
long long big_id = 123456789012LL;
printf("id: %d\n", big_id);   // compiles; prints garbage — %d expects int, not long long
```

This compiles cleanly and prints nonsense, because `printf`'s format string and its arguments are
connected by nothing the compiler checks. `%d` vs `%lld` vs `%ld` is a portability tax you pay on
every platform where `long` changes size, and there is no way to teach `printf` to format your own
types — it only knows what libc knows.

## iostreams

```cpp
std::cout << std::setw(10) << std::setfill('0') << std::setprecision(3)
          << std::fixed << value << '\n';

fmt::print("{:0>10.3f}\n", value);  // same output, one line, nothing left behind
```

:::danger[Stream manipulators are sticky — setting precision changes every later output on that stream]
`std::setprecision`, `std::setfill` and friends mutate the stream's state and stay set until
something else changes them. Format one value with three decimal places and forget to reset it, and
every subsequent `<<` on that stream inherits it — a common source of "why does this number print
wrong three functions later" bugs.
:::

## Comparison table

| | printf | iostreams | fmt |
|---|---|---|---|
| Type safety | None — undefined behavior on mismatch | Full | Full, checked at compile time for literals |
| Extensibility to custom types | No | Yes, via `operator<<` | Yes, via `formatter<T>`, more powerful |
| Throughput | Fast | Slow | Fast, comparable to printf |
| Output size (binary) | Small | Large — templated `operator<<` per type | Small |
| Localisation | Locale-dependent by default | Locale-dependent by default | Locale-independent by default, opt-in |
| Compile time | Fast | Slow — heavy header, many instantiations | Moderate — compile-time checking has a cost |
| Readability of the call site | Terse but easy to get wrong | Verbose, state scattered across `<<` chains | Terse, self-contained per call |

## Where printf still wins

It's honest to say printf hasn't lost everywhere. It's the lingua franca for C interop — any C
library, kernel logging facility, or embedded toolchain expects it. It has zero dependencies since
it's part of libc, and every C++ programmer already knows its format specifiers even if they've never
touched fmt. For a one-off debug print in code that's already deep in C territory, reaching for
`printf` isn't a mistake.

## Migration sketch

| printf | fmt |
|---|---|
| `%d` | `{}` (for `int`) |
| `%s` | `{}` (for `const char*`/`std::string`) |
| `%.3f` | `{:.3f}` |
| `%-10s` | `{:<10}` |
| `%08.2f` | `{:08.2f}` |

See [Format spec syntax](../02-format-spec-mini-language/format-spec-syntax.md) for the full grammar
behind the right-hand column — every printf conversion has a direct fmt equivalent, plus several that
printf never had.

## See also

- <Icon icon="lucide:sparkles" inline /> [What is fmt?](./what-is-fmt.md) — the broader introduction this comparison supports.
- <Icon icon="lucide:git-branch" inline /> [Relationship to std::format](./relationship-to-std-format.md) — how the standard library's answer fits in.
- <Icon icon="lucide:ruler" inline /> [Format spec syntax](../02-format-spec-mini-language/format-spec-syntax.md) — where the migration sketch above leads next.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
