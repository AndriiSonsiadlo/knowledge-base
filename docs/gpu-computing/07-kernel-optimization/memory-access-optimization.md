---
id: memory-access-optimization
title: Memory Access Optimization
sidebar_label: Memory Access
sidebar_position: 3
tags: [gpu, cuda, optimization, coalescing]
---

# Memory Access Optimization

[Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) establishes the 32-byte-sector model and works out the arithmetic for coalesced, strided, and AoS access patterns. This page turns that model into an ordered checklist for a memory-bound kernel: which lever to pull first, which to skip, and why the order matters more than any individual technique.

## Coalescing first

Fix the access pattern before reaching for anything else, because the ceiling every other technique here operates under is set by how many sectors a warp actually touches. The order of payoff, largest first: **layout change (AoS to SoA) > coalescing the access pattern > vectorizing the loads > everything else.** A layout change fixes the root cause across every kernel that touches the data; coalescing an individual access pattern is the next-largest win and is the fix [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) covers in depth; vectorization and the read-only path below are real but smaller wins layered on top of an already-coalesced access — applying them to an uncoalesced kernel wastes effort on the wrong problem, the same trap [The Optimization Workflow](./the-optimization-workflow.md) warns about generally.

## Vectorized loads

Once accesses are coalesced, issuing one 16-byte `float4` load per thread instead of four separate 4-byte loads reduces the instruction count for the same data:

```cpp showLineNumbers
__global__ void scaleVec4(float4* data, int n4, float a) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n4) {
        float4 v = data[i];              // one 16-byte load per thread
        v.x *= a; v.y *= a; v.z *= a; v.w *= a;
        data[i] = v;
    }
}
```

`n4` here is the element count in `float4` units, not `float` units — if the underlying buffer has `n` `float`s, `n4 = n / 4`, and `n` must be divisible by 4 or the remaining tail elements need a separate scalar pass. The `float4*` reinterpretation of an existing `float*` buffer also carries an alignment precondition: the base pointer must be 16-byte aligned, which `cudaMalloc` guarantees for its returned base address but which an *offset* into that allocation does not necessarily preserve — check alignment at the point of the cast, as [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) notes for the same reinterpret-cast pattern.

Why this helps is mechanical, not magical: fewer, wider memory instructions mean fewer requests in flight per byte moved, which relieves pressure on the load/store unit and the memory-instruction scoreboard. It does **not** move more bytes than a fully coalesced scalar access already does — a warp of coalesced `float` loads and a warp of coalesced `float4` loads touch the same number of sectors for the same data. The win is in instruction and request overhead, not in bandwidth a scalar coalesced access was somehow leaving on the table.

## Alignment

The `float4` precondition above generalizes: any vector load type (`float2`, `float4`, `int4`) requires the accessed address to be aligned to the vector's size, and a misaligned vector load is either slower or outright illegal depending on the architecture. When a buffer's natural size isn't a multiple of the vector width, pad the allocation rather than letting the last few elements force a fallback to scalar loads for the whole kernel.

## Layout changes

Ranked first above for a reason: switching a struct-of-arrays-eligible kernel from AoS to SoA fixes the coalescing problem at its source rather than working around it access-by-access. [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) works the exact numbers — a single-field update on an AoS layout touches 16 sectors for 128 useful bytes (25% efficiency) versus 4 sectors at 100% efficiency for the SoA equivalent. A layout decision made once at the data-structure level benefits every kernel that touches the data afterward, which is why it outranks per-kernel access-pattern fixes.

## The read-only path

Marking a pointer parameter `const __restrict__` tells the compiler two things at once: the data won't be written through this pointer (`const`), and no other pointer in the kernel aliases the same memory (`__restrict__`). Together, those guarantees let the compiler route eligible loads through the GPU's read-only data cache automatically, without the kernel calling `__ldg()` explicitly:

```cpp showLineNumbers
__global__ void axpy(int n, float a, const float* __restrict__ x, float* y) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        y[i] += a * x[i];   // load from x routed through the read-only path automatically
    }
}
```

:::note[Automatic routing since CC 3.5]
This automatic `const __restrict__` routing through the read-only path has been in place since compute capability 3.5 (Kepler GK110), the same generation `__ldg()` itself was introduced on — see [Constant and Texture Memory](../04-cuda-memory-model/constant-and-texture-memory.md). Explicit `__ldg()` calls are largely legacy from before compilers reliably inferred this from `const __restrict__`; on every architecture this section covers, annotating the pointer is sufficient and reads more naturally than the explicit intrinsic.
:::

## Padding

Padding belongs to shared-memory bank conflicts, not global-memory coalescing — the two problems look similar (an access pattern losing bandwidth to a hardware layout) but the fix operates on a different resource. [Shared Memory Tiling](./shared-memory-tiling.md) covers the `TILE + 1` padding pattern in full; nothing about padding a global-memory buffer improves coalescing the way it improves shared-memory bank distribution.

:::warning[Vectorized loads raise register pressure]
Loading a `float4` instead of four separate `float`s means the compiler holds a 16-byte value live in registers at once instead of four values it could otherwise stream through more narrowly. Applying vectorization to a kernel that's already register-constrained can push it into spilling. Check `-Xptxas -v` after applying vectorized loads, the same way [Occupancy Tuning](./occupancy-tuning.md) checks it after `__launch_bounds__`.
:::

## See also

- [Shared Memory Tiling](./shared-memory-tiling.md) — the next step once coalescing and vectorization are exhausted and the kernel still re-reads the same data from DRAM.
- [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) — the sector model and coalescing arithmetic this page's ordering is built on.
- [Registers and Local Memory](../04-cuda-memory-model/registers-and-local-memory.md) — what happens when the warning above is ignored.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
