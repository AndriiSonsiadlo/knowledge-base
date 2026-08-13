---
id: register-file-and-occupancy
title: The Register File and Occupancy
sidebar_label: Registers & Occupancy
sidebar_position: 4
tags: [gpu, hardware, registers, occupancy]
---

# The Register File and Occupancy

Occupancy is defined in the [glossary](../00-overview/glossary.md) as the ratio of resident warps to the maximum an SM supports, and [Latency, Throughput, and Latency Hiding](../01-parallel-computing-foundations/latency-throughput-and-hiding.md) explains why that ratio matters — resident warps are what supply the concurrent memory requests Little's Law demands. This page is about the other half: occupancy is not a tunable dial, it's the *output* of a fixed calculation against fixed hardware limits, and the register file is usually the tightest of those limits.

## The register file is the scarce resource

Every thread's local variables live in registers for as long as the thread is resident, and the hardware never spills a live thread's registers to make room for another thread — a launch that requests more registers per thread simply leaves less of the register file, and therefore fewer resident threads, available. Because registers are the fastest storage on the chip and every thread needs some, they're also the resource a kernel runs out of first far more often than shared memory or thread slots. [The Streaming Multiprocessor](./streaming-multiprocessor.md) covers the register file's physical layout — one slice per sub-partition, 65,536 32-bit registers total per SM on Hopper (compute capability 9.0), the number this page's worked example uses.

## Occupancy is a hardware-limit calculation

The number of blocks the hardware can keep resident on an SM simultaneously is capped independently by three resources: the register file, the shared-memory pool, and a fixed hardware limit on the number of resident blocks and threads. Each cap, computed on its own, gives a maximum number of blocks per SM; the SM can only run as many blocks as the *most restrictive* of the three allows, so occupancy is the minimum across all three, never an average or a sum.

## The three limiters

- **Registers.** Divide the SM's total register count by the registers a single block consumes (registers per thread × threads per block, subject to allocation granularity — see below) to get the register-limited blocks/SM.
- **Shared memory.** Divide the SM's usable shared-memory capacity by the shared memory a single block requests to get the shared-memory-limited blocks/SM.
- **Block and thread slots.** Every SM has a fixed maximum number of resident threads (2048 on an H100 SM, compute capability 9.0) and a fixed maximum number of resident blocks (32 on Hopper), regardless of how frugal a kernel is with registers and shared memory. Dividing max resident threads by threads/block gives the thread-slot-limited blocks/SM; the hardware block-count cap applies on top of that.

## Worked example

Take a kernel launched with 256 threads/block, using 64 registers/thread and 48 KB of shared memory per block, on an SM with 65,536 registers and 164 KB of usable shared memory (an Ampere-class, compute capability 8.0, figure — a smaller pool than Hopper's, chosen here because it's the shared-memory number that makes this example bind on that limiter rather than only on registers). Max resident threads/SM is 2048.

**Registers.** A block needs 64 registers/thread × 256 threads/block = 16,384 registers. This assumes no rounding loss from register allocation granularity: registers are actually allocated per warp, not per thread, in fixed-size chunks (commonly a multiple of 256 registers per warp on recent architectures), and 64 registers/thread × 32 threads/warp = 2,048 registers/warp is already an exact multiple of that granularity, so the naive per-thread multiplication and the per-warp accounting agree here. With a registers-per-thread count that didn't divide evenly into the allocation granularity, the per-block total would round up and this step would need re-deriving from the per-warp figure instead.

```text
blocks/SM (registers) = 65,536 / 16,384 = 4
```

**Shared memory.** A block needs 48 KB.

```text
blocks/SM (shared memory) = 164 KB / 48 KB = 3.41... -> 3
```

(Blocks are indivisible, so this rounds down — a 4th block would need 192 KB, more than the 164 KB available.)

**Block and thread slots.** 256 threads/block against a 2048-thread/SM ceiling:

```text
blocks/SM (threads) = 2048 / 256 = 8
```

8 is also under the fixed 32-block/SM hardware cap on this generation, so the thread-slot limiter stays at 8.

**Take the minimum.** Registers allow 4, shared memory allows 3, thread slots allow 8 — the binding constraint is shared memory, at **3 blocks/SM**.

```text
occupancy = min(4, 3, 8) = 3 blocks/SM
          = 3 x 256 = 768 resident threads / 2048 max
          = 37.5% occupancy
```

Note that the register limiter (4 blocks) was not the binding one in this example — shared memory was — which is exactly the kind of result you can't guess without running all three numbers; a kernel tuned only against its register count could still be shared-memory-bound.

`cudaOccupancyMaxActiveBlocksPerMultiprocessor` computes exactly this minimum for you, given a kernel's actual register and shared-memory usage — you don't hand-compute it in practice. Its use in choosing a launch configuration is covered in [Choosing a Launch Configuration](../03-cuda-programming-model/launch-configuration.md); this page exists so the number it returns is not a black box.

## Why maximum occupancy is not the goal

Occupancy is necessary for latency hiding, not sufficient for speed. A kernel that is compute-bound rather than latency-bound can run at full speed with far less than 100% occupancy, because it never has enough idle cycles for extra resident warps to fill. Pushing occupancy higher by cutting registers per thread can even make a kernel slower: fewer registers per thread means the compiler runs out of room to keep live values on-chip and starts **spilling** them to local memory — which physically lives in the same DRAM/L2 path as global memory — trading a register-file hit for an actual memory round trip on every spilled access. A modest occupancy loss is often cheaper than a spill. [Registers and Local Memory](../04-cuda-memory-model/registers-and-local-memory.md) covers what a spill costs and how to see one in generated code; [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) covers the practical tradeoffs between raising occupancy and avoiding this trap.

:::warning[Cutting registers to raise occupancy can cost more than it gains]
Forcing a lower register count per thread — via `-maxrregcount` or a `__launch_bounds__` annotation — can raise the blocks/SM the register limiter allows, but if the kernel's live-value set doesn't actually fit in the new, smaller register budget, the compiler spills the overflow to local memory. The resulting kernel can have *higher* occupancy and be *slower*, because spills add real memory traffic that the extra resident warps don't fully hide. See [Registers and Local Memory](../04-cuda-memory-model/registers-and-local-memory.md) before reaching for this lever.
:::

## See also

- [The Streaming Multiprocessor](./streaming-multiprocessor.md) — the physical register file and shared-memory pool this calculation draws its inputs from.
- [Warps and Warp Schedulers](./warps-and-schedulers.md) — what the scheduler does with however many warps this calculation leaves resident.
- [Choosing a Launch Configuration](../03-cuda-programming-model/launch-configuration.md) — using `cudaOccupancyMaxActiveBlocksPerMultiprocessor` in practice instead of hand-computing it.
- [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md) — the practical levers for raising occupancy and when to stop.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
