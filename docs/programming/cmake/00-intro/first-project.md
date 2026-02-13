---
id: first-project
title: Your First CMake Project
sidebar_label: First CMake Project
tags: [ c++, cmake ]
---

# Your First CMake Project

## Project Structure

Let's create a simple C++ project:

```
my-first-project/
├── CMakeLists.txt
├── src/
│   └── main.cpp
└── include/
    └── greeting.h
```

## Step-by-Step Guide

### 1. Create Project Directory

```bash title="Terminal"
mkdir my-first-project
cd my-first-project
mkdir src include
```

### 2. Write Your Code

```cpp title="src/main.cpp"
#include <iostream>
#include "greeting.h"

int main() {
    std::cout << getGreeting() << std::endl;
    return 0;
}
```

```cpp title="include/greeting.h"
#ifndef GREETING_H
#define GREETING_H

#include <string>

inline std::string getGreeting() {
    return "Hello from my first CMake project!";
}

#endif // GREETING_H
```

### 3. Create CMakeLists.txt

```python title="CMakeLists.txt"
# Minimum required version
cmake_minimum_required(VERSION 3.15)

# Project name and version
project(MyFirstProject VERSION 1.0)

# Require C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add include directories
include_directories(include)

# Create executable
add_executable(myapp src/main.cpp)
```

:::info Understanding Each Line

- `cmake_minimum_required()` - Ensures compatibility
- `project()` - Names your project, sets variables like `PROJECT_NAME`
- `set(CMAKE_CXX_STANDARD)` - Specifies C++ version
- `include_directories()` - Adds header search paths
- `add_executable()` - Creates the build target
  :::

### 4. Configure and Build

```bash title="Terminal"
# Create build directory (out-of-source build)
mkdir build
cd build

# Configure (generate build files)
cmake ..

# Build
cmake --build .

# Run
./myapp
```

:::success Output

```
Hello from my first CMake project!
```

:::

## Understanding the Build Process

### Configure Phase

```bash title="Terminal"
cmake ..
```

What happens:

1. CMake reads `CMakeLists.txt`
2. Detects compiler and system
3. Generates native build files (Makefiles, .vcxproj, etc.)

Output example:

```
-- The C compiler identification is GNU 11.4.0
-- The CXX compiler identification is GNU 11.4.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Configuring done
-- Generating done
-- Build files written to: /path/to/build
```

### Build Phase

```bash title="Terminal"
cmake --build .
```

What happens:

1. Invokes native build tool (make, ninja, msbuild)
2. Compiles source files
3. Links executable

Output example:

```
[ 50%] Building CXX object CMakeFiles/myapp.dir/src/main.cpp.o
[100%] Linking CXX executable myapp
[100%] Built target myapp
```

## Common Build Configurations

### Debug Build

```bash title="Terminal"
cmake -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .
```

### Release Build

```bash title="Terminal"
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

### Using Different Generators

```bash title="Terminal"
# Unix Makefiles (default on Linux)
cmake -G "Unix Makefiles" ..

# Ninja (faster)
cmake -G "Ninja" ..

# Visual Studio
cmake -G "Visual Studio 17 2022" ..

# Xcode
cmake -G "Xcode" ..
```

## Modern CMake Approach

:::warning Better Practice
The example above works, but modern CMake uses **target-based** configuration:
:::

```python title="CMakeLists.txt (Modern Style)"
cmake_minimum_required(VERSION 3.15)
project(MyFirstProject VERSION 1.0)

# Create executable
add_executable(myapp src/main.cpp)

# Set C++ standard for this target
target_compile_features(myapp PRIVATE cxx_std_17)

# Add include directories for this target
target_include_directories(myapp PRIVATE include)
```

**Why is this better?**

- Settings apply only to `myapp`, not globally
- Clearer dependencies
- Better scalability for multi-target projects

## Quick Reference Commands

| Command | Purpose |
|---------|---------|
| `cmake -S . -B build` | Configure project (source: `.`, build: `build/`) |
| `cmake --build build` | Build project |
| `cmake --build build --clean-first` | Clean then build |
| `cmake --build build --target myapp` | Build specific target |
| `cmake --build build --parallel 8` | Build with 8 parallel jobs |

:::info Pro Tip
Modern CMake syntax: `cmake -S . -B build` is clearer than `cd build && cmake ..`
:::

## Troubleshooting

### "CMake Error: The source directory does not appear to contain CMakeLists.txt"

- Ensure `CMakeLists.txt` is in the project root
- Check spelling (case-sensitive!)

### "No CMAKE_CXX_COMPILER could be found"

- Install a C++ compiler:

  ```bash title="Terminal"
  sudo apt install build-essential  # Linux
  xcode-select --install            # macOS
  ```

### Build directory cluttered?

```bash title="Terminal"
# Always use out-of-source builds
rm -rf build/*  # Safe to delete
cmake -S . -B build
```

## Next Steps

Now that you've created your first project:

[//]: # (1. Learn about [CMakeLists.txt structure]&#40;../basics/cmakelists-structure.md&#41;)

[//]: # (2. Explore [variables]&#40;../basics/variables.md&#41;)

[//]: # (3. Understand [targets]&#40;../targets/executables.md&#41;)
