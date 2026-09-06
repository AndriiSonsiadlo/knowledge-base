---
id: mmio-and-port-io
title: "MMIO, `ioremap`, and Accessors"
sidebar_label: "MMIO and accessors"
sidebar_position: 4
tags: [linux, kernel, drivers]
prerequisites:
  - linux/device-drivers-and-hardware/pci-and-pcie-drivers
  - linux/concurrency-and-locking/memory-ordering-and-barriers
draft: false
---

# MMIO, `ioremap`, and Accessors

Why a driver never dereferences a device pointer: `ioremap`, `readl`/`writel` and their ordering, `__iomem`, relaxed accessors, and port I/O.

:::info[Not yet written]
This page is a stub. See [the roadmap](../00-overview/roadmap.md) for what lands when.
:::
