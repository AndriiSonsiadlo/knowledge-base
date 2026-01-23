---
id: concepts-and-requires
title: Concepts and Requires Expressions (C++20)
sidebar_label: Concepts & Requires
sidebar_position: 11
tags: [c++, cpp20, concepts, requires, constraints]
---

# Concepts and Requires Expressions (C++20)

Concepts are named requirements for template arguments that replace SFINAE with readable constraints. Requires expressions are the building blocks that check if code compiles at compile-time.

:::info Named Constraints with Readable Checks
**Concepts** = Named sets of requirements (e.g., `std::integral<T>`)  
**Requires expressions** = Check if operations are valid at compile-time  
Together they provide clear, readable template constraints with great error messages
:::

## Concepts Basics

Concepts are named predicates that constrain template parameters.
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

All equivalent - choose based on readability:
```cpp showLineNumbers
// 1. Template constraint
template<std::integral T>
T add(T a, T b) { return a + b; }

// 2. Trailing requires clause
template<typename T>
requires std::integral<T>
T add(T a, T b) { return a + b; }

// 3. Abbreviated function template (auto)
auto add(std::integral auto a, std::integral auto b) {
    return a + b;
}

// 4. Inline concept check
template<typename T>
T add(T a, T b) requires std::integral<T> {
    return a + b;
}
```

## Requires Expressions

Requires expressions check if code compiles without actually compiling it.
```cpp showLineNumbers
template<typename T>
void process(T value) {
    // Check if T supports these operations
    requires {
        value + value;      // Addition
        value * 2;          // Multiplication with int
        value < value;      // Comparison
    };
    
    // If requires succeeds, this code runs
    auto result = value + value;
}
```

**Not used directly like this!** Typically used in concepts or requires clauses.

## Requires Clause

Check constraints before function execution:
```cpp showLineNumbers
template<typename T>
requires requires(T x) {  // First = clause, second = expression
    x + x;
    x * 2;
}
T twice(T value) {
    return value * 2;
}

twice(5);      // ✅ OK: int supports these ops
twice(3.14);   // ✅ OK: double supports these ops
// twice("hi");   // ❌ Error: const char* doesn't support * 2
```

## Simple Requirements

Check if expressions are valid (compile):
```cpp showLineNumbers
template<typename T>
requires requires(T x) {
    x.size();       // Must have .size() method
    x.begin();      // Must have .begin() method
    x.end();        // Must have .end() method
}
void process(const T& container) {
    for (const auto& item : container) {
        std::cout << item;
    }
}

process(std::vector<int>{1,2,3});  // ✅ Has size, begin, end
// process(42);  // ❌ int doesn't have these methods
```

## Type Requirements

Check if types exist:
```cpp showLineNumbers
template<typename T>
requires requires {
    typename T::value_type;     // Must have value_type
    typename T::iterator;       // Must have iterator
    typename T::size_type;      // Must have size_type
}
void info(const T&) {
    std::cout << "Container type\n";
}

info(std::vector<int>{});  // ✅ Has all these types
// info(42);  // ❌ int doesn't have these types
```

## Compound Requirements

Check expressions AND their return types:
```cpp showLineNumbers
template<typename T>
requires requires(T x) {
    { x.size() } -> std::convertible_to<size_t>;  // size() returns size_t-like
    { x[0] } -> std::same_as<typename T::value_type&>;  // operator[] returns reference
}
void process(T& container) {
    size_t n = container.size();
    auto& first = container[0];
}
```

**Syntax:** `{ expression } -> concept<type>;`

## Nested Requirements

Check for nested properties:
```cpp showLineNumbers
template<typename T>
requires requires(T x) {
    requires sizeof(T) <= 8;  // Size constraint
    requires std::is_trivially_copyable_v<T>;  // Type trait
    x + x;  // Operation
}
void fastProcess(T value) {
    // Optimized for small, trivially copyable types
}
```

## Custom Concepts

Define your own requirements:
```cpp showLineNumbers
// Simple concept
template<typename T>
concept Incrementable = requires(T x) {
    { ++x } -> std::same_as<T&>;  // Pre-increment returns reference
    { x++ } -> std::same_as<T>;   // Post-increment returns value
};

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
```cpp showLineNumbers
// AND (conjunction)
template<typename T>
concept SignedIntegral = std::integral<T> && std::signed_integral<T>;

// OR (disjunction)
template<typename T>
concept Number = std::integral<T> || std::floating_point<T>;

// NOT (negation)
template<typename T>
concept NotPointer = !std::is_pointer_v<T>;
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
// add("hello", 5); // ❌ const char* + int not addable
```

## Standard Concepts Overview

**Core language concepts:**
```cpp showLineNumbers
std::same_as<T, U>          // T and U are same type
std::derived_from<T, Base>  // T derives from Base
std::convertible_to<From, To>  // From converts to To
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

## Summary

**Concepts:**
- Named requirements for template arguments
- Replace SFINAE with readable constraints
- Provide clear error messages
- Enable overload resolution via subsumption
- Four equivalent syntaxes

**Requires expressions:**
- Check if code compiles at compile-time
- Simple requirements: check operations
- Type requirements: check types exist
- Compound requirements: check operation + return type
- Nested requirements: check compile-time conditions

**Benefits:**
- **Readable:** `std::integral<T>` vs complex SFINAE
- **Self-documenting:** Requirements are explicit
- **Clear errors:** Shows exactly what failed
- **Overload resolution:** Subsumption picks best match
- **Standard library:** Many concepts provided

**Common patterns:**
- Combining with `&&`, `||`, `!`
- Building complex concepts from simpler ones
- Using standard concepts from `<concepts>`
- Custom concepts for domain-specific requirements
