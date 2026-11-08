---
id: non-copyable
title: Non-Copyable
sidebar_label: Non-Copyable
sidebar_position: 4
tags: [c++, non-copyable, move-only, idioms, deleted-functions]
---

# Non-Copyable

A **non-copyable** type is one whose copies would be wrong: duplicating a file handle, a lock or a
unique owner either double-releases a resource or breaks an invariant. The idiom is to make the
mistake a compile error instead of a runtime bug. In modern C++ that is one line, `= delete`.

Which special members a class should declare, and the implicit-generation table that explains why
declaring one suppresses another, is owned by
[Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md#deleting-operations). This page is
the idiom: the forms, when each fits, and the pitfalls.

**Prerequisites:** [Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md),
[Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md), [RAII](./01-raii.md).

## When a type should not be copyable

- It owns a resource with a single owner: a file descriptor, a socket, a heap object (`unique_ptr`).
- Its identity is its address or registration: a mutex, an atomic, an object registered in a table
  by pointer.
- Copying has no sensible meaning: a thread, a scope guard.

If copies *can* be made meaningful (deep copy, reference count), prefer that and keep the type a
value. Make the type non-copyable when no copy semantics are correct, not merely because copying is
expensive; an expensive copy can be left available and made visible with an explicit `clone()`.

## The three forms

```cpp title="nc.cpp" showLineNumbers
#include <cstdio>
#include <mutex>
#include <type_traits>
#include <utility>

struct Handle {                            // move-only: deleting the copies is enough
    Handle() = default;
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
    Handle(Handle&&) noexcept { std::puts("moved"); }
    Handle& operator=(Handle&&) noexcept = default;
};

struct Pinned {                            // neither copyable nor movable
    Pinned() = default;
    Pinned(Pinned&&) = delete;             // deleting the move ctor also suppresses the copies
    Pinned& operator=(Pinned&&) = delete;
};

struct Holder {                            // rule of zero: the member decides
    std::mutex m;
    int n = 0;
};

Pinned make() { return Pinned{}; }         // C++17: the prvalue initializes the result directly

struct NonCopyableBase {
protected:
    NonCopyableBase() = default;
    ~NonCopyableBase() = default;
    NonCopyableBase(const NonCopyableBase&) = delete;
    NonCopyableBase& operator=(const NonCopyableBase&) = delete;
};
struct Derived : private NonCopyableBase { int x = 1; };

static_assert(!std::is_copy_constructible_v<Handle> && std::is_move_constructible_v<Handle>);
static_assert(!std::is_copy_constructible_v<Pinned> && !std::is_move_constructible_v<Pinned>);
static_assert(!std::is_copy_constructible_v<Holder> && !std::is_move_constructible_v<Holder>);
static_assert(!std::is_copy_constructible_v<Derived>);

int main() {
    Handle a;
    Handle b = std::move(a);
    Pinned p = make();
    (void)b; (void)p;
}
```

Output with g++ 15 and clang++ 21, `-std=c++20 -Wall -Wextra`, `-O0` and `-O2`: `moved` (once).
All the `static_assert`s hold.

### 1. Delete the copies: move-only

`Handle` above. The deleted copy operations make the type move-only, and a user-declared copy
operation already suppresses the implicit moves, so write the moves yourself (or `= default` them).
This is the form for owning handles; `unique_ptr`, `std::thread`, `std::fstream` and
`std::unique_lock` are move-only in the standard library.

Using a deleted function is an error at the call site, with the function named:

```text
error: use of deleted function 'H::H(const H&)'          (g++ 15)
error: call to deleted constructor of 'H'                 (clang++ 21)
```

Convention is to declare deleted functions `public`, where the intent is visible in the class
interface. Both compilers above report a deleted function as deleted even when it is declared `private`,
so access does not change the message.

### 2. Delete the moves: non-copyable and non-movable

`Pinned`. Deleting the move constructor is enough, because a user-declared move constructor causes
the copy operations to be implicitly deleted (see the table in
[Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md#implicit-generation-rules)).
Use it for types that must stay at one address (mutexes, atomics, self-registering objects).

Since C++17, guaranteed copy elision means a function can still *return* such an object by prvalue,
as `make()` does, because no move or copy is involved. A named local (`Pinned p; return p;`) cannot be
returned; see [copy elision](../07-classes-and-oop/copy-and-move-semantics.md#copy-elision).

Do not delete only the copies "to be safe" and then rely on the move for a type whose address
matters; that makes it movable.

### 3. Let a member decide (rule of zero)

`Holder` declares nothing. Its `std::mutex` member is non-copyable and non-movable, so the
implicitly generated copy and move operations of `Holder` are defined as deleted. That is usually the
best way to get a non-copyable class: write no special members and let a member's type carry the
property. It is also the reason a class can silently become non-copyable after a member changes;
a `static_assert(!std::is_copy_constructible_v<T>)` documents the intent.

## The base-class variant

`NonCopyableBase` (the old `boost::noncopyable` shape) puts the deleted operations in a base so any
class gets them by inheriting. It dates from before `= delete` (C++11), when the only way to block copying was a
private, undefined copy constructor. Today it saves a few lines per class at a cost:

- It must be inherited **privately**, or `Derived*` converts to `NonCopyableBase*` publicly for no reason.
- The base's constructor and destructor should be `protected` and non-virtual so it cannot be used
  as a standalone type or deleted through.
- Whether an empty base adds to `sizeof` depends on the empty base optimization: a single empty base
  usually costs nothing, but the rule is ABI- and layout-dependent (see
  [class layout](../07-classes-and-oop/class-layout.md)).

Prefer the explicit `= delete` lines: they are local, greppable and have no ABI footprint.

## Pitfalls

- **Declaring a destructor and expecting deletion.** A user-declared destructor does not delete the
  copy operations (their implicit generation is deprecated, not removed), so an owning class that
  forgets to delete them is silently copyable and double-frees. Delete or define them.
- **Containers.** `std::vector` growth needs the element type to be move-insertable (even for
  `emplace_back`), so a non-movable type cannot live in a `vector`; use `std::deque`, `std::list` or
  a vector of `unique_ptr`. For a movable type, mark the moves `noexcept` so reallocation moves rather
  than copies ([why](../07-classes-and-oop/copy-and-move-semantics.md#why-move-operations-should-be-noexcept)).
- **Passing by value.** A move-only parameter type forces callers to write `std::move`, which is the
  desired ownership signal. A non-movable type cannot be passed by value from an lvalue (only from a prvalue, C++17); take a reference.
- **Singletons are not an excuse.** Deleting the copies of a singleton prevents duplicates, but a
  global instance is a design choice with its own costs; the idiom is separate from it.

## Related

- [Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md): why declaring one special member affects the others.
- [RAII](./01-raii.md): the usual reason a type is move-only.
- [Copy-and-Swap](./05-copy-and-swap.md): the other branch, when copies are allowed and must be exception-safe.
- [`unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md): the standard move-only owner.

## References

- [cppreference: Deleted functions](https://en.cppreference.com/w/cpp/language/function#Deleted_functions)
- [cppreference: Copy elision](https://en.cppreference.com/w/cpp/language/copy_elision)
- [C++ Core Guidelines: C.81, C.67](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c81-use-delete-when-you-want-to-disable-default-behavior-without-wanting-an-alternative)
