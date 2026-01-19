---
id: variadic-templates
title: Variadic Templates
sidebar_label: Variadic Templates
sidebar_position: 6
tags: [c++, templates, variadic-templates, cpp11]
---

# Variadic Templates

Variadic templates accept any number of arguments of any types. They're the foundation for functions like `std::make_tuple`, `printf`, and perfect forwarding.

:::info Variable Number of Arguments
`...` = template parameter pack (any number of types)  
Functions can accept 0, 1, 2, or any number of arguments!
:::

## Basic Variadic Template

```cpp
// Base case: no arguments
void print() {
    std::cout << "\n";
}

// Recursive case: at least one argument
template<typename T, typename... Args>
void print(T first, Args... rest) {
    std::cout << first << " ";
    print(rest...);  // Recursive call with remaining args
}

print(1, 2, 3);              // "1 2 3"
print("hello", 42, 3.14);    // "hello 42 3.14"
print();                     // "" (calls base case)
```

**How it works:**
- `typename... Args` = parameter pack (0 or more types)
- `Args... rest` = expands to multiple parameters
- `rest...` = expands pack in function call

## Parameter Pack Expansion

```cpp
template<typename... Args>
void forward(Args... args) {
    // args... expands to: arg1, arg2, arg3, ...
    process(args...);
}

forward(1, 2, 3);
// Expands to: process(1, 2, 3);
```

## Getting Pack Size

```cpp
template<typename... Args>
void info(Args... args) {
    std::cout << "Number of arguments: " << sizeof...(Args) << "\n";
    std::cout << "Number of values: " << sizeof...(args) << "\n";
}

info(1, 2, 3);        // 3
info("hello", 3.14);  // 2
info();               // 0
```

`sizeof...` is a compile-time operator that returns pack size.

## Modern Approach: Fold Expressions (C++17)

Much simpler than recursion!

```cpp
// Sum all arguments
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // Right fold: ((arg1 + arg2) + arg3) + ...
}

auto total = sum(1, 2, 3, 4, 5);  // 15

// Print all arguments
template<typename... Args>
void print(Args... args) {
    ((std::cout << args << " "), ...);
    std::cout << "\n";
}

print(1, "hello", 3.14);  // "1 hello 3.14"
```

We'll cover fold expressions in detail in the next section!

## Perfect Forwarding

Variadic templates + forwarding = perfect forwarding:

```cpp
template<typename... Args>
void wrapper(Args&&... args) {
    // Forward all arguments preserving lvalue/rvalue-ness
    actualFunction(std::forward<Args>(args)...);
}

int x = 42;
wrapper(x, 100, std::string("hello"));
// x forwarded as lvalue
// 100 forwarded as rvalue
// temporary string forwarded as rvalue
```

This is how `std::make_unique` and `std::make_shared` work!

## Variadic Class Templates

```cpp
template<typename... Types>
class Tuple {};

// Specialization for non-empty tuple
template<typename Head, typename... Tail>
class Tuple<Head, Tail...> {
    Head head;
    Tuple<Tail...> tail;
    
public:
    Tuple(Head h, Tail... t) : head(h), tail(t...) {}
    
    Head getHead() const { return head; }
    Tuple<Tail...>& getTail() { return tail; }
};

Tuple<int, double, std::string> t(42, 3.14, "hello");
```

## Expanding in Different Contexts

```cpp
template<typename... Args>
void example(Args... args) {
    // Function call
    func(args...);              // func(arg1, arg2, arg3)
    
    // Constructor initialization
    MyClass obj(args...);       // MyClass(arg1, arg2, arg3)
    
    // Brace initialization
    int arr[] = {args...};      // {arg1, arg2, arg3}
    
    // Template arguments
    std::tuple<Args...> t(args...);
}
```

## Processing Each Argument

```cpp
// C++17: Using fold expression
template<typename... Args>
void processAll(Args... args) {
    (process(args), ...);  // Calls process() for each arg
}

// Pre-C++17: Using initializer list trick
template<typename... Args>
void processAll(Args... args) {
    int dummy[] = {(process(args), 0)...};
    (void)dummy;  // Avoid unused variable warning
}

processAll(1, 2, 3);
// Calls: process(1), process(2), process(3)
```

## Variadic Constructor

```cpp
template<typename... Args>
class Logger {
    std::vector<std::string> messages;
    
public:
    Logger(Args... args) {
        (messages.push_back(std::to_string(args)), ...);
    }
    
    void print() {
        for (const auto& msg : messages) {
            std::cout << msg << " ";
        }
        std::cout << "\n";
    }
};

Logger log(1, 2, 3, 4);
log.print();  // "1 2 3 4"
```

## Index Sequence

Generating indices at compile-time for accessing tuple elements:

```cpp
template<size_t... Is>
void printIndices(std::index_sequence<Is...>) {
    ((std::cout << Is << " "), ...);
}

printIndices(std::make_index_sequence<5>{});
// Output: 0 1 2 3 4
```

Used internally by standard library for tuple operations.

## Real-World: make_unique

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// Usage
auto p1 = make_unique<std::string>(10, 'x');  // string(10, 'x')
auto p2 = make_unique<std::vector<int>>(5, 42);  // vector(5, 42)
```

Perfect forwarding lets you pass constructor arguments through!

## Type Constraints

```cpp
// C++20: Require all types satisfy a concept
template<typename... Args>
requires (std::integral<Args> && ...)
auto sum(Args... args) {
    return (args + ...);
}

sum(1, 2, 3);      // ✅ OK: all ints
// sum(1, 2.5, 3);   // ❌ Error: 2.5 is not integral
```

:::success Variadic Template Essentials

**Parameter pack** = `typename... Args` (0+ types)  
**Pack expansion** = `args...` expands to multiple arguments  
**sizeof...** = pack size at compile-time  
**Fold expressions (C++17)** = `(args + ...)` simplifies operations  
**Perfect forwarding** = `std::forward<Args>(args)...`  
**Common use** = factory functions, wrappers, tuples  
**Recursion vs folds** = prefer fold expressions when possible
:::