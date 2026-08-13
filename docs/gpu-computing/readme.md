---
title: GPU & Accelerators
sidebar_label: Overview
sidebar_position: 0
tags: [gpu, cuda, npu]
---

# GPU & Accelerators

A GPU is a throughput machine bolted onto a latency machine: thousands of simple cores, oversubscribed with far more threads than can run at once, trading single-thread speed for the ability to hide memory latency behind other work. Almost every performance question in this section reduces to the same one — did you keep the memory system busy, or is the chip sitting idle waiting on a load.

This section goes deep on CUDA — the programming model, the memory hierarchy, execution and synchronization, the runtime, and kernel optimization — then widens out to what production work actually uses: libraries, profiling tools, multi-GPU scaling, vendor-neutral portability layers, and NPU/inference accelerators. It does not cover graphics or rendering; for rasterization, shading, and the render pipeline, see [Rendering](../game-development/unreal-engine/12-rendering/gpu-profiling.md) in the Unreal Engine section.

:::info[How this is organised]
Folders 00–02 build the mental model (why GPUs look the way they do, and the hardware underneath). Folders 03–07 are CUDA proper — the programming model, memory, execution, runtime, and optimization. Folders 08–10 are what you reach for in production — libraries, profiling tools, and multi-GPU scaling. Folders 11–13 close out portability, inference accelerators, and worked kernels. Every folder from 03 onward is self-contained — you can start at any of them once you have the 00–02 grounding.
:::

## Three learning paths

| Path | Sequence | What you can do at the end |
|---|---|---|
| Write fast CUDA kernels | [CUDA Programming Model](./03-cuda-programming-model/your-first-kernel.md) → [Memory Model](./04-cuda-memory-model/memory-spaces-overview.md) → [Execution](./05-execution-and-synchronization/warp-execution-and-divergence.md) → [Kernel Optimization](./07-kernel-optimization/the-optimization-workflow.md) → [Applied Kernels](./13-applied-kernels-and-patterns/parallel-reduction.md) | Write, launch, and systematically optimize a CUDA kernel |
| Understand the hardware | [Foundations](./01-parallel-computing-foundations/flynn-taxonomy-simd-simt.md) → [Hardware Architecture](./02-gpu-hardware-architecture/anatomy-of-a-gpu.md) → [Tooling & Profiling](./09-tooling-profiling-and-debugging/nsight-compute.md) | Explain why a GPU is fast, and read its profiler output |
| Deploy models on accelerators | [Overview](./00-overview/cpu-vs-gpu-vs-npu.md) → [Libraries & Ecosystem](./08-libraries-and-ecosystem/choosing-a-library.md) → [NPUs & Inference Accelerators](./12-npu-and-inference-accelerators/what-is-an-npu.md) | Pick the right accelerator and library for a deployment target |

## Sections

| Section | What it covers |
|---|---|
| [Overview](./00-overview/why-gpus-exist.md) | Why GPUs exist, how they compare to CPUs and NPUs, the accelerator landscape, and when not to reach for a GPU |
| [Parallel Computing Foundations](./01-parallel-computing-foundations/flynn-taxonomy-simd-simt.md) | Flynn's taxonomy, Amdahl/Gustafson, latency hiding, arithmetic intensity, and the parallel patterns vocabulary |
| [GPU Hardware Architecture](./02-gpu-hardware-architecture/anatomy-of-a-gpu.md) | GPCs, SMs, warp schedulers, register files, caches, tensor cores, and the NVIDIA architecture generations |
| [CUDA Programming Model](./03-cuda-programming-model/installing-the-cuda-toolkit.md) | Toolkit setup, your first kernel, threads/blocks/grids, launch configuration, and the compilation model |
| [CUDA Memory Model](./04-cuda-memory-model/memory-spaces-overview.md) | Global, shared, constant, and register memory; coalescing; bank conflicts; unified memory; async data movement |
| [Execution and Synchronization](./05-execution-and-synchronization/warp-execution-and-divergence.md) | Warp divergence, independent thread scheduling, warp-level primitives, cooperative groups, and atomics |
| [CUDA Runtime and APIs](./06-cuda-runtime-and-apis/runtime-vs-driver-api.md) | Runtime vs driver API, device management, streams and events, CUDA graphs, and error handling |
| [Kernel Optimization](./07-kernel-optimization/the-optimization-workflow.md) | The measure-classify-fix workflow, occupancy tuning, memory access and instruction-level optimization, tensor cores |
| [Libraries and Ecosystem](./08-libraries-and-ecosystem/choosing-a-library.md) | cuBLAS, cuDNN, Thrust, CUB, CUTLASS, NCCL, and the Python stack (CuPy, Numba, Triton, PyTorch extensions) |
| [Tooling, Profiling, and Debugging](./09-tooling-profiling-and-debugging/building-cuda-with-cmake.md) | CMake builds, Nsight Systems and Compute, cuda-gdb and Compute Sanitizer, and roofline analysis in practice |
| [Multi-GPU and Scaling](./10-multi-gpu-and-scaling/multi-gpu-basics.md) | Multi-GPU basics, peer-to-peer and NVLink, NCCL collectives, parallelism strategies, and cluster scheduling |
| [Portable and Vendor-Neutral](./11-portable-and-vendor-neutral/the-portability-problem.md) | HIP/ROCm, SYCL/oneAPI, OpenCL, OpenMP/OpenACC offload, Vulkan/DirectX compute, Metal, and WebGPU |
| [NPUs and Inference Accelerators](./12-npu-and-inference-accelerators/what-is-an-npu.md) | Systolic arrays, Google TPU, edge NPUs, Jetson/DLA, quantization, TensorRT, ONNX Runtime, and OpenVINO |
| [Applied Kernels and Patterns](./13-applied-kernels-and-patterns/vector-add-and-saxpy.md) | Progressive optimizations of reduction, scan, matrix multiply, histogram, sorting, softmax, and FlashAttention |

## Conventions used here

- CUDA C++ is the default language throughout the section and appears in `cpp` code fences.
- Python is confined to [Libraries and Ecosystem](./08-libraries-and-ecosystem/cuda-python-and-cupy.md) (CuPy, Numba, Triton, PyTorch extensions), plus the toolkit-installation page.
- Every compute-capability requirement is called out in a `:::note`, since features like thread block clusters and independent thread scheduling only exist from a given architecture generation onward.
- Every performance number states the GPU it was measured on — a speedup on one architecture generation does not transfer to another.
