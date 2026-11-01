---
id: object-slicing
title: Object Slicing
sidebar_label: Object Slicing
sidebar_position: 9
tags: [c++, object-slicing, polymorphism, inheritance, pitfalls]
---

# Object Slicing

**Object slicing** happens when a derived object is copied into an object of a base type. The base
copy constructor or copy assignment only knows about the base subobject, so it copies that part and
ignores the rest. The result is a plain base object: the derived members are gone, and virtual calls
on it run the base versions. Nothing about it is an error to the compiler, which is why it is a
common bug in polymorphic code. This page is the canonical home for slicing; how virtual dispatch
works is on [Virtual Functions and vtables](./virtual-functions.md).

**Prerequisites:** [Inheritance](./inheritance.md), [Virtual Functions and vtables](./virtual-functions.md),
[Copy and Move Semantics](./copy-and-move-semantics.md).

## How a copy slices

A derived object contains its base as a subobject ([class layout](./class-layout.md)). A variable of
type `Animal` has room for exactly one `Animal`, and its dynamic type is always `Animal`. Copying a
`Dog` into it calls `Animal(const Animal&)`, which binds the reference to the `Animal` subobject of
the `Dog` and copies that.

<Diagram title="Animal sliced = dog;" caption="Only the base subobject is copied. The new object's vptr points to Animal's vtable." accent="amber">
  <DiagramGroup label="Dog d">
    <DiagramNode title="Animal subobject" accent>vptr → Dog vtable, legs</DiagramNode>
    <DiagramNode title="Dog members">breed</DiagramNode>
  </DiagramGroup>
  <DiagramArrow label="Animal(const Animal&)" />
  <DiagramGroup label="Animal sliced">
    <DiagramNode title="Animal object" accent>vptr → Animal vtable, legs copied</DiagramNode>
    <DiagramNode title="breed" dashed>not copied: no room, not known to Animal</DiagramNode>
  </DiagramGroup>
</Diagram>

The constructor sets the new object's vptr for its own class, so virtual calls on `sliced` go to
`Animal`. The vptr is an implementation mechanism (the standard only says the object's dynamic type
is `Animal`), but it explains why the override "disappears".

```cpp title="slicing.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

struct Animal {
    virtual ~Animal() = default;
    virtual const char* speak() const { return "..."; }
    int legs = 4;
};

struct Dog : Animal {
    const char* speak() const override { return "Woof"; }
    std::string breed = "Labrador";
};

void by_value(Animal a)      { std::printf("by value:     %s\n", a.speak()); }
void by_ref(const Animal& a) { std::printf("by reference: %s\n", a.speak()); }

int main() {
    Dog d;
    Animal sliced = d;                     // copies only the Animal subobject
    std::printf("sliced:       %s\n", sliced.speak());
    by_value(d);
    by_ref(d);

    std::vector<std::unique_ptr<Animal>> zoo;
    zoo.push_back(std::make_unique<Dog>());
    std::printf("unique_ptr:   %s\n", zoo[0]->speak());
}
```

Output (g++ 15, clang++ 21):

```text
sliced:       ...
by value:     ...
by reference: Woof
unique_ptr:   Woof
```

## Where slicing happens

Every place that copies or moves into a base-typed *object* slices:

- **Initialization:** `Animal a = d;`, `Animal a(d);`, `Animal a{d};`.
- **Pass by value:** a parameter of type `Animal` initialized from a `Dog`.
- **Return by value:** a function returning `Animal` that returns a `Dog`.
- **Containers of base objects:** `std::vector<Animal>::push_back(dog)` stores an `Animal`.
- **Catch by value:** `catch (std::exception e)` slices a `std::runtime_error` and loses its
  override of `what()`. Catch by `const&`.

Moves slice the same way: `Animal a = std::move(d);` runs `Animal(Animal&&)` on the base part.

## Assignment through a base reference

Slicing also happens without creating a new object. Assigning through a base reference calls the
base class's `operator=`, which is not virtual, so only the base members of the target are
overwritten:

```cpp title="partial_assign.cpp" showLineNumbers
#include <cstdio>
#include <string>

struct Animal {
    virtual ~Animal() = default;
    Animal() = default;
    Animal(const Animal&) = default;
    Animal& operator=(const Animal&) = default;
    std::string name;
};

struct Dog : Animal {
    std::string breed;
};

int main() {
    Dog rex;   rex.name = "Rex";   rex.breed = "Labrador";
    Dog fido;  fido.name = "Fido"; fido.breed = "Beagle";

    Animal& ref = rex;
    ref = fido;            // Animal::operator=: copies name only
    std::printf("%s the %s\n", rex.name.c_str(), rex.breed.c_str());
}
```

Output: `Fido the Labrador`. `rex` is now half of each dog. This is often called **partial
assignment**. It is worse than ordinary slicing because the result is an object of the right type
in an inconsistent state.

## Avoiding it

1. **Handle polymorphic objects through references or pointers.** Take parameters as
   `const Animal&` or `Animal&`, and store them as `std::unique_ptr<Animal>` (or
   `std::shared_ptr` when ownership is shared, see [unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md)).
2. **Catch exceptions by reference:** `catch (const std::exception& e)`.
3. **Make the base impossible to copy from outside.** If a class is abstract, it cannot be
   instantiated, so `Shape s = sq;` is already an error. Making the base's copy operations
   `protected` also blocks partial assignment through a base reference, while derived classes can
   still use them in their own copy operations. For a polymorphic copy, add a virtual `clone()`.

```cpp title="no_slicing.cpp" showLineNumbers
#include <memory>

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual std::unique_ptr<Shape> clone() const = 0;

protected:
    Shape() = default;
    Shape(const Shape&) = default;              // derived classes can still copy
    Shape& operator=(const Shape&) = default;
};

class Square final : public Shape {
public:
    explicit Square(double s) : side_(s) {}
    double area() const override { return side_ * side_; }
    std::unique_ptr<Shape> clone() const override { return std::make_unique<Square>(*this); }
private:
    double side_;
};

int main() {
    Square sq(2.0);
    Square copy = sq;                 // fine: copying the complete type
    // Shape s = sq;                  // error: Shape is abstract and its copy ctor is protected
    const Shape& ref = sq;
    // Shape& r2 = copy; r2 = ref;    // error: Shape::operator= is protected
    std::unique_ptr<Shape> p = ref.clone();   // polymorphic copy
    return p->area() == copy.area() ? 0 : 1;
}
```

Because `Shape` now declares a destructor and copy operations, it also controls which moves exist;
see [Rule of 0/3/5](./rule-of-zero-three-five.md#polymorphic-base-classes).

## Compiler diagnostics

Neither GCC 15 (with `-Wall -Wextra -Weffc++`) nor Clang 21 (even with `-Weverything`) warns about
the slicing copies in `slicing.cpp` above. Clang's `-Wdeprecated` reports the implicit copy
constructor of `Animal` as deprecated (because `Animal` declares a destructor), which points at the
copy but does not say "slicing". The one compiler warning aimed at slicing is GCC's
`-Wcatch-value` (enabled by `-Wall`), which reports `catching polymorphic type 'class
std::exception' by value`.

clang-tidy's `cppcoreguidelines-slicing` check does find the copies. On `slicing.cpp` (clang-tidy 21):

```text
22:21: warning: slicing object from type 'Dog' to 'Animal' discards 36 bytes of state [cppcoreguidelines-slicing]
22:21: warning: slicing object from type 'Dog' to 'Animal' discards override 'speak' [cppcoreguidelines-slicing]
24:14: warning: slicing object from type 'Dog' to 'Animal' discards 36 bytes of state [cppcoreguidelines-slicing]
24:14: warning: slicing object from type 'Dog' to 'Animal' discards override 'speak' [cppcoreguidelines-slicing]
```

Even with tooling, the protected-copy design above is the reliable defense,
because it turns the mistake into a compile error.

## References

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), rules C.67
  (a polymorphic class should suppress public copy/move) and C.145 (access polymorphic objects
  through pointers and references), and E.15 (catch exceptions from a hierarchy by reference)
- clang-tidy: [cppcoreguidelines-slicing](https://clang.llvm.org/extra/clang-tidy/checks/cppcoreguidelines/slicing.html)
