---
id: vmalloc-and-choosing-an-allocator
title: "`vmalloc` and Choosing an Allocator"
sidebar_label: "Choosing an allocator"
sidebar_position: 9
tags: [linux, kernel, memory-management]
prerequisites:
  - linux/memory-management/the-page-allocator
draft: false
---

# `vmalloc` and Choosing an Allocator

Every allocation decision in the kernel eventually comes down to one distinction: **physically
contiguous** versus **virtually contiguous**. Some consumers genuinely require the first — a device doing
DMA without an IOMMU, a page-table page the hardware itself walks by physical address. Most code that
*thinks* it needs physical contiguity does not; it just needs a range of addresses it can index like an
array. `vmalloc` exists to serve that majority, at a price this page spends its first two sections
explaining.

## What `vmalloc` does

`vmalloc()` allocates individual physical pages — not necessarily adjacent to each other, wherever the
page allocator happens to have order-0 pages free — and then builds page-table entries in the kernel's
own address space that map those scattered pages **consecutively** into one virtual range, in the
dedicated vmalloc region carved out of the kernel's part of the address space (see [The Virtual Address
Space](./the-virtual-address-space.md) for where that region sits). The result, from the caller's point
of view, is one contiguous run of virtual addresses. What lies behind it is whatever pages happened to be
available, in whatever physical order.

## What it costs

Nothing here is free, which is exactly why `vmalloc` is not the default:

- **Page-table setup on every allocation.** Unlike a `kmalloc` allocation, which lands inside the direct
  map that is already built, `vmalloc` has to create new page-table entries for the range it just
  invented, on every call.
- **A TLB entry per 4 KiB.** The general-case `vmalloc` mapping is not huge-page backed — the scattered
  physical pages behind it usually cannot form the aligned, physically-contiguous 2 MiB run a huge
  mapping needs — so a large `vmalloc` buffer consumes far more TLB entries to walk than the same amount
  of memory would from `kmalloc`, where the direct map is frequently huge-page mapped already.
- **Potential shootdowns on free.** Tearing down the mapping means invalidating those page-table entries
  on every CPU that might have cached them — the same [TLB shootdown](./tlb-and-address-space-switching.md)
  cost that makes `munmap` expensive in user space, paid again here.
- **A limited region size.** The vmalloc address range is finite (visible as `VmallocTotal` in
  `/proc/meminfo`); it is enormous on 64-bit machines in practice, but it is not "as much as physical
  memory allows" the way `kmalloc`/the page allocator effectively is.

The plain conclusion: kernel code prefers `kmalloc` whenever it can, not out of habit but because the
direct map is *already* mapped, and it is often huge-page backed — `kmalloc` memory costs essentially no
extra TLB pressure over memory the kernel would have mapped anyway, while `vmalloc` memory is a mapping
built and torn down specifically for this one allocation.

## When you actually need physical contiguity

Two cases where "virtually contiguous" genuinely is not good enough:

- **DMA without an IOMMU.** A device programmed with a single base address and length reads and writes
  physical memory directly; if the buffer behind that address is not physically contiguous, the device
  walks off the end of the first physical page into whatever happens to be next — memory corruption, not
  a graceful failure.
- **Anything hardware or a device indexes directly** by physical address — a page-table page itself is
  the canonical example, since the MMU walks page tables by physical address with no software translation
  layer in between.

With an IOMMU in the path, the first case often disappears: the IOMMU can present a device with its own
contiguous *device-visible* address space mapped onto scattered physical pages, the same trick `vmalloc`
plays for the CPU's own MMU. Folder 14 develops this point properly when it covers DMA and IOMMUs
directly; here it is enough to know the requirement is conditional on the hardware path, not an absolute
property of "using a device."

## `vmalloc` versus `kvmalloc`

`kvmalloc()` is the pragmatic middle ground: try `kmalloc` first, and only fall back to `vmalloc` if the
request is large enough that a physically contiguous allocation of that size would be unreasonable to
demand from the page allocator (large orders fragment first and fail first, per
[The Page Allocator](./the-page-allocator.md#fragmentation-and-compaction)). It is the right call for a
buffer that is usually small, occasionally large, and never needs physical contiguity — a good fit for
data whose size is driven by user input rather than a fixed kernel structure. It is the *wrong* call for
anything that will be handed to a device for DMA, because the caller cannot know in advance which
underlying allocator actually served the request, and treating the result as physically contiguous when
`kvmalloc` silently fell back to `vmalloc` corrupts memory exactly as passing a `vmalloc` buffer to DMA
directly would.

## The decision table

Checked against the kernel's own guidance at
`https://docs.kernel.org/core-api/memory-allocation.html`, which is the authority where this table and
that page might otherwise disagree:

| Allocator | Physically contiguous? | May sleep? | Size range | Freed by | Typical use |
|---|---|---|---|---|---|
| `kmalloc`/`kzalloc` | Yes | Depends on `gfp_t` (`GFP_KERNEL` may sleep; `GFP_ATOMIC`/`GFP_NOWAIT` may not) | Small — up to the largest `kmalloc` size class (2 MiB at v6.18, and in practice far smaller for anything expected to succeed reliably) | `kfree()` | The default for ordinary kernel objects; reach for this first. |
| `kvmalloc`/`kvzalloc` | Not guaranteed — falls back to `vmalloc` for large requests | Yes (its `vmalloc` fallback always may sleep) | Small to large, no hard limit | `kvfree()` | A buffer that does not need contiguity and is usually small but occasionally large — never for DMA. |
| `vmalloc`/`vzalloc` | No | Yes, always | Large; bounded by the vmalloc region size, not physical memory | `vfree()` (or `kvfree()`) | Large buffers with no contiguity requirement — module loading's own text/data mapping is a classic example. |
| `alloc_pages`/`__get_free_pages` | Yes | Depends on `gfp_t`, same as `kmalloc` | Order-0 up to the zone's maximum order | `__free_pages()` | Direct page-allocator use — page-order granularity, no slab overhead, the base every other allocator here is built on. |
| `kmem_cache_alloc` | Yes (within one slab) | Depends on `gfp_t` passed to the call | Fixed — whatever size the cache was created with | `kmem_cache_free()` | Many identical objects of one type, allocated and freed constantly — see [Slab, SLUB, and `kmalloc`](./slab-slub-and-kmalloc.md). |
| `devm_kzalloc` | Yes (it is a `kzalloc` under the hood) | Yes | Same range as `kzalloc` | Automatically, when the owning device unbinds — or explicitly via `devm_kfree()` | Driver-owned memory that should not outlive the device, without a manual free on every error and teardown path. |
| Per-CPU allocator (`alloc_percpu`) | N/A — one physically-backed chunk per CPU, not one shared region | Yes | Small to moderate, one instance per possible CPU | `free_percpu()` | Data every CPU touches independently and that would otherwise bounce a shared cache line between cores — the pattern [Per-CPU Data](../09-concurrency-and-locking/per-cpu-data.md) covers in full. |

## `devm_*`, briefly

Device-managed (`devm_*`) allocation attaches an allocation's lifetime to the owning `struct device`
instead of to manual bookkeeping: memory obtained through `devm_kzalloc()` and its relatives is freed
automatically when the device unbinds, so a driver's error-unwind and `remove()` paths do not each need
their own matching `kfree()`. Folder 14 owns this properly — driver code meets `devm_*` constantly, and
two sentences here is enough to place it in the table above.

## Context decides more than size

The question "which allocator" almost always resolves before the question "how much memory," because the
first thing that matters is **may this code sleep?** Code running with a spinlock held, in an interrupt
handler, or anywhere else preemption or blocking is forbidden cannot use `GFP_KERNEL` at all, regardless
of size — it needs `GFP_ATOMIC`/`GFP_NOWAIT`, which immediately rules out anything that might reclaim or
block, `vmalloc` included. That is a question about the calling context, not the object being allocated,
and it is exactly what [Why Kernel Concurrency Is
Different](../09-concurrency-and-locking/why-kernel-concurrency-is-different.md) exists to explain in
full: size picks a row in the table above, but context decides whether that row is even reachable.

<KernelFacts
  structure={[["struct vm_struct", "include/linux/vmalloc.h"]]}
  path="vmalloc() [alloc_hooks(vmalloc_noprof(...))] → __vmalloc_node_range() [alloc_hooks(__vmalloc_node_range_noprof(...))] → alloc_pages() per page → map_kernel_range() → contiguous virtual range"
  observe="cat /proc/vmallocinfo | head && grep -E 'VmallocTotal|VmallocUsed' /proc/meminfo"
  trap="vmalloc memory is not usable for DMA even though it looks like one buffer. The device sees physical addresses, and the physical pages behind a vmalloc range are scattered — passing one to a DMA API without a scatter-gather list corrupts memory." />

## References

- <Src file="mm/vmalloc.c" symbol="__vmalloc_node_range" /> — the allocation path; at v6.18 the public
  `vmalloc()`/`__vmalloc_node_range()` are macros (`alloc_hooks(..._noprof(...))`) wrapping `_noprof`
  implementations, the same allocation-tagging pattern `alloc_pages()` uses — the per-page allocation and
  the mapping step are both visible in `__vmalloc_node_range_noprof()`.
- `https://docs.kernel.org/core-api/memory-allocation.html` — the kernel's own "which allocator should I
  use" guidance; the decision table above was checked against it directly, row by row.
- `https://docs.kernel.org/core-api/mm-api.html` — the API reference for every function named in the
  table.
- `man 5 proc`, the `/proc/meminfo` `Vmalloc*` fields — for the observation command; confirmed
  world-readable and present on this machine (`VmallocTotal`/`VmallocUsed` both read successfully),
  unlike `/proc/vmallocinfo`, which is root-only.
