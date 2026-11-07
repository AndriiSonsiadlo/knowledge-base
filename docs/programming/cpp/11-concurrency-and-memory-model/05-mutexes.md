---
id: mutexes
title: Mutexes and Locks
sidebar_label: Mutexes
sidebar_position: 5
tags: [cpp, concurrency, mutex, lock-guard, unique-lock, scoped-lock, shared-mutex, deadlock, call-once]
---

# Mutexes and Locks

A **mutex** (mutual exclusion) lets only one thread at a time run a **critical section**, which is how you
protect data that more than one thread touches and that is too big or too interrelated for a single
[atomic](./02-atomics-and-fences.md). Locking creates the happens-before edges from the
[memory model](./01-cpp-memory-model.md): everything one thread wrote before `unlock()` is visible to the
next thread that `lock()`s the same mutex. This page is the canonical home for the mutex types, the RAII
lock wrappers, deadlock avoidance and `std::call_once`.

**Prerequisites:** [Data races](./03-data-races.md), [Threads](./04-threads.md).
All headers: `<mutex>` (plus `<shared_mutex>` for reader-writer locks). Link with `-pthread` on Linux.

## Never lock by hand: the RAII wrappers

Calling `m.lock()` and `m.unlock()` yourself leaks the lock if anything between them throws or returns early.
Use a wrapper that unlocks in its destructor. This is [RAII](../13-idioms-and-design/01-raii.md) applied to a lock.

| Wrapper | Since | Use it for |
|---|---|---|
| `std::lock_guard<M>` | C++11 | One mutex, locked for the whole scope. The default choice. |
| `std::scoped_lock<M...>` | C++17 | One or more mutexes at once, deadlock-free (see below). Can replace `lock_guard` everywhere. |
| `std::unique_lock<M>` | C++11 | When you need to unlock early, defer or retry locking, transfer ownership (movable), or use a condition variable. |
| `std::shared_lock<M>` | C++14 | A shared (reader) lock on a `shared_mutex`. |

```cpp title="counter_lock_guard.cpp"
#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>

class Counter {
public:
    void increment() {
        std::lock_guard<std::mutex> lock(m_);   // locked here, unlocked at scope exit
        ++value_;
    }
    int get() const {
        std::lock_guard<std::mutex> lock(m_);
        return value_;
    }
private:
    mutable std::mutex m_;                      // mutable: const get() must lock
    int value_ = 0;
};

int main() {
    Counter c;
    std::vector<std::thread> ts;
    for (int i = 0; i < 4; ++i)
        ts.emplace_back([&c] { for (int k = 0; k < 50000; ++k) c.increment(); });
    for (auto& t : ts) t.join();
    std::printf("%d\n", c.get());
}
```

Output `200000` (g++ and clang++, `-O0`/`-O2`, clean under `-fsanitize=thread`). The mutex lives next to
the data it guards, is `mutable` so `const` readers can lock it, and no function hands out a pointer or reference to
`value_` (which would let callers bypass the lock).

`std::unique_lock` adds flexibility at a small cost (it stores an ownership flag):

```cpp title="unique_lock.cpp"
#include <cstdio>
#include <mutex>
#include <thread>

std::mutex m1, m2;

int main() {
    std::thread t([] {
        std::unique_lock a(m1, std::defer_lock);   // not locked yet
        std::unique_lock b(m2, std::defer_lock);
        std::lock(a, b);                           // locks both, deadlock-free
        std::puts("both held");
    });
    t.join();
    std::unique_lock lk(m1);
    std::printf("owns: %d\n", lk.owns_lock());
    lk.unlock();                                   // can release early
    std::printf("owns: %d\n", lk.owns_lock());
}
```

```text
both held
owns: 1
owns: 0
```

Other constructors: `std::try_to_lock` (try without blocking, check `owns_lock()`), `std::adopt_lock`
(take over a mutex already locked by this thread). Waiting on a condition variable requires a `unique_lock`
because the wait must unlock and relock; see [Condition variables](./06-condition-variables.md).

## Mutex types

| Type | Header / since | Property |
|---|---|---|
| `std::mutex` | `<mutex>` C++11 | Exclusive, non-recursive. The default. |
| `std::recursive_mutex` | C++11 | The owning thread may lock it again; must unlock the same number of times. |
| `std::timed_mutex`, `std::recursive_timed_mutex` | C++11 | Add `try_lock_for` / `try_lock_until`. |
| `std::shared_timed_mutex` | `<shared_mutex>` C++14 | Shared (many readers) or exclusive (one writer), with timed locking. |
| `std::shared_mutex` | `<shared_mutex>` C++17 | Same without the timed operations. |

Rules common to all of them: the mutex is neither copyable nor movable; it must not be destroyed while
locked; only the locking thread may unlock it. For a plain `std::mutex`, locking it again from the thread that holds it, or
unlocking it from another, is undefined behaviour (the standard allows a deadlock or an error, an implementation
is free to do anything).

**`std::recursive_mutex` is usually a design smell.** It exists for code where a locked member function calls
another locked member function. Prefer splitting into a public function that locks and a private one that
assumes the lock is held. It does work:

```cpp title="recursive.cpp"
#include <cstdio>
#include <mutex>

class Tree {
public:
    void a() { std::lock_guard<std::recursive_mutex> l(m_); b(); }   // b() locks again, same thread
    void b() { std::lock_guard<std::recursive_mutex> l(m_); std::puts("b"); }
private:
    std::recursive_mutex m_;
};

int main() { Tree().a(); }
```

**Timed locking** gives up after a deadline instead of blocking forever:

```cpp title="timed_mutex.cpp"
#include <chrono>
#include <cstdio>
#include <mutex>
#include <thread>

int main() {
    std::timed_mutex m;
    m.lock();                                         // main holds it
    std::thread t([&] {
        bool got = m.try_lock_for(std::chrono::milliseconds(20));
        std::printf("while held: %d\n", got);        // 0: timed out
    });
    t.join();
    m.unlock();
    std::thread u([&] {
        bool got = m.try_lock_for(std::chrono::milliseconds(20));
        std::printf("after unlock: %d\n", got);       // 1
        if (got) m.unlock();
    });
    u.join();
}
```

(Output: `while held: 0`, `after unlock: 1`; `try_lock_for` may block somewhat longer than the timeout.)
A plain `try_lock()` on any mutex is allowed to fail spuriously, so do not use its failure to conclude that another thread holds the lock.

### Reader-writer locking with `shared_mutex`

When reads vastly outnumber writes, `std::shared_mutex` allows many concurrent readers
(`std::shared_lock`) and one exclusive writer (`std::unique_lock` or `lock_guard`):

```cpp title="shared_mutex.cpp"
#include <cstdio>
#include <map>
#include <mutex>
#include <shared_mutex>
#include <string>
#include <thread>
#include <vector>

class Registry {
public:
    std::string lookup(int key) const {
        std::shared_lock lock(m_);                  // many readers at once
        auto it = map_.find(key);
        return it == map_.end() ? "?" : it->second;
    }
    void set(int key, std::string v) {
        std::unique_lock lock(m_);                  // exclusive writer
        map_[key] = std::move(v);
    }
private:
    mutable std::shared_mutex m_;
    std::map<int, std::string> map_;
};

int main() {
    Registry r;
    r.set(1, "one");
    std::vector<std::jthread> ts;
    ts.emplace_back([&] { for (int i = 0; i < 1000; ++i) r.set(2, "two"); });
    for (int i = 0; i < 3; ++i)
        ts.emplace_back([&] { for (int k = 0; k < 1000; ++k) (void)r.lookup(1); });
    ts.clear();                                      // jthreads join here
    std::printf("%s %s\n", r.lookup(1).c_str(), r.lookup(2).c_str());   // one two
}
```

A `shared_mutex` is more expensive per operation than a `std::mutex`, so it pays off only when the critical
section is long enough and reads dominate; measure it. There is no upgrade from shared to exclusive: release the shared lock and
take the exclusive one (and re-check, since the state may have changed). Whether writers can starve is
implementation-specific.

## Deadlock

A **deadlock** is a cycle of waiting: thread 1 holds A and waits for B while thread 2 holds B and waits for A.
Neither proceeds. The standard cause is taking several mutexes in different orders:

```cpp
// Fragment, not run: this can deadlock.
void f() { std::lock_guard a(m1); std::lock_guard b(m2); /* ... */ }
void g() { std::lock_guard a(m2); std::lock_guard b(m1); /* ... */ }   // opposite order
```

Ways out, in order of preference:

1. **Hold one lock at a time.** Copy what you need out of the critical section, release, then continue.
2. **Lock several mutexes in one call.** `std::scoped_lock lock(m1, m2)` (C++17) or `std::lock(m1, m2)` locks
   all of them using a deadlock-avoidance algorithm (the standard requires that no deadlock occurs; the
   algorithm itself is unspecified), regardless of the argument order at each call site.
3. **A fixed global lock order**, documented and enforced by code review, when the locks cannot be taken
   together.
4. **Do not call unknown code (callbacks, virtual functions) while holding a lock**; it may take locks you do not know about.

```cpp title="transfer.cpp"
#include <cstdio>
#include <mutex>
#include <thread>

struct Account {
    std::mutex m;
    long balance;
    explicit Account(long b) : balance(b) {}
};

// scoped_lock locks both with a deadlock-avoidance algorithm, regardless of argument order.
void transfer(Account& from, Account& to, long amt) {
    if (&from == &to) return;                       // locking the same std::mutex twice is UB
    std::scoped_lock lock(from.m, to.m);
    from.balance -= amt;
    to.balance += amt;
}

int main() {
    Account a(1000), b(1000);
    std::thread t1([&] { for (int i = 0; i < 10000; ++i) transfer(a, b, 1); });
    std::thread t2([&] { for (int i = 0; i < 10000; ++i) transfer(b, a, 1); });
    t1.join(); t2.join();
    std::printf("%ld %ld\n", a.balance, b.balance);   // 1000 1000
}
```

The two threads transfer in opposite directions, the classic deadlock setup, and the program finishes with
`1000 1000` every time (both compilers, `-O0`/`-O2`, no TSan reports).

## One-time initialization \{#one-time-initialization\}

For "do this exactly once, even with many threads arriving at once", don't write double-checked locking
with a hand-rolled flag (that is a common source of data races). Use:

- `std::call_once(std::once_flag, f, args...)`: the first caller runs `f`, others block until it finishes;
  everything `f` did is visible to them afterwards. If `f` throws, the flag stays unset and another caller
  tries.
- A **function-local static** (C++11): initialization is thread-safe, as
  [Storage duration](../05-memory-and-object-lifetime/storage-duration.md) explains. This is the simplest option.

```cpp title="call_once.cpp"
#include <cstdio>
#include <mutex>
#include <thread>

std::once_flag flag;
int config = 0;

void init() { config = 99; std::puts("init ran"); }

struct Logger { Logger() { std::puts("Logger built"); } };
Logger& logger() {
    static Logger instance;        // C++11: initialized exactly once, thread-safe
    return instance;
}

int main() {
    std::thread a([] { std::call_once(flag, init); });
    std::thread b([] { std::call_once(flag, init); });
    a.join(); b.join();
    std::printf("%d\n", config);
    std::thread c([] { logger(); }), d([] { logger(); });
    c.join(); d.join();
}
```

Output: `init ran`, `99`, `Logger built`, each exactly once.

## Pitfalls

- **Returning references to guarded data** from a locked function lets callers use it after the lock is
  released. Return copies, or keep the access inside the class.
- **Locking granularity.** One big lock is simple but serializes everything; many fine locks risk deadlock.
  Start coarse and split only when contention is measured.
- **Holding a lock during slow operations** (I/O, sleeping, allocation-heavy work) blocks every other
  thread that wants it.
- **A mutex protects code only if all accesses use it.** One unlocked read elsewhere is still a
  [data race](./03-data-races.md).
- **Locking a temporary:** `std::lock_guard<std::mutex>(m);` (no variable name) creates and immediately
  destroys an unnamed lock, protecting nothing. Name the variable.
- **Spurious wake-ups and lost notifications** are a [condition variable](./06-condition-variables.md) topic, not a mutex one.
- **Never use `volatile` or a plain `bool` instead of a lock.**

## References

- [`std::mutex` and friends (cppreference)](https://en.cppreference.com/w/cpp/thread/mutex)
- [`std::lock_guard`, `std::scoped_lock`, `std::unique_lock`, `std::shared_lock` (cppreference)](https://en.cppreference.com/w/cpp/thread/lock_guard)
- [`std::call_once` (cppreference)](https://en.cppreference.com/w/cpp/thread/call_once)
- [Mutual exclusion, \[thread.mutex\]](https://eel.is/c++draft/thread.mutex)
