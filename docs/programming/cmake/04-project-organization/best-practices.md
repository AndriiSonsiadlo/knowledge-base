---
id: best-practices
title: CMake Best Practices
sidebar_label: Best Practices
tags: [cmake, best-practices, modern-cmake, patterns]
---

# CMake Best Practices

## Modern CMake Philosophy

Modern CMake (3.15+) emphasizes **target-based** configuration over global settings. The core principle: each target explicitly declares its own requirements, making dependencies clear and builds modular.

The shift from "directory-based" to "target-based" CMake is fundamental. Old CMake scattered settings globally using commands like `include_directories()` and `link_libraries()`. Modern CMake attaches everything to specific targets with `target_*` commands, making relationships explicit and preventing unintended side effects.

## Essential Principles

### 1. Use Target Commands, Not Global

This is the single most important rule for maintainable CMake projects.

```cmake
# ❌ Old style - affects everything in directory
include_directories(include/)
add_definitions(-DFEATURE=1)
link_libraries(somelib)

# ✅ Modern style - affects only specific target
add_executable(myapp main.cpp)
target_include_directories(myapp PRIVATE include/)
target_compile_definitions(myapp PRIVATE FEATURE=1)
target_link_libraries(myapp PRIVATE somelib)
```

**Why this matters:** Global commands create hidden dependencies. When you add a new target, it mysteriously picks up settings meant for other targets. Target commands make everything explicit.

### 2. Visibility Keywords Are Critical

Always use `PRIVATE`, `PUBLIC`, or `INTERFACE` - never omit them.

```cmake
add_library(mylib mylib.cpp)

# ✅ Explicit visibility
target_include_directories(mylib
    PRIVATE src/          # Only mylib needs this
    PUBLIC include/       # Mylib and its users need this
)

target_link_libraries(mylib
    PRIVATE internal_dep  # Implementation detail
    PUBLIC api_dep        # Exposed in our headers
)
```

**Rule of thumb:**

- **PRIVATE**: Implementation details (most common)
- **PUBLIC**: Part of your API, users need it too
- **INTERFACE**: Header-only or requirements for users only

### 3. Avoid file(GLOB)

Don't use `file(GLOB)` to collect source files - CMake won't detect when you add/remove files.

```cmake
# ❌ Bad - CMake won't know about new files
file(GLOB SOURCES "src/*.cpp")
add_executable(myapp ${SOURCES})

# ✅ Good - explicit list
add_executable(myapp
    src/main.cpp
    src/utils.cpp
    src/config.cpp
)

# ✅ Also good - variable with explicit list
set(SOURCES
    src/main.cpp
    src/utils.cpp
    src/config.cpp
)
add_executable(myapp ${SOURCES})
```

**Why:** When you add `src/new_feature.cpp`, CMake doesn't re-configure, so the file won't be compiled until you manually re-run CMake.

### 4. Out-of-Source Builds Always

Never build in your source directory. Always use a separate build directory.

```bash
# ✅ Correct - out-of-source build
cmake -S . -B build
cmake --build build

# ❌ Wrong - pollutes source directory
cmake .
make
```

**Benefits:**

- Clean source tree (no build artifacts mixed with code)
- Multiple build configurations simultaneously
- Easy to clean (just delete build directory)
- `.gitignore` is simpler

### 5. Set Minimum CMake Version Appropriately

Use a recent version but be realistic about user requirements.

```cmake
# ✅ Good - modern but widely available
cmake_minimum_required(VERSION 3.15)

# 3.15: target_link_directories(), better generator expressions
# 3.14: FetchContent_MakeAvailable()
# 3.12: object library improvements
```

**Guidelines:**

- **3.15+** for new projects (widely available, modern features)
- **3.10-3.14** if supporting older systems
- **Avoid 3.0-3.9** (missing critical features)

### 6. Use target_compile_features() for C++ Standard

Prefer feature requirements over directly setting `CMAKE_CXX_STANDARD`.

```cmake
# ✅ Best - portable and clear
add_executable(myapp main.cpp)
target_compile_features(myapp PRIVATE cxx_std_17)

# ✅ Also good - explicit property
set_target_properties(myapp PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# ❌ Avoid - global setting affects all targets
set(CMAKE_CXX_STANDARD 17)
```

**Why target_compile_features():** It's more portable and explicitly states "this target needs C++17," making requirements obvious.

## Project Structure Best Practices

### Directory Layout

Organize projects with a standard structure:

```
project/
├── CMakeLists.txt          # Root CMakeLists
├── cmake/                  # CMake modules and scripts
│   ├── Dependencies.cmake  # Dependency management
│   └── CompilerWarnings.cmake
├── include/                # Public headers
│   └── myproject/
│       └── api.h
├── src/                    # Implementation
│   ├── CMakeLists.txt
│   ├── main.cpp
│   └── impl.cpp
├── libs/                   # Internal libraries
│   └── mylib/
│       ├── CMakeLists.txt
│       ├── include/
│       └── src/
├── external/               # Third-party code (if vendored)
├── tests/                  # Test code
│   └── CMakeLists.txt
├── docs/                   # Documentation
└── examples/               # Example programs
    └── CMakeLists.txt
```

### Root CMakeLists.txt Pattern

```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# Global settings (minimal)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_EXAMPLES "Build examples" OFF)

# Dependencies
include(cmake/Dependencies.cmake)

# Main project
add_subdirectory(src)

# Optional components
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
```

### Library CMakeLists.txt Pattern

```cmake
add_library(mylib
    src/implementation.cpp
    src/utils.cpp
)

# Alias for consistent usage
add_library(MyProject::mylib ALIAS mylib)

target_include_directories(mylib
    PRIVATE src/
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(mylib PUBLIC cxx_std_17)

target_link_libraries(mylib
    PRIVATE internal_dep
    PUBLIC external_api_dep
)
```

The alias `MyProject::mylib` allows using the library consistently whether it's built as part of your project or found via `find_package()`.

## Dependency Management

### Prefer FetchContent for Small Libraries

```cmake
include(FetchContent)

set(JSON_BuildTests OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    GIT_SHALLOW ON
)

FetchContent_MakeAvailable(json)
```

### Use find_package() for System Libraries

```cmake
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)

target_link_libraries(myapp PRIVATE
    Threads::Threads
    OpenSSL::SSL
)
```

### Hybrid Approach

Try system package first, fall back to fetch:

```cmake
find_package(fmt 9.0 QUIET)

if(NOT fmt_FOUND)
    message(STATUS "fmt not found, fetching...")
    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG 9.1.0
    )
    FetchContent_MakeAvailable(fmt)
endif()
```

## Compiler Warnings

Enable warnings per-target, not globally:

```cmake
function(set_project_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE
            /W4          # High warning level
            /WX          # Warnings as errors
        )
    else()
        target_compile_options(${target} PRIVATE
            -Wall
            -Wextra
            -Wpedantic
            -Werror      # Warnings as errors
        )
    endif()
endfunction()

# Use it
add_executable(myapp main.cpp)
set_project_warnings(myapp)
```

Store this function in `cmake/CompilerWarnings.cmake` and include it.

## Build Types

Always provide a sensible default:

```cmake
# Set default build type
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
        "Debug" "Release" "MinSizeRel" "RelWithDebInfo"
    )
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
```

## Installation

Make libraries installable and discoverable:

```cmake
install(TARGETS mylib
    EXPORT MyProjectTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
)

install(DIRECTORY include/
    DESTINATION include
)

# Generate and install CMake config files
include(CMakePackageConfigHelpers)

configure_package_config_file(
    cmake/MyProjectConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake
    INSTALL_DESTINATION lib/cmake/MyProject
)

write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake
    DESTINATION lib/cmake/MyProject
)

install(EXPORT MyProjectTargets
    FILE MyProjectTargets.cmake
    NAMESPACE MyProject::
    DESTINATION lib/cmake/MyProject
)
```

Now users can `find_package(MyProject)` after installation.

## Common Anti-Patterns to Avoid

### Don't Use Global Commands

```cmake
# ❌ Don't do this
include_directories(include/)
link_directories(/usr/local/lib)
add_definitions(-DDEBUG)

# ✅ Do this
target_include_directories(myapp PRIVATE include/)
target_link_libraries(myapp PRIVATE somelib)
target_compile_definitions(myapp PRIVATE DEBUG)
```

### Don't Modify CMAKE_CXX_FLAGS Directly

```cmake
# ❌ Avoid
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# ✅ Better
target_compile_options(myapp PRIVATE -Wall)
```

### Don't Use Absolute Paths

```cmake
# ❌ Breaks on other systems
include_directories(/home/user/myproject/include)

# ✅ Use relative or generated paths
target_include_directories(myapp PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

### Don't Build in Source Directory

```cmake
# Prevent in-source builds
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR
        "In-source builds are not allowed. "
        "Please create a build directory and use cmake from there."
    )
endif()
```

## Testing

Integrate testing cleanly:

```cmake
if(BUILD_TESTS)
    enable_testing()
    
    # Fetch testing framework
    FetchContent_Declare(
        catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG v3.3.2
    )
    FetchContent_MakeAvailable(catch2)
    
    add_executable(tests
        tests/test_main.cpp
        tests/test_feature.cpp
    )
    
    target_link_libraries(tests PRIVATE
        mylib
        Catch2::Catch2WithMain
    )
    
    include(CTest)
    include(Catch)
    catch_discover_tests(tests)
endif()
```

## Documentation

Document your CMake options and configuration:

```cmake
# At the top of CMakeLists.txt
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)
option(BUILD_TESTS "Build test suite" ON)
option(ENABLE_IPO "Enable interprocedural optimization" ON)

# Show current configuration
message(STATUS "")
message(STATUS "========== Build Configuration ==========")
message(STATUS "CMake version:    ${CMAKE_VERSION}")
message(STATUS "Build type:       ${CMAKE_BUILD_TYPE}")
message(STATUS "Compiler:         ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Shared libs:      ${BUILD_SHARED_LIBS}")
message(STATUS "Build tests:      ${BUILD_TESTS}")
message(STATUS "IPO enabled:      ${ENABLE_IPO}")
message(STATUS "==========================================")
message(STATUS "")
```

## Performance Tips

### Cache Expensive Operations

```cmake
# ✅ Check once, cache result
include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported OUTPUT error)

if(ipo_supported AND ENABLE_IPO)
    set_target_properties(myapp PROPERTIES
        INTERPROCEDURAL_OPTIMIZATION ON
    )
endif()
```

### Use Precompiled Headers (CMake 3.16+)

```cmake
target_precompile_headers(myapp PRIVATE
    <iostream>
    <string>
    <vector>
    "common_header.h"
)
```

### Parallel Builds

```bash
# Use all cores
cmake --build build --parallel

# Or specific number
cmake --build build --parallel 8
```

## Quick Reference Checklist

:::success Essential Best Practices

✅ **Use target commands** (`target_*` not global commands)  
✅ **Always specify visibility** (PRIVATE/PUBLIC/INTERFACE)  
✅ **Avoid file(GLOB)** for source files  
✅ **Out-of-source builds** always  
✅ **CMake 3.15+** minimum version  
✅ **target_compile_features()** for C++ standard  
✅ **find_package()** for system libraries  
✅ **FetchContent** for header-only/small libs  
✅ **Enable warnings** per-target  
✅ **Set default build type**  
✅ **Document options** with comments  
✅ **Test on multiple platforms**  
✅ **Use generator expressions** for conditionals  
✅ **Create ALIAS targets** for consistency  
✅ **Make libraries installable**
:::

## Example: Complete Modern Project

```cmake
cmake_minimum_required(VERSION 3.15)
project(ModernProject VERSION 1.0.0 LANGUAGES CXX)

# Prevent in-source builds
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "In-source builds not allowed")
endif()

# Global settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Default build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Options
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)
option(BUILD_TESTS "Build tests" ON)

# Dependencies
find_package(Threads REQUIRED)

include(FetchContent)
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(json)

# Library
add_library(mylib
    src/mylib.cpp
    include/mylib.h
)

add_library(ModernProject::mylib ALIAS mylib)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(mylib
    PUBLIC nlohmann_json::nlohmann_json
    PRIVATE Threads::Threads
)

# Executable
add_executable(myapp src/main.cpp)
target_link_libraries(myapp PRIVATE ModernProject::mylib)

# Warnings
if(MSVC)
    target_compile_options(myapp PRIVATE /W4)
else()
    target_compile_options(myapp PRIVATE -Wall -Wextra)
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
install(TARGETS myapp mylib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
```

This follows all modern CMake best practices in a clean, maintainable structure.
