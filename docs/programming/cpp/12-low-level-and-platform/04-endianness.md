---
id: endianness
title: Endianness
sidebar_label: Endianness
sidebar_position: 4
tags: [cpp, endianness, byte-order, byteswap, serialization, portability]
---

# Endianness

**Endianness** is the order in which the bytes of a multi-byte value are stored in memory.
**Little-endian** stores the least significant byte at the lowest address, **big-endian** the most significant
byte. Inside one program you never see it: arithmetic and comparisons act on values, not bytes. It matters in exactly one
situation: the program's bytes meet someone else's interpretation of them, as in a file, a socket, a
shared-memory region, a hardware register or a different architecture. So the rule for this page is
**convert at the edge**: keep values in native form inside the program and fix the byte order in the code that
reads or writes the external format.

**Prerequisites:** [Fundamental types](../03-types-and-values/fundamental-types.md) (fixed-width integers),
[strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md) (why not to read bytes through a
cast pointer), [Padding and offsetof](./03-padding-and-offsetof.md) (why not to write a struct as-is).

<Diagram title="0x12345678 as a 32-bit integer in memory" caption="Same value, opposite byte order. Addresses increase to the right." accent="blue">
  <DiagramGroup label="Little-endian (x86-64, AArch64 by default)">
    <DiagramRow>
      <DiagramNode title="+0">78</DiagramNode>
      <DiagramNode title="+1">56</DiagramNode>
      <DiagramNode title="+2">34</DiagramNode>
      <DiagramNode title="+3" accent>12</DiagramNode>
    </DiagramRow>
  </DiagramGroup>
  <DiagramGroup label="Big-endian (network order)">
    <DiagramRow>
      <DiagramNode title="+0" accent>12</DiagramNode>
      <DiagramNode title="+1">34</DiagramNode>
      <DiagramNode title="+2">56</DiagramNode>
      <DiagramNode title="+3">78</DiagramNode>
    </DiagramRow>
  </DiagramGroup>
</Diagram>

## Asking which one you have: `std::endian`

`std::endian` *(C++20, `<bit>`)* is an enum with three enumerators, `little`, `big` and `native`.
`native` equals `little` on a little-endian target and `big` on a big-endian one. If the target is
neither (the standard allows "mixed" orders), `native` equals neither, so portable code asserts it:

```cpp title="endian.cpp" showLineNumbers
#include <bit>

static_assert(std::endian::native == std::endian::little ||
              std::endian::native == std::endian::big,
              "mixed-endian targets are not supported");

int main() {}
```

Use it in `if constexpr`. Do not detect byte order at run time by reading an integer's first byte through
a cast pointer, which is a [strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md)
question, and do not reach for `<endian.h>` macros, which are a glibc/BSD extension, not C++.

On x86-64 the compile-time answer is `little`. On this machine (g++ 15 and clang++ 21, x86-64 Linux, `-O0`
and `-O2`), `memcpy`-ing `0x12345678` into a byte array gave `78 56 34 12`. No big-endian target was
available, so the big-endian rows on this page follow from the definitions, not from a run.

## Swapping bytes: `std::byteswap`

`std::byteswap(x)` *(C++23, `<bit>`)* returns `x` with the order of its bytes reversed. It accepts integral types,
is `constexpr`, and is a no-op for one-byte types. Compiling with `-std=c++20` fails with "`byteswap` is not a
member of `std`" on both g++ 15 and clang++ 21, so before C++23 you need a fallback such as
`__builtin_bswap32` (GCC, Clang), `_byteswap_ulong` (MSVC, `<stdlib.h>`) or the shift version below.

```cpp title="byteswap.cpp  (-std=c++23)" showLineNumbers
#include <bit>
#include <concepts>
#include <cstdint>
#include <cstdio>

static_assert(std::byteswap(std::uint32_t{0x12345678}) == 0x78563412);
static_assert(std::byteswap(std::uint16_t{0x1234}) == 0x3412);

template <std::integral T>
constexpr T to_big_endian(T v) {
    if constexpr (std::endian::native == std::endian::little) return std::byteswap(v);
    else return v;                                   // already big-endian
}

int main() {
    std::printf("%08x\n", to_big_endian(std::uint32_t{0x12345678}));
}
```

```text
78563412
```

(g++ 15 and clang++ 21, `-std=c++23`, `-O0` and `-O2`, x86-64 Linux.)

`to_big_endian` is the same function for the opposite direction, because swapping is its own inverse. The
result is a value whose *in-memory bytes* are in big-endian order, not a number that means the same
thing: do not do arithmetic on it. Keep it as the thing to write out.

## Reading and writing a fixed byte order portably

The most portable form does not mention the host byte order at all: build the value from bytes with shifts. Shifts
act on values, so the result is the same on every target, and compilers recognise the pattern and emit a single load plus
`bswap` where it is profitable.

```cpp title="be32.cpp" showLineNumbers
#include <cstdint>
#include <cstdio>

constexpr std::uint32_t load_be32(const unsigned char* p) {
    return std::uint32_t{p[0]} << 24 | std::uint32_t{p[1]} << 16 |
           std::uint32_t{p[2]} << 8  | std::uint32_t{p[3]};
}
constexpr void store_be32(unsigned char* p, std::uint32_t v) {
    p[0] = static_cast<unsigned char>(v >> 24);
    p[1] = static_cast<unsigned char>(v >> 16);
    p[2] = static_cast<unsigned char>(v >> 8);
    p[3] = static_cast<unsigned char>(v);
}

int main() {
    unsigned char be[4];
    store_be32(be, 0x12345678);
    std::printf("%02x %02x %02x %02x -> %08x\n", be[0], be[1], be[2], be[3], load_be32(be));
}
```

```text
12 34 56 78 -> 12345678
```

(g++ 15 and clang++ 21, `-std=c++20`, `-O0` and `-O2`; a `static_assert` of the same round trip also holds
at compile time.) Note the `std::uint32_t{p[0]}` before the shift: a bare `p[0] << 24` is done in `int`, giving a negative value for bytes of 0x80 and above (implementation-defined before C++20) and undefined behaviour once the shift exceeds the width, as in a 64-bit variant. Keep the unsigned type.

The same pattern with `<<` swapped for loops handles 16 and 64 bits and little-endian formats. Write the
load/store pair once per width and use it for every field; do not `memcpy` a whole struct.

### Four ways to touch the bytes of an object

| Technique | Verdict |
|---|---|
| `std::memcpy(buf, &v, sizeof v)` | Defined. Copies *native* order. Combine with `std::byteswap` when the format differs |
| `std::bit_cast<std::array<unsigned char, 4>>(v)` *(C++20)* | Defined. Same bytes as `memcpy`, usable in `constexpr` |
| `*reinterpret_cast<uint32_t*>(buf)` on a byte buffer | Undefined (aliasing and alignment). See [strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md) |
| Reading a union member other than the one last written | Allowed in C, not in C++. See [strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md#unions-are-not-a-portable-alternative) |

## Network byte order

Internet protocols transmit multi-byte integers in big-endian order (**network byte order**). POSIX
provides `htons`, `htonl` (host to network) and `ntohs`, `ntohl` (network to host) in `<arpa/inet.h>`;
Windows has the same names in `<winsock2.h>`. They are 16- and 32-bit only and they swap or not depending
on the host, so the same code is correct everywhere. For 64 bits there is no standard function; use
`std::byteswap` or the shift helpers.

```cpp title="htonl.cpp  (POSIX)" showLineNumbers
#include <arpa/inet.h>
#include <cstdio>

int main() {
    std::printf("%08x %04x\n", htonl(0x12345678), htons(0x1234));
}
```

```text
78563412 3412
```

(x86-64 Linux, little-endian. On a big-endian host both functions are identities and it would print `12345678 1234`.)
The returned `uint32_t` holds a value whose bytes, if you copy them out, are in network order. Do not
compare or add it to other numbers.

## A header, written the right way

Instead of filling a struct and sending it (padding, alignment and byte order all depend on the host), write each field with the
helper for its width:

```cpp title="wire.cpp (fragment)" showLineNumbers
struct PacketHeader { std::uint16_t magic, version; std::uint32_t length; };

void encode(const PacketHeader& h, unsigned char out[8]) {
    store_be16(out + 0, h.magic);
    store_be16(out + 2, h.version);
    store_be32(out + 4, h.length);
}
```

Here `store_be16` is the 16-bit counterpart of `store_be32`. The in-memory struct can then change without
changing the format, and the format is documented by the code. This is the
[ABI](./01-abi.md)-independent alternative to the layout-pinning of
[Padding and offsetof](./03-padding-and-offsetof.md).

## Where endianness still shows up

- **Bit-fields**: the order in which fields of a bit-field struct land in a byte is implementation-defined and
  often depends on endianness. Use masks and shifts for registers and protocols.
- **Floating point**: `float` and `double` have a byte order too. Move them as their integer bit
  pattern: `std::bit_cast<std::uint32_t>(f)` then the integer helpers. On this machine `1.0f` gave
  `3f800000`. IEEE 754 layout is common but the C++ standard does not require it.
- **Text**: UTF-16 and UTF-32 files carry a byte-order mark or a declared order. UTF-8 has none.
- **Hardware**: a memory-mapped register block has the device's byte order, which may differ from the
  CPU's. See [volatile](./05-volatile.md).

## Which targets are which

x86-64 is little-endian. AArch64 Linux, Android and Apple platforms run little-endian by default; the
architecture can also be configured big-endian. Some architectures, for instance POWER, are bi-endian: the byte
order depends on the toolchain target, such as `powerpc64le` versus `powerpc64`. IBM Z (s390x) is big-endian. Treat any such list as a
hint and let `std::endian::native` tell you for the target you build.

## Key points

- Endianness is invisible to arithmetic and visible only when bytes cross a boundary: convert there, and only there.
- `std::endian` *(C++20)* names the native order at compile time. `std::byteswap` *(C++23)* reverses
  bytes. In C++20 use the compiler builtin or shifts.
- The portable read/write is shift-based on `unsigned` values (or `memcpy` plus `byteswap`). Never
  `reinterpret_cast` a buffer to an integer pointer.
- Network byte order is big-endian. `htonl`/`ntohl` are POSIX and 32-bit; write the 64-bit one yourself.
- Serialise field by field instead of writing a struct, which brings padding and ABI problems on top.

## References

- [cppreference: `std::endian`](https://en.cppreference.com/w/cpp/types/endian)
- [cppreference: `std::byteswap`](https://en.cppreference.com/w/cpp/numeric/byteswap)
- [POSIX: `htonl`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/htonl.html)
