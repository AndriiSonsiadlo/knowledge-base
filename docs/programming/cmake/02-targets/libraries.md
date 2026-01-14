---
id: libraries
title: Library Targets
sidebar_label: Library Targets
sidebar_position: 2
tags: [ c++, cmake ]
---

# Library Targets

## Types of Libraries

CMake supports several library types, each with different use cases.

## Creating Libraries

### Basic Syntax

```cmake
add_library(library_name <type>
    source1.cpp
    source2.cpp
    ...
)
```

## Library Types

### STATIC Libraries

Compiled into the executable at link time (`.a` on Unix, `.lib` on Windows).

```cmake
add_library(mylib STATIC
    src/mylib.cpp
    include/mylib.h
)
```

**Pros:**

- ✅ No runtime dependencies
- ✅ Faster runtime (no dynamic linking overhead)
- ✅ Easier distribution

**Cons:**

- ❌ Larger executable size
- ❌ Code duplication if used by multiple executables
- ❌ Cannot update library without recompiling

```cmake
# Example
add_library(math_lib STATIC
    src/add.cpp
    src/multiply.cpp
)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE math_lib)

# math_lib code is compiled into app executable
```

### SHARED Libraries

Dynamically loaded at runtime (`.so` on Unix, `.dll` on Windows, `.dylib` on macOS).

```cmake
add_library(mylib SHARED
    src/mylib.cpp
    include/mylib.h
)
```

**Pros:**

- ✅ Smaller executables
- ✅ Code shared between executables
- ✅ Can update library without recompiling app

**Cons:**

- ❌ Runtime dependencies (must distribute `.so`/`.dll`)
- ❌ Slightly slower (dynamic linking)
- ❌ Version compatibility issues

```cmake
# Example
add_library(graphics_lib SHARED
    src/renderer.cpp
    src/texture.cpp
)

add_executable(game main.cpp)
target_link_libraries(game PRIVATE graphics_lib)

# graphics_lib is separate file loaded at runtime
```

:::info Symbol Visibility
For shared libraries, consider using `CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS` or explicit export macros.
:::

### MODULE Libraries

Plugins loaded at runtime via `dlopen()` (Unix) or `LoadLibrary()` (Windows).

```cmake
add_library(myplugin MODULE
    src/plugin.cpp
)
```

**Use cases:**

- Plugin systems
- Dynamically loaded extensions
- Optional functionality

```cmake
# Plugin example
add_library(audio_plugin MODULE
    plugins/audio/mp3_decoder.cpp
)

# Don't link directly - load at runtime
# target_link_libraries(app PRIVATE audio_plugin)  # Wrong!

# Instead, app loads it dynamically:
# void* handle = dlopen("libaudio_plugin.so", RTLD_LAZY);
```

:::warning MODULE vs SHARED
`MODULE` libraries are NOT linked, only loaded at runtime with `dlopen`/`LoadLibrary`.
:::

### OBJECT Libraries

Compile sources into object files without creating an archive.

```cmake
add_library(common OBJECT
    src/common.cpp
    src/utils.cpp
)

add_executable(app1 app1.cpp $<TARGET_OBJECTS:common>)
add_executable(app2 app2.cpp $<TARGET_OBJECTS:common>)
```

**Use cases:**

- Compile once, link many times
- Avoid creating unnecessary archives
- Share compiled objects

```cmake
# More modern approach (CMake 3.12+)
add_library(common OBJECT
    common.cpp
    utils.cpp
)

target_include_directories(common PUBLIC include/)

add_executable(app1 app1.cpp)
target_link_libraries(app1 PRIVATE common)

add_executable(app2 app2.cpp)
target_link_libraries(app2 PRIVATE common)
```

### INTERFACE Libraries

Header-only libraries with no compiled sources.

```cmake
add_library(myheaderlib INTERFACE)

target_include_directories(myheaderlib INTERFACE
    include/
)

target_compile_definitions(myheaderlib INTERFACE
    USE_HEADER_LIBRARY
)
```

**Use cases:**

- Header-only libraries (like Eigen, GLM)
- Propagating settings to dependents
- Interface requirements

```cmake
# Header-only math library
add_library(math_header INTERFACE)

target_include_directories(math_header INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(math_header INTERFACE
    cxx_std_17
)

# Usage
add_executable(app main.cpp)
target_link_libraries(app PRIVATE math_header)
# Gets include directories and C++17 requirement
```

## Default Library Type

```cmake
# User can choose via BUILD_SHARED_LIBS
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

# Creates STATIC if OFF, SHARED if ON
add_library(mylib
    src/mylib.cpp
)
```

User controls:

```bash
cmake -DBUILD_SHARED_LIBS=ON ..  # Build shared
cmake -DBUILD_SHARED_LIBS=OFF .. # Build static
```

## Library Properties

### Output Name

```cmake
add_library(mylib STATIC mylib.cpp)

set_target_properties(mylib PROPERTIES
    OUTPUT_NAME "myproject_lib"
)

# Creates libmyproject_lib.a instead of libmylib.a
```

### Version Information (Shared Libraries)

```cmake
add_library(mylib SHARED mylib.cpp)

set_target_properties(mylib PROPERTIES
    VERSION 1.2.3           # lib version
    SOVERSION 1             # API version
)

# Creates:
# libmylib.so.1.2.3  (actual file)
# libmylib.so.1      (symlink - API version)
# libmylib.so        (symlink - for linking)
```

### Position Independent Code

```cmake
add_library(mylib STATIC mylib.cpp)

# Required for linking static library into shared library
set_target_properties(mylib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)
```

## Include Directories

```cmake
add_library(mylib STATIC
    src/mylib.cpp
)

# PRIVATE: Only mylib needs these
target_include_directories(mylib PRIVATE
    src/
)

# PUBLIC: mylib and its consumers need these
target_include_directories(mylib PUBLIC
    include/
)

# INTERFACE: Only consumers need these (not mylib itself)
target_include_directories(mylib INTERFACE
    external/headers/
)
```

**Directory structure:**

```
mylib/
├── CMakeLists.txt
├── src/              # Private implementation
│   ├── mylib.cpp
│   └── internal.h
└── include/          # Public API
    └── mylib.h
```

```cmake
target_include_directories(mylib
    PRIVATE src/
    PUBLIC include/
)
```

## Visibility Keywords

Understanding `PRIVATE`, `PUBLIC`, and `INTERFACE`:

```cmake
add_library(A STATIC a.cpp)
add_library(B STATIC b.cpp)
add_library(C STATIC c.cpp)

# A uses B internally, doesn't expose it
target_link_libraries(A PRIVATE B)

# A uses C and exposes it in headers
target_link_libraries(A PUBLIC C)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE A)

# app gets:
# - A (directly)
# - C (transitively via A's PUBLIC dependency)
# - NOT B (A's PRIVATE dependency)
```

:::success Rule of Thumb

- **PRIVATE**: Implementation detail
- **PUBLIC**: Part of your API
- **INTERFACE**: Requirement for users (header-only libs)
  :::

## Compile Definitions

```cmake
add_library(mylib STATIC mylib.cpp)

# Only for mylib
target_compile_definitions(mylib PRIVATE
    MYLIB_IMPLEMENTATION
)

# For mylib and its users
target_compile_definitions(mylib PUBLIC
    MYLIB_VERSION=1
)

# Only for users
target_compile_definitions(mylib INTERFACE
    USE_MYLIB
)
```

## Export Symbols (Shared Libraries)

### Windows DLL Export/Import

```cpp title="mylib_export.h"
#ifdef _WIN32
  #ifdef MYLIB_EXPORTS
    #define MYLIB_API __declspec(dllexport)
  #else
    #define MYLIB_API __declspec(dllimport)
  #endif
#else
  #define MYLIB_API
#endif

// Usage
class MYLIB_API MyClass {
public:
    void myFunction();
};

MYLIB_API void myFreeFunction();
```

```cmake
add_library(mylib SHARED mylib.cpp)

# Define export macro when building mylib
target_compile_definitions(mylib PRIVATE MYLIB_EXPORTS)
```

### CMake's generate_export_header

```cmake
include(GenerateExportHeader)

add_library(mylib SHARED mylib.cpp)

generate_export_header(mylib
    EXPORT_FILE_NAME include/mylib_export.h
)

target_include_directories(mylib PUBLIC
    ${CMAKE_CURRENT_BINARY_DIR}/include
)
```

## Complete Examples

### Static Library

```cmake
# Math library
add_library(math_lib STATIC
    src/add.cpp
    src/subtract.cpp
    src/multiply.cpp
    include/math_lib.h
)

target_include_directories(math_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(math_lib PUBLIC
    cxx_std_17
)

# Application using the library
add_executable(calculator main.cpp)
target_link_libraries(calculator PRIVATE math_lib)
```

### Shared Library

```cmake
# Graphics library
add_library(graphics SHARED
    src/renderer.cpp
    src/texture.cpp
    src/shader.cpp
)

target_include_directories(graphics PUBLIC
    include/
)

# Export symbols on Windows
if(WIN32)
    target_compile_definitions(graphics PRIVATE GRAPHICS_EXPORTS)
endif()

# Set version
set_target_properties(graphics PROPERTIES
    VERSION 2.1.0
    SOVERSION 2
)

# Game using the library
add_executable(game main.cpp)
target_link_libraries(game PRIVATE graphics)

# Install library
install(TARGETS graphics
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY include/ DESTINATION include)
```

### Header-Only Library

```cmake
# Vector math header library
add_library(vecmath INTERFACE)

target_include_directories(vecmath INTERFACE
    include/
)

target_compile_features(vecmath INTERFACE
    cxx_std_17
)

# Application
add_executable(physics_sim main.cpp)
target_link_libraries(physics_sim PRIVATE vecmath)
```

## Library Hierarchies

```cmake
# Low-level library
add_library(core STATIC
    src/core/memory.cpp
    src/core/thread.cpp
)
target_include_directories(core PUBLIC include/core)

# Mid-level library using core
add_library(engine STATIC
    src/engine/entity.cpp
    src/engine/system.cpp
)
target_include_directories(engine PUBLIC include/engine)
target_link_libraries(engine PUBLIC core)  # Expose core to users

# High-level library using engine
add_library(game STATIC
    src/game/player.cpp
    src/game/world.cpp
)
target_include_directories(game PUBLIC include/game)
target_link_libraries(game PUBLIC engine)

# Application
add_executable(mygame main.cpp)
target_link_libraries(mygame PRIVATE game)
# Automatically gets: game, engine, and core
```

## Best Practices

:::success Recommendations

1. **Modern library interface**

   ```cmake
   add_library(mylib mylib.cpp)
   target_include_directories(mylib PUBLIC include/)
   target_compile_features(mylib PUBLIC cxx_std_17)
   ```

2. **Separate public/private includes**

   ```
   mylib/
   ├── include/    # Public headers
   └── src/        # Private headers + sources
   ```

3. **Use visibility keywords correctly**
    - `PRIVATE` for implementation
    - `PUBLIC` for API requirements
    - `INTERFACE` for header-only

4. **Version shared libraries**

   ```cmake
   set_target_properties(mylib PROPERTIES
       VERSION ${PROJECT_VERSION}
       SOVERSION ${PROJECT_VERSION_MAJOR}
   )
   ```

5. **Let users choose library type**

   ```cmake
   option(BUILD_SHARED_LIBS "Build shared" OFF)
   add_library(mylib mylib.cpp)  # Type determined by option
   ```

:::

## Common Patterns

### Internal Library

```cmake
# Library not installed, only used internally
add_library(internal_utils STATIC utils.cpp)
target_include_directories(internal_utils PRIVATE src/)

set_target_properties(internal_utils PROPERTIES
    EXCLUDE_FROM_ALL TRUE  # Don't build by default
)
```

### Conditional Library Type

```cmake
if(MOBILE_PLATFORM)
    # Static linking on mobile
    add_library(mylib STATIC mylib.cpp)
else()
    # Shared linking on desktop
    add_library(mylib SHARED mylib.cpp)
endif()
```

### Library with Dependencies

```cmake
add_library(mylib STATIC mylib.cpp)

# Find dependencies
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)

# Link (users get these transitively if PUBLIC)
target_link_libraries(mylib
    PRIVATE Threads::Threads  # Internal use
    PUBLIC ZLIB::ZLIB         # Exposed in API
)
```

## Troubleshooting

### Undefined symbols in shared library

```cmake
# Ensure all dependencies are linked
target_link_libraries(mylib PRIVATE all_deps)
```

### "position independent code" error

```cmake
set_target_properties(mylib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)
```

### DLL export errors on Windows

```cmake
# Use GenerateExportHeader
include(GenerateExportHeader)
generate_export_header(mylib)
```

### Can't find headers when linking

```cmake
# Ensure PUBLIC include directories
target_include_directories(mylib PUBLIC include/)
```
