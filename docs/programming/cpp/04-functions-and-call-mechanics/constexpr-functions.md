---
id: constexpr-functions
title: constexpr Functions
sidebar_label: constexpr
sidebar_position: 5
tags: [c++, constexpr, compile-time, optimization, cpp11]
---

# constexpr Functions

`constexpr` indicates values or functions can be evaluated at compile-time, enabling compile-time computation and optimization.

:::info Compile-Time Execution
`constexpr` functions execute during compilation when possible, producing constants that can be used in array sizes, template arguments, and other constant expressions.
:::

## Basic Usage

```cpp
// constexpr variable (must be compile-time constant)
constexpr int x = 42;
constexpr double pi = 3.14159;

// Use in compile-time contexts
int arr[x];  // ✅ OK: x is compile-time constant
```

---

## constexpr Functions

```cpp
// C++11 constexpr function (single return statement)
constexpr int square(int x) {
    return x * x;
}

// Compile-time evaluation
constexpr int result = square(5);  // Computed at compile-time
int arr[result];  // ✅ OK: result is compile-time constant

// Can also run at runtime
int n = 10;
int runtime_result = square(n);  // Computed at runtime
```

**Key property**: `constexpr` functions can execute at compile-time OR runtime depending on context.

---

## C++11 vs C++14 vs C++20

### C++11 Restrictions

```cpp
// C++11: Very limited
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);  // Only recursion
}

// ❌ Not allowed in C++11:
// - Local variables
// - Multiple statements
// - Loops
```

### C++14 Relaxed Rules

```cpp
// C++14: Much more flexible
constexpr int factorial(int n) {
    int result = 1;  // Local variables OK
    for (int i = 2; i <= n; ++i) {  // Loops OK
        result *= i;
    }
    return result;
}

constexpr int fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}
```

### C++20 Enhanced

```cpp
// C++20: Even more features
constexpr std::string getMessage() {
    std::string s = "Hello";  // Dynamic allocation OK!
    s += " World";
    return s;
}

constexpr std::vector<int> getNumbers() {
    std::vector<int> v;
    v.push_back(1);
    v.push_back(2);
    return v;  // Vector destroyed properly at compile-time
}
```

---

## constexpr vs const

```cpp
// const: Runtime or compile-time constant
const int x = 10;           // Compile-time
const int y = getValue();   // Runtime (depends on getValue)

// constexpr: MUST be compile-time constant
constexpr int a = 10;              // ✅ OK
constexpr int b = getValue();      // ❌ Error if getValue not constexpr

// In practice
const int size1 = 10;
int arr1[size1];  // ✅ OK (const works here)

const int size2 = getValue();
int arr2[size2];  // ❌ Error: not compile-time constant

constexpr int size3 = 10;
int arr3[size3];  // ✅ OK (guaranteed compile-time)
```

**Rule**: `constexpr` is always compile-time; `const` might be runtime.

---

## constexpr Constructors

```cpp
class Point {
    int x, y;
public:
    constexpr Point(int x_, int y_) : x(x_), y(y_) {}
    
    constexpr int getX() const { return x; }
    constexpr int getY() const { return y; }
    
    constexpr int distanceSquared() const {
        return x * x + y * y;
    }
};

// Compile-time object
constexpr Point p(3, 4);
constexpr int dist = p.distanceSquared();  // 25 at compile-time

// Use in constant expressions
int arr[dist];  // ✅ OK: array of 25 elements
```

---

## Compile-Time vs Runtime

```cpp
constexpr int compute(int x) {
    return x * x + 1;
}

// Compile-time
constexpr int result1 = compute(5);  // Evaluated at compile-time
static_assert(result1 == 26);        // Can verify at compile-time

// Runtime
int n;
std::cin >> n;
int result2 = compute(n);  // Evaluated at runtime (n not known)
```

**Compiler decides**: If all arguments are compile-time constants, function executes at compile-time.

---

## Requirements for constexpr Functions

```cpp
// ✅ OK
constexpr int good(int x) {
    return x * 2;  // Simple computation
}

// ❌ Not OK
constexpr int bad1(int x) {
    static int counter = 0;  // ❌ Static local variables
    return x + counter++;
}

constexpr int bad2() {
    return rand();  // ❌ rand() not constexpr
}

// C++11 ❌, C++14+ ✅
constexpr int maybe(int x) {
    int result = 0;  // Local variable
    for (int i = 0; i < x; ++i) {
        result += i;
    }
    return result;
}
```

---

## constexpr if (C++17)

Compile-time conditional compilation:

```cpp
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        return value * 2;  // Integer path
    } else if constexpr (std::is_floating_point_v<T>) {
        return value * 1.5;  // Float path
    } else {
        return value;  // Other types
    }
}

auto x = process(10);      // Returns 20 (int path compiled)
auto y = process(3.14);    // Returns 4.71 (float path compiled)
// Other paths not compiled for these types!
```

**Difference from regular if**: Only the selected branch is compiled.

---

## Practical Uses

### Array Sizes

```cpp
constexpr int buffer_size = 1024;
char buffer[buffer_size];  // Compile-time array size
```

### Template Arguments

```cpp
constexpr int size = compute_size();
std::array<int, size> arr;  // Template argument must be compile-time
```

### Lookup Tables

```cpp
constexpr int pow2(int n) {
    return 1 << n;
}

constexpr std::array<int, 10> powers = {
    pow2(0), pow2(1), pow2(2), pow2(3), pow2(4),
    pow2(5), pow2(6), pow2(7), pow2(8), pow2(9)
};  // Computed at compile-time
```

### Compile-Time Validation

```cpp
constexpr bool is_valid_port(int port) {
    return port > 0 && port <= 65535;
}

static_assert(is_valid_port(8080), "Port must be valid");
// static_assert(is_valid_port(70000), "Invalid"); // ❌ Compile error
```

---

## consteval (C++20)

Forces compile-time evaluation:

```cpp
consteval int must_be_compile_time(int x) {
    return x * x;
}

constexpr int result1 = must_be_compile_time(5);  // ✅ OK: compile-time

int n = 5;
int result2 = must_be_compile_time(n);  // ❌ Error: runtime argument
```

**Difference**: `constexpr` can be runtime, `consteval` must be compile-time.

---

## Performance Benefits

### Code Bloat Reduction

```cpp
// Without constexpr
int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int size = factorial(5);  // Computed at runtime
char buffer[120];  // Must hardcode result

// With constexpr
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int size = factorial(5);  // Computed at compile-time
char buffer[size];  // size = 120, no runtime computation
```

### Optimization Opportunities

```cpp
constexpr int compute_hash(const char* str) {
    int hash = 0;
    while (*str) {
        hash = hash * 31 + *str++;
    }
    return hash;
}

// Compile-time hash
switch (compute_hash(input)) {
    case compute_hash("command1"):  // Compare at compile-time
        handle_command1();
        break;
    case compute_hash("command2"):
        handle_command2();
        break;
}
```

---

## Common Pitfalls

### Undefined Behavior

```cpp
constexpr int divide(int a, int b) {
    return a / b;  // ❌ UB if b is 0
}

// constexpr int x = divide(10, 0);  // ❌ Compile error (UB detected)
```

### Non-constexpr Dependencies

```cpp
int global = 42;

constexpr int bad() {
    return global;  // ❌ Error: global not constexpr
}

constexpr int global_constexpr = 42;

constexpr int good() {
    return global_constexpr;  // ✅ OK
}
```

### Pointer Conversions

```cpp
constexpr int x = 42;

constexpr int* ptr = &x;  // ❌ Error: address not compile-time constant
                          // (except in constexpr context)

constexpr const int* ptr2 = &x;  // ❌ Still problematic
```

---

## Best Practices

:::success DO
- Use `constexpr` for compile-time computations
- Mark constructors `constexpr` when possible
- Use `constexpr if` for type-dependent code
- Prefer `constexpr` over macros
  :::

:::danger DON'T
- Mark functions `constexpr` if they can't be evaluated at compile-time
- Use `constexpr` for runtime-only operations
- Assume `constexpr` always means compile-time (can be runtime)
  :::

---

## Summary

**constexpr**:
- Enables compile-time evaluation
- Can also run at runtime
- C++14 added loops, local variables
- C++20 added dynamic allocation

**vs const**:
- `const`: Runtime or compile-time
- `constexpr`: Compile-time capable

**vs consteval (C++20)**:
- `constexpr`: Can be runtime
- `consteval`: Must be compile-time

```cpp
// Common pattern
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

constexpr int size = factorial(5);  // 120 at compile-time
int arr[size];  // No runtime computation
```

**Use when**: Need compile-time constants, optimization, or type-safe alternatives to macros.