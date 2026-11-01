---
id: rule-of-zero-three-five
title: Rule of 0/3/5
sidebar_label: Rule of 0/3/5
sidebar_position: 5
tags: [c++, special-members, rule-of-five, rule-of-zero, raii]
---

# Rule of 0/3/5

The compiler can write six **special member functions** for a class: the default constructor, the
destructor, and the four copy and move operations. Whether it writes them, and whether what it
writes is correct, depends on what else you declared. The rules of zero, three and five are the
guidelines for choosing which ones to declare yourself. This page is the canonical home for that
decision and for the implicit-generation rules behind it. What copy and move operations *do* is on
[Copy and Move Semantics](./copy-and-move-semantics.md).

**Prerequisites:** [Copy and Move Semantics](./copy-and-move-semantics.md),
[constructors and destructors](./constructors-and-destructors.md),
[RAII](../13-idioms-and-design/01-raii.md).

## The six special members

```cpp title="Fragment: declarations only"
class Widget {
public:
    Widget();                                // default constructor
    ~Widget();                               // destructor
    Widget(const Widget&);                   // copy constructor
    Widget& operator=(const Widget&);        // copy assignment
    Widget(Widget&&) noexcept;               // move constructor   (C++11)
    Widget& operator=(Widget&&) noexcept;    // move assignment    (C++11)
};
```

An implicitly generated member does the obvious member-wise thing: the copy constructor copies each
base and member, the destructor destroys them, and so on. That is exactly right when every member
manages itself, and exactly wrong when a member is a raw handle (an owning pointer, a file
descriptor) whose meaning the compiler cannot know.

## Implicit generation rules

"User-declared" below includes `= default` and `= delete`. The rows are what you declare; the
columns are what the compiler then gives you.

| You declare | Default ctor | Destructor | Copy ctor | Copy assign | Move ctor | Move assign |
|---|---|---|---|---|---|---|
| Nothing | implicit | implicit | implicit | implicit | implicit | implicit |
| Any constructor | not declared | implicit | implicit | implicit | implicit | implicit |
| Destructor | implicit | **yours** | implicit, deprecated | implicit, deprecated | not declared | not declared |
| Copy constructor | not declared | implicit | **yours** | implicit, deprecated | not declared | not declared |
| Copy assignment | implicit | implicit | implicit, deprecated | **yours** | not declared | not declared |
| Move constructor | not declared | implicit | deleted | deleted | **yours** | not declared |
| Move assignment | implicit | implicit | deleted | deleted | not declared | **yours** |

Two consequences matter in practice:

- **"Not declared" move means moves silently copy.** An rvalue then binds to the copy constructor,
  so `std::move` still compiles. Declaring only a destructor, even `virtual ~Base() = default;`,
  turns every move of the class into a copy.
- **"Deprecated" still compiles.** The implicit copy in a class with a user-declared destructor or
  copy operation was deprecated in C++11 but never removed. GCC warns with `-Wdeprecated-copy-dtor`
  (not in `-Wall`) and Clang with `-Wdeprecated`.

The rules can be checked with type traits:

```cpp title="generation.cpp" showLineNumbers
#include <type_traits>

struct DtorOnly { ~DtorOnly() {} };                       // copy still implicit (deprecated), no move
struct CopyOnly { CopyOnly() = default; CopyOnly(const CopyOnly&) {} };
struct MoveOnly { MoveOnly() = default; MoveOnly(MoveOnly&&) noexcept {} };

// Moves of DtorOnly and CopyOnly silently fall back to copying:
static_assert(std::is_move_constructible_v<DtorOnly>);    // satisfied by the copy ctor
static_assert(std::is_move_constructible_v<CopyOnly>);    // also the copy ctor
// Declaring a move constructor deletes the implicit copy operations
// and suppresses the implicit move assignment:
static_assert(!std::is_copy_constructible_v<MoveOnly>);
static_assert(!std::is_copy_assignable_v<MoveOnly>);
static_assert(!std::is_move_assignable_v<MoveOnly>);

struct WithCtor { WithCtor(int) {} };                     // no implicit default ctor
static_assert(!std::is_default_constructible_v<WithCtor>);

int main() {}
```

An implicitly declared member can also end up **defined as deleted** even with nothing declared,
when a member or base makes it impossible: a `std::unique_ptr` member deletes the copy operations,
and a `const` or reference member deletes the assignments.

## Rule of zero

> If a class does not directly own a resource, declare none of the five (destructor, copy and move
> operations). Let members that are already correct do the work.

This is the default for almost every class. Wrap each resource in a type that manages exactly that
resource (a container, a smart pointer, a lock, a file wrapper), and compose classes from those.
The implicit members then copy, move and destroy correctly, and the moves are `noexcept` whenever
the members' moves are.

```cpp title="rule_of_zero.cpp" showLineNumbers
#include <cstddef>
#include <memory>
#include <type_traits>
#include <vector>

class Buffer {                           // rule of zero: vector owns the bytes
public:
    explicit Buffer(std::size_t n) : data_(n) {}
    std::size_t size() const { return data_.size(); }
private:
    std::vector<char> data_;
};

class Handle {                           // rule of zero, move-only by composition
    std::unique_ptr<int> p_ = std::make_unique<int>(0);
};

static_assert(std::is_copy_constructible_v<Buffer> && std::is_nothrow_move_constructible_v<Buffer>);
static_assert(!std::is_copy_constructible_v<Handle> && std::is_nothrow_move_constructible_v<Handle>);

int main() {}
```

`Handle` shows that the rule of zero also covers copy *policy*: a `unique_ptr` member makes the class
move-only without a single `= delete`. For a non-memory resource, a `unique_ptr` with a custom
deleter is often enough of a wrapper ([custom
deleters](../06-pointers-references-and-smart-pointers/custom-deleters.md)).

## Rule of three

> If a class needs a user-provided destructor, copy constructor, or copy assignment operator, it
> almost certainly needs all three.

The rule dates from C++98. A destructor that releases something means the class owns it, and then
the implicit member-wise copy is wrong: it copies the handle, not the resource, and both objects
release it.

```cpp title="double_free.cpp" showLineNumbers
struct Broken {
    int* data;
    explicit Broken(int v) : data(new int(v)) {}
    ~Broken() { delete data; }
};
int main() {
    Broken b1(42);
    Broken b2 = b1;   // copies the pointer, not the int
}
```

Both destructors delete the same pointer. Built with `-fsanitize=address`, the program stops with
`AddressSanitizer: attempting double-free`. GCC 15 also flags the copy with
`-Wdeprecated-copy-dtor`, and Clang 21 with `-Wdeprecated`, which is a reason to enable them.

## Rule of five

> If a class declares any of the destructor or the four copy and move operations, declare all five,
> using `= default` or `= delete` for the ones whose implicit behavior you want or want removed.

C++11 added the move operations, and the generation table shows why the rule grew from three to
five: declaring a destructor or copy operation quietly removes the moves. A class that owns a raw
resource writes all five:

```cpp title="rule_of_five.cpp (fragment: declarations only)" showLineNumbers
#include <cstddef>

class Buffer {
public:
    explicit Buffer(std::size_t n);
    ~Buffer();                                      // 1: release the resource
    Buffer(const Buffer& other);                    // 2: deep copy
    Buffer& operator=(const Buffer& other);         // 3: deep copy, strong guarantee
    Buffer(Buffer&& other) noexcept;                // 4: steal, leave other empty
    Buffer& operator=(Buffer&& other) noexcept;     // 5: release own, then steal
    std::size_t size() const;

private:
    std::size_t size_;
    char* data_;
};
```

The definitions of all five, with the reasoning for each, are on the
[copy and move semantics](./copy-and-move-semantics.md) page, which owns what the operations do.
This page owns which ones to declare. One declaration-level detail matters here: both moves are
`noexcept` so containers use them ([why](./copy-and-move-semantics.md#why-move-operations-should-be-noexcept)).

A single by-value `operator=(Buffer other)` with a `noexcept` swap can replace both assignment
operators; that is the [copy-and-swap idiom](../13-idioms-and-design/05-copy-and-swap.md).

### Polymorphic base classes

A base class meant for deletion through a base pointer needs a virtual destructor
([why](./virtual-functions.md#virtual-destructors)). That destructor is user-declared, so by the
table above the class loses its implicit moves. The usual fix is to default all five:

```cpp title="polymorphic_base.cpp" showLineNumbers
#include <string>
#include <type_traits>

struct Base {                        // declaring the destructor suppresses the implicit moves
    virtual ~Base() = default;
    std::string name;
};
static_assert(!std::is_nothrow_move_constructible_v<Base>);   // "move" is really the copy

struct Base5 {                       // default all five to get the moves back
    virtual ~Base5() = default;
    Base5() = default;
    Base5(const Base5&) = default;
    Base5& operator=(const Base5&) = default;
    Base5(Base5&&) = default;
    Base5& operator=(Base5&&) = default;
    std::string name;
};
static_assert(std::is_nothrow_move_constructible_v<Base5>);

int main() {}
```

Many polymorphic hierarchies make the copy operations `protected` or deleted instead, to prevent
[object slicing](./object-slicing.md).

## Deleting operations

When copying or moving makes no sense (a mutex, a type that registers its own address somewhere),
say so with `= delete`. Deleting the copy operations is enough: a user-declared copy constructor
already suppresses the implicit moves, so rvalues find the deleted copy and fail to compile.

```cpp title="Fragment: non-copyable, non-movable"
class Registry {
public:
    Registry() = default;
    Registry(const Registry&) = delete;
    Registry& operator=(const Registry&) = delete;
    // moves are not declared, so they are not available either
};
```

Spelling out all four as deleted is also common and documents intent. A deleted function gives a
clearer error than the pre-C++11 trick of a private, undefined copy constructor. The trade-offs
between these forms are on the [non-copyable](../13-idioms-and-design/04-non-copyable.md) page.

## Choosing

| The class... | Declare | Example |
|---|---|---|
| holds only self-managing members | nothing (rule of zero) | `std::string`, `std::vector`, `std::unique_ptr` members |
| owns a raw resource directly | all five (rule of five) | a hand-written buffer or handle wrapper |
| is a polymorphic base | virtual destructor plus the other four as `= default`, `protected`, or `= delete` | interface classes |
| must never be copied or moved | deleted copy operations | registries, objects whose address is shared |

Prefer moving the raw resource into a small dedicated wrapper (rule of five, once) so that every
class using it gets the rule of zero.

## References

- cppreference: [The rule of three/five/zero](https://en.cppreference.com/w/cpp/language/rule_of_three),
  [Destructors](https://en.cppreference.com/w/cpp/language/destructor),
  [Move constructors](https://en.cppreference.com/w/cpp/language/move_constructor)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), rules C.20
  (rule of zero) and C.21 (define or delete all default operations)
