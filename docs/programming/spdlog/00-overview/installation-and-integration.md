---
id: installation-and-integration
title: Installation and integration
sidebar_label: Installation
sidebar_position: 2
tags: [c++, spdlog, install, cmake, build]
---

# Installation and integration

The header-only default is what makes spdlog trivial to adopt — copy a directory, add an include
path, done. It's also what makes a large project's incremental compile times worse, because every
translation unit that includes `spdlog.h` re-parses (and re-instantiates) all of it. The compiled
mode exists for exactly that trade-off.

## Header-only

Copy or vendor the `include/spdlog` directory into your project, add it to your include path, and
you're done:

```cpp
#include "spdlog/spdlog.h"
```

No linking, no build step. This is the right default for small projects, examples, and anything
where compile time isn't yet a problem.

## Compiled mode

Define `SPDLOG_COMPILED_LIB` and build `spdlog` as a static or shared library instead. In CMake terms
that's the difference between linking against the `spdlog::spdlog` target (compiled) and
`spdlog::spdlog_header_only` (header-only) — both are provided by the project's CMake config.

What compiled mode buys you: each translation unit only sees declarations, not the full
implementation, so incremental builds get noticeably faster once you have more than a handful of
files including spdlog. What it costs: an actual build/link step, and an ABI contract between the
compiled library and your code (same compiler, same standard library, same `SPDLOG_ACTIVE_LEVEL` —
see [Compile-time log level](../06-performance-and-configuration/compile-time-log-level.md)).

## CMake: find_package

If spdlog is installed on the system (via a package manager or `cmake --install`):

```cmake showLineNumbers title="CMakeLists.txt"
find_package(spdlog REQUIRED)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE spdlog::spdlog)   # compiled
# target_link_libraries(app PRIVATE spdlog::spdlog_header_only)  # header-only
```

## CMake: FetchContent

When you don't want to assume spdlog is installed, pull it in at configure time:

```cmake showLineNumbers title="CMakeLists.txt"
include(FetchContent)
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.14.1
)
FetchContent_MakeAvailable(spdlog)

target_link_libraries(app PRIVATE spdlog::spdlog)
```

See [FetchContent](../../cmake/03-dependencies/fetchcontent.md) for the general mechanism this
builds on.

## vcpkg and Conan

```bash
vcpkg install spdlog
```

```bash
conan install spdlog/1.14.1@
```

Both packages expose the same `spdlog::spdlog` / `spdlog::spdlog_header_only` targets, so the
`find_package` block above doesn't change regardless of which one provided the package.

## The bundled fmt

spdlog vendors a copy of fmt by default (`spdlog/fmt/bundled/`), so you don't need a separate fmt
install to get started. Define `SPDLOG_FMT_EXTERNAL` to use your own fmt installation instead — useful
when another dependency in your project already pulls in fmt and you want one copy, not two.

:::danger[Mixing a vendored fmt and an external fmt in one binary causes ODR violations]
If one translation unit links against spdlog's bundled fmt and another links against a system fmt,
you can end up with two different definitions of the same fmt symbols in one binary. Pick one mode
(`SPDLOG_FMT_EXTERNAL` or not) and apply it consistently across every target that touches spdlog.
:::

## Which mode should I use?

| | Header-only | Compiled lib |
|---|---|---|
| Compile time | Slower per TU, no link step | Faster per TU, one link step |
| Distribution | Copy headers, nothing to build | Ship or build a `.a`/`.so`/`.lib` |
| ABI | N/A — always recompiled together | Must match compiler/stdlib/`SPDLOG_ACTIVE_LEVEL` |
| Best for | Small projects, quick integration | Large projects, many TUs including spdlog |

:::note[Start header-only, switch when compile time hurts]
There's no reason to reach for compiled mode on day one. Switch when `spdlog.h` shows up meaningfully
in your build-time profile.
:::

## See also

- <Icon icon="lucide:info" inline /> [What is spdlog?](./what-is-spdlog.md) — the architecture these install modes plug into.
- <Icon icon="lucide:rocket" inline /> [Quick start](../01-basics/quick-start.md) — first program once it's installed.
- <Icon icon="lucide:package" inline /> [find_package](../../cmake/03-dependencies/find-package.md) — the general CMake mechanism used above.
- <Icon icon="lucide:download-cloud" inline /> [FetchContent](../../cmake/03-dependencies/fetchcontent.md) — pulling in a dependency without a system install.
- <Icon icon="lucide:book-open" inline /> [spdlog overview](../readme.md).
