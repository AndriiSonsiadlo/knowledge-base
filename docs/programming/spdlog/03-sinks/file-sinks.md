---
id: file-sinks
title: File sinks
sidebar_label: File sinks
sidebar_position: 3
tags: [c++, spdlog, sinks, files]
---

# File sinks

The simplest durable destination — and the one whose failure modes (permissions, unbounded growth,
buffering) don't show up until production.

## basic_file_sink

```cpp showLineNumbers
auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/app.log");
auto logger = std::make_shared<spdlog::logger>("file", sink);
```

Or the one-line factory equivalent:

```cpp
auto logger = spdlog::basic_logger_mt("file", "logs/app.log");
```

## Truncate vs append

The `basic_file_sink_mt` constructor takes an optional `truncate` flag (default `false`):

| `truncate` | Behaviour on restart |
|---|---|
| `false` (default) | Appends to the existing file — history is preserved |
| `true` | Empties the file on open — clean slate every run |

## Directory creation

spdlog creates any missing directories in the log path for you — `spdlog::basic_logger_mt("app",
"logs/nested/app.log")` doesn't require `logs/nested/` to exist beforehand. If it can't create the
directory or open the file (permissions, a full disk), it throws `spdlog::spdlog_ex` from the
constructor.

## Buffering and durability

Writes to a file sink are buffered by the C++ standard library / OS before they hit disk.

:::danger[A crash loses everything not yet flushed]
A `basic_file_sink` doesn't flush on every message by default. If the process crashes (segfault,
`abort`, power loss), whatever's still sitting in the buffer never reaches disk. See
[Flush policies](../06-performance-and-configuration/flush-policies.md) for `flush_on(level)` and
periodic flushing.
:::

## Unbounded growth

:::note[basic_file_sink never rotates — use a rotating or daily sink for anything long-lived]
`basic_file_sink` writes to one file forever. For a short script that's fine; for a service that runs
for weeks, that file grows without bound. Use
[Rotating and daily sinks](./rotating-and-daily-sinks.md) instead for anything that isn't a one-shot
run.
:::

## See also

- <Icon icon="lucide:refresh-cw" inline /> [Rotating and daily sinks](./rotating-and-daily-sinks.md) — the bounded-growth alternative.
- <Icon icon="lucide:layers" inline /> [Sink overview](./sink-overview.md) — the shared sink interface.
- <Icon icon="lucide:droplets" inline /> [Flush policies](../06-performance-and-configuration/flush-policies.md) — durability vs throughput.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
