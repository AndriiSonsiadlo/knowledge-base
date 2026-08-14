# GPU & Accelerators — Plan 2: CUDA Programming, Memory, and Execution

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the 28 pages of `03-cuda-programming-model/`, `04-cuda-memory-model/`, and `05-execution-and-synchronization/` — the core of the CUDA material.

**Architecture:** Every file already exists as a stub with correct frontmatter, created by plan 1 task 1. This plan only fills in bodies, so `npm run build` (with `onBrokenLinks: "throw"`) passes after every task and no link ever points at a missing page.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism `cpp`/`bash`/`text` fences, Biome, Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Prerequisite:** Plan 1 (`2026-08-13-gpu-computing-01-wiring-and-foundations.md`) must be complete. Verify with `ls docs/gpu-computing/03-cuda-programming-model/` — nine `.md` files must already be present.

**Plan series:** plan 2 of 6.

---

## Global Constraints

These apply to **every** page this plan writes and are not restated per task.

### Frontmatter

Already written by plan 1. **Do not change `id`, `title`, `sidebar_label`, `sidebar_position`, or `tags`** — other plans link to these files by path and the sidebar order is fixed. Only replace the body below the frontmatter.

### Page structure

1. `# H1` matching `title` exactly (already in the stub).
2. 1–2 paragraphs of prose framing **what problem this solves**, before any API detail. No page opens with a code block, a bullet list, or a definition list.
3. `##` sections per subtopic. `###` sparingly.
4. Ends with `## See also` — 3–5 bullets, **plain relative Markdown links**:
   `- [Link text](./relative-path.md) — one-line reason to go there.`
   Order: siblings first, then cross-folder, then `../readme.md` last.

**Do not use `<Icon icon="lucide:..." />`** — this section uses plain link bullets (the `docs/machine-learning/` convention). The icon set is a hand-curated allowlist in `scripts/gen-icons.mjs` and unlisted names render empty.

### Admonitions

Only these four:

| Admonition | Use for |
|---|---|
| `:::info[...]` | Framing the problem a feature solves |
| `:::note[...]` | Side facts, version / compute-capability caveats |
| `:::tip[...]` | Practical guidance, rules of thumb |
| `:::warning[...]` | Pitfalls, correctness traps, performance cliffs |

Every compute-capability requirement gets a `:::note`, pointing at [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).

### Code fences

- **CUDA C++ uses ` ```cpp `.** No Prism grammar for CUDA exists or can be added.
- **PTX and SASS use ` ```text `.**
- Also permitted here: `bash`, `cmake`, `json`. **`python` only in `03-cuda-programming-model/installing-the-cuda-toolkit.md`** — nowhere else in this plan.
- `showLineNumbers` on any fence longer than ~5 lines; `title="filename.cu"` when the snippet is a standalone file.
- Kernels are complete and compilable where practical; elided bodies use `// ...`, never pseudocode.
- **`CUDA_CHECK` is defined once**, in `06-cuda-runtime-and-apis/error-handling.md` (written in plan 3). Pages in this plan may *use* `CUDA_CHECK(...)` freely but must never define it; the first page to use it adds a one-line note pointing at [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md).

### MDX hazards

Outside code fences and inline backticks:

- `__global__`, `__device__`, `__shared__`, `__syncthreads`, `__constant__`, `__restrict__` — bare double underscores become Markdown emphasis. **Always backtick them in prose.**
- `<<<grid, block>>>`, `<T>`, `cuda::atomic<int>` — angle brackets are parsed as JSX. **Always backtick them in prose.**
- Bare `{` or `}` in prose is a JSX expression. Backtick it.

### Diagrams

Mermaid (` ```mermaid `) for structural content. **Quote every edge label:** `A -->|"label (with parens)"| B`. An unescaped label broke a build before (commit `958a2e6`).

### Content currency

CUDA 13.x semantics. Specifically:

- Thread block clusters (CC 9.0+) are a first-class hierarchy level, launched with `__cluster_dims__` or `cudaLaunchKernelEx` + `cudaLaunchAttributeClusterDimension`.
- Distributed shared memory via `cluster.map_shared_rank()` and `cluster.sync()`.
- Tensor Memory Accelerator (CC 9.0+) for multi-dimensional global→shared transfers.
- `cuda::memcpy_async` / `cg::memcpy_async`, `cuda::barrier`, `cuda::pipeline` (asynchronous from CC 8.0+).
- Cooperative Groups as the modern replacement for raw `__syncthreads()` idioms.
- **`__shfl_sync`-family intrinsics only.** The non-`_sync` variants are removed, not deprecated — show them only as a clearly labelled historical note.
- Never document anything as CUDA-11-or-earlier-only without saying so.

### Verification gate — every task

1. `npm run build` exits 0.
2. `npm run format` then `npm run lint` — both exit 0.
3. Commit. One-line message, `<type>: <what>`. **Never** add a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

---

## File Structure

```
docs/gpu-computing/
├── 03-cuda-programming-model/     9 pages   Task 1 (1-5), Task 2 (6-9)
├── 04-cuda-memory-model/         11 pages   Task 3 (1-6), Task 4 (7-11)
└── 05-execution-and-synchronization/ 8 pages Task 5 (1-4), Task 6 (5-8)

static/img/gpu/
├── 03-cuda-programming-model/               Task 7
└── SOURCES.md                               Task 7 (append rows)
```

---

### Task 1: `03-cuda-programming-model`, pages 1–5

**Files:**
- Modify: `installing-the-cuda-toolkit.md`, `your-first-kernel.md`, `threads-blocks-and-grids.md`, `thread-indexing.md`, `launch-configuration.md`

**Interfaces:**
- Consumes: `02-gpu-hardware-architecture/register-file-and-occupancy.md` (occupancy limiters), `01-parallel-computing-foundations/the-host-device-model.md` (offload cycle).
- Produces: the SAXPY kernel used as the running example in `13-applied-kernels-and-patterns/vector-add-and-saxpy.md`; the grid-stride loop idiom every later kernel example uses.

- [ ] **Step 1: Write `installing-the-cuda-toolkit.md`**

Sections: `## Driver, toolkit, and runtime`, `## Version compatibility`, `## Installing`, `## WSL2`, `## Containers`, `## Verifying the install`.

Requirements:
- The three-layer picture stated first, because it is the thing people get wrong: the **driver** (kernel module, backward compatible with older toolkits), the **toolkit** (`nvcc`, headers, libraries), the **runtime** (`libcudart`, linked into your binary). A newer driver runs older toolkits; the reverse is not generally true.
- A `bash` block for the verification trio:
  ```bash
  nvidia-smi                 # driver version + CUDA version the driver supports
  nvcc --version             # toolkit version
  /usr/local/cuda/extras/demo_suite/deviceQuery   # if installed
  ```
- WSL2 section: the driver is installed on **Windows**, not inside the distro; installing a Linux driver in WSL breaks it. Point at `/usr/lib/wsl/lib`.
- Containers section: `nvidia-container-toolkit` and `docker run --gpus all`.
- The one Python block permitted in this folder — a five-line check that PyTorch sees the device:
  ```python
  import torch
  print(torch.cuda.is_available())
  print(torch.cuda.get_device_name(0))
  print(torch.version.cuda)          # toolkit PyTorch was built against
  ```
- `:::warning[...]` on mixing a distro-packaged driver with a `.run` installer.

See also: `your-first-kernel.md`, `the-compilation-model.md`, `../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md`, `../readme.md`.

- [ ] **Step 2: Write `your-first-kernel.md`**

Sections: `## The program`, `## Allocating on the device`, `## Copying in`, `## Launching`, `## Copying back and freeing`, `## Compiling and running`, `## What just happened`.

Requirements:
- One complete, compilable SAXPY file, shown once in full and then dissected section by section:
  ```cpp showLineNumbers title="saxpy.cu"
  #include <cstdio>

  __global__ void saxpy(int n, float a, const float* x, float* y) {
      int i = blockIdx.x * blockDim.x + threadIdx.x;
      if (i < n) y[i] = a * x[i] + y[i];
  }

  int main() {
      const int n = 1 << 20;
      const size_t bytes = n * sizeof(float);

      float* h_x = (float*)malloc(bytes);
      float* h_y = (float*)malloc(bytes);
      for (int i = 0; i < n; ++i) { h_x[i] = 1.0f; h_y[i] = 2.0f; }

      float *d_x, *d_y;
      cudaMalloc(&d_x, bytes);
      cudaMalloc(&d_y, bytes);
      cudaMemcpy(d_x, h_x, bytes, cudaMemcpyHostToDevice);
      cudaMemcpy(d_y, h_y, bytes, cudaMemcpyHostToDevice);

      const int threads = 256;
      const int blocks = (n + threads - 1) / threads;
      saxpy<<<blocks, threads>>>(n, 2.0f, d_x, d_y);

      cudaMemcpy(h_y, d_y, bytes, cudaMemcpyDeviceToHost);
      printf("y[0] = %f\n", h_y[0]);   // expect 4.0

      cudaFree(d_x); cudaFree(d_y);
      free(h_x); free(h_y);
      return 0;
  }
  ```
- The compile line: `nvcc -O2 -arch=sm_80 saxpy.cu -o saxpy`.
- `:::warning[...]` that this program checks no return codes — every later page uses `CUDA_CHECK`, defined in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md), and real code must too.
- `:::note[...]` that the ceiling-division `(n + threads - 1) / threads` plus the `if (i < n)` guard is a pair — dropping either is the most common first bug.
- The closing section names the three costs the reader just paid without noticing: two H2D copies, one launch, one D2H copy. Forward-link to [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md).

See also: `threads-blocks-and-grids.md`, `thread-indexing.md`, `../06-cuda-runtime-and-apis/error-handling.md`, `../13-applied-kernels-and-patterns/vector-add-and-saxpy.md`, `../readme.md`.

- [ ] **Step 3: Write `threads-blocks-and-grids.md`**

Sections: `## The hierarchy`, `## `dim3` and multi-dimensional launches`, `## Why blocks must be independent`, `## How blocks map to SMs`, `## The limits`.

Requirements:
- Mermaid tree of grid → block → warp → thread, with cluster shown as an optional level marked CC 9.0+:
  ```mermaid
  flowchart TD
    G["Grid"] --> C["Cluster (CC 9.0+, optional)"]
    C --> B["Block"]
    G -->|"without clusters"| B
    B --> W["Warp (32 threads)"]
    W --> T["Thread"]
  ```
- State the independence rule precisely: blocks may run in any order, concurrently or serially, on any SM, and there is no portable way to synchronise across blocks in a plain launch — that is what makes the model scale across GPU sizes. Forward to [Grid-Wide Synchronization](../05-execution-and-synchronization/grid-wide-synchronization.md) for the exception.
- A limits table: max threads per block (1024), max block dimensions, max grid dimensions, warp size (32). Say these are queryable via `cudaDeviceProp`.
- A `cpp` snippet with a 2-D launch over an image, using `dim3`.

See also: `thread-indexing.md`, `thread-block-clusters.md`, `../02-gpu-hardware-architecture/warps-and-schedulers.md`, `../05-execution-and-synchronization/grid-wide-synchronization.md`, `../readme.md`.

- [ ] **Step 4: Write `thread-indexing.md`**

Sections: `## The 1-D formula`, `## 2-D and 3-D`, `## Bounds guards`, `## Grid-stride loops`, `## Row-major indexing and pitch`.

Requirements:
- Show the 1-D, 2-D, and 3-D global-index formulas as separate `cpp` snippets, each with its bounds guard.
- The grid-stride loop in full, with the reasoning for it — the kernel becomes independent of grid size, so you can size the grid for occupancy instead of for the data, and the same kernel handles any `n`:
  ```cpp showLineNumbers
  __global__ void saxpy_gs(int n, float a, const float* x, float* y) {
      for (int i = blockIdx.x * blockDim.x + threadIdx.x;
           i < n;
           i += blockDim.x * gridDim.x) {
          y[i] = a * x[i] + y[i];
      }
  }
  ```
- `:::tip[...]` — prefer grid-stride loops by default; they also make a kernel debuggable at `<<<1, 1>>>`.
- Row-major indexing `row * width + col` and why the *column* index must be the fastest-varying one for a warp, connecting to [Global Memory and Coalescing](../04-cuda-memory-model/global-memory-and-coalescing.md).

See also: `threads-blocks-and-grids.md`, `launch-configuration.md`, `../04-cuda-memory-model/global-memory-and-coalescing.md`, `../readme.md`.

- [ ] **Step 5: Write `launch-configuration.md`**

Sections: `## What you are actually choosing`, `## Block size`, `## Grid size`, `## The occupancy API`, `## When 256 is not the answer`.

Requirements:
- Block-size rules with reasons: a multiple of 32 (otherwise you waste lanes), at least 64 (to fill sub-partitions), rarely above 512 (register pressure and the tail effect).
- The occupancy API used correctly:
  ```cpp showLineNumbers
  int blockSize = 0, minGridSize = 0;
  CUDA_CHECK(cudaOccupancyMaxPotentialBlockSize(
      &minGridSize, &blockSize, saxpy_gs, 0, 0));
  int gridSize = (n + blockSize - 1) / blockSize;
  ```
- A section on sizing the grid for a grid-stride loop instead: `minGridSize` from the API, or `SM count × blocks per SM`, obtained via `cudaDeviceGetAttribute(&smCount, cudaDevAttrMultiProcessorCount, dev)`.
- `:::warning[...]` on the tail effect — a grid of 33 blocks on a 32-SM-wide machine costs nearly twice a grid of 32.
- `:::tip[...]` — measure. The occupancy API optimizes occupancy, which is a proxy, not the objective; forward to [Occupancy Tuning](../07-kernel-optimization/occupancy-tuning.md).

See also: `thread-indexing.md`, `../02-gpu-hardware-architecture/register-file-and-occupancy.md`, `../07-kernel-optimization/occupancy-tuning.md`, `../readme.md`.

- [ ] **Step 6: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/03-cuda-programming-model
git commit -m "docs: cuda programming model, part 1"
```
Expected: build exits 0.

---

### Task 2: `03-cuda-programming-model`, pages 6–9

**Files:**
- Modify: `thread-block-clusters.md`, `function-qualifiers.md`, `the-compilation-model.md`, `separate-compilation-and-linking.md`

**Interfaces:**
- Consumes: Task 1's hierarchy diagram and launch vocabulary.
- Produces: the cluster launch snippet reused by `04-cuda-memory-model/distributed-shared-memory.md`; the PTX/SASS reading workflow reused by `07-kernel-optimization/ptx-and-inline-assembly.md`.

- [ ] **Step 1: Write `thread-block-clusters.md`**

Sections: `## Why a level between grid and block`, `## Declaring a cluster`, `## Launching with `cudaLaunchKernelEx``, `## Guaranteed co-residency`, `## Cluster synchronization`, `## Sizing and portability`.

Requirements:
- Open with the problem: blocks are independent by design, which means no data sharing and no cheap synchronization between them — a cluster relaxes exactly that, for a small group of blocks guaranteed to be co-resident on one GPC.
- `:::note[Requires CC 9.0+]` at the top of the API material, linking [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).
- Both launch forms, complete:
  ```cpp showLineNumbers
  // Form 1: compile-time cluster dimensions
  __global__ void __cluster_dims__(2, 1, 1) kernel_a(float* out) {
      namespace cg = cooperative_groups;
      cg::cluster_group cluster = cg::this_cluster();
      cluster.sync();
      // ...
  }
  ```
  ```cpp showLineNumbers
  // Form 2: runtime cluster dimensions
  cudaLaunchConfig_t config = {};
  config.gridDim = dim3(numBlocks, 1, 1);
  config.blockDim = dim3(256, 1, 1);

  cudaLaunchAttribute attrs[1];
  attrs[0].id = cudaLaunchAttributeClusterDimension;
  attrs[0].val.clusterDim.x = 2;
  attrs[0].val.clusterDim.y = 1;
  attrs[0].val.clusterDim.z = 1;
  config.attrs = attrs;
  config.numAttrs = 1;

  CUDA_CHECK(cudaLaunchKernelEx(&config, kernel_b, d_out));
  ```
- State the portable maximum (8 blocks per cluster) and that larger sizes must be queried with `cudaOccupancyMaxPotentialClusterSize`.
- `:::warning[...]` that a cluster kernel launched on pre-Hopper hardware fails; guard with a `cudaDeviceProp::major` check or ship both paths.

See also: `threads-blocks-and-grids.md`, `../04-cuda-memory-model/distributed-shared-memory.md`, `../05-execution-and-synchronization/cooperative-groups.md`, `../02-gpu-hardware-architecture/compute-capability.md`, `../readme.md`.

- [ ] **Step 2: Write `function-qualifiers.md`**

Sections: `## Function qualifiers`, `## Variable qualifiers`, `## Inlining and `__restrict__``, `## Combining `__host__ __device__``, `## What the C++ subset allows`.

Requirements:
- A table `| Qualifier | Applies to | Callable from | Runs on |` for `__global__`, `__device__`, `__host__`, `__host__ __device__`.
- A table for `__shared__`, `__constant__`, `__managed__`, `__device__` (on variables), covering scope, lifetime, and where it lives.
- `__restrict__` explained with the actual payoff: it lets the compiler prove non-aliasing and keep loads in registers or use the read-only path. Show a before/after signature.
- `:::note[...]` on the C++ subset: no exceptions, no RTTI, no virtual calls across the host/device boundary, `constexpr` largely fine — cross-link `../../programming/cpp/` for the language itself.
- `:::warning[...]` that `__forceinline__` and `__noinline__` are hints that interact with register pressure; do not sprinkle them.

See also: `the-compilation-model.md`, `../04-cuda-memory-model/constant-and-texture-memory.md`, `../../programming/cpp/readme.md`, `../readme.md`.

- [ ] **Step 3: Write `the-compilation-model.md`**

Sections: `## What `nvcc` actually does`, `## PTX, the virtual ISA`, `## SASS, the machine code`, `## Fatbinaries`, `## JIT compilation`, `## Reading the output`.

Requirements:
- A Mermaid flow of the compile path with quoted labels:
  ```mermaid
  flowchart TD
    SRC[".cu source"] -->|"nvcc splits"| HOST["Host C++"]
    SRC -->|"nvcc splits"| DEV["Device code"]
    HOST -->|"host compiler"| OBJH["Host object"]
    DEV -->|"cicc"| PTX["PTX (virtual ISA)"]
    PTX -->|"ptxas"| SASS["SASS (per-architecture)"]
    PTX --> FAT["Fatbinary"]
    SASS --> FAT
    FAT -->|"embedded"| OBJH
    PTX -->|"driver JIT at load"| SASSJIT["SASS for a newer GPU"]
  ```
- Show inspecting a binary, with a `text` fence for the sample output:
  ```bash
  nvcc -O2 -arch=sm_90 -ptx kernel.cu -o kernel.ptx
  cuobjdump -sass ./kernel        # SASS
  nvdisasm -c kernel.cubin        # control-flow annotated
  ```
- `-arch` vs `-code` explained by mapping them onto the diagram: `-arch=compute_90` stops at PTX, `-code=sm_90` continues to SASS. Point at [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md) for the shipping recipe.
- `:::tip[...]` — `-Xptxas -v` prints register and shared-memory usage per kernel; it is the cheapest optimization feedback that exists. Show a sample `text` output line.

See also: `separate-compilation-and-linking.md`, `../02-gpu-hardware-architecture/compute-capability.md`, `../07-kernel-optimization/ptx-and-inline-assembly.md`, `../readme.md`.

- [ ] **Step 4: Write `separate-compilation-and-linking.md`**

Sections: `## Whole-program compilation is the default`, `## Relocatable device code`, `## Device linking`, `## What it costs`, `## When you cannot avoid it`.

Requirements:
- Show the failure first: a `__device__` function defined in one `.cu` and called from another does not link without `-rdc=true`. Give the error text in a `text` fence.
- The full build:
  ```bash
  nvcc -rdc=true -arch=sm_80 -c a.cu -o a.o
  nvcc -rdc=true -arch=sm_80 -c b.cu -o b.o
  nvcc -arch=sm_80 a.o b.o -o app          # nvcc performs the device link
  ```
- The cost, stated concretely: cross-TU calls cannot be inlined, so register allocation is conservative and ABI calls appear in the SASS; expect a measurable slowdown on small hot kernels.
- `:::note[...]` on the cases that force it: device-side `virtual` dispatch, dynamic parallelism, `__device__` globals shared across TUs, and linking against device libraries such as cuFFT device callbacks.
- `:::tip[...]` — in CMake this is `set_target_properties(tgt PROPERTIES CUDA_SEPARABLE_COMPILATION ON)`; see [Building CUDA with CMake](../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md).

See also: `the-compilation-model.md`, `../06-cuda-runtime-and-apis/dynamic-parallelism.md`, `../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/03-cuda-programming-model
git commit -m "docs: cuda programming model, part 2"
```
Expected: build exits 0.

---

### Task 3: `04-cuda-memory-model`, pages 1–6

**Files:**
- Modify: `memory-spaces-overview.md`, `global-memory-and-coalescing.md`, `shared-memory.md`, `bank-conflicts.md`, `registers-and-local-memory.md`, `constant-and-texture-memory.md`

**Interfaces:**
- Consumes: `02-gpu-hardware-architecture/cache-hierarchy.md` (sector granularity), Task 1's indexing formulas.
- Produces: the tiled-transpose and padded-array snippets reused by `13-applied-kernels-and-patterns/matrix-transpose.md` and `07-kernel-optimization/shared-memory-tiling.md`.

- [ ] **Step 1: Write `memory-spaces-overview.md`**

Sections: `## The six spaces`, `## Scope and lifetime`, `## Latency and bandwidth`, `## Choosing a space`.

Requirements:
- One table doing the heavy lifting: `| Space | Declared as | Scope | Lifetime | Cached | Typical latency | Typical size |` with rows for register, local, shared, global, constant, texture/read-only. Name the architecture the latency numbers describe.
- Mermaid hierarchy diagram: thread → registers/local; block → shared; grid → global/constant/texture.
- `:::warning[...]` that "local" memory is not local to anything fast — it is device memory with per-thread addressing, and a register spill lands there. Forward to [Registers and Local Memory](./registers-and-local-memory.md).
- Closing decision list: per-thread scratch → registers; block-wide reuse → shared; read-only broadcast to all threads → constant; everything else → global.

See also: `global-memory-and-coalescing.md`, `shared-memory.md`, `../02-gpu-hardware-architecture/cache-hierarchy.md`, `../00-overview/glossary.md`, `../readme.md`.

- [ ] **Step 2: Write `global-memory-and-coalescing.md`**

Sections: `## Transactions and sectors`, `## What coalescing means`, `## Strided access`, `## Scattered access`, `## Array of structs versus struct of arrays`, `## Vectorized loads`.

Requirements:
- The mechanism stated exactly once and precisely: a warp's 32 loads are serviced in 32-byte sectors; consecutive, aligned, 4-byte accesses by 32 threads touch four sectors (128 bytes) — the minimum. A stride of 32 floats touches 32 sectors for the same 128 useful bytes, an 8× waste. Show the arithmetic.
- Three `cpp` kernels: coalesced, strided (`data[i * stride]`), and AoS-vs-SoA. For AoS/SoA give both struct definitions and both kernels.
- A table `| Pattern | Sectors per warp | Useful bytes | Efficiency |`.
- `float4` vectorized load snippet, with the alignment requirement stated (the pointer must be 16-byte aligned; `cudaMalloc` guarantees 256-byte alignment, but an offset into the array may not preserve it).
- `:::tip[...]` — the Nsight Compute metric to check is `l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum` per request; see [Metrics That Matter](../09-tooling-profiling-and-debugging/metrics-that-matter.md).

See also: `memory-spaces-overview.md`, `bank-conflicts.md`, `../07-kernel-optimization/memory-access-optimization.md`, `../13-applied-kernels-and-patterns/matrix-transpose.md`, `../readme.md`.

- [ ] **Step 3: Write `shared-memory.md`**

Sections: `## Two roles: scratchpad and channel`, `## Static allocation`, `## Dynamic allocation`, `## The L1 carveout`, `## Opting into more than 48 KB`, `## The lifetime rule`.

Requirements:
- Both allocation forms in `cpp`: `__shared__ float tile[32][33];` and `extern __shared__ float buf[];` with the third launch parameter `kernel<<<g, b, bytes>>>()`.
- The >48 KB opt-in, complete, because it is easy to get wrong:
  ```cpp showLineNumbers
  CUDA_CHECK(cudaFuncSetAttribute(
      myKernel, cudaFuncAttributeMaxDynamicSharedMemorySize, 65536));
  myKernel<<<blocks, threads, 65536>>>(/* ... */);
  ```
- `cudaFuncSetCacheConfig` / `cudaFuncAttributePreferredSharedMemoryCarveout` and what the L1/shared split trades.
- `:::warning[...]` that shared memory is per-block and uninitialized, and that shared-memory size directly caps blocks per SM — a 48 KB block on a 164 KB SM means at most 3 resident blocks. Link [The Register File and Occupancy](../02-gpu-hardware-architecture/register-file-and-occupancy.md).
- The lifetime rule: writes are visible to the block only after `__syncthreads()`; forward to [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md).

See also: `bank-conflicts.md`, `distributed-shared-memory.md`, `../05-execution-and-synchronization/block-synchronization.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `../readme.md`.

- [ ] **Step 4: Write `bank-conflicts.md`**

Sections: `## 32 banks`, `## What counts as a conflict`, `## The broadcast exception`, `## The padding fix`, `## Swizzling`, `## Measuring conflicts`.

Requirements:
- The rule stated precisely: shared memory is 32 banks of 4-byte words; bank = `(address / 4) % 32`. Threads in a warp hitting distinct banks are serviced in one cycle; N threads hitting distinct addresses in the *same* bank serialize into N cycles. All threads reading the *same* address is a broadcast, not a conflict.
- The transpose example worked: a `__shared__ float tile[32][32]` accessed column-wise puts all 32 threads in the same bank — a 32-way conflict. `tile[32][33]` shifts each row by one word and removes it entirely. Show both declarations and explain the arithmetic.
- An XOR-swizzle alternative, with the reason to prefer it (no wasted shared memory, matters when shared memory is the occupancy limiter):
  ```cpp
  // column index swizzled instead of padded
  int col = threadIdx.x ^ threadIdx.y;
  ```
- `:::tip[...]` — the Nsight Compute metric is `l1tex__data_bank_conflicts_pipe_lsu_mem_shared`; a nonzero value on a tiled kernel almost always means a missing pad.

See also: `shared-memory.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `../13-applied-kernels-and-patterns/matrix-transpose.md`, `../readme.md`.

- [ ] **Step 5: Write `registers-and-local-memory.md`**

Sections: `## Registers are allocated per thread, statically`, `## What spills`, `## Detecting spills`, `## Controlling register usage`, `## When spilling is fine`.

Requirements:
- The allocation model: `ptxas` fixes register count per thread at compile time; it multiplies by threads per block to decide blocks per SM. There is no dynamic register allocation.
- What forces a spill: too many live values, and — importantly — any local array indexed with a non-constant index, which cannot live in registers at all. Show that case in `cpp`.
- Detection, with real output shape:
  ```bash
  nvcc -O2 -arch=sm_80 -Xptxas -v -c kernel.cu
  ```
  ```text
  ptxas info    : Used 72 registers, 96 bytes cumulative stack size, 380 bytes cmem[0]
  ```
  Say that a nonzero "stack size" or the `local_load`/`local_store` counters in Nsight Compute are the spill signal.
- `__launch_bounds__` and `-maxrregcount` compared, with the recommendation: prefer `__launch_bounds__` (per-kernel, travels with the code) over the translation-unit-wide flag.
  ```cpp
  __global__ void __launch_bounds__(256, 4) myKernel(/* ... */) { /* ... */ }
  ```
- `:::warning[...]` — capping registers to raise occupancy often trades a fast register access for an L1-or-worse local access; measure both.

See also: `memory-spaces-overview.md`, `../02-gpu-hardware-architecture/register-file-and-occupancy.md`, `../07-kernel-optimization/occupancy-tuning.md`, `../readme.md`.

- [ ] **Step 6: Write `constant-and-texture-memory.md`**

Sections: `## Constant memory`, `## The broadcast rule`, `## The read-only data cache`, `## Texture objects`, `## When textures still pay off`.

Requirements:
- `__constant__` declaration and `cudaMemcpyToSymbol` shown together, plus the 64 KB limit.
- The broadcast rule stated as the whole point: constant memory is fast when every thread in a warp reads the *same* address, and degrades linearly when they read different ones — the opposite of the coalescing rule for global memory.
- `__ldg` and a note that on CC 5.0+ the compiler routes `const __restrict__` loads through the read-only path automatically, so explicit `__ldg` is mostly a legacy idiom.
- Texture objects (`cudaTextureObject_t`, `cudaCreateTextureObject`) with a short `cpp` snippet, and the honest verdict: worth it for 2-D spatial locality, hardware interpolation, and free boundary clamping — not as a general fast path.
- `:::note[...]` that texture *references* are removed; only texture objects exist in current CUDA.

See also: `memory-spaces-overview.md`, `../03-cuda-programming-model/function-qualifiers.md`, `../13-applied-kernels-and-patterns/stencil-and-convolution.md`, `../readme.md`.

- [ ] **Step 7: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/04-cuda-memory-model
git commit -m "docs: cuda memory model, part 1"
```
Expected: build exits 0.

---

### Task 4: `04-cuda-memory-model`, pages 7–11

**Files:**
- Modify: `unified-memory.md`, `pinned-memory-and-transfers.md`, `distributed-shared-memory.md`, `asynchronous-data-movement.md`, `memory-consistency-and-fences.md`

**Interfaces:**
- Consumes: Task 3's memory-space table; Task 2's cluster launch snippet.
- Produces: the `cuda::pipeline` double-buffering skeleton reused by `07-kernel-optimization/software-pipelining.md`; the DSMEM histogram kernel reused by `13-applied-kernels-and-patterns/histogram.md`.

- [ ] **Step 1: Write `unified-memory.md`**

Sections: `## One pointer, two memories`, `## Page migration`, `## Prefetching`, `## Advising the driver`, `## Oversubscription`, `## The performance traps`.

Requirements:
- `cudaMallocManaged` shown replacing the `cudaMalloc` + two `cudaMemcpy` calls from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md), so the reader sees exactly what it removes.
- The migration mechanism: a page fault on either side triggers a migration at page granularity; a kernel that touches a fresh managed buffer for the first time pays a fault storm.
- `cudaMemPrefetchAsync` and `cudaMemAdvise` with their real enum values (`cudaMemAdviseSetReadMostly`, `cudaMemAdviseSetPreferredLocation`, `cudaMemAdviseSetAccessedBy`), each with one line on when it helps.
- `:::warning[...]` — the classic trap is a host loop touching managed memory between kernel launches, which ping-pongs pages every iteration. Show the pattern and the prefetch fix.
- `:::note[...]` that behaviour differs sharply between systems with hardware coherence (Grace-Hopper, and Pascal+ on Linux with HMM) and Windows/WDDM, where the whole allocation migrates.

See also: `pinned-memory-and-transfers.md`, `memory-spaces-overview.md`, `../06-cuda-runtime-and-apis/memory-allocation-apis.md`, `../readme.md`.

- [ ] **Step 2: Write `pinned-memory-and-transfers.md`**

Sections: `## Pageable versus pinned`, `## Allocating pinned memory`, `## Zero-copy and mapped memory`, `## Overlapping transfer with compute`, `## Measuring PCIe throughput`.

Requirements:
- Why pageable transfers are slower, mechanically: the driver stages through an internal pinned buffer, so a pageable `cudaMemcpy` is two copies, and it cannot be asynchronous.
- `cudaHostAlloc` / `cudaMallocHost` / `cudaHostRegister`, with the flags `cudaHostAllocPortable`, `cudaHostAllocMapped`, `cudaHostAllocWriteCombined` and one line each.
- The overlap pattern in full — this is the payoff of the whole page:
  ```cpp showLineNumbers
  const int nStreams = 4;
  cudaStream_t stream[nStreams];
  for (int i = 0; i < nStreams; ++i) CUDA_CHECK(cudaStreamCreate(&stream[i]));

  const int chunk = n / nStreams;
  for (int i = 0; i < nStreams; ++i) {
      const int off = i * chunk;
      CUDA_CHECK(cudaMemcpyAsync(d_x + off, h_x + off, chunk * sizeof(float),
                                 cudaMemcpyHostToDevice, stream[i]));
      saxpy<<<(chunk + 255) / 256, 256, 0, stream[i]>>>(chunk, 2.0f, d_x + off, d_y + off);
      CUDA_CHECK(cudaMemcpyAsync(h_y + off, d_y + off, chunk * sizeof(float),
                                 cudaMemcpyDeviceToHost, stream[i]));
  }
  for (int i = 0; i < nStreams; ++i) CUDA_CHECK(cudaStreamSynchronize(stream[i]));
  ```
  Note that `h_x`/`h_y` **must** be pinned for these copies to be genuinely asynchronous. Forward to [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md).
- `:::warning[...]` that pinned memory is a scarce OS resource; over-pinning degrades the whole system.
- A bandwidth measurement recipe with `cudaEvent` timing, deferring the details to [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md), and realistic expectations (~85–90% of theoretical PCIe on a good host).

See also: `unified-memory.md`, `../06-cuda-runtime-and-apis/streams-and-concurrency.md`, `../00-overview/when-not-to-use-a-gpu.md`, `../readme.md`.

- [ ] **Step 3: Write `distributed-shared-memory.md`**

Sections: `## Shared memory across a cluster`, `## Mapping another block's shared memory`, `## The cluster histogram`, `## When it beats global atomics`, `## Constraints`.

Requirements:
- `:::note[Requires CC 9.0+]` at the top, linking [Thread Block Clusters](../03-cuda-programming-model/thread-block-clusters.md) and [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).
- The canonical histogram kernel, complete:
  ```cpp showLineNumbers title="cluster_histogram.cu"
  #include <cooperative_groups.h>
  namespace cg = cooperative_groups;

  __global__ void __cluster_dims__(2, 1, 1)
  clusterHist(int* bins, const int* input, int n, int binsPerBlock) {
      extern __shared__ int smem[];
      cg::cluster_group cluster = cg::this_cluster();
      const unsigned rank = cluster.block_rank();
      const unsigned nBlocks = cluster.num_blocks();

      for (int i = threadIdx.x; i < binsPerBlock; i += blockDim.x) smem[i] = 0;
      cluster.sync();

      for (int i = blockIdx.x * blockDim.x + threadIdx.x;
           i < n; i += blockDim.x * gridDim.x) {
          const int bin = input[i];
          const int owner = bin / binsPerBlock;         // which block owns this bin
          int* dst = cluster.map_shared_rank(smem, owner);
          atomicAdd(&dst[bin % binsPerBlock], 1);       // DSMEM atomic
      }
      cluster.sync();

      for (int i = threadIdx.x; i < binsPerBlock; i += blockDim.x)
          atomicAdd(&bins[rank * binsPerBlock + i], smem[i]);
      (void)nBlocks;
  }
  ```
- The win explained: a histogram too large for one block's shared memory previously fell back to global atomics; a cluster lets `nBlocks × 48 KB` of privatized bins stay on-chip.
- `:::warning[...]` — `cluster.sync()` is required before *and* after the DSMEM phase; a missing barrier is a silent data race, not a crash. `compute-sanitizer --tool racecheck` finds it.
- Constraints: mapped pointers are valid only inside the cluster's lifetime, and only shared memory is mappable.

See also: `shared-memory.md`, `../03-cuda-programming-model/thread-block-clusters.md`, `../13-applied-kernels-and-patterns/histogram.md`, `../05-execution-and-synchronization/atomics.md`, `../readme.md`.

- [ ] **Step 4: Write `asynchronous-data-movement.md`**

Sections: `## Why the copy should not block`, `## `cuda::memcpy_async``, `## Barriers and pipelines`, `## Double buffering`, `## The Tensor Memory Accelerator`, `## Alignment requirements`.

Requirements:
- Frame the problem: the classic tiled loop is `load → __syncthreads() → compute → __syncthreads()`, which leaves the memory system idle during compute and the ALUs idle during load. Asynchronous copy lets stage *i+1* load while stage *i* computes.
- `:::note[...]` that async copy is genuinely asynchronous from CC 8.0+; on older hardware the API compiles and works but degrades to a synchronous copy.
- A complete two-stage pipeline skeleton:
  ```cpp showLineNumbers
  #include <cuda/pipeline>
  #include <cooperative_groups.h>
  namespace cg = cooperative_groups;

  __global__ void pipelined(const float* g_in, float* g_out, int nTiles) {
      __shared__ float tile[2][256];
      auto block = cg::this_thread_block();
      constexpr size_t stages = 2;
      __shared__ cuda::pipeline_shared_state<cuda::thread_scope_block, stages> pss;
      auto pipe = cuda::make_pipeline(block, &pss);

      pipe.producer_acquire();
      cuda::memcpy_async(block, tile[0], g_in, sizeof(float) * 256, pipe);
      pipe.producer_commit();

      for (int t = 0; t < nTiles; ++t) {
          const int cur = t % stages, nxt = (t + 1) % stages;
          if (t + 1 < nTiles) {
              pipe.producer_acquire();
              cuda::memcpy_async(block, tile[nxt], g_in + (t + 1) * 256,
                                 sizeof(float) * 256, pipe);
              pipe.producer_commit();
          }
          pipe.consumer_wait();
          // ... compute on tile[cur] ...
          pipe.consumer_release();
      }
      (void)g_out;
  }
  ```
- The TMA section: what it adds over `memcpy_async` (a single thread issues a whole multi-dimensional tile copy described by a tensor map, freeing the other threads and the address-generation units), and that it is driven through `cuda::device::experimental::cp_async_bulk_tensor_*` or CUTLASS. `:::note[Requires CC 9.0+]`.
- Alignment: `memcpy_async` reaches its fastest path only at 16-byte alignment and 4/8/16-byte element sizes; state that misalignment silently falls back.

See also: `pinned-memory-and-transfers.md`, `../07-kernel-optimization/software-pipelining.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../02-gpu-hardware-architecture/nvidia-architecture-generations.md`, `../readme.md`.

- [ ] **Step 5: Write `memory-consistency-and-fences.md`**

Sections: `## The default is weak`, `## Fences`, `## `volatile` is not a fence`, `## Scoped atomics`, `## Putting it together`.

Requirements:
- State the model plainly: CUDA's memory model is weakly ordered; without a fence or an atomic, one thread's writes may become visible to another in any order.
- The fence family as a table: `__threadfence_block()` (block scope), `__threadfence()` (device scope), `__threadfence_system()` (system scope, includes host and peer GPUs).
- `volatile` explained correctly — it prevents the compiler from caching a value in a register, and nothing more. It orders nothing. `:::warning[...]` that pre-Volta code using `volatile` for warp-synchronous reduction is broken on all current hardware; the fix is `__shfl_sync`, see [Warp-Level Primitives](../05-execution-and-synchronization/warp-level-primitives.md).
- `cuda::atomic` with scopes, shown concretely:
  ```cpp showLineNumbers
  #include <cuda/atomic>

  __device__ cuda::atomic<int, cuda::thread_scope_device> flag{0};

  // producer
  data[0] = 42;
  flag.store(1, cuda::memory_order_release);

  // consumer
  while (flag.load(cuda::memory_order_acquire) != 1) { /* spin */ }
  int v = data[0];   // guaranteed to see 42
  ```
- A closing table `| I want | Use |` mapping intents to constructs: publish data to my block → `__syncthreads()`; publish to the device → release atomic or `__threadfence()`; publish to the host → `__threadfence_system()` plus a system-scope atomic.

See also: `asynchronous-data-movement.md`, `../05-execution-and-synchronization/atomics.md`, `../05-execution-and-synchronization/block-synchronization.md`, `../readme.md`.

- [ ] **Step 6: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/04-cuda-memory-model
git commit -m "docs: cuda memory model, part 2"
```
Expected: build exits 0.

---

### Task 5: `05-execution-and-synchronization`, pages 1–4

**Files:**
- Modify: `warp-execution-and-divergence.md`, `independent-thread-scheduling.md`, `warp-level-primitives.md`, `block-synchronization.md`

**Interfaces:**
- Consumes: `02-gpu-hardware-architecture/warps-and-schedulers.md`.
- Produces: the `warpReduceSum` function used verbatim by Task 6's `reductions-and-scans.md` and by `13-applied-kernels-and-patterns/parallel-reduction.md`.

- [ ] **Step 1: Write `warp-execution-and-divergence.md`**

Sections: `## One instruction, 32 threads`, `## The active mask`, `## What divergence costs`, `## Divergence that does not cost anything`, `## Restructuring to converge`.

Requirements:
- The cost model stated numerically: an `if/else` where both sides are taken within a warp executes both sides, so the warp pays the *sum* of the branches, not the max of one. A 32-way switch inside a warp costs 32 sequential passes.
- The crucial distinction with a `cpp` example of each: divergence *within* a warp costs; a branch on `blockIdx.x`, or on `threadIdx.x / 32`, is warp-uniform and costs nothing.
- A Mermaid diagram of the active mask through a diverging branch, with quoted labels.
- `:::tip[...]` — sorting or binning work so that similar work lands in the same warp is usually a bigger win than any branch-free rewrite; forward to [Reducing Divergence](../07-kernel-optimization/reducing-divergence.md).

See also: `independent-thread-scheduling.md`, `warp-level-primitives.md`, `../07-kernel-optimization/reducing-divergence.md`, `../02-gpu-hardware-architecture/warps-and-schedulers.md`, `../readme.md`.

- [ ] **Step 2: Write `independent-thread-scheduling.md`**

Sections: `## Before Volta`, `## Per-thread program counters`, `## What broke`, `## Why every intrinsic now takes a mask`, `## Reconvergence is not automatic`.

Requirements:
- `:::note[CC 7.0+]` — this is the behaviour on every GPU from Volta onward; pre-Volta behaviour is historical context only.
- Show the broken idiom explicitly, clearly labelled as **broken**, because readers will meet it in old tutorials:
  ```cpp showLineNumbers
  // BROKEN on CC 7.0+ — do not use. Historical example only.
  __device__ int warpReduceOld(volatile int* s, int lane) {
      if (lane < 16) s[lane] += s[lane + 16];
      if (lane <  8) s[lane] += s[lane +  8];   // no guarantee the previous line
      if (lane <  4) s[lane] += s[lane +  4];   // has completed across the warp
      // ...
      return s[0];
  }
  ```
  Then the correct version using `__shfl_down_sync`, forward-referencing the next page.
- Explain the mask argument's real meaning: it names the threads that must participate, and it is the programmer's assertion of convergence — a wrong mask is undefined behaviour, not a no-op.
- `__syncwarp()` introduced here as the explicit reconvergence tool.

See also: `warp-level-primitives.md`, `warp-execution-and-divergence.md`, `../04-cuda-memory-model/memory-consistency-and-fences.md`, `../readme.md`.

- [ ] **Step 3: Write `warp-level-primitives.md`**

Sections: `## The shuffle family`, `## Vote intrinsics`, `## `__activemask` and `__match_any_sync``, `## A warp reduction`, `## Masks in divergent code`.

Requirements:
- A table of the shuffle family: `__shfl_sync`, `__shfl_up_sync`, `__shfl_down_sync`, `__shfl_xor_sync` — each with its lane-selection rule and one use case.
- The vote intrinsics: `__all_sync`, `__any_sync`, `__ballot_sync`, with `__popc(__ballot_sync(...))` shown as the standard "count matching lanes" idiom.
- The canonical warp reduction, which later pages reuse **verbatim** — keep this exact signature and name:
  ```cpp showLineNumbers
  __inline__ __device__ float warpReduceSum(float val) {
      for (int offset = warpSize / 2; offset > 0; offset >>= 1)
          val += __shfl_down_sync(0xffffffff, val, offset);
      return val;   // lane 0 holds the total
  }
  ```
- `:::warning[...]` that `0xffffffff` is correct only when the whole warp is converged. Inside divergent code use `__activemask()` — and explain why `__activemask()` is itself dangerous as a general habit (it reports what *is* converged, not what *should* be).
- `__match_any_sync` with its one great use: grouping lanes by key for conflict-free aggregation, e.g. warp-aggregated atomics.

See also: `independent-thread-scheduling.md`, `reductions-and-scans.md`, `cooperative-groups.md`, `../13-applied-kernels-and-patterns/parallel-reduction.md`, `../readme.md`.

- [ ] **Step 4: Write `block-synchronization.md`**

Sections: `## What `__syncthreads` guarantees`, `## The divergence rule`, `## The variants`, `## `__syncwarp``, `## Common deadlocks`.

Requirements:
- Both guarantees stated: execution barrier *and* memory barrier for shared and global accesses made by the block.
- The divergence rule stated as a hard rule: every thread in the block must reach the same `__syncthreads()`. A `__syncthreads()` inside a conditional that only some threads take is undefined behaviour.
- Show the deadlock pattern and its fix:
  ```cpp showLineNumbers
  // WRONG — threads with i >= n never reach the barrier
  if (i < n) {
      tile[threadIdx.x] = in[i];
      __syncthreads();
  }

  // RIGHT — barrier is unconditional
  tile[threadIdx.x] = (i < n) ? in[i] : 0.0f;
  __syncthreads();
  ```
- The variants table: `__syncthreads_count`, `__syncthreads_and`, `__syncthreads_or` with one use each.
- `:::tip[...]` — `compute-sanitizer --tool synccheck` catches divergent barriers; see [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md).

See also: `cooperative-groups.md`, `../04-cuda-memory-model/shared-memory.md`, `../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/05-execution-and-synchronization
git commit -m "docs: execution and synchronization, part 1"
```
Expected: build exits 0.

---

### Task 6: `05-execution-and-synchronization`, pages 5–8

**Files:**
- Modify: `cooperative-groups.md`, `atomics.md`, `grid-wide-synchronization.md`, `reductions-and-scans.md`

**Interfaces:**
- Consumes: Task 5's `warpReduceSum`.
- Produces: `blockReduceSum`, used by `13-applied-kernels-and-patterns/parallel-reduction.md` and `softmax-and-layernorm.md`.

- [ ] **Step 1: Write `cooperative-groups.md`**

Sections: `## The idea`, `## `thread_block``, `## Tiled partitions`, `## `coalesced_group``, `## `grid_group` and `cluster_group``, `## Why this replaces hand-rolled idioms`.

Requirements:
- Frame it as making the *group* explicit: instead of an implicit warp and a magic mask, you hold an object whose `size()`, `thread_rank()`, `sync()`, and `shfl_down()` are well defined — which is what makes the code correct under independent thread scheduling.
- The tiled-partition reduction, contrasted with the raw-intrinsic version from the previous task:
  ```cpp showLineNumbers
  #include <cooperative_groups.h>
  #include <cooperative_groups/reduce.h>
  namespace cg = cooperative_groups;

  __device__ float tileReduceSum(float val) {
      auto block = cg::this_thread_block();
      auto tile  = cg::tiled_partition<32>(block);
      return cg::reduce(tile, val, cg::plus<float>());
  }
  ```
- A table of the group types: `thread_block`, `thread_block_tile<N>`, `coalesced_group`, `grid_group`, `cluster_group` — scope, how to obtain it, and what `sync()` costs on each.
- `:::tip[...]` — `cg::reduce` and `cg::inclusive_scan` compile down to the same shuffles you would write by hand and are correct by construction; prefer them.
- `:::note[...]` that `grid_group` requires a cooperative launch and `cluster_group` requires CC 9.0+.

See also: `warp-level-primitives.md`, `grid-wide-synchronization.md`, `../03-cuda-programming-model/thread-block-clusters.md`, `../readme.md`.

- [ ] **Step 2: Write `atomics.md`**

Sections: `## What atomics guarantee`, `## Global versus shared`, `## Supported types`, `## Contention`, `## `atomicCAS` for everything else`, `## Privatization`.

Requirements:
- The performance model stated as the page's core message: atomics to the *same address* serialize. 32 threads hitting one address is a 32× slowdown on that instruction; 32 threads hitting 32 addresses is close to free.
- A table of the built-ins: `atomicAdd` (int, unsigned, unsigned long long, float, double, `__half2`), `atomicMin/Max`, `atomicCAS`, `atomicExch`, `atomicAnd/Or/Xor`, noting `atomicAdd` for `double` requires CC 6.0+.
- The `atomicCAS` loop pattern for an unsupported operation, complete:
  ```cpp showLineNumbers
  __device__ float atomicMaxFloat(float* addr, float value) {
      int* iaddr = reinterpret_cast<int*>(addr);
      int old = *iaddr, assumed;
      do {
          assumed = old;
          const float cur = __int_as_float(assumed);
          if (cur >= value) break;
          old = atomicCAS(iaddr, assumed, __float_as_int(value));
      } while (assumed != old);
      return __int_as_float(old);
  }
  ```
  `:::warning[...]` that this works only for non-negative floats because of the sign-bit ordering of the integer reinterpretation.
- Privatization as the standard fix: per-block shared-memory accumulators, one global atomic per block at the end. Forward to [Histogram](../13-applied-kernels-and-patterns/histogram.md) and, on CC 9.0+, [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md).

See also: `../04-cuda-memory-model/memory-consistency-and-fences.md`, `../04-cuda-memory-model/distributed-shared-memory.md`, `../13-applied-kernels-and-patterns/histogram.md`, `../readme.md`.

- [ ] **Step 3: Write `grid-wide-synchronization.md`**

Sections: `## Why blocks cannot normally sync`, `## Cooperative launch`, `## `grid.sync()``, `## The occupancy constraint`, `## When a second kernel is better`.

Requirements:
- The mechanism: `grid.sync()` is only sound if every block is *resident simultaneously*, so a cooperative launch caps the grid at what fits on the device — which is why it needs `cudaOccupancyMaxActiveBlocksPerMultiprocessor` to size the launch.
- The full launch, since the API shape is unusual:
  ```cpp showLineNumbers
  void* args[] = { &d_data, &n };
  int blocksPerSm = 0;
  CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(
      &blocksPerSm, myCoopKernel, threads, 0));
  int smCount = 0;
  CUDA_CHECK(cudaDeviceGetAttribute(&smCount, cudaDevAttrMultiProcessorCount, 0));
  dim3 grid(smCount * blocksPerSm), block(threads);
  CUDA_CHECK(cudaLaunchCooperativeKernel(
      (void*)myCoopKernel, grid, block, args));
  ```
- The honest verdict, as a `:::tip`: two kernel launches cost a few microseconds and impose no occupancy cap; a cooperative launch is worth it only when the kernel keeps large state resident across the barrier. Point at [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md) for cutting the launch cost instead.
- `:::note[...]` that cluster-level `cluster.sync()` (CC 9.0+) is the cheaper middle ground for small groups.

See also: `cooperative-groups.md`, `../03-cuda-programming-model/thread-block-clusters.md`, `../06-cuda-runtime-and-apis/cuda-graphs.md`, `../readme.md`.

- [ ] **Step 4: Write `reductions-and-scans.md`**

Sections: `## The shape of the problem`, `## Warp reduction`, `## Block reduction`, `## The two-phase grid reduction`, `## Scan`, `## Use CUB in production`.

Requirements:
- Reuse `warpReduceSum` **verbatim** from `warp-level-primitives.md`, then build on it — keep this exact name and signature, since folder 13 uses both:
  ```cpp showLineNumbers
  __inline__ __device__ float blockReduceSum(float val) {
      static __shared__ float shared[32];       // one slot per warp
      const int lane = threadIdx.x % warpSize;
      const int wid  = threadIdx.x / warpSize;

      val = warpReduceSum(val);                 // reduce within each warp
      if (lane == 0) shared[wid] = val;
      __syncthreads();

      val = (threadIdx.x < blockDim.x / warpSize) ? shared[lane] : 0.0f;
      if (wid == 0) val = warpReduceSum(val);   // reduce the warp totals
      return val;                               // thread 0 holds the block total
  }
  ```
- The two-phase pattern: kernel 1 reduces to one value per block, kernel 2 reduces those. State why this beats a single kernel with a grid-wide barrier for most sizes.
- Scan: state the difference from reduction (every prefix is an output), name Hillis-Steele vs Blelloch, and defer the full treatment to [Prefix Sum (Scan)](../13-applied-kernels-and-patterns/prefix-sum.md).
- `:::tip[...]` — `cub::BlockReduce` and `cub::DeviceScan` are faster than almost any hand-written version and are tuned per architecture; write your own to understand the machine, ship CUB. Link [CUB](../08-libraries-and-ecosystem/cub.md).

See also: `warp-level-primitives.md`, `cooperative-groups.md`, `../08-libraries-and-ecosystem/cub.md`, `../13-applied-kernels-and-patterns/parallel-reduction.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/05-execution-and-synchronization
git commit -m "docs: execution and synchronization, part 2"
```
Expected: build exits 0.

---

### Task 7: Figures for folder 03

**Files:**
- Create: `static/img/gpu/03-cuda-programming-model/*.png`
- Modify: `static/img/gpu/SOURCES.md`
- Modify: `docs/gpu-computing/03-cuda-programming-model/threads-blocks-and-grids.md`, `thread-block-clusters.md`

- [ ] **Step 1: Download the two figures**

```bash
mkdir -p static/img/gpu/03-cuda-programming-model
curl -fsSL -o static/img/gpu/03-cuda-programming-model/grid-of-thread-blocks.png \
  https://docs.nvidia.com/cuda/cuda-c-programming-guide/_images/grid-of-thread-blocks.png
curl -fsSL -o static/img/gpu/03-cuda-programming-model/grid-of-clusters.png \
  https://docs.nvidia.com/cuda/cuda-c-programming-guide/_images/grid-of-clusters.png
```

- [ ] **Step 2: Verify the downloads**

Run: `file static/img/gpu/03-cuda-programming-model/*.png`
Expected: both report `PNG image data`.

**If a download 404s or is not a PNG:** delete it, skip its Steps 3–4, keep the page's Mermaid diagram, and say so in the commit message. Do not substitute an image from another source without checking its terms.

- [ ] **Step 3: Add the `SOURCES.md` rows**

Append to the table in `static/img/gpu/SOURCES.md`, replacing `<today>` with the actual ISO date:

```md
| `03-cuda-programming-model/grid-of-thread-blocks.png` | https://docs.nvidia.com/cuda/cuda-c-programming-guide/ | NVIDIA | <today> | Figure from the CUDA C++ Programming Guide; NVIDIA documentation terms. |
| `03-cuda-programming-model/grid-of-clusters.png` | https://docs.nvidia.com/cuda/cuda-c-programming-guide/ | NVIDIA | <today> | Figure from the CUDA C++ Programming Guide; NVIDIA documentation terms. |
```

- [ ] **Step 4: Reference them from the pages**

In `threads-blocks-and-grids.md`, in `## The hierarchy`, after the Mermaid tree:

```md
![A 2-D grid of 2-D thread blocks](/img/gpu/03-cuda-programming-model/grid-of-thread-blocks.png)
*Source: [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)*
```

In `thread-block-clusters.md`, in `## Why a level between grid and block`:

```md
![A grid of clusters, each cluster containing several thread blocks](/img/gpu/03-cuda-programming-model/grid-of-clusters.png)
*Source: [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)*
```

- [ ] **Step 5: Verify and commit**

```bash
npm run build && npm run format && npm run lint
git add static/img/gpu docs/gpu-computing/03-cuda-programming-model
git commit -m "docs: add cuda programming model figures"
```
Expected: build exits 0.

---

## Plan 2 completion criteria

- 28 pages written; `npm run build` and `npm run lint` both exit 0.
- `warpReduceSum` and `blockReduceSum` exist with exactly the signatures above — plans 4 and 6 reuse them by name.
- Every CC-gated feature (clusters, DSMEM, TMA, independent thread scheduling, `atomicAdd` for `double`) carries a `:::note` naming its compute capability.
- No non-`_sync` warp intrinsic appears except inside a block explicitly labelled as a broken historical example.
- `static/img/gpu/SOURCES.md` has a row for every file under `static/img/gpu/`.
