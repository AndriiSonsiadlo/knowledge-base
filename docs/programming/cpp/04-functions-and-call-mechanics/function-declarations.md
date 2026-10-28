---
id: function-declarations
title: Function Declarations and Definitions
sidebar_label: Function Declarations
sidebar_position: 1
tags: [cpp, functions, declarations, signatures, prototypes]
---

# Function Declarations and Definitions

A **declaration** tells the compiler a function exists and what its type is, so calls can be checked
and compiled. A **definition** is a declaration that also supplies the body. You can declare a
function as often as you like, but the program needs exactly one definition of each non-inline
function that is used. This page covers how declarations are written and what makes two of them the
same function. The rest of this section builds on it: [default arguments](./default-arguments.md),
[overloading](./overloading.md), [inline](./inline-functions.md),
[constexpr](./constexpr-functions.md), [noexcept](./noexcept.md) and
[calling conventions](./calling-conventions.md).

**Prerequisites:** [Translation Units](../01-toolchain-and-build/translation-units.md) (why each
`.cpp` file needs its own declarations, and the One Definition Rule).

```cpp showLineNumbers
int add(int a, int b);            // declaration ("prototype")
int add(int, int);                // redeclaration: parameter names are optional and ignored

int add(int a, int b) {           // definition
    return a + b;
}
```

A call compiles as long as a declaration is visible; the definition can be in another file. If no
file defines it, the error comes from the linker ("undefined reference to `add(int, int)`"), not the
compiler.

<Diagram title="Declarations in headers, one definition in a source file" accent="blue">
  <DiagramNode icon="file-text" title="math.h" accent>`int add(int, int);`</DiagramNode>
  <DiagramArrow label="#include" />
  <DiagramRow>
    <DiagramNode icon="file-text" title="math.cpp">Defines `add`</DiagramNode>
    <DiagramNode icon="file-text" title="main.cpp">Calls `add`</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="link" />
  <DiagramNode icon="binary" title="Program">The call in main.o resolves to the definition in math.o</DiagramNode>
</Diagram>

To *define* a function in a header instead, it must be [`inline`](./inline-functions.md) (or a
template), or every file that includes it adds another definition.

## The function's type and its signature

A function's **type** is its return type plus its parameter-type list (and, *(C++17)*, whether it is
`noexcept`). The **parameter-type list** is what makes two declarations name the same function or
two different [overloads](./overloading.md). The return type isn't part of that comparison: two
functions with the same name and parameters but different return types are an error, not overloads.

Before parameter types are compared, each one is **adjusted**:

| Written | Adjusted to | So these declare one function |
|---|---|---|
| `const int x` | `int` (top-level `const` dropped) | `void f(int)` and `void f(const int)` |
| `int a[10]` or `int a[]` | `int*` | `void f(int*)` and `void f(int[10])` |
| `int g(int)` (a function) | `int (*)(int)` | `void f(int g(int))` and `void f(int (*g)(int))` |

Top-level `const` in a *definition* still matters inside the body (`x` can't be modified), so it is
fine to write it there while the header declares plain `int`. Note that an array parameter loses its
size: `sizeof a` inside the function is the size of a pointer.

## Return types: leading, trailing, deduced

```cpp title="returns.cpp" showLineNumbers
#include <vector>

int square(int x) { return x * x; }                  // classic

auto cube(int x) -> int { return x * x * x; }       // trailing return type (C++11)

template <class T, class U>
auto mul(T a, U b) -> decltype(a * b) {             // return type depends on the parameters
    return a * b;
}

auto half(double x) { return x / 2; }                // deduced from the return statement (C++14)

auto& first(std::vector<int>& v) { return v[0]; }   // deduced reference: int&

int main() {
    std::vector<int> v{1, 2};
    first(v) = 7;
    return square(2) + cube(1) + static_cast<int>(mul(2, 1.5) + half(2.0)) + v[0];   // 4+1+3+1+7
}
```

The trailing form exists because a leading return type can't name the parameters. A deduced return
type (`auto` with no trailing part) needs the body to be visible, so such a function is normally
defined in a header and can't be used before its definition. The deduction rules are on
[Type Deduction](../03-types-and-values/type-deduction/auto.md).

## Attributes worth knowing

```cpp showLineNumbers
// ...
[[nodiscard]] int parse(const char* s);          // C++17: warn if the result is ignored
[[nodiscard("check the error")]] int open_file();  // C++20: with a reason
[[noreturn]] void fatal(const char* msg);         // C++11: never returns (exit, throw, abort)
[[deprecated("use parse2")]] int parse_old();     // C++14
[[maybe_unused]] static void debug_dump();        // C++17: no unused warning
```

`parse("1");` on its own line then gives GCC's "ignoring return value of 'int parse(const char*)',
declared with attribute 'nodiscard'". `[[noreturn]]` lets the compiler drop code after the call; if
such a function does return, the behaviour is undefined.

## Function types and pointers

A function name converts to a pointer to the function, and a pointer can be called directly:

```cpp title="pointers.cpp" showLineNumbers
#include <cstdio>

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

using BinaryOp = int (*)(int, int);       // pointer-to-function type alias
// equivalently: using BinaryOp = int(*)(int, int);  or  int (*op)(int, int);

int apply(BinaryOp op, int x, int y) { return op(x, y); }

int main() {
    BinaryOp op = add;                    // &add is the same
    std::printf("%d %d\n", apply(op, 5, 3), apply(sub, 5, 3));   // 8 2
}
```

For callbacks that may also be lambdas with captures, take a template parameter or `std::function`
instead (see [Lambdas](../07-classes-and-oop/lambdas.md)). Member functions have a different pointer
type (`int (Widget::*)() const`) because they need an object to be called on.

## Common mistakes

- **Declaration and definition disagree.** `int area(int, int);` in the header and
  `int area(long w, long h) { ... }` in the source define a *different* overload. Callers link
  against the declared one and get "undefined reference". Include the header in its own `.cpp` so
  mismatches in return type at least become compile errors.
- **`int f();` in C++ means "no parameters".** In C before C23 it meant "unspecified parameters".
  See [C vs C++](../00-overview/c-vs-cpp.md).
- **The most vexing parse.** `Widget w();` declares a function returning `Widget`, not a
  default-constructed object. Write `Widget w;` or `Widget w{};`.
- **Relying on an array parameter's size.** `void f(int a[10])` takes an `int*`; nothing checks that
  the caller passed ten elements. Use `std::span<int, 10>` *(C++20)* or a reference to an array.

## Key points

- Declare many times, define once; missing definitions are link errors.
- Overloads are told apart by the adjusted parameter-type list; the return type doesn't take part.
- Top-level `const`, array sizes and parameter names don't change which function you declared.
- Use a trailing return type when it depends on parameters; `auto` deduction needs a visible body.
