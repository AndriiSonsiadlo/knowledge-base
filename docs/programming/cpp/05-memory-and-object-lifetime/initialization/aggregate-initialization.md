---
id: aggregate-initialization
title: Aggregate Initialization
sidebar_label: Aggregate Initialization
sidebar_position: 3
tags: [c++, initialization, aggregates, structs, arrays]
---

# Aggregate Initialization

Aggregate initialization allows you to initialize arrays and simple structs using brace-enclosed lists of values. This provides a concise syntax for initializing multiple members at once without requiring constructors.

:::info What is an Aggregate?
An aggregate is an array or a class with no user-declared constructors, no private or protected non-static data members, no base classes, and no virtual functions.
:::

## Arrays

Arrays are the simplest form of aggregates. You can initialize them by providing values in braces, and the compiler matches each value to the corresponding array element by position.

```cpp showLineNumbers 
int arr[5] = {1, 2, 3, 4, 5};  // All elements initialized

for (int i = 0; i < 5; ++i) {
    std::cout << arr[i];  // Prints: 1 2 3 4 5
}
```

The values in the braces are assigned to array elements in order from index 0 onward. This is both concise and clear, avoiding the need for loops or individual assignments. The initialization happens at compile-time when the values are constants, which can be more efficient than runtime initialization.

### Partial Initialization

When you provide fewer initializers than array elements, the remaining elements are value-initialized (set to zero for fundamental types). This is a convenient way to initialize only some elements while zeroing the rest.

```cpp showLineNumbers 
int arr[5] = {1, 2, 3};  // arr = {1, 2, 3, 0, 0}
// Elements 3 and 4 are value-initialized to 0

std::cout << arr[3];  // ✅ Safe: 0
std::cout << arr[4];  // ✅ Safe: 0
```

This behavior is particularly useful when you want to initialize the first few elements and don't care about the exact values of the rest, as long as they're zeroed. It's much cleaner than manually assigning zero to each remaining element.

### Complete Zero Initialization

An empty initializer list provides a shorthand for zero-initializing all array elements. This is equivalent to value initialization and guarantees all elements are set to zero.

```cpp showLineNumbers 
int arr[5] = {};  // All elements initialized to 0

// Equivalent to:
int arr[5] = {0, 0, 0, 0, 0};
```

## Simple Structures

Structures that meet the aggregate requirements can be initialized using brace-enclosed lists where each value initializes the corresponding member in declaration order. This provides clean syntax without requiring constructor definitions.

```cpp showLineNumbers 
struct Point {
    int x;
    int y;
};

Point p = {10, 20};  // x = 10, y = 20
std::cout << p.x << ", " << p.y;  // Prints: 10, 20
```

The members are initialized in the order they're declared in the struct. This makes the code self-documenting: when you see `{10, 20}`, you immediately know you're setting x to 10 and y to 20 because that's the declaration order in the struct definition.

### Nested Aggregates

Aggregates can contain other aggregates, and you can use nested braces to initialize them. The inner braces initialize the nested aggregate, while the outer braces initialize the containing aggregate.

```cpp showLineNumbers 
struct Point {
    int x, y;
};

struct Line {
    Point start;
    Point end;
};

Line line = {{0, 0}, {10, 20}};  // Nested initialization
// line.start = {0, 0}
// line.end = {10, 20}

std::cout << line.end.y;  // Prints: 20
```

The nested brace structure mirrors the struct's layout, making initialization clear and maintainable. You can see at a glance how the nested data structures are being populated.

### Omitting Inner Braces

You can actually omit inner braces in nested aggregate initialization, and the initializers will be assigned to members in order. However, this makes the code less clear about the structure being initialized.

```cpp showLineNumbers 
Line line = {0, 0, 10, 20};  // Valid but less clear
// Same as {{0, 0}, {10, 20}}
```

While this works, it's generally better style to include the inner braces because they make the structure's organization explicit. The brevity gained by omitting braces isn't worth the loss in clarity.

## Designated Initializers (C++20)

C++20 introduced designated initializers, allowing you to explicitly name which member you're initializing. This makes aggregate initialization more self-documenting and allows you to initialize members out of order (though they must still be in declaration order).

```cpp showLineNumbers 
struct Point {
    int x;
    int y;
    int z;
};

Point p = {.x = 10, .y = 20, .z = 30};  // C++20

// Can omit members (they're value-initialized)
Point p2 = {.x = 5, .z = 15};  // y = 0
```

Designated initializers significantly improve code readability by making it explicit which member receives which value. You no longer have to count positions or refer back to the struct definition to understand what's being initialized. The omitted member `.y` is value-initialized to zero, which is often what you want.

### Partial Designated Initialization

You can initialize only some members using designated initializers, and the remaining members are value-initialized. This is particularly useful for large structs where you only need to set a few fields.

```cpp showLineNumbers 
struct Config {
    int timeout;
    int retry_count;
    bool debug_mode;
    int buffer_size;
};

Config cfg = {.timeout = 5000, .debug_mode = true};
// retry_count = 0, buffer_size = 0 (value-initialized)
```

## Aggregate Requirements

Not every struct can be initialized as an aggregate. The requirements are deliberately restrictive to ensure that aggregate initialization has well-defined semantics without requiring complex constructor logic.

```cpp showLineNumbers 
// ✅ Valid aggregate
struct Aggregate {
    int a;
    double b;
};

// ❌ Not aggregate: has constructor
struct NotAggregate1 {
    int a;
    NotAggregate1(int x) : a(x) {}
};

// ❌ Not aggregate: has private members
struct NotAggregate2 {
private:
    int a;
public:
    int b;
};

// ❌ Not aggregate: has base class
struct NotAggregate3 : Aggregate {
    int c;
};

// ❌ Not aggregate: has virtual function
struct NotAggregate4 {
    int a;
    virtual void func() {}
};
```

These restrictions ensure that aggregate initialization is simple and efficient. If a class needs complex initialization logic, it should use constructors instead. Aggregates are meant for simple data structures that are just collections of public data members.

## Arrays of Aggregates

You can combine array initialization with aggregate initialization to create arrays of structs. This is commonly used for lookup tables and configuration data.

```cpp showLineNumbers 
struct Point {
    int x, y;
};

Point points[3] = {
    {0, 0},
    {10, 20},
    {30, 40}
};

for (int i = 0; i < 3; ++i) {
    std::cout << "(" << points[i].x << ", " << points[i].y << ")\n";
}
// Prints:
// (0, 0)
// (10, 20)
// (30, 40)
```

Each element of the array is itself an aggregate, so you use nested braces where the outer braces initialize the array and each inner set of braces initializes one struct. This pattern is very efficient because all initialization can happen at compile-time for const data.

## Partial Aggregate Initialization

When you provide fewer initializers than aggregate members, the remaining members are value-initialized. For fundamental types, this means they're set to zero, making partial initialization safe and predictable.

```cpp showLineNumbers 
struct Widget {
    int a;
    int b;
    int c;
};

Widget w = {1, 2};  // w = {1, 2, 0}
// c is value-initialized to 0

std::cout << w.c;  // ✅ Safe: 0
```

This behavior is consistent with array initialization and provides a convenient way to set only the members you care about while ensuring the others have deterministic values rather than garbage.

## Using Aggregates with STL

Standard library containers work seamlessly with aggregate-initialized objects. You can construct aggregates directly in place using brace initialization.

```cpp showLineNumbers 
struct Point {
    int x, y;
};

std::vector<Point> points = {
    {0, 0},
    {10, 20},
    {30, 40}
};

// Or emplace:
points.emplace_back(Point{50, 60});
```

The brace initialization syntax integrates naturally with STL containers, making it easy to build up collections of aggregate objects without explicitly calling constructors. This is one of the reasons aggregates are popular for simple data structures.

## Comparison with Constructors

Aggregates provide a lightweight alternative to classes with constructors for simple data structures. If your type is just a collection of public data members, using an aggregate is simpler than writing constructors.

```cpp showLineNumbers 
// Aggregate approach (simple)
struct Point {
    int x, y;
};
Point p = {10, 20};

// Constructor approach (more code)
class PointClass {
    int x, y;
public:
    PointClass(int x_, int y_) : x(x_), y(y_) {}
    int getX() const { return x; }
    int getY() const { return y; }
};
PointClass pc(10, 20);
```

The aggregate approach has less boilerplate code and is sufficient when you don't need encapsulation or invariants. However, if you need to validate inputs or maintain invariants, proper constructors are necessary. Choose aggregates for plain data and classes with constructors when you need more control.

## Summary

Aggregate initialization provides a clean syntax for initializing arrays and simple structs using brace-enclosed lists. Aggregates must have no user-declared constructors, no private members, no base classes, and no virtual functions, ensuring they remain simple data containers. You can partially initialize aggregates, with remaining members being value-initialized to zero. C++20's designated initializers make aggregate initialization even more readable by allowing named member initialization. Aggregates are perfect for plain data structures where you don't need encapsulation or complex initialization logic, and they integrate seamlessly with STL containers through brace initialization. When your type is just a collection of public data members, using aggregate initialization is simpler and clearer than writing explicit constructors.