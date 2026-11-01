---
id: virtual-functions-and-vtables
title: Virtual Functions and vtables
sidebar_label: Virtual Functions & vtables
sidebar_position: 7
tags: [c++, virtual-functions, vtables, polymorphism, dynamic-dispatch, override, final]
---

# Virtual Functions and vtables

A call through a `Base&` or `Base*` normally runs `Base`'s function, because the compiler picks the
function from the **static type** of the expression. Declaring the function `virtual` changes that:
the call runs the version belonging to the **dynamic type**, the type of the complete object the
reference actually refers to. This is **dynamic dispatch**, and it is how one piece of code can
operate on many derived types it was compiled without knowing.

This page is the canonical home for virtual functions: overriding, `override` and `final`, abstract
classes, virtual destructors, how dispatch is implemented with vtables, what it costs, and the
traps around constructors and default arguments. Choosing between virtual functions and templates
is on [dynamic vs static polymorphism](./dynamic-vs-static-polymorphism.md).

**Prerequisites:** [Inheritance](./inheritance.md) (derived-to-base conversion, name hiding).

## Overriding and dynamic dispatch

```cpp title="shapes.cpp" showLineNumbers
#include <iostream>
#include <memory>
#include <vector>

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;                       // pure virtual
    virtual const char* name() const { return "shape"; }   // has a default
};

class Circle : public Shape {
public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return 3.14159265 * r_ * r_; }
    const char* name() const override { return "circle"; }
private:
    double r_;
};

class Square final : public Shape {
public:
    explicit Square(double s) : s_(s) {}
    double area() const override { return s_ * s_; }       // keeps Shape::name
private:
    double s_;
};

int main() {
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(1.0));
    shapes.push_back(std::make_unique<Square>(2.0));
    for (const auto& s : shapes)
        std::cout << s->name() << ' ' << s->area() << '\n';
}
```

```text
circle 3.14159
shape 4
```

A derived function **overrides** a base virtual function when it has the same name, the same
parameter types, and the same `const`/`volatile` and reference qualifiers. It is then virtual too,
with or without the keyword. The return type must match, except for
[covariant returns](#covariant-return-types). Dispatch happens only for calls through a pointer or
reference. Calling on an object of known type (`Circle c; c.area();`), or with a qualified name
(`s->Shape::name()`), calls the named function directly.

`Square` does not override `name()`, so its calls fall back to `Shape::name`. A function that is
not virtual in the base is never dispatched, even if a derived class declares one with the same
signature. The derived one only [hides](./inheritance.md#name-lookup-and-name-hiding) it.

## Pure virtual functions and abstract classes

`= 0` declares a **pure virtual** function. A class with at least one pure virtual function, declared
or inherited and not overridden, is **abstract**: you cannot create objects of it, but you can have
pointers and references to it. A derived class becomes concrete once every pure virtual function
has a final overrider. `Shape` above is abstract. `Circle` and `Square` are concrete.

A pure virtual function may still have a definition, written outside the class, which derived
classes can call as `Shape::area()`. A pure virtual destructor *must* have one, because every
derived destructor calls it.

## `override` and `final`

`override` *(C++11)* states that the function is meant to override a base virtual function. If it
doesn't, because of a typo, a different parameter type or a missing `const`, the program is
ill-formed. Without `override`, the same mistakes silently declare a new function that hides the
base one.

```cpp title="override.cpp" showLineNumbers
struct Base {
    virtual ~Base() = default;
    virtual void f(int) {}
    virtual void g() const {}
};
struct Derived : Base {
    void f(int) override {}
    void g() const override {}
    // void f(double) override {}   // error: does not override (parameter type)
    // void g() override {}         // error: does not override (missing const)
};
int main() { Derived d; (void)d; }
```

`final` *(C++11)* on a virtual function forbids further overriding. On a class
(`class Square final`) it forbids deriving from it. Besides documenting intent, `final` lets the
compiler call a function directly when it knows no further override can exist
(see [devirtualization](#devirtualization)). Mark every override with `override` (or `final`) and
don't repeat `virtual` on it. Clang's `-Winconsistent-missing-override` and GCC's
`-Wsuggest-override` flag overrides that lack it.

## Virtual destructors

`delete p` where `p` is a `Base*` pointing at a `Derived` object is **undefined behaviour** unless
`Base`'s destructor is virtual. In practice `~Derived` and the destructors of `Derived`'s members do
not run, but the standard promises nothing at all.

```cpp title="non_virtual_dtor.cpp" showLineNumbers
#include <string>

struct Base {
    virtual void f() {}
    ~Base() {}                       // non-virtual
};
struct Derived : Base {
    std::string name = "leaks if ~Derived never runs";
};

int main() {
    Base* p = new Derived;
    delete p;                        // undefined behaviour: ~Derived is not called
}
```

Both compilers warn under `-Wall` (GCC 15: `-Wdelete-non-virtual-dtor`, Clang 21:
`-Wdelete-non-abstract-non-virtual-dtor`). The same applies
to `std::unique_ptr<Base>` holding a `Derived`, because its default deleter calls `delete` on a
`Base*`. `std::shared_ptr<Base>` created from a `Derived*` is the exception: it records the
deleter for the original type (see [shared_ptr](../06-pointers-references-and-smart-pointers/shared-ptr.md)).

The rule for a base class: its destructor should be either **public and virtual**, if objects may be
deleted through a base pointer, or **protected and non-virtual**, if they must not be (mixins and
[CRTP](../13-idioms-and-design/03-crtp.md) bases). With a virtual destructor, `delete p` runs
`~Derived`, then the member destructors, then `~Base`. The order is on
[constructors and destructors](./constructors-and-destructors.md). Declaring the destructor
(even `= default`) affects which special members the compiler still generates. See
[rule of zero/three/five](./rule-of-zero-three-five.md).

## How dispatch is implemented: vtables

The standard only specifies what a virtual call does, not how. Every mainstream compiler (GCC and
Clang with the Itanium C++ ABI, used on Linux and macOS, and MSVC) uses the same basic design:

- Each polymorphic class has a **vtable**, a static, read-only array of function pointers with one
  slot per virtual function, plus RTTI data the Itanium ABI stores next to it. A derived class's
  vtable starts with the base's slots in the same order. Overridden slots point at the derived
  functions, and new virtual functions get new slots at the end.
- Each object of a polymorphic class carries a hidden **vptr** pointing at its class's vtable. With
  single inheritance it is at offset 0 under the Itanium ABI. The constructor sets it.

<Diagram title="Dispatch through a Circle object (Itanium ABI, simplified)" caption="Objects share their class's vtable; only the vptr is per object." accent="violet">
  <DiagramRow>
    <DiagramGroup label="Circle object">
      <DiagramNode title="vptr" accent>8 bytes on x86-64</DiagramNode>
      <DiagramNode title="r_">double</DiagramNode>
    </DiagramGroup>
    <DiagramArrow direction="right" label="points to" />
    <DiagramGroup label="Circle vtable">
      <DiagramNode title="~Circle">destructor slots</DiagramNode>
      <DiagramNode title="Circle::area">overridden</DiagramNode>
      <DiagramNode title="Circle::name">overridden</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

A call `s->area()` through a `Shape*` compiles to roughly:

<Walkthrough title="What s->area() does" accent="violet">
  <Step title="Load the vptr">

Read the hidden pointer from the object: `vtbl = *(void***)s`. For a `Circle` it now points to
<StepChange>Circle's vtable</StepChange>.

  </Step>
  <Step title="Load the slot">

`area` has a fixed slot index known at compile time from `Shape`'s declaration. Load
`fn = vtbl[index_of_area]`, which is <StepChange>`&Circle::area`</StepChange>.

  </Step>
  <Step title="Indirect call">

Call `fn(s)`, passing `s` as `this`. The callee is whatever the pointer says, so the compiler
cannot inline it unless it can [prove the target](#devirtualization).

  </Step>
</Walkthrough>

Measured with GCC 15 and Clang 21 on x86-64 Linux, adding one virtual function to
`struct { int data; }` grows it from 4 to 16 bytes: an 8-byte vptr, the `int`, and 4 bytes of tail
padding. The byte-level layout, including multiple and virtual bases, is on
[class layout](./class-layout.md) and [object layout](../12-low-level-and-platform/02-object-layout.md).

## What a virtual call costs

- **Space:** one vptr per object (per polymorphic base subobject with multiple inheritance), plus
  one vtable per class.
- **Time:** two dependent loads and an indirect call instead of a direct call. On modern CPUs a
  well-predicted indirect call is cheap. The cost shows up when the target varies unpredictably
  (branch mispredictions) or when the vtables are cold in cache.
- **Lost optimisation:** usually the biggest cost. An indirect call blocks inlining, and with it
  constant propagation and vectorisation across the call. For a tiny function such as a getter in a
  hot loop, that matters far more than the call itself.

How much this matters depends on the workload. Measure with a profiler before restructuring a
design to avoid virtual calls.

## Devirtualization

The compiler turns a virtual call into a direct (and inlinable) call when it can prove the dynamic
type:

- the call is on an object, not a pointer or reference (`Circle c; c.area();`);
- the class or the function is `final`, so a `Square*` or `Square&` can only refer to a `Square`;
- after inlining, the object's construction is visible (`auto c = Circle{1}; Shape& s = c; s.area();`);
- with link-time optimisation and whole-program visibility (for example Clang's
  `-fwhole-program-vtables` with `-flto`, or GCC with `-flto`), the compiler can see that a virtual
  function has a single implementation.

GCC and Clang also do *speculative* devirtualization: compare the loaded function pointer with a
likely target and call it directly if they match. None of this is guaranteed. Check the generated
code if you depend on it.

## Covariant return types

An override may return a pointer or reference to a class *derived from* the base function's return
type. The standard example is `clone()`:

```cpp title="clone.cpp" showLineNumbers
#include <memory>

struct Shape {
    virtual ~Shape() = default;
    virtual Shape* clone() const { return new Shape(*this); }
};

struct Circle : Shape {
    Circle* clone() const override { return new Circle(*this); }  // covariant
};

int main() {
    Circle c;
    std::unique_ptr<Circle> copy{c.clone()};   // no cast needed
    const Shape& s = c;
    std::unique_ptr<Shape> poly{s.clone()};    // dispatches to Circle::clone
}
```

Covariance works only with raw pointers and references. `std::unique_ptr<Circle>` is not
covariant with `std::unique_ptr<Shape>`. The usual workaround is a public non-virtual `clone()`
returning a smart pointer that wraps a private virtual one returning a raw pointer.

## Virtual calls during construction and destruction

While a base-class constructor or destructor runs, the object's dynamic type *is* that base class.
The derived part is not built yet, or has already been destroyed. Virtual calls made then dispatch
to the base's version:

```cpp title="ctor_dispatch.cpp" showLineNumbers
#include <iostream>

struct Base {
    Base()          { hello(); }        // calls Base::hello
    virtual ~Base() { hello(); }        // calls Base::hello
    virtual void hello() const { std::cout << "Base::hello\n"; }
    void run() const { hello(); }       // ordinary dispatch
};

struct Derived : Base {
    Derived()  { hello(); }
    ~Derived() override { hello(); }
    void hello() const override { std::cout << "Derived::hello\n"; }
};

int main() {
    Derived d;
    d.run();
}
```

```text
Base::hello
Derived::hello
Derived::hello
Derived::hello
Base::hello
```

Under the Itanium ABI this is literal: each constructor sets the vptr to its own class's vtable
before running its body, and each destructor resets it. Calling a **pure** virtual function this way
is undefined behaviour. With GCC's and Clang's runtime libraries it typically aborts with "pure virtual method called". If
derived-specific setup must run after construction, use a factory function or a two-phase `init()`
called by the owner.

## Default arguments are bound statically

Default arguments come from the **static** type of the call expression, even though the function
body is picked dynamically:

```cpp title="default_args.cpp" showLineNumbers
#include <iostream>

struct Base {
    virtual ~Base() = default;
    virtual void print(int x = 10) const { std::cout << "Base " << x << '\n'; }
};

struct Derived : Base {
    void print(int x = 20) const override { std::cout << "Derived " << x << '\n'; }
};

int main() {
    Derived d;
    const Base& b = d;
    b.print();   // Derived::print, with Base's default
    d.print();   // Derived::print, with Derived's default
}
```

```text
Derived 10
Derived 20
```

Don't give overrides their own default arguments. Either don't use defaults on virtual functions,
or put them only on a non-virtual public function (see NVI below). Default arguments in general are
covered on [default arguments](../04-functions-and-call-mechanics/default-arguments.md).

## Non-virtual interface (NVI)

The **NVI idiom** keeps the public functions non-virtual and makes the virtual hooks `private` (or
`protected`). The base then controls what happens around every call (checks, logging, locking),
and derived classes only supply the variable step:

```cpp title="nvi.cpp" showLineNumbers
#include <iostream>

class Task {
public:
    virtual ~Task() = default;
    void run() {                        // non-virtual: fixed sequence
        std::cout << "[start]\n";
        do_run();
        std::cout << "[done]\n";
    }
private:
    virtual void do_run() = 0;          // the customisation point
};

class Print final : public Task {
    void do_run() override { std::cout << "printing\n"; }
};

int main() {
    Print p;
    p.run();
}
```

```text
[start]
printing
[done]
```

A derived class can override a `private` virtual function. Access controls who may *call* a name,
not who may override it.

## RTTI: `dynamic_cast` and `typeid`

Polymorphic classes also carry **run-time type information**. With the Itanium ABI, a pointer to
the class's `std::type_info` sits just before the vtable's function slots. Two operators use it:

```cpp title="rtti.cpp" showLineNumbers
#include <iostream>
#include <typeinfo>

struct Base { virtual ~Base() = default; };
struct Derived : Base { void only_derived() const { std::cout << "derived\n"; } };

void inspect(const Base& b) {
    if (auto* d = dynamic_cast<const Derived*>(&b))
        d->only_derived();
    std::cout << typeid(b).name() << '\n';   // dynamic type; name is implementation-defined
}

int main() {
    Derived d;
    inspect(d);
}
```

```text
derived
7Derived
```

- `dynamic_cast<Derived*>(p)` returns `nullptr` if `*p` is not a `Derived` (the reference form
  throws `std::bad_cast`). It needs a polymorphic source type, and it can be much slower than a
  virtual call because it may have to walk the class hierarchy.
- `typeid(expr)` on a polymorphic lvalue gives the dynamic type. `name()` is implementation-defined:
  GCC and Clang return the mangled name (`7Derived` above, demangle with `c++filt -t`), MSVC returns
  a readable one.

Frequent `dynamic_cast` downcasts usually mean an operation belongs in the base interface as a
virtual function. `-fno-rtti` (GCC/Clang) removes RTTI, which disables both operators on
polymorphic types but not virtual dispatch.

## References

- [cppreference: virtual function specifier](https://en.cppreference.com/w/cpp/language/virtual)
- [cppreference: abstract class](https://en.cppreference.com/w/cpp/language/abstract_class)
- [cppreference: override](https://en.cppreference.com/w/cpp/language/override), [final](https://en.cppreference.com/w/cpp/language/final)
- [cppreference: dynamic_cast](https://en.cppreference.com/w/cpp/language/dynamic_cast), [typeid](https://en.cppreference.com/w/cpp/language/typeid)
- [Itanium C++ ABI, virtual table layout](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#vtable)
- Herb Sutter, [Virtuality](http://www.gotw.ca/publications/mill18.htm) (NVI and destructor guideline)
