---
id: cuda-python-and-cupy
title: CUDA Python and CuPy
sidebar_label: CUDA Python & CuPy
sidebar_position: 9
tags: [gpu, cuda, libraries, python]
---

# CUDA Python and CuPy

Two different Python packages both answer to "CUDA in Python," and confusing them is the first mistake most people make. NVIDIA's `cuda-python` is a thin, official binding to the driver and runtime APIs — the same calls this section has been making in C++, now callable from Python. CuPy is a third-party, NumPy-compatible array library built on top of those bindings. Almost nobody wants the first one directly; almost everybody wants the second.

## Two different things

`cuda-python` (the `cuda.bindings` and newer `cuda.core` modules) exposes `cuMemAlloc`, `cuLaunchKernel`, and the rest of the driver API — and the `cudart`-equivalent runtime calls — as Python functions with the same signatures and the same manual bookkeeping as the C++ versions covered in [Runtime API vs Driver API](../06-cuda-runtime-and-apis/runtime-vs-driver-api.md). It exists mainly as a foundation for other libraries to build on, and as an escape hatch for code that needs a CUDA API call CuPy doesn't wrap. CuPy sits on top of it (and of libraries like cuBLAS and cuRAND) and presents an array type, `cupy.ndarray`, whose API mirrors `numpy.ndarray` closely enough that a large fraction of NumPy code runs on the GPU after changing one import line. Unless there's a specific reason to manage device memory and kernel launches by hand, CuPy is the one to reach for.

## CuPy as a NumPy replacement

```python
import cupy as cp

x = cp.random.rand(1 << 20, dtype=cp.float32)
y = cp.random.rand(1 << 20, dtype=cp.float32)
z = 2.0 * x + y                    # runs on the GPU
print(float(cp.sum(z)))            # implicit device-to-host sync
```

Every operation on `x` and `y` — the elementwise multiply-add, the reduction inside `cp.sum` — dispatches to a CUDA kernel instead of running on the CPU, and the arrays themselves live in device memory throughout. `cp.random`, `cp.linalg`, `cp.fft`, and most of the `ndarray` method set exist as near-drop-in equivalents of their NumPy counterparts.

:::warning[Converting to a Python scalar or a NumPy array synchronizes]
`float(cp.sum(z))`, `z.get()`, and `print(z)` all force a device-to-host transfer, which waits for every pending GPU operation to finish before it can happen. That's invisible in a script that does it once, but a `print` or a scalar conversion left inside a timing loop serializes the GPU behind the host on every iteration and destroys the measurement — the loop ends up timing host-device synchronization, not the kernels.
:::

## Writing kernels from Python

CuPy covers most array workloads without ever writing CUDA C++, but two escape hatches exist for the rest.

`cp.RawKernel` compiles a literal CUDA C++ source string with NVRTC on first use and caches the result; it's the same kernel code this section writes elsewhere, just launched from Python:

```python showLineNumbers
add_kernel = cp.RawKernel(r'''
extern "C" __global__
void my_add(const float* x1, const float* x2, float* y) {
    int tid = blockDim.x * blockIdx.x + threadIdx.x;
    y[tid] = x1[tid] + x2[tid];
}
''', 'my_add')

x1 = cp.arange(25, dtype=cp.float32).reshape(5, 5)
x2 = cp.arange(25, dtype=cp.float32).reshape(5, 5)
y = cp.zeros((5, 5), dtype=cp.float32)
add_kernel((5,), (5,), (x1, x2, y))   # grid, block, args
```

`cp.ElementwiseKernel` goes further and generates the boilerplate — the index computation, the bounds check, the type dispatch — from a type signature and a one-line body:

```python
squared_diff = cp.ElementwiseKernel(
    'T x, T y', 'T z',
    'z = (x - y) * (x - y)',
    'squared_diff')
```

`T` is a type placeholder CuPy resolves from the arguments at call time, so `squared_diff` works unmodified across `float32`, `float64`, and other dtypes without writing a separate kernel per type — something a hand-written `cp.RawKernel` would need explicit dispatch to do.

## Memory pools

CuPy pools device allocations by default rather than calling `cudaMalloc`/`cudaFree` on every array creation and destruction: freed memory is kept in a pool and reused for the next allocation of a compatible size instead of being returned to the driver. This is why `nvidia-smi` routinely reports more memory in use than the live arrays account for — the pool is holding freed blocks in reserve.

```python
mempool = cp.get_default_memory_pool()
print(mempool.used_bytes())     # bytes currently referenced by live arrays
print(mempool.total_bytes())    # used_bytes() plus cached, reusable blocks
mempool.free_all_blocks()       # return cached blocks to the driver
```

`used_bytes()` and `total_bytes()` are the pair to check when device memory usage doesn't match expectations, and `free_all_blocks()` is the way to actually release cached memory — useful before a large one-off allocation, or when handing the GPU to another process.

## Streams

`cp.cuda.Stream()` creates a stream the way `cudaStreamCreate` does in C++, and CuPy operations issued while a stream is the "current" one — inside a `with stream:` block — enqueue onto it instead of the default stream, the same overlap-and-ordering model [Runtime API vs Driver API](../06-cuda-runtime-and-apis/runtime-vs-driver-api.md) describes at the C++ level. `stream.synchronize()` blocks the host until everything queued on that stream completes, mirroring `cudaStreamSynchronize`.

## DLPack interop

DLPack is a tensor-exchange protocol that lets CuPy hand a device array to PyTorch, or accept one from it, without copying any data — both frameworks end up pointing at the same underlying device memory.

```python
import torch

tx = torch.randn(1, 2, 3, 4).cuda()
cx = cp.from_dlpack(tx)          # PyTorch tensor -> CuPy array, no copy
tx2 = torch.from_dlpack(cx)      # and back
```

This is the mechanism behind mixing a CuPy `RawKernel` into an otherwise-PyTorch pipeline — write the custom part in CuPy, exchange tensors at the boundary — which [PyTorch CUDA Extensions](./pytorch-cuda-extensions.md) covers as one of several ways to add a custom op.

## See also

- [Numba CUDA](./numba-cuda.md) — writing kernels directly in a restricted Python subset instead of a CUDA C++ string.
- [PyTorch CUDA Extensions](./pytorch-cuda-extensions.md) — the DLPack boundary from the PyTorch side, plus C++-based custom ops.
- [Runtime API vs Driver API](../06-cuda-runtime-and-apis/runtime-vs-driver-api.md) — the C++-level API `cuda-python` binds directly and CuPy builds on.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
