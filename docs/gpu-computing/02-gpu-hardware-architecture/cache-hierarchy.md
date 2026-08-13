---
id: cache-hierarchy
title: Cache Hierarchy
sidebar_label: Cache Hierarchy
sidebar_position: 5
tags: [gpu, hardware, cache, memory]
---

# Cache Hierarchy

A GPU's cache hierarchy looks superficially like a CPU's — an L1 per core-analog, a shared L2 behind it — but the access pattern it's optimized for is completely different. A CPU cache is tuned for one thread's temporal and spatial locality; a GPU's L1 and L2 exist to serve tens of thousands of threads issuing memory requests in 32-wide warps, and the granularity at which those requests are actually served is the fact that explains coalescing, wasted bandwidth, and most of what looks like "mysterious" memory performance on a GPU.

## The unified L1 and shared memory

Since Volta, each SM's L1 data cache and its programmer-managed shared memory occupy the same physical SRAM, split by a configurable carveout rather than existing as separate pools — [The Streaming Multiprocessor](./streaming-multiprocessor.md) covers the per-generation sizes of that combined pool. As a cache, this L1 is private to its SM: it holds recently-touched global-memory lines for the threads currently resident there, with no visibility into what any other SM's L1 holds.

## L2

Behind every SM's private L1 sits one L2 cache shared by the whole GPU, sitting alongside the GPC hierarchy as shown in [Anatomy of a GPU](./anatomy-of-a-gpu.md#top-down). L2 is where cross-SM reuse actually happens — two blocks on different SMs touching the same global-memory region can both hit in L2 even though neither can see the other's L1. It's also the backstop between the SMs and DRAM: an L2 miss is what actually issues a transaction to the memory controllers, so a working set that fits in L2 (tens of megabytes on recent datacenter parts) can run far faster than the raw DRAM bandwidth in [Device Memory and Bandwidth](./device-memory-and-bandwidth.md) would suggest.

## Sectors, not cache lines

The mechanical fact that governs almost everything about GPU memory-access performance: a global-memory line is 128 bytes, but the hardware does not fetch a whole line as one indivisible unit the way a CPU does. It fetches in **32-byte sectors**, four of which make up a 128-byte line, and a memory transaction only pulls in the sectors a warp's addresses actually touch. If a warp's 32 threads access 32 consecutive 4-byte words, those addresses span exactly 128 bytes and land in all four sectors of one line — one fully-utilized transaction. If the same warp instead accesses a strided or scattered pattern that touches only one 4-byte word per sector, the hardware still fetches all four sectors — 128 bytes moved to deliver 4 bytes actually used per sector, an 8x waste. This sector-versus-line distinction *is* the mechanism behind coalescing: a "coalesced" access pattern is exactly one where a warp's addresses concentrate into the fewest possible sectors. [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) works through the access patterns that hit this well and badly.

## The read-only path

Global data that a kernel only ever reads — never writes, for the lifetime of the kernel — can additionally route through a read-only data cache, a separate path from the ordinary L1. The compiler routes eligible loads through it automatically when it can prove the data is `const` and `__restrict__`-qualified; when it can't prove that, the intrinsic `__ldg()` forces a load through the read-only path explicitly. On modern architectures this is largely automatic — the compiler's inference is good enough that hand-inserting `__ldg()` rarely changes generated code — but it remains available as an explicit hint when the compiler can't establish read-only-ness on its own (for example, through a pointer aliased in a way it can't rule out).

:::note[`__ldg` is mostly a legacy explicit form now]
On early architectures where the compiler's automatic detection of read-only, non-aliased data was weaker, `__ldg()` was a common manual optimization. On current compilers and architectures, marking pointers `const __restrict__` gets you the same routing automatically in the overwhelming majority of cases, and `__ldg()` is more often seen in older code or in kernels where aliasing genuinely can't be ruled out by the type system.
:::

## What is and is not cached

Global-memory reads populate L1 and L2 as described above; global-memory *writes* by default do not use L1 as a write-back cache — a write typically goes through to L2 (write-allocate/write-back at the L2 level), leaving L1 as a read-oriented cache for global traffic rather than a full read/write cache the way a CPU's L1 is. Shared memory is a separate matter entirely: it is not a cache at all in the sense used here, since nothing is ever silently evicted and refetched — the programmer explicitly populates and reads it, as covered in [Shared Memory](../04-cuda-memory-model/shared-memory.md).

Compare this to [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md): the ideas of locality and fixed-granularity fetches **carry over directly** — a GPU L1/L2 miss is expensive for the same underlying reason a CPU one is, and the 32-byte-sector-within-a-128-byte-line structure here plays the same practical role as a 64-byte cache line does on a CPU. What does **not** carry over is coherence: a CPU's private per-core L1/L2 are kept consistent by a hardware protocol like MESI, so one core's write becomes visible to another core's cache automatically. A GPU's per-SM L1s have **no such protocol between them** — one SM's L1 can hold a stale copy of data another SM has since written, and the program is only guaranteed a consistent view at synchronization points (kernel boundaries, or explicit fences/atomics within a kernel), not continuously the way MESI provides on a CPU. Combined with L1 not being write-back for global memory by default, this means a GPU's cache hierarchy trades away automatic cross-core consistency for much higher aggregate throughput across far more concurrent threads than any CPU coherence protocol targets.

## See also

- [Device Memory and Bandwidth](./device-memory-and-bandwidth.md) — what happens once a request misses L2 and reaches DRAM.
- [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md) — access patterns that make the sector mechanism above work for or against you.
- [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) — the coherence protocol and write-back model that GPU L1 does not provide.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
