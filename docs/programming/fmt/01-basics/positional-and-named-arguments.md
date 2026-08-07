---
id: positional-and-named-arguments
title: Positional and named arguments
sidebar_label: Positional and named
sidebar_position: 3
tags: [c++, fmt, basics, arguments]
---

# Positional and named arguments

Positional and named arguments exist for the same reason: the order of the holes in a format string
shouldn't be dictated by the order your variables happen to be declared in — especially once
translators get involved.

## Positional

`{N}` picks argument `N` (zero-indexed), and the same argument can be reused as many times as you
like.

```cpp
fmt::format("{1} {0} {1}", "world", "hello");  // "hello world hello"
```

## Named

`fmt::arg("name", value)` attaches a name to an argument, and `{name}` in the format string refers to
it. The `_a` user-defined literal from `<fmt/args.h>` is shorthand for `fmt::arg`.

```cpp showLineNumbers
#include <fmt/args.h>
using namespace fmt::literals;

fmt::format("{name} is {age} years old", "name"_a = "Ada", "age"_a = 36);
// equivalent, without the literal:
fmt::format("{name} is {age} years old", fmt::arg("name", "Ada"), fmt::arg("age", 36));
```

## Why this matters for translation

A string handed to a translator can reorder its fields freely as long as the call site passes named
arguments — the C++ code doesn't need to change to match a language where the sentence structure
differs.

```cpp
// English: "{name} scored {score} points"
// German:  "{score} Punkte für {name}" — same fmt::arg calls, reordered template
```

:::tip[Named arguments make a format string safe to hand to a translator]
With positional or automatic indexing, reordering the sentence in translation means reordering (and
re-testing) the argument list in code. With named arguments, only the translated string changes.
:::

## Dynamic argument lists

When the set of arguments isn't known until runtime — building a log line from a variable number of
key/value pairs, say — `fmt::dynamic_format_arg_store` accumulates arguments one at a time before a
single `fmt::vformat` call.

```cpp showLineNumbers
fmt::dynamic_format_arg_store<fmt::format_context> store;
for (const auto& [key, value] : fields) {
    store.push_back(fmt::arg(key.c_str(), value));
}
std::string line = fmt::vformat(format_string, store);
```

## Lifetime

:::danger[fmt::arg and dynamic_format_arg_store hold references — the referenced values must outlive the format call]
`fmt::arg("name", value)` stores a reference to `value`, not a copy. Building a `dynamic_format_arg_store`
across a loop and only formatting after values have gone out of scope is a dangling-reference bug.
See [Common pitfalls](../06-performance-and-best-practices/common-pitfalls.md) for the exact shape of
this mistake and the fix.
:::

## std::format compatibility

:::note[Named arguments are fmt-only — std::format has no equivalent]
If code needs to compile against both fmt and `std::format`, named arguments are one of the features
that doesn't port. See [Relationship to std::format](../00-overview/relationship-to-std-format.md)
for the full list of what each side has that the other doesn't.
:::

## See also

- <Icon icon="lucide:type" inline /> [Format strings and arguments](./format-strings-and-arguments.md) — the basics these examples build on.
- <Icon icon="lucide:list-ordered" inline /> [The format function family](./the-format-function-family.md) — where the formatted result goes once the arguments are resolved.
- <Icon icon="lucide:git-branch" inline /> [Relationship to std::format](../00-overview/relationship-to-std-format.md) — what does and doesn't carry over to the standard facility.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
