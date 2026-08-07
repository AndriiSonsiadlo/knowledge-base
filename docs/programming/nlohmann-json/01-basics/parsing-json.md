---
id: parsing-json
title: Parsing JSON
sidebar_label: Parsing
sidebar_position: 1
tags: [c++, nlohmann-json, parsing, basics]
---

# Parsing JSON

Parsing is the boundary between untrusted text and typed data. Every way into a `json` value from
raw bytes ends up calling the same parser, but the entry points differ in what input they accept
and — more importantly — in what happens when that input is malformed.

## From a string

The most direct route: hand `json::parse` a `std::string` (or anything convertible to one,
including a raw string literal).

```cpp
json j = json::parse(R"({"name": "ada", "age": 36})");
```

## From a stream

Two ways to read from a stream, and they don't behave identically. `operator>>` reads a JSON value
from the stream into an existing `json`:

```cpp
std::ifstream ifs("config.json");
json j;
ifs >> j;
```

`json::parse(ifs)` does the same job but returns the value instead of taking an out-parameter, and
gives a slightly more detailed error on failure (a `parse_error` carrying the byte offset within the
stream, versus `operator>>` setting the stream's failbit):

```cpp
std::ifstream ifs("config.json");
json j = json::parse(ifs);
```

Prefer `json::parse(ifs)` when you want exception-based error handling with a useful message;
`operator>>` fits more naturally into code that's already checking stream state.

## From iterators / raw bytes

`json::parse` also accepts an iterator range, which is how you parse a `std::vector<uint8_t>` or
any other contiguous byte buffer without first copying it into a `std::string`:

```cpp
std::vector<uint8_t> buffer = read_file_bytes("config.json");
json j = json::parse(buffer.begin(), buffer.end());
```

## The _json literal

For test fixtures and constants embedded directly in source, the `_json` user-defined literal
parses a string literal at the call site:

```cpp
using namespace nlohmann::literals;

json j = R"({"a": 1, "b": 2})"_json;
```

:::tip[This is sugar for tests and fixtures, not for runtime input]
The literal still runs the full parser — it isn't compile-time — so it buys you nothing but
readability. Use it for hard-coded expected values in unit tests and small embedded constants;
reach for `json::parse()` explicitly anywhere the input is actually variable, so the parse call and
its error handling are visible at the call site.
:::

## Parse callbacks and filtering

`json::parse` takes an optional `parser_callback_t` that's invoked for every parsed element,
letting you inspect or discard pieces of the document as it's built rather than after the fact:

```cpp showLineNumbers
json j = json::parse(text, /* cb */ [](int /*depth*/, json::parse_event_t event, json& parsed) {
    // drop any key literally named "password" as it's parsed
    if (event == json::parse_event_t::key && parsed == json("password")) {
        return false;   // returning false discards this element
    }
    return true;
});
```

Returning `false` from the callback removes the element (and everything nested under it) from the
resulting document — useful for stripping sensitive fields or unwanted sections without a
post-parse pass over the whole tree.

## Failure modes

Malformed input throws `json::parse_error`, which — like every exception in this library — carries
a numeric `id` and, for parse errors specifically, a `byte` offset into the input where parsing
failed:

```cpp
try {
    json j = json::parse("{invalid}");
} catch (const json::parse_error& e) {
    std::cerr << "parse failed at byte " << e.byte << ": " << e.what() << "\n";
}
```

If you'd rather not use exceptions at all, `json::parse` has an overload taking
`allow_exceptions = false`, which returns a `json` of type `value_t::discarded` on failure instead
of throwing:

```cpp
json j = json::parse(text, /* cb */ nullptr, /* allow_exceptions */ false);
if (j.is_discarded()) {
    // handle the parse failure without a try/catch
}
```

:::danger[Never parse untrusted input without a size limit]
The parser has no built-in cap on document size, nesting depth, or number of elements. Parsing an
attacker-controlled document with unbounded size or pathological nesting can exhaust memory or stack
space before you ever get a chance to validate the result. Enforce a maximum input size and a
sensible depth limit at your application boundary, before the bytes ever reach `json::parse`.
:::

## See also

- <Icon icon="lucide:box" inline /> [The JSON value type](./the-json-value-type.md) — what the parser actually produces.
- <Icon icon="lucide:printer" inline /> [Serialization and dumping](./serialization-and-dumping.md) — the inverse operation.
- <Icon icon="lucide:alert-triangle" inline /> [Error handling and exceptions](../04-advanced-features/error-handling-and-exceptions.md) — the full exception hierarchy and non-throwing patterns.
- <Icon icon="lucide:radio" inline /> [The SAX interface](../04-advanced-features/sax-interface.md) — parsing without building a DOM at all.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
