---
id: glvalue-prvalue-xvalue
title: glvalue, prvalue, xvalue
sidebar_label: Value Categories
sidebar_position: 2
tags: [c++, value-categories, glvalue, prvalue, xvalue, cpp11, cpp17]
---

# glvalue, prvalue, xvalue

The lvalue/rvalue split on the [previous page](./lvalues-rvalues.md) leaves one case unexplained:
`std::move(x)` is an rvalue, yet it refers to the existing object `x`, unlike `42`. C++11 named that
case **xvalue** and split every expression into exactly one of three *primary* categories, plus two
*mixed* categories that group them. C++17 then changed what a prvalue *is*, which is the reason
`return T{...};` never copies. This page gives the precise model, a table of which expressions fall
where, and the temporary-materialization rule.

**Prerequisites:** [Lvalues and Rvalues](./lvalues-rvalues.md)

## Two properties, three categories

The categories come from two yes/no questions about an expression:

- **Identity:** does it refer to a particular object or function, one you could compare by address
  with another?
- **Movable:** may the object's resources be taken, because nobody will look at it again?

<Diagram title="The value-category tree" caption="Every expression is exactly one of the bottom row. xvalue belongs to both mixed categories." accent="violet">
  <DiagramRow>
    <DiagramNode title="glvalue">Has identity. Either an lvalue or an xvalue.</DiagramNode>
    <DiagramNode title="rvalue">Movable. Either an xvalue or a prvalue.</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="each splits into" />
  <DiagramRow>
    <DiagramNode title="lvalue">Identity, not movable. `x`, `*p`, `++i`, `"text"`</DiagramNode>
    <DiagramNode title="xvalue" accent>Identity and movable. `std::move(x)`, `f().member`</DiagramNode>
    <DiagramNode title="prvalue">No identity. `42`, `x + 1`, `make()`</DiagramNode>
  </DiagramRow>
</Diagram>

The fourth combination, no identity and not movable, has no category. The standard
([\[basic.lval\]](https://eel.is/c++draft/basic.lval)) defines the categories by what the expression
does rather than by these two properties, but the two views agree:

| Category | Standard definition (paraphrased) |
|---|---|
| **glvalue** ("generalized lvalue") | Its evaluation determines the identity of an object, bit-field, or function |
| **prvalue** ("pure rvalue") | Its evaluation computes a value, or initializes an object |
| **xvalue** ("expiring value") | A glvalue denoting an object whose resources can be reused |
| **lvalue** | A glvalue that is not an xvalue |
| **rvalue** | A prvalue or an xvalue |

## Which expressions are which

Each row below was checked by the program in the next section with GCC 15 and Clang 21; both agree.

| Expression | Category | Rule |
|---|---|---|
| `i`, `*p`, `pt.x` | lvalue | Name of a variable, dereference, member of an lvalue |
| `"text"` | lvalue | String literals are arrays with static storage |
| `++i`, `i = 5` | lvalue | Built-in prefix increment and assignment return their left operand |
| `fn`, `std::move(fn)` | lvalue | Any expression naming a function is an lvalue, even through `T&&` |
| `42`, `nullptr`, `red` (enumerator) | prvalue | Literals other than string literals; enumerators |
| `i++`, `i + 1` | prvalue | Built-in arithmetic and postfix increment compute a value |
| `make()` (returns `Point`) | prvalue | Call to a function returning a non-reference |
| `s + "b"` | prvalue | `operator+` for `std::string` returns by value |
| `[] {}` | prvalue | A lambda expression |
| `this` | prvalue | A pointer value, not an object you can take the address of |
| `std::move(s)`, `static_cast<int&&>(i)` | xvalue | Call or cast to rvalue reference to object type |
| `make().x`, `std::move(pt).x` | xvalue | Non-static data member of an rvalue |

Two rows surprise people. `make().x` is an xvalue, not a prvalue: once the `Point` returned by
`make()` is materialized it is an object with an address, so its member has identity. And a
function never becomes an rvalue: `std::move(fn)` returns `void(&&)()`, and a call returning an
rvalue reference to a *function* is an lvalue.

## Asking the compiler

`decltype((e))` with double parentheses encodes the category of `e` in a type: `T&` for an lvalue,
`T&&` for an xvalue, plain `T` for a prvalue (the full rule is on [decltype](../type-deduction/decltype.md)).
That turns the category into something you can print:

```cpp title="category.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

template <class T> constexpr const char* category() {
    if constexpr (std::is_lvalue_reference_v<T>) return "lvalue";
    else if constexpr (std::is_rvalue_reference_v<T>) return "xvalue";
    else return "prvalue";
}
// highlight-next-line
#define SHOW(...) std::printf("%-16s %s\n", #__VA_ARGS__, category<decltype((__VA_ARGS__))>())

struct Point { int x; int y; };
Point make() { return {1, 2}; }

int main() {
    int i = 0;
    std::string s = "a";
    SHOW(i);
    SHOW(i++);
    SHOW(make());
    SHOW(make().x);
    SHOW(std::move(s));
    SHOW(s + "b");
}
```

```text
i                lvalue
i++              prvalue
make()           prvalue
make().x         xvalue
std::move(s)     xvalue
s + "b"          prvalue
```

`decltype` doesn't evaluate its operand, so `SHOW(i++)` leaves `i` unchanged (Clang warns about
exactly that with `-Wunevaluated-expression`).

## Temporary materialization *(C++17)*

Before C++17 a prvalue of class type was itself a temporary object, so `Point p = make();` notionally
created a temporary and then copied or moved it into `p`. Compilers usually elided that copy, but the
copy or move constructor still had to exist.

Since C++17 a prvalue is not an object. It is a *recipe* for initializing one, and it runs directly
against its final destination. When the language needs an actual object, for example to bind a
reference or to access a member, it applies the **temporary materialization conversion**: it creates
a temporary from the prvalue, and the result is an xvalue that denotes that temporary.

```cpp title="materialize.cpp" showLineNumbers
struct Pinned {
    Pinned() = default;
    Pinned(const Pinned&) = delete;   // neither copyable
    Pinned(Pinned&&) = delete;        // nor movable
};

Pinned make() { return Pinned{}; }    // OK since C++17: the prvalue initializes the return object

int main() {
    Pinned a = make();                // OK since C++17: no temporary, no copy, no move
    const Pinned& r = make();         // materialized: a temporary exists, r binds to it
    (void)a; (void)r;
}
```

This compiles with `-std=c++17` and later. With `-std=c++14`, both GCC and Clang reject lines 7 and
10 because the deleted move constructor is still required. This is the **guaranteed copy elision**
of C++17. It applies only to prvalues: `return local_variable;` is still *named* return value
optimization (NRVO), which is allowed but not required. See [Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md#copy-elision-and-rvo).

## Tracing one statement

The categories nest: the category of an outer expression depends on the operator, not on the
categories of its operands. Follow one initialization through its sub-expressions:

```cpp
std::string r = std::move(a) + b.substr(1);   // a and b are std::string variables
```

<Walkthrough title="Categories inside one initializer" caption="Checked with the SHOW macro above, GCC 15 and Clang 21." accent="violet">
  <Step title="Name the operands">

`a` and `b` are names of variables: both are <StepChange>lvalues</StepChange>. Nothing may be stolen
from them yet.

  </Step>
  <Step title="std::move(a)">

`std::move` returns `std::string&&`. A call returning an rvalue reference to an object is an
<StepChange>xvalue</StepChange>: it still denotes `a` (identity), but it is now marked as movable.

  </Step>
  <Step title="b.substr(1)">

`substr` returns `std::string` by value, so the call is a <StepChange>prvalue</StepChange>. It
doesn't name an object yet.

  </Step>
  <Step title="Binding the operands of operator+">

The best overload is `operator+(std::string&&, std::string&&)`. The xvalue binds directly. The
prvalue is <StepChange label="materialized">materialized</StepChange> into a temporary so the
reference has an object to bind to.

  </Step>
  <Step title="The sum">

`operator+` returns `std::string` by value, so `std::move(a) + b.substr(1)` is a
<StepChange>prvalue</StepChange>. Because its operands were rvalues, this overload may append
into `a`'s existing buffer instead of allocating a new one.

  </Step>
  <Step title="Initializing r">

The prvalue initializes `r` directly. There is <StepChange label="C++17">no temporary and no
move</StepChange> at this step. Afterwards `a` is valid but unspecified.

  </Step>
</Walkthrough>

## Common mistakes

- **Reading the category off the type.** A variable of type `std::string&&` is an lvalue when
  named. Category describes how an expression is used, not what was declared.
- **Treating "rvalue" as "temporary".** An xvalue is an rvalue that refers to a perfectly ordinary
  long-lived object, such as `std::move(member)`. Moving from it changes that object.
- **Expecting `return x;` to be guaranteed elision.** Only prvalues are guaranteed. Returning a
  named local is NRVO, which can fail (for example with two different locals returned on different
  paths) and then falls back to an implicit move.
- **Moving the same object twice.** `f(std::move(v), std::move(v))` passes two xvalues denoting the
  same `v`. Whichever parameter is initialized second sees a moved-from object.

## Key points

- Two properties, identity and movable, give three primary categories: lvalue, xvalue, prvalue.
- glvalue = lvalue or xvalue. rvalue = xvalue or prvalue. xvalue is in both.
- An xvalue is what you get from `std::move` and from members of rvalues.
- Since C++17 a prvalue initializes its destination directly. A temporary appears only when it is
  materialized, and the result is then an xvalue.

## Related

- [Reference Collapsing](./reference-collapsing.md): forwarding references and `std::forward`, which
  preserve these categories through templates.
- [Copy and Move Semantics](../../07-classes-and-oop/copy-and-move-semantics.md): the constructors
  that rvalue arguments select.
