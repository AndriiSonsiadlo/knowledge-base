---
id: reference-collapsing
title: Reference Collapsing Rules
sidebar_label: Reference Collapsing
sidebar_position: 3
tags: [c++, reference-collapsing, forwarding, templates]
---

# Reference Collapsing Rules

When template type deduction creates "reference to reference", C++ applies collapsing rules. This enables perfect forwarding.

:::info The Rule
`& &` → `&`  
`& &&` → `&`  
`&& &` → `&`  
`&& &&` → `&&`

**Only `&& &&` → `&&`, everything else → `&`**
:::

## The Problem

References to references aren't valid C++:

```cpp showLineNumbers 
int x = 42;
int& r = x;

// int& & rr = r;  // ❌ Error: reference to reference
```

But templates can create them:

```cpp showLineNumbers 
template<typename T>
void func(T&& param);

int x = 42;
func(x);  // T deduced as int&
          // param type becomes int& && (reference to reference!)
```

C++ applies **reference collapsing** to resolve this.

---

## Collapsing Rules

```cpp showLineNumbers 
typedef int&  LRef;
typedef int&& RRef;

// Combinations
LRef &    // int& & → int&
LRef &&   // int& && → int&
RRef &    // int&& & → int&
RRef &&   // int&& && → int&&
```
:::warning Collapsing Rule
**Only double `rvalue` reference stays `rvalue` reference!**
:::

---

## Universal References

Template parameter `T&&` is a **universal reference** (forwarding reference):

```cpp showLineNumbers 
template<typename T>
void func(T&& param);

int x = 42;
const int cx = x;

func(x);         // T = int&, param = int& && → int&
func(cx);        // T = const int&, param = const int& && → const int&
func(42);        // T = int, param = int&& (no collapsing)
func(std::move(x)); // T = int, param = int&&
```

**Universal reference** = `rvalue` reference in deduced context (`template` or `auto`)

---

## Type Deduction with Forwarding

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {
    // arg has type T&&
    // But after deduction and collapsing:
    
    // If passed lvalue int: T = int&
    //   arg type: int& && → int&
    
    // If passed rvalue int: T = int
    //   arg type: int&&
}

int x = 10;
wrapper(x);      // T = int&, arg = int&
wrapper(10);     // T = int, arg = int&&
```

---

## Perfect Forwarding

std::forward uses reference collapsing:

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {
    // Forward preserving value category
    target(std::forward<T>(arg));
}

// std::forward implementation (simplified)
template<typename T>
T&& forward(std::remove_reference_t<T>& arg) {
    return static_cast<T&&>(arg);
}

int x = 10;
wrapper(x);   // T = int&
              // forward<int&>(arg)
              // Returns: int& && → int& (lvalue)

wrapper(10);  // T = int
              // forward<int>(arg)
              // Returns: int&& (rvalue)
```

---

## Practical Examples

### Example 1: Type Alias

```cpp showLineNumbers 
template<typename T>
struct AddLRef {
    using type = T&;
};

// Specialization not needed - collapsing handles it!
AddLRef<int>::type x;     // int&
AddLRef<int&>::type y;    // int& & → int&
AddLRef<int&&>::type z;   // int&& & → int&
```

### Example 2: Function Template

```cpp showLineNumbers 
template<typename T>
void process(T&& arg) {
    using RRefType = T&&;
    
    // Collapses based on T
    RRefType r1 = std::forward<T>(arg);
}

int x = 42;
process(x);        // T = int&
                   // RRefType = int& && → int&
                   
process(10);       // T = int
                   // RRefType = int&&
```

### Example 3: Factory Function

```cpp showLineNumbers 
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

std::string s = "hello";

// Each arg preserves value category via collapsing
auto p1 = make_unique<std::string>(s);           // Copy
auto p2 = make_unique<std::string>(std::move(s)); // Move
auto p3 = make_unique<std::string>("literal");   // Construct from rvalue
```

---

## decltype and Collapsing

decltype doesn't cause collapsing (preserves exact type):

```cpp showLineNumbers 
int x = 42;
decltype(x)& r1 = x;    // int& (x is int)
decltype((x))& r2 = x;  // int& & → int& (collapsing)

int& ref = x;
decltype(ref)& r3 = x;  // int& & → int& (collapsing)
decltype(ref)&& r4 = 42; // int& && → int& (can't bind to rvalue!)
```

---

## Auto and Collapsing

auto also participates in reference collapsing:

```cpp showLineNumbers 
int x = 42;

auto&& r1 = x;           // int& (x is lvalue, int& && → int&)
auto&& r2 = 42;          // int&& (42 is rvalue)
auto&& r3 = std::move(x); // int&& (xvalue)

// Using auto&&
for (auto&& elem : container) {
    // Binds to both lvalues and rvalues
    // elem is reference (no copy)
}
```

---

## Why It Matters

### Without Collapsing

```cpp showLineNumbers 
template<typename T>
void broken(T&& arg) {
    // Hypothetically without collapsing:
    
    int x;
    broken(x);  // T = int&
                // arg type: int& && 
                // ❌ Error: invalid type!
}
```

### With Collapsing

```cpp showLineNumbers 
template<typename T>
void working(T&& arg) {
    // With collapsing:
    
    int x;
    working(x);  // T = int&
                 // arg type: int& && → int&
                 // ✅ Valid lvalue reference
}
```

---

## Common Patterns

### Forwarding Wrapper

```cpp showLineNumbers 
template<typename Func, typename... Args>
auto invoke_and_log(Func&& f, Args&&... args) 
    -> decltype(std::forward<Func>(f)(std::forward<Args>(args)...))
{
    log("Calling function");
    return std::forward<Func>(f)(std::forward<Args>(args)...);
}

// Each parameter perfectly forwarded via collapsing
```

### Move-If-Rvalue

```cpp showLineNumbers 
template<typename T>
decltype(auto) move_if_rvalue(T&& arg) {
    return std::forward<T>(arg);
    // If arg was lvalue: returns lvalue ref (no move)
    // If arg was rvalue: returns rvalue ref (enables move)
}
```

---

## Summary

**Reference collapsing rules**:
```
& &   → &
& &&  → &
&& &  → &
&& && → &&
```

**Key points**:
- Enables universal references (`T&&` in templates)
- Makes perfect forwarding possible
- Applied during template instantiation
- Only `&& &&` remains `&&`, rest become `&`

**Practical use**:
```cpp showLineNumbers 
template<typename T>
void forward_call(T&& arg) {
    // T&& is universal reference
    // Collapsing preserves value category
    func(std::forward<T>(arg));
}

int x = 10;
forward_call(x);      // Forwards as lvalue (T = int&, collapses)
forward_call(10);     // Forwards as rvalue (T = int, no collapse)
```

Reference collapsing is the mechanism that makes C++11's perfect forwarding work seamlessly.