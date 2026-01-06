---
id: multi-directory
title: Multi-Directory Projects
sidebar_label: Multi-Directory
tags: [cmake, project-structure, organization, subdirectories]
---

# Multi-Directory Projects

## Why Multiple Directories?

As projects grow, keeping everything in one directory becomes unmanageable. Multi-directory organization provides:

- **Logical separation** of components (UI, business logic, data layer)
- **Reusable libraries** that can be built independently
- **Parallel compilation** - separate directories can build simultaneously
- **Team scalability** - different teams work on different directories
- **Selective building** - build only what you need

The key is structuring directories so they represent actual architectural boundaries, not just arbitrary file groupings.

## Basic Structure

A typical multi-directory project:

```
project/
├── CMakeLists.txt              # Root configuration
├── app/                        # Main application
│   ├── CMakeLists.txt
│   └── main.cpp
├── libs/                       # Internal libraries
│   ├── core/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   └── src/
│   ├── ui/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   └── src/
│   └── utils/
│       ├── CMakeLists.txt
│       ├── include/
│       └── src/
├── external/                   # Third-party dependencies
│   └── vendored_lib/
└── tests/                      # Test suite
    └── CMakeLists.txt
```

## Root CMakeLists.txt

The root file orchestrates the entire build:

```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# Project-wide settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Output directories - keep binaries organized
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_EXAMPLES "Build examples" OFF)

# Build order matters - dependencies first
add_subdirectory(libs/utils)     # No dependencies
add_subdirectory(libs/core)      # Depends on utils
add_subdirectory(libs/ui)        # Depends on core
add_subdirectory(app)            # Depends on everything

# Optional components
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
```

**Key points:**

- Libraries are built before executables that use them
- Output directories centralize all binaries
- Optional components are conditionally included
- Build order reflects dependency chain

## Library Directories

Each library gets its own CMakeLists.txt:

```cmake title="libs/core/CMakeLists.txt"
add_library(core
    src/engine.cpp
    src/processor.cpp
    include/core/engine.h
    include/core/processor.h
)

# Create namespaced alias for consistency
add_library(MyProject::core ALIAS core)

# Public headers available to users
target_include_directories(core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        src/  # Private implementation headers
)

# Link dependencies
target_link_libraries(core
    PUBLIC MyProject::utils    # Exposed in our API
    PRIVATE Threads::Threads   # Internal use only
)

target_compile_features(core PUBLIC cxx_std_17)
```

**Why alias?** The alias `MyProject::core` works whether the library is built as part of your project or installed and found via `find_package()`. This consistency prevents errors.

**Generator expressions** like `$<BUILD_INTERFACE:...>` provide different paths during build vs. after installation.

## Application Directory

The application depends on libraries:

```cmake title="app/CMakeLists.txt"
add_executable(myapp
    main.cpp
    application.cpp
)

# Link all required libraries
target_link_libraries(myapp PRIVATE
    MyProject::core
    MyProject::ui
)

# Installation
install(TARGETS myapp
    RUNTIME DESTINATION bin
)
```

Because we used `add_library(MyProject::core ALIAS core)`, the linking syntax is consistent and clear.

## Dependency Flow

Understanding how dependencies flow through directories is crucial:

```
utils (no dependencies)
  ↓
core (depends on utils)
  ↓
ui (depends on core, transitively gets utils)
  ↓
app (depends on ui, transitively gets core and utils)
```

If `core` links to `utils` with `PUBLIC`, then `ui` automatically gets `utils` too. This transitive propagation is powerful but requires careful use of visibility keywords.

```cmake
# In libs/core/CMakeLists.txt
target_link_libraries(core
    PUBLIC MyProject::utils    # ui gets this automatically
)

# In libs/ui/CMakeLists.txt
target_link_libraries(ui
    PUBLIC MyProject::core     # app gets core AND utils
)

# In app/CMakeLists.txt
target_link_libraries(app
    PRIVATE MyProject::ui      # Gets ui, core, utils
)
```

## Include Directory Organization

Proper include directory structure prevents conflicts and clarifies dependencies:

```
libs/core/
├── include/
│   └── myproject/           # Project namespace
│       └── core/            # Component namespace
│           ├── engine.h
│           └── processor.h
└── src/
    ├── engine.cpp
    └── internal.h           # Private header
```

Usage in code:

```cpp
// Clear where this comes from
#include <myproject/core/engine.h>
#include <myproject/utils/helper.h>

// Not this - conflicts with other libraries
#include <engine.h>  // Which engine?
```

Configure in CMake:

```cmake
target_include_directories(core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE
        src/
)
```

Users include: `#include <myproject/core/engine.h>`  
Implementation includes private headers directly: `#include "internal.h"`

## Header-Only Libraries

Some components are header-only:

```cmake title="libs/utils/CMakeLists.txt"
add_library(utils INTERFACE)

add_library(MyProject::utils ALIAS utils)

target_include_directories(utils INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_compile_features(utils INTERFACE cxx_std_17)

# Header-only libraries can have interface dependencies
target_link_libraries(utils INTERFACE
    nlohmann_json::nlohmann_json
)
```

`INTERFACE` means the library itself doesn't use these settings, but anyone linking to it does.

## Platform-Specific Directories

Organize platform-specific code:

```
libs/platform/
├── CMakeLists.txt
├── include/
│   └── myproject/
│       └── platform/
│           └── api.h        # Common API
└── src/
    ├── windows/
    │   └── implementation.cpp
    ├── linux/
    │   └── implementation.cpp
    └── macos/
        └── implementation.cpp
```

```cmake title="libs/platform/CMakeLists.txt"
add_library(platform)

target_include_directories(platform
    PUBLIC include/
    PRIVATE src/
)

# Platform-specific sources
if(WIN32)
    target_sources(platform PRIVATE src/windows/implementation.cpp)
elseif(APPLE)
    target_sources(platform PRIVATE src/macos/implementation.cpp)
elseif(UNIX)
    target_sources(platform PRIVATE src/linux/implementation.cpp)
endif()

add_library(MyProject::platform ALIAS platform)
```

## External Dependencies

Handle third-party code in separate directory:

```cmake title="external/CMakeLists.txt"
include(FetchContent)

# Configure all external projects
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
set(FMT_INSTALL OFF CACHE BOOL "" FORCE)

FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)

FetchContent_Declare(fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
)

FetchContent_MakeAvailable(json fmt)
```

```cmake title="Root CMakeLists.txt"
# Fetch dependencies before our code
add_subdirectory(external)

# Now our libraries can use them
add_subdirectory(libs)
add_subdirectory(app)
```

## Testing Directory

Organize tests to mirror source structure:

```
tests/
├── CMakeLists.txt
├── core/
│   ├── test_engine.cpp
│   └── test_processor.cpp
├── ui/
│   └── test_renderer.cpp
└── integration/
    └── test_full_system.cpp
```

```cmake title="tests/CMakeLists.txt"
# Fetch test framework
FetchContent_Declare(catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.3.2
)
FetchContent_MakeAvailable(catch2)

# Test for core library
add_executable(test_core
    core/test_engine.cpp
    core/test_processor.cpp
)

target_link_libraries(test_core PRIVATE
    MyProject::core
    Catch2::Catch2WithMain
)

add_test(NAME CoreTests COMMAND test_core)

# Test for UI library
add_executable(test_ui
    ui/test_renderer.cpp
)

target_link_libraries(test_ui PRIVATE
    MyProject::ui
    Catch2::Catch2WithMain
)

add_test(NAME UITests COMMAND test_ui)

# Integration tests
add_executable(test_integration
    integration/test_full_system.cpp
)

target_link_libraries(test_integration PRIVATE
    MyProject::core
    MyProject::ui
    Catch2::Catch2WithMain
)

add_test(NAME IntegrationTests COMMAND test_integration)
```

## Selective Building

Large projects benefit from building only needed components:

```cmake
# Root CMakeLists.txt
option(BUILD_APP "Build application" ON)
option(BUILD_CORE "Build core library" ON)
option(BUILD_UI "Build UI library" ON)

if(BUILD_CORE)
    add_subdirectory(libs/core)
endif()

if(BUILD_UI AND BUILD_CORE)
    add_subdirectory(libs/ui)
elseif(BUILD_UI)
    message(FATAL_ERROR "UI requires core library")
endif()

if(BUILD_APP AND BUILD_UI AND BUILD_CORE)
    add_subdirectory(app)
endif()
```

Users can now: `cmake -DBUILD_UI=OFF -B build`

## Installation

Install while preserving structure:

```cmake
# In each library's CMakeLists.txt
install(TARGETS core
    EXPORT MyProjectTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    INCLUDES DESTINATION include
)

install(DIRECTORY include/
    DESTINATION include
)

# In root CMakeLists.txt
install(EXPORT MyProjectTargets
    FILE MyProjectTargets.cmake
    NAMESPACE MyProject::
    DESTINATION lib/cmake/MyProject
)
```

After installation, the directory structure is:

```
/usr/local/
├── bin/
│   └── myapp
├── lib/
│   ├── libcore.a
│   ├── libui.a
│   └── cmake/
│       └── MyProject/
│           └── MyProjectTargets.cmake
└── include/
    └── myproject/
        ├── core/
        └── ui/
```

## Complete Example

A realistic multi-directory project:

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(GameEngine VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Options
option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" OFF)
option(BUILD_EDITOR "Build editor application" ON)

# External dependencies
add_subdirectory(external)

# Engine libraries (dependency order)
add_subdirectory(libs/math)       # Math utilities
add_subdirectory(libs/core)       # Core engine
add_subdirectory(libs/graphics)   # Graphics system
add_subdirectory(libs/audio)      # Audio system
add_subdirectory(libs/physics)    # Physics simulation

# Applications
add_subdirectory(game)            # Game application

if(BUILD_EDITOR)
    add_subdirectory(editor)      # Editor application
endif()

# Development tools
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()
```

```cmake title="libs/graphics/CMakeLists.txt"
find_package(OpenGL REQUIRED)

add_library(graphics
    src/renderer.cpp
    src/shader.cpp
    src/texture.cpp
    include/gameengine/graphics/renderer.h
    include/gameengine/graphics/shader.h
)

add_library(GameEngine::graphics ALIAS graphics)

target_include_directories(graphics
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        src/
)

target_link_libraries(graphics
    PUBLIC
        GameEngine::core
        GameEngine::math
        OpenGL::GL
    PRIVATE
        fmt::fmt
)

target_compile_features(graphics PUBLIC cxx_std_17)
```

## Common Patterns

### Utility Functions Directory

Create reusable CMake functions:

```
cmake/
├── CompilerWarnings.cmake
├── Dependencies.cmake
└── InstallHelper.cmake
```

```cmake title="cmake/CompilerWarnings.cmake"
function(target_set_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    else()
        target_compile_options(${target} PRIVATE
            -Wall -Wextra -Wpedantic -Werror
        )
    endif()
endfunction()
```

Use in root:

```cmake
list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)
include(CompilerWarnings)
include(Dependencies)

# Later in subdirectory
target_set_warnings(core)
```

### Plugin Architecture

Organize plugins in subdirectories:

```
plugins/
├── CMakeLists.txt
├── audio_mp3/
│   └── CMakeLists.txt
├── audio_wav/
│   └── CMakeLists.txt
└── image_png/
    └── CMakeLists.txt
```

```cmake title="plugins/CMakeLists.txt"
file(GLOB plugin_dirs RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} */CMakeLists.txt)

foreach(plugin_cmake ${plugin_dirs})
    get_filename_component(plugin_dir ${plugin_cmake} DIRECTORY)
    message(STATUS "Adding plugin: ${plugin_dir}")
    add_subdirectory(${plugin_dir})
endforeach()
```

Each plugin is a MODULE library:

```cmake title="plugins/audio_mp3/CMakeLists.txt"
add_library(audio_mp3 MODULE
    mp3_decoder.cpp
)

target_link_libraries(audio_mp3 PRIVATE GameEngine::core)

# Plugins go to special directory
set_target_properties(audio_mp3 PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/plugins
)
```

## Best Practices

:::success Multi-Directory Guidelines

1. **One target per directory** - clarity and modularity
2. **Use ALIAS targets** - consistency when used internally or externally
3. **Respect dependency order** - add subdirectories in order
4. **Keep includes namespaced** - `myproject/component/header.h`
5. **Separate public/private** - clear API boundaries
6. **Generator expressions for paths** - build vs install differences
7. **Central output directories** - easy to find binaries
8. **Document dependencies** - comments explaining why
   :::

:::warning Common Mistakes

❌ **Circular dependencies** between directories  
❌ **Global commands** affecting all subdirectories  
❌ **Forgetting to add subdirectory** to root  
❌ **Wrong build order** causing link errors  
❌ **Mixing business logic with CMake** code
:::

Multi-directory projects require discipline but provide excellent scalability and maintainability for growing codebases.
