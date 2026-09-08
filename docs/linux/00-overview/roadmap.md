---
id: roadmap
title: "Roadmap"
sidebar_label: "Roadmap"
sidebar_position: 7
tags: [linux, kernel]
prerequisites: []
draft: false
---

# Roadmap

Every page in this section declares its prerequisites in front matter, and the build fails on a
prerequisite that does not resolve to a real page or on a dependency cycle. The *Before this*,
*Next*, and *Related* chips at the top and bottom of every page are generated from those
declarations rather than hand-maintained, so the page you are on always knows what it needs. This
page is the editorial route through it — the order a human would actually want to read in, not the
raw dependency graph.

## Learning paths

Paths are filled in as the folders they cross are written. Folders 00 through 13 exist now; the
rest of the section is specified but not yet scaffolded.

<LearningPath
  title="I just want to understand my machine"
  steps={[
    ["The kernel/user-space boundary", "./the-kernel-userspace-boundary.md"],
    ["What Linux actually is", "./what-linux-actually-is.md"],
    ["What happens when you type ls", "../02-guided-traces/what-happens-when-you-type-ls.md"],
    ["The life of a write()", "../02-guided-traces/the-life-of-a-write.md"],
    ["From power-on to login prompt", "../02-guided-traces/from-power-on-to-login-prompt.md"],
    ["Distributions and what actually differs", "./distributions-and-what-differs.md"],
    ["`/proc` as the process interface", "../06-processes-and-threads/proc-as-the-process-interface.md"],
    ["What `free` and RSS really tell you", "../08-memory-management/what-free-and-rss-really-say.md"],
    ["Priorities, nice, and weights", "../07-scheduling/priorities-nice-and-weights.md"],
    ["Why the VFS exists", "../11-vfs-and-filesystems/why-vfs-exists.md"],
    ["The storage stack, mapped", "../12-block-layer-and-storage/the-block-layer-map.md"],
    ["The network stack, mapped", "../13-networking-stack/the-network-stack-map.md"],
  ]} />

<LearningPath
  title="I want to read kernel source"
  steps={[
    ["The hardware the kernel assumes", "./hardware-the-kernel-assumes.md"],
    ["Monolithic, with modules", "../04-kernel-architecture-and-idioms/monolithic-with-modules.md"],
    ["The source tree, mapped", "../04-kernel-architecture-and-idioms/the-source-tree-map.md"],
    ["The kernel is not C you know", "../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md"],
    ["Kernel data structures", "../04-kernel-architecture-and-idioms/kernel-data-structures.md"],
    ["container_of and embedded structs", "../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md"],
    ["Error-handling idioms", "../04-kernel-architecture-and-idioms/error-handling-idioms.md"],
    ["The entry path", "../05-syscalls-and-the-boundary/the-entry-path.md"],
    ["`task_struct`: the anatomy of a task", "../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md"],
    ["`mm_struct` and VMAs", "../08-memory-management/mm-struct-and-vmas.md"],
    ["Why kernel concurrency is different", "../09-concurrency-and-locking/why-kernel-concurrency-is-different.md"],
  ]} />

<LearningPath
  title="I want to build and debug a kernel"
  steps={[
    ["The lab machine", "../01-lab-and-toolchain/the-lab-machine.md"],
    ["Getting and navigating the source", "../01-lab-and-toolchain/getting-and-navigating-the-source.md"],
    ["Building a kernel", "../01-lab-and-toolchain/building-a-kernel.md"],
    ["A minimal rootfs", "../01-lab-and-toolchain/a-minimal-rootfs.md"],
    ["Booting your kernel in QEMU", "../01-lab-and-toolchain/booting-your-kernel-in-qemu.md"],
    ["Debugging the kernel with GDB", "../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md"],
    ["A full-system VM and WSL2", "../01-lab-and-toolchain/a-full-system-vm-and-wsl2.md"],
  ]} />

<LearningPath
  title="I want to understand boot"
  steps={[
    ["From power-on to login prompt", "../02-guided-traces/from-power-on-to-login-prompt.md"],
    ["Firmware: BIOS and UEFI", "../03-boot-and-init/firmware-bios-and-uefi.md"],
    ["The boot chain", "../03-boot-and-init/the-boot-chain.md"],
    ["Bootloaders: GRUB and friends", "../03-boot-and-init/bootloaders-grub-and-friends.md"],
    ["The kernel image", "../03-boot-and-init/the-kernel-image.md"],
    ["Early boot and arch setup", "../03-boot-and-init/early-boot-and-arch-setup.md"],
    ["start_kernel and initcalls", "../03-boot-and-init/start-kernel-and-initcalls.md"],
    ["initramfs and early userspace", "../03-boot-and-init/initramfs-and-early-userspace.md"],
    ["switch_root and PID 1", "../03-boot-and-init/switch-root-and-pid-1.md"],
    ["systemd: the model", "../03-boot-and-init/systemd-the-model.md"],
  ]} />

<LearningPath
  title="My boot is broken"
  steps={[
    ["The kernel command line", "../03-boot-and-init/the-kernel-command-line.md"],
    ["systemd in practice and boot debugging", "../03-boot-and-init/systemd-in-practice-and-boot-debugging.md"],
    ["initramfs and early userspace", "../03-boot-and-init/initramfs-and-early-userspace.md"],
    ["Debugging the kernel with GDB", "../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md"],
  ]} />

Crash and oops reading lands with folder 17.

<LearningPath
  title="I want to write a module"
  steps={[
    ["Monolithic, with modules", "../04-kernel-architecture-and-idioms/monolithic-with-modules.md"],
    ["Kconfig and Kbuild", "../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md"],
    ["Modules in practice", "../04-kernel-architecture-and-idioms/modules-in-practice.md"],
    ["Exported symbols and the module ABI", "../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md"],
    ["Reference counting and lifetime", "../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md"],
    ["kobjects, sysfs, and the object model", "../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md"],
    ["Memory safety in kernel C", "../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md"],
  ]} />

A real character driver is built in [folder 14's lab](../14-device-drivers-and-hardware/lab-a-character-driver.md).

<LearningPath
  title="My server is slow"
  steps={[
    ["Diagnosing scheduling latency", "../07-scheduling/diagnosing-scheduling-latency.md"],
    ["What `free` and RSS really tell you", "../08-memory-management/what-free-and-rss-really-say.md"],
    ["Reclaim, LRU, and kswapd", "../08-memory-management/reclaim-lru-and-kswapd.md"],
    ["Interrupt affinity", "../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md"],
    ["cgroup CPU control", "../07-scheduling/cgroup-cpu-control.md"],
    ["Diagnosing I/O problems", "../12-block-layer-and-storage/diagnosing-io-problems.md"],
    ["Diagnosing network problems", "../13-networking-stack/diagnosing-network-problems.md"],
  ]} />

The tooling to go with all of this lands with folder 17.

<LearningPath
  title="I want to understand memory"
  steps={[
    ["The virtual address space", "../08-memory-management/the-virtual-address-space.md"],
    ["Page tables and the walk", "../08-memory-management/page-tables-and-the-walk.md"],
    ["`mm_struct` and VMAs", "../08-memory-management/mm-struct-and-vmas.md"],
    ["The page fault handler", "../08-memory-management/the-page-fault-handler.md"],
    ["Demand paging and copy-on-write", "../08-memory-management/demand-paging-and-cow.md"],
    ["The page allocator", "../08-memory-management/the-page-allocator.md"],
    ["Folios and compound pages", "../08-memory-management/folios-and-compound-pages.md"],
    ["The page cache", "../08-memory-management/the-page-cache.md"],
    ["Reclaim, LRU, and kswapd", "../08-memory-management/reclaim-lru-and-kswapd.md"],
    ["What `free` and RSS really tell you", "../08-memory-management/what-free-and-rss-really-say.md"],
  ]} />

<LearningPath
  title="I want to write correct concurrent kernel code"
  steps={[
    ["Why kernel concurrency is different", "../09-concurrency-and-locking/why-kernel-concurrency-is-different.md"],
    ["Memory ordering and barriers", "../09-concurrency-and-locking/memory-ordering-and-barriers.md"],
    ["Atomic operations", "../09-concurrency-and-locking/atomics-and-refcounts.md"],
    ["Spinlocks", "../09-concurrency-and-locking/spinlocks.md"],
    ["Mutexes and semaphores", "../09-concurrency-and-locking/mutexes-and-semaphores.md"],
    ["Seqlocks", "../09-concurrency-and-locking/seqlocks.md"],
    ["RCU: the idea", "../09-concurrency-and-locking/rcu-the-idea.md"],
    ["RCU in practice", "../09-concurrency-and-locking/rcu-in-practice.md"],
    ["Reader-writer locks", "../09-concurrency-and-locking/rwlocks-and-rwsems.md"],
    ["Choosing a lock", "../09-concurrency-and-locking/choosing-a-lock.md"],
    ["Finding locking bugs", "../09-concurrency-and-locking/finding-locking-bugs.md"],
  ]} />

The storage path assumes the "I want to understand memory" path above, and its path-lookup step leans
on RCU from the concurrency path.

<LearningPath
  title="I want to understand storage"
  steps={[
    ["Why the VFS exists", "../11-vfs-and-filesystems/why-vfs-exists.md"],
    ["The four VFS objects", "../11-vfs-and-filesystems/the-four-objects.md"],
    ["Path lookup and the dcache", "../11-vfs-and-filesystems/path-lookup-and-the-dcache.md"],
    ["`open`, `read`, `write` in the kernel", "../11-vfs-and-filesystems/open-read-write-in-the-kernel.md"],
    ["Journaling and crash consistency", "../11-vfs-and-filesystems/journaling-and-crash-consistency.md"],
    ["ext4", "../11-vfs-and-filesystems/ext4.md"],
    ["The storage stack, mapped", "../12-block-layer-and-storage/the-block-layer-map.md"],
    ["Block devices and `gendisk`", "../12-block-layer-and-storage/block-devices-and-gendisk.md"],
    ["The `bio`", "../12-block-layer-and-storage/the-bio.md"],
    ["blk-mq", "../12-block-layer-and-storage/blk-mq.md"],
    ["I/O schedulers", "../12-block-layer-and-storage/io-schedulers.md"],
    ["Buffered I/O, `O_DIRECT`, and alignment", "../12-block-layer-and-storage/buffered-direct-and-alignment.md"],
    ["`io_uring`", "../12-block-layer-and-storage/io-uring.md"],
    ["Diagnosing I/O problems", "../12-block-layer-and-storage/diagnosing-io-problems.md"],
  ]} />

The networking path assumes three pages outside it: [softirqs](../10-interrupts-time-and-deferred-work/softirqs.md),
[the four VFS objects](../11-vfs-and-filesystems/the-four-objects.md) (a socket is a file), and the
[sockets API](../../computer-science/computer-networks/sockets-and-the-application-boundary.md) from
Computer Networks.

<LearningPath
  title="I want to understand networking"
  steps={[
    ["The network stack, mapped", "../13-networking-stack/the-network-stack-map.md"],
    ["`sk_buff`: the packet container", "../13-networking-stack/sk-buff.md"],
    ["Sockets in the kernel", "../13-networking-stack/sockets-in-the-kernel.md"],
    ["The receive path", "../13-networking-stack/the-receive-path.md"],
    ["The transmit path", "../13-networking-stack/the-transmit-path.md"],
    ["TCP in the kernel", "../13-networking-stack/tcp-in-the-kernel.md"],
    ["netfilter and nftables", "../13-networking-stack/netfilter-and-nftables.md"],
    ["Connection tracking and NAT", "../13-networking-stack/connection-tracking-and-nat.md"],
    ["Routing and neighbours", "../13-networking-stack/routing-and-neighbours.md"],
    ["Network namespaces and virtual devices", "../13-networking-stack/network-namespaces-and-virtual-devices.md"],
    ["Diagnosing network problems", "../13-networking-stack/diagnosing-network-problems.md"],
  ]} />

## Where the rest is

Folders 14 through 19 remain specified and not yet scaffolded, covering drivers, containers,
security, observability, eBPF, and contributing.
