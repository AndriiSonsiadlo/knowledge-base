---
id: cv-qualifiers
title: const and volatile Qualifiers
sidebar_label: const & volatile
sidebar_position: 2
tags: [c++, const, volatile, qualifiers, const-correctness]
---

# const and volatile Qualifiers

`const` and `volatile`, the **cv-qualifiers**, are part of a type: `const int` and `int` are
different types, and the compiler tracks the difference through every expression, pointer, and
reference. `const` means the object may not be modified through this name. `volatile` means every
access to the object is an observable side effect that the compiler must not remove or merge. This
page covers what the qualifiers attach to, the **top-level / low-level** distinction that the
deduction rules depend on, and `const` member functions. Pointer declarations and `volatile` in
hardware code have their own pages, linked below.

**Prerequisites:** [Fundamental Types](./fundamental-types.md)

## `const` objects

A `const` object must be initialized, and can't be assigned afterwards:

```cpp title="const-basics.cpp" showLineNumbers
int compute() { return 7; }

int main() {
    const int limit = 100;          // known at compile time
    const int answer = compute();   // fine: const doesn't require a constant expression
    // const int missing;           // error: uninitialized const
    // limit = 5;                   // error: assignment of read-only variable
    return limit + answer;
}
```

`const` is a promise about modification, not about compile-time evaluation. When you need a value
the compiler computes, such as an array bound or template argument, use `constexpr`; see
[constexpr Functions](../04-functions-and-call-mechanics/constexpr-functions.md).

Modifying an object that was *defined* `const` is undefined behavior, even if you get a non-`const`
path to it with `const_cast`. Removing `const` is only safe when the object itself was not `const`.
Details are on [const and Pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md#casting-away-const).

## Top-level and low-level `const`

In a compound type, each `const` applies to one level. For pointers, read the declaration from
right to left: `const int* const p` is "`p` is a const pointer to a const int".

<Diagram title="Two levels of const in one declaration" caption="const int* const p = &x;" accent="green">
  <DiagramRow>
    <DiagramNode title="p (the pointer)" accent>**Top-level** `const`: `p` can't be reseated. Dropped when `p` is copied</DiagramNode>
    <DiagramArrow direction="right" label="points to" />
    <DiagramNode title="*p (the int)">**Low-level** `const`: can't write through `p`. Kept when `p` is copied</DiagramNode>
  </DiagramRow>
</Diagram>

- A **top-level** `const` qualifies the object itself: `const int x`, or the pointer in
  `int* const p`.
- A **low-level** `const` qualifies something reached through the object: the pointee in
  `const int* p`, or the referenced object in `const int& r`. A reference has no top-level
  `const`; it can't be reseated anyway.

The distinction matters whenever a value is copied. A copy is a new object, so the source's
top-level `const` doesn't constrain it. Low-level `const` protects some *other* object, so a copy
must keep it:

```cpp title="levels.cpp" showLineNumbers
int main() {
    int x = 1;
    const int ci = 2;

    int a = ci;                 // OK: top-level const of ci is irrelevant to the copy a
    const int* p = &x;          // low-level const
    const int* q = p;           // OK: q keeps the low-level const
    // int* r = p;              // error: would discard the low-level const
    int* const s = &x;          // top-level const
    int* t = s;                 // OK: copying s drops its top-level const
    *t = 3;
    return a + *q;
}
```

This is the rule [auto](./type-deduction/auto.md) and template deduction follow: deducing a
by-value type drops top-level cv-qualifiers and keeps low-level ones. Function signatures follow it
too: `void f(int)` and `void f(const int)` declare the same function, because a top-level `const`
on a by-value parameter only affects the function body. The full set of pointer forms is on
[const and Pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md).

## `const` references

A `const T&` can bind to a `const` or non-`const` lvalue and also to an rvalue, so it is the usual
parameter type for "read this, don't copy it". Binding to a temporary extends the temporary's
lifetime to the reference's. See [Lvalues and Rvalues](./value-categories/lvalues-rvalues.md#how-references-bind).
The referenced object can still change through another name: `const` restricts the reference, not
the object.

## `const` member functions

A member function declared with `const` after the parameter list promises not to modify the
object. Inside it, `this` has type `const T*`, so every data member is accessed as `const`.
Only `const` member functions can be called on a `const` object, or through a `const T&`:

```cpp title="const-member.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <utility>

class Document {
public:
    explicit Document(std::string text) : text_(std::move(text)) {}

    std::size_t length() const {        // callable on const Document
        ++reads_;                       // OK: reads_ is mutable
        return text_.size();
    }
    void append(const std::string& s) { text_ += s; }

    std::size_t reads() const { return reads_; }

private:
    std::string text_;
    mutable std::size_t reads_ = 0;     // bookkeeping, not part of the observable value
};

void show(const Document& d) {
    std::printf("%zu\n", d.length());
    // d.append("!");                   // error: append is not const
}

int main() {
    Document doc("hello");
    show(doc);
    show(doc);
    std::printf("reads: %zu\n", doc.reads());
}
```

```text
5
5
reads: 2
```

`const` and non-`const` member functions can overload each other. That is how containers return
`T&` from `operator[]` on a non-`const` container and `const T&` on a `const` one.

A **`mutable`** data member can be modified even in a `const` member function. Use it for state
that isn't part of the object's logical value: caches, counters, or a mutex. A `const` member
function can be called from several threads at once, so a `mutable` member that it writes needs
synchronization.

## `volatile`

`volatile` tells the compiler that every read and write of the object must happen as written:
it can't keep the value in a register, remove a "redundant" read, or combine two writes. That is
what memory-mapped hardware registers need, and what a variable written from a signal handler
needs (as `volatile std::sig_atomic_t`).

`volatile` does **not** make an access atomic or order it with respect to other threads. It has
never been a way to share data between threads in standard C++; use `std::atomic`. Hardware use,
and what `volatile` does not guarantee, are covered on [volatile](../12-low-level-and-platform/05-volatile.md).
C++20 deprecated several uses of `volatile` that suggested it did more, such as `++` and compound
assignment on a `volatile` variable ([P1152](https://wg21.link/p1152r4)).

`volatile` follows the same top-level / low-level rules as `const`, and the two combine:
`const volatile std::uint32_t*` is a pointer to a read-only register that may change on its own.

## Common mistakes

- **Expecting `const` to make data immutable.** `const int& r = x;` doesn't stop other code from
  changing `x`. It only stops you from changing it through `r`.
- **Top-level `const` on a returned value.** `const std::string f();` prevents the caller from
  moving out of the result and has no other effect. Return non-`const` values.
- **`const` on a by-value parameter in the declaration.** `void f(const int x);` in a header is
  the same signature as `void f(int x);`. Put the `const` only in the definition if you want it.
- **Using `volatile` for thread communication.** It doesn't prevent data races; the program has
  undefined behavior. Use `std::atomic<bool>`.

## Key points

- cv-qualifiers are part of the type and apply to one level of a compound type.
- Copies drop top-level `const` and must keep low-level `const`. Deduction follows the same rule.
- In a `const` member function `this` is `const T*`; `mutable` members are the exception.
- `volatile` is about accesses not being optimized away, not about threads.

## Related

- [const and Pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md): every
  pointer/`const` combination and `const_cast`.
- [volatile](../12-low-level-and-platform/05-volatile.md): memory-mapped I/O, interrupts, and
  `volatile` versus atomics.
