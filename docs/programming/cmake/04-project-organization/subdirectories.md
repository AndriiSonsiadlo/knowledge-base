---
id: subdirectories
title: Working with Subdirectories
sidebar_label: Subdirectories
sidebar_position: 2
tags: [cmake, subdirectories, add_subdirectory, scope]
---

# Working with Subdirectories

## The add_subdirectory() Command

`add_subdirectory()` tells CMake to process another directory containing its own `CMakeLists.txt`. This is fundamental for organizing multi-component projects.

```cmake
add_subdirectory(source_dir [binary_dir] [EXCLUDE_FROM_ALL])
```

**Parameters:**

- `source_dir`: Path to directory with CMakeLists.txt
- `binary_dir`: (Optional) Where to put build files
- `EXCLUDE_FROM_ALL`: Don't build by default

## How It Works

When CMake encounters `add_subdirectory()`:

1. Enters the specified directory
2. Processes that directory's `CMakeLists.txt`
3. Creates a new scope (variables can be isolated)
4. Returns to the parent when done

```cmake title="Root CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(MyProject)

message(STATUS "Processing root")

add_subdirectory(libs)      # Process libs/CMakeLists.txt
add_subdirectory(app)       # Then process app/CMakeLists.txt

message(STATUS "Back in root")
```

```cmake title="libs/CMakeLists.txt"
message(STATUS "Processing libs")

add_library(mylib mylib.cpp)
```

**Output:**

```
-- Processing root
-- Processing libs
-- Back in root
```

## Variable Scope

Subdirectories create new variable scopes, but it's not complete isolation:

### Variables Are Inherited

Child directories see parent variables:

```cmake title="Root"
set(MY_VAR "from parent")
add_subdirectory(child)
```

```cmake title="child/CMakeLists.txt"
message(STATUS "MY_VAR = ${MY_VAR}")  # Output: "from parent"
```

### Changes Don't Propagate Upward

By default, changes in child don't affect parent:

```cmake title="child/CMakeLists.txt"
set(CHILD_VAR "value")
```

```cmake title="Root (after add_subdirectory)"
message(STATUS "${CHILD_VAR}")  # Empty! Not set in parent scope
```

### Explicit Parent Scope

Use `PARENT_SCOPE` to modify parent variables:

```cmake title="child/CMakeLists.txt"
set(RESULT "computed value" PARENT_SCOPE)
```

```cmake title="Root"
add_subdirectory(child)
message(STATUS "${RESULT}")  # Output: "computed value"
```

**Important:** Setting `PARENT_SCOPE` doesn't set the variable in the current scope:

```cmake
set(VAR "value" PARENT_SCOPE)
message(STATUS "${VAR}")  # Empty in current scope!

# To set both:
set(VAR "value" PARENT_SCOPE)
set(VAR "value")
```

## Targets Are Global

Unlike variables, targets (executables, libraries) are globally visible after creation:

```cmake title="libs/CMakeLists.txt"
add_library(mylib mylib.cpp)
```

```cmake title="app/CMakeLists.txt"
add_executable(myapp main.cpp)

# Can link to library from sibling directory
target_link_libraries(myapp PRIVATE mylib)
```

This works because targets exist in a global namespace. However, best practice is to use ALIAS targets for clarity:

```cmake title="libs/CMakeLists.txt"
add_library(mylib mylib.cpp)
add_library(MyProject::mylib ALIAS mylib)  # Namespaced
```

```cmake title="app/CMakeLists.txt"
target_link_libraries(myapp PRIVATE MyProject::mylib)
```

## Directory Properties

Beyond variables and targets, directories have properties you can set:

```cmake
# Set property for current directory
set_property(DIRECTORY PROPERTY COMPILE_OPTIONS -Wall)

# Set for specific directory
set_property(DIRECTORY libs PROPERTY COMPILE_DEFINITIONS DEBUG_MODE)

# Get directory property
get_property(options DIRECTORY PROPERTY COMPILE_OPTIONS)
```

Common directory properties:

- `COMPILE_OPTIONS`: Compiler flags for all targets in directory
- `COMPILE_DEFINITIONS`: Preprocessor definitions
- `INCLUDE_DIRECTORIES`: Include paths
- `LINK_DIRECTORIES`: Library search paths (avoid, use target commands)

## Binary Directory Structure

CMake mirrors source directory structure in build directory:

```
Source tree:              Build tree:
project/                  build/
├── CMakeLists.txt        ├── CMakeFiles/
├── libs/                 ├── libs/
│   └── CMakeLists.txt    │   └── CMakeFiles/
└── app/                  └── app/
    └── CMakeLists.txt        └── CMakeFiles/
```

Each subdirectory gets its own build directory. Access them with:

- `CMAKE_CURRENT_SOURCE_DIR`: Source directory being processed
- `CMAKE_CURRENT_BINARY_DIR`: Corresponding build directory

```cmake
message(STATUS "Source: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "Binary: ${CMAKE_CURRENT_BINARY_DIR}")
```

### Custom Binary Directory

Override default build location:

```cmake
add_subdirectory(libs ${CMAKE_BINARY_DIR}/mylibs)
```

Now `libs/` builds to `build/mylibs/` instead of `build/libs/`. Rarely needed but useful for organizing complex builds.

## Include vs add_subdirectory

### add_subdirectory()

- Processes `CMakeLists.txt` in another directory
- Creates new scope
- Has its own binary directory
- Use for: components with their own build

```cmake
add_subdirectory(libs)
```

### include()

- Processes a `.cmake` file inline
- No new scope (unless you create one)
- No binary directory
- Use for: shared CMake code, utilities, macros

```cmake
include(cmake/CompilerWarnings.cmake)
```

**When to use each:**

- **add_subdirectory()**: Component has targets (library, executable)
- **include()**: Shared CMake functions, variables, or configuration

## EXCLUDE_FROM_ALL

Prevent subdirectory targets from building by default:

```cmake
add_subdirectory(optional_tools EXCLUDE_FROM_ALL)
```

```cmake title="optional_tools/CMakeLists.txt"
add_executable(tool1 tool1.cpp)
add_executable(tool2 tool2.cpp)
```

**Behavior:**

- `cmake --build build` → tools won't build
- `cmake --build build --target tool1` → only tool1 builds
- `cmake --build build --target all` → tools still excluded

**Use cases:**

- Optional utilities
- Documentation generators
- Development-only tools
- Large examples that slow down builds

## Ordering Matters

Subdirectories are processed in order listed:

```cmake
add_subdirectory(libs)  # Build libraries first
add_subdirectory(app)   # Then app that uses libraries
```

If `app` depends on targets from `libs`, they must be added in this order. Wrong order causes errors:

```cmake
add_subdirectory(app)   # ❌ Error: 'mylib' target not found
add_subdirectory(libs)  # Defines mylib too late
```

**Dependencies determine order:**

```cmake
# Correct order based on dependencies
add_subdirectory(external)     # Third-party libs (no deps)
add_subdirectory(libs/utils)   # Utils (no deps)
add_subdirectory(libs/core)    # Core (depends on utils)
add_subdirectory(libs/ui)      # UI (depends on core)
add_subdirectory(app)          # App (depends on ui)
add_subdirectory(tests)        # Tests (depend on everything)
```

## Relative Paths

`add_subdirectory()` accepts relative paths from current directory:

```cmake
# From root
add_subdirectory(libs/core)        # Relative to root
add_subdirectory(../shared)        # Parent directory (unusual)

# Absolute paths work but aren't portable
add_subdirectory(/usr/src/lib)     # Avoid
```

**Best practice:** Keep subdirectories within your project tree and use relative paths.

## Conditional Subdirectories

Add subdirectories based on conditions:

```cmake
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_EXAMPLES "Build examples" OFF)

if(BUILD_TESTS)
    add_subdirectory(tests)
endif()

if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# Platform-specific
if(WIN32)
    add_subdirectory(windows)
elseif(UNIX)
    add_subdirectory(unix)
endif()
```

## Communicating Between Subdirectories

### Via Global Targets

Most common - one subdirectory creates target, another uses it:

```cmake title="lib/CMakeLists.txt"
add_library(mylib mylib.cpp)
add_library(Project::mylib ALIAS mylib)
```

```cmake title="app/CMakeLists.txt"
add_executable(app main.cpp)
target_link_libraries(app PRIVATE Project::mylib)
```

### Via Cache Variables

Share configuration across subdirectories:

```cmake title="Root"
set(SHARED_OPTION ON CACHE BOOL "Shared option")
add_subdirectory(component1)
add_subdirectory(component2)
```

Both components see `SHARED_OPTION`.

### Via Parent Scope

Child can pass information to parent:

```cmake title="child/CMakeLists.txt"
set(STATUS_MESSAGE "Child completed successfully" PARENT_SCOPE)
```

```cmake title="Root"
add_subdirectory(child)
message(STATUS "${STATUS_MESSAGE}")
```

## Common Patterns

### Library Collection

Building multiple libraries:

```cmake title="Root"
add_subdirectory(libs)
```

```cmake title="libs/CMakeLists.txt"
add_subdirectory(core)
add_subdirectory(utils)
add_subdirectory(network)
```

Each library directory has its own `CMakeLists.txt` defining the library target.

### Optional Features

```cmake
option(ENABLE_NETWORKING "Enable network features" ON)

if(ENABLE_NETWORKING)
    add_subdirectory(network)
    set(HAS_NETWORKING TRUE CACHE INTERNAL "")
else()
    set(HAS_NETWORKING FALSE CACHE INTERNAL "")
endif()

# Later, other code can check:
if(HAS_NETWORKING)
    target_compile_definitions(app PRIVATE HAS_NETWORKING)
endif()
```

### Automatic Discovery

Find all subdirectories with CMakeLists.txt:

```cmake
file(GLOB children RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} */CMakeLists.txt)

foreach(child ${children})
    get_filename_component(dir ${child} DIRECTORY)
    message(STATUS "Adding subdirectory: ${dir}")
    add_subdirectory(${dir})
endforeach()
```

**Warning:** This makes build non-deterministic - order depends on filesystem. Prefer explicit lists.

## Practical Example

A complete multi-subdirectory project:

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(MultiComponent VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)

# Configuration
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)
option(BUILD_TESTS "Build tests" ON)

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# External dependencies
add_subdirectory(external)

# Project components (dependency order)
add_subdirectory(libs/math)
add_subdirectory(libs/core)
add_subdirectory(libs/graphics)

# Main application
add_subdirectory(app)

# Optional components
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

```cmake title="libs/core/CMakeLists.txt"
add_library(core
    src/engine.cpp
    src/system.cpp
)

add_library(MultiComponent::core ALIAS core)

target_include_directories(core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE
        src/
)

target_link_libraries(core
    PUBLIC MultiComponent::math
)

target_compile_features(core PUBLIC cxx_std_17)
```

```cmake title="app/CMakeLists.txt"
add_executable(myapp main.cpp)

target_link_libraries(myapp PRIVATE
    MultiComponent::core
    MultiComponent::graphics
)
```

## Debugging Subdirectories

### See What's Being Processed

```cmake
message(STATUS "Entering directory: ${CMAKE_CURRENT_SOURCE_DIR}")
```

### Check Variables

```cmake
# At end of subdirectory
get_cmake_property(_vars VARIABLES)
foreach(_var ${_vars})
    message(STATUS "${_var} = ${${_var}}")
endforeach()
```

### Verify Targets Exist

```cmake
if(NOT TARGET Project::mylib)
    message(FATAL_ERROR "Expected target Project::mylib not found")
endif()
```

## Best Practices

:::success Subdirectory Guidelines

1. **One component per subdirectory** - clear boundaries
2. **Use ALIAS targets** - namespace your targets
3. **Respect dependency order** - dependencies before dependents
4. **Limit PARENT_SCOPE** - prefer cache variables or global targets
5. **Don't rely on subdirectory order** - make dependencies explicit
6. **Use relative paths** - stay within project
7. **Document subdirectory purpose** - comment in root CMakeLists.txt
8. **Keep subdirectory CMakeLists.txt focused** - just that component
   :::

:::warning Common Pitfalls

❌ **Wrong order** causing "target not found" errors  
❌ **Assuming variables propagate** back to parent  
❌ **Overusing global commands** in root affecting all subdirs  
❌ **Circular dependencies** between subdirectories  
❌ **Modifying parent directory properties** from child
:::

## Quick Reference

```cmake
# Add subdirectory
add_subdirectory(path)
add_subdirectory(path binary_dir)
add_subdirectory(path EXCLUDE_FROM_ALL)

# Conditional subdirectory
if(BUILD_FEATURE)
    add_subdirectory(feature)
endif()

# Current directories
${CMAKE_CURRENT_SOURCE_DIR}  # Current source dir
${CMAKE_CURRENT_BINARY_DIR}  # Current build dir

# Parent scope
set(VAR "value" PARENT_SCOPE)

# Check target exists
if(TARGET mylib)
    # Target available
endif()

# Include vs add_subdirectory
include(file.cmake)          # For CMake code
add_subdirectory(component)  # For components with targets
```

Understanding `add_subdirectory()` is key to organizing scalable CMake projects. It provides structure while maintaining the flexibility to share targets and configuration across components.
