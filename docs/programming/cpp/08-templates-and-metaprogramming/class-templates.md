---
id: class-templates
title: Class Templates
sidebar_label: Class Templates
sidebar_position: 2
tags: [c++, templates, class-templates, generic-programming]
---

# Class Templates

Class templates create generic classes that work with different types. Think `std::vector<T>` or `std::unique_ptr<T>` - same class, different types.

:::info One Class Definition, Many Types
Class template = blueprint for creating type-specific classes. `vector<int>` and `vector<string>` are different types from same template.
:::

## Basic Class Template

```cpp showLineNumbers 
template<typename T>
class Box {
    T value;
    
public:
    Box(T v) : value(v) {}
    
    T get() const { return value; }
    void set(T v) { value = v; }
};

// Usage
Box<int> intBox(42);
Box<std::string> strBox("hello");
Box<double> dblBox(3.14);

std::cout << intBox.get();   // 42
std::cout << strBox.get();   // "hello"
```

Compiler generates `Box<int>`, `Box<std::string>`, and `Box<double>` as separate classes.

## Template with Multiple Parameters

```cpp showLineNumbers 
template<typename Key, typename Value>
class Pair {
    Key key;
    Value value;
    
public:
    Pair(Key k, Value v) : key(k), value(v) {}
    
    Key getKey() const { return key; }
    Value getValue() const { return value; }
};

Pair<int, std::string> p(1, "one");
Pair<std::string, double> p2("pi", 3.14159);
```

## Non-Type Template Parameters

```cpp showLineNumbers 
template<typename T, size_t Size>
class Array {
    T data[Size];
    
public:
    size_t size() const { return Size; }
    
    T& operator[](size_t i) { return data[i]; }
    const T& operator[](size_t i) const { return data[i]; }
};

Array<int, 10> arr1;      // Array of 10 ints
Array<double, 5> arr2;    // Array of 5 doubles
// Each is a different type!
```

Non-type parameters must be compile-time constants.

## Member Function Implementation

**Inside class:**
```cpp showLineNumbers 
template<typename T>
class Widget {
public:
    void process() {  // Defined inside
        // Implementation
    }
};
```

**Outside class:**
```cpp showLineNumbers 
template<typename T>
class Widget {
public:
    void process();  // Declaration
};

// Definition outside (note the template<typename T> again)
template<typename T>
void Widget<T>::process() {
    // Implementation
}
```

## Template Specialization

Provide different implementation for specific types:

```cpp showLineNumbers 
// General template
template<typename T>
class Container {
public:
    void print() {
        std::cout << "Generic container\n";
    }
};

// Full specialization for bool
template<>
class Container<bool> {
public:
    void print() {
        std::cout << "Bool container (optimized!)\n";
    }
};

Container<int> c1;
c1.print();   // "Generic container"

Container<bool> c2;
c2.print();   // "Bool container (optimized!)"
```

## Partial Specialization

Specialize for pointer types:

```cpp showLineNumbers 
// General template
template<typename T>
class Smart {
public:
    void info() { std::cout << "Regular type\n"; }
};

// Partial specialization for pointers
template<typename T>
class Smart<T*> {
public:
    void info() { std::cout << "Pointer type\n"; }
};

Smart<int> s1;
s1.info();    // "Regular type"

Smart<int*> s2;
s2.info();    // "Pointer type"
```

## Default Template Arguments

```cpp showLineNumbers 
template<typename T, typename Container = std::vector<T>>
class Stack {
    Container data;
    
public:
    void push(const T& value) {
        data.push_back(value);
    }
    
    T pop() {
        T val = data.back();
        data.pop_back();
        return val;
    }
};

Stack<int> s1;                    // Uses vector<int>
Stack<int, std::deque<int>> s2;   // Uses deque<int>
```

## Template Template Parameters

Template parameter that is itself a template:

```cpp showLineNumbers 
template<typename T, template<typename> class Container>
class Stack {
    Container<T> data;
    
public:
    void push(const T& value) {
        data.push_back(value);
    }
};

// Container must be a template taking one type parameter
Stack<int, std::vector> s1;  // std::vector is a template
Stack<double, std::list> s2;  // std::list is a template
```

## Friend Functions in Templates

```cpp showLineNumbers 
template<typename T>
class Box {
    T value;
    
    // Friend function template
    template<typename U>
    friend std::ostream& operator<<(std::ostream& os, const Box<U>& box);
    
public:
    Box(T v) : value(v) {}
};

template<typename T>
std::ostream& operator<<(std::ostream& os, const Box<T>& box) {
    os << box.value;
    return os;
}

Box<int> b(42);
std::cout << b;  // Works!
```

## Static Members in Templates

Each template instantiation has its own static members:

```cpp showLineNumbers 
template<typename T>
class Counter {
    static int count;
    
public:
    Counter() { ++count; }
    ~Counter() { --count; }
    
    static int getCount() { return count; }
};

// Definition (must be outside class)
template<typename T>
int Counter<T>::count = 0;

Counter<int> c1, c2, c3;
std::cout << Counter<int>::getCount();  // 3

Counter<double> d1, d2;
std::cout << Counter<double>::getCount();  // 2

// int and double counters are SEPARATE!
```

## Class Template Argument Deduction (C++17)

```cpp showLineNumbers 
template<typename T>
class Pair {
public:
    T first, second;
    Pair(T a, T b) : first(a), second(b) {}
};

// C++17: No need to specify <int>
Pair p(10, 20);           // Deduced as Pair<int>
Pair p2(3.14, 2.71);      // Deduced as Pair<double>
Pair p3("hi", "there");   // Deduced as Pair<const char*>

// Can provide deduction guides
template<typename T>
Pair(T, T) -> Pair<T>;
```

## Nested Templates

```cpp showLineNumbers 
template<typename T>
class Outer {
public:
    template<typename U>
    class Inner {
        T outer_value;
        U inner_value;
        
    public:
        Inner(T t, U u) : outer_value(t), inner_value(u) {}
    };
};

Outer<int>::Inner<double> nested(5, 3.14);
```

## Real-World Example: Smart Pointer

```cpp showLineNumbers 
template<typename T>
class UniquePtr {
    T* ptr;
    
public:
    explicit UniquePtr(T* p = nullptr) : ptr(p) {}
    
    ~UniquePtr() { delete ptr; }
    
    // Delete copy
    UniquePtr(const UniquePtr&) = delete;
    UniquePtr& operator=(const UniquePtr&) = delete;
    
    // Move constructor
    UniquePtr(UniquePtr&& other) noexcept : ptr(other.ptr) {
        other.ptr = nullptr;
    }
    
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    T* get() const { return ptr; }
};

UniquePtr<int> p(new int(42));
std::cout << *p;  // 42
```

:::success Class Template Key Points

**Generic classes** = one template, many type-specific classes  
**Multiple parameters** = types and non-type values  
**Specialization** = custom implementation for specific types  
**Partial specialization** = customize for type patterns  
**Static members** = separate for each instantiation  
**CTAD (C++17)** = automatic type deduction from constructor  
**Define in headers** = definitions must be visible
:::
