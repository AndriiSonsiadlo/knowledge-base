---
id: boost-thread
title: Boost.Thread
sidebar_label: Boost.Thread
sidebar_position: 1
tags: [c++, boost, thread, concurrency, mutex]
---

# Boost.Thread

`Boost.Thread` provides portable threading primitives — threads, mutexes, condition variables, futures,
and shared locks. It is the direct ancestor of `std::thread` and `std::mutex` from C++11, and it still
offers features the standard has not fully absorbed: **thread interruption**, `thread_group`, and
`shared_mutex` that shipped in Boost years before C++17 adopted it.

:::info The problem it solves
Before C++11, the language had no threading model at all. Platform code meant `pthread_create` on POSIX
and `CreateThread` on Windows, with completely different APIs. Boost.Thread gave C++ a single, portable
threading abstraction — and its design became the blueprint for the standard.
:::

## Creating and joining threads

A `boost::thread` takes any callable and runs it in a new OS thread. The destructor calls
`std::terminate` if the thread is still joinable, so you must either `join()` or `detach()`.

```cpp showLineNumbers title="thread_basics.cpp"
#include <boost/thread.hpp>
#include <iostream>

void work(int id) {
    std::cout << "thread " << id << " running\n";
}

int main() {
    boost::thread t1(work, 1);
    boost::thread t2(work, 2);
    t1.join();
    t2.join();
}
```

```bash
g++ -std=c++17 thread_basics.cpp -lboost_thread -lpthread -o demo
```

## Mutexes and locks

Boost provides the same lock types as `std`: `mutex`, `recursive_mutex`, `timed_mutex`, plus
`shared_mutex` for reader-writer scenarios.

```cpp showLineNumbers title="shared_mutex.cpp"
#include <boost/thread/shared_mutex.hpp>
#include <boost/thread.hpp>
#include <string>

boost::shared_mutex rw;
std::string data = "initial";

void reader(int id) {
    boost::shared_lock<boost::shared_mutex> lock(rw);   // multiple readers OK
    std::cout << "reader " << id << ": " << data << "\n";
}

void writer(const std::string& val) {
    boost::unique_lock<boost::shared_mutex> lock(rw);   // exclusive
    data = val;
}
```

:::tip shared_mutex arrived in Boost first
`boost::shared_mutex` has been available since Boost 1.35 (2008). The standard equivalent,
`std::shared_mutex`, did not appear until C++17. On older toolchains, Boost is the only portable
option.
:::

## Thread interruption — a Boost exclusive

`boost::thread` supports cooperative interruption. Calling `t.interrupt()` sets a flag; the target
thread throws `boost::thread_interrupted` at the next **interruption point** (`sleep`, `join`,
`condition_variable::wait`, etc.).

```cpp showLineNumbers title="interruption.cpp"
#include <boost/thread.hpp>
#include <iostream>

void background() {
    try {
        while (true) {
            boost::this_thread::sleep_for(boost::chrono::milliseconds(100));
        }
    } catch (boost::thread_interrupted&) {
        std::cout << "interrupted cleanly\n";
    }
}

int main() {
    boost::thread t(background);
    boost::this_thread::sleep_for(boost::chrono::milliseconds(500));
    t.interrupt();
    t.join();
}
```

:::warning std::thread has no interruption
`std::thread` deliberately omits interruption — the committee considered it too error-prone for a
standard facility. If you need cooperative cancellation with `std::thread`, you must roll your own
with an atomic flag or `std::stop_token` (C++20). Boost.Thread gives it to you out of the box.
:::

## thread_group

`boost::thread_group` manages a collection of threads: create them with `create_thread()`, then
`join_all()` or `interrupt_all()` in one call.

```cpp showLineNumbers
#include <boost/thread.hpp>

void task(int id) { /* ... */ }

int main() {
    boost::thread_group pool;
    for (int i = 0; i < 4; ++i)
        pool.create_thread(boost::bind(task, i));
    pool.join_all();
}
```

## Futures and promises

Boost.Thread includes `boost::future` and `boost::promise`, analogous to their `std` counterparts but
with additional features like `.then()` continuations (available long before any standard equivalent).

```cpp showLineNumbers title="future.cpp"
#include <boost/thread/future.hpp>
#include <iostream>

int compute() { return 42; }

int main() {
    boost::future<int> f = boost::async(boost::launch::async, compute);
    std::cout << f.get() << "\n";
}
```

## Boost.Thread versus std::thread

| Feature | `boost::thread` | `std::thread` |
|---------|-----------------|---------------|
| Header | `<boost/thread.hpp>` | `<thread>` |
| Interruption | yes (cooperative) | no |
| `thread_group` | yes | no |
| `shared_mutex` | since Boost 1.35 | C++17 |
| `.then()` continuations | yes | no (C++23 proposal stalled) |
| Move-only | yes | yes |
| Needs linking | `-lboost_thread` | platform-dependent |

:::note Which to choose
On C++17 and later, prefer `std::thread` and `std::shared_mutex` for standard code. Reach for
Boost.Thread when you need thread interruption, `thread_group`, or must support a pre-C++11 toolchain.
See [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) for the broader lineage.
:::

## See also

- <Icon icon="lucide:atom" inline /> [Boost.Atomic](./boost-atomic.md) — atomic operations for lock-free coordination.
- <Icon icon="lucide:waypoints" inline /> [Boost.Asio](./boost-asio.md) — async I/O as an alternative to manual threading.
- <Icon icon="lucide:lock" inline /> [Boost.Lockfree](./boost-lockfree.md) — lock-free queues and stacks.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::thread` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
