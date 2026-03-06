---
id: operator-precedence
title: Operator Precedence and Associativity
sidebar_label: Precedence
sidebar_position: 4
tags: [c++, operators, precedence]
---

# Operator Precedence and Associativity

**Precedence** decides which operator binds first when an expression mixes operators;
**associativity** decides the order among operators of *equal* precedence. Together they determine
how `a - b - c` or `*p++` parses — before any value is computed.

:::info Don't memorise the whole table
Nobody recalls all 17 levels correctly. The professional habit is: **parenthesise anything
non-obvious.** This page exists so you can resolve a specific ambiguity, not so you can rely on
remembering it.
:::

## Precedence, high to low

Higher rows bind tighter. This is the practical subset; rare operators omitted.

| Level | Operators                                   | Associativity |
|-------|---------------------------------------------|---------------|
| 1     | `::`                                        | left          |
| 2     | `a()` `a[]` `a.b` `a->b` `a++` `a--`        | left          |
| 3     | `++a` `--a` `+a` `-a` `!` `~` `*p` `&x` `sizeof` `(cast)` `new` `delete` | **right** |
| 4     | `.*` `->*`                                  | left          |
| 5     | `*` `/` `%`                                 | left          |
| 6     | `+` `-`                                     | left          |
| 7     | `<<` `>>`                                   | left          |
| 8     | `<=>`                                       | left          |
| 9     | `<` `<=` `>` `>=`                           | left          |
| 10    | `==` `!=`                                   | left          |
| 11    | `&`                                         | left          |
| 12    | `^`                                         | left          |
| 13    | `\|`                                        | left          |
| 14    | `&&`                                        | left          |
| 15    | `\|\|`                                      | left          |
| 16    | `?:` `=` `+=` `-=` … `throw`                | **right**     |
| 17    | `,`                                         | left          |

## The cases that actually bite

**Bitwise vs comparison.** `&` `|` `^` sit *below* `==`/`<`. This misparses constantly:

```cpp showLineNumbers
if (flags & MASK == 0)    // parses as: flags & (MASK == 0)  — almost never intended
if ((flags & MASK) == 0)  // what you meant
```

**Shift vs arithmetic.** `<<` is below `+`:

```cpp showLineNumbers
std::cout << x + y;       // OK: x + y first, then <<
std::cout << (x & 1);     // parens REQUIRED: << outranks &, so x would bind to <<1... write it out
```

**Ternary is very low and right-associative.** It binds looser than almost everything, and chains
nest to the right:

```cpp showLineNumbers
int s = x > 0 ? 1 : x < 0 ? -1 : 0;   // = x>0 ? 1 : (x<0 ? -1 : 0)
```

**Assignment is right-associative**, which is what makes chained assignment work:

```cpp showLineNumbers
a = b = c = 0;            // = a = (b = (c = 0))
```

## Precedence is not evaluation order

A subtle but critical distinction: precedence says how operands *group*, **not** the order in which
subexpressions are *evaluated*. In `f() + g()`, precedence does not say whether `f` or `g` runs
first — and before C++17 it was unspecified. Relying on evaluation order between unsequenced
operands is a classic bug:

```cpp showLineNumbers
int i = 0;
a[i] = i++;               // unsequenced read/write of i — undefined behaviour (pre-C++17)
func(i++, i++);           // order of the two i++ is unspecified
```

See [Undefined Behavior](../../10-error-handling-and-safety/06-undefined-behavior.md) for the
sequencing rules.

## Summary

- Precedence groups operators; associativity orders equal-precedence ones.
- The classic trap: `&`/`|`/`^` bind *looser* than `==`/`<` — always parenthesise masks.
- Ternary and assignment are low-precedence and right-associative.
- Precedence ≠ evaluation order; don't read and modify the same object in one unsequenced expression.
- When in doubt, add parentheses — they cost nothing and document intent.

## Related

- [Expressions and Statements](../expressions-and-statements.md)
- [Bitwise Operators](./bitwise.md) — the precedence trap lives here
- [Undefined Behavior](../../10-error-handling-and-safety/06-undefined-behavior.md) — sequencing
