---
id: target-properties
title: Target Properties
sidebar_label: Target Properties
sidebar_position: 3
tags: [c++, cmake, targets, properties, configuration]
---

# Target Properties

## Understanding Target Properties

Target properties are key-value pairs that configure how a target (executable or library) is built, linked, and installed. They control everything from compiler flags and output locations to version numbers and installation paths. Properties provide fine-grained control over individual targets without affecting the global build configuration.

Modern CMake encourages setting properties on specific targets rather than using global commands. This approach creates more maintainable, modular build systems where each target explicitly declares its requirements.

## Setting Properties

There are several ways to set target properties, each with different use cases and levels of convenience.

### set_target_properties()

This is the most direct way to set one or more properties on one or more targets simultaneously. It's useful when you need to set multiple properties or configure multiple targets identically.

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    OUTPUT_NAME "MyApplication"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
```

You can set properties on multiple targets at once:

```cmake showLineNumbers 
add_executable(app1 app1.cpp)
add_executable(app2 app2.cpp)

# Set same properties for both
set_target_properties(app1 app2 PROPERTIES
    CXX_STANDARD 17
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
```

### set_property()

This command offers more flexibility, allowing you to set properties with different behaviors like appending or using generator expressions.

```cmake showLineNumbers 
add_library(mylib mylib.cpp)

# Set a property
set_property(TARGET mylib PROPERTY
    POSITION_INDEPENDENT_CODE ON
)

# Append to a property
set_property(TARGET mylib APPEND PROPERTY
    COMPILE_DEFINITIONS "EXTRA_DEFINE"
)

# Set for multiple targets
set_property(TARGET lib1 lib2 lib3 PROPERTY
    CXX_STANDARD 17
)
```

The `APPEND` keyword is particularly useful for properties that hold lists of values.

### get_target_property()

Retrieve the current value of a target property. This is useful for debugging or conditional logic based on existing property values.

```cmake showLineNumbers 
get_target_property(output_name myapp OUTPUT_NAME)
message(STATUS "Output name: ${output_name}")

# Check if a property is set
get_target_property(pic_enabled mylib POSITION_INDEPENDENT_CODE)
if(pic_enabled)
    message(STATUS "PIC is enabled for mylib")
endif()
```

## Common Target Properties

### C++ Standard

Control which C++ standard your target uses. This is fundamental for modern C++ development.

```cmake showLineNumbers 
add_executable(myapp main.cpp)

# Method 1: Using properties
set_target_properties(myapp PROPERTIES
    CXX_STANDARD 17                # C++ version: 11, 14, 17, 20, 23
    CXX_STANDARD_REQUIRED ON       # Error if compiler doesn't support it
    CXX_EXTENSIONS OFF             # Use -std=c++17, not -std=gnu++17
)

# Method 2: Using target_compile_features (preferred)
target_compile_features(myapp PRIVATE cxx_std_17)
```

**CXX_STANDARD:** Specifies the C++ version. Note this sets the minimum version - the compiler may use a newer one if available and compatible.

**CXX_STANDARD_REQUIRED:** When ON, CMake will error if the compiler cannot support the requested standard. When OFF, it falls back to the latest supported version.

**CXX_EXTENSIONS:** Controls whether compiler-specific extensions are enabled. OFF gives you portable, standard-compliant C++. ON allows GNU extensions like `typeof` or `__attribute__`.

### Output Configuration

Control where and how target output files are named and placed.

#### Output Name

Change the name of the generated file:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

# Creates "MyApplication" instead of "myapp"
set_target_properties(myapp PROPERTIES
    OUTPUT_NAME "MyApplication"
)

# Different names per configuration
set_target_properties(myapp PROPERTIES
    OUTPUT_NAME_DEBUG "MyApp_Debug"
    OUTPUT_NAME_RELEASE "MyApp"
)
```

#### Output Directory

Specify where built files are placed:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

# Put executable in bin/
set_target_properties(myapp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Different locations per configuration
set_target_properties(myapp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/debug/bin"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/release/bin"
)
```

**Directory properties by target type:**

- **RUNTIME_OUTPUT_DIRECTORY:** For executables and DLLs on Windows
- **LIBRARY_OUTPUT_DIRECTORY:** For shared libraries (`.so`, `.dylib`)
- **ARCHIVE_OUTPUT_DIRECTORY:** For static libraries (`.a`, `.lib`)

```cmake showLineNumbers 
# Library output example
add_library(mylib SHARED mylib.cpp)

set_target_properties(mylib PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)
```

#### Prefix and Suffix

Control the prefix and suffix of library names:

```cmake showLineNumbers 
add_library(mylib SHARED mylib.cpp)

# On Unix: normally creates "libmylib.so"
# This creates "mylib.so" (no lib prefix)
set_target_properties(mylib PROPERTIES
    PREFIX ""
)

# Custom suffix
set_target_properties(mylib PROPERTIES
    SUFFIX ".so.1"
)
```

### Position Independent Code (PIC)

Position Independent Code is required when static libraries are linked into shared libraries. On most platforms, shared libraries must be loadable at any memory address.

```cmake showLineNumbers 
add_library(mystaticlib STATIC lib.cpp)

# Enable PIC (required if this will be linked into a shared lib)
set_target_properties(mystaticlib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)
```

**When you need PIC:**

- Static library that will be linked into a shared library
- Creating plugins or dynamically loaded modules
- Most modern development (many compilers default to PIC now)

**Performance note:** PIC code has a small performance overhead on some architectures (particularly 32-bit x86), but it's negligible on modern 64-bit systems.

### Version Information

Version properties are important for shared libraries, enabling API compatibility tracking.

```cmake showLineNumbers 
add_library(mylib SHARED mylib.cpp)

set_target_properties(mylib PROPERTIES
    VERSION 3.2.1      # Full version (changes with every release)
    SOVERSION 3        # API version (changes only on incompatible changes)
)
```

On Linux, this creates:

- `libmylib.so.3.2.1` (actual file with full version)
- `libmylib.so.3` (symlink, API compatibility version)
- `libmylib.so` (symlink for building against the library)

**VERSION:** The full semantic version of your library. Update this with each release.

**SOVERSION:** The "shared object version" - increment only when you make ABI-incompatible changes. This allows the system to ensure binary compatibility. Applications linked against `libmylib.so.3` will work with any version 3.x.y but not with version 4.0.0.

### Compile Definitions

Add preprocessor macros to a target. These become `-D` flags passed to the compiler.

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    COMPILE_DEFINITIONS "DEBUG_MODE;VERSION=1.0"
)

# Better: use target_compile_definitions
target_compile_definitions(myapp PRIVATE
    DEBUG_MODE
    VERSION=1.0
    $<$<CONFIG:Debug>:VERBOSE_LOGGING>
)
```

While you can set `COMPILE_DEFINITIONS` as a property, `target_compile_definitions()` is preferred because it supports visibility keywords (PRIVATE/PUBLIC/INTERFACE) and generator expressions more naturally.

### Include Directories

While you can set include directories as properties, using `target_include_directories()` is more common and clearer:

```cmake showLineNumbers 
add_library(mylib mylib.cpp)

# Property approach
set_target_properties(mylib PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

# Preferred approach
target_include_directories(mylib PUBLIC
    include/
)
```

The command-based approach better expresses intent and handles visibility keywords naturally.

## Platform-Specific Properties

### Windows-Specific

Windows has unique requirements for GUI applications and DLL exports.

#### WIN32 Executable

Create a GUI application without a console window:

```cmake showLineNumbers 
add_executable(myapp WIN32 main.cpp)

# Or set as property
set_target_properties(myapp PROPERTIES
    WIN32_EXECUTABLE ON
)
```

When `WIN32_EXECUTABLE` is ON, the application uses `WinMain` instead of `main` as the entry point and doesn't create a console window.

#### DLL Export/Import

Windows requires explicit export/import declarations for shared libraries:

```cmake showLineNumbers 
add_library(mylib SHARED mylib.cpp)

# Automatically export all symbols (Windows only)
set_target_properties(mylib PROPERTIES
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)
```

This is a convenience feature. For production code, you typically want manual control using `__declspec(dllexport/dllimport)` or CMake's `GenerateExportHeader`.

### macOS-Specific

macOS applications can be bundled with resources and frameworks.

#### Application Bundle

Create a `.app` bundle on macOS:

```cmake showLineNumbers 
add_executable(MyApp MACOSX_BUNDLE main.cpp)

set_target_properties(MyApp PROPERTIES
    MACOSX_BUNDLE_BUNDLE_NAME "My Application"
    MACOSX_BUNDLE_GUI_IDENTIFIER "com.example.myapp"
    MACOSX_BUNDLE_SHORT_VERSION_STRING "1.0"
    MACOSX_BUNDLE_LONG_VERSION_STRING "1.0.0"
    MACOSX_BUNDLE_ICON_FILE "AppIcon"
)
```

This creates `MyApp.app` with the proper directory structure and Info.plist.

#### Framework

Create a macOS framework:

```cmake showLineNumbers 
add_library(MyFramework SHARED framework.cpp)

set_target_properties(MyFramework PROPERTIES
    FRAMEWORK ON
    FRAMEWORK_VERSION A
    MACOSX_FRAMEWORK_IDENTIFIER com.example.framework
    VERSION 1.0.0
    SOVERSION 1.0.0
    PUBLIC_HEADER "include/public_header.h"
)
```

Frameworks bundle headers, resources, and the library into a single package.

### RPATH Configuration

RPATH tells executables where to find shared libraries at runtime. This is critical for proper deployment.

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
    INSTALL_RPATH_USE_LINK_PATH ON
    BUILD_RPATH "${CMAKE_BINARY_DIR}/lib"
)
```

**INSTALL_RPATH:** The runtime search path embedded in the installed executable. The executable will look here for shared libraries.

**INSTALL_RPATH_USE_LINK_PATH:** When ON, automatically add directories of linked targets to RPATH. This usually does what you want.

**BUILD_RPATH:** RPATH to use during development (before installation). Allows running from build directory.

**Common RPATH patterns:**

```cmake showLineNumbers 
# Use $ORIGIN to make path relative to executable location
set_target_properties(myapp PROPERTIES
    INSTALL_RPATH "$ORIGIN/../lib"
)

# Multiple paths
set_target_properties(myapp PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib:/opt/custom/lib"
)
```

`$ORIGIN` (Linux) or `@executable_path` (macOS) refers to the directory containing the executable, enabling relocatable installations.

## Optimization and Build Properties

### Interprocedural Optimization (LTO)

Link-Time Optimization allows the compiler to optimize across translation units, potentially improving performance significantly.

```cmake showLineNumbers 
add_executable(myapp main.cpp utils.cpp)

# Enable LTO if supported
include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported OUTPUT error)

if(ipo_supported)
    set_target_properties(myapp PROPERTIES
        INTERPROCEDURAL_OPTIMIZATION ON
    )
    message(STATUS "IPO/LTO enabled")
else()
    message(STATUS "IPO/LTO not supported: ${error}")
endif()
```

LTO can significantly improve performance but increases build time. Typically used only for Release builds:

```cmake showLineNumbers 
set_target_properties(myapp PROPERTIES
    INTERPROCEDURAL_OPTIMIZATION_RELEASE ON
)
```

### Visibility

Control symbol visibility in shared libraries (Unix/Linux):

```cmake showLineNumbers 
add_library(mylib SHARED mylib.cpp)

set_target_properties(mylib PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)
```

**CXX_VISIBILITY_PRESET hidden:** Makes symbols private by default. You must explicitly mark public API with `__attribute__((visibility("default")))` or use `GenerateExportHeader`.

**VISIBILITY_INLINES_HIDDEN:** Hides inline functions from the ABI, reducing symbol count and potentially improving link time and performance.

This is good practice for shared libraries - it creates cleaner ABIs and can improve performance by allowing more optimization.

## Debug and Development Properties

### Debug Postfix

Add a suffix to debug builds to distinguish them from release builds:

```cmake showLineNumbers 
add_library(mylib STATIC mylib.cpp)

set_target_properties(mylib PROPERTIES
    DEBUG_POSTFIX "d"
)
```

Creates `libmylib.a` for Release and `libmylibd.a` for Debug, allowing both to coexist.

### Build Exclusion

Exclude targets from the default build:

```cmake showLineNumbers 
add_executable(optional_tool tool.cpp)

set_target_properties(optional_tool PROPERTIES
    EXCLUDE_FROM_ALL ON
)
```

The target won't build with a plain `make` or `cmake --build .` but can be built explicitly: `cmake --build . --target optional_tool`

Useful for:

- Documentation generation targets
- Optional tools
- Test executables
- Examples

## Linking Properties

### Link Libraries

While `target_link_libraries()` is the standard way to link, you can also use properties:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    LINK_LIBRARIES "lib1;lib2;lib3"
)

# Better: use target_link_libraries()
target_link_libraries(myapp PRIVATE lib1 lib2 lib3)
```

The command-based approach is preferred because it handles visibility and transitive dependencies correctly.

### Link Flags

Add custom linker flags:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    LINK_FLAGS "-Wl,--as-needed -Wl,--no-undefined"
)

# Better: use target_link_options() (CMake 3.13+)
target_link_options(myapp PRIVATE
    -Wl,--as-needed
    -Wl,--no-undefined
)
```

### Link Dependencies

Control the order and method of linking:

```cmake showLineNumbers 
add_library(mylib STATIC mylib.cpp)

set_target_properties(mylib PROPERTIES
    LINK_INTERFACE_LIBRARIES ""  # Don't propagate dependencies
)
```

This is advanced and rarely needed - usually `PRIVATE/PUBLIC/INTERFACE` in `target_link_libraries()` handles what you need.

## Installation Properties

Configure how targets are installed.

### Install Name (macOS)

On macOS, shared libraries embed their expected installation path:

```cmake showLineNumbers 
add_library(mylib SHARED mylib.cpp)

set_target_properties(mylib PROPERTIES
    INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
)
```

This tells the library where it expects to be installed, which affects how executables find it at runtime.

### Install RPATH

Control RPATH in installed binaries:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
    INSTALL_RPATH_USE_LINK_PATH ON
    SKIP_BUILD_RPATH OFF
    BUILD_WITH_INSTALL_RPATH OFF
    INSTALL_RPATH_USE_ORIGIN ON
)
```

**SKIP_BUILD_RPATH:** Don't set RPATH for build tree. Usually OFF so you can run from build directory.

**BUILD_WITH_INSTALL_RPATH:** Use install RPATH even in build tree. Usually OFF for flexibility during development.

**INSTALL_RPATH_USE_ORIGIN:** Enable `$ORIGIN` substitution in RPATH, allowing relative paths.

## Custom Properties

You can define custom properties for organizational purposes or meta-information:

```cmake showLineNumbers 
# Define a custom property
define_property(TARGET PROPERTY CUSTOM_CATEGORY
    BRIEF_DOCS "Category of the target"
    FULL_DOCS "Specifies which category this target belongs to"
)

add_executable(myapp main.cpp)
set_target_properties(myapp PROPERTIES
    CUSTOM_CATEGORY "Tools"
)

# Later, query it
get_target_property(category myapp CUSTOM_CATEGORY)
message(STATUS "Target category: ${category}")
```

This is useful for:

- Organizing targets in large projects
- Generating custom reports
- Conditional processing based on target metadata

## Complete Example

Here's a comprehensive example showing various properties in context:

```cmake showLineNumbers 
cmake_minimum_required(VERSION 3.15)
project(CompleteExample VERSION 1.2.3)

# Shared library with full configuration
add_library(mylib SHARED
    src/mylib.cpp
    src/utils.cpp
)

set_target_properties(mylib PROPERTIES
    # C++ standard
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    
    # Version information
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    
    # Output configuration
    OUTPUT_NAME "myproject_lib"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    
    # Position independent code
    POSITION_INDEPENDENT_CODE ON
    
    # Symbol visibility
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
    
    # Debug postfix
    DEBUG_POSTFIX "d"
    
    # Installation
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
    INSTALL_RPATH_USE_LINK_PATH ON
)

# Windows-specific
if(WIN32)
    set_target_properties(mylib PROPERTIES
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )
endif()

# macOS-specific
if(APPLE)
    set_target_properties(mylib PROPERTIES
        INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
        FRAMEWORK OFF  # Could be ON to create framework
    )
endif()

# Executable
add_executable(myapp
    src/main.cpp
    src/application.cpp
)

set_target_properties(myapp PROPERTIES
    # C++ standard
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    
    # Output configuration
    OUTPUT_NAME "MyApplication"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    
    # Debug builds
    OUTPUT_NAME_DEBUG "MyApplication_Debug"
    
    # LTO for release builds
    INTERPROCEDURAL_OPTIMIZATION_RELEASE ON
    
    # Installation
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
)

# Link the library
target_link_libraries(myapp PRIVATE mylib)

# Installation
install(TARGETS myapp mylib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
```

## Best Practices

:::success Property Management

1. **Use target-specific commands when available**
    - `target_compile_features()` over setting `CXX_STANDARD`
    - `target_compile_definitions()` over setting `COMPILE_DEFINITIONS`
    - `target_include_directories()` over setting `INCLUDE_DIRECTORIES`

2. **Set properties per target, not globally**
    - Avoids unexpected behavior in multi-target projects
    - Makes dependencies explicit
    - Improves modularity

3. **Use generator expressions for conditional properties**

   ```cmake showLineNumbers 
   set_target_properties(myapp PROPERTIES
       COMPILE_DEFINITIONS "$<$<CONFIG:Debug>:DEBUG_MODE>"
   )
   ```

4. **Document custom properties**
    - Use `define_property()` to add documentation
    - Makes intent clear to other developers

5. **Be explicit about requirements**
    - Set `CXX_STANDARD_REQUIRED ON` if you need a specific standard
    - Don't rely on compiler defaults
      :::

## Common Pitfalls

:::warning Avoid These Mistakes

1. **Setting global properties instead of target properties**

   ```cmake showLineNumbers 
   # ❌ Bad - affects all targets
   set(CMAKE_CXX_STANDARD 17)
   
   # ✅ Good - affects only this target
   set_target_properties(myapp PROPERTIES CXX_STANDARD 17)
   ```

2. **Forgetting POSITION_INDEPENDENT_CODE for static libs**

   ```cmake showLineNumbers 
   # If static lib will link into shared lib
   set_target_properties(mystaticlib PROPERTIES
       POSITION_INDEPENDENT_CODE ON
   )
   ```

3. **Not setting SOVERSION for shared libraries**

   ```cmake showLineNumbers 
   # Always set for shared libraries
   set_target_properties(mylib PROPERTIES
       VERSION ${PROJECT_VERSION}
       SOVERSION ${PROJECT_VERSION_MAJOR}
   )
   ```

4. **Using deprecated properties**
    - Avoid `COMPILE_FLAGS` (use `target_compile_options()`)
    - Avoid `LINK_FLAGS` (use `target_link_options()`)
      :::

## Quick Reference

```cmake showLineNumbers 
# C++ Standard
set_target_properties(target PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# Output configuration
set_target_properties(target PROPERTIES
    OUTPUT_NAME "name"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Version (shared libraries)
set_target_properties(target PROPERTIES
    VERSION 1.2.3
    SOVERSION 1
)

# Position Independent Code
set_target_properties(target PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

# Debug postfix
set_target_properties(target PROPERTIES
    DEBUG_POSTFIX "d"
)

# RPATH
set_target_properties(target PROPERTIES
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
    INSTALL_RPATH_USE_LINK_PATH ON
)

# LTO
set_target_properties(target PROPERTIES
    INTERPROCEDURAL_OPTIMIZATION ON
)

# Get property value
get_target_property(value target PROPERTY_NAME)
```
