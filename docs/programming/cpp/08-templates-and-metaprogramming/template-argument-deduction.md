---
id: template-argument-deduction
title: Template Argument Deduction
sidebar_label: Argument Deduction
sidebar_position: 2
tags: [c++, templates, deduction, type-deduction, ctad, forwarding-reference]
---

# Template Argument Deduction

When you call `larger(3, 7)` instead of `larger<int>(3, 7)`, the compiler works out `T` itself by
comparing each function parameter type with the type of the matching argument. This is **template
argument deduction**. It decides which specialization is called, whether `const` survives, whether
an array decays to a pointer, and whether a `T&&` parameter receives an lvalue or an rvalue. This
page is the canonical home for the deduction rules for function templates and for **class template
argument deduction** (CTAD) with deduction guides.

**Prerequisites:** [Function Templates](./function-templates.md),
[lvalues and rvalues](../03-types-and-values/value-categories/lvalues-rvalues.md).

`auto` variables use the same rules (with one exception for braced lists), described on
[auto](../03-types-and-values/type-deduction/auto.md). Why `T&&` turns into `int&` for an lvalue
is explained by [Reference Collapsing](../03-types-and-values/value-categories/reference-collapsing.md).

## How deduction works

For each function parameter whose type `P` mentions a template parameter, and its argument of type
`A`, the compiler adjusts both types and then looks for a `T` that makes them identical. Each
parameter is deduced on its own, and all the results must agree.

<Diagram title="Deducing T for one parameter" caption="P is the parameter type as written, A is the argument's type. Every parameter is deduced independently, then the results are merged." accent="blue">
  <DiagramRow>
    <DiagramNode title="Adjust A">If P is not a reference: array and function types decay to pointers, top-level const/volatile is dropped.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Adjust P">If P is a reference, deduce against the referred-to type. Top-level cv on P is ignored.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Match" accent>Find T so that P equals A. If P is T&amp;&amp; and the argument is an lvalue, use A&amp; for A.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="Merge">All parameters must deduce the same T, otherwise deduction fails.</DiagramNode>
  </DiagramRow>
</Diagram>

Deduction failure is not an error by itself: the template simply drops out of the overload set. It
becomes an error only when no other candidate is viable. That property is what
[SFINAE](./sfinae-and-enable-if.md) builds on.

## By value: `T`

With a by-value parameter the function receives a copy, so the qualifiers of the original object
don't matter. References are ignored, top-level `const`/`volatile` is dropped, and arrays and
functions decay to pointers.

```cpp title="by_value.cpp" showLineNumbers
#include <type_traits>

template <typename T> T by_value(T) { return {}; }   // returns T so decltype can show it

int main() {
    int x = 0;
    const int cx = 0;
    const int& rx = x;
    int arr[4]{};
    const char* const p = "hi";

    static_assert(std::is_same_v<decltype(by_value(x)),    int>);
    static_assert(std::is_same_v<decltype(by_value(cx)),   int>);          // top-level const dropped
    static_assert(std::is_same_v<decltype(by_value(rx)),   int>);          // reference ignored
    static_assert(std::is_same_v<decltype(by_value(arr)),  int*>);         // array decays
    static_assert(std::is_same_v<decltype(by_value("hi")), const char*>);  // so does a literal
    static_assert(std::is_same_v<decltype(by_value(p)),    const char*>);  // only top-level const goes
    static_assert(std::is_same_v<decltype(by_value(main)), int(*)()>);     // function decays
}
```

Only the **top-level** `const` is removed. In `const char* const p`, the second `const` belongs to
the pointer and disappears, the first belongs to the pointee and stays (see
[cv-qualifiers](../03-types-and-values/cv-qualifiers.md)).

## By reference, by pointer, and forwarding references

With a reference parameter nothing is copied, so `const` must be kept and arrays don't decay. The
examples below use `std::type_identity<T>` *(C++20)* to carry the deduced `T` out of the call.

```cpp title="by_reference.cpp" showLineNumbers
#include <type_traits>

template <typename T> constexpr auto ref_T(T&)        { return std::type_identity<T>{}; }
template <typename T> constexpr auto cref_T(const T&) { return std::type_identity<T>{}; }
template <typename T> constexpr auto fwd_T(T&&)       { return std::type_identity<T>{}; }
template <typename T> constexpr auto ptr_T(T*)        { return std::type_identity<T>{}; }

template <typename Id> using get = typename Id::type;

int main() {
    int x = 0;
    const int cx = 0;
    int arr[4]{};

    static_assert(std::is_same_v<get<decltype(ref_T(x))>,   int>);
    static_assert(std::is_same_v<get<decltype(ref_T(cx))>,  const int>);  // const kept in T
    static_assert(std::is_same_v<get<decltype(ref_T(arr))>, int[4]>);     // no decay
    // ref_T(5);                                                         // error: rvalue to T&
    static_assert(std::is_same_v<get<decltype(cref_T(cx))>, int>);        // const already in P
    static_assert(std::is_same_v<get<decltype(cref_T(5))>,  int>);
    static_assert(std::is_same_v<get<decltype(fwd_T(x))>,   int&>);       // lvalue: T = int&
    static_assert(std::is_same_v<get<decltype(fwd_T(cx))>,  const int&>);
    static_assert(std::is_same_v<get<decltype(fwd_T(5))>,   int>);        // rvalue: T = int
    static_assert(std::is_same_v<get<decltype(ptr_T(&cx))>, const int>);
}
```

| Parameter | Argument `const int cx` | Argument `5` (rvalue) | Argument `int arr[4]` |
|---|---|---|---|
| `T` | `T = int` | `T = int` | `T = int*` |
| `T&` | `T = const int` | does not bind | `T = int[4]` |
| `const T&` | `T = int` | `T = int` | `T = int[4]` |
| `T&&` (forwarding) | `T = const int&` | `T = int` | `T = int(&)[4]` |
| `T*` | (needs `&cx`) `T = const int` | not a pointer | `T = int` |

`T&&` is a **forwarding reference** only when `T` is a template parameter of that same function
template being deduced, with no `const` and no wrapper around it. `const T&&` and
`std::vector<T>&&` are ordinary rvalue references and reject lvalues. The rule that makes the
lvalue case work (deduce `T = int&`, then `int& &&` collapses to `int&`) and how `std::forward`
uses it are on [Reference Collapsing](../03-types-and-values/value-categories/reference-collapsing.md).

## When deduction can't help

Some parameters cannot deduce anything. The template arguments for them must come from elsewhere:
another parameter, a default, or the caller writing them out.

```cpp title="non_deduced.cpp" showLineNumbers
#include <cstdio>
#include <type_traits>
#include <vector>

template <typename To, typename From>
To convert(From v) { return static_cast<To>(v); }      // To can't be deduced: list it first

template <typename T>
void from_iter(typename std::vector<T>::iterator) {}   // T is in a non-deduced context

template <typename T>
void fill(std::vector<T>&, std::type_identity_t<T> value) { (void)value; }  // C++20

int main() {
    double d = convert<double>(3);   // To = double given, From = int deduced
    std::vector<int> v{1, 2};
    // from_iter(v.begin());         // error: couldn't deduce T
    from_iter<int>(v.begin());       // fine once T is given
    fill(v, 2);                      // T = int from v alone; the 2nd argument only converts
    std::printf("%.1f\n", d);
}
```

```text
3.0
```

- **Return types.** In a function call, the return type is never used for deduction. Put such parameters first so callers can write
  `convert<double>(x)` and let the rest be deduced. Explicit arguments fill the parameter list from
  the left.
- **Non-deduced contexts.** A type to the left of `::` (`typename std::vector<T>::iterator`) cannot be
  reversed: many `T` could give the same iterator type. The same applies to `decltype(expr)` and to a
  non-type parameter used inside an expression (`std::array<int, N + 1>`).
- **Blocking deduction on purpose.** `std::type_identity_t<T>` *(C++20)* wraps a parameter in a
  non-deduced context, so only the other parameters determine `T` and the argument just converts.
  Without it, `fill(v, 2.5)` would fail with `T` deduced as both `int` and `double`.
- **Braced lists have no type.** `template <typename T> void f(T)` cannot be called as `f({1, 2})`.
  A parameter of type `std::initializer_list<T>` can: there `T = int`.
- **No implicit conversions during deduction.** `larger(3, 7.0)` fails even though `int` converts
  to `double`. Conversions are applied only after `T` has been fixed.

## Class template argument deduction (C++17)

Since C++17 you can omit the template arguments of a class template when you create an object, and
the compiler deduces them from the initializer. CTAD works by treating every constructor as if it
were a function template and running the deduction above on it.

```cpp title="ctad.cpp" showLineNumbers
#include <iterator>
#include <string>
#include <type_traits>
#include <vector>

template <typename T>
struct Box {
    T value;
    Box(T v) : value(v) {}
};

template <typename T>
struct Named {
    T value;
    Named(const T& v) : value(v) {}
};
Named(const char*) -> Named<std::string>;           // deduction guide for literals

template <typename T>
struct Range {
    std::vector<T> items;
    template <typename It>
    Range(It first, It last) : items(first, last) {}
};
template <typename It>
Range(It, It) -> Range<typename std::iterator_traits<It>::value_type>;

template <typename T>
struct Agg { T x; T y; };                           // aggregate: C++20 deduces without a guide

int main() {
    Box b{42};                                      // Box<int>
    Box s{"hi"};                                    // Box<const char*>: by-value decay
    Named n{"hi"};                                  // Named<std::string>, from the guide
    std::vector<int> v{1, 2, 3};
    Range r(v.begin(), v.end());                    // Range<int>, from the guide
    Agg a{1, 2};                                    // Agg<int>
    std::vector w{1, 2, 3};                         // std::vector<int>
    std::vector copy{w};                            // std::vector<int>: a copy, not a nested vector

    static_assert(std::is_same_v<decltype(b), Box<int>>);
    static_assert(std::is_same_v<decltype(s), Box<const char*>>);
    static_assert(std::is_same_v<decltype(n), Named<std::string>>);
    static_assert(std::is_same_v<decltype(r), Range<int>>);
    static_assert(std::is_same_v<decltype(a), Agg<int>>);
    static_assert(std::is_same_v<decltype(copy), std::vector<int>>);
}
```

### Deduction guides

A **deduction guide** `Template(params) -> Template<args>;` adds a pretend constructor that only
exists for deduction. Write one when the constructors don't mention `T` in a deducible way:

- `Range` takes a pair of iterators. Its constructor is a template over `It`, and nothing connects
  `It` to `T`, so without the guide `Range r(v.begin(), v.end())` fails.
- `Named` would deduce `T = char[3]` from `"hi"` through `const T&`. The guide `Named(const char*)`
  is a **non-template** guide: it applies to any argument that converts to `const char*` and maps
  it to `Named<std::string>`.

Guides are declared at namespace scope, next to the class template. They don't have to correspond to
any real constructor: the deduced specialization is still constructed with its real constructors
afterwards.

### CTAD pitfalls

- **All or nothing.** CTAD runs only when no template argument list is written. `std::pair<int> p{1, 2.0}`
  does not deduce the second argument, it is an error.
- **Copy deduction wins.** `std::vector copy{w}` with one `std::vector<int>` argument deduces
  `std::vector<int>` (a copy), not `std::vector<std::vector<int>>`. Two vectors in the braces would
  give the nested type.
- **Aggregates** need a deduction guide before C++20. Since C++20 (P1816) aggregate initialization
  deduces directly, as `Agg a{1, 2}` shows. Alias templates gained CTAD in C++20 too (P1814).
- **Literals decay or don't.** `Box{"hi"}` gives `Box<const char*>` because the constructor takes
  `T` by value. A constructor taking `const T&` deduces an array type. Decide which you want and add
  a guide if neither is right.

## References

- [cppreference: Template argument deduction](https://en.cppreference.com/w/cpp/language/template_argument_deduction)
- [cppreference: Class template argument deduction (CTAD)](https://en.cppreference.com/w/cpp/language/class_template_argument_deduction)
- [cppreference: `std::type_identity`](https://en.cppreference.com/w/cpp/types/type_identity)
- [P1816R0: CTAD for aggregates](https://wg21.link/p1816r0), [P1814R0: CTAD for alias templates](https://wg21.link/p1814r0)
