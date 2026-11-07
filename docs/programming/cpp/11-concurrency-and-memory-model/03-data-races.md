---
id: data-races
title: Data Races and Race Conditions
sidebar_label: Data Races
sidebar_position: 3
tags: [cpp, concurrency, data-races, race-conditions, undefined-behavior, threadsanitizer]
---

# Data Races and Race Conditions

Two different bugs share the word "race". A **data race** is a precise language-level term: it is
undefined behaviour. A **race condition** is a logic bug where the result depends on timing, and it can
exist in a program with no data race at all. This page is the canonical home for both definitions
and for finding them with ThreadSanitizer.

**Prerequisites:** [C++ memory model](./01-cpp-memory-model.md) (happens-before).

## What counts as a data race

The standard defines it in terms of the memory model: a program has a **data race** when two
*conflicting* actions in different threads are not ordered by happens-before. Conflicting means they
access the same memory location and at least one writes. (There is an exception for operations that are
all atomic.) Compare this with the usual folk definition: "two threads, one writes, no lock". The
standard's version is stricter: it does not matter whether the access happens to be one instruction or
whether the value "looks fine".

A program with a data race has **undefined behaviour** for the entire execution, not just that line:
the compiler is entitled to assume no race exists, so it may keep a value in a register, hoist a load
out of a loop, or split a write. See [Undefined behavior](../10-error-handling-and-safety/06-undefined-behavior.md)
for what UB permits.

```cpp title="racy_counter.cpp"
// RACE DEMO: undefined behaviour. Do not copy.
#include <cstdio>
#include <thread>

int counter = 0;                    // plain int shared by two threads

int main() {
    auto work = [] { for (int i = 0; i < 100000; ++i) ++counter; };
    std::thread a(work), b(work);
    a.join();
    b.join();
    std::printf("%d\n", counter);   // value is unspecified: the program has UB
}
```

The two `++counter` calls are conflicting accesses with no happens-before between them. Typical
hardware does the increment as load, add, store, so two threads can both load the same old value and one
update is lost, but that is just one thing UB may look like. Never rely on a particular outcome.

:::warning[Benign races do not exist]
"Only a statistics counter", "only a bool flag" and "the value is only ever 0 or 1" are all still undefined
behaviour. Compilers do exploit this: a plain `bool` polled in a loop can be hoisted so the loop never
exits. `volatile` is not a fix ([volatile](../12-low-level-and-platform/05-volatile.md)).
:::

### What does not race

- **Different memory locations.** Distinct objects, or distinct elements of an array, never race
  with each other, even when they share a cache line (that costs performance as false sharing, not
  correctness).
- **Read-only data.** Any number of threads may read an object nobody writes.
- **Accesses ordered by happens-before.** Thread creation, `join`, mutex lock/unlock, atomics with
  release/acquire, `promise`/`future`; see [the memory model](./01-cpp-memory-model.md#mutexes-and-thread-operations-are-synchronization-too).
- **Initialization of function-local statics** (C++11) and `std::call_once`: one thread runs the initializer
  while others wait.

## Four ways to remove a data race

1. **Don't share.** Give each thread its own data and combine after `join`; a `thread_local`
   ([Storage duration](../05-memory-and-object-lifetime/storage-duration.md)) is one way.
2. **Share only immutable data.** `const` objects fully built before the threads start.
3. **Make the access atomic.** `std::atomic<T>` for a single variable ([Atomics](./02-atomics-and-fences.md)).
4. **Serialize with a lock.** [`std::mutex`](./05-mutexes.md) around everything that touches the shared state.

The first costs nothing at run time and is usually the best choice:

```cpp title="partial_sums.cpp"
#include <cstdio>
#include <thread>
#include <vector>

int main() {
    std::vector<long> partial(4, 0);
    std::vector<std::thread> ts;
    for (int t = 0; t < 4; ++t)
        ts.emplace_back([&partial, t] {
            for (int i = 0; i < 100000; ++i) ++partial[t];   // each thread owns one element
        });
    for (auto& th : ts) th.join();
    long total = 0;
    for (long p : partial) total += p;                       // read after join: ordered
    std::printf("%ld\n", total);
}
```

```text
400000
```

No race (distinct elements of a `std::vector<long>`, which the container rule above allows), the output is always `400000` (g++ and clang++, `-O0`/`-O2`, clean under
`-fsanitize=thread`). Adjacent `long`s do share a cache line, so this can be slow because of false
sharing; pad each element if it matters ([Alignment](../05-memory-and-object-lifetime/alignment.md#avoiding-false-sharing)).

### Standard containers

The library's rule ([container.reqmts], "Data races") is: member functions that only read, and a short list
that the standard treats as `const` for this purpose (`begin`, `end`, `rbegin`, `rend`, `front`, `back`, `data`,
`find`, `lower_bound`, `upper_bound`, `equal_range`, `at`, and `operator[]` except on associative and unordered
containers), may run concurrently. **Different elements of one container may be modified concurrently**, with the
exception of `std::vector<bool>`, whose elements share bytes. Anything that changes the container's structure
(`push_back`, `insert`, `erase`, `resize`, `reserve`, `clear`, `operator[]` on a map) is a data race with any
other access to the same container. Distinct containers are independent. The `push_back` pair below races on
size, capacity and the buffer:

```cpp title="racy_vector.cpp"
// RACE DEMO: undefined behaviour. Do not copy.
#include <thread>
#include <vector>

int main() {
    std::vector<int> v;
    std::thread a([&] { for (int i = 0; i < 1000; ++i) v.push_back(i); });
    std::thread b([&] { for (int i = 0; i < 1000; ++i) v.push_back(-i); });
    a.join(); b.join();
}
```

The fix is a mutex around every access, or one vector per thread merged after the join.

## Race conditions without a data race \{#race-conditions\}

A **race condition** means the outcome depends on how operations interleave. Making every access atomic
does not remove it if the *logic* spans several operations. Check-then-act is the classic form:

```cpp title="check_then_act.cpp"
#include <atomic>
#include <cstdio>
#include <mutex>
#include <thread>

// Race condition WITHOUT a data race: every access is atomic, but the logic is wrong.
struct BadAccount {
    std::atomic<int> balance{100};
    bool withdraw(int amt) {
        if (balance.load() >= amt) {        // check
            balance.fetch_sub(amt);         // act: another thread may have withdrawn in between
            return true;                    // so the balance can go negative
        }
        return false;
    }
};

// Fix 1: make check-and-act one atomic step.
struct CasAccount {
    std::atomic<int> balance{100};
    bool withdraw(int amt) {
        int cur = balance.load();
        while (cur >= amt) {
            if (balance.compare_exchange_weak(cur, cur - amt)) return true;
        }
        return false;
    }
};

// Fix 2: a mutex protects the whole invariant.
struct LockedAccount {
    bool withdraw(int amt) {
        std::lock_guard lock(m_);
        if (balance_ < amt) return false;
        balance_ -= amt;
        return true;
    }
    int balance() { std::lock_guard lock(m_); return balance_; }
private:
    std::mutex m_;
    int balance_ = 100;
};

int main() {
    CasAccount c;
    LockedAccount l;
    std::atomic<int> okc{0}, okl{0};
    auto work = [&] {
        for (int i = 0; i < 10; ++i) {
            if (c.withdraw(10)) okc.fetch_add(1);
            if (l.withdraw(10)) okl.fetch_add(1);
        }
    };
    std::thread a(work), b(work);
    a.join(); b.join();
    std::printf("%d %d | %d %d\n", okc.load(), c.balance.load(), okl.load(), l.balance());
}
```

```text
10 0 | 10 0
```

`BadAccount` is free of data races (TSan stays silent) yet wrong. Two threads can both pass the check
for the last 10 and drive the balance negative. The other two never do: exactly 10 withdrawals succeed
and the balance ends at 0 (g++ and clang++, `-O0`/`-O2`, no TSan reports). TSan finds data races, not
race conditions; for those you need tests that stress interleavings and careful review of every invariant that spans
more than one operation.

Other common race conditions: reading `size()` then indexing, `if (!queue.empty()) queue.pop()` across
threads, and acting on a `future`/flag that another thread may have changed. They are cured the same
way: make the check and the act one critical section.

## Finding races with ThreadSanitizer \{#finding-races-with-threadsanitizer\}

**ThreadSanitizer (TSan)** instruments memory accesses and synchronization at compile time and reports
a data race when it sees two conflicting accesses with no happens-before edge between them. It is
available in GCC and Clang (`-fsanitize=thread`), runs on 64-bit Linux, macOS and some other targets, and
cannot be combined with AddressSanitizer in one build. Expect a large slowdown and memory
increase (the Clang documentation quotes roughly 5x-15x time and 5x-10x memory; measure your own).

```bash
g++ -std=c++20 -O1 -g -fsanitize=thread -pthread racy_counter.cpp -o racy && ./racy
```

Run on the counter demo above, it prints a report whose shape (abridged, frames and addresses vary by
compiler and version) is:

```text
WARNING: ThreadSanitizer: data race
  Read of size 4 at 0x... by thread T2:
    #0 operator() racy_counter.cpp:8 ...
  Previous write of size 4 at 0x... by thread T1:
    #0 operator() racy_counter.cpp:8 ...
  Location is global 'counter' of size 4 at 0x... 
  Thread T1 (tid=..., finished) created by main thread at: ...
```

Read it as: the two accesses and their stacks, the memory location, and where each thread was created.
A race that depends on timing may need several runs or heavier workloads before TSan sees both accesses, and
TSan only reports races that actually occur in the run it observes, so absence of reports is not proof.

Notes from using it:

- Use `-O1 -g` for usable stack traces; TSan works at `-O2` too.
- Instrumenting only your code is not enough if a library you call is not instrumented: its internal locks
  appear as missing synchronization. Standard-library synchronization (mutex, atomics, `std::thread` join) is understood.
- It does not model standalone `std::atomic_thread_fence`; GCC warns and Clang can report a false race
  ([Atomics and fences](./02-atomics-and-fences.md#fences)).
- The other tool in this family is Valgrind's Helgrind/DRD, which needs no recompilation and is slower.

## Pitfalls

- **Assuming a data race is "just a stale value".** It is UB; the optimizer may transform the code in ways
  that have no interleaving explanation.
- **Atomic variables, non-atomic logic.** See race conditions above.
- **Sharing a lambda's reference captures.** `[&]` into a detached or long-lived thread shares (and may
  dangle). See [Threads](./04-threads.md).
- **Races on destruction.** One thread destroying an object while another uses it is a race on the whole
  object; ownership has to be settled before the threads start.

## References

- [Memory model, "Data races" (cppreference)](https://en.cppreference.com/w/cpp/language/memory_model)
- [Data races, \[intro.races\]](https://eel.is/c++draft/intro.races)
- [ThreadSanitizer (Clang documentation)](https://clang.llvm.org/docs/ThreadSanitizer.html)
