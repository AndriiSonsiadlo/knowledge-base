---
id: how-to-use-this-section
title: "How to Use This Section"
sidebar_label: "How to use this"
sidebar_position: 6
tags: [linux]
prerequisites: []
draft: false
---

# How to Use This Section

Every convention this section uses, with a live example of each. The prose explaining the folder
ladder and the learning paths lands with the rest of folder 00; what follows is the component
gallery, which exists from the first day so that the conventions are visible while the section is
being written.

## Every page ends with a facts card

Four fixed rows, always in this order. The structure that matters and where it is defined, the code
path in a few hops, the command that shows the mechanism on a live system, and the single most
common wrong belief about the topic.

<KernelFacts
  structure={[["struct vm_area_struct", "include/linux/mm_types.h"]]}
  path="do_page_fault() → handle_mm_fault() → handle_pte_fault() → do_anonymous_page()"
  observe="perf trace -e 'exceptions:page_fault_user' -p $(pgrep -n bash)"
  trap="A major fault is not a fault that is worse. It is a fault that needed I/O. Most faults your process takes are minor, and minor faults are how ordinary memory allocation works." />

## Source references are pinned

Every reference into the kernel source names a file and a symbol and never a line number, because
line numbers rot within one release. Path resolution happens in
<Src file="fs/namei.c" symbol="path_openat" />, the allocator lives in
<Src file="mm/page_alloc.c" />, and <Src symbol="handle_mm_fault" /> is where a fault is resolved.
