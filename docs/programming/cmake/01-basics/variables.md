---
id: variables
title: CMake Variables
sidebar_label: Variables
tags: [ c++, cmake ]
---

# CMake Variables

## What are Variables?

Variables in CMake store strings, lists, or paths. They're the primary way to store and pass information in your build configuration.

## Basic Variable Operations

### Setting Variables

```cmake
# Simple string
set(MY_VAR "Hello")

# Number (stored as string)
set(VERSION_MAJOR 1)

# Multiple values (creates a list)
set(SOURCES main.cpp utils.cpp helper.cpp)

# With CACHE (persists between runs)
set(BUILD_TYPE "Release" CACHE STRING "Build type")
```

### Using Variables

```cmake
set(GREETING "Hello")
message(STATUS "Greeting: ${GREETING}")

# Output: -- Greeting: Hello
```

:::info Dereferencing
Use `${VAR_NAME}` to access the value. Without `${}`, you get the literal string.
:::

### Unsetting Variables

```cmake
unset(MY_VAR)
unset(CACHE_VAR CACHE)  # Remove from cache
```

## Variable Scope

### Normal Variables (Function/Directory Scope)

```cmake
set(LOCAL_VAR "value")  # Only in current scope

function(my_function)
    set(FUNC_VAR "inside")  # Only in function
    message(STATUS ${FUNC_VAR})  # ✅ Works
endfunction()

message(STATUS ${FUNC_VAR})  # ❌ Undefined!
```

### PARENT_SCOPE

```cmake
function(set_parent)
    set(MY_VAR "value" PARENT_SCOPE)
endfunction()

set_parent()
message(STATUS ${MY_VAR})  # ✅ "value"
```

### Cache Variables (Global/Persistent)

```cmake
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build shared libraries")
```

Cache variables:

- Persist in `CMakeCache.txt`
- Can be overridden from command line
- Visible in GUI tools (ccmake, cmake-gui)

**Override from command line:**

```bash title="Terminal"
cmake -DBUILD_SHARED_LIBS=ON ..
```

## Built-in Variables

### Project Variables

```cmake
project(MyProject VERSION 1.2.3)

message(STATUS "Name: ${PROJECT_NAME}")           # MyProject
message(STATUS "Version: ${PROJECT_VERSION}")     # 1.2.3
message(STATUS "Major: ${PROJECT_VERSION_MAJOR}") # 1
message(STATUS "Source: ${PROJECT_SOURCE_DIR}")   # /path/to/source
message(STATUS "Binary: ${PROJECT_BINARY_DIR}")   # /path/to/build
```

### Common CMake Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CMAKE_SOURCE_DIR` | Top-level source directory | `/home/user/project` |
| `CMAKE_BINARY_DIR` | Top-level build directory | `/home/user/project/build` |
| `CMAKE_CURRENT_SOURCE_DIR` | Current CMakeLists.txt location | `/home/user/project/src` |
| `CMAKE_CURRENT_BINARY_DIR` | Current build subdirectory | `/home/user/project/build/src` |
| `CMAKE_CURRENT_LIST_DIR` | Directory of current list file | `/home/user/project/cmake` |

:::success Use Current Variables
In subdirectories, prefer `CMAKE_CURRENT_SOURCE_DIR` over `CMAKE_SOURCE_DIR`
:::

### Compiler Variables

```cmake
message(STATUS "C++ Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Compiler ID: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Compiler Version: ${CMAKE_CXX_COMPILER_VERSION}")
```

**Common `CMAKE_CXX_COMPILER_ID` values:**

- `GNU` - GCC
- `Clang` - Clang/LLVM
- `MSVC` - Microsoft Visual C++
- `AppleClang` - Apple's Clang

### System Variables

```cmake
message(STATUS "System: ${CMAKE_SYSTEM_NAME}")
message(STATUS "Processor: ${CMAKE_SYSTEM_PROCESSOR}")

if(WIN32)
    message(STATUS "Windows detected")
elseif(UNIX)
    message(STATUS "Unix-like system")
    if(APPLE)
        message(STATUS "macOS detected")
    elseif(LINUX)  # Not standard, use: ${CMAKE_SYSTEM_NAME} STREQUAL "Linux"
        message(STATUS "Linux detected")
    endif()
endif()
```

### Build Configuration Variables

```cmake
# Build type
set(CMAKE_BUILD_TYPE Release)
# Options: Debug, Release, RelWithDebInfo, MinSizeRel

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
```

## List Variables

Lists are semicolon-separated strings.

### Creating Lists

```cmake
# Method 1: Multiple arguments
set(SOURCES main.cpp utils.cpp)

# Method 2: Explicit semicolons
set(SOURCES "main.cpp;utils.cpp")

# Method 3: Append
set(SOURCES main.cpp)
list(APPEND SOURCES utils.cpp helper.cpp)
```

### List Operations

```cmake
set(MY_LIST a b c d e)

# Length
list(LENGTH MY_LIST len)
message(STATUS "Length: ${len}")  # 5

# Get element
list(GET MY_LIST 2 third_element)
message(STATUS "3rd: ${third_element}")  # c

# Append
list(APPEND MY_LIST f g)  # a b c d e f g

# Remove item
list(REMOVE_ITEM MY_LIST c)  # a b d e

# Remove duplicates
list(REMOVE_DUPLICATES MY_LIST)

# Reverse
list(REVERSE MY_LIST)

# Sort
list(SORT MY_LIST)

# Find
list(FIND MY_LIST "d" index)
if(index EQUAL -1)
    message(STATUS "Not found")
else()
    message(STATUS "Found at index ${index}")
endif()
```

:::warning Quoting Lists
When passing lists to commands, don't quote them:

```cmake
# ✅ Correct
add_executable(myapp ${SOURCES})

# ❌ Wrong - treated as single argument
add_executable(myapp "${SOURCES}")
```

:::

## String Operations

### String Manipulation

```cmake
set(STR "Hello World")

# Length
string(LENGTH "${STR}" len)

# Substring
string(SUBSTRING "${STR}" 0 5 result)  # "Hello"

# Replace
string(REPLACE "World" "CMake" result "${STR}")  # "Hello CMake"

# To upper/lower
string(TOUPPER "${STR}" upper)  # "HELLO WORLD"
string(TOLOWER "${STR}" lower)  # "hello world"

# Strip whitespace
string(STRIP "  spaces  " stripped)  # "spaces"
```

### Regular Expressions

```cmake
set(VERSION "v1.2.3-beta")

# Match
string(REGEX MATCH "v([0-9]+)\\.([0-9]+)" match "${VERSION}")
message(STATUS "Match: ${match}")  # v1.2
message(STATUS "Major: ${CMAKE_MATCH_1}")  # 1
message(STATUS "Minor: ${CMAKE_MATCH_2}")  # 2

# Replace
string(REGEX REPLACE "v([0-9.]+).*" "\\1" clean_version "${VERSION}")
message(STATUS "Clean: ${clean_version}")  # 1.2.3
```

## Environment Variables

### Reading

```cmake
# Get environment variable
message(STATUS "PATH: $ENV{PATH}")
message(STATUS "HOME: $ENV{HOME}")

# Store in CMake variable
set(USER_HOME $ENV{HOME})
```

### Setting

```cmake
# Set for current CMake run only
set(ENV{MY_VAR} "value")

# Note: Does NOT persist outside CMake
```

:::warning Temporary Only
`set(ENV{...})` only affects the CMake process, not the system or build process.
:::

## Practical Examples

### Version Header Generation

```cmake
project(MyApp VERSION 1.2.3)

configure_file(
    "${PROJECT_SOURCE_DIR}/version.h.in"
    "${PROJECT_BINARY_DIR}/version.h"
)
```

```cpp title="version.h.in"
#ifndef VERSION_H
#define VERSION_H

#define VERSION_MAJOR @PROJECT_VERSION_MAJOR@
#define VERSION_MINOR @PROJECT_VERSION_MINOR@
#define VERSION_PATCH @PROJECT_VERSION_PATCH@
#define VERSION_STRING "@PROJECT_VERSION@"

#endif
```

Generated `version.h`:

```cpp
#ifndef VERSION_H
#define VERSION_H

#define VERSION_MAJOR 1
#define VERSION_MINOR 2
#define VERSION_PATCH 3
#define VERSION_STRING "1.2.3"

#endif
```

### Platform-Specific Configuration

```cmake
if(WIN32)
    set(PLATFORM_SOURCES src/windows.cpp)
    set(PLATFORM_LIBS ws2_32)
elseif(UNIX)
    set(PLATFORM_SOURCES src/unix.cpp)
    set(PLATFORM_LIBS pthread)
endif()

add_executable(myapp 
    src/main.cpp
    ${PLATFORM_SOURCES}
)

target_link_libraries(myapp PRIVATE ${PLATFORM_LIBS})
```

### Compiler-Specific Flags

```cmake
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    set(WARNINGS -Wall -Wextra -Wpedantic)
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    set(WARNINGS /W4)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(WARNINGS -Wall -Wextra -Wpedantic)
endif()

target_compile_options(myapp PRIVATE ${WARNINGS})
```

## Variable Naming Conventions

:::success Best Practices

- `UPPERCASE_WITH_UNDERSCORES` - Cache variables, important settings
- `MixedCase` or `lowercase_with_underscores` - Local variables
- `_` prefix - Private/internal variables
- Project prefix - `MYPROJECT_OPTION_NAME`
  :::

```cmake
# Good
set(MYPROJECT_BUILD_TESTS ON CACHE BOOL "Build tests")
set(source_files main.cpp utils.cpp)

# Avoid
set(BuildTests ON)  # Unclear scope
set(x main.cpp)     # Unclear purpose
```

## Common Pitfalls

### Unquoted Variables

```cmake
set(MY_VAR "value with spaces")

# ❌ Wrong - split into multiple arguments
message(STATUS ${MY_VAR})

# ✅ Correct
message(STATUS "${MY_VAR}")
```

### Variable Expansion in Lists

```cmake
set(LIST_A a b c)
set(LIST_B ${LIST_A} d e)

message(STATUS "${LIST_B}")  # a;b;c;d;e
```

### Conditional Comparisons

```cmake
set(MY_VAR "ON")

# All these are equivalent:
if(MY_VAR)
if(${MY_VAR})
if("${MY_VAR}")

# String comparison:
if(MY_VAR STREQUAL "ON")
if("${MY_VAR}" STREQUAL "ON")
```

## Quick Reference

```cmake
# Set
set(VAR "value")
set(VAR "value" CACHE TYPE "description")
set(VAR "value" PARENT_SCOPE)

# Unset
unset(VAR)

# Lists
list(APPEND VAR item1 item2)
list(LENGTH VAR len)
list(GET VAR index result)

# Strings  
string(TOUPPER "${VAR}" upper)
string(REPLACE "old" "new" result "${VAR}")

# Check if defined
if(DEFINED VAR)
if(DEFINED CACHE{VAR})
if(DEFINED ENV{VAR})
```
