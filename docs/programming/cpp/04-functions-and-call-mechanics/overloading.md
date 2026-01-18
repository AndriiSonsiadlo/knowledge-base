---
id: function-overloading
title: Function Overloading
sidebar_label: Overloading
sidebar_position: 3
tags: [c++, functions, overloading, overload-resolution]
---

# Function Overloading

Function overloading allows multiple functions with the same name but different parameters. The compiler selects the best match based on arguments.

:::info Compile-Time Selection
Overload resolution happens at compile-time based on argument types, not runtime values.
:::

## Basic Overloading

```cpp
void print(int x) {
    std::cout << "int: " << x << "\n";
}

void print(double x) {
    std::cout << "double: " << x << "\n";
}

void print(const char* x) {
    std::cout << "string: " << x << "\n";
}

print(42);       // Calls print(int)
print(3.14);     // Calls print(double)
print("hello");  // Calls print(const char*)
```

---

## Overloading Rules

Functions can differ by:

✅ **Number of parameters**
```cpp
void func(int x);
void func(int x, int y);
```

✅ **Type of parameters**
```cpp
void func(int x);
void func(double x);
```

✅ **const/volatile qualifiers**
```cpp
void func(int x);
void func(const int x);  // ❌ Same (top-level const ignored)

void func(int* p);
void func(const int* p);  // ✅ Different (low-level const)

void process(std::string& s);      // Lvalue
void process(const std::string& s); // Lvalue (different)
void process(std::string&& s);     // Rvalue
```

✅ **Reference qualifiers**
```cpp
void func(int& x);   // Lvalue reference
void func(int&& x);  // Rvalue reference
```

❌ **Return type only** (not allowed)
```cpp
int func(int x);
double func(int x);  // ❌ Error: differs only by return type
```

---

## Overload Resolution Process

1. **Find candidates**: Functions with matching name
2. **Filter viable**: Can be called with given arguments
3. **Select best match**: Most specific match wins

```cpp
void func(int x);          // #1
void func(double x);       // #2
void func(int x, int y);   // #3

func(42);        // Calls #1: exact match
func(3.14);      // Calls #2: exact match
func(42, 10);    // Calls #3: exact match
func('c');       // Calls #1: char promotes to int
```

---

## Exact Match vs Conversion

```cpp
void print(int x);
void print(double x);

print(42);       // Exact match → print(int)
print(3.14);     // Exact match → print(double)
print(3.14f);    // float → double conversion → print(double)
print('A');      // char → int promotion → print(int)
```

**Ranking**:
1. Exact match
2. Promotions (char→int, float→double)
3. Standard conversions (int→double)
4. User-defined conversions

---

## Ambiguous Overloads

```cpp
void func(int x, double y);
void func(double x, int y);

func(42, 3.14);    // ✅ OK: exact match on both
// func(42, 42);   // ❌ Error: ambiguous!
                   // Both require one conversion
```

### Resolving Ambiguity

```cpp
// Explicit cast
func(42, static_cast<double>(42));  // Calls first overload
func(static_cast<double>(42), 42);  // Calls second overload

// Or add more overloads
void func(int x, int y);  // Exact match for func(42, 42)
```

---

## const Overloading

```cpp
class Widget {
public:
    int getValue() const {        // const version
        std::cout << "const\n";
        return value;
    }
    
    int& getValue() {             // non-const version
        std::cout << "non-const\n";
        return value;
    }
    
private:
    int value = 42;
};

Widget w;
w.getValue() = 100;  // Calls non-const, returns int&

const Widget cw;
int x = cw.getValue();  // Calls const version
```

---

## Reference Overloading

```cpp
void process(const std::string& s) {
    std::cout << "lvalue: " << s << "\n";
}

void process(std::string&& s) {
    std::cout << "rvalue: " << s << "\n";
    // Can move from s
}

std::string str = "hello";
process(str);              // Calls lvalue version
process("temporary");      // Calls rvalue version
process(std::move(str));   // Calls rvalue version
```

---

## Pointer vs Array

```cpp
void func(int* arr);
void func(int arr[]);     // Same as int*
void func(int arr[10]);   // Still same as int*

// All three are identical - no overloading!

void func(int (&arr)[10]); // ✅ Different: reference to array
```

---

## Default Arguments

```cpp
void func(int x, int y = 0);
void func(int x);  // ❌ Error: ambiguous with func(x, 0)

// Call
func(42);  // Which one? Ambiguous!
```

---

## Template Overloading

```cpp
template<typename T>
void func(T x) {
    std::cout << "template\n";
}

void func(int x) {
    std::cout << "non-template\n";
}

func(42);    // Calls non-template (exact match preferred)
func(3.14);  // Calls template (only option)
```

**Rule**: Non-template functions preferred over templates for exact matches.

---

## Variadic Overloading

```cpp
void print(int x) {
    std::cout << x << "\n";
}

template<typename T, typename... Args>
void print(T first, Args... rest) {
    std::cout << first << ", ";
    print(rest...);  // Recursive
}

print(1, 2, 3, 4);  // 1, 2, 3, 4
```

---

## Name Hiding in Inheritance

```cpp
class Base {
public:
    void func(int x) {
        std::cout << "Base::func\n";
    }
};

class Derived : public Base {
public:
    void func(double x) {  // Hides Base::func!
        std::cout << "Derived::func\n";
    }
};

Derived d;
d.func(42);    // Calls Derived::func(double), not Base::func(int)!
               // Even though int→int is better than int→double
```

**Solution**: Use `using` declaration:

```cpp
class Derived : public Base {
public:
    using Base::func;  // Bring Base::func into scope
    
    void func(double x) {
        std::cout << "Derived::func\n";
    }
};

Derived d;
d.func(42);  // Now calls Base::func(int) - better match
```

---

## Operator Overloading

```cpp
class Complex {
    double real, imag;
public:
    Complex(double r, double i) : real(r), imag(i) {}
    
    // Member function
    Complex operator+(const Complex& other) const {
        return Complex(real + other.real, imag + other.imag);
    }
    
    // Can also overload as friend/global function
};

Complex a(1, 2), b(3, 4);
Complex c = a + b;  // Calls operator+
```

---

## Best Practices

:::success DO
- Overload for different types/counts
- Use const overloading for getter/setter pairs
- Use reference qualifiers (lvalue/rvalue) for optimization
- Keep overload sets intuitive
  :::

:::danger DON'T
- Overload with same parameter types (differs only by names)
- Create ambiguous overload sets
- Differ only by return type
- Use overloading when different names are clearer
  :::

---

## Common Pitfalls

### Surprising Conversions

```cpp
void func(long x);
void func(double x);

func(42);  // ❌ Ambiguous! int→long and int→double both conversions
```

### Pointer/Bool Conversion

```cpp
void func(int x);
void func(bool x);

func(nullptr);  // ❌ Ambiguous in some cases
```

### Forwarding References

```cpp
template<typename T>
void func(T&& x);  // Universal reference

void func(int& x);

int x = 42;
func(x);  // Which one? Template is exact match!
```

---

## Summary

Function overloading:
- **Same name, different parameters**
- Resolved at **compile-time**
- Ranked: Exact > Promotion > Conversion

**Can overload on**:
- Parameter count
- Parameter types
- const qualifiers (low-level)
- Reference type (lvalue/rvalue)

**Cannot overload on**:
- Return type only
- Parameter names
- Top-level const

```cpp
// Good overload set
void process(int x);              // Integer
void process(double x);           // Floating-point
void process(const std::string& s); // String lvalue
void process(std::string&& s);    // String rvalue
```

Overloading enables type-safe, expressive APIs while maintaining performance through compile-time resolution.