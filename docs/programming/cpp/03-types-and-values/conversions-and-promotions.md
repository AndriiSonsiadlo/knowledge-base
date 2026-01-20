---
id: conversions-and-promotions
title: Type Conversions and Promotions
sidebar_label: Conversions
sidebar_position: 7
tags: [c++, conversions, casting, promotion, implicit]
---

# Type Conversions and Promotions

C++ performs automatic (implicit) and manual (explicit) type conversions. Understanding these prevents bugs and data loss.

## Implicit Conversions

Automatic conversions performed by compiler:

```cpp showLineNumbers 
int x = 3.14;        // double → int (truncates to 3)
double y = 5;        // int → double (promotes to 5.0)
float f = 3.14;      // double → float (may lose precision)

bool b = 42;         // int → bool (true)
int i = true;        // bool → int (1)
```

---

## Integral Promotion

Small integer types promote to `int` in expressions:

```cpp showLineNumbers 
char c = 'A';
short s = 100;

// Both promote to int before operation
int result = c + s;  // char→int, short→int, then add

// Even in this case:
char x = 1, y = 2;
auto z = x + y;      // z is int, not char!
```

---

## Usual Arithmetic Conversions

Rules for mixed-type operations:

```cpp showLineNumbers 
int x = 5;
double y = 2.5;

auto result = x + y;  // int→double, result is double (7.5)

// Hierarchy (smaller converts to larger)
// long double > double > float > unsigned long > long > unsigned > int
```

---

## Narrowing Conversions

Losing information (often warns):

```cpp showLineNumbers 
int x = 1000;
char c = x;         // ⚠️ Truncates (c = -24 on 8-bit char)

double d = 3.14;
int i = d;          // ⚠️ Truncates fractional part (i = 3)

// Brace initialization prevents narrowing
int y{3.14};        // ❌ Error: narrowing
int y = {3.14};     // ❌ Error
int y = 3.14;       // ⚠️ Warning but allowed
```

---

## Explicit Conversions (Casts)

### C++ Style Casts (Preferred)

```cpp showLineNumbers 
double d = 3.14;

// static_cast - compile-time conversion
int x = static_cast<int>(d);  // 3

// const_cast - add/remove const
const int* cp = &x;
int* p = const_cast<int*>(cp);  // Remove const

// reinterpret_cast - reinterpret bits
int* ip = reinterpret_cast<int*>(0x12345678);

// dynamic_cast - runtime polymorphic cast
Derived* d = dynamic_cast<Derived*>(base_ptr);
```

### C-Style Cast (Avoid)

```cpp showLineNumbers 
double d = 3.14;
int x = (int)d;      // C-style cast (works but avoid)
```

Use C++ casts for:
- Clarity of intent
- Easier to search (`grep static_cast`)
- Safer (more compile-time checking)

---

## Pointer Conversions

```cpp showLineNumbers 
// Derived → Base (implicit, safe)
class Base {};
class Derived : public Base {};

Derived d;
Base* bp = &d;  // ✅ OK: upcast

// Base → Derived (requires cast, dangerous)
Base b;
Derived* dp = static_cast<Derived*>(&b);  // ⚠️ Unsafe if b not Derived

// void* ↔ other pointers
int x = 42;
void* vp = &x;                     // Implicit
int* ip = static_cast<int*>(vp);   // Explicit back

// nullptr converts to any pointer
int* ptr = nullptr;  // OK
```

---

## Boolean Conversions

```cpp showLineNumbers 
// To bool
bool b1 = 42;        // true (non-zero → true)
bool b2 = 0;         // false
bool b3 = nullptr;   // false
bool b4 = "";        // true (pointer is non-null)

// From bool
int x = true;        // 1
int y = false;       // 0
```

---

## User-Defined Conversions

Classes can define conversions:

```cpp showLineNumbers 
class Fraction {
    int num, den;
public:
    Fraction(int n, int d = 1) : num(n), den(d) {}
    
    // Conversion to double
    operator double() const {
        return static_cast<double>(num) / den;
    }
};

Fraction f(1, 2);
double d = f;  // Calls operator double() → 0.5

// Prevent implicit: use explicit
explicit operator double() const { /*...*/ }
// Now requires: double d = static_cast<double>(f);
```

---

## Common Pitfalls

### Silent Truncation

```cpp showLineNumbers 
int x = 1000000;
short s = x;  // ⚠️ Overflow/truncation

// Use narrowing check
short s = static_cast<short>(x);  // Explicit
if (x > SHRT_MAX || x < SHRT_MIN) {
    // Handle overflow
}
```

### Signed/Unsigned

```cpp showLineNumbers 
int x = -1;
unsigned int y = 10;

if (x < y) {  // ⚠️ False! x converts to huge unsigned
    // Doesn't execute
}
```

### Double to Float

```cpp showLineNumbers 
double d = 1.23456789012345;
float f = d;  // Loses precision

std::cout << std::setprecision(20);
std::cout << f;  // 1.234567890... (fewer digits)
```

---

## Summary

**Implicit**: Automatic (int→double, char→int)  
**Explicit**: Manual casts (static_cast, etc.)  
**Promotion**: Small types → int  
**Narrowing**: Loses information (warns)

**Best practices**:
- Prefer C++ casts (`static_cast`)
- Watch for narrowing
- Avoid mixing signed/unsigned
- Use `explicit` for constructors/conversions

```cpp showLineNumbers 
// Good
double d = 3.14;
int x = static_cast<int>(d);  // Clear intent

// Avoid
int x = (int)d;  // C-style cast
int x = d;       // Implicit narrowing
```