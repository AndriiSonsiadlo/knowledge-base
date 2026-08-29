---
id: hardware-the-kernel-assumes
title: "The Hardware the Kernel Assumes"
sidebar_label: "Hardware assumed"
sidebar_position: 4
tags: [linux, kernel]
prerequisites: []
related:
  - computer-science/cpu-architecture/privilege-levels-and-protection
  - computer-science/cpu-architecture/exceptions-traps-and-interrupts
draft: false
---

# The Hardware the Kernel Assumes

The seven hardware capabilities every Linux mechanism rests on, each linked to the Computer Science page that owns it.

Linux is not portable to *any* machine. It is portable to machines that provide a specific short
list of capabilities — a privilege boundary, an MMU, precise exceptions, interrupts, atomic
read-modify-write instructions, a trustworthy clock, and DMA-capable devices — and it assumes
nothing beyond that list. Naming the list explains why the kernel is shaped the way it is: every
mechanism described anywhere in this section — the scheduler, the page-fault handler, `fork()`,
every lock, every driver — is built on one or more of these seven, and none of them re-teaches the
underlying hardware. That is a deliberate choice, not an oversight: each capability already has an
owner in `computer-science/`, and this page is where a later Linux page points instead of
re-explaining what an MMU or an interrupt controller is. If you are writing one of those pages and
find yourself about to explain a piece of hardware, check the table below first — it is almost
certainly owned already.

## The seven capabilities

### 1. Privilege levels

The CPU must offer at least two privilege levels, one of them unreachable by ordinary instructions,
so that kernel code can hold authority user code cannot forge. Without it there is no kernel, only a
library: any function user code could call, user code could also skip, and nothing distinguishes
"trusted" from "untrusted" memory or instructions. See
[Privilege Levels and Protection](../../computer-science/cpu-architecture/privilege-levels-and-protection.md).

### 2. An MMU with a page table walker

The CPU must be able to translate every memory access through a table the kernel controls, and walk
that table in hardware rather than trapping to software on every access. Per-process address spaces,
demand paging, and `fork()`'s copy-on-write all follow directly from it — a process's view of memory
is only private because the MMU enforces the mapping, and pages can only be shared lazily because a
hardware fault, not a software check, catches the first write. See
[Virtual Memory and Paging](../../computer-science/memory-hierarchy/virtual-memory-and-paging.md).

:::note
`nommu` Linux exists — a configuration for microcontrollers with no MMU at all, where every process
shares one flat address space and `fork()` degrades to `vfork()`-like semantics. It is real and
shipping, but out of scope: this section assumes an MMU throughout.
:::

### 3. Precise exceptions

When an instruction faults, the CPU must stop *before* that instruction's effect happens and hand
the kernel an exact description of what was attempted — not an approximation, not a fault reported
several instructions later. Demand paging depends on this: the kernel services the fault, fixes up
the page table, and the CPU must be able to *retry* the exact faulting instruction from scratch as
if it had never run. An imprecise exception would make that retry unsafe. See
[Exceptions, Traps, and Interrupts](../../computer-science/cpu-architecture/exceptions-traps-and-interrupts.md).

### 4. Interrupts and a controller to route them

The CPU must be interruptible by external hardware, and something must exist to route, prioritize,
and mask those interrupts across every device in the machine. Without them the kernel would have to
poll every device in a loop, burning cycles whether or not anything happened — interrupts are what
let the CPU do other work until a device actually has something to report. See
[I/O and Interrupts](../../computer-science/buses-and-io/io-and-interrupts.md).

### 5. Atomic read-modify-write instructions

The CPU must offer at least one instruction that reads, modifies, and writes a memory location as
one indivisible step, visible to other cores. Every lock and every reference count in the kernel —
spinlocks, `atomic_t`, RCU's grace-period counters — bottoms out in one of these; without an atomic
primitive, two cores updating the same counter could always race, and no software-only trick fixes
that on a shared-memory multiprocessor. See
[Multicore and Parallelism](../../computer-science/cpu-architecture/multicore-and-parallelism.md).

### 6. A monotonic timer and a way to interrupt on it

The machine must provide a clock that only ever moves forward and a way to ask it to raise an
interrupt at a future point. Preemption depends on it — the scheduler cannot take the CPU back from
a running task without a timer tick to interrupt on — and so do timeouts throughout the kernel and
the guarantee behind `CLOCK_MONOTONIC` in user space: a clock the kernel trusts never to run
backward. This capability is owned by a later folder in this section, once timekeeping gets its own
treatment; for now, treat "a clock the kernel trusts" as a placeholder for a chapter that has not
landed yet.

### 7. DMA-capable devices

A device must be able to move data to and from memory on its own, without the CPU copying every
byte through a register. This is the reason drivers are about buffers and ownership — who currently
owns a region of memory, the CPU or the device, and when that ownership may safely change hands —
rather than about copying bytes: the CPU hands a device a buffer address and gets on with other
work while the transfer happens in the background. See
[System Interconnects](../../computer-science/buses-and-io/system-interconnects.md).

## What Linux does not assume

The list above is short on purpose, and what is missing from it is as informative as what is on it:

- **No floating point in kernel context.** Kernel code by default avoids the FPU/SSE/AVX register
  state entirely, because saving and restoring it on every entry and exit would be wasted cost for
  code that almost never needs it; the rare kernel code that does use it must save that state
  explicitly.
- **No specific device set.** The kernel assumes DMA-capable devices exist in general, not that any
  particular device — a given disk controller, a given NIC — is present. Everything device-specific
  lives in a driver, never in core kernel code.
- **No fixed page size across architectures.** 4 KiB is common but not universal — some
  architectures default to larger base pages, and huge pages exist everywhere on top of whatever the
  base size is. Code that hardcodes a page size is a portability bug.
- **No cache coherence with devices.** A CPU's caches are not guaranteed to see what a DMA-capable
  device just wrote to memory, or vice versa, without explicit synchronization — which is precisely
  why the DMA API exists: `dma_map_*()`/`dma_unmap_*()` and friends make the CPU/device
  synchronization explicit instead of assuming the hardware does it for free.
- **No strong memory ordering.** x86-64 happens to provide a fairly strong ordering model, but the
  kernel is written for architectures that do not — which is why kernel code is full of explicit
  memory barriers (`smp_mb()` and friends) even in code paths that, on x86-64 specifically, would
  work without them. The barrier is there for every architecture the code might run on, not for the
  one it was written on.

## Where each one is owned

The operational form of the no-duplication contract: before explaining a piece of hardware on any
later page in this section, check whether it is already owned here.

| Capability | Owning page |
|---|---|
| Privilege levels | [Privilege Levels and Protection](../../computer-science/cpu-architecture/privilege-levels-and-protection.md) |
| MMU and page table walker | [Virtual Memory and Paging](../../computer-science/memory-hierarchy/virtual-memory-and-paging.md) |
| Precise exceptions | [Exceptions, Traps, and Interrupts](../../computer-science/cpu-architecture/exceptions-traps-and-interrupts.md) |
| Interrupts and a controller | [I/O and Interrupts](../../computer-science/buses-and-io/io-and-interrupts.md) |
| Atomic read-modify-write | [Multicore and Parallelism](../../computer-science/cpu-architecture/multicore-and-parallelism.md) |
| Monotonic timer | Owned by a later folder in this section (not yet written) |
| DMA-capable devices | [System Interconnects](../../computer-science/buses-and-io/system-interconnects.md) |

<Figure src="/img/linux/overview/privilege-rings.svg" alt="Concentric rings 0 through 3, with the kernel at ring 0 and applications at ring 3" caption="x86 protection rings. Linux uses two of the four: ring 0 for the kernel, ring 3 for everything else." source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Priv_rings.svg" />

<KernelFacts
  structure={[["struct cpuinfo_x86", "arch/x86/include/asm/processor.h"]]}
  path="CPU feature bits → cpu_has()/boot_cpu_has() at init → the kernel enables or refuses a mechanism"
  observe="lscpu && grep -m1 flags /proc/cpuinfo"
  trap="The kernel does not require a *fast* MMU, a *fast* atomic, or a *precise* clock — it requires that they exist and are correct. Nearly every performance chapter in this section is about the gap between correct and fast." />

## References

- [Kernel documentation — Architecture-specific documentation](https://docs.kernel.org/arch/index.html)
  — what the kernel actually requires of an architecture port, and how the arch layer that isolates
  those requirements from the rest of the kernel is structured.
- [`Documentation/core-api/dma-api.rst`](https://docs.kernel.org/core-api/dma-api.html) — the
  clearest statement in the kernel's own documentation of what it does *not* assume about
  device/CPU cache coherence, and the API that makes the synchronization explicit.
- Intel® 64 and IA-32 Architectures Software Developer's Manual, Volume 3A, chapters 1–2 — the
  architectural features this page depends on (protection, paging, interrupts), described in their
  primary source rather than secondhand.
