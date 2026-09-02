---
id: misconceptions-index
title: "Index of Misconceptions"
sidebar_label: "Misconceptions"
sidebar_position: 9
tags: [linux, kernel]
prerequisites: []
draft: false
---

# Index of Misconceptions

Every widely-held wrong belief this section corrects, gathered in one place and linked to the
correction. Read only this page and you still walk away knowing which of your assumptions about the
kernel are wrong, even if you never open another page in this section.

Each entry below is a summary, not the full argument — the owning page carries the reasoning,
the code, and the diagram; this page exists so you can find the belief fast and know where to go
next.

## 00 — Overview

**"The kernel is a program that runs alongside my programs."** No — there is no kernel process
sitting in a run queue next to yours. The kernel is code your own process executes, in a different
privilege mode, and then stops executing when it returns to you.
[The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**"A system call is a function call into a library."** No — a library call is an ordinary jump your
compiler placed; a system call is a hardware-mediated privilege transition to an address you did not
choose and cannot change. `libc` wrapper functions like `write()` exist precisely to hide the
`SYSCALL` instruction underneath an ordinary-looking function call.
[The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**"The kernel can read my variables directly."** It can, physically — but it must not, and the
convention that it does not is enforced in code, not by the hardware alone: a raw pointer from user
space is never dereferenced directly. It goes through a checked copy routine that validates the
address is actually yours before touching it, turning what would be a kernel crash on a bad pointer
into an ordinary `-EFAULT` returned to the caller.
[The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**"Linux is an operating system."** The kernel is not an operating system by itself — it has no
shell, no compiler, no package manager, nothing a user would sit down and use. What people run is a
distribution: the kernel plus everything a distribution adds. "Linux" the kernel is one component of
that, not the whole of it.
[What Linux Actually Is](./what-linux-actually-is.md)

**"A newer kernel version means newer features on my machine."** Not reliably. Distribution kernels
backport fixes and even whole features from newer upstream releases onto an older base, so a
distribution's `6.1` kernel can legitimately contain code that first landed upstream in `6.9`. The
version number tells you the base a distribution started from, not the complete feature set actually
present.
[What Linux Actually Is](./what-linux-actually-is.md)

**"GNU/Linux is a political point."** It is also a straightforwardly technical one. Alpine Linux and
Android are both, unambiguously, Linux — they run the Linux kernel — and neither is GNU: Alpine
pairs the kernel with musl and BusyBox, Android with Bionic and its own userland. "Linux" and "GNU"
name independent things that are very often, but not always, combined.
[What Linux Actually Is](./what-linux-actually-is.md)

**"Distributions ship different kernels."** They ship different *configurations and patch sets* of
the same upstream kernel, not different kernels in any architectural sense. The syscall interface,
the VFS, and the rest of the mechanism described in this section are the same code everywhere.
[Distributions and What Actually Differs](./distributions-and-what-differs.md)

**"Alpine is small because its kernel is small."** Alpine's install footprint is small because of its
userland choices — musl instead of glibc, BusyBox instead of GNU coreutils — not because its kernel
is a stripped-down or different kernel. The kernel itself is ordinary upstream Linux with Alpine's
own config.
[Distributions and What Actually Differs](./distributions-and-what-differs.md)

**"The distribution decides how memory management works."** A distribution decides *defaults* — the
`sysctl` values a fresh install ships with, things like swappiness or overcommit policy — not the
underlying mechanism. The memory-management code itself is the same kernel code, unaffected by which
distribution is running it.
[Distributions and What Actually Differs](./distributions-and-what-differs.md)

## 02 — Guided Traces

**"`write()` returning means the data is on disk."** No — it means the data is in the page cache and
the kernel has accepted responsibility for it. Nothing about a successful `write()` says the bytes
have left RAM.
[The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)

**"`O_DIRECT` means synchronous."** No — `O_DIRECT` bypasses the page cache and writes (or DMAs)
straight from your buffer, but it still needs a flush to guarantee the device's own cache has
committed the data; skipping the page cache is not the same promise as durability.
[The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)

**"`fsync` on the file is enough."** Usually, but not always: if the write created a new file, the
*directory entry* that names it may need its own `fsync` (on the directory fd) before a crash can't
make the file disappear even though its contents are safely on disk.
[The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)

**"Page faults mean something is wrong."** No — they are the normal mechanism by which memory is
allocated one page at a time, deferred until the moment it's actually needed. A process taking zero
page faults after startup would be unusual, not healthy.
[The Life of a Page Fault](../02-guided-traces/the-life-of-a-page-fault.md)

**"A major fault is a worse fault."** It's not more severe, just more expensive: a major fault is one
that needed I/O, and I/O is slow relative to a memory access. "Major" describes the mechanism that
resolved it, not how badly anything went wrong.
[The Life of a Page Fault](../02-guided-traces/the-life-of-a-page-fault.md)

**"`malloc` returning non-`NULL` means the memory exists."** It means the *mapping* exists — the
kernel has agreed to service faults against that range if you touch it. Under Linux's default
overcommit behavior, the kernel can promise more virtual memory than the machine could ever back
with physical pages and RAM plus swap, and it is entirely possible for a later fault against that
promise to fail.
[The Life of a Page Fault](../02-guided-traces/the-life-of-a-page-fault.md)

**"The kernel copies each packet at each layer."** No — one `sk_buff` carries the packet through
every layer, and each layer that strips a header moves a pointer within that same buffer. The first
copy of the payload happens at `recv()`, not at any point before it.
[The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**"One packet, one interrupt."** True only under light load. NAPI disables interrupts on a busy
queue and switches to polling instead, precisely so a flood of small packets doesn't turn into a
flood of interrupts.
[The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**"`ping` measures the network."** It measures the network plus both kernels' queueing and
processing on the way in and out. A loaded host — on either end — inflates the number without a
single bit changing about the link between them.
[The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**"A container is a lightweight VM."** No — there is no guest kernel, no hypervisor, no second
instruction set being emulated or virtualized. A container's process runs on the exact same kernel,
scheduled by the exact same scheduler, as everything else on the host.
[The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**"Containers are a kernel feature."** The kernel provides namespaces, cgroups, capabilities, and
seccomp — four separate, independently useful mechanisms, none of them named "container" anywhere in
their implementation. "Container" is the name for a particular userspace assembly of those four; the
kernel has no idea it's building one.
[The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**"Root in a container is safe."** Only if a user namespace maps that root to an unprivileged UID on
the host. Without `CLONE_NEWUSER` (or an equivalent explicit UID remap), UID 0 inside the container
is the same UID 0 the host trusts completely, and any host resource the container's mount namespace
can still reach is reachable with full host root privilege.
[The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

## 03 — Boot and Init

**"GRUB boots Linux."** GRUB loads a file into memory and jumps to it. It never runs Linux code,
never understands processes or system calls, and is not present in memory in any meaningful sense
the moment after that jump — "boots Linux" credits the loader with work the kernel does entirely on
its own, once handed off to.
[Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**"Editing `grub.cfg` fixes it."** On a system that still regenerates it per kernel install
(Debian/Ubuntu), the edit survives only until the next kernel update silently discards it — the
durable fix is `/etc/default/grub` or `/etc/grub.d/`, followed by re-running `grub-mkconfig`. On BLS
systems (Fedora/RHEL 8+) it's worse than temporary: `grub.cfg` is closer to a static launcher, so an
edit there may not even be read at all.
[Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**"You need a boot loader."** You need something to find a kernel, find an initramfs, build a
command line, and hand over — but on UEFI, the kernel can do all four of those for itself as an EFI
stub. A boot loader is the common answer, not the only possible one.
[Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**"`bzImage` means bzip2."** It means *big zImage*. The original `zImage` format had a hard 512 KB
size limit; `bzImage` is the format that lifted it. The name predates bzip2 support in the kernel
build and has nothing to do with that compression algorithm.
[Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**"`vmlinuz` can be loaded into GDB."** Not usefully. `vmlinuz` is a `bzImage` — setup code plus a
compressed payload — not an ELF file with symbols. GDB needs `vmlinux` from the exact same build.
[Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**"The boot loader decompresses the kernel."** It doesn't. The boot loader's job ends at handoff;
the compressed payload carries its own decompressor and extracts itself once running.
[Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**"PID 1 is unkillable because it's root."** No — permissions were never the mechanism. The kernel
simply never delivers `SIGKILL`/`SIGSTOP` to the global init, and leaves every other signal at its
default (ignored) disposition unless PID 1 installs a handler; a non-root user's `kill -9 1` fails on
permissions before it would even reach this logic, and root's succeeds at sending and still does
nothing.
[`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**"`switch_root` is a syscall."** It's a userspace program (`/sbin/switch_root` or systemd's own
equivalent) built on top of the real syscalls, `pivot_root(2)` and `chroot(2)`/`mount(2)` with
`MS_MOVE`. The kernel has no `switch_root` entry point of its own.
[`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**"Zombie processes are a memory leak."** A zombie is a dead process whose exit status hasn't been
collected yet — it holds almost nothing but a `task_struct` and an exit code, kept around
specifically so a parent's `wait()` has something to read. It's bookkeeping, not a leak.
[`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**"`After=` makes it a dependency."** It only orders. A unit ordered `After=` something that never
starts for any reason simply starts as soon as its other constraints allow — the ordering directive
produces no requirement of its own.
[systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**"Targets are runlevels."** A runlevel was an ordered, numbered ladder; a target is an unordered
synchronisation label multiple units can reference, several of which may be reached in parallel. The
runlevel-named aliases exist for compatibility, not because targets work the same way.
[systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**"systemd is PID 1 doing everything."** The manager process is PID 1, but it delegates actual work
to a forked, `exec`ed process per unit, placed in its own cgroup for tracking — that cgroup is what
lets `systemctl status` account for every descendant process a unit spawns, even after a
double-fork tries to escape its parent.
[systemd: The Model](../03-boot-and-init/systemd-the-model.md)

## 04 — Kernel Architecture and Idioms

**"Modules are sandboxed."** No. A module is ordinary kernel code, executing with the same
privileges as every other kernel subsystem. There is no container, namespace, or capability boundary
around a loaded module — those mechanisms constrain user-space processes, not kernel code.
[Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**"A module crash only kills the module."** No. A fault inside a module's code is a kernel fault, in
kernel context, and it is handled exactly like a fault anywhere else in the kernel — an oops, and
possibly a panic if it happens somewhere the kernel cannot safely continue from. `rmmod` after a
module has faulted usually will not help, because the fault may have left kernel data structures in a
state the kernel cannot cleanly unwind from.
[Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**"Monolithic means one huge file, or one huge blob."** No. Monolithic describes the address-space
and privilege model, not the source layout: the kernel's source is spread across thousands of files,
most of a given build's code is optional and selected at configure time, and a running kernel may
load only a small fraction of the drivers physically present in the source tree.
[Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**"The kernel has no ABI."** No — it has an extremely strict *user-space* ABI, held stable for
decades (`man 2 syscalls` from 1995 mostly still works). What it does not have is a stable
*in-kernel* ABI between subsystems and modules.
[Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**"`EXPORT_SYMBOL_GPL` is a licence check on your code."** No. It is a link-time check on your
module's *declared* `MODULE_LICENSE` string — a string you write yourself. It cannot verify that
your source is actually GPL-compatible; it only refuses to resolve the symbol for a module that
didn't declare a GPL-compatible license.
[Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**"Modversions makes modules portable across kernel versions."** No — it makes an incompatibility
*detectable* at load time instead of silently corrupting memory at call time. That is closer to the
opposite of portability: it is precisely what stops an incompatible module from loading at all.
[Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

---

This index grows with the section — folders 05 through 19 add their own misconceptions here as they
land.
