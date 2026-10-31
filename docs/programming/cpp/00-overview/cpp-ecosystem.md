---
id: cpp-ecosystem
title: The C++ Ecosystem
sidebar_label: C++ Ecosystem
sidebar_position: 4
tags: [c++, ecosystem, tools, libraries, overview]
---

# The C++ Ecosystem

The C++ standard defines a language and its standard library, and nothing else: no compiler, build
system, package manager or test runner is official. A working C++ setup is something you assemble.
This page maps each tool layer, lists the common choices with how they differ, and links to the
page in this knowledge base that covers each one. Read it to get oriented. The linked pages have
the detail.

**Prerequisites:** [What is C++?](./what-is-cpp.md)

<Diagram title="The layers of a C++ toolchain" caption="You pick one tool per layer; they communicate through files (CMakeLists.txt, compile_commands.json, object files)." accent="green">
  <DiagramNode icon="monitor" title="Editor / IDE">Code completion, navigation, debugging UI</DiagramNode>
  <DiagramArrow label="drives" />
  <DiagramRow>
    <DiagramNode icon="package" title="Package manager">Fetches and builds dependencies</DiagramNode>
    <DiagramArrow direction="right" label="feeds" />
    <DiagramNode icon="hammer" title="Build system" accent>Decides what to compile, in which order</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="invokes" />
  <DiagramNode icon="cpu" title="Compiler + linker">Turns sources into a binary</DiagramNode>
  <DiagramArrow label="checked by" />
  <DiagramGroup label="Quality tools">
    <DiagramNode icon="flask-conical" title="Tests" />
    <DiagramNode icon="bug" title="Sanitizers & debuggers" />
    <DiagramNode icon="filter" title="Static analysis" />
  </DiagramGroup>
</Diagram>

## Compilers

| Compiler | Where it's the default | Notes |
|---|---|---|
| **GCC** (`g++`) | Most Linux distributions, many embedded toolchains | Wide range of target architectures |
| **Clang** (`clang++`) | macOS (as Apple Clang), Android NDK, FreeBSD | Built on LLVM. Also the base for clangd, clang-tidy and clang-format. |
| **MSVC** (`cl`) | Windows with Visual Studio | Different flag syntax (`/W4`, `/std:c++20`) and its own ABI |

All three implement the same standard, but they differ in which features they support and when, in
their warnings, and in their extensions. Building with two compilers in CI catches code that is
less portable than it looks. What the compiler does internally is covered in
[The Compilation Pipeline](../01-toolchain-and-build/compilation-pipeline.md).

## Build systems

| Tool | Use it when |
|---|---|
| **CMake** | Almost always. It is the de facto standard, and most libraries ship CMake support. It generates Ninja, Make or Visual Studio builds. |
| **Make** | Small projects, or reading older ones |
| **Meson** | You prefer a smaller, stricter language and the project doesn't need CMake interop |
| **Bazel** | Large monorepos that need hermetic, cached builds |

Covered in [Build Systems: CMake](../01-toolchain-and-build/build-systems-cmake.md) and
[Makefiles](../01-toolchain-and-build/makefiles.md). The [CMake section](../../cmake/readme.md)
teaches CMake in depth.

## Package managers

C++ has no built-in package manager. The two common ones are **vcpkg** (from Microsoft, with a curated
port registry and CMake toolchain-file integration) and **Conan** (from JFrog, with recipes,
prebuilt binaries and lockfiles). Many projects instead fetch dependencies from source with CMake's
`FetchContent`. All three are compared in
[Package Managers](../01-toolchain-and-build/package-managers.md).

## Editors and IDEs

| Tool | Notes |
|---|---|
| **Visual Studio** | The full Windows IDE: MSVC, debugger and profiler in one |
| **CLion** | JetBrains' cross-platform IDE, built around CMake |
| **VS Code**, Neovim, Emacs… | Use the **clangd** language server for completion and diagnostics |

Whichever you choose, code intelligence needs to know your compile flags. Clang-based tools read
them from `compile_commands.json`, which CMake writes when `CMAKE_EXPORT_COMPILE_COMMANDS=ON`.

## Quality tools

| Need | Tools | Covered in |
|---|---|---|
| Catch mistakes at compile time | Compiler warnings (`-Wall -Wextra`, `/W4`) | [Compilation](../01-toolchain-and-build/compilation.md) |
| Static analysis | clang-tidy, cppcheck | — |
| Formatting | clang-format | — |
| Runtime memory and UB errors | AddressSanitizer, UndefinedBehaviorSanitizer, ThreadSanitizer, Valgrind | [Sanitizers](../14-debugging-and-profiling/04-sanitizers.md), [Valgrind](../14-debugging-and-profiling/05-valgrind.md) |
| Debugging | GDB, LLDB, the Visual Studio debugger | [GDB](../14-debugging-and-profiling/02-gdb.md) |
| Profiling | `perf`, Valgrind's Callgrind | [Perf Tools](../14-debugging-and-profiling/06-perf-tools.md) |
| Unit tests | GoogleTest/GoogleMock, Catch2, doctest | [GoogleTest Basics](../15-testing/01-gtest-basics.md) |
| API documentation | Doxygen | — |

**Recommended baseline** for a new project: CMake, warnings on and treated seriously, a debug
build with AddressSanitizer and UBSan, clang-format, and one test framework in CI. Each piece takes
minutes to set up and finds bugs early, while they are still cheap to fix.

## Libraries

- **The standard library** comes with every compiler: containers, algorithms, strings, threads,
  filesystem and more. See [Standard Library](../09-standard-library/containers.md).
- **Boost** is a large collection of peer-reviewed libraries. Several standard features (smart
  pointers, `optional`, `filesystem`) started there. See [Boost](../../boost/readme.md).
- **Focused libraries** documented here: [fmt](../../fmt/readme.md) (formatting, the basis of
  `std::format`), [spdlog](../../spdlog/readme.md) (logging) and
  [nlohmann/json](../../nlohmann-json/readme.md) (JSON).

## Reference sites

- [cppreference.com](https://en.cppreference.com): the standard language and library reference,
  with version annotations.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/): guidance on writing modern
  C++, edited by Stroustrup and Sutter.
- [Compiler Explorer](https://godbolt.org): compile a snippet with many compilers and read the
  assembly.
- [isocpp.org](https://isocpp.org): the standard committee's news and status.
