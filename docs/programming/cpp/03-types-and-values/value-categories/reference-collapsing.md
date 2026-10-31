---
id: reference-collapsing
title: Reference Collapsing and Forwarding References
sidebar_label: Reference Collapsing
sidebar_position: 3
tags: [c++, reference-collapsing, forwarding, templates, cpp11]
---

# Reference Collapsing and Forwarding References

You can't write a reference to a reference (`int& &` is a syntax error), but templates, type aliases
and `decltype` can produce one by substitution: put `T = int&` into `T&&` and you get `int& &&`.
**Reference collapsing** *(C++11)* is the rule that turns such a type back into a single reference.
Together with one special deduction rule it makes **forwarding references** work: a template
parameter `T&&` that accepts both lvalues and rvalues and remembers which one it got, so that
`std::forward` can pass the argument on with its original category. This page is the canonical home
for both mechanisms.

**Prerequisites:** [Lvalues and Rvalues](./lvalues-rvalues.md),
[Template Argument Deduction](../../08-templates-and-metaprogramming/template-argument-deduction.md)

## The collapsing rule

| Formed type | Collapses to |
|---|---|
| `T& &` | `T&` |
| `T& &&` | `T&` |
| `T&& &` | `T&` |
| `T&& &&` | `T&&` |

An lvalue reference anywhere wins. Only an rvalue reference to an rvalue reference stays an rvalue
reference. The rule applies wherever a reference type is *formed* from a name that already denotes
a reference: template type arguments, `typedef`/`using` aliases, `decltype`, and `auto`.

```cpp title="collapse.cpp" showLineNumbers
#include <type_traits>

using LRef = int&;
using RRef = int&&;

static_assert(std::is_same_v<LRef&,  int&>);    // & &   -> &
static_assert(std::is_same_v<LRef&&, int&>);    // & &&  -> &
static_assert(std::is_same_v<RRef&,  int&>);    // && &  -> &
static_assert(std::is_same_v<RRef&&, int&&>);   // && && -> &&

int x = 0;
int& rx = x;
static_assert(std::is_same_v<decltype(rx)&&, int&>);   // decltype yields int&, then & && -> &

int main() {}
```

## Forwarding references

A function parameter of the form `T&&`, where `T` is a template parameter of *that* function
template and is deduced from the call, is a **forwarding reference**. Scott Meyers popularized the
name "universal reference"; the standard term since C++17 is forwarding reference. `auto&&` is one
too.

Deduction for a forwarding reference has one special case
([\[temp.deduct.call\]](https://eel.is/c++draft/temp.deduct.call)): if the argument is an lvalue of
type `A`, `T` is deduced as `A&` instead of `A`. Collapsing then finishes the job:

| Argument | `T` deduced as | Parameter `T&&` becomes |
|---|---|---|
| lvalue `std::string s` | `std::string&` | `std::string& &&` → `std::string&` |
| lvalue `const std::string cs` | `const std::string&` | `const std::string&` |
| rvalue `std::string("tmp")` | `std::string` | `std::string&&` |
| xvalue `std::move(s)` | `std::string` | `std::string&&` |

So `T` itself records the argument's category: a reference type means "was an lvalue", a
non-reference means "was an rvalue".

Not every `&&` next to a template parameter is a forwarding reference:

```cpp title="not-forwarding.cpp" showLineNumbers
#include <vector>

template <class T> void a(T&& x);               // forwarding reference
template <class T> void b(const T&& x);         // rvalue reference to const T: binds rvalues only
template <class T> void c(std::vector<T>&& v);  // rvalue reference to vector<T>

template <class T> struct Box {
    void put(T&& x);                            // T is fixed by Box<T>, not deduced here
    template <class U> void emplace(U&& x);     // forwarding reference
};

int main() {
    int i = 0;
    // b(i);          // error: cannot bind const int&& to an lvalue
    // Box<int>{}.put(i);  // error: put takes int&&
    (void)i;
}
```

## `std::forward` restores the category

Inside the function the parameter has a name, so it is an lvalue whatever was passed. Passing
`arg` on as is would always copy. `std::forward<T>(arg)` (in `<utility>`) uses the information
stored in `T` to cast it back:

```cpp title="forward-sketch.cpp"
// Simplified from the standard library. The real one also has an overload for rvalue arguments.
template <class T>
constexpr T&& forward(std::remove_reference_t<T>& arg) noexcept {
    return static_cast<T&&>(arg);
}
// ...
```

With `T = std::string&` the cast is to `std::string& &&`, which collapses to `std::string&`: an
lvalue. With `T = std::string` it is a cast to `std::string&&`: an xvalue. The parameter type
`remove_reference_t<T>&` is there so that `T` can't be deduced, and the caller must spell
`std::forward<T>` explicitly.

<Diagram title="Perfect forwarding" caption="The caller's category is stored in T and recovered by std::forward." accent="blue">
  <DiagramNode title="Argument">lvalue or rvalue</DiagramNode>
  <DiagramArrow label="special deduction rule" />
  <DiagramNode title="T">`A&` for an lvalue, `A` for an rvalue</DiagramNode>
  <DiagramArrow label="reference collapsing" />
  <DiagramNode title={"Parameter T&&"}>`A&` or `A&&`, but named, so an lvalue</DiagramNode>
  <DiagramArrow label="std::forward<T>" />
  <DiagramNode title="Forwarded expression" accent>lvalue again, or xvalue again</DiagramNode>
</Diagram>

## A traced example

The program below forwards four different arguments to an overload pair. The output is from GCC 15
with `-std=c++23 -Wall -Wextra`; Clang 21 prints the same.

```cpp title="forward.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

void sink(const std::string&) { std::puts("  sink(const std::string&)  copy"); }
void sink(std::string&&)      { std::puts("  sink(std::string&&)       move"); }

template <class T>
void wrapper(T&& arg) {
    std::printf("T = %s\n", std::is_lvalue_reference_v<T> ? "lvalue ref" : "non-reference");
    // highlight-next-line
    sink(std::forward<T>(arg));
}

int main() {
    std::string s = "hi";
    const std::string cs = "hi";
    wrapper(s);
    wrapper(cs);
    wrapper(std::string("tmp"));
    wrapper(std::move(s));
}
```

```text
T = lvalue ref
  sink(const std::string&)  copy
T = lvalue ref
  sink(const std::string&)  copy
T = non-reference
  sink(std::string&&)       move
T = non-reference
  sink(std::string&&)       move
```

<Walkthrough title="Three calls through wrapper" accent="blue">
  <Step title="wrapper(s): an lvalue">

`s` is an lvalue of type `std::string`, so the special rule deduces
<StepChange>`T = std::string&`</StepChange>. The parameter type `T&&` is `std::string& &&`, which
collapses to `std::string&`. `std::forward<std::string&>(arg)` casts to `std::string&`: an lvalue,
so `sink(const std::string&)` is chosen and the string is copied.

  </Step>
  <Step title="wrapper(cs): a const lvalue">

`T = const std::string&`. The `const` is part of the deduced type, so it survives. The forwarded
expression is a <StepChange>`const` lvalue</StepChange>, and only `sink(const std::string&)` can
accept it.

  </Step>
  <Step title='wrapper(std::string("tmp")): a prvalue'>

An rvalue argument uses the ordinary rule: <StepChange>`T = std::string`</StepChange>, no
collapsing, parameter type `std::string&&`. The prvalue is materialized and `arg` binds to it.
Inside, `arg` is an lvalue; `std::forward<std::string>(arg)` casts it to `std::string&&`, an
xvalue, so `sink(std::string&&)` runs.

  </Step>
</Walkthrough>

The fourth call, `wrapper(std::move(s))`, behaves like the third: an xvalue is an rvalue, so
`T = std::string`.

## Common mistakes

- **`std::move` on a forwarding reference.** `sink(std::move(arg))` moves from the caller's lvalue
  `s` in the first call above, silently emptying a variable the caller still owns. Use
  `std::forward<T>` on forwarding references and `std::move` on rvalue references.
- **Forwarding the same argument twice.** After `sink(std::forward<T>(arg))` with an rvalue, `arg`
  may be moved-from. Forward a parameter only on its last use.
- **Expecting `T&&` in a class template member to forward.** In `Box<T>::put(T&&)` the type `T` was
  fixed when `Box<int>` was named, so `put` takes only rvalues. Make the member a template
  (`template <class U> void put(U&&)`) to get forwarding.
- **Assuming `T` is the plain argument type.** After `wrapper(s)`, `T` is `std::string&`. Code that
  writes `T copy = arg;` makes a reference, not a copy. Use `std::remove_cvref_t<T>` *(C++20)* or
  `std::decay_t<T>` when you need the value type.

## Key points

- An lvalue reference wins: only `&& &&` collapses to `&&`.
- `T&&` forwards only when `T` is a template parameter deduced from that very call.
- For an lvalue argument `T` becomes `A&`. That reference type is how `T` remembers the category.
- `std::forward<T>` is a conditional `std::move`: it casts to rvalue only when `T` isn't a reference.

## Related

- [auto](../type-deduction/auto.md): `auto&&` is a forwarding reference deduced by the same rules.
- [decltype(auto)](../type-deduction/decltype-auto.md): returning a forwarded result without
  changing its category.
- [Variadic Templates](../../08-templates-and-metaprogramming/variadic-templates.md): forwarding a
  whole parameter pack with `std::forward<Args>(args)...`.
