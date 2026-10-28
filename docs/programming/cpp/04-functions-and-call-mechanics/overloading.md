---
id: function-overloading
title: Function Overloading
sidebar_label: Overloading
sidebar_position: 3
tags: [c++, functions, overloading, overload-resolution]
---

# Function Overloading

**Overloading** lets several functions in the same scope share a name as long as their parameter
lists differ. At each call the compiler runs **overload resolution**: it collects the candidates,
discards the ones that can't take the arguments, and ranks the rest by how much conversion each
argument needs. This happens entirely at compile time and is a different mechanism from overriding
a [virtual function](../07-classes-and-oop/virtual-functions.md), which is chosen at run time.
Overloading is also why C++ needs [name mangling](../01-toolchain-and-build/name-mangling.md).

**Prerequisites:** [Function Declarations](./function-declarations.md) (what a signature is),
[Conversions and Promotions](../03-types-and-values/conversions-and-promotions.md) (the conversions
that resolution ranks).

```cpp title="basic.cpp" showLineNumbers
#include <cstdio>
#include <string>

void print(int)                { std::puts("int"); }
void print(long)               { std::puts("long"); }
void print(double)             { std::puts("double"); }
void print(const std::string&) { std::puts("string"); }

int main() {
    print('A');     // int:    char -> int is a promotion
    print(3.14f);   // double: float -> double is a promotion
    print(42L);     // long:   exact match
}
```

## What can and cannot differ

Two declarations overload each other only if their parameter-type lists differ **after adjustment**.
The compiler first rewrites each parameter type: top-level `const`/`volatile` is dropped, arrays
become pointers, and function types become function pointers.

| Declarations | Result |
|---|---|
| `f(int)` / `f(int, int)` | Overloads: different count |
| `f(int)` / `f(double)` | Overloads: different type |
| `f(int*)` / `f(const int*)` | Overloads: `const` on the pointee is part of the type |
| `f(int&)` / `f(int&&)` / `f(const int&)` | Overloads: different reference types |
| `f(int)` / `f(const int)` | **Same function**: top-level `const` is dropped |
| `f(int*)` / `f(int[])` / `f(int[10])` | **Same function**: arrays adjust to pointers |
| `int f(int)` / `double f(int)` | **Error**: differ only in return type |

Member functions can also overload on their `const` qualifier and on ref-qualifiers (`&`, `&&`),
because those change the type of the implicit object parameter:

```cpp showLineNumbers
// ...
class Buffer {
public:
    char&       at(std::size_t i)       { return data_[i]; }  // called on non-const objects
    const char& at(std::size_t i) const { return data_[i]; }  // called on const objects
    std::string take() &&               { return std::move(data_); }  // only on rvalues
private:
    std::string data_;
};
```

## How resolution ranks candidates

Overload resolution has three stages:

1. **Candidate functions.** Name lookup finds every function with that name visible at the call:
   ordinary lookup plus [argument-dependent lookup](https://en.cppreference.com/w/cpp/language/adl).
   Function templates contribute a specialization each, if deduction succeeds.
2. **Viable functions.** Keep the candidates with the right number of parameters (counting defaults
   and `...`) where every argument has *some* implicit conversion to its parameter.
3. **Best viable function.** For each argument, rank the conversion that each candidate needs.

Each argument's conversion sequence falls into one of these categories, best first:

| Rank | What it covers | Examples |
|---|---|---|
| **Exact match** | No conversion, or only lvalue-to-rvalue, array-to-pointer, function-to-pointer, adding `const` to a pointee | `int` → `int`, `int[4]` → `int*`, `int*` → `const int*` |
| **Promotion** | Integral promotion, `float` → `double` | `char` → `int`, `bool` → `int`, `float` → `double` |
| **Conversion** | Any other standard conversion | `int` → `long`, `int` → `double`, `double` → `int`, `Derived*` → `Base*` |
| **User-defined conversion** | A converting constructor or conversion operator, plus standard conversions around it | `const char*` → `std::string` |
| **Ellipsis** | Matching a `...` parameter | `printf`-style |

Candidate F1 is **better** than F2 if none of F1's argument conversions is worse than F2's and at
least one is strictly better. The best viable function must be better than *every* other viable
function. If no candidate satisfies that, the call is **ambiguous** and won't compile. A function
that wins on one argument and loses on another is not better than its rival.

Note that `int` → `long` is a *conversion*, not a promotion. Only conversions to `int` (or
`unsigned int`) and `float` → `double` count as promotions.

## A traced example

Three overloads and two calls. Compiled with GCC 15 and Clang 21 (`-std=c++23`):

```cpp title="trace.cpp" showLineNumbers
#include <cstdio>

void f(int, double)  { std::puts("#1 f(int, double)"); }
void f(double, int)  { std::puts("#2 f(double, int)"); }
void f(long, long)   { std::puts("#3 f(long, long)"); }

int main() {
    f('a', 2.0f);    // prints "#1 f(int, double)"
    // f(1, 2);      // error: call of overloaded 'f(int, int)' is ambiguous
}
```

<Walkthrough title="Resolving f('a', 2.0f), then f(1, 2)" caption="Each argument is ranked separately; the winner must be at least as good on every argument." accent="blue">
  <Step title="Candidates and viability">

All three `f` are candidates. All three are viable for `f('a', 2.0f)`: `char` and `float` both
convert implicitly to `int`, `double` and `long`.

  </Step>
  <Step title="Rank argument 1: 'a' (char)">

| | #1 `int` | #2 `double` | #3 `long` |
|---|---|---|---|
| `char` → | <StepChange>Promotion</StepChange> | Conversion | Conversion |

Only #1 gets a promotion. `char` → `long` is a conversion, not a promotion.

  </Step>
  <Step title="Rank argument 2: 2.0f (float)">

| | #1 `double` | #2 `int` | #3 `long` |
|---|---|---|---|
| `float` → | <StepChange>Promotion</StepChange> | Conversion | Conversion |

`float` → `double` is the one floating-point promotion.

  </Step>
  <Step title="Compare: #1 wins">

#1 is at least as good as #2 and #3 on both arguments and strictly better on at least one.
<StepChange>#1 `f(int, double)` is the best viable function.</StepChange>

  </Step>
  <Step title="Now f(1, 2): rank both arguments">

| | #1 `(int, double)` | #2 `(double, int)` | #3 `(long, long)` |
|---|---|---|---|
| arg 1 `int` → | Exact | Conversion | Conversion |
| arg 2 `int` → | Conversion | Exact | Conversion |

  </Step>
  <Step title="Compare: no winner">

#1 beats #2 on argument 1 but loses on argument 2, so neither is better. Both beat #3, but that
doesn't help: the best function must beat every other one.
<StepChange>Ambiguous: compile error.</StepChange> Adding `f(int, int)` or casting one argument fixes it.

  </Step>
</Walkthrough>

## Tie-breakers

When the argument rankings don't separate two candidates, these rules are tried, among others:

- A **non-template** beats a function-template specialization with equally good conversions.
- Between two templates, the **more specialized** one wins (see
  [Function Templates](../08-templates-and-metaprogramming/function-templates.md)).
- For reference binding, an rvalue binds better to `T&&` than to `const T&`, and a reference to a
  less-qualified type beats a more-qualified one (`int&` over `const int&` for a non-const lvalue).
- *(C++20)* A candidate whose constraints subsume the other's wins (see
  [Concepts](../08-templates-and-metaprogramming/concepts-and-requires.md)).

```cpp title="refs.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <utility>

void process(const std::string&) { std::puts("lvalue"); }
void process(std::string&&)      { std::puts("rvalue"); }

int main() {
    std::string s = "hi";
    process(s);             // lvalue
    process(std::string{}); // rvalue: && binds an rvalue better than const&
    process(std::move(s));  // rvalue
}
```

## Common mistakes

**A forwarding-reference template beats your specific overload.** `T&&` deduces to the exact type,
including non-const, so it often matches better than a hand-written `const` overload:

```cpp title="greedy.cpp" showLineNumbers
#include <cstdio>

template <class T> void g(T&&)  { std::puts("template T&&"); }
void g(const int&)              { std::puts("const int&"); }

int main() {
    int x = 1;
    const int cx = 2;
    g(x);    // template T&&: T = int&, exact; const int& would add const
    g(cx);   // const int&: tie on conversions, non-template wins
}
```

The fix is to constrain the template (`requires`) so it drops out for the types you handle
separately.

**Two conversions of the same rank are ambiguous.** With `k(long)` and `k(double)`, `k(42)` doesn't
compile: `int` → `long` and `int` → `double` are both conversions. Add `k(int)` or cast.

**A derived class hides base overloads.** Declaring `func` in a derived class hides *every* `func`
from the base, so resolution never sees them:

```cpp title="hiding.cpp" showLineNumbers
#include <cstdio>

struct Base { void func(int) { std::puts("Base::func(int)"); } };
struct D1 : Base { void func(double) { std::puts("D1::func(double)"); } };
struct D2 : Base {
    using Base::func;   // bring the base overloads into this scope
    void func(double) { std::puts("D2::func(double)"); }
};

int main() {
    D1{}.func(42);   // D1::func(double): Base::func(int) is hidden
    D2{}.func(42);   // Base::func(int): exact match now visible
}
```

**Overloads that collide with default arguments.** Declaring `f(int, int = 0)` and `f(int)` is legal,
but every call `f(42)` is ambiguous. See [Default Arguments](./default-arguments.md).

Operators are overloaded with the same resolution rules; how to write them is on
[Operator Overloading](../02-language-fundamentals/operators/operator-overloading.md).

## Key points

- Overloads must differ in parameter types after adjustment; return type and top-level `const` don't
  count.
- Ranking per argument: exact match, promotion, conversion, user-defined, ellipsis.
- The winner must be at least as good on every argument and better on one; otherwise the call is
  ambiguous.
- `int` → `long` is a conversion, not a promotion; that surprise causes many ambiguities.
- Watch unconstrained `T&&` templates and name hiding in derived classes.
- Full rules: [overload resolution on cppreference](https://en.cppreference.com/w/cpp/language/overload_resolution).
