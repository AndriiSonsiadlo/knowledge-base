---
id: cub
title: CUB
sidebar_label: CUB
sidebar_position: 6
tags: [gpu, cuda, libraries, cub]
---

# CUB

CUB is the layer [Thrust](./thrust.md) is built on and [Choosing a Library](./choosing-a-library.md) already named as the tuned building block for reductions, scans, and sorts: a template library of GPU primitives available at three different scopes, chosen depending on whether the call site is host code, a whole kernel, or a handful of cooperating threads inside one. Where Thrust replaces a kernel you'd otherwise write, CUB is what you reach for when you're still writing the kernel yourself and want a tuned, per-architecture primitive as one piece of it.

## Three levels

| Level | Callable from | Scope | Example |
|---|---|---|---|
| `cub::Device*` | Host code | Whole array, across the entire grid | `cub::DeviceReduce::Sum` |
| `cub::Block*` | Inside a `__global__` kernel | One thread block | `cub::BlockReduce` |
| `cub::Warp*` | Inside a `__global__` kernel | One warp | `cub::WarpReduce` |

The three are independent entry points, not a hierarchy you must pass through — a kernel can use `cub::WarpReduce` directly without ever touching `cub::BlockReduce`, and host code calling `cub::DeviceReduce::Sum` never sees a block or warp primitive at all, since the device-level call already launches and manages a full kernel internally.

## Device-level primitives

`cub::Device*` primitives — `DeviceReduce`, `DeviceScan`, `DeviceSort`, `DeviceSelect`, and others — are called from host code exactly the way a `cublasSgemm` call is: pass device pointers and a size, get a result, no kernel-writing involved. They differ from a Thrust call in one structural way: every `cub::Device*` call needs a caller-managed temporary storage buffer, sized by a first, separate call to the same function.

## The temp-storage protocol

Every `cub::Device*` algorithm is called twice with the same arguments — once to ask how much scratch space it needs, once to actually do the work — because the storage requirement depends on the problem size and can't be known before that first query. Getting this backwards, or reusing a stale `tempBytes` after the input size changes, is the standard CUB bug.

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

`d_temp == nullptr` is the signal CUB's own code checks to decide it's being asked for a size rather than asked to run — pass anything else on the first call and the size returned in `tempBytes` won't be meaningful. Every `cub::Device*` function follows this exact two-call shape, so once it's internalized for `DeviceReduce::Sum` it transfers directly to `DeviceScan::InclusiveSum`, `DeviceSort::SortKeys`, and the rest.

## Block-level primitives

`cub::BlockReduce` is CUB's in-kernel replacement for a hand-written block reduction like `blockReduceSum` from [Reductions and Scans](../05-execution-and-synchronization/reductions-and-scans.md). Both take one value per thread and return the block's total to thread 0; the difference is entirely in what's tunable and what's handled for you.

```cpp showLineNumbers
#include <cub/cub.cuh>

__global__ void sumKernel(const float* in, float* out, int n) {
    using BlockReduce = cub::BlockReduce<float, 256>;
    __shared__ typename BlockReduce::TempStorage temp;

    int i = blockIdx.x * blockDim.x + threadIdx.x;
    float val = (i < n) ? in[i] : 0.0f;

    float total = BlockReduce(temp).Sum(val);   // thread 0 holds the block total
    if (threadIdx.x == 0) out[blockIdx.x] = total;
}
```

`cub::BlockReduce<float, 256>` is templated on both the value type and the block size, and it declares its own `TempStorage` type sized exactly for that combination — the caller allocates one `__shared__ TempStorage` and hands it to the constructor, rather than sizing a shared array by hand the way `blockReduceSum`'s fixed `shared[32]` does. `Sum()` handles the warp-then-block reduction internally, including block sizes that aren't a multiple of the warp size, which `blockReduceSum` assumes away.

## Warp-level primitives

`cub::WarpReduce` is the same idea one level down — a single warp's worth of values reduced to one, without a `__syncthreads()` since a warp needs no block-wide barrier to exchange values via shuffle. It's the CUB equivalent of a hand-written `warpReduceSum` built on `__shfl_down_sync`, packaged the same way as `cub::BlockReduce`: templated on type, declaring its own `TempStorage`, called through a constructed instance.

## Why CUB beats a hand-rolled reduction

The mechanism is compile-time specialization, not a runtime trick: `cub::BlockReduce<T, BLOCK_DIM_X>` is templated on the exact block size and, through internal architecture dispatch, on the target compute capability, so the tile size, the number of items processed per thread, and the underlying algorithm — a raking reduction through shared memory versus a pure warp-shuffle tree — are all chosen and baked in at compile time for that specific combination. A hand-written `blockReduceSum` picks one algorithm and one shared-memory layout and uses it regardless of block size or architecture; CUB picks a different one per instantiation, and a new architecture gets a new tuned choice from a library update rather than a rewrite.

:::note[CUB ships with the CUDA Toolkit]
CUB is header-only and included with every CUDA Toolkit install — `#include <cub/cub.cuh>` needs no separate library to link. It's also the implementation underneath most of [Thrust](./thrust.md)'s device-side algorithms, so code that calls `thrust::reduce` is, in practice, already calling into CUB one layer down.
:::

## See also

- [Thrust](./thrust.md) — the host-callable layer built on top of these same primitives.
- [Reductions and Scans](../05-execution-and-synchronization/reductions-and-scans.md) — the hand-written `blockReduceSum` this page's `cub::BlockReduce` example replaces.
- [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md) — a full applied kernel built around the hand-written version CUB is compared against here.
- [Sorting on the GPU](../13-applied-kernels-and-patterns/sorting-on-the-gpu.md) — an applied use of `cub::DeviceSort` in context.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
