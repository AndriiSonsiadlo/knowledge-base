---
id: math-libraries
title: cuFFT, cuRAND, cuSPARSE, cuSOLVER
sidebar_label: Math Libraries
sidebar_position: 4
tags: [gpu, cuda, libraries, math]
---

# cuFFT, cuRAND, cuSPARSE, cuSOLVER

Beyond dense linear algebra and deep learning, four more CUDA libraries cover the numerical building blocks that show up constantly but rarely justify a hand-written kernel: Fourier transforms, random number generation, sparse linear algebra, and dense/sparse factorizations. Each has its own handle type and its own lifecycle, but — as the closing section here makes explicit — they share more structure with each other, and with [cuBLAS](./cublas.md), than the four separate APIs first suggest.

## cuFFT

cuFFT computes discrete Fourier transforms on the GPU — 1D, 2D, and 3D, real-to-complex, complex-to-real, and complex-to-complex — and organizes work around a **plan**: an opaque object (`cufftHandle`) that encodes a transform's size, type, and batch count, created once with `cufftPlan1d`/`cufftPlan2d`/`cufftPlan3d` for a single transform or `cufftPlanMany` for a batch of them, then reused across every execution of that same transform shape. Plan creation does real work — choosing an algorithm and, for FFT sizes that don't factor cleanly, allocating internal workspace — so creating a plan inside a hot loop defeats the point; create it once outside the loop and call `cufftExecR2C`/`cufftExecC2R`/`cufftExecC2C` repeatedly against it.

```cpp showLineNumbers
cufftHandle plan;
int n = 1024;
int batch = 64;
// One 1D R2C transform of length n, repeated batch times, each with contiguous stride 1.
cufftPlanMany(&plan, 1, &n,
              nullptr, 1, n,       // input: no custom embedding, unit stride, dist n
              nullptr, 1, n / 2 + 1, // output: unit stride, dist n/2+1 complex values
              CUFFT_R2C, batch);
cufftSetStream(plan, stream);
cufftExecR2C(plan, d_input, d_output);
```

The pitfall that catches almost everyone: a real-to-complex transform of length `n` produces `n / 2 + 1` complex output values, not `n` — the upper half of the spectrum is redundant for real input and cuFFT doesn't store it. Sizing an output buffer for `n` complex values instead of `n / 2 + 1` either wastes memory or, worse, under-allocates when going the other direction. The second classic bug is normalization: cuFFT's inverse transform does not divide by `n` the way some other FFT libraries' inverse does, so a forward transform followed immediately by an inverse transform returns the *original signal scaled by `n`*, not the original signal — the caller is responsible for dividing by `n` if an unscaled round trip is what's wanted.

## cuRAND

cuRAND generates pseudo- and quasi-random numbers on the GPU through two distinct entry points. The **host API** creates a generator (`curandCreateGenerator(&gen, CURAND_RNG_PSEUDO_DEFAULT)`), seeds it (`curandSetPseudoRandomGeneratorSeed`), and then bulk-fills a device buffer in one call (`curandGenerateUniform`, `curandGenerateNormal`) — the natural fit when random numbers are a discrete step in a larger pipeline, like initializing weights before training starts. The **device API** instead gives each thread its own generator state (`curandState`), initialized in-kernel with `curand_init` and drawn from with `curand_uniform`/`curand_normal` calls inside the kernel body — the fit for something like Monte Carlo sampling, where every thread needs its own private stream of random draws as part of a larger kernel.

```cpp showLineNumbers
__global__ void mcKernel(curandState* states, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    curandState local = states[i];      // load this thread's persistent state
    float u = curand_uniform(&local);   // draw one uniform sample
    out[i] = u;
    states[i] = local;                  // store the advanced state back
}
```

:::warning[Seeding and per-thread state]
`curand_init` with a distinct sequence number per thread is the correct way to get statistically independent streams, but the call itself is relatively expensive — it should be done once, outside the hot loop, into a persisted `curandState` array (as above), never called fresh inside a kernel that runs every iteration. The opposite mistake is seeding every thread with the *same* seed and sequence number: that produces identical or heavily correlated random streams across threads, which silently corrupts anything downstream that assumes independence, such as a Monte Carlo estimate's variance.
:::

## cuSPARSE

cuSPARSE covers sparse matrix operations — sparse matrix-vector product (SpMV), sparse matrix-matrix product (SpMM/SpGEMM), and format conversions — through a **generic API** built around opaque, format-agnostic descriptors rather than one function signature per storage format. The most common format is **CSR** (compressed sparse row): three arrays — row offsets (one entry per row plus a terminal sentinel, giving each row's start index into the other two arrays), column indices, and values — that together store only the nonzero entries of a matrix, at the cost of no longer being able to index an element in constant time the way a dense array allows.

```cpp showLineNumbers
cusparseSpMatDescr_t matA;
cusparseDnVecDescr_t vecX, vecY;
cusparseCreateCsr(&matA, rows, cols, nnz, d_rowOffsets, d_colIdx, d_values,
                   CUSPARSE_INDEX_32I, CUSPARSE_INDEX_32I,
                   CUSPARSE_INDEX_BASE_ZERO, CUDA_R_32F);
cusparseCreateDnVec(&vecX, cols, d_x, CUDA_R_32F);
cusparseCreateDnVec(&vecY, rows, d_y, CUDA_R_32F);

size_t bufferSize;
cusparseSpMV_bufferSize(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
                         &alpha, matA, vecX, &beta, vecY,
                         CUDA_R_32F, CUSPARSE_SPMV_ALG_DEFAULT, &bufferSize);
cudaMalloc(&dBuffer, bufferSize);
cusparseSpMV(handle, CUSPARSE_OPERATION_NON_TRANSPOSE,
             &alpha, matA, vecX, &beta, vecY,
             CUDA_R_32F, CUSPARSE_SPMV_ALG_DEFAULT, dBuffer);
```

Every generic-API operation follows the same two-call protocol: an `_bufferSize` query that reports how much scratch device memory the operation needs for the given descriptors and algorithm, followed by the execute call itself once that buffer is allocated. Skipping the query and guessing a buffer size is the reliable way to get either wasted allocation or a silently wrong result.

## cuSOLVER

cuSOLVER factors and solves dense and sparse linear systems — LU, Cholesky, QR, eigenvalue and singular value decompositions — split across two handle types for two different problem classes. `cusolverDnHandle_t` covers dense factorizations (built on cuBLAS and cuSPARSE internally), and `cusolverSpHandle_t` covers sparse direct solvers (sparse Cholesky, sparse QR, sparse LU) built on cuSPARSE. Dense routines follow the same workspace-query pattern as cuSPARSE — call `cusolverDnSgetrf_bufferSize` to learn how much scratch space an LU factorization of a given size needs, allocate it, then call `cusolverDnSgetrf` itself — and every factorization call takes a `devInfo` output parameter: a single device-resident integer, one per call, that the caller must copy back to the host and check explicitly, since cuSOLVER's factorization calls themselves return only whether the *call* launched correctly, not whether the *factorization* succeeded (a zero pivot in LU, say, shows up in `devInfo`, not in the call's own return status).

## Shared conventions

All four libraries in this page, plus [cuBLAS](./cublas.md), converge on the same handful of conventions once the surface differences are set aside: a handle created once and bound to a stream (`cufftSetStream`, `cusparseSetStream`, `cusolverDnSetStream`) so the library composes with the rest of a stream-based pipeline; a workspace-query-then-execute two-call protocol for anything that needs scratch device memory sized to the specific problem; and, for the dense routines in particular, the column-major layout inherited from classical Fortran BLAS and LAPACK that [cuBLAS](./cublas.md) covers in full. Learning that shared shape once pays off across all five libraries, not just the one it was first learned on.

## See also

- [cuBLAS](./cublas.md) — the column-major convention referenced above, and the dense-GEMM counterpart to cuSOLVER's dense factorizations.
- [Sparse Matrix-Vector Product](../13-applied-kernels-and-patterns/sparse-matrix-vector.md) — an applied walkthrough of the CSR SpMV this page introduces.
- [Choosing a Library](./choosing-a-library.md) — where these four sit in the broader decision table.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
