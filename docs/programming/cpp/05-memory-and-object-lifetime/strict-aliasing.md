---
id: strict-aliasing
title: Strict Aliasing Rule
sidebar_label: Strict Aliasing
sidebar_position: 8
tags: [c++, strict-aliasing, type-punning, undefined-behavior, optimization]
---

# Strict Aliasing Rule

The strict aliasing rule states that pointers of different types cannot point to the same memory location (with specific exceptions). This rule allows compilers to assume pointers of unrelated types don't alias, enabling aggressive optimizations. Violating this rule causes undefined behavior.

:::danger Undefined Behavior
Accessing an object through a pointer of an incompatible type is undefined behavior, even though it often appears to work. The compiler may assume no aliasing and generate incorrect code.
:::

## The Rule

An object's stored value may only be accessed through an lvalue of certain compatible types. Accessing it through an incompatible type is undefined behavior, even if the memory contains a valid representation.

```cpp
int x = 42;
float* fp = reinterpret_cast<float*>(&x);

// ❌ Undefined behavior: accessing int through float*
float f = *fp;  // Not guaranteed to work correctly
```

The compiler assumes an `int*` and `float*` never point to the same memory. Based on this assumption, it might reorder or optimize operations in ways that break when pointers actually do alias. The program might work in debug builds but fail with optimizations enabled.

## Why the Rule Exists

Strict aliasing enables important compiler optimizations. If the compiler knows two pointers cannot alias, it can reorder operations and cache values in registers without worrying about one pointer modifying what the other points to.

```cpp
void optimize_example(int* a, float* b) {
    *a = 1;
    *b = 2.0f;
    *a = 3;  // Compiler can eliminate the first assignment to *a
             // because it "knows" b can't point to the same memory
}

// With strict aliasing: only one write to *a
// Without strict aliasing: must perform both writes (slower)
```

The compiler can eliminate the first assignment because it assumes `b` cannot point to the same memory as `a`. If they could alias, both writes would be necessary. These optimizations accumulate across a program, providing significant performance gains.

## Allowed Aliasing

The rule permits several specific forms of aliasing that are necessary for common programming patterns and language features.

```cpp
struct Widget {
    int x;
    char c;
};

Widget w;
Widget* wp = &w;       // ✅ Same type
void* vp = &w;         // ✅ void* can alias anything
char* cp = (char*)&w;  // ✅ char*/unsigned char* can alias anything

// Accessing through compatible types
int* ip = &w.x;        // ✅ Pointer to member
*ip = 42;
```

These exceptions exist for practical reasons: `void*` is used for generic memory manipulation; `char*` is used for byte-wise memory access (like `memcpy`); and pointers to members are necessary for struct access. Without these exceptions, many fundamental C++ patterns would be impossible.

### Compatible Types

Certain type relationships permit aliasing because they're defined to be compatible or have special language support.

```cpp
// ✅ Signed and unsigned variants
int x;
unsigned int* up = (unsigned int*)&x;  // Allowed
*up = 42;

// ✅ Base and derived class (inheritance)
struct Base { int b; };
struct Derived : Base { int d; };
Derived obj;
Base* bp = &obj;  // Allowed (standard conversion)

// ✅ const and non-const versions
int x;
const int* cp = &x;  // Allowed
```

## Type Punning Violations

Type punning means reinterpreting memory as a different type. Most forms of type punning violate strict aliasing and cause undefined behavior.

```cpp
// ❌ Classic type-punning violation
int x = 42;
float* fp = (float*)&x;
float f = *fp;  // Undefined behavior

// ❌ Array trick
int array[1] = {42};
float* fp = (float*)array;
float f = *fp;  // Still undefined behavior
```

Even though the memory representations might be compatible (both are 4-byte values), the compiler is free to assume the `float*` and `int` don't alias. Optimizations based on this assumption can cause the read to see a stale value or get completely optimized away.

## Consequences of Violation

Violating strict aliasing can cause different behaviors depending on optimization level, making bugs extremely difficult to debug.

```cpp
void demonstrate_violation() {
    int x = 42;
    float* fp = reinterpret_cast<float*>(&x);
    
    x = 100;
    float f = *fp;  // Might see 42 or 100 or garbage!
    
    // Compiler might reorder these or cache x in a register
    // because it thinks fp cannot affect x
}
```

With optimizations disabled, this might work because the compiler performs operations in source order. With optimizations enabled, the compiler might cache `x` in a register, making the read through `fp` see the old value. The behavior is unpredictable and depends on compiler version and optimization settings.

## Safe Type Punning Methods

C++ provides several safe ways to reinterpret memory when you actually need type punning functionality.

### Using memcpy

The `memcpy` approach is the standard-blessed way to reinterpret bits as another type. The compiler recognizes this pattern and optimizes it efficiently.

```cpp
int x = 42;
float f;

// ✅ Safe type punning
std::memcpy(&f, &x, sizeof(float));
// f now contains the bit pattern of x interpreted as float

// Modern compilers optimize this to a simple copy
// No actual function call in optimized builds
```

This works because `memcpy` operates on the storage (bytes) rather than the objects themselves, sidestepping strict aliasing. The compiler typically optimizes `memcpy` of small, known sizes to a simple register move.

### Using Unions (C++11 onward)

C++11 allows type punning through unions as a special case, though it's not guaranteed to work for all types and some compilers issue warnings.

```cpp
union IntFloat {
    int i;
    float f;
};

// ✅ Type punning through union (C++11 extension)
IntFloat u;
u.i = 42;
float f = u.f;  // Access different member - technically allowed

// Some compilers may warn about this
```

Accessing a different union member than the one last written is technically undefined in C++, but many compilers support it as an extension for type punning. However, `memcpy` is more portable.

### Using std::bit_cast (C++20)

C++20 introduces `std::bit_cast` as the official, type-safe way to reinterpret object representations.

```cpp
#include <bit>

int x = 42;

// ✅ C++20 type-safe reinterpretation
float f = std::bit_cast<float>(x);

// Requirements: source and destination must be same size
// and trivially copyable
static_assert(sizeof(int) == sizeof(float));
```

`std::bit_cast` provides a type-safe, constexpr-capable interface for bit reinterpretation. It fails at compile-time if types are incompatible (different sizes or non-trivially-copyable), preventing many type-punning bugs.

## Pointer-Based Aliasing

Even without dereferencing, just creating an aliasing pointer can cause undefined behavior in optimized code.

```cpp
void dangerous(int* a, float* b) {
    *a = 1;
    *b = 2.0f;
    *a = *a + 1;  // Compiler assumes *a is still 1
                  // Optimizes to: *a = 2
}

int x;
float* fp = (float*)&x;
dangerous(&x, fp);  // Undefined behavior - violates strict aliasing
// Expected: x = 2
// Actual: unpredictable - might be 2, might be 1
```

The compiler assumes `a` and `b` point to different memory and optimizes based on this. When they actually alias, these optimizations produce wrong results.

## Debugging Aliasing Violations

Compiler flags can help detect some aliasing violations, though not all can be caught at compile-time.

```bash
# GCC/Clang warnings
g++ -O2 -Wstrict-aliasing=2 program.cpp

# Disable strict aliasing optimization (slower but safer)
g++ -O2 -fno-strict-aliasing program.cpp

# Sanitizers can sometimes catch violations
g++ -O2 -fsanitize=undefined program.cpp
```

The `-Wstrict-aliasing` warning catches some violations at compile-time, though many are only detectable at runtime. Disabling strict aliasing optimization (`-fno-strict-aliasing`) makes violations "work" but sacrifices performance. Use this temporarily to debug suspected aliasing issues, not in production code.

## Real-World Example

A common pitfall occurs when trying to inspect bytes of a structure or when implementing serialization.

```cpp
// ❌ Wrong way to access bytes
struct Data {
    int x;
    float y;
};

Data d;
int* ip = (int*)&d.y;  // ❌ Undefined behavior
*ip = 42;

// ✅ Right way to access bytes
char* bytes = reinterpret_cast<char*>(&d);
// Can safely access d through char* (special exception)
for (size_t i = 0; i < sizeof(d); ++i) {
    process_byte(bytes[i]);
}
```

The `char*` exception exists specifically to enable byte-level memory manipulation. This is how `memcpy`, `memset`, and serialization functions work - they operate on memory as a sequence of bytes rather than typed objects.

## Summary

The strict aliasing rule prohibits accessing an object through a pointer of incompatible type, allowing compilers to assume pointers of different types don't alias and enabling aggressive optimizations. Violating this rule causes undefined behavior that often manifests only with optimizations enabled, making bugs difficult to find. The rule permits specific exceptions: same type, `char*`/`unsigned char*` (byte access), `void*` (generic pointers), signed/unsigned variants, and inheritance relationships. Most type punning violates strict aliasing; safe methods include `std::memcpy` (works everywhere), unions (C++11 extension), and `std::bit_cast` (C++20). When you need to reinterpret bits, always use one of these safe methods rather than pointer casts. The rule exists because strict aliasing enables significant compiler optimizations - assuming no aliasing lets the compiler cache values in registers and reorder operations. Compiler warnings (`-Wstrict-aliasing`) catch some violations, and `-fno-strict-aliasing` disables the optimization if needed for debugging. Understanding strict aliasing is essential for writing correct low-level C++ code that works reliably across optimization levels and compiler versions.