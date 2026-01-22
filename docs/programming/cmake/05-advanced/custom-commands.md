---
id: custom-commands
title: Custom Commands and Targets
sidebar_label: Custom Commands
sidebar_position: 4
tags: [cmake, custom-commands, custom-targets, build-process]
---

# Custom Commands and Targets

## Overview

Custom commands and targets extend CMake's build process beyond compiling code. Use them for:

- Code generation
- Resource processing
- Running external tools
- Post-build operations
- Custom build steps

The difference:

- **Custom commands**: Execute as part of building another target
- **Custom targets**: Standalone targets you can build explicitly

## Custom Commands

### add_custom_command() - Two Forms

CMake's `add_custom_command()` has two distinct uses:

**Form 1: Generating files** (happens during build)
**Form 2: Pre/post build actions** (attached to targets)

### Generating Files

Create files as part of the build:

```cmake showLineNumbers 
add_custom_command(
    OUTPUT generated_file.cpp              # File to generate
    COMMAND python3 ${CMAKE_SOURCE_DIR}/generate.py
        ${CMAKE_CURRENT_BINARY_DIR}/generated_file.cpp
    DEPENDS ${CMAKE_SOURCE_DIR}/template.txt
    COMMENT "Generating source file..."
)

add_executable(myapp
    main.cpp
    ${CMAKE_CURRENT_BINARY_DIR}/generated_file.cpp
)
```

**How it works:**

- CMake sees `generated_file.cpp` in target sources
- Finds the custom command that generates it
- Runs command if output missing or dependencies changed
- Then compiles normally

**Key options:**

- `OUTPUT`: Files the command creates (required)
- `COMMAND`: Command to execute
- `DEPENDS`: Files that trigger regeneration when changed
- `COMMENT`: Message shown when running
- `WORKING_DIRECTORY`: Where to run command

### Multiple Outputs

One command generating multiple files:

```cmake showLineNumbers 
add_custom_command(
    OUTPUT
        config.h
        config.cpp
    COMMAND ${CMAKE_COMMAND}
        -DINPUT=${CMAKE_SOURCE_DIR}/config.in
        -DOUTPUT_H=${CMAKE_CURRENT_BINARY_DIR}/config.h
        -DOUTPUT_CPP=${CMAKE_CURRENT_BINARY_DIR}/config.cpp
        -P ${CMAKE_SOURCE_DIR}/cmake/generate_config.cmake
    DEPENDS config.in
    COMMENT "Generating configuration files"
)

add_library(config ${CMAKE_CURRENT_BINARY_DIR}/config.cpp)
```

### Pre/Post Build Actions

Run commands before or after building a target:

```cmake showLineNumbers 
add_executable(myapp main.cpp)

# Run after building
add_custom_command(TARGET myapp POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:myapp>
        ${CMAKE_BINARY_DIR}/dist/
    COMMENT "Copying executable to dist/"
)
```

**Event types:**

- `PRE_BUILD`: Before compilation (Visual Studio only, otherwise same as PRE_LINK)
- `PRE_LINK`: After compilation, before linking
- `POST_BUILD`: After linking completes

**Common uses:**

```cmake showLineNumbers 
# Copy DLLs on Windows
if(WIN32)
    add_custom_command(TARGET myapp POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:mylib>
            $<TARGET_FILE_DIR:myapp>
    )
endif()

# Strip symbols in Release
add_custom_command(TARGET myapp POST_BUILD
    COMMAND $<$<CONFIG:Release>:strip>
    ARGS $<TARGET_FILE:myapp>
    COMMENT "Stripping symbols..."
)

# Sign executable on macOS
if(APPLE)
    add_custom_command(TARGET myapp POST_BUILD
        COMMAND codesign -s "Developer ID" $<TARGET_FILE:myapp>
        COMMENT "Signing application..."
    )
endif()
```

## Custom Targets

Targets that don't produce normal build outputs:

```cmake showLineNumbers 
add_custom_target(name
    [ALL]
    COMMAND command1
    COMMAND command2
    DEPENDS dependencies
    COMMENT "Comment shown when building"
)
```

**ALL keyword:** Include in default build (runs when you type `make`)

### Documentation Generation

```cmake showLineNumbers 
find_package(Doxygen)

if(DOXYGEN_FOUND)
    add_custom_target(docs
        COMMAND ${DOXYGEN_EXECUTABLE} ${CMAKE_SOURCE_DIR}/Doxyfile
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Generating documentation with Doxygen"
        VERBATIM
    )
endif()
```

Build with: `cmake --build build --target docs`

### Format Code

```cmake showLineNumbers 
find_program(CLANG_FORMAT clang-format)

if(CLANG_FORMAT)
    file(GLOB_RECURSE ALL_SOURCE_FILES
        ${CMAKE_SOURCE_DIR}/src/*.cpp
        ${CMAKE_SOURCE_DIR}/src/*.h
        ${CMAKE_SOURCE_DIR}/include/*.h
    )
    
    add_custom_target(format
        COMMAND ${CLANG_FORMAT} -i ${ALL_SOURCE_FILES}
        COMMENT "Formatting source code..."
    )
endif()
```

### Run Linter

```cmake showLineNumbers 
add_custom_target(lint
    COMMAND cppcheck
        --enable=all
        --std=c++17
        --quiet
        ${CMAKE_SOURCE_DIR}/src
    COMMENT "Running cppcheck..."
)
```

### Package Distribution

```cmake showLineNumbers 
add_custom_target(package
    COMMAND ${CMAKE_COMMAND} -E tar czf
        ${CMAKE_BINARY_DIR}/myapp-${PROJECT_VERSION}.tar.gz
        --format=gnutar
        ${CMAKE_BINARY_DIR}/bin/myapp
        ${CMAKE_SOURCE_DIR}/README.md
        ${CMAKE_SOURCE_DIR}/LICENSE
    COMMENT "Creating distribution package..."
)
```

## Practical Examples

### Protocol Buffer Compilation

```cmake showLineNumbers 
find_package(Protobuf REQUIRED)

set(PROTO_FILES
    messages.proto
    requests.proto
)

foreach(proto ${PROTO_FILES})
    get_filename_component(proto_name ${proto} NAME_WE)
    
    add_custom_command(
        OUTPUT
            ${CMAKE_CURRENT_BINARY_DIR}/${proto_name}.pb.h
            ${CMAKE_CURRENT_BINARY_DIR}/${proto_name}.pb.cc
        COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
            --cpp_out=${CMAKE_CURRENT_BINARY_DIR}
            --proto_path=${CMAKE_CURRENT_SOURCE_DIR}
            ${CMAKE_CURRENT_SOURCE_DIR}/${proto}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${proto}
        COMMENT "Compiling ${proto}"
    )
    
    list(APPEND PROTO_SRCS ${CMAKE_CURRENT_BINARY_DIR}/${proto_name}.pb.cc)
endforeach()

add_library(protos ${PROTO_SRCS})
target_link_libraries(protos PUBLIC ${PROTOBUF_LIBRARIES})
target_include_directories(protos PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
```

### Qt MOC Generation

While Qt provides modules, here's the manual approach:

```cmake showLineNumbers 
find_package(Qt5 COMPONENTS Core REQUIRED)

set(MOC_HEADERS
    mywidget.h
    mymodel.h
)

foreach(header ${MOC_HEADERS})
    get_filename_component(header_name ${header} NAME_WE)
    
    add_custom_command(
        OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/moc_${header_name}.cpp
        COMMAND Qt5::moc
            ${CMAKE_CURRENT_SOURCE_DIR}/${header}
            -o ${CMAKE_CURRENT_BINARY_DIR}/moc_${header_name}.cpp
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${header}
        COMMENT "Generating MOC for ${header}"
    )
    
    list(APPEND MOC_SOURCES ${CMAKE_CURRENT_BINARY_DIR}/moc_${header_name}.cpp)
endforeach()

add_executable(myapp main.cpp ${MOC_SOURCES})
```

### Resource Embedding

Convert files to C arrays:

```cmake showLineNumbers 
function(embed_resource output input)
    add_custom_command(
        OUTPUT ${output}
        COMMAND xxd -i ${input} ${output}
        DEPENDS ${input}
        COMMENT "Embedding ${input}"
    )
endfunction()

embed_resource(
    ${CMAKE_CURRENT_BINARY_DIR}/logo.h
    ${CMAKE_SOURCE_DIR}/resources/logo.png
)

add_executable(myapp
    main.cpp
    ${CMAKE_CURRENT_BINARY_DIR}/logo.h
)
```

### Shader Compilation

```cmake showLineNumbers 
file(GLOB SHADERS ${CMAKE_SOURCE_DIR}/shaders/*.glsl)

foreach(shader ${SHADERS})
    get_filename_component(shader_name ${shader} NAME)
    
    add_custom_command(
        OUTPUT ${CMAKE_BINARY_DIR}/shaders/${shader_name}.spv
        COMMAND glslc ${shader}
            -o ${CMAKE_BINARY_DIR}/shaders/${shader_name}.spv
        DEPENDS ${shader}
        COMMENT "Compiling shader ${shader_name}"
    )
    
    list(APPEND COMPILED_SHADERS ${CMAKE_BINARY_DIR}/shaders/${shader_name}.spv)
endforeach()

# Custom target to compile all shaders
add_custom_target(shaders ALL DEPENDS ${COMPILED_SHADERS})

# Make executable depend on shaders
add_executable(renderer main.cpp)
add_dependencies(renderer shaders)
```

## Dependencies Between Custom Targets

Custom targets can depend on other targets:

```cmake showLineNumbers 
# Custom target that depends on executable
add_custom_target(run
    COMMAND myapp
    DEPENDS myapp
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMENT "Running application..."
)

# Chain of custom targets
add_custom_target(build_docs DEPENDS docs)
add_custom_target(deploy DEPENDS build_docs package)
```

## Using Generator Expressions

Custom commands support generator expressions:

```cmake showLineNumbers 
add_custom_command(TARGET myapp POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:myapp>
        ${CMAKE_BINARY_DIR}/$<CONFIG>/
    COMMENT "Copying to config directory: $<CONFIG>"
)
```

## Cross-Platform Considerations

Use `${CMAKE_COMMAND} -E` for portable file operations:

```cmake showLineNumbers 
add_custom_command(TARGET myapp POST_BUILD
    # Copy file
    COMMAND ${CMAKE_COMMAND} -E copy
        source.txt dest.txt
    
    # Copy directory
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/resources
        ${CMAKE_BINARY_DIR}/resources
    
    # Make directory
    COMMAND ${CMAKE_COMMAND} -E make_directory
        ${CMAKE_BINARY_DIR}/output
    
    # Remove files
    COMMAND ${CMAKE_COMMAND} -E remove
        temp.txt
)
```

**Available commands:**

- `copy`, `copy_if_different`, `copy_directory`
- `make_directory`, `remove`, `remove_directory`
- `rename`, `touch`, `tar`, `echo`

## VERBATIM Option

Always use `VERBATIM` for commands with complex arguments:

```cmake showLineNumbers 
add_custom_command(
    OUTPUT output.txt
    COMMAND ${CMAKE_COMMAND} -E echo "Complex string with spaces"
        > output.txt
    VERBATIM
)
```

`VERBATIM` ensures proper escaping of arguments across platforms.

## Byproducts

Declare files created as side effects:

```cmake showLineNumbers 
add_custom_command(
    OUTPUT main_output.txt
    BYPRODUCTS side_effect.log
    COMMAND python3 script.py
        --output main_output.txt
        --log side_effect.log
    DEPENDS script.py
)
```

This helps CMake understand the full build graph, important for Ninja generator.

## Best Practices

:::success Custom Command Guidelines

1. **Depend on actual inputs** - list all files that trigger rebuild
2. **Use absolute paths** for `OUTPUT` - ensures correct location
3. **Use target file properties** - `$<TARGET_FILE:tgt>` not hardcoded names
4. **Add VERBATIM** - for proper argument escaping
5. **Use CMAKE_COMMAND -E** - for portable file operations
6. **Comment your commands** - explain what and why
7. **Check tools exist** - use `find_program()` first
8. **Use BYPRODUCTS** - for files created but not as main OUTPUT
   :::

:::warning Common Pitfalls

**❌ Relative paths in OUTPUT:**

```cmake showLineNumbers 
OUTPUT file.cpp  # Wrong - unclear which directory
```

**✅ Absolute paths:**

```cmake showLineNumbers 
OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/file.cpp
```

**❌ Forgetting dependencies:**

```cmake showLineNumbers 
# Missing DEPENDS - won't rebuild when template changes
add_custom_command(
    OUTPUT file.cpp
    COMMAND generate.py
)
```

**✅ Include dependencies:**

```cmake showLineNumbers 
add_custom_command(
    OUTPUT file.cpp
    COMMAND generate.py
    DEPENDS template.txt generate.py
)
```

:::

## Quick Reference

```cmake showLineNumbers 
# Generate files
add_custom_command(
    OUTPUT file.cpp
    COMMAND tool args
    DEPENDS input.txt
    COMMENT "Generating..."
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    VERBATIM
)

# Pre/post build
add_custom_command(TARGET myapp POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy file dest
    COMMENT "Copying..."
)

# Custom target
add_custom_target(name [ALL]
    COMMAND cmd1
    COMMAND cmd2
    DEPENDS targets
    COMMENT "Comment..."
)

# Dependencies
add_dependencies(target_name dependency)

# Portable commands
${CMAKE_COMMAND} -E copy src dst
${CMAKE_COMMAND} -E make_directory dir
${CMAKE_COMMAND} -E remove file
```

Custom commands and targets are powerful for integrating external tools and extending the build process beyond standard compilation.
