---
id: boost-function
title: Boost.Function
sidebar_label: Boost.Function
sidebar_position: 1
tags: [c++, boost, function, callable, type-erasure]
---

# Boost.Function

`boost::function` is a **polymorphic function wrapper** — it can store and invoke any callable
(function pointer, functor, lambda, member-function pointer) whose signature matches the declared
type. It was the direct ancestor of `std::function`, standardised in C++11, and remains one of the
clearest examples of Boost libraries graduating into the language.

:::info The problem it solves
C++ has many kinds of callables — free functions, member functions, lambdas, `operator()` objects —
but they all have different types. Storing "something callable with signature `int(double)`" in a
variable, a container, or a callback slot requires **type erasure**. `boost::function` provides
exactly that: a single type that wraps any callable matching a given signature.
:::

## Basic usage

```cpp showLineNumbers title="function_basics.cpp"
#include <boost/function.hpp>
#include <iostream>

int add(int a, int b) { return a + b; }

struct Multiplier {
    int factor;
    int operator()(int x) const { return x * factor; }
};

int main() {
    boost::function<int(int, int)> op;

    op = &add;
    std::cout << op(3, 4) << "\n";        // 7

    op = Multiplier{10};
    std::cout << op(3, 0) << "\n";        // 30  (second arg ignored by Multiplier)

    op = [](int a, int b) { return a - b; };
    std::cout << op(10, 3) << "\n";       // 7
}
```

## Testing for emptiness

A `boost::function` that holds no target is **empty**. Calling an empty function throws
`boost::bad_function_call`.

```cpp showLineNumbers title="empty_check.cpp"
#include <boost/function.hpp>
#include <iostream>

int main() {
    boost::function<void()> f;

    if (!f) {
        std::cout << "empty\n";
    }

    try {
        f();   // throws
    } catch (const boost::bad_function_call& e) {
        std::cout << e.what() << "\n";
    }
}
```

:::danger Calling an empty function throws
Unlike raw function pointers (which are undefined behaviour when null-called), an empty
`boost::function` throws `boost::bad_function_call`. Always check with `if (f)` before calling, or
design the API so that the function is never empty.
:::

## Storing member functions

Member functions need an object to call through. Combine with `boost::bind` or a lambda to capture
the object.

```cpp showLineNumbers title="member_fn.cpp"
#include <boost/function.hpp>
#include <boost/bind.hpp>
#include <iostream>

struct Printer {
    void print(const std::string& msg) const {
        std::cout << msg << "\n";
    }
};

int main() {
    Printer p;

    // Option 1: boost::bind
    boost::function<void(const std::string&)> f1 =
        boost::bind(&Printer::print, &p, _1);

    // Option 2: lambda (C++11)
    boost::function<void(const std::string&)> f2 =
        [&p](const std::string& s) { p.print(s); };

    f1("hello from bind");
    f2("hello from lambda");
}
```

## Callbacks and event systems

The primary use case is **callback registration** — decoupling the caller from the callee.

```cpp showLineNumbers title="callback.cpp"
#include <boost/function.hpp>
#include <vector>
#include <iostream>

class Button {
public:
    using Callback = boost::function<void()>;

    void on_click(Callback cb) { callbacks_.push_back(std::move(cb)); }

    void click() {
        for (auto& cb : callbacks_) cb();
    }

private:
    std::vector<Callback> callbacks_;
};

int main() {
    Button btn;
    btn.on_click([] { std::cout << "handler A\n"; });
    btn.on_click([] { std::cout << "handler B\n"; });
    btn.click();
}
```

## Performance and overhead

`boost::function` (and `std::function`) use type erasure internally, which means:

- A **small-buffer optimisation** avoids heap allocation for small callables (typically up to
  ~24-32 bytes on most implementations).
- Larger callables are heap-allocated.
- Every call goes through an indirect function pointer (virtual-call-like overhead).

:::warning Not free
For hot inner loops or performance-critical callbacks, prefer templates or `auto` parameters that
avoid type erasure entirely. `boost::function` is for **interface boundaries** where you need to
store heterogeneous callables — not for tight numerical kernels.
:::

## Boost.Function versus std::function

| Feature | `boost::function` | `std::function` |
|---------|-------------------|-----------------|
| Header | `<boost/function.hpp>` | `<functional>` |
| Empty-call behaviour | throws `bad_function_call` | throws `bad_function_call` |
| Small-buffer optimisation | implementation-defined | implementation-defined |
| Allocator support | yes (deprecated) | removed in C++17 |
| `target()` / `target_type()` | yes | yes |
| Available pre-C++11 | yes | no |

:::note Which to choose
On C++11 and later, prefer `std::function` — it is standard, widely optimised, and interchangeable
with `boost::function` in almost all cases. Use `boost::function` only when targeting a pre-C++11
toolchain. See [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) for the
broader lineage.
:::

## See also

- <Icon icon="lucide:link" inline /> [Boost.Bind](./boost-bind.md) — partial application, often paired with `function`.
- <Icon icon="lucide:flame" inline /> [Boost.Phoenix](./boost-phoenix.md) — functional-programming toolkit built on top of function objects.
- <Icon icon="lucide:puzzle" inline /> [Boost.Any](../02-core-utilities/boost-any.md) — type erasure for values, not callables.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::function` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
