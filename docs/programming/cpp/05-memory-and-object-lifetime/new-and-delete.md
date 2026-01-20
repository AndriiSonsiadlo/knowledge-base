---
id: new-and-delete
title: new and delete Operators
sidebar_label: new & delete
sidebar_position: 5
tags: [c++, new, delete, dynamic-memory, heap, allocation]
---

# new and delete Operators

The `new` and `delete` operators provide manual dynamic memory management in C++, allocating memory on the heap and requiring explicit deallocation. While modern C++ prefers smart pointers, understanding `new` and `delete` is essential for working with legacy code and implementing resource management.

:::warning Manual Memory Management
Using `new` requires matching `delete` to avoid memory leaks. Modern C++ prefers smart pointers (`std::unique_ptr`, `std::shared_ptr`) which provide automatic cleanup.
:::

## Basic new and delete

The `new` operator allocates memory on the heap and constructs an object in that memory. It returns a pointer to the newly created object that you must eventually delete to avoid memory leaks.

```cpp showLineNumbers 
int* ptr = new int;        // Allocate int (uninitialized)
*ptr = 42;                 // Assign value
delete ptr;                // Deallocate memory
ptr = nullptr;             // Good practice: prevent dangling pointer

// With initialization
int* ptr2 = new int(42);   // Allocate and initialize
delete ptr2;

// Using braces (C++11)
int* ptr3 = new int{42};   // Allocate and initialize
delete ptr3;
```

The `new` operator does two things: it allocates raw memory from the heap (calling `operator new`), then constructs an object in that memory by calling the appropriate constructor. The `delete` operator reverses this process by calling the destructor and then freeing the memory. Every `new` must be paired with exactly one `delete` to avoid leaking memory.

### Initialization Forms

Different initialization forms with `new` produce different results, particularly for fundamental types where the distinction between initialized and uninitialized values matters.

```cpp showLineNumbers 
int* p1 = new int;      // Uninitialized (indeterminate value) ❌
int* p2 = new int();    // Value-initialized (zero)  ✅
int* p3 = new int{};    // Value-initialized (zero)  ✅
int* p4 = new int(42);  // Initialized to 42
int* p5 = new int{42};  // Initialized to 42

std::cout << *p1;  // ❌ Undefined behavior
std::cout << *p2;  // ✅ Safe: 0

delete p1; delete p2; delete p3; delete p4; delete p5;
```

For class types, all forms call the appropriate constructor, so the difference mainly matters for fundamental types. However, using parentheses or braces for value-initialization is always safer than relying on uninitialized memory.

## Array new and delete[]

Dynamic arrays require special syntax with `new[]` and must be deallocated with `delete[]` rather than `delete`. Mixing the single-object and array forms causes undefined behavior.

```cpp showLineNumbers 
int* arr = new int[10];        // Allocate array of 10 ints
arr[0] = 1;
arr[9] = 10;
delete[] arr;                  // ✅ Correct: array delete

// ❌ Wrong way
int* bad = new int[10];
delete bad;  // ❌ Undefined behavior! Memory corrupted
```

The `delete[]` operator knows how to properly destroy all array elements and deallocate the entire array memory. Using `delete` instead of `delete[]` on an array typically only destroys the first element and frees part of the memory, leaving the rest leaked and potentially corrupting the heap's internal structures. This is a common source of hard-to-debug crashes.

### Array Initialization

You can initialize arrays allocated with `new[]` using parentheses or braces. Empty parentheses value-initialize all elements (setting them to zero for fundamental types).

```cpp showLineNumbers 
int* arr1 = new int[5];        // Uninitialized ❌
int* arr2 = new int[5]();      // All zeros ✅  
int* arr3 = new int[5]{};      // All zeros ✅
int* arr4 = new int[5]{1,2,3}; // {1, 2, 3, 0, 0} ✅

std::cout << arr1[0];  // ❌ Undefined behavior
std::cout << arr2[0];  // ✅ Safe: 0

delete[] arr1; delete[] arr2; delete[] arr3; delete[] arr4;
```

Partial initialization fills the specified elements and value-initializes the rest, giving you safe zero values rather than garbage for unspecified elements. This makes `new int[n]{}` the safest form for dynamic array allocation.

## Handling Allocation Failure

By default, if `new` cannot allocate memory, it throws `std::bad_alloc`. You can either catch this exception or use the nothrow form that returns `nullptr` instead.

```cpp showLineNumbers 
try {
    int* huge = new int[1000000000000];  // Impossible allocation
    delete[] huge;
} catch (const std::bad_alloc& e) {
    std::cerr << "Allocation failed: " << e.what() << "\n";
}

// Nothrow form
int* ptr = new (std::nothrow) int[1000];
if (!ptr) {
    std::cerr << "Allocation failed\n";
    // Handle error
} else {
    delete[] ptr;
}
```

The throwing behavior is the default because most code doesn't handle allocation failure anyway (if you can't allocate memory, the program typically can't continue). The nothrow form is useful in specialized contexts like embedded systems or custom memory managers where you want explicit control over failure handling.

## Memory Leaks

Forgetting to `delete` allocated memory causes memory leaks where the program gradually consumes more memory until it crashes or exhausts system resources.

```cpp showLineNumbers 
void leak() {
    int* ptr = new int(42);
    // Forgot to delete! Memory leaked
}

void multiple_leaks() {
    for (int i = 0; i < 1000; ++i) {
        int* ptr = new int(i);
        // Leaks 1000 integers
    }
}

// ✅ Correct
void no_leak() {
    int* ptr = new int(42);
    // Use ptr...
    delete ptr;  // Properly cleaned up
}
```

Memory leaks accumulate over the program's lifetime. Each leaked allocation permanently reduces available memory, eventually causing allocation failures or system slowdowns. Leaked memory is only reclaimed when the process terminates, so long-running programs (servers, GUI applications) are particularly vulnerable to leak-induced crashes.

### Common Leak Patterns

Several patterns commonly cause memory leaks, often involving early returns or exceptions that bypass cleanup code.

```cpp showLineNumbers 
void early_return_leak() {
    int* ptr = new int(42);
    
    if (some_condition) {
        return;  // ❌ Leaks ptr
    }
    
    delete ptr;  // Never reached if early return
}

void exception_leak() {
    int* ptr = new int(42);
    risky_function();  // ❌ If throws, ptr leaked
    delete ptr;        // Never reached if exception thrown
}

// ✅ Solution: RAII with smart pointers
void safe() {
    std::unique_ptr<int> ptr = std::make_unique<int>(42);
    if (some_condition) {
        return;  // ✅ ptr automatically deleted
    }
    // ✅ ptr automatically deleted here too
}
```

Smart pointers solve these problems by tying memory lifetime to object lifetime. When the smart pointer goes out of scope (whether by normal return, early return, or exception), the destructor automatically frees the memory.

## Double Delete

Calling `delete` twice on the same pointer causes undefined behavior, typically corrupting the heap allocator's internal data structures and causing crashes.

```cpp showLineNumbers 
int* ptr = new int(42);
delete ptr;
delete ptr;  // ❌ Undefined behavior! Heap corrupted

// ✅ Solution: Nullify after delete
int* safe_ptr = new int(42);
delete safe_ptr;
safe_ptr = nullptr;
delete safe_ptr;  // ✅ Safe: deleting nullptr is defined as no-op
```

Setting pointers to `nullptr` after deletion prevents double-delete bugs because deleting a null pointer is explicitly defined to do nothing. This defensive programming practice catches many double-delete bugs at runtime instead of corrupting memory.

## Use After Free

Accessing memory after it's been deleted causes undefined behavior. The pointer still points to the memory location, but that memory may have been reused for something else.

```cpp showLineNumbers 
int* ptr = new int(42);
delete ptr;
std::cout << *ptr;  // ❌ Undefined behavior
*ptr = 10;          // ❌ Undefined behavior

// The memory might:
// - Still contain 42 (appears to work, but is wrong)
// - Contain garbage (random values)
// - Cause a crash (if memory was unmapped)
// - Corrupt other data (if memory was reused)
```

Use-after-free bugs are particularly insidious because they often appear to work in testing (the memory still contains the expected value) but fail intermittently in production when memory reuse patterns differ. Tools like AddressSanitizer can detect these bugs during development.

## Placement new

Placement new constructs an object in pre-allocated memory without allocating new memory. This is used for custom memory management and object pools where allocation and construction are separate concerns.

```cpp showLineNumbers 
#include <new>  // For placement new

alignas(int) char buffer[sizeof(int)];  // Raw memory

int* ptr = new (buffer) int(42);  // Construct int in buffer
std::cout << *ptr;  // ✅ Safe: 42

ptr->~int();  // Explicit destructor call
// Don't delete ptr! We didn't allocate with new
```

Placement new calls the constructor on existing memory without allocating. You must call the destructor explicitly because `delete` would try to free memory that wasn't allocated by `new`. This technique is fundamental to custom allocators and memory pools where you want to separate allocation strategy from object construction.

## Custom new and delete

You can overload `operator new` and `operator delete` to customize memory allocation behavior globally or per-class, enabling techniques like memory pooling and debugging instrumentation.

```cpp showLineNumbers 
class Widget {
public:
    // Class-specific allocation
    static void* operator new(size_t size) {
        std::cout << "Widget::new " << size << " bytes\n";
        return ::operator new(size);  // Use global new
    }
    
    static void operator delete(void* ptr) {
        std::cout << "Widget::delete\n";
        ::operator delete(ptr);  // Use global delete
    }
};

Widget* w = new Widget();  // Calls Widget::operator new
delete w;                  // Calls Widget::operator delete
```

Custom allocators are used for performance (memory pools), debugging (tracking allocations), or special requirements (aligned memory, specific memory regions). The ability to customize per-class allows different allocation strategies for different types without affecting the rest of the program.

## Modern Alternatives

Modern C++ code should prefer smart pointers over raw `new`/`delete` because they provide automatic memory management without the risk of leaks or double-deletes.

```cpp showLineNumbers 
// ❌ Old style (error-prone)
int* ptr = new int(42);
// ... must remember to delete
delete ptr;

// ✅ Modern style (automatic cleanup)
auto ptr = std::make_unique<int>(42);
// Automatically deleted when ptr goes out of scope

// Shared ownership
auto shared = std::make_shared<int>(42);
// Reference-counted, deleted when last reference destroyed
```

Smart pointers eliminate entire categories of bugs (leaks, double-deletes, use-after-free) by automatically managing lifetime. The slight overhead is negligible compared to the bugs they prevent. Use `std::unique_ptr` for exclusive ownership and `std::shared_ptr` for shared ownership.

## Summary

The `new` and `delete` operators provide manual heap memory management, requiring paired calls to avoid leaks. Use `new[]` with `delete[]` for arrays, never mixing single-object and array forms. Uninitialized allocations with `new int` leave values indeterminate; use parentheses or braces for value-initialization. Forgetting `delete` causes memory leaks that accumulate over time; calling `delete` twice causes heap corruption and crashes. Setting deleted pointers to `nullptr` prevents double-delete bugs. Placement new constructs objects in pre-existing memory for custom allocation strategies. Modern C++ strongly prefers smart pointers (`std::unique_ptr`, `std::shared_ptr`) over raw `new`/`delete` because they provide automatic memory management without the manual bookkeeping and associated bugs. Only use raw `new`/`delete` when implementing custom memory management or working with legacy code, and always prefer RAII-based smart pointers for application-level code.