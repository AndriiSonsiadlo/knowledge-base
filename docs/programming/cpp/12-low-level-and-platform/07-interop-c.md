---
id: interop-c
title: C Interoperability
sidebar_label: C Interoperability
sidebar_position: 7
tags: [cpp, c-interop, extern-c, abi, compatibility]
---

# C Interoperability

C++ can call C functions and vice versa using `extern "C"` linkage. Essential for using C libraries, system APIs, and creating C-compatible interfaces.

:::info Name Mangling
C++ mangles function names (see [Name Mangling](../01-toolchain-and-build/name-mangling.md)). C doesn't. `extern "C"` disables mangling for C compatibility.
:::

## extern "C" Linkage
```cpp showLineNumbers
// C++ function (mangled)
void foo(int x);
// Mangled name: _Z3fooi

// C linkage (not mangled)
extern "C" void foo(int x);
// Actual name: foo
```

### Single Declaration
```cpp showLineNumbers
extern "C" void c_function(int x);

void c_function(int x) {
    // Implementation
}
```

### Block Declaration
```cpp showLineNumbers
extern "C" {
    void function1(int x);
    void function2(double y);
    int function3();
}
```

## Calling C from C++
```cpp showLineNumbers
// c_library.h (C header)
#ifdef __cplusplus
extern "C" {
#endif

void c_function(int x);
int c_calculate(double a, double b);

#ifdef __cplusplus
}
#endif

// main.cpp (C++ code)
#include "c_library.h"

int main() {
    c_function(42);               // ✅ Works
    int result = c_calculate(3.14, 2.71);  // ✅ Works
}
```

**Pattern**: Header works in both C and C++.

## Calling C++ from C

C++ must expose C-compatible interface.
```cpp showLineNumbers
// cpp_library.h
#ifdef __cplusplus
extern "C" {
#endif

typedef struct OpaqueHandle OpaqueHandle;

OpaqueHandle* create_object();
void destroy_object(OpaqueHandle* obj);
int object_calculate(OpaqueHandle* obj, int x);

#ifdef __cplusplus
}
#endif

// cpp_library.cpp
class MyClass {
    int value;
public:
    MyClass() : value(0) {}
    int calculate(int x) { return x + value; }
};

extern "C" {
    OpaqueHandle* create_object() {
        return reinterpret_cast<OpaqueHandle*>(new MyClass());
    }
    
    void destroy_object(OpaqueHandle* obj) {
        delete reinterpret_cast<MyClass*>(obj);
    }
    
    int object_calculate(OpaqueHandle* obj, int x) {
        return reinterpret_cast<MyClass*>(obj)->calculate(x);
    }
}

// main.c (pure C)
#include "cpp_library.h"

int main() {
    OpaqueHandle* obj = create_object();
    int result = object_calculate(obj, 42);
    destroy_object(obj);
    return 0;
}
```

**Pattern**: Opaque handle hides C++ class from C code.

## What Works in extern "C"
```cpp showLineNumbers
// ✅ OK: Plain functions
extern "C" void func(int x);

// ✅ OK: Function pointers
extern "C" typedef void (*callback_t)(int);

// ✅ OK: POD structs
extern "C" struct Point {
    int x, y;
};

// ❌ Can't: Overloaded functions
extern "C" {
    void func(int x);      // ❌ Error: overloading
    void func(double x);   // not allowed in C
}

// ❌ Can't: Member functions
extern "C" {
    class Widget {
        void method();  // ❌ Can't use extern "C" on members
    };
}

// ❌ Can't: Templates
extern "C" {
    template<typename T>
    void func(T x);  // ❌ Error: templates not in C
}
```

**Restrictions**: Only plain functions, no overloading, templates, or members.

## Type Compatibility
```cpp showLineNumbers
// ✅ Compatible types
extern "C" {
    // C fundamental types work
    void func(int, double, char);
    
    // POD structs work
    struct Data {
        int x;
        double y;
    };
    
    // Pointers work
    void process(int* arr, size_t len);
}

// ❌ Incompatible types
extern "C" {
    // void func(std::string s);  // ❌ C++ class
    // void func(std::vector<int> v);  // ❌ STL
}
```

## Common Patterns

### 1. Wrapping C Library
```cpp showLineNumbers
// c_math.h (C library)
extern "C" {
    double c_sqrt(double x);
    double c_sin(double x);
}

// cpp_wrapper.hpp (C++ wrapper)
#include "c_math.h"
#include <stdexcept>

namespace math {
    inline double sqrt(double x) {
        if (x < 0) throw std::invalid_argument("Negative sqrt");
        return c_sqrt(x);
    }
    
    inline double sin(double x) {
        return c_sin(x);
    }
}
```

### 2. C++ Class → C Interface
```cpp showLineNumbers
// calculator.hpp (C++ class)
class Calculator {
    int value;
public:
    Calculator() : value(0) {}
    void add(int x) { value += x; }
    int get() const { return value; }
};

// calculator_c.h (C interface)
#ifdef __cplusplus
extern "C" {
#endif

typedef struct Calculator_t Calculator_t;

Calculator_t* Calculator_create();
void Calculator_destroy(Calculator_t* calc);
void Calculator_add(Calculator_t* calc, int x);
int Calculator_get(const Calculator_t* calc);

#ifdef __cplusplus
}
#endif

// calculator_c.cpp (C interface implementation)
extern "C" {
    Calculator_t* Calculator_create() {
        return reinterpret_cast<Calculator_t*>(new Calculator());
    }
    
    void Calculator_destroy(Calculator_t* calc) {
        delete reinterpret_cast<Calculator*>(calc);
    }
    
    void Calculator_add(Calculator_t* calc, int x) {
        reinterpret_cast<Calculator*>(calc)->add(x);
    }
    
    int Calculator_get(const Calculator_t* calc) {
        return reinterpret_cast<const Calculator*>(calc)->get();
    }
}
```

### 3. Callback Functions
```cpp showLineNumbers
// C library expecting callback
extern "C" {
    typedef void (*callback_t)(int value, void* user_data);
    void register_callback(callback_t cb, void* data);
}

// C++ usage
class Handler {
public:
    void onValue(int value) {
        std::cout << "Got: " << value << "\n";
    }
};

extern "C" void callback_wrapper(int value, void* user_data) {
    Handler* handler = static_cast<Handler*>(user_data);
    handler->onValue(value);
}

Handler h;
register_callback(callback_wrapper, &h);
```

## Exceptions and extern "C"
```cpp showLineNumbers
// ❌ Don't throw exceptions across C boundary
extern "C" void risky() {
    throw std::runtime_error("Error");  // ❌ UB if called from C!
}

// ✅ Catch exceptions, return error codes
extern "C" int safe_function(int x) {
    try {
        might_throw(x);
        return 0;  // Success
    } catch (...) {
        return -1;  // Error
    }
}
```

**Rule**: Never let exceptions cross `extern "C"` boundary.

## Linking C and C++ Code
```bash
# Compile C code
gcc -c library.c -o library.o

# Compile C++ code
g++ -c main.cpp -o main.o

# Link together (use C++ linker)
g++ main.o library.o -o app

# Or link C++ library with C code
gcc main.c -L. -lmycpplib -lstdc++ -o app
```

## Common Pitfalls
```cpp showLineNumbers
// ❌ Forgetting extern "C"
// header.h
void func(int x);  // C++ mangled name

// main.c (C code)
void func(int x);  // C linker looks for unmangled name
// Linking error: undefined reference

// ✅ Fixed
// header.h
extern "C" void func(int x);
```

## Best Practices

:::success DO
- Use `extern "C"` for C compatibility
- Wrap with `#ifdef __cplusplus`
- Use opaque pointers for C++ classes
- Return error codes, not exceptions
- Document C API clearly
  :::

:::danger DON'T
- Throw exceptions across boundary
- Expose C++ types (std::string, std::vector) to C
- Use function overloading in extern "C"
- Forget to use C++ linker when mixing
- Assume same ABI across compilers
  :::

## Summary

- `extern "C"` provides C-compatible linkage by disabling name mangling. Essential for calling C from C++ and vice versa. 
- **C→C++**: Wrap C headers with `extern "C"`.
- **C++→C**: Create C interface with opaque handles for C++ objects.
- **Restrictions**: No overloading, templates, or member functions in `extern "C"`.
- Never throw exceptions across boundary - use error codes.
- Use C++ linker when linking mixed code.
- Common pattern: opaque handle + C-style functions wrapping C++ class.

:::info
Memory aid: `No MOTE` (what C can't handle)
- `M` = Member functions (only free functions)
- `O` = Overloading (one name, one function)
- `T` = Templates (C has no templates)
- `E` = Exceptions (catch before boundary)
:::

```cpp
// Interview answer:
// "extern 'C' disables C++ name mangling for C compatibility.
// C calls C++: wrap C headers in extern 'C' blocks. C++ calls C:
// create C interface with opaque pointers hiding C++ classes.
// Can't use overloading, templates, or members in extern 'C'.
// Never throw exceptions across boundary - catch and return
// error codes. Use C++ linker when mixing. Pattern: opaque
// handle typedef, create/destroy/operate functions wrapping
// C++ class methods."
```