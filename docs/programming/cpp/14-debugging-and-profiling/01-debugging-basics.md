---
id: debugging-basics
title: Debugging Basics
sidebar_label: Debugging Basics
sidebar_position: 1
tags: [cpp, debugging, gdb, breakpoints, watchpoints]
---

# Debugging Basics

Systematic techniques for finding and fixing bugs: compilation flags, assertions, logging, debuggers. Understanding debugging tools is essential for efficient development.

:::info Debug vs Release
**Debug builds** (`-g -O0`): symbols, no optimization, debugger-friendly  
**Release builds** (`-O2/-O3`): optimized, hard to debug, production-ready
:::

## Compilation Flags
```bash
# Debug build (full symbols, no optimization)
g++ -g -O0 -Wall -Wextra program.cpp -o program_debug

# Debug with sanitizers
g++ -g -O0 -fsanitize=address,undefined program.cpp -o program

# Release with debug symbols
g++ -g -O2 program.cpp -o program_release

# Disable assertions (production)
g++ -O2 -DNDEBUG program.cpp -o program
```

**Flags:**
- `-g` = Debug symbols (for debugger)
- `-O0` = No optimization (easier debugging)
- `-Wall -Wextra` = Enable warnings
- `-DNDEBUG` = Disable asserts

## Assertions

Catch logic errors early.
```cpp showLineNumbers
#include <cassert>

void process(int* ptr, size_t size) {
    assert(ptr != nullptr);           // Precondition
    assert(size > 0);                 // Precondition
    
    for (size_t i = 0; i < size; ++i) {
        assert(i < size);             // Invariant check
        process_item(ptr[i]);
    }
}

// Custom assertion with message
#define ASSERT_MSG(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cerr << "Assertion failed: " << msg \
                      << " at " << __FILE__ << ":" << __LINE__ << "\n"; \
            std::abort(); \
        } \
    } while (0)

ASSERT_MSG(x > 0, "x must be positive");
```

**Production**: Asserts disabled with `-DNDEBUG` (no runtime cost).

## Static Assertions

Compile-time checks.
```cpp showLineNumbers
static_assert(sizeof(int) == 4, "int must be 4 bytes");
static_assert(std::is_trivially_copyable_v<Point>);

template<typename T>
void process(T value) {
    static_assert(std::is_integral_v<T>, "T must be integral");
}
```

## Logging
```cpp showLineNumbers
// Simple logging
#ifdef DEBUG
    #define LOG(msg) std::cout << "[DEBUG] " << msg << "\n"
#else
    #define LOG(msg) do {} while(0)
#endif

LOG("Processing value: " << x);

// Conditional compilation
#ifdef DEBUG
    std::cout << "Debug: x = " << x << ", y = " << y << "\n";
#endif
```

### Log Levels
```cpp showLineNumbers
enum LogLevel { ERROR, WARN, INFO, DEBUG };

class Logger {
    LogLevel level;
public:
    void log(LogLevel lvl, const std::string& msg) {
        if (lvl <= level) {
            std::cout << levelStr(lvl) << ": " << msg << "\n";
        }
    }
};

logger.log(DEBUG, "Entering function");
logger.log(ERROR, "Critical failure");
```

## Defensive Programming
```cpp showLineNumbers
void process(const std::vector<int>& data) {
    // Check preconditions
    if (data.empty()) {
        throw std::invalid_argument("Empty vector");
    }
    
    // Check invariants during processing
    for (size_t i = 0; i < data.size(); ++i) {
        assert(i < data.size());  // Redundant but catches bugs
        // process...
    }
    
    // Check postconditions
    assert(result.size() == data.size());
}
```

## Debugging Techniques

### 1. Print Debugging
```cpp showLineNumbers
void debug_vector(const std::vector<int>& v) {
    std::cout << "Vector[" << v.size() << "]: ";
    for (int x : v) std::cout << x << " ";
    std::cout << "\n";
}

// Trace execution
std::cout << "Entering function " << __func__ << "\n";
std::cout << "File: " << __FILE__ << " Line: " << __LINE__ << "\n";
```

### 2. Binary Search
```cpp showLineNumbers
// Comment out half the code
void complex_function() {
    part1();
    // part2();  // Commented out
    // part3();
    // part4();
}
// Bug still happens? → Bug in part1
// Bug gone? → Bug in part2/3/4
```

### 3. Rubber Duck Debugging

Explain code line-by-line to someone (or something). Often reveals the bug.

### 4. Minimal Reproducible Example
```cpp showLineNumbers
// Original: 1000 lines
// Minimal: 20 lines that still show bug

#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.push_back(1);
    std::cout << v[5] << "\n";  // Bug: out of bounds
}
```

## Common Bug Patterns

### Off-by-One Errors
```cpp showLineNumbers
// ❌ Wrong
for (int i = 0; i <= arr.size(); ++i) {  // <= is wrong!
    arr[i] = 0;
}

// ✅ Correct
for (int i = 0; i < arr.size(); ++i) {
    arr[i] = 0;
}
```

### Uninitialized Variables
```cpp showLineNumbers
// ❌ Bug
int x;
std::cout << x;  // Undefined behavior

// ✅ Fixed
int x = 0;
std::cout << x;
```

### Use After Free
```cpp showLineNumbers
// ❌ Bug
int* p = new int(42);
delete p;
std::cout << *p;  // Use after free!

// ✅ Fixed
int* p = new int(42);
delete p;
p = nullptr;
// Or use smart pointer
auto p = std::make_unique<int>(42);
```

### Memory Leaks
```cpp showLineNumbers
// ❌ Bug
void leak() {
    int* p = new int(42);
    if (error) return;  // Forgot to delete!
    delete p;
}

// ✅ Fixed
void no_leak() {
    auto p = std::make_unique<int>(42);
    if (error) return;  // Auto-deleted
}
```

## Quick Debugging Checklist

:::success Before Using Debugger
1. **Read error message** completely
2. **Check recent changes** (version control)
3. **Add print statements** at key points
4. **Check assumptions** (assert preconditions)
5. **Minimize** to smallest reproducing code
6. **Search** error message online
:::

## Preprocessor Debugging
```cpp showLineNumbers
// Show macro expansion
g++ -E program.cpp

// Show included files
g++ -H program.cpp

// Show defines
g++ -dM -E - < /dev/null
```

## Summary
:::info
- **Build flags**:
  - `-g` (symbols)
  - `-O0` (no optimization)
  - `-Wall` (warnings)
- **Assertions**:
  - Runtime checks (disabled in release)
  - `static_assert` (compile-time)
- **Logging**: Conditional with DEBUG macro, log levels.
- **Techniques**:
  - Print debugging (quick)
  - binary search (isolate)
  - minimal example (simplify)
- **Common bugs**:
  - Off-by-one
  - uninitialized vars
  - use-after-free
  - leaks
- Use debugger when prints aren't enough.
:::

```cpp
// Debugging flow:
// 1. Reproduce bug consistently
// 2. Isolate with prints/binary search
// 3. Minimize to smallest example
// 4. Use debugger for complex cases
// 5. Fix and add regression test
```
