---
id: padding-and-offsetof
title: Padding and offsetof
sidebar_label: Padding & offsetof
sidebar_position: 3
tags: [cpp, padding, offsetof, alignment, memory-layout]
---

# Padding and offsetof

Padding bytes align struct members to hardware requirements. `offsetof` macro queries member positions. Understanding both optimizes memory usage and enables low-level memory manipulation.

See [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) for comprehensive alignment coverage.

## Why Padding Exists
```cpp showLineNumbers
struct Example {
    char c;    // 1 byte, offset 0
    // 3 bytes padding inserted here
    int i;     // 4 bytes, offset 4 (must be aligned to 4)
};
sizeof(Example);  // 8 bytes (not 5!)
```

**Reason**: CPU requires `int` at address divisible by 4. Padding ensures alignment.

## Padding Rules
```cpp showLineNumbers
struct Rules {
    char c1;     // offset 0
    // 3 padding
    int i;       // offset 4 (aligned to 4)
    char c2;     // offset 8
    // 3 padding (for array alignment)
};  // sizeof = 12

// In array:
Rules arr[2];
// arr[0] at 0x1000, arr[1] at 0x100C
// Each element's members stay aligned
```

**Array alignment**: Struct size must be multiple of largest member alignment.

## Visualizing Padding
```cpp showLineNumbers
struct Visual {
    char a;      // [a]
    // [_][_][_]  padding
    int b;       // [b][b][b][b]
    char c;      // [c]
    // [_][_][_]  padding
    double d;    // [d][d][d][d][d][d][d][d]
};  // Total: 24 bytes
```

## offsetof Macro

Query member offset in bytes from struct start.
```cpp showLineNumbers
#include <cstddef>

struct Point {
    int x;
    int y;
    int z;
};

size_t x_off = offsetof(Point, x);  // 0
size_t y_off = offsetof(Point, y);  // 4
size_t z_off = offsetof(Point, z);  // 8

std::cout << "y is at offset " << y_off << " bytes\n";
```

### Using offsetof
```cpp showLineNumbers
struct Packet {
    uint32_t header;
    uint16_t type;
    uint16_t length;
    uint8_t data[256];
};

// Calculate data offset for network protocol
size_t data_offset = offsetof(Packet, data);  // 8

// Access member via byte offset
char* base = reinterpret_cast<char*>(&packet);
uint8_t* data_ptr = reinterpret_cast<uint8_t*>(base + data_offset);
```

**Use case**: Binary protocols, serialization, memory-mapped I/O.

## offsetof Requirements
```cpp showLineNumbers
// ✅ OK: standard layout type
struct StandardLayout {
    int a;
    int b;
};
offsetof(StandardLayout, b);  // ✅ Defined

// ❌ UB: non-standard layout (virtual functions)
struct NonStandard {
    virtual void f();
    int x;
};
// offsetof(NonStandard, x);  // ❌ Undefined behavior!

// ❌ UB: non-standard layout (base class)
struct Base { int a; };
struct Derived : Base { int b; };
// offsetof(Derived, b);  // ❌ UB
```

**Rule**: `offsetof` only safe for standard-layout types.

## Minimizing Padding
```cpp showLineNumbers
// ❌ Poor: 24 bytes (12 wasted)
struct Poor {
    char a;      // 1 + 7 padding
    double b;    // 8
    char c;      // 1 + 7 padding
};

// ✅ Better: 16 bytes (6 wasted)
struct Better {
    double b;    // 8
    char a;      // 1
    char c;      // 1
    // 6 padding
};

// ✅ Best: 16 bytes (6 usefully filled)
struct Best {
    double b;    // 8
    int i;       // 4
    char a;      // 1
    char c;      // 1
    short s;     // 2
};
```

**Strategy**: Order members: largest first, smallest last. Fill gaps.

## Calculating Padding
```cpp showLineNumbers
struct Calculate {
    char c;      // 1 byte
    int i;       // 4 bytes
    short s;     // 2 bytes
};

// Manual calculation:
// c: offset 0, size 1
// padding: 3 bytes (align i to 4)
// i: offset 4, size 4
// s: offset 8, size 2
// padding: 2 bytes (align struct to 4)
// Total: 12 bytes

sizeof(Calculate);  // 12
```

## Bit Fields (No Padding Between)
```cpp showLineNumbers
struct Flags {
    unsigned int flag1 : 1;  // 1 bit
    unsigned int flag2 : 1;  // 1 bit
    unsigned int value : 6;  // 6 bits
    // All packed into 1 byte, then padded to word boundary
};
sizeof(Flags);  // 4 (platform-dependent)
```

**Warning**: Bit field layout is implementation-defined.

## Zero-Size Arrays (GCC Extension)
```cpp showLineNumbers
struct FlexibleArray {
    int count;
    int data[0];  // Or int data[]; (C99 flexible array)
};

// Allocate variable-size structure
size_t n = 10;
FlexibleArray* fa = (FlexibleArray*)malloc(
    sizeof(FlexibleArray) + n * sizeof(int)
);
fa->count = n;
fa->data[5] = 42;  // Access extended data
```

**Use**: Serialization, variable-size packets.

## Inspecting Padding
```cpp showLineNumbers
struct Data {
    char c;
    int i;
    char c2;
};

// Print offsets
std::cout << "c offset: " << offsetof(Data, c) << "\n";    // 0
std::cout << "i offset: " << offsetof(Data, i) << "\n";    // 4
std::cout << "c2 offset: " << offsetof(Data, c2) << "\n";  // 8
std::cout << "size: " << sizeof(Data) << "\n";             // 12

// Padding:
// After c: 4 - 0 - 1 = 3 bytes
// After c2: 12 - 8 - 1 = 3 bytes
```

## Practical Example: Network Protocol
```cpp showLineNumbers
struct NetworkPacket {
    uint32_t magic;      // offset 0
    uint16_t version;    // offset 4
    uint16_t flags;      // offset 6
    uint32_t length;     // offset 8
    uint8_t data[1024];  // offset 12
};

static_assert(offsetof(NetworkPacket, data) == 12);
static_assert(std::is_standard_layout_v<NetworkPacket>);

// Safe for binary I/O
void send(const NetworkPacket& packet) {
    write(socket, &packet, sizeof(packet));
}
```

## Padding in Inheritance
```cpp showLineNumbers
struct Base {
    char c;
    // 3 padding
    int i;
};  // sizeof = 8

struct Derived : Base {
    char c2;
    // 3 padding (inherited padding not reused)
};  // sizeof = 12
```

**Note**: Derived class doesn't reuse base class padding.

## Summary

- Padding aligns struct members to hardware requirements (CPU needs aligned access).
- Compiler inserts padding to ensure each member is properly aligned.
- Struct size must be multiple of largest member alignment for array support.

:::info
- Rule 1: Each member aligned to its size
- Rule 2: Struct aligned to largest member
- Rule 3: Size = multiple of alignment (for arrays)
---
- Minimize: Order large→small, fill gaps
- Check: `offsetof(Type, member)` returns byte offset, but only for standard-layout types
- Only safe for: standard-layout types
:::

```cpp
// Interview answer:
// "Padding aligns struct members - compiler inserts bytes so
// each member's address is divisible by its alignment. Struct
// size must be multiple of largest member alignment for arrays.
// offsetof(Type, member) queries byte offset, but only defined
// for standard-layout types. Minimize padding by ordering
// members large to small. Critical for binary protocols and
// memory optimization. Example: char (1), int (4), char (1)
// becomes 12 bytes with padding, not 6."
```