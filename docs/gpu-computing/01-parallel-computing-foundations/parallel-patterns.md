---
id: parallel-patterns
title: Parallel Patterns
sidebar_label: Parallel Patterns
sidebar_position: 6
tags: [gpu, parallelism, patterns, algorithms]
---

# Parallel Patterns

Almost every GPU kernel, however specialized, is built from a small set of recurring data-access shapes. Recognizing which pattern a problem is — before writing any code — tells you how parallelizable it is, what its likely performance limiter will be, and often points directly at a library implementation that already exists and is already tuned. This page names those shapes once, and every later applied-kernel page in this knowledge base assumes you already know these names — "this is a reduction" or "this needs a scan" is meant to carry full meaning by the time you reach folder 13.

## Map

Apply the same independent function to every element of a collection, with no data dependency between elements. This is the pattern behind SAXPY, elementwise activations, and type conversions. Data access is fully independent — each thread reads its own input and writes its own output, nothing is shared. It is the easiest pattern to parallelize: there is no synchronization, no ordering constraint, and near-perfect scaling with thread count, limited only by memory bandwidth. See [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md).

## Reduce

Combine all elements of a collection into a single value using an associative operator — sum, max, min, logical AND. Data access starts independent but the outputs must be combined, which forces a tree-shaped dependency: pairs combine into partial results, partial results combine into fewer partial results, until one value remains. That tree structure is the parallelization difficulty — a naive approach serializes the final combination steps, and doing it well requires warp-level primitives and careful use of shared memory to avoid becoming synchronization-bound. See [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md).

## Scan

Compute all prefix combinations of a sequence under an associative operator — running sums, cumulative maximums. Unlike reduce, every element of a scan's output depends on every element before it, not just contributing to one final value, which makes naive parallelization look impossible: the definition itself reads like a serial loop. The classic resolution (Blelloch scan) is a two-pass tree — an up-sweep that builds partial reductions, then a down-sweep that redistributes them into per-element prefixes — trading a factor of roughly 2x extra work for full parallelism. It's a harder pattern to implement correctly than reduce, though the algorithmic idea is well established. See [Prefix Sum](../13-applied-kernels-and-patterns/prefix-sum.md).

## Gather and scatter

Gather reads from computed (data-dependent) addresses into a dense output; scatter writes to computed addresses from a dense input. Both break the clean one-thread-one-contiguous-element mapping that map and reduce enjoy — the addresses come from an index array or the data itself, so access to DRAM is potentially irregular per thread. Parallelization is easy in the sense that each thread's work is still independent, but performance is hard: uncoalesced access patterns can cost an order of magnitude of bandwidth, and scatter additionally risks write conflicts when multiple threads compute the same destination address, requiring atomics or a conflict-free indexing scheme. Sparse matrix formats are the canonical example, since a sparse row's nonzero column indices are exactly a gather pattern. See [Sparse Matrix-Vector Multiply](../13-applied-kernels-and-patterns/sparse-matrix-vector.md).

## Stencil

Compute each output element from a fixed neighborhood of input elements — the 3-point stencil used as a worked example in [Arithmetic Intensity and the Roofline Model](./arithmetic-intensity-and-roofline.md), or its 2D/3D analogues in image filtering and PDE solvers. Data access is structured and local (each output reads a small, regular window around the corresponding input) but heavily overlapping between neighboring outputs, which is exactly what makes stencils bandwidth-hungry without careful implementation: the naive version reloads each input several times over. Parallelization itself is straightforward — outputs are independent of each other — but getting good performance requires shared-memory tiling to capture the neighbor reuse, the same technique that raised the roofline-page stencil's arithmetic intensity from ≈0.31 to ≈0.63 FLOP/byte. See [Stencil and Convolution](../13-applied-kernels-and-patterns/stencil-and-convolution.md).

## Histogram

Count occurrences of values (or accumulate into value-indexed bins) across a large input. Data access is a scatter into a small, shared output range — many threads potentially incrementing the same bin simultaneously. That contention is the parallelization difficulty: a naive implementation needs one atomic add per element into global memory, and if the input distribution is skewed, a small number of bins take nearly all the traffic and become a serialization bottleneck. Per-block private histograms merged at the end, or warp-aggregated atomics, are the standard mitigation. See [Histogram](../13-applied-kernels-and-patterns/histogram.md).

## Sort

Reorder a collection into a total order. Data access has no fixed shape — it depends entirely on the algorithm chosen, since sort has no natural one-thread-one-element mapping the way map or stencil do. That's also the parallelization difficulty: comparison-based sequential sorts don't parallelize cleanly, so GPU sorts use fundamentally different algorithms (radix sort, bitonic sort, merge-based approaches) chosen for their regular, GPU-friendly access patterns rather than for matching how a CPU would sort the same data. See [Sorting on the GPU](../13-applied-kernels-and-patterns/sorting-on-the-gpu.md).

## Composing patterns

Real kernels are rarely a single pattern in isolation — softmax is a reduce (find the max, sum the exponentials) composed with a map (divide each element by the sum); flash attention composes gather, map, and reduce across tiled blocks with a running softmax. Recognizing the constituent patterns in a composite kernel is what makes it tractable to reason about: each piece inherits the parallelization difficulty and likely performance limiter of its constituent pattern, and the whole kernel's profile is usually explained by whichever piece is weakest. [CUB](../08-libraries-and-ecosystem/cub.md) implements tuned versions of map, reduce, scan, histogram, and sort as reusable device-wide and block-level primitives — composing correct, fast implementations of these patterns is usually a matter of calling CUB rather than reimplementing the tree structure by hand.

| Pattern | Work | Communication | Implemented in |
|---|---|---|---|
| Map | O(n) | None | [Vector Add and SAXPY](../13-applied-kernels-and-patterns/vector-add-and-saxpy.md) |
| Reduce | O(n) | Tree-structured, O(log n) depth | [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md) |
| Scan | O(n log n) work-inefficient, O(n) work-efficient | Two-pass tree (up-sweep, down-sweep) | [Prefix Sum](../13-applied-kernels-and-patterns/prefix-sum.md) |
| Gather / scatter | O(n) | None (but irregular addressing) | [Sparse Matrix-Vector Multiply](../13-applied-kernels-and-patterns/sparse-matrix-vector.md) |
| Stencil | O(n) | Local neighborhood overlap | [Stencil and Convolution](../13-applied-kernels-and-patterns/stencil-and-convolution.md) |
| Histogram | O(n) | Contended writes into shared bins | [Histogram](../13-applied-kernels-and-patterns/histogram.md) |
| Sort | O(n log n) | Algorithm-dependent, often all-to-all | [Sorting on the GPU](../13-applied-kernels-and-patterns/sorting-on-the-gpu.md) |

## See also

- [SIMD, SIMT, and Flynn's Taxonomy](./flynn-taxonomy-simd-simt.md) — the execution model these patterns are implemented against.
- [Parallel Reduction](../13-applied-kernels-and-patterns/parallel-reduction.md) — the full worked implementation of the reduce pattern.
- [Prefix Sum](../13-applied-kernels-and-patterns/prefix-sum.md) — the full worked implementation of the scan pattern.
- [CUB](../08-libraries-and-ecosystem/cub.md) — tuned, reusable implementations of most of the patterns on this page.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
