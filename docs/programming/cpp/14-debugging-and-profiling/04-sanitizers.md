---
id: sanitizers
title: Sanitizers
sidebar_label: Sanitizers
sidebar_position: 4
tags: [sanitizers, asan, ubsan, tsan, msan, memory-safety]
---

# Sanitizers

Compiler-based runtime tools that detect bugs: memory errors, undefined behavior, data races, memory leaks. Much faster than Valgrind, part of GCC/Clang.

:::info Compile-Time Instrumentation
Sanitizers add checks during compilation. Catch bugs at runtime with minimal overhead (2-3x slowdown vs 10-100x for Valgrind).
:::

## Available Sanitizers

| Sanitizer | Flag | Detects |
|-----------|------|---------|
| **AddressSanitizer** | `-fsanitize=address` | Memory errors, leaks |
| **UndefinedBehaviorSanitizer** | `-fsanitize=undefined` | Undefined behavior |
| **ThreadSanitizer** | `-fsanitize=thread` | Data races |
| **MemorySanitizer** | `-fsanitize=memory` | Uninitialized reads |
| **LeakSanitizer** | `-fsanitize=leak` | Memory leaks only |

## AddressSanitizer (ASan)

Detects memory errors: buffer overflows, use-after-free, double-free, memory leaks.
```bash
# Compile with ASan
g++ -g -O1 -fsanitize=address program.cpp -o program

# Run
./program
```

### What ASan Catches
```cpp showLineNumbers
// 1. Heap buffer overflow
int* arr = new int[10];
arr[10] = 42;  // ❌ ASan: heap-buffer-overflow

// 2. Stack buffer overflow
int arr[10];
arr[10] = 42;  // ❌ ASan: stack-buffer-overflow

// 3. Use after free
int* p = new int(42);
delete p;
*p = 100;  // ❌ ASan: heap-use-after-free

// 4. Use after return
int* return_local_address() {
    int local = 42;
    return &local;  // ❌ ASan: stack-use-after-return
}

// 5. Double free
int* p = new int(42);
delete p;
delete p;  // ❌ ASan: attempting double-free

// 6. Memory leak
void leak() {
    int* p = new int(42);
    // Forgot to delete  // ❌ ASan: memory leak
}
```

### ASan Output
```
=================================================================
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000034
READ of size 4 at 0x602000000034 thread T0
    #0 0x400567 in main program.cpp:10
    #1 0x7f8b2e4b5b96 in __libc_start_main

0x602000000034 is located 0 bytes to the right of 40-byte region
allocated by thread T0 here:
    #0 0x7f8b2f0b2d38 in operator new[](unsigned long)
    #1 0x400557 in main program.cpp:8
=================================================================
```

**Reading ASan output:**
1. Error type (heap-buffer-overflow)
2. Location (program.cpp:10)
3. Allocation location (program.cpp:8)

## UndefinedBehaviorSanitizer (UBSan)

Catches undefined behavior: integer overflow, null pointer dereference, division by zero.
```bash
# Compile with UBSan
g++ -g -fsanitize=undefined program.cpp -o program
```

### What UBSan Catches
```cpp showLineNumbers
// 1. Signed integer overflow
int x = INT_MAX;
x++;  // ❌ UBSan: signed integer overflow

// 2. Division by zero
int x = 10 / 0;  // ❌ UBSan: division by zero

// 3. Null pointer dereference
int* p = nullptr;
*p = 42;  // ❌ UBSan: null pointer dereference

// 4. Shift errors
int x = 1 << 32;  // ❌ UBSan: shift exponent too large

// 5. Invalid enum value
enum Color { RED, GREEN, BLUE };
Color c = static_cast<Color>(100);  // ❌ UBSan: invalid enum value

// 6. Misaligned pointer
char buffer[10];
int* p = reinterpret_cast<int*>(buffer + 1);  // Misaligned
*p = 42;  // ❌ UBSan: misaligned address
```

### UBSan Options
```bash
# Specific checks only
g++ -fsanitize=signed-integer-overflow,null program.cpp

# Available checks:
# -fsanitize=shift
# -fsanitize=integer-divide-by-zero
# -fsanitize=null
# -fsanitize=alignment
# -fsanitize=bounds (array bounds)
```

## ThreadSanitizer (TSan)

Detects data races in multi-threaded programs.
```bash
# Compile with TSan
g++ -g -O1 -fsanitize=thread program.cpp -o program -pthread
```

### What TSan Catches
```cpp showLineNumbers
#include <thread>

int shared = 0;  // Shared, unprotected

void thread1() {
    shared = 1;  // ❌ TSan: data race
}

void thread2() {
    shared = 2;  // ❌ TSan: data race
}

int main() {
    std::thread t1(thread1);
    std::thread t2(thread2);
    t1.join();
    t2.join();
}
```

### TSan Output
```
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 4 at 0x7ffc1234 by thread T1:
    #0 thread1() program.cpp:5

  Previous write of size 4 at 0x7ffc1234 by thread T2:
    #0 thread2() program.cpp:9

  Location is global 'shared' at program.cpp:3
==================
```

## MemorySanitizer (MSan)

Detects reads of uninitialized memory. **Clang only**.
```bash
# Compile with MSan (Clang only)
clang++ -g -O1 -fsanitize=memory program.cpp -o program
```
```cpp showLineNumbers
void test() {
    int x;
    std::cout << x;  // ❌ MSan: use of uninitialized value
}
```

## LeakSanitizer (LSan)

Detects memory leaks. Included in ASan, can be used standalone.
```bash
# Standalone
g++ -g -fsanitize=leak program.cpp -o program

# Or use ASan (includes leak detection)
g++ -g -fsanitize=address program.cpp -o program
```
```cpp showLineNumbers
void leak() {
    int* p = new int[100];
    // Forgot to delete[]  // ❌ LSan: detected memory leaks
}
```

## Combining Sanitizers
```bash
# ASan + UBSan (most common combo)
g++ -g -O1 -fsanitize=address,undefined program.cpp -o program

# Can't combine TSan with ASan/MSan (incompatible)
# Use separately:
g++ -fsanitize=thread program.cpp       # For race detection
g++ -fsanitize=address program.cpp      # For memory errors
```

## Runtime Options

### ASan Options
```bash
# Detect leaks on exit
ASAN_OPTIONS=detect_leaks=1 ./program

# Abort on first error
ASAN_OPTIONS=halt_on_error=1 ./program

# Verbose output
ASAN_OPTIONS=verbosity=1 ./program

# Symbolize stack traces
ASAN_OPTIONS=symbolize=1 ./program

# Multiple options
ASAN_OPTIONS=detect_leaks=1:halt_on_error=0 ./program
```

### TSan Options
```bash
# Suppress specific warnings
TSAN_OPTIONS=suppressions=tsan.supp ./program

# tsan.supp file:
race:function_name
race:file.cpp

# Report thread names
TSAN_OPTIONS=report_thread_leaks=1 ./program
```

## Suppressing False Positives
```cpp showLineNumbers
// Suppress specific function (ASan)
__attribute__((no_sanitize("address")))
void external_library_function() {
    // ASan won't check this function
}

// Suppress UBSan checks
__attribute__((no_sanitize("undefined")))
void intentional_overflow() {
    int x = INT_MAX + 1;  // Won't report
}
```

## Performance Impact

| Sanitizer | Slowdown | Memory Overhead |
|-----------|----------|-----------------|
| **ASan** | 2x | 3x |
| **TSan** | 5-15x | 5-10x |
| **MSan** | 3x | 2x |
| **UBSan** | 1.2x | minimal |
| **LSan** | 1.1x | minimal |

## Integration with CI/CD
```bash
# CMake example
cmake_minimum_required(VERSION 3.15)
project(MyProject)

option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)

if(ENABLE_ASAN)
    add_compile_options(-fsanitize=address)
    add_link_options(-fsanitize=address)
endif()

if(ENABLE_UBSAN)
    add_compile_options(-fsanitize=undefined)
    add_link_options(-fsanitize=undefined)
endif()

if(ENABLE_TSAN)
    add_compile_options(-fsanitize=thread)
    add_link_options(-fsanitize=thread)
endif()
```
```bash
# Build with sanitizers
cmake -DENABLE_ASAN=ON -DENABLE_UBSAN=ON ..
make
```

## Common Patterns
```bash
# Development: ASan + UBSan
g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer \
    program.cpp -o program

# Testing threads: TSan
g++ -g -O1 -fsanitize=thread program.cpp -o program -pthread

# CI: All tests with sanitizers
cmake -DENABLE_ASAN=ON -DENABLE_UBSAN=ON ..
make test
```

## Best Practices

:::success DO
- Use ASan+UBSan in development (always)
- Run tests with sanitizers in CI
- Fix sanitizer warnings immediately
- Use `-O1` (not `-O0`) for better detection
- Keep `-fno-omit-frame-pointer` for better stack traces
  :::

:::danger DON'T
- Combine TSan with ASan/MSan (incompatible)
- Deploy with sanitizers (performance/size)
- Ignore sanitizer warnings (all are real bugs)
- Use `-O0` (misses some bugs)
  :::

## Quick Reference
```bash
# Memory errors & leaks
g++ -g -O1 -fsanitize=address program.cpp

# Undefined behavior
g++ -g -fsanitize=undefined program.cpp

# Data races
g++ -g -O1 -fsanitize=thread program.cpp -pthread

# Combined (recommended)
g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer program.cpp
```

## Summary
:::info
Sanitizers catch bugs at runtime with low overhead (2-3x vs 10-100x for Valgrind).
- **ASan**: memory errors, leaks, overflows.
- **UBSan**: undefined behavior, overflow, division by zero.
- **TSan**: data races in threads.
- **MSan**: uninitialized reads (Clang only).
- **Combine** ASan+UBSan in development.
- **Can't mix** TSan with ASan/MSan.
---
- Use `-O1 -fno-omit-frame-pointer` for best results.
- Fix all warnings immediately.
:::

```bash
# Daily development:
g++ -g -O1 -fsanitize=address,undefined \
    -fno-omit-frame-pointer program.cpp

# Thread testing:
g++ -g -O1 -fsanitize=thread program.cpp -pthread

# CI: Run all tests with sanitizers enabled
```