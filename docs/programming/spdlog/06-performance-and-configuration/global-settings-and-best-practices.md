---
id: global-settings-and-best-practices
title: Global settings and best practices
sidebar_label: Best practices
sidebar_position: 4
tags: [c++, spdlog, configuration, best-practices]
---

# Global settings and best practices

spdlog's globals — the registry, the default logger, the registry-wide setters — are what make the
five-minute setup possible. They're also what makes a thousand-file codebase confusing if nobody ever
decided the policy on purpose. This page is the one place to make that decision.

## The global setters

| Call | Affects |
|---|---|
| `spdlog::set_level(level)` | Runtime level of every registered logger |
| `spdlog::set_pattern(pattern)` | Pattern of every registered logger's sinks (unless overridden per sink) |
| `spdlog::flush_on(level)` | Flush trigger level for every registered logger |
| `spdlog::set_default_logger(logger)` | What `spdlog::info(...)` and friends log through |
| `spdlog::set_error_handler(fn)` | What runs when a sink throws during logging |
| `spdlog::set_automatic_registration(bool)` | Whether factory helpers add new loggers to the registry |
| `spdlog::apply_all(fn)` | Runs `fn` against every registered logger — for anything not covered above |

## A canonical init function

```cpp showLineNumbers title="logging_init.cpp"
void init_logging() {
    std::vector<spdlog::sink_ptr> sinks;

    auto console = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console->set_level(spdlog::level::warn);
    console->set_pattern("[%^%l%$] %v");
    sinks.push_back(console);

    auto file = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
        "logs/app.log", 1024 * 1024 * 10, 5);
    file->set_level(spdlog::level::debug);
    file->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v");
    sinks.push_back(file);

    auto logger = std::make_shared<spdlog::logger>("app", sinks.begin(), sinks.end());
    logger->set_level(spdlog::level::debug);
    logger->flush_on(spdlog::level::err);

    spdlog::set_default_logger(logger);
    spdlog::set_error_handler([](const std::string& msg) {
        std::fprintf(stderr, "spdlog internal error: %s\n", msg.c_str());
    });
}
```

Call this once, early in `main()`, and every unqualified `spdlog::info(...)` call in the rest of the
program routes through it without further setup.

## Error handling

`spdlog::set_error_handler(...)` installs a handler for exceptions thrown *inside* spdlog's own
logging path (a sink's write failing, for example) — it's how you find out logging itself broke,
without that failure taking down the calling code. Left unset, spdlog's default handler prints a
message to stderr and continues.

:::danger[An exception escaping your error handler terminates the process]
The error handler runs inside spdlog's internals; letting an exception propagate out of it is
undefined behavior in that context and typically ends in `std::terminate`. Keep the handler simple
and exception-free — log to stderr, increment a counter, nothing that can itself throw.
:::

## Library code vs application code

:::note[A library should take a logger, not create one — or at minimum disable automatic registration]
Library code that calls `spdlog::stdout_color_mt("mylib")` registers a name into the *application's*
registry, where it can collide with a name the application chose, and shows up in the application's
`apply_all` calls whether or not that's wanted. Prefer accepting a `std::shared_ptr<spdlog::logger>`
from the caller; if you must create your own, disable automatic registration first — see
[The registry](../02-loggers-and-registry/the-registry.md) for the mechanism.
:::

## Pitfalls checklist

- Using an `_st` sink from more than one thread — see [Creating loggers](../02-loggers-and-registry/creating-loggers.md).
- Calling `spdlog::get` in a hot loop instead of caching the `shared_ptr` — see [Logger lifecycle](../02-loggers-and-registry/logger-lifecycle.md).
- Logging after `spdlog::shutdown()`, or from a static destructor — see [Logger lifecycle](../02-loggers-and-registry/logger-lifecycle.md).
- `SPDLOG_ACTIVE_LEVEL` set inconsistently across translation units — see [Compile-time log level](./compile-time-log-level.md).
- `overrun_oldest` dropping messages silently — see [Overflow policies](../05-async-logging/overflow-policies.md).
- ANSI color codes ending up in a redirected log file — see [Console sinks](../03-sinks/console-sinks.md).
- External `logrotate` pointed at a file spdlog still has open — see [Rotating and daily sinks](../03-sinks/rotating-and-daily-sinks.md).
- Expensive arguments still evaluated at a runtime-disabled level — see [Basic formatting](../01-basics/basic-formatting.md).

## A production baseline

1. Set `SPDLOG_ACTIVE_LEVEL` per build type — trace/debug in debug builds, info in release.
2. Use one multi-sink logger as the application default rather than scattering ad hoc loggers.
3. Use a machine-parseable, timestamped pattern in file/production sinks.
4. Set `flush_on(err)` plus `flush_every(3s)`.
5. Reach for async only after measuring that synchronous I/O is actually the bottleneck.
6. Call `spdlog::shutdown()` at the very end of `main()`, after every other subsystem has stopped
   logging.

## See also

- <Icon icon="lucide:droplets" inline /> [Flush policies](./flush-policies.md) — the durability half of the baseline above.
- <Icon icon="lucide:zap" inline /> [Compile-time log level](./compile-time-log-level.md) — the build-type-dependent piece of the baseline.
- <Icon icon="lucide:list-tree" inline /> [The registry](../02-loggers-and-registry/the-registry.md) — what the global setters actually operate on.
- <Icon icon="lucide:scale" inline /> [Async vs sync trade-offs](../05-async-logging/async-vs-sync-tradeoffs.md) — deciding whether step 5 applies to you.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
