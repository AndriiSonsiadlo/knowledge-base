---
id: enable-if
title: std::enable_if and SFINAE
sidebar_label: enable_if
sidebar_position: 9
tags: [c++, templates, sfinae, enable-if, metaprogramming]
---

# std::enable_if and SFINAE

SFINAE (Substitution Failure Is Not An Error) lets you enable/disable templates based on type properties. `std::enable_if` is the main tool for this.

:::info Conditional Template Compilation
Enable templates only for certain types. If substitution fails, the compiler tries other overloads instead of erroring.
:::

## Basic enable_if

```cpp showLineNumbers 
#include <type_traits>

// Only enable for integral types
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
increment(T value) {
    return value + 1;
}

int x = increment(5);      // ✅ int is integral
// double y = increment(3.14);  // ❌ Removed from overload set
```

**How it works:**
- `std::enable_if<condition, T>::type` exists only if condition is true
- If false, substitution fails (SFINAE)
- Template removed from consideration, not an error

## Modern enable_if (C++14)

```cpp showLineNumbers 
// Shorter with _t alias
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
- `enable_if_t` = shortcut for `::type`
- `is_integral_v` = shortcut for `::value`

## Return Type enable_if

```cpp showLineNumbers 
// Enable based on return type
template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
sqrt(T value) {
    return std::sqrt(value);
}

auto x = sqrt(3.14);   // ✅ double
// auto y = sqrt(5);      // ❌ int not floating point
```

## Template Parameter enable_if

```cpp showLineNumbers 
// Default template parameter approach (cleaner)
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

This approach keeps the function signature clean.

## Multiple Overloads

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

Different implementations for different type categories!

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
// Multiple requirements with conjunction
template<typename T>
std::enable_if_t<std::is_arithmetic_v<T> && !std::is_same_v<T, bool>, T>
process(T value) {
    return value * 2;
}

// std::conjunction (C++17)
template<typename T>
std::enable_if_t<std::conjunction_v<
    std::is_arithmetic<T>,
    std::negation<std::is_same<T, bool>>
>, T>
process2(T value) {
    return value * 2;
}
```

## Member Function enable_if

```cpp showLineNumbers 
class Widget {
public:
    // Only enabled for integral types
    template<typename T>
    std::enable_if_t<std::is_integral_v<T>, void>
    set(T value) {
        std::cout << "Setting integer: " << value << "\n";
    }
    
    // Only enabled for strings
    template<typename T>
    std::enable_if_t<std::is_same_v<T, std::string>, void>
    set(T value) {
        std::cout << "Setting string: " << value << "\n";
    }
};

Widget w;
w.set(42);        // "Setting integer: 42"
w.set(std::string("hello"));  // "Setting string: hello"
```

## Concepts (C++20) - Modern Alternative

Concepts are cleaner than enable_if:

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

Much more readable!

## Common Type Traits

```cpp showLineNumbers 
std::is_integral<T>         // int, long, char, bool, etc.
std::is_floating_point<T>   // float, double
std::is_arithmetic<T>       // integral or floating
std::is_pointer<T>          // pointer types
std::is_reference<T>        // reference types
std::is_const<T>            // const qualified
std::is_class<T>            // class or struct
std::is_enum<T>             // enum types
std::is_array<T>            // array types
std::is_function<T>         // function types

std::is_same<T, U>          // T and U are same type
std::is_base_of<Base, Derived>  // Inheritance check
std::is_convertible<From, To>   // Can convert?
```

## Real-World Example

```cpp showLineNumbers 
// Serialize only types with .serialize() method
template<typename T>
auto serialize(const T& obj)
    -> decltype(obj.serialize(), std::string())  // SFINAE
{
    return obj.serialize();
}

// Fallback for types without .serialize()
template<typename T>
auto serialize(const T& obj)
    -> std::enable_if_t<!std::is_member_function_pointer_v<
        decltype(&T::serialize)
    >, std::string>
{
    return "No serialization available";
}
```

## Expression SFINAE

```cpp showLineNumbers 
// Check if type has .size() method
template<typename T>
auto getSize(const T& container)
    -> decltype(container.size(), size_t())  // SFINAE on expression
{
    return container.size();
}

// Fallback for types without .size()
template<typename T>
size_t getSize(const T&, ...) {  // Variadic fallback
    return 0;
}
```

:::success enable_if Key Points

**SFINAE** = Substitution Failure Is Not An Error  
**enable_if** = conditionally enable templates  
**Type traits** = check type properties at compile-time  
**Multiple overloads** = different impl for different types  
**Concepts (C++20)** = cleaner alternative to enable_if  
**Common pattern** = template parameter with default  
**Expression SFINAE** = check for member functions/types
:::