---
id: modules
title: Modules (C++20)
sidebar_label: Modules
sidebar_position: 15
tags: [c++, modules, cpp20, build, compilation]
---

# Modules (C++20)

Modules *(C++20)* replace textual inclusion for sharing declarations between translation units.
Instead of the preprocessor pasting a header's text into every TU that uses it, a module's
interface is **compiled once** into a binary module interface (BMI), and other TUs `import` it. That
removes three long-standing problems of headers: the same text reparsed in every TU, macros leaking
in both directions, and results that depend on include order.

**Prerequisites:** [Headers and Includes](./headers-and-includes.md) and
[Translation Units](./translation-units.md): the model that modules replace.

<Diagram title="Headers vs modules" accent="green">
  <DiagramRow>
    <DiagramGroup label="#include">
      <DiagramNode icon="file-text" title="lib.h">Text</DiagramNode>
      <DiagramNode title="a.cpp, b.cpp, c.cpp">Each pastes and reparses the text</DiagramNode>
    </DiagramGroup>
    <DiagramGroup label="import">
      <DiagramNode icon="file-text" title="lib.cppm">Compiled once</DiagramNode>
      <DiagramNode icon="binary" title="BMI" accent>Compiler-specific binary interface</DiagramNode>
      <DiagramNode title="a.cpp, b.cpp, c.cpp">Each loads the BMI</DiagramNode>
    </DiagramGroup>
  </DiagramRow>
</Diagram>

## A module in two files

```cpp title="math.cppm"
export module math;          // this file is the interface of module 'math'

export int add(int a, int b) { return a + b; }

int helper() { return 42; }  // not exported: invisible to importers
```

```cpp title="main.cpp"
import math;

int main() { return add(2, 3); }
```

The file extension is not standardised: Clang and CMake use `.cppm`, MSVC uses `.ixx`, and GCC
accepts any extension if told it is C++ (`-x c++`).

Using an unexported name is an ordinary lookup error (GCC 15):

```text
priv.cpp:2:21: error: ‘helper’ was not declared in this scope
```

## Building modules

The new constraint is ordering: the interface must be compiled (producing the BMI) **before** any TU
that imports it. With headers, every TU could be compiled in any order.

<Tabs groupId="compiler">
  <TabItem value="gcc" label="GCC 15">

```bash
g++ -std=c++23 -fmodules -x c++ -c math.cppm -o math.o   # also writes gcm.cache/math.gcm
g++ -std=c++23 -fmodules -c main.cpp -o main.o            # reads gcm.cache/math.gcm
g++ main.o math.o -o app
./app; echo $?                                            # 5
```

  </TabItem>
  <TabItem value="clang" label="Clang 21">

```bash
clang++ -std=c++23 --precompile math.cppm -o math.pcm      # the BMI
clang++ -std=c++23 -fmodule-file=math=math.pcm main.cpp math.pcm -o app
./app; echo $?                                             # 5
```

  </TabItem>
  <TabItem value="cmake" label="CMake 3.28+ with Ninja">

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.28)
project(mods LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 23)

add_executable(app main.cpp)
target_sources(app PRIVATE FILE_SET CXX_MODULES FILES math.cppm)
```

```bash
cmake -S . -B build -G Ninja && cmake --build build
```

CMake scans every source for `import`/`export module` and orders the compiles; this needs the Ninja
or Visual Studio generator ([CMake: C++ modules](https://cmake.org/cmake/help/latest/manual/cmake-cxxmodules.7.html)).

  </TabItem>
</Tabs>

All three were run on this page's machine and the program returns 5. The BMI is a build artifact
tied to the exact compiler, version and relevant flags. It is not a distributable format: libraries
ship the `.cppm` source, and each user's build compiles its own BMI.

## What `export` controls

Only exported declarations are visible to importers. Everything else in the module has **module
linkage**: visible in all files of the same module, invisible outside it.

```cpp title="widget.cppm (fragment)"
export module widget;

export class Widget { /* ... */ };   // public interface
export void configure(Widget&);

namespace detail {                   // not exported: module-internal
    int compute();
}

export namespace widget_api {        // export everything inside
    void reset();
}
```

Macros never cross an `import`: a `#define` inside a module interface does not reach importers, and
importers' macros don't affect the module. Code that needs to export configuration macros still
needs a small header.

Larger modules are split into **partitions** (`export module widget:parts;`, imported inside the
module as `import :parts;`) and **implementation units** (`module widget;` without `export`), which
mirror the header/source split: changing an implementation unit does not change the BMI, so
importers do not rebuild.

### Existing headers

- **Global module fragment.** A module that still needs `#include`s puts them before the module
  declaration:

  ```cpp title="fragment"
  module;                  // global module fragment starts
  #include <cstdio>        // ordinary textual inclusion, not exported
  export module logging;
  ```

- **Header units.** `import <vector>;` treats a header as a module. Build-system support is less
  mature than for named modules.

## `import std;` (C++23)

C++23 provides the whole standard library as the named module `std` (and `std.compat`, which also
puts the C library names in the global namespace):

```cpp title="std.cpp"
import std;

int main() {
    std::vector<int> v{1, 2, 3};
    std::println("{}", v.size());
}
```

The standard library's module must be compiled once per configuration, like any other module:

```bash
g++ -std=c++23 -fmodules -fsearch-include-path -c bits/std.cc    # GCC 15: builds gcm.cache/std.gcm
g++ -std=c++23 -fmodules std.cpp -o stdapp && ./stdapp
```

```text
3
```

CMake 4.2 can do this for you with `set(CMAKE_CXX_MODULE_STD ON)`, which at the time of writing
is still behind an experimental flag (`CMAKE_EXPERIMENTAL_CXX_IMPORT_STD`). Tested here with GCC 15;
other toolchains need their own setup.

## Trade-offs

| | Headers | Modules |
|---|---|---|
| Parsing cost | Every TU reparses every header | Interface compiled once; imports load the BMI |
| Encapsulation | Everything in the header is visible | Only `export`ed names |
| Macros | Leak both ways | Do not cross `import` |
| Build ordering | Any order | Interfaces first; the build system must scan for dependencies |
| Tool support | Universal | Compilers and CMake/Ninja work; IDEs, static analysers, and package managers are still catching up |
| Distribution | Ship headers | Ship interface sources; BMIs are rebuilt by each consumer |

How much faster a build becomes depends on how much header text the project reparses today. Measure
your own project. A mixed approach is normal: new code as modules, third-party code still through
headers (or the global module fragment).

## Pitfalls

- **Expecting the BMI to be portable.** A GCC `.gcm` cannot be read by Clang, nor by another GCC
  version or with incompatible flags. Never commit or ship BMIs.
- **Using a generator without module support.** CMake's Makefile generator does not support named
  modules; use Ninja.
- **Circular imports.** Two module interfaces cannot import each other; restructure with partitions
  or a third module.
- **Macro-based configuration.** `#ifdef FEATURE` around exported declarations only sees macros
  defined when the *module* was compiled, not in the importer.

## Key points

- A module is compiled once into a BMI and imported; text is no longer pasted.
- `export` defines the interface; non-exported names have module linkage; macros never cross
  `import`.
- Interfaces must be built before importers, so the build system scans sources for dependencies.
- `import std;` *(C++23)* works with GCC 15 and CMake once the std module has been built.

## References

- [cppreference: Modules](https://en.cppreference.com/w/cpp/language/modules)
- [CMake: cmake-cxxmodules(7)](https://cmake.org/cmake/help/latest/manual/cmake-cxxmodules.7.html)
