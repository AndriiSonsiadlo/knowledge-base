---
id: decltype-auto
title: decltype(auto)
sidebar_label: decltype(auto)
sidebar_position: 3
tags: [c++, decltype-auto, type-deduction, cpp14]
---

# decltype(auto)

`decltype(auto)` (C++14) combines `auto` convenience with `decltype` precision - deduces type while preserving references and const.

:::info Best of Both Worlds
`auto` is convenient but drops references. `decltype` preserves them but verbose. `decltype(auto)` gives both.
:::

## The Problem

```cpp
std::vector<int> vec = {1, 2, 3};

// auto drops reference
auto x = vec[0];  // int (copy)
x = 42;           // Doesn't modify vec

// decltype preserves reference but verbose
decltype(vec[0]) y = vec[0];  // int&
y = 42;  // Modifies vec[0]

// decltype(auto) - concise AND preserves reference
decltype(auto) z = vec[0];  // int&
z = 42;  // Modifies vec[0]
```

---

## Basic Usage

```cpp
int x = 42;
const int cx = x;
int& rx = x;

// auto deduction (drops reference/const)
auto a = rx;            // int

// decltype deduction (preserves)
decltype(rx) b = rx;    // int&

// decltype(auto) - auto syntax, decltype rules
decltype(auto) c = rx;  // int&
```

**Rule**: `decltype(auto)` uses `decltype` rules on the initializer expression.

---

## Perfect Return Type Forwarding

### Before C++14

```cpp
// C++11: Need to duplicate expression
template<typename Container, typename Index>
auto getElement(Container& c, Index i) -> decltype(c[i]) {
    return c[i];  // Expression duplicated
}
```

### C++14: decltype(auto)

```cpp
// Clean and DRY (Don't Repeat Yourself)
template<typename Container, typename Index>
decltype(auto) getElement(Container& c, Index i) {
    return c[i];  // Preserves reference if c[i] returns reference
}

std::vector<int> vec = {1, 2, 3};
decltype(auto) elem = getElement(vec, 0);  // int&
elem = 42;  // Modifies vec[0]
```

---

## Variable Declarations

```cpp
int x = 42;
int& ref = x;

// Deduction from initializer
decltype(auto) a = x;    // int (x is lvalue)
decltype(auto) b = ref;  // int& (ref is reference)
decltype(auto) c = (x);  // int& (parentheses → expression)
```

:::danger Parentheses Matter
```cpp
int x = 42;

decltype(auto) a = x;    // int
decltype(auto) b = (x);  // int& (expression!)

b = 10;  // Modifies x
```

`(x)` is an expression, making `b` a reference to `x`.
:::

---

## Return Type Deduction

### Value vs Reference

```cpp
std::string getString() {
    std::string s = "hello";
    return s;  // Returns by value
}

decltype(auto) func1() {
    return getString();  // std::string (by value)
}

decltype(auto) func2() {
    std::string s = "hello";
    return s;  // std::string (by value)
}

decltype(auto) func3() {
    std::string s = "hello";
    return (s);  // std::string& (expression!) ⚠️ Dangling!
}
```

:::warning Dangling References
```cpp
decltype(auto) bad() {
    int x = 42;
    return (x);  // ❌ Returns int& to local variable!
}  // x destroyed, reference dangles
```
:::

---

## Comparison Table

| Syntax | Type Deduced | Preserves Ref | Preserves Const |
|--------|--------------|---------------|-----------------|
| `auto x = expr` | Template rules | ❌ No | ❌ No (top-level) |
| `auto& x = expr` | Template + & | ✅ Yes | ✅ Yes |
| `decltype(expr) x` | Exact type | ✅ Yes | ✅ Yes |
| `decltype(auto) x = expr` | decltype rules | ✅ Yes | ✅ Yes |

---

## Practical Examples

### Generic Wrapper

```cpp
template<typename Func, typename... Args>
decltype(auto) callWrapper(Func&& f, Args&&... args) {
    log("Calling function");
    return std::forward<Func>(f)(std::forward<Args>(args)...);
    // Preserves exact return type of f (value, ref, or rvalue ref)
}

int getValue() { return 42; }
int& getRef() { static int x = 42; return x; }

auto val = callWrapper(getValue);  // int
decltype(auto) ref = callWrapper(getRef);  // int&
```

### Container Access

```cpp
template<typename Container>
class Wrapper {
    Container c;
public:
    decltype(auto) operator[](size_t i) {
        return c[i];  // Preserves Container's operator[] return type
    }
};

Wrapper<std::vector<int>> w;
decltype(auto) elem = w[0];  // int& (matches vector's behavior)
```

### Lazy Evaluation

```cpp
template<typename Func>
class Lazy {
    Func func;
public:
    Lazy(Func f) : func(f) {}
    
    decltype(auto) get() {
        return func();  // Preserves func's return type
    }
};

auto lazy = Lazy([]() -> int& { 
    static int x = 42; 
    return x; 
});

decltype(auto) value = lazy.get();  // int&
```

---

## When to Use

### Use decltype(auto) When

```cpp
// ✅ Perfect forwarding return types
template<typename T>
decltype(auto) forward_call(T&& arg) {
    return some_function(std::forward<T>(arg));
}

// ✅ Preserving reference in generic code
template<typename Container>
decltype(auto) getFirst(Container& c) {
    return c[0];  // Reference if Container returns reference
}

// ✅ Avoiding type repetition
decltype(auto) result = complicated_expression();
```

### Use auto When

```cpp
// ✅ Want a copy
auto copy = vec[0];  // int (copy)

// ✅ Don't want reference
auto value = get_reference();  // Copy even if returns reference

// ✅ Type is obvious
auto count = vec.size();  // size_t
```

---

## Common Pitfalls

### Unintended Reference

```cpp
decltype(auto) getLocal() {
    int x = 42;
    return (x);  // ❌ Returns int& to local!
}
```

### Expression vs Variable

```cpp
int x = 42;

decltype(auto) a = x;    // int (variable)
decltype(auto) b = (x);  // int& (expression)

a = 10;  // OK: modifies a
b = 10;  // OK: modifies x through reference
```

### Const Propagation

```cpp
const std::vector<int> cvec = {1, 2, 3};

decltype(auto) elem = cvec[0];  // const int& (preserves const)
elem = 42;  // ❌ Error: const
```

---

## Summary

`decltype(auto)`:
- **C++14 feature**
- Uses `decltype` deduction rules
- Preserves references and const
- Useful for perfect forwarding
- **Beware parentheses** - create expressions!

**Decision guide**:
```cpp
auto x = expr;              // Want copy, drop ref/const
auto& x = expr;             // Want reference
decltype(expr) x;           // Exact type, but verbose
decltype(auto) x = expr;    // Exact type, concise
```

**Common use**:
```cpp
// Generic return type forwarding
template<typename F, typename... Args>
decltype(auto) call(F&& f, Args&&... args) {
    return std::forward<F>(f)(std::forward<Args>(args)...);
}
```

The key benefit: write `auto` simplicity while getting `decltype` precision.