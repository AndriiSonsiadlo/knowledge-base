---
id: c-vs-cpp
title: C vs C++
sidebar_label: C vs C++
sidebar_position: 2
tags: [ c++, c, comparison, overview ]
---

# C vs C++

C++ started as C with classes, and most C still compiles as C++. But C++ is not a strict superset of
C. The two are separate languages with separate ISO standards (C23 and C++23 are the current ones),
and some valid C is rejected by a C++ compiler or means something different. This page is for
readers who know C: it lists where the languages part ways and what C++ adds on top.

**Prerequisites:** [What is C++?](./what-is-cpp.md)

<Diagram title="How the two languages overlap" accent="violet">
  <DiagramRow>
    <DiagramNode title="C only" dashed>VLAs, `restrict`, implicit `void*` conversion, C++ keywords as names</DiagramNode>
    <DiagramNode title="Common subset" accent>Functions, structs, pointers, the C library</DiagramNode>
    <DiagramNode title="C++ only">Classes, references, overloading, templates, namespaces, exceptions</DiagramNode>
  </DiagramRow>
</Diagram>

## Valid C that is not valid C++

All of the following compiles as C17 with `gcc -std=c17`. The commented lines are errors or
warnings under `g++ -std=c++17 -pedantic`:

```c title="valid-c.c" showLineNumbers
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(4 * sizeof *p);   // C++: error, void* does not convert to int*
    int n = 3;
    int vla[n];                       // C++: variable-length arrays are not standard
    int class = 1;                    // C++: `class` is a keyword
    printf("%zu %d %zu\n", sizeof 'a', class, sizeof vla);
    free(p);
}
```

| Construct | C | C++ |
|---|---|---|
| `void*` to `T*` | Implicit conversion | Requires a cast. In C++, prefer `new` or a container anyway. |
| Variable-length arrays | C99. Optional since C11. | Not standard. GCC and Clang accept them as an extension (`-Wvla` warns). |
| `restrict` | Keyword (C99) | Not standard. Compilers offer `__restrict`. |
| Type of `'a'` | `int`, so `sizeof 'a'` is 4 on common platforms | `char`, so `sizeof 'a'` is 1 |
| `int f();` | Before C23: parameters unspecified. C23: no parameters. | Always no parameters |
| C++ keywords (`class`, `new`, `template`, …) as identifiers | Allowed | Errors |
| Designated initializers | Any order, nested, arrays (`[3] = 1`) | C++20 only, in declaration order, no array designators. See [aggregate initialization](../05-memory-and-object-lifetime/initialization/aggregate-initialization.md). |
| `const int x = 1;` at file scope | External linkage | Internal linkage (each translation unit has its own copy) |

Most of these only matter when you compile C sources as C++ or share headers between the two
languages. The usual fix is to keep C files compiled as C and put `extern "C"` on the shared
declarations. See [Interop with C](../12-low-level-and-platform/07-interop-c.md).

## What C++ adds

| Feature | What it changes | Canonical page |
|---|---|---|
| References | Aliases that can't be null or reseated, so you don't need pointers for out-parameters | [References](../06-pointers-references-and-smart-pointers/references.md) |
| Function overloading | Several functions with one name, chosen by argument types. This forces [name mangling](../01-toolchain-and-build/name-mangling.md). | [Overloading](../04-functions-and-call-mechanics/overloading.md) |
| Classes, constructors, destructors | Objects that establish and clean up their own state | [Constructors & Destructors](../07-classes-and-oop/constructors-and-destructors.md) |
| RAII and smart pointers | Resources released automatically at scope exit | [RAII](../13-idioms-and-design/01-raii.md), [unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md) |
| Templates | Type-safe generic code, generated at compile time | [Function Templates](../08-templates-and-metaprogramming/function-templates.md) |
| Namespaces | No more `prefix_` naming to avoid collisions | [Program Structure](../02-language-fundamentals/program-structure.md) |
| Exceptions | Error propagation separated from the return value | [Exceptions](../10-error-handling-and-safety/01-exceptions.md) |
| Standard library | Containers, algorithms, strings, threads, filesystem | [Standard Library](../09-standard-library/containers.md) |

## The same task in both languages

The biggest practical difference is who releases resources. In C, every allocation is paired with
a matching free on every path, including error paths:

```c title="greet.c" showLineNumbers
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *make_greeting(const char *name) {
    size_t len = strlen("Hello, ") + strlen(name) + 1;
    char *s = malloc(len);
    if (!s) return NULL;                    // caller must check
    snprintf(s, len, "Hello, %s", name);
    return s;                               // caller must free
}

int main(void) {
    char *g = make_greeting("Ada");
    if (!g) return 1;
    puts(g);
    free(g);                                // forget this and it leaks
}
```

In C++, `std::string` owns its buffer. The buffer is freed when the string's destructor runs, on
every path out of the scope, and allocation failure is reported by an exception rather than a
`NULL` the caller can forget to check:

```cpp title="greet.cpp" showLineNumbers
#include <iostream>
#include <string>

std::string make_greeting(const std::string& name) {
    return "Hello, " + name;
}

int main() {
    std::cout << make_greeting("Ada") << '\n';
}   // nothing to free
```

The C++ version doesn't run any slower: the work is the same allocation and copy. The
difference is that the compiler inserts the cleanup for you.

## When C is still the better choice

- **The platform only has a C toolchain**, or the C++ runtime (exceptions, RTTI, the standard
  library) doesn't fit in the memory budget. Many embedded targets have one of these constraints,
  although a restricted C++ subset is often still possible there.
- **You need a stable ABI**, for example a library meant to be called from many languages. C's ABI
  is the common denominator. C++ libraries usually expose a C interface for this reason.
- **The codebase and its contributors are C**, as in the Linux kernel.

## Related

- [Interop with C](../12-low-level-and-platform/07-interop-c.md): `extern "C"`, sharing headers,
  and passing data across the boundary.
- [Name Mangling](../01-toolchain-and-build/name-mangling.md): why C++ symbols look different from
  C's in an object file.
- [Memory & Object Lifetime](../05-memory-and-object-lifetime/memory-model-overview.md): where the
  C++ object model goes beyond C's.
