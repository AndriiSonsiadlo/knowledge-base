---
id: default-initialization
title: Default Initialization
sidebar_label: Default Initialization
sidebar_position: 1
tags: [c++, initialization, default-init, indeterminate-value, constructors]
---

# Default Initialization

**Default initialization** is what happens when an object is created with **no initializer at all**:
`T x;`, `new T`, or a member or base missing from a constructor's member-initializer list. The rule splits sharply by type. A class type runs its **default
constructor**. A non-class type, such as `int`, a pointer or an array of them, is left with an
**indeterminate value**, whatever bytes were in that storage before. This page owns that rule. The
other three pages cover the forms that avoid it: [value](./value-initialization.md),
[aggregate](./aggregate-initialization.md) and [list](./uniform-initialization.md) initialization.

**Prerequisites:** [Storage duration](../storage-duration.md) (automatic versus static objects),
[object lifetime](../object-lifetime.md).

Constructors, member-initializer lists and the order members are initialized in belong to
[constructors and destructors](../../07-classes-and-oop/constructors-and-destructors.md). This page
only covers what happens when they are *absent*.

## The rule

| `T` is | `T x;` does |
|---|---|
| Class type | Overload resolution picks a default constructor and calls it. If there is none, or it is deleted or inaccessible, the program is ill-formed. |
| Array | Default-initializes each element in order. |
| Anything else (`int`, `double`, pointer, enum) | Nothing. The object has an indeterminate value. |

Static and thread storage duration objects are the exception to the last row. They are
**zero-initialized** before anything else happens, so `static int n;` is `0`. That is covered in
[Storage duration](../storage-duration.md), and the zero-initialization step itself is described in
[value initialization](./value-initialization.md#zero-initialization).

## Indeterminate values

```cpp title="indeterminate.cpp" showLineNumbers
#include <iostream>

int global;                        // static storage: zero-initialized

int main() {
    static int local_static;       // also zero-initialized
    int automatic;                 // default-initialized: indeterminate
    int* p = new int;              // same, on the heap
    *p = 5;                        // assign before the first read

    automatic = 7;
    std::cout << global << ' ' << local_static << ' ' << automatic << ' ' << *p << '\n';
    delete p;
}
```

```text
0 0 7 5
```

Reading `automatic` or `*p` *before* the assignments would be **undefined behavior**: the compiler
may fold the read to any value, drop the code that depends on it, or keep whatever bytes happen to be
there, and the result can differ between `-O0` and `-O2`. Do not rely on any observed value. That is
why this page prints none.

:::info[C++26: erroneous behavior]
C++26 (P2795R5) changes the rule for automatic variables: reading one that was not initialized is no
longer plain undefined behavior but **erroneous behavior**. The implementation gives the bytes a
fixed value of its choosing and may diagnose the read. `[[indeterminate]]` opts a variable
out. Until your compiler implements it, treat every uninitialized read as undefined behavior.
:::

Tools that find these reads: `-Wall -Wextra` (`-Wuninitialized`, `-Wmaybe-uninitialized`, which
need `-O1` or higher to see through control flow), MemorySanitizer (`clang++ -fsanitize=memory`),
and Valgrind. GCC and Clang can also zero or pattern-fill automatic variables on request
(`-ftrivial-auto-var-init=zero|pattern`), which hides the bug rather than fixing it.

## Class types

For a class, "default-initialized" means "the default constructor runs". Which constructor that is
depends on how the class is written.

```cpp title="class-default.cpp" showLineNumbers
#include <iostream>
#include <string>

struct Logger {
    Logger() { std::cout << "Logger()\n"; }
};

struct Widget {
    Logger log;                 // class member: its default constructor runs
    std::string name;           // class member: empty string
    int id;                     // fundamental member: indeterminate
    int count = 0;              // default member initializer (C++11): used
    Widget() {}                 // user-provided; does not mention id
};

int main() {
    Widget w;                   // default-initialization
    std::cout << '[' << w.name << "] " << w.count << '\n';
    // reading w.id here would be undefined behavior
}
```

```text
Logger()
[] 0
```

Even with `Widget() {}` writing nothing, the members of class type are default-initialized and
members with a default member initializer use it. Only `id`, a fundamental type with neither, is
left indeterminate. A default member initializer is the cheapest way to close this hole for every
constructor at once.

### Implicitly declared default constructor

If a class declares no constructors, the compiler declares a default one. It default-initializes every
base and member, which means it initializes **nothing** for fundamental members:

```cpp title="implicit.cpp" showLineNumbers
#include <iostream>
#include <string>

struct Point { int x; int y; };                 // x, y indeterminate under T p;
struct Named { std::string s; int n = 3; };     // s is empty, n is 3

int main() {
    Named n;
    std::cout << '[' << n.s << "] " << n.n << '\n';
    Point p;                                     // legal, but p.x and p.y are not usable yet
    p.x = 1; p.y = 2;
    std::cout << p.x + p.y << '\n';
}
```

```text
[] 3
3
```

### No usable default constructor

```cpp title="no-default.cpp (fragment, does not compile)"
struct NeedsArg { explicit NeedsArg(int); };

NeedsArg a;            // error: no default constructor
struct S { NeedsArg m; };
S s;                   // error: S's implicit default constructor is deleted
```

A class gets an implicitly **deleted** default constructor when a member or base cannot be
default-initialized: a reference member without a default member initializer, a `const` member
without one whose type is not itself const-default-constructible (a `const std::string` member is
fine), a variant member in some cases, or a member or base type that itself has no usable default constructor. Declaring any
constructor also suppresses the implicit one, so adding `Foo(int)` to a class makes `Foo f;` an error
unless you also write `Foo() = default;`.

### `const` objects

A `const` object must be initialized, and default-initializing it is only allowed when the type is
**const-default-constructible**: a class whose every member and base class has a default member initializer or is
itself const-default-constructible (C++17, CWG 253), or a class with a user-provided default
constructor.

```cpp title="const-default.cpp" showLineNumbers
struct Empty {};
struct Initialized { int v = 1; };
struct Raw { int v; };

const Empty e;          // OK since C++17: nothing to leave uninitialized
const Initialized i;    // OK: v has a default member initializer
// const Raw r;         // error: Raw has an uninitialized member
// const int k;         // error: no initializer for a const scalar

int main() {}
```

## Arrays

```cpp title="arrays.cpp" showLineNumbers
#include <iostream>

struct Counter {
    static inline int made = 0;
    Counter() { ++made; }
};

int main() {
    Counter cs[3];                  // default constructor runs three times
    int ints[3];                    // three indeterminate ints
    ints[0] = ints[1] = ints[2] = 0;
    std::cout << Counter::made << ' ' << ints[0] + ints[1] + ints[2] << '\n';
}
```

```text
3 0
```

An array with a partial initializer list, `int a[5] = {1, 2}`, is *not* default-initialized. The
remaining elements are value-initialized, so they are `0`. That form is covered in
[aggregate initialization](./aggregate-initialization.md).

## Avoiding default initialization of scalars

Default initialization is the right choice in exactly one case: you are about to overwrite the
storage and the zeroing cost matters (a large buffer filled by `read()`, for example). Everywhere
else, initialize.

| Want | Write | Page |
|---|---|---|
| Zero / empty / default value | `int n{};` or `int n = 0;` | [value](./value-initialization.md) |
| A specific value | `int n{42};` | [list](./uniform-initialization.md) |
| A dynamic array of zeroes | `new int[n]()` or `std::make_unique<int[]>(n)` | [value](./value-initialization.md) |
| A dynamic array you will fill yourself | `new int[n]` or `std::make_unique_for_overwrite<int[]>(n)` (C++20) | this page |
| Members that are never indeterminate | default member initializers: `int id = 0;` | this page |

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `int sum; for (...) sum += x;` | Reads an indeterminate value on the first iteration | `int sum = 0;` |
| Assuming `new int[n]` is zeroed because the global `int a[n]` was | Static storage is zeroed. Heap and stack storage are not. | `new int[n]()` |
| `Widget w();` meant as default initialization | Declares a function (the most vexing parse), not an object | `Widget w;` or `Widget w{};` |
| Relying on a user-provided constructor to "zero things" | Members it does not mention are still default-initialized | Default member initializers |
| Copying a struct with an indeterminate member | The copy reads it | Initialize first |

## Key points

- No initializer means default initialization: a class runs its default constructor, everything else
  stays indeterminate.
- Static and thread storage objects are zeroed first. Automatic and dynamic ones are not.
- Reading an indeterminate value is undefined behavior (erroneous behavior for automatic variables in C++26, still a bug).
- A class with no usable default constructor cannot be default-initialized, and a `const` object can
  be only if every member is initialized by something.
- Default member initializers remove the indeterminate-member problem for every constructor at once.
