---
id: glossary
title: "Glossary"
sidebar_label: "Glossary"
sidebar_position: 8
tags: [linux, kernel]
prerequisites: []
draft: false
---

# Glossary

Every term below links to the one page that owns and genuinely defines it, so "where did this come from" always has an answer. The list only covers folders 00–04 so far and grows as later folders land — a term you expect but can't find here probably belongs to a page that hasn't been written yet.

**ABI (application binary interface)** — the binary-level contract a program compiles against; this section uses it specifically for the kernel's promise that it never breaks the *user-space* ABI (syscalls, `/proc`, ELF layout) across releases, even though it makes no such promise internally. [What Linux Actually Is](./what-linux-actually-is.md)

**Boot loader** — the software that runs after firmware and before the kernel, whose entire job is four things: find a kernel, find an initramfs, build a command line, and hand over control. [Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**Boot variable** — an NVRAM entry (`Boot0000`, `Boot0001`, …) plus a `BootOrder` list that tells UEFI firmware which `.efi` file to run and in what order; this state lives in firmware, not on disk. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**`bzImage`** — the actual bootable kernel file: real-mode setup code, a setup header, and a compressed payload that self-extracts on first run. "bz" stands for "big zImage," unrelated to the bzip2 algorithm. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**cgroup** — a directory in the cgroupfs virtual filesystem whose auto-populated files (`cpu.weight`, `memory.max`, `io.max`, `pids.max`, …) express resource limits; it answers "what can this process *use*," a question orthogonal to namespaces. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**`container_of`** — a macro that recovers a pointer to a containing struct from a pointer to one of its embedded fields, by subtracting that field's compile-time offset and casting the result to the containing type. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**`defconfig`** — the `make defconfig` target that produces a sane, complete `.config` close to what a real distribution ships; the usual starting point before hand-tuning debug options. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Dirty page** — a page-cache page holding data that has been modified in RAM but not yet written back to its backing device. [The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)

**Distribution** — a specific packaging of the kernel plus a userland (C library, init system, package manager, patch set, and kernel configuration), with its own name, release cadence, and support policy. [What Linux Actually Is](./what-linux-actually-is.md)

**`ERR_PTR`** — a function that encodes a negative `errno` value as a pointer, exploiting the fact that the top few thousand bytes of kernel address space are never a valid allocation, so the encoded value is unambiguously distinguishable from a real pointer. [Error Handling](../04-kernel-architecture-and-idioms/error-handling-idioms.md)

**ESP (EFI System Partition)** — a FAT32 partition that UEFI firmware can read directly, holding `.efi` boot loader files; it replaces the MBR's chainloading trick that legacy BIOS relies on. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**`EXPORT_SYMBOL_GPL`** — the macro placed after a kernel function's definition that makes it callable from a module whose declared license the kernel recognizes as GPL-compatible; the plain `EXPORT_SYMBOL` allows any module regardless of license. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**Freestanding C** — a C implementation with no operating system underneath it to supply a standard library, a `main()` entry point, or a heap; the kernel supplies its own equivalents of everything (`printk`, `kmalloc`, its own boot entry) because it *is* the OS. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**GRO (Generic Receive Offload)** — merges several related small segments arriving close together (e.g. TCP segments from the same stream) into one larger `sk_buff` before the packet climbs further up the stack, trading a small merge cost for large savings in per-header processing. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**`__init`** — an annotation placing a function in a discardable code section whose memory is freed once boot completes; calling it later dereferences freed memory. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Initcall** — a function pointer a built-in driver or subsystem registers into a named linker section at build time, which the kernel walks and calls at the appropriate point in boot rather than being invoked by name from `start_kernel()`. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initcall level** — one of nine ordered phases (`early`, `pure`, `core`, `postcore`, `arch`, `subsys`, `fs`, `device`, `late`) that group initcalls; a driver can pick its level, but not an ordering relative to other drivers within it. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initramfs** (build sense) — a gzip-compressed `cpio` archive the kernel unpacks directly into an in-memory `tmpfs` mounted as `/`, before any real block device or filesystem driver is touched; the kernel then executes `/init` from it as PID 1. [A Minimal Root Filesystem](../01-lab-and-toolchain/a-minimal-rootfs.md)

**Intrusive list** — a container design where the link field that makes an object a list member lives inside the object's own struct rather than in a separately allocated node, costing no extra allocation on insert at the price of baking list membership into the object's type. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Journal** — systemd's structured log store, where each entry is a set of key-value fields rather than a text line, letting it be filtered by unit, boot, or priority as a query; whether a previous boot's log survives depends on the `Storage=` setting. [systemd in Practice, and Debugging a Broken Boot](../03-boot-and-init/systemd-in-practice-and-boot-debugging.md)

**KASAN** — the Kernel Address Sanitizer, which instruments every memory access to catch use-after-free and out-of-bounds reads/writes at the exact faulting instruction, by poisoning freed and redzone memory and checking accesses against it. [What Goes Wrong in Kernel C](../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md)

**KASLR** — Kernel Address Space Layout Randomization; x86-64 randomizes the kernel's load address on every boot by default, which shifts the running kernel's addresses away from those in a static `vmlinux` unless disabled with `nokaslr`, breaking naive breakpoint resolution. [Debugging the Kernel with GDB](../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md)

**Kconfig symbol** — a named configuration option declared by a `config` entry in a `Kconfig` file, with a type, dependency rules, a default, and help text, that governs whether a piece of code is compiled into the kernel at all. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**Kernel** — the single upstream Linux project: one source tree, one `git` history, one maintainer chain, releasing on a roughly nine-week cadence — distinct from any distribution's userland or packaging around it. [What Linux Actually Is](./what-linux-actually-is.md)

**Kernel command line** — the text handed to the kernel at the moment of handoff (via the setup header's `cmd_line_ptr`), the only channel for changing kernel behavior before any user space exists. [The Kernel Command Line](../03-boot-and-init/the-kernel-command-line.md)

**Kernel thread** — a schedulable kernel-code entity with no user process to be charged to (visible via `ps` in square brackets, e.g. `[kworker/0:1]`), forked from `kthreadd`, distinct from kernel code that runs inside a process's own context. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**`kobject`** — the generic, embeddable unit that participates in the kernel's object graph: a name, a reference count, a parent pointer, and a pointer to its type; never allocated standalone, always embedded inside a larger structure. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`kref`** — a thin standard wrapper around a `refcount_t` plus the convention of pairing it with a release callback; `kref_put` invokes the release function exactly once, when the count it decrements reaches zero. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**`kset`** — a collection of `kobject`s that is itself a `kobject` (it embeds one), giving a group of objects its own place — and its own directory — in the object graph sysfs renders. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`ktype` (`kobj_type`)** — the behavior attached to a `kobject` — its release function and its attribute (`show`/`store`) operations — shared by every `kobject` of a given kind. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`list_head`** — the kernel's circular, doubly-linked intrusive list node/head type (two pointers, `next` and `prev`), embedded directly as a field inside the objects it links. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Lockdep** — a runtime validator that builds a graph of lock acquisition ordering as the kernel actually runs and reports the first sequence that could deadlock, even before that exact sequence has actually occurred. [What Goes Wrong in Kernel C](../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md)

**LTS (long-term support)** — a designation given to a subset of kernel releases for which the community keeps backporting fixes for years after an ordinary release would have been abandoned. [What Linux Actually Is](./what-linux-actually-is.md)

**Module** — relocatable object code linked into an already-running kernel at load time instead of build time, running with exactly the same privileges as code compiled into `vmlinux`. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**Modversions** — a build-time mechanism (`CONFIG_MODVERSIONS`) that computes a CRC over each exported symbol's type signature and checks it at module-load time, refusing to load a module whose recorded CRC no longer matches the running kernel's. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**Monolithic kernel** — a kernel design where every subsystem runs in one address space at one privilege level, calling each other through ordinary function calls with no isolation boundary between them; drivers can still be compiled in or loaded as modules. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**Namespace** — a kernel mechanism that changes what a process can *see* (which processes, network devices, hostname, IPC objects, etc. are visible or enumerable) without affecting what resources it's allowed to *use*; created via `CLONE_NEW*` flags to `clone()`. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**NAPI** — the receive-path model where a hardware interrupt only schedules polling rather than processing the packet itself; under light load it behaves like one interrupt per packet, but under heavy load the queue's interrupts are disabled and a poll loop drains it instead, bounding interrupt cost. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**`offsetof`** — a compile-time constant giving the byte offset of a named field within its struct type, with no runtime cost; it is the arithmetic building block `container_of` is built on. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**Ordering versus requirement** — in systemd, `Requires=` and `After=` are independent axes: `Requires=` says what else must start as a dependency, `After=` says only which of two already-starting units goes first; declaring one does not imply the other. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**overlayfs** — the filesystem that merges a stack of read-only layers plus one writable layer into what looks like a single ordinary filesystem; a read resolves top-down through the layers, and writing a file that only exists in a lower layer copies it into the writable layer first. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**Page cache** — the in-RAM cache of file-backed pages that ordinary buffered I/O goes through; a `write()` copies bytes into page-cache pages and marks them dirty rather than touching the device immediately, so the data can exist only in RAM at the moment the call returns. [The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)

**Page fault** (minor/major) — a CPU exception raised when an instruction touches a virtual address with no valid page-table entry; "minor" means the kernel resolved it without I/O (zero page, page-cache hit, copy-on-write copy), "major" means it had to block on a device (disk read or swap-in). [The Life of a Page Fault](../02-guided-traces/the-life-of-a-page-fault.md)

**PID 1** — the first user-space process, distinguished from every other process only by having no parent, which is the single cause behind its special signal handling, orphan-reaping duty, and the kernel panic that follows if it ever exits. [`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**`pivot_root`** — the call that swaps a process's root directory for another directory already mounted in its (private) mount namespace, changing what an absolute path resolves through; distinct from `chroot`, which affects every process sharing that mount namespace rather than establishing a new root wholesale. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**QEMU gdbstub** (`-s -S`) — `-s` opens a GDB stub listening on TCP port 1234 exposing the guest's virtual CPU; `-S` freezes the guest at its first instruction until GDB tells it to continue, letting GDB drive the CPU directly regardless of whether guest software is responsive. [Debugging the Kernel with GDB](../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md)

**`refcount_t`** — a dedicated reference-counting type (distinct from `atomic_t`) that saturates instead of wrapping on overflow and refuses to increment from zero, closing two failure modes a plain atomic counter has when used as an object's lifetime counter. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**rootfs** — the always-present `tmpfs`-family filesystem the kernel mounts at `/` before anything else exists, whether or not an initramfs archive is ever unpacked into it. [initramfs and Early User Space](../03-boot-and-init/initramfs-and-early-userspace.md)

**Secure Boot** — a signature-verification gate that checks, at each handoff from firmware to boot loader to kernel, whether the thing about to execute is signed by a key the machine trusts; it verifies provenance only, not the safety of what runs. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**Setup header** — the fixed-layout struct inside a `bzImage` that forms the binary contract between the boot loader and the kernel, specifying which fields the loader must fill in (like `cmd_line_ptr`, `ramdisk_image`) versus only read. [Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**`sk_buff`** — the single structure that represents a packet through its entire trip up the networking stack, carrying both its bytes and the kernel's accumulating understanding of them; each layer strips a header by moving a pointer, not by copying. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**sparse** — a separate static-checking tool (`make C=1`/`C=2`) that understands the kernel's address-space annotations (`__user`, `__percpu`, `__iomem`, `__rcu`) as real types with real rules, catching misuse the C compiler itself silently accepts. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Sysfs attribute** — a small `struct attribute` (name plus mode) representing one exposed value; reading or writing the corresponding file in `/sys` calls the owning `ktype`'s `show()`/`store()` functions live, computing the value on access rather than reading stored bytes. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**System call** — a deliberate, synchronous request a user process makes for a named kernel service, initiated by executing a trapping instruction and blocking (from the process's view) until the kernel returns. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**Taint** — a kernel-wide flag set when something happens that maintainers should weigh when reading a bug report — for example loading a module with a non-GPL-compatible license — recorded as a bitmask readable from `/proc/sys/kernel/tainted`. [Kernel Modules](../04-kernel-architecture-and-idioms/modules-in-practice.md)

**Target** — a systemd synchronization point with no process or executable of its own, just a name other units order themselves around, unlike a numbered SysV runlevel. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**Tristate** — a Kconfig symbol type with three legal values — `n` (absent), `y` (built into `vmlinux`), or `m` (built as a separate loadable module) — as opposed to `bool`'s two. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**UEFI** — the modern firmware model that behaves like a small OS: it reads a normal FAT32 partition, loads `.efi` executables, and exposes boot-services/runtime-services APIs, in contrast to legacy BIOS's real-mode, interrupt-driven model. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Unit** — anything systemd manages; its filename suffix (`.service`, `.socket`, `.target`, `.mount`, `.timer`, `.path`, `.slice`) says what kind of thing it represents. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**`__user`** — an annotation marking a pointer as pointing into user-space address space, which must never be dereferenced directly in kernel context; enforced only by sparse, not the compiler itself. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**User space** — code the machine does not trust with the hardware directly (shells, browsers, ordinary programs); it has its own address space and can only touch what its mappings and file descriptors permit. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**Vermagic** — a string embedded in both a compiled module and the running kernel (kernel release, SMP/preemption config, module-unload/modversions support, arch token) that must match exactly for a module to load, checked independently of and before modversions. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**`vmlinux`** — the uncompressed ELF kernel image carrying full DWARF debug symbols when `CONFIG_DEBUG_INFO` is on; it is not bootable itself and exists to be read by tools like GDB. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**`vmlinuz`** — the conventional installed name (e.g. `/boot/vmlinuz-$(uname -r)`) a distribution gives to a copy of its `bzImage`; same file, different name and location. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Writeback** — the kernel-driven, deferred process — kthreads flushing pages once a dirty-memory or age limit is crossed — that moves dirty pages back to their filesystem; "later" is typically tens of seconds, not milliseconds. [The Life of a `write()`](../02-guided-traces/the-life-of-a-write.md)
