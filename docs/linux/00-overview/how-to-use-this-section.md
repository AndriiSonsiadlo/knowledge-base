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

## Labs state where they run

Every lab carries a host badge. `QEMU lab` needs the virtual machine from
[Setting Up a Lab](../01-lab-and-toolchain/the-lab-machine.md); `Any Linux` runs anywhere;
`WSL2 OK` is explicitly confirmed to work under WSL2. Every lab shows expected output, not just
commands.

<Lab host="qemu" title="Confirm your lab kernel is the pinned version" time="2 min">

1. Boot the lab VM and run:

   ```bash
   uname -r
   ```

2. Expected output — the version string starts with the pinned release:

   ```text
   6.18.0
   ```

**If it fails:** you booted the distribution's kernel rather than the one you built. Check the
`-kernel` argument in your QEMU invocation.

</Lab>

## Videos are linked, never stored

Where a talk develops an idea better than a page can, it is embedded. The video stays on its own
host; nothing is committed to this repository.

## Terminal sessions are replayable

Tool pages carry recorded sessions you can scrub through. They are text, not video — a few
kilobytes each — and the decisive output always appears as a code block too, because the player
does not render without JavaScript and the offline search cannot index it.

<Cast src="/casts/linux/hello.cast" caption="Checking the running kernel version in the lab VM" />

```text
$ uname -r
6.18.0
```

## Pages end with annotated references

Two to six entries, each saying why you would click it. Never a bare URL.

- [Docusaurus admonitions](https://docusaurus.io/docs/markdown-features/admonitions) — the five
  callout types this section uses, and nothing beyond them.
- [asciinema player](https://docs.asciinema.org/manual/player/) — options and keyboard controls for
  the recorded terminal sessions above.
- [Bootlin Elixir cross-referencer](https://elixir.bootlin.com/linux/v6.18/source) — where every
  `<Src>` link in this section points, pinned to v6.18.
