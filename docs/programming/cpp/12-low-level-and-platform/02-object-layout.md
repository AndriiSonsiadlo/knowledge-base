---
id: object-layout
title: Object Layout and Memory Structure
sidebar_label: Object Layout
sidebar_position: 2
tags: [cpp, object-layout, memory, vtable, inheritance]
---

# Object Layout in Memory

How C++ objects are arranged in memory: data members, padding, vtables, base class subobjects. Understanding layout is crucial for binary compatibility and optimization.

:::info Memory Organization
Objects = members + padding + vtable pointer (if virtual) + base class subobjects (if inheritance)
:::

## Simple Class Layout
```cpp showLineNumbers
class Simple {
    int a;      // 4 bytes
    char b;     // 1 byte
    // 3 bytes padding
    double c;   // 8 bytes
};
// Total: 16 bytes

// Memory layout:
// [a: 4][b: 1][pad: 3][c: 8]
```

See [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) for padding rules.

## Empty Classes
```cpp showLineNumbers
class Empty {};
sizeof(Empty);  // 1 (not 0!)

// Why? Two objects must have different addresses
Empty arr[2];
// &arr[0] != &arr[1] requires non-zero size
```

**Empty Base Optimization (EBO):**
```cpp showLineNumbers
class Base {};
class Derived : Base {
    int x;
};
sizeof(Derived);  // 4, not 5! (Base optimized away)
```

## Virtual Functions and vtable
```cpp showLineNumbers
class Base {
    int data;           // 4 bytes
public:
    virtual void foo();
};
// Layout: [vptr: 8][data: 4][padding: 4] = 16 bytes

// vtable (separate):
// [ptr to foo()]
```

**vtable pointer** (`vptr`) added as hidden first member.
```
Object:  [vptr][data][padding]
           |
           v
vtable:  [&Base::foo]
```

## Single Inheritance
```cpp showLineNumbers
class Base {
    int base_data;      // 4 bytes
public:
    virtual void foo();
};

class Derived : Base {
    int derived_data;   // 4 bytes
};

// Layout:
// [vptr: 8][base_data: 4][derived_data: 4][padding: 4] = 20 bytes

// vtable:
// [&Derived::foo or &Base::foo]
```

**Memory:**
```
[Base subobject: vptr, base_data][Derived data]
```

## Multiple Inheritance
```cpp showLineNumbers
class A {
    int a;
public:
    virtual void fA();
};

class B {
    int b;
public:
    virtual void fB();
};

class C : public A, public B {
    int c;
};

// Layout (simplified):
// [A's vptr][a][B's vptr][b][c]
//    ^                ^
//    |                |
//  vtable A        vtable B
```

**Two `vptr`s** for two bases with virtual functions!

## Virtual Inheritance (Diamond Problem)
```cpp showLineNumbers
class Base {
    int base;
public:
    virtual void f();
};

class Left : virtual Base {
    int left;
};

class Right : virtual Base {
    int right;
};

class Bottom : Left, Right {
    int bottom;
};

// Layout (complex):
// [Left part][Right part][shared Base][Bottom data]
// Uses vbase pointer to locate shared Base
```

**Virtual base** stored separately, accessed via offset.

## Inspecting Object Layout

### GCC/Clang
```bash
# Show class layout
g++ -fdump-lang-class file.cpp

# Or
clang++ -Xclang -fdump-record-layouts file.cpp
```

### MSVC
```bash
cl /d1reportAllClassLayout file.cpp
```

### Example Output
```cpp showLineNumbers
class Widget {
    char c;
    int i;
    double d;
};
```

**Output:**
```
*** Dumping AST Record Layout
         0 | class Widget
         0 |   char c
         4 |   int i
         8 |   double d
           | [sizeof=16, align=8]
```

## Member Access Optimization
```cpp showLineNumbers
// ❌ Poor layout (12 bytes wasted)
struct Poor {
    char a;      // offset 0
    // 7 padding
    double b;    // offset 8
    // 8 padding
    char c;      // offset 16
    // 7 padding
};  // sizeof = 24

// ✅ Optimized (6 bytes wasted)
struct Optimized {
    double b;    // offset 0
    char a;      // offset 8
    char c;      // offset 9
    // 6 padding
};  // sizeof = 16
```

**Rule**: Order members large → small for minimal padding.

## offsetof Macro
```cpp showLineNumbers
#include <cstddef>

struct Point {
    int x;
    int y;
};

size_t x_offset = offsetof(Point, x);  // 0
size_t y_offset = offsetof(Point, y);  // 4
```

See [Padding and offsetof](03-padding-and-offsetof.md) for details.

## POD and Standard Layout
```cpp showLineNumbers
// POD (Plain Old Data) - C++03
struct POD {
    int x;
    double y;
    // No virtuals, all public, no constructors
};

// Standard Layout - C++11 (more flexible)
struct StandardLayout {
    int x;
private:
    double y;
public:
    StandardLayout() : x(0), y(0.0) {}  // OK
    // No virtuals, same access for all members
};

static_assert(std::is_standard_layout_v<StandardLayout>);
```

**Standard layout** guarantees compatible C layout for first member.

## Compiler-Specific Layouts

Different compilers may use different layouts (ABI differences):
```cpp showLineNumbers
class Widget {
    virtual void foo();
    int data;
};

// GCC/Clang (Itanium ABI): [vptr][data]
// MSVC: may differ in alignment/padding
```

## Controlling Layout
```cpp showLineNumbers
// Explicit packing (GCC/Clang)
struct __attribute__((packed)) Packed {
    char c;
    int i;   // Misaligned!
};  // sizeof = 5 (no padding)

// MSVC
#pragma pack(push, 1)
struct Packed {
    char c;
    int i;
};
#pragma pack(pop)
```

⚠️ **Warning**: Packed structs cause slow/unsafe memory access. See [Alignment](../05-memory-and-object-lifetime/alignment.md).

## Summary

:::info
Objects contain:
- `vptr` to `vtable` (if virtual functions) - 8 bytes
- Data members (in declaration order)
- Padding (alignment)
- Base class subobjects (if inheritance)
---
- Size formula: `vptr` + members + padding (aligned to largest member)
- Multiple inheritance → multiple `vptr`s
- Virtual inheritance → shared base at end
:::

Use `offsetof` to query member positions. POD and standard layout types have predictable C-compatible layouts.

```cpp
// Interview answer:
// "Object layout: members in declaration order plus alignment
// padding. Virtual functions add vptr (8 bytes) pointing to
// vtable. Single inheritance: base subobject first. Multiple
// inheritance: multiple vptrs for multiple bases. Virtual
// inheritance: shared base stored separately. Minimize padding
// by ordering members large to small. Standard layout types
// have C-compatible layout for first member."
```