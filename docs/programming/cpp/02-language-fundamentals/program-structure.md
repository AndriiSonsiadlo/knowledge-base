---
id: program-structure
title: Program Structure
sidebar_label: Program Structure
sidebar_position: 2
tags: [c++, program-structure, main, namespaces]
---

# Program Structure

A C++ program is one or more source files. Each holds **declarations** (introducing names) and
**definitions** (giving them bodies or storage). Exactly one function, `main`, is where your code
starts. This page covers what a program is made of at the source level: `main` and its arguments,
how a program starts and ends, declaring before use, splitting code across files, and namespaces.

**Prerequisites:** [Basic Syntax](./basic-syntax.md).

## `main`: the entry point

Every program must define exactly one `main` in the global namespace, returning `int`. The standard
guarantees two forms:

```cpp
int main() { /* ... */ }
int main(int argc, char* argv[]) { /* ... */ }   // char** argv means the same
```

Implementations may accept others (some add a third `envp` parameter), but these two are portable.
`main` is special: you cannot call it yourself, take its address, or overload it.

### Command-line arguments

`argc` is the number of arguments, and `argv` an array of C strings holding them. `argv[0]` is
usually the program name as invoked (it may be empty), and `argv[argc]` is always a null pointer.

```cpp title="args.cpp" showLineNumbers
#include <iostream>

int main(int argc, char* argv[]) {
    std::cout << "argc = " << argc << '\n';
    for (int i = 0; i < argc; ++i)
        std::cout << "argv[" << i << "] = " << argv[i] << '\n';
}
```

```bash
./args hello "two words"
```

```text
argc = 3
argv[0] = ./args
argv[1] = hello
argv[2] = two words
```

The shell, not C++, splits the command line: the quotes made `two words` a single argument. To work
with the arguments as strings, copy them: `std::vector<std::string> args(argv, argv + argc);`.

### The exit status

The value `main` returns becomes the process's exit status. `0` (or `EXIT_SUCCESS` from
`<cstdlib>`) means success; `EXIT_FAILURE` or any other non-zero value means failure. Scripts and
build tools check it (`$?` in a POSIX shell, `&&` chaining). POSIX shells see only the low 8 bits,
so `return 259;` shows up as `3`; keep codes between 0 and 255.

Reaching the closing `}` of `main` without a `return` is equivalent to `return 0;`. This applies to
`main` only, and has done since C++98. Every other non-`void` function must return a value.

## How a program starts and ends

`main` is not the first code to run. Objects with **static storage duration** (global variables,
`static` data members, namespace-scope objects) are initialised before `main` starts, and destroyed
after it returns:

<Walkthrough title="Running startup.cpp" caption="Two globals and one local, each printing when constructed and destroyed." accent="green">
  <Step title="The program">

```cpp title="startup.cpp" showLineNumbers
#include <iostream>

struct Tracer {
    const char* name;
    explicit Tracer(const char* n) : name{n} { std::cout << "construct " << name << '\n'; }
    ~Tracer() { std::cout << "destroy " << name << '\n'; }
};

Tracer first{"first"};      // global: constructed before main
Tracer second{"second"};

int main() {
    std::cout << "main starts\n";
    Tracer local{"local"};
    std::cout << "main returns\n";
}
```

  </Step>
  <Step title="Before main: globals constructed">

Globals defined in one file are initialised in the order they appear.

```text
construct first
construct second
```

  </Step>
  <Step title="main runs">

```text
main starts
construct local
main returns
```

  </Step>
  <Step title="main returns: local destroyed">

Leaving `main`'s block destroys its local objects first, like any other block.

```text
destroy local
```

  </Step>
  <Step title="After main: globals destroyed in reverse">

The return value is passed to `std::exit`, which destroys static objects in **reverse** order of
construction and then ends the process.

```text
destroy second
destroy first
```

  </Step>
</Walkthrough>

Within one file the order is the order of definition. **Across files it is unspecified**, so a
global in one file must not rely on a global from another being ready: the "static initialisation
order fiasco". The details and fixes are in
[Storage Duration](../05-memory-and-object-lifetime/storage-duration.md).

## Declare before use

The compiler reads each file top to bottom, and a name must be declared before the code that uses
it. A **declaration** says a name exists and what type it has; a **definition** also provides the
body or storage. A function can be declared early and defined later:

```cpp title="forward.cpp" showLineNumbers
#include <iostream>

void greet(const char* who);   // declaration ("prototype"): no body

int main() {
    greet("world");            // OK: greet has been declared
}

void greet(const char* who) {  // definition
    std::cout << "Hello, " << who << "!\n";
}
```

Without the declaration on line 3, the call in `main` fails with "'greet' was not declared in this
scope". Everything may be declared many times but defined only once in the whole program: the
**One Definition Rule**, covered in [Translation Units](../01-toolchain-and-build/translation-units.md).

## Splitting a program across files

Real programs put declarations in **headers** (`.h`/`.hpp`) and definitions in **source files**
(`.cpp`). Any file that needs a function includes the header that declares it; exactly one `.cpp`
defines it.

<Tabs groupId="files">
  <TabItem value="h" label="mathx.h">

```cpp title="mathx.h"
#pragma once            // include this header only once per source file

int add(int a, int b);  // declaration only
```

  </TabItem>
  <TabItem value="cpp" label="mathx.cpp">

```cpp title="mathx.cpp"
#include "mathx.h"

int add(int a, int b) { return a + b; }   // the one definition
```

  </TabItem>
  <TabItem value="main" label="main.cpp">

```cpp title="main.cpp"
#include <iostream>
#include "mathx.h"

int main() { std::cout << add(2, 3) << '\n'; }   // prints 5
```

  </TabItem>
</Tabs>

```bash
g++ -std=c++20 -Wall main.cpp mathx.cpp -o app && ./app
```

Each `.cpp` is compiled separately and the linker joins the results. How that works, and why it is
organised this way, is in [Translation Units](../01-toolchain-and-build/translation-units.md),
[Headers and Includes](../01-toolchain-and-build/headers-and-includes.md) and
[Include Guards and `#pragma once`](../01-toolchain-and-build/include-guards-and-pragma-once.md).

## Namespaces

Large programs and libraries all need names like `add`, `Buffer` or `parse`. A **namespace** groups
names under a prefix so they cannot collide. The standard library lives in `std`.

```cpp title="namespaces.cpp" showLineNumbers
#include <iostream>

namespace geometry {
    constexpr double pi = 3.141592653589793;
    double circle_area(double r) { return pi * r * r; }
}

namespace app::config {          // nested namespace shorthand (C++17)
    int verbosity = 1;
}

int main() {
    std::cout << geometry::circle_area(2.0) << '\n';   // qualified name: namespace::name
    std::cout << app::config::verbosity << '\n';
}
```

`::` is the scope resolution operator; a leading `::` (`::name`) means the global namespace. You can
shorten names in two ways:

| Form | Effect | Use |
|---|---|---|
| `using std::cout;` | **using-declaration**: brings one name into the current scope | fine in `.cpp` files and inside functions |
| `using namespace std;` | **using-directive**: makes every name in `std` visible | small programs and tests at most |
| `namespace fs = std::filesystem;` | **alias**: a shorter name for a namespace | anywhere |

:::warning[No `using namespace` in headers]
A using-directive in a header applies to every file that includes it, and can silently change which
function a call picks or create ambiguities in code you never saw. Put using-directives only in
`.cpp` files, after all `#include`s, or inside a function.
:::

A namespace without a name (`namespace { ... }`) makes its contents private to one source file;
see [Translation Units](../01-toolchain-and-build/translation-units.md).

## Key points

- One `main` per program; its return value is the exit status, and falling off its end returns 0.
- `argv[0]` is the program name, `argv[argc]` is null.
- Globals are constructed before `main` and destroyed after, in reverse order; across files the order is unspecified.
- Declare before use; define once. Headers declare, source files define.
- Namespaces prevent name collisions; never put `using namespace` in a header.

## Related

- [Compilation Pipeline](../01-toolchain-and-build/compilation-pipeline.md) — from these files to an executable
- [Storage Duration](../05-memory-and-object-lifetime/storage-duration.md) — static, automatic and dynamic lifetimes
- [Function Declarations](../04-functions-and-call-mechanics/function-declarations.md) — declarations in depth
