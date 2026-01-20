---
id: alignment-and-offsetof
title: Alignment and offsetof
sidebar_label: Alignment
sidebar_position: 8
tags: [c++, alignment, offsetof, memory-layout, padding]
---

# Alignment and offsetof

Alignment ensures data is placed at memory addresses divisible by its size, improving CPU access speed. Padding fills gaps to maintain alignment.

## Alignment Basics

```cpp showLineNumbers 
struct Example {
    char c;     // 1 byte
    int i;      // 4 bytes
};

sizeof(Example);  // 8, not 5! (3 bytes padding after c)
```

**Why**: CPU reads memory in aligned chunks (typically 4 or 8 bytes). Misaligned access is slower or crashes on some platforms.

---

## Alignment Requirements

```cpp showLineNumbers 
#include <iostream>

std::cout << alignof(char) << "\n";    // 1
std::cout << alignof(int) << "\n";     // 4
std::cout << alignof(double) << "\n";  // 8
std::cout << alignof(void*) << "\n";   // 8 (64-bit)
```

**Rule**: Type must be aligned to multiple of its size.

---

## Struct Padding

```cpp showLineNumbers 
struct Bad {
    char c;      // Offset 0, size 1
    // 3 bytes padding
    int i;       // Offset 4, size 4
    char c2;     // Offset 8, size 1
    // 7 bytes padding (for array alignment)
};
sizeof(Bad);  // 16 bytes

struct Good {
    int i;       // Offset 0, size 4
    char c;      // Offset 4, size 1
    char c2;     // Offset 5, size 1
    // 2 bytes padding
};
sizeof(Good);  // 8 bytes (50% savings!)
```

**Tip**: Order members largest to smallest to minimize padding.

---

## offsetof Macro

Get member offset within struct:

```cpp showLineNumbers 
#include <cstddef>

struct Point {
    int x;
    int y;
    int z;
};

std::cout << offsetof(Point, x) << "\n";  // 0
std::cout << offsetof(Point, y) << "\n";  // 4
std::cout << offsetof(Point, z) << "\n";  // 8
```

---

## Controlling Alignment

### alignas (C++11)

```cpp showLineNumbers 
// Align to 16 bytes
struct alignas(16) Aligned {
    int x;
    int y;
};

sizeof(Aligned);   // 16 (8 data + 8 padding)
alignof(Aligned);  // 16

// Align member
struct Container {
    alignas(64) char buffer[64];  // Cache-line aligned
};
```

### Packed Structs

```cpp showLineNumbers 
// Remove padding (compiler-specific)
struct __attribute__((packed)) Packed {
    char c;
    int i;
    char c2;
};
sizeof(Packed);  // 6 (no padding)

// MSVC syntax
#pragma pack(push, 1)
struct Packed {
    char c;
    int i;
};
#pragma pack(pop)
```

⚠️ **Warning**: Packed structs can cause crashes on some architectures and are slower due to unaligned access.

---

## Practical Examples

### Network Protocol

```cpp showLineNumbers 
// Bad: padding wastes bandwidth
struct Message {
    char type;     // 1 byte
    int length;    // 4 bytes (3 padding before)
    char data[100];
};  // 108 bytes (3 wasted)

// Better: pack or reorder
#pragma pack(push, 1)
struct Message {
    char type;
    int length;
    char data[100];
};  // 105 bytes
#pragma pack(pop)
```

### Cache Optimization

```cpp showLineNumbers 
// Align to cache line (64 bytes) to prevent false sharing
struct alignas(64) Counter {
    std::atomic<int> value;
    char padding[60];  // Fill cache line
};
```

---

## Summary

- **Alignment**: Memory addresses divisible by type size
- **Padding**: Filler bytes for alignment
- **sizeof**: Includes padding
- **offsetof**: Member offset in struct
- **alignas**: Control alignment
- **Order members**: Large → small minimizes padding

```cpp showLineNumbers 
// Minimize padding
struct Optimized {
    double d;  // 8 bytes
    int i;     // 4 bytes
    short s;   // 2 bytes
    char c;    // 1 byte
    // 1 byte padding
};  // 16 bytes total
```