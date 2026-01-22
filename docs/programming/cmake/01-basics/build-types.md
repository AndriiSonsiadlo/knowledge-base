---
id: build-types
title: Build Types
sidebar_label: Build Types
sidebar_position: 4
tags: [ c++, cmake ]
---

# Build Types

## What are Build Types?

Build types define how your code is compiled - with optimization, debug symbols, or minimal size. CMake provides four standard configurations.

## Standard Build Types

### Debug

Optimized for **debugging**.

```cmake showLineNumbers 
set(CMAKE_BUILD_TYPE Debug)
```

**Characteristics:**

- ❌ No optimization (`-O0`)
- ✅ Debug symbols (`-g`)
- ✅ Assertions enabled
- 📦 Large binaries
- 🐌 Slow runtime

**Command line:**

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

**Use when:**

- Developing and debugging
- Using debuggers (GDB, LLDB, Visual Studio)
- Need stack traces and variable inspection

### Release

Optimized for **performance**.

```cmake showLineNumbers 
set(CMAKE_BUILD_TYPE Release)
```

**Characteristics:**

- ✅ Full optimization (`-O3` or `/O2`)
- ❌ No debug symbols
- ❌ Assertions disabled (`-DNDEBUG`)
- 📦 Smaller binaries
- 🚀 Fast runtime

**Command line:**

```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
```

**Use when:**

- Production builds
- Performance testing
- Shipping to users

### RelWithDebInfo

**Release with Debug Info** - best of both worlds.

```cmake showLineNumbers 
set(CMAKE_BUILD_TYPE RelWithDebInfo)
```

**Characteristics:**

- ✅ Optimization (`-O2`)
- ✅ Debug symbols (`-g`)
- ❌ Assertions disabled
- 📦 Larger than Release
- 🚀 Fast runtime

**Command line:**

```bash
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
```

**Use when:**

- Profiling optimized code
- Debugging performance issues
- Need stack traces in production

:::success Recommended for Profiling
This is the ideal configuration for performance profiling tools!
:::

### MinSizeRel

Optimized for **minimal binary size**.

```cmake showLineNumbers 
set(CMAKE_BUILD_TYPE MinSizeRel)
```

**Characteristics:**

- ⚠️ Size optimization (`-Os`)
- ❌ No debug symbols
- ❌ Assertions disabled
- 📦 Smallest binaries
- ⚡ Moderate runtime speed

**Command line:**

```bash
cmake -DCMAKE_BUILD_TYPE=MinSizeRel ..
```

**Use when:**

- Embedded systems
- Limited storage
- Download size matters

## Comparison Table

| Build Type | Optimization | Debug Symbols | Assertions | Use Case |
|------------|-------------|---------------|------------|----------|
| **Debug** | None | ✅ | ✅ | Development |
| **Release** | Maximum | ❌ | ❌ | Production |
| **RelWithDebInfo** | High | ✅ | ❌ | Profiling |
| **MinSizeRel** | Size | ❌ | ❌ | Embedded |

## Compiler Flags by Build Type

### GCC/Clang

```cmake showLineNumbers 
# Debug
CMAKE_CXX_FLAGS_DEBUG = "-g"

# Release
CMAKE_CXX_FLAGS_RELEASE = "-O3 -DNDEBUG"

# RelWithDebInfo
CMAKE_CXX_FLAGS_RELWITHDEBINFO = "-O2 -g -DNDEBUG"

# MinSizeRel
CMAKE_CXX_FLAGS_MINSIZEREL = "-Os -DNDEBUG"
```

### MSVC (Visual Studio)

```cmake showLineNumbers 
# Debug
CMAKE_CXX_FLAGS_DEBUG = "/MDd /Zi /Ob0 /Od /RTC1"

# Release
CMAKE_CXX_FLAGS_RELEASE = "/MD /O2 /Ob2 /DNDEBUG"

# RelWithDebInfo
CMAKE_CXX_FLAGS_RELWITHDEBINFO = "/MD /Zi /O2 /Ob1 /DNDEBUG"

# MinSizeRel
CMAKE_CXX_FLAGS_MINSIZEREL = "/MD /O1 /Ob1 /DNDEBUG"
```

## Setting Build Type

### In CMakeLists.txt

```cmake showLineNumbers 
# Set default if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
```

### Command Line

```bash
# Configure with specific type
cmake -DCMAKE_BUILD_TYPE=Debug -S . -B build

# Or multi-config generators (Visual Studio, Xcode)
cmake -S . -B build
cmake --build build --config Release
```

### GUI Tools

```bash
# ccmake (terminal GUI)
ccmake -B build

# cmake-gui (graphical)
cmake-gui -B build
```

## Multi-Configuration Generators

Some generators support **multiple configurations** in one build tree:

- Visual Studio
- Xcode
- Ninja Multi-Config

```bash
# Generate
cmake -G "Visual Studio 17 2022" -S . -B build

# Build different types
cmake --build build --config Debug
cmake --build build --config Release

# No need to set CMAKE_BUILD_TYPE!
```

## Custom Build Types

You can create your own build types:

```cmake showLineNumbers 
# Create Profiling build type
set(CMAKE_CXX_FLAGS_PROFILING "-O2 -g -pg" 
    CACHE STRING "Flags for profiling build")
set(CMAKE_C_FLAGS_PROFILING "-O2 -g -pg" 
    CACHE STRING "Flags for profiling build")

# Mark as advanced
mark_as_advanced(
    CMAKE_CXX_FLAGS_PROFILING
    CMAKE_C_FLAGS_PROFILING
)

# Use it
# cmake -DCMAKE_BUILD_TYPE=Profiling ..
```

:::warning Consistency
Ensure all compiler/linker flags are set for your custom type!
:::

## Per-Configuration Properties

Set different values per build type:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

# Different output names
set_target_properties(myapp PROPERTIES
    OUTPUT_NAME_DEBUG "myapp_debug"
    OUTPUT_NAME_RELEASE "myapp"
)

# Different output directories
set_target_properties(myapp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/debug/bin"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/release/bin"
)
```

## Conditional Compilation by Build Type

### Using Generator Expressions

```cmake showLineNumbers 
add_executable(myapp main.cpp)

target_compile_definitions(myapp PRIVATE
    $<$<CONFIG:Debug>:DEBUG_BUILD>
    $<$<CONFIG:Release>:RELEASE_BUILD>
)

target_compile_options(myapp PRIVATE
    $<$<CONFIG:Debug>:-Wall -Wextra>
    $<$<CONFIG:Release>:-O3>
)
```

### Using CMAKE_BUILD_TYPE

```cmake showLineNumbers 
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(myapp PRIVATE VERBOSE_LOGGING)
    target_link_libraries(myapp PRIVATE debug_helper)
endif()

if(CMAKE_BUILD_TYPE MATCHES "Release|RelWithDebInfo")
    target_compile_definitions(myapp PRIVATE OPTIMIZED)
endif()
```

## Practical Examples

### Development Configuration

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.15)
project(MyApp)

# Default to Debug for development
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug)
endif()

add_executable(myapp main.cpp)

# Add sanitizers in Debug
if(CMAKE_BUILD_TYPE STREQUAL "Debug" AND NOT MSVC)
    target_compile_options(myapp PRIVATE 
        -fsanitize=address
        -fsanitize=undefined
    )
    target_link_options(myapp PRIVATE
        -fsanitize=address
        -fsanitize=undefined
    )
endif()
```

### Production Configuration

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.15)
project(MyApp)

# Default to Release for production
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

add_executable(myapp main.cpp)

# Link-Time Optimization in Release
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    include(CheckIPOSupported)
    check_ipo_supported(RESULT ipo_supported)
    
    if(ipo_supported)
        set_target_properties(myapp PROPERTIES
            INTERPROCEDURAL_OPTIMIZATION TRUE
        )
    endif()
endif()
```

### Logging by Build Type

```cpp title="main.cpp"
#include <iostream>

int main() {
#ifdef DEBUG_BUILD
    std::cout << "Running in DEBUG mode" << std::endl;
    std::cout << "Verbose logging enabled" << std::endl;
#elif defined(RELEASE_BUILD)
    std::cout << "Running in RELEASE mode" << std::endl;
#endif

#ifndef NDEBUG
    std::cout << "Assertions are enabled" << std::endl;
#else
    std::cout << "Assertions are disabled" << std::endl;
#endif

    return 0;
}
```

## Build Type Best Practices

:::success Recommendations

1. **Development**: Use `Debug`
    - Full debugging capability
    - Fast compile times
    - Easier to track issues

2. **Testing**: Use `RelWithDebInfo`
    - Performance close to release
    - Can still debug crashes
    - Stack traces available

3. **Production**: Use `Release`
    - Maximum performance
    - Smallest binaries (except MinSizeRel)
    - No debug overhead

4. **Embedded**: Use `MinSizeRel`
    - Smallest possible binary
    - Ideal for flash constraints

5. **Always set a default**:

   ```cmake showLineNumbers 
   if(NOT CMAKE_BUILD_TYPE)
       set(CMAKE_BUILD_TYPE Release)
   endif()
   ```

6. **Document your choice**:

   ```cmake showLineNumbers 
   message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
   ```

:::

## Checking Current Build Type

```cmake showLineNumbers 
message(STATUS "Current build type: ${CMAKE_BUILD_TYPE}")

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Debug build - optimizations disabled")
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
    message(STATUS "Release build - full optimizations")
endif()

# Check if debug
if(CMAKE_BUILD_TYPE MATCHES "Debug")
    # Debug-specific code
endif()

# Check if optimized
if(CMAKE_BUILD_TYPE MATCHES "Release|RelWithDebInfo|MinSizeRel")
    # Optimization-specific code
endif()
```

## Common Issues

:::warning Pitfalls

**Issue**: Build type ignored

```bash
cmake ..  # No -DCMAKE_BUILD_TYPE specified
```

**Solution**: Always specify or set default in CMakeLists.txt

**Issue**: Wrong type for multi-config generators

```cmake showLineNumbers 
set(CMAKE_BUILD_TYPE Release)  # Ignored by Visual Studio!
```

**Solution**: Use `cmake --build build --config Release`

**Issue**: Case sensitivity

```bash
cmake -DCMAKE_BUILD_TYPE=debug ..  # Won't work!
```

**Solution**: Use exact case: `Debug`, `Release`, etc.
:::
