---
id: raw-pointers
title: Raw Pointers
sidebar_label: Raw Pointers
sidebar_position: 1
tags: [c++, pointers, nullptr, void-pointer, function-pointer, dangling]
---

# Raw Pointers

A **raw pointer** is an object whose value is the address of another object or function (or a special
"points nowhere" value). It is the language's most basic form of indirection: it lets code refer to
an object it did not create, choose the target at run time, and let an object outlive the scope that
named it. The price is that a pointer says nothing about whether the target is still alive or who
must clean it up. Everything else in this section, from [references](./references.md) to the
[smart pointers](./unique-ptr.md), exists to fix one of those two gaps.

**Prerequisites:** [Fundamental types](../03-types-and-values/fundamental-types.md),
[storage duration](../05-memory-and-object-lifetime/storage-duration.md) (what "the object is gone"
means).

## Taking an address and following it

`&x` yields a pointer to `x`; `*p` follows a pointer back to the object it points to. The type of
`&x` is `T*` when `x` has type `T`. A pointer is itself an object with its own address and storage,
so there is a pointer-to-pointer type as well.

```cpp title="basics.cpp" showLineNumbers
#include <cstdio>

struct Point { int x, y; };

int main() {
    int value = 42;
    int* p = &value;          // p holds the address of value
    *p = 100;                 // writes through p: value is now 100
    std::printf("%d\n", value);

    Point pt{10, 20};
    Point* pp = &pt;
    pp->x = 30;               // same as (*pp).x = 30
    std::printf("%d %d\n", pt.x, pt.y);

    int** pq = &p;            // a pointer to the pointer
    **pq = 7;
    std::printf("%d\n", value);
}
```

```text
100
30 20
7
```

<Diagram title="Three objects, two levels of indirection" caption="Arrows are addresses. Changing **pq writes to value, not to p." accent="blue">
  <DiagramRow>
    <DiagramNode title="pq" icon="pointer">int**</DiagramNode>
    <DiagramArrow direction="right" label="holds &p" />
    <DiagramNode title="p" icon="pointer">int*</DiagramNode>
    <DiagramArrow direction="right" label="holds &value" />
    <DiagramNode title="value" accent>int, currently 7</DiagramNode>
  </DiagramRow>
</Diagram>

The exact numeric value of a pointer and `sizeof(T*)` are implementation-defined. On x86-64 and
AArch64 Linux, an ordinary object pointer is 8 bytes and holds a virtual address, but the standard
promises neither. Printing a pointer with `%p` or `operator<<` shows that address, which differs
from run to run under address-space randomization, so don't put it in expected output.

:::warning[The `*` binds to the name, not the type]
`int* a, b;` declares `a` as `int*` and `b` as plain `int`. Declare one pointer per statement.
:::

## Null and `nullptr`

A **null pointer** is a pointer that is guaranteed not to point to any object or function. The null
pointer literal is `nullptr` *(C++11)*, of type `std::nullptr_t`, which converts implicitly to every
pointer type and to nothing else. It replaces `0` and `NULL`, which are integers and therefore pick
the wrong overload:

```cpp title="nullptr.cpp" showLineNumbers
#include <cstdio>

void f(int)   { std::puts("f(int)"); }
void f(char*) { std::puts("f(char*)"); }

int main() {
    f(0);          // calls f(int): 0 is an int
    f(nullptr);    // calls f(char*)
    int* p = nullptr;
    if (!p) std::puts("p is null");   // a pointer converts to bool: false iff null
}
```

```text
f(int)
f(char*)
p is null
```

`NULL` is an implementation-defined null pointer constant, in practice an integer such as `0` or `0L` (GCC defines it as `__null`), so it takes part in overload resolution as an integer. Prefer `nullptr` everywhere.

Dereferencing a null pointer is **undefined behavior**. On mainstream hosted systems it usually
ends in a segmentation fault because the OS leaves page zero unmapped, but that is a platform
habit, not a guarantee: the optimizer may assume the pointer is non-null from the moment you
dereference it, and delete a later null check.

An **uninitialized** pointer is worse than a null one: it holds an indeterminate value, and merely
reading it is undefined behavior *(until C++26, which makes it erroneous behavior; the value is still
unspecified)*. Initialize every pointer, to `nullptr` if nothing better is available.

## Pointers and arrays

An array of `T` converts implicitly to a `T*` pointing at its first element (**array-to-pointer
conversion**, informally "decay") in nearly every expression. The conversion is why `arr` works where
a pointer is expected, and also why a function can never receive an array by value: a parameter
declared `int a[5]` is adjusted to `int* a`, and the size is lost.

```cpp title="decay.cpp" showLineNumbers
#include <cstdio>

int sum(const int* a, std::size_t n) {          // `const int a[]` means the same thing
    int s = 0;
    for (std::size_t i = 0; i < n; ++i) s += a[i];
    return s;
}

int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int* p = arr;                                // decays: p == &arr[0]

    static_assert(sizeof(arr) == 5 * sizeof(int));   // sizeof sees the array...
    static_assert(sizeof(p) == sizeof(void*));       // ...but not through the pointer

    std::printf("%d\n", sum(arr, 5));
    // arr = p;                                  // error: an array is not assignable
    p = arr + 1;                                 // a pointer is
    std::printf("%d\n", *p);
}
```

```text
15
2
```

The conversion does not happen under `sizeof`, `&arr` (which has type `int (*)[5]`, a pointer to the
whole array), `decltype`, and when binding to a reference to array. Moving a pointer along the
array is the subject of [pointer arithmetic](./pointer-arithmetic.md), and `std::span` *(C++20)* is
the modern way to pass a pointer and a length together.

## Ownership: the question a pointer cannot answer

Nothing in the type `T*` records whether the code holding it must `delete` the target. A function
that takes `Widget*` might merely look at the widget, take ownership, or stash the pointer for
later. The convention in modern C++ is to make the owner explicit and leave raw pointers for the
**non-owning** case:

| Role | Spelling |
|---|---|
| Sole owner | [`std::unique_ptr<T>`](./unique-ptr.md) (or a value member) |
| Shared owner | [`std::shared_ptr<T>`](./shared-ptr.md) |
| Observes, may be absent | `T*` |
| Observes, never absent | `T&` ([reference](./references.md)) |
| Observes a shared object without owning it | [`std::weak_ptr<T>`](./weak-ptr.md) |

A raw `T*` that is the only owner needs a matching `delete` on every path out of the scope,
including exceptions. How `new`, `delete` and `delete[]` pair up is on
[new and delete](../05-memory-and-object-lifetime/new-and-delete.md), and the pattern that makes
the cleanup automatic is [RAII](../13-idioms-and-design/01-raii.md).

## Dangling pointers

A pointer is **dangling** when its target's lifetime has ended: the object was destroyed, its
storage freed, or its scope exited. The pointer itself is untouched, which is exactly what makes the
bug quiet. Dereferencing a dangling pointer is undefined behavior, and since C++ treats the *value*
of such a pointer as **invalid**, even copying or comparing it is only implementation-defined.

Three common sources:

```cpp title="dangling.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <vector>

int* from_local() {
    int x = 42;
    return &x;                       // x dies when the function returns
}

int main() {
    // 1. Pointer to a returned local (GCC and Clang warn about this one).
    int* a = from_local();
    (void)a;                         // using *a here would be undefined behavior

    // 2. Pointer into a container that reallocates.
    std::vector<int> v{1, 2, 3};
    int* first = &v[0];
    v.push_back(4);                  // may reallocate: `first` may now dangle
    (void)first;                     // do not dereference it

    // 3. Pointer to a temporary's buffer.
    const char* s = std::string("temporary").c_str();   // string destroyed at the semicolon
    (void)s;
    std::puts("none of the pointers above was dereferenced");
}
```

Setting a pointer to `nullptr` after `delete` does not fix the general problem, because every *other*
copy of the pointer still dangles. The fix is structural: give the object a single clear owner
([RAII](../13-idioms-and-design/01-raii.md)), keep pointers shorter-lived than their targets, and
use `weak_ptr` where a non-owner must detect that the target is gone. AddressSanitizer
(`-fsanitize=address`) reports use-after-free and use-after-scope at run time.

## `void*`

Any pointer to an object type converts implicitly to `void*`, which erases the type. A `void*`
cannot be dereferenced or incremented. Getting a typed pointer back needs an explicit
`static_cast` to the **original** type (any other type is a strict-aliasing problem, see
[strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md)). It survives mainly in C
APIs and callback "user data" arguments; templates, `std::any` and
[type erasure](../13-idioms-and-design/06-type-erasure.md) are the typed replacements.

```cpp title="void-ptr.cpp" showLineNumbers
#include <cstdio>

struct Counter { int n = 0; };

// A C-style callback API: the library stores and returns an opaque void*.
void call_twice(void (*cb)(void*), void* user) { cb(user); cb(user); }

void bump(void* user) { ++static_cast<Counter*>(user)->n; }   // back to the original type

int main() {
    Counter c;
    call_twice(bump, &c);             // &c converts to void* implicitly
    std::printf("%d\n", c.n);
}
```

```text
2
```

Pointers to `const` objects need `const void*`; going back needs `static_cast<const T*>`. Casting
away `const` is covered on [const and pointers](./const-and-pointers.md).

## Function pointers

A function name converts to a pointer to that function, and calling through the pointer is the same
as calling the function. The declarator syntax is awkward (the `*` and the name sit inside
parentheses), so name the type with `using`:

```cpp title="func-ptr.cpp" showLineNumbers
#include <cstdio>
#include <functional>

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

using BinOp = int (*)(int, int);       // pointer to function (int, int) -> int

int apply(BinOp op, int a, int b) { return op(a, b); }

int main() {
    BinOp op = add;                    // same as &add
    std::printf("%d\n", op(5, 3));
    op = sub;
    std::printf("%d\n", apply(op, 5, 3));

    int offset = 10;
    std::function<int(int)> f = [offset](int v) { return v + offset; };   // captures state
    std::printf("%d\n", f(1));

    // BinOp bad = [offset](int a, int b) { return a + b + offset; };     // error: capturing
}
```

```text
8
2
11
```

A plain function pointer is one machine pointer and cannot carry state. Only a *captureless* lambda
converts to one. For callables with state use a template parameter (no overhead, and the call can be
inlined), or `std::function` when the type must be erased (a heap allocation is possible, and the
call is an indirect one). Function pointers do not convert to `void*` in standard C++; POSIX
`dlsym` relies on a conditionally-supported conversion. Calls through function pointers are also what
a [virtual call](../07-classes-and-oop/virtual-functions.md) boils down to, minus the table lookup.

## Pitfalls

- **Dereferencing before checking.** The check must come first, and the optimizer is allowed to
  treat the dereference as proof that the pointer was non-null.
- **`delete` on the wrong form.** `new[]` pairs with `delete[]`. See
  [new and delete](../05-memory-and-object-lifetime/new-and-delete.md).
- **Comparing unrelated pointers with `<`.** `==` and `!=` work on any two pointers of compatible
  type. Built-in `<` on pointers into different arrays or objects is unspecified; `std::less`
  gives a total order for those cases.
- **Treating `T*` as an array handle.** A pointer does not know its length. Pass a size or a
  `std::span`.
- **Two owners.** Two raw pointers that both `delete` the same object is a double free.

## Key points

- A pointer holds an address and nothing else: no lifetime, no length, no ownership.
- Use `nullptr`, initialize every pointer, never dereference null or dangling values.
- A raw `T*` in modern code means "non-owning, may be null". Ownership belongs in `unique_ptr` or
  `shared_ptr`.
- Arrays decay to pointers; `void*` and function pointers are the type-erased and callback forms.

## Related

- [Pointer arithmetic](./pointer-arithmetic.md): moving a pointer through an array and where the legal range ends.
- [const and pointers](./const-and-pointers.md): pointer-to-const versus const pointer.
- [References](./references.md): the non-null, non-reseatable alternative.
- [new and delete](../05-memory-and-object-lifetime/new-and-delete.md): the raw allocation that smart pointers wrap.
