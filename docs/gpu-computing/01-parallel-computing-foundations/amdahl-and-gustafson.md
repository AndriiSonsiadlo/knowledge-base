---
id: amdahl-and-gustafson
title: Amdahl's and Gustafson's Laws
sidebar_label: Amdahl & Gustafson
sidebar_position: 2
tags: [gpu, parallelism, scaling, amdahl]
---

# Amdahl's and Gustafson's Laws

Buying a bigger GPU, or more of them, does not buy a proportionally bigger speedup, and the reason has nothing to do with the hardware being slow. It has to do with the fraction of the program that was never made parallel in the first place. Two laws describe the two ways to think about that fraction — one holds the problem size fixed and asks how fast you can finish it, the other holds the *time budget* fixed and asks how much bigger a problem you can solve — and knowing which one describes your situation changes what "more parallelism" is even supposed to buy you.

## Amdahl's law

Amdahl's law fixes the problem size and asks how much faster a fixed amount of work finishes as you add workers. If a fraction `s` of the runtime is strictly serial and the remaining fraction `1 - s` parallelizes perfectly across `N` workers, the speedup over one worker is:

```text
speedup(N) = 1 / ( s + (1 - s) / N )
```

As `N` grows without bound, the parallel term `(1 - s) / N` goes to zero and the speedup asymptotes to `1 / s` — the serial fraction alone puts a hard ceiling on how fast the program can ever finish, no matter how many workers you throw at it.

## Strong scaling in practice

"Strong scaling" is the name for exactly this experiment: fixed problem, increasing worker count. The table below computes Amdahl speedup for four serial fractions across three worker counts (8, 64, 1024 — a modest CPU thread pool, a large one, and a worker count in the range of a single GPU's resident warps):

| Serial fraction | 8 workers | 64 workers | 1024 workers |
|---|---|---|---|
| 1% | 7.48x | 39.26x | 91.18x |
| 5% | 5.93x | 15.42x | 19.64x |
| 10% | 4.71x | 8.77x | 9.91x |
| 25% | 2.91x | 3.82x | 3.99x |

Read the 25% row across: going from 8 to 1024 workers — a 128x increase in raw parallelism — buys barely more than 1.37x more speedup, because at that serial fraction the ceiling (`1/0.25 = 4x`) is already almost reached at 64 workers. Read the 1% row down: a small serial fraction lets speedup keep climbing well past 1024 workers, because the ceiling (`1/0.01 = 100x`) is still far off. The lesson is not "parallelize more" — it's "measure `s` before buying more workers," because `s` alone tells you which regime you're in.

On a GPU, `s` is rarely arithmetic. A kernel body itself usually parallelizes almost perfectly across thousands of threads — the serial fraction that actually shows up in a profile is host-side setup, kernel launch overhead, the synchronous portions of a data transfer, and any host-side glue code between kernels that never got offloaded at all. That has a direct consequence: once you've found a nontrivial `s`, the fix is usually **structural** — fuse kernels, overlap transfers with compute on streams, batch small launches, keep data resident on the device across iterations — not algorithmic. Rewriting the math inside an already-parallel kernel does nothing to a serial fraction that lives outside it.

## Gustafson's law and weak scaling

Amdahl's law implicitly assumes the problem size is fixed as you add workers, which is often not what happens in practice — usually you add workers *because* you want to solve a bigger problem in the same wall-clock time. Gustafson's law reframes the question around that case, called **weak scaling**: hold the time budget fixed, and ask how much bigger a problem `N` workers can solve compared to one worker, if the serial portion of the *time budget* stays a fixed fraction `s'` regardless of scale:

```text
scaled speedup(N) = N - s' * (N - 1)
```

This grows roughly linearly in `N`, not asymptotically toward a ceiling, because as you add workers you also grow the parallel portion of the problem to fill the same time budget — the serial part doesn't have to eat a growing share of a fixed pie. Gustafson's observation is why large-scale GPU and HPC computing works at all in practice: nobody buys a bigger cluster to finish yesterday's problem size faster forever; they use it to run a larger simulation, a bigger batch, a finer grid, in the same time they used to spend on a smaller one.

## Which law applies to you

Ask which quantity you're actually holding fixed. If the problem size is fixed and given (a specific input file, a specific batch you must finish), you're in Amdahl's regime, and the serial fraction is a hard ceiling worth measuring before you invest in more parallel hardware. If instead the problem size is negotiable and what's fixed is your time or latency budget (train on more data in the same night, simulate a finer mesh in the same wall-clock hour), you're in Gustafson's regime, and scaling out remains worthwhile far longer than Amdahl's law alone would suggest. Most real GPU workloads are a mix: the launch-and-transfer overhead per kernel behaves like Amdahl's fixed serial cost, while the problem size you choose to run behaves like Gustafson's scaled workload.

:::tip[Measure before you optimize]
Profile the whole application — not just the kernel — and find the actual serial fraction before touching the parallel part. If host-side glue and transfers are 20% of wall-clock time, no amount of kernel tuning gets you past a 5x speedup, and the next unit of engineering time is better spent on that 20% than on shaving another millisecond off an already-fast kernel.
:::

## See also

- [Latency, Throughput, and Latency Hiding](./latency-throughput-and-hiding.md) — the mechanism that makes the parallel portion of a kernel actually reach near-perfect scaling.
- [When Not to Use a GPU](../00-overview/when-not-to-use-a-gpu.md) — the transfer and launch-overhead arithmetic behind a typical GPU serial fraction.
- [Multi-GPU Basics](../10-multi-gpu-and-scaling/multi-gpu-basics.md) — where these same laws reappear at the scale of multiple devices instead of multiple threads.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
