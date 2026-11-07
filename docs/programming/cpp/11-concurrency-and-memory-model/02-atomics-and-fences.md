---
id: atomics-and-fences
title: Atomics and Memory Fences
sidebar_label: Atomics & Fences
sidebar_position: 2
tags: [cpp, concurrency, atomics, fences, memory-order, lock-free, compare-exchange]
---

# Atomics and Memory Fences

`std::atomic<T>` (header `<atomic>`) gives a variable operations that no other thread can observe half
done, and lets each operation say how much ordering it also provides. This page is the canonical home
for the `std::atomic` API, choosing a `memory_order`, and fences. What the orders *mean*
(synchronizes-with, happens-before) is in the [C++ memory model](./01-cpp-memory-model.md); why
you need atomics at all is in [Data races](./03-data-races.md).

**Prerequisites:** [C++ memory model](./01-cpp-memory-model.md).

## The operations

An atomic operation is indivisible: no other thread sees a torn value or an intermediate step.
`std::atomic<T>` works for any trivially copyable `T`; integral, pointer and (C++20) floating-point
specializations add arithmetic.

| Operation | What it does |
|---|---|
| `load()`, `store(v)` | Read / write. `=` and the conversion operator are `seq_cst` versions of these. |
| `exchange(v)` | Store `v`, return the old value. |
| `compare_exchange_strong/weak(expected, desired)` | If the value equals `expected`, store `desired` and return `true`; otherwise copy the current value into `expected` and return `false`. |
| `fetch_add/sub/and/or/xor(v)` | Read-modify-write, return the old value (integers; `add`/`sub` also on pointers and, C++20, floats). |
| `++`, `--`, `+=`, ... | The same, returning the new value; always `seq_cst`. |
| `wait(old)`, `notify_one/all()` | C++20: block until the value is not `old`; wake waiters. |
| `is_lock_free()`, `is_always_lock_free` | Whether operations avoid an internal lock (see below). |

Each member takes an optional `std::memory_order` argument (default `seq_cst`); the operator forms cannot.

A counter shared by four threads, with no ordering needed beyond atomicity:

```cpp title="counter.cpp"
#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

std::atomic<long> hits{0};

void count_hits() {
    for (int i = 0; i < 100000; ++i)
        hits.fetch_add(1, std::memory_order_relaxed);
}

int main() {
    std::vector<std::thread> ts;
    for (int i = 0; i < 4; ++i) ts.emplace_back(count_hits);
    for (auto& t : ts) t.join();                 // join synchronizes-with, so this read is ordered
    std::printf("%ld\n", hits.load());
}
```

```text
400000
```

The output is always `400000` (built with `g++` and `clang++ -std=c++20 -pthread`, at `-O0` and `-O2`; clean
under `-fsanitize=thread`). The same loop on a plain `long` would be a [data race](./03-data-races.md).

## Compare-and-swap loops \{#compare-and-swap\}

`compare_exchange` is the building block for any update that is not one of the built-in
read-modify-writes. The pattern: read the current value, compute the new one, try to install it, and
retry if someone changed it meanwhile.

```cpp title="update_max.cpp"
#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

// Atomic maximum as a CAS loop (the standard has no fetch_max before C++26).
void update_max(std::atomic<int>& target, int value) {
    int cur = target.load(std::memory_order_relaxed);
    while (cur < value &&
           !target.compare_exchange_weak(cur, value, std::memory_order_relaxed)) {
        // on failure `cur` was reloaded with the current value; the loop re-checks it
    }
}

int main() {
    std::atomic<int> peak{0};
    std::vector<std::thread> ts;
    for (int i = 1; i <= 4; ++i)
        ts.emplace_back([&peak, i] { for (int k = 0; k < 1000; ++k) update_max(peak, i * 1000 + k); });
    for (auto& t : ts) t.join();
    std::printf("%d\n", peak.load());
}
```

```text
4999
```

Why `expected` is passed by reference: on failure it is overwritten with the value actually seen, so the
next iteration needs no extra `load`.

**Strong vs weak.** `compare_exchange_weak` is allowed to fail spuriously (return `false` even though the
value matched); on some CPUs (LL/SC architectures like ARM and POWER) that lets it compile to cheaper code.
Use `weak` inside a retry loop, `strong` when a single attempt should be reliable.

**ABA.** CAS only checks that the value is *equal*, not that nothing happened in between. If a pointer goes
`A -> B -> A` another thread's CAS succeeds on stale assumptions. This is the main trap when writing
lock-free containers (for example freeing a popped node while another thread still holds its address), and
the reason such structures are better taken from a vetted library than written by hand.

## Choosing a memory order \{#memory-order-choices\}

| Situation | Order | Why |
|---|---|---|
| Not sure | default `seq_cst` | Simplest to reason about; the single total order removes surprises. |
| Independent counter or statistic, read after `join` or by a tolerant observer | `relaxed` | Atomicity only. Nothing else depends on it. |
| A flag that publishes other data (producer sets, consumer reads) | `release` store, `acquire` load | Creates the synchronizes-with edge ([example](./01-cpp-memory-model.md#synchronizes-with-and-happens-before)). |
| Read-modify-write that both consumes and publishes (lock-like, reference-count drop) | `acq_rel` | Acquire the previous owner's writes, release yours. |
| Spin lock acquire / release | `acquire` on the successful `test_and_set`/`exchange`; `release` on unlock | Critical section stays between them. |
| Two or more atomics where all threads must agree on a global order (Dekker/Peterson style) | `seq_cst` | Acquire/release does not give that, see [store buffering](./01-cpp-memory-model.md#what-sequential-consistency-adds). |

Restrictions: a `load` cannot use `release` or `acq_rel`, a `store` cannot use `acquire` or `acq_rel`.
`compare_exchange` takes two orders, one for success and one for failure; the failure order is a load and
cannot be `release`/`acq_rel`. (Before C++17 the failure order could not be stronger than the success one;
that restriction was removed.) Do not use `consume`.

Relaxed is easy to get wrong because correctness may depend on no other code: start from `seq_cst` and
relax only a hot spot you have measured. Cycle counts quoted for each order vary by CPU and
compiler and are not given here.

## Fences \{#fences\}

`std::atomic_thread_fence(order)` orders surrounding operations without being tied to one atomic
object. A release fence followed (in program order) by an atomic store, and an atomic load followed
by an acquire fence, produce the same synchronizes-with edge as release/acquire on the atomic itself,
even when the atomic accesses are `relaxed`:

```cpp title="fence_pair.cpp"
#include <atomic>
#include <cstdio>
#include <thread>

int x = 0, y = 0;
std::atomic<bool> ready{false};

void writer() {
    x = 1;
    y = 2;
    std::atomic_thread_fence(std::memory_order_release);
    ready.store(true, std::memory_order_relaxed);
}

void reader() {
    while (!ready.load(std::memory_order_relaxed)) {
    }
    std::atomic_thread_fence(std::memory_order_acquire);
    std::printf("%d %d\n", x, y);       // 1 2
}

int main() {
    std::thread r(reader), w(writer);
    w.join();
    r.join();
}
```

This is correct and prints `1 2`. Both fences are needed in this program, and they only work through the atomic that
carries the value from one side to the other. (A release fence can also pair with an acquire *load*, and a release *store* with an acquire fence; each combination synchronizes if the load reads the stored value.)

When to prefer a fence: when one release publishes many writes and several relaxed loads need only one
acquire after the loop, or when the order depends on a branch. Otherwise the per-operation form is clearer.

:::warning[ThreadSanitizer does not model standalone fences]
`-fsanitize=thread` does not understand `std::atomic_thread_fence`. GCC 15 warns (`-Wtsan`:
"`atomic_thread_fence` is not supported with `-fsanitize=thread`") and clang 21 reports a false data
race on `x` for the program above, which is correct code. If you use fences, prefer release/acquire on
the atomic itself where possible, so the tool can verify it. See [Data races](./03-data-races.md#finding-races-with-threadsanitizer).
:::

`atomic_signal_fence` is the compiler-only variant, for ordering against a signal handler in the
same thread; it emits no hardware barrier.

## `std::atomic_flag` and the C++20 additions

`std::atomic_flag` is the one type guaranteed lock-free in every hosted implementation (C++20 also adds `std::atomic_signed_lock_free` and `std::atomic_unsigned_lock_free`, aliases for an always-lock-free integer type). It holds a bool-like
state with `test_and_set` and `clear`; C++20 adds `test()` and `wait/notify`, and makes a default-constructed flag
clear (`ATOMIC_FLAG_INIT` is no longer needed but still valid; it was kept for C compatibility, while `ATOMIC_VAR_INIT` and `atomic_init` are the deprecated ones). A spin lock, with `wait` so a loser sleeps instead of burning CPU:

```cpp title="spinlock.cpp"
#include <atomic>
#include <cstdio>
#include <thread>

class Spinlock {
    std::atomic_flag flag_;                       // C++20: starts clear
public:
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire)) {
            flag_.wait(true, std::memory_order_relaxed);   // block until the flag changes
        }
    }
    void unlock() {
        flag_.clear(std::memory_order_release);
        flag_.notify_one();
    }
};

Spinlock lk;
long total = 0;                                   // protected by lk

int main() {
    auto work = [] { for (int i = 0; i < 100000; ++i) { lk.lock(); ++total; lk.unlock(); } };
    std::thread a(work), b(work);
    a.join(); b.join();
    std::printf("%ld\n", total);                  // 200000
}
```

Passes under `-fsanitize=thread` with both compilers. In real code use [`std::mutex`](./05-mutexes.md): it
blocks in the OS under contention instead of burning CPU, and it is the standard, reviewed primitive.

Other C++20 types: `std::atomic_ref<T>` applies atomic operations to an ordinary object
(which must stay suitably aligned and must not be accessed non-atomically while any `atomic_ref` to it
exists), and `std::atomic<std::shared_ptr<T>>` / `atomic<weak_ptr<T>>` are the supported way to
share a smart pointer; see [shared_ptr](../06-pointers-references-and-smart-pointers/shared-ptr.md).

## Is it really lock-free?

`std::atomic<T>` for a `T` the hardware cannot handle in one instruction falls back to a lock hidden in the
library. `is_always_lock_free` (C++17, a `static constexpr`) answers at compile time; `is_lock_free()` at
run time. Both are implementation-specific. On the platform and compilers tested here (x86-64 Linux, GCC 15
and clang 21), `atomic<int>` and `atomic<void*>` are always lock-free and a 64-byte struct is not:

```cpp title="lock_free_check.cpp"
#include <atomic>
#include <cstdio>

struct Big { char bytes[64]; };

int main() {
    static_assert(std::atomic<int>::is_always_lock_free);   // true on mainstream targets, not guaranteed everywhere
    std::atomic<Big> big;
    std::printf("%d\n", big.is_lock_free() ? 1 : 0);          // 0 here
    std::printf("%d\n", std::atomic<void*>::is_always_lock_free ? 1 : 0);   // 1 here
}
```

Output `0` then `1`. Link with `-latomic`: the lock-based fallback for `atomic<Big>` lives in libatomic,
and without it the link fails (`undefined reference to '__atomic_is_lock_free'`). That fallback also
means such an atomic may not be address-free, so don't place it in memory shared between processes.

## Pitfalls

- **Atomic operations don't compose.** `if (a.load() == 0) a.store(1);` is two operations and races with
  another thread; use `compare_exchange` or a mutex.
- **Two atomics are not one atomic.** Updating `count` and `sum` separately lets another thread see one new
  and one old. Put related state under a [mutex](./05-mutexes.md).
- **Mixing atomic and plain access** to the same object is a data race.
- **Relaxed publication.** Setting a `relaxed` flag and then reading plain data in another thread is a race;
  the flag needs release/acquire ([example](./01-cpp-memory-model.md#synchronizes-with-and-happens-before)).
- **False sharing.** Atomics next to each other in memory contend for a cache line; see
  [Alignment](../05-memory-and-object-lifetime/alignment.md) for `alignas` and `hardware_destructive_interference_size`.
- **Hand-written lock-free containers** are rarely worth it; correctness (ABA, memory reclamation) is
  hard, and a mutex is often fast enough.

## References

- [`std::atomic` (cppreference)](https://en.cppreference.com/w/cpp/atomic/atomic)
- [`std::atomic_thread_fence` (cppreference)](https://en.cppreference.com/w/cpp/atomic/atomic_thread_fence)
- [`std::atomic_flag` (cppreference)](https://en.cppreference.com/w/cpp/atomic/atomic_flag)
- [Atomic operations library, \[atomics\]](https://eel.is/c++draft/atomics)
