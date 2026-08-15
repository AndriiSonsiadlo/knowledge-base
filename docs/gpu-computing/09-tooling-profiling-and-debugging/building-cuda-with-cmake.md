---
id: building-cuda-with-cmake
title: Building CUDA with CMake
sidebar_label: CUDA with CMake
sidebar_position: 1
tags: [gpu, cuda, tooling, cmake]
---

# Building CUDA with CMake

A CUDA project stops being a single `nvcc` invocation the moment it has more than one translation unit, a library dependency, or a need to target more than one GPU architecture, and hand-rolled build scripts get brittle fast at that point. CMake treats CUDA as a first-class language rather than a special case bolted onto a C++ build, which is what makes multi-file projects, per-architecture code generation, and linking against CUDA libraries manageable without duplicating flags across a Makefile.

## Enabling the CUDA language

The modern, recommended form is `project(x LANGUAGES CXX CUDA)`. This makes CMake treat `.cu` files as first-class sources — compiled with the right compiler, given their own set of language properties — the same way it already treats `.cpp` files. The older `find_package(CUDA)` module is deprecated as of CMake 3.10 and should not be used in new projects; it predates native CUDA language support and works by shelling out to `nvcc` through custom commands rather than integrating with the target model, which is also why hand-writing a raw `nvcc` command line for anything beyond a single file is not worth it once CMake's target-based approach is available.

## Architectures

`CUDA_ARCHITECTURES` on a target controls which GPU generations `nvcc` generates code for, and it accepts a few distinct forms:

- `80` — both PTX and SASS for compute capability 8.0 (embedded SASS for that exact architecture, plus PTX for forward compatibility via JIT).
- `80-real` — SASS only, no embedded PTX; smaller binary, but no forward-compatible JIT fallback.
- `80-virtual` — PTX only, no SASS; the driver JIT-compiles at load time on every run.
- `native` — whatever GPU is present on the machine doing the build; convenient for a workstation, wrong for a build that has to run on hardware it wasn't compiled on.
- `all-major` — one architecture per major GPU generation CMake knows about; the right default for a broadly distributed release build.

See [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) for what compute capability numbers correspond to which hardware generation.

## Separable compilation

By default, CUDA compiles each `.cu` file to a self-contained object with no device-side external linkage: a `__global__` or `__device__` function in one file can't be called from another. Setting `CUDA_SEPARABLE_COMPILATION ON` turns on relocatable device code generation and a device-link step, so device functions can be declared in a header and defined in a different translation unit than their caller — ordinary C++ practice, but not the CUDA default.

:::note[Separable compilation has a cost]
Relocatable device code disables some cross-function optimizations `nvcc` can otherwise perform when everything is visible in one translation unit, and the extra device-link step adds build time. Turn it on only for targets that actually need cross-TU device calls; see [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md) for what that link step is doing and what it costs at runtime.
:::

## Linking CUDA libraries

`find_package(CUDAToolkit REQUIRED)` locates the installed toolkit and exposes imported targets — `CUDA::cudart`, `CUDA::cublas`, `CUDA::cufft`, and the rest — that carry their own include directories and link flags. Linking against `CUDA::cublas` pulls in the right headers and library path without hand-writing `-I` and `-L` flags for wherever the toolkit happens to be installed on a given machine.

## Host compiler flags

`nvcc` splits every translation unit into a host part and a device part and forwards flags to whichever underlying host compiler it's paired with, which means a flag meant only for `nvcc` or only for the device compilation can leak into the host compiler and break the build in confusing ways. The generator expression `$<$<COMPILE_LANGUAGE:CUDA>:...>` scopes flags so they apply only when CMake is compiling a CUDA source, never a plain C++ one — the standard way to add `nvcc`-specific options like `--expt-relaxed-constexpr` without corrupting host-only compiles in a mixed-language target. Going the other direction — a flag meant for the host compiler that `nvcc` would otherwise misinterpret as its own — needs `-Xcompiler` to pass it through unchanged, for example `-Xcompiler -fPIC`.

## A complete example

```cmake showLineNumbers title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.24)
project(gpuapp LANGUAGES CXX CUDA)

add_executable(gpuapp src/main.cu src/kernels.cu)

set_target_properties(gpuapp PROPERTIES
    CUDA_ARCHITECTURES "80;90"       # SASS for Ampere and Hopper
    CUDA_SEPARABLE_COMPILATION ON)   # only if you need cross-TU device calls

target_compile_options(gpuapp PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr -lineinfo>)

find_package(CUDAToolkit REQUIRED)
target_link_libraries(gpuapp PRIVATE CUDA::cublas CUDA::cudart)
```

`-lineinfo` is worth calling out on its own: it embeds source file and line correlation into the generated code at negligible compile-time and runtime cost, without disabling optimizations the way full device debug info (`-G`) does. It's what makes [Nsight Compute](./nsight-compute.md)'s source-level view — and `compute-sanitizer`'s line-numbered reports — point at an actual line in `kernels.cu` instead of a bare instruction address.

## See also

- [Nsight Compute](./nsight-compute.md) — the profiler that needs `-lineinfo` for source-level attribution.
- [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md) — what the device-link step under `CUDA_SEPARABLE_COMPILATION` actually does.
- [CMake](../../programming/cmake/readme.md) — CMake fundamentals beyond the CUDA-specific pieces on this page.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
