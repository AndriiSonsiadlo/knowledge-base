---
id: constructors-and-destructors
title: Constructors and Destructors
sidebar_label: Constructors & Destructors
sidebar_position: 3
tags: [c++, classes, constructors, destructors, member-initializer-list, raii]
---

# Constructors and Destructors

A **constructor** turns raw storage into a valid object: it initializes every base and member and
establishes the class's invariant. A **destructor** runs when the object's lifetime ends and releases
whatever the object owns. Because the compiler calls both automatically, at points fixed by the
language, they are the foundation of RAII: a resource tied to an object's lifetime is released on
every path out of a scope, including exceptions. This page is the canonical home for member
initializer lists, the order of construction and destruction, delegating and inheriting
constructors, `explicit`, and `= default` / `= delete`.

**Prerequisites:** [Object lifetime](../05-memory-and-object-lifetime/object-lifetime.md),
[Access control](./access-control.md). Initialization syntax (`T x{}`, `T x()`, `T x = ...`) is covered
in [Uniform initialization](../05-memory-and-object-lifetime/initialization/uniform-initialization.md).

Which special members (copy, move, destructor) a class should declare at all is decided on
[Rule of zero/three/five](./rule-of-zero-three-five.md). How copy and move constructors work is on
[Copy and move semantics](./copy-and-move-semantics.md).

## Declaring constructors

A constructor has the class's name and no return type. A class may have several, chosen by overload
resolution on the arguments. The **default constructor** is the one callable with no arguments.
If you declare no constructor at all, the compiler declares a default constructor for you; declaring
any constructor suppresses that, and `= default` brings it back.

```cpp title="widget.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <utility>

class Widget {
public:
    Widget() = default;                                  // uses the default member initializers
    Widget(int id, std::string name) : id_(id), name_(std::move(name)) {}
    explicit Widget(int id) : Widget(id, "unnamed") {}   // delegating constructor
    int id() const { return id_; }
    const std::string& name() const { return name_; }
private:
    int id_ = 0;                        // default member initializers (C++11)
    std::string name_ = "default";
};

int main() {
    Widget a;
    Widget b(7);
    std::cout << a.id() << ' ' << a.name() << ' ' << b.id() << ' ' << b.name() << '\n';
}
```

```text
0 default 7 unnamed
```

## The member initializer list

The list after the colon (`: id_(id), name_(...)`) **initializes** members and bases. Code in the
constructor body runs later, after every member already exists, so a statement such as
`name_ = name;` in the body is an *assignment* to an already-constructed string, not its
initialization.

These must be initialized by the initializer list or by a default member initializer; they cannot be assigned in the body:

- `const` members and reference members,
- members and bases with no default constructor,
- a base class whose constructor needs arguments.

```cpp title="config.cpp" showLineNumbers
#include <string>

struct Config {
    Config(const std::string& path, int& counter)
        : path(path), counter(counter), retries(3) {}   // cannot be assigned in the body
    const std::string path;
    int& counter;
    const int retries;
};

int main() {
    int n = 0;
    Config c("app.toml", n);
    return c.retries - 3;
}
```

For everything else the list is still the better place: it constructs the member once with the
right value instead of default-constructing it and then assigning. A **default member initializer**
(`int id_ = 0;` in the class body) supplies the value for constructors whose list does not mention
that member, so simple defaults are written once instead of in every constructor.

## Construction and destruction order {#construction-order}

The order in which parts are initialized is fixed by the class definition, **not** by the order you
write the initializer list:

1. Virtual base classes, if any (see [Multiple inheritance](./multiple-inheritance.md)).
2. Direct base classes, left to right as listed after the class name.
3. Non-static data members, in **declaration order**.
4. The constructor body.

Destruction runs the exact reverse: the destructor body, then members in reverse declaration order,
then bases right to left. Reverse order guarantees that while any part is being destroyed, every
part it might depend on still exists.

```cpp title="order.cpp" showLineNumbers
#include <iostream>

struct Tracer {
    const char* name;
    explicit Tracer(const char* n) : name(n) { std::cout << "+" << name << ' '; }
    ~Tracer() { std::cout << "-" << name << ' '; }
};

struct Base1 { Tracer t{"Base1"}; };
struct Base2 { Tracer t{"Base2"}; };

struct Widget : Base1, Base2 {
    Tracer a{"a"};
    Tracer b;
    Widget() : b("b") { std::cout << "body "; }
    ~Widget() { std::cout << "~body "; }
};

int main() {
    { Widget w; std::cout << "| "; }
    std::cout << '\n';
}
```

```text
+Base1 +Base2 +a +b body | ~body -b -a -Base2 -Base1
```

<Walkthrough title="Lifetime of Widget w" caption="Each step is one stage of construction or destruction." accent="blue">
  <Step title="Bases, left to right">

`Base1` is constructed, then `Base2`, because that is the order in `struct Widget : Base1, Base2`.
Output so far: <StepChange>`+Base1 +Base2`</StepChange>

  </Step>
  <Step title="Members, in declaration order">

`a` is declared before `b`, so `a` is initialized first even though only `b` appears in the
initializer list. Output adds <StepChange>`+a +b`</StepChange>

  </Step>
  <Step title="Constructor body">

All parts now exist, and the body runs. The object's lifetime begins when the constructor finishes.
Output adds <StepChange>`body`</StepChange>

  </Step>
  <Step title="Scope ends: destructor body, then members">

The destructor body runs first, while every member is still alive, then members in reverse
declaration order. Output adds <StepChange>`~body -b -a`</StepChange>

  </Step>
  <Step title="Bases, right to left">

Finally the base subobjects, in reverse of their construction order. Output adds
<StepChange>`-Base2 -Base1`</StepChange>

  </Step>
</Walkthrough>

### The initializer-list order trap

Because members are initialized in declaration order, an initializer that reads another member can
read it before it has been set:

```cpp title="reorder.cpp" showLineNumbers
struct Range {
    int* data;   // declared first, so initialized first
    int  size;
    // Listed size-first, but data is initialized first and reads size too early.
    // BUG: size is read before it is initialized (indeterminate value)
    Range(int n) : size(n), data(new int[size]) {}
    ~Range() { delete[] data; }
};

int main() { Range r(3); }
```

GCC and Clang both warn under `-Wall` (`-Wreorder`, Clang: `-Wreorder-ctor`) when the list order
differs from the declaration order. Write the list in declaration order, and avoid initializers that
read other members, so the warning stays meaningful.

## Delegating constructors (C++11)

A constructor may hand off to another constructor of the same class by naming it as the **only**
entry in its initializer list. The target constructor runs completely, then the delegating
constructor's body runs. Mixing delegation with member initializers is ill-formed
(GCC: "mem-initializer for 'W::b' follows constructor delegation").

```cpp
// fragment, see widget.cpp above
explicit Widget(int id) : Widget(id, "unnamed") {}         // OK
// Widget(int id) : Widget(id, "unnamed"), id_(1) {}       // error: delegation must be alone
```

The object counts as constructed once the *target* constructor finishes. If the delegating
constructor's body then throws, the destructor runs.

## `explicit`: no silent conversions

A constructor that can be called with one argument is also an implicit **converting constructor**:
the compiler will use it to turn a value of the argument type into the class type when a function
needs one. Marking it `explicit` disables that, so the conversion has to be written out.

```cpp title="explicit.cpp" showLineNumbers
struct Meters {
    explicit Meters(double v) : value(v) {}
    double value;
};

double twice(Meters m) { return 2 * m.value; }

int main() {
    // twice(3.0);                   // error: no implicit conversion from double to Meters
    return twice(Meters{3.0}) == 6.0 ? 0 : 1;
}
```

Make single-argument constructors `explicit` unless the conversion is genuinely lossless and
expected (`std::string` from `const char*` is the classic intentional case). Copy and move
constructors should not be marked `explicit` (that breaks copy-initialization and return by value). Since C++20, `explicit(condition)` makes it conditional,
which generic wrappers like `std::pair` use. How implicit conversions are ranked is covered in
[Conversions and promotions](../03-types-and-values/conversions-and-promotions.md).

## `= default` and `= delete` (C++11)

`= default` asks for the compiler-generated version of a special member function, for example to
restore the default constructor after declaring another constructor, or to make a defaulted
destructor `virtual`. `= delete` declares a function that exists for overload resolution but makes
any use of it a compile error. Deleted copy operations are the standard way to make a type
non-copyable (see [Non-copyable](../13-idioms-and-design/04-non-copyable.md)). Any function can be
deleted, not only special members, which is useful for rejecting particular argument types:

```cpp
// fragment
void set_ratio(double r);
void set_ratio(int) = delete;   // set_ratio(3) is an error instead of a silent conversion
```

## Exceptions during construction

If a constructor throws, the object never starts its lifetime, so **its destructor is not called**.
Everything that had already been fully constructed is destroyed in reverse order: initialized members
and base subobjects. A resource held by a raw pointer member leaks, because a raw pointer has no
destructor that frees anything. A resource held by an RAII member is released by that member's
destructor.

```cpp title="parser.cpp" showLineNumbers
#include <memory>
#include <stdexcept>
#include <string>

class Parser {
public:
    explicit Parser(const std::string& text)
        : buffer_(std::make_unique<char[]>(text.size() + 1)) {
        if (text.empty()) throw std::invalid_argument("empty input");
        // buffer_ is already constructed, so its destructor frees it if we throw
    }
private:
    std::unique_ptr<char[]> buffer_;
};

int main() {
    try { Parser p(""); } catch (const std::invalid_argument&) { return 0; }
    return 1;
}
```

This is why a class should own at most one raw resource directly, and otherwise hold
[`std::unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md) or containers.
The general pattern is described in [RAII](../13-idioms-and-design/01-raii.md).

Destructors, by contrast, should not throw. Since C++11 a destructor is implicitly `noexcept` unless a
member or base destructor is not, so an exception escaping one calls `std::terminate`. See
[noexcept](../04-functions-and-call-mechanics/noexcept.md).

## Inheriting constructors (C++11)

`using Base::Base;` makes the base class's constructors usable to construct the derived class. Each
inherited constructor initializes the base with the given arguments, and the derived class's own
members get their default member initializers (or default initialization if they have none).

```cpp title="inheriting.cpp" showLineNumbers
struct Base {
    Base(int) {}
    Base(int, int) {}
};

struct Derived : Base {
    using Base::Base;   // Derived(int) and Derived(int, int)
    int extra = 7;      // initialized by its default member initializer
};

int main() {
    Derived d1(1), d2(1, 2);
    return d1.extra + d2.extra - 14;
}
```

Copy and move constructors are not inherited. Use this only when the derived class adds no
invariant of its own; otherwise write the constructor and validate.

## Destructors and polymorphism

A destructor has the name `~ClassName`, takes no parameters, and there is exactly one per class.
Two rules concern class hierarchies, and both are explained on
[Virtual functions](./virtual-functions.md):

- If an object may be deleted through a pointer to its base class, the base's destructor must be
  `virtual`. Otherwise `delete base_ptr` is undefined behavior. See
  [Virtual destructors](./virtual-functions.md#virtual-destructors).
- During a base-class constructor or destructor, virtual calls dispatch to the base's version, not
  the derived override, because the derived part does not exist yet (or any more).

## Trivial destructors

A destructor is **trivial** if it is not user-provided, not virtual, and every base and member also
has a trivial destructor. A trivial destructor does nothing, so the compiler emits no call for it,
and containers can free a block of such elements without visiting each one.

```cpp title="trivial.cpp" showLineNumbers
#include <string>
#include <type_traits>

struct Plain  { int x, y; };
struct Owning { std::string s; };

static_assert(std::is_trivially_destructible_v<Plain>);
static_assert(!std::is_trivially_destructible_v<Owning>);   // std::string must free memory

int main() {}
```

Writing an empty body, `~Plain() {}`, makes the destructor user-provided and therefore non-trivial.
Write `= default` or nothing at all. Constructing objects in raw storage and destroying them by an
explicit destructor call is covered in [Placement new](../05-memory-and-object-lifetime/placement-new.md).

## References

- [cppreference: Constructors and member initializer lists](https://en.cppreference.com/w/cpp/language/constructor)
- [cppreference: Destructors](https://en.cppreference.com/w/cpp/language/destructor)
- [cppreference: `explicit` specifier](https://en.cppreference.com/w/cpp/language/explicit)
- [cppreference: Using-declaration, inheriting constructors](https://en.cppreference.com/w/cpp/language/using_declaration#Inheriting_constructors)
- [C++ Core Guidelines C.41–C.52](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rc-ctor)
