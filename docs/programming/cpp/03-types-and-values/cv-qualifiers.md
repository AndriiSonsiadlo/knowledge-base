---
id: cv-qualifiers
title: const and volatile Qualifiers
sidebar_label: const & volatile
sidebar_position: 2
tags: [c++, const, volatile, qualifiers, const-correctness]
---

# const and volatile Qualifiers

CV-qualifiers (`const` and `volatile`) modify type behavior. `const` prevents modification; `volatile` prevents compiler optimization.

:::info const is About Contract
`const` is a compile-time contract stating "this value won't change" - enabling optimization and catching bugs early.
:::

## const Qualifier

### Basic const

```cpp
const int x = 42;
x = 10;  // ❌ Error: cannot modify const

int y = 100;
y = 200;  // ✅ OK: not const
```

### const Variables Must Initialize

```cpp
const int x;        // ❌ Error: uninitialized const
const int y = 42;   // ✅ OK
```

### const with Pointers

```cpp
// Pointer to const (cannot modify value)
const int* ptr1 = &x;
*ptr1 = 10;  // ❌ Error
ptr1 = &y;   // ✅ OK: can change pointer

// Const pointer (cannot change pointer)
int* const ptr2 = &x;
*ptr2 = 10;  // ✅ OK: can modify value
ptr2 = &y;   // ❌ Error: cannot change pointer

// Const pointer to const (both const)
const int* const ptr3 = &x;
*ptr3 = 10;  // ❌ Error
ptr3 = &y;   // ❌ Error

// Read right-to-left
const int* ptr;        // ptr is pointer to const int
int const* ptr;        // Same as above
int* const ptr;        // ptr is const pointer to int
const int* const ptr;  // ptr is const pointer to const int
```

### const with References

```cpp
int x = 42;

// const reference (cannot modify through reference)
const int& ref = x;
ref = 10;  // ❌ Error
x = 10;    // ✅ OK: x itself can change

// const reference can bind to temporary
const int& ref2 = 42;  // ✅ OK: lifetime extended
int& ref3 = 42;        // ❌ Error: non-const ref to temporary
```

### const Member Functions

```cpp
class Counter {
    int count;
public:
    Counter() : count(0) {}
    
    // const member function (doesn't modify object)
    int getCount() const {
        // count++;  // ❌ Error: modifies member
        return count;
    }
    
    // Non-const member function
    void increment() {
        count++;  // ✅ OK
    }
};

const Counter c;
c.getCount();    // ✅ OK: const function
c.increment();   // ❌ Error: non-const function on const object
```

### mutable (Override const)

```cpp
class Cache {
    mutable int access_count;  // Can modify even in const functions
    std::string data;
    
public:
    std::string getData() const {
        access_count++;  // ✅ OK: mutable
        return data;
    }
};
```

---

## constexpr (C++11)

Compile-time constants and functions:

```cpp
constexpr int square(int x) {
    return x * x;
}

constexpr int value = square(5);  // Evaluated at compile-time

int arr[value];  // OK: value is compile-time constant
```

**const vs constexpr**:
```cpp
const int x = 10;           // Runtime or compile-time
constexpr int y = 10;       // Must be compile-time

const int cx = getValue();  // ✅ OK: runtime const
constexpr int cy = getValue();  // ❌ Error: must be compile-time
```

---

## volatile Qualifier

Prevents compiler optimization - value can change externally:

```cpp
volatile int* hardware_register = (volatile int*)0x40000000;

// Compiler won't optimize away reads
int x = *hardware_register;
int y = *hardware_register;  // Second read actually happens

// Without volatile, compiler might optimize to:
// int x = *hardware_register;
// int y = x;  // Reuse cached value
```

### Common Uses

```cpp
// 1. Memory-mapped I/O
volatile uint32_t* GPIO = (volatile uint32_t*)0x40020000;
*GPIO = 0xFF;  // Write to hardware

// 2. Multi-threaded shared data (pre-C++11, now use atomics)
volatile bool flag = false;  // Can change in another thread

// 3. Signal handlers
volatile sig_atomic_t signal_received = 0;
```

:::warning volatile is NOT for Threading
In modern C++, use `std::atomic` for thread-safe variables, not `volatile`.
:::

---

## const Correctness

Practice of using `const` wherever possible:

```cpp
// Good const correctness
class String {
    char* data;
    size_t length;
    
public:
    // const getters
    size_t size() const { return length; }
    char at(size_t i) const { return data[i]; }
    
    // const parameters
    void append(const String& other) {
        // ...
    }
    
    // const return (for immutable access)
    const char* c_str() const { return data; }
};
```

### Benefits

```cpp
void process(const std::vector<int>& data) {  // Won't modify
    // data.push_back(5);  // ❌ Error: const
    
    for (int x : data) {  // OK to read
        std::cout << x;
    }
}

// Accepts temporaries
process({1, 2, 3});  // OK: binds to const&
```

---

## Top-Level vs Low-Level const

```cpp
const int x = 42;          // Top-level const (x itself)
const int* ptr = &x;       // Low-level const (pointed-to value)
int* const ptr2 = &y;      // Top-level const (pointer itself)
const int* const ptr3 = &x;// Both

// Copying ignores top-level const
const int a = 10;
int b = a;  // OK: copies value, b is non-const

// Low-level const must match
const int* p1 = &a;
int* p2 = p1;  // ❌ Error: discards const
```

---

## Summary

**const**:
- Prevents modification
- Enables optimization
- `const int* ptr` = pointer to const
- `int* const ptr` = const pointer
- const member functions don't modify object
- constexpr = compile-time const

**volatile**:
- Prevents optimization
- For hardware registers, old threading
- Modern code uses `std::atomic` instead

**Best practices**:
- Use `const` by default
- Pass large objects as `const&`
- Mark non-modifying members `const`
- Use `constexpr` for compile-time values

```cpp
// Good const usage
void process(const std::string& input) {
    // Read-only access
}

class Widget {
public:
    int getValue() const { return value; }  // const method
private:
    int value;
};
```