---
id: inline-assembly
title: Inline Assembly
sidebar_label: Inline Assembly
sidebar_position: 6
tags: [cpp, assembly, inline-asm, gcc, clang, msvc, intrinsics, low-level]
---

# Inline Assembly

Inline assembly puts a few machine instructions inside a C++ function: a CPU instruction the language has no
spelling for (`rdtsc`, `cpuid`, a system-register read), or an instruction sequence the compiler would not
choose. It is the last resort: it is tied to one instruction set and one compiler family, it blocks
optimisations around it, and the compiler cannot check what the text does. Most of the time an
intrinsic, a standard-library function or `std::atomic` does the same job better.

**Prerequisites:** [Calling conventions](../04-functions-and-call-mechanics/calling-conventions.md)
(registers, which the constraints below hide) and [Reading assembly](../14-debugging-and-profiling/07-reading-assembly.md).

## What the standard says

The language has an *asm-declaration*, `asm("text");`, and says its meaning is **implementation-defined**
([dcl.asm]). Everything below is therefore compiler documentation, not C++:

| Compiler family | Form | Notes |
|---|---|---|
| GCC, Clang (every target they support) | `asm("...")` and extended `asm("..." : outputs : inputs : clobbers)` | The syntax is the same on x86, AArch64, RISC-V, and so on. The instruction text and the constraint letters are per architecture. |
| MSVC, x86 (32-bit) only | `__asm { ... }` blocks | Microsoft's documentation says [inline assembly is not supported on ARM and x64](https://learn.microsoft.com/en-us/cpp/assembler/inline/inline-assembler). Use intrinsics or a separate `.asm` file |

All examples below are GCC/Clang extended asm for x86-64, compiled with g++ 15.2 and clang++ 21.1 in the
default AT&T syntax (`-masm=intel` switches it). AT&T order is `op source, destination`.

## Extended asm: telling the compiler what the code does

The compiler treats the template string as opaque text. Operands tell it how the code connects to C++
variables, and clobbers tell it what else the code changes. Get either wrong and the program miscompiles
silently, at some optimisation level.

```cpp title="add.cpp" showLineNumbers
#include <cstdint>
#include <cstdio>

int add(int a, int b) {
    asm("addl %[rhs], %[acc]"
        : [acc] "+r"(a)             // read-write: starts as a, ends as the sum
        : [rhs] "r"(b)
        : "cc");                    // the add changes the flags register
    return a;
}

std::uint64_t rdtsc() {
    std::uint32_t lo, hi;
    asm volatile("rdtsc" : "=a"(lo), "=d"(hi));      // the instruction writes eax and edx
    return std::uint64_t{hi} << 32 | lo;
}

int bsr32(std::uint32_t x) {                         // index of highest set bit; x must not be 0
    int r;
    asm("bsrl %1, %0" : "=r"(r) : "rm"(x) : "cc");
    return r;
}

int main() {
    std::printf("%d %d\n", add(40, 2), bsr32(0x80));
    std::uint64_t t0 = rdtsc(), t1 = rdtsc();
    std::printf("%d\n", t1 >= t0);
}
```

```text
42 7
1
```

(g++ 15 and clang++ 21, `-std=c++20 -Wall -Wextra`, `-O0` and `-O2`, x86-64 Linux; the second line depends on
the TSC being monotonic on the machine, which cannot be guaranteed across CPU migration.)

The three parts after the template, separated by colons:

- **Outputs** `[name] "constraint"(lvalue)`. `=` means write-only, `+` read-write. The compiler picks a
  location satisfying the constraint, then copies the result into the C++ variable.
- **Inputs** `[name] "constraint"(expression)`. The compiler loads the value into the chosen location first.
- **Clobbers**: registers or state the code changes that are *not* listed as outputs: register names (`"rax"`),
  `"cc"` (the condition-code register) and `"memory"`.

Operands are referred to as `%0`, `%1`, ... in order, or by the `%[name]` you give them, which survives
reordering. A literal `%` in the template is written `%%` (so `%%eax` is the register `eax`).

Common x86 constraints (GCC machine-constraints documentation lists the rest, per architecture):

| Constraint | Meaning on x86 |
|---|---|
| `r` | Any general register |
| `a`, `b`, `c`, `d`, `S`, `D` | Specifically `eax/rax`, `ebx`, `ecx`, `edx`, `esi`, `edi` |
| `m` | A memory operand |
| `i` | A constant known at compile time |
| `rm` | Register or memory, compiler's choice |
| `=` / `+` / `&` | Write-only / read-write / early-clobber output (the output may be written before all inputs are read, so it must not share a register with them) |

### What goes wrong

Hand-written constraints are the usual source of bugs. Typical ones:

- **Naming a register in the template without listing it.** Writing `movl $5, %%eax` without clobbering `eax` lets the
  compiler keep a live value in it. g++ 15 accepted this without a diagnostic. Use an output operand and let
  the compiler choose the register.
- **Leaving out `"cc"`** on an instruction that sets flags (GCC's documentation: it names the flags register and is valid on every target, a no-op where flags are not tracked separately).
- **Reading an output before the inputs are consumed**, which is what `&` is for.
- **Writing memory the compiler does not know about** (next section).

### `volatile` on an asm statement

Without `volatile`, the compiler treats the asm as a pure function of its inputs: it may delete it if the outputs
are unused, hoist it out of a loop, or merge two copies. GCC's documentation says an asm statement with no output
operands is implicitly volatile. Mark `asm volatile` any statement with an effect beyond its outputs: `rdtsc` (a
different value each call), an I/O instruction, a barrier. `volatile` here is a different feature from the type
qualifier on [the volatile page](./05-volatile.md), but the same idea: the compiler must not drop or duplicate
it. It still does not stop the compiler from *moving* the asm relative to ordinary code.

### The `"memory"` clobber is a compiler barrier, not a CPU barrier

`"memory"` tells the compiler the asm may read or write any memory, so cached values must be written out and
reloaded around it. It generates no instruction. In this test (g++ 15.2, `-O2`, x86-64):

```cpp title="clob.cpp" showLineNumbers
int flag;
int without()             { flag = 1;                              int a = flag; flag = 2; return a; }
int with_compiler_barrier() { flag = 1; asm volatile("" ::: "memory"); int a = flag; flag = 2; return a; }
```

```text
without:                 mov DWORD PTR flag[rip], 2 ; mov eax, 1     (the load and first store are folded away)
with_compiler_barrier:   mov DWORD PTR flag[rip], 1 ; mov eax, DWORD PTR flag[rip] ; mov DWORD PTR flag[rip], 2
```

The empty asm with the clobber forces the store and reload. It does nothing to the processor: another core
can still see the writes in a different order. Hardware ordering needs a fence instruction (`mfence` on x86),
and that is what `std::atomic_thread_fence` and the `memory_order` arguments give you portably. See
[Atomics and fences](../11-concurrency-and-memory-model/02-atomics-and-fences.md). Do not write your own
compare-and-swap or spin-lock in asm; `std::atomic` compiles to the right instruction (`lock cmpxchg` on
x86-64) for the target, and the optimiser understands it.

## Prefer intrinsics

An **intrinsic** is a function the compiler recognises and expands to one or a few instructions, with correct
operand and register handling and full knowledge of its effects. Instead of the asm above:

| Task | Intrinsic or library | Header |
|---|---|---|
| Time-stamp counter | `__rdtsc()` | `<x86intrin.h>` (GCC, Clang), `<intrin.h>` (MSVC) |
| Spin-wait hint | `_mm_pause()` | `<immintrin.h>` |
| Bit scan, popcount, rotate | `std::countl_zero`, `std::popcount`, `std::rotl` *(C++20, `<bit>`)* | `<bit>` |
| Byte swap | `std::byteswap` *(C++23)*, see [Endianness](./04-endianness.md) | `<bit>` |
| SIMD arithmetic | `_mm256_add_ps` and similar | `<immintrin.h>` |
| Atomic read-modify-write, fences | `std::atomic`, `std::atomic_thread_fence` | `<atomic>` |
| Prefetch | `__builtin_prefetch(p)` (GCC, Clang) | none |

Intrinsics are architecture-specific too (x86 intrinsics do not exist on AArch64, which has its own in
`<arm_neon.h>` and `<arm_acle.h>`), but they work with MSVC on x64 where inline asm does not, and the
optimiser can schedule, inline and constant-fold them.

When there is no intrinsic and the instruction is a system operation, a separate assembly file (`.S` or `.s`),
assembled and linked with the program, is often cleaner than inline asm in a C++ function. The calling convention
of the surrounding page applies; see [Calling conventions](../04-functions-and-call-mechanics/calling-conventions.md).

## Other targets

The extended-asm syntax is identical on other architectures; constraints and mnemonics change. The same
`add` for AArch64, compiled to assembly only with `clang++ --target=aarch64-linux-gnu -S` (not run on this x86 machine):

```cpp title="add-aarch64.cpp (AArch64 only)"
int add(int a, int b) { asm("add %w0, %w0, %w1" : "+r"(a) : "r"(b)); return a; }
```

It emitted an `add w8, w8, w9` in the `-O0` output. Code with inline asm therefore needs a guard such as
`#if defined(__x86_64__)` and a portable fallback; `static_assert` or `#error` in the `#else` branch if there is none.

## When to use it

| Situation | Use |
|---|---|
| An instruction that has an intrinsic or a `<bit>`/`<atomic>` function | That function |
| Atomic operations, fences, spin-lock hints | `std::atomic`, `std::atomic_thread_fence`, `_mm_pause` |
| A system instruction with no intrinsic (a control or system register, `cpuid` on a compiler without one) | Inline asm, guarded by architecture, with exact constraints |
| Speeding up a hot loop | Profile first; prefer intrinsics or letting the vectoriser work, and verify with a benchmark. Hand asm often loses to the compiler's output and blocks inlining of the surrounding code |

## Key points

- `asm` is implementation-defined in C++; GCC and Clang share extended-asm syntax across architectures.
  MSVC supports inline asm only for 32-bit x86.
- The template is opaque. Operands and clobbers (`"cc"`, registers, `"memory"`) are the only information the compiler has.
  Wrong ones miscompile at some optimisation level, silently.
- `asm volatile` for effects beyond the outputs. `"memory"` is a compiler barrier, never a hardware fence.
- Prefer intrinsics, `<bit>` and `std::atomic`; keep asm for what they cannot express, behind an architecture guard.

## References

- [GCC: Extended asm](https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html) (operands, clobbers, `volatile`)
- [GCC: Constraints for particular machines](https://gcc.gnu.org/onlinedocs/gcc/Machine-Constraints.html)
- [Microsoft: Inline assembler](https://learn.microsoft.com/en-us/cpp/assembler/inline/inline-assembler)
- [cppreference: `asm` declaration](https://en.cppreference.com/w/cpp/language/asm)
