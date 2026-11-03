---
id: const-pointers
title: const Pointers
sidebar_label: const Pointers
sidebar_position: 4
tags: [c++, pointers, const, const-correctness, const_cast, qualification-conversion]
---

# const Pointers

A pointer involves two objects, the pointer and the thing it points to, and `const` can apply to
either one. Mixing the two up is the classic source of "why won't this compile" and, worse, of
`const_cast` calls that turn into undefined behavior. This page covers the four pointer forms, how
`const` survives (and doesn't survive) conversions between pointer types, and the rules for
casting it away. The general idea of top-level versus low-level `const` is introduced on
[const and volatile qualifiers](../03-types-and-values/cv-qualifiers.md#top-level-and-low-level-const).

**Prerequisites:** [Raw pointers](./raw-pointers.md),
[const and volatile qualifiers](../03-types-and-values/cv-qualifiers.md).

## The four forms

Read a declaration from the name outward, right to left. A `const` before the `*` qualifies the
pointee; a `const` after the `*` qualifies the pointer itself. `const int` and `int const` are the
same type.

| Declaration | Reads as | Reseat `p` | Write `*p` |
|---|---|---|---|
| `int* p` | pointer to int | yes | yes |
| `const int* p` (or `int const* p`) | pointer to const int | yes | no |
| `int* const p` | const pointer to int | no | yes |
| `const int* const p` | const pointer to const int | no | no |

```cpp title="forms.cpp" showLineNumbers
int main() {
    int a = 1, b = 2;

    const int* pc = &a;         // pointee is read-only through pc
    // *pc = 5;                 // error: assignment of read-only location
    pc = &b;                    // fine: pc itself can move

    int* const cp = &a;         // pointer is fixed
    *cp = 5;                    // fine: a is now 5
    // cp = &b;                 // error: cp is const

    const int* const both = &a; // neither
    return *pc + *cp + *both;   // 2 + 5 + 5
}
```

<Diagram title="Which const guards what" caption="The pointer and the pointee are separate objects with separate constness." accent="green">
  <DiagramRow>
    <DiagramNode title="const int* p">`p` can move, `*p` can't be written</DiagramNode>
    <DiagramNode title="int* const p">`p` can't move, `*p` can be written</DiagramNode>
    <DiagramNode title="const int* const p" accent>neither can change</DiagramNode>
  </DiagramRow>
</Diagram>

A pointer-to-const does **not** promise the target is constant. It promises that *this path*
won't modify it. The object may well change through another name:

```cpp title="view.cpp" showLineNumbers
#include <cstdio>

int main() {
    int x = 1;
    const int* view = &x;   // read-only view of a mutable int
    x = 2;                  // legal: x is not const
    std::printf("%d\n", *view);
}
```

```text
2
```

## Conversions: adding `const` is free, removing it is not

Converting `T*` to `const T*` is implicit and safe, because it only takes away permissions. The
reverse needs a `const_cast`. A multi-level pointer adds a subtlety: `T**` does not convert to
`const T**`, even though it looks like the same rule one level down.

```cpp title="conversions.cpp" showLineNumbers
int main() {
    int x = 0;
    int* p = &x;
    const int* cp = p;              // OK: add low-level const
    (void)cp;
    // int* back = cp;              // error: discards const

    int** pp = &p;
    // const int** bad = pp;        // error, and for a good reason (below)
    const int* const* ok = pp;      // OK: once const is added at one level, every level above it (except the outermost) is const too
    return **ok;
}
```

If `int**` were convertible to `const int**`, you could write through the `const int**` a pointer to
a genuinely `const` object into `p`, and then modify that object through `*p`:

```cpp
// Hypothetical: pretend the conversion were allowed (it is not).
const int c = 10;
int* p;
const int** q = &p;     // the forbidden conversion
*q = &c;                // stores &c into p, no cast needed
*p = 20;                // modifies a const object
```

The language rule that blocks this (the **qualification conversion** rules) says: if you add `const` at one level, you must also have `const` at
every level between it and the outermost pointer. `const int* const*` satisfies that, so it works.

## Casting away const

`const_cast<T>` is the only cast that removes `const` (or `volatile`). The cast itself is always
legal. What matters is the object underneath:

- If the object was **defined** `const`, writing to it through any path is **undefined behavior** (except to its `mutable` members).
  The compiler may place it in read-only memory or fold reads to the initial value.
- If the object was not defined `const` and you merely reached it through a `const` path, the write
  is fine.

```cpp title="const-cast.cpp" showLineNumbers
#include <cstdio>

// A C-style API that never modifies s but forgot to say so.
extern "C" int legacy_len(char* s) {
    int n = 0;
    while (s[n]) ++n;
    return n;
}

void touch(const int* p) {
    *const_cast<int*>(p) = 99;     // legal only if *p was not defined const
}

int main() {
    const char* name = "pointer";
    std::printf("%d\n", legacy_len(const_cast<char*>(name)));   // OK: it only reads

    int plain = 1;
    touch(&plain);                 // fine: plain was not defined const
    std::printf("%d\n", plain);

    const int fixed = 1;
    // touch(&fixed);              // undefined behavior: writes to an object defined const
    (void)fixed;
}
```

```text
7
99
```

Legitimate uses of `const_cast` are narrow: calling a `const`-incorrect C API that only reads, and
sharing one implementation between `const` and non-`const` overloads of a member function. Anywhere
else, it means a `const` was put in the wrong place, and the fix is to change the declaration.

String literals are the common trap. In C++ the type of `"abc"` is `const char[4]`, and modifying
the characters is undefined behavior; `char* s = "abc";` has been ill-formed since C++11. Use
`const char*`, or `char s[] = "abc";` to get a modifiable copy.

## Function parameters and return types

`const T*` and `const T&` parameters say "I only read this", and they accept both const and non-const
arguments. A top-level `const` on a by-value parameter (`void f(const int x)`) is not part of the
function's type and only restricts the body, so it is rarely worth writing in a declaration.

```cpp title="params.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>

std::size_t count_zeros(const int* data, std::size_t n) {   // reads only
    std::size_t z = 0;
    for (std::size_t i = 0; i < n; ++i) z += (data[i] == 0);
    return z;
}

void fill(int* data, std::size_t n, int v) {                // writes: non-const
    for (std::size_t i = 0; i < n; ++i) data[i] = v;
}

int main() {
    int buf[4] = {0, 1, 0, 2};
    const int frozen[3] = {0, 0, 7};
    std::printf("%zu %zu\n", count_zeros(buf, 4), count_zeros(frozen, 3));
    fill(buf, 4, 0);
    // fill(frozen, 3, 0);   // error: const int* to int*
    std::printf("%zu\n", count_zeros(buf, 4));
}
```

```text
2 2
4
```

Returning a pointer-to-const (`const Foo* find(...)`) hands out a read-only handle. Returning `T* const`
is pointless: the returned pointer is a copy, so its top-level `const` is ignored.

## Pointers to arrays and `const`

`const` on an array element type applies to every element, and it moves through the array-to-pointer
conversion: `const int a[3]` decays to `const int*`. A pointer to the whole array is
`const int (*)[3]`. In a multidimensional array, a row pointer is `const int (*)[3]`, not
`const int**`. The `**` form is a different thing, a pointer to a pointer, and no array converts to it.

## const and smart pointers

The same two-level split exists for [`unique_ptr`](./unique-ptr.md) and
[`shared_ptr`](./shared-ptr.md), spelled differently. `const std::unique_ptr<T>` is the *const
pointer* form (can't reseat), while `std::unique_ptr<const T>` is the *pointer to const* form (can't
modify the pointee). On a smart pointer, `operator*` returns `T&` and `operator->` returns `T*`, both from `const`
member functions, so a `const std::unique_ptr<T>` still lets you modify the pointee. This is
**shallow const**, the same as for raw pointers. [`std::propagate_const`](https://en.cppreference.com/w/cpp/experimental/propagate_const)
(library fundamentals TS v2, not in the standard) gives deep const.

## Pitfalls

- **Misreading placement.** `const int*` and `int const*` are identical; `int* const` is different.
  The position relative to `*` decides.
- **`const_cast` then write** on an object that was defined `const`: undefined behavior, and often
  no crash at all until an optimizer exploits it.
- **Assuming pointer-to-const is immutable.** It is a restriction on one path.
- **`T**` to `const T**`.** Rejected for the reason above; use `const T* const*`.

## Key points

- `const` left of `*` protects the pointee, right of `*` fixes the pointer. Read right to left.
- Adding `const` is implicit; removing needs `const_cast`, and writing after it is only valid if the object wasn't defined `const`.
- Multi-level pointers need `const` at every intermediate level.
- Smart pointers are shallow const too.

## Related

- [const and volatile qualifiers](../03-types-and-values/cv-qualifiers.md): `const` objects, member functions, top-level and low-level const in general.
- [References](./references.md): references to const and why they bind to temporaries.
- [Conversions and promotions](../03-types-and-values/conversions-and-promotions.md): where `const_cast` sits among the casts.
