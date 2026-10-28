---
id: storage-duration
title: Storage Duration
sidebar_label: Storage Duration
sidebar_position: 2
tags: [c++, storage-duration, static-initialization, thread-local, lifetime]
---

# Storage Duration

Every object has a **storage duration**: the minimum time its storage is guaranteed to exist. C++ has
four of them: automatic, static, thread and dynamic. The duration is fixed by how the object is
declared or created. It decides when the object is initialized, when it is destroyed, and in which
order relative to other objects. Getting the order wrong is the cause of the "static initialization
order fiasco" and of crashes at program exit.

**Prerequisites:** [Process memory overview](./memory-model-overview.md) (where each duration is
usually stored).

## The four durations

| Duration | Declared as | Storage exists | Typical location |
|---|---|---|---|
| Automatic | Block-scope variable without `static`/`thread_local`/`extern`; function parameters | From block entry to block exit | Stack (or registers) |
| Static | Namespace-scope variable; any variable declared `static` or `extern` | Whole program run | `.data` / `.bss` |
| Thread *(C++11)* | Any variable declared `thread_local` | Lifetime of the thread | Per-thread TLS block |
| Dynamic | Object created by a `new`-expression or by an allocator | Until it is explicitly released | Heap |

Storage duration belongs to **objects**, and a variable's duration is that of the object it names.
A member has the duration of its enclosing object: a `std::string` member of a global has static
storage duration, even though the characters it owns are on the heap with dynamic duration.

Storage existing does not mean the object exists. An object's lifetime starts when its
initialization finishes and ends when its destructor starts, which is a shorter span inside the
storage duration. See [Object lifetime](./object-lifetime.md).

## Automatic storage

Automatic objects are created when control reaches their declaration and destroyed when control
leaves the block, in reverse order of construction. That includes leaving by `return`, `break`,
`goto`, or an exception. This guarantee is what [RAII](../13-idioms-and-design/01-raii.md) relies on.

```cpp title="automatic.cpp" showLineNumbers
#include <cstdio>

struct Tag {
    const char* name;
    explicit Tag(const char* n) : name(n) { std::printf("+%s ", name); }
    ~Tag() { std::printf("-%s ", name); }
};

int main() {
    Tag a("a");
    {
        Tag b("b");
        Tag c("c");
    }               // c, then b
    Tag d("d");
    std::printf("| ");
}                   // d, then a
```

Output:

```text
+a +b +c -c -b +d | -d -a
```

## Static storage

Namespace-scope variables, `static` data members and `static` locals all have static storage
duration. They are initialized in two phases:

1. **Static initialization**, done before any other code runs. Every static object is first
   **zero-initialized** (see [Value initialization](./initialization/value-initialization.md#zero-initialization)).
   If its initializer is a constant expression, it gets **constant initialization** instead, and
   the value is usually baked into `.data` by the compiler.
2. **Dynamic initialization** for the rest: initializers that call non-`constexpr` functions or
   constructors run at run time, before the first use of anything in their translation unit (in
   practice, before `main` for ordinary globals).

```cpp title="phases.cpp" showLineNumbers
#include <cstdlib>

int zeroed;                                   // zero-initialized only: 0
constexpr int limit = 64;                     // constant initialization
int doubled = limit * 2;                      // constant initialization (constant expression)
const char* home = std::getenv("HOME");       // dynamic initialization at run time

int main() { return zeroed + (home ? 0 : 0) + doubled - 128; }   // returns 0
```

### Static locals

A `static` local is initialized the first time control passes through its declaration, not at
program start. Since C++11 this initialization is thread-safe: if two threads reach it at once, one
runs the initializer and the other waits. A static local with a constant initializer is constant
initialized up front, like a global.

```cpp title="counter.cpp" showLineNumbers
int next_id() {
    static int id = 0;   // initialized once; keeps its value between calls
    return ++id;
}

int main() { next_id(); next_id(); return next_id() - 3; }   // returns 0
```

### The static initialization order fiasco

Within one translation unit, dynamically initialized globals are initialized in the order they are
defined. Across translation units the order is **unspecified**. If a global in `a.cpp` reads a
global from `b.cpp` during its own initialization, it may see a zero-initialized object that has not
been constructed yet.

```cpp title="two files (fragment)"
// config.cpp
std::string config_path = std::string(std::getenv("HOME")) + "/.app";

// logger.cpp
extern std::string config_path;
Logger global_logger(config_path);   // may run before config_path is constructed: UB
```

Two fixes:

- **Make it constant.** If the value can be a constant expression, declare it `constexpr`, or
  `constinit` *(C++20)*. `constinit` requires constant initialization and fails to compile if the
  initializer is not a constant expression, so the variable can never take part in the order
  problem.
- **Use a function-local static** (the "construct on first use" idiom). The object is created the
  first time someone asks for it, whichever translation unit that is.

```cpp title="first-use.cpp" showLineNumbers
#include <string>

const std::string& config_path() {
    static const std::string path = "/etc/app.conf";   // built on first call
    return path;
}

constinit int max_connections = 128;   // C++20: guaranteed compile-time initialization

int main() { return config_path().empty() + max_connections - 128; }   // returns 0
```

### Destruction at exit

Static objects are destroyed after `main` returns (or `std::exit` is called), in the **reverse
order** of the completion of their construction. Static locals that were never reached are never
constructed and so are never destroyed. The same order problem exists in reverse: a destructor that
uses another static object may find it already destroyed. When that matters, a common choice is to
never destroy the object: `static auto& log = *new Logger;` leaks on purpose and stays usable until
the process ends.

## Thread storage

A `thread_local` variable has one instance per thread. Each thread's instance is initialized before
that thread first uses it (or at thread start, depending on the implementation) and destroyed when
the thread exits. `thread_local` at block scope implies `static`.

```cpp title="tls.cpp" showLineNumbers
#include <cstdio>
#include <thread>

thread_local int calls = 0;

void work(const char* who) {
    for (int i = 0; i < 3; ++i) ++calls;
    std::printf("%s: %d\n", who, calls);   // each thread counts its own calls
}

int main() {
    std::thread t1(work, "t1");
    std::thread t2(work, "t2");
    t1.join();
    t2.join();
    work("main");
}
```

Each line prints `3`. The order of the `t1` and `t2` lines can vary between runs. Typical uses are
per-thread caches, random number generators, and error state like `errno`. Accessing a
`thread_local` can cost more than a plain global, especially from a shared library, because the
address has to be looked up for the current thread.

## Dynamic storage

Objects with dynamic storage duration are created by a `new`-expression (or by an allocator plus
construction) and live until they are explicitly destroyed. Nothing destroys them for you, so in
modern code they are always owned by another object: a container, a `std::unique_ptr`, or a
`std::shared_ptr`. The mechanics are in [new and delete](./new-and-delete.md), the owners in
[unique_ptr](../06-pointers-references-and-smart-pointers/unique-ptr.md).

## Watching all four

The program below creates one object of each duration and prints when each is constructed and
destroyed.

```cpp title="durations.cpp" showLineNumbers
#include <cstdio>
#include <thread>

struct Logger {
    const char* name;
    explicit Logger(const char* n) : name(n) { std::printf("%s created\n", name); }
    ~Logger() { std::printf("%s destroyed\n", name); }
};

Logger global("global");                       // static: before main

void in_thread() { thread_local Logger tls("thread_local"); }

int main() {
    std::printf("main starts\n");
    Logger local("local");                     // automatic
    static Logger once("static local");        // static: on first pass
    Logger* dynamic = new Logger("dynamic");   // dynamic
    std::thread(in_thread).join();             // created and destroyed with the thread
    delete dynamic;
    std::printf("main ends\n");
}                                              // local, then static local, then global
```

<Walkthrough title="Order of construction and destruction" caption="Output of durations.cpp, built with g++ 15 and clang++ 21, -std=c++23." accent="blue">
  <Step title="Before main">

```text
global created
```

Dynamic initialization of the namespace-scope `global` runs before `main` starts.

  </Step>
  <Step title="Inside main">

```text
main starts
local created
static local created
dynamic created
```

`local` is constructed when its declaration is reached. The static local is constructed on the
first pass through its declaration. `new` creates the dynamic object.

  </Step>
  <Step title="The thread">

```text
thread_local created
thread_local destroyed
```

The `thread_local` exists only while the thread runs. It is <StepChange>destroyed at thread
exit</StepChange>, before `join` returns.

  </Step>
  <Step title="Explicit delete">

```text
dynamic destroyed
main ends
```

The dynamic object dies exactly where `delete` runs, not at any scope boundary.

  </Step>
  <Step title="After main">

```text
local destroyed
static local destroyed
global destroyed
```

`local` dies at the closing brace of `main`. Then the statics are destroyed in
<StepChange>reverse order of construction</StepChange>: the static local was constructed after
`global`, so it is destroyed first.

  </Step>
</Walkthrough>

## Pitfalls

- **Reading another TU's global during initialization.** The order is unspecified. Use `constinit`
  or a function-local static.
- **Returning a pointer or reference to an automatic object.** It is destroyed at `return`. Compilers
  warn (`-Wreturn-local-addr` in GCC, `-Wreturn-stack-address` in Clang), but not through
  indirections.
- **Static destructors using other statics.** Destruction order is the reverse of construction and
  may not be what you expect across translation units.
- **Large automatic arrays.** `char buf[16 << 20];` compiles fine and overflows an 8 MiB stack at
  run time. Use `std::vector`.

## Key points

- Four durations: automatic (scope), static (program), thread (thread), dynamic (until `delete`).
- Statics are zero-initialized first, then constant or dynamic initialized. Only dynamic
  initialization has ordering problems.
- `constinit` *(C++20)* and function-local statics remove cross-file order dependencies.
- Destruction is always in reverse order of construction, for both automatic and static objects.
