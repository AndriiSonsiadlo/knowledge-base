---
id: ptx-and-inline-assembly
title: PTX and Inline Assembly
sidebar_label: PTX & Inline Asm
sidebar_position: 10
tags: [gpu, cuda, optimization, ptx]
---

# PTX and Inline Assembly

Almost every optimization in this section works through the C++ source and trusts `nvcc` to generate good machine code from it. Occasionally that trust runs out — an instruction has no intrinsic, or the compiler's chosen code sequence needs to be inspected or overridden directly — and the only way forward is reading or writing below the C++ level. This page covers both: reading the SASS a kernel actually compiles to, and, rarely, writing PTX by hand to reach an instruction the compiler won't emit on its own.

## PTX is not the machine code

[The Compilation Model](../03-cuda-programming-model/the-compilation-model.md) lays out the full pipeline: PTX is a virtual ISA that device code compiles to first, `ptxas` compiles that PTX into SASS for a specific architecture, and `ptxas` optimizes aggressively in the process — so the PTX a kernel produces is not what runs on the GPU, and reasoning about performance from PTX alone can be misleading.

## Reading SASS

The same inspection commands [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md) introduces apply here directly:

```bash
cuobjdump -sass ./kernel        # disassembled SASS
nvdisasm -c kernel.cubin        # control-flow annotated
```

The following is a representative sample of the kind of output those commands produce for a tiled kernel's inner loop — not a captured compile, but illustrative of the instruction classes worth recognizing:

```text
/*0058*/  LDG.E.128 R4, [R8];              // vectorized 128-bit global load
/*0068*/  LDS R12, [R20];                  // shared-memory load
/*0070*/  FFMA R16, R4, R12, R16;          // fused multiply-add, FP32
/*0078*/  HFMA2 R18, R6, R14, R18;         // fused multiply-add, packed FP16 pair
/*0088*/  BAR.SYNC 0x0;                    // block-wide barrier (__syncthreads)
```

`LDG.E.128` is a coalesced, vectorized global load moving 128 bits (four FP32 elements) in one instruction rather than four separate 32-bit loads — see [Memory Access Optimization](./memory-access-optimization.md) for why vectorizing loads this way matters. `LDS` is a shared-memory load. `FFMA` and `HFMA2` are fused multiply-add on FP32 and packed FP16 pairs respectively — seeing `FFMA` where the source wrote a separate multiply and add confirms contraction happened, per [Instruction-Level Optimization](./instruction-level-optimization.md). `BAR.SYNC` is the SASS a `__syncthreads()` call compiles to.

## Inline PTX

For the rare case where no intrinsic reaches a specific instruction, `asm` embeds PTX directly in device code:

```cpp showLineNumbers
__device__ float fmaRn(float a, float b, float c) {
    float d;
    asm volatile("fma.rn.f32 %0, %1, %2, %3;"
                 : "=f"(d)
                 : "f"(a), "f"(b), "f"(c));
    return d;
}
```

`%0`–`%3` map positionally onto the operand list that follows the instruction string: outputs first, then inputs, in the order they're listed.

## Constraints and clobbers

Each operand's constraint letter tells the compiler which register class to allocate and how it's used:

| Constraint | Meaning |
|---|---|
| `h` | 16-bit register |
| `r` | 32-bit integer register |
| `l` | 64-bit integer register |
| `f` | 32-bit float register |
| `d` | 64-bit float register |
| `=` (prefix) | write-only operand |
| `+` (prefix) | read-write operand |

`volatile` on the `asm` statement stops the compiler from reordering, moving, or eliding the instruction as dead code — without it, an `asm` block with no observed output can simply disappear under optimization the same way any other dead code can. A `"memory"` clobber tells the compiler the instruction has side effects on memory it can't see from the operand list alone — necessary for anything that reads or writes through a pointer the constraint list doesn't capture — and forces the compiler to avoid reordering ordinary loads/stores across it.

## `cuda::ptx` helpers

Raw `asm` strings are untyped, unchecked by the compiler beyond the constraint syntax, and easy to get subtly wrong. `cuda::ptx`, part of libcu++, is the preferred modern route for the instructions it covers: typed, documented wrapper functions over specific PTX instructions — `cp.async.bulk`, `mbarrier` operations, and others — that give normal C++ overload resolution and type checking instead of a hand-written asm string. Code reaching for one of the instructions `cuda::ptx` wraps should use the wrapper rather than write raw `asm` for it.

:::warning[Inline PTX blocks optimization across it]
An `asm` block is opaque to the compiler: it cannot be scheduled around, reordered with, or optimized together with surrounding instructions the way ordinary C++ can, and it pins the kernel to whatever instruction availability the target architecture happens to have. It is justified for instructions with no intrinsic and no `cuda::ptx` wrapper — a specific `mbarrier` operation, `redux.sync`, a cache-hint load variant — and almost never justified for ordinary arithmetic, where the compiler's own instruction selection is already good.
:::

## When this is justified

Reach for inline PTX or `cuda::ptx` only after confirming, via the SASS, that the compiler isn't already emitting the instruction sequence wanted — not from a guess about what the compiler "should" do. [Nsight Compute](../09-tooling-profiling-and-debugging/nsight-compute.md) and the disassembly commands above are how that gets confirmed before reaching for either tool.

## See also

- [The Compilation Model](../03-cuda-programming-model/the-compilation-model.md) — the PTX-to-SASS pipeline this page reads and occasionally bypasses.
- [Instruction-Level Optimization](./instruction-level-optimization.md) — checking the SASS for contraction, unrolling, and independent accumulators, the same technique this page applies more broadly.
- [Nsight Compute](../09-tooling-profiling-and-debugging/nsight-compute.md) — confirming an instruction-level problem is real before reaching for `asm`.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
