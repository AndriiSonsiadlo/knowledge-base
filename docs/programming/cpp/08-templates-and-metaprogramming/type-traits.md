---
id: type-traits
title: Type Traits
sidebar_label: Type Traits
sidebar_position: 8
tags: [c++, templates, type-traits, metaprogramming]
---

# Type Traits

Type traits are compile-time tools that query and transform types. They power template metaprogramming and SFINAE, letting you write code that adapts to different types automatically.

:::info Compile-Time Type Information
Type traits answer questions about types at compile-time: Is it a pointer? Is it const? Can it be copied? No runtime cost!
:::

## Basic Type Traits

```cpp
#include <type_traits>

// Check properties
std::is_integral<int>::value;        // true
std::is_integral<double>::value;     // false
std::is_pointer<int*>::value;        // true
std::is_const<const int>::value;     // true

// C++17: Shorter with _v
std::is_integral_v<int>;             // true
std::is_pointer_v<int*>;             // true
```

## Primary Type Categories

```cpp
// Fundamental types
std::is_void_v<void>           // true
std::is_null_pointer_v<nullptr_t>  // true
std::is_integral_v<int>        // true (int, char, long, bool, etc.)
std::is_floating_point_v<double>   // true (float, double, long double)
std::is_array_v<int[10]>       // true
std::is_enum_v<Color>          // true for enum types
std::is_union_v<MyUnion>       // true
std::is_class_v<MyClass>       // true (class or struct)
std::is_function_v<void()>     // true
std::is_pointer_v<int*>        // true
std::is_reference_v<int&>      // true
std::is_member_pointer_v<int MyClass::*>  // true
```

## Composite Type Categories

```cpp
// Arithmetic = integral or floating
std::is_arithmetic_v<int>      // true
std::is_arithmetic_v<double>   // true

// Fundamental = arithmetic or void or nullptr
std::is_fundamental_v<int>     // true

// Object = not function, not reference, not void
std::is_object_v<int>          // true
std::is_object_v<int&>         // false

// Scalar = arithmetic, enum, pointer, member pointer, nullptr
std::is_scalar_v<int>          // true
std::is_scalar_v<int*>         // true

// Compound = array, function, pointer, reference, class, union, enum
std::is_compound_v<int*>       // true
```

## Type Properties

```cpp
// const/volatile
std::is_const_v<const int>     // true
std::is_volatile_v<volatile int>  // true

// Signedness
std::is_signed_v<int>          // true
std::is_unsigned_v<unsigned>   // true

// Trivial operations
std::is_trivially_copyable_v<int>      // true
std::is_trivially_constructible_v<int> // true
std::is_trivially_destructible_v<int>  // true

// Standard layout
std::is_standard_layout_v<MyStruct>    // true if C-compatible

// POD (Plain Old Data)
std::is_pod_v<MyStruct>  // true if both trivial and standard layout
```

## Type Relationships

```cpp
// Same type
std::is_same_v<int, int>           // true
std::is_same_v<int, const int>     // false
std::is_same_v<int, int&>          // false

// Base and derived
class Base {};
class Derived : public Base {};

std::is_base_of_v<Base, Derived>   // true
std::is_base_of_v<Derived, Base>   // false

// Convertible
std::is_convertible_v<int, double>     // true
std::is_convertible_v<double, int>     // true (narrowing though)
std::is_convertible_v<int*, void*>     // true
std::is_convertible_v<void*, int*>     // false
```

## Type Transformations

```cpp
// Remove modifiers
using T1 = std::remove_const_t<const int>;     // int
using T2 = std::remove_reference_t<int&>;      // int
using T3 = std::remove_pointer_t<int*>;        // int
using T4 = std::remove_cv_t<const volatile int>; // int

// Add modifiers
using T5 = std::add_const_t<int>;              // const int
using T6 = std::add_pointer_t<int>;            // int*
using T7 = std::add_lvalue_reference_t<int>;   // int&
using T8 = std::add_rvalue_reference_t<int>;   // int&&

// Decay (like pass-by-value)
using T9 = std::decay_t<int&>;                 // int
using T10 = std::decay_t<int[10]>;             // int*
using T11 = std::decay_t<int()>;               // int(*)()
```

## Conditional Type Selection

```cpp
// Choose type based on condition
template<bool B, typename T, typename F>
using conditional_t = std::conditional<B, T, F>::type;

// Example: Choose int or double based on size
using BigType = std::conditional_t<
    sizeof(int) >= 4,
    int,      // if true
    long      // if false
>;

// Return type selection
template<typename T>
auto getValue(T value) {
    using RetType = std::conditional_t<
        std::is_integral_v<T>,
        long,     // integral → long
        double    // non-integral → double
    >;
    return static_cast<RetType>(value);
}
```

## Common Type

```cpp
// Find common type between multiple types
using T1 = std::common_type_t<int, long, short>;  // long
using T2 = std::common_type_t<int, double>;       // double
using T3 = std::common_type_t<int*, void*>;       // void*

template<typename T, typename U>
auto add(T a, U b) {
    using ResultType = std::common_type_t<T, U>;
    return static_cast<ResultType>(a + b);
}
```

## Practical Examples

**Safe division:**
```cpp
template<typename T>
auto safeDivide(T a, T b) {
    static_assert(std::is_arithmetic_v<T>, "Must be arithmetic type");
    if constexpr (std::is_integral_v<T>) {
        return static_cast<double>(a) / b;  // Avoid integer division
    } else {
        return a / b;
    }
}
```

**Generic swap:**
```cpp
template<typename T>
void swap(T& a, T& b) {
    static_assert(std::is_move_constructible_v<T>, 
                  "Type must be move constructible");
    static_assert(std::is_move_assignable_v<T>,
                  "Type must be move assignable");
    
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}
```

**Type-specific optimization:**
```cpp
template<typename T>
void process(const T& value) {
    if constexpr (std::is_trivially_copyable_v<T>) {
        // Fast memcpy-based copy
        std::memcpy(&dest, &value, sizeof(T));
    } else {
        // Safe copy constructor
        dest = value;
    }
}
```

## Custom Type Traits

```cpp
// Check if type has .size() method
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

template<typename T>
constexpr bool has_size_v = has_size<T>::value;

// Usage
has_size_v<std::vector<int>>  // true
has_size_v<int>                // false
```

## Compile-Time Assertions

```cpp
template<typename T>
void processInteger(T value) {
    static_assert(std::is_integral_v<T>, 
                  "T must be an integral type");
    // ...
}

template<typename T>
class Container {
    static_assert(std::is_default_constructible_v<T>,
                  "T must be default constructible");
    static_assert(std::is_copy_constructible_v<T>,
                  "T must be copy constructible");
    // ...
};
```

## constexpr if with Type Traits (C++17)

```cpp
template<typename T>
auto getValue(T value) {
    if constexpr (std::is_pointer_v<T>) {
        return *value;  // Dereference pointer
    } else {
        return value;   // Return as-is
    }
}

int x = 42;
int* ptr = &x;

auto a = getValue(x);    // Returns 42
auto b = getValue(ptr);  // Returns 42 (dereferenced)
```

## Most Commonly Used Traits

**Type checking:**
- `is_integral`, `is_floating_point`, `is_arithmetic`
- `is_pointer`, `is_reference`, `is_array`
- `is_const`, `is_volatile`
- `is_class`, `is_enum`

**Type relationships:**
- `is_same`, `is_base_of`, `is_convertible`

**Type properties:**
- `is_trivially_copyable`, `is_standard_layout`
- `is_default_constructible`, `is_copy_constructible`
- `is_move_constructible`, `is_nothrow_move_constructible`

**Type transformations:**
- `remove_const`, `remove_reference`, `remove_pointer`
- `add_const`, `add_pointer`, `add_lvalue_reference`
- `decay`, `conditional`, `common_type`

:::success Type Traits Summary

**Query types** = is_integral, is_pointer, is_const, etc.  
**Transform types** = remove_const, add_pointer, decay, etc.  
**Relationships** = is_same, is_base_of, is_convertible  
**Compile-time** = all evaluated during compilation  
**_v suffix** = C++17 shortcut for ::value  
**_t suffix** = C++14 shortcut for ::type  
**static_assert** = enforce type requirements  
**if constexpr** = branch based on type properties
:::