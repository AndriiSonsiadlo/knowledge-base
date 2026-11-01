---
id: dynamic-vs-static-polymorphism
title: Dynamic vs Static Polymorphism
sidebar_label: Dynamic vs Static Polymorphism
sidebar_position: 10
tags: [c++, polymorphism, templates, virtual-functions, variant, crtp]
---

# Dynamic vs Static Polymorphism

Polymorphism means one piece of code works with several types. C++ gives you three ways to get it,
and they differ in *when* the concrete type is chosen and *what that choice costs*:

- **Dynamic polymorphism**: virtual functions behind a base-class pointer or reference. The type is
  chosen at run time.
- **Static polymorphism**: templates (optionally constrained by concepts, or shaped with CRTP). The
  type is chosen at compile time.
- **Closed-set polymorphism**: `std::variant` + `std::visit` *(C++17)*. The type is chosen at run
  time, but only from a list fixed at compile time.

This page is the canonical comparison of the three. The mechanisms themselves live elsewhere:
vtables and dispatch in [Virtual Functions](./virtual-functions.md), templates in
[Function Templates](../08-templates-and-metaprogramming/function-templates.md), CRTP in
[CRTP](../13-idioms-and-design/03-crtp.md), and hand-rolled run-time polymorphism without
inheritance in [Type Erasure](../13-idioms-and-design/06-type-erasure.md).

**Prerequisites:** [Inheritance](./inheritance.md), [Virtual Functions](./virtual-functions.md),
[Function Templates](../08-templates-and-metaprogramming/function-templates.md).

## One problem, three solutions

All three examples below sum the areas of a square of side 2 and a circle of radius 1 (with π
rounded to 3 so the output is exact). Each compiles with `g++ -std=c++23 -Wall -Wextra` and prints `7`.

### Dynamic: virtual functions

```cpp title="dynamic.cpp" showLineNumbers
#include <iostream>
#include <memory>
#include <vector>

struct Shape {
    virtual ~Shape() = default;
    virtual double area() const = 0;
};
struct Square : Shape {
    double s;
    explicit Square(double side) : s(side) {}
    double area() const override { return s * s; }
};
struct Circle : Shape {
    double r;
    explicit Circle(double radius) : r(radius) {}
    double area() const override { return 3.0 * r * r; }   // rough pi keeps output exact
};

double total(const std::vector<std::unique_ptr<Shape>>& shapes) {   // compiled once
    double sum = 0;
    for (const auto& s : shapes) sum += s->area();                  // virtual call
    return sum;
}

int main() {
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Square>(2));
    shapes.push_back(std::make_unique<Circle>(1));
    std::cout << total(shapes) << '\n';   // 7
}
```

`total` is compiled once and works for every current and future `Shape` subclass, including ones
loaded from a shared library. The price: every type must inherit from `Shape`, objects live behind
pointers (usually one heap allocation each), and each `area()` call is an indirect call through the
vtable that the optimizer can only remove when it can prove the dynamic type (devirtualization, see
[Virtual Functions](./virtual-functions.md)).

### Static: templates and concepts

```cpp title="static.cpp" showLineNumbers
#include <concepts>
#include <iostream>

struct Square { double s; double area() const { return s * s; } };   // no common base
struct Circle { double r; double area() const { return 3.0 * r * r; } };

template <typename T>
concept HasArea = requires(const T& t) { { t.area() } -> std::convertible_to<double>; };

template <HasArea... Ts>
double total(const Ts&... shapes) {     // one instantiation per argument-type list
    return (shapes.area() + ... + 0.0);  // direct calls, inlinable
}

int main() {
    std::cout << total(Square{2}, Circle{1}) << '\n';   // 7
}
```

No base class, no virtual functions, no heap: the types only need to *fit the interface* (the
`HasArea` [concept](../08-templates-and-metaprogramming/concepts-and-requires.md)). The compiler
generates a separate `total` for each list of argument types and can inline every call. The price:
the set of types must be known where `total` is called, the code must live in headers, and each new
combination of types adds another instantiation to the binary. You cannot put a `Square` and a
`Circle` in one `std::vector` this way.

### Closed set: `std::variant`

```cpp title="variant.cpp" showLineNumbers
#include <iostream>
#include <variant>
#include <vector>

struct Square { double s; double area() const { return s * s; } };
struct Circle { double r; double area() const { return 3.0 * r * r; } };

using Shape = std::variant<Square, Circle>;   // closed set, stored by value

double total(const std::vector<Shape>& shapes) {
    double sum = 0;
    for (const auto& sh : shapes)
        sum += std::visit([](const auto& s) { return s.area(); }, sh);
    return sum;
}

int main() {
    std::vector<Shape> shapes{Square{2}, Circle{1}};   // no heap allocation per element
    std::cout << total(shapes) << '\n';                // 7
}
```

The variant stores whichever alternative is active inline (its size is roughly the largest
alternative plus a discriminator), so a `std::vector<Shape>` is contiguous and has no per-element
allocation. `std::visit` dispatches on the stored index at run time, and the generic lambda is
instantiated for each alternative at compile time. Adding a new *operation* is easy (write another
visitor); adding a new *type* means editing the `Shape` alias and recompiling every user. That is
the opposite trade-off from virtual functions, where new types are cheap and new operations require
touching the base class.

<Diagram title="When the concrete type is fixed" caption="Each approach moves the decision to a different point; the cost moves with it." accent="violet">
  <DiagramRow>
    <DiagramNode icon="braces" title="Templates / CRTP">Compile time. Direct, inlinable calls; one instantiation per type.</DiagramNode>
    <DiagramNode icon="layers" title="std::variant" accent>Run time, from a closed list. Values stored inline; dispatch on an index.</DiagramNode>
    <DiagramNode icon="shapes" title="Virtual functions">Run time, open set. One compiled function; indirect call per dispatch.</DiagramNode>
  </DiagramRow>
</Diagram>

## CRTP: a base-class interface without virtual calls

The **curiously recurring template pattern** passes the derived class to its base as a template
argument, so the base can call derived members through a `static_cast` that is resolved at compile
time:

```cpp title="crtp.cpp" showLineNumbers
#include <iostream>

template <typename Derived>
struct ShapeBase {
    double doubled() const {
        return 2 * static_cast<const Derived&>(*this).area();   // resolved at compile time
    }
};

struct Square : ShapeBase<Square> {
    double s;
    explicit Square(double side) : s(side) {}
    double area() const { return s * s; }
};

int main() { std::cout << Square{3}.doubled() << '\n'; }   // 18
```

CRTP gives code reuse in a base class (`doubled` is written once) with static dispatch, but
`ShapeBase<Square>` and `ShapeBase<Circle>` are unrelated types, so CRTP does **not** give you a
heterogeneous container. Since C++23, explicit object parameters (`this auto& self`) cover many CRTP
uses without the template base. Details, variants and pitfalls are on the
[CRTP](../13-idioms-and-design/03-crtp.md) page.

## Comparison

| | Virtual functions | Templates / concepts / CRTP | `std::variant` + `std::visit` |
|---|---|---|---|
| Type chosen | Run time | Compile time | Run time, from a fixed list |
| Set of types | Open: new subclasses anywhere, even in plugins | Open, but must be visible at the call site | Closed: listed in the variant |
| Common base required | Yes | No (interface checked structurally) | No |
| Heterogeneous container | Yes, via pointers (`vector<unique_ptr<Base>>`) | No | Yes, by value (`vector<variant<...>>`) |
| Per-object overhead | A vptr in each object (8 bytes on typical 64-bit ABIs), usually a heap allocation | None | Storage for the largest alternative plus an index |
| Call cost | Indirect call; inlined only if devirtualized | Direct call; inlinable | Dispatch on the index, then direct calls; inlinable per alternative |
| Code size | One copy of the generic code | One copy per type combination | One visitor body per alternative |
| Adding a type | Cheap (new subclass) | Cheap | Edit the variant, recompile users |
| Adding an operation | Edit the base class and every subclass | Cheap (new function template) | Cheap (new visitor) |
| Error messages | Plain | Long without concepts, readable with them | Long when a visitor misses an alternative |

"Faster" depends on the workload. An indirect call is cheap when the branch predictor sees the same
target repeatedly; what usually costs more is the lost inlining (and the vectorization that inlining
enables) and the pointer-chasing of heap-allocated objects. Measure your own loop before choosing on
speed alone.

## Choosing

- **Use virtual functions** when the set of types is open: plugins, frameworks where users add
  subclasses, types decided by configuration or input, or ABI boundaries where templates cannot
  cross. Also when compile time and binary size matter more than per-call speed.
- **Use templates (with concepts)** for generic algorithms and libraries where the type is known at
  the call site: containers, `std::sort`, math kernels, policy parameters
  ([policy-based design](../13-idioms-and-design/07-policy-based-design.md)).
- **Use `std::variant`** when the set of alternatives is small, known, and owned by you (AST nodes,
  messages, states), and you want value semantics and contiguous storage.
- **Use type erasure** (`std::function`, `std::any`, or a hand-written wrapper) when you need run-time
  polymorphism over types that do *not* share a base class. See
  [Type Erasure](../13-idioms-and-design/06-type-erasure.md).

The approaches combine: a template algorithm can operate on `Shape&`, and a class hierarchy can use
CRTP internally to share implementation while still exposing a virtual interface.

## References

- [cppreference: virtual function specifier](https://en.cppreference.com/w/cpp/language/virtual)
- [cppreference: `std::variant`](https://en.cppreference.com/w/cpp/utility/variant) and [`std::visit`](https://en.cppreference.com/w/cpp/utility/variant/visit)
- [cppreference: constraints and concepts](https://en.cppreference.com/w/cpp/language/constraints)
- [P0847R7: Deducing `this`](https://wg21.link/P0847R7) (C++23 explicit object parameters)
