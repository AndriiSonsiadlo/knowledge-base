---
id: cublas
title: cuBLAS
sidebar_label: cuBLAS
sidebar_position: 2
tags: [gpu, cuda, libraries, cublas]
---

# cuBLAS

cuBLAS is NVIDIA's implementation of the BLAS (Basic Linear Algebra Subprograms) interface on the GPU: vector-vector, matrix-vector, and matrix-matrix operations, including the GEMM that [Choosing a Library](./choosing-a-library.md) and [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) both treat as the target hand-written kernels are measured against. The API is small and stable — a handle, a stream, and a handful of call shapes — but it inherits one convention from Fortran BLAS that trips up nearly everyone writing C or C++ against it for the first time.

## Handles and streams

Every cuBLAS call goes through a `cublasHandle_t`, created once and reused across calls; it holds internal workspace and state the library needs between operations, so creating one per call is wasted work. The handle is bound to a CUDA stream with `cublasSetStream`, and every operation issued through that handle runs on that stream — this is how cuBLAS calls compose with the rest of a stream-based pipeline rather than forcing their own synchronization point.

```cpp showLineNumbers
cublasHandle_t h;
CUBLAS_CHECK(cublasCreate(&h));
CUBLAS_CHECK(cublasSetStream(h, stream));
```

:::note[`CUBLAS_CHECK` is a cuBLAS-specific analogue of `CUDA_CHECK`]
[`CUDA_CHECK`](../06-cuda-runtime-and-apis/error-handling.md) checks a `cudaError_t` against `cudaSuccess`. cuBLAS calls return a different enum, `cublasStatus_t`, so they need their own checking macro rather than reusing `CUDA_CHECK` — the two are not interchangeable. `CUBLAS_CHECK` is local to this page and defined the same way, just against the cuBLAS status type:

```cpp
#define CUBLAS_CHECK(call)                                                  \
    do {                                                                    \
        cublasStatus_t st_ = (call);                                        \
        if (st_ != CUBLAS_STATUS_SUCCESS) {                                 \
            std::fprintf(stderr, "cuBLAS error %d at %s:%d\n",              \
                         (int)st_, __FILE__, __LINE__);                     \
            std::exit(EXIT_FAILURE);                                        \
        }                                                                   \
    } while (0)
```
:::

## Column-major, and what to do about it

cuBLAS inherits Fortran BLAS's column-major storage convention: it interprets a matrix argument as columns laid out contiguously in memory, with the leading dimension parameter (`lda`, `ldb`, `ldc`) giving the stride between columns. Nearly every C or C++ codebase, by contrast, stores matrices row-major — rows contiguous, with the leading dimension giving the stride between rows. Passing a row-major buffer straight into `cublasSgemm` and expecting a row-major result is the single biggest source of cuBLAS bugs: the call succeeds, returns a plausible-looking matrix, and that matrix is simply wrong (in general, the transpose of what was expected, though not exactly — see below).

The standard trick avoids ever transposing data in memory. A row-major matrix `M` of shape `(rows x cols)` is bit-for-bit identical, in memory, to a column-major matrix of shape `(cols x rows)` — reinterpreting a row-major buffer as column-major transposes it implicitly, for free, just by relabeling its dimensions. So to compute a row-major `C = A x B` where `A` is `(M x K)`, `B` is `(K x N)`, and `C` is `(M x N)`, reinterpret each buffer as its column-major transpose (`A` becomes `A^T`, an implicit `(K x M)`; `B` becomes `B^T`, an implicit `(N x K)`; `C` becomes `C^T`, an implicit `(N x M)`) and solve for the transposed identity instead: `C^T = B^T x A^T`. Concretely, that means swapping the `A` and `B` arguments and swapping the `M`/`N` dimensions passed to the call, while leaving the buffers themselves untouched.

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

No data is transposed at runtime — only the arguments describing how to read it change. This is the convention [CUTLASS](./cutlass.md) and [Matrix Multiply](../13-applied-kernels-and-patterns/matrix-multiply.md) both assume without re-deriving; this page is the one place in the section that spells it out.

## GEMM

`cublasSgemm` (and its `cublasDgemm`, `cublasHgemm`, `cublasGemmEx` siblings for other precisions) computes `C = alpha * op(A) * op(B) + beta * C`, where `op` is either the identity (`CUBLAS_OP_N`) or a transpose (`CUBLAS_OP_T`) applied by the library without materializing a transposed copy. `alpha` and `beta` are host- or device-resident scalars (controlled by `cublasSetPointerMode`) that let a single call fold in scaling and accumulation — `beta = 0` overwrites `C`, `beta = 1` accumulates into it. `cublasGemmEx` generalizes this further with explicit input, output, and compute-type arguments, which is how mixed-precision GEMM (FP16 inputs, FP32 accumulation) is expressed without a separate function per precision combination.

## Batched and strided-batched

Many small, independent GEMMs of the same shape — one per item in a batch — are common in both classical numerics and deep learning, and cuBLAS provides two ways to issue them as a single call rather than a loop of individual `cublasSgemm` calls, each paying its own launch overhead.

`cublasSgemmBatched` takes arrays of device pointers — `A[]`, `B[]`, `C[]` — one entry per matrix in the batch, each of which can in principle live anywhere in device memory. `cublasSgemmStridedBatched` instead takes a single base pointer per operand plus a constant stride between consecutive matrices, requiring that all matrices in the batch actually be laid out contiguously with uniform spacing. The strided form is faster when it applies, because it avoids the extra indirection of dereferencing a pointer array per matrix and avoids the array-of-pointers setup (and the host-to-device copy of that array) the batched form needs before the call. When a batch is naturally contiguous — the common case for batched training data — prefer the strided form.

## cuBLASLt

`cublasSgemm` computes a GEMM and nothing else; if the surrounding computation also needs a bias add, a ReLU, or a GELU applied to the result, that's a second kernel launch and a second pass over `C` in memory. cuBLASLt (`cublasLtHandle_t`, `cublasLtMatmul`) exists to close that gap: it exposes **epilogues** — bias, ReLU, GELU, and others — fused directly into the GEMM's output stage, plus finer control over layout (row- vs. column-major inputs without the classic-API's reinterpretation trick) and algorithm selection (`cublasLtMatmulAlgoGetHeuristic` searches candidate kernels for a given problem size). The reason cuBLASLt exists at all is fusion: everything it does could, in principle, be assembled from separate calls, but a fused epilogue avoids the extra kernel launch and the extra read-modify-write pass over the output that assembling it by hand would cost.

## Math modes and TF32

`cublasSetMathMode(handle, CUBLAS_TF32_TENSOR_OP_MATH)` tells cuBLAS to route FP32 GEMM calls through tensor cores using TF32 — full FP32 range, reduced mantissa — instead of full-precision FP32 math, without changing a single data type in the calling code. [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) covers TF32 as a hardware precision mode; this is the switch that turns it on for library calls specifically.

:::warning[TF32 changes numerical results silently]
Enabling TF32 math mode reduces the mantissa precision of every FP32 GEMM routed through it, and several popular framework builds enable it by default for FP32 training and inference. This is a common source of "the numbers changed between runs or versions" reports, because nothing in the calling code changes — only the math mode does. When bit-for-bit FP32 reproducibility matters, check the math mode explicitly rather than assuming full precision from a `float` type alone.
:::

## See also

- [CUTLASS](./cutlass.md) — the template library for GEMM shapes and epilogues cuBLAS doesn't cover, built on the same column-major convention.
- [Choosing a Library](./choosing-a-library.md) — where cuBLAS sits in the decision table against CUTLASS, CUB, and Triton.
- [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) — the hand-written `wmma` path cuBLAS's GEMM kernels outperform, and the TF32 precision mode this page's math-mode section switches on.
- [Matrix Multiply](../13-applied-kernels-and-patterns/matrix-multiply.md) — an applied GEMM walkthrough that assumes this page's column-major convention.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
