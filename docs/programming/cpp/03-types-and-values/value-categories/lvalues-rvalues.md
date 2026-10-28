---
id: lvalues-rvalues
title: Lvalues and Rvalues
sidebar_label: Lvalues & Rvalues
sidebar_position: 1
tags: [c++, lvalue, rvalue, value-categories, references]
---

# Lvalues and Rvalues

Every C++ expression has two independent properties: a **type** (`int`, `std::string`) and a
**value category**. The category answers one question: does this expression name an object that
keeps existing after the expression, or is it a value you may consume? The answer decides which
references can bind to the expression, which overload is chosen, and whether an object is copied or
moved. This page covers the two-way split, lvalue versus rvalue, which is enough for everyday code.
The full five-category taxonomy is on [glvalue, prvalue, xvalue](./glvalue-prvalue-xvalue.md).

**Prerequisites:** [References](../../06-pointers-references-and-smart-pointers/references.md)

## The two categories

- An **lvalue** designates an object or function that you can refer to again: a variable, `*p`,
  `a[i]`, a call to a function that returns `T&`. You can take its address with `&`.
- An **rvalue** is an expression whose object (if any) you are allowed to treat as expendable: a
  literal such as `42`, the result of `x + 1`, a call that returns by value, or `std::move(x)`.

The quick test is "can I take its address?". It works for most expressions but not all:
`std::move(x)` refers to the very object `x`, yet `&std::move(x)` doesn't compile because the
expression is an rvalue. Category is a property of the *expression*, not of the object behind it.

```cpp title="basic.cpp" showLineNumbers
int main() {
    int x = 42;   // `x` is an lvalue, `42` is an rvalue
    x = 10;       // OK: assign to an lvalue
    int* p = &x;  // OK: take the address of an lvalue
    *p = 7;       // `*p` is an lvalue too

    // 10 = x;    // error: cannot assign to an rvalue of type int
    // &42;       // error: cannot take the address of an rvalue
    // &(x + 1);  // error: same
}
```

| Expression | Category | Why |
|---|---|---|
| `x`, `*p`, `a[i]`, `s.member` (with `s` an lvalue) | lvalue | Names an existing object |
| `++x`, `x = 5`, `x += 1` | lvalue | Built-in prefix increment and assignment return the object |
| `"text"` | lvalue | A string literal is an array object with static storage |
| A call to a function returning `T&` | lvalue | Refers to an object that lives elsewhere |
| `42`, `true`, `nullptr` | rvalue | Just a value |
| `x + 1`, `x++`, `a < b` | rvalue | A computed value. `x++` yields a copy of the old value |
| A call to a function returning `T` (by value) | rvalue | A fresh value |
| `std::move(x)`, `static_cast<T&&>(x)` | rvalue | Marks `x` as expendable |

## How references bind

The categories matter most when initializing references. Each kind of reference accepts a different
set of expressions:

| Reference | Binds to lvalue | Binds to rvalue |
|---|---|---|
| `T&` | Yes | No |
| `const T&` | Yes | Yes |
| `T&&` *(C++11)* | No | Yes |

```cpp title="binding.cpp" showLineNumbers
#include <utility>

int main() {
    int x = 10;

    int& r1 = x;                // lvalue to T&
    // int& r2 = 42;            // error: T& cannot bind to an rvalue

    const int& r3 = x;          // lvalue to const T&
    const int& r4 = 42;         // rvalue to const T&: a temporary is created

    // int&& r5 = x;            // error: T&& cannot bind to an lvalue
    int&& r6 = 42;              // rvalue to T&&
    int&& r7 = std::move(x);    // std::move turns x into an rvalue

    (void)r1; (void)r3; (void)r4; (void)r6; (void)r7;
}
```

`const T&` accepting both kinds is why it is the default parameter type for read-only arguments.
When `r4` or `r6` binds to a temporary, the temporary lives as long as the reference. That rule and
its exceptions are on [Object Lifetime](../../05-memory-and-object-lifetime/object-lifetime.md#lifetime-extension).

## A named rvalue reference is an lvalue

The type of a variable and the category of an expression naming it are separate. A parameter
declared `int&& x` has type "rvalue reference to `int`", but inside the function the expression `x`
is an lvalue, because it has a name and can be used again on the next line:

```cpp title="named.cpp" showLineNumbers
#include <utility>

void take(int&&) {}

void process(int&& x) {
    int& lref = x;           // OK: the expression `x` is an lvalue
    // take(x);              // error: cannot bind int&& to an lvalue
    take(std::move(x));      // OK: cast back to an rvalue
    (void)lref;
}

int main() { process(42); }
```

This is deliberate. If a named rvalue reference were an rvalue, the first use of it could move from
the object and every later use would see a moved-from value.

## Overloading on category

Because `T&`/`const T&` and `T&&` accept different categories, a pair of overloads can treat
"the caller still needs this" and "the caller is done with this" differently. The output below is
from GCC 15 and Clang 21 with `-std=c++23`:

```cpp title="overload.cpp" showLineNumbers
#include <iostream>
#include <utility>

void process(const int& x) { std::cout << "lvalue overload: " << x << '\n'; }
void process(int&& x)      { std::cout << "rvalue overload: " << x << '\n'; }

int main() {
    int a = 10;
    process(a);             // a is an lvalue
    process(20);            // literal: rvalue
    process(a + 5);         // computed value: rvalue
    process(std::move(a));  // cast to rvalue
}
```

```text
lvalue overload: 10
rvalue overload: 20
rvalue overload: 15
rvalue overload: 10
```

This is the mechanism behind move semantics: a class provides a copy constructor taking
`const T&` and a move constructor taking `T&&`, and the argument's category picks one. Writing those
constructors is covered on [Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md).

## `std::move` is only a cast

`std::move(x)` (in `<utility>`) is `static_cast<std::remove_reference_t<T>&&>(x)`. It generates no
code and moves nothing. It changes the category of the expression to rvalue, so that overload
resolution picks a `T&&` overload if one exists. The move, if any, happens in the function that
receives the rvalue:

```cpp title="move-cast.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <utility>

int main() {
    std::string a = "hello";
    std::string&& r = std::move(a);      // no move: r is just a reference to a
    std::cout << r << '\n';              // prints hello: r and a are the same object

    std::string b = std::move(a);        // the move constructor runs here
    std::cout << b << ' ' << a.size() << '\n';
}
```

```text
hello
hello 0
```

The `0` is what libstdc++ and libc++ happen to leave behind. The standard only says a moved-from
`std::string` is in a *valid but unspecified* state: calling `size()` on it is fine, relying on the
value is not.

## Common mistakes

- **Assuming moved-from means unusable.** A moved-from standard library object is valid. You may
  call any member without preconditions (`size()`, `clear()`, assignment). What you can't do is
  assume its contents. Assign a new value before reading it again.
- **`std::move` on a `const` object.** `std::move(c)` with `const std::string c` yields
  `const std::string&&`. That doesn't bind to `std::string&&`, so the *copy* constructor runs, and
  neither GCC nor Clang warns about it with `-Wall -Wextra`.
- **`std::move` on a return value.** `return std::move(local);` turns a return that the compiler
  could have elided into a forced move. Write `return local;`. GCC and Clang warn with
  `-Wpessimizing-move`, which both enable with `-Wall`.
- **Returning a reference to a temporary.** `const std::string& f() { return "x"; }` returns a
  reference to a temporary that dies at the end of the `return` statement. The caller reads a
  dangling reference. Return by value.

## Key points

- Category belongs to an expression, not to an object or a variable's type.
- `T&` takes lvalues, `T&&` takes rvalues, `const T&` takes both.
- Anything with a name is an lvalue, including a variable of type `T&&`.
- `std::move` is a cast to rvalue; the move happens in whatever receives it.

## Related

- [glvalue, prvalue, xvalue](./glvalue-prvalue-xvalue.md): the precise five-category model and
  temporary materialization.
- [Reference Collapsing](./reference-collapsing.md): how `T&&` in a template accepts both
  categories and how `std::forward` restores them.
- [decltype](../type-deduction/decltype.md): asking the compiler for an expression's category.
