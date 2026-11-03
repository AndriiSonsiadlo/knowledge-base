---
id: shared-ptr
title: std::shared_ptr
sidebar_label: shared_ptr
sidebar_position: 6
tags: [c++, smart-pointers, shared-ptr, control-block, make-shared, reference-counting, cpp11]
---

# std::shared_ptr

`std::shared_ptr<T>` *(C++11, `<memory>`)* is a smart pointer for **shared ownership**: any number
of `shared_ptr`s can own the same object, and it is destroyed when the last owner goes away. That
is the right tool when no single owner has a clearly longer lifetime than the others, for example a
cache entry handed to several consumers, or a node referenced from several threads. It costs more
than [`unique_ptr`](./unique-ptr.md): a separate heap block, atomic reference counts, and a pointer
twice the size. If one owner can be named, use `unique_ptr`. A `unique_ptr` also converts to a
`shared_ptr` by move, so starting with `unique_ptr` never closes a door.

**Prerequisites:** [unique_ptr](./unique-ptr.md),
[new and delete](../05-memory-and-object-lifetime/new-and-delete.md).

## The control block

A `shared_ptr` is two pointers: one to the object (the **stored pointer**) and one to a **control
block** holding the bookkeeping. Copies of a `shared_ptr` share a control block, which holds:

- the **strong count**: the number of `shared_ptr`s that own the object,
- the **weak count**: the number of [`weak_ptr`](./weak-ptr.md)s observing it (plus one while any strong
  owner exists, in the common implementations),
- the **deleter** and allocator, type-erased, and
- with `make_shared`, the object itself.

<Diagram title="Three owners of one object" caption="Each shared_ptr is a pair (object pointer, control block pointer). The pairs are copied; the control block and the object are not." accent="blue">
  <DiagramRow>
    <DiagramGroup label="Owners (16 bytes each on 64-bit libstdc++)">
      <DiagramNode title="shared_ptr a" />
      <DiagramNode title="shared_ptr b" />
      <DiagramNode title="shared_ptr c" />
    </DiagramGroup>
    <DiagramArrow direction="right" label="all point to" />
    <DiagramNode title="Control block" accent>strong = 3, weak count, deleter, allocator</DiagramNode>
    <DiagramArrow direction="right" label="manages" />
    <DiagramNode title="Widget" dashed>the object</DiagramNode>
  </DiagramRow>
</Diagram>

The control block's exact layout is implementation-defined; libstdc++ uses two
counters plus a type-erased deleter, and `sizeof(std::shared_ptr<T>)` is two pointers on 64-bit
targets (the standard does not require either; other libraries may differ).

When the strong count drops to zero the object is destroyed (via the deleter). When the weak count
also drops to zero the control block is freed. The reason there are two counts is
[`weak_ptr`](./weak-ptr.md): a weak reference must be able to ask "is the object still alive?",
which needs the control block to outlive the object.

```cpp title="counts.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct Widget {
    ~Widget() { std::puts("~Widget"); }
};

int main() {
    auto a = std::make_shared<Widget>();
    std::printf("1: %ld\n", a.use_count());
    {
        auto b = a;                                   // copy: count++
        std::printf("2: %ld\n", a.use_count());
        auto c = std::move(a);                        // move: count unchanged, a is empty
        std::printf("3: %ld %s\n", c.use_count(), a ? "a owns" : "a empty");
    }                                                 // b and c destroyed: count -> 0
    std::puts("end");
}
```

```text
1: 1
2: 2
3: 2 a empty
~Widget
end
```

`use_count()` is for diagnostics. Under concurrency the value may be stale the instant you read it,
and `unique()` (the "count == 1" test) was removed in C++20 for that reason.

## `make_shared` and the two allocations

`std::shared_ptr<T>(new T(args))` performs two allocations: one for the object (your `new`) and one
for the control block. `std::make_shared<T>(args...)` performs one, placing the control block and
the object side by side. That is faster, improves locality, and is exception-safe. The following
program counts calls to the global `operator new`:

```cpp title="allocs.cpp" showLineNumbers
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

static int g_allocs = 0;
void* operator new(std::size_t n) {
    ++g_allocs;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Widget { int v = 0; };

int main() {
    g_allocs = 0;
    { std::shared_ptr<Widget> a(new Widget); }
    std::printf("shared_ptr(new): %d allocations\n", g_allocs);

    g_allocs = 0;
    { auto b = std::make_shared<Widget>(); }
    std::printf("make_shared:     %d allocation\n", g_allocs);
}
```

```text
shared_ptr(new): 2 allocations
make_shared:     1 allocation
```

(Measured with libstdc++ from GCC 15 on x86-64 Linux. The standard only *recommends* that
`make_shared` use a single allocation, so other library implementations may differ.)

`make_shared` has trade-offs, and the second is easy to miss:

- **Object memory is freed with the control block.** After the last `shared_ptr` is gone the object
  is destroyed, but its storage is part of the control block and stays allocated until the last
  `weak_ptr` is gone too. For a large object with long-lived `weak_ptr`s, that memory is held much
  longer than with `shared_ptr(new T)`, where it is freed immediately.
- **No custom deleter, no class-specific `operator new`.** It always uses `std::allocator` (use
  `std::allocate_shared` for a custom allocator). If the type needs `delete` through a deleter, or
  its own `operator new`, construct `shared_ptr` directly.
- **It needs a public constructor**, like `make_unique`. A private constructor needs the direct form.
- **Array support** came in C++20: `make_shared<T[]>(n)` and `make_shared<T[N]>()`.

## Where the deleter lives

The deleter is stored in the control block with its type erased, so it is **not part of the
`shared_ptr`'s type**: `shared_ptr<File>` is the same type whether it closes with `fclose` or
`delete`. A second consequence is that a `shared_ptr<Base>` created from a `Derived*` remembers how
to delete a `Derived`, so a virtual destructor isn't strictly required for correctness. (Add one
anyway if anything else can `delete` through a `Base*`.) The deleter mechanics are on
[custom deleters](./custom-deleters.md).

```cpp title="erased-deleter.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct Base { ~Base() { std::puts("~Base"); } };           // note: non-virtual
struct Derived : Base { ~Derived() { std::puts("~Derived"); } };

int main() {
    std::shared_ptr<Base> p(new Derived);   // deleter remembers "delete (Derived*)"
}                                           // runs ~Derived, then ~Base
```

```text
~Derived
~Base
```

With `make_shared<Derived>()` converted to `shared_ptr<Base>`, the same holds: the control block was
built for `Derived`. With `unique_ptr<Base>` it would be undefined behavior.

## Ownership operations

| Operation | Effect |
|---|---|
| copy construct / assign | shares ownership, strong count + 1 |
| move construct / assign | transfers ownership, count unchanged, source empty |
| `reset()` / `reset(p)` | release this ownership / own `p` through a new control block |
| `get()` | stored raw pointer, no ownership change |
| `use_count()` | strong count (approximate under concurrency) |
| `weak_ptr<T>(sp)` | observer; does not change the strong count |
| `swap` | exchange pointers |
| aliasing constructor | `shared_ptr<U>(owner, ptr)`: shares `owner`'s control block, points at `ptr` |

### The aliasing constructor

`std::shared_ptr<U>(const shared_ptr<T>& owner, U* ptr)` creates a pointer that **owns** whatever
`owner` owns but **points at** `ptr`. Typical use: hand out a `shared_ptr` to a member or element
that keeps the whole parent alive. `ptr` is not deleted separately and is not checked for being
related to the owned object.

```cpp title="aliasing.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <string>

struct Config {
    std::string name = "prod";
    int retries = 3;
    ~Config() { std::puts("~Config"); }
};

std::shared_ptr<int> retries_of(const std::shared_ptr<Config>& c) {
    return std::shared_ptr<int>(c, &c->retries);   // points into *c, shares c's control block
}

int main() {
    std::shared_ptr<int> r;
    {
        auto cfg = std::make_shared<Config>();
        r = retries_of(cfg);
        std::printf("count %ld\n", cfg.use_count());
    }                                              // cfg is gone, but r still owns the Config
    std::printf("retries %d\n", *r);
}
```

```text
count 2
retries 3
~Config
```

## Never create two owners from one raw pointer

Each `shared_ptr` constructed from a raw pointer makes its **own** control block with a count of 1.
Two of them would delete the same object twice:

```cpp title="fragment: double ownership (bug)"
Widget* raw = new Widget;
std::shared_ptr<Widget> a(raw);
std::shared_ptr<Widget> b(raw);   // second control block: double delete when both die
```

Always copy a `shared_ptr` to share, or create it once with `make_shared`.
`std::enable_shared_from_this` solves the case where an object needs to hand out `shared_ptr`s to
itself.

### `enable_shared_from_this`

Inherit publicly from `std::enable_shared_from_this<T>` and call `shared_from_this()` instead of
`shared_ptr<T>(this)`. The base class holds a `weak_ptr` that the first `shared_ptr` constructed
for the object initializes, so every pointer produced shares one control block.

```cpp title="from-this.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <vector>

struct Task : std::enable_shared_from_this<Task> {
    void schedule(std::vector<std::shared_ptr<Task>>& queue) {
        queue.push_back(shared_from_this());       // not shared_ptr<Task>(this)
    }
};

int main() {
    std::vector<std::shared_ptr<Task>> queue;
    auto t = std::make_shared<Task>();
    t->schedule(queue);
    std::printf("count %ld\n", t.use_count());

    Task on_stack;
    try {
        on_stack.schedule(queue);                  // no shared_ptr owns it yet
    } catch (const std::bad_weak_ptr&) {
        std::puts("bad_weak_ptr");
    }
}
```

```text
count 2
bad_weak_ptr
```

Calling `shared_from_this()` on an object not yet owned by a `shared_ptr` throws
`std::bad_weak_ptr` *(since C++17; undefined behavior before)*. In particular, don't call it in the
constructor, because the owning `shared_ptr` does not exist yet. C++17 also added `weak_from_this()`.

## Thread safety

The standard guarantees these separately:

- **The control block is thread-safe.** Copying, destroying and `use_count` on different
  `shared_ptr` *objects* that share a control block may run concurrently from different threads
  without a race on the counts. libstdc++ on Linux selects atomic or plain counter updates at run time
  depending on whether the program uses threads; MSVC and libc++ use atomic operations.
- **The pointee is not protected.** Two threads writing the same `Widget` through different
  `shared_ptr`s race unless you synchronize.
- **A single `shared_ptr` object is not thread-safe.** One thread reassigning `p` while another
  copies `p` is a data race on `p`, even though each is fine on its own. `std::atomic<std::shared_ptr<T>>`
  *(C++20)* is the supported way to share a `shared_ptr` variable. The `std::atomic_load(&p)` free
  functions are deprecated in C++20.

The atomic increment on every copy is the main cost of `shared_ptr`: it is a cache-line
read-modify-write that contends when many threads copy the same pointer. Don't copy in hot loops
that only read.

## Passing a `shared_ptr`

Passing by value costs an atomic increment and decrement. Choose the parameter by what the callee
does with ownership (C++ Core Guidelines R.34 to R.37):

| The function... | Parameter |
|---|---|
| uses the object | `Widget&` or `Widget*` (pass `*sp`) |
| shares or stores ownership | `std::shared_ptr<Widget>` by value |
| may or may not keep a copy | `const std::shared_ptr<Widget>&` |
| reseats the caller's pointer | `std::shared_ptr<Widget>&` |

The caller must guarantee the borrowed reference stays valid during the call, which is easy when its
own `shared_ptr` outlives the call and impossible if the callee could reset that same pointer
through some other path.

## Conversions and casts

`shared_ptr<Derived>` converts implicitly to `shared_ptr<Base>`. For downcasts and `const` changes
use `std::static_pointer_cast`, `std::dynamic_pointer_cast`, `std::const_pointer_cast` and
`std::reinterpret_pointer_cast` *(C++17)*: they return a `shared_ptr` that shares the control
block. Casting the raw pointer out and into a new `shared_ptr` would create a second control block
(see above). `dynamic_pointer_cast` returns an empty pointer if the dynamic type doesn't match.

## Pitfalls

- **Cycles leak.** If `A` holds a `shared_ptr<B>` and `B` holds a `shared_ptr<A>`, neither count
  reaches zero. Make the back reference a [`weak_ptr`](./weak-ptr.md).
- **Overuse.** `shared_ptr` everywhere makes lifetimes hard to reason about (the object dies at an
  unpredictable point, possibly on another thread) and costs atomic traffic. Start from
  `unique_ptr` and value members.
- **Constructing from `this` or a raw pointer twice**, covered above.
- **Concurrent reassignment of one `shared_ptr` variable**, covered above.
- **`make_shared` plus long-lived `weak_ptr`s** pins the object's memory.
- **Destruction cascades.** Dropping the last reference to the head of a long `shared_ptr` list
  destroys nodes recursively and can overflow the stack. Unlink iteratively in the destructor.
- **Callbacks that capture `shared_ptr` of their owner** create cycles. Capture a `weak_ptr` and
  `lock()` it inside the callback.

## Key points

- Shared ownership via a control block with strong and weak counts; the object dies with the last strong owner.
- Two pointers wide; copying is an atomic increment.
- Prefer `make_shared`, unless you need a custom deleter or must free the memory before the last `weak_ptr` goes.
- The deleter is type-erased; it is not part of the type.
- Never build two `shared_ptr`s from one raw pointer; use `enable_shared_from_this`.
- The counts are thread-safe; the pointee and a single `shared_ptr` object are not.

## Related

- [weak_ptr](./weak-ptr.md): the non-owning observer that breaks cycles and checks liveness.
- [Custom deleters](./custom-deleters.md): per-object cleanup, and how it differs from `unique_ptr`.
- [unique_ptr](./unique-ptr.md): the cheaper default when one owner is enough.
