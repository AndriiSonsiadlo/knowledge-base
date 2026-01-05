---
id: external-projects
title: ExternalProject Module
sidebar_label: ExternalProject
tags: [c++, cmake, dependencies, externalproject, build-system]
---

# ExternalProject Module

## What is ExternalProject?

ExternalProject is a CMake module that manages the download, configuration, build, and installation of external projects at **build time**, not configure time. This is fundamentally different from FetchContent, which operates during the CMake configuration phase.

The key characteristic of ExternalProject is that it creates custom build targets for external dependencies. When you build your project, these external projects are built as separate CMake invocations, completely isolated from your main build. This isolation is both a strength and a limitation.

ExternalProject is particularly useful for large dependencies, projects that don't use CMake, or when you need complete control over the build process of dependencies.

## When to Use ExternalProject

Understanding when to use ExternalProject versus alternatives is crucial for project architecture decisions.

### Use ExternalProject For

**Non-CMake projects:** Projects using Make, Autotools, Meson, or custom build systems can be integrated through ExternalProject's flexible command system.

**Very large dependencies:** Building Boost, LLVM, or Qt as part of your configure step (via FetchContent) would make configuration prohibitively slow. ExternalProject builds these at build time when you have time to wait.

**Complex build requirements:** When dependencies need special configuration steps, patches, or have unusual build processes that don't fit the standard CMake model.

**Superbuild patterns:** Creating a "superbuild" that orchestrates building all components of a complex system in the correct order with proper dependencies.

**Binary compatibility isolation:** When you need to ensure dependencies are completely separate from your build, perhaps because they use different compiler settings or standards.

### Don't Use ExternalProject For

**Header-only libraries:** FetchContent is simpler and more appropriate since there's no build step.

**Small CMake-based libraries:** FetchContent integrates these more naturally and makes their targets immediately available.

**Dependencies you want to link against directly:** ExternalProject creates separate build trees, making linking more complex. You'll need explicit installation steps and `find_package()` calls.

## Basic Concepts

ExternalProject works in distinct phases that execute sequentially during the build:

1. **Download:** Fetch the source code (git, URL, SVN, etc.)
2. **Update:** Pull latest changes (for git/svn)
3. **Patch:** Apply modifications to source
4. **Configure:** Run CMake/configure script
5. **Build:** Compile the project
6. **Install:** Copy artifacts to installation directory
7. **Test:** Run tests (optional)

Each phase can be customized or disabled based on your needs.

## Basic Usage

### Including the Module

```cmake
include(ExternalProject)
```

### Simple Example

Here's a minimal example building a CMake-based library:

```cmake
include(ExternalProject)

ExternalProject_Add(
    json_external
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
    
    # Installation directory
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
        -DJSON_BuildTests=OFF
)
```

This downloads nlohmann/json at build time and installs it to `${CMAKE_BINARY_DIR}/external`. However, you can't use it directly in your project yet - you need to find it:

```cmake
# After the external project is built, find it
find_package(nlohmann_json REQUIRED
    PATHS ${CMAKE_BINARY_DIR}/external
    NO_DEFAULT_PATH
)

# Now use it
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE nlohmann_json::nlohmann_json)

# Ensure external project builds first
add_dependencies(myapp json_external)
```

## Download Methods

ExternalProject supports multiple ways to obtain source code.

### Git Repository

The most common method for open-source dependencies:

```cmake
ExternalProject_Add(
    fmt_external
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0              # Tag, branch, or commit hash
    GIT_SHALLOW ON             # Shallow clone (faster)
    GIT_PROGRESS ON            # Show progress
    GIT_SUBMODULES ""          # Don't fetch submodules
)
```

**GIT_TAG best practices:**

- Use specific tags or commit hashes for reproducibility
- Avoid branch names like "master" unless you want automatic updates
- Commit hashes are immutable and most secure

**GIT_SHALLOW:** Only clones the specific commit, not entire history. Significantly faster but you can't switch branches/tags later.

**GIT_SUBMODULES:** Empty string disables submodule fetching. Or specify which ones: `GIT_SUBMODULES "path/to/submodule1 path/to/submodule2"`.

### URL Download

Download from a direct URL (tarball, zip file, etc.):

```cmake
ExternalProject_Add(
    boost_external
    URL https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz
    URL_HASH SHA256=121da556b718fd7bd700b5f2e734f8004f1cfa78b7d30145471c526ba75a151c
    
    # URL download is faster than git for releases
)
```

**URL_HASH:** Critical for security and reproducibility. Verifies download integrity. Get the hash from the project's release page or compute it:

```bash
sha256sum boost_1_81_0.tar.gz
```

**When to use URL vs GIT:**

- URL is faster for released versions
- Git allows tracking development branches
- URL has smaller bandwidth requirements
- Git makes it easier to apply patches

### SVN Repository

For projects still using Subversion:

```cmake
ExternalProject_Add(
    legacy_project
    SVN_REPOSITORY http://svn.example.com/project/trunk
    SVN_REVISION 1234
)
```

### Local Directory

Useful for development or vendored dependencies:

```cmake
ExternalProject_Add(
    local_lib
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/local_lib
    
    # Skip download/update steps
    DOWNLOAD_COMMAND ""
    UPDATE_COMMAND ""
)
```

## Configure Step

The configure step sets up the external project's build system.

### CMake Projects

Pass CMake variables to the external project:

```cmake
ExternalProject_Add(
    my_cmake_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    GIT_TAG v1.0.0
    
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
        -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
        -DBUILD_TESTING=OFF
        -DBUILD_EXAMPLES=OFF
        
    # Or use CMAKE_CACHE_ARGS for CACHE variables
    CMAKE_CACHE_ARGS
        -DOPTION_NAME:BOOL=ON
)
```

**CMAKE_ARGS vs CMAKE_CACHE_ARGS:**

- `CMAKE_ARGS`: Regular CMake variables, passed on command line
- `CMAKE_CACHE_ARGS`: Explicitly cached variables with type specification
- Use `CMAKE_ARGS` for most cases, `CMAKE_CACHE_ARGS` when you need exact cache control

**Common variables to forward:**

```cmake
CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
    -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
    -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}
    -DCMAKE_TOOLCHAIN_FILE=${CMAKE_TOOLCHAIN_FILE}
    -DCMAKE_PREFIX_PATH=${CMAKE_PREFIX_PATH}
```

### Non-CMake Projects

For Autotools-based projects (./configure, make, make install):

```cmake
ExternalProject_Add(
    zlib_external
    URL https://www.zlib.net/zlib-1.2.13.tar.gz
    
    # Custom configure command
    CONFIGURE_COMMAND <SOURCE_DIR>/configure
        --prefix=<INSTALL_DIR>
        --static
        
    # Build and install commands
    BUILD_COMMAND make -j8
    INSTALL_COMMAND make install
)
```

**Placeholder expansion:**

- `<SOURCE_DIR>`: Where source was downloaded
- `<BINARY_DIR>`: Build directory
- `<INSTALL_DIR>`: Installation directory
- `<DOWNLOAD_DIR>`: Download directory

For projects with custom build systems:

```cmake
ExternalProject_Add(
    custom_lib
    URL https://example.com/custom_lib.tar.gz
    
    CONFIGURE_COMMAND ""  # No configure step
    
    BUILD_COMMAND python3 <SOURCE_DIR>/build.py
        --output=<BINARY_DIR>
        --optimize
        
    INSTALL_COMMAND python3 <SOURCE_DIR>/install.py
        --prefix=<INSTALL_DIR>
)
```

## Build Step

Control how the external project is built.

### Parallel Builds

```cmake
ExternalProject_Add(
    parallel_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    
    # Use all cores
    BUILD_COMMAND ${CMAKE_COMMAND}
        --build <BINARY_DIR>
        --config $<CONFIG>
        --parallel
)
```

The `--parallel` flag uses all available cores. You can also specify a number: `--parallel 4`.

### Custom Build Commands

```cmake
ExternalProject_Add(
    make_based_lib
    URL https://example.com/lib.tar.gz
    
    CONFIGURE_COMMAND ""
    
    # Custom make command with specific targets
    BUILD_COMMAND make -C <SOURCE_DIR>
        CC=${CMAKE_C_COMPILER}
        CXX=${CMAKE_CXX_COMPILER}
        lib
        tools
        
    BUILD_IN_SOURCE ON  # Build in source directory
)
```

**BUILD_IN_SOURCE:** Some older projects require in-source builds. Use this flag, but prefer out-of-source builds when possible.

## Install Step

Control where and how artifacts are installed.

### Standard Installation

```cmake
ExternalProject_Add(
    installed_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
        
    # Default install command works for most CMake projects
    # INSTALL_COMMAND ${CMAKE_COMMAND}
    #     --build <BINARY_DIR>
    #     --target install
)
```

### Custom Installation

```cmake
ExternalProject_Add(
    custom_install
    URL https://example.com/lib.tar.gz
    
    # Manually copy files
    INSTALL_COMMAND
        ${CMAKE_COMMAND} -E copy_directory
        <SOURCE_DIR>/include
        <INSTALL_DIR>/include
    COMMAND
        ${CMAKE_COMMAND} -E copy
        <BINARY_DIR>/libmylib.a
        <INSTALL_DIR>/lib/libmylib.a
)
```

### Skipping Installation

Sometimes you just want to build, not install:

```cmake
ExternalProject_Add(
    no_install
    GIT_REPOSITORY https://github.com/example/lib.git
    
    INSTALL_COMMAND ""  # Skip install step
)

# Access build artifacts directly
ExternalProject_Get_Property(no_install BINARY_DIR)
include_directories(${BINARY_DIR}/include)
link_directories(${BINARY_DIR}/lib)
```

## Patch Step

Apply modifications to external projects.

### Patch Files

```cmake
ExternalProject_Add(
    patched_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    GIT_TAG v1.0.0
    
    # Apply patch after download
    PATCH_COMMAND patch -p1 < ${CMAKE_SOURCE_DIR}/patches/fix_bug.patch
)
```

Create the patch file:

```bash
cd external_lib
git diff > ../patches/fix_bug.patch
```

### Multiple Patches

```cmake
ExternalProject_Add(
    multi_patch
    URL https://example.com/lib.tar.gz
    
    PATCH_COMMAND
        patch -p1 < ${CMAKE_SOURCE_DIR}/patches/patch1.patch
    COMMAND
        patch -p1 < ${CMAKE_SOURCE_DIR}/patches/patch2.patch
    COMMAND
        sed -i 's/old/new/g' <SOURCE_DIR>/config.h
)
```

### Script-Based Patching

For complex modifications:

```cmake
ExternalProject_Add(
    script_patched
    GIT_REPOSITORY https://github.com/example/lib.git
    
    PATCH_COMMAND ${CMAKE_COMMAND}
        -P ${CMAKE_SOURCE_DIR}/cmake/patch_lib.cmake
)
```

```cmake title="cmake/patch_lib.cmake"
file(READ "${SOURCE_DIR}/config.h" content)
string(REPLACE "old_value" "new_value" content "${content}")
file(WRITE "${SOURCE_DIR}/config.h" "${content}")
```

## Dependencies Between External Projects

Control build order when external projects depend on each other.

```cmake
ExternalProject_Add(
    dependency_base
    GIT_REPOSITORY https://github.com/example/base.git
)

ExternalProject_Add(
    dependency_user
    GIT_REPOSITORY https://github.com/example/user.git
    
    # Wait for base to be installed
    DEPENDS dependency_base
    
    # Use base in configuration
    CMAKE_ARGS
        -DCMAKE_PREFIX_PATH=${CMAKE_BINARY_DIR}/external
)

# Internal targets that need external projects
add_executable(myapp main.cpp)
add_dependencies(myapp dependency_user)
```

The `DEPENDS` keyword ensures proper build order. The external project won't start until its dependencies are complete.

## Using External Projects

After building external projects, you need to link against them.

### Via find_package()

The recommended approach:

```cmake
# Define external project
ExternalProject_Add(
    fmt_external
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 9.1.0
    
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
        -DFMT_INSTALL=ON
)

# Find it (won't work during configure, only at build time)
# So we need a workaround...

# Option 1: Use imported targets directly
add_library(fmt::fmt STATIC IMPORTED)
set_target_properties(fmt::fmt PROPERTIES
    IMPORTED_LOCATION ${CMAKE_BINARY_DIR}/external/lib/libfmt.a
    INTERFACE_INCLUDE_DIRECTORIES ${CMAKE_BINARY_DIR}/external/include
)

# Use it
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE fmt::fmt)
add_dependencies(myapp fmt_external)
```

### Via Manual Linking

```cmake
ExternalProject_Add(
    mylib_external
    # ... configuration ...
    CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
)

# Get properties
ExternalProject_Get_Property(mylib_external INSTALL_DIR)

# Include and link
include_directories(${INSTALL_DIR}/include)
link_directories(${INSTALL_DIR}/lib)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE mylib)
add_dependencies(myapp mylib_external)
```

## Superbuild Pattern

A "superbuild" is a CMake project that orchestrates building all components as external projects.

### Structure

```
superbuild/
├── CMakeLists.txt           # Superbuild
├── cmake/
│   ├── External_ProjectA.cmake
│   ├── External_ProjectB.cmake
│   └── External_MyApp.cmake
└── src/                     # Your actual project
    └── CMakeLists.txt
```

### Implementation

```cmake title="CMakeLists.txt (Superbuild)"
cmake_minimum_required(VERSION 3.14)
project(SuperBuild NONE)

include(ExternalProject)

# Installation directory for all components
set(INSTALL_DIR ${CMAKE_BINARY_DIR}/install)

# Build dependencies first
include(cmake/External_ProjectA.cmake)
include(cmake/External_ProjectB.cmake)

# Build main project last
include(cmake/External_MyApp.cmake)
```

```cmake title="cmake/External_ProjectA.cmake"
ExternalProject_Add(
    ProjectA
    GIT_REPOSITORY https://github.com/example/ProjectA.git
    GIT_TAG v1.0.0
    
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR}
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
)
```

```cmake title="cmake/External_MyApp.cmake"
ExternalProject_Add(
    MyApp
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/src
    
    CMAKE_ARGS
        -DCMAKE_PREFIX_PATH=${INSTALL_DIR}
        -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR}
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
        
    DEPENDS ProjectA ProjectB
    
    # Don't install MyApp (it's the main project)
    INSTALL_COMMAND ""
)
```

This pattern is excellent for complex projects with many dependencies and components. Each piece is built in isolation with clear dependency chains.

## Advanced Features

### Logging

Control output from external projects:

```cmake
ExternalProject_Add(
    quiet_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    
    # Redirect output to files
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    LOG_INSTALL ON
    
    # Output goes to: ${CMAKE_BINARY_DIR}/quiet_lib-prefix/src/quiet_lib-stamp/
)
```

This keeps your build output clean while preserving logs for debugging.

### Step Targets

Create individual targets for each step:

```cmake
ExternalProject_Add(
    stepped_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    
    STEP_TARGETS download update configure build install
)

# Now you can build individual steps:
# cmake --build . --target stepped_lib-download
# cmake --build . --target stepped_lib-configure
# cmake --build . --target stepped_lib-build
```

Useful for debugging or manual intervention between steps.

### Timestamp Checking

Control when steps re-execute:

```cmake
ExternalProject_Add(
    cached_lib
    URL https://example.com/lib.tar.gz
    
    # Don't re-download if file exists
    DOWNLOAD_NO_EXTRACT OFF
    
    # Only rebuild if source changes
    UPDATE_DISCONNECTED ON
)
```

**UPDATE_DISCONNECTED:** Skips the update step after initial download. Useful for released versions that won't change.

### Exclude from All

Don't build by default:

```cmake
ExternalProject_Add(
    optional_lib
    GIT_REPOSITORY https://github.com/example/lib.git
    
    EXCLUDE_FROM_ALL ON
)

# Build explicitly: cmake --build . --target optional_lib
```

## Complete Real-World Example

Building Boost (a complex, large dependency):

```cmake
cmake_minimum_required(VERSION 3.14)
project(BoostExample)

include(ExternalProject)

set(BOOST_VERSION 1.81.0)
set(BOOST_VERSION_UNDERSCORE 1_81_0)

# Determine platform-specific options
if(WIN32)
    set(BOOST_BOOTSTRAP_COMMAND bootstrap.bat)
    set(BOOST_BUILD_COMMAND b2.exe)
else()
    set(BOOST_BOOTSTRAP_COMMAND ./bootstrap.sh)
    set(BOOST_BUILD_COMMAND ./b2)
endif()

ExternalProject_Add(
    boost
    URL https://boostorg.jfrog.io/artifactory/main/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz
    URL_HASH SHA256=121da556b718fd7bd700b5f2e734f8004f1cfa78b7d30145471c526ba75a151c
    
    # Boost uses its own build system (b2)
    CONFIGURE_COMMAND ${BOOST_BOOTSTRAP_COMMAND}
        --prefix=<INSTALL_DIR>
        --with-libraries=filesystem,system,thread
        
    BUILD_COMMAND ${BOOST_BUILD_COMMAND}
        --prefix=<INSTALL_DIR>
        variant=release
        link=static
        threading=multi
        -j8
        
    BUILD_IN_SOURCE ON
    
    INSTALL_COMMAND ${BOOST_BUILD_COMMAND}
        --prefix=<INSTALL_DIR>
        variant=release
        link=static
        threading=multi
        install
        
    # Quiet the output
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    LOG_INSTALL ON
)

# Get installation directory
ExternalProject_Get_Property(boost INSTALL_DIR)

# Create imported targets
add_library(Boost::filesystem STATIC IMPORTED)
set_target_properties(Boost::filesystem PROPERTIES
    IMPORTED_LOCATION ${INSTALL_DIR}/lib/libboost_filesystem.a
    INTERFACE_INCLUDE_DIRECTORIES ${INSTALL_DIR}/include
)

add_library(Boost::system STATIC IMPORTED)
set_target_properties(Boost::system PROPERTIES
    IMPORTED_LOCATION ${INSTALL_DIR}/lib/libboost_system.a
    INTERFACE_INCLUDE_DIRECTORIES ${INSTALL_DIR}/include
)

# Your application
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE
    Boost::filesystem
    Boost::system
)
add_dependencies(myapp boost)
```

## Best Practices

:::success Recommendations

1. **Use specific versions**
    - Tags or commit hashes, not branch names
    - Ensures reproducible builds

2. **Forward compiler settings**

   ```cmake
   CMAKE_ARGS
       -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
       -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
   ```

3. **Disable unnecessary components**

   ```cmake
   CMAKE_ARGS
       -DBUILD_TESTING=OFF
       -DBUILD_EXAMPLES=OFF
       -DBUILD_DOCS=OFF
   ```

4. **Use logging for quiet builds**

   ```cmake
   LOG_DOWNLOAD ON
   LOG_BUILD ON
   ```

5. **Set installation prefix consistently**

   ```cmake
   CMAKE_ARGS
       -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
   ```

6. **Verify downloads**

   ```cmake
   URL_HASH SHA256=...
   ```

7. **Cache downloads between clean builds**
    - Use `DOWNLOAD_DIR` to persist downloads
    - Don't put in `CMAKE_BINARY_DIR` if you clean it
      :::

## ExternalProject vs FetchContent

| Aspect | ExternalProject | FetchContent |
|--------|-----------------|--------------|
| **When** | Build time | Configure time |
| **Integration** | Separate build | Same build |
| **Targets** | Manual import | Automatic |
| **Best for** | Large deps | Small deps |
| **CMake version** | 2.8+ | 3.11+ |
| **Build speed** | Slower (isolated) | Faster (integrated) |
| **Complexity** | Higher | Lower |
| **Use when** | Non-CMake, huge projects | CMake-based, small libs |

## Quick Reference

```cmake
include(ExternalProject)

# Basic CMake project
ExternalProject_Add(
    name
    GIT_REPOSITORY url
    GIT_TAG version
    CMAKE_ARGS
        -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
)

# Non-CMake project
ExternalProject_Add(
    name
    URL archive_url
    URL_HASH SHA256=hash
    CONFIGURE_COMMAND ./configure --prefix=<INSTALL_DIR>
    BUILD_COMMAND make -j8
    INSTALL_COMMAND make install
)

# Using the external project
ExternalProject_Get_Property(name INSTALL_DIR)
include_directories(${INSTALL_DIR}/include)
link_directories(${INSTALL_DIR}/lib)

add_executable(app main.cpp)
target_link_libraries(app library_name)
add_dependencies(app name)
```

:::info When to Choose ExternalProject

**Perfect for:**

- Large dependencies (Boost, Qt, LLVM)
- Non-CMake build systems
- Complex superbuild scenarios
- When you need total build isolation

**Avoid for:**

- Small CMake libraries (use FetchContent)
- Header-only libraries (use FetchContent)
- When you want immediate target availability
  :::
