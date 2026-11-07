---
id: interop-c
title: C Interoperability
sidebar_label: C Interoperability
sidebar_position: 7
tags: [cpp, c-interop, extern-c, language-linkage, abi, opaque-handle, c-api]
---

# C Interoperability

C is the lowest common denominator of native languages: nearly every language, and every operating
system API, can call a C function. A C++ library that wants to be callable from C, Python, Rust or from a plug-in
loaded with `dlopen` exposes a **C interface**, and a C++ program that uses a C library includes its header.
Both directions rest on one language feature, **language linkage** (`extern "C"`), plus rules about what may
appear in the signatures.

**Prerequisites:** [Name mangling](../01-toolchain-and-build/name-mangling.md) (what `extern "C"` turns
off and how a header is shared) and [ABI](./01-abi.md).

## What `extern "C"` does

`extern "C"` gives a declaration **C language linkage**. In practice, with GCC and Clang, that means:

- the symbol name is the plain identifier (`counter_get`), with no mangling, so a C compiler or
  `dlsym("counter_get")` finds it;
- the function can have only one definition per name: no overloads, since both would need the same symbol
  (two overloads with C linkage are ill-formed);
- the function uses the platform's C calling convention, which on x86-64 is the one C++ functions already
  use. See [Calling conventions](../04-functions-and-call-mechanics/calling-conventions.md).

It is a **linkage** property only. It does not make the function body C: the body is C++ and can use
classes, templates and exceptions internally. The standard also says that function types with different
language linkages are distinct types, but GCC and Clang treat them as the same,
so passing a C++-linkage function as a C callback compiles. Declare callbacks `extern "C"` anyway; code that
relies on the leniency is formally not portable.

```cpp title="forms.cpp (fragment)"
extern "C" int one(int);                  // a single declaration

extern "C" {                              // a block: everything inside has C linkage
    int two(int);
    int three(int);
}
```

Linkage specifications may only appear at namespace scope. Names declared inside a namespace in the block
still get plain symbol names. Two functions in different namespaces with the same name and C linkage refer
to the *same* function.

## A header that both languages can include

Use the pattern from the [name mangling](../01-toolchain-and-build/name-mangling.md#extern-c-switching-mangling-off)
page: `#ifdef __cplusplus` around `extern "C" {`. The header below is written in the subset both languages share. Its
implementation shows the usual shape of a C wrapper around a C++ class: an **opaque handle**, explicit
create/destroy functions, and error codes instead of exceptions.

```c title="counter.h"
#ifndef COUNTER_H
#define COUNTER_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct counter counter;                 /* opaque to C */

enum counter_status { COUNTER_OK = 0, COUNTER_ERR_RANGE = 1, COUNTER_ERR_INTERNAL = 2 };

counter* counter_create(int start);             /* NULL on failure */
void counter_destroy(counter* c);
enum counter_status counter_add(counter* c, int delta);
int counter_get(const counter* c);

typedef void (*counter_visit_fn)(int value, void* user);
void counter_for_each_step(const counter* c, counter_visit_fn fn, void* user);

#ifdef __cplusplus
}
#endif
#endif
```

```cpp title="counter.cpp" showLineNumbers
#include "counter.h"

#include <climits>
#include <stdexcept>
#include <vector>

struct counter {                                 // a C++ type; C only sees a pointer to it
    std::vector<int> history;
    int value;
};

extern "C" {

counter* counter_create(int start) {
    try {
        return new counter{{}, start};
    } catch (...) {
        return nullptr;
    }
}

void counter_destroy(counter* c) { delete c; }

counter_status counter_add(counter* c, int delta) {
    try {
        if ((delta > 0 && c->value > INT_MAX - delta) || (delta < 0 && c->value < INT_MIN - delta))
            throw std::out_of_range("overflow");
        c->history.push_back(c->value);          // may throw std::bad_alloc
        c->value += delta;
        return COUNTER_OK;
    } catch (const std::out_of_range&) {
        return COUNTER_ERR_RANGE;
    } catch (...) {
        return COUNTER_ERR_INTERNAL;
    }
}

int counter_get(const counter* c) { return c->value; }

void counter_for_each_step(const counter* c, counter_visit_fn fn, void* user) {
    for (int v : c->history) fn(v, user);
}

}  // extern "C"
```

```c title="main.c"
#include <stdio.h>
#include "counter.h"

static void print_step(int value, void* user) {
    int* n = (int*)user;
    printf("step %d: %d\n", (*n)++, value);
}

int main(void) {
    counter* c = counter_create(10);
    if (!c) return 1;
    counter_add(c, 5);
    counter_add(c, -3);
    enum counter_status st = counter_add(c, 2147483647);
    printf("final %d, overflow status %d\n", counter_get(c), (int)st);
    int n = 0;
    counter_for_each_step(c, print_step, &n);
    counter_destroy(c);
    return 0;
}
```

```bash
g++ -std=c++20 -Wall -Wextra -c counter.cpp
gcc -std=c11   -Wall -Wextra -c main.c
g++ main.o counter.o -o app        # link with the C++ driver
./app
```

```text
final 12, overflow status 1
step 0: 10
step 1: 15
```

(gcc/g++ 15 and clang/clang++ 21, `-O0` and `-O2`, x86-64 Linux. Each pair compiled and linked with the
matching C and C++ compilers, same output.) The failed `counter_add(c, INT_MAX)` left the counter unchanged,
because the range check runs before any modification. This is the strong exception-safety guarantee turned into an error code;
see [Exception safety](../10-error-handling-and-safety/02-noexcept-and-strong-guarantee.md).

Design points visible in this example:

- **Opaque handle.** C sees `struct counter` as an incomplete type and only holds a `counter*`. The same `struct`
  name is a full C++ class in the `.cpp`, so no cast is needed. (If the C++ type has another name, or is a class hierarchy,
  an opaque `struct handle` plus `static_cast`/`reinterpret_cast` inside the wrapper does the same job.)
- **Create/destroy pairs.** C has no destructors, so every resource has an explicit release function, and the
  header documents who owns what. `new` in the library must be matched by `delete` in the library, never `free`
  in the caller. See [new and delete](../05-memory-and-object-lifetime/new-and-delete.md).
- **No C++ types in signatures**: no references, `std::string`, `std::vector`, classes by value,
  default arguments, overloads or templates. The header must compile as C.
- **Callbacks** take a `void* user` argument so the C++ side can smuggle its object through, and are
  declared with C linkage.
- **Link with the C++ driver** (`g++`) or add `-lstdc++`. Linking the same objects with plain `gcc` fails on this
  machine with `undefined reference to 'operator new(unsigned long)'` and `__cxa_begin_catch`, because the C
  driver does not add the C++ runtime. The same objects linked with `gcc ... -lstdc++` produced the output
  above.

## No exceptions across the boundary

A C function has no way to catch an exception, and C frames have no unwind information to unwind through (they
are normally compiled without `-fexceptions`). The standard does not say what happens when a C++ exception
leaves an `extern "C"` function; the practical outcomes are `std::terminate` or undefined behaviour. So every
exported function must catch everything and translate it to a return value, as `counter_create` and `counter_add`
do. A common error-reporting shape is a status enum, as here, with `counter_last_error()`-style functions for the message.
Marking the functions `noexcept` makes the guarantee explicit and the compiler will terminate on a missed
exception instead of unwinding: see [noexcept](../04-functions-and-call-mechanics/noexcept.md).

The same applies to callbacks in the other direction: a C++ callback invoked by C code must not let an exception
escape into the C library.

## Types that can cross

| Type | Cross the boundary? |
|---|---|
| Fixed-width integers, `size_t`, `double`, `float`, pointers | Yes. Prefer `<stdint.h>` types for anything with a defined size |
| `bool` in C++, `_Bool` in C (`bool` from `<stdbool.h>`) | Same size on common ABIs, but not guaranteed by the standards. Many C APIs use `int` for flags |
| `enum` | The underlying type is implementation-defined unless fixed, and C and C++ rules differ. Fine within one toolchain, as in the example. For a stable binary interface pass an `int` or fixed-width integer |
| Standard-layout structs of the above | Yes, with the same layout on both sides *for one platform and ABI*. Pin it with `static_assert` on `sizeof`/`offsetof` ([Padding and offsetof](./03-padding-and-offsetof.md)) |
| Classes with virtual functions, bases with state, `std::string`, containers, references | No. Their layout is a C++ ABI matter ([Object layout](./02-object-layout.md)) and C cannot spell them |
| Function pointers | Yes, with C linkage and a C-compatible signature |
| Variadic functions | Yes, but a C++ caller must see a correct prototype. See [Calling conventions](../04-functions-and-call-mechanics/calling-conventions.md#variadic-functions) |

A struct that must be shared by value, not behind a handle, should be a plain aggregate of the types in the
table, written in the common subset of C and C++ (no member functions, no access specifiers, no default
member initialisers). Whether C and C++ agree on its layout is an ABI question; for mainstream
platforms they do for such structs, which is the point of "standard-layout".

## What does not carry over

| In `extern "C"` | Why |
|---|---|
| Overloaded functions | One symbol per name |
| Templates | `extern "C"` templates are ill-formed. Wrap each instantiation you want in its own named function |
| Member functions | They have an implicit `this` and a mangled name. Export a free function taking the handle |
| References | C has none. Use pointers |
| Default arguments | C declarations have none. A header shared with C cannot use them |

## Calling C from C++

Include the C library's header. If it carries its own `__cplusplus` guard, nothing else is needed.
A header without guards must be wrapped by the includer:

```cpp title="legacy.cpp (fragment)"
extern "C" {
#include "legacy_c_library.h"      // a header with no extern "C" of its own
}
```

Do not wrap standard headers this way: `<stdio.h>` and `<cstdio>` are already C++-aware. Skipping the wrapper
for a C-only header compiles and then fails at link time with an `undefined reference` to a mangled name; the
[name mangling page](../01-toolchain-and-build/name-mangling.md#signature-mismatches) shows how to read it.
C++ wrappers of a C API typically give it RAII: a `std::unique_ptr` with a custom deleter that calls the
library's `destroy` function ([Custom deleters](../06-pointers-references-and-smart-pointers/custom-deleters.md)).

## Differences between C and C++ to watch for

The common subset is smaller than it looks. Constructs valid in C that are errors or behave differently in C++
(implicit `void*` conversion, `const` linkage, `sizeof('a')`, and others) are listed on
[C versus C++](../00-overview/c-vs-cpp.md). Notably for a shared header: variable-length arrays and `restrict` are not standard C++, and C++20 designated
initialisers are more restricted than C99's.

## Key points

- `extern "C"` selects C language linkage: unmangled names, no overloading, the C calling convention. It does
  not make the code C.
- Share one header with `#ifdef __cplusplus` guards. Expose C++ classes through opaque handles and
  create/destroy functions.
- Never let an exception cross: catch everything inside each exported function and return a status.
- Only C-compatible types appear in signatures: fixed-width scalars, pointers, standard-layout structs,
  C-linkage function pointers.
- Link with the C++ driver (or add the C++ runtime) when any object is C++.

## References

- [cppreference: language linkage](https://en.cppreference.com/w/cpp/language/language_linkage)
