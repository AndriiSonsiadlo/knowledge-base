---
id: inline-assembly
title: Inline Assembly
sidebar_label: Inline Assembly
sidebar_position: 6
tags: [cpp, assembly, inline-asm, low-level, optimization]
---

# Inline Assembly

Embed assembly instructions directly in C++ code for performance-critical operations, hardware access, or platform-specific features unavailable in C++.

:::warning Platform-Specific
Assembly is **not portable**. Different syntax for GCC/Clang (AT&T/Intel) vs MSVC. Use only when necessary.
:::

## Basic Syntax (GCC/Clang)
```cpp showLineNumbers
// GCC/Clang: AT&T syntax by default
asm("instruction");

// Intel syntax (more readable)
asm(".intel_syntax noprefix\n"
    "mov eax, 42\n"
    ".att_syntax prefix");
```

## Extended Inline Assembly (GCC)
```cpp showLineNumbers
asm ("assembly code"
     : output operands
     : input operands
     : clobbered registers
);
```

### Example: Add Two Numbers
```cpp showLineNumbers
int add(int a, int b) {
    int result;
    
    asm("addl %1, %2\n"      // Add b to a
        "movl %%eax, %0"     // Move result
        : "=r"(result)       // Output: result
        : "r"(a), "r"(b)     // Inputs: a, b
        : "%eax"             // Clobbered: eax
    );
    
    return result;
}
```

**Syntax:**
- `%0`, `%1`, `%2` - operand placeholders
- `=r` - output, any register
- `r` - input, any register
- `%%eax` - literal register name (escape %)

## Common Constraints

| Constraint | Meaning              |
|------------|----------------------|
| `r`        | Any general register |
| `a`        | `rax/eax` register   |
| `b`        | `rbx/ebx` register   |
| `c`        | `rcx/ecx` register   |
| `d`        | `rdx/edx` register   |
| `m`        | Memory operand       |
| `i`        | Immediate integer    |
| `=`        | Write-only output    |
| `+`        | Read-write operand   |

## Practical Examples

### 1. Read CPU Timestamp
```cpp showLineNumbers
uint64_t rdtsc() {
    uint32_t low, high;
    
    asm volatile("rdtsc"
                 : "=a"(low), "=d"(high)
                 :
                 :
    );
    
    return ((uint64_t)high << 32) | low;
}
```

### 2. Memory Barrier
```cpp showLineNumbers
void memory_barrier() {
    asm volatile("mfence" ::: "memory");
    // Prevents reordering across this point
}
```

### 3. Atomic Compare-and-Swap
```cpp showLineNumbers
bool cas(int* ptr, int expected, int desired) {
    uint8_t result;
    
    asm volatile(
        "lock cmpxchgl %3, %1\n"  // Atomic compare-exchange
        "sete %0"                  // Set result based on zero flag
        : "=q"(result), "+m"(*ptr)
        : "a"(expected), "r"(desired)
        : "memory", "cc"
    );
    
    return result != 0;
}
```

### 4. Spin Loop Hint
```cpp showLineNumbers
void spin_wait() {
    while (condition) {
        asm volatile("pause");  // Hint to CPU: spin loop
    }
}
```

### 5. Prefetch Data
```cpp showLineNumbers
void prefetch(const void* addr) {
    asm volatile("prefetcht0 %0" : : "m"(*(const char*)addr));
}
```

## volatile Keyword in asm
```cpp showLineNumbers
// Without volatile: compiler may optimize away or reorder
asm("nop");

// With volatile: prevents optimization
asm volatile("nop");  // Guaranteed to execute
```

**Use `volatile`**: When asm has side effects (I/O, barriers).

## MSVC Syntax
```cpp showLineNumbers
// MSVC: different syntax
int add(int a, int b) {
    int result;
    
    __asm {
        mov eax, a
        add eax, b
        mov result, eax
    }
    
    return result;
}
```

**Note**: MSVC doesn't support inline asm in x64 mode - use intrinsics instead.

## Compiler Intrinsics (Portable Alternative)
```cpp showLineNumbers
#include <immintrin.h>  // x86 intrinsics

// Instead of inline asm
uint64_t rdtsc() {
    return __rdtsc();  // Compiler intrinsic
}

// Memory barrier
void barrier() {
    _mm_mfence();
}

// Atomic operations
bool cas(int* ptr, int expected, int desired) {
    return __sync_bool_compare_and_swap(ptr, expected, desired);
}
```

**Prefer intrinsics**: More portable, compiler can optimize better.

## Clobber List

Tells compiler which registers/memory are modified.
```cpp showLineNumbers
asm volatile(
    "movl $42, %%eax\n"
    "movl $100, %%ebx"
    :                    // No outputs
    :                    // No inputs
    : "%eax", "%ebx"     // Clobbered registers
);

// Memory clobber
asm volatile("" ::: "memory");  // Tells compiler memory changed
```

**"memory" clobber**: Acts as a memory barrier, prevents reordering.

## Intel vs AT&T Syntax
```asm
# AT&T (GCC default)
movl $42, %eax          # Source, Destination
addl %ebx, %eax         # Add ebx to eax

# Intel (more readable)
mov eax, 42             # Destination, Source
add eax, ebx            # Add ebx to eax
```

**Switch to Intel:**
```cpp showLineNumbers
asm(".intel_syntax noprefix");
```

## Common Use Cases

### Performance-Critical Code
```cpp showLineNumbers
// SIMD operations
void vec_add(float* a, float* b, float* result, int n) {
    for (int i = 0; i < n; i += 4) {
        asm volatile(
            "movups (%1), %%xmm0\n"      // Load a
            "movups (%2), %%xmm1\n"      // Load b
            "addps %%xmm1, %%xmm0\n"     // Add
            "movups %%xmm0, (%0)\n"      // Store result
            :
            : "r"(result + i), "r"(a + i), "r"(b + i)
            : "%xmm0", "%xmm1"
        );
    }
}
```

### Hardware Access (Embedded)
```cpp showLineNumbers
// Disable interrupts
void disable_interrupts() {
    asm volatile("cli");
}

// Enable interrupts
void enable_interrupts() {
    asm volatile("sti");
}

// Read control register
uint32_t read_cr0() {
    uint32_t value;
    asm volatile("mov %%cr0, %0" : "=r"(value));
    return value;
}
```

## Best Practices

:::success DO
- Use `volatile` for side effects
- Specify clobber list accurately
- Prefer compiler intrinsics when available
- Document what assembly does
- Test on target platform
  :::

:::danger DON'T
- Use for premature optimization
- Assume portability across compilers
- Forget clobber lists (causes subtle bugs)
- Mix assembly with complex C++ (exception handling issues)
- Use in x64 MSVC (not supported)
  :::

## When to Use Inline Assembly

| Use Case                          | Use Assembly?       |
|-----------------------------------|---------------------|
| **CPU instructions not in C++**   | ✅ Yes               |
| **Specific instruction sequence** | ✅ Yes               |
| **Compiler intrinsic available**  | ❌ No, use intrinsic |
| **General optimization**          | ❌ No, profile first |
| **Portable code**                 | ❌ No                |

## Summary


:::info Inline assembly
Embeds native CPU instructions in C++ code.
- Memory aid: "Last Resort Only"
- Syntax: `asm("code" : outputs : inputs : clobbers)`
- **GCC/Clang** use extended asm syntax with input/output operands and clobber lists.
- **MSVC** has different syntax and doesn't support x64 inline asm.
- Use when: CPU feature not in C++, hardware access, specific CPU features
- Prefer: Compiler intrinsics (`__rdtsc`, `_mm_mfence`) when available - more portable and optimizer-friendly
- Always: Use `volatile` for side effects
- Not portable: Different compilers, different syntax
:::
 
```cpp
// Interview answer:
// "Inline assembly embeds CPU instructions in C++. GCC uses
// extended asm with input/output operands; MSVC has different
// syntax and no x64 support. Use for hardware access or CPU
// instructions unavailable in C++. Prefer compiler intrinsics
// (__rdtsc, _mm_mfence) - more portable and optimizer-friendly.
// Always use 'volatile' for side effects. Not portable - test
// on target platform. Last resort after profiling shows need."
```