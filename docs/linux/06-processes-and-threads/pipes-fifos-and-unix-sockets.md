---
id: pipes-fifos-and-unix-sockets
title: "Pipes, FIFOs, and UNIX Sockets"
sidebar_label: "Pipes and UNIX sockets"
sidebar_position: 10
tags: [linux, kernel, processes]
prerequisites:
  - linux/processes-and-threads/the-process-address-space
related:
  - computer-science/operating-systems/interprocess-communication
draft: false
---

# Pipes, FIFOs, and UNIX Sockets

The IPC processes actually use, at the kernel level: a ring of pages, `splice`, socket pairs, and passing a file descriptor.

:::info[Not yet written]
This page is a stub. See [the roadmap](../00-overview/roadmap.md) for what lands when.
:::
