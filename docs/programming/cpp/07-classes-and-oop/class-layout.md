---
id: class-layout
title: Class Memory Layout
sidebar_label: Class Layout
sidebar_position: 1
tags: [c++, classes, memory-layout, padding, vtable]
---

# Class Memory Layout

Understanding how classes are laid out in memory is essential for optimization, debugging, and interfacing with other languages. The compiler arranges data members, adds padding for alignment, and includes hidden pointers for virtual functions.

:::info Memory Organization
Class layout determines size, alignment, and performance. Members are arranged in declaration order with padding for alignment, plus hidden vtable pointers for polymorphism.
:::

## Basic Class Layout

Classes lay out their data members in memory in the order they're declared, just like structs. The compiler adds padding to meet alignment requirements.

```cpp
class Simple {
    int a;      // 4 bytes
    char b;     // 1 byte
    // 3 bytes padding
    int c;      // 4 bytes
};

sizeof(Simple);  // 12 bytes (not 9!)

// Memory layout:
// [int a: 4 bytes][char b: 1 byte][padding: 3 bytes][int c: 4 bytes]
```

The padding after `b` ensures `c` starts at an address divisible by 4 (its alignment requirement). The compiler never reorders members to minimize padding - they appear exactly in declaration order. This predictability is important for binary compatibility and interfacing with C.

### Member Order Matters

Reordering members can reduce wasted space from padding, sometimes significantly.

```cpp
class Wasteful {
    char a;     // 1 byte + 7 padding
    double b;   // 8 bytes
    char c;     // 1 byte + 7 padding
    double d;   // 8 bytes
};
sizeof(Wasteful);  // 32 bytes

class Efficient {
    double b;   // 8 bytes
    double d;   // 8 bytes
    char a;     // 1 byte
    char c;     // 1 byte
    // 6 bytes padding (to make size multiple of 8)
};
sizeof(Efficient);  // 24 bytes (25% smaller!)
```

Grouping larger members together and smaller members together minimizes padding. For frequently-allocated classes, this optimization can significantly reduce memory usage. However, logical grouping of related members sometimes matters more than saving a few bytes.

## Empty Classes

Even empty classes have non-zero size to ensure distinct addresses for different objects.

```cpp
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

The one-byte minimum ensures every object has a unique address, which is required by the C++ standard. However, when an empty class is used as a base class, the compiler can apply empty base optimization, giving it zero size in the derived class layout.

## Member Access and Offsets

The compiler calculates fixed offsets for each member, enabling efficient direct access.

```cpp
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

Classes with virtual functions have a hidden pointer to a virtual function table (vtable), adding overhead.

```cpp
class Base {
    int data;           // 4 bytes
    virtual void f() {} // Adds vtable pointer
};

sizeof(Base);  // 16 bytes (8-byte vtable ptr + 4-byte data + 4 padding)

// Layout:
// [vtable ptr: 8 bytes][int data: 4 bytes][padding: 4 bytes]
```

The vtable pointer (vptr) typically appears at the start of the object, though this is implementation-defined. It points to a table of function pointers used for dynamic dispatch. Every object of a class with virtual functions has its own vptr pointing to the shared vtable for that class.

### vtable Structure

The vtable contains function pointers for all virtual functions in the class hierarchy.

```cpp
class Animal {
public:
    virtual void speak() { std::cout << "Animal\n"; }
    virtual void move() { std::cout << "Moving\n"; }
};

class Dog : public Animal {
public:
    void speak() override { std::cout << "Woof\n"; }
};

// vtable for Animal:
// [0]: &Animal::speak
// [1]: &Animal::move

// vtable for Dog:
// [0]: &Dog::speak     (overridden)
// [1]: &Animal::move   (inherited)

Dog d;
Animal* ptr = &d;
ptr->speak();  // 1. Load vptr from object
               // 2. Load speak function pointer from vtable[0]
               // 3. Call that function
```

Virtual function calls require an extra indirection: load the vptr, then load the function pointer, then call it. This is slower than non-virtual calls but enables polymorphism. The vtable itself is shared among all objects of the same dynamic type.

## Multiple Inheritance Layout

Multiple inheritance creates complex layouts with multiple base class subobjects.

```cpp
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

// Layout:
// [Base1: int b1][Base2: int b2][int d]
```

Each base class appears as a subobject within the derived object. The derived class members appear after all base class members. Pointer conversions between derived and base classes may require address adjustments to point to the correct subobject.

### Multiple Inheritance with Virtual Functions

When multiple base classes have virtual functions, the derived class contains multiple vtable pointers.

```cpp
class Base1 {
    int b1;
    virtual void f1() {}
};

class Base2 {
    int b2;
    virtual void f2() {}
};

class Derived : public Base1, public Base2 {
    int d;
};

sizeof(Derived);  // 32 bytes on 64-bit
// [vtable ptr 1][Base1::b1][vtable ptr 2][Base2::b2][Derived::d][padding]
```

Each base class with virtual functions contributes a vtable pointer. Converting `Derived*` to `Base2*` requires adjusting the pointer to skip over the Base1 subobject. This adds complexity but enables polymorphism through any base class.

## Alignment and Padding

The class's overall alignment is the maximum alignment of its members.

```cpp
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

```cpp
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

```cpp
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

```cpp
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

You can examine class layout using compiler-specific tools and `offsetof`.

```cpp
#include <cstddef>

class Widget {
public:
    char a;
    int b;
    double c;
};

// offsetof only works for standard-layout types
std::cout << offsetof(Widget, a) << "\n";  // 0
std::cout << offsetof(Widget, b) << "\n";  // 4
std::cout << offsetof(Widget, c) << "\n";  // 8

// Compiler-specific layout info:
// GCC: g++ -fdump-class-hierarchy file.cpp
// Clang: clang++ -Xclang -fdump-record-layouts file.cpp
// MSVC: cl /d1reportAllClassLayout file.cpp
```

These tools show exact memory layout including padding, vtable pointers, and base class subobjects. Use them when optimizing memory usage or debugging low-level issues.

:::warning Platform-Specific Behavior

**Padding Varies**: Different platforms have different alignment requirements.

**vtable Layout**: Implementation-defined - don't rely on specific vtable structure.

**Member Order**: Declared order is guaranteed, but padding can vary.

**Bit Fields**: Layout is completely implementation-defined.

**ABI Matters**: Changing class layout breaks binary compatibility across versions.
:::

## Summary

Class memory layout follows declaration order with padding for alignment. Members appear in the order declared, never reordered by the compiler. Padding is inserted before members to meet their alignment requirements, and after the last member to make the total size a multiple of the class's alignment. The class's alignment is the maximum alignment of its members. Empty classes have size 1 unless used as base classes where empty base optimization applies. Virtual functions add a hidden vtable pointer (typically 8 bytes on 64-bit) at the start of the object. Multiple inheritance creates multiple base class subobjects within the derived object, potentially with multiple vtable pointers. Pointer conversions may require address adjustments in multiple inheritance. Bit fields pack multiple values into fewer bits but have implementation-defined layout. Structure packing removes padding but causes misalignment problems. Standard layout classes guarantee C compatibility by having restrictions on their structure. Use compiler tools to inspect exact layout for debugging and optimization. Reordering members from largest to smallest minimizes padding waste. The size must be a multiple of alignment to support arrays. Virtual function calls are indirect through vtables, adding runtime cost. Understanding layout is essential for optimization, binary compatibility, and interfacing with C code.

:::success Memory Layout Essentials

**Declaration Order**: Members appear in declared order - never reordered.

**Padding for Alignment**: Inserted before members and after last member.

**vtable Overhead**: Virtual functions add 8-byte pointer (64-bit).

**Optimize Order**: Group large members together to minimize padding.

**Multiple Inheritance**: Multiple base subobjects, complex pointer adjustments.

**Standard Layout**: C-compatible but requires restrictions.

**Size = Multiple of Alignment**: Ensures array elements stay aligned.

**ABI Stability**: Changing layout breaks binary compatibility.
:::