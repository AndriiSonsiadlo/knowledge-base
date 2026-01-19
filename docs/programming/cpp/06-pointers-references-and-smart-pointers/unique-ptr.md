---
id: unique-ptr
title: std::unique_ptr
sidebar_label: unique_ptr
sidebar_position: 5
tags: [c++, smart-pointers, unique-ptr, raii, cpp11]
---

# std::unique_ptr

`std::unique_ptr` is a smart pointer that owns and manages an object through a pointer and disposes of that object when the unique_ptr goes out of scope. It provides exclusive ownership semantics with zero runtime overhead compared to raw pointers.

:::info Exclusive Ownership
A `unique_ptr` is the sole owner of its object. It cannot be copied, only moved, ensuring exactly one pointer manages the resource at any time.
:::

## Basic Usage

Creating and using a unique_ptr is straightforward. The managed object is automatically deleted when the unique_ptr is destroyed.

```cpp
#include <memory>

// Create unique_ptr
std::unique_ptr<int> ptr = std::make_unique<int>(42);

// Use like a raw pointer
std::cout << *ptr;      // 42
*ptr = 100;
std::cout << *ptr;      // 100

// Automatically deleted when ptr goes out of scope
```

The key benefit is automatic cleanup: you never call `delete`. The unique_ptr's destructor handles deallocation, preventing memory leaks. This is RAII (Resource Acquisition Is Initialization) - the resource lifetime is tied to object lifetime.

### make_unique (C++14)

Always prefer `std::make_unique` over direct `new` for exception safety and conciseness.

```cpp
// ✅ Preferred: make_unique
auto ptr1 = std::make_unique<int>(42);
auto ptr2 = std::make_unique<std::string>("hello");

// ❌ Avoid: direct new
std::unique_ptr<int> ptr3(new int(42));

// Exception safety example
void risky() {
    process(std::unique_ptr<Widget>(new Widget),  // ❌ Can leak
            std::unique_ptr<Gadget>(new Gadget)); // if second throws
    
    process(std::make_unique<Widget>(),  // ✅ Safe
            std::make_unique<Gadget>());  // No leak possible
}
```

`make_unique` is exception-safe because it creates the object and wraps it in the unique_ptr atomically. With raw `new`, if an exception occurs between allocation and the unique_ptr construction, the memory leaks.

## Exclusive Ownership

unique_ptr cannot be copied because that would create two owners. It can only be moved, transferring ownership.

```cpp
std::unique_ptr<int> ptr1 = std::make_unique<int>(42);

// std::unique_ptr<int> ptr2 = ptr1;  // ❌ Error: cannot copy

std::unique_ptr<int> ptr2 = std::move(ptr1);  // ✅ Transfer ownership
// ptr1 is now nullptr
// ptr2 owns the int

if (!ptr1) {
    std::cout << "ptr1 is empty\n";  // This executes
}
std::cout << *ptr2;  // 42
```

After moving, the source unique_ptr becomes null. This ensures exclusive ownership: at most one unique_ptr owns the object at any time. Moving is cheap (just pointer copy) and makes ownership transfer explicit in code.

### Move Semantics

unique_ptr is move-only, which prevents accidental copies and makes ownership transfer explicit.

```cpp
std::unique_ptr<int> create() {
    auto ptr = std::make_unique<int>(42);
    return ptr;  // Automatically moved (no std::move needed)
}

std::unique_ptr<int> result = create();  // Ownership transferred

void consume(std::unique_ptr<int> ptr) {
    // Takes ownership, will delete when function ends
    std::cout << *ptr;
}

auto p = std::make_unique<int>(100);
consume(std::move(p));  // Explicit transfer
// p is now nullptr
```

Return values are automatically moved, so no explicit `std::move` needed when returning. For function parameters, you must explicitly move to transfer ownership, documenting the ownership transfer at the call site.

## Accessing the Pointer

unique_ptr provides several ways to access the managed pointer for different use cases.

```cpp
auto ptr = std::make_unique<int>(42);

// Dereference
int value = *ptr;        // 42
*ptr = 100;

// Get raw pointer (doesn't transfer ownership)
int* raw = ptr.get();    // Get raw pointer
std::cout << *raw;       // 100
// ptr still owns the object

// Bool conversion (check if not null)
if (ptr) {
    std::cout << "Valid\n";
}

// Arrow operator for member access
auto widget = std::make_unique<Widget>();
widget->doSomething();
```

The `get()` method returns the raw pointer without transferring ownership. This is useful when passing to functions that need a raw pointer but don't take ownership. Never delete the pointer returned by `get()` - the unique_ptr still owns it.

## Releasing Ownership

You can explicitly release ownership, getting the raw pointer and leaving the unique_ptr empty.

```cpp
auto ptr = std::make_unique<int>(42);

int* raw = ptr.release();  // ptr becomes nullptr
// You now own the pointer and must delete it

delete raw;  // Your responsibility now

// After release, ptr is empty
if (!ptr) {
    std::cout << "Empty\n";
}
```

Use `release()` when transferring ownership to code that expects raw pointers (legacy APIs, C libraries). You're responsible for deletion after release. This is rarely needed with modern C++ but necessary when interfacing with older code.

## Resetting

Reset deletes the current object and optionally takes ownership of a new one.

```cpp
auto ptr = std::make_unique<int>(42);

ptr.reset();  // Deletes int(42), ptr becomes nullptr

ptr.reset(new int(100));  // Takes ownership of new int
std::cout << *ptr;  // 100

// Can also reset to nullptr explicitly
ptr.reset(nullptr);  // Equivalent to ptr.reset()
```

Reset is useful when you want to replace the managed object or delete it early without waiting for the unique_ptr to go out of scope. The old object (if any) is deleted before taking ownership of the new one.

## Arrays

unique_ptr has a partial specialization for arrays that calls `delete[]` instead of `delete`.

```cpp
// Single object
auto ptr = std::make_unique<int>(42);

// Array
auto arr = std::make_unique<int[]>(10);  // Array of 10 ints
arr[0] = 1;
arr[9] = 10;

// Don't need delete[] - automatic
```

The array specialization changes the interface slightly: you can use subscript notation but not dereference. However, prefer `std::vector` or `std::array` over unique_ptr to arrays - they provide better interfaces and safety.

### Prefer Containers

For dynamic arrays, standard containers are almost always better than unique_ptr to arrays.

```cpp
// ❌ Using unique_ptr for array
auto arr1 = std::make_unique<int[]>(10);
arr1[5] = 42;
// No size(), no bounds checking, no convenient operations

// ✅ Using vector
std::vector<int> arr2(10);
arr2[5] = 42;
arr2.size();        // Know the size
arr2.push_back(99); // Can grow
arr2.at(5);         // Bounds-checked access
```

unique_ptr to arrays lacks the convenience methods containers provide. Use it only when you need a smart pointer to a C-style array, typically when interfacing with C APIs.

## Custom Deleters

You can provide a custom deleter for non-standard cleanup (we'll cover this in detail in the Custom Deleters section).

```cpp
// Custom deleter for FILE*
auto deleter = [](FILE* f) { 
    if (f) fclose(f); 
};

std::unique_ptr<FILE, decltype(deleter)> file(
    fopen("data.txt", "r"), 
    deleter
);

// File automatically closed when unique_ptr destroyed
```

Custom deleters enable using unique_ptr with resources that aren't heap-allocated (files, sockets, handles) or that need special cleanup beyond `delete`.

## Polymorphism

unique_ptr works seamlessly with polymorphism, properly calling derived class destructors.

```cpp
class Base {
public:
    virtual ~Base() { std::cout << "~Base\n"; }
    virtual void identify() { std::cout << "Base\n"; }
};

class Derived : public Base {
public:
    ~Derived() override { std::cout << "~Derived\n"; }
    void identify() override { std::cout << "Derived\n"; }
};

std::unique_ptr<Base> ptr = std::make_unique<Derived>();
ptr->identify();  // "Derived" (polymorphic call)
// Destructor calls: ~Derived, then ~Base (correct!)
```

The virtual destructor ensures proper cleanup. When the unique_ptr is destroyed, it calls the destructor through the base pointer, which properly invokes the derived destructor first thanks to the virtual mechanism.

## Containers of unique_ptr

Containers can hold unique_ptrs, enabling collections of polymorphic objects with automatic cleanup.

```cpp
std::vector<std::unique_ptr<Widget>> widgets;

widgets.push_back(std::make_unique<Widget>(1));
widgets.push_back(std::make_unique<Widget>(2));
widgets.push_back(std::make_unique<Widget>(3));

// Access elements
widgets[0]->doSomething();

// All widgets automatically deleted when vector destroyed

// Move semantics work
auto widget = std::make_unique<Widget>(4);
widgets.push_back(std::move(widget));  // Transfer ownership
```

This pattern is common for managing collections of polymorphic objects. Each vector element owns its widget. When the vector is destroyed or elements are removed, the widgets are automatically deleted.

## Passing to Functions

Different parameter types express different ownership semantics for functions.

```cpp
// Observe: doesn't take ownership
void observe(const Widget* w) {
    w->inspect();
}

// Use: doesn't take ownership (preferred for observation)
void use(const Widget& w) {
    w.process();
}

// Consume: takes ownership
void consume(std::unique_ptr<Widget> w) {
    w->finalize();
}  // w deleted here

// Modify but don't take ownership
void modify(Widget* w) {
    w->update();
}

auto widget = std::make_unique<Widget>();

observe(widget.get());        // Just looking
use(*widget);                 // Using without ownership
modify(widget.get());         // Modifying
consume(std::move(widget));   // Transferring ownership
// widget is now nullptr
```

Pass by raw pointer or reference when the function doesn't take ownership. Pass by unique_ptr when transferring ownership. This makes ownership semantics explicit in the function signature and at call sites.

## Factory Functions

unique_ptr is ideal for factory functions that create and return objects.

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() = 0;
};

class Circle : public Shape {
public:
    void draw() override { std::cout << "Circle\n"; }
};

class Square : public Shape {
public:
    void draw() override { std::cout << "Square\n"; }
};

std::unique_ptr<Shape> createShape(const std::string& type) {
    if (type == "circle") {
        return std::make_unique<Circle>();
    } else if (type == "square") {
        return std::make_unique<Square>();
    }
    return nullptr;
}

auto shape = createShape("circle");
if (shape) {
    shape->draw();
}
```

The factory returns ownership to the caller through unique_ptr. This is clearer than returning a raw pointer where ownership is ambiguous. The caller knows they own the object and it will be automatically cleaned up.

## Performance

unique_ptr has zero overhead compared to raw pointers. The abstraction is completely compile-time.

```cpp
// Same size as raw pointer
sizeof(std::unique_ptr<int>) == sizeof(int*)  // true

// No runtime overhead
auto ptr = std::make_unique<int>(42);
int* raw = ptr.get();
// ptr and raw are identical in memory representation
// Dereferencing ptr compiles to same code as dereferencing raw
```

The compiler inlines all unique_ptr operations. The destructor call, null checks, and member access compile to the same machine code as manual memory management. You get safety without sacrificing performance.

:::warning Common Mistakes

**Copying**: Cannot copy unique_ptr - use `std::move()` to transfer ownership.

**Double Delete**: Don't manually delete what unique_ptr manages.

**Dangling get()**: Don't store the result of `get()` longer than the unique_ptr lives.

**Forgetting std::move**: Must explicitly move when passing to functions that take unique_ptr.

**Circular References**: unique_ptr alone can't handle circular ownership (use shared_ptr/weak_ptr).
:::

## Summary

`std::unique_ptr` provides automatic memory management with exclusive ownership semantics and zero runtime overhead. It cannot be copied, only moved, ensuring exactly one unique_ptr owns the object at any time. Always use `std::make_unique` to create unique_ptrs for exception safety. The managed object is automatically deleted when the unique_ptr is destroyed (RAII). Use `get()` to access the raw pointer without transferring ownership. Use `release()` to give up ownership and get the raw pointer. Use `reset()` to delete the current object and optionally take ownership of a new one. Move semantics make ownership transfer explicit in code. unique_ptr works with polymorphism through virtual destructors. Pass raw pointers or references to functions that observe without taking ownership. Pass unique_ptr by value to transfer ownership. Return unique_ptr from factories to clearly transfer ownership to callers. unique_ptr has a specialization for arrays but prefer `std::vector` for better interface. Custom deleters enable managing non-heap resources. Performance is identical to raw pointers - no runtime overhead. unique_ptr is the default choice for exclusive ownership: use it instead of raw `new`/`delete` for automatic, exception-safe memory management. It makes ownership explicit, prevents leaks, and costs nothing at runtime.

:::success Essential Points

**Exclusive Ownership**: Only one unique_ptr owns the object - no copies allowed.

**Zero Overhead**: Same performance as raw pointers, pure compile-time abstraction.

**Automatic Cleanup**: Destructor deletes the managed object - no memory leaks.

**Move-Only**: Use `std::move()` to transfer ownership explicitly.

**make_unique**: Always prefer over raw `new` for exception safety.

**Clear Ownership**: Function signatures show ownership transfer through unique_ptr parameters.

**RAII**: Resource lifetime tied to object lifetime - exception-safe by design.
:::