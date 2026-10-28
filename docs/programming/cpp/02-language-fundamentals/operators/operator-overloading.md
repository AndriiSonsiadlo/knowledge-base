---
id: operator-overloading
title: Operator Overloading
sidebar_label: Overloading
sidebar_position: 6
tags: [c++, operators, overloading, custom-types]
---

# Operator Overloading

Operator overloading lets your own types use operator syntax: `a + b` for vectors, `v[i]` for a
container, `std::cout << x` for printing. An overloaded operator is an ordinary function with a
special name. When the compiler sees `a + b` and an operand has class or enum type, it looks for a
function called `operator+` and rewrites the expression into a call:

<Diagram title="What a + b becomes" accent="blue">
  <DiagramNode variant="pill" accent>a + b</DiagramNode>
  <DiagramArrow label="compiler looks for both" />
  <DiagramRow>
    <DiagramNode title="Member">`a.operator+(b)`</DiagramNode>
    <DiagramNode title="Non-member">`operator+(a, b)`</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="normal overload resolution picks one" />
  <DiagramNode title="Ordinary function call">Precedence, associativity and number of operands stay those of the built-in `+`</DiagramNode>
</Diagram>

**Prerequisites:** [Arithmetic Operators](./arithmetic.md), [Operator Precedence](./operator-precedence.md),
[Function Overloading](../../04-functions-and-call-mechanics/overloading.md). Classes appear in the
examples; [Constructors and Destructors](../../07-classes-and-oop/constructors-and-destructors.md)
covers them properly.

## When to overload

Overload an operator only when its meaning for your type is what a reader would guess: `+` on a
vector or money amount, `==` on almost anything, `[]` on a container, `<<` for printing. `+` on a
`BankAccount` is a riddle; use a named function. Following the built-in conventions matters too:
`+` should not modify its operands, `+=` should return `*this`, `==` and `!=` should agree.

## Member or non-member

```cpp title="money.cpp" showLineNumbers
#include <iostream>

class Money {
public:
    explicit Money(long cents) : cents_{cents} {}

    // Member: modifies the left operand, needs access to private data.
    Money& operator+=(const Money& rhs) { cents_ += rhs.cents_; return *this; }

    // Non-member friend, defined in-class: symmetric, built from +=.
    friend Money operator+(Money lhs, const Money& rhs) { return lhs += rhs; }

    friend bool operator==(const Money&, const Money&) = default;   // (C++20)

    // Stream output: the left operand is the stream, so it cannot be a Money member.
    friend std::ostream& operator<<(std::ostream& os, const Money& m) {
        return os << m.cents_ / 100 << '.' << (m.cents_ % 100 < 10 ? "0" : "") << m.cents_ % 100;
    }

private:
    long cents_;
};

int main() {
    Money a{250}, b{105};
    a += b;
    std::cout << a << ' ' << a + b << ' ' << (a == Money{355}) << '\n';   // 3.55 4.60 1
}
```

| Kind of operator | Make it | Why |
|---|---|---|
| `=`, `[]`, `()`, `->` | member | the language requires it |
| `+=`, `-=`, `++`, `--` and other modifiers | member | they change `*this` |
| `+`, `-`, `*`, `==`, `<`, symmetric binary ops | non-member (often `friend`) | conversions then apply to both operands |
| `<<`, `>>` for streams | non-member | the stream is the left operand |

Implementing `+` in terms of `+=` keeps the two from drifting apart. Taking `lhs` by value gives a
copy to modify and return.

## Comparisons *(C++20)*

Since C++20, defaulting `operator<=>` (three-way comparison) gives `<`, `<=`, `>`, `>=`, and a
defaulted `<=>` also implicitly declares a defaulted `==`, which gives `!=`. Members are compared in
declaration order:

```cpp
#include <compare>

struct Version {
    int major, minor;
    auto operator<=>(const Version&) const = default;   // also brings == and !=
};

static_assert(Version{1, 2} < Version{1, 10});
static_assert(Version{2, 0} != Version{1, 9});
```

Before C++20 you wrote all six comparisons by hand, usually `==` and `<` plus four that call them.

## Increment, subscript, call

```cpp
struct Counter {
    int n = 0;
    Counter& operator++()    { ++n; return *this; }                 // prefix ++c
    Counter  operator++(int) { Counter old = *this; ++n; return old; } // postfix c++: dummy int
};

struct Grid {
    int cells[3][3]{};
    int& operator[](int r, int c) { return cells[r][c]; }   // (C++23) multi-argument []
};

struct Adder {
    int operator()(int a, int b) const { return a + b; }   // a "function object"
};
```

The `int` parameter only tells the compiler which `++` is postfix. A type with `operator()` is a
**function object**: [lambdas](../../07-classes-and-oop/lambdas.md) are compiler-generated ones.
Copy and move assignment (`operator=`) belong to
[Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md).

## What you cannot change

- No new operators, and no changing the number of operands, precedence or associativity. That is
  why `std::cout << a < b` still fails to compile.
- Not overloadable: `::`, `.`, `.*`, `?:`, `sizeof`, `alignof`, `typeid`.
- At least one operand must be a class or enum type: `int + int` is fixed.

## Pitfalls

**Overloading `&&`, `||` or `,`.** Legal, but the overload is a plain function call: both operands
are always evaluated, so [short-circuiting](./logical.md) is lost. Readers will assume the built-in
behaviour; don't.

**`+` that modifies an operand, or `+=` that returns by value.** Both break the conventions
callers rely on (`a + b` leaving `a` changed; `(a += b) += c` modifying a temporary).

**Member `operator==` with a converting constructor.** As a member, `m == 5` compiles via the
conversion but `5 == m` does not *before C++20*. Make symmetric operators non-members. (C++20 also
tries the reversed form `m == 5` for `5 == m`.)

## Key points

- An overloaded operator is a function named `operator@`; `a @ b` becomes a call.
- Modifiers are members; symmetric binary operators are non-members; build `+` from `+=`.
- In C++20, `= default` on `<=>` gives all six comparisons.
- Precedence, arity and associativity never change.
- Never overload `&&`, `||` or `,`.

## Related

- [Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md) — `operator=`
- [Copy-and-Swap](../../13-idioms-and-design/05-copy-and-swap.md) — exception-safe assignment
- [Lambdas](../../07-classes-and-oop/lambdas.md) — compiler-generated `operator()`
