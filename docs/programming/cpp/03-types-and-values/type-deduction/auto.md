---
id: auto-type-deduction
title: auto Type Deduction
sidebar_label: auto
sidebar_position: 1
tags: [c++, auto, type-deduction, cpp11, cpp14, cpp17, cpp20]
---

# auto Type Deduction

`auto` *(C++11)* asks the compiler to work out a variable's type from its initializer. The rule it
follows is not "use the initializer's exact type". It is template argument deduction: `auto x = e;`
deduces the same type as `T` in a call `f(e)` to `template <class T> void f(T)`. That is why plain
`auto` drops references and top-level `const`, why `auto&` keeps `const`, and why `auto&&` binds to
anything. This page gives the rule for each form, traces it through several declarations, and lists
the places it surprises people.

**Prerequisites:** [const and volatile](../cv-qualifiers.md) (top-level vs low-level `const`),
[Reference Collapsing](../value-categories/reference-collapsing.md) (for `auto&&`).
The underlying template rules are on
[Template Argument Deduction](../../08-templates-and-metaprogramming/template-argument-deduction.md).

## The three forms

| Declaration | Behaves like the parameter | Result |
|---|---|---|
| `auto x = e;` | `T` (by value) | A copy. References, top-level `const`/`volatile` removed. Arrays and functions decay to pointers. |
| `auto& x = e;` / `const auto& x = e;` | `T&` / `const T&` | A reference. `const` of the referred object is kept. Arrays don't decay. `auto&` can't bind to an rvalue. |
| `auto&& x = e;` | `T&&` (forwarding reference) | `A&` for an lvalue, `A&&` for an rvalue. Binds to anything. |

`auto` can be combined with `const`, `*` and `&` like any type: `const auto* p = &x;` is valid and
deduces `auto` from the pointee.

## Tracing deduction

All the declarations below share these variables. Each result is confirmed by a `static_assert`
in the program after the walkthrough.

```cpp
const int  ci = 1;
const int& cr = ci;
int arr[3] = {};
const int* cp = &ci;
```

<Walkthrough title="Deducing auto, one declaration at a time" accent="green">
  <Step title="auto a = cr;">

Match `cr` (type `const int&`) against a by-value `T`. The reference is dropped first, giving
`const int`. A copy has its own `const`-ness, so the top-level `const` goes too:
<StepChange>`a` is `int`</StepChange>.

  </Step>
  <Step title="auto& b = cr;">

Match against `T&`. The reference is dropped, then `const int` is matched to `T`, so `T` is
`const int`. Removing `const` here would let you modify `ci` through `b`, so it stays:
<StepChange>`b` is `const int&`</StepChange>.

  </Step>
  <Step title="auto c = arr;">

A by-value `T` can't hold an array, so the array decays to a pointer to its first element:
<StepChange>`c` is `int*`</StepChange>. `sizeof c` is the size of a pointer, not 12.

  </Step>
  <Step title="auto& d = arr;">

A reference parameter doesn't decay its argument. `T` becomes `int[3]`:
<StepChange>`d` is `int(&)[3]`</StepChange>, and `sizeof d` is `sizeof arr`.

  </Step>
  <Step title="auto&& e = ci;">

`ci` is an lvalue, so the forwarding-reference rule deduces `T = const int&`, and `T&&` collapses:
<StepChange>`e` is `const int&`</StepChange>.

  </Step>
  <Step title="auto&& f = 42;">

`42` is a prvalue. `T = int`, no collapsing: <StepChange>`f` is `int&&`</StepChange>, bound to a
materialized temporary whose lifetime is extended to that of `f`.

  </Step>
  <Step title="auto g = cp;">

`cp` is `const int*`. The `const` here applies to the pointee, not to `cp`, so it is low-level and
is kept: <StepChange>`g` is `const int*`</StepChange>. Only the pointer itself is copied.

  </Step>
</Walkthrough>

```cpp title="auto-deduction.cpp" showLineNumbers
#include <type_traits>
using std::is_same_v;

int main() {
    const int  ci = 1;
    const int& cr = ci;
    int arr[3] = {};
    const int* cp = &ci;

    auto   a = cr;   static_assert(is_same_v<decltype(a), int>);
    auto&  b = cr;   static_assert(is_same_v<decltype(b), const int&>);
    auto   c = arr;  static_assert(is_same_v<decltype(c), int*>);
    auto&  d = arr;  static_assert(is_same_v<decltype(d), int(&)[3]>);
    auto&& e = ci;   static_assert(is_same_v<decltype(e), const int&>);
    auto&& f = 42;   static_assert(is_same_v<decltype(f), int&&>);
    auto   g = cp;   static_assert(is_same_v<decltype(g), const int*>);
    const auto h = &arr[0];  static_assert(is_same_v<decltype(h), int* const>);
    (void)a; (void)b; (void)c; (void)d; (void)e; (void)f; (void)g; (void)h;
}
```

`decltype(name)` reports the declared type of a variable, which makes it the standard way to check
what `auto` produced (see [decltype](./decltype.md)). The last line shows that `const auto` applies
`const` to the deduced type itself: a `const` pointer to `int`, not a pointer to `const int`.

## Braced initializers

Braces are the one place where `auto` differs from template deduction. A template parameter `T`
can't be deduced from `{1, 2}` at all; `auto` has its own rules:

```cpp title="auto-braces.cpp" showLineNumbers
#include <initializer_list>
#include <type_traits>

int main() {
    auto a = {1, 2};   // std::initializer_list<int>
    auto b = {1};      // std::initializer_list<int>
    auto c{1};         // int  (C++17 rule, see below)
    // auto d{1, 2};   // error: direct-list-init with auto needs exactly one element
    // auto e = {1, 2.0};  // error: elements must have the same type

    static_assert(std::is_same_v<decltype(a), std::initializer_list<int>>);
    static_assert(std::is_same_v<decltype(b), std::initializer_list<int>>);
    static_assert(std::is_same_v<decltype(c), int>);
}
```

Copy-list-initialization (`= {…}`) always gives `std::initializer_list`. Direct-list-initialization
(`{…}` without `=`) gives the element type and requires one element. C++11 and C++14 as published
deduced `std::initializer_list<int>` for `auto c{1};`. The change came from
[N3922](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2014/n3922.html), adopted for C++17,
and GCC and Clang apply it in their C++11 and C++14 modes as well.

## `auto` beyond variables

| Use | Since | Notes |
|---|---|---|
| `auto f() { return …; }` | C++14 | Return type deduced from the `return` statements with the by-value rule. All `return` statements must deduce the same type. |
| `auto f() -> T` | C++11 | Trailing return type. Here `auto` deduces nothing; it is a placeholder for the syntax. |
| `[](auto x) { … }` | C++14 | Generic lambda: each `auto` parameter is an invented template parameter. |
| `void f(auto x);` | C++20 | Abbreviated function template, the same as `template <class T> void f(T x);`. |
| `auto [k, v] = pair;` | C++17 | Structured binding. `auto` applies to a hidden object, not to `k` and `v` individually. |
| `template <auto N>` | C++17 | Non-type template parameter whose type is deduced from the argument. |
| `auto(x)`, `auto{x}` | C++23 | Makes a prvalue copy of `x` with the by-value rule (*decay-copy*). |

A deduced return type that drops a reference you wanted is the motivation for
[decltype(auto)](./decltype-auto.md).

## Common mistakes

**Copying when you meant to refer.** `for (auto s : names)` copies every `std::string`. Use
`const auto&` to read and `auto&` to modify. The same happens with a function returning a reference:
`auto x = v.front();` is a copy, and assigning to `x` doesn't change `v`.

**Proxy types.** Some functions return an object that stands in for a reference.
`std::vector<bool>::operator[]` is the classic case:

```cpp title="proxy.cpp" showLineNumbers
#include <iostream>
#include <vector>

std::vector<bool> flags() { return {true, false}; }

int main() {
    auto ok = flags()[0];    // std::vector<bool>::reference, not bool
    // The temporary vector is destroyed at the end of the line above,
    // so `ok` refers into freed memory. Reading it is undefined behavior.
    bool safe = flags()[0];  // converts to bool while the vector is still alive
    std::cout << safe << '\n';
    (void)ok;
}
```

Expression-template libraries (Eigen, for example) have the same issue. Name the type you want
(`bool`), or convert explicitly with `static_cast<bool>(…)`. C++23 `auto(…)` doesn't help: it copies
the proxy, not the value.

**Unexpected integer types.** `auto n = v.size();` is `std::size_t` (unsigned), and `auto i = 0;`
is `int`. Comparing or subtracting them mixes signedness; see [Signedness](../signedness.md).
Use `auto i = 0uz;` *(C++23)* or `std::ssize(v)` *(C++20)* when the types should match.

**Mixed declarators.** `auto a = 1, b = 2.5;` is an error: every declarator in one `auto`
declaration must deduce the same type.

## Key points

- `auto` follows template deduction. By value, by reference, and forwarding reference are three
  different rules.
- Plain `auto` copies: it removes references and top-level `const` and decays arrays.
- `auto&` keeps `const`; `auto&&` binds to anything and records lvalue or rvalue.
- `auto x = {…}` is `std::initializer_list`; `auto x{v}` is the type of `v`.

## Related

- [decltype](./decltype.md): the other deduction rule, which keeps references.
- [Uniform Initialization](../../05-memory-and-object-lifetime/initialization/uniform-initialization.md):
  how braces interact with constructors, including `std::initializer_list` overloads.
