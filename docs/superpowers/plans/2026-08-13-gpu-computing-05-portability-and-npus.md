# GPU & Accelerators — Plan 5: Portability Layers and Inference Accelerators

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write the 20 pages of `11-portable-and-vendor-neutral/` and `12-npu-and-inference-accelerators/` — everything that is not CUDA on an NVIDIA GPU.

**Architecture:** Every file already exists as a stub with correct frontmatter (plan 1, task 1). This plan fills in bodies only, so `npm run build` (`onBrokenLinks: "throw"`) passes after every task.

**Tech Stack:** Docusaurus 3.9 (MDX), `@docusaurus/theme-mermaid`, Prism `cpp`/`glsl`/`hlsl`/`wgsl`/`bash`/`text` fences, Biome, Node ≥20.

**Spec:** `docs/superpowers/specs/2026-08-13-gpu-computing-docs-design.md`

**Prerequisite:** Plans 1–4 complete. Verify: `grep -n 'glsl' docusaurus.config.js` shows `glsl`, `hlsl`, and `wgsl` in `prism.additionalLanguages` — plan 1 added them, and the code fences in folder 11 depend on it.

**Plan series:** plan 5 of 6.

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

Only `:::info[...]`, `:::note[...]`, `:::tip[...]`, `:::warning[...]`.

### Code fences

- `cpp` for C++ (HIP, SYCL, OpenCL host code, Metal-cpp, OpenMP/OpenACC).
- `glsl` for GLSL compute shaders, `hlsl` for HLSL compute shaders, `wgsl` for WebGPU shaders. These three were added to `prism.additionalLanguages` by plan 1; do not add more.
- `bash`, `json`, `text` as needed. **No `python` anywhere in this plan** — Python is confined to folder 08 and `03-cuda-programming-model/installing-the-cuda-toolkit.md`.
- `showLineNumbers` on fences longer than ~5 lines.
- **Never redefine `CUDA_CHECK`** (defined once, in [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md)).

### Cross-vendor accuracy

- Use each vendor's own vocabulary, not translated CUDA terms: AMD has **wavefronts** (64 or 32 depending on architecture), **LDS** (not "shared memory"), and **CUs/WGPs** (not "SMs"). SYCL has **work-items**, **work-groups**, **nd-range**. Say the CUDA equivalent once in a mapping table, then use the native term.
- Do not claim performance parity between stacks. Where a portability layer costs performance, say so and say why (missing intrinsics, generic scheduling, immature codegen) — do not attach a number you cannot attribute.

### MDX hazards

Outside code fences and inline backticks, always backtick: `__global__`, `__device__`, `<<<grid, block>>>`, `<T>`, `sycl::queue`, `q.parallel_for<class name>`, and any bare `{` or `}`.

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
├── 11-portable-and-vendor-neutral/     9 pages  Task 1 (1-5), Task 2 (6-9)
└── 12-npu-and-inference-accelerators/ 11 pages  Task 3 (1-5), Task 4 (6-8), Task 5 (9-11)

static/img/gpu/
├── 12-npu-and-inference-accelerators/           Task 6
└── SOURCES.md                                   Task 6 (append rows)
```

---

### Task 1: `11-portable-and-vendor-neutral`, pages 1–5

**Files:**
- Modify: `the-portability-problem.md`, `hip-and-rocm.md`, `sycl-and-oneapi.md`, `opencl.md`, `openmp-and-openacc-offload.md`

**Interfaces:**
- Consumes: `01-parallel-computing-foundations/the-host-device-model.md` (the shared offload model), `03-cuda-programming-model/*` (the CUDA vocabulary being mapped from).
- Produces: the CUDA↔HIP↔SYCL↔OpenCL terminology mapping table, reused by `choosing-a-portability-layer.md` in Task 2.

- [ ] **Step 1: Write `the-portability-problem.md`**

Sections: `## What actually locks you in`, `## Three kinds of portability`, `## What portability costs`, `## The portable-performance question`, `## A realistic strategy`.

Requirements:
- Be specific about the lock-in, ranked from easy to hard to escape: (1) API calls — mechanical to translate; (2) libraries — cuBLAS/cuDNN/NCCL have counterparts of varying maturity; (3) warp-level intrinsics and hardware assumptions — warp size 32, bank count 32, tensor-core shapes; (4) tuning — tile sizes, unroll factors, and occupancy targets that were chosen for one architecture.
- Define the three portabilities clearly: *source* portability (it compiles), *functional* portability (it runs correctly), *performance* portability (it runs well). Say that the first two are largely solved and the third mostly is not.
- `:::warning[...]` that a "portable" kernel tuned only on NVIDIA hardware is usually a badly-tuned kernel everywhere else — portability without testing on the other target is a claim, not a property.
- Close with the realistic strategy: keep the algorithm portable, isolate the tuned inner kernel behind an interface, and accept per-vendor specializations for the few kernels that matter.

See also: `hip-and-rocm.md`, `choosing-a-portability-layer.md`, `../01-parallel-computing-foundations/the-host-device-model.md`, `../readme.md`.

- [ ] **Step 2: Write `hip-and-rocm.md`**

Sections: `## HIP as a near-CUDA API`, `## Porting with `hipify``, `## The ROCm stack`, `## AMD hardware differences`, `## Where the port breaks`.

Requirements:
- Show the API correspondence directly — a table with rows `cudaMalloc`/`hipMalloc`, `cudaMemcpy`/`hipMemcpy`, `<<<>>>`/`hipLaunchKernelGGL` (and that `<<<>>>` also works), `__syncthreads` (same), `cudaStream_t`/`hipStream_t`.
- `hipify-perl` and `hipify-clang` in `bash`, with the honest note that mechanical translation handles the API and leaves the hard parts.
- The ROCm library correspondence table: cuBLAS→rocBLAS/hipBLAS, cuDNN→MIOpen, CUB→hipCUB/rocPRIM, Thrust→rocThrust, NCCL→RCCL, cuFFT→rocFFT.
- The hardware differences that actually break ported kernels, each with its consequence:
  - **Wavefront size 64** on CDNA (32 on RDNA) — any kernel with a hardcoded `32`, a `0xffffffff` mask, or a warp-shuffle reduction assuming 32 lanes is wrong. Use `warpSize` and `__ballot(...)`'s 64-bit type.
  - **LDS** instead of shared memory — different size and bank behaviour.
  - **Matrix cores** with their own MFMA instructions, not `wmma`-compatible.
  - CDNA (datacenter) versus RDNA (consumer) having genuinely different compute characteristics.
- `:::warning[...]` on the 64-bit lane mask: `__ballot` returns `uint64_t` on CDNA, and code assuming a 32-bit mask silently drops half the lanes.
- `:::tip[...]` — build with `hipcc` and target with `--offload-arch=gfx90a`; `rocminfo` reports the target name.

See also: `the-portability-problem.md`, `sycl-and-oneapi.md`, `../05-execution-and-synchronization/warp-level-primitives.md`, `../readme.md`.

- [ ] **Step 3: Write `sycl-and-oneapi.md`**

Sections: `## Single-source C++`, `## Queues`, `## Buffers and accessors`, `## Unified shared memory`, `## DPC++ and the backends`, `## Running on NVIDIA and AMD`.

Requirements:
- A complete SAXPY in SYCL with USM, so it lines up with the CUDA version from [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md):
  ```cpp showLineNumbers title="saxpy.cpp"
  #include <sycl/sycl.hpp>

  int main() {
      sycl::queue q{sycl::default_selector_v};
      const int n = 1 << 20;

      float* x = sycl::malloc_device<float>(n, q);
      float* y = sycl::malloc_device<float>(n, q);
      // ... fill x and y ...

      q.parallel_for(sycl::range<1>(n), [=](sycl::id<1> i) {
          y[i] = 2.0f * x[i] + y[i];
      }).wait();

      sycl::free(x, q);
      sycl::free(y, q);
  }
  ```
- The two memory models compared: buffers + accessors (the runtime infers a dependency graph from accessor declarations, so you never write an explicit copy or wait) versus USM (pointers and explicit `q.memcpy`, familiar to CUDA programmers). Say when each is preferable.
- `nd_range` and `nd_item` for when you need work-group structure and local memory — the SYCL equivalent of choosing a block size — with a short snippet using `sycl::local_accessor`.
- The terminology mapping table: CUDA thread/block/grid/shared memory ↔ SYCL work-item/work-group/nd-range/local memory ↔ OpenCL's identical terms.
- Backends: DPC++ targeting Level Zero (Intel), CUDA (via the Codeplay/oneAPI plugin), and HIP (AMD). Give the `bash` compile line with `-fsycl-targets=nvptx64-nvidia-cuda`.
- `:::note[...]` that SYCL is a Khronos standard with several implementations (DPC++, AdaptiveCpp); oneAPI is Intel's product built around it.

See also: `opencl.md`, `hip-and-rocm.md`, `choosing-a-portability-layer.md`, `../readme.md`.

- [ ] **Step 4: Write `opencl.md`**

Sections: `## The object model`, `## Kernel language`, `## The host-side ceremony`, `## Why it lost mindshare`, `## Where it still matters`.

Requirements:
- The object chain as a Mermaid diagram with quoted labels: platform → device → context → command queue → program → kernel → buffers.
- A short OpenCL C kernel and the host-side setup that goes with it, deliberately shown at enough length to make the verbosity visible — that verbosity is part of the page's argument.
- The honest post-mortem, as concrete reasons rather than opinion: separate-source compilation (kernels as strings) breaks type checking and IDE support; no single-source C++; vendor implementations diverged in quality and lagged the standard; CUDA shipped a far better library ecosystem.
- Where it still matters: embedded and mobile GPUs, FPGA vendor toolchains, and as the portable fallback in software that must run anywhere (e.g. some rendering and video tools).
- `:::note[...]` that SPIR-V gave OpenCL an intermediate representation, which is also the substrate Vulkan compute and SYCL use.

See also: `sycl-and-oneapi.md`, `vulkan-and-directx-compute.md`, `the-portability-problem.md`, `../readme.md`.

- [ ] **Step 5: Write `openmp-and-openacc-offload.md`**

Sections: `## Directive-based offload`, `## The OpenMP target constructs`, `## Data clauses`, `## OpenACC`, `## The incremental-porting appeal`, `## The ceiling`.

Requirements:
- The pitch stated fairly: annotate an existing loop nest, keep one source that still compiles and runs on the CPU, and get working GPU code in an afternoon.
- The OpenMP construct stack explained one level at a time — `target` (move execution to the device), `teams` (create leagues, ≈ blocks), `distribute` (split the loop across teams), `parallel for simd` (across threads within a team) — then the combined form:
  ```cpp showLineNumbers
  #pragma omp target teams distribute parallel for simd \
          map(to: x[0:n]) map(tofrom: y[0:n])
  for (int i = 0; i < n; ++i)
      y[i] = a * x[i] + y[i];
  ```
- Data clauses as the performance-critical part: `map(to:)`, `map(from:)`, `map(tofrom:)`, `map(alloc:)`, and `#pragma omp target data` to hoist a region so arrays are not re-copied every loop. `:::warning[...]` that the default mapping copies on every construct entry and exit — this is the single most common reason a directive port is slower than the CPU version.
- OpenACC in a short section: `#pragma acc parallel loop` with `copyin`/`copyout`, `gang`/`worker`/`vector`, its NVIDIA-centric history, and its strong position in Fortran HPC.
- `## The ceiling`, stated plainly: no explicit control of shared memory, tiling, or warp-level operations, so a directive version typically reaches a fraction of a tuned kernel. It is the right tool for porting a large legacy codebase, the wrong one for a hot kernel.
- `:::tip[...]` — build with `nvc++ -mp=gpu` or `clang -fopenmp -fopenmp-targets=nvptx64` and check the compiler's offload remarks; a silently host-fallback loop is a common failure.

See also: `sycl-and-oneapi.md`, `choosing-a-portability-layer.md`, `../07-kernel-optimization/shared-memory-tiling.md`, `../readme.md`.

- [ ] **Step 6: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/11-portable-and-vendor-neutral
git commit -m "docs: portability layers, part 1"
```
Expected: build exits 0.

---

### Task 2: `11-portable-and-vendor-neutral`, pages 6–9

**Files:**
- Modify: `vulkan-and-directx-compute.md`, `metal-and-apple-silicon.md`, `webgpu.md`, `choosing-a-portability-layer.md`

**Interfaces:**
- Consumes: Task 1's terminology mapping table.
- Produces: the decision table in `choosing-a-portability-layer.md`, which `00-overview/the-accelerator-landscape.md` already points at.

- [ ] **Step 1: Write `vulkan-and-directx-compute.md`**

Sections: `## Compute in a graphics API`, `## The Vulkan setup`, `## GLSL compute shaders`, `## HLSL and DirectCompute`, `## Graphics interop`, `## When this is the right choice`.

Requirements:
- The framing that justifies the page: if your compute result feeds a render pass, doing it in the graphics API avoids a cross-API copy and a synchronization point — that, not raw compute throughput, is the reason to choose it.
- A GLSL compute shader in a ` ```glsl ` fence:
  ```glsl showLineNumbers
  #version 450
  layout(local_size_x = 256) in;

  layout(std430, binding = 0) buffer InBuf  { float x[]; };
  layout(std430, binding = 1) buffer OutBuf { float y[]; };
  layout(push_constant) uniform Params { float a; int n; };

  void main() {
      uint i = gl_GlobalInvocationID.x;
      if (i < uint(n)) y[i] = a * x[i] + y[i];
  }
  ```
  and the HLSL equivalent in a ` ```hlsl ` fence with `[numthreads(256,1,1)]`, `RWStructuredBuffer`, and `SV_DispatchThreadID`.
- A terminology row added to the mapping: workgroup ≈ block, invocation ≈ thread, subgroup ≈ warp, shared ≈ `__shared__`.
- The host-side cost described honestly: descriptor set layouts, pipeline layouts, command buffers, barriers, and explicit memory types — far more ceremony than a CUDA launch, and the main reason not to pick it for pure compute.
- `:::note[...]` on subgroup operations (`GL_KHR_shader_subgroup`) as the portable analogue of warp intrinsics, with the caveat that subgroup size varies by vendor and must be queried.

See also: `webgpu.md`, `opencl.md`, `metal-and-apple-silicon.md`, `../readme.md`.

- [ ] **Step 2: Write `metal-and-apple-silicon.md`**

Sections: `## Metal compute`, `## Unified memory on Apple Silicon`, `## MPS and MPSGraph`, `## The Neural Engine`, `## What to expect`.

Requirements:
- Metal's object model (device, command queue, command buffer, compute command encoder, pipeline state) in a Mermaid diagram with quoted labels, plus a short Metal Shading Language kernel in a ` ```cpp ` fence (MSL is a C++14 dialect; there is no Prism grammar for it, and `cpp` highlights it acceptably — say so in a one-line note).
- Unified memory treated as the genuinely different thing: on Apple Silicon the CPU and GPU share physical memory, so `MTLStorageModeShared` buffers need no copy at all. State the consequence — the transfer-cost analysis from [When Not to Use a GPU](../00-overview/when-not-to-use-a-gpu.md) changes shape entirely, and small-kernel offload becomes viable.
- MPS (Metal Performance Shaders) and MPSGraph as the cuBLAS/cuDNN-equivalent layer, and the route most users take: PyTorch's `mps` backend.
- The Neural Engine covered accurately: it is **not** directly programmable from Metal; it is reached through Core ML, and whether a model runs on ANE, GPU, or CPU is decided by Core ML's partitioner. Forward to [Edge NPUs](../12-npu-and-inference-accelerators/edge-npus.md).
- `:::warning[...]` that ANE operator support is narrow and undocumented in detail; a model that "supports ANE" may still run mostly on the GPU. Verify with Instruments rather than assuming.

See also: `webgpu.md`, `../12-npu-and-inference-accelerators/edge-npus.md`, `../00-overview/the-accelerator-landscape.md`, `../readme.md`.

- [ ] **Step 3: Write `webgpu.md`**

Sections: `## Compute in the browser`, `## WGSL`, `## Bind groups and pipelines`, `## The sandbox's limits`, `## Realistic use cases`.

Requirements:
- A WGSL compute shader in a ` ```wgsl ` fence:
  ```wgsl showLineNumbers
  @group(0) @binding(0) var<storage, read>       x : array<f32>;
  @group(0) @binding(1) var<storage, read_write> y : array<f32>;
  @group(0) @binding(2) var<uniform>             params : vec2<f32>;

  @compute @workgroup_size(256)
  fn main(@builtin(global_invocation_id) gid : vec3<u32>) {
      let i = gid.x;
      if (i < arrayLength(&x)) {
          y[i] = params.x * x[i] + y[i];
      }
  }
  ```
- The bind-group model explained in one paragraph plus a Mermaid diagram: layout → bind group → pipeline → pass → dispatch.
- The limits, stated concretely because they decide feasibility: conservative default buffer-size and workgroup-size limits (queryable via `adapter.limits`), no 64-bit floats, no pointers, no direct memory mapping, and required-feature negotiation.
- Realistic use cases: client-side inference of small models, interactive visualization, and in-browser simulation — not training and not HPC.
- `:::note[...]` that WebGPU also runs natively via `wgpu` and Dawn, which makes WGSL a plausible portable shader target outside the browser.

See also: `vulkan-and-directx-compute.md`, `choosing-a-portability-layer.md`, `../00-overview/the-accelerator-landscape.md`, `../readme.md`.

- [ ] **Step 4: Write `choosing-a-portability-layer.md`**

Sections: `## The four questions`, `## The decision table`, `## By target hardware`, `## By team and language`, `## Ecosystem maturity`, `## The pragmatic default`.

Requirements:
- The four questions asked up front: which hardware must this run on; what language does the team already write; how close to peak must it be; does it need to interoperate with graphics or a browser.
- The main decision table, with a row per option (CUDA, HIP, SYCL, OpenCL, OpenMP/OpenACC, Vulkan/DirectX, Metal, WebGPU, Triton) and columns `Targets | Language | Effort to port from CUDA | Performance ceiling | Ecosystem`.
- A second, shorter "if you must run on X" table keyed by hardware: NVIDIA only → CUDA; NVIDIA + AMD → HIP; NVIDIA + AMD + Intel → SYCL; Apple → Metal; browser → WebGPU; anything with a compute-capable driver → Vulkan or OpenCL; existing Fortran/C++ HPC code → OpenMP offload.
- `## The pragmatic default`, stated as an opinion the reader can act on: write CUDA, keep the algorithm and the host code free of CUDA-specific structure, and port with HIP if a second vendor becomes real. Adopting a portability layer before you have a second target usually costs more than it saves.
- `:::warning[...]` that "supports NVIDIA" in a portability layer's docs can mean anything from a first-class backend to a community plugin — check the CI matrix, not the marketing page.

See also: `the-portability-problem.md`, `hip-and-rocm.md`, `sycl-and-oneapi.md`, `../00-overview/the-accelerator-landscape.md`, `../readme.md`.

- [ ] **Step 5: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/11-portable-and-vendor-neutral
git commit -m "docs: portability layers, part 2"
```
Expected: build exits 0.

- [ ] **Step 6: Verify the new Prism languages render**

Run: `npm run serve`, open `http://localhost:3000/knowledge-base/docs/gpu-computing/11-portable-and-vendor-neutral/webgpu` and the Vulkan page. Confirm the WGSL, GLSL, and HLSL blocks are syntax-highlighted, not plain. If any is plain, check that plan 1 added it to `prism.additionalLanguages`. Stop the server.

---

### Task 3: `12-npu-and-inference-accelerators`, pages 1–5

**Files:**
- Modify: `what-is-an-npu.md`, `systolic-arrays-and-dataflow.md`, `google-tpu.md`, `edge-npus.md`, `jetson-and-dla.md`

**Interfaces:**
- Consumes: `00-overview/cpu-vs-gpu-vs-npu.md`, `02-gpu-hardware-architecture/tensor-cores.md`.
- Produces: the dataflow vocabulary (weight-stationary, output-stationary) reused by `google-tpu.md` and `compiler-stacks.md`.

- [ ] **Step 1: Write `what-is-an-npu.md`**

Sections: `## The design point`, `## Fixed function versus programmable`, `## Energy per operation`, `## What an NPU is bad at`, `## The operator-coverage problem`.

Requirements:
- The core tradeoff quantified in the right currency: an NPU spends almost all its area on multiply-accumulate hardware and on-chip weight storage, and almost none on instruction fetch, scheduling, or general-purpose memory access. That buys roughly an order of magnitude in energy per MAC and costs general programmability. State the direction confidently; attribute any specific figure to a source or omit it.
- A comparison table `| | GPU (SIMT) | NPU (fixed-function) |` over: unit of work, control flow support, precision support, memory model, programming interface, energy per MAC.
- `## The operator-coverage problem` is the practical heart of the page: an NPU implements a fixed operator set, and an unsupported op forces a fallback to CPU or GPU, often with a layout conversion on each boundary — so a model with one unsupported op can be *slower* than not using the NPU at all.
- `:::warning[...]` on exactly that fallback cost, forward-linking [Deploying to Accelerators](./deploying-to-accelerators.md).

See also: `systolic-arrays-and-dataflow.md`, `edge-npus.md`, `../00-overview/cpu-vs-gpu-vs-npu.md`, `../readme.md`.

- [ ] **Step 2: Write `systolic-arrays-and-dataflow.md`**

Sections: `## The idea`, `## GEMM on a systolic array`, `## Weight-stationary`, `## Output-stationary`, `## Row-stationary`, `## Why data movement dominates energy`.

Requirements:
- Explain the mechanism concretely: a 2-D grid of MAC cells where each cell passes its operand to its neighbour every cycle, so one memory read feeds an entire row or column of cells. That reuse — not the MAC count — is the win.
- A Mermaid diagram of a small array showing operands flowing right and partial sums flowing down, with quoted edge labels.
- Each dataflow gets a section: what stays resident in the cell, what streams, and which shape it suits — weight-stationary for large batches over fixed weights (the classic TPU case), output-stationary for deep accumulation, row-stationary as the Eyeriss-style compromise.
- The energy argument stated as a hierarchy: a DRAM access costs orders of magnitude more energy than a MAC, an SRAM access much less, and a register-file or neighbour access less again — which is why the whole field is organized around reuse. Give the ordering and say it is architecture-dependent rather than quoting exact picojoules without a source.
- `:::note[...]` connecting this back to [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md): a tensor core is a small, programmable matrix engine embedded in a SIMT machine — the same idea at a different point on the flexibility axis.

See also: `google-tpu.md`, `what-is-an-npu.md`, `../02-gpu-hardware-architecture/tensor-cores.md`, `../readme.md`.

- [ ] **Step 3: Write `google-tpu.md`**

Sections: `## The MXU`, `## Memory`, `## Pods and the interconnect`, `## XLA is the only entry point`, `## TPU versus GPU`.

Requirements:
- The MXU described as a large systolic matrix unit, with the consequence for users: shapes that do not fill the MXU waste it, which is why TPU guidance is full of "pad your batch and feature dimensions to a multiple of the tile".
- Pod topology: chips connected in a 2-D or 3-D torus with dedicated inter-chip links, and why that topology suits all-reduce.
- The programming model stated plainly: you do not write TPU kernels. You write JAX or PyTorch/XLA, XLA compiles the graph, and your control over the hardware is through graph structure and shapes. Pallas exists for custom kernels but is niche.
- A comparison table `| | TPU | NVIDIA GPU |` over: programming model, kernel-level control, ecosystem, sparse/irregular workloads, availability.
- `:::warning[...]` on shape polymorphism: XLA recompiles per shape, so a model with variable sequence lengths can spend most of its time compiling. Bucketing shapes is the standard fix.

See also: `systolic-arrays-and-dataflow.md`, `compiler-stacks.md`, `../00-overview/the-accelerator-landscape.md`, `../readme.md`.

- [ ] **Step 4: Write `edge-npus.md`**

Sections: `## What "edge NPU" covers`, `## Apple Neural Engine`, `## Qualcomm Hexagon`, `## Arm Ethos-U`, `## Laptop NPUs`, `## The common constraints`.

Requirements:
- One `##` per vendor, each with: what it is, its SDK or entry point, its supported precisions, and its main limitation.
  - Apple Neural Engine — Core ML only; no direct API; partitioner decides placement.
  - Qualcomm Hexagon — QNN SDK / AI Engine Direct, also reachable through ONNX Runtime's QNN execution provider and LiteRT.
  - Arm Ethos-U — microcontroller-class, INT8-only, driven by TFLite Micro with the Vela compiler; the operator set is small and the model must be compiled ahead of time.
  - Laptop NPUs (Intel AI Boost / AMD XDNA) — reached through OpenVINO, DirectML, or ONNX Runtime; positioned for sustained low-power inference rather than peak throughput.
- A summary table `| NPU | SDK | Precisions | Typical use |`.
- `## The common constraints` collects what they share: INT8 (sometimes INT4/FP16) only, a fixed operator set, ahead-of-time compilation, static shapes, and small on-chip memory that caps model size.
- `:::tip[...]` — target these through ONNX Runtime or LiteRT with the vendor execution provider rather than the native SDK, unless you need something the provider does not expose. Link [ONNX and ONNX Runtime](./onnx-and-runtimes.md).

See also: `what-is-an-npu.md`, `onnx-and-runtimes.md`, `openvino.md`, `../11-portable-and-vendor-neutral/metal-and-apple-silicon.md`, `../readme.md`.

- [ ] **Step 5: Write `jetson-and-dla.md`**

Sections: `## The Jetson platform`, `## Unified memory`, `## The Deep Learning Accelerator`, `## Power modes and clocks`, `## Thermal limits`, `## Developing for Jetson`.

Requirements:
- Jetson described as a full CUDA GPU on an SoC — so everything in folders 03–07 applies — with three differences that change decisions: memory is physically shared with the CPU, the power envelope is fixed, and the DLA sits alongside the GPU.
- Unified memory on Jetson: `cudaMallocManaged` needs no migration because there is one physical memory, so the [Unified Memory](../04-cuda-memory-model/unified-memory.md) performance traps mostly do not apply — but pinned/mapped allocation still matters for cache coherence. Say this explicitly, because it is the most commonly mis-transferred piece of desktop CUDA knowledge.
- The DLA: a fixed-function inference engine reached through TensorRT (`config->setDeviceType(layer, DeviceType::kDLA)`), supporting a subset of layers, with GPU fallback for the rest. Its value is running inference while leaving the GPU free.
- Power modes: `nvpmodel -m <n>` selects a power/clock profile and `jetson_clocks` pins clocks to maximum. `:::warning[...]` that benchmarking without fixing the power mode makes results irreproducible — this is the Jetson-specific instance of the rule in [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md).
- `:::note[...]` that thermal throttling on a passively cooled module makes sustained throughput materially lower than burst throughput; measure over minutes, not seconds.

See also: `tensorrt.md`, `../04-cuda-memory-model/unified-memory.md`, `../09-tooling-profiling-and-debugging/benchmarking-methodology.md`, `../readme.md`.

- [ ] **Step 6: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/12-npu-and-inference-accelerators
git commit -m "docs: npu architecture and platform pages"
```
Expected: build exits 0.

---

### Task 4: `12-npu-and-inference-accelerators`, pages 6–8

**Files:**
- Modify: `quantization-for-accelerators.md`, `tensorrt.md`, `onnx-and-runtimes.md`

**Interfaces:**
- Consumes: Task 3's operator-coverage framing.
- Produces: the quantization vocabulary (symmetric/asymmetric, per-tensor/per-channel, PTQ/QAT) reused by `openvino.md` and `deploying-to-accelerators.md`; the **required cross-section link** to `docs/machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md`.

- [ ] **Step 1: Write `quantization-for-accelerators.md`**

Sections: `## Why accelerators want integers`, `## The affine mapping`, `## Symmetric versus asymmetric`, `## Per-tensor versus per-channel`, `## PTQ and QAT`, `## Calibration`, `## FP8 and INT4`, `## Accuracy budgets`.

Requirements:
- Motivate from hardware rather than from ML: INT8 MACs are smaller and cheaper than FP16 ones, weights take a quarter of the memory of FP32, and on a memory-bound inference workload the bandwidth saving alone is most of the speedup.
- The affine mapping given explicitly with both directions:
  `q = round(x / s) + z` and `x ≈ s × (q − z)`, defining scale `s` and zero-point `z`, and stating that symmetric quantization forces `z = 0`.
- Symmetric vs asymmetric compared in a table over: zero-point, hardware cost, typical use (weights symmetric, activations often asymmetric), and accuracy on skewed distributions.
- Per-tensor vs per-channel: one scale for the whole tensor versus one per output channel; per-channel is standard for weights because channel dynamic ranges differ by orders of magnitude, and is often unsupported for activations in hardware.
- PTQ vs QAT compared over: effort, data needed, typical accuracy recovery, and when each is the right call.
- Calibration: a few hundred representative samples, and the choice of range estimator (min/max, percentile, entropy/KL) with one line each on when it matters.
- FP8 (E4M3 for weights/activations, E5M2 for gradients) and INT4 with its group-wise scaling — say which hardware generations support each, referencing [Tensor Cores](../02-gpu-hardware-architecture/tensor-cores.md).
- **Required cross-section link**, in prose and in See also: [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) — say plainly that mixed-precision *training* and post-training *quantization* are different problems that share vocabulary.
- `:::warning[...]` — always validate quantized accuracy on a held-out set, not on the calibration set. A quantized model that looks fine on calibration data and fails in production is the standard failure.

See also: `tensorrt.md`, `deploying-to-accelerators.md`, `../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md`, `../readme.md`.

- [ ] **Step 2: Write `tensorrt.md`**

Sections: `## Build time versus run time`, `## Building an engine`, `## Precision modes`, `## Dynamic shapes and optimization profiles`, `## Layer fusion`, `## Plugins`, `## Engine portability`.

Requirements:
- The central fact framed first: TensorRT is a *compiler*. It benchmarks candidate kernels for your exact layers, shapes, and GPU, then emits a serialized engine. That is why building is slow, why the engine is fast, and why the engine is not portable.
- The build path in `bash` with `trtexec`, which is how most people should start:
  ```bash
  trtexec --onnx=model.onnx --saveEngine=model.plan \
          --fp16 --memPoolSize=workspace:4096 \
          --minShapes=input:1x3x224x224 \
          --optShapes=input:8x3x224x224 \
          --maxShapes=input:32x3x224x224
  ```
- Precision modes: FP32, FP16, INT8 (requires calibration or Q/DQ nodes in the ONNX graph), FP8 on supported hardware; and `--best` letting TensorRT choose per layer.
- Optimization profiles explained as the mechanism behind dynamic shapes — min/opt/max per input, with kernels selected for the *opt* shape. `:::tip[...]` that a profile spanning batch 1 to 128 gives worse performance at both ends than two narrower profiles.
- Layer fusion: conv+bias+activation into one kernel, plus tensor-layout selection; and that the fusion is why the engine's layer names no longer match the ONNX graph's.
- Plugins (`IPluginV2DynamicExt`) for unsupported ops, with the note that a plugin is a CUDA kernel you write — folders 03–07 are the prerequisite.
- `:::warning[...]` — an engine is tied to the TensorRT version, the GPU architecture, and often the exact driver. Build on the deployment target, or rebuild in the deployment container; do not ship a `.plan` built elsewhere.

See also: `onnx-and-runtimes.md`, `quantization-for-accelerators.md`, `jetson-and-dla.md`, `deploying-to-accelerators.md`, `../readme.md`.

- [ ] **Step 3: Write `onnx-and-runtimes.md`**

Sections: `## The exchange format`, `## Opsets`, `## ONNX Runtime`, `## Execution providers`, `## Provider fallback`, `## Graph optimizations`, `## Exporting cleanly`.

Requirements:
- ONNX described accurately: a protobuf graph of typed tensors and versioned operators — a format, not a runtime — and ONNX Runtime as one (dominant) engine that consumes it.
- Opsets explained as the compatibility axis: an exporter targets an opset version and a runtime supports a range; most "unsupported operator" errors are an opset mismatch, not a missing feature.
- The execution-provider table: CPU, CUDA, TensorRT, DirectML, CoreML, QNN, OpenVINO, ROCm — each with its target hardware and one line on maturity.
- Provider fallback explained as the thing that silently costs performance: providers are tried in priority order per node, so an unsupported node splits the graph and inserts a memory transfer at each boundary. Show how to inspect the partitioning (session profiling / verbose logging) rather than guessing.
- `:::warning[...]` on exactly that: a model reported as "running on the NPU" may be running half on the CPU with a copy at every boundary. Check the node assignment.
- Exporting cleanly: constant-fold, avoid data-dependent control flow, prefer static shapes where the target requires them, and validate numerics against the source framework before optimizing anything.

See also: `tensorrt.md`, `openvino.md`, `edge-npus.md`, `deploying-to-accelerators.md`, `../readme.md`.

- [ ] **Step 4: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/12-npu-and-inference-accelerators
git commit -m "docs: quantization and inference runtime pages"
```
Expected: build exits 0.

---

### Task 5: `12-npu-and-inference-accelerators`, pages 9–11

**Files:**
- Modify: `openvino.md`, `compiler-stacks.md`, `deploying-to-accelerators.md`

**Interfaces:**
- Consumes: Tasks 3 and 4.
- Produces: the deployment checklist, which is the folder's closing page.

- [ ] **Step 1: Write `openvino.md`**

Sections: `## What OpenVINO is for`, `## Model conversion and the IR`, `## Device plugins`, `## AUTO, HETERO, and MULTI`, `## Quantization with NNCF`, `## Where it fits`.

Requirements:
- Position it: Intel's inference stack, strongest on Intel CPUs, integrated GPUs, and laptop NPUs — the natural target when the deployment hardware is an Intel client machine.
- Model conversion: `ovc` / `openvino.convert_model` producing the IR (`.xml` topology + `.bin` weights), and that OpenVINO also reads ONNX directly, so the IR is an optimization, not a requirement.
- Device plugins `CPU`, `GPU`, `NPU` and the virtual devices explained precisely, since the names are easy to confuse:
  - `AUTO` — picks a device and can start on CPU while a faster device compiles.
  - `HETERO` — splits one model across devices by operator support.
  - `MULTI` — runs inference requests across several devices for throughput.
- NNCF for post-training and training-time quantization, connecting back to [Quantization for Accelerators](./quantization-for-accelerators.md) rather than restating the theory.
- `:::tip[...]` — throughput mode plus multiple inference requests matters more than any single-stream optimization on CPU and integrated GPU; latency mode is a different configuration.

See also: `onnx-and-runtimes.md`, `edge-npus.md`, `quantization-for-accelerators.md`, `../readme.md`.

- [ ] **Step 2: Write `compiler-stacks.md`**

Sections: `## Kernel libraries versus graph compilers`, `## XLA`, `## TVM`, `## MLIR`, `## `torch.compile` and Inductor`, `## What compilers are still bad at`.

Requirements:
- The framing that organizes the page: a kernel library gives you a fast implementation of an operator you name; a graph compiler looks at the whole graph and generates code, which is what lets it fuse across operator boundaries and choose layouts globally.
- XLA: HLO as its IR, fusion and layout assignment as its main passes, shape specialization and recompilation as its main cost. Cross-reference [Google TPU](./google-tpu.md).
- TVM: separation of compute and schedule, autotuning over a schedule space (AutoTVM/Ansor), and its strength on diverse edge targets.
- MLIR: not a compiler but a compiler *infrastructure* — dialects and progressive lowering — and why almost every stack in this list is converging on it. Name the dialects the reader will actually meet (`linalg`, `affine`, `gpu`, `nvvm`).
- `torch.compile` / Inductor: TorchDynamo captures the graph, Inductor generates Triton for GPU and C++/OpenMP for CPU. Link [Triton](../08-libraries-and-ecosystem/triton.md) and [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md).
- A comparison table `| Stack | Frontend | IR | Backends | Autotuning |`.
- `## What compilers are still bad at`, stated honestly: tuned GEMM and attention (still library or hand-written territory), dynamic shapes, data-dependent control flow, and graph breaks that silently disable the whole optimization.
- `:::tip[...]` — `TORCH_LOGS=graph_breaks` (or `torch._dynamo.explain`) shows where compilation gave up; one graph break in a hot loop can erase the entire benefit.

See also: `../08-libraries-and-ecosystem/triton.md`, `google-tpu.md`, `../07-kernel-optimization/kernel-fusion-and-launch-overhead.md`, `../readme.md`.

- [ ] **Step 3: Write `deploying-to-accelerators.md`**

Sections: `## Choosing a target`, `## Checking operator coverage first`, `## Validating accuracy after quantization`, `## Latency, throughput, and batching`, `## Fallback paths`, `## A deployment checklist`.

Requirements:
- This is the folder's closing page — it should be a procedure, not a survey.
- Target selection as a table `| Constraint | Target | Stack |`: server throughput → NVIDIA GPU + TensorRT; server with mixed hardware → ONNX Runtime with providers; Intel client → OpenVINO; Apple client → Core ML; Android/Qualcomm → LiteRT or ONNX Runtime + QNN; microcontroller → TFLite Micro + Ethos-U; Google Cloud training → TPU + XLA.
- Operator coverage checked **before** committing: export to ONNX, run the target's compatibility check, and list unsupported nodes. Say plainly that this step, done first, prevents most deployment failures.
- Accuracy validation: compare against the source framework on a held-out set with a task metric, not just tensor MSE; define an accuracy budget before quantizing, not after.
- Latency versus throughput: batching raises throughput and raises tail latency; state the tradeoff, mention dynamic batching in serving stacks, and note that on an NPU the batch size may be fixed at compile time.
- Fallback paths: what happens when the accelerator is absent, busy, or the model fails to compile — and that a CPU path must exist and be tested.
- `## A deployment checklist` as a numbered list of the above, verifiable item by item.

See also: `tensorrt.md`, `onnx-and-runtimes.md`, `quantization-for-accelerators.md`, `compiler-stacks.md`, `../readme.md`.

- [ ] **Step 4: Verify, format, commit**

```bash
npm run build && npm run format && npm run lint
git add docs/gpu-computing/12-npu-and-inference-accelerators
git commit -m "docs: accelerator deployment pages"
```
Expected: build exits 0.

---

### Task 6: Figure for folder 12

**Files:**
- Create: `static/img/gpu/12-npu-and-inference-accelerators/tpu-systolic-array.png`
- Modify: `static/img/gpu/SOURCES.md`
- Modify: `docs/gpu-computing/12-npu-and-inference-accelerators/systolic-arrays-and-dataflow.md`

- [ ] **Step 1: Attempt the download**

Google Cloud's TPU architecture documentation publishes a systolic-array animation/diagram:

```bash
mkdir -p static/img/gpu/12-npu-and-inference-accelerators
curl -fsSL -o static/img/gpu/12-npu-and-inference-accelerators/tpu-systolic-array.png \
  https://cloud.google.com/static/tpu/docs/images/tpu-systolic-array.png
```

- [ ] **Step 2: Verify the download**

Run: `file static/img/gpu/12-npu-and-inference-accelerators/tpu-systolic-array.png`
Expected: `PNG image data`.

**If it 404s, returns HTML, or is not a PNG — which is likely, since this URL is less stable than the `docs.nvidia.com` ones:** delete the file and **stop here**. Skip Steps 3–5 entirely and keep the Mermaid diagram already on the page; it covers the same mechanism. Do not go hunting for a substitute image on a blog or an image host — provenance matters more than having a figure. Record the skip by committing nothing for this task.

- [ ] **Step 3: Add the `SOURCES.md` row**

Only if Step 2 succeeded. Append, replacing `<today>` with the actual ISO date:

```md
| `12-npu-and-inference-accelerators/tpu-systolic-array.png` | https://cloud.google.com/tpu/docs/system-architecture-tpu-vm | Google | <today> | Figure from Google Cloud TPU documentation; Google Cloud documentation terms. |
```

- [ ] **Step 4: Reference it from the page**

In `systolic-arrays-and-dataflow.md`, in `## GEMM on a systolic array`, after the Mermaid diagram:

```md
![Operands flowing through a systolic array of multiply-accumulate cells](/img/gpu/12-npu-and-inference-accelerators/tpu-systolic-array.png)
*Source: [Google Cloud TPU system architecture](https://cloud.google.com/tpu/docs/system-architecture-tpu-vm)*
```

- [ ] **Step 5: Verify and commit**

```bash
npm run build && npm run format && npm run lint
git add static/img/gpu docs/gpu-computing/12-npu-and-inference-accelerators
git commit -m "docs: add systolic array figure"
```
Expected: build exits 0.

---

## Plan 5 completion criteria

- 20 pages written; `npm run build` and `npm run lint` both exit 0.
- `grep -rln '```python' docs/gpu-computing/1[12]-*` returns nothing.
- WGSL, GLSL, and HLSL blocks render highlighted (verified in Task 2, Step 6).
- `12-npu-and-inference-accelerators/quantization-for-accelerators.md` links `../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md`.
- AMD pages use wavefront/LDS/CU terminology, not translated CUDA terms, and call out the 64-lane wavefront explicitly.
- `static/img/gpu/SOURCES.md` has a row for every file under `static/img/gpu/`.
