---
id: package-managers
title: C++ Package Managers
sidebar_label: Package Managers
sidebar_position: 16
tags: [vcpkg, conan, package-manager, dependencies, windows, linux]
---

# C++ Package Managers

C++ has no built-in package manager. Third-party tools fill this gap. The two dominant options are **vcpkg** (Microsoft, integrates tightly with CMake and Visual Studio) and **Conan** (JFrog, cross-platform, more configuration power). Both work on Windows and Linux.

## vcpkg

vcpkg downloads, builds, and installs libraries from source. It integrates directly into CMake via a toolchain file so `find_package()` just works — no manual library paths.

### Install vcpkg

**Linux**
```bash
git clone https://github.com/microsoft/vcpkg.git ~/vcpkg
cd ~/vcpkg
./bootstrap-vcpkg.sh

# Add to shell (bash/zsh)
echo 'export VCPKG_ROOT="$HOME/vcpkg"' >> ~/.bashrc
echo 'export PATH="$VCPKG_ROOT:$PATH"'  >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
cd C:\vcpkg
.\bootstrap-vcpkg.bat

# Add to user PATH (permanent)
[Environment]::SetEnvironmentVariable("VCPKG_ROOT", "C:\vcpkg", "User")
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;C:\vcpkg", "User")
```

### Install packages

```bash
vcpkg install boost-filesystem   # specific lib from boost
vcpkg install fmt                # {fmt} formatting library
vcpkg install nlohmann-json      # JSON for Modern C++
vcpkg install gtest              # Google Test
vcpkg install openssl            # OpenSSL

# Install for a specific triplet (target platform)
vcpkg install zlib:x64-windows   # 64-bit Windows static
vcpkg install zlib:x64-linux     # 64-bit Linux static
vcpkg install zlib:x64-mingw-dynamic  # MinGW dynamic
```

Common triplets:

| Triplet | Platform |
|---------|----------|
| `x64-windows` | Windows 64-bit, dynamic |
| `x64-windows-static` | Windows 64-bit, static |
| `x64-linux` | Linux 64-bit |
| `arm64-osx` | macOS Apple Silicon |
| `x64-mingw-dynamic` | Windows with MinGW |

### vcpkg with CMake

**Manifest mode (recommended)** — declare dependencies in `vcpkg.json` at the project root. vcpkg installs them automatically when CMake configures.

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "dependencies": [
    "fmt",
    "nlohmann-json",
    { "name": "boost-filesystem", "version>=": "1.82.0" }
  ]
}
```

Configure CMake with the vcpkg toolchain file:

```bash
# Linux
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake

# Windows (PowerShell)
cmake -B build `
  -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake"
```

Then use packages normally in `CMakeLists.txt`:

```cmake
find_package(fmt CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

target_link_libraries(my_app PRIVATE
    fmt::fmt
    nlohmann_json::nlohmann_json
)
```

**Classic mode (global install)** — install packages globally, then pass the toolchain file. No `vcpkg.json` needed. Simpler for personal use, but version control is harder.

```bash
vcpkg install fmt nlohmann-json
cmake -B build -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake
```

### Visual Studio integration

vcpkg can integrate globally into all Visual Studio projects (no toolchain file needed):

```cmd
vcpkg integrate install
```

After this, installed packages are visible to all MSBuild projects automatically.

### Useful commands

```bash
vcpkg search fmt              # search available packages
vcpkg list                    # list installed packages
vcpkg remove fmt              # uninstall
vcpkg upgrade                 # update installed packages
vcpkg x-history fmt           # show version history
vcpkg env                     # print environment for the default triplet
```

---

## Conan

Conan is a decentralized package manager — packages come from ConanCenter (public) or your own Artifactory/Nexus server. It generates build system integration files (CMake, Make, MSBuild) rather than installing libraries to a global location.

### Install Conan

Conan is a Python tool. Requires Python 3.6+.

**Linux**
```bash
pip install conan             # user install
# or
pip install --user conan

conan --version               # verify
conan profile detect --force  # auto-detect compiler and create default profile
```

**Windows (PowerShell)**
```powershell
pip install conan
conan --version
conan profile detect --force
```

The profile detection reads your installed compiler (MSVC version on Windows, GCC/Clang on Linux) and sets defaults for architecture, build type, and C++ standard.

### Profiles

A profile defines the target compiler, architecture, and settings. The default profile is stored at `~/.conan2/profiles/default`.

```ini
# ~/.conan2/profiles/default  (auto-generated, Linux example)
[settings]
arch=x86_64
build_type=Release
compiler=gcc
compiler.cppstd=17
compiler.libcxx=libstdc++11
compiler.version=12
os=Linux
```

Create multiple profiles for different targets:

```bash
# Create a debug profile
conan profile show default > ~/.conan2/profiles/debug
# Edit: set build_type=Debug

# Use a specific profile
conan install . --profile debug
```

### conanfile.txt (simple projects)

Declare dependencies in `conanfile.txt` at the project root:

```ini
[requires]
fmt/10.2.1
nlohmann_json/3.11.3
boost/1.84.0

[generators]
CMakeDeps
CMakeToolchain

[options]
boost/*:shared=False
```

Install dependencies:

```bash
mkdir build && cd build
conan install .. --output-folder=. --build=missing
```

`--build=missing` builds packages from source if no binary exists for your profile.

### conanfile.py (advanced projects)

Python-based recipe gives full control: conditional dependencies, custom options, cross-compilation settings.

```python
from conan import ConanFile
from conan.tools.cmake import cmake_layout

class MyProject(ConanFile):
    name = "my-project"
    version = "1.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires("fmt/10.2.1")
        self.requires("nlohmann_json/3.11.3")
        if self.settings.os == "Windows":
            self.requires("winflexbison/2.5.25")

    def layout(self):
        cmake_layout(self)
```

### Conan with CMake

After `conan install`, generated files live in the build directory. Include `conan_toolchain.cmake` and use `find_package` as usual.

```bash
cd build
conan install .. --output-folder=. --build=missing
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release
cmake --build .
```

`CMakeLists.txt` stays standard — Conan generates the `Find*.cmake` files:

```cmake
find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)

target_link_libraries(my_app PRIVATE
    fmt::fmt
    nlohmann_json::nlohmann_json
)
```

### Searching and inspecting packages

```bash
conan search fmt               # search local cache
conan search fmt -r conancenter  # search remote ConanCenter
conan inspect fmt/10.2.1       # show package metadata and options
conan list "*"                 # list all packages in local cache
conan remove fmt/10.2.1        # remove from local cache
```

### Conan remotes

ConanCenter is the default public remote. You can add private remotes (Artifactory):

```bash
conan remote list                          # show configured remotes
conan remote add myserver https://myartifactory.example.com/artifactory/api/conan/conan-local
conan remote auth myserver                 # login
```

---

## vcpkg vs Conan

| | vcpkg | Conan |
|---|---|---|
| **Setup** | Clone repo + bootstrap | `pip install conan` |
| **Config file** | `vcpkg.json` (JSON) | `conanfile.txt` or `conanfile.py` |
| **CMake integration** | Toolchain file, transparent | Generated files, explicit |
| **VS integration** | `vcpkg integrate install` | No native integration |
| **Private registry** | GitHub Actions / custom overlay | Artifactory / self-hosted |
| **Cross-compilation** | Triplets | Profiles |
| **Package count** | ~2500 ports | ~1800 ConanCenter recipes |
| **Binary caching** | GitHub Actions cache / NuGet | Artifactory / local cache |
| **Best for** | Windows + MSVC, simple setups | Complex builds, CI/CD, enterprise |

Both tools work well. vcpkg is simpler to start with on Windows; Conan scales better for multi-config CI pipelines and private package hosting.

---

## System Package Managers (Linux only)

For quick installs on Linux, system package managers work — but versions are often outdated and packages vary by distro.

```bash
# Debian / Ubuntu
sudo apt install libboost-all-dev    # Boost (may be old)
sudo apt install libfmt-dev          # {fmt}
sudo apt install nlohmann-json3-dev  # nlohmann/json
sudo apt install libssl-dev          # OpenSSL
sudo apt install libgtest-dev        # GTest (headers only, must build)

# Fedora / RHEL / CentOS
sudo dnf install boost-devel
sudo dnf install fmt-devel
sudo dnf install openssl-devel

# Arch Linux
sudo pacman -S boost fmt nlohmann-json openssl
```

:::caution
System packages install to `/usr` and link against the system libstdc++. Mixing system and vcpkg/Conan packages in the same binary can cause ABI conflicts. Prefer one source for all dependencies.
:::

Prefer vcpkg or Conan for production projects where version pinning and reproducibility matter.
