---
id: fold-expressions
title: Fold Expressions
sidebar_label: Fold Expressions
sidebar_position: 6
tags: [c++, templates, fold-expressions, parameter-pack, cpp17]
---

# Fold Expressions

A **fold expression** *(C++17)* reduces a [parameter pack](./variadic-templates.md) with a binary
operator: `(args + ...)` adds every element, `(args && ...)` ANDs them. Before C++17 the same job
needed a recursive template with a base case. A fold does it in one expression and one
instantiation. This page is the canonical home for fold syntax, associativity, empty-pack rules and
the comma-fold idiom.

**Prerequisites:** [Variadic templates](./variadic-templates.md) (packs and pack expansion).

## The four forms

A fold is always written in parentheses. `E` is an expression containing an unexpanded pack, `op`
is one operator used in both places, and `I` is an initial value that contains no pack.

| Form | Syntax | Expands to, for `E = {E1, E2, E3}` |
|---|---|---|
| Unary right fold | `(E op ...)` | `E1 op (E2 op E3)` |
| Unary left fold | `(... op E)` | `(E1 op E2) op E3` |
| Binary right fold | `(E op ... op I)` | `E1 op (E2 op (E3 op I))` |
| Binary left fold | `(I op ... op E)` | `((I op E1) op E2) op E3` |

The side the `...` is on tells you where the nesting goes: `...` on the right means the parentheses
pile up on the right. Elements always keep their order, `E1` first. For associative operators like
`+` on integers the two directions give the same result. For `-`, `/`, `<<` and assignment they do
not:

```cpp title="fold_direction.cpp" showLineNumbers
template <typename... Ts>
constexpr auto right_sub(Ts... xs) { return (xs - ...); }   // x1 - (x2 - (x3 - x4))

template <typename... Ts>
constexpr auto left_sub(Ts... xs) { return (... - xs); }    // ((x1 - x2) - x3) - x4

static_assert(right_sub(10, 4, 3, 1) == 10 - (4 - (3 - 1)));  // 8
static_assert(left_sub(10, 4, 3, 1)  == ((10 - 4) - 3) - 1);  // 2

int main() {}
```

<Walkthrough title="left_sub(10, 4, 3, 1) vs right_sub(10, 4, 3, 1)" caption="Same elements, same order; only the grouping changes.">
  <Step title="Left fold: first step">

`(... - xs)` groups from the left: <StepChange>`10 - 4 = 6`</StepChange>.

  </Step>
  <Step title="Left fold: finish">

`6 - 3 = 3`, then <StepChange>`3 - 1 = 2`</StepChange>.

  </Step>
  <Step title="Right fold: innermost first">

`(xs - ...)` groups from the right, so the innermost pair is the last two: <StepChange>`3 - 1 = 2`</StepChange>.

  </Step>
  <Step title="Right fold: finish">

`4 - 2 = 2`, then <StepChange>`10 - 2 = 8`</StepChange>.

  </Step>
</Walkthrough>

## Allowed operators

Any of the 32 binary operators can fold:

`+ - * / % ^ & | = < > << >> += -= *= /= %= ^= &= |= <<= >>= == != <= >= && || , .* ->*`

Not allowed: `.`, `->`, `[]`, `?:`, and `<=>`. An operand that itself contains an operator with lower
precedence than a cast must be parenthesized: `(args * 2 + ...)` is ill-formed, write
`((args * 2) + ...)`.

## Empty packs

A **unary** fold over an empty pack is ill-formed except for three operators, which have a defined
identity:

| Operator | Value for an empty pack |
|---|---|
| `&&` | `true` |
| `\|\|` | `false` |
| `,` | `void()` |

For everything else, `sum()` with `(args + ...)` fails to compile. Use a **binary** fold with an
explicit initial value, `(0 + ... + args)`, when a pack may be empty. The initial value also fixes the
result type: `(std::string{} + ... + args)` makes every step a `std::string` concatenation, so string
literals can be folded.

## Common patterns

```cpp title="fold_patterns.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <vector>

template <typename... Ts>
auto sum(Ts... xs) { return (0 + ... + xs); }       // binary left fold, safe for empty pack

template <typename... Ts>
bool all(Ts... bs) { return (bs && ...); }          // empty pack -> true

template <typename... Ts>
void print(const Ts&... xs) {
    ((std::cout << xs << ' '), ...);                 // comma fold: left to right
    std::cout << '\n';
}

template <typename... Ts>
void push_all(std::vector<int>& v, Ts... xs) { (v.push_back(xs), ...); }

template <typename... Ts>
std::string concat(const Ts&... xs) { return (std::string{} + ... + xs); }

int main() {
    std::vector<int> v;
    push_all(v, 1, 2, 3);
    print(sum(), sum(1, 2, 3), all(), all(true, false), v.size(), concat("a", "b", "c"));
}
```

```text
0 6 1 0 3 abc 
```

- **Comma fold** `(f(args), ...)` calls `f` once per element. The built-in comma operator sequences
  its operands, so the calls happen left to right. This is the C++17 replacement for the pre-C++17
  trick `int dummy[] = {(f(args), 0)...};`. If an element type overloads `operator,`, cast the
  operand to `void` to keep the built-in operator.
- **`<<` fold** `(std::cout << ... << args)` is a binary left fold with `std::cout` as the initial
  value, printing all elements with no separators. To add a separator, fold over the comma instead,
  as `print` does.
- **`&&` / `||` folds short-circuit** just like the written-out expression: `(check(args) && ...)`
  stops at the first `false`.

## Folding with state

A fold applies one fixed operator, so a relation between neighbouring elements (is the pack
sorted?) needs state carried across steps. A comma or `&&` fold over an expression that updates a
local does it:

```cpp title="is_ascending.cpp" showLineNumbers
#include <iostream>

template <typename T, typename... Ts>
bool is_ascending(T first, Ts... rest) {
    [[maybe_unused]] T prev = first;   // unused when rest is empty
    // comma-separated && fold: each step compares to the previous value, then updates it
    return ((prev <= rest ? (prev = rest, true) : false) && ...);
}

int main() {
    std::cout << is_ascending(1, 2, 2, 5) << is_ascending(1, 3, 2) << is_ascending(7) << '\n';
}
```

```text
101
```

This relies on `&&` evaluating left to right, which it guarantees. Once the logic gets this
involved, a loop over an array is often clearer: `for (T x : {rest...})`, if all elements share a type.

## Folds in constraints

A fold over `&&` or `||` works on compile-time booleans too, which makes it the natural way to
check every type in a pack:

```cpp title="fragment"
template <typename... Ts>
    requires (std::integral<Ts> && ...)        // C++20 constraint
auto add_all(Ts... xs) { return (0 + ... + xs); }

static_assert((std::is_trivially_copyable_v<Ts> && ...));   // C++17, inside a template
```

In a `requires` clause, a fold of concepts is an atomic constraint as a whole in C++20/23, so it does
not take part in [subsumption](./concepts-and-requires.md#subsumption-picking-the-more-constrained-overload)
element by element. C++26 (P2963) changes that for fold expressions of concepts.

## References

- [cppreference: Fold expressions](https://en.cppreference.com/w/cpp/language/fold)
- [N4295: Folding expressions](https://wg21.link/N4295) (original proposal)
- [P2963R3: Ordering of constraints involving fold expressions](https://wg21.link/P2963R3) (C++26)
