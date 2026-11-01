---
id: partial-specialization
title: Partial Template Specialization
sidebar_label: Partial Specialization
sidebar_position: 2
tags: [c++, templates, partial-specialization, metaprogramming]
---

# Partial Template Specialization

A [full specialization](./full-specialization.md) replaces a template for one exact set of
arguments. A **partial specialization** replaces it for a *pattern*: every pointer type, every pair
whose two types are equal, every `std::vector<T, A>`. It still has template parameters of its own,
and the compiler deduces them by matching the pattern against the arguments. This is the mechanism
behind most of [`<type_traits>`](../type-traits.md) and behind detecting "is this a container of
something". This page is the canonical home for how partial specializations are written, matched
and ranked.

**Prerequisites:** [Class templates](../class-templates.md),
[template argument deduction](../template-argument-deduction.md).

Only **class templates** and **variable templates** *(C++14)* can be partially specialized.
Function templates cannot; use [overloading](#functions-overload-instead) instead.

## Writing a pattern

The specialization has its own `template <...>` list, and after the template name an argument list
written in terms of those parameters. That argument list is the pattern.

```cpp title="pair_kind.cpp" showLineNumbers
#include <iostream>

template <typename T, typename U>
struct Pair {                       // primary template
    static constexpr const char* kind = "different types";
};

template <typename T>
struct Pair<T, T> {                 // partial specialization: both arguments equal
    static constexpr const char* kind = "same type";
};

template <typename T, typename U>
struct Pair<T*, U*> {               // partial specialization: both pointers
    static constexpr const char* kind = "two pointers";
};

int main() {
    std::cout << Pair<int, double>::kind << '\n'      // different types
              << Pair<int, int>::kind << '\n'         // same type
              << Pair<int*, char*>::kind << '\n';     // two pointers
    // Pair<int*, int*>::kind;  // error: ambiguous, both partial specializations match
}
```

```text
different types
same type
two pointers
```

As with full specialization, each partial specialization is a separate class definition and
inherits nothing from the primary template. The number of the specialization's own parameters is
unrelated to the primary's: `Pair<T, T>` has one parameter, `Pair<T*, U*>` two.

## How the compiler picks one

For `Pair<X, Y>` the compiler:

1. **Matches** every partial specialization against `<X, Y>` by deducing its parameters, exactly as
   it would deduce a function template's parameters from arguments. Specializations that don't match
   drop out.
2. If **none** match, it uses the primary template.
3. If **one** matches, it uses that.
4. If **several** match, it uses the **most specialized** one: specialization A is more specialized
   than B if every argument list A accepts is also accepted by B, but not the other way round. If no
   single one is more specialized than all the others, the program is ill-formed (ambiguous).

<Walkthrough title="Choosing a definition for Pair<int*, int*>" accent="violet">
  <Step title="Match each pattern">

| Specialization | Deduction | Matches? |
|---|---|---|
| `Pair<T, T>` | `T = int*` | yes |
| `Pair<T*, U*>` | `T = int`, `U = int` | yes |

  </Step>
  <Step title="Compare the matches">

Every `Pair<T, T>` is not a pair of pointers, and every `Pair<T*, U*>` does not have two equal types.
Neither pattern's set contains the other, so neither is more specialized: <StepChange>ambiguous</StepChange>.
GCC 15: `ambiguous template instantiation for 'struct Pair<int*, int*>'`. Clang 21:
`ambiguous partial specializations of 'Pair<int *, int *>'`.

  </Step>
  <Step title="Add a tie-breaker">

Adding `template <typename T> struct Pair<T*, T*>` resolves it. That pattern accepts only pairs that
both `Pair<T, T>` and `Pair<T*, U*>` accept, so it is more specialized than each and
<StepChange>wins</StepChange>.

  </Step>
</Walkthrough>

```cpp title="tie_breaker.cpp" showLineNumbers {4}
#include <iostream>

template <typename T, typename U> struct Pair     { static constexpr int id = 0; };
template <typename T>             struct Pair<T, T>   { static constexpr int id = 1; };
template <typename T, typename U> struct Pair<T*, U*> { static constexpr int id = 2; };
template <typename T>             struct Pair<T*, T*> { static constexpr int id = 3; };  // more specialized than 1 and 2

int main() { std::cout << Pair<int*, int*>::id << '\n'; }   // 3
```

## Patterns you can match

The pattern can take apart any compound type: cv-qualifiers, pointers, references, arrays (deducing
the bound), function types, and instances of other templates.

```cpp title="describe.cpp" showLineNumbers
#include <cstddef>
#include <iostream>
#include <map>
#include <string>
#include <vector>

template <typename T>
struct Describe { static void print() { std::cout << "scalar\n"; } };

template <typename T>
struct Describe<const T> { static void print() { std::cout << "const "; Describe<T>::print(); } };

template <typename T, std::size_t N>
struct Describe<T[N]> { static void print() { std::cout << "array of " << N << ' '; Describe<T>::print(); } };

template <typename R, typename... Args>
struct Describe<R(*)(Args...)> {
    static void print() { std::cout << "function pointer taking " << sizeof...(Args) << " args\n"; }
};

template <typename T, typename A>
struct Describe<std::vector<T, A>> { static void print() { std::cout << "vector of "; Describe<T>::print(); } };

template <typename K, typename V, typename C, typename A>
struct Describe<std::map<K, V, C, A>> { static void print() { std::cout << "map\n"; } };

int main() {
    Describe<int>::print();                    // scalar
    Describe<const int>::print();              // const scalar
    Describe<int[4]>::print();                 // array of 4 scalar
    Describe<void (*)(int, char)>::print();    // function pointer taking 2 args
    Describe<std::vector<double>>::print();    // vector of scalar
    Describe<std::map<int, std::string>>::print(); // map
}
```

Two details in that listing matter in practice:

- `std::vector` has two template parameters (element and allocator), so the pattern is
  `std::vector<T, A>`. Writing `std::vector<T>` also works for the default allocator, because the
  default argument is filled in before matching, but it misses vectors with a custom allocator.
- The specializations recurse into `Describe<T>`. Traits are built this way: strip one layer, ask
  again.

### Matching any template: template template parameters

To match "any class template instantiation" without listing each one, deduce the template itself:

```cpp title="elem.cpp" showLineNumbers
#include <iostream>
#include <list>
#include <vector>

template <typename T>
struct Elem { static constexpr bool is_container = false; };

template <template <typename...> class C, typename T, typename... Rest>
struct Elem<C<T, Rest...>> { static constexpr bool is_container = true; using type = T; };

static_assert(Elem<std::vector<int>>::is_container);
static_assert(Elem<std::list<char>>::is_container);
static_assert(!Elem<int>::is_container);

// overload instead of partially specializing a function template
template <typename T> const char* kind(T)  { return "value"; }
template <typename T> const char* kind(T*) { return "pointer"; }

int main() { int x = 0; std::cout << kind(x) << ' ' << kind(&x) << '\n'; }
```

Declaring `C` as `template <typename...> class` lets it match templates with any number of type
parameters. With `template <typename> class C` and pattern `C<T>`, `std::vector<int>` (really
`std::vector<int, std::allocator<int>>`) did not match before C++17; since C++17
([P0522R0](https://wg21.link/p0522r0)) a template with defaulted extra parameters may bind to a
one-parameter template template parameter, so it does. The pattern still only matches class
templates whose parameters are all types: `std::array<T, N>` has a non-type parameter and needs its
own specialization.

## The standard traits are partial specializations

Most of `<type_traits>` is a primary template that gives the default answer plus partial
specializations for the matching patterns. Three of them, in full:

```cpp title="mini_traits.cpp" showLineNumbers
template <typename T> struct remove_ref      { using type = T; };
template <typename T> struct remove_ref<T&>  { using type = T; };
template <typename T> struct remove_ref<T&&> { using type = T; };

template <bool B, typename T, typename F> struct conditional           { using type = T; };
template <typename T, typename F>         struct conditional<false, T, F> { using type = F; };

template <typename T> constexpr bool is_ptr = false;      // variable template (C++14)
template <typename T> constexpr bool is_ptr<T*> = true;   // partial specialization of it

static_assert(__is_same(remove_ref<int&&>::type, int));
static_assert(__is_same(conditional<false, int, double>::type, double));
static_assert(is_ptr<int*> && !is_ptr<int>);

int main() {}
```

`__is_same` is a GCC/Clang built-in, used here only to keep the example free of `<type_traits>`.
Real code writes `std::is_same_v`. Note that `conditional<false, T, F>` specializes on a non-type
argument: patterns can fix values as well as types.

## Functions: overload instead

`template <typename T> void kind<T*>(T*)` is a syntax error; function templates cannot be partially
specialized. The two overloads of `kind` in `elem.cpp` above do the same job: for `kind(&x)` both
match, and partial ordering of function templates picks `kind(T*)` as more specialized. If the
behaviour has to live in a class (for example because it needs a nested type), forward the function
to a static member of a partially specialized class template.

## References

- [cppreference: Partial template specialization](https://en.cppreference.com/w/cpp/language/partial_specialization)
- [cppreference: Template template arguments](https://en.cppreference.com/w/cpp/language/template_parameters#Template_template_arguments)
- [P0522R0: Matching of template template-arguments excludes compatible templates](https://wg21.link/p0522r0)
