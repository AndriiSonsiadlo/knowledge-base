---
id: const-pointers
title: const Pointers
sidebar_label: const Pointers
sidebar_position: 4
tags: [c++, pointers, const, immutability]
---

# const Pointers

The `const` qualifier with pointers creates three distinct scenarios: pointer to const data, const pointer to data, and const pointer to const data. Understanding these combinations is essential for expressing immutability guarantees and intent.

:::info Reading const Declarations
Read declarations right-to-left: `const int* ptr` = "ptr is a pointer to const int". `int* const ptr` = "ptr is a const pointer to int".
:::

## Pointer to const

A pointer to const cannot modify the pointed-to data, but the pointer itself can be reassigned to point elsewhere.

```cpp
int x = 10, y = 20;
const int* ptr = &x;  // Pointer to const int

// *ptr = 30;  // ❌ Error: cannot modify through pointer
ptr = &y;      // ✅ OK: can change what we point to

x = 30;        // ✅ OK: x itself is modifiable
std::cout << *ptr;  // 20 (ptr now points to y)
```

The `const` protects the data from modification through this particular pointer, but the data itself might not be const. Other pointers or direct access to `x` can still modify it. This is useful for function parameters that should read but not write the argument.

### Alternative Syntax

Both `const int*` and `int const*` mean the same thing: pointer to const int. The const applies to the int, not the pointer.

```cpp
const int* ptr1 = &x;  // Pointer to const int
int const* ptr2 = &x;  // Same thing (const after type)

// Both are equivalent - matter of style preference
// *ptr1 = 10;  // ❌ Error
// *ptr2 = 10;  // ❌ Error
```

The first form (`const int*`) is more common, but the second form (`int const*`) makes the right-to-left reading rule more consistent. Choose one style and use it consistently in your codebase.

## const Pointer

A const pointer always points to the same object but allows modifying that object's value.

```cpp
int x = 10, y = 20;
int* const ptr = &x;  // const pointer to int

*ptr = 30;     // ✅ OK: can modify what we point to
std::cout << x;     // 30

// ptr = &y;   // ❌ Error: cannot change where pointer points
```

The pointer is const (can't be reassigned), but the data isn't const (can be modified). This is less common but useful when you need a pointer that always refers to the same object, like a permanent reference to an object.

### Use Cases

Const pointers are useful when you want a pointer with reference-like "cannot be reseated" semantics but need actual pointer behavior.

```cpp
class Widget {
    int* const internal_ptr;  // Always points to same allocation
    
public:
    Widget(int* p) : internal_ptr(p) {
        // internal_ptr cannot be changed after initialization
    }
    
    void modify() {
        *internal_ptr = 100;  // ✅ Can modify pointed-to value
    }
};
```

Member pointers that should never change what they point to benefit from being const pointers. This documents intent and prevents accidental reassignment bugs.

## const Pointer to const

Both the pointer and the pointed-to data are const. Neither can be changed.

```cpp
int x = 10, y = 20;
const int* const ptr = &x;  // const pointer to const int

// *ptr = 30;  // ❌ Error: cannot modify data
// ptr = &y;   // ❌ Error: cannot change pointer

x = 30;        // ✅ OK: x itself is still modifiable
```

This provides maximum immutability for the pointer. You're promising not to modify the data through this pointer and not to point elsewhere. This is the most restrictive form and clearly communicates read-only intent.

### Reading Complex Declarations

The right-to-left reading rule helps parse complex const declarations correctly.

```cpp
const int* const ptr;
// Read right-to-left: "ptr is a const pointer to const int"

int const* const ptr;  
// Read right-to-left: "ptr is a const pointer to const int"

const int* ptr;
// Read right-to-left: "ptr is a pointer to const int"

int* const ptr;
// Read right-to-left: "ptr is a const pointer to int"
```

The position of `const` relative to `*` determines what's const. Before `*` (or after type) = data is const. After `*` = pointer is const.

## Function Parameters

const pointers in function signatures communicate intent and enable compiler optimizations.

```cpp
// Pointer to const - can't modify through pointer
void read_data(const int* data, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        std::cout << data[i];  // ✅ Can read
        // data[i] = 0;  // ❌ Cannot modify
    }
}

// const pointer - pointer itself won't change
void process(int* const ptr) {
    *ptr = 42;  // ✅ Can modify data
    // ptr = nullptr;  // ❌ Cannot change pointer
}

// Both const
void display(const int* const ptr) {
    std::cout << *ptr;  // ✅ Can read
    // *ptr = 10;  // ❌ Cannot modify
    // ptr = nullptr;  // ❌ Cannot change pointer
}
```

Most commonly, functions take pointer-to-const to indicate they won't modify the argument. The const pointer (second case) is rare for parameters since local copies of pointers can freely be reassigned without affecting the caller.

## Arrays and const

Pointer-to-const works naturally with arrays, preventing modification of array elements.

```cpp
int arr[] = {1, 2, 3, 4, 5};
const int* ptr = arr;  // Pointer to const int

std::cout << ptr[2];  // ✅ Can read: 3
// ptr[2] = 10;  // ❌ Cannot modify through ptr

arr[2] = 10;  // ✅ Array itself is modifiable
std::cout << ptr[2];  // 10 (sees the change)
```

Array subscripting works through pointer-to-const because it's syntactic sugar for pointer arithmetic and dereferencing. The const prevents modification but allows navigation.

## Casting Away const

You can remove const with `const_cast`, but modifying originally-const data is undefined behavior.

```cpp
int x = 10;
const int* cptr = &x;

// Remove const
int* ptr = const_cast<int*>(cptr);
*ptr = 20;  // ✅ OK: x wasn't originally const

// Dangerous!
const int y = 30;
const int* cptr2 = &y;
int* ptr2 = const_cast<int*>(cptr2);
*ptr2 = 40;  // ❌ Undefined behavior: y was const!
```

If the original object was declared const, removing const and modifying it is undefined behavior. However, if the object wasn't originally const and you're just removing const from a pointer, it's safe. Use `const_cast` sparingly and only when interfacing with badly-designed APIs.

## const with Dynamic Memory

const affects what you can do with dynamically allocated memory through the pointer.

```cpp
// Pointer to const on heap
const int* ptr1 = new int(42);
// *ptr1 = 10;  // ❌ Cannot modify
delete ptr1;  // ✅ Can still delete

// const pointer to heap memory
int* const ptr2 = new int(42);
*ptr2 = 10;  // ✅ Can modify
delete ptr2;  // ✅ Can delete

// Both const
const int* const ptr3 = new int(42);
// *ptr3 = 10;  // ❌ Cannot modify
delete ptr3;  // ✅ Can delete
```

The const qualifiers don't prevent deleting the memory, only modification through the pointer. Deletion is a memory management operation, not data modification.

## const Correctness

Using const correctly throughout your code catches bugs at compile-time and documents intent.

```cpp
class Buffer {
    int* data;
    size_t size;
    
public:
    // const accessor - can't modify
    const int* getData() const {
        return data;
    }
    
    // Non-const accessor - can modify
    int* getData() {
        return data;
    }
    
    // const parameter
    void append(const int* values, size_t count) {
        // values won't be modified
    }
};

const Buffer cb;
// const int* ptr = cb.getData();  // Calls const version

Buffer b;
int* ptr = b.getData();  // Calls non-const version
```

Const correctness means using const everywhere possible. This helps the compiler catch bugs where you accidentally modify something, optimizes better (knowing data won't change), and clearly communicates intent to other programmers.

:::warning Common Pitfalls

**Const Placement**: `const int* ptr` vs `int* const ptr` - very different meanings!

**Cannot Cast Away Real const**: Removing const from originally-const data is undefined behavior.

**Low-Level const**: `const int* ptr` doesn't make `int` const everywhere, only through this pointer.

**Implicit Conversion**: Non-const pointer converts to const pointer, not vice versa.
:::

## Summary

Pointers and const combine in three ways: pointer to const data, const pointer, and const pointer to const data. A pointer to const (`const T*` or `T const*`) cannot modify data through the pointer but can point elsewhere. A const pointer (`T* const`) always points to the same object but can modify that object. A const pointer to const (`const T* const`) cannot modify data or change where it points. Read declarations right-to-left: `const int*` reads as "pointer to const int". The position of const relative to `*` determines what's const: before `*` means data is const, after `*` means pointer is const. Function parameters commonly use pointer-to-const to indicate read-only access. Non-const pointers implicitly convert to const pointers but not vice versa. Casting away const with `const_cast` is dangerous and only safe if the underlying object wasn't originally const. Const correctness means using const everywhere applicable - it catches bugs at compile-time, enables optimizations, and documents intent. The compiler enforces const through pointers, preventing modification of const-qualified data. Use const pointers to clearly communicate whether functions will modify arguments, whether pointers will be reassigned, and what the ownership semantics are. Modern practice embraces const correctness as a form of compile-time verification and self-documenting code.

:::success Key Principles

**Three Combinations**: Pointer to const, const pointer, const pointer to const.

**Read Right-to-Left**: `const int* const ptr` = "ptr is const pointer to const int".

**Before `*` = Data const**: After `*` = Pointer const.

**Most Common**: `const T*` for function parameters (won't modify argument).

**Const Correctness**: Use const everywhere possible for safety and clarity.

**One-Way Conversion**: Non-const → const is implicit. Reverse requires cast and is dangerous.
:::