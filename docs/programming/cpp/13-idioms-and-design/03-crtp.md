---
id: crtp
title: CRTP
sidebar_label: CRTP
sidebar_position: 3
tags: [c++, crtp, templates, mixins, static-polymorphism]
---

# CRTP

The **curiously recurring template pattern** has a class derive from a template instantiated with
the class itself: `struct D : Base<D>`. The base is then compiled knowing the exact derived type, so
it can call derived members, return derived references and add per-derived state, all resolved at
compile time. Its practical job is the **mixin**: write a piece of behavior once and stamp it onto
many classes without virtual functions.

How CRTP compares with virtual functions, `std::variant` and concepts as a way to get polymorphism
is owned by [Dynamic vs Static Polymorphism](../07-classes-and-oop/dynamic-vs-static-polymorphism.md#crtp-a-base-class-interface-without-virtual-calls),
which also has the minimal example. This page covers what that page leaves out: mixins, the rules
the pattern depends on, its traps, and the C++23 replacement.

**Prerequisites:** [Class Templates](../08-templates-and-metaprogramming/class-templates.md),
[Inheritance](../07-classes-and-oop/inheritance.md).

## How it works

`Base<D>` is instantiated when `D` is named as a base, and `D` is still an incomplete type at that
point. That has one consequence for everything below: the body of a **member function** of `Base<D>`
may use `D`'s members, because member function bodies are instantiated only when called, after `D`
is complete. The **declarations** of `Base<D>` (data members, member signatures, nested typedefs)
may not.

```cpp title="Fragment: the incomplete-type rule"
template <typename D> struct Base { typename D::inner x; };   // error
struct Der : Base<Der> { using inner = int; };
```

```text
error: invalid use of incomplete type 'struct Der'      (g++ 15)
```

Inside a member function, `static_cast<D&>(*this)` is the downcast to the derived object. It is
well-defined as long as the object really is a `D`.

## Mixin 1: derive operators from one

A mixin supplies several operations from a few the derived class provides. Here `Relational` gives
`>`, `<=` and `>=` from a user-written `<`. (In C++20, defaulting or writing `operator<=>` replaces
this particular example; the point is the shape.)

```cpp title="mixin.cpp" showLineNumbers
#include <cstdio>

template <typename Derived>
struct Relational {
    friend bool operator>(const Derived& a, const Derived& b) { return b < a; }
    friend bool operator<=(const Derived& a, const Derived& b) { return !(b < a); }
    friend bool operator>=(const Derived& a, const Derived& b) { return !(a < b); }
private:
    Relational() = default;
    friend Derived;                 // only Derived can construct the base
};

struct Version : Relational<Version> {
    int major, minor;
    Version(int a, int b) : major(a), minor(b) {}
    friend bool operator<(const Version& a, const Version& b) {
        return a.major != b.major ? a.major < b.major : a.minor < b.minor;
    }
};

template <typename Derived>
class Counted {                     // per-derived state: each Derived has its own counter
public:
    static int alive() { return count_; }
protected:
    Counted() { ++count_; }
    Counted(const Counted&) { ++count_; }
    ~Counted() { --count_; }
private:
    inline static int count_ = 0;
};

struct A : Counted<A> {};
struct B : Counted<B> {};

int main() {
    Version v1{1, 2}, v2{1, 10};
    std::printf("%d %d %d\n", v2 > v1, v1 >= v2, v1 <= v2);
    {
        A a1, a2; B b1;
        A a3 = a1;
        std::printf("A=%d B=%d\n", A::alive(), B::alive());
    }
    std::printf("A=%d B=%d\n", A::alive(), B::alive());
}
```

Output (g++ 15 and clang++ 21, `-std=c++23`, `-O0` and `-O2` identical):

```text
1 0 1
A=3 B=1
A=0 B=0
```

Two details do real work. The private constructor plus `friend Derived;` makes `struct Oops : Relational<Version>` fail to compile when an `Oops` is constructed (see the next section). And `Counted<A>` and
`Counted<B>` are different classes, so they have separate `count_` statics; that is something a
plain non-template base cannot give you. The same mechanism makes `Counted` the standard way to
count instances per class.

## Traps

- **Naming the wrong class.** `struct Circle : Shape<Square>` compiles. A call that does
  `static_cast<const Square&>(*this)` on a `Circle` is then undefined behavior. The defense is to
  make the base's constructor private and `friend Derived` (as above), so only `Derived` can construct
  the base and `struct Circle : Shape<Square>` fails as soon as a `Circle` is constructed. (A
  `static_assert(std::is_base_of_v<Base<D>, D>)` does not help: it is true, since `Square` really does
  derive from `Shape<Square>`.)
- **Using `D` in the base's declarations.** The incomplete-type rule above. To expose a derived
  member type, read it inside a member function or through a trait specialized on `D`; a return type
  of `typename D::value_type` on a member declaration fails the same way. (C++14 `auto` return types
  deduced in the body are a common workaround.)
- **No common base.** `Base<A>` and `Base<B>` are unrelated types, so CRTP gives no
  `std::vector<Base*>`. If you need a heterogeneous collection, use virtual functions, `std::variant`,
  or [type erasure](./06-type-erasure.md).
- **Slicing and public non-virtual bases.** A CRTP base is not meant to be deleted through, so make
  its destructor `protected` and non-virtual, and do not store base pointers.
- **Error messages** from deep mixin stacks are long. Concepts on the derived class's required
  members (`requires` on a function in the base, or `static_assert(requires { ... })` in the body)
  localize them.
- **Code size.** One base instantiation per derived class; for a few tiny mixins that is nothing, but
  a large base class template duplicated across many types grows the binary. No general
  figure applies; measure.

## Static interface and dispatch

When the base calls `static_cast<const D&>(*this).area()`, the call is a direct call that the
compiler can inline, with no vtable or vptr. That is the entire "cost" argument for CRTP; how large the
effect is depends on the call, the inliner and whether a virtual call could have been devirtualized
anyway. This page gives no speedup figure because none holds generally. The trade-off table is on
the [polymorphism](../07-classes-and-oop/dynamic-vs-static-polymorphism.md) page.

## The C++23 alternative: explicit object parameters

C++23 explicit object parameters (`this auto&& self`, P0847) let a plain base class write a member
function that sees the derived type, which removes the template and the downcast:

```cpp title="deducing_this.cpp (-std=c++23)" showLineNumbers
#include <cstdio>

template <typename Derived>
struct Shape {
    double describe() const { return static_cast<const Derived&>(*this).area() + 1; }
};
struct Sq : Shape<Sq> { double area() const { return 4; } };

struct Shape23 {
    double describe(this const auto& self) { return self.area() + 1; }   // self is deduced as Sq23
};
struct Sq23 : Shape23 { double area() const { return 4; } };

int main() { std::printf("%g %g\n", Sq{}.describe(), Sq23{}.describe()); }
```

```text
5 5
```

(g++ 15 and clang++ 21, `-std=c++23`, `-O0` and `-O2`.) `Shape23` is an ordinary class, so it
cannot be misnamed, adds no template parameter to the type, and its derived classes need no
`: Base<Derived>` spelling. It does not replace CRTP where the base needs the derived type in its
declarations (per-derived statics like `Counted`, or member types), because the explicit object
parameter only exists inside the function.

## When to use it

Use CRTP for mixins that need the derived type or per-derived state: instance counting,
operator generation before C++20, `std::enable_shared_from_this<T>` (a standard-library CRTP base),
`std::ranges::view_interface<D>` (C++20), which gives a view its `empty()`, `front()`, `operator[]` and so on from just `begin()`
and `end()`. In C++23 code, prefer an explicit object parameter when only member-function bodies
need the derived type. Reach for virtual functions or a concept instead if you need a heterogeneous
collection or only a compile-time interface check.

## Related

- [Dynamic vs Static Polymorphism](../07-classes-and-oop/dynamic-vs-static-polymorphism.md): the comparison and decision table.
- [Concepts and requires](../08-templates-and-metaprogramming/concepts-and-requires.md): checking an interface without a base class.
- [Policy-Based Design](./07-policy-based-design.md): the sibling pattern that composes behavior from template parameters.

## References

- [cppreference: Curiously recurring template pattern](https://en.cppreference.com/w/cpp/language/crtp)
- [cppreference: Explicit object parameter](https://en.cppreference.com/w/cpp/language/member_functions#Explicit_object_member_functions)
- [cppreference: `std::ranges::view_interface`](https://en.cppreference.com/w/cpp/ranges/view_interface)
- [cppreference: `std::enable_shared_from_this`](https://en.cppreference.com/w/cpp/memory/enable_shared_from_this)
