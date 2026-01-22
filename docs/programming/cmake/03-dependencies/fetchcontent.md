---
id: fetchcontent
title: FetchContent Module
sidebar_label: FetchContent
sidebar_position: 2
tags: [c++, cmake, dependencies, fetchcontent, package-management]
---

# FetchContent Module

## What is FetchContent?

`FetchContent` is a CMake module introduced in version 3.11 that downloads and makes external projects available at **configure time**. Unlike ExternalProject which builds dependencies at build time, FetchContent integrates external dependencies directly into your build as if they were part of your source tree.

This approach is particularly powerful for modern C++ development where you want header-only libraries or small dependencies to be automatically fetched and built alongside your project. It eliminates the need for users to pre-install dependencies and ensures everyone builds with the same versions.

The key distinction: FetchContent downloads during the CMake configure step and makes the dependency's targets immediately available for use in your `CMakeLists.txt`. This means you can link against fetched libraries just like local targets.

## Basic Usage

### Setup

`FetchContent` requires CMake 3.11 or later (3.14+ recommended for `FetchContent_MakeAvailable`).

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.14)
project(MyProject)

# Include the module
include(FetchContent)
```

### Simple Example

Here's a complete example fetching the fmt library:

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.14)
project(MyApp)

include(FetchContent)

# Declare what to fetch
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0  # Specify version tag
)

# Make it available
FetchContent_MakeAvailable(fmt)

# Now use it like a normal library
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE fmt::fmt)
```

In this example, CMake will:

1. Download fmt from GitHub during configuration
2. Configure fmt's CMake build
3. Make fmt's targets (like `fmt::fmt`) available
4. Allow you to link against them normally

## FetchContent_Declare()

This command tells CMake what to fetch and where to find it. It doesn't actually download anything - it just records the information for later use.

### Fetching from Git

The most common source is Git repositories:

```cmake showLineNumbers 
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    GIT_SHALLOW ON        # Only fetch the specific tag, not full history
    GIT_PROGRESS ON       # Show download progress
)
```

**`GIT_TAG`:** Can be a tag, branch name, or commit hash. Tags are recommended for reproducibility.

**`GIT_SHALLOW`:** Downloads only the specified commit, significantly faster for large repositories. However, you can't switch to other branches/tags without re-fetching.

**`GIT_PROGRESS`:** Shows progress during the clone operation, useful for large repositories to confirm it's not stuck.

**Using commit hashes for security:**

```cmake showLineNumbers 
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG 76fb40d95455f249bd70824ecfcae7a8f0930fa3  # v1.11.0
    GIT_SHALLOW ON
)
```

Commit hashes are immutable - tags can be moved, but hashes cannot. This guarantees you always get exactly the same code.

### Fetching from URL

You can download tarballs or zip files:

```cmake showLineNumbers 
FetchContent_Declare(
    catch2
    URL https://github.com/catchorg/Catch2/archive/refs/tags/v3.3.2.tar.gz
    URL_HASH SHA256=8361907f4d9bff3ae7c1edb027f813659f793053c99b67837a0c0d34290c2d3f
)
```

**URL_HASH:** Verifies the download's integrity. Get the hash from the release page or compute it with `sha256sum`. This is critical for security - ensures the downloaded file hasn't been tampered with.

**When to use URL vs GIT:**

- **URL:** Faster for releases, no Git dependency required
- **GIT:** Better for development, can track branches, easier to update

### Fetching from Local Path

Useful during development or for vendored dependencies:

```cmake showLineNumbers 
FetchContent_Declare(
    mylib
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/mylib
)
```

This treats a local directory as if it were fetched, making it easy to switch between local development and remote fetching.

## FetchContent_MakeAvailable()

Introduced in CMake 3.14, this command does the actual work of making the content available. For earlier CMake versions, you need a more verbose approach (shown later).

```cmake showLineNumbers 
FetchContent_MakeAvailable(fmt spdlog json)
```

This single command:

1. Downloads the content if not already present
2. Runs `add_subdirectory()` on it
3. Makes all targets from those projects available

You can make multiple dependencies available at once, and CMake will parallelize the downloads when possible.

### For CMake < 3.14

If you're stuck with CMake 3.11-3.13, use this pattern:

```cmake showLineNumbers 
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
)

# Manual population
FetchContent_GetProperties(fmt)
if(NOT fmt_POPULATED)
    FetchContent_Populate(fmt)
    add_subdirectory(${fmt_SOURCE_DIR} ${fmt_BINARY_DIR})
endif()
```

This is what `FetchContent_MakeAvailable()` does internally - it's just more verbose.

## Configuring Fetched Dependencies

Often you need to control how dependencies are built. FetchContent lets you set their CMake options before they're configured.

### Setting Options

```cmake showLineNumbers 
# Disable examples and tests for dependencies
set(FMT_INSTALL OFF CACHE BOOL "" FORCE)
set(FMT_TEST OFF CACHE BOOL "" FORCE)
set(FMT_DOC OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
)

FetchContent_MakeAvailable(fmt)
```

The `CACHE ... FORCE` syntax ensures your settings override the dependency's defaults. This is important because dependencies might have different default values.

### Common Options to Disable

Most well-designed CMake projects have options to disable non-essential components:

```cmake showLineNumbers 
# For most libraries, consider disabling:
set(DEPENDENCY_INSTALL OFF CACHE BOOL "" FORCE)      # Don't install dependency
set(DEPENDENCY_TESTS OFF CACHE BOOL "" FORCE)        # Don't build tests
set(DEPENDENCY_EXAMPLES OFF CACHE BOOL "" FORCE)     # Don't build examples
set(DEPENDENCY_DOCS OFF CACHE BOOL "" FORCE)         # Don't build documentation
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)       # Force static linking

FetchContent_Declare(...)
FetchContent_MakeAvailable(...)
```

### Why Disable These?

**Installation:** If you're embedding a dependency, you typically don't want to install it separately from your project.

**Tests/Examples:** These increase build time significantly and aren't needed when you're just using the library.

**Documentation:** Usually not needed at build time - you'll read docs online.

**BUILD_SHARED_LIBS:** Static linking simplifies deployment and ensures ABI compatibility. Dynamic linking is sometimes necessary, but static is often easier.

## Multiple Dependencies

Real projects usually have several dependencies. Here's how to manage them cleanly:

```cmake showLineNumbers 
include(FetchContent)

# Configure all dependencies first
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
set(FMT_INSTALL OFF CACHE BOOL "" FORCE)
set(SPDLOG_FMT_EXTERNAL ON CACHE BOOL "" FORCE)  # Use our fmt, not spdlog's
set(SPDLOG_INSTALL OFF CACHE BOOL "" FORCE)

# Declare all dependencies
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    GIT_SHALLOW ON
)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
    GIT_SHALLOW ON
)

FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.11.0
    GIT_SHALLOW ON
)

# Make all available at once (faster, downloads in parallel)
FetchContent_MakeAvailable(json fmt spdlog)

# Use them
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    nlohmann_json::nlohmann_json
    fmt::fmt
    spdlog::spdlog
)
```

Notice `SPDLOG_FMT_EXTERNAL` - this tells spdlog to use our fetched fmt instead of bundling its own. This avoids having multiple versions of fmt in your build.

## Best Practices

### Organize Dependencies

For projects with many dependencies, create a separate file:

```cmake showLineNumbers  title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.14)
project(MyProject)

# Fetch all dependencies
include(cmake/Dependencies.cmake)

# Continue with your project
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    fmt::fmt
    spdlog::spdlog
    nlohmann_json::nlohmann_json
)
```

```cmake showLineNumbers  title="cmake/Dependencies.cmake"
include(FetchContent)

# Configure options
set(FMT_INSTALL OFF CACHE BOOL "" FORCE)
set(SPDLOG_INSTALL OFF CACHE BOOL "" FORCE)
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)

# Declare dependencies
FetchContent_Declare(fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
    GIT_SHALLOW ON
)

FetchContent_Declare(spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.11.0
    GIT_SHALLOW ON
)

FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    GIT_SHALLOW ON
)

# Make available
FetchContent_MakeAvailable(fmt spdlog json)
```

This separation keeps your main `CMakeLists.txt` clean and makes dependency management easier.

### Caching Downloads

FetchContent downloads to `${CMAKE_BINARY_DIR}/_deps` by default. If you clean your build directory, it re-downloads everything. To cache across build directory cleanups:

```cmake showLineNumbers 
# Put downloads in a global cache directory
set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/.fetchcontent-cache"
    CACHE PATH "FetchContent download directory")
```

Now dependencies are cached in `.fetchcontent-cache/` in your source tree (add to `.gitignore`). They persist even if you delete your build directory.

### Updating Dependencies

To update to a newer version:

```cmake showLineNumbers 
# Change the version tag
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.0.0  # Updated from 9.1.0
    GIT_SHALLOW ON
)
```

Then delete the old download:

```bash
rm -rf build/_deps/fmt-*
cmake -B build
```

Or if using a cache directory:

```bash
rm -rf .fetchcontent-cache/fmt-*
cmake -B build
```

### Quiet Downloads

Reduce output clutter:

```cmake showLineNumbers 
set(FETCHCONTENT_QUIET ON CACHE BOOL "" FORCE)

FetchContent_Declare(...)
FetchContent_MakeAvailable(...)
```

Only errors will be shown. During initial setup, keep this OFF to see progress.

## Advanced Patterns

### Optional Dependencies

Make a dependency optional based on availability or user choice:

```cmake showLineNumbers 
option(USE_FMT "Use fmt library for formatting" ON)

if(USE_FMT)
    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG 9.1.0
    )
    FetchContent_MakeAvailable(fmt)
    
    target_link_libraries(myapp PRIVATE fmt::fmt)
    target_compile_definitions(myapp PRIVATE HAS_FMT)
endif()
```

### Version Selection

Allow users to override dependency versions:

```cmake showLineNumbers 
# Default versions
set(FMT_VERSION "9.1.0" CACHE STRING "fmt library version")
set(SPDLOG_VERSION "v1.11.0" CACHE STRING "spdlog library version")

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG ${FMT_VERSION}
)

FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG ${SPDLOG_VERSION}
)
```

Users can now override: `cmake -DFMT_VERSION=10.0.0 -B build`

### Conditional Fetching

Only fetch if not already available on the system:

```cmake showLineNumbers 
find_package(fmt QUIET)

if(NOT fmt_FOUND)
    message(STATUS "fmt not found on system, fetching...")
    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG 9.1.0
    )
    FetchContent_MakeAvailable(fmt)
else()
    message(STATUS "Using system fmt")
endif()
```

This gives users flexibility - they can use system packages if available, or let CMake fetch them automatically.

### Patch Dependencies

Sometimes you need to modify a dependency. Use patch files:

```cmake showLineNumbers 
FetchContent_Declare(
    somelib
    GIT_REPOSITORY https://github.com/example/somelib.git
    GIT_TAG v1.0.0
    PATCH_COMMAND git apply ${CMAKE_SOURCE_DIR}/patches/somelib.patch
)
```

The patch is applied after downloading but before configuring. Keep patches in your repository for reproducibility.

## Complete Real-World Example

Here's a comprehensive example for a real project:

```cmake showLineNumbers  title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.14)
project(WebServer VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fetch dependencies
include(cmake/Dependencies.cmake)

# Main application
add_executable(webserver
    src/main.cpp
    src/server.cpp
    src/request_handler.cpp
)

target_include_directories(webserver PRIVATE include)

target_link_libraries(webserver PRIVATE
    fmt::fmt
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    httplib::httplib
)

# Enable warnings
if(MSVC)
    target_compile_options(webserver PRIVATE /W4)
else()
    target_compile_options(webserver PRIVATE -Wall -Wextra -pedantic)
endif()

# Installation
install(TARGETS webserver DESTINATION bin)
```

```cmake showLineNumbers  title="cmake/Dependencies.cmake"
include(FetchContent)

# Cache directory for faster rebuilds
set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/.fetchcontent-cache")

# Quiet mode after initial download
set(FETCHCONTENT_QUIET ON)

# Configure dependency options
set(FMT_INSTALL OFF CACHE BOOL "" FORCE)
set(FMT_TEST OFF CACHE BOOL "" FORCE)
set(FMT_DOC OFF CACHE BOOL "" FORCE)

set(SPDLOG_FMT_EXTERNAL ON CACHE BOOL "" FORCE)
set(SPDLOG_INSTALL OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)

set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
set(JSON_Install OFF CACHE BOOL "" FORCE)

# Declare all dependencies
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
    GIT_SHALLOW ON
)

FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.11.0
    GIT_SHALLOW ON
)

FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    GIT_SHALLOW ON
)

FetchContent_Declare(
    httplib
    GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
    GIT_TAG v0.12.2
    GIT_SHALLOW ON
)

# Make all available (downloads in parallel)
FetchContent_MakeAvailable(fmt spdlog json httplib)

# Log what was fetched
message(STATUS "Dependencies fetched and configured:")
message(STATUS "  - fmt")
message(STATUS "  - spdlog")
message(STATUS "  - nlohmann_json")
message(STATUS "  - cpp-httplib")
```

```cmake showLineNumbers  title=".gitignore"
build/
.fetchcontent-cache/
```

## FetchContent vs find_package()

When should you use each?

### Use FetchContent When

✅ **Dependency is not commonly system-installed**

- Header-only libraries (Eigen, GLM)
- Modern C++ libraries (fmt, spdlog, json)
- Specialized libraries

✅ **You need a specific version**

- Ensures all developers use the same version
- Reproducible builds across systems

✅ **Simplifying setup for users**

- No installation prerequisites
- Works out of the box

✅ **Active development**

- Easy to test new versions
- Can point to development branches

### Use find_package() When

✅ **Large, stable dependencies**

- OpenCV, Qt, Boost
- These are huge and slow to build

✅ **System integration is important**

- OpenSSL, zlib, pthread
- These often have system-specific optimization

✅ **Binary compatibility matters**

- Multiple applications sharing libraries
- System-wide updates apply to all apps

✅ **Deployment requirements**

- Package managers (apt, yum, brew)
- Linux distributions prefer system libraries

### Hybrid Approach

Best of both worlds - try system first, fall back to fetch:

```cmake showLineNumbers 
find_package(fmt QUIET)

if(fmt_FOUND)
    message(STATUS "Using system fmt")
else()
    message(STATUS "System fmt not found, fetching...")
    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG 9.1.0
    )
    FetchContent_MakeAvailable(fmt)
endif()
```

## Common Issues and Solutions

### Different Targets Available

Some projects don't create imported targets or use different names:

```cmake showLineNumbers 
FetchContent_Declare(
    somelib
    GIT_REPOSITORY https://github.com/example/somelib.git
    GIT_TAG v1.0.0
)

FetchContent_MakeAvailable(somelib)

# Check what targets were created
get_directory_property(targets DIRECTORY ${somelib_SOURCE_DIR} BUILDSYSTEM_TARGETS)
message(STATUS "somelib targets: ${targets}")

# Might need to use:
# target_link_libraries(myapp PRIVATE somelib)  # Not somelib::somelib
```

### Header-Only Libraries

Some header-only libraries need special handling:

```cmake showLineNumbers 
FetchContent_Declare(
    eigen
    GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
    GIT_TAG 3.4.0
)

FetchContent_MakeAvailable(eigen)

# Eigen creates Eigen3::Eigen target
target_link_libraries(myapp PRIVATE Eigen3::Eigen)
```

### Build Time Issues

FetchContent can slow down configuration. Mitigate this:

```cmake showLineNumbers 
# Use shallow clones
GIT_SHALLOW ON

# Use URL downloads instead of git when possible
URL https://github.com/project/archive/v1.0.tar.gz

# Cache the download directory
set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/.fetchcontent-cache")

# Only populate once
FetchContent_GetProperties(lib)
if(NOT lib_POPULATED)
    FetchContent_Populate(lib)
endif()
```

### Conflicting Dependencies

Two dependencies might fetch different versions of the same library:

```cmake showLineNumbers 
# Force both to use your version
set(COMMON_LIB_VERSION "1.0.0" CACHE STRING "" FORCE)

# Tell dependencies to use external version
set(DEPENDENCY_A_USE_EXTERNAL_COMMON ON CACHE BOOL "" FORCE)
set(DEPENDENCY_B_USE_EXTERNAL_COMMON ON CACHE BOOL "" FORCE)

# Fetch common library first
FetchContent_Declare(common_lib
    GIT_REPOSITORY https://github.com/common/lib.git
    GIT_TAG ${COMMON_LIB_VERSION}
)
FetchContent_MakeAvailable(common_lib)

# Then fetch dependencies
FetchContent_MakeAvailable(dependency_a dependency_b)
```

## Quick Reference

```cmake showLineNumbers 
# Basic usage
include(FetchContent)

FetchContent_Declare(
    name
    GIT_REPOSITORY https://github.com/user/repo.git
    GIT_TAG v1.0.0
    GIT_SHALLOW ON
)

FetchContent_MakeAvailable(name)

target_link_libraries(myapp PRIVATE name::name)

# Configure dependency options
set(DEPENDENCY_OPTION VALUE CACHE TYPE "" FORCE)

# Cache downloads
set(FETCHCONTENT_BASE_DIR "${CMAKE_SOURCE_DIR}/.cache")

# From URL
FetchContent_Declare(name
    URL https://example.com/file.tar.gz
    URL_HASH SHA256=abc123...
)

# Conditional fetch
find_package(name QUIET)
if(NOT name_FOUND)
    FetchContent_Declare(...)
    FetchContent_MakeAvailable(name)
endif()
```

:::success When to Use FetchContent

**Perfect for:**

- Header-only libraries
- Modern C++ libraries (fmt, spdlog, json)
- Small to medium dependencies
- Version-sensitive projects
- Simplifying user setup

**Consider alternatives for:**

- Very large libraries (Boost, Qt, OpenCV)
- System libraries (OpenSSL, zlib)
- When binary compatibility is critical
- When system integration is important
  :::
