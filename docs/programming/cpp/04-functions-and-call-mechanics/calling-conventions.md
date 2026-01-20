---
id: calling-conventions
title: Calling Conventions
sidebar_label: Calling Conventions
sidebar_position: 7
tags: [c++, calling-conventions, abi, platform, assembly]
---

# Calling Conventions

Calling conventions define how functions receive parameters and return values at the assembly level - register usage, stack cleanup, and parameter passing order.

:::info Platform Specific
Calling conventions vary by architecture (x86, x64, ARM) and compiler. Understanding them helps with debugging, interop, and low-level optimization.
:::

## What They Define

1. **Parameter passing**: Registers vs stack, left-to-right vs right-to-left
2. **Return values**: Which register holds return value
3. **Stack cleanup**: Caller vs callee responsibility
4. **Register preservation**: Which registers must be saved/restored
5. **Name mangling**: How function names are encoded

---

## Common Conventions (x86/x64)

### cdecl (C Declaration)

Default for C/C++ on x86:

```cpp showLineNumbers 
int __cdecl add(int a, int b) {
    return a + b;
}

// Parameters pushed right-to-left on stack
// Caller cleans up stack
// Return value in EAX/RAX
```

**Stack layout**:
```
[return address]
[parameter b]  ← pushed first
[parameter a]  ← pushed last
```

**Characteristics**:
- Caller cleanup → enables variadic functions (`printf`)
- Most flexible but slower

### stdcall (Standard Call)

Windows API standard:

```cpp showLineNumbers 
int __stdcall add(int a, int b) {
    return a + b;
}

// Parameters pushed right-to-left
// Callee cleans up stack
// Return value in EAX/RAX
```

**Benefits**: Smaller code (one cleanup site instead of many)  
**Limitation**: Can't do variadic functions

### fastcall

First 2-4 parameters in registers:

```cpp showLineNumbers 
int __fastcall add(int a, int b) {
    return a + b;
}

// First 2 params in ECX, EDX (x86)
// Remaining on stack
// Faster for small parameter counts
```

---

## x64 Conventions

### Microsoft x64

Used on Windows:

```cpp showLineNumbers 
int add(int a, int b, int c, int d, int e) {
    return a + b + c + d + e;
}

// Parameters:
// a → RCX
// b → RDX
// c → R8
// d → R9
// e → stack
// Return → RAX
```

**Register usage**:
- Integer args: RCX, RDX, R8, R9
- Float args: XMM0-XMM3
- Return: RAX (int), XMM0 (float)

### System V AMD64 ABI

Used on Linux, macOS, BSD:

```cpp showLineNumbers 
int add(int a, int b, int c, int d, int e, int f, int g) {
    return a + b + c + d + e + f + g;
}

// Parameters:
// a-f → RDI, RSI, RDX, RCX, R8, R9
// g → stack
// Return → RAX
```

**More efficient**: 6 integer registers vs Windows' 4

---

## Practical Example

```cpp showLineNumbers 
// C++ code
int compute(int x, int y, int z) {
    return x * y + z;
}

int main() {
    int result = compute(5, 10, 3);
}
```

**x86-64 System V (Linux) assembly**:
```asm
compute:
    ; Parameters: RDI=x, RSI=y, RDX=z
    imul    edi, esi        ; x * y
    add     edi, edx        ; + z
    mov     eax, edi        ; Return in RAX
    ret

main:
    mov     edx, 3          ; z
    mov     esi, 10         ; y
    mov     edi, 5          ; x
    call    compute
    ; result in RAX
```

---

## ARM Conventions (AAPCS)

```cpp showLineNumbers 
int add(int a, int b, int c, int d, int e) {
    return a + b + c + d + e;
}

// Parameters:
// a-d → R0-R3
// e → stack
// Return → R0
```

---

## Return Value Handling

### Small Types

```cpp showLineNumbers 
int func() { return 42; }
// Return in RAX/EAX register

bool check() { return true; }
// Return in AL (low byte of RAX)
```

### Large Types (Structs)

```cpp showLineNumbers 
struct Large {
    int data[100];
};

Large create() {
    Large l;
    // ...
    return l;
}

// Typically uses "hidden parameter":
// void create(Large* result) { ... }
// Caller allocates space, passes pointer
```

**Modern**: RVO (Return Value Optimization) eliminates copy.

---

## Variadic Functions

```cpp showLineNumbers 
void printf(const char* fmt, ...) {
    // Variable arguments
}

// Requirements:
// - Caller cleanup (cdecl on x86)
// - Special handling for va_list
// - Platform-specific argument access
```

**Implementation varies**: x64 uses register + stack mix.

---

## Specifying Conventions

### GCC/Clang Attributes

```cpp showLineNumbers 
int __attribute__((cdecl)) func1();
int __attribute__((stdcall)) func2();
int __attribute__((fastcall)) func3();
```

### MSVC Keywords

```cpp showLineNumbers 
int __cdecl func1();
int __stdcall func2();
int __fastcall func3();
int __vectorcall func4();  // SIMD optimization
```

### C++ Default

```cpp showLineNumbers 
// Default: compiler chooses
// Usually most efficient for platform
int func(int x, int y);
```

---

## Interoperability

### C++ Calling C

```cpp showLineNumbers 
extern "C" {
    // Uses C calling convention (cdecl typically)
    void c_function(int x);
}
```

### Platform-Specific Code

```cpp showLineNumbers 
#ifdef _WIN32
    #define CALL_CONV __stdcall
#else
    #define CALL_CONV
#endif

int CALL_CONV platform_function(int x);
```

---

## Register Preservation

### Caller-Saved (Volatile)

Caller must save if needed:

```cpp showLineNumbers 
// RAX, RCX, RDX, R8-R11 (x64)
// Function can freely modify
// Caller saves before call if values needed after
```

### Callee-Saved (Non-volatile)

Callee must preserve:

```cpp showLineNumbers 
// RBX, RBP, RSI, RDI, R12-R15 (x64)
// Function must save/restore if used
// Caller can assume unchanged after call
```

---

## Stack Alignment

Modern platforms require aligned stacks:

```cpp showLineNumbers 
// x64: 16-byte alignment
// Must maintain alignment across calls

void func() {
    // Stack must be 16-byte aligned on entry
}
```

**Failure** to maintain alignment causes crashes with SSE instructions.

---

## Performance Implications

```cpp showLineNumbers 
// Many parameters → stack usage (slower)
void slow(int a, int b, int c, int d, int e, int f, int g, int h) {
    // g, h on stack (x64)
}

// Few parameters → register usage (faster)
void fast(int a, int b) {
    // All in registers
}

// Small struct by value (fast)
struct Point { int x, y; };
void process(Point p);  // Passed in registers

// Large struct by value (slow)
struct Big { int data[100]; };
void process(Big b);  // Passed via hidden pointer
```

---

## Debugging Tips

### View Assembly

```bash
# GCC/Clang
g++ -S -O2 code.cpp

# Compiler Explorer (godbolt.org)
# Visual side-by-side source and assembly
```

### Check Calling Convention

```bash
# View symbols
nm -C binary

# Disassemble
objdump -d binary
```

---

## Summary

**Calling conventions define**:
- Parameter passing mechanism
- Stack vs register usage
- Cleanup responsibility
- Return value location

**Common conventions**:
- **cdecl**: C default, caller cleanup
- **stdcall**: Windows API, callee cleanup
- **fastcall**: Registers for speed
- **x64**: Platform-specific (MS vs System V)

**Key differences**:
```
x86 cdecl:     Stack, right-to-left, caller cleanup
x64 MS:        RCX,RDX,R8,R9 + stack
x64 System V:  RDI,RSI,RDX,RCX,R8,R9 + stack
ARM:           R0-R3 + stack
```

**Practical impact**:
- Performance: Registers faster than stack
- Interop: Must match when calling C/assembly
- Debugging: Understanding conventions helps read assembly

**Modern practice**: Let compiler choose unless doing platform interop or assembly integration.