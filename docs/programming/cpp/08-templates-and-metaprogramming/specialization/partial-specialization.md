---
id: partial-specialization
title: Partial Template Specialization
sidebar_label: Partial Specialization
sidebar_position: 2
tags: [c++, templates, partial-specialization, template-specialization]
---

# Partial Template Specialization

Partial specialization lets you specialize templates for a pattern of types, not just one specific type. It's like "for all pointer types" or "for all pairs of same types."

:::info Pattern Matching
Partial specialization = specialize for type patterns. Full specialization = one exact type. Partial = whole categories of types.
:::

## Basic Partial Specialization

```cpp
// Primary template
template<typename T, typename U>
class Pair {
public:
    T first;
    U second;
    void info() { std::cout << "Different types\n"; }
};

// Partial specialization: both same type
template<typename T>
class Pair<T, T> {  // Pattern: both parameters same
public:
    T first;
    T second;
    void info() { std::cout << "Same type\n"; }
    
    void swap() {  // Extra functionality
        std::swap(first, second);
    }
};

Pair<int, double> p1;  // Primary template
p1.info();  // "Different types"

Pair<int, int> p2;  // Partial specialization
p2.info();  // "Same type"
p2.swap();  // Available!
```

**Pattern:** `T, T` matches any two identical types.

## Specialization for Pointers

```cpp
// Primary template
template<typename T>
class SmartPtr {
    T value;
public:
    void set(T v) { value = v; }
    T get() { return value; }
};

// Partial specialization for pointers
template<typename T>
class SmartPtr<T*> {  // Pattern: any pointer type
    T* ptr;
public:
    T& operator*() { return *ptr; }
    T* operator->() { return ptr; }
    T* get() { return ptr; }
};

SmartPtr<int> s1;      // Primary template
s1.set(42);

SmartPtr<int*> s2;     // Pointer specialization
int x = 42;
s2 = &x;
*s2;  // Dereference works
```

## Multiple Parameter Patterns

```cpp
// Primary: three different types
template<typename T, typename U, typename V>
class Triple {
    void info() { std::cout << "Three different types\n"; }
};

// Partial: first two same
template<typename T, typename V>
class Triple<T, T, V> {
    void info() { std::cout << "First two same\n"; }
};

// Partial: all three same
template<typename T>
class Triple<T, T, T> {
    void info() { std::cout << "All same\n"; }
};

Triple<int, double, char> t1;  // Primary
Triple<int, int, char> t2;     // First two same
Triple<int, int, int> t3;      // All same (most specialized!)
```

## const Specialization

```cpp
// Primary template
template<typename T>
class Wrapper {
public:
    void modify(T& value) {
        value = T{};  // Can modify
    }
};

// Partial specialization for const
template<typename T>
class Wrapper<const T> {
public:
    void modify(const T& value) {
        // Cannot modify const value
        std::cout << "Cannot modify const\n";
    }
};

Wrapper<int> w1;
int x = 42;
w1.modify(x);  // Modifies

Wrapper<const int> w2;
const int cx = 42;
w2.modify(cx);  // "Cannot modify const"
```

## Reference Specialization

```cpp
// Primary template
template<typename T>
class Storage {
    T value;
public:
    void set(T v) { value = v; }
};

// Partial specialization for references
template<typename T>
class Storage<T&> {  // References need special handling
    T* ptr;  // Store pointer instead
public:
    Storage(T& ref) : ptr(&ref) {}
    void set(T v) { *ptr = v; }
};

int x = 42;
Storage<int> s1;
s1.set(100);  // Stores copy

Storage<int&> s2(x);  // Stores reference
s2.set(200);  // Modifies x!
std::cout << x;  // 200
```

## Array Specialization

```cpp
// Primary template
template<typename T>
class Container {
public:
    void info() { std::cout << "Generic\n"; }
};

// Partial specialization for arrays
template<typename T, size_t N>
class Container<T[N]> {
    T data[N];
public:
    void info() {
        std::cout << "Array of " << N << " elements\n";
    }
    
    size_t size() const { return N; }
};

Container<int> c1;
c1.info();  // "Generic"

Container<int[10]> c2;
c2.info();  // "Array of 10 elements"
c2.size();  // 10
```

## Function Objects vs Function Pointers

```cpp
template<typename T>
class Callback {
public:
    void info() { std::cout << "Functor\n"; }
};

// Partial specialization for function pointers
template<typename Ret, typename... Args>
class Callback<Ret(*)(Args...)> {
public:
    void info() { std::cout << "Function pointer\n"; }
};

struct Functor {
    void operator()() {}
};

Callback<Functor> c1;
c1.info();  // "Functor"

Callback<void(*)()> c2;
c2.info();  // "Function pointer"
```

## Nested Template Specialization

```cpp
// Primary template
template<typename T>
class Outer {
public:
    void info() { std::cout << "Generic outer\n"; }
};

// Partial: specialization for containers
template<template<typename> class Container, typename T>
class Outer<Container<T>> {
public:
    void info() {
        std::cout << "Container with element type\n";
    }
};

Outer<int> o1;
o1.info();  // "Generic outer"

Outer<std::vector<int>> o2;
o2.info();  // "Container with element type"
```

## Specialization Priority

More specialized templates are chosen:

```cpp
// Primary: most general
template<typename T, typename U>
class Widget {
    void print() { std::cout << "1: General\n"; }
};

// Partial: pointer pattern
template<typename T, typename U>
class Widget<T*, U*> {
    void print() { std::cout << "2: Both pointers\n"; }
};

// Partial: same type pattern
template<typename T>
class Widget<T, T> {
    void print() { std::cout << "3: Same types\n"; }
};

// Partial: both same pointer type
template<typename T>
class Widget<T*, T*> {
    void print() { std::cout << "4: Same pointer types\n"; }
};

Widget<int, double> w1;    // 1: General
Widget<int*, double*> w2;  // 2: Both pointers
Widget<int, int> w3;       // 3: Same types
Widget<int*, int*> w4;     // 4: Same pointer types (most specialized!)
```

Compiler picks most specific match!

## Remove Reference Implementation

```cpp
// Primary: does nothing
template<typename T>
struct remove_reference {
    using type = T;
};

// Partial: remove lvalue reference
template<typename T>
struct remove_reference<T&> {
    using type = T;
};

// Partial: remove rvalue reference
template<typename T>
struct remove_reference<T&&> {
    using type = T;
};

remove_reference<int>::type;     // int
remove_reference<int&>::type;    // int
remove_reference<int&&>::type;   // int
```

This is how `std::remove_reference` works!

## Conditional Type Selection

```cpp
// Primary: select first type
template<bool Condition, typename T, typename F>
struct conditional {
    using type = T;
};

// Partial: when condition is false, select second
template<typename T, typename F>
struct conditional<false, T, F> {
    using type = F;
};

conditional<true, int, double>::type;   // int
conditional<false, int, double>::type;  // double
```

Implementation of `std::conditional`!

## is_same Implementation

```cpp
// Primary: types are different
template<typename T, typename U>
struct is_same {
    static constexpr bool value = false;
};

// Partial: both types identical
template<typename T>
struct is_same<T, T> {
    static constexpr bool value = true;
};

is_same<int, int>::value;     // true
is_same<int, double>::value;  // false
```

## Complex Pattern Matching

```cpp
// Primary template
template<typename T>
class Parser {
    void info() { std::cout << "Generic parser\n"; }
};

// Partial: std::pair
template<typename T, typename U>
class Parser<std::pair<T, U>> {
    void info() { std::cout << "Pair parser\n"; }
};

// Partial: std::vector
template<typename T>
class Parser<std::vector<T>> {
    void info() { std::cout << "Vector parser\n"; }
};

// Partial: std::map
template<typename K, typename V>
class Parser<std::map<K, V>> {
    void info() { std::cout << "Map parser\n"; }
};

Parser<int> p1;
Parser<std::pair<int, int>> p2;
Parser<std::vector<int>> p3;
Parser<std::map<int, std::string>> p4;
```

## Function Templates Can't Be Partially Specialized

```cpp
// ❌ Partial specialization not allowed for functions!
template<typename T>
void process(T value) { /* ... */ }

// template<typename T>
// void process<T*>(T* value) { /* ❌ Error! */ }

// ✅ Solution: Overload or use class template
template<typename T>
void process(T value) { /* General */ }

template<typename T>
void process(T* value) { /* Pointers */ }  // Overload, not specialization
```

## Avoiding Ambiguity

```cpp
template<typename T, typename U>
class X;

// Partial 1
template<typename T>
class X<T, T*> { /* ... */ };

// Partial 2
template<typename T>
class X<T*, T> { /* ... */ };

// X<int*, int*> is ambiguous!
// Both partials match equally
// ❌ Compilation error
```

Make sure specializations don't overlap ambiguously.

:::success Partial Specialization Essentials

**Pattern matching** = specialize for type categories  
**Class templates only** = functions can't be partially specialized  
**More specific wins** = compiler picks best match  
**Common patterns** = pointers, references, const, arrays  
**Type traits** = implemented with partial specialization  
**Template parameters** = some specified, some remain generic  
**Ambiguity** = avoid overlapping patterns  
**Use cases** = optimization, type-specific behavior, metaprogramming
:::