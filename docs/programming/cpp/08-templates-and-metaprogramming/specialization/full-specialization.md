---
id: full-specialization
title: Full Template Specialization
sidebar_label: Full Specialization
sidebar_position: 1
tags: [c++, templates, specialization, explicit-specialization]
---

# Full Template Specialization

A template generates the same code for every argument. Sometimes one exact argument needs a
different definition: a trait that must answer "what is this type called", a `std::hash` for your
own class, a member function that has to format `bool` differently. A **full specialization** (the
standard calls it an **explicit specialization**) replaces the template's definition for one
complete set of template arguments. This page is the canonical home for `template<>`: what it can
specialize, the declaration-order rule, and why functions should usually be overloaded instead.

**Prerequisites:** [Function templates](../function-templates.md),
[class templates](../class-templates.md).

Specializing for a *pattern* of arguments (`T*`, `Pair<T, T>`) is
[partial specialization](./partial-specialization.md), which only class and variable templates
support.

## Syntax: `template<>` plus every argument

The specialization starts with an empty parameter list, `template <>`, and names the template with
all its arguments filled in. The primary template must already be declared.

```cpp title="type_name.cpp" showLineNumbers
#include <iostream>

template <typename T>
struct TypeName {
    static constexpr const char* value = "unknown";
};

template <>
struct TypeName<int> {
    static constexpr const char* value = "int";
};

template <>
struct TypeName<double> {
    static constexpr const char* value = "double";
};

int main() {
    std::cout << TypeName<int>::value << ' '
              << TypeName<double>::value << ' '
              << TypeName<char>::value << '\n';
}
```

```text
int double unknown
```

A class specialization is a **separate class**. It shares nothing with the primary template: no
members, no base classes, no default member initializers. If `TypeName<int>` forgot to declare
`value`, `TypeName<int>::value` would not compile even though the primary template has one.

<Diagram title="Which definition does TypeName<X> use?" accent="violet">
  <DiagramNode variant="pill" accent>TypeName&lt;X&gt;</DiagramNode>
  <DiagramArrow label="look for an explicit specialization with exactly X" />
  <DiagramGroup label="Candidates">
    <DiagramNode title="TypeName<int>">used when X is int</DiagramNode>
    <DiagramNode title="TypeName<double>">used when X is double</DiagramNode>
    <DiagramNode title="Primary template" dashed>instantiated for every other X</DiagramNode>
  </DiagramGroup>
</Diagram>

## What can be fully specialized

| Entity | Fully specializable | Notes |
|---|---|---|
| Class template | Yes | The whole class is replaced. |
| Member of a class template | Yes | One member function or static data member for one argument; the rest of the class is still generated from the primary template. |
| Function template | Yes | Usually the wrong tool, see [below](#prefer-overloading-for-function-templates). |
| Variable template *(C++14)* | Yes | `template <> constexpr bool is_x<int> = true;` |
| Alias template | No | An alias is not a type of its own. Specialize a class template and alias its `::type`. |

### Specializing one member

When only one behaviour differs, specialize just that member instead of copying the class:

```cpp title="member_spec.cpp" showLineNumbers {13-14}
#include <iostream>

template <typename T>
struct Printer {
    void print(const T& v) const;
    int width = 8;                       // shared by every Printer<T>
};

template <typename T>
void Printer<T>::print(const T& v) const { std::cout << "generic: " << v << '\n'; }

// Explicit specialization of one member: the rest of Printer<bool> is generated as usual.
template <>
void Printer<bool>::print(const bool& v) const { std::cout << (v ? "yes" : "no") << '\n'; }

int main() {
    Printer<int>{}.print(42);
    Printer<bool> pb;
    pb.print(true);
    std::cout << pb.width << '\n';
}
```

```text
generic: 42
yes
8
```

`Printer<bool>` still has `width`, because only `print` was replaced. This form is also how you
give one instantiation a different value for a static data member.

## Declare it before it is used

A specialization must be declared before the first use that would cause the primary template to be
**implicitly instantiated** for the same arguments, in every translation unit that has such a use.
If the compiler sees the use first, the primary template has already been instantiated and the
later specialization contradicts it:

```cpp title="too_late.cpp" showLineNumbers
template <typename T>
struct Limits { static constexpr int bits = 0; };

void use() { (void)Limits<int>::bits; }   // implicitly instantiates Limits<int>

// template <> struct Limits<int> { static constexpr int bits = 32; };
// error: specialization of 'Limits<int>' after instantiation

int main() { use(); }
```

GCC 15 and Clang 21 both reject the commented line. The dangerous case is the one the compiler
cannot see: the specialization lives in a `.cpp` file and another translation unit uses the
template without seeing it. That program is ill-formed with no diagnostic required, and the two
translation units silently disagree about what `Limits<int>` is. Put specializations in the same
header as the primary template, or in a header that every user of that argument includes.

## Specializing standard library templates

You may specialize a standard class template for a program-defined type when the standard allows it.
The everyday case is `std::hash`, so the type can be an `unordered_map` key:

```cpp title="hash_point.cpp" showLineNumbers {8-14}
#include <cstddef>
#include <functional>
#include <string>
#include <unordered_map>

struct Point { int x, y; bool operator==(const Point&) const = default; };

template <>
struct std::hash<Point> {
    std::size_t operator()(const Point& p) const noexcept {
        std::size_t h = std::hash<int>{}(p.x);
        return h ^ (std::hash<int>{}(p.y) + 0x9e3779b9 + (h << 6) + (h >> 2));
    }
};

int main() {
    std::unordered_map<Point, std::string> names{{{0, 0}, "origin"}};
    return names.contains({0, 0}) ? 0 : 1;
}
```

Writing `struct std::hash<Point>` at namespace scope (qualified name) is allowed by CWG 374, a
defect report adopted into C++11; older compilers need the specialization inside
`namespace std { ... }`. Specializing a standard template for types that are not program-defined,
such as `std::hash<std::pair<int, int>>`, is undefined behavior (a specialization of a type the
library already defines, like `std::hash<int>`, is a redefinition error), and
specializing standard **function** templates is not allowed at all since C++20.

## Prefer overloading for function templates

A function template specialization does not take part in overload resolution. The compiler first
picks the best **primary** template among the overloads, and only then checks whether that template
has a specialization for the deduced arguments. A specialization can therefore lose to an overload
it was meant to beat:

```cpp title="spec_vs_overload.cpp" showLineNumbers
#include <iostream>

template <typename T> void f(T)  { std::cout << "f(T)\n"; }     // (1)
template <>           void f(int*) { std::cout << "f<int*>\n"; } // specializes (1)
template <typename T> void f(T*) { std::cout << "f(T*)\n"; }    // (2) overload

int main() {
    int x = 0;
    f(&x);   // overload resolution picks (2); the specialization of (1) is never considered
}
```

```text
f(T*)
```

Both primary templates match `int*`; (2) is more specialized, so it wins, and the explicit
specialization of (1) is ignored. Move the specialization below (2) and it would specialize (2)
instead: which template a function specialization belongs to depends on what is declared above it.

The fix is to write the special case as an ordinary overload, `void f(int*)`. A non-template
function is preferred over a template when both are equally good matches, and it follows the same
rules as every other overload ([overloading](../../04-functions-and-call-mechanics/overloading.md)).
Use specialization for class templates (traits, `std::hash`); use overloads, or `if constexpr` in one
template, for functions.

## When not to specialize

A long list of specializations for `int`, `long`, `short`, `unsigned`... usually means you want a
category, not a list of types. One template with `if constexpr (std::is_integral_v<T>)`
([type traits](../type-traits.md)) or a [concept](../concepts-and-requires.md)-constrained overload
covers every integral type, including ones you forgot.

## References

- [cppreference: Explicit (full) template specialization](https://en.cppreference.com/w/cpp/language/template_specialization)
- [cppreference: Extending the namespace std](https://en.cppreference.com/w/cpp/language/extending_std)
- Herb Sutter, [Why Not Specialize Function Templates?](http://www.gotw.ca/publications/mill17.htm) (C/C++ Users Journal, 2001)
