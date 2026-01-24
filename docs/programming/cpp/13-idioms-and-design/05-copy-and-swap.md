---
id: copy-and-swap
title: Copy-and-Swap Idiom
sidebar_label: Copy-and-Swap
sidebar_position: 5
tags: [cpp, copy-and-swap, idioms, exception-safety, assignment]
---

# Copy-and-Swap Idiom

Copy-and-swap is an elegant technique for implementing assignment operators that provides strong exception safety and eliminates code duplication by leveraging the copy constructor and a non-throwing swap function.

:::info Exception-Safe Assignment
Copy-and-swap guarantees strong exception safety: if an exception occurs during assignment, the object remains unchanged. The idiom unifies copy and move assignment into a single function.
:::

## The Problem with Naive Assignment

```cpp showLineNumbers
class Widget {
    int* data_;
    size_t size_;
    
public:
    // ❌ Problematic assignment
    Widget& operator=(const Widget& other) {
        if (this == &other) return *this;  // Self-assignment check
        
        delete[] data_;  // ⚠️ If next line throws, object is broken!
        
        size_ = other.size_;
        data_ = new int[size_];  // ⚠️ May throw!
        std::copy(other.data_, other.data_ + size_, data_);
        
        return *this;
    }
};

// Problem: If 'new' throws, we've deleted our data but failed to copy
// Object is in invalid state!
```

## Copy-and-Swap Pattern

```cpp showLineNumbers
class Widget {
    int* data_;
    size_t size_;
    
public:
    // Constructor
    Widget(size_t size) 
        : data_(new int[size]), size_(size) {}
    
    // Destructor
    ~Widget() {
        delete[] data_;
    }
    
    // Copy constructor
    Widget(const Widget& other)
        : data_(new int[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }
    
    // ✅ Copy-and-swap assignment
    Widget& operator=(Widget other) {  // Pass by value - copies implicitly
        swap(*this, other);             // Non-throwing swap
        return *this;                   // Temp 'other' destroyed, takes old data
    }
    
    // Swap function
    friend void swap(Widget& first, Widget& second) noexcept {
        using std::swap;
        swap(first.data_, second.data_);
        swap(first.size_, second.size_);
    }
};
```

**How it works:**
1. Assignment parameter passed **by value** → invokes copy constructor
2. If copy throws, our object is unchanged (exception safety!)
3. Swap our contents with the copy (non-throwing)
4. Copy (holding our old data) destroyed automatically

## Step-by-Step Example

```cpp showLineNumbers
Widget w1(10);  // data1, size=10
Widget w2(20);  // data2, size=20

w1 = w2;  // What happens?

// Step 1: Parameter 'other' created (copy constructor)
//   other.data_ = new copy of w2.data_
//   other.size_ = 20

// Step 2: Swap w1 and other
//   w1.data_ now points to copied data
//   w1.size_ = 20
//   other.data_ points to old w1.data_
//   other.size_ = 10

// Step 3: other destroyed (destructor)
//   Deletes old w1.data_

// Result: w1 has w2's data, old w1 data cleaned up
```

## Unified Copy and Move Assignment

The same function handles both copy and move:

```cpp showLineNumbers
class Widget {
    int* data_;
    size_t size_;
    
public:
    Widget(size_t size) 
        : data_(new int[size]), size_(size) {}
    
    ~Widget() { delete[] data_; }
    
    // Copy constructor
    Widget(const Widget& other)
        : data_(new int[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }
    
    // Move constructor
    Widget(Widget&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    // ✅ Unified assignment (handles both copy and move!)
    Widget& operator=(Widget other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    friend void swap(Widget& a, Widget& b) noexcept {
        using std::swap;
        swap(a.data_, b.data_);
        swap(a.size_, b.size_);
    }
};

int main() {
    Widget w1(10);
    Widget w2(20);
    
    // Copy assignment
    w1 = w2;  // Calls copy constructor to create 'other'
    
    // Move assignment  
    w1 = std::move(w2);  // Calls move constructor to create 'other'
    
    // Same operator= handles both!
}
```

**Why it works:**
- `w1 = w2` → `Widget other(w2)` → copy constructor
- `w1 = std::move(w2)` → `Widget other(std::move(w2))` → move constructor

## Complete Implementation

```cpp showLineNumbers
#include <algorithm>
#include <cstring>

class String {
    char* data_;
    size_t size_;
    
public:
    // Constructor
    String(const char* str = "") {
        size_ = std::strlen(str);
        data_ = new char[size_ + 1];
        std::strcpy(data_, str);
    }
    
    // Destructor
    ~String() {
        delete[] data_;
    }
    
    // Copy constructor
    String(const String& other) 
        : size_(other.size_), data_(new char[other.size_ + 1]) {
        std::strcpy(data_, other.data_);
    }
    
    // Move constructor
    String(String&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    // Unified assignment (copy-and-swap)
    String& operator=(String other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    // Non-throwing swap
    friend void swap(String& first, String& second) noexcept {
        using std::swap;
        swap(first.data_, second.data_);
        swap(first.size_, second.size_);
    }
    
    // Accessors
    const char* c_str() const { return data_; }
    size_t size() const { return size_; }
};

// Usage
int main() {
    String s1("Hello");
    String s2("World");
    
    s1 = s2;              // Copy assignment
    s1 = String("Test");  // Move assignment
    s1 = s1;              // Self-assignment (works correctly!)
}
```

## Why It's Exception-Safe

```cpp showLineNumbers
Widget w1(10);  // Original data
Widget w2(20);

try {
    w1 = w2;
    // Step 1: Create temporary 'other' by copying w2
    //   If copy constructor throws → w1 unchanged ✅
    
    // Step 2: Swap w1 with other (no-throw)
    //   Always succeeds
    
    // Step 3: Destroy temp (no-throw)
    //   Always succeeds
} catch (...) {
    // w1 is either completely unchanged (if copy threw)
    // or successfully updated (if copy succeeded)
    // Never in broken state!
}
```

**Strong exception guarantee:** Operation either succeeds completely or has no effect.

## Self-Assignment Safety

```cpp showLineNumbers
String s("Hello");
s = s;  // Self-assignment

// What happens with copy-and-swap?
// Step 1: Create temp copy of s
//   temp.data_ = copy of s.data_
// Step 2: Swap s with temp
//   Now s.data_ points to new copy
//   temp.data_ points to old data
// Step 3: Destroy temp
//   Old data deleted

// Result: s contains copy of itself (correct!)
// No explicit self-assignment check needed!
```

Traditional implementation needs explicit check; copy-and-swap handles it automatically.

## Performance Considerations

### When Copy-and-Swap Is Good

```cpp showLineNumbers
class ResourceHolder {
    std::unique_ptr<ExpensiveResource> resource_;
    
public:
    // Copy-and-swap shines here
    ResourceHolder& operator=(ResourceHolder other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    friend void swap(ResourceHolder& a, ResourceHolder& b) noexcept {
        using std::swap;
        swap(a.resource_, b.resource_);  // Just pointer swap!
    }
};
```

When resources are held by pointers/handles, swap is very cheap.

### When Copy-and-Swap May Be Slow

```cpp showLineNumbers
class LargeArray {
    std::array<int, 1000000> data_;  // Large value member
    
public:
    // Copy-and-swap always makes full copy
    LargeArray& operator=(LargeArray other) noexcept {
        swap(*this, other);  // Swaps entire array!
        return *this;
    }
    
    // Alternative: traditional assignment can reuse memory
    LargeArray& operator=(const LargeArray& other) {
        if (this != &other) {
            data_ = other.data_;  // May reuse existing allocation
        }
        return *this;
    }
};
```

For large value types, copy-and-swap always allocates; traditional assignment might reuse.

## Implementing Swap

### Friend Function (Preferred)

```cpp showLineNumbers
class Widget {
public:
    friend void swap(Widget& a, Widget& b) noexcept {
        using std::swap;
        swap(a.data_, b.data_);
        swap(a.size_, b.size_);
    }
};

// ADL finds the swap
Widget w1, w2;
swap(w1, w2);  // Calls friend function via ADL
```

### Member Function

```cpp showLineNumbers
class Widget {
public:
    void swap(Widget& other) noexcept {
        using std::swap;
        swap(data_, other.data_);
        swap(size_, other.size_);
    }
};

// Free function forwards to member
inline void swap(Widget& a, Widget& b) noexcept {
    a.swap(b);
}
```

Both work; friend is more idiomatic.

## std::swap Specialization

```cpp showLineNumbers
class Widget {
    // ... implementation
};

// Specialize std::swap (pre-C++11 style)
namespace std {
    template<>
    void swap<Widget>(Widget& a, Widget& b) noexcept {
        a.swap(b);
    }
}

// Modern way: use ADL-findable swap
friend void swap(Widget& a, Widget& b) noexcept {
    // ...
}
```

Modern C++ prefers ADL-findable `swap` over `std::swap` specialization.

## Complete Example with All Special Functions

```cpp showLineNumbers
#include <algorithm>
#include <iostream>

class Array {
    int* data_;
    size_t size_;
    
public:
    // Constructor
    explicit Array(size_t size = 0)
        : data_(size ? new int[size]() : nullptr), size_(size) {
        std::cout << "Ctor\n";
    }
    
    // Destructor
    ~Array() {
        std::cout << "Dtor\n";
        delete[] data_;
    }
    
    // Copy constructor
    Array(const Array& other)
        : data_(other.size_ ? new int[other.size_] : nullptr),
          size_(other.size_) {
        std::cout << "Copy ctor\n";
        std::copy(other.data_, other.data_ + size_, data_);
    }
    
    // Move constructor
    Array(Array&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        std::cout << "Move ctor\n";
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    // Unified assignment (copy-and-swap)
    Array& operator=(Array other) noexcept {
        std::cout << "Assignment (via copy-and-swap)\n";
        swap(*this, other);
        return *this;
    }
    
    // Swap
    friend void swap(Array& a, Array& b) noexcept {
        std::cout << "Swap\n";
        using std::swap;
        swap(a.data_, b.data_);
        swap(a.size_, b.size_);
    }
    
    // Access
    int& operator[](size_t i) { return data_[i]; }
    const int& operator[](size_t i) const { return data_[i]; }
    size_t size() const { return size_; }
};

int main() {
    Array a1(10);     // Ctor
    Array a2(20);     // Ctor
    
    a1 = a2;          // Copy ctor (creates temp) + Swap + Dtor (temp)
    
    a1 = Array(30);   // Ctor + Move ctor (creates temp) + Swap + Dtor (temp)
    
    Array a3(a1);     // Copy ctor
    Array a4(std::move(a1));  // Move ctor
}
```

## Variations

### Separate Copy and Move Assignment

If you need different behavior:

```cpp showLineNumbers
class Widget {
public:
    // Copy assignment
    Widget& operator=(const Widget& other) {
        Widget temp(other);  // Copy
        swap(*this, temp);
        return *this;
    }
    
    // Move assignment
    Widget& operator=(Widget&& other) noexcept {
        swap(*this, other);
        return *this;
    }
};
```

### With Custom Allocator

```cpp showLineNumbers
template<typename T, typename Allocator = std::allocator<T>>
class Vector {
    T* data_;
    size_t size_;
    Allocator alloc_;
    
public:
    Vector& operator=(Vector other) noexcept {
        // Swap only data and size, not allocator
        using std::swap;
        swap(data_, other.data_);
        swap(size_, other.size_);
        // alloc_ not swapped (allocators may not be swappable)
        return *this;
    }
};
```

## Best Practices

:::success DO
- Use copy-and-swap for strong exception safety
- Implement non-throwing `swap`
- Pass assignment parameter by value
- Mark swap as `noexcept`
- Use for resource-managing classes
  :::

:::danger DON'T
- Forget to implement move constructor
- Make swap throwing
- Use when traditional assignment is more efficient
- Over-apply to simple value types
- Forget `using std::swap` in swap function
  :::

## When NOT to Use

```cpp showLineNumbers
// Simple types - copy-and-swap is overkill
class Point {
    int x_, y_;
    
public:
    // Traditional assignment is fine and efficient
    Point& operator=(const Point& other) {
        x_ = other.x_;
        y_ = other.y_;
        return *this;
    }
};

// Types with allocator/memory that can be reused
class OptimizedString {
    char* data_;
    size_t size_, capacity_;
    
public:
    // Traditional can reuse existing allocation
    OptimizedString& operator=(const OptimizedString& other) {
        if (this != &other) {
            if (capacity_ < other.size_) {
                delete[] data_;
                data_ = new char[other.size_];
                capacity_ = other.size_;
            }
            std::strcpy(data_, other.data_);
            size_ = other.size_;
        }
        return *this;
    }
};
```

## Summary

Copy-and-swap idiom implements assignment using copy constructor and swap:

**Pattern:**
```cpp
class T {
public:
    T(const T& other);              // Copy constructor
    T(T&& other) noexcept;          // Move constructor
    T& operator=(T other) noexcept { // Pass by value!
        swap(*this, other);
        return *this;
    }
    friend void swap(T& a, T& b) noexcept;
};
```

**Benefits:**
- Strong exception safety
- Automatic self-assignment safety
- Unified copy and move assignment
- Code reuse (leverages copy/move constructors)
- No code duplication

**Trade-offs:**
- Always creates temporary (may be less efficient)
- Not optimal for types that can reuse allocations
- Requires proper move constructor for efficiency

**Use when:**
- Managing resources (memory, handles, connections)
- Need strong exception safety
- Want to unify copy/move assignment

```cpp
// Interview answer:
// "Copy-and-swap implements assignment by taking parameter by value
// (which invokes copy or move constructor), then swapping contents
// with a non-throwing swap. Provides strong exception safety because
// if the copy/move throws, the original object is unchanged. Also
// handles self-assignment automatically. Unifies copy and move
// assignment into single function. Trade-off is always creating a
// temporary, but eliminates code duplication and guarantees safety."
```