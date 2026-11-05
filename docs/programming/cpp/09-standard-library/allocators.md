---
id: allocators
title: Allocators
sidebar_label: Allocators
sidebar_position: 10
tags: [c++, allocators, allocator-traits, pmr, polymorphic-allocator, memory-resource, monotonic-buffer-resource, arena]
---

# Allocators

Every standard container obtains its memory through an **allocator**, an object that answers
"give me storage for `n` objects of type `T`" and "take this storage back". The default allocator
calls `operator new`. Replacing it lets you put a container's memory in an arena, a fixed buffer,
a pool, or shared memory, count or trace allocations, or align them, without changing the container's
code. This page is the canonical home for the allocator model, `std::allocator_traits`, propagation
rules, and the C++17 `std::pmr` facilities. How `operator new` itself works is on
[new and delete](../05-memory-and-object-lifetime/new-and-delete.md).

**Prerequisites:** [Containers](./containers.md), [placement new](../05-memory-and-object-lifetime/placement-new.md),
[alignment](../05-memory-and-object-lifetime/alignment.md), [class templates](../08-templates-and-metaprogramming/class-templates.md).

## What an allocator does, and does not

An allocator separates two jobs that `new` combines: **allocating raw storage** and **constructing
objects** in it. A container asks for storage with `allocate(n)`, constructs elements in it (through
`std::allocator_traits<A>::construct`, which defaults to placement new), and on removal destroys the
element and calls `deallocate(p, n)`.

<Diagram title="Container, allocator and storage" accent="blue">
  <DiagramRow>
    <DiagramNode title="container" accent>vector, list, map, ...</DiagramNode>
    <DiagramArrow direction="right" label="allocate(n) / deallocate(p, n)" />
    <DiagramNode title="allocator">strategy + state</DiagramNode>
    <DiagramArrow direction="right" label="operator new or custom" />
    <DiagramNode title="storage">raw bytes, suitably aligned</DiagramNode>
  </DiagramRow>
</Diagram>

`allocate` returns storage aligned for `T` but with **no object in it**, which is why elements are
created with placement new and ended with an explicit destructor call (see
[object lifetime](../05-memory-and-object-lifetime/object-lifetime.md)).

## The minimal allocator

Since C++11 an allocator needs far less than the old interface. Everything else is supplied by
`std::allocator_traits`. A conforming minimum:

```cpp title="min-allocator.cpp" showLineNumbers
#include <cstddef>
#include <iostream>
#include <new>
#include <vector>

template <class T>
struct CountingAlloc {
    using value_type = T;

    CountingAlloc() = default;
    template <class U> CountingAlloc(const CountingAlloc<U>&) noexcept {}   // rebind support

    T* allocate(std::size_t n) {
        std::cout << "allocate " << n << " x " << sizeof(T) << " bytes\n";
        return static_cast<T*>(::operator new(n * sizeof(T), std::align_val_t{alignof(T)}));
    }
    void deallocate(T* p, std::size_t n) noexcept {
        std::cout << "deallocate " << n << '\n';
        ::operator delete(p, std::align_val_t{alignof(T)});
    }
};

template <class T, class U>
bool operator==(const CountingAlloc<T>&, const CountingAlloc<U>&) noexcept { return true; }

int main() {
    std::vector<int, CountingAlloc<int>> v;
    v.reserve(4);
    for (int i = 0; i < 4; ++i) v.push_back(i);
    v.push_back(4);                                  // exceeds capacity: allocate, move, free old
}
```

```text
allocate 4 x 4 bytes
allocate 8 x 4 bytes
deallocate 4
deallocate 8
```

The requirements, in words:

1. `value_type`, `allocate(n)` returning `T*`, and `deallocate(p, n)` (`n` must be the value passed to `allocate`).
2. A **converting constructor** from `Alloc<U>`: containers like `list` and `map` allocate *nodes*, not `T`, so
   they rebind your allocator to another type (`allocator_traits<A>::rebind_alloc<Node>`).
3. `operator==`: two allocators compare equal if storage allocated by one can be deallocated by the other.
   Stateless allocators are always equal.

The 8-element growth here (4 to 8) is libstdc++'s doubling; the standard only requires amortized-constant
`push_back`, so the numbers vary by library. C++23 added `allocate_at_least(n)`, which may return more
space than asked and tells you how much.

Old interfaces (`pointer`, `construct`, `destroy`, `max_size`, `rebind`, `address`) are optional or
removed: `std::allocator::construct`/`destroy` were deprecated in C++17 and removed in C++20, and
`std::allocator<void>` members likewise. Call them through `allocator_traits`, not directly.

## `std::allocator_traits`

`allocator_traits<A>` is the one place containers talk to allocators. It fills in defaults for anything
the allocator omits: `pointer` (defaults to `T*`; fancy pointers are allowed), `construct` (placement
new), `destroy`, `max_size`, `select_on_container_copy_construction`, and the propagation flags below. Write
your container code against it if you build an allocator-aware container.

### Propagation: what happens when containers are copied, moved and swapped

An allocator with state raises questions: when you assign one container to another, which allocator does
the target keep? Three traits answer (each defaults to `false_type`, except `is_always_equal`, which
defaults to `is_empty<A>`):

| Trait | When `true` |
|---|---|
| `propagate_on_container_copy_assignment` (POCCA) | copy assignment also copies the allocator |
| `propagate_on_container_move_assignment` (POCMA) | move assignment also moves the allocator |
| `propagate_on_container_swap` (POCS) | `swap` also swaps the allocators |
| `is_always_equal` | all instances compare equal (stateless), so storage can be stolen freely |

Consequences worth knowing: moving a `vector` steals its buffer only if the allocators are equal
(or POCMA is true); with unequal non-propagating allocators the elements are moved one by one into
storage from the destination's allocator. `swap` of containers with unequal allocators that don't
propagate is **undefined behavior**. A copy-constructed container uses
`select_on_container_copy_construction(alloc)`, which by default copies the allocator. The default
`std::allocator` is stateless and always equal, so none of this appears until you add state.

## Polymorphic allocators: `std::pmr` *(C++17)*

The classic design encodes the allocator in the container's **type**: `vector<int, ArenaAlloc<int>>`
and `vector<int>` are unrelated types, so APIs and templates must carry the allocator everywhere.
`<memory_resource>` solves this with runtime polymorphism. A `std::pmr::memory_resource` is an
abstract base class with `allocate(bytes, alignment)`, `deallocate`, and `is_equal`; a single
allocator type, `std::pmr::polymorphic_allocator<T>`, holds a *pointer* to a resource. The aliases in
`std::pmr` (`pmr::vector<T>`, `pmr::string`, `pmr::map`, ...) are the usual containers with that
allocator, so all of them share one type regardless of the resource behind them.

<Diagram title="pmr: one container type, many memory resources" accent="green">
  <DiagramRow>
    <DiagramNode title="pmr::vector&lt;int&gt;" accent>holds a polymorphic_allocator</DiagramNode>
    <DiagramArrow direction="right" label="pointer to" />
    <DiagramGroup label="memory_resource (chosen at run time)">
      <DiagramNode title="new_delete_resource">default: operator new</DiagramNode>
      <DiagramNode title="monotonic_buffer_resource">bump-pointer arena</DiagramNode>
      <DiagramNode title="unsynchronized_pool_resource">size-class pools</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

The standard resources:

| Resource | Behavior |
|---|---|
| `new_delete_resource()` | `operator new`/`delete`; the default resource |
| `null_memory_resource()` | always throws `std::bad_alloc`; use to forbid allocation |
| `monotonic_buffer_resource` | takes a buffer you provide, then bumps a pointer; **`deallocate` does nothing**, everything is freed at once when the resource is destroyed or `release()`d; when the buffer is exhausted it asks its **upstream** resource for more |
| `unsynchronized_pool_resource` | pools per size class; not thread-safe |
| `synchronized_pool_resource` | same, thread-safe |

`set_default_resource` changes what `pmr` containers use when you pass no resource (it returns the
previous one); it is global state, so avoid it in libraries.

```cpp title="pmr-arena.cpp" showLineNumbers
#include <array>
#include <cstddef>
#include <iostream>
#include <memory_resource>
#include <string>
#include <vector>

int main() {
    alignas(std::max_align_t) std::array<std::byte, 1024> buf;
    std::pmr::monotonic_buffer_resource arena(buf.data(), buf.size(),
                                              std::pmr::null_memory_resource());   // no fallback

    std::pmr::vector<std::pmr::string> names(&arena);       // container and elements share the arena
    names.reserve(3);
    names.emplace_back("a string that is long enough to need heap storage, not just SSO");
    names.emplace_back("another quite long string, also past the small-string buffer size");

    const std::byte* b = buf.data();
    const auto* s = reinterpret_cast<const std::byte*>(names[0].data());
    std::cout << (s >= b && s < b + buf.size()) << '\n';    // the characters live in buf
    std::cout << names.size() << '\n';
}                                                           // arena dies: one free for everything
```

```text
1
2
```

Two points make this work. `null_memory_resource` as the upstream turns running out of buffer into a
`std::bad_alloc` instead of a silent heap allocation. And the `pmr::string` elements use the
**same resource** as the vector because of **uses-allocator construction**: an allocator-aware element
type gets the container's allocator passed to its constructor when it is constructed through the
allocator. `std::pmr::polymorphic_allocator::construct` does this automatically, which is why
`emplace_back("...")` gave the string the arena. A user type opts in by providing an
`allocator_type` typedef and constructors that take an allocator (`std::uses_allocator<T, Alloc>`).

Costs and caveats: a `pmr` container is one pointer bigger, each allocation goes through a virtual call, and
a **monotonic resource never reuses freed memory**, so a long-lived container that grows and
shrinks inside one will use more and more memory. The resource must outlive every container using it,
and `pmr` containers do not copy the resource on copy assignment (the destination keeps its own,
since `polymorphic_allocator` does not propagate on assignment), which you should expect when copying
between containers on different arenas. Whether pmr is faster than the default depends on the
allocation pattern, so measure.

## When to write an allocator

Reach for one when allocation is measurably a cost or a constraint:

- **Arena/bump** (`monotonic_buffer_resource`): many small allocations with a shared lifetime, such as
  one request, one frame, or one parse. Free everything at once.
- **Pool**: many same-size objects with individual lifetimes (`unsynchronized_pool_resource`), which
  avoids fragmentation and per-allocation headers.
- **Fixed storage**: no heap at all (embedded), with a stack or static buffer plus `null_memory_resource`.
- **Instrumentation**: a counting or tracing resource wrapping `new_delete_resource()` in tests.
- **Special memory**: shared memory, huge pages, aligned or device-visible memory.

Do not write one to "make it faster" unprofiled. A general-purpose allocator (`malloc`) is
already well tuned, and a replacement `operator new` is the simpler tool if you want to change all
allocations (see [new and delete](../05-memory-and-object-lifetime/new-and-delete.md)).

## Related

- [New and delete](../05-memory-and-object-lifetime/new-and-delete.md): `operator new`, the default allocator's backend
- [Placement new](../05-memory-and-object-lifetime/placement-new.md): how allocators construct in raw storage
- [Containers](./containers.md): the allocator template parameter and what `swap` and move do
- [Strings](./strings.md): `std::pmr::string`, and small string optimization
- [Custom deleters](../06-pointers-references-and-smart-pointers/custom-deleters.md): the same idea for smart pointers

## References

- [Allocator requirements, cppreference](https://en.cppreference.com/w/cpp/named_req/Allocator)
- [`<memory_resource>`, cppreference](https://en.cppreference.com/w/cpp/header/memory_resource)
- ISO C++ [allocator.requirements], [mem.res]
