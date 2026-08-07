---
id: installation-and-integration
title: Installation and integration
sidebar_label: Installation
sidebar_position: 2
tags: [c++, nlohmann-json, install, cmake, build]
---

# Installation and integration

There isn't one right way to add nlohmann/json to a project — there's a spectrum from "copy one
file into the repo" to "declare a proper package dependency", and the right point on that spectrum
depends on how much you value zero-setup portability versus reproducible, versioned builds.

## The single header

The simplest integration is a single generated header, `json.hpp`, that contains the entire
library. Download it, put it under your include path, and `#include <nlohmann/json.hpp>` — no
build system changes, no submodules, nothing to configure.

The cost is compile time: every translation unit that includes it re-parses roughly 25,000 lines of
template-heavy C++. On a small project this is unnoticeable; on a large one it adds up, which is
part of why the library also ships as a split header tree (below).

## The include/ tree

The `include/nlohmann/` tree splits the implementation into `json.hpp` plus a set of detail
headers, and — importantly — also provides `nlohmann/json_fwd.hpp`, a forward-declaration-only
header. If a header in your project only needs to name `nlohmann::json` (as a parameter or member
type) without calling any of its methods, including `json_fwd.hpp` instead of the full `json.hpp`
avoids dragging the whole implementation into every file that includes that header.

```cpp
// some_widget.hpp — only needs the type name
#include <nlohmann/json_fwd.hpp>

class Widget {
public:
    explicit Widget(const nlohmann::json& config);
private:
    nlohmann::json config_;
};
```

The corresponding `.cpp` file includes the full `<nlohmann/json.hpp>` where the methods are
actually used. This is the same forward-declaration discipline you'd apply to any heavy header —
it just matters more here because `json.hpp` is unusually large.

## CMake: find_package

If nlohmann/json is installed system-wide or via a package manager that provides CMake config
files, `find_package` is the least code:

```cmake showLineNumbers title="CMakeLists.txt"
find_package(nlohmann_json 3.11 REQUIRED)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE nlohmann_json::nlohmann_json)
```

`nlohmann_json::nlohmann_json` is a header-only `INTERFACE` target — linking it does nothing more
than add the include path, but it does that correctly for every consumer transitively, which a
hand-written `include_directories()` call does not.

## CMake: FetchContent

When you don't want an external install step at all, `FetchContent` downloads and configures the
library as part of your own build:

```cmake showLineNumbers
include(FetchContent)

FetchContent_Declare(
    json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
)
FetchContent_MakeAvailable(json)

target_link_libraries(app PRIVATE nlohmann_json::nlohmann_json)
```

This is a good default for reproducible builds — the version is pinned in your `CMakeLists.txt`
rather than depending on whatever happens to be installed on the build machine. See
[FetchContent](../../cmake/03-dependencies/fetchcontent.md) for the general pattern and its caveats
(mainly: first-configure network access).

## vcpkg and Conan

Both major C++ package managers carry it under a package name close to the project name:

```bash
vcpkg install nlohmann-json
```

```bash
conan install . --requires=nlohmann_json/3.11.3 --build=missing
```

Either way you still finish with a `find_package(nlohmann_json)` in your `CMakeLists.txt` — the
package manager's job is only to make that call succeed.

## Which one should I use?

| Method | Best for | Cost |
|---|---|---|
| Single header, vendored | Small projects, quick prototypes, no build-system access | Compile time, manual updates |
| `include/` tree, vendored | Slightly larger projects wanting `json_fwd.hpp` | Same manual-update problem |
| `find_package` | Projects where the library is already installed/provisioned | Requires an install step outside CMake |
| `FetchContent` | Reproducible builds, CI, "just clone and build" | First-configure network fetch |
| vcpkg / Conan | Projects already standardized on that package manager | Extra tooling dependency |

:::note[Default recommendation]
Unless the project already has a package manager convention, reach for `FetchContent` with a pinned
version tag. It gives you a reproducible, network-fetched dependency without requiring contributors
to install anything beforehand, and it's a two-line change to switch to `find_package` later if the
library ends up vendored by the system or a package manager.
:::

## See also

- <Icon icon="lucide:book-open" inline /> [What is nlohmann/json?](./what-is-nlohmann-json.md) — the two integration shapes at a glance.
- <Icon icon="lucide:file-json" inline /> [Parsing JSON](../01-basics/parsing-json.md) — the first thing you'll do once it's linked in.
- <Icon icon="lucide:search" inline /> [find_package](../../cmake/03-dependencies/find-package.md) — the general CMake mechanism this section relies on.
- <Icon icon="lucide:download-cloud" inline /> [FetchContent](../../cmake/03-dependencies/fetchcontent.md) — the general CMake mechanism behind the recommended default.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
