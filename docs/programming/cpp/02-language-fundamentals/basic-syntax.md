---
id: basic-syntax
title: C++ Basic Syntax
sidebar_label: Basic Syntax
sidebar_position: 1
tags: [c++, syntax, fundamentals, basics]
---

# C++ Basic Syntax

This page is a first tour of what C++ source code looks like: one small, complete program, and the
handful of rules every line follows (statements, blocks, comments, names, whitespace). Each feature
gets a sentence or two and a link to the page that covers it properly, so you can read real C++
before learning any part of it in depth.

**Prerequisites:** none. If you have not compiled a program yet, [What is C++](../00-overview/what-is-cpp.md)
shows the one-line build command.

## A complete program

```cpp title="average.cpp" showLineNumbers
#include <iostream>     // make std::cout and std::cin available
#include <vector>

// Return the arithmetic mean of the values (0 for an empty vector).
double average(const std::vector<double>& values) {
    if (values.empty()) {
        return 0.0;
    }
    double sum = 0.0;
    for (double v : values) {
        sum += v;
    }
    return sum / values.size();
}

int main() {
    std::vector<double> scores{7.5, 9.0, 6.0};
    std::cout << "Average: " << average(scores) << '\n';
    return 0;
}
```

```text
Average: 7.5
```

<Diagram title="The parts of average.cpp" accent="blue">
  <DiagramNode icon="file-text" title="Preprocessor directives (lines 1–2)">`#include` pastes in the declarations of library facilities before compilation</DiagramNode>
  <DiagramNode icon="square-function" title="Function definition (lines 5–14)">Return type, name, parameters, and a body in braces</DiagramNode>
  <DiagramNode icon="rocket" title="main (lines 16–20)" accent>Where execution starts; its return value is the exit status</DiagramNode>
</Diagram>

Line by line:

- **`#include <iostream>`** is a preprocessor directive: it copies in the header that declares
  `std::cout`. Directives start with `#` and end at the line break, with no `;`. See
  [Preprocessing](../01-toolchain-and-build/preprocessing.md).
- **`double average(const std::vector<double>& values)`** defines a function that takes a vector by
  `const` reference (no copy, no modification) and returns a `double`. See
  [Function Declarations](../04-functions-and-call-mechanics/function-declarations.md).
- **`if`** and **`for`** are control statements: [Conditional Statements](./control-flow/if-switch.md)
  and [Loops](./control-flow/loops.md). `for (double v : values)` visits each element.
- **`sum / values.size()`** divides a `double` by an unsigned integer; the integer is converted to
  `double` first. [Arithmetic Operators](./operators/arithmetic.md) explains when that conversion does
  *not* happen.
- **`int main()`** is the entry point. `return 0;` reports success; see
  [Program Structure](./program-structure.md).
- **`std::cout << ... << '\n'`** writes to standard output; `'\n'` ends the line. See
  [I/O Streams](../09-standard-library/iostreams.md).

## Statements, semicolons and blocks

Code inside a function is a sequence of **statements**, run top to bottom. Most end with `;`:

```cpp
double sum = 0.0;   // declaration statement
sum += v;           // expression statement
return sum;         // jump statement
```

A **block** `{ ... }` groups statements so they can act as one, for example as the body of an `if`
or a function. A block is not followed by `;`. Class and struct definitions are the exception that
needs one: `struct Point { int x, y; };`.

What statements and expressions are, exactly, is in
[Expressions and Statements](./expressions-and-statements.md).

## Comments

```cpp
// A line comment runs to the end of the line.

/* A block comment can span
   several lines. Block comments do not nest. */
```

Comments explain *why*; well-named code already says *what*. A `/* */` around code that itself
contains `*/` ends early, so use `//` or `#if 0 ... #endif` to disable a block of code.

## Whitespace and case

- C++ is **free-form**: spaces, tabs and newlines only separate tokens. `int x=1;` and
  `int   x = 1 ;` are identical. Indentation is for humans; the compiler ignores it.
- C++ is **case-sensitive**: `count`, `Count` and `COUNT` are different names, and `Int` is not a type.
- Inside string literals whitespace is kept exactly: `"a  b"` has two spaces.

The rules for names, keywords and literals are in [Keywords and Tokens](./keywords-and-tokens.md).

## Variables and types: a first look

A variable is declared with a type, a name and, ideally, an initial value:

```cpp
int count = 0;              // whole number
double price = 19.99;       // floating point
char grade = 'A';           // one character, single quotes
bool done = false;          // true or false
std::string name = "Ada";   // text, double quotes (needs #include <string>)
auto total = price * 2;     // auto: type deduced from the initialiser (double)
```

A local variable declared without an initialiser (`int n;`) holds an indeterminate value; reading
it before assigning is undefined behaviour. Always initialise. The types themselves are covered in
[Fundamental Types](../03-types-and-values/fundamental-types.md).

## `std::` and namespaces

Standard library names live in the namespace `std`, so their full names are `std::cout`,
`std::vector`, `std::string`. Writing the prefix keeps it clear where a name comes from. Many
tutorials write `using namespace std;` to drop it; that is acceptable in a tiny program and
harmful in a header. [Program Structure](./program-structure.md#namespaces) explains why.

## Reading on

This folder continues in order:

1. [Program Structure](./program-structure.md): `main`, multiple files, namespaces.
2. [Keywords and Tokens](./keywords-and-tokens.md): names, keywords, literals.
3. [Expressions and Statements](./expressions-and-statements.md): what code is made of.
4. [Operators](./operators/arithmetic.md): arithmetic, logical, bitwise, precedence, evaluation order, overloading.
5. [Control flow](./control-flow/if-switch.md): `if`, `switch`, loops, `goto`.

## Key points

- Statements end with `;`; blocks `{ }` group them and are not followed by `;` (class definitions are).
- `#` lines are preprocessor directives, not statements.
- Whitespace is insignificant outside string literals; letter case is significant.
- Always initialise variables.
- Standard names are in `std::`.
