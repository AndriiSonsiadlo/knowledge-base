---
id: vulkan-and-directx-compute
title: Vulkan and DirectX Compute
sidebar_label: Vulkan & DirectX
sidebar_position: 6
tags: [gpu, vulkan, directx, compute-shaders]
---

# Vulkan and DirectX Compute

Vulkan and Direct3D 12 are graphics APIs first, and each exposes a compute pipeline as a sibling of its graphics pipeline rather than a separate product. The reason to reach for one of them is almost never raw compute throughput — it's what happens on either side of the kernel. If a compute pass writes into a buffer or texture that a render pass reads next, doing both in the same API keeps the data on the device, in the API's own memory model, with no cross-API copy and no synchronization handoff between two separate runtimes. That's the entire case for this page: not "Vulkan compute is fast," but "Vulkan compute is already where your renderer lives."

## Compute in a graphics API

A CUDA or HIP program that also needs to put pixels on screen has to interoperate with a separate graphics API — register a buffer with `cudaGraphicsGLRegisterBuffer` or the Vulkan/D3D12 external-memory extensions, map it, synchronize across the boundary, and hope the driver's interop path is well-tested for that pairing. Doing the compute work as a Vulkan or D3D12 compute shader sidesteps the whole problem: the buffer a compute shader writes is the same `VkBuffer` (or D3D12 resource) a graphics pipeline binds next, in the same command queue, ordered by the same barriers. A particle simulation that updates positions on the GPU and immediately renders them, a post-processing pass, or a physics step feeding a render pass are the workloads this actually fits.

## The Vulkan setup

Vulkan's compute path reuses the same object model as its graphics path: a `VkDevice`, one or more queues, a `VkPipeline` built from a `VkShaderModule` and a `VkPipelineLayout`, and `VkDescriptorSet`s that bind buffers and images to the shader's expected slots. A compute dispatch is recorded into a command buffer like any other Vulkan command — `vkCmdBindPipeline`, `vkCmdBindDescriptorSets`, `vkCmdDispatch(x, y, z)` — and submitted to a queue that supports the `VK_QUEUE_COMPUTE_BIT`, which on most hardware is the same queue graphics work uses.

## GLSL compute shaders

Vulkan consumes SPIR-V, and GLSL compiled through `glslangValidator` or `glslc` is the most common source language for it. A GLSL compute shader declares its work-group size, its buffer bindings, and any push constants explicitly:

```glsl showLineNumbers
#version 450
layout(local_size_x = 256) in;

layout(std430, binding = 0) buffer InBuf  { float x[]; };
layout(std430, binding = 1) buffer OutBuf { float y[]; };
layout(push_constant) uniform Params { float a; int n; };

void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i < uint(n)) y[i] = a * x[i] + y[i];
}
```

`layout(local_size_x = 256) in` fixes the work-group size at shader compile time — the GLSL equivalent of choosing a CUDA block size. `std430` is a buffer layout rule that determines how the compiler packs `InBuf` and `OutBuf`'s members, matching the layout the host side must use when writing those buffers. `layout(push_constant)` declares a small block of data pushed directly into the command buffer rather than bound as a descriptor — the cheapest way to pass a handful of scalars like `a` and `n` into a shader without allocating a uniform buffer for them. `gl_GlobalInvocationID.x` is GLSL's name for the flattened global index, playing the role `blockIdx.x * blockDim.x + threadIdx.x` plays in CUDA.

## HLSL and DirectCompute

Direct3D 12's compute shaders are written in HLSL and compiled to DXIL. The same SAXPY, in HLSL:

```hlsl showLineNumbers
RWStructuredBuffer<float> x : register(u0);
RWStructuredBuffer<float> y : register(u1);

cbuffer Params : register(b0) {
    float a;
    int n;
};

[numthreads(256, 1, 1)]
void main(uint3 dtid : SV_DispatchThreadID) {
    uint i = dtid.x;
    if (i < (uint)n) y[i] = a * x[i] + y[i];
}
```

`[numthreads(256, 1, 1)]` is HLSL's work-group size declaration, equivalent to GLSL's `layout(local_size_x = 256) in`. `RWStructuredBuffer<float>` is a read-write structured buffer bound to a `u`-register — HLSL's unordered-access-view slot, the counterpart of a GLSL `std430 buffer` block. `SV_DispatchThreadID` is a system-value semantic that HLSL binds automatically to the invocation's global position, the same role `gl_GlobalInvocationID` plays in GLSL.

A terminology row belongs alongside the CUDA/SYCL/OpenCL mapping in [SYCL and oneAPI](./sycl-and-oneapi.md#the-terminology-mapping-table): a graphics API's **workgroup** is a CUDA **block**, its **invocation** is a CUDA **thread**, its **subgroup** is a CUDA **warp**, and its shader-declared `shared` block plays the role `__shared__` plays in a CUDA kernel.

## Graphics interop

The payoff shows up in the command stream, not the shader. A frame that dispatches a compute shader to update a vertex buffer, inserts a `VkBufferMemoryBarrier` (or a D3D12 resource barrier) to make the write visible, and then issues a draw call that reads that same buffer never leaves the GPU and never crosses an API boundary. The barrier is the whole synchronization mechanism — no host-side `wait()`, no separate context to schedule against, because the graphics and compute work were always in the same command buffer.

## When this is the right choice

Set against that payoff is a genuinely large amount of host-side ceremony that has nothing to do with the computation itself: descriptor set layouts and pipeline layouts must be declared up front and match the shader's expectations exactly, command buffers must be explicitly allocated and recorded, barriers must be inserted by hand at every point a resource changes how it's used, and memory must be allocated against an explicit memory type chosen from the device's reported heaps — none of which a CUDA `<<<grid, block>>>` launch or a `cudaMalloc` call asks for. That ceremony is the reason not to pick Vulkan or DirectX for pure compute with no graphics component: [OpenCL](./opencl.md) and [SYCL](./sycl-and-oneapi.md) both reach the same SPIR-V target with a fraction of the boilerplate, because neither one is also solving the graphics-pipeline problem. Reach for this page's APIs when the compute result feeds a render pass in the same frame; reach for a general compute API everywhere else.

:::note[Subgroup operations are the portable analogue of warp intrinsics]
Vulkan's `GL_KHR_shader_subgroup` extension (and its HLSL wave-intrinsic equivalent) exposes cross-invocation operations — broadcast, ballot, reduction — within a subgroup, the graphics-API term for the hardware unit CUDA calls a warp. The catch is that subgroup size is not fixed by the API: it varies by vendor and even by pipeline, and a portable shader must query it at pipeline-creation time (`VkPhysicalDeviceSubgroupProperties`) rather than assume 32 or 64, the way a warp-synchronous CUDA kernel can assume 32.
:::

## See also

- [WebGPU](./webgpu.md) — a browser-safe subset of the same compute-in-a-graphics-API idea, with WGSL instead of GLSL or HLSL.
- [OpenCL](./opencl.md) — the lower-ceremony choice when there is no graphics pipeline to interoperate with.
- [Metal and Apple Silicon](./metal-and-apple-silicon.md) — Apple's equivalent graphics-and-compute API, with a very different memory model underneath it.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
