---
id: creating-loggers
title: Creating loggers
sidebar_label: Creating loggers
sidebar_position: 1
tags: [c++, spdlog, loggers, factory]
---

# Creating loggers

There are two ways to make a logger: the factory helpers, which build a sink and register the logger
in one call, and explicit construction, for when you want to own the sinks yourself or avoid the
global registry entirely.

## Factory helpers

| Factory | Sink created | Registered |
|---|---|---|
| `spdlog::stdout_color_mt(name)` | Colored console (stdout) | Yes |
| `spdlog::stderr_color_mt(name)` | Colored console (stderr) | Yes |
| `spdlog::basic_logger_mt(name, path)` | Plain file, no rotation | Yes |
| `spdlog::rotating_logger_mt(name, path, max_size, max_files)` | Size-based rotating file | Yes |
| `spdlog::daily_logger_mt(name, path, hour, minute)` | Date-stamped daily file | Yes |

Every one of these both creates the logger *and* registers it, so `spdlog::get(name)` finds it
afterward from anywhere in the program.

## _mt vs _st

Every factory has an `_mt` (mutex-protected sink) and `_st` (single-threaded, unguarded) variant —
`stdout_color_st`, `basic_logger_st`, and so on.

:::danger[Using an _st logger from two threads is a data race]
`_st` sinks skip locking entirely for speed. If more than one thread can reach the same `_st` logger,
you have a data race the sanitizers will eventually find — or worse, won't. Default to `_mt`; only
drop to `_st` for a logger you've confirmed is genuinely single-threaded.
:::

## Explicit construction

Build the sink and logger yourself when you want to configure the sink before it's attached, share a
sink between loggers, or skip automatic registration:

```cpp showLineNumbers
auto sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
sink->set_level(spdlog::level::warn);

auto logger = std::make_shared<spdlog::logger>("app", sink);
logger->set_level(spdlog::level::debug);

spdlog::register_logger(logger);   // optional — makes spdlog::get("app") work
```

## Duplicate names

The factory helpers throw `spdlog::spdlog_ex` if a logger with that name is already registered.
Either `spdlog::drop(name)` first, or use explicit construction and skip `register_logger` if you
don't need the name to be globally reachable — see [The registry](./the-registry.md) for what
registration actually buys you.

## Per-logger configuration

`set_level`, `set_pattern`, and `flush_on` called on a logger apply to *all* of its sinks unless an
individual sink has its own override — a sink-level `set_pattern`/`set_level` wins for that sink. See
[Multi-sink loggers](./multi-sink-loggers.md) for the common case of different settings per
destination.

## See also

- <Icon icon="lucide:list-tree" inline /> [The registry](./the-registry.md) — what registration means and costs.
- <Icon icon="lucide:layers" inline /> [Multi-sink loggers](./multi-sink-loggers.md) — one logger, several sinks.
- <Icon icon="lucide:plug" inline /> [Sink overview](../03-sinks/sink-overview.md) — what a sink actually is.
- <Icon icon="lucide:rocket" inline /> [Quick start](../01-basics/quick-start.md) — the factory helpers in a first program.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
