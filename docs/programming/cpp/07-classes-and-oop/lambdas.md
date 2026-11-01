---
id: lambdas
title: Lambda Expressions
sidebar_label: Lambdas
sidebar_position: 11
tags: [c++, lambdas, closures, cpp11, cpp14, cpp20, cpp23, functional]
---

# Lambda Expressions

A **lambda expression** *(C++11)* writes a function object inline, where it is used: a comparator
for `std::sort`, a callback, a one-off predicate. The compiler turns each lambda into an unnamed
class, the **closure type**, with an `operator()`, and the expression itself evaluates to an object
of that class, the **closure**. Variables the lambda uses from the surrounding scope are stored in
the closure as data members, either copied or as references. Knowing that one fact explains almost
every rule on this page: captures, `mutable`, lifetime bugs, size and performance.

This page is the canonical home for closure types and captures. Storing callables in general
(`std::function` and friends) is covered in [Type Erasure](../13-idioms-and-design/06-type-erasure.md);
passing callables to algorithms in [Algorithms](../09-standard-library/algorithms.md).

**Prerequisites:** [Function declarations](../04-functions-and-call-mechanics/function-declarations.md),
[Operator overloading](../02-language-fundamentals/operators/operator-overloading.md) (for
`operator()`), [Constructors and destructors](./constructors-and-destructors.md).

## Syntax

```cpp
// fragment: the parts of a lambda expression
[captures] (parameters) specifiers -> return_type { body }
```

- **Captures** list which enclosing variables the closure stores and how. `[]` captures nothing.
- **Parameters** work as for any function. The `()` may be omitted when empty (`[] { ... }`).
- **Specifiers** include `mutable`, `constexpr` / `consteval`, `noexcept`, and `static` *(C++23)*.
- **Return type** is deduced from `return` statements unless given with `->`.

## The closure type

```cpp title="closure.cpp" showLineNumbers
#include <iostream>

int main() {
    int base = 10;
    auto add = [base](int x) { return base + x; };   // closure object

    // What the compiler generates, roughly:
    struct AddClosure {
        int base;                                     // captured copy
        int operator()(int x) const { return base + x; }
    };
    AddClosure same{base};

    base = 99;                                        // the copy is unaffected
    std::cout << add(1) << ' ' << same(1) << '\n';    // 11 11
    static_assert(sizeof(add) == sizeof(int));
}
```

Consequences of the closure being a class:

- **Every lambda expression has its own unique type**, even two textually identical ones. Use
  `auto` to hold one, a template parameter to accept one, and `decltype` to name one.
- **The call operator is `const` by default**, so by-copy captures cannot be modified in the body.
  `mutable` removes that `const`.
- **The size is the size of its captures.** The `static_assert` above holds on GCC 15 and Clang 21;
  the layout of a closure's members is unspecified by the standard, so treat this as typical, not
  guaranteed. A capture-less lambda is an empty class.
- **A capture-less lambda converts to a plain function pointer**, so it can be passed to C APIs.
- **Since C++20**, capture-less closure types are default-constructible and assignable, so
  `decltype(lambda)` can be used as, for example, a `std::set` comparator type.

<Diagram title="[base](int x) { return base + x; }" caption="The lambda expression is evaluated once to create the closure; each call runs operator() on that object." accent="blue">
  <DiagramRow>
    <DiagramNode icon="file-text" title="Lambda expression">Source text at the point of use.</DiagramNode>
    <DiagramArrow direction="right" label="compiler" />
    <DiagramNode icon="boxes" title="Closure type" accent>Unnamed class: member <code>int base</code>, <code>int operator()(int) const</code>.</DiagramNode>
    <DiagramArrow direction="right" label="evaluation" />
    <DiagramNode icon="package" title="Closure object">Holds a copy of <code>base</code> taken when the expression ran.</DiagramNode>
  </DiagramRow>
</Diagram>

## Captures

A capture is taken **when the lambda expression is evaluated**, not when it is called.

```cpp title="captures.cpp" showLineNumbers
#include <iostream>
#include <memory>
#include <utility>

int main() {
    int a = 1, b = 2;
    auto byValue = [a] { return a; };          // copy of a at creation
    auto byRef   = [&b] { return b; };         // refers to b
    a = 10; b = 20;
    std::cout << byValue() << ' ' << byRef() << '\n';   // 1 20

    auto counter = [n = 0]() mutable { return ++n; };   // init-capture (C++14)
    counter(); counter();
    std::cout << counter() << '\n';                      // 3

    auto p = std::make_unique<int>(42);
    auto owner = [q = std::move(p)] { return *q; };      // move-only capture
    std::cout << owner() << ' ' << (p == nullptr) << '\n'; // 42 1
}
```

| Capture | Meaning |
|---|---|
| `[x]` | Copy `x` into the closure |
| `[&x]` | Store a reference to `x` |
| `[=]` | Copy every variable the body uses (default by copy) |
| `[&]` | Reference every variable the body uses (default by reference) |
| `[=, &x]`, `[&, x]` | A default plus explicit exceptions |
| `[y = expr]` *(C++14)* | **Init-capture**: a new member `y` initialized from `expr`; use `std::move` to capture move-only objects |
| `[&r = expr]` *(C++14)* | Init-capture by reference |
| `[this]` | Copy the `this` pointer; members are accessed through it |
| `[*this]` *(C++17)* | Copy the whole enclosing object |
| `[...xs]`, `[...ys = std::move(xs)]` *(C++20)* | Capture a parameter pack |

Only variables with automatic storage duration are captured. Globals and `static` locals are used
directly, never copied, so `[=]` does not snapshot them.

### Capturing `this`

Inside a member function, a lambda that uses a data member captures `this`, a **pointer** to the
object, not the member itself:

```cpp title="this-capture.cpp" showLineNumbers
#include <iostream>
#include <string>

struct Button {
    std::string label = "OK";
    auto handler() {
        // [this] captures the pointer: the lambda must not outlive *this.
        // [*this] (C++17) copies the whole object instead.
        auto byPtr  = [this] { return label; };
        auto byCopy = [*this] { return label; };
        return byPtr() + byCopy();
    }
};

int main() { std::cout << Button{}.handler() << '\n'; }   // OKOK
```

`[=]` used to capture `this` implicitly, which hid the fact that members were accessed by pointer.
That implicit capture is **deprecated in C++20**; GCC 15 and Clang 21 warn about it under `-Wall`
(`-Wdeprecated` / `-Wdeprecated-this-capture`). Write `[=, this]` or `[*this]` explicitly.

### `mutable`

By-copy captures are `const` inside the body because `operator()` is `const`. `mutable` makes the
call operator non-`const`, so the closure can update its own copies, as `counter` above does. The
original variables are never affected, and a `mutable` closure cannot be called through a `const`
reference.

## Dangling captures

A reference capture, `[this]`, or a captured raw pointer does not extend any lifetime. If the
closure outlives the referenced object, calling it is undefined behaviour. This happens when a lambda
is returned, stored as a callback, or handed to another thread:

```cpp title="lifetime.cpp" showLineNumbers
#include <functional>
#include <memory>
#include <iostream>

std::function<int()> makeDangling() {
    int x = 42;
    return [&x] { return x; };      // BUG: x dies when the function returns
}

std::function<int()> makeSafe() {
    int x = 42;
    return [x] { return x; };       // copy lives inside the closure
}

std::move_only_function<int()> makeOwner() {     // C++23
    auto p = std::make_unique<int>(42);
    return [p = std::move(p)] { return *p; };    // std::function would not compile: closure is move-only
}

int main() {
    std::cout << makeSafe()() << ' ' << makeOwner()() << '\n';  // 42 42
    (void)makeDangling;
}
```

`std::function` requires a copyable callable, so a closure holding a `std::unique_ptr` cannot be
stored in it. Return `auto`, or use `std::move_only_function` *(C++23)*.

Rule of thumb: capture by reference only when the lambda is used and discarded within the current
scope (algorithms, immediately invoked lambdas). For anything stored or deferred, capture by value
or with an init-capture that owns what it needs, for example a `std::shared_ptr`.

## Generic, template and recursive lambdas

```cpp title="generic.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <vector>

int main() {
    auto print = [](const auto& x) { std::cout << x << ' '; };   // generic (C++14)
    print(42); print(3.5); print(std::string("hi"));

    auto first = []<typename T>(const std::vector<T>& v) { return v.front(); };  // C++20
    std::cout << first(std::vector{7, 8}) << '\n';                // 42 3.5 hi 7

    auto fact = [](this auto self, int n) -> long {               // C++23
        return n <= 1 ? 1 : n * self(n - 1);
    };
    std::cout << fact(10) << '\n';                                // 3628800

    constexpr auto sq = [](int x) { return x * x; };              // implicitly constexpr (C++17)
    static_assert(sq(4) == 16);

    const std::vector<int> table = [] {                           // immediately invoked
        std::vector<int> v;
        for (int i = 0; i < 4; ++i) v.push_back(i * i);
        return v;
    }();
    std::cout << table.back() << '\n';                            // 9
}
```

- **Generic lambdas** *(C++14)*: an `auto` parameter makes `operator()` a member function template.
  Each call with a new argument type instantiates it, following the rules on
  [Template Argument Deduction](../08-templates-and-metaprogramming/template-argument-deduction.md).
- **Template parameter lists** *(C++20)*: `[]<typename T>(...)` names the type, which `auto` cannot,
  for example to require a `std::vector<T>`.
- **Recursion**: a lambda cannot refer to its own variable inside its initializer. Before C++23 the
  workarounds were storing it in a `std::function` (type-erased, slower) or passing it to itself as
  an argument. C++23's **explicit object parameter** (`this auto self`) gives the body access to the
  closure directly.
- **`constexpr`**: since C++17 a lambda's call operator is `constexpr` automatically when it meets the
  [`constexpr` function](../04-functions-and-call-mechanics/constexpr-functions.md) requirements.
- **Immediately invoked lambdas** let you initialize a `const` variable with multi-statement logic.

## Passing lambdas around

```cpp title="passing.cpp" showLineNumbers
#include <functional>

template <typename F>
int applyTemplate(F f) { return f(2); }                 // one instantiation per closure type; inlinable

int applyErased(const std::function<int(int)>& f) { return f(2); }  // one function; indirect call

int (*asPointer)(int) = [](int x) { return x + 1; };   // captureless -> function pointer

int main() {
    int k = 3;
    auto mul = [k](int x) { return x * k; };
    return applyTemplate(mul) + applyErased(mul) + asPointer(0) - 13;   // 6 + 6 + 1 - 13 = 0
}
```

| Parameter type | Accepts | Cost |
|---|---|---|
| Template parameter `F` (or `std::invocable auto`) | Any callable | None beyond the call; the compiler sees the body and can inline it |
| `std::function<R(Args...)>` | Any **copyable** callable with that signature | Type erasure: an indirect call, and a heap allocation when the closure does not fit the implementation's small buffer |
| `std::move_only_function<R(Args...)>` *(C++23)* | Move-only callables too | Same kind of cost as `std::function` |
| `std::function_ref<R(Args...)>` *(C++26)* | Any callable, non-owning | Indirect call, no allocation; must not outlive the callable |
| Function pointer `R(*)(Args...)` | Capture-less lambdas and functions | Indirect call |

Prefer templates for parameters that are called immediately (algorithm-style), and a type-erased
wrapper when the callable must be stored in a non-template data member or cross an ABI boundary.

## References

- [cppreference: Lambda expressions](https://en.cppreference.com/w/cpp/language/lambda)
- [cppreference: `std::move_only_function`](https://en.cppreference.com/w/cpp/utility/functional/move_only_function)
- [P0806R2: Deprecate implicit capture of `this` via `[=]`](https://wg21.link/P0806R2)
- [P0847R7: Deducing `this`](https://wg21.link/P0847R7)
