---
id: linking
title: Linking Libraries
sidebar_label: Linking
sidebar_position: 4
tags: [c++, cmake, linking, dependencies]
---

# Linking Libraries

## Understanding Library Linking

Linking is the process of combining compiled object files and libraries into a final executable or library. In CMake, linking determines which libraries your target depends on and how those dependencies are propagated through your build system.

The distinction between compile-time requirements (headers, definitions) and link-time requirements (actual library binaries) is crucial for proper dependency management. CMake's modern approach uses target-based linking, which automatically handles both aspects through the `target_link_libraries()` command.

## The target_link_libraries() Command

This is the primary command for establishing dependencies between targets. It does more than just linking - it also propagates include directories, compile definitions, and compiler flags based on the visibility specifiers you choose.

### Basic Syntax

```cmake showLineNumbers 
target_link_libraries(target
    <PRIVATE|PUBLIC|INTERFACE> library1 library2 ...
)
```

The target must already exist (created with `add_executable()` or `add_library()`). Libraries can be CMake targets or system libraries.

### Simple Example

```cmake showLineNumbers 
# Create a library
add_library(math_operations STATIC
    src/add.cpp
    src/multiply.cpp
)

# Create an executable
add_executable(calculator main.cpp)

# Link the library to the executable
target_link_libraries(calculator PRIVATE math_operations)
```

In this example, `calculator` needs `math_operations` to build and run, but since it's an executable, nothing else will depend on it, so we use `PRIVATE`.

## Visibility Keywords: The Heart of Modern CMake

The visibility keywords (`PRIVATE`, `PUBLIC`, `INTERFACE`) control how dependencies and their properties propagate through your build system. Understanding these is essential for maintainable CMake projects.

### PRIVATE

Use `PRIVATE` when a library is an implementation detail that consumers don't need to know about. The dependency is used internally but doesn't appear in your public API.

```cmake showLineNumbers 
add_library(database STATIC
    src/database.cpp
    src/connection.cpp
)

# SQLite is used internally but not exposed in headers
find_package(SQLite3 REQUIRED)
target_link_libraries(database PRIVATE SQLite3::SQLite3)
```

**When to use PRIVATE:**

- The library is used only in `.cpp` files, not headers
- You want to hide implementation details
- The dependency won't be needed by code that uses your library
- You're linking to an executable (executables are always endpoints)

**What gets propagated:** Nothing to dependents. Only the current target gets the library, includes, and compile options.

### PUBLIC

Use `PUBLIC` when a library appears in your public interface - when users of your library also need to know about and link to this dependency.

```cmake showLineNumbers 
add_library(graphics_engine STATIC
    src/renderer.cpp
    src/shader.cpp
)

# OpenGL is used and exposed in our public headers
find_package(OpenGL REQUIRED)
target_link_libraries(graphics_engine PUBLIC OpenGL::GL)
```

**When to use PUBLIC:**

- The dependency appears in your public header files
- Users of your library need to link to the same dependency
- You're creating a wrapper or facade around another library
- Your API directly exposes types from the dependency

**What gets propagated:** Everything - include directories, compile definitions, compile options, and the link dependency itself.

### INTERFACE

Use `INTERFACE` when a library is needed by consumers but not by the library itself. This is primarily used for header-only libraries or when you're propagating requirements without using them yourself.

```cmake showLineNumbers 
# Header-only library
add_library(math_utilities INTERFACE)

# Only consumers need the include directory
target_include_directories(math_utilities INTERFACE
    include/
)

# Only consumers need C++17
target_compile_features(math_utilities INTERFACE
    cxx_std_17
)
```

**When to use INTERFACE:**

- You're creating a header-only library
- You need to pass requirements to consumers without using them
- You're creating an "umbrella" target that just groups dependencies

**What gets propagated:** Everything to dependents, but the library itself doesn't use these dependencies.

## Transitive Dependencies

One of CMake's most powerful features is automatic handling of transitive dependencies. When you link with `PUBLIC`, the dependencies automatically propagate down the dependency chain.

### How Transitivity Works

```cmake showLineNumbers 
# Low-level library
add_library(logging STATIC logging.cpp)
target_include_directories(logging PUBLIC include/logging)

# Mid-level library uses and exposes logging
add_library(database STATIC database.cpp)
target_link_libraries(database PUBLIC logging)
target_include_directories(database PUBLIC include/database)

# High-level library uses database
add_library(application_logic STATIC app.cpp)
target_link_libraries(application_logic PUBLIC database)

# Executable uses application_logic
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE application_logic)
```

**What myapp automatically gets:**

- Direct link to `application_logic`
- Transitive link to `database` (via `application_logic`)
- Transitive link to `logging` (via `database`)
- Include directories from all three libraries
- Any compile definitions from all three libraries

This happens automatically because of the `PUBLIC` links. No manual tracking needed.

### Breaking the Chain

You can break transitive propagation using `PRIVATE`:

```cmake showLineNumbers 
add_library(A STATIC a.cpp)
add_library(B STATIC b.cpp)
add_library(C STATIC c.cpp)

# B uses A but doesn't expose it
target_link_libraries(B PRIVATE A)

# C uses B
target_link_libraries(C PUBLIC B)

# An executable using C
add_executable(app main.cpp)
target_link_libraries(app PRIVATE C)
```

**What app gets:**

- C (direct)
- B (transitive via C)
- NOT A (B's PRIVATE dependency)

## Linking Static Libraries

Static libraries (`.a` on Unix, `.lib` on Windows) are archives of compiled object files that get incorporated directly into the final binary at link time.

### Characteristics

When you link a static library, the linker extracts only the object files you actually use and copies them into your executable. This creates a self-contained binary with no runtime dependencies on those libraries.

```cmake showLineNumbers 
add_library(mylib STATIC
    src/core.cpp
    src/utils.cpp
    src/helpers.cpp
)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE mylib)
```

**Advantages:**

- No runtime dependencies - easier distribution
- Potential for better optimization (linker can see more code)
- Slightly faster startup (no dynamic linking overhead)

**Disadvantages:**

- Larger executable size
- Memory duplication if multiple processes use the same code
- Must relink executables to update the library
- Code bloat if multiple executables link the same static library

### Position Independent Code

When a static library will be linked into a shared library, it must be compiled with position-independent code (PIC):

```cmake showLineNumbers 
add_library(my_static_lib STATIC lib.cpp)

# Required if this static lib will be linked into a shared lib
set_target_properties(my_static_lib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

# Now we can use it in a shared library
add_library(my_shared_lib SHARED shared.cpp)
target_link_libraries(my_shared_lib PRIVATE my_static_lib)
```

This is necessary because shared libraries must be loadable at any memory address, which requires PIC.

## Linking Shared Libraries

Shared libraries (`.so` on Unix, `.dll` on Windows, `.dylib` on macOS) are loaded at runtime, allowing multiple processes to share the same library code in memory.

### Runtime Dependencies

Unlike static libraries, shared libraries remain separate files that must be present at runtime:

```cmake showLineNumbers 
add_library(mylib SHARED
    src/api.cpp
    src/implementation.cpp
)

# Set version information
set_target_properties(mylib PROPERTIES
    VERSION 2.1.4
    SOVERSION 2
)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE mylib)
```

On Linux, this creates:

- `libmylib.so.2.1.4` - the actual library file
- `libmylib.so.2` - symlink (API compatibility version)
- `libmylib.so` - symlink (for linking at build time)

**Runtime behavior:**
When you run `app`, the system's dynamic linker searches for `libmylib.so.2` in standard locations (`/usr/lib`, `/usr/local/lib`, or paths in `LD_LIBRARY_PATH`).

### RPATH Configuration

RPATH (Run-time search path) tells the executable where to find shared libraries. By default, CMake sets up reasonable RPATH behavior:

```cmake showLineNumbers 
# CMake's default RPATH settings (usually don't need to change)
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
```

For custom library locations:

```cmake showLineNumbers 
add_executable(app main.cpp)
target_link_libraries(app PRIVATE mylib)

# Add custom RPATH
set_target_properties(app PROPERTIES
    INSTALL_RPATH "/opt/myapp/lib:$ORIGIN/../lib"
)
```

The `$ORIGIN` variable expands to the executable's directory, allowing relative paths.

## Linking System Libraries

System libraries are external libraries installed on the system, typically found through `find_package()` or `find_library()`.

### Using find_package()

The modern approach uses imported targets, which encapsulate all necessary information:

```cmake showLineNumbers 
# Find the package
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)
find_package(OpenSSL REQUIRED)

add_executable(myapp main.cpp)

# Link using imported targets (preferred)
target_link_libraries(myapp PRIVATE
    Threads::Threads    # Thread library (pthread on Unix)
    ZLIB::ZLIB         # Compression library
    OpenSSL::SSL       # SSL library
    OpenSSL::Crypto    # Crypto library
)
```

**Why imported targets are better:**

- Automatically include the necessary include directories
- Handle compile definitions
- Work correctly for both Debug and Release builds
- Provide better error messages
- More portable across platforms

### Legacy Variable-Based Linking

Older CMake code uses variables. While this still works, it's less maintainable:

```cmake showLineNumbers 
find_package(ZLIB REQUIRED)

add_executable(myapp main.cpp)

# Old style (avoid if possible)
target_include_directories(myapp PRIVATE ${ZLIB_INCLUDE_DIRS})
target_link_libraries(myapp PRIVATE ${ZLIB_LIBRARIES})

# Modern style (preferred)
target_link_libraries(myapp PRIVATE ZLIB::ZLIB)
```

### Platform-Specific System Libraries

Different platforms have different system libraries. Handle them conditionally:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

if(WIN32)
    # Windows-specific libraries
    target_link_libraries(myapp PRIVATE
        ws2_32      # Winsock
        user32      # Windows API
        gdi32       # Graphics
    )
elseif(APPLE)
    # macOS frameworks
    find_library(COCOA_LIBRARY Cocoa REQUIRED)
    find_library(OPENGL_LIBRARY OpenGL REQUIRED)
    target_link_libraries(myapp PRIVATE
        ${COCOA_LIBRARY}
        ${OPENGL_LIBRARY}
    )
elseif(UNIX)
    # Linux libraries
    find_package(Threads REQUIRED)
    target_link_libraries(myapp PRIVATE
        Threads::Threads
        dl          # Dynamic loading
        m           # Math library
    )
endif()
```

## Linking Order and Circular Dependencies

The order in which you link libraries can matter, especially with static libraries on Unix-like systems. The linker processes libraries left to right, resolving symbols as it goes.

### Link Order Matters for Static Libraries

```cmake showLineNumbers 
# If libB depends on symbols in libA
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    libB    # Should come first
    libA    # Should come second
)
```

With modern CMake and target-based linking, CMake usually handles this correctly based on `target_link_libraries()` relationships. However, sometimes you need to explicitly control order.

### Handling Circular Dependencies

Sometimes two static libraries depend on each other (though this is a design smell):

```cmake showLineNumbers 
# If libA and libB have circular dependencies
target_link_libraries(myapp PRIVATE
    libA
    libB
    libA    # Link libA again
)
```

Better solution: redesign to eliminate the circular dependency or combine into one library.

### Using Link Groups

For stubborn circular dependencies with static libraries:

```cmake showLineNumbers 
target_link_libraries(myapp PRIVATE
    -Wl,--start-group
    libA
    libB
    -Wl,--end-group
)
```

This tells the linker to resolve symbols within the group iteratively. Note this is GNU ld specific.

## Advanced Linking Techniques

### Whole Archive Linking

Sometimes you need to force the linker to include all symbols from a static library, not just those referenced:

```cmake showLineNumbers 
if(MSVC)
    target_link_libraries(myapp PRIVATE
        -WHOLEARCHIVE:mylib
    )
else()
    target_link_libraries(myapp PRIVATE
        -Wl,--whole-archive mylib -Wl,--no-whole-archive
    )
endif()
```

This is useful for libraries with static initializers or plugin systems where symbols register themselves.

### Link Options

Add linker-specific flags:

```cmake showLineNumbers 
target_link_options(myapp PRIVATE
    -Wl,--as-needed        # Only link libraries actually used
    -Wl,--no-undefined     # Error on undefined symbols
)

# Platform-specific
if(APPLE)
    target_link_options(myapp PRIVATE
        -Wl,-dead_strip    # Remove unused code
    )
endif()
```

### Interface Libraries for Convenience

Group common dependencies into interface libraries:

```cmake showLineNumbers 
# Create a convenience interface library
add_library(common_deps INTERFACE)

target_link_libraries(common_deps INTERFACE
    Threads::Threads
    ZLIB::ZLIB
    fmt::fmt
)

# Now multiple targets can easily use common dependencies
add_executable(app1 app1.cpp)
target_link_libraries(app1 PRIVATE common_deps)

add_executable(app2 app2.cpp)
target_link_libraries(app2 PRIVATE common_deps)
```

## Complete Real-World Example

Here's a comprehensive example showing different linking scenarios:

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.15)
project(ComplexProject VERSION 1.0.0)

# Find system dependencies
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)
find_package(OpenSSL REQUIRED)

# Low-level utility library (header-only)
add_library(utilities INTERFACE)
target_include_directories(utilities INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include/utilities
)
target_compile_features(utilities INTERFACE cxx_std_17)

# Core library (static, uses utilities, ZLIB internally)
add_library(core STATIC
    src/core/engine.cpp
    src/core/config.cpp
)

target_include_directories(core
    PRIVATE src/core
    PUBLIC include/core
)

target_link_libraries(core
    PUBLIC utilities              # Exposed in headers
    PRIVATE ZLIB::ZLIB           # Used internally only
    PRIVATE Threads::Threads     # Used internally only
)

# Network library (static, uses core and OpenSSL, exposes both)
add_library(network STATIC
    src/network/client.cpp
    src/network/server.cpp
)

target_include_directories(network
    PRIVATE src/network
    PUBLIC include/network
)

target_link_libraries(network
    PUBLIC core                   # Types in our headers
    PUBLIC OpenSSL::SSL          # Types in our headers
    PRIVATE OpenSSL::Crypto      # Used internally
)

# Application (uses network, gets everything transitively)
add_executable(myapp
    src/main.cpp
    src/application.cpp
)

target_link_libraries(myapp PRIVATE network)
# myapp automatically gets: network, core, utilities, OpenSSL::SSL
# myapp does NOT get: ZLIB, Threads, OpenSSL::Crypto (all PRIVATE)

# Installation
install(TARGETS myapp core network utilities
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    INCLUDES DESTINATION include
)
```

## Best Practices

:::success Link Visibility Guidelines

**Use PRIVATE when:**

- Linking to an executable (always)
- The dependency is used only in `.cpp` files
- You want to hide implementation details

**Use PUBLIC when:**

- The dependency appears in your public headers
- Users of your library need the same dependency
- You're creating a wrapper library

**Use INTERFACE when:**

- Creating header-only libraries
- Creating umbrella/convenience targets
- Propagating requirements without using them
  :::

:::success General Best Practices

1. **Always use visibility keywords** - never omit PRIVATE/PUBLIC/INTERFACE
2. **Prefer imported targets** over variable-based linking
3. **Link to the minimum required** - don't over-link
4. **Keep implementation private** - minimize PUBLIC dependencies
5. **Use interface libraries** to group common dependencies
6. **Set POSITION_INDEPENDENT_CODE** for static libs used in shared libs
7. **Let CMake handle link order** through target dependencies
   :::

## Common Issues and Solutions

### Undefined Reference Errors

When you see "undefined reference to..." errors:

```cmake showLineNumbers 
# Check that you've linked all required libraries
target_link_libraries(myapp PRIVATE
    all_required_libs
)

# For static libraries, check link order
# Dependent libraries should come before dependencies
```

### Multiple Definition Errors

When the same symbol is defined multiple times:

```cmake showLineNumbers 
# Ensure libraries aren't linked multiple times
# Use PRIVATE where possible
# Check for duplicate object files in link command
```

### Missing Shared Libraries at Runtime

When executable can't find `.so`/`.dll` files:

```bash
# Linux: Check LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/path/to/libs:$LD_LIBRARY_PATH

# Or set RPATH in CMake
set_target_properties(myapp PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
)
```

### Circular Dependencies

When libraries depend on each other:

```cmake showLineNumbers 
# Best: Redesign to remove circular dependency
# Workaround: Use link groups or link twice
target_link_libraries(myapp PRIVATE A B A)
```

## Quick Reference

```cmake showLineNumbers 
# Basic linking
target_link_libraries(target PRIVATE library)

# Multiple libraries with visibility
target_link_libraries(target
    PRIVATE private_libs
    PUBLIC public_libs
    INTERFACE interface_libs
)

# System libraries (modern)
find_package(PackageName REQUIRED)
target_link_libraries(target PRIVATE PackageName::Component)

# System libraries (legacy)
target_link_libraries(target PRIVATE ${LIBRARY_VARIABLE})

# Link options
target_link_options(target PRIVATE -Wl,--flag)

# RPATH
set_target_properties(target PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
)
```
