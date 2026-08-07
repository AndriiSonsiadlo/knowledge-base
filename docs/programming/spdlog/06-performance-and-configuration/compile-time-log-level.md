---
id: compile-time-log-level
title: Compile-time log level
sidebar_label: Compile-time level
sidebar_position: 1
tags: [c++, spdlog, performance, macros, build]
---

# Compile-time log level

A runtime level check is cheap, but it isn't free — it's still a branch and, on the disabled path,
arguments that were already evaluated before the check ran. A compile-time level goes further: it
deletes the call site entirely, arguments included, so a disabled debug log costs nothing in the
compiled binary.

## SPDLOG_ACTIVE_LEVEL

`SPDLOG_ACTIVE_LEVEL`, set to one of the `SPDLOG_LEVEL_*` constants (`SPDLOG_LEVEL_TRACE` through
`SPDLOG_LEVEL_OFF`), controls which `SPDLOG_*` macros compile to real code. It has no effect on
`spdlog::info(...)` and friends — only the macro forms respect it.

:::danger[Setting SPDLOG_ACTIVE_LEVEL does nothing if you call spdlog::info() instead of SPDLOG_INFO()]
`spdlog::debug("x")` always compiles to a real call regardless of `SPDLOG_ACTIVE_LEVEL` — only the
runtime level (`set_level`) filters it. If you want the compile-time deletion, the call site has to
use the macro form, `SPDLOG_DEBUG("x")`.
:::

## Setting it in the build

```cmake showLineNumbers title="CMakeLists.txt"
target_compile_definitions(app PRIVATE SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_INFO)

# Per-configuration variant using a generator expression
target_compile_definitions(app PRIVATE
    $<$<CONFIG:Debug>:SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_TRACE>
    $<$<CONFIG:Release>:SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_INFO>
)
```

See [Generator expressions](../../cmake/05-advanced/generator-expressions.md) for the general
`$<CONFIG:...>` mechanism used above.

## What "deleted" means

Below the active level, `SPDLOG_TRACE(...)`/`SPDLOG_DEBUG(...)` expand to nothing — not a no-op call,
literally no tokens. Argument expressions are never evaluated:

```cpp showLineNumbers
// with SPDLOG_ACTIVE_LEVEL == SPDLOG_LEVEL_INFO:
SPDLOG_DEBUG("state: {}", expensive_dump(state));   // expensive_dump() is never called —
                                                      // the whole statement compiles to nothing
```

## ODR hazard

:::danger[Different translation units compiled with different SPDLOG_ACTIVE_LEVEL values violate the ODR]
`SPDLOG_ACTIVE_LEVEL` affects macro expansion at each call site, not a single global symbol — but
inline functions and templates that reference logging macros can still end up with different bodies
in different translation units if the define isn't consistent project-wide, which is undefined
behavior under the One Definition Rule. Set it once, in one place (a top-level `target_compile_definitions`
or a shared config header), not per-file.
:::

## Runtime vs compile-time

| | Runtime `set_level` | `SPDLOG_ACTIVE_LEVEL` |
|---|---|---|
| Cost when disabled | One comparison, arguments may still evaluate | Zero — code doesn't exist |
| Changeable without rebuild | Yes | No |
| Argument evaluation when disabled | Yes, unless guarded | Never |
| Scope | Per logger/sink, at runtime | Whole binary, at compile time |

## Recommended setup

:::tip[Debug builds at SPDLOG_LEVEL_TRACE, release at SPDLOG_LEVEL_INFO, then use runtime levels for everything finer]
Compile-time filtering sets the ceiling — the finest level that can possibly appear in a build.
Runtime `set_level` calls narrow from there per logger, per environment, without needing a rebuild.
Combine both rather than choosing one.
:::

## See also

- <Icon icon="lucide:settings" inline /> [Global settings and best practices](./global-settings-and-best-practices.md) — where this fits into a production setup.
- <Icon icon="lucide:sliders" inline /> [Log levels](../01-basics/log-levels.md) — the runtime half of level filtering.
- <Icon icon="lucide:map-pin" inline /> [Source location and structured logging](../04-formatting-and-patterns/source-location-and-structured-logging.md) — the `SPDLOG_*` macros this page's deletion applies to.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
