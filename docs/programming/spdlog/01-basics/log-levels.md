---
id: log-levels
title: Log levels
sidebar_label: Log levels
sidebar_position: 2
tags: [c++, spdlog, basics, levels, filtering]
---

# Log levels

Levels aren't one filter, they're two: a runtime one that lives per logger (and optionally per sink),
and a compile-time one that deletes the call site entirely before the compiler even sees it as a
function call. Confusing the two is the most common reason "I set the level but nothing changed."

## The six levels

| Level | enum | Intended for |
|---|---|---|
| `trace` | `spdlog::level::trace` | Extremely verbose, per-iteration detail — off by default even in dev |
| `debug` | `spdlog::level::debug` | Development diagnostics, disabled in production |
| `info` | `spdlog::level::info` | Normal operational messages — the default level |
| `warn` | `spdlog::level::warn` | Something unexpected but recoverable |
| `err` | `spdlog::level::err` | An operation failed |
| `critical` | `spdlog::level::critical` | The process can't continue meaningfully |
| `off` | `spdlog::level::off` | Suppresses everything, including `critical` |

## Runtime filtering

`logger->set_level(spdlog::level::debug)` changes one logger; `spdlog::set_level(...)` changes every
*registered* logger at once. Independently, each **sink** can also have its own level via
`sink->set_level(...)`.

:::danger[A message must pass both the logger level and the sink level]
```cpp
auto sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
sink->set_level(spdlog::level::warn);   // sink drops anything below warn

auto log = std::make_shared<spdlog::logger>("app", sink);
log->set_level(spdlog::level::debug);   // logger itself is happy to pass debug+

log->debug("this is silently dropped by the sink, not the logger");
log->warn("this gets through — it passes both filters");
```
Whichever filter is stricter wins. If a message vanishes, check the sink level before assuming the
logger level is wrong.
:::

## Compile-time filtering

`SPDLOG_ACTIVE_LEVEL` and the matching `SPDLOG_TRACE`/`SPDLOG_DEBUG`/`SPDLOG_INFO`/... macros remove
disabled calls at compile time — arguments included, so an expensive-to-format argument at a disabled
level costs nothing at runtime.

```cmake
target_compile_definitions(app PRIVATE SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_DEBUG)
```

See [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) for the
full mechanism, including the ODR hazard of mixing values across translation units.

## Level from environment

`spdlog::cfg::load_env_levels()` reads `SPDLOG_LEVEL` and applies it to loggers by name:

```bash
SPDLOG_LEVEL=info,app=debug ./myapp
```

That sets the global default to `info` and overrides the `"app"` logger specifically to `debug`.

:::tip[Env-var levels are the cheapest runtime config you'll ever add]
One call at startup (`spdlog::cfg::load_env_levels()`) gets you per-deployment, per-logger level
control with zero configuration-file machinery.
:::

## Which mechanism when

| | Runtime level | Sink level | Compile-time macro |
|---|---|---|---|
| Cost when disabled | One comparison | One comparison, after formatting starts | Zero — code doesn't exist |
| Granularity | Per logger | Per sink | Whole binary (or per-TU if you're not careful) |
| Changeable without rebuild | Yes | Yes | No |

## See also

- <Icon icon="lucide:rocket" inline /> [Quick start](./quick-start.md) — where `set_level` first shows up.
- <Icon icon="lucide:zap" inline /> [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) — deleting disabled calls entirely.
- <Icon icon="lucide:layers" inline /> [Multi-sink loggers](../02-loggers-and-registry/multi-sink-loggers.md) — per-sink levels in practice.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
