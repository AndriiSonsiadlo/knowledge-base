---
id: value-initialization
title: Value Initialization
sidebar_label: Value Initialization
sidebar_position: 2
tags: [c++, initialization, value-init, zero-initialization]
---

# Value Initialization

**Value initialization** is what you get when you ask for an object with an **empty initializer**:
`T()`, `T{}`, `T x{};`, `new T()`, or a member named in a member-initializer list with `()` or `{}`.
It is the "give me a sensible, fully defined object" form. Where
[default initialization](./default-initialization.md) can leave a scalar indeterminate, value
initialization always ends with a defined value: zero for scalars, and a constructor call for classes.

**Prerequisites:** [Default initialization](./default-initialization.md),
[storage duration](../storage-duration.md).

## The rules

What value initialization does depends on the type, in this order. The rules took their current
shape with CWG 1301 and 1368 (C++14), and the aggregate case of `T{}` with CWG 1467:

| `T` is | Effect |
|---|---|
| Class with no default constructor, or a **user-provided** or **deleted** one | [Default-initialize](./default-initialization.md): call it, or ill-formed if there is none or it is deleted. No zeroing first. For `T{}` the braced-list rules apply first, see [uniform initialization](./uniform-initialization.md). |
| Class with an implicit, defaulted, or `= default` on first declaration default constructor, no user-provided one | **Zero-initialize** the object, then, if the default constructor is non-trivial, call it. |
| Array | Value-initialize each element. |
| Anything else (`int`, pointer, enum, `double`) | **Zero-initialize.** |

Two details are easy to miss. A constructor is *user-provided* if it is not defaulted or deleted on
its first declaration, so `T() = default;` inside the class is **not** user-provided, but
`T();` declared in the class and defined as `T::T() = default;` outside it **is**. And with
`T{}`, an aggregate (see [aggregate initialization](./aggregate-initialization.md)) is
aggregate-initialized and every member then gets its default member initializer or is
value-initialized, which gives the same effect for ordinary structs.

## Zero-initialization

Zero-initialization is a *step*, not a syntax you can write. It sets an object to the zero value of
its type:

- scalars: the integer `0`, `0.0`, a null pointer, or the value `0` converted to an enum type;
- classes: every non-static member and base subobject zero-initialized, and **padding bits set to zero**;
- unions: the first non-static named member (and padding bits);
- arrays: every element.

It happens in two situations. [Static and thread storage](../storage-duration.md) objects get it
before any other initialization, which is why `static int n;` reads as `0`. And value initialization
performs it explicitly, as the table above shows. You cannot request zero-initialization of an
automatic object on its own: `int x{};` and `int x = 0;` both do it via value initialization or
copy-initialization from `0`.

## Scalars

```cpp title="scalars.cpp" showLineNumbers
#include <iostream>

int main() {
    int a{};                // value-init: 0
    int b = int();          // value-init: 0
    double d{};             // 0.0
    int* p{};               // nullptr
    bool flag{};            // false
    char buf[4]{};          // each element 0

    std::cout << a << ' ' << b << ' ' << d << ' ' << (p == nullptr) << ' ' << flag
              << ' ' << int(buf[0]) + int(buf[3]) << '\n';
}
```

```text
0 0 0 1 0 0
```

Compare `int a;`, which is indeterminate, with `int a{};`, which is `0`. For one variable that costs
one store, and it removes a whole class of bugs.

## Classes: it depends on the constructor

The third row of the table is the interesting one, because the *same* member can come out defined or
indeterminate depending on how the default constructor is declared:

```cpp title="class-value.cpp" showLineNumbers
#include <iostream>

struct Implicit { int x; };               // implicit default constructor
struct Defaulted { Defaulted() = default; int x; };   // defaulted on first declaration
struct UserProvided { UserProvided() {} int x; };     // user-provided, does not touch x

int main() {
    Implicit    a{};         // aggregate: x value-initialized -> 0
    Implicit    b = Implicit();   // zero-initialized, then trivial ctor: x == 0
    Defaulted   c{};         // zero-initialized first: x == 0
    UserProvided u1{};       // calls the constructor only: x is indeterminate
    UserProvided u2 = UserProvided();   // same

    std::cout << a.x << ' ' << b.x << ' ' << c.x << '\n';
    (void)u1; (void)u2;      // reading u1.x or u2.x would be undefined behavior
}
```

```text
0 0 0
```

The practical rule: with `T()` or `T{}`, a class that relies on the compiler-generated constructor
gets zeroed first. A class with a hand-written default constructor gets **only** what that
constructor does. If you write the constructor, initialize every scalar member in it, or give the
members default member initializers.

:::note[C++20]
Since C++20 a class with *any* user-declared constructor (including `= default` and `= delete`) is
not an aggregate, so `Defaulted{}` above value-initializes via the rule in the table. Before C++20
`Defaulted{}` was aggregate initialization, which also produced `x == 0`. The result is the same for
this example, but the path differs and matters for classes with `= delete`d constructors.
:::

## Arrays and members

```cpp title="members.cpp" showLineNumbers
#include <iostream>
#include <string>

struct Config {
    int retries;
    double timeout;
    std::string name;
};

struct Holder {
    int n;
    std::string s;
    Holder() : n(), s() {}          // n() value-initializes: 0
};

int main() {
    Config c{};                     // all members value-initialized
    int arr[3]{};                   // {0, 0, 0}
    Holder h;
    std::cout << c.retries << ' ' << c.timeout << " [" << c.name << "] "
              << arr[2] << ' ' << h.n << '\n';
}
```

```text
0 0 [] 0 0
```

In a member-initializer list, `n()` or `n{}` value-initializes `n`; leaving `n` out of the list would
default-initialize it. See
[constructors and destructors](../../07-classes-and-oop/constructors-and-destructors.md) for the list
itself.

## Dynamic allocation

```cpp title="dynamic.cpp" showLineNumbers
#include <iostream>
#include <memory>
#include <vector>

int main() {
    int* a = new int();             // 0
    int* b = new int{};             // 0
    int* arr = new int[4]();        // four zeros
    auto up = std::make_unique<int[]>(4);   // value-initializes: zeros
    std::vector<int> v(4);          // elements value-initialized: zeros

    std::cout << *a << *b << arr[3] << up[3] << v[3] << '\n';
    delete a; delete b; delete[] arr;
}
```

```text
00000
```

`new int` (no parentheses) is default initialization and leaves the value indeterminate. The
difference of two characters is the most common source of "works in debug, garbage in release" bugs
with heap scalars. `std::make_unique<int[]>(n)` and `std::vector<int>(n)` both zero for you. The
`new` expression itself is covered in [new and delete](../new-and-delete.md).

## Cost

Zeroing is one store per scalar, or a `memset` for arrays, and for a small object it is usually
free. For a large buffer that you are about to overwrite, it is wasted work: use
`std::make_unique_for_overwrite<T[]>(n)` *(C++20)* or `new T[n]` deliberately, and write the intent
in a comment.

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `T x();` | Declares a function returning `T` (most vexing parse) | `T x{};` or `T x;` |
| `new int` where you meant `new int()` | Indeterminate, not zero | `new int()` or `new int{}` |
| Expecting `T{}` to zero a class with a user-provided default constructor | Only the constructor runs | Initialize members in the constructor or with default member initializers |
| Relying on zeroed padding bytes after `T{}` | Copies of the object and compiler optimizations are free to change padding | Do not compare objects with `memcmp` |

## Key points

- An empty initializer (`()` or `{}`) value-initializes: scalars become zero, arrays go element by
  element, and classes depend on their default constructor.
- Zero-initialization is the step that sets everything to zero. Static storage gets it automatically,
  and value initialization does it for classes without a user-provided default constructor.
- A user-provided default constructor is the only thing that runs for such a class. Members it ignores
  stay indeterminate.
- `new T()` and `new T{}` are value-initialized. `new T` is not.
