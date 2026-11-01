---
id: access-control
title: Access Control
sidebar_label: Access Control
sidebar_position: 2
tags: [c++, classes, access-control, encapsulation, friend, inheritance]
---

# Access Control

Access specifiers (`public`, `protected`, `private`) decide which code may **name** a class member.
They are the language's tool for encapsulation: a class keeps its data private so that only its own
member functions can change it, which lets the class guarantee its **invariants**, the conditions
that must hold for every object, such as "the balance is never negative". This page is the canonical
home for member access, `friend`, and how the access of a base class changes under `public`,
`protected` and `private` inheritance.

**Prerequisites:** [Class memory layout](./class-layout.md) is useful but not required. You should
know how to declare a class with members.

Access control is checked at **compile time** and only on names. It does not change the object's
layout in memory (apart from the rare standard-layout rule in [Class layout](./class-layout.md#standard-layout-classes)),
and it is not a security boundary: code that has a pointer to the object can still reach the bytes.

## The three access levels

| Specifier | Member functions and friends of the class | Derived classes | Everyone else |
|---|---|---|---|
| `public` | yes | yes | yes |
| `protected` | yes | yes, through the derived type (see below) | no |
| `private` | yes | no | no |

A specifier applies to every member declared after it, until the next specifier. The only
difference between `class` and `struct` is the default: members and bases of a `class` are `private`
unless stated otherwise, those of a `struct` are `public`. A common convention is `struct` for plain
aggregates of data with no invariant and `class` for types that protect one.

Access is checked **per class, not per object**. A member function may read the private members of
any object of its own class, which is how copy constructors and comparison functions work.

```cpp title="account.cpp" showLineNumbers
#include <stdexcept>

class Account {
public:
    explicit Account(long cents) : balance_(cents) {
        if (cents < 0) throw std::invalid_argument("negative balance");
    }
    bool withdraw(long cents) {
        if (cents < 0 || cents > balance_) return false;   // invariant: balance_ >= 0
        balance_ -= cents;
        return true;
    }
    long balance() const { return balance_; }
    bool same_balance(const Account& other) const {
        return balance_ == other.balance_;   // OK: another Account's private member
    }
private:
    long balance_;
};

int main() {
    Account a{1000};
    a.withdraw(250);
    // a.balance_ = -5;       // error: 'balance_' is private
    return a.balance() == 750 ? 0 : 1;
}
```

Since `balance_` can only change inside `Account`'s own functions, a reader has to check four
functions, not the whole program, to be sure the balance never goes negative. Making the data
private also lets the representation change later (to a decimal type, say) without touching
callers.

## `friend`: granting access to specific code

A **friend** declaration inside a class gives another function or class the same access as the
class's own members. It can name a free function, a member function of another class, or a whole
class. Friendship is granted by the class, never taken. It is not symmetric (`A` befriending `B` does
not make `A` a friend of `B`), not transitive, and not inherited.

The most common legitimate use is a symmetric operator that must be a non-member, because its left
operand is not the class type (`std::ostream& << Vec2`) or because both operands should allow
implicit conversions. Defining the friend inside the class makes it a **hidden friend**: it is found
only by argument-dependent lookup, which keeps overload sets small. Operator overloading itself is
covered in [Operator overloading](../02-language-fundamentals/operators/operator-overloading.md).

```cpp title="vec2.cpp" showLineNumbers
#include <iostream>

class Vec2 {
public:
    Vec2(double x, double y) : x_(x), y_(y) {}

    friend Vec2 operator+(const Vec2& a, const Vec2& b) {
        return {a.x_ + b.x_, a.y_ + b.y_};
    }
    friend std::ostream& operator<<(std::ostream& os, const Vec2& v) {
        return os << '(' << v.x_ << ", " << v.y_ << ')';
    }
private:
    double x_, y_;
};

int main() { std::cout << (Vec2{1, 2} + Vec2{3, 4}) << '\n'; }
```

```text
(4, 6)
```

To befriend a single member function of another class, that class must be complete first:
`friend void Reader::read(const Storage&);`. A whole-class friend (`friend class Reader;`) is
simpler but grants access to every member function `Reader` has now or gains later. Prefer the
narrowest friendship that works, because each friend is one more piece of code that can break the
class's invariants.

## Protected members and the "through the derived type" rule

`protected` members are reachable from member functions of derived classes, which lets a base class
offer hooks to subclasses without making them public. There is one restriction that surprises
people: a derived class may access a protected **non-static** member only through an object of its
own type (or a type derived from it), not through an arbitrary `Base`.

```cpp title="protected.cpp" showLineNumbers
class Base {
protected:
    int counter_ = 0;
};

class Derived : public Base {
public:
    void bump() { ++counter_; }                     // OK: this is a Derived
    void bump_other(Derived& d) { ++d.counter_; }   // OK: through a Derived
    // void bump_base(Base& b) { ++b.counter_; }    // error: 'int Base::counter_' is protected
};

int main() {
    Derived d, e;
    d.bump();
    d.bump_other(e);
}
```

The rule stops one subclass from reaching into the protected state of an unrelated sibling subclass
through a `Base&`. Protected data members are still widely discouraged: every derived class becomes
code that can break the base's invariants. Protected member **functions** are the usual compromise.

## Inheritance access: public, protected, private bases

The access specifier on a base class caps the access of what is inherited. Private members of the
base are never accessible in the derived class, whatever the specifier. The base's own member
functions can of course still use them.

| Member in `Base` | `: public Base` | `: protected Base` | `: private Base` |
|---|---|---|---|
| `public` | public | protected | private |
| `protected` | protected | protected | private |
| `private` | not accessible | not accessible | not accessible |

The specifier also controls who may **convert** a `Derived*` to a `Base*`. With public inheritance
anyone can, which is what makes `Derived` usable wherever a `Base` is expected: an "is-a"
relationship. With private inheritance only `Derived` itself (and its friends) can, so outsiders
cannot treat a `Derived` as a `Base` at all. Private inheritance therefore means "implemented in
terms of": `Derived` reuses `Base`'s code without exposing its interface. A data member does the same
job and is usually clearer. Private inheritance is chosen when the derived class must override a
virtual function of the base or wants the [empty base optimization](./class-layout.md#empty-classes-and-the-empty-base-optimization).
Protected inheritance is rare in practice. Base/derived relationships in general are covered in
[Inheritance](./inheritance.md).

## Re-exposing members with `using`

A `using`-declaration in the derived class redeclares a base member with the access of the section
it appears in. It is how you re-publish chosen members of a privately inherited base, or widen a
protected member to public. It cannot reach a member that is private in the base.

```cpp title="using-access.cpp" showLineNumbers
class Engine {
public:
    void start() {}
    void stop() {}
};

class Car : private Engine {
public:
    using Engine::start;   // public in Car; stop() stays private
};

int main() {
    Car c;
    c.start();
    // c.stop();           // error: stop() is private in Car
    // Engine& e = c;      // error: 'Engine' is an inaccessible base of 'Car'
}
```

## Nested classes

A nested class is a member of the enclosing class, so since C++11 it has the same access as any other
member: it can use the enclosing class's private members. The reverse is not true. The enclosing
class has no special access to the nested class's private members unless the nested class befriends
it.

```cpp title="nested.cpp" showLineNumbers
class Outer {
    int secret_ = 42;

    struct Inner {
        int peek(const Outer& o) const { return o.secret_; }   // OK: Inner is a member
    };
public:
    int read() const { return Inner{}.peek(*this); }
};

int main() { return Outer{}.read() == 42 ? 0 : 1; }
```

Static members follow the same rules as non-static ones: `Config::private_count` is accessible only
in `Config`'s member functions and friends.

## Design guidelines

- Make data members private when the class has an invariant, and provide operations, not a
  getter/setter pair for every field. A public setter that accepts any value is the same as a
  public member.
- Use `struct` with public members when there is no invariant (a point, a config record). Adding
  trivial accessors to such a type only adds noise.
- Prefer protected member functions to protected data.
- Keep friends few and specific. Hidden-friend operators are the standard good case.

## References

- [cppreference: Access specifiers](https://en.cppreference.com/w/cpp/language/access)
- [cppreference: Friend declaration](https://en.cppreference.com/w/cpp/language/friend)
- [cppreference: Derived classes, member access](https://en.cppreference.com/w/cpp/language/derived_class)
- [C++ Core Guidelines C.2, C.9, C.133](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-class)
