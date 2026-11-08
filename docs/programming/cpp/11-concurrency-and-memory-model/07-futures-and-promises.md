---
id: futures-and-promises
title: Futures and Promises
sidebar_label: Futures & Promises
sidebar_position: 7
tags: [cpp, concurrency, future, promise, async, packaged-task, shared-future]
---

# Futures and Promises

A **future** is a handle to a value that will exist later, possibly produced by another thread. It
replaces "start a thread, join, read a shared variable" with a single object that carries the result
(or the exception) and does the synchronization for you. This page is the canonical home for
`std::future`, `std::promise`, `std::packaged_task`, `std::shared_future` and `std::async` (header `<future>`).

**Prerequisites:** [Threads](./04-threads.md), [Data races](./03-data-races.md).

## One channel, two ends

Producer and consumer share a **shared state**. The producing end writes it once: a `std::promise`
(you set it), a `std::packaged_task` (it runs a function and sets it), or `std::async` (it starts the function
for you). The consuming end is a `std::future`, whose `get()` waits until the state is ready and then returns
the value or rethrows the stored exception. Setting the value synchronizes-with the `get()` that returns it, so
the consumer sees everything the producer wrote before setting it; no extra lock is needed.

<Diagram title="Shared state between producer and consumer" caption="The value is written once and read once through a future." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Producer side">
      <DiagramNode title="std::promise / packaged_task / async">set_value, set_exception, or return/throw</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="writes once" />
    <DiagramGroup label="Shared state">
      <DiagramNode title="value or exception" accent>ready flag</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="get() waits, returns" />
    <DiagramGroup label="Consumer side">
      <DiagramNode title="std::future&lt;T&gt;">single use, movable</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

`future::get()` can be called **once**; after that `valid()` is `false` and calling `get()` again is undefined behaviour (implementations are encouraged to throw `std::future_error`). A `future` is
move-only. `wait()` blocks without consuming; `wait_for` / `wait_until` return a `std::future_status`
(`ready`, `timeout`, or `deferred`).

## `std::async`

`std::async(policy, f, args...)` runs `f(args...)` and returns a `std::future` for its result. Arguments are copied like
for [`std::thread`](./04-threads.md#starting-a-thread-and-passing-arguments), so use `std::ref`/`std::cref` to share.

```cpp title="async_sum.cpp"
#include <cstdio>
#include <future>
#include <numeric>
#include <vector>

long sum(const std::vector<int>& v, std::size_t b, std::size_t e) {
    return std::accumulate(v.begin() + b, v.begin() + e, 0L);
}

int main() {
    std::vector<int> v(1000);
    std::iota(v.begin(), v.end(), 1);
    auto lo = std::async(std::launch::async, sum, std::cref(v), 0, 500);
    auto hi = std::async(std::launch::async, sum, std::cref(v), 500, 1000);
    std::printf("%ld\n", lo.get() + hi.get());       // get() waits and returns the value (once)
}
```

Prints `500500` (both compilers, `-O0`/`-O2`, TSan clean).

### Launch policies

| Policy | Meaning |
|---|---|
| `std::launch::async` | Run on a new thread of execution, immediately. |
| `std::launch::deferred` | Run lazily, in the thread that calls `get()` or `wait()`. No new thread. |
| default (`async \| deferred`) | The implementation chooses. Do not rely on either behaviour. |

Because the default may defer, a `wait_for` on such a future can return `future_status::deferred` forever without
the task running. Specify `std::launch::async` when you need concurrency. A deferred task that nobody
waits on never runs.

### A future from `async` blocks in its destructor \{#async-destructor\}

The destructor of the last future referring to a shared state **created by `std::async` with `std::launch::async`** blocks until the task finishes (a deferred task never runs, so there is nothing to wait for).
Futures from `promise` or `packaged_task` do not. The consequence is that a discarded `async` result is silently
synchronous:

```cpp title="async_dtor.cpp"
#include <chrono>
#include <cstdio>
#include <future>
#include <thread>

int main() {
    using namespace std::chrono;
    auto t0 = steady_clock::now();
    {
        auto f = std::async(std::launch::async, [] { std::this_thread::sleep_for(milliseconds(200)); });
    }                                           // ~future blocks here until the task finishes
    auto ms = duration_cast<milliseconds>(steady_clock::now() - t0).count();
    std::printf("blocked at least 150 ms: %d\n", ms >= 150);
}
```

Prints `blocked at least 150 ms: 1`. The standard library declares `std::async` `[[nodiscard]]` since C++20 (P0600R1, `[[nodiscard]]` in the library), and both compilers warn on a bare
`std::async(...);` statement for this reason. If you want fire-and-forget, use a
thread you manage ([Threads](./04-threads.md)), not `async`.

## `std::promise`: setting the value yourself

A `std::promise<T>` is the writing end. Obtain its future once with `get_future()`, hand the promise to the producer, and
call exactly one of `set_value`, `set_exception` (a second call throws `std::future_error`). If the promise is destroyed
without either, the future's `get()` throws `std::future_error` with code `broken_promise`, so a waiting consumer
is not stuck forever.

```cpp title="promise_future.cpp"
#include <cstdio>
#include <future>
#include <stdexcept>
#include <string>
#include <thread>

int main() {
    std::promise<std::string> p;
    std::future<std::string> f = p.get_future();
    std::thread t([&p] { p.set_value("result"); });
    std::printf("%s\n", f.get().c_str());
    t.join();

    std::promise<int> p2;
    auto f2 = p2.get_future();
    std::thread t2([&p2] {
        try { throw std::runtime_error("boom"); }
        catch (...) { p2.set_exception(std::current_exception()); }
    });
    try { f2.get(); }
    catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
    t2.join();

    std::future<int> f3;
    {
        std::promise<int> p3;
        f3 = p3.get_future();
    }                                           // promise destroyed without a value
    try { f3.get(); }
    catch (const std::future_error& e) {
        std::printf("broken promise: %d\n", e.code() == std::future_errc::broken_promise);
    }
}
```

```text
result
caught: boom
broken promise: 1
```

This is the answer to "exceptions do not cross threads" from [Threads](./04-threads.md#exceptions-do-not-cross-threads):
the exception is stored and rethrown by `get()` in the consumer. `std::async` and `packaged_task` do
the catch-and-store for you, so a throwing task surfaces at `get()`.

## `std::packaged_task`: a callable bound to a future

A `std::packaged_task<R(Args...)>` wraps any callable. Invoking it runs the callable and fulfils its future with the
result or exception. It is the piece that lets you decide *where* the call runs: on a thread, in a pool, or
later. It is move-only.

```cpp title="packaged_task.cpp"
#include <cstdio>
#include <future>
#include <thread>

int main() {
    std::packaged_task<int(int, int)> task([](int a, int b) { return a * b; });
    std::future<int> f = task.get_future();
    std::thread t(std::move(task), 6, 7);       // run it wherever you like
    std::printf("%d\n", f.get());               // 42
    t.join();
}
```

A thread pool is mostly a queue of such tasks; see [Thread pools](./08-thread-pools.md).

## `std::shared_future`: many consumers

A plain `future` has one consumer. Call `.share()` (or construct from a future) to get a `std::shared_future<T>`,
which is copyable, and whose `get()` may be called many times and from many threads, returning a `const T&`.
Give each thread **its own copy** of the `shared_future`: concurrent `get()` on copies is safe, but calling non-const
operations on one shared object from several threads is a data race.

```cpp title="shared_future.cpp"
#include <cstdio>
#include <future>
#include <thread>
#include <vector>

int main() {
    std::promise<int> p;
    std::shared_future<int> sf = p.get_future().share();
    std::vector<std::jthread> readers;
    for (int i = 0; i < 3; ++i)
        readers.emplace_back([sf] { (void)sf.get(); });   // each thread has its OWN copy of sf
    p.set_value(5);
    readers.clear();
    std::printf("%d valid: %d\n", sf.get(), sf.valid());   // 5 valid: 1
}
```

## Waiting with a timeout

```cpp title="wait_for.cpp"
#include <chrono>
#include <cstdio>
#include <future>
#include <thread>

int main() {
    std::promise<int> p;
    auto f = p.get_future();
    auto st = f.wait_for(std::chrono::milliseconds(20));
    std::printf("timeout: %d\n", st == std::future_status::timeout);
    p.set_value(1);
    std::printf("ready: %d\n", f.wait_for(std::chrono::seconds(1)) == std::future_status::ready);

    auto d = std::async(std::launch::deferred, [] { return 3; });
    std::printf("deferred status: %d\n", d.wait_for(std::chrono::seconds(0)) == std::future_status::deferred);
    std::printf("%d\n", d.get());               // runs the task here, in this thread
}
```

Output: `timeout: 1`, `ready: 1`, `deferred status: 1`, `3`. Timed waits can return later than requested
(scheduling); never use them as a precise timer.

## async vs thread vs packaged_task

| Need | Use |
|---|---|
| One result (or exception) from a background computation | `std::async(std::launch::async, ...)` |
| The result of work you schedule yourself (a pool, a specific thread) | `std::packaged_task` + your executor |
| Hand a value from one place in the code to another, set from a callback or an event | `std::promise` |
| A long-lived worker, no single result | [`std::jthread`](./04-threads.md#jthread) |
| Many results over time | A [blocking queue](./06-condition-variables.md#blocking-queue), or (C++20) a coroutine generator, see [Coroutines](./09-coroutines.md) |

## Limits of std::future

The standard future has no `then()` continuation, no cancellation, no combinators such as "when any of these is ready", and
`async` has no scheduler or pool you control (the standard has no thread pool; see [Thread pools](./08-thread-pools.md)).
The Concurrency TS added `then`/`when_all` in `std::experimental`, but it was not adopted into the standard;
the standardization direction is `std::execution` (senders/receivers), in the C++26 draft. Check that your standard library ships it before relying on it.

## Pitfalls

- **Calling `get()` twice** on a `std::future` (it is single-use; use `shared_future`).
- **Ignoring the returned future** from `async`: it blocks right there, and loses exceptions.
- **A default-policy `async` that is secretly deferred**, so `wait_for` never completes. Name the policy.
- **Forgetting a `promise` must be fulfilled** on every path, including error paths; otherwise the consumer gets `broken_promise`.
- **Dangling captures** into an `async` task are no different from a thread: the referenced objects must outlive the call.

## References

- [`std::future` (cppreference)](https://en.cppreference.com/w/cpp/thread/future)
- [`std::async` (cppreference)](https://en.cppreference.com/w/cpp/thread/async)
- [`std::promise` (cppreference)](https://en.cppreference.com/w/cpp/thread/promise)
- [`std::packaged_task` (cppreference)](https://en.cppreference.com/w/cpp/thread/packaged_task)
- [Futures, \[futures\]](https://eel.is/c++draft/futures)
