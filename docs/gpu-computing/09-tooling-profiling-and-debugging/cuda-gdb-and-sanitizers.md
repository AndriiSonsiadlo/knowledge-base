---
id: cuda-gdb-and-sanitizers
title: cuda-gdb and Compute Sanitizer
sidebar_label: Debugging & Sanitizers
sidebar_position: 4
tags: [gpu, cuda, tooling, debugging]
---

# cuda-gdb and Compute Sanitizer

A kernel that reads garbage, writes out of bounds, or produces different output run to run is a different kind of problem from a slow one, and [Nsight Compute](./nsight-compute.md) is the wrong tool for it — a profiler reports how fast something ran, not whether it was correct. cuda-gdb steps through device code the way `gdb` steps through host code; Compute Sanitizer is a family of runtime checkers that catch specific classes of memory and synchronization bugs without stepping through anything at all.

## Compiling for debug

`-g -G` produces full device debug information and disables device-side optimization, which is what makes single-stepping and variable inspection in cuda-gdb reliable. `-lineinfo` alone — the same flag [Building CUDA with CMake](./building-cuda-with-cmake.md) recommends for Nsight Compute — embeds source line correlation without disabling optimization, which is what the sanitizer tools below need to report line numbers at close to full speed.

:::warning[`-G` changes the kernel it's debugging]
Disabling device optimization means the compiled code is not the code that ships, so timing measurements taken under `-G` are meaningless — a kernel can look many times slower under `-G` than in a release build. It can also change *correctness* behavior: some data races depend on instruction scheduling and reordering that the optimizer performs, and a race that reproduces reliably in a release build can vanish under `-G` because the unoptimized code happens to serialize the racing accesses. Reach for `-lineinfo` and the sanitizers first; use `-g -G` and cuda-gdb when a bug needs to be caught mid-execution and inspected.
:::

## cuda-gdb

cuda-gdb extends `gdb` with CUDA-specific commands for switching focus between threads and blocks on the device:

```text
break kernel.cu:42
cuda block (1,0,0) thread (0,0,0)
info cuda threads
p var
```

`break kernel.cu:42` sets a breakpoint on a source line inside device code, same as a host breakpoint. `cuda block (1,0,0) thread (0,0,0)` switches the debugger's focus to a specific thread within a specific block, so subsequent commands inspect that thread's state. `info cuda threads` lists resident threads and which ones are currently stopped at the breakpoint, grouped by their program counter. `p var` prints a variable's value in the currently focused thread, exactly like host `gdb`.

## Compute Sanitizer

Compute Sanitizer runs a kernel under dynamic instrumentation and checks every memory access or synchronization event against a specific class of bug as it happens, rather than requiring a human to notice wrong output and go looking. It ships four tools, selected with `--tool`, each catching a different class of bug:

```bash
compute-sanitizer --tool memcheck   ./gpuapp   # out-of-bounds, misaligned access
compute-sanitizer --tool racecheck  ./gpuapp   # shared-memory data races
compute-sanitizer --tool initcheck  ./gpuapp   # reads of uninitialized device memory
compute-sanitizer --tool synccheck  ./gpuapp   # divergent or illegal __syncthreads
```

## memcheck

`memcheck` catches out-of-bounds and misaligned global, local, and shared memory accesses, along with invalid `free`/`malloc` pairing on device memory. It's the closest device-side equivalent to a host memory sanitizer, and it's the tool to reach for first when a kernel produces wrong values or crashes intermittently — an out-of-bounds write from one thread corrupting a completely unrelated array is a common source of symptoms that look nothing like their actual cause.

## racecheck

`racecheck` detects data races on shared memory: two threads in the same block accessing the same shared-memory location without a `__syncthreads()` (or equivalent) enforcing an order between them, where at least one access is a write. These races are the ones most likely to produce correct-looking output on the machine that wrote the kernel and wrong output somewhere else, because whether the race actually manifests depends on scheduling that varies across GPU generations and occupancy.

## initcheck and synccheck

`initcheck` flags reads of device global memory that was allocated but never written — a value that happens to be zero on one run and garbage on the next, which is otherwise invisible until it isn't. `synccheck` flags illegal or divergent use of `__syncthreads()` and related barrier intrinsics: every thread in a block must reach the same barrier call, and a barrier inside a divergent branch that not all threads take is undefined behavior that `synccheck` catches directly instead of leaving it to manifest as an intermittent hang. See [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md) for what a barrier is actually guaranteeing.

## Reading a report

```text
========= COMPUTE-SANITIZER
========= Invalid __global__ write of size 4 bytes
=========     at 0x00000230 in kernels.cu:57:saxpy(int, float, float const*, float*)
=========     by thread (127,0,0) in block (4,0,0)
=========     Address 0x7f2a4a001000 is out of bounds
=========     Saved host backtrace up to driver entry point at kernel launch time
=========     Host Frame: ... in main.cu:23
=========
========= ERROR SUMMARY: 1 error
```

The first two lines name the violation and its size — a 4-byte write past the end of an array here. The `kernels.cu:57` line is the exact source line, available because the binary was built with `-lineinfo` or `-G`; without either, this line is a bare address. `thread (127,0,0) in block (4,0,0)` identifies precisely which of the launch's threads made the bad access, which for a bounds bug is usually the last thread in the last block — the tail case that a quick manual test with a "nice" input size never exercises. The host backtrace at the bottom shows the launch site in `main.cu`, tying the device-side fault back to the specific kernel call that triggered it.

:::tip[Run memcheck and racecheck in CI]
Both tools catch classes of bug that produce correct-looking output on the machine that wrote the kernel and wrong output on someone else's — an out-of-bounds read that happens to land in still-allocated memory, or a race whose outcome depends on scheduling that differs by GPU generation or occupancy. Running `memcheck` and `racecheck` in CI against a small input catches these before they reach hardware where they'd actually misbehave.
:::

## See also

- [Error Handling and Checking](../06-cuda-runtime-and-apis/error-handling.md) — the `CUDA_CHECK` pattern that surfaces the errors these tools trace back to their cause.
- [Block Synchronization](../05-execution-and-synchronization/block-synchronization.md) — what `__syncthreads()` guarantees, and why `synccheck` cares whether every thread reaches it.
- [Distributed Shared Memory](../04-cuda-memory-model/distributed-shared-memory.md) — a memory space `racecheck` and `memcheck` extend their checks to.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
