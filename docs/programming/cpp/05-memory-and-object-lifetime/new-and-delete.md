---
id: new-and-delete
title: new and delete
sidebar_label: new & delete
sidebar_position: 5
tags: [c++, new, delete, dynamic-memory, heap, operator-new]
---

# new and delete

A `new`-expression creates an object with dynamic storage duration: it allocates memory **and**
constructs the object in it. A `delete`-expression does the reverse: it destroys the object **and**
frees the memory. The *expression* is built into the language and cannot be changed. The memory half is a call to an
`operator new` / `operator delete` *function*, which you can call directly, replace, or overload. That split is what
[placement new](./placement-new.md), custom allocators, and memory-leak checkers build on. In
application code you rarely write `new` directly: `std::make_unique`, `std::make_shared`, and the
containers do it for you. You still need to know what they do.

**Prerequisites:** [Storage duration](./storage-duration.md),
[object lifetime](./object-lifetime.md).

## The forms

```cpp title="forms.cpp" showLineNumbers
#include <string>

int main() {
    int* a = new int;              // default-initialized: indeterminate value
    int* b = new int();            // value-initialized: 0
    int* c = new int{42};          // 42
    auto* s = new std::string(3, 'x');   // "xxx"

    int* arr  = new int[4];        // 4 indeterminate ints
    int* zero = new int[4]();      // 4 zeros
    int* some = new int[4]{1, 2};  // {1, 2, 0, 0}

    delete a; delete b; delete c; delete s;
    delete[] arr; delete[] zero; delete[] some;   // array form for array new
}
```

The initializer after the type follows the normal [initialization rules](./initialization/default-initialization.md):
no initializer means default initialization, which leaves scalars indeterminate.

`new T` must be paired with `delete`, and `new T[n]` with `delete[]`. Mixing them is undefined
behavior. For arrays, prefer `std::vector<T>` or `std::make_unique<T[]>(n)`.

## Expression versus function

A `new`-expression is not a call to `operator new`. The compiler expands it into two steps: a call to an
**allocation function** named `operator new`, then construction in the returned storage.

```cpp title="expansion.cpp" showLineNumbers
#include <cstdio>
#include <cstdlib>
#include <new>

void* operator new(std::size_t n) {          // replace the global allocation function
    std::printf("operator new(%zu)\n", n);
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::printf("operator delete\n"); std::free(p); }
void operator delete(void* p, std::size_t n) noexcept {   // sized form (C++14)
    std::printf("operator delete(%zu)\n", n);
    std::free(p);
}

struct Widget {
    int a, b;
    Widget() : a(1), b(2) { std::printf("Widget()\n"); }
    ~Widget() { std::printf("~Widget()\n"); }
};

int main() {
    Widget* w = new Widget;   // allocate, then construct
    delete w;                 // destroy, then deallocate
}
```

<Walkthrough title="new Widget and delete w" caption="g++ 15 and clang++ 21 on x86-64, -std=c++23. Both call the sized operator delete." accent="amber">
  <Step title="Allocate">

```text
operator new(8)
```

The compiler calls `operator new(sizeof(Widget))`. It returns <StepChange>raw storage</StepChange>:
8 bytes, aligned to at least `__STDCPP_DEFAULT_NEW_ALIGNMENT__` (16 on x86-64 Linux). No `Widget`
exists yet. If allocation fails, `operator new` throws `std::bad_alloc` and nothing else happens.

  </Step>
  <Step title="Construct">

```text
Widget()
```

The constructor runs in that storage. When it returns, the <StepChange>lifetime begins</StepChange>
and `w` holds the address. If the constructor had thrown, the compiler would call the matching
`operator delete` automatically and let the exception continue. The memory does not leak.

  </Step>
  <Step title="Destroy">

```text
~Widget()
```

`delete w` first calls the destructor. The <StepChange>lifetime ends</StepChange>. The storage
still belongs to the program.

  </Step>
  <Step title="Deallocate">

```text
operator delete(8)
```

Then the compiler calls the deallocation function. With sized deallocation *(C++14)* it passes the
size it already knows, so the allocator can skip looking it up. <StepChange>The storage is
released</StepChange>, and `w` is now dangling.

  </Step>
</Walkthrough>

The `new T[n]` forms work the same way through `operator new[]`, then construct `n` elements in order.
`delete[]` destroys them in reverse order before calling `operator delete[]`. To know how many
destructors to run, implementations typically store the element count in front of the array when the
element type has a non-trivial destructor. The Itanium C++ ABI (GCC, Clang on Linux) calls this an
"array cookie"; the layout is not specified by the C++ standard. GCC and Clang on x86-64 Linux store a
`std::size_t` just before the returned pointer, and the pointer you get back from `new[]` is therefore
not the address `operator new[]` returned. That is why `delete` on a `new[]` pointer breaks: it passes
the wrong address to the deallocator and runs one destructor. Mixing the forms is undefined behavior
even for types with trivial destructors, where it may appear to work.

The three layers, in the order the compiler uses them:

<Diagram>
  <DiagramRow>
    <DiagramNode icon="code" title="new-expression">Language construct: allocate, then construct. Fixed.</DiagramNode>
    <DiagramArrow label="calls" />
    <DiagramNode icon="boxes" title="operator new">Allocation function: returns raw storage or fails. Replaceable.</DiagramNode>
    <DiagramArrow label="defaults to" />
    <DiagramNode icon="server" title="malloc-like allocator">Library or OS memory.</DiagramNode>
  </DiagramRow>
</Diagram>

You can call the allocation function yourself, which is how containers and
[placement new](./placement-new.md) users get raw storage without constructing anything:

```cpp title="raw-calls.cpp" showLineNumbers
#include <new>

int main() {
    void* raw = ::operator new(sizeof(int));   // storage only; no object exists
    int* p = ::new (raw) int{7};               // construct (placement new)
    (void)p;                                   // an int needs no destructor call
    ::operator delete(raw);                    // deallocate only
}
```

## When allocation fails

The default `operator new` does not return null. It loops:

1. Try to allocate. On success, return.
2. On failure, call the current **new-handler** (installed with `std::set_new_handler`).
3. If there is no handler, throw `std::bad_alloc`. If there is one, it must free memory and return
   (so the loop retries), install a different handler, or throw or terminate.

```cpp title="new-handler.cpp" showLineNumbers
#include <cstdio>
#include <new>

static int attempts = 0;
void on_fail() {
    std::printf("new_handler call %d\n", ++attempts);
    if (attempts == 3) std::set_new_handler(nullptr);   // next failure throws bad_alloc
}

int main() {
    std::set_new_handler(on_fail);
    try {
        char* p = new char[1ull << 60];   // far more than any machine has
        delete[] p;
    } catch (const std::bad_alloc&) {
        std::puts("bad_alloc after handler removed");
    }
}
```

Output (g++ 15 and clang++ 21, x86-64 Linux, `-std=c++20`):

```text
new_handler call 1
new_handler call 2
new_handler call 3
bad_alloc after handler removed
```

The **nothrow** form reports failure with a null pointer instead of an exception:

```cpp title="nothrow.cpp" showLineNumbers
#include <cstdio>
#include <new>

int main() {
    char* p = new (std::nothrow) char[1ull << 60];
    std::puts(p ? "allocated" : "nullptr");   // nullptr
    delete[] p;                               // deleting nullptr is a no-op
}
```

`std::nothrow` only makes the *allocation function* non-throwing. The new-handler still runs first
(and may throw), and the constructor can still throw. You release the result with an ordinary
`delete`.

On Linux, overcommit means that ordinary-sized requests usually succeed even when memory is short,
and the OOM killer ends the process later when it touches the pages. Do not rely on `bad_alloc` as
an out-of-memory detector there.

## Constructor throws: the matching deallocation

If the constructor throws, the compiler calls the deallocation function that **matches** the
allocation function it used, then lets the exception propagate. For a plain `new T` that is the
ordinary `operator delete`. For a placement-style `new (args) T` it is the `operator delete` with the
same extra parameters, if one exists; if none exists, the memory is not released. This is why a
custom `operator new(std::size_t, Arg)` should come with a matching `operator delete(void*, Arg)`.

## Replacing and overloading

**Replaceable (global).** The library provides these in the global namespace, and a program may
define its own version of each in exactly one translation unit (no `static`, no `inline`):

| Function | Default behavior |
|---|---|
| `operator new(size_t)`, `operator new[](size_t)` | Allocate; loop with the new-handler; throw `bad_alloc`. `new[]` calls `new` by default. |
| `operator new(size_t, nothrow_t)` and `[]` | Call the throwing form and catch `bad_alloc`, returning null. |
| `operator new(size_t, align_val_t)` and `[]`, plus nothrow forms *(C++17)* | Aligned counterparts. |
| `operator delete(void*)`, `operator delete[](void*)` | Free. `delete[]` calls `delete` by default. |
| `operator delete(void*, size_t)` and `[]` *(C++14)* | Sized forms. Call the unsized form by default. |
| `operator delete(void*, align_val_t)` and `[]`, and sized versions *(C++17)* | Aligned counterparts. |

Because of the defaults, replacing just `operator new(size_t)` and `operator delete(void*)` is usually
enough to route every ordinary allocation (including `std::vector`, `std::string`, and
`make_unique`) through your code. This is how leak counters and tracking allocators work.

**Class-specific.** Declare `static void* operator new(std::size_t)` and
`static void operator delete(void*, std::size_t)` inside a class. Lookup for `new T` finds the
class's functions first, and if it finds any named `operator new` there, they **hide** the global
ones (including the global placement and nothrow forms). Derived classes inherit them. With a virtual destructor, a
`delete` through a base pointer passes the size of the dynamic type to a sized class-specific
`operator delete`, so the allocator knows how much it is freeing.

```cpp title="class-specific.cpp" showLineNumbers
#include <cstddef>
#include <cstdio>
#include <new>

struct Pooled {
    int x = 0;
    static void* operator new(std::size_t n) {
        std::printf("Pooled::operator new(%zu)\n", n);
        return ::operator new(n);                        // fall back to the global one
    }
    static void operator delete(void* p, std::size_t n) noexcept {
        std::printf("Pooled::operator delete(%zu)\n", n);
        ::operator delete(p);
    }
};

int main() {
    Pooled* p = new Pooled;
    delete p;
}
```

```text
Pooled::operator new(4)
Pooled::operator delete(4)
```

Rules for any replacement: `operator new` must return suitably aligned storage and either succeed,
throw `bad_alloc`, or (for the nothrow form) return null. `operator delete` must be `noexcept`
and accept null.

## Sized and aligned deallocation

- **Sized deallocation** *(C++14)* gives `operator delete` the size of the object being freed, which
  the compiler already knows from the type. Allocators can skip a size lookup. Support is by compiler:
  GCC enables it by default in C++14 and later, while older Clang releases required
  `-fsized-deallocation`. Check your toolchain version if you depend on the sized overload being
  called.
- **Aligned allocation** *(C++17)*: when `alignof(T)` exceeds `__STDCPP_DEFAULT_NEW_ALIGNMENT__`, the
  `new`-expression selects the `std::align_val_t` overloads, and the `delete`-expression selects the
  matching aligned deallocation. Before C++17, such types were silently under-aligned. The worked
  example is in [alignment](./alignment.md#over-aligned-types-and-new). If you replace allocation
  functions, replace the aligned ones as well, or aligned types bypass your allocator.

## Allocation elision

Since C++14, an implementation may omit a call to a replaceable allocation function made by a
new-expression, or merge several into one larger allocation, and may do the same for the matching
deallocations. So a `new` that is created and deleted within a function can disappear entirely, and
counting calls to `operator new` is not a reliable way to measure how many objects you made. The
allocation is not "observable behavior" unless the pointer escapes.

## Deleting through a base pointer

`delete p` where `p` is a `Base*` pointing to a `Derived` is undefined behavior unless `Base` has a
**virtual destructor**. Without it only `~Base` runs and the wrong size may be passed to
`operator delete`. Give every polymorphic base `virtual ~Base() = default;`. See
[virtual functions](../07-classes-and-oop/virtual-functions.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Missing `delete` (often on an early `return` or an exception) | Memory leak | `std::unique_ptr` / `std::make_unique` |
| `delete p;` twice | Undefined behavior. Typically heap corruption, detected by glibc as `free(): double free detected` | One owner. Smart pointers. |
| Using `*p` after `delete p` | Use after free | Smart pointers. AddressSanitizer finds it. |
| `delete` for `new[]`, or `delete[]` for `new` | Undefined behavior | Use `std::vector` / `std::make_unique<T[]>` |
| `free` on `new` memory, or `delete` on `malloc` memory | Undefined behavior: different allocation functions | Keep each pair together |
| `new int` and reading the value | Indeterminate value | `new int()` or `new int{}` |

Setting a pointer to `nullptr` after `delete` makes a second `delete` of *that variable* harmless,
but does nothing for other copies of the pointer. It is a patch, not ownership.

## The modern replacement

```cpp title="owners.cpp" showLineNumbers
#include <memory>
#include <vector>

struct Widget { int value = 0; };

int main() {
    auto one = std::make_unique<Widget>();            // owned; deleted at scope exit
    auto shared = std::make_shared<Widget>();         // reference-counted
    auto arr = std::make_unique<int[]>(100);          // value-initialized: 100 zeros
    std::vector<Widget> many(10);                     // usually the best "dynamic array"
    return one->value + shared->value + arr[0] + many[9].value;   // returns 0
}
```

Ownership semantics are covered in
[unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md) and
[shared_ptr](../06-pointers-references-and-smart-pointers/shared-ptr.md).

## Key points

- `new` = `operator new` (allocate) + constructor. `delete` = destructor + `operator delete`
  (deallocate).
- If a constructor throws inside `new`, the memory is freed for you.
- Match `new`/`delete`, `new[]`/`delete[]`, `malloc`/`free`, never across.
- Write `new` only inside owning types. Everywhere else use `make_unique`, `make_shared` and
  containers.
