---
id: roadmap
title: "Roadmap and Knowledge Graph"
sidebar_label: "Roadmap"
sidebar_position: 7
tags: [linux, kernel]
prerequisites: []
draft: false
---

# Roadmap and Knowledge Graph

Every page in this section declares what you need to have read first. The graph below is generated
from those declarations rather than drawn by hand, so it cannot disagree with the pages themselves —
and a page that named a prerequisite which does not exist, or a set of pages that depended on each
other in a loop, would fail the site build.

## The section at folder granularity

<KnowledgeGraph />

## Inside one folder

Folder-level edges hide a lot. Here is the page-level graph for the kernel architecture folder,
which is the one every later folder depends on:

<KnowledgeGraph folder="04-kernel-architecture-and-idioms" />

## Learning paths

The six routes through this section. Each is an ordered list, and every page's prerequisites appear
earlier in its own path.

Paths are filled in as the folders they cross are written. Folders 00 through 04 exist now; the
rest of the section is scaffolded and being written.

### I just want to understand my machine

1. [The kernel/user-space boundary](./the-kernel-userspace-boundary.md)
2. [What Linux actually is](./what-linux-actually-is.md)
3. [What happens when you type `ls`](../02-guided-traces/what-happens-when-you-type-ls.md)
4. [The life of a `write()`](../02-guided-traces/the-life-of-a-write.md)
5. [From power-on to login prompt](../02-guided-traces/from-power-on-to-login-prompt.md)

### I want to read kernel source

1. [The hardware the kernel assumes](./hardware-the-kernel-assumes.md)
2. [Monolithic, with modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)
3. [The source tree, mapped](../04-kernel-architecture-and-idioms/the-source-tree-map.md)
4. [The kernel is not C you know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)
5. [Kernel data structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)
6. [`container_of` and embedded structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)
