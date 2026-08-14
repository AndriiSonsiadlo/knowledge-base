# GPU & Accelerators — Plan 1: Wiring, Skeleton, and Foundations

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire a new top-level `GPU & Accelerators` section into the site, create the complete 129-file skeleton for all 14 folders, and write the section landing page plus folders `00-overview`, `01-parallel-computing-foundations`, and `02-gpu-hardware-architecture`.

**Architecture:** Task 1 creates *every* file the whole six-plan series will ever touch — 14 `_category_.json` files and 129 Markdown files as valid stubs (frontmatter + H1 + one framing sentence). Because every link target exists from Task 1 onward, `npm run build` (with `onBrokenLinks: "throw"`) passes after every subsequent task in every plan, and no forward-reference pass is ever needed. Later tasks only ever *fill in* stubs, never create pages.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism code fences, Biome (format/lint), Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Plan series:** This is plan 1 of 6.
1. **(this plan)** wiring + skeleton + `readme.md` + folders 00, 01, 02
2. folders 03, 04, 05 — CUDA programming, memory, execution
3. folders 06, 07 — runtime APIs, kernel optimization
4. folders 08, 09, 10 — libraries, tooling, multi-GPU
5. folders 11, 12 — portability layers, NPUs
6. folder 13 — applied kernels, plus the outward cross-link pass and final audit

---

## Global Constraints

These apply to **every** page in **every** plan of this series. They are always in force and are not restated per task.

### Placement and skeleton

- Section root is `docs/gpu-computing/`. It gets **no** top-level `_category_.json` — it is a sidebar root (matches `docs/machine-learning/`).
- The skeleton created in Task 1 of this plan is the complete file list. **Never create a page that is not in the skeleton, and never link to a path that is not in the skeleton.** If a page seems missing, that is a spec gap — flag it, do not invent a file.

### Frontmatter

Every topic page, exactly:

```md
---
id: <kebab-case-id, equals the filename without .md>
title: <Human Title>
sidebar_label: <short label>
sidebar_position: <int, starts at 1 within its folder>
tags: [gpu, <area-tag>, <topic-tag>, <topic-tag>]
---
```

- `tags` always begins with `gpu`. Folders 03–10 add `cuda` second. Folder 11 uses the API slug (`hip`, `sycl`, `opencl`, `vulkan`, `metal`, `webgpu`, `openmp`). Folder 12 uses `npu` plus the stack slug (`tensorrt`, `onnx`, `tpu`, `openvino`). Then 1–2 more lowercase hyphenated topic tags. 3–5 tags total.
- `readme.md` has **no** `id` (matches `docs/programming/boost/readme.md`) and uses `sidebar_position: 0` so it sorts above `00-overview` (which is category position 1).

### Folder `_category_.json`

**Tab-indented** — every existing `_category_.json` in this repo uses a literal tab, and Biome's 2-space setting targets JS/TS. Do not reformat these.

```json
{
	"label": "<Label>",
	"position": <int>,
	"link": {
		"type": "generated-index"
	}
}
```

`position` = numeric folder prefix + 1. Labels carry no numeric prefix (matches `docs/machine-learning/*/`).

### Page structure

1. `# H1` matching `title` exactly.
2. 1–2 paragraphs of prose framing **what problem this solves**, before any API detail. No page opens with a code block, a bullet list, or a definition list.
3. `##` sections per subtopic. `###` sparingly, only where a `##` genuinely has parts.
4. Ends with `## See also` — 3–5 bullets, **plain relative Markdown links**, in this shape:
   `- [Link text](./relative-path.md) — one-line reason to go there.`
   Order: siblings first, then cross-folder, then `../readme.md` last.

**Do not use `<Icon icon="lucide:..." />`.** The boost/cmake sections use it, but the icons come from a hand-curated allowlist in `scripts/gen-icons.mjs`; an unlisted name renders empty. This section follows the `docs/machine-learning/` convention of plain link bullets, which needs no script change.

### Admonitions

Only these four, with these meanings. Do not invent new ones.

| Admonition | Use for |
|---|---|
| `:::info[...]` | Framing the problem a feature solves |
| `:::note[...]` | Side facts, version / compute-capability caveats |
| `:::tip[...]` | Practical guidance, rules of thumb |
| `:::warning[...]` | Pitfalls, correctness traps, performance cliffs |

Compute-capability gating is a recurring `:::note` — e.g. thread block clusters and distributed shared memory require CC 9.0+; independent thread scheduling requires CC 7.0+.

### Code fences

- **CUDA C++ uses ` ```cpp `.** There is no Prism grammar for CUDA and none can be added — `node_modules/prismjs/components/` has no `cuda`. `cpp` is bundled by `prism-react-renderer` by default.
- **PTX and SASS use ` ```text `.** No grammar exists; `nasm` mis-highlights both.
- Other permitted fences: `bash`, `cmake`, `json`, `python`, `glsl`, `hlsl`, `wgsl`.
- **Python appears only** in folder 08 and in `03-cuda-programming-model/installing-the-cuda-toolkit.md`.
- Add `showLineNumbers` to any fence longer than ~5 lines. Add `title="filename.cu"` when the snippet is a real standalone file.
- Kernels are complete and compilable where practical; elided bodies use `// ...`, never pseudocode.
- **Error checking is defined once**, in `06-cuda-runtime-and-apis/error-handling.md`, as a `CUDA_CHECK` macro. Every other page uses `CUDA_CHECK(...)` without redefining it.

:::note[Spec inconsistency, resolved]
The spec's *Code* section refers to `06-cuda-runtime-and-apis/error-handling-and-checking.md`, but its page-by-page outline lists the file as `error-handling.md`. The outline wins: the file is **`error-handling.md`**.
:::

### MDX hazards — the most common way these pages break the build

Docusaurus renders these files as MDX. Inside fenced code blocks and inline backticks everything is safe. **Outside** them:

- `__global__`, `__device__`, `__shared__`, `__syncthreads` — bare double underscores become Markdown emphasis. **Always backtick them in prose.**
- `<<<grid, block>>>`, `<T>`, `dim3<...>` — angle brackets are parsed as JSX. **Always backtick them in prose.**
- Bare `{` `}` in prose is a JSX expression. Backtick it.

### Diagrams

Mermaid (` ```mermaid `) for anything structural: grid/block/warp mapping, memory hierarchy trees, stream/event timelines, pipeline stages, compilation flow, collective topologies. **Quote every edge label** — an unescaped label broke a build before (commit `958a2e6`). Write `A -->|"label (with parens)"| B`, never `A -->|label (with parens)| B`.

### Images

- Path: `static/img/gpu/<folder-slug>/<name>.png`, referenced as `/img/gpu/<folder-slug>/<name>.png` — do **not** include the `baseUrl` prefix; Docusaurus resolves a root-absolute Markdown image path against `static/` and prepends `baseUrl` itself.
- Every image is followed immediately by an italic source caption linking the origin page.
- Every image adds a row to `static/img/gpu/SOURCES.md`.
- Prefer Mermaid. Download an image only for die shots, block diagrams too dense for Mermaid, Nsight UI screenshots, and published benchmark/roofline plots.

### Content currency

Document current CUDA (13.x semantics), not CUDA-10-era material:

- Thread block clusters (CC 9.0+) are a first-class level of the execution hierarchy.
- Distributed shared memory, `cluster.map_shared_rank()`, `cluster.sync()`.
- Tensor Memory Accelerator (CC 9.0+).
- `cuda::memcpy_async` / `cg::memcpy_async`, `cuda::barrier`, `cuda::pipeline` (async from CC 8.0+).
- Cooperative Groups as the modern replacement for raw `__syncthreads()` idioms.
- Architecture coverage through **Blackwell**.
- **`__shfl_sync`-family intrinsics only.** The non-`_sync` variants are removed, not deprecated — never show them except as a labelled historical note.
- Every performance claim on an optimization page states the hardware generation it was measured on.

### Verification gate — every task

1. `npm run build` exits 0. This is the repo's only correctness gate: it validates internal links, MDX syntax, and admonitions.
2. `npm run format` (Biome) over the new Markdown, then `npm run lint` exits 0.
3. Commit. Message is one line, `<type>: <what>`. **Never** add a `Co-Authored-By` trailer or a "Generated with Claude Code" line (`CLAUDE.md`).

---

## File Structure

```
docs/gpu-computing/
├── readme.md                              landing page + three learning paths
├── 00-overview/                    (6)    why GPUs, CPU/GPU/NPU, landscape, glossary
├── 01-parallel-computing-foundations/ (7) SIMT, Amdahl, latency hiding, roofline
├── 02-gpu-hardware-architecture/  (10)    SM, warps, caches, tensor cores, generations
├── 03-cuda-programming-model/      (9)    install, first kernel, indexing, clusters, nvcc
├── 04-cuda-memory-model/          (11)    spaces, coalescing, shared, DSMEM, async copy
├── 05-execution-and-synchronization/ (8)  divergence, warp primitives, coop groups, atomics
├── 06-cuda-runtime-and-apis/       (9)    streams, events, graphs, errors, MPS/MIG
├── 07-kernel-optimization/        (11)    workflow, occupancy, tiling, tensor cores, PTX
├── 08-libraries-and-ecosystem/    (12)    cuBLAS, CUB, CUTLASS, NCCL, CuPy, Triton
├── 09-tooling-profiling-and-debugging/ (7) CMake, Nsight, sanitizers, benchmarking
├── 10-multi-gpu-and-scaling/       (6)    P2P, NCCL collectives, parallelism, clusters
├── 11-portable-and-vendor-neutral/ (9)    HIP, SYCL, OpenCL, Vulkan, Metal, WebGPU
├── 12-npu-and-inference-accelerators/ (11) TPU, edge NPUs, quantization, TensorRT, ONNX
└── 13-applied-kernels-and-patterns/ (12)  reduction, scan, GEMM, transpose, FlashAttention

static/img/gpu/
├── SOURCES.md                             image provenance manifest
└── <folder-slug>/                         downloaded vendor figures
```

Files changed outside `docs/`: `sidebars.js`, `docusaurus.config.js` (navbar + prism), `static/img/gpu/`.

---

### Task 1: Site wiring and the complete skeleton

Creates everything. After this task, every internal link used anywhere in plans 1–6 resolves.

**Files:**
- Modify: `sidebars.js`
- Modify: `docusaurus.config.js` (navbar items array; `prism.additionalLanguages`)
- Create: `docs/gpu-computing/readme.md` (stub)
- Create: `docs/gpu-computing/<14 folders>/_category_.json`
- Create: 128 topic stubs

**Interfaces:**
- Consumes: nothing.
- Produces: the sidebar id `gpuComputingSidebar`; every file path, `id`, `title`, `sidebar_label`, `sidebar_position`, and tag set that plans 1–6 fill in and link to.

- [ ] **Step 1: Add the sidebar**

In `sidebars.js`, add after `gameDevSidebar`:

```js
  gpuComputingSidebar: [{ type: "autogenerated", dirName: "gpu-computing" }],
```

- [ ] **Step 2: Add the navbar tab**

In `docusaurus.config.js`, inside `themeConfig.navbar.items`, insert **immediately after** the Machine Learning `docSidebar` entry and before the commented-out Blog entry:

```js
          {
            type: "docSidebar",
            sidebarId: "gpuComputingSidebar",
            position: "left",
            label: "GPU & Accelerators",
            description:
              "CUDA, GPU architecture, kernel optimization, and NPU/inference accelerators.",
            icon: "🚀",
          },
```

- [ ] **Step 3: Add the three Prism languages**

In `docusaurus.config.js`, replace the `additionalLanguages` line:

```js
        additionalLanguages: [
          "bash",
          "cmake",
          "csharp",
          "glsl",
          "hlsl",
          "ini",
          "json",
          "python",
          "wgsl",
        ],
```

No CUDA entry is added — no Prism grammar for CUDA exists.

- [ ] **Step 4: Create the 14 `_category_.json` files (tab-indented)**

Shape (see Global Constraints). Values:

| Folder | `label` | `position` |
|---|---|---|
| `00-overview` | Overview | 1 |
| `01-parallel-computing-foundations` | Parallel Computing Foundations | 2 |
| `02-gpu-hardware-architecture` | GPU Hardware Architecture | 3 |
| `03-cuda-programming-model` | CUDA Programming Model | 4 |
| `04-cuda-memory-model` | CUDA Memory Model | 5 |
| `05-execution-and-synchronization` | Execution and Synchronization | 6 |
| `06-cuda-runtime-and-apis` | CUDA Runtime and APIs | 7 |
| `07-kernel-optimization` | Kernel Optimization | 8 |
| `08-libraries-and-ecosystem` | Libraries and Ecosystem | 9 |
| `09-tooling-profiling-and-debugging` | Tooling, Profiling, and Debugging | 10 |
| `10-multi-gpu-and-scaling` | Multi-GPU and Scaling | 11 |
| `11-portable-and-vendor-neutral` | Portable and Vendor-Neutral | 12 |
| `12-npu-and-inference-accelerators` | NPUs and Inference Accelerators | 13 |
| `13-applied-kernels-and-patterns` | Applied Kernels and Patterns | 14 |

- [ ] **Step 5: Create the `readme.md` stub**

`docs/gpu-computing/readme.md`:

```md
---
title: GPU & Accelerators
sidebar_label: Overview
sidebar_position: 0
tags: [gpu, cuda, npu]
---

# GPU & Accelerators

How parallel accelerators actually work, and how to write code that uses them well.
```

- [ ] **Step 6: Create the 128 topic stubs**

Every stub is exactly frontmatter + `# H1` + one sentence of framing prose. **No `## See also` yet** — later tasks write the real body.

Template:

```md
---
id: why-gpus-exist
title: Why GPUs Exist
sidebar_label: Why GPUs Exist
sidebar_position: 1
tags: [gpu, overview, architecture]
---

# Why GPUs Exist

Stub — filled in by plan 1, task 3.
```

`id` always equals the filename without `.md`. `sidebar_label` equals `title` unless a short label is given below. The tables below give `sidebar_position` (the row order, starting at 1), `title`, and `tags`.

**`00-overview/`** — tags start `[gpu, overview, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `why-gpus-exist.md` | Why GPUs Exist | Why GPUs Exist | `[gpu, overview, architecture, throughput]` |
| 2 | `cpu-vs-gpu-vs-npu.md` | CPU vs GPU vs NPU | CPU vs GPU vs NPU | `[gpu, overview, npu, comparison]` |
| 3 | `the-accelerator-landscape.md` | The Accelerator Landscape | Accelerator Landscape | `[gpu, overview, npu, vendors]` |
| 4 | `when-not-to-use-a-gpu.md` | When Not to Use a GPU | When Not to Use a GPU | `[gpu, overview, amdahl, tradeoffs]` |
| 5 | `how-this-section-is-organised.md` | How This Section Is Organised | How This Is Organised | `[gpu, overview, navigation]` |
| 6 | `glossary.md` | Glossary | Glossary | `[gpu, overview, glossary, terminology]` |

**`01-parallel-computing-foundations/`** — tags start `[gpu, parallelism, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `flynn-taxonomy-simd-simt.md` | SIMD, SIMT, and Flynn's Taxonomy | SIMD, SIMT, Flynn | `[gpu, parallelism, simt, simd]` |
| 2 | `amdahl-and-gustafson.md` | Amdahl's and Gustafson's Laws | Amdahl & Gustafson | `[gpu, parallelism, scaling, amdahl]` |
| 3 | `latency-throughput-and-hiding.md` | Latency, Throughput, and Latency Hiding | Latency & Throughput | `[gpu, parallelism, latency, throughput]` |
| 4 | `arithmetic-intensity-and-roofline.md` | Arithmetic Intensity and the Roofline Model | Roofline Model | `[gpu, parallelism, roofline, performance]` |
| 5 | `memory-bound-vs-compute-bound.md` | Memory-Bound vs Compute-Bound | Memory vs Compute Bound | `[gpu, parallelism, bandwidth, performance]` |
| 6 | `parallel-patterns.md` | Parallel Patterns | Parallel Patterns | `[gpu, parallelism, patterns, algorithms]` |
| 7 | `the-host-device-model.md` | The Host–Device Model | Host–Device Model | `[gpu, parallelism, offload, memory]` |

**`02-gpu-hardware-architecture/`** — tags start `[gpu, hardware, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `anatomy-of-a-gpu.md` | Anatomy of a GPU | Anatomy of a GPU | `[gpu, hardware, architecture, sm]` |
| 2 | `streaming-multiprocessor.md` | The Streaming Multiprocessor | Streaming Multiprocessor | `[gpu, hardware, sm, architecture]` |
| 3 | `warps-and-schedulers.md` | Warps and Warp Schedulers | Warps & Schedulers | `[gpu, hardware, warps, scheduling]` |
| 4 | `register-file-and-occupancy.md` | The Register File and Occupancy | Registers & Occupancy | `[gpu, hardware, registers, occupancy]` |
| 5 | `cache-hierarchy.md` | Cache Hierarchy | Cache Hierarchy | `[gpu, hardware, cache, memory]` |
| 6 | `device-memory-and-bandwidth.md` | Device Memory and Bandwidth | Memory & Bandwidth | `[gpu, hardware, hbm, bandwidth]` |
| 7 | `tensor-cores.md` | Tensor Cores | Tensor Cores | `[gpu, hardware, tensor-cores, mma]` |
| 8 | `nvidia-architecture-generations.md` | NVIDIA Architecture Generations | Architecture Generations | `[gpu, hardware, nvidia, generations]` |
| 9 | `compute-capability.md` | Compute Capability | Compute Capability | `[gpu, hardware, compute-capability, nvcc]` |
| 10 | `interconnects-pcie-and-nvlink.md` | Interconnects: PCIe and NVLink | PCIe & NVLink | `[gpu, hardware, nvlink, pcie]` |

**`03-cuda-programming-model/`** — tags start `[gpu, cuda, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `installing-the-cuda-toolkit.md` | Installing the CUDA Toolkit | Installing CUDA | `[gpu, cuda, toolkit, setup]` |
| 2 | `your-first-kernel.md` | Your First Kernel | Your First Kernel | `[gpu, cuda, kernel, tutorial]` |
| 3 | `threads-blocks-and-grids.md` | Threads, Blocks, and Grids | Threads, Blocks, Grids | `[gpu, cuda, threads, hierarchy]` |
| 4 | `thread-indexing.md` | Thread Indexing | Thread Indexing | `[gpu, cuda, indexing, grid-stride]` |
| 5 | `launch-configuration.md` | Choosing a Launch Configuration | Launch Configuration | `[gpu, cuda, occupancy, launch]` |
| 6 | `thread-block-clusters.md` | Thread Block Clusters | Thread Block Clusters | `[gpu, cuda, clusters, hopper]` |
| 7 | `function-qualifiers.md` | Function and Variable Qualifiers | Qualifiers | `[gpu, cuda, qualifiers, language]` |
| 8 | `the-compilation-model.md` | The Compilation Model | Compilation Model | `[gpu, cuda, nvcc, ptx]` |
| 9 | `separate-compilation-and-linking.md` | Separate Compilation and Linking | Separate Compilation | `[gpu, cuda, nvcc, linking]` |

**`04-cuda-memory-model/`** — tags start `[gpu, cuda, memory, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `memory-spaces-overview.md` | Memory Spaces Overview | Memory Spaces | `[gpu, cuda, memory, overview]` |
| 2 | `global-memory-and-coalescing.md` | Global Memory and Coalescing | Global Memory & Coalescing | `[gpu, cuda, memory, coalescing]` |
| 3 | `shared-memory.md` | Shared Memory | Shared Memory | `[gpu, cuda, memory, shared-memory]` |
| 4 | `bank-conflicts.md` | Shared Memory Bank Conflicts | Bank Conflicts | `[gpu, cuda, memory, bank-conflicts]` |
| 5 | `registers-and-local-memory.md` | Registers and Local Memory | Registers & Local Memory | `[gpu, cuda, memory, registers]` |
| 6 | `constant-and-texture-memory.md` | Constant and Texture Memory | Constant & Texture | `[gpu, cuda, memory, texture]` |
| 7 | `unified-memory.md` | Unified Memory | Unified Memory | `[gpu, cuda, memory, unified-memory]` |
| 8 | `pinned-memory-and-transfers.md` | Pinned Memory and Host Transfers | Pinned Memory | `[gpu, cuda, memory, transfers]` |
| 9 | `distributed-shared-memory.md` | Distributed Shared Memory | Distributed Shared Memory | `[gpu, cuda, memory, clusters]` |
| 10 | `asynchronous-data-movement.md` | Asynchronous Data Movement | Async Data Movement | `[gpu, cuda, memory, memcpy-async]` |
| 11 | `memory-consistency-and-fences.md` | Memory Consistency and Fences | Consistency & Fences | `[gpu, cuda, memory, atomics]` |

**`05-execution-and-synchronization/`** — tags start `[gpu, cuda, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `warp-execution-and-divergence.md` | Warp Execution and Divergence | Warp Divergence | `[gpu, cuda, warps, divergence]` |
| 2 | `independent-thread-scheduling.md` | Independent Thread Scheduling | Independent Thread Scheduling | `[gpu, cuda, warps, volta]` |
| 3 | `warp-level-primitives.md` | Warp-Level Primitives | Warp Primitives | `[gpu, cuda, warps, shuffle]` |
| 4 | `block-synchronization.md` | Block Synchronization | Block Synchronization | `[gpu, cuda, synchronization, syncthreads]` |
| 5 | `cooperative-groups.md` | Cooperative Groups | Cooperative Groups | `[gpu, cuda, cooperative-groups, synchronization]` |
| 6 | `atomics.md` | Atomic Operations | Atomics | `[gpu, cuda, atomics, contention]` |
| 7 | `grid-wide-synchronization.md` | Grid-Wide Synchronization | Grid-Wide Sync | `[gpu, cuda, synchronization, cooperative-groups]` |
| 8 | `reductions-and-scans.md` | Reductions and Scans | Reductions & Scans | `[gpu, cuda, reduction, scan]` |

**`06-cuda-runtime-and-apis/`** — tags start `[gpu, cuda, runtime, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `runtime-vs-driver-api.md` | Runtime API vs Driver API | Runtime vs Driver API | `[gpu, cuda, runtime, driver-api]` |
| 2 | `device-management.md` | Device Management | Device Management | `[gpu, cuda, runtime, devices]` |
| 3 | `memory-allocation-apis.md` | Memory Allocation APIs | Allocation APIs | `[gpu, cuda, runtime, allocation]` |
| 4 | `streams-and-concurrency.md` | Streams and Concurrency | Streams & Concurrency | `[gpu, cuda, runtime, streams]` |
| 5 | `events-and-timing.md` | Events and Timing | Events & Timing | `[gpu, cuda, runtime, timing]` |
| 6 | `cuda-graphs.md` | CUDA Graphs | CUDA Graphs | `[gpu, cuda, runtime, graphs]` |
| 7 | `dynamic-parallelism.md` | Dynamic Parallelism | Dynamic Parallelism | `[gpu, cuda, runtime, dynamic-parallelism]` |
| 8 | `error-handling.md` | Error Handling and Checking | Error Handling | `[gpu, cuda, runtime, error-handling]` |
| 9 | `mps-and-mig.md` | MPS and MIG | MPS & MIG | `[gpu, cuda, runtime, sharing]` |

**`07-kernel-optimization/`** — tags start `[gpu, cuda, optimization, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `the-optimization-workflow.md` | The Optimization Workflow | Optimization Workflow | `[gpu, cuda, optimization, profiling]` |
| 2 | `occupancy-tuning.md` | Occupancy Tuning | Occupancy Tuning | `[gpu, cuda, optimization, occupancy]` |
| 3 | `memory-access-optimization.md` | Memory Access Optimization | Memory Access | `[gpu, cuda, optimization, coalescing]` |
| 4 | `shared-memory-tiling.md` | Shared Memory Tiling | Shared Memory Tiling | `[gpu, cuda, optimization, tiling]` |
| 5 | `instruction-level-optimization.md` | Instruction-Level Optimization | Instruction-Level | `[gpu, cuda, optimization, ilp]` |
| 6 | `reducing-divergence.md` | Reducing Divergence | Reducing Divergence | `[gpu, cuda, optimization, divergence]` |
| 7 | `kernel-fusion-and-launch-overhead.md` | Kernel Fusion and Launch Overhead | Fusion & Launch Overhead | `[gpu, cuda, optimization, fusion]` |
| 8 | `programming-tensor-cores.md` | Programming Tensor Cores | Programming Tensor Cores | `[gpu, cuda, optimization, tensor-cores]` |
| 9 | `software-pipelining.md` | Software Pipelining and Double Buffering | Software Pipelining | `[gpu, cuda, optimization, pipelining]` |
| 10 | `ptx-and-inline-assembly.md` | PTX and Inline Assembly | PTX & Inline Asm | `[gpu, cuda, optimization, ptx]` |
| 11 | `common-antipatterns.md` | Common Antipatterns | Antipatterns | `[gpu, cuda, optimization, antipatterns]` |

**`08-libraries-and-ecosystem/`** — tags start `[gpu, cuda, libraries, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `choosing-a-library.md` | Choosing a Library Over a Kernel | Choosing a Library | `[gpu, cuda, libraries, decision-guide]` |
| 2 | `cublas.md` | cuBLAS | cuBLAS | `[gpu, cuda, libraries, cublas]` |
| 3 | `cudnn.md` | cuDNN | cuDNN | `[gpu, cuda, libraries, cudnn]` |
| 4 | `math-libraries.md` | cuFFT, cuRAND, cuSPARSE, cuSOLVER | Math Libraries | `[gpu, cuda, libraries, math]` |
| 5 | `thrust.md` | Thrust | Thrust | `[gpu, cuda, libraries, thrust]` |
| 6 | `cub.md` | CUB | CUB | `[gpu, cuda, libraries, cub]` |
| 7 | `cutlass.md` | CUTLASS | CUTLASS | `[gpu, cuda, libraries, cutlass]` |
| 8 | `nccl.md` | NCCL | NCCL | `[gpu, cuda, libraries, nccl]` |
| 9 | `cuda-python-and-cupy.md` | CUDA Python and CuPy | CUDA Python & CuPy | `[gpu, cuda, libraries, python]` |
| 10 | `numba-cuda.md` | Numba CUDA | Numba CUDA | `[gpu, cuda, libraries, numba]` |
| 11 | `pytorch-cuda-extensions.md` | PyTorch CUDA Extensions | PyTorch Extensions | `[gpu, cuda, libraries, pytorch]` |
| 12 | `triton.md` | Triton | Triton | `[gpu, cuda, libraries, triton]` |

**`09-tooling-profiling-and-debugging/`** — tags start `[gpu, cuda, tooling, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `building-cuda-with-cmake.md` | Building CUDA with CMake | CUDA with CMake | `[gpu, cuda, tooling, cmake]` |
| 2 | `nsight-systems.md` | Nsight Systems | Nsight Systems | `[gpu, cuda, tooling, profiling]` |
| 3 | `nsight-compute.md` | Nsight Compute | Nsight Compute | `[gpu, cuda, tooling, profiling]` |
| 4 | `cuda-gdb-and-sanitizers.md` | cuda-gdb and Compute Sanitizer | Debugging & Sanitizers | `[gpu, cuda, tooling, debugging]` |
| 5 | `metrics-that-matter.md` | Metrics That Matter | Metrics That Matter | `[gpu, cuda, tooling, metrics]` |
| 6 | `roofline-in-practice.md` | Roofline Analysis in Practice | Roofline in Practice | `[gpu, cuda, tooling, roofline]` |
| 7 | `benchmarking-methodology.md` | Benchmarking Methodology | Benchmarking | `[gpu, cuda, tooling, benchmarking]` |

**`10-multi-gpu-and-scaling/`** — tags start `[gpu, cuda, multi-gpu, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `multi-gpu-basics.md` | Multi-GPU Basics | Multi-GPU Basics | `[gpu, cuda, multi-gpu, scaling]` |
| 2 | `peer-to-peer-and-nvlink.md` | Peer-to-Peer Access and NVLink | Peer-to-Peer & NVLink | `[gpu, cuda, multi-gpu, nvlink]` |
| 3 | `collectives-with-nccl.md` | Collectives with NCCL | Collectives with NCCL | `[gpu, cuda, multi-gpu, nccl]` |
| 4 | `parallelism-strategies.md` | Data, Model, Pipeline, and Tensor Parallelism | Parallelism Strategies | `[gpu, cuda, multi-gpu, parallelism]` |
| 5 | `gpudirect-and-rdma.md` | GPUDirect and RDMA | GPUDirect & RDMA | `[gpu, cuda, multi-gpu, rdma]` |
| 6 | `clusters-and-schedulers.md` | GPU Clusters and Schedulers | Clusters & Schedulers | `[gpu, cuda, multi-gpu, slurm]` |

**`11-portable-and-vendor-neutral/`** — tags start `[gpu, <api-slug>, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `the-portability-problem.md` | The Portability Problem | The Portability Problem | `[gpu, portability, vendor-neutral]` |
| 2 | `hip-and-rocm.md` | HIP and ROCm | HIP & ROCm | `[gpu, hip, rocm, amd]` |
| 3 | `sycl-and-oneapi.md` | SYCL and oneAPI | SYCL & oneAPI | `[gpu, sycl, oneapi, intel]` |
| 4 | `opencl.md` | OpenCL | OpenCL | `[gpu, opencl, portability]` |
| 5 | `openmp-and-openacc-offload.md` | OpenMP and OpenACC Offload | OpenMP & OpenACC | `[gpu, openmp, openacc, directives]` |
| 6 | `vulkan-and-directx-compute.md` | Vulkan and DirectX Compute | Vulkan & DirectX | `[gpu, vulkan, directx, compute-shaders]` |
| 7 | `metal-and-apple-silicon.md` | Metal and Apple Silicon | Metal & Apple Silicon | `[gpu, metal, apple, unified-memory]` |
| 8 | `webgpu.md` | WebGPU | WebGPU | `[gpu, webgpu, wgsl, browser]` |
| 9 | `choosing-a-portability-layer.md` | Choosing a Portability Layer | Choosing a Layer | `[gpu, portability, decision-guide]` |

**`12-npu-and-inference-accelerators/`** — tags start `[gpu, npu, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `what-is-an-npu.md` | What Is an NPU? | What Is an NPU? | `[gpu, npu, accelerators, architecture]` |
| 2 | `systolic-arrays-and-dataflow.md` | Systolic Arrays and Dataflow | Systolic Arrays | `[gpu, npu, systolic-array, dataflow]` |
| 3 | `google-tpu.md` | Google TPU | Google TPU | `[gpu, npu, tpu, xla]` |
| 4 | `edge-npus.md` | Edge NPUs | Edge NPUs | `[gpu, npu, edge, mobile]` |
| 5 | `jetson-and-dla.md` | NVIDIA Jetson and DLA | Jetson & DLA | `[gpu, npu, jetson, dla]` |
| 6 | `quantization-for-accelerators.md` | Quantization for Accelerators | Quantization | `[gpu, npu, quantization, int8]` |
| 7 | `tensorrt.md` | TensorRT | TensorRT | `[gpu, npu, tensorrt, inference]` |
| 8 | `onnx-and-runtimes.md` | ONNX and ONNX Runtime | ONNX & Runtimes | `[gpu, npu, onnx, inference]` |
| 9 | `openvino.md` | OpenVINO | OpenVINO | `[gpu, npu, openvino, intel]` |
| 10 | `compiler-stacks.md` | Compiler Stacks: XLA, TVM, MLIR | Compiler Stacks | `[gpu, npu, compilers, mlir]` |
| 11 | `deploying-to-accelerators.md` | Deploying to Accelerators | Deploying | `[gpu, npu, deployment, inference]` |

**`13-applied-kernels-and-patterns/`** — tags start `[gpu, cuda, kernels, ...]`

| # | file | title | sidebar_label | tags |
|---|---|---|---|---|
| 1 | `vector-add-and-saxpy.md` | Vector Add and SAXPY | Vector Add & SAXPY | `[gpu, cuda, kernels, bandwidth]` |
| 2 | `parallel-reduction.md` | Parallel Reduction, Optimized | Parallel Reduction | `[gpu, cuda, kernels, reduction]` |
| 3 | `prefix-sum.md` | Prefix Sum (Scan) | Prefix Sum | `[gpu, cuda, kernels, scan]` |
| 4 | `matrix-multiply.md` | Matrix Multiply: Naive to Tiled | Matrix Multiply | `[gpu, cuda, kernels, gemm]` |
| 5 | `matrix-multiply-tensor-cores.md` | Matrix Multiply on Tensor Cores | GEMM on Tensor Cores | `[gpu, cuda, kernels, tensor-cores]` |
| 6 | `matrix-transpose.md` | Matrix Transpose | Matrix Transpose | `[gpu, cuda, kernels, transpose]` |
| 7 | `histogram.md` | Histogram | Histogram | `[gpu, cuda, kernels, atomics]` |
| 8 | `stencil-and-convolution.md` | Stencil and Convolution | Stencil & Convolution | `[gpu, cuda, kernels, stencil]` |
| 9 | `sorting-on-the-gpu.md` | Sorting on the GPU | Sorting | `[gpu, cuda, kernels, sorting]` |
| 10 | `sparse-matrix-vector.md` | Sparse Matrix-Vector Multiply | Sparse Matrix-Vector | `[gpu, cuda, kernels, sparse]` |
| 11 | `softmax-and-layernorm.md` | Softmax and LayerNorm Kernels | Softmax & LayerNorm | `[gpu, cuda, kernels, softmax]` |
| 12 | `flash-attention.md` | FlashAttention, Explained | FlashAttention | `[gpu, cuda, kernels, attention]` |

- [ ] **Step 7: Create the image manifest**

`static/img/gpu/SOURCES.md`:

```md
# Image sources — `static/img/gpu/`

Third-party figures republished under `docs/gpu-computing/`. Every image referenced from a page
in that section has a row here, so any figure can be located, re-sourced, or removed without
searching 128 Markdown files.

| file | source_url | publisher | retrieved | notes |
|---|---|---|---|---|
```

- [ ] **Step 8: Verify the build**

Run: `npm run build`
Expected: exits 0. The `GPU & Accelerators` tab appears in the navbar with 14 categories and 129 pages.

- [ ] **Step 9: Verify the section renders**

Run: `npm run serve`
Open `http://localhost:3000/knowledge-base/docs/gpu-computing/readme`. Confirm the sidebar lists all 14 categories in the order in Step 4, with `Overview` (the readme) at the top. Stop the server.

- [ ] **Step 10: Format, lint, and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing static/img/gpu sidebars.js docusaurus.config.js
git commit -m "feat: scaffold GPU & Accelerators section"
```

---

### Task 2: Section landing page

**Files:**
- Modify: `docs/gpu-computing/readme.md`

**Interfaces:**
- Consumes: every path from Task 1.
- Produces: the canonical folder-map table and three learning paths that `00-overview/how-this-section-is-organised.md` expands on.

- [ ] **Step 1: Write the landing page**

Keep the Task 1 frontmatter unchanged. Body:

1. `# GPU & Accelerators`
2. Two paragraphs: a GPU is a throughput machine bolted onto a latency machine, and almost every performance question in the section reduces to *did you keep the memory system busy*. Say what the section covers (CUDA in depth, plus portable layers and inference accelerators) and what it does not (graphics/rendering — point at `docs/game-development/unreal-engine/12-rendering/`).
3. `:::info[How this is organised]` — 00–02 build the mental model, 03–07 are CUDA proper, 08–10 are what you use in production, 11–13 are portability, accelerators, and worked kernels. Say the folders are self-contained after 03.
4. `## Three learning paths` — a table, one row per path, columns `Path | Sequence | What you can do at the end`:
   - *Write fast CUDA kernels*: [CUDA Programming Model](./03-cuda-programming-model/your-first-kernel.md) → [Memory Model](./04-cuda-memory-model/memory-spaces-overview.md) → [Execution](./05-execution-and-synchronization/warp-execution-and-divergence.md) → [Kernel Optimization](./07-kernel-optimization/the-optimization-workflow.md) → [Applied Kernels](./13-applied-kernels-and-patterns/parallel-reduction.md)
   - *Understand the hardware*: [Foundations](./01-parallel-computing-foundations/flynn-taxonomy-simd-simt.md) → [Hardware Architecture](./02-gpu-hardware-architecture/anatomy-of-a-gpu.md) → [Tooling & Profiling](./09-tooling-profiling-and-debugging/nsight-compute.md)
   - *Deploy models on accelerators*: [Overview](./00-overview/cpu-vs-gpu-vs-npu.md) → [Libraries & Ecosystem](./08-libraries-and-ecosystem/choosing-a-library.md) → [NPUs & Inference Accelerators](./12-npu-and-inference-accelerators/what-is-an-npu.md)
5. `## Sections` — a 14-row table, columns `Section | What it covers`, each linking the folder's first page. Use the folder labels from Task 1 Step 4 and one-line descriptions drawn from the spec's folder briefs.
6. `## Conventions used here` — four bullets: CUDA C++ is the default language and appears in `cpp` fences; Python is confined to [Libraries and Ecosystem](./08-libraries-and-ecosystem/cuda-python-and-cupy.md); every compute-capability requirement is called out in a note; every performance number states the GPU it was measured on.
7. **No `## See also`** — the landing page's section table already serves that role (matches `docs/machine-learning/intro.md`).

- [ ] **Step 2: Verify the build**

Run: `npm run build`
Expected: exits 0. Every link in the two tables resolves — they all target Task 1 stubs.

- [ ] **Step 3: Format and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing/readme.md
git commit -m "docs: gpu section landing page"
```

---

### Task 3: `00-overview` — six pages

**Files:**
- Modify: all six files in `docs/gpu-computing/00-overview/`

**Interfaces:**
- Consumes: skeleton paths from Task 1.
- Produces: `glossary.md` anchors (`#warp`, `#occupancy`, `#coalescing`, `#compute-capability`, `#roofline`, `#quantization`, …) generated from its `###` headings — later plans link to `../00-overview/glossary.md` without anchors, so no anchor contract is required, but keep the heading text stable.

- [ ] **Step 1: Write `why-gpus-exist.md`**

Sections: `## Two ways to spend a transistor budget`, `## Latency machines and throughput machines`, `## How graphics produced a general compute engine`, `## What this buys you, and what it costs`.

Requirements:
- Opening prose frames the real question: not "GPUs are faster" but "GPUs spend area on ALUs instead of on caches and out-of-order machinery, and that only pays off when you have thousands of independent work items".
- A comparison table: `| | CPU core | GPU SM |` rows for out-of-order execution, branch prediction, cache per thread, threads in flight, peak FP32 throughput. State the concrete hardware for any number you give (e.g. "an H100 SXM at ~67 TFLOPS FP32").
- A Mermaid diagram contrasting the two die-area splits:
  ```mermaid
  flowchart LR
    subgraph CPU["CPU die area"]
      C1["Control + OoO"] --- C2["Large caches"] --- C3["Few ALUs"]
    end
    subgraph GPU["GPU die area"]
      G1["Small control"] --- G2["Small caches"] --- G3["Many ALUs"]
    end
  ```
- `:::info[The problem it solves]` on throughput-oriented work.
- `:::warning[...]` that peak FLOPS is almost never the number that matters — link forward to [Memory-Bound vs Compute-Bound](../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md).

See also: `cpu-vs-gpu-vs-npu.md`, `when-not-to-use-a-gpu.md`, `../01-parallel-computing-foundations/latency-throughput-and-hiding.md`, `../02-gpu-hardware-architecture/anatomy-of-a-gpu.md`, `../readme.md`.

- [ ] **Step 2: Write `cpu-vs-gpu-vs-npu.md`**

Sections: `## Three design points`, `## Control logic and flexibility`, `## Parallelism and memory`, `## Which workloads land where`, `## Where they overlap`.

Requirements:
- Central table with columns `| | CPU | GPU | NPU |` and rows: execution model, unit of parallelism, typical precisions, memory system, programmability, best-fit workload, worst-fit workload.
- Prose must make the NPU point sharply: an NPU trades programmability for energy per MAC, which is why phones ship one and why an operator it doesn't implement falls back to the CPU.
- Cross-link out to `docs/computer-science/cpu-architecture/` for CPU internals — use the relative path `../../computer-science/cpu-architecture/superscalar-and-out-of-order-execution.md`.
- `:::tip[...]` giving a one-line triage rule: branchy and serial → CPU; large regular data-parallel → GPU; fixed quantized inference graph at low power → NPU.

See also: `why-gpus-exist.md`, `the-accelerator-landscape.md`, `../12-npu-and-inference-accelerators/what-is-an-npu.md`, `../../computer-science/cpu-architecture/superscalar-and-out-of-order-execution.md`, `../readme.md`.

- [ ] **Step 3: Write `the-accelerator-landscape.md`**

Sections: `## Discrete GPUs`, `## Integrated and mobile`, `## Datacenter inference and training ASICs`, `## FPGAs`, `## The software stack each one implies`.

Requirements:
- A table `| Vendor | Hardware | Primary stack | Portable option |` covering NVIDIA (CUDA / HIP-via-hipify), AMD (ROCm/HIP / SYCL), Intel (oneAPI/Level Zero / SYCL, OpenVINO), Apple (Metal / MPS), Qualcomm (Hexagon SDK, QNN / ONNX Runtime), Google (TPU / XLA via JAX or PyTorch-XLA), Arm (Ethos-U / TFLite Micro), FPGA vendors (oneAPI FPGA, HLS).
- The section's thesis, stated plainly: hardware choice is mostly a software-stack choice, and stack maturity varies far more than peak FLOPS.
- `:::note[...]` that this table dates quickly — it reflects the landscape as of 2026, and the durable content is the *shape* of the tradeoff, not the model numbers.

See also: `cpu-vs-gpu-vs-npu.md`, `../11-portable-and-vendor-neutral/choosing-a-portability-layer.md`, `../12-npu-and-inference-accelerators/edge-npus.md`, `../readme.md`.

- [ ] **Step 4: Write `when-not-to-use-a-gpu.md`**

Sections: `## Transfer-dominated workloads`, `## Branchy and serial code`, `## Problems too small to fill the machine`, `## Latency-critical paths`, `## Amdahl in practice`, `## A checklist before you port`.

Requirements:
- A worked transfer-cost calculation: moving 1 GB over PCIe Gen4 x16 at ~25 GB/s effective takes ~40 ms round trip; a kernel that saves 10 ms of CPU time loses. Show the arithmetic.
- A worked Amdahl number: 90% of runtime offloaded and made infinitely fast still caps total speedup at 10×.
- A `cpp` snippet showing the pattern that kills throughput — a kernel launch inside a host loop with a `cudaMemcpy` on both sides — with `// ...` for the kernel body.
- `:::warning[...]` on `cudaDeviceSynchronize()` in a hot loop.
- Closing checklist as a numbered list: is there ≥10⁵ independent work items; is arithmetic intensity above ~1 FLOP/byte; can data stay resident on the device across iterations; is the tail latency budget above ~1 ms.

See also: `why-gpus-exist.md`, `../01-parallel-computing-foundations/amdahl-and-gustafson.md`, `../04-cuda-memory-model/pinned-memory-and-transfers.md`, `../readme.md`.

- [ ] **Step 5: Write `how-this-section-is-organised.md`**

Sections: `## The folder map`, `## Three learning paths`, `## What is deliberately not here`, `## Conventions`.

Requirements:
- Expands the `readme.md` tables rather than duplicating them: each of the 14 folders gets a short paragraph on what it assumes you already know and what it hands to the next folder.
- A Mermaid dependency graph of the folders:
  ```mermaid
  flowchart TD
    F00["00 Overview"] --> F01["01 Foundations"] --> F02["02 Hardware"]
    F02 --> F03["03 Programming Model"] --> F04["04 Memory"] --> F05["05 Execution"]
    F05 --> F06["06 Runtime APIs"] --> F07["07 Optimization"]
    F07 --> F09["09 Tooling"]
    F07 --> F13["13 Applied Kernels"]
    F06 --> F08["08 Libraries"] --> F10["10 Multi-GPU"]
    F03 --> F11["11 Portability"]
    F00 --> F12["12 NPUs"]
  ```
- `## What is deliberately not here`: graphics/rendering pipelines, ML theory (points at `../../machine-learning/intro.md`), and pre-CUDA-12 material.

See also: `glossary.md`, `why-gpus-exist.md`, `../readme.md`.

- [ ] **Step 6: Write `glossary.md`**

Sections: one `##` per letter group is *not* wanted. Use a single `## Terms` with `###` per term, alphabetical.

Requirements:
- One `###` heading per term, one paragraph each, ending with a link to the page that covers it properly. Terms, at minimum: Arithmetic intensity, Bank conflict, Coalescing, Compute capability, Cooperative group, CUDA core, Divergence, Grid / block / thread, HBM, Host and device, Kernel, Occupancy, PTX, Roofline, SASS, Shared memory, SM (streaming multiprocessor), Stream, Tensor core, TFLOPS, Thread block cluster, Warp, Quantization.
- Every definition must be self-contained enough to read alone — this page is a lookup target, not a narrative.
- No admonitions on this page.

See also: `how-this-section-is-organised.md`, `../02-gpu-hardware-architecture/anatomy-of-a-gpu.md`, `../03-cuda-programming-model/threads-blocks-and-grids.md`, `../readme.md`.

- [ ] **Step 7: Verify the build**

Run: `npm run build`
Expected: exits 0.

- [ ] **Step 8: Format, lint, and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing/00-overview
git commit -m "docs: gpu overview pages"
```

---

### Task 4: `01-parallel-computing-foundations` — seven pages

**Files:**
- Modify: all seven files in `docs/gpu-computing/01-parallel-computing-foundations/`

**Interfaces:**
- Consumes: `00-overview` pages from Task 3.
- Produces: the roofline vocabulary (ridge point, arithmetic intensity, achieved vs peak bandwidth) that plans 3 and 4 reuse in `07-kernel-optimization/the-optimization-workflow.md` and `09-tooling-profiling-and-debugging/roofline-in-practice.md`.

- [ ] **Step 1: Write `flynn-taxonomy-simd-simt.md`**

Sections: `## Flynn's four categories`, `## SIMD: one instruction, one register width`, `## SIMT: one instruction, many threads`, `## Why the distinction changes how you write code`.

Requirements:
- Explain SIMT's difference concretely: each thread has its own register state and (from CC 7.0+) its own program counter, so divergence is legal but costs execution slots — where SIMD lanes have no independent control flow at all.
- A `cpp` snippet showing an AVX intrinsic loop next to the equivalent CUDA kernel, so the reader sees "explicit vector width" vs "implicit via block size".
- `:::note[...]` that a "CUDA core" is a lane, not a core, and 32 lanes issue together as a warp — link to [Warps and Warp Schedulers](../02-gpu-hardware-architecture/warps-and-schedulers.md).

See also: `parallel-patterns.md`, `../02-gpu-hardware-architecture/warps-and-schedulers.md`, `../05-execution-and-synchronization/warp-execution-and-divergence.md`, `../readme.md`.

- [ ] **Step 2: Write `amdahl-and-gustafson.md`**

Sections: `## Amdahl's law`, `## Strong scaling in practice`, `## Gustafson's law and weak scaling`, `## Which law applies to you`.

Requirements:
- Both formulas, then a table of speedup vs serial fraction: serial fraction 1%, 5%, 10%, 25% at 8, 64, 1024 workers.
- Prose has to land the practical point: the serial fraction on a GPU is usually *transfers and launches*, not arithmetic, so the fix is usually structural, not algorithmic.
- `:::tip[...]` — measure the serial fraction before optimizing the parallel part.

See also: `latency-throughput-and-hiding.md`, `../00-overview/when-not-to-use-a-gpu.md`, `../10-multi-gpu-and-scaling/multi-gpu-basics.md`, `../readme.md`.

- [ ] **Step 3: Write `latency-throughput-and-hiding.md`**

Sections: `## Little's Law`, `## Why a GPU runs thousands of threads`, `## Occupancy as concurrency, not as a score`, `## Worked example`.

Requirements:
- Little's Law stated and applied: to sustain 2 TB/s at ~500 ns DRAM latency you need ~1 MB of memory requests in flight; show the arithmetic and name the GPU generation the numbers describe.
- A Mermaid diagram of the scheduler switching between warps as each stalls (use `flowchart`, not `gantt` — gantt task labels with parentheses are a build hazard):
  ```mermaid
  flowchart LR
    W0["Warp 0 issues load"] -->|"stalls on DRAM"| W1["Warp 1 issues load"]
    W1 -->|"stalls on DRAM"| W2["Warp 2 issues load"]
    W2 -->|"stalls on DRAM"| W3["Warp 3 issues load"]
    W3 -->|"Warp 0 data arrives"| W0
  ```
  The point the prose must make: the scheduler is never idle as long as *some* warp is eligible, which is why the machine needs many more warps than it can issue.
- `:::info[...]` framing: latency hiding is the entire reason the programming model exposes so many threads.

See also: `arithmetic-intensity-and-roofline.md`, `../02-gpu-hardware-architecture/register-file-and-occupancy.md`, `../07-kernel-optimization/occupancy-tuning.md`, `../readme.md`.

- [ ] **Step 4: Write `arithmetic-intensity-and-roofline.md`**

Sections: `## Arithmetic intensity`, `## The roofline`, `## The ridge point`, `## Classifying a kernel before you touch it`, `## Limits of the model`.

Requirements:
- Define AI as FLOPs ÷ bytes moved from DRAM, and compute it for three kernels: SAXPY (≈0.083 FLOP/byte), a 3-point stencil, and a tiled SGEMM with tile size 32 (≈16 FLOP/byte). Show each calculation.
- Give the ridge point formula (peak FLOPS ÷ peak bandwidth) and compute it for one named GPU, stating the generation.
- Describe the roofline plot in prose and axes; do **not** hand-draw it in Mermaid (Mermaid cannot do log-log scatter). The measured version is deferred to [Roofline Analysis in Practice](../09-tooling-profiling-and-debugging/roofline-in-practice.md).
- `:::warning[...]` on the model's blind spots: it ignores latency-bound kernels, cache reuse it can't see, and instruction mix.

See also: `memory-bound-vs-compute-bound.md`, `latency-throughput-and-hiding.md`, `../09-tooling-profiling-and-debugging/roofline-in-practice.md`, `../readme.md`.

- [ ] **Step 5: Write `memory-bound-vs-compute-bound.md`**

Sections: `## How to tell which you are`, `## Why most kernels are memory-bound`, `## What each diagnosis implies`, `## The third case: latency-bound`.

Requirements:
- A decision table `| Symptom | Likely limiter | First thing to try |` with rows for high DRAM throughput + low SM busy, high SM busy + low DRAM, both low (→ latency/occupancy), both high (→ you are done).
- Name the Nsight Compute metrics by their real names — `dram__throughput.avg.pct_of_peak_sustained_elapsed`, `sm__throughput.avg.pct_of_peak_sustained_elapsed` — and say they are covered in [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).
- `:::tip[...]` the "both low" case is the most common and the most misdiagnosed.

See also: `arithmetic-intensity-and-roofline.md`, `../07-kernel-optimization/the-optimization-workflow.md`, `../09-tooling-profiling-and-debugging/metrics-that-matter.md`, `../readme.md`.

- [ ] **Step 6: Write `parallel-patterns.md`**

Sections: `## Map`, `## Reduce`, `## Scan`, `## Gather and scatter`, `## Stencil`, `## Histogram`, `## Sort`, `## Composing patterns`.

Requirements:
- Each pattern gets: one-sentence definition, its data-access shape, its parallelization difficulty, and a forward link to the folder-13 page that implements it.
- A summary table `| Pattern | Work | Communication | Implemented in |`.
- Prose must set up the section's shared vocabulary — say explicitly that later pages assume these names.

See also: `flynn-taxonomy-simd-simt.md`, `../13-applied-kernels-and-patterns/parallel-reduction.md`, `../13-applied-kernels-and-patterns/prefix-sum.md`, `../08-libraries-and-ecosystem/cub.md`, `../readme.md`.

- [ ] **Step 7: Write `the-host-device-model.md`**

Sections: `## Two machines, two address spaces`, `## The offload cycle`, `## Asynchrony is the default`, `## The same model in HIP, SYCL, and OpenCL`.

Requirements:
- A Mermaid diagram of the offload cycle with quoted edge labels:
  ```mermaid
  flowchart LR
    H["Host memory"] -->|"H2D copy"| D["Device memory"]
    D -->|"kernel reads/writes"| D
    D -->|"D2H copy"| H
  ```
- A table mapping the concepts across CUDA / HIP / SYCL / OpenCL: device, queue-or-stream, kernel, device allocation, explicit copy.
- `:::note[...]` that unified and shared-virtual memory blur the address-space split without removing the transfer cost — forward to [Unified Memory](../04-cuda-memory-model/unified-memory.md).

See also: `latency-throughput-and-hiding.md`, `../03-cuda-programming-model/your-first-kernel.md`, `../11-portable-and-vendor-neutral/the-portability-problem.md`, `../readme.md`.

- [ ] **Step 8: Verify the build**

Run: `npm run build`
Expected: exits 0.

- [ ] **Step 9: Format, lint, and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing/01-parallel-computing-foundations
git commit -m "docs: parallel computing foundations pages"
```

---

### Task 5: `02-gpu-hardware-architecture`, pages 1–5

**Files:**
- Modify: `anatomy-of-a-gpu.md`, `streaming-multiprocessor.md`, `warps-and-schedulers.md`, `register-file-and-occupancy.md`, `cache-hierarchy.md`

**Interfaces:**
- Consumes: Task 4's latency-hiding vocabulary.
- Produces: the occupancy-limiter model (registers / shared memory / block slots) that `07-kernel-optimization/occupancy-tuning.md` builds on.

- [ ] **Step 1: Write `anatomy-of-a-gpu.md`**

Sections: `## Top-down`, `## What a "core" actually is`, `## The memory side`, `## Reading a spec sheet`.

Requirements:
- Mermaid tree: GPU → GPCs → TPCs → SMs → sub-partitions → lanes, with L2 and memory controllers as siblings of the GPC group.
- `:::warning[...]` that "CUDA cores" in marketing material counts FP32 lanes, so a "16,896-core" GPU has ~132 SMs, not 16,896 independent processors. State the GPU generation used for the numbers.
- A table decoding a spec sheet line by line: SM count, cores per SM, boost clock, memory type, bus width, peak bandwidth, L2 size.

See also: `streaming-multiprocessor.md`, `device-memory-and-bandwidth.md`, `../00-overview/glossary.md`, `../readme.md`.

- [ ] **Step 2: Write `streaming-multiprocessor.md`**

Sections: `## Sub-partitions`, `## Functional units`, `## The register file`, `## Shared memory and L1`, `## What limits how much fits`.

Requirements:
- Mermaid diagram of one SM: 4 sub-partitions each with a warp scheduler, dispatch unit, register file slice, and FP32/INT32/tensor units; shared L1/shared-memory block and LSU/SFU below.
- Concrete numbers with the generation named — e.g. on Hopper (CC 9.0), 64 KB of registers per sub-partition, 256 KB combined L1/shared per SM, 32 KB … 227 KB configurable shared.
- `:::note[...]` that these numbers change every generation and the durable content is the structure.

See also: `warps-and-schedulers.md`, `register-file-and-occupancy.md`, `cache-hierarchy.md`, `../04-cuda-memory-model/shared-memory.md`, `../readme.md`.

- [ ] **Step 3: Write `warps-and-schedulers.md`**

Sections: `## Why 32`, `## Eligible, stalled, and selected`, `## Issue rate and dual issue`, `## Scheduling as the latency-hiding mechanism`, `## Stall reasons you will actually see`.

Requirements:
- A table of the common Nsight Compute stall reasons and what each means: `stall_long_scoreboard` (waiting on global/local memory), `stall_short_scoreboard` (shared memory / MIO), `stall_barrier`, `stall_not_selected`, `stall_wait`. State that these are covered in depth in [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).
- `:::tip[...]` — `stall_not_selected` being high is a *good* sign: you have enough parallelism.

See also: `register-file-and-occupancy.md`, `../05-execution-and-synchronization/warp-execution-and-divergence.md`, `../09-tooling-profiling-and-debugging/metrics-that-matter.md`, `../readme.md`.

- [ ] **Step 4: Write `register-file-and-occupancy.md`**

Sections: `## The register file is the scarce resource`, `## Occupancy is a hardware-limit calculation`, `## The three limiters`, `## Worked example`, `## Why maximum occupancy is not the goal`.

Requirements:
- Give the occupancy calculation explicitly and work one example end to end: 64 registers/thread, 48 KB shared per block, 256 threads/block, on an SM with 65,536 registers and 164 KB shared → compute blocks/SM from each of the three limiters and take the minimum. Show all three numbers.
- `:::warning[...]` that raising occupancy by cutting registers can cost more (spills) than it gains — forward to [Registers and Local Memory](../04-cuda-memory-model/registers-and-local-memory.md).
- Mention `cudaOccupancyMaxActiveBlocksPerMultiprocessor` by name, deferring usage to [Choosing a Launch Configuration](../03-cuda-programming-model/launch-configuration.md).

See also: `streaming-multiprocessor.md`, `warps-and-schedulers.md`, `../03-cuda-programming-model/launch-configuration.md`, `../07-kernel-optimization/occupancy-tuning.md`, `../readme.md`.

- [ ] **Step 5: Write `cache-hierarchy.md`**

Sections: `## The unified L1 and shared memory`, `## L2`, `## Sectors, not cache lines`, `## The read-only path`, `## What is and is not cached`.

Requirements:
- The key mechanical fact stated precisely: a global load is served in 32-byte sectors from 128-byte lines, so a warp's access pattern determines how many sectors are fetched — this is the mechanism behind coalescing, covered in [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md).
- Cross-link to `../../computer-science/memory-hierarchy/cpu-caches.md` and say explicitly what carries over (locality, line granularity) and what does not (no coherence between SMs' L1s; L1 is not write-back for global by default).
- `:::note[...]` on `__ldg` and the read-only cache being largely automatic on modern architectures.

See also: `device-memory-and-bandwidth.md`, `../04-cuda-memory-model/global-memory-and-coalescing.md`, `../../computer-science/memory-hierarchy/cpu-caches.md`, `../readme.md`.

- [ ] **Step 6: Verify the build**

Run: `npm run build`
Expected: exits 0.

- [ ] **Step 7: Format, lint, and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing/02-gpu-hardware-architecture
git commit -m "docs: gpu hardware architecture, part 1"
```

---

### Task 6: `02-gpu-hardware-architecture`, pages 6–10

**Files:**
- Modify: `device-memory-and-bandwidth.md`, `tensor-cores.md`, `nvidia-architecture-generations.md`, `compute-capability.md`, `interconnects-pcie-and-nvlink.md`

**Interfaces:**
- Consumes: Task 5's SM and cache model.
- Produces: the compute-capability table that every later `:::note[Requires CC X.Y]` refers back to, and the tensor-core precision table reused by `07-kernel-optimization/programming-tensor-cores.md`.

- [ ] **Step 1: Write `device-memory-and-bandwidth.md`**

Sections: `## GDDR and HBM`, `## Peak versus achievable`, `## Measuring effective bandwidth`, `## Bandwidth as the usual ceiling`.

Requirements:
- The effective-bandwidth formula — `(bytes_read + bytes_written) / seconds` — and a worked SAXPY case: 3 arrays × 4 bytes × N elements, so a kernel achieving 80% of peak is near optimal and no amount of arithmetic tuning will help.
- A table `| Memory | Bus width | Typical peak | Where you find it |` for GDDR6X and HBM2e/HBM3/HBM3e, each row naming a real product generation.
- `:::tip[...]` that 80–90% of peak is the realistic ceiling for a streaming kernel; treat peak as a denominator, not a target.

See also: `cache-hierarchy.md`, `../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md`, `../13-applied-kernels-and-patterns/vector-add-and-saxpy.md`, `../readme.md`.

- [ ] **Step 2: Write `tensor-cores.md`**

Sections: `## The MMA primitive`, `## Precisions by generation`, `## Throughput versus CUDA cores`, `## What makes a kernel eligible`, `## How you actually reach them`.

Requirements:
- Table `| Generation | Introduced precisions | Notes |` for Volta (FP16), Turing (INT8/INT4), Ampere (BF16, TF32, structured sparsity), Ada (FP8), Hopper (FP8, TMA-fed, wgmma), Blackwell (FP4/FP6).
- State the eligibility conditions concretely: shapes must match a supported MMA tile, operands must live in the right fragment layout, and the accumulator precision is usually FP32 even when inputs are FP16.
- `:::tip[...]` — most code should reach tensor cores through cuBLAS/CUTLASS/cuDNN, not `wmma`; forward to [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md).

See also: `nvidia-architecture-generations.md`, `../07-kernel-optimization/programming-tensor-cores.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md`, `../readme.md`.

- [ ] **Step 3: Write `nvidia-architecture-generations.md`**

Sections: one `##` per generation: `## Volta (CC 7.0)`, `## Turing (CC 7.5)`, `## Ampere (CC 8.0 / 8.6)`, `## Ada Lovelace (CC 8.9)`, `## Hopper (CC 9.0)`, `## Blackwell (CC 10.x / 12.x)`, then `## What actually changed for programmers`.

Requirements:
- Each generation section lists what it added *that changes code*, not marketing features: Volta → independent thread scheduling and `_sync` intrinsics; Turing → INT8/INT4 tensor cores; Ampere → async copy (`cuda::memcpy_async`), BF16/TF32, L2 residency control; Ada → FP8; Hopper → thread block clusters, distributed shared memory, TMA, `wgmma`; Blackwell → FP4/FP6 and further tensor-memory changes.
- The closing section is a table `| Feature | Requires CC |` — this is the canonical table later `:::note` blocks point at.

See also: `compute-capability.md`, `tensor-cores.md`, `../03-cuda-programming-model/thread-block-clusters.md`, `../04-cuda-memory-model/asynchronous-data-movement.md`, `../readme.md`.

- [ ] **Step 4: Write `compute-capability.md`**

Sections: `## What the number gates`, `## Virtual and real architectures`, `## `-arch`, `-code`, and `-gencode``, `## Forward compatibility and JIT`, `## What to ship`.

Requirements:
- Explain `compute_XX` (virtual, produces PTX) vs `sm_XX` (real, produces SASS) precisely, then show the flags:
  ```bash
  # SASS for Ampere and Hopper, plus PTX for future JIT
  nvcc -gencode arch=compute_80,code=sm_80 \
       -gencode arch=compute_90,code=sm_90 \
       -gencode arch=compute_90,code=compute_90 \
       kernel.cu -o kernel
  ```
- `:::warning[...]` that shipping only SASS means a newer GPU fails to launch with `no kernel image is available for execution on the device`; the trailing `code=compute_90` line is what prevents it.
- `:::note[...]` on the JIT cache (`CUDA_CACHE_PATH`) and the first-run latency it hides.

See also: `nvidia-architecture-generations.md`, `../03-cuda-programming-model/the-compilation-model.md`, `../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md`, `../readme.md`.

- [ ] **Step 5: Write `interconnects-pcie-and-nvlink.md`**

Sections: `## PCIe`, `## NVLink and NVSwitch`, `## Topology decides strategy`, `## Discovering your topology`.

Requirements:
- Table `| Link | Generation | Per-direction bandwidth | Typical use |` for PCIe Gen3/4/5 x16 and NVLink 3/4/5, each figure labelled with the generation it belongs to.
- A `bash` snippet running `nvidia-smi topo -m` with an annotated sample output showing `NV18`, `PIX`, `SYS` and what each implies.
- `:::tip[...]` — measure P2P bandwidth before designing a multi-GPU decomposition; forward to [Peer-to-Peer Access and NVLink](../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md).

See also: `device-memory-and-bandwidth.md`, `../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md`, `../10-multi-gpu-and-scaling/gpudirect-and-rdma.md`, `../readme.md`.

- [ ] **Step 6: Verify the build**

Run: `npm run build`
Expected: exits 0.

- [ ] **Step 7: Format, lint, and commit**

```bash
npm run format
npm run lint
git add docs/gpu-computing/02-gpu-hardware-architecture
git commit -m "docs: gpu hardware architecture, part 2"
```

---

### Task 7: Figures for folders 00–02

Downloads the vendor figures this plan's pages reference, records their provenance, and inserts them.

**Files:**
- Create: `static/img/gpu/02-gpu-hardware-architecture/*.png`
- Modify: `static/img/gpu/SOURCES.md`
- Modify: `docs/gpu-computing/02-gpu-hardware-architecture/anatomy-of-a-gpu.md`, `streaming-multiprocessor.md`

**Interfaces:**
- Consumes: pages from Tasks 5–6.
- Produces: the `SOURCES.md` row format and `static/img/gpu/<folder-slug>/` layout that plans 2–6 follow.

- [ ] **Step 1: Download the two architecture figures**

The CUDA C++ Programming Guide publishes its figures as stable PNGs under `_images/`. Download two:

```bash
mkdir -p static/img/gpu/02-gpu-hardware-architecture
curl -fsSL -o static/img/gpu/02-gpu-hardware-architecture/automatic-scalability.png \
  https://docs.nvidia.com/cuda/cuda-c-programming-guide/_images/automatic-scalability.png
curl -fsSL -o static/img/gpu/02-gpu-hardware-architecture/memory-hierarchy.png \
  https://docs.nvidia.com/cuda/cuda-c-programming-guide/_images/memory-hierarchy.png
```

- [ ] **Step 2: Verify both downloads**

Run: `file static/img/gpu/02-gpu-hardware-architecture/*.png && du -h static/img/gpu/02-gpu-hardware-architecture/*.png`
Expected: both report `PNG image data` with a non-trivial size.

**If either `curl` returns 404 or the file is not a PNG:** delete the file, skip Steps 3–4 for that figure, and keep the Mermaid diagram already on the page. Do not substitute an image from a different source without checking its terms. Record the skip in the commit message.

- [ ] **Step 3: Add the `SOURCES.md` rows**

Append to the table in `static/img/gpu/SOURCES.md` (replace `<today>` with the actual ISO date):

```md
| `02-gpu-hardware-architecture/automatic-scalability.png` | https://docs.nvidia.com/cuda/cuda-c-programming-guide/ | NVIDIA | <today> | Figure from the CUDA C++ Programming Guide; NVIDIA documentation terms. |
| `02-gpu-hardware-architecture/memory-hierarchy.png` | https://docs.nvidia.com/cuda/cuda-c-programming-guide/ | NVIDIA | <today> | Figure from the CUDA C++ Programming Guide; NVIDIA documentation terms. |
```

- [ ] **Step 4: Reference the figures from the pages**

In `anatomy-of-a-gpu.md`, inside `## Top-down`, after the Mermaid tree:

```md
![A grid of blocks scheduled across a varying number of SMs](/img/gpu/02-gpu-hardware-architecture/automatic-scalability.png)
*Source: [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)*
```

In `streaming-multiprocessor.md`, inside `## Shared memory and L1`:

```md
![CUDA memory hierarchy: per-thread, per-block, and global memory](/img/gpu/02-gpu-hardware-architecture/memory-hierarchy.png)
*Source: [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)*
```

- [ ] **Step 5: Verify the build and the rendered images**

Run: `npm run build && npm run serve`
Open `http://localhost:3000/knowledge-base/docs/gpu-computing/02-gpu-hardware-architecture/anatomy-of-a-gpu`. Confirm the image renders (a broken image means the `/knowledge-base/` prefix is missing). Stop the server.

- [ ] **Step 6: Format, lint, and commit**

```bash
npm run format
npm run lint
git add static/img/gpu docs/gpu-computing/02-gpu-hardware-architecture
git commit -m "docs: add architecture figures with source manifest"
```

---

## Plan 1 completion criteria

- `npm run build` exits 0 and `npm run lint` exits 0.
- The navbar shows six tabs, `GPU & Accelerators` sixth.
- `docs/gpu-computing/` contains 129 Markdown files and 14 `_category_.json` files; 24 of the Markdown files are fully written, 105 remain stubs for plans 2–6.
- `static/img/gpu/SOURCES.md` has a row for every file under `static/img/gpu/`.
