---
id: cmakelists-structure
title: CMakeLists.txt Structure
sidebar_label: CMakeLists Structure
tags: [ c++, cmake ]
---

# CMakeLists.txt Structure

## File Anatomy

A well-structured `CMakeLists.txt` follows a logical order that ensures maintainability and
readability. This structure typically starts with version requirements, project declaration,
compiler settings, and gradually adds dependencies, subdirectories, targets, installation rules, and
testing configuration.

```python title="CMakeLists.txt (Complete Example)"
# 1. Minimum version requirement
cmake_minimum_required(VERSION 3.15)

# 2. Project declaration
project(MyProject 
    VERSION 1.0.0
    DESCRIPTION "A sample project"
    LANGUAGES CXX)

# 3. Project-wide settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 4. Options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

# 5. Dependencies
find_package(Threads REQUIRED)

# 6. Subdirectories (if any)
add_subdirectory(src)
add_subdirectory(external)

# 7. Targets
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Threads::Threads)

# 8. Installation rules
install(TARGETS myapp DESTINATION bin)

# 9. Testing (if enabled)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

## Breaking Down Each Section

### 1. Version Requirement

```python title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
```

:::info Why This Matters

* Ensures CMake features you use are available
* Prevents cryptic errors from older versions
* **3.15+** recommended for modern projects to leverage newer CMake functionality
* Always place this at the very top of your `CMakeLists.txt`
  :::

This sets the baseline for CMake's capabilities and avoids undefined behavior from deprecated or
missing commands.

### 2. Project Declaration

```python title="CMakeLists.txt"
project(MyProject 
    VERSION 1.0.0
    DESCRIPTION "A sample project"
    HOMEPAGE_URL "https://github.com/user/project"
    LANGUAGES CXX C)
```

This section defines your project and automatically sets up useful variables like:

* `PROJECT_NAME` → "MyProject"
* `PROJECT_VERSION` → "2.1.0"
* `PROJECT_VERSION_MAJOR` → "2"
* `PROJECT_VERSION_MINOR` → "1"
* `PROJECT_VERSION_PATCH` → "0"
* `PROJECT_SOURCE_DIR` → Absolute path to the source directory
* `PROJECT_BINARY_DIR` → Absolute path to the build directory

:::success Variables Created
After `project()`, you can reference `${PROJECT_NAME}`, `${PROJECT_VERSION}`,
`${PROJECT_SOURCE_DIR}`, etc., in other parts of your CMake scripts.
:::

**Why this matters:**
Declaring the project at the top centralizes configuration and ensures consistent metadata is
available for all targets, dependencies, and packaging commands.

### 3. Compiler Settings

This section ensures all targets use a consistent C++ standard and compiler options, and optionally
generates `compile_commands.json` for IDEs or code analysis tools.

```python title="CMakeLists.txt"
# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type default
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Export compile commands (for IDEs/tools)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

| Variable                      | Purpose                            |
|-------------------------------|------------------------------------|
| `CMAKE_CXX_STANDARD`          | C++ version (11, 14, 17, 20, 23)   |
| `CMAKE_CXX_STANDARD_REQUIRED` | Fail if standard not available     |
| `CMAKE_CXX_EXTENSIONS`        | Use `-std=c++17` vs `-std=gnu++17` |

### 4. Options

Options allow users to customize the build without editing CMake files. For example, users may
enable/disable tests, documentation, or optional features using `cmake -DOPTION=ON/OFF ..`.

```python title="CMakeLists.txt"
option(BUILD_TESTS "Build the test suite" ON)
option(BUILD_DOCS "Build documentation" OFF)
option(ENABLE_WARNINGS "Enable compiler warnings" ON)
```

This pattern ensures optional features are only included when explicitly enabled:

```python title="CMakeLists.txt"
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

**User can override:**

```bash title="Terminal"
cmake -DBUILD_TESTS=OFF ..
```

### 5. Dependencies

Dependencies are external libraries, frameworks, or system packages your project relies on. Managing
them properly ensures your project builds consistently across different machines and platforms.
CMake provides tools like `find_package()` and `find_library()` to locate and configure dependencies
automatically.

#### Using find_package()

```python title="CMakeLists.txt"
# Mandatory dependency (System libraries)
find_package(Threads REQUIRED)

# Optional dependency with version check
find_package(Boost 1.70 COMPONENTS filesystem system)
if(Boost_FOUND)
    message(STATUS "Boost found: ${Boost_VERSION}")
endif()

# Modern CMake targets
find_package(OpenSSL REQUIRED)
target_link_libraries(myapp PRIVATE OpenSSL::SSL OpenSSL::Crypto)
```

| Feature                   | Description                                                                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQUIRED**              | Stops configuration if the package is not found. Ensures mandatory dependencies are present.                                                                           |
| **Optional**              | Without `REQUIRED`, the build continues even if the library is missing. You can check `${PACKAGE_FOUND}` to conditionally include functionality.                       |
| **Version specification** | Ensures a minimum (or exact) version is available. Example: `find_package(Boost 1.70 REQUIRED)`                                                                        |
| **Components**            | Some packages are modular (like Boost). You can request specific components like `filesystem`, `system`, or `regex`.                                                   |
| **Imported targets**      | Modern CMake provides targets (`Threads::Threads`, `OpenSSL::SSL`) that encapsulate include directories, libraries, and compile options. Avoid manually setting these. |

#### Using find_library() and find_path()

For more manual control, CMake also provides:

```python title="CMakeLists.txt"
# Locate a library file
find_library(MYLIB_PATH mylib PATHS /usr/local/lib /opt/lib)

# Locate an include directory
find_path(MYLIB_INCLUDE mylib.h PATHS /usr/local/include /opt/include)

if(MYLIB_PATH AND MYLIB_INCLUDE)
    message(STATUS "Found mylib at ${MYLIB_PATH}")
endif()
```

These are lower-level commands useful if `find_package()` is not available for a library.

#### Best Practices

:::info

* Prefer `find_package()` with modern imported targets whenever possible.
* Avoid manually adding `include_directories()` or `link_directories()` globally; this can create conflicts.
* Use `REQUIRED` for essential dependencies to **fail early if missing**.
* Use optional dependencies to add features without breaking the core build.
* For external projects, consider using FetchContent or `add_subdirectory()` to include the dependency directly in your build.

:::

```python title="Example: Modern CMake with Dependencies"
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(Boost 1.70 COMPONENTS filesystem system QUIET)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Threads::Threads OpenSSL::SSL OpenSSL::Crypto)

if(Boost_FOUND)
    target_include_directories(myapp PRIVATE ${Boost_INCLUDE_DIRS})
    target_link_libraries(myapp PRIVATE ${Boost_LIBRARIES})
endif()
```

### 6. Subdirectories

The `add_subdirectory()` command allows you to split a large project into smaller, self-contained modules, each with its own `CMakeLists.txt`. This makes it easier to manage complex builds.

```python title="CMakeLists.txt"
add_subdirectory(src)
add_subdirectory(libs)
add_subdirectory(external/fmt)
```

:::info

* Each subdirectory can define its own **targets** (executables or libraries) and **dependencies** independently.
* Build rules and compile options can be localized to a specific module without affecting the rest of the project.
* Dependencies between modules are automatically propagated if targets are linked with `target_link_libraries()`.
* It supports hierarchical project structure, enabling clean organization of source code (`src/`), libraries (`libs/`), and third-party/external dependencies (`external/`).
* Improves maintainability, readability, and scalability, especially for multi-developer projects.

:::

:::tip
The order of `add_subdirectory()` calls matters if targets in later directories depend on targets in earlier ones. Always add libraries before executables that link against them.
:::

**Purpose:**
Organizes large projects by splitting code into directories, each with its own `CMakeLists.txt`.
This improves modularity, readability, and maintainability.

### 7. Targets (Executables/Libraries)

Targets are the **fundamental building blocks** in CMake. They represent the actual outputs of your project: either executables or libraries. Properly defining targets makes your build modular, maintainable, and portable.

```python title="CMakeLists.txt"
# Executable
add_executable(myapp 
    src/main.cpp
    src/utils.cpp
)

# Library
add_library(mylib STATIC
    src/mylib.cpp
    include/mylib.h
)

# Target properties
target_include_directories(myapp PRIVATE include)
target_link_libraries(myapp PRIVATE mylib Threads::Threads)
target_compile_options(myapp PRIVATE -Wall -Wextra)
```

:::info **Executables vs Libraries**:

* `add_executable()` defines a binary that can be run.
* `add_library()` defines a library (`STATIC`, `SHARED`, or `INTERFACE`) that can be linked to other targets.
:::

:::info **Target properties**:

* Using `target_*` commands (`target_include_directories`, `target_link_libraries`, `target_compile_options`, etc.) applies properties **only to that target**, avoiding global side effects and making dependencies explicit.
:::

:::info **Linking dependencies**:

* Link libraries using `target_link_libraries()`.
* Modern CMake prefers linking **targets** (like `mylib` or imported targets such as `Threads::Threads`) rather than raw library paths.
* Target-based linking automatically propagates include directories, compile options, and other necessary settings to dependent targets.
:::

:::info **Include directories**:

* `PRIVATE`: Only for this target.
* `PUBLIC`: For this target and anything linking to it.
* `INTERFACE`: Only for targets linking to this one (used for header-only libraries).
:::

:::info **Compile options**:

* Use `target_compile_options()` instead of global flags like `CMAKE_CXX_FLAGS`.
* Allows different targets to have different warning levels or optimizations.

:::

:::success Benefits of using targets properly

1. **Encapsulation**: Each target defines its own behavior and dependencies.
2. **Portability**: Imported targets and modern CMake practices work seamlessly across platforms.
3. **Scalability**: Adding new libraries or executables is straightforward.
4. **Clarity**: Anyone reading the `CMakeLists.txt` can see exactly which files and libraries are involved in each build artifact.

:::

:::tip
For header-only libraries, define them as `INTERFACE` libraries with `target_include_directories()` rather than adding sources. This keeps the build clean and avoids unnecessary compilation.
:::

### 8. Installation

CMake provides the `install()` command to define how your project’s binaries, libraries, and headers are installed on a system or packaged for distribution. This is especially important if you want users or other projects to use your library or executable without building from source.

```python title="CMakeLists.txt"
# Install executable and libraries
install(TARGETS myapp mylib
    RUNTIME DESTINATION bin       # Executable binaries (Windows/Linux)
    LIBRARY DESTINATION lib       # Shared libraries (.so/.dylib)
    ARCHIVE DESTINATION lib       # Static libraries (.a/.lib)
)

# Install headers
install(DIRECTORY include/ 
    DESTINATION include           # Copy all headers from include/ to the install location
)
```

:::info Key Points

* `TARGETS` specifies which targets (executables or libraries) to install.
* `RUNTIME` is for executables or DLLs.
* `LIBRARY` is for shared libraries (.so on Linux, .dylib on macOS).
* `ARCHIVE` is for static libraries (.a on Linux, .lib on Windows).
* `DIRECTORY` is used to install entire directories, commonly header files, while preserving the folder structure.

:::

You can also install files selectively using `FILES`:

```python title="CMakeLists.txt"
install(FILES README.md LICENSE DESTINATION share/doc/MyProject)
```

Flag `--prefix` specifies the installation root directory:

```bash title="Terminal" title="Terminal"
cmake --install build --prefix /usr/local
```

If no `--prefix` is given, CMake uses the default install directory, which varies by platform.

:::info Advanced Notes

* You can create **component-based installations** to separate binaries, libraries, and documentation.
* `install()` works in combination with `CPack` to generate packages (like `.deb`, `.rpm`, or `.zip`).
* Installing headers and libraries properly ensures other projects can find your library with `find_package()` or `pkg-config`.

:::

### 9. Testing

CMake provides built-in support for testing through **CTest**. By defining test executables and registering them, you can easily run automated tests as part of your build process. This helps catch regressions early and ensures your code behaves as expected.

```python title="CMakeLists.txt"
if(BUILD_TESTS)
    enable_testing()  # Enable CTest functionality

    # Define test executable
    add_executable(test_suite tests/test_main.cpp)

    # Link test executable to library under test
    target_link_libraries(test_suite PRIVATE mylib)

    # Register test with CTest
    add_test(NAME MyLibTests COMMAND test_suite)
endif()
```

:::info Key Points

* `enable_testing()` must be called once to activate CTest support.
* `add_test(NAME <test_name> COMMAND <executable>)` registers a test that can be run with `ctest`.
* Linking the test executable to the library under test ensures it has access to all necessary code.
* Tests can be conditional, depending on `BUILD_TESTS` or other options.

:::

**Run the tests from the command line:**

```bash title="Terminal"
ctest --test-dir build
```

* Flag `--test-dir` points to the build directory containing the compiled test executables.
* You can run all tests, or filter by name using `-R`:

```bash title="Terminal"
ctest --test-dir build -R MyLibTests
```

* Additional options:

  * `ctest -V` → verbose output
  * `ctest -j N` → run tests in parallel

:::success Benefits of using CTest

* Automatically handles multiple test executables and their dependencies.
* Integrates with CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, etc.).
* Provides standardized reporting of test results, including pass/fail status.
* Supports test fixtures, custom commands, and timeout controls for advanced testing.

:::

:::tip
For unit tests, consider frameworks like **Google Test**, **Catch2**, or **doctest**. These can be easily linked to your CMake test targets and used with `add_test()`.
:::

## Common Patterns

### Organizing Source Files

**Pattern 1: List explicitly**

```python title="CMakeLists.txt"
add_executable(myapp
    src/main.cpp
    src/file1.cpp
    src/file2.cpp
)
```

**Pattern 2: Use variables**

```python title="CMakeLists.txt"
set(SOURCES
    src/main.cpp
    src/file1.cpp
    src/file2.cpp
)
add_executable(myapp ${SOURCES})
```

**Pattern 3: Glob (not recommended)**

```python title="CMakeLists.txt"
file(GLOB SOURCES "src/*.cpp")
add_executable(myapp ${SOURCES})
```

:::danger Avoid GLOB
CMake won't detect new files added after initial configuration. Prefer explicit lists.
:::

### Header-Only Libraries

```python title="CMakeLists.txt"
add_library(myheaderlib INTERFACE)
target_include_directories(myheaderlib INTERFACE include)
```

### Conditional Compilation

```python title="CMakeLists.txt"
if(WIN32)
    target_sources(myapp PRIVATE src/windows_specific.cpp)
elseif(UNIX)
    target_sources(myapp PRIVATE src/unix_specific.cpp)
endif()
```

## Multi-File Project Example

```text title="Project tree"
project/
├── CMakeLists.txt          # Root
├── src/
│   ├── CMakeLists.txt      # Builds executable
│   ├── main.cpp
│   └── app.cpp
├── lib/
│   ├── CMakeLists.txt      # Builds library
│   ├── mylib.cpp
│   └── mylib.h
└── tests/
    ├── CMakeLists.txt      # Builds tests
    └── test_mylib.cpp
```

```python title="CMakeLists.txt (Root)"
cmake_minimum_required(VERSION 3.15)
project(MultiFileProject VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)

add_subdirectory(lib)
add_subdirectory(src)

option(BUILD_TESTS "Build tests" ON)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

```python title="lib/CMakeLists.txt"
add_library(mylib STATIC
    mylib.cpp
)

target_include_directories(mylib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)
```

```python title="src/CMakeLists.txt"
add_executable(myapp
    main.cpp
    app.cpp
)

target_link_libraries(myapp PRIVATE mylib)
```

```python title="tests/CMakeLists.txt"
add_executable(test_suite test_mylib.cpp)
target_link_libraries(test_suite PRIVATE mylib)
add_test(NAME MyLibTests COMMAND test_suite)
```

## Best Practices

:::success Do's
✅ Use `target_*` commands (not global `include_directories()`)  
✅ Put `cmake_minimum_required()` first  
✅ Version your project  
✅ Use out-of-source builds  
✅ Set C++ standard with `target_compile_features()`
:::

:::danger Don'ts
❌ Don't use `file(GLOB)` for source files  
❌ Don't set global compiler flags  
❌ Don't use absolute paths  
❌ Don't build in source directory  
❌ Don't use `link_directories()`
:::

## Quick Template

```python title="Minimal Modern CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(ProjectName VERSION 1.0 LANGUAGES CXX)

add_executable(${PROJECT_NAME}
    src/main.cpp
)

target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)
target_include_directories(${PROJECT_NAME} PRIVATE include)

if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4)
else()
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -pedantic)
endif()
```
