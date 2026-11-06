---
id: assertions
title: Assertions and static_assert
sidebar_label: Assertions
sidebar_position: 4
tags: [cpp, assertions, assert, static-assert, ndebug, preconditions]
---

# Assertions and static_assert

An **assertion** states something that must be true if the program is correct. If it is false, the
program has a bug, and the right response is to stop loudly at the point of the mistake rather than
continue with corrupt state. C++ has two built-in mechanisms: `static_assert`, checked at compile
time, and the `assert` macro, checked at run time and removable. Assertions are for *programmer
errors*. Failures that can happen in a correct program (bad input, a missing file) belong to
[exceptions](./01-exceptions.md) or [error codes](./03-error-codes.md). C++26 proposes language-level
[contracts](./05-contracts.md) that cover the same ground; this page is about what exists today in
every compiler.

**Prerequisites:** [Exceptions](./01-exceptions.md) for the contrast between bugs and expected failures.

## static_assert: compile-time checks

`static_assert(constant-expression, message)` *(C++11)* fails compilation when the expression is
false. It costs nothing at run time and works in any scope, including inside templates, where the
check happens at instantiation. The message must be a string literal in C++11/14; it is optional since
C++17.

```cpp title="static_assert.cpp" showLineNumbers
#include <cstdint>
#include <type_traits>

struct Header { std::uint32_t magic; std::uint16_t version; std::uint16_t flags; };
static_assert(sizeof(Header) == 8, "Header must be 8 bytes");   // layout assumption
static_assert(std::is_trivially_copyable_v<Header>);            // message optional since C++17

template <class T>
T twice(T x) {
    static_assert(std::is_arithmetic_v<T>, "twice() needs an arithmetic type");
    return x + x;
}
int main() { return twice(2) - 4; }
```

This compiles with no warnings under `g++ -std=c++20 -Wall -Wextra` and clang++. Calling
`twice(std::true_type{})` fails with
`error: static assertion failed: twice() needs an arithmetic type`
(g++ 15.2), usually followed by unrelated follow-on errors.

Use it for assumptions the build must guarantee: sizes and alignments of types that cross a file or
network boundary, `std::is_*` properties a template relies on, enum-count checks. In C++20, prefer a
[concept](../08-templates-and-metaprogramming/concepts-and-requires.md) when the check should be part of
the function's interface and take part in overload resolution; use `static_assert` when you want a
hard error with a custom message after overload resolution has chosen.

Before CWG2518 / P2593R1 (a defect report applied to all standard versions since C++11; GCC 13+ and
Clang 17+ implement it), compilers rejected `static_assert(false, "...")` even in a template branch
that is never instantiated. On older toolchains make the condition depend on a template parameter,
for example `static_assert(sizeof(T) == 0, "unsupported T")`.

## assert: run-time checks

`assert(expr)` is a macro from `<cassert>`. If the macro `NDEBUG` is **not** defined when `<cassert>` is
included, it evaluates `expr` and, when false, prints a diagnostic (the expression, file, line,
and usually the function) to `stderr` and calls `std::abort()`. If `NDEBUG` is defined, it expands to
`((void)0)`: **the expression is not evaluated at all.**

```cpp title="assert.cpp" showLineNumbers
#include <cassert>
#include <cstdio>

int calls = 0;
bool tick() { ++calls; return true; }

int main() {
    assert(tick());                         // BUG: the side effect vanishes under -DNDEBUG
    std::printf("calls=%d\n", calls);
}
```

```text
$ g++ -std=c++20 -O2 assert.cpp && ./a.out
calls=1
$ g++ -std=c++20 -O2 -DNDEBUG assert.cpp && ./a.out
calls=0
```

Same on g++ 15.2 and clang++ 21.1. Typical build systems define `NDEBUG` in release configurations
(CMake's `Release` and `RelWithDebInfo`), so a release build silently drops every check.

A failed assertion looks like this (the format is the C library's, here glibc, and differs elsewhere):

```text
f: fail.cpp:2: int main(): Assertion `x == 4 && "x must be 4"' failed.
Aborted (core dumped)
```

The `&& "message"` idiom puts a human explanation into that text, because a non-empty string literal is
always true.

### Pitfalls

- **Side effects inside `assert`.** Never put work in the expression (`assert(close(fd) == 0)`).
- **Commas outside parentheses.** `assert(std::is_same<int, int>::value)` fails to compile before C++26
  because the preprocessor sees two macro arguments (g++ 15.2 with glibc: "macro 'assert' passed 2
  arguments, but takes just 1"). Add parentheses. C++26 makes `assert` variadic.
- **`assert` is usable in constant expressions**: while the condition holds it has no effect, and a failure
  makes the evaluation non-constant, which is a compile error (per LWG 2234, applied to C++11).
- **Using it to validate input.** Anything an external caller can trigger must be handled in release
  builds too.
- **Silent undefined behavior after removal.** Code written as `assert(p != nullptr); *p = 1;` becomes an
  unchecked dereference in release builds. See [Undefined Behavior](./06-undefined-behavior.md).

## What to assert

Assert conditions that are the caller's or your own responsibility, never environmental ones.

| Kind | Meaning | Example |
|---|---|---|
| Precondition | What the caller must guarantee on entry | `assert(!v.empty());` in `front_or_die` |
| Postcondition | What the function guarantees on exit | `assert(is_sorted(out.begin(), out.end()));` |
| Invariant | What always holds for an object or loop | `assert(size_ <= capacity_);` |
| Unreachable | A branch that cannot happen | `default: assert(false && "bad enum");` |

Checks that are themselves expensive (an `is_sorted` over a million elements) change the complexity of
the function in debug builds. Keep them for debug or use a project-level level switch.

Standard library hardening is a related but distinct mechanism: libstdc++ `-D_GLIBCXX_ASSERTIONS` and
libc++ hardening modes add precondition checks (such as `operator[]` bounds) to the library and abort on
violation. Their exact coverage is implementation-specific; see your library's documentation.

For paths the compiler may be told are unreachable, C++23 provides `std::unreachable()` in `<utility>`.
Unlike `assert(false)` it is *undefined behavior* if reached, in every build, so use it only after the
guard is proven.

## Custom assertion macros

A project often wraps `assert` to keep checks in some builds (release with logging), print more, or
route to a crash reporter. Keep these rules: evaluate the expression exactly once, wrap the macro body
in `do { ... } while (0)`, and stringify with `#expr`.

```cpp showLineNumbers
// ...  (fragment)
#include <cstdio>
#include <cstdlib>

#define MY_ASSERT(expr)                                                      \
    do {                                                                     \
        if (!(expr)) {                                                       \
            std::fprintf(stderr, "%s:%d: assertion failed: %s\n",            \
                         __FILE__, __LINE__, #expr);                         \
            std::abort();                                                    \
        }                                                                    \
    } while (0)
```

C++20's `std::source_location` can replace `__FILE__`/`__LINE__` in a function, but not the stringified
expression, so a macro is still needed to capture it. Contracts, proposed for C++26 (status unsettled, see [Contracts](./05-contracts.md)), would remove this need.

## assert versus exceptions

| | `assert` | Exception / error code |
|---|---|---|
| Detects | Bugs in the program | Conditions a correct program can face |
| Release builds | Usually removed | Always active |
| Recoverable | No, it aborts | Yes |
| Caller can test for it | No | Yes |

An exception for a precondition violation lets tests observe it, but invites callers to catch and
ignore a bug and requires the function to be non-`noexcept`; many codebases choose assert-and-abort
instead. Whichever you pick, state the rule in the function's documentation.

## Key points

- `static_assert` is free, compile-time, and ideal for layout and type assumptions. The message is
  optional from C++17.
- `assert` aborts on failure and is removed entirely, with its argument unevaluated, under `NDEBUG`.
- Never rely on side effects in an assertion, and never use assertions for run-time input errors.
- Parenthesize commas in `assert` arguments until C++26.
- Contracts, proposed for C++26 (status unsettled), may eventually replace ad hoc macros; see [Contracts](./05-contracts.md).
