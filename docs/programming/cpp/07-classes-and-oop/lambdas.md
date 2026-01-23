---
id: lambdas
title: Lambda Expressions
sidebar_label: Lambdas
sidebar_position: 8
tags: [c++, lambdas, closures, cpp11, functional]
---

# Lambda Expressions

Lambdas (C++11) are anonymous functions that can capture variables from surrounding scope, enabling functional programming patterns and convenient callbacks.

:::info Syntactic Sugar
Lambdas are compiler-generated function objects (functors). The lambda `[](){}` creates an unnamed class with `operator()`.
:::

## Basic Syntax

```cpp showLineNumbers 
// Minimal lambda
auto lambda = []() { 
    std::cout << "Hello\n"; 
};

lambda();  // Call it

// With parameters and return
auto add = [](int a, int b) { 
    return a + b; 
};

int result = add(5, 3);  // 8
```

**Parts**:
```cpp showLineNumbers 
[capture](parameters) -> return_type { body }
 ^^^^^^^  ^^^^^^^^^^    ^^^^^^^^^^^   ^^^^
 capture  params        return type   code
 clause                 (optional)
```

---

## Captures

### No Capture

```cpp showLineNumbers 
auto lambda = []() { return 42; };
// Cannot access outer variables
```

### Capture by Value

```cpp showLineNumbers 
int x = 10;
auto lambda = [x]() { 
    return x * 2;  // Copy of x
};

x = 20;
std::cout << lambda();  // 20 (uses old value of x)
```

### Capture by Reference

```cpp showLineNumbers 
int x = 10;
auto lambda = [&x]() { 
    x *= 2;  // Modifies original x
};

lambda();
std::cout << x;  // 20
```

### Multiple Captures

```cpp showLineNumbers 
int x = 1, y = 2;

[x, y]()      { }  // Capture x and y by value
[&x, &y]()    { }  // Capture x and y by reference
[x, &y]()     { }  // x by value, y by reference
[=]()         { }  // Capture all by value
[&]()         { }  // Capture all by reference
[=, &x]()     { }  // All by value except x by reference
[&, x]()      { }  // All by reference except x by value
```

### Init Capture (C++14)

```cpp showLineNumbers 
int x = 10;

// Create new variable in capture
auto lambda = [y = x * 2]() { 
    return y;  // y = 20
};

// Move capture
auto ptr = std::make_unique<int>(42);
auto lambda2 = [p = std::move(ptr)]() {
    return *p;  // Owns the unique_ptr
};
```

---

## Parameters and Return Types

### Auto Parameters (C++14)

```cpp showLineNumbers 
// Generic lambda
auto print = [](auto x) { 
    std::cout << x << "\n"; 
};

print(42);       // Works with int
print(3.14);     // Works with double
print("hello");  // Works with const char*
```

### Explicit Return Type

```cpp showLineNumbers 
// Return type deduced
auto add = [](int a, int b) { return a + b; };  // Returns int

// Explicit return type
auto divide = [](int a, int b) -> double { 
    return static_cast<double>(a) / b; 
};
```

---

## mutable Keyword

By default, captured-by-value variables are const:

```cpp showLineNumbers 
int x = 10;

auto lambda1 = [x]() { 
    // x = 20;  // ❌ Error: x is const
    return x;
};

auto lambda2 = [x]() mutable { 
    x = 20;  // ✅ OK: modifies copy
    return x;
};

lambda2();
std::cout << x;  // 10 (original unchanged)
```

---

## Common Use Cases

### STL Algorithms

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5, 6};

// Count even numbers
int count = std::count_if(vec.begin(), vec.end(), 
                         [](int n) { return n % 2 == 0; });

// Transform
std::transform(vec.begin(), vec.end(), vec.begin(),
              [](int n) { return n * 2; });

// Custom sort
std::sort(vec.begin(), vec.end(),
         [](int a, int b) { return a > b; });  // Descending
```

### Callbacks

```cpp showLineNumbers 
void process(std::function<void()> callback) {
    // Do work...
    callback();
}

int result = 0;
process([&result]() {
    result = 42;
});
```

### RAII Guards

```cpp showLineNumbers 
{
    auto guard = [cleanup = some_resource]() {
        // Cleanup happens when guard destroyed
    };
    
    // ... use resource ...
    
}  // Guard destroyed, cleanup happens
```

---

## Lambda as Function Object

Lambdas are functors - classes with `operator()`:

```cpp showLineNumbers 
// Lambda
auto lambda = [x = 10](int y) { return x + y; };

// Equivalent class
class Lambda {
    int x;
public:
    Lambda(int x_) : x(x_) {}
    int operator()(int y) const { return x + y; }
};
Lambda lambda2(10);
```

---

## Recursive Lambdas

Requires `std::function` or `auto` with explicit type:

```cpp showLineNumbers 
// Using std::function
std::function<int(int)> factorial = [&factorial](int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
};

// C++23: Explicit object parameter (deducing this)
auto factorial = [](this auto&& self, int n) {
    return n <= 1 ? 1 : n * self(n - 1);
};
```

---

## Immediately Invoked Lambda

```cpp showLineNumbers 
// IIFE (Immediately Invoked Function Expression)
int value = []() {
    int temp = expensive_computation();
    return temp * 2;
}();  // Called immediately

// Useful for const initialization
const auto data = [&]() {
    std::vector<int> v;
    // Complex initialization
    return v;
}();
```

---

## Template Lambdas (C++20)

```cpp showLineNumbers 
// Template lambda
auto lambda = []<typename T>(T value) {
    return value * 2;
};

auto x = lambda(5);      // int
auto y = lambda(3.14);   // double
```

---

## Captures and Object Lifetime

```cpp showLineNumbers 
// ❌ Dangling reference
std::function<int()> makeFunc() {
    int x = 42;
    return [&x]() { return x; };  // ❌ x destroyed!
}

// ✅ Capture by value
std::function<int()> makeFunc() {
    int x = 42;
    return [x]() { return x; };  // ✅ Copy of x
}

// ✅ Init capture with move
std::function<int()> makeFunc() {
    auto ptr = std::make_unique<int>(42);
    return [p = std::move(ptr)]() { return *p; };
}
```

---

## Performance Considerations

```cpp showLineNumbers 
// Stack-allocated (fast)
auto lambda = [](int x) { return x * 2; };

// std::function (slower, heap allocation possible)
std::function<int(int)> func = [](int x) { return x * 2; };

// Template parameter (fastest, inlined)
template<typename Func>
void process(Func f) {
    f(42);
}

process([](int x) { std::cout << x; });  // No overhead
```

**Guideline**: Use `auto` for lambdas, `std::function` only when type erasure needed.

---

## Best Practices

:::success DO
- Use `auto` for lambda variables
- Prefer capture by value for small types
- Use init capture for move-only types
- Mark non-modifying lambdas `const` (default)
  :::

:::danger DON'T
- Capture by reference if lambda outlives scope
- Use `[=]` when you mean specific captures
- Forget `mutable` when modifying captured values
- Over-use `std::function` (performance cost)
  :::

---

## Summary

**Lambda syntax**:
```cpp showLineNumbers 
[captures](params) -> return_type { body }
```

**Captures**:
- `[x]` - Value
- `[&x]` - Reference
- `[=]` - All by value
- `[&]` - All by reference
- `[y = x]` - Init capture (C++14)

**Common patterns**:
```cpp showLineNumbers 
// STL algorithm
std::sort(vec.begin(), vec.end(), [](int a, int b) { return a > b; });

// Callback
button.onClick([this]() { handleClick(); });

// IIFE
const auto x = []() { return compute(); }();

// Generic lambda (C++14)
auto print = [](const auto& x) { std::cout << x; };
```

**Use when**:
- Inline callbacks
- STL algorithms
- Short-lived function objects
- Functional programming patterns

Lambdas make C++ more expressive, enabling clean functional-style code while maintaining zero-overhead abstraction principles.