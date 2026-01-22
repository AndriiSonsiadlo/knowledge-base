---
id: references
title: References
sidebar_label: References
sidebar_position: 2
tags: [c++, references, aliases, pointers]
---

# References

A reference is an alias - another name for an existing object. Unlike pointers, references cannot be null, must be initialized, and cannot be reseated.

:::info Reference = Alias
Not a new variable, just another name for the same memory location.
```cpp
int x = 42;
int& ref = x;  // ref IS x, not a copy
ref = 100;     // modifies x
```
:::


## Basic References

References create an _alternate name_ for an existing variable. All operations on the reference affect the original variable because they're the same thing.

```cpp showLineNumbers 
int x = 42;
int& ref = x;  // ref is an alias for x

ref = 100;            // Modifies x
std::cout << x;       // 100
std::cout << ref;     // 100
std::cout << &ref;    // Same address as &x

x = 200;              // Modifying x
std::cout << ref;     // 200 (ref sees the change)
```


## Initialization Rules
```cpp showLineNumbers
// ✅ Must initialize
int x = 42;
int& ref = x;

// ❌ Cannot be uninitialized
int& bad_ref;  // Error

// ❌ Cannot be null
int& null_ref = nullptr;  // Error

// ❌ Cannot reseat
int y = 100;
ref = y;  // Copies value, doesn't reseat
```

## Function Parameters

References enable efficient **_pass-by-reference_** semantics, allowing functions to modify caller's variables without copying.

```cpp showLineNumbers
// Pass by value (copy)
void increment_copy(int x) {
    x++;  // Modifies copy
}

// Pass by reference (no copy)
void increment_ref(int& x) {
    x++;  // Modifies original
}

int value = 10;
increment_copy(value);  // value still 10
increment_ref(value);   // value now 11
```

### const References

Const references allow reading but prevent modification, making them ideal for passing large objects efficiently without allowing changes.

:::success Best Practice for Large Objects
```cpp
// ❌ Expensive copy
void print(std::string s) {
    std::cout << s;
}

// ✅ No copy, can't modify
void print(const std::string& s) {
    std::cout << s;
    // s[0] = 'X';  // Error: const
}

print("Hello");  // ✅ Binds to temporary
```
:::

**Why `const&`?**
- No copy overhead (efficient)
- Can bind to temporaries
- Documents intent (won't modify)
- Prevents accidental changes

## Return by Reference

Functions can return references to allow modification of class members or avoid copying large objects.

```cpp showLineNumbers 
class Widget {
    std::string name;
public:
    // Non-const getter (allows modification)
    std::string& getName() {
        return name;
    }
    
    // const getter (read-only)
    const std::string& getName() const {
        return name;
    }
};

Widget w;
w.getName() = "New Name";  // ✅ Modifies through reference

const Widget cw;
// cw.getName() = "X";     // ❌ const version returns const&
```

Returning `non-const references` enables chaining and direct modification of internals. Returning `const references` provides efficient read access without allowing modification. This pattern is common for container element access (`vector::operator[]`) and getter methods.

### Danger: Dangling References

Never return references to local variables. Locals are destroyed when the function returns, creating dangling references.

```cpp showLineNumbers 
int& dangerous() {
    int x = 42;
    return x;  // ❌ x destroyed at return
}

int& safe(int& param) {
    return param;  // ✅ param outlives function
}

class Safe {
    int data;
public:
    int& get() { return data; }  // ✅ member outlives call
};
```

References don't extend object lifetimes. Returning a reference to a local creates the same problem as returning a pointer to a local - **undefined behavior**.

## L‑values and R‑values (C++11)

For a more detailed explanation, see: [Value categories](../03-types-and-values/value-categories/lvalues-rvalues.md)

### Move Semantics

Move operations transfer ownership of resources from a source object to a destination object, avoiding unnecessary and expensive copying.

For a more detailed explanation, see: [Move and copy semantics](../07-classes-and-oop/copy-and-move-semantics.md)

## Reference Wrappers

`std::reference_wrapper` allows storing references in containers, which normally can't hold references directly.

```cpp showLineNumbers 
int x = 10, y = 20, z = 30;

// ❌ Can't store references in vector
// std::vector<int&> refs;  // Error

// ✅ Can store reference_wrappers
std::vector<std::reference_wrapper<int>> refs;
refs.push_back(std::ref(x));
refs.push_back(std::ref(y));
refs.push_back(std::ref(z));

refs[0].get()++;  // Increments x
std::cout << x;   // 11
```

References can't be stored in containers because they're not regular objects (can't be reassigned, no default construction). `std::reference_wrapper` wraps a reference in a copyable, assignable object that acts like a reference.



## References vs Pointers

| Feature         | Reference                 | Pointer           |
|-----------------|---------------------------|-------------------|
| Syntax          | `int& ref = x`            | `int* ptr = &x`   |
| Null possible   | ❌ No                      | ✅ Yes (`nullptr`) |
| Must initialize | ✅ Yes                     | ❌ No (but should) |
| Can reassign    | ❌ No (always same object) | ✅ Yes             |
| Dereference     | Automatic                 | Manual (`*ptr`)   |
| Size            | Same as original          | 8 bytes (64-bit)  |


## Summary

:::info References vs Pointers
- Reference = alias (same object)
- Pointer = variable storing address
- References safer (no null, no reassignment)
- Pointers more flexible (nullable, reassignable)
:::

:::info Key rules
- Must initialize at declaration
- Cannot be null or reseated
- Assignment copies values, doesn't reseat
- Perfect for function parameters
:::

:::info Usage patterns
- `const T&` for read-only parameters (large objects)
- `T&` for modifiable parameters
- Return `T&` for member access
- Never return reference to local
:::
