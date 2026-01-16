---
id: compilation
title: Compilation Phase
sidebar_label: Compilation
sidebar_position: 3
tags: [c++, compiler, optimization, assembly]
---

# Compilation Phase

The compilation phase translates preprocessed C++ code into assembly language. This is where syntax checking, semantic analysis, optimization, and code generation happen.

:::info Brain of the Build
Compilation is the "smart" phase - it understands C++, checks types, instantiates templates, and performs optimizations.
:::

## What the Compiler Does

```mermaid
graph LR
    A[Preprocessed C++] --> B[Parser]
    B --> C[AST]
    C --> D[Semantic Analysis]
    D --> E[Optimizer]
    E --> F[Code Generator]
    F --> G[Assembly]
```

**Input**: Preprocessed `.i` file (pure C++, no directives)  
**Output**: Assembly `.s` file (human-readable CPU instructions)

---

## Compilation Stages

### 1. Lexical Analysis (Tokenization)

Breaks source code into tokens (keywords, identifiers, operators):

```cpp
int x = 42 + y;

// Tokenized as:
[int] [x] [=] [42] [+] [y] [;]
```

### 2. Syntax Analysis (Parsing)

Builds Abstract Syntax Tree (AST) ensuring code follows C++ grammar:

```cpp
x = a + b * c;

// AST:
    =
   / \
  x   +
     / \
    a   *
       / \
      b   c
```

The tree respects operator precedence (`*` before `+`). Syntax errors are caught here.

### 3. Semantic Analysis

Checks types, scopes, and semantics:

```cpp
int x = "hello";  // ❌ Type error: can't assign string to int
foo();            // ❌ Error: 'foo' not declared
int y = x + z;    // ✅ OK if z is int/compatible type
```

**Checks performed**:
- Type compatibility
- Function signatures
- Variable declarations
- Access control (private/public)
- Template instantiation

### 4. Intermediate Representation (IR)

Converts AST to platform-independent intermediate form. Optimizations work on IR:

```cpp
int sum(int a, int b) {
    int temp = a + b;
    return temp;
}

// IR (LLVM-style, simplified):
%temp = add i32 %a, %b
ret i32 %temp
```

### 5. Optimization

Transforms code for better performance without changing behavior:

```cpp
// Original
int square(int x) {
    return x * x;
}
int result = square(5);

// After constant folding & inlining
int result = 25;  // Computed at compile-time!
```

### 6. Code Generation

Translates optimized IR to target assembly:

```cpp
int add(int a, int b) {
    return a + b;
}

// Generated x86-64 assembly:
add:
    lea    eax, [rdi + rsi]  # eax = rdi + rsi (a + b)
    ret
```

---

## Optimization Levels

```bash
g++ -O0 main.cpp  # No optimization (default, fastest compile)
g++ -O1 main.cpp  # Basic optimization
g++ -O2 main.cpp  # Recommended for production
g++ -O3 main.cpp  # Aggressive optimization
g++ -Os main.cpp  # Optimize for size
g++ -Og main.cpp  # Optimize for debugging
```

### O0 vs O3 Comparison

```cpp
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

**-O0 (no optimization)**:
```asm
factorial:
    push   rbp
    mov    rbp, rsp
    sub    rsp, 16
    mov    DWORD PTR [rbp-4], edi
    cmp    DWORD PTR [rbp-4], 1
    jg     .L2
    mov    eax, 1
    jmp    .L3
.L2:
    mov    eax, DWORD PTR [rbp-4]
    sub    eax, 1
    mov    edi, eax
    call   factorial
    imul   eax, DWORD PTR [rbp-4]
.L3:
    leave
    ret
```

**-O3 (aggressive optimization)**:
```asm
factorial:
    cmp    edi, 1
    jle    .L4
    push   rbx
    mov    ebx, edi
.L3:
    sub    edi, 1
    call   factorial
    imul   ebx, eax
    mov    eax, ebx
    pop    rbx
    ret
.L4:
    mov    eax, 1
    ret
```

The `-O3` version is shorter, faster, and may even unroll loops or use tail recursion optimization.

---

## Common Optimizations

### 1. Constant Folding

```cpp
int x = 3 + 4 * 5;  // Computed at compile-time
// Becomes: int x = 23;
```

### 2. Dead Code Elimination

```cpp
int compute() {
    int unused = 42;  // Removed - never used
    return 10;
    // Everything after return is removed
}
```

### 3. Function Inlining

```cpp
inline int square(int x) { return x * x; }

int result = square(5);
// Becomes: int result = 5 * 5;  (no function call overhead)
```

The compiler replaces function calls with the function body when beneficial.

### 4. Loop Unrolling

```cpp
for (int i = 0; i < 4; i++) {
    sum += arr[i];
}

// Unrolled:
sum += arr[0];
sum += arr[1];
sum += arr[2];
sum += arr[3];
// Eliminates loop overhead
```

### 5. Strength Reduction

```cpp
int result = x * 8;
// Optimized to: int result = x << 3;  (bit shift is faster)

for (int i = 0; i < n; i++) {
    y = i * 4;  // In loop
}
// Optimized to:
for (int i = 0, y = 0; i < n; i++, y += 4) {
    // Use y directly (addition instead of multiplication)
}
```

---

## Template Instantiation

The compiler generates code for each template specialization used:

```cpp
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

int main() {
    max(5, 10);           // Instantiates max<int>
    max(3.14, 2.71);      // Instantiates max<double>
    max("ab", "cd");      // Instantiates max<const char*>
}
```

The compiler creates **three separate functions** in the assembly output. This is why template code must be in headers - the compiler needs the definition to instantiate.

---

## Viewing Compiler Output

```bash
# Generate assembly
g++ -S main.cpp -o main.s

# Generate assembly with mixed source
g++ -S -fverbose-asm main.cpp -o main.s

# Generate LLVM IR (Clang)
clang++ -S -emit-llvm main.cpp -o main.ll

# Show optimization remarks
g++ -O3 -fopt-info main.cpp

# Compiler Explorer (godbolt.org)
# Visual side-by-side source and assembly
```

---

## Compiler Warnings

Enable warnings to catch potential bugs:

```bash
g++ -Wall -Wextra -Wpedantic main.cpp

# Individual warnings
-Wunused-variable      # Unused variables
-Wunused-parameter     # Unused function parameters
-Wconversion           # Implicit conversions
-Wsign-compare         # Signed/unsigned comparison
-Wformat              # printf format errors
```

```cpp
// Examples caught by warnings
int x;                    // -Wuninitialized
void foo(int unused) {}   // -Wunused-parameter
if (x = 5) {}            // -Wparentheses (assignment in condition)
unsigned u = -1;          // -Wsign-conversion
```

**Treat warnings as errors**:
```bash
g++ -Wall -Wextra -Werror main.cpp  # Fail on warnings
```

---

## Compilation Time Optimization

### 1. Precompiled Headers

```cpp
// pch.h - stable headers
#include <iostream>
#include <vector>
#include <map>

// Precompile once
g++ -x c++-header pch.h -o pch.h.gch

// Use in compilation (faster)
g++ -include pch.h main.cpp
```

### 2. Forward Declarations

```cpp
// ❌ Slow - includes entire header
#include "widget.h"

// ✅ Fast - just declares
class Widget;
void process(Widget* w);
```

### 3. Extern Templates

```cpp
// header.h
template<typename T>
class Container { /* ... */ };

extern template class Container<int>;  // Don't instantiate here

// implementation.cpp
template class Container<int>;  // Instantiate once here
```

Prevents the compiler from instantiating templates in every translation unit.

---

## Common Compiler Errors

### Undefined Reference (Actually Linker Error)

```cpp
// header.h
void foo();

// main.cpp
foo();  // ❌ undefined reference to `foo()'
```

**Solution**: Implement `foo()` in a source file and link it.

### Template Instantiation Error

```cpp
template<typename T>
void print(T value) {
    std::cout << value.name << "\n";  // Assumes T has 'name'
}

print(42);  // ❌ int has no member 'name'
```

**Solution**: Add concept/static_assert or SFINAE.

### Ambiguous Overload

```cpp
void foo(int x) {}
void foo(double x) {}

foo(3.14f);  // ❌ Ambiguous: float converts to both int and double
```

---

## Compiler-Specific Features

```cpp
// GCC/Clang attributes
[[gnu::always_inline]]
int fast_func() { return 42; }

[[gnu::noinline]]
int debug_func() { return 42; }

// MSVC
__declspec(noinline)
void no_inline() {}

// Portable C++11
[[noreturn]]
void exit_program() { std::exit(1); }
```

---

## Summary

The compilation phase:

- **Parses** C++ into AST
- **Checks** syntax, types, and semantics
- **Instantiates** templates
- **Optimizes** code (-O0 to -O3)
- **Generates** assembly language

**Key points**:
- Use `-O2` or `-O3` for production
- Enable all warnings (`-Wall -Wextra`)
- Understand optimization impact on debugging
- Template code must be in headers
- Compilation is the slowest build phase

```bash
# Recommended production compilation
g++ -std=c++20 -O3 -Wall -Wextra -Werror -march=native main.cpp -o app
```