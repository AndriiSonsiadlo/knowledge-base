---
id: flush-policies
title: Flush policies
sidebar_label: Flush policies
sidebar_position: 3
tags: [c++, spdlog, durability, flush]
---

# Flush policies

A log line that's still sitting in a buffer when the process dies never existed, as far as anyone
debugging the crash is concerned. Flushing is the knob between durability (get it to disk now) and
throughput (batch writes, flush less often) — spdlog gives you several ways to set it.

## Manual flush

```cpp
logger->flush();          // one logger
spdlog::apply_all([](auto l) { l->flush(); });   // every registered logger
```

## flush_on(level)

Flush automatically whenever a message at or above a given level is logged:

```cpp
logger->flush_on(spdlog::level::err);   // any err/critical message triggers an immediate flush
```

Messages below that level are still buffered normally — only reaching the threshold forces the flush.

## Periodic flush

```cpp
spdlog::flush_every(std::chrono::seconds(3));
```

This starts a background thread that flushes every registered logger on a timer, independent of
message level.

:::danger[flush_every's worker interacts with static destruction — call spdlog::shutdown() before exit]
The periodic-flush background thread is itself a piece of global state with its own shutdown
requirements. Not calling `spdlog::shutdown()` before the process exits risks the thread still running
(or being torn down in an unspecified order relative to other statics) during global destruction. See
[Logger lifecycle](../02-loggers-and-registry/logger-lifecycle.md) for the general shutdown-ordering
picture.
:::

## Comparison table

| Policy | Durability | Throughput cost | Use when |
|---|---|---|---|
| Never / manual only | Whatever's buffered at crash time is lost | None | Logs are purely diagnostic, loss is acceptable |
| `flush_on(err)` | Errors and above always survive | Small — only on error-level messages | The default for most services |
| `flush_every(Ns)` | Bounded loss window of `N` seconds | Small, amortized | Combine with `flush_on(err)` for belt-and-suspenders |
| Flush every message | Nothing is ever lost | High — one flush syscall per log call | Audit logs, compliance requirements |

## Async and flush

A flush on an async logger has to drain whatever's still queued before it can actually flush the
sink.

:::note[flush() on an async logger blocks until the worker has drained]
Calling `logger->flush()` on an async logger is a synchronous call from the caller's point of view —
it waits for the background worker to catch up. See
[Thread pool and async logger](../05-async-logging/thread-pool-and-async-logger.md) for what's
actually happening on the other end of that wait.
:::

## Recommended default

:::tip[flush_on(err) plus flush_every(3s) is the setting most services should start with]
Error-level messages hit disk immediately (you don't lose your last words on failure), and everything
else gets flushed at least every few seconds without paying a flush cost on every single log call.
:::

## See also

- <Icon icon="lucide:settings" inline /> [Global settings and best practices](./global-settings-and-best-practices.md) — flush policy as part of a full setup.
- <Icon icon="lucide:file-text" inline /> [File sinks](../03-sinks/file-sinks.md) — the durability trade-off this page addresses.
- <Icon icon="lucide:gauge" inline /> [Overflow policies](../05-async-logging/overflow-policies.md) — the other way async logging can lose messages.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
