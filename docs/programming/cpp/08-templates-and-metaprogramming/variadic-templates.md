---
id: variadic-templates
title: Variadic Templates
sidebar_label: Variadic Templates
sidebar_position: 5
tags: [c++, templates, variadic-templates, parameter-pack, pack-expansion, cpp11]
---

# Variadic Templates

A **variadic template** *(C++11)* takes any number of template arguments, zero included. It is how
`std::tuple`, `std::make_unique`, `std::thread`'s constructor and `std::format` accept argument lists
of arbitrary length and type, with full type checking and no C-style `...` varargs. This page is the
canonical home for parameter packs, pack expansion and `sizeof...`. Reducing a pack with an operator
has its own page, [fold expressions](./fold-expressions.md).

**Prerequisites:** [Function templates](./function-templates.md),
[template argument deduction](./template-argument-deduction.md). Forwarding a pack uses
[reference collapsing](../03-types-and-values/value-categories/reference-collapsing.md).

## Parameter packs

A **template parameter pack** is declared with `...` before the name; it stands for zero or more
template arguments. A **function parameter pack** is a function parameter whose type contains a
template parameter pack.

```cpp title="fragment"
template <typename... Ts>          // Ts: template parameter pack (types)
void f(Ts... args);                // args: function parameter pack

template <int... Ns>               // a pack of values works too
struct Ints {};

template <template <typename> class... Ms>   // and a pack of templates
struct Templates {};
```

For `f(1, "a", 2.5)` deduction gives `Ts = {int, const char*, double}` and `args` is three
parameters of those types. A pack is not a value or a type you can use on its own. The only things
you can do with it are **expand** it and ask its size.

## Pack expansion

A **pack expansion** is a *pattern* followed by `...`. The compiler instantiates the pattern once per
pack element, replacing the pack with that element, and joins the results with commas. The pattern
can be any expression or type that mentions the pack, not just the pack's name.

| You write | `Ts = {int, double}`, `args = {a, b}` expands to |
|---|---|
| `g(args...)` | `g(a, b)` |
| `g(h(args)...)` | `g(h(a), h(b))` |
| `g(args * args...)` | `g(a * a, b * b)` |
| `std::tuple<Ts...>` | `std::tuple<int, double>` |
| `std::tuple<std::vector<Ts>...>` | `std::tuple<std::vector<int>, std::vector<double>>` |
| `std::forward<Ts>(args)...` | `std::forward<int>(a), std::forward<double>(b)` |

Expansion is allowed only where the grammar has a comma-separated list: function arguments,
template arguments, braced initializers, base-class lists, member initializer lists, lambda
captures, `using` declarations *(C++17)*, and a few more. If two packs appear in one pattern, they
are expanded in lockstep and must have the same length.

```cpp title="expansion.cpp" showLineNumbers
#include <cstddef>
#include <memory>
#include <string>
#include <tuple>
#include <utility>

template <typename... Ts>
constexpr std::size_t count(const Ts&...) { return sizeof...(Ts); }

template <typename T, typename... Args>
std::unique_ptr<T> make(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

template <typename... Ts>
auto squares(Ts... xs) {
    return std::tuple<Ts...>(xs * xs...);         // pattern xs * xs, expanded per element
}

int main() {
    static_assert(count() == 0 && count(1, 'a', 2.0) == 3);
    auto s = make<std::string>(3, 'x');           // std::string(3, 'x') == "xxx"
    auto t = squares(2, 3.0);
    return (*s == "xxx" && std::get<0>(t) == 4 && std::get<1>(t) == 9.0) ? 0 : 1;
}
```

`sizeof...(Ts)` and `sizeof...(args)` are compile-time constants giving the number of elements.
`make` is essentially `std::make_unique`: `Args&&...` is a pack of
[forwarding references](./template-argument-deduction.md), and `std::forward<Args>(args)...` passes
each argument on with its original value category.

## Processing elements one at a time

There is no way to index a function parameter pack directly before C++26 (P2662 pack indexing,
`args...[0]`). The traditional technique is **recursion**: one overload takes the first element plus
the rest as a pack, handles the first and calls itself on the rest. A non-template overload, or an
`if constexpr` on `sizeof...`, stops it.

```cpp title="recursive_print.cpp" showLineNumbers
#include <iostream>

void print() { std::cout << '\n'; }               // base case: empty pack

template <typename T, typename... Rest>
void print(const T& first, const Rest&... rest) {
    std::cout << first;
    if constexpr (sizeof...(rest) > 0) std::cout << ", ";
    print(rest...);                               // recurse on the tail
}

int main() {
    print(1, "two", 3.5);
    print();
}
```

```text
1, two, 3.5

```

<Walkthrough title='print(1, "two", 3.5)' caption="Each call peels one element off the pack; the pack shrinks until the non-template base case matches.">
  <Step title="First call">

`T = int`, `Rest = {const char*, double}`. Prints `1, ` and calls `print("two", 3.5)`.

  </Step>
  <Step title="Second call">

`T = const char*`, <StepChange>`Rest = {double}`</StepChange>. Prints `two, ` and calls `print(3.5)`.

  </Step>
  <Step title="Third call">

`T = double`, <StepChange>`Rest = {}`</StepChange>. `sizeof...(rest)` is 0, so no comma. Calls `print()`.

  </Step>
  <Step title="Base case">

The non-template `print()` is the only match for zero arguments. It prints the newline. Three
template instantiations plus the base case were generated, one per pack length.

  </Step>
</Walkthrough>

Each step is a separate instantiation, so long packs mean more compile time and, without inlining,
more code. When the per-element work is the same operation every time, a
[fold expression](./fold-expressions.md) *(C++17)* does it in one line with no recursion:
`((std::cout << args), ...)`.

## Indexing a pack with `std::index_sequence`

To pair each element of a tuple with its position, generate a pack of indices and expand over it.
`std::index_sequence<0, 1, ..., N-1>` *(C++14)* is an empty type whose only job is to carry that pack
into a function, where deduction recovers it as `Is...`.

```cpp title="print_tuple.cpp" showLineNumbers
#include <cstddef>
#include <iostream>
#include <tuple>
#include <utility>

template <typename Tuple, std::size_t... Is>
void print_tuple(const Tuple& t, std::index_sequence<Is...>) {
    ((std::cout << (Is == 0 ? "" : " ") << std::get<Is>(t)), ...);
    std::cout << '\n';
}

template <typename... Ts>
void print_tuple(const std::tuple<Ts...>& t) {
    print_tuple(t, std::index_sequence_for<Ts...>{});
}

int main() { print_tuple(std::tuple{1, "hi", 2.5}); }
```

```text
1 hi 2.5
```

`std::index_sequence_for<Ts...>` is `std::make_index_sequence<sizeof...(Ts)>`. For a whole tuple,
`std::apply(f, t)` *(C++17)* does this unpacking for you and calls `f(get<0>(t), get<1>(t), ...)`.

## Variadic class templates

A class template pack is usually consumed by a [partial specialization](./specialization/partial-specialization.md)
that splits off the head, the type-level version of the recursive function above. This is the
classic shape of a hand-written tuple (real implementations store elements through inheritance, recursive or flat depending on the library, rather than nested members, which enables the empty-base optimization):

```cpp title="mini_tuple.cpp" showLineNumbers
#include <cstddef>
// A minimal recursive tuple: one element plus the tuple of the rest.
template <typename... Ts>
struct Tuple {};                                  // empty pack: the end

template <typename Head, typename... Tail>
struct Tuple<Head, Tail...> {
    Head head;
    Tuple<Tail...> tail;
};

template <std::size_t I, typename Head, typename... Tail>
constexpr auto& get(Tuple<Head, Tail...>& t) {
    if constexpr (I == 0) return t.head;
    else return get<I - 1>(t.tail);
}

int main() {
    Tuple<int, double, char> t{1, {2.5, {'c', {}}}};
    get<1>(t) = 4.0;
    return (get<0>(t) == 1 && get<1>(t) == 4.0 && get<2>(t) == 'c') ? 0 : 1;
}
```

<Diagram title="Tuple<int, double, char> as nested members" caption="Each level stores one element and the tuple of the remaining types; the empty Tuple<> ends the chain." accent="violet">
  <DiagramNode title="Tuple<int, double, char>" accent>head: int</DiagramNode>
  <DiagramArrow label="tail" />
  <DiagramNode title="Tuple<double, char>">head: double</DiagramNode>
  <DiagramArrow label="tail" />
  <DiagramNode title="Tuple<char>">head: char</DiagramNode>
  <DiagramArrow label="tail" />
  <DiagramNode title="Tuple<>" dashed>empty primary template</DiagramNode>
</Diagram>

Packs also expand in base-class lists. `struct Overloaded : Fs... { using Fs::operator()...; };`
inherits from every lambda type in `Fs` and pulls in all their call operators *(C++17)*, which is the
usual helper for `std::visit`.

## Constraining a pack

A [concept](./concepts-and-requires.md) can constrain every element, either with a constrained pack
`template <std::integral... Ts>` or with a fold over the constraint, `requires (std::integral<Ts> && ...)`.
Before C++20 the same check is a `static_assert` over a fold or `std::conjunction_v<std::is_integral<Ts>...>`.

## Pitfalls

- **Forgetting the `...`.** Using a pack without expanding it, `g(args)`, is an error: "parameter
  packs not expanded".
- **Ambiguous recursion end.** If the base case is a template that also matches one argument, the
  one-element call can become ambiguous. A non-template zero-argument base, or `if constexpr`, avoids
  that.
- **A deduced pack must come last** among the function parameters it is deduced from. In
  `template <typename... Ts, typename U> void f(Ts..., U)`, `Ts` is in a non-deduced context and is
  deduced as empty.
- **Unspecified evaluation order.** Arguments in an expanded call `g(h(args)...)` are evaluated in unspecified
  order, as with any function call. Braced-init-lists and comma [folds](./fold-expressions.md) are
  evaluated left to right.

## References

- [cppreference: Pack](https://en.cppreference.com/w/cpp/language/pack)
- [cppreference: `sizeof...`](https://en.cppreference.com/w/cpp/language/sizeof...)
- [cppreference: `std::integer_sequence`](https://en.cppreference.com/w/cpp/utility/integer_sequence)
- [P2662R3: Pack indexing](https://wg21.link/P2662R3) (C++26)
