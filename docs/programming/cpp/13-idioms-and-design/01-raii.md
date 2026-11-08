---
id: raii
title: RAII
sidebar_label: RAII
sidebar_position: 1
tags: [c++, raii, idioms, resource-management, exception-safety]
---

# RAII

**RAII** (Resource Acquisition Is Initialization) ties a resource's lifetime to an object's: the
constructor acquires it, the destructor releases it. C++ guarantees the destructor of a fully
constructed automatic object runs when its scope exits, by `return`, `break`, `goto` or a thrown
exception alike, so the cleanup cannot be skipped. This is the idiom that replaces `finally`,
cleanup labels and `try/catch` ladders in C++.

The language rules behind it are owned elsewhere: when destructors run in
[storage duration](../05-memory-and-object-lifetime/storage-duration.md), stack unwinding and
partially constructed objects in [constructors and destructors](../07-classes-and-oop/constructors-and-destructors.md#exceptions-during-construction).
This page is about how to design the wrapper.

**Prerequisites:** [Constructors and Destructors](../07-classes-and-oop/constructors-and-destructors.md),
[Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## The problem: cleanup on every exit path

```cpp title="Fragment: manual cleanup"
void process() {
    std::FILE* f = std::fopen("data.txt", "r");
    if (!f) return;
    if (!parse(f)) return;          // leak: fclose skipped
    use(f);                          // may throw: fclose skipped
    std::fclose(f);
}
```

Every new `return` or call that can throw is another path where the release must be repeated. The
bug is not any single line; it is that correctness depends on the programmer remembering at every
exit.

## The idiom

Wrap the resource in a class whose destructor releases it:

```cpp title="file_guard.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>
#include <utility>

class File {
public:
    File(const char* path, const char* mode) : f_(std::fopen(path, mode)) {
        if (!f_) throw std::runtime_error("cannot open file");   // acquisition failed: no object
        std::puts("open");
    }
    ~File() {
        if (f_) { std::fclose(f_); std::puts("close"); }
    }
    File(File&& o) noexcept : f_(std::exchange(o.f_, nullptr)) {}
    File& operator=(File&& o) noexcept {
        if (this != &o) {
            if (f_) std::fclose(f_);
            f_ = std::exchange(o.f_, nullptr);
        }
        return *this;
    }                                        // user-declared moves delete the copies
    std::FILE* get() const { return f_; }

private:
    std::FILE* f_;
};

void work(bool fail) {
    File f("/dev/null", "r");
    if (fail) throw std::runtime_error("work failed");
    std::puts("work done");
}

int main() {
    work(false);
    try { work(true); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
    try { File g("/no/such/file", "r"); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
}
```

Output (g++ 15 and clang++ 21, `-std=c++20`, `-O0` and `-O2` identical):

```text
open
work done
close
open
close
caught: work failed
caught: cannot open file
```

Note the order in the middle: `close` prints before `caught`, because the destructor runs during
stack unwinding, before the handler. The third call never prints `close`: if the constructor
throws, no object exists and no destructor runs, which is why the constructor must either finish
acquiring or leave nothing acquired.

### What a well-formed RAII class needs

1. **Acquire in the constructor, throw on failure.** An object that exists is a valid, owning
   object. Avoid a "constructed but empty, check `is_open()`" state unless the empty state is
   needed anyway, as it is for a moved-from object.
2. **Release in the destructor, and never throw from it.** A destructor is implicitly `noexcept`
   (C++11), so an escaping exception calls `std::terminate`. Swallow or log errors that cannot be
   handled (`fclose` can fail on a buffered write; if the caller needs to know, give the class an
   explicit `close()` that reports errors, and let the destructor be the fallback).
3. **Decide copy and move.** Sole ownership means non-copyable and, usually, movable. That is the
   [rule of five](../07-classes-and-oop/rule-of-zero-three-five.md) applied to a handle;
   [Non-Copyable](./04-non-copyable.md) covers the options. If copies would have to share the
   resource, use reference counting ([`shared_ptr`](../06-pointers-references-and-smart-pointers/shared-ptr.md))
   instead of inventing it.
4. **One resource per class.** A class that owns two raw resources leaks the first if acquiring the
   second throws. Give each its own wrapper and compose them; then the compiler-generated members
   are correct (rule of zero).

## Prefer existing wrappers

Most RAII classes you need already exist:

| Resource | Standard wrapper |
|---|---|
| Heap object | [`std::unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md), `std::shared_ptr` |
| Heap array | `std::vector`, `std::array`, `std::unique_ptr<T[]>` |
| Mutex ownership | `std::lock_guard`, `std::unique_lock`, `std::scoped_lock` (C++17) |
| File stream | `std::fstream` family (closes on destruction) |
| Thread | `std::jthread` (C++20) joins on destruction; a joinable `std::thread` destructor calls `std::terminate` |
| Any C handle | `unique_ptr` with a [custom deleter](../06-pointers-references-and-smart-pointers/custom-deleters.md) |

A `unique_ptr` with a custom deleter is the shortest way to wrap a C handle whose release is one
function call. Write a dedicated class (like `File` above) when the handle needs more than release:
extra operations, a non-pointer handle type, or an error-reporting `close()`.

## Scope guards: cleanup without a resource type

Sometimes the "resource" is an action: roll back a half-done operation, restore a flag. A small
template runs a callable on scope exit and can be disarmed on success:

```cpp title="guard.cpp" showLineNumbers
#include <cstdio>
#include <utility>

template <typename F>
class ScopeGuard {
public:
    explicit ScopeGuard(F f) : f_(std::move(f)) {}
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;
    ~ScopeGuard() { if (active_) f_(); }
    void dismiss() noexcept { active_ = false; }

private:
    F f_;
    bool active_ = true;
};

bool transfer(bool ok) {
    ScopeGuard rollback([] { std::puts("rollback"); });   // CTAD deduces F (C++17)
    std::puts("step 1");
    if (!ok) return false;               // early return: rollback runs
    std::puts("step 2");
    rollback.dismiss();                  // success: commit
    return true;
}

int main() {
    transfer(true);
    transfer(false);
}
```

```text
step 1
step 2
step 1
rollback
```

The callable passed to a guard must not throw, for the same reason a destructor must not. The
standard has no scope guard in C++23. `std::experimental::scope_exit` (Library Fundamentals TS v3,
`<experimental/scope>`) is shipped by libstdc++ but not by MSVC's STL, so portable code writes the
template above or uses a library one.

## What RAII does not cover

- **Cycles and shared state.** RAII handles ownership by scope. Objects that outlive any one scope
  need an owner decision, and `shared_ptr` cycles leak; see [`weak_ptr`](../06-pointers-references-and-smart-pointers/weak-ptr.md).
- **Failed release.** A destructor cannot report failure. Provide an explicit fallible `close()`
  or `commit()` when failure matters (transactions are the classic case: the destructor rolls back
  unless `commit()` ran).
- **`std::exit` and `std::abort`.** `exit` destroys static-duration objects but not locals of the
  calling frames; `abort` and a call to `std::terminate` destroy nothing. RAII guarantees cleanup
  on normal and exceptional scope exit only.
- **Uncaught exceptions.** If no handler is found, whether the stack is unwound before
  `std::terminate` is implementation-defined, so do not rely on destructors running there.

## Pitfalls

- **Unnamed temporaries.** `std::lock_guard<std::mutex>{m};` creates a temporary that is destroyed at
  the semicolon, so the lock is released at once. (Without braces, `std::lock_guard<std::mutex>(m);`
  parses as a declaration of a variable named `m`.) Name the guard: `std::lock_guard lock(m);`.
- **Handing the raw handle out.** `get()` is fine for passing to a C API; storing it beyond the
  wrapper's lifetime reintroduces dangling handles.
- **Copying a handle by accident.** A wrapper with a raw-handle member and no declared copy
  operations is copyable, and both copies release the same resource. Delete or define the copies.
- **Throwing destructors.** See above; they terminate.

## Related

- [`unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md): RAII for heap objects, the model every wrapper copies.
- [Copy-and-Swap](./05-copy-and-swap.md): writing the assignment operator of an owning class.
- [Exceptions](../10-error-handling-and-safety/01-exceptions.md): what unwinding does and why RAII makes it safe.

## References

- [cppreference: RAII](https://en.cppreference.com/w/cpp/language/raii)
- [cppreference: `std::jthread`](https://en.cppreference.com/w/cpp/thread/jthread)
- [C++ Core Guidelines: E.6, R.1](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#e6-use-raii-to-prevent-leaks)
