---
id: generator-expressions
title: Generator Expressions
sidebar_label: Generator Expressions
tags: [cmake, generator-expressions, conditional, advanced]
---

# Generator Expressions

## What Are Generator Expressions?

Generator expressions are evaluated **during build system generation**, not during CMake configuration. They allow you to create conditional logic that depends on information only available at generation time, like build configuration (Debug/Release) or target properties.

The syntax uses `$<...>` and looks unusual, but it's powerful for expressing complex build logic without verbose if-statements.

**Why they exist:** Some information isn't known during configuration. For example, with multi-config generators (Visual Studio, Xcode), the build type isn't determined until you actually build. Generator expressions let you handle this elegantly.

## Basic Syntax

```cmake
$<CONDITION:value_if_true>
$<IF:condition,value_if_true,value_if_false>
```

**Key point:** Generator expressions evaluate to strings. They don't execute code - they produce text that becomes part of your build system.

## Common Use Cases

### Configuration-Specific Settings

Different flags for Debug vs Release:

```cmake
add_executable(myapp main.cpp)

target_compile_definitions(myapp PRIVATE
    $<$<CONFIG:Debug>:DEBUG_MODE>
    $<$<CONFIG:Release>:RELEASE_MODE>
)
```

This expands to:

- Debug build: `-DDEBUG_MODE`
- Release build: `-DRELEASE_MODE`

Traditional approach (more verbose):

```cmake
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(myapp PRIVATE DEBUG_MODE)
else()
    target_compile_definitions(myapp PRIVATE RELEASE_MODE)
endif()
```

But this fails with multi-config generators! Generator expressions handle both cases.

### Compiler-Specific Flags

```cmake
target_compile_options(myapp PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
    $<$<CXX_COMPILER_ID:GNU>:-Wall>
    $<$<CXX_COMPILER_ID:Clang>:-Wall>
)
```

**Cleaner with matches:**

```cmake
target_compile_options(myapp PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
    $<$<OR:$<CXX_COMPILER_ID:GNU>,$<CXX_COMPILER_ID:Clang>>:-Wall>
)
```

### Platform-Specific Settings

```cmake
target_compile_definitions(myapp PRIVATE
    $<$<PLATFORM_ID:Windows>:WINDOWS_BUILD>
    $<$<PLATFORM_ID:Linux>:LINUX_BUILD>
    $<$<PLATFORM_ID:Darwin>:MACOS_BUILD>
)
```

## Conditional Expressions

### Basic Conditions

```cmake
# Simple boolean
$<BOOL:value>           # 1 if value is true-like, 0 otherwise

# Equality
$<STREQUAL:str1,str2>   # 1 if strings equal, 0 otherwise
$<EQUAL:num1,num2>      # 1 if numbers equal, 0 otherwise

# String matching
$<IN_LIST:item,list>    # 1 if item in list
```

### Logical Operators

```cmake
# AND - all must be true
$<AND:cond1,cond2,...>

# OR - at least one true
$<OR:cond1,cond2,...>

# NOT - invert condition
$<NOT:condition>
```

**Example combining conditions:**

```cmake
target_compile_options(myapp PRIVATE
    # Warnings only in Debug with GCC or Clang
    $<$<AND:$<CONFIG:Debug>,$<OR:$<CXX_COMPILER_ID:GNU>,$<CXX_COMPILER_ID:Clang>>>:-Wall>
)
```

This reads: "If (Debug AND (GCC OR Clang)), add -Wall"

### String Operations

```cmake
# Concatenation
$<JOIN:list,separator>              # Join list with separator

# Conditionals with strings
$<IF:condition,true_string,false_string>

# Lowercase/uppercase
$<LOWER_CASE:string>
$<UPPER_CASE:string>
```

**Example:**

```cmake
set(MY_LIST "a;b;c")
target_compile_definitions(myapp PRIVATE
    "ITEMS=$<JOIN:${MY_LIST},->"  # Expands to: ITEMS=a->b->c
)
```

## Target Expressions

Access target properties in generator expressions:

```cmake
# Target property
$<TARGET_PROPERTY:target,property>

# Check if target exists
$<TARGET_EXISTS:target>

# Get target file
$<TARGET_FILE:target>              # Full path to target file
$<TARGET_FILE_NAME:target>         # Just filename
$<TARGET_FILE_DIR:target>          # Directory containing target
```

### Practical Examples

Get library output location:

```cmake
add_library(mylib SHARED mylib.cpp)

add_custom_command(TARGET mylib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:mylib>
        ${CMAKE_BINARY_DIR}/dist/
)
```

This copies `mylib` to `dist/` after building, and it works for any platform/configuration.

### Target Property Queries

```cmake
# Include directories from another target
target_include_directories(myapp PRIVATE
    $<TARGET_PROPERTY:mylib,INTERFACE_INCLUDE_DIRECTORIES>
)
```

**Check target type:**

```cmake
$<TARGET_PROPERTY:mylib,TYPE>  # STATIC_LIBRARY, SHARED_LIBRARY, etc.
```

## Build Interface vs Install Interface

Critical for libraries that are both used in-source and installed:

```cmake
target_include_directories(mylib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
```

**What this means:**

- During build: include from source tree `${CMAKE_CURRENT_SOURCE_DIR}/include`
- After install: include from install location `include/`

Without this distinction, installed libraries would reference non-existent source directories.

### Complete Example

```cmake
add_library(mylib
    src/mylib.cpp
)

add_library(MyProject::mylib ALIAS mylib)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
)

target_compile_definitions(mylib PUBLIC
    $<BUILD_INTERFACE:MYLIB_BUILDING>
    $<INSTALL_INTERFACE:MYLIB_USING>
)
```

## Config Expressions

These evaluate based on build configuration:

```cmake
$<CONFIG:cfg>                    # True if current config matches
$<CONFIG>                        # Current config name

# Multi-config aware
target_compile_options(myapp PRIVATE
    $<$<CONFIG:Debug>:-g3>
    $<$<CONFIG:Release>:-O3>
    $<$<CONFIG:RelWithDebInfo>:-O2 -g>
)
```

**Configuration comparisons:**

```cmake
# Is this a debug build?
$<OR:$<CONFIG:Debug>,$<CONFIG:RelWithDebInfo>>

# Optimization enabled?
$<NOT:$<CONFIG:Debug>>
```

## Practical Patterns

### Per-Configuration Output Names

```cmake
add_executable(myapp main.cpp)

set_target_properties(myapp PROPERTIES
    OUTPUT_NAME myapp$<$<CONFIG:Debug>:_debug>
)
```

Creates:

- Debug: `myapp_debug`
- Release: `myapp`

### Conditional Linking

```cmake
target_link_libraries(myapp PRIVATE
    mylib
    $<$<PLATFORM_ID:Windows>:ws2_32>
    $<$<PLATFORM_ID:Linux>:pthread>
)
```

Only links platform-specific libraries on relevant platforms.

### Version-Based Logic

```cmake
# Check CMake version
$<VERSION_GREATER:version1,version2>
$<VERSION_LESS:version1,version2>
$<VERSION_EQUAL:version1,version2>

# Example: feature requires CMake 3.20+
target_compile_definitions(myapp PRIVATE
    $<$<VERSION_GREATER_EQUAL:${CMAKE_VERSION},3.20>:HAS_NEW_FEATURE>
)
```

### Optimization Flags

```cmake
target_compile_options(myapp PRIVATE
    # Disable optimizations in Debug
    $<$<CONFIG:Debug>:-O0>
    
    # Maximum optimization in Release
    $<$<CONFIG:Release>:-O3>
    
    # Balanced optimization in RelWithDebInfo
    $<$<CONFIG:RelWithDebInfo>:-O2>
)
```

## Advanced Patterns

### Nested Expressions

Generator expressions can be nested:

```cmake
target_compile_options(myapp PRIVATE
    # If (Release OR RelWithDebInfo) AND (GCC OR Clang), enable LTO
    $<$<AND:$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>,$<OR:$<CXX_COMPILER_ID:GNU>,$<CXX_COMPILER_ID:Clang>>>:-flto>
)
```

**Readability tip:** Break complex expressions into variables:

```cmake
set(IS_OPTIMIZED_BUILD $<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>)
set(IS_GCC_OR_CLANG $<OR:$<CXX_COMPILER_ID:GNU>,$<CXX_COMPILER_ID:Clang>>)

target_compile_options(myapp PRIVATE
    $<$<AND:${IS_OPTIMIZED_BUILD},${IS_GCC_OR_CLANG}>:-flto>
)
```

### Custom Properties

Use with custom target properties:

```cmake
define_property(TARGET PROPERTY MY_CUSTOM_FLAG
    BRIEF_DOCS "Custom flag"
)

set_target_properties(mylib PROPERTIES MY_CUSTOM_FLAG "custom_value")

# Use in another target
target_compile_definitions(myapp PRIVATE
    "FLAG=$<TARGET_PROPERTY:mylib,MY_CUSTOM_FLAG>"
)
```

### Installation Expressions

```cmake
install(FILES
    $<$<CONFIG:Debug>:debug_config.ini>
    $<$<CONFIG:Release>:release_config.ini>
    DESTINATION config
)
```

Only installs the config file relevant to the build type.

## Debugging Generator Expressions

Generator expressions can be hard to debug since they're evaluated late. Use `file(GENERATE)` to see results:

```cmake
set(EXPR $<$<CONFIG:Debug>:DEBUG_FLAG>)

file(GENERATE OUTPUT ${CMAKE_BINARY_DIR}/genex_debug.txt
    CONTENT "Expression result: ${EXPR}\n"
)
```

After generation, check `genex_debug.txt` to see the evaluated result.

**Alternative - print during generation:**

```cmake
add_custom_target(show_genex ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Config: $<CONFIG>"
    VERBATIM
)
```

## Common Mistakes

:::warning Pitfalls

**❌ Using in set() commands**

```cmake
# Doesn't work - evaluated too late
set(MY_VAR $<CONFIG>)
message(STATUS "${MY_VAR}")  # Prints the genex, not value
```

**❌ Using in if() statements**

```cmake
# Doesn't work
if($<CONFIG:Debug>)  # if() evaluates during configure
    # ...
endif()
```

**✅ Correct usage - in target commands:**

```cmake
target_compile_definitions(myapp PRIVATE
    $<$<CONFIG:Debug>:DEBUG_MODE>
)
```

:::

## When to Use Generator Expressions

**Use generator expressions for:**

- Multi-configuration generators (Visual Studio, Xcode)
- Compiler/platform-specific settings
- Build vs install differences
- Target-specific conditional logic
- Avoiding verbose if-statements

**Don't use generator expressions for:**

- Simple configure-time decisions
- Variables needed during configuration
- Logic in if() conditions
- Setting cache variables

**Example of when NOT to use:**

```cmake
# ❌ Over-complicated
set(SOURCES 
    main.cpp
    $<$<PLATFORM_ID:Windows>:windows.cpp>
    $<$<PLATFORM_ID:Linux>:linux.cpp>
)

# ✅ Simpler and clearer
if(WIN32)
    set(SOURCES main.cpp windows.cpp)
elseif(UNIX)
    set(SOURCES main.cpp linux.cpp)
endif()
```

## Quick Reference

```cmake
# Conditionals
$<condition:value_if_true>
$<IF:cond,true,false>

# Logical
$<AND:cond1,cond2>
$<OR:cond1,cond2>
$<NOT:condition>

# Comparisons
$<BOOL:value>
$<STREQUAL:a,b>
$<CONFIG:Debug>
$<PLATFORM_ID:Windows>
$<CXX_COMPILER_ID:GNU>

# Target properties
$<TARGET_PROPERTY:target,prop>
$<TARGET_FILE:target>
$<TARGET_EXISTS:target>

# Build/Install
$<BUILD_INTERFACE:value>
$<INSTALL_INTERFACE:value>

# String operations
$<JOIN:list,sep>
$<LOWER_CASE:string>
```

Generator expressions are powerful but should be used judiciously. They shine for configuration-dependent logic and multi-config builds, but simple if-statements are often clearer for basic cases.
