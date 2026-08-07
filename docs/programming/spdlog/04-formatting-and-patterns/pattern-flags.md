---
id: pattern-flags
title: Pattern flags
sidebar_label: Pattern flags
sidebar_position: 1
tags: [c++, spdlog, formatting, patterns]
---

# Pattern flags

The pattern controls the *line around* your message — timestamp, level, logger name, thread id — and
it's set per logger or per sink, not per call. You write `spdlog::info("connected")` once; the
pattern decides whether that becomes `connected` or `[2026-08-07 14:02:11.123] [app] [info]
connected`.

## Setting a pattern

`spdlog::set_pattern(...)` sets the pattern for every registered logger; `logger->set_pattern(...)`
sets it for one logger's sinks that don't have their own override; `sink->set_pattern(...)` sets it
for that sink specifically. The most specific one wins — a sink-level pattern always overrides
whatever the logger or global call set. See
[Multi-sink loggers](../02-loggers-and-registry/multi-sink-loggers.md) for why that matters when
different sinks want different layouts.

## The flag table

| Flag | Meaning | Example output |
|---|---|---|
| `%v` | The actual log message | `connection refused` |
| `%n` | Logger name | `app` |
| `%l` | Level, full name | `info` |
| `%L` | Level, short (single letter) | `I` |
| `%t` | Thread id | `140735` |
| `%P` | Process id | `4242` |
| `%Y` | Year, 4 digits | `2026` |
| `%m` | Month, 2 digits | `08` |
| `%d` | Day, 2 digits | `07` |
| `%H` | Hour, 24h | `14` |
| `%M` | Minute | `02` |
| `%S` | Second | `11` |
| `%e` | Millisecond | `123` |
| `%f` | Microsecond | `123456` |
| `%F` | Nanosecond | `123456789` |
| `%z` | UTC offset | `+00:00` |
| `%+` | spdlog's full default format | `[2026-08-07 14:02:11.123] [app] [info] connected` |
| `%@` | Source location (`file:line`) | `main.cpp:42` |
| `%s` | Source filename, basename only | `main.cpp` |
| `%#` | Source line number | `42` |
| `%!` | Source function name | `handle_request` |

## Color range

`%^` and `%$` bound the span a color sink actually colors — everything outside that range prints in
the terminal's default color regardless of level:

```cpp
sink->set_pattern("[%H:%M:%S] %^[%l]%$ %v");   // only "[info]" (etc.) gets colored
```

## Padding and alignment

Width specifiers between `%` and the flag pad or truncate: `%-8l` left-justifies the level name in an
8-character field; `%8n` right-justifies the logger name in 8 characters.

## Cost

Every flag in a pattern is work performed on every message that passes both the logger and sink level
filters — timestamps in particular involve a syscall-backed clock read.

:::note[%s/%# only carry a value if you use the SPDLOG_* macros]
Calling `spdlog::info(...)` directly never populates source location — `%s`, `%#`, `%!`, and `%@`
render empty unless the call went through `SPDLOG_INFO(...)` or one of the other `SPDLOG_*` macros.
See [Source location and structured logging](./source-location-and-structured-logging.md) for why.
:::

## Recommended patterns

A short list to start from:

- **Dev, human-readable:** `"[%H:%M:%S] %^[%l]%$ %v"` — fast to scan, colored, no date noise.
- **Production, machine-parseable:** a fixed-width, unambiguous format that log tooling can split on.
- **Minimal console:** `"%v"` — just the message, for tools that already prefix their own timestamp.

:::tip[A production pattern worth copying]
```
[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v
```
Full timestamp to the millisecond, logger name, level, message — sortable, greppable, and unambiguous
across timezones if you also fix the process to UTC.
:::

## See also

- <Icon icon="lucide:pencil" inline /> [Custom formatters](./custom-formatters.md) — adding your own flag when none of these carry the field you need.
- <Icon icon="lucide:map-pin" inline /> [Source location and structured logging](./source-location-and-structured-logging.md) — the `%s`/`%#`/`%!`/`%@` flags in depth.
- <Icon icon="lucide:type" inline /> [Basic formatting](../01-basics/basic-formatting.md) — formatting the message itself, not the line around it.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
