---
id: headers-and-includes
title: Headers and Includes
sidebar_label: Headers & Includes
sidebar_position: 10
tags: [c++, headers, includes, organization, preprocessor]
---

# Headers and Includes

C++ has no built-in way for one source file to see another's declarations. The convention that fills
the gap is the **header**: a file of declarations that every user `#include`s, which the
preprocessor pastes into each [translation unit](./translation-units.md). The mechanism is pure
text, so everything about headers (what goes in them, the order you include them, how fast the
build is) follows from one fact: **a header is compiled again as part of every TU that includes
it.**

**Prerequisites:** [Preprocessing](./preprocessing.md), [Translation Units](./translation-units.md).

Preventing a header from being pasted twice into one TU is on
[Include Guards and `#pragma once`](./include-guards-and-pragma-once.md).
[Modules](./modules.md) *(C++20)* are the alternative to this model.

## The interface/implementation split

<Tabs>
  <TabItem value="h" label="calculator.h">

```cpp title="calculator.h"
#pragma once

class Calculator {
public:
    explicit Calculator(int start);
    int value() const;
    void add(int x);
private:
    int value_;
};

int multiply(int a, int b);
```

  </TabItem>
  <TabItem value="cpp" label="calculator.cpp">

```cpp title="calculator.cpp"
#include "calculator.h"

Calculator::Calculator(int start) : value_(start) {}
int Calculator::value() const { return value_; }
void Calculator::add(int x) { value_ += x; }

int multiply(int a, int b) { return a * b; }
```

  </TabItem>
</Tabs>

Users include `calculator.h` and link `calculator.o`. Changing a function body only recompiles
`calculator.cpp`; changing the class (even a private member) recompiles every user, because the
class definition determines object size and layout. [PIMPL](../13-idioms-and-design/02-pimpl.md)
exists to break that dependency.

## What belongs in a header

The rule comes straight from the [One Definition Rule](./translation-units.md#the-one-definition-rule):
a header may contain only what is allowed to appear in many TUs.

| In the header | Why it is safe |
|---|---|
| Function declarations, `extern` variable declarations | Declarations can repeat |
| Class, struct, enum definitions | Allowed once per TU, identical everywhere |
| `inline` functions, member functions defined inside the class body | Inline: the linker keeps one copy |
| Templates (definitions, not just declarations) | Must be visible to instantiate |
| `constexpr` variables, `inline` variables *(C++17)* | Internal linkage / inline: no duplicates |
| Type aliases, `concept`s | Not objects; no linker symbol |

| Not in the header | What goes wrong |
|---|---|
| Non-inline function definitions, `int global = 0;` | `multiple definition` at link time |
| `using namespace std;` at file scope | Applies to every file that includes the header, after the include |
| `static` functions or variables | A separate private copy in every TU (bloat; a "global" that is not shared) |
| Includes the header itself doesn't need | Every user pays to parse them |

## Where the compiler looks

GCC searches in this order ([GCC: Search Path](https://gcc.gnu.org/onlinedocs/cpp/Search-Path.html)):

<Diagram title="Include search order (GCC, Clang)" accent="violet">
  <DiagramNode title="#include with quotes" accent>1. The directory of the file containing the `#include` (not the current working directory). 2. Directories from `-iquote`.</DiagramNode>
  <DiagramArrow label="then, for both forms" />
  <DiagramNode title="Both forms">3. `-I` directories, left to right. 4. `-isystem` directories. 5. The standard system directories. 6. `-idirafter`.</DiagramNode>
</Diagram>

So quotes only *add* places to look in front of the angle-bracket list. Use `"…"` for your
project's headers and `<…>` for the standard library and third-party libraries. Print the actual
system list for your compiler with:

```bash
echo | g++ -std=c++23 -x c++ -E -v - 2>&1 | sed -n '/search starts/,/End of search/p'
```

```text
#include "..." search starts here:
#include <...> search starts here:
 /usr/include/c++/15
 /usr/include/x86_64-linux-gnu/c++/15
 /usr/include/c++/15/backward
 /usr/lib/gcc/x86_64-linux-gnu/15/include
 /usr/local/include
 /usr/include/x86_64-linux-gnu
 /usr/include
End of search list.
```

Headers found through `-isystem` (and the system directories) are treated as **system headers**:
warnings inside them are suppressed. That is the right place for third-party code you don't
control; CMake does this for imported targets automatically.

### A project layout

```text
project/
├── include/mylib/      public headers, installed with the library
│   ├── api.h
│   └── util.h
├── src/                implementation and private headers
│   ├── api.cpp
│   └── detail.h
└── tests/
```

Compile with `-I include` and write `#include "mylib/api.h"`. The `mylib/` prefix makes names
unique across libraries (two libraries can both have a `util.h`) and tells the reader where the
header comes from. In CMake that is `target_include_directories(mylib PUBLIC include PRIVATE src)`
([CMake: target properties](../../cmake/02-targets/target-properties.md)).

## Self-contained headers and include order

A header must compile on its own: it includes everything it uses. Test it by compiling the header
alone as C++:

```bash
g++ -std=c++23 -fsyntax-only -x c++ bad.h     # bad.h uses std::cout without <iostream>
```

```text
bad.h: In member function ‘void W::print()’:
bad.h:1:39: error: ‘cout’ is not a member of ‘std’
```

(Don't use `g++ -c widget.h` for this: GCC treats a `.h` input as a request to build a
[precompiled header](#precompiled-headers) and writes `widget.h.gch`.)

A common include order makes the same check happen for free in every build:

```cpp title="widget.cpp"
#include "mylib/widget.h"     // 1. this file's own header first: proves it is self-contained

#include <string>             // 2. standard library
#include <vector>

#include <fmt/format.h>       // 3. third-party libraries

#include "mylib/util.h"       // 4. other project headers
```

**Include what you use.** If a file uses `std::vector`, it includes `<vector>`, even if another
header happens to include it today. Transitive includes change between library versions; code that
relied on them stops compiling. The `include-what-you-use` tool and clang-tidy's
`misc-include-cleaner` check report both missing and unused includes.

## Forward declarations

When a header only needs to *name* a type, a forward declaration avoids including that type's header:

```cpp title="widget.h"
#pragma once
class Database;                   // forward declaration

class Widget {
public:
    explicit Widget(Database& db);
    void process();
private:
    Database* db_;                // pointer to an incomplete type: fine
};
```

`widget.cpp` then includes `database.h`. Users of `widget.h` no longer recompile when
`database.h` changes.

| Works with only `class Database;` | Needs the full definition |
|---|---|
| `Database*`, `Database&` members and parameters | `Database db;` member by value |
| Function declarations taking or returning `Database` by value | Calling any member, `sizeof(Database)` |
| `std::unique_ptr<Database>` member (if the destructor is defined in the `.cpp`) | Inheriting from `Database` |

```text
w2.h:2:25: error: field ‘db’ has incomplete type ‘Database’
```

Forward declarations also break **circular includes**: if `a.h` needs `B` and `b.h` needs `A`, at
least one of them must use a pointer or reference and a forward declaration, because two classes
cannot contain each other by value.

Don't forward-declare names from `std` (`namespace std { class string; }` is undefined behaviour);
use `<iosfwd>` for the stream types.

## Precompiled headers

A precompiled header (PCH) stores the compiler's parsed state for a set of stable headers, so each
TU loads it instead of reparsing.

```bash
g++ -std=c++23 -O2 -x c++-header pch.h -o pch.h.gch    # build once
g++ -std=c++23 -O2 -include pch.h -c main.cpp          # GCC uses pch.h.gch if compatible
```

`-H` shows whether it was used: `! ./pch.h.gch` means used, `x ./pch.h.gch` means rejected. In
this run, the same command with `-O0` instead of `-O2` printed `x`: GCC only accepts a PCH built with
compatible options. The `.gch` for `<iostream>`, `<vector>` and `<map>` was 58.7 MB. With CMake,
`target_precompile_headers(app PRIVATE <vector> <string>)` handles the details; measure the build
before and after to decide whether it is worth it.

## Header-only libraries

A library that consists only of headers (all `inline` functions and templates) needs no separate
build or link step: users just include it. Many popular libraries work this way
([nlohmann/json](../../nlohmann-json/readme.md), much of Boost). The cost is compile time: every TU
compiles all of it, and a change to the library recompiles everything that includes it.

## Pitfalls

- **Relying on transitive includes.** Compiles today, breaks after a library upgrade.
- **`using namespace` in a header.** Name clashes appear in files that never asked for them.
- **A heavy include in a widely used header.** `<windows.h>` or a large framework header in a
  `common.h` multiplies build time across the whole project. Move it into the `.cpp`.
- **Headers that compile only after another include.** Caught by including each file's own header
  first.

## Key points

- A header is text pasted into every TU that includes it; it may contain only ODR-safe entities.
- `"…"` searches the including file's directory first, then the same paths as `<…>`.
- Include your own header first, include what you use, and forward-declare what you only name.
- Build time scales with header text times TUs: PCH and modules attack that product.
