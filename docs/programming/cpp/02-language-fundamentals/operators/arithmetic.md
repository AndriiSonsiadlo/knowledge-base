---
id: arithmetic-operators
title: Arithmetic Operators
sidebar_label: Arithmetic
sidebar_position: 1
tags: [c++, operators, arithmetic]
---

# Arithmetic Operators

The arithmetic operators look like school maths, and for small positive numbers they behave like it.
The differences show up at the edges: integer division throws away the fraction, `%` has a sign
rule, signed overflow is undefined behaviour, and both operands are converted to a common type
*before* the operation runs. This page covers those edges.

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md),
[Fundamental Types](../../03-types-and-values/fundamental-types.md).

## The operators

| Operator | Name | Notes |
|---|---|---|
| `a + b`, `a - b` | addition, subtraction | also unary `+a`, `-a` |
| `a * b` | multiplication | |
| `a / b` | division | integer division when both operands are integers |
| `a % b` | remainder | integers only; for floating point use `std::fmod` from `<cmath>` |
| `++a`, `a++` | increment | prefix and postfix differ (see below) |
| `--a`, `a--` | decrement | |
| `a += b`, `a -= b`, … | compound assignment | `a = a + b`, but `a` is evaluated once |

## Integer division truncates

The **operand types** decide which division runs, not the type of the variable you store into.

```cpp
int    a = 7 / 2;                        // 3    two ints: integer division
double b = 7 / 2;                        // 3.0  still integer division, converted afterwards
double c = 7.0 / 2;                      // 3.5  one double operand: floating division
double d = static_cast<double>(7) / 2;   // 3.5  convert explicitly when both are variables
```

Integer division **truncates toward zero**: `-7 / 2` is `-3`, not `-4`. This has been guaranteed
since C++11; before that, the direction for negative operands was implementation-defined.

## Remainder and its sign

`a % b` gives the remainder that goes with truncating division, so this identity always holds
(for `b != 0`):

$$(a / b) \cdot b + a \,\%\, b = a$$

The result therefore has the **sign of the left operand**:

```cpp
 7 %  3    //  1
-7 %  3    // -1    sign of the left operand
 7 % -3    //  1
-7 % -3    // -1
```

That makes `i % n` a bad way to wrap an index that can go negative: `-1 % 5` is `-1`, not `4`. Add
`n` and take the remainder again:

```cpp
int wrap(int i, int n) { return ((i % n) + n) % n; }   // wrap(-1, 5) == 4, for n > 0
```

Integer division or remainder **by zero is undefined behaviour**, not an exception you can catch.
Floating-point division by zero follows IEEE 754 on mainstream platforms (`1.0 / 0.0` is infinity),
but check `d != 0` before integer division.

## Increment and decrement

Both forms add one to the variable. They differ in the value the expression **produces**:

```cpp
int a = 5;
int x = ++a;   // prefix:  a becomes 6, expression yields the new value -> x == 6
int b = 5;
int y = b++;   // postfix: b becomes 6, expression yields the old value -> y == 5
```

On a plain `int` used as a statement of its own (`++i;` or `i++;`), the two compile to the same
code. For class types such as iterators, postfix has to copy the old value to return it, so use
prefix (`++it`) when you do not need the old value.

Do not modify a variable with `++` and also use it elsewhere in the same expression: `i++ + i` is
undefined. See [Order of Evaluation](./evaluation-order.md).

## Mixed types: conversions happen first

Before a binary arithmetic operator runs, both operands go through the **usual arithmetic
conversions**:

<Diagram title="What happens to the operands of a + b" accent="violet">
  <DiagramRow>
    <DiagramNode title="Operands">e.g. `char` and `unsigned`</DiagramNode>
    <DiagramArrow direction="right" label="1" />
    <DiagramNode title="Integral promotion">`bool`, `char`, `short` become `int`</DiagramNode>
    <DiagramArrow direction="right" label="2" />
    <DiagramNode title="Common type" accent>Both converted to one type: floating beats integer; for integers, rank and signedness decide</DiagramNode>
    <DiagramArrow direction="right" label="3" />
    <DiagramNode title="Operate">Result has the common type</DiagramNode>
  </DiagramRow>
</Diagram>

Two consequences catch beginners:

- `'A' + 1` has type `int` (value 66 in ASCII), not `char`.
- Mixing `int` and `unsigned int` converts the `int` to `unsigned`. So `-1 < 0u` is **false**:
  `-1` becomes 4294967295 (with 32-bit `unsigned`). `-Wall` warns about this comparison
  (`-Wsign-compare`).

The full rules, including how `long` and `unsigned` combine, are in
[Conversions and Promotions](../../03-types-and-values/conversions-and-promotions.md).

## Overflow

| Type | When the result doesn't fit |
|---|---|
| signed integers (`int`, `long`, …) | **undefined behaviour**. The optimiser may assume it never happens |
| unsigned integers | wraps around modulo 2ⁿ: `0u - 1u` is `UINT_MAX`. Defined, often unintended |
| floating point | becomes infinity (IEEE 754) |

Undefined means you cannot test for overflow after the fact with `if (a + b < a)`: the compiler is
allowed to delete that check. Test before the operation, or use a checked helper:

```cpp
int r;
if (__builtin_add_overflow(a, b, &r)) {   // GCC and Clang builtin, not standard C++
    // handle overflow
}
int s = std::add_sat(a, b);   // (C++26) <numeric>: clamps to INT_MAX / INT_MIN instead
```

[Signedness](../../03-types-and-values/signedness.md) explains the signed/unsigned trade-offs, and
[Undefined Behavior](../../10-error-handling-and-safety/06-undefined-behavior.md) why the compiler
treats overflow this way.

## Key points

- Two integer operands mean integer division, whatever you assign the result to.
- Division truncates toward zero; `%` takes the sign of the left operand.
- Integer division by zero and signed overflow are undefined behaviour. Check first.
- Operands are promoted and converted to a common type before the operation; `int` with `unsigned`
  becomes `unsigned`.
- Prefix `++` yields the new value, postfix the old one; prefer prefix for iterators.

## Related

- [Operator Precedence](./operator-precedence.md) — how `a + b * c` groups
- [Bitwise Operators](./bitwise.md) — shifts, the other way to multiply by powers of two
- [Conversions and Promotions](../../03-types-and-values/conversions-and-promotions.md) — full conversion rules
