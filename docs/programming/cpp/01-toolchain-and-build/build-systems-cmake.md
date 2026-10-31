---
id: build-systems-cmake
title: Build Systems and CMake
sidebar_label: Build Systems & CMake
sidebar_position: 12
tags: [c++, build-systems, cmake, make, automation]
---

# Build Systems and CMake

Running the [pipeline](./compilation-pipeline.md) by hand stops working at about three files. Every
`.cpp` needs the same flags, only the files affected by an edit should be rebuilt, a header change
must rebuild every TU that includes it, and libraries have to be linked in the right order. A
**build system** does that: it keeps a graph of which outputs depend on which inputs and runs the
minimum set of compiler and linker commands to bring the outputs up to date.

This page is the toolchain view: what a build system does with the compiler, and how CMake maps
onto the stages. How to *write* CMake is covered in its own section, the
[CMake knowledge base](../../cmake/readme.md).

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md),
[Linking](./linking.md).

## What a build system tracks

<Diagram title="The dependency graph for the two-file program" caption="Touching square.h makes both objects and the executable out of date; touching square.cpp only square.o and app." accent="blue">
  <DiagramRow>
    <DiagramNode icon="file-text" title="main.cpp" />
    <DiagramNode icon="file-text" title="square.h" accent>Included by both</DiagramNode>
    <DiagramNode icon="file-text" title="square.cpp" />
  </DiagramRow>
  <DiagramArrow label="compile (one command per .cpp)" />
  <DiagramRow>
    <DiagramNode icon="binary" title="main.o" />
    <DiagramNode icon="binary" title="square.o" />
  </DiagramRow>
  <DiagramArrow label="link" />
  <DiagramNode icon="cpu" title="app" />
</Diagram>

The `.cpp` → `.o` edges are declared by you. The header edges are discovered from the compiler:
`-MD`/`-MMD` makes GCC and Clang write a small dependency file while compiling, listing every header
the TU opened ([GCC: Preprocessor Options](https://gcc.gnu.org/onlinedocs/gcc/Preprocessor-Options.html)):

```bash
g++ -MMD -MP -c main.cpp      # writes main.d next to main.o
cat main.d
```

```text
main.o: main.cpp square.h
square.h:
```

`-MMD` omits system headers; `-MP` adds the empty `square.h:` rule so that deleting a header does
not break the build. The build tool reads these files on the next run. Independent nodes (the two
compiles) run in parallel.

## Generators and build tools

Build systems come in two layers:

| Layer | Examples | Role |
|---|---|---|
| **Build tool** | [Make](./makefiles.md), Ninja, MSBuild | Executes a graph of commands; compares timestamps |
| **Generator / meta-build** | CMake, Meson, Premake | Reads a high-level project description and writes the build tool's input for the current platform and compiler |
| Integrated | Bazel, Buck2, build2 | Both layers in one tool, usually with hermetic, cacheable actions |

CMake is the most widely used generator for C++, and most libraries ship CMake package files, so
this knowledge base uses it. Ninja is a build tool designed to be generated, not hand-written; it is
the usual pairing with CMake on all platforms.

## CMake from the compiler's point of view

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.20)
project(squares LANGUAGES CXX)

add_executable(app main.cpp square.cpp)
target_compile_features(app PRIVATE cxx_std_23)
target_compile_options(app PRIVATE -Wall -Wextra)
```

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release    # configure: generate build/build.ninja
cmake --build build -- -v                                  # build, printing each command
```

These are the commands CMake 4.2 generated (paths shortened; the link line also had a `-Wl,--dependency-file=…` option, removed here):

```text
[1/3] /usr/bin/c++ -O3 -DNDEBUG -std=gnu++23 -Wall -Wextra -MD -MT CMakeFiles/app.dir/main.cpp.o -MF CMakeFiles/app.dir/main.cpp.o.d -o CMakeFiles/app.dir/main.cpp.o -c main.cpp
[2/3] /usr/bin/c++ -O3 -DNDEBUG -std=gnu++23 -Wall -Wextra -MD -MT CMakeFiles/app.dir/square.cpp.o -MF CMakeFiles/app.dir/square.cpp.o.d -o CMakeFiles/app.dir/square.cpp.o -c square.cpp
[3/3] /usr/bin/c++ -O3 -DNDEBUG CMakeFiles/app.dir/main.cpp.o CMakeFiles/app.dir/square.cpp.o -o app
```

Each part of the CMake file became a compiler flag for a specific stage:

| CMake | Became | Stage |
|---|---|---|
| `add_executable(app main.cpp square.cpp)` | one `-c` command per source, one link command | all |
| `CMAKE_BUILD_TYPE=Release` | `-O3 -DNDEBUG` | compile, preprocess |
| `target_compile_features(… cxx_std_23)` | `-std=gnu++23` (GNU extensions on; set `CMAKE_CXX_EXTENSIONS OFF` for `-std=c++23`) | compile |
| `target_compile_options` | `-Wall -Wextra` | compile |
| (automatic) | `-MD -MT … -MF ….o.d` | dependency discovery |
| `target_include_directories` | `-I` / `-isystem` | preprocess |
| `target_link_libraries` | library paths and `-l…`, in dependency order | link |

The incremental behaviour, from the same build directory:

<Tabs>
  <TabItem value="h" label="touch square.h">

```text
[1/3] Building CXX object CMakeFiles/app.dir/square.cpp.o
[2/3] Building CXX object CMakeFiles/app.dir/main.cpp.o
[3/3] Linking CXX executable app
```

  </TabItem>
  <TabItem value="cpp" label="touch square.cpp">

```text
[1/2] Building CXX object CMakeFiles/app.dir/square.cpp.o
[2/2] Linking CXX executable app
```

  </TabItem>
</Tabs>

Note that the Release type gives `-O3`, not `-O2`; see [CMake build types](../../cmake/01-basics/build-types.md)
if you want to change the defaults.

### Where to read further

| Topic | Page |
|---|---|
| First project, configure/build/install | [First Project](../../cmake/00-intro/first-project.md) |
| Targets and `PUBLIC`/`PRIVATE` usage requirements | [Linking (CMake)](../../cmake/02-targets/linking.md), [Target Properties](../../cmake/02-targets/target-properties.md) |
| Debug/Release and other configurations | [Build Types](../../cmake/01-basics/build-types.md) |
| Shared settings across machines | [Presets](../../cmake/01-basics/presets.md) |
| Third-party libraries | [find_package](../../cmake/03-dependencies/find-package.md), [FetchContent](../../cmake/03-dependencies/fetchcontent.md), [Package Managers](./package-managers.md) |
| Building for another architecture | [Cross-Compilation](./cross-compilation.md) |
| C++20 modules | [Modules](./modules.md#building-modules) |

## `compile_commands.json`

Configure with `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` and CMake writes `build/compile_commands.json`,
one entry per TU with its exact compiler command. clangd, clang-tidy, include-what-you-use and most
IDEs read it to understand the code exactly as the compiler does. Link it into the source root so
tools find it.

## Pitfalls

- **Building in the source directory.** Use a separate build directory (`-B build`); it can be
  deleted to start clean, and several configurations can coexist.
- **Global flags (`CMAKE_CXX_FLAGS`, `add_compile_options`, `include_directories`) instead of
  `target_*`.** They apply to everything, including dependencies, and hide which target needs what.
- **Globbing sources (`file(GLOB …)`).** CMake does not notice new files until it re-runs configure.
  List sources explicitly, or use `CONFIGURE_DEPENDS` and accept the cost.
- **Editing generated files.** `build.ninja` and Makefiles in the build directory are overwritten on
  the next configure.

## Key points

- A build system is a dependency graph plus the minimum commands to update it; the compiler supplies
  header dependencies with `-MD`.
- CMake generates the graph for a build tool (usually Ninja); every `target_*` command becomes a flag
  for a particular pipeline stage.
- `cmake --build build -- -v` shows the real compiler commands; `compile_commands.json` gives them to
  tools.
