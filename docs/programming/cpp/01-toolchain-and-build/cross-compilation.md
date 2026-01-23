---
id: cross-compilation
title: Cross-Compilation
sidebar_label: Cross-Compilation
sidebar_position: 14
tags: [c++, cross-compilation, toolchain, embedded, arm, build]
---

# Cross-Compilation

Cross-compilation builds executables for a different platform (target) than the one running the compiler (host). Essential for embedded systems, mobile development, and deploying to different architectures.

:::info Build Here, Run There
**Host** = where you compile (e.g., x86-64 Linux laptop)  
**Target** = where executable runs (e.g., ARM Raspberry Pi)
:::

## Why Cross-Compile?

**Common scenarios:**
- **Embedded systems** - ARM microcontrollers (limited resources)
- **Raspberry Pi / IoT** - ARM devices
- **Mobile** - Android (ARM), iOS
- **Different OS** - Linux → Windows
- **Performance** - Fast host, slow target
```mermaid
graph LR
    A[Host: x86-64 Linux] -->|Cross-Compile| B[Target Binary]
    B --> C[Target: ARM Raspberry Pi]
    
    style A fill:#B4E5FF
    style C fill:#FFE5B4
```

## Basic Concepts
```bash
# Native compilation (same platform)
g++ main.cpp -o app      # Runs on x86-64
./app                    # Works

# Cross-compilation
arm-linux-gnueabihf-g++ main.cpp -o app  # For ARM
./app                    # ❌ Won't run on x86-64!
scp app pi@raspberrypi:~/  # Transfer to target
ssh pi@raspberrypi ./app   # ✅ Runs on ARM
```

## Cross-Compiler Toolchain

A toolchain contains:
- **Compiler** - `arm-linux-gnueabihf-gcc`
- **Linker** - `arm-linux-gnueabihf-ld`
- **Libraries** - Target platform libraries
- **Headers** - Target system headers

### Installing Toolchains
```bash
# Debian/Ubuntu - ARM toolchain
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# Raspberry Pi 64-bit
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# Windows cross-compilation on Linux
sudo apt-get install mingw-w64

# Custom toolchains
# Download from vendor (ARM, Xilinx, etc.)
```

## Basic Cross-Compilation
```bash
# Check toolchain
arm-linux-gnueabihf-g++ --version

# Compile for ARM
arm-linux-gnueabihf-g++ \
    -march=armv7-a \
    -mfpu=neon \
    main.cpp -o app_arm

# Check binary type
file app_arm
# app_arm: ELF 32-bit LSB executable, ARM, version 1 (SYSV)
```

## CMake Cross-Compilation

Create a toolchain file:
```cmake
# toolchain-arm.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)

# Cross-compiler location
set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)

# Target environment
set(CMAKE_FIND_ROOT_PATH /usr/arm-linux-gnueabihf)

# Search for programs in host environment
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)

# Search for libraries/includes in target environment
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

**Use toolchain:**
```bash
# Configure with toolchain
cmake -S . -B build \
    -DCMAKE_TOOLCHAIN_FILE=toolchain-arm.cmake \
    -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build
```

## Common Target Architectures
```bash
# ARM 32-bit (Raspberry Pi 3 and older)
arm-linux-gnueabihf-g++ -march=armv7-a main.cpp -o app

# ARM 64-bit (Raspberry Pi 4, modern ARM)
aarch64-linux-gnu-g++ main.cpp -o app

# Windows from Linux (MinGW)
x86_64-w64-mingw32-g++ main.cpp -o app.exe

# RISC-V
riscv64-linux-gnu-g++ main.cpp -o app

# MIPS
mips-linux-gnu-g++ main.cpp -o app
```

## Architecture-Specific Flags
```bash
# Raspberry Pi 3 optimization
arm-linux-gnueabihf-g++ \
    -march=armv8-a \           # Architecture
    -mtune=cortex-a53 \        # CPU type
    -mfpu=neon-fp-armv8 \      # FPU
    -mfloat-abi=hard \         # Floating point ABI
    main.cpp -o app

# Generic ARM (portable)
arm-linux-gnueabihf-g++ \
    -march=armv7-a \
    main.cpp -o app
```

## Handling Dependencies

### Static Linking (Simplest)
```bash
# Include all libraries in binary
arm-linux-gnueabihf-g++ \
    -static \
    main.cpp -lpthread -o app

# Self-contained, but large
```

### Dynamic Linking (Requires Target Libraries)
```bash
# Need target's shared libraries
arm-linux-gnueabihf-g++ \
    main.cpp -lpthread -o app

# Check dependencies
arm-linux-gnueabihf-readelf -d app | grep NEEDED
# libpthread.so.0
# libc.so.6

# Must be present on target system
```

### Sysroot (Target Filesystem)
```bash
# Point to target's root filesystem
arm-linux-gnueabihf-g++ \
    --sysroot=/path/to/rpi-sysroot \
    main.cpp -o app

# CMake
cmake -DCMAKE_SYSROOT=/path/to/rpi-sysroot ...
```

## Testing Without Target Hardware

### QEMU Emulation
```bash
# Install QEMU
sudo apt-get install qemu-user-static

# Run ARM binary on x86-64
qemu-arm-static app_arm

# With libraries
qemu-arm-static -L /usr/arm-linux-gnueabihf app_arm
```

### Docker for Cross-Compilation
```dockerfile
# Dockerfile for ARM cross-compilation
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    cmake

WORKDIR /build
COPY . .

RUN mkdir build && cd build && \
    cmake .. -DCMAKE_TOOLCHAIN_FILE=../toolchain-arm.cmake && \
    cmake --build .
```
```bash
docker build -t cross-compiler .
docker run -v $(pwd):/build cross-compiler
```

## Common Pitfalls

:::danger Watch Out

**Endianness mismatch:**
- Most ARM is little-endian like x86
- Some embedded systems are big-endian
- Check binary formats match

**Library versions:**
- Target libraries must match toolchain
- Use sysroot or static linking

**Architecture assumptions:**
- Don't hardcode `sizeof(void*)` == 8
- Use `size_t`, `intptr_t` for portable code

**Optimization flags:**
- Host optimizations may not work on target
- Test on actual hardware
  :::

## Quick Reference
```bash
# Install ARM toolchain (Debian/Ubuntu)
sudo apt-get install gcc-arm-linux-gnueabihf

# Compile for ARM
arm-linux-gnueabihf-g++ main.cpp -o app

# Check binary
file app
arm-linux-gnueabihf-readelf -h app

# Transfer to target
scp app user@target:/path/

# Test with QEMU (without hardware)
qemu-arm-static app
```

## Summary

Cross-compilation builds for different platforms:

**Key components:**
- **Toolchain** - compiler for target architecture
- **Sysroot** - target filesystem (headers/libraries)
- **Toolchain file** - CMake configuration for cross-build

**Common targets:**
- ARM (Raspberry Pi, embedded)
- Windows from Linux (MinGW)
- Mobile (Android NDK, iOS)

**Best practices:**
- Use CMake toolchain files
- Static linking for simplicity
- Test with QEMU or actual hardware
- Use Docker for reproducible builds
```bash
