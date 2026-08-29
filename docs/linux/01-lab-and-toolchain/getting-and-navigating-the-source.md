---
id: getting-and-navigating-the-source
title: "Getting the Source"
sidebar_label: "Getting the source"
sidebar_position: 2
tags: [linux, kernel, lab]
prerequisites:
  - linux/lab-and-toolchain/the-lab-machine
draft: false
---

# Getting the Source

Cloning or downloading the pinned kernel, what the repository costs in disk and time, and a first orientation pass through the tree.

The Linux kernel source tree is not a codebase you read front to back — at tens of millions of lines
across every driver, filesystem, and architecture the kernel supports, nobody reads all of it, ever.
It is a reference you learn to *query*: given a syscall name, a struct, a config symbol, or a boot
message, find the exact lines responsible. Getting a copy onto your own machine matters for that
reason specifically — `git grep` over a real, checked-out tree answers questions no search engine
answers as precisely or as fast, and every `<Src>` link anywhere in this section points at the same
tree, at the same pinned commit, that you are about to check out.

## Clone, or tarball?

There are three ways to get the source, and they trade size for capability.

| Method | Size | What you lose | When it's right |
|---|---|---|---|
| Full clone (`git clone`, full history) | ~5 GB | Nothing | Kernel archaeology: `git log`, `git blame`, `git bisect` on a specific file or subsystem |
| Shallow clone (`--depth 1 --branch v6.18`) | ~1.5 GB | All history — `git log` on any file shows exactly one commit | A first pass through the tree; most labs in this section |
| Release tarball from kernel.org | Smallest, no `.git/` at all | History, and `git` itself — no `git grep`, no `git log`, nothing but files on disk | Reading a fixed snapshot with ordinary tools, no intention of using `git` at all |

`git log` on a single file is, on its own, one of the single best tools for understanding *why* a
piece of kernel code looks the way it does — the commit message next to a subtle-looking line very
often explains a bug it fixed or a race it closed, in a way the code alone never will. A shallow clone
throws that away entirely; it is not a smaller version of that capability, it is the complete absence
of it. For a first pass through the tree, that's a fine trade — you're finding your way, not doing
archaeology yet. **Recommendation for this section: the shallow clone at the pinned tag.** Reach for a
full clone later, on the specific subsystem you're actually investigating, rather than paying 5 GB up
front for history you won't touch yet.

## Getting v6.18 exactly

Every command and every `<Src>` link in this section is pinned to kernel **v6.18**. Get exactly that
tag, not "whatever `master` happens to be today":

```text
$ mkdir -p ~/kernel-lab && cd ~/kernel-lab
$ git clone --depth 1 --branch v6.18 \
    https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git linux
$ cd linux
```

Two commands confirm you actually got what you asked for — a shallow clone silently gives you the tip
of the tag, but it's worth checking rather than assuming:

```text
$ git describe --tags
v6.18

$ make kernelversion
6.18
```

`git describe --tags` reads the tag your clone is checked out at; `make kernelversion` reads it a
different way, out of the top-level <Src file="Makefile" /> — `VERSION`, `PATCHLEVEL`, and `SUBLEVEL`
variables near the very top of the file are concatenated into the string every kernel build reports as
its own version. If the two disagree, or `make kernelversion` fails outright, something about the
checkout is wrong before you've built anything.

## The first orientation pass

A first pass through the top level, one line each — enough to guess where something lives without yet
knowing the tree in depth. Folder 04's source-tree page goes much deeper into how these are organized
and why; this table exists so you can find your way today.

| Directory | What's there |
|---|---|
| `arch/` | Per-architecture code — entry points, page tables, the parts of the kernel that cannot be architecture-neutral |
| `block/` | The block layer: request queues, I/O schedulers, the code between a filesystem and a block device |
| `certs/` | Keys and infrastructure for module and kernel signature verification |
| `crypto/` | The kernel's own crypto API and algorithm implementations |
| `Documentation/` | Source-controlled documentation, versioned with the code — see below |
| `drivers/` | The overwhelming majority of the tree by line count: device drivers, organized by subsystem |
| `fs/` | Filesystems — VFS core plus every concrete filesystem implementation |
| `include/` | Public and internal headers, including the UAPI headers userspace itself compiles against |
| `init/` | Kernel start-of-day: `start_kernel()` and the earliest boot sequence |
| `io_uring/` | The `io_uring` asynchronous I/O interface |
| `ipc/` | System V and POSIX inter-process communication: message queues, semaphores, shared memory |
| `kernel/` | Core kernel subsystems that aren't a filesystem, driver, or network code — scheduler, signals, `cgroups`, timekeeping |
| `lib/` | Generic library code shared across the kernel: string routines, data structures, compression |
| `mm/` | Memory management: paging, the page allocator, `mmap`, reclaim |
| `net/` | The networking stack, protocol by protocol |
| `rust/` | Kernel-side support for writing drivers and subsystems in Rust |
| `samples/` | Example code, meant to be read and copied, not built into a production kernel |
| `scripts/` | Build-system and developer tooling — `Kconfig` frontends, checkers, the scripts that run under `make` |
| `security/` | LSM infrastructure and concrete security modules (SELinux, AppArmor, and others) |
| `sound/` | ALSA and the kernel's audio subsystem |
| `tools/` | Userspace-facing tools shipped alongside the kernel — `perf`, `bpftool`, `tools/testing/selftests` |
| `usr/` | Build-time generation of the default initramfs image |
| `virt/` | Architecture-independent virtualization infrastructure (KVM's non-arch-specific half) |

## Finding things

Three tools, in the order you should actually reach for them:

1. **`git grep -n`** — fast, and it respects the tree exactly as checked out, no index to go stale.
   This is the everyday tool: grepping the real source for an exact string or symbol name.
2. **[elixir.bootlin.com](https://elixir.bootlin.com/linux/v6.18/source)** — a cross-referenced,
   identifier-aware search across kernel versions, with every use of a symbol linked. This is what
   every `<Src>` link in this section resolves into, and it's the fastest way to check whether a
   symbol you're about to cite actually exists at the pinned tag before you write it down.
3. **`cscope`/`ctags`** — build a local index once, then jump to definitions and callers straight from
   your editor. Worth the one-time setup cost once you're spending real time in the tree rather than
   making a single query.

A real worked example: find where the `read()` syscall is actually defined.

```text
$ git grep -n "SYSCALL_DEFINE3(read"
fs/read_write.c:722:SYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf, size_t, count)
```

One hit, in `fs/read_write.c` — the `SYSCALL_DEFINE3` macro expands into the entry point the syscall
table dispatches to, and its body immediately calls <Src file="fs/read_write.c" symbol="ksys_read" />,
the actual implementation shared with the kernel's own internal callers. That two-step shape — a thin
`SYSCALL_DEFINEn` wrapper around a real `ksys_*`/`do_*` function — repeats throughout `fs/read_write.c`
and across most of the syscall surface; folder 02 covers why.

## Documentation/ is part of the source

`Documentation/` is not a wiki bolted on beside the code — it's a directory in the same tree, versioned
with the same commits, reviewed the same way as any other patch, and it renders directly into
[docs.kernel.org](https://docs.kernel.org/). That means it's exactly as current as the checkout you
just made, never further out of date than the code itself, and it is considerably more complete than
most readers expect on first contact — subsystem design documents, the admin guide, the full API
reference for things like the DMA and locking APIs are all in there, not scattered across external wikis.

```text
$ ls Documentation/ | head
ABI
CodingStyle
Kconfig
Makefile
PCI
RCU
SubmittingPatches
accel
accounting
admin-guide
```

When later pages in this section point you at `Documentation/`, that's what they mean: files sitting
right there in the tree you just cloned, not a separate site to go find.

<Lab host="any-linux" title="Clone the pinned kernel and find a syscall" time="15 min">

1. Make the lab directory and clone the pinned tag:

   ```text
   $ mkdir -p ~/kernel-lab && cd ~/kernel-lab
   $ git clone --depth 1 --branch v6.18 \
       https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git linux
   ```

2. Confirm the version:

   ```text
   $ cd linux && make kernelversion
   6.18
   ```

3. Find the `read()` syscall's definition:

   ```text
   $ git grep -n "SYSCALL_DEFINE3(read"
   fs/read_write.c:722:SYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf, size_t, count)
   ```

   Expect exactly one hit, in `fs/read_write.c`.

4. Take a first look at the documentation tree:

   ```text
   $ ls Documentation/ | head
   ```

**If it fails:** `git.kernel.org` is occasionally slow or blocked from some networks. If the clone
hangs or refuses to connect, use the GitHub mirror instead, same tag:

```text
$ git clone --depth 1 --branch v6.18 https://github.com/torvalds/linux.git linux
```

</Lab>

<KernelFacts
  structure={[["Makefile", "the top-level build entry point; VERSION/PATCHLEVEL at the top define the version"]]}
  path="git clone --depth 1 --branch v6.18 → make kernelversion → git grep"
  observe="make kernelversion"
  trap="A shallow clone saves 3 GB and costs you `git log`, `git blame`, and `git bisect` — which are the three reasons to have the source locally at all. Shallow is for a first look, not for investigating." />

## References

- [git.kernel.org — the stable tree](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git)
  — the canonical repository this page clones from, and the source of the `v6.18` tag pinned throughout
  this section.
- [Kernel documentation — Submitting patches](https://docs.kernel.org/process/submitting-patches.html)
  — why the tree is laid out and reviewed the way it is; worth a skim now, essential once folder 19
  covers contributing upstream.
- [elixir.bootlin.com — Linux source, v6.18](https://elixir.bootlin.com/linux/v6.18/source)
  — the cross-referencer every `<Src>` link in this section resolves into; use it to verify a symbol
  before citing it, exactly as this page's own commands were checked.
