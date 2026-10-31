---
id: what-is-cpp
title: What is C++?
sidebar_label: What is C++
sidebar_position: 1
tags: [ c++, overview, introduction, history ]
---

# What is C++?

C++ is a statically typed, compiled, general-purpose language. Its design bet is that you can have
high-level abstractions (classes, templates, containers, algorithms) without giving up the control
and speed of C: the abstractions are resolved at compile time and become ordinary machine code,
with no virtual machine or garbage collector underneath. That bet explains both why C++ is used
where performance and hardware control matter, and why it is a large, demanding language.

This page covers where C++ came from, the ideas that shape it, what it costs, and how a program
gets built. Everything here is a summary. Each topic links to the page that covers it in full.

## Origins

| Year | Event |
|---|---|
| 1979 | Bjarne Stroustrup starts "C with Classes" at Bell Labs: C plus Simula-style classes. |
| 1983 | Renamed C++ (`++` is C's increment operator). |
| 1985 | First commercial release (the Cfront compiler) and *The C++ Programming Language*, 1st edition. |
| 1998 | First ISO standard, C++98. |
| 2011 | C++11, the start of what people call "modern C++". A new standard every three years since. |

The per-standard detail is in [C++ Versions](./cpp-versions.md).

## The ideas behind the language

### Zero-overhead abstraction

Stroustrup states the principle in two parts: *what you don't use, you don't pay for*, and *what you
do use, you couldn't hand-code any better*. A feature you don't use must cost nothing at runtime. A
feature you do use should compile to roughly what you would have written by hand.

```cpp showLineNumbers
#include <numeric>
#include <vector>

int sum_vector(const std::vector<int>& v) {
    return std::accumulate(v.begin(), v.end(), 0);   // generic algorithm + iterators
}

int sum_array(const int* p, std::size_t n) {
    int s = 0;
    for (std::size_t i = 0; i < n; ++i) s += p[i];   // the hand-written loop
    return s;
}
```

With optimisation on (`-O2`), GCC and Clang inline the iterator and template machinery in
`sum_vector`, which leaves a loop over the same memory as `sum_array`. Don't take that on trust:
paste both into [Compiler Explorer](https://godbolt.org) and compare the assembly.
[Reading Assembly](../14-debugging-and-profiling/07-reading-assembly.md) shows how.

The principle is a goal, not a guarantee. Some features have a cost you pay when you use them, such
as virtual dispatch, exceptions on the throw path, and `std::shared_ptr` reference counting. The
pages for those features say what the cost is.

### Close to the hardware

C++ keeps C's model of memory: objects have addresses, pointers are addresses, and you choose where
an object lives (stack, heap, static storage, or a buffer you manage). You can control object layout
and alignment and write to memory-mapped registers. That is why C++ fits operating-system
components, embedded firmware, game engines and anything with a latency budget. See
[Memory & Object Lifetime](../05-memory-and-object-lifetime/memory-model-overview.md) and
[Low-Level & Platform](../12-low-level-and-platform/01-abi.md).

### Deterministic cleanup

C++ has no garbage collector. Instead, an object's destructor runs at a known point: when the object
goes out of scope or is deleted. Tying a resource (memory, a file, a lock) to an object's lifetime is
called **RAII**, and it is the main way C++ code avoids leaks without a runtime. See
[RAII](../13-idioms-and-design/01-raii.md).

### Multi-paradigm

C++ doesn't push one style. Procedural code, classes with
[virtual functions](../07-classes-and-oop/virtual-functions.md),
[templates](../08-templates-and-metaprogramming/function-templates.md) for generic code, and
[lambdas](../07-classes-and-oop/lambdas.md) for functional style all mix freely, often in the same
function.

### Compatibility with C

Most C code compiles as C++, and C++ can call C libraries directly. This was a deliberate choice
for adoption, and the reason C++ inherits C's sharp edges. The two languages differ in more places
than people expect. See [C vs C++](./c-vs-cpp.md).

## What it costs

These trade-offs come from the same design choices:

- **Undefined behaviour.** Out-of-bounds access, signed overflow, use-after-free and data races are
  not checked. The program's behaviour is simply undefined, and the optimiser is allowed to assume
  they never happen. See [Undefined Behavior](../10-error-handling-and-safety/06-undefined-behavior.md).
- **Size.** Forty years of backward compatibility mean there are often several ways to do the same
  thing. Old and new styles coexist in real codebases, so you have to be able to read both.
- **Build times.** Headers are re-parsed in every translation unit, and templates are instantiated
  at compile time. [Modules](../01-toolchain-and-build/modules.md) (C++20) address the first problem.
- **No single toolchain.** The standard defines the language, not a build system or package
  manager. You assemble those yourself; [the ecosystem](./cpp-ecosystem.md) maps the usual choices.

## From source to running program

A C++ program is translated ahead of time into a native executable for one target platform:

<Diagram title="Building a C++ program" caption="Each .cpp file is compiled separately; the linker joins the results." accent="blue">
  <DiagramRow>
    <DiagramNode icon="file-text" title="Source">main.cpp, util.cpp + headers</DiagramNode>
    <DiagramArrow direction="right" label="compile each" />
    <DiagramNode icon="binary" title="Object files">main.o, util.o</DiagramNode>
    <DiagramArrow direction="right" label="link" />
    <DiagramNode icon="cpu" title="Executable" accent>Native machine code</DiagramNode>
  </DiagramRow>
</Diagram>

Each step is covered in [The Compilation Pipeline](../01-toolchain-and-build/compilation-pipeline.md).
For a single file, one command runs all of them:

```cpp title="hello.cpp"
#include <iostream>

int main() {
    std::cout << "Hello, C++!\n";
}
```

```bash
g++ -std=c++20 -Wall -Wextra -O2 hello.cpp -o hello
./hello
```

```text
Hello, C++!
```

- `-std=c++20` selects the language standard. See [C++ Versions](./cpp-versions.md#choosing-a-standard).
- `-Wall -Wextra` turns on the commonly useful warnings. Despite its name, `-Wall` is not every
  warning.
- `-O2` enables optimisation. Without it, the zero-overhead claims above don't hold.
- `main` is the program's entry point. Reaching the end of `main` without a `return` returns 0.

## Where C++ is used

C++ is common wherever performance, latency or hardware access decides the design. Projects whose
core is written in C++ include:

- **Browsers and compilers:** Chromium, Firefox (alongside Rust), LLVM/Clang, GCC (written in C++ since GCC 4.8).
- **Game engines:** Unreal Engine, and the runtime of Unity.
- **Machine learning:** the cores of PyTorch and TensorFlow, which expose Python APIs.
- **Databases:** MySQL, MongoDB, ClickHouse.

Many other systems are written in C rather than C++, including the Linux kernel and PostgreSQL.

## Where to go next

- [C vs C++](./c-vs-cpp.md): read this next if you know C.
- [C++ Versions](./cpp-versions.md): which standard added what, and which one to use.
- [The C++ Ecosystem](./cpp-ecosystem.md): compilers, build systems, libraries and tools.
- [The Compilation Pipeline](../01-toolchain-and-build/compilation-pipeline.md): the start of the
  main reading path.

## References

- Bjarne Stroustrup, [FAQ](https://www.stroustrup.com/bs_faq.html): history and design aims, in the
  author's words.
- Bjarne Stroustrup, *The Design and Evolution of C++* (1994): source of the zero-overhead
  principle.
- [isocpp.org: The Standard](https://isocpp.org/std/the-standard): how C++ is standardised.
