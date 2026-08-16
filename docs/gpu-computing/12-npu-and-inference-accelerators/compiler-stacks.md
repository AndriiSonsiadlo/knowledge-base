---
id: compiler-stacks
title: "Compiler Stacks: XLA, TVM, MLIR"
sidebar_label: Compiler Stacks
sidebar_position: 10
tags: [gpu, npu, compilers, mlir]
---

# Compiler Stacks: XLA, TVM, MLIR

Every deployment path covered so far in this folder eventually hands a graph to something that turns it into device code, and up to now that "something" has mostly been a fixed toolkit: TensorRT's builder, OpenVINO's plugins, a vendor NPU SDK. This page steps back and looks at the compilers underneath those toolkits and behind the frameworks themselves — what a graph compiler actually does that a kernel library doesn't, and the handful of stacks (XLA, TVM, MLIR, and `torch.compile`) that show up across nearly every deployment target in this section.

## Kernel libraries versus graph compilers

A **kernel library** — cuBLAS, cuDNN, oneDNN — gives you a fast, hand-tuned implementation of an operator you name: call the matmul routine, get a fast matmul. Its scope stops at the operator boundary; it has no idea what comes before or after the call in your model, and it can't do anything about that boundary. Two kernel-library calls back to back mean two full round trips to memory, one for each call's output, even when a human reading the code could see that the intermediate result never needs to leave the chip.

A **graph compiler** looks at the whole computation graph at once and generates code for it, which is what lets it do two things a kernel library structurally cannot: fuse operations across the boundaries between them into one kernel, avoiding exactly that unnecessary round trip, and choose memory layouts globally rather than accept whatever layout each individual library call happens to prefer. The tradeoff runs the other way too — a kernel library's hand-tuned implementation of a well-known operator like a large GEMM is frequently faster than what any graph compiler generates for the same operator, because a human expert tuned it specifically for that shape and that hardware, which is why the two approaches coexist rather than one replacing the other. Every stack on this page, in practice, still calls out to a hand-tuned library for the operators where doing so wins, and reserves its own generated code for everything around and between those calls.

## XLA

XLA (Accelerated Linear Algebra) is the compiler behind JAX and PyTorch/XLA, and [Google TPU](./google-tpu.md) covers it from the hardware side — the MXU, the shape-tiling story, the reasons you don't write TPU kernels by hand. This page covers the compiler itself. XLA's intermediate representation is **HLO** (High Level Operations), a graph of linear-algebra ops that XLA lowers through a sequence of passes; the two that matter most for understanding its behavior are **fusion**, which merges adjacent HLO ops into single compiled kernels the same way this page's opening section describes generically, and **layout assignment**, which chooses the physical memory layout for every tensor in the graph rather than accepting whatever layout each op would prefer in isolation. XLA's main cost, and the one worth internalizing before relying on it, is **shape specialization**: XLA compiles a distinct program for each distinct combination of input shapes it sees, so a model whose shapes vary at runtime can trigger repeated recompilation — the same shape-polymorphism cost [Google TPU](./google-tpu.md) covers as a TPU-specific warning, here stated as a property of the compiler itself, since XLA also targets GPU and CPU.

## TVM

TVM's organizing idea is a clean split between **compute** — a mathematical description of what an operator computes, independent of how — and **schedule** — the concrete decisions about loop order, tiling, vectorization, and parallelization that turn that computation into actual code for a specific target. The same compute definition can pair with many different schedules, each a different point in a large search space of possible implementations, and TVM's distinctive move is to search that space automatically rather than have a human hand-write each schedule. **AutoTVM** was the first generation of that search: given a schedule template with tunable knobs (tile sizes, unroll factors) written by a human expert, AutoTVM statistically searches the space those knobs define. **Ansor** (TVM's auto-scheduler) removed the requirement for a hand-written template, searching a much larger space of schedule structures directly and generally finding better schedules with less manual engineering per operator. Because this whole approach starts from a compute description and searches for a schedule rather than depending on a hand-tuned library for each target, TVM's particular strength is diverse and unusual edge targets — hardware combinations no vendor has written a tuned kernel library for — where AutoTVM or Ansor's search can still produce a competitive schedule without one existing.

TVM's frontend imports models from PyTorch, ONNX, and other formats into **Relay**, its graph-level IR, then lowers individual operators into **TIR** (Tensor IR), the level where compute/schedule separation and autotuning actually operate. That two-level structure — a graph IR for whole-model transformations, a lower tensor IR for per-operator codegen — is part of why TVM ports to unusual targets more readily than a stack built around a single fixed IR: a new backend mostly needs a new TIR codegen path, not a rewrite of the graph-level logic above it.

## MLIR

MLIR (Multi-Level Intermediate Representation) is not itself a compiler — it is compiler *infrastructure*: a framework for defining IRs at multiple levels of abstraction and progressively lowering a program from a high-level, semantically rich representation down to something close to hardware, one **dialect** at a time. A dialect is a self-contained set of operations, types, and attributes for one level of abstraction; a program moves between dialects through explicit, verifiable lowering passes rather than one big all-at-once translation. A few dialects show up often enough in this space to be worth naming: `linalg` captures linear-algebra operations (matmuls, convolutions, elementwise ops) at a level where fusion and tiling transformations are still easy to express; `affine` represents loop nests with affine (polyhedral) index expressions, the level where loop-level optimizations like tiling and interchange happen; `gpu` is a retargetable, vendor-neutral GPU programming model that later lowers to a vendor-specific backend dialect; and `nvvm` is that NVIDIA-specific backend dialect, an LLVM-IR-based representation that sits just above NVIDIA's PTX/NVPTX code generation. The reason almost every stack mentioned on this page — XLA, TVM's newer components, `torch.compile`'s Inductor backend, and vendor NPU compilers alike — is converging on MLIR or something MLIR-shaped is that building a new compiler backend from scratch for every hardware target is enormously expensive, and MLIR's whole design is aimed at letting a new target reuse the dialects and lowering passes that already exist rather than starting over.

Recompilation triggered by shape specialization is not a bug to work around so much as a cost to budget for: the first call with a new shape pays a real compile latency, and only subsequent calls with that same shape run the compiled program at full speed. Workloads with a small, predictable set of shapes amortize that cost fine; workloads with genuinely unbounded shape variety — unpadded natural-language sequences being the recurring example — need to bucket their inputs into a fixed set of shapes deliberately, rather than let the compiler discover the shape space one recompilation at a time in production.

## `torch.compile` and Inductor

`torch.compile` is PyTorch's own graph compiler, and it splits into two pieces with distinct jobs. **TorchDynamo** captures the graph: it hooks into Python bytecode execution to trace the model's actual operations into an FX graph, falling back to eager execution for any Python it can't safely trace — which is exactly what a **graph break** is, a point where Dynamo gives up capturing and drops back to the interpreter for that stretch of code. **Inductor** is the backend that takes Dynamo's captured graph and generates code from it: Triton kernels (see [Triton](../08-libraries-and-ecosystem/triton.md)) for GPU targets, and C++ with OpenMP for CPU targets. The fusion Inductor performs across operator boundaries, and the reason a chain of small ops compiled together beats the same chain executed eagerly, is the same launch-overhead argument [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) makes for hand-written kernels — `torch.compile` is largely automating that same fusion decision.

| Stack | Frontend | IR | Backends | Autotuning |
|---|---|---|---|---|
| XLA | JAX, PyTorch/XLA | HLO | TPU, GPU, CPU | Limited; mostly fixed heuristic passes |
| TVM | Relay/TorchScript/ONNX import | Relay + TIR | CPU, GPU, diverse edge accelerators | AutoTVM (templated search), Ansor (template-free search) |
| MLIR | N/A — infrastructure other compilers build on | Multiple dialects (`linalg`, `affine`, `gpu`, `nvvm`, ...) | Whatever a downstream stack lowers to | N/A — depends on the consuming compiler |
| `torch.compile` (Inductor) | PyTorch (via TorchDynamo) | FX graph | GPU (Triton), CPU (C++/OpenMP) | Limited autotuning of generated Triton kernel configs |

## What compilers are still bad at

None of these stacks make hand-tuning obsolete, and it's worth being honest about where they still fall short. Tuned GEMM and attention kernels remain library or hand-written territory more often than not — cuBLAS, CUTLASS, and FlashAttention-style hand-written kernels still beat what a general graph compiler generates for these specific, extremely well-studied operators, because a human expert's knowledge of the exact hardware still outperforms automated search on the operators that matter most. Dynamic shapes are a persistent weak point across the board: every stack on this page either recompiles per shape (XLA, and `torch.compile` with `dynamic=False`) or accepts a performance cost for shape generality. Data-dependent control flow — a branch or loop whose behavior depends on tensor values at runtime, not just their shapes — resists ahead-of-time compilation structurally, the same limitation [What Is an NPU?](./what-is-an-npu.md) describes for fixed-function hardware, and shows up here as a compiler-level version of the same problem. And graph breaks are the quiet failure mode: a single unsupported construct in a hot loop can silently disable fusion and optimization for everything downstream of it, while the code still runs correctly — which makes it the kind of regression that shows up as "the model didn't get faster" rather than as an error.

```bash
TORCH_LOGS=graph_breaks
```

Setting that environment variable before running a `torch.compile`-wrapped program makes TorchDynamo report every point where it fell back to eager execution, with the source location and the reason tracing stopped there — the fastest way to find a graph break without instrumenting the model by hand.

:::tip[Find graph breaks before assuming `torch.compile` didn't help]
`TORCH_LOGS=graph_breaks` and `torch._dynamo.explain(model)(*args)` both report where TorchDynamo gave up tracing and fell back to eager execution. A single graph break sitting in a hot loop can erase most of the benefit `torch.compile` would otherwise deliver, and because the code keeps running correctly either way, the only way to notice is to check for graph breaks directly rather than infer their absence from correct output.
:::

## See also

- [Triton](../08-libraries-and-ecosystem/triton.md) — the kernel language Inductor targets on GPU.
- [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) — the launch-overhead argument these compilers automate.
- [Google TPU](./google-tpu.md) — XLA and the MXU from the hardware side.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
