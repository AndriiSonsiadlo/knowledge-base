---
id: class-templates
title: Class Templates
sidebar_label: Class Templates
sidebar_position: 3
tags: [c++, templates, class-templates, generic-programming, dependent-names]
---

# Class Templates

A **class template** is a pattern for a family of classes. `std::vector<int>` and
`std::vector<std::string>` come from one definition, but they are two unrelated types with their own
members, their own static data, and no conversion between them. Containers, smart pointers,
`std::optional` and `std::function` are all class templates. This page is the canonical home for
defining class templates and their members, lazy member instantiation, static members per
specialization, template template parameters, member templates, and the `typename`/`template`/
`this->` rules for dependent names.

**Prerequisites:** [Function Templates](./function-templates.md) (instantiation, why definitions go
in headers), [Constructors and Destructors](../07-classes-and-oop/constructors-and-destructors.md).

Deducing a class template's arguments from a constructor call (`std::vector v{1, 2}`) is
[CTAD](./template-argument-deduction.md#class-template-argument-deduction-c17). Giving one
specialization a different definition is [Full](./specialization/full-specialization.md) or
[Partial Specialization](./specialization/partial-specialization.md).

## Defining a class template

```cpp title="fixed_stack.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>
#include <string>
#include <utility>

template <typename T, std::size_t Capacity>
class FixedStack {
public:
    bool push(T value);
    T& top() { return items_[size_ - 1]; }
    void pop() { --size_; }
    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }

private:
    T items_[Capacity]{};
    std::size_t size_ = 0;
};

// Out-of-class member definition: repeat the template header and name FixedStack<T, Capacity>.
template <typename T, std::size_t Capacity>
bool FixedStack<T, Capacity>::push(T value) {
    if (size_ == Capacity) return false;
    items_[size_++] = std::move(value);
    return true;
}

int main() {
    FixedStack<std::string, 2> s;   // FixedStack<std::string, 3> would be a different type
    s.push("a");
    s.push("b");
    std::printf("%d %zu %s\n", s.push("c"), s.size(), s.top().c_str());
}
```

```text
0 2 b
```

Inside the class body the bare name `FixedStack` means the current specialization
(`FixedStack<T, Capacity>`), the **injected-class-name**. Outside it, in the out-of-class definition,
you must spell out the arguments. `Capacity` is a non-type template parameter: it must be a constant
expression and becomes part of the type, so the array size is fixed at compile time. Member
definitions follow the same rule as function templates: they must be visible wherever they are
instantiated, so in practice they live in the header.

## Members are instantiated on demand

Naming `FixedStack<std::string, 2>` instantiates the class **definition**: data members, base
classes, member declarations. It does **not** instantiate the bodies of member functions. Each member
function is instantiated only when it is used. A class template can therefore be used with a type
that supports only some of its operations, as long as you only call those.

```cpp title="lazy_members.cpp" showLineNumbers
#include <cstdio>

struct NoLess {};

template <typename T>
struct Pair {
    T a, b;
    T smaller() const { return b < a ? b : a; }   // needs operator<
    void swap() { T t = a; a = b; b = t; }
};

int main() {
    Pair<NoLess> p{};     // fine: smaller() is never called, so never instantiated
    p.swap();
    // p.smaller();       // error only here: no operator< for NoLess
    std::puts("ok");
}
```

The standard library relies on this. `std::vector<T>::resize(n)` requires `T` to be
default-insertable, but a `std::vector` of a type without a default constructor is fine if you never
call it. The flip side: an error in a rarely used member can hide until someone calls it. Explicit
instantiation (`template class Pair<int>;`) instantiates every member and flushes those errors out,
which is useful in a test.

<Diagram title="What is instantiated when" caption="Using a specialization as a type instantiates the class definition. Each member function body waits for its first use." accent="green">
  <DiagramNode variant="pill">Pair&lt;NoLess&gt; p{};</DiagramNode>
  <DiagramArrow label="instantiates" />
  <DiagramGroup label="Pair&lt;NoLess&gt;">
    <DiagramNode title="Class definition" accent>members a, b; declarations of smaller() and swap()</DiagramNode>
    <DiagramNode title="swap() body">instantiated by p.swap()</DiagramNode>
    <DiagramNode title="smaller() body" dashed>never instantiated, so never checked</DiagramNode>
  </DiagramGroup>
</Diagram>

## Static members: one per specialization

Each specialization is a separate class, so each has its own static data members.

```cpp title="counter.cpp" showLineNumbers
#include <cstdio>

template <typename T>
struct Counter {
    Counter()  { ++live; }
    ~Counter() { --live; }
    inline static int live = 0;   // C++17: defined in the class, one variable per specialization
};

int main() {
    Counter<int> a, b, c;
    Counter<double> d;
    std::printf("%d %d\n", Counter<int>::live, Counter<double>::live);
}
```

```text
3 1
```

Before C++17 a non-`const` static data member had to be defined outside the class:
`template <typename T> int Counter<T>::live = 0;`. That definition can go in the header, because a
templated static member is allowed to be defined in every translation unit. `inline static` is the
shorter modern form (see [inline variables](../04-functions-and-call-mechanics/inline-functions.md#inline-variables-c17)).

## Default arguments and template template parameters

Template parameters can have defaults, and a parameter can itself be a template. A **template
template parameter** accepts a class template, not a type, so the class can choose which
specialization to build:

```cpp title="stack_tt.cpp" showLineNumbers
#include <cstdio>
#include <deque>
#include <list>
#include <vector>

template <typename T, template <typename> class Container = std::vector>
class Stack {
public:
    void push(const T& v) { data_.push_back(v); }
    T pop() { T v = data_.back(); data_.pop_back(); return v; }
    bool empty() const { return data_.empty(); }
private:
    Container<T> data_;   // the container's allocator parameter takes its default
};

int main() {
    Stack<int> a;                    // std::vector<int>
    Stack<double, std::list> b;      // std::list<double>
    Stack<char, std::deque> c;       // std::deque<char>
    a.push(1); b.push(2.5); c.push('x');
    std::printf("%d %.1f %c\n", a.pop(), b.pop(), c.pop());
}
```

```text
1 2.5 x
```

`std::vector` has **two** template parameters (`T` and `Allocator`, the second defaulted), yet it
matches `template <typename> class`. That has only been allowed since C++17 (P0522R0). Before that,
the parameter kinds had to match exactly: GCC 15 rejects this code with `-std=c++14` ("type/value
mismatch"), while Clang 21 accepts it there too. For pre-C++17 code, declare the parameter as
`template <typename...> class Container`.

In practice a plain type parameter is usually simpler: `std::stack<T, Container = std::deque<T>>`
takes the full container type, which also lets users pass a custom allocator.

## Member templates and friends

A class template can have member function templates, and a friend function defined inside it becomes
a separate non-template function for each specialization.

```cpp title="box.cpp" showLineNumbers
#include <iostream>

template <typename T>
class Box {
public:
    explicit Box(T v) : value_(v) {}

    // Hidden friend: one ordinary function per Box<T>, found only by argument-dependent lookup.
    friend std::ostream& operator<<(std::ostream& os, const Box& b) {
        return os << "Box(" << b.value_ << ')';
    }

    template <typename U>
    Box<U> as() const { return Box<U>(static_cast<U>(value_)); }   // member template

private:
    T value_;
};

int main() {
    Box<double> d(2.75);
    std::cout << d << ' ' << d.as<int>() << '\n';
}
```

```text
Box(2.75) Box(2)
```

The **hidden friend** is the simplest way to give a class template operators. Declaring a friend
*template* outside the class instead (`template <typename U> friend std::ostream& operator<<(...,
const Box<U>&)`) also works, but it makes every `operator<<` specialization a friend of every `Box`.
Note that `Box<int>` cannot read `Box<double>::value_`: different specializations are different
classes, so `as<U>()` goes through the public constructor.

## Dependent names: `typename`, `template`, `this->`

Inside a template, a name that depends on a template parameter is not looked up until instantiation.
The compiler still has to parse the code before that, so three rules tell it what such a name is:

```cpp title="dependent_names.cpp" showLineNumbers
#include <cstdio>
#include <vector>

template <typename Container>
typename Container::value_type first(const Container& c) {
    typename Container::const_iterator it = c.begin();   // 'typename': this name is a type
    return *it;
}

struct Factory {
    template <typename T> static T make() { return T{}; }
};

template <typename F>
int build() {
    return F::template make<int>();   // 'template': make is a member template, '<' is not less-than
}

template <typename T>
struct Base { int value = 7; };

template <typename T>
struct Derived : Base<T> {
    int get() const { return this->value; }   // 'this->': value is in a dependent base
};

int main() {
    std::vector<int> v{4, 5};
    std::printf("%d %d %d\n", first(v), build<Factory>(), Derived<int>{}.get());
}
```

```text
4 0 7
```

1. **`typename`** marks a dependent qualified name as a type. Without it, `Container::const_iterator`
   is assumed to be a value. C++20 (P0634) dropped the requirement in places where only a type can
   appear, such as the return type above, but it is still needed for a local variable declaration
   like line 6.
2. **`template`** after `::`, `.` or `->` says the next name is a template, so the `<` that follows
   opens an argument list.
3. **`this->`** (or `Base<T>::`) is needed to use members of a base class that depends on `T`.
   Unqualified names are not looked up in dependent bases, because a specialization of `Base` might
   not have them. Without `this->`, GCC 15 reports "'value' was not declared in this scope".

## Pitfalls

- **Specializations are unrelated types.** `Box<Derived>` does not convert to `Box<Base>`, and a
  `std::vector<Derived*>` is not a `std::vector<Base*>`. Provide a converting constructor template if
  you need it, as `std::unique_ptr` does.
- **Errors in unused members stay hidden** until something calls them. Use an explicit instantiation
  in a test to check every member.
- **Every non-type argument is a new type.** `FixedStack<int, 2>` and `FixedStack<int, 3>` share no
  code unless the compiler merges identical functions. Many sizes means more code.
- **Forgetting `this->`** in a class that derives from a dependent base gives "not declared" errors,
  or silently picks a global with the same name.

## References

- [cppreference: Class template](https://en.cppreference.com/w/cpp/language/class_template)
- [cppreference: Member templates](https://en.cppreference.com/w/cpp/language/member_template)
- [cppreference: Template parameters (template template parameters)](https://en.cppreference.com/w/cpp/language/template_parameters)
- [cppreference: Dependent names](https://en.cppreference.com/w/cpp/language/dependent_name)
- [P0522R0: Matching of template template-arguments excludes compatible templates](https://wg21.link/p0522r0)
- [P0634R3: Down with `typename`!](https://wg21.link/p0634r3)
