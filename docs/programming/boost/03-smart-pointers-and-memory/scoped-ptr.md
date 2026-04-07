---
id: scoped-ptr
title: boost::scoped_ptr and scoped_array
sidebar_label: scoped_ptr
sidebar_position: 4
tags: [ c++, boost, smart-pointers, memory ]
---

# boost::scoped_ptr and scoped_array

`boost::scoped_ptr<T>` is the simplest smart pointer: it owns a single heap object and deletes it when
the `scoped_ptr` goes out of scope. It is **non-copyable and non-movable** — ownership stays put for
the pointer's entire lifetime. That deliberate restriction makes intent crystal clear: "this object
lives exactly as long as this scope, and nobody else can take it."

:::info Zero overhead
`scoped_ptr` stores nothing but the raw pointer. There is no reference count and no control block, so
it is exactly as cheap as a hand-written `new`/`delete` pair — just exception-safe.
:::

## Usage

```cpp showLineNumbers title="scoped_basics.cpp"
#include <boost/scoped_ptr.hpp>
#include <iostream>

struct Widget { void draw() const { std::cout << "draw\n"; } };

void render() {
    boost::scoped_ptr<Widget> w(new Widget);
    w->draw();
    if (!w) return;          // explicit-bool test
}                            // deleted automatically here
```

Because it cannot be copied or returned by value, `scoped_ptr` is for **local, owned-here** objects —
a member that the class fully owns, or a temporary that must survive a function body. To transfer
ownership out of a function, you need a movable type instead.

## scoped_array

`boost::scoped_array<T>` is the same idea for arrays allocated with `new[]`, calling `delete[]` on
destruction and offering `operator[]`:

```cpp showLineNumbers
#include <boost/scoped_array.hpp>

boost::scoped_array<int> buf(new int[256]);
buf[0] = 42;
```

## Relationship to unique_ptr

`scoped_ptr` predates `std::unique_ptr`. They share the "single owner, automatic delete" core, but
`unique_ptr` adds **move semantics** (so ownership can be transferred and returned) and custom
deleters, while remaining just as cheap.

| Feature | `boost::scoped_ptr` | `std::unique_ptr` |
|---------|---------------------|-------------------|
| Single ownership | Yes | Yes |
| Movable / transferable | No | Yes |
| Custom deleter | No | Yes |
| Array form | `scoped_array` | `unique_ptr<T[]>` |
| Overhead | None | None |

:::tip Prefer std::unique_ptr in new code
`unique_ptr` is a strict superset of what `scoped_ptr` offers and is the modern default. Keep
`scoped_ptr` in mind only for pre-C++11 code or where you specifically want to *forbid* moving as
documentation of intent. See [Boost and the standard](../00-overview/boost-and-the-standard.md).
:::

## See also

- [Smart Pointers Overview](./smart-ptr-overview.md) — choosing among the family.
- [boost::shared_ptr and weak_ptr](./shared-ptr.md) — when ownership must be shared.
