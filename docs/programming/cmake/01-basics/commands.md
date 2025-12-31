---
id: commands
title: Essential CMake Commands
sidebar_label: Commands
tags: [ c++, cmake ]
---

# Essential CMake Commands

## Core Commands

### message()

Print messages during configuration.

```cmake
message(STATUS "Configuring project...")
message(WARNING "This is deprecated")
message(SEND_ERROR "Error but continue")
message(FATAL_ERROR "Stop immediately")
message("Regular message")
```

**Types:**

- `STATUS` - Informational (prefixed with `--`)
- `WARNING` - Yellow warning
- `SEND_ERROR` - Red error, continues configuration
- `FATAL_ERROR` - Red error, stops immediately
- None - Regular output

**Example:**

```cmake
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

if(NOT CMAKE_BUILD_TYPE)
    message(WARNING "Build type not set, using Release")
    set(CMAKE_BUILD_TYPE Release)
endif()
```

### add_executable()

Create an executable target.

```cmake
add_executable(target_name
    source1.cpp
    source2.cpp
    header.h
)
```

:::info Header Files
Including headers is optional but helps IDEs index them.
:::

**Examples:**

```cmake
# Simple
add_executable(myapp main.cpp)

# Multiple files
add_executable(myapp
    src/main.cpp
    src/utils.cpp
    src/config.cpp
)

# Using variables
set(APP_SOURCES
    main.cpp
    utils.cpp
)
add_executable(myapp ${APP_SOURCES})

# WIN32 console vs GUI app
add_executable(myapp WIN32 main.cpp)  # GUI app on Windows
```

### add_library()

Create a library target.

```cmake
add_library(mylib STATIC
    src/mylib.cpp
    include/mylib.h
)
```

**Library types:**

- `STATIC` - `.a` / `.lib` (linked at compile time)
- `SHARED` - `.so` / `.dll` (linked at runtime)
- `MODULE` - Plugin loaded at runtime
- `INTERFACE` - Header-only library
- `OBJECT` - Compiled objects, no archive

**Examples:**

```cmake
# Static library
add_library(mylib STATIC mylib.cpp)

# Shared library
add_library(mylib SHARED mylib.cpp)

# Header-only library
add_library(mylib INTERFACE)
target_include_directories(mylib INTERFACE include/)

# Object library (compile once, link many times)
add_library(common OBJECT common.cpp)
add_executable(app1 app1.cpp $<TARGET_OBJECTS:common>)
add_executable(app2 app2.cpp $<TARGET_OBJECTS:common>)
```

### target_link_libraries()

Link libraries to a target.

```cmake
target_link_libraries(target
    <PRIVATE|PUBLIC|INTERFACE> lib1 lib2 ...
)
```

**Visibility keywords:**

- `PRIVATE` - Only this target needs it
- `PUBLIC` - This target and dependents need it
- `INTERFACE` - Only dependents need it

```cmake
add_library(engine STATIC engine.cpp)
add_library(ui STATIC ui.cpp)
add_executable(game main.cpp)

# engine needs pthread privately
target_link_libraries(engine PRIVATE Threads::Threads)

# ui needs engine and exposes it
target_link_libraries(ui PUBLIC engine)

# game needs ui (and transitively gets engine)
target_link_libraries(game PRIVATE ui)
```

:::success Transitive Dependencies
`PUBLIC` and `INTERFACE` propagate requirements to dependents automatically!
:::

### target_include_directories()

Add include paths to a target.

```cmake
target_include_directories(target
    <PRIVATE|PUBLIC|INTERFACE>
    include/
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

**Example:**

```cmake
add_library(mylib mylib.cpp)

# Only mylib needs these headers
target_include_directories(mylib PRIVATE src/)

# Anyone using mylib needs these headers  
target_include_directories(mylib PUBLIC include/)

# Header-only library
add_library(headerlib INTERFACE)
target_include_directories(headerlib INTERFACE include/)
```

### target_compile_definitions()

Add preprocessor definitions.

```cmake
target_compile_definitions(target
    <PRIVATE|PUBLIC|INTERFACE>
    DEFINE_NAME
    DEFINE_NAME=value
)
```

**Example:**

```cmake
add_executable(myapp main.cpp)

# Define DEBUG macro
target_compile_definitions(myapp PRIVATE DEBUG)

# Define with value
target_compile_definitions(myapp PRIVATE 
    VERSION_MAJOR=1
    VERSION_MINOR=2
)

# Conditional
if(WIN32)
    target_compile_definitions(myapp PRIVATE PLATFORM_WINDOWS)
endif()
```

In code:

```cpp
#ifdef DEBUG
    std::cout << "Debug mode" << std::endl;
#endif

#ifdef PLATFORM_WINDOWS
    #include <windows.h>
#endif
```

### target_compile_options()

Add compiler flags.

```cmake
target_compile_options(target
    <PRIVATE|PUBLIC|INTERFACE>
    -Wall -Wextra
)
```

**Example:**

```cmake
add_executable(myapp main.cpp)

if(MSVC)
    target_compile_options(myapp PRIVATE /W4 /WX)
else()
    target_compile_options(myapp PRIVATE 
        -Wall 
        -Wextra 
        -pedantic
        -Werror
    )
endif()

# Optimization
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(myapp PRIVATE -O3)
endif()
```

:::warning Use Sparingly
Prefer `target_compile_features()` for C++ standard and portable options.
:::

### target_compile_features()

Require specific C++ features.

```cmake
target_compile_features(target
    <PRIVATE|PUBLIC|INTERFACE>
    cxx_std_17
)
```

**Available standards:**

- `cxx_std_11`, `cxx_std_14`, `cxx_std_17`, `cxx_std_20`, `cxx_std_23`

**Specific features:**

```cmake
target_compile_features(mylib PUBLIC
    cxx_std_17
    cxx_constexpr
    cxx_lambdas
)
```

## Control Flow

### if/elseif/else

```cmake
if(condition)
    # ...
elseif(other_condition)
    # ...
else()
    # ...
endif()
```

**Conditions:**

```cmake
# Variable existence
if(DEFINED MY_VAR)

# Boolean
if(BUILD_TESTS)

# String comparison
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")

# Numeric comparison
if(VERSION_MAJOR GREATER 2)
if(VERSION_MINOR LESS_EQUAL 5)

# File existence
if(EXISTS "${CMAKE_SOURCE_DIR}/config.txt")
if(IS_DIRECTORY "${CMAKE_SOURCE_DIR}/libs")

# Platform
if(WIN32)
if(UNIX)
if(APPLE)

# Logical operators
if(BUILD_TESTS AND BUILD_EXAMPLES)
if(USE_OPENGL OR USE_VULKAN)
if(NOT DISABLE_WARNINGS)
```

**Examples:**

```cmake
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Debug build enabled")
    target_compile_definitions(myapp PRIVATE DEBUG_MODE)
endif()

if(WIN32)
    target_sources(myapp PRIVATE windows_main.cpp)
elseif(APPLE)
    target_sources(myapp PRIVATE macos_main.cpp)
else()
    target_sources(myapp PRIVATE linux_main.cpp)
endif()
```

### foreach

Iterate over lists.

```cmake
foreach(var IN LISTS list_var)
    # ${var} holds current item
endforeach()
```

**Examples:**

```cmake
# Simple list
set(NUMBERS 1 2 3 4 5)
foreach(num IN LISTS NUMBERS)
    message(STATUS "Number: ${num}")
endforeach()

# Range
foreach(i RANGE 5)
    message(STATUS "i = ${i}")  # 0, 1, 2, 3, 4, 5
endforeach()

foreach(i RANGE 2 5)
    message(STATUS "i = ${i}")  # 2, 3, 4, 5
endforeach()

# Multiple items
set(SOURCES main.cpp utils.cpp helper.cpp)
foreach(src IN LISTS SOURCES)
    message(STATUS "Source: ${src}")
endforeach()

# Practical: add tests
set(TEST_NAMES test_math test_string test_file)
foreach(test IN LISTS TEST_NAMES)
    add_executable(${test} ${test}.cpp)
    add_test(NAME ${test} COMMAND ${test})
endforeach()
```

### while

```cmake
set(i 0)
while(i LESS 5)
    message(STATUS "i = ${i}")
    math(EXPR i "${i} + 1")
endwhile()
```

## Functions and Macros

### function()

Create reusable functions.

```cmake
function(function_name arg1 arg2)
    # Function body
    # ${arg1}, ${arg2} available
endfunction()
```

**Examples:**

```cmake
function(add_my_executable name)
    add_executable(${name} ${ARGN})
    target_compile_features(${name} PRIVATE cxx_std_17)
    target_compile_options(${name} PRIVATE -Wall -Wextra)
endfunction()

# Use it
add_my_executable(app1 main.cpp utils.cpp)
add_my_executable(app2 other_main.cpp)

# With named arguments
function(create_test)
    cmake_parse_arguments(
        TEST                      # Prefix
        "WILL_FAIL"              # Options
        "NAME"                    # Single-value args
        "SOURCES;LIBRARIES"       # Multi-value args
        ${ARGN}
    )
    
    add_executable(${TEST_NAME} ${TEST_SOURCES})
    target_link_libraries(${TEST_NAME} PRIVATE ${TEST_LIBRARIES})
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
    
    if(TEST_WILL_FAIL)
        set_tests_properties(${TEST_NAME} PROPERTIES WILL_FAIL TRUE)
    endif()
endfunction()

# Usage
create_test(
    NAME test_mylib
    SOURCES test.cpp
    LIBRARIES mylib
)
```

### macro()

Similar to functions but different scoping.

```cmake
macro(macro_name arg1)
    # Macro body
endmacro()
```

:::warning Function vs Macro

- **Function**: Creates new scope, use `PARENT_SCOPE` to modify parent
- **Macro**: No new scope, directly modifies caller's scope
- **Prefer functions** for most cases
  :::

## File Operations

### configure_file()

Generate files from templates.

```cmake
configure_file(input output [@ONLY])
```

```cmake
# config.h.in
#define VERSION "@PROJECT_VERSION@"
#define COMPILER "@CMAKE_CXX_COMPILER_ID@"
```

```cmake
configure_file(
    "${PROJECT_SOURCE_DIR}/config.h.in"
    "${PROJECT_BINARY_DIR}/config.h"
)
```

### file()

File system operations.

```cmake
# Read
file(READ "file.txt" content)

# Write
file(WRITE "output.txt" "content")
file(APPEND "output.txt" "more content")

# Copy
file(COPY src/file.txt DESTINATION ${CMAKE_BINARY_DIR})

# Glob (use sparingly!)
file(GLOB sources "src/*.cpp")

# Download
file(DOWNLOAD 
    "https://example.com/file.zip"
    "${CMAKE_BINARY_DIR}/file.zip"
)

# Make directory
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/output")
```

## Other Important Commands

### include()

Include another CMake file.

```cmake
include(CMakePackageConfigHelpers)
include(${CMAKE_SOURCE_DIR}/cmake/Utilities.cmake)
```

### find_package()

Find external dependencies.

```cmake
find_package(Threads REQUIRED)
find_package(OpenCV 4.5 REQUIRED)
find_package(Boost 1.70 COMPONENTS filesystem regex)
```

### add_subdirectory()

Add a subdirectory to build.

```cmake
add_subdirectory(src)
add_subdirectory(libs/mylib)
add_subdirectory(external/fmt EXCLUDE_FROM_ALL)
```

`EXCLUDE_FROM_ALL` - don't build by default

### install()

Define installation rules.

```cmake
install(TARGETS myapp mylib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES config.txt DESTINATION etc)
install(DIRECTORY include/ DESTINATION include)
```

### option()

Create a CMake option.

```cmake
option(BUILD_TESTS "Build test suite" ON)
option(ENABLE_LTO "Enable link-time optimization" OFF)
```

User can set:

```bash title="Terminal"
cmake -DBUILD_TESTS=OFF ..
```

## Quick Reference Table

| Command                        | Purpose                     |
|--------------------------------|-----------------------------|
| `add_executable()`             | Create executable           |
| `add_library()`                | Create library              |
| `target_link_libraries()`      | Link libraries              |
| `target_include_directories()` | Add include paths           |
| `target_compile_definitions()` | Add preprocessor macros     |
| `target_compile_options()`     | Add compiler flags          |
| `target_compile_features()`    | Require C++ features        |
| `find_package()`               | Find external package       |
| `add_subdirectory()`           | Add subdirectory            |
| `install()`                    | Install targets/files       |
| `message()`                    | Print message               |
| `option()`                     | Create user option          |
| `configure_file()`             | Generate file from template |
