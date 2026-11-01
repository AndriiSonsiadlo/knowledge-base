---
id: copy-and-move
title: Copy and Move Semantics
sidebar_label: Copy & Move
sidebar_position: 4
tags: [c++, copy, move, std-move, copy-elision, noexcept]
---

# Copy and Move Semantics

When one object is initialized or assigned from another, a class decides what that means. A
**copy** produces an independent duplicate: the source is unchanged, and both objects own their own
resources. A **move** *(C++11)* is allowed to take the source's resources instead of duplicating
them, leaving the source in a valid but unspecified state. For a type that owns heap memory, a copy
allocates and duplicates every element, while a move swaps a few pointers. This page is the
canonical home for the copy and move operations themselves, `std::move`, and copy elision as it
applies to class objects. Which of these operations a class should declare is covered in
[Rule of 0/3/5](./rule-of-zero-three-five.md).

**Prerequisites:** [lvalues and rvalues](../03-types-and-values/value-categories/lvalues-rvalues.md),
[glvalue, prvalue, xvalue](../03-types-and-values/value-categories/glvalue-prvalue-xvalue.md),
[constructors and destructors](./constructors-and-destructors.md).

## The four operations

A class has up to four operations that create or overwrite an object from another one of the same
type:

| Operation | Signature | Runs for |
|---|---|---|
| Copy constructor | `T(const T&)` | `T b = a;`, `T b(a);`, pass by value from an lvalue |
| Move constructor | `T(T&&)` | the same forms when the source is an rvalue |
| Copy assignment | `T& operator=(const T&)` | `b = a;` with an existing `b` |
| Move assignment | `T& operator=(T&&)` | `b = std::move(a);`, `b = make();` |

Overload resolution picks between them by the source's [value
category](../03-types-and-values/value-categories/glvalue-prvalue-xvalue.md): an lvalue binds to
`const T&` only, an rvalue (prvalue or xvalue) prefers `T&&`. If a class has no usable move
operation, an rvalue binds to `const T&` too, so the "move" silently becomes a copy.

The class below owns a heap array and implements all four. Constructors are the canonical home of
member initializer lists ([constructors and destructors](./constructors-and-destructors.md)); here
the point is what each operation does with the pointer.

```cpp title="buffer.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>
#include <utility>

class Buffer {
public:
    explicit Buffer(std::size_t n) : size_(n), data_(new int[n]{}) {}
    ~Buffer() { delete[] data_; }

    Buffer(const Buffer& other)                     // copy: allocate and duplicate
        : size_(other.size_), data_(new int[other.size_]) {
        for (std::size_t i = 0; i < size_; ++i) data_[i] = other.data_[i];
        std::puts("copy ctor");
    }

    Buffer(Buffer&& other) noexcept                 // move: take the pointer
        : size_(std::exchange(other.size_, 0)),
          data_(std::exchange(other.data_, nullptr)) {
        std::puts("move ctor");
    }

    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            Buffer tmp(other);                      // may throw; *this untouched
            std::swap(size_, tmp.size_);
            std::swap(data_, tmp.data_);
        }
        std::puts("copy assign");
        return *this;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            size_ = std::exchange(other.size_, 0);
            data_ = std::exchange(other.data_, nullptr);
        }
        std::puts("move assign");
        return *this;
    }

    std::size_t size() const { return size_; }

private:
    std::size_t size_;
    int* data_;
};

int main() {
    Buffer a(1000);
    Buffer b = a;              // copy ctor
    Buffer c = std::move(a);   // move ctor; a is now empty
    b = c;                     // copy assign
    c = Buffer(10);            // move assign from a prvalue
    std::printf("%zu %zu %zu\n", a.size(), b.size(), c.size());
}
```

Output (g++ 15, clang++ 21):

```text
copy ctor
move ctor
copy ctor
copy assign
move assign
0 1000 10
```

The third `copy ctor` line comes from the temporary inside copy assignment, which builds the new
state first and only then swaps it in. If the allocation throws, `*this` is unchanged (the strong
exception guarantee). [Copy-and-swap](../13-idioms-and-design/05-copy-and-swap.md) generalizes that
pattern into one by-value assignment operator.

<Diagram title="Copy vs move of a Buffer" caption="A copy allocates a second array. A move transfers the existing one and nulls the source." accent="blue">
  <DiagramGroup label="Copy: Buffer b = a;">
    <DiagramNode title="a">size 1000, data → array #1</DiagramNode>
    <DiagramNode title="b">size 1000, data → array #2 (new, 1000 ints copied)</DiagramNode>
  </DiagramGroup>
  <DiagramGroup label="Move: Buffer c = std::move(a);">
    <DiagramNode title="a" dashed>size 0, data → nullptr</DiagramNode>
    <DiagramNode title="c" accent>size 1000, data → array #1 (no allocation)</DiagramNode>
  </DiagramGroup>
</Diagram>

## What a move must leave behind

The moved-from object will still be destroyed, and it may be assigned to or reused. A move must
therefore leave it in a state where its destructor and its operations without preconditions work.
For standard library types the guarantee is exactly that: **valid but unspecified**. You may call
`clear()`, assign a new value, or destroy it. You must not call something with a precondition, such
as `front()` on a vector that may be empty, without first putting it back into a known state.

```cpp title="moved_from.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

int main() {
    std::vector<int> v1 = {1, 2, 3};
    std::vector<int> v2 = std::move(v1);   // v1: valid but unspecified
    v1.clear();                            // no preconditions: fine
    v1.push_back(4);                       // fine: v1 is now {4}

    const std::string cs = "hello";
    std::string s = std::move(cs);         // const string&& binds to the copy ctor: copies
    std::printf("%zu %zu %s %s\n", v1.size(), v2.size(), cs.c_str(), s.c_str());
}
```

Output: `1 3 hello hello`. Reusing a moved-from object is not undefined behavior. Reading a value
from it and expecting something specific is a logic error.

The last two lines show the second trap: `std::move` on a `const` object yields `const std::string&&`,
which cannot bind to `std::string&&`. It binds to `const std::string&` instead and copies, without a
diagnostic.

## `std::move` and `std::forward` are casts

`std::move(x)` moves nothing. It is `static_cast<std::remove_reference_t<T>&&>(x)`: it turns the
expression `x` into an xvalue so that overload resolution selects the move constructor or move
assignment, if one exists. Use it when you are finished with a named object and want to hand its
resources on:

- passing a local into a sink parameter, `store(std::move(name));`
- moving a member out in a function that consumes the object;
- implementing move operations of a class in terms of its members, `name_(std::move(other.name_))`.

Do not write `return std::move(local);`. A returned local is already treated as an rvalue, and the
cast prevents NRVO (below). GCC warns about this with `-Wpessimizing-move`, which `-Wall` enables.

`std::forward<T>(x)` is the conditional version used in templates: it casts to an rvalue only if
the original argument was an rvalue. It belongs with forwarding references, covered in
[reference collapsing](../03-types-and-values/value-categories/reference-collapsing.md) and
[template argument deduction](../08-templates-and-metaprogramming/template-argument-deduction.md).

## Why move operations should be `noexcept`

`std::vector` growth must give the strong exception guarantee: if reallocation throws, the old
elements must be intact. Moving elements into the new storage cannot be undone if one move throws
halfway, so the library uses `std::move_if_noexcept` and **copies** elements whose move constructor
may throw (unless the type is not copyable at all). A move constructor without `noexcept` therefore
makes every reallocation do full copies. The mechanism and a measured example are on the
[noexcept page](../04-functions-and-call-mechanics/noexcept.md#move-semantics-and-noexcept).

Implicitly generated and `= default` move operations are `noexcept` when every member's move is.
Hand-written ones need the keyword.

## Copy elision

Sometimes no copy or move happens at all, because the object is constructed directly in its final
location. This is **copy elision**, and it comes in two kinds.

- **Guaranteed elision** *(C++17)*. Initializing an object from a prvalue of the same type
  constructs it in place: `T x = T{};` and `return T{};` create one object. Since C++17 this is not
  an optimization but the meaning of a prvalue (temporary materialization), so it works even for
  types with deleted copy and move constructors.
- **Named return value optimization (NRVO).** `return local;` where `local` is a non-volatile
  automatic object (not a function parameter) of the return type *may* be constructed directly in the caller's storage. It is
  permitted, not required. When it does not happen, the return uses the move constructor (the
  returned name is treated as an rvalue), falling back to copy only if there is no move.

```cpp title="elision.cpp" showLineNumbers
#include <cstdio>

struct Noisy {
    Noisy() { std::puts("ctor"); }
    Noisy(const Noisy&) { std::puts("copy"); }
    Noisy(Noisy&&) noexcept { std::puts("move"); }
};

Noisy make_prvalue() { return Noisy{}; }       // guaranteed elision (C++17)
Noisy make_named()   { Noisy n; return n; }    // NRVO: allowed, not required
Noisy make_either(bool b) {
    Noisy x, y;
    return b ? x : y;                          // conditional expr is an lvalue: copy
}

int main() {
    std::puts("-- prvalue");  [[maybe_unused]] Noisy a = make_prvalue();
    std::puts("-- named");    [[maybe_unused]] Noisy b = make_named();
    std::puts("-- either");   [[maybe_unused]] Noisy c = make_either(true);
}
```

Output with g++ 15 at `-O0`:

```text
-- prvalue
ctor
-- named
ctor
-- either
ctor
ctor
copy
```

GCC and Clang apply NRVO here even without optimization, but that is a compiler choice
(`-fno-elide-constructors` turns it off for NRVO, not for the C++17 guaranteed case). The last case
returns an expression that is not a plain name, so neither elision nor the implicit move applies.

Because guaranteed elision is about prvalues, it compiles since C++17 even for a type that can be
neither copied nor moved (see the `Pinned` example on the page below).

The full value-category story behind this, including temporary materialization, is on the
[glvalue, prvalue, xvalue](../03-types-and-values/value-categories/glvalue-prvalue-xvalue.md) page.

## Common mistakes

- **Missing `noexcept` on a hand-written move constructor.** Containers fall back to copying on
  reallocation.
- **`std::move` on a `const` object.** It compiles and copies.
- **`return std::move(local);`.** It disables NRVO and at best gives you the move you would have
  had anyway.
- **Expecting a specific value in a moved-from object.** Only "valid" is promised. Reassign before
  reading.
- **Forgetting to null the source in a hand-written move.** Both objects then free the same
  resource. Prefer `std::exchange` for the steal-and-reset step, or better, members that already
  move correctly ([rule of zero](./rule-of-zero-three-five.md#rule-of-zero)).

## References

- cppreference: [Copy constructors](https://en.cppreference.com/w/cpp/language/copy_constructor),
  [Move constructors](https://en.cppreference.com/w/cpp/language/move_constructor),
  [Copy elision](https://en.cppreference.com/w/cpp/language/copy_elision),
  [`std::move`](https://en.cppreference.com/w/cpp/utility/move)
- P0135R1, *Wording for guaranteed copy elision through simplified value categories* (C++17)
