---
id: exceptions
title: Exception Handling
sidebar_label: Exceptions
sidebar_position: 1
tags: [cpp, exceptions, error-handling, try-catch, throw, stack-unwinding, exception-ptr]
---

# Exception Handling

An **exception** transfers control from the point where an error is detected to a handler somewhere
up the call stack, without every function in between having to check and forward a return value. The
runtime destroys the locals of each abandoned scope on the way, so cleanup happens even though the
normal path never completes. This page covers the mechanism: `throw`, `catch`, unwinding, the
standard hierarchy, and carrying exceptions across boundaries. How to keep data consistent when a
function exits by exception is on [Exception Safety](./02-noexcept-and-strong-guarantee.md), and when
to prefer return values over exceptions is on [Error Codes](./03-error-codes.md).

**Prerequisites:** [Constructors and destructors](../07-classes-and-oop/constructors-and-destructors.md),
[noexcept](../04-functions-and-call-mechanics/noexcept.md) for the specifier and what happens when
an exception reaches one.

## throw and catch

`throw expr;` copy-initializes an **exception object** from `expr` in storage managed by the
runtime, and begins unwinding. The type that matters is the static type of `expr` with top-level
`const`/references removed and arrays/functions decayed. A `catch` clause matches if its type is the
same, a public unambiguous base, or a pointer convertible to the thrown pointer type. Handlers are
tried in order, so list derived types before their bases.

```cpp showLineNumbers
// ...
try {
    risky();
} catch (const std::invalid_argument& e) {   // most specific first
    handle_bad_input(e);
} catch (const std::exception& e) {          // any standard exception
    log(e.what());
} catch (...) {                              // anything at all, including non-std types
    cleanup();
    throw;                                   // re-throw the active exception unchanged
}
```

Rules that cause real bugs:

- **Catch by `const` reference.** Catching by value copies and *slices* a derived exception to its
  base, and an exception object that is expensive or throws when copied makes it worse. GCC warns
  about it with `-Wall` (`-Wcatch-value`).
- **`throw;` re-throws the original object.** `throw e;` throws a *copy of the static type of `e`*,
  which slices if `e` is a base reference. Inside a handler, always write bare `throw;`.
- **`catch (...)` has no way to name the object.** Use `std::current_exception()` (below) to capture
  it, or `throw;` to propagate it.
- Any type can be thrown (`throw 42;` is legal), but throw types derived from `std::exception`, so
  that a `catch (const std::exception&)` can report them.

## Stack unwinding

When an exception is thrown, the runtime searches the call stack for a matching handler. If it finds
one, each scope between the throw and the handler is exited: **stack unwinding** destroys the
automatic objects of those scopes in reverse order of construction, then control resumes in the
handler.

```cpp title="unwind.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>

struct Guard {
    const char* name;
    explicit Guard(const char* n) : name(n) { std::printf("ctor %s\n", name); }
    ~Guard() { std::printf("dtor %s\n", name); }
};

void inner() {
    Guard g("inner");
    throw std::runtime_error("boom");
}
void outer() {
    Guard g("outer");
    inner();
    std::puts("not reached");
}
int main() {
    try { outer(); }
    catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
}
```

```text
ctor outer
ctor inner
dtor inner
dtor outer
caught: boom
```

Output is identical at `-O0`/`-O2` on g++ 15.2 and clang++ 21.1 (`-std=c++20`).

<Walkthrough title="Unwinding through two frames" caption="The handler runs only after every abandoned scope has been destroyed." accent="violet">
  <Step title="throw in inner()">

`inner` has constructed `Guard g("inner")`. The `throw` creates the exception object and starts
the search for a handler: <StepChange>inner → outer → main</StepChange>.

  </Step>
  <Step title="Handler found in main">

`main`'s `catch (const std::exception&)` matches `std::runtime_error`. Now that a handler is known,
the runtime unwinds the frames in between.

  </Step>
  <Step title="Destroy locals, innermost first">

<StepChange>`dtor inner`, then `dtor outer`</StepChange>: reverse of construction order, one frame at
a time. The line `not reached` is never executed.

  </Step>
  <Step title="Handler runs">

Control enters the `catch` block and prints the message. The exception object is destroyed when the
handler exits.

  </Step>
</Walkthrough>

Two consequences follow:

- **Destructors run during unwinding, so a destructor that lets an exception escape while another is
  already active calls `std::terminate`.** Destructors are `noexcept` by default for this reason.
- **If no handler is found**, or an exception reaches a `noexcept` boundary, `std::terminate` is
  called. Whether the stack is unwound first in the no-handler case is implementation-defined, so
  never rely on destructors running for an uncaught exception.

Unwinding only destroys objects. A raw `new` with no owner, a `FILE*`, or a locked mutex managed by
hand leaks. That is the reason to hold resources in
[RAII](../13-idioms-and-design/01-raii.md) objects such as
[`std::unique_ptr`](../06-pointers-references-and-smart-pointers/unique-ptr.md).
A constructor that throws leaves no object, so its destructor never runs, but fully constructed
members and bases are destroyed; see
[Exceptions during construction](../07-classes-and-oop/constructors-and-destructors.md#exceptions-during-construction).

## The standard hierarchy

`std::exception` (in `<exception>`) is the root, with a virtual `const char* what() const noexcept`.
The text returned by `what()` is unspecified by the standard, so don't parse it.

<Diagram title="Standard exception hierarchy (main branches)" accent="violet">
  <DiagramNode variant="pill" accent title="std::exception" />
  <DiagramArrow label="derived" />
  <DiagramRow>
    <DiagramNode title="logic_error">invalid_argument, domain_error, length_error, out_of_range</DiagramNode>
    <DiagramNode title="runtime_error">range_error, overflow_error, underflow_error, system_error</DiagramNode>
    <DiagramNode title="bad_alloc, bad_cast, bad_typeid, bad_function_call, bad_optional_access, ...">thrown by the language or library facilities</DiagramNode>
  </DiagramRow>
</Diagram>

`std::logic_error` is meant for mistakes a caller could have avoided; `std::runtime_error` for
failures only detectable at run time. In practice the distinction is loose, and the standard library
itself throws `out_of_range` from `at()` and `bad_alloc` from `new` (see
[new and delete](../05-memory-and-object-lifetime/new-and-delete.md)). `std::system_error` carries a
`std::error_code`; see [Error Codes](./03-error-codes.md).

## Custom exceptions

Derive from `std::runtime_error` or `std::logic_error` when the message string is enough: the base
stores and owns the text, so copying the exception cannot throw. Add fields only when handlers need
them.

```cpp showLineNumbers
// ...
#include <stdexcept>
#include <string>

class ParseError : public std::runtime_error {
public:
    ParseError(const std::string& what, int line)
        : std::runtime_error(what), line_(line) {}
    int line() const noexcept { return line_; }
private:
    int line_;
};
```

An exception type's copy constructor must not throw, because copying happens while another exception
is in flight (for example `std::exception_ptr`, or a by-value catch). Prefer `int`, enums, or
reference-counted data over a `std::string` member in types that derive directly from
`std::exception`.

## Nested exceptions and context

A low-level failure rarely means anything to the top-level handler. `std::throw_with_nested` (C++11)
throws a new exception that also carries the active one, and `std::rethrow_if_nested` unpacks it.

```cpp title="nested.cpp" showLineNumbers
#include <cstdio>
#include <exception>
#include <stdexcept>

struct AppError : std::runtime_error { using std::runtime_error::runtime_error; };

void low() { throw std::invalid_argument("bad digit"); }
void high() {
    try { low(); }
    catch (...) { std::throw_with_nested(AppError("config load failed")); }
}
void print(const std::exception& e, int depth = 0) {
    std::printf("%*s%s\n", depth * 2, "", e.what());
    try { std::rethrow_if_nested(e); }
    catch (const std::exception& n) { print(n, depth + 1); }
}
int main() {
    try { high(); } catch (const std::exception& e) { print(e); }
}
```

```text
config load failed
  bad digit
```

Verified with g++ 15.2 and clang++ 21.1 at `-O0` and `-O2`.

## Moving an exception between threads

`std::exception_ptr` (C++11) is a shared handle to an exception object of any type.
`std::current_exception()` captures the active exception inside a `catch`, and
`std::rethrow_exception(ep)` throws it again, possibly on another thread. An exception that escapes
a `std::thread`'s function calls `std::terminate`, so a worker has to catch and hand it over.
[`std::promise`/`std::future`](../11-concurrency-and-memory-model/07-futures-and-promises.md) do this
for you through `set_exception` and `get`.

```cpp title="exception_ptr.cpp" showLineNumbers
#include <cstdio>
#include <exception>
#include <stdexcept>
#include <thread>

int main() {
    std::exception_ptr ep;
    std::thread t([&] {
        try { throw std::runtime_error("from worker"); }
        catch (...) { ep = std::current_exception(); }
    });
    t.join();                         // join synchronizes: reading ep afterwards is safe
    try { if (ep) std::rethrow_exception(ep); }
    catch (const std::exception& e) { std::printf("main got: %s\n", e.what()); }
}
```

```text
main got: from worker
```

Compile with `-pthread`.

## Function-try-blocks

A constructor's member initializers run before its body, so an ordinary `try` in the body cannot
catch an exception from them. A **function-try-block** wraps the initializer list too:

```cpp title="function_try.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>

struct Res { Res() { throw std::runtime_error("res"); } };
struct W {
    Res r;
    W() try : r() { } catch (const std::exception& e) {
        std::printf("handler: %s\n", e.what());   // reaching the end re-throws
    }
};
int main() {
    try { W w; } catch (const std::exception& e) { std::printf("main: %s\n", e.what()); }
}
```

```text
handler: res
main: res
```

A constructor's handler cannot recover: if it finishes without throwing, the exception is re-thrown
automatically, because the object cannot exist. It is only useful for logging or translating the
exception. Members are already destroyed when the handler runs, so don't touch them.

## Costs and when to use them

Implementations differ, so treat these as typical behaviour of the Itanium ABI table-driven model
(GCC, Clang on Linux/macOS) and verify for your target: code on the non-throwing path normally has
no per-call checks, while actually throwing is very slow compared with a return (it allocates the
exception object and walks unwind tables). MSVC x64 uses a similar table-driven design. This
asymmetry is why exceptions suit *rare* failures and not routine control flow. Exceptions also may be
disabled (`-fno-exceptions`) in embedded and game code, which excludes the standard library parts
that throw.

Use exceptions when the failure is rare, the immediate caller usually can't handle it, and you want
to guarantee it is not silently ignored (constructors and operators have no return value to carry
errors). Use [return codes or `std::expected`](./03-error-codes.md) when failure is expected and
handled locally. Use [assertions or contracts](./04-assertions.md) for programmer errors that should
never occur.

## Common mistakes

- **Catching by value**, which slices; and `throw e;` instead of `throw;`.
- **Throwing from a destructor** (terminates if an unwinding is already running).
- **Empty `catch (...) {}`** that hides failures. At minimum log and rethrow.
- **Handlers in the wrong order**: a `catch (const std::exception&)` before a derived-type handler
  makes the later one unreachable.
- **Throwing across a language or ABI boundary** (a C callback, a `extern "C"` function, a shared
  library compiled with a different runtime). Catch everything at the boundary and translate.
- **Using exceptions for normal control flow**, such as ending a loop.

## Key points

- `throw` copies an exception object; catch it by `const` reference; rethrow with bare `throw;`.
- Unwinding destroys automatic objects in reverse order, so resource ownership belongs in RAII objects.
- A destructor must not let an exception escape; no matching handler or a `noexcept` boundary calls `std::terminate`.
- Use `std::throw_with_nested` for context and `std::exception_ptr` to cross threads.
- Constructors report failure by throwing; a function-try-block can only translate, not suppress.
