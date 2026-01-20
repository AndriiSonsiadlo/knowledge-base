---
id: function-templates
title: Function Templates
sidebar_label: Function Templates
sidebar_position: 1
tags: [c++, templates, generic-programming, function-templates]
---

# Function Templates

Function templates let you write one function that works with different types. The compiler generates specific versions for each type you use.

:::info Write Once, Use for Any Type
Templates = blueprints. The compiler stamps out type-specific versions as needed.
:::

## Basic Function Template

```cpp showLineNumbers 
// Template definition
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// Usage - compiler generates versions automatically
int x = max(5, 10);           // max<int>
double y = max(3.14, 2.71);   // max<double>
std::string s = max("abc", "xyz");  // max<std::string>
```

**How it works:**
1. You write one template
2. Compiler sees `max(5, 10)` and generates `max<int>`
3. Compiler sees `max(3.14, 2.71)` and generates `max<double>`
4. Each type gets its own compiled function

## Template Parameters

```cpp showLineNumbers 
// Type parameter
template<typename T>
void print(T value) {
    std::cout << value << "\n";
}

// Multiple type parameters
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;
}

int result = add(5, 3.14);  // T=int, U=double, returns double

// Non-type parameters
template<typename T, size_t N>
size_t arraySize(T (&array)[N]) {
    return N;
}

int arr[10];
size_t size = arraySize(arr);  // N=10
```

**Note:** `typename` and `class` are interchangeable in templates. Modern style prefers `typename`.

## Template Argument Deduction

Compiler figures out template arguments from function arguments:

```cpp showLineNumbers 
template<typename T>
T square(T x) {
    return x * x;
}

auto result = square(5);      // T deduced as int
auto result2 = square(3.14);  // T deduced as double

// Explicit template arguments
auto result3 = square<long>(5);  // Force T to be long
```

**Deduction rules:**
- Exact match preferred
- Reference and const dropped during deduction
- No implicit conversions between template types

## Multiple Parameters

```cpp showLineNumbers 
template<typename T, typename U>
void process(T first, U second) {
    std::cout << first << ", " << second << "\n";
}

process(42, "hello");      // T=int, U=const char*
process(3.14, true);       // T=double, U=bool
```

Different parameters can have different types. They're independently deduced.

## Return Type Deduction

```cpp showLineNumbers 
// C++11: Trailing return type
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

// C++14: Auto deduction
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;  // Return type deduced from return statement
}

auto x = add(5, 3.14);  // Returns double
```

## Template Specialization

Provide specific implementation for certain types:

```cpp showLineNumbers 
// General template
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// Specialization for const char*
template<>
const char* max(const char* a, const char* b) {
    return (strcmp(a, b) > 0) ? a : b;
}

int x = max(5, 10);          // Uses general template
const char* s = max("abc", "xyz");  // Uses specialization
```

## Overloading Function Templates

```cpp showLineNumbers 
// Template version
template<typename T>
void print(T value) {
    std::cout << "Template: " << value << "\n";
}

// Non-template version (preferred for exact match)
void print(int value) {
    std::cout << "Non-template int: " << value << "\n";
}

print(42);      // "Non-template int: 42" (exact match)
print(3.14);    // "Template: 3.14" (template version)
```

**Overload resolution:**
1. Exact match non-template
2. Template
3. Non-template with conversions

## Constraints and Concepts (C++20)

```cpp showLineNumbers 
// Require type to support operator<
template<typename T>
requires std::totally_ordered<T>
T min(T a, T b) {
    return (a < b) ? a : b;
}

// Shorter syntax
template<std::totally_ordered T>
T min(T a, T b) {
    return (a < b) ? a : b;
}

min(5, 10);     // ✅ OK: int is totally_ordered
min("a", "b");  // ✅ OK: const char* is totally_ordered
// min(std::vector{1}, std::vector{2});  // ❌ Error: vector not comparable
```

Concepts make templates fail with clear error messages instead of cryptic template errors.

## Common Patterns

**Generic swap:**
```cpp showLineNumbers 
template<typename T>
void swap(T& a, T& b) {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}
```

**Generic comparison:**
```cpp showLineNumbers 
template<typename T>
bool equal(const T& a, const T& b) {
    return a == b;
}
```

**Generic algorithm:**
```cpp showLineNumbers 
template<typename T>
T sum(const std::vector<T>& vec) {
    T result{};
    for (const auto& val : vec) {
        result += val;
    }
    return result;
}
```

## Template Compilation

Templates are compiled when instantiated, not when defined:

```cpp showLineNumbers 
// header.h
template<typename T>
T add(T a, T b) {
    return a + b;  // Compiled when someone uses it
}

// main.cpp
#include "header.h"
auto x = add(5, 10);  // NOW template is compiled for int
```

**Important:** Template definitions must be in headers (or same translation unit where used).

:::success Function Template Essentials

**Generic code** = write once, works for many types  
**Compiler generates** = separate function for each type used  
**Type deduction** = automatic from arguments  
**Specialization** = custom behavior for specific types  
**Concepts (C++20)** = constrain what types are allowed  
**Define in headers** = must be visible where used  
**Explicit instantiation** = `template int add<int>(int, int);`
:::