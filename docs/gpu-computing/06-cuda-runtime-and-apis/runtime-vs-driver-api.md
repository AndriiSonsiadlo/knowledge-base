---
id: runtime-vs-driver-api
title: Runtime API vs Driver API
sidebar_label: Runtime vs Driver API
sidebar_position: 1
tags: [gpu, cuda, runtime, driver-api]
---

# Runtime API vs Driver API

Every CUDA C++ example so far — `<<<grid, block>>>` launches, `cudaMalloc`, `cudaMemcpy` — has gone through the **runtime API**, the high-level interface linked in as `cudart` and initialized implicitly the first time a program touches the GPU. Underneath it sits the **driver API** (`cuda.h`, linked as `cuda`), a lower-level, explicit interface that the runtime itself is built on. Almost nothing in application code needs the driver API directly, but understanding what the runtime is hiding explains a class of errors ("invalid device context") that only make sense once you know a context exists at all.

## Two APIs over one driver

Both APIs talk to the same underlying driver and the same GPU; they differ in how much the programmer has to manage explicitly.

| Concept | Runtime API | Driver API |
| --- | --- | --- |
| Initialization | Implicit, on first CUDA call | Explicit `cuInit(0)` |
| Context | Implicit *primary* context per device, created lazily | Explicit `cuCtxCreate` / `cuCtxSetCurrent`, or retain the primary context |
| Module loading | Kernels compiled and linked in at build time via `nvcc` | Explicit `cuModuleLoad` of a cubin or PTX blob at run time |
| Kernel launch | `kernel<<<grid, block>>>(args...)` | `cuLaunchKernel` with an explicit `void* args[]` array |
| Symbol lookup | Kernel is a named C++ function; globals via `cudaGetSymbolAddress` | `cuModuleGetFunction` / `cuModuleGetGlobal` by string name |
| Error type | `cudaError_t` | `CUresult` |

## Contexts

A CUDA context is the analog of a process on the GPU: it owns the device's address space, its loaded modules, and its allocations. The driver API makes context management explicit — code calls `cuCtxCreate` to create one and `cuCtxSetCurrent` to make it current on a thread. The runtime API hides all of this behind the **primary context**, described below.

## Modules and `cuLaunchKernel`

The runtime API compiles a `.cu` file's `__global__` functions into the executable (or a fatbinary embedded in it) at build time, and `kernel<<<grid, block>>>(a, b, c)` is `nvcc`-generated sugar over a launch that already knows the function's address and argument types. The driver API has no such compile-time link: it loads a cubin or PTX module explicitly with `cuModuleLoad`, looks up the kernel by name with `cuModuleGetFunction`, and launches it with `cuLaunchKernel`, which takes its arguments as an untyped `void* args[]` array instead of a typed parameter list:

```cpp showLineNumbers
// Runtime API
saxpy<<<grid, block>>>(n, a, d_x, d_y);

// Driver API — same launch, made explicit
CUfunction saxpyFn;
CUDA_CHECK(cuModuleGetFunction(&saxpyFn, module, "saxpy"));
void* args[] = { &n, &a, &d_x, &d_y };
CUDA_CHECK(cuLaunchKernel(saxpyFn,
    grid.x, grid.y, grid.z,
    block.x, block.y, block.z,
    0, stream, args, nullptr));
```

The `<<<>>>` syntax is exactly this call with the function handle, argument packing, and error type resolved at compile time instead of at run time.

## The primary context

The runtime API lazily creates and shares a single **primary context** per device, retained for the lifetime of the process (or until `cudaDeviceReset`). Every runtime call on that device operates through this one context. Driver-API code that calls `cuCtxCreate` creates a *separate*, non-primary context — and mixing that context with runtime-API calls on the same thread is the classic source of "invalid device context" errors, because the runtime keeps operating against the primary context while the driver-API code just made a different one current. `cuDevicePrimaryCtxRetain` is the interop path: it hands driver-API code a reference to the *same* primary context the runtime uses, instead of creating a rival one.

## When you need the driver API

:::tip[Use the runtime API]
The honest recommendation is to write runtime-API code by default — it is simpler, less error-prone, and does everything most CUDA programs need. Reach for the driver API only for JIT-loading cubins or PTX at run time (plugin systems, compiler-generated kernels), for managing multiple isolated contexts deliberately, or when writing a language binding that needs the driver's finer-grained control.
:::

:::note[Python has a modern driver-API wrapper]
CUDA 12 added `cuda.core` / `cuda.bindings` on the Python side as a modern wrapper directly over the driver API, replacing the older ad hoc ctypes bindings some projects hand-rolled. See [CUDA Python and CuPy](../08-libraries-and-ecosystem/cuda-python-and-cupy.md).
:::

## See also

- [Device Management](./device-management.md) — enumerating and selecting devices through the runtime API this page recommends.
- [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md) — how `nvcc` turns `__global__` functions into the modules the driver API loads explicitly.
- [CUDA Python and CuPy](../08-libraries-and-ecosystem/cuda-python-and-cupy.md) — where `cuda.core` fits among the Python options.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
