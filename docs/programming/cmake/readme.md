---
title: Overview of CMake
sidebar_label: Overview
tags: [ c++, cmake ]
---

# CMake Overview

A comprehensive, user-friendly guide to CMake organized for easy reference and learning.

## Documentation Structure

### Introduction

Start here if you're new to CMake:

- **[What is CMake?](intro/what-is-cmake)** - Understanding the build system generator
- **[Installation](intro/installing-cmake)** - Getting CMake set up on your system
- **[First Project](intro/first-project)** - Your first CMake project step-by-step

### Basics

Core concepts you'll use daily:

- **[CMakeLists.txt Structure](basics/cmakelists-structure)** - Anatomy of a CMakeLists file
- **[Variables](basics/variables)** - Working with CMake variables and lists
- **[Commands](basics/commands)** - Essential CMake commands reference
- **[Build Types](basics/build-types)** - Debug, Release, and other configurations

### Targets

Understanding executables and libraries:

- **[Executables](targets/executables)** - Creating and configuring executables
- **[Libraries](targets/libraries)** - Static, shared, and interface libraries
- **[Target Properties](targets/target-properties)** - Configuring target-specific settings
- **[Linking](targets/linking)** - Understanding library linking

### Dependencies

Managing external libraries:

- **[find_package()](dependencies/find-package)** - Finding installed packages
- **[FetchContent](dependencies/fetchcontent)** - Downloading dependencies at configure time
- **[ExternalProject](dependencies/external-projects)** - Building external projects

### Project Organization

Structuring larger projects:

- **[Multi-Directory Projects](project-organization/multi-directory)** - Organizing code
- **[Subdirectories](project-organization/subdirectories)** - Using add_subdirectory
- **[Best Practices](project-organization/best-practices)** - Modern CMake patterns

### Advanced Topics

Level up your CMake skills:

- **[Generator Expressions](advanced/generator-expressions)** - Conditional compilation
- **[Functions and Macros](advanced/functions-and-macros)** - Reusable CMake code
- **[Find Modules](advanced/find-modules)** - Writing custom package finders
- **[Custom Commands](advanced/custom-commands)** - Extending the build process

### Testing

Adding tests to your project:

- **[CTest Basics](testing/ctest-basics)** - Introduction to CTest
- **[Test Integration](testing/integration)** - Integrating tests in your project

## Quick References

### Common Commands

```python title="CMake Basics"
# Project setup
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 1.0)

# Executables and libraries
add_executable(myapp main.cpp)
add_library(mylib STATIC lib.cpp)

# Linking
target_link_libraries(myapp PRIVATE mylib)

# Include directories
target_include_directories(myapp PRIVATE include/)

# Compile features
target_compile_features(myapp PRIVATE cxx_std_17)

# Finding packages
find_package(Threads REQUIRED)
```

### Build Workflow

```python title="Terminal"
# Configure
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build

# Test
ctest --test-dir build

# Install
cmake --install build --prefix /usr/local
```

## Documentation Conventions

Throughout this knowledge base:

:::info Information Boxes
Provide helpful context and explanations
:::

:::success Best Practices
Highlight recommended approaches
:::

:::warning Common Pitfalls
Alert you to potential issues
:::

:::danger Anti-Patterns
Identify and avoid bad practices
:::

## Code Examples

All code examples are **complete and ready to use**. They follow modern CMake practices (3.15+) and include:

- Full listings with syntax highlighting
- Comments explaining key concepts
- Practical, real-world scenarios
- Both simple and complex examples

## Finding What You Need

### By Topic

- **Getting Started**: See Introduction section
- **Day-to-Day Usage**: See Basics and Targets sections
- **Project Structure**: See Project Organization section
- **External Dependencies**: See Dependencies section
- **Advanced Features**: See Advanced Topics section

### By Use Case

- **Simple Application**: First Project → Executables
- **Library Development**: Libraries → Target Properties
- **Multi-Library Project**: Subdirectories → Linking
- **Using External Libs**: `find_package()` → FetchContent

---

**Remember**: CMake is a tool for building software. The best way to learn is by doing. Start with simple projects and gradually incorporate more features as you need them.

Happy building! 🎉
