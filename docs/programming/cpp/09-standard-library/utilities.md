---
id: utilities
title: Utility Library (pair, tuple, optional, variant, any)
sidebar_label: Utilities
sidebar_position: 10
tags: [c++, utilities, pair, optional, variant, any, tuple]
---

# Utilities

The **utilities** library provides general-purpose components that don't fit into other categories but are essential for modern C++ development.

## std::pair

A simple container holding two heterogeneous values.
```cpp
#include <utility>
#include <string>

void pairExample() {
    // Construction
    std::pair<int, std::string> p1{42, "hello"};
    auto p2 = std::make_pair(3.14, 'x');
    
    // Access
    int first = p1.first;
    std::string second = p1.second;
    
    // Structured bindings (C++17)
    auto [num, text] = p1;
    
    // Comparison
    std::pair<int, int> a{1, 2};
    std::pair<int, int> b{1, 3};
    bool less = a < b;  // Lexicographic comparison
}
```

## std::tuple

A fixed-size collection of heterogeneous values.
```cpp
#include <tuple>
#include <string>

void tupleExample() {
    // Construction
    std::tuple<int, double, std::string> t1{42, 3.14, "text"};
    auto t2 = std::make_tuple(1, 2.0, 'c');
    
    // Access by index
    int x = std::get<0>(t1);
    double y = std::get<1>(t1);
    
    // Access by type (if unique)
    std::string s = std::get<std::string>(t1);
    
    // Structured bindings
    auto [i, d, str] = t1;
    
    // Tuple size
    constexpr size_t size = std::tuple_size_v<decltype(t1)>;
}
```

:::info
Use `std::tie` to unpack tuples into existing variables:
```cpp
int a; double b; std::string c;
std::tie(a, b, c) = t1;
```
:::

## std::optional (C++17)

Represents a value that may or may not be present.
```cpp
#include <optional>
#include <string>

std::optional<std::string> findUser(int id) {
    if (id == 42) {
        return "Alice";
    }
    return std::nullopt;  // No value
}

void optionalExample() {
    auto result = findUser(42);
    
    // Check if value exists
    if (result.has_value()) {
        std::cout << *result << '\n';
    }
    
    // Alternative: boolean conversion
    if (result) {
        std::cout << result.value() << '\n';
    }
    
    // Provide default value
    std::string name = result.value_or("Unknown");
}
```

:::warning
Accessing an empty `optional` with `value()` throws `std::bad_optional_access`.
Use `value_or()` or check `has_value()` first.
:::

## std::variant (C++17)

A type-safe union that can hold one of several types.
```cpp
#include <variant>
#include <string>

using Variant = std::variant<int, double, std::string>;

void variantExample() {
    Variant v = 42;                    // Holds int
    v = 3.14;                          // Now holds double
    v = std::string("text");           // Now holds string
    
    // Check current type
    if (std::holds_alternative<std::string>(v)) {
        std::string s = std::get<std::string>(v);
    }
    
    // Get by index
    try {
        int x = std::get<int>(v);  // Throws if wrong type
    } catch (const std::bad_variant_access&) {
        // Handle error
    }
    
    // Visit pattern
    std::visit([](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "int: " << arg << '\n';
        } else if constexpr (std::is_same_v<T, double>) {
            std::cout << "double: " << arg << '\n';
        } else {
            std::cout << "string: " << arg << '\n';
        }
    }, v);
}
```

## std::any (C++17)

A type-safe container for single values of any type.
```cpp
#include <any>
#include <string>

void anyExample() {
    std::any a = 42;
    a = 3.14;
    a = std::string("text");
    
    // Check type
    if (a.type() == typeid(std::string)) {
        std::string s = std::any_cast<std::string>(a);
    }
    
    // Safe cast with pointer
    if (auto* ptr = std::any_cast<std::string>(&a)) {
        std::cout << *ptr << '\n';
    }
    
    // Reset
    a.reset();
    bool empty = !a.has_value();
}
```

:::danger
`std::any_cast` throws `std::bad_any_cast` if types don't match. Use pointer version for non-throwing cast.
:::

## std::function

Type-erased wrapper for callable objects.
```cpp
#include <functional>

void functionExample() {
    // Wrap function pointer
    std::function<int(int, int)> f1 = [](int a, int b) { return a + b; };
    
    // Wrap lambda
    int multiplier = 10;
    std::function<int(int)> f2 = [multiplier](int x) { return x * multiplier; };
    
    // Call
    int result = f1(5, 3);      // 8
    int scaled = f2(5);          // 50
    
    // Check if empty
    if (f1) {
        f1(1, 2);
    }
}
```

## std::reference_wrapper

A wrapper for storing references in containers.
```cpp
#include <functional>
#include <vector>

void referenceWrapperExample() {
    int a = 10, b = 20, c = 30;
    
    // Vector of references
    std::vector<std::reference_wrapper<int>> refs{a, b, c};
    
    // Modify through references
    for (auto& ref : refs) {
        ref.get() += 1;
    }
    
    // a=11, b=21, c=31
    
    // Helper function
    auto ref_a = std::ref(a);
    auto cref_b = std::cref(b);  // const reference
}
```

## std::move and std::forward
```cpp
#include <utility>
#include <string>

void moveForwardExample() {
    std::string s1 = "hello";
    
    // Move semantics
    std::string s2 = std::move(s1);  // s1 is now empty
    
    // Perfect forwarding
    auto forwarder = [](auto&& arg) {
        return std::forward<decltype(arg)>(arg);
    };
}
```

## std::exchange (C++14)

Replaces a value and returns the old value.
```cpp
#include <utility>

void exchangeExample() {
    int x = 42;
    int old = std::exchange(x, 100);  // x=100, old=42
    
    // Useful in move constructors
    struct Widget {
        int* data;
        
        Widget(Widget&& other) noexcept
            : data(std::exchange(other.data, nullptr)) {}
    };
}
```

## Comparison Utilities
```cpp
#include <compare>

struct Point {
    int x, y;
    
    // C++20 three-way comparison
    auto operator<=>(const Point&) const = default;
};

void comparisonExample() {
    Point p1{1, 2};
    Point p2{1, 3};
    
    bool less = p1 < p2;
    bool equal = p1 == p2;
    auto result = p1 <=> p2;  // std::strong_ordering
}
```

## Type Traits Helpers
```cpp
#include <type_traits>

template<typename T>
void typeTraitsExample() {
    if constexpr (std::is_integral_v<T>) {
        // Handle integral types
    }
    
    if constexpr (std::is_pointer_v<T>) {
        // Handle pointers
    }
    
    using NoRef = std::remove_reference_t<T>;
    using NoCV = std::remove_cv_t<T>;
}
```

## Utility Functions Comparison

| Utility                      | Purpose                                         | Use Case                                                          |
|------------------------------|-------------------------------------------------|-------------------------------------------------------------------|
| `std::pair`                  | Two heterogeneous values                        | Return two related values from a function                         |
| `std::tuple`                 | Fixed-size heterogeneous collection             | Return or group more than two values                              |
| `std::optional`              | Optional (nullable) value                       | Represent a result that may fail or be absent                     |
| `std::variant`               | Type-safe union                                 | Store one of several alternative types                            |
| `std::any`                   | Type-erased single value                        | Store arbitrary values when the type is not known at compile time |
| `std::function`              | Type-erased callable wrapper                    | Store callbacks, lambdas, or function objects                     |
| `std::reference_wrapper`     | Copyable wrapper around references              | Store references inside containers                                |
| `std::move` / `std::forward` | Cast to rvalue / preserve value category        | Enable move semantics and perfect forwarding                      |
| `std::exchange`              | Replace value and return old one                | Implement move constructors or state-reset patterns               |
| Three-way comparison (`<=>`) | Unified comparison operator                     | Simplify and auto-generate relational operators                   |
| Type traits utilities        | Compile-time type inspection and transformation | Write generic, type-aware code                                    |


## Summary

The utilities library brings together many small but powerful building blocks that enable:

* safer APIs (`std::optional`, `std::variant`)
* flexible abstractions (`std::function`, `std::any`)
* efficient value handling (`std::move`, `std::forward`, `std::exchange`)
* expressive generic programming (type traits and comparison utilities)

:::success In practice:
* Prefer **`std::optional`** over sentinel values.
* Prefer **`std::variant`** over unions or manual type tagging.
* Use **`std::any`** only when true type erasure is required.
* Use **`std::reference_wrapper`** when a container must refer to existing objects.
* Rely on **`<=>`** and defaulted comparisons to reduce boilerplate.
* Use **type traits** to write constraints and compile-time logic for templates.
:::