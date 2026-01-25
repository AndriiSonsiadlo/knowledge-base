---
id: new-and-delete
title: new and delete Operators
sidebar_label: new & delete
sidebar_position: 5
tags: [c++, new, delete, dynamic-memory, heap, allocation]
---

# new and delete Operators

Manual dynamic memory management in C++. Allocates on heap, requires explicit deallocation. Modern C++ prefers smart pointers.

:::warning Manual Memory = Manual Cleanup
Every `new` requires exactly one `delete`. Missing = leak. Double = crash. Modern code uses `unique_ptr`/`shared_ptr` instead.
:::

## Basic Usage
```cpp showLineNumbers
// Allocation + construction
int* p = new int;           // Uninitialized ❌
int* p = new int();         // Zero-initialized ✅
int* p = new int{42};       // Direct initialization ✅

delete p;                   // Deallocation + destruction
p = nullptr;                // Prevent dangling pointer
```

**Rule**: `new` = allocate + construct. `delete` = destruct + deallocate.

## Arrays
```cpp showLineNumbers
// Array allocation
int* arr = new int[10];     // Allocate 10 ints
int* arr = new int[10]();   // All zeros ✅
int* arr = new int[10]{1,2,3}; // Partial init {1,2,3,0...0} ✅

delete[] arr;               // ✅ Array delete

// ❌ WRONG
delete arr;                 // Undefined behavior! Use delete[]
```

**Critical**: `new[]` ⟷ `delete[]` and `new` ⟷ `delete`. Never mix.

## Memory Problems

### Memory Leak
```cpp showLineNumbers
void leak() {
    int* p = new int(42);
    return;                 // ❌ Forgot delete - memory leaked
}

// ✅ Fix with RAII
void safe() {
    auto p = std::make_unique<int>(42);
    return;                 // ✅ Auto-deleted
}
```

### Double Delete
```cpp showLineNumbers
int* p = new int(42);
delete p;
delete p;                   // ❌ Undefined behavior - heap corrupted

// ✅ Safe pattern
delete p;
p = nullptr;
delete p;                   // ✅ OK: deleting nullptr is no-op
```

### Use After Free
```cpp showLineNumbers
int* p = new int(42);
delete p;
*p = 10;                    // ❌ Undefined behavior - accessing freed memory
std::cout << *p;            // ❌ May crash, return garbage, or "work"
```

## Allocation Failure
```cpp showLineNumbers
// Default: throws exception
try {
    int* huge = new int[1000000000000];
} catch (const std::bad_alloc& e) {
    std::cerr << "Out of memory\n";
}

// Nothrow: returns nullptr
int* p = new (std::nothrow) int[1000];
if (!p) {
    std::cerr << "Allocation failed\n";
}
```

## Quick Comparison

| Operation | Stack | Heap (`new`) |
|-----------|-------|--------------|
| **Speed** | ~1ns | ~50-100ns |
| **Size** | Limited (1-8MB) | Large (GB) |
| **Lifetime** | Automatic | Manual |
| **Cleanup** | Automatic | `delete` required |
| **Failure** | Stack overflow (crash) | Exception or nullptr |

## Modern Alternatives
```cpp showLineNumbers
// ❌ Old style (manual management)
Widget* w = new Widget();
// ... use w ...
delete w;

// ✅ Modern (automatic management)
auto w = std::make_unique<Widget>();
// Auto-deleted when out of scope

// ✅ Shared ownership
auto shared = std::make_shared<Widget>();
// Deleted when last reference dies
```

**Prefer**: `unique_ptr` > `shared_ptr` > raw `new/delete`

## Common Patterns
```cpp showLineNumbers
// Resource leak with early return
void dangerous() {
    int* p = new int(42);
    if (error) return;      // ❌ Leaks p
    delete p;
}

// Exception safety
void risky() {
    int* p = new int(42);
    might_throw();          // ❌ If throws, p leaks
    delete p;
}

// ✅ Solution: RAII
void safe() {
    auto p = std::make_unique<int>(42);
    if (error) return;      // ✅ Auto-cleaned
    might_throw();          // ✅ Auto-cleaned on exception
}
```

## Key Rules

:::success DO
- Use smart pointers (`unique_ptr`, `shared_ptr`)
- Match `new` with `delete`, `new[]` with `delete[]`
- Set deleted pointers to `nullptr`
- Initialize with `()` or `{}`, not bare `new int`
  :::

:::danger DON'T
- Mix `new/delete` with `new[]/delete[]`
- Delete same pointer twice
- Use after delete
- Forget to delete (use smart pointers instead)
  :::

## Summary

`new` allocates heap memory and constructs objects; `delete` destructs and deallocates. Arrays need `new[]`/`delete[]`. Common errors: memory leaks (missing delete), double delete (heap corruption), use-after-free (undefined behavior). **Modern C++ uses smart pointers** which provide automatic memory management, eliminating these entire bug categories.
```cpp
// Interview answer template:
// "new allocates on heap, requires manual delete. Every new needs
// exactly one matching delete (new[] needs delete[]). Common bugs:
// leaks (forgot delete), double-delete (crash), use-after-free (UB).
// Modern C++ uses unique_ptr/shared_ptr for automatic cleanup via
// RAII, eliminating manual memory management and its associated bugs."
```