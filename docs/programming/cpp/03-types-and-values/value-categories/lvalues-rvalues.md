---
id: lvalues-rvalues
title: Lvalues and Rvalues
sidebar_label: Lvalues & Rvalues
sidebar_position: 1
tags: [c++, lvalue, rvalue, value-categories, move-semantics]
---

# Lvalues and Rvalues

Every C++ expression has a type and a **value category**. Lvalues have persistent storage; rvalues are temporaries.

:::info Simple Rule
**Can you take its address?** → Lvalue  
**Is it temporary?** → Rvalue
:::

## Basic Distinction

```cpp
int x = 42;  // x is lvalue, 42 is rvalue

x = 10;      // ✅ OK: lvalue on left
// 10 = x;   // ❌ Error: rvalue cannot be assigned to

int* ptr = &x;     // ✅ OK: can take address of lvalue
// int* p = &42;   // ❌ Error: cannot take address of rvalue
```

**Lvalue**: Has identity (name/address), persists beyond expression  
**Rvalue**: Temporary value, exists only during expression evaluation

---

## Identifying Lvalues

```cpp
// Variables are lvalues
int x = 5;           // x is lvalue
std::string s;       // s is lvalue

// Array elements are lvalues
int arr[10];
arr[0] = 42;         // arr[0] is lvalue

// Dereferenced pointers are lvalues
int* ptr = &x;
*ptr = 10;           // *ptr is lvalue

// Functions returning references are lvalues
int& getRef() { static int x = 0; return x; }
getRef() = 100;      // ✅ OK: lvalue

// String literals are lvalues (special case)
const char* p = "hello";  // "hello" is lvalue
&"hello";            // ✅ OK: can take address
```

---

## Identifying Rvalues

```cpp
// Literals (except strings)
42                   // rvalue
3.14                 // rvalue
true                 // rvalue

// Temporary results
x + y                // rvalue (temporary sum)
x * 2                // rvalue
x++                  // rvalue (post-increment returns copy)

// Functions returning by value
int getValue() { return 42; }
getValue()           // rvalue (temporary)

// Casts to non-reference types
static_cast<int>(3.14)  // rvalue

// Temporaries
std::string("temp")  // rvalue
Point{1, 2}         // rvalue (temporary object)
```

---

## Lvalue References

Bind to lvalues only:

```cpp
int x = 42;

int& ref = x;        // ✅ OK: lvalue reference to lvalue
// int& r2 = 42;     // ❌ Error: cannot bind to rvalue

// Exception: const lvalue reference binds to anything
const int& cref1 = x;   // ✅ OK: lvalue
const int& cref2 = 42;  // ✅ OK: rvalue (lifetime extended!)
```

:::success const& Magic
`const T&` can bind to both lvalues and rvalues, making it perfect for function parameters.
:::

---

## Rvalue References (C++11)

Bind to rvalues only:

```cpp
int x = 42;

int&& rref1 = 42;        // ✅ OK: rvalue reference to rvalue
int&& rref2 = x + 1;     // ✅ OK: temporary
// int&& rref3 = x;      // ❌ Error: cannot bind to lvalue

// Convert lvalue to rvalue with std::move
int&& rref4 = std::move(x);  // ✅ OK: explicit cast
```

---

## Named Rvalue References are Lvalues!

```cpp
void process(int&& x) {
    // Inside function, x has a name
    // Therefore x is an LVALUE, even though type is rvalue reference!
    
    int& lref = x;       // ✅ OK: x is lvalue
    // int&& rref = x;   // ❌ Error: x is lvalue
    
    int&& rref = std::move(x);  // ✅ OK: explicit cast
}

process(42);  // 42 is rvalue, binds to x
```

**Key insight**: Expression's value category ≠ its type

---

## Reference Binding Rules

```cpp
int x = 10;

// Lvalue reference
int& r1 = x;              // ✅ Lvalue → lvalue ref
// int& r2 = 42;          // ❌ Rvalue → lvalue ref

// Const lvalue reference (universal)
const int& r3 = x;        // ✅ Lvalue → const lvalue ref
const int& r4 = 42;       // ✅ Rvalue → const lvalue ref

// Rvalue reference
// int&& r5 = x;          // ❌ Lvalue → rvalue ref
int&& r6 = 42;            // ✅ Rvalue → rvalue ref
int&& r7 = std::move(x);  // ✅ Lvalue→rvalue (explicit)
```

| Reference Type | Binds to Lvalue | Binds to Rvalue |
|----------------|-----------------|-----------------|
| `T&` | ✅ Yes | ❌ No |
| `const T&` | ✅ Yes | ✅ Yes |
| `T&&` | ❌ No | ✅ Yes |

---

## Lifetime Extension

Binding rvalue to const reference extends its lifetime:

```cpp
std::string getString() { return "temporary"; }

// Destroyed immediately
getString();  

// Lifetime extended to ref's scope
const std::string& ref = getString();
std::cout << ref;  // ✅ OK: still valid

// Also works with rvalue references
std::string&& rref = getString();
std::cout << rref;  // ✅ OK: still valid
```

---

## std::move

Casts lvalue to rvalue (enables move):

```cpp
#include <utility>

std::vector<int> v1 = {1, 2, 3};

// std::move casts v1 to rvalue
std::vector<int> v2 = std::move(v1);

// v1 is now in valid but unspecified state
std::cout << v1.size();  // Likely 0, but not guaranteed
```

:::warning std::move Doesn't Move!
`std::move` only casts to rvalue. Actual moving happens in move constructor/assignment.
:::

---

## Function Overloading

Functions can overload on value category:

```cpp
void process(int& x) {
    std::cout << "Lvalue: " << x << "\n";
}

void process(int&& x) {
    std::cout << "Rvalue: " << x << "\n";
}

int main() {
    int a = 10;
    
    process(a);           // Calls lvalue version
    process(20);          // Calls rvalue version
    process(a + 5);       // Calls rvalue version
    process(std::move(a)); // Calls rvalue version
}
```

---

## Move Semantics

Rvalue references enable efficient resource transfer:

```cpp
class Buffer {
    int* data;
    size_t size;
public:
    // Copy constructor (from lvalue)
    Buffer(const Buffer& other) {
        size = other.size;
        data = new int[size];
        std::copy(other.data, other.data + size, data);
        std::cout << "Copied\n";
    }
    
    // Move constructor (from rvalue)
    Buffer(Buffer&& other) noexcept {
        size = other.size;
        data = other.data;      // Steal pointer
        other.data = nullptr;   // Leave other valid
        other.size = 0;
        std::cout << "Moved\n";
    }
};

Buffer create() { return Buffer(100); }

Buffer b1 = create();  // Move (creates temporary)
Buffer b2 = b1;        // Copy (b1 is lvalue)
Buffer b3 = std::move(b1);  // Move (explicit)
```

---

## Pre-increment vs Post-increment

```cpp
int x = 5;

++x;  // Pre-increment: modifies x, returns lvalue (reference to x)
x++;  // Post-increment: modifies x, returns rvalue (old value copy)

int& r1 = ++x;  // ✅ OK: lvalue
// int& r2 = x++;  // ❌ Error: rvalue

(++x) = 10;  // ✅ OK: lvalue can be assigned
// (x++) = 10;  // ❌ Error: rvalue cannot be assigned
```

---

## Practical Examples

### Temporary Objects

```cpp
std::string s1 = "hello";
std::string s2 = "world";

// Temporary from concatenation
std::string s3 = s1 + s2;  // s1 + s2 is rvalue
// (s1 + s2).append("!");  // ❌ Can't modify rvalue (pre-C++11)

// In C++11+, temporaries can be used if class allows
(s1 + s2).size();  // ✅ OK: const member function
```

### Perfect Forwarding

```cpp
template<typename T>
void wrapper(T&& arg) {
    // Forward preserving value category
    actual_function(std::forward<T>(arg));
}

int x = 10;
wrapper(x);      // Forwards as lvalue
wrapper(20);     // Forwards as rvalue
```

---

## Common Pitfalls

### Using Moved-From Objects

```cpp
std::vector<int> v1 = {1, 2, 3};
std::vector<int> v2 = std::move(v1);

// ⚠️ v1 is now moved-from
std::cout << v1.size();  // Undefined! Don't use moved-from objects
// v1.clear();           // Must reset before using
```

### Dangling References

```cpp
const std::string& getDangling() {
    return "temporary";  // ❌ Returns reference to temporary!
}

const std::string& ref = getDangling();
std::cout << ref;  // ❌ Undefined: temporary destroyed
```

### Moving const Objects

```cpp
const std::vector<int> cv = {1, 2, 3};
std::vector<int> v2 = std::move(cv);  // ❌ Calls COPY! const prevents move
```

---

## Summary

**Lvalue**:
- Has persistent storage
- Can take address: `&x`
- Variables, dereferenced pointers, references
- Binds to `T&` or `const T&`

**Rvalue**:
- Temporary value
- Cannot take address
- Literals, temporaries, function returns by value
- Binds to `T&&` or `const T&`

**Key points**:
```cpp
int x = 42;

x                    // lvalue
42                   // rvalue
x + 1                // rvalue
std::move(x)         // rvalue (cast)

int& lr = x;         // OK
const int& cr = 42;  // OK (extends lifetime)
int&& rr = 42;       // OK
int&& rr2 = std::move(x);  // OK
```

Understanding lvalues and rvalues is essential for move semantics, perfect forwarding, and writing efficient modern C++.