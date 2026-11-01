---
id: inheritance
title: Inheritance
sidebar_label: Inheritance
sidebar_position: 6
tags: [c++, inheritance, base-class, derived-class, name-hiding, oop]
---

# Inheritance

A **derived class** is declared with one or more **base classes**: `class Dog : public Animal`. Every
`Dog` object contains a complete `Animal` object inside it, the **base-class subobject**, followed by
`Dog`'s own members. The derived class gets the base's members without re-declaring them, and with
`public` inheritance a `Dog&` can be used wherever an `Animal&` is expected. That substitutability
is what makes [virtual functions](./virtual-functions.md) useful.

This page covers the mechanics of single inheritance: how a derived class is declared and
constructed, the derived-to-base conversion, and how names from the base are found or hidden.
Other pages cover the neighbouring topics:

- [Access control](./access-control.md) owns `public` / `protected` /
  `private` inheritance and what each does to the base's members.
- [Virtual functions](./virtual-functions.md) owns overriding, `override`/`final`, abstract classes
  and virtual destructors.
- [Multiple inheritance](./multiple-inheritance.md) owns several bases, diamonds and `virtual` bases.
- [Constructors and destructors](./constructors-and-destructors.md) owns the full
  construction/destruction order.

**Prerequisites:** [Access control](./access-control.md),
[constructors and destructors](./constructors-and-destructors.md).

## Declaring a derived class

```cpp title="inheritance.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <utility>

class Animal {
public:
    explicit Animal(std::string name) : name_(std::move(name)) {}
    void eat() const { std::cout << name_ << " eats\n"; }
    void move(int metres) const { std::cout << name_ << " moves " << metres << " m\n"; }
protected:
    const std::string& name() const { return name_; }
private:
    std::string name_;
};

class Dog : public Animal {
public:
    using Animal::Animal;                       // inherit Animal(std::string)
    void bark() const { std::cout << name() << " barks\n"; }
};

int main() {
    Dog d{"Rex"};
    d.eat();
    d.bark();
    Animal& a = d;      // Dog& -> Animal& is implicit
    a.move(3);
}
```

```text
Rex eats
Rex barks
Rex moves 3 m
```

Points the example shows:

- `Dog` calls `eat()` and `move()` as if it had declared them. They are members of the `Animal`
  subobject, found by name lookup in the base.
- `name_` is `private` in `Animal`, so `Dog` cannot touch it. `Dog` uses the `protected` accessor
  instead. Keeping data `private` and giving derived classes a narrow `protected` interface lets the
  base keep its invariants.
- `using Animal::Animal;` inherits the base's constructors *(C++11)*. Without it, `Dog` would have
  to write `explicit Dog(std::string n) : Animal(std::move(n)) {}`. Either way, the base subobject
  is always constructed before the derived class's members and body, and destroyed after them. The
  details are on [constructors and destructors](./constructors-and-destructors.md).
- `class` defaults to `private` inheritance and `struct` to `public`, so write the keyword
  explicitly for `class`.

## What a derived object looks like

<Diagram title="A Dog object" caption="The Animal subobject comes first in practice; Dog's own members follow. Exact placement is up to the ABI." accent="blue">
  <DiagramGroup label="Dog">
    <DiagramNode title="Animal subobject" accent>name_ (std::string)</DiagramNode>
    <DiagramNode title="Dog's own members">none in this example</DiagramNode>
  </DiagramGroup>
</Diagram>

Because the base subobject is a real `Animal`, converting a `Dog*` to an `Animal*` (or `Dog&` to
`Animal&`) is implicit and just yields the address of that subobject. With single, non-virtual
inheritance the address usually does not change. With [multiple
inheritance](./multiple-inheritance.md) it can. How the compiler places bases, members and
vtable pointers is covered in [class layout](./class-layout.md).

The conversion only works where the base is **accessible**: for `private` or `protected`
inheritance, code outside the class cannot convert `Derived*` to `Base*`. The opposite direction,
base to derived, is never implicit. Use `static_cast` when you know the dynamic type, or
`dynamic_cast` to check it at run time
(see [RTTI](./virtual-functions.md#rtti-dynamic_cast-and-typeid)).

Copying a `Dog` *into* an `Animal` by value copies only the `Animal` subobject. That is
[object slicing](./object-slicing.md), and it is why polymorphic objects are handled through
references and pointers.

## Name lookup and name hiding

A name used in a derived class is looked up in the derived class first and only then in its bases.
Lookup stops at the first scope that declares the name. **Overload resolution happens only after
that**, among the candidates from that one scope. So a member function in the derived class
**hides every base member with the same name**, whatever their parameter lists:

```cpp title="name_hiding.cpp" showLineNumbers
#include <iostream>

struct Base {
    void f(int)    { std::cout << "Base::f(int)\n"; }
    void f(double) { std::cout << "Base::f(double)\n"; }
};

struct Hides : Base {
    void f(const char*) { std::cout << "Hides::f(const char*)\n"; }
};

struct Unhides : Base {
    using Base::f;                               // bring both Base::f back
    void f(const char*) { std::cout << "Unhides::f(const char*)\n"; }
};

int main() {
    Hides h;
    h.f("x");
    // h.f(1);        // error: Hides::f(const char*) hides every Base::f
    h.Base::f(1);     // a qualified name still reaches it
    Unhides u;
    u.f(1);
    u.f(2.5);
    u.f("x");
}
```

```text
Hides::f(const char*)
Base::f(int)
Base::f(int)
Base::f(double)
Unhides::f(const char*)
```

`h.f(1)` does not fall back to `Base::f(int)`. Lookup found `f` in `Hides` and stopped, and
`const char*` cannot be initialized from `1`. The two fixes are a **using-declaration**
(`using Base::f;`), which adds the base overloads to the derived scope so all of them take part in
overload resolution, or a qualified call (`h.Base::f(1)`). The same hiding rule applies to data
members and nested types.

Hiding is different from overriding. A derived function with the same signature as a base
**virtual** function overrides it and takes part in dynamic dispatch. A function with the same name
and any signature that does not override anything only hides. Marking intended overrides with
`override` makes the compiler tell the two apart for you (see
[virtual functions](./virtual-functions.md#override-and-final)).

A using-declaration can also change the access of an inherited member, for example to make a
`protected` base function `public` in the derived class. That is covered on
[access control](./access-control.md).

## When to inherit

Public inheritance means "is a": every operation valid on the base must make sense on the derived
object, and code written against `Animal&` must keep working when handed a `Dog`. When that is not
true, or when you only want to reuse an implementation, a data member (composition) is usually the
better tool. It doesn't expose the base's interface, doesn't allow the derived-to-base conversion,
and can be replaced without changing the class's public type.

Inheritance without virtual functions is still useful: mixin and policy bases, empty bases that
cost no space under the [empty base optimization](./class-layout.md),
and the [CRTP](../13-idioms-and-design/03-crtp.md). Such a base should not have a public
non-virtual destructor if users might `delete` a derived object through a base pointer. Make it
`protected`, or make it virtual (see [virtual destructors](./virtual-functions.md#virtual-destructors)).

## References

- [cppreference: Derived classes](https://en.cppreference.com/w/cpp/language/derived_class)
- [cppreference: Unqualified name lookup](https://en.cppreference.com/w/cpp/language/unqualified_lookup)
- [cppreference: Using-declaration](https://en.cppreference.com/w/cpp/language/using_declaration)
