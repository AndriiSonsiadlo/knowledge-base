---
id: aggregate-initialization
title: Aggregate Initialization
sidebar_label: Aggregate Initialization
sidebar_position: 3
tags: [c++, initialization, aggregates, structs, arrays]
---

# Aggregate Initialization

Initialize arrays and simple structs using brace-enclosed lists without constructors. Concise syntax for multiple members.

:::info What's an Aggregate?
Array OR class with: no user constructors, no private/protected members, no base classes, no virtual functions.
:::

## Arrays
```cpp showLineNumbers
// Full initialization
int arr[5] = {1, 2, 3, 4, 5};

// Partial initialization (rest zeroed)
int arr[5] = {1, 2, 3};  // {1, 2, 3, 0, 0}

// Zero initialization
int arr[5] = {};  // All zeros
```

**Rule**: Fewer initializers → remaining elements value-initialized to zero.

## Simple Structures
```cpp showLineNumbers
struct Point {
    int x;
    int y;
};

Point p = {10, 20};  // x=10, y=20 (declaration order)
```

**Order**: Members initialized in declaration order.

### Nested Aggregates
```cpp showLineNumbers
struct Point { int x, y; };
struct Line { Point start, end; };

Line line = {{0, 0}, {10, 20}};  // ✅ Clear structure

// Can omit inner braces (less clear)
Line line2 = {0, 0, 10, 20};  // Works but confusing
```

**Best practice**: Include inner braces for clarity.

## Designated Initializers (C++20)

Name members explicitly for self-documenting code.
```cpp showLineNumbers
struct Point {
    int x;
    int y;
    int z;
};

Point p = {.x = 10, .y = 20, .z = 30};

// Omit members (zeroed)
Point p2 = {.x = 5, .z = 15};  // y = 0
```

**Benefits**: Clear, explicit, can omit members (they're zeroed).

### Partial Initialization
```cpp showLineNumbers
struct Config {
    int timeout;
    int retry_count;
    bool debug_mode;
    int buffer_size;
};

Config cfg = {.timeout = 5000, .debug_mode = true};
// retry_count = 0, buffer_size = 0
```

## Aggregate Requirements
```cpp showLineNumbers
// ✅ Aggregate
struct Good {
    int a;
    double b;
};

// ❌ Has constructor
struct Bad1 {
    int a;
    Bad1(int x) : a(x) {}
};

// ❌ Has private members
struct Bad2 {
private:
    int a;
public:
    int b;
};

// ❌ Has base class
struct Bad3 : Good {
    int c;
};

// ❌ Has virtual function
struct Bad4 {
    int a;
    virtual void func() {}
};
```

**Restrictions**: Keep aggregates simple - just public data members.

## Arrays of Aggregates
```cpp showLineNumbers
struct Point { int x, y; };

Point points[3] = {
    {0, 0},
    {10, 20},
    {30, 40}
};

// Partial array initialization
Point points2[5] = {{1, 2}, {3, 4}};  // Last 3 are {0, 0}
```

## Partial Initialization Safety
```cpp showLineNumbers
struct Widget {
    int a;
    int b;
    int c;
};

Widget w = {1, 2};  // {1, 2, 0} - c is zeroed ✅
```

**Safety**: Unspecified members value-initialized (zero for fundamentals).

## STL Integration
```cpp showLineNumbers
struct Point { int x, y; };

std::vector<Point> points = {
    {0, 0},
    {10, 20},
    {30, 40}
};

points.emplace_back(Point{50, 60});
```

## Quick Comparison

| Feature | Aggregate | Class with Constructor |
|---------|-----------|------------------------|
| **Syntax** | `{1, 2}` | `(1, 2)` or `{1, 2}` |
| **Boilerplate** | None | Constructor code |
| **Encapsulation** | No | Yes |
| **Validation** | No | Yes |
| **Use case** | Plain data | Complex invariants |
```cpp showLineNumbers
// Aggregate (simple)
struct Point { int x, y; };
Point p = {10, 20};

// Class (more control)
class Point {
    int x, y;
public:
    Point(int x_, int y_) : x(x_), y(y_) {
        if (x < 0 || y < 0) throw std::invalid_argument("Negative!");
    }
};
```

## Summary

Aggregate initialization uses brace-enclosed lists for arrays and simple structs. **Requirements**: no user constructors, all public members, no inheritance, no virtual functions. Partial initialization zeros remaining members. **C++20 designated initializers** (`.x = 10`) make code self-documenting. Perfect for plain data structures; use classes with constructors when you need validation or encapsulation.
```cpp
// Interview answer:
// "Aggregate initialization uses braces to initialize arrays
// and simple structs. Aggregates must have no user constructors,
// all public members, no base classes, no virtual functions.
// Fewer initializers → rest are zeroed. C++20 adds designated
// initializers (.x = 10) for clarity. Use for plain data;
// use constructors when you need validation or invariants."
```