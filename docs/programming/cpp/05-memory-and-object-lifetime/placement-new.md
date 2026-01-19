---
id: placement-new
title: Placement new
sidebar_label: Placement new
sidebar_position: 6
tags: [c++, placement-new, memory, construction, advanced]
---

# Placement new

Placement new constructs objects in pre-allocated memory without performing allocation. This low-level facility separates object construction from memory allocation, enabling custom memory management strategies like memory pools, aligned allocations, and stack-based object storage.

:::info Construction Without Allocation
Placement new calls only the constructor on existing memory, giving you full control over where objects are stored. You must manually call the destructor and manage the memory separately.
:::

## Basic Syntax

Placement new takes a pointer to existing memory and constructs an object at that location. The syntax uses parentheses after `new` to pass the memory address where construction should occur.

```cpp
#include <new>  // Required for placement new

alignas(int) char buffer[sizeof(int)];  // Pre-allocated memory

int* ptr = new (buffer) int(42);  // Construct int in buffer
std::cout << *ptr;  // ✅ Works: 42

ptr->~int();  // Explicit destructor call (trivial for int)
// Don't call delete! Memory not allocated by new
```

The placement new expression `new (buffer) int(42)` calls the `int` constructor (which for fundamental types means setting the value) at the memory location pointed to by `buffer`. Unlike normal `new`, this doesn't allocate memory - it assumes the memory at `buffer` is valid and appropriately sized and aligned.

## Memory Requirements

The memory you provide to placement new must meet specific requirements, or you'll invoke undefined behavior. These requirements ensure the constructed object operates correctly.

```cpp
class Widget {
    int data;
public:
    Widget(int d) : data(d) {
        std::cout << "Widget constructed\n";
    }
    ~Widget() {
        std::cout << "Widget destroyed\n";
    }
};

// ✅ Correct: properly aligned and sized
alignas(Widget) char buffer[sizeof(Widget)];
Widget* w = new (buffer) Widget(42);
w->~Widget();

// ❌ Wrong: insufficient size
char small[1];  
Widget* bad = new (small) Widget(42);  // ❌ Undefined behavior!

// ❌ Wrong: misaligned
char unaligned[sizeof(Widget)];
Widget* misaligned = new (unaligned) Widget(42);  // ❌ May crash!
```

The memory must be at least as large as `sizeof(T)` and properly aligned for type `T`. Using `alignas(T)` ensures correct alignment automatically. Insufficient size or improper alignment can cause crashes, data corruption, or subtle bugs depending on the platform and optimization level.

## Explicit Destructor Call

Objects constructed with placement new must have their destructors called explicitly because you can't use `delete` on memory you didn't allocate. The destructor cleans up the object state but doesn't deallocate memory.

```cpp
class Resource {
    int* data;
public:
    Resource() : data(new int[100]) {
        std::cout << "Resource acquired\n";
    }
    ~Resource() {
        delete[] data;
        std::cout << "Resource released\n";
    }
};

alignas(Resource) char buffer[sizeof(Resource)];

Resource* r = new (buffer) Resource();  // Construct
r->~Resource();  // ✅ Explicit destructor call
// buffer still exists, but object is destroyed

// ❌ Wrong: calling delete
// delete r;  // Undefined behavior! buffer not from new
```

The explicit destructor call `r->~Resource()` runs the destructor's cleanup code (releasing the allocated array) but leaves the memory at `buffer` untouched. This separation of object lifetime from memory lifetime is the key feature of placement new.

## Memory Pools

Placement new enables memory pool implementations where you pre-allocate a large block and construct objects within it. This amortizes allocation overhead and improves cache locality.

```cpp
class ObjectPool {
    static constexpr size_t POOL_SIZE = 100;
    alignas(Widget) char pool[POOL_SIZE * sizeof(Widget)];
    bool used[POOL_SIZE] = {};
    
public:
    Widget* allocate() {
        for (size_t i = 0; i < POOL_SIZE; ++i) {
            if (!used[i]) {
                used[i] = true;
                void* slot = pool + i * sizeof(Widget);
                return new (slot) Widget();  // Construct in pool
            }
        }
        return nullptr;  // Pool exhausted
    }
    
    void deallocate(Widget* w) {
        w->~Widget();  // Destroy object
        
        // Find and mark slot as free
        char* base = reinterpret_cast<char*>(w);
        size_t index = (base - pool) / sizeof(Widget);
        used[index] = false;
    }
};
```

The pool allocates a large array once and reuses that memory for multiple objects. Constructing with placement new and explicit destruction allows the pool to control both allocation strategy and object lifecycle independently. This is much faster than heap allocation for small, frequently created objects.

## Stack-Based Objects

Placement new can construct objects on the stack or in any memory region, not just heap memory. This is useful when you want object-like behavior with stack storage duration.

```cpp
void function() {
    // Stack-allocated buffer
    alignas(std::string) char buffer[sizeof(std::string)];
    
    // Construct string in stack memory
    std::string* str = new (buffer) std::string("Hello");
    
    std::cout << *str;  // Works like normal string
    
    str->~std::string();  // Explicit cleanup before stack unwind
}
```

The string object lives in `buffer` which is on the stack, yet you can use all of `std::string`'s member functions normally. The explicit destructor call before the function returns ensures the string is properly cleaned up before its storage is reclaimed by the stack unwind.

## Array Placement New

You can construct arrays using placement new, though this requires careful calculation of offsets and multiple destructor calls.

```cpp
constexpr size_t N = 5;
alignas(Widget) char buffer[N * sizeof(Widget)];

// Construct array
Widget* arr = new (buffer) Widget[N];

// Use array
for (size_t i = 0; i < N; ++i) {
    arr[i].use();
}

// Destroy array (reverse order)
for (size_t i = N; i > 0; --i) {
    arr[i-1].~Widget();
}
```

Array placement new requires you to track the array size yourself since `delete[]` can't be used. You must manually call the destructor for each element in reverse order of construction, matching the behavior of normal array destruction.

## Alignment and Padding

Placement new requires properly aligned memory. Using `alignas` ensures the buffer meets alignment requirements automatically.

```cpp
struct alignas(64) CacheLine {  // 64-byte aligned
    int data[16];
};

// ✅ Properly aligned buffer
alignas(CacheLine) char buffer[sizeof(CacheLine)];
CacheLine* ptr = new (buffer) CacheLine();

// ❌ May be misaligned
char bad_buffer[sizeof(CacheLine)];
CacheLine* bad = new (bad_buffer) CacheLine();  // Might crash!
```

Alignment requirements are platform and type-specific. SSE/AVX types need 16/32-byte alignment; cache-line-optimized structures need 64-byte alignment. Improper alignment can cause crashes on some platforms or severe performance degradation on others. Always use `alignas` to guarantee correct alignment.

## Relocating Objects

Placement new enables object relocation by constructing a copy in new memory and destroying the old one. This is how `std::vector` moves objects during reallocation.

```cpp
void relocate_object() {
    // Original object
    std::string orig("Hello, World!");
    
    // New location
    alignas(std::string) char new_buffer[sizeof(std::string)];
    
    // Move construct in new location
    std::string* relocated = new (new_buffer) std::string(std::move(orig));
    
    // Original is now moved-from but valid
    // relocated contains the data
    
    relocated->~std::string();
}
```

This pattern underlies container growth: allocate new storage, move-construct elements into it, destroy old elements, and deallocate old storage. Placement new gives you the granular control needed to implement this efficiently.

## Reusing Memory

After destructing an object created with placement new, you can reuse the same memory for another object of the same type (or compatible size/alignment).

```cpp
alignas(Widget) char buffer[sizeof(Widget)];

// First use
Widget* w1 = new (buffer) Widget(1);
w1->~Widget();

// Reuse the same memory
Widget* w2 = new (buffer) Widget(2);
w2->~Widget();

// Can even use for different type if compatible
alignas(int) char int_buffer[sizeof(int)];
int* i = new (int_buffer) int(42);
i->~int();

// Reuse for int again
int* i2 = new (int_buffer) int(100);
i2->~int();
```

Memory reuse is fundamental to custom allocators and object pools. The same physical memory can host many different object instances over time, reducing allocation overhead in hot code paths.

## Comparison with Regular new

Understanding the differences between placement new and regular new helps clarify when each is appropriate.

```cpp
// Regular new: allocates + constructs
Widget* w1 = new Widget(42);
delete w1;  // Destroys + deallocates

// Placement new: constructs only
alignas(Widget) char buffer[sizeof(Widget)];
Widget* w2 = new (buffer) Widget(42);
w2->~Widget();  // Destroys only (memory still exists)
```

Regular `new` handles the entire memory lifecycle (allocation through deallocation), while placement new handles only construction and destruction, leaving memory management to you. This separation enables custom allocation strategies but requires more careful programming.

## Common Mistakes

Several common errors can cause crashes or subtle bugs when using placement new incorrectly.

```cpp
// ❌ Calling delete on placement new
alignas(Widget) char buffer[sizeof(Widget)];
Widget* w = new (buffer) Widget();
delete w;  // ❌ Undefined behavior! buffer not from new

// ❌ Insufficient buffer size
char small[1];
Widget* bad = new (small) Widget();  // ❌ Buffer overflow

// ❌ Not calling destructor
alignas(Widget) char buffer[sizeof(Widget)];
{
    Widget* w = new (buffer) Widget();
}  // ❌ Destructor never called! Resources leaked

// ❌ Reusing memory without destroying
Widget* w1 = new (buffer) Widget(1);
Widget* w2 = new (buffer) Widget(2);  // ❌ Didn't destroy w1!
```

Always ensure buffers are properly sized and aligned, always call destructors explicitly, and never use `delete` on objects constructed with placement new. These rules are essential for correct placement new usage.

## Summary

Placement new constructs objects in pre-allocated memory without performing allocation, enabling custom memory management strategies. The syntax `new (ptr) T(args)` constructs a `T` object at the address `ptr`, which must be properly sized (`sizeof(T)`) and aligned (`alignas(T)`). Objects created with placement new require explicit destructor calls and cannot be deleted with `delete` since the memory wasn't allocated by `new`. This facility enables memory pools, stack-based object storage, and custom allocators by separating construction from allocation. Common use cases include performance-critical code that benefits from pre-allocated memory pools and container implementations that need fine control over object lifecycle. However, placement new requires careful programming to avoid buffer overflows, misalignment, and resource leaks from missing destructor calls. Modern code rarely needs placement new directly except when implementing low-level memory management or interfacing with custom allocators, but understanding it is essential for knowing how containers and allocators work internally.