---
id: decltype
title: decltype
sidebar_label: decltype
sidebar_position: 2
tags: [c++, decltype, type-deduction, cpp11]
---

# decltype

`decltype(e)` *(C++11)* names the type of an entity or expression without evaluating it. Where
[auto](./auto.md) answers "what type should a copy of this have?", `decltype` answers "what type
is this, exactly?", references and `const` included. It has two rules, and which one applies
depends on whether you write a bare name or any other expression. Most `decltype` surprises,
`decltype(x)` versus `decltype((x))` among them, come from that split.

**Prerequisites:** [glvalue, prvalue, xvalue](../value-categories/glvalue-prvalue-xvalue.md)

## The two rules

<Diagram title="How decltype(e) picks a type" accent="green">
  <DiagramNode variant="pill" accent>decltype(e)</DiagramNode>
  <DiagramArrow label="is e an unparenthesized name or member access?" />
  <DiagramRow>
    <DiagramNode title="Yes: rule 1">The **declared** type of that variable, parameter, or member</DiagramNode>
    <DiagramNode title="No: rule 2">Type `T` of the expression, adjusted by its category</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="rule 2 by category" />
  <DiagramRow>
    <DiagramNode title="lvalue">`T&`</DiagramNode>
    <DiagramNode title="xvalue">`T&&`</DiagramNode>
    <DiagramNode title="prvalue">`T`</DiagramNode>
  </DiagramRow>
</Diagram>

1. If `e` is an **unparenthesized id-expression** (a variable, function or parameter name, an
   enumerator) or an **unparenthesized class member access** (`p.x`, `ptr->x`), the result is the
   type the entity was declared with. A variable declared `const int&` gives `const int&`; a
   member declared `double` gives `double` even when accessed through a `const` object.
2. Otherwise `e` is an ordinary expression of some type `T`, and the result encodes its value
   category: `T&` for an lvalue, `T&&` for an xvalue, `T` for a prvalue.

Rule 1 also covers structured bindings *(C++17)*, which report the type of the element they
refer to. The full wording is on [cppreference: decltype](https://en.cppreference.com/w/cpp/language/decltype).

The operand is never evaluated: `decltype(f())` doesn't call `f`, and `decltype(i++)` doesn't
increment `i`. The function only has to be declared.

## Applying the rules

<Walkthrough title="decltype on six operands" caption="Each line is checked by static_assert in the program below." accent="green">
  <Step title="decltype(x)">

`x` is a bare name, declared `int`, so rule 1 applies: <StepChange>`int`</StepChange>.

  </Step>
  <Step title="decltype((x))">

Parentheses make `(x)` an ordinary expression, so rule 2 applies. `(x)` is an lvalue of type
`int`: <StepChange>`int&`</StepChange>. Same object, different rule.

  </Step>
  <Step title="decltype(cr)">

`cr` is declared `const int&`. Rule 1 reports the declaration unchanged:
<StepChange>`const int&`</StepChange>. Compare `auto`, which would give `int`.

  </Step>
  <Step title="decltype(x + 1) and decltype(x++)">

Neither is a name. Both are prvalues of type `int`: <StepChange>`int`</StepChange>. Prefix
`++x` is an lvalue, so `decltype(++x)` is `int&`.

  </Step>
  <Step title="decltype(cp.v) and decltype((cp.v))">

`cp` is a `const Point`. `cp.v` is an unparenthesized member access, so rule 1 gives the member's
declared type, <StepChange>`double`</StepChange>, ignoring the object's `const`. `(cp.v)` is an
lvalue of type `const double`, so rule 2 gives `const double&`.

  </Step>
  <Step title="decltype(std::move(x))">

A call returning `int&&` is an xvalue: <StepChange>`int&&`</StepChange>.

  </Step>
</Walkthrough>

```cpp title="decltype-rules.cpp" showLineNumbers
#include <type_traits>
#include <utility>
#include <vector>
using std::is_same_v;

struct Point { double v; };
int compute();                         // declared only: decltype doesn't call it

int main() {
    int x = 0;
    const int& cr = x;
    const Point cp{1.0};
    std::vector<int> vec{1, 2, 3};

    static_assert(is_same_v<decltype(x),            int>);
    static_assert(is_same_v<decltype((x)),          int&>);
    static_assert(is_same_v<decltype(cr),           const int&>);
    static_assert(is_same_v<decltype(x + 1),        int>);
    static_assert(is_same_v<decltype(++x),          int&>);
    static_assert(is_same_v<decltype(cp.v),         double>);
    static_assert(is_same_v<decltype((cp.v)),       const double&>);
    static_assert(is_same_v<decltype(std::move(x)), int&&>);
    static_assert(is_same_v<decltype(Point::v),     double>);   // non-static member, unevaluated
    static_assert(is_same_v<decltype(compute()),    int>);
    static_assert(is_same_v<decltype(vec[0]),       int&>);     // operator[] returns int&
    static_assert(is_same_v<decltype("hi"),         const char(&)[3]>);  // string literal: lvalue
    (void)cr;
}
```

## Where `decltype` is used

**Declaring something with the type of something else.** `decltype(vec) copy;` or
`using Elem = decltype(vec)::value_type;` (C++11 allows `decltype(...)` before `::`). If the
result is a reference, the declaration needs an initializer: `decltype(vec[0]) e;` is an error
because `e` would be an uninitialized `int&`.

**Return types that depend on parameters.** Before C++14 the only way to return "whatever `a + b`
is" was a trailing return type, because the parameters aren't in scope before the parameter list:

```cpp title="trailing.cpp" showLineNumbers
#include <type_traits>

template <class T, class U>
auto add(T a, U b) -> decltype(a + b) { return a + b; }

static_assert(std::is_same_v<decltype(add(5, 3.14)), double>);

int main() {}
```

C++14 lets you write plain `auto add(T a, U b)` instead. That uses the `auto` by-value rule, so it
can't return a reference; [decltype(auto)](./decltype-auto.md) can.

**Types of expressions you can't write out.** `decltype` of a lambda, or of
`std::declval<T>().size()` in a trait (`std::declval` from `<utility>` produces an expression of type
`T&&` without constructing a `T`, and is only usable in unevaluated contexts). See
[Type Traits](../../08-templates-and-metaprogramming/type-traits.md).

## Common mistakes

- **Parenthesizing a name by accident.** `decltype((x))` and `decltype(x)` differ for any variable.
  Macros that wrap their argument in parentheses trigger this silently.
- **Expecting `const` from a `const` object's member.** `decltype(cp.v)` is `double`. Write
  `decltype((cp.v))` or `std::remove_reference_t<decltype((cp.v))>` to see the access type.
- **Declaring a reference without an initializer.** Any rule-2 lvalue gives a reference type.
  `decltype(*p) y;` doesn't compile.
- **`vector<bool>`.** `decltype(bvec[0])` is `std::vector<bool>::reference`, a proxy class, not
  `bool&`.

## Key points

- Bare name or member access: the declared type. Anything else: the type plus its category.
- lvalue gives `T&`, xvalue `T&&`, prvalue `T`. Extra parentheses turn a name into an lvalue
  expression.
- The operand is unevaluated; a declaration is enough.

## Related

- [auto](./auto.md): the by-value deduction rule that `decltype` doesn't follow.
- [decltype(auto)](./decltype-auto.md): `decltype` rules with `auto` syntax, for forwarding return
  types.
