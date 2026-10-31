---
id: operator-precedence
title: Operator Precedence and Associativity
sidebar_label: Precedence
sidebar_position: 4
tags: [c++, operators, precedence]
---

# Operator Precedence and Associativity

When an expression mixes operators, the compiler has to decide which operands belong to which
operator before it can compute anything. **Precedence** settles this between different operators
(`*` binds tighter than `+`, so `2 + 3 * 4` is `2 + (3 * 4)`). **Associativity** settles it between
operators of the *same* precedence (`-` groups left to right, so `a - b - c` is `(a - b) - c`).

This page is a lookup reference plus the handful of cases that cause real bugs. It is about
*grouping* only; when each part actually runs is a separate rule, covered in
[Order of Evaluation](./evaluation-order.md).

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md).

## The table

Higher rows bind tighter. "Right" associativity is marked in bold because it is the exception.

| Level | Operators | Associativity |
|---|---|---|
| 1 | `::` | left |
| 2 | `a++` `a--` `f()` `a[]` `a.b` `a->b` `T(a)` `T{a}` | left |
| 3 | `++a` `--a` `+a` `-a` `!` `~` `*p` `&x` `(T)a` `sizeof` `co_await` `new` `delete` | **right** |
| 4 | `.*` `->*` | left |
| 5 | `*` `/` `%` | left |
| 6 | `+` `-` | left |
| 7 | `<<` `>>` | left |
| 8 | `<=>` *(C++20)* | left |
| 9 | `<` `<=` `>` `>=` | left |
| 10 | `==` `!=` | left |
| 11 | `&` (bitwise AND) | left |
| 12 | `^` | left |
| 13 | `\|` | left |
| 14 | `&&` | left |
| 15 | `\|\|` | left |
| 16 | `a ? b : c` `throw` `co_yield` `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `\|=` | **right** |
| 17 | `,` (comma operator) | left |

Three anchors cover most code: **unary > arithmetic > comparison > logical > assignment**. Inside
arithmetic, multiplicative beats additive as in school. The bitwise operators `& ^ |` are the odd
ones out: they sit *below* comparison.

<details>
<summary>Where the table comes from</summary>

The standard does not contain a precedence table. It defines a grammar, and the table is derived
from it (this one matches [cppreference](https://en.cppreference.com/w/cpp/language/operator_precedence)).
The grammar has a few corners a table cannot show: the middle operand of `?:` is parsed as if
parenthesised, so `a ? b , c : d` is legal; and `sizeof (int) * p` means `(sizeof(int)) * p`, not a
cast.

</details>

## Traced: grouping a mixed expression

Take `bool r = 2 + 3 * 4 > 10 && !done;` with `done == false`. The compiler builds the grouping
from the tightest-binding operator outward:

<Walkthrough title="How 2 + 3 * 4 > 10 && !done groups" caption="Each step binds the highest-precedence operator still free." accent="blue">
  <Step title="Unary ! (level 3)">

`!` binds to its operand first.

`2 + 3 * 4 > 10 && `<StepChange>`(!done)`</StepChange>

  </Step>
  <Step title="Multiplicative * (level 5)">

`2 + `<StepChange>`(3 * 4)`</StepChange>` > 10 && (!done)`

  </Step>
  <Step title="Additive + (level 6)">

<StepChange>`(2 + (3 * 4))`</StepChange>` > 10 && (!done)`

  </Step>
  <Step title="Relational > (level 9)">

<StepChange>`((2 + (3 * 4)) > 10)`</StepChange>` && (!done)`

  </Step>
  <Step title="Logical && (level 14)">

<StepChange>`(((2 + (3 * 4)) > 10) && (!done))`</StepChange>

  </Step>
  <Step title="Assignment = (level 16), then evaluate">

The initialiser is the whole expression. With values: `3 * 4` is `12`, `2 + 12` is `14`,
`14 > 10` is `true`, `!done` is `true`, so <StepChange>`r == true`</StepChange>.

  </Step>
</Walkthrough>

The steps show how the expression *groups*, not the order the machine runs it in. Here it makes no
difference, but if the operands were function calls, their call order would be decided by the
[sequencing rules](./evaluation-order.md), not by this table.

## Associativity in practice

Associativity only matters when the same level repeats:

```cpp
a - b - c          // (a - b) - c         left
a = b = c = 0      // a = (b = (c = 0))   right: chained assignment works
x > 0 ? 1 : x < 0 ? -1 : 0   // x > 0 ? 1 : (x < 0 ? -1 : 0)   right: ternary chains like else-if
*p++               // *(p++)              postfix beats prefix: increments the pointer, not *p
-x * y             // (-x) * y            unary beats binary
```

## The cases that cause bugs

**Bitwise operators below comparison.** The classic mask test is misparsed:

```cpp
if (flags & MASK == 0)     // flags & (MASK == 0)  — tests bit 0 against a bool
if ((flags & MASK) == 0)   // what you meant
```

GCC and Clang warn about this with `-Wall` (`-Wparentheses`).

**`<<` on streams binds tighter than comparison and bitwise.** It is still the shift operator,
precedence and all:

```cpp
std::cout << a + b;        // fine: + is level 6, << is level 7
std::cout << (a < b);      // parentheses required
std::cout << a < b;        // (std::cout << a) < b  — does not compile
std::cout << (x & 1);      // parentheses required: << is tighter than &
```

**Shifts below arithmetic.** `1 << n + 1` is `1 << (n + 1)`, not `(1 << n) + 1`.

**Chained comparisons are not range tests.** `0 < x < 10` groups as `(0 < x) < 10`: a `bool`
compared with `10`, which is always `true`. Write `0 < x && x < 10`.

**Assignment inside a ternary.** In C++, `?:` and `=` share a level and group right, so
`cond ? a : b = 1` is `cond ? a : (b = 1)`. It assigns only when `cond` is false. Parenthesise
whichever meaning you intend.

## Key points

- Precedence and associativity decide grouping; they never decide run-time order.
- Unary > arithmetic > shift > comparison > bitwise > logical > ternary/assignment > comma.
- `& ^ |` bind looser than `==` and `<`: always parenthesise mask tests.
- Unary operators, `?:` and assignment group right to left; everything else left to right.
- Overloaded operators keep the built-in precedence, which is why `cout << a < b` fails.
- When a reader would have to look up the table, add parentheses.

## Related

- [Order of Evaluation and Sequencing](./evaluation-order.md) — when each operand runs
- [Bitwise Operators](./bitwise.md) — where the mask-test trap lives
- [Operator Overloading](./operator-overloading.md) — overloads cannot change precedence
