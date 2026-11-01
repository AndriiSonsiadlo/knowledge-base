---
id: sfinae-and-enable-if
title: SFINAE and enable_if
sidebar_label: SFINAE & enable_if
sidebar_position: 8
tags: [c++, templates, sfinae, enable-if, void-t, detection-idiom, metaprogramming]
---

# SFINAE and enable_if

**SFINAE**, "substitution failure is not an error", is the overload-resolution rule that makes it
possible to switch function templates on and off depending on properties of their template
arguments. Before C++20 it was the only way to say "this overload exists only for integral types" or
"only if `T` has a `.size()`". `std::enable_if` and `std::void_t` are the library tools built on it.
This page is the canonical home for SFINAE, `enable_if` and the `void_t` detection idiom.

In C++20 code, prefer [concepts and `requires`](./concepts-and-requires.md): they express the same
constraints directly, give readable diagnostics, and rank overloads by subsumption. You still need
SFINAE to read pre-C++20 code and libraries, and to target older compilers.

**Prerequisites:** [Function templates](./function-templates.md),
[template argument deduction](./template-argument-deduction.md),
[type traits](./type-traits.md), [`decltype`](../03-types-and-values/type-deduction/decltype.md).

## The rule

For each function template in an overload set, the compiler deduces the template arguments and then
**substitutes** them into the function's declaration: its return type, parameter types, and template
parameter list (including default arguments). If that substitution produces an invalid type or
expression, the template is **silently removed** from the candidate set. Only if no viable candidate
remains is there an error.

```cpp title="sfinae_basic.cpp" showLineNumbers
#include <iostream>
#include <vector>

// Candidate 1: the return type names T::value_type.
template <typename T>
typename T::value_type first(const T& c) { return c[0]; }

// Candidate 2: an ordinary function for numbers.
long first(long x) { return x; }

int main() {
    std::vector<int> v{42, 7};
    std::cout << first(v) << ' '    // only candidate 1 is viable
              << first(5) << '\n';  // candidate 1: int::value_type fails -> dropped; uses 2
}
```

```text
42 5
```

<Diagram title="Overload resolution for first(5)" caption="Substitution failure removes a candidate; it does not stop compilation." accent="blue">
  <DiagramNode variant="pill" accent>Call: first(5)</DiagramNode>
  <DiagramArrow label="collect candidates" />
  <DiagramGroup label="Candidates">
    <DiagramNode title="template first(const T&)">Deduce T = int. Substitute: return type int::value_type is invalid.</DiagramNode>
    <DiagramNode title="first(long)">Non-template. int converts to long.</DiagramNode>
  </DiagramGroup>
  <DiagramArrow label="SFINAE drops the template" icon="filter" />
  <DiagramNode title="Viable set: first(long)" accent>Chosen.</DiagramNode>
</Diagram>

### The immediate context

SFINAE covers only failures in the **immediate context** of the substitution: the types and
expressions written in the declaration itself. If substitution requires instantiating some *other*
template, and that instantiation fails inside its own body, the error is hard:

```cpp title="hard_error.cpp" showLineNumbers
#include <type_traits>

template <typename T>
struct Bad {
    static_assert(sizeof(T) == 0, "instantiated");   // hard error if Bad<T> is instantiated
    using type = T;
};

// Substitution needs Bad<T>::type, which instantiates Bad<int>; the static_assert fires
// outside the immediate context, so this is a hard error, not SFINAE.
template <typename T>
typename Bad<T>::type g(T);

void g(...) {}

int main() {
    // g(1);   // error: static assertion failed: instantiated
    g();
}
```

The function body is never part of the immediate context either. A template whose declaration
substitutes fine but whose body does not compile for `T` is selected and then fails to instantiate.
SFINAE constrains declarations, not bodies.

## Expression SFINAE with `decltype`

*(C++11)* Any expression can be put into the declaration through `decltype`, usually as a trailing
return type. If the expression is invalid for the deduced types, the overload disappears:

```cpp title="expression_sfinae.cpp" showLineNumbers
#include <cstddef>
#include <iostream>
#include <vector>

// Expression SFINAE: viable only if c.size() is a valid expression.
template <typename T>
auto length(const T& c) -> decltype(c.size()) { return c.size(); }

template <typename T, std::size_t N>
std::size_t length(const T (&)[N]) { return N; }

int main() {
    std::vector<int> v{1, 2, 3};
    int a[5]{};
    std::cout << length(v) << ' ' << length(a) << '\n';   // 3 5
    // length(42);   // error: no viable candidate (both were removed / did not match)
}
```

To test several expressions but return a different type, use the comma operator inside `decltype`:
`-> decltype(c.begin(), c.end(), void())` requires both calls to be valid and yields `void`.

## `std::enable_if`

`std::enable_if<Cond, T>` *(C++11)* has a member `type` (equal to `T`, default `void`) only when `Cond`
is `true`. Naming `enable_if<false, T>::type` is a substitution failure, so it turns any compile-time
boolean, usually a [type trait](./type-traits.md), into an on/off switch. `std::enable_if_t<Cond, T>`
*(C++14)* is the alias for `::type`. A minimal implementation is just a partial specialization:

```cpp title="fragment"
template <bool B, typename T = void> struct enable_if {};
template <typename T>                struct enable_if<true, T> { using type = T; };
```

It can go in three places. The template-parameter form is the most common because it leaves the
return and parameter types readable and works for constructors, which have no return type:

```cpp title="enable_if.cpp" showLineNumbers
#include <iostream>
#include <type_traits>

// 1. In the return type
template <typename T>
std::enable_if_t<std::is_integral_v<T>, T> twice(T x) { return x * 2; }

// 2. As a non-type template parameter (the usual form)
template <typename T, std::enable_if_t<std::is_floating_point_v<T>, int> = 0>
T half(T x) { return x / 2; }

// Overloads on mutually exclusive conditions
template <typename T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
const char* kind(T) { return "integer"; }

template <typename T, std::enable_if_t<std::is_floating_point_v<T>, int> = 0>
const char* kind(T) { return "floating"; }

int main() {
    std::cout << twice(21) << ' ' << half(3.0) << ' ' << kind(1) << ' ' << kind(1.0) << '\n';
    // twice(1.5);   // error: no matching function
}
```

```text
42 1.5 integer floating
```

The third place, an extra defaulted function parameter `std::enable_if_t<Cond>* = nullptr`, works but
changes the function's arity and is rarely used now.

Combine conditions with ordinary `&&`, `||`, `!` on the `_v` values, or with `std::conjunction_v<...>`,
`std::disjunction_v<...>`, `std::negation<...>` *(C++17)*, which short-circuit instantiation of the
remaining traits.

### Pitfall: the `typename = enable_if_t<...>` form

A popular variant puts `enable_if_t` in a defaulted **type** template parameter. That breaks as soon
as two overloads differ only in the condition, because default template arguments are not part of a
function template's signature:

```cpp title="enable_if_redefinition.cpp" showLineNumbers
#include <type_traits>

// Broken: two templates that differ only in a default template argument
// are the same template declared twice.
//
// template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
// void f(T) {}
// template <typename T, typename = std::enable_if_t<std::is_floating_point_v<T>>>
// void f(T) {}   // error: redefinition of 'template<class T, class> void f(T)'

// Fixed: the condition is part of the template-parameter's type.
template <typename T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
void f(T) {}
template <typename T, std::enable_if_t<std::is_floating_point_v<T>, int> = 0>
void f(T) {}

int main() { f(1); f(1.0); }
```

### Pitfall: conditions on a class's own parameter

Inside a class template, a member function's condition must depend on a template parameter of
**that member**. `T` of the enclosing class is already fixed when the class is instantiated, so
`enable_if_t<is_pointer_v<T>>` in a member declaration is a hard error for every `T` where it is
false. The fix is a defaulted member template parameter `U = T`:

```cpp title="member_enable_if.cpp" showLineNumbers
#include <type_traits>

template <typename T>
struct Box {
    // Not SFINAE: T is fixed once Box<int> is instantiated, so this is a hard error.
    // std::enable_if_t<std::is_pointer_v<T>, int> deref();

    // SFINAE: U is deduced when deref() is called, so the condition is in the immediate context.
    template <typename U = T, std::enable_if_t<std::is_pointer_v<U>, int> = 0>
    auto deref() const { return *value; }

    T value;
};

int main() {
    int x = 5;
    Box<int*> p{&x};
    Box<int> b{3};          // fine: deref() is never instantiated for Box<int>
    return p.deref() - 5 + b.value - 3;
}
```

In C++20 this becomes a trailing `requires std::is_pointer_v<T>` on the member, with no dummy
parameter.

## Detection idiom: `std::void_t`

To ask "does `T` have a `.size()`?" as a compile-time boolean (rather than to drop an overload),
combine SFINAE with [partial specialization](./specialization/partial-specialization.md).
`std::void_t<Ts...>` *(C++17)* is an alias that is always `void`, but substituting into it still
checks that every `Ts` is a valid type:

```cpp title="detection.cpp" showLineNumbers
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

// Primary template: the default answer.
template <typename T, typename = void>
struct has_size : std::false_type {};

// Partial specialization: chosen only if the expression inside void_t is valid.
template <typename T>
struct has_size<T, std::void_t<decltype(std::declval<const T&>().size())>> : std::true_type {};

template <typename T>
inline constexpr bool has_size_v = has_size<T>::value;

static_assert(has_size_v<std::vector<int>>);
static_assert(has_size_v<std::string>);
static_assert(!has_size_v<int>);

int main() {}
```

How the match works for `has_size<std::vector<int>>`, written as `has_size<std::vector<int>, void>`
after the default argument is filled in:

1. The specialization's second argument is `void_t<decltype(...)>`. For a vector the expression is
   valid, so it is `void`, matching the `void` the user's type was given. The specialization is more
   specialized than the primary, so it wins: `true_type`.
2. For `int`, `std::declval<const int&>().size()` is invalid. Substitution into the specialization
   fails, the specialization is discarded (SFINAE applies to partial specialization matching too), and
   the primary template gives `false_type`.

`std::declval<T>()` produces an expression of type `T&&` for use in unevaluated operands like
`decltype`, without needing `T` to be default-constructible. The default argument must be exactly
`void`; that is why `void_t` maps everything to `void`.

Library Fundamentals TS v2 proposed a generic `std::experimental::is_detected` on top of this
pattern. It never became part of the standard; in C++20 a `requires` expression does the same job
inline.

## SFINAE, `if constexpr` and concepts

| Need | C++11/14 | C++17 | C++20 |
|---|---|---|---|
| Remove an overload unless a condition holds | `enable_if_t` in a template parameter | same | `requires` clause / constrained parameter |
| Ask "is this expression valid?" as a `bool` | `void_t`-style detector (hand-written `void_t` in C++11/14) | `std::void_t` detector | `requires { expr; }` |
| Pick one of several code paths inside one function | tag dispatch or overloads | `if constexpr` | `if constexpr` with a `requires` expression |
| Prefer the more specific of two overloads | manual mutual exclusion of conditions | same | automatic, via [subsumption](./concepts-and-requires.md#subsumption-picking-the-more-constrained-overload) |

`if constexpr` *(C++17)* does not remove overloads; it discards the untaken branch *inside* a template
body. It replaces SFINAE when one function can handle every type and only the implementation
differs.

## References

- [cppreference: SFINAE](https://en.cppreference.com/w/cpp/language/sfinae)
- [cppreference: `std::enable_if`](https://en.cppreference.com/w/cpp/types/enable_if)
- [cppreference: `std::void_t`](https://en.cppreference.com/w/cpp/types/void_t)
- [N3911: TransformationTrait Alias `void_t`](https://wg21.link/N3911)
