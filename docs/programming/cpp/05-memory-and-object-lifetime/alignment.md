---
id: memory-alignment
title: Memory Alignment
sidebar_label: Memory Alignment
sidebar_position: 7
tags: [c++, alignment, memory, performance, padding]
---

# Memory Alignment

Data arranged at addresses that are multiples of its size. Required for correctness on some architectures, critical for performance on all.

:::info Hardware Requirement
**x86-64**: Misaligned = 2-10x slower  
**ARM/RISC**: Misaligned = crash  
Compiler aligns automatically, but understanding helps optimize struct layouts.
:::

## Why Alignment Matters

CPUs read memory in chunks (4/8/16 bytes). Aligned data = one read. Misaligned = multiple reads + masking.
```
Memory:  [0][1][2][3][4][5][6][7]
         └─────────┘ 4-byte read

Aligned int at [0]:     One read ✅
Misaligned int at [1]:  Two reads ❌ (slower)
```

**Performance impact**: 2-10x slower for misaligned access on x86-64.

## Natural Alignment

Type alignment = its size (up to word size).
```cpp showLineNumbers
char c;      // 1-byte alignment
short s;     // 2-byte alignment
int i;       // 4-byte alignment
double d;    // 8-byte alignment

// Memory layout:
// Address  Type
// 0x1000   char c
// 0x1001   (padding)
// 0x1002   short s
// 0x1004   int i
// 0x1008   double d
```

**Rule**: Address must be divisible by alignment requirement.

## Struct Padding

Compiler inserts padding for alignment.
```cpp showLineNumbers
struct Bad {
    char c;    // 1 byte
    // 3 bytes padding
    int i;     // 4 bytes
    char c2;   // 1 byte
    // 3 bytes padding
};
sizeof(Bad);  // 12 bytes (50% waste!)

struct Good {
    int i;     // 4 bytes
    char c;    // 1 byte
    char c2;   // 1 byte
    // 2 bytes padding
};
sizeof(Good);  // 8 bytes (33% smaller!)
```

**Optimization**: Order members largest → smallest to minimize padding.

## Array Alignment

Struct size must be multiple of alignment for array elements.
```cpp showLineNumbers
struct Example {
    char c;    // 1 byte
    int i;     // 4 bytes (+ 3 padding before)
    char c2;   // 1 byte
    // 3 bytes trailing padding → size = 12
};

Example arr[2];
// arr[0] at 0x1000: properly aligned
// arr[1] at 0x100C: properly aligned
// Without trailing padding, arr[1].i would be misaligned!
```

**Why trailing padding**: Ensures array elements stay aligned.

## alignof and alignas

Query and control alignment.
```cpp showLineNumbers
// Query alignment
std::cout << alignof(char) << "\n";    // 1
std::cout << alignof(int) << "\n";     // 4
std::cout << alignof(double) << "\n";  // 8

struct Widget { char c; int i; };
std::cout << alignof(Widget) << "\n";  // 4 (largest member)

// Specify alignment
alignas(64) int cache_line_var;  // 64-byte aligned

struct alignas(32) Aligned {
    int x;
    // Padding to 32 bytes
};
```

## Common Use Cases

### Cache-Line Alignment (Prevent False Sharing)
```cpp showLineNumbers
// Problem: False sharing
struct Counters {
    int thread1;  // Same cache line
    int thread2;  // Threads fight for cache line ownership
};

// Solution: Align to cache line (64 bytes)
struct Counters {
    alignas(64) int thread1;  // Cache line 1
    alignas(64) int thread2;  // Cache line 2
};
// 10-100x faster in multithreaded code!
```

### SIMD Alignment
```cpp showLineNumbers
// SIMD requires 16-byte alignment
alignas(16) float vector[4];

// Fast: aligned SIMD load
load_simd(vector);  // 1 instruction

// Slow: unaligned load
float* unaligned = (float*)((char*)vector + 1);
load_simd(unaligned);  // Multiple instructions + shuffles
```

## Optimal Struct Layout
```cpp showLineNumbers
// ❌ Poor: 24 bytes (7 bytes wasted)
struct Poor {
    char a;      // 1 + 7 padding
    double b;    // 8
    char c;      // 1 + 7 padding
};

// ✅ Better: 16 bytes (6 bytes wasted)
struct Better {
    double b;    // 8
    char a;      // 1
    char c;      // 1
    // 6 bytes padding
};

// ✅ Best: 16 bytes (6 bytes used)
struct Best {
    double b;    // 8
    int i;       // 4
    char a;      // 1
    char c;      // 1
    short s;     // 2
};
```

**Strategy**: Largest types first, fill gaps with smaller types.

## Packed Structures

Remove padding (dangerous, slow).
```cpp showLineNumbers
// GCC/Clang
struct __attribute__((packed)) Packed {
    char c;      // 1
    int i;       // 4 (misaligned!)
    char c2;     // 1
};  // 6 bytes total

// MSVC
#pragma pack(push, 1)
struct Packed {
    char c; int i; char c2;
};
#pragma pack(pop)
```

**Effects**:
- x86-64: Works but slow (2-10x)
- ARM: May crash
- Use only for: file formats, network protocols

## Alignment at Runtime
```cpp showLineNumbers
template<typename T>
bool is_aligned(const T* ptr) {
    return reinterpret_cast<uintptr_t>(ptr) % alignof(T) == 0;
}

int x;
std::cout << is_aligned(&x);  // Usually true

char buffer[16];
int* p = reinterpret_cast<int*>(buffer + 1);
std::cout << is_aligned(p);  // False - misaligned
```

## Quick Reference

| Type      | Size          | Alignment  |
|-----------|---------------|------------|
| `char`    | 1             | 1          |
| `short`   | 2             | 2          |
| `int`     | 4             | 4          |
| `long`    | 8             | 8 (64-bit) |
| `float`   | 4             | 4          |
| `double`  | 8             | 8          |
| `pointer` | 8             | 8 (64-bit) |
| `struct`  | sum + padding | max member |

## Summary

Alignment = addresses divisible by type size. Misaligned access is slow (x86) or crashes (ARM). Compiler aligns automatically and inserts struct padding. Order struct members large→small to minimize padding. Trailing padding ensures array elements stay aligned. Use `alignof` to query, `alignas` to specify (cache lines, SIMD). Packed structs remove padding but cause slow/unsafe access. Cache-line alignment (64 bytes) prevents false sharing in multithreaded code. Understand alignment to optimize memory layouts and avoid performance pitfalls.
```cpp
// Interview answer:
// "Alignment means data at addresses divisible by its size.
// Required for correctness (ARM crashes on misalignment) and
// performance (x86 is 2-10x slower). Compiler inserts struct
// padding to align members. Optimize by ordering large→small.
// Cache-line alignment (64 bytes) prevents false sharing in
// multithreaded code. Use alignof/alignas for explicit control."
```