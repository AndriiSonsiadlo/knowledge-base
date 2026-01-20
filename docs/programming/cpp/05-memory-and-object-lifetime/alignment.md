---
id: memory-alignment
title: Memory Alignment
sidebar_label: Memory Alignment
sidebar_position: 7
tags: [c++, alignment, memory, performance, padding]
---

# Memory Alignment

Memory alignment refers to arranging data in memory at addresses that are multiples of the data's size. Proper alignment is required for correct program operation on many architectures and significantly affects performance on all platforms.

:::info Hardware Requirement
Most CPUs require or strongly prefer aligned data access. Misaligned access can cause crashes (ARM, SPARC) or severe performance penalties (x86-64).
:::

## Why Alignment Matters

Modern CPUs read memory in chunks (typically 4, 8, or 16 bytes). When data is properly aligned, the CPU can read it in a single operation. Misaligned data may span chunk boundaries, requiring multiple reads and masking operations.

```cpp showLineNumbers 
// Assume 4-byte memory reads

// Aligned int at address 0x1000
// CPU reads bytes 0x1000-0x1003 in one operation ✅

// Misaligned int at address 0x1001
// CPU must read 0x1000-0x1003 AND 0x1004-0x1007
// Then combine parts - much slower! ❌
```

On x86-64, misaligned access is handled automatically but runs 2-10x slower depending on cache line crossing. On ARM and other RISC architectures, misaligned access can cause a hardware exception, crashing the program. The compiler automatically aligns variables to avoid these problems, but understanding alignment helps you write more efficient code.

## Natural Alignment

Each type has a natural alignment equal to its size (or platform word size for types larger than a word). The compiler ensures objects are placed at addresses divisible by their alignment.

```cpp showLineNumbers 
char c;      // 1-byte alignment (any address)
short s;     // 2-byte alignment (even addresses)
int i;       // 4-byte alignment (divisible by 4)
double d;    // 8-byte alignment (divisible by 8)
void* ptr;   // 4 or 8-byte (32/64-bit platform)

// Example memory layout:
// Address  Variable  Value
// 0x1000   char c    'A'
// 0x1001   (padding)
// 0x1002   short s   100
// 0x1004   int i     42
// 0x1008   double d  3.14
```

The compiler inserts padding bytes to ensure each variable starts at an appropriately aligned address. This padding is invisible to your code but increases memory usage. Understanding where padding occurs helps you optimize struct layouts.

## struct Padding

Structs contain padding to align members and ensure the struct itself can be properly aligned in arrays. The compiler adds padding after members to meet alignment requirements.

```cpp showLineNumbers 
struct Bad {
    char c;    // 1 byte
    // 3 bytes padding
    int i;     // 4 bytes
    char c2;   // 1 byte
    // 3 bytes padding
};
sizeof(Bad);  // 12 bytes (not 6!)

struct Good {
    int i;     // 4 bytes
    char c;    // 1 byte
    char c2;   // 1 byte
    // 2 bytes padding
};
sizeof(Good);  // 8 bytes (50% smaller!)
```

The padding after `c` in `Bad` ensures `i` starts at an address divisible by 4. The trailing padding ensures that in an array of `Bad` structs, each element's members remain properly aligned. Reordering members from largest to smallest typically minimizes padding, though sometimes grouping related data matters more for cache performance than saving a few bytes.

### Array Alignment

The struct's size must be a multiple of its alignment requirement so that array elements maintain proper alignment. This sometimes requires trailing padding even after the last member.

```cpp showLineNumbers 
struct Example {
    char c;    // 1 byte
    int i;     // 4 bytes (after 3 bytes padding)
    char c2;   // 1 byte
    // 3 bytes trailing padding to make size = 12
};

Example arr[2];
// arr[0] at 0x1000: members properly aligned
// arr[1] at 0x100C: members properly aligned
// Without trailing padding, arr[1].i would be misaligned!
```

## alignof and alignas

C++11 provides `alignof` to query alignment requirements and `alignas` to specify custom alignment, giving you explicit control over data layout.

```cpp showLineNumbers 
#include <iostream>

std::cout << alignof(char) << "\n";    // 1
std::cout << alignof(int) << "\n";     // 4
std::cout << alignof(double) << "\n";  // 8

struct Widget {
    char c;
    int i;
};
std::cout << alignof(Widget) << "\n";  // 4 (alignment of largest member)
```

The `alignof` operator returns the alignment requirement in bytes. This is useful for allocating properly aligned buffers or understanding struct layout. Structures inherit the alignment of their most strictly aligned member to ensure all members can be properly aligned.

### Using alignas

The `alignas` specifier increases (never decreases) alignment requirements, useful for cache-line alignment, SIMD types, or hardware requirements.

```cpp showLineNumbers 
// Cache-line aligned (64 bytes on most platforms)
struct alignas(64) CacheLinePadded {
    int data;
    // 60 bytes padding to reach 64
};

// SIMD-friendly alignment (16 bytes)
alignas(16) float vec[4];

// Increase struct alignment
struct alignas(32) HighlyAligned {
    int x;
    // Padding to 32 bytes
};
```

Cache-line alignment prevents false sharing in multithreaded code where different threads modify different variables that happen to share a cache line. SIMD operations require 16 or 32-byte alignment for optimal performance. The compiler inserts padding to meet the specified alignment.

## Alignment in Practice

Understanding alignment helps you write more efficient code by minimizing wasted space and avoiding performance penalties.

```cpp showLineNumbers 
// Poor layout - 24 bytes with 7 bytes wasted
struct Poor {
    char a;      // 1 byte + 7 padding
    double b;    // 8 bytes
    char c;      // 1 byte + 7 padding
};

// Optimized layout - 16 bytes with 6 bytes wasted
struct Optimized {
    double b;    // 8 bytes
    char a;      // 1 byte
    char c;      // 1 byte
    // 6 bytes padding
};

// Even better - 16 bytes with 6 bytes of useful space
struct BestCase {
    double b;    // 8 bytes
    char a;      // 1 byte
    char c;      // 1 byte
    short s;     // 2 bytes
    int i;       // 4 bytes
};
```

The `BestCase` layout groups smaller members together to fill padding gaps, wasting no space compared to natural alignment requirements. This matters more for large arrays of structures where the savings multiply.

## Packed Structures

Some compilers allow removing padding entirely, though this causes misalignment and should be avoided except for binary compatibility or memory-constrained systems.

```cpp showLineNumbers 
// GCC/Clang: Remove padding
struct __attribute__((packed)) Packed {
    char c;      // 1 byte
    int i;       // 4 bytes
    char c2;     // 1 byte
};
sizeof(Packed);  // 6 bytes

// MSVC syntax
#pragma pack(push, 1)
struct Packed {
    char c;
    int i;
    char c2;
};
#pragma pack(pop)
```

Packed structures eliminate padding, reducing memory usage but causing misaligned member access. On x86-64, this is slow but functional; on ARM, it may crash. Use packed structures only when interfacing with external formats (file formats, network protocols) that require specific layouts, never for general program data.

## Dynamic Allocation Alignment

The `new` operator returns memory aligned to the largest fundamental type's alignment (typically 8 or 16 bytes), sufficient for most types. For over-aligned types, C++17 provides alignment-aware allocation.

```cpp showLineNumbers 
// Normal new - aligned to max_align_t (16 bytes typically)
int* p = new int;  // Aligned to 4 bytes (int's requirement)
double* d = new double;  // Aligned to 8 bytes

// C++17: Over-aligned new
struct alignas(64) CacheLine {
    int data[16];
};

CacheLine* cl = new CacheLine;  // Aligned to 64 bytes
delete cl;

// Or allocate aligned memory manually
void* aligned_alloc(size_t alignment, size_t size);
void* ptr = aligned_alloc(64, sizeof(CacheLine));
free(ptr);
```

Over-aligned types (alignment > `alignof(std::max_align_t)`) require special handling. C++17 automatically uses alignment-aware allocation when you `new` an over-aligned type. For C++11/14, you need to use platform-specific functions like `aligned_alloc`, `_aligned_malloc`, or `posix_memalign`.

## Performance Impact

Alignment significantly affects performance through both instruction efficiency and cache behavior. Properly aligned data enables efficient memory operations.

```cpp showLineNumbers 
// Aligned access - fast (1 cycle)
alignas(16) float data[4];
load_vector(data);  // SIMD load, 1 instruction

// Misaligned access - slow (10+ cycles)
float* unaligned = (float*)((char*)data + 1);
load_vector(unaligned);  // Multiple loads + shuffles

// False sharing - very slow (100+ cycles)
struct {
    alignas(64) int thread1_counter;  // Cache line 1
    alignas(64) int thread2_counter;  // Cache line 2
} counters;
// Without alignment, both on same cache line
// Threads fight over cache line ownership
```

False sharing occurs when independent variables share a cache line, causing cache coherency traffic between CPU cores. Aligning frequently-modified thread-local data to cache line boundaries (64 bytes) eliminates this problem, sometimes providing 10-100x speedups in multithreaded code.

## Checking Alignment at Runtime

You can verify pointer alignment at runtime using modulo arithmetic, useful for debugging alignment assumptions.

```cpp showLineNumbers 
template<typename T>
bool is_aligned(const T* ptr, size_t alignment = alignof(T)) {
    return reinterpret_cast<uintptr_t>(ptr) % alignment == 0;
}

int x;
std::cout << is_aligned(&x);  // Usually true

char buffer[16];
int* p = reinterpret_cast<int*>(buffer + 1);
std::cout << is_aligned(p);  // Likely false - misaligned
```

## Summary

Memory alignment requires data to be stored at addresses divisible by its size, enabling efficient CPU access. Misaligned access is slow on x86-64 and crashes on ARM/RISC architectures. The compiler automatically aligns variables to their natural alignment, inserting padding in structs to meet alignment requirements. Struct size must be a multiple of its alignment to support arrays, often requiring trailing padding. Use `alignof` to query alignment and `alignas` to specify increased alignment for cache lines or SIMD. Order struct members largest-to-smallest to minimize padding waste. Packed structs eliminate padding but cause slow misaligned access - use only for binary compatibility. Over-aligned types (> 16 bytes) require special allocation in C++17. Proper alignment is essential for performance, especially preventing false sharing in multithreaded code where independent variables on the same cache line cause cache thrashing. While the compiler handles basic alignment automatically, understanding these rules helps you optimize memory layouts and avoid performance pitfalls.