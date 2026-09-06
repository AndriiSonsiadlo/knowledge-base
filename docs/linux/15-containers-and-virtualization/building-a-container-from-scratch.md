---
id: building-a-container-from-scratch
title: "Lab: Build a Container from Scratch"
sidebar_label: "Lab: a container"
sidebar_position: 8
tags: [linux, kernel, containers]
prerequisites:
  - linux/containers-and-virtualization/mount-and-pid-namespaces
  - linux/containers-and-virtualization/user-namespaces
  - linux/containers-and-virtualization/cgroup-v2-architecture
  - linux/networking-stack/network-namespaces-and-virtual-devices
related:
  - linux/security/seccomp
draft: false
---

# Lab: Build a Container from Scratch

About 150 lines of C and shell: namespaces, `pivot_root`, `/proc`, a cgroup limit, dropped capabilities, a seccomp filter, a veth pair, then `exec`.

:::info[Not yet written]
This page is a stub. See [the roadmap](../00-overview/roadmap.md) for what lands when.
:::
