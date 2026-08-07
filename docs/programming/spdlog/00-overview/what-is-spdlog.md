---
id: what-is-spdlog
title: What is spdlog?
sidebar_label: What is spdlog
sidebar_position: 1
tags: [c++, spdlog, overview, introduction]
---

# What is spdlog?

For a long time, logging in C++ meant one of two things: hand-rolled `iostream` chains guarded by
`#ifdef DEBUG`, or a macro-heavy framework like log4cplus that made you write an XML config file
before your first log line appeared. Both worked, and both were slow enough or awkward enough that
teams either logged too little or paid for it in the profiler.

spdlog optimised for the opposite of that experience: speed first, and a setup you can do in under
five minutes. It is header-only by default (drop it in, `#include`, done), it uses
[fmt](https://github.com/fmtlib/fmt)'s `{}` formatting instead of `printf` or streams, and its
common-case throughput is measured in millions of messages per second — fast enough that "just log
it" is usually the right call instead of a performance trade-off you have to justify.

## The shape of the library

Three types cover almost everything you'll touch:

- A **logger** decides *whether* a message gets logged, based on a level.
- A **sink** decides *where* an accepted message goes — console, file, syslog, wherever.
- A **formatter** decides *how* the message is rendered before it reaches the sink.

A logger owns one or more sinks; each sink owns a formatter. That's the whole architecture, and it's
why the API scales from "one call, colored console output" to "five sinks, custom binary format,
async delivery" without changing shape. See [Design philosophy](./design-philosophy.md) for why it's
built this way.

## A first taste

```cpp showLineNumbers title="hello_log.cpp"
#include "spdlog/spdlog.h"

int main() {
    spdlog::info("application starting, pid={}", 4242);
    spdlog::warn("cache miss rate is {:.1f}%", 12.5);
    spdlog::error("failed to open {}: {}", "config.yaml", "no such file");

    spdlog::set_pattern("[%H:%M:%S] [%^%l%$] %v");
    spdlog::info("this line uses the new pattern");
}
```

No setup function, no config file — the default logger is ready as soon as `spdlog::spdlog.h` is
included.

## What you get out of the box

- Colored console output (with plain-text fallback when stdout isn't a TTY)
- Rotating and daily-rotated file sinks
- Syslog / systemd journal / Windows Event Log integration
- Async logging via a background thread pool
- An in-memory backtrace ring buffer for "show me what led up to this crash"
- Compile-time log-level filtering that deletes disabled calls entirely

## What it is not

spdlog is a logging *library*, not a logging *platform*. It does not ship:

- Log shipping or aggregation — pair it with your existing pipeline (journald, Fluentd, a sidecar)
- Structured/JSON output built in — it logs formatted text lines
- A configuration file format — configuration is C++ calls, not YAML/INI

:::note[Structured logging is a workaround, not a feature]
If you need typed, machine-parseable events rather than text lines, spdlog can still get you there —
see [Source location and structured logging](../04-formatting-and-patterns/source-location-and-structured-logging.md)
for the custom-formatter approach.
:::

## See also

- <Icon icon="lucide:download" inline /> [Installation and integration](./installation-and-integration.md) — header-only vs compiled, CMake, package managers.
- <Icon icon="lucide:compass" inline /> [Design philosophy](./design-philosophy.md) — why loggers, sinks, and fmt are the whole story.
- <Icon icon="lucide:rocket" inline /> [Quick start](../01-basics/quick-start.md) — a complete first program.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
