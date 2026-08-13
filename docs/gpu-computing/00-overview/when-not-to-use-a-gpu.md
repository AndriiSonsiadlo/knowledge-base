---
id: when-not-to-use-a-gpu
title: When Not to Use a GPU
sidebar_label: When Not to Use a GPU
sidebar_position: 4
tags: [gpu, overview, amdahl, tradeoffs]
---

# When Not to Use a GPU

Most failed GPU ports do not fail because the kernel was slow. They fail because the workload was never shaped like something a GPU accelerates, and the port made that visible only after weeks of work. The kernel itself often *does* run twenty times faster than the CPU loop it replaced — and the program gets slower anyway, because the time now goes into transfers, synchronization, and the 60% of the runtime that was never offloaded at all.

This page is the negative case, deliberately placed before any CUDA syntax. Four patterns account for nearly all of it: the data costs more to move than the computation saves, the code is too branchy or too serial to use the width, the problem is too small to fill the machine, or the latency budget is tighter than the launch overhead. Each has arithmetic behind it that you can do on a whiteboard in five minutes, before committing to anything.

## Transfer-dominated workloads

A discrete GPU is on the far side of a bus, and that bus is slower than either machine attached to it by a large factor. PCIe Gen4 x16 has a theoretical ceiling near 31.5 GB/s per direction; with pinned host memory and a good driver you see roughly **25 GB/s effective**, and with pageable memory considerably less because the driver stages through an internal bounce buffer.

Work an example. Suppose one call ships 512 MB to the device, runs a kernel, and brings 512 MB of results back — 1 GB crossing the bus in total:

```text
bytes moved      = 512 MB up + 512 MB down = 1.0 GB = 1.0e9 bytes
effective rate   = 25 GB/s = 25e9 bytes/s
transfer time    = 1.0e9 / 25e9 = 0.040 s = 40 ms
```

So the round trip costs about **40 ms** before the kernel executes a single instruction. Now suppose the kernel replaces a CPU computation that took 50 ms and finishes it in 40 ms — a real 10 ms saving on the compute. The net result:

```text
CPU only   : 50 ms
GPU path   : 40 ms transfer + 40 ms kernel = 80 ms
net change : 30 ms slower
```

The offload lost, and it lost by more than the compute speedup was worth. Push the volume up and it gets worse in the same proportion: 1 GB in *each* direction is 2.0e9 bytes, or 80 ms of bus time. The saving would have to exceed 40 ms per direction just to break even.

This arithmetic is why the single most important structural question in GPU programming is not "how fast is my kernel" but **can the data stay resident on the device across iterations**. A pipeline that uploads once, runs two hundred kernels, and downloads once amortises the 40 ms across all two hundred. A pipeline that uploads and downloads every iteration pays it two hundred times. Pinned memory, copy/compute overlap on streams, and unified memory all reduce the constant — see [Pinned Memory and Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md) — but none of them changes the structure. Integrated and unified-memory parts (Apple silicon, Jetson, Grace-Hopper) sidestep it entirely, which is a genuine reason those platforms accelerate workloads a discrete card cannot.

## Branchy and serial code

The GPU's width only counts when the threads of a warp want the same instruction. When they diverge, the hardware executes each taken path in sequence with the other threads masked off, so the cost is the sum of the branch arms rather than the longest. A warp whose 32 threads each take a different case of a switch statement runs at roughly 1/32 of peak — worse than a CPU core, which would have executed exactly one arm per element with a predictor to hide the branch.

Serial dependencies are the sharper version of the same problem. If element `i` cannot be computed until element `i-1` is done, there is nothing to parallelise at the element level, and the GPU has no mechanism to help. Some apparently-serial algorithms have parallel reformulations — prefix sums are the classic case, solved by a work-inefficient but parallel scan — but that is a change of algorithm, not a port. Recursive descent over an irregular tree, an interpreter loop, a sequential state machine, or anything where the next memory address depends on the value just loaded, all belong on the CPU.

Between those poles sits the large middle ground of *irregular but parallel* work — sparse matrices, graph traversal, adaptive meshes. These can run well on a GPU, but only with data structures designed for coalesced access and load balance across warps. Treat them as a rewrite, not a port.

## Problems too small to fill the machine

Latency hiding is the whole mechanism, and it needs surplus work to hide behind. An H100 SXM has 132 SMs, each holding up to 2048 resident threads — **270,336 threads resident at once** (132 × 2048), and you generally want several times that many total work items so the scheduler always has a ready warp while others wait on memory.

Against that, a problem with 10,000 elements does not begin to occupy the device. It will run correctly; it will use a fraction of the SMs; and the fixed costs — the kernel launch, the driver call, the synchronization — will dominate a kernel body that finishes in microseconds. On problems that small a well-vectorized CPU loop, with the data already in L2 and no bus crossing at all, routinely wins.

The related trap is a *sequence* of small kernels. Each launch costs a few microseconds of overhead; a loop of a thousand tiny launches spends milliseconds doing nothing but launching. The fixes are to fuse the kernels, to batch the small problems into one large one, or to capture the whole sequence into a CUDA graph so the launches are replayed as a unit. All three are covered in [Kernel Fusion and Launch Overhead](../07-kernel-optimization/kernel-fusion-and-launch-overhead.md).

Here is the shape to recognise — a small kernel launched inside a host loop with a copy on both sides of it, which manages to hit every one of this page's failure modes at once:

```cpp showLineNumbers
// Anti-pattern: transfer + launch + full-device sync, every iteration.
for (int step = 0; step < num_steps; ++step) {
    cudaMemcpy(d_in, h_in, n * sizeof(float), cudaMemcpyHostToDevice);

    process<<<blocks, threads>>>(d_in, d_out, n);   // kernel body: // ...

    cudaMemcpy(h_out, d_out, n * sizeof(float), cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();                        // drains the whole device

    update_on_host(h_out);                          // serial, ~nothing to overlap
}
```

Every iteration pays two bus crossings, a launch, and a full-device drain, to run a kernel that may occupy the GPU for tens of microseconds. The restructured version keeps `d_in` and `d_out` resident for the whole loop, moves `update_on_host` onto the device as a second kernel, and copies out once at the end.

:::warning[`cudaDeviceSynchronize()` in a hot loop]
`cudaDeviceSynchronize()` blocks the host until *every* stream on the device has drained. Calling it once per iteration destroys the asynchrony the API is built around: the host can no longer queue the next iteration's work while the current one runs, no copy can overlap any kernel, and the launch overhead of every iteration is exposed instead of hidden behind execution. It is a debugging tool. In steady-state code, synchronize on a specific event or stream, and only where a genuine dependency requires it — see [Streams and Concurrency](../06-cuda-runtime-and-apis/streams-and-concurrency.md). The same warning applies to any per-iteration blocking `cudaMemcpy`, which carries an implicit synchronization of its own.
:::

## Latency-critical paths

Throughput and latency are different products, and a GPU sells the first. Even a perfectly-sized kernel carries fixed costs: a launch is on the order of a few microseconds, a host-device round trip over PCIe adds its own, and the driver, the scheduler, and any queueing behind other work add more. If the answer must be back in tens of microseconds, that budget is already spent before your code runs.

Worse, the *tail* is far less predictable than the mean. The GPU may be shared with a display, another process, or another tenant; the driver may be servicing someone else's launch; clocks may be throttled. If your service level objective is stated at the 99th percentile rather than the mean, a discrete GPU introduces a variance source you do not control. High-frequency trading paths, real-time control loops, and audio processing at small buffer sizes stay on the CPU for exactly this reason — and where they do use an accelerator, it is usually an FPGA, whose latency is deterministic by construction.

As a rule of thumb, a GPU is a reasonable candidate when the per-request latency budget is comfortably above ~1 ms and the work is batched. Below that, examine the fixed costs directly before assuming anything.

## Amdahl in practice

The quiet killer is not any of the above; it is the fraction of the program you did not offload. Amdahl's law states the overall speedup when a fraction `p` of the runtime is accelerated by a factor `s`:

```text
speedup = 1 / ( (1 - p) + p/s )
```

Take a generous case: you offload 90% of the runtime, so `p = 0.9`, and the remaining 10% stays on the host. Make the offloaded part **infinitely fast** — `s → ∞`, so the term `p/s` goes to zero:

```text
speedup = 1 / (1 - 0.9) = 1 / 0.1 = 10x
```

Ten times, and not one bit more, no matter what hardware you buy. Realistic accelerations are less flattering still:

```text
s = 10   ->  1 / (0.1 + 0.9/10)  = 1 / 0.19   =  5.3x
s = 100  ->  1 / (0.1 + 0.9/100) = 1 / 0.109  =  9.2x
```

Going from a 10× kernel to a 100× kernel — a heroic amount of optimization work — moves the program from 5.3× to 9.2×. The remaining 10% is now 92% of the runtime. That is the real lesson: past a point, further kernel tuning is worthless and the only remaining lever is offloading more of the program, or restructuring so the serial fraction shrinks. Gustafson's counter-argument — that in practice you scale the problem up rather than holding it fixed — is the reason large-scale GPU computing works at all, and it is developed in [Amdahl and Gustafson](../01-parallel-computing-foundations/amdahl-and-gustafson.md).

The practical procedure follows directly: profile the *whole application* first and find the true value of `p`. If 40% of runtime is in file I/O and JSON parsing, your ceiling is 1.67× and no kernel will save you.

## A checklist before you port

Run these four before writing any CUDA. Failing one is a warning; failing two means the answer is probably no.

1. **Is there at least ~10⁵ independent work items?** An H100 SXM holds 270,336 threads resident, so anything below that scale leaves most of the machine idle. Fewer than ~10⁴ and a vectorized CPU loop is very likely faster.
2. **Is arithmetic intensity above ~1 FLOP/byte?** Count the useful FLOPs and divide by the bytes that must move from DRAM. Below ~1 you are purely bandwidth-bound and your speedup ceiling is the ratio of GPU to CPU memory bandwidth, not the ratio of FLOPS — which is a much smaller number. See [Arithmetic Intensity and Roofline](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md).
3. **Can the data stay resident on the device across iterations?** If every iteration requires a host round trip, apply the 40 ms-per-gigabyte calculation from the top of this page to your actual volumes and iteration count before proceeding.
4. **Is the tail latency budget above ~1 ms?** Launch overhead, driver queueing, and contention with other GPU users all land in the tail. If your requirement is stated at p99 and measured in microseconds, this is the wrong hardware.

## See also

- [Why GPUs Exist](./why-gpus-exist.md) — the bargain these four checks are testing whether you can actually take.
- [Amdahl and Gustafson](../01-parallel-computing-foundations/amdahl-and-gustafson.md) — the serial-fraction ceiling, and the scaling argument that answers it.
- [Pinned Memory and Transfers](../04-cuda-memory-model/pinned-memory-and-transfers.md) — how to shrink the transfer constant once you have decided to pay it.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
