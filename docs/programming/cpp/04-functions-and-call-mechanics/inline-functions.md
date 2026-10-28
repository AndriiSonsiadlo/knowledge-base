---
id: inline-functions
title: Inline Functions
sidebar_label: Inline
sidebar_position: 4
tags: [c++, functions, inline, optimization, odr]
---

# Inline Functions

The `inline` keyword has two meanings that people mix up. Its **language meaning**, the one the
standard guarantees, is about linkage: an inline function (or *(C++17)* variable) may be *defined* in
every translation unit that uses it, which is what lets you put a definition in a header. Its
**optimization meaning**, replacing a call with the function body, is only a hint, and modern
compilers mostly ignore it in favour of their own heuristics. This page separates the two.

**Prerequisites:** [Translation Units](../01-toolchain-and-build/translation-units.md) and the
[One Definition Rule](../01-toolchain-and-build/linking.md#one-definition-rule-odr), which this page
builds on rather than repeats. [Function Declarations](./function-declarations.md) for
declaration versus definition.

<Diagram title="Two things called inline" accent="green">
  <DiagramRow>
    <DiagramNode title="Language rule (guaranteed)" accent>The function may be defined in many translation units. All definitions must be identical; the linker keeps one.</DiagramNode>
    <DiagramNode title="Inlining (optimization)" dashed>Replace a call with the body. Decided by the optimizer for any function whose body it can see, keyword or not.</DiagramNode>
  </DiagramRow>
</Diagram>

## The ODR meaning: definitions in headers

The ODR allows only one definition of a non-inline function in the whole program. Put that definition
in a header included by two `.cpp` files and each object file gets a copy:

```cpp title="util.h"
#pragma once
int square(int x) { return x * x; }   // no inline
```

```cpp title="a.cpp"
#include "util.h"
int a() { return square(2); }
```

```cpp title="main.cpp"
#include "util.h"
int a();
int main() { return square(3) + a(); }
```

```text
$ g++ -std=c++23 a.cpp main.cpp -o app
ld: main.cpp:(.text+0x0): multiple definition of `square(int)'; a.cpp:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

Write `inline int square(int x)` and the program links and exits with 13. The compiler now emits
`square` as a **weak** symbol in a mergeable section. `nm` shows the difference:

```text
$ nm -C a.o | grep square
0000000000000000 W square(int)     # W = weak; without inline it is T, a strong definition
```

<Diagram title="How an inline function survives linking" caption="Each translation unit emits its own copy; the linker keeps one and discards the rest." accent="green">
  <DiagramRow>
    <DiagramNode icon="file-text" title="a.o">weak `square(int)`</DiagramNode>
    <DiagramNode icon="file-text" title="main.o">weak `square(int)`</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="link" />
  <DiagramNode icon="binary" title="app" accent>one `square(int)`, every call and `&square` refer to it</DiagramNode>
</Diagram>

The price of this permission is a promise: **every definition must be token-for-token identical and
mean the same thing.** The linker does not check it. If two translation units see different
definitions (say a macro changes the body), the program is ill-formed, no diagnostic required, and the
linker silently picks one copy. An inline function still has a single address in the program, and its
`static` local variables are shared by all translation units.

### What is implicitly inline

You rarely write `inline` on functions, because the common header-defined cases are already inline:

- Member functions **defined inside the class body**, including friends defined there.
- `constexpr` functions *(C++11)* and `consteval` functions *(C++20)*.
- Deleted functions (`= delete`).
- *(C++17)* `static constexpr` data members.

Function **templates are not implicitly inline**. They may also appear in headers, but under a
separate ODR provision for templates. A full specialization of a function template is an ordinary
function and needs `inline` if it is defined in a header.

*(C++20)* Inside a [named module](../01-toolchain-and-build/modules.md), a member function defined in
the class body is no longer implicitly inline. Modules don't need the header permission, and this lets
the module's interface keep the body private to its own compilation.

## Inline variables *(C++17)*

The same rule applies to variables. Before C++17, a global shared through a header needed an `extern`
declaration in the header and one definition in a `.cpp` file. Now the header can define it:

```cpp title="config.h"
#pragma once
#include <string>

inline int request_count = 0;                    // one object shared by every TU
inline const std::string default_host = "localhost";

struct Limits {
    static constexpr int max_users = 100;        // implicitly inline (C++17)
    static inline int created = 0;               // non-const static member defined in-class
};
```

Without `inline`, `const` namespace-scope variables have internal linkage, so each translation unit
would get its *own* copy, which is a different and sometimes surprising result.

## The optimization meaning: inlining

**Inlining** replaces a call with a copy of the callee's body. It removes the call itself, but the
bigger win is that the optimizer can then simplify the body in context (constant-fold arguments,
drop dead branches). The cost is code size, since every inlined call site gets its own copy.

The keyword doesn't control it. At `-O2` GCC inlines small functions whose body it can see whether
they are marked `inline` or not. Here neither function says `inline`; one is inlined, the other is
stopped with an attribute:

```cpp title="inl.cpp" showLineNumbers
static int square(int x) { return x * x; }          // no inline keyword
[[gnu::noinline]] int cube(int x) { return x * x * x; }

int use(int n) { return square(n) + cube(n); }
```

GCC 15.2, `g++ -std=c++23 -O2 -S -masm=intel` (directives removed):

```nasm
_Z3usei:
    call  _Z4cubei        ; cube: still a call, noinline forbids inlining
    mov   edx, edi
    imul  edx, edi        ; square(n) inlined: n * n, no call
    add   eax, edx
    ret
```

At `-O0` the same file has two `call` instructions and nothing is inlined.

What decides it is visibility of the body and the optimizer's cost model. A function defined in
another `.cpp` file can't be inlined at all unless you enable link-time optimization (`-flto`), which
lets the optimizer see across files.

### Controlling it when you must

| Intent | GCC / Clang | MSVC |
|---|---|---|
| Always inline (error/warning if impossible) | `[[gnu::always_inline]] inline` | `__forceinline` |
| Never inline | `[[gnu::noinline]]` | `__declspec(noinline)` |

Use these for measured hot spots or to keep a function visible in profiles and backtraces, not as a
default. Inlined frames don't appear as separate calls in a stack trace unless the debugger
reconstructs them from debug info (GDB does this with `-g`).

## Common mistakes

- **Using `inline` as a speed annotation.** It doesn't make a call faster, and leaving it off doesn't
  stop inlining. Use it when a definition has to live in a header.
- **Defining a non-inline function in a header.** Works while one `.cpp` includes it, then fails with
  "multiple definition" the day a second one does.
- **Different inline definitions in different TUs.** A macro or `#ifdef` that changes the body per file
  is an ODR violation the linker won't report; one version silently wins.
- **"Virtual or recursive functions can't be inlined."** Not quite. A virtual call is inlined when the
  compiler can prove the dynamic type (devirtualization), and compilers can inline a few levels of a
  recursive call. Through an unknown base pointer, a virtual call stays a call.
- **Expecting a `static` local in an inline function to be per-file.** There is one object for the
  whole program. (A `static` *non-member* function is the opposite: each TU gets its own copy.)

## Key points

- `inline` means "may be defined in several translation units"; the definitions must be identical.
- Use it for functions and *(C++17)* variables defined in headers; class-body members and `constexpr`
  functions already have it.
- Function templates are not implicitly inline, but they may be defined in headers anyway.
- Whether a call is actually inlined is the optimizer's choice; the keyword barely affects it.
- Cross-file inlining needs the body visible: a header definition or `-flto`.
