---
id: backtrace-and-crash-dump
title: Backtrace and crash dump
sidebar_label: Backtrace
sidebar_position: 2
tags: [c++, spdlog, diagnostics, backtrace]
---

# Backtrace and crash dump

The messages you want after a failure are almost always the debug-level ones you weren't writing to
the log — too verbose for normal operation, exactly what you need once something's gone wrong. The
backtrace ring buffer keeps those messages in memory and only emits them on demand, when a failure
actually happens.

## enable_backtrace

```cpp
spdlog::enable_backtrace(32);        // global: 32-message ring
logger->enable_backtrace(32);        // per-logger
```

Once enabled, messages below the logger's active level are stored in the ring instead of being
dropped outright — they still don't reach any sink until you explicitly dump the ring.

## Dumping

```cpp showLineNumbers title="backtrace_demo.cpp"
spdlog::enable_backtrace(32);
spdlog::set_level(spdlog::level::info);   // debug messages go to the ring, not stdout

for (int i = 0; i < 100; ++i) {
    spdlog::debug("processing item {}", i);   // stored in the ring, not printed
}

try {
    risky_operation();
} catch (const std::exception& e) {
    spdlog::error("risky_operation failed: {}", e.what());
    spdlog::dump_backtrace();   // now the last 32 debug lines are emitted too
}
```

`spdlog::dump_backtrace()` dumps every logger's ring; `logger->dump_backtrace()` dumps just one.

## Cost

:::danger[With backtrace enabled, a runtime-disabled debug log is no longer free]
Normally a `debug` call below the active level costs one comparison and nothing else. With backtrace
enabled, that same call still formats its arguments and copies the result into the ring buffer — the
whole point is to retain what would otherwise be discarded, which means the "disabled log is free"
assumption from [Compile-time log level](./compile-time-log-level.md) no longer holds for backtrace-
enabled loggers.
:::

## Interaction with compile-time levels

:::note[Compile-time filtering wins over backtrace — keep SPDLOG_ACTIVE_LEVEL at trace if you rely on backtrace]
A message elided at compile time by `SPDLOG_ACTIVE_LEVEL` never executes at all, so it never reaches
the backtrace ring either. If you want backtrace to actually capture trace/debug detail, your build's
`SPDLOG_ACTIVE_LEVEL` has to be low enough to let those calls exist in the first place — backtrace
only filters what already compiled.
:::

## Crash handlers

Logging from inside a signal handler (`SIGSEGV`, `SIGABRT`) is unsafe — spdlog's internals allocate,
lock mutexes, and call into the C++ runtime, none of which are guaranteed safe to do inside a signal
handler.

:::danger[spdlog calls are not async-signal-safe — do not log from a signal handler]
What's realistic instead: have the signal handler set a flag or write a minimal marker using only
async-signal-safe calls (`write()` to a raw fd), then perform actual spdlog logging (including a
backtrace dump) from a safe context afterward — a watchdog process, a `atexit`/terminate handler that
runs before full unwind, or a supervisor that restarts and inspects state.
:::

## See also

- <Icon icon="lucide:droplets" inline /> [Flush policies](./flush-policies.md) — making sure the dump actually reaches disk.
- <Icon icon="lucide:zap" inline /> [Compile-time log level](./compile-time-log-level.md) — the filtering layer that runs before backtrace ever sees a message.
- <Icon icon="lucide:scale" inline /> [Async vs sync trade-offs](../05-async-logging/async-vs-sync-tradeoffs.md) — the other tool for "don't lose the last words before a crash."
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
