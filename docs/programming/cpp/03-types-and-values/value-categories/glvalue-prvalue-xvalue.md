---
id: glvalue-prvalue-xvalue
title: glvalue, prvalue, xvalue
sidebar_label: Value Categories
sidebar_position: 2
tags: [c++, value-categories, glvalue, prvalue, xvalue, cpp11]
---

# Value Categories (C++11)

C++11 refined value categories into five types: lvalue, prvalue, xvalue, glvalue, and rvalue. Understanding these enables perfect forwarding and move semantics.

:::info Category Tree
```
        expression
       /          \
   glvalue      rvalue
   /    \       /    \
lvalue xvalue prvalue
```
:::

## The Five Categories

### Primary Categories

**lvalue**: Has identity, can't be moved from
- Variables: `int x`
- Dereferenced pointers: `*ptr`
- Functions returning lvalue references: `getRef()`

**prvalue**: No identity, can be moved from (pure rvalue)
- Literals: `42`, `3.14`
- Temporaries: `x + y`, `Point{1,2}`
- Functions returning by value: `getValue()`

**xvalue**: Has identity, can be moved from (expiring value)
- `std::move(x)`
- Cast to rvalue reference: `static_cast<T&&>(x)`
- Temporary materialization

### Composite Categories

**glvalue** (generalized lvalue): Has identity
- Includes: lvalue + xvalue

**rvalue**: Can be moved from
- Includes: prvalue + xvalue

---

## Detailed Breakdown

### lvalue (Locator Value)

Has persistent address, cannot be moved from:

```cpp showLineNumbers 
int x = 42;              // x is lvalue
int* p = &x;             // Can take address
x = 10;                  // Can appear on left of assignment

int& getRef() { static int x = 0; return x; }
getRef() = 100;          // Function returning lvalue ref → lvalue

std::string s = "hello";
s.append(" world");      // s is lvalue, can call non-const methods
```

**Properties**:
- Can take address
- May or may not be modifiable (depends on const)
- Cannot bind to rvalue reference

### prvalue (Pure Rvalue)

Temporary value with no address:

```cpp showLineNumbers 
42                       // Literal prvalue
x + y                    // Arithmetic result
x && y                   // Logical result
std::string("temp")      // Temporary object

int getValue() { return 42; }
getValue()               // Function returning by value → prvalue

// Cannot take address
// int* p = &42;         // ❌ Error
// int* p = &getValue(); // ❌ Error
```

**Properties**:
- No address
- Always movable
- Binds to rvalue reference or const lvalue reference

### xvalue (Expiring Value)

Has identity but about to expire (can be moved from):

```cpp showLineNumbers 
std::vector<int> v = {1, 2, 3};

std::move(v)             // xvalue (cast to rvalue)
static_cast<std::vector<int>&&>(v)  // xvalue

// Function returning rvalue reference
std::vector<int>&& getRRef() { 
    static std::vector<int> v; 
    return std::move(v); 
}
getRRef()                // xvalue
```

**Properties**:
- Has identity (can be named)
- Can be moved from
- Result of std::move
- Binds to rvalue reference

---

## Examples by Category

### lvalues

```cpp showLineNumbers 
int x;                   // Variable
int arr[10];             
arr[0]                   // Array element
*ptr                     // Dereferenced pointer
++x                      // Pre-increment
s.append("!")            // Non-const member function
"string literal"         // String literal (special case)
```

### prvalues

```cpp showLineNumbers 
42                       // Literals
x + y                    // Arithmetic
x++                      // Post-increment (returns copy)
this                     // this pointer
lambda expression        // []{} 
Point{1, 2}             // Temporary object
```

### xvalues

```cpp showLineNumbers 
std::move(x)             // Cast to rvalue
std::move(vec[0])        // Element moved
static_cast<T&&>(x)      // Explicit cast
a.m (where a is rvalue and m is non-static member)
```

---

## Reference Binding

```cpp showLineNumbers 
int x = 42;

// lvalue references
int& lr1 = x;                    // ✅ lvalue → lvalue ref
// int& lr2 = 42;                // ❌ prvalue → lvalue ref
// int& lr3 = std::move(x);      // ❌ xvalue → lvalue ref

// const lvalue references (bind to everything)
const int& clr1 = x;             // ✅ lvalue
const int& clr2 = 42;            // ✅ prvalue
const int& clr3 = std::move(x);  // ✅ xvalue

// rvalue references
// int&& rr1 = x;                // ❌ lvalue → rvalue ref
int&& rr2 = 42;                  // ✅ prvalue → rvalue ref
int&& rr3 = std::move(x);        // ✅ xvalue → rvalue ref
```

| Category | Has Identity | Movable | Binds to T& | Binds to T&& | Binds to const T& |
|----------|--------------|---------|-------------|--------------|-------------------|
| lvalue | ✅ Yes | ❌ No | ✅ Yes | ❌ No | ✅ Yes |
| prvalue | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| xvalue | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |

---

## Temporary Materialization

prvalues convert to xvalues when binding to references:

```cpp showLineNumbers 
struct Point { int x, y; };

Point getPoint() { return {1, 2}; }  // Returns prvalue

// Temporary materialization
const Point& ref = getPoint();  
// getPoint() prvalue → xvalue when binding
// Lifetime extended to ref's scope
```

---

## Perfect Forwarding

Value categories enable perfect forwarding:

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {
    // arg is always lvalue (has name)
    // But T encodes original value category
    
    // std::forward preserves value category
    actual_function(std::forward<T>(arg));
}

int x = 10;
wrapper(x);           // T = int&, forwards as lvalue
wrapper(10);          // T = int, forwards as rvalue
wrapper(std::move(x)); // T = int, forwards as rvalue
```

---

## Move Semantics

Understanding categories is key to move semantics:

```cpp showLineNumbers 
class Buffer {
    int* data;
public:
    // Copy constructor (lvalue source)
    Buffer(const Buffer& other);
    
    // Move constructor (rvalue source: prvalue or xvalue)
    Buffer(Buffer&& other) noexcept;
};

Buffer b1 = getBuffer();      // Move (prvalue)
Buffer b2 = std::move(b1);    // Move (xvalue)
Buffer b3 = b1;               // Copy (lvalue)
```

---

## decltype and Value Categories

`decltype` reveals value category:

```cpp showLineNumbers 
int x = 42;

decltype(x)       // int (lvalue variable → type)
decltype((x))     // int& (lvalue expression)
decltype(42)      // int (prvalue)
decltype(std::move(x))  // int&& (xvalue)

// Rule: decltype(expression)
// - lvalue → T&
// - xvalue → T&&
// - prvalue → T
```

---

## Practical Impact

### Overload Resolution

```cpp showLineNumbers 
void process(const std::string& s) {
    std::cout << "lvalue\n";
}

void process(std::string&& s) {
    std::cout << "rvalue\n";
}

std::string s = "hello";
process(s);                // lvalue
process("hello");          // prvalue → rvalue overload
process(std::move(s));     // xvalue → rvalue overload
```

### Return Value Optimization

```cpp showLineNumbers 
std::string make() {
    return std::string("hello");  // prvalue
    // Compiler can elide copy/move (RVO)
}

std::string s = make();  // No copy, no move with RVO
```

---

## Summary

**Five categories**:
- **lvalue**: Has address, can't move (variables)
- **prvalue**: Pure temporary, can move (literals, function returns)
- **xvalue**: Expiring value, can move (std::move result)
- **glvalue**: lvalue or xvalue (has identity)
- **rvalue**: prvalue or xvalue (can move from)

**Key distinctions**:
```cpp showLineNumbers 
int x = 42;

x                    // lvalue (has identity, not movable)
42                   // prvalue (no identity, movable)
std::move(x)         // xvalue (has identity, movable)

x + 1                // prvalue (temporary)
std::move(x).size()  // xvalue (member of xvalue)
```

**Binding rules**:
- `T&` binds to lvalues only
- `T&&` binds to rvalues (prvalue + xvalue)
- `const T&` binds to everything

Understanding value categories is essential for:
- ✅ Move semantics
- ✅ Perfect forwarding
- ✅ Overload resolution
- ✅ Template metaprogramming