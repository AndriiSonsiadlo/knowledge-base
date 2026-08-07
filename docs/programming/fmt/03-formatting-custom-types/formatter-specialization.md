---
id: formatter-specialization
title: formatter specialization
sidebar_label: formatter
sidebar_position: 1
tags: [c++, fmt, custom-types, formatter]
---

# formatter specialization

Extensibility is the thing `printf` can never have. A `formatter<T>` specialization makes your own
type a first-class formattable value — spec grammar included, not just a fixed `to_string`.

## The minimal specialization

A specialization needs a `parse` member (consumes the spec text after the `:`) and a `format` member
(produces the output).

```cpp showLineNumbers title="point_formatter.hpp"
struct Point { double x, y; };

template <>
struct fmt::formatter<Point> {
    constexpr auto parse(format_parse_context& ctx) {
        return ctx.begin();  // no custom spec — just consume nothing and stop
    }

    auto format(const Point& p, format_context& ctx) const {
        return fmt::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};
```

## Inheriting parse

Deriving from an existing `formatter<U>` gets you its spec grammar for free — useful when your type
is "really" a couple of numbers or strings and you want the standard numeric spec to apply to them.

```cpp showLineNumbers
template <>
struct fmt::formatter<Point> : fmt::formatter<double> {
    auto format(const Point& p, format_context& ctx) const {
        auto out = ctx.out();
        out = fmt::formatter<double>::format(p.x, ctx);
        out = fmt::format_to(out, ", ");
        ctx.advance_to(out);
        return fmt::formatter<double>::format(p.y, ctx);
    }
};
```

Now `{:.2f}` on a `Point` forwards the `.2f` spec to both coordinates: `(1.50, 2.75)`.

## Accepting your own spec

`parse` can recognize its own letters instead of only forwarding an inherited grammar, and should
throw `fmt::format_error` on anything it doesn't understand.

```cpp
constexpr auto parse(format_parse_context& ctx) {
    auto it = ctx.begin(), end = ctx.end();
    if (it != end && *it == 'p') { presentation = 'p'; ++it; }
    if (it != end && *it != '}') throw fmt::format_error("invalid format spec for Point");
    return it;
}
```

:::danger[parse must stop at the closing brace and return the iterator to it — running past it corrupts the rest of the format string]
`parse` is only responsible for the characters that belong to *this* argument's spec. If it advances
past the closing `}`, everything after it in the format string is parsed incorrectly — the failure
usually shows up as a confusing error on a completely different, unrelated argument.
:::

## const-correctness

:::danger[format must be const for the type to be formattable as a const reference — a non-const format compiles until someone passes a const object]
```cpp
auto format(const Point& p, format_context& ctx) const { /* ... */ }  // correct
auto format(const Point& p, format_context& ctx) { /* ... */ }        // compiles, breaks later
```
The non-`const` version works fine right up until someone tries to format a `const Point&` or a
`Point` obtained through a `const` accessor, at which point it fails to compile at the call site
rather than at the formatter definition — an unpleasant place to first learn about it.
:::

## Enums

```cpp
enum class Status { Ok, Warning, Error };

template <>
struct fmt::formatter<Status> : fmt::formatter<std::string_view> {
    auto format(Status s, format_context& ctx) const {
        std::string_view name = "unknown";
        switch (s) {
            case Status::Ok:      name = "ok"; break;
            case Status::Warning: name = "warning"; break;
            case Status::Error:   name = "error"; break;
        }
        return fmt::formatter<std::string_view>::format(name, ctx);
    }
};
```

## Where it must live

The specialization must be declared in namespace `fmt` (as `template <> struct fmt::formatter<T>`,
shown above). For a type that's just a thin wrapper convertible to something already formattable,
`FMT_FORMAT_AS(WrapperType, UnderlyingType)` is a one-line shortcut instead of writing the
specialization by hand.

## See also

- <Icon icon="lucide:list" inline /> [Ranges, tuples and containers](./ranges-tuples-and-containers.md) — formatting collections of your custom types.
- <Icon icon="lucide:arrow-right-left" inline /> [ostream fallback formatting](./ostream-fallback-formatting.md) — the lower-effort alternative when you already have `operator<<`.
- <Icon icon="lucide:braces" inline /> [Format spec syntax](../02-format-spec-mini-language/format-spec-syntax.md) — the grammar `parse` is consuming.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
