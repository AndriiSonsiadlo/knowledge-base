---
id: unique-ptr
title: std::unique_ptr
sidebar_label: unique_ptr
sidebar_position: 5
tags: [c++, smart-pointers, unique-ptr, ownership, raii, move-only, cpp11]
---

# std::unique_ptr

`std::unique_ptr<T>` *(C++11, `<memory>`)* is a smart pointer that **solely owns** the object it
points to and destroys it when the `unique_ptr` is destroyed or reset. It is the default way to own
a dynamically allocated object: it is the same size as a raw pointer in the common case, adds no
run-time bookkeeping, and turns "who deletes this?" into a property the compiler enforces. Because
there is one owner, it can't be copied, only moved.

**Prerequisites:** [Raw pointers](./raw-pointers.md),
[new and delete](../05-memory-and-object-lifetime/new-and-delete.md),
[RAII](../13-idioms-and-design/01-raii.md). Moves are explained in
[copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## Ownership you can see in the type

A `unique_ptr` holds a raw pointer and a deleter. The destructor calls the deleter on the pointer if
it is non-null. Copying is deleted, so two `unique_ptr`s can never own the same object; move
construction and move assignment transfer ownership and leave the source null.

<Diagram title="Moving a unique_ptr" caption="Exactly one unique_ptr owns the Widget at any time." accent="green">
  <DiagramRow>
    <DiagramNode title="a">after the move: nullptr</DiagramNode>
    <DiagramArrow direction="right" label="std::move" />
    <DiagramNode title="b" accent>owns the Widget</DiagramNode>
    <DiagramArrow direction="right" label="destructor deletes" />
    <DiagramNode title="Widget" dashed>heap object</DiagramNode>
  </DiagramRow>
</Diagram>

```cpp title="basics.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <utility>

struct Widget {
    int id;
    explicit Widget(int i) : id(i) { std::printf("Widget(%d)\n", id); }
    ~Widget() { std::printf("~Widget(%d)\n", id); }
};

int main() {
    auto a = std::make_unique<Widget>(1);       // C++14
    // auto copy = a;                           // error: copy constructor is deleted
    auto b = std::move(a);                      // ownership moves; a is now null
    std::printf("a %s, b %s\n", a ? "owns" : "empty", b ? "owns" : "empty");

    b = std::make_unique<Widget>(2);            // old Widget(1) is destroyed here
    std::puts("end of main");
}                                               // Widget(2) destroyed here
```

```text
Widget(1)
a empty, b owns
Widget(2)
~Widget(1)
end of main
~Widget(2)
```

Note the order on `b = make_unique<Widget>(2)`: the new object is constructed first, then the
assignment destroys the old one.

## Creating one: `make_unique` over `new`

`std::make_unique<T>(args...)` *(C++14)* allocates, constructs and wraps in one call. The
constructor `unique_ptr<T>(new T(args))` is `explicit`, so you cannot accidentally return or pass a
raw pointer where a `unique_ptr` is expected.

Prefer `make_unique` because it names the type once and avoids a leak that existed before C++17:

```cpp title="fragment: pre-C++17 leak"
// Before C++17 this could leak: the compiler may run  new Widget -> g() -> unique_ptr ctor,
// and if g() throws, the Widget is never owned.
f(std::unique_ptr<Widget>(new Widget(1)), g());
```

C++17 (P0145R3) forbids interleaving the evaluation of one function argument with another, so this
exact leak is gone in C++17 and later, but `make_unique` is still shorter and safe in every mode.

Use the raw constructor when `make_unique` can't do the job: a custom deleter, adopting a pointer
from a factory you don't control, or a type with a private constructor (`make_unique` can't reach
it). For `make_unique` itself:

- It value-initializes: `make_unique<int>()` holds `0`. `std::make_unique_for_overwrite<T>()`
  *(C++20)* default-initializes and leaves a scalar uninitialized, for large buffers you will fill.
- It can't pass braced-init-lists (`make_unique<std::vector<int>>({1,2})` fails to deduce).
- It can't take a custom deleter.

## The operations

| Operation | Effect | Ownership |
|---|---|---|
| `*p`, `p->m`, `p[i]` (array form) | access the object | unchanged |
| `p.get()` | the raw pointer | **unchanged**: don't `delete` it, don't build a second owner from it |
| `bool(p)` / `p != nullptr` | is it non-null | unchanged |
| `p.release()` | returns the raw pointer, `p` becomes null | **given up**: the caller must now delete it |
| `p.reset()` | deletes the object, `p` becomes null | destroyed |
| `p.reset(q)` | deletes the old object, adopts `q` | adopted |
| `p.swap(q)` | exchanges pointers (and deleters) | exchanged |
| `p = std::move(q)` | deletes `p`'s old object, takes `q`'s | transferred |
| `p.get_deleter()` | access the stored deleter | |

`release()` is the escape hatch for handing the pointer to an API that takes ownership
(for example a C library that frees it). Calling it and discarding the result leaks the object.

Comparisons (`==`, `<=>` since C++20) compare the stored pointers, and `std::hash<unique_ptr<T>>`
hashes the pointer, so `unique_ptr`s work as keys of ordered and unordered containers by identity.

## Passing and returning ownership

The parameter type states what the function does with ownership. This is the part of a
`unique_ptr` API that matters most:

| Intent | Signature | Call site |
|---|---|---|
| Uses the object, doesn't care how it is owned | `void use(Widget&)` or `void use(Widget*)` | `use(*p)` |
| Takes ownership (a **sink**) | `void sink(std::unique_ptr<Widget>)` | `sink(std::move(p))` |
| May replace what the caller owns | `void reseat(std::unique_ptr<Widget>&)` | `reseat(p)` |
| Returns ownership (a **factory**) | `std::unique_ptr<Widget> make()` | `auto p = make();` |

`v.emplace_back(new Widget(2))` also compiles, but if the vector must reallocate and that throws, the
raw pointer was never adopted and leaks. Create the `unique_ptr` first (`make_unique`), then move it in.
A `unique_ptr<Widget>` returned by a factory also converts to `std::shared_ptr<Widget>` by move
(`std::shared_ptr<Widget> s = make(3);`) if sharing turns out to be needed.

Taking `const std::unique_ptr<Widget>&` is almost always a mistake: it requires the caller to own
the object through a `unique_ptr` for no benefit, and it can't take ownership. Use `Widget&` or
`Widget*` instead (C++ Core Guidelines R.30 and F.7).

```cpp title="passing.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <utility>
#include <vector>

struct Widget {
    int id;
    explicit Widget(int i) : id(i) {}
};

void inspect(const Widget& w) { std::printf("inspect %d\n", w.id); }       // borrows
void adopt(std::unique_ptr<Widget> w) { std::printf("adopted %d\n", w->id); }   // owns, deletes at end

std::unique_ptr<Widget> make(int id) {
    auto w = std::make_unique<Widget>(id);
    return w;                       // implicit move (or elision); no std::move needed
}

int main() {
    auto w = make(7);
    inspect(*w);
    adopt(std::move(w));            // the move is visible at the call site
    std::printf("after adopt: %s\n", w ? "owns" : "empty");

    std::vector<std::unique_ptr<Widget>> v;
    v.push_back(make(1));           // rvalue: moved in
    v.push_back(std::make_unique<Widget>(2));   // not emplace_back(new ...): see the note above
    // v.push_back(w);              // error: would copy
    for (const auto& p : v) std::printf("%d ", p->id);
    std::puts("");
}
```

```text
inspect 7
adopted 7
after adopt: empty
1 2 
```

A `std::vector<std::unique_ptr<T>>` is a normal container of move-only elements. It can't be copied,
but it can be moved, sorted (elements are swapped) and have elements erased, each erase deleting the
owned object. When the elements are polymorphic, it's the standard way to own a heterogeneous
collection.

## Arrays and `unique_ptr<T[]>`

`unique_ptr<T[]>` is a separate specialization that calls `delete[]` and offers `operator[]` instead
of `*` and `->`. `make_unique<T[]>(n)` allocates `n` value-initialized elements.

```cpp title="array.cpp" showLineNumbers
#include <cstdio>
#include <memory>

int main() {
    auto buf = std::make_unique<int[]>(4);      // four zeros
    buf[2] = 9;
    std::printf("%d %d\n", buf[0], buf[2]);
    // std::unique_ptr<int> wrong(new int[4]);  // compiles, but calls delete (not delete[]): UB
}
```

```text
0 9
```

The array form stores no size, so you keep the length separately. For almost every use,
`std::vector` or `std::array` is better: it knows its size, can grow, and has iterators. The array
`unique_ptr` is for adopting a buffer from another API or for large, fixed-size, uninitialized
storage.

## Polymorphism

A `unique_ptr<Derived>` converts implicitly to `unique_ptr<Base>` when a `Derived*` converts to
`Base*`. The default deleter then calls `delete` on a `Base*`, so **`Base` needs a virtual
destructor** or deleting a `Derived` through it is undefined behavior. (`shared_ptr` doesn't have
this requirement; its deleter is captured when the pointer is created. See
[shared_ptr](./shared-ptr.md).)

```cpp title="poly.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <vector>

struct Shape {
    virtual ~Shape() = default;                 // required for deletion through Shape*
    virtual double area() const = 0;
};
struct Square : Shape {
    double s;
    explicit Square(double s_) : s(s_) {}
    double area() const override { return s * s; }
};
struct Circle : Shape {
    double r;
    explicit Circle(double r_) : r(r_) {}
    double area() const override { return 3.0 * r * r; }
};

std::unique_ptr<Shape> make_shape(bool square) {
    if (square) return std::make_unique<Square>(2.0);   // unique_ptr<Square> -> unique_ptr<Shape>
    return std::make_unique<Circle>(1.0);
}

int main() {
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(make_shape(true));
    shapes.push_back(make_shape(false));
    double total = 0;
    for (const auto& s : shapes) total += s->area();
    std::printf("%.1f\n", total);
}
```

```text
7.0
```

## Incomplete types and the pimpl idiom

`unique_ptr<T>` can be declared with an incomplete `T` (a forward declaration), but wherever its
destructor, move assignment or `reset` is *instantiated*, `T` must be complete, because the default
deleter does `sizeof(T)` and `delete`. In a class holding a `unique_ptr<Impl>`, that means declaring
the special members in the header and defining them (even as `= default`) in the `.cpp` where `Impl`
is complete. Otherwise the compiler generates an inline destructor in every including file and
fails with "invalid application of sizeof to incomplete type". The idiom is on
[Pimpl](../13-idioms-and-design/02-pimpl.md).

## Cost

With the default deleter, `sizeof(std::unique_ptr<T>) == sizeof(T*)` in libstdc++ and libc++ (the
standard does not require it, but both use an empty-base or `[[no_unique_address]]` trick for the
stateless deleter), and the destructor is a null check plus `delete`, which inlines to the same code
as hand-written cleanup. A function-pointer or capturing deleter adds its own state to the object (see
[custom deleters](./custom-deleters.md#unique_ptr-the-deleter-is-part-of-the-type)). Passing a `unique_ptr` **by value** is not free on the common ABIs: because it has a
non-trivial destructor it is passed in memory (by hidden reference) rather than in a register under
the Itanium C++ ABI, so hot paths that only need to look at the object should take `T&` or `T*`.

```cpp title="size.cpp" showLineNumbers
#include <memory>

struct Widget {};

// Holds for libstdc++ and libc++ on 64-bit targets; not guaranteed by the standard.
static_assert(sizeof(std::unique_ptr<Widget>) == sizeof(Widget*));

int main() {}
```

Deleter choices and their costs are covered on [custom deleters](./custom-deleters.md).

## Pitfalls

- **Two owners from one raw pointer.** `unique_ptr<T> a(p); unique_ptr<T> b(p);` deletes `p` twice.
  Likewise `unique_ptr<T> b(a.get());`. Obtain a raw pointer to *lend*, never to own.
- **Using a moved-from `unique_ptr`.** After `std::move(a)` into another owner, `a` is guaranteed
  null, so dereferencing it is a null dereference.
- **Forgetting `[]`.** `unique_ptr<T>` over `new T[n]` calls scalar `delete`: undefined behavior.
- **Non-virtual destructor** on a polymorphic base, see above.
- **Ignoring the result of `release()`.** That leaks the object.
- **Sharing by accident.** If two places truly need to own the object, that is the case for
  [`shared_ptr`](./shared-ptr.md), not for copying `get()` around.
- **Observers that outlive the owner.** A raw pointer kept after the owning `unique_ptr` is reset or
  destroyed dangles. Keep observers shorter-lived than the owner.

## Key points

- `unique_ptr` is the default owner: sole, move-only, zero-overhead with the default deleter.
- Create with `make_unique`; pass by value to transfer ownership, by `T&`/`T*` to borrow.
- `get()` borrows, `release()` gives up ownership, `reset()` destroys.
- Convertible to `unique_ptr<Base>`; needs a virtual destructor there.
- Upgrades to `shared_ptr` by move when sharing is genuinely needed.

## Related

- [shared_ptr](./shared-ptr.md): when ownership truly is shared, and what it costs.
- [Custom deleters](./custom-deleters.md): `unique_ptr<T, D>` for files, handles and non-`delete` cleanup.
- [RAII](../13-idioms-and-design/01-raii.md): the idiom `unique_ptr` is the standard example of.
- [Pimpl](../13-idioms-and-design/02-pimpl.md): the incomplete-type pattern in full.
