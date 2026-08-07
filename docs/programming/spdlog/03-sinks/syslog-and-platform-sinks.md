---
id: syslog-and-platform-sinks
title: Syslog and platform sinks
sidebar_label: Platform sinks
sidebar_position: 5
tags: [c++, spdlog, sinks, syslog, platform]
---

# Syslog and platform sinks

When the platform already owns log collection — syslog, the systemd journal, the Windows Event Log —
writing your own file and reinventing rotation, retention, and shipping is the wrong answer.

## syslog_sink

`spdlog/sinks/syslog_sink.h` wraps POSIX `syslog(3)`. Construction takes an ident string and a
facility (`LOG_USER`, `LOG_DAEMON`, etc.); spdlog levels map onto syslog priorities:

| spdlog level | syslog priority |
|---|---|
| `trace`, `debug` | `LOG_DEBUG` |
| `info` | `LOG_INFO` |
| `warn` | `LOG_WARNING` |
| `err` | `LOG_ERR` |
| `critical` | `LOG_CRIT` |

## systemd journal

`systemd_sink` writes directly to the systemd journal via `sd_journal_send`, rather than through
syslog. The practical difference: the journal is structured (you can attach extra fields, and
`journalctl` can query them), and you don't format your own timestamp — the journal stamps entries
itself, so a timestamp pattern flag in your logger's pattern is redundant here.

## Windows event log and debugger

`win_eventlog_sink` writes to the Windows Event Log, the closest Windows equivalent to syslog — useful
for services managed by the Service Control Manager. `msvc_sink` writes via `OutputDebugString`
instead, which shows up in the Visual Studio output window and any attached debugger; it's a
development-time tool, not a production destination.

## Android

`android_sink` maps onto `__android_log_write`, so output shows up in `adb logcat` under the tag you
provide, using the platform's own level constants under the hood.

## Portability

| Sink | Platform | Header |
|---|---|---|
| `syslog_sink` | POSIX (Linux, macOS, BSD) | `spdlog/sinks/syslog_sink.h` |
| `systemd_sink` | Linux with systemd | `spdlog/sinks/systemd_sink.h` |
| `win_eventlog_sink` | Windows | `spdlog/sinks/win_eventlog_sink.h` |
| `msvc_sink` | Windows (MSVC/debugger) | `spdlog/sinks/msvc_sink.h` |
| `android_sink` | Android | `spdlog/sinks/android_sink.h` |

:::danger[These headers are platform-specific — including them unconditionally breaks cross-platform builds]
`#include "spdlog/sinks/syslog_sink.h"` on Windows, or `win_eventlog_sink.h` on Linux, won't compile.
Guard these includes and the code that uses them behind the same platform macros you use elsewhere
(`#ifdef _WIN32`, `#ifdef __linux__`), or isolate them behind a small platform-logging module that the
rest of the codebase doesn't need to know about.
:::

## See also

- <Icon icon="lucide:layers" inline /> [Sink overview](./sink-overview.md) — the shared sink interface these all implement.
- <Icon icon="lucide:wrench" inline /> [Custom sinks](./custom-sinks.md) — for platform integrations spdlog doesn't ship.
- <Icon icon="lucide:terminal" inline /> [Console sinks](./console-sinks.md) — the portable fallback.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
