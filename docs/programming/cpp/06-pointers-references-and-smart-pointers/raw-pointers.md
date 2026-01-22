---
id: raw-pointers
title: Raw Pointers
sidebar_label: Raw Pointers
sidebar_position: 1
tags: [c++, pointers, memory, addresses, fundamentals]
---

# Raw Pointers

A pointer is a variable that stores a memory address, allowing indirect access to other variables.

:::info Core Concept
**Pointer = Address**, not the data itself
- `&` gets address → `&x` gives address of x
- `*` dereferences → `*ptr` accesses value at address
- Pointers enable dynamic memory, data structures, polymorphism
:::

## Memory Representation
```
Stack Memory:
┌─────────────┐
│ value: 42   │ ← Address: 0x1000
├─────────────┤
│ ptr: 0x1000 │ ← Stores address of value
└─────────────┘

*ptr = 42  (dereferences to get value)
ptr = 0x1000  (the address itself)
```

## Pointer Basics

Pointers hold memory addresses as their values. You create pointers using the `*` symbol in the declaration, and you access what they point to using the dereference operator `*`.

```cpp showLineNumbers
int value = 42;
int* ptr = &value;      // ptr stores address of value

// Three ways to interact with pointers:
std::cout << ptr;       // Address: 0x7fff5fbff5ac
std::cout << *ptr;      // Dereference: 42
std::cout << &ptr;      // Address of pointer itself

*ptr = 100;             // Modify through pointer
std::cout << value;     // 100 (changed!)
```

:::warning Declaration Syntax
```cpp
int* p1, p2;    // ⚠️ p1 is pointer, p2 is int!
int *p3, *p4;   // ✅ Both are pointers
int* p5;        // ✅ Best: one per line
int* p6;
```
:::

## Null Pointers

A null pointer doesn't point to any valid object. Always check pointers before dereferencing to avoid crashes.

```cpp showLineNumbers 
int* bad;            // garbage address
int* ptr = nullptr;  // C++11: null pointer literal

if (ptr) {
    *ptr = 42;  // ✅ Safe: checked first
}
*ptr = 42;      // ❌ Crash! Dereferencing null pointer
```

:::warning Rules
- `nullptr` is type-safe null (C++11)
- Dereferencing null = crash (segmentation fault)
- Uninitialized pointers are worse (random corruption)
:::

## Pointer Operations

Pointers support several operations beyond basic dereferencing, including member access and address arithmetic for adjacent memory.

```cpp showLineNumbers 
struct Point {
    int x, y;
};

Point p = {10, 20};
Point* ptr = &p;

// Member access
(*ptr).x = 30;      // Dereference then access (verbose)
ptr->x = 30;        // Arrow operator (preferred)

std::cout << ptr->x;  // Prints 30
```

### Pointer Comparison

Pointers can be compared to check if they point to the same location or to compare their relative positions in memory.

```cpp showLineNumbers 
int a = 10, b = 20;
int* p1 = &a;
int* p2 = &a;
int* p3 = &b;

if (p1 == p2) {  // ✅ True: both point to a
    std::cout << "Same address\n";
}

if (p1 != p3) {  // ✅ True: point to different objects
    std::cout << "Different addresses\n";
}
```

## Pointers and Arrays

Array names decay to pointers to their first element in most contexts. This allows passing arrays to functions efficiently but loses size information.

```cpp showLineNumbers 
int arr[5] = {1, 2, 3, 4, 5};
int* ptr = arr;  // Decays to pointer to first element

std::cout << *ptr;      // 1 (first element)
std::cout << *(ptr+1);  // 2 (second element)
std::cout << ptr[2];    // 3 (subscript works on pointers)

// Array name is (mostly) equivalent to pointer
arr[2];    // 3
*(arr+2);  // 3 (same thing)
```

### Array vs Pointer Differences

Despite appearing similar, arrays and pointers are different types with different semantics, particularly regarding `sizeof` and assignment.

```cpp showLineNumbers 
int arr[5] = {1, 2, 3, 4, 5};
int* ptr = arr;

sizeof(arr);  // 20 bytes (5 * 4)
sizeof(ptr);  // 8 bytes (pointer size on 64-bit)

// arr = ptr;  // ❌ Error: can't assign to array
ptr = arr;     // ✅ OK: pointer can be reassigned
```

:::info Array-Pointer Relationship
`ptr[i]` is identical to `*(ptr + i)`
- Compiler scales by `sizeof(type)` automatically
- `ptr + 1` moves by 4 bytes for `int*`, not 1 byte
:::

## Dynamic Memory

Pointers are essential for dynamic memory allocation on the heap, where object lifetimes extend beyond their creating scope.

```mermaid
graph LR
    A[Stack: ptr] -->|points to| B[Heap: object]
    B -.->|must manually| C[delete]
    style B fill:#ffcccc
    style C fill:#ff6666
```

```cpp showLineNumbers
// Allocation
int* ptr = new int(42);     // Single object
int* arr = new int[100];    // Array

// Usage
*ptr = 100;
arr[0] = 10;

// Cleanup - YOUR RESPONSIBILITY
delete ptr;      // Single object
delete[] arr;    // Array (must match allocation!)
```

:::danger Memory Management Rules
- **Every `new` needs matching `delete`**
- **Every `new[]` needs matching `delete[]`**
- Missing `delete` = memory leak
- Wrong delete form = undefined behavior
- Double delete = crash
:::

## Common Dangers

### Dangling Pointers
A dangling pointer points to memory that has been deallocated or is no longer valid. Dereferencing creates undefined behavior.

```cpp showLineNumbers 
int* dangling = new int(42);
delete dangling;
*dangling = 100;  // ❌ Undefined behavior: use-after-free

// Set to null after delete to catch errors
delete dangling;
dangling = nullptr;
if (dangling) {
    *dangling = 100;  // Won't execute
}
```

### Returning Pointers to Locals

Returning a pointer to a local variable creates a dangling pointer because locals are destroyed when the function returns.

```cpp showLineNumbers 
int* dangerous() {
    int x = 42;
    return &x;  // ❌ Dangling: x destroyed when function returns
}

int* ptr = dangerous();
*ptr = 100;  // ❌ Undefined behavior

// ✅ Correct: return pointer to dynamic memory
int* safe() {
    return new int(42);  // Caller must delete
}
```

### Use-After-Free
```cpp showLineNumbers
int* ptr = new int(42);
delete ptr;
*ptr = 100;     // ❌ Undefined behavior

// Solution: nullify after delete
delete ptr;
ptr = nullptr;  // ✅ Now safe to check
if (ptr) {
    *ptr = 100; // Won't execute
}
```

### Memory Leaks
```cpp showLineNumbers
void leak() {
    int* ptr = new int(42);
    // ❌ Never deleted - memory leaked
}

void correct() {
    int* ptr = new int(42);
    // Use ptr...
    delete ptr;  // ✅ Cleaned up
}
```

## Pointer to Pointer

Pointers can point to other pointers, creating multiple levels of indirection useful for modifying pointers themselves or creating 2D structures.

```cpp showLineNumbers 
int value = 42;
int* ptr = &value;
int** ptr_to_ptr = &ptr;  // Pointer to pointer

std::cout << **ptr_to_ptr;  // 42 (double dereference)
**ptr_to_ptr = 100;         // Modifies value through double indirection
std::cout << value;         // 100

// Common use: modifying a pointer
void allocate(int** pp) {
    *pp = new int(42);  // Modifies caller's pointer
}

int* p = nullptr;
allocate(&p);  // p now points to allocated memory
```

Double pointers are particularly useful when you need a function to allocate memory and modify the caller's pointer variable. The function receives the address of the pointer variable itself, allowing it to change where that pointer points.

## Void Pointers

A `void*` is a generic pointer that can point to any type but must be cast before dereferencing. It's used for type-agnostic memory operations.

```cpp showLineNumbers 
int x = 42;
void* vptr = &x;  // Can point to anything

// *vptr;  // ❌ Error: can't dereference void*
int* iptr = static_cast<int*>(vptr);  // Cast back to specific type
*iptr = 100;  // ✅ OK after cast

// Used in C APIs
void* memcpy(void* dest, const void* src, size_t n);
```

## Function Pointers

Pointers can store addresses of functions, enabling callbacks, plugin systems, and strategy patterns.

```cpp showLineNumbers 
int add(int a, int b) { return a + b; }
int subtract(int a, int b) { return a - b; }

// Function pointer declaration
int (*operation)(int, int);

operation = add;
std::cout << operation(5, 3);  // 8

operation = subtract;
std::cout << operation(5, 3);  // 2

// Modern alternative: std::function (better)
std::function<int(int, int)> op = add;
```

Function pointer syntax is notoriously difficult to read: `int (*ptr)(int, int)` declares a pointer to a function taking two ints and returning int. Modern C++ prefers `std::function` which provides a cleaner syntax and can store lambdas, not just function pointers.

:::success Key Insights

**Memory Address**: Pointers store addresses, not values. The value lives elsewhere.

**Dereferencing**: `*ptr` follows the address to access the actual data.

**Null Safety**: Always initialize to `nullptr` and check before dereferencing.

**Ownership**: Who `delete`s the memory? Unclear with raw pointers → use smart pointers.

**Lifetime**: Pointers don't extend object lifetime. Locals die at scope end even if pointers exist.
:::

## Summary

**Core concepts:**
- Pointer = variable storing memory address
- `*` dereferences, `&` gets address
- `nullptr` for null, always initialize

**Memory management:**
- `new` allocates, `delete` frees
- `new[]` with `delete[]` for arrays
- Missing delete = leak, double delete = crash

**Dangers:**
- Dangling pointers (pointing to destroyed data)
- Use-after-free (accessing deleted memory)
- Memory leaks (forgetting to delete)
- Uninitialized pointers (garbage addresses)

**Modern practice:**
- Use smart pointers (`unique_ptr`, `shared_ptr`)
- Raw pointers only for non-owning references
- Let compiler manage lifetime automatically
