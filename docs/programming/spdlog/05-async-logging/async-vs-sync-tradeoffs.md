---
id: async-vs-sync-tradeoffs
title: Async vs sync trade-offs
sidebar_label: Async vs sync
sidebar_position: 3
tags: [c++, spdlog, async, performance, latency]
---

# Async vs sync trade-offs

Async logging is not strictly better than sync — it trades tail latency and complexity for
throughput, and it changes what "the log survived the crash" actually means. Reach for it because
you've measured a problem it solves, not by default.

## Comparison table

| | Sync logger | Async logger |
|---|---|---|
| Caller-thread cost | Format + write, on the caller | Format + queue copy, on the caller |
| Throughput | Bounded by sink I/O speed | Bounded by queue drain rate |
| Message ordering | Always call order | Guaranteed only with one worker thread |
| Memory | Minimal | Queue size × per-message cost |
| Crash durability | Whatever's flushed survives | Anything still queued is lost |
| Shutdown complexity | Trivial | Must drain and join workers |
| Debuggability | Log line appears exactly when logged | Log line can lag behind real time |

## When async wins

High message rates where the caller thread can't afford to wait on I/O; slow sinks (network
destinations, syslog under load, a rotating file sink on a busy disk); latency-sensitive callers where
even a few hundred microseconds of synchronous file I/O per request adds up.

## When async loses

Low log volume where sync I/O was never the bottleneck; short-lived processes where the thread pool's
own startup/shutdown overhead outweighs anything it saves; anything where a message lost on crash is
unacceptable; tests that assert on log output synchronously and don't want to wait for or coordinate
with a background worker.

## The crash case

:::danger[Messages sitting in the async queue are lost on abort]
A sync logger with `flush_on(err)` writes the last words before a crash to disk before the process
actually dies. An async logger's queued messages are still in memory when `abort()`/segfault happens
— they never reach the sink. If "what led up to the crash" matters, keep a sync logger (or a sync
error-level path) for exactly that purpose. See
[Flush policies](../06-performance-and-configuration/flush-policies.md) and
[Backtrace and crash dump](../06-performance-and-configuration/backtrace-and-crash-dump.md) for
complementary approaches to the same problem.
:::

## The middle ground

A common pattern: keep console/error output on a synchronous logger (low volume, and you want it
immediately) while routing high-volume diagnostic logging through an async logger. Two loggers, not
one — see [Multi-sink loggers](../02-loggers-and-registry/multi-sink-loggers.md) if you want to
combine destinations within a single sync or single async logger instead.

## Measuring before switching

:::tip[Measure the caller-thread cost of your existing logger first]
With compile-time level filtering in place, most disabled log calls already cost effectively nothing
— see [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md). Profile
before assuming async is the fix; often the actual cost is enabled logs at a level you didn't need to
enable in production.
:::

## See also

- <Icon icon="lucide:waypoints" inline /> [Thread pool and async logger](./thread-pool-and-async-logger.md) — the mechanism behind the async column above.
- <Icon icon="lucide:gauge" inline /> [Overflow policies](./overflow-policies.md) — what happens when async can't keep up.
- <Icon icon="lucide:zap" inline /> [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md) — the cheaper fix to check first.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
