---
id: constexpr-functions
title: constexpr, consteval and constinit
sidebar_label: constexpr
sidebar_position: 5
tags: [c++, constexpr, consteval, constinit, compile-time, cpp11, cpp20]
---

# constexpr, consteval and constinit

C++ can run ordinary-looking code during compilation. A `constexpr` function **may** be evaluated
at compile time when it is called in a context that needs a constant, and runs as a normal function
otherwise. *(C++20)* `consteval` makes compile-time evaluation **mandatory**, and `constinit` makes
a global's **initialization** happen at compile time without making it `const`. This page explains
when each one is evaluated, what each standard allowed inside such functions, and the mistakes that
come from assuming `constexpr` means "computed at compile time".

**Prerequisites:** [Function Declarations](./function-declarations.md),
[cv-qualifiers](../03-types-and-values/cv-qualifiers.md) (`const` versus `constexpr` variables),
[Storage Duration](../05-memory-and-object-lifetime/storage-duration.md) (for `constinit`).

<Diagram title="The three keywords" accent="amber">
  <DiagramRow>
    <DiagramNode title="constexpr (C++11)">Function: *can* run at compile time. Variable: is a `const` compile-time constant.</DiagramNode>
    <DiagramNode title="consteval (C++20)" accent>Function only: *every* call must be a constant expression.</DiagramNode>
    <DiagramNode title="constinit (C++20)">Static/thread variable only: initialized at compile time, still mutable.</DiagramNode>
  </DiagramRow>
</Diagram>

## When a constexpr function runs at compile time

The compiler **must** evaluate a call during compilation only when the result is needed in a
**manifestly constant-evaluated** context: a `constexpr` variable's initializer, an array bound, a
template argument, a `static_assert`, a `case` label, a `constinit` initializer. Everywhere else the
call is an ordinary function call. The optimizer may still fold it to a constant, but that is an
optimization, not a guarantee.

```cpp title="contexts.cpp" showLineNumbers
#include <array>
#include <cstdio>

constexpr int factorial(int n) {        // C++14 rules: locals and loops
    int r = 1;
    for (int i = 2; i <= n; ++i) r *= i;
    return r;
}

static_assert(factorial(5) == 120);      // compile time: required
std::array<int, factorial(4)> slots{};   // compile time: template argument

int main(int argc, char**) {
    constexpr int a = factorial(6);      // compile time: constexpr variable
    int b = factorial(6);                // not required; the optimizer will probably fold it
    int c = factorial(argc + 3);         // run time: argc is unknown
    std::printf("%d %d %d %zu\n", a, b, c, slots.size());   // 720 720 24 24
}
```

During constant evaluation the compiler acts as an interpreter that **must reject undefined
behaviour**. That makes compile-time evaluation a correctness check:

<Walkthrough title="Constant-evaluating factorial(4)" caption="The compiler interprets the body; any undefined behaviour stops compilation." accent="amber">
  <Step title="Call">

`static_assert(factorial(4) == 24)` needs a constant, so the compiler evaluates the call itself.
`n` = 4, <StepChange>`r` = 1</StepChange>.

  </Step>
  <Step title="i = 2, 3, 4">

The loop runs in the interpreter: `r` = 2, then 6, then <StepChange>`r` = 24</StepChange>. Every
signed multiplication is checked for overflow.

  </Step>
  <Step title="Return and check">

`i` = 5 ends the loop; the call yields <StepChange>24</StepChange> and the assertion holds. No code
for this call is emitted.

  </Step>
  <Step title="What if it went wrong">

`factorial(13)` overflows `int` (13! > 2³¹−1). In a constant-required context this is a
<StepChange>compile error</StepChange> ("overflow in constant expression"), where at run time it would
be silent undefined behaviour. Division by zero, out-of-bounds access and reading a dead object are
caught the same way.

  </Step>
</Walkthrough>

## What each standard allows inside

`constexpr` started very restricted and has been relaxed in every standard since:

| Standard | Newly allowed in `constexpr` functions |
|---|---|
| C++11 | Only a single `return` statement (plus `using`, `static_assert`). Recursion instead of loops. |
| C++14 | Local variables, loops, `if`/`switch`, mutation of locals. Member functions are no longer implicitly `const`. |
| C++17 | `constexpr` lambdas; `if constexpr` (a compile-time branch, see [Type Traits](../08-templates-and-metaprogramming/type-traits.md)) |
| C++20 | Virtual functions, `try` blocks (a `throw` still can't be evaluated), `dynamic_cast`/`typeid`, uninitialized locals, changing the active union member, **transient allocation** with `new`/`delete` (so `std::vector` and `std::string` work), `std::is_constant_evaluated()` |
| C++23 | `static`/`thread_local` variables that are themselves `constexpr`, `goto` and labels in code that isn't evaluated, `if consteval` |

These are checked with GCC 15: the C++14 `factorial` above fails under `-std=c++11` with "body of
'constexpr' function not a return-statement". The full list per paper is on
[cppreference](https://en.cppreference.com/w/cpp/language/constexpr).

*(C++20)* "Transient" means the memory must be freed before constant evaluation ends. You can build
and use a `std::vector` inside a `constexpr` function, but you can't keep one as a `constexpr`
variable:

```cpp title="transient.cpp" showLineNumbers
#include <string>
#include <vector>

constexpr std::size_t total_len() {
    std::vector<std::string> v{"ab", "cde"};   // allocated during constant evaluation...
    std::size_t n = 0;
    for (const auto& s : v) n += s.size();
    return n;                                   // ...and freed before it ends
}
static_assert(total_len() == 5);

// constexpr std::vector<int> leak{1, 2};       // error: refers to a result of 'operator new'

int main() {}
```

A common use is building a lookup table once, at compile time, with an immediately invoked lambda:

```cpp title="table.cpp" showLineNumbers
#include <array>

constexpr auto pow2 = [] {
    std::array<int, 8> t{};
    for (int i = 0; i < 8; ++i) t[i] = 1 << i;
    return t;
}();
static_assert(pow2[7] == 128);

int main() { return pow2[3]; }   // exits with 8
```

## consteval: compile time or error *(C++20)*

A `consteval` function is an **immediate function**: every call must produce a constant, or the
program doesn't compile. Use it when running at run time would be a bug, for example validating a
format string or computing a hash of a literal.

```cpp title="consteval.cpp" showLineNumbers
consteval int sq(int x) { return x * x; }

constexpr int nine = sq(3);     // OK
int main(int argc, char**) {
    int ok = sq(4);             // OK: 4 is a constant, so the call is constant-evaluated
    // int bad = sq(argc);      // error: call to consteval function 'sq(argc)' is not a constant expression
    return ok - 16 + nine - 9 + argc - argc;
}
```

*(C++23)* `if consteval` lets one `constexpr` function choose a path depending on whether it is being
constant-evaluated, and makes it legal to call `consteval` functions from the compile-time branch:

```cpp title="if-consteval.cpp" showLineNumbers
#include <cstdio>

constexpr int pick(int x) {
    if consteval { return x * 10; }   // during constant evaluation
    else         { return x; }        // at run time
}
static_assert(pick(2) == 20);

int main(int argc, char**) { std::printf("%d\n", pick(argc)); }   // prints 1
```

## constinit: compile-time initialization, run-time mutation *(C++20)*

Global and `static` variables are initialized either at compile time (**constant initialization**) or
when the program starts (**dynamic initialization**). Dynamic initialization across translation units
happens in an unspecified order, the static initialization order problem described in
[Storage Duration](../05-memory-and-object-lifetime/storage-duration.md). `constinit` asserts that a
variable gets constant initialization and refuses to compile otherwise, but leaves the variable
mutable:

```cpp title="constinit.cpp" showLineNumbers
consteval int sq(int x) { return x * x; }

constinit int counter = sq(4);     // initialized at compile time
void tick() { ++counter; }          // still writable: constinit is not const

int g = 0;
// constinit int h = g;            // error: 'constinit' variable 'h' does not have a constant initializer

int main() { tick(); return counter; }   // exits with 17
```

`constinit` applies only to variables with static or thread storage duration, and it can be put on an
`extern` declaration in a header, so users in other files know the variable is safe to read during
their own static initialization.

## Common mistakes

- **Assuming `constexpr` means compile time.** `int b = factorial(6);` is allowed to run at run time.
  If it must be a constant, store it in a `constexpr` variable or use `consteval`.
- **Expecting `constexpr` on a function to be checked.** Since C++23 a `constexpr` function doesn't have
  to be usable in a constant expression for *any* argument; you find out at the first call that needs
  it. Add a `static_assert` test next to it.
- **`constexpr` versus `const`.** `const int n = read();` is a run-time constant and can't size an
  array. `constexpr int n = ...;` must be a compile-time constant.
- **Taking the address of a local in a `constexpr` pointer.** `constexpr const int* p = &x;` works only
  if `x` has static storage; the address of an automatic variable isn't a constant.
- **Using `constinit` as `const`.** It only fixes *when* the variable is initialized.

## Key points

- `constexpr` function: may run at compile time; must when the result is needed as a constant.
- Constant evaluation rejects undefined behaviour, so `static_assert` tests catch bugs early.
- C++14 allowed loops and locals, C++20 allowed `virtual`, `try` and transient `new`; check the table
  before relying on a feature.
- `consteval`: always compile time. `constinit`: compile-time initialization of a mutable global.
- `constexpr` functions are implicitly [inline](./inline-functions.md), so they belong in headers.
