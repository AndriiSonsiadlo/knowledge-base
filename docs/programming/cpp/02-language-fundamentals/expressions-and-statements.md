---
id: expressions-and-statements
title: Expressions and Statements
sidebar_label: Expressions
sidebar_position: 4
tags: [c++, expressions, statements, syntax, fundamentals]
---

# Expressions and Statements

C++ code is built from two kinds of pieces. An **expression** computes something: `x + 1`,
`f(3)`, `a < b`. A **statement** is a unit of execution: it does something, in order, as part of a
function body (`int x = 5;`, `return x;`, an `if`). Expressions live inside statements, and the
distinction explains rules that otherwise look arbitrary, such as why `x + 1;` compiles and why
`i++ + i++` is broken.

**Prerequisites:** [Basic Syntax](./basic-syntax.md), [Keywords and Tokens](./keywords-and-tokens.md).

<Diagram title="return total + price * qty;" caption="A statement contains one full-expression, which is a tree of subexpressions." accent="blue">
  <DiagramNode title="Statement">`return ... ;` (a jump statement)</DiagramNode>
  <DiagramArrow label="contains" />
  <DiagramNode title="Full-expression" accent>`total + price * qty`: not part of a larger expression</DiagramNode>
  <DiagramArrow label="built from" />
  <DiagramRow>
    <DiagramNode title="Subexpression">`total`</DiagramNode>
    <DiagramNode title="Subexpression">`price * qty`, itself built from `price` and `qty`</DiagramNode>
  </DiagramRow>
</Diagram>

## Expressions

An expression is operators applied to operands, or a single operand on its own: a literal (`42`), a
name (`x`), a function call (`f(3)`), or any combination (`(x + y) * f(3)`). Evaluating it can do
two things:

- produce a **value**, which has a **type** (`x + 1` is an `int` when `x` is an `int`);
- cause **side effects**: changes to the state of the program, such as writing a variable (`x = 5`,
  `++i`) or performing output (`std::cout << x`).

Some expressions exist only for their value (`a + b`), some only for their side effect (a call to a
`void` function), some for both (`i++` yields the old value *and* increments `i`). Assignment is an
expression too: `x = 5` has the value of `x` after the assignment, which is why `a = b = 0` works.

Each expression also has a **value category**: roughly, whether it names an object that has an
address (an *lvalue*, like `x` or `v[0]`) or is a temporary value (a *prvalue*, like `x + 1`). You
can assign to `x` but not to `x + 1`, and that rule is the reason. The full story is in
[Lvalues and Rvalues](../03-types-and-values/value-categories/lvalues-rvalues.md).

### How expressions group and when they run

Two independent sets of rules apply to an expression with several operators:

| Question | Answered by | Page |
|---|---|---|
| Which operands belong to which operator? (`2 + 3 * 4` is `2 + (3 * 4)`) | precedence and associativity | [Operator Precedence](./operators/operator-precedence.md) |
| In what order do the parts run? (is `f()` called before `g()` in `f() + g()`?) | sequencing rules | [Order of Evaluation](./operators/evaluation-order.md) |

The second set is where `i++ + i++` becomes undefined behaviour. Until you have read that page, keep
each side effect in a statement of its own.

### The conditional operator `?:`

`cond ? a : b` evaluates `cond`, then exactly **one** of `a` or `b`, and yields its value. It is the
expression form of `if`/`else`, used where a value is needed:

```cpp
int larger = (x > y) ? x : y;
std::string label = (n == 1) ? "item" : "items";   // both become std::string
```

`a` and `b` must have a common type. Chains (`x > 0 ? 1 : x < 0 ? -1 : 0`) read like `else if`; past
two levels, use an `if` or a small function.

### The comma operator

`a, b` evaluates `a`, discards its value, then evaluates `b` and yields `b`. Its main legitimate use
is a `for` header that updates two variables: `for (int i = 0, j = n - 1; i < j; ++i, --j)`. Note
that the commas in a function call `f(a, b)` and in a declaration `int i = 0, j = 1;` are
separators, not this operator.

## Statements

A function body is a sequence of statements, executed one after another unless a control statement
changes the order. The kinds:

| Statement | Example | Covered in |
|---|---|---|
| Expression statement | `x = 5;` `print(x);` | below |
| Declaration statement | `int x = 5;` `auto it = v.begin();` | [Fundamental Types](../03-types-and-values/fundamental-types.md) |
| Compound statement (block) | `{ int t = a; a = b; b = t; }` | below |
| Selection | `if`, `switch` | [Conditional Statements](./control-flow/if-switch.md) |
| Iteration | `for`, `while`, `do`, range-`for` | [Loops](./control-flow/loops.md) |
| Jump | `break` `continue` `return` `goto` | [Loops](./control-flow/loops.md), [goto](./control-flow/goto-and-labels.md) |
| Labeled | `case 1:` `default:` `done:` | [Conditional Statements](./control-flow/if-switch.md) |
| Null statement | `;` | below |
| `try` block | `try { ... } catch (...) { ... }` | [Exceptions](../10-error-handling-and-safety/01-exceptions.md) |

### Expression statements

Any expression followed by `;` is a statement. The value is discarded; only side effects remain.
That is why `x + 1;` and `x == 5;` compile but do nothing (`-Wall` warns: GCC says "statement has
no effect", Clang "expression result unused"). Marking a function `[[nodiscard]]` *(C++17)* makes the
compiler warn when a caller ignores its result.

Each statement's full-expression is completely evaluated, side effects included, before the next
statement starts. That is the simplest way to make order explicit:

```cpp
int a = read();   // first
int b = read();   // definitely second
use(a, b);
```

### Blocks and scope

A block `{ ... }` groups statements so they can stand where one statement is expected, such as the
body of an `if`. It also opens a **scope**: names declared inside exist only until the closing
brace, and local objects are destroyed there, in reverse order of declaration.

```cpp title="scope.cpp" showLineNumbers
#include <iostream>

int main() {
    int x = 1;
    {
        // highlight-next-line
        int x = 2;               // a new x that hides (shadows) the outer one
        std::cout << x << ' ';   // 2
    }                            // inner x destroyed here
    std::cout << x << '\n';      // 1
}
```

Shadowing is legal but confusing; `-Wshadow` (not in `-Wall`) warns about it. How long objects live
beyond blocks is covered in [Storage Duration](../05-memory-and-object-lifetime/storage-duration.md).

### The null statement

A lone `;` is a statement that does nothing. It is useful as an intentionally empty loop body, best
written on its own line so it is clearly deliberate:

```cpp
while (std::cin.get() != '\n')
    ;                            // discard the rest of the line
```

The accidental version is a classic bug: `if (ready);` or `for (...);` ends the statement at the
semicolon, and the block that follows runs unconditionally, once.

## Pitfalls

**`=` instead of `==` in a condition.** `if (x = 5)` assigns 5 and is always true. GCC and Clang
warn (`-Wparentheses`). If you really mean to assign and test, use an `if` init-statement:
`if (int n = read(); n != 0)`.

**Several side effects on one variable in one expression.** `v[i] = i++;`, `f(i++, i++)`,
`i = i++ + 1`: some are undefined, some unspecified, some fine only since C++17. Split them into
statements. [Order of Evaluation](./operators/evaluation-order.md) explains which is which.

**Thinking a declaration is an expression.** `int x = 5` is not an expression and has no value, so
`if ((int x = 5) > 0)` does not compile. Use the init-statement form above.

## Key points

- Expressions compute a value and may have side effects; statements execute in order.
- `expression;` is a statement that keeps only the side effects.
- Precedence decides grouping; sequencing decides order. They are separate rules.
- `?:` evaluates only one branch; the comma operator evaluates both and keeps the right.
- A block creates a scope; locals die at its closing brace.

## Related

- [Operator Precedence](./operators/operator-precedence.md) — grouping
- [Order of Evaluation](./operators/evaluation-order.md) — timing and undefined behaviour
- [Control Flow](./control-flow/if-switch.md) — the statements that change execution order
