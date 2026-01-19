---
id: inheritance
title: Inheritance
sidebar_label: Inheritance
sidebar_position: 6
tags: [c++, inheritance, polymorphism, oop]
---

# Inheritance

Inheritance lets you create new classes based on existing ones, reusing code and establishing "is-a" relationships. Derived classes inherit members from base classes and can add new functionality or override existing behavior.

:::info Base and Derived
**Base class** (parent) provides common functionality  
**Derived class** (child) inherits and extends or specializes
:::

## Basic Inheritance

```cpp
class Animal {
protected:
    std::string name;
    
public:
    Animal(std::string n) : name(n) {}
    
    void eat() { std::cout << name << " is eating\n"; }
};

class Dog : public Animal {  // Dog inherits from Animal
public:
    Dog(std::string n) : Animal(n) {}  // Call base constructor
    
    void bark() { std::cout << name << " says woof!\n"; }
};

Dog d("Buddy");
d.eat();   // ✅ Inherited from Animal
d.bark();  // ✅ Defined in Dog
```

**Key points:**
- Dog has everything Animal has plus its own stuff
- `protected` members accessible in derived class
- Must call base constructor in derived constructor initializer list

## Access Control in Inheritance

The inheritance specifier affects how base members appear in derived class:

```cpp
class Base {
public:    int pub;
protected: int prot;
private:   int priv;
};

// Public inheritance (most common)
class Derived1 : public Base {
    // pub stays public
    // prot stays protected
    // priv inaccessible
};

// Protected inheritance (rare)
class Derived2 : protected Base {
    // pub becomes protected
    // prot stays protected  
    // priv inaccessible
};

// Private inheritance (implementation reuse)
class Derived3 : private Base {
    // pub becomes private
    // prot becomes private
    // priv inaccessible
};
```

**Public inheritance** = "is-a" relationship (Dog IS-A Animal)  
**Private inheritance** = "implemented-in-terms-of" (rare, prefer composition)

## Virtual Functions

Virtual functions enable polymorphism - calling the right function based on actual object type:

```cpp
class Shape {
public:
    virtual void draw() {  // virtual = can be overridden
        std::cout << "Drawing shape\n";
    }
    
    virtual ~Shape() = default;  // Always virtual destructor!
};

class Circle : public Shape {
public:
    void draw() override {  // override = replacing base version
        std::cout << "Drawing circle\n";
    }
};

Shape* s = new Circle();
s->draw();  // "Drawing circle" (calls Circle's version!)
delete s;   // Calls Circle's destructor (virtual!)
```

**Without virtual:** Calls base class version (static binding)  
**With virtual:** Calls actual object's version (dynamic binding)

## Pure Virtual and Abstract Classes

Pure virtual functions have no implementation and make class abstract:

```cpp
class Shape {
public:
    virtual void draw() = 0;  // = 0 means pure virtual
    virtual double area() = 0;
    
    virtual ~Shape() = default;
};

// Shape s;  // ❌ Error: can't instantiate abstract class

class Rectangle : public Shape {
public:
    void draw() override { /* must implement */ }
    double area() override { return width * height; }
    
private:
    double width, height;
};

Rectangle r;  // ✅ OK: all pure virtuals implemented
```

Abstract classes define interfaces that derived classes must implement.

## Override and Final

Modern C++ keywords make intent explicit:

```cpp
class Base {
public:
    virtual void foo() {}
    virtual void bar() {}
};

class Derived : public Base {
public:
    void foo() override {  // ✅ Explicitly overriding
        // If foo() doesn't exist in Base, compiler error
    }
    
    void bar() final {  // final = can't override further
        // No further derived class can override bar()
    }
    
    // void baz() override {}  // ❌ Error: nothing to override
};

class MoreDerived : public Derived {
    // void bar() override {}  // ❌ Error: bar is final
};
```

## Constructor and Destructor Order

```cpp
class Base {
public:
    Base() { std::cout << "Base constructor\n"; }
    ~Base() { std::cout << "Base destructor\n"; }
};

class Derived : public Base {
public:
    Derived() { std::cout << "Derived constructor\n"; }
    ~Derived() { std::cout << "Derived destructor\n"; }
};

Derived d;
// Output:
// Base constructor
// Derived constructor
// Derived destructor  
// Base destructor
```

**Construction:** Base → Derived (bottom-up)  
**Destruction:** Derived → Base (top-down, reverse order)

## Virtual Destructors

Always make base class destructor virtual if you'll delete through base pointer:

```cpp
class Base {
public:
    ~Base() { std::cout << "~Base\n"; }  // ❌ Not virtual!
};

class Derived : public Base {
    int* data;
public:
    Derived() : data(new int[100]) {}
    ~Derived() { delete[] data; std::cout << "~Derived\n"; }
};

Base* ptr = new Derived();
delete ptr;  // ⚠️ Only calls ~Base, not ~Derived! Memory leak!

// ✅ Fix: virtual destructor
class Base {
public:
    virtual ~Base() { std::cout << "~Base\n"; }
};
// Now delete ptr calls both destructors correctly
```

## Slicing Problem

Copying derived object to base object "slices off" derived parts:

```cpp
class Base {
public:
    int x = 1;
    virtual void print() { std::cout << "Base\n"; }
};

class Derived : public Base {
public:
    int y = 2;
    void print() override { std::cout << "Derived\n"; }
};

Derived d;
Base b = d;  // ⚠️ Slicing! y is lost

b.print();  // "Base" (not "Derived"!)
// Only Base part was copied, Derived part lost
```

**Solution:** Use pointers or references to maintain polymorphism.

:::success Inheritance Checklist

**public inheritance** = is-a relationship  
**virtual functions** = runtime polymorphism  
**override keyword** = catch typos at compile-time  
**virtual destructor** = essential for base classes  
**Pure virtual (=0)** = defines interface  
**final keyword** = prevent further overriding  
**Avoid slicing** = use pointers/references for polymorphism
:::