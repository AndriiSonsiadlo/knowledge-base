---
id: console-sinks
title: Console sinks
sidebar_label: Console sinks
sidebar_position: 2
tags: [c++, spdlog, sinks, console, color]
---

# Console sinks

Console output is the default destination because it's the one that always exists — no file
permissions to worry about, no disk to fill. The interesting decisions here are which stream you
write to and whether you color the output.

## stdout vs stderr

`stdout_color_sink_mt`/`_st` and `stderr_color_sink_mt`/`_st` write colored output to stdout or
stderr respectively; `stdout_sink_mt`/`_st` and `stderr_sink_mt`/`_st` are the plain, uncolored
equivalents.

:::tip[Log errors to stderr so pipelines can separate them]
If your process's stdout is piped somewhere meaningful (another program, a file), routing `warn`+ to
a stderr sink keeps operational noise out of that pipe while still surfacing problems on the
terminal.
:::

## Color

Color is applied per level using a default mapping (red for errors, yellow for warnings, and so on),
which you can override:

```cpp
sink->set_color(spdlog::level::info, sink->green);
```

Only the part of the pattern between `%^` and `%$` is colored — everything outside that range prints
in the terminal's default color:

```cpp
sink->set_pattern("[%H:%M:%S] %^[%l]%$ %v");   // only "[info]" (etc.) is colored
```

See [Pattern flags](../04-formatting-and-patterns/pattern-flags.md) for the rest of the pattern
syntax.

## Color and redirection

:::danger[ANSI codes end up in your log file when stdout is redirected]
`./myapp > out.log` still sends spdlog raw ANSI escape codes if you used a color sink — spdlog does
not detect the redirection for you. Use a non-color sink (`stdout_sink_mt`) whenever the destination
might not be an interactive terminal, or detect TTY-ness yourself and pick the sink accordingly.
:::

## Windows

Windows console color historically didn't support ANSI escapes the way Unix terminals do, so spdlog
provides `wincolor_stdout_sink_mt` using the Windows console API directly instead of writing escape
codes. Watch for the UTF-8 code page caveat — non-ASCII output can come out mangled unless the console
is switched to UTF-8 (`chcp 65001`) or you use the Windows-native sink's built-in handling.

## Throughput

Console I/O is slow and serialized by the OS terminal driver — orders of magnitude slower than
writing to a file, let alone an in-memory buffer.

:::note[If console logging is in your hot path, move it to a file or async]
A tight loop logging to console at `info` level will bottleneck on terminal I/O long before it
bottlenecks on formatting. See
[Async vs sync trade-offs](../05-async-logging/async-vs-sync-tradeoffs.md) for when moving console
output off the caller's thread is worth the complexity.
:::

## See also

- <Icon icon="lucide:layers" inline /> [Sink overview](./sink-overview.md) — the shared sink interface.
- <Icon icon="lucide:file-text" inline /> [File sinks](./file-sinks.md) — the durable alternative.
- <Icon icon="lucide:type" inline /> [Pattern flags](../04-formatting-and-patterns/pattern-flags.md) — controlling the colored range and layout.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
