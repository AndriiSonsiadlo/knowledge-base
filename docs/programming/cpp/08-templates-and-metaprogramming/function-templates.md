---
id: function-templates
title: Function Templates
sidebar_label: Function Templates
sidebar_position: 1
tags: [c++, templates, generic-programming, function-templates, instantiation]
---

# Function Templates

A **function template** is a pattern from which the compiler generates functions. You write the
body once with a placeholder type, and each distinct set of template arguments produces a separate
ordinary function, called a **specialization**. This is how `std::max`, `std::sort` and
`std::make_unique` work for any type without virtual calls or `void*`. This page is the canonical
home for declaring function templates, how and when they are instantiated, why definitions live in
headers, and how templates take part in overload resolution.

**Prerequisites:** [Function Overloading](../04-functions-and-call-mechanics/overloading.md),
[Translation Units](../01-toolchain-and-build/translation-units.md).

How the compiler works out `T` from the call arguments has its own page:
[Template Argument Deduction](./template-argument-deduction.md). Restricting which types a template
accepts is covered in [Concepts and Requires](./concepts-and-requires.md).

## Declaring a function template

A template declaration starts with a **template parameter list**. `typename` and `class` mean the
same thing in it.

```cpp title="larger.cpp" showLineNumbers
#include <cstdio>
#include <string>

template <typename T>
T larger(T a, T b) {
    return a < b ? b : a;
}

int main() {
    int i = larger(3, 7);                        // T = int
    double d = larger(2.5, 1.5);                 // T = double
    std::string s = larger(std::string("pear"), std::string("apple"));
    // larger(3, 7.0);                           // error: T deduced as int and as double
    double m = larger<double>(3, 7.0);           // explicit T: both args convert to double
    std::printf("%d %.1f %s %.1f\n", i, d, s.c_str(), m);
}
```

```text
7 2.5 pear 7.0
```

`larger` itself is not a function: you cannot take its address or call it until a `T` is chosen.
`larger<int>` and `larger<double>` are two unrelated functions with different mangled names (see
[Name Mangling](../01-toolchain-and-build/name-mangling.md)). The body only requires that `T` be
copyable and support `<`. Nothing states that requirement until you add a constraint.

## Kinds of template parameters

| Kind | Example | Argument |
|---|---|---|
| Type | `template <typename T>` | any type: `int`, `std::string`, `int*` |
| Non-type (constant) | `template <int N>`, `template <std::size_t N>` | a constant expression of that type. Since C++20 also floating-point types and *structural* class types (all bases and non-static data members public and non-mutable, recursively structural) |
| Template template | `template <template <typename> class C>` | a class template, see [Class Templates](./class-templates.md#default-arguments-and-template-template-parameters) |
| Pack | `template <typename... Ts>` | zero or more arguments, see [Variadic Templates](./variadic-templates.md) |

Parameters can have defaults (`template <typename T = int>`), and since C++20 a function parameter
declared `auto` makes the function an **abbreviated function template**: each `auto` adds an
invented type parameter.

```cpp title="params.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>

template <typename T, std::size_t N>
constexpr std::size_t length(const T (&)[N]) { return N; }   // N deduced from the array type

template <int Factor>
int scale(int x) { return x * Factor; }                     // Factor must be given explicitly

auto twice(auto x) { return x + x; }        // C++20: same as template <typename T> auto twice(T x)

int main() {
    int a[12]{};
    static_assert(length(a) == 12);
    std::printf("%d %d %.1f\n", scale<3>(5), twice(4), twice(1.25));
}
```

```text
15 8 2.5
```

## Instantiation

When a call needs `larger<int>` and no such function exists yet, the compiler **implicitly
instantiates** it: it substitutes `int` for `T` in the declaration and body, and compiles the result
as a normal function. Each translation unit that uses `larger<int>` instantiates its own copy. The
copies are exempt from the one definition rule, so the linker may keep one; on ELF and COFF toolchains (GCC, Clang, MSVC) they are emitted as weak/COMDAT symbols (the same mechanism as
[inline functions](../04-functions-and-call-mechanics/inline-functions.md)).

<Diagram title="One template, several functions" caption="Each set of template arguments produces its own function. The template itself produces no code." accent="blue">
  <DiagramNode variant="pill" accent>template &lt;typename T&gt; T larger(T, T)</DiagramNode>
  <DiagramArrow label="instantiated on use" />
  <DiagramRow>
    <DiagramNode title="larger&lt;int&gt;">int larger(int, int)</DiagramNode>
    <DiagramNode title="larger&lt;double&gt;">double larger(double, double)</DiagramNode>
    <DiagramNode title="larger&lt;std::string&gt;">std::string larger(std::string, std::string)</DiagramNode>
  </DiagramRow>
</Diagram>

### Two-phase checking

A template body is checked twice:

1. **At the definition**, everything that does not depend on `T` is looked up and checked. A call to
   an undeclared non-dependent function is an error even if the template is never used.
2. **At instantiation**, everything that depends on `T` is checked with the real type.

```cpp title="two_phase.cpp" showLineNumbers
template <typename T>
void bad_nondependent(T) {
    // undeclared_function();   // error at the definition: not dependent, looked up now
}

template <typename T>
void bad_dependent(T t) {
    t.no_such_member();         // accepted until instantiated with a type lacking it
}

int main() {
    bad_nondependent(1);
    // bad_dependent(1);        // error here: 'int' has no member 'no_such_member'
}
```

This is why template errors often point deep inside a library: the failing expression is in the
body, and it only fails once your type is substituted. Constraints move that check to the call site.

### Why definitions go in headers

To instantiate `larger<char>` the compiler needs the **body** in the translation unit that makes the
call. If the header only declares the template and the body lives in a `.cpp`, every other
translation unit compiles fine and the link fails:

```text
undefined reference to `char larger<char>(char, char)'
```

The usual fix is to put the whole template in the header. The alternative is **explicit
instantiation**: keep the body in one `.cpp` and list the specializations it must emit. Users can
then only use those.

```cpp title="larger.cpp (fragment)"
#include "larger.h"   // declares: template <typename T> T larger(T a, T b);

template <typename T> T larger(T a, T b) { return a < b ? b : a; }

template int    larger<int>(int, int);      // explicit instantiation definition
template double larger(double, double);    // template argument deduced
```

The opposite tool, `extern template int larger<int>(int, int);` *(C++11)* in a header, tells other
translation units not to instantiate that specialization themselves because one `.cpp` provides it.
It saves compile time, not run time. C++20 [modules](../01-toolchain-and-build/modules.md) also
export templates, but the definition still has to be reachable from the importing code.

## Templates and overloading

Function templates overload with each other and with ordinary functions. For each template,
deduction produces one candidate specialization, and then normal
[overload resolution](../04-functions-and-call-mechanics/overloading.md) ranks the candidates by
their conversions. Two template-specific tie-breakers apply only when conversions are equally good:

1. A **non-template** function beats a template specialization.
2. Between two templates, the **more specialized** one wins (**partial ordering**). `which(T*)` is
   more specialized than `which(T)` because every argument that `T*` accepts, `T` also accepts, but
   not the reverse.

```cpp title="overloads.cpp" showLineNumbers
#include <cstdio>

template <typename T> const char* which(T)  { return "template T"; }
template <typename T> const char* which(T*) { return "template T*"; }
const char* which(int)                      { return "non-template int"; }

int main() {
    int x = 0;
    std::puts(which(x));     // exact match everywhere: the non-template wins
    std::puts(which(&x));    // T* is more specialized than T
    std::puts(which(2.0));   // only the template is an exact match
    std::puts(which('a'));   // template T with T = char beats int (a promotion)
}
```

```text
non-template int
template T*
template T
template T
```

The last line is the common surprise: a non-template is preferred only on a **tie**. A template that
deduces the exact type beats a non-template that needs a promotion or conversion.

### Overload, don't specialize

To handle one type differently, add an overload. `larger("apple", "pear")` deduces
`T = const char*` and compares the two **addresses**, which is meaningless. An ordinary overload
fixes it:

```cpp title="larger_cstr.cpp" showLineNumbers
#include <cstdio>
#include <cstring>

template <typename T>
T larger(T a, T b) { return a < b ? b : a; }

// Overload, not a specialization: compares contents, not addresses.
inline const char* larger(const char* a, const char* b) {
    return std::strcmp(a, b) < 0 ? b : a;
}

int main() {
    std::puts(larger("apple", "pear"));   // pear
}
```

An explicit specialization `template <> const char* larger(const char*, const char*)` would also
work here, but specializations don't take part in overload resolution; see
[Full Specialization](./specialization/full-specialization.md#prefer-overloading-for-function-templates).

## Pitfalls

- **Conflicting deductions.** `larger(3, 7.0)` fails because `T` cannot be both `int` and `double`.
  Convert one argument, name `T` explicitly, or use two parameters.
- **Pointers compare as pointers.** String literals and arrays decay to pointers when passed by
  value, so generic comparisons compare addresses.
- **Name clashes with `std`.** A function template called `max` or `swap` in the global namespace
  can become ambiguous with `std::max`/`std::swap` when argument-dependent lookup also finds the
  `std` one (for example with `std::string` arguments). Pick distinct names or qualify the call.
- **Unconstrained templates are greedy.** A template accepts any type that makes the signature
  valid, then fails inside the body. Constrain it with a
  [concept](./concepts-and-requires.md) so it drops out of overload resolution instead.
- **Code size.** Every distinct argument set is a separate function. Many instantiations of a large
  template increase compile time and binary size.

## References

- [cppreference: Function template](https://en.cppreference.com/w/cpp/language/function_template)
- [cppreference: Explicit instantiation and `extern template`](https://en.cppreference.com/w/cpp/language/class_template#Explicit_instantiation)
- [cppreference: Two-phase name lookup (dependent names)](https://en.cppreference.com/w/cpp/language/dependent_name)
- [cppreference: Abbreviated function template (C++20)](https://en.cppreference.com/w/cpp/language/function_template#Abbreviated_function_template)
