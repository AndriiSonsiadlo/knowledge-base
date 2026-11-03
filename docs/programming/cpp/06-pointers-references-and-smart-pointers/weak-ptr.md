---
id: weak-ptr
title: std::weak_ptr
sidebar_label: weak_ptr
sidebar_position: 7
tags: [c++, smart-pointers, weak-ptr, observer, circular-references, cpp11]
---

# std::weak_ptr

`std::weak_ptr<T>` *(C++11, `<memory>`)* is a non-owning handle to an object managed by
[`shared_ptr`](./shared-ptr.md). It does not keep the object alive, and it can tell you whether the
object still exists. That solves two problems that `shared_ptr` alone can't: **cycles** (two
objects that own each other never get freed) and **safe observation** (a raw pointer to a
shared-owned object dangles silently, while a `weak_ptr` knows it expired).

**Prerequisites:** [shared_ptr](./shared-ptr.md), especially its control block and strong/weak
counts.

## What it is, and what it isn't

A `weak_ptr` holds a pointer to the same control block as the `shared_ptr`s it observes and
increments the control block's **weak** count. It has no strong count of its own, so it doesn't
influence when the object is destroyed. It deliberately has no `operator*` or `operator->`: you
can't touch the object without first proving it is still there.

| Operation | Effect |
|---|---|
| `weak_ptr<T> w(sp)`, `w = sp` | observe what `sp` owns (from a `shared_ptr` or another `weak_ptr`, never a raw pointer) |
| `w.lock()` | returns a `shared_ptr<T>`: owning if the object is alive, **empty** if it is gone |
| `w.expired()` | `true` if no strong owner remains |
| `w.use_count()` | current strong count (0 if expired) |
| `w.reset()` | stop observing |
| `w.owner_before(x)` | ordering by control block (see below) |

<Walkthrough title="One object, an owner and an observer" caption="Strong owners keep the object alive; the weak observer only keeps the control block." accent="green">
  <Step title="An owner and an observer">

```cpp
auto sp = std::make_shared<Widget>();
std::weak_ptr<Widget> w = sp;
```

`sp.use_count()` is <StepChange>1</StepChange>. The weak pointer adds nothing to it. `w.expired()` is `false`.

  </Step>
  <Step title="Lock for the duration of a use">

```cpp
if (auto locked = w.lock()) { /* use *locked */ }
```

Inside the `if`, `locked` is a second strong owner, so the count is <StepChange>2</StepChange>. The object cannot be destroyed while `locked` is in scope, even if `sp` is reset on another thread.

  </Step>
  <Step title="The owner lets go">

```cpp
sp.reset();
```

The strong count reaches <StepChange>0</StepChange>: the `Widget` is destroyed. The control block lives on because `w` still refers to it.

  </Step>
  <Step title="The observer finds out">

```cpp
w.expired();   // true
w.lock();      // empty shared_ptr
```

When `w` itself is destroyed, the weak count reaches zero and the control block is freed. With `make_shared`, that is also when the object's storage is returned.

  </Step>
</Walkthrough>

```cpp title="lifecycle.cpp" showLineNumbers
#include <cstdio>
#include <memory>

struct Widget {
    ~Widget() { std::puts("~Widget"); }
};

int main() {
    auto sp = std::make_shared<Widget>();
    std::weak_ptr<Widget> w = sp;
    std::printf("use_count %ld, expired %d\n", w.use_count(), w.expired());

    if (auto locked = w.lock())
        std::printf("locked, use_count %ld\n", locked.use_count());

    sp.reset();                                           // last strong owner gone
    std::printf("use_count %ld, expired %d\n", w.use_count(), w.expired());
    std::printf("lock() %s\n", w.lock() ? "non-empty" : "empty");
}
```

```text
use_count 1, expired 0
locked, use_count 2
~Widget
use_count 0, expired 1
lock() empty
```

## `lock()`, not `expired()` then `lock()`

`lock()` atomically checks that the strong count is non-zero and increments it (conceptually a
compare-and-swap loop in the implementation), so there is no gap between "is it alive?" and "now I
own it". Splitting the check from the use opens a race:

```cpp
// Racy: another thread may drop the last owner between the two lines.
if (!w.expired()) {
    auto sp = w.lock();   // may already be empty
    sp->use();            // null dereference
}

// Correct: one call, test the result.
if (auto sp = w.lock()) {
    sp->use();
}
```

`expired()` is only a hint ("it was alive a moment ago") and is fine for cheap pruning of a list of
observers. Anything that goes on to use the object must use the pointer `lock()` returned. Keep the
locked `shared_ptr` for the shortest scope that works: while it exists, it is a real owner, and it
may be the one that ends up running the object's destructor.

## Breaking a cycle

The textbook problem: a parent owns its children and each child points back to its parent. If both
directions are `shared_ptr`, the parent's count never reaches zero while any child exists, and
the children's counts never reach zero while the parent exists. Nothing is freed.

```cpp title="cycle.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <vector>

struct LeakyNode {
    std::shared_ptr<LeakyNode> peer;                 // owning both ways: cycle
    ~LeakyNode() { std::puts("~LeakyNode"); }
};

struct Parent;
struct Child {
    std::weak_ptr<Parent> parent;                    // non-owning back reference
    ~Child() { std::puts("~Child"); }
};
struct Parent {
    std::vector<std::shared_ptr<Child>> children;    // the owning direction
    ~Parent() { std::puts("~Parent"); }
};

int main() {
    {   // Leak: this scope ends and ~LeakyNode never runs.
        auto a = std::make_shared<LeakyNode>();
        auto b = std::make_shared<LeakyNode>();
        a->peer = b;
        b->peer = a;
    }
    std::puts("-- after leaky scope (no destructor ran)");

    {   // No leak: ownership is a tree, the back edge is weak.
        auto p = std::make_shared<Parent>();
        auto c = std::make_shared<Child>();
        c->parent = p;
        p->children.push_back(c);
    }
    std::puts("-- after tree scope");
}
```

The leak is real: built with `-fsanitize=address`, LeakSanitizer reports two leaked allocations
(the two `make_shared` blocks) at exit and the process returns a non-zero status. The output below is
from a run with `ASAN_OPTIONS=detect_leaks=0`:

```text
-- after leaky scope (no destructor ran)
~Parent
~Child
-- after tree scope
```

The rule: **ownership edges form a tree (or DAG) of `shared_ptr`s; every edge that goes "up" or
"sideways" is a `weak_ptr`**. Parent pointers, observer lists and caches usually fall on the weak
side. If you can't draw which side owns, the design needs a decision before the smart pointer does.

## Observers and caches

A `weak_ptr` lets a registry refer to objects without controlling their lifetime. The registry
checks `lock()` when it needs the object and removes entries that have expired.

```cpp title="observers.cpp" showLineNumbers
#include <algorithm>
#include <cstdio>
#include <memory>
#include <vector>

struct Listener {
    int id;
    explicit Listener(int i) : id(i) {}
    void notify() const { std::printf("listener %d notified\n", id); }
};

class Subject {
    std::vector<std::weak_ptr<Listener>> listeners_;
public:
    void subscribe(const std::shared_ptr<Listener>& l) { listeners_.push_back(l); }

    void publish() {
        // erase expired entries, then notify the rest
        std::erase_if(listeners_, [](const std::weak_ptr<Listener>& w) {
            if (auto l = w.lock()) { l->notify(); return false; }
            return true;
        });
    }
    std::size_t size() const { return listeners_.size(); }
};

int main() {
    Subject s;
    auto a = std::make_shared<Listener>(1);
    {
        auto b = std::make_shared<Listener>(2);
        s.subscribe(a);
        s.subscribe(b);
        s.publish();                       // both alive
    }                                      // b destroyed; the subject never owned it
    s.publish();                           // only a is notified; b's entry is pruned
    std::printf("%zu subscribed\n", s.size());
}
```

```text
listener 1 notified
listener 2 notified
listener 1 notified
1 subscribed
```

`std::erase_if` for `std::vector` is C++20. The same shape gives a **cache**: a
`map<Key, weak_ptr<Value>>` that returns the live object if someone still uses it, and otherwise
rebuilds it. Entries for dead objects accumulate until you prune them.

Two limits to know:

- **It only observes `shared_ptr`-managed objects.** There is no `weak_ptr` for an object owned by a
  `unique_ptr`, a stack variable or a container. If the owner is a `unique_ptr`, the observer must
  rely on a lifetime guarantee instead, or the design needs `shared_ptr`.
- **A listener must be owned by a `shared_ptr`**, which dictates how callers construct it.

## `enable_shared_from_this`

A class that derives from `std::enable_shared_from_this<T>` carries a hidden `weak_ptr` to itself,
set by the first `shared_ptr` that takes ownership. That is how `shared_from_this()` and
`weak_from_this()` *(C++17)* find the control block. Its use, and why `shared_ptr<T>(this)` is wrong,
is covered on [shared_ptr](./shared-ptr.md#enable_shared_from_this). For callbacks, capture
`weak_from_this()` so the callback does not keep the object alive:

```cpp
// fragment: inside a member function of a class deriving enable_shared_from_this<Self>
schedule([weak = weak_from_this()] {
    if (auto self = weak.lock()) self->on_timer();   // runs only if still alive
});
```

## Ordering and hashing

`weak_ptr` has no `operator<` or `std::hash`, because a `weak_ptr` has no stable pointer value (the
object may be gone). To use one as a map key, compare by **ownership** with `std::owner_less<>`
(`owner_before`), which orders by control block and works for `shared_ptr` and `weak_ptr` alike.
Two pointers compare equivalent if they share a control block, even if their stored pointers
differ (aliasing). `std::owner_hash` and `std::owner_equal` *(C++26)* do the same for unordered
containers.

## Thread safety and cost

- `lock()`, `expired()`, copying and destroying `weak_ptr`s that share a control block may be called
  concurrently on **different `weak_ptr` objects**, like `shared_ptr` copies. A single `weak_ptr`
  object that one thread modifies while another reads is a data race; `std::atomic<std::weak_ptr<T>>`
  *(C++20)* covers that.
- `sizeof(weak_ptr<T>)` equals `sizeof(shared_ptr<T>)`: two pointers in libstdc++.
- `lock()` costs an atomic compare-and-swap loop, slightly more than copying a `shared_ptr`.
- A live `weak_ptr` keeps the **control block** allocated. Many long-lived `weak_ptr`s to dead
  objects mean leaked control blocks; with `make_shared`, that also means the object's storage
  (see [make_shared](./shared-ptr.md#make_shared-and-the-two-allocations)).

## Pitfalls

- **Check then lock** as two steps. Use `lock()` once and test the result.
- **Holding the locked `shared_ptr` too long** (for example in a member), turning an observer back
  into an owner, and recreating the cycle.
- **Expecting a `weak_ptr` to a stack or `unique_ptr`-owned object.** Not possible.
- **Never pruning.** Containers of `weak_ptr` grow with dead entries until you remove them.
- **A weak back edge to an object nobody else owns.** If the `shared_ptr` is destroyed when the
  creating function returns, the weak pointer was expired from the start.

## Key points

- `weak_ptr` observes without owning: no effect on the strong count, no direct access.
- `lock()` turns it into a `shared_ptr` or an empty one, atomically.
- Use it for back references, observers and caches, so that `shared_ptr` ownership stays a tree.
- It keeps the control block (and, with `make_shared`, the storage) alive until it is destroyed.

## Related

- [shared_ptr](./shared-ptr.md): the owner it observes, control block layout and `make_shared`.
- [unique_ptr](./unique-ptr.md): when a single owner makes the whole question moot.
- [Custom deleters](./custom-deleters.md): per-object cleanup that runs when the strong count hits zero.
