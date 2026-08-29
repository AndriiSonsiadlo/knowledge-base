---
id: what-this-section-covers
title: "What This Section Covers"
sidebar_label: "What this covers"
sidebar_position: 1
tags: [linux, kernel]
prerequisites: []
draft: false
---

# What This Section Covers

The scope of this section, what it deliberately leaves out, and what "understanding Linux" means in practice.

Understanding Linux, here, means three specific capabilities — not trivia, not a command list. First,
predicting behaviour from mechanism: knowing *why* something happens well enough to guess what a
system will do in a situation you have never seen, instead of pattern-matching against commands you
remember running before. Second, reading kernel source to answer a question nobody has already
blogged about — the documentation for a live system is the code that runs on it, and everything else
is a summary someone wrote once and stopped updating. Third, instrumenting a running system instead
of guessing: when something is slow, stuck, or wrong, reaching for `perf`, `ftrace`, or a `bpftrace`
one-liner rather than restarting it and hoping. Every page in this section is trying to move you
closer to one of those three.

## What this section is

A ladder that starts at the syscall boundary — the one door between your code and the machine — and
descends through processes, memory, locking, the VFS, and the network stack down to page tables and
RCU and the shape of a packet on the wire. It is source-anchored to one pinned kernel release, so
every claim can be checked instead of taken on faith, and it treats the hands-on lab — build a kernel,
boot it, break it, watch it with a tracer — as the spine that the reading hangs off, not an
afterthought at the end of a chapter.

## What this section is not

- **Not a distribution guide.** No page tells you how to configure a specific distribution's package
  manager, init scripts, or defaults.
- **Not a sysadmin certification path.** It does not track any vendor's exam objectives.
- **Not a command reference.** Commands appear as evidence for a mechanism, never as the thing being
  taught.
- **Not a substitute for `man`.** When a flag or a syscall's exact contract matters, the manual page
  is the source of truth; this section explains the machinery a flag triggers, not the flag itself.

## Who it is for

Someone who is comfortable writing C and comfortable at a shell, and who wants the layer underneath
both — what a process actually is to the kernel, what a system call actually does, why the tools
behave the way they do. No prior kernel experience is assumed; comfort with C and a shell is.

## What it assumes, and where the assumptions live

This section does not re-teach computer architecture or general operating-system theory — CPU
privilege levels, virtual memory, scheduling theory, and the rest already have a home in
[`computer-science/`](../../computer-science/intro.md), and pages here link to that material and go
deeper rather than repeating it. Where Linux specifically depends on hardware behaviour — what a
kernel can assume the CPU, the MMU, and the interrupt controller will do for it — that assumption is
collected in one place: [The Hardware the Kernel Assumes](./hardware-the-kernel-assumes.md).

## How it is organised

Folder position on disk is reading order. The first five folders exist now; the rest are specified —
their scope is fixed, their pages are not yet written.

| Folder | Covers | Status |
|---|---|---|
| `00-overview` | Scope, the kernel/user boundary, hardware assumptions, the roadmap | This phase |
| `01-lab-and-toolchain` | Building a kernel, booting it under QEMU, attaching a debugger | This phase |
| `02-guided-traces` | Six familiar operations — a command, a write, a fault, a boot — followed all the way down | This phase |
| `03-boot-and-init` | Firmware to login prompt: UEFI, GRUB, the kernel image, initramfs, PID 1, systemd | This phase |
| `04-kernel-architecture-and-idioms` | Kernel structure and the C idioms it is written in | This phase |
| `05` | Syscalls | Specified |
| `06` | Processes | Specified |
| `07` | Scheduling | Specified |
| `08` | Memory | Specified |
| `09` | Locking | Specified |
| `10` | Interrupts | Specified |
| `11` | The VFS | Specified |
| `12` | Block I/O | Specified |
| `13` | Networking | Specified |
| `14` | Drivers | Specified |
| `15` | Containers | Specified |
| `16` | Security | Specified |
| `17` | Observability | Specified |
| `18` | eBPF | Specified |
| `19` | Contributing | Specified |

*The folder ladder: position on disk is reading order, and only the first five folders have pages
behind them yet.*

For the routes people actually want to take through this ladder — "I just want to understand my
machine," "I want to build and debug a kernel," and others — see [the roadmap](./roadmap.md). For the
conventions every page follows (the facts card, pinned source links, lab host badges), see
[How to Use This Section](./how-to-use-this-section.md).

## The pinned kernel

Every claim in this section is checked against one specific long-term-support release: **Linux
v6.18**. Pinning matters because the kernel is not one stable target — a struct field, a function
name, or a lock's scope can change between releases, and a claim that is true here can be false on a
kernel from two years ago or two years from now. Where this section says "the kernel does X," read it
as "v6.18 does X," and check [the source](../readme.md) if you are running something else.

<KernelFacts
  structure={[]}
  path="Read the boundary, pick a route from the roadmap, build the lab, then follow the ladder"
  observe="uname -r"
  trap="Knowing which command does a thing is not knowing what happens. This section is about the second one, and it will not make you faster at the first." />

## References

- [docs.kernel.org](https://docs.kernel.org/) — the section's primary source, and what every claim in
  it is checked against.
- [LWN.net Kernel Index](https://lwn.net/Kernel/Index/) — a by-topic index into the best secondary
  writing on kernel mechanism, for when a subsystem needs more depth than one page can give.
- [Bootlin Elixir Cross Referencer, Linux v6.18](https://elixir.bootlin.com/linux/v6.18/source) — the
  pinned source tree every `<Src>` link in this section resolves into.
