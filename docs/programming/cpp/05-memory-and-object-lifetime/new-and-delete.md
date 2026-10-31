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
frees the memory. Each half calls a separate function you can see and replace, which is what
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

## What a new-expression does

A `new`-expression is not a function call. The compiler expands it into two steps: a call to an
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

`new T[n]` works the same way through `operator new[]`, then constructs `n` elements in order, and
`delete[]` destroys them in reverse order before calling `operator delete[]`. For element types with
a non-trivial destructor, implementations store the element count in front of the array (the Itanium
C++ ABI calls it an "array cookie"), which is how `delete[]` knows how many destructors to run. That
is also why `delete` on a `new[]` pointer breaks things: it passes the wrong address and runs only
one destructor.

Types that need more alignment than `__STDCPP_DEFAULT_NEW_ALIGNMENT__` get an aligned
`operator new(std::size_t, std::align_val_t)` overload *(C++17)*. See
[alignment](./alignment.md#over-aligned-types-and-new).

## When allocation fails

```cpp title="failure.cpp" showLineNumbers
#include <cstdio>
#include <new>

int main() {
    try {
        auto* huge = new char[1ull << 60];        // far more than any machine has
        delete[] huge;
    } catch (const std::bad_alloc&) {
        std::puts("bad_alloc");
    }

    char* p = new (std::nothrow) char[1ull << 60];   // returns nullptr instead of throwing
    std::puts(p ? "allocated" : "nullptr");
    delete[] p;                                     // deleting nullptr is a no-op
}
```

Output:

```text
bad_alloc
nullptr
```

On Linux, overcommit means that ordinary-sized requests usually succeed even when memory is short,
and the process is killed by the OOM killer later when it touches the pages. Do not rely on
`bad_alloc` as an out-of-memory detector there. The `std::nothrow` form only makes the
*allocation* non-throwing. The constructor can still throw.

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
