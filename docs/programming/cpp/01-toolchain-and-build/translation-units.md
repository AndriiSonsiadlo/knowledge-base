---
id: translation-units
title: Translation Units and the One Definition Rule
sidebar_label: Translation Units
sidebar_position: 9
tags: [c++, translation-units, compilation, linking, one-definition-rule]
---

# Translation Units and the One Definition Rule

A **translation unit** (TU) is one source file after preprocessing: the `.cpp` with every header it
includes pasted in. It is the unit the compiler works on, and each one is compiled with no knowledge
of any other. Two consequences shape all multi-file C++: the compiler can only check a TU against
the *declarations* it contains, and the rules that keep the separately compiled pieces consistent
(**linkage** and the **One Definition Rule**) are checked only partly, by the linker, or not at all.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md),
[Object Files and Symbols](./object-files-and-symbols.md).

## One `.cpp`, one TU, one object

<Diagram title="Separate compilation" caption="No arrow connects the two TUs until the linker." accent="blue">
  <DiagramRow>
    <DiagramGroup label="TU 1">
      <DiagramNode icon="file-text" title="main.cpp">+ square.h pasted in</DiagramNode>
      <DiagramNode icon="binary" title="main.o">needs `square(int)`</DiagramNode>
    </DiagramGroup>
    <DiagramGroup label="TU 2">
      <DiagramNode icon="file-text" title="square.cpp">+ square.h pasted in</DiagramNode>
      <DiagramNode icon="binary" title="square.o">defines `square(int)`</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
  <DiagramArrow label="link" />
  <DiagramNode icon="cpu" title="app" accent>The only place the two meet</DiagramNode>
</Diagram>

Headers are not compiled on their own; they are text that becomes part of every TU that includes
them. That is why a header's contents must be things that are safe to repeat in many TUs:
declarations, class definitions, `inline` functions and templates. See
[Headers and Includes](./headers-and-includes.md) for how to organise them.

Separate compilation is what makes incremental builds possible: edit `square.cpp` and only that TU
is recompiled before relinking. Edit `square.h` and every TU that includes it is recompiled.

## Declarations and definitions

A **declaration** introduces a name and its type. A **definition** is a declaration that also
creates the entity: allocates the variable, provides the function body, gives the class its members
([cppreference: definitions and ODR](https://en.cppreference.com/w/cpp/language/definition)).

| Code | Declaration or definition? |
|---|---|
| `int square(int x);` | Declaration of a function |
| `int square(int x) { return x * x; }` | Definition |
| `extern int counter;` | Declaration of a variable |
| `int counter;` / `int counter = 0;` | Definition (zero-initialised if no initialiser, for a namespace-scope variable) |
| `class Widget;` | Declaration (forward declaration; `Widget` is an incomplete type) |
| `class Widget { int v; };` | Definition of the class (its member functions may still be only declared) |

A TU can use a function or variable after seeing only its declaration; the linker supplies the
definition. Using a class by value, or calling its members, needs the class definition in the TU.

## Linkage: which names are shared

**Linkage** decides whether the same name in two TUs refers to the same entity.

| Linkage | How you get it | Effect | `nm` shows |
|---|---|---|---|
| **External** | Default for non-`const` namespace-scope variables and functions; `extern` | One entity for the whole program | Upper-case letter (`T`, `D`, `B`) |
| **Internal** | `static` at namespace scope, anything in an unnamed namespace, namespace-scope `const`/`constexpr` variables (unless `extern` or `inline`) | Each TU has its own private copy | Lower-case letter, or nothing at all |
| **None** | Local variables, function parameters | Only visible in its own scope | Nothing |
| **Module** *(C++20)* | Non-exported names in a named module | Shared within the module only | [Modules](./modules.md) |

```cpp title="linkage.cpp"
namespace { int hidden = 1; }   // internal
static int also_hidden = 2;     // internal
int visible = 3;                // external
int use() { return hidden + also_hidden; }
```

```text
0000000000000000 T use()
0000000000000004 d also_hidden
0000000000000000 d (anonymous namespace)::hidden
0000000000000008 D visible
```

Prefer the unnamed namespace for TU-private helpers. It also works for types, which `static`
cannot mark.

## The One Definition Rule

The ODR has two halves:

1. **Within one TU**, any variable, function, class, enum or template may be defined at most once.
   The compiler checks this (`redefinition of …`).
2. **Across the program**, every non-inline function and variable with external linkage that is
   used must be defined **exactly once**. Classes, `inline` functions, `inline` variables
   *(C++17)* and templates may be defined in several TUs, but **every definition must be token for
   token identical** and mean the same thing.

The linker enforces only part of the second half:

| Violation | Detected? |
|---|---|
| A used function or variable defined in no TU | Yes: `undefined reference` |
| A non-inline definition in two TUs (for example, `int global = 42;` in a header) | Yes: `multiple definition of 'global'` |
| An `inline` function or a class defined *differently* in two TUs | **No.** Undefined behaviour, no diagnostic required |

The last row is the dangerous one. Two TUs that each define their own `struct Config` and
`inline int get_size()`:

<Tabs>
  <TabItem value="a" label="a.cpp">

```cpp title="a.cpp"
struct Config { int size = 1; };
inline int get_size() { Config c; return c.size; }
int from_a() { return get_size(); }
```

  </TabItem>
  <TabItem value="b" label="b.cpp">

```cpp title="b.cpp"
struct Config { int size = 2; };
inline int get_size() { Config c; return c.size; }
int from_a();
#include <cstdio>
int main() { std::printf("%d %d\n", from_a(), get_size()); }
```

  </TabItem>
</Tabs>

<Walkthrough title="One ODR violation, three answers" caption="GCC 15. Same sources, no warnings, different output." accent="amber">
  <Step title="g++ -O0 a.cpp b.cpp">

```text
1 1
```

`get_size` is a weak symbol in both objects. The linker keeps the **first** one it sees, from
<StepChange>`a.o`</StepChange>, so `main` also gets `1`.

  </Step>
  <Step title="g++ -O0 b.cpp a.cpp">

```text
2 2
```

Only the order of the files changed. Now <StepChange>`b.o`'s copy</StepChange> is kept, and
`from_a` returns `2`.

  </Step>
  <Step title="g++ -O2 a.cpp b.cpp">

```text
1 2
```

At `-O2` each TU inlines its own `get_size` before the linker runs, so each one sees
<StepChange>its own `Config`</StepChange>. The weak copies are never called.

  </Step>
</Walkthrough>

The real-world version of this bug is two libraries that each have an internal `struct Node`, or a
header compiled with different `#define`s in different TUs. The fixes:

- Put TU-private types and helpers in an **unnamed namespace**: each TU then has its own distinct
  entity, and there is nothing to violate.
- Put shared definitions in **one header**, included everywhere, never copied.
- Compile all TUs of a program with the same macros and flags that affect headers.

### Defining shared variables

```cpp title="config.h"
extern int request_count;          // declaration: every TU may see it
inline int max_connections = 64;   // definition, allowed in many TUs (C++17)
constexpr int buffer_size = 4096;  // internal linkage: one private copy per TU
```

`request_count` then needs exactly one `int request_count = 0;` in one `.cpp`. `inline` variables
*(C++17)* remove that need: the linker keeps one copy, as with `inline` functions.

## Templates and inline functions

To instantiate a template or inline a function, the compiler needs its **definition** in the
current TU. A template declared in a header and defined in a `.cpp` compiles, then fails to link:

```cpp title="fragment: max.h, max.cpp, main.cpp"
// max.h
template <typename T> T biggest(T a, T b);
// max.cpp
#include "max.h"
template <typename T> T biggest(T a, T b) { return a > b ? a : b; }
// main.cpp
#include "max.h"
int main() { return biggest(5, 10); }
```

```text
main.cpp:(.text+0x13): undefined reference to `int biggest<int>(int, int)'
```

`main.cpp` needed `biggest<int>` but could not create it; `max.cpp` could have, but nothing in that
TU asked for `int`. Either define the template in the header, or keep it in the `.cpp` and add
explicit instantiations there (`template int biggest<int>(int, int);`) for the types you support.
The meaning of `inline` itself is on [Inline Functions](../04-functions-and-call-mechanics/inline-functions.md).

## How big is a TU?

Measured with GCC 15, `g++ -std=c++23 -E -P | wc -l` on a file containing only the include:

| Header | Lines after preprocessing |
|---|---|
| `<iostream>` | 49,552 |
| `<algorithm>` | 23,974 |
| `<string>` | 23,859 |
| `<vector>` | 21,470 |
| `<map>` | 20,155 |
| all five together | 61,707 |

The headers share most of their internals, so the total is far less than the sum. Even so, a
one-line `main.cpp` that includes them makes the compiler parse over 60,000 lines, and it does so
again in every TU. This is the cost [modules](./modules.md) and
[precompiled headers](./headers-and-includes.md#precompiled-headers) attack.

## Pitfalls

- **A variable defined in a header** without `inline`/`extern`: `multiple definition` as soon as two
  TUs include it.
- **The same class name for two different classes** in two `.cpp` files, both at namespace scope:
  a silent ODR violation, as traced above. Use an unnamed namespace.
- **A `static` variable in a header used as a "global".** Each TU gets its own copy; updates in one
  TU are invisible in the others.
- **Different `-D` flags for different TUs** that include the same header with `#ifdef`-dependent
  class layouts: the classes differ, and nothing reports it.

## Key points

- A TU is one `.cpp` after preprocessing; the compiler sees nothing else.
- External linkage = one entity program-wide; internal linkage = a private copy per TU.
- ODR: one definition of each non-inline entity; identical definitions of inline entities and
  classes. The linker catches missing and duplicate definitions, not differing ones.
- Templates must be defined (or explicitly instantiated) where they are used.
