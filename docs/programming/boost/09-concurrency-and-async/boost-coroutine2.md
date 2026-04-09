---
id: boost-coroutine2
title: Boost.Coroutine2
sidebar_label: Boost.Coroutine2
sidebar_position: 6
tags: [c++, boost, coroutine, generator, pull-push]
---

# Boost.Coroutine2

`Boost.Coroutine2` provides **stackful coroutines** — functions that can suspend and resume while
preserving their full call stack. Unlike C++20 coroutines (which are stackless and require compiler
support), Boost coroutines carry their own stack and can yield from any depth in the call chain. The
library offers two types: `pull_type` (the caller pulls values from the coroutine) and `push_type`
(the caller pushes values into the coroutine).

:::info The problem it solves
Generators, cooperative state machines, and pipeline stages all need a function that can *pause*,
return a value, and later *resume* from where it left off. Without coroutines you are forced into
callback spaghetti, explicit state machines, or threads — all of which are harder to read and maintain.
:::

## Pull-type coroutines (generators)

A `pull_type` coroutine produces values. The coroutine body calls `sink(value)` to yield, and the
caller iterates using `source()` and `source.get()`.

```cpp showLineNumbers title="generator.cpp"
#include <boost/coroutine2/all.hpp>
#include <iostream>

using coro_t = boost::coroutines2::coroutine<int>;

void fibonacci(coro_t::push_type& sink) {
    int a = 0, b = 1;
    while (true) {
        sink(a);          // yield a value
        int next = a + b;
        a = b;
        b = next;
    }
}

int main() {
    coro_t::pull_type source(fibonacci);
    for (int i = 0; i < 10; ++i) {
        std::cout << source.get() << " ";
        source();         // resume the coroutine
    }
    std::cout << "\n";
    // output: 0 1 1 2 3 5 8 13 21 34
}
```

## Push-type coroutines (sinks)

A `push_type` coroutine consumes values. The caller pushes data in, and the coroutine processes each
value as it arrives.

```cpp showLineNumbers title="sink.cpp"
#include <boost/coroutine2/all.hpp>
#include <iostream>

using coro_t = boost::coroutines2::coroutine<int>;

void printer(coro_t::pull_type& source) {
    while (source) {
        std::cout << "received: " << source.get() << "\n";
        source();         // wait for next value
    }
}

int main() {
    coro_t::push_type sink(printer);
    sink(10);
    sink(20);
    sink(30);
    // coroutine destroyed when sink goes out of scope
}
```

## Range-based for with coroutines

`pull_type` models an input range, so you can iterate it directly with a range-for loop:

```cpp showLineNumbers title="range_for.cpp"
#include <boost/coroutine2/all.hpp>
#include <iostream>

using coro_t = boost::coroutines2::coroutine<int>;

void squares(coro_t::push_type& sink) {
    for (int i = 1; i <= 5; ++i)
        sink(i * i);
}

int main() {
    for (int v : coro_t::pull_type(squares))
        std::cout << v << " ";
    // output: 1 4 9 16 25
}
```

## Pipeline composition

Coroutines compose naturally into processing pipelines — each stage is a coroutine that pulls from
a source and pushes to a sink:

```mermaid
flowchart LR
    G[Generator] -- pull --> F[Filter] -- pull --> C[Consumer]
```

```cpp showLineNumbers title="pipeline.cpp"
#include <boost/coroutine2/all.hpp>
#include <iostream>

using coro_t = boost::coroutines2::coroutine<int>;

void range(coro_t::push_type& sink, int from, int to) {
    for (int i = from; i <= to; ++i)
        sink(i);
}

void evens_only(coro_t::push_type& sink, coro_t::pull_type& source) {
    for (auto& v : source)
        if (v % 2 == 0)
            sink(v);
}

int main() {
    coro_t::pull_type src([](coro_t::push_type& s) { range(s, 1, 10); });
    coro_t::pull_type filtered([&](coro_t::push_type& s) { evens_only(s, src); });

    for (int v : filtered)
        std::cout << v << " ";
    // output: 2 4 6 8 10
}
```

## Stackful versus stackless coroutines

| Aspect | Boost.Coroutine2 (stackful) | C++20 coroutines (stackless) |
|--------|----------------------------|-----------------------------|
| Stack | owns a full stack (~64KB default) | compiler-generated frame |
| Yield from nested calls | yes — any depth | no — only at `co_await`/`co_yield` |
| Compiler support | none required (library-only) | requires C++20 compiler |
| Overhead per coroutine | stack allocation + context switch | frame allocation only |
| Standard | no | yes |

:::note When to use which
Stackful coroutines (Boost.Coroutine2) are simpler when you need to yield from deep call chains.
Stackless coroutines (C++20) are more efficient when you can restructure code to yield only at
explicit suspension points. For new code on C++20 compilers, prefer the standard coroutines; use
Boost.Coroutine2 on older toolchains or when deep-yield is essential.
:::

:::warning Boost.Coroutine (v1) is deprecated
The original `Boost.Coroutine` (without the "2") is deprecated. Always use `Boost.Coroutine2`.
:::

## See also

- <Icon icon="lucide:layers" inline /> [Boost.Fiber](./boost-fiber.md) — fibers build on coroutines to add scheduling and sync primitives.
- <Icon icon="lucide:waypoints" inline /> [Boost.Asio](./boost-asio.md) — integrates with coroutines for async I/O.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
