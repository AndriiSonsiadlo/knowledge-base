---
id: concepts
title: Concepts (C++20)
sidebar_label: Concepts
sidebar_position: 11
tags: [c++, cpp20, concepts, constraints, templates]
---

# Concepts (C++20)

Concepts are named requirements for template arguments. They replace SFINAE with readable constraints, provide clear error messages, and make template interfaces self-documenting.

:::info Named Constraints
Concept = named set of requirements. Instead of cryptic SFINAE, you get clear, readable constraints like `std::integral<T>` or `Sortable<T>`.
:::

## Basic Concept Definition

```cpp showLineNumbers 
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

// Use in templates
template<Numeric T>
T add(T a, T b) {
    return a + b;
}

add(5, 10);      // ✅ int is Numeric
add(3.14, 2.71); // ✅ double is Numeric
// add("a", "b");   // ❌ Error: const char* doesn't satisfy Numeric
```

Much clearer than SFINAE!

## Standard Library Concepts

C++20 provides many concepts in `<concepts>`:

```cpp showLineNumbers 
#include <concepts>

// Integral types
template<std::integral T>
T twice(T value) {
    return value * 2;
}

// Floating point types
template<std::floating_point T>
T half(T value) {
    return value / 2.0;
}

// Same as another type
template<typename T>
requires std::same_as<T, int>
void process(T value) {
    // Only accepts int
}

// Convertible
template<typename From, typename To>
requires std::convertible_to<From, To>
To convert(From value) {
    return static_cast<To>(value);
}
```

## Four Ways to Use Concepts

**1. Template constraint:**
```cpp showLineNumbers 
template<std::integral T>
T add(T a, T b) { return a + b; }
```

**2. Trailing requires clause:**
```cpp showLineNumbers 
template<typename T>
requires std::integral<T>
T add(T a, T b) { return a + b; }
```

**3. Abbreviated function template (auto):**
```cpp showLineNumbers 
auto add(std::integral auto a, std::integral auto b) {
    return a + b;
}
```

**4. Inline concept check:**
```cpp showLineNumbers 
template<typename T>
T add(T a, T b) requires std::integral<T> {
    return a + b;
}
```

All four are equivalent! Choose based on readability.

## Custom Concepts

Define your own requirements:

```cpp showLineNumbers 
// Simple concept
template<typename T>
concept Incrementable = requires(T x) {
    ++x;  // Must support pre-increment
    x++;  // Must support post-increment
};

// Use it
template<Incrementable T>
void advance(T& value, int steps) {
    for (int i = 0; i < steps; ++i) {
        ++value;
    }
}

// Concept with type checks
template<typename T>
concept Container = requires(T c) {
    typename T::value_type;
    typename T::iterator;
    c.begin();
    c.end();
    c.size();
};
```

## Combining Concepts

**AND (conjunction):**
```cpp showLineNumbers 
template<typename T>
concept SignedIntegral = std::integral<T> && std::signed_integral<T>;

template<SignedIntegral T>
T negate(T value) {
    return -value;
}
```

**OR (disjunction):**
```cpp showLineNumbers 
template<typename T>
concept Number = std::integral<T> || std::floating_point<T>;

template<Number T>
T square(T value) {
    return value * value;
}
```

**NOT (negation):**
```cpp showLineNumbers 
template<typename T>
concept NotPointer = !std::is_pointer_v<T>;

template<NotPointer T>
void process(T value) {
    // Works with non-pointers only
}
```

## Subsumption

More specific concepts are preferred:

```cpp showLineNumbers 
template<typename T>
concept Integral = std::is_integral_v<T>;

template<typename T>
concept SignedIntegral = Integral<T> && std::is_signed_v<T>;

// General version
template<Integral T>
void process(T value) {
    std::cout << "Integral\n";
}

// Specific version (preferred when both match)
template<SignedIntegral T>
void process(T value) {
    std::cout << "Signed Integral\n";
}

process(5u);   // "Integral" (unsigned)
process(5);    // "Signed Integral" (signed - more specific!)
```

Compiler picks the most constrained overload.

## Concepts with Multiple Parameters

```cpp showLineNumbers 
template<typename T, typename U>
concept Addable = requires(T a, U b) {
    { a + b } -> std::convertible_to<T>;
};

template<typename T, typename U>
requires Addable<T, U>
T add(T a, U b) {
    return a + b;
}

add(5, 10);      // ✅ int + int
add(3.14, 2);    // ✅ double + int
add("hello", 5); // ❌ const char* + int not addable
```

## Concept Refinement

Build concepts on top of others:

```cpp showLineNumbers 
template<typename T>
concept Readable = requires(T x) {
    { x.read() } -> std::same_as<std::string>;
};

template<typename T>
concept Writable = requires(T x, std::string s) {
    { x.write(s) } -> std::same_as<void>;
};

// Combine both
template<typename T>
concept ReadWritable = Readable<T> && Writable<T>;

template<ReadWritable T>
void processFile(T& file) {
    auto data = file.read();
    file.write(data);
}
```

## Standard Concepts Overview

**Core language concepts:**
```cpp showLineNumbers 
std::same_as<T, U>          // T and U are same type
std::derived_from<T, Base>  // T derives from Base
std::convertible_to<From, To>  // From converts to To
std::common_reference_with<T, U>  // Common reference type exists
std::common_with<T, U>      // Common type exists
std::integral<T>            // int, long, char, etc.
std::signed_integral<T>     // Signed integral
std::unsigned_integral<T>   // Unsigned integral
std::floating_point<T>      // float, double, long double
```

**Comparison concepts:**
```cpp showLineNumbers 
std::equality_comparable<T>     // Supports ==
std::totally_ordered<T>         // Supports <, >, <=, >=
std::three_way_comparable<T>    // Supports <=>
```

**Object concepts:**
```cpp showLineNumbers 
std::movable<T>              // Move constructible/assignable
std::copyable<T>             // Copy constructible/assignable
std::semiregular<T>          // Default + move/copy
std::regular<T>              // Semiregular + equality comparable
```

**Callable concepts:**
```cpp showLineNumbers 
std::invocable<F, Args...>   // Can call F with Args
std::predicate<F, Args...>   // Returns bool
```

## Concepts with Ranges

```cpp showLineNumbers 
#include <ranges>

// Only accept ranges
template<std::ranges::range R>
void process(R&& range) {
    for (auto&& elem : range) {
        std::cout << elem << " ";
    }
}

// Only accept sorted ranges
template<std::ranges::random_access_range R>
requires std::sortable<std::ranges::iterator_t<R>>
void binarySearch(R&& range, const auto& value) {
    // Can use binary search
}
```

## Concept Specialization

Different implementations for different concepts:

```cpp showLineNumbers 
// Generic version
template<typename T>
void serialize(const T& value) {
    // Generic serialization
}

// Specialized for integrals
template<std::integral T>
void serialize(const T& value) {
    std::cout << "Int: " << value << "\n";
}

// Specialized for strings
template<typename T>
requires std::same_as<T, std::string>
void serialize(const T& value) {
    std::cout << "String: " << value << "\n";
}

serialize(42);         // "Int: 42"
serialize(3.14);       // Generic version
serialize(std::string("hi"));  // "String: hi"
```

## Class Template Concepts

```cpp showLineNumbers 
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

// Constrain class template
template<Numeric T>
class Calculator {
    T value;
public:
    Calculator(T v) : value(v) {}
    T square() { return value * value; }
};

Calculator<int> c1(5);      // ✅ OK
Calculator<double> c2(3.14); // ✅ OK
// Calculator<std::string> c3("hi");  // ❌ Error
```

## Better Error Messages

**Without concepts (SFINAE):**
```
error: no matching function for call to 'add(const char*)'
note: candidate template ignored: substitution failure [with T = const char*]:
no type named 'value' in 'std::is_arithmetic<const char*>'
[200 lines of template instantiation stack...]
```

**With concepts:**
```
error: no matching function for call to 'add(const char*)'
note: constraints not satisfied
note: concept 'Numeric<const char*>' was not satisfied
```

Clear and concise!

## Real-World Example

```cpp showLineNumbers 
// Generic container algorithm
template<typename C>
concept Container = requires(C c) {
    typename C::value_type;
    typename C::iterator;
    { c.begin() } -> std::same_as<typename C::iterator>;
    { c.end() } -> std::same_as<typename C::iterator>;
    { c.size() } -> std::convertible_to<size_t>;
};

template<Container C>
auto sum(const C& container) {
    typename C::value_type result{};
    for (const auto& item : container) {
        result += item;
    }
    return result;
}

// Works with any container
std::vector<int> vec{1, 2, 3};
std::list<double> lst{1.1, 2.2, 3.3};
sum(vec);  // 6
sum(lst);  // 6.6
```

:::success Concepts Key Benefits

**Readable** = `std::integral<T>` vs complex SFINAE  
**Self-documenting** = requirements are explicit  
**Clear errors** = shows exactly what failed  
**Overload resolution** = subsumption picks best match  
**Standard library** = many concepts provided  
**Four syntaxes** = choose most readable  
**Composition** = combine with &&, ||, !  
**Modern C++** = replaces enable_if patterns
:::