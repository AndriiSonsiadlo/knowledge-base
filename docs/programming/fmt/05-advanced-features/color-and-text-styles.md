---
id: color-and-text-styles
title: Color and text styles
sidebar_label: Color and styles
sidebar_position: 3
tags: [c++, fmt, advanced, color, terminal]
---

# Color and text styles

Terminal color is a formatting concern, and fmt handles it with the same type-safe API used
everywhere else instead of leaving you to paste raw ANSI escape codes into string literals.

## Basic use

```cpp showLineNumbers
#include <fmt/color.h>

fmt::print(fg(fmt::color::crimson) | fmt::emphasis::bold, "{}\n", msg);
```

`fg(color)` sets the foreground color; combined with `fmt::emphasis::bold` via `|`, the whole thing is
a `fmt::text_style` object that any `fmt::print`/`fmt::format` call accepts as its first argument.

## The pieces

`fg(color)` sets foreground, `bg(color)` sets background, and `fmt::emphasis` covers `bold`,
`italic`, `underline`, and `strikethrough` — all combinable with `|`.

| API | Palette | Portability |
|---|---|---|
| `fmt::terminal_color` | 8/16-color ANSI palette | Works on nearly every terminal, including old ones |
| `fmt::color` | 24-bit RGB | Needs a truecolor-capable terminal |

Prefer `fmt::terminal_color` for output that has to work in a plain SSH session or CI log; reach for
`fmt::color`'s full RGB range when you know the target terminal supports it.

## fmt::styled

`fmt::styled(value, style)` attaches a style to a single argument inside a larger format string,
rather than styling the whole call.

```cpp
fmt::print("Status: {}\n", fmt::styled("OK", fg(fmt::color::green) | fmt::emphasis::bold));
```

## Getting it into a string

`fmt::format(fg(...), ...)` embeds the ANSI escape codes directly in the returned string — useful when
the result is going to a terminal-writing function that doesn't take a style argument itself.

## Redirection

:::danger[fmt does not detect whether the output is a TTY — escape codes will land in your log file if you redirect]
`fmt::print(fg(fmt::color::red), "error\n")` writes raw ANSI escapes into whatever `stdout` currently
points at. Redirected to a file or piped into a log aggregator that doesn't strip ANSI, those escape
codes show up as garbage characters. Check `isatty` (or your platform's equivalent) yourself and pick
a style-free formatting path when the destination isn't a terminal.
:::

## Windows

:::note[On older Windows consoles the escapes print literally unless VT mode is enabled]
Windows consoles didn't historically interpret ANSI escape sequences at all; virtual terminal (VT)
processing has to be enabled explicitly (`ENABLE_VIRTUAL_TERMINAL_PROCESSING` via
`SetConsoleMode`) before colored fmt output renders correctly instead of printing the raw escape
bytes.
:::

## See also

- <Icon icon="lucide:languages" inline /> [Unicode and encoding notes](./unicode-and-encoding-notes.md) — the other terminal-output-specific corner of fmt.
- <Icon icon="lucide:list-ordered" inline /> [The format function family](../01-basics/the-format-function-family.md) — how a `text_style` argument fits into the usual call shape.
- <Icon icon="lucide:move-horizontal" inline /> [Alignment, fill and width](../02-format-spec-mini-language/alignment-fill-and-width.md) — combining color with column layout.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
