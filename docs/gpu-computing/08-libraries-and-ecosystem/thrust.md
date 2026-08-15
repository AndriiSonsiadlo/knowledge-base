---
id: thrust
title: Thrust
sidebar_label: Thrust
sidebar_position: 5
tags: [gpu, cuda, libraries, thrust]
---

# Thrust

Thrust is a C++ template library, shipped with the CUDA Toolkit, that reproduces the shape of the C++ Standard Template Library on the GPU: containers that own device memory, algorithms that operate over iterator ranges, and functors that customize them — `thrust::sort`, `thrust::reduce`, `thrust::transform` — without a single explicit `cudaMalloc`, `cudaMemcpy`, or `<<<grid, block>>>` in the calling code. It is the fastest way to get a correct, reasonably fast GPU implementation of a standard algorithm working from host code, and [Choosing a Library](./choosing-a-library.md) already places it precisely: the host-callable layer above `cub`'s in-kernel primitives.

## STL for the device

Thrust mirrors the STL's separation of containers, iterators, and algorithms so that a C++ programmer already fluent in `std::vector` and `std::transform` can read Thrust code without learning a new mental model — only the memory space the container lives in changes.

```cpp showLineNumbers
#include <thrust/device_vector.h>
#include <thrust/transform.h>
#include <thrust/reduce.h>
#include <thrust/functional.h>
#include <cstdio>

int main() {
    thrust::device_vector<float> in(1 << 20, 1.0f);
    thrust::device_vector<float> out(in.size());

    // out[i] = in[i] * 2
    thrust::transform(in.begin(), in.end(), out.begin(),
                       [] __device__ (float x) { return x * 2.0f; });

    float total = thrust::reduce(out.begin(), out.end(), 0.0f, thrust::plus<float>());
    std::printf("sum = %f\n", total);
}
```

Nothing here names a pointer, a stream, or a launch configuration. Constructing `in` allocates and initializes device memory; `transform` and `reduce` each compile to their own kernel launch under the hood, chosen and tuned by [CUB](./cub.md), which Thrust uses as its device-side implementation for most algorithms.

## Containers

`thrust::device_vector<T>` owns memory on the GPU; `thrust::host_vector<T>` owns memory on the host; assigning one to the other issues the `cudaMemcpy` for you, in the direction implied by which side is which. Both support the usual `push_back`, `resize`, `size`, and iterator interface `std::vector` does, which is exactly the point — the container API is unchanged, only where the bytes live differs.

:::warning[`device_vector` construction is synchronous, and default construction zero-initializes]
Constructing a `thrust::device_vector<float> v(n)` doesn't just allocate `n * sizeof(float)` bytes — it also zero-initializes them, which costs a kernel launch (or a `cudaMemset`) on top of the allocation, and the allocation itself is a synchronous `cudaMalloc` under Thrust's default execution policy. Neither cost is visible in the source, and both are easy to miss when a `device_vector` is constructed inside a hot loop instead of once outside it. Preallocate and reuse vectors across iterations, or construct with `thrust::no_init` when the zero-fill is provably unnecessary, the same way [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md) treats `cudaMalloc` in a loop as an antipattern to avoid.
:::

## Algorithms and execution policies

Every Thrust algorithm accepts an optional execution policy as its first argument, which selects where the algorithm actually runs and how it's scheduled: `thrust::device` forces device-side execution, `thrust::host` forces host-side execution regardless of where the iterators point, and `thrust::cuda::par.on(stream)` runs on the device bound to a specific CUDA stream instead of the default stream.

```cpp showLineNumbers
// Runs on the given stream instead of the default stream, and does not
// implicitly synchronize the whole device on completion.
thrust::reduce(thrust::cuda::par.on(stream), in.begin(), in.end(), 0.0f);
```

The stream-bound policy matters for more than placement: several Thrust algorithms allocate temporary storage internally, and without an explicit policy that allocation and the algorithm's completion can force a device-wide synchronization that stalls every other stream in flight. Binding the policy to a specific stream is how Thrust calls compose into a larger, overlapped pipeline instead of each one becoming an implicit barrier.

## Fancy iterators

Thrust's iterators aren't limited to walking existing memory — a `counting_iterator` produces `0, 1, 2, ...` without a backing array, and a `transform_iterator` applies a functor to whatever it dereferences to, lazily, on read. Composing the two lets an algorithm consume a computed sequence without ever materializing it in memory, which is Thrust's real advantage over writing the equivalent kernel by hand: fusion through iterators rather than through an extra pass.

```cpp showLineNumbers
#include <thrust/iterator/counting_iterator.h>
#include <thrust/iterator/transform_iterator.h>

struct square {
    __device__ float operator()(int i) const { return static_cast<float>(i) * i; }
};

// Sum of squares 0^2 + 1^2 + ... + (n-1)^2, with no intermediate array ever allocated.
thrust::counting_iterator<int> first(0), last(n);
float sum_of_squares = thrust::reduce(
    thrust::make_transform_iterator(first, square()),
    thrust::make_transform_iterator(last, square()),
    0.0f);
```

`reduce` sees a range of `float` and has no idea the values are being generated on the fly from a counter; the transform happens exactly once per element, exactly when it's consumed, with no buffer holding `i * i` for every `i` in between.

## Custom functors

Any callable with a device-side `operator()` — a lambda marked `__device__`, or a struct like `square` above — works as the operation passed to `transform`, `reduce`, `sort` (as a comparator), or `for_each`. This is how domain-specific logic plugs into Thrust's tuned algorithm skeletons without forking the library: the loop structure, the block/grid decomposition, and the memory access pattern are Thrust's; only the per-element operation is the caller's.

## Where Thrust stops

Thrust's abstraction has real edges, and knowing them is what keeps a codebase from fighting the library instead of using it.

- **No control over launch configuration.** Thrust picks the grid and block size for you; there's no parameter for "use 256 threads per block" the way a hand-written kernel launch has one.
- **No fusion across separate algorithm calls**, except through the iterator composition shown above. Two consecutive `thrust::transform` calls are two kernel launches and two passes over memory, not one — the library doesn't look across call boundaries to fuse them.
- **No in-kernel use.** Thrust algorithms are host-callable entry points, not something invokable from inside a `__global__` you're writing. That's exactly the gap [CUB](./cub.md) fills: block- and warp-level primitives meant to be called *inside* a kernel, which Thrust builds most of its own device-side implementation on top of.

## See also

- [CUB](./cub.md) — the in-kernel primitives layer beneath Thrust's algorithms, and the tool for the cases above the last bullet rules out.
- [Choosing a Library](./choosing-a-library.md) — where Thrust sits in the decision table against CUB, CUTLASS, and cuBLAS.
- [Reductions and Scans](../05-execution-and-synchronization/reductions-and-scans.md) — the hand-written reduction Thrust's `reduce` replaces for host-callable use.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
