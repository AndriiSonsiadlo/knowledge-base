---
id: constructors-and-destructors
title: Constructors and Destructors
sidebar_label: Constructors & Destructors
sidebar_position: 3
tags: [c++, classes, constructors, destructors, lifecycle, raii]
---

# Constructors and Destructors

Constructors initialize objects and allocate resources. Destructors clean up when objects are destroyed. Together they enable RAII (Resource Acquisition Is Initialization).

:::info Object Lifecycle
**Birth** → Constructor runs  
**Life** → Object is usable  
**Death** → Destructor runs (automatic cleanup)
:::

## Constructor Basics

Constructors initialize objects. They have the same name as the class and no return type.
```cpp showLineNumbers
class Widget {
    int value;
    std::string name;
    
public:
    // Default constructor
    Widget() : value(0), name("default") {}
    
    // Parameterized constructor
    Widget(int v) : value(v), name("widget") {}
    
    // Multiple parameters
    Widget(int v, std::string n) : value(v), name(n) {}
};

Widget w1;              // Calls default constructor
Widget w2(42);          // Calls Widget(int)
Widget w3(42, "test");  // Calls Widget(int, string)
```

**Member initializer list** (`: value(v), name(n)`) is preferred over assignment in the body because it directly constructs members rather than default-constructing then assigning.

## Initialization vs Assignment
```cpp showLineNumbers
class Widget {
    const int id;
    std::string name;
    
public:
    // ✅ Correct: initializer list
    Widget(int i, std::string n) 
        : id(i), name(n) {}
    
    // ❌ Won't compile: can't assign to const
    Widget(int i, std::string n) {
        id = i;      // Error: id is const
        name = n;    // Works but inefficient (default construct + assign)
    }
};
```

:::success Use Initializer Lists
**Required for:**
- const members
- Reference members
- Members without default constructor

**Better for:**
- All other members (more efficient)
:::

## Construction Order

Members initialize in **declaration order**, not initializer list order. Bases initialize before members.
```cpp showLineNumbers
class Base {
public:
    Base() { std::cout << "1. Base "; }
};

class Widget : public Base {
    int second;
    int first;
    
public:
    // ⚠️ Misleading: first listed but second initializes first!
    Widget(int val) : first(val), second(first * 2) {}
    // Order: Base → second → first (declaration order)
    
    // ✅ Correct: match declaration order
    Widget(int val) : second(val), first(val * 2) {}
};

Widget w(5);
// Output: "1. Base "
// Initialization: Base() → second=5 → first=10
```

**Initialization order:**
1. Base classes (left to right for multiple inheritance)
2. Member variables (declaration order)
3. Constructor body

:::warning Order Matters
Always list initializers in declaration order to avoid confusion. Compiler may warn if order doesn't match.
:::

## Destruction Order

Destruction happens in **exact reverse** of construction.
```cpp showLineNumbers
class Base {
public:
    ~Base() { std::cout << "~Base "; }
};

class Member {
public:
    ~Member() { std::cout << "~Member "; }
};

class Derived : public Base {
    Member m;
    
public:
    ~Derived() { std::cout << "~Derived "; }
};

{
    Derived d;
}
// Output: ~Derived ~Member ~Base
```

**Destruction order:**
1. Destructor body
2. Member variables (reverse declaration order)
3. Base classes (reverse construction order)

## Delegating Constructors

One constructor can call another, avoiding code duplication.
```cpp showLineNumbers
class Widget {
    int value;
    std::string name;
    bool initialized;
    
    void init() { /* common initialization */ }
    
public:
    // Main constructor
    Widget(int v, std::string n) 
        : value(v), name(n), initialized(true) {
        init();
    }
    
    // Delegate to main constructor
    Widget(int v) : Widget(v, "default") {}
    Widget() : Widget(0, "default") {}
};
```

:::danger Delegation Rules
**Cannot mix** delegation with member initialization:
```cpp
// ❌ Error: can't have both
Widget(int v) : Widget(v, "default"), value(42) {}

// ✅ Choose one:
Widget(int v) : Widget(v, "default") {}  // Delegation
// OR
Widget(int v) : value(v), name("default") {}  // Direct
```
:::

## Explicit Constructors

Prevent implicit conversions with single-argument constructors.
```cpp showLineNumbers
class String {
public:
    String(int size) {}  // ⚠️ Allows implicit conversion
};

void process(String s) {}

process(100);  // ⚠️ Implicit: int → String(100)

// ✅ Use explicit
class String {
public:
    explicit String(int size) {}
};

// process(100);  // ❌ Error: no implicit conversion
process(String(100));  // ✅ OK: explicit conversion
```

:::success Use explicit
**Always use `explicit`** for single-argument constructors (except copy/move constructors) to prevent accidental conversions.
:::

## Default and Delete (C++11)

Explicitly control compiler-generated functions.
```cpp showLineNumbers
class Widget {
public:
    Widget() = default;  // Use compiler-generated version
    ~Widget() = default;
    
    // Prevent copying
    Widget(const Widget&) = delete;
    Widget& operator=(const Widget&) = delete;
};

Widget w1;
// Widget w2 = w1;  // ❌ Error: copy deleted
```

`= default` tells compiler to generate the default implementation. `= delete` prevents the function from being used at all.

## Exceptions in Constructors

If a constructor throws, the object isn't fully constructed and the destructor won't run.
```cpp showLineNumbers
class Resource {
    int* data;
    
public:
    Resource(int size) {
        data = new int[size];
        
        if (someCondition()) {
            throw std::runtime_error("Init failed");
            // ⚠️ data leaked! Destructor won't run!
        }
    }
    
    ~Resource() {
        delete[] data;  // Never called if constructor throws
    }
};
```

**Solution**: Use RAII members that clean themselves up.
```cpp showLineNumbers
class Resource {
    std::unique_ptr<int[]> data;  // ✅ Cleans up automatically
    
public:
    Resource(int size) : data(new int[size]) {
        if (someCondition()) {
            throw std::runtime_error("Init failed");
            // data automatically deleted (unique_ptr destructor runs)
        }
    }
    // No destructor needed - unique_ptr handles it
};
```

:::info Constructor Exception Safety
Members that were successfully constructed before the exception **will** have their destructors called. Only the object's destructor won't run.
:::

## Virtual Destructors

Always make base class destructor virtual if you'll delete through a base pointer.
```cpp showLineNumbers
class Base {
public:
    ~Base() {  // ❌ Not virtual!
        std::cout << "~Base\n";
    }
};

class Derived : public Base {
    int* data;
    
public:
    Derived() : data(new int[100]) {}
    
    ~Derived() {
        delete[] data;
        std::cout << "~Derived\n";
    }
};

Base* ptr = new Derived();
delete ptr;  // ⚠️ Only calls ~Base! Memory leak!

// ✅ Fix: virtual destructor
class Base {
public:
    virtual ~Base() { std::cout << "~Base\n"; }
};

// Now delete ptr calls both ~Derived and ~Base
```

:::danger Always Virtual
**If your class has any virtual functions, make the destructor virtual!** Otherwise, deleting through a base pointer causes resource leaks.
:::

## Virtual Functions in Constructors/Destructors

Don't call virtual functions in constructors or destructors - they won't dispatch to derived versions.
```cpp showLineNumbers
class Base {
public:
    Base() {
        init();  // ⚠️ Calls Base::init, not Derived::init!
    }
    
    virtual void init() { 
        std::cout << "Base init\n"; 
    }
    
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void init() override { 
        std::cout << "Derived init\n"; 
    }
};

Derived d;  // Output: "Base init"
```

**Why?** During Base's constructor, the object is still just a Base - the Derived part hasn't been constructed yet. Virtual dispatch uses the current type.

:::warning Construction Phases
- During Base constructor → object is a Base
- During Derived constructor → object becomes Derived
- During Derived destructor → object becomes Base again
- During Base destructor → object is a Base
:::

## Inheriting Constructors

Derived class can inherit base class constructors.
```cpp showLineNumbers
class Base {
public:
    Base(int x) {}
    Base(int x, int y) {}
};

class Derived : public Base {
public:
    using Base::Base;  // ✅ Inherit all Base constructors
    
    // Now have:
    // Derived(int x) : Base(x) {}
    // Derived(int x, int y) : Base(x, y) {}
};

Derived d1(5);
Derived d2(5, 10);
```

This avoids writing forwarding constructors when you just want to pass arguments to the base class.

## Placement new

Construct an object in pre-allocated memory.
```cpp showLineNumbers
alignas(Widget) char buffer[sizeof(Widget)];

Widget* w = new (buffer) Widget(42);  // Placement new
w->use();

w->~Widget();  // Explicit destructor call
// Don't delete w! Memory not from heap
```

**Used for:**
- Memory pools
- Custom allocators
- Embedded systems
- Avoiding heap allocations

## Trivial Destructors

Trivial destructors can be optimized away by the compiler.
```cpp showLineNumbers
struct Simple {
    int x, y;
    // Implicit trivial destructor (does nothing)
};

// Compiler optimizes: no destructor calls needed
std::vector<Simple> vec(1000);
vec.clear();  // Just deallocates memory

struct Complex {
    std::string s;
    ~Complex() {}  // Non-trivial (string destructor must run)
};

std::vector<Complex> vec2(1000);
vec2.clear();  // Calls 1000 destructors
```

**Trivial destructor** = compiler-generated, does nothing. Allows optimizations like `memcpy` instead of element-wise copy.

## Summary

:::info Constructor basics:
- Initialize objects, same name as class, no return type
- Use initializer list (required for const/reference, efficient for all)
- Initialization order: bases → members (declaration order) → body
:::

:::info Destructor basics:
- Clean up resources, runs automatically
- Destruction order: body → members (reverse) → bases (reverse)
- Make virtual if base class with virtual functions
:::

:::info Modern features:
- Delegating constructors avoid code duplication
- `explicit` prevents implicit conversions
- `= default` uses compiler-generated version
- `= delete` prevents function use
:::

:::info Safety:
- Use RAII members for exception safety in constructors
- Never call virtual functions in constructors/destructors
- Always virtual destructor for polymorphic base classes
:::

:::info Advanced:
- Inheriting constructors with `using Base::Base`
- Placement new for custom memory management
- Trivial destructors enable optimizations
:::
