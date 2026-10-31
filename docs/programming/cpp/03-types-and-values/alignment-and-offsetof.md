---
id: alignment-and-offsetof
title: Alignment and offsetof
sidebar_label: Alignment
sidebar_position: 7
tags: [c++, alignment, offsetof, alignof, alignas]
---

# Alignment and `offsetof`

Besides a size, every object type has an **alignment**: a power of two that the object's address
must be a multiple of. Alignment is a property of the type, like `sizeof`, and the language gives
you three tools for it: `alignof` *(C++11)* to query it, `alignas` *(C++11)* to strengthen it, and
the `offsetof` macro to see where a member landed after the compiler inserted padding. This page is
the reference for those three tools.

Why padding exists and how to order members to avoid it, cache-line and SIMD alignment, and packing
are on the canonical [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) page. Layout
as a binary contract (serialization, bit-fields) is on
[Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md).

**Prerequisites:** [Fundamental Types](./fundamental-types.md)

## `alignof`

`alignof(T)` is a `std::size_t` constant expression. The values for fundamental types are set by
the platform ABI, not by the standard; the ones below are from GCC 15 on x86-64 Linux:

```cpp title="alignof.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>

struct Record {
    char  tag;
    int   value;
    short count;
};

int main() {
    std::printf("char %zu, short %zu, int %zu, double %zu, void* %zu, max_align_t %zu\n",
                alignof(char), alignof(short), alignof(int), alignof(double),
                alignof(void*), alignof(std::max_align_t));
    std::printf("Record: alignof %zu, sizeof %zu\n", alignof(Record), sizeof(Record));
    std::printf("offsets: tag %zu, value %zu, count %zu\n",
                offsetof(Record, tag), offsetof(Record, value), offsetof(Record, count));
}
```

```text
char 1, short 2, int 4, double 8, void* 8, max_align_t 16
Record: alignof 4, sizeof 12
offsets: tag 0, value 4, count 8
```

A class's alignment is the largest alignment among its members (and bases). `alignof(char)` is
1 everywhere. `std::max_align_t` (`<cstddef>`) is a type whose alignment is at least as strict as
every scalar type; `malloc` and default `operator new` return memory aligned for it.

## `offsetof`

`offsetof(Type, member)` (`<cstddef>`) is the byte offset of `member` from the start of a `Type`
object, as a `std::size_t` constant expression. For `Record` it shows the padding the compiler
inserted:

<Diagram title="Record on x86-64: 12 bytes" accent="amber">
  <DiagramRow>
    <DiagramNode title="tag">offset 0, 1 byte</DiagramNode>
    <DiagramNode title="padding" dashed>offsets 1–3</DiagramNode>
    <DiagramNode title="value" accent>offset 4, 4 bytes, aligned to 4</DiagramNode>
    <DiagramNode title="count">offset 8, 2 bytes</DiagramNode>
    <DiagramNode title="tail padding" dashed>offsets 10–11, so the next array element is aligned</DiagramNode>
  </DiagramRow>
</Diagram>

Restrictions:

- `Type` should be a **standard-layout** class (`std::is_standard_layout_v<Type>`). For other
  types, using `offsetof` was undefined behavior before C++17 and is *conditionally-supported*
  since C++17 ([cppreference](https://en.cppreference.com/w/cpp/types/offsetof)). GCC and Clang
  accept it with an `-Winvalid-offsetof` warning, but the value is meaningless for classes with
  virtual bases.
- `member` can't be a static member, a member function, or a bit-field.

When code depends on a layout, assert it:

```cpp title="assert-layout.cpp" showLineNumbers
#include <cstddef>
#include <type_traits>

struct Header {
    unsigned magic;
    unsigned short version;
    unsigned short flags;
};

static_assert(std::is_standard_layout_v<Header>);
static_assert(offsetof(Header, flags) == 6);
static_assert(sizeof(Header) == 8);

int main() {}
```

## `alignas`

`alignas(N)` on a variable, a non-static data member, or a class definition requests alignment `N`.
`alignas(T)` means `alignas(alignof(T))`.

```cpp title="alignas.cpp" showLineNumbers
#include <cstdio>

struct alignas(16) Vec4 { float v[4]; };     // the whole type, e.g. for SSE loads

struct Counters {
    alignas(64) long hot;                    // starts its own 64-byte block
    long cold;
};

int main() {
    alignas(double) unsigned char buf[sizeof(double)];   // raw storage suitable for a double
    std::printf("%zu %zu %zu %zu\n", alignof(Vec4), alignof(Counters), sizeof(Counters),
                alignof(decltype(buf)));
}
```

```text
16 64 64 1
```

`Counters` is 64 bytes: `hot` starts at offset 0 and `cold` fits in the same 64-byte block, and the
size is rounded up to the alignment. The last value is 1 because `alignas` on a variable aligns that variable, not its type:
`decltype(buf)` is still `unsigned char[8]`. Use `alignof(Vec4)`-style queries on types you have
declared with `alignas`.

Rules:

- `N` must be zero (ignored) or a power of two that the implementation supports. Values above
  `alignof(std::max_align_t)` are **over-aligned**; dynamic allocation honors them only since C++17
  (`operator new` with `std::align_val_t`).
- `alignas` can only strengthen. If the strictest `alignas` on a declaration is weaker than the
  type's natural alignment, the program is ill-formed. Clang 21 rejects `alignas(1) int x;`; GCC 15
  accepts it without a diagnostic and places `x` at an odd address, so don't rely on it. To reduce
  alignment, use a compiler extension such as `#pragma pack`, described on the canonical page.

## Key points

- `alignof(T)` is a power of two set by the ABI; a class takes its strictest member's.
- `offsetof` reports where members are; use it on standard-layout types and `static_assert` the
  layouts you depend on.
- `alignas` only strengthens, and applies to a declaration, not to the declared type of a variable.
