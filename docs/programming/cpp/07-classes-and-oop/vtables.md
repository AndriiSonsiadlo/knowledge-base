---
id: vtables
title: Virtual Tables (vtables)
sidebar_label: vtables
sidebar_position: 10
tags: [c++, vtables, virtual-functions, implementation]
---

# Virtual Tables (vtables)

vtables are the mechanism that makes virtual functions work. Understanding vtables helps you understand the cost of polymorphism and how inheritance works under the hood.

:::info How Virtual Calls Work
Each object with virtual functions has a **vptr** (vtable pointer) pointing to its class's **vtable** (virtual function table). The vtable contains pointers to the actual functions to call.
:::

## Basic vtable Structure

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

// Animal's vtable:
// [0]: &Animal::speak
// [1]: &Animal::move

// Dog's vtable:
// [0]: &Dog::speak     (overridden)
// [1]: &Animal::move   (inherited)

Dog d;
// d's memory layout:
// [vptr → Dog's vtable][other members...]
```

Each class with virtual functions has one shared vtable. Each object has its own vptr pointing to its class's vtable.

## How Virtual Calls Work

```cpp showLineNumbers 
Animal* ptr = new Dog();
ptr->speak();

// Compiler generates approximately:
// 1. Load vptr from ptr: vtable_ptr = ptr->vptr
// 2. Load function pointer: func = vtable_ptr[0]  (speak is at index 0)
// 3. Call function: func(ptr)  (ptr becomes 'this')
```

**Steps:**
1. Dereference object to get vptr
2. Index into vtable to get function pointer
3. Call through function pointer

**vs non-virtual call:**
```cpp showLineNumbers 
ptr->nonVirtualFunc();
// Just: call Animal::nonVirtualFunc(ptr)
// Direct call, no indirection
```

## vtable Memory Layout

```cpp showLineNumbers 
class Base {
    int data;           // 4 bytes
public:
    virtual void f() {}  // Adds vptr
};

sizeof(Base);  // 16 bytes (8 vptr + 4 data + 4 padding)

// Memory layout:
// [vptr: 8 bytes][data: 4 bytes][padding: 4 bytes]
```

The vptr is typically the first member (implementation-defined), allowing safe downcasting and upcasting.

## Multiple Inheritance and vtables

Multiple inheritance with virtual functions gets complex:

```cpp showLineNumbers 
class A {
public:
    virtual void fa() {}
};

class B {
public:
    virtual void fb() {}
};

class C : public A, public B {
public:
    void fa() override {}
    void fb() override {}
};

// C has TWO vptrs:
// [vptr_A][A's data][vptr_B][B's data][C's data]

C obj;
A* pa = &obj;  // Points to start
B* pb = &obj;  // Points to B subobject (different address!)
// pa != pb (pointer adjustment)
```

Each base class with virtual functions contributes a vptr. Pointer conversions adjust the address to point to the right subobject.

## vtable Construction

vtables are constructed during compilation:

```cpp showLineNumbers 
// Compiler generates (pseudocode):
struct Animal_vtable {
    void (*speak)(Animal*);  // &Animal::speak
    void (*move)(Animal*);   // &Animal::move
};

Animal_vtable Animal_vtable_instance = {
    &Animal::speak,
    &Animal::move
};

struct Dog_vtable {
    void (*speak)(Animal*);  // &Dog::speak (overridden!)
    void (*move)(Animal*);   // &Animal::move (inherited)
};

Dog_vtable Dog_vtable_instance = {
    &Dog::speak,     // Points to Dog's implementation
    &Animal::move    // Points to Animal's implementation
};
```

vtables are constant, read-only data created at compile-time.

## RTTI and vtables

Run-Time Type Information is stored with vtables:

```cpp showLineNumbers 
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {};

Base* ptr = new Derived();

// dynamic_cast uses vtable to check type
Derived* d = dynamic_cast<Derived*>(ptr);  // Works!

// typeid uses vtable
std::cout << typeid(*ptr).name();  // "Derived"
```

RTTI information is stored near the vtable, enabling `dynamic_cast` and `typeid` for polymorphic types.

## Performance Implications

```cpp showLineNumbers 
class Hot {
public:
    virtual void process() {  // Virtual
        // Called in tight loop
    }
};

// Tight loop performance:
for (int i = 0; i < 1000000; ++i) {
    obj.process();
    // Each call: load vptr, load function, indirect call
    // ~3ns overhead per call = 3ms total
}

// Non-virtual alternative:
for (int i = 0; i < 1000000; ++i) {
    obj.processNonVirtual();
    // Direct call, compiler can inline
    // ~1ns per call = 1ms total
}
```

**Costs:**
- Memory: 8 bytes per object (vptr)
- CPU: 2-3ns per virtual call
- Cache: May miss if calling many different types
- Inlining: Virtual calls usually can't be inlined

## devirtualization

Compilers can sometimes optimize away virtual calls:

```cpp showLineNumbers 
void process() {
    Dog d;
    d.speak();  // Compiler knows exact type: direct call!
    // No vtable lookup needed
}

void process(Animal* a) {
    a->speak();  // Must use vtable (don't know actual type)
}
```

If the compiler knows the exact object type, it can skip the vtable lookup and call directly.

## Examining vtables

Use compiler flags to see vtable layout:

```bash
# GCC/Clang
g++ -fdump-class-hierarchy file.cpp

# MSVC  
cl /d1reportAllClassLayout file.cpp

# Output shows:
# - vtable layout
# - vptr location
# - Function pointer mappings
```

## Virtual Inheritance and vtables

Virtual inheritance adds complexity:

```cpp showLineNumbers 
class A {
public:
    virtual void f() {}
};

class B : virtual public A {};
class C : virtual public A {};
class D : public B, public C {};

// D has:
// - vptr for B
// - vptr for C  
// - vptr for shared A
// vtables contain offsets to find the shared A subobject
```

Virtual inheritance requires additional vtable entries for offset information to locate the shared base class.

:::success vtable Key Points

**vptr per object** = pointer to class's vtable (8 bytes)  
**vtable per class** = shared table of function pointers  
**Virtual call** = load vptr → index vtable → call function  
**Overhead** = ~2-3ns per call + 8 bytes per object  
**Multiple inheritance** = multiple vptrs per object  
**RTTI** = stored with vtable data  
**devirtualization** = compiler optimizes when type known
:::