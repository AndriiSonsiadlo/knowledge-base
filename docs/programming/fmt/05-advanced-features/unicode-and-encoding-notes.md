---
id: unicode-and-encoding-notes
title: Unicode and encoding notes
sidebar_label: Unicode
sidebar_position: 4
tags: [c++, fmt, advanced, unicode, encoding]
---

# Unicode and encoding notes

fmt treats `char`-based strings as UTF-8. That's the right default for nearly every modern codebase,
and it's also the source of every surprise on Windows and in aligned output — width, byte count, and
"number of characters" are three different numbers, and only one of them is what you usually mean.

## UTF-8 by default

`char`-based arguments and format strings are assumed to be UTF-8. `fmt::print` handles the
transcoding needed to get UTF-8 bytes onto a Windows console correctly, which historically expects
the system's active code page rather than UTF-8 directly.

## Width vs bytes vs code points

| String | Bytes | Code points | Display width |
|---|---|---|---|
| `"cafe"` | 4 | 4 | 4 |
| `"café"` (é as U+00E9) | 5 | 4 | 4 |
| `"日本語"` | 9 | 3 | 6 (each CJK character is 2 columns wide) |
| `"👍"` | 4 | 1 | 2 |

The `width` component of a format spec counts *display width* — the number of terminal columns the
string occupies — not bytes and not code points. See
[Alignment, fill and width](../02-format-spec-mini-language/alignment-fill-and-width.md) for how
width is used in the spec grammar.

## Alignment with non-ASCII

:::danger[Aligning a column of mixed-script text by width will still look ragged — display width is an approximation, and combining characters and emoji sequences break it]
Display width is a heuristic, not a guarantee agreed on by every terminal emulator. Combining
characters (a base letter plus a separate accent code point), multi-code-point emoji sequences (a
flag, a family emoji with a zero-width joiner), and font-dependent glyph widths can all disagree with
fmt's width calculation. Treat width-based alignment as "usually lines up," not "always lines up,"
once the content isn't ASCII.
:::

## Precision on strings

:::danger[Truncation can still split a grapheme cluster — do not use it to cut user-visible text at an arbitrary point]
`.N` precision truncates by display width, which avoids cutting a multi-byte UTF-8 sequence in half,
but it can still cut a combining character away from its base character or split an emoji sequence
mid-cluster, producing a broken-looking result. Don't use precision-based truncation as the last step
before showing text to a user; do that with a proper text-segmentation library if grapheme boundaries
matter.
:::

## Wide strings

`<fmt/xchar.h>` adds support for `wchar_t`-based format strings and arguments.

:::note[Prefer UTF-8 char strings everywhere and convert at the OS boundary — wide-string formatting is a compatibility path, not the recommended one]
Wide-string support exists for interoperating with Windows APIs that are natively `wchar_t`-based. The
recommended pattern is still to keep application logic in UTF-8 `char` strings and convert only at the
boundary where a wide-string API is unavoidable, not to thread `wchar_t` through the rest of the
codebase.
:::

## Windows specifics

Windows consoles historically used an active code page rather than UTF-8; `fmt::print` performs the
necessary conversion so UTF-8 source text renders correctly, but writing to a `FILE*` yourself
bypasses that conversion. Source files should be saved as UTF-8 *without* a byte-order mark — a
leading BOM is not part of the string content and, depending on the compiler, can end up embedded in
string literals or rejected outright.

## See also

- <Icon icon="lucide:palette" inline /> [Color and text styles](./color-and-text-styles.md) — the other terminal-output-specific corner of fmt.
- <Icon icon="lucide:move-horizontal" inline /> [Alignment, fill and width](../02-format-spec-mini-language/alignment-fill-and-width.md) — how width is defined and used in the spec grammar.
- <Icon icon="lucide:globe" inline /> [Numeric grouping and locales](../02-format-spec-mini-language/numeric-grouping-and-locales.md) — the other place locale/encoding assumptions matter.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
