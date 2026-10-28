---
id: placement-new
title: Placement new and std::launder
sidebar_label: Placement new
sidebar_position: 6
tags: [c++, placement-new, construct-at, launder, memory, advanced]
---

# Placement new and `std::launder`

**Placement new** constructs an object in storage you already have. It does no allocation. It is how
`std::vector` constructs elements in spare capacity, how `std::optional` holds an object that may or
may not exist, and how memory pools hand out objects. Once you construct objects yourself, you also
destroy them yourself, and you have to follow the rules for reusing storage, which is where
`std::launder` comes in.

**Prerequisites:** [Object lifetime](./object-lifetime.md), [new and delete](./new-and-delete.md),
[alignment](./alignment.md).

## Syntax

```cpp title="basic.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <new>
#include <string>

int main() {
    alignas(std::string) unsigned char buf[sizeof(std::string)];   // size and alignment

    std::string* s = ::new (buf) std::string("hello");   // construct only
    std::printf("%s\n", s->c_str());
    s->~basic_string();                                  // destroy only; never `delete s`

    std::string* t = std::construct_at(reinterpret_cast<std::string*>(buf), "again");  // C++20
    std::printf("%s\n", t->c_str());
    std::destroy_at(t);                                  // C++17
}
```

Output:

```text
hello
again
```

- `new (p) T(args)` calls the non-allocating `operator new(std::size_t, void*)` from `<new>`, which
  just returns `p`, then runs the constructor. Writing `::new` makes sure a class-specific
  `operator new` is not picked up instead.
- `std::construct_at(p, args...)` *(C++20)* does the same thing, can be used in `constexpr`
  evaluation, and is what library code uses now.
- Destroy with an explicit destructor call `p->~T()` or `std::destroy_at(p)` *(C++17)*. A
  pseudo-destructor call on a type alias works for any type, including `int`: `using T = int;
  p->~T();`.

## The storage requirements

The storage must be:

- **large enough**: at least `sizeof(T)` bytes;
- **suitably aligned**: the address is a multiple of `alignof(T)`. A plain `char buf[sizeof(T)]` has
  alignment 1, so always write `alignas(T)`;
- **not holding a live object you still need**. Constructing over an object ends its lifetime
  without running its destructor. That is allowed, but whatever the destructor would have done
  (free memory, unlock) does not happen.

The buffer should be an array of `unsigned char` or `std::byte`. Those are the types the standard
says can *provide storage* for other objects. A `char` array may not, since CWG 2489.

## Allocation and construction, separately

The usual reason to use placement new is to allocate once and construct many times. The walkthrough
traces a two-slot buffer the way `std::vector` uses its capacity.

```cpp title="slots.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <new>

struct Item {
    int id;
    explicit Item(int i) : id(i) { std::printf("Item(%d)\n", id); }
    ~Item() { std::printf("~Item(%d)\n", id); }
};

int main() {
    void* raw = ::operator new(2 * sizeof(Item));        // storage for 2, no objects
    Item* slots = static_cast<Item*>(raw);

    std::construct_at(slots + 0, 10);
    std::construct_at(slots + 1, 20);

    std::destroy_at(slots + 0);                          // free slot 0 again
    std::construct_at(slots + 0, 30);                    // reuse its storage

    std::destroy(slots, slots + 2);                      // destroy both (C++17)
    ::operator delete(raw);                              // then release the storage
}
```

<Walkthrough title="Two slots, three objects" caption="Output of slots.cpp, g++ 15 and clang++ 21." accent="green">
  <Step title="Storage only">

`::operator new(2 * sizeof(Item))` returns 8 bytes. Both slots are <StepChange>empty</StepChange>:
no `Item` exists, and nothing prints.

  </Step>
  <Step title="Construct 10 and 20">

```text
Item(10)
Item(20)
```

`construct_at` starts the lifetime of an `Item` in each slot: <StepChange>`[10][20]`</StepChange>.

  </Step>
  <Step title="Destroy slot 0">

```text
~Item(10)
```

The first object's lifetime ends. Slot 0 is <StepChange>storage again</StepChange>: `[--][20]`.
`slots[0]` must not be used now.

  </Step>
  <Step title="Reuse slot 0">

```text
Item(30)
```

A new `Item` is created in the same storage: <StepChange>`[30][20]`</StepChange>. `slots + 0`
points to the new object, because the old one is transparently replaceable (see below).

  </Step>
  <Step title="Tear down">

```text
~Item(30)
~Item(20)
```

`std::destroy(first, last)` destroys in order from first to last. Only after all lifetimes have
ended does `::operator delete` <StepChange>release the storage</StepChange>. Calling `delete slots`
instead would be undefined behavior: the memory came from `::operator new`, not from a
`new`-expression for an `Item`.

  </Step>
</Walkthrough>

For arrays, call the construct-in-a-loop helpers in `<memory>` instead of array placement new
(`new (buf) T[n]`): `std::uninitialized_default_construct_n`, `std::uninitialized_value_construct_n`,
`std::uninitialized_copy`, and `std::destroy_n`. They also destroy what was already built if a
constructor throws. (Array placement new was once allowed to need extra space for an element count;
CWG 2382 removed that, but older MSVC versions still did it.)

## `std::launder` *(C++17)*

When you create a new object in storage that held another object, can you keep using the old
pointers? The rule is in [basic.life]: old pointers, references and names automatically refer to the
new object if the old object is **transparently replaceable** by the new one, which means:

- the new object occupies exactly the same storage;
- it has the same type (ignoring top-level `const`/`volatile`);
- the old object was not a complete `const` object;
- neither is a base-class subobject or a `[[no_unique_address]]` member (potentially-overlapping).

Until C++20 (national-body comment RU007), a class with a `const` or reference member was also not transparently
replaceable, which is why older articles show `std::launder` for `struct X { const int n; };`. In
C++20 that case works without it.

`std::launder(p)` is needed when the rule does not hold, or when you only have a pointer that never
pointed to the new object. The most common real case is the buffer pointer itself:

```cpp title="launder.cpp" showLineNumbers
#include <cstddef>
#include <new>

struct Msg { int code; };

alignas(Msg) std::byte storage[sizeof(Msg)];

void emplace(int c) { ::new (storage) Msg{c}; }

int read_code() {
    // reinterpret_cast<Msg*>(storage) points to the byte array, not to the Msg in it.
    // launder returns a pointer to the Msg object that lives at that address.
    return std::launder(reinterpret_cast<Msg*>(storage))->code;
}

int main() { emplace(7); return read_code() - 7; }   // returns 0
```

Keeping the pointer returned by placement new avoids `std::launder` completely: that pointer points
to the new object by definition. `std::optional`-like classes that store only the buffer and
re-derive the pointer each time are the ones that need `std::launder`. It is a no-op at run time;
it only stops the optimizer from assuming the old object's values, such as a `const` member or a
vtable pointer, still hold.

<details>
<summary>The base-class case, where launder is still required</summary>

```cpp title="base-replace.cpp" showLineNumbers
#include <new>

struct Base { virtual int id() { return 1; } virtual ~Base() = default; };
struct Derived : Base { int id() override { return 2; } };

int main() {
    Base b;
    static_assert(sizeof(Derived) == sizeof(Base));
    b.~Base();
    Base* p = ::new (&b) Derived;               // a Derived now lives where b was
    int via_launder = std::launder(&b)->id();   // 2: refers to the new object
    // b.id() would be UB: `b` names a complete Base, the new object is a Derived
    p->~Base();
    ::new (&b) Base;                            // put a Base back before b's destructor runs
    return via_launder - 2;                     // returns 0
}
```

This is the `transmogrify` example from cppreference, reduced. Code like this is rare. It is shown
to make the rule concrete.

</details>

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `char buf[sizeof(T)]` without `alignas(T)` | Misaligned object: undefined behavior; crashes with SIMD types | `alignas(T) std::byte buf[sizeof(T)]` |
| `delete p` on a placement-new object | `delete` frees memory that did not come from `new T` | `std::destroy_at(p)`, then release the storage the way it was obtained |
| Never calling the destructor | Resources owned by the object leak | Pair every construct with a destroy, or use RAII around the buffer |
| Constructing twice in the same slot | The first object's destructor never runs | Destroy before reconstructing |
| `reinterpret_cast<T*>(buffer)` to reach the object | That pointer points to the buffer, not to the `T` | Keep the pointer from placement new, or use `std::launder` |
| Hand-rolled pools without exception handling | If a constructor throws mid-way, constructed objects leak | Use `std::uninitialized_*` algorithms, which clean up |

## Key points

- Placement new and `std::construct_at` construct only. `std::destroy_at` destroys only. You manage
  the storage separately.
- Storage must be big enough, aligned for `T`, and a `std::byte`/`unsigned char` array (or from an
  allocation function).
- The pointer returned by placement new is always valid for the new object. Pointers to the buffer
  or to an old object may need `std::launder`.
- In application code, prefer `std::optional`, `std::variant` and containers. They already do all of
  this correctly.
