---
id: evaluation-order
title: Order of Evaluation and Sequencing
sidebar_label: Evaluation Order
sidebar_position: 5
tags: [c++, operators, evaluation-order, sequencing, undefined-behavior]
---

# Order of Evaluation and Sequencing

[Precedence](./operator-precedence.md) tells you how an expression **groups**: `f() + g() * h()`
means `f() + (g() * h())`. It says nothing about **when** each part runs. Whether `f` is called
before `g` is a separate question, answered by the **sequencing** rules on this page. Getting it
wrong produces code that prints different things on different compilers, or is undefined behaviour.

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md),
[Operator Precedence](./operator-precedence.md).

## Two jobs every subexpression does

Evaluating an expression involves two kinds of work:

- a **value computation**: working out the result (`i + 1` produces a number, `v[i]` finds an
  element);
- a **side effect**: a change to the program's state (`i++` writes `i`, `std::cout << x` writes
  output, `f()` may do anything).

Sequencing rules say which of these must finish before which others start. Between any two
evaluations A and B there are three possible relationships:

<Diagram title="How two evaluations can be ordered" accent="amber">
  <DiagramRow>
    <DiagramNode icon="arrow-right" title="Sequenced before">A completes before B starts. Fully defined.</DiagramNode>
    <DiagramNode icon="git-branch" title="Indeterminately sequenced">One runs completely before the other, but the compiler picks which. Unspecified, not undefined.</DiagramNode>
    <DiagramNode icon="circle-alert" title="Unsequenced" accent>No order at all; the two may even overlap. Undefined if both touch the same object and one writes.</DiagramNode>
  </DiagramRow>
</Diagram>

The rightmost box is the dangerous one. The rule to remember:

:::danger[The undefined-behaviour rule]
If a side effect on a scalar object (an `int`, a pointer, …) is **unsequenced** relative to another
side effect on the same object, or to a value computation that reads it, the behaviour is undefined.
:::

## What *is* sequenced

These orderings are guaranteed. Everything not listed is unsequenced unless it is a function call
(see below).

| Construct | Guarantee | Since |
|---|---|---|
| `stmt1; stmt2;` | Each **full-expression** (roughly: each statement) is complete before the next starts | always |
| `a && b`, `a \|\| b` | `a` completes before `b`; `b` may be skipped ([short-circuit](./logical.md)) | always |
| `a , b` (comma operator) | `a` completes before `b` | always |
| `c ? x : y` | `c` completes before whichever branch runs | always |
| `f(args)` | All arguments complete before the body of `f` starts | always |
| `f(a, b)` | Arguments are **indeterminately** sequenced: never interleaved, order unspecified | *(C++17)* (before: unsequenced) |
| `f(a, b)` | The expression naming `f` completes before any argument | *(C++17)* |
| `a.b`, `a->b`, `a->*b` | `a` before `b` | *(C++17)* |
| `a[b]` | `a` before `b` | *(C++17)* |
| `a << b`, `a >> b` | `a` before `b` | *(C++17)* |
| `a = b`, `a += b`, … | **`b` before `a`** (right side first) | *(C++17)* |
| overloaded `a @ b` | Same order as the built-in `@` it overloads | *(C++17)* |

The C++17 rows come from proposal [P0145](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0145r3.pdf),
which turned a family of undefined expressions into defined ones. The ordinary arithmetic and
comparison operators were left alone: in `a + b`, `a < b` or `a * b` the two operands are still
unsequenced.

## Traced: `v[i] = i++`

This line was undefined before C++17: the read of `i` on the left and the write by `i++` on the
right were unsequenced. Since C++17 the right operand of `=` is sequenced before the left one, so
it has exactly one meaning.

<Walkthrough title="v[i] = i++ under C++17" caption="Start: v = {10, 20, 30}, i = 0." accent="blue">
  <Step title="Right operand first">

`=` evaluates its right side first. `i++` yields the **old** value `0` and, as its side effect,
sets `i` to <StepChange>`1`</StepChange>.

  </Step>
  <Step title="Then the left operand">

Now `v[i]` is evaluated. `i` is already `1`, so the left side names <StepChange>`v[1]`</StepChange>.

  </Step>
  <Step title="Assign">

The value `0` from step 1 is stored into `v[1]`: `v` becomes <StepChange>`{10, 0, 30}`</StepChange>,
`i == 1`.

  </Step>
</Walkthrough>

Defined does not mean readable. Write `int old = i++; v[i] = old;` if that is what you mean.

## Unspecified versus undefined

The difference matters: unspecified code still has a small set of valid outcomes; undefined code has
none, and the optimiser may assume it never runs.

<Tabs groupId="behaviour">
  <TabItem value="unspecified" label="Unspecified: one of a few outcomes">

```cpp
int a = f() + g();     // f and g both run, in some order
show(j++, j++);        // C++17: (0, 1) or (1, 0) — but j ends as 2 either way
```

The compiler may choose differently per call site, per optimisation level, or per compiler. Your
program is correct only if every allowed order gives an acceptable result.

  </TabItem>
  <TabItem value="undefined" label="Undefined: no meaning at all">

```cpp
int k = i++ + i++;     // two unsequenced writes to i
int m = i + i++;       // unsequenced read and write of i
```

The operands of `+` are unsequenced in every standard version. There is no "right answer" to
discover by testing: the program is broken.

  </TabItem>
</Tabs>

## What actually differs between compilers

The program below exercises each rule. Output from GCC 15.2 and Clang 21.1, both with
`-std=c++17 -Wall -Wextra`:

```cpp title="sequencing.cpp" showLineNumbers
#include <iostream>
#include <map>
#include <string>
#include <vector>

int counter = 0;
int next() { return ++counter; }
void show(int a, int b) { std::cout << "show(" << a << ", " << b << ")\n"; }

int main() {
    std::vector<int> v{10, 20, 30};
    int i = 0;
    v[i] = i++;                                     // defined since C++17
    std::cout << "i=" << i << " v[1]=" << v[1] << '\n';

    std::map<std::string, std::size_t> m;
    m["a"] = m.size();                              // size() runs before the insert
    std::cout << "m[a]=" << m["a"] << '\n';

    std::cout << next() << ' ' << next() << '\n';   // left to right since C++17

    int j = 0;
    // highlight-next-line
    show(j++, j++);                                 // unspecified order
}
```

<Tabs groupId="compiler">
  <TabItem value="gcc" label="GCC 15.2">

```text
i=1 v[1]=0
m[a]=0
1 2
show(1, 0)
```

  </TabItem>
  <TabItem value="clang" label="Clang 21.1">

```text
i=1 v[1]=0
m[a]=0
1 2
show(0, 1)
```

  </TabItem>
</Tabs>

The first three lines are fixed by C++17 and match. The last line is unspecified, and the two
compilers really do disagree. Compiled with `-std=c++14`, GCC also prints `m[a]=1`: there,
`m["a"]` inserted the key before `m.size()` was read.

## Pitfalls

**Relying on argument order.** `std::make_pair(read_int(), read_int())` may read the second value
first. Sequence the calls yourself:

```cpp
int first  = read_int();
int second = read_int();
auto p = std::make_pair(first, second);
```

**Modifying and reading a variable in one expression.** `i++ + i`, `a[i] == i++`, `x = x++ + 1`
before C++17. The fix is always the same: split it into separate statements.

**Assuming "left to right" for everything.** C++17 ordered `<<`, `[]`, `.` and `=`, not `+`, `*`,
`==` or function arguments. `std::cout << f() << g()` is ordered; `f() + g()` is not.

**Trusting the warnings to be complete or exact.** GCC's `-Wsequence-point` and Clang's
`-Wunsequenced` (both enabled by `-Wall`) catch the obvious cases. They miss modifications hidden
inside function calls, and GCC 15 still warns about `v[i] = i++` under `-std=c++17`, where the line
is well-defined. UndefinedBehaviorSanitizer does not check sequencing.

<details>
<summary>The pre-C++11 terminology: sequence points</summary>

C++98/03 described the same ideas with **sequence points**: positions (the end of a full-expression,
after `&&`'s left operand, before a function body…) where all earlier side effects were complete.
C++11 replaced this with the sequenced-before relation, which also covers threads. Old articles that
mention sequence points are describing the same rule, without the C++17 additions.

</details>

## Key points

- Precedence decides grouping; sequencing decides timing. They are independent.
- `&&`, `||`, `,`, `?:` and the end of each statement always order their parts.
- C++17 added left-to-right for `.`, `->`, `[]`, `<<`, `>>` and right-to-left for assignment.
- Function arguments run in an unspecified order; never let one argument depend on another.
- Two unsequenced accesses to one variable, at least one a write, is undefined behaviour.

## References

- [cppreference: Order of evaluation](https://en.cppreference.com/w/cpp/language/eval_order)
- [P0145R3: Refining Expression Evaluation Order for Idiomatic C++](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0145r3.pdf)
- [Undefined Behavior](../../10-error-handling-and-safety/06-undefined-behavior.md) — the wider family this page belongs to
