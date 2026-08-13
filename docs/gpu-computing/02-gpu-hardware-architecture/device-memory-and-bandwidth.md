---
id: device-memory-and-bandwidth
title: Device Memory and Bandwidth
sidebar_label: Memory & Bandwidth
sidebar_position: 6
tags: [gpu, hardware, hbm, bandwidth]
---

# Device Memory and Bandwidth

Every figure in [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) ultimately rests on one number: how many bytes per second a kernel can move between the SMs and DRAM. That number is set by the physical memory technology soldered onto (or stacked next to) the GPU die, and it is very different from the number a datasheet advertises. This page covers what GDDR and HBM actually are, why achieved bandwidth always falls short of the peak figure, and how to measure the one that actually matters for a given kernel.

## GDDR and HBM

Consumer and workstation GPUs use **GDDR** — GDDR6 or GDDR6X — a handful of discrete DRAM chips soldered onto the board around the GPU package, each connected by a relatively narrow set of PCB traces running at a very high per-pin clock. Datacenter compute parts instead use **HBM** (High Bandwidth Memory) — DRAM dies stacked vertically and placed on the same silicon interposer as the GPU die (a "2.5D" package), connected by an extremely wide bus running at a comparatively modest per-pin clock. GDDR trades bus width for clock speed to fit on a conventional PCB; HBM trades clock speed for bus width because the interposer packaging allows thousands of parallel signal traces that would be impossible to route on a normal board. The result is that HBM parts reach far higher aggregate bandwidth per watt and per die, at higher packaging cost — which is why HBM is reserved for datacenter accelerators rather than consumer cards.

| Memory | Bus width | Typical peak | Where you find it |
| --- | --- | --- | --- |
| GDDR6X | 384-bit | ~1.0 TB/s | GeForce RTX 4090 (Ada) |
| HBM2e | 5120-bit | ~2.0 TB/s | A100 SXM (Ampere, CC 8.0) |
| HBM3 | 5120-bit | ~3.35 TB/s | H100 SXM (Hopper, CC 9.0) |
| HBM3e | 5120-bit | ~4.8 TB/s | H200 SXM (Hopper, CC 9.0) |

:::note[The H100's bus width is a product figure, not the die's full bus]
The 5120-bit figure above is the H100 SXM5 *product* configuration, in which 5 of the 6 HBM3 stacks the GH100 die supports are wired and active. The GH100 die itself is built for a 6144-bit bus across all 6 stacks; NVIDIA ships the SXM5 module with one stack disabled (for yield and product-segmentation reasons), so a reader cross-referencing NVIDIA's die-level documentation will see 6144-bit there and 5120-bit here — both are correct, describing the die and the shipped product respectively.
:::

## Peak versus achievable

The "peak" figure in a datasheet is a theoretical ceiling computed from the memory clock, the bus width, and the transfer-rate multiplier of the signaling scheme (e.g. GDDR6X's PAM4 encoding, HBM's wide single-data-rate-per-pin but massively parallel bus) — it assumes every clock cycle on every pin moves useful data, forever. Real kernels never reach it, for reasons that stack on top of each other: DRAM needs periodic refresh cycles that steal bus cycles from useful traffic; ECC (where enabled) consumes some fraction of the bus for redundancy; switching between reads and writes, or between widely separated addresses, costs idle bus cycles for command overhead and bank timing; and — the factor a programmer has the most control over — an access pattern that isn't well-coalesced (see [Cache Hierarchy](./cache-hierarchy.md#sectors-not-cache-lines)) wastes bus bandwidth fetching sectors the kernel doesn't actually use. A well-written, fully-coalesced streaming kernel can still only reach roughly 80–90% of the advertised peak; a poorly-coalesced one can fall far short of that.

## Measuring effective bandwidth

The only bandwidth number worth trusting is one measured against what a kernel actually moved, not what the datasheet promises:

```text
effective bandwidth = (bytes_read + bytes_written) / seconds
```

Take SAXPY (`y[i] = a * x[i] + y[i]`) in single precision as a worked example. Each of the `N` iterations touches three 4-byte values: it reads `x[i]`, reads `y[i]`, and writes `y[i]` back — 3 arrays × 4 bytes × N elements of total traffic, or `12N` bytes.

For `N = 268,435,456` (2^28) elements:

```text
bytes  = 12 x 268,435,456 = 3,221,225,472 bytes  (~3.00 GiB)
```

Suppose a profiler measures this kernel's execution time at 1.20 ms on an H100 SXM. Effective bandwidth is then:

```text
bandwidth = 3,221,225,472 bytes / 0.00120 s ≈ 2.68 x 10^12 B/s ≈ 2.68 TB/s
```

Against the H100 SXM's ~3.35 TB/s HBM3 peak (established in [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md#the-ridge-point)), that's 2.68 / 3.35 ≈ 80% of peak. SAXPY's arithmetic intensity is far below the H100's ~20 FLOP/byte ridge point (it does one multiply-add — 2 FLOPs — per 12 bytes moved, an AI around 0.17), so this kernel is memory-bound by a wide margin. At 80% of peak bandwidth, it is already near the achievable ceiling for this GPU: no amount of instruction-level tuning, unrolling, or arithmetic optimization can move performance further, because the bottleneck was never the arithmetic. Only moving fewer bytes — a different algorithm, a narrower data type, or better reuse — would raise the ceiling.

## Bandwidth as the usual ceiling

This is the mechanical reason the roofline model in [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) matters: most real kernels, not just SAXPY, sit well to the left of the ridge point, which means DRAM bandwidth — not FP32 or tensor-core throughput — is the resource actually being spent. [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md) works through this specific kernel end to end, including how to hit the 80%+ figure in practice.

:::tip[Treat peak as a denominator, not a target]
80–90% of advertised peak bandwidth is a realistic ceiling for a well-written streaming kernel — never 100%. When profiling, use peak bandwidth only to compute "percentage of peak achieved," and stop optimizing memory access patterns once that percentage plateaus in the 80–90% range; the remaining gap is refresh, ECC, and command overhead you cannot design around.
:::

## See also

- [Cache Hierarchy](./cache-hierarchy.md) — what happens to a request before it ever reaches DRAM, and why coalescing determines how much of "peak" a kernel can actually reach.
- [Arithmetic Intensity and the Roofline Model](../01-parallel-computing-foundations/arithmetic-intensity-and-roofline.md) — the ridge-point comparison this page's bandwidth ceiling feeds into.
- [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md) — the worked kernel this page's SAXPY example is drawn from, implemented end to end.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
