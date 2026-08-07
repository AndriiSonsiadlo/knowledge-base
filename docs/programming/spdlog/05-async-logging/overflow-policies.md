---
id: overflow-policies
title: Overflow policies
sidebar_label: Overflow policies
sidebar_position: 2
tags: [c++, spdlog, async, backpressure]
---

# Overflow policies

The async queue is bounded, so at some point the producer (your application logging quickly) outruns
the consumer (the worker thread writing to a slow sink). The overflow policy decides which guarantee
you give up when that happens: latency, or completeness.

## The policies

| Policy | On a full queue | You lose | Use when |
|---|---|---|---|
| `block` | Caller thread stalls until space frees | Nothing — every message eventually logs | Correctness of the log matters more than latency |
| `overrun_oldest` | The oldest queued message is dropped, caller never stalls | Old messages, silently | Latency matters more than completeness |

:::note[Newer spdlog releases add discard_new]
Some spdlog versions also expose a `discard_new` policy (drop the incoming message instead of the
oldest queued one). Check the version you're actually building against rather than assuming it's
available — it isn't in every release.
:::

## Setting the policy

```cpp showLineNumbers
auto tp = std::make_shared<spdlog::details::thread_pool>(8192, 1);
auto sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "logs/app.log", 1024 * 1024 * 10, 3);

auto logger = std::make_shared<spdlog::async_logger>(
    "app", sink, tp, spdlog::async_overflow_policy::overrun_oldest);
```

Or use the shortcut factory, which sets `overrun_oldest` for you:

```cpp
auto logger = spdlog::create_async_nb<spdlog::sinks::rotating_file_sink_mt>(
    "app", "logs/app.log", 1024 * 1024 * 10, 3);
```

## block

:::danger[block turns a slow disk into application latency — including in your request path]
If the sink can't keep up (a slow disk, a syslog daemon under load, a network sink), `block` means
the *next* log call from your application stalls until space frees in the queue. In a request-handling
thread, that turns "logging is slow" into "requests are slow" — the exact latency problem async
logging was supposed to avoid.
:::

## overrun_oldest

:::danger[Dropped messages are silent — the log looks complete and isn't]
There's no gap marker, no "N messages dropped" line by default. A log that overran looks exactly like
a log that didn't, until you notice the message you needed isn't there. If you rely on
`overrun_oldest`, budget for the possibility that any given message might be missing.
:::

## Sizing the queue instead

The real fix for chronic overflow is usually a bigger queue paired with a faster sink, not picking
the "least bad" overflow policy. For a queue of `N` entries at roughly 200 bytes each (typical for a
short formatted message), `N = 8192` costs on the order of 1.6 MB — cheap insurance against a burst
that would otherwise trigger the overflow policy at all.

## Choosing

:::note[Audit/compliance logs → block. Diagnostic logs in a latency-sensitive service → overrun_oldest.]
If a missing log line is a compliance problem, accept the latency risk of `block` and size your queue
generously. If a missing debug line is a minor inconvenience but a latency spike is a real cost,
`overrun_oldest` is the right default.
:::

## See also

- <Icon icon="lucide:waypoints" inline /> [Thread pool and async logger](./thread-pool-and-async-logger.md) — where the queue and workers live.
- <Icon icon="lucide:scale" inline /> [Async vs sync trade-offs](./async-vs-sync-tradeoffs.md) — whether the trade is worth making at all.
- <Icon icon="lucide:droplets" inline /> [Flush policies](../06-performance-and-configuration/flush-policies.md) — the durability question that overlaps with overflow.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
