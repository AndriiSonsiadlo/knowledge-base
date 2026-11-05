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
`operator delete` ([new and delete](./new-and-delete.md#expression-versus-function)).

## Subobjects: bases and members

A class's bases and members have their own lifetimes nested inside the enclosing object's: bases
first, then members in **declaration order** (not in the order of the member initializer list),
then the constructor body. Destruction runs exactly in reverse. The rules and examples are in
[constructors and destructors](../07-classes-and-oop/constructors-and-destructors.md#construction-order).

## Temporaries

A temporary is an object that exists only because an expression needed one: a prvalue that gets
materialized (`std::string("x")` passed to a `const std::string&`, or a call result you take a member
of). It is destroyed at the end of the **full-expression** that created it, roughly at the next `;`.
Using it within that expression is fine:

```cpp
std::size_t n = std::string("hello").size();   // the temporary lives until the ';'
```

### Lifetime extension

Binding a temporary to a reference **extends** its lifetime to that of the reference: a `const T&` or
a `T&&` variable, in the same way for a reference to a subobject or member of the temporary (`const
int& v = Noisy(2).id;` keeps all of `Noisy(2)` alive). The rule is about the *direct binding of a
prvalue*. It is lost as soon as the reference passes through something else. The program below traces
each case with a type that prints when it is built and destroyed.

```cpp title="extension.cpp" showLineNumbers
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("  Noisy(%d)\n", id); }
    ~Noisy() { std::printf("  ~Noisy(%d)\n", id); }
    const Noisy& self() const { return *this; }
};

struct Holder { const Noisy& ref; };                                    // aggregate

const Noisy& pass(const Noisy& n) { return n; }

int main() {
    std::puts("direct bind:");
    { const Noisy& a = Noisy(1); std::puts("  in scope"); (void)a; }
    std::puts("member of temporary:");
    { const int& v = Noisy(2).id; std::printf("  v=%d\n", v); }
    std::puts("aggregate member:");
    { Holder h{Noisy(3)}; std::printf("  h.ref=%d\n", h.ref.id); }
    std::puts("through a function:");
    { const Noisy& c = pass(Noisy(4)); std::puts("  after ;  (c dangles)"); (void)c; }
    std::puts("through a member function:");
    { const Noisy& d = Noisy(5).self(); std::puts("  after ;  (d dangles)"); (void)d; }
}
```

Output with g++ 15 (`-std=c++20`):

```text
direct bind:
  Noisy(1)
  in scope
  ~Noisy(1)
member of temporary:
  Noisy(2)
  v=2
  ~Noisy(2)
aggregate member:
  Noisy(3)
  h.ref=3
  ~Noisy(3)
through a function:
  Noisy(4)
  ~Noisy(4)
  after ;  (c dangles)
through a member function:
  Noisy(5)
  ~Noisy(5)
  after ;  (d dangles)
```

In the extended cases the destructor runs at the end of the block, together with the reference. In the
others it runs before the next statement. GCC warned, with `-Wdangling-reference` (part of `-Wall` in GCC 13 and later), about `c` and `d`. The cases where extension does **not** apply:

| Binding | Lifetime of the temporary |
|---|---|
| `const T& r = T();`, `T&& r = T();` | Extended to the end of `r`'s scope |
| `const int& v = T().member;`, `static_cast<const T&>(T())` | Extended (the whole temporary) |
| `Holder h{T()};` (aggregate initialization of a reference member) | Extended to the end of `h`. With parentheses, `Holder h(T{});` *(C++20)*, it is **not** |
| `pass(T())` where `pass` returns a reference | Dies at the end of the full-expression. A function call is not a direct binding |
| Reference **member** initialized from a temporary in a constructor's member initializer list | Ill-formed since C++14 (CWG 1696, [class.base.init]). Clang rejects it, GCC only warns. Never extended |
| `return T();` from a function returning `const T&` | Dies at the return, so the caller gets a dangling reference. Ill-formed since C++26 (P2748R5) |
| Reference parameter `f(T())` | Lives until the end of the full-expression containing the call, not beyond the call |
| Initializer of a `new` expression with a reference member (`new Holder{T()}`) | Dies at the end of the full-expression |

Extended or not, a reference to a `const` lvalue that you obtained from a function is only as good as
the object it refers to. Typical real-world traps: `std::max(a, b)` on temporaries, `std::string_view
sv = std::string("x");` (a view owns nothing, so nothing is extended), and member functions that
return a reference into `*this` called on a temporary.

In a range-based `for`, the range expression is bound to `auto&&`, which extends only the outermost
temporary. C++23 *(P2718)* extends **all** temporaries created in the range expression to the end of
the loop. This is the difference:

```cpp title="range-for.cpp" showLineNumbers
#include <cstdio>
#include <string>

struct W {
    std::string s = "abc";
    std::string& get() { return s; }     // reference into the temporary W
    ~W() { std::puts("~W"); }
};
W make() { return {}; }

int main() {
    for (char c : make().get()) std::putchar(c);   // C++20: dangling. C++23: fine
    std::putchar('\n');
}
```

Compiled with g++ 15, `-std=c++20` prints `~W` **before** `abc` (the `W` was already destroyed when
the loop started, so reading `s` is undefined behavior and only happens to work), while `-std=c++23`
prints `abc` and then `~W`. Compilers that predate P2718 behave as C++20 even with `-std=c++23`; check the cppreference compiler support table.

## Dangling references and pointers

A reference or pointer **dangles** when the object it designates is no longer alive. The storage may
still hold the old bytes, which is why such code often appears to work. Causes you meet most:

- **Scope ended**: returning a reference or pointer to a local ([automatic storage](./storage-duration.md#automatic-storage)).
- **Destroyed or freed**: `delete p;` then `p->f()`, or `std::destroy_at(p)` then use.
- **Temporary expired**: the table above.
- **Invalidated by a container**: `push_back` reallocation destroys the old elements.
- **Captured by reference** in a lambda that outlives the captured locals.

## Moved-from objects are alive

`std::move` does not end a lifetime. A moved-from object is still within its lifetime and is
destroyed normally at the end of its scope. The standard library leaves its types in a "valid but
unspecified" state: you may assign to them, destroy them, or call member functions with no
preconditions (`clear()`, `empty()`), but you should not rely on their value. See
[move semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## Reusing storage: `std::launder`

Ending an object's lifetime and constructing another in the same storage is legal. The
[placement new page](./placement-new.md) covers the mechanics, the "transparently replaceable" rule
that decides whether old pointers and names still refer to the new object, and
[`std::launder`](./placement-new.md#stdlaunder-c17) *(C++17)*. The lifetime-side summary: after storage reuse,
a pointer or reference obtained *before* the reuse refers to the new object only if the replaceable
rule holds. Otherwise use the pointer returned by the placement new, or `std::launder` of the
address. `std::launder` does not start a lifetime. It only returns a pointer to an object that
already lives at that address, and it is undefined behavior if there is none.

## Implicit object creation *(C++20)*

C code routinely does `struct P* p = malloc(sizeof *p); p->x = 1;`. Before this was addressed it was
technically undefined behavior in C++: `malloc` returns storage, not an object, and nothing started a
`P`'s lifetime. P0593 fixed this. It was adopted as a defect report, so compilers apply it in all
language modes. Certain operations **implicitly create objects** of **implicit-lifetime types** in
their storage, as many as needed (and with whatever lifetimes) to give the program defined behavior.

An **implicit-lifetime type** is a scalar type, an array type, an aggregate class whose destructor is
not user-provided, or a class with at least one trivial eligible constructor and a trivial,
non-deleted destructor. `std::string`, containers and anything with a user-provided constructor and
destructor are not.

The operations that implicitly create objects are:

- the allocation functions `std::malloc`, `calloc`, `realloc`, `std::aligned_alloc`, and
  `operator new` / `operator new[]` (the functions, not the `new T` expression, which creates a `T`
  explicitly);
- `std::allocator<T>::allocate` (which creates an array of `T`, without constructing elements);
- `std::memcpy` and `std::memmove`, which implicitly create objects in the destination;
- starting the lifetime of an array of `unsigned char` or `std::byte`,
  which implicitly creates objects in that array. This is also what makes it work when a placement-new
  buffer is a plain byte array.

```cpp title="malloc.cpp" showLineNumbers
#include <cstdlib>
#include <cstring>

struct Point { int x, y; };   // aggregate: implicit-lifetime type

int main() {
    auto* p = static_cast<Point*>(std::malloc(sizeof(Point)));  // a Point is implicitly created
    if (!p) return 1;
    p->x = 1;                 // defined
    p->y = 2;
    int sum = p->x + p->y;
    std::free(p);

    alignas(Point) unsigned char buf[sizeof(Point)] = {};
    Point q;
    std::memcpy(&q, buf, sizeof q);   // the bytes become a Point's value
    return sum - 3 + q.x;             // returns 0
}
```

Two limits are worth remembering:

- A type with a non-trivial constructor (`std::string`, anything owning a resource) is never
  created implicitly. Use `new`, placement new or `std::construct_at`.
- The creation is "as needed to make behavior defined". That means `static_cast<Point*>(malloc(...))`
  points at the created `Point`. It does not mean every pointer cast on arbitrary memory is
  now valid. A cast between unrelated types on an *existing* object is still an aliasing violation
  ([strict aliasing](./strict-aliasing.md)).

## `std::start_lifetime_as` *(C++23)*

Implicit creation only happens at the operations above. A buffer filled by `read()` or `recv()` is
different: the bytes have a defined representation, but no operation created a `Pkt` there.
`std::start_lifetime_as<T>(p)` (header `<memory>`, P2590R2) starts the lifetime of a `T` (or an array of
`T`) at `p` **and keeps the existing bytes** as its value, for implicit-lifetime `T`. It returns a
pointer to that object. Compared with `placement new T{}`, it does not re-initialize the storage.

```cpp title="start_lifetime_as.cpp (fragment, needs C++23 library support)"
alignas(Pkt) unsigned char buf[sizeof(Pkt)];
read_into(buf);                                   // bytes now hold a valid Pkt representation
const Pkt* p = std::start_lifetime_as<Pkt>(buf);  // a Pkt now lives in buf; p->a is readable
```

**Support is limited.** Test the feature-test macro `__cpp_lib_start_lifetime_as` (shown below) rather than assuming the library has it. When this page was written, g++ 15.2 with libstdc++ and Clang 21.1 did not define it, so the snippet above was **not compiled**. Check the
[cppreference compiler support table](https://en.cppreference.com/w/cpp/compiler_support/23) for the current status of
your toolchain, and test the macro before use:

```cpp
#include <memory>
#ifdef __cpp_lib_start_lifetime_as
// std::start_lifetime_as is available
#endif
```

Until it is, the portable way to read a value out of raw bytes is `std::memcpy` into an object of
the right type, which compilers optimize to a plain load ([safe type punning](./strict-aliasing.md#safe-type-punning)).
Casting the buffer with `reinterpret_cast<Pkt*>(buf)` and reading through it remains undefined behavior
in C++ even though it works in practice on many compilers. See [strict aliasing](./strict-aliasing.md).

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `int& r = v[0]; v.push_back(1); r = 2;` | Reallocation destroys the old elements and frees their storage. `r` dangles. | Re-fetch after operations that invalidate (see container docs), or store an index. |
| `std::string_view sv = get_name();` where `get_name` returns `std::string` | The string temporary dies at `;`. `sv` points into freed memory. | Keep the `std::string`: `auto name = get_name();` |
| Returning `const T&` from a function argument that may be a temporary | Lifetime extension does not pass through functions. | Return by value. |
| Reference member initialized from a temporary in a constructor | Ill-formed since C++14 (CWG 1696); Clang rejects it, GCC warns. The temporary would die when the constructor exits. | Store by value, or take the object by reference parameter. |
| Lambda captures `[&]` and is stored or run later | The captured locals may be gone when it runs. | Capture by value, or make sure the lambda does not outlive the scope. |
| `delete p; p->f();` or use after `std::destroy_at` | Lifetime has ended. Often "works" until the memory is reused. | Use owning types. Build tests with AddressSanitizer. |
| `for (x : make().get())` before C++23 | Only the outermost temporary is extended. | Name the temporary first, or use C++23. |
| Calling a virtual function in a constructor expecting the derived override | During construction the dynamic type is the class being constructed. | Call the virtual function after construction, from a factory. |

AddressSanitizer (`-fsanitize=address`) catches use after free, use after return
(with `ASAN_OPTIONS=detect_stack_use_after_return=1`) and use after scope at run time. See
[Sanitizers](../14-debugging-and-profiling/04-sanitizers.md).

## Key points

- Storage outlives the object at both ends: lifetime is from the end of construction to the start
  of destruction.
- A temporary dies at the end of its full-expression unless a reference is bound directly to it.
  Extension never passes through a function call. Binding a reference member to a temporary in a mem-initializer is ill-formed since C++14 (CWG 1696); Clang rejects, GCC warns.
- A moved-from object is alive. It will be destroyed normally.
- Since C++20 (as a defect report), `malloc`, `operator new` and `memcpy` implicitly create
  implicit-lifetime objects (scalars, arrays, trivial aggregates). Everything else needs a
  constructor call.
- `std::launder` (C++17) finds the object after storage reuse. `std::start_lifetime_as` (C++23) is
  for bytes that already hold a valid object, but check library support first (`__cpp_lib_start_lifetime_as`).
