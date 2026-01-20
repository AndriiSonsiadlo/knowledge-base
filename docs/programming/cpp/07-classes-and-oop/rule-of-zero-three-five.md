---
id: rule-of-zero-three-five
title: Rule of 0/3/5
sidebar_label: Rule of 0/3/5
sidebar_position: 4
tags: [c++, special-members, rule-of-five, raii, best-practices]
---

# Rule of Zero/Three/Five

These rules tell you which special member functions (constructor, destructor, copy, move, assignment) you need to define based on your class's resource management needs. Following these rules prevents memory leaks, double-deletes, and other resource management bugs.

:::info Special Members Working Together
If you manage resources manually, you must handle all related operations (Rule of 5). If you use RAII wrappers, you don't need to define any (Rule of 0)!
:::

## The Special Member Functions

C++ automatically generates up to six special member functions if you don't define them yourself:

```cpp showLineNumbers 
class Widget {
public:
    Widget();                              // Default constructor
    ~Widget();                             // Destructor
    Widget(const Widget&);                 // Copy constructor
    Widget& operator=(const Widget&);      // Copy assignment
    Widget(Widget&&) noexcept;             // Move constructor (C++11)
    Widget& operator=(Widget&&) noexcept;  // Move assignment (C++11)
};
```

These functions handle object creation, destruction, copying, and moving. The compiler generates them if needed, but its defaults only work for simple cases. When you manage resources (memory, files, handles), you need to define them yourself!

## Rule of Zero

**Best Case**: If your class doesn't directly manage resources, don't define any of these functions! Let the compiler handle everything.

```cpp showLineNumbers 
// ✅ Rule of Zero - no special members needed
class Person {
    std::string name;        // string manages its own memory
    int age;                 // trivial type
    std::vector<int> scores; // vector manages its own memory
    
    // Don't need to define:
    // - Destructor (members clean themselves up)
    // - Copy constructor (memberwise copy works fine)
    // - Copy assignment (memberwise copy works fine)
    // - Move constructor (memberwise move works fine)
    // - Move assignment (memberwise move works fine)
};

Person p1{"Alice", 30, {95, 87, 92}};
Person p2 = p1;           // ✅ Copy works automatically
Person p3 = std::move(p1); // ✅ Move works automatically
```

This is the ideal! By using smart pointers, standard containers, and RAII wrappers for all resources, you let those classes handle resource management. Your class just uses them. This is safer, simpler, and less error-prone than manual resource management.

### When Rule of Zero Applies

Use standard library types instead of raw pointers and manual memory management:

```cpp showLineNumbers 
// ❌ Manual resource management (need Rule of 5)
class BadBuffer {
    char* data;
    size_t size;
    
public:
    BadBuffer(size_t s) : size(s) {
        data = new char[size];
    }
    // Need destructor, copy, move, assignment...
};

// ✅ Rule of Zero (standard types handle it)
class GoodBuffer {
    std::vector<char> data;
    
public:
    GoodBuffer(size_t s) : data(s) {}
    // No special members needed! vector handles everything
};
```

The `std::vector` version is shorter, safer, and automatically handles copying, moving, and cleanup. This is modern C++ - use RAII wrappers for everything!

## Rule of Three (Pre-C++11)

**Classic C++**: If you define a destructor, copy constructor, OR copy assignment operator, you probably need to define all three.

```cpp showLineNumbers 
class Buffer {
    char* data;
    size_t size;
    
public:
    // Constructor
    Buffer(size_t s) : size(s), data(new char[size]) {}
    
    // Destructor (need it to free memory)
    ~Buffer() {
        delete[] data;
    }
    
    // Copy constructor (need it for deep copy)
    Buffer(const Buffer& other) 
        : size(other.size), data(new char[size]) {
        std::copy(other.data, other.data + size, data);
    }
    
    // Copy assignment (need it for deep copy)
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data;  // Free old memory
            size = other.size;
            data = new char[size];
            std::copy(other.data, other.data + size, data);
        }
        return *this;
    }
};
```

The Rule of Three exists because if you need custom cleanup (destructor), the compiler-generated copy operations will just copy the pointer, not the data! This causes double-delete bugs and shallow copies. You need to define all three to handle the resource properly.

### Why All Three?

These operations are intimately related when managing resources:

```cpp showLineNumbers 
// ❌ Only defined destructor
class Broken {
    int* data;
    
public:
    Broken(int v) : data(new int(v)) {}
    ~Broken() { delete data; }
    
    // Compiler generates copy operations that just copy pointer!
};

Broken b1(42);
Broken b2 = b1;  // ⚠️ Both point to same memory
// Both destructors try to delete the same memory! Crash! 💥
```

If you need a destructor to clean up, you need copy operations that properly duplicate the resource. They're a package deal!

## Rule of Five (C++11+)

**Modern C++**: If you define any of destructor, copy constructor, copy assignment, move constructor, or move assignment, you should probably define or explicitly delete all five.

```cpp showLineNumbers 
class Buffer {
    char* data;
    size_t size;
    
public:
    // Constructor
    Buffer(size_t s) : size(s), data(new char[size]) {}
    
    // Destructor
    ~Buffer() {
        delete[] data;
    }
    
    // Copy constructor
    Buffer(const Buffer& other)
        : size(other.size), data(new char[size]) {
        std::copy(other.data, other.data + size, data);
    }
    
    // Copy assignment
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data;
            size = other.size;
            data = new char[size];
            std::copy(other.data, other.data + size, data);
        }
        return *this;
    }
    
    // Move constructor
    Buffer(Buffer&& other) noexcept
        : size(other.size), data(other.data) {
        other.data = nullptr;  // Steal resource
        other.size = 0;
    }
    
    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data;  // Free our old resource
            data = other.data;  // Steal other's resource
            size = other.size;
            other.data = nullptr;  // Leave other valid but empty
            other.size = 0;
        }
        return *this;
    }
};
```

Move operations enable efficient transfer of resources without copying. If you're managing resources manually, you should provide move operations for performance. They're like copy but they "steal" the resource instead of duplicating it.

### Explicitly Deleting Operations

Sometimes you want to prevent copying or moving:

```cpp showLineNumbers 
class Uncopyable {
    std::mutex mtx;  // Mutexes can't be copied or moved
    
public:
    Uncopyable() = default;
    ~Uncopyable() = default;
    
    // Delete copy operations
    Uncopyable(const Uncopyable&) = delete;
    Uncopyable& operator=(const Uncopyable&) = delete;
    
    // Delete move operations
    Uncopyable(Uncopyable&&) = delete;
    Uncopyable& operator=(Uncopyable&&) = delete;
};

Uncopyable u1;
// Uncopyable u2 = u1;  // ❌ Error: copy deleted
// Uncopyable u3 = std::move(u1);  // ❌ Error: move deleted
```

Explicitly deleting operations makes your intent clear and gives better error messages than making them private.

## Copy-and-Swap Idiom

A clever technique that implements both copy and move assignment using the copy constructor and swap:

```cpp showLineNumbers 
class Buffer {
    char* data;
    size_t size;
    
public:
    // Constructor, destructor, copy constructor as before...
    
    // Swap member
    void swap(Buffer& other) noexcept {
        std::swap(data, other.data);
        std::swap(size, other.size);
    }
    
    // Unified assignment operator (by-value parameter!)
    Buffer& operator=(Buffer other) {  // Note: by value!
        swap(other);  // Swap with the parameter
        return *this;
        // other destructs with our old data
    }
};

Buffer b1(100);
Buffer b2(200);

b1 = b2;           // Copy: parameter constructed via copy
b1 = std::move(b2); // Move: parameter constructed via move
```

This is elegant because you write one assignment operator that handles both copy and move! The parameter is constructed either by copying or moving (depending on what you pass), then you swap your contents with it. When the parameter destructs, it cleans up your old data. Less code, less chance for bugs!

## Generated vs Deleted

The compiler's rules for generating these functions are complex:

```cpp showLineNumbers 
class Example {
public:
    // If you declare ANY constructor, default is not generated
    Example(int x) {}
    // Example obj;  // ❌ Error: no default constructor
    
    // Declaring a destructor doesn't prevent copy/move generation
    ~Example() {}
    
    // But declaring copy constructor prevents move generation!
    Example(const Example&) {}
    // Move constructor and move assignment NOT generated
    
    // Declaring move constructor prevents copy generation!
    Example(Example&&) noexcept {}
    // Copy constructor and copy assignment DELETED
};
```

These rules encourage modern practice: if you're managing resources (have a destructor), you should handle copy and move explicitly. The compiler tries to prevent silent bugs.

## Practical Guidelines

Here's how to decide which rule to follow:

```cpp showLineNumbers 
// ✅ Rule of Zero (BEST): Use RAII wrappers
class Widget {
    std::unique_ptr<Resource> resource;
    std::vector<int> data;
    // No special members needed!
};

// ✅ Rule of Five: Only if you MUST manage resources manually
class ManualResource {
    int* ptr;
    
public:
    ~ManualResource();
    ManualResource(const ManualResource&);
    ManualResource& operator=(const ManualResource&);
    ManualResource(ManualResource&&) noexcept;
    ManualResource& operator=(ManualResource&&) noexcept;
};

// ✅ Explicitly deleted: When copies/moves don't make sense
class NonMovable {
public:
    NonMovable() = default;
    NonMovable(const NonMovable&) = delete;
    NonMovable(NonMovable&&) = delete;
};
```

Prefer Rule of Zero! Only fall back to Rule of Five when you absolutely must manage resources manually (rare in modern C++). Make deletion explicit to show intent.

:::warning Common Mistakes

**Forgetting Self-Assignment**: Check `if (this != &other)` in copy assignment!

**Resource Leaks**: Not deleting old resource in assignment before acquiring new one.

**Not noexcept**: Move constructors should almost always be noexcept.

**Shallow Copy**: Compiler-generated copy just copies pointers, not what they point to.

**Dangling Pointers**: After move, source object should be left in valid state (usually nullptr).

**Missing Operations**: If you define one of destructor/copy/move, define or delete them all.
:::

## Summary

The Rule of Zero says if you don't manage resources directly, don't define special member functions - let the compiler generate them and use RAII wrappers like smart pointers and containers. This is the modern C++ ideal and the safest approach. The Rule of Three (pre-C++11) says if you define destructor, copy constructor, or copy assignment, define all three because they're related when managing resources. The Rule of Five (C++11+) adds move constructor and move assignment to the Rule of Three - if you manage resources, define or delete all five special members. Move operations enable efficient resource transfer without copying. Explicitly delete operations you don't want rather than making them private. The copy-and-swap idiom provides strong exception safety and unified copy/move assignment. Compiler generation rules are complex: declaring a destructor doesn't prevent copy/move but declaring copy prevents move generation. Always mark move operations noexcept. Check for self-assignment in assignment operators. Leave moved-from objects in valid (usually empty) state. Prefer Rule of Zero by using standard library types. Only implement Rule of Five when you absolutely must manage resources manually. These rules prevent resource leaks, double-deletes, and shallow copy bugs.

:::success Key Principles

**Rule of Zero = Best**: Use RAII wrappers, no special members needed.

**All or Nothing**: If you need one of destructor/copy/move, define or delete all five.

**Move = noexcept**: Move constructors and assignments should be noexcept.

**Self-Assignment**: Always check `this != &other` in assignment operators.

**Moved-From = Valid**: Leave objects usable after moving (usually empty/null state).

**Delete Explicitly**: Use `= delete` to show intent, not private.

**Standard Library**: Use smart pointers, containers, RAII wrappers.

**Copy-and-Swap**: Provides strong exception safety and unified assignment.
:::