---
id: cross-compilation
title: Cross-Compilation
sidebar_label: Cross-Compilation
sidebar_position: 14
tags: [c++, cross-compilation, toolchain, embedded, arm, build]
---

# Cross-Compilation

Cross-compiling means building on one machine (the **host**, say an x86-64 Linux laptop) a program
that runs on a different kind of machine (the **target**, say a 64-bit ARM board). You need it when
the target is too slow or too small to compile on, when you ship for several architectures from
one CI machine, or when the target has no operating system at all. The pipeline is the same four
stages, but every stage must be the target's version, and the headers and libraries you link
against must be the target's too.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md),
[Static vs Dynamic Linking](./static-vs-dynamic-linking.md).

This page covers hosted targets (a target that runs Linux or another OS). Bare-metal
microcontrollers (`arm-none-eabi`), multilibs and startup code are covered in the embedded
section: [Embedded Cross-Compilation](../../../embedded/03-toolchain-and-build/cross-compilation.md).

## What has to match the target

<Diagram title="A cross toolchain is a matched set" caption="Everything in the dotted frame comes from the target's world, even though it all runs on the host." accent="amber">
  <DiagramNode icon="monitor" title="Host: x86-64 Linux">Runs the tools</DiagramNode>
  <DiagramArrow label="runs" />
  <DiagramGroup label="Built for the target">
    <DiagramNode icon="wrench" title="Compiler, assembler, linker" accent>`aarch64-linux-gnu-g++`, `-as`, `-ld`: emit target instructions</DiagramNode>
    <DiagramNode icon="folder-tree" title="Sysroot">Target headers and libraries: libc, libstdc++, dependencies</DiagramNode>
  </DiagramGroup>
  <DiagramArrow label="produces" />
  <DiagramNode icon="cpu" title="Target binary">Runs only on aarch64 Linux</DiagramNode>
</Diagram>

GCC builds one compiler per target, named by a **target triplet**: `arch-vendor-os-abi`, with parts
often omitted. `gcc -dumpmachine` prints the triplet a compiler targets; the native one on this
machine prints `x86_64-linux-gnu`.

| Triplet | Target |
|---|---|
| `aarch64-linux-gnu` | 64-bit ARM Linux, glibc |
| `arm-linux-gnueabihf` | 32-bit ARM Linux, hard-float ABI |
| `riscv64-linux-gnu` | 64-bit RISC-V Linux |
| `x86_64-w64-mingw32` | 64-bit Windows, built with MinGW-w64 |
| `arm-none-eabi` | Bare-metal ARM, no OS ([embedded section](../../../embedded/03-toolchain-and-build/cross-compilation.md)) |

On Debian and Ubuntu the GCC cross compilers are packages: `g++-aarch64-linux-gnu`,
`g++-arm-linux-gnueabihf`, `g++-mingw-w64-x86-64`. They also install a matching libc and libstdc++
under `/usr/<triplet>/`, which acts as a minimal sysroot.

Clang is different: one Clang binary can target every architecture it was built with, selected by
`--target`. It still needs the target's headers and libraries for anything beyond freestanding code.

## Seeing the difference

Same source, two targets, compiled on the same x86-64 host with Clang 21:

<Tabs groupId="target">
  <TabItem value="x86" label="Native">

```bash
clang++ -O2 -c square.cpp -o sq_x86.o
file sq_x86.o
```

```text
sq_x86.o: ELF 64-bit LSB relocatable, x86-64, version 1 (SYSV), not stripped
```

  </TabItem>
  <TabItem value="arm" label="--target=aarch64-linux-gnu">

```bash
clang++ --target=aarch64-linux-gnu -O2 -c square.cpp -o sq_arm64.o
file sq_arm64.o
llvm-objdump -d sq_arm64.o
```

```text
sq_arm64.o: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped

0000000000000000 <_Z6squarei>:
       0: 1b007c00     	mul	w0, w0, w0
       4: d65f03c0     	ret
```

  </TabItem>
</Tabs>

`square.cpp` includes no system headers, so this works with no sysroot. The host's GNU `objdump`
cannot disassemble it (`can't disassemble for architecture UNKNOWN!`); you need the target's
binutils or the multi-target `llvm-objdump`. As soon as a file includes `<cstdio>`, the same
command fails with `fatal error: 'cstdio' file not found`: the compiler is ready, but the target's
headers are missing. That is what a sysroot provides.

## The sysroot

A **sysroot** is a directory that looks like the target's root filesystem for the parts the build
needs: `usr/include`, `usr/lib`, `lib`. The compiler and linker look there instead of in the host's
`/usr`:

```bash
aarch64-linux-gnu-g++ --sysroot=/opt/sysroots/rpi4 -O2 main.cpp -o app
clang++ --target=aarch64-linux-gnu --sysroot=/opt/sysroots/rpi4 -fuse-ld=lld -O2 main.cpp -o app
```

Ways to get one: the distribution's cross packages (for standard libraries only), a copy of the
target's `/usr` and `/lib` (`rsync` from the device), or the SDK that a board vendor or Yocto/Buildroot
generates. Every third-party library you link must also be built for the target and installed
into the sysroot. This is usually the hardest part of a cross build.

## Cross-compiling with CMake

CMake takes the cross settings from a **toolchain file**, passed once at configure time
([CMake: toolchains](https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html)):

```cmake title="aarch64-linux.cmake"
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER   aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

set(CMAKE_SYSROOT /opt/sysroots/rpi4)          # optional with distro cross packages

# Look for programs (code generators) on the host, but headers, libraries and packages only in the target.
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

```bash
cmake -S . -B build-arm64 -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=aarch64-linux.cmake \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build-arm64
```

Setting `CMAKE_SYSTEM_NAME` is what tells CMake this is a cross build (`CMAKE_CROSSCOMPILING`
becomes true). Keep one build directory per target. Package managers have their own equivalents:
vcpkg **triplets** and Conan **host profiles** ([Package Managers](./package-managers.md)).

## Running and testing target binaries

- **On the device:** copy with `scp`, run over `ssh`.
- **With user-mode QEMU:** `qemu-aarch64` runs a single Linux binary of another architecture on the
  host. For a dynamically linked binary, point it at the target libraries with `-L <sysroot>`; a
  statically linked one runs as is. With `binfmt_misc` registered (Debian's `qemu-user-binfmt`
  package), the kernel runs foreign binaries through QEMU automatically, so `./app` just works and
  CTest can run the test suite.
- **In a container:** Docker's `--platform linux/arm64` runs an ARM image through the same QEMU
  mechanism, which is another way to get a complete target userland and sysroot.

Emulation checks correctness, not performance; measure speed on the real hardware.

## Tuning for the target CPU

`-march` selects the instruction set that may be used, `-mtune` only the scheduling model. A
cross build should name the oldest CPU you support, never `native` (that would mean the host's CPU).

```bash
aarch64-linux-gnu-g++ -O2 -mcpu=cortex-a72 main.cpp -o app       # Raspberry Pi 4's CPU core
aarch64-linux-gnu-g++ -O2 -march=armv8-a main.cpp -o app          # any 64-bit ARMv8 CPU
```

On ARM, GCC prefers `-mcpu` (which sets both architecture and tuning). 32-bit ARM also has
floating-point ABI options (`-mfloat-abi=hard` for `gnueabihf`) that must match the target's
libraries; mixing them fails at link time or, worse, passes floats in the wrong registers.

## Pitfalls

- **Host libraries in a cross link.** `-L/usr/lib` or a `find_package` that finds the host's
  copy gives `file in wrong format` or `incompatible` errors from the linker. That is what the
  `CMAKE_FIND_ROOT_PATH_MODE_*` settings prevent.
- **A newer glibc in the sysroot than on the device.** The binary fails on the device with
  `version 'GLIBC_2.xx' not found`. Build against a sysroot taken from the oldest target you support.
- **Code generators built for the target.** A build step that compiles a tool and runs it (protoc
  plugins, table generators) must build that tool for the *host*. Build it separately and import it.
- **Assuming the host's type sizes.** `long` is 64-bit on aarch64 Linux but 32-bit on 32-bit ARM
  and on Windows. Use `<cstdint>` types where the size matters, and `static_assert` your
  assumptions.

## Key points

- Every stage and every library must be the target's; the host only runs the tools.
- The compiler is the easy part; the sysroot (target headers and libraries) is the work.
- With CMake, put all of it in a toolchain file and use one build directory per target.
- QEMU user mode runs target binaries on the host for testing.
