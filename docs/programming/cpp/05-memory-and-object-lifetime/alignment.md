---
id: memory-alignment
title: Memory Alignment
sidebar_label: Memory Alignment
sidebar_position: 7
tags: [c++, alignment, alignas, alignof, over-aligned, padding]
---

# Memory Alignment

Every object type has an **alignment requirement**: a power of two, and every object of that type
must start at an address that is a multiple of it. An `int` on x86-64 needs a multiple of 4, a
`double` a multiple of 8. The compiler meets these requirements for variables and members by itself,
which is where struct padding comes from. You have to handle them yourself when you provide raw
storage (placement new, pools, `reinterpret_cast` on byte buffers) or when you want stronger
alignment than the default, for cache lines or SIMD. This page is the canonical home for
`alignof`, `alignas`, over-aligned types and aligned allocation.

**Prerequisites:** [Fundamental types](../03-types-and-values/fundamental-types.md),
[process memory overview](./memory-model-overview.md).

Related pages: [Alignment and offsetof](../03-types-and-values/alignment-and-offsetof.md) shows how to
inspect member offsets, [class layout](../07-classes-and-oop/class-layout.md) covers how a class's
members, bases and vptr are placed, and [Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md)
covers ABI concerns, packing and bit-fields.

## Why alignment exists

The CPU loads and stores memory in naturally aligned units. An aligned 4-byte `int` is always inside
one cache line and one page, so one access is enough. A misaligned one may straddle two. Some
architectures handle that in hardware (x86, modern ARMv8 for ordinary loads), some trap, and some
instructions trap even on x86, for example the aligned SSE load `movaps`.

The C++ rule does not depend on the hardware: **accessing an object through a misaligned pointer is
undefined behavior**, and the compiler may emit instructions that assume alignment. Code that
"works on x86" can crash after a compiler upgrade enables vectorization. UBSan reports misaligned
accesses with `-fsanitize=alignment`.

## `alignof`: query the requirement

`alignof(T)` *(C++11)* is a constant expression of type `std::size_t`. Values measured with g++ 15 and
clang++ 21 on x86-64 Linux (they are ABI-defined and differ on other platforms, for example `long`
is 4 bytes on Windows and on 32-bit targets):

| Type | `sizeof` | `alignof` |
|---|---|---|
| `char` | 1 | 1 |
| `short` | 2 | 2 |
| `int`, `float` | 4 | 4 |
| `long`, `double`, `T*` | 8 | 8 |
| `long double` (x87 80-bit) | 16 | 16 |
| `std::max_align_t` | 32 | 16 |
| Class | at least the sum of members, rounded up | strictest member or base |

`std::max_align_t` (in `<cstddef>`) is the type with the largest **fundamental alignment**. Any
alignment above `alignof(std::max_align_t)` is an **extended alignment**. An implementation may
refuse extended alignments in some contexts. GCC and Clang accept them everywhere that matters.

## Padding: the compiler's half of the job

Inside a class, each member is placed at the next offset that satisfies its alignment, and the total
size is rounded up to a multiple of the class's alignment, so that every element of an array of the
class is aligned too.

```cpp title="padding.cpp" showLineNumbers
#include <cstddef>

struct Bad  { char c; int i; char c2; };   // 1 + 3 pad + 4 + 1 + 3 pad
struct Good { int i; char c; char c2; };   // 4 + 1 + 1 + 2 pad

static_assert(sizeof(Bad) == 12 && alignof(Bad) == 4);
static_assert(sizeof(Good) == 8 && alignof(Good) == 4);
static_assert(offsetof(Bad, i) == 4);        // not 1: int needs a multiple of 4

int main() {}
```

<Diagram title="struct Bad on x86-64 (12 bytes)" caption="Shaded padding bytes exist only to keep i aligned and to keep arrays of Bad aligned." accent="amber">
  <DiagramRow>
    <DiagramNode title="c">offset 0</DiagramNode>
    <DiagramNode title="pad" dashed>offsets 1-3</DiagramNode>
    <DiagramNode title="i" accent>offsets 4-7, aligned to 4</DiagramNode>
    <DiagramNode title="c2">offset 8</DiagramNode>
    <DiagramNode title="tail pad" dashed>offsets 9-11, so sizeof is a multiple of 4</DiagramNode>
  </DiagramRow>
</Diagram>

Ordering members from largest to smallest alignment usually removes most padding, as `Good` shows.
The compiler will not reorder members for you: non-static data members are laid out in declaration
order (for members with different access specifiers this became guaranteed in C++23, P1847, and is
what GCC, Clang and MSVC always did). Tools such as `pahole` show the holes in real binaries.

## `alignas`: ask for more

`alignas(N)` *(C++11)* applies to a variable, a non-static data member, or a class. `N` must be a
valid alignment (a power of two that the implementation supports), or `alignas(T)` gives the
alignment of type `T`. Rules worth knowing:

- `alignas` can only **strengthen** alignment. A request weaker than the natural one is ill-formed.
  Clang 21 rejects it. GCC 15 accepts it without a diagnostic, even with `-pedantic`, and keeps the
  natural alignment. `alignas(0)` is ignored.
- If several `alignas` apply to one entity, the strictest wins.
- On a class, it raises the class's alignment, and `sizeof` grows to a multiple of it.
- It cannot be applied to function parameters or bit-fields.

```cpp title="alignas.cpp" showLineNumbers
#include <cstddef>

struct alignas(64) CacheLine { int counter; };            // occupies a full 64-byte line
static_assert(alignof(CacheLine) == 64 && sizeof(CacheLine) == 64);

struct Vec8 { alignas(32) float lanes[8]; };              // for 256-bit AVX loads
static_assert(alignof(Vec8) == 32);

alignas(CacheLine) std::byte raw[sizeof(CacheLine)];      // storage for placement new

int main() { return static_cast<int>(sizeof(raw)) - 64; } // returns 0
```

## Common use cases

### Avoiding false sharing

Two threads that write different variables in the **same cache line** force the line to move between
cores on every write. Putting each frequently written variable in its own line removes that.
`std::hardware_destructive_interference_size` *(C++17, `<new>`)* is the minimum offset that avoids
false sharing. It is 64 with GCC 15 on x86-64. GCC warns (`-Winterference-size`) if you use it in a
header, because the value can differ between compiler settings and so between translation units.

```cpp title="false-sharing.cpp" showLineNumbers
#include <atomic>
#include <new>
#include <thread>

struct Counters {
    alignas(std::hardware_destructive_interference_size) std::atomic<long> a{0};
    alignas(std::hardware_destructive_interference_size) std::atomic<long> b{0};
};

int main() {
    Counters c;
    std::thread t1([&] { for (int i = 0; i < 1'000'000; ++i) c.a.fetch_add(1, std::memory_order_relaxed); });
    std::thread t2([&] { for (int i = 0; i < 1'000'000; ++i) c.b.fetch_add(1, std::memory_order_relaxed); });
    t1.join();
    t2.join();
    return static_cast<int>(c.a + c.b - 2'000'000);   // returns 0
}
```

How much this gains depends on the CPU and the access pattern. Measure with and without the
`alignas` on your target before keeping the extra memory cost.

### SIMD buffers

Aligned vector loads (`_mm256_load_ps`) require 32-byte alignment. Unaligned variants
(`_mm256_loadu_ps`) accept any address. Over-aligned buffers let you use the aligned forms and keep
loads inside one cache line. Declare the buffer with `alignas(32)`, or allocate it with an aligned
allocator, as below.

### Raw storage for placement new

Storage for a `T` must be `alignas(T)`. See [placement new](./placement-new.md#the-storage-requirements).

## Over-aligned types and `new`

The default `operator new` returns memory aligned to `__STDCPP_DEFAULT_NEW_ALIGNMENT__` *(C++17)*,
which is 16 with GCC and Clang on x86-64 Linux. Before C++17, `new` of a type with stronger alignment
silently returned under-aligned memory. Since C++17, for a type with
`alignof(T) > __STDCPP_DEFAULT_NEW_ALIGNMENT__`, a `new`-expression calls the aligned overload
`operator new(std::size_t, std::align_val_t)`, and `delete` calls the matching aligned
`operator delete`. Containers using `std::allocator` get the same behavior.

```cpp title="overaligned-new.cpp" showLineNumbers
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <vector>

struct alignas(64) Block { char data[64]; };

int main() {
    auto p = std::make_unique<Block>();               // uses aligned operator new
    std::vector<Block> v(4);                          // std::allocator does too
    void* q = ::operator new(100, std::align_val_t{128});   // direct call
    void* r = std::aligned_alloc(64, 256);            // C11/C++17: size must be a multiple of 64

    auto mis = [](const void* x, std::size_t a) { return reinterpret_cast<std::uintptr_t>(x) % a; };
    std::printf("%zu %zu %zu %zu\n", mis(p.get(), 64), mis(v.data(), 64), mis(q, 128), mis(r, 64));

    ::operator delete(q, std::align_val_t{128});      // must pass the same alignment
    std::free(r);
}
```

Output (all zero: every pointer is aligned):

```text
0 0 0 0
```

`std::aligned_alloc` is not available with MSVC, whose C runtime cannot free such memory with `free`.
There, use `_aligned_malloc`/`_aligned_free`, or simply `operator new` with `std::align_val_t`, which
is portable.

## Checking and adjusting alignment at run time

```cpp title="runtime.cpp" showLineNumbers
#include <cstddef>
#include <cstdint>
#include <memory>

bool is_aligned(const void* p, std::size_t a) {
    return reinterpret_cast<std::uintptr_t>(p) % a == 0;
}

int main() {
    alignas(16) unsigned char buf[64];
    void* p = buf + 1;                    // deliberately misaligned
    std::size_t space = sizeof(buf) - 1;
    void* aligned = std::align(8, sizeof(double), p, space);  // bumps p up to a multiple of 8
    return (aligned && is_aligned(aligned, 8) && !is_aligned(buf + 1, 8)) ? 0 : 1;   // returns 0
}
```

`std::align` *(C++11, `<memory>`)* moves a pointer forward to the next suitably aligned address
inside a buffer and shrinks the remaining space, or returns `nullptr` if it does not fit. It is the
building block of bump allocators. `std::assume_aligned<N>(p)` *(C++20)* goes the other way: it
promises the optimizer that `p` is aligned. If the promise is false, the behavior is undefined.

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `int* p = reinterpret_cast<int*>(bytes + 1); *p` | Misaligned access is UB (and also breaks [strict aliasing](./strict-aliasing.md)) | `std::memcpy` the bytes into an `int` |
| `char buf[sizeof(T)]` as storage for `T` | Alignment 1 | `alignas(T) std::byte buf[sizeof(T)]` |
| Pre-C++17 code or a custom allocator ignoring `alignof(T)` | Over-aligned types end up misaligned | Build as C++17 or later. Have allocators honor alignment. |
| Packed structs (`__attribute__((packed))`, `#pragma pack(1)`) used as normal data | Members are misaligned. Taking a member's address yields a pointer the compiler assumes is aligned. | Use packing only for wire formats, and copy fields out. See [Padding and offsetof](../12-low-level-and-platform/03-padding-and-offsetof.md). |
| `alignas(64)` on every hot member "for speed" | Inflates memory use and cache footprint | Align only data written by different threads. Measure. |

## Key points

- Alignment is a power of two per type. Objects must start at a multiple of it, or behavior is
  undefined, whatever the CPU tolerates.
- Padding is how the compiler meets alignment in classes. Order members from large to small to
  minimize it.
- `alignof` queries, `alignas` strengthens. It never weakens.
- Since C++17, `new` and `std::allocator` handle over-aligned types via `std::align_val_t`.
