---
id: quick-start
title: Quick start
sidebar_label: Quick start
sidebar_position: 1
tags: [c++, spdlog, basics, getting-started]
---

# Quick start

The default logger exists so that adding logging to a program is one include and one call. Everything
else in these docs — named loggers, sinks, patterns, async — is about outgrowing the default logger
once a program has more than one component or more than one destination for its logs.

## The default logger

`spdlog::info(...)`, `spdlog::warn(...)`, `spdlog::error(...)`, and friends are free functions that
log through spdlog's default logger. Out of the box, that logger writes to stdout, in color, at
`info` level and above (`trace` and `debug` are filtered out until you raise the level).

## A complete first program

```cpp showLineNumbers title="main.cpp"
#include "spdlog/spdlog.h"

int main() {
    spdlog::set_level(spdlog::level::debug);          // now debug+ is visible
    spdlog::set_pattern("[%H:%M:%S] [%^%l%$] %v");     // short, colored pattern

    spdlog::debug("loading configuration from {}", "config.yaml");
    spdlog::info("server listening on port {}", 8080);
    spdlog::warn("{} of {} worker threads started", 3, 4);

    return 0;
}
```

## Naming your own logger

The default logger is fine for a small program; the moment you have more than one component, a
named logger lets you tell them apart in output and configure them independently:

```cpp showLineNumbers
auto log = spdlog::stdout_color_mt("app");
log->info("this line is tagged with the 'app' logger name");
```

Named loggers are also what makes per-component level control possible — you can turn on `debug` for
`"db"` while leaving everything else at `info`. See
[Creating loggers](../02-loggers-and-registry/creating-loggers.md) for the full set of factory
helpers.

## Logging to a file in three lines

```cpp showLineNumbers
auto file_log = spdlog::basic_logger_mt("file", "logs/app.log");
file_log->info("this goes to logs/app.log, not stdout");
```

That's the simplest durable sink. For anything long-running, prefer a rotating or daily sink instead
— see [File sinks](../03-sinks/file-sinks.md) for why `basic_logger_mt` alone isn't enough for a
service that runs for weeks.

## Shutting down

Call `spdlog::shutdown()` before your program exits. It drops every registered logger and, if you're
using async logging, joins the background thread pool so queued messages aren't lost. It matters more
than it looks like it should — see [Logger lifecycle](../02-loggers-and-registry/logger-lifecycle.md)
for what goes wrong if you skip it.

## See also

- <Icon icon="lucide:sliders" inline /> [Log levels](./log-levels.md) — runtime and compile-time filtering.
- <Icon icon="lucide:type" inline /> [Basic formatting](./basic-formatting.md) — the `{}` syntax used above.
- <Icon icon="lucide:list-tree" inline /> [Creating loggers](../02-loggers-and-registry/creating-loggers.md) — the full factory-helper reference.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
