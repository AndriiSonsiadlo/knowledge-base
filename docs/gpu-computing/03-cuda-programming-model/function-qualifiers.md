---
id: function-qualifiers
title: Function and Variable Qualifiers
sidebar_label: Qualifiers
sidebar_position: 7
tags: [gpu, cuda, qualifiers, language]
---

# Function and Variable Qualifiers

Every function and variable in a CUDA source file needs to answer two questions: which processor does this run on or live on, and who is allowed to call or touch it. C++ alone has no way to express that — `__global__`, `__device__`, `__host__`, `__shared__`, `__constant__`, and their relatives are CUDA's answer, and getting them right is what makes the rest of the language (templates, references, most of the standard library subset) usable across the host/device boundary at all.

## Function qualifiers

| Qualifier | Applies to | Callable from | Runs on |
|---|---|---|---|
| `__global__` | Kernel entry point | Host (or device, with dynamic parallelism) | Device |
| `__device__` | Ordinary function | Device only | Device |
| `__host__` | Ordinary function | Host only | Host |
| `__host__ __device__` | Ordinary function | Host and device | Both (compiled twice) |

A function with no qualifier at all defaults to `__host__`. `__global__` functions must return `void`, are called with the `<<<grid, block>>>` launch syntax rather than a plain call, and cannot be called directly from other device functions the way a `__device__` function can.

## Variable qualifiers

| Qualifier | Scope | Lifetime | Lives in |
|---|---|---|---|
| `__shared__` | One block | Block's execution | On-chip shared memory |
| `__constant__` | Whole grid, read-only from device | Application | Constant memory (cached) |
| `__managed__` | Whole application, host and device | Application | Unified-memory-managed allocation |
| `__device__` (on a variable) | Whole grid | Application | Global memory |

`__shared__` variables are declared inside a kernel and exist only while that block is resident — every thread in the block sees the same instance. `__constant__` and `__device__` variables are declared at file scope and persist for the life of the program, the difference being that `__constant__` is read-only from device code and backed by a small, heavily cached memory space; [Constant and Texture Memory](../04-cuda-memory-model/constant-and-texture-memory.md) covers that space in depth. `__managed__` variables are the odd one out: the same symbol is directly accessible from both host and device code, with the unified memory system migrating pages between them as needed.

## Inlining and `__restrict__`

`__restrict__` is CUDA's spelling of C99's `restrict`: it tells the compiler that a pointer is the only way a given piece of memory will be accessed for the lifetime of the pointer, so no write through any other pointer in scope can alias it. Without that promise, the compiler must assume any two pointer parameters might overlap, which forces it to reload from memory after every write instead of keeping values in registers, and blocks it from routing loads through the read-only data cache. The payoff shows up directly in the generated code:

```cpp showLineNumbers
// Before: compiler cannot assume x and y don't overlap
__global__ void saxpy(int n, float a, const float* x, float* y);

// After: compiler can keep loads in registers, use the read-only path
__global__ void saxpy(int n, float a, const float* __restrict__ x, float* __restrict__ y);
```

The qualifier is a promise the programmer makes, not something the compiler verifies — passing overlapping pointers to a function declared `__restrict__` is undefined behavior, not a slowdown.

## Combining `__host__ __device__`

A function marked `__host__ __device__` is compiled twice, once for each target, which is why it must stick to code both compilers can produce: no direct calls into a library that only exists on one side, and no branching on `__CUDA_ARCH__` unless the divergent branches are themselves valid on their respective side. This is the idiom that lets a single templated math function, or a small utility like a `dim3`-style struct, be reused unchanged from both host and device code instead of being written twice.

:::warning[`__forceinline__` and `__noinline__` are hints, not switches]
Both interact directly with register pressure and code size: forcing inlining can blow up register usage per thread and reduce occupancy, while forcing a function out-of-line adds call overhead and, without `-rdc=true`, must stay within the same translation unit. Reach for either only after profiling shows the compiler's default inlining decision is the actual bottleneck — do not sprinkle them speculatively.
:::

## What the C++ subset allows

:::note[Device code is a restricted subset of C++]
Exceptions and RTTI are unavailable in device code, and virtual function calls cannot cross the host/device boundary — a `__device__` object can use virtual dispatch among device-side overrides, but a virtual call cannot resolve to a host-side override or vice versa. `constexpr` is largely usable as-is since it's evaluated at compile time on whichever side needs it. For everything about the host-side language itself — templates, the standard library, object lifetime — see [C++](../../programming/cpp/readme.md).
:::

## See also

- [The Compilation Model](./the-compilation-model.md) — how `__host__` and `__device__` functions end up compiled twice.
- [Constant and Texture Memory](../04-cuda-memory-model/constant-and-texture-memory.md) — the memory space `__constant__` variables occupy.
- [C++](../../programming/cpp/readme.md) — the host-side language these qualifiers extend.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
