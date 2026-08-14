# GPU & Accelerators — Plan 6: Applied Kernels, Cross-Links, and Final Audit

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the 12 pages of `13-applied-kernels-and-patterns/`, complete the six outward cross-links the spec requires, and run the final audit that closes the section.

**Architecture:** Every file already exists as a stub with correct frontmatter (plan 1, task 1). This plan fills in the last bodies, then does a whole-section verification pass. Each folder-13 page follows one fixed shape: naive version → measure → identify the limiter → improved version → measure again.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism `cpp`/`bash`/`text` fences, Biome, Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Prerequisite:** Plans 1–5 complete. Verify all three:
```bash
ls docs/gpu-computing/13-applied-kernels-and-patterns/ | wc -l     # 13 (12 md + _category_.json)
grep -rn "define CUDA_CHECK" docs/gpu-computing/ | wc -l           # 1
grep -rn "sgemmTiled" docs/gpu-computing/07-kernel-optimization/   # non-empty
```

**Plan series:** plan 6 of 6.

---

## Global Constraints

These apply to **every** page this plan writes and are not restated per task.

### Frontmatter

Already written by plan 1. **Do not change `id`, `title`, `sidebar_label`, `sidebar_position`, or `tags`.** Replace only the body below the frontmatter.

### The folder-13 page shape

Every page in folder 13 follows this structure. It is not optional — the folder's value is the repetition of one disciplined method.

1. `# H1` (already in the stub), then 1–2 paragraphs on **what the kernel is for and why it is interesting as an optimization problem**.
2. `## The naive version` — complete, compilable kernel.
3. `## Measuring it` — what to measure and against what ceiling (effective bandwidth vs peak, or time vs the library equivalent).
4. `## What limits it` — the diagnosis, naming the Nsight Compute metric that shows it.
5. One `##` per optimization step, each with the change, the reason, and the new measurement.
6. `## Comparison with the library` — cuBLAS/CUB/cuSPARSE where one exists, with the honest gap.
7. `## See also` — 3–5 plain relative Markdown links, siblings first, then cross-folder, then `../readme.md`.

### Performance numbers

**Every number states the GPU it was measured on, the problem size, and the dtype.** Format: "≈ 1.35 TB/s on an A100-SXM4-80GB (CC 8.0) at N = 2²⁶, FP32 — about 85% of the 1.6 TB/s peak."

If you cannot attribute a number to a specific measurement, **do not invent one.** Write the direction and the mechanism instead: "removing the bank conflict eliminates the 32-way serialization on the shared-memory read, which is the dominant stall in the naive version." A fabricated benchmark is worse than no benchmark.

Every page must also state the benchmarking conditions once, referring to [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) rather than restating the checklist.

### Reused code

These names are already defined earlier in the section. **Reuse them by name; do not redefine them.**

| Symbol | Defined in |
|---|---|
| `CUDA_CHECK` | `06-cuda-runtime-and-apis/error-handling.md` |
| `warpReduceSum` | `05-execution-and-synchronization/warp-level-primitives.md` |
| `blockReduceSum` | `05-execution-and-synchronization/reductions-and-scans.md` |
| `sgemmTiled` (`TILE = 32`) | `07-kernel-optimization/shared-memory-tiling.md` |

A page may show a *variant* of one of these (e.g. a register-tiled `sgemmRegTiled`), but must name the variant differently and say what it changed.

### Code fences

`cpp` for CUDA C++, `text` for PTX/SASS and profiler output, `bash` for commands. **No `python` anywhere in this plan.** `showLineNumbers` on fences longer than ~5 lines; `title="filename.cu"` for standalone files.

### Admonitions

Only `:::info[...]`, `:::note[...]`, `:::tip[...]`, `:::warning[...]`.

### MDX hazards

Outside code fences and inline backticks, always backtick: `__global__`, `__device__`, `__shared__`, `__syncthreads`, `<<<grid, block>>>`, `<T>`, and any bare `{` or `}`.

### Diagrams

Mermaid for structural content. **Quote every edge label:** `A -->|"label (with parens)"| B`.

### Verification gate — every task

1. `npm run build` exits 0.
2. `npm run format` then `npm run lint` — both exit 0.
3. Commit. One-line message, `<type>: <what>`. **Never** add a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

---

## File Structure

```
docs/gpu-computing/
└── 13-applied-kernels-and-patterns/  12 pages  Task 1 (1-4), Task 2 (5-8), Task 3 (9-12)

Task 4 modifies one page in 07-kernel-optimization/ (the last outward cross-link).
Task 5 audits the whole section and touches nothing unless it finds a defect.
```

---

### Task 1: Applied kernels, pages 1–4

**Files:**
- Modify: `vector-add-and-saxpy.md`, `parallel-reduction.md`, `prefix-sum.md`, `matrix-multiply.md`

**Interfaces:**
- Consumes: `warpReduceSum`, `blockReduceSum`, `sgemmTiled`; the metric names from `09-tooling-profiling-and-debugging/metrics-that-matter.md`.
- Produces: `sgemmRegTiled` (register-tiled variant), which `matrix-multiply-tensor-cores.md` in Task 2 compares against.

- [ ] **Step 1: Write `vector-add-and-saxpy.md`**

The bandwidth-bound baseline. This page teaches the measurement method the rest of the folder uses, so it is the most method-heavy of the twelve.

Sections beyond the standard shape: `## Effective bandwidth`, `## Grid-stride version`, `## Vectorized version`, `## The ceiling`.

Requirements:
- Naive kernel: the one-thread-one-element SAXPY from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md), restated so the page stands alone.
- The effective-bandwidth formula worked for SAXPY explicitly: 2 reads + 1 write × 4 bytes × N = 12N bytes, so `GB/s = 12N / (t × 10⁹)`. This is the number every later page's measurement section is modelled on.
- Grid-stride variant (from [Thread Indexing](../03-cuda-programming-model/thread-indexing.md)) with the reason it matters here: grid size becomes an occupancy choice rather than a data-size consequence.
- `float4` variant, with the alignment precondition and the tail handling shown.
- `## The ceiling` makes the page's real point: SAXPY has arithmetic intensity ≈ 0.083 FLOP/byte, so it is bandwidth-bound at every problem size and no arithmetic optimization can help. Once you are at 80–90% of measured peak bandwidth, you are done — link [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md).
- `:::tip[...]` — measure peak bandwidth on your own device with a pure copy kernel and use *that* as the denominator, not the spec sheet.

See also: `parallel-reduction.md`, `../04-cuda-memory-model/global-memory-and-coalescing.md`, `../09-tooling-profiling-and-debugging/benchmarking-methodology.md`, `../02-gpu-hardware-architecture/device-memory-and-bandwidth.md`, `../readme.md`.

- [ ] **Step 2: Write `parallel-reduction.md`**

The classic staged optimization, done in the modern idiom rather than the 2007 one.

Sections beyond the standard shape: one `##` per stage — `## Stage 1: interleaved addressing`, `## Stage 2: sequential addressing`, `## Stage 3: first add during load`, `## Stage 4: warp shuffles`, `## Comparison with CUB`.

Requirements:
- Stage 1 kernel with `if (tid % (2 * s) == 0)` and the diagnosis: maximum warp divergence and shared-memory bank conflicts.
- Stage 2 replaces the stride pattern with `for (s = blockDim.x / 2; s > 0; s >>= 1)` and `if (tid < s)` — divergence now only in the last warp, no bank conflicts. Explain why.
- Stage 3 halves the grid and performs one add during the global load, so the first level of the tree costs nothing extra.
- Stage 4 replaces the final in-shared-memory stages with `warpReduceSum` from [Warp-Level Primitives](../05-execution-and-synchronization/warp-level-primitives.md), then presents the whole kernel using `blockReduceSum` from [Reductions and Scans](../05-execution-and-synchronization/reductions-and-scans.md):
  ```cpp showLineNumbers title="reduce.cu"
  __global__ void reduceKernel(const float* __restrict__ in, float* out, int n) {
      float sum = 0.0f;
      for (int i = blockIdx.x * blockDim.x + threadIdx.x;
           i < n; i += blockDim.x * gridDim.x)
          sum += in[i];

      sum = blockReduceSum(sum);
      if (threadIdx.x == 0) out[blockIdx.x] = sum;
  }
  ```
  and note that the second pass reduces the per-block partials.
- `:::warning[...]` that floating-point reduction is not associative, so the result depends on the tree shape; a "wrong" result versus the CPU may be a rounding difference, not a bug. Suggest comparing against a Kahan or double-precision reference.
- The CUB comparison, stated honestly: `cub::DeviceReduce::Sum` is at least as fast and handles every block size and architecture. The staged walkthrough exists to teach the machine, not to produce shipping code.

See also: `../05-execution-and-synchronization/reductions-and-scans.md`, `../08-libraries-and-ecosystem/cub.md`, `prefix-sum.md`, `histogram.md`, `../readme.md`.

- [ ] **Step 3: Write `prefix-sum.md`**

Sections beyond the standard shape: `## Hillis-Steele`, `## Blelloch (work-efficient)`, `## Block scan plus block offsets`, `## Decoupled look-back`, `## Comparison with CUB`.

Requirements:
- Define inclusive vs exclusive scan in the opening prose, since the rest of the page depends on the distinction.
- Hillis-Steele shown in `cpp` with its cost: `O(n log n)` work, `O(log n)` steps — simple, and fine within a warp or a small block.
- Blelloch shown as the two-phase up-sweep/down-sweep with `O(n)` work, plus a Mermaid diagram of the reduce and down-sweep trees with quoted labels.
- The three-kernel decomposition for large arrays: block scan → scan the block sums → add block offsets. State the cost: three passes over the data on a bandwidth-bound problem.
- Decoupled look-back explained as the modern single-pass answer: each block publishes an aggregate, then an inclusive prefix, and looks backward through predecessors' flags rather than waiting for a global barrier — turning three passes into roughly one. Describe the state machine (invalid → aggregate available → inclusive prefix available) rather than showing a full implementation, and say plainly this is what `cub::DeviceScan` implements.
- `:::warning[...]` that a hand-written decoupled-look-back scan needs correct memory ordering (see [Memory Consistency and Fences](../04-cuda-memory-model/memory-consistency-and-fences.md)); this is one of the easiest kernels to get subtly wrong.

See also: `parallel-reduction.md`, `../08-libraries-and-ecosystem/cub.md`, `../04-cuda-memory-model/memory-consistency-and-fences.md`, `sorting-on-the-gpu.md`, `../readme.md`.

- [ ] **Step 4: Write `matrix-multiply.md`**

Sections beyond the standard shape: `## The naive kernel`, `## Shared-memory tiling`, `## Register tiling`, `## Vectorized loads`, `## Arithmetic intensity at each step`, `## Comparison with cuBLAS`.

Requirements:
- Naive kernel: one thread per output element, `2N` global reads per output. Compute its arithmetic intensity (≈0.25 FLOP/byte FP32) and conclude it is hopelessly bandwidth-bound.
- Shared-memory tiling: reuse `sgemmTiled` from [Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md) **verbatim, by name**, with a one-line pointer rather than a re-derivation. Recompute intensity: reuse rises by a factor of `TILE`.
- Register tiling as the step folder 07 did not cover — each thread computes a `TM × TN` micro-tile held in registers, so shared-memory traffic drops by the same factor. Name it `sgemmRegTiled` and show the accumulator array and the inner loop:
  ```cpp showLineNumbers title="sgemm_regtiled.cu"
  #define TILE 32
  #define TM 4          // rows of C per thread
  #define TN 4          // cols of C per thread

  __global__ void sgemmRegTiled(int N, const float* __restrict__ A,
                                const float* __restrict__ B, float* __restrict__ C) {
      __shared__ float As[TILE][TILE + 1];
      __shared__ float Bs[TILE][TILE + 1];
      float acc[TM][TN] = {};
      // ... cooperative tile load into As/Bs, then:
      for (int k = 0; k < TILE; ++k) {
          float a[TM], b[TN];
          // ... load a[] from As column k, b[] from Bs row k ...
          for (int i = 0; i < TM; ++i)
              for (int j = 0; j < TN; ++j)
                  acc[i][j] += a[i] * b[j];      // TM*TN FMAs per TM+TN loads
      }
      // ... write acc back to C ...
  }
  ```
  State the ratio explicitly: `TM × TN` FMAs per `TM + TN` shared-memory reads — that ratio is the whole point.
- Vectorized loads (`float4`) on the tile load, referencing [Memory Access Optimization](../07-kernel-optimization/memory-access-optimization.md).
- A summary table `| Version | Arithmetic intensity | Dominant limiter |` across the four versions.
- `## Comparison with cuBLAS` closes honestly: a good hand-written SGEMM reaches a fraction of cuBLAS, which uses tensor cores, TMA, warp specialization, and per-architecture tuning. Link [cuBLAS](../08-libraries-and-ecosystem/cublas.md) and [CUTLASS](../08-libraries-and-ecosystem/cutlass.md).

See also: `matrix-multiply-tensor-cores.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `../08-libraries-and-ecosystem/cublas.md`, `matrix-transpose.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/13-applied-kernels-and-patterns
git commit -m "docs: applied kernels, part 1"
```
Expected: build exits 0.

---

### Task 2: Applied kernels, pages 5–8

**Files:**
- Modify: `matrix-multiply-tensor-cores.md`, `matrix-transpose.md`, `histogram.md`, `stencil-and-convolution.md`

**Interfaces:**
- Consumes: Task 1's `sgemmRegTiled`; the `wmma` fragment example from `07-kernel-optimization/programming-tensor-cores.md`; the cluster histogram from `04-cuda-memory-model/distributed-shared-memory.md`.
- Produces: nothing later tasks depend on by name.

- [ ] **Step 1: Write `matrix-multiply-tensor-cores.md`**

Sections beyond the standard shape: `## From FMA to MMA`, `## The wmma kernel`, `## Fragment layouts`, `## Accuracy`, `## Comparison with cuBLAS`.

Requirements:
- `:::note[...]` on hardware requirements, linking [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md); do not restate the per-generation precision table.
- Build the kernel by replacing the inner FMA loop of the tiled version with `wmma` fragments — extend the example from [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) into a complete kernel over a `16 × 16 × 16` tile grid, with `half` inputs and `float` accumulators.
- The two facts that break people's first attempt, stated as `:::warning`: a fragment is warp-owned so all 32 threads must execute every `wmma` call (no divergence), and the leading dimension passed to `load_matrix_sync` is in elements of the fragment's type, not bytes.
- Accuracy: FP16 inputs with FP32 accumulate is far more accurate than FP16 accumulate; say what changes and why the accumulator type is the number that matters. Cross-link [Quantization for Accelerators](../12-npu-and-inference-accelerators/quantization-for-accelerators.md) for the inference-side view.
- The cuBLAS comparison, framed as the lesson of the page: `wmma` gets you tensor-core throughput, and you still lose to cuBLAS because the remaining gap is pipelining, layout, and warp specialization — which is what [CUTLASS](../08-libraries-and-ecosystem/cutlass.md) exists to give you.

See also: `matrix-multiply.md`, `../07-kernel-optimization/programming-tensor-cores.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../02-gpu-hardware-architecture/tensor-cores.md`, `../readme.md`.

- [ ] **Step 2: Write `matrix-transpose.md`**

The cleanest demonstration in the section that coalescing alone can dominate a kernel's runtime.

Sections beyond the standard shape: `## The naive kernel`, `## Why it is slow`, `## Shared-memory staging`, `## The padding fix`, `## The copy-kernel ceiling`.

Requirements:
- Naive kernel with `out[x * n + y] = in[y * n + x]`, and the diagnosis stated exactly: the read is coalesced and the write is strided by `n`, so each warp's 32 writes touch 32 separate sectors — one wasted 32-byte transaction per 4 useful bytes.
- Shared-memory staging: read coalesced into a `TILE × TILE` shared tile, `__syncthreads()`, write coalesced out of it transposed. Show the complete kernel.
- The padding fix as its own section, since the staged version is *still* slow without it: `__shared__ float tile[TILE][TILE]` gives a 32-way bank conflict on the transposed read; `tile[TILE][TILE + 1]` removes it. Link [Shared Memory Bank Conflicts](../04-cuda-memory-model/bank-conflicts.md) and show the one-character diff.
- `## The copy-kernel ceiling`: benchmark a pure copy kernel of the same size as the ceiling, because transpose moves exactly the same bytes. The fraction of copy bandwidth achieved is the real score.
- `:::tip[...]` — this three-step progression (naive → staged → padded) is the canonical worked example for the whole memory-access chapter; if a kernel writes with a stride, this is the pattern to reach for.

See also: `../04-cuda-memory-model/bank-conflicts.md`, `../04-cuda-memory-model/global-memory-and-coalescing.md`, `matrix-multiply.md`, `../readme.md`.

- [ ] **Step 3: Write `histogram.md`**

Sections beyond the standard shape: `## The naive kernel`, `## Global atomic contention`, `## Shared-memory privatization`, `## Handling more bins than fit`, `## Distributed shared memory`, `## Comparison with CUB`.

Requirements:
- Naive kernel: `atomicAdd(&bins[in[i]], 1)` straight to global memory, with the diagnosis — throughput collapses when the input distribution is skewed, because every thread hitting the same bin serializes. Say explicitly that this kernel's performance is *data-dependent*, which makes it easy to benchmark misleadingly (`:::warning[...]`, and benchmark on both uniform and skewed input).
- Privatization: per-block shared-memory bins, zeroed with `__syncthreads()` on both sides, then one global `atomicAdd` per bin per block. Show the complete kernel.
- The bin-count problem: shared memory caps bins per block, so histograms with many bins need either multiple passes over bin ranges or the cluster approach.
- Distributed shared memory: reference the cluster histogram from [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) **by link, not by copy**, and add what that page does not — when it wins (bins that fit in `nBlocks × 48 KB` but not in one block) and `:::note[Requires CC 9.0+]`.
- Warp-aggregated atomics mentioned as the third technique: `__match_any_sync` groups lanes writing the same bin so one lane performs the atomic for the group. Link [Warp-Level Primitives](../05-execution-and-synchronization/warp-level-primitives.md).
- CUB comparison: `cub::DeviceHistogram::HistogramEven`.

See also: `../04-cuda-memory-model/distributed-shared-memory.md`, `../05-execution-and-synchronization/atomics.md`, `../08-libraries-and-ecosystem/cub.md`, `parallel-reduction.md`, `../readme.md`.

- [ ] **Step 4: Write `stencil-and-convolution.md`**

Sections beyond the standard shape: `## The naive kernel`, `## Halo regions`, `## Shared-memory tiling with halos`, `## Separable filters`, `## Constant memory for coefficients`, `## Register tiling in the slow dimension`.

Requirements:
- Naive 2-D 5-point stencil, and the diagnosis: each element is read up to 5 times from global memory; the L1/L2 caches recover some of it but not reliably at large widths.
- Halo tiling explained with a Mermaid diagram (an interior tile plus its one-element border) and the index arithmetic spelled out, since off-by-one in the halo load is the standard bug. Show the complete kernel with the `TILE + 2R` shared array.
- `:::warning[...]` on the two loading strategies and their tradeoff: fewer threads than shared elements (some threads load twice) versus a larger block that loads once and has idle threads during compute. Say which is usually better and why.
- Separable filters: a 2-D Gaussian as two 1-D passes turns `K²` multiply-adds per output into `2K`. Give the arithmetic and say when separability applies.
- `__constant__` coefficients with the broadcast argument from [Constant and Texture Memory](../04-cuda-memory-model/constant-and-texture-memory.md) — every thread reads the same coefficient, which is exactly constant memory's fast case.
- 3-D stencils: sweep in the slow dimension holding a register window, so each plane is loaded once. Describe the technique and show the register-rotation sketch.

See also: `../04-cuda-memory-model/constant-and-texture-memory.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `matrix-transpose.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/13-applied-kernels-and-patterns
git commit -m "docs: applied kernels, part 2"
```
Expected: build exits 0.

---

### Task 3: Applied kernels, pages 9–12

**Files:**
- Modify: `sorting-on-the-gpu.md`, `sparse-matrix-vector.md`, `softmax-and-layernorm.md`, `flash-attention.md`

**Interfaces:**
- Consumes: `prefix-sum.md` (radix sort is built on scan), `blockReduceSum`.
- Produces: the folder's closing page (`flash-attention.md`), which ties the whole section together.

- [ ] **Step 1: Write `sorting-on-the-gpu.md`**

Sections beyond the standard shape: `## Why comparison sorts are awkward`, `## Radix sort`, `## Bitonic sort`, `## Segmented and key-value sorts`, `## Comparison with CUB`.

Requirements:
- Frame the problem: sorting is a global data movement problem, not an arithmetic one, so the GPU question is how to compute destination indices in parallel — which is why radix sort dominates.
- Radix sort structure explained as repeated stable counting sorts over `k`-bit digits, with the key insight that each pass is a histogram plus an exclusive scan plus a scatter — link [Prefix Sum (Scan)](./prefix-sum.md) and [Histogram](./histogram.md) and say explicitly that this page is where those two combine.
- A Mermaid diagram of one radix pass (digit histogram → scan → scatter) with quoted labels.
- Bitonic sort: a fixed comparison network, `O(n log²n)` work, no data-dependent branching — worth knowing because it is the right answer *inside* a block or for small fixed sizes, and the wrong answer for large arrays.
- `:::tip[...]` — `cub::DeviceRadixSort::SortPairs` is the practical answer; it is a highly tuned decoupled-look-back implementation, and a hand-written version will not match it. Write one to understand scan; ship CUB.
- Note key-value sorting as the common real use (sort indices alongside keys) and segmented sort for batched problems.

See also: `prefix-sum.md`, `histogram.md`, `../08-libraries-and-ecosystem/cub.md`, `../08-libraries-and-ecosystem/thrust.md`, `../readme.md`.

- [ ] **Step 2: Write `sparse-matrix-vector.md`**

Sections beyond the standard shape: `## Formats`, `## Scalar CSR (thread per row)`, `## Vector CSR (warp per row)`, `## ELL and hybrid`, `## Load imbalance`, `## Comparison with cuSPARSE`.

Requirements:
- The formats section defines CSR (`values`, `col_idx`, `row_ptr`) with a small worked example matrix, then ELL (padded to the max row length) and HYB (ELL + COO for the long tail). A table `| Format | Memory | Access pattern | Best when |`.
- Scalar CSR kernel — one thread per row — with the diagnosis: adjacent threads read non-adjacent `values`, so the access is uncoalesced, and rows of unequal length cause severe intra-warp divergence.
- Vector CSR kernel — one warp per row, with `warpReduceSum` for the partial products. Show the complete kernel and explain that the load is now coalesced within a row.
- The tradeoff stated plainly: warp-per-row wastes lanes on short rows, thread-per-row wastes bandwidth on long ones. The right choice depends on the average row length; state the rough crossover and say it must be measured on the actual matrix.
- ELL's argument: fixed row length in column-major layout makes every access perfectly coalesced, at the cost of padding — excellent for near-uniform row lengths, catastrophic for power-law ones. That is exactly what HYB fixes.
- `:::warning[...]` that SpMV performance is a property of the *matrix*, not just the kernel; benchmark on real matrices (e.g. from the SuiteSparse collection), never on a synthetic uniform one.
- cuSPARSE comparison via `cusparseSpMV`, linking [cuFFT, cuRAND, cuSPARSE, cuSOLVER](../08-libraries-and-ecosystem/math-libraries.md).

See also: `../08-libraries-and-ecosystem/math-libraries.md`, `../07-kernel-optimization/reducing-divergence.md`, `../05-execution-and-synchronization/warp-level-primitives.md`, `../readme.md`.

- [ ] **Step 3: Write `softmax-and-layernorm.md`**

Sections beyond the standard shape: `## Naive softmax and why it overflows`, `## The stable two-pass form`, `## Online (single-pass) softmax`, `## LayerNorm with Welford`, `## Fusing with neighbours`.

Requirements:
- The overflow problem first: `exp(x)` overflows FP32 above ≈88, so the naive form fails on real logits. The fix — subtract the row max — is mathematically identity and numerically essential.
- The two-pass kernel using `blockReduceSum` (and a max reduction built the same way) for one row per block.
- Online softmax derived: keep a running max `m` and running sum `d`; when a larger max appears, rescale the accumulated sum by `exp(m_old − m_new)`. Give the update rule explicitly — it is the exact mechanism FlashAttention depends on:
  ```cpp showLineNumbers
  // Online softmax accumulation over one row, per thread then reduced.
  float m = -INFINITY;    // running max
  float d = 0.0f;         // running sum of exp(x - m)
  for (int i = tid; i < n; i += blockDim.x) {
      const float x = row[i];
      const float m_new = fmaxf(m, x);
      d = d * __expf(m - m_new) + __expf(x - m_new);
      m = m_new;
  }
  // ... block-reduce (m, d) pairs with the same rescaling rule ...
  ```
- LayerNorm with single-pass Welford: the running mean/M2 update and the parallel merge formula for combining two partial (count, mean, M2) triples. Say why Welford is preferred over the naive `E[x²] − E[x]²` (catastrophic cancellation).
- Fusion: these ops are bandwidth-bound, so fusing the preceding bias/residual add saves a full pass over the tensor. Link [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) and [Triton](../08-libraries-and-ecosystem/triton.md), noting the Triton softmax on that page is the same algorithm in a different language.

See also: `flash-attention.md`, `parallel-reduction.md`, `../08-libraries-and-ecosystem/triton.md`, `../07-kernel-optimization/kernel-fusion-and-launch-overhead.md`, `../readme.md`.

- [ ] **Step 4: Write `flash-attention.md`**

The section's closing page. It should read as the payoff: every idea from folders 04, 05, and 07 appears in one real kernel.

Sections beyond the standard shape: `## The memory problem`, `## Tiling attention`, `## Online softmax makes it possible`, `## The backward pass and recomputation`, `## How the real kernels map to hardware`, `## What to actually use`.

Requirements:
- State the problem quantitatively: standard attention materializes an `N × N` score matrix, so memory is `O(N²)` and — more importantly — the kernel reads and writes that matrix to HBM several times. For long sequences the HBM traffic, not the FLOPs, is the cost.
- The insight: attention is not memory-bound because of the matmuls; it is memory-bound because of the intermediate. Tiling over key/value blocks keeps the intermediate in SRAM and never writes it to HBM.
- A Mermaid diagram of the tiled loop (outer over query blocks, inner over key/value blocks) with quoted labels.
- The algorithm in pseudocode-free `cpp`-commented structure: for each query tile, loop over key/value tiles computing `S = QK^T`, updating the running max and sum with the online-softmax rule from [Softmax and LayerNorm Kernels](./softmax-and-layernorm.md), and rescaling the accumulated output by `exp(m_old − m_new)`. Reference that page for the update rule rather than re-deriving it.
- Backward pass: storing only the row statistics `(m, d)` and recomputing `S` in the backward pass trades FLOPs for memory — and wins because the kernel was never FLOP-bound.
- `## How the real kernels map to hardware` ties the section together explicitly, one sentence each: shared-memory tiling ([Shared Memory Tiling](../07-kernel-optimization/shared-memory-tiling.md)), `wmma`/`wgmma` on tensor cores ([Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md)), `memcpy_async`/TMA pipelining ([Software Pipelining](../07-kernel-optimization/software-pipelining.md)), warp specialization on Hopper, and online softmax as the algorithmic enabler.
- `:::tip[...]` — use the reference implementations (FlashAttention-2/3, or the fused kernels in PyTorch's `scaled_dot_product_attention`). This page explains why they are fast, not how to replace them.

See also: `softmax-and-layernorm.md`, `matrix-multiply-tensor-cores.md`, `../07-kernel-optimization/software-pipelining.md`, `../08-libraries-and-ecosystem/cutlass.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/13-applied-kernels-and-patterns
git commit -m "docs: applied kernels, part 3"
```
Expected: build exits 0.

---

### Task 4: The outward cross-link pass

The spec requires six links from the new section into existing sections. Five were placed by earlier plans; this task adds the last one and verifies all six.

**Files:**
- Modify: `docs/gpu-computing/07-kernel-optimization/programming-tensor-cores.md`

**Interfaces:**
- Consumes: everything.
- Produces: the completed cross-link set. **Reciprocal links back from the ML/CS/programming pages are explicitly out of scope** (spec) — do not add them.

- [ ] **Step 1: Add the missing link**

In `docs/gpu-computing/07-kernel-optimization/programming-tensor-cores.md`, in the precision section, add a sentence and a `## See also` bullet pointing at the ML section's treatment of mixed precision:

```md
- [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) — the training-side view: autocast, loss scaling, and which layers stay in FP32.
```

Keep the existing bullets; if that pushes the list past five, drop the least useful one so the list stays at 3–5.

- [ ] **Step 2: Verify all six required cross-links exist**

Run:
```bash
grep -rn "machine-learning/02-deep-learning/gpu-training-and-mixed-precision" docs/gpu-computing/
grep -rn "machine-learning/02-deep-learning/distributed-training" docs/gpu-computing/
grep -rn "computer-science/memory-hierarchy" docs/gpu-computing/
grep -rn "computer-science/cpu-architecture" docs/gpu-computing/
grep -rn "programming/cmake" docs/gpu-computing/
grep -rn "programming/cpp" docs/gpu-computing/
```

Expected, per the spec:
1. `gpu-training-and-mixed-precision` — hits in **both** `07-kernel-optimization/` and `12-npu-and-inference-accelerators/quantization-for-accelerators.md`.
2. `distributed-training` — a hit in `10-multi-gpu-and-scaling/parallelism-strategies.md`.
3. `computer-science/memory-hierarchy` — a hit in `02-gpu-hardware-architecture/cache-hierarchy.md`.
4. `computer-science/cpu-architecture` — a hit in `00-overview/cpu-vs-gpu-vs-npu.md`.
5. `programming/cmake` — a hit in `09-tooling-profiling-and-debugging/building-cuda-with-cmake.md`.
6. `programming/cpp` — a hit in `03-cuda-programming-model/function-qualifiers.md`.

Any missing hit means the earlier plan's page skipped its required link. Add it to the named page now, in prose **and** in `## See also`.

- [ ] **Step 3: Verify the link targets resolve**

Run: `npm run build`
Expected: exits 0. `onBrokenLinks: "throw"` means any bad relative path fails here. Confirm the four target files exist if the build complains:
```bash
ls docs/machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md \
   docs/machine-learning/02-deep-learning/distributed-training.md \
   docs/computer-science/memory-hierarchy/cpu-caches.md \
   docs/computer-science/cpu-architecture/superscalar-and-out-of-order-execution.md \
   docs/programming/cmake/readme.md \
   docs/programming/cpp/readme.md
```

- [ ] **Step 4: Commit**

```bash
npm run format && npm run lint
git add docs/gpu-computing
git commit -m "docs: complete gpu section cross-links"
```

---

### Task 5: Final audit

Nothing here writes new content. Each step is a check with a defined expected result; fix anything that fails, then re-run the step.

**Files:** none, unless a check fails.

- [ ] **Step 1: File counts**

Run:
```bash
find docs/gpu-computing -name '*.md' | wc -l          # expect 129
find docs/gpu-computing -name '_category_.json' | wc -l   # expect 14
```

- [ ] **Step 2: No stubs left**

Run: `grep -rn "Stub — filled in by" docs/gpu-computing/`
Expected: no output. Any hit is a page a plan skipped.

- [ ] **Step 3: Every page ends with `## See also`**

Run:
```bash
for f in $(find docs/gpu-computing -name '*.md' ! -name 'readme.md'); do
  grep -q '^## See also' "$f" || echo "MISSING See also: $f"
done
```
Expected: no output. (`readme.md` is exempt — its sections table serves that role.)

- [ ] **Step 4: Single `CUDA_CHECK` definition**

Run: `grep -rn "define CUDA_CHECK" docs/gpu-computing/`
Expected: exactly one hit, in `06-cuda-runtime-and-apis/error-handling.md`.

- [ ] **Step 5: Python confined to its five pages**

Run: `grep -rln '```python' docs/gpu-computing/`
Expected: exactly five files — `03-cuda-programming-model/installing-the-cuda-toolkit.md` plus the four Python pages in `08-libraries-and-ecosystem/`.

- [ ] **Step 6: No removed warp intrinsics**

Run: `grep -rn "__shfl_down(\|__shfl_up(\|__shfl_xor(\|__ballot(\|__any(\|__all(" docs/gpu-computing/`
Expected: hits **only** inside blocks explicitly labelled as broken historical examples (`05-execution-and-synchronization/independent-thread-scheduling.md`, and `11-portable-and-vendor-neutral/hip-and-rocm.md` where `__ballot` is HIP's own 64-bit intrinsic). Anywhere else, replace with the `_sync` variant.

- [ ] **Step 7: No CUDA code fence mislabelled**

Run: `grep -rn '```cuda' docs/gpu-computing/`
Expected: no output. There is no Prism grammar for CUDA; every CUDA fence is ` ```cpp `.

- [ ] **Step 8: Image manifest is complete**

Run:
```bash
find static/img/gpu -type f ! -name 'SOURCES.md' -printf '%P\n' | sort
grep -o '`[^`]*\.png`' static/img/gpu/SOURCES.md | tr -d '`' | sort
```
Expected: the two lists match. Every downloaded figure has a manifest row, and no row names a missing file.

- [ ] **Step 9: No image reference carries the baseUrl prefix**

Run: `grep -rn '](/img/gpu' docs/gpu-computing/` and check every match's source path does **not** also carry the site's `baseUrl` segment ahead of `/img/gpu`.
Expected: every reference reads `/img/gpu/...` with nothing before it. Docusaurus resolves a root-absolute Markdown image path against `static/` and prepends `baseUrl` itself, so a source path that already includes the `baseUrl` segment resolves to a nonexistent directory under `static/` and 404s on the deployed site.

- [ ] **Step 10: Full build and lint**

Run: `npm run clear && npm run build && npm run lint`
Expected: both exit 0. `npm run clear` first, so the build does not read a stale `.docusaurus` cache.

- [ ] **Step 11: Visual check**

Run: `npm run serve`, then open:
- `http://localhost:3000/knowledge-base/docs/gpu-computing/readme` — sidebar shows 14 categories in order, `Overview` first.
- One page per folder, spot-checking that Mermaid diagrams render (not raw text) and code blocks are highlighted.
- `http://localhost:3000/knowledge-base/docs/tags/gpu` — the tag page lists the section's pages.

Stop the server.

- [ ] **Step 12: Commit any fixes**

If steps 1–11 required changes:
```bash
npm run format
git add -A
git commit -m "fix: gpu section audit corrections"
```
If nothing changed, commit nothing.

---

## Plan 6 completion criteria

- 12 applied-kernel pages written; the section is 129 Markdown files with no stubs remaining.
- All twelve audit checks in Task 5 pass.
- All six spec-required outward cross-links exist and resolve.
- `npm run build` and `npm run lint` exit 0 from a cleared cache.

## Known deviations from the spec, and why

Recorded here so a reviewer comparing plan to spec is not surprised:

1. **`error-handling.md`, not `error-handling-and-checking.md`.** The spec's *Code* section and its page-by-page outline disagree; the outline was followed.
2. **The full 129-file skeleton is created in plan 1, task 1**, rather than folders being written strictly in numeric order with a final forward-reference pass. The spec's staged approach exists to keep `onBrokenLinks: "throw"` satisfied; creating all stubs up front satisfies it more strongly, since every link target exists from the first commit and no forward-reference pass is needed.
3. **No `<Icon icon="lucide:..." />` in `## See also` bullets.** The boost/cmake sections use them, but the icon set is a hand-curated allowlist in `scripts/gen-icons.mjs` and an unlisted name renders empty. This section follows the `docs/machine-learning/` convention of plain link bullets, which requires no script change. The spec specifies the *structure* of `## See also`, not its decoration.
4. **The footer's "Docs" column is not updated** to include the new section. The spec lists exactly four files changing outside `docs/`, and the footer is not among them. Adding a sixth footer entry is a reasonable follow-up but is out of this plan's scope.
