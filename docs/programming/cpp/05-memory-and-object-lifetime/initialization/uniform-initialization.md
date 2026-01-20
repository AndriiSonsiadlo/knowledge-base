---
id: uniform-initialization
title: Uniform Initialization
sidebar_label: Uniform Initialization
sidebar_position: 4
tags: [c++, initialization, uniform-init, cpp11, braces]
---

# Uniform Initialization

Uniform initialization (also called brace initialization or list initialization) is a C++11 feature that provides a consistent syntax for all types of initialization using braces. This single syntax works for fundamental types, aggregates, classes, arrays, and STL containers, eliminating the need to remember multiple initialization syntaxes.

:::success One Syntax for Everything
Braces `{}` work for any type, making initialization uniform across the language. This consistency improves code readability and reduces initialization-related bugs.
:::

## The Motivation

Before C++11, C++ had multiple initialization syntaxes that could be confusing and sometimes behaved differently. Uniform initialization was introduced to provide one syntax that works everywhere.

```cpp showLineNumbers 
// Pre-C++11: Multiple confusing syntaxes
int a = 5;              // Copy initialization
int b(5);               // Direct initialization  
int c[] = {1, 2, 3};    // Array initialization
Widget w(10);           // Constructor call
std::vector<int> v;     // Default construction
v.push_back(1);         // Can't initialize with values easily

// C++11: Uniform syntax with braces
int a{5};
int b{5};
int c[]{1, 2, 3};
Widget w{10};
std::vector<int> v{1, 2, 3};  // Direct initialization!
```

The brace syntax unifies all these different forms, making the language more consistent and easier to teach. You can use braces everywhere and get predictable behavior.

## Basic Syntax

Braces can be used to initialize any type, from fundamental types to complex class types. The syntax is always the same: put the initializer values inside curly braces.

```cpp showLineNumbers 
int x{42};                    // Fundamental type
double d{3.14};              
std::string s{"hello"};       // Class type
int arr[]{1, 2, 3, 4, 5};    // Array
std::vector<int> vec{1, 2, 3}; // STL container
Widget w{10, 20};            // Custom class
```

This consistent syntax means you can initialize variables without remembering type-specific rules. Braces work the same way regardless of what type you're initializing, which significantly reduces cognitive load when writing code.

## Prevents Narrowing Conversions

One of the most important features of uniform initialization is that it prevents narrowing conversions - implicit conversions that might lose information. This catches common bugs at compile-time that would otherwise cause silent data loss.

```cpp showLineNumbers 
int x = 3.14;    // ⚠️ OK but truncates: x = 3 (silent data loss)
int y{3.14};     // ❌ Error: narrowing conversion

double d = 1000000;
int i = d;       // ⚠️ OK but dangerous (might overflow)
int j{d};        // ❌ Error: narrowing conversion

int large = 10000;
char c = large;  // ⚠️ OK but truncates
char d{large};   // ❌ Error: narrowing conversion
```

The compiler rejects any initialization that would lose precision or change the value. This compile-time checking prevents bugs that are hard to find with testing because they only manifest with certain input values. While you can work around this with explicit casts, the fact that you must be explicit makes the potential data loss visible.

## Default Initialization with Empty Braces

Empty braces provide value-initialization, which zero-initializes fundamental types and calls the default constructor for class types. This is safer than default initialization which leaves fundamental types with indeterminate values.

```cpp showLineNumbers 
int x{};        // Value-initialized to 0
double d{};     // Value-initialized to 0.0
bool b{};       // Value-initialized to false
int* ptr{};     // Value-initialized to nullptr

std::string s{};     // Calls default constructor
std::vector<int> v{}; // Calls default constructor
```

Using empty braces gives you predictable zero values for fundamental types, eliminating undefined behavior from reading uninitialized variables. For class types, it explicitly calls the default constructor, making your intent clear in the code.

## Most Vexing Parse Solution

Uniform initialization solves the "most vexing parse" problem where syntax that looks like a variable declaration is actually parsed as a function declaration. This was a notorious gotcha in C++98/03.

```cpp showLineNumbers 
// Pre-C++11: Most vexing parse
Widget w();  // ❌ This declares a function, not a variable!
// Function named 'w' that takes no args and returns Widget

// C++11: Braces create a variable
Widget w{};  // ✅ This creates a Widget object
```

The vexing parse occurred because the compiler always prefers to interpret syntax as a function declaration when possible. Braces cannot introduce a function declaration, so they unambiguously create an object. This removes an entire category of confusing bugs.

## Initializing STL Containers

Uniform initialization makes it easy to create STL containers with initial values. Before C++11, you often had to create an empty container and then add elements one by one.

```cpp showLineNumbers 
// Direct initialization with values
std::vector<int> v{1, 2, 3, 4, 5};
std::set<std::string> names{"Alice", "Bob", "Charlie"};
std::map<int, std::string> id_map{{1, "one"}, {2, "two"}};

// Compare to pre-C++11
std::vector<int> old_vec;
old_vec.push_back(1);
old_vec.push_back(2);
old_vec.push_back(3);
// Much more verbose!
```

The brace initialization syntax lets you see the container's initial contents at a glance. This is particularly useful for test data, constant lookup tables, and default configurations.

## Initializer Lists

When you use braces with multiple values, the compiler creates an `std::initializer_list` that's passed to the appropriate constructor. This is how STL containers know to initialize themselves with the values you provide.

```cpp showLineNumbers 
std::vector<int> v{1, 2, 3};
// Calls: vector(std::initializer_list<int>)

class Container {
public:
    Container(std::initializer_list<int> init) {
        for (int value : init) {
            // Process each value
        }
    }
};

Container c{1, 2, 3, 4};  // Calls initializer_list constructor
```

Initializer list constructors are given priority when braces are used with multiple values. This means containers like `std::vector` can be directly initialized with a list of elements, which is much more convenient than other initialization methods.

## Initialization with Parentheses vs Braces

While braces work universally, parentheses still exist for backward compatibility. Understanding when each syntax is preferred helps you write more idiomatic code.

```cpp showLineNumbers 
std::vector<int> v1(10);     // Constructor: vector of 10 zeros
std::vector<int> v2{10};     // Initializer list: vector with one element: 10

std::vector<int> v3(10, 5);  // Constructor: 10 elements, each = 5
std::vector<int> v4{10, 5};  // Initializer list: two elements: 10 and 5
```

This difference can be surprising. Braces prefer initializer list constructors when available, while parentheses call regular constructors. For containers, this means braces create lists of elements while parentheses set container size and fill value. Understanding this distinction is important for writing correct container initializations.

## Constructor Overload Priority

When a class has both an initializer list constructor and regular constructors, braces always prefer the initializer list constructor, even if the regular constructor would be a better match.

```cpp showLineNumbers 
class Widget {
public:
    Widget(int x, int y) {  // Regular constructor
        std::cout << "Regular: " << x << ", " << y << "\n";
    }
    
    Widget(std::initializer_list<int> list) {  // Initializer list constructor
        std::cout << "Initializer list: " << list.size() << " elements\n";
    }
};

Widget w1(10, 20);   // Calls regular constructor
// Output: Regular: 10, 20

Widget w2{10, 20};   // Calls initializer_list constructor!
// Output: Initializer list: 2 elements
```

The initializer list constructor takes precedence with braces even though the regular constructor would be a perfect match. This is usually the right behavior for containers, but it can be surprising with custom classes. If you want to call a specific constructor, use parentheses instead of braces.

## Copy List Initialization

You can also use braces with the assignment syntax for copy list initialization. This combines the consistency of braces with traditional assignment-style declaration.

```cpp showLineNumbers 
int x = {42};                // Copy list initialization
std::string s = {"hello"};
std::vector<int> v = {1, 2, 3};

// Still prevents narrowing
int y = {3.14};  // ❌ Error: narrowing conversion
```

Copy list initialization provides the same benefits as direct list initialization (narrowing prevention, uniform syntax) but looks more like traditional initialization. This can make code more familiar to programmers used to assignment-style initialization.

## Aggregate Initialization

Braces work naturally with aggregates (arrays and simple structs), maintaining the traditional aggregate initialization syntax while adding narrowing protection.

```cpp showLineNumbers 
struct Point {
    int x, y;
};

Point p{10, 20};  // Aggregate initialization with braces

int arr[]{1, 2, 3, 4, 5};  // Array with braces

// Narrowing still prevented
Point bad{3.14, 2.71};  // ❌ Error: narrowing double to int
```

Using braces for aggregate initialization is safer than traditional syntax because it catches type mismatches. This protection is particularly valuable when initializing configuration structures or data tables.

## Brace Elision

When initializing nested aggregates, you can omit inner braces and the compiler will match initializers to members in order. However, including inner braces makes the structure clearer.

```cpp showLineNumbers 
struct Inner { int a, b; };
struct Outer { Inner i; int c; };

Outer o1 = {{1, 2}, 3};  // With inner braces (clear)
Outer o2 = {1, 2, 3};    // Without inner braces (works but less clear)
```

While brace elision is allowed, explicit inner braces make the nesting structure obvious. This is especially important for complex nested structures where the declaration order might not be immediately apparent.

## When to Use Braces vs Parentheses

As a general guideline, prefer braces for their safety benefits, but use parentheses when you specifically need to avoid the initializer list constructor or when the braces syntax would be confusing.

```cpp showLineNumbers 
// Prefer braces (safety, consistency)
int x{42};
std::string s{"hello"};
std::vector<int> v{1, 2, 3};

// Use parentheses for container sizing
std::vector<int> v(100);      // 100 zeros
std::string s(10, 'x');        // "xxxxxxxxxx"

// Use parentheses to avoid initializer_list constructor
Widget w(10, 20);  // Calls Widget(int, int) not Widget(initializer_list)
```

The narrowing prevention and consistency of braces make them the better default choice. However, there are legitimate cases where parentheses are more appropriate, particularly when sizing containers or when you need to call a specific constructor.

## Summary

Uniform initialization with braces provides a single, consistent syntax that works for all types. It prevents dangerous narrowing conversions at compile-time, catching bugs that would otherwise cause silent data loss. Empty braces provide safe value-initialization (zero for fundamental types), solving the undefined behavior problem of uninitialized variables. Braces also solve the most vexing parse and make STL container initialization straightforward. However, be aware that braces prefer initializer list constructors when available, which can lead to different behavior than parentheses for the same values. As a general rule, prefer braces for their safety and consistency, but understand when parentheses are more appropriate (container sizing, avoiding initializer list constructors). This modern initialization syntax is one of C++11's most important improvements for writing safer, more consistent code.