---
id: boost-preprocessor
title: Boost.Preprocessor
sidebar_label: Boost.Preprocessor
sidebar_position: 1
tags: [ c++, boost, metaprogramming ]
---

# Boost.Preprocessor

Boost.Preprocessor is a header-only library that turns the C preprocessor — a blunt text-substitution
tool most C++ developers use only for `#include` and the occasional macro — into a small, Turing-ish
metaprogramming engine. It provides data structures (sequences, tuples, lists, arrays), control
constructs (repetition, iteration, conditionals), and the two primitive operations every preprocessor
trick is built on: token pasting and stringizing.

:::info Why a preprocessor metaprogramming library?
Templates run at compile time but operate on **types and values**. The preprocessor runs *earlier*,
operating on **raw tokens** before the compiler ever parses them. That makes it the only tool that can
mechanically generate *source code itself* — repeated function overloads, enum-to-string tables,
boilerplate registration — from a single declarative description.
:::

## What preprocessor metaprogramming is

A normal macro expands once. Boost.Preprocessor lets a macro expand *based on data* and *repeat itself
a controlled number of times*, all during the preprocessing pass. Because it works on tokens, it can
produce constructs that templates cannot — for example, generating ten distinct function signatures
each with a different arity.

Historically this mattered enormously. Before C++11 gave us **variadic templates**, libraries like
Boost.Function, Boost.Bind, and Boost.Tuple supported "0 to N arguments" by *preprocessing the same
header N times*, once per arity. Boost.Preprocessor was the machinery that made that practical.

```mermaid
flowchart LR
    SRC[Source with BOOST_PP macros] --> PP[Preprocessor pass]
    PP --> GEN[Expanded C++ tokens]
    GEN --> C[Compiler / templates]
    C --> OBJ[Object code]
```

## The data structures

The library models several "container" forms purely as token sequences. You rarely need all of them;
**sequences** and **tuples** cover most real code.

| Structure | Literal form | Notes |
|-----------|--------------|-------|
| Tuple | `(a, b, c)` | Fixed, comma-separated; fast random access by index |
| Sequence (seq) | `(a)(b)(c)` | The workhorse; easy to append and iterate |
| List | `(a, (b, (c, BOOST_PP_NIL)))` | Cons-cell style; mostly legacy |
| Array | `(3, (a, b, c))` | A size paired with a tuple |

```cpp showLineNumbers title="data_structures.cpp"
#include <boost/preprocessor/seq/elem.hpp>
#include <boost/preprocessor/seq/size.hpp>
#include <boost/preprocessor/tuple/elem.hpp>

#define COLORS (red)(green)(blue)

// Random access into a seq and a tuple, fully resolved before compilation:
static const char* k0 = BOOST_PP_STRINGIZE(BOOST_PP_SEQ_ELEM(0, COLORS)); // "red"
static const int   n  = BOOST_PP_SEQ_SIZE(COLORS);                        // 3
static const char* t1 = BOOST_PP_STRINGIZE(BOOST_PP_TUPLE_ELEM(1, (x, y, z))); // "y"
```

## The two primitives: CAT and STRINGIZE

Almost every higher-level macro decomposes into token pasting (`BOOST_PP_CAT`) and stringizing
(`BOOST_PP_STRINGIZE`). The Boost versions exist because the raw `##` and `#` operators do **not**
expand their arguments first — a classic foot-gun. `BOOST_PP_CAT` forces an extra expansion pass so
that macro arguments are evaluated before they are joined.

```cpp showLineNumbers title="cat_stringize.cpp"
#include <boost/preprocessor/cat.hpp>
#include <boost/preprocessor/stringize.hpp>

#define VERSION 3

// Raw ## would paste "var" + "VERSION" -> varVERSION (no expansion).
int BOOST_PP_CAT(var, VERSION) = 0;            // declares: int var3 = 0;

const char* tag = BOOST_PP_STRINGIZE(VERSION); // yields "3", not "VERSION"
```

:::tip Prefer the Boost macros over raw `#`/`##`
If you ever find that `name ## SUFFIX` produced literally `nameSUFFIX` instead of the value of
`SUFFIX`, reach for `BOOST_PP_CAT`. The double-expansion behaviour is exactly what you almost always
want.
:::

## Repetition: BOOST_PP_REPEAT and BOOST_PP_ENUM

`BOOST_PP_REPEAT(count, macro, data)` invokes `macro(z, n, data)` for `n` in `[0, count)`. This is the
core code-generation primitive. `BOOST_PP_ENUM` is similar but inserts commas between expansions —
ideal for parameter lists.

```cpp showLineNumbers title="repeat.cpp"
#include <boost/preprocessor/repetition/repeat.hpp>
#include <boost/preprocessor/repetition/enum.hpp>
#include <boost/preprocessor/repetition/enum_params.hpp>

// Generate: T0 a0; T1 a1; T2 a2;
#define DECL(z, n, _) BOOST_PP_CAT(T, n) BOOST_PP_CAT(a, n);
struct Holder {
    BOOST_PP_REPEAT(3, DECL, ~)
};
#undef DECL

// Generate a comma-separated parameter pack: int a0, int a1, int a2
#define PARAM(z, n, type) type BOOST_PP_CAT(a, n)
void take(BOOST_PP_ENUM(3, PARAM, int)) { }
#undef PARAM

// BOOST_PP_ENUM_PARAMS is a shorthand for "p0, p1, p2"
template <BOOST_PP_ENUM_PARAMS(3, class T)>   // template <class T0, class T1, class T2>
struct Triple { };
```

The `z` parameter threaded through these macros is the "repetition dimension." It lets repetitions
nest without colliding; for non-nested code you pass it straight through and otherwise ignore it.

## The classic use case: variadic-style overloads pre-C++11

The motivating example for the whole library is generating a family of overloads that differ only in
arity. This is how pre-C++11 Boost emulated variadic templates. Here is a miniature `make`-style
factory generated for 1..4 constructor arguments:

```cpp showLineNumbers title="gen_overloads.cpp"
#include <boost/preprocessor/repetition/repeat_from_to.hpp>
#include <boost/preprocessor/repetition/enum_params.hpp>
#include <boost/preprocessor/repetition/enum_binary_params.hpp>
#include <boost/preprocessor/arithmetic/inc.hpp>

template <class T> struct Widget { /* ... */ };

// For arity n, emit:
//   template <class T0, ... > Widget<...> make(T0 const& a0, ...) { ... }
#define MAKE_OVERLOAD(z, n, _)                                              \
    template <BOOST_PP_ENUM_PARAMS(BOOST_PP_INC(n), class T)>               \
    auto make(BOOST_PP_ENUM_BINARY_PARAMS(BOOST_PP_INC(n), T, const& a))    \
    { return /* construct from a0..aN */ 0; }

BOOST_PP_REPEAT_FROM_TO(0, 4, MAKE_OVERLOAD, ~)   // generates arities 1..4
#undef MAKE_OVERLOAD
```

:::note This is what variadic templates replaced
In C++11 and later you would write a single `template <class... Ts> auto make(Ts const&... args)`.
The preprocessor approach above only exists because that language feature did not. If you target
C++11+, prefer the variadic template — it is shorter, debuggable, and not capped at an arbitrary
`N`.
:::

## Iterating over data with a horizontal/vertical fold

`BOOST_PP_SEQ_FOR_EACH` walks a sequence and applies a macro to each element — perfect for turning a
single list of names into parallel tables. A common, genuinely useful pattern is generating an
enum together with its stringized names:

```cpp showLineNumbers title="enum_to_string.cpp"
#include <boost/preprocessor/seq/for_each.hpp>
#include <boost/preprocessor/seq/enum.hpp>
#include <boost/preprocessor/stringize.hpp>

#define STATES (Idle)(Running)(Paused)(Stopped)

enum class State { BOOST_PP_SEQ_ENUM(STATES) };   // enum class State { Idle, Running, ... };

#define NAME_CASE(r, _, st) case State::st: return BOOST_PP_STRINGIZE(st);
const char* to_string(State s) {
    switch (s) {
        BOOST_PP_SEQ_FOR_EACH(NAME_CASE, ~, STATES)
    }
    return "?";
}
#undef NAME_CASE
```

Adding a new state now means editing exactly one line (`STATES`); the enum *and* its `to_string` stay
in sync automatically. This "single source of truth" property is the strongest argument for the
library in modern code.

## Real-world use cases

- **Enum / name tables and reflection-lite registration** (as above) where keeping declarations and
  metadata in sync by hand is error-prone.
- **X-macro replacement** — a cleaner, composable alternative to the old `#define X(...)` include
  trick.
- **Testing matrices** — generating many similar test cases or type-parameterised checks.
- **Library back-compat shims** — supporting both pre- and post-variadic toolchains from one header.

## When NOT to use it

Boost.Preprocessor is powerful but it operates *beneath* the type system, so the compiler cannot help
you when something goes wrong. Reach for a modern language feature first:

| Goal | Prefer this instead of BOOST_PP |
|------|---------------------------------|
| Variable arity functions | Variadic templates (`Ts...`) |
| Compile-time computation | `constexpr` / `consteval` functions |
| Type lists / type manipulation | Templates, `std::tuple`, fold expressions |
| A handful of similar values | Just write them out, or a normal `constexpr` array |

:::warning Debuggability is the real cost
Preprocessor errors are notoriously opaque: a single mistake expands into a wall of unrelated tokens,
and stepping through generated code in a debugger shows you machine-expanded source you never wrote.
Use `g++ -E` (or `clang++ -E`) to inspect the expansion when diagnosing problems, and keep BOOST_PP
to the smallest surface that solves the problem.
:::

:::danger Recursion and reentrancy limits
The preprocessor cannot truly recurse. Boost.Preprocessor fakes recursion with a fixed pool of
expansion "states," so a macro that re-enters itself (for example, calling `BOOST_PP_REPEAT` inside
another `BOOST_PP_REPEAT` without using the `z`/`d` dimension parameters) silently fails to expand.
Respect the dimension arguments, and do not assume unlimited depth.
:::

## See also

- <Icon icon="lucide:sigma" inline /> [Boost.MPL](../07-functional-and-metaprogramming/boost-mpl.md) — type-level metaprogramming that often pairs with BOOST_PP.
- <Icon icon="lucide:puzzle" inline /> [Boost.Config](../01-build-and-integration/boost-config.md) — portability macros that lean on the preprocessor.
- <Icon icon="lucide:book-open" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — why variadic templates superseded much of this.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost overview](../readme.md).
