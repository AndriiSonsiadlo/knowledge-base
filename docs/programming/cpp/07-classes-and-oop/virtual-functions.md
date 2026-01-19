---
id: virtual-functions
title: Virtual Functions
sidebar_label: Virtual Functions
sidebar_position: 9
tags: [c++, virtual-functions, polymorphism, dynamic-dispatch]
---

# Virtual Functions

Virtual functions enable runtime polymorphism - calling the correct function based on the actual object type, not the pointer/reference type.

:::info Runtime Polymorphism
**Without virtual**: Compiler decides at compile-time (static binding)  
**With virtual**: Decision made at runtime based on actual object type (dynamic binding)
:::

## Basic Virtual Functions

```cpp
class Animal {
public:
    virtual void speak() {  // virtual keyword
        std::cout << "Animal sound\n";
    }
};

class Dog : public Animal {
public:
    void speak() override {  // overrides base version
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

**Key point**: The function called depends on what `ptr` actually points to, not its declared type.

## Without Virtual (Static Binding)

```cpp
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
```

Without `virtual`, the compiler uses the pointer type, not the actual object type.

## Override Specifier (C++11)

Use `override` to catch mistakes:

```cpp
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
};
```

`override` makes the compiler verify you're actually overriding something. Catches typos and signature mismatches.

## Virtual Destructors

Always make base class destructor virtual if you'll delete through base pointer:

```cpp
class Base {
public:
    virtual ~Base() {  // MUST be virtual!
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
delete ptr;  // Calls both destructors correctly!
// Output: ~Derived, ~Base

// Without virtual destructor:
// Only ~Base called, data leaked! ⚠️
```

**Rule**: If your class has any virtual functions, make the destructor virtual.

## Pure Virtual Functions

Pure virtual functions have no implementation and make the class abstract:

```cpp
class Shape {
public:
    virtual void draw() = 0;  // = 0 means pure virtual
    virtual double area() = 0;
    
    virtual ~Shape() = default;
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

Circle c;  // ✅ OK: implemented all pure virtuals
Shape* s = &c;  // ✅ OK: polymorphic use
```

Pure virtual functions define an interface that derived classes must implement.

## Virtual Function Performance

Virtual functions have a small performance cost:

```cpp
class Base {
public:
    virtual void vfunc() {}  // Virtual: ~3ns overhead
    void regular() {}         // Non-virtual: ~1ns
};

// Cost breakdown:
// 1. Load vtable pointer from object (1 memory access)
// 2. Load function pointer from vtable (1 memory access)
// 3. Indirect call through pointer
// vs direct call for non-virtual

// Memory cost: 8 bytes per object (vtable pointer)
sizeof(Base);  // 8 bytes (just the vtable pointer)
```

**Real impact**: Usually negligible. Only matters in extremely tight loops. The flexibility usually outweighs the tiny cost.

## Final Specifier (C++11)

Prevent further overriding:

```cpp
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

Use `final` when you know the implementation is complete and shouldn't be changed by further derived classes.

## Covariant Return Types

Overriding function can return a derived type:

```cpp
class Base {
public:
    virtual Base* clone() {
        return new Base(*this);
    }
};

class Derived : public Base {
public:
    Derived* clone() override {  // Returns Derived*, not Base*!
        return new Derived(*this);
    }
};

Derived d;
Derived* copy = d.clone();  // Returns Derived* directly
```

The return type can be more specific in the derived class, as long as it's a pointer or reference to a derived class.

## Virtual Function Access

Virtual functions can be called even with different access levels:

```cpp
class Base {
private:
    virtual void secret() {
        std::cout << "Base secret\n";
    }
    
public:
    void callSecret() {
        secret();  // Calls through virtual mechanism
    }
};

class Derived : public Base {
public:
    void secret() override {  // public in Derived!
        std::cout << "Derived secret\n";
    }
};

Derived d;
d.callSecret();  // "Derived secret" - calls public Derived version!
```

Access control is checked at compile-time based on the static type, but the virtual call happens based on dynamic type.

## Default Arguments

Virtual functions and default arguments don't mix well:

```cpp
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
// Calls Derived::print (virtual)
// But uses Base's default argument (static)!
```

**Avoid**: Don't use different default arguments in overridden functions. Default arguments are bound at compile-time, not runtime.

## Virtual vs Non-Virtual Interface (NVI)

The Non-Virtual Interface idiom:

```cpp
class Widget {
public:
    // Public non-virtual interface
    void doWork() {
        setup();        // Do pre-work
        doWorkImpl();   // Virtual implementation
        cleanup();      // Do post-work
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

Benefits: Base class controls the workflow, derived classes only customize the implementation.

:::success Virtual Function Essentials

**virtual keyword** = enables runtime polymorphism  
**override** = catches override mistakes (use it!)  
**= 0** = pure virtual (interface definition)  
**Virtual destructor** = essential for base classes  
**final** = prevent further overriding  
**Small cost** = ~2-3ns overhead (usually negligible)  
**Covariant returns** = can return derived type
:::