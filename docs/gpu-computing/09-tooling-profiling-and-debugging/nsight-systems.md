---
id: nsight-systems
title: Nsight Systems
sidebar_label: Nsight Systems
sidebar_position: 2
tags: [gpu, cuda, tooling, profiling]
---

# Nsight Systems

Nsight Systems answers "where does the wall-clock time go across CPU, GPU, memory, and the network"; [Nsight Compute](./nsight-compute.md) answers "why is this one kernel slow" — start with Systems, because a kernel that looks slow in isolation is sometimes just waiting behind something else, and no amount of kernel-level tuning fixes a scheduling gap.

## What it shows

Nsight Systems captures a single timeline across every engine involved in a run: CPU thread activity, CUDA API calls, kernel execution on the GPU, memory copies, and — with the right trace flags — OS scheduling and NVTX ranges. It's a system-wide view built for spotting where time is lost between the pieces, not for inspecting the internals of one kernel.

## Capturing from the CLI

```bash
nsys profile -t cuda,nvtx,osrt --stats=true -o report ./gpuapp
nsys stats report.nsys-rep       # summary tables without opening the GUI
```

`-t cuda,nvtx,osrt` selects which activity gets traced — CUDA API and kernel activity, NVTX ranges, and OS runtime events. `--stats=true` prints summary tables (kernel time, API call counts, memcpy time) straight to the console alongside the `.nsys-rep` file that the GUI opens. `nsys stats` re-reads an existing report to print those same tables later, without rerunning the program or opening the GUI.

## Reading the timeline

The GUI lays out one row per CPU thread and one per GPU stream, time running left to right, so overlap — or its absence — is visible directly: a kernel row running while a memcpy row is also active means the two are genuinely concurrent, and a gap in the GPU rows while a CPU row is busy means the GPU was idle waiting on the host. That gap is usually the first thing worth explaining, because a kernel that is individually fast can still leave the GPU idle most of the time if launches aren't keeping it fed. Zooming into a single gap and hovering the surrounding CUDA API row usually identifies the cause directly — a synchronous `cudaMemcpy`, a `cudaDeviceSynchronize`, or a host-side computation between launches all show up as a specific, named call sitting in the gap rather than as an unexplained blank space.

## NVTX ranges

The CUDA API and kernel rows alone are already recognizable, but a timeline of dozens of similarly-named kernels back to back is unreadable without knowing which application-level phase each one belongs to. NVTX ranges label a span of host code with a name that shows up as its own colored bar on the timeline, turning "these fifteen kernels" into "the forward pass":

```cpp showLineNumbers
#include <nvtx3/nvToolsExt.h>

nvtxRangePushA("forward");
forwardKernel<<<grid, block, 0, stream>>>(/* ... */);
nvtxRangePop();
```

`nvtxRangePushA` opens a named range and `nvtxRangePop` closes the most recently opened one; nesting pushes inside pushes gives nested bars on the timeline, which is how a training step, a forward pass within it, and a single fused kernel within that all show up at their own level of the same view.

## What to look for

| Timeline symptom | Likely cause | Where to go next |
|---|---|---|
| Gaps between kernels | Launch overhead or a host bottleneck feeding the queue | [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) |
| H2D/D2H copies not overlapping kernels | Pageable host memory, or everything issued on one stream | [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md) |
| One long single kernel | The bottleneck is inside that kernel, not between kernels | [Nsight Compute](./nsight-compute.md) |
| CPU thread pegged while the GPU sits idle | The input pipeline, not the GPU, is the bottleneck | Profile the CPU-side data loading path itself |

:::tip[Capture a few iterations, not the whole run]
Profile a handful of representative iterations rather than an entire training run or batch job. A multi-gigabyte `.nsys-rep` file takes as long to load in the GUI as it did to capture, and the extra iterations rarely show anything the first few didn't already establish.
:::

## See also

- [Nsight Compute](./nsight-compute.md) — the next step once the timeline points at one slow kernel.
- [Benchmarking Methodology](./benchmarking-methodology.md) — how to turn timeline observations into a repeatable measurement.
- [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md) — the overlap model the timeline is showing whether or not you're getting.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
