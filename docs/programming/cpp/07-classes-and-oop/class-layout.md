---
id: class-layout
title: Class Memory Layout
sidebar_label: Class Layout
sidebar_position: 1
tags: [c++, classes, memory-layout, padding, vtable, standard-layout]
---

# Class Memory Layout

A class object is a block of bytes made of three kinds of parts: its **base-class subobjects**, its
**non-static data members**, and, if the class is polymorphic, a hidden **vtable pointer** (vptr)
that the compiler adds. Knowing where these go explains why `sizeof` is often larger than the sum of
the members, why a virtual function costs space in every object, and why converting a pointer to a
second base class can change its address. This page gives the class-level picture. The byte-exact
ABI rules (vtable contents, virtual-base offsets) live in
[Object Layout](../12-low-level-and-platform/02-object-layout.md).

**Prerequisites:** [Memory alignment](../05-memory-and-object-lifetime/alignment.md) (padding and
`alignof`).

All sizes below were checked with `static_assert` under g++ 15 and clang++ 21 on x86-64 Linux, which
use the Itanium C++ ABI. The standard fixes only some of these facts. Where a number is ABI-specific,
the text says so. MSVC uses a different ABI and can differ, especially with multiple and virtual
inheritance.

<Diagram title="Parts of a class object" caption="Typical Itanium ABI order for a class with one polymorphic base. The vptr is shared with the primary base." accent="blue">
  <DiagramRow>
    <DiagramNode title="Base subobject" accent>Base members, in base declaration order; holds the shared vptr if the base is polymorphic</DiagramNode>
    <DiagramNode title="Own members">Declaration order, with padding</DiagramNode>
    <DiagramNode title="Tail padding" dashed>Rounds sizeof up to a multiple of alignof</DiagramNode>
  </DiagramRow>
</Diagram>

## Data members: declaration order plus padding

Non-static data members are laid out in **declaration order**. The compiler never reorders them. It
inserts padding so each member meets its alignment and rounds the total size up so that arrays of the
class stay aligned. (For members with different access specifiers the order was only guaranteed
from C++23, P1847. GCC, Clang and MSVC always used declaration order.)

```cpp title="simple.cpp" showLineNumbers
#include <cstddef>

struct Simple {
    int  a;   // offset 0
    char b;   // offset 4, then 3 bytes of padding
    int  c;   // offset 8
};
static_assert(sizeof(Simple) == 12);         // not 9
static_assert(offsetof(Simple, c) == 8);

int main() {}
```

Because you control the order, sorting members from the largest alignment to the smallest is the
cheapest way to shrink a class. The rules behind padding are explained once, in
[Memory alignment](../05-memory-and-object-lifetime/alignment.md#padding-the-compilers-half-of-the-job).
Packing and bit-fields are covered in
[Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md).

Static data members and member functions take no space in the object. A static member is a single
variable with static storage duration, and member functions are ordinary code.

## Virtual functions add a vptr

A class that declares or inherits a virtual function is **polymorphic**. Every mainstream compiler
implements this by storing a pointer to a per-class table of function pointers (the **vtable**) in
each object. The standard does not mention vtables. It only requires dynamic dispatch to work. In the
Itanium ABI the vptr sits at offset 0, and on a 64-bit target it is 8 bytes.

```cpp title="vptr.cpp" showLineNumbers
struct NoVirtual   { int data; };
struct WithVirtual {
    int data;
    virtual void f() {}
    virtual ~WithVirtual() = default;
};

static_assert(sizeof(NoVirtual) == 4);
static_assert(sizeof(WithVirtual) == 16);   // x86-64: vptr 8 + int 4 + 4 padding

int main() {}
```

The cost is one pointer per object, however many virtual functions the class has, because the vtable
itself is shared by every object of the class. Each virtual call also loads the vptr and the
function address before calling through it. How dispatch uses the table is the subject of
[Virtual functions](./virtual-functions.md).

## Empty classes and the empty base optimization

Two distinct objects of the same type must have distinct addresses, so even a class with no data
members has `sizeof` at least 1. As a **base class**, though, an empty class may occupy zero bytes:
the **empty base optimization** (EBO) places it at the same address as the derived object's first
member. The standard allows EBO, and it is required for standard-layout classes. Every mainstream
compiler applies it.

An empty class used as a **member** still takes a byte, plus padding. C++20 added
`[[no_unique_address]]` so a member can overlap other members the same way an empty base does.
MSVC ignores the standard attribute for ABI reasons and spells it `[[msvc::no_unique_address]]`.

```cpp title="ebo.cpp" showLineNumbers
struct Empty {};

struct UsesEbo        : Empty { int value; };                 // empty base
struct HasEmptyMember { Empty e; int value; };                // empty member
struct UsesNua        { [[no_unique_address]] Empty e; int value; };

static_assert(sizeof(Empty) == 1);
static_assert(sizeof(UsesEbo) == 4);          // base takes no space
static_assert(sizeof(HasEmptyMember) == 8);   // 1 byte + 3 padding + int
static_assert(sizeof(UsesNua) == 4);          // GCC/Clang; MSVC needs [[msvc::no_unique_address]]

int main() {}
```

This is why stateless allocators, comparators and policy classes cost nothing when a container
stores them as a base or as a `[[no_unique_address]]` member.

## Base classes are subobjects

A base class is stored whole inside the derived object, as a **base-class subobject**. Derived
members follow the bases. With several bases, each one is a separate subobject at its own offset,
in the order the bases are listed.

```cpp title="bases.cpp" showLineNumbers
#include <cstdio>

struct Base1 { int b1; };
struct Base2 { int b2; };
struct Derived : Base1, Base2 { int d; };     // [b1][b2][d]
static_assert(sizeof(Derived) == 12);

struct P1 { virtual ~P1() = default; int x; };
struct P2 { virtual ~P2() = default; int y; };
struct Both : P1, P2 { int z; };              // two polymorphic bases: two vptrs
static_assert(sizeof(Both) == 32);            // x86-64 Itanium ABI

int main() {
    Both b;
    P1* p1 = &b;
    P2* p2 = &b;                               // the compiler adds an offset here
    std::printf("%td %td\n",
                reinterpret_cast<char*>(p1) - reinterpret_cast<char*>(&b),
                reinterpret_cast<char*>(p2) - reinterpret_cast<char*>(&b));
}
```

```text
0 16
```

Converting `Both*` to `P2*` adds 16 so the pointer lands on the `P2` subobject. The compiler does the
adjustment for implicit conversions and `static_cast`, which is one reason a `reinterpret_cast`
between base and derived pointers is wrong. Each polymorphic base that cannot share the primary
base's vptr brings its own. Diamonds and virtual bases are covered in
[Multiple inheritance](./multiple-inheritance.md).

<Diagram title="struct Both on x86-64 (32 bytes)" accent="amber">
  <DiagramRow>
    <DiagramNode title="P1 subobject">offset 0: vptr, x, pad</DiagramNode>
    <DiagramNode title="P2 subobject" accent>offset 16: vptr, y</DiagramNode>
    <DiagramNode title="z">offset 28</DiagramNode>
  </DiagramRow>
</Diagram>

## Standard-layout classes

A **standard-layout** class has a layout the standard pins down enough for C interop: its first
member is at the class's address, `offsetof` is well-defined, and it matches an equivalent C
`struct` on the same platform. The main conditions:

- no virtual functions and no virtual base classes,
- all non-static data members have the same access control,
- all non-static data members are declared in one class of the hierarchy (the class itself or one
  base, not both),
- every member and base is itself standard-layout, and no base has the same type as the first member.

```cpp title="standard-layout.cpp" showLineNumbers
#include <type_traits>

struct Ok    { int a; int b; };
struct Mixed { private: int a; public: int b; void touch() { a = 0; } };
struct Poly  { virtual ~Poly() = default; int a; };

static_assert(std::is_standard_layout_v<Ok>);
static_assert(!std::is_standard_layout_v<Mixed>);   // mixed access
static_assert(!std::is_standard_layout_v<Poly>);    // has a vptr

int main() {}
```

Standard-layout is about layout only. Whether bytes can be copied with `memcpy` is a separate
property, `std::is_trivially_copyable`, discussed in
[Type traits](../08-templates-and-metaprogramming/type-traits.md).

## Inspecting a real layout

Ask the compiler instead of guessing:

```bash
g++ -fdump-lang-class -c file.cpp                     # GCC: writes file.cpp.*.class
clang++ -Xclang -fdump-record-layouts -c file.cpp     # Clang: prints to stdout
cl /d1reportAllClassLayout file.cpp                    # MSVC (undocumented flag)
```

`pahole` reads DWARF debug info from a built binary and shows each member's offset and the padding
holes between them.

## References

- [cppreference: Non-static data members, layout](https://en.cppreference.com/w/cpp/language/data_members#Layout)
- [cppreference: Empty base optimization](https://en.cppreference.com/w/cpp/language/ebo)
- [cppreference: `[[no_unique_address]]`](https://en.cppreference.com/w/cpp/language/attributes/no_unique_address)
- [cppreference: StandardLayoutType](https://en.cppreference.com/w/cpp/named_req/StandardLayoutType)
- [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)
