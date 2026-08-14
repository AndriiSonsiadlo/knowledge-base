# GPU & Accelerators — Plan 3: CUDA Runtime APIs and Kernel Optimization

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the 20 pages of `06-cuda-runtime-and-apis/` and `07-kernel-optimization/` — the host-side API surface and the optimization discipline that uses it.

**Architecture:** Every file already exists as a stub with correct frontmatter (plan 1, task 1). This plan fills in bodies only, so `npm run build` (`onBrokenLinks: "throw"`) passes after every task.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism `cpp`/`bash`/`text` fences, Biome, Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Prerequisite:** Plans 1 and 2 complete. Verify: `ls docs/gpu-computing/06-cuda-runtime-and-apis/` shows nine `.md` files, and `grep -rl "warpReduceSum" docs/gpu-computing/05-execution-and-synchronization/` returns two files.

**Plan series:** plan 3 of 6.

---

## Global Constraints

These apply to **every** page this plan writes and are not restated per task.

### Frontmatter

Already written by plan 1. **Do not change `id`, `title`, `sidebar_label`, `sidebar_position`, or `tags`.** Replace only the body below the frontmatter.

### Page structure

1. `# H1` matching `title` exactly (already in the stub).
2. 1–2 paragraphs of prose framing **what problem this solves**, before any API detail. No page opens with a code block, a bullet list, or a definition list.
3. `##` sections per subtopic. `###` sparingly.
4. Ends with `## See also` — 3–5 bullets, **plain relative Markdown links**:
   `- [Link text](./relative-path.md) — one-line reason to go there.`
   Order: siblings first, then cross-folder, then `../readme.md` last.

**Do not use `<Icon icon="lucide:..." />`.**

### Admonitions

Only `:::info[...]` (framing a problem), `:::note[...]` (side facts, version / CC caveats), `:::tip[...]` (practical guidance), `:::warning[...]` (pitfalls, correctness traps, performance cliffs).

### Code fences

- **CUDA C++ uses ` ```cpp `.** PTX and SASS use ` ```text `. Also permitted: `bash`, `cmake`, `json`.
- **No `python` anywhere in this plan.**
- `showLineNumbers` on fences longer than ~5 lines; `title="filename.cu"` for standalone files.
- **`CUDA_CHECK` is defined in exactly one place: `06-cuda-runtime-and-apis/error-handling.md`, written in Task 2 of this plan.** Every other page in the whole section uses it without redefining it.

### MDX hazards

Outside code fences and inline backticks, always backtick: `__global__`, `__device__`, `__shared__`, `__launch_bounds__`, `__syncthreads`, `<<<grid, block>>>`, `<T>`, and any bare `{` or `}`.

### Diagrams

Mermaid for structural content. **Quote every edge label:** `A -->|"label (with parens)"| B` (an unescaped label broke a build before — commit `958a2e6`).

### Performance claims

**Every performance number on an optimization page states the hardware generation it applies to.** "3.2× faster" is not acceptable; "3.2× faster on an A100 (CC 8.0) at N = 2²⁴" is. If you cannot attribute a number, describe the direction and mechanism instead of inventing a figure.

### Content currency

CUDA 13.x. Clusters, distributed shared memory, TMA, `cuda::memcpy_async` / `cuda::pipeline`, Cooperative Groups, `__shfl_sync`-family only, architecture coverage through Blackwell. Dynamic parallelism means **CDP2** semantics.

### Verification gate — every task

1. `npm run build` exits 0.
2. `npm run format` then `npm run lint` — both exit 0.
3. Commit. One-line message, `<type>: <what>`. **Never** add a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

---

## File Structure

```
docs/gpu-computing/
├── 06-cuda-runtime-and-apis/    9 pages   Task 1 (1-5), Task 2 (6-9)
└── 07-kernel-optimization/     11 pages   Task 3 (1-4), Task 4 (5-8), Task 5 (9-11)

static/img/gpu/
├── 07-kernel-optimization/                Task 6
└── SOURCES.md                             Task 6 (append rows)
```

---

### Task 1: `06-cuda-runtime-and-apis`, pages 1–5

**Files:**
- Modify: `runtime-vs-driver-api.md`, `device-management.md`, `memory-allocation-apis.md`, `streams-and-concurrency.md`, `events-and-timing.md`

**Interfaces:**
- Consumes: `04-cuda-memory-model/pinned-memory-and-transfers.md` (the four-stream overlap loop).
- Produces: the stream/event vocabulary that `cuda-graphs.md`, `07-kernel-optimization/the-optimization-workflow.md`, and `09-tooling-profiling-and-debugging/benchmarking-methodology.md` all build on.

- [ ] **Step 1: Write `runtime-vs-driver-api.md`**

Sections: `## Two APIs over one driver`, `## Contexts`, `## Modules and `cuLaunchKernel``, `## The primary context`, `## When you need the driver API`.

Requirements:
- A side-by-side table `| Concept | Runtime API | Driver API |` for initialization, context, module loading, kernel launch, symbol lookup, error type.
- Show the same launch both ways — `<<<>>>` versus `cuLaunchKernel` with its `void* args[]` array — so the reader sees exactly what the runtime hides.
- The primary-context rule stated clearly: the runtime API lazily creates and shares a *primary* context per device; driver-API code that creates its own context and mixes with runtime calls is the classic source of "invalid device context" errors. `cuDevicePrimaryCtxRetain` is the interop path.
- `:::tip[...]` — the honest recommendation: use the runtime API. Reach for the driver API only for JIT-loading cubins/PTX at runtime, for multiple isolated contexts, or when writing a language binding.
- `:::note[...]` that CUDA 12 added `cuda::core`/`cuda.bindings` on the Python side as a modern wrapper over the driver API; see [CUDA Python and CuPy](../08-libraries-and-ecosystem/cuda-python-and-cupy.md).

See also: `device-management.md`, `../03-cuda-programming-model/the-compilation-model.md`, `../08-libraries-and-ecosystem/cuda-python-and-cupy.md`, `../readme.md`.

- [ ] **Step 2: Write `device-management.md`**

Sections: `## Enumerating devices`, `## `cudaDeviceProp``, `## Selecting a device`, `## Per-thread device state`, `## Resetting`.

Requirements:
- A complete enumeration snippet printing the fields that actually matter:
  ```cpp showLineNumbers
  int count = 0;
  CUDA_CHECK(cudaGetDeviceCount(&count));
  for (int d = 0; d < count; ++d) {
      cudaDeviceProp p{};
      CUDA_CHECK(cudaGetDeviceProperties(&p, d));
      printf("%d: %s  CC %d.%d  SMs %d  global %.1f GiB  shared/SM %zu KiB\n",
             d, p.name, p.major, p.minor, p.multiProcessorCount,
             p.totalGlobalMem / 1073741824.0,
             p.sharedMemPerMultiprocessor / 1024);
  }
  ```
- A table of the high-value `cudaDeviceProp` fields: `major`/`minor`, `multiProcessorCount`, `maxThreadsPerBlock`, `sharedMemPerBlock`, `regsPerBlock`, `warpSize`, `memoryBusWidth`, `memoryClockRate`, `l2CacheSize`, `concurrentKernels`, `unifiedAddressing` — each with what decision it informs.
- The threading rule: `cudaSetDevice` sets *thread-local* state; every host thread that touches the GPU must set it, and allocations belong to the device current at allocation time.
- `:::warning[...]` that `cudaDeviceReset()` destroys all allocations and contexts on the device — it belongs at the end of a program (and in profiling runs so the profiler flushes), never in a loop.
- `:::tip[...]` — `CUDA_VISIBLE_DEVICES` renumbers devices from the process's point of view; it is the cleanest way to pin a job to a GPU. Link [GPU Clusters and Schedulers](../10-multi-gpu-and-scaling/clusters-and-schedulers.md).

See also: `runtime-vs-driver-api.md`, `mps-and-mig.md`, `../10-multi-gpu-and-scaling/multi-gpu-basics.md`, `../readme.md`.

- [ ] **Step 3: Write `memory-allocation-apis.md`**

Sections: `## `cudaMalloc` and its cost`, `## Pitched allocations`, `## Stream-ordered allocation`, `## Memory pools`, `## The virtual memory management API`, `## Choosing`.

Requirements:
- State the cost up front, because it drives every other choice on the page: `cudaMalloc` and `cudaFree` are synchronizing, device-wide operations that can take tens of microseconds — allocating inside a hot loop is a common and invisible performance bug.
- `cudaMallocPitch` / `cudaMemcpy2D` with the reason: it pads each row so every row start is aligned for coalescing. Show the indexing (`row * pitch + col * sizeof(T)` with `pitch` in bytes).
- Stream-ordered allocation, which is the modern answer:
  ```cpp showLineNumbers
  cudaStream_t s;
  CUDA_CHECK(cudaStreamCreate(&s));

  float* d = nullptr;
  CUDA_CHECK(cudaMallocAsync(&d, bytes, s));   // ordered in the stream, from a pool
  myKernel<<<grid, block, 0, s>>>(d);
  CUDA_CHECK(cudaFreeAsync(d, s));             // returns to the pool, no device sync
  ```
  Explain the pool: freed memory is retained for reuse instead of returned to the driver, so a steady-state loop stops paying allocation cost entirely. Mention `cudaMemPoolSetAttribute` with `cudaMemPoolAttrReleaseThreshold`.
- The VMM API (`cuMemCreate`, `cuMemAddressReserve`, `cuMemMap`) in one short section: what it is for (growing an allocation without copying, physical/virtual separation) and that it is a driver-API facility most code never needs.
- A closing decision table `| Situation | Use |`.

See also: `streams-and-concurrency.md`, `../04-cuda-memory-model/unified-memory.md`, `../04-cuda-memory-model/pinned-memory-and-transfers.md`, `../readme.md`.

- [ ] **Step 4: Write `streams-and-concurrency.md`**

Sections: `## What a stream is`, `## The null stream`, `## Per-thread default stream`, `## Concurrent kernels`, `## Overlapping transfer and compute`, `## Priorities`, `## Making concurrency actually happen`.

Requirements:
- Definition first: a stream is an ordered queue; operations in one stream execute in issue order, operations in different streams have no ordering unless you create one with events.
- The null-stream trap, explained precisely because it silently destroys overlap: the legacy default stream implicitly synchronizes with all blocking streams, so one stray `kernel<<<g,b>>>(...)` in an otherwise-streamed pipeline serializes everything. The fixes: create streams with `cudaStreamNonBlocking`, or compile with `--default-stream per-thread`.
- A Mermaid timeline of three streams overlapping H2D, kernel, and D2H, with quoted labels.
- The checklist for why concurrency fails to appear, as a list: host memory not pinned; not enough work per kernel to leave SMs free; only one copy engine so H2D and D2H cannot overlap each other; implicit sync from `cudaMalloc`/`cudaFree`/`cudaMemcpy`(sync form)/`cudaDeviceSynchronize`.
- `:::tip[...]` — verify overlap in the Nsight Systems timeline, not by reasoning about the code. Link [Nsight Systems](../09-tooling-profiling-and-debugging/nsight-systems.md).
- Priorities via `cudaStreamCreateWithPriority` and `cudaDeviceGetStreamPriorityRange`, with the caveat that priority affects block scheduling, not preemption of running blocks.

See also: `events-and-timing.md`, `cuda-graphs.md`, `../04-cuda-memory-model/pinned-memory-and-transfers.md`, `../09-tooling-profiling-and-debugging/nsight-systems.md`, `../readme.md`.

- [ ] **Step 5: Write `events-and-timing.md`**

Sections: `## Events as markers`, `## Timing a kernel correctly`, `## Cross-stream dependencies`, `## Why wall-clock timing lies`, `## Polling versus blocking`.

Requirements:
- The correct timing pattern, complete, since this is the snippet the rest of the section refers to:
  ```cpp showLineNumbers
  cudaEvent_t start, stop;
  CUDA_CHECK(cudaEventCreate(&start));
  CUDA_CHECK(cudaEventCreate(&stop));

  myKernel<<<grid, block>>>(/* ... */);        // warm-up: JIT, cache, clocks
  CUDA_CHECK(cudaDeviceSynchronize());

  CUDA_CHECK(cudaEventRecord(start));
  for (int i = 0; i < iters; ++i) myKernel<<<grid, block>>>(/* ... */);
  CUDA_CHECK(cudaEventRecord(stop));
  CUDA_CHECK(cudaEventSynchronize(stop));

  float ms = 0.0f;
  CUDA_CHECK(cudaEventElapsedTime(&ms, start, stop));
  printf("%.3f ms/iter\n", ms / iters);
  ```
- The wall-clock failure explained: launches are asynchronous, so a host timer around a launch measures launch overhead, not execution — usually a few microseconds regardless of the kernel.
- Cross-stream dependency with `cudaEventRecord` + `cudaStreamWaitEvent`, shown in `cpp`, and the point that this is how you express a DAG without host synchronization.
- `:::note[...]` on `cudaEventCreateWithFlags(&e, cudaEventDisableTiming)` for pure dependency events (cheaper) and `cudaEventBlockingSync` for yielding the CPU instead of spinning.
- `:::warning[...]` that event timing includes queueing delays if other work is in the stream, and that clock boost makes the first measurements unrepresentative — forward to [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md).

See also: `streams-and-concurrency.md`, `../09-tooling-profiling-and-debugging/benchmarking-methodology.md`, `../07-kernel-optimization/the-optimization-workflow.md`, `../readme.md`.

- [ ] **Step 6: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/06-cuda-runtime-and-apis
git commit -m "docs: cuda runtime apis, part 1"
```
Expected: build exits 0.

---

### Task 2: `06-cuda-runtime-and-apis`, pages 6–9

**Files:**
- Modify: `cuda-graphs.md`, `dynamic-parallelism.md`, `error-handling.md`, `mps-and-mig.md`

**Interfaces:**
- Consumes: Task 1's stream and event model.
- Produces: **the `CUDA_CHECK` macro definition** — the single canonical definition for the whole section. Its exact text is fixed in Step 3 below; every other page in every plan calls it without redefining it.

- [ ] **Step 1: Write `cuda-graphs.md`**

Sections: `## The launch-overhead problem`, `## Stream capture`, `## Explicit construction`, `## Instantiate once, launch many`, `## Updating a graph`, `## Where graphs pay off`.

Requirements:
- Open with the arithmetic: a kernel launch costs roughly 3–10 µs of CPU-side work; a pipeline of 50 small kernels per iteration spends more time launching than computing. A graph collapses that into one launch.
- Stream capture shown in full, because it is the path most code should take:
  ```cpp showLineNumbers
  cudaGraph_t graph;
  cudaGraphExec_t exec;
  cudaStream_t s;
  CUDA_CHECK(cudaStreamCreate(&s));

  CUDA_CHECK(cudaStreamBeginCapture(s, cudaStreamCaptureModeGlobal));
  for (int i = 0; i < 50; ++i) smallKernel<<<grid, block, 0, s>>>(d_data, i);
  CUDA_CHECK(cudaStreamEndCapture(s, &graph));

  CUDA_CHECK(cudaGraphInstantiate(&exec, graph, nullptr, nullptr, 0));
  for (int step = 0; step < steps; ++step)
      CUDA_CHECK(cudaGraphLaunch(exec, s));      // one launch replaces 50
  CUDA_CHECK(cudaStreamSynchronize(s));
  ```
- Explicit construction (`cudaGraphAddKernelNode` and friends) described and shown briefly, with the reason to prefer it: an explicit DAG when the topology is known and not naturally expressible as a stream sequence.
- `cudaGraphExecKernelNodeSetParams` / `cudaGraphExecUpdate` for changing arguments without re-instantiating, and why that matters (instantiation is the expensive part).
- `:::warning[...]` — capture forbids synchronous calls and queries inside the captured region (`cudaMalloc`, `cudaMemcpy` sync form, `cudaStreamSynchronize` on the captured stream); those turn into capture errors.
- `:::tip[...]` — graphs help when kernels are short and numerous, and do nothing when one kernel dominates. Measure before adopting.

See also: `streams-and-concurrency.md`, `../07-kernel-optimization/kernel-fusion-and-launch-overhead.md`, `../09-tooling-profiling-and-debugging/nsight-systems.md`, `../readme.md`.

- [ ] **Step 2: Write `dynamic-parallelism.md`**

Sections: `## Launching from the device`, `## CDP2 semantics`, `## What it costs`, `## Depth and resource limits`, `## When it is the wrong tool`.

Requirements:
- A short `cpp` example of a device-side launch on an irregular workload (e.g. refining only the tiles that need it), compiled with `-rdc=true`.
- CDP2 semantics stated precisely, since this is where old material misleads: in CDP2 a parent grid **cannot** synchronize on its children with a device-side `cudaDeviceSynchronize()` — that API is removed from device code. Child work is guaranteed complete only when the parent grid itself completes, or via a stream/event mechanism at the parent's tail. Say that any tutorial calling `cudaDeviceSynchronize()` inside a kernel predates CDP2.
- The costs, concretely: each device-side launch has meaningfully higher overhead than a host launch, requires `-rdc=true` (see [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md)), and reserves device memory for the launch pool.
- `:::warning[...]` on unbounded recursion and the launch-depth limit.
- `:::tip[...]` — the usual better answers: a grid-stride loop with a work queue, a persistent kernel, or two host-launched kernels with a compacted work list. Reach for dynamic parallelism only when the child work is data-dependent, large, and irregular.

See also: `../03-cuda-programming-model/separate-compilation-and-linking.md`, `cuda-graphs.md`, `../07-kernel-optimization/kernel-fusion-and-launch-overhead.md`, `../readme.md`.

- [ ] **Step 3: Write `error-handling.md`**

Sections: `## Errors are asynchronous`, `## Sticky and non-sticky errors`, `## The `CUDA_CHECK` macro`, `## Checking after a launch`, `## Making a bug reproducible`.

Requirements:
- This page **defines the macro the entire section uses**. Use exactly this text:
  ```cpp showLineNumbers title="cuda_check.h"
  #pragma once
  #include <cuda_runtime.h>
  #include <cstdio>
  #include <cstdlib>

  #define CUDA_CHECK(call)                                                    \
      do {                                                                    \
          cudaError_t err_ = (call);                                          \
          if (err_ != cudaSuccess) {                                          \
              std::fprintf(stderr, "CUDA error %s at %s:%d: %s\n",            \
                           cudaGetErrorName(err_), __FILE__, __LINE__,        \
                           cudaGetErrorString(err_));                         \
              std::exit(EXIT_FAILURE);                                        \
          }                                                                   \
      } while (0)
  ```
  State immediately after it: *this macro is used unqualified on every other page in this section.*
- The launch case, which the macro alone does not cover, because `<<<>>>` returns nothing:
  ```cpp showLineNumbers
  myKernel<<<grid, block>>>(/* ... */);
  CUDA_CHECK(cudaGetLastError());        // catches launch-configuration errors
  CUDA_CHECK(cudaDeviceSynchronize());   // catches errors raised during execution
  ```
  `:::warning[...]` that the `cudaDeviceSynchronize()` line is a debug-build measure; leaving it in a hot loop destroys throughput.
- Sticky vs non-sticky, explained with consequences: a non-sticky error (e.g. `cudaErrorInvalidValue`) is cleared by `cudaGetLastError`; a sticky error (an illegal address in a kernel) corrupts the context — every subsequent call fails and the process must exit. This is why "my code fails at a random later call" happens.
- `:::tip[...]` — `CUDA_LAUNCH_BLOCKING=1` makes launches synchronous so the reported error location is the real one; use it only while debugging. Then `compute-sanitizer` for the actual diagnosis, see [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md).

See also: `device-management.md`, `../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md`, `../03-cuda-programming-model/your-first-kernel.md`, `../readme.md`.

- [ ] **Step 4: Write `mps-and-mig.md`**

Sections: `## One GPU, many processes`, `## Time-slicing (the default)`, `## Multi-Process Service`, `## Multi-Instance GPU`, `## Choosing between them`.

Requirements:
- A comparison table `| | Time-slicing | MPS | MIG |` with rows: isolation, memory partitioning, error containment, concurrency mechanism, supported hardware, typical use.
- MPS explained mechanically: client processes funnel into one server context so their kernels can run *concurrently* rather than in alternating time slices — which is why it helps small-kernel, low-occupancy workloads and does nothing for one process already saturating the GPU. Include the `bash` control commands (`nvidia-cuda-mps-control -d`, `echo quit | nvidia-cuda-mps-control`).
- MIG explained as a hardware partition: SMs, L2 slices, and memory controllers are physically divided, giving real fault and performance isolation. `nvidia-smi mig -cgi ... -C` shown in `bash`, and the resulting device UUIDs used with `CUDA_VISIBLE_DEVICES`.
- `:::note[...]` on availability — MIG requires A100-class or newer datacenter hardware; MPS is broadly available.
- `:::warning[...]` that MPS gives no memory-error containment: one client's illegal access can take down the server and all clients.

See also: `device-management.md`, `../10-multi-gpu-and-scaling/clusters-and-schedulers.md`, `streams-and-concurrency.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/06-cuda-runtime-and-apis
git commit -m "docs: cuda runtime apis, part 2"
```
Expected: build exits 0.

- [ ] **Step 6: Verify the `CUDA_CHECK` single-definition rule**

Run: `grep -rn "define CUDA_CHECK" docs/gpu-computing/`
Expected: **exactly one** hit, in `06-cuda-runtime-and-apis/error-handling.md`. If any other page defines it, delete that definition and leave the call sites alone.

---

### Task 3: `07-kernel-optimization`, pages 1–4

**Files:**
- Modify: `the-optimization-workflow.md`, `occupancy-tuning.md`, `memory-access-optimization.md`, `shared-memory-tiling.md`

**Interfaces:**
- Consumes: `01-parallel-computing-foundations/memory-bound-vs-compute-bound.md`, `04-cuda-memory-model/global-memory-and-coalescing.md`, `04-cuda-memory-model/bank-conflicts.md`.
- Produces: the tiled SGEMM kernel that `13-applied-kernels-and-patterns/matrix-multiply.md` extends with register tiling — keep the tile size `TILE = 32` and the kernel name `sgemmTiled` consistent between the two.

- [ ] **Step 1: Write `the-optimization-workflow.md`**

Sections: `## Measure first`, `## Classify the limiter`, `## Fix the dominant limiter only`, `## Re-measure`, `## Knowing when to stop`.

Requirements:
- The loop stated as the page's spine, then each stage given a section: profile → classify (memory-bound / compute-bound / latency-bound) → apply the fix that targets *that* limiter → re-measure → repeat until you hit a hardware roof.
- A Mermaid flowchart of the decision, with quoted edge labels:
  ```mermaid
  flowchart TD
    P["Profile the kernel"] --> Q{"Which is near peak?"}
    Q -->|"DRAM throughput"| M["Memory-bound: coalesce, vectorize, tile, fuse"]
    Q -->|"SM throughput"| C["Compute-bound: better instructions, tensor cores, math mode"]
    Q -->|"neither"| L["Latency-bound: raise occupancy or ILP, cut dependencies"]
    M --> R["Re-measure"]
    C --> R
    L --> R
    R --> Q
  ```
- A table mapping limiter → the two or three fixes that actually target it, each linking the page that covers it.
- `:::warning[...]` — the two most common wasted efforts are tuning occupancy on a memory-bound kernel and micro-optimizing instructions on a latency-bound one.
- `:::tip[...]` — establish a hardware roof first (effective bandwidth for a streaming kernel, cuBLAS time for a GEMM). If you are within 20% of it, stop.

See also: `occupancy-tuning.md`, `../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md`, `../09-tooling-profiling-and-debugging/nsight-compute.md`, `../09-tooling-profiling-and-debugging/metrics-that-matter.md`, `../readme.md`.

- [ ] **Step 2: Write `occupancy-tuning.md`**

Sections: `## What occupancy buys`, `## Computing it`, `## `__launch_bounds__``, `## The point where it stops helping`, `## High-ILP, low-occupancy kernels`.

Requirements:
- Restate the purpose in one sentence — occupancy is the supply of independent warps available to hide latency, nothing more — then show the three limiters worked through with `-Xptxas -v` output in a `text` fence.
- `__launch_bounds__(maxThreadsPerBlock, minBlocksPerMultiprocessor)` explained as a *contract with `ptxas`*: it caps registers so the requested block count fits. Show it applied and the register count changing in the `-Xptxas -v` output.
- The saturation argument, with numbers attributed to hardware: past roughly 50% occupancy most memory-bound kernels stop improving because the memory system, not the warp supply, is the limit — state the GPU generation the observation applies to.
- Volkov's counter-case given properly: a kernel with high instruction-level parallelism (several independent accumulators per thread) can beat a high-occupancy version at 25% occupancy, because each thread has more independent work in flight. Show a two-accumulator loop in `cpp`.
- `:::tip[...]` — Nsight Compute reports *achieved* occupancy alongside theoretical; a large gap usually means load imbalance or a tail effect, not a register problem.

See also: `the-optimization-workflow.md`, `instruction-level-optimization.md`, `../02-gpu-hardware-architecture/register-file-and-occupancy.md`, `../04-cuda-memory-model/registers-and-local-memory.md`, `../readme.md`.

- [ ] **Step 3: Write `memory-access-optimization.md`**

Sections: `## Coalescing first`, `## Vectorized loads`, `## Alignment`, `## Layout changes`, `## The read-only path`, `## Padding`.

Requirements:
- Ordered by payoff and say so: layout (AoS→SoA) > coalescing > vectorization > everything else.
- The `float4` load shown correctly with its alignment precondition, plus the reinterpret-cast form and the count arithmetic:
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
  Note that `n` must be divisible by 4 (or the tail handled separately) and the base pointer 16-byte aligned.
- Why vectorization helps mechanically: fewer, wider memory instructions means fewer requests in flight per byte moved, which relieves the LSU and the scoreboard — it does **not** move more bytes than a fully coalesced scalar access already does. State the direction of the win honestly.
- `const __restrict__` and the read-only path; note explicit `__ldg` is largely legacy on CC 5.0+.
- `:::warning[...]` — vectorized loads raise register pressure; check `-Xptxas -v` after applying them.

See also: `shared-memory-tiling.md`, `../04-cuda-memory-model/global-memory-and-coalescing.md`, `../04-cuda-memory-model/registers-and-local-memory.md`, `../readme.md`.

- [ ] **Step 4: Write `shared-memory-tiling.md`**

Sections: `## The reuse argument`, `## The naive kernel`, `## The tiled kernel`, `## Choosing a tile size`, `## Conflict-free layout`, `## What tiling does not fix`.

Requirements:
- Start from arithmetic intensity: naive SGEMM reads 2N bytes per output element and does 2N FLOPs, giving ~0.25 FLOP/byte in FP32; a `TILE × TILE` tiled version reuses each loaded element `TILE` times, raising intensity by a factor of `TILE`. Show that calculation — it is the whole justification.
- The tiled kernel in full. **Keep this exact name and tile size** — `13-applied-kernels-and-patterns/matrix-multiply.md` extends it:
  ```cpp showLineNumbers title="sgemm_tiled.cu"
  #define TILE 32

  __global__ void sgemmTiled(int N, const float* __restrict__ A,
                             const float* __restrict__ B, float* __restrict__ C) {
      __shared__ float As[TILE][TILE + 1];   // +1 removes the bank conflict
      __shared__ float Bs[TILE][TILE + 1];

      const int row = blockIdx.y * TILE + threadIdx.y;
      const int col = blockIdx.x * TILE + threadIdx.x;
      float acc = 0.0f;

      for (int t = 0; t < N / TILE; ++t) {
          As[threadIdx.y][threadIdx.x] = A[row * N + t * TILE + threadIdx.x];
          Bs[threadIdx.y][threadIdx.x] = B[(t * TILE + threadIdx.y) * N + col];
          __syncthreads();

          for (int k = 0; k < TILE; ++k)
              acc += As[threadIdx.y][k] * Bs[k][threadIdx.x];
          __syncthreads();
      }
      C[row * N + col] = acc;
  }
  ```
  State the simplifying assumption explicitly (`N` divisible by `TILE`) and that folder 13 handles the general case.
- Tile-size selection as a tradeoff table: larger tiles raise reuse but consume shared memory and cut blocks per SM.
- `:::note[...]` explaining the `TILE + 1` padding, linking [Shared Memory Bank Conflicts](../04-cuda-memory-model/bank-conflicts.md).
- `## What tiling does not fix`: it does not help a kernel with no reuse (SAXPY), and the two `__syncthreads()` per tile leave the memory system idle during compute — the next step is [Software Pipelining](./software-pipelining.md).

See also: `memory-access-optimization.md`, `software-pipelining.md`, `../04-cuda-memory-model/bank-conflicts.md`, `../13-applied-kernels-and-patterns/matrix-multiply.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/07-kernel-optimization
git commit -m "docs: kernel optimization, part 1"
```
Expected: build exits 0.

---

### Task 4: `07-kernel-optimization`, pages 5–8

**Files:**
- Modify: `instruction-level-optimization.md`, `reducing-divergence.md`, `kernel-fusion-and-launch-overhead.md`, `programming-tensor-cores.md`

**Interfaces:**
- Consumes: Task 3's `sgemmTiled`; `02-gpu-hardware-architecture/tensor-cores.md` (precision table).
- Produces: the `wmma` fragment example that `13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md` builds a full kernel from.

- [ ] **Step 1: Write `instruction-level-optimization.md`**

Sections: `## ILP and independent work`, `## Loop unrolling`, `## Intrinsics versus precise math`, `## `--use_fast_math``, `## Integer division and modulo`, `## FMA and contraction`.

Requirements:
- ILP shown as code: one accumulator versus four independent accumulators in the inner loop, and why the second hides FMA latency without needing more warps.
- `#pragma unroll` and `#pragma unroll N`, with the tradeoff stated (register pressure, I-cache) and the note that `nvcc` unrolls constant-trip-count loops on its own.
- An intrinsics table: `__fdividef`, `__sinf`, `__expf`, `__logf`, `rsqrtf` — each with its speed/accuracy character in ULP terms where known, and the recommendation to use them selectively rather than globally.
- `--use_fast_math` decomposed into what it actually enables (`--ffast-math`-style contraction, flush-to-zero denormals, fast intrinsic substitution, `--prec-div=false`, `--prec-sqrt=false`) and `:::warning[...]` that it changes results and must never be enabled silently in numerical code.
- Integer division: 32-bit integer division and modulo are multi-instruction sequences on the GPU; replace by power-of-two masks/shifts, or hoist a reciprocal, when the divisor is loop-invariant. Show the `& (n - 1)` substitution and state its precondition.
- `:::tip[...]` — verify any of this in the SASS, not the source; see [PTX and Inline Assembly](./ptx-and-inline-assembly.md).

See also: `occupancy-tuning.md`, `ptx-and-inline-assembly.md`, `../09-tooling-profiling-and-debugging/nsight-compute.md`, `../readme.md`.

- [ ] **Step 2: Write `reducing-divergence.md`**

Sections: `## Only intra-warp divergence costs`, `## Restructuring branches`, `## Predication`, `## Sorting and binning work`, `## Warp-uniform conditions`.

Requirements:
- Re-state the rule from [Warp Execution and Divergence](../05-execution-and-synchronization/warp-execution-and-divergence.md) in one sentence, then move straight to fixes — this page is the applied counterpart.
- Restructuring shown concretely: change `if (i % 2)` (divergent) to a mapping where the branch depends on `i / 32` (warp-uniform). Show both.
- Predication explained mechanically: short branches compile to predicated instructions with no branch at all, so a two-instruction `if` costs nothing; the compiler does this automatically below a threshold. Show the `text` SASS shape (`@!P0 FADD ...`).
- Binning: for a kernel with several work types, a preliminary pass that sorts indices by type turns a fully divergent kernel into a uniform one. Give the pattern in prose plus a short `cpp` sketch using a compacted index array.
- `:::warning[...]` that branch-free arithmetic tricks often cost more than the branch they remove, because both sides get executed unconditionally. Measure.

See also: `../05-execution-and-synchronization/warp-execution-and-divergence.md`, `instruction-level-optimization.md`, `../13-applied-kernels-and-patterns/sparse-matrix-vector.md`, `../readme.md`.

- [ ] **Step 3: Write `kernel-fusion-and-launch-overhead.md`**

Sections: `## The cost of a launch`, `## Fusing elementwise chains`, `## When fusion hurts`, `## Persistent kernels`, `## The alternatives`.

Requirements:
- The bandwidth argument made numerically: three separate elementwise kernels over one array read and write it three times; fused, once. For a bandwidth-bound chain that is close to a 3× reduction in traffic. Show the before/after kernels.
- When fusion hurts: the fused kernel's register footprint is the union of the parts, which can cut occupancy or spill; and fusing a memory-bound kernel with a compute-bound one can leave both under-served.
- Persistent kernels described with their tradeoff: one grid sized to the device, looping over a work queue, avoiding launch cost and keeping state in registers — at the price of no automatic load balancing and a hard occupancy cap.
- `:::tip[...]` — before hand-fusing, check whether the framework already does it: `torch.compile`/Inductor and Triton generate fused elementwise kernels automatically. Link [Triton](../08-libraries-and-ecosystem/triton.md) and [Compiler Stacks](../12-npu-and-inference-accelerators/compiler-stacks.md).
- Cross-link [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) as the answer when the kernels cannot be fused but the launches are the problem.

See also: `../06-cuda-runtime-and-apis/cuda-graphs.md`, `../08-libraries-and-ecosystem/triton.md`, `../13-applied-kernels-and-patterns/softmax-and-layernorm.md`, `../readme.md`.

- [ ] **Step 4: Write `programming-tensor-cores.md`**

Sections: `## What you are programming`, `## The `wmma` API`, `## Fragment layouts`, `## Precision and accumulators`, `## `mma` PTX intrinsics`, `## Why CUTLASS usually wins`.

Requirements:
- `:::note[...]` on hardware requirements, linking [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md) for the per-generation precision table rather than repeating it.
- The `wmma` fragment example, which folder 13 extends — keep these names:
  ```cpp showLineNumbers
  #include <mma.h>
  using namespace nvcuda;

  // One 16x16x16 FP16 tile product, accumulated in FP32.
  __global__ void wmmaTile(const half* A, const half* B, float* C, int N) {
      wmma::fragment<wmma::matrix_a, 16, 16, 16, half, wmma::row_major> aFrag;
      wmma::fragment<wmma::matrix_b, 16, 16, 16, half, wmma::col_major> bFrag;
      wmma::fragment<wmma::accumulator, 16, 16, 16, float> cFrag;

      wmma::fill_fragment(cFrag, 0.0f);
      wmma::load_matrix_sync(aFrag, A, N);
      wmma::load_matrix_sync(bFrag, B, N);
      wmma::mma_sync(cFrag, aFrag, bFrag, cFrag);
      wmma::store_matrix_sync(C, cFrag, N, wmma::mem_row_major);
  }
  ```
- The two facts that trip people up, stated plainly: a fragment is *warp-owned* — all 32 threads cooperate on one tile and the per-thread element mapping is deliberately unspecified — and every `wmma` call is warp-collective, so it must not appear in divergent code.
- Precision: FP16/BF16 inputs with FP32 accumulate is the default; TF32 gives FP32-like range with reduced mantissa and needs no source change beyond the math mode; FP8 (Ada/Hopper) and FP4/FP6 (Blackwell) need scaling factors.
- `mma` PTX intrinsics and `wgmma` (CC 9.0+) mentioned as the layer below `wmma`, with the honest framing: they expose larger shapes and asynchrony that `wmma` cannot reach, which is why library kernels use them.
- `:::tip[...]` — a hand-written `wmma` GEMM typically reaches a fraction of cuBLAS. Write one to understand the machine; ship cuBLAS or CUTLASS. Link [CUTLASS](../08-libraries-and-ecosystem/cutlass.md).

See also: `../02-gpu-hardware-architecture/tensor-cores.md`, `software-pipelining.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/07-kernel-optimization
git commit -m "docs: kernel optimization, part 2"
```
Expected: build exits 0.

---

### Task 5: `07-kernel-optimization`, pages 9–11

**Files:**
- Modify: `software-pipelining.md`, `ptx-and-inline-assembly.md`, `common-antipatterns.md`

**Interfaces:**
- Consumes: `04-cuda-memory-model/asynchronous-data-movement.md` (the `cuda::pipeline` skeleton), Task 3's `sgemmTiled`.
- Produces: nothing later plans depend on by name.

- [ ] **Step 1: Write `software-pipelining.md`**

Sections: `## The bubble in the tiled loop`, `## Double buffering with shared memory`, `## `memcpy_async` and `cuda::pipeline``, `## Multi-stage pipelines`, `## TMA-based pipelines`, `## When it pays`.

Requirements:
- Open by drawing the bubble explicitly against `sgemmTiled` from [Shared Memory Tiling](./shared-memory-tiling.md): load, barrier, compute, barrier — the memory system idles during compute and the ALUs idle during load.
- A Mermaid diagram of the two-stage overlap with quoted labels.
- The classic double-buffer with two shared tiles and manual index toggling, shown in `cpp` as a modification of `sgemmTiled` (elide the inner math with `// ...`).
- Then the modern form using `cuda::pipeline` — reference the skeleton in [Asynchronous Data Movement](../04-cuda-memory-model/asynchronous-data-movement.md) rather than repeating it in full, and show only the delta: how the tile loads become `cuda::memcpy_async` and where `producer_commit` / `consumer_wait` sit.
- Multi-stage: why three or four stages beat two when DRAM latency exceeds one tile's compute time, and the shared-memory cost that caps the stage count.
- TMA-based pipelines (`:::note[Requires CC 9.0+]`): one thread issues a bulk tensor copy, the rest wait on an `mbarrier`; this is the shape CUTLASS 3.x uses on Hopper.
- `:::tip[...]` — pipelining pays only when the kernel is already tiled and latency-bound; on a memory-bandwidth-saturated kernel it changes nothing.

See also: `shared-memory-tiling.md`, `../04-cuda-memory-model/asynchronous-data-movement.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../readme.md`.

- [ ] **Step 2: Write `ptx-and-inline-assembly.md`**

Sections: `## PTX is not the machine code`, `## Reading SASS`, `## Inline PTX`, `## Constraints and clobbers`, `## `cuda::ptx` helpers`, `## When this is justified`.

Requirements:
- The layering restated in one sentence (PTX is a virtual ISA, `ptxas` compiles it to SASS, and `ptxas` optimizes aggressively — so PTX is *not* what runs), linking [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md).
- The inspection commands and a short annotated SASS sample in a ` ```text ` fence, pointing out `LDG.E.128` (a vectorized global load), `LDS` (shared load), `HFMA2`/`FFMA`, and `BAR.SYNC`.
- Inline PTX with correct constraint letters, complete:
  ```cpp showLineNumbers
  __device__ float fmaRn(float a, float b, float c) {
      float d;
      asm volatile("fma.rn.f32 %0, %1, %2, %3;"
                   : "=f"(d)
                   : "f"(a), "f"(b), "f"(c));
      return d;
  }
  ```
  Give the constraint table: `h` (16-bit), `r` (32-bit int), `l` (64-bit int), `f` (32-bit float), `d` (64-bit float); `=` for write-only, `+` for read-write; `volatile` to stop the compiler moving or eliding it; and the `"memory"` clobber for anything with side effects.
- `cuda::ptx` (in libcu++) presented as the preferred modern route: typed, documented wrappers over PTX instructions such as `cp.async.bulk` and `mbarrier` operations, with no raw `asm` in your code.
- `:::warning[...]` — inline PTX blocks compiler optimization across it and pins you to instruction availability per architecture. It is justified for instructions with no intrinsic (specific `mbarrier`, `redux.sync`, cache-hint variants), and almost never for arithmetic.

See also: `../03-cuda-programming-model/the-compilation-model.md`, `instruction-level-optimization.md`, `../09-tooling-profiling-and-debugging/nsight-compute.md`, `../readme.md`.

- [ ] **Step 3: Write `common-antipatterns.md`**

Sections: one `##` per antipattern, each stating the symptom, the mechanism, and the fix.

Requirements — cover exactly these, in this order:
1. `## Optimizing before profiling` — the fix is [The Optimization Workflow](./the-optimization-workflow.md).
2. `## Synchronizing in the hot loop` — `cudaDeviceSynchronize()` per iteration; fix with events or a single sync at the end.
3. `## Allocating inside the loop` — `cudaMalloc`/`cudaFree` per iteration; fix with `cudaMallocAsync` and pools, see [Memory Allocation APIs](../06-cuda-runtime-and-apis/memory-allocation-apis.md).
4. `## Host–device ping-pong` — copying back to make a scalar decision every step; fix by keeping the decision on the device.
5. `## Pageable memory in an async pipeline` — silently makes `cudaMemcpyAsync` synchronous; fix with pinned memory.
6. `## `printf` in kernels` — serializes through a device buffer and can change the timing being measured; fine for debugging, never in a benchmark.
7. `## Benchmarking without warm-up` — first launch pays JIT, context creation, and low clocks.
8. `## Benchmarking code the compiler deleted` — an unused result gets optimized away; fix by writing to a volatile sink or a device array.
9. `## Chasing occupancy on a memory-bound kernel` — see [Occupancy Tuning](./occupancy-tuning.md).
10. `## Assuming warp-synchronous execution` — broken since CC 7.0; see [Independent Thread Scheduling](../05-execution-and-synchronization/independent-thread-scheduling.md).

Each gets a two-to-four-line `cpp` "wrong" snippet where a snippet makes the point, and one sentence of fix. Keep the page terse — it is a checklist, not an essay.

See also: `the-optimization-workflow.md`, `../09-tooling-profiling-and-debugging/benchmarking-methodology.md`, `../06-cuda-runtime-and-apis/error-handling.md`, `../readme.md`.

- [ ] **Step 4: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/07-kernel-optimization
git commit -m "docs: kernel optimization, part 3"
```
Expected: build exits 0.

---

### Task 6: Figures for folder 07

**Files:**
- Create: `static/img/gpu/07-kernel-optimization/*.png`
- Modify: `static/img/gpu/SOURCES.md`
- Modify: `docs/gpu-computing/07-kernel-optimization/shared-memory-tiling.md`

- [ ] **Step 1: Download the figure**

```bash
mkdir -p static/img/gpu/07-kernel-optimization
curl -fsSL -o static/img/gpu/07-kernel-optimization/matrix-multiplication-with-shared-memory.png \
  https://docs.nvidia.com/cuda/cuda-c-programming-guide/_images/matrix-multiplication-with-shared-memory.png
```

- [ ] **Step 2: Verify the download**

Run: `file static/img/gpu/07-kernel-optimization/matrix-multiplication-with-shared-memory.png`
Expected: `PNG image data`.

**If the download 404s or is not a PNG:** delete the file, skip Steps 3–4, keep the page's Mermaid diagram, and note the skip in the commit message. Do not substitute an image from another source without checking its terms.

- [ ] **Step 3: Add the `SOURCES.md` row**

Append to the table in `static/img/gpu/SOURCES.md`, replacing `<today>` with the actual ISO date:

```md
| `07-kernel-optimization/matrix-multiplication-with-shared-memory.png` | https://docs.nvidia.com/cuda/cuda-c-programming-guide/ | NVIDIA | <today> | Figure from the CUDA C++ Programming Guide; NVIDIA documentation terms. |
```

- [ ] **Step 4: Reference it from the page**

In `shared-memory-tiling.md`, at the start of `## The tiled kernel`:

```md
![Each block loads a tile of A and a tile of B into shared memory and reuses them across the tile's inner product](/img/gpu/07-kernel-optimization/matrix-multiplication-with-shared-memory.png)
*Source: [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)*
```

- [ ] **Step 5: Verify and commit**

```bash
npm run build && npm run format && npm run lint
git add static/img/gpu docs/gpu-computing/07-kernel-optimization
git commit -m "docs: add kernel optimization figure"
```
Expected: build exits 0.

---

## Plan 3 completion criteria

- 20 pages written; `npm run build` and `npm run lint` both exit 0.
- `grep -rn "define CUDA_CHECK" docs/gpu-computing/` returns exactly one hit, in `06-cuda-runtime-and-apis/error-handling.md`.
- `sgemmTiled` with `TILE = 32` exists in `07-kernel-optimization/shared-memory-tiling.md` — plan 6 extends it by name.
- Every performance figure in folder 07 names the GPU generation it applies to.
- Dynamic parallelism is documented with CDP2 semantics, with no device-side `cudaDeviceSynchronize()`.
- `static/img/gpu/SOURCES.md` has a row for every file under `static/img/gpu/`.
