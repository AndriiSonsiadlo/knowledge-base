---
id: inline-functions
title: Inline Functions
sidebar_label: Inline
sidebar_position: 4
tags: [c++, functions, inline, optimization, performance]
---

# Inline Functions

`inline` suggests the compiler replace function calls with function body, eliminating call overhead. Modern compilers decide automatically.

:::info Suggestion, Not Command
`inline` is a hint. Compilers inline automatically based on optimization settings, often ignoring the keyword.
:::

## Basic Usage

```cpp
// Without inline
int square(int x) {
    return x * x;
}

int result = square(5);  // Function call overhead

// With inline
inline int square(int x) {
    return x * x;
}

int result = square(5);  // May be replaced with: 5 * 5
```

---

## How Inlining Works

### Normal Function Call

```cpp
int add(int a, int b) {
    return a + b;
}

int x = add(5, 3);

// Assembly (simplified):
// push 3
// push 5
// call add
// add esp, 8
// mov x, eax
```

### Inlined Function

```cpp
inline int add(int a, int b) {
    return a + b;
}

int x = add(5, 3);

// Assembly (simplified):
// mov eax, 5
// add eax, 3
// mov x, eax
```

No call overhead: no stack manipulation, no jump, faster execution.

---

## When to Inline

### Good Candidates

```cpp
// Small, frequently called functions
inline int max(int a, int b) {
    return a > b ? a : b;
}

// Getters/setters
class Widget {
    int value;
public:
    inline int getValue() const { return value; }
    inline void setValue(int v) { value = v; }
};

// Simple calculations
inline double square(double x) { return x * x; }
```

### Poor Candidates

```cpp
// Large functions (defeats purpose)
inline void processComplexData(/*...*/) {
    // 100 lines of code
    // Inlining duplicates code everywhere
}

// Recursive functions (compiler won't inline)
inline int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

// Virtual functions (can't inline through base pointer)
class Base {
public:
    virtual inline void func() {}  // inline ineffective
};
```

---

## Definition Placement

Inline functions must be defined in headers (visible to all translation units):

```cpp
// widget.h
#pragma once

class Widget {
public:
    // Implicitly inline (defined in class)
    int getValue() const { return value; }
    
    // Explicitly inline
    inline void setValue(int v);
    
private:
    int value;
};

// Still in header
inline void Widget::setValue(int v) {
    value = v;
}
```

:::warning One Definition Rule
Inline functions can be defined in multiple translation units (identical definitions required).
:::

---

## Implicit Inline

### Member Functions Defined in Class

```cpp
class Widget {
public:
    // Implicitly inline
    int getValue() const {
        return value;
    }
    
    // Also implicitly inline
    void setValue(int v) { value = v; }
    
private:
    int value;
};
```

### constexpr Functions

```cpp
// constexpr is implicitly inline
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}
```

---

## Modern Compiler Behavior

### Automatic Inlining

```cpp
// Even without 'inline', compilers inline with optimization
int square(int x) {
    return x * x;
}

// With -O2 or -O3, this is inlined automatically
```

### Force Inline (Compiler-Specific)

```cpp
// GCC/Clang
__attribute__((always_inline))
inline int add(int a, int b) {
    return a + b;
}

// MSVC
__forceinline int add(int a, int b) {
    return a + b;
}
```

### Prevent Inline

```cpp
// GCC/Clang
__attribute__((noinline))
void debug_func() {
    // Always appears in stack traces
}

// MSVC
__declspec(noinline) void debug_func() {
    // ...
}
```

---

## Performance Impact

### Benefits

```cpp
// Eliminates call overhead
for (int i = 0; i < 1000000; i++) {
    result += square(i);  // No function call per iteration
}

// Enables further optimization
inline int compute(int x) {
    return x * 2 + 1;
}

int y = compute(5);  // Compiler sees: 5 * 2 + 1
                     // Can optimize to: 11 (constant folding)
```

### Drawbacks

```cpp
// Code bloat
inline void largeFunction() {
    // 50 lines of code
}

// Called 100 times = 100 copies of 50 lines
// Increases binary size, hurts instruction cache
```

---

## Inline Variables (C++17)

```cpp
// header.h
inline int global_counter = 0;  // OK in header (C++17)

inline const std::string default_name = "Widget";
```

Before C++17, needed workarounds:

```cpp
// C++14 workaround
extern const std::string default_name;

// In one .cpp file:
const std::string default_name = "Widget";
```

---

## Templates and Inline

Template functions are implicitly inline:

```cpp
// Implicitly inline (defined in header)
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

// Can explicitly mark inline (redundant)
template<typename T>
inline T min(T a, T b) {
    return a < b ? a : b;
}
```

---

## Link-Time Optimization (LTO)

```bash
# Modern alternative: LTO inlines across files
g++ -flto -O3 file1.cpp file2.cpp -o app

# Compiler can inline functions in file1.cpp called from file2.cpp
# Without needing 'inline' keyword
```

---

## Best Practices

:::success DO
- Let compiler decide (use -O2/-O3)
- Mark small, frequently-called functions inline
- Define inline functions in headers
- Use for getters/setters
  :::

:::danger DON'T
- Inline large functions
- Inline recursive functions
- Inline virtual functions (ineffective)
- Rely on inline for performance (profile first)
  :::

---

## Debugging

Inlined functions don't appear in stack traces:

```cpp
inline void helper() {
    throw std::runtime_error("Error");
}

void process() {
    helper();  // Stack trace won't show helper()
}
```

**Solution**: Compile with `-O0` or use `noinline` attribute for debugging.

---

## Summary

**inline keyword**:
- Suggests function body replacement
- Eliminates call overhead
- Must be defined in header
- Compilers decide automatically with optimization

**Implicit inline**:
- Functions defined in class body
- constexpr functions
- Template functions

**Modern practice**:
```cpp
// Let compiler decide
int square(int x) { return x * x; }

// Compile with optimization
g++ -O3 program.cpp

// Compiler inlines automatically
```

**Use inline when**:
- Multiple definitions needed (header-only)
- Defining globals in headers (C++17)
- Small, performance-critical functions

**Key point**: Modern compilers are better at inlining decisions than humans. Use optimization flags (`-O2`, `-O3`) and profile performance rather than manually adding `inline` everywhere.