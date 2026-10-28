---
id: package-managers
title: C++ Package Managers
sidebar_label: Package Managers
sidebar_position: 16
tags: [vcpkg, conan, package-manager, dependencies, windows, linux]
---

# C++ Package Managers

C++ has no standard package manager. A third-party library has to be built with the same compiler,
standard library, architecture and configuration as your program (the [ABI](../12-low-level-and-platform/01-abi.md)
must match), its headers put on the include path, and its libraries linked in the right order.
Package managers automate that: they fetch a pinned version, build it (or download a matching
prebuilt binary) for your configuration, and hand CMake the result so that `find_package` works.
The two dominant tools are **vcpkg** (Microsoft) and **Conan** (JFrog); both work on Linux, Windows
and macOS.

**Prerequisites:** [Build Systems and CMake](./build-systems-cmake.md);
[find_package](../../cmake/03-dependencies/find-package.md) for the consuming side.
For pulling a dependency's source into your own build instead, see
[FetchContent](../../cmake/03-dependencies/fetchcontent.md).

<Diagram title="Where the package manager sits" accent="violet">
  <DiagramRow>
    <DiagramNode icon="file-text" title="Manifest">`vcpkg.json` / `conanfile.txt`: names and versions</DiagramNode>
    <DiagramArrow direction="right" label="install" />
    <DiagramNode icon="package" title="vcpkg / Conan" accent>Builds or downloads binaries for your triplet/profile</DiagramNode>
    <DiagramArrow direction="right" label="toolchain + config files" />
    <DiagramNode icon="settings" title="CMake">`find_package(fmt)` → `fmt::fmt`</DiagramNode>
  </DiagramRow>
</Diagram>

## vcpkg

vcpkg builds libraries from source using **ports** (build recipes in the vcpkg repository) and
plugs into CMake through a toolchain file.

### Install

<Tabs groupId="os">
  <TabItem value="linux" label="Linux / macOS">

```bash
git clone https://github.com/microsoft/vcpkg.git ~/vcpkg
~/vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT="$HOME/vcpkg"          # add to your shell profile
export PATH="$VCPKG_ROOT:$PATH"
```

  </TabItem>
  <TabItem value="win" label="Windows (PowerShell)">

```powershell
git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
[Environment]::SetEnvironmentVariable("VCPKG_ROOT", "C:\vcpkg", "User")
```

  </TabItem>
</Tabs>

### Manifest mode

Declare dependencies in `vcpkg.json` at the project root
([manifest mode](https://learn.microsoft.com/en-us/vcpkg/concepts/manifest-mode)):

```json title="vcpkg.json"
{
  "name": "my-project",
  "version": "1.0.0",
  "builtin-baseline": "<commit SHA of the vcpkg repository>",
  "dependencies": [
    "fmt",
    "nlohmann-json",
    { "name": "boost-filesystem", "version>=": "1.82.0" }
  ]
}
```

The **baseline** pins every dependency to the versions in that vcpkg commit. Without a
`builtin-baseline`, vcpkg ignores all version fields, including `version>=`
([versioning](https://learn.microsoft.com/en-us/vcpkg/users/versioning)). `vcpkg x-update-baseline --add-initial-baseline`
fills it in.

Pass the toolchain file at configure time; vcpkg installs the manifest's dependencies during
configuration:

```bash
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake"
cmake --build build
```

```cmake title="CMakeLists.txt"
find_package(fmt CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE fmt::fmt nlohmann_json::nlohmann_json)
```

The vcpkg port name (`nlohmann-json`), the CMake package name (`nlohmann_json`) and the target
name can all differ. After installing a port, vcpkg prints the exact `find_package` and
`target_link_libraries` lines to use.

**Classic mode** (`vcpkg install fmt` with no manifest) installs into one shared tree under the vcpkg
directory. It is fine for experiments; projects should use manifests, which keep the dependency list
and versions in the repository.

### Triplets

A **triplet** names the target configuration a library is built for
([triplets](https://learn.microsoft.com/en-us/vcpkg/users/triplets)). Library linkage per the
triplet files in the vcpkg repository:

| Triplet | Platform | Libraries built as |
|---|---|---|
| `x64-linux` | Linux x86-64 | static |
| `arm64-linux` | Linux 64-bit ARM | static |
| `x64-windows` | Windows x64, MSVC | DLLs |
| `x64-windows-static` | Windows x64, MSVC | static, static CRT |
| `arm64-osx` | macOS on Apple Silicon | static |
| `x64-mingw-dynamic` | Windows x64, MinGW (community triplet) | DLLs |

Select one with `-DVCPKG_TARGET_TRIPLET=x64-windows-static`. Triplets are also how vcpkg
[cross-compiles](./cross-compilation.md).

### Useful commands

```bash
vcpkg search fmt          # find a port
vcpkg list                # installed packages (classic mode)
vcpkg remove fmt          # uninstall (classic mode)
vcpkg integrate install   # Windows: make classic-mode packages visible to all MSBuild projects
```

## Conan

Conan is a Python tool that resolves dependencies from **remotes** (ConanCenter by default, or a
private Artifactory/Nexus server), stores built binaries in a local cache keyed by configuration,
and generates CMake integration files.

### Install and profile

```bash
pip install conan             # Conan 2.x
conan profile detect --force  # writes ~/.conan2/profiles/default from your compiler
```

A **profile** records the configuration packages are built for:

```ini title="~/.conan2/profiles/default (example, Linux)"
[settings]
arch=x86_64
build_type=Release
compiler=gcc
compiler.cppstd=17
compiler.libcxx=libstdc++11
compiler.version=12
os=Linux
```

Make variants by copying the file (for example to `~/.conan2/profiles/debug` with
`build_type=Debug`) and select them with `--profile:host debug`. A cross-compilation setup uses a
separate **host** profile for the target and **build** profile for the machine running the build
([profiles](https://docs.conan.io/2/reference/config_files/profiles.html)).

### Declaring dependencies

<Tabs>
  <TabItem value="txt" label="conanfile.txt">

```ini title="conanfile.txt"
[requires]
fmt/10.2.1
nlohmann_json/3.11.3

[generators]
CMakeDeps
CMakeToolchain

[options]
fmt/*:shared=False
```

  </TabItem>
  <TabItem value="py" label="conanfile.py">

```python title="conanfile.py"
from conan import ConanFile
from conan.tools.cmake import cmake_layout

class MyProject(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires("fmt/10.2.1")
        self.requires("nlohmann_json/3.11.3")

    def layout(self):
        cmake_layout(self)
```

The Python form allows conditions (`if self.settings.os == "Windows": …`), options and custom build
logic.

  </TabItem>
</Tabs>

### Conan with CMake

```bash
conan install . --output-folder=build --build=missing
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

`--build=missing` builds from source any package with no prebuilt binary for your profile. The
`CMakeDeps` generator writes `<name>-config.cmake` package files
([CMakeDeps](https://docs.conan.io/2/reference/tools/cmake/cmakedeps.html)), so `CMakeLists.txt`
uses plain `find_package`:

```cmake title="CMakeLists.txt"
find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)
target_link_libraries(my_app PRIVATE fmt::fmt nlohmann_json::nlohmann_json)
```

With the `conanfile.py` and `cmake_layout`, the generated files go to `build/Release/generators/`
instead; check the path `conan install` prints.

### Useful commands

```bash
conan search "fmt*" -r conancenter      # search a remote
conan list "fmt/*"                      # what is in the local cache
conan remove "fmt/10.2.1"               # remove from the local cache
conan remote list                       # configured remotes
conan remote add mycorp https://artifactory.example.com/artifactory/api/conan/conan-local
```

## Choosing

| | vcpkg | Conan |
|---|---|---|
| Setup | Clone the repository and bootstrap | `pip install conan` |
| Dependency file | `vcpkg.json` | `conanfile.txt` / `conanfile.py` |
| Version pinning | Baseline commit + overrides | Exact versions in the recipe; lockfiles |
| Binaries | Built from source; binary caching (local, NuGet, cloud storage) is optional | Prebuilt binaries from the remote when available |
| Configuration | Triplets | Profiles (host and build) |
| CMake integration | One toolchain file; installs during configure | Separate `conan install` step, then a generated toolchain |
| Private packages | Overlay ports, custom registries | Private remote server |

Both are mature. vcpkg needs fewer moving parts and integrates with Visual Studio; Conan suits
setups that want prebuilt binaries shared from a server across many configurations. Browse what
each provides at [vcpkg.io/en/packages](https://vcpkg.io/en/packages) and
[ConanCenter](https://conan.io/center).

## System package managers

On Linux, distribution packages (`apt install libfmt-dev`, `dnf install fmt-devel`,
`pacman -S fmt`) are the quickest way to get a library, and they are built against the system's
`libstdc++`. Versions follow the distribution's release cycle, often older than the current release,
and differ between distributions, so the build is not reproducible elsewhere.

## Pitfalls

- **Mixing sources for one dependency graph.** A library from vcpkg linked with another from `apt`
  that was built against a different version of a shared dependency (OpenSSL, Boost) causes ODR
  violations or link errors. Take all dependencies from one source.
- **Debug/Release mismatch on MSVC.** Debug and release builds use different runtime libraries;
  linking one with the other fails (`LNK2038: mismatch detected for '_ITERATOR_DEBUG_LEVEL'`).
  Both tools build per configuration; make sure CMake's configuration matches.
- **Unpinned versions.** Without a vcpkg baseline or exact Conan versions, two machines can resolve
  different library versions.

## Key points

- A package manager builds each library for your exact configuration and hands CMake config files.
- vcpkg: manifest + baseline + triplet, wired in through one toolchain file.
- Conan: requirements + profile, `conan install`, then the generated toolchain.
- Pin versions and use a single source for every dependency.
