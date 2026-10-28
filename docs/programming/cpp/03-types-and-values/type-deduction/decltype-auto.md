---
id: decltype-auto
title: decltype(auto)
sidebar_label: decltype(auto)
sidebar_position: 3
tags: [c++, decltype-auto, type-deduction, cpp14]
---

# decltype(auto)

`decltype(auto)` *(C++14)* is a placeholder like `auto`, but it deduces with the
[decltype](./decltype.md) rules applied to the initializer: `decltype(auto) x = e;` gives `x` the
type `decltype(e)`. Its main job is in function return types, where a wrapper has to return exactly
what the function it wraps returns, a reference included. Plain `auto` can't: it always deduces a
non-reference. The same exactness makes it easy to return a dangling reference, so this page covers
both.

**Prerequisites:** [auto](./auto.md), [decltype](./decltype.md)

## The rule

| Declaration | Deduced as |
|---|---|
| `auto x = e;` | By-value template rule: no reference, no top-level `const` |
| `decltype(auto) x = e;` | `decltype(e)`: declared type for a bare name, otherwise `T` / `T&` / `T&&` by category |

```cpp title="decltype-auto-vars.cpp" showLineNumbers
#include <type_traits>
#include <vector>
using std::is_same_v;

int main() {
    std::vector<int> v{1, 2, 3};
    int x = 0;
    const int& cr = x;

    auto           a = v[0];   static_assert(is_same_v<decltype(a), int>);         // copy
    decltype(auto) b = v[0];   static_assert(is_same_v<decltype(b), int&>);        // refers to v[0]
    decltype(auto) c = x;      static_assert(is_same_v<decltype(c), int>);         // bare name: declared type
    decltype(auto) d = (x);    static_assert(is_same_v<decltype(d), int&>);        // lvalue expression
    decltype(auto) e = cr;     static_assert(is_same_v<decltype(e), const int&>);  // declared type kept
    b = 42;                    // changes v[0]
    (void)a; (void)c; (void)d; (void)e;
}
```

`decltype(auto)` must appear on its own: `const decltype(auto)`, `decltype(auto)&` and
`decltype(auto)*` are all errors. As a variable declaration it is rarely clearer than naming the
type or writing `auto&`. Its real use is return types.

## Forwarding a return type

A function that wraps another, such as a logging or locking wrapper, should not change what the
callee returns. With `auto` the reference disappears:

<Tabs>
  <TabItem value="auto" label="auto: always a copy">

```cpp title="wrap-auto.cpp" showLineNumbers
#include <vector>

template <class C>
auto at(C& c, std::size_t i) { return c[i]; }   // deduces int for vector<int>

int main() {
    std::vector<int> v{1, 2, 3};
    // at(v, 0) = 10;   // error: assigning to a prvalue int
    return at(v, 0);
}
```

  </TabItem>
  <TabItem value="decltype-auto" label="decltype(auto): exactly what c[i] is">

```cpp title="wrap-decltype-auto.cpp" showLineNumbers
#include <cstdio>
#include <vector>

template <class C>
decltype(auto) at(C& c, std::size_t i) { return c[i]; }   // int& for vector<int>

int main() {
    std::vector<int> v{1, 2, 3};
    at(v, 0) = 10;             // writes through the returned reference
    std::printf("%d\n", v[0]); // prints 10
}
```

  </TabItem>
</Tabs>

For a container whose `operator[]` returns a value (or a proxy, like `std::vector<bool>`), the
`decltype(auto)` version returns that value too. The general wrapper forwards both its arguments
and its result:

```cpp title="invoke-wrapper.cpp" showLineNumbers
#include <cstdio>
#include <functional>
#include <type_traits>
#include <utility>

template <class F, class... Args>
decltype(auto) logged(F&& f, Args&&... args) {
    std::puts("calling");
    return std::invoke(std::forward<F>(f), std::forward<Args>(args)...);
}

int  value() { return 1; }
int& counter() { static int n = 0; return n; }

int main() {
    static_assert(std::is_same_v<decltype(logged(value)), int>);
    static_assert(std::is_same_v<decltype(logged(counter)), int&>);
    logged(counter) += 5;
    std::printf("%d\n", counter());
}
```

```text
calling
5
```

`std::invoke` *(C++17, `<functional>`)* calls any callable. `decltype` is unevaluated, so the two
`static_assert` lines print nothing; only the call on line 18 prints.

## Return statements, traced

With `decltype(auto)` the exact spelling of the `return` operand decides the return type. Each
function below returns something different:

```cpp title="returns.cpp" showLineNumbers
#include <utility>
#include <vector>

std::vector<int> g_vec{1, 2, 3};
int make();

decltype(auto) r1() { return g_vec[0]; }        // int&
decltype(auto) r2() { int x = 0; return x; }    // int
decltype(auto) r3() { int x = 0; return (x); }  // int& (C++20), int&& (C++23): dangles
decltype(auto) r4() { int x = 0; return std::move(x); }  // int&& -> dangles
decltype(auto) r5() { return make(); }          // int
// ...
```

<Walkthrough title="What each return statement deduces" accent="amber">
  <Step title="return g_vec[0];">

`g_vec[0]` is a call to `operator[]`, which returns `int&`, so it is an lvalue expression of type
`int`: <StepChange>`int&`</StepChange>. Safe, because `g_vec` outlives the call.

  </Step>
  <Step title="return x;">

`x` is a bare name declared `int`, so rule 1 gives the declared type:
<StepChange>`int`</StepChange>. A copy (or NRVO) of the local, which is fine.

  </Step>
  <Step title="return (x);">

The parentheses make it an expression rather than a bare name, so rule 2 applies. Up to C++20 it is
an lvalue: <StepChange label="dangling">`int&`</StepChange>. C++23
([P2266](https://wg21.link/p2266r3)) treats a returned local as an xvalue even in parentheses, so
GCC 15 and Clang 21 with `-std=c++23` deduce `int&&`. Either way the function returns a reference
to `x`, which is destroyed on return. Both compilers warn (`-Wreturn-local-addr` /
`-Wreturn-stack-address`, on by default).

  </Step>
  <Step title="return std::move(x);">

`std::move(x)` is an xvalue: <StepChange label="dangling">`int&&`</StepChange>. Also a reference to
a dead local. Plain `auto` would have deduced `int` here and been correct.

  </Step>
  <Step title="return make();">

A call returning `int` by value is a prvalue: <StepChange>`int`</StepChange>. With `auto` and with
`decltype(auto)` alike, the result is the value.

  </Step>
</Walkthrough>

## Common mistakes

- **Parentheses around a returned local.** `return (result);` is a habit carried over from C. With
  `decltype(auto)` it turns a value return into a dangling reference.
- **Forwarding a temporary into a reference.** A pass-through like
  `template <class T> decltype(auto) id(T&& t) { return std::forward<T>(t); }` returns `T&&`. Then
  `decltype(auto) s = id(std::string("x"));` declares `s` as `std::string&&` bound to a temporary
  that dies at the end of the line. Lifetime extension doesn't pass through function returns.
- **Using it where you want a value.** If the caller should get its own object, write `auto`. Use
  `decltype(auto)` only when the function's purpose is to return whatever the inner expression is.

## Key points

- `decltype(auto) x = e;` means "the type `decltype(e)`".
- It is the tool for wrappers that must not change a callee's return type.
- `return (x);` and `return std::move(x);` in a `decltype(auto)` function return references to
  locals.

## Related

- [Reference Collapsing](../value-categories/reference-collapsing.md): forwarding the arguments that
  go with a forwarded return.
- [Object Lifetime](../../05-memory-and-object-lifetime/object-lifetime.md#lifetime-extension):
  which reference bindings extend a temporary's lifetime.
