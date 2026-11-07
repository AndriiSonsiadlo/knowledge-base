---
id: condition-variables
title: Condition Variables
sidebar_label: Condition Variables
sidebar_position: 6
tags: [cpp, concurrency, condition-variable, wait, notify, spurious-wakeup, latch, semaphore]
---

# Condition Variables

A **condition variable** lets a thread sleep until another thread says that something it is waiting for
may now be true. Without one you either poll in a loop (burning CPU, or sleeping too long) or invent
signalling from atomics. This page is the canonical home for `std::condition_variable`,
`std::condition_variable_any`, and the waiting protocol around them.

**Prerequisites:** [Mutexes](./05-mutexes.md) (`unique_lock`), [Data races](./03-data-races.md).
Headers: `<condition_variable>`, `<mutex>`.

## The protocol

A condition variable holds no state and no condition of its own. The **condition** is ordinary shared
data (a flag, a queue, a counter) protected by a mutex; the variable is only the sleep/wake mechanism.
The waiting side:

1. Lock the mutex with a `std::unique_lock` (not `lock_guard`: the wait must unlock and relock it).
2. Call `cv.wait(lock, predicate)`. While `predicate()` is false, this atomically releases the
   mutex and blocks; when woken it re-acquires the mutex and rechecks. It returns with the mutex held and the
   predicate true.

The signalling side:

1. **Change the shared state while holding the mutex**, even if the state is an atomic. This is what
   prevents the lost wakeup described below.
2. Call `notify_one()` (wake one waiter) or `notify_all()` (wake all). You may notify with the mutex held or after
   releasing it; both are correct, and releasing first avoids waking a thread that then immediately blocks on the mutex.

<Diagram title="The wait/notify handshake" caption="The mutex protects the condition; the condition variable only moves threads between asleep and runnable." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Waiting thread">
      <DiagramNode title="lock mutex">unique_lock</DiagramNode>
      <DiagramNode title="predicate false?" accent>wait releases mutex and sleeps</DiagramNode>
      <DiagramNode title="woken: relock, recheck">proceeds when true</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="notify" />
    <DiagramGroup label="Signalling thread">
      <DiagramNode title="lock mutex, change state">flag, queue, counter</DiagramNode>
      <DiagramNode title="notify_one / notify_all" accent>after or while holding</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

```cpp title="wait_notify.cpp"
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <thread>

std::mutex m;
std::condition_variable cv;
bool ready = false;          // the condition lives in shared state, protected by m
int data = 0;

int main() {
    std::thread consumer([] {
        std::unique_lock lk(m);
        cv.wait(lk, [] { return ready; });   // loops internally: while (!ready) wait(lk);
        std::printf("got %d\n", data);
    });
    {
        std::lock_guard lk(m);
        data = 42;
        ready = true;                        // change the state under the mutex
    }
    cv.notify_one();                         // notifying after unlock is fine
    consumer.join();
}
```

Prints `got 42`; both compilers, `-O0`/`-O2`, clean under `-fsanitize=thread`. It is correct whichever thread
reaches the mutex first: if the notify happens before the consumer waits, the predicate is already true and
`wait` returns immediately.

## Why a predicate: spurious wakeups and lost wakeups

- **Spurious wakeup.** A waiting thread may return from `wait` without anyone calling notify. The standard permits it
  (implementations use it to simplify the OS layer). The fix is always to recheck the condition in a loop, which is
  exactly what the predicate overload does. `cv.wait(lk)` without a predicate is correct only inside your own
  `while (!cond) cv.wait(lk);`.
- **Notification without state.** A notification is not remembered. If thread A calls `notify_one()` before B
  starts waiting, B sleeps forever unless the *state* says "already done". Hence: signal through shared
  state, and have the waiter test that state before sleeping (the predicate does).
- **Lost wakeup from unprotected state.** If the signaller changes the flag without the mutex, it can change
  and notify in the gap between the waiter's predicate check and its going to sleep; the waiter then sleeps
  through the notification. Modifying the state under the mutex closes that gap.
- **Stolen wakeup.** With several waiters, another thread may take the item first; the predicate makes the
  loser go back to sleep.

## Timeouts

`wait_for(lock, duration, pred)` and `wait_until(lock, time_point, pred)` stop waiting after a deadline. The predicate overloads
return the predicate's value (`false` means timed out with the condition still unmet); the overloads
without a predicate return `std::cv_status`. Use `steady_clock` for deadlines, not `system_clock`, which can jump.
See [chrono](../09-standard-library/chrono.md).

```cpp title="wait_for.cpp"
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>

int main() {
    std::mutex m;
    std::condition_variable cv;
    bool ready = false;
    std::unique_lock lk(m);
    bool ok = cv.wait_for(lk, std::chrono::milliseconds(20), [&] { return ready; });
    std::printf("%d\n", ok);        // 0: timed out, predicate still false
}
```

## A blocking queue (producer-consumer) \{#blocking-queue\}

The standard use: producers push, consumers sleep until there is work or the queue is closed. The shutdown
flag is part of the *same* predicate, so closing wakes everyone cleanly.

```cpp title="blocking_queue.cpp"
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <optional>
#include <queue>
#include <thread>
#include <vector>

template <class T>
class BlockingQueue {
public:
    void push(T v) {
        {
            std::lock_guard lk(m_);
            q_.push(std::move(v));
        }
        cv_.notify_one();
    }
    void close() {
        { std::lock_guard lk(m_); closed_ = true; }
        cv_.notify_all();                                   // wake every waiting consumer
    }
    std::optional<T> pop() {                                // nullopt: closed and drained
        std::unique_lock lk(m_);
        cv_.wait(lk, [this] { return !q_.empty() || closed_; });
        if (q_.empty()) return std::nullopt;
        T v = std::move(q_.front());
        q_.pop();
        return v;
    }
private:
    std::mutex m_;
    std::condition_variable cv_;
    std::queue<T> q_;
    bool closed_ = false;
};

int main() {
    BlockingQueue<int> q;
    long sum[2] = {0, 0};
    std::vector<std::jthread> consumers;
    for (int c = 0; c < 2; ++c)
        consumers.emplace_back([&q, &sum, c] { while (auto v = q.pop()) sum[c] += *v; });
    for (int i = 1; i <= 1000; ++i) q.push(i);
    q.close();
    consumers.clear();                                      // join
    std::printf("%ld\n", sum[0] + sum[1]);
}
```

It prints `500500` regardless of how the items were split between the two consumers (g++ and clang++, both
optimization levels, TSan clean). `notify_one` suffices in `push` because one new item can satisfy only one
consumer; `close` uses `notify_all` because all of them must see the flag. The [thread
pool page](./08-thread-pools.md) builds on this queue.

## Cancellable waits: `condition_variable_any` and stop tokens (C++20)

`std::condition_variable` works only with `std::unique_lock<std::mutex>`. `std::condition_variable_any` works with any
lock type and (C++20) has `wait` overloads that take a `std::stop_token`, so a `std::jthread` can be told to stop while
blocked:

```cpp title="cv_any_stop.cpp"
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <stop_token>
#include <thread>

int main() {
    std::mutex m;
    std::condition_variable_any cv;
    bool ready = false;                       // never becomes true
    std::jthread t([&](std::stop_token st) {
        std::unique_lock lk(m);
        bool ok = cv.wait(lk, st, [&] { return ready; });   // returns when stop is requested
        std::printf("predicate satisfied: %d\n", ok);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    t.request_stop();
}
```

Prints `predicate satisfied: 0`: the wait ended because of the stop request, not because the condition held.
See [Threads](./04-threads.md#jthread) for stop tokens. The cost of `_any` is a possible extra internal
mutex, so use the plain variable when you do not need these features.

## Often better than a condition variable (C++20)

For common patterns the library now has ready-made primitives, so you do not have to build them from a mutex, a flag and a
condition variable: `std::latch` (one-shot countdown), `std::barrier` (reusable phase barrier),
`std::counting_semaphore` / `std::binary_semaphore`, and `std::atomic::wait/notify`
([Atomics](./02-atomics-and-fences.md)).

```cpp title="latch_semaphore.cpp"
#include <cstdio>
#include <latch>
#include <semaphore>
#include <thread>
#include <vector>

int main() {
    std::latch done(3);                                   // one-shot countdown
    std::vector<std::jthread> ws;
    for (int i = 0; i < 3; ++i) ws.emplace_back([&] { done.count_down(); });
    done.wait();
    std::puts("all 3 finished");

    std::counting_semaphore<4> slots(2);                  // at most 2 holders
    slots.acquire();
    std::printf("try_acquire: %d\n", slots.try_acquire());
    std::printf("try_acquire: %d\n", slots.try_acquire());   // 0: none left
    slots.release(2);
}
```

Output: `all 3 finished`, `try_acquire: 1`, `try_acquire: 0`. (`try_acquire` may fail spuriously by
specification; here no other thread contends and both compilers printed these values.)

## Pitfalls

- **`wait` without a predicate and without a loop** is a bug: spurious wakeups.
- **Setting the flag without the mutex** (even for `atomic<bool>`) can lose the wakeup.
- **Using one condition variable with different mutexes** is undefined behaviour for concurrent waiters;
  pair each condition variable with exactly one mutex.
- **Destroying a condition variable** while threads wait on it is UB; shut waiters down first.
- **`notify_all` on a single-consumer condition** works but wakes needlessly; `notify_one` on a queue with
  mixed waiting conditions (e.g. "not empty" and "not full" on one variable) can wake the wrong thread
  and stall: use separate variables or `notify_all`.
- **Calling notify and then destroying** the condition variable or its mutex right away (e.g. the waiter
  frees them as soon as it wakes) needs care that the notifier is finished with them.

## References

- [`std::condition_variable` (cppreference)](https://en.cppreference.com/w/cpp/thread/condition_variable)
- [`std::condition_variable_any` (cppreference)](https://en.cppreference.com/w/cpp/thread/condition_variable_any)
- [`std::latch`, `std::barrier`, `std::counting_semaphore` (cppreference)](https://en.cppreference.com/w/cpp/thread)
- [Condition variables, \[thread.condition\]](https://eel.is/c++draft/thread.condition)
