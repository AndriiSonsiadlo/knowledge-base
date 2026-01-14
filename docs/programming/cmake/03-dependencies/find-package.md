---
id: find-package
title: Finding External Packages
sidebar_label: Finding Packages
sidebar_position: 1
tags: [ c++, cmake ]
---

# Finding External Packages

## What is find_package()?

`find_package()` locates external libraries and sets up variables/targets for using them.

## Basic Usage

```cmake
find_package(PackageName [version] [REQUIRED] [COMPONENTS ...])
```

**Examples:**

```cmake
# Find any version
find_package(OpenCV)

# Find specific version or newer
find_package(Boost 1.70)

# Require package (fail if not found)
find_package(Threads REQUIRED)

# Find with components
find_package(Qt5 COMPONENTS Core Widgets REQUIRED)
```

## How It Works

CMake searches for one of two files:

1. **FindPackage.cmake** - in `CMAKE_MODULE_PATH`
2. **PackageConfig.cmake** - in various locations

### Config Mode (Preferred)

```cmake
find_package(MyPackage CONFIG)
```

Searches for:

- `MyPackageConfig.cmake`
- `mypackage-config.cmake`

**Where:**

- `/usr/lib/cmake/MyPackage/`
- `/usr/local/lib/cmake/MyPackage/`
- `<PackageName>_DIR`

### Module Mode

```cmake
find_package(MyPackage MODULE)
```

Searches for:

- `FindMyPackage.cmake`

**Where:**

- `CMAKE_MODULE_PATH`
- CMake's built-in modules

:::info Automatic Detection
CMake tries both modes automatically. Use `CONFIG` or `MODULE` to force one.
:::

## Common Packages

### Threads

```cmake
find_package(Threads REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Threads::Threads)
```

### OpenSSL

```cmake
find_package(OpenSSL REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE 
    OpenSSL::SSL 
    OpenSSL::Crypto
)
```

### Boost

```cmake
find_package(Boost 1.70 REQUIRED COMPONENTS
    filesystem
    system
    regex
)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    Boost::filesystem
    Boost::system
    Boost::regex
)
```

### Qt5/Qt6

```cmake
find_package(Qt5 COMPONENTS
    Core
    Widgets
    Network
    REQUIRED
)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    Qt5::Core
    Qt5::Widgets
    Qt5::Network
)
```

### OpenCV

```cmake
find_package(OpenCV REQUIRED)

add_executable(vision main.cpp)
target_link_libraries(vision PRIVATE ${OpenCV_LIBS})

# Or with imported target (if available)
target_link_libraries(vision PRIVATE opencv_core opencv_imgproc)
```

### Python

```cmake
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Python3::Python)
```

## Version Requirements

```cmake
# Exact version
find_package(MyPackage 2.1.3 EXACT REQUIRED)

# Minimum version
find_package(MyPackage 1.5 REQUIRED)

# Version range (CMake 3.19+)
find_package(MyPackage 1.0...2.0 REQUIRED)
```

## Components

```cmake
# Find specific components
find_package(Boost COMPONENTS
    filesystem
    regex
    REQUIRED
)

# Optional components
find_package(Boost REQUIRED COMPONENTS filesystem)
find_package(Boost COMPONENTS regex)  # Optional

if(TARGET Boost::regex)
    target_compile_definitions(myapp PRIVATE HAS_BOOST_REGEX)
    target_link_libraries(myapp PRIVATE Boost::regex)
endif()
```

## Checking Results

### Variables Set

Most packages set these:

- `<Package>_FOUND` - Whether package was found
- `<Package>_VERSION` - Version found
- `<Package>_INCLUDE_DIRS` - Include directories
- `<Package>_LIBRARIES` - Libraries to link

```cmake
find_package(ZLIB)

if(ZLIB_FOUND)
    message(STATUS "ZLIB version: ${ZLIB_VERSION}")
    message(STATUS "ZLIB include: ${ZLIB_INCLUDE_DIRS}")
    message(STATUS "ZLIB libraries: ${ZLIB_LIBRARIES}")
    
    target_include_directories(myapp PRIVATE ${ZLIB_INCLUDE_DIRS})
    target_link_libraries(myapp PRIVATE ${ZLIB_LIBRARIES})
endif()
```

### Modern Imported Targets (Preferred)

```cmake
find_package(ZLIB REQUIRED)

# ✅ Modern way - use imported target
target_link_libraries(myapp PRIVATE ZLIB::ZLIB)

# ❌ Old way - manual include/link
target_include_directories(myapp PRIVATE ${ZLIB_INCLUDE_DIRS})
target_link_libraries(myapp PRIVATE ${ZLIB_LIBRARIES})
```

:::success Use Imported Targets
Modern packages provide `Package::Component` targets. These are self-contained and handle includes/links automatically.
:::

## Handling Optional Packages

```cmake
# Try to find optional package
find_package(OptionalLib)

if(OptionalLib_FOUND)
    message(STATUS "OptionalLib found, enabling feature")
    target_compile_definitions(myapp PRIVATE HAS_OPTIONAL_LIB)
    target_link_libraries(myapp PRIVATE OptionalLib::OptionalLib)
else()
    message(STATUS "OptionalLib not found, disabling feature")
endif()
```

**With option:**

```cmake
option(USE_OPTIONALLIB "Use OptionalLib if available" ON)

if(USE_OPTIONALLIB)
    find_package(OptionalLib)
    if(OptionalLib_FOUND)
        target_link_libraries(myapp PRIVATE OptionalLib::OptionalLib)
    else()
        message(WARNING "OptionalLib requested but not found")
    endif()
endif()
```

## Specifying Package Location

### Hint Paths

```cmake
# Set before find_package
set(MyPackage_DIR "/path/to/MyPackageConfig.cmake")
find_package(MyPackage REQUIRED)
```

```bash
# Or from command line
cmake -DMyPackage_DIR=/path/to/cmake ..
```

### CMAKE_PREFIX_PATH

```cmake
list(APPEND CMAKE_PREFIX_PATH "/opt/mypackage")
find_package(MyPackage REQUIRED)
```

```bash
# Or from command line
cmake -DCMAKE_PREFIX_PATH=/opt/mypackage ..
```

### Environment Variables

```bash
# Set package location
export MyPackage_DIR=/path/to/package/cmake
cmake ..
```

## Custom Module Path

```cmake
# Add custom Find modules
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")

find_package(CustomPackage REQUIRED)
```

**Directory structure:**

```
project/
├── CMakeLists.txt
└── cmake/
    └── modules/
        └── FindCustomPackage.cmake
```

## Writing Custom Find Modules

```cmake title="cmake/modules/FindMyLib.cmake"
# Find include directory
find_path(MyLib_INCLUDE_DIR
    NAMES mylib.h
    PATHS /usr/include /usr/local/include
)

# Find library
find_library(MyLib_LIBRARY
    NAMES mylib
    PATHS /usr/lib /usr/local/lib
)

# Set version (if possible)
if(EXISTS "${MyLib_INCLUDE_DIR}/mylib_version.h")
    file(READ "${MyLib_INCLUDE_DIR}/mylib_version.h" version_header)
    string(REGEX MATCH "VERSION ([0-9]+\\.[0-9]+\\.[0-9]+)" _ "${version_header}")
    set(MyLib_VERSION ${CMAKE_MATCH_1})
endif()

# Standard handling
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(MyLib
    REQUIRED_VARS MyLib_LIBRARY MyLib_INCLUDE_DIR
    VERSION_VAR MyLib_VERSION
)

# Create imported target
if(MyLib_FOUND AND NOT TARGET MyLib::MyLib)
    add_library(MyLib::MyLib UNKNOWN IMPORTED)
    set_target_properties(MyLib::MyLib PROPERTIES
        IMPORTED_LOCATION "${MyLib_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${MyLib_INCLUDE_DIR}"
    )
endif()

# Set output variables
if(MyLib_FOUND)
    set(MyLib_LIBRARIES ${MyLib_LIBRARY})
    set(MyLib_INCLUDE_DIRS ${MyLib_INCLUDE_DIR})
endif()

mark_as_advanced(MyLib_INCLUDE_DIR MyLib_LIBRARY)
```

**Usage:**

```cmake
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")

find_package(MyLib REQUIRED)

add_executable(app main.cpp)
target_link_libraries(app PRIVATE MyLib::MyLib)
```

## Practical Examples

### Multi-Package Application

```cmake
cmake_minimum_required(VERSION 3.15)
project(MultiPackageApp)

# System libraries
find_package(Threads REQUIRED)
find_package(ZLIB REQUIRED)

# Graphics
find_package(OpenGL REQUIRED)
find_package(glfw3 REQUIRED)

# Optional
find_package(OpenCV)

add_executable(app
    src/main.cpp
    src/graphics.cpp
)

# Required dependencies
target_link_libraries(app PRIVATE
    Threads::Threads
    ZLIB::ZLIB
    OpenGL::GL
    glfw
)

# Optional dependency
if(OpenCV_FOUND)
    target_compile_definitions(app PRIVATE HAS_OPENCV)
    target_link_libraries(app PRIVATE ${OpenCV_LIBS})
endif()
```

### Version-Specific Features

```cmake
find_package(Boost 1.70 REQUIRED COMPONENTS filesystem)

if(Boost_VERSION VERSION_GREATER_EQUAL "1.75")
    message(STATUS "Using Boost 1.75+ features")
    target_compile_definitions(app PRIVATE BOOST_NEW_API)
endif()
```

### Platform-Specific Packages

```cmake
if(WIN32)
    find_package(WindowsSDK REQUIRED)
    target_link_libraries(app PRIVATE WindowsSDK::Core)
elseif(APPLE)
    find_library(COCOA_LIBRARY Cocoa REQUIRED)
    target_link_libraries(app PRIVATE ${COCOA_LIBRARY})
elseif(UNIX)
    find_package(X11 REQUIRED)
    target_link_libraries(app PRIVATE X11::X11)
endif()
```

## Troubleshooting

### Package Not Found

```cmake
find_package(MyPackage)

if(NOT MyPackage_FOUND)
    message(STATUS "MyPackage not found. Tried:")
    message(STATUS "  CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")
    message(STATUS "  CMAKE_MODULE_PATH: ${CMAKE_MODULE_PATH}")
    message(STATUS "  MyPackage_DIR: ${MyPackage_DIR}")
    
    message(FATAL_ERROR "Please install MyPackage or set MyPackage_DIR")
endif()
```

:::warning Common Issues

1. **Wrong package name**

   ```cmake
   find_package(opencv)  # ❌ Wrong
   find_package(OpenCV)  # ✅ Correct (case-sensitive!)
   ```

2. **Missing components**

   ```cmake
   find_package(Qt5)  # ❌ No components
   find_package(Qt5 COMPONENTS Core Widgets)  # ✅ Specify
   ```

3. **Package not in standard location**

   ```bash
   cmake -DCMAKE_PREFIX_PATH=/custom/install ..
   ```

4. **Config file not found**

   ```bash
   cmake -DMyPackage_DIR=/path/to/cmake/config ..
   ```

:::

## Best Practices

:::success Recommendations

1. **Use REQUIRED for mandatory packages**

   ```cmake
   find_package(Threads REQUIRED)
   ```

2. **Prefer imported targets**

   ```cmake
   target_link_libraries(app PRIVATE Package::Component)
   ```

3. **Check version explicitly**

   ```cmake
   find_package(Boost 1.70 REQUIRED)
   ```

4. **Handle optional packages gracefully**

   ```cmake
   find_package(Optional)
   if(Optional_FOUND)
       target_link_libraries(app PRIVATE Optional::Optional)
   endif()
   ```

5. **Provide helpful messages**

   ```cmake
   if(NOT Package_FOUND)
       message(STATUS "Package not found. Install with:")
       message(STATUS "  Ubuntu: sudo apt install libpackage-dev")
       message(STATUS "  macOS: brew install package")
   endif()
   ```

:::

## Quick Reference

```cmake
# Basic
find_package(Package REQUIRED)

# With version
find_package(Package 2.0 REQUIRED)

# With components
find_package(Package COMPONENTS comp1 comp2 REQUIRED)

# Optional
find_package(Package)
if(Package_FOUND)
    # use it
endif()

# Force config mode
find_package(Package CONFIG REQUIRED)

# Specify location
set(Package_DIR /path/to/cmake)
find_package(Package REQUIRED)

# Use imported target (preferred)
target_link_libraries(app PRIVATE Package::Package)

# Old style (avoid)
target_include_directories(app PRIVATE ${Package_INCLUDE_DIRS})
target_link_libraries(app PRIVATE ${Package_LIBRARIES})
```
