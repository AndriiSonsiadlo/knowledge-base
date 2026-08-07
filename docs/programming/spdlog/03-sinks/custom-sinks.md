---
id: custom-sinks
title: Custom sinks
sidebar_label: Custom sinks
sidebar_position: 6
tags: [c++, spdlog, sinks, custom, thread-safety]
---

# Custom sinks

A custom sink is the supported way to send logs anywhere spdlog doesn't already reach — an in-memory
ring for a diagnostics endpoint, a socket to a log collector, or a vector-backed sink for asserting on
output in a unit test.

## base_sink&lt;Mutex&gt;

Derive from `spdlog::sinks::base_sink<Mutex>` and implement two protected virtuals:
`sink_it_(const details::log_msg&)` and `flush_()`. `base_sink` handles locking and formatting
plumbing for you.

```cpp showLineNumbers title="ring_sink.hpp"
template <typename Mutex>
class ring_sink : public spdlog::sinks::base_sink<Mutex> {
public:
    explicit ring_sink(size_t capacity) : capacity_(capacity) {}

    std::vector<std::string> last_n() const { return {ring_.begin(), ring_.end()}; }

protected:
    void sink_it_(const spdlog::details::log_msg& msg) override {
        spdlog::memory_buf_t formatted;
        this->formatter_->format(msg, formatted);
        ring_.push_back(fmt::to_string(formatted));
        if (ring_.size() > capacity_) ring_.pop_front();
    }

    void flush_() override {}   // nothing buffered beyond the ring itself

private:
    size_t capacity_;
    std::deque<std::string> ring_;
};

using ring_sink_mt = ring_sink<std::mutex>;
using ring_sink_st = ring_sink<spdlog::details::null_mutex>;
```

## Why base_sink and not sink

`spdlog::sinks::sink` is the raw interface; `base_sink<Mutex>` is a small template that locks a mutex
around `sink_it_`/`flush_` and gives you `this->formatter_` already wired up.

:::danger[Deriving from sink directly means you own all thread-safety yourself]
Skipping `base_sink` and implementing `sink::log`/`sink::flush` directly means no locking happens on
your behalf — every concurrent call from multiple threads is your responsibility to serialize
correctly. There's rarely a reason to do this instead of `base_sink<Mutex>`.
:::

## Formatting inside a sink

`this->formatter_->format(msg, buffer)` renders the message into a `spdlog::memory_buf_t`; from there
you write `buffer.data()`/`buffer.size()` to wherever your sink sends data.

:::danger[Storing msg.payload without copying dangles]
`log_msg::payload` is a `string_view` into a buffer owned by the caller — it does not outlive the
`sink_it_` call. If you need the message later, copy it (as the ring sink above does with
`fmt::to_string`), never just store the `string_view`.
:::

## The mutex parameter

| Mutex type | Use |
|---|---|
| `std::mutex` | The `_mt` variant — safe from multiple threads |
| `spdlog::details::null_mutex` | The `_st` variant — no locking, single-threaded use only |

## Testing with a custom sink

:::tip[A vector-backed sink is the cleanest way to assert on log output in unit tests]
Instead of capturing stdout or parsing a file, attach a small custom sink that appends formatted
messages to a `std::vector<std::string>` and assert directly against its contents. No process
capture, no file cleanup between tests.
:::

## Registering it

Pass the sink to a logger exactly like a built-in one:

```cpp
auto sink = std::make_shared<ring_sink_mt>(200);
auto logger = std::make_shared<spdlog::logger>("diag", sink);
```

If you want a matching one-line factory helper (`ring_logger_mt("name", 200)`), write a small wrapper
following the same pattern as spdlog's own `basic_logger_mt` — construct the sink, construct the
logger, register it.

## See also

- <Icon icon="lucide:layers" inline /> [Sink overview](./sink-overview.md) — the interface this extends.
- <Icon icon="lucide:list-tree" inline /> [Multi-sink loggers](../02-loggers-and-registry/multi-sink-loggers.md) — combining a custom sink with built-in ones.
- <Icon icon="lucide:type" inline /> [Custom formatters](../04-formatting-and-patterns/custom-formatters.md) — the other supported extension point.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
