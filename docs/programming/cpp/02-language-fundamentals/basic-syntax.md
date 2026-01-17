---
id: basic-syntax
title: C++ Basic Syntax
sidebar_label: Basic Syntax
sidebar_position: 1
tags: [c++, syntax, fundamentals, basics]
---

# C++ Basic Syntax

C++ syntax defines how code is written and structured. Understanding basic syntax is essential for writing valid C++ programs.

:::info Case Sensitive
C++ is case-sensitive: `variable`, `Variable`, and `VARIABLE` are three different identifiers.
:::

## Hello World

```cpp
#include <iostream>  // Preprocessor directive

int main() {         // Entry point
    std::cout << "Hello, World!\n";  // Output
    return 0;        // Exit status
}
```

**Breakdown**:
- `#include` copies iostream library contents
- `main()` is where execution starts (required)
- `std::cout` is standard output stream
- `<<` is output operator
- `return 0` indicates success to OS

---

## Statements and Expressions

```cpp
int x = 5;           // Statement (ends with ;)
x + 3;               // Expression
x = x + 1;           // Statement containing expression

if (x > 0) {         // Statement
    std::cout << x;  // Statement inside block
}
```

**Statement**: Complete instruction ending with `;`  
**Expression**: Produces a value (`5 + 3`, `x > 0`)  
**Block**: `{ }` groups multiple statements

---

## Comments

```cpp
// Single-line comment

/* Multi-line
   comment */

int x = 5;  // Inline comment

/*
 * Documentation style
 * multi-line comment
 */
```

---

## Variables and Types

```cpp
int age = 25;                    // Integer
double price = 19.99;            // Floating-point
char grade = 'A';                // Single character
bool is_valid = true;            // Boolean
std::string name = "Alice";     // String (C++11)

auto value = 42;                 // Type deduction (int)
auto ratio = 3.14;               // double
```

---

## Operators

```cpp
// Arithmetic
int sum = 5 + 3;     // Addition
int diff = 5 - 3;    // Subtraction
int prod = 5 * 3;    // Multiplication
int quot = 5 / 3;    // Division (integer)
int rem = 5 % 3;     // Modulus (remainder)

// Comparison
bool eq = (x == y);  // Equal
bool ne = (x != y);  // Not equal
bool gt = (x > y);   // Greater than
bool lt = (x < y);   // Less than

// Logical
bool and_op = (x > 0 && y > 0);  // AND
bool or_op = (x > 0 || y > 0);   // OR
bool not_op = !(x > 0);           // NOT

// Assignment
x = 5;               // Assign
x += 3;              // x = x + 3
x++;                 // x = x + 1
++x;                 // Increment first
```

---

## Control Flow

```cpp
// If statement
if (x > 0) {
    std::cout << "Positive\n";
} else if (x < 0) {
    std::cout << "Negative\n";
} else {
    std::cout << "Zero\n";
}

// For loop
for (int i = 0; i < 10; i++) {
    std::cout << i << "\n";
}

// While loop
int count = 0;
while (count < 5) {
    std::cout << count++ << "\n";
}

// Range-based for (C++11)
std::vector<int> nums = {1, 2, 3};
for (int n : nums) {
    std::cout << n << "\n";
}
```

---

## Functions

```cpp
// Function declaration
int add(int a, int b);

// Function definition
int add(int a, int b) {
    return a + b;
}

// Usage
int result = add(5, 3);  // Calls function
```

---

## Arrays

```cpp
// Fixed-size array
int numbers[5] = {1, 2, 3, 4, 5};
int first = numbers[0];  // Access element

// Array size
int size = sizeof(numbers) / sizeof(numbers[0]);

// Modern: std::vector (dynamic)
std::vector<int> vec = {1, 2, 3};
vec.push_back(4);        // Add element
int elem = vec[0];       // Access
```

---

## Input/Output

```cpp
#include <iostream>

// Output
std::cout << "Hello" << std::endl;
std::cout << "Value: " << 42 << "\n";

// Input
int age;
std::cout << "Enter age: ";
std::cin >> age;

// Multiple inputs
int x, y;
std::cin >> x >> y;
```

---

## Namespaces

```cpp
// Using full qualification
std::cout << "Hello\n";
std::vector<int> vec;

// Using declaration (specific)
using std::cout;
cout << "Hello\n";

// Using directive (entire namespace)
using namespace std;
cout << "Hello\n";  // No std:: prefix

// ⚠️ Avoid in headers - pollutes namespace
```

---

## Summary

Basic C++ syntax:
- **Statements** end with `;`
- **Blocks** use `{ }`
- **Case sensitive**
- `main()` is entry point
- `std::` prefix for standard library
- `//` and `/* */` for comments

```cpp
// Template
#include <iostream>

int main() {
    // Your code here
    std::cout << "Program output\n";
    return 0;
}
```