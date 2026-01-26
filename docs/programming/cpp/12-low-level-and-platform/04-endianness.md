---
id: endianness
title: Endianness
sidebar_label: Endianness
sidebar_position: 4
tags: [cpp, endianness, byte-order, portability, binary]
---

# Endianness

Byte order in multi-byte values. 
- **Little-endian** stores least significant byte first
- **big-endian** stores most significant byte first. Critical for binary I/O and network protocols.

:::info Network Byte Order
Network protocols use **big-endian** (network byte order). x86/x86-64/ARM are typically **little-endian**.
:::

## Little vs Big Endian
```cpp showLineNumbers
uint32_t value = 0x12345678;

// Little-endian (x86, x86-64, ARM):
// Address: [0x00] [0x01] [0x02] [0x03]
// Bytes:   [0x78] [0x56] [0x34] [0x12]
//           ^^^^LSB         ^^^^MSB

// Big-endian (network, some RISC):
// Address: [0x00] [0x01] [0x02] [0x03]
// Bytes:   [0x12] [0x34] [0x56] [0x78]
//           ^^^^MSB         ^^^^LSB
```

**Visualization:**
```
Value: 0x12345678

Little-endian memory:
  +----+----+----+----+
  | 78 | 56 | 34 | 12 |
  +----+----+----+----+
   LSB            MSB

Big-endian memory:
  +----+----+----+----+
  | 12 | 34 | 56 | 78 |
  +----+----+----+----+
   MSB            LSB
```

## Detecting Endianness
```cpp showLineNumbers
#include <cstdint>

bool isLittleEndian() {
    uint32_t test = 1;
    return *reinterpret_cast<uint8_t*>(&test) == 1;
}

// Or at compile-time (C++20)
constexpr bool isLittleEndian() {
    return std::endian::native == std::endian::little;
}
```

### Platform Macros
```cpp showLineNumbers
#include <endian.h>  // Linux
// or
#include <sys/param.h>  // BSD

#if __BYTE_ORDER == __LITTLE_ENDIAN
    // Little-endian system
#elif __BYTE_ORDER == __BIG_ENDIAN
    // Big-endian system
#endif
```

## Byte Swapping
```cpp showLineNumbers
#include <cstdint>

// Swap 16-bit
uint16_t swap16(uint16_t value) {
    return (value >> 8) | (value << 8);
}

// Swap 32-bit
uint32_t swap32(uint32_t value) {
    return ((value >> 24) & 0x000000FF) |
           ((value >>  8) & 0x0000FF00) |
           ((value <<  8) & 0x00FF0000) |
           ((value << 24) & 0xFF000000);
}

// Swap 64-bit
uint64_t swap64(uint64_t value) {
    return ((value >> 56) & 0x00000000000000FFULL) |
           ((value >> 40) & 0x000000000000FF00ULL) |
           ((value >> 24) & 0x0000000000FF0000ULL) |
           ((value >>  8) & 0x00000000FF000000ULL) |
           ((value <<  8) & 0x000000FF00000000ULL) |
           ((value << 24) & 0x0000FF0000000000ULL) |
           ((value << 40) & 0x00FF000000000000ULL) |
           ((value << 56) & 0xFF00000000000000ULL);
}
```

### Compiler Intrinsics (Faster)
```cpp showLineNumbers
// GCC/Clang
uint16_t swap16(uint16_t x) {
    return __builtin_bswap16(x);
}

uint32_t swap32(uint32_t x) {
    return __builtin_bswap32(x);
}

uint64_t swap64(uint64_t x) {
    return __builtin_bswap64(x);
}

// MSVC
#include <intrin.h>
uint16_t swap16(uint16_t x) {
    return _byteswap_ushort(x);
}
```

**Benefit**: Compiles to single CPU instruction (e.g., `bswap`).

## Network Byte Order Conversion
```cpp showLineNumbers
#include <arpa/inet.h>  // POSIX

// Host to network (big-endian)
uint16_t port_network = htons(8080);  // Host to network short
uint32_t addr_network = htonl(0x7F000001);  // Host to network long

// Network to host
uint16_t port_host = ntohs(port_network);
uint32_t addr_host = ntohl(addr_network);
```

**Portable**: These functions handle endianness automatically.

## Binary File I/O

### Writing (Portable)
```cpp showLineNumbers
#include <fstream>
#include <cstdint>

void writeInt32(std::ofstream& file, uint32_t value) {
    // Always write big-endian
    uint32_t network_order = htonl(value);
    file.write(reinterpret_cast<const char*>(&network_order), 
               sizeof(network_order));
}

void writeInt16(std::ofstream& file, uint16_t value) {
    uint16_t network_order = htons(value);
    file.write(reinterpret_cast<const char*>(&network_order), 
               sizeof(network_order));
}
```

### Reading (Portable)
```cpp showLineNumbers
uint32_t readInt32(std::ifstream& file) {
    uint32_t network_order;
    file.read(reinterpret_cast<char*>(&network_order), 
              sizeof(network_order));
    return ntohl(network_order);  // Convert to host order
}

uint16_t readInt16(std::ifstream& file) {
    uint16_t network_order;
    file.read(reinterpret_cast<char*>(&network_order), 
              sizeof(network_order));
    return ntohs(network_order);
}
```

## Network Protocol Example
```cpp showLineNumbers
struct PacketHeader {
    uint16_t magic;
    uint16_t version;
    uint32_t length;
};

void sendPacket(int socket, const PacketHeader& header) {
    PacketHeader network_header;
    network_header.magic = htons(header.magic);
    network_header.version = htons(header.version);
    network_header.length = htonl(header.length);
    
    send(socket, &network_header, sizeof(network_header), 0);
}

PacketHeader receivePacket(int socket) {
    PacketHeader network_header;
    recv(socket, &network_header, sizeof(network_header), 0);
    
    PacketHeader header;
    header.magic = ntohs(network_header.magic);
    header.version = ntohs(network_header.version);
    header.length = ntohl(network_header.length);
    
    return header;
}
```

## C++20 std::endian
```cpp showLineNumbers
#include <bit>

if constexpr (std::endian::native == std::endian::little) {
    // Little-endian system
} else if constexpr (std::endian::native == std::endian::big) {
    // Big-endian system
}

// Generic byte swap
template<typename T>
T byteSwap(T value) {
    if constexpr (std::endian::native == std::endian::big) {
        return value;  // Already in network order
    } else {
        return __builtin_bswap32(value);  // Convert
    }
}
```

## Common Platforms

| Platform       | Endianness |
|----------------|------------|
| **x86**        | Little     |
| **x86-64**     | Little     |
| **ARM (most)** | Little     |
| **ARM (some)** | Bi-endian  |
| **MIPS**       | Bi-endian  |
| **PowerPC**    | Big        |
| **Network**    | Big        |
| **JVM**        | Big        |

## Pitfalls
```cpp showLineNumbers
// ❌ Wrong: direct binary write (not portable)
uint32_t value = 0x12345678;
file.write(reinterpret_cast<char*>(&value), sizeof(value));
// Different byte order on different systems!

// ✅ Right: convert to fixed byte order
uint32_t network_value = htonl(value);
file.write(reinterpret_cast<char*>(&network_value), sizeof(network_value));

// ❌ Wrong: type punning with endianness assumptions
union {
    uint32_t i;
    char bytes[4];
} u;
u.i = 0x12345678;
// bytes[0] is 0x78 on little-endian, 0x12 on big-endian
```

## Summary

:::info Endianness
**Endianness** is byte order in multi-byte values
- Little-endian: `0x12345678 → [78][56][34][12]` (LSB first)
- Big-endian:    `0x12345678 → [12][34][56][78]` (MSB first)
:::

:::info
- Networks = Big-endian (always)
- x86/ARM = Little-endian (usually)
- Portable I/O = `htonl/htons` (host→network) and `ntohl/ntohs` (network→host) (POSIX)
- Never write multi-byte types directly to files/network without conversion.
- Compiler intrinsics (`__builtin_bswap32`) provide fast byte swapping. C++20 `std::endian` for compile-time detection.
:::

```cpp
// Interview answer:
// "Endianness is byte order for multi-byte values. Little-endian
// (x86, ARM) stores LSB first; big-endian (network, some RISC)
// stores MSB first. Network protocols use big-endian. For
// portability, use htonl/ntohl (POSIX) to convert between host
// and network byte order. Never write multi-byte values directly
// to binary files/network - always convert to fixed endianness.
// C++20 provides std::endian for compile-time detection."
```
