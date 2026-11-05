---
id: aggregate-initialization
title: Aggregate Initialization
sidebar_label: Aggregate Initialization
sidebar_position: 3
tags: [c++, initialization, aggregate, designated-initializers, c++20]
---

# Aggregate Initialization

An **aggregate** is a plain bundle of data, an array or a simple class, that you can fill by listing
its elements in braces: `Point p{1, 2};`. No constructor is involved. The initializer list is matched
to the elements in order, and anything you leave out is value-initialized. This page owns what counts
as an aggregate, how the elements are matched, **designated initializers** *(C++20)* and
**parenthesized aggregate initialization** *(C++20)*. How braces behave in general (narrowing,
`std::initializer_list` preference) is in [uniform initialization](./uniform-initialization.md).

**Prerequisites:** [Default initialization](./default-initialization.md),
[value initialization](./value-initialization.md).

## What is an aggregate

| Type | Aggregate if (C++20) |
|---|---|
| Array | Always (arrays of any element type) |
| Class (`struct`, `class`, `union`) | No user-declared or inherited constructors, no `explicit` constructors, no private or protected direct non-static data members, no virtual functions, no virtual, private or protected base classes |

The constructor condition changed over time, and old tutorials disagree:

| Standard | Constructors in an aggregate |
|---|---|
| C++11 | None user-provided |
| C++17 | None user-provided, `explicit`, or inherited. Public non-virtual **base classes allowed**. |
| C++20 | **None user-declared**. `Foo() = default;` and `Foo() = delete;` now make a class a non-aggregate. |

Default member initializers are allowed since C++14. Reference members must get an initializer
(explicit or a default member initializer). An omitted `const` member is value-initialized.

```cpp title="is-aggregate.cpp" showLineNumbers
#include <string>
#include <type_traits>

struct Point { int x; int y; };                          // aggregate
struct Person { std::string name; int age; };            // aggregate: members may be class types
struct WithCtor { WithCtor(int); int v; };               // not: user-declared constructor
struct WithDefault { WithDefault() = default; int v; };  // not since C++20
struct Priv { int a; private: int b; };                  // not: private member
struct Virt { virtual void f(); int v; };                // not: virtual function
struct Derived : Point { int z; };                       // aggregate since C++17 (public base)

static_assert(std::is_aggregate_v<Point>);
static_assert(std::is_aggregate_v<Person>);
static_assert(!std::is_aggregate_v<WithCtor>);
static_assert(!std::is_aggregate_v<WithDefault>);
static_assert(!std::is_aggregate_v<Priv>);
static_assert(!std::is_aggregate_v<Virt>);
static_assert(std::is_aggregate_v<Derived>);
static_assert(std::is_aggregate_v<int[3]>);

int main() {}
```

`std::is_aggregate` *(C++17, `<type_traits>`)* tests it.

## How the list is matched

Elements are initialized **in declaration order** (base classes first, then members, or array
indices ascending), each copy-initialized from the corresponding initializer clause. Remaining
elements get their default member initializer if they have one, otherwise they are
copy-initialized from an empty list, which value-initializes them (so scalars become `0`). More
initializers than elements is an error.

```cpp title="basic.cpp" showLineNumbers
#include <iostream>
#include <string>

struct Point { int x; int y; };
struct Line { Point a; Point b; };
struct Person { std::string name; int age = 18; };

int main() {
    int arr[5] = {1, 2};                // {1, 2, 0, 0, 0}
    int auto_sized[] = {4, 5, 6};       // size deduced: 3
    Point p{3};                         // y value-initialized: 0
    Line l{{0, 0}, {5, 7}};             // nested braces
    Line l2{0, 0, 5, 7};                // brace elision: same object, works but is harder to read
    Person who{"Ada"};                  // age takes its default member initializer: 18

    std::cout << arr[4] << ' ' << sizeof(auto_sized) / sizeof(int) << ' '
              << p.x << p.y << ' ' << l.b.y << l2.b.y << ' ' << who.name << who.age << '\n';
}
```

```text
0 3 30 77 Ada18
```

Writing the inner braces is clearer than relying on **brace elision**, and both GCC and Clang can warn about
it with `-Wmissing-braces` (Clang 21 includes it in `-Wall`; GCC needs it enabled explicitly). Leaving
elements out also triggers `-Wmissing-field-initializers` under `-Wextra`, though the result is
well-defined.

`= {}` and `{}` on an aggregate zero everything that has no default member initializer, which makes
`Point p{};` the usual way to get a zeroed struct.

### Narrowing still applies

Aggregate initialization is a form of list-initialization, so narrowing conversions in the element
initializers are errors:
`Point p{1.5, 2};` does not compile. The rule is explained in
[uniform initialization](./uniform-initialization.md#narrowing).

## Designated initializers (C++20)

C++20 lets you name the members. Names must appear **in declaration order**, and for each one you
may use `= value` or `{...}`:

```cpp title="designated.cpp" showLineNumbers
#include <iostream>

struct Options {
    bool verbose = false;
    int level = 1;
    const char* name = "default";
};

struct Pair { int a; int b; };

int main() {
    Options o{.verbose = true, .name = "run"};     // level keeps its default of 1
    Pair p{.a = 1};                                 // b value-initialized: 0
    // Options bad{.level = 2, .verbose = true};    // error: out of declaration order (C++ only)

    std::cout << o.verbose << o.level << ' ' << o.name << ' ' << p.a << p.b << '\n';
}
```

```text
11 run 10
```

Compared with C99, the C++20 version is stricter: **no reordering, no skipping around, no mixing**
designated and positional initializers in one list, no array designators (`[2] = 5`), and no
nested designators (`.a.b = 1`: write `.a = {.b = 1}`). Designated initializers are valid only for
aggregates. GCC and Clang accept them in earlier language modes as an extension (with
`-Wpedantic` warnings).

## Parenthesized aggregate initialization (C++20)

*(C++20, P0960)* `T(1, 2)` now works for an aggregate when no constructor matches, which lets
`std::make_unique<Point>(1, 2)` and `emplace_back(1, 2)` build aggregates:

```cpp title="paren.cpp" showLineNumbers
#include <iostream>
#include <memory>
#include <vector>

struct Point { int x; int y; };

int main() {
    Point p(1, 2);                          // C++20: aggregate init via parentheses
    auto up = std::make_unique<Point>(3, 4);
    std::vector<Point> v;
    v.emplace_back(5, 6);
    std::cout << p.x << p.y << up->x << up->y << v[0].x << v[0].y << '\n';
}
```

```text
123456
```

Differences from the braced form: narrowing conversions are **allowed** (a warning at most), brace
elision is not performed, and a temporary bound to a reference member dangles at the end of the
full-expression (the lifetime extension that braces give does not apply). In C++17 and earlier this
code does not compile.

## Arrays, and `std::array`

A built-in array is initialized as shown. `std::array<T, N>` is a class that wraps one, and since it
is an aggregate with a single array member, it takes the same list (brace elision makes the single
set of braces work):

```cpp title="stdarray.cpp" showLineNumbers
#include <array>
#include <iostream>

int main() {
    std::array<int, 3> a{1, 2, 3};
    std::array b{4, 5, 6};          // C++17 CTAD: std::array<int, 3>
    std::array<int, 4> c{};         // all zero
    std::cout << a[2] << b[2] << c[3] << '\n';
}
```

```text
360
```

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| Adding a constructor to a struct and keeping `S{1, 2}` | It is no longer an aggregate, so `S{1, 2}` looks for a constructor | Add the matching constructor, or leave the struct a plain aggregate |
| Adding `S() = default;` to an aggregate in C++20 | The class stops being an aggregate | Remove it. Default member initializers already cover it. |
| Adding or reordering a member | Positional `S{1, 2}` silently re-targets the other members | Use designated initializers, or add new members at the end |
| Designators out of order, or `.a.b = 1` | Valid in C99, ill-formed in C++20 | Declaration order, `.a = {.b = 1}` |
| `Point p(1.5, 2)` expecting an error | Parenthesized form permits narrowing | Use braces |

## Key points

- Aggregates are arrays and simple classes without user-declared constructors, private data, virtual
  functions or virtual bases. The definition tightened in C++20.
- Elements are initialized in order. Missing ones use their default member initializer or are
  value-initialized.
- Designated initializers *(C++20)* must be in declaration order, with no mixing and no nesting
  shorthand.
- Parenthesized aggregate initialization *(C++20)* makes `T(a, b)` and `make_unique<T>(a, b)` work
  for aggregates, but allows narrowing.
- `std::is_aggregate_v<T>` *(C++17)* checks the property.
