---
id: operator-overloading
title: Operator Overloading
sidebar_label: Overloading
sidebar_position: 5
tags: [c++, operators, overloading, custom-types]
---

# Operator Overloading

Operator overloading lets your types reuse built-in operator syntax — `a + b`, `v[i]`, `os << x` —
so user-defined types read like primitives. It is *syntactic sugar over function calls*: `a + b` is
exactly `a.operator+(b)` or `operator+(a, b)`.

:::info Guiding principle
Overload an operator only when its meaning is **obvious and conventional** for the type. `+` on a
`Matrix` is clear; `+` on a `BankAccount` is a riddle. When in doubt, write a named method.
:::

## Member vs non-member

```cpp showLineNumbers
struct Money {
    long cents;
    // Member: left operand is *this, can touch private state directly.
    Money& operator+=(Money rhs) { cents += rhs.cents; return *this; }
};

// Non-member (free function): symmetric, allows conversions on BOTH sides.
// Define + in terms of += so the two never disagree.
Money operator+(Money lhs, Money rhs) { return lhs += rhs; }
```

The rule of thumb:

- **Members:** operators that modify the left operand or are intrinsically tied to it —
  `=`, `+=`, `[]`, `()`, `->`, the increments. `=` `[]` `()` `->` *must* be members.
- **Free functions:** symmetric binary operators (`+`, `==`, `<`). Making them non-members lets
  `1 + obj` convert the left side too, which a member version cannot.

## Canonical forms

**Arithmetic** — implement the compound assignment as a member, derive the binary form from it:

```cpp showLineNumbers
Vec& operator+=(const Vec& r) { x += r.x; y += r.y; return *this; }
friend Vec operator+(Vec l, const Vec& r) { return l += r; }   // l is a copy, reused as result
```

**Comparison (C++20)** — define `operator<=>` once and `==`; the compiler synthesises `<`, `>`,
`<=`, `>=`. This replaces the old six-function boilerplate:

```cpp showLineNumbers
struct Version {
    int major, minor;
    auto operator<=>(const Version&) const = default;   // all six relational ops, for free
    bool operator==(const Version&) const = default;
};
```

**Stream insertion** — always a free function (left operand is the stream, not your type):

```cpp showLineNumbers
std::ostream& operator<<(std::ostream& os, const Money& m) {
    return os << m.cents / 100 << '.' << m.cents % 100;
}
```

**Subscript / call** — members; `operator()` is what makes a *functor*:

```cpp showLineNumbers
struct Grid {
    int& operator[](std::size_t i) { return data[i]; }   // C++23 allows multi-arg operator[]
};
struct Adder { int operator()(int a, int b) const { return a + b; } };   // callable like a function
```

## What you cannot do

- Cannot invent new operators or change **arity**, **precedence**, or **associativity**.
- Cannot overload `::`, `.`, `.*`, `?:`, or `sizeof`.
- At least one operand must be a user-defined type — you cannot redefine `int + int`.

:::warning Overloading `&&`, `||`, `,`
Legal, but these lose their special behaviour: overloaded `&&`/`||` **stop short-circuiting** and
overloaded `,` loses its sequencing. Readers will assume the built-in semantics. Don't.
:::

## Summary

- An overloaded operator is just a function — overload only when the meaning is conventional.
- Members for `=` `[]` `()` `->` and compound assignments; free functions for symmetric binary ops.
- Define `+` from `+=`, and in C++20 define `<=>` + `==` once to get all comparisons.
- `operator<<`/`>>` for streams are free functions taking the stream on the left.
- You can't change precedence/arity or overload `.`, `::`, `?:`; avoid `&&`/`||`/`,`.

## Related

- [Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md) — `operator=`
- [Copy-and-Swap](../../13-idioms-and-design/05-copy-and-swap.md) — exception-safe assignment
- [Lambdas](../../07-classes-and-oop/lambdas.md) — compiler-generated `operator()`
- [Logical Operators](./logical.md) — why overloading `&&`/`||` is a trap
