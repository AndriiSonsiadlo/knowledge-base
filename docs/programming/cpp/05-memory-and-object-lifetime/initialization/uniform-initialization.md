---
id: uniform-initialization
title: Uniform Initialization
sidebar_label: Uniform Initialization
sidebar_position: 4
tags: [c++, initialization, uniform-init, cpp11, braces]
---

# Uniform Initialization

C++11 brace initialization `{}` - one syntax for all types. Consistent, safe (prevents narrowing), solves gotchas.

:::success One Syntax, Everywhere
Braces `{}` work for any type: fundamentals, aggregates, classes, arrays, containers. Prevents narrowing conversions.
:::

## Motivation: Multiple Syntaxes → One
```cpp showLineNumbers
// Pre-C++11: confusing variety
int a = 5;
int b(5);
int c[] = {1, 2, 3};
Widget w(10);
std::vector<int> v; v.push_back(1);

// C++11: uniform braces
int a{5};
int b{5};
int c[]{1, 2, 3};
Widget w{10};
std::vector<int> v{1, 2, 3};  // ✅ Direct!
```

## Basic Syntax
```cpp showLineNumbers
int x{42};
double d{3.14};
std::string s{"hello"};
int arr[]{1, 2, 3, 4, 5};
std::vector<int> vec{1, 2, 3};
Widget w{10, 20};
```

**Rule**: Braces work everywhere, same syntax.

## Prevents Narrowing Conversions

Catches silent data loss at compile-time.
```cpp showLineNumbers
// Old style: silent truncation
int x = 3.14;    // ⚠️ OK but x = 3 (data loss)
double d = 1000000;
int i = d;       // ⚠️ OK but dangerous

// Braces: compile error
int y{3.14};     // ❌ Error: narrowing
int j{d};        // ❌ Error: narrowing

char c = 1000;   // ⚠️ OK but truncated
char d{1000};    // ❌ Error: narrowing
```

**Benefit**: Catches bugs at compile-time, not runtime.

## Safe Zero Initialization

Empty braces = value-initialization (zero for fundamentals).
```cpp showLineNumbers
int x{};        // 0
double d{};     // 0.0
bool b{};       // false
int* ptr{};     // nullptr

std::string s{};       // Default constructor
std::vector<int> v{};  // Default constructor
```

**Safe**: No indeterminate values, explicit intent.

## Solves Most Vexing Parse
```cpp showLineNumbers
// Pre-C++11
Widget w();  // ❌ Function declaration, not object!

// C++11
Widget w{};  // ✅ Unambiguous: creates object
```

**Fix**: Braces cannot declare functions, always create objects.

## STL Containers
```cpp showLineNumbers
// Direct initialization with values
std::vector<int> v{1, 2, 3, 4, 5};
std::set<std::string> names{"Alice", "Bob"};
std::map<int, std::string> m{{1, "one"}, {2, "two"}};

// vs Pre-C++11 verbosity
std::vector<int> old;
old.push_back(1);
old.push_back(2);
// ...
```

## Initializer List Priority

Braces prefer `std::initializer_list` constructor.
```cpp showLineNumbers
std::vector<int> v1(10);     // 10 zeros
std::vector<int> v2{10};     // One element: 10

std::vector<int> v3(10, 5);  // 10 elements, each = 5
std::vector<int> v4{10, 5};  // Two elements: 10, 5
```

**Important**: Braces create element lists, parentheses call constructors.

### Constructor Overload Priority
```cpp showLineNumbers
class Widget {
public:
    Widget(int x, int y) {
        std::cout << "Regular: " << x << ", " << y << "\n";
    }
    
    Widget(std::initializer_list<int> list) {
        std::cout << "List: " << list.size() << " elements\n";
    }
};

Widget w1(10, 20);   // Regular: 10, 20
Widget w2{10, 20};   // List: 2 elements (prefers initializer_list!)
```

**Rule**: Braces always prefer `initializer_list` constructor when available.

## When to Use Each

| Syntax | Use For |
|--------|---------|
| `{}` braces | Default choice (safe, consistent) |
| `()` parens | Container sizing, avoid `initializer_list` |
```cpp showLineNumbers
// Prefer braces (safety)
int x{42};
std::string s{"hello"};
std::vector<int> v{1, 2, 3};  // Element list

// Use parentheses for sizing
std::vector<int> v(100);      // 100 zeros
std::string s(10, 'x');       // "xxxxxxxxxx"

// Avoid initializer_list constructor
Widget w(10, 20);  // Call Widget(int, int)
```

## Copy List Initialization
```cpp showLineNumbers
int x = {42};
std::string s = {"hello"};
std::vector<int> v = {1, 2, 3};

// Still prevents narrowing
int y = {3.14};  // ❌ Error
```

## Quick Decision Guide
```mermaid
graph TD
    A[Need initialization?] -->|Safety| B[Use braces {}]
    B -->|Exception 1| C[Container sizing]
    B -->|Exception 2| D[Avoid initializer_list]
    
    C --> E[Use parentheses]
    D --> E
    
    style B fill:#90EE90
```

## Key Benefits Summary

| Feature | Benefit |
|---------|---------|
| **Uniform syntax** | Works everywhere |
| **Narrowing prevention** | Catches type errors |
| **Zero initialization** | Safe defaults with `{}` |
| **Most vexing parse** | Solved |
| **STL containers** | Direct initialization |

## Common Gotchas
```cpp showLineNumbers
// 1. Initializer list priority
std::vector<int> v{10};  // ONE element, not size!

// 2. Narrowing errors (feature, not bug)
int x{3.14};  // ❌ Error (this is good!)

// 3. Empty braces call default constructor
Widget w{};  // Calls Widget(), not Widget(initializer_list)
```

## Summary

Uniform initialization with braces `{}` provides one syntax for all types. **Prevents narrowing** conversions (compile-time safety), **solves most vexing parse**, enables **direct STL container initialization**. Empty braces `{}` safely zero-initialize fundamentals. **Braces prefer `initializer_list` constructors** - use parentheses for container sizing or to avoid this. General rule: **prefer braces** for safety and consistency, use parentheses when specifically needed.
```cpp
// Interview answer:
// "Uniform initialization (C++11 braces) provides one syntax
// for all types. Key benefits: prevents narrowing conversions
// at compile-time, solves most vexing parse, enables direct
// container initialization. Empty braces safely zero-initialize.
// Braces prefer initializer_list constructors - use parentheses
// for container sizing. Default to braces for safety unless
// you specifically need parentheses behavior."
```