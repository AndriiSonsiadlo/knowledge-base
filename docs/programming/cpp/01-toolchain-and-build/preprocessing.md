---
id: preprocessing
title: Preprocessing
sidebar_label: Preprocessing
sidebar_position: 2
tags: [c++, preprocessor, macros, includes, compilation]
---

# Preprocessing

The preprocessor is stage 1 of the [compilation pipeline](./compilation-pipeline.md). It rewrites
the source text before the compiler parses it: it pastes in `#include`d files, expands macros, and
keeps or drops blocks of code under `#if`. It works on **tokens, not on C++**: it knows nothing
about types, scopes or namespaces. That is what makes it useful for things the language cannot
express (platform switches, build-time configuration) and dangerous for everything else.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md).

This page covers the directives and macros. How to organise headers is on
[Headers and Includes](./headers-and-includes.md), and stopping a header from being pasted twice is
on [Include Guards and `#pragma once`](./include-guards-and-pragma-once.md).

## What the preprocessor does

<Diagram title="Inputs and output of stage 1" accent="violet">
  <DiagramRow>
    <DiagramNode icon="file-text" title="main.cpp">Your source with `#` directives</DiagramNode>
    <DiagramNode icon="layers" title="Headers">Every file reached through `#include`, recursively</DiagramNode>
    <DiagramNode icon="settings" title="Command line">`-D`, `-U`, `-I`, plus predefined macros</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="include, expand, select" />
  <DiagramNode icon="file-text" title="Translation unit (.ii)" accent>One long C++ text with no directives left</DiagramNode>
</Diagram>

The standard describes this as translation phases 1–6: line splicing (a `\` at the end of a line
joins it to the next), splitting into preprocessing tokens, then directive execution and macro
expansion ([cppreference: phases of translation](https://en.cppreference.com/w/cpp/language/translation_phases)).
To see the result, stop after stage 1:

```bash
g++ -std=c++23 -E main.cpp -o main.ii        # full output with '# line' markers
g++ -std=c++23 -E -P main.cpp                # without line markers
g++ -std=c++23 -H -fsyntax-only main.cpp     # print the include tree to stderr
echo | g++ -std=c++23 -dM -E -x c++ -        # list every predefined macro
```

The result is large: with GCC 15, preprocessing a file that contains only `#include <iostream>`
gives 49,552 lines (`g++ -std=c++23 -E -P | wc -l`).

## The directives

| Directive | Purpose |
|---|---|
| `#include <file>` / `#include "file"` | Replace the line with the file's contents. Search rules: [Headers and Includes](./headers-and-includes.md#where-the-compiler-looks) |
| `#define`, `#undef` | Define or remove a macro |
| `#if`, `#ifdef`, `#ifndef`, `#elif`, `#else`, `#endif` | Conditional inclusion of code |
| `#elifdef`, `#elifndef` *(C++23)* | Shorthand for `#elif defined(X)` / `#elif !defined(X)` |
| `#error "msg"`, `#warning "msg"` *(`#warning` standard since C++23)* | Stop with an error, or print a warning |
| `#pragma …` | Implementation-defined instruction to the compiler |
| `#line N "file"` | Change the reported line number and file name (used by code generators) |
| `__has_include(<file>)` *(C++17)* | In `#if`: is this header available? |

## Object-like and function-like macros

A macro is a name that the preprocessor replaces with a token sequence before the compiler sees it.

```cpp
#define BUFFER_SIZE 4096                 // object-like
#define SQUARE(x) ((x) * (x))            // function-like
```

Function-like macros are text substitution, not calls, so the argument is pasted in as written. The
three classic failures, all from one run (GCC 15, `-Wall -Wextra`):

```cpp title="macro_traps.cpp"
#include <iostream>
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define BAD_SQUARE(x) x * x
int main() {
    int x = 5;
    int m = MAX(x++, 10);
    std::cout << "m=" << m << " x=" << x << '\n';
    int y = 15;
    int n = MAX(y++, 10);
    std::cout << "n=" << n << " y=" << y << '\n';
    std::cout << BAD_SQUARE(2 + 3) << '\n';
}
```

```text
m=10 x=6
n=16 y=17
11
```

- **Missing parentheses.** `BAD_SQUARE(2 + 3)` expands to `2 + 3 * 2 + 3`, which is 11, not 25.
  Parenthesise every parameter and the whole body.
- **Double evaluation.** `MAX(y++, 10)` expands to `((y++) > (10) ? (y++) : (10))`. When `y` wins,
  `y++` runs twice: the result is 16 and `y` ends at 17. When `x` loses, it runs once. Parentheses
  cannot fix this.
- **No scope.** A macro is visible from its `#define` to the end of the translation unit, in every
  namespace and every header included after it. A header that defines `max` breaks `std::max`.

### Prefer language features

Every macro in this table has a replacement that is typed, scoped and visible in a debugger:

| Macro use | Replacement |
|---|---|
| `#define PI 3.14159` | `constexpr double pi = 3.14159;` (or `std::numbers::pi` *(C++20)*) |
| `#define SQUARE(x) ((x)*(x))` | `constexpr int square(int x) { return x * x; }` or a template |
| `#define MAX(a,b) …` | `std::max(a, b)` |
| `#ifdef` around a few lines of logic | `if constexpr (flag)` on a `constexpr bool` *(C++17)* |
| Header text pasted per TU | [Modules](./modules.md) *(C++20)* |

`if constexpr` only replaces the *branch*; it still needs a `constexpr bool` defined somewhere, and
both branches must be valid C++ that parses. Selecting between headers or platform APIs that do not
exist on the other platform still needs `#if`.

## Stringification and token pasting

Two operators work only inside a function-like macro body:

- `#param` turns the argument into a string literal, spelled as written.
- `a##b` glues two tokens into one, which can form a new identifier.

```cpp title="stringify.cpp"
#include <iostream>

#define STRINGIFY(x) #x
#define LOG(var) std::cout << #var << " = " << (var) << '\n'
#define CONCAT(a, b) a##b

int main() {
    int count = 42;
    int CONCAT(value, _tmp) = 7;      // declares value_tmp
    LOG(count);
    LOG(value_tmp * 2);
    std::cout << STRINGIFY(hello world) << '\n';
    std::cout << __FILE__ << ':' << __LINE__ << " in " << __func__ << '\n';
}
```

```text
count = 42
value_tmp * 2 = 14
hello world
stringify.cpp:13 in main
```

This is the one job macros do that nothing else can: capture the *source text* of an expression,
which is how `assert` prints the failed condition. Since C++20, `std::source_location` replaces the
`__FILE__`/`__LINE__` part without a macro.

## Conditional compilation

`#if` takes an integer constant expression over macros; undefined identifiers count as `0`.
`defined(NAME)` tests whether a macro exists. Code in a dropped branch is removed before the
compiler sees it, so it does not even have to compile.

```cpp title="config.cpp"
#include <iostream>

#ifndef NDEBUG
#define TRACE(msg) std::cerr << __FILE__ << ':' << __LINE__ << ": " << (msg) << '\n'
#else
#define TRACE(msg) ((void)0)
#endif

constexpr bool kVerbose =
#ifdef VERBOSE
    true;
#else
    false;
#endif

int main() {
    TRACE("starting");
    if constexpr (kVerbose) {
        std::cout << "verbose build\n";
    }
    std::cout << "done\n";
}
```

<Tabs groupId="build">
  <TabItem value="debug" label="g++ config.cpp">

```text
config.cpp:17: starting
done
```

  </TabItem>
  <TabItem value="release" label="g++ -DNDEBUG -DVERBOSE config.cpp">

```text
verbose build
done
```

  </TabItem>
</Tabs>

The pattern converts the macro into a `constexpr bool` once, at the top, so the rest of the code
uses an ordinary typed constant. `NDEBUG` is the standard switch: `<cassert>` disables `assert` when
it is defined, and build systems define it in release configurations
([CMake build types](../../cmake/01-basics/build-types.md)).

### Platform and feature detection

Compilers predefine macros that describe the target and the language level. The values below are
from `g++ -std=c++23 -dM -E` (GCC 15) and the same with Clang 21:

| Macro | GCC 15 | Clang 21 | Meaning |
|---|---|---|---|
| `__cplusplus` | `202302L` | `202302L` | Language standard selected by `-std` (`201703L` C++17, `202002L` C++20) |
| `__GNUC__` | `15` | `4` | GCC major version. Clang defines it as `4` for compatibility, so test `__clang__` first |
| `__clang_major__` | (undefined) | `21` | Clang major version |
| `__linux__`, `_WIN32`, `__APPLE__` | target OS | target OS | Operating system of the **target**, not the build machine |
| `__x86_64__`, `__aarch64__` | target CPU | target CPU | Architecture |
| `__cpp_concepts`, `__cpp_lib_print`, … | `202002L`, … | | Feature-test macros: test the feature, not the version |

Prefer feature-test macros over `__cplusplus` comparisons. Library macros such as `__cpp_lib_print`
are defined by the library headers, so include `<version>` *(C++20)* first.

```cpp
#include <version>
#if defined(__cpp_lib_print)
#include <print>          // use std::println
#else
#include <cstdio>         // fall back to printf
#endif
```

## `#pragma`

A pragma is a compiler-specific instruction. An unknown pragma is ignored (GCC warns with
`-Wunknown-pragmas`, part of `-Wall`), so they are not portable by construction.

| Pragma | Supported by | Effect |
|---|---|---|
| `#pragma once` | GCC, Clang, MSVC | Include this file at most once per TU: [Include Guards](./include-guards-and-pragma-once.md) |
| `#pragma pack(push, 1)` … `pop` | GCC, Clang, MSVC | Remove padding: `struct { char c; int i; }` becomes 5 bytes instead of 8 (checked with `static_assert` on GCC 15 x86-64). See [Padding](../12-low-level-and-platform/03-padding-and-offsetof.md) |
| `#pragma GCC diagnostic push/ignored "-W…"/pop` | GCC, Clang | Silence one warning in a region |
| `#pragma warning(push)` / `disable: N` / `pop` | MSVC | Same, MSVC syntax |
| `#pragma message("text")` | GCC, Clang, MSVC | Print a note during compilation |

`_Pragma("…")` is the operator form, usable inside a macro body where `#pragma` cannot appear.

## Pitfalls

- **A macro that names a common identifier.** `<windows.h>` defines `min` and `max` unless
  `NOMINMAX` is defined first; then `std::max(a, b)` stops compiling. Name macros in `UPPER_CASE`
  with a project prefix, and `#undef` local helpers when done.
- **Multi-statement macros without `do { … } while (0)`.** `#define SWAP(a,b) t=a; a=b; b=t;` under
  an un-braced `if` runs only the first statement conditionally. Wrap the body in
  `do { … } while (0)`, or better, write a function.
- **Testing a macro's value with `#ifdef`.** `#define DEBUG 0` makes `#ifdef DEBUG` *true*. Use
  `#if DEBUG` when the value matters.
- **Expecting a self-referential macro to loop.** `#define X Y` / `#define Y X` does not recurse: a
  macro is never re-expanded inside its own expansion, so `int X = 1;` preprocesses to
  `int X = 1;`. This is a confusing name, not an infinite loop.
- **Platform checks against the host.** `#ifdef __linux__` describes the target you compile for,
  which matters when [cross-compiling](./cross-compilation.md).

## Key points

- The preprocessor is text rewriting before parsing; `g++ -E` shows exactly what the compiler gets.
- Function-like macros paste arguments: parenthesise everything, and never pass side effects.
- Use macros for what only they can do: conditional compilation, platform detection, capturing
  source text. Use `constexpr`, templates and `if constexpr` for everything else.
- Detect features with `__cpp_*` macros after `#include <version>`, not with compiler versions.

## References

- [cppreference: Preprocessor](https://en.cppreference.com/w/cpp/preprocessor)
- [GCC: Preprocessor Options](https://gcc.gnu.org/onlinedocs/gcc/Preprocessor-Options.html)
