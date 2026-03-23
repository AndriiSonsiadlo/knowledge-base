---
id: class-layout
title: Class Memory Layout
sidebar_label: Class Layout
sidebar_position: 1
tags: [c++, classes, memory-layout, padding, vtable]
---

# Class Memory Layout

This page explains how the **class features you write** — members, virtual functions, inheritance —
translate into a memory layout. It's the OOP-level intuition; the byte-exact ABI details and tooling
live in [Object Layout](../12-low-level-and-platform/02-object-layout.md).

:::info Three things shape a class's layout
1. **Members** sit in declaration order, with padding for alignment (see [Memory Alignment](../05-memory-and-object-lifetime/alignment.md)).
2. **Virtual functions** add a hidden vtable pointer.
3. **Base classes** are embedded as subobjects.
:::

## Members: declaration order + padding

The compiler lays members out **in declaration order — never reordered** — and inserts padding so
each is aligned. That predictability is what makes C interop and `offsetof` possible.

```cpp showLineNumbers
class Simple {
    int  a;   // offset 0
    char b;   // offset 4
              // 3 bytes padding
    int  c;   // offset 8
};
sizeof(Simple);   // 12, not 9
```

Because *you* control the order, ordering members **largest → smallest** is the cheapest way to
shrink a class. The mechanics (alignment rules, why trailing padding exists) are covered once in
[Memory Alignment](../05-memory-and-object-lifetime/alignment.md); the packing/bit-field options in
[Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md).

## Virtual functions add a vptr

A class with any virtual function gains a hidden **vtable pointer** (`vptr`), conventionally first.
Every object carries the `vptr`; the vtable itself is shared per type.

```cpp showLineNumbers
class NoVirtual { int data; };
sizeof(NoVirtual);    // 4

class WithVirtual { int data; virtual void f(); };
sizeof(WithVirtual);  // 16 on 64-bit: 8 (vptr) + 4 (data) + 4 (padding)
```

So virtual dispatch costs **8 bytes per object** plus one indirection per call. How the vtable is
built and used for overriding is in [Virtual Functions](./virtual-functions.md); the byte-level
picture across inheritance is in [Object Layout](../12-low-level-and-platform/02-object-layout.md).

## Empty classes and the empty base optimization

Every object needs a unique address, so even an empty class has `sizeof == 1`. But an **empty base**
contributes nothing — the *empty base optimization* (EBO) folds it away. This is why stateless
policy/allocator base classes are free.

```cpp showLineNumbers
class Empty {};
sizeof(Empty);                 // 1 — needs a distinct address

class Derived : Empty { int value; };
sizeof(Derived);               // 4 — Empty base takes no space (EBO)
```

## Inheritance: bases are subobjects

A base class is embedded whole inside the derived object; derived members follow. With **multiple
inheritance**, each base is a separate subobject — which is why converting `Derived*` to a second
base may *adjust the pointer* to land on that base's subobject.

```cpp showLineNumbers
struct Base1 { int b1; };
struct Base2 { int b2; };
struct Derived : Base1, Base2 { int d; };   // layout: [b1][b2][d]
```

If those bases have virtual functions, the derived object carries **one vptr per polymorphic base**.
The diamond/virtual-inheritance cases and their shared-base layout are detailed in
[Object Layout](../12-low-level-and-platform/02-object-layout.md) and
[Multiple Inheritance](./multiple-inheritance.md).

## Standard-layout: the contract for C interop

A **standard-layout** class has a predictable, C-compatible layout — required for `offsetof`, for
`memcpy`-style serialization, and for passing structs to C. The rules in practice: no virtual
functions or virtual bases, and all non-static data members with the **same access**.

```cpp showLineNumbers
struct Ok    { int a; int b; };                 // standard-layout
struct NotOk { private: int a; public: int b; }; // mixed access — not standard-layout

static_assert(std::is_standard_layout_v<Ok>);
```

## Inspecting real layout

Don't guess — ask the compiler:

```bash
g++   -fdump-lang-class                 file.cpp   # GCC
clang++ -Xclang -fdump-record-layouts   file.cpp   # Clang
cl    /d1reportAllClassLayout           file.cpp   # MSVC
```

## Summary

- Members lay out in declaration order with alignment padding; order them large→small to save space.
- A virtual function adds an 8-byte `vptr` per object and one indirection per call.
- Empty classes are size 1, but empty *bases* vanish under the empty base optimization.
- Each base is a subobject; multiple polymorphic bases mean multiple vptrs and pointer adjustment.
- **Standard-layout** types give the C-compatible layout that `offsetof` and serialization rely on.

## Related

- [Object Layout](../12-low-level-and-platform/02-object-layout.md) — byte-exact ABI view, vtables, virtual inheritance
- [Virtual Functions](./virtual-functions.md) — how the vtable enables overriding
- [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) · [Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md)
