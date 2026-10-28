---
id: noexcept
title: noexcept Specifier
sidebar_label: noexcept
sidebar_position: 6
tags: [c++, noexcept, exceptions, cpp11, cpp17]
---

# noexcept Specifier

`noexcept` does two jobs. As a **specifier** on a function (`void f() noexcept`) it promises that no
exception leaves the function, and the language enforces that promise by calling `std::terminate` if
one tries. As an **operator** (`noexcept(expr)`) it asks the compiler, at compile time, whether an
expression is declared not to throw. Generic code combines the two, and the standard library uses the
answer to choose between moving and copying. This page covers the mechanics. Why a non-throwing
commit step makes the strong exception guarantee possible is on
[Exception Safety and the Strong Guarantee](../10-error-handling-and-safety/02-noexcept-and-strong-guarantee.md).

**Prerequisites:** [Exceptions](../10-error-handling-and-safety/01-exceptions.md),
[Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## The specifier

```cpp showLineNumbers
// ...
void a() noexcept;                // non-throwing
void b() noexcept(true);          // same as a
void c() noexcept(false);         // potentially throwing, same as no specifier
void d();                         // potentially throwing

template <class T>
void e(T& x) noexcept(std::is_nothrow_move_constructible_v<T>);   // conditional
```

The argument of `noexcept(...)` must be a constant expression convertible to `bool`. `noexcept` is not
a static check: the compiler doesn't verify that the body can't throw. It only changes what happens
if an exception reaches the function's boundary.

*(C++17)* The exception specification is **part of the function type**. A pointer to a `noexcept`
function converts to a plain function pointer, but not the other way round, and `void(*)() noexcept`
and `void(*)()` are distinct types. You still can't overload on `noexcept` alone.

## What happens when the promise is broken

```cpp title="terminate.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>

void parse() { throw std::runtime_error("bad input"); }
void load() noexcept { parse(); }        // compiles: nothing checks the body

int main() {
    try { load(); }
    catch (const std::exception&) { std::puts("caught"); }   // never runs
}
```

```text
$ g++ -std=c++23 terminate.cpp -o terminate && ./terminate
terminate called after throwing an instance of 'std::runtime_error'
  what():  bad input
Aborted (core dumped)        # exit status 134
```

<Walkthrough title="An exception meets a noexcept boundary" caption="Unwinding searches outward for a handler; a noexcept frame ends the search." accent="violet">
  <Step title="throw in parse()">

`parse()` throws `std::runtime_error`. The runtime starts looking for a matching handler in the
frames above: <StepChange>`parse` → `load` → `main`</StepChange>.

  </Step>
  <Step title="Reach load()">

`load` is `noexcept`. The search reaches its boundary before it ever gets to `main`'s `try` block.
<StepChange>The exception may not leave this frame.</StepChange>

  </Step>
  <Step title="std::terminate">

The runtime calls <StepChange>`std::terminate()`</StepChange>, which by default calls `std::abort`.
The `catch` in `main` never runs. Whether `parse`'s frame was unwound (its destructors run) before
terminating is implementation-defined, so don't rely on cleanup happening.

  </Step>
</Walkthrough>

This is why the compiler can generate less exception-handling code around calls to `noexcept`
functions: callers don't need to prepare for an exception coming out of them. How much that saves
depends on the code and platform; measure before claiming a speedup.

## The noexcept operator

`noexcept(expr)` is a compile-time `bool`: `false` if `expr` contains a call to a potentially throwing
function, a `throw`, or a `dynamic_cast` to a reference that could throw, and `true` otherwise. The
expression isn't evaluated.

```cpp title="operator.cpp" showLineNumbers
#include <string>
#include <type_traits>
#include <vector>

void f() noexcept;
void g();

static_assert(noexcept(f()));
static_assert(!noexcept(g()));
static_assert(noexcept(1 + 2));
static_assert(!noexcept(std::string("hello")));              // may allocate
static_assert(std::is_nothrow_move_constructible_v<std::string>);

std::vector<int> v(1);
static_assert(noexcept(v.size()));
static_assert(noexcept(v[0]));      // libstdc++ marks operator[] noexcept; the standard doesn't require it
static_assert(!noexcept(v.at(0)));  // at() throws std::out_of_range

int main() {}
void f() noexcept {}
void g() {}
```

Combining specifier and operator gives **conditional `noexcept`**: "I don't throw if the operations I
use don't throw". The doubled keyword is not a typo; the inner one is the operator:

```cpp showLineNumbers
// ...
template <class T>
class Wrapper {
    T value_;
public:
    void swap(Wrapper& other) noexcept(noexcept(std::swap(value_, other.value_))) {
        std::swap(value_, other.value_);
    }
};
```

For the common cases, the `std::is_nothrow_*` traits in `<type_traits>` read better than a raw
operator.

## What is noexcept without saying so

- **Destructors**, unless a base or member destructor is potentially throwing, or you write
  `noexcept(false)`.
- **Implicitly declared or `= default` special members** (constructors, assignments) are `noexcept`
  exactly when the operations they call on bases and members are.
- `operator delete` and the global deallocation functions.

Everything else, including your own move constructor written by hand, is potentially throwing unless
you mark it.

## Why move operations should be noexcept \{#move-semantics-and-noexcept\}

When `std::vector` grows it has to transfer its elements to new storage. If it moved them and a move
threw halfway, the old buffer would already be partly hollowed out, and `push_back` could no longer
promise to leave the vector unchanged. So it uses `std::move_if_noexcept`: it moves only if the move
constructor is `noexcept` (or the type can't be copied), and **copies** otherwise.

```cpp title="grow.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct Loud {
    std::string s = "x";
    Loud() = default;
    Loud(const Loud& o) : s(o.s) { std::puts("copy"); }
    Loud(Loud&& o) : s(std::move(o.s)) { std::puts("move"); }            // not noexcept
};
struct Quiet {
    std::string s = "x";
    Quiet() = default;
    Quiet(const Quiet& o) : s(o.s) { std::puts("copy"); }
    Quiet(Quiet&& o) noexcept : s(std::move(o.s)) { std::puts("move"); }
};

int main() {
    std::vector<Loud>  a(1); std::puts("-- Loud grows");  a.emplace_back();
    std::vector<Quiet> b(1); std::puts("-- Quiet grows"); b.emplace_back();
}
```

```text
-- Loud grows
copy
-- Quiet grows
move
```

Output from GCC 15.2 with libstdc++ (`-std=c++23`). In both cases the new element is constructed in
place; the printed line is the transfer of the one existing element. The easiest fix is to not write
the move constructor at all: a defaulted one is `noexcept` whenever the members' moves are.

## Where to put noexcept

- **Always:** move constructors, move assignment, `swap`, and destructors (already implicit). These are
  the operations other code relies on to be non-throwing.
- **Templates:** use conditional `noexcept` that forwards the property of the operations you call.
- **Otherwise, be careful.** `noexcept` is part of your interface; removing it later can break callers
  that tested it with the operator. A common guideline (the "Lakos rule", followed by the standard
  library) is not to mark functions with preconditions (narrow contracts) `noexcept`, so a checking
  build can report a violation by throwing.

`throw()` is the pre-C++11 spelling. Dynamic exception specifications (`throw(X)`) were deprecated in
C++11 and removed in C++17; `throw()` meant `noexcept(true)` in C++17 and was removed in C++20. Use
`noexcept`.

## Common mistakes

- **Promising too much.** `void log(const std::string& s) noexcept { std::string copy = s; }` can throw
  `std::bad_alloc`, which now ends the program instead of reaching a handler.
- **Hand-written move constructor without `noexcept`.** The type works, but every `vector`
  reallocation copies it, as the output above shows.
- **Thinking `noexcept` is checked.** A `noexcept` function may call anything; GCC warns only for a
  `throw` written directly in the body (`-Wterminate`).
- **Throwing from a destructor.** Destructors are `noexcept`, so the exception terminates the program.
  Report failures from a separate `close()` function instead.

## Key points

- Specifier: a promise enforced by `std::terminate`, not by the compiler.
- Operator: a compile-time `bool` saying whether an expression is declared non-throwing.
- `noexcept(noexcept(expr))` forwards the property in generic code; *(C++17)* it is part of the
  function type.
- Mark moves and `swap` `noexcept`, or containers copy instead of moving.
