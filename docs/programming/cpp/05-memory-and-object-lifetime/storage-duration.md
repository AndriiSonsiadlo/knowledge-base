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

**Prerequisites:** [Memory model overview](./memory-model-overview.md) (objects, storage and bytes).

## The four durations

| Duration | Declared as | Storage exists | Typical location |
|---|---|---|---|
| Automatic | Block-scope variable without `static`/`thread_local`/`extern`; function parameters | From block entry to block exit | Stack (or registers) |
| Static | Namespace-scope variable; block-scope `static` local; `static` data member; block-scope `extern` declaration (names an object defined elsewhere) | Whole program run | `.data` / `.bss` |
| Thread *(C++11)* | Any variable declared `thread_local` | Lifetime of the thread | Per-thread TLS block |
| Dynamic | Object created by a `new`-expression or by an allocator | Until it is explicitly released | Heap |

Storage duration belongs to **objects**, and a variable's duration is that of the object it names.
A member has the duration of its enclosing object: a `std::string` member of a global has static
storage duration, even though the characters it owns are on the heap with dynamic duration.

Storage existing does not mean the object exists. An object's lifetime starts when its
initialization finishes and ends when its destructor starts, which is a shorter span inside the
storage duration. See [Object lifetime](./object-lifetime.md).

## Linkage is not storage duration

Storage duration is about **lifetime**: how long the object exists. **Linkage** is about **names**:
whether a declaration in another translation unit refers to the same entity (see
[Translation units](../01-toolchain-and-build/translation-units.md)). The two are independent.

- A namespace-scope variable always has static duration. `static` there only gives it **internal
  linkage**; the object is the same kind of object, just invisible to other files. An unnamed
  namespace has the same effect, and is the preferred spelling.
- A namespace-scope `const` (non-`inline`, non-`extern`) variable has internal linkage and static
  duration. `extern const int n = 1;` gives it external linkage.
- A variable with external linkage is shared by name across files; other files declare it with
  `extern`. `extern int n;` is a declaration only, with no definition.
- `inline` variables *(C++17)* have external linkage and exactly one object program-wide, even if
  defined in a header included by many files. Without `inline`, a non-const header variable would
  violate the one definition rule.
- `static` therefore means two things: at namespace scope it selects linkage, at block scope it
  selects static duration (`static int id` inside a function; the name has no linkage).

```cpp title="linkage.cpp" showLineNumbers
static int hidden = 1;          // static duration, internal linkage
namespace { int also_hidden = 2; }   // same
const int limit = 3;            // static duration, internal linkage (const)
inline int shared = 4;          // static duration, external linkage, one object (C++17)
int visible = 5;                // static duration, external linkage

int f() { static int calls = 0; return ++calls; }   // static duration, no linkage

int main() { return hidden + also_hidden + limit + shared + visible + f() - 16; }   // returns 0
```

## Where implementations put each duration

The standard defines the four durations and says nothing about a stack, a heap or segments. The
layout below is what you get on Linux with an ELF executable on x86-64. Other platforms use the same
ideas with different names and addresses.

<Diagram title="Typical process address space (high addresses at the top)" caption="Typical for Linux/ELF, not mandated by the standard. Each thread gets its own stack. Shared libraries and memory-mapped files sit in the gap between heap and stack." accent="blue">
  <DiagramNode icon="layers" title="Stack" accent>Automatic storage: locals, parameters, return addresses. Grows down. One per thread.</DiagramNode>
  <DiagramArrow label="free gap: mmap regions, shared libraries" dashed />
  <DiagramNode icon="boxes" title="Heap">Dynamic storage: `new`, `malloc`, container buffers. Grows up.</DiagramNode>
  <DiagramGroup label="Static storage (from the executable file)">
    <DiagramNode icon="binary" title=".bss">Zero-initialized statics. Takes no space in the file.</DiagramNode>
    <DiagramNode icon="file-text" title=".data">Statics with a non-zero initial value.</DiagramNode>
    <DiagramNode icon="lock" title=".rodata">String literals, constant tables. Read-only.</DiagramNode>
  </DiagramGroup>
  <DiagramNode icon="cpu" title=".text">Machine code. Read-only and executable, shared between processes running the same file.</DiagramNode>
</Diagram>

| Duration | Usually placed in | Created | Released |
|---|---|---|---|
| Automatic | Stack, or a register | Function entry or declaration reached | Scope exit |
| Static, zero or no initializer | `.bss` | Load time, zero-filled by the loader | Process exit |
| Static, non-zero constant initializer | `.data` (or `.rodata` if `const`) | Load time, copied from the file | Process exit |
| Static, dynamic initializer | `.bss`, filled by startup code | Before `main` (or at first use for a local) | Process exit |
| Thread | Per-thread TLS block | Thread start or first use | Thread exit |
| Dynamic | Heap (allocator, which gets pages from the OS) | `new`, `malloc` | `delete`, `free` |

String literals are themselves static objects, normally in `.rodata`; a `const char*` that points
to one is a separate object with its own storage.

### Stack and heap

Most day-to-day decisions are between automatic and dynamic storage.

| | Stack | Heap |
|---|---|---|
| Allocation | Adjusting the stack pointer, once per call for all locals | A call into the allocator (`operator new`, `malloc`) that searches its free lists, may take a lock, and may ask the OS for pages |
| Release | Automatic at scope exit, reverse order | Explicit (`delete`) or by an owner such as `std::unique_ptr` or `std::vector` |
| Size limit | Small and fixed per thread: the Linux main thread's limit is `ulimit -s`, 8 MiB by default; MSVC links a 1 MiB default | Limited by available virtual memory |
| Size known | At compile time (VLAs are not standard C++) | At run time |
| Lifetime control | Tied to the scope | Any lifetime you arrange |
| Failure mode | Stack overflow, usually `SIGSEGV` | `std::bad_alloc` (or `nullptr` with `std::nothrow`) |
| Typical bugs | Pointer or reference to a returned local | Leaks, double `delete`, use after free |

Heap allocation costs more than stack allocation, but by how much depends on the allocator, the
size and the access pattern, so measure rather than assume a ratio. Default to automatic storage.
Use dynamic storage when the size is known only at run time or is too large for the stack, when the
object must outlive its scope, or when its dynamic type is chosen at run time, and let an owning
type manage it.

The addresses below show the layout on a typical Linux run. Absolute values change every run
(address-space layout randomization); the relative order is what to look at.

```cpp title="regions.cpp" showLineNumbers
#include <cstdio>
#include <memory>

int initialized = 42;          // .data
int zeroed;                    // .bss

int main() {
    int local = 1;                          // stack
    auto heap = std::make_unique<int>(2);   // the int is on the heap, `heap` itself on the stack
    std::printf("data  %p\nbss   %p\nheap  %p\nstack %p\n",
                static_cast<void*>(&initialized), static_cast<void*>(&zeroed),
                static_cast<void*>(heap.get()), static_cast<void*>(&local));
}
```

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
   **zero-initialized** (see [Value initialization](./initialization/value-initialization.md)).
   Then, if the object has a constant initializer, **constant initialization** gives it that
   value, usually baked into `.data` by the compiler.
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

- Four durations: automatic (scope), static (program), thread (thread), dynamic (until `delete`). Stack, heap and `.data`/`.bss` are how typical implementations provide them, not part of the standard.
- Statics are zero-initialized first, then constant or dynamic initialized. Only dynamic
  initialization has ordering problems.
- `constinit` *(C++20)* and function-local statics remove cross-file order dependencies.
- Destruction is always in reverse order of construction, for both automatic and static objects.
