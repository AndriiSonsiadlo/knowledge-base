---
id: sycl-and-oneapi
title: SYCL and oneAPI
sidebar_label: SYCL & oneAPI
sidebar_position: 3
tags: [gpu, sycl, oneapi, intel]
---

# SYCL and oneAPI

SYCL takes a different route to portability than HIP's near-identical-API strategy: instead of translating CUDA calls one-for-one, it's a Khronos standard for expressing host and device code in single-source, standard C++, with the compiler splitting host and device parts of the same file at compile time. The same `.cpp` file that launches a kernel also defines it, using ordinary lambdas and templates instead of a separate kernel language. oneAPI is Intel's product built around SYCL — a toolchain, a compiler, and a set of libraries — but SYCL itself is vendor-neutral and has multiple independent implementations.

## Single-source C++

A complete SAXPY makes the shape concrete, and lines up directly with the CUDA version from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md):

```cpp showLineNumbers title="saxpy.cpp"
#include <sycl/sycl.hpp>

int main() {
    sycl::queue q{sycl::default_selector_v};
    const int n = 1 << 20;

    float* x = sycl::malloc_device<float>(n, q);
    float* y = sycl::malloc_device<float>(n, q);
    // ... fill x and y ...

    q.parallel_for(sycl::range<1>(n), [=](sycl::id<1> i) {
        y[i] = 2.0f * x[i] + y[i];
    }).wait();

    sycl::free(x, q);
    sycl::free(y, q);
}
```

`sycl::queue` is where CUDA's implicit default stream became an explicit, constructed object; `q.parallel_for(...)` is where `saxpy<<<blocks, threads>>>(...)` became a call taking an iteration space and a lambda instead of a special launch syntax. There is no separate `.cu`-style kernel file and no `__global__` — the kernel is just the lambda passed to `parallel_for`, compiled for the device by the same compiler that compiles the host code around it.

## Queues

`sycl::queue` is the SYCL analog of a CUDA stream: an ordered (by default) or out-of-order sequence of work submitted to one device. Constructing a queue against a *selector* — `sycl::default_selector_v` above, or a more specific GPU/CPU selector — is how SYCL decides which physical device the queue's work actually targets, which is also the point at which portability across vendors gets resolved: the same source recompiles against whichever backend the queue ends up bound to.

## Buffers and accessors

SYCL 2020 has two distinct memory models, and choosing between them is a real design decision, not a stylistic one. **Buffers and accessors** wrap data in a `sycl::buffer` and declare intent to read or write it through `sycl::accessor` objects; the SYCL runtime inspects those accessor declarations and builds a dependency graph automatically, inserting the copies and waits itself — no explicit `memcpy`, no explicit `wait()` between dependent kernels. That automatic scheduling is the buffer model's whole value: it is harder to get a data race or a missing synchronization wrong, at the cost of the runtime making scheduling decisions for you.

## Unified shared memory

**USM** (unified shared memory) — the model the SAXPY example above uses — is pointer-based: `sycl::malloc_device` returns a raw device pointer, moving data is an explicit `q.memcpy(...)`, and ordering between kernels is an explicit `.wait()` or event dependency. This is the model a CUDA programmer will recognize immediately, because it's structurally identical to `cudaMalloc`/`cudaMemcpy`. Prefer USM when porting existing pointer-based CUDA code, or when explicit control over transfers and ordering matters; prefer buffers/accessors for new code where the runtime's automatic dependency tracking is worth more than manual control.

### Work-group structure with `nd_range`

For kernels that need block-style structure — a fixed group size, and memory shared within that group — `parallel_for` takes an `nd_range` instead of a flat `range`, and the kernel receives an `nd_item` instead of a flat `id`. `sycl::local_accessor` is the equivalent of a `__shared__` array, scoped to one work-group:

```cpp showLineNumbers
q.submit([&](sycl::handler& h) {
    sycl::local_accessor<float, 1> tile(sycl::range<1>(256), h);
    h.parallel_for(sycl::nd_range<1>(sycl::range<1>(n), sycl::range<1>(256)),
        [=](sycl::nd_item<1> item) {
            int local_id = item.get_local_id(0);
            tile[local_id] = /* ... */;
            item.barrier(sycl::access::fence_space::local_space);
        });
});
```

`nd_range` packages the global iteration space and the local (work-group) size together — the SYCL equivalent of choosing a CUDA block size — and `item.barrier(...)` is the work-group-wide synchronization point, playing the role `__syncthreads()` plays in CUDA.

### The terminology mapping table

CUDA, SYCL, and OpenCL describe the same hierarchy of parallelism with three different vocabularies; SYCL and OpenCL happen to use identical terms for it, since SYCL was built on OpenCL's execution model:

| CUDA | SYCL | OpenCL |
|---|---|---|
| Thread | Work-item | Work-item |
| Block | Work-group | Work-group |
| Grid | `nd_range` | NDRange |
| Shared memory | Local memory | Local memory |

Say the CUDA term once for orientation and then use each stack's native vocabulary — a SYCL kernel operates on work-items in a work-group, not on "threads in a block."

## DPC++ and the backends

DPC++ is Intel's open-source SYCL implementation (the basis of oneAPI's compiler); AdaptiveCpp is an independent open-source implementation. Both compile the same standard SYCL source, but which backends a given implementation targets varies. DPC++ can target Intel GPUs directly through Level Zero, and can target NVIDIA and AMD GPUs through backends built with Codeplay's oneAPI plugins — CUDA for NVIDIA, HIP for AMD:

```bash
icpx -fsycl -fsycl-targets=nvptx64-nvidia-cuda saxpy.cpp -o saxpy
```

## Running on NVIDIA and AMD

That a single SYCL source can target Level Zero, CUDA, and HIP from the same `.cpp` file is the concrete case for SYCL as a portability layer: the terminology, the memory models, and the kernel code all stay the same, and only the `-fsycl-targets` flag (and the resulting codegen) changes per vendor. It does not mean the generated code performs identically across those three backends — see [The Portability Problem](./the-portability-problem.md) for why that is a separate, harder claim.

:::note[SYCL is a standard, oneAPI is a product]
SYCL is a Khronos open standard with several independent implementations — DPC++ and AdaptiveCpp among them. oneAPI is Intel's toolchain and library ecosystem, built around SYCL as its programming model, but SYCL code is not tied to Intel or to oneAPI specifically.
:::

## See also

- [OpenCL](./opencl.md) — the lower-level standard SYCL builds its execution model on top of.
- [HIP and ROCm](./hip-and-rocm.md) — the alternative portability strategy of translating the CUDA API directly instead of using single-source C++.
- [Choosing a Portability Layer](./choosing-a-portability-layer.md) — how SYCL's tradeoffs compare against HIP, OpenCL, and directive-based offload.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
