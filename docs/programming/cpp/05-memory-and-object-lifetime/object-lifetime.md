---
id: object-lifetime
title: Object Lifetime
sidebar_label: Object Lifetime
sidebar_position: 4
tags: [c++, lifetime, construction, destruction, temporaries, implicit-object-creation, advanced]
---

# Object Lifetime

An object's **lifetime** is the part of its storage duration during which the object exists and may
be used as an object of its type. Storage comes first and goes last. The lifetime starts once
initialization is complete and ends when destruction starts. Reading or writing an object outside its
lifetime is undefined behavior. That covers every dangling pointer, use-after-free and dangling
reference bug, and it is also why storage reuse needs [placement new](./placement-new.md) and, in some
cases, `std::launder`.

**Prerequisites:** [Storage duration](./storage-duration.md),
[constructors and destructors](../07-classes-and-oop/constructors-and-destructors.md).

## Storage versus lifetime

<Diagram title="Five phases of every object" caption="Lifetime is the accented middle: a strict subset of the time the storage exists." accent="violet">
  <DiagramRow>
    <DiagramNode title="1. Storage acquired">Stack frame, allocator, static segment, or a buffer</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="2. Initialized">Constructor runs. Not yet alive.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="3. Lifetime" accent>Object may be read, written, passed around</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="4. Destroyed">Destructor runs. Lifetime already over.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="5. Storage released">Memory reused or returned</DiagramNode>
  </DiagramRow>
</Diagram>

The precise rules, from [basic.life]:

- **Lifetime begins** when storage with the right size and alignment is obtained **and** the object's
  initialization (if any) is complete. For a class, that means the constructor has returned. If the
  constructor throws, the lifetime never begins and the destructor is not called. Already
  constructed members and bases are destroyed.
- **Lifetime ends** when the destructor call **starts** (class types), when the object is destroyed
  (non-class types), or when its storage is released or **reused** by another object.

During construction and destruction the object is not yet (or no longer) alive, but the standard
gives special rules for this window. Member functions can be called from the constructor and
destructor, and virtual calls dispatch to the class currently being constructed, not to a derived
class. See [virtual functions](../07-classes-and-oop/virtual-functions.md).

## Tracing one object

The program below makes each phase visible. The storage is a buffer on the stack, so acquiring and
releasing it are separate from constructing and destroying the object.

```cpp title="phases.cpp" showLineNumbers
#include <cstdio>
#include <memory>
#include <new>

struct Widget {
    int value;
    explicit Widget(int v) : value(v) { std::printf("construct %d\n", value); }
    ~Widget() { std::printf("destroy %d\n", value); }
};

int main() {
    alignas(Widget) unsigned char storage[sizeof(Widget)];  // 1. storage
    Widget* w = std::construct_at(reinterpret_cast<Widget*>(storage), 7);  // 2.
    w->value += 1;                                            // 3. use
    std::printf("use %d\n", w->value);
    std::destroy_at(w);                                       // 4. destroy
    // w now dangles: storage still exists, the Widget does not
}                                                             // 5. storage released
```

<Walkthrough title="A Widget from storage to release" caption="Output: construct 7, use 8, destroy 8." accent="violet">
  <Step title="Storage acquired">

```cpp
alignas(Widget) unsigned char storage[sizeof(Widget)];
```

`main`'s stack frame now has `sizeof(Widget)` bytes, aligned for `Widget`. There is
<StepChange>no Widget yet</StepChange>: reading `w->value` here would be undefined behavior.

  </Step>
  <Step title="Initialization">

```cpp
Widget* w = std::construct_at(reinterpret_cast<Widget*>(storage), 7);
```

`std::construct_at` *(C++20)* runs `Widget(7)` in that storage and prints `construct 7`. When the
constructor returns, <StepChange>the lifetime begins</StepChange>. The returned pointer points to the
new object.

  </Step>
  <Step title="In lifetime">

```cpp
w->value += 1;
```

Reads and writes through `w` are valid. `value` is <StepChange>8</StepChange>. The program prints
`use 8`.

  </Step>
  <Step title="Destruction">

```cpp
std::destroy_at(w);
```

The destructor is called. As soon as it <StepChange>starts</StepChange>, the lifetime has ended. It
prints `destroy 8`. The bytes are still there, but `w` is now a dangling pointer.

  </Step>
  <Step title="Storage released">

At the closing brace of `main` the stack frame goes away and <StepChange>the storage
ends</StepChange>. Nothing else runs: `storage` is an `unsigned char` array, so it has no destructor.
With a plain `Widget w(7);` the compiler does steps 1 to 5 for you.

  </Step>
</Walkthrough>

For an ordinary automatic variable, steps 1 and 5 are the stack frame and steps 2 and 4 are the
constructor and destructor. For `new`/`delete`, steps 1 and 5 are `operator new` and
`operator delete` ([new and delete](./new-and-delete.md#what-a-new-expression-does)).

## Subobjects: bases and members

A class's bases and members have their own lifetimes nested inside the enclosing object's: bases
first, then members in **declaration order** (not in the order of the member initializer list),
then the constructor body. Destruction runs exactly in reverse. The rules and examples are in
[constructors and destructors](../07-classes-and-oop/constructors-and-destructors.md#construction-order).

## Temporaries

A temporary (the result of a prvalue that has to exist in memory, like `std::string("x")` passed to a
`const std::string&`) is destroyed at the end of the **full-expression** that created it, roughly at
the next `;`. Using it within that expression is fine:

```cpp
std::size_t n = std::string("hello").size();   // the temporary lives until the ';'
```

### Lifetime extension

Binding a temporary directly to a `const T&` or a `T&&` **extends** its lifetime to that of the
reference. The rule applies only to the reference the temporary is bound to directly, and it does
not carry through functions.

```cpp title="extension.cpp" showLineNumbers
#include <string>
#include <utility>

std::string make() { return "temp"; }
const std::string& pass(const std::string& s) { return s; }

int main() {
    const std::string& a = make();      // extended: lives as long as `a`
    std::string&& b = make();           // extended as well
    const std::string& c = pass(make()); // NOT extended: the temporary dies at ';'
    // c.size() here would read a destroyed string: undefined behavior
    (void)c;
    return static_cast<int>(a.size() + b.size()) - 8;   // returns 0
}
```

The `c` line is a dangling reference. The compiler sees `pass` returning some reference, not the
temporary, so nothing is extended. GCC 15 warns with `-Wdangling-reference` (enabled by `-Wall`).
The same trap appears with `std::max(a, b)` on temporaries, `std::string_view sv = std::string(...)`
(a view does not extend anything), and member functions returning references into `*this` called on
a temporary.

C++23 fixed one common case. In a range-based `for`, temporaries created in the range expression now
live until the end of the loop *(C++23, P2718)*, so `for (char c : make().substr(1))` is safe.
Before C++23 only the outermost temporary was extended.

## Moved-from objects are alive

`std::move` does not end a lifetime. A moved-from object is still within its lifetime and is
destroyed normally at the end of its scope. The standard library leaves its types in a "valid but
unspecified" state: you may assign to them, destroy them, or call member functions with no
preconditions (`clear()`, `empty()`), but you should not rely on their value. See
[move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## Implicit object creation *(C++20)*

C code routinely does `struct P* p = malloc(sizeof *p); p->x = 1;`. For years this was technically
undefined behavior in C++: `malloc` returns storage, not an object, and nothing started a `P`'s
lifetime. P0593 (adopted for C++20 and applied as a defect report to earlier standards) made it
defined. Certain operations **implicitly create objects** of **implicit-lifetime types**, as many as
needed to make the program's behavior defined.

| Implicit-lifetime types | Operations that implicitly create objects |
|---|---|
| Scalars (`int`, `double`, pointers, enums) | `std::malloc`, `calloc`, `realloc`, `std::aligned_alloc` |
| Arrays of any type | `operator new` / `operator new[]` (the allocation functions, not `new T`) |
| Aggregates whose destructor is not user-provided | `std::allocator<T>::allocate` |
| Classes with a trivial eligible constructor and a trivial, non-deleted destructor | `std::memcpy`, `std::memmove`, `std::bit_cast` |
| | Starting the lifetime of an `unsigned char` or `std::byte` array |

```cpp title="malloc.cpp" showLineNumbers
#include <cstdlib>

struct Point { int x, y; };   // aggregate: implicit-lifetime type

int main() {
    auto* p = static_cast<Point*>(std::malloc(sizeof(Point)));  // a Point is implicitly created
    if (!p) return 1;
    p->x = 1;                 // defined since C++20 (and as a DR before)
    p->y = 2;
    int sum = p->x + p->y;
    std::free(p);
    return sum - 3;           // returns 0
}
```

This does **not** help with a type that has a non-trivial constructor such as `std::string`. Its
objects must still be created explicitly with `new` or `std::construct_at`.

To reinterpret bytes that already hold a valid representation (a buffer filled by `read()` from a
file or socket), C++23 adds `std::start_lifetime_as<T>(p)`. It starts the lifetime of a `T` at `p`
with the existing bytes as its value. As of GCC 15 / libstdc++ the feature-test macro
`__cpp_lib_start_lifetime_as` is not defined, so the portable choice today is still `std::memcpy`
into a real `T` (see [strict aliasing](./strict-aliasing.md#safe-type-punning)).

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `int& r = v[0]; v.push_back(1); r = 2;` | Reallocation destroys the old elements and frees their storage. `r` dangles. | Re-fetch after operations that invalidate (see container docs), or store an index. |
| `std::string_view sv = get_name();` where `get_name` returns `std::string` | The string temporary dies at `;`. `sv` points into freed memory. | Keep the `std::string`: `auto name = get_name();` |
| Returning `const T&` from a function argument that may be a temporary | Lifetime extension does not pass through functions. | Return by value. |
| Lambda captures `[&]` and is stored or run later | The captured locals may be gone when it runs. | Capture by value, or make sure the lambda does not outlive the scope. |
| `delete p; p->f();` or use after `std::destroy_at` | Lifetime has ended. Often "works" until the memory is reused. | Use owning types. Build tests with AddressSanitizer. |
| Calling a virtual function in a constructor expecting the derived override | During construction the dynamic type is the class being constructed. | Call the virtual function after construction, from a factory. |

AddressSanitizer (`-fsanitize=address`) catches use after free, use after return
(with `ASAN_OPTIONS=detect_stack_use_after_return=1`) and use after scope at run time. See
[Sanitizers](../14-debugging-and-profiling/04-sanitizers.md).

## Key points

- Storage outlives the object at both ends: lifetime is from the end of construction to the start
  of destruction.
- A temporary dies at the end of its full-expression unless bound directly to a reference. Extension
  never passes through a function call.
- A moved-from object is alive. It will be destroyed normally.
- Since C++20, `malloc` and `memcpy` create implicit-lifetime objects (scalars, arrays, trivial
  aggregates) automatically. Everything else needs a constructor call.
