---
id: template-argument-deduction
title: Template Argument Deduction
sidebar_label: Argument Deduction
sidebar_position: 3
tags: [c++, templates, deduction, type-deduction]
---

# Template Argument Deduction

Template argument deduction lets the compiler figure out template parameters from function arguments automatically. No need to write `func<int>(5)` when `func(5)` works!

:::info Compiler Figures It Out
The compiler examines function arguments and deduces template parameters. Usually just works, but understanding the rules helps debug errors.
:::

## Basic Deduction

```cpp
template<typename T>
void func(T param) {
    // ...
}

func(5);        // T deduced as int
func(3.14);     // T deduced as double
func("hello");  // T deduced as const char*

std::string s = "world";
func(s);        // T deduced as std::string
```

Compiler matches argument types to template parameters automatically.

## Reference Deduction

**lvalue reference:**
```cpp
template<typename T>
void func(T& param) {
    // ...
}

int x = 42;
const int cx = x;

func(x);   // T = int, param type is int&
func(cx);  // T = const int, param type is const int&
// func(5);   // ❌ Error: can't bind rvalue to lvalue ref
```

**const reference:**
```cpp
template<typename T>
void func(const T& param) {
    // ...
}

func(x);   // T = int, param = const int&
func(cx);  // T = int, param = const int& (const is redundant)
func(5);   // ✅ OK: const ref binds to rvalue
```

**rvalue reference (forwarding reference):**
```cpp
template<typename T>
void func(T&& param) {  // Universal/forwarding reference
    // ...
}

int x = 42;
func(x);         // lvalue: T = int&, param = int&
func(42);        // rvalue: T = int, param = int&&
func(std::move(x));  // rvalue: T = int, param = int&&
```

## Pointer Deduction

```cpp
template<typename T>
void func(T* param) {
    // ...
}

int x = 42;
const int cx = 100;

func(&x);   // T = int, param = int*
func(&cx);  // T = const int, param = const int*
```

## Array Deduction

```cpp
template<typename T>
void func(T param) {
    // ...
}

int arr[10];
func(arr);  // T = int* (array decays to pointer)

// With reference: preserves array type!
template<typename T>
void func2(T& param) {
    // ...
}

func2(arr);  // T = int[10], param = int(&)[10]

// Deduce array size
template<typename T, size_t N>
size_t arraySize(T (&)[N]) {
    return N;
}

int arr[15];
size_t size = arraySize(arr);  // N = 15
```

## const and Reference Stripping

```cpp
template<typename T>
void func(T param) {  // Pass by value
    // ...
}

int x = 42;
const int cx = x;
const int& rx = x;

func(x);   // T = int (copy, const ignored)
func(cx);  // T = int (copy, const stripped)
func(rx);  // T = int (copy, reference and const stripped)
```

When passing by value, top-level const and references are stripped because you're getting a copy anyway.

## Multiple Parameters

```cpp
template<typename T>
void func(T a, T b) {  // Both must be same type
    // ...
}

func(5, 10);      // ✅ T = int
// func(5, 3.14);   // ❌ Error: conflicting types (int vs double)

// Solution: Multiple template parameters
template<typename T, typename U>
void func2(T a, U b) {
    // ...
}

func2(5, 3.14);  // ✅ T = int, U = double
```

## Explicit Template Arguments

```cpp
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

auto x = max(5, 10);        // T = int
auto y = max<double>(5, 10);  // Force T = double (converts args)

// Can specify some, deduce others
template<typename R, typename T>
R convert(T value) {
    return static_cast<R>(value);
}

int x = 42;
double d = convert<double>(x);  // R = double (specified), T = int (deduced)
```

## Return Type Deduction

```cpp
// C++11: Trailing return with decltype
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

// C++14: Auto return type deduction
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;  // Return type deduced from expression
}

auto x = add(5, 3.14);  // Returns double
```

## Class Template Argument Deduction (CTAD - C++17)

```cpp
template<typename T>
class Pair {
public:
    T first, second;
    Pair(T a, T b) : first(a), second(b) {}
};

// Before C++17
Pair<int> p1(10, 20);

// C++17: Deduction from constructor
Pair p2(10, 20);  // Deduced as Pair<int>
Pair p3(3.14, 2.71);  // Deduced as Pair<double>

// std::vector example
std::vector v{1, 2, 3, 4, 5};  // Deduced as vector<int>
```

## Deduction Guides (C++17)

Help the compiler deduce template arguments:

```cpp
template<typename T>
class Container {
public:
    Container(T value) { /* ... */ }
};

// Deduction guide
template<typename T>
Container(T) -> Container<T>;

Container c(42);  // Deduced as Container<int>

// For const char*
Container(const char*) -> Container<std::string>;
Container c2("hello");  // Deduced as Container<std::string>
```

## Common Deduction Failures

```cpp
template<typename T>
void func(T a, T b) {
    // ...
}

// ❌ Type mismatch
// func(5, 3.14);  // int vs double

// ❌ Can't deduce from return type alone
template<typename T>
T convert(int value) {
    return static_cast<T>(value);
}
// auto x = convert(42);  // ❌ Can't deduce T
auto x = convert<double>(42);  // ✅ Must specify

// ❌ Non-deduced context
template<typename T>
void func(typename std::vector<T>::iterator it) {
    // ...
}
// Can't deduce T from iterator type (nested dependent type)
```

## Perfect Forwarding

```cpp
template<typename T>
void wrapper(T&& arg) {
    // Forward preserving value category
    actualFunction(std::forward<T>(arg));
}

int x = 42;
wrapper(x);          // T = int&, forwards lvalue
wrapper(42);         // T = int, forwards rvalue
wrapper(std::move(x));  // T = int, forwards rvalue
```

:::success Deduction Rules Summary

**By value** = strips const and references  
**By reference** = preserves const, deduces reference  
**By pointer** = deduces pointer, preserves const  
**Array** = decays to pointer unless reference parameter  
**Universal ref (T&&)** = forwards lvalue/rvalue correctly  
**CTAD (C++17)** = deduce class template args from constructor  
**Explicit args** = can override deduction  
**Multiple params** = all T must match unless separate template params
:::
