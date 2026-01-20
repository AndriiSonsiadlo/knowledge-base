---
id: constructors-and-destructors
title: Constructors and Destructors
sidebar_label: Constructors & Destructors
sidebar_position: 3
tags: [c++, classes, constructors, destructors, lifecycle, raii]
---

# Constructors and Destructors

Deep dive into object lifecycle, construction/destruction order, exception safety, and advanced patterns.

:::info Object Lifecycle
**Birth**: Constructor runs  
**Life**: Object is usable  
**Death**: Destructor runs (automatic cleanup)
:::

## Construction Order Details

Members initialize in declaration order, not initializer list order:

```cpp showLineNumbers 
class Widget {
    int b;
    int a;
    
public:
    // ⚠️ Misleading: a listed first but b initializes first!
    Widget(int val) : a(val), b(a * 2) {
        // b initializes first (uninitialized value!)
        // then a initializes
    }
    
    // ✅ Correct: match declaration order
    Widget(int val) : b(val * 2), a(val) {
        // b = val * 2
        // a = val
    }
};
```

**Rules:**
1. Base classes (left to right if multiple inheritance)
2. Member variables (declaration order)
3. Constructor body

## Destruction Order

Exact reverse of construction:

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

Derived d;
// Output on destruction: ~Derived ~Member ~Base
```

**Rules:**
1. Destructor body
2. Member variables (reverse declaration order)
3. Base classes (reverse of construction order)

## Exceptions in Constructors

If constructor throws, object isn't fully constructed:

```cpp showLineNumbers 
class Resource {
    int* data;
    
public:
    Resource() {
        data = new int[1000];
        
        if (someCondition()) {
            // ⚠️ Exception before constructor completes!
            throw std::runtime_error("Init failed");
            // data leaked! Destructor won't run!
        }
    }
    
    ~Resource() {
        delete[] data;  // Never called if constructor throws
    }
};
```

**Solution:** Use RAII members that clean themselves up:

```cpp showLineNumbers 
class Resource {
    std::unique_ptr<int[]> data;  // ✅ Cleans up automatically
    
public:
    Resource() : data(new int[1000]) {
        if (someCondition()) {
            throw std::runtime_error("Init failed");
            // data automatically deleted (unique_ptr destructor runs)
        }
    }
};
```

## Two-Phase Initialization

Sometimes you need separate construction and initialization:

```cpp showLineNumbers 
class Database {
    Connection* conn;
    
public:
    // Phase 1: Constructor (can't fail)
    Database() : conn(nullptr) {}
    
    // Phase 2: Initialize (can fail)
    bool initialize(const std::string& connString) {
        try {
            conn = new Connection(connString);
            return true;
        } catch (...) {
            return false;
        }
    }
    
    ~Database() { delete conn; }
};

Database db;
if (!db.initialize("localhost:5432")) {
    std::cerr << "Failed to connect\n";
}
```

**Better:** Use exception-throwing constructor or factory function.

## Virtual Functions in Constructors/Destructors

Don't call virtual functions in constructor/destructor:

```cpp showLineNumbers 
class Base {
public:
    Base() {
        init();  // ⚠️ Calls Base::init, not Derived::init!
    }
    
    virtual void init() { std::cout << "Base init\n"; }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void init() override { std::cout << "Derived init\n"; }
};

Derived d;  // Output: "Base init"
// During Base constructor, object is still a Base, not Derived yet!
```

During construction, the object's type gradually "becomes" the derived type. In Base constructor, it's only a Base.

## Delegating Constructors

One constructor calls another (C++11):

```cpp showLineNumbers 
class Widget {
    int value;
    std::string name;
    
public:
    // Main constructor
    Widget(int v, std::string n) 
        : value(v), name(n) {
        // Common initialization
    }
    
    // Delegates to main constructor
    Widget(int v) : Widget(v, "default") {}
    Widget() : Widget(0, "default") {}
};
```

**Can't** mix delegation with member initialization:

```cpp showLineNumbers 
// ❌ Error: can't have both
Widget(int v) : Widget(v, "default"), value(42) {}

// ✅ Must choose one:
Widget(int v) : Widget(v, "default") {}  // Delegation
// OR
Widget(int v) : value(v), name("default") {}  // Direct init
```

## Inheriting Constructors

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

## Placement new

Construct object in pre-allocated memory:

```cpp showLineNumbers 
alignas(Widget) char buffer[sizeof(Widget)];

Widget* w = new (buffer) Widget(42);  // Placement new
w->use();

w->~Widget();  // Explicit destructor call
// Don't delete w! (memory not from heap)
```

Used for memory pools, custom allocators, and embedded systems.

## Trivial Destructors

Trivial destructors can be optimized away:

```cpp showLineNumbers 
struct Simple {
    int x, y;
    // Implicit trivial destructor (does nothing)
};

// Compiler can optimize: no destructor call needed
std::vector<Simple> vec(1000);
vec.clear();  // Just deallocates memory, no destructor calls

struct Complex {
    std::string s;
    ~Complex() {}  // Non-trivial (string's destructor must run)
};
```

**Trivial if:**
- No user-defined destructor
- No virtual functions
- No virtual base classes
- All members have trivial destructors

:::success Constructor/Destructor Key Points

**Order matters** = members by declaration, bases before members  
**Exceptions** = use RAII members for exception safety  
**No virtual calls** = in ctor/dtor (wrong type context)  
**Delegation** = one ctor calls another (can't mix with member init)  
**Inheriting** = `using Base::Base` inherits constructors  
**Placement new** = construct in pre-allocated memory
:::