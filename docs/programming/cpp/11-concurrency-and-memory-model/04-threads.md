---
id: threads
title: Thread Management
sidebar_label: Threads
sidebar_position: 4
tags: [cpp, concurrency, threads, jthread, stop-token, thread-local]
---

# Thread Management

`std::thread` (C++11, `<thread>`) wraps one OS thread. Creating one starts the function immediately; the
object is a handle that you must either wait for or give up. C++20 adds `std::jthread`, which waits for
itself and supports cooperative cancellation, and is what you should reach for first. This page is the canonical
home for `std::thread` and `std::jthread` lifetimes, argument passing, stop tokens and thread
identity. What threads can safely share is in [Data races](./03-data-races.md).

**Prerequisites:** [C++ memory model](./01-cpp-memory-model.md) (thread start and join are synchronization points),
[Lambdas](../07-classes-and-oop/lambdas.md) (captures).

On Linux with GCC or Clang, link with `-pthread`; MSVC needs no flag.

## Starting a thread and passing arguments

`std::thread t(callable, args...)` starts a new thread running `callable(args...)`. The arguments are
**copied (or moved) into storage owned by the thread** first, then passed as rvalues to the callable. Three
consequences:

- A function taking `int&` does not compile when you pass `n`: the copy is an rvalue and cannot bind to a
  non-const lvalue reference. Wrap it in `std::ref(n)` to opt into sharing, and then make sure `n` outlives
  the thread and the accesses are synchronized.
- Pointers and references captured by a lambda (`[&]`) are shared as is: nothing is copied.
- Member functions need the object: `std::thread t(&Worker::run, &w, 3)`.

```cpp title="start_thread.cpp"
#include <cstdio>
#include <functional>
#include <string>
#include <thread>

void greet(const std::string& name, int& out) {
    out = static_cast<int>(name.size());
}

struct Worker {
    int id = 7;
    void run(int n) { std::printf("worker %d got %d\n", id, n); }
};

int main() {
    int len = 0;
    std::thread t1(greet, std::string("threads"), std::ref(len));   // args copied; ref needs std::ref
    t1.join();
    std::printf("len=%d\n", len);                                   // join orders the write before this read

    Worker w;
    std::thread t2(&Worker::run, &w, 3);                            // member function + object pointer
    t2.join();

    std::thread t3([] { /* runs concurrently */ });
    std::printf("joinable before join: %d\n", t3.joinable());
    t3.join();
    std::printf("joinable after join: %d\n", t3.joinable());
}
```

```text
len=7
worker 7 got 3
joinable before join: 1
joinable after join: 0
```

Output identical with g++ and clang++ at `-O0` and `-O2`, and clean under `-fsanitize=thread`.

## A thread must be joined or detached

A `std::thread` is **joinable** when it owns a running or finished thread of execution. Destroying (or
assigning over) a joinable `std::thread` calls `std::terminate`: the whole process aborts. So every path
out of the scope, including exceptions, must call one of:

- **`join()`** blocks until the thread finishes. It synchronizes-with the thread's completion, so
  everything the thread wrote is visible afterwards. After it returns, `joinable()` is `false`.
- **`detach()`** lets the thread run on its own; you can no longer wait for it or learn its result.
  A detached thread must not touch anything that may be destroyed before it finishes (locals of the
  starting function, `main`'s objects at exit). Use it rarely, and only with data the thread owns
  (e.g. moved in or `shared_ptr`).

```cpp title="forgot_to_join.cpp"
// Dangerous by design: destroying a joinable std::thread calls std::terminate.
#include <thread>
int main() {
    std::thread t([] {});
}   // t still joinable -> std::terminate
```

Running that aborts with `terminate called without an active exception` (libstdc++ on Linux; the text and
exit code are implementation-specific, `SIGABRT` here).

## `std::jthread` (C++20) \{#jthread\}

`std::jthread` is `std::thread` with two additions: the destructor **requests stop and then joins**, so a
scope exit or an exception cannot terminate the program, and it carries a stop request
state for **cooperative cancellation**. If the callable's first parameter is a `std::stop_token`, the
`jthread` passes its token in automatically.

```cpp title="jthread_stop.cpp"
#include <chrono>
#include <cstdio>
#include <stop_token>
#include <thread>

int main() {
    std::jthread worker([](std::stop_token st) {
        int ticks = 0;
        while (!st.stop_requested()) {
            ++ticks;
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        std::printf("stopped, ticked: %s\n", ticks > 0 ? "yes" : "no");
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    worker.request_stop();
    // destructor: request_stop() (already done) then join()
}
```

```text
stopped, ticked: yes
```

The pieces:

| Type | Role |
|---|---|
| `std::stop_source` | Owns the shared state; `request_stop()` sets it (the first call wins). `jthread::get_stop_source()` returns it. |
| `std::stop_token` | Read-only view: `stop_requested()`, `stop_possible()`. Cheap to copy into workers. |
| `std::stop_callback` | RAII registration of a callable that runs when stop is requested. |

Stop is a request, not a kill: the worker must poll the token (or use a `stop_callback`, or a
`condition_variable_any::wait` overload that takes one, see
[Condition variables](./06-condition-variables.md)) and return. A `stop_callback` runs synchronously inside
`request_stop()`, on the calling thread, or immediately in the constructor if stop was already requested:

```cpp title="stop_callback.cpp"
#include <chrono>
#include <cstdio>
#include <stop_token>
#include <thread>

int main() {
    const auto main_id = std::this_thread::get_id();
    std::jthread t([main_id](std::stop_token st) {
        std::stop_callback cb(st, [main_id] {
            // runs synchronously inside request_stop(), on the thread that called it
            std::printf("callback on requesting thread: %s\n",
                        std::this_thread::get_id() == main_id ? "yes" : "no");
        });
        while (!st.stop_requested()) std::this_thread::yield();
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    t.request_stop();
}
```

Prints `callback on requesting thread: yes` (both compilers, `-O0`/`-O2`, TSan clean).

A `jthread` can still be `detach()`ed or `join()`ed manually. It is movable, not copyable, like `std::thread`.

## Moving and storing threads

`std::thread` and `std::jthread` are move-only, so they can live in a `std::vector`, be returned from a
function, and be transferred between owners. A fixed set of workers, each owning one chunk of data and
joined at the end of a block (`jthread`s join when the vector is destroyed):

```cpp title="parallel_sum.cpp"
#include <algorithm>
#include <cstdio>
#include <numeric>
#include <thread>
#include <vector>

int main() {
    std::vector<int> data(1000);
    std::iota(data.begin(), data.end(), 1);

    unsigned n = std::max(1u, std::thread::hardware_concurrency());
    std::vector<long> sums(n, 0);
    {
        std::vector<std::jthread> pool;                  // jthreads join when `pool` is destroyed
        std::size_t chunk = (data.size() + n - 1) / n;
        for (unsigned i = 0; i < n; ++i) {
            pool.emplace_back([&, i] {
                std::size_t b = i * chunk, e = std::min(data.size(), b + chunk);
                for (std::size_t k = b; k < e; ++k) sums[i] += data[k];   // each thread owns sums[i]
            });
        }
    }                                                    // all joined here
    std::printf("%ld\n", std::accumulate(sums.begin(), sums.end(), 0L));
}
```

Prints `500500` regardless of core count. `std::thread::hardware_concurrency()` is only a hint: it may return `0`
when it cannot be determined, hence the `std::max`. Creating a thread per task does not scale; for many small
tasks see [Thread pools](./08-thread-pools.md). For a single result, see [`std::async` and futures](./07-futures-and-promises.md).

## Exceptions do not cross threads

An exception that escapes the thread's function calls `std::terminate`; it is **not** delivered to whoever
started the thread. Catch inside the thread and hand the error back via `std::exception_ptr`
(or use `std::promise`/`std::async`, which do this for you):

```cpp title="exception_ptr.cpp"
#include <cstdio>
#include <exception>
#include <stdexcept>
#include <thread>

int main() {
    std::exception_ptr err;
    std::thread t([&err] {
        try {
            throw std::runtime_error("worker failed");
        } catch (...) {
            err = std::current_exception();   // only this thread writes err
        }
    });
    t.join();                                 // join orders the write before the read below
    if (err) {
        try { std::rethrow_exception(err); }
        catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
    }
}
```

Output: `caught: worker failed`. See [Exceptions](../10-error-handling-and-safety/01-exceptions.md) for `exception_ptr`.

## Thread identity, sleeping, yielding

- `std::this_thread::get_id()` and `t.get_id()` return a `std::thread::id`: comparable, hashable, printable;
  a default-constructed id means "no thread". Its text form is not specified.
- `std::this_thread::sleep_for(duration)` / `sleep_until(time_point)` block the calling thread; they
  take [`<chrono>`](../09-standard-library/chrono.md) types. Sleeping is not synchronization: never use it to
  "wait until the other thread is done".
- `std::this_thread::yield()` hints that the scheduler may run another thread. It is a hint; do not
  build waiting logic on it (use [condition variables](./06-condition-variables.md) or atomics' `wait`).
- Native handles (`native_handle()`) give access to priority and affinity APIs; they are platform-specific and not portable.

## Thread-local storage

`thread_local` gives each thread its own instance of a variable, so there is nothing to synchronize. The
storage-duration rules (when it is constructed and destroyed) are owned by
[Storage duration](../05-memory-and-object-lifetime/storage-duration.md#thread-storage); here is only the effect:

```cpp title="thread_local.cpp"
#include <cstdio>
#include <thread>

thread_local int calls = 0;

int main() {
    ++calls;
    std::thread t([] { ++calls; ++calls; std::printf("thread: %d\n", calls); });
    t.join();
    std::printf("main: %d\n", calls);
}
```

```text
thread: 2
main: 1
```

## Pitfalls

- **Dangling references.** `std::thread t([&]{ use(local); }); t.detach();` outlives `local`. Capture by
  value or move the data in.
- **Passing a pointer to a temporary.** The thread's copy of a `const char*` argument is converted to
  `std::string` *inside the new thread* if the parameter is a `std::string`; if the char array was a local that
  is gone by then, it dangles. Build the `std::string` at the call site.
- **Too many threads.** More runnable threads than cores adds context-switch cost without more throughput
  for CPU-bound work.
- **Use `jthread` unless you need the old semantics.** A manual `join()` is skipped by an early `return` or a
  thrown exception.

## References

- [`std::thread` (cppreference)](https://en.cppreference.com/w/cpp/thread/thread)
- [`std::jthread` (cppreference)](https://en.cppreference.com/w/cpp/thread/jthread)
- [Cooperative cancellation: `std::stop_token` (cppreference)](https://en.cppreference.com/w/cpp/thread/stop_token)
- [Thread support library, \[thread\]](https://eel.is/c++draft/thread)
