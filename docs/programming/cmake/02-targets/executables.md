---
id: executables
title: Executable Targets
sidebar_label: Executable Targets
sidebar_position: 1
tags: [ c++, cmake ]
---

# Executable Targets

## Creating Executables

The `add_executable()` command creates a build target for an executable program.

## Basic Syntax

```cmake
add_executable(target_name
    source1.cpp
    source2.cpp
    ...
)
```

## Simple Examples

### Single File

```cmake
cmake_minimum_required(VERSION 3.15)
project(HelloWorld)

add_executable(hello main.cpp)
```

```cpp title="main.cpp"
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
```

### Multiple Files

```cmake
add_executable(myapp
    src/main.cpp
    src/utils.cpp
    src/config.cpp
    include/utils.h
    include/config.h
)
```

:::info Including Headers
Header files are optional but recommended - helps IDEs index them.
:::

## Organizing Source Files

### Using Variables

```cmake
set(APP_SOURCES
    src/main.cpp
    src/engine.cpp
    src/renderer.cpp
)

set(APP_HEADERS
    include/engine.h
    include/renderer.h
)

add_executable(myapp ${APP_SOURCES} ${APP_HEADERS})
```

### Separate by Type

```cmake
set(CORE_SOURCES
    src/core/main.cpp
    src/core/app.cpp
)

set(GRAPHICS_SOURCES
    src/graphics/renderer.cpp
    src/graphics/shader.cpp
)

set(ALL_SOURCES
    ${CORE_SOURCES}
    ${GRAPHICS_SOURCES}
)

add_executable(game ${ALL_SOURCES})
```

## Target Properties

### C++ Standard

```cmake
add_executable(myapp main.cpp)

# Method 1: Using target_compile_features (recommended)
target_compile_features(myapp PRIVATE cxx_std_17)

# Method 2: Using set_property
set_property(TARGET myapp PROPERTY CXX_STANDARD 17)
set_property(TARGET myapp PROPERTY CXX_STANDARD_REQUIRED ON)

# Method 3: Using set_target_properties
set_target_properties(myapp PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)
```

:::success Recommended Approach
Use `target_compile_features()` - it's more portable and explicit.
:::

### Output Name

```cmake
add_executable(myapp main.cpp)

# Change executable name
set_target_properties(myapp PROPERTIES
    OUTPUT_NAME "MyApplication"
)

# Result: MyApplication (not myapp)
```

### Output Directory

```cmake
add_executable(myapp main.cpp)

# Put executable in bin/
set_target_properties(myapp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Different per configuration
set_target_properties(myapp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/debug"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/release"
)
```

## Include Directories

```cmake
add_executable(myapp 
    src/main.cpp
    src/utils.cpp
)

# Private include directories (only for this target)
target_include_directories(myapp PRIVATE
    include/
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Public include directories (for this target and dependents)
target_include_directories(myapp PUBLIC
    ${PROJECT_SOURCE_DIR}/public_include
)
```

**Directory structure:**

```
project/
├── CMakeLists.txt
├── include/          # Private headers
│   └── utils.h
├── src/
│   ├── main.cpp
│   └── utils.cpp
└── public_include/   # Public headers
    └── api.h
```

## Compile Definitions

Add preprocessor macros:

```cmake
add_executable(myapp main.cpp)

target_compile_definitions(myapp PRIVATE
    APP_VERSION="1.0.0"
    ENABLE_LOGGING
    MAX_CONNECTIONS=100
)
```

In code:

```cpp
#ifdef ENABLE_LOGGING
    std::cout << "Logging enabled" << std::endl;
#endif

std::cout << "Version: " << APP_VERSION << std::endl;
std::cout << "Max connections: " << MAX_CONNECTIONS << std::endl;
```

### Conditional Definitions

```cmake
add_executable(myapp main.cpp)

# Platform-specific
if(WIN32)
    target_compile_definitions(myapp PRIVATE PLATFORM_WINDOWS)
elseif(UNIX)
    target_compile_definitions(myapp PRIVATE PLATFORM_UNIX)
endif()

# Build type specific
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(myapp PRIVATE DEBUG_MODE)
endif()
```

## Compile Options (Compiler Flags)

```cmake
add_executable(myapp main.cpp)

# GCC/Clang warnings
target_compile_options(myapp PRIVATE
    -Wall
    -Wextra
    -pedantic
    -Werror
)

# MSVC warnings
if(MSVC)
    target_compile_options(myapp PRIVATE
        /W4
        /WX
    )
endif()
```

### Generator Expressions

```cmake
add_executable(myapp main.cpp)

target_compile_options(myapp PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
    $<$<CONFIG:Debug>:-g3>
    $<$<CONFIG:Release>:-O3>
)
```

## Linking Libraries

```cmake
add_executable(myapp main.cpp)

# Link with libraries
target_link_libraries(myapp PRIVATE
    mylib
    Threads::Threads
    OpenSSL::SSL
)
```

**Visibility keywords:**

- `PRIVATE` - Only this target needs it
- `PUBLIC` - This target and dependents need it (rarely used for executables)
- `INTERFACE` - Only dependents need it (not applicable to executables)

:::info Executables Usually Use PRIVATE
Executables typically use `PRIVATE` since nothing depends on them.
:::

## Platform-Specific Executables

### Windows GUI Application

```cmake
# Console application (default)
add_executable(myapp_console main.cpp)

# GUI application (no console window)
add_executable(myapp_gui WIN32 main.cpp)
```

### macOS Application Bundle

```cmake
add_executable(MyApp MACOSX_BUNDLE main.cpp)

set_target_properties(MyApp PROPERTIES
    MACOSX_BUNDLE_BUNDLE_NAME "My Application"
    MACOSX_BUNDLE_GUI_IDENTIFIER "com.example.myapp"
    MACOSX_BUNDLE_SHORT_VERSION_STRING "1.0"
)
```

## Adding Sources Dynamically

### target_sources()

```cmake
add_executable(myapp main.cpp)

# Add more sources later
target_sources(myapp PRIVATE
    utils.cpp
    config.cpp
)

# Conditional sources
if(WIN32)
    target_sources(myapp PRIVATE windows_impl.cpp)
else()
    target_sources(myapp PRIVATE unix_impl.cpp)
endif()
```

## Complete Example

```cmake
cmake_minimum_required(VERSION 3.15)
project(GameEngine VERSION 1.0.0)

# Executable
add_executable(game)

# Sources
target_sources(game PRIVATE
    src/main.cpp
    src/engine.cpp
    src/renderer.cpp
    src/input.cpp
)

# C++ standard
target_compile_features(game PRIVATE cxx_std_17)

# Include directories
target_include_directories(game PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Preprocessor definitions
target_compile_definitions(game PRIVATE
    ENGINE_VERSION="${PROJECT_VERSION}"
    $<$<CONFIG:Debug>:DEBUG_MODE>
    $<$<CONFIG:Release>:RELEASE_MODE>
)

# Compiler warnings
target_compile_options(game PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -pedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

# Link libraries
find_package(SDL2 REQUIRED)
find_package(OpenGL REQUIRED)

target_link_libraries(game PRIVATE
    SDL2::SDL2
    OpenGL::GL
)

# Output directory
set_target_properties(game PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Installation
install(TARGETS game DESTINATION bin)
```

## Multiple Executables

```cmake
# Main application
add_executable(app src/main.cpp src/app.cpp)
target_link_libraries(app PRIVATE mylib)

# Tool #1
add_executable(tool1 tools/tool1.cpp)
target_link_libraries(tool1 PRIVATE mylib)

# Tool #2
add_executable(tool2 tools/tool2.cpp)
target_link_libraries(tool2 PRIVATE mylib)

# Build all by default
# Or exclude tools:
set_target_properties(tool1 tool2 PROPERTIES
    EXCLUDE_FROM_ALL TRUE
)
```

Build specific target:

```bash
cmake --build build --target tool1
```

## Imported Executables

Sometimes you need to reference external executables:

```cmake
# Create imported executable target
add_executable(external_tool IMPORTED)

# Set location
set_target_properties(external_tool PROPERTIES
    IMPORTED_LOCATION "/usr/bin/external_tool"
)

# Use in custom command
add_custom_command(
    OUTPUT generated_file.txt
    COMMAND external_tool input.txt generated_file.txt
    DEPENDS input.txt
)
```

## Common Patterns

### Executable with Library

```cmake
# Library (reusable logic)
add_library(engine STATIC
    src/engine.cpp
    src/renderer.cpp
)

target_include_directories(engine PUBLIC include)

# Executable (just main + UI)
add_executable(game src/main.cpp)
target_link_libraries(game PRIVATE engine)

# Test executable
add_executable(engine_test tests/test_engine.cpp)
target_link_libraries(engine_test PRIVATE engine)
```

### Configuration File

Generate version header:

```cmake
# Configure version header
configure_file(
    "${CMAKE_SOURCE_DIR}/version.h.in"
    "${CMAKE_BINARY_DIR}/version.h"
)

add_executable(myapp src/main.cpp)

# Include generated header
target_include_directories(myapp PRIVATE
    "${CMAKE_BINARY_DIR}"
)
```

```cpp title="version.h.in"
#define VERSION_MAJOR @PROJECT_VERSION_MAJOR@
#define VERSION_MINOR @PROJECT_VERSION_MINOR@
#define VERSION_STRING "@PROJECT_VERSION@"
```

## Best Practices

:::success Recommendations

1. **Use target-based commands**

   ```cmake
   # ✅ Good
   target_include_directories(myapp PRIVATE include/)
   
   # ❌ Avoid
   include_directories(include/)
   ```

2. **Explicit source lists**

   ```cmake
   # ✅ Good
   add_executable(myapp main.cpp utils.cpp)
   
   # ❌ Avoid
   file(GLOB SOURCES "*.cpp")
   add_executable(myapp ${SOURCES})
   ```

3. **Set C++ standard per target**

   ```cmake
   target_compile_features(myapp PRIVATE cxx_std_17)
   ```

4. **Use PRIVATE for executable dependencies**

   ```cmake
   target_link_libraries(myapp PRIVATE mylib)
   ```

5. **Organize by feature, not file type**

   ```
   src/
   ├── core/       # Core functionality
   ├── graphics/   # Graphics code
   └── audio/      # Audio code
   ```

:::

## Troubleshooting

### Undefined reference errors

```cmake
# Ensure libraries are linked
target_link_libraries(myapp PRIVATE required_lib)
```

### Header not found

```cmake
# Add include directory
target_include_directories(myapp PRIVATE include/)
```

### Wrong C++ standard

```cmake
# Set explicitly
target_compile_features(myapp PRIVATE cxx_std_17)
```

### Multiple main() functions

- Only one `.cpp` file should have `int main()`
- Or create separate executables
