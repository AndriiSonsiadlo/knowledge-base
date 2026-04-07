---
id: installation
title: Installing Boost
sidebar_label: Installing Boost
sidebar_position: 3
tags: [ c++, boost, installation, build ]
---

# Installing Boost

There is no single "install Boost" button, and that is mostly fine: because the majority of Boost is
[header-only](./header-only-vs-compiled.md), "installing" often means nothing more than putting the
`boost/` header tree somewhere your compiler can find it. The work only begins when you need one of the
[compiled libraries](./header-only-vs-compiled.md) (Filesystem, Thread, Program_options, and friends),
which must be built into `.a`/`.lib`/`.so` files first.

This page walks through the realistic options, from "let the package manager do it" to "build it
yourself with b2".

:::tip Pick the lightest option that works
For most projects a system package or a package manager (vcpkg/Conan) is enough. Only download and
build the source tree yourself when you need a specific version, custom build flags, or a platform your
package manager does not serve.
:::

## Option 1: System package managers

The fastest route. These install prebuilt headers *and* the compiled libraries into standard system
locations, so the compiler usually finds them with no extra flags.

```bash
# Debian / Ubuntu
sudo apt-get install libboost-all-dev

# macOS (Homebrew)
brew install boost

# Fedora / RHEL
sudo dnf install boost-devel
```

The trade-off is version freshness: distro packages can lag the current Boost release by a year or
more. If you need a recent version, prefer a C++ package manager or a manual build.

## Option 2: C++ package managers (vcpkg / Conan)

These integrate cleanly with CMake and let you pin an exact version per project. They are covered in
depth on [Boost via vcpkg and Conan](../01-build-and-integration/package-managers.md); the essentials:

```bash
# vcpkg — install a specific component set
vcpkg install boost-filesystem boost-program-options

# Conan — add to conanfile and install
conan install --requires=boost/1.85.0 --build=missing
```

With vcpkg you typically build via its CMake toolchain file, after which `find_package(Boost ...)`
just works. See [Using Boost with CMake](../01-build-and-integration/cmake-integration.md) for the
consumer side.

## Option 3: Download a release tarball

To control the exact version, grab a release from the official site and unpack it. Releases are named
`boost_1_XX_0` (note the underscores).

```bash
# Download and unpack (adjust the version as needed)
curl -L -O https://archives.boost.io/release/1.85.0/source/boost_1_85_0.tar.gz
tar -xzf boost_1_85_0.tar.gz
cd boost_1_85_0
```

### Directory layout

After unpacking (and, later, building), the tree you care about looks like this:

```
boost_1_85_0/
├── boost/            # the entire header tree — this is what -I points at
│   ├── optional.hpp
│   ├── filesystem.hpp
│   └── ...
├── libs/             # per-library source, tests, and docs
├── tools/            # build tooling, including b2's source
├── bootstrap.sh      # generates the b2 build engine (bootstrap.bat on Windows)
├── b2                # the build driver (after bootstrap)
└── stage/
    └── lib/          # compiled libraries land here after a build
```

Two directories matter for using Boost:

- **`boost/`** — the header root. Add its parent to the include path so that `#include <boost/...>`
  resolves. For header-only libraries, this is all you need.
- **`stage/lib/`** — where built `.a`/`.so`/`.lib` files appear after you run b2.

:::note Header path vs header root
You point the compiler at the directory that *contains* `boost/`, not at `boost/` itself. With the
tarball above that directory is `boost_1_85_0`, so the flag is `-I/path/to/boost_1_85_0`.
:::

## Bootstrapping and building compiled libraries

If you only use header-only libraries, skip this section entirely. To get the compiled ones, build them
with Boost's own build tool, **b2** (formerly `bjam`). First generate the engine with the bootstrap
script, then run b2:

```bash
# From inside the unpacked source tree
./bootstrap.sh                 # builds the b2 executable
./b2                           # builds all compiled libraries into stage/lib
```

You can narrow the build and tune it — useful because building everything is slow:

```bash
# Build only the libraries you need, both static and shared, optimised
./b2 --with-filesystem --with-program_options \
     link=static,shared variant=release -j8

# Install headers + built libs into a prefix
./b2 --prefix=/opt/boost install
```

:::warning b2 is its own world
b2 has an extensive syntax for toolsets, variants, and properties that is easy to get lost in. This page
shows only enough to produce usable libraries. For the full treatment — toolsets, `user-config.jam`,
addressing models, and layout options — see
[Boost.Build (b2)](../01-build-and-integration/boost-build-b2.md).
:::

## Pointing a compiler at Boost

Once Boost is on disk, using it comes down to two kinds of flags.

### Header-only libraries: just the include path

```bash
# -I adds the directory that contains boost/ to the header search path
g++ -std=c++17 -I/opt/boost/include hello.cpp -o hello
```

```cpp showLineNumbers title="hello.cpp"
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <string>

int main() {
    std::string s = "  Boost  ";
    boost::algorithm::trim(s);          // header-only: no linking
    std::cout << '[' << s << "]\n";     // prints [Boost]
}
```

### Compiled libraries: add the lib path and link

For the minority that need linking, add `-L` (where the libs live) and one `-l` per library. The link
name drops the `lib` prefix and `.a`/`.so` suffix — `libboost_filesystem.so` becomes
`-lboost_filesystem`.

```bash
g++ -std=c++17 -I/opt/boost/include app.cpp -o app \
    -L/opt/boost/lib -lboost_filesystem
```

```cpp showLineNumbers title="app.cpp"
#include <boost/filesystem.hpp>
#include <iostream>

namespace fs = boost::filesystem;

int main() {
    for (const auto& entry : fs::directory_iterator("."))
        std::cout << entry.path().filename().string() << '\n';
}
```

:::warning Link order and runtime path
On most linkers, libraries listed with `-l` must come *after* the object files that use them. And for
shared libraries you may also need the runtime loader to find them at launch (for example via
`LD_LIBRARY_PATH` or an rpath). Which libraries need linking at all is covered in
[header-only vs compiled](./header-only-vs-compiled.md).
:::

### CMake: let the toolchain do the linking

In practice you rarely write `-I`/`-L`/`-l` by hand — CMake handles it through imported targets:

```cmake showLineNumbers title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.20)
project(boost_demo CXX)

find_package(Boost 1.70 REQUIRED COMPONENTS filesystem program_options)

add_executable(app app.cpp)
target_link_libraries(app PRIVATE
    Boost::filesystem        # compiled component, links automatically
    Boost::program_options
)
```

The `Boost::headers` target covers header-only usage; each compiled component has its own
`Boost::<component>` target that carries both the include path and the link step. The full setup,
including version selection and component discovery, is on
[Using Boost with CMake](../01-build-and-integration/cmake-integration.md).

## Where to go next

- <Icon icon="lucide:puzzle" inline /> [Header-only vs compiled](./header-only-vs-compiled.md) — decide whether you even need to build anything.
- <Icon icon="lucide:hammer" inline /> [Boost.Build (b2)](../01-build-and-integration/boost-build-b2.md) — the deep dive on b2.
- <Icon icon="lucide:package" inline /> [Boost via vcpkg and Conan](../01-build-and-integration/package-managers.md) — per-project, versioned installs.
- <Icon icon="lucide:wrench" inline /> [Using Boost with CMake](../01-build-and-integration/cmake-integration.md) — wire it into a CMake build.
- <Icon icon="lucide:library" inline /> [Boost overview](../readme.md) — the full library catalogue.
