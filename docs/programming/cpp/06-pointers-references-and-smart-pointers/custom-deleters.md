---
id: custom-deleters
title: Custom Deleters
sidebar_label: Custom Deleters
sidebar_position: 8
tags: [c++, smart-pointers, deleters, unique-ptr, shared-ptr, raii, resource-management]
---

# Custom Deleters

A smart pointer's job is "run cleanup when the last owner goes away", and the default cleanup is
`delete` (or `delete[]` for arrays). A **deleter** replaces that step. It lets
[`unique_ptr`](./unique-ptr.md) and [`shared_ptr`](./shared-ptr.md) manage anything with an
acquire/release pair: a `FILE*` closed with `fclose`, memory from `malloc`, a C library handle, an
object that must be returned to a pool, or an object owned by someone else that must not be freed at
all. This page is the canonical home for how deleters work in both pointers.

**Prerequisites:** [unique_ptr](./unique-ptr.md), [shared_ptr](./shared-ptr.md) (control block),
[RAII](../13-idioms-and-design/01-raii.md).

## What a deleter is

A deleter is any callable that can be invoked with the managed pointer: a function, function
pointer, functor, or lambda. The smart pointer calls `deleter(ptr)` instead of `delete ptr`. The
callable should not throw, since it runs in a destructor.

```cpp title="file-closer.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct FileCloser {
    void operator()(std::FILE* f) const noexcept {
        std::puts("fclose");
        std::fclose(f);
    }
};

int main() {
    std::unique_ptr<std::FILE, FileCloser> f(std::fopen("/dev/null", "w"));
    if (!f) return 1;
    std::fputs("hello", f.get());
}   // FileCloser{}(f.get()) runs here, on every path out of main
```

```text
fclose
```

The same with a lambda needs the lambda's type, which is only nameable through `decltype`:

```cpp title="lambda-deleter.cpp" showLineNumbers
#include <cstdio>
#include <cstdlib>
#include <memory>

int main() {
    auto closer = [](std::FILE* f) { std::fclose(f); };
    std::unique_ptr<std::FILE, decltype(closer)> f(std::fopen("/dev/null", "w"), closer);

    // C allocation: free(), not delete
    std::unique_ptr<int, decltype(&std::free)> buf(
        static_cast<int*>(std::malloc(4 * sizeof(int))), &std::free);
    if (f && buf) buf.get()[0] = 1;
}
```

`decltype(&std::free)` is a function pointer type. Taking the address of a standard-library
function is formally unspecified (the library may add overloads), though it works with every major
implementation for `std::free` and `std::fclose`. A small functor like `FileCloser` avoids the
question and is also the smaller object (next section).

## `unique_ptr`: the deleter is part of the type

`unique_ptr<T, D>` has the deleter type `D` as a template parameter and stores a `D` object inside
the pointer. Consequences:

- **Different `D` means a different type.** `unique_ptr<FILE, FileCloser>` cannot be assigned to
  `unique_ptr<FILE, decltype(&fclose)>`. The type tells readers (and the compiler) how it will be
  cleaned up.
- **No allocation, and often no space.** A stateless functor or captureless lambda adds nothing to
  `sizeof` in libstdc++ and libc++ (they use an empty-base or `[[no_unique_address]]` layout, not
  required by the standard). A function-pointer deleter or one with captures adds that state.
- **The deleter is invoked only if the stored pointer is non-null.**
- **The deleter is moved with the pointer.** Move construction and assignment move it too.

```cpp title="sizes.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct Stateless { void operator()(int* p) const { delete p; } };
struct Counting  { long* counter; void operator()(int* p) const { ++*counter; delete p; } };

// libstdc++ and libc++ on 64-bit; the standard does not guarantee these sizes.
static_assert(sizeof(std::unique_ptr<int>) == sizeof(void*));
static_assert(sizeof(std::unique_ptr<int, Stateless>) == sizeof(void*));
static_assert(sizeof(std::unique_ptr<int, void (*)(int*)>) == 2 * sizeof(void*));
static_assert(sizeof(std::unique_ptr<int, Counting>) == 2 * sizeof(void*));

int main() {
    long freed = 0;
    {
        std::unique_ptr<int, Counting> a(new int(1), Counting{&freed});
        auto b = std::move(a);                  // deleter moves along
    }
    std::printf("freed %ld\n", freed);
}
```

```text
freed 1
```

### Non-pointer handles with `pointer`

Many C APIs hand out handles that are not pointers: file descriptors, GL object names, `HANDLE`s. If
the deleter type has a member typedef `pointer`, `unique_ptr` stores *that* type instead of `T*`.
The type must satisfy **NullablePointer**: default-constructible to a "null" value, comparable with
`nullptr`, and contextually convertible to `bool`. `unique_ptr<T, D>`'s `get()`, `reset()` and
`release()` then speak in that type.

```cpp title="handle.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>
#include <memory>

// A fake C API: handles are small integers, 0 means "none".
using RawHandle = unsigned;
RawHandle api_open()            { return 7; }
void      api_close(RawHandle h) { std::printf("api_close(%u)\n", h); }

// A NullablePointer wrapper for the handle.
struct Handle {
    RawHandle v = 0;
    Handle() = default;
    Handle(RawHandle h) : v(h) {}
    Handle(std::nullptr_t) {}
    explicit operator bool() const { return v != 0; }
    friend bool operator==(Handle a, Handle b) { return a.v == b.v; }
};

struct HandleCloser {
    using pointer = Handle;                      // unique_ptr stores a Handle, not Handle*
    void operator()(Handle h) const { api_close(h.v); }
};

using UniqueHandle = std::unique_ptr<RawHandle, HandleCloser>;   // T is just a tag here

int main() {
    UniqueHandle h(api_open());
    std::printf("open: %u\n", h.get().v);
    UniqueHandle empty;                          // null: deleter never runs
}
```

```text
open: 7
api_close(7)
```

Writing the wrapper is the cost of using a non-pointer handle with `unique_ptr`. For one-off cases a
small dedicated RAII class (see [RAII](../13-idioms-and-design/01-raii.md)) is often clearer. The
Library Fundamentals TS v3 has `std::experimental::unique_resource` for this, but it isn't in the standard as of C++23.

## `shared_ptr`: the deleter is erased

`shared_ptr` takes the deleter as a **constructor argument** and stores it, type-erased, in the
control block. It is not a template parameter, so:

- `shared_ptr<FILE>` has one type regardless of how it closes the file.
- Different deleters can live behind the same type, as in a container of `shared_ptr<Resource>`.
- Storing the deleter costs nothing in the `shared_ptr` object itself (it is two pointers), and
  adds to the control block instead. A deleter with state makes that block bigger.
- The deleter is moved/copied into the control block once. Copies of the `shared_ptr` share it.
- **The deleter is called even if the stored pointer is null**, whenever the
  `shared_ptr` was *constructed* with one. That differs from `unique_ptr`. A deleter that cannot
  handle `nullptr` must check.
- If the constructor throws (for example, the control block allocation fails), `d(ptr)` is called
  first, so the resource is not leaked.
- The deleter can be retrieved with `std::get_deleter<D>(sp)`, which returns `nullptr` if the
  stored deleter is not of type `D`.

```cpp title="shared-deleter.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct Conn { int id; };

void close_conn(Conn* c) {
    std::printf("close_conn(%s)\n", c ? "non-null" : "nullptr");
    delete c;                                    // delete on nullptr is a no-op
}

int main() {
    std::shared_ptr<Conn> a(new Conn{1}, close_conn);
    std::shared_ptr<Conn> b = a;                 // shares the deleter; same type either way

    std::shared_ptr<Conn> c(nullptr, close_conn);   // null pointer, but the deleter is stored
    std::unique_ptr<Conn, void (*)(Conn*)> u(nullptr, close_conn);   // deleter will NOT run

    auto lambda = std::shared_ptr<Conn>(new Conn{2}, [](Conn* p) {
        std::puts("lambda deleter");
        delete p;
    });                                          // still std::shared_ptr<Conn>
    a = lambda;                                  // different deleters, assignable
    std::puts("end");
}
```

```text
end
close_conn(nullptr)
close_conn(non-null)
lambda deleter
```

<Walkthrough title="Who runs which deleter" caption="Follow the strong count of each control block through main." accent="blue">
  <Step title="a and b share one block">

`a` and `b` share the control block with <StepChange label="deleter">`close_conn`</StepChange> and strong count 2. `c` has its own block, holding a null pointer and `close_conn`. `lambda` has a third block with the lambda deleter.

  </Step>
  <Step title="Assigning a = lambda">

`a` releases its share of the first block, whose count goes <StepChange>2 to 1</StepChange> (`b` still owns it), then shares `lambda`'s block (count 2). No deleter runs.

  </Step>
  <Step title="End of main: reverse declaration order">

Destruction order is `lambda`, `u`, `c`, `b`, `a`. `lambda` only drops the lambda block from 2 to 1. `u` holds a null pointer, so its deleter does not run. `c`'s block reaches 0, so `close_conn(nullptr)` runs. `b` was the last owner of the first block, so `close_conn(non-null)` runs. `a` is the last owner of the lambda block, so "lambda deleter" prints last.

  </Step>
</Walkthrough>

## Comparison

| | `unique_ptr<T, D>` | `shared_ptr<T>` |
|---|---|---|
| Where the deleter is given | template argument (and constructor, unless default-constructible) | constructor argument only |
| Part of the type | yes | no |
| Where it is stored | inside the pointer object | in the control block |
| Cost of a stateless deleter | zero (common implementations) | none beyond the control block |
| Called for a null pointer | no | yes, if constructed with it |
| Non-pointer handles (`pointer` typedef) | supported | not supported: needs a pointer |
| Works with `make_*` | `make_unique` uses the default deleter only | `make_shared` uses the default only |
| Retrieve it | `p.get_deleter()` | `std::get_deleter<D>(sp)` |

Converting `unique_ptr<T, D>` to `shared_ptr<T>` (by move) keeps the deleter, so a factory can return
a `unique_ptr` with a specific deleter and let the caller decide whether to share it.

## Useful deleters

**Pool return.** The deleter hands the object back instead of destroying it.

```cpp title="pool.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <vector>

struct Buffer { char data[64]; };

class Pool {
    std::vector<Buffer*> free_;
public:
    struct Return {
        Pool* pool;
        void operator()(Buffer* b) const { pool->free_.push_back(b); }   // recycle, don't delete
    };
    using Handle = std::unique_ptr<Buffer, Return>;

    Handle acquire() {
        Buffer* b;
        if (free_.empty()) { b = new Buffer; }
        else { b = free_.back(); free_.pop_back(); }
        return Handle(b, Return{this});
    }
    std::size_t idle() const { return free_.size(); }
    ~Pool() { for (Buffer* b : free_) delete b; }
};

int main() {
    Pool pool;                                   // must outlive every Handle
    { auto h = pool.acquire(); }                 // returned to the pool on scope exit
    std::printf("idle %zu\n", pool.idle());
    { auto h = pool.acquire(); }                 // reuses the same Buffer
    std::printf("idle %zu\n", pool.idle());
}
```

```text
idle 1
idle 1
```

**Arrays.** `unique_ptr<T[]>` already uses `delete[]`. For a `shared_ptr` of an array, use the
`T[]` specialization *(C++17)*, or pass `std::default_delete<T[]>{}` explicitly. A bare
`shared_ptr<T>(new T[n])` calls scalar `delete`: undefined behavior.

**Unlock, close, release.** Any "undo" step fits, but if the only goal is "run this at scope exit",
a dedicated scope guard or `std::lock_guard` states the intent better than a smart pointer with a
fake pointee.

**No-op deleter for non-owned objects.** `shared_ptr<T>(&obj, [](T*){})` adapts a stack or global
object to an API that wants a `shared_ptr`. It works, but it hides a lifetime hazard (the
`shared_ptr` can outlive `obj`), so prefer changing the API to take `T&` or `T*`.

## `std::default_delete`

`std::default_delete<T>` is the deleter `unique_ptr<T>` uses: it calls `delete`.
`default_delete<T[]>` calls `delete[]`. It is stateless, so it costs nothing. Both make `operator()`
ill-formed for an incomplete type (libstdc++ and libc++ use a `static_assert`), which is why a pimpl class must define its destructor
where the type is complete (see [unique_ptr](./unique-ptr.md#incomplete-types-and-the-pimpl-idiom)).
It also converts: `default_delete<Derived>` converts to `default_delete<Base>`, which is what lets
`unique_ptr<Derived>` convert to `unique_ptr<Base>` (and is also why that needs a virtual destructor).

## Pitfalls

- **Throwing from a deleter.** It runs in a destructor, which is `noexcept` by default; the program
  terminates. Report errors some other way (for example log, since `fclose` can fail but the caller
  usually can't act).
- **Deleter outliving its data.** A deleter that captures a pointer or reference (the pool above)
  requires that thing to outlive every smart pointer using it.
- **Mismatched cleanup.** Pointing a default-deleter `unique_ptr` at `malloc` memory or at a
  `new[]` array. Give the pointer the matching deleter or use the array form.
- **Assuming `shared_ptr` skips null.** It doesn't if built with a deleter. Check inside the
  deleter.
- **Stateful deleters in `unique_ptr`** make the pointer larger, and make two `unique_ptr`s of the
  same `T` and `D` assignable only if the deleter itself is.
- **Expecting `make_shared` / `make_unique` to take a deleter.** They don't. Build the pointer
  directly from the raw pointer.

## Key points

- A deleter replaces `delete`: it turns `unique_ptr` and `shared_ptr` into general RAII holders.
- `unique_ptr<T, D>`: deleter in the type and in the object; free if stateless; skipped for null.
- `shared_ptr<T>`: deleter given at construction, type-erased in the control block; called even for null.
- The `pointer` typedef lets `unique_ptr` hold non-pointer handles.
- Deleters must not throw, and anything they capture must outlive the owners.

## Related

- [unique_ptr](./unique-ptr.md): sole ownership, `release`, passing and returning.
- [shared_ptr](./shared-ptr.md): the control block that stores the deleter.
- [RAII](../13-idioms-and-design/01-raii.md): the idiom, and when a dedicated class beats a smart pointer.
