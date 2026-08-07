---
id: alignment-fill-and-width
title: Alignment, fill and width
sidebar_label: Alignment and width
sidebar_position: 2
tags: [c++, fmt, format-spec, alignment]
---

# Alignment, fill and width

Width and alignment are what turn a stream of values into a readable table, and the defaults differ
by type in a way that surprises people exactly once.

## The three alignments

| Align | Meaning | Default for |
|---|---|---|
| `<` | Left-align | Strings, `bool`, `char` |
| `>` | Right-align | Numbers |
| `^` | Center | Nothing — always explicit |
| `=` | Pad *after* the sign, before the digits | Numbers only, must be requested explicitly |

`=` is the one that doesn't exist for strings: it keeps a `+`/`-` sign at the far left of the field
and pushes the padding between the sign and the first digit, which is what you want for a column of
signed numbers that still needs to line up on the decimal point.

## Fill characters

The fill character goes immediately *before* the alignment marker, not after.

```cpp
fmt::format("{:*>8}", 42);   // "******42"
fmt::format("{:0>5}", 7);    // "00007"
```

:::danger[A fill character without an explicit alignment is not parsed as fill]
```cpp
fmt::format("{:*8}", 42);   // error — '*' is not a valid spec character on its own
fmt::format("{:*>8}", 42);  // "******42" — correct: fill needs an alignment marker right after it
```
The fill character is only recognized when it's immediately followed by one of `<`, `>`, `^`, `=`.
Without the alignment marker, fmt doesn't know it's a fill character at all.
:::

## Width

Width sets a *minimum* field size, never a maximum.

:::danger[Width never truncates — an over-long value blows out your column]
```cpp
fmt::format("{:5}", "a very long string");  // prints the whole string, width is ignored
```
If you need to bound the output length, use precision instead — see
[Sign and numeric precision](./sign-and-numeric-precision.md) for truncating strings with `.N`.
:::

## Building a table

```cpp showLineNumbers title="table.cpp"
struct Row { std::string name; int score; };
std::vector<Row> rows = {{"Alice", 97}, {"Bob", 84}, {"Carol", 100}};

size_t name_width = 0;
for (auto& r : rows) name_width = std::max(name_width, r.name.size());

fmt::print("{:<{}} | {:>5}\n", "Name", name_width, "Score");
for (auto& r : rows) {
    fmt::print("{:<{}} | {:>5}\n", r.name, name_width, r.score);
}
```

## Width and Unicode

Width counts *display width* — how many terminal columns a string occupies — not the number of
`char`s or bytes. That mostly matches expectations for ASCII, but combining characters and East Asian
wide characters change the relationship between byte count and displayed width. See
[Unicode and encoding notes](../05-advanced-features/unicode-and-encoding-notes.md) for the exact
caveats and where alignment can still look ragged despite a correct width count.

## See also

- <Icon icon="lucide:braces" inline /> [Format spec syntax](./format-spec-syntax.md) — the full grammar this page is one piece of.
- <Icon icon="lucide:hash" inline /> [Sign and numeric precision](./sign-and-numeric-precision.md) — precision, which truncates where width does not.
- <Icon icon="lucide:languages" inline /> [Unicode and encoding notes](../05-advanced-features/unicode-and-encoding-notes.md) — why width and byte count diverge.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
