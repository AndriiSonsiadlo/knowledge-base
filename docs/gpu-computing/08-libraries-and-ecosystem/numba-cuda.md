---
id: numba-cuda
title: Numba CUDA
sidebar_label: Numba CUDA
sidebar_position: 10
tags: [gpu, cuda, libraries, numba]
---

# Numba CUDA

CuPy covers array operations, and `cp.RawKernel` covers the case where you need a real kernel — but that kernel is a CUDA C++ string embedded in a Python file, with no syntax highlighting, no type checking, and no debugger. Numba takes the other route: you write the kernel in Python, decorated with `@cuda.jit`, and Numba compiles that Python function to PTX at first call.

The result is the CUDA execution model with Python syntax. Threads, blocks, shared memory, and barriers are all still there and still mean exactly what they mean in C++ — what changes is that the kernel body is Python that an editor can read and a reader can follow without switching languages mid-file.

## Kernels in Python

SAXPY is the same program as [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md), rewritten:

```python showLineNumbers title="saxpy_numba.py"
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

Line for line, this is the C++ version. `@cuda.jit` replaces `__global__`. The square brackets in `saxpy[blocks, threads](...)` replace the `<<<blocks, threads>>>` launch syntax. The ceiling division and the `if i < x.size` guard are the same pair for the same reason — the block count rounds up, so the last block contains threads with no element to work on.

The differences are what Numba does for you. Array shape travels with the array, so `x.size` is available inside the kernel and the separate `n` parameter disappears. Device arrays created by `cuda.to_device` know their own dtype and shape, so there is no `sizeof` arithmetic and no untyped `void*`. And there is no explicit free: the device array is a Python object, released when it goes out of scope.

## Indexing

`cuda.grid(1)` is a wrapper over the index arithmetic that [Thread Indexing](../03-cuda-programming-model/thread-indexing.md) derives — it returns exactly `cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x`. `cuda.grid(2)` returns a tuple of two indices for a 2-D launch, which is where it earns its keep:

```python
@cuda.jit
def transpose(src, dst):
    row, col = cuda.grid(2)
    if row < src.shape[0] and col < src.shape[1]:
        dst[col, row] = src[row, col]
```

`cuda.gridsize(1)` returns the total thread count across the grid, which is the stride for a grid-stride loop — the pattern that lets one launch configuration handle any input size:

```python
@cuda.jit
def scale(x, factor):
    start = cuda.grid(1)
    stride = cuda.gridsize(1)
    for i in range(start, x.size, stride):
        x[i] *= factor
```

The raw `cuda.threadIdx.x`, `cuda.blockIdx.x`, and `cuda.blockDim.x` are all still available when you need them directly.

## Memory management

`cuda.to_device(arr)` copies a NumPy array to the device and returns a device array; `.copy_to_host()` brings it back. Passing a plain NumPy array straight to a kernel also works — Numba copies it in before the launch and back afterwards — which is convenient and quietly expensive:

:::warning[Implicit transfers happen on every launch]
A kernel called with NumPy arrays transfers them to the device before the launch and back after it, *every time it is called*. In a loop, that is a host-to-device and device-to-host round trip per iteration, and the transfers will dominate the kernel entirely. Call `cuda.to_device` once outside the loop and pass device arrays in.
:::

`cuda.device_array(shape, dtype)` allocates on the device without copying anything, for outputs that have no meaningful initial value. `cuda.pinned_array` allocates page-locked host memory, the prerequisite for the asynchronous copies described in [Pinned Memory and Host Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md).

## Shared memory and atomics

The on-chip primitives are all present under the same names:

```python showLineNumbers
from numba import cuda, float32

TPB = 128

@cuda.jit
def block_sum(x, out):
    buf = cuda.shared.array(TPB, dtype=float32)

    tid = cuda.threadIdx.x
    i = cuda.grid(1)
    buf[tid] = 0.0
    if i < x.size:
        buf[tid] = x[i]
    cuda.syncthreads()

    stride = cuda.blockDim.x // 2
    while stride > 0:
        if tid < stride:
            buf[tid] += buf[tid + stride]
        cuda.syncthreads()
        stride //= 2

    if tid == 0:
        cuda.atomic.add(out, 0, buf[0])
```

`cuda.shared.array(shape, dtype)` declares the block's shared memory, and its shape must be a **compile-time constant** — `TPB` here is a module-level literal, not a kernel argument. This is the same restriction as a statically sized `__shared__` array in C++, and it is the most common surprise when porting: you cannot size shared memory from a runtime value.

`cuda.syncthreads()` is `__syncthreads()`, with the same rule that every thread in the block must reach it. `cuda.atomic.add(array, index, value)` is `atomicAdd`, taking the array and index separately rather than a pointer.

## What Numba cannot do

The kernel body is a **restricted subset of Python**, not Python. Inside `@cuda.jit` there are no classes, no dynamic allocation, no list or dict construction, no exceptions, no string operations, and no calls into arbitrary Python libraries — only NumPy-style array indexing, scalar math, and calls to other Numba-compiled functions. Code that strays outside the subset fails at compile time, which is at least loud, but the boundary is not always where you would guess.

The control you give up matters at the margin: no `__launch_bounds__` equivalent to cap register usage, no direct control over the L1/shared split, no inline PTX in the general case, and no access to the newer hardware features — the tensor-core and asynchronous-copy paths from [Programming Tensor Cores](../07-kernel-optimization/programming-tensor-cores.md) and [Asynchronous Data Movement](../04-cuda-memory-model/asynchronous-data-movement.md) are not expressible. On simple memory-bound kernels the generated code is competitive; on complex kernels where occupancy and register pressure decide the outcome, there is a real gap, and no knob to close it.

:::tip[Use it where it belongs]
Numba is excellent for two things: prototyping a kernel quickly, and shipping a kernel that lives inside an otherwise-Python pipeline where a C++ build step would be the largest cost in the project. Both are common and both are legitimate. When the kernel becomes the bottleneck and you need the last factor of two, port it — to CUDA C++ via [PyTorch CUDA Extensions](./pytorch-cuda-extensions.md), or to [Triton](./triton.md) if it is a fusable block-level operation.
:::

## See also

- [CUDA Python and CuPy](./cuda-python-and-cupy.md) — array-level GPU work, and `cp.RawKernel` as the CUDA C++ alternative to `@cuda.jit`.
- [Triton](./triton.md) — the other Python kernel language, at block granularity instead of thread granularity.
- [Thread Indexing](../03-cuda-programming-model/thread-indexing.md) — the index arithmetic `cuda.grid()` wraps.
- [Your First Kernel](../03-cuda-programming-model/your-first-kernel.md) — the CUDA C++ SAXPY this page mirrors.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
