---
id: separate-compilation-and-linking
title: Separate Compilation and Linking
sidebar_label: Separate Compilation
sidebar_position: 9
tags: [gpu, cuda, nvcc, linking]
---

# Separate Compilation and Linking

`nvcc` defaults to compiling each `.cu` file's device code as a self-contained whole, with every `__device__` call resolved and inlined within that one translation unit. That default is invisible right up until device code needs to span files, at which point it fails in a way whole-program C++ intuition doesn't predict.

## Whole-program compilation is the default

By default, device code in one `.cu` file cannot call a `__device__` function defined in another `.cu` file. A `__device__` function is, by default, compiled as if it were the only translation unit that exists — there is no device-side equivalent of the ordinary host linker resolving a symbol across object files, unless that behavior is explicitly requested:

```text
error: kernel calls undefined function "helper" (declared in another translation unit)
```

## Relocatable device code

`-rdc=true` switches `nvcc` to generating relocatable device code — device object files with unresolved symbol references, the device-side analogue of ordinary host object files — instead of the default whole-program, fully-inlined device code per translation unit.

## Device linking

With `-rdc=true`, a separate device-link step resolves those cross-file references before the final host link happens; `nvcc` performs it automatically when it sees multiple relocatable device objects on its command line:

```bash
nvcc -rdc=true -arch=sm_80 -c a.cu -o a.o
nvcc -rdc=true -arch=sm_80 -c b.cu -o b.o
nvcc -arch=sm_80 a.o b.o -o app          # nvcc performs the device link
```

## What it costs

Relocatable device code is not free. Calls across translation units can no longer be inlined the way calls within one TU can, so the compiler must fall back to conservative register allocation and emit real ABI calls in the generated SASS instead of folding the callee's body into the caller. For small, hot kernels — the kind called millions of times per launch — that shows up as a measurable slowdown relative to the same logic compiled whole-program.

:::note[Cases that force separate compilation]
Some patterns cannot be expressed as whole-program device code at all: device-side `virtual` dispatch across translation units, dynamic parallelism (a kernel launching another kernel), `__device__` global variables shared across multiple `.cu` files, and linking against device-side libraries that expose callbacks, such as cuFFT's device callback API. Any of these forces `-rdc=true`, regardless of the performance cost above.
:::

## When you cannot avoid it

:::tip[CMake support is a single target property]
`set_target_properties(tgt PROPERTIES CUDA_SEPARABLE_COMPILATION ON)` turns on relocatable device code and the device-link step for a CMake target, without hand-assembling the `-rdc=true` and multi-step `nvcc` invocation shown above. See [Building CUDA with CMake](../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md) for the rest of a CUDA CMake setup.
:::

## See also

- [The Compilation Model](./the-compilation-model.md) — the whole-program pipeline this page's default departs from.
- [Dynamic Parallelism](../06-cuda-runtime-and-apis/dynamic-parallelism.md) — one of the patterns that forces `-rdc=true`.
- [Building CUDA with CMake](../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md) — the `CUDA_SEPARABLE_COMPILATION` target property in context.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
