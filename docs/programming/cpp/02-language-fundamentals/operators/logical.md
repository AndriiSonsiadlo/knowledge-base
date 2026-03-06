---
id: logical-operators
title: Logical Operators
sidebar_label: Logical
sidebar_position: 2
tags: [c++, operators, logical, boolean]
---

# Logical Operators

`&&`, `||`, and `!` combine boolean conditions. The detail that matters is **short-circuit
evaluation**: the right operand of `&&`/`||` is evaluated only when it can change the result. That
behaviour is not a micro-optimisation — code routinely *depends* on it for correctness.

:::info Don't confuse with bitwise
`&&`/`||` are logical (operate on truth values, short-circuit). `&`/`|` are
[bitwise](./bitwise.md) (operate per bit, always evaluate both sides). `if (flags & MASK)` and
`if (a && b)` mean very different things.
:::

## The operators

| Operator | Meaning | Short-circuits? | Result type |
|----------|---------|-----------------|-------------|
| `&&`     | logical AND | yes — stops if left is `false` | `bool` |
| `\|\|`   | logical OR  | yes — stops if left is `true`  | `bool` |
| `!`      | logical NOT | n/a | `bool` |

Any operand is contextually converted to `bool` first: `0`, `nullptr`, and `0.0` are `false`;
everything else is `true`.

## Short-circuit evaluation

```cpp showLineNumbers
// Right side runs ONLY if ptr is non-null — this is the guard idiom.
if (ptr != nullptr && ptr->ready()) { /* ... */ }

// Right side runs ONLY if the cheap/likely check fails first.
if (cache_hit(key) || expensive_lookup(key)) { /* ... */ }
```

:::danger Side effects hide here
Because the right operand may not run, never bury required side effects in it.

```cpp
if (validate(x) && log_attempt(x)) { ... }   // log_attempt skipped when validate fails!
```
Order operands so the cheap/most-likely-decisive test comes first, and keep side effects out.
:::

## `!` and double negation

```cpp showLineNumbers
bool ok = !errors.empty();      // readable: "there are errors" negated
bool b  = !!ptr;                // !! forces any value to a clean 0/1 bool
```

## Returns `bool`, not the operand

Unlike Python or JavaScript, C++ `&&`/`||` always yield `bool` — never the surviving operand. There
is no `a || default_value` idiom; use the ternary or `value_or`.

```cpp showLineNumbers
// auto name = user_input || "guest";        // WRONG: this is bool, not a string
auto name = user_input.empty() ? "guest" : user_input;   // correct
```

## Operator overloading caveat

You *can* overload `operator&&` / `operator||` for custom types, but the overloads **lose
short-circuiting** — both operands are always evaluated like a normal function call. This surprises
readers, so it is almost always the wrong choice. See [Operator Overloading](./operator-overloading.md).

## Summary

- `&&`/`||` short-circuit; `&`/`|` (bitwise) do not.
- The skipped operand is genuinely not evaluated — never put required side effects there.
- Result is always `bool` — there is no "return the truthy operand" behaviour.
- Avoid overloading `&&`/`||`; the overload silently drops short-circuiting.

## Related

- [Bitwise Operators](./bitwise.md) — the per-bit cousins
- [Conditional Statements (if, switch)](../control-flow/if-switch.md)
- [Conversions and Promotions](../../03-types-and-values/conversions-and-promotions.md) — contextual conversion to `bool`
