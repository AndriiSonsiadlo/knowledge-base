---
id: rotating-and-daily-sinks
title: Rotating and daily sinks
sidebar_label: Rotating and daily
sidebar_position: 4
tags: [c++, spdlog, sinks, rotation, files]
---

# Rotating and daily sinks

Two different answers to "the log file cannot grow forever": rotate by size whenever the current file
gets too big, or start a fresh file on a schedule regardless of size.

## rotating_file_sink

```cpp showLineNumbers
auto sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "logs/app.log",
    1024 * 1024 * 10,   // max_size: 10 MB per file
    5                    // max_files: keep 5 rotated files
);
```

When `app.log` reaches `max_size`, it's renamed `app.1.log`, the previous `app.1.log` becomes
`app.2.log`, and so on up to `max_files`; the oldest file beyond that count is deleted, and a fresh
`app.log` is opened.

## daily_file_sink

```cpp
auto sink = std::make_shared<spdlog::sinks::daily_file_sink_mt>(
    "logs/app", 2, 30);   // roll at 02:30 local time
```

The filename gets a date stamp (`app_2026-08-07.log`), a new file opens at the given hour:minute each
day, and an optional `max_files` retention parameter (a later overload) deletes files older than that
many days.

## Comparison table

| | rotating | daily |
|---|---|---|
| Disk-usage bound | Yes — `max_size × max_files` | Only if `max_files` retention is set |
| Filename predictability | Numbered suffix, changes as it rotates | Date-stamped, one file per day |
| Process running minutes | May never rotate at all | Still produces one dated file |
| Process running months | Rotates repeatedly, bounded total size | One new file every day, unbounded unless retention is set |
| External logrotate | Redundant/conflicting — spdlog already rotates | Same — don't combine |

## Rotation on open

`rotating_file_sink_mt` accepts a `rotate_on_open` flag — when `true`, the sink rotates immediately on
construction rather than waiting for `max_size` to be hit. Use it when you want a guaranteed fresh
file per process run instead of appending to whatever's already there.

## Interaction with logrotate

:::danger[Do not point external logrotate at a file spdlog holds open — the writes go to the unlinked inode]
If an external tool renames or removes the file spdlog has open, spdlog keeps writing to the original
(now unlinked) file descriptor — the data goes nowhere anyone can read it until the process restarts
and reopens the path. Let spdlog own rotation for files it writes; don't layer logrotate on top.
:::

## Choosing

:::note[Bound by disk quota → rotating. Bound by "one file per day for ops" → daily.]
Reach for `rotating_file_sink` when the constraint is "don't let logs eat the disk." Reach for
`daily_file_sink` when the constraint is operational — humans or tooling expect one file per calendar
day regardless of volume.
:::

## See also

- <Icon icon="lucide:file-text" inline /> [File sinks](./file-sinks.md) — the unbounded baseline this improves on.
- <Icon icon="lucide:layers" inline /> [Sink overview](./sink-overview.md) — the shared sink interface.
- <Icon icon="lucide:droplets" inline /> [Flush policies](../06-performance-and-configuration/flush-policies.md) — durability alongside rotation.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
