---
id: find-modules
title: Writing Find Modules
sidebar_label: Find Modules
tags: [cmake, find-modules, packages, dependencies]
---

# Writing Find Modules

## What Are Find Modules?

Find modules are CMake scripts that locate external packages and set up variables/targets for using them. When you call `find_package(MyLib)`, CMake searches for `FindMyLib.cmake`.

Modern packages provide Config files (`MyLibConfig.cmake`), but you may need to write Find modules for:

- Legacy libraries without CMake support
- System libraries
- Custom internal packages
- Wrapping non-CMake build systems

## Basic Structure

A Find module must:

1. Search for the package (headers, libraries)
2. Set result variables
3. Call `find_package_handle_standard_args()`
4. Create imported targets (modern practice)

### Minimal Example

```cmake title="cmake/FindMyLib.cmake"
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

# Handle standard arguments
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(MyLib
    REQUIRED_VARS MyLib_LIBRARY MyLib_INCLUDE_DIR
)

# Create imported target
if(MyLib_FOUND AND NOT TARGET MyLib::MyLib)
    add_library(MyLib::MyLib UNKNOWN IMPORTED)
    set_target_properties(MyLib::MyLib PROPERTIES
        IMPORTED_LOCATION "${MyLib_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${MyLib_INCLUDE_DIR}"
    )
endif()

# Set standard variables
if(MyLib_FOUND)
    set(MyLib_LIBRARIES ${MyLib_LIBRARY})
    set(MyLib_INCLUDE_DIRS ${MyLib_INCLUDE_DIR})
endif()

# Hide cache variables from GUI
mark_as_advanced(MyLib_INCLUDE_DIR MyLib_LIBRARY)
```

**Usage:**

```cmake
list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)

find_package(MyLib REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE MyLib::MyLib)
```

## Finding Headers

Use `find_path()` to locate header files:

```cmake
find_path(MyLib_INCLUDE_DIR
    NAMES mylib/api.h          # Header to find
    PATHS                      # Search paths
        /usr/include
        /usr/local/include
        $ENV{MYLIB_ROOT}/include
    PATH_SUFFIXES mylib        # Look in subdirectories
    DOC "MyLib include directory"
)
```

**Key options:**

- `NAMES`: Headers to search for (can list multiple)
- `PATHS`: Explicit paths to check
- `PATH_SUFFIXES`: Subdirectories to check within each path
- `DOC`: Description for cache variable

**Multiple header locations:**

```cmake
find_path(MyLib_INCLUDE_DIR
    NAMES mylib.h
    PATHS /usr/include /usr/local/include
)

find_path(MyLib_CONFIG_DIR
    NAMES mylib/config.h
    PATHS /etc/mylib /usr/local/etc/mylib
)
```

## Finding Libraries

Use `find_library()` to locate library files:

```cmake
find_library(MyLib_LIBRARY
    NAMES mylib libmylib        # Library names (without prefix/suffix)
    PATHS
        /usr/lib
        /usr/local/lib
        $ENV{MYLIB_ROOT}/lib
    PATH_SUFFIXES lib64 lib     # Check lib64 first, then lib
    DOC "MyLib library"
)
```

**Platform considerations:**

```cmake
# Different names on different platforms
if(WIN32)
    set(LIB_NAMES mylib.lib)
elseif(APPLE)
    set(LIB_NAMES libmylib.dylib libmylib.a)
else()
    set(LIB_NAMES libmylib.so libmylib.a)
endif()

find_library(MyLib_LIBRARY
    NAMES ${LIB_NAMES}
    # ...
)
```

## Version Detection

Extract version from header or library:

```cmake
# Find version from header
if(EXISTS "${MyLib_INCLUDE_DIR}/mylib/version.h")
    file(READ "${MyLib_INCLUDE_DIR}/mylib/version.h" version_header)
    
    string(REGEX MATCH "MYLIB_VERSION_MAJOR ([0-9]+)" _ "${version_header}")
    set(MyLib_VERSION_MAJOR ${CMAKE_MATCH_1})
    
    string(REGEX MATCH "MYLIB_VERSION_MINOR ([0-9]+)" _ "${version_header}")
    set(MyLib_VERSION_MINOR ${CMAKE_MATCH_1})
    
    string(REGEX MATCH "MYLIB_VERSION_PATCH ([0-9]+)" _ "${version_header}")
    set(MyLib_VERSION_PATCH ${CMAKE_MATCH_1})
    
    set(MyLib_VERSION "${MyLib_VERSION_MAJOR}.${MyLib_VERSION_MINOR}.${MyLib_VERSION_PATCH}")
endif()

# Pass to standard args handler
find_package_handle_standard_args(MyLib
    REQUIRED_VARS MyLib_LIBRARY MyLib_INCLUDE_DIR
    VERSION_VAR MyLib_VERSION
)
```

**Using pkg-config for version:**

```cmake
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_MyLib QUIET mylib)
    set(MyLib_VERSION ${PC_MyLib_VERSION})
endif()
```

## Components

Handle libraries with optional components:

```cmake title="FindMyLib.cmake"
# Core library (always required)
find_library(MyLib_CORE_LIBRARY
    NAMES mylib_core
    # ...
)

# Optional components
set(MyLib_COMPONENTS network graphics audio)

foreach(component ${MyLib_FIND_COMPONENTS})
    if(NOT component IN_LIST MyLib_COMPONENTS)
        message(FATAL_ERROR "Unknown component: ${component}")
    endif()
    
    find_library(MyLib_${component}_LIBRARY
        NAMES mylib_${component}
        PATHS /usr/lib /usr/local/lib
    )
    
    if(MyLib_${component}_LIBRARY)
        set(MyLib_${component}_FOUND TRUE)
        list(APPEND MyLib_LIBRARIES ${MyLib_${component}_LIBRARY})
    else()
        set(MyLib_${component}_FOUND FALSE)
        if(MyLib_FIND_REQUIRED_${component})
            message(FATAL_ERROR "Required component ${component} not found")
        endif()
    endif()
endforeach()

# Standard handling
find_package_handle_standard_args(MyLib
    REQUIRED_VARS MyLib_CORE_LIBRARY MyLib_INCLUDE_DIR
    HANDLE_COMPONENTS
)
```

**Usage:**

```cmake
find_package(MyLib REQUIRED COMPONENTS network graphics)

if(MyLib_network_FOUND)
    # Use network component
endif()
```

## Creating Imported Targets

Modern Find modules create imported targets:

```cmake
if(MyLib_FOUND AND NOT TARGET MyLib::MyLib)
    # Static or shared library
    add_library(MyLib::MyLib UNKNOWN IMPORTED)
    
    set_target_properties(MyLib::MyLib PROPERTIES
        IMPORTED_LOCATION "${MyLib_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${MyLib_INCLUDE_DIR}"
    )
    
    # If library has dependencies
    set_target_properties(MyLib::MyLib PROPERTIES
        INTERFACE_LINK_LIBRARIES "Threads::Threads;ZLIB::ZLIB"
    )
    
    # If different configurations
    if(MyLib_LIBRARY_DEBUG)
        set_target_properties(MyLib::MyLib PROPERTIES
            IMPORTED_LOCATION_DEBUG "${MyLib_LIBRARY_DEBUG}"
            IMPORTED_LOCATION_RELEASE "${MyLib_LIBRARY_RELEASE}"
        )
    endif()
endif()
```

**Component targets:**

```cmake
# Core library
add_library(MyLib::Core UNKNOWN IMPORTED)
set_target_properties(MyLib::Core PROPERTIES
    IMPORTED_LOCATION "${MyLib_CORE_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${MyLib_INCLUDE_DIR}"
)

# Component
if(MyLib_network_FOUND)
    add_library(MyLib::Network UNKNOWN IMPORTED)
    set_target_properties(MyLib::Network PROPERTIES
        IMPORTED_LOCATION "${MyLib_network_LIBRARY}"
        INTERFACE_LINK_LIBRARIES "MyLib::Core"
    )
endif()
```

## Complete Example

A production-ready Find module:

```cmake title="cmake/FindSQLite3.cmake"
#[=======================================================================[.rst:
FindSQLite3
-----------

Finds the SQLite3 library.

Imported Targets
^^^^^^^^^^^^^^^^

This module provides the following imported targets, if found:

``SQLite3::SQLite3``
  The SQLite3 library

Result Variables
^^^^^^^^^^^^^^^^

This will define the following variables:

``SQLite3_FOUND``
  True if the system has the SQLite3 library.
``SQLite3_VERSION``
  The version of the SQLite3 library.
``SQLite3_INCLUDE_DIRS``
  Include directories needed to use SQLite3.
``SQLite3_LIBRARIES``
  Libraries needed to link to SQLite3.

Cache Variables
^^^^^^^^^^^^^^^

The following cache variables may also be set:

``SQLite3_INCLUDE_DIR``
  The directory containing ``sqlite3.h``.
``SQLite3_LIBRARY``
  The path to the SQLite3 library.

#]=======================================================================]

# Use pkg-config if available
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_SQLite3 QUIET sqlite3)
    set(SQLite3_VERSION ${PC_SQLite3_VERSION})
endif()

# Find include directory
find_path(SQLite3_INCLUDE_DIR
    NAMES sqlite3.h
    PATHS ${PC_SQLite3_INCLUDE_DIRS}
    PATH_SUFFIXES include
)

# Find library
find_library(SQLite3_LIBRARY
    NAMES sqlite3
    PATHS ${PC_SQLite3_LIBRARY_DIRS}
    PATH_SUFFIXES lib lib64
)

# Extract version from header if not found via pkg-config
if(SQLite3_INCLUDE_DIR AND NOT SQLite3_VERSION)
    file(READ "${SQLite3_INCLUDE_DIR}/sqlite3.h" version_header)
    string(REGEX MATCH "SQLITE_VERSION[ \t]+\"([0-9.]+)\"" _ "${version_header}")
    set(SQLite3_VERSION ${CMAKE_MATCH_1})
endif()

# Standard argument handling
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(SQLite3
    REQUIRED_VARS
        SQLite3_LIBRARY
        SQLite3_INCLUDE_DIR
    VERSION_VAR SQLite3_VERSION
)

# Create imported target
if(SQLite3_FOUND AND NOT TARGET SQLite3::SQLite3)
    add_library(SQLite3::SQLite3 UNKNOWN IMPORTED)
    set_target_properties(SQLite3::SQLite3 PROPERTIES
        IMPORTED_LOCATION "${SQLite3_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${SQLite3_INCLUDE_DIR}"
    )
    
    # SQLite3 may need threading library
    find_package(Threads)
    if(CMAKE_USE_PTHREADS_INIT)
        set_target_properties(SQLite3::SQLite3 PROPERTIES
            INTERFACE_LINK_LIBRARIES Threads::Threads
        )
    endif()
endif()

# Set standard variables
if(SQLite3_FOUND)
    set(SQLite3_LIBRARIES ${SQLite3_LIBRARY})
    set(SQLite3_INCLUDE_DIRS ${SQLite3_INCLUDE_DIR})
endif()

# Mark cache variables as advanced
mark_as_advanced(
    SQLite3_INCLUDE_DIR
    SQLite3_LIBRARY
)
```

## Search Path Order

CMake searches in this order:

1. Hints from user (`HINTS` option)
2. Package-specific environment variables
3. `CMAKE_PREFIX_PATH`
4. System-specific paths

```cmake
find_library(MyLib_LIBRARY
    NAMES mylib
    HINTS ${MyLib_ROOT}              # 1. User hint
    PATHS
        $ENV{MYLIB_ROOT}             # 2. Environment
        ${CMAKE_PREFIX_PATH}         # 3. CMake prefix path
        /usr/local                   # 4. System paths
        /usr
    PATH_SUFFIXES lib lib64
)
```

**Controlling search:**

```cmake
# Only search in specified paths
find_library(MyLib_LIBRARY
    NAMES mylib
    PATHS /custom/path
    NO_DEFAULT_PATH           # Don't use system paths
)

# Search specified paths first, then system
find_library(MyLib_LIBRARY
    NAMES mylib
    PATHS /custom/path
)
```

## Handling Dependencies

If your library depends on others:

```cmake
# Find dependencies first
find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)

# Find your library
find_library(MyLib_LIBRARY NAMES mylib)

# Create target with dependencies
if(MyLib_FOUND)
    add_library(MyLib::MyLib UNKNOWN IMPORTED)
    set_target_properties(MyLib::MyLib PROPERTIES
        IMPORTED_LOCATION "${MyLib_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${MyLib_INCLUDE_DIR}"
        INTERFACE_LINK_LIBRARIES "ZLIB::ZLIB;Threads::Threads"
    )
endif()
```

## Best Practices

:::success Find Module Guidelines

1. **Always create imported targets** - modern CMake expects them
2. **Use find_package_handle_standard_args()** - handles REQUIRED, QUIET, version checking
3. **Mark cache variables as advanced** - cleaner GUI
4. **Document your module** - use .rst format for help
5. **Support pkg-config** - many libraries provide .pc files
6. **Handle components properly** - use `HANDLE_COMPONENTS`
7. **Set standard variables** - `_FOUND`, `_LIBRARIES`, `_INCLUDE_DIRS`
8. **Check target existence** - `if(NOT TARGET MyLib::MyLib)`
   :::

## Testing Your Find Module

```cmake title="test/CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(FindModuleTest)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/../cmake)

find_package(MyLib REQUIRED)

add_executable(test_find main.cpp)
target_link_libraries(test_find PRIVATE MyLib::MyLib)

# Print what was found
message(STATUS "MyLib_FOUND: ${MyLib_FOUND}")
message(STATUS "MyLib_VERSION: ${MyLib_VERSION}")
message(STATUS "MyLib_INCLUDE_DIRS: ${MyLib_INCLUDE_DIRS}")
message(STATUS "MyLib_LIBRARIES: ${MyLib_LIBRARIES}")
```

## Quick Reference

```cmake
# Find header
find_path(Pkg_INCLUDE_DIR
    NAMES header.h
    PATHS /usr/include /usr/local/include
)

# Find library
find_library(Pkg_LIBRARY
    NAMES pkgname
    PATHS /usr/lib /usr/local/lib
)

# Standard handling
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Pkg
    REQUIRED_VARS Pkg_LIBRARY Pkg_INCLUDE_DIR
    VERSION_VAR Pkg_VERSION
)

# Create imported target
if(Pkg_FOUND AND NOT TARGET Pkg::Pkg)
    add_library(Pkg::Pkg UNKNOWN IMPORTED)
    set_target_properties(Pkg::Pkg PROPERTIES
        IMPORTED_LOCATION "${Pkg_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${Pkg_INCLUDE_DIR}"
    )
endif()

# Set variables
set(Pkg_LIBRARIES ${Pkg_LIBRARY})
set(Pkg_INCLUDE_DIRS ${Pkg_INCLUDE_DIR})

# Hide from GUI
mark_as_advanced(Pkg_INCLUDE_DIR Pkg_LIBRARY)
```

Writing Find modules is necessary for integrating legacy libraries, but for new projects, Config files (via `install(EXPORT)`) are preferred as they're more maintainable and accurate.
