---
id: logical-operators
title: Logical Operators
sidebar_label: Logical
sidebar_position: 2
tags: [c++, operators, logical, boolean]
---

# Logical Operators

`&&` (and), `||` (or) and `!` (not) combine conditions into a single `true` or `false`. The part
that matters in real code is **short-circuit evaluation**: `&&` and `||` evaluate their right
operand only when the left one has not already decided the result. Code relies on this for
correctness, not just speed: `p != nullptr && p->ready()` is safe only because of it.

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md).

## The operators

| Operator | Alternative token | Result is `true` when… | Right operand evaluated… |
|---|---|---|---|
| `a && b` | `a and b` | both are true | only if `a` is true |
| `a \|\| b` | `a or b` | at least one is true | only if `a` is false |
| `!a` | `not a` | `a` is false | (unary) |

Each operand is first converted to `bool`: zero, a null pointer and `0.0` become `false`;
everything else becomes `true`. The result is always a `bool`. Unlike Python or JavaScript, C++
never returns the operand itself, so `name || "guest"` is a `bool`, not a string. Use the
conditional operator for that: `name.empty() ? "guest" : name`.

## Short-circuit evaluation

The left operand is always evaluated first and completely, including its side effects. Then:

- `&&` stops if the left side is `false`: the whole result must be `false`.
- `||` stops if the left side is `true`: the whole result must be `true`.

The skipped operand is not evaluated at all. Its function calls do not happen; its `++` does not
increment.

<Walkthrough title="Short-circuiting a guarded lookup" caption="if (i < v.size() && v[i] > 0 || fallback()) with v = {5, 7}, i = 2." accent="green">
  <Step title="Group it">

`&&` binds tighter than `||`, so the condition is
`(i < v.size() && v[i] > 0) || fallback()`. The `||` evaluates its left operand, the `&&`, first.

  </Step>
  <Step title="Left of &&">

`i < v.size()` is `2 < 2`, which is <StepChange>`false`</StepChange>.

  </Step>
  <Step title="&& short-circuits">

The left side of `&&` is false, so `v[i] > 0` is **not evaluated**. That matters: `v[2]` would read
past the end of the vector. The `&&` yields <StepChange>`false`</StepChange>.

  </Step>
  <Step title="|| needs its right side">

The left of `||` is false, so it cannot decide yet. `fallback()` <StepChange>is called</StepChange>,
and its result becomes the value of the whole condition.

  </Step>
</Walkthrough>

The program below runs the same logic with `i = 0` and `i = 2`, logging every call:

```cpp title="short_circuit.cpp" showLineNumbers
#include <iostream>
#include <vector>

bool in_range(const std::vector<int>& v, std::size_t i) { std::cout << "in_range "; return i < v.size(); }
bool positive(int x)                                     { std::cout << "positive "; return x > 0; }
bool fallback()                                          { std::cout << "fallback "; return true; }

int main() {
    std::vector<int> v{5, 7};
    for (std::size_t i : {0, 2}) {
        // highlight-next-line
        bool r = (in_range(v, i) && positive(v[i])) || fallback();
        std::cout << "-> " << r << '\n';
    }
}
```

```text
in_range positive -> 1
in_range fallback -> 1
```

With `i = 0` the `&&` is true, so `||` never calls `fallback()`. With `i = 2` the range check fails,
`positive(v[2])` is skipped (so `v[2]` is never read), and `fallback()` decides.

## Using short-circuiting on purpose

**Guard first, use second.** Put the check that makes the second operand safe on the left:

```cpp
if (ptr && ptr->ready())             { /* ... */ }   // never dereferences null
if (!s.empty() && s.front() == '#')  { /* ... */ }   // never reads front() of an empty string
if (d != 0 && n / d > limit)         { /* ... */ }   // never divides by zero
```

**Cheap test first.** When neither side is a guard, put the cheaper or more decisive test on the
left: `cache_hit(key) || expensive_lookup(key)`.

## Pitfalls

**Required side effects on the right.** In `if (validate(x) && log_attempt(x))`, nothing is logged
for invalid input. If a call must always happen, make it a separate statement.

**Using `&` or `|` by mistake.** The [bitwise operators](./bitwise.md) evaluate both sides and
combine bits. `if (ptr & ptr->ready())` does not compile for a pointer, but with integers
`a & b` silently means "share a set bit", not "both non-zero": `2 & 1` is `0`, while `2 && 1` is
`true`.

**Mixing `&&` and `||` without parentheses.** `a || b && c` is `a || (b && c)`. It is correct C++,
but readers misread it; GCC and Clang warn with `-Wparentheses`. Add the parentheses.

**`!` binds tightly.** `!x == y` is `(!x) == y`, not `!(x == y)`. Write `x != y`.

**Overloaded `&&` and `||` do not short-circuit.** A class may define `operator&&`, but then it is
an ordinary function call: both operands are always evaluated (left first, since C++17). This
surprises every reader, which is why [Operator Overloading](./operator-overloading.md) advises
against it.

## Key points

- `&&` skips its right operand when the left is false; `||` when the left is true.
- The skipped operand is not evaluated at all: use this for guards, never for required work.
- The left operand, with all its side effects, is complete before the right one starts.
- The result is always `bool`.
- `&&` binds tighter than `||`; parenthesise mixtures anyway.

## Related

- [Bitwise Operators](./bitwise.md) — the per-bit operators that do not short-circuit
- [Order of Evaluation](./evaluation-order.md) — the general sequencing rules `&&`/`||` are part of
- [Conditional Statements](../control-flow/if-switch.md) — where most conditions end up
- [Conversions and Promotions](../../03-types-and-values/conversions-and-promotions.md) — conversion to `bool`
