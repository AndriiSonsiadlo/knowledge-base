---
id: functions-and-macros
title: Functions and Macros
sidebar_label: Functions & Macros
sidebar_position: 2
tags: [cmake, functions, macros, reusability, scripting]
---

# Functions and Macros

## Overview

Functions and macros allow you to create reusable CMake code, reducing duplication and improving maintainability. While they appear similar, they have important differences in how they handle variable scope.

## Functions

Functions create a new scope for variables. Changes to variables inside the function don't affect the calling scope unless explicitly requested.

### Basic Syntax

```cmake showLineNumbers 
function(function_name arg1 arg2)
    # Function body
    # Variables set here are local
endfunction()

# Call it
function_name(value1 value2)
```

### Simple Example

```cmake showLineNumbers 
function(print_message msg)
    message(STATUS "Message: ${msg}")
endfunction()

print_message("Hello, CMake!")
# Output: -- Message: Hello, CMake!
```

### Arguments

Functions automatically get these variables:

- `${ARGC}`: Argument count
- `${ARGV}`: All arguments as a list
- `${ARGN}`: Arguments beyond named ones
- `${ARG0}`, `${ARG1}`, etc.: Individual arguments

```cmake showLineNumbers 
function(show_args first second)
    message(STATUS "first: ${first}")
    message(STATUS "second: ${second}")
    message(STATUS "ARGC: ${ARGC}")
    message(STATUS "ARGV: ${ARGV}")
    message(STATUS "ARGN: ${ARGN}")
endfunction()

show_args(a b c d e)
# Output:
# first: a
# second: b
# ARGC: 5
# ARGV: a;b;c;d;e
# ARGN: c;d;e
```

**ARGN is useful for variadic functions:**

```cmake showLineNumbers 
function(add_my_executable name)
    add_executable(${name} ${ARGN})
    target_compile_features(${name} PRIVATE cxx_std_17)
endfunction()

add_my_executable(myapp main.cpp utils.cpp config.cpp)
# Creates executable with all source files
```

### Return Values

Functions don't have explicit return values. Use `set(... PARENT_SCOPE)` to return data:

```cmake showLineNumbers 
function(compute_value result_var)
    set(computed "some_value")
    set(${result_var} ${computed} PARENT_SCOPE)
endfunction()

compute_value(my_result)
message(STATUS "Result: ${my_result}")  # Result: some_value
```

**Important:** Setting PARENT_SCOPE doesn't set the variable in the function's scope:

```cmake showLineNumbers 
function(example)
    set(VAR "value" PARENT_SCOPE)
    message(STATUS "In function: ${VAR}")  # Empty!
endfunction()

example()
message(STATUS "In parent: ${VAR}")  # value
```

To set both:

```cmake showLineNumbers 
function(example)
    set(VAR "value" PARENT_SCOPE)
    set(VAR "value")  # Also set locally
endfunction()
```

## Macros

Macros are like text substitution - they don't create a new scope. Variables set in a macro affect the calling scope.

### Basic Syntax

```cmake showLineNumbers 
macro(macro_name arg1 arg2)
    # Macro body
    # Variables set here affect caller
endmacro()

macro_name(value1 value2)
```

### Function vs Macro

Key difference illustrated:

```cmake showLineNumbers 
function(my_function)
    set(RESULT "from function")
endfunction()

macro(my_macro)
    set(RESULT "from macro")
endmacro()

my_function()
message(STATUS "${RESULT}")  # Empty - function scope isolated

my_macro()
message(STATUS "${RESULT}")  # from macro - macro modifies caller
```

### When to Use Macros

Use macros when you need to:

- Modify variables in the calling scope
- Create control flow (loops, conditionals)
- Want simple text substitution

**Most common use - control flow wrappers:**

```cmake showLineNumbers 
macro(require_package package)
    find_package(${package} REQUIRED)
    if(NOT ${package}_FOUND)
        message(FATAL_ERROR "${package} is required but not found")
    endif()
endmacro()
```

## Argument Parsing

For complex functions with optional and named arguments, use `cmake_parse_arguments()`:

```cmake showLineNumbers 
function(create_test)
    cmake_parse_arguments(
        TEST                          # Prefix for output variables
        "WILL_FAIL"                   # Options (boolean flags)
        "NAME;TIMEOUT"                # Single-value keywords
        "SOURCES;LIBRARIES"           # Multi-value keywords
        ${ARGN}                       # Arguments to parse
    )
    
    if(NOT TEST_NAME)
        message(FATAL_ERROR "NAME is required")
    endif()
    
    add_executable(${TEST_NAME} ${TEST_SOURCES})
    target_link_libraries(${TEST_NAME} PRIVATE ${TEST_LIBRARIES})
    
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
    
    if(TEST_WILL_FAIL)
        set_tests_properties(${TEST_NAME} PROPERTIES WILL_FAIL TRUE)
    endif()
    
    if(TEST_TIMEOUT)
        set_tests_properties(${TEST_NAME} PROPERTIES TIMEOUT ${TEST_TIMEOUT})
    endif()
endfunction()

# Usage
create_test(
    NAME test_math
    SOURCES test_math.cpp
    LIBRARIES mylib
    TIMEOUT 30
    WILL_FAIL
)
```

After parsing:

- `TEST_NAME` = "test_math"
- `TEST_SOURCES` = "test_math.cpp"
- `TEST_LIBRARIES` = "mylib"
- `TEST_TIMEOUT` = "30"
- `TEST_WILL_FAIL` = TRUE

## Practical Examples

### Compiler Warnings

```cmake showLineNumbers 
function(target_set_warnings target_name)
    if(MSVC)
        target_compile_options(${target_name} PRIVATE
            /W4           # Warning level 4
            /WX           # Warnings as errors
        )
    else()
        target_compile_options(${target_name} PRIVATE
            -Wall
            -Wextra
            -Wpedantic
            -Werror
        )
    endif()
endfunction()

# Use it
add_executable(myapp main.cpp)
target_set_warnings(myapp)
```

### Library Creator

```cmake showLineNumbers 
function(add_project_library name)
    cmake_parse_arguments(
        LIB
        "INTERFACE"
        "TYPE"
        "SOURCES;PUBLIC_HEADERS;PRIVATE_HEADERS;DEPENDENCIES"
        ${ARGN}
    )
    
    # Determine library type
    if(LIB_INTERFACE)
        set(lib_type INTERFACE)
    elseif(LIB_TYPE)
        set(lib_type ${LIB_TYPE})
    else()
        set(lib_type STATIC)
    endif()
    
    # Create library
    add_library(${name} ${lib_type} ${LIB_SOURCES})
    add_library(MyProject::${name} ALIAS ${name})
    
    # Setup includes
    if(NOT LIB_INTERFACE)
        target_include_directories(${name}
            PUBLIC
                $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
                $<INSTALL_INTERFACE:include>
            PRIVATE
                ${CMAKE_CURRENT_SOURCE_DIR}/src
        )
    else()
        target_include_directories(${name} INTERFACE
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
        )
    endif()
    
    # Link dependencies
    if(LIB_DEPENDENCIES)
        target_link_libraries(${name} PUBLIC ${LIB_DEPENDENCIES})
    endif()
    
    # C++17 requirement
    target_compile_features(${name} PUBLIC cxx_std_17)
endfunction()

# Usage
add_project_library(mylib
    TYPE STATIC
    SOURCES
        src/impl.cpp
        src/utils.cpp
    DEPENDENCIES
        MyProject::core
        fmt::fmt
)
```

### Executable with Standard Setup

```cmake showLineNumbers 
function(add_project_executable name)
    cmake_parse_arguments(
        EXE
        ""
        ""
        "SOURCES;LIBRARIES"
        ${ARGN}
    )
    
    add_executable(${name} ${EXE_SOURCES})
    
    target_link_libraries(${name} PRIVATE ${EXE_LIBRARIES})
    
    target_compile_features(${name} PRIVATE cxx_std_17)
    
    # Standard warnings
    target_set_warnings(${name})
    
    # Standard output directory
    set_target_properties(${name} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )
endfunction()

# Usage
add_project_executable(myapp
    SOURCES main.cpp app.cpp
    LIBRARIES MyProject::core MyProject::ui
)
```

### Install Helper

```cmake showLineNumbers 
function(install_project_library target)
    install(TARGETS ${target}
        EXPORT MyProjectTargets
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin
        INCLUDES DESTINATION include
    )
    
    # Install headers
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/include)
        install(DIRECTORY include/
            DESTINATION include
        )
    endif()
endfunction()

# Usage
install_project_library(mylib)
```

## Variable Scope Comparison

Understanding scope differences:

```cmake showLineNumbers 
set(GLOBAL_VAR "global")

function(test_function)
    set(FUNC_VAR "function local")
    set(GLOBAL_VAR "modified in function")
    message(STATUS "In function: ${GLOBAL_VAR}")
endfunction()

macro(test_macro)
    set(MACRO_VAR "macro local")
    set(GLOBAL_VAR "modified in macro")
    message(STATUS "In macro: ${GLOBAL_VAR}")
endmacro()

test_function()
message(STATUS "After function: ${GLOBAL_VAR}")  # Still "global"
message(STATUS "FUNC_VAR: ${FUNC_VAR}")          # Empty

test_macro()
message(STATUS "After macro: ${GLOBAL_VAR}")     # "modified in macro"
message(STATUS "MACRO_VAR: ${MACRO_VAR}")        # "macro local"
```

## Control Flow in Macros

Macros can use flow control that affects the caller:

```cmake showLineNumbers 
macro(early_return)
    if(SOME_CONDITION)
        return()  # Returns from caller, not just macro!
    endif()
endmacro()
```

**This is dangerous and usually unintended.** Functions don't have this problem:

```cmake showLineNumbers 
function(safe_early_return)
    if(SOME_CONDITION)
        return()  # Returns from function only
    endif()
endfunction()
```

## Organizing Functions

Create a utilities file:

```cmake showLineNumbers  title="cmake/ProjectUtils.cmake"
function(target_set_warnings target)
    # ... implementation
endfunction()

function(add_project_library name)
    # ... implementation
endfunction()

function(add_project_executable name)
    # ... implementation
endfunction()
```

Include in root CMakeLists.txt:

```cmake showLineNumbers 
list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)
include(ProjectUtils)

# Now functions are available
add_project_library(mylib SOURCES src/lib.cpp)
```

## Advanced Patterns

### Function Returning Multiple Values

```cmake showLineNumbers 
function(get_version major minor patch)
    set(${major} 1 PARENT_SCOPE)
    set(${minor} 2 PARENT_SCOPE)
    set(${patch} 3 PARENT_SCOPE)
endfunction()

get_version(MAJ MIN PAT)
message(STATUS "Version: ${MAJ}.${MIN}.${PAT}")  # 1.2.3
```

### Optional Arguments

```cmake showLineNumbers 
function(add_my_library name)
    cmake_parse_arguments(
        LIB
        "HEADER_ONLY"              # Optional flag
        "VERSION"                  # Optional value
        "SOURCES"                  # Required value
        ${ARGN}
    )
    
    if(LIB_HEADER_ONLY)
        add_library(${name} INTERFACE)
    else()
        if(NOT LIB_SOURCES)
            message(FATAL_ERROR "SOURCES required for non-header-only library")
        endif()
        add_library(${name} ${LIB_SOURCES})
    endif()
    
    if(LIB_VERSION)
        set_target_properties(${name} PROPERTIES VERSION ${LIB_VERSION})
    endif()
endfunction()

# Header-only usage
add_my_library(utils HEADER_ONLY)

# Regular library usage
add_my_library(core SOURCES core.cpp VERSION 1.0.0)
```

### Conditional Compilation Helper

```cmake showLineNumbers 
function(target_add_feature target feature)
    string(TOUPPER ${feature} FEATURE_UPPER)
    
    option(ENABLE_${FEATURE_UPPER} "Enable ${feature}" ON)
    
    if(ENABLE_${FEATURE_UPPER})
        target_compile_definitions(${target} PRIVATE HAS_${FEATURE_UPPER})
        message(STATUS "${target}: ${feature} enabled")
    else()
        message(STATUS "${target}: ${feature} disabled")
    endif()
endfunction()

# Usage
add_executable(myapp main.cpp)
target_add_feature(myapp networking)
target_add_feature(myapp graphics)
```

## Best Practices

:::success Function/Macro Guidelines

**Prefer functions over macros:**

- Functions provide proper scoping
- Less surprising behavior
- Easier to debug

**Use macros only for:**

- Control flow wrappers (rare)
- Simple text substitution
- When you specifically need caller scope modification

**Naming conventions:**

- Lowercase with underscores: `add_my_library`
- Prefix with project: `myproject_add_library`
- Descriptive names: `target_set_warnings` not `set_warn`

**Documentation:**

```cmake showLineNumbers 
# Add a library with standard project configuration
#
# Arguments:
#   name - Library name
#   TYPE - STATIC, SHARED, or INTERFACE (default: STATIC)
#   SOURCES - Source files
#   DEPENDENCIES - Libraries to link
function(add_project_library name)
    # ...
endfunction()
```

:::

## Common Pitfalls

:::warning Avoid These Mistakes

**❌ Forgetting PARENT_SCOPE in functions:**

```cmake showLineNumbers 
function(get_value result)
    set(${result} "value")  # Wrong - only local
endfunction()
```

**✅ Correct:**

```cmake showLineNumbers 
function(get_value result)
    set(${result} "value" PARENT_SCOPE)
endfunction()
```

**❌ Using return() in macros:**

```cmake showLineNumbers 
macro(bad_macro)
    return()  # Returns from caller!
endmacro()
```

**✅ Use function:**

```cmake showLineNumbers 
function(good_function)
    return()  # Returns from function only
endfunction()
```

:::

## Quick Reference

```cmake showLineNumbers 
# Function
function(name arg1 arg2)
    # New scope
    set(var "value" PARENT_SCOPE)  # Return value
endfunction()

# Macro
macro(name arg1 arg2)
    # Caller's scope
    # Changes affect caller
endmacro()

# Argument parsing
cmake_parse_arguments(
    PREFIX
    "OPTIONS"
    "SINGLE_VALUES"
    "MULTI_VALUES"
    ${ARGN}
)

# Built-in variables
${ARGC}    # Argument count
${ARGV}    # All arguments
${ARGN}    # Extra arguments
${ARG0}    # First argument
```

Functions and macros are essential for creating maintainable, reusable CMake code. Master them to build clean, DRY (Don't Repeat Yourself) build systems.
