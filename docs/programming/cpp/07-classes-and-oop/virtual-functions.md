---
id: virtual-functions-and-vtables
title: Virtual Functions and vtables
sidebar_label: Virtual Functions & vtables
sidebar_position: 9
tags: [c++, virtual-functions, vtables, polymorphism, dynamic-dispatch]
---

# Virtual Functions and vtables

Virtual functions enable runtime polymorphism through dynamic dispatch. Understanding how they work (`vtables`) helps you understand their cost and use them effectively.

:::info Runtime Polymorphism
**Virtual functions** = Call correct function based on actual object type  
**vtables** = Mechanism that makes virtual functions work  
**Cost** = Small overhead (~2-3ns per call + 8 bytes per object)
:::

## Virtual Functions Basics

Virtual functions allow calling the correct function based on the actual object type, not the pointer/reference type.
```cpp showLineNumbers
class Animal {
public:
    virtual void speak() {  // virtual keyword
        std::cout << "Animal sound\n";
    }
};

class Dog : public Animal {
public:
    void speak() override {  // override base version
        std::cout << "Woof!\n";
    }
};

class Cat : public Animal {
public:
    void speak() override {
        std::cout << "Meow!\n";
    }
};

Animal* ptr = new Dog();
ptr->speak();  // "Woof!" - calls Dog's version!
delete ptr;

ptr = new Cat();
ptr->speak();  // "Meow!" - calls Cat's version!
delete ptr;
```

The function called depends on what `ptr` actually points to at runtime, not its declared type.

## Without Virtual (Static Binding)

Without `virtual`, the compiler uses the pointer type, not the actual object type.
```cpp showLineNumbers
class Animal {
public:
    void speak() {  // NOT virtual
        std::cout << "Animal sound\n";
    }
};

class Dog : public Animal {
public:
    void speak() {  // Hides, doesn't override
        std::cout << "Woof!\n";
    }
};

Animal* ptr = new Dog();
ptr->speak();  // "Animal sound" - wrong!
// Calls Animal::speak because pointer type is Animal*

Dog* dogPtr = new Dog();
dogPtr->speak();  // "Woof!" - correct (knows it's Dog*)
```

**Static binding** (compile-time) vs **dynamic binding** (runtime):
- Without `virtual`: compiler decides at compile-time based on pointer type
- With `virtual`: decision made at runtime based on actual object

## How vtables Work

`vtables` (virtual tables) are the mechanism behind virtual functions. Each class with virtual functions gets a `vtable`, and each object gets a `vptr` (`vtable` pointer).
```cpp showLineNumbers
class Animal {
public:
    virtual void speak() { std::cout << "Animal\n"; }
    virtual void move() { std::cout << "Moving\n"; }
};

class Dog : public Animal {
public:
    void speak() override { std::cout << "Woof\n"; }
    // move() inherited
};

// Animal's vtable:        Dog's vtable:
// [0] → Animal::speak    [0] → Dog::speak (overridden)
// [1] → Animal::move     [1] → Animal::move (inherited)

Dog d;
// d's memory layout:
// [vptr → Dog's vtable][other members...]
```

**Key components:**
- `vtable` - table of function pointers (one per class)
- `vptr` - pointer to `vtable` (one per object)

### Virtual Call Mechanism
```cpp showLineNumbers
Animal* ptr = new Dog();
ptr->speak();

// Compiler generates approximately:
// 1. Load vptr from object:    vtable_ptr = ptr->vptr
// 2. Load function pointer:    func = vtable_ptr[0]
// 3. Call through pointer:     func(ptr)
```

**Steps:**
1. Dereference object to get `vptr` (1 memory read)
2. Index into `vtable` to get function pointer (1 memory read)
3. Call through function pointer (indirect call)

**vs non-virtual call:**
```cpp
ptr->nonVirtual();
// Just: call Animal::nonVirtual(ptr)
// Direct call, can be inlined
```

## vtable Memory Layout

Virtual functions add overhead to object size.
```cpp showLineNumbers
class NoVirtual {
    int data;
};
sizeof(NoVirtual);  // 4 bytes

class WithVirtual {
    int data;
    virtual void f() {}
};
sizeof(WithVirtual);  // 16 bytes (8 vptr + 4 data + 4 padding)
```

**Memory layout:**
```
Object layout:
[vptr: 8 bytes] → points to vtable
[data: 4 bytes]
[padding: 4 bytes]
Total: 16 bytes

vtable (shared by all objects):
[0] → &WithVirtual::f
[RTTI info]
```

The `vptr` is typically the first member (implementation-defined), allowing safe upcasting and downcasting.

## Override Specifier (C++11)

Use `override` to catch mistakes at compile-time.
```cpp showLineNumbers
class Base {
public:
    virtual void foo(int x) {}
    virtual void bar() const {}
};

class Derived : public Base {
public:
    void foo(double x) override {  // ❌ Error: doesn't override
        // Different parameter type!
    }
    
    void bar() override {  // ❌ Error: doesn't override
        // Missing const!
    }
    
    void foo(int x) override {  // ✅ Correct override
    }
    
    void bar() const override {  // ✅ Correct override
    }
};
```

:::success Always Use override
Catches typos, parameter mismatches, and signature differences. Makes intent clear.
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
// data is never deleted!

// ✅ Fix: virtual destructor
class Base {
public:
    virtual ~Base() { std::cout << "~Base\n"; }
};

// Now delete ptr calls ~Derived, then ~Base
```

:::danger Virtual Destructor Rule
**If your class has any virtual functions, make the destructor virtual!** Otherwise deleting through base pointer leaks resources.
:::

## Pure Virtual Functions

Pure virtual functions define an interface without implementation, making the class abstract.
```cpp showLineNumbers
class Shape {
public:
    virtual void draw() = 0;      // = 0 means pure virtual
    virtual double area() = 0;
    
    virtual ~Shape() = default;   // Virtual destructor
};

// Shape s;  // ❌ Error: can't instantiate abstract class

class Circle : public Shape {
    double radius;
public:
    void draw() override {
        std::cout << "Drawing circle\n";
    }
    
    double area() override {
        return 3.14159 * radius * radius;
    }
};

Circle c;      // ✅ OK: implemented all pure virtuals
Shape* s = &c; // ✅ OK: polymorphic use
s->draw();     // Calls Circle::draw()
```

Pure virtual functions create interfaces that derived classes must implement.

## Multiple Inheritance and vtables

Multiple inheritance with virtual functions creates multiple `vtable` pointers.
```cpp showLineNumbers
class Base1 {
public:
    virtual void f1() {}
};

class Base2 {
public:
    virtual void f2() {}
};

class Derived : public Base1, public Base2 {
public:
    void f1() override {}
    void f2() override {}
};

sizeof(Derived);  // 16 bytes (two 8-byte vptrs)
```

**Memory layout:**
```
[vptr1: 8 bytes] → Base1's vtable
[vptr2: 8 bytes] → Base2's vtable
Total: 16 bytes
```

Each base class with virtual functions contributes a `vptr`. Pointer conversions may require address adjustment.
```cpp showLineNumbers
Derived d;
Base1* p1 = &d;  // Points to start
Base2* p2 = &d;  // Points to Base2 subobject (different address!)

// p1 != p2 (pointer adjustment occurs)
```

## Performance Implications

Virtual functions have small but measurable cost.
```cpp showLineNumbers
class Widget {
public:
    virtual void process() {  // Virtual call
        // Implementation
    }
    
    void processNonVirtual() {  // Non-virtual call
        // Implementation
    }
};

// Benchmark: 1 million calls
Widget w;

// Virtual: ~3ns per call = 3ms total
for (int i = 0; i < 1000000; ++i) {
    w.process();  // vtable lookup + indirect call
}

// Non-virtual: ~1ns per call = 1ms total
for (int i = 0; i < 1000000; ++i) {
    w.processNonVirtual();  // direct call, can inline
}
```

**Costs:**
- **Memory:** 8 bytes per object (`vptr`)
- **CPU:** ~2-3ns per virtual call
- **Cache:** May miss if calling many different types
- **Inlining:** Virtual calls usually can't be inlined

**When it matters:**
- Tight loops with millions of calls
- Embedded systems with limited memory
- Real-time systems with strict timing

**Usually negligible** for most applications!

## Final Specifier (C++11)

Prevent further overriding of virtual functions.
```cpp showLineNumbers
class Base {
public:
    virtual void foo() {}
};

class Derived : public Base {
public:
    void foo() final {  // Can't be overridden further
        std::cout << "Derived::foo\n";
    }
};

class MoreDerived : public Derived {
public:
    // void foo() override {}  // ❌ Error: foo is final
};
```

`final` also works on classes to prevent inheritance:
```cpp showLineNumbers
class Sealed final {
    // Cannot be inherited from
};

// class Derived : public Sealed {};  // ❌ Error
```

## Covariant Return Types

Overriding function can return a more derived type.
```cpp showLineNumbers
class Base {
public:
    virtual Base* clone() {
        return new Base(*this);
    }
};

class Derived : public Base {
public:
    Derived* clone() override {  // Returns Derived*, not Base*
        return new Derived(*this);
    }
};

Derived d;
Derived* copy = d.clone();  // Returns Derived* directly
// No cast needed!
```

The return type can be more specific (covariant) as long as it's a pointer or reference to a derived class.

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
    
    virtual ~Base() {
        cleanup();  // ⚠️ Calls Base::cleanup
    }
    
    virtual void cleanup() {
        std::cout << "Base cleanup\n";
    }
};

class Derived : public Base {
public:
    void init() override { 
        std::cout << "Derived init\n"; 
    }
    
    void cleanup() override {
        std::cout << "Derived cleanup\n";
    }
};

Derived d;
// Output: "Base init" (not "Derived init")
// Destruction: "Base cleanup" (not "Derived cleanup")
```

**Why?** During construction/destruction, the object's type gradually changes:
- In Base constructor → object is a Base (Derived part not constructed yet)
- In Derived constructor → object becomes Derived
- In Derived destructor → object becomes Base again (Derived part destroyed)
- In Base destructor → object is a Base

## Devirtualization

Compilers can sometimes optimize away virtual calls when the exact type is known.
```cpp showLineNumbers
void example1() {
    Dog d;
    d.speak();  // Compiler knows exact type: direct call!
    // No vtable lookup needed
}

void example2(Animal* a) {
    a->speak();  // Must use vtable (don't know actual type)
}

void example3(Dog& d) {
    d.speak();  // Might be devirtualized if inlined
}
```

Modern compilers can devirtualize when:
- Exact type is known at compile-time
- Function is inlined and type becomes visible
- Link-time optimization reveals actual type

## Default Arguments Trap

Virtual functions and default arguments don't mix well.
```cpp showLineNumbers
class Base {
public:
    virtual void print(int x = 10) {
        std::cout << "Base: " << x << "\n";
    }
};

class Derived : public Base {
public:
    void print(int x = 20) override {
        std::cout << "Derived: " << x << "\n";
    }
};

Base* ptr = new Derived();
ptr->print();  // "Derived: 10" ⚠️
// Calls Derived::print (virtual dispatch)
// But uses Base's default argument (static binding)!
```

:::warning Avoid Different Defaults
Don't use different default arguments in overridden functions. Default arguments are bound at compile-time, not runtime.
:::

## Non-Virtual Interface (NVI) Idiom

Separate the interface (non-virtual public) from customization points (virtual private).
```cpp showLineNumbers
class Widget {
public:
    // Public non-virtual interface
    void doWork() {
        setup();        // Pre-work
        doWorkImpl();   // Virtual customization point
        cleanup();      // Post-work
    }
    
private:
    // Private virtual implementation
    virtual void doWorkImpl() = 0;
    
    void setup() { /* ... */ }
    void cleanup() { /* ... */ }
};

class ConcreteWidget : public Widget {
private:
    void doWorkImpl() override {
        // Actual work here
    }
};
```

**Benefits:**
- Base class controls the workflow
- Derived classes only customize implementation
- Pre/post conditions enforced
- Interface is stable (non-virtual)

## RTTI and vtables

Run-Time Type Information uses `vtable` data.
```cpp showLineNumbers
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {};

Base* ptr = new Derived();

// dynamic_cast uses vtable for type checking
Derived* d = dynamic_cast<Derived*>(ptr);  // Works!
if (d) {
    std::cout << "It's a Derived\n";
}

// typeid uses vtable
std::cout << typeid(*ptr).name();  // "Derived"

// Only works with polymorphic types (have virtual functions)
```

RTTI information is stored with the `vtable`, enabling `dynamic_cast` and `typeid`.

## Summary

:::info Virtual functions
- Enable runtime polymorphism (dynamic dispatch)
- Use `virtual` keyword in base class
- Use `override` in derived class (catches errors)
- Call correct function based on actual object type
:::

:::info vtables mechanism
- Each class gets one `vtable` (function pointer table)
- Each object gets one `vptr` (points to class's `vtable`)
- Virtual call: load `vptr` → index `vtable` → call function
- 2-3ns overhead per call + 8 bytes per object
:::

:::info Best practices
- Always use `override` keyword
- Virtual destructor if base class has virtual functions
- Pure virtual (`= 0`) for interfaces
- `final` to prevent further overriding
- Avoid different default arguments
:::

:::info Special cases
- Multiple inheritance: multiple `vptr`s
- Covariant return types: can return derived type
- Don't call virtuals in constructor/destructor
- Devirtualization when compiler knows exact type
:::

:::info Costs
- Memory: 8 bytes per object (`vptr`)
- CPU: 2-3ns per call (vs 1ns direct call)
- Can't inline virtual calls (usually)
- Usually negligible in practice
:::

:::info Alternatives
- Templates (static polymorphism, zero overhead)
- Function pointers (manual `vtable`)
- std::variant + std::visit (value-based polymorphism)
:::