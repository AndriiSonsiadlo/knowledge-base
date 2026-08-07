---
id: source-location-and-structured-logging
title: Source location and structured logging
sidebar_label: Source location
sidebar_position: 3
tags: [c++, spdlog, formatting, macros, structured]
---

# Source location and structured logging

File, line, and function are free only if the call site captures them — which is exactly why they're
macros rather than function arguments, and why spdlog doesn't ship built-in JSON output: both would
require doing work at every call site whether or not you use the result.

## The SPDLOG_* macros

`SPDLOG_INFO(...)`, `SPDLOG_LOGGER_INFO(logger, ...)`, and the lower-level `SPDLOG_LOGGER_CALL(...)`
capture `__FILE__`, `__LINE__`, and `SPDLOG_FUNCTION` at the call site and pass them through to the
log message alongside your formatted text. They also respect `SPDLOG_ACTIVE_LEVEL` — a
`SPDLOG_DEBUG(...)` call compiles to nothing at all when the active level excludes debug, which
`spdlog::debug(...)` never does on its own. See
[Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) for that
mechanism.

## Function vs macro

| | `spdlog::info(...)` | `SPDLOG_INFO(...)` |
|---|---|---|
| Source location captured | No | Yes (file, line, function) |
| Elided at compile time | Never | Yes, below `SPDLOG_ACTIVE_LEVEL` |
| Arguments evaluated when disabled (compile-time) | Always | Never — code doesn't exist |
| Arguments evaluated when disabled (runtime only) | Yes | Yes |

## Printing the location

The `%s` (filename), `%#` (line), `%!` (function), and `%@` (`file:line` combined) pattern flags
render whatever source location the call captured:

```cpp showLineNumbers
spdlog::set_pattern("[%s:%#] [%l] %v");
SPDLOG_INFO("handler dispatched");
// -> "[request_handler.cpp:88] [info] handler dispatched"
```

## Structured logging

spdlog logs lines of text, not typed events — there's no schema, no field registry. Two practical
ways to get something structured-shaped out of it:

- **(a) A key=value convention** in the message itself, with a fixed pattern around it, so downstream
  tools can split on `=` and whitespace:

```cpp showLineNumbers
std::string kv(std::string_view key, std::string_view value) {
    return fmt::format("{}={}", key, value);
}

spdlog::info("{} {} {}",
    kv("event", "order_placed"), kv("order_id", order_id), kv("amount_cents", amount));
```

- **(b) A custom formatter emitting JSON** — see [Custom formatters](./custom-formatters.md) for the
  mechanism; instead of appending a formatted line, you'd serialize the message and any attached
  fields as a JSON object.

## Correlation ids

A custom flag that reads a thread-local request id is a common structured-logging building block —
same `custom_flag_formatter` mechanism as the thread-name example in
[Custom formatters](./custom-formatters.md), just backed by a `thread_local` value set at the top of
each request handler instead of a fixed lookup.

## Honest limitation

:::note[If you need real structured events with typed fields, spdlog is a transport, not the answer]
Format JSON (or your wire format of choice) in a custom formatter and treat the whole rendered message
as one opaque field from spdlog's point of view. spdlog doesn't validate schemas, doesn't type fields,
and doesn't know your event has a shape — it just gets a byte string to a sink fast. If that's not
enough, you want a structured-logging library layered on top, not more out of spdlog itself.
:::

## See also

- <Icon icon="lucide:type" inline /> [Pattern flags](./pattern-flags.md) — the `%s`/`%#`/`%!`/`%@` flags this page relies on.
- <Icon icon="lucide:pencil" inline /> [Custom formatters](./custom-formatters.md) — the mechanism behind both correlation ids and JSON output.
- <Icon icon="lucide:zap" inline /> [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) — what makes the `SPDLOG_*` macros free when disabled.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
