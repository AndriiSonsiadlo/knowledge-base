---
id: type-traits
title: Type Traits
sidebar_label: Type Traits
sidebar_position: 7
tags: [c++, templates, type-traits, metaprogramming]
---

# Type Traits

Generic code often needs to ask a question about its type argument (is `T` integral? can it be
copied with `memcpy`? is its move constructor `noexcept`?) or to compute a related type (`T`
without `const`, the type a by-value parameter would have). The `<type_traits>` header *(C++11)*
answers these at compile time: each trait is a class template whose result is a constant or a type,
with no runtime cost. This page is the canonical home for the standard traits, the `_v`/`_t`
conventions, and writing your own traits.

**Prerequisites:** [Class templates](./class-templates.md),
[partial specialization](./specialization/partial-specialization.md) (how traits are implemented).

Using traits to remove overloads from consideration is [SFINAE and `enable_if`](./sfinae-and-enable-if.md);
since C++20, [concepts](./concepts-and-requires.md) are usually the better way to constrain a
template. Traits remain the building blocks both use.

## The two kinds of trait

<Diagram title="Shape of a trait" accent="violet">
  <DiagramGroup label="Type traits">
    <DiagramNode title="Query (unary / binary)">`std::is_pointer<T>` derives from `std::integral_constant<bool, ...>`. Read `::value`, or `_v`.</DiagramNode>
    <DiagramNode title="Transformation">`std::remove_const<T>` has a member `::type`. Read it, or use `_t`.</DiagramNode>
  </DiagramGroup>
</Diagram>

- A **query** trait derives from `std::integral_constant<bool, B>`, which is `std::true_type` or
  `std::false_type`. Its result is the static member `value`. A few non-bool queries exist too
  (`std::rank`, `std::extent`, `std::alignment_of` give a `std::size_t`).
- A **transformation** trait has a member type alias `type` holding the result.

Two families of helpers cut the boilerplate, and modern code uses them everywhere:

| Helper | Since | Spelled-out form |
|---|---|---|
| `std::remove_const_t<T>` | C++14 | `typename std::remove_const<T>::type` |
| `std::is_pointer_v<T>` | C++17 | `std::is_pointer<T>::value` |

The `_t` form also removes the need for `typename` in dependent contexts, which the `::type` form
requires inside a template (before C++20 relaxed some of those cases).

## Query traits

Every snippet below is one compiled file (`traits.cpp`, GCC 15 and Clang 21, `-std=c++23`); each
line is a `static_assert` that holds.

```cpp title="traits.cpp" showLineNumbers
#include <string>
#include <type_traits>
#include <vector>

struct Base {};
struct Derived : Base {};
enum class Color { red };

// primary type categories: each type is in exactly one
static_assert(std::is_integral_v<bool> && std::is_integral_v<char>);
static_assert(std::is_floating_point_v<long double>);
static_assert(std::is_enum_v<Color> && std::is_class_v<Base>);
static_assert(std::is_pointer_v<int*> && !std::is_pointer_v<int Base::*>);
static_assert(std::is_lvalue_reference_v<int&>);

// composite categories
static_assert(std::is_arithmetic_v<double> && std::is_scalar_v<Color>);
static_assert(std::is_object_v<int> && !std::is_object_v<int&>);

// properties
static_assert(std::is_const_v<const int> && !std::is_const_v<const int&>);
static_assert(std::is_signed_v<int> && std::is_unsigned_v<unsigned>);
static_assert(std::is_trivially_copyable_v<int> && !std::is_trivially_copyable_v<std::string>);
static_assert(std::is_nothrow_move_constructible_v<std::vector<int>>);

// relationships
static_assert(std::is_same_v<int, signed int> && !std::is_same_v<int, const int>);
static_assert(std::is_base_of_v<Base, Derived> && std::is_convertible_v<Derived*, Base*>);
static_assert(std::is_convertible_v<double, int>);           // implicit, even though narrowing
static_assert(!std::is_convertible_v<void*, int*>);

// transformations
static_assert(std::is_same_v<std::remove_cvref_t<const int&>, int>);   // C++20
static_assert(std::is_same_v<std::decay_t<int[3]>, int*>);
static_assert(std::is_same_v<std::decay_t<int(double)>, int (*)(double)>);
static_assert(std::is_same_v<std::add_lvalue_reference_t<int&&>, int&>); // reference collapsing
static_assert(std::is_same_v<std::common_type_t<int, long, short>, long>);
static_assert(std::is_same_v<std::conditional_t<sizeof(long) == 8, long, long long>, long>); // LP64

int main() {}
```

The surprises worth remembering:

- **Categories are disjoint.** A member pointer (`int Base::*`) is not a pointer;
  `std::is_member_pointer_v` covers it. `bool` and `char` are integral.
- **`is_const` looks at the top level only.** `const int&` is a reference, and references are never
  const, so `is_const_v<const int&>` is false. Strip the reference first
  (`std::is_const_v<std::remove_reference_t<T>>`).
- **`is_convertible` means implicit conversion**, including narrowing ones like `double` to `int`.
  It is not "converts without loss".
- **`is_trivially_copyable`** is the condition under which copying the bytes with `std::memcpy` is
  a valid copy. `std::string` owns a heap buffer, so it is not.
- `std::is_pod` is deprecated since C++20; GCC 15 and Clang 21 warn and suggest
  `is_standard_layout_v && is_trivial_v`. Usually what you actually need is one of those two
  separately. What standard layout means is on [class layout](../07-classes-and-oop/class-layout.md).

### Families at a glance

| Family | Examples |
|---|---|
| Primary categories | `is_void`, `is_null_pointer`, `is_integral`, `is_floating_point`, `is_array`, `is_enum`, `is_union`, `is_class`, `is_function`, `is_pointer`, `is_lvalue_reference`, `is_rvalue_reference`, `is_member_object_pointer`, `is_member_function_pointer` |
| Composite categories | `is_arithmetic`, `is_fundamental`, `is_object`, `is_scalar`, `is_compound`, `is_reference`, `is_member_pointer` |
| Properties | `is_const`, `is_volatile`, `is_signed`, `is_unsigned`, `is_abstract`, `is_polymorphic`, `is_final`, `is_aggregate` (C++17), `is_standard_layout`, `is_trivially_copyable` |
| Supported operations | `is_constructible`, `is_default_constructible`, `is_copy_constructible`, `is_move_constructible`, `is_assignable`, `is_destructible`, each with `is_trivially_` and `is_nothrow_` variants; `is_invocable` (C++17) |
| Relationships | `is_same`, `is_base_of`, `is_convertible`, `is_nothrow_convertible` (C++20) |
| Transformations | `remove_const`, `remove_cv`, `remove_reference`, `remove_cvref` (C++20), `remove_pointer`, `add_const`, `add_pointer`, `add_lvalue_reference`, `decay`, `conditional`, `common_type`, `underlying_type`, `invoke_result` (C++17) |
| Logical (C++17) | `conjunction`, `disjunction`, `negation` |

`std::decay_t<T>` is the type a by-value parameter of type `T` would have: references and top-level
cv are removed, arrays become pointers, functions become function pointers. It is what
`std::make_pair` and `std::thread` use to decide what to store. `add_lvalue_reference_t<int&&>`
being `int&` is [reference collapsing](../03-types-and-values/value-categories/reference-collapsing.md).

## Using traits

Traits are consumed in three places: `if constexpr` (choose code), `static_assert` (reject a type
with a readable message), and constraints ([`enable_if`](./sfinae-and-enable-if.md) or
[`requires`](./concepts-and-requires.md)) that choose between overloads.

```cpp title="using_traits.cpp" showLineNumbers {7,17-18}
#include <cstring>
#include <string>
#include <type_traits>

template <typename T>
void copy_n(T* dst, const T* src, std::size_t n) {
    if constexpr (std::is_trivially_copyable_v<T>) {
        if (n) std::memcpy(dst, src, n * sizeof(T));   // one bulk copy
    } else {
        for (std::size_t i = 0; i < n; ++i) dst[i] = src[i];   // run each copy assignment
    }
}

template <typename T>
class Ring {
    static_assert(std::is_nothrow_move_constructible_v<T>,
                  "Ring<T> needs a noexcept move constructor");
    // ...
};

int main() {
    int a[3]{1, 2, 3}, b[3]{};
    copy_n(b, a, 3);
    std::string s[2]{"x", "y"}, t[2];
    copy_n(t, s, 2);
    Ring<std::string> r;
    (void)r;
    return b[2] == 3 && t[1] == "y" ? 0 : 1;
}
```

In `copy_n`, the discarded `if constexpr` branch is not instantiated, so the `memcpy` path is never
compiled for `std::string`. A plain `if` would compile both branches for every `T`; here that still
builds, but in general the wrong branch need not even be valid for `T`. The `static_assert` puts the
requirement at the top of the class, so a bad `T` fails with your message instead of an error deep
inside a member function. Why `noexcept` move matters for containers is on
[copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## Writing your own trait

Follow the standard shape: derive the primary template from `std::false_type`, derive the
specializations from `std::true_type`, and add a `_v` variable template.

```cpp title="is_char_ptr.cpp" showLineNumbers
#include <type_traits>

template <typename T>
struct is_char_ptr : std::false_type {};

template <> struct is_char_ptr<char*>       : std::true_type {};
template <> struct is_char_ptr<const char*> : std::true_type {};

template <typename T>
inline constexpr bool is_char_ptr_v = is_char_ptr<std::remove_cv_t<T>>::value;

static_assert(is_char_ptr_v<const char*> && is_char_ptr_v<char* const>);
static_assert(!is_char_ptr_v<int*>);
static_assert(std::integral_constant<int, 3>::value == 3 && std::true_type{});

int main() {}
```

Deriving from `integral_constant` gives the trait `value`, `value_type`, and a `constexpr`
conversion to `bool`, so `std::true_type{}` can be used directly in a condition. Stripping cv in the
`_v` helper makes `char* const` count as well, matching how the standard traits treat top-level cv.
Traits that ask "does `T` have member `size()`?" are built with `std::void_t`, which is covered with
the [detection idiom](./sfinae-and-enable-if.md).

:::warning[Don't specialize standard traits]
Adding specializations of the `<type_traits>` templates (for example `std::is_integral<MyInt>`) is
undefined behavior, except where the standard explicitly permits it (`std::common_type` and, since
C++20, `std::basic_common_reference`). Write your own trait instead.
:::

## References

- [cppreference: Metaprogramming library (`<type_traits>`)](https://en.cppreference.com/w/cpp/meta)
- [cppreference: `std::integral_constant`](https://en.cppreference.com/w/cpp/types/integral_constant)
- [cppreference: `std::decay`](https://en.cppreference.com/w/cpp/types/decay)
- [cppreference: `std::is_pod` (deprecated)](https://en.cppreference.com/w/cpp/types/is_pod)
