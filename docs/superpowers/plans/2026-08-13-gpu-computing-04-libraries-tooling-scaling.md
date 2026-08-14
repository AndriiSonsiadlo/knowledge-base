# GPU & Accelerators — Plan 4: Libraries, Tooling, and Multi-GPU

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the 25 pages of `08-libraries-and-ecosystem/`, `09-tooling-profiling-and-debugging/`, and `10-multi-gpu-and-scaling/` — what you actually use in production, how you measure it, and how you scale it past one device.

**Architecture:** Every file already exists as a stub with correct frontmatter (plan 1, task 1). This plan fills in bodies only, so `npm run build` (`onBrokenLinks: "throw"`) passes after every task.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism `cpp`/`python`/`bash`/`cmake`/`text` fences, Biome, Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Prerequisite:** Plans 1–3 complete. Verify: `grep -rn "define CUDA_CHECK" docs/gpu-computing/` returns exactly one hit, in `06-cuda-runtime-and-apis/error-handling.md`.

**Plan series:** plan 4 of 6.

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

Only `:::info[...]`, `:::note[...]`, `:::tip[...]`, `:::warning[...]`, with the meanings used throughout the section.

### Code fences

- CUDA C++ in ` ```cpp `; PTX/SASS in ` ```text `; also `bash`, `cmake`, `json`.
- **`python` is permitted only in folder 08** — specifically `cuda-python-and-cupy.md`, `numba-cuda.md`, `pytorch-cuda-extensions.md`, and `triton.md`. Folders 09 and 10 contain no Python.
- `showLineNumbers` on fences longer than ~5 lines; `title="filename"` for standalone files.
- **Never redefine `CUDA_CHECK`** — it is defined once in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md). Use it freely.
- Library examples must use the library's real API: correct handle types, correct enum names, correct argument order. A snippet that would not compile is a defect.

### MDX hazards

Outside code fences and inline backticks, always backtick: `__global__`, `__device__`, `__shared__`, `<<<grid, block>>>`, `<T>`, `thrust::device_vector<float>`, and any bare `{` or `}`.

### Diagrams

Mermaid for structural content. **Quote every edge label:** `A -->|"label (with parens)"| B`.

### Performance claims

Every performance number states the hardware generation it applies to. If you cannot attribute a number, describe the direction and mechanism instead of inventing one.

### Verification gate — every task

1. `npm run build` exits 0.
2. `npm run format` then `npm run lint` — both exit 0.
3. Commit. One-line message, `<type>: <what>`. **Never** add a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

---

## File Structure

```
docs/gpu-computing/
├── 08-libraries-and-ecosystem/       12 pages  Task 1 (1-4), Task 2 (5-8), Task 3 (9-12)
├── 09-tooling-profiling-and-debugging/ 7 pages  Task 4 (1-4), Task 5 (5-7)
└── 10-multi-gpu-and-scaling/          6 pages  Task 6

static/img/gpu/
├── 09-tooling-profiling-and-debugging/          Task 7
└── SOURCES.md                                   Task 7 (append rows)
```

---

### Task 1: `08-libraries-and-ecosystem`, pages 1–4

**Files:**
- Modify: `choosing-a-library.md`, `cublas.md`, `cudnn.md`, `math-libraries.md`

**Interfaces:**
- Consumes: `07-kernel-optimization/programming-tensor-cores.md` (why library GEMM wins).
- Produces: the cuBLAS column-major convention explained once, reused by `cutlass.md` and `13-applied-kernels-and-patterns/matrix-multiply.md`.

- [ ] **Step 1: Write `choosing-a-library.md`**

Sections: `## The default answer is a library`, `## What a library gives you that you cannot easily rebuild`, `## When a hand-written kernel wins`, `## The decision table`, `## Layering`.

Requirements:
- Open with the honest framing: NVIDIA's libraries are tuned per architecture by people with access to the SASS scheduler and the hardware team; a hand-written GEMM reaching 60% of cuBLAS is a good hand-written GEMM.
- The three cases where a custom kernel genuinely wins, each with an example: an operation with no library equivalent; a fusion the library cannot express (elementwise chain around a reduction); a shape or dtype the library handles badly (very small or very skewed matrices).
- A decision table `| Need | Reach for | Why |` covering dense linear algebra (cuBLAS/cuBLASLt), convolution and attention (cuDNN), custom GEMM shapes and epilogues (CUTLASS), sort/scan/reduce (CUB, Thrust), FFT (cuFFT), sparse (cuSPARSE), random numbers (cuRAND), collectives (NCCL), and "fused elementwise around a reduction" (Triton).
- `:::tip[...]` — the composition rule: use CUB inside your own kernel, Thrust for host-level algorithm calls, CUTLASS when you need to own the GEMM, cuBLAS when you do not.

See also: `cublas.md`, `cub.md`, `cutlass.md`, `triton.md`, `../readme.md`.

- [ ] **Step 2: Write `cublas.md`**

Sections: `## Handles and streams`, `## Column-major, and what to do about it`, `## GEMM`, `## Batched and strided-batched`, `## cuBLASLt`, `## Math modes and TF32`.

Requirements:
- The column-major problem addressed head-on, since it is the single biggest source of cuBLAS bugs, with the standard trick spelled out: to compute a row-major `C = A × B`, call cuBLAS as `C^T = B^T × A^T` by swapping the `A` and `B` arguments and the corresponding dimensions. Show the exact call.
- A complete SGEMM call with every argument named in a comment:
  ```cpp showLineNumbers
  cublasHandle_t h;
  CUBLAS_CHECK(cublasCreate(&h));
  CUBLAS_CHECK(cublasSetStream(h, stream));

  const float alpha = 1.0f, beta = 0.0f;
  // Row-major C(MxN) = A(MxK) * B(KxN), expressed column-major as C^T = B^T * A^T
  CUBLAS_CHECK(cublasSgemm(h,
      CUBLAS_OP_N, CUBLAS_OP_N,
      N, M, K,              // m, n, k in the transposed formulation
      &alpha,
      d_B, N,               // B^T with leading dimension N
      d_A, K,               // A^T with leading dimension K
      &beta,
      d_C, N));             // C^T with leading dimension N
  ```
  `:::note[...]` that `CUBLAS_CHECK` is a cuBLAS-specific analogue of `CUDA_CHECK`; define it inline in this snippet's surrounding prose as a one-liner testing against `CUBLAS_STATUS_SUCCESS`, and say it is local to this page.
- Batched vs strided-batched: the array-of-pointers form versus the constant-stride form, and that the strided form is faster when it applies because it avoids the pointer array.
- `cublasLt` introduced as the layer that exposes epilogues (bias, ReLU, GELU) and layout/algorithm selection — the reason it exists is fusion.
- Math modes: `cublasSetMathMode` with `CUBLAS_TF32_TENSOR_OP_MATH`, and `:::warning[...]` that TF32 silently reduces mantissa precision; it is on by default in some framework builds, which is a common source of "the numbers changed" reports.

See also: `cutlass.md`, `choosing-a-library.md`, `../07-kernel-optimization/programming-tensor-cores.md`, `../13-applied-kernels-and-patterns/matrix-multiply.md`, `../readme.md`.

- [ ] **Step 3: Write `cudnn.md`**

Sections: `## What cuDNN covers`, `## The descriptor model`, `## Algorithm selection and workspaces`, `## The graph API`, `## Fused operations`, `## Where it sits under a framework`.

Requirements:
- Explain the descriptor model as the API's organizing idea: tensors, filters, and operations are described declaratively, then a plan is chosen for the described problem — which is what allows algorithm autotuning.
- Algorithm selection concretely: `cudnnFindConvolutionForwardAlgorithm` (empirical, benchmarks candidates) versus `cudnnGetConvolutionForwardAlgorithm_v7` (heuristic), and the workspace buffer each algorithm requires. `:::tip[...]` that this is exactly what `torch.backends.cudnn.benchmark = True` toggles, and why it costs time on the first iteration of each new shape.
- The graph API (cuDNN 8+) presented as the current direction: you describe an operation graph and cuDNN picks a fused engine; it is how conv+bias+activation becomes one kernel.
- `:::note[...]` that most readers meet cuDNN through PyTorch or TensorFlow and never call it directly; the value of knowing the model is diagnosing shape-dependent performance cliffs and non-determinism.
- `:::warning[...]` on non-determinism: some algorithms use atomics and are not bitwise reproducible; deterministic mode trades speed for reproducibility.

See also: `cublas.md`, `../12-npu-and-inference-accelerators/tensorrt.md`, `../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md`, `../readme.md`.

- [ ] **Step 4: Write `math-libraries.md`**

Sections: `## cuFFT`, `## cuRAND`, `## cuSPARSE`, `## cuSOLVER`, `## Shared conventions`.

Requirements:
- One `##` per library, each with: what it covers, its handle/plan lifecycle, one representative `cpp` snippet, and one pitfall.
  - **cuFFT** — plans are expensive and reusable; `cufftPlanMany` for batches; R2C output is `N/2 + 1` complex values, and forgetting the normalization factor on the inverse transform is the classic bug.
  - **cuRAND** — the host API (bulk generation into a device buffer) versus the device API (`curand_init` + per-thread state inside a kernel); `:::warning[...]` that `curand_init` with a per-thread sequence number is slow and should be hoisted out of hot kernels, and that seeding every thread identically produces correlated streams.
  - **cuSPARSE** — the generic API (`cusparseSpMV` with `cusparseCreateCsr`/`cusparseCreateDnVec`), the CSR format described in one paragraph, and the buffer-size-then-execute two-call protocol.
  - **cuSOLVER** — dense (`cusolverDn`) and sparse (`cusolverSp`) handles, the workspace query pattern, and `devInfo` as the per-call status output that must be checked on the host.
- A closing `## Shared conventions` section noting what all four have in common: a handle bound to a stream, a workspace query followed by an execute call, and column-major dense layouts inherited from BLAS/LAPACK.

See also: `cublas.md`, `../13-applied-kernels-and-patterns/sparse-matrix-vector.md`, `choosing-a-library.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/08-libraries-and-ecosystem
git commit -m "docs: cuda libraries, part 1"
```
Expected: build exits 0.

---

### Task 2: `08-libraries-and-ecosystem`, pages 5–8

**Files:**
- Modify: `thrust.md`, `cub.md`, `cutlass.md`, `nccl.md`

**Interfaces:**
- Consumes: `05-execution-and-synchronization/reductions-and-scans.md` (`blockReduceSum`, as the thing CUB replaces).
- Produces: the NCCL collective vocabulary reused by `10-multi-gpu-and-scaling/collectives-with-nccl.md` — that page covers algorithms and overlap; this one covers the API.

- [ ] **Step 1: Write `thrust.md`**

Sections: `## STL for the device`, `## Containers`, `## Algorithms and execution policies`, `## Fancy iterators`, `## Custom functors`, `## Where Thrust stops`.

Requirements:
- A short complete program: fill a `thrust::device_vector<float>`, `thrust::transform` it, `thrust::reduce` it, print the result — showing that no explicit `cudaMalloc` or `cudaMemcpy` appears.
- Execution policies (`thrust::device`, `thrust::host`, `thrust::cuda::par.on(stream)`) with the point that the stream-bound policy is how you keep Thrust from implicitly synchronizing.
- Fancy iterators with one worked example — `counting_iterator` + `transform_iterator` computing a reduction without materializing the intermediate array, which is Thrust's real superpower.
- `:::warning[...]` that `device_vector` construction zero-initializes and allocation is synchronous, so building vectors in a loop is a common hidden cost.
- `## Where Thrust stops`: no control over launch configuration, no fusion across separate algorithm calls (except via iterators), and no in-kernel use — that is CUB's job.

See also: `cub.md`, `choosing-a-library.md`, `../05-execution-and-synchronization/reductions-and-scans.md`, `../readme.md`.

- [ ] **Step 2: Write `cub.md`**

Sections: `## Three levels`, `## Device-level primitives`, `## The temp-storage protocol`, `## Block-level primitives`, `## Warp-level primitives`, `## Why CUB beats a hand-rolled reduction`.

Requirements:
- The three levels table: `cub::Device*` (callable from the host, whole-array), `cub::Block*` (inside a kernel, block-wide), `cub::Warp*` (inside a kernel, warp-wide).
- The two-call temp-storage protocol shown exactly, because getting it wrong is the standard CUB bug:
  ```cpp showLineNumbers
  void* d_temp = nullptr;
  size_t tempBytes = 0;
  // First call: query the size. d_temp must be nullptr.
  CUDA_CHECK(cub::DeviceReduce::Sum(d_temp, tempBytes, d_in, d_out, n, stream));
  CUDA_CHECK(cudaMallocAsync(&d_temp, tempBytes, stream));
  // Second call: do the work.
  CUDA_CHECK(cub::DeviceReduce::Sum(d_temp, tempBytes, d_in, d_out, n, stream));
  CUDA_CHECK(cudaFreeAsync(d_temp, stream));
  ```
- `cub::BlockReduce` inside a kernel, shown against `blockReduceSum` from [Reductions and Scans](../05-execution-and-synchronization/reductions-and-scans.md) — same result, but CUB picks the algorithm per architecture and handles non-power-of-two block sizes.
- The reason CUB wins, stated mechanically rather than as a claim: it is templated on block size and architecture, so the tile size, the number of items per thread, and the algorithm (raking versus warp-shuffle) are chosen at compile time for the target.
- `:::note[...]` that CUB ships with the CUDA Toolkit and is the implementation under most of Thrust's algorithms.

See also: `thrust.md`, `../05-execution-and-synchronization/reductions-and-scans.md`, `../13-applied-kernels-and-patterns/parallel-reduction.md`, `../13-applied-kernels-and-patterns/sorting-on-the-gpu.md`, `../readme.md`.

- [ ] **Step 3: Write `cutlass.md`**

Sections: `## What CUTLASS is for`, `## The tile hierarchy`, `## Epilogues`, `## CuTe and layouts`, `## CUTLASS 3.x on Hopper`, `## When to reach for it`.

Requirements:
- Position it precisely: CUTLASS is a template library that lets you *build* a GEMM with cuBLAS-class performance but your own shapes, dtypes, and fused epilogue — it is what you use when cuBLAS is fast but not fusable.
- The tile hierarchy as a Mermaid tree with quoted labels: problem → threadblock tile → warp tile → instruction (MMA) tile, and the statement that choosing these three shapes *is* the tuning problem.
- Epilogues explained as the payoff: bias + activation + scaling fused into the GEMM's output stage, avoiding a second pass over the result.
- CuTe introduced honestly: a layout algebra (shape and stride as composable objects) that replaces CUTLASS 2.x's hand-written iterators, with a one-paragraph explanation of `Layout = Shape : Stride` and why it makes swizzling and TMA descriptors expressible.
- `:::note[Requires CC 9.0+]` on the CUTLASS 3.x Hopper path — warp-specialized kernels with TMA and `wgmma`, referencing [Software Pipelining](../07-kernel-optimization/software-pipelining.md) and [Asynchronous Data Movement](../04-cuda-memory-model/asynchronous-data-movement.md).
- `:::warning[...]` on the cost: long compile times, heavy template errors, and a steep learning curve. Do not adopt it to save a few percent.

See also: `cublas.md`, `../07-kernel-optimization/programming-tensor-cores.md`, `../07-kernel-optimization/software-pipelining.md`, `../13-applied-kernels-and-patterns/matrix-multiply-tensor-cores.md`, `../readme.md`.

- [ ] **Step 4: Write `nccl.md`**

Sections: `## What NCCL provides`, `## Communicators`, `## The collectives`, `## Stream integration`, `## Topology awareness`, `## Grouped calls`.

Requirements:
- The collectives table: `ncclAllReduce`, `ncclBroadcast`, `ncclReduce`, `ncclAllGather`, `ncclReduceScatter`, `ncclSend`/`ncclRecv` — each with its data movement described in one line.
- A Mermaid diagram showing all-reduce as reduce-scatter followed by all-gather, with quoted labels.
- Communicator setup shown for the one-process-per-GPU case, which is the recommended topology:
  ```cpp showLineNumbers
  ncclUniqueId id;
  if (rank == 0) NCCL_CHECK(ncclGetUniqueId(&id));
  MPI_Bcast(&id, sizeof(id), MPI_BYTE, 0, MPI_COMM_WORLD);

  CUDA_CHECK(cudaSetDevice(localRank));
  ncclComm_t comm;
  NCCL_CHECK(ncclCommInitRank(&comm, worldSize, id, rank));

  NCCL_CHECK(ncclAllReduce(d_grad, d_grad, count, ncclFloat, ncclSum, comm, stream));
  CUDA_CHECK(cudaStreamSynchronize(stream));
  ```
  Note in prose that `NCCL_CHECK` is this page's local analogue of `CUDA_CHECK`, testing against `ncclSuccess`.
- Stream integration as the key operational fact: NCCL calls are enqueued on a CUDA stream, so communication genuinely overlaps compute if you put them on different streams and express the dependency with events.
- `ncclGroupStart`/`ncclGroupEnd` for batching, and `:::warning[...]` that every rank must call the same collectives in the same order — a mismatch hangs rather than errors.
- `:::tip[...]` — `NCCL_DEBUG=INFO` prints the chosen topology and algorithm; it is the first thing to check when bandwidth is below expectation.

See also: `../10-multi-gpu-and-scaling/collectives-with-nccl.md`, `../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md`, `../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/08-libraries-and-ecosystem
git commit -m "docs: cuda libraries, part 2"
```
Expected: build exits 0.

---

### Task 3: `08-libraries-and-ecosystem`, pages 9–12 (the Python pages)

**Files:**
- Modify: `cuda-python-and-cupy.md`, `numba-cuda.md`, `pytorch-cuda-extensions.md`, `triton.md`

**Interfaces:**
- Consumes: `03-cuda-programming-model/thread-indexing.md` (the indexing formulas, restated in Python).
- Produces: nothing later plans depend on by name. **These four pages are the only place in the section where `python` fences appear** (besides `03-cuda-programming-model/installing-the-cuda-toolkit.md`).

- [ ] **Step 1: Write `cuda-python-and-cupy.md`**

Sections: `## Two different things`, `## CuPy as a NumPy replacement`, `## Writing kernels from Python`, `## Memory pools`, `## Streams`, `## DLPack interop`.

Requirements:
- Separate the two clearly at the top: `cuda-python` (`cuda.bindings`, `cuda.core`) is NVIDIA's official low-level binding to the driver/runtime APIs; CuPy is a third-party NumPy-compatible array library built on them. Most users want CuPy.
- The drop-in demonstration:
  ```python
  import cupy as cp

  x = cp.random.rand(1 << 20, dtype=cp.float32)
  y = cp.random.rand(1 << 20, dtype=cp.float32)
  z = 2.0 * x + y                    # runs on the GPU
  print(float(cp.sum(z)))            # implicit device-to-host sync
  ```
  `:::warning[...]` that any conversion to a Python scalar or a NumPy array synchronizes — a `print` inside a timing loop destroys the measurement.
- `cp.RawKernel` (raw CUDA C++ source compiled at runtime) and `cp.ElementwiseKernel` (CuPy generates the boilerplate), one snippet each.
- Memory pools: CuPy pools device allocations by default, so `cupy.get_default_memory_pool().used_bytes()` and `free_all_blocks()` are how you reason about memory — and why `nvidia-smi` shows more memory used than your arrays occupy.
- DLPack: `cp.from_dlpack(torch_tensor)` and back, exchanging device arrays with PyTorch with no copy.

See also: `numba-cuda.md`, `pytorch-cuda-extensions.md`, `../06-cuda-runtime-and-apis/runtime-vs-driver-api.md`, `../readme.md`.

- [ ] **Step 2: Write `numba-cuda.md`**

Sections: `## Kernels in Python`, `## Indexing`, `## Memory management`, `## Shared memory and atomics`, `## What Numba cannot do`.

Requirements:
- A complete SAXPY, matching the CUDA C++ one from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) so the mapping is obvious:
  ```python
  from numba import cuda
  import numpy as np

  @cuda.jit
  def saxpy(a, x, y):
      i = cuda.grid(1)
      if i < x.size:
          y[i] = a * x[i] + y[i]

  n = 1 << 20
  x = cuda.to_device(np.ones(n, dtype=np.float32))
  y = cuda.to_device(np.full(n, 2.0, dtype=np.float32))

  threads = 256
  blocks = (n + threads - 1) // threads
  saxpy[blocks, threads](2.0, x, y)
  print(y.copy_to_host()[0])          # 4.0
  ```
- `cuda.grid(1)` / `cuda.grid(2)` as the wrapper over the index arithmetic, and `cuda.gridsize(1)` for grid-stride loops.
- `cuda.shared.array(shape, dtype)` (shape must be a compile-time constant), `cuda.syncthreads()`, and `cuda.atomic.add`.
- The limits, stated plainly: a restricted Python subset, no classes, no dynamic allocation, weaker control over launch bounds and registers, and a real performance gap on complex kernels. `:::tip[...]` — Numba is excellent for prototyping and for kernels that live inside an otherwise-Python pipeline; port to C++ or Triton when it becomes the bottleneck.

See also: `cuda-python-and-cupy.md`, `triton.md`, `../03-cuda-programming-model/thread-indexing.md`, `../readme.md`.

- [ ] **Step 3: Write `pytorch-cuda-extensions.md`**

Sections: `## Why write an extension`, `## `load_inline` for iteration`, `## setuptools for shipping`, `## Tensor accessors`, `## Autograd integration`, `## Stream semantics`.

Requirements:
- Motivate it precisely: a custom op that PyTorch cannot express efficiently as a composition — a fused kernel, an irregular gather, a novel attention variant.
- The `load_inline` path shown end to end (Python string containing CUDA C++, compiled on first call), because it is the fastest way to iterate.
- The accessor pattern with the reason: `packed_accessor32<float, 2, torch::RestrictPtrTraits>()` gives bounds-aware, strided indexing inside the kernel and encodes `__restrict__`, which raw pointers lose.
- `torch::autograd::Function` with `forward` and `backward` static methods, so the custom op participates in autograd.
- Stream semantics as the correctness trap: launch on `c10::cuda::getCurrentCUDAStream()`, never on the null stream, or the op will race with the rest of the model. `:::warning[...]` on exactly this.
- `:::tip[...]` — check whether `torch.compile` already fuses the pattern before writing an extension; see [Triton](./triton.md).

See also: `triton.md`, `cuda-python-and-cupy.md`, `../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md`, `../readme.md`.

- [ ] **Step 4: Write `triton.md`**

Sections: `## A block-level programming model`, `## Loads, stores, and masks`, `## A fused softmax`, `## Autotuning`, `## How it compares to raw CUDA`, `## Where it fits`.

Requirements:
- The model's central idea stated first: you write code for a *block* of elements, not a thread. Triton owns the thread mapping, the vectorization, and the shared-memory staging; you own the tiling and the algorithm.
- The fused softmax kernel, complete — it is the canonical example and shows masking clearly:
  ```python
  import triton
  import triton.language as tl

  @triton.jit
  def softmax_kernel(out_ptr, in_ptr, in_stride, out_stride,
                     n_cols, BLOCK: tl.constexpr):
      row = tl.program_id(0)
      cols = tl.arange(0, BLOCK)
      mask = cols < n_cols

      x = tl.load(in_ptr + row * in_stride + cols, mask=mask, other=-float("inf"))
      x = x - tl.max(x, axis=0)              # numerically stable
      num = tl.exp(x)
      y = num / tl.sum(num, axis=0)
      tl.store(out_ptr + row * out_stride + cols, y, mask=mask)
  ```
  Explain each part: `program_id` is the block index, `tl.arange` builds the in-block offsets, `mask` handles the ragged tail, and the whole row stays in registers/shared so it is read from DRAM once.
- `@triton.autotune` with a `configs` list over `BLOCK` and `num_warps`, and the note that autotuning runs on the first call per shape.
- An honest comparison table `| | Triton | CUDA C++ |` over: control granularity, boilerplate, tensor-core access, debugging tools, performance ceiling. Say plainly that Triton reaches near-cuBLAS on many fused ops and does not on tuned GEMM.
- `:::tip[...]` — `torch.compile` emits Triton, so reading generated Triton is a fast way to see what Inductor fused.

See also: `pytorch-cuda-extensions.md`, `../07-kernel-optimization/kernel-fusion-and-launch-overhead.md`, `../13-applied-kernels-and-patterns/softmax-and-layernorm.md`, `../12-npu-and-inference-accelerators/compiler-stacks.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/08-libraries-and-ecosystem
git commit -m "docs: cuda python ecosystem pages"
```
Expected: build exits 0.

- [ ] **Step 6: Verify the Python-fence rule**

Run: `grep -rln '```python' docs/gpu-computing/`
Expected: exactly five files — the four written in this task plus `03-cuda-programming-model/installing-the-cuda-toolkit.md`. If any other file appears, convert its snippet to `cpp` or remove it.

---

### Task 4: `09-tooling-profiling-and-debugging`, pages 1–4

**Files:**
- Modify: `building-cuda-with-cmake.md`, `nsight-systems.md`, `nsight-compute.md`, `cuda-gdb-and-sanitizers.md`

**Interfaces:**
- Consumes: `03-cuda-programming-model/separate-compilation-and-linking.md`, `02-gpu-hardware-architecture/compute-capability.md`.
- Produces: the metric names that `metrics-that-matter.md` (Task 5) explains one by one.

- [ ] **Step 1: Write `building-cuda-with-cmake.md`**

Sections: `## Enabling the CUDA language`, `## Architectures`, `## Separable compilation`, `## Linking CUDA libraries`, `## Host compiler flags`, `## A complete example`.

Requirements:
- The modern form, stated as the recommendation: `project(x LANGUAGES CXX CUDA)` and `CUDA_ARCHITECTURES`, not `find_package(CUDA)` (deprecated) and not manual `nvcc` invocation.
- A complete, working `CMakeLists.txt`:
  ```cmake showLineNumbers title="CMakeLists.txt"
  cmake_minimum_required(VERSION 3.24)
  project(gpuapp LANGUAGES CXX CUDA)

  add_executable(gpuapp src/main.cu src/kernels.cu)

  set_target_properties(gpuapp PROPERTIES
      CUDA_ARCHITECTURES "80;90"       # SASS for Ampere and Hopper
      CUDA_SEPARABLE_COMPILATION ON)   # only if you need cross-TU device calls

  target_compile_options(gpuapp PRIVATE
      $<$<COMPILE_LANGUAGE:CUDA>:--expt-relaxed-constexpr -lineinfo>)

  find_package(CUDAToolkit REQUIRED)
  target_link_libraries(gpuapp PRIVATE CUDA::cublas CUDA::cudart)
  ```
- Explain `CUDA_ARCHITECTURES` values: `80` means `sm_80` SASS; `80-real` SASS only; `80-virtual` PTX only; `native` for the build machine; `all-major` for a broad release build. Link [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md).
- `-lineinfo` called out specifically as the flag that makes Nsight Compute's source-level view work, at negligible cost.
- The `$<COMPILE_LANGUAGE:CUDA>` generator expression explained, since flags leaking into the host compiler is the standard mistake, and `-Xcompiler` for passing host flags through `nvcc`.
- Cross-link `../../programming/cmake/readme.md` for CMake itself.
- `:::note[...]` on `CUDA_SEPARABLE_COMPILATION` costing performance — see [Separate Compilation and Linking](../03-cuda-programming-model/separate-compilation-and-linking.md).

See also: `nsight-compute.md`, `../03-cuda-programming-model/separate-compilation-and-linking.md`, `../../programming/cmake/readme.md`, `../readme.md`.

- [ ] **Step 2: Write `nsight-systems.md`**

Sections: `## What it shows`, `## Capturing from the CLI`, `## Reading the timeline`, `## NVTX ranges`, `## What to look for`.

Requirements:
- Position it against Nsight Compute in one sentence at the top: Systems answers "where does the wall-clock time go across CPU, GPU, memory, and the network"; Compute answers "why is this one kernel slow". Start with Systems.
- The CLI capture, complete:
  ```bash
  nsys profile -t cuda,nvtx,osrt --stats=true -o report ./gpuapp
  nsys stats report.nsys-rep       # summary tables without opening the GUI
  ```
- NVTX ranges shown in `cpp`, since they are what turns an unreadable timeline into a readable one:
  ```cpp showLineNumbers
  #include <nvtx3/nvToolsExt.h>

  nvtxRangePushA("forward");
  forwardKernel<<<grid, block, 0, stream>>>(/* ... */);
  nvtxRangePop();
  ```
- A checklist of what to look for, as a table `| Timeline symptom | Likely cause | Where to go next |`: gaps between kernels (launch overhead or host bottleneck → [CUDA Graphs](../06-cuda-runtime-and-apis/cuda-graphs.md)); H2D/D2H not overlapping kernels (pageable memory or one stream → [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md)); a long single kernel (→ [Nsight Compute](./nsight-compute.md)); CPU thread pegged during GPU idle (input pipeline).
- `:::tip[...]` — profile a few representative iterations, not the whole run; a multi-gigabyte report is unusable.

See also: `nsight-compute.md`, `benchmarking-methodology.md`, `../06-cuda-runtime-and-apis/streams-and-concurrency.md`, `../readme.md`.

- [ ] **Step 3: Write `nsight-compute.md`**

Sections: `## Kernel-level profiling`, `## Capturing`, `## Speed of Light`, `## Memory Workload Analysis`, `## The roofline chart`, `## Source-level counters`, `## Section sets and cost`.

Requirements:
- The CLI, with the flags that matter:
  ```bash
  ncu --set full -k saxpy -c 3 -o profile ./gpuapp     # full sections, 3 launches
  ncu --set basic --target-processes all ./gpuapp      # cheap first pass
  ncu -i profile.ncu-rep --page details                # re-read without rerunning
  ```
- Explain Speed of Light as the first thing to read: two percentages (compute throughput and memory throughput relative to peak) that classify the kernel immediately, exactly the classification from [The Optimization Workflow](../07-kernel-optimization/the-optimization-workflow.md).
- Memory Workload Analysis described as a diagram of the memory path with measured traffic at each level (L1 ↔ L2 ↔ DRAM), and the specific thing to check: requests versus sectors per request, which is coalescing efficiency.
- Source-level counters: requires `-lineinfo`; shows stall reasons and memory traffic per source line, which is how you find the one line responsible.
- `:::warning[...]` on cost: profiling serializes and replays kernels, so a profiled run can be orders of magnitude slower and the wall-clock time in the report is not a benchmark. Use `--set basic` for a first pass, `-k` and `-c` to narrow.

See also: `metrics-that-matter.md`, `roofline-in-practice.md`, `../07-kernel-optimization/the-optimization-workflow.md`, `../readme.md`.

- [ ] **Step 4: Write `cuda-gdb-and-sanitizers.md`**

Sections: `## Compiling for debug`, `## cuda-gdb`, `## Compute Sanitizer`, `## memcheck`, `## racecheck`, `## initcheck and synccheck`, `## Reading a report`.

Requirements:
- Build flags: `-g -G` for full device debug (and `:::warning[...]` that `-G` disables device optimization, so timing under it is meaningless and some races disappear); `-lineinfo` alone for sanitizer reports with line numbers at near-full speed.
- cuda-gdb essentials in a `bash`/`text` block: `break kernel.cu:42`, `cuda thread (0,0,0) block (1,0,0)` to switch focus, `info cuda threads`, `p var`.
- The four sanitizer tools, one `##` each, with the invocation and what each catches:
  ```bash
  compute-sanitizer --tool memcheck   ./gpuapp   # out-of-bounds, misaligned access
  compute-sanitizer --tool racecheck  ./gpuapp   # shared-memory data races
  compute-sanitizer --tool initcheck  ./gpuapp   # reads of uninitialized device memory
  compute-sanitizer --tool synccheck  ./gpuapp   # divergent or illegal __syncthreads
  ```
- An annotated sample `memcheck` report in a ` ```text ` fence, showing how to read the offending thread/block and the source line.
- `:::tip[...]` — run `memcheck` and `racecheck` in CI on a small input. Both catch classes of bug that produce correct-looking output on your machine and wrong output on someone else's.

See also: `../06-cuda-runtime-and-apis/error-handling.md`, `../05-execution-and-synchronization/block-synchronization.md`, `../04-cuda-memory-model/distributed-shared-memory.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/09-tooling-profiling-and-debugging
git commit -m "docs: gpu tooling and debugging pages"
```
Expected: build exits 0.

---

### Task 5: `09-tooling-profiling-and-debugging`, pages 5–7

**Files:**
- Modify: `metrics-that-matter.md`, `roofline-in-practice.md`, `benchmarking-methodology.md`

**Interfaces:**
- Consumes: Task 4's Nsight material; `01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md`.
- Produces: the benchmarking checklist referenced by `13-applied-kernels-and-patterns/*` (every folder-13 page measures).

- [ ] **Step 1: Write `metrics-that-matter.md`**

Sections: `## The short list`, then one `##` per metric, then `## Metrics that mislead`.

Requirements:
- Cover exactly these, each with: the Nsight Compute metric name, what it measures, what value is good, and what to change if it is bad.
  - Achieved occupancy — `sm__warps_active.avg.pct_of_peak_sustained_active`
  - DRAM throughput — `dram__throughput.avg.pct_of_peak_sustained_elapsed`
  - Compute (SM) throughput — `sm__throughput.avg.pct_of_peak_sustained_elapsed`
  - L2 hit rate — `lts__t_sector_hit_rate.pct`
  - Global load efficiency — sectors per request from `l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum` ÷ `l1tex__t_requests_pipe_lsu_mem_global_op_ld.sum`
  - Shared-memory bank conflicts — `l1tex__data_bank_conflicts_pipe_lsu_mem_shared`
  - Warp stall reasons — `smsp__average_warps_issue_stalled_*`
  - Register spills — `local_load`/`local_store` traffic plus `-Xptxas -v` stack size
- `## Metrics that mislead` covers: theoretical occupancy quoted without achieved occupancy; instructions-per-cycle without knowing the limiter; and any percentage measured on a kernel too short to be sampled reliably.
- `:::tip[...]` — read Speed of Light first and let it choose which of these to look at; collecting everything on a big kernel is slow and rarely informative.

See also: `nsight-compute.md`, `roofline-in-practice.md`, `../01-parallel-computing-foundations/memory-bound-vs-compute-bound.md`, `../readme.md`.

- [ ] **Step 2: Write `roofline-in-practice.md`**

Sections: `## From counters to a point`, `## Getting the machine's roofs`, `## Placing the kernel`, `## Reading the position`, `## The hierarchical roofline`.

Requirements:
- The measurement recipe, step by step: FLOPs from `smsp__sass_thread_inst_executed_op_*_pred_on.sum` (fadd + fmul + 2 × ffma), bytes from `dram__bytes.sum`, arithmetic intensity as their ratio, achieved FLOP/s as FLOPs ÷ kernel duration.
- Getting the roofs: peak FLOP/s from the device spec, peak bandwidth measured (not quoted) with a streaming kernel — and say why measured is the right denominator.
- A table `| Where the point lands | What it means | Next move |`: under the diagonal (bandwidth-bound, below achievable) → improve coalescing/reuse; on the diagonal → raise arithmetic intensity by tiling or fusing; under the horizontal roof → improve instruction mix or use tensor cores; on the roof → stop.
- The hierarchical roofline explained: adding L1 and L2 roofs shows whether tiling actually moved traffic off DRAM, which is the question tiling is supposed to answer.
- `:::note[...]` that Nsight Compute's roofline chart does all of this automatically in `--set full`; the manual recipe matters when you need it in a script or on a platform without the GUI.

See also: `metrics-that-matter.md`, `../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `../readme.md`.

- [ ] **Step 3: Write `benchmarking-methodology.md`**

Sections: `## Warm-up`, `## Locking clocks`, `## Repetition and variance`, `## Timing correctly`, `## Defeating dead-code elimination`, `## Reporting honestly`, `## A checklist`.

Requirements:
- Each source of error gets its mechanism and its fix:
  - Warm-up — first launch pays context creation, JIT, and cold caches; discard at least the first few iterations.
  - Clocks — GPUs boost and then throttle thermally, so a long run is slower than a short one. `nvidia-smi -lgc <freq>` locks the SM clock; `nvidia-smi -q -d CLOCK` reports throttle reasons. `:::warning[...]` that unlocked-clock results are not comparable across runs or machines.
  - Repetition — report median and interquartile range, not a single number or a bare mean; a single outlier from a scheduler hiccup ruins a mean.
  - Timing — CUDA events around a loop, per [Events and Timing](../06-cuda-runtime-and-apis/events-and-timing.md), not host wall clock.
  - Dead code — if the result is unused, `ptxas` may delete the computation; write to a device array or a `volatile` sink.
  - Reporting — always state GPU model, driver, CUDA version, problem size, dtype, clock state, and how many iterations. A speedup without a baseline description is not a result.
- Close with `## A checklist` as a numbered list of the above, phrased as verifiable items — the folder-13 pages follow it.
- `:::tip[...]` — always report against a hardware ceiling too (effective bandwidth as a fraction of peak, or time as a multiple of cuBLAS), so the number means something without the reader knowing your GPU.

See also: `../06-cuda-runtime-and-apis/events-and-timing.md`, `../07-kernel-optimization/common-antipatterns.md`, `../13-applied-kernels-and-patterns/vector-add-and-saxpy.md`, `../readme.md`.

- [ ] **Step 4: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/09-tooling-profiling-and-debugging
git commit -m "docs: profiling metrics and benchmarking pages"
```
Expected: build exits 0.

---

### Task 6: `10-multi-gpu-and-scaling` — six pages

**Files:**
- Modify: all six files in `docs/gpu-computing/10-multi-gpu-and-scaling/`

**Interfaces:**
- Consumes: `08-libraries-and-ecosystem/nccl.md` (API), `02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md` (bandwidths).
- Produces: the outward link to `docs/machine-learning/02-deep-learning/distributed-training.md`, one of the six cross-section links the spec requires.

- [ ] **Step 1: Write `multi-gpu-basics.md`**

Sections: `## Two process models`, `## Device switching`, `## Per-device streams`, `## Partitioning work`, `## Where the time actually goes`.

Requirements:
- The two models compared in a table `| | One process, many devices | One process per device |` over: code complexity, NCCL support, fault isolation, memory per process, typical use. State plainly that one process per device (with NCCL and a launcher like `torchrun` or `mpirun`) is the standard for training.
- The single-process loop shown in `cpp`, making the `cudaSetDevice` discipline explicit:
  ```cpp showLineNumbers
  for (int d = 0; d < nDevices; ++d) {
      CUDA_CHECK(cudaSetDevice(d));
      CUDA_CHECK(cudaMemcpyAsync(d_in[d], h_in + d * chunk, bytes, 
                                 cudaMemcpyHostToDevice, stream[d]));
      myKernel<<<grid, block, 0, stream[d]>>>(d_in[d], d_out[d], chunk);
  }
  for (int d = 0; d < nDevices; ++d) {
      CUDA_CHECK(cudaSetDevice(d));
      CUDA_CHECK(cudaStreamSynchronize(stream[d]));
  }
  ```
  `:::warning[...]` that a stream belongs to the device that was current when it was created; using it under a different current device is an error.
- Partitioning: contiguous chunks for streaming work, interleaved for load balance, and the halo problem for stencils (forward to [Stencil and Convolution](../13-applied-kernels-and-patterns/stencil-and-convolution.md)).
- `:::tip[...]` — scaling efficiency, not raw throughput, is the number to track; anything below ~80% at small scale means communication is already dominating.

See also: `peer-to-peer-and-nvlink.md`, `parallelism-strategies.md`, `../06-cuda-runtime-and-apis/device-management.md`, `../readme.md`.

- [ ] **Step 2: Write `peer-to-peer-and-nvlink.md`**

Sections: `## What P2P gives you`, `## Enabling it`, `## Direct copies and direct access`, `## Discovering topology`, `## Bandwidth expectations`.

Requirements:
- The enable-and-copy sequence, complete:
  ```cpp showLineNumbers
  int canAccess = 0;
  CUDA_CHECK(cudaDeviceCanAccessPeer(&canAccess, 0, 1));
  if (canAccess) {
      CUDA_CHECK(cudaSetDevice(0));
      CUDA_CHECK(cudaDeviceEnablePeerAccess(1, 0));   // 0 accesses 1's memory
      CUDA_CHECK(cudaMemcpyPeerAsync(d1, 1, d0, 0, bytes, stream));
  }
  ```
- The distinction that matters: `cudaMemcpyPeer` is a copy; peer *access* lets a kernel on device 0 dereference a pointer into device 1's memory directly — convenient, but every access crosses the link, so it is only sensible for low-volume irregular access.
- `nvidia-smi topo -m` in `bash` with an annotated ` ```text ` sample output explaining `NV#`, `PIX`, `PXB`, `NODE`, `SYS`, and what each implies for placement.
- `:::warning[...]` that P2P over PCIe may be blocked by the chipset or IOMMU settings, and that `cudaDeviceCanAccessPeer` returning false silently routes copies through host memory at a large cost.
- Bandwidth expectations as a table referencing [Interconnects: PCIe and NVLink](../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md) rather than restating the numbers.

See also: `collectives-with-nccl.md`, `gpudirect-and-rdma.md`, `../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md`, `../readme.md`.

- [ ] **Step 3: Write `collectives-with-nccl.md`**

Sections: `## Ring algorithms`, `## Tree algorithms`, `## Cost models`, `## Overlapping communication with compute`, `## Bucketing gradients`.

Requirements:
- This page is about *algorithms and overlap*; the API lives in [NCCL](../08-libraries-and-ecosystem/nccl.md). Say so in the opening prose and do not duplicate the API.
- The ring all-reduce cost model, derived: `2(P-1)/P × N/B` — each of `P` ranks sends `N/P` bytes `2(P-1)` times. State the consequence: ring all-reduce time is nearly independent of `P` for large `N`, which is why it scales.
- Tree all-reduce contrasted: `O(log P)` latency, better for small messages; NCCL picks between them automatically, which is why `NCCL_ALGO` exists as an override.
- A Mermaid diagram of one ring reduce-scatter step with quoted labels.
- Overlap: the gradient-bucketing pattern used by DDP — start the all-reduce for layer *n*'s gradients while layer *n-1* is still computing its backward pass. Explain why bucket size is a tradeoff (too small: latency-dominated; too large: less overlap).
- `:::tip[...]` — confirm overlap on the Nsight Systems timeline; NCCL kernels appear as their own GPU work and should sit under the compute kernels, not after them.

See also: `../08-libraries-and-ecosystem/nccl.md`, `parallelism-strategies.md`, `../09-tooling-profiling-and-debugging/nsight-systems.md`, `../readme.md`.

- [ ] **Step 4: Write `parallelism-strategies.md`**

Sections: `## Data parallelism`, `## Model (tensor) parallelism`, `## Pipeline parallelism`, `## Sequence and expert parallelism`, `## Communication volume compared`, `## Combining them`.

Requirements:
- Each strategy gets: what it partitions, what must be communicated and when, and its failure mode (data: memory per device caps model size; tensor: needs very fast interconnect, so it stays within a node; pipeline: bubbles, mitigated by micro-batching; expert: routing imbalance).
- A comparison table `| Strategy | Partitions | Communicates | Per-step volume | Interconnect sensitivity |`.
- A Mermaid diagram of 3-D parallelism (data × tensor × pipeline) as a grid of devices, with quoted labels.
- **Required cross-section link**, in prose and in See also: [Distributed Training](../../machine-learning/02-deep-learning/distributed-training.md) for the training-side treatment (ZeRO/FSDP sharding, optimizer state, gradient accumulation). State explicitly that this page covers the communication mechanics and that page covers the training recipe.
- `:::tip[...]` — the standard layering on a multi-node cluster: tensor parallel within a node (NVLink), pipeline parallel across a few nodes, data parallel across the rest.

See also: `collectives-with-nccl.md`, `clusters-and-schedulers.md`, `../../machine-learning/02-deep-learning/distributed-training.md`, `../readme.md`.

- [ ] **Step 5: Write `gpudirect-and-rdma.md`**

Sections: `## Bypassing the host`, `## GPUDirect P2P`, `## GPUDirect RDMA`, `## GPUDirect Storage`, `## When the network becomes the bottleneck`.

Requirements:
- The unifying idea stated once: all three variants remove a bounce through host memory, saving both bandwidth and latency — and the reason each needs kernel/driver support is that a third-party device must be able to address GPU memory.
- GPUDirect RDMA: an InfiniBand or RoCE NIC DMAs straight into GPU memory; this is what makes NCCL's inter-node path fast, and it requires `nvidia-peermem` (or DMA-BUF on newer stacks).
- GPUDirect Storage: NVMe → GPU without a host bounce, via `cuFile`. Give the shape of the API in one short `cpp` snippet and say the win is largest for data-loading-bound inference and analytics.
- A table `| Path | Without GPUDirect | With GPUDirect |` showing the hop count in each case.
- `:::warning[...]` that GPUDirect requires specific hardware, driver, and topology support, and silently falls back to a staged copy when unavailable — verify with `NCCL_DEBUG=INFO` or the `cuFile` diagnostics rather than assuming.

See also: `peer-to-peer-and-nvlink.md`, `clusters-and-schedulers.md`, `../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md`, `../readme.md`.

- [ ] **Step 6: Write `clusters-and-schedulers.md`**

Sections: `## Requesting GPUs`, `## Slurm`, `## Kubernetes`, `## `CUDA_VISIBLE_DEVICES``, `## Containers`, `## Sharing policies`.

Requirements:
- Slurm: `sbatch` with `--gres=gpu:4` / `--gpus-per-node=4`, and the fact that Slurm sets `CUDA_VISIBLE_DEVICES` for you — so a job that also sets it usually breaks itself. Give a short `bash` job script launching one process per GPU.
- Kubernetes: `nvidia.com/gpu` as an extended resource in the pod spec (show a `json` or inline YAML-as-text snippet), the device plugin, and that GPUs are not fractionally allocatable without MPS/MIG/time-slicing configuration.
- `CUDA_VISIBLE_DEVICES` explained precisely: it renumbers devices from the process's perspective, so `CUDA_VISIBLE_DEVICES=2,3` makes physical GPU 2 appear as device 0. `:::warning[...]` that this makes logs ambiguous — log the device UUID from `cudaDeviceProp` when it matters.
- Containers: the NVIDIA Container Toolkit, `--gpus all`, and the rule that the *driver* comes from the host while the *toolkit* comes from the image.
- Sharing policies: point at [MPS and MIG](../06-cuda-runtime-and-apis/mps-and-mig.md) rather than restating it.

See also: `multi-gpu-basics.md`, `../06-cuda-runtime-and-apis/mps-and-mig.md`, `../06-cuda-runtime-and-apis/device-management.md`, `../readme.md`.

- [ ] **Step 7: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/10-multi-gpu-and-scaling
git commit -m "docs: multi-gpu and scaling pages"
```
Expected: build exits 0.

---

### Task 7: Figures for folder 09

**Files:**
- Create: `static/img/gpu/09-tooling-profiling-and-debugging/*.png`
- Modify: `static/img/gpu/SOURCES.md`
- Modify: `docs/gpu-computing/09-tooling-profiling-and-debugging/nsight-compute.md`

A profiler UI screenshot is one of the few cases where Mermaid genuinely cannot substitute — the page is teaching the reader to read a specific screen.

- [ ] **Step 1: Download the Nsight Compute figures**

```bash
mkdir -p static/img/gpu/09-tooling-profiling-and-debugging
curl -fsSL -o static/img/gpu/09-tooling-profiling-and-debugging/speed-of-light.png \
  https://docs.nvidia.com/nsight-compute/ProfilingGuide/graphics/gpu-speed-of-light.png
curl -fsSL -o static/img/gpu/09-tooling-profiling-and-debugging/roofline-chart.png \
  https://docs.nvidia.com/nsight-compute/ProfilingGuide/graphics/roofline-chart.png
```

- [ ] **Step 2: Verify the downloads**

Run: `file static/img/gpu/09-tooling-profiling-and-debugging/*.png`
Expected: `PNG image data` for each.

**If either 404s or is not a PNG:** delete it and skip its Steps 3–4. Replace the figure with a prose walkthrough of the section's fields (the page must still teach how to read the screen), and note the skip in the commit message. Do not substitute a screenshot from a blog or a third party.

- [ ] **Step 3: Add the `SOURCES.md` rows**

Append to the table in `static/img/gpu/SOURCES.md`, replacing `<today>` with the actual ISO date:

```md
| `09-tooling-profiling-and-debugging/speed-of-light.png` | https://docs.nvidia.com/nsight-compute/ProfilingGuide/ | NVIDIA | <today> | Screenshot from the Nsight Compute Profiling Guide; NVIDIA documentation terms. |
| `09-tooling-profiling-and-debugging/roofline-chart.png` | https://docs.nvidia.com/nsight-compute/ProfilingGuide/ | NVIDIA | <today> | Screenshot from the Nsight Compute Profiling Guide; NVIDIA documentation terms. |
```

- [ ] **Step 4: Reference them from the page**

In `nsight-compute.md`, in `## Speed of Light`:

```md
![The Speed of Light section, showing compute and memory throughput as percentages of peak](/img/gpu/09-tooling-profiling-and-debugging/speed-of-light.png)
*Source: [NVIDIA Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/)*
```

In `## The roofline chart`:

```md
![The roofline chart, plotting achieved performance against arithmetic intensity](/img/gpu/09-tooling-profiling-and-debugging/roofline-chart.png)
*Source: [NVIDIA Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/)*
```

- [ ] **Step 5: Verify and commit**

```bash
npm run build && npm run format && npm run lint
git add static/img/gpu docs/gpu-computing/09-tooling-profiling-and-debugging
git commit -m "docs: add nsight compute figures"
```
Expected: build exits 0.

---

## Plan 4 completion criteria

- 25 pages written; `npm run build` and `npm run lint` both exit 0.
- `grep -rln '```python' docs/gpu-computing/` lists exactly five files: the four Python pages in folder 08 plus `03-cuda-programming-model/installing-the-cuda-toolkit.md`.
- `grep -rn "define CUDA_CHECK" docs/gpu-computing/` still returns exactly one hit.
- `10-multi-gpu-and-scaling/parallelism-strategies.md` links `../../machine-learning/02-deep-learning/distributed-training.md`, and `09-tooling-profiling-and-debugging/building-cuda-with-cmake.md` links `../../programming/cmake/readme.md`.
- `static/img/gpu/SOURCES.md` has a row for every file under `static/img/gpu/`.
