---
id: pimpl
title: Pimpl
sidebar_label: Pimpl
sidebar_position: 2
tags: [c++, pimpl, idioms, compilation, encapsulation, abi]
---

# Pimpl

**Pimpl** (pointer to implementation, also the "compiler firewall") moves a class's private data
and helper types out of its header into a hidden `Impl` struct defined in the `.cpp` file. The
public class keeps one pointer to it. Clients that include the header no longer see, or depend on,
anything in `Impl`.

**Prerequisites:** [Headers and Includes](../01-toolchain-and-build/headers-and-includes.md),
[`unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md) (especially
[incomplete types](../06-pointers-references-and-smart-pointers/unique-ptr.md#incomplete-types-and-the-pimpl-idiom)),
[Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md).

## The problem

A class definition lists every non-static data member, so its header must include whatever those
members' types need. Every file that includes the header then:

- recompiles when any private member or its header changes, even though callers cannot touch it;
- sees (and may accidentally depend on) third-party or platform headers that were only an
  implementation detail;
- has `sizeof(Widget)` and member offsets baked in. For a shared library, adding a private member
  changes the size, so clients must be recompiled to stay correct.

Pimpl cuts all three by making the class a fixed-size handle.

## The idiom

```cpp title="widget.h" showLineNumbers
#pragma once
#include <memory>
#include <string>

class Widget {
public:
    explicit Widget(std::string name);
    ~Widget();                                   // defined where Impl is complete
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    Widget(const Widget&);                       // deep copy, user-provided
    Widget& operator=(const Widget&);

    void rename(std::string name);
    const std::string& name() const;
    int renames() const;

private:
    struct Impl;                                 // declared, not defined
    std::unique_ptr<Impl> impl_;
};
```

```cpp title="widget.cpp" showLineNumbers
#include "widget.h"
#include <utility>

struct Widget::Impl {                            // complete only in this file
    std::string name;
    int renames = 0;
};

Widget::Widget(std::string name) : impl_(std::make_unique<Impl>(Impl{std::move(name), 0})) {}
Widget::~Widget() = default;
Widget::Widget(Widget&&) noexcept = default;
Widget& Widget::operator=(Widget&&) noexcept = default;
Widget::Widget(const Widget& o)
    : impl_(o.impl_ ? std::make_unique<Impl>(*o.impl_) : nullptr) {}
Widget& Widget::operator=(const Widget& o) {
    if (this == &o) return *this;
    if (!o.impl_)      impl_.reset();                       // source is moved-from
    else if (!impl_)   impl_ = std::make_unique<Impl>(*o.impl_);   // target is moved-from
    else               *impl_ = *o.impl_;
    return *this;
}

void Widget::rename(std::string name) { impl_->name = std::move(name); ++impl_->renames; }
const std::string& Widget::name() const { return impl_->name; }
int Widget::renames() const { return impl_->renames; }
```

```cpp title="main.cpp"
#include "widget.h"
#include <cstdio>
#include <utility>

int main() {
    Widget a("alpha");
    Widget b = a;                 // deep copy
    b.rename("beta");
    Widget c = std::move(b);
    std::printf("%s %d | %s %d\n", a.name().c_str(), a.renames(), c.name().c_str(), c.renames());
    b = a;                        // b is moved-from (null impl_): assignment re-creates it
    std::printf("%s\n", b.name().c_str());
}
```

Built with `g++` 15 and `clang++` 21, `-std=c++20 -Wall -Wextra`, at `-O0` and `-O2`, the output is
`alpha 0 | beta 1` then `alpha`. The last two lines of `main` assign to a moved-from `Widget`; the copy
assignment handles that case, where a plain `*impl_ = *o.impl_` would dereference null and abort.

<Diagram title="What a client sees" caption="The header exposes only a pointer; the definition of Impl and its dependencies stay in widget.cpp." accent="blue">
  <DiagramRow>
    <DiagramGroup label="widget.h (included by clients)">
      <DiagramNode icon="package" title="Widget">one pointer: <code>unique_ptr&lt;Impl&gt;</code></DiagramNode>
    </DiagramGroup>
    <DiagramGroup label="widget.cpp only">
      <DiagramNode icon="lock" title="Widget::Impl" accent>data members, helper types, third-party includes</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

### Why the special members are declared in the header and defined in the .cpp

`std::unique_ptr<Impl>`'s default deleter needs `Impl` complete wherever the destructor is
instantiated. If you leave `~Widget()` implicit, the compiler defines it inline in every file that
needs it, where `Impl` is only declared:

```text
error: invalid application of 'sizeof' to incomplete type 'Impl'
```

(g++ 15 and clang++ 21 both report this for a class with an implicit destructor and an incomplete
`Impl`.) The same applies to move assignment, which destroys the old object. So declare the
destructor and the move operations in the header and define them, even as `= default`, in the
`.cpp` after `Impl` is complete. The rule is explained with the deleter on the
[`unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md#incomplete-types-and-the-pimpl-idiom)
page.

### Copy semantics are your choice

`unique_ptr` makes `Widget` move-only by default, and declaring the moves suppresses the implicit
copies. If the class should be copyable, write a deep copy as above. A moved-from `Widget` has a
null `impl_`; any member function called on it dereferences null, so either document that only
destruction, assignment and copying are valid on a moved-from object (the operations above are written to
allow exactly that), or have the move constructor allocate a
fresh `Impl`. `shared_ptr<const Impl>` gives cheap copies with shared immutable state, which is a
different semantics, not a free copy.

### `const` does not propagate

In a `const` member function `impl_` is a `const unique_ptr<Impl>`, so `impl_->name` is still
mutable: constness stops at the pointer. The discipline is to treat `Impl` as part of the object and
keep `const` member functions honest by hand, or wrap the pointer in `std::experimental::propagate_const`
(Library Fundamentals TS v2, not in `std`; libstdc++ ships it, other libraries vary, and MSVC's STL does not, so check yours).

## Costs

- **An extra indirection on every member access** and, normally, **one heap allocation per object**
  (two if `Impl` holds containers; copies allocate again). Whether this matters depends on the call
  rate and cache behavior; measure in your own code. For a rarely-constructed class with coarse
  operations the cost is negligible; for a small value type used in a tight loop it is the wrong tool.
- **Member functions cannot be inlined across translation units** without LTO, since their
  bodies live in the `.cpp`.
- **Boilerplate:** forwarding functions, and the special-member declarations above.
- **Debugging** takes one more hop to see state.

## What pimpl buys

- **Build time.** Changing `Impl` rebuilds only `widget.cpp`; clients relink. Dependencies of `Impl`
  (platform headers, third-party libraries) leave the client's include graph. The size of the gain is
  project-specific; it is largest for widely included headers.
- **Binary compatibility (library authors).** `sizeof(Widget)` and its member offsets are fixed by
  the single pointer, so adding or reordering private state in `Impl` does not change the class
  layout that clients compiled against. This holds for the layout of `Widget` only: any change to
  the public interface, to virtual functions, or to inline code in the header is still an ABI
  change, and the effect on symbol mangling and layout is compiler- and ABI-specific. See
  [class layout](../07-classes-and-oop/class-layout.md) for what determines `sizeof`.
- **Encapsulation.** Private members are not just inaccessible but invisible.

## Alternatives

| Technique | Hides data? | Cost | Use when |
|---|---|---|---|
| Pimpl | yes | pointer + allocation per object | a concrete value-like class with a stable public interface |
| Abstract interface + factory (`std::unique_ptr<Base> make()`) | yes | virtual call + allocation | clients only use the object through a polymorphic interface anyway ([virtual functions](../07-classes-and-oop/virtual-functions.md)) |
| C++20 modules | only partially | none at run time | the goal is build time, not ABI: importers see only exported declarations, so private dependencies stop affecting their name lookup, though an exported class definition (and so its layout) is still part of the interface |
| Plain header with private members | no | none | internal code where rebuild cost is acceptable |

A "fast pimpl" stores `Impl` inline in an aligned buffer to avoid the allocation. It reintroduces
the size dependency (the buffer must be at least `sizeof(Impl)`), which defeats the ABI benefit, so
guard it with a `static_assert(sizeof(Impl) <= Size)` in the `.cpp` and use it only when the
allocation is measured to matter.

## Pitfalls

- **Forgetting to define the destructor in the .cpp:** the "incomplete type" error above.
- **Putting `Impl` in the header "just for now":** every client depends on it again.
- **Using Pimpl on everything:** it trades run-time cost and boilerplate for build time and
  stability; apply it at module boundaries, not to small helper classes.

## Related

- [`unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md): the owning pointer and its incomplete-type rule.
- [Non-Copyable](./04-non-copyable.md): the alternative when a pimpl class should be move-only.
- [Copy-and-Swap](./05-copy-and-swap.md): a strong-guarantee copy assignment for the deep-copy case.

## References

- [cppreference: `std::unique_ptr` (incomplete types)](https://en.cppreference.com/w/cpp/memory/unique_ptr)
- [cppreference: `std::experimental::propagate_const`](https://en.cppreference.com/w/cpp/experimental/propagate_const)
- [C++ Core Guidelines: I.27](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#i27-for-stable-library-abi-consider-the-pimpl-idiom)
