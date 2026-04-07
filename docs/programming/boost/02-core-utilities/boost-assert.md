---
id: boost-assert
title: Boost.Assert
sidebar_label: Boost.Assert
sidebar_position: 3
tags: [ c++, boost, assert, diagnostics ]
---

# Boost.Assert

Boost.Assert is a tiny header-only library that replaces the C standard `assert` macro with a more
flexible, more informative, and *customisable* family of macros. It is one of the very few dependencies
that [Boost.Core](./boost-core.md) itself allows, which tells you how foundational it is: Boost code
sprinkles `BOOST_ASSERT` everywhere to document and enforce its own invariants.

:::info Why not just use `<cassert>`?
The C `assert` macro is rigid. It is controlled only by the global `NDEBUG` switch, it always aborts,
and you cannot intercept a failure to log it, throw, or break into a debugger gracefully. Boost.Assert
keeps the familiar syntax but lets you control *all* of that per-translation-unit.
:::

## The core macros

```cpp showLineNumbers title="assert_basics.cpp"
#include <boost/assert.hpp>

int divide(int a, int b) {
    BOOST_ASSERT(b != 0);                       // invariant check
    BOOST_ASSERT_MSG(b != 0, "divisor is zero"); // with a message
    return a / b;
}
```

- **`BOOST_ASSERT(expr)`** — like `assert(expr)`: checks a condition in debug builds.
- **`BOOST_ASSERT_MSG(expr, msg)`** — same, but attaches an explanatory message to the failure.
- **`BOOST_VERIFY(expr)`** — evaluates `expr` **even when assertions are disabled**, only skipping the
  *check*. Use it when the expression has a side effect you still need.

```cpp showLineNumbers
#include <boost/assert.hpp>

void f() {
    // The lock must actually be taken even in release builds;
    // only the success *check* is compiled out when assertions are off.
    BOOST_VERIFY(try_lock() == true);
}
```

:::warning BOOST_ASSERT vs BOOST_VERIFY
`BOOST_ASSERT(expr)` may compile `expr` *away entirely* when assertions are disabled. Never put a
required side effect inside it — if `do_work()` matters, use `BOOST_VERIFY(do_work())`, not
`BOOST_ASSERT(do_work())`.
:::

## How it differs from `<cassert>`

| Aspect | C `assert` | `BOOST_ASSERT` |
|--------|-----------|-----------------|
| Disable switch | `NDEBUG` only | `BOOST_DISABLE_ASSERTS` / `NDEBUG`, per TU |
| On failure | always `abort()` | calls a user-replaceable handler |
| Custom message | no | `BOOST_ASSERT_MSG` |
| Side-effecting check | no equivalent | `BOOST_VERIFY` |
| Force-disable detection | no | `BOOST_ASSERT_IS_VOID` |

By default, with neither `NDEBUG` nor any Boost macro set, `BOOST_ASSERT` behaves *exactly* like the C
`assert` — it forwards to it. The power comes from the switches you can flip.

## Customising the failure handler

Define `BOOST_ENABLE_ASSERT_HANDLER` before including the header, and Boost.Assert will route failures
to two functions **you** implement: `boost::assertion_failed` and `boost::assertion_failed_msg`. This
lets you log, throw, record telemetry, or trap into a debugger instead of aborting.

```cpp showLineNumbers title="custom_handler.cpp"
#define BOOST_ENABLE_ASSERT_HANDLER
#include <boost/assert.hpp>
#include <iostream>
#include <stdexcept>

namespace boost {
void assertion_failed(char const* expr, char const* function,
                      char const* file, long line) {
    std::cerr << "assert failed: " << expr
              << " in " << function
              << " at " << file << ':' << line << '\n';
    throw std::logic_error(expr);   // turn a broken invariant into an exception
}

void assertion_failed_msg(char const* expr, char const* msg,
                          char const* function, char const* file, long line) {
    std::cerr << "assert failed: " << expr << " -- " << msg
              << " in " << function
              << " at " << file << ':' << line << '\n';
    throw std::logic_error(msg);
}
} // namespace boost
```

:::tip One handler, whole program
The handler is an ordinary function with external linkage, so defining it once in a single `.cpp` file
changes the behaviour of every `BOOST_ASSERT` in your program that was compiled with
`BOOST_ENABLE_ASSERT_HANDLER`. This is a clean way to make a long-running service log and recover
instead of crashing.
:::

## BOOST_ASSERT_IS_VOID and current_function

`BOOST_ASSERT_IS_VOID` is defined whenever assertions are *disabled*. It lets you compile out code that
exists only to support an assertion — for example an expensive `is_valid()` helper used nowhere else.

```cpp showLineNumbers
#include <boost/assert.hpp>

void process(const Buffer& b) {
#if !defined(BOOST_ASSERT_IS_VOID)
    // Only build this validation helper when asserts are live.
    const bool ok = expensive_consistency_check(b);
    BOOST_ASSERT(ok);
#endif
    do_work(b);
}
```

The companion header `<boost/current_function.hpp>` defines `BOOST_CURRENT_FUNCTION`, a portable macro
expanding to the enclosing function's name (the best of `__func__`, `__PRETTY_FUNCTION__`, or
`__FUNCSIG__` available on your compiler). This is exactly what the assertion handler receives as its
`function` argument, and it is useful in your own logging too.

## Assertions versus contracts

An assertion documents a **programmer error** — a precondition or invariant that should *never* be
false if the code is correct. It is not error handling.

:::danger Do not validate untrusted input with assertions
If a condition can legitimately be false at runtime (malformed user input, a missing file, a network
timeout), throw an exception or return an error — do **not** assert. Assertions can be compiled out, so
relying on them for real validation means the check vanishes in release builds, which can become a
security or correctness hole.
:::

Contract-checking proposals for C++ generalise this idea with first-class preconditions,
postconditions, and invariants. Until contracts land in the standard, the Boost.Assert family — and the
related Boost.Contract library — are the practical way to express the same intent. For everyday
"this should be impossible" checks, `BOOST_ASSERT` is the right, lightweight tool.

## See also

- <Icon icon="lucide:wrench" inline /> [Boost.Core](./boost-core.md) — the foundation that depends on Boost.Assert.
- <Icon icon="lucide:bug" inline /> [Boost.Optional](./boost-optional.md) — a safer way to model "maybe no value" than asserting on a sentinel.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — where contracts and `std` diagnostics are heading.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
