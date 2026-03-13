---
id: alignment-and-offsetof
title: Alignment and offsetof
sidebar_label: Alignment
sidebar_position: 8
tags: [c++, alignment, offsetof, memory-layout, padding]
---

# Alignment and `offsetof`

Every type has an **alignment**: an address it must start on, always a power of two. `char` can live
anywhere; an `int` must sit at an address divisible by 4; a `double` at one divisible by 8. This page
covers alignment *as a property of types* and the `offsetof` macro that reports where members land.

:::info This is the type-system view
Here: `alignof`, `alignas`, and `offsetof` as language tools. For *why* padding exists, how to order
members to shrink a struct, cache-line/SIMD alignment, and packing — see the canonical
[Memory Alignment](../05-memory-and-object-lifetime/alignment.md) page. For the ABI / wire-format
angle (serialization, bit-fields, standard-layout rules) see
[Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md).
:::

## `alignof` — a type's required alignment

```cpp showLineNumbers
#include <cstddef>

alignof(char);    // 1
alignof(int);     // 4
alignof(double);  // 8
alignof(void*);   // 8 on a 64-bit target

struct Widget { char c; int i; };
alignof(Widget);  // 4 — a struct's alignment is that of its strictest member
```

The corollary that surprises people: because members must each be aligned, the compiler inserts
**padding**, so `sizeof` is usually larger than the sum of the member sizes.

```cpp showLineNumbers
struct Example {
    char c;   // offset 0
    int  i;   // offset 4 — 3 bytes of padding sit between them
};
sizeof(Example);   // 8, not 5
```

## `offsetof` — where a member sits

`offsetof(Type, member)` (from `<cstddef>`) returns the member's byte offset from the start of the
object. It makes the padding above observable:

```cpp showLineNumbers
struct Record {
    char  tag;    // offset 0
    int   value;  // offset 4  (after 3 padding bytes)
    short count;  // offset 8
};

offsetof(Record, tag);    // 0
offsetof(Record, value);  // 4
offsetof(Record, count);  // 8
```

:::warning `offsetof` is only defined for standard-layout types
Using it on a type with virtual functions or a non-trivial base is **undefined behaviour** — those
types have no fixed, simple member offsets. Guard real code with a `static_assert`:

```cpp
static_assert(std::is_standard_layout_v<Record>);
```
:::

## `alignas` — requesting stronger alignment

`alignas(N)` raises (never lowers) the alignment of a variable, member, or type. The two everyday
uses — cache-line isolation and SIMD — are covered on the [canonical page](../05-memory-and-object-lifetime/alignment.md#common-use-cases); the syntax is:

```cpp showLineNumbers
alignas(64) int hot_counter;          // start on a 64-byte boundary

struct alignas(16) Vec4 { float v[4]; };   // whole type aligned to 16 (SIMD)
```

## Summary

- Alignment is a per-type, power-of-two requirement; a struct inherits its strictest member's.
- Padding makes `sizeof` exceed the member sizes; `offsetof` lets you see exactly where members land.
- `offsetof` is well-defined only for standard-layout types — assert it.
- `alignas(N)` strengthens alignment; the layout-optimisation details live on the canonical page.

## Related

- [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) — padding, ordering, cache lines, SIMD, packing
- [Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md) — serialization, bit-fields, standard layout
- [Fundamental Types](./fundamental-types.md) · [Object Layout](../12-low-level-and-platform/02-object-layout.md)
