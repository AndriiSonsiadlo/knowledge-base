---
id: padding-and-offsetof
title: Padding and offsetof
sidebar_label: Padding & offsetof
sidebar_position: 3
tags: [cpp, padding, offsetof, alignment, memory-layout]
---

# Padding and `offsetof`

This page is the **low-level / ABI** view: how padding affects a struct's on-the-wire byte layout,
and how `offsetof` lets you address members by raw byte offset for serialization and memory-mapped
I/O.

:::info Prerequisite
The fundamentals — what alignment is, why padding exists, how to order members to shrink a struct —
live on the canonical [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) page. The
language-level `alignof`/`alignas`/`offsetof` reference is in
[Alignment and offsetof](../03-types-and-values/alignment-and-offsetof.md). This page assumes both.
:::

## Why layout matters at the ABI level

When you `write()` a struct to a socket or `mmap` a file onto one, you are betting that *your* byte
layout matches the *other side's*. Padding is part of that layout — and it is not guaranteed across
compilers or architectures. Two rules keep you safe:

1. Verify the layout you depend on with `static_assert`.
2. Only treat **standard-layout** types as raw bytes.

```cpp showLineNumbers
struct NetworkPacket {
    uint32_t magic;      // offset 0
    uint16_t version;    // offset 4
    uint16_t flags;      // offset 6
    uint32_t length;     // offset 8
    uint8_t  data[1024]; // offset 12
};

static_assert(std::is_standard_layout_v<NetworkPacket>);
static_assert(offsetof(NetworkPacket, data) == 12);   // pin the layout you rely on

void send(int sock, const NetworkPacket& p) {
    write(sock, &p, sizeof p);   // safe only because the asserts above hold
}
```

## `offsetof` for byte-level access

`offsetof(Type, member)` yields the member's byte offset, letting you reach a field through a raw
pointer — the basis of serialization and protocol parsing.

```cpp showLineNumbers
#include <cstddef>

char*    base     = reinterpret_cast<char*>(&packet);
uint8_t* data_ptr = reinterpret_cast<uint8_t*>(base + offsetof(NetworkPacket, data));
```

:::warning Standard-layout only
`offsetof` on a type with virtual functions, multiple/virtual inheritance, or mixed-access members
is **undefined behaviour** — such types have no flat, portable offset table. See
[Object Layout](./02-object-layout.md) for what the vtable pointer does to a class.
:::

## Bit-fields — sub-byte packing

Bit-fields pack several values into the bits of one integer. Useful for hardware registers and dense
flags, but the **bit order and straddling rules are implementation-defined** — never rely on the
layout across compilers, and don't `offsetof` a bit-field (it's ill-formed).

```cpp showLineNumbers
struct Flags {
    unsigned ready : 1;
    unsigned mode  : 2;
    unsigned count : 5;
    // packed into one byte, then padded to the type's width
};
sizeof(Flags);   // 4 — implementation-defined
```

## Flexible array members

A trailing array of unspecified size lets one allocation hold a header plus a variable-length
payload — a common serialization trick. `[]` is the C99 flexible array member (well supported as an
extension); `[0]` is the older GCC spelling.

```cpp showLineNumbers
struct Message {
    uint32_t count;
    uint32_t data[];   // occupies no space in sizeof(Message)
};

size_t n = 10;
auto* m = static_cast<Message*>(std::malloc(sizeof(Message) + n * sizeof(uint32_t)));
m->count = n;
m->data[5] = 42;       // lives in the extra bytes allocated above
```

## Inheritance does not reuse base padding

A derived class's members are placed *after* the base subobject's trailing padding, not inside it —
so deriving can grow a type more than you'd expect. (The exception is the *empty base optimization*,
covered in [Object Layout](./02-object-layout.md).)

```cpp showLineNumbers
struct Base    { char c; /* 3 padding */ int i; };   // sizeof 8
struct Derived : Base { char c2; /* 3 padding */ };  // sizeof 12, not 9
```

## Summary

- A struct's byte layout — padding included — is what crosses the wire; pin it with `static_assert`.
- Treat only **standard-layout** types as raw bytes; `offsetof` is UB otherwise.
- Bit-fields pack sub-byte data but are implementation-defined — not portable across compilers.
- Flexible array members carry a variable payload in a single allocation.
- Inheritance appends after base padding; it isn't reused (barring the empty base optimization).

## Related

- [Memory Alignment](../05-memory-and-object-lifetime/alignment.md) — alignment & padding fundamentals
- [Alignment and offsetof](../03-types-and-values/alignment-and-offsetof.md) — `alignof`/`alignas`/`offsetof` reference
- [Object Layout](./02-object-layout.md) · [ABI](./01-abi.md) · [Endianness](./04-endianness.md)
