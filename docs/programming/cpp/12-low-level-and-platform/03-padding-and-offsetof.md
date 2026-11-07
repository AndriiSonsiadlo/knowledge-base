---
id: padding-and-offsetof
title: Padding and offsetof
sidebar_label: Padding & offsetof
sidebar_position: 3
tags: [cpp, padding, offsetof, standard-layout, bit-fields, packed, serialization]
---

# Padding and `offsetof`

Padding is the bytes the compiler inserts so members stay aligned. Most code never sees it. You meet
it when a struct's bytes leave the program (a file, a socket, a hardware register block, a C library)
or when you compare or hash objects bytewise. This page covers the tools for looking at and pinning a
layout: `offsetof`, standard-layout, padding inspection, packing, bit-fields and trailing arrays.

**Prerequisites:** [Memory alignment](../05-memory-and-object-lifetime/alignment.md) explains why
padding exists and how to order members to shrink it. [Alignment and offsetof](../03-types-and-values/alignment-and-offsetof.md)
introduces `alignof`, `alignas` and the basic `offsetof` call; this page does not repeat them.
Where a class's bases, vptr and non-POD tail padding go is on [Object layout](./02-object-layout.md).

All output below is from g++ 15.2 and clang++ 21.1 at `-O0` and `-O2` on x86-64 Linux (Itanium ABI),
unless a line says otherwise.

## `offsetof` and what it is allowed on

`offsetof(Type, member)` from `<cstddef>` is a `std::size_t` constant expression: the distance in bytes
from the start of a `Type` object to `member`. It is meant for **standard-layout** types, the class
category whose layout the language pins down enough for C interop (the conditions are listed on
[Class layout](../07-classes-and-oop/class-layout.md#standard-layout-classes)).

| Argument | Behaviour |
|---|---|
| Standard-layout class | Defined |
| Other class (virtual functions, mixed access control, ...) | *Conditionally-supported* since C++17 (undefined before). g++ warns with `-Winvalid-offsetof`: "offsetof within non-standard-layout type is conditionally-supported" |
| Bit-field, static member, member function | Undefined (GCC and Clang reject it with an error) |

Pin the layouts you depend on with `static_assert(offsetof(...) == N && sizeof(T) == M)`, as shown on
[Alignment and offsetof](../03-types-and-values/alignment-and-offsetof.md#offsetof), and use fixed-width
members: `unsigned long` is 8 bytes on x86-64 Linux and 4 on Windows x64 (see [ABI](./01-abi.md)), which
changes every later offset.

### Getting from a member back to its owner

`offsetof` is how an intrusive container finds the object that embeds a link. The Linux kernel calls
the pattern `container_of`:

```cpp title="container-of.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>

struct Node { int key; Node* next; };
struct Item { int x; Node link; int y; };

int main() {
    Item it{1, {2, nullptr}, 3};
    Node* n = &it.link;
    Item* back = reinterpret_cast<Item*>(reinterpret_cast<char*>(n) - offsetof(Item, link));
    std::printf("%d\n", back->y);     // 3
}
```

It printed `3` on both compilers at both levels. Strictly by the language rules, pointer arithmetic from a
subobject's address to its enclosing object is not something the standard blesses, so treat it as a
widely used idiom that works on mainstream compilers rather than a guarantee. See
[Pointer arithmetic](../06-pointers-references-and-smart-pointers/pointer-arithmetic.md) for the rules it
bends.

## Looking at padding

Padding is invisible in source. Four ways to see it:

```cpp title="padded.cpp" showLineNumbers
struct Padded { char c; int i; char c2; };    // 1 + 3 hole + 4 + 1 + 3 tail = 12
```

- **`pahole`** (dwarves), on an object built with `-g`: `pahole -C Padded padded.o` printed

  ```text
  struct Padded {
          char                       c;                    /*     0     1 */

          /* XXX 3 bytes hole, try to pack */

          int                        i;                    /*     4     4 */
          char                       c2;                   /*     8     1 */

          /* size: 12, cachelines: 1, members: 3 */
          /* sum members: 6, holes: 1, sum holes: 3 */
          /* padding: 3 */
          /* last cacheline: 12 bytes */
  };
  ```
- **`-Wpadded`** (GCC and Clang) warns at each hole: `padding struct to align 'Padded::i'` and `padding
  struct size to alignment boundary with 3 bytes`. It is noisy; use it on a header you want to audit.
- **The layout dumps** from [Object layout](./02-object-layout.md#ask-the-compiler).
- **`std::has_unique_object_representations_v<T>`** *(C++17, `<type_traits>`)* is true only if every
  byte of a `T` takes part in its value, i.e. there is no padding and no member whose equal values
  can have different bytes. A struct of `std::uint32_t, std::uint16_t, std::uint16_t` satisfies it, `Padded` above does not.

### Why padding bytes matter

Padding bytes have unspecified values. Copying a struct (copy constructor, assignment, `memcpy`) does
not promise to copy them faithfully, and assigning members does not touch them. After `memset` to
`0xAA` and then assigning the three members of `Padded`, both compilers at both levels printed

```text
01 aa aa aa 02 00 00 00 03 aa aa aa
```

That output is what these compilers happened to do, not a guarantee. The consequences are real, though:

- **Do not `memcmp` or hash a struct that has padding.** Two equal objects can differ in padding.
  Compare member by member, or require `has_unique_object_representations`.
- **Do not send a padded struct over a network or write it to a file** if you can avoid it. Besides
  leaking indeterminate bytes (an information leak, if they came from uninitialised memory), the layout
  is ABI-dependent. Serialise field by field into a byte buffer instead ([Endianness](./04-endianness.md)
  shows how), and `static_assert` the layout where you do copy a struct as-is, such as memory-mapped
  register blocks or a file format you control on one platform.
- Padding is unspecified after a `memset`, as above. In an uninitialised object it is indeterminate, and there only copying the bytes is allowed; using the value (before C++26) is undefined behaviour.

## Packing

`#pragma pack` and `__attribute__((packed))` remove padding, at the cost of misaligned members. Both are
compiler extensions:

```cpp title="packed.cpp" showLineNumbers
struct __attribute__((packed)) Packed { char c; int i; };     // GCC, Clang

#pragma pack(push, 1)                                         // GCC, Clang, MSVC
struct Pragma1 { char c; int i; };
#pragma pack(pop)
```

Both are 5 bytes with `i` at offset 1 (printed with `sizeof`; the unpacked version is 8). Misaligned access
of `i` is undefined behaviour in standard C++; the compiler generates safe, usually slower, loads for member
access, but it cannot know about a pointer you take:

```text
warning: taking address of packed member 'i' of class or structure 'P' may result in an unaligned pointer value [-Waddress-of-packed-member]
```

Clang printed this form; GCC's text is similar. Never bind a reference or pointer to a packed member. Copy
the value out (`std::memcpy` into a local) instead. Packing is for matching an external wire or file
format, not for saving memory. The performance and alignment details are on
[Memory alignment](../05-memory-and-object-lifetime/alignment.md).

## Bit-fields

A bit-field declares a member of a given number of bits: `unsigned mode : 2;`. How they are packed into
**allocation units**, which direction bits are numbered, and whether a field may straddle a unit are
**implementation-defined**, and the ABIs differ:

```cpp title="bitfields.cpp (fragment)"
struct Mixed { char a : 4; int b : 4; };
```

| Target | `sizeof(Mixed)` |
|---|---|
| Itanium ABI (x86-64 Linux and AArch64 Linux, Clang layout dump) | 4 |
| MSVC layout (x86-64, Clang layout dump) | 8 |

The Itanium ABI packs `b` into the same storage as `a`. In the MSVC layout, a bit-field whose declared type
differs in size from the previous one starts a new unit. Same source, two sizes. The consequences:

- Never use bit-fields to describe a wire format or a hardware register layout that has to be portable.
  Extract fields with shifts and masks on a fixed-width integer instead.
- `offsetof` of a bit-field is undefined (compilers reject it), and you cannot take its address or bind a non-`const`
  reference.
- Adjacent bit-fields are one *memory location* for data-race purposes, so two threads writing
  different bit-fields of the same word race. See
  [Data races](../11-concurrency-and-memory-model/03-data-races.md).

## Trailing arrays

C99 allows a **flexible array member**, `uint32_t data[];`, as the last member of a struct, so one
allocation holds a header and a variable payload. **It is not C++.** Standard C++ has no such member;
GCC and Clang accept it as an extension (and `data[0]` or `data[1]` as older spellings), with
`-Wpedantic` warnings. If you need it for a C API:

```cpp title="flexible.cpp (needs a compiler extension)" showLineNumbers
#include <cstdint>
#include <cstdlib>
#include <new>

struct Message {
    std::uint32_t count;
    std::uint32_t data[];          // extension in C++: not valid ISO C++
};

Message* make(std::size_t n) {
    void* mem = std::malloc(sizeof(Message) + n * sizeof(std::uint32_t));
    if (!mem) return nullptr;
    auto* m = new (mem) Message{};   // start the object's lifetime
    m->count = static_cast<std::uint32_t>(n);
    return m;
}
```

Whether indexing `data[i]` beyond the declared (empty) bound is permitted is exactly the gap between
the extension and the standard. Prefer a pointer plus a count, or a `std::vector`, in new C++ code.

## Key points

- `offsetof` is defined for standard-layout types only (conditionally supported otherwise since C++17);
  pin the offsets you rely on with `static_assert`, and use fixed-width types.
- See padding with `pahole`, `-Wpadded`, the compiler's layout dump or
  `std::has_unique_object_representations`.
- Padding bytes are unspecified: do not `memcmp`, hash or ship such structs, and serialise field by field.
- Packed structs are misaligned by design; never take a pointer to their members.
- Bit-field packing is implementation-defined and differs between the Itanium and MSVC ABIs; flexible
  array members are a C feature, not C++.

## References

- [cppreference: `offsetof`](https://en.cppreference.com/w/cpp/types/offsetof)
- [cppreference: bit-field](https://en.cppreference.com/w/cpp/language/bit_field)
- [cppreference: `std::has_unique_object_representations`](https://en.cppreference.com/w/cpp/types/has_unique_object_representations)
- [GCC: Common type attributes (`packed`)](https://gcc.gnu.org/onlinedocs/gcc/Common-Type-Attributes.html)
