---
id: concepts-and-requires
title: Concepts and Requires Expressions
sidebar_label: Concepts & Requires
sidebar_position: 9
tags: [c++, cpp20, concepts, requires, constraints, subsumption]
---

# Concepts and Requires Expressions

An unconstrained template accepts any type and fails, deep inside its body, when the type turns out
not to support some operation. **Concepts** *(C++20)* let a template state its requirements in its
declaration: `template <std::integral T>` accepts only integral types, and a call with `double` is
rejected at the call site with a message naming the unsatisfied concept. They replace most uses of
[SFINAE and `enable_if`](./sfinae-and-enable-if.md), and they add something SFINAE never had: when
two overloads both match, the more constrained one is chosen automatically. This page is the
canonical home for concepts, `requires` clauses, `requires` expressions and subsumption.

**Prerequisites:** [Function templates](./function-templates.md),
[type traits](./type-traits.md). Knowing [SFINAE](./sfinae-and-enable-if.md) helps to see what
concepts replace, but is not required.

## Vocabulary

- A **constraint** is a compile-time boolean condition on template arguments.
- A **concept** is a named constraint: `template <typename T> concept Name = constraint-expression;`.
  `Name<int>` is a `bool` prvalue, so concepts can be used in `static_assert` and `if constexpr` too.
- A **requires clause** attaches a constraint to a template: `requires std::integral<T>`.
- A **requires expression** is a `bool` expression that checks whether some code would compile:
  `requires (T x) { x.size(); }`.

If a template's constraints are not satisfied for the deduced arguments, the template is dropped
from overload resolution, just as a substitution failure would drop it.

## Four ways to constrain a function

All four declarations below mean the same thing:

```cpp title="constrain_syntax.cpp" showLineNumbers
#include <concepts>

// 1. Type-constraint in the template head
template <std::integral T>
T twice1(T x) { return x * 2; }

// 2. requires-clause after the template head
template <typename T>
    requires std::integral<T>
T twice2(T x) { return x * 2; }

// 3. Trailing requires-clause after the declarator
template <typename T>
T twice3(T x) requires std::integral<T> { return x * 2; }

// 4. Abbreviated function template (C++20): each constrained auto is its own parameter
auto twice4(std::integral auto x) { return x * 2; }

int main() {
    return twice1(1) + twice2(1) + twice3(1) + twice4(1) - 8;
    // twice1(1.5);   // error: constraints not satisfied
}
```

Use the short form (1 or 4) when a single concept constrains a single parameter. Use a `requires`
clause (2) when the condition involves several parameters or is not a concept,
`requires std::is_trivially_copyable_v<T> && (sizeof(T) <= 16)`. The trailing form (3) is the only one
available for a non-template member function of a class template:

```cpp title="constrained_member.cpp" showLineNumbers
#include <concepts>

template <typename T>
struct Wrapper {
    T value;
    // Constrained member of a class template: exists only for some T.
    T next() const requires std::integral<T> { return value + 1; }
};

int main() {
    Wrapper<int> w{1};
    Wrapper<double> d{1.0};        // fine: next() is not available, but not needed
    // d.next();                   // error: constraints not satisfied
    return w.next() - 2 + static_cast<int>(d.value) - 1;
}
```

Note that the two `auto` parameters in `void f(std::integral auto a, std::integral auto b)` are
independent template parameters: `f(1, 2L)` deduces `int` and `long`. Write `template <std::integral T> void f(T a, T b)`
when they must match.

## Requires expressions

A requires expression lists **requirements**. It is `true` if every requirement is satisfied and
`false` otherwise. Inside a template, a requirement that is invalid for the given arguments makes the expression `false` instead of causing an error; a requirement that is invalid regardless of the template arguments is still an error. There are four kinds:

```cpp title="sized_range.cpp" showLineNumbers
#include <concepts>
#include <cstddef>
#include <list>
#include <string>
#include <vector>

template <typename C>
concept SizedRange = requires(const C& c) {
    typename C::value_type;                                // type requirement
    c.begin();                                             // simple requirement
    c.end();
    { c.size() } -> std::convertible_to<std::size_t>;      // compound requirement
    requires std::default_initializable<typename C::value_type>;  // nested requirement
};

template <SizedRange C>
auto sum(const C& c) {
    typename C::value_type total{};
    for (const auto& x : c) total += x;
    return total;
}

static_assert(SizedRange<std::vector<int>>);
static_assert(SizedRange<std::list<double>>);
static_assert(!SizedRange<int>);

int main() {
    return sum(std::vector{1, 2, 3}) == 6 && sum(std::list<double>{1.5, 2.5}) == 4.0 ? 0 : 1;
}
```

| Requirement | Syntax | Satisfied when |
|---|---|---|
| Simple | `expr;` | `expr` is a valid expression. It is never evaluated, only checked. |
| Type | `typename T::name;` | The named type exists. |
| Compound | `{ expr } noexcept(opt) -> Concept<Args>;` | `expr` is valid, is `noexcept` if that is written, and `Concept<decltype((expr)), Args...>` holds. |
| Nested | `requires bool-constant;` | The constant expression is `true`. |

Two details trip people up:

- In a compound requirement, the expression's type is inserted as the concept's **first** argument.
  `{ c.size() } -> std::convertible_to<std::size_t>` checks `std::convertible_to<decltype((c.size())), std::size_t>`.
  The arrow takes a type-constraint, not a type: `-> std::size_t` is ill-formed.
- A simple requirement `sizeof(T) <= 8;` only checks that the comparison is a *valid expression*,
  which is always true. To require the *value*, write the nested form `requires sizeof(T) <= 8;`.

The parameter list `(const C& c)` only introduces names to write expressions with. No objects are
created.

### Requires expressions outside concepts

A requires expression is an ordinary `bool` constant, so it can drive `if constexpr` directly:

```cpp title="requires_in_if.cpp" showLineNumbers
#include <concepts>
#include <cstdio>

// requires-expression used as a value: true/false for an invalid-for-T requirement, not an error.
template <typename T>
void show(const T& x) {
    if constexpr (requires { x.print(); })
        x.print();
    else
        std::puts("(no print)");
}

struct P { void print() const { std::puts("P"); } };

int main() {
    show(P{});
    show(42);
}
```

```text
P
(no print)
```

Inside a requires clause you sometimes see `requires requires (T x) { ... }`. The first `requires`
starts the clause, the second starts an inline requires expression. It works, but naming the
expression as a concept is easier to read and to reuse.

## Defining concepts

A concept is a template with no body other than its constraint. It cannot be specialized or
constrained itself, and it can be combined with `&&`, `||` and `!` like any boolean:

```cpp title="fragment"
template <typename T>
concept Number = std::integral<T> || std::floating_point<T>;

template <typename T, typename U>
concept AddableTo = requires(T a, U b) { { a + b } -> std::convertible_to<T>; };
```

With multiple parameters, the short form fills in the **first** one: `template <AddableTo<int> T>`
means `AddableTo<T, int>`.

## Subsumption: picking the more constrained overload

When two constrained templates are both viable and otherwise equally good, the compiler picks the
one whose constraints **subsume** the other's. It decides this by normalizing each constraint into a
conjunction/disjunction of **atomic constraints** and checking logical implication. Concepts are
expanded during normalization; everything else, including a trait like `std::is_signed_v<T>`, is an
opaque atom.

```cpp title="subsumption.cpp" showLineNumbers
#include <concepts>
#include <iostream>

template <typename T>
concept Number = std::integral<T> || std::floating_point<T>;

template <typename T>
concept SignedNumber = Number<T> && std::is_signed_v<T>;   // refines Number

void describe(Number auto)       { std::cout << "number\n"; }
void describe(SignedNumber auto) { std::cout << "signed number\n"; }

int main() {
    describe(5u);    // only Number satisfied
    describe(-5);    // both satisfied; SignedNumber subsumes Number, so it wins
    describe(2.5);   // double is signed: signed number
}
```

```text
number
signed number
signed number
```

<Diagram title="Why SignedNumber subsumes Number" caption="After normalization, SignedNumber is Number plus one more atom, so anything satisfying it satisfies Number." accent="green">
  <DiagramRow>
    <DiagramNode title="Number<T>">integral&lt;T&gt; ∨ floating_point&lt;T&gt;</DiagramNode>
    <DiagramArrow direction="right" label="implied by" />
    <DiagramNode title="SignedNumber<T>" accent>(integral&lt;T&gt; ∨ floating_point&lt;T&gt;) ∧ is_signed_v&lt;T&gt;</DiagramNode>
  </DiagramRow>
</Diagram>

Subsumption only sees through **concepts**. Writing the same logic as raw trait expressions gives
unrelated atoms and an ambiguous call:

```cpp title="no_subsumption.cpp" showLineNumbers
#include <type_traits>

// Same constraints written as trait expressions: not concepts, so no subsumption.
template <typename T>
    requires std::is_integral_v<T>
int pick(T) { return 1; }

template <typename T>
    requires std::is_integral_v<T> && std::is_signed_v<T>
int pick(T) { return 2; }

int main() {
    // pick(-1);   // error: call of overloaded 'pick(int)' is ambiguous
    return pick(1u) - 1;
}
```

Atomic constraints are identical only if they are the same expression at the same place in the
source. The two `std::is_integral_v<T>` atoms are written twice, so the compiler cannot prove that
either constraint implies the other. Wrapping the shared part in a concept fixes it, which is why
the rule of thumb is: build refinements from named concepts.

## Diagnostics

The diagnostic names the concept that failed and the reason. For `twice(1.5)` against
`template <std::integral T> T twice(T)`, Clang 21 reports (source excerpts trimmed):

```text
error: no matching function for call to 'twice'
note: candidate template ignored: constraints not satisfied [with T = double]
note: because 'double' does not satisfy 'integral'
note: because 'is_integral_v<double>' evaluated to false
```

GCC 15 gives the same information as "constraints not satisfied" followed by
`the expression 'is_integral_v<_Tp> [with _Tp = double]' evaluated to 'false'`. With an
unconstrained template the error would instead point at `x * 2` or wherever the body first fails.

## The standard concepts

`<concepts>` and `<iterator>` define the vocabulary most code needs. A selection:

| Group | Concepts |
|---|---|
| Core language | `same_as`, `derived_from`, `convertible_to`, `common_with`, `integral`, `signed_integral`, `unsigned_integral`, `floating_point`, `assignable_from`, `swappable` |
| Object | `destructible`, `constructible_from`, `default_initializable`, `move_constructible`, `copy_constructible`, `movable`, `copyable`, `semiregular`, `regular` |
| Comparison | `equality_comparable`, `totally_ordered`, `three_way_comparable` (`<compare>`) |
| Callable | `invocable`, `regular_invocable`, `predicate`, `relation`, `strict_weak_order` |
| Iterators / ranges | `input_iterator`, `forward_iterator`, `random_access_iterator`, `contiguous_iterator`, `std::ranges::range`, `std::ranges::sized_range`, ... |

Standard concepts also carry **semantic requirements** that the compiler cannot check: a type
satisfying `std::regular` is expected to have copies that compare equal to the original, for
example. A type that compiles against a concept but breaks its semantics makes the program ill-formed, no diagnostic
required ([res.on.requirements]) when used with standard algorithms.

## References

- [cppreference: Constraints and concepts](https://en.cppreference.com/w/cpp/language/constraints)
- [cppreference: Requires expression](https://en.cppreference.com/w/cpp/language/requires)
- [cppreference: Concepts library](https://en.cppreference.com/w/cpp/concepts)
- [P0734R0: Wording paper, C++ extensions for Concepts](https://wg21.link/P0734R0)
