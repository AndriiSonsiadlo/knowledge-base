---
id: storage-overview
title: "Storage: HDD, SSD & NVMe — Overview"
sidebar_label: Overview
sidebar_position: 1
tags: [computer-science, storage, hdd, ssd, nvme]
---

# Storage: HDD, SSD & NVMe — Overview

## Overview

Storage is the **persistent** tier of the memory hierarchy: unlike RAM, it retains data with the
power off. This section covers the two dominant physical technologies (spinning magnetic disks and
flash memory) and the interfaces used to talk to them, because the physical mechanism directly
explains their performance characteristics — why HDDs are bad at random access, why SSDs wear out,
and why NVMe exists.

## Core Concepts

| Term | Meaning |
|---|---|
| **HDD (Hard Disk Drive)** | Persistent storage using spinning magnetic platters and a moving read/write head. |
| **SSD (Solid-State Drive)** | Persistent storage using NAND flash memory cells, with no moving parts. |
| **NVMe (Non-Volatile Memory Express)** | A modern host-controller interface/protocol designed for flash storage attached via PCIe, replacing the older SATA/AHCI stack. |
| **IOPS** | Input/Output Operations Per Second — the key throughput metric for random-access workloads (databases, VMs). |
| **Latency** | Time for a single storage operation to complete — dominates for HDDs (mechanical seek time) far more than for SSDs. |

## Comparison at a Glance

| Aspect | HDD | SATA SSD | NVMe SSD |
|---|---|---|---|
| Mechanism | Spinning platters, moving head | NAND flash | NAND flash |
| Random read latency | ~5-10 ms | ~50-100 µs | ~10-50 µs |
| Interface | SATA/SAS | SATA (AHCI) | PCIe (NVMe protocol) |
| Typical IOPS | ~100-200 | ~90,000 | ~500,000+ |
| Failure mode | Mechanical wear | Flash cell wear (limited write cycles) | Flash cell wear |
| Cost per GB | Lowest | Medium | Highest |

## In This Section

- [Hard Disk Drives](./hard-disk-drives.md) — platters, heads, seek time, rotational latency, and why
  RPM matters.
- [SSDs & NAND Flash](./ssd-and-nand-flash.md) — cell types, pages/blocks, the flash translation
  layer, wear leveling, TRIM, and write amplification.
- [NVMe & Storage Interfaces](./nvme-and-storage-interfaces.md) — the PATA → SATA/AHCI → NVMe/PCIe
  evolution, and why M.2 is a connector, not a protocol.
- [Filesystems Basics](./filesystems-basics.md) — inodes vs. FAT-style layouts, journaling, and
  copy-on-write filesystems.

## Why It Matters

- **[Memory Hierarchy & RAM](../memory-hierarchy/intro.md)**: storage sits below RAM in the hierarchy
  — orders of magnitude slower, which is why OSes and databases cache aggressively in RAM.
- **[Buses & I/O](../buses-and-io/intro.md)**: NVMe's performance advantage comes largely from being
  attached directly over PCIe with a leaner command protocol than legacy SATA/AHCI.
- **[Databases](../databases/intro.md)**: storage-engine design (B-trees vs. LSM-trees) is chosen
  specifically around the random vs. sequential I/O characteristics described here.

## Related Pages

- [Memory Hierarchy & RAM](../memory-hierarchy/intro.md)
- [Buses & I/O](../buses-and-io/intro.md)
- [Databases](../databases/intro.md)
