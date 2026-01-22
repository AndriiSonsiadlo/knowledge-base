---
id: class-layout
title: Class Memory Layout
sidebar_label: Class Layout
sidebar_position: 1
tags: [c++, classes, memory-layout, padding, vtable]
---

# Class Memory Layout

Understanding how classes are laid out in memory is essential for optimization, debugging, and interfacing with other languages.

:::info Memory Organization
Members are arranged in declaration order with padding for alignment. Virtual functions add hidden vtable pointers.
:::

## Basic Class Layout

Members appear in memory in declaration order, never reordered by the compiler. Padding is inserted to meet alignment requirements.
```cpp showLineNumbers
class Simple {
    int a;      // 4 bytes, offset 0
    char b;     // 1 byte, offset 4
    // 3 bytes padding
    int c;      // 4 bytes, offset 8
};

sizeof(Simple);  // 12 bytes (not 9!)
```

**Memory layout:**
```
Offset  Size  Member
0       4     int a
4       1     char b
5       3     [padding]
8       4     int c
Total: 12 bytes
```

The padding after `b` ensures `c` starts at an address divisible by 4 (its alignment requirement). The compiler never reorders members to minimize padding - they appear exactly in declaration order. This predictability is important for binary compatibility and interfacing with C.

## Member Order Matters

Reordering members from largest to smallest minimizes padding waste.
```cpp showLineNumbers
// ❌ Wasteful: 32 bytes
class Wasteful {
    char a;     // 1 byte + 7 padding
    double b;   // 8 bytes
    char c;     // 1 byte + 7 padding
    double d;   // 8 bytes
};

// ✅ Efficient: 24 bytes (25% smaller)
class Efficient {
    double b;   // 8 bytes
    double d;   // 8 bytes
    char a;     // 1 byte
    char c;     // 1 byte
    // 6 bytes padding (to make size multiple of 8)
};
```

:::success Optimization Rule
**Group by size:** doubles together, ints together, chars together. This minimizes padding between members.
:::

## Alignment Requirements

Each type has an alignment requirement - the address must be divisible by this value.
```cpp showLineNumbers
alignof(char);    // 1
alignof(short);   // 2
alignof(int);     // 4
alignof(double);  // 8
alignof(void*);   // 8 (on 64-bit)

class Example {
    char c;    // Align: 1
    int i;     // Align: 4
    double d;  // Align: 8
};

alignof(Example);  // 8 (max alignment of members)
sizeof(Example);   // 16 (must be multiple of alignment)
```

**Alignment determines:**
- Where members can be placed (must be at aligned addresses)
- Overall class size (must be multiple of max member alignment)
- Performance (aligned access is faster)

## Empty Classes

Even empty classes have non-zero size to ensure distinct addresses for different objects.

```cpp showLineNumbers 
class Empty {};
sizeof(Empty);  // 1 byte (minimum)

Empty arr[10];
&arr[0] != &arr[1];  // Must have different addresses

// Empty base optimization
class Derived : Empty {
    int value;
};
sizeof(Derived);  // 4 bytes (Empty takes no space as base)
```

:::info Why Size 1?
C++ requires every object to have a unique address. Zero-size objects would violate this. However, base classes can be optimized away (EBO).
:::

## Member Access and Offsets

The compiler calculates fixed offsets for each member, enabling efficient direct access.

```cpp showLineNumbers 
class Widget {
    int x;      // Offset: 0
    int y;      // Offset: 4
    int z;      // Offset: 8
};

Widget w;
int* px = &w.x;  // Address of w + 0
int* py = &w.y;  // Address of w + 4
int* pz = &w.z;  // Address of w + 8

// Member access compiles to:
// w.y  →  *(address_of_w + 4)
```

Member access is just pointer arithmetic using compile-time offsets. This makes member access as fast as array indexing. The offsets are fixed at compile-time and never change, enabling aggressive optimization.

## Virtual Functions and vtables

Classes with virtual functions have a hidden vtable pointer (vptr) at the start of the object.
```cpp showLineNumbers
class NoVirtual {
    int data;
};
sizeof(NoVirtual);  // 4 bytes

class WithVirtual {
    int data;
    virtual void f() {}
};
sizeof(WithVirtual);  // 16 bytes (8 vptr + 4 data + 4 padding)
```

**vtable overhead:**
```
[vptr: 8 bytes] → points to vtable
[int data: 4 bytes]
[padding: 4 bytes]
Total: 16 bytes
```

The `vptr` points to a table of function pointers used for dynamic dispatch. Every object of a class with virtual functions has its own `vptr` pointing to the shared vtable for that class.

### vtable Structure

The `vtable` contains function pointers for all virtual functions in the class hierarchy.

```cpp showLineNumbers 
class Animal {
public:
    virtual void speak() { std::cout << "Animal\n"; }
    virtual void move() { std::cout << "Moving\n"; }
};

class Dog : public Animal {
public:
    void speak() override { std::cout << "Woof\n"; } // Overridden
    // move() inherited
};

// Animal's vtable:        Dog's vtable:
// [0] → Animal::speak    [0] → Dog::speak (overridden)
// [1] → Animal::move     [1] → Animal::move (inherited)
```

**Virtual call mechanism:**
```cpp
Animal* ptr = new Dog();
ptr->speak();

// Compiled to approximately:
// 1. Load vptr from object
// 2. Load function pointer from vtable[0]
// 3. Call that function
```

Virtual function calls require an extra indirection: load the `vptr`, then load the function pointer, then call it. This is slower than non-virtual calls but enables polymorphism. The `vtable` itself is shared among all objects of the same dynamic type.

## Multiple Inheritance Layout

Multiple base classes create multiple subobjects within the derived class.

```cpp showLineNumbers
class Base1 {
    int b1;
};

class Base2 {
    int b2;
};

class Derived : public Base1, public Base2 {
    int d;
};

sizeof(Derived);  // 12 bytes
```

**Layout:**
```
[Base1: b1: 4 bytes]
[Base2: b2: 4 bytes]
[Derived: d: 4 bytes]
```

Each base class appears as a subobject within the derived object. The derived class members appear after all base class members. Pointer conversions between derived and base classes may require address adjustments to point to the correct subobject.

### Multiple Inheritance with Virtual Functions

When multiple base classes have virtual functions, the derived class contains multiple `vtable` pointers.

```cpp showLineNumbers 
class Base1 {
    virtual void f1() {}
};

class Base2 {
    virtual void f2() {}
};

class Derived : public Base1, public Base2 {
    int d;
};

sizeof(Derived);  // 32 bytes on 64-bit
```
**Layout:**
```
[vptr1: 8 bytes] → Base1's vtable
[Base1 data]
[vptr2: 8 bytes] → Base2's vtable  
[Base2 data]
[Derived data]
[padding]
```

Each base class with virtual functions contributes a `vtable` pointer. Converting `Derived*` to `Base2*` requires adjusting the pointer to skip over the `Base1` subobject. This adds complexity but enables polymorphism through any base class.

## Alignment and Padding

The class's overall alignment is the maximum alignment of its members.

```cpp showLineNumbers 
class Example {
    char c;      // Align: 1
    int i;       // Align: 4
    double d;    // Align: 8
};

alignof(Example);  // 8 (from double)
sizeof(Example);   // 16

// Layout:
// [char c: 1][padding: 3][int i: 4][double d: 8]
// Total must be multiple of alignment (16 = 2 * 8)
```

The size must be a multiple of the alignment to ensure arrays of objects maintain proper alignment for all members. This sometimes requires trailing padding after the last member.

## Bit Fields

Bit fields allow packing multiple values into fewer bytes, useful for flags and low-level structures.

```cpp showLineNumbers 
struct Flags {
    unsigned int flag1 : 1;  // 1 bit
    unsigned int flag2 : 1;  // 1 bit
    unsigned int value : 6;  // 6 bits
    // All 8 bits fit in 1 byte
};

sizeof(Flags);  // 4 bytes (implementation-defined, often padded to int)

Flags f;
f.flag1 = 1;
f.flag2 = 0;
f.value = 42;
```

Bit fields specify the exact number of bits for each member. The compiler packs them together to save space. However, bit fields have limitations: you can't take their address, and layout is implementation-defined. Use them sparingly for memory-constrained scenarios.

## Structure Packing

Some compilers allow forcing tighter packing, eliminating padding but potentially causing misalignment.

```cpp showLineNumbers 
// GCC/Clang: packed attribute
struct __attribute__((packed)) Packed {
    char c;      // 1 byte
    int i;       // 4 bytes (no padding before!)
    char c2;     // 1 byte
};
sizeof(Packed);  // 6 bytes (no padding)

// MSVC: pragma pack
#pragma pack(push, 1)
struct Packed {
    char c;
    int i;
    char c2;
};
#pragma pack(pop)
sizeof(Packed);  // 6 bytes
```

Packed structures eliminate padding but members may be misaligned. On x86-64 this is slow; on ARM it can crash. Only use packing for binary file formats or network protocols where you need exact layout. Never use for normal program data.

## Standard Layout Classes

Standard layout classes have restrictions but guarantee C-compatible memory layout.

```cpp showLineNumbers 
// Standard layout: C-compatible
class StandardLayout {
public:
    int a;
    int b;
};

// Not standard layout: different access control
class NotStandard {
private:
    int a;
public:
    int b;
};

// Not standard layout: virtual functions
class NotStandard2 {
    virtual void f() {}
    int a;
};

static_assert(std::is_standard_layout_v<StandardLayout>);
```

Standard layout classes can be passed to C code because their layout is predictable and compatible. They require: no virtual functions, no virtual base classes, same access control for all non-static members, no non-standard-layout base classes or members.

## Inspecting Layout

Use `offsetof` and compiler tools to examine exact memory layout.
```cpp showLineNumbers
#include <cstddef>

class Widget {
public:
    char a;
    int b;
    double c;
};

// offsetof only works for standard-layout types
offsetof(Widget, a)  // 0
offsetof(Widget, b)  // 4
offsetof(Widget, c)  // 8

sizeof(Widget);       // 16
alignof(Widget);      // 8
```

**Compiler tools:**
```bash
# GCC/Clang: dump class hierarchy
g++ -fdump-class-hierarchy file.cpp

# Clang: dump record layouts
clang++ -Xclang -fdump-record-layouts file.cpp

# MSVC: dump all class layouts
cl /d1reportAllClassLayout file.cpp
```

## Summary

:::info Core principles:
- Members appear in declaration order (never reordered)
- Padding inserted for alignment requirements
- Size must be multiple of alignment
- Virtual functions add 8-byte vptr (64-bit)
:::

:::info Alignment rules:
- Each type has alignment requirement (1, 2, 4, 8 bytes)
- Class alignment = max member alignment
- Size = multiple of alignment (for arrays)
:::

:::info Optimization:
- Order members largest → smallest to minimize padding
- Group related data for cache performance
- Empty base optimization (EBO) eliminates empty base size
:::

:::info Virtual function overhead:
- 8 bytes per object (vptr)
- Multiple inheritance = multiple vptrs
- ~2-3ns per virtual call (indirect through vtable)
:::

:::info Tools:
- `sizeof()` - total size including padding
- `alignof()` - alignment requirement
- `offsetof()` - member offset (standard-layout types only)
- Compiler flags - dump exact layout
:::
