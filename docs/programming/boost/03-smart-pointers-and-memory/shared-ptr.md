---
id: shared-ptr
title: boost::shared_ptr and weak_ptr
sidebar_label: shared_ptr & weak_ptr
sidebar_position: 2
tags: [ c++, boost, smart-pointers, memory ]
---

# boost::shared_ptr and weak_ptr

`boost::shared_ptr<T>` is a reference-counted smart pointer: any number of `shared_ptr` instances can
own the same object, and the object is destroyed exactly when the last owner goes away. It is the
direct ancestor of `std::shared_ptr` — the standard version is essentially this design after a decade
of field testing.

:::info Two allocations vs one
A naive `shared_ptr<T>(new T)` allocates twice: once for the object, once for the **control block**
that holds the reference counts. `boost::make_shared<T>(args...)` fuses both into a single allocation
— faster, more cache-friendly, and it can't leak if the constructor throws.
:::

## Shared ownership

```cpp showLineNumbers title="shared_basics.cpp"
#include <boost/shared_ptr.hpp>
#include <boost/make_shared.hpp>
#include <iostream>

struct Texture { Texture() { std::cout << "load\n"; } ~Texture() { std::cout << "free\n"; } };

int main() {
    boost::shared_ptr<Texture> a = boost::make_shared<Texture>();
    {
        boost::shared_ptr<Texture> b = a;   // use_count() == 2
        std::cout << "owners: " << a.use_count() << "\n";
    }                                        // b gone, use_count() == 1
    std::cout << "owners: " << a.use_count() << "\n";
}                                            // last owner gone -> "free"
```

The control block tracks two counts: a **strong** count (`shared_ptr` owners) and a **weak** count
([`weak_ptr`](#weak_ptr-breaking-cycles) observers). The object is destroyed at strong-count zero; the
control block itself survives until the weak count also hits zero.

## Custom deleters

A `shared_ptr` can own anything, not just heap objects, by supplying a deleter callable. This is how
you wrap C handles in RAII:

```cpp showLineNumbers
#include <cstdio>
#include <boost/shared_ptr.hpp>

boost::shared_ptr<FILE> open_log() {
    return boost::shared_ptr<FILE>(std::fopen("app.log", "a"), &std::fclose);
}
```

## weak_ptr: breaking cycles

Two objects that hold `shared_ptr`s to each other form a cycle whose counts never reach zero — a leak.
`weak_ptr` observes an object without contributing to its strong count; you `lock()` it to obtain a
temporary `shared_ptr` only when you actually need access.

```cpp showLineNumbers title="weak_cycle.cpp"
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>

struct Node {
    boost::shared_ptr<Node> next;   // owns forward
    boost::weak_ptr<Node>   prev;   // observes back -> no cycle
};

void use(const boost::weak_ptr<Node>& w) {
    if (boost::shared_ptr<Node> n = w.lock()) {
        // safe: n keeps the object alive for this scope
    }
}
```

:::danger Cycles of strong pointers leak silently
If a parent owns its children with `shared_ptr` and each child owns its parent with `shared_ptr`,
nothing is ever freed and no error is reported. Make exactly one direction `weak_ptr`.
:::

## enable_shared_from_this

When an object needs to hand out a `shared_ptr` to itself, deriving from `enable_shared_from_this`
lets it call `shared_from_this()` instead of dangerously wrapping `this` in a fresh `shared_ptr`
(which would create a second, independent control block).

```cpp showLineNumbers
#include <boost/enable_shared_from_this.hpp>
#include <boost/shared_ptr.hpp>

struct Session : boost::enable_shared_from_this<Session> {
    boost::shared_ptr<Session> self() { return shared_from_this(); }
};
```

## The aliasing constructor

A subtle but powerful feature: a `shared_ptr` can *own* one object while *pointing* at a sub-object of
it. The owned object keeps the whole thing alive; the stored pointer gives access to a member.

```cpp showLineNumbers
struct Frame { int header; int payload; };
boost::shared_ptr<Frame> f = boost::make_shared<Frame>();
boost::shared_ptr<int> p(f, &f->payload);   // shares ownership with f, points at payload
```

## Thread-safety

The reference counting is **atomic**: copying, destroying, and assigning `shared_ptr`s from multiple
threads is safe. What is *not* automatically safe is concurrent access to the **pointed-to object**,
or mutating the *same* `shared_ptr` instance from two threads. See
[Boost.Atomic](../09-concurrency-and-async/boost-atomic.md) for the primitives underneath.

| Operation | Thread-safe? |
|-----------|--------------|
| Copy/destroy *different* `shared_ptr` to same object | Yes (atomic counts) |
| Mutate the *same* `shared_ptr` from two threads | No (needs external sync) |
| Access the managed object from two threads | Depends on the object |

:::tip Prefer std::shared_ptr in new code
`std::shared_ptr` (C++11) has the same semantics and integrates with `std::weak_ptr`,
`std::make_shared`, and allocators. Use `boost::shared_ptr` for pre-C++11 code or interop with Boost
APIs (such as older [Asio](../09-concurrency-and-async/boost-asio.md) signatures).
:::

## See also

- [Smart Pointers Overview](./smart-ptr-overview.md) — choosing among the family.
- [boost::intrusive_ptr](./intrusive-ptr.md) — when a separate control block is too expensive.
- [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md).
