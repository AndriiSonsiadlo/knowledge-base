---
id: thread-pools
title: Thread Pools
sidebar_label: Thread Pools
sidebar_position: 8
tags: [cpp, concurrency, thread-pool, task-queue, packaged-task, jthread]
---

# Thread Pools

A **thread pool** is a fixed set of worker threads that take tasks from a shared queue. It exists because
creating a thread per task costs a system call and a stack each time, and because unbounded thread counts
overload the machine. The pool caps the number of threads and reuses them.

:::info[There is no standard thread pool]
As of C++23 the standard library has no thread pool, executor or task scheduler. `std::async` is not one:
it gives you no control over thread count, and implementations are free to start a thread per call. The
standardized direction is `std::execution` (senders/receivers, adopted for C++26), but do not assume your
standard library ships it yet. In the meantime you write a small pool (below), use a library
(for example Boost.Asio's `thread_pool`, oneTBB, or your platform's), or use the parallel algorithms
(`std::for_each(std::execution::par, ...)`, C++17; see [Algorithms](../09-standard-library/algorithms.md)).
:::

**Prerequisites:** [Threads](./04-threads.md) (`jthread`, stop tokens),
[Condition variables](./06-condition-variables.md#blocking-queue) (the blocking queue this builds on),
[Futures](./07-futures-and-promises.md) (`packaged_task`).

## The design

<Diagram title="Pool structure" caption="Submitters push tasks; workers pop and run them. The mutex guards only the queue." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Callers">
      <DiagramNode title="submit(f)">returns a future</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="push + notify" />
    <DiagramGroup label="Shared">
      <DiagramNode title="task queue" accent>mutex + condition variable</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="pop, run outside the lock" />
    <DiagramGroup label="Workers">
      <DiagramNode title="jthread 1..N">loop until stop and queue empty</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

Decisions the code makes explicit:

- **Workers are `std::jthread`s.** Destroying the pool requests stop on each and the destructor of the
  `jthread` joins, so shutdown cannot be forgotten.
- **A `condition_variable_any` with a stop token**: `wait(lock, stop_token, pred)` wakes when work arrives
  *or* stop is requested ([Condition variables](./06-condition-variables.md#cancellable-waits-condition_variable_any-and-stop-tokens-c20)).
- **Drain on shutdown.** A worker exits only when stop was requested *and* the queue is empty, so submitted tasks are not lost.
- **Tasks run outside the lock**, otherwise the pool is serial.
- **Results via `packaged_task`.** `submit` returns a `std::future`; exceptions thrown by the task are stored and
  rethrown by `get()` ([Futures](./07-futures-and-promises.md)). `packaged_task` is move-only but `std::function`
  needs a copyable callable, so the example shares it through a `shared_ptr`. With C++23 use
  `std::move_only_function<void()>` for the queue's element type and drop the `shared_ptr`.
- **Member order matters**: `workers_` is declared last so it is destroyed first, while the queue and mutex the workers use still exist.

## A minimal pool

```cpp title="thread_pool.cpp"
#include <condition_variable>
#include <cstdio>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <queue>
#include <stop_token>
#include <thread>
#include <type_traits>
#include <vector>

class ThreadPool {
public:
    explicit ThreadPool(std::size_t n) {
        for (std::size_t i = 0; i < n; ++i)
            workers_.emplace_back([this](std::stop_token st) { run(st); });
    }

    // Destruction: request stop on every worker, let them drain the queue, then jthread joins.
    ~ThreadPool() {
        for (auto& w : workers_) w.request_stop();
    }

    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    template <class F>
    auto submit(F f) -> std::future<std::invoke_result_t<F>> {
        using R = std::invoke_result_t<F>;
        // packaged_task is move-only but std::function needs a copyable callable: share it.
        auto task = std::make_shared<std::packaged_task<R()>>(std::move(f));
        auto fut = task->get_future();
        {
            std::lock_guard lk(m_);
            q_.push([task] { (*task)(); });
        }
        cv_.notify_one();
        return fut;
    }

private:
    void run(std::stop_token st) {
        for (;;) {
            std::function<void()> job;
            {
                std::unique_lock lk(m_);
                cv_.wait(lk, st, [this] { return !q_.empty(); });
                if (q_.empty()) return;            // stop requested and nothing left
                job = std::move(q_.front());
                q_.pop();
            }
            job();                                 // run outside the lock
        }
    }

    std::mutex m_;
    std::condition_variable_any cv_;
    std::queue<std::function<void()>> q_;
    std::vector<std::jthread> workers_;            // declared last: destroyed (joined) first
};

int main() {
    std::vector<std::future<long>> parts;
    {
        ThreadPool pool(4);
        for (int c = 0; c < 8; ++c)
            parts.push_back(pool.submit([c] {
                long s = 0;
                for (int i = c * 1000 + 1; i <= (c + 1) * 1000; ++i) s += i;
                return s;
            }));
    }                                              // pool destroyed: queue drained, workers joined
    long total = 0;
    for (auto& f : parts) total += f.get();        // futures outlive the pool
    std::printf("%ld\n", total);
}
```

```text
32004000
```

That is the sum of 1 to 8000, and it is the output with g++ 15 and clang++ 21 at `-O0` and `-O2`; ThreadSanitizer
reported nothing in 150 runs with each compiler on the final version.

Limits of this pool, deliberately: no way to submit after destruction begins (do not call `submit`
while the pool is being destroyed), no task priorities, no work stealing, one shared queue (so a single mutex is
the contention point at high task rates), and a task that blocks waiting for another task in the same pool can
deadlock it when all workers are busy waiting. Do not wait on pool futures from inside pool tasks unless
the pool has spare workers.

:::note[TSan and exception_ptr]
In an earlier variant of this example, one task threw, and ThreadSanitizer with GCC 15 intermittently
(2 of about 300 runs) reported a data race inside libstdc++'s `std::exception_ptr` release between the worker
and the thread calling `get()`. It was not confirmed whether that is a real race or a TSan limitation with the
uninstrumented library's reference counting, so treat reports with `exception_ptr` frames in them with
suspicion and re-check, and don't assume either way. The version shown has no throwing task and ran clean.
:::

## Choosing the size

Pick the thread count from the workload, then measure:

- **CPU-bound** tasks gain nothing past the number of hardware threads. `std::thread::hardware_concurrency()` is a hint and may
  return `0`.
- **Blocking** tasks (I/O, waiting on locks) can profit from more threads than cores, because most of them are asleep.
  There is no universal multiplier; measure.
- Mixing both in one pool lets slow tasks hold all the workers; separate pools per kind of work avoid it.

## Task granularity

Each task costs a lock, a heap allocation (the `std::function` and `packaged_task`) and a wakeup. If the work
per task is comparable to that cost, the pool is slower than a plain loop. Batch many small items into one
task (a chunk of a range) so each task does a worthwhile amount of work. How large "worthwhile" is depends on your
machine; profile ([Debugging and profiling](../14-debugging-and-profiling/01-debugging-basics.md)).

## Pitfalls

- **Task exceptions vanish if nobody calls `get()`**: they are stored in the future, never reported.
- **Dangling captures.** The task runs later, on another thread: capture by value or ensure the referenced
  objects outlive it.
- **Submit after shutdown.** Decide what it means (reject, throw) and enforce it.
- **Blocking on futures inside the pool** can deadlock, as above.
- **Hard cancellation does not exist.** A stop request only reaches tasks that check the token themselves. A pool task cannot be
  killed.
- **Shared mutable state between tasks** is still a [data race](./03-data-races.md); the pool changes who runs the code, not the rules.

## References

- [`std::jthread` (cppreference)](https://en.cppreference.com/w/cpp/thread/jthread)
- [`std::condition_variable_any::wait` with stop_token (cppreference)](https://en.cppreference.com/w/cpp/thread/condition_variable_any/wait)
- [P2300, `std::execution`](https://wg21.link/p2300)
