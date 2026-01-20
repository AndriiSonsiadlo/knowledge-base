---
id: sfinae
title: SFINAE (Substitution Failure Is Not An Error)
sidebar_label: SFINAE
sidebar_position: 10
tags: [c++, templates, sfinae, metaprogramming, advanced]
---

# SFINAE

SFINAE is a fundamental C++ template mechanism: when template argument substitution fails, the compiler removes that template from consideration instead of causing a compilation error. This enables powerful compile-time decisions.

:::info The Core Rule
"Substitution Failure Is Not An Error" - If substituting template arguments fails, that's okay. The compiler just tries other overloads.
:::

## Basic SFINAE Example

```cpp showLineNumbers 
// Works for types with .size() method
template<typename T>
auto getSize(const T& container) 
    -> decltype(container.size()) 
{
    return container.size();
}

// Works for array types
template<typename T, size_t N>
size_t getSize(const T (&array)[N]) {
    return N;
}

std::vector<int> vec{1, 2, 3};
int arr[5];

auto s1 = getSize(vec);  // Calls first version
auto s2 = getSize(arr);  // Calls second version
// Both overloads are valid, but compiler picks best match
```

If `vec.size()` didn't exist, the first template would be removed from consideration (SFINAE), not cause an error.

## How SFINAE Works

```cpp showLineNumbers 
// This will SFINAE away for types without ::value_type
template<typename T>
typename T::value_type get(const T& container) {
    return container[0];
}

// Fallback for types without ::value_type
template<typename T>
T get(const T& value) {
    return value;
}

std::vector<int> vec{42};
int x = 42;

auto a = get(vec);  // Uses first (vector has value_type)
auto b = get(x);    // Uses second (int doesn't have value_type, SFINAE)
```

**What happens:**
1. Compiler tries first template with `int`
2. Substitution fails: `int::value_type` doesn't exist
3. SFINAE: Remove first template, no error
4. Try second template: Success!

## Expression SFINAE

Check if an expression is valid:

```cpp showLineNumbers 
// Check if T supports operator[]
template<typename T>
auto access(T& container, size_t index)
    -> decltype(container[index])  // SFINAE on this expression
{
    return container[index];
}

// Fallback
template<typename T>
auto access(T& value, size_t)
    -> decltype(value)
{
    return value;
}

std::vector<int> vec{1, 2, 3};
int x = 42;

access(vec, 1);  // Returns vec[1]
access(x, 0);    // Returns x (no operator[])
```

## Trailing Return Type SFINAE

The trailing return type is perfect for SFINAE:

```cpp showLineNumbers 
// Only enabled if T has .begin() and .end()
template<typename T>
auto print(const T& container)
    -> decltype(container.begin(), container.end(), void())
{
    for (const auto& item : container) {
        std::cout << item << " ";
    }
}

// Fallback for non-containers
void print(...) {  // Variadic catch-all
    std::cout << "Not a container";
}

std::vector<int> vec{1, 2, 3};
int x = 42;

print(vec);  // "1 2 3"
print(x);    // "Not a container"
```

**Trick:** `(expr1, expr2, void())` checks multiple expressions and returns `void`.

## SFINAE with std::enable_if

Classic approach before C++20 concepts:

```cpp showLineNumbers 
// Only for integral types
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
twice(T value) {
    return value * 2;
}

// Only for floating point
template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
twice(T value) {
    return value * 2.0;
}

twice(5);     // Calls integral version
twice(3.14);  // Calls floating point version
```

If the condition is false, `enable_if<false, T>::type` doesn't exist → SFINAE.

## Detection Idiom

Check if a type has specific members:

```cpp showLineNumbers 
// Primary template: assume false
template<typename, typename = void>
struct has_size : std::false_type {};

// Specialization: true if T::size() exists
template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

// Helper variable template
template<typename T>
constexpr bool has_size_v = has_size<T>::value;

// Usage
has_size_v<std::vector<int>>  // true
has_size_v<int>                // false
```

**How it works:**
- `std::void_t` turns any type into `void`
- If `T::size()` doesn't exist, substitution fails → SFINAE
- Falls back to primary template (false_type)

## Checking Member Functions

```cpp showLineNumbers 
// Check for .serialize() method
template<typename T, typename = void>
struct is_serializable : std::false_type {};

template<typename T>
struct is_serializable<
    T,
    std::void_t<decltype(std::declval<T>().serialize())>
> : std::true_type {};

// Use it
template<typename T>
std::enable_if_t<is_serializable<T>::value, std::string>
save(const T& obj) {
    return obj.serialize();
}

template<typename T>
std::enable_if_t<!is_serializable<T>::value, std::string>
save(const T&) {
    return "Cannot serialize";
}
```

## Checking Member Types

```cpp showLineNumbers 
// Check if type has ::iterator
template<typename T, typename = void>
struct has_iterator : std::false_type {};

template<typename T>
struct has_iterator<T, std::void_t<typename T::iterator>>
    : std::true_type {};

// Check if type has ::value_type
template<typename T, typename = void>
struct has_value_type : std::false_type {};

template<typename T>
struct has_value_type<T, std::void_t<typename T::value_type>>
    : std::true_type {};

has_iterator<std::vector<int>>::value   // true
has_value_type<std::map<int, int>>::value  // true
```

## Function Overloading with SFINAE

```cpp showLineNumbers 
// For containers
template<typename T>
auto sum(const T& container)
    -> decltype(container.begin(), int())
{
    int total = 0;
    for (const auto& item : container) {
        total += item;
    }
    return total;
}

// For arithmetic types
template<typename T>
std::enable_if_t<std::is_arithmetic_v<T>, T>
sum(T value) {
    return value;
}

std::vector<int> vec{1, 2, 3};
sum(vec);   // 6 (container version)
sum(42);    // 42 (arithmetic version)
```

## SFINAE in Class Templates

```cpp showLineNumbers 
template<typename T, typename Enable = void>
class Wrapper;

// Specialization for pointers
template<typename T>
class Wrapper<T, std::enable_if_t<std::is_pointer_v<T>>> {
public:
    void info() { std::cout << "Pointer wrapper\n"; }
};

// Specialization for non-pointers
template<typename T>
class Wrapper<T, std::enable_if_t<!std::is_pointer_v<T>>> {
public:
    void info() { std::cout << "Value wrapper\n"; }
};

Wrapper<int*> w1;
w1.info();  // "Pointer wrapper"

Wrapper<int> w2;
w2.info();  // "Value wrapper"
```

## Complex SFINAE Conditions

```cpp showLineNumbers 
// Type must be integral AND not bool
template<typename T>
std::enable_if_t<
    std::is_integral_v<T> && !std::is_same_v<T, bool>,
    T
>
process(T value) {
    return value * 2;
}

// Type must have begin(), end(), and size()
template<typename T>
auto process(const T& container)
    -> decltype(
        container.begin(),
        container.end(),
        container.size(),
        void()
    )
{
    return container.size();
}
```

## std::void_t Explained

```cpp showLineNumbers 
// std::void_t always produces void
template<typename...>
using void_t = void;

// Useful for SFINAE
template<typename T, typename = void>
struct has_foo : std::false_type {};

template<typename T>
struct has_foo<T, std::void_t<decltype(&T::foo)>>
    : std::true_type {};

// If T::foo exists, void_t<...> produces void
// Matches the specialization
// Otherwise, SFINAE removes specialization, uses primary
```

## Common SFINAE Patterns

**Has member function:**
```cpp showLineNumbers 
template<typename T, typename = void>
struct has_print : std::false_type {};

template<typename T>
struct has_print<T, std::void_t<decltype(std::declval<T>().print())>>
    : std::true_type {};
```

**Has member type:**
```cpp showLineNumbers 
template<typename T, typename = void>
struct has_value_type : std::false_type {};

template<typename T>
struct has_value_type<T, std::void_t<typename T::value_type>>
    : std::true_type {};
```

**Supports operator:**
```cpp showLineNumbers 
template<typename T, typename = void>
struct has_addition : std::false_type {};

template<typename T>
struct has_addition<T, std::void_t<decltype(std::declval<T>() + std::declval<T>())>>
    : std::true_type {};
```

## SFINAE vs Concepts (C++20)

**SFINAE (complex):**
```cpp showLineNumbers 
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
twice(T value) {
    return value * 2;
}
```

**Concepts (clean):**
```cpp showLineNumbers 
template<std::integral T>
T twice(T value) {
    return value * 2;
}
```

Concepts are the modern, readable alternative to SFINAE.

:::success SFINAE Key Concepts

**Substitution failure** = template removed, not an error  
**Expression SFINAE** = check if expression is valid  
**std::enable_if** = conditionally enable templates  
**Detection idiom** = check for members/methods  
**std::void_t** = turn any type into void (SFINAE helper)  
**Trailing return** = perfect place for SFINAE checks  
**Concepts** = modern, cleaner alternative  
**Use cases** = overload resolution, trait detection, conditional compilation
:::