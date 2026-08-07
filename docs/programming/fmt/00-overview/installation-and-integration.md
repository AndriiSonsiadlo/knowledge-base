---
id: installation-and-integration
title: Installation and integration
sidebar_label: Installation
sidebar_position: 2
tags: [c++, fmt, install, cmake, build]
---

# Installation and integration

fmt can be dropped into a project as header-only, with no build step at all, or built and linked as
a small compiled library. The choice is entirely about compile time, not about functionality — every
public API is identical either way.

## Header-only

Define `FMT_HEADER_ONLY` before the first `#include <fmt/format.h>`, or link the
`fmt::fmt-header-only` CMake target, which defines it for you. There is nothing to build and nothing
to link — fmt's implementation is included and instantiated in every translation unit that uses it.
The trade-off is compile time: every TU that formats anything pays for instantiating fmt's internals
from scratch.

## Compiled

The default CMake target is `fmt::fmt`. fmt's implementation is built once into a static (or shared)
library, and every translation unit just links against the already-compiled symbols.

```cmake showLineNumbers title="CMakeLists.txt"
find_package(fmt REQUIRED)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE fmt::fmt)
```

## CMake: FetchContent

If fmt isn't installed system-wide, pull a pinned release with `FetchContent` instead of
`find_package`:

```cmake showLineNumbers
include(FetchContent)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG        11.0.2
)
FetchContent_MakeAvailable(fmt)

target_link_libraries(app PRIVATE fmt::fmt)
```

See [FetchContent](../../cmake/03-dependencies/fetchcontent.md) for the general pattern this
follows, including how to override it with a system package when one is available.

## vcpkg and Conan

```bash
vcpkg install fmt
```

```bash
conan install fmt/11.0.2@
```

Both produce the same `fmt::fmt` target for `find_package(fmt)` to pick up; neither changes anything
about how you write code against fmt.

## Version pinning

:::danger[fmt has made source-breaking changes across major versions — pin a version, do not track master]
Format-spec behavior, header names, and even default output (quoted strings in containers, for
example) have changed between major releases. Pin an exact tag in `FetchContent`/vcpkg/Conan and
bump it deliberately, with the changelog open, rather than floating on `master` or `*`.
:::

## Coexisting with spdlog

spdlog vendors its own copy of fmt by default so it has zero external dependencies. If your project
also links its own fmt, you now have two independent copies of fmt's symbols in one binary. Defining
`SPDLOG_FMT_EXTERNAL` when building spdlog makes it use your external fmt instead of its bundled one,
so the whole binary shares a single implementation.

:::danger[Two copies of fmt in one binary is an ODR violation waiting to happen]
Both copies define the same symbols under the same names. Whether the linker catches it, silently
picks one, or you get subtly wrong behavior at runtime depends on visibility settings and luck. Set
`SPDLOG_FMT_EXTERNAL` (or vendor consistently) rather than finding out which.
:::

## Which mode should I use?

| | Header-only | Compiled |
|---|---|---|
| Compile time per TU | Higher — reinstantiated everywhere | Lower — implementation built once |
| Link step | None | Requires linking `fmt::fmt` |
| Binary size | Larger if used from many TUs | Smaller — one implementation |
| Ease of vendoring | Trivial — copy headers | Needs a build step or package manager |

For anything beyond a handful of translation units, compiled mode is worth the one extra CMake line.
See [Header-only vs compiled mode](../06-performance-and-best-practices/header-only-vs-compiled-mode.md)
for the full comparison and the mechanics of why the compile-time gap grows with TU count.

## See also

- <Icon icon="lucide:sparkles" inline /> [What is fmt?](./what-is-fmt.md) — start here if you haven't decided to adopt fmt yet.
- <Icon icon="lucide:gauge" inline /> [Header-only vs compiled mode](../06-performance-and-best-practices/header-only-vs-compiled-mode.md) — the detailed compile-time comparison.
- <Icon icon="lucide:package-search" inline /> [find_package](../../cmake/03-dependencies/find-package.md) — how CMake locates an installed fmt.
- <Icon icon="lucide:download-cloud" inline /> [FetchContent](../../cmake/03-dependencies/fetchcontent.md) — pulling fmt as source when no system package exists.
- <Icon icon="lucide:book-open" inline /> [fmt overview](../readme.md) — the full doc set.
