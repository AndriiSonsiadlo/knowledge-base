---
id: cpp-memory-model
title: C++ Memory Model
sidebar_label: Memory Model
sidebar_position: 1
tags: [cpp, concurrency, memory-model, happens-before, synchronizes-with, memory-order]
---

# C++ Memory Model

Since C++11 the language itself defines what a thread may observe of another thread's writes. That
definition is the **memory model**. It exists because both compilers and CPUs reorder and cache
memory operations for speed, so "thread 2 reads what thread 1 wrote" is not true by default. The model
says exactly when it is true, and gives you the tools (atomics, mutexes, thread start/join) that
create those guarantees. Everything else in this section builds on it.

This page is the canonical home for **happens-before**, **synchronizes-with** and the meaning of
the `memory_order` values. The `std::atomic` API and how to choose an order live in
[Atomics and fences](./02-atomics-and-fences.md); the definition of a data race and how to find one
live in [Data races](./03-data-races.md).

**Prerequisites:** [Memory model overview](../05-memory-and-object-lifetime/memory-model-overview.md)
(the process address space, which is a different thing from this model), and
[Storage duration](../05-memory-and-object-lifetime/storage-duration.md).

## The problem: reordering you cannot see from one thread

Within one thread the compiler and CPU must preserve the program's observable single-threaded
behaviour (the as-if rule), but they may reorder independent loads and stores, keep values in registers,
and buffer stores. A second thread can therefore see a thread's writes late, out of order, or (for plain
variables) not in any consistent way. The model's answer is a contract: if you use the synchronization
tools correctly, the program behaves as if there was a sensible interleaving; if you do not (a data
race), the behaviour is undefined.

## Evaluation order and memory locations

Two terms underpin the rest.

- **Memory location**: a scalar object (or a maximal run of adjacent non-zero-width bit-fields). Two threads
  writing *different* memory locations never race, even if they sit in the same struct or cache line.
  (Same cache line is a performance problem, not a correctness one.)
- **Sequenced-before**: the single-threaded ordering of evaluations within one thread, defined by the
  language's evaluation rules (a full-expression is sequenced before the next one).

## Synchronizes-with and happens-before

The model builds cross-thread ordering from a few relations.

**Synchronizes-with** is established by specific pairs of operations. The key one: an atomic
**release** store (or stronger) to an atomic object `a`, and an atomic **acquire** load (or stronger) of
`a` that reads the value written by that store (or a value from its release sequence).
Other sources: unlocking a mutex synchronizes with the next lock of it, a thread's start is
synchronized with the beginning of the new thread's function, the end of a thread synchronizes with
the `join()` that returns, and the fulfilment of a `promise` synchronizes with the `future` call that
returns the result.

**Inter-thread happens-before** chains sequenced-before and synchronizes-with edges, and
**happens-before** is what you reason with (the formal definition also covers `consume` dependency chains, which this page skips). If A happens-before B, then A's effects are visible to B.

<Diagram title="One release/acquire pair orders everything around it" caption="Every write before the release is visible to every read after the acquire that observed it." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Producer thread">
      <DiagramNode title="payload = 42">plain write</DiagramNode>
      <DiagramNode title="ready.store(true, release)" accent>publishes</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="synchronizes-with" />
    <DiagramGroup label="Consumer thread">
      <DiagramNode title="ready.load(acquire) == true" accent>observes the store</DiagramNode>
      <DiagramNode title="read payload">sees 42</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

```cpp title="message_passing.cpp"
#include <atomic>
#include <cstdio>
#include <thread>

int payload = 0;                    // plain, non-atomic
std::atomic<bool> ready{false};

void producer() {
    payload = 42;                                    // (1)
    ready.store(true, std::memory_order_release);    // (2)
}

void consumer() {
    while (!ready.load(std::memory_order_acquire)) { // (3)
    }
    std::printf("%d\n", payload);                    // (4) reads 42
}

int main() {
    std::thread c(consumer);
    std::thread p(producer);
    p.join();
    c.join();
}
```

(1) is sequenced-before (2); (2) synchronizes-with (3) once (3) reads `true`; (3) is sequenced-before (4).
So (1) happens-before (4), the plain read in (4) cannot race with the plain write in (1), and the
output is `42`. Built with `-pthread`, this also runs clean under `-fsanitize=thread`.

If you weaken `release`/`acquire` to `relaxed`, the store and load still happen atomically but no
synchronizes-with edge exists, so (1) and (4) race on `payload` and the program has undefined behaviour.

## The six memory orders

Each atomic operation takes a `std::memory_order`. It does not make the operation atomic (that is
always so); it states which *other* operations it orders relative to it.

| Order | Meaning on the operation | Can be used on |
|---|---|---|
| `relaxed` | Atomic, but creates no synchronizes-with edge and no ordering of surrounding operations. Still obeys the modification order of that one object. | load, store, RMW |
| `acquire` | No later read or write in this thread can be moved before it; pairs with a release. | load, RMW, fence |
| `release` | No earlier read or write in this thread can be moved after it; pairs with an acquire. | store, RMW, fence |
| `acq_rel` | Both, for a read-modify-write. | RMW, fence |
| `seq_cst` | Acquire/release plus one single total order of all `seq_cst` operations that every thread agrees on. The default. | all |
| `consume` | Like acquire but only for operations that carry a data dependency from the load. | load |

On `consume`: since C++17 the standard says its specification is being revised and its use is
discouraged, and mainstream compilers implement it as `acquire`. Do not use it. Which order to pick for a given job, and
the exact operations each applies to, is in [Atomics and fences](./02-atomics-and-fences.md#memory-order-choices).

Two further rules matter in practice:

- **Modification order.** Every atomic object has a single total order of its writes that all
  threads agree on, even with `relaxed`. What `relaxed` does not give you is any relationship between the
  orders of *different* objects.
- **Release sequences.** A read-modify-write to an atomic that follows a release store continues that
  release sequence, so an acquire that reads the RMW's value still synchronizes with the original
  release (C++20 narrowed this: only RMWs, not later stores by the same thread, continue it).

## What sequential consistency adds

With `seq_cst` every thread agrees on one global order of the `seq_cst` operations, and that order is
consistent with each thread's program order. Acquire/release alone does not promise that. The classic
case is the store-buffering pattern:

```cpp title="store_buffering.cpp"
#include <atomic>
#include <cstdio>
#include <thread>

std::atomic<int> x{0}, y{0};
int r1, r2;

int main() {
    std::thread a([] {
        x.store(1);        // seq_cst (default)
        r1 = y.load();
    });
    std::thread b([] {
        y.store(1);
        r2 = x.load();
    });
    a.join();
    b.join();
    // r1 == 0 && r2 == 0 is impossible; the other three outcomes can occur.
    std::printf("%s\n", (r1 == 0 && r2 == 0) ? "impossible outcome seen" : "ok");
}
```

With the default `seq_cst` the outcome `r1 == r2 == 0` cannot happen, so this prints `ok`. Replace all four
operations with `release` stores and `acquire` loads and the outcome `0, 0` becomes allowed: each
store may still sit in a store buffer while the other thread's load runs. This is why `seq_cst` is the
default and the safe choice. Weaker orders trade that guarantee for fewer barriers on some CPUs (on x86-64
plain loads and stores already have acquire/release hardware ordering, so the difference shows mainly on
weakly ordered CPUs such as ARM and POWER); measure before relying on any speedup.

## Mutexes and thread operations are synchronization too

You do not need atomics to get happens-before. A `std::mutex` unlock synchronizes with the next
lock, so everything written under the lock is visible to the next thread that takes it. Thread
creation and `join()`, `std::call_once`, the initialization of function-local statics (C++11), and
the `promise`/`future` pair do the same. See [Mutexes](./05-mutexes.md),
[Threads](./04-threads.md) and [Futures and promises](./07-futures-and-promises.md). Prefer them; reach
for explicit memory orders only when profiling shows a lock is the bottleneck.

## Pitfalls

- **Ordering is not visibility "soon".** `relaxed` guarantees nothing about when a write is seen or
  about other variables. Spinning on a relaxed flag then reading plain data is a data race.
- **`volatile` is not atomic and does not synchronize.** See [volatile](../12-low-level-and-platform/05-volatile.md).
- **Mixing atomic and non-atomic access to one object** is a data race.
- **Fences are not magic barriers.** `std::atomic_thread_fence` only works together with atomic
  operations on some atomic object; see [Atomics and fences](./02-atomics-and-fences.md#fences).

## References

- [Memory model (cppreference)](https://en.cppreference.com/w/cpp/language/memory_model)
- [`std::memory_order` (cppreference)](https://en.cppreference.com/w/cpp/atomic/memory_order)
- [Multi-threaded executions and data races, \[intro.multithread\]](https://eel.is/c++draft/intro.multithread)
