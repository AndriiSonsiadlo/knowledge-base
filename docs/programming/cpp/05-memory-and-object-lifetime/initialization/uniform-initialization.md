---
id: uniform-initialization
title: Uniform Initialization
sidebar_label: Uniform Initialization
sidebar_position: 4
tags: [c++, initialization, brace-init, list-initialization, narrowing, initializer-list]
---

# Uniform Initialization

C++11 added **list initialization**: initializing with a braced list, `T x{args}` or `T x = {args}`.
It was marketed as "uniform" because the same syntax works for scalars, aggregates, containers and
classes with constructors. The syntax is uniform, the semantics are not: braces pick *different
initialization forms* depending on the type, and they carry two special rules, a **ban on narrowing
conversions** and a strong **preference for `std::initializer_list` constructors**. This page owns
those rules. The forms braces dispatch to are on the other pages of this section.

**Prerequisites:** [Default](./default-initialization.md), [value](./value-initialization.md) and
[aggregate](./aggregate-initialization.md) initialization.

## What braces do

For `T x{...}` the compiler picks the first row that applies (C++20 wording, simplified). Before CWG 1467 (C++14) the empty-list row came first, so `T{}` on an
aggregate value-initialized it:

| Condition | Result |
|---|---|
| `T` is an aggregate and the list is one element of the same or derived type | Copy/initialize from that element (CWG 1467) |
| `T` is an aggregate | [Aggregate initialization](./aggregate-initialization.md) (this also covers `T{}`) |
| Empty braces and `T` has a default constructor | [Value-initialization](./value-initialization.md) |
| `T` has `std::initializer_list` constructors | Try those first, with the whole list as one argument |
| Otherwise, `T` is a class | Overload resolution over all constructors with the list elements as arguments |
| `T` is a scalar with one element | Initialize from it, but narrowing is an error |
| `T` is an enumeration with a fixed underlying type, one integer element *(C++17)* | Initialize the enum from it, if not narrowing |
| `T` is a scalar with an empty list | Value-initialization: zero |

Direct-list-initialization is `T x{...}`, copy-list-initialization is `T x = {...}`. They differ only
in that copy-list-initialization is ill-formed if the selected constructor is `explicit`.

## Narrowing is an error \{#narrowing\}

A **narrowing conversion** is an implicit conversion that can lose information. Inside braces it is
ill-formed, where parentheses and `=` accept it silently:

```cpp title="narrowing.cpp" showLineNumbers
#include <iostream>

int main() {
    double d = 3.9;
    int a = d;              // OK: truncates to 3, silently
    int b(d);               // OK: same
    // int c{d};            // error: narrowing double -> int
    int e{static_cast<int>(d)};   // explicit cast: OK

    constexpr int big = 300;
    char ok{65};            // OK: constant that fits in char
    // char no{big};        // error: 300 does not fit in char
    float f{1};             // OK: int constant 1 fits float exactly

    std::cout << a << b << e << ' ' << int(ok) << ' ' << f << '\n';
}
```

```text
333 65 1
```

The cases that count as narrowing: floating to integer; `long double` to `double` or `float`, or
`double` to `float`, unless the source is a constant that fits (in range, even if inexact); integer
to floating type unless a constant that is exactly representable; integer to a narrower integer, or
signed/unsigned change, unless a constant that fits; an unscoped enumeration to an integer type that
cannot hold all its values; and, since C++20 (P1957), a pointer or pointer-to-member to `bool`. The
list is simplified. Compilers may report it only as a warning
(GCC does for non-constants, with `-Wnarrowing`), but the standard requires a diagnostic and Clang
makes it an error. Treat it as an error.

## Braces and `std::initializer_list`

If a class has a constructor taking `std::initializer_list<E>` as its first parameter, braces try it
**first**, before any other constructor, even when another constructor would be a better match:

```cpp title="init-list.cpp" showLineNumbers
#include <initializer_list>
#include <iostream>
#include <vector>

struct Widget {
    Widget(int, int)                       { std::cout << "Widget(int, int)\n"; }
    Widget(std::initializer_list<int>)     { std::cout << "Widget(initializer_list)\n"; }
};

struct Plain {
    Plain(int, int) { std::cout << "Plain(int, int)\n"; }
};

int main() {
    Widget a(1, 2);                 // parentheses: constructor (int, int)
    Widget b{1, 2};                 // braces: initializer_list wins
    Widget c = {1, 2};              // same
    Plain  d{1, 2};                 // no initializer_list ctor: ordinary overload resolution

    std::vector<int> v1(3, 7);      // 3 elements, all 7
    std::vector<int> v2{3, 7};      // 2 elements: 3 and 7
    std::cout << v1.size() << v2.size() << '\n';
}
```

```text
Widget(int, int)
Widget(initializer_list)
Widget(initializer_list)
Plain(int, int)
32
```

The preference is strong. If the `initializer_list` constructor is viable at all, even after a
conversion, it wins. If it is viable only through a narrowing conversion, the program is ill-formed
rather than falling back to another constructor. Only when no `initializer_list` constructor is
viable at all does overload resolution continue with the others.

Empty braces are the exception: `Widget e{};` calls the **default constructor**, not an
`initializer_list` one with zero elements.

The practical consequence is for library types: `std::vector<int>{3, 7}` and
`std::vector<int>(3, 7)` build different things. Use parentheses when you mean "size, value".

## What the braces buy you

**Containers.** Braces are how you give a standard container its elements:

```cpp title="containers.cpp" showLineNumbers
#include <iostream>
#include <map>
#include <string>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    std::map<std::string, int> m{{"a", 1}, {"b", 2}};
    std::cout << v.size() << m.size() << m.at("b") << '\n';
}
```

```text
322
```

**The most vexing parse** (canonical home: [function declarations](../../04-functions-and-call-mechanics/function-declarations.md)). `Widget w();` declares a function. `Widget w{};` cannot be read that way,
and it also value-initializes:

```cpp title="vexing.cpp" showLineNumbers
struct Timer { Timer() {} };
struct Clock { Clock(Timer) {} };

Clock c1(Timer());      // declares a function taking a function! (most vexing parse)
Clock c2{Timer{}};      // an object

int main() {
    Timer t();          // declares a function
    Timer u{};          // an object
    (void)c2; (void)u;
}
```

**Returning and passing.** A braced list can initialize a return value or argument when the target
type is known: `return {1, 2};`, `f({1, 2})`. With `explicit` constructors, this is rejected, which is
usually the point.

## `auto` and braces

`auto x{1}` deduces `int` and `auto x = {1}` deduces `std::initializer_list<int>` (C++17 rules,
N3922, applied retroactively as a defect report). The rules, and why `auto x{1, 2}` is an error, are
in [auto](../../03-types-and-values/type-deduction/auto.md#braced-initializers).

## Choosing a form

| You want | Write | Note |
|---|---|---|
| Zero or default object | `T x{};` | Value-initialization, no most vexing parse |
| Specific scalar value, no silent loss | `int n{expr};` | Narrowing is rejected |
| Aggregate | `Point p{1, 2};` or `.x = 1` designators (C++20) | [Aggregate page](./aggregate-initialization.md) |
| Container with elements | `std::vector<int> v{1, 2, 3};` | Uses `initializer_list` |
| Container with size and fill | `std::vector<int> v(n, 0);` | Braces would mean two elements |
| Class with an explicit single-argument constructor | `T x{arg};` | `T x = {arg};` is an error |
| Generic code that must accept narrowing conversions | `T x(args)` | Parentheses |

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `std::vector<int> v{10, 0}` meaning ten zeros | Braces mean the two elements `10` and `0` | `std::vector<int> v(10, 0)` |
| Adding an `initializer_list` constructor to an existing class | Every `T{a, b}` call site silently re-targets | Audit braced call sites, or keep both forms explicit |
| `int n{x}` with `double x` | Narrowing: ill-formed | Cast deliberately, or use `=` if truncation is intended |
| `T x = {a}` with an `explicit` constructor | Copy-list-initialization rejects `explicit` constructors | `T x{a};` |
| Expecting `Widget{}` to call the `initializer_list` constructor | Empty braces select the default constructor | Pass an explicit empty list: `Widget{std::initializer_list<int>{}}` |
| `auto v = {1, 2}` expecting a vector | Deduces `std::initializer_list<int>` | Name the type |
| Storing an `initializer_list` returned from a function | Its backing array is a temporary and dies at the end of the full-expression (or with the variable it initialized) | Copy into a container |

## Key points

- Braces select the form: value, aggregate, `initializer_list` constructor, or ordinary constructor.
- Narrowing conversions inside braces are ill-formed. Constants that fit are allowed.
- `std::initializer_list` constructors win over all others when braces are used, except for `{}`.
- `std::vector<int>{3, 7}` and `std::vector<int>(3, 7)` are different objects.
- Empty braces call the default constructor, which also avoids the most vexing parse.
