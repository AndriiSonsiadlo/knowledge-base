---
id: raw-pointers
title: Raw Pointers
sidebar_label: Raw Pointers
sidebar_position: 1
tags: [c++, pointers, memory, addresses, fundamentals]
---

# Raw Pointers

A pointer is a variable that stores a memory address, allowing indirect access to other variables. Pointers provide the foundation for dynamic memory, data structures, and polymorphism, but require careful management to avoid crashes and memory leaks.

:::info Core Concept
A pointer **stores an address** where data lives, not the data itself. Dereferencing (`*ptr`) accesses the actual value at that address.
:::

## Pointer Basics

Pointers hold memory addresses as their values. You create pointers using the `*` symbol in the declaration, and you access what they point to using the dereference operator `*`.

```cpp
int value = 42;
int* ptr = &value;  // ptr stores the address of value

std::cout << ptr;    // Prints address (e.g., 0x7fff5fbff5ac)
std::cout << *ptr;   // Dereferences: prints 42
*ptr = 100;          // Modifies value through pointer
std::cout << value;  // Prints 100 (changed via pointer)
```

The `&` operator (address-of) gets the memory address of a variable. The pointer stores this address. Dereferencing with `*` follows the address to access the actual data stored there. This indirection lets you modify variables through pointers, which is fundamental to many C++ patterns like passing by reference and dynamic memory.

### Declaration Syntax

The placement of `*` in declarations is stylistic, but understanding the declaration reading rules helps avoid confusion with multiple pointers.

```cpp
int* p1;        // Pointer to int (common style)
int *p2;        // Pointer to int (alternative style)
int* p3, p4;    // ⚠️ p3 is pointer, p4 is int! (confusing)
int *p5, *p6;   // Both are pointers (clearer with *)
int* p7, *p8;   // Both are pointers (mixed style)

// Best practice: one declaration per line
int* ptr1;
int* ptr2;
```

The `*` binds to the variable name, not the type, which is why `int* p3, p4` only makes `p3` a pointer. This syntactic quirk causes bugs when multiple variables are declared on one line. Modern practice prefers one pointer per line to avoid ambiguity.

## Null Pointers

A null pointer doesn't point to any valid object. Always check pointers before dereferencing to avoid crashes.

```cpp
int* ptr = nullptr;  // C++11: null pointer literal

if (ptr) {
    *ptr = 42;  // ✅ Safe: checked first
}

if (ptr != nullptr) {
    *ptr = 42;  // ✅ Explicit null check
}

*ptr = 42;  // ❌ Crash! Dereferencing null pointer
```

Dereferencing a null pointer is undefined behavior that typically causes a segmentation fault (crash). The `nullptr` keyword (C++11) provides a type-safe null value that can't accidentally convert to integers like the old `NULL` macro could. Always initialize pointers to `nullptr` when you don't have a valid address yet, and check before dereferencing.

### Uninitialized Pointers

Uninitialized pointers contain garbage addresses and are extremely dangerous. They might "work" by pointing to valid memory, making bugs hard to find.

```cpp
int* bad_ptr;        // ❌ Uninitialized: contains garbage
*bad_ptr = 42;       // ❌ Crashes or corrupts memory

int* good_ptr = nullptr;  // ✅ Explicitly null
if (good_ptr) {
    *good_ptr = 42;  // Won't execute, no crash
}
```

An uninitialized pointer might contain an address that happens to be valid memory, silently corrupting data elsewhere in your program. This is worse than a crash because the bug isn't immediately obvious. Always initialize pointers, even if just to `nullptr`.

## Pointer Operations

Pointers support several operations beyond basic dereferencing, including member access and address arithmetic for adjacent memory.

```cpp
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

The arrow operator `->` combines dereferencing and member access: `ptr->x` is shorthand for `(*ptr).x`. This is the idiomatic way to access members through pointers and makes code more readable than explicit dereferencing.

### Pointer Comparison

Pointers can be compared to check if they point to the same location or to compare their relative positions in memory.

```cpp
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

if (p1 < p3) {  // Compares addresses (rarely useful)
    // Only meaningful for array elements
}
```

Pointer equality checks if two pointers point to the same object, which is useful for identity comparisons. Relational operators (`<`, `>`) compare addresses numerically, which only makes sense for pointers into the same array or object.

## Pointers and Arrays

Array names decay to pointers to their first element in most contexts. This allows passing arrays to functions efficiently but loses size information.

```cpp
int arr[5] = {1, 2, 3, 4, 5};
int* ptr = arr;  // Decays to pointer to first element

std::cout << *ptr;      // 1 (first element)
std::cout << *(ptr+1);  // 2 (second element)
std::cout << ptr[2];    // 3 (subscript works on pointers)

// Array name is (mostly) equivalent to pointer
arr[2];    // 3
*(arr+2);  // 3 (same thing)
```

The subscript operator `ptr[i]` is syntactic sugar for `*(ptr + i)`, which adds `i` to the pointer and dereferences. This works because arrays are contiguous memory where elements are adjacent. However, you lose the size information when an array decays to a pointer.

### Array vs Pointer Differences

Despite appearing similar, arrays and pointers are different types with different semantics, particularly regarding `sizeof` and assignment.

```cpp
int arr[5] = {1, 2, 3, 4, 5};
int* ptr = arr;

sizeof(arr);  // 20 bytes (5 * 4)
sizeof(ptr);  // 8 bytes (pointer size on 64-bit)

// arr = ptr;  // ❌ Error: can't assign to array
ptr = arr;     // ✅ OK: pointer can be reassigned
```

An array name is a constant pointer-like entity that can't be reassigned. The `sizeof` operator applied to an array gives the total array size, while `sizeof` on a pointer gives the pointer's size (4 or 8 bytes). This distinction matters when passing arrays to functions, where the size information is lost.

## Dynamic Memory

Pointers are essential for dynamic memory allocation on the heap, where object lifetimes extend beyond their creating scope.

```cpp
int* ptr = new int(42);  // Allocate on heap
std::cout << *ptr;       // 42
delete ptr;              // Deallocate

int* arr = new int[100];  // Dynamic array
arr[0] = 10;
delete[] arr;             // Array delete

// ❌ Memory leak
int* leak = new int(42);
// Never deleted! Memory leaked
```

Dynamic allocation returns a pointer to heap memory that persists until explicitly deleted. Forgetting `delete` causes memory leaks that accumulate over time. Using `delete[]` for arrays is crucial because `delete` only deallocates the first element, leaking the rest.

## Dangling Pointers

A dangling pointer points to memory that has been deallocated or is no longer valid. Dereferencing creates undefined behavior.

```cpp
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

After deletion, the pointer still holds the address, but the memory is no longer valid for your use. Accessing it might work initially (the memory might not be reused yet), crash, or corrupt other data. Setting pointers to `nullptr` after deletion is defensive programming that converts silent corruption into a detectable crash.

### Returning Pointers to Locals

Returning a pointer to a local variable creates a dangling pointer because locals are destroyed when the function returns.

```cpp
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

Local variables live on the stack and are destroyed at the end of their scope. Returning their addresses gives the caller a pointer to memory that will be reused for other purposes. This is a common source of subtle bugs that appear to work sometimes but fail unpredictably.

## Pointer to Pointer

Pointers can point to other pointers, creating multiple levels of indirection useful for modifying pointers themselves or creating 2D structures.

```cpp
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

```cpp
int x = 42;
void* vptr = &x;  // Can point to anything

// *vptr;  // ❌ Error: can't dereference void*
int* iptr = static_cast<int*>(vptr);  // Cast back to specific type
*iptr = 100;  // ✅ OK after cast

// Used in C APIs
void* memcpy(void* dest, const void* src, size_t n);
```

You lose type information with `void*`, so the compiler can't perform type checking or know the pointed-to object's size. This makes `void*` useful for implementing generic containers in C but error-prone. Modern C++ prefers templates for type-safe generic programming.

## Function Pointers

Pointers can store addresses of functions, enabling callbacks, plugin systems, and strategy patterns.

```cpp
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

Raw pointers are variables storing memory addresses that enable indirect access to data. The dereference operator `*` accesses the value at the address, while `&` gets an object's address. Null pointers (`nullptr`) don't point to valid memory and must be checked before dereferencing. Uninitialized pointers contain garbage and cause undefined behavior. The arrow operator `->` accesses members through pointers conveniently. Arrays decay to pointers but lose size information. Dynamic memory allocated with `new` must be deallocated with `delete` to avoid leaks. Dangling pointers point to deallocated memory and cause use-after-free bugs. Setting pointers to `nullptr` after `delete` catches these errors. Double pointers enable modifying pointers in functions. `void*` provides type-agnostic pointers but requires casting. Function pointers enable callbacks but have complex syntax. Modern C++ prefers smart pointers (`unique_ptr`, `shared_ptr`) over raw pointers because they provide automatic memory management and clear ownership semantics. Use raw pointers only for non-owning references or when interfacing with C APIs. The fundamental pointer operations are: declaration (`int* ptr`), addressing (`&var`), dereferencing (`*ptr`), member access (`ptr->member`), and null checking (`if (ptr)`). Understanding these operations is essential for C++ programming, though modern code increasingly uses references and smart pointers for safety.