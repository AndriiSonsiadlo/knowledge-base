---
id: fold-expressions
title: Fold Expressions (C++17)
sidebar_label: Fold Expressions
sidebar_position: 4
tags: [c++, templates, fold-expressions, cpp17]
---

# Fold Expressions (C++17)

Fold expressions provide a concise way to apply operators to variadic template parameter packs. They eliminate the need for recursive template patterns.

:::info Simplifying Variadic Templates
Before C++17: Complex recursion  
C++17: `(args + ...)` - simple and readable!
:::

## Basic Fold Expressions

```cpp showLineNumbers 
// Sum all arguments
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // Fold with +
}

sum(1, 2, 3, 4, 5);  // 15

// Multiply all arguments
template<typename... Args>
auto product(Args... args) {
    return (args * ...);  // Fold with *
}

product(2, 3, 4);  // 24
```

**Syntax:** `(pack op ...)`

## Four Types of Folds

**Unary right fold:** `(pack op ...)`
```cpp showLineNumbers 
(args + ...)  // ((arg1 + arg2) + arg3) + ...
```

**Unary left fold:** `(... op pack)`
```cpp showLineNumbers 
(... + args)  // ... + (arg3 + (arg2 + arg1))
```

**Binary right fold:** `(pack op ... op init)`
```cpp showLineNumbers 
(args + ... + 0)  // ((arg1 + arg2) + arg3) + 0
```

**Binary left fold:** `(init op ... op pack)`
```cpp showLineNumbers 
(0 + ... + args)  // 0 + (arg1 + (arg2 + arg3))
```

## Common Operations

**Logical AND:**
```cpp showLineNumbers 
template<typename... Args>
bool all(Args... args) {
    return (args && ...);  // All must be true
}

all(true, true, true);   // true
all(true, false, true);  // false
```

**Logical OR:**
```cpp showLineNumbers 
template<typename... Args>
bool any(Args... args) {
    return (args || ...);  // At least one true
}

any(false, false, true);  // true
any(false, false, false); // false
```

**Comma operator (execute all):**
```cpp showLineNumbers 
template<typename... Args>
void print(Args... args) {
    ((std::cout << args << " "), ...);
    std::cout << "\n";
}

print(1, "hello", 3.14);  // "1 hello 3.14"
```

## With Initial Value

```cpp showLineNumbers 
// Sum with initial value
template<typename... Args>
auto sumFrom(int start, Args... args) {
    return (start + ... + args);  // start + arg1 + arg2 + ...
}

sumFrom(100, 1, 2, 3);  // 106

// Concatenate strings
template<typename... Args>
std::string concat(Args... args) {
    return (std::string("") + ... + args);
}

concat("Hello", " ", "World");  // "Hello World"
```

## Function Calls

```cpp showLineNumbers 
// Call function for each argument
template<typename... Args>
void processAll(Args... args) {
    (process(args), ...);
}

// Push all to vector
template<typename... Args>
void addAll(std::vector<int>& vec, Args... args) {
    (vec.push_back(args), ...);
}

std::vector<int> v;
addAll(v, 1, 2, 3, 4, 5);  // v = {1, 2, 3, 4, 5}
```

## Comparison Chains

```cpp showLineNumbers 
// Check if all equal
template<typename T, typename... Args>
bool allEqual(T first, Args... args) {
    return ((first == args) && ...);
}

allEqual(5, 5, 5, 5);   // true
allEqual(5, 5, 6, 5);   // false

// Check if in ascending order
template<typename... Args>
bool isAscending(Args... args) {
    return ((args < args...) && ...);  // Won't work directly!
}
```

## Combining Folds

```cpp showLineNumbers 
// Average
template<typename... Args>
double average(Args... args) {
    return (args + ...) / sizeof...(args);
}

average(10, 20, 30);  // 20.0

// All within range
template<typename... Args>
bool allInRange(int min, int max, Args... args) {
    return ((args >= min && args <= max) && ...);
}

allInRange(0, 100, 50, 75, 25);   // true
allInRange(0, 100, 50, 150, 25);  // false
```

## With Member Functions

```cpp showLineNumbers 
struct Point {
    int x, y;
    void print() const {
        std::cout << "(" << x << "," << y << ") ";
    }
};

template<typename... Args>
void printAll(const Args&... args) {
    (args.print(), ...);
}

Point p1{1, 2}, p2{3, 4}, p3{5, 6};
printAll(p1, p2, p3);  // "(1,2) (3,4) (5,6)"
```

## Building Tuples

```cpp showLineNumbers 
template<typename... Args>
auto makeTuple(Args... args) {
    return std::tuple<Args...>(args...);
}

// Unpacking with fold
template<typename Tuple, size_t... Is>
void printTuple(const Tuple& t, std::index_sequence<Is...>) {
    ((std::cout << std::get<Is>(t) << " "), ...);
}

auto t = makeTuple(1, "hello", 3.14);
printTuple(t, std::make_index_sequence<3>{});  // "1 hello 3.14"
```

## Comparison: Before and After

**Before C++17 (recursive):**
```cpp showLineNumbers 
// Base case
void print() {}

// Recursive case
template<typename T, typename... Args>
void print(T first, Args... rest) {
    std::cout << first << " ";
    print(rest...);
}
```

**C++17 (fold expression):**
```cpp showLineNumbers 
template<typename... Args>
void print(Args... args) {
    ((std::cout << args << " "), ...);
}
```

Much simpler and clearer!

## Operator Support

Fold expressions work with these operators:
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Bitwise: `&`, `|`, `^`, `<<`, `>>`
- Logical: `&&`, `||`
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Assignment: `=`, `+=`, `-=`, etc.
- Comma: `,`
- Member access: `.*`, `->*`

:::success Fold Expression Patterns

**Sum** = `(args + ...)`  
**Product** = `(args * ...)`  
**All true** = `(args && ...)`  
**Any true** = `(args || ...)`  
**Call function** = `(func(args), ...)`  
**Print all** = `((cout << args << " "), ...)`  
**With initial** = `(init + ... + args)`  
**Pack size** = `sizeof...(args)` (not a fold, but related)
:::
