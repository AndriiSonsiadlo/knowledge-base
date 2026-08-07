---
id: custom-formatters
title: Custom formatters
sidebar_label: Custom formatters
sidebar_position: 2
tags: [c++, spdlog, formatting, custom-flag]
---

# Custom formatters

When no built-in pattern flag carries the field you need — a request id, a thread name, a tenant —
the supported move is adding your own pattern flag, not stuffing that field into every individual log
message by hand.

## custom_flag_formatter

```cpp showLineNumbers title="thread_name_flag.hpp"
class thread_name_flag : public spdlog::custom_flag_formatter {
public:
    void format(const spdlog::details::log_msg&, const std::tm&,
                spdlog::memory_buf_t& dest) override {
        std::string name = current_thread_name();   // your own lookup
        dest.append(name.data(), name.data() + name.size());
    }

    std::unique_ptr<custom_flag_formatter> clone() const override {
        return spdlog::details::make_unique<thread_name_flag>(*this);
    }
};
```

## Wiring it up

```cpp showLineNumbers
auto f = std::make_unique<spdlog::pattern_formatter>();
f->add_flag<thread_name_flag>('*').set_pattern("[%*] %v");
spdlog::set_formatter(std::move(f));
```

`'*'` is the flag character you're choosing to bind — pick one that isn't already a built-in flag (see
[Pattern flags](./pattern-flags.md) for the reserved set).

## clone() is not optional

:::danger[Each sink clones the formatter; a clone() that drops state produces silently wrong output]
spdlog clones the formatter once per sink so each sink can format independently. If `clone()` doesn't
copy every piece of state your flag depends on, sinks beyond the first silently format with
default-initialized (often empty or wrong) state — no crash, no warning, just quietly incorrect
output in the second and later sinks.
:::

## Replacing the whole formatter

For a wire format that isn't line-oriented at all — say, a fixed binary layout for a metrics
collector — implement `spdlog::formatter` directly instead of composing pattern flags. That's more
work than `custom_flag_formatter`, but it's the right tool when the pattern-flag model (a sequence of
fields in a text line) doesn't match what you're producing.

## Where formatters live

A formatter can be set per logger or per sink, following the same override rules as patterns — see
[Multi-sink loggers](../02-loggers-and-registry/multi-sink-loggers.md). Whichever level you set it at,
remember it gets cloned once per sink; see [Sink overview](../03-sinks/sink-overview.md) for how a
sink actually consumes its formatter.

## See also

- <Icon icon="lucide:type" inline /> [Pattern flags](./pattern-flags.md) — the built-in flags this extends.
- <Icon icon="lucide:wrench" inline /> [Custom sinks](../03-sinks/custom-sinks.md) — the sibling extension point for destinations rather than formatting.
- <Icon icon="lucide:map-pin" inline /> [Source location and structured logging](./source-location-and-structured-logging.md) — a concrete use case for a custom flag.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
