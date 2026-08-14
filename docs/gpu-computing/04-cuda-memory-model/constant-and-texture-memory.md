---
id: constant-and-texture-memory
title: Constant and Texture Memory
sidebar_label: Constant & Texture
sidebar_position: 6
tags: [gpu, cuda, memory, texture]
---

# Constant and Texture Memory

Global memory's performance rules assume threads in a warp want *different* addresses and reward spreading them out into distinct sectors. Constant memory and the read-only data path invert that assumption: they're fast precisely when a warp's threads all want the *same* data, and the further a kernel's access pattern gets from that, the less either buys over an ordinary global read.

## Constant memory

`__constant__` declares a fixed-size, read-only-from-the-device global variable, populated from the host before launch with `cudaMemcpyToSymbol`:

```cpp
__constant__ float coeffs[16];
```

```cpp
CUDA_CHECK(cudaMemcpyToSymbol(coeffs, hostCoeffs, sizeof(hostCoeffs)));
```

See [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) for what `CUDA_CHECK` does with the status this call returns. Constant memory has a hard **64 KB** total limit across a whole program — it's sized for small, broadly-shared data like a filter's coefficients or a small lookup table, not for anything approaching the scale of an ordinary global allocation.

## The broadcast rule

The whole point of constant memory is this rule: reads through it are fast when every thread in a warp reads the **same** address — the access broadcasts from a dedicated constant cache in a single cycle — and the cost degrades roughly linearly as threads diverge onto more distinct addresses within the warp, down to the cost of 32 separate reads if every thread wants something different. This is the mirror image of the coalescing rule for global memory: coalescing rewards *spreading* a warp's addresses across consecutive locations, while constant memory rewards *collapsing* them onto the same one. Using constant memory for data that different threads in a warp read differently gets you none of its benefit and can be worse than an ordinary global read.

## The read-only data cache

Global data a kernel only ever reads for the kernel's lifetime can route through a separate read-only data cache instead of (or alongside) the ordinary L1 path — [Cache Hierarchy](../02-gpu-hardware-architecture/cache-hierarchy.md) covers this cache as part of the SM's overall cache structure. The intrinsic `__ldg()` forces a load through this path explicitly:

```cpp
float v = __ldg(&data[i]);
```

:::note[Automatic routing since CC 3.5]
This automatic routing has been in place since compute capability 3.5 (Kepler GK110), alongside `__ldg` itself, so it holds on every GPU generation this section covers — see [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).
:::

The compiler routes eligible loads through the read-only path automatically whenever it can prove a pointer is `const` and `__restrict__`-qualified, without needing `__ldg()` written explicitly:

```cpp
__global__ void auto_readonly(const float* __restrict__ data, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        out[i] = data[i] * 2.0f;  // routed through the read-only cache automatically
    }
}
```

Because of that automatic routing, explicit `__ldg()` is mostly a legacy idiom now — it still works, and remains useful when the compiler can't establish read-only-ness on its own (an aliased pointer it can't rule out, for instance), but on current compilers `const __restrict__` gets you the same result in the overwhelming majority of cases without touching the intrinsic at all.

## Texture objects

Textures are a different mechanism again: a **texture object** (`cudaTextureObject_t`) binds a region of memory with an interpretation — dimensionality, addressing mode, filtering — and reads go through dedicated texture hardware rather than the ordinary load path.

```cpp
cudaTextureObject_t tex = 0;
cudaResourceDesc resDesc = {};
resDesc.resType = cudaResourceTypeLinear;
resDesc.res.linear.devPtr = devData;
resDesc.res.linear.desc = cudaCreateChannelDesc<float>();
resDesc.res.linear.sizeInBytes = n * sizeof(float);

cudaTextureDesc texDesc = {};
texDesc.readMode = cudaReadModeElementType;

CUDA_CHECK(cudaCreateTextureObject(&tex, &resDesc, &texDesc, nullptr));
```

:::note[Texture references are removed]
Older CUDA code binds textures with **texture references** (`texture<float, 1>` global declarations plus `cudaBindTexture`). That API is removed, not merely deprecated, in current CUDA — only texture objects exist now. Treat any texture-reference example as historical.
:::

## When textures still pay off

The honest verdict: texture objects are worth reaching for when a kernel has genuine 2-D or 3-D spatial locality that doesn't fit the linear-address assumptions the rest of this page makes, when hardware bilinear/trilinear interpolation replaces code you'd otherwise write by hand, or when the free boundary-clamping modes save an explicit bounds check at every edge. They are not a general-purpose fast path for ordinary linear data — for a simple 1-D array that's already read-only and `__restrict__`-qualified, the automatic read-only-cache routing above gets most of the benefit with none of the setup.

## See also

- [Memory Spaces Overview](./memory-spaces-overview.md) — where constant and texture memory sit relative to global and shared memory.
- [Function Qualifiers](../03-cuda-programming-model/function-qualifiers.md) — `__constant__` alongside the other declaration-space qualifiers.
- [Stencil and Convolution](../13-applied-kernels-and-patterns/stencil-and-convolution.md) — a kernel where constant-memory coefficients and 2-D spatial locality both apply.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
