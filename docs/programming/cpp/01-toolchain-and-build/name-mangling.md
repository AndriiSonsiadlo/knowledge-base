---
id: name-mangling
title: Name Mangling in C++
sidebar_label: Name Mangling
sidebar_position: 8
tags: [c++, name-mangling, abi, linking, symbols]
---

# Name Mangling in C++

Name mangling (name decoration) encodes C++ function signatures into unique symbol names for the linker. This enables function overloading and namespaces while maintaining linkage compatibility.

:::info Why Mangle?
C++ supports function overloading (multiple functions with same name), but linkers only understand unique symbol names. Mangling creates unique names by encoding type information.
:::

## The Problem

```cpp showLineNumbers 
// C++ allows this
void print(int x);
void print(double x);
void print(const char* x);

// But linker needs unique names for each!
// Solution: Mangle names to include parameter types
```

Without mangling, the linker would see three symbols all called `print` and report duplicate definitions.

---

## Mangled vs Unmangled

```cpp showLineNumbers 
void calculate(int a, double b);
```

**Unmangled (source code)**: `calculate`  
**Mangled (symbol table)**: `_Z9calculateid`

The mangled name encodes:
- `_Z` = C++ mangling prefix
- `9` = name length (9 characters)
- `calculate` = function name
- `i` = int parameter
- `d` = double parameter

---

## Viewing Mangled Names

```bash
# Compile
g++ -c example.cpp -o example.o

# View mangled symbols
nm example.o
# Output:
# 0000000000000000 T _Z9calculateid

# Demangle symbols
nm -C example.o
# Output:
# 0000000000000000 T calculate(int, double)

# Demangle specific name
c++filt _Z9calculateid
# Output: calculate(int, double)
```

The `-C` flag or `c++filt` tool converts mangled names back to readable form.

---

## Mangling Rules

Different compilers use different schemes, but most follow Itanium C++ ABI:

### Basic Types

```cpp showLineNumbers 
void func(int);           // _Z4funci
void func(char);          // _Z4funcc
void func(bool);          // _Z4funcb
void func(float);         // _Z4funcf
void func(double);        // _Z4funcd
void func(void*);         // _Z4funcPv
```

**Type codes**:
- `i` = int
- `c` = char
- `b` = bool
- `f` = float
- `d` = double
- `v` = void
- `P` = pointer
- `R` = reference

### Pointers and References

```cpp showLineNumbers 
void func(int*);          // _Z4funcPi   (Pointer to int)
void func(int&);          // _Z4funcRi   (Reference to int)
void func(int**);         // _Z4funcPPi  (Pointer to pointer to int)
void func(const int*);    // _Z4funcPKi  (Pointer to const int, K=const)
```

### Classes and Namespaces

```cpp showLineNumbers 
namespace math {
    class Vector {
    public:
        void normalize();
    };
}

// Mangled: _ZN4math6Vector9normalizeEv
// Breakdown:
// _Z = prefix
// N...E = nested name
// 4math = namespace "math" (4 chars)
// 6Vector = class "Vector" (6 chars)
// 9normalize = method "normalize" (9 chars)
// v = void return type
```

### Function Overloading

```cpp showLineNumbers 
void print(int x);           // _Z5printi
void print(double x);        // _Z5printd
void print(int x, int y);    // _Z5printii
```

Each overload gets a unique mangled name encoding its parameter types.

### Templates

```cpp showLineNumbers 
template<typename T>
void sort(T* data, int size);

sort<int>(arr, 10);          // _Z4sortIiEvPT_i
sort<double>(arr2, 10);      // _Z4sortIdEvPT_i

// IiE = template parameter int
// IdE = template parameter double
```

---

## C Linkage (No Mangling)

C doesn't support overloading, so C functions don't get mangled:

```c
// C code
void c_function(int x);  // Symbol: c_function (unmangled)
```

### extern "C"

Prevents name mangling for C++ code, enabling C/C++ interoperability:

```cpp showLineNumbers 
// C++ code
extern "C" void c_style_function(int x);
// Symbol: c_style_function (unmangled, C-compatible)

extern "C" {
    void func1(int x);
    void func2(double y);
    // Both unmangled
}
```

**Common use case**: Creating C-compatible libraries from C++:

```cpp showLineNumbers 
// library.h
#ifdef __cplusplus
extern "C" {
#endif

void api_function(int x);

#ifdef __cplusplus
}
#endif
```

This header works in both C and C++ code.

---

## Platform Differences

### GCC/Clang (Itanium ABI)

```cpp showLineNumbers 
void func(int, double);
// _Z4funcid
```

### MSVC (Windows)

```cpp showLineNumbers 
void func(int, double);
// ?func@@YAXHN@Z
```

MSVC uses a different mangling scheme with `?` prefix and `@@` separators.

**Consequence**: Object files compiled with GCC can't link with MSVC-compiled code due to different mangling.

---

## ABI Compatibility

Name mangling is part of the ABI (Application Binary Interface). Breaking changes cause link errors:

```cpp showLineNumbers 
// Version 1
void process(int x);         // _Z7processi

// Version 2 (changed signature)
void process(long x);        // _Z7processl  (different mangled name!)
```

Programs compiled against v1 looking for `_Z7processi` won't find it in v2. This breaks binary compatibility.

---

## Practical Examples

### Linking Errors

```cpp showLineNumbers 
// header.h
void calculate(int a, int b);

// implementation.cpp
void calculate(int a, double b) {  // Wrong signature!
    // ...
}

// main.cpp
#include "header.h"
calculate(5, 10);  // ❌ Undefined reference to _Z9calculateii
                   // Implementation provides _Z9calculateid
```

The mangled names don't match because parameter types differ.

### Finding Functions

```bash
# Find all functions in library
nm -C libmath.so | grep " T "

# Find specific overload
nm libmath.so | grep calculate
# _Z9calculateii  (int, int)
# _Z9calculateid  (int, double)
# _Z9calculatedd  (double, double)

# Search for class methods
nm -C libwidget.so | grep "Widget::"
```

---

## Member Functions

```cpp showLineNumbers 
class Widget {
    int value;
public:
    void setValue(int v);
    int getValue() const;
    static void reset();
};

// Mangled names:
// _ZN6Widget8setValueEi       - setValue
// _ZNK6Widget8getValueEv      - getValue (K = const)
// _ZN6Widget5resetEv          - reset (static, no 'this')
```

Member functions encode:
- Class name
- Function name
- Parameter types
- `const` qualification
- `static` vs non-static

---

## Constructor and Destructor

```cpp showLineNumbers 
class Widget {
public:
    Widget();                    // Constructor
    ~Widget();                   // Destructor
};

// Mangled:
// _ZN6WidgetC1Ev              - Constructor (C1)
// _ZN6WidgetD1Ev              - Destructor (D1)
```

Special mangling for constructors (C1, C2) and destructors (D1, D2) to handle different variants (complete object, base object).

---

## Troubleshooting

### Undefined Reference

```bash
# Error:
undefined reference to `_Z4funcPKc'

# Demangle to see what's missing
c++filt _Z4funcPKc
# Output: func(char const*)

# Solution: Implement func(const char*) or link correct library
```

### Symbol Not Found

```bash
# Check if symbol exists
nm -C library.a | grep "function_name"

# If found with different signature:
# Signature mismatch - recompile or fix declaration
```

---

## Demangling in Code

```cpp showLineNumbers 
#include <cxxabi.h>
#include <memory>

std::string demangle(const char* name) {
    int status;
    std::unique_ptr<char, void(*)(void*)> result(
        abi::__cxa_demangle(name, nullptr, nullptr, &status),
        std::free
    );
    return (status == 0) ? result.get() : name;
}

// Usage
typeid(std::vector<int>).name();  // Returns mangled name
demangle(typeid(std::vector<int>).name());  // Human-readable
```

---

## Best Practices

:::success DO
- Use `extern "C"` for C compatibility
- Use `nm -C` to debug link errors
- Maintain ABI compatibility in library updates
- Document exported symbols
  :::

:::danger DON'T
- Rely on mangled names directly in code
- Change function signatures in stable ABIs
- Mix compilers with different mangling schemes
- Assume mangling scheme across platforms
  :::

---

## Summary

Name mangling:
- **Encodes** function signatures into unique symbol names
- **Enables** function overloading and namespaces
- **Differs** between compilers (GCC vs MSVC)
- **Can be disabled** with `extern "C"` for C compatibility

**Key tools**:
```bash
nm -C file.o        # View demangled symbols
c++filt name        # Demangle specific name
objdump -t file.o   # Symbol table
```

**Encoding scheme** (Itanium ABI):
```
_Z<length><name><param_types>
_ZN<namespace><class><method>E<params>
```

Name mangling is transparent most of the time, but understanding it helps debug linking issues and maintain ABI compatibility across library versions.