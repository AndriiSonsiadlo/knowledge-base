---
id: sfinae-and-enable-if
title: SFINAE and enable_if
sidebar_label: SFINAE & enable_if
sidebar_position: 9
tags: [c++, templates, sfinae, enable-if, metaprogramming]
---

# SFINAE and enable_if

SFINAE (Substitution Failure Is Not An Error) is a fundamental C++ template mechanism that enables conditional template compilation. `std::enable_if` is the primary tool for applying SFINAE in practice.

:::info Conditional Template Compilation
**SFINAE:** When template substitution fails, remove template from consideration instead of erroring  
**enable_if:** Enable/disable templates based on compile-time conditions
:::

## SFINAE Core Concept

When the compiler tries to substitute template arguments and fails, that's not an error - the template is simply removed from the overload set.
```cpp showLineNumbers
// Works for types with .size() method
template<typename T>
auto getSize(const T& container) 
    -> decltype(container.size()) 
{
    return container.size();
}

// Works for array types
template<typename T, size_t N>
size_t getSize(const T (&array)[N]) {
    return N;
}

std::vector<int> vec{1, 2, 3};
int arr[5];

auto s1 = getSize(vec);  // Calls first (vector has .size())
auto s2 = getSize(arr);  // Calls second (array version)
```

If `vec.size()` didn't exist, the first template would SFINAE away, not cause an error.

## How SFINAE Works
```cpp showLineNumbers
// This will SFINAE away for types without ::value_type
template<typename T>
typename T::value_type get(const T& container) {
    return container[0];
}

// Fallback for types without ::value_type
template<typename T>
T get(const T& value) {
    return value;
}

std::vector<int> vec{42};
int x = 42;

auto a = get(vec);  // Uses first (vector has value_type)
auto b = get(x);    // Uses second (int doesn't, SFINAE)
```

**Process:**
1. Compiler tries first template with `int`
2. Substitution fails: `int::value_type` doesn't exist
3. SFINAE: Remove first template, **no error**
4. Try second template: Success!

## Expression SFINAE

Check if expressions compile without actually compiling them.
```cpp showLineNumbers
// Check if T supports operator[]
template<typename T>
auto access(T& container, size_t index)
    -> decltype(container[index])  // SFINAE on this
{
    return container[index];
}

// Fallback
template<typename T>
auto access(T& value, size_t)
    -> decltype(value)
{
    return value;
}

std::vector<int> vec{1, 2, 3};
int x = 42;

access(vec, 1);  // Returns vec[1]
access(x, 0);    // Returns x (no operator[])
```

## Trailing Return Type SFINAE

Perfect for SFINAE - checked during substitution.
```cpp showLineNumbers
// Only enabled if T has .begin() and .end()
template<typename T>
auto print(const T& container)
    -> decltype(container.begin(), container.end(), void())
{
    for (const auto& item : container) {
        std::cout << item << " ";
    }
}

// Fallback
void print(...) {  // Variadic catch-all
    std::cout << "Not a container";
}

std::vector<int> vec{1, 2, 3};
int x = 42;

print(vec);  // "1 2 3"
print(x);    // "Not a container"
```

**Trick:** `(expr1, expr2, void())` checks multiple expressions and returns `void`.

## Basic enable_if

`std::enable_if` is the standard tool for SFINAE-based template control.
```cpp showLineNumbers
#include <type_traits>

// Only enable for integral types
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
increment(T value) {
    return value + 1;
}

int x = increment(5);       // ✅ int is integral
// double y = increment(3.14);  // ❌ Removed from overload set
```

**How it works:**
- `std::enable_if<condition, T>::type` exists only if condition is true
- If false, substitution fails → SFINAE
- Template removed, not an error

## Modern enable_if (C++14)
```cpp showLineNumbers
// C++14: Shorter with _t alias
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
increment(T value) {
    return value + 1;
}

// Even shorter with trailing return
template<typename T>
auto increment(T value) 
    -> std::enable_if_t<std::is_integral_v<T>, T>
{
    return value + 1;
}
```

**C++14 helpers:**
- `enable_if_t<...>` = shortcut for `::type`
- `is_integral_v<T>` = shortcut for `::value`

## Return Type enable_if
```cpp showLineNumbers
template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
sqrt(T value) {
    return std::sqrt(value);
}

auto x = sqrt(3.14);  // ✅ double
// auto y = sqrt(5);     // ❌ int not floating point
```

## Template Parameter enable_if

Cleaner - keeps function signature readable.
```cpp showLineNumbers
// Default template parameter approach
template<typename T, 
         std::enable_if_t<std::is_integral_v<T>, int> = 0>
T twice(T value) {
    return value * 2;
}

// Or as extra parameter
template<typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
T triple(T value) {
    return value * 3;
}
```

## Multiple Overloads

Different implementations for different type categories.
```cpp showLineNumbers
// For integral types
template<typename T>
std::enable_if_t<std::is_integral_v<T>, void>
process(T value) {
    std::cout << "Processing integer: " << value << "\n";
}

// For floating point types
template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, void>
process(T value) {
    std::cout << "Processing float: " << value << "\n";
}

process(42);     // "Processing integer: 42"
process(3.14);   // "Processing float: 3.14"
```

## Class Templates
```cpp showLineNumbers
template<typename T, typename Enable = void>
class Container;

// Specialization for integral types
template<typename T>
class Container<T, std::enable_if_t<std::is_integral_v<T>>> {
public:
    void info() { std::cout << "Integer container\n"; }
};

// Specialization for floating point
template<typename T>
class Container<T, std::enable_if_t<std::is_floating_point_v<T>>> {
public:
    void info() { std::cout << "Float container\n"; }
};

Container<int> c1;
c1.info();  // "Integer container"

Container<double> c2;
c2.info();  // "Float container"
```

## Combining Conditions
```cpp showLineNumbers
// Multiple requirements
template<typename T>
std::enable_if_t<std::is_arithmetic_v<T> && !std::is_same_v<T, bool>, T>
process(T value) {
    return value * 2;
}

// std::conjunction (C++17)
template<typename T>
std::enable_if_t<std::conjunction_v
    std::is_arithmetic<T>,
    std::negation<std::is_same<T, bool>>
>, T>
process2(T value) {
    return value * 2;
}
```

## Detection Idiom

Check if types have specific members.
```cpp showLineNumbers
// Primary template: assume false
template<typename, typename = void>
struct has_size : std::false_type {};

// Specialization: true if T::size() exists
template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

// Helper variable template
template<typename T>
constexpr bool has_size_v = has_size<T>::value;

// Usage
has_size_v<std::vector<int>>  // true
has_size_v<int>                // false
```

**How it works:**
- `std::void_t` turns any type into `void`
- If `T::size()` doesn't exist, substitution fails → SFINAE
- Falls back to primary template (false_type)

## std::void_t Explained
```cpp showLineNumbers
// std::void_t always produces void
template<typename...>
using void_t = void;

// Useful for SFINAE
template<typename T, typename = void>
struct has_foo : std::false_type {};

template<typename T>
struct has_foo<T, std::void_t<decltype(&T::foo)>>
    : std::true_type {};

// If T::foo exists, void_t<...> produces void → matches specialization
// Otherwise, SFINAE removes specialization, uses primary
```

## Common Type Traits
```cpp showLineNumbers
std::is_integral<T>         // int, long, char, bool
std::is_floating_point<T>   // float, double
std::is_arithmetic<T>       // integral or floating
std::is_pointer<T>          // pointer types
std::is_reference<T>        // reference types
std::is_const<T>            // const qualified
std::is_class<T>            // class or struct
std::is_enum<T>             // enum types

std::is_same<T, U>          // T and U are same type
std::is_base_of<Base, Derived>  // Inheritance check
std::is_convertible<From, To>   // Can convert?
```

## Concepts (C++20) - Modern Alternative

Concepts are cleaner and more readable than SFINAE/enable_if.
```cpp showLineNumbers
// Old way with enable_if
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
twice(T value) {
    return value * 2;
}

// New way with concepts
template<std::integral T>
T twice(T value) {
    return value * 2;
}

// Or with requires clause
template<typename T>
requires std::integral<T>
T twice(T value) {
    return value * 2;
}
```

Much more readable! See the Concepts section for details.

## Summary

**SFINAE fundamentals:**
- Substitution Failure Is Not An Error
- Failed substitution removes template, doesn't error
- Enables conditional template compilation
- Foundation for template metaprogramming

**enable_if usage:**
- `enable_if<condition, T>::type` exists only if condition true
- Use `enable_if_t` (C++14) for brevity
- Common positions: return type, template parameter, function parameter
- Combine with type traits for powerful conditions

**Common patterns:**
- Multiple overloads for different type categories
- Detection idiom with `void_t` for member checking
- Expression SFINAE with `decltype`
- Trailing return types for SFINAE

**Modern alternatives:**
- Concepts (C++20) - cleaner, better errors
- `if constexpr` (C++17) - simpler branching
- Prefer these over SFINAE when available
