---
id: logger-lifecycle
title: Logger lifecycle
sidebar_label: Lifecycle
sidebar_position: 3
tags: [c++, spdlog, loggers, lifetime, shutdown]
---

# Logger lifecycle

Loggers are `shared_ptr`-owned. The registry holds one reference, you typically hold another (or
several), and if you're using async logging, the thread pool needs to stay alive as long as anything
might still log through it. Getting shutdown order wrong is the most common way spdlog "loses" the
last few log lines before a crash.

## Shared ownership

```cpp showLineNumbers
class Server {
    std::shared_ptr<spdlog::logger> log_ = spdlog::get("server");
public:
    void handle_request() {
        log_->info("handling request");   // no lookup on every call
    }
};
```

:::tip[spdlog::get takes a lock — cache the shared_ptr]
`spdlog::get` walks the registry under a lock every time it's called. Look a logger up once —
typically at construction — and keep the `shared_ptr`, rather than calling `spdlog::get` on every log
statement in a hot path.
:::

## Sink sharing

Several loggers can share one sink instance — that's how two independent components can both write
to the same file without interleaving corrupted output, because the sink (not the logger) owns the
mutex that serializes writes. See [Multi-sink loggers](./multi-sink-loggers.md) for the construction
pattern.

## Shutdown

`spdlog::shutdown()` drops every registered logger (equivalent to `drop_all()`) and, if async logging
is in use, joins the background thread pool so it doesn't outlive the loggers using it.

:::danger[Logging after shutdown, or from a static destructor, is undefined]
Once `spdlog::shutdown()` has run, logging through a dangling reference to a dropped logger — or from
a static object's destructor that races with spdlog's own static teardown — is undefined behavior.
Call `spdlog::shutdown()` as close to the end of `main()` as you can, after every other subsystem that
might still log has already stopped.
:::

## Static initialization order

The classic trap: a file-scope `static auto logger = spdlog::stdout_color_mt("lib");` in a library.
Static initialization order across translation units is unspecified, so this can run before or after
spdlog's own internal statics are ready, depending on link order and luck.

The fix is either a function-local static (guaranteed to initialize on first use, not at program
start):

```cpp showLineNumbers
spdlog::logger& lib_logger() {
    static auto logger = spdlog::stdout_color_mt("lib");
    return *logger;
}
```

or an explicit `init()` call the application invokes at a known point in startup.

## Lifetime with async loggers

An async logger's thread pool must be alive whenever the logger might flush — which means the pool
has to outlive every async logger that uses it. `spdlog::shutdown()` handles the ordering for you if
you let it own the teardown; see
[Thread pool and async logger](../05-async-logging/thread-pool-and-async-logger.md) for what happens
if you tear the pool down manually and get the order wrong.

## See also

- <Icon icon="lucide:list-tree" inline /> [The registry](./the-registry.md) — where the shared ownership starts.
- <Icon icon="lucide:list-tree" inline /> [Creating loggers](./creating-loggers.md) — factory vs explicit construction.
- <Icon icon="lucide:waypoints" inline /> [Thread pool and async logger](../05-async-logging/thread-pool-and-async-logger.md) — the extra lifetime constraint async adds.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
