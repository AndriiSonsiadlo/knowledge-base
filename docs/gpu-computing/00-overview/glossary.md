---
id: glossary
title: Glossary
sidebar_label: Glossary
sidebar_position: 6
tags: [gpu, overview, glossary, terminology]
---

# Glossary

This page collects the vocabulary the rest of the section assumes, in one alphabetical list rather than grouped by topic, so it works as a lookup target rather than something you read start to finish. Each entry is written to stand alone — you should be able to land here from a search result with no other context and still understand the term — and each ends with a link to the page that develops it properly, with worked examples and the surrounding detail this page deliberately omits.

## Terms

### Arithmetic intensity

The ratio of floating-point operations performed to bytes moved from DRAM, expressed in FLOPs/byte. It is the single number that predicts whether a kernel's ceiling is set by the arithmetic units or by the memory system: below the machine's balance point (peak TFLOPS divided by peak bandwidth) a kernel is memory-bound and faster ALUs change nothing, above it a kernel is compute-bound and faster memory changes nothing. See [Arithmetic Intensity and Roofline](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md).

### Bank conflict

A stall that occurs when multiple threads in the same warp access shared memory addresses that map to the same memory bank in the same transaction, forcing the accesses to serialize instead of completing in one cycle. Shared memory is organised into 32 banks precisely so a full warp can normally be served at once; a conflicting access pattern — most commonly a stride that is a multiple of the bank count — turns one fast transaction into several slow ones. See [Bank Conflicts](../04-cuda-memory-model/bank-conflicts.md).

### Coalescing

The property that the 32 threads of a warp issue a global-memory access whose addresses fall into the minimum number of memory transactions the hardware can serve at once, typically because consecutive threads touch consecutive addresses. A coalesced access uses the full width of a fetched cache line; an uncoalesced one — scattered, strided, or transposed — wastes most of the bytes each transaction brings back, and is the most common reason a ported kernel runs far below the advertised bandwidth. See [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md).

### Compute capability

NVIDIA's versioning scheme for GPU architecture generations, written as a major.minor number (for example 7.0 for Volta, 9.0 for Hopper, 10.0 for Blackwell datacenter parts). It is the axis every hardware-gated feature is pinned to — independent thread scheduling requires 7.0+, thread block clusters require 9.0+ — so a feature or an intrinsic's availability is stated as a compute-capability floor rather than a product name. See [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).

### Cooperative group

A programming-model abstraction, introduced with the Cooperative Groups API, that names an explicit, arbitrarily-shaped set of threads — a warp tile, a block, a cluster, or an entire grid — as a first-class object you can synchronize and communicate through, rather than relying on the implicit warp/block granularity `__syncthreads()` offers. It is what makes grid-wide synchronization and flexible sub-warp operations expressible without hand-rolled primitives. See [Cooperative Groups](../05-execution-and-synchronization/cooperative-groups.md).

### CUDA core

The marketing name for a single scalar floating-point/integer ALU lane inside a streaming multiprocessor — the unit that executes one thread's arithmetic instruction per cycle when the warp scheduler issues it. A GPU's "core count" is the sum of these lanes across all SMs, which is why it is not directly comparable to a CPU's core count: a CUDA core has no independent instruction stream, no scheduler of its own, and does nothing outside the warp it belongs to. See [Streaming Multiprocessor](../02-gpu-hardware-architecture/streaming-multiprocessor.md).

### Divergence

What happens when threads within the same warp take different paths through a conditional, because the hardware issues one instruction stream per warp. The GPU executes each taken branch path in sequence with the threads not on that path masked off, so a fully divergent warp runs at a fraction of its peak — the cost is the sum of the branch arms, not the longest one. See [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md).

### Grid / block / thread

The three-level hierarchy a CUDA kernel launch is organised into: a grid is the whole launch, made of blocks; a block is a group of threads that can share memory and synchronize together via `__syncthreads()`, scheduled as a unit onto one SM; a thread is a single logical instance of the kernel, distinguished from its siblings by its index within the block and grid. The launch configuration `` `<<<grid, block>>>` `` sets the grid and block dimensions at the point a kernel is called. See [Threads, Blocks, and Grids](../03-cuda-programming-model/threads-blocks-and-grids.md).

### HBM

High Bandwidth Memory, a stacked-DRAM technology connected to the GPU die through a very wide interposer bus, trading capacity and cost for bandwidth far beyond what a conventional DIMM or GDDR interface reaches — an H100 SXM's HBM3, for example, delivers roughly 3.35 TB/s. Datacenter GPUs use HBM; consumer GPUs typically use cheaper, narrower GDDR instead, which is the main reason a consumer card's real-world throughput on bandwidth-bound kernels lags its datacenter counterpart by more than the FLOPS numbers suggest. See [Device Memory and Bandwidth](../02-gpu-hardware-architecture/device-memory-and-bandwidth.md).

### Host and device

The standard CUDA terms for, respectively, the CPU and its system memory (the host) and the GPU and its own memory (the device). Code and data start on the host; a kernel launch transfers execution to the device, and any result the host needs must be explicitly copied back — there is no implicit sharing unless the program opts into unified memory. Almost every CUDA API name reflects this split (`cudaMemcpyHostToDevice`, `__host__`, `__device__`). See [The Host/Device Model](../01-parallel-computing-foundations/the-host-device-model.md).

### Kernel

A function written to run on the GPU, launched from host code with the `` `<<<grid, block>>>` `` syntax and executed once per thread across the launch's entire thread hierarchy, marked with the `` `__global__` `` qualifier. A kernel launch is asynchronous with respect to the host by default — the host call returns immediately, and the work runs on the device's queue. See [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md).

### Occupancy

The ratio of warps actually resident on a streaming multiprocessor to the maximum the hardware supports, determined by how much of each per-SM resource — registers, shared memory, and the fixed number of thread/block slots — a launch configuration consumes. Occupancy matters because resident warps are the mechanism that hides memory latency: too few resident warps and the scheduler sometimes has no ready warp to switch to, exposing stalls that would otherwise be free. High occupancy is not automatically fast, but low occupancy on a latency-bound kernel usually is slow. See [Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md).

### PTX

Parallel Thread Execution, NVIDIA's intermediate assembly-like instruction set that `nvcc` compiles CUDA C++ down to. PTX is forward-compatible and architecture-generic — it is what lets a single compiled artifact run, via JIT recompilation by the driver, on GPU generations newer than the one it was built for. It sits between source code and the machine-specific instructions a given GPU actually executes. See [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md).

### Quantization

Reducing the numeric precision used to represent weights and activations — typically from FP32 or FP16 down to INT8, INT4, or an FP8 variant — to cut memory footprint and increase the throughput of accelerators (tensor cores and NPUs alike) whose low-precision paths are wider than their high-precision ones. It trades some model accuracy for a substantial gain in throughput and energy efficiency, and is close to mandatory for deploying a model on an NPU, whose dataflow is often fixed at low precision entirely. See [Quantization for Accelerators](../12-npu-and-inference-accelerators/quantization-for-accelerators.md).

### Roofline

A performance model that plots achievable performance (in FLOP/s) against arithmetic intensity (in FLOP/byte), with a diagonal "memory roof" rising until it meets a flat "compute roof" at the machine's balance point. Placing a kernel's measured intensity and throughput on the plot tells you immediately which roof is limiting it and how much headroom is theoretically available before you touch a single line of code. See [Roofline in Practice](../09-tooling-profiling-and-debugging/roofline-in-practice.md).

### SASS

Streaming Assembler, the actual machine code a given GPU architecture executes — the final compilation target after PTX is translated for a specific compute capability. Unlike PTX, SASS is architecture-specific and not forward-compatible; it is what a disassembler or `cuobjdump` shows you when you need to see exactly what instructions a kernel compiled down to. See [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md).

### Shared memory

A small, fast, software-managed scratchpad memory local to each streaming multiprocessor, explicitly allocated and populated by kernel code (as opposed to a hardware-managed cache) and shared by every thread in a block. It is one of the primary levers of kernel optimization — staging data in shared memory once and reusing it across threads avoids repeated trips to global memory — but it is small, and poorly-patterned access to it causes bank conflicts. See [Shared Memory](../04-cuda-memory-model/shared-memory.md).

### SM (streaming multiprocessor)

The GPU's core processing unit — analogous in role, though not in design, to a CPU core — containing warp schedulers, a large register file, ALUs (CUDA cores and, on recent architectures, tensor cores), and the on-chip shared memory/L1 cache. A GPU is built from many SMs (132 on an H100 SXM, for example); a block is scheduled onto exactly one SM for its entire lifetime, and everything about occupancy and residency is accounted per SM. See [Streaming Multiprocessor](../02-gpu-hardware-architecture/streaming-multiprocessor.md).

### Stream

An ordered queue of GPU operations — kernel launches, memory copies, events — that execute in issue order within the stream but, on the default asynchronous model, can run concurrently with operations in a different stream. Streams are the mechanism behind overlapping a transfer with a computation instead of paying for them serially, and behind running independent kernels side by side on the same device. See [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md).

### Tensor core

A fixed-function matrix-multiply-accumulate unit built into each SM from Volta onward, computing a small matrix product (for example a 4×4 by 4×4 tile) per instruction at reduced precision — originally FP16, now spanning TF32, BF16, FP8, and FP4 on Blackwell — at throughput far above the SM's general-purpose FP32 lanes. Reaching a tensor core's peak requires the operands to be laid out and typed the way it expects; a matrix multiply that doesn't route through it leaves most of the SM's arithmetic throughput unused. See [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md).

### TFLOPS

Trillions (10¹²) of floating-point operations per second — the standard unit for a GPU's peak arithmetic throughput, always specific to a precision (FP64, FP32, TF32, FP16, and so on) and a named part, since the number changes across both axes: an H100 SXM reaches roughly 67 TFLOPS at FP32 but an order of magnitude more at lower tensor-core precisions, and a different generation or SKU changes both figures again. A TFLOPS number on its own, without a precision and a part, is not a usable fact. See [Arithmetic Intensity and Roofline](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md).

### Thread block cluster

A grouping of thread blocks, introduced at compute capability 9.0 (Hopper), that are guaranteed to be scheduled concurrently on the same GPC and can cooperate through distributed shared memory — reading and writing each other's shared memory directly instead of routing through global memory. It sits one level above the block in the hierarchy, giving explicit control over locality that previously only existed implicitly within a single block. See [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md).

### Warp

The GPU's actual unit of execution: a fixed group of 32 threads that the hardware issues one instruction to at a time, in lockstep, from a single program counter (subject to independent thread scheduling on compute capability 7.0+, which lets diverged threads within a warp track separate program counters without changing the underlying cost model). Every SIMT behavior in CUDA — coalescing, divergence, warp-level primitives like `` `__shfl_sync` `` — is a consequence of this 32-wide granularity. See [Warps and Schedulers](../02-gpu-hardware-architecture/warps-and-schedulers.md).

## See also

- [How This Section Is Organised](./how-this-section-is-organised.md) — the folder map this vocabulary is drawn from.
- [Anatomy of a GPU](../02-gpu-hardware-architecture/anatomy-of-a-gpu.md) — the physical structure behind SM, warp, CUDA core, and HBM.
- [Threads, Blocks, and Grids](../03-cuda-programming-model/threads-blocks-and-grids.md) — the programming-model hierarchy behind grid, block, and thread.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
