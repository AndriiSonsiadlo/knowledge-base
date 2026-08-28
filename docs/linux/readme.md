---
title: Linux & Kernel
sidebar_label: Overview
sidebar_position: 0
tags: [linux, kernel]
prerequisites: []
---

# Linux & Kernel

How Linux actually works, from the boundary between a command you type and the kernel that
services it, down to page-table walks, RCU grace periods, and the path a packet takes through the
network stack. The aim is understanding you can reason from — not commands you have memorised.

:::info[This section is being written]
Folders and pages exist as stubs so the structure and its dependency graph are navigable from the
start.
:::

## The pinned kernel

Every source reference in this section points at **Linux v6.18** — released 2025-11-30, a longterm
release with projected end-of-life in December 2028. Citations name a file and a symbol
(`fs/namei.c:path_openat()`) and never a line number, because line numbers rot within a single
release while paths and symbol names survive for years.

Where behaviour changed recently enough that older material is now wrong — the fair scheduler, the
folio conversion, `io_uring` — the page says so explicitly.

## The lab

Nearly every hands-on exercise runs against a kernel you build yourself, booted under QEMU. A
kernel panic there costs you nothing and you can attach a debugger to the virtual CPU itself.
[Setting Up a Lab](./01-lab-and-toolchain/the-lab-machine.md) covers the whole setup, including
what WSL2 can and cannot do.

See [the roadmap](./00-overview/roadmap.md) for the dependency graph and the learning paths
through everything here.
