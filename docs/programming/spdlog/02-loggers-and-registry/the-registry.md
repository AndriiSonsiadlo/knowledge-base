---
id: the-registry
title: The registry
sidebar_label: The registry
sidebar_position: 2
tags: [c++, spdlog, loggers, registry, global]
---

# The registry

The registry is a global name→logger map. It's what makes `spdlog::get("db")` work from any file in
your program without threading a reference through every function call, and it's also what makes
shutdown order matter — everything registered has to be torn down, and torn down in a sane order,
before the process exits.

## What lives in it

Any logger created through a factory helper (`stdout_color_mt`, `basic_logger_mt`, etc.), plus
anything you explicitly pass to `spdlog::register_logger(...)`. The default logger — the one behind
`spdlog::info(...)` — lives here too, under the name `""`.

## Looking up

```cpp showLineNumbers
auto logger = spdlog::get("db");
if (logger) {
    logger->info("query took {}ms", elapsed_ms);
}
```

:::danger[spdlog::get returns nullptr, it does not throw — check it]
A typo'd or not-yet-created logger name silently returns `nullptr` from `spdlog::get`. Dereferencing
that is a crash, and it's a crash that only shows up once, at the log call site that happens to run
first — always check before use.
:::

## The default logger

`spdlog::default_logger()` returns the logger behind the free functions (`spdlog::info`,
`spdlog::warn`, ...). `spdlog::set_default_logger(...)` replaces it — useful for redirecting every
unqualified log call to a file or a multi-sink logger without touching call sites.

```cpp showLineNumbers
auto file_logger = spdlog::basic_logger_mt("main_file", "logs/app.log");
spdlog::set_default_logger(file_logger);

spdlog::info("this now goes to logs/app.log");   // no call-site changes needed
```

The old default logger is simply replaced — if nothing else holds a `shared_ptr` to it, it's
destroyed once the swap happens.

## Global operations

`spdlog::set_level(...)`, `spdlog::set_pattern(...)`, `spdlog::flush_on(...)`, and
`spdlog::apply_all(fn)` all iterate the registry and apply to every logger in it.

:::note[An unregistered logger is invisible to every global setter]
A logger built with explicit construction and never passed to `register_logger` won't be touched by
`spdlog::set_level`, `spdlog::apply_all`, or any other registry-wide call — you have to configure it
directly.
:::

## Automatic registration

If you're writing library code, `spdlog::set_automatic_registration(false)` stops the factory helpers
from adding new loggers to the registry.

:::tip[Libraries should not register loggers into the host application's registry]
A registered logger from your library can collide by name with one the application creates, and it
shows up in the application's `apply_all` calls whether the application wants it to or not. Disable
automatic registration, or better, let the application pass you a logger instead of creating your
own.
:::

## Dropping

`spdlog::drop(name)` removes one logger from the registry; `spdlog::drop_all()` removes every one.
Neither destroys the logger immediately if something else still holds a `shared_ptr` to it — dropping
only removes the registry's reference. See [Logger lifecycle](./logger-lifecycle.md) for what that
means for shutdown ordering.

## See also

- <Icon icon="lucide:list-tree" inline /> [Creating loggers](./creating-loggers.md) — how loggers end up in the registry in the first place.
- <Icon icon="lucide:timer" inline /> [Logger lifecycle](./logger-lifecycle.md) — ownership and shutdown once a logger is registered.
- <Icon icon="lucide:settings" inline /> [Global settings and best practices](../06-performance-and-configuration/global-settings-and-best-practices.md) — the registry-wide calls in a real setup.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
