---
id: pytorch-cuda-extensions
title: PyTorch CUDA Extensions
sidebar_label: PyTorch Extensions
sidebar_position: 11
tags: [gpu, cuda, libraries, pytorch]
---

# PyTorch CUDA Extensions

PyTorch composes: nearly anything can be built from existing operators. What composition cannot always give you is *one kernel*. A sequence of PyTorch ops writes every intermediate tensor to global memory and reads it back for the next op, so a chain of cheap elementwise operations spends almost all its time moving data — the problem [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) covers in general.

A CUDA extension is the escape hatch: your own kernel, compiled against PyTorch's C++ API, callable from Python as an ordinary function, operating directly on tensor memory with no copies at the boundary.

## Why write an extension

There are three honest reasons, and a great many bad ones.

| Reason | Example |
|---|---|
| **Fusion the framework cannot express** | A normalization, a bias add, and an activation that should be one pass over memory |
| **An irregular access pattern** | A gather or scatter over a structure PyTorch's indexing turns into several passes |
| **An operation that does not exist** | A novel attention variant, a custom quantization scheme, a domain-specific reduction |

:::tip[Check that the compiler has not already done it]
`torch.compile` fuses elementwise chains and many reductions automatically, emitting [Triton](./triton.md) kernels. Before writing an extension, compile the module and look at what came out — if Inductor already fused the pattern into one kernel, a hand-written extension buys nothing and costs a build system. Extensions earn their place when the pattern is beyond what the compiler will fuse.
:::

## `load_inline` for iteration

`torch.utils.cpp_extension.load_inline` takes CUDA C++ as a Python string, compiles it on first call, caches the result, and returns a module. There is no build file and no separate compile step, which makes it the right way to iterate:

```python showLineNumbers title="fused_relu.py"
import torch
from torch.utils.cpp_extension import load_inline

cuda_source = r"""
#include <torch/extension.h>
#include <c10/cuda/CUDAStream.h>

__global__ void add_relu_kernel(const float* __restrict__ a,
                                const float* __restrict__ b,
                                float* __restrict__ out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        float v = a[i] + b[i];
        out[i] = v > 0.f ? v : 0.f;
    }
}

torch::Tensor add_relu(torch::Tensor a, torch::Tensor b) {
    TORCH_CHECK(a.is_cuda() && b.is_cuda(), "inputs must be CUDA tensors");
    TORCH_CHECK(a.sizes() == b.sizes(), "size mismatch");
    a = a.contiguous();
    b = b.contiguous();

    auto out = torch::empty_like(a);
    const int n = a.numel();
    const int threads = 256;
    const int blocks = (n + threads - 1) / threads;

    auto stream = c10::cuda::getCurrentCUDAStream();
    add_relu_kernel<<<blocks, threads, 0, stream>>>(
        a.data_ptr<float>(), b.data_ptr<float>(),
        out.data_ptr<float>(), n);
    return out;
}
"""

mod = load_inline(name="fused", cuda_sources=cuda_source,
                  functions=["add_relu"], verbose=True)

a = torch.randn(1 << 20, device="cuda")
b = torch.randn(1 << 20, device="cuda")
torch.testing.assert_close(mod.add_relu(a, b), torch.relu(a + b))
```

Two details in that kernel are not decoration. `a.contiguous()` is necessary because `data_ptr` hands you a raw pointer with no stride information — a non-contiguous tensor read through it silently produces garbage. And `TORCH_CHECK` raises a Python exception rather than letting a wrong-device tensor become an illegal memory access somewhere inside the kernel.

## setuptools for shipping

`load_inline` compiles at import time on the user's machine, which is fine for development and wrong for a package. For shipping, `setup.py` with `CUDAExtension` builds ahead of time:

```python showLineNumbers title="setup.py"
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name="myops",
    ext_modules=[
        CUDAExtension(
            name="myops._C",
            sources=["csrc/bindings.cpp", "csrc/fused_kernels.cu"],
            extra_compile_args={"cxx": ["-O3"],
                                "nvcc": ["-O3", "-lineinfo"]},
        )
    ],
    cmdclass={"build_ext": BuildExtension},
)
```

`CUDAExtension` handles the include paths, the library paths, and the ABI flags that must match the PyTorch build. `-lineinfo` in the `nvcc` flags costs essentially nothing and is what makes the source-level view in [Nsight Compute](../09-tooling-profiling-and-debugging/nsight-compute.md) work later.

## Tensor accessors

`data_ptr<float>()` gives a bare pointer and loses everything the tensor knew about itself. For anything with more than one dimension, the accessor is better:

```cpp showLineNumbers
__global__ void row_scale_kernel(
    torch::PackedTensorAccessor32<float, 2, torch::RestrictPtrTraits> x,
    const torch::PackedTensorAccessor32<float, 1, torch::RestrictPtrTraits> s) {
    const int row = blockIdx.x;
    const int col = threadIdx.x + blockIdx.y * blockDim.x;
    if (row < x.size(0) && col < x.size(1)) {
        x[row][col] *= s[row];
    }
}

// host side:
row_scale_kernel<<<grid, block, 0, stream>>>(
    x.packed_accessor32<float, 2, torch::RestrictPtrTraits>(),
    s.packed_accessor32<float, 1, torch::RestrictPtrTraits>());
```

The accessor carries sizes and strides into the kernel, so `x[row][col]` does the correct strided arithmetic and `x.size(0)` is available for the bounds check. `RestrictPtrTraits` marks the underlying pointers `__restrict__`, which tells the compiler they do not alias — that is what allows it to keep values in registers across stores instead of reloading defensively, and a raw `float*` throws the information away. The `32` selects 32-bit indexing, which is faster and correct for any tensor with under 2³¹ elements; use `packed_accessor64` above that.

## Autograd integration

An extension is only half an operator until it has a gradient. `torch.autograd.Function` supplies one:

```python showLineNumbers
class FusedAddReLU(torch.autograd.Function):
    @staticmethod
    def forward(ctx, a, b):
        out = mod.add_relu(a, b)
        ctx.save_for_backward(out)
        return out

    @staticmethod
    def backward(ctx, grad_out):
        (out,) = ctx.saved_tensors
        grad = grad_out * (out > 0)     # ReLU passes gradient where it was active
        return grad, grad               # one gradient per forward input

fused_add_relu = FusedAddReLU.apply
```

`backward` returns exactly as many values as `forward` took inputs, in the same order, with `None` for anything that does not require a gradient. The C++ equivalent, `torch::autograd::Function` with static `forward` and `backward` methods, has the same shape and is used when the whole op lives on the C++ side.

:::tip[Check the gradient, do not assume it]
`torch.autograd.gradcheck(fused_add_relu, (a.double().requires_grad_(), b.double().requires_grad_()))` compares your analytic backward against finite differences. A wrong backward does not crash — it trains a slightly wrong model, which is far more expensive to discover later.
:::

## Stream semantics

This is the correctness trap of the whole page, and it is silent when you get it wrong.

:::warning[Launch on the current stream, never the default one]
`myKernel<<<blocks, threads>>>(...)` with no stream argument launches on the **default stream**. PyTorch does not run on the default stream in general — it has its own current stream per device, and under CUDA graph capture, `torch.cuda.stream()` blocks, or DataParallel it is definitely not the default one.

A kernel on the wrong stream has no ordering relationship with the tensors it reads. It can start before the op that produces its input has finished, and it will usually appear to work anyway — the race only loses when timing shifts. Always fetch and pass the current stream:

```cpp
auto stream = c10::cuda::getCurrentCUDAStream();
myKernel<<<blocks, threads, 0, stream>>>(/* ... */);
```

The same applies to every `cudaMemcpyAsync` in the op.
:::

Allocations have a matching rule: use `torch::empty`/`torch::empty_like` rather than raw `cudaMalloc`, so the memory comes from PyTorch's caching allocator and is tracked, stream-aware, and visible to `torch.cuda.memory_allocated()`.

## See also

- [Triton](./triton.md) — the same fusion goal with far less boilerplate, and what `torch.compile` emits.
- [CUDA Python and CuPy](./cuda-python-and-cupy.md) — the DLPack boundary, for mixing a CuPy kernel into a PyTorch pipeline.
- [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) — why fusing is worth this much trouble.
- [GPU Training and Mixed Precision](../../machine-learning/02-deep-learning/gpu-training-and-mixed-precision.md) — the training-side view of the framework these extensions plug into.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
