---
id: noexcept
title: noexcept Specifier
sidebar_label: noexcept
sidebar_position: 6
tags: [c++, noexcept, exceptions, optimization, cpp11]
---

# noexcept Specifier

`noexcept` specifies that a function won't throw exceptions, enabling optimizations and stronger guarantees.

:::info Performance & Safety
`noexcept` allows compilers to optimize (no exception handling overhead) and enables move operations in standard containers.
:::

## Basic Usage

```cpp
// Function that doesn't throw
void safe_function() noexcept {
    // No exceptions thrown
}

// Function that might throw (default)
void risky_function() {
    throw std::runtime_error("Error");
}

// Conditional noexcept (C++11)
void conditional() noexcept(sizeof(int) == 4) {
    // noexcept if condition is true
}
```

---

## noexcept vs throw()

```cpp
// Old style (C++98, deprecated)
void old_style() throw() {
    // Exception specification (avoid)
}

// Modern style (C++11+)
void modern_style() noexcept {
    // Preferred
}
```

**Difference**: `throw()` calls `std::unexpected`, `noexcept` calls `std::terminate`. Both crash if exception escapes, but `noexcept` is more efficient.

---

## What Happens if Exception Thrown?

```cpp
void marked_noexcept() noexcept {
    throw std::runtime_error("Oops");  // ⚠️ Compiles but dangerous!
}

int main() {
    try {
        marked_noexcept();
    } catch (...) {
        // Never reached!
    }
}
// std::terminate called → program crashes
```

**Rule**: If exception escapes `noexcept` function, `std::terminate` is called immediately.

---

## Conditional noexcept

```cpp
// noexcept depends on expression
template<typename T>
void swap(T& a, T& b) noexcept(std::is_nothrow_move_constructible_v<T>) {
    T temp(std::move(a));
    a = std::move(b);
    b = std::move(temp);
}

// Simple types
int x = 1, y = 2;
swap(x, y);  // noexcept(true)

// Complex types
std::string s1 = "hello", s2 = "world";
swap(s1, s2);  // noexcept(true) - string's move doesn't throw

// Custom type that might throw
struct MightThrow {
    MightThrow(MightThrow&&) { /* might throw */ }
};
MightThrow a, b;
swap(a, b);  // noexcept(false)
```

---

## Testing for noexcept

```cpp
void func1() noexcept { }
void func2() { }

// Check if function is noexcept
static_assert(noexcept(func1()), "func1 is noexcept");
static_assert(!noexcept(func2()), "func2 can throw");

// Check expressions
int x = 0;
static_assert(noexcept(x + 1), "Addition doesn't throw");
static_assert(!noexcept(std::string("hello")), "String ctor might throw");
```

---

## Move Semantics and noexcept

Standard containers use move only if it's `noexcept`:

```cpp
class Widget {
public:
    // Without noexcept
    Widget(Widget&& other) {
        // std::vector uses COPY when growing
    }
    
    // With noexcept
    Widget(Widget&& other) noexcept {
        // std::vector uses MOVE when growing (efficient!)
    }
};

std::vector<Widget> vec;
vec.push_back(Widget{});  // Triggers potential reallocation
```

**Why**: If move throws during vector reallocation, strong exception guarantee is broken. So vector copies instead (inefficient but safe).

:::warning Critical for Performance
Mark move constructors/assignments `noexcept` or standard containers won't use them!
:::

---

## Destructors

Destructors are implicitly `noexcept`:

```cpp
class Widget {
public:
    ~Widget() {  // Implicitly noexcept
        // Throwing here is dangerous
    }
};

// Explicitly not noexcept (rare, dangerous)
class Bad {
public:
    ~Bad() noexcept(false) {
        throw std::runtime_error("Bad idea");
    }
};
```

**Rule**: Never throw from destructors. If exception during stack unwinding, `std::terminate` is called.

---

## Functions That Should Be noexcept

```cpp
class Widget {
public:
    // Move operations (critical!)
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    
    // Destructor (implicit)
    ~Widget() noexcept;
    
    // Swap
    void swap(Widget& other) noexcept;
    
    // Simple getters
    int getValue() const noexcept { return value; }
    
private:
    int value;
};
```

---

## Propagating noexcept

```cpp
template<typename T>
class Wrapper {
    T value;
public:
    // Propagate noexcept from T's constructor
    Wrapper(T v) noexcept(std::is_nothrow_move_constructible_v<T>)
        : value(std::move(v)) {}
    
    // Propagate from T's swap
    void swap(Wrapper& other) noexcept(noexcept(std::swap(value, other.value))) {
        std::swap(value, other.value);
    }
};
```

---

## Performance Impact

### Without noexcept

```cpp
void process() {
    // Compiler must generate exception handling code
    // - Setup exception tables
    // - Add cleanup code
    // - Maintain exception state
}
```

### With noexcept

```cpp
void process() noexcept {
    // Compiler can optimize away exception handling
    // - Smaller code
    // - Faster execution
    // - Better inlining opportunities
}
```

**Typical improvement**: 10-20% faster in hot paths, smaller binary.

---

## Wide Contracts vs Narrow Contracts

### Wide Contract (noexcept friendly)

```cpp
// Accepts any input, never throws
int abs(int x) noexcept {
    return x < 0 ? -x : x;
}
```

### Narrow Contract (throws on invalid input)

```cpp
// Preconditions: size > 0
int front(std::vector<int>& vec) {
    if (vec.empty()) {
        throw std::out_of_range("Empty vector");
    }
    return vec.front();
}
// Can't mark noexcept - might throw
```

**Guideline**: Wide contracts (no preconditions) can be `noexcept`, narrow contracts (preconditions) usually can't.

---

## Real-World Example

```cpp
class String {
    char* data;
    size_t len;
    
public:
    // Move constructor - must be noexcept for container optimization
    String(String&& other) noexcept
        : data(other.data), len(other.len) {
        other.data = nullptr;
        other.len = 0;
    }
    
    // Move assignment - also noexcept
    String& operator=(String&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            len = other.len;
            other.data = nullptr;
            other.len = 0;
        }
        return *this;
    }
    
    // Destructor - implicitly noexcept
    ~String() noexcept {
        delete[] data;
    }
    
    // Swap - should be noexcept
    void swap(String& other) noexcept {
        std::swap(data, other.data);
        std::swap(len, other.len);
    }
};
```

---

## Common Mistakes

### Over-promising

```cpp
void process(const std::string& s) noexcept {
    std::string copy = s;  // ❌ Might throw bad_alloc!
}
// If throws, std::terminate is called
```

### Under-promising

```cpp
// Could be noexcept but isn't marked
int add(int a, int b) {
    return a + b;  // Never throws
}
// Missed optimization opportunity
```

---

## Checking Standard Library

```cpp
#include <type_traits>

// Check if type's operations are noexcept
static_assert(std::is_nothrow_move_constructible_v<std::string>);
static_assert(std::is_nothrow_move_assignable_v<std::vector<int>>);

// Check specific operations
std::vector<int> vec;
static_assert(noexcept(vec.size()));     // true
static_assert(!noexcept(vec.at(0)));     // false (throws on out of range)
static_assert(noexcept(vec[0]));         // true (no bounds checking)
```

---

## Best Practices

:::success DO
- Mark move constructors/assignments `noexcept`
- Mark destructors `noexcept` (implicit, but can be explicit)
- Mark swap functions `noexcept`
- Mark simple getters `noexcept`
- Use conditional `noexcept` for templates
  :::

:::danger DON'T
- Mark functions `noexcept` if they might throw
- Throw from destructors
- Throw from `noexcept` functions (causes terminate)
- Forget `noexcept` on move operations
  :::

---

## Summary

**noexcept**:
- Promises no exceptions
- Enables optimizations
- Required for efficient moves
- Crashes program if violated (std::terminate)

**Key functions to mark**:
```cpp
class T {
    T(T&&) noexcept;              // Move constructor
    T& operator=(T&&) noexcept;   // Move assignment
    ~T() noexcept;                 // Destructor (implicit)
    void swap(T&) noexcept;       // Swap
};
```

**Benefits**:
- ✅ Better performance (10-20% in hot paths)
- ✅ Smaller binary size
- ✅ Standard containers use move operations
- ✅ Stronger exception safety guarantees

**Cost**: Must ensure function truly doesn't throw, or program terminates.