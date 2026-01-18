---
id: fundamental-types
title: Fundamental Types
sidebar_label: Fundamental Types
sidebar_position: 1
tags: [c++, types, primitives, int, float, char, bool]
---

# Fundamental Types

C++ provides built-in fundamental types for integers, floating-point numbers, characters, and booleans.

:::info Type System
C++ is statically typed - every variable has a type known at compile-time, enabling type checking and optimization.
:::

## Integer Types

### Basic Integer Types

```cpp
// Standard integers
char        // At least 8 bits (usually 1 byte)
short       // At least 16 bits
int         // At least 16 bits (usually 32 bits)
long        // At least 32 bits
long long   // At least 64 bits (C++11)

// Signed (default)
signed int x = -42;
int y = -42;         // Same as signed int

// Unsigned
unsigned int count = 42;
unsigned char byte = 255;
```

### Size Guarantees

```cpp
#include <iostream>
#include <climits>

int main() {
    std::cout << "char: " << sizeof(char) << " bytes\n";      // 1
    std::cout << "short: " << sizeof(short) << " bytes\n";    // ≥2
    std::cout << "int: " << sizeof(int) << " bytes\n";        // ≥2 (usually 4)
    std::cout << "long: " << sizeof(long) << " bytes\n";      // ≥4
    std::cout << "long long: " << sizeof(long long) << "\n";  // ≥8
}
```

### Range Examples

| Type | Typical Size | Range (signed) |
|------|--------------|----------------|
| `char` | 1 byte | -128 to 127 |
| `short` | 2 bytes | -32,768 to 32,767 |
| `int` | 4 bytes | -2,147,483,648 to 2,147,483,647 |
| `long` | 4/8 bytes | Platform-dependent |
| `long long` | 8 bytes | -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 |

Unsigned types: 0 to (2^bits - 1)

### Fixed-Width Types (C++11)

```cpp
#include <cstdint>

int8_t   x;   // Exactly 8 bits
int16_t  y;   // Exactly 16 bits
int32_t  z;   // Exactly 32 bits
int64_t  w;   // Exactly 64 bits

uint8_t  a;   // Unsigned 8 bits
uint32_t b;   // Unsigned 32 bits

// Use these for platform-independent code
```

---

## Floating-Point Types

```cpp
float       // Single precision (usually 32 bits, ~7 decimal digits)
double      // Double precision (usually 64 bits, ~15 decimal digits)
long double // Extended precision (usually 80 or 128 bits)

float f = 3.14f;           // f suffix
double d = 3.14159265359;  // Default for literals
long double ld = 3.14L;    // L suffix
```

### Precision

```cpp
#include <iostream>
#include <iomanip>

float f = 1.0f / 3.0f;
double d = 1.0 / 3.0;

std::cout << std::setprecision(20);
std::cout << "float: " << f << "\n";    // ~0.333333343267
std::cout << "double: " << d << "\n";   // ~0.333333333333333
```

---

## Character Types

```cpp
char         // At least 8 bits, typically ASCII/UTF-8
wchar_t      // Wide character (16 or 32 bits)
char16_t     // UTF-16 (C++11)
char32_t     // UTF-32 (C++11)
char8_t      // UTF-8 (C++20)

char c = 'A';           // Single character
char newline = '\n';    // Escape sequence
wchar_t wide = L'中';   // Wide character
```

**char is an integer type**:
```cpp
char c = 65;    // Same as 'A' (ASCII)
c++;            // Now 66 ('B')
int x = c;      // Implicit conversion
```

---

## Boolean Type

```cpp
bool flag = true;
bool result = false;

// Converts to int: true=1, false=0
int x = true;   // x = 1

// Non-zero converts to true
bool b = 42;    // b = true
bool b2 = 0;    // b2 = false
```

---

## void Type

Special type indicating "no value":

```cpp
void func() {
    // No return value
}

void* ptr;  // Generic pointer (can point to any type)
```

---

## Type Sizes

```cpp
#include <iostream>

int main() {
    std::cout << "bool: " << sizeof(bool) << "\n";
    std::cout << "char: " << sizeof(char) << "\n";
    std::cout << "int: " << sizeof(int) << "\n";
    std::cout << "float: " << sizeof(float) << "\n";
    std::cout << "double: " << sizeof(double) << "\n";
    std::cout << "pointer: " << sizeof(void*) << "\n";
}

// Typical output (64-bit system):
// bool: 1
// char: 1
// int: 4
// float: 4
// double: 8
// pointer: 8
```

**Guarantee**: `1 == sizeof(char) ≤ sizeof(short) ≤ sizeof(int) ≤ sizeof(long) ≤ sizeof(long long)`

---

## Type Limits

```cpp
#include <limits>
#include <iostream>

int main() {
    std::cout << "int max: " << std::numeric_limits<int>::max() << "\n";
    std::cout << "int min: " << std::numeric_limits<int>::min() << "\n";
    
    std::cout << "double max: " << std::numeric_limits<double>::max() << "\n";
    std::cout << "double min: " << std::numeric_limits<double>::lowest() << "\n";
    
    std::cout << "double digits: " << std::numeric_limits<double>::digits10 << "\n";
}
```

---

## Type Inference (auto)

```cpp
auto x = 5;           // int
auto y = 3.14;        // double
auto z = 'c';         // char
auto b = true;        // bool

auto f = 3.14f;       // float (f suffix)
auto l = 42L;         // long

// Useful for complex types
auto iter = vec.begin();  // std::vector<int>::iterator
```

---

## Type Aliases

```cpp
// typedef (old style)
typedef unsigned long ulong;
typedef int* IntPtr;

// using (C++11, preferred)
using ulong = unsigned long;
using IntPtr = int*;

ulong count = 1000;
IntPtr ptr = &x;
```

---

## Summary

**Integers**: `char`, `short`, `int`, `long`, `long long` (signed/unsigned)  
**Floating-point**: `float`, `double`, `long double`  
**Character**: `char`, `wchar_t`, `char16_t`, `char32_t`  
**Boolean**: `bool`  
**Special**: `void`

**Fixed-width** (C++11): `int8_t`, `int16_t`, `int32_t`, `int64_t`, `uint*_t`

**Key points**:
- Sizes are platform-dependent (use `sizeof`)
- Fixed-width types for portability
- `auto` for type inference
- `char` is an integer type

```cpp
// Typical usage
int count = 0;              // Counters, indices
double price = 19.99;       // Decimals
bool is_valid = true;       // Flags
char letter = 'A';          // Single characters
uint32_t id = 123456;       // Fixed-width
```