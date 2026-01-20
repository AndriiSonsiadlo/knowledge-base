---
id: full-specialization
title: Full Template Specialization
sidebar_label: Full Specialization
sidebar_position: 1
tags: [c++, templates, specialization, template-specialization]
---

# Full Template Specialization

Full specialization provides a completely custom implementation for specific template arguments. It's like saying "for this exact type, use this completely different code."

:::info Complete Override
Full specialization = brand new implementation for specific types. `Template<int>` can be totally different from `Template<double>`.
:::

## Function Template Specialization

```cpp showLineNumbers 
// Primary template
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// Full specialization for const char*
template<>
const char* max<const char*>(const char* a, const char* b) {
    return (strcmp(a, b) > 0) ? a : b;
}

// Usage
int x = max(5, 10);           // Uses primary template
const char* s = max("abc", "xyz");  // Uses specialization
```

**Syntax:** `template<>` with explicit type after function name.

## Why Specialize?

**Different algorithm for specific types:**
```cpp showLineNumbers 
// Generic swap
template<typename T>
void swap(T& a, T& b) {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}

// Optimized for large arrays - swap pointers instead
template<>
void swap<std::array<int, 1000>>(
    std::array<int, 1000>& a,
    std::array<int, 1000>& b
) {
    a.swap(b);  // Member swap is faster
}
```

## Class Template Specialization

```cpp showLineNumbers 
// Primary template
template<typename T>
class Storage {
    T data;
public:
    void set(T value) { data = value; }
    T get() const { return data; }
    void print() const { std::cout << data << "\n"; }
};

// Full specialization for bool (bit packing)
template<>
class Storage<bool> {
    unsigned char data;
    int position;
public:
    void set(bool value) {
        if (value) {
            data |= (1 << position);
        } else {
            data &= ~(1 << position);
        }
    }
    
    bool get() const {
        return (data >> position) & 1;
    }
    
    void print() const {
        std::cout << (get() ? "true" : "false") << "\n";
    }
};

Storage<int> intStore;
intStore.set(42);

Storage<bool> boolStore;  // Uses specialized version
boolStore.set(true);
```

**Different implementation, same interface!**

## Multiple Template Parameters

```cpp showLineNumbers 
// Primary template
template<typename T, typename U>
class Pair {
public:
    T first;
    U second;
    void info() { std::cout << "Different types\n"; }
};

// Full specialization: both same type
template<typename T>
class Pair<T, T> {
public:
    T first;
    T second;
    void info() { std::cout << "Same type\n"; }
    
    void swap() {  // Extra method only for same types
        std::swap(first, second);
    }
};

Pair<int, double> p1;
p1.info();  // "Different types"

Pair<int, int> p2;
p2.info();  // "Same type"
p2.swap();  // Only available in specialization
```

## Specialization for Pointers

```cpp showLineNumbers 
// Primary template
template<typename T>
class SmartPtr {
    T* ptr;
public:
    T& operator*() { return *ptr; }
    T* operator->() { return ptr; }
};

// Specialization for void* (can't dereference)
template<>
class SmartPtr<void> {
    void* ptr;
public:
    // No operator* or operator-> (void* can't be dereferenced)
    void* get() { return ptr; }
};
```

## Specialization Declaration and Definition

**Declare in header:**
```cpp showLineNumbers 
// header.h
template<typename T>
class Widget {
    void process();
};

// Declare specialization
template<>
class Widget<int>;

// Or declare just member
template<>
void Widget<int>::process();
```

**Define in source:**
```cpp showLineNumbers 
// source.cpp
template<>
class Widget<int> {
    void process() {
        std::cout << "Specialized for int\n";
    }
};

// Or define just member
template<>
void Widget<int>::process() {
    std::cout << "Specialized member for int\n";
}
```

## Member Function Specialization

```cpp showLineNumbers 
template<typename T>
class Processor {
public:
    void process(T value);
};

// General template definition
template<typename T>
void Processor<T>::process(T value) {
    std::cout << "Generic: " << value << "\n";
}

// Specialize just one member function
template<>
void Processor<std::string>::process(std::string value) {
    std::cout << "String specialized: " << value << "\n";
}

Processor<int> pi;
pi.process(42);  // "Generic: 42"

Processor<std::string> ps;
ps.process("hello");  // "String specialized: hello"
```

## Specialization for Complex Types

```cpp showLineNumbers 
// Primary template
template<typename T>
class Container {
public:
    void info() { std::cout << "Generic container\n"; }
};

// Specialization for std::vector
template<typename T>
class Container<std::vector<T>> {
public:
    void info() { std::cout << "Vector container\n"; }
};

Container<int> c1;
c1.info();  // "Generic container"

Container<std::vector<int>> c2;
c2.info();  // "Vector container"
```

## static Members in Specializations

Each specialization has its own static members:

```cpp showLineNumbers 
template<typename T>
class Counter {
    static int count;
public:
    Counter() { ++count; }
    static int getCount() { return count; }
};

template<typename T>
int Counter<T>::count = 0;

// Specialization for bool with different initial value
template<>
int Counter<bool>::count = 100;

Counter<int> i1, i2, i3;
std::cout << Counter<int>::getCount();  // 3

Counter<bool> b1, b2;
std::cout << Counter<bool>::getCount();  // 102 (started at 100!)
```

## Specialization Order Matters

```cpp showLineNumbers 
// Forward declare specialization before use
template<typename T>
class Widget;

template<>
class Widget<int> {
    // Specialization
};

// ❌ Too late! Already used above
// template<>
// class Widget<int> { ... };
```

Always declare specializations before first use.

## Friend Functions in Specializations

```cpp showLineNumbers 
template<typename T>
class Box {
    T value;
    
    friend std::ostream& operator<<(std::ostream& os, const Box& b) {
        os << b.value;
        return os;
    }
};

// Specialized for bool - different output format
template<>
class Box<bool> {
    bool value;
    
    friend std::ostream& operator<<(std::ostream& os, const Box& b) {
        os << (b.value ? "TRUE" : "FALSE");
        return os;
    }
};
```

## Type Traits Implementation

Specialization is how type traits work:

```cpp showLineNumbers 
// Primary template: assume false
template<typename T>
struct is_pointer {
    static constexpr bool value = false;
};

// Specialization for pointer types
template<typename T>
struct is_pointer<T*> {
    static constexpr bool value = true;
};

is_pointer<int>::value;    // false
is_pointer<int*>::value;   // true
is_pointer<char*>::value;  // true
```

## Real-World Example: Custom Hash

```cpp showLineNumbers 
// Primary template (assumes type has std::hash)
template<typename T>
struct MyHash {
    size_t operator()(const T& value) const {
        return std::hash<T>{}(value);
    }
};

// Specialization for custom type
struct Point {
    int x, y;
};

template<>
struct MyHash<Point> {
    size_t operator()(const Point& p) const {
        // Custom hash combining x and y
        return std::hash<int>{}(p.x) ^ (std::hash<int>{}(p.y) << 1);
    }
};

std::unordered_map<Point, std::string, MyHash<Point>> map;
```

## Avoid Over-Specialization

```cpp showLineNumbers 
// ❌ Bad: Too many specializations
template<> void process<int>();
template<> void process<long>();
template<> void process<short>();
template<> void process<unsigned>();
// ... 20 more specializations

// ✅ Better: Use if constexpr or concepts
template<typename T>
void process() {
    if constexpr (std::is_integral_v<T>) {
        // Handle all integral types
    } else if constexpr (std::is_floating_point_v<T>) {
        // Handle all floating types
    }
}
```

## Specialization vs Overloading

**Function templates:** Prefer overloading over specialization:

```cpp showLineNumbers 
// ❌ Specialization (can cause surprises)
template<typename T>
void func(T value) { std::cout << "Template\n"; }

template<>
void func<int>(int value) { std::cout << "Specialized\n"; }

// ✅ Better: Overload
template<typename T>
void func(T value) { std::cout << "Template\n"; }

void func(int value) { std::cout << "Overload\n"; }
```

Overloading participates in normal overload resolution. Specialization doesn't!

:::success Full Specialization Key Points

**Complete override** = entirely new implementation  
**`template<>`** = syntax for full specialization  
**All parameters specified** = no template parameters left  
**Classes and functions** = both can be specialized  
**Static members** = separate for each specialization  
**Member functions** = can specialize individually  
**Type traits** = built using specialization  
**Prefer overloading** = for function templates  
**Use sparingly** = if constexpr often better
:::