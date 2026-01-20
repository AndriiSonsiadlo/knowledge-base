---
id: installing-cmake
title: Installing CMake
sidebar_label: Installing CMake
sidebar_position: 2
tags: [ c++, cmake ]
---

# Installing CMake

## Installation Methods

### Linux

#### Ubuntu/Debian

```bash title="Terminal"
# Option 1: APT (may be older version)
sudo apt update
sudo apt install cmake

# Option 2: Official CMake APT repository (latest)
wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc | sudo apt-key add -
sudo apt-add-repository 'deb https://apt.kitware.com/ubuntu/ focal main'
sudo apt update
sudo apt install cmake
```

#### Fedora/RHEL

```bash title="Terminal"
sudo dnf install cmake
```

#### Arch Linux

```bash title="Terminal"
sudo pacman -S cmake
```

### macOS

```bash title="Terminal"
# Using Homebrew (recommended)
brew install cmake

# Using MacPorts
sudo port install cmake
```

### Windows

:::info Recommended Method
Download the installer from [cmake.org/download](https://cmake.org/download/)
:::

**Steps:**

1. Download the `.msi` installer
2. Run installer
3. ✅ Check "Add CMake to system PATH"
4. Complete installation

**Alternative - Chocolatey:**

```powershell
choco install cmake
```

## Verifying Installation

```bash title="Terminal"
cmake --version
```

Expected output:

```
cmake version 3.28.1
```

:::success Minimum Version
For modern C++ projects, use **CMake 3.15+**. Many features require this baseline.
:::

## Installing from Source

For the latest features or specific versions:

```bash title="Terminal"
# Download source
wget https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1.tar.gz
tar -xzvf cmake-3.28.1.tar.gz
cd cmake-3.28.1

# Build and install
./bootstrap
make -j$(nproc)
sudo make install
```

## IDE Integration

### Visual Studio Code

Install extensions:

```bash title="Terminal"
code --install-extension ms-vscode.cmake-tools
code --install-extension twxs.cmake
```

### CLion

CMake support is **built-in** - no setup needed! ✨

### Visual Studio

CMake support included in:

- Visual Studio 2017+
- Install "C++ CMake tools for Windows" component

## Environment Setup

### Setting CMake Path (if needed)

**Linux/macOS:**

```bash title="Terminal"
# Add to ~/.bashrc or ~/.zshrc
export PATH="/opt/cmake/bin:$PATH"
```

**Windows:**

```
System Properties → Environment Variables → Path → Add:
C:\Program Files\CMake\bin
```

## Testing Your Setup

Create a test project:

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(TestSetup)

message(STATUS "CMake version: ${CMAKE_VERSION}")
message(STATUS "System: ${CMAKE_SYSTEM_NAME}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
```

Run:

```bash title="Terminal"
mkdir build && cd build
cmake ..
```

:::warning Common Issues

- **cmake: command not found** → Path not set correctly
- **Old version** → Update using package manager or install from source
- **Permission denied** → Use `sudo` for system-wide installation
  :::

## Additional Tools

Consider installing alongside CMake:

```bash title="Terminal"
# Ninja - faster build tool
sudo apt install ninja-build  # Linux
brew install ninja            # macOS

# ccache - compilation cache
sudo apt install ccache       # Linux
brew install ccache          # macOS
```
