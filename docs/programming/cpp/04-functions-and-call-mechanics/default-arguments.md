---
id: default-arguments
title: Default Function Arguments
sidebar_label: Default Arguments
sidebar_position: 2
tags: [cpp, functions, default-arguments, parameters]
---

# Default Function Arguments

A **default argument** is a value the compiler supplies for a trailing parameter the caller leaves
out. The important thing to understand is *where* that happens: at the **call site**, by rewriting
`connect("db")` into `connect("db", 80)` using the declaration the caller can see. The function
itself always receives every argument. That one fact explains all of the rules and surprises below.

**Prerequisites:** [Function Declarations](./function-declarations.md).

```cpp showLineNumbers
// ...
void connect(const std::string& host, int port = 80, bool tls = false);

connect("db");             // connect("db", 80, false)
connect("db", 443);        // connect("db", 443, false)
connect("db", 443, true);
```

## Rules

- **Defaults go at the end.** After a parameter with a default, every later parameter needs one too
  (except a function parameter pack). `void p(int a = 1, int b);` is an error.
- **Put them in the declaration the callers see,** normally the header. A default can't be repeated
  in a later declaration of the same scope, so a `.cpp` definition that restates it is an error
  ("default argument given for parameter 1").
- **Later declarations can add defaults** for parameters that don't have one yet, right to left:

  ```cpp showLineNumbers
  // ...
  void connect(const std::string& host, int port = 80);
  void connect(const std::string& host = "localhost", int port);   // OK: adds a default for host
  ```

- **What a default may refer to:** any expression valid at the declaration, including function calls
  and `static` members. Not other parameters (`void f(int a, int b = a)` is an error), not `this`,
  and not non-static members.

```cpp showLineNumbers
// ...
struct Widget {
    int size_ = 100;
    static constexpr int default_size = 64;
    void resize(int n = default_size);    // OK: static member
    // void grow(int n = size_);          // error: invalid use of non-static data member
};
```

## Evaluated at every call

The default expression is evaluated anew for each call that uses it, in the caller's context:

```cpp title="each-call.cpp" showLineNumbers
#include <cstdio>

int next_id() { static int id = 0; return ++id; }
void tag(int id = next_id()) { std::printf("id %d\n", id); }

int main() {
    tag();     // id 1
    tag();     // id 2
    tag(7);    // id 7: next_id() not called
}
```

## Pitfalls

**Virtual functions take the default from the static type.** The *function* is chosen at run time,
but the default is inserted at compile time from the declaration the compiler sees:

```cpp title="virtual-default.cpp" showLineNumbers
#include <cstdio>

struct Base {
    virtual void greet(const char* who = "base") const { std::printf("Base %s\n", who); }
    virtual ~Base() = default;
};
struct Derived : Base {
    void greet(const char* who = "derived") const override { std::printf("Derived %s\n", who); }
};

int main() {
    Derived d;
    const Base& b = d;
    b.greet();   // "Derived base": Derived's body, Base's default
    d.greet();   // "Derived derived"
}
```

Don't give overrides different defaults. Better still, keep defaults off virtual functions and put
them on a non-virtual wrapper.

**Defaults are not part of the function type.** A function pointer to `void cb(int, int = 5)` has
type `void(*)(int, int)`, and calling it with one argument is an error. The same goes for
`std::function` and templates that forward arguments.

**Defaults are baked into the caller's binary.** Changing a default in a library header has no effect
on already-compiled callers until they are rebuilt, because the value lives in their call
instructions, not in the library.

**Overlapping with an overload.** `void f(int, int = 0);` and `void f(int);` can both be declared, but
every call `f(42)` is ambiguous. See [Overloading](./overloading.md).

## Defaults or overloads?

| Prefer a default argument when | Prefer overloads when |
|---|---|
| The omitted case is the same function with a common value | The omitted case needs different logic |
| The value is stable across library versions | The value might change without rebuilding callers |
| The function isn't virtual and isn't taken by address | You need each arity as a separate function (pointers, callbacks) |

## Key points

- The compiler fills defaults in at the call site, from the declaration visible there.
- Defaults are trailing, declared once (usually in the header), and evaluated on every call.
- Virtual calls use the static type's default; function pointers don't carry defaults at all.
- Changing a default requires recompiling the callers.
