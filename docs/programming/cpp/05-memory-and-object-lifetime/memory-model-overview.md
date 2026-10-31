---
id: memory-model-and-allocation
title: Process Memory and Allocation
sidebar_label: Process Memory Overview
sidebar_position: 1
tags: [c++, memory, stack, heap, address-space, storage-duration]
---

# Process Memory and Allocation

A running C++ program keeps its code, its global variables, its function-local variables and its
dynamically allocated objects in different parts of its address space. Where an object lives decides
how long it lives, how fast it is to create, and who is responsible for destroying it. This page is
the map of that address space and the entry point for this section. The pages after it cover each
part in detail.

:::note[Not the concurrency memory model]
The standard also uses "memory model" for the rules on how threads see each other's writes
(happens-before, `std::memory_order`, data races). That topic is in
[C++ memory model](../11-concurrency-and-memory-model/01-cpp-memory-model.md). This page is about
*where objects are stored*, not about ordering between threads.
:::

**Prerequisites:** [Fundamental types](../03-types-and-values/fundamental-types.md) and
[raw pointers](../06-pointers-references-and-smart-pointers/raw-pointers.md).

## The address space of a process

The C++ standard does not define a stack, a heap or segments. It defines four
[storage durations](./storage-duration.md), and compilers and operating systems implement them with
the regions below. The diagram shows the usual layout of a Linux process on x86-64 (ELF executable).
Other platforms use the same regions with different addresses.

<Diagram title="Typical process address space (high addresses at the top)" caption="Each thread gets its own stack. Shared libraries and memory-mapped files sit in the gap between heap and stack." accent="blue">
  <DiagramNode icon="layers" title="Stack" accent>Automatic storage: locals, parameters, return addresses. Grows down. One per thread.</DiagramNode>
  <DiagramArrow label="free gap: mmap regions, shared libraries" dashed />
  <DiagramNode icon="boxes" title="Heap">Dynamic storage: `new`, `malloc`, container buffers. Grows up.</DiagramNode>
  <DiagramGroup label="Static storage (from the executable file)">
    <DiagramNode icon="binary" title=".bss">Zero-initialized statics. Takes no space in the file.</DiagramNode>
    <DiagramNode icon="file-text" title=".data">Statics with a non-zero initial value.</DiagramNode>
    <DiagramNode icon="lock" title=".rodata">String literals, constant tables. Read-only.</DiagramNode>
  </DiagramGroup>
  <DiagramNode icon="cpu" title=".text">Machine code. Read-only and executable, shared between processes running the same file.</DiagramNode>
</Diagram>

| Region | Holds | Storage duration | Created / released |
|---|---|---|---|
| `.text` | Compiled functions | — (code, not objects) | Mapped when the program loads |
| `.rodata` | String literals, `const` tables the compiler can place there | Static | Load time |
| `.data` | `int g = 42;`, `static int s = 7;` | Static | Load time, values copied from the file |
| `.bss` | `int g;`, `static int s = 0;` | Static | Load time, zero-filled by the loader |
| Heap | Objects from `new`, `malloc`, allocators | Dynamic | Your code allocates and frees |
| Stack | Local variables, parameters, spilled registers | Automatic | Function entry and exit |
| Thread-local block | `thread_local` variables | Thread | Thread start and exit |

The snippet shows one variable of each kind. Printing their addresses on Linux shows the order of the
diagram: the global and static addresses are low, the heap address is above them, and the stack
address is far higher.

```cpp title="regions.cpp" showLineNumbers
#include <cstdio>
#include <memory>

int initialized = 42;          // .data
int zeroed;                    // .bss
const char* text = "hello";    // pointer in .data, the characters in .rodata

int main() {
    static int counter = 0;                 // .bss: static storage, zero initial value
    int local = 1;                          // stack
    auto heap = std::make_unique<int>(2);   // the int is on the heap, `heap` itself on the stack
    std::printf("data  %p\nbss   %p\nheap  %p\nstack %p\n",
                static_cast<void*>(&initialized), static_cast<void*>(&zeroed),
                static_cast<void*>(heap.get()), static_cast<void*>(&local));
    return counter + *heap - local - 1 + zeroed;  // keep everything used; returns 0
}
```

The exact addresses change on every run because of address-space layout randomization (ASLR). The
relative order is what stays the same.

## Stack and heap

Most day-to-day decisions are between the stack (automatic storage) and the heap (dynamic storage).

| | Stack | Heap |
|---|---|---|
| Allocation | Adjusting the stack pointer, done once per function call for all locals | A call into the allocator (`operator new`, `malloc`), which searches its free lists |
| Release | Automatic at scope exit, in reverse order of construction | Explicit (`delete`) or by an owning object such as `std::unique_ptr` or `std::vector` |
| Size limit | Small and fixed per thread: on Linux the main thread's limit is `ulimit -s`, 8 MiB by default; MSVC links a 1 MiB default stack | Limited by available virtual memory |
| Size known | At compile time (VLAs are not standard C++) | At run time |
| Failure mode | Stack overflow: the process crashes, usually with `SIGSEGV` | `std::bad_alloc` is thrown (or `nullptr` with `std::nothrow`) |
| Typical bugs | Returning a pointer or reference to a local | Leaks, double `delete`, use after free |

Heap allocation is slower than stack allocation because the allocator has to find a free block, may
take a lock, and may ask the operating system for more pages. How much slower depends on the
allocator, the size, and the access pattern, so measure your own case rather than trusting a fixed
ratio.

Default to the stack. Use the heap when:

- the size is only known at run time, or is too large for the stack (`std::vector`, `std::string`);
- the object has to outlive the scope that created it (return a `std::unique_ptr`);
- the object's dynamic type is chosen at run time (`std::unique_ptr<Base>` holding a `Derived`).

In all three cases, let an owning type manage the heap memory. Plain `new` and `delete` are covered
in [new and delete](./new-and-delete.md) so you know what those types do for you.

```cpp title="choose.cpp" showLineNumbers
#include <array>
#include <memory>
#include <vector>

struct Shape { virtual ~Shape() = default; virtual double area() const = 0; };
struct Square : Shape { double s = 2; double area() const override { return s * s; } };

std::unique_ptr<Shape> make_shape() { return std::make_unique<Square>(); }  // outlives the call

int main() {
    std::array<int, 16> small{};             // fixed size: stack
    std::vector<int> big(1'000'000);         // 4 MB of ints: heap, owned by the vector
    auto shape = make_shape();               // runtime type: heap, owned by unique_ptr
    return static_cast<int>(shape->area()) - 4 + small[0] + big[0];   // returns 0
}
```

## What else lives in this section

<Diagram title="From storage to a usable object" accent="green">
  <DiagramRow>
    <DiagramNode title="Storage duration">Which region, and for how long</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Initialization">What value the object starts with</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Object lifetime" accent>When the object exists and may be used</DiagramNode>
  </DiagramRow>
</Diagram>

- [Storage duration](./storage-duration.md): the four durations, static initialization order,
  `thread_local`.
- [Initialization](./initialization/default-initialization.md): default, value, aggregate and list
  initialization, and when a variable is left indeterminate.
- [Object lifetime](./object-lifetime.md): when lifetime starts and ends, temporaries, implicit
  object creation.
- [new and delete](./new-and-delete.md) and [placement new](./placement-new.md): separating
  allocation from construction.
- [Alignment](./alignment.md) and [strict aliasing](./strict-aliasing.md): the rules that decide
  which addresses an object may live at and which types may access it.

Common lifetime bugs, how undefined behavior lets the compiler exploit them, and the tools that catch
them are covered in [Undefined behavior](../10-error-handling-and-safety/06-undefined-behavior.md)
and [Sanitizers](../14-debugging-and-profiling/04-sanitizers.md).

## Key points

- The standard speaks of storage durations. Stack, heap and segments are how implementations provide
  them.
- Globals and statics are in `.data` or `.bss` and exist for the whole run. `.bss` costs no file
  space because the loader zero-fills it.
- The stack is fast and small. A large local array can overflow it without any warning at compile
  time.
- Heap memory should always have an owner object. Write `new` only inside such owners.
