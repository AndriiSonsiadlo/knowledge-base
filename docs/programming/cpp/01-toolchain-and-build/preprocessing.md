---
id: preprocessing
title: Preprocessing in C++
sidebar_label: Preprocessing
sidebar_position: 2
tags: [c++, preprocessor, macros, includes, compilation]
---

# Preprocessing in C++

The preprocessor is a text manipulation tool that runs before compilation. It handles `#include`, `#define`, `#ifdef`, and other directives, producing pure C++ code for the compiler.

:::info Text Substitution
The preprocessor doesn't understand C++ - it only does text replacement. This makes it powerful but dangerous if misused.
:::

## Preprocessor Directives

All preprocessor commands start with `#` and are processed before compilation:

```cpp
#include <iostream>      // File inclusion
#define MAX 100          // Macro definition
#ifdef DEBUG             // Conditional compilation
#pragma once             // Compiler-specific directive
```

---

## File Inclusion (#include)

`#include` literally copies the entire contents of a file into your source code.

### Angle Brackets vs Quotes

```cpp
#include <iostream>      // System/standard library headers
                         // Searches: /usr/include, /usr/local/include

#include "myheader.h"    // User headers
                         // Searches: Current directory first, then system paths
```

**How it works**: The preprocessor finds the file and replaces the `#include` line with the file's contents.

```cpp
// Before preprocessing
#include <iostream>
int main() {
    std::cout << "Hello\n";
}

// After preprocessing (simplified - actually ~10,000 lines)
namespace std {
    // ... entire iostream implementation ...
}
int main() {
    std::cout << "Hello\n";
}
```

### Include Guard Problem

Without protection, including the same header multiple times causes redefinition errors:

```cpp
// widget.h
class Widget {
    int value;
};

// main.cpp
#include "widget.h"
#include "widget.h"  // ❌ Error: redefinition of 'class Widget'
```

**Solution 1: Include Guards**

```cpp
// widget.h
#ifndef WIDGET_H
#define WIDGET_H

class Widget {
    int value;
};

#endif  // WIDGET_H
```

First inclusion defines `WIDGET_H`, second inclusion skips the content because `WIDGET_H` is already defined.

**Solution 2: #pragma once (Modern)**

```cpp
// widget.h
#pragma once  // Non-standard but universally supported

class Widget {
    int value;
};
```

`#pragma once` is simpler and faster than include guards. All modern compilers support it.

---

## Macros (#define)

Macros perform text substitution before compilation. They're useful but dangerous - prefer `const` or `inline` functions when possible.

### Object-Like Macros

```cpp
#define PI 3.14159
#define MAX_SIZE 1000

double area = PI * r * r;  // Becomes: 3.14159 * r * r

// ✅ Better alternative: const
const double PI = 3.14159;
constexpr int MAX_SIZE = 1000;
```

The preprocessor replaces `PI` with `3.14159` everywhere. Unlike `const`, macros have no type safety.

### Function-Like Macros

```cpp
#define SQUARE(x) ((x) * (x))

int result = SQUARE(5);    // Becomes: ((5) * (5)) = 25
int bad = SQUARE(2 + 3);   // Becomes: ((2 + 3) * (2 + 3)) = 25 ✅

// ⚠️ Without parentheses - bug!
#define BAD_SQUARE(x) x * x
int oops = BAD_SQUARE(2 + 3);  // Becomes: 2 + 3 * 2 + 3 = 11 ❌

// ✅ Better: inline function
inline int square(int x) { return x * x; }
```

**Always use parentheses** in macro arguments and the entire expression. Better yet, use inline functions which are type-safe.

### Macro Pitfalls

```cpp
#define MAX(a, b) ((a) > (b) ? (a) : (b))

// Problem 1: Multiple evaluation
int x = 5;
int m = MAX(x++, 10);  // Expands to: ((x++) > (10) ? (x++) : (10))
                       // x incremented twice if x > 10! 

// Problem 2: No type checking
MAX("hello", 42);  // Compiles but nonsensical!

// ✅ Solution: template function
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
```

---

## Conditional Compilation

Compile different code based on conditions - useful for platform-specific code, debug builds, and feature flags.

### Basic Conditionals

```cpp
#define DEBUG 1

int main() {
    #ifdef DEBUG
        std::cout << "Debug mode\n";  // Included if DEBUG defined
    #endif
    
    #ifndef RELEASE
        doDebugChecks();  // Included if RELEASE NOT defined
    #endif
    
    #if DEBUG == 1
        verboseLogging();  // Included if DEBUG equals 1
    #elif DEBUG == 2
        minimalLogging();
    #else
        noLogging();
    #endif
}
```

The preprocessor evaluates these conditions and removes code from branches not taken. Dead code never reaches the compiler.

### Platform-Specific Code

```cpp
#ifdef _WIN32
    #include <windows.h>
    void platformInit() {
        // Windows-specific code
    }
#elif __linux__
    #include <unistd.h>
    void platformInit() {
        // Linux-specific code
    }
#elif __APPLE__
    #include <mach-o/dyld.h>
    void platformInit() {
        // macOS-specific code
    }
#endif
```

This allows one codebase to compile on multiple platforms with platform-specific implementations.

### Debug vs Release

```cpp
class Widget {
    void process() {
        #ifdef DEBUG
            std::cout << "Processing widget " << id << "\n";
            validateState();
        #endif
        
        // Production code
        doWork();
    }
};

// Compile with debug
g++ -DDEBUG main.cpp

// Compile without debug (no logging, no validation)
g++ main.cpp
```

The `-DDEBUG` flag defines `DEBUG` during compilation, enabling debug code. Release builds omit it for performance.

---

## Predefined Macros

The preprocessor provides standard macros for debugging and meta-information:

```cpp
#include <iostream>

void logError() {
    std::cout << "Error at " 
              << __FILE__      // Current filename
              << ":" 
              << __LINE__      // Current line number
              << " in " 
              << __func__      // Current function name (C99)
              << "\n";
}

void showCompileInfo() {
    std::cout << "Compiled on " 
              << __DATE__      // "Feb 15 2024"
              << " at " 
              << __TIME__      // "14:30:00"
              << "\n";
              
    std::cout << "C++ version: " 
              << __cplusplus   // 201703L for C++17, 202002L for C++20
              << "\n";
}
```

These macros are replaced with actual values during preprocessing. Useful for logging, assertions, and version checks.

---

## Stringification and Token Pasting

Advanced macro techniques for manipulating tokens.

### Stringification (#)

Converts macro argument to string literal:

```cpp
#define STRINGIFY(x) #x
#define LOG(var) std::cout << #var << " = " << var << "\n"

int main() {
    int count = 42;
    
    LOG(count);  // Expands to: std::cout << "count" << " = " << count << "\n"
    // Output: count = 42
    
    std::string s = STRINGIFY(hello);  // Becomes: "hello"
}
```

The `#` operator turns the token into a string, preserving whitespace and quotes.

### Token Pasting (##)

Concatenates tokens to create new identifiers:

```cpp
#define DECLARE_VAR(type, name, suffix) \
    type name##suffix

DECLARE_VAR(int, value, _tmp);  // Expands to: int value_tmp;
DECLARE_VAR(double, pi, _val);  // Expands to: double pi_val;

// Useful for generating similar code
#define PROPERTY(type, name) \
    private: type m_##name; \
    public: \
        type get##name() const { return m_##name; } \
        void set##name(type value) { m_##name = value; }

class Widget {
    PROPERTY(int, Width)   // Generates getWidth/setWidth
    PROPERTY(int, Height)  // Generates getHeight/setHeight
};
```

---

## #pragma Directives

Compiler-specific directives for control and optimization:

```cpp
#pragma once  // Include guard alternative (universal support)

#pragma pack(push, 1)  // Pack struct without padding
struct Data {
    char c;
    int i;
};  // Size: 5 bytes instead of 8
#pragma pack(pop)

#pragma GCC optimize("O3")  // Force optimization for next function

#pragma message("Compiling with debug mode")  // Compile-time message

#pragma warning(push)
#pragma warning(disable: 4996)  // MSVC: Disable specific warning
// ... code that triggers warning ...
#pragma warning(pop)
```

---

## Viewing Preprocessor Output

```bash
# See what preprocessor produces
g++ -E main.cpp -o main.i

# Show only user code (filter out system headers)
g++ -E main.cpp | grep -v "^#"

# Show include tree
g++ -H main.cpp

# Show all predefined macros
g++ -dM -E - < /dev/null
```

This shows exactly what the compiler sees after preprocessing. Useful for debugging macro issues.

---

## Best Practices

:::success DO
- Use `#pragma once` for include guards (simpler)
- Use `const`/`constexpr` instead of `#define` for constants
- Use `inline` functions instead of function macros
- Use `#ifdef` for platform-specific code
- Document complex macros thoroughly
  :::

:::danger DON'T
- Use macros when templates/inline functions work
- Forget parentheses in macro arguments
- Rely on macro side effects (like `x++`)
- Use macros for type-unsafe operations
- Create multi-line macros without backslashes
  :::

### Modern Alternatives

```cpp
// ❌ Old style
#define MAX 100
#define SQUARE(x) ((x) * (x))

// ✅ Modern C++
constexpr int MAX = 100;
constexpr int square(int x) { return x * x; }

// ❌ Old debug logging
#ifdef DEBUG
    #define LOG(x) std::cout << x << "\n"
#else
    #define LOG(x)
#endif

// ✅ Modern C++17
if constexpr (DEBUG) {
    std::cout << value << "\n";
}
```

---

## Common Patterns

### Debug Assertions

```cpp
#ifdef DEBUG
    #define ASSERT(condition) \
        if (!(condition)) { \
            std::cerr << "Assertion failed: " #condition \
                      << " at " << __FILE__ << ":" << __LINE__ << "\n"; \
            std::abort(); \
        }
#else
    #define ASSERT(condition) ((void)0)  // No-op in release
#endif

ASSERT(ptr != nullptr);
ASSERT(size > 0);
```

### Feature Detection

```cpp
#if __cplusplus >= 202002L
    // C++20 code
    #define HAS_CONCEPTS 1
    template<std::integral T>
    void process(T value) { }
#else
    // Pre-C++20 fallback
    #define HAS_CONCEPTS 0
    template<typename T>
    void process(T value) { }
#endif
```

---

## Summary

The preprocessor:
- Runs before compilation as **text manipulation**
- Handles `#include` (file insertion), `#define` (macros), `#ifdef` (conditionals)
- Has **no understanding of C++** - purely textual
- Powerful but **dangerous** - prefer modern C++ alternatives
- Essential for platform-specific code and conditional compilation

**Key Rules**:
- Always use `#pragma once` or include guards
- Prefer `const`/`constexpr`/`inline` over macros
- Parenthesize all macro arguments
- Test preprocessor output with `g++ -E`