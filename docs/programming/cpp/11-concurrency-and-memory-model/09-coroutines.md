---
id: coroutines
title: Coroutines (C++20)
sidebar_label: Coroutines
sidebar_position: 9
tags: [cpp, coroutines, cpp20, cpp23, generator, co-await, promise-type, awaiter]
---

# Coroutines (C++20)

A **coroutine** is a function that can **suspend** in the middle, return control to its caller, and
later be **resumed** where it left off with its local variables intact. Ordinary functions run to
completion on the caller's stack; a coroutine's state lives in a separate object, so it can outlive any
single call. That makes two things easy: **lazy sequences** (generators) and **asynchronous code that
reads like synchronous code**. Coroutines are not threads: nothing runs in parallel unless you resume them
from different threads yourself.

**Prerequisites:** [Threads](./04-threads.md) (for the last section),
[Object lifetime](../05-memory-and-object-lifetime/object-lifetime.md). Compile with `-std=c++20`
(`-std=c++23` for `std::generator`); GCC 11 or later needs no extra flag (GCC 10 needed `-fcoroutines`).

:::warning[C++20 gives the mechanism, not the types]
C++20 standardised the language support (`co_await`, `co_yield`, `co_return`, `std::coroutine_handle`, the
`promise_type` protocol) and a few trivial awaitables, but **no generator or task type**. The first
standard coroutine type, `std::generator`, arrived in **C++23**. Anything asynchronous (a `task<T>`, schedulers) comes
from a library (cppcoro, Asio, libunifex, ...) or from code you write. Library support for each needs checking against your compiler.
:::

## What makes a function a coroutine

A function is a coroutine if its body contains any of:

| Keyword | Effect |
|---|---|
| `co_await expr` | Suspend until the awaited operation is ready, then continue with its result. |
| `co_yield value` | Hand `value` to the caller and suspend (equivalent to `co_await promise.yield_value(value)`). |
| `co_return [value]` | Finish the coroutine, optionally with a result. |

The return type decides which library protocol applies, through a nested `promise_type`. A coroutine cannot use
plain `return`, C-style varargs (`...`) or a placeholder return type (`auto`), and it cannot be `constexpr`/`consteval`, `main`,
or a constructor or destructor.

## The coroutine frame

When a coroutine is called, the compiler creates a **coroutine frame** that holds the parameters (copied or
moved in), the locals that live across a suspension, the promise object, and the resume point. Coroutines are
**stackless**: only the coroutine itself can suspend, not functions it calls, and suspension does not keep any of
the caller's stack. The frame is normally allocated with `operator new` (the promise type can supply its own
`operator new`), and the compiler is allowed to elide that allocation when the coroutine's lifetime is
nested inside the caller's. Whether it does so is implementation-specific.

<Diagram title="One coroutine call" caption="The caller holds a return object; the return object owns a handle to the frame, which holds the promise and the saved locals." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Caller">
      <DiagramNode title="return object">e.g. Generator&lt;int&gt;</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="coroutine_handle" />
    <DiagramGroup label="Coroutine frame">
      <DiagramNode title="promise_type" accent>current value, exception</DiagramNode>
      <DiagramNode title="copied parameters">live across suspensions</DiagramNode>
      <DiagramNode title="locals and resume point">saved at each suspend</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

At each `co_await` (including the implicit ones at the start and end), the compiler asks the awaiter three things:

1. `await_ready()`: already done? If `true`, don't suspend.
2. `await_suspend(handle)`: called with the coroutine already considered suspended. It may return `void` (stay suspended), a
   `bool` (`false` means resume immediately), or another `coroutine_handle` (resume that one: **symmetric transfer**,
   which avoids unbounded stack growth in chains of coroutines).
3. `await_resume()`: runs on resumption; its result is the value of the `co_await` expression.

`std::suspend_always` (`await_ready` false) and `std::suspend_never` (true) are the two trivial awaiters in
`<coroutine>`.

The promise type's hooks control the rest:

| Hook | Called |
|---|---|
| `get_return_object()` | At the start; its result is what the caller receives. |
| `initial_suspend()` | Right after; return `suspend_always` for a lazy coroutine, `suspend_never` to run at once. |
| `yield_value(v)` / `return_value(v)` / `return_void()` | For `co_yield` / `co_return v` / `co_return;` or falling off the end. |
| `unhandled_exception()` | If an exception escapes the body. |
| `final_suspend()` | At the end, must be `noexcept`. Returning `suspend_always` keeps the frame alive so you can inspect it. |

## A generator

A generator produces values on demand: each `co_yield` produces one element and suspends until the consumer asks for the
next. The sequence can be infinite because nothing is computed ahead. Below is a hand-written C++20 `Generator`, minimal
enough to show every piece:

```cpp title="generator_cpp20.cpp"
#include <coroutine>
#include <cstdio>
#include <exception>
#include <utility>

template <class T>
class Generator {
public:
    struct promise_type {
        T current;
        std::exception_ptr error;
        Generator get_return_object() {
            return Generator{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept { return {}; }   // lazy: start suspended
        std::suspend_always final_suspend() noexcept { return {}; }     // keep frame so we can query done()
        std::suspend_always yield_value(T v) { current = std::move(v); return {}; }
        void return_void() {}
        void unhandled_exception() { error = std::current_exception(); }
    };

    Generator(Generator&& o) noexcept : h_(std::exchange(o.h_, {})) {}
    Generator& operator=(Generator&& o) noexcept {
        if (this != &o) { if (h_) h_.destroy(); h_ = std::exchange(o.h_, {}); }
        return *this;
    }
    ~Generator() { if (h_) h_.destroy(); }              // frees the coroutine frame

    // Pull interface: advance to the next value; false when the coroutine has finished.
    bool next() {
        h_.resume();
        if (h_.promise().error) std::rethrow_exception(h_.promise().error);
        return !h_.done();
    }
    const T& value() const { return h_.promise().current; }

private:
    explicit Generator(std::coroutine_handle<promise_type> h) : h_(h) {}
    std::coroutine_handle<promise_type> h_;
};

Generator<int> fibonacci() {
    int a = 0, b = 1;
    for (;;) {
        co_yield a;                        // hand back one value, suspend here
        a = std::exchange(b, a + b);
    }
}

int main() {
    auto g = fibonacci();
    while (g.next() && g.value() <= 50) std::printf("%d ", g.value());
    std::puts("");
}
```

```text
0 1 1 2 3 5 8 13 21 34
```

Same output with g++ 15 and clang++ 21, `-O0`/`-O2`, and under `-fsanitize=thread,undefined`. The `Generator` owns the
frame and **must destroy it** (`h_.destroy()`); nothing else will, since the coroutine is suspended forever in the
infinite loop. That is [RAII](../13-idioms-and-design/01-raii.md) for a coroutine handle.

<Walkthrough title="What each next() does for fibonacci()" accent="violet">
  <Step title="Created, not started">

`fibonacci()` allocates the frame, builds the promise and returns the `Generator`. `initial_suspend` returned
`suspend_always`, so <StepChange>no body code has run</StepChange>.

  </Step>
  <Step title="First next()">

`resume()` runs the body from the top: `a = 0, b = 1`, then `co_yield a`. `yield_value(0)` stores
<StepChange>current = 0</StepChange> and suspends. `done()` is `false`, so `next()` returns `true`.

  </Step>
  <Step title="Second next()">

The body resumes after the `co_yield`, executes `a = exchange(b, a + b)` (so <StepChange>a = 1, b = 1</StepChange>),
loops, yields `1`. Locals `a` and `b` survived because they live in the frame.

  </Step>
  <Step title="Destruction">

When `g` goes out of scope its destructor calls `destroy()` on a coroutine that is suspended mid-loop; the frame and
its locals are destroyed.

  </Step>
</Walkthrough>

### `std::generator` (C++23)

You do not have to write that yourself in C++23: `std::generator<T>` (header `<generator>`) is a move-only
input range, so it works in range-for and composes with the [range adaptors](../09-standard-library/ranges.md):

```cpp title="generator_cpp23.cpp"
#include <cstdio>
#include <generator>
#include <ranges>
#include <utility>

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    for (;;) {
        co_yield a;
        a = std::exchange(b, a + b);
    }
}

int main() {
    for (int x : fibonacci() | std::views::take(10)) std::printf("%d ", x);
    std::puts("");
}
```

Prints `0 1 1 2 3 5 8 13 21 34` (built with `-std=c++23`, g++ 15 and clang++ 21 against libstdc++; library support
for `<generator>` differs between standard libraries and versions, so check yours). It also supports
`co_yield std::ranges::elements_of(r)` to yield all elements of another range or generator recursively.

## Asynchronous code: awaitable tasks

`co_await` lets one coroutine wait for another (or for I/O, a timer, a lock) without blocking its thread. The
awaited thing is a `task<T>`-like type. Here is a minimal lazy one with symmetric transfer, only to show how the
protocol composes: it runs entirely on one thread and uses no I/O.

```cpp title="task.cpp"
#include <coroutine>
#include <cstdio>
#include <exception>
#include <optional>
#include <utility>

// A minimal lazy Task<T>: starts when awaited or when run() is called, resumes its awaiter when done.
template <class T>
class Task {
public:
    struct promise_type {
        std::optional<T> value;
        std::exception_ptr error;
        std::coroutine_handle<> continuation;

        Task get_return_object() { return Task{std::coroutine_handle<promise_type>::from_promise(*this)}; }
        std::suspend_always initial_suspend() noexcept { return {}; }
        struct FinalAwaiter {
            bool await_ready() noexcept { return false; }
            std::coroutine_handle<> await_suspend(std::coroutine_handle<promise_type> h) noexcept {
                // symmetric transfer: jump straight into whoever awaited us, if anyone
                auto c = h.promise().continuation;
                return c ? c : std::noop_coroutine();
            }
            void await_resume() noexcept {}
        };
        FinalAwaiter final_suspend() noexcept { return {}; }
        void return_value(T v) { value = std::move(v); }
        void unhandled_exception() { error = std::current_exception(); }
    };

    Task(Task&& o) noexcept : h_(std::exchange(o.h_, {})) {}
    ~Task() { if (h_) h_.destroy(); }

    // co_await on a Task
    bool await_ready() const noexcept { return false; }
    std::coroutine_handle<> await_suspend(std::coroutine_handle<> awaiter) noexcept {
        h_.promise().continuation = awaiter;
        return h_;                                    // start the awaited task
    }
    T await_resume() {
        if (h_.promise().error) std::rethrow_exception(h_.promise().error);
        return std::move(*h_.promise().value);
    }

    // Driver for this single-threaded demo: run to completion, get the result.
    T run() {
        h_.resume();
        return await_resume();
    }

private:
    explicit Task(std::coroutine_handle<promise_type> h) : h_(h) {}
    std::coroutine_handle<promise_type> h_;
};

Task<int> square(int x) {
    std::puts("square runs");
    co_return x * x;
}

Task<int> sum_of_squares(int a, int b) {
    std::puts("sum starts");
    int s = co_await square(a) + co_await square(b);   // each co_await suspends us until the child is done
    co_return s;
}

int main() {
    auto t = sum_of_squares(3, 4);                      // lazy: nothing has run yet
    std::puts("created");
    std::printf("%d\n", t.run());
}
```

```text
created
sum starts
square runs
square runs
25
```

Lazy start is visible: `created` prints before any coroutine body runs. The two `square(...)` temporaries
live until the end of the full expression, which spans the suspensions, so they are alive when resumed. This `run()`
only works because nothing here ever suspends for real. A real task needs a scheduler or event loop to
resume it when I/O completes, plus more care (cancellation, allocation, exceptions, resumption on the right thread). The C++26 draft's `std::execution` aims to standardize this; for now use a library rather than extending this sketch.

### Which thread resumes?

`co_await` itself does not move work to another thread. After a suspension, the coroutine continues on **whichever thread
calls `resume()`**. An awaiter's `await_suspend` can hand the handle to a thread pool, a timer or an I/O completion
thread, and that thread then runs the rest of the coroutine. That is how coroutine libraries get concurrency, and it is why
everything in the frame must then follow the usual rules: state shared with other threads still needs
[synchronization](./01-cpp-memory-model.md), and the resumed code runs in a different thread from the one that started it
(`thread_local` values and thread-affine locks such as a held `std::mutex` do not carry over).

:::caution[Test cross-thread resumption under TSan]
GCC 15's ThreadSanitizer has reported data races on the coroutine frame when an awaiter resumes the coroutine from
another thread, while Clang's did not on the same code. This page shows no cross-thread resumption code; if you
write such an awaiter, test it with your own compiler and `-fsanitize=thread`.
:::

## Pitfalls

- **Dangling reference parameters.** A coroutine copies its parameters into the frame, but a reference parameter is
  copied *as a reference*. If the referenced object dies while the coroutine is suspended, the coroutine reads freed
  memory. This applies to `const T&`, `std::string_view`, `std::span`. Take such parameters by value:

  ```cpp
  // Fragment: Task is any coroutine return type.
  Task<void> risky(const std::string& msg);   // msg may dangle after the first suspension
  Task<void> safer(std::string msg);          // copied into the frame
  ```

- **Lambda coroutines and captures.** The closure object is not copied into the frame; only the arguments are. A
  capturing lambda that is a coroutine and is destroyed (or is a temporary) before the coroutine finishes leaves it
  with dangling captures. Pass what you need as parameters, or keep the lambda alive until completion.
- **Resuming wrongly.** Resuming a coroutine that is not suspended, or one that has finished, is undefined behaviour. A coroutine that is never resumed (or destroyed) leaks its frame.
- **Leaking frames.** Whoever holds the `coroutine_handle` must call `destroy()` exactly once (or let the coroutine destroy
  itself at `final_suspend`, using `suspend_never`).
- **Exceptions.** An exception escaping the body goes to `unhandled_exception()`; if you leave that empty, the exception is swallowed. Store it and rethrow
  at the consumer, as above.
- **Not a replacement for threads.** A coroutine that computes in a loop still occupies its thread; coroutines help
  with waiting, not with CPU parallelism.

## References

- [Coroutines (C++20) (cppreference)](https://en.cppreference.com/w/cpp/language/coroutines)
- [`std::generator` (cppreference)](https://en.cppreference.com/w/cpp/coroutine/generator)
- [`<coroutine>` library (cppreference)](https://en.cppreference.com/w/cpp/header/coroutine)
- [Coroutines, \[dcl.fct.def.coroutine\]](https://eel.is/c++draft/dcl.fct.def.coroutine)
