---
id: value-initialization
title: Value Initialization
sidebar_label: Value Initialization
sidebar_position: 2
tags: [c++, initialization, value-init, zero-initialization]
---

# Value Initialization

Value initialization provides a way to explicitly request zero-initialization for fundamental types and default construction for class types. Unlike default initialization, value initialization guarantees that fundamental types are set to zero rather than left with indeterminate values.

:::success Safer than Default
Value initialization ensures fundamental types are zeroed, making it safer than default initialization which leaves values indeterminate.
:::

## Syntax for Value Initialization

Value initialization is triggered by using empty parentheses or braces when creating an object. This explicit syntax signals to the compiler that you want a "zero-like" value rather than an indeterminate one.

```cpp showLineNumbers 
int x{};        // Value-initialized to 0
int y = int();  // Value-initialized to 0
double d{};     // Value-initialized to 0.0
int* ptr{};     // Value-initialized to nullptr

std::cout << x;    // ✅ Safe: 0
std::cout << y;    // ✅ Safe: 0
std::cout << d;    // ✅ Safe: 0.0
std::cout << ptr;  // ✅ Safe: nullptr
```

The key difference from default initialization is that value initialization performs zero-initialization first. For fundamental types, this means the object is set to zero (or nullptr for pointers, false for bool). For class types that have a user-defined constructor, that constructor is called just as with default initialization.

## Fundamental Types

For all fundamental types, value initialization produces a predictable zero value. This makes value initialization much safer than default initialization when you need to ensure a known starting state.

```cpp showLineNumbers 
void function() {
    // Default initialization - indeterminate values
    int a;
    double b;
    bool c;
    char* d;
    
    // Value initialization - zero values
    int x{};        // 0
    double y{};     // 0.0
    bool z{};       // false
    char* ptr{};    // nullptr
}
```

This behavior is particularly important for types like pointers, where an indeterminate value can lead to crashes when dereferenced. Value-initializing a pointer always yields nullptr, which can be safely checked before use. The performance cost of this initialization is typically negligible compared to the safety benefit.

## Class Types

For class types, value initialization's behavior depends on whether the class has any user-defined constructors. If the class has user-defined constructors, value initialization calls the default constructor, just like default initialization would.

```cpp showLineNumbers 
class Widget {
    int value;
public:
    Widget() : value(42) {
        std::cout << "Constructor called\n";
    }
};

Widget w1;    // Default initialization - calls Widget()
Widget w2{};  // Value initialization - also calls Widget()
// Both produce the same result when a constructor exists
```

When a user-defined constructor exists, both default and value initialization produce identical behavior. The distinction only matters when there's no user-defined constructor or when dealing with fundamental types.

### Classes Without User-Defined Constructors

The real difference in behavior appears when a class has no user-defined constructors. In this case, value initialization zero-initializes all members, while default initialization leaves fundamental type members with indeterminate values.

```cpp showLineNumbers 
struct Point {
    int x;
    int y;
    // No constructor defined
};

Point p1;    // Default initialization: x and y indeterminate ❌
Point p2{};  // Value initialization: x = 0, y = 0 ✅

std::cout << p1.x;  // ❌ Undefined behavior
std::cout << p2.x;  // ✅ Safe: 0
```

This makes value initialization the safer choice when working with simple aggregates (structs or classes with no constructors). The empty braces guarantee that all members, including fundamental types, are properly zeroed out rather than containing garbage values.

## Arrays

Arrays can be value-initialized to ensure all elements are properly initialized. For fundamental type arrays, this means all elements are set to zero. For class type arrays, each element is value-initialized according to the rules for that type.

```cpp showLineNumbers 
int arr1[5];     // Default initialization: indeterminate values ❌
int arr2[5]{};   // Value initialization: all zeros ✅

for (int i = 0; i < 5; ++i) {
    std::cout << arr1[i];  // ❌ Undefined behavior
    std::cout << arr2[i];  // ✅ Safe: 0
}
```

Value initialization of arrays is particularly useful when you need a clean slate for an array but don't want to explicitly assign every element. The compiler generates efficient code to zero out the memory, which is often faster than manually writing a loop.

### Multi-Dimensional Arrays

Value initialization works with multi-dimensional arrays as well, zeroing out all elements regardless of the array's dimensionality.

```cpp showLineNumbers 
int matrix1[3][3];     // Indeterminate values
int matrix2[3][3]{};   // All zeros

matrix2[0][0];  // ✅ 0
matrix2[2][2];  // ✅ 0
```

## Dynamic Allocation with new

When using `new` to allocate objects dynamically, you can request value initialization by using parentheses or braces. Without these, fundamental types are default-initialized (left with indeterminate values).

```cpp showLineNumbers 
int* p1 = new int;      // Default-initialized: indeterminate value ❌
int* p2 = new int();    // Value-initialized: 0 ✅
int* p3 = new int{};    // Value-initialized: 0 ✅

std::cout << *p1;  // ❌ Undefined behavior
std::cout << *p2;  // ✅ Safe: 0

delete p1; delete p2; delete p3;
```

This distinction is critical when allocating fundamental types on the heap. The empty parentheses or braces ensure the allocated memory contains a zero rather than random garbage. This small syntactic difference can prevent subtle bugs where you accidentally use uninitialized heap memory.

### Array Allocation

When allocating arrays dynamically, value initialization can be requested for each element. This is particularly useful for fundamental type arrays where you want to ensure clean initialization.

```cpp showLineNumbers 
int* arr1 = new int[10];     // Default-initialized: indeterminate ❌
int* arr2 = new int[10]();   // Value-initialized: all zeros ✅
int* arr3 = new int[10]{};   // Value-initialized: all zeros ✅

std::cout << arr1[0];  // ❌ Undefined behavior
std::cout << arr2[0];  // ✅ Safe: 0

delete[] arr1; delete[] arr2; delete[] arr3;
```

## Member Initialization

When initializing members in a constructor's initializer list, using empty braces provides value initialization for each member. This is a clean way to ensure all members start in a known state.

```cpp showLineNumbers 
class Container {
    int value;
    double ratio;
    int* ptr;
    
public:
    Container() 
        : value{},    // Value-initialized to 0
          ratio{},    // Value-initialized to 0.0
          ptr{}       // Value-initialized to nullptr
    {}
    
    void print() {
        std::cout << value;  // ✅ Safe: 0
        std::cout << ratio;  // ✅ Safe: 0.0
        if (ptr) {           // ✅ Safe: always false
            *ptr = 42;
        }
    }
};
```

This pattern guarantees that even if you forget to provide explicit values, the members have sensible defaults. It's more explicit and safer than relying on default initialization, which would leave the fundamental type members with indeterminate values.

## Comparison with Default Initialization

Understanding when to use value initialization versus default initialization is important for writing correct code. The choice affects both correctness and performance.

```cpp showLineNumbers 
// Default initialization
int a;              // Indeterminate value - dangerous ❌
Widget w;           // Calls Widget() - fine if constructor exists ✅

// Value initialization  
int b{};            // Always 0 - safe ✅
Widget w2{};        // Calls Widget() - same as default for classes ✅
```

For fundamental types, value initialization is almost always preferable unless you're immediately assigning a value and concerned about micro-optimizations. For class types with constructors, the behavior is identical, so the choice is mostly stylistic. However, using consistent value initialization syntax (with braces) is safer because it works correctly in all cases.

## Performance Considerations

Value initialization does have a small performance cost compared to default initialization because it requires zeroing memory. However, this cost is typically negligible and far outweighed by the safety benefits of not having indeterminate values.

```cpp showLineNumbers 
void process_large_array() {
    int data[1000000];     // No initialization cost
    // But data is full of garbage! ❌
    
    int safe_data[1000000]{}; // Small cost to zero memory
    // But safe to read any element ✅
}
```

Modern compilers are very efficient at zero-initialization, often using special CPU instructions designed for this purpose. The performance difference is usually measured in nanoseconds and only matters in extremely performance-critical code paths. In almost all cases, the safety of value initialization is worth the tiny performance cost.

## Summary

Value initialization provides guaranteed zero-initialization for fundamental types while calling default constructors for class types. This makes it safer than default initialization, which leaves fundamental types with indeterminate values. The syntax uses empty parentheses or braces: `int x{}`, `new int()`, or `member{}` in initializer lists. While there is a small performance cost for the zero-initialization, it's typically negligible and prevents dangerous undefined behavior from reading uninitialized values. As a general rule, prefer value initialization (empty braces) for fundamental types unless you're immediately assigning a value, and use it for class types when you want explicit default construction. This consistent approach eliminates entire categories of bugs related to indeterminate values.