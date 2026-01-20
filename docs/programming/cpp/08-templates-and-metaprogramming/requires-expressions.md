---
id: requires-expressions
title: Requires Expressions (C++20)
sidebar_label: Requires Expressions
sidebar_position: 12
tags: [c++, cpp20, concepts, requires, constraints]
---

# Requires Expressions

Requires expressions (C++20) check if code compiles without actually compiling it. They're the building blocks of concepts, providing fine-grained compile-time checks.

:::info Compile-Time Validation
`requires` checks if operations are valid at compile-time. Unlike SFINAE, it's readable and gives clear error messages!
:::

## Basic Requires Expression

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

Check constraints before function body:

```cpp showLineNumbers 
template<typename T>
requires requires(T x) {  // First 'requires' = clause, second = expression
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
void fast_process(T value) {
    // Optimized for small, trivially copyable types
}
```

## Multiple Parameter Requirements

```cpp showLineNumbers 
template<typename T, typename U>
requires requires(T a, U b) {
    { a + b } -> std::same_as<T>;  // Addition returns T
    { a - b } -> std::same_as<T>;  // Subtraction returns T
    { a * b } -> std::same_as<T>;  // Multiplication returns T
}
T compute(T a, U b) {
    return a + b * a - b;
}
```

## Checking for Specific Operations

```cpp showLineNumbers 
// Check if type is incrementable
template<typename T>
concept Incrementable = requires(T x) {
    { ++x } -> std::same_as<T&>;  // Pre-increment returns reference
    { x++ } -> std::same_as<T>;   // Post-increment returns value
};

template<Incrementable T>
void advance(T& value, int n) {
    for (int i = 0; i < n; ++i) {
        ++value;
    }
}

int x = 0;
advance(x, 5);  // ✅ int is incrementable
```

## Checking Member Functions

```cpp showLineNumbers 
template<typename T>
concept Printable = requires(T x) {
    { x.print() } -> std::same_as<void>;  // Must have print() returning void
};

template<Printable T>
void display(const T& obj) {
    obj.print();
}

struct Widget {
    void print() { std::cout << "Widget\n"; }
};

display(Widget{});  // ✅ Widget has print()
// display(42);  // ❌ int doesn't have print()
```

## Checking Constructors

```cpp showLineNumbers 
template<typename T>
concept DefaultConstructible = requires {
    T{};  // Can default-construct
};

template<typename T>
concept ConstructibleFromInt = requires(int n) {
    T{n};  // Can construct from int
};

template<DefaultConstructible T>
T create() {
    return T{};
}
```

## Combining Requirements

```cpp showLineNumbers 
template<typename T>
concept Container = requires(T c) {
    // Type requirements
    typename T::value_type;
    typename T::iterator;
    
    // Operation requirements
    { c.begin() } -> std::same_as<typename T::iterator>;
    { c.end() } -> std::same_as<typename T::iterator>;
    { c.size() } -> std::convertible_to<size_t>;
    
    // Nested requirement
    requires std::is_default_constructible_v<T>;
};

template<Container T>
void process(const T& container) {
    for (auto it = container.begin(); it != container.end(); ++it) {
        // Process...
    }
}
```

## Short-Circuit Evaluation

Requirements are checked in order, stopping at first failure:

```cpp showLineNumbers 
template<typename T>
requires requires(T x) {
    x.size();           // Checked first
    x.begin();          // Only checked if size() exists
    { x[0] };           // Only checked if begin() exists
}
void process(const T& container);

// If size() doesn't exist, stops immediately
// Doesn't waste time checking begin() and operator[]
```

## Boolean Expressions

```cpp showLineNumbers 
template<typename T>
requires requires {
    requires sizeof(T) <= 8;  // Must be small
    requires std::is_trivially_copyable_v<T>;  // Must be trivial
    requires !std::is_pointer_v<T>;  // Must NOT be pointer
}
void optimize(T value) {
    // Fast path for small, trivial, non-pointer types
}
```

## With Standard Concepts

```cpp showLineNumbers 
#include <concepts>

template<typename T>
requires requires(T x) {
    requires std::integral<T>;  // Use standard concept
    requires sizeof(T) >= 4;     // At least 4 bytes
    { x * x } -> std::same_as<T>;  // Closed under multiplication
}
void process(T value) {
    auto squared = value * value;
}
```

## Real-World Example: Generic Swap

```cpp showLineNumbers 
template<typename T>
concept Swappable = requires(T a, T b) {
    { std::swap(a, b) } -> std::same_as<void>;
};

// Or more detailed
template<typename T>
concept MoveSwappable = requires(T a, T b) {
    requires std::is_move_constructible_v<T>;
    requires std::is_move_assignable_v<T>;
    { std::swap(a, b) } noexcept -> std::same_as<void>;
};

template<MoveSwappable T>
void sortTwo(T& a, T& b) {
    if (b < a) {
        std::swap(a, b);
    }
}
```

## Debugging Requires Expressions

```cpp showLineNumbers 
template<typename T>
concept Debuggable = requires(T x) {
    { x.print() } -> std::same_as<void>;
};

// When constraint fails, compiler shows exactly which requirement failed
template<Debuggable T>
void debug(const T& obj) {
    obj.print();
}

struct NoDebug {};
// debug(NoDebug{});
// Error: constraints not satisfied
// note: { x.print() } -> std::same_as<void> failed
```

Much clearer than SFINAE errors!

## Common Patterns

**Range-like:**
```cpp showLineNumbers 
template<typename T>
concept Range = requires(T r) {
    r.begin();
    r.end();
    { r.begin() != r.end() } -> std::convertible_to<bool>;
};
```

**Arithmetic:**
```cpp showLineNumbers 
template<typename T>
concept Arithmetic = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
    { a - b } -> std::same_as<T>;
    { a * b } -> std::same_as<T>;
    { a / b } -> std::same_as<T>;
};
```

**Comparable:**
```cpp showLineNumbers 
template<typename T>
concept Comparable = requires(T a, T b) {
    { a == b } -> std::convertible_to<bool>;
    { a != b } -> std::convertible_to<bool>;
    { a < b } -> std::convertible_to<bool>;
};
```

:::success Requires Expression Essentials

**Simple** = `x.foo()` checks if valid  
**Type** = `typename T::value_type` checks type exists  
**Compound** = `{ expr } -> concept` checks type  
**Nested** = `requires condition` checks compile-time bool  
**Readable** = much clearer than SFINAE  
**Short-circuit** = stops at first failure  
**Error messages** = shows exactly what failed  
**Building block** = foundation for concepts
:::