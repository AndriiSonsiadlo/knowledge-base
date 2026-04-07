---
id: header-only-vs-compiled
title: Header-only vs Compiled Libraries
sidebar_label: Header-only vs Compiled
sidebar_position: 4
tags: [ c++, boost, build, linking ]
---

# Header-only vs Compiled Libraries

One of the first practical questions every Boost user hits is: *do I need to link anything?* The answer
is usually **no** — the large majority of Boost libraries are **header-only**, meaning you include a
header and you are done. But a meaningful minority carry code that must be **compiled into a library and
linked**, and forgetting to link them produces some of the most confusing errors a newcomer will see.

This page explains the split, lists the common offenders, and shows how to tell which kind a library is.

:::info The short version
Header-only: add an include path, write `#include <boost/...>`, compile. Done.
Compiled: do all of the above **and** link the matching `libboost_<name>` library.
:::

## Why most of Boost is header-only

Boost is built on templates, and template code generally has to live in headers — the compiler needs to
see the full definition to instantiate it for your specific types. A `boost::optional<MyType>` or a
`boost::container::flat_map<K, V>` is generated at *your* compile time, from source the header provides.
There is nothing to precompile and nothing to link.

This is why [installation](./installation.md) is often trivial: point the compiler at the header root and
the bulk of Boost is immediately usable.

```cpp showLineNumbers title="header_only.cpp"
#include <boost/optional.hpp>          // header-only
#include <boost/algorithm/string.hpp> // header-only
#include <iostream>

int main() {
    boost::optional<int> maybe = 7;
    if (maybe) std::cout << "value: " << *maybe << '\n';
}
```

```bash
# No -l flags: there is no library to link
g++ -std=c++17 -I/opt/boost/include header_only.cpp -o demo
```

## Why some libraries must be compiled

A library needs separate compilation when it contains **non-template code that must exist exactly once**
in your program, or when it depends on the operating system in ways a header cannot express:

- **Out-of-line implementation.** Functions that are not templates (and not marked `inline`) must be
  compiled into a single object somewhere — they cannot be re-emitted by every translation unit without
  causing duplicate-symbol errors.
- **Operating-system and runtime hooks.** Threads, filesystem syscalls, process control, and similar
  facilities wrap platform APIs that belong in a compiled unit.
- **Global state.** Some libraries (logging, serialization registries) maintain shared state that must
  be a single instance across the program.

If you `#include` such a library but forget to link it, the compile succeeds and the **linker** fails
with "undefined reference" / "unresolved external symbol" errors naming `boost::<something>`.

:::warning The classic newcomer error
`undefined reference to 'boost::filesystem::...'` does **not** mean Boost is missing or your include path
is wrong. It means you included a *compiled* library but did not link it. Add the matching
`-lboost_<name>` (or the `Boost::<component>` CMake target).
:::

## Common compiled libraries

The following libraries are the ones you will most often need to link. This list is representative, not
exhaustive, and a few entries have header-only modes (noted below).

| Library | Link name (typical) | What it does | Standardised as |
|---------|--------------------|--------------|-----------------|
| Filesystem | `boost_filesystem` | Paths, directory iteration, file ops | `std::filesystem` (C++17) |
| System | `boost_system` | Portable error codes; dependency of others | `std::error_code` (C++11) |
| Thread | `boost_thread` | Threads, mutexes, futures | `std::thread` (C++11) |
| Program_options | `boost_program_options` | Command-line and config parsing | — |
| Regex | `boost_regex` | Regular expressions | `std::regex` (C++11) |
| Serialization | `boost_serialization` | Object persistence to archives | — |
| Log | `boost_log`, `boost_log_setup` | Logging framework | — |
| Date_Time | `boost_date_time` | Dates, times, durations | partly `std::chrono` |
| Chrono | `boost_chrono` | Clocks and durations | `std::chrono` (C++11) |
| Iostreams | `boost_iostreams` | Filtering streams, compression | — |

:::note Header-only modes exist for a few
Some of these can be used header-only with extra defines or by including a different header — Boost.Regex
and Boost.System, for example, have header-only paths. When the standard version exists and your toolchain
supports it, prefer it: `std::filesystem`, `std::regex`, and `std::chrono` remove the link dependency
entirely. See [Boost and the C++ standard](./boost-and-the-standard.md).
:::

Linking them by hand looks like this:

```bash
g++ -std=c++17 -I/opt/boost/include app.cpp -o app \
    -L/opt/boost/lib -lboost_program_options -lboost_filesystem -lboost_system
```

Or, far more commonly, via CMake imported targets that carry the link step for you:

```cmake showLineNumbers title="CMakeLists.txt"
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem program_options)

add_executable(app app.cpp)
target_link_libraries(app PRIVATE
    Boost::filesystem          # pulls in Boost::system transitively
    Boost::program_options
)
```

Note that **Filesystem depends on System**, so linking `boost_filesystem` usually drags in
`boost_system`. CMake targets handle that transitive dependency automatically.

## Auto-linking on MSVC

Visual C++ has a trick the GNU/Clang world does not: **auto-linking**. Boost headers contain
`#pragma comment(lib, ...)` directives, so when you compile on MSVC the headers emit an instruction
telling the linker exactly which `.lib` to pull in — *without* you naming it on the link line. The
filename it requests encodes the toolset, threading model, and ABI (for example
`libboost_filesystem-vc143-mt-x64-1_85.lib`).

This is convenient but occasionally baffling: a link can fail because the auto-requested library name
does not match what you actually built (wrong toolset, wrong address model). Useful knobs:

```cpp showLineNumbers
// Turn auto-linking off and link manually instead
#define BOOST_ALL_NO_LIB
// Or print which libraries the headers are requesting (helps debug mismatches)
#define BOOST_LIB_DIAGNOSTIC
#include <boost/filesystem.hpp>
```

:::tip On non-Windows platforms you link explicitly
GCC and Clang have no auto-linking, so on Linux and macOS you always name the libraries yourself (via
`-l` or CMake targets). If you move a project from MSVC to GCC and suddenly hit undefined-reference
errors, this is usually why — the implicit links you never noticed are now your responsibility.
:::

## How to tell which kind a library is

A few reliable signals:

1. **Read the library's documentation.** Each Boost library's docs have a section that says, in effect,
   "header-only" or "must be built and linked." This is the authoritative answer.
2. **Check whether it appears as a b2/CMake component.** If `find_package(Boost COMPONENTS x)` recognises
   `x`, or b2 has a `--with-x` that produces a `stage/lib` file, it is compiled. Header-only libraries do
   not appear as components.
3. **Look in `stage/lib` after building.** If you built Boost and a `libboost_x` file exists, that
   library is compiled.
4. **Let the linker tell you.** An "undefined reference to `boost::x::...`" error after a clean compile is
   the loudest possible signal that `x` needs linking.

## The hidden cost of header-only

Header-only is convenient, but it is not free. Because the implementation lives in headers, **every
translation unit that includes a Boost header re-parses and re-compiles that code**, and heavy libraries
pull in deep webs of internal headers. The result can be dramatically slower builds.

:::warning Header-only inflates compile times
A single `#include <boost/spirit.hpp>` or large metaprogramming headers can add seconds *per translation
unit*. Mitigations: include only the narrow sub-header you need (`<boost/algorithm/string/trim.hpp>`
rather than the umbrella header), confine heavy includes behind a compilation firewall, and precompile
common Boost headers if your build system supports it.
:::

Compiled libraries, by contrast, pay their implementation cost **once** when the library is built, not on
every include — which is part of why those particular libraries are compiled in the first place.

## Where to go next

- <Icon icon="lucide:hammer" inline /> [Installing Boost](./installation.md) — how to get the headers and build the compiled libs.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ standard](./boost-and-the-standard.md) — prefer `std::` to drop link dependencies.
- <Icon icon="lucide:wrench" inline /> [Using Boost with CMake](../01-build-and-integration/cmake-integration.md) — let targets handle linking.
- <Icon icon="lucide:package" inline /> [Boost via vcpkg and Conan](../01-build-and-integration/package-managers.md) — install only the components you link.
