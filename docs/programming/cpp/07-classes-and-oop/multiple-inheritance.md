---
id: multiple-inheritance
title: Multiple Inheritance
sidebar_label: Multiple Inheritance
sidebar_position: 8
tags: [c++, classes, multiple-inheritance, diamond-problem, virtual-inheritance]
---

# Multiple Inheritance

A C++ class can have several direct base classes: `class Duck : public Flyer, public Swimmer`. The
derived object then holds one subobject per base, and converts implicitly to a reference to any of
them. This is how a class implements several independent interfaces, or picks up several small
mixins. It also brings two problems single inheritance doesn't have: **ambiguous names**, when two
bases declare the same member, and the **diamond**, when two bases share a common base of their own.
**Virtual inheritance** solves the diamond, at a cost in layout and construction rules.

This page is the canonical home for multiple and virtual inheritance. Single-inheritance mechanics
(name lookup, hiding) are on [inheritance](./inheritance.md). Byte-level layouts are on
[object layout](../12-low-level-and-platform/02-object-layout.md).

**Prerequisites:** [Inheritance](./inheritance.md),
[virtual functions](./virtual-functions.md) (vptrs, for the layout sections).

## Several bases, several subobjects

Bases are constructed in the order they appear in the base-specifier list (not the order of the
mem-initializer list) and destroyed in reverse. Each base is a separate subobject, so converting a
`Derived*` to its second base generally **changes the pointer value** to point at that subobject:

```cpp title="mi_layout.cpp" showLineNumbers
#include <cstdio>

struct B1 { virtual void f1() {} };
struct B2 { virtual void f2() {} };
struct D : B1, B2 {
    void f1() override {}
    void f2() override {}
};

int main() {
    D d;
    B1* p1 = &d;
    B2* p2 = &d;
    std::printf("sizeof(D) = %zu, p2 - p1 = %td bytes\n",
                sizeof(D), reinterpret_cast<char*>(p2) - reinterpret_cast<char*>(p1));
}
```

```text
sizeof(D) = 16, p2 - p1 = 8 bytes
```

Measured with GCC 15 and Clang 21 on x86-64 Linux (Itanium ABI). The `B1` subobject sits at offset
0 and the `B2` subobject at offset 8, each with its own vptr.

<Diagram title="D with two polymorphic bases (x86-64, Itanium ABI)" caption="Converting D* to B2* adds 8. Calls through the B2 vptr reach D's overrides via small adjustment stubs (thunks)." accent="blue">
  <DiagramGroup label="D object, 16 bytes">
    <DiagramNode title="B1 subobject" accent>offset 0: vptr (D's primary vtable)</DiagramNode>
    <DiagramNode title="B2 subobject">offset 8: vptr (D's secondary vtable for B2)</DiagramNode>
  </DiagramGroup>
</Diagram>

The compiler applies this adjustment for every implicit conversion and `static_cast`, and
`p2 == &d` still compares equal because `&d` is converted first. The adjustment does *not* happen
through `void*` or `reinterpret_cast`. Round-tripping a `D*` through `void*` and then casting it to
`B2*` gives a wrong pointer. When `D::f2` is called through a `B2*`, `this` must point at the whole
`D`. The Itanium ABI handles this with a **thunk**, a stub in the `B2`-in-`D` vtable that subtracts 8
from `this` and jumps to `D::f2`.

## Ambiguous names

If a name is found in more than one base, using it unqualified is ill-formed. Lookup does not
prefer one base over the other, and overload resolution is not used to break the tie:

```cpp title="ambiguity.cpp" showLineNumbers
#include <iostream>

struct Flyer   { void move() const { std::cout << "fly\n"; } };
struct Swimmer { void move() const { std::cout << "swim\n"; } };

struct Duck : Flyer, Swimmer {
    void move() const { Flyer::move(); Swimmer::move(); }  // resolves the ambiguity
};

int main() {
    Duck d;
    d.move();
    d.Swimmer::move();
}
```

```text
fly
swim
swim
```

Without `Duck::move`, the call `d.move()` would be ambiguous. Three ways to resolve it: declare
the member in the derived class, as above (it hides both); qualify the call (`d.Swimmer::move()`);
or bring one version in with `using Flyer::move;`.

## The diamond

A diamond forms when two bases share a common base:

<Diagram title="Diamond hierarchy" accent="amber">
  <DiagramNode title="Animal" accent>int age</DiagramNode>
  <DiagramArrow label="both derive from Animal" />
  <DiagramRow>
    <DiagramNode title="Mammal" />
    <DiagramNode title="Winged" />
  </DiagramRow>
  <DiagramArrow label="Bat derives from both" />
  <DiagramNode title="Bat" />
</Diagram>

With ordinary inheritance, `Bat` contains **two** `Animal` subobjects, one inside `Mammal` and one
inside `Winged`:

```cpp title="diamond.cpp" showLineNumbers
#include <iostream>

struct Animal { int age = 0; };
struct Mammal : Animal {};
struct Winged : Animal {};
struct Bat : Mammal, Winged {};

int main() {
    Bat bat;
    // bat.age = 5;               // error: request for member 'age' is ambiguous
    bat.Mammal::age = 5;
    bat.Winged::age = 3;          // a second, independent Animal
    // Animal* a = &bat;          // error: Animal is an ambiguous base of Bat
    Animal* a = static_cast<Mammal*>(&bat);
    std::cout << a->age << ' ' << bat.Winged::age << '\n';
}
```

```text
5 3
```

Sometimes two copies are what you want, for example two independent intrusive list hooks. Usually
they are a modelling error: a bat has one age.

## Virtual inheritance

Declaring the base `virtual` in every class on the paths to it makes all of them share a single
subobject:

```cpp title="virtual_base.cpp" showLineNumbers
#include <iostream>

struct Animal {
    explicit Animal(int age) : age(age) { std::cout << "Animal(" << age << ")\n"; }
    int age;
};
struct Mammal : virtual Animal {
    Mammal() : Animal(1) {}             // ignored when Mammal is not the most derived
};
struct Winged : virtual Animal {
    Winged() : Animal(2) {}             // ignored when Winged is not the most derived
};
struct Bat : Mammal, Winged {
    Bat() : Animal(7) {}                // the most derived class initializes Animal
};

int main() {
    Bat b;
    std::cout << b.age << '\n';
    Mammal m;
    std::cout << m.age << '\n';
}
```

```text
Animal(7)
7
Animal(1)
1
```

`b.age` is now unambiguous, and `Animal* a = &b;` compiles. Two construction rules come with it:

- **The most derived class constructs every virtual base**, before any non-virtual base. The
  `Animal(1)` and `Animal(2)` initializers in `Mammal` and `Winged` are skipped when those classes
  are bases of `Bat`, and used when they are the complete object, as `Mammal m` shows. If `Bat`
  didn't name `Animal`, its default constructor would be used, and since `Animal` has none, `Bat`
  would not compile. Every class further down the hierarchy inherits this obligation.
- `virtual` must be on the edges *into* the shared base (`Mammal : virtual Animal`). Marking only
  `Bat : virtual Mammal, virtual Winged` does not merge the two `Animal`s.

## What virtual inheritance costs

The virtual base is no longer at a fixed offset from each class that inherits it. Its position
depends on the most derived type. In the Itanium ABI, each class with a virtual base gets a vptr,
and its vtable records the offset to the virtual base. Reaching a virtual base member through a
`Mammal&` takes an extra load. Sizes measured with GCC 15 and Clang 21 on x86-64 Linux:

| Type | Bases | `sizeof` |
|---|---|---|
| `struct Base { int data; }` | none | 4 |
| `struct NormalDerived : Base { int d; }` | non-virtual | 8 |
| `struct VirtualDerived : virtual Base { int d; }` | virtual | 16 (vptr + `d` + `Base`) |
| `Bat : Mammal, Winged`, where `Mammal` and `Winged` each derive from `Animal`, and `Animal`, `Mammal`, `Winged`, `Bat` each declare one `int` | non-virtual diamond | 20 |
| Same with `virtual Animal` | virtual diamond | 40 (two vptrs, members, one `Animal`, padding) |

Other costs:

- Converting from a virtual base back down to a derived class cannot use `static_cast`.
  It needs `dynamic_cast`, so the virtual base must be polymorphic.
- Construction and destruction are harder to follow. The Itanium ABI emits a complete-object (C1)
  and a base-subobject (C2) variant of every constructor; with virtual bases they stop being
  identical, because only C1 constructs the virtual bases.
- Layout is not [standard-layout](./class-layout.md), so no `offsetof` or C interop.

Use virtual inheritance only when a shared base subobject is really what the design needs. The
standard library uses it in iostreams: `std::basic_iostream` derives from `basic_istream` and
`basic_ostream`, which both inherit virtually from `basic_ios`.

## When multiple inheritance fits

- **Several interfaces**: bases with only pure virtual functions and no data (`Drawable`,
  `Serializable`). This is the use that causes the fewest problems. Diamonds of stateless interfaces
  are harmless and rarely need `virtual`, unless code needs to convert to the shared interface (the conversion is ambiguous without it).
- **Mixins and policies**: small, often empty bases that add one capability, such as a
  [non-copyable](../13-idioms-and-design/04-non-copyable.md) base or a [CRTP](../13-idioms-and-design/03-crtp.md)
  helper. Empty bases usually cost no space (empty base optimization).
- **Implementation reuse from several classes with state**: usually a design smell. Composition
  (data members, forwarding functions) avoids the ambiguity and the diamond, and keeps
  implementation details out of the class's type.

## References

- [cppreference: Derived classes, virtual base classes](https://en.cppreference.com/w/cpp/language/derived_class#Virtual_base_classes)
- [cppreference: Constructors and member initializer lists, initialization order](https://en.cppreference.com/w/cpp/language/constructor#Initialization_order)
- [Itanium C++ ABI: class layout and virtual tables](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#layout)
