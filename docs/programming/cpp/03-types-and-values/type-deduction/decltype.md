---
id: decltype
title: decltype
sidebar_label: decltype
sidebar_position: 2
tags: [c++, decltype, type-deduction, cpp11]
---

# decltype

`decltype` deduces the type of an expression, preserving references and const qualifiers exactly.

:::info Difference from auto
`auto` uses template deduction (drops ref/const), `decltype` preserves exact type including references.
:::

## Basic Usage

```cpp
int x = 42;
decltype(x) y = x;  // int (same type as x)

const int& ref = x;
decltype(ref) r = x;  // const int& (preserves reference and const)

auto a = ref;         // int (drops reference and const)
decltype(ref) b = ref;  // const int& (keeps everything)
```

---

## decltype Rules

### Named Variables

```cpp
int x = 42;
const int cx = x;
int& rx = x;

decltype(x)   // int
decltype(cx)  // const int
decltype(rx)  // int&
```

**Rule 1**: For named variables, `decltype` gives the declared type exactly.

### Expressions

```cpp
int x = 42;

decltype((x))    // int& (parentheses make it expression)
decltype(x + 0)  // int (expression result)
decltype(x++)    // int (post-increment returns value)
decltype(++x)    // int& (pre-increment returns reference)
```

**Rule 2**: For expressions (including parentheses around names), `decltype` gives value category:
- **lvalue expression** → `T&`
- **xvalue expression** → `T&&`
- **prvalue expression** → `T`

---

## Practical Uses

### Variable Type Matching

```cpp
std::vector<int> vec;

// Declare same type as existing variable
decltype(vec) vec2;  // std::vector<int>
decltype(vec.size()) size;  // size_t

// Useful when type is complex
std::map<std::string, std::vector<int>> map;
decltype(map) map2;  // Exact same type
```

### Return Type Deduction

```cpp
template<typename Container>
auto getElement(Container& c, int index) -> decltype(c[index]) {
    return c[index];
}

// c[index] might return reference
std::vector<int> vec = {1, 2, 3};
auto& elem = getElement(vec, 0);  // Returns int&
```

### Perfect Return Type

```cpp
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

auto result = add(5, 3.14);  // double (decltype(int + double))
```

---

## decltype vs auto

```cpp
const int x = 42;
const int& ref = x;

// auto drops const and reference
auto a = ref;       // int

// decltype preserves everything
decltype(ref) b = ref;  // const int&

// auto with modifiers
auto& c = ref;      // const int&
const auto d = ref; // const int

// decltype for exact type
decltype(ref) e = ref;  // const int& (exact match)
```

---

## Common Patterns

### Type of Member

```cpp
struct Point {
    double x, y;
};

Point p;
decltype(p.x) value;  // double

decltype(Point::x) coord;  // double (static member access)
```

### Container Element Type

```cpp
std::vector<int> vec;
decltype(vec[0]) elem;  // int& (vector::operator[] returns reference)

std::vector<bool> bvec;
decltype(bvec[0]) proxy;  // std::vector<bool>::reference (proxy)
```

### Function Return Type

```cpp
int func();

decltype(func()) x;  // int (return type of func)
decltype(func) f;    // int() (function type)
decltype(&func) fp;  // int(*)() (function pointer type)
```

---

## Parentheses Matter!

```cpp
int x = 42;

decltype(x)   // int (name)
decltype((x)) // int& (expression - lvalue)

// Why? (x) is an lvalue expression referring to x
// decltype of lvalue expression → reference
```

:::warning Critical Difference
`decltype(name)` ≠ `decltype((name))`  
Parentheses change name to expression!
:::

---

## Return Type Deduction (C++11 vs C++14)

### C++11: Trailing Return Type

```cpp
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}
```

Must use trailing return type because `a` and `b` not in scope before parameter list.

### C++14: auto Return

```cpp
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;  // auto deduction (uses template rules)
}

// Returns int for add(5, 10), drops reference
std::vector<int> vec;
auto getFirst() {
    return vec[0];  // Returns int (copy), not int&
}
```

---

## Combining auto and decltype

```cpp
std::vector<int> vec = {1, 2, 3};

// auto drops reference
auto x = vec[0];  // int (copy)

// decltype preserves reference
decltype(vec[0]) y = vec[0];  // int&

// decltype(auto) - best of both worlds (C++14)
decltype(auto) z = vec[0];  // int& (preserves return type)
```

---

## Use Cases

### Generic Code

```cpp
template<typename Container>
void process(Container& c) {
    // Get exact type of element
    decltype(c[0]) elem = c[0];
    
    // Modify if it's a reference
    elem = 42;  // Modifies container if elem is reference
}
```

### Type Traits

```cpp
template<typename T>
struct remove_reference {
    using type = T;
};

template<typename T>
struct remove_reference<T&> {
    using type = T;
};

int x;
using Type = typename remove_reference<decltype(x)>::type;  // int
```

---

## Summary

**decltype**:
- Preserves exact type including references and const
- `decltype(name)` → declared type
- `decltype(expression)` → value category type
- `decltype((name))` → reference (expression)

**Comparison**:
```cpp
const int& ref = x;

auto a = ref;           // int (template deduction)
decltype(ref) b = ref;  // const int& (exact type)
decltype(auto) c = ref; // const int& (C++14)
```

**Use when**:
- Need exact type preservation
- Template return type forwarding
- Type of complex expressions
- Generic code requiring perfect forwarding

```cpp
// Common idioms
decltype(expr) var;           // Match expression type
decltype(auto) var = expr;    // Deduce with preservation (C++14)
auto func() -> decltype(expr) // Trailing return type
```