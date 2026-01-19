---
id: shared-ptr
title: std::shared_ptr
sidebar_label: shared_ptr
sidebar_position: 6
tags: [c++, smart-pointers, shared-ptr, reference-counting, cpp11]
---

# std::shared_ptr

`std::shared_ptr` is a smart pointer that retains shared ownership of an object through a pointer. Multiple shared_ptrs can own the same object, which is deleted when the last shared_ptr owning it is destroyed.

:::info Reference Counting
shared_ptr uses reference counting - each copy increments the count, each destruction decrements it. When the count reaches zero, the object is deleted automatically.
:::

## Basic Usage

Creating and copying shared_ptrs is straightforward. All copies share ownership of the same object.

```cpp
#include <memory>

// Create shared_ptr
std::shared_ptr<int> ptr1 = std::make_shared<int>(42);

// Copy shares ownership
std::shared_ptr<int> ptr2 = ptr1;  // ✅ OK: both own the int

std::cout << *ptr1;  // 42
std::cout << *ptr2;  // 42 (same object)

*ptr2 = 100;
std::cout << *ptr1;  // 100 (modified through either pointer)

// Object deleted when last shared_ptr destroyed
```

Copying a shared_ptr increments the reference count. The object persists as long as any shared_ptr owns it. When the last shared_ptr is destroyed, the reference count reaches zero and the object is automatically deleted.

### make_shared (C++11)

Always prefer `std::make_shared` over direct `new` for efficiency and exception safety.

```cpp
// ✅ Preferred: make_shared (single allocation)
auto ptr1 = std::make_shared<int>(42);
auto ptr2 = std::make_shared<std::string>("hello");

// ❌ Avoid: direct new (two allocations)
std::shared_ptr<int> ptr3(new int(42));
```

`make_shared` allocates the object and control block (containing reference count) in a single memory allocation, which is more efficient than separate allocations. It's also exception-safe, preventing leaks if an exception occurs during construction.

## Reference Counting

shared_ptr maintains a reference count tracking how many shared_ptrs own the object.

```cpp
auto ptr1 = std::make_shared<int>(42);
std::cout << ptr1.use_count();  // 1

{
    auto ptr2 = ptr1;  // Copy
    std::cout << ptr1.use_count();  // 2
    std::cout << ptr2.use_count();  // 2 (same count)
    
    auto ptr3 = ptr1;  // Another copy
    std::cout << ptr1.use_count();  // 3
}  // ptr2 and ptr3 destroyed

std::cout << ptr1.use_count();  // 1
// Object still alive
```

Each shared_ptr can query the current reference count with `use_count()`. When the count drops to zero, the managed object is deleted. The count is shared across all copies through the control block.

### Thread Safety

Reference count updates are thread-safe (atomic), but the pointed-to object is not automatically protected.

```cpp
std::shared_ptr<int> global_ptr = std::make_shared<int>(42);

void thread1() {
    auto local = global_ptr;  // ✅ Thread-safe copy
    // Reference count increment is atomic
}

void thread2() {
    auto local = global_ptr;  // ✅ Thread-safe copy
    *local = 100;  // ❌ Data race if thread1 also modifies!
}
```

Copying shared_ptrs between threads is safe - the reference count operations are atomic. However, if multiple threads access the pointed-to object, you need additional synchronization (mutex, atomic operations) to protect the data.

## Shared Ownership

Multiple shared_ptrs can own the same object, useful for shared resources and graph structures.

```cpp
class Node {
public:
    std::string data;
    std::vector<std::shared_ptr<Node>> children;
    
    Node(std::string d) : data(d) {}
};

auto root = std::make_shared<Node>("root");
auto child1 = std::make_shared<Node>("child1");
auto child2 = std::make_shared<Node>("child2");

root->children.push_back(child1);
root->children.push_back(child2);

// child1 is owned by both root and child1 variable
std::cout << child1.use_count();  // 2
```

This enables building complex data structures where multiple objects reference the same sub-object. The shared object persists as long as any owner exists.

## Resetting

Like unique_ptr, you can reset shared_ptrs to release ownership or take ownership of a different object.

```cpp
auto ptr1 = std::make_shared<int>(42);
auto ptr2 = ptr1;

std::cout << ptr1.use_count();  // 2

ptr1.reset();  // ptr1 releases ownership
// ptr1 is now nullptr
// Object still alive because ptr2 owns it

std::cout << ptr2.use_count();  // 1

ptr2.reset(new int(100));  // Takes ownership of new int
// Old int(42) deleted
```

Resetting decrements the reference count. If it was the last owner, the object is deleted. You can also reset with a new pointer to take ownership of a different object.

## Polymorphism

shared_ptr works naturally with inheritance and polymorphism.

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

std::shared_ptr<Base> ptr1 = std::make_shared<Derived>();
ptr1->identify();  // "Derived"

std::shared_ptr<Base> ptr2 = ptr1;  // Share ownership
std::cout << ptr1.use_count();  // 2

// Proper cleanup: ~Derived, then ~Base
```

The virtual destructor ensures correct cleanup. All shared_ptrs can share ownership of the derived object through base class pointers, and cleanup happens correctly when the last owner is destroyed.

## Containers of shared_ptr

Containers can hold shared_ptrs, enabling collections where multiple containers can reference the same objects.

```cpp
class Widget {
public:
    int id;
    Widget(int i) : id(i) {}
};

std::vector<std::shared_ptr<Widget>> all_widgets;
std::vector<std::shared_ptr<Widget>> active_widgets;

auto w1 = std::make_shared<Widget>(1);
auto w2 = std::make_shared<Widget>(2);

all_widgets.push_back(w1);
all_widgets.push_back(w2);

active_widgets.push_back(w1);  // w1 shared between both vectors

std::cout << w1.use_count();  // 3 (w1 variable + 2 vectors)
std::cout << w2.use_count();  // 2 (w2 variable + all_widgets)
```

Objects persist as long as any container holds a shared_ptr to them. This enables flexible ownership patterns where objects can be referenced from multiple collections.

## Passing to Functions

Different parameter types express different ownership and lifetime requirements.

```cpp
// Observe: doesn't extend lifetime
void observe(const Widget* w) {
    w->inspect();
}

// Use: doesn't affect ownership (preferred)
void use(const Widget& w) {
    w->process();
}

// Share: participates in ownership
void share(std::shared_ptr<Widget> w) {
    // Keeps object alive during function
}

// Observe through shared_ptr (unusual)
void observe_shared(const std::shared_ptr<Widget>& w) {
    w->inspect();
}

auto widget = std::make_shared<Widget>();

observe(widget.get());     // Just observing
use(*widget);              // Using temporarily
share(widget);             // Sharing ownership (increment count)
observe_shared(widget);    // Observing (no count change)
```

Pass by raw pointer or reference when the function doesn't need ownership. Pass by shared_ptr value when the function should extend the object's lifetime (store it, pass to async operations). Pass by const reference to shared_ptr when you need to check/copy the shared_ptr itself without affecting ownership.

## Circular References Problem

shared_ptr can create circular references that prevent deletion, causing memory leaks.

```cpp
class Node {
public:
    std::shared_ptr<Node> next;  // ❌ Circular reference possible
    ~Node() { std::cout << "~Node\n"; }
};

auto node1 = std::make_shared<Node>();
auto node2 = std::make_shared<Node>();

node1->next = node2;  // node1 → node2
node2->next = node1;  // node2 → node1 (circular!)

// node1 and node2 go out of scope
// But reference counts never reach zero!
// Neither destructor called - memory leaked!
```

Each node keeps the other alive through its shared_ptr. When the original shared_ptrs go out of scope, the reference counts only drop to 1 (the circular reference), never reaching zero. The objects are never deleted - a memory leak despite using smart pointers.

### Breaking Cycles with weak_ptr

Use `weak_ptr` to break circular references (covered in the next section).

```cpp
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // ✅ Weak reference breaks cycle
    ~Node() { std::cout << "~Node\n"; }
};

auto node1 = std::make_shared<Node>();
auto node2 = std::make_shared<Node>();

node1->next = node2;       // Strong reference
node2->prev = node1;       // Weak reference (doesn't increase count)

// Destructors properly called!
```

## aliasing Constructor

shared_ptr supports aliasing - storing one pointer but referencing another, useful for managing members of an object.

```cpp
struct Widget {
    int value;
    Widget(int v) : value(v) {}
};

auto widget = std::make_shared<Widget>(42);

// Aliased shared_ptr to member
std::shared_ptr<int> value_ptr(widget, &widget->value);

std::cout << *value_ptr;  // 42
std::cout << widget.use_count();  // 2 (widget and value_ptr)

value_ptr.reset();
std::cout << widget.use_count();  // 1

// widget keeps the object alive as long as value_ptr exists
```

The aliased shared_ptr shares ownership of the Widget but points to its member. This ensures the Widget stays alive as long as any pointer to its members exists.

## Custom Deleters

shared_ptr supports custom deleters for non-standard cleanup, passed at construction time.

```cpp
auto deleter = [](FILE* f) {
    if (f) {
        std::cout << "Closing file\n";
        fclose(f);
    }
};

std::shared_ptr<FILE> file(fopen("data.txt", "r"), deleter);

// File closed when last shared_ptr destroyed
```

Unlike unique_ptr, the deleter type isn't part of shared_ptr's type, making it easier to work with. We'll cover custom deleters in detail in the next section.

## Performance Considerations

shared_ptr has overhead compared to unique_ptr and raw pointers due to reference counting.

```cpp
// Size overhead
sizeof(std::shared_ptr<int>) > sizeof(std::unique_ptr<int>)
// shared_ptr: 16 bytes (2 pointers: object + control block)
// unique_ptr: 8 bytes (1 pointer)
// raw pointer: 8 bytes

// Runtime overhead
// - Reference count increments/decrements (atomic operations)
// - Two allocations with new (one with make_shared)
// - Destructor checks reference count
```

The control block contains the reference count and weak count, requiring extra memory. Atomic increment/decrement operations for thread safety are slower than simple pointer copies. Use shared_ptr when you need shared ownership; prefer unique_ptr for exclusive ownership (cheaper).

## Factory Functions

Like unique_ptr, shared_ptr works well with factory functions, but allows sharing the returned object.

```cpp
std::shared_ptr<Widget> createWidget(int id) {
    return std::make_shared<Widget>(id);
}

auto w1 = createWidget(1);
auto w2 = w1;  // ✅ Can share ownership
```

The factory returns a shared_ptr, making the ownership model clear. Callers can copy the shared_ptr to share ownership, unlike unique_ptr which requires explicit moves.

:::warning Common Pitfalls

**Circular References**: Shared_ptrs referencing each other leak memory - use weak_ptr.

**Creating from this**: Inside member functions, use `enable_shared_from_this`, not `shared_ptr<T>(this)`.

**Two Control Blocks**: Creating two shared_ptrs from the same raw pointer creates separate control blocks - disaster!

**Performance**: shared_ptr is slower than unique_ptr - only use when you need shared ownership.

**Thread Safety**: Reference counts are thread-safe, but the object itself isn't automatically protected.
:::

## Summary

`std::shared_ptr` provides automatic memory management with shared ownership through reference counting. Multiple shared_ptrs can own the same object, which is deleted when the last owner is destroyed. Always use `std::make_shared` for efficiency (single allocation) and exception safety. Reference count operations are thread-safe (atomic), but the pointed-to object needs separate synchronization for concurrent access. Copy shared_ptrs freely to share ownership - the count increases automatically. Use `use_count()` to check how many owners exist. Reset shared_ptrs to release ownership and optionally take ownership of new objects. Circular references prevent deletion causing memory leaks - use `weak_ptr` to break cycles. Pass by raw pointer/reference for observation, by shared_ptr value to share ownership. shared_ptr works with polymorphism and containers naturally. The aliasing constructor enables managing object members. Custom deleters enable managing non-heap resources. Performance overhead includes atomic operations and control block allocation - use unique_ptr when exclusive ownership suffices. Never create multiple shared_ptrs from the same raw pointer - they'll have independent control blocks causing double-delete. Use `enable_shared_from_this` when creating shared_ptrs to `this` in member functions. shared_ptr is the choice for shared ownership: use when multiple parts of code need to keep an object alive, for callbacks and async operations, and for collections where objects can be referenced from multiple places.

:::success Core Principles

**Shared Ownership**: Multiple shared_ptrs can own the same object safely.

**Reference Counting**: Automatic - increments on copy, decrements on destruction.

**Zero Count = Delete**: Object deleted when reference count reaches zero.

**Thread-Safe Counts**: Copying shared_ptrs is thread-safe, but not the object itself.

**make_shared**: Prefer for efficiency (single allocation) and exception safety.

**Avoid Cycles**: Use weak_ptr to break circular references or memory leaks.

**Cost**: Overhead from atomic operations and control blocks - use when truly needed.
:::