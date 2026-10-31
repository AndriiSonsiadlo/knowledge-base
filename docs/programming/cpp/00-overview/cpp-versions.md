---
id: cpp-versions
title: C++ Standard Versions
sidebar_label: C++ Versions
sidebar_position: 3
tags: [c++, standards, cpp11, cpp14, cpp17, cpp20, cpp23, cpp26, history]
---

# C++ Standard Versions

C++ is defined by an ISO standard, ISO/IEC 14882, maintained by the committee WG21. Since 2011 a new
edition has shipped every three years. Each one keeps almost all existing code working and adds
features on top. You need to know which standard you are compiling against for two reasons: it
decides which features you can use, and code you read may have been written for an older standard.

This page summarises what each standard added, links to the page that covers each feature, and
ends with how to choose a standard and select it in your build.

**Prerequisites:** [What is C++?](./what-is-cpp.md)

## Timeline

| Standard | ISO edition | Character | Working name |
|---|---|---|---|
| C++98 | 14882:1998 | First standard: templates, the STL, exceptions, namespaces | — |
| C++03 | 14882:2003 | Defect fixes only | — |
| C++11 | 14882:2011 | Major revision. The start of "modern C++". | C++0x |
| C++14 | 14882:2014 | Refinements to C++11 | C++1y |
| C++17 | 14882:2017 | Practical library and language additions | C++1z |
| C++20 | 14882:2020 | Major revision: concepts, ranges, coroutines, modules | C++2a |
| C++23 | 14882:2024 | Library-heavy refinements. The current published standard. | C++2b |
| C++26 | — | Technical work completed March 2026. Not yet published by ISO (as of October 2026). | C++2c |

Working names use a placeholder digit because the release year wasn't fixed during development.
C++0x was expected in the 2000s and shipped in 2011. C++23 is named for the year its technical work
finished, even though ISO published it in 2024.

## C++98 and C++03

C++98 defined the language most legacy code is written in: classes, templates, exceptions,
namespaces, and the STL's containers, iterators and algorithms. C++03 fixed defects without adding
features. Code from this era is recognisable by explicit iterator types, owning raw pointers with
manual `delete`, and `NULL`.

## C++11: modern C++

The largest change in the language's history. It changed everyday style more than any other
standard:

| Feature | Covered in |
|---|---|
| `auto` type deduction, `decltype` | [auto](../03-types-and-values/type-deduction/auto.md), [decltype](../03-types-and-values/type-deduction/decltype.md) |
| Move semantics and rvalue references | [Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md) |
| `std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr` | [unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md), [shared_ptr](../06-pointers-references-and-smart-pointers/shared-ptr.md) |
| Lambdas | [Lambdas](../07-classes-and-oop/lambdas.md) |
| Brace initialization, `std::initializer_list` | [Uniform Initialization](../05-memory-and-object-lifetime/initialization/uniform-initialization.md) |
| Range-based `for` | [Loops](../02-language-fundamentals/control-flow/loops.md) |
| `constexpr` (single-`return` functions only) | [constexpr Functions](../04-functions-and-call-mechanics/constexpr-functions.md) |
| `noexcept` | [noexcept](../04-functions-and-call-mechanics/noexcept.md) |
| Variadic templates | [Variadic Templates](../08-templates-and-metaprogramming/variadic-templates.md) |
| A memory model, `std::thread`, `std::mutex`, `std::atomic` | [C++ Memory Model](../11-concurrency-and-memory-model/01-cpp-memory-model.md), [Threads](../11-concurrency-and-memory-model/04-threads.md) |
| `nullptr`, `enum class`, `override`/`final`, `= default`/`= delete` | Below and in the linked class pages |

`nullptr` is the clearest single example of why C++11 matters. `NULL` is an integer constant, so
overload resolution can't treat it as a pointer:

```cpp showLineNumbers
#include <cstddef>

void f(int);
void f(char*);

void call() {
    f(NULL);     // error with GCC and Clang: ambiguous (NULL is an integer)
    f(nullptr);  // calls f(char*): nullptr has its own type, std::nullptr_t
}
```

## C++14: finishing C++11

| Feature | Example |
|---|---|
| Generic lambdas | `[](auto a, auto b) { return a + b; }` |
| Return type deduction for functions | `auto f() { return 42; }` |
| Relaxed `constexpr`: loops, local variables, multiple statements | See [constexpr Functions](../04-functions-and-call-mechanics/constexpr-functions.md) |
| `std::make_unique` (missing from C++11) | `auto p = std::make_unique<Widget>(42);` |
| Binary literals and digit separators | `0b1111'0000`, `1'000'000` |

## C++17: practical additions

| Feature | Covered in |
|---|---|
| Structured bindings: `for (const auto& [key, value] : map)` | [Loops](../02-language-fundamentals/control-flow/loops.md) |
| `if constexpr` | [Type Traits](../08-templates-and-metaprogramming/type-traits.md) |
| Fold expressions | [Fold Expressions](../08-templates-and-metaprogramming/fold-expressions.md) |
| `std::optional`, `std::variant`, `std::any` | [Utilities](../09-standard-library/utilities.md) |
| `std::string_view` | [Strings](../09-standard-library/strings.md) |
| `std::filesystem` | [Filesystem](../09-standard-library/filesystem.md) |
| Guaranteed copy elision for prvalues | [glvalue, prvalue, xvalue](../03-types-and-values/value-categories/glvalue-prvalue-xvalue.md) |
| Class template argument deduction (CTAD): `std::vector v{1, 2, 3};` | [Class Templates](../08-templates-and-metaprogramming/class-templates.md) |
| Parallel algorithms (`std::execution::par`) | [Algorithms](../09-standard-library/algorithms.md) |

```cpp showLineNumbers
#include <map>
#include <optional>
#include <string>

std::optional<int> parse_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    return std::nullopt;                       // "no value", no sentinel needed
}

void print_ages(const std::map<std::string, int>& ages) {
    for (const auto& [name, age] : ages) {     // structured binding
        // ...
    }
}
```

## C++20: the second major revision

| Feature | Covered in |
|---|---|
| Concepts and `requires` | [Concepts and requires](../08-templates-and-metaprogramming/concepts-and-requires.md) |
| Ranges and views | [Ranges](../09-standard-library/ranges.md) |
| Coroutines (language support only, no library types) | [Coroutines](../11-concurrency-and-memory-model/09-coroutines.md) |
| Modules | [Modules](../01-toolchain-and-build/modules.md) |
| Three-way comparison `<=>` | [Operator Overloading](../02-language-fundamentals/operators/operator-overloading.md) |
| `consteval`, `constinit`, more `constexpr` (including `std::vector` and `std::string` during constant evaluation) | [constexpr Functions](../04-functions-and-call-mechanics/constexpr-functions.md) |
| Designated initializers | [Aggregate Initialization](../05-memory-and-object-lifetime/initialization/aggregate-initialization.md) |
| `std::span` | [Containers](../09-standard-library/containers.md) |
| `std::jthread`, `std::stop_token` | [Threads](../11-concurrency-and-memory-model/04-threads.md) |
| `<chrono>` calendars and time zones | [Chrono](../09-standard-library/chrono.md) |
| `std::format` | — (the [fmt](../../fmt/readme.md) library it was standardised from) |

Concepts and a defaulted `<=>` remove two large sources of boilerplate:

```cpp showLineNumbers
#include <compare>
#include <concepts>

template <std::integral T>      // a clear error if T isn't an integer type
T twice(T v) { return v * 2; }

struct Point {
    int x, y;
    auto operator<=>(const Point&) const = default;   // also gives ==, !=, <, <=, >, >=
};
```

## C++23: refinements

| Feature | Covered in |
|---|---|
| `std::expected<T, E>` | [Error Codes](../10-error-handling-and-safety/03-error-codes.md) |
| `std::print` / `std::println` | — (see example below) |
| `std::generator`, the first standard coroutine type | [Coroutines](../11-concurrency-and-memory-model/09-coroutines.md) |
| `import std;` (the standard library as a module) | [Modules](../01-toolchain-and-build/modules.md) |
| Deducing `this` (explicit object parameter) | — |
| `if consteval`, multidimensional `operator[]`, `std::mdspan` | — |
| `std::flat_map`, `std::flat_set` | — |

```cpp showLineNumbers
#include <expected>
#include <generator>
#include <print>
#include <ranges>
#include <string>
#include <utility>

std::expected<int, std::string> safe_div(int a, int b) {
    if (b == 0) return std::unexpected("division by zero");
    return a / b;
}

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        a = std::exchange(b, a + b);
    }
}

int main() {
    auto r = safe_div(1, 0);
    std::println("{}", r ? "ok" : r.error());          // division by zero
    for (int x : fibonacci() | std::views::take(8))
        std::print("{} ", x);                          // 0 1 1 2 3 5 8 13
}
```

## C++26: finished, awaiting publication

WG21 completed C++26's technical content in March 2026. ISO had not published it as of October
2026, and compilers implement its features one at a time. The headline additions:

- **Static reflection**: inspecting types, members and enumerators at compile time.
- **Contracts**: `pre`, `post` and `contract_assert`. See
  [Contracts](../10-error-handling-and-safety/05-contracts.md).
- **`std::execution`**: a standard framework for asynchronous and parallel work (senders and
  receivers).
- **Safety changes**: reading an uninitialised variable becomes *erroneous behaviour* (defined but
  diagnosable) rather than undefined behaviour, and the standard library gains a hardened mode with
  bounds-checked preconditions.
- **`#embed`**: include a binary file's bytes as an initializer.

## Choosing a standard

**Recommendation:**

- **New code:** use C++20, or C++23 if every compiler you target supports the C++23 features you
  need.
- **Existing code:** move to at least C++17. It is the default in current GCC and Clang, and moving
  up from C++11 or C++14 rarely breaks anything.
- **Avoid relying on C++26 features** until your compilers ship them as non-experimental.

Support for a standard arrives feature by feature, not all at once. C++20 modules in particular
still depend on build-system support. Check cppreference's
[compiler support tables](https://en.cppreference.com/w/cpp/compiler_support) before relying on a
specific feature.

### Selecting it in a build

| Toolchain | Flag | Notes |
|---|---|---|
| GCC, Clang | `-std=c++20` | `-std=gnu++20` also enables GNU extensions. GCC 11+ and Clang 16+ default to `gnu++17`. |
| MSVC | `/std:c++20`, `/std:c++latest` | The default is C++14. |
| CMake | `set(CMAKE_CXX_STANDARD 20)` + `set(CMAKE_CXX_STANDARD_REQUIRED ON)` | Add `set(CMAKE_CXX_EXTENSIONS OFF)` for `-std=c++20` instead of `gnu++20`. See [CMake](../01-toolchain-and-build/build-systems-cmake.md). |

### Detecting it in code

`__cplusplus` holds the standard the compiler is using:

| Standard | `__cplusplus` |
|---|---|
| C++98/03 | `199711L` |
| C++11 | `201103L` |
| C++14 | `201402L` |
| C++17 | `201703L` |
| C++20 | `202002L` |
| C++23 | `202302L` |

MSVC reports `199711L` unless you pass `/Zc:__cplusplus`. To check for one feature rather than a
whole standard, use the feature-test macros: `__cpp_concepts` for language features, and
`__cpp_lib_expected` and similar from `<version>` (C++20) for library features.

## References

- [isocpp.org: Current Status](https://isocpp.org/std/status): the committee's schedule and
  published standards.
- [cppreference: C++ compiler support](https://en.cppreference.com/w/cpp/compiler_support): which
  compiler version implements each feature.
- [cppreference: Feature testing](https://en.cppreference.com/w/cpp/feature_test): the list of
  `__cpp_*` macros.
- Herb Sutter, [C++26 is done!](https://herbsutter.com/2026/03/29/c26-is-done-trip-report-march-2026-iso-c-standards-meeting-london-croydon-uk/)
  (March 2026): the C++26 completion trip report.
