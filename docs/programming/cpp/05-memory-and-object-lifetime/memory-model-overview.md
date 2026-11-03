---
id: memory-model-and-allocation
title: The C++ Memory Model of Objects and Storage
sidebar_label: Memory Model Overview
sidebar_position: 1
tags: [c++, memory, object, storage, lifetime, alignment, aliasing, abstract-machine]
---

# The C++ Memory Model of Objects and Storage

C++ describes memory for an **abstract machine**, not for a particular CPU or operating system. In
that description a program manipulates **objects** that live in **storage** made of **bytes**. Four
properties of an object decide whether code using it is valid: how long its storage exists, when the
object itself exists in that storage, which addresses it may occupy, and through which types it may
be accessed. This page defines the vocabulary and shows how the rest of the section fits together.

:::note[Not the concurrency memory model]
The standard also uses "memory model" for how threads observe each other's writes. That topic is in
[C++ memory model](../11-concurrency-and-memory-model/01-cpp-memory-model.md).
:::

**Prerequisites:** [Fundamental types](../03-types-and-values/fundamental-types.md) and
[raw pointers](../06-pointers-references-and-smart-pointers/raw-pointers.md).

## Bytes, objects and memory locations

- A **byte** is the smallest addressable unit of storage. It has `CHAR_BIT` bits (at least 8) and is
  what `sizeof` counts. `char`, `unsigned char` and `std::byte` *(C++17)* are the types for
  inspecting bytes.
- An **object** is a region of storage with a type, a lifetime and (usually) a value. This is wider
  than "instance of a class": an `int` variable, an array element and a class subobject are all
  objects.
- An object's **object representation** is the sequence of `sizeof(T)` bytes it occupies. Its
  **value representation** is the subset of those bits that determine the value. The rest is padding.
- A **memory location** is the storage of an object of scalar type, or of a maximal run of adjacent
  bit-fields. It is the unit the standard uses for "do two accesses conflict". Distinct memory
  locations can be modified independently, even by different threads.

```cpp title="model.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <new>

struct Flags { int a : 3; int b : 5; };   // a and b share one memory location
struct Pair  { char x; char y; };          // x and y are separate memory locations

int main() {
    alignas(int) unsigned char storage[sizeof(int)];   // bytes: storage, but no int object yet
    int* p = new (storage) int(0x01020304);            // an int object is created in them
    unsigned char bytes[sizeof(int)];
    std::memcpy(bytes, p, sizeof bytes);               // read its object representation
    std::printf("sizeof(int)=%zu first byte=0x%02x\n", sizeof(int), bytes[0]);
    static_assert(sizeof(Pair) == 2 && sizeof(Flags) >= 1);
    return 0;
}
```

Compiled with `g++ -std=c++20 -Wall -Wextra` on x86-64 Linux it prints:

```text
sizeof(int)=4 first byte=0x04
```

The first byte is `0x04` because x86-64 is little-endian. Byte order is implementation-defined.

The snippet also shows the central distinction of this section: `storage` is storage, and no `int`
exists in it until the placement `new` creates one. Storage and objects are separate things.

## Four properties of an object

<Diagram title="What decides whether an access is valid" accent="blue">
  <DiagramRow>
    <DiagramNode title="Storage duration">How long the bytes are reserved</DiagramNode>
    <DiagramNode title="Lifetime" accent>When an object exists in those bytes</DiagramNode>
    <DiagramNode title="Alignment">Which addresses the object may start at</DiagramNode>
    <DiagramNode title="Aliasing">Which types may read or write it</DiagramNode>
  </DiagramRow>
</Diagram>

| Property | Question it answers | Typical bug when ignored | Canonical page |
|---|---|---|---|
| Storage duration | Which of automatic, static, thread or dynamic storage, and so when are the bytes released? | Pointer to a local that has returned | [Storage duration](./storage-duration.md) |
| Lifetime | Does an object exist in the bytes right now? | Using an object before construction or after destruction | [Object lifetime](./object-lifetime.md) |
| Alignment | Is the address a multiple of the type's alignment? | Misaligned access through a cast byte buffer | [Alignment](./alignment.md) |
| Aliasing | Is this access through a type the standard allows for the object? | Reading a `float` through an `int*` | [Strict aliasing](./strict-aliasing.md) |

Storage outlives or equals an object's lifetime, never the reverse: an object cannot exist without
storage, but storage can exist with no object, as before construction or after destruction. A
[new-expression](./new-and-delete.md) allocates storage and constructs an object in it, and a
delete-expression destroys the object and deallocates the storage. The two steps can be separated:
`operator new` only allocates, and [placement new](./placement-new.md) only constructs an object in
storage you already have.

Breaking any of the four rules is undefined behavior. The compiler is allowed to assume it never
happens, so the symptom can appear far from the cause. See
[Undefined behavior](../10-error-handling-and-safety/06-undefined-behavior.md) and
[Sanitizers](../14-debugging-and-profiling/04-sanitizers.md) for the tools that catch these bugs.

## Where the abstract machine meets real memory

The standard defines storage durations and does not mention a stack, a heap or segments. Typical
implementations map automatic storage to the call stack, dynamic storage to an allocator on top of
the operating system, and static storage to sections of the executable. The mapping is covered in
[Storage duration](./storage-duration.md).

For choosing between them: prefer automatic storage, and use dynamic storage when the size is known
only at run time, the object must outlive its scope, or its dynamic type is chosen at run time. In
those cases let an owning type such as `std::unique_ptr` or `std::vector` manage the memory.

## Reading order

Pages build on one another, so follow the sidebar order.

1. [Storage duration](./storage-duration.md): the four durations, static initialization order,
   `thread_local`.
2. Initialization: what value an object starts with.
   [Default](./initialization/default-initialization.md),
   [value](./initialization/value-initialization.md),
   [aggregate](./initialization/aggregate-initialization.md) and
   [list (uniform)](./initialization/uniform-initialization.md) initialization.
3. [Object lifetime](./object-lifetime.md): when lifetime begins and ends, temporaries, dangling
   references, implicit object creation.
4. [new and delete](./new-and-delete.md): allocation functions versus new and delete expressions.
5. [Placement new and std::launder](./placement-new.md): constructing objects in existing storage.
6. [Alignment](./alignment.md): `alignof`, `alignas`, padding, over-aligned allocation.
7. [Strict aliasing](./strict-aliasing.md): which types may access an object, and type punning with
   `memcpy` and `std::bit_cast`.

## Key points

- The standard describes objects in bytes of storage on an abstract machine. Stack and heap are how
  implementations provide storage durations.
- Storage and objects are distinct: bytes can exist with no object in them.
- Validity of an access depends on storage duration, lifetime, alignment and aliasing. Each has one
  canonical page in this section.
- A memory location is a scalar object or a run of adjacent bit-fields. It is the unit that matters
  for conflicting accesses.
- Thread visibility rules are a separate topic in the concurrency section.
