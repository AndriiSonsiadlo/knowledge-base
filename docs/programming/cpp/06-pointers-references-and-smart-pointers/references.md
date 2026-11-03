---
id: references
title: References
sidebar_label: References
sidebar_position: 2
tags: [c++, references, aliases, reference-wrapper, dangling, parameters]
---

# References

A **reference** is another name for an existing object. Unlike a [pointer](./raw-pointers.md), it
has no "null" state, must be bound when it is created, and can never be rebound to a different
object. Those restrictions are the point: a function that takes `T&` is saying "there is always an
object here", and the caller does not need `&` and `*` noise to pass it. References are what make
pass-by-reference, operator overloading (`a[i] = v`) and range-`for` over elements practical.

**Prerequisites:** [Raw pointers](./raw-pointers.md). Value categories are explained once, in
[Lvalues and rvalues](../03-types-and-values/value-categories/lvalues-rvalues.md); this page uses the terms without
re-deriving them.

## An alias, not an object

After initialization, a reference and its referent are indistinguishable: every use of the
reference names the referent. Taking `&ref` gives the referent's address, and `sizeof(ref)` is
`sizeof` of the referent.

```cpp title="alias.cpp" showLineNumbers
#include <cassert>

int main() {
    int x = 42;
    int& r = x;               // r names x
    r = 100;                  // writes x
    assert(x == 100 && &r == &x);

    int y = 7;
    r = y;                    // NOT rebinding: assigns y's value to x
    assert(x == 7 && &r == &x);

    static_assert(sizeof(int&) == sizeof(int));
}
```

Three rules follow from this:

- **A reference must be initialized.** `int& r;` is ill-formed (except for members, parameters and
  `extern` declarations, which are bound by the constructor, the call or another definition).
- **A reference cannot be reseated.** Assignment writes through to the referent, as the second
  half of the snippet shows.
- **There is no null reference.** `int& r = *p;` with a null `p` is already undefined behavior at
  the dereference, and the optimizer may assume that references are always valid.

Whether a compiler stores a reference as a hidden pointer or eliminates it entirely is an
implementation detail. Local references are usually optimized away, while a reference *member* or a
reference that crosses a non-inlined function boundary is typically a pointer under the hood on
common ABIs (the Itanium C++ ABI used by GCC and Clang passes `T&` like `T*`). The language does not
specify this, and it never lets you observe a reference's own storage.

## What can bind to what

| Reference type | Binds to | Typical use |
|---|---|---|
| `T&` | non-const lvalues of type `T` | out-parameter, alias into a container element |
| `const T&` | any `T`: lvalue, const lvalue, or rvalue (temporary) | read-only parameter |
| `T&&` *(C++11)* | rvalues of type `T` (and, if `T` is a deduced template parameter, forwarding references that bind anything) | move operations, perfect forwarding |
| `const T&&` | rvalues, including const ones | rare |

The `const T&` row is the one worth understanding: binding a `const T&` (or a `T&&`) directly to a temporary extends that
temporary's lifetime to the reference's ([lifetime extension](../05-memory-and-object-lifetime/object-lifetime.md#lifetime-extension)). See
[how references bind](../03-types-and-values/value-categories/lvalues-rvalues.md#how-references-bind) for the binding rules and
[reference collapsing](../03-types-and-values/value-categories/reference-collapsing.md) for what
`T&&` means in templates. Moving from an rvalue reference is on
[copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

A reference to an array keeps the array's size, unlike a pointer: `int (&a)[5]` binds only to an
`int[5]`, and a template `template <std::size_t N> void f(int (&a)[N])` deduces `N`.

## Function parameters

Choose the parameter type by what the function does with the argument:

| The function... | Parameter | Call site |
|---|---|---|
| reads a cheap type (`int`, `double`, a pointer) | by value | `f(x)` |
| reads an expensive type (`std::string`, a vector) | `const T&` | `f(x)` |
| modifies the caller's object | `T&` | `f(x)` (nothing says it is modified) |
| keeps its own copy of the argument | by value, then `std::move` into place | `f(x)` or `f(std::move(x))` |
| may be absent | `T*` or `std::optional<T>` (a reference cannot be null) | `f(&x)`, `f(nullptr)` |

The "modifies" row is the one where pointers still compete: `f(&x)` shows the mutation at the call
site, `f(x)` does not. Some style guides (the Google C++ style guide used to) require a pointer for
output parameters for that reason, while the C++ Core Guidelines (F.20) prefer returning the
result, using a struct or tuple for several values. Returning a value is also cheap, because of
copy elision and moves.

```cpp title="params.cpp" showLineNumbers
#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>

std::size_t length(const std::string& s) { return s.size(); }   // no copy

void shout(std::string& s) {                                     // modifies the caller's string
    for (char& c : s) c = static_cast<char>(c - 'a' + 'A');      // `char&` aliases each element
}

struct Person {
    std::string name;
    explicit Person(std::string n) : name(std::move(n)) {}       // by value + move
};

int main() {
    std::string s = "hello";
    std::printf("%zu\n", length(s));
    std::printf("%zu\n", length("temporary"));    // const& binds a temporary std::string
    shout(s);
    std::printf("%s\n", s.c_str());
    Person p{std::string("Ada")};
    std::printf("%s\n", p.name.c_str());
}
```

```text
5
9
HELLO
Ada
```

(The `shout` conversion is ASCII-only and for illustration; use `std::toupper` with care for real text.)

## Returning references

Returning `T&` is how `operator[]`, `front()`, assignment operators and getters hand out access to
an existing object without a copy. It is valid only while that object lives longer than the call:
a reference to a local variable or to a temporary dangles the moment the function returns.

```cpp title="return-ref.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <vector>

class Registry {
    std::vector<std::string> names_{"a", "b"};
public:
    std::string& at(std::size_t i) { return names_[i]; }              // refers to a member: fine
    const std::string& at(std::size_t i) const { return names_[i]; }  // const overload
};

const std::string& longest_bad(const std::string& a, const std::string& b) {
    return a.size() >= b.size() ? a : b;   // returns one of the arguments
}

int main() {
    Registry r;
    r.at(0) = "changed";                   // assigns into the vector element
    std::printf("%s\n", r.at(0).c_str());

    std::string x = "abc", y = "de";
    const std::string& l = longest_bad(x, y);   // fine: x and y outlive l
    std::printf("%s\n", l.c_str());

    // const std::string& oops = longest_bad("abc", "de");
    // The temporaries die at the end of this statement, and the function's return
    // does NOT extend their lifetime: oops would dangle.
}
```

```text
changed
abc
```

The commented-out line is the standard trap: lifetime extension applies only when a reference is bound
*directly* to a temporary, not when it passes through a function's return value. The rules, the
compiler warnings and the range-`for` pitfall are on
[lifetime extension](../05-memory-and-object-lifetime/object-lifetime.md#lifetime-extension).

## Reference members

A class can hold a reference member, bound in the constructor's member-initializer list. This makes
the class non-assignable by default (the implicit copy assignment is deleted, because a reference
cannot be rebound), and the referent must outlive the object. Most code is better off with a
pointer member (nullable, reassignable) or a value. The usual legitimate use is a non-owning
"view" or "context" object that is constructed and destroyed within the referent's lifetime.

## `std::reference_wrapper`

Containers need element types that are copyable and assignable, which references are not, so
`std::vector<int&>` is ill-formed. `std::reference_wrapper<T>` *(C++11, `<functional>`)* is a
copyable, assignable object that holds a reference to a `T` and converts implicitly back to `T&`. The
standard library utilities page covers it in more depth ([utilities](../09-standard-library/utilities.md)).
`std::ref(x)` and `std::cref(x)` create one. It is also how you pass an argument *by reference* to
`std::thread` or `std::bind`, which copy their arguments by default.

```cpp title="refwrap.cpp" showLineNumbers
#include <algorithm>
#include <cstdio>
#include <functional>
#include <vector>

int main() {
    int a = 3, b = 1, c = 2;
    std::vector<std::reference_wrapper<int>> view{a, b, c};     // refers to the originals

    std::sort(view.begin(), view.end());     // compares the ints; reorders only the wrappers
    for (int& v : view) std::printf("%d ", v);
    std::puts("");

    view[0].get() = 100;                     // writes through to b
    std::printf("a=%d b=%d c=%d\n", a, b, c);
}
```

```text
1 2 3 
a=3 b=100 c=2
```

The vector holds the three wrappers in sorted order, while `a`, `b`, `c` keep their positions. That
is the typical use: a sorted or filtered *view* over objects you cannot or do not want to move.

## References versus pointers

| | Reference | Pointer |
|---|---|---|
| Can be null | no | yes |
| Must be initialized | yes | no (but should be) |
| Can be rebound | no | yes |
| Supports arithmetic / walking an array | no (array refs keep their size) | yes, see [pointer arithmetic](./pointer-arithmetic.md) |
| Can be stored in a container | not directly (use `reference_wrapper`) | yes |
| Syntax at the use site | the same as the object | `*p`, `p->` |
| Overloaded operators | natural (`a + b`) | operate on the address |

Use a reference when the object must exist and you do not need to rebind; use a pointer for
optional or reassignable access; use a smart pointer when ownership is part of the story.

## Pitfalls

- **Dangling reference to a local or temporary**, covered above. Never return `T&` to a local.
- **A reference into a container that reallocates.** `auto& first = v[0]; v.push_back(x);` may leave
  `first` dangling, exactly as with a pointer.
- **Using `auto` and losing the `&`.** `auto x = v[0];` copies; `auto& x = v[0];` aliases.
- **Expecting assignment to rebind.** It assigns through; to switch targets use a pointer or
  `std::reference_wrapper::operator=`.
- **A lambda capturing by reference** that outlives its variables. The lambda is an object holding
  references, and it dangles in the same way.

## Key points

- A reference is a permanent alias: initialized once, never null, never rebound.
- `const T&` for read-only parameters; `T&` for modified ones; pointers when "absent" must be expressible.
- Returned references must refer to something that outlives the call.
- `std::reference_wrapper` is the copyable, container-friendly stand-in.

## Related

- [Lvalues and rvalues](../03-types-and-values/value-categories/lvalues-rvalues.md): the categories that decide what a reference may bind to.
- [Copy and move semantics](../07-classes-and-oop/copy-and-move-semantics.md): what `T&&` parameters are for.
- [const and pointers](./const-and-pointers.md): `const` on the referent, and how it differs from `const` on a pointer.
