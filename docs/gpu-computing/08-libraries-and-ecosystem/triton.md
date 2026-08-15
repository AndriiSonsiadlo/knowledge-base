---
id: triton
title: Triton
sidebar_label: Triton
sidebar_position: 12
tags: [gpu, cuda, libraries, triton]
---

# Triton

Writing a fused kernel in CUDA C++ means writing the fusion *and* everything around it: the thread-to-element mapping, the shared-memory staging, the vectorized loads, the bank-conflict-free layout. Most of that work is mechanical, most of it is where the bugs live, and none of it is the algorithm you actually wanted to express.

Triton removes that layer. You write Python describing what happens to a **block** of elements; the compiler decides how threads within the block divide the work, how loads are vectorized and coalesced, and how data is staged through shared memory. What you keep is the part that needs judgement — the tiling, the loop structure, the algorithm.

## A block-level programming model

The single idea worth internalizing: **a Triton program instance operates on a block of elements, not on one element.** In CUDA, `threadIdx` identifies a thread and you reason about what one thread does. In Triton, `tl.program_id` identifies a block and every value in the kernel is a vector spanning that block. There is no `threadIdx` because threads are not yours to address.

| You own | Triton owns |
|---|---|
| Block shape and tiling | Thread-to-element mapping within the block |
| The algorithm and loop structure | Vectorization and coalescing of loads/stores |
| Which data is loaded and when | Shared-memory staging and layout/swizzling |
| Masking at the boundaries | Register allocation and instruction scheduling |

This is why a Triton kernel is short. It is also why, when Triton's decisions are wrong for your case, there is no knob — the division of responsibility is the whole design.

## Loads, stores, and masks

Memory access is explicit and always pointer arithmetic on vectors. `tl.load(ptr + offsets, mask=..., other=...)` fetches the elements where `mask` is true and substitutes `other` elsewhere; `tl.store(ptr + offsets, value, mask=...)` writes only where the mask holds.

The mask is not optional bookkeeping. A block size is a compile-time constant, usually a power of two, and real tensors rarely divide evenly by it — so the last block always runs past the end of the data, and the mask is what makes that safe. Every load and store against a dimension that is not a multiple of the block size needs one.

The choice of `other` matters as much as the mask. For a maximum reduction it must be `-inf`; for a sum, `0`. Using the wrong identity gives a kernel that is correct on aligned shapes and wrong on ragged ones — which is the worst possible failure mode, because it passes the first test you write.

## A fused softmax

Softmax is the canonical example: a max reduction, a subtraction, an exponential, a sum reduction, and a division. In PyTorch that is five passes over memory; in Triton it is one.

```python showLineNumbers title="softmax.py"
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

Reading it line by line:

- `tl.program_id(0)` is the block index along the first launch dimension. The kernel is launched with one program per row, so `row` selects which row this instance owns.
- `tl.arange(0, BLOCK)` builds the vector `[0, 1, …, BLOCK-1]` of in-block offsets. `BLOCK` is `tl.constexpr`, so it is baked in at compile time and the compiler can unroll and vectorize against it.
- `mask = cols < n_cols` handles the ragged tail. `other=-float("inf")` is the identity for the max that follows — padding lanes cannot win it, and after `tl.exp` they contribute exactly zero to the sum.
- `x - tl.max(x, axis=0)` is the standard numerical-stability shift. Without it, `tl.exp` of a large logit overflows to infinity and the result is `nan`.
- The row is loaded **once** and everything after that happens in registers. That is the entire point: the max, the subtract, the exponential, the sum, and the divide all read from registers rather than from DRAM, so the kernel touches global memory twice — one read, one write — instead of ten times.

The launch supplies the grid and the block size:

```python
def softmax(x):
    n_rows, n_cols = x.shape
    out = torch.empty_like(x)
    BLOCK = triton.next_power_of_2(n_cols)
    softmax_kernel[(n_rows,)](out, x, x.stride(0), out.stride(0),
                              n_cols, BLOCK=BLOCK)
    return out
```

:::note[This version needs the row to fit in one block]
Because the whole row is held in registers, `BLOCK` must be at least `n_cols`, and a very wide row will exhaust the register file or fail to compile. Handling arbitrarily wide rows needs an online (streaming) softmax that keeps a running maximum and sum across several passes — the same restructuring that makes FlashAttention work. See [Softmax and LayerNorm](../13-applied-kernels-and-patterns/softmax-and-layernorm.md).
:::

## Autotuning

Block size and warp count decide performance and their best values depend on the shape and the hardware. `@triton.autotune` benchmarks a list of candidates and keeps the winner:

```python showLineNumbers
@triton.autotune(
    configs=[
        triton.Config({"BLOCK": 128},  num_warps=4),
        triton.Config({"BLOCK": 256},  num_warps=4),
        triton.Config({"BLOCK": 512},  num_warps=8),
        triton.Config({"BLOCK": 1024}, num_warps=8),
        triton.Config({"BLOCK": 2048}, num_warps=16),
    ],
    key=["n_cols"],
)
@triton.jit
def softmax_kernel(out_ptr, in_ptr, in_stride, out_stride,
                   n_cols, BLOCK: tl.constexpr):
    ...
```

`key` names the arguments that invalidate the cache: when `n_cols` changes, Triton re-runs the search; when it does not, the cached winner is reused. `num_warps` sets how many warps cooperate on one block — the closest thing Triton offers to a launch-configuration knob.

:::warning[Autotuning runs on the first call for each new key]
The search actually executes every config, so the first call with a new `n_cols` pays for all of them. In a benchmark loop that shows up as a wildly slow first iteration — warm up before timing, as [Benchmarking Methodology](../09-tooling-profiling-and-debugging/benchmarking-methodology.md) requires. In a serving path with many distinct shapes, it can mean repeated recompilation at unpredictable moments.
:::

## How it compares to raw CUDA

|  | Triton | CUDA C++ |
|---|---|---|
| **Control granularity** | Block: you choose tiles, the compiler maps threads | Thread: you control every lane and every access |
| **Boilerplate** | Very low — the softmax above is the whole kernel | High — indexing, staging, and bounds by hand |
| **Tensor cores** | Automatic for `tl.dot` on supported dtypes and shapes | Explicit, via WMMA/MMA or [CUTLASS](./cutlass.md) |
| **Debugging** | Limited: `TRITON_INTERPRET=1`, printing, no cuda-gdb | Full: [cuda-gdb and Compute Sanitizer](../09-tooling-profiling-and-debugging/cuda-gdb-and-sanitizers.md) |
| **Profiling** | Nsight sees the kernel, but source attribution is weaker | Full source-level attribution with `-lineinfo` |
| **Performance ceiling** | Reaches near-library speed on fused, memory-bound ops | Higher — nothing is out of reach |

The honest summary: on fused elementwise-and-reduction work — softmax, layer norm, attention variants, activation chains — Triton lands close to what a good hand-written kernel achieves, and gets there in a fraction of the code. On a tuned dense GEMM it does not match cuBLAS or CUTLASS, which are tuned per architecture against the SASS scheduler. That is the trade, and for most workloads it is a good one, because most workloads are not GEMM.

## Where it fits

Triton is the default first attempt when a fusion is needed and the operation is memory-bound. Reach past it when you need a hardware feature it does not expose, when you need the debugging and profiling tooling, or when the operation is a GEMM — in which case use a library, as [Choosing a Library](./choosing-a-library.md) argues.

:::tip[Read what the compiler already wrote]
`torch.compile` emits Triton. Setting `TORCH_LOGS="output_code"` prints the generated kernels, which is the fastest way to see exactly which operations Inductor fused and which it did not — and often the fastest way to learn idiomatic Triton, since the generated code is real, working, autotuned Triton for a problem you already understand.
:::

## See also

- [PyTorch CUDA Extensions](./pytorch-cuda-extensions.md) — the CUDA C++ route to the same goal, with autograd and stream handling.
- [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md) — why fusion is worth this much effort.
- [Softmax and LayerNorm](../13-applied-kernels-and-patterns/softmax-and-layernorm.md) — this kernel worked through as an optimization example.
- [Compiler Stacks](../12-npu-and-inference-accelerators/compiler-stacks.md) — where Triton sits among the other tensor compilers.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
