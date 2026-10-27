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

Every term below links to the one page that owns and genuinely defines it, so "where did this come from" always has an answer. The list covers folders 00–16 so far and grows as later folders land — a term you expect but can't find here probably belongs to a page that hasn't been written yet.

**`--privileged`** — The runtime flag that grants every capability and also removes seccomp, the LSM profile, device restrictions and read-only `/sys`. [Capabilities and Container Privilege](../15-containers-and-virtualization/capabilities-in-containers.md)

**ABI (application binary interface)** — the binary-level contract a program compiles against; this section uses it specifically for the kernel's promise that it never breaks the *user-space* ABI (syscalls, `/proc`, ELF layout) across releases, even though it makes no such promise internally. [What Linux Actually Is](./what-linux-actually-is.md)

**Accept queue** — the queue of fully established connections waiting for a listening socket's `accept()`; its limit is the `listen()` backlog, silently capped by `net.core.somaxconn`. [Sockets in the Kernel](../13-networking-stack/sockets-in-the-kernel.md)

**ACPI `_HID`** — An ACPI device's hardware ID, the ACPI counterpart of a `compatible` string, matched against a driver's `acpi_match_table`. [Platform Devices, Device Tree, and ACPI](../14-device-drivers-and-hardware/platform-devices-and-description.md)

**Acquire and release** — the kernel's spelling of publish/subscribe ordering: `smp_store_release()` guarantees a store is visible only after every earlier access in program order, `smp_load_acquire()` guarantees a load happens before every later access; reach for this pair before a bare `smp_mb()` because it states exactly the ordering needed rather than a full fence in both directions. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**Address space (`address_space`)** — the per-inode structure that owns a cacheable file's folios: an `i_pages` XArray indexed by page-offset-within-file, plus the owning inode, the filesystem's `a_ops` callback table, folio count, and `gfp_mask`. [The Page Cache](../08-memory-management/the-page-cache.md)

**Allocation group** — one of the independent regions an XFS filesystem is split into, each with its own free-space and inode B+ trees, so many threads can allocate at once without contending on one structure. [XFS and Btrfs](../11-vfs-and-filesystems/xfs-and-btrfs.md)

**Ambient capability set** — Capabilities kept across `execve()` of ordinary, non-privileged programs; each must also be permitted and inheritable. [Capabilities](../16-security/capabilities.md)

**AppArmor profile** — A per-program list of allowed paths, capabilities and network access, attached to the program by its executable path. [AppArmor](../16-security/apparmor.md)

**ARP (Address Resolution Protocol)** — the IPv4 protocol that maps an IP address on the local link to its MAC address by broadcasting a request and caching the reply. [ARP, ICMP, and Neighbour Discovery](../../computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md)

**Attack surface** — The set of interfaces an attacker can reach and use; for an isolation boundary, how much code sits behind it. [Virtualization and Isolation](../../computer-science/operating-systems/virtualization-and-isolation.md)

**Audit rule** — A kernel filter (`auditctl -a`, `-w`) selecting which syscalls or file accesses produce audit records. [Auditing and Security Observability](../16-security/auditing-and-security-observability.md)

**`auditd`** — The user-space daemon that receives audit records from the kernel over netlink and writes them to `/var/log/audit/audit.log`. [Auditing and Security Observability](../16-security/auditing-and-security-observability.md)

**Autogroup** — a per-session grouping (on by default via `kernel.sched_autogroup_enabled`) that nests every task's fair-class scheduling entity inside its session's group rather than competing directly against every other task system-wide; the group, not the individual task, competes for CPU share, which is why renicing one process inside a crowded autogroup can appear to do nothing against unrelated work in another session. [Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**Autosuspend** — Runtime PM's delay before suspending an idle device, so a burst of accesses doesn't cause a suspend–resume cycle each time. [Power Management](../14-device-drivers-and-hardware/power-management.md)

**Autotuning (TCP buffers)** — the kernel growing a connection's receive and send buffers as the path proves it needs them, up to the `tcp_rmem`/`tcp_wmem` maximum; setting `SO_RCVBUF` switches it off. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**AVC (access vector cache)** — SELinux's cache of policy decisions; also the name of the audit record logging a denial. [SELinux](../16-security/selinux.md)

**BAR (base address register)** — A configuration-space register through which a device declares an MMIO or I/O region and the OS assigns its address. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**Barrier** — two independent reorderers exist and a fix for one is not a fix for the other: `barrier()` is a pure compiler directive with no emitted instruction, while `smp_mb()`/`smp_rmb()`/`smp_wmb()` constrain the CPU's own reordering and imply a compiler barrier too; on `CONFIG_SMP=n` every `smp_`-prefixed barrier degrades to a plain compiler barrier. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**BBR** — a model-based TCP congestion control that estimates bottleneck bandwidth and minimum RTT and paces at that rate instead of reacting to loss; mainline v6.18 ships version 1. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**BDF (bus:device.function)** — The address of a PCI function, such as `00:03.0`. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**Bind and unbind** — Attaching a driver to a device (a successful `probe`) and detaching it (`remove`); also writable by hand through `/sys/bus/*/drivers/*/bind` and `unbind`. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**Bind mount** — a second mount of an existing directory tree at another place, with its own mount flags, so the same data can appear read-only in one location and writable in another. [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md)

**`binfmt`** — the registered-handler chain (`struct linux_binfmt`, e.g. `binfmt_elf`, `binfmt_script`, `binfmt_misc`) that `execve()` asks, in turn, "is this file yours?" — the mechanism by which the kernel supports ELF, `#!` scripts, and user-registered formats without special-casing any of them. [`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**`bio`** — the block layer's unit of work: a direction, a starting sector, a list of memory segments holding the data, and a function to call when it is done. [The `bio`](../12-block-layer-and-storage/the-bio.md)

**`bio_vec`** — one memory segment of a `bio` — a page, an offset, and a length — so a single I/O can gather data from scattered pages without copying it together. [The `bio`](../12-block-layer-and-storage/the-bio.md)

**Bitmap** — a fixed-size set of small integers (CPU masks, IRQ masks, feature flags) stored as `unsigned long` words via `DECLARE_BITMAP`, manipulated with `set_bit()`/`clear_bit()`/`test_bit()`; the atomic variants like `test_and_set_bit()` are the default whenever more than one context might touch the same bitmap concurrently. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**blk-mq (multi-queue block I/O)** — the block layer's design since the single-queue path was removed: per-CPU software queues feed per-device hardware queues, so CPUs submitting I/O don't contend on one lock. [blk-mq: Multi-Queue Block I/O](../12-block-layer-and-storage/blk-mq.md)

**Block device** — a device the kernel can address as an array of fixed-size sectors in any order, with a logical block size every transfer is a multiple of, buffered through the page cache. [Block Devices and `gendisk`](../12-block-layer-and-storage/block-devices-and-gendisk.md)

**Block group** — one of the fixed-size regions — 32,768 blocks at a 4 KiB block size — an ext4 volume is divided into, each with its own bitmaps and inode table, so related data can be kept close together. [ext4](../11-vfs-and-filesystems/ext4.md)

**Boot loader** — the software that runs after firmware and before the kernel, whose entire job is four things: find a kernel, find an initramfs, build a command line, and hand over control. [Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**Boot variable** — an NVRAM entry (`Boot0000`, `Boot0001`, …) plus a `BootOrder` list that tells UEFI firmware which `.efi` file to run and in what order; this state lives in firmware, not on disk. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Bounding set** — The limit on what `execve()` can add to the permitted set; it can only shrink, and container runtimes cut it. [Capabilities](../16-security/capabilities.md)

**BPF-LSM** — eBPF programs attached to LSM hooks, which can observe the hook's arguments or deny the operation. [Auditing and Security Observability](../16-security/auditing-and-security-observability.md)

**BQL (Byte Queue Limits)** — a dynamic limit on how many bytes may sit in a driver's transmit ring — enough to keep the NIC busy, no more — moving queueing up into the qdisc; the driver must implement it. [The Transmit Path](../13-networking-stack/the-transmit-path.md)

**Bridge** — a software Ethernet switch in the kernel that learns which MAC address is behind each port (its FDB) and forwards frames only where they need to go. [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)

**Buddy allocator** — the page allocator's free-list structure within a zone, one list per order of 2ⁿ contiguous pages; splitting an order-*k*+1 block on allocation and coalescing two buddies (found by `buddy_pfn = pfn ^ (1 << order)`, no search needed) back together on free are its two governing operations. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Bundle** — A directory holding a `config.json` and a root filesystem: the unit an OCI runtime is given to run. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**Bus mastering** — Permission for a PCI device to start its own memory transactions (DMA); a driver turns it on with `pci_set_master()`. [PCI and PCIe Drivers](../14-device-drivers-and-hardware/pci-and-pcie-drivers.md)

**Bus type (`struct bus_type`)** — The kernel object for one kind of bus (PCI, USB, platform): it owns the list of devices and drivers on that bus and the `match()` that pairs them. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**`bzImage`** — the actual bootable kernel file: real-mode setup code, a setup header, and a compressed payload that self-extracts on first run. "bz" stands for "big zImage," unrelated to the bzip2 algorithm. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Canonical address** — an x86-64 virtual address whose unimplemented high bits are a sign-extension of the top implemented bit (47, or 56 with 5-level paging); a non-canonical address is rejected by the CPU with `#GP` before translation even starts, which is why some bad pointers oops differently than others. [The Virtual Address Space](../08-memory-management/the-virtual-address-space.md)

**Capability sets** — A thread's five capability sets: permitted, effective, inheritable, bounding and ambient, each a 64-bit mask in `struct cred`. [Capabilities](../16-security/capabilities.md)

**CBS (Constant Bandwidth Server)** — the live enforcement mechanism behind `SCHED_DEADLINE`: it tracks each deadline task's runtime budget as it consumes it and throttles the task the moment it overruns its declared runtime within the current period, containing a runaway deadline task with the same machinery that guarantees well-behaved ones their share. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**`cdev`** — The kernel object connecting a range of character-device numbers to a `file_operations` table. [Character Devices](../14-device-drivers-and-hardware/character-devices.md)

**CFS (Completely Fair Scheduler)** — the fair-class algorithm that ran Linux from 2.6.23 (2007) until EEVDF began replacing it in 6.6; at the pinned v6.18 it is not the running scheduler, but its vocabulary (vruntime, the red-black tree, nice-to-weight) is preserved as the historical model EEVDF is a direct response to. [CFS and Virtual Runtime](../07-scheduling/cfs-and-vruntime.md)

**CGNAT (carrier-grade NAT)** — NAT performed by an ISP across many customers at once, so a subscriber's "public" address is itself behind another layer of translation. [NAT and Connection Tracking](../../computer-science/computer-networks/nat-and-connection-tracking.md)

**cgroup** — a directory in the cgroupfs virtual filesystem whose auto-populated files (`cpu.weight`, `memory.max`, `io.max`, `pids.max`, …) express resource limits; it answers "what can this process *use*," a question orthogonal to namespaces. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**cgroup delegation** — Handing ownership of a cgroup subtree to an unprivileged user or a container, which may then manage it without affecting anything outside. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**`cgroup.subtree_control`** — The file that enables controllers for a cgroup's children; a controller must be enabled in the parent before a child's interface files appear. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**Clock event device** — a programmable timer the kernel arms for a specific future moment and that then raises an interrupt at approximately that time, driving both the periodic tick and every one-shot timer; unlike a clocksource, it interrupts rather than merely being read. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**Clocksource** — a free-running hardware counter that only ever increases and is never itself an interrupt source; the kernel reads it and converts the reading to nanoseconds via a fixed-point `mult`/`shift` multiply, choosing among registered sources (TSC, HPET, ACPI PM timer, arm64's architected timer) by rating. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**`clone()` flags** — the single set of bits (`CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, and more) that decide, one `task_struct` pointer at a time, whether a new task shares or copies its parent's address space, filesystem context, file table, and signal handlers; `fork()`, `vfork()`, and `pthread_create()` are just three different flag words passed to the same `clone()`. [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**clsact** — a pseudo-qdisc providing ingress and egress attach points for tc filters and eBPF programs, without queueing anything. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**CNI (Container Network Interface)** — The plugin protocol for container networking: a runtime executes plugin binaries with a namespace path and JSON config, and they set up its interfaces. [Container Networking](../15-containers-and-virtualization/container-networking.md)

**CoDel** — active queue management that drops based on how long packets have *waited* (sojourn time) rather than how many are queued, removing standing queues while leaving bursts alone. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**Coherent DMA mapping** — A long-lived buffer from `dma_alloc_coherent()` that CPU and device can both access at any time without explicit syncs. [The DMA API](../14-device-drivers-and-hardware/the-dma-api.md)

**Coldplug** — Replaying uevents for devices that appeared before udev started (`udevadm trigger`), so they get the same treatment as hotplugged ones. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**Compaction** — active defragmentation: migrating movable pages out of a region to consolidate scattered free order-0 pages into the higher-order contiguous blocks a THP or other high-order allocation needs, the mirror image of what the buddy allocator does on free. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Compat syscall** — a syscall reached through a second, architecture-specific syscall table (e.g. the 32-bit `syscall_32.tbl` a 64-bit kernel also carries) plus `compat_` translation functions and structs, needed because pointers, `long`s, and struct layouts differ in width between a 32-bit caller and the kernel's native 64-bit types. [ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md)

**`compatible`** — The device-tree property naming what a node is, most specific first; a driver's `of_match_table` lists the strings it handles. [Platform Devices, Device Tree, and ACPI](../14-device-drivers-and-hardware/platform-devices-and-description.md)

**Complain mode** — AppArmor's mode in which a profile's denials are logged but not enforced, used while writing the profile. [AppArmor](../16-security/apparmor.md)

**Compound page** — the pre-folio name for a multi-page allocation from the buddy allocator: an order-*n* block with a **head** page carrying the real metadata and every **tail** page pointing back at it via `compound_head`, an arrangement that left every function taking a `struct page *` responsible for checking which kind it had. [Folios and Compound Pages](../08-memory-management/folios-and-compound-pages.md)

**configfs** — a pseudo-filesystem where user space *creates* kernel objects by making directories and writing attributes, the inverse of sysfs, which only shows objects the kernel already made. [procfs, sysfs, debugfs, configfs](../11-vfs-and-filesystems/procfs-sysfs-debugfs-configfs.md)

**Configuration space** — A PCI function's standard register block (256 bytes, 4 KiB on PCIe) holding its IDs, BARs and capability lists. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**Congestion control module** — a `tcp_congestion_ops` implementation that decides how fast a TCP connection sends; CUBIC is the default, BBR an alternative, selectable per socket with `TCP_CONGESTION`. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**Conntrack (connection tracking)** — the kernel's table of every flow it has seen, each an `nf_conn` with original and reply tuples, a protocol state, and a timeout; stateful rules and NAT both depend on it. [Connection Tracking and NAT](../13-networking-stack/connection-tracking-and-nat.md)

**Conntrack helper** — a module that parses a protocol's payload (FTP, SIP) to find the connections it announces and creates expectations for them; since Linux 6.0 helpers must be assigned explicitly with a `ct helper` rule. [Connection Tracking and NAT](../13-networking-stack/connection-tracking-and-nat.md)

**Container** — An ordinary process started in its own namespaces, under a cgroup, with reduced capabilities and a seccomp filter; there is no container object in the kernel. [What a Container Actually Is](../15-containers-and-virtualization/what-a-container-actually-is.md)

**`container_of`** — a macro that recovers a pointer to a containing struct from a pointer to one of its embedded fields, by subtracting that field's compile-time offset and casting the result to the containing type. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**containerd** — The daemon below Docker and Kubernetes that pulls and stores images, prepares bundles and runs containers through shims. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**Context switch** — the three-stage handoff between tasks: `__schedule` picks the next task (cheap bookkeeping), `context_switch` swaps the address space only if it changed, and `switch_to` swaps register state unconditionally; the nameable direct cost is small, and the real expense is the unnamed indirect cost paid afterward by the incoming task's cold caches and TLB. [The Context Switch](../07-scheduling/the-context-switch.md)

**Copy-on-write** — the mechanism that makes `fork()` cheap: both parent and child page tables point at the same physical pages, marked read-only, and the kernel copies a page only at the moment either side actually writes to it. [`fork()` and Copy-on-Write](../06-processes-and-threads/fork-and-copy-on-write.md)

**Copy-up** — overlayfs copying a file from a read-only lower layer into the writable upper layer the first time it is modified, so the change never touches the lower layer. [overlayfs](../11-vfs-and-filesystems/overlayfs.md)

**`cpu.max`** — the cgroup v2 hard CPU cap: a quota of microseconds a group may consume out of every period, written as `"$MAX $PERIOD"` (default `"max 100000"`, i.e. no cap). Hitting the quota does not slow the group down — it stops it dead for the rest of the period, turning a CPU limit into a latency problem. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**`cpu.weight`** — the cgroup v2 proportional CPU control (replacing v1's `cpu.shares`), a value in [1, 10000], default 100; it only changes the outcome when the CPU is contended — a low-weight group still gets the whole CPU to itself if nothing else wants it, because the mechanism is work-conserving. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**Crash consistency** — the property that a storage system's on-disk structures are valid after a crash at any instant, achieved by ordering writes, journaling, or copy-on-write. [Crash Consistency and Journaling](../../computer-science/storage/crash-consistency-and-journaling.md)

**Credentials (`struct cred`)** — the separately allocated, refcounted, and immutable-once-published object holding a task's user/group IDs and capability sets; `task_struct` holds two pointers to it (`cred`, `real_cred`) rather than the fields themselves, and changing credentials means installing a whole new object, never editing one in place. [Credentials and Identity](../06-processes-and-threads/credentials-and-identity.md)

**ctstate** — the per-packet connection state rules match on — `new`, `established`, `related`, `invalid`, `untracked` — describing the packet's relationship to its conntrack entry. [Connection Tracking and NAT](../13-networking-stack/connection-tracking-and-nat.md)

**`current`** — the currently running task on a given CPU, resolved via a per-CPU variable populated by `current_task`, not (on x86-64) by masking the stack pointer as older documentation describes. [`task_struct`: The Anatomy of a Task](../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md)

**D state** — the `ps` letter for `TASK_UNINTERRUPTIBLE`; because signal delivery only happens on the return to user space and a `D`-state task never reaches that checkpoint, not even `SIGKILL` can act on it until the underlying wait completes. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**`data=ordered`** — ext4's default journaling mode: only metadata is journaled, but a file's data blocks are forced to disk before the metadata transaction that references them commits, so a crash never exposes stale blocks. [Journaling and Crash Consistency](../11-vfs-and-filesystems/journaling-and-crash-consistency.md)

**dcache (dentry cache)** — the hash table of dentries keyed on (parent dentry, name) that lets path lookup resolve most components without asking the filesystem at all. [Path Lookup and the Dentry Cache](../11-vfs-and-filesystems/path-lookup-and-the-dcache.md)

**debugfs** — a pseudo-filesystem for kernel developers' ad-hoc debugging files, with no stability promise at all — unlike sysfs, whose files are ABI documented under `Documentation/ABI`. [procfs, sysfs, debugfs, configfs](../11-vfs-and-filesystems/procfs-sysfs-debugfs-configfs.md)

**`defconfig`** — the `make defconfig` target that produces a sane, complete `.config` close to what a real distribution ships; the usual starting point before hand-tuning debug options. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Deferred probe** — A `probe()` returning `-EPROBE_DEFER` because something it needs (a clock, a regulator, a GPIO) isn't ready yet; the core retries it later instead of failing it. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**Delayed allocation** — ext4 choosing physical blocks for written data only at writeback time rather than at `write()`, so a whole batch of dirty pages gets one contiguous allocation. [ext4](../11-vfs-and-filesystems/ext4.md)

**Demand paging** — the policy that `mmap()` creates a VMA and maps no physical pages at all; only a fault — a first read (the zero page) or first write (a fresh zeroed frame) — actually costs physical memory, so address space is issued freely on the promise most of it is never touched. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Dentry (`struct dentry`)** — the VFS object binding one name in one directory to an inode; dentries are what path lookup walks and what the dcache caches. [Superblock, Inode, Dentry, File](../11-vfs-and-filesystems/the-four-objects.md)

**Device class** — A grouping of devices by what they do rather than how they're connected (`net`, `block`, `input`), visible as `/sys/class/<name>`. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**Device ID table** — A driver's list of the devices it handles (`pci_device_id`, `of_device_id`, …), used by the bus `match()` and exported for module autoloading. [PCI and PCIe Drivers](../14-device-drivers-and-hardware/pci-and-pcie-drivers.md)

**Device mapper** — the kernel framework that builds a virtual block device from others by loading a table mapping sector ranges to targets — linear, crypt, thin, snapshot, and more. [Device Mapper and LVM](../12-block-layer-and-storage/device-mapper-and-lvm.md)

**Device tree** — A data structure the bootloader hands the kernel that describes non-discoverable hardware: nodes, addresses, interrupts and `compatible` strings. [Platform Devices, Device Tree, and ACPI](../14-device-drivers-and-hardware/platform-devices-and-description.md)

**devres (`devm_*`)** — Device-managed resources: allocations and mappings made with `devm_*` helpers are released automatically when the driver unbinds, so error paths and `remove()` need no matching frees. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**Direct map** — the kernel address-space region holding a permanent virtual address for every physical page of installed RAM, at a fixed offset from its physical address; this linear-by-construction mapping is what makes `virt_to_phys()`/`phys_to_virt()` plain arithmetic instead of a page-table walk. [The Virtual Address Space](../08-memory-management/the-virtual-address-space.md)

**Direct reclaim** — reclaim run synchronously, on the allocating task's own time, triggered when a zone crosses its **min** watermark; unlike `kswapd`'s background work, this is a latency event with an unbounded tail because the allocating thread is now doing reclaim instead of its own work. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**Dirty page** — a page-cache page holding data that has been modified in RAM but not yet written back to its backing device. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**Distribution** — a specific packaging of the kernel plus a userland (C library, init system, package manager, patch set, and kernel configuration), with its own name, release cadence, and support policy. [What Linux Actually Is](./what-linux-actually-is.md)

**dm-crypt** — the device-mapper target that encrypts and decrypts every `bio` passing through it; LUKS is the on-disk format usually layered on top. [Device Mapper and LVM](../12-block-layer-and-storage/device-mapper-and-lvm.md)

**DMA mask** — The range of addresses a device can generate, declared with `dma_set_mask_and_coherent()`, so the DMA API never gives it a buffer it can't reach. [The DMA API](../14-device-drivers-and-hardware/the-dma-api.md)

**`dma_addr_t`** — An address as the device sees it, which may differ from the CPU's physical address because of an IOMMU or bus offsets; what the DMA API hands a driver to program into hardware. [The DMA API](../14-device-drivers-and-hardware/the-dma-api.md)

**`Documentation/ABI`** — The kernel tree's directory documenting user-visible sysfs and other interfaces, sorted into `stable`, `testing`, `obsolete` and `removed`. [Talking to User Space](../14-device-drivers-and-hardware/talking-to-user-space.md)

**Doorbell** — a device register the driver writes to say "new commands are in the submission queue"; NVMe has one per queue. [NVMe in the Kernel](../12-block-layer-and-storage/nvme-in-the-kernel.md)

**Double fetch** — Reading the same user-space value twice, once to check and once to use, so another thread can change it in between. [Vulnerability Classes in the Kernel](../16-security/vulnerability-classes.md)

**Drop reason** — the `enum skb_drop_reason` value passed to `kfree_skb_reason()` wherever the stack drops a packet, reported by the `skb:kfree_skb` tracepoint so every drop names its cause. [The Receive Path](../13-networking-stack/the-receive-path.md)

**Dynamic debug** — Turning individual `pr_debug()`/`dev_dbg()` call sites on and off at run time through `/proc/dynamic_debug/control`. [Debugging Drivers](../14-device-drivers-and-hardware/debugging-drivers.md)

**Dynticks** (`CONFIG_NO_HZ_IDLE`) — stops the periodic tick on a CPU that has gone idle with nothing due soon, reprogramming the clock event device as a one-shot event for the actual next expiry instead of polling at a fixed rate; `nohz_full` extends the same idea to a busy CPU with exactly one runnable task. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**ECAM** — Enhanced Configuration Access Mechanism: PCIe configuration space mapped into physical memory, one 4 KiB window per function. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**EEVDF (Earliest Eligible Virtual Deadline First)** — the fair-class scheduler actually running at v6.18, replacing CFS beginning in kernel 6.6 and becoming the default in 6.12. It separates the two questions CFS's single `nice` knob conflated — how much CPU a task deserves (still weight, from nice) and how promptly it should run (a per-task request size) — selecting among eligible tasks by earliest virtual deadline instead of comparing vruntime directly. [EEVDF](../07-scheduling/eevdf.md)

**`EFAULT`** — the negative-errno value a copy routine's caller returns when `copy_from_user`/`copy_to_user` reports a nonzero, uncopied remainder, produced when the exception table's fixup redirects execution away from a user-memory access that faulted rather than letting it become a kernel oops. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**Eligibility** — under EEVDF, a task is eligible exactly when its lag is non-negative (its vruntime is at or behind the runqueue's average virtual time `V`); only eligible tasks are candidates for selection at all, regardless of how early their virtual deadline would otherwise be. [EEVDF](../07-scheduling/eevdf.md)

**EPT and NPT** — Intel's and AMD's second-level page tables, translating guest physical addresses to host physical addresses in hardware. [Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md)

**`ERESTARTSYS`** — an internal-only return value a blocking syscall hands back when a signal interrupts it, never seen by user space: the kernel either rewinds `pt_regs->ip` to re-execute the `SYSCALL` instruction (if the handler was installed with `SA_RESTART`) or converts it to the `-EINTR` user space actually observes. [Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**`ERR_PTR`** — a function that encodes a negative `errno` value as a pointer, exploiting the fact that the top few thousand bytes of kernel address space are never a valid allocation, so the encoded value is unambiguously distinguishable from a real pointer. [Error Handling](../04-kernel-architecture-and-idioms/error-handling-idioms.md)

**`errseq_t`** — the error-sequence counter on each `address_space` that lets every file descriptor learn about a writeback error exactly once, the fix that came out of the 2018 `fsync` error-reporting work. [Journaling and Crash Consistency](../11-vfs-and-filesystems/journaling-and-crash-consistency.md)

**ESP (EFI System Partition)** — a FAT32 partition that UEFI firmware can read directly, holding `.efi` boot loader files; it replaces the MBR's chainloading trick that legacy BIOS relies on. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**EVM (Extended Verification Module)** — The subsystem protecting security xattrs and inode metadata with an HMAC or signature in `security.evm`, so IMA's stored values can be trusted. [Integrity: IMA, EVM, and Module Signing](../16-security/integrity-and-signing.md)

**Exception table** — a table of `(instruction, fixup)` offset pairs (`struct exception_table_entry`) that lets a page fault on a deliberate `copy_from_user`/`copy_to_user` access be redirected to fixup code returning an error, instead of being treated as the kernel bug an unprotected fault normally is. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**`EXPORT_SYMBOL_GPL`** — the macro placed after a kernel function's definition that makes it callable from a module whose declared license the kernel recognizes as GPL-compatible; the plain `EXPORT_SYMBOL` allows any module regardless of license. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**Extent** — a run of contiguous physical blocks described by one record (start, length), replacing a list of per-block pointers; ext4, XFS, and Btrfs all map file data with extents. [ext4](../11-vfs-and-filesystems/ext4.md)

**FIB (forwarding information base)** — a routing table as the kernel stores it — an LC-trie searched by longest-prefix match; Linux has had no routing cache in front of it since 3.6. [Routing and Neighbours](../13-networking-stack/routing-and-neighbours.md)

**File capability** — Capabilities attached to an executable in its `security.capability` xattr, granted at `execve()`; the fine-grained replacement for setuid-root. [Capabilities](../16-security/capabilities.md)

**File descriptor table (`files_struct`)** — the per-process table behind `current->files` that maps each small integer fd to a `struct file`; threads share one, and `fork()` copies it. [`open`, `read`, `write` in the Kernel](../11-vfs-and-filesystems/open-read-write-in-the-kernel.md)

**`file_system_type`** — the structure a filesystem registers with `register_filesystem()`: its name, and the function that builds a superblock when it is mounted. [Lab: A Filesystem in 200 Lines](../11-vfs-and-filesystems/lab-a-minimal-filesystem.md)

**First touch** — the rule that a virtual address owns no physical memory until something faults it in; on a NUMA machine the same fault also decides node placement, since the allocator asks the faulting CPU's own node first, which is why a single thread that initializes a shared array pins the whole array to one node. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Folio (`struct folio`)** — a type guaranteed to be a head page (or a trivially-its-own-head order-0 page), overlaying the same `struct page` array memory rather than adding a second structure; the guarantee is enforced by the type system, not by a runtime check every caller used to have to redo. [Folios and Compound Pages](../08-memory-management/folios-and-compound-pages.md)

**`FORTIFY_SOURCE`** — Size-checked versions of string and memory functions, which fail at build time or run time when a copy would overflow a buffer of known size. [Kernel Hardening](../16-security/kernel-hardening.md)

**fq_codel** — a qdisc that gives each flow its own queue and drops or marks packets once their queueing delay stays above 5 ms over a 100 ms interval; systemd's default. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**Freestanding C** — a C implementation with no operating system underneath it to supply a standard library, a `main()` entry point, or a heap; the kernel supplies its own equivalents of everything (`printk`, `kmalloc`, its own boot entry) because it *is* the OS. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**fsuid** — The UID the VFS uses for permission checks; it follows `euid` automatically and exists so a server can act on files as another user. [Credentials in the Kernel](../16-security/credentials-in-the-kernel.md)

**`fsync`** — a call guaranteeing that, on success, a file's data and the metadata needed to find it have been handed to the device with a cache-flush/`FUA` request; it says nothing about the containing directory's own entry, which needs its own `fsync` on the directory file descriptor. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**FUA (Force Unit Access)** — a per-write flag telling the device to put that one write on stable media before completing it, instead of flushing its entire volatile cache; jbd2 uses it for commit records. [Journaling and Crash Consistency](../11-vfs-and-filesystems/journaling-and-crash-consistency.md)

**FUSE (Filesystem in Userspace)** — the kernel interface that forwards VFS operations as requests over `/dev/fuse` to an ordinary process, which implements the filesystem's logic. [FUSE](../11-vfs-and-filesystems/fuse-and-userspace-filesystems.md)

**FUSE passthrough** — a FUSE mode in which the daemon hands the kernel a backing file and reads and writes then go straight to it, skipping the round trip through the daemon for data. [FUSE](../11-vfs-and-filesystems/fuse-and-userspace-filesystems.md)

**fw_devlink** — Links between devices inferred from firmware descriptions (device-tree phandles, ACPI dependencies), used to order probing so suppliers probe before consumers. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**`gendisk`** — the structure describing one whole disk to the block layer — its name, its request queue, its partitions — from which most of `/dev` and `/sys/block` is generated. [Block Devices and `gendisk`](../12-block-layer-and-storage/block-devices-and-gendisk.md)

**GFP flags** — the bits passed to an allocation request that state what the allocator is *permitted* to do on the caller's behalf (sleep, run direct reclaim, issue I/O, call back into a filesystem) — a permission grant, not a performance knob — with `GFP_KERNEL`, `GFP_ATOMIC`, `GFP_NOWAIT`, `GFP_NOFS`, and `GFP_NOIO` each forbidding a different subset for a different calling context. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Grace period** — an interval during which every CPU has passed through at least one quiescent state; once a grace period that started after a writer's update has elapsed, every reader that could have observed the old version is guaranteed to have finished, and only then may the old version be reclaimed. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**GRO (Generic Receive Offload)** — merges several related small segments arriving close together (e.g. TCP segments from the same stream) into one larger `sk_buff` before the packet climbs further up the stack, trading a small merge cost for large savings in per-header processing. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md); in depth: [The Receive Path](../13-networking-stack/the-receive-path.md)

**Hard IRQ context** — the context a hardware interrupt handler runs in, borrowing whatever task happened to be running with no task identity of its own; every prohibition (no sleeping, no mutex, no `GFP_KERNEL`, no `copy_to_user`) follows from that one fact. [Hard IRQ Context and Its Rules](../10-interrupts-time-and-deferred-work/hardirq-context.md)

**Headroom** — space reserved in an `sk_buff`'s buffer in front of the data, so each layer on the transmit path can prepend its header by moving a pointer instead of copying the payload. [`sk_buff`: The Packet Container](../13-networking-stack/sk-buff.md)

**`hlist`** — `hlist_head`/`hlist_node`, `list_head`'s sibling for hash tables: a single-pointer head (rather than `list_head`'s two) keeps millions of empty buckets cheap, with the node side carrying `pprev` — a pointer to the previous node's `next` field — so removal can splice a node out without walking the list. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Hook priority** — the number deciding the order of functions at one netfilter hook: raw (-300), conntrack (-200), DNAT (-100), filter (0), SNAT (100). [netfilter and nftables](../13-networking-stack/netfilter-and-nftables.md)

**hrtimer** — a timer ordered in a red-black tree keyed on absolute expiry time, feeding a programmable clock event device armed for exactly its leftmost (soonest) node; used when a deadline must actually be met, at the cost of O(log n) insertion against the timer wheel's O(1). [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**htb (hierarchical token bucket)** — a classful qdisc giving each class a guaranteed `rate` and a `ceil` up to which it may borrow unused bandwidth from its parent. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**htree** — ext4's hashed B-tree directory index, which turns a lookup in a directory of millions of entries from a linear scan into a few block reads. [ext4](../11-vfs-and-filesystems/ext4.md)

**Huge page** — a page-table walk that stops one or two levels early because a PMD or PUD entry's page-size bit is set, mapping the entire 2 MiB (PMD) or 1 GiB (PUD) region that level's fan-out would otherwise have covered through a whole subtree of tables. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**hugetlbfs** — the explicit, reserved huge-page mechanism: an administrator or application pre-allocates a pool of huge pages (at boot or via `nr_hugepages`) that is taken out of the general page allocator entirely — never reclaimed, never swapped, never silently given back — and applications opt in by name via `MAP_HUGETLB` or a file on a `hugetlbfs` mount. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**`HZ`** — the build-time constant (100, 250, 300, or 1000) setting how many times a second the periodic tick fires on a CPU that has not stopped it; it still governs how often the tick's timer-expiry and accounting jobs run, but no longer determines the scheduler's own fairness granularity. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**`idr`/`ida`** — the kernel's "give me the smallest unused integer, and let me give it back later" allocators; `idr` maps a small integer to a pointer (file descriptors, device minor numbers), while `ida` is the same machinery with no pointer attached, just an ID allocator. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**IMA (Integrity Measurement Architecture)** — The subsystem that hashes files on access under a policy, logs the hashes and extends a TPM PCR, and optionally appraises them against `security.ima`. [Integrity: IMA, EVM, and Module Signing](../16-security/integrity-and-signing.md)

**`__init`** — an annotation placing a function in a discardable code section whose memory is freed once boot completes; calling it later dereferences freed memory. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Initcall** — a function pointer a built-in driver or subsystem registers into a named linker section at build time, which the kernel walks and calls at the appropriate point in boot rather than being invoked by name from `start_kernel()`. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initcall level** — one of nine ordered phases (`early`, `pure`, `core`, `postcore`, `arch`, `subsys`, `fs`, `device`, `late`) that group initcalls; a driver can pick its level, but not an ordering relative to other drivers within it. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initramfs** (build sense) — a gzip-compressed `cpio` archive the kernel unpacks directly into an in-memory `tmpfs` mounted as `/`, before any real block device or filesystem driver is touched; the kernel then executes `/init` from it as PID 1. [A Minimal Root Filesystem](../01-lab-and-toolchain/a-minimal-rootfs.md)

**Inode** — the VFS object for a file itself, independent of any name: its type, permissions, size, timestamps, and how to find its data. A file with two hard links has one inode and two dentries. [Superblock, Inode, Dentry, File](../11-vfs-and-filesystems/the-four-objects.md)

**Intrusive list** — a container design where the link field that makes an object a list member lives inside the object's own struct rather than in a separately allocated node, costing no extra allocation on insert at the price of baking list membership into the object's type. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**I/O scheduler** — an optional blk-mq stage that reorders and merges requests before dispatch — `none`, `mq-deadline`, `bfq`, or `kyber` — chosen per device in `/sys/block/<dev>/queue/scheduler`. [I/O Schedulers](../12-block-layer-and-storage/io-schedulers.md)

**`io.latency`** — A cgroup I/O latency target: when it is missed, siblings with looser targets are throttled until it recovers. [cgroup Controllers in Practice](../15-containers-and-virtualization/cgroup-controllers-in-practice.md)

**`io_uring`** — an asynchronous I/O interface built on two rings shared between the application and the kernel — submissions in, completions out — so many operations cost one syscall, or none. [`io_uring`](../12-block-layer-and-storage/io-uring.md)

**ioctl number** — The 32-bit command passed to `ioctl()`, built with `_IO`/`_IOR`/`_IOW`/`_IOWR` from a type, a number, a direction and an argument size. [Character Devices](../14-device-drivers-and-hardware/character-devices.md)

**`__iomem`** — A sparse annotation marking a pointer as device memory, so only the MMIO accessors may dereference it. [MMIO, ioremap, and Accessors](../14-device-drivers-and-hardware/mmio-and-port-io.md)

**IOMMU** — The unit translating device-generated addresses through per-device page tables, so a device can reach only the memory mapped for it. [DMA and the IOMMU](../../computer-science/buses-and-io/dma-and-iommu.md)

**`ioremap`** — Maps a physical MMIO range into kernel virtual address space with device-appropriate (uncached) attributes and returns an `__iomem` pointer. [MMIO, ioremap, and Accessors](../14-device-drivers-and-hardware/mmio-and-port-io.md)

**IOTLB** — The IOMMU's cache of address translations, which must be invalidated when a mapping is removed. [DMA and the IOMMU](../../computer-science/buses-and-io/dma-and-iommu.md)

**IOVA** — An I/O virtual address: a device-side address an IOMMU translates to a physical one. [DMA and the IOMMU](../../computer-science/buses-and-io/dma-and-iommu.md)

**`iowait`** — CPU time spent idle while some task on that CPU waits for I/O — a property of idle time, not a measure of how busy or slow a device is. [Diagnosing I/O Problems](../12-block-layer-and-storage/diagnosing-io-problems.md)

**`iptables-nft`** — the iptables command implemented on nftables: it accepts iptables syntax and creates nftables objects, unlike `iptables-legacy`, whose rules live in the older `x_tables` code. [netfilter and nftables](../13-networking-stack/netfilter-and-nftables.md)

**IRQ affinity** — the CPU (or set of CPUs) an interrupt is permitted (`smp_affinity`) and actually delivered to (`effective_affinity`); keeping an interrupt, the softirq it raises, and the task consuming the data on the same CPU avoids cross-CPU cache traffic on every occurrence. [Interrupt Affinity](../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md)

**`irq_chip`** — the vtable (`irq_mask`, `irq_unmask`, `irq_ack`, `irq_eoi`, `irq_set_affinity`) that makes an I/O APIC and a GIC interchangeable to every layer of generic IRQ code above it. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**`irq_desc`** — one struct per Linux IRQ number, tying together the chip, the flow handler, the registered-handler action chain, per-CPU statistics, and the lock serializing all of it. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**irq domain** — the object that maps a controller-local hardware number (`hwirq`) to a Linux IRQ number, needed because nested controllers each describe an interrupt only in their own local numbering; the number in `/proc/interrupts` is allocated at probe time through this mapping, not fixed by the hardware. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**IRQ number versus vector** — two different numbers for the same event: the hardware vector is the IDT index the interrupt controller told the CPU to use, while the Linux IRQ number is the software identifier assigned by an irq domain that `/proc/interrupts`, `request_irq()`, and every driver actually deal in. [How an Interrupt Reaches the Kernel](../10-interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel.md)

**`IRQ_NONE`** — The return value telling the IRQ core "this interrupt wasn't from my device"; essential on shared lines, and counted to detect stuck interrupts. [Interrupts in a Driver](../14-device-drivers-and-hardware/interrupts-in-drivers.md)

**`IRQF_ONESHOT`** — the `request_threaded_irq()` flag that keeps a level-triggered line masked until the thread function itself finishes, not just until the primary handler returns; omitting it on a threaded handler for a level-triggered line produces an interrupt storm. [Threaded IRQs](../10-interrupts-time-and-deferred-work/threaded-irqs.md)

**`irqsave`** — the `spin_lock_irqsave()`/`spin_unlock_irqrestore()` pair, which saves the CPU's current interrupt-enabled state and restores exactly that on unlock rather than assuming interrupts were on; the safe default whenever a caller can't prove the prior interrupt state, since an unconditional `spin_lock_irq()` would wrongly re-enable interrupts that were already off. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**jbd2** — the journaling block device layer ext4 uses: a reusable kernel subsystem that groups metadata changes into transactions and commits them to the journal before they are written in place. [Journaling and Crash Consistency](../11-vfs-and-filesystems/journaling-and-crash-consistency.md)

**`jiffies`** — the global counter the periodic tick increments, wrapping as an `unsigned long`; kernel code compares two values with `time_after()`/`time_before()` rather than `<`/`>` specifically because a direct comparison breaks at the wraparound. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**Journal** — systemd's structured log store, where each entry is a set of key-value fields rather than a text line, letting it be filtered by unit, boot, or priority as a query; whether a previous boot's log survives depends on the `Storage=` setting. [systemd in Practice, and Debugging a Broken Boot](../03-boot-and-init/systemd-in-practice-and-boot-debugging.md)

**KASAN** — the Kernel Address Sanitizer, which instruments every memory access to catch use-after-free and out-of-bounds reads/writes at the exact faulting instruction, by poisoning freed and redzone memory and checking accesses against it. [What Goes Wrong in Kernel C](../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md)

**KASLR** — kernel address space layout randomisation; the decompressor picks a randomised physical load address at every boot, and relocation logic in `extract_kernel()` plus fixups in the kernel's own `startup_64` make a kernel built for one address run correctly wherever it lands. Booting with `nokaslr` disables this, loading the kernel at its link-time address instead — which is also why a GDB session's symbol table only matches a running kernel with KASLR off. [Kernel Hardening](../16-security/kernel-hardening.md)

**Kconfig symbol** — a named configuration option declared by a `config` entry in a `Kconfig` file, with a type, dependency rules, a default, and help text, that governs whether a piece of code is compiled into the kernel at all. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**KCSAN** — the Kernel Concurrency Sanitizer, a sampling-based data-race detector that instruments ordinary loads and stores and reports a concurrent, unsynchronized access to the same memory where at least one side is a write, naming both racing accesses. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Kernel** — the single upstream Linux project: one source tree, one `git` history, one maintainer chain, releasing on a roughly nine-week cadence — distinct from any distribution's userland or packaging around it. [What Linux Actually Is](./what-linux-actually-is.md)

**Kernel command line** — the text handed to the kernel at the moment of handoff (via the setup header's `cmd_line_ptr`), the only channel for changing kernel behavior before any user space exists. [The Kernel Command Line](../03-boot-and-init/the-kernel-command-line.md)

**Kernel thread** — a schedulable kernel-code entity with no user process to be charged to (visible via `ps` in square brackets, e.g. `[kworker/0:1]`), forked from `kthreadd`, distinct from kernel code that runs inside a process's own context. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**kernfs** — the generic in-memory filesystem framework sysfs (and cgroupfs) are built on, generating directories and files from kernel objects. [procfs, sysfs, debugfs, configfs](../11-vfs-and-filesystems/procfs-sysfs-debugfs-configfs.md)

**Key type** — The `struct key_type` that defines how a key's payload is created, read and destroyed: `user`, `logon`, `keyring`, `asymmetric`, `trusted`, … [Keyrings](../16-security/keyrings.md)

**Keyring** — A key that holds links to other keys; per-thread, per-process, per-session and per-user keyrings form the search path for `request_key()`. [Keyrings](../16-security/keyrings.md)

**`kfifo`** — the kernel's ready-made single-producer/single-consumer lock-free ring buffer; its own header documentation is explicit that it is lockless only in the strict SPSC case, and a second producer or consumer requires an explicit spinlock (`kfifo_in_spinlocked()`/`kfifo_out_spinlocked()`). [Lock-Free Patterns](../09-concurrency-and-locking/lock-free-and-ring-buffers.md)

**`kobject`** — the generic, embeddable unit that participates in the kernel's object graph: a name, a reference count, a parent pointer, and a pointer to its type; never allocated standalone, always embedded inside a larger structure. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**KPTI (kernel page-table isolation)** — Separate page tables for user mode that map almost none of the kernel, defending against Meltdown at the cost of a `CR3` switch per kernel entry. [Kernel Hardening](../16-security/kernel-hardening.md)

**`kref`** — a thin standard wrapper around a `refcount_t` plus the convention of pairing it with a release callback; `kref_put` invokes the release function exactly once, when the count it decrements reaches zero. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**`kset`** — a collection of `kobject`s that is itself a `kobject` (it embeds one), giving a group of objects its own place — and its own directory — in the object graph sysfs renders. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`ksoftirqd`** — a per-CPU kernel thread, one per online CPU, that runs softirq work the interrupt-exit path's budget could not finish; seeing it at the top of `top` means a CPU's deferred-work load exceeds what one pass can absorb, not that the softirq mechanism is broken. [Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**`kswapd`** — a per-node kernel thread woken when a zone drops below its **low** watermark, reclaiming memory in the background while allocations continue to be satisfied from whatever's still available; the healthy counterpart to direct reclaim. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**`ktype` (`kobj_type`)** — the behavior attached to a `kobject` — its release function and its attribute (`show`/`store`) operations — shared by every `kobject` of a given kind. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**KVM** — The kernel's hypervisor: a VM is a process, each vCPU a thread, and the interface is `ioctl`s on file descriptors from `/dev/kvm`. [KVM](../15-containers-and-virtualization/kvm-and-hardware-virtualization.md)

**`kvm_run`** — The page shared between KVM and user space for each vCPU, through which `KVM_RUN` reports why it returned. [KVM](../15-containers-and-virtualization/kvm-and-hardware-virtualization.md)

**Lag** — under EEVDF, the gap between the CPU service a task should have received under ideal weighted-fair sharing and what it actually has: `weight × (V − vruntime)`. Positive lag means the task is owed time and is eligible to run; negative lag means it has run ahead of its share and must wait for `V` to catch up. [EEVDF](../07-scheduling/eevdf.md)

**libfs** — `fs/libfs.c`, the kernel's library of ready-made VFS helpers that let a simple in-memory filesystem be written in a couple of hundred lines. [Lab: A Filesystem in 200 Lines](../11-vfs-and-filesystems/lab-a-minimal-filesystem.md)

**`list_head`** — the kernel's circular, doubly-linked intrusive list node/head type (two pointers, `next` and `prev`), embedded directly as a field inside the objects it links. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**`local_lock`** — a lock type that compiles to nothing but `preempt_disable()`/`preempt_enable()` (or the IRQ-disabling equivalents) on a non-`PREEMPT_RT` kernel, and to a real per-CPU lock under `PREEMPT_RT`, so the same source line means "disable preemption" on one configuration and "take a lock" on the other. [Per-CPU Data](../09-concurrency-and-locking/per-cpu-data.md)

**Lock class** — what `lockdep` actually tracks: not individual lock instances but classes, by default one per initialization call site, so the deadlock-cycle graph is a statement about which *kinds* of lock nest inside which, not which specific instances did. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Lockdep** — a runtime validator that builds a graph of lock acquisition ordering as the kernel actually runs and reports the first sequence that could deadlock, even before that exact sequence has actually occurred. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Lockdown** (`CONFIG_SECURITY_LOCKDOWN_LSM`) — closes the ways an already-signature-verified, running kernel could still be made to execute unsigned code or expose kernel memory; its `integrity` mode forbids modifying the running kernel, and `confidentiality` additionally forbids reading kernel memory or secrets, which is why `nokaslr` and kernel debugging stop working once it's active. [Kernel Hardening](../16-security/kernel-hardening.md)

**LRU (lists)** — the classic reclaim scheme: per-`lruvec` active and inactive lists, split further by anonymous versus file-backed (five `lru_list` types in total), where a page found re-referenced while on the inactive list gets a second chance onto the active list instead of being evicted outright. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**LSM (Linux Security Module)** — A module that registers functions on the kernel's security hooks; it can deny accesses the base checks allowed, never allow ones they denied. [The LSM Framework](../16-security/the-lsm-framework.md)

**LSM hook** — A call (`security_*()`) at a security-relevant point in the kernel that runs every registered module's handler. [The LSM Framework](../16-security/the-lsm-framework.md)

**LSM stacking** — Running several LSMs at once, in the order from `lsm=`; SELinux, AppArmor and Smack are exclusive with each other, the rest stack freely. [The LSM Framework](../16-security/the-lsm-framework.md)

**LTS (long-term support)** — a designation given to a subset of kernel releases for which the community keeps backporting fixes for years after an ordinary release would have been abandoned. [What Linux Actually Is](./what-linux-actually-is.md)

**LVM (Logical Volume Manager)** — the user-space tool set that manages volume groups and logical volumes by loading device-mapper tables; the kernel only ever sees the tables. [Device Mapper and LVM](../12-block-layer-and-storage/device-mapper-and-lvm.md)

**macvlan and ipvlan** — virtual sub-interfaces of a physical NIC that appear on its network directly — with their own MAC addresses (macvlan) or sharing the parent's (ipvlan). [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)

**Major and minor numbers** — The two halves of a device number: the major selects the driver, the minor selects which device of that driver. [Character Devices](../14-device-drivers-and-hardware/character-devices.md)

**Maple tree** — the B-tree-like structure (`mm_mt`) an `mm_struct` uses to index its VMAs at v6.18, replacing the older rbtree-plus-linked-list scheme; it supports RCU-safe, lock-free lookups, and `vma->vm_next` no longer exists as a field. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**Masquerade** — source NAT that uses the outgoing interface's current address as the new source, and forgets its mappings when that address goes away. [Connection Tracking and NAT](../13-networking-stack/connection-tracking-and-nat.md)

**md personality** — the per-RAID-level module (`raid0`, `raid1`, `raid456`, `raid10`) that the `md` driver uses to turn several block devices into one array. [Software RAID (md)](../12-block-layer-and-storage/software-raid.md)

**Measurement versus appraisal** — IMA's two modes: measurement records a file's hash for someone else to check; appraisal compares it locally and denies access on a mismatch. [Integrity: IMA, EVM, and Module Signing](../16-security/integrity-and-signing.md)

**`MemAvailable`** — `/proc/meminfo`'s estimate of memory a new process could actually get without swapping: free memory plus the portion of cache that's cheaply reclaimable; the number to read instead of `MemFree`, which counts none of the reclaimable cache. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**Memory ordering** — a plain, unadorned access gives the compiler license to merge, split, invent, or hoist it, and the CPU separately reorders at run time through its store-buffer and speculation machinery; `READ_ONCE()`/`WRITE_ONCE()` close the compiler half and the `smp_*` barrier family closes the CPU half, and the two must be reasoned about separately. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**`memory.high`** — The cgroup memory throttle threshold: tasks over it are forced into reclaim and slowed, but never OOM-killed for it. [cgroup Controllers in Practice](../15-containers-and-virtualization/cgroup-controllers-in-practice.md)

**`memory.max`** — The cgroup memory hard limit: allocation beyond it triggers reclaim within the cgroup, then the OOM killer inside the cgroup. [cgroup Controllers in Practice](../15-containers-and-virtualization/cgroup-controllers-in-practice.md)

**mempolicy (`struct mempolicy`)** — the kernel structure recording which policy (default, bind, preferred, interleave, or weighted interleave) governs which node(s) a fault may draw a frame from, settable per-task (`set_mempolicy`), per-VMA (`mbind`), and bounded underneath both by a cpuset's node set. [NUMA and Memory Policy](../08-memory-management/numa-and-memory-policy.md)

**MGLRU (multi-generational LRU)** — an alternative reclaim implementation organizing pages into generations aged by scanning page-table accessed bits directly rather than the classic two-list scheme's reference-on-fault/reference-on-scan signal; it is a compile-time option (`CONFIG_LRU_GEN`) with no `default y`, not something every kernel ships active. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**microVM** — A minimal virtual machine (Firecracker, Cloud Hypervisor) with a tiny device model, used to give container-like workloads VM isolation. [Virtualization and Isolation](../../computer-science/operating-systems/virtualization-and-isolation.md)

**Misc device** — A character device registered with `misc_register()`, sharing major 10 and getting a dynamic minor and a `/dev` node with one call. [Character Devices](../14-device-drivers-and-hardware/character-devices.md)

**`mm_struct`** — the one-per-address-space structure every thread of a multi-threaded process shares, carrying the VMA collection, the top-level page-table pointer, and layout fields; its lifetime is split across two reference counts, `mm_users` (userspace/semantic references) and `mm_count` (the allocation itself), specifically so a lazy-TLB kernel thread can hold the struct without keeping the address space alive. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**`mmap_lock`** — the per-`mm` reader-writer semaphore serializing structural changes to the VMA collection (insert/remove/split/merge); at v6.18 per-VMA locking (`CONFIG_PER_VMA_LOCK`, enabled in most configurations since 6.4/6.5) lets the page-fault fast path take a lock on just the faulted VMA instead, falling back to `mmap_lock` only when that path can't proceed. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**Modalias** — A string describing a device in the form its bus's ID tables use; udev hands it to `modprobe`, which loads whichever module's aliases match. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**Mode bits** — The 12 permission bits of `st_mode`: setuid, setgid, sticky, and read/write/execute for owner, group and other. [The UNIX Permission Model](../16-security/the-unix-permission-model.md)

**Module** — relocatable object code linked into an already-running kernel at load time instead of build time, running with exactly the same privileges as code compiled into `vmlinux`. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**Module signing** — Verification of a PKCS#7 signature appended to each `.ko` against the kernel's trusted keyrings at load time; enforced with `module.sig_enforce`. [Integrity: IMA, EVM, and Module Signing](../16-security/integrity-and-signing.md)

**Modversions** — a build-time mechanism (`CONFIG_MODVERSIONS`) that computes a CRC over each exported symbol's type signature and checks it at module-load time, refusing to load a module whose recorded CRC no longer matches the running kernel's. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**Monolithic kernel** — a kernel design where every subsystem runs in one address space at one privilege level, calling each other through ordinary function calls with no isolation boundary between them; drivers can still be compiled in or loaded as modules. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**Mount namespace** — a private copy of the mount tree, created with `CLONE_NEWNS`, so a process can mount, unmount, and `pivot_root` without changing what anyone else sees. [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md)

**Mount propagation** — the per-mount property (shared, slave, private, unbindable) deciding whether a mount event at one place is replayed at its peers — the reason a USB drive mounted on the host may or may not appear inside a container. [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md)

**MSI-X** — a PCIe device signals an interrupt by writing a specific data value to a specific address rather than asserting a physical line; MSI-X is the larger, more flexible per-device table of these write-triggered vectors, which is what makes one interrupt vector per hardware queue per core a real configuration. [Interrupt Controllers](../../computer-science/buses-and-io/interrupt-controllers.md)

**`MSR_LSTAR`** — the model-specific register holding the address the kernel registered at boot as the `SYSCALL` entry point; the CPU loads `RIP` from it as the first of the five hardwired steps `SYSCALL` performs on x86-64. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**Mutex** — a sleeping lock that spins first (optimistic spinning) before falling back to sleep, tracks a single owner, and — unlike a spinlock — may be held across anything that can block; for a short critical section a contended mutex costs close to what a contended spinlock costs. [Mutexes and Semaphores](../09-concurrency-and-locking/mutexes-and-semaphores.md)

**Nagle's algorithm** — holding a small TCP segment back while earlier data is unacknowledged; combined with delayed ACKs it stalls request/response traffic, which `TCP_NODELAY` disables. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**Namespace** — a kernel mechanism that changes what a process can *see* (which processes, network devices, hostname, IPC objects, etc. are visible or enumerable) without affecting what resources it's allowed to *use*; created via `CLONE_NEW*` flags to `clone()`. [Namespaces](../15-containers-and-virtualization/namespaces-overview.md)

**NAPI** — the receive-path model where a hardware interrupt only schedules polling rather than processing the packet itself; under light load it behaves like one interrupt per packet, but under heavy load the queue's interrupts are disabled and a poll loop drains it instead, bounding interrupt cost. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md); in depth: [The Receive Path](../13-networking-stack/the-receive-path.md)

**NAPT (port address translation)** — NAT that rewrites ports as well as addresses, so many private hosts can share one public address; what home routers and `masquerade` do. [NAT and Connection Tracking](../../computer-science/computer-networks/nat-and-connection-tracking.md)

**`ndo_start_xmit`** — The network-driver callback that hands one `sk_buff` to the hardware for transmission. [Block and Network Driver Shapes](../14-device-drivers-and-hardware/block-and-network-driver-shapes.md)

**`need_resched`** — at v6.18, `TIF_NEED_RESCHED`, a per-task bit in `struct thread_info::flags` set when a higher-priority task becomes runnable; a reschedule happens only once this flag is set *and* `preempt_count` is zero, at a point the kernel actually checks. x86-64 adds a second, weaker `TIF_NEED_RESCHED_LAZY` for `PREEMPT_LAZY`. [Preemption Models](../07-scheduling/preemption-models.md)

**Negative dentry** — a dentry that caches the answer "this name does not exist", so repeated failed lookups — `$PATH` searches, library probing — stay as cheap as successful ones. [Path Lookup and the Dentry Cache](../11-vfs-and-filesystems/path-lookup-and-the-dcache.md)

**Negative errno** — the kernel's actual failure convention: a syscall handler returns a small negative number (e.g. `-ENOENT`) directly as its return value instead of setting a side-channel `errno`, which the kernel has no variable for at all; a value from `0` up to `-MAX_ERRNO - 1` is success, everything from `-MAX_ERRNO` to `-1` is an error. [Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**Neighbour Discovery (NDP)** — IPv6's replacement for ARP, built on ICMPv6, which also handles router discovery and duplicate-address detection. [ARP, ICMP, and Neighbour Discovery](../../computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md)

**`netdev_budget`** — `net.core.netdev_budget` (and `netdev_budget_usecs`), the packet and time limits on one `NET_RX` softirq run; running out with work left increments `time_squeeze`. [The Receive Path](../13-networking-stack/the-receive-path.md)

**netem** — a qdisc that adds delay, jitter, loss, duplication, and reordering to an interface, to reproduce a bad network on a good one. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**Netfilter hook** — one of the fixed points in the stack — PRE_ROUTING, LOCAL_IN, FORWARD, LOCAL_OUT, POST_ROUTING, plus netdev ingress and egress — where registered functions can inspect, change, accept, or drop a packet. [netfilter and nftables](../13-networking-stack/netfilter-and-nftables.md)

**Network namespace** — a complete, separate copy of the network stack — interfaces, routes, netfilter rules, conntrack table, sockets — created with `CLONE_NEWNET`; a new one has only a loopback device, down. [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)

**New mount API** — the six syscalls added in Linux 5.2 — `fsopen`, `fsconfig`, `fsmount`, `move_mount`, `fspick`, `open_tree` — that split one `mount(2)` call into create, configure, and attach steps. [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md)

**Nexthop object** — a next hop defined once (`ip nexthop`, since Linux 5.3) and referenced by ID from many routes, optionally grouped for multipath. [Routing and Neighbours](../13-networking-stack/routing-and-neighbours.md)

**nftables** — the firewall front end that compiles rules in user space into bytecode for a small in-kernel virtual machine, with user-defined tables and chains, sets, maps, and atomic ruleset replacement. [netfilter and nftables](../13-networking-stack/netfilter-and-nftables.md)

**Nice weight** — the value `nice` actually changes: `sched_prio_to_weight[]` maps a nice level to a weight (`sched_entity.load.weight`) that scales how fast a task's vruntime advances and how its EEVDF virtual deadline is projected. Each nice step is a fixed ~1.25× geometric ratio, so a nice difference buys a constant *percentage* change in CPU share, not a fixed amount. [Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**No-internal-process rule** — cgroup v2's rule that a non-root cgroup with controllers enabled for its children may not itself contain processes. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**`no_new_privs`** — A per-task, irreversible, inherited flag under which `execve()` can't gain privilege from setuid bits or file capabilities; required for unprivileged seccomp. [Capabilities and Container Privilege](../15-containers-and-virtualization/capabilities-in-containers.md)

**`nohz_full`** — the boot parameter marking specific CPUs as adaptive-tick, stopping the periodic tick on a busy CPU once it has exactly one runnable task; it requires at least one housekeeping CPU and RCU callback offloading (`rcu_nocbs`), and is one part of a CPU-isolation configuration, not a standalone flag. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**`ns_capable`** — The kernel's capability check against a specific user namespace, so a capability held in a child namespace counts only for resources that namespace owns. [User Namespaces](../15-containers-and-virtualization/user-namespaces.md)

**`NSpid`** — The `/proc/<pid>/status` line listing a process's PID in each nested PID namespace, outermost first. [Mount and PID Namespaces](../15-containers-and-virtualization/mount-and-pid-namespaces.md)

**`nsproxy`** — The per-task structure pointing at the task's namespaces (all except the user namespace, which lives in its credentials). [Namespaces](../15-containers-and-virtualization/namespaces-overview.md)

**`nstat`** — the tool that reads the kernel's SNMP and netstat counters from `/proc/net/snmp` and `/proc/net/netstat`, showing what changed since its last run. [Diagnosing Network Problems](../13-networking-stack/diagnosing-network-problems.md)

**NUD state** — the state of a neighbour-table entry — `INCOMPLETE`, `REACHABLE`, `STALE`, `DELAY`, `PROBE`, `FAILED`, `NOARP`, `PERMANENT`; a healthy idle entry spends most of its life in `STALE`. [Routing and Neighbours](../13-networking-stack/routing-and-neighbours.md)

**NVMe queue pair** — one submission ring and one completion ring in host memory; the Linux NVMe driver maps one pair to each blk-mq hardware queue, usually one per CPU. [NVMe in the Kernel](../12-block-layer-and-storage/nvme-in-the-kernel.md)

**`O_DIRECT`** — an open flag that moves data between the user's buffer and the device without the page cache, at the price of alignment rules and no readahead or write-behind — and with no durability promise of its own. [Buffered I/O, `O_DIRECT`, and Alignment](../12-block-layer-and-storage/buffered-direct-and-alignment.md)

**`O_DSYNC`** — an open flag making each `write()` return only once its data, and the metadata needed to read it back, has reached stable storage — as if followed by `fdatasync()`. [Buffered I/O, `O_DIRECT`, and Alignment](../12-block-layer-and-storage/buffered-direct-and-alignment.md)

**OCI image** — A container image in the Open Container Initiative format: an index, a manifest, a config and content-addressed layer tarballs. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**OCI runtime spec** — The standard for what a runtime does with a bundle: the `config.json` fields and the create/start/kill/delete lifecycle. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**`offsetof`** — a compile-time constant giving the byte offset of a named field within its struct type, with no runtime cost; it is the arithmetic building block `container_of` is built on. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**OOM score** — the per-task badness value `oom_badness()` computes (RSS plus swapped-out memory plus page-table memory, shifted by `oom_score_adj`) and exposes read-only at `/proc/PID/oom_score`; it measures who freeing would help most, not who is at fault. [The OOM Killer](../08-memory-management/the-oom-killer.md)

**Opaque directory** — an upper-layer directory marked with an extended attribute so overlayfs shows none of the lower layer's entries beneath it — how deleting and recreating a directory is represented. [overlayfs](../11-vfs-and-filesystems/overlayfs.md)

**Optimistic spinning** — a contended mutex's first response: check whether the recorded owner is currently running on some CPU and, if so, spin (via an MCS queue) on the reasoning that a running owner will likely finish soon, only falling back to a real sleep once the owner is observed descheduled or the spin otherwise fails. [Mutexes and Semaphores](../09-concurrency-and-locking/mutexes-and-semaphores.md)

**Ordering versus requirement** — in systemd, `Requires=` and `After=` are independent axes: `Requires=` says what else must start as a dependency, `After=` says only which of two already-starting units goes first; declaring one does not imply the other. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**Overcommit** — the kernel's policy for how strictly it enforces "can I back everything I've promised" at allocation time rather than fault time, controlled by `vm.overcommit_memory` (0 heuristic, 1 always, 2 strict against `swap + RAM × overcommit_ratio`); a successful `malloc()` under modes 0/1 is a promise the kernel may not be able to keep in full. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**overlayfs** — the filesystem that merges a stack of read-only layers plus one writable layer into what looks like a single ordinary filesystem; a read resolves top-down through the layers, and writing a file that only exists in a lower layer copies it into the writable layer first. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md); in depth: [overlayfs](../11-vfs-and-filesystems/overlayfs.md)

**Page cache** — the in-RAM cache of file-backed pages that ordinary buffered I/O goes through; a `write()` copies bytes into page-cache pages and marks them dirty rather than touching the device immediately, so the data can exist only in RAM at the moment the call returns. [The Page Cache](../08-memory-management/the-page-cache.md)

**Page fault** (minor/major) — a CPU exception raised when an instruction touches a virtual address with no valid page-table entry; "minor" means the kernel resolved it without I/O (zero page, page-cache hit, copy-on-write copy), "major" means it had to block on a device (disk read or swap-in). [The Page Fault Handler](../08-memory-management/the-page-fault-handler.md)

**Page table level** — one of the fixed stages a virtual-address walk passes through (PGD, PUD, PMD, PTE on x86-64, with a generic `p4d_t` level that folds away to a no-op on a 4-level configuration), each level a 9-bit index into one 4 KiB table of 512 entries. [Page Tables and the Walk](../08-memory-management/page-tables-and-the-walk.md)

**Path MTU discovery** — finding the largest packet a path can carry by sending with "don't fragment" set and shrinking on ICMP "fragmentation needed" replies; a path that drops those replies becomes a black hole. [ARP, ICMP, and Neighbour Discovery](../../computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md)

**PCID (Process-Context Identifier)** — a hardware TLB tag letting entries from more than one address space coexist without a full flush on every switch; Linux recycles a small pool of PCIDs as ASIDs across recently-used `mm`s per CPU, and it is the concrete reason KPTI's per-syscall cost varies so much between machines with and without PCID support. [The TLB and Address-Space Switching](../08-memory-management/tlb-and-address-space-switching.md)

**PCIe link and lane** — A lane is one pair of differential signal pairs; a link is one or more lanes (x1 to x16) between two PCIe ports. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**Peer group** — the set of mounts that propagate mount and unmount events to one another; a mount's propagation type is defined relative to its peer group. [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md)

**Pending signal** — the state between a signal's generation (a bit set in `struct sigpending`) and its delivery at the next return to user space; a signal can be pending indefinitely if the target never reaches that checkpoint. [Signals](../06-processes-and-threads/signals.md)

**Per-CPU data** — the strategy that beats every lock by eliminating sharing rather than protecting it: give each CPU its own copy via `this_cpu_*`/`per_cpu()`, so there is no cache-line bouncing and nothing to combine except when a caller actually needs the aggregate total. [Per-CPU Data](../09-concurrency-and-locking/per-cpu-data.md)

**Permissive mode** — SELinux mode in which denials are logged but not enforced, for the whole system or for one domain. [SELinux](../16-security/selinux.md)

**`pick_next_task`** — the function (`kernel/sched/core.c`) that walks the scheduling classes from highest to lowest priority and takes the first task offered, with a fast path that skips straight to `pick_next_task_fair()` whenever every runnable task on the runqueue already belongs to the fair class. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**PID 1** — the first user-space process, distinguished from every other process only by having no parent, which is the single cause behind its special signal handling, orphan-reaping duty, and the kernel panic that follows if it ever exits. [`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**`pids.max`** — The cap on tasks in a cgroup subtree; `fork()` beyond it fails with `EAGAIN`. [cgroup Controllers in Practice](../15-containers-and-virtualization/cgroup-controllers-in-practice.md)

**`pivot_root`** — the call that moves a *mount namespace's* root to another directory already mounted within it, changing what an absolute path resolves through for every process sharing that namespace; distinct from `chroot`, which changes only the calling *process's* idea of `/` — a per-process attribute, not a mount-namespace-wide change. [Mount and PID Namespaces](../15-containers-and-virtualization/mount-and-pid-namespaces.md)

**Platform device** — A device that isn't discoverable on its bus, so firmware (device tree or ACPI) or board code has to declare it; matched to a `platform_driver`. [Platform Devices, Device Tree, and ACPI](../14-device-drivers-and-hardware/platform-devices-and-description.md)

**Plugging** — a batching window opened with `blk_start_plug()` in which adjacent `bio`s can merge into one larger request before any is dispatched. [The `bio`](../12-block-layer-and-storage/the-bio.md)

**Policy routing rule** — an `ip rule` entry that selects which routing table to consult based on source, mark, interface, UID, or protocol, evaluated in priority order before any route lookup. [Routing and Neighbours](../13-networking-stack/routing-and-neighbours.md)

**Popek–Goldberg requirements** — The 1974 conditions for a virtualizable architecture: every sensitive instruction must be privileged, so it traps when run in a VM. [Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md)

**Port publishing** — Making a container port reachable on a host port, implemented as a DNAT rule plus conntrack. [Container Networking](../15-containers-and-virtualization/container-networking.md)

**POSIX ACL** — Additional named-user and named-group permission entries on a file, capped by a mask entry, stored in the `system.posix_acl_access` xattr. [The UNIX Permission Model](../16-security/the-unix-permission-model.md)

**Posted write** — A PCIe memory write that completes for the CPU before it reaches the device; reading back a register on the device forces earlier writes to arrive. [MMIO, ioremap, and Accessors](../14-device-drivers-and-hardware/mmio-and-port-io.md)

**`PR_SET_CHILD_SUBREAPER`** — a `prctl(2)` flag letting any process opt in to reaping orphans from its own descendant tree, instead of every orphan reparenting all the way up to PID 1; it's the mechanism container supervisors like `tini` and `dumb-init` rely on. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Predictable interface name** — A network interface name derived from hardware location or firmware data (`enp0s3`, `ens3`) instead of probe order, set by udev. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**`preempt_count`** — a per-CPU counter incremented by taking a spinlock, entering interrupt or softirq context, or an explicit `preempt_disable()`; a reschedule is legal only when it is exactly zero, regardless of what `need_resched` says. [Preemption Models](../07-scheduling/preemption-models.md)

**Preemption model** — the kernel-wide policy for whether kernel-mode execution may be interrupted for scheduling before it finishes voluntarily; v6.18 offers four (`PREEMPT_NONE`, `PREEMPT_VOLUNTARY`, `PREEMPT`, `PREEMPT_LAZY`) plus `PREEMPT_RT` layered independently on top, trading worst-case latency against throughput. [Preemption Models](../07-scheduling/preemption-models.md)

**Probe** — A driver's `probe()` callback, called when the bus matches it to a device: it claims resources and makes the device usable, or returns an error and the device stays unbound. [The Linux Device Model](../14-device-drivers-and-hardware/the-linux-device-model.md)

**`proto_ops`** — the table of socket-API operations (`bind`, `connect`, `accept`, `poll`, ...) for one address family and socket type, such as `inet_stream_ops` for IPv4 TCP. [Sockets in the Kernel](../13-networking-stack/sockets-in-the-kernel.md)

**PSI (Pressure Stall Information)** — the fraction of recent wall-clock time tasks in some scope spent runnable-but-waiting for a resource (`some`: at least one task waiting; `full`: every task waiting simultaneously), reported over 10/60/300-second windows; it measures lost time directly, which is why it distinguishes an overloaded machine from a busy-but-unblocked one in a way plain utilisation or load average cannot. [Diagnosing Scheduling Latency](../07-scheduling/diagnosing-scheduling-latency.md)

**PSS (proportional set size)** — resident pages divided by their number of sharers, summed per process; the only one of the four per-process memory metrics (VSZ, RSS, PSS, USS) that sums correctly across processes into a true total, which RSS explicitly does not. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**`PT_INTERP`** — the ELF program header naming the dynamic linker's path; when present, `load_elf_binary()` maps that second binary into the new address space and jumps to *its* entry point first, not the program's own. [`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**`pt_regs`** — the fixed-layout struct the syscall entry stub builds on the kernel stack from the registers `SYSCALL` didn't save itself (`ss`, old `rsp`, `rflags`, `cs`, old `rip`, syscall number, then the general-purpose registers), giving every syscall handler, tracer, and oops dump the same byte-for-byte way to find a caller's register state. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**PTE** — the leaf page-table entry; its present, read/write, user/supervisor, accessed, dirty, and NX bits are what copy-on-write, permission faults, the approximate-LRU accessed-bit scheme, and W^X hardening are each built directly out of. [Page Tables and the Walk](../08-memory-management/page-tables-and-the-walk.md)

**qdisc (queueing discipline)** — the scheduler in front of each transmit queue that decides which packet goes next, how long packets wait, and which are dropped. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**QEMU gdbstub** (`-s -S`) — `-s` opens a GDB stub listening on TCP port 1234 exposing the guest's virtual CPU; `-S` freezes the guest at its first instruction until GDB tells it to continue, letting GDB drive the CPU directly regardless of whether guest software is responsive. [Debugging the Kernel with GDB](../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md)

**`queue_rq`** — The blk-mq callback a block driver implements to start one request on the hardware. [Block and Network Driver Shapes](../14-device-drivers-and-hardware/block-and-network-driver-shapes.md)

**Queued spinlock** — the kernel's actual `spinlock_t` implementation (`struct qspinlock`, MCS-lock-derived): each waiter beyond the first queues on its own per-CPU node instead of the shared lock word, turning contention into a fair FIFO instead of a cache-line-bouncing free-for-all. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**Quiescent state** — a moment at which a given CPU is provably not in the middle of an RCU read-side critical section (a context switch, a return to user space, going idle); detecting one costs nothing extra because it rides on events the kernel already produces for other reasons. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**RACK-TLP** — Linux's default TCP loss detection (RFC 8985): a segment is lost if a later one was acknowledged and enough time passed, with a tail loss probe for the last segments of a burst. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**RAID level** — a scheme for spreading data across disks — striping (0), mirroring (1), parity (5, 6), or combinations — trading capacity against how many failures are survived. [RAID and Redundancy](../../computer-science/storage/raid-and-redundancy.md)

**`raw_spinlock_t`** — the spinlock type exempted from `PREEMPT_RT`'s transformation of ordinary `spinlock_t` into a sleeping, priority-inheriting `rt_mutex`; it stays a genuine non-sleeping, non-preemptible spinlock on every configuration, which is why scheduler internals and interrupt-core code use it explicitly. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**RCU (Read-Copy-Update)** — a synchronization scheme where readers take no lock, write no shared state, and are never blocked by a writer; a writer instead builds an entire new version, publishes it with one pointer store, and defers reclaiming the old version until every reader that could still hold it has finished. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**`rcu_dereference`** — the RCU-specific acquire-paired pointer read: fetches a pointer with the dependency-ordering guarantee that a reader can safely follow it into newly-published data, and is only valid inside a read-side critical section (or, on the update side under the writer's own lock, via `rcu_dereference_protected()` instead). [RCU in Practice](../09-concurrency-and-locking/rcu-in-practice.md)

**RCU-walk and ref-walk** — the two modes of path walking: RCU-walk resolves components without taking a single reference or lock, and falls back to ref-walk (`try_to_unlazy`) only when something it read may have changed underneath it. [Path Lookup and the Dentry Cache](../11-vfs-and-filesystems/path-lookup-and-the-dcache.md)

**`READ_ONCE`** (and `WRITE_ONCE`) — a genuine single load or store via a `volatile` cast that forbids the compiler from merging, splitting, inventing, or hoisting the access; it says nothing about ordering relative to other variables and nothing to the CPU about store-buffer visibility, so it solves only the compiler half of the ordering problem. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**Readahead** — detection of a sequential access pattern that triggers large asynchronous reads ahead of where a caller currently is, so the folios covering the next offset are usually already resident by the time `read()` reaches them; a pattern that starts sequential and then jumps randomly defeats it as **read amplification**, I/O issued for data never consumed. [The Page Cache](../08-memory-management/the-page-cache.md)

**Readiness versus completion** — the two shapes of asynchronous I/O API: readiness (`select`, `epoll`) says an operation would no longer block; completion (`io_uring`, IOCP) says it has finished. [Sockets and the Application Boundary](../../computer-science/computer-networks/sockets-and-the-application-boundary.md)

**Real-time signal** — a signal in `SIGRTMIN`–`SIGRTMAX` that, unlike a standard signal, genuinely queues (multiple pending instances are each delivered) and can carry an integer or pointer value via `sigqueue()`. [Signals](../06-processes-and-threads/signals.md)

**Red-black tree** (`rb_node`/`rb_root`) — the kernel's balanced binary search tree, embedded intrusively like `list_head`; the kernel's rbtree code owns balancing (`rb_insert_color()`, `rb_erase()`) while the caller writes the comparison and walk logic itself, avoiding a per-comparison indirect call. The CFS scheduler's runqueue is the canonical example. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Refault** — a page reclaimed and then read back almost immediately, costing the reclaim work for zero net memory saved; it is the direct, measurable signal (`workingset_refault_file`/`_anon`) that the working set no longer fits available memory, distinguishing healthy reclaim from thrashing. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**Refcount saturation** — `refcount_t`'s behaviour on overflow: it sticks at a saturated value and warns, leaking the object instead of freeing it while in use. [Vulnerability Classes in the Kernel](../16-security/vulnerability-classes.md)

**`refcount_t`** — a dedicated reference-counting type (distinct from `atomic_t`) that saturates instead of wrapping on overflow and refuses to increment from zero, closing two failure modes a plain atomic counter has when used as an object's lifetime counter. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**Reflink** — a copy-on-write clone of a file's extents (`FICLONE`): both files share the same blocks until one of them writes, so a "copy" of any size is instant. [XFS and Btrfs](../11-vfs-and-filesystems/xfs-and-btrfs.md)

**Relaxed accessor** — `readl_relaxed()`/`writel_relaxed()`: MMIO accesses without the barriers the ordinary accessors include, for hot paths that order DMA themselves. [MMIO, ioremap, and Accessors](../14-device-drivers-and-hardware/mmio-and-port-io.md)

**Reparenting** — what happens to a task's children when it dies first: `forget_original_parent()` hands each one to the nearest subreaper ancestor, or to PID 1 of its PID namespace if none exists. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**`REQ_PREFLUSH`** — a `bio` flag asking the device to flush its volatile write cache before this write; paired with `REQ_FUA`, it is how a filesystem makes ordering survive power loss. [The `bio`](../12-block-layer-and-storage/the-bio.md)

**Request size (slice)** — a task's declared amount of CPU per turn under EEVDF (`sched_entity.slice`), defaulting to `sysctl_sched_base_slice` (0.7ms) but settable per-task via `sched_setattr()`'s `sched_runtime` field (clamped to 0.1–100ms). A smaller request size earns an earlier virtual deadline and therefore more prompt scheduling, entirely independent of the task's weight or aggregate CPU share. [EEVDF](../07-scheduling/eevdf.md)

**`request_firmware`** — The call a driver uses to load a firmware blob, which the kernel looks up in `/lib/firmware` and hands back as a buffer. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**`RESOLVE_*` flags** — `openat2(2)` options that constrain path resolution itself — `RESOLVE_BENEATH`, `RESOLVE_IN_ROOT`, `RESOLVE_NO_SYMLINKS` and others — so a program can open a path inside a directory without `..` or symlinks escaping it. [Path Lookup and the Dentry Cache](../11-vfs-and-filesystems/path-lookup-and-the-dcache.md)

**Resync** — `md` re-checking an array's redundancy after an unclean shutdown, because a stripe in flight at the crash may have data and parity that disagree. [Software RAID (md)](../12-block-layer-and-storage/software-raid.md)

**rootfs** — the always-present `tmpfs`-family filesystem the kernel mounts at `/` before anything else exists, whether or not an initramfs archive is ever unpacked into it. [initramfs and Early User Space](../03-boot-and-init/initramfs-and-early-userspace.md)

**Rootless container** — A container whose runtime runs as an ordinary user, using a user namespace to be root inside without being root on the host. [User Namespaces](../15-containers-and-virtualization/user-namespaces.md)

**`rp_filter`** — reverse-path filtering: dropping a received packet if a reply to its source would not leave by the interface it arrived on (strict, `1`) or by any interface (loose, `2`). [Routing and Neighbours](../13-networking-stack/routing-and-neighbours.md)

**RSS (resident set size)** — physical pages currently resident and mapped into a process's page tables; it double-counts, since a page shared with N other processes counts fully in every one of their RSS, which is why summing RSS across a forked worker pool can overstate real memory use by several times. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**RSS, RPS, RFS** — three layers of receive steering: the NIC hashing flows to queues (RSS), the kernel spreading packets to CPUs in software (RPS), and steering each flow to the CPU its reading thread runs on (RFS). [The Receive Path](../13-networking-stack/the-receive-path.md)

**RT throttling** — the safety valve bounding `SCHED_FIFO`/`SCHED_RR` tasks, which have no deadline-style budget of their own: by default the real-time class as a whole may consume only `sched_rt_runtime_us` out of every `sched_rt_period_us` (95% by default), guaranteeing the remaining 5% to non-RT tasks; when the throttle triggers, the RT class simply stops running for the rest of the period. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**RTO (retransmission timeout)** — how long TCP waits for an ACK before retransmitting, computed from the smoothed RTT and its variance and never below `TCP_RTO_MIN` (200 ms). [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**runc** — The reference OCI runtime, which turns a bundle into a running container by making the namespace, cgroup, mount, capability and seccomp calls. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**Runqueue** — `struct rq`, one per CPU, the lock-protected container holding a sub-runqueue per scheduling class (`cfs`, `rt`, `dl`, and `scx` when enabled) plus cross-class bookkeeping (`nr_running`, `clock`, `curr`); waking a task that last ran on a different CPU means touching that CPU's runqueue lock and cache lines, which is why cross-CPU wakeup and migration are expensive relative to a local reschedule. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**Runtime PM** — Per-device power management while the system runs: a device is suspended when idle and resumed on use, tracked by a usage count. [Power Management](../14-device-drivers-and-hardware/power-management.md)

**`rw_semaphore`** — the sleeping reader-writer lock, FIFO-fair by default via a handoff flag that prevents a stream of new readers from starving a waiting writer; it earns its keep specifically for long, sleeping read-side sections (`mmap_lock` is the canonical example), not for short critical sections where a plain lock is usually faster. [Reader-Writer Locks](../09-concurrency-and-locking/rwlocks-and-rwsems.md)

**s2idle** — Suspend-to-idle: system sleep implemented by freezing tasks, suspending devices and idling all CPUs, without platform firmware support. [Power Management](../14-device-drivers-and-hardware/power-management.md)

**Saved set-user-ID** — the copy of a task's effective UID taken at `exec()` time, which lets a setuid-root program drop privilege temporarily and later regain it with one `seteuid()` call, even as an unprivileged real UID. [Credentials and Identity](../06-processes-and-threads/credentials-and-identity.md)

**Scatter-gather** — DMA over a list of separate memory segments in one operation, so a buffer needn't be physically contiguous. [DMA and the IOMMU](../../computer-science/buses-and-io/dma-and-iommu.md)

**`SCHED_DEADLINE`** — the policy under which a task declares a runtime, deadline, and period instead of a priority; the kernel runs a schedulability (admission) test at `sched_setattr()` time and refuses the task outright if accepting it would leave the system unschedulable — the only Linux scheduling policy that makes a guarantee rather than a promise. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**`SCHED_FIFO`** — a static-priority (1–99) real-time policy that preempts and stays ahead of every fair-class task unconditionally; a task runs until it blocks, yields, or is preempted by a higher-priority task, with no time slice and no rotation among equal-priority tasks (unlike its sibling `SCHED_RR`). [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**Scheduling class** — one of the (five, six counting `sched_ext`) fixed, strictly-ordered schedulers stop → deadline → real-time → fair → idle, each implementing the `struct sched_class` vtable (`enqueue_task`, `pick_next_task`, `task_tick`, `select_task_rq`, …) and getting first refusal on the CPU before the next lower class is even consulted. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**Scheduling domain** — `struct sched_domain`, the hierarchy the load balancer builds to mirror a machine's actual hardware-sharing structure (SMT siblings, cores sharing an LLC, sockets, NUMA nodes), so migration cost can be weighed against which level a move crosses instead of treating every CPU as interchangeable. [SMP and Load Balancing](../07-scheduling/smp-load-balancing.md)

**`SCM_RIGHTS`** — ancillary data sent over a UNIX-domain socket that transfers an open file descriptor to another, unrelated process, installing a new descriptor in the receiver that points at the identical underlying `struct file`. [Pipes, FIFOs, and UNIX Sockets](../06-processes-and-threads/pipes-fifos-and-unix-sockets.md)

**seccomp filter** — A classic BPF program run on every syscall of a thread and its descendants, returning allow, errno, trap, kill, trace, log or user-notify. [seccomp and Syscall Filtering](../16-security/seccomp.md)

**Seccomp user notification** (`SECCOMP_RET_USER_NOTIF`) — the mechanism actually built to intervene in a syscall rather than merely observe it: a matching filter suspends the calling task and hands a supervisor process a file descriptor carrying a race-free `struct seccomp_notif` snapshot, letting the supervisor allow, fail, or (carefully) continue the call. [seccomp and Syscall Filtering](../16-security/seccomp.md)

**Secure Boot** — a signature-verification gate that checks, at each handoff from firmware to boot loader to kernel, whether the thing about to execute is signed by a key the machine trusts; it verifies provenance only, not the safety of what runs. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**Securebits** — Per-credential flags that turn off root's special treatment in the capability rules, each with a lock bit making it permanent. [Capabilities](../16-security/capabilities.md)

**Security context** — An SELinux label, `user:role:type:level`, on every process and object; the type is what most rules use. [SELinux](../16-security/selinux.md)

**SELinux boolean** — A run-time switch that turns a group of conditional policy rules on or off without recompiling the policy. [SELinux](../16-security/selinux.md)

**`seq_file`** — the kernel interface (`include/linux/seq_file.h`) behind most non-trivial `/proc` entries: rather than a stored buffer, it invokes a `show` callback that formats live kernel state into a transient buffer at the moment of the read. [`/proc` as the Process Interface](../06-processes-and-threads/proc-as-the-process-interface.md)

**Seqlock** — a scheme that lets readers proceed with no lock and no wait at all, and instead detects after the fact whether a writer interfered, via a sequence counter that's odd while a write is in progress and a reader retry loop; the kernel's timekeeper is the canonical user. [Seqlocks](../09-concurrency-and-locking/seqlocks.md)

**Sequence counter** — the bare counter half of a seqlock (`seqcount_t`), with no lock embedded, for use when the caller already holds some other lock that serializes writers and only needs the counter for readers' retry-detection benefit; `seqlock_t` is this counter bundled with its own spinlock instead. [Seqlocks](../09-concurrency-and-locking/seqlocks.md)

**`setns`** — The syscall that joins an existing namespace, given a file descriptor for it from `/proc/<pid>/ns/` or a pidfd. [Namespaces](../15-containers-and-virtualization/namespaces-overview.md)

**Setup header** — the fixed-layout struct inside a `bzImage` that forms the binary contract between the boot loader and the kernel, specifying which fields the loader must fill in (like `cmd_line_ptr`, `ramdisk_image`) versus only read. [Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**Shaping and policing** — two ways to enforce a rate: shaping delays excess egress traffic in a queue, policing drops excess traffic as it arrives — the only option on ingress. [Traffic Control and qdiscs](../13-networking-stack/traffic-control.md)

**`shim`** — a small loader signed by Microsoft's UEFI CA that nearly every Secure-Boot-enabled PC trusts out of the box; once running, it verifies a distribution's actual boot loader against its own baked-in key instead, so only `shim` itself needs a key in every machine's `db`. It also supports MOK enrolment, letting a user add their own signing key for a locally-built kernel module. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**Shim** — The small per-container process (`containerd-shim-runc-v2`, or Podman's `conmon`) that stays as the container's parent, holding its stdio and exit status. [Images, Layers, and the OCI Runtime](../15-containers-and-virtualization/images-layers-and-oci.md)

**shmem** — the one subsystem (`mm/shmem.c`) behind tmpfs, POSIX shared memory, `memfd_create`, and System V shared memory — they differ only in how a name gets attached to a shmem inode. [tmpfs and Memory-Backed Filesystems](../11-vfs-and-filesystems/tmpfs-and-memory-filesystems.md)

**Shrinker (`struct shrinker`)** — the callback pair (count freeable objects, free a requested count) a cache the page allocator can't see directly — the dentry cache, the inode cache, any slab-built subsystem cache — registers so reclaim can ask it to give memory back as part of the same pass that scans the LRU lists. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**`sigreturn`** — the syscall (`rt_sigreturn()`) a handler's return compiles down to, which reads the signal frame back off the user stack and restores the interrupted registers, mask, and instruction pointer; it must validate that frame carefully, since a forged one is the basis of sigreturn-oriented-programming (SROP) exploits. [Signals](../06-processes-and-threads/signals.md)

**Size class** — the power-of-two (plus 96- and 192-byte) object sizes `kmalloc()`'s generic slab caches are built at; a request is rounded up to the smallest class that fits it, so a struct that grows just past a class boundary can nearly double its per-object memory cost. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**`sk_buff`** — the single structure that represents a packet through its entire trip up the networking stack, carrying both its bytes and the kernel's accumulating understanding of them; each layer strips a header by moving a pointer, not by copying. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md); in depth: [`sk_buff`: The Packet Container](../13-networking-stack/sk-buff.md)

**Slab (cache)** — a pool dedicated to one object type or size, carved from pages the page allocator supplied, with a freelist threading unused slots together so `alloc`/`free` push and pop that list instead of touching the page allocator on every call. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**Slice and scope** — systemd's cgroup units: a slice is a node for grouping (`user.slice`), a scope holds processes started elsewhere, alongside services that systemd starts itself. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**SLUB** — the only slab allocator left in the tree at v6.18 (SLAB and SLOB were both removed), built on a per-CPU active slab per cache, a freelist threaded through the free objects' own memory rather than a separate bookkeeping array, and per-node partial lists consulted before a fresh page allocation. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**SMAP** (Supervisor Mode Access Prevention) — hardware that stops the kernel from accessing user pages at all except inside a window explicitly opened with `stac` and closed with `clac`, the window the user-copy routines run inside; it turns an unprotected user dereference into an immediate, reproducible fault instead of a bug that might silently work for years. [Kernel Hardening](../16-security/kernel-hardening.md)

**SMEP** (Supervisor Mode Execution Prevention) — hardware that stops the kernel from ever executing instructions living on a user page, closing off jumping into attacker-controlled code regardless of what confused kernel-mode state set `RIP` there. [Kernel Hardening](../16-security/kernel-hardening.md)

**`sock_diag`** — the netlink interface `ss` uses to ask the kernel for socket state, with filtering done in the kernel, instead of parsing `/proc/net/tcp` as text. [Diagnosing Network Problems](../13-networking-stack/diagnosing-network-problems.md)

**Socket (API)** — the operating system's endpoint abstraction for network communication: a handle an application binds, connects, listens, and reads and writes through. [Sockets and the Application Boundary](../../computer-science/computer-networks/sockets-and-the-application-boundary.md)

**Softirq** — one of a fixed set of ten compile-time deferred-work types, run with interrupts enabled on the interrupt-exit path (`irq_exit()` → `invoke_softirq()` → `handle_softirqs()`) almost immediately after a hard-IRQ handler returns; still atomic and unable to sleep, and the same type can run on several CPUs simultaneously. [Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**`somaxconn`** — `net.core.somaxconn`, the cap the kernel applies, without an error, to every `listen()` backlog in the namespace. [Sockets in the Kernel](../13-networking-stack/sockets-in-the-kernel.md)

**sparse** — a separate static-checking tool (`make C=1`/`C=2`) that understands the kernel's address-space annotations (`__user`, `__percpu`, `__iomem`, `__rcu`) as real types with real rules, catching misuse the C compiler itself silently accepts. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Spinlock** — a lock that busy-waits rather than sleeps, correct whenever the critical section is short or the context cannot sleep at all; taking one disables preemption on that CPU, and sleeping while holding one can hang the machine. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**SQPOLL** — an `io_uring` setup flag that starts a kernel thread to poll the submission ring, so a steady stream of I/O needs no `io_uring_enter()` calls at all, at the cost of a busy CPU. [`io_uring`](../12-block-layer-and-storage/io-uring.md)

**SRCU** — sleepable RCU: relaxes the classic-RCU rule against sleeping in a read-side section by tracking each `srcu_struct` domain's grace periods independently, at the cost of a read side that does real per-CPU bookkeeping instead of being nearly free. [RCU in Practice](../09-concurrency-and-locking/rcu-in-practice.md)

**Stack protector** — A compiler-inserted canary between local buffers and the return address, checked on function return. [Kernel Hardening](../16-security/kernel-hardening.md)

**`STATX_DIOALIGN`** — the `statx(2)` mask (since Linux 6.1) that reports a file's actual `O_DIRECT` alignment requirements for the buffer address and the file offset. [Buffered I/O, `O_DIRECT`, and Alignment](../12-block-layer-and-storage/buffered-direct-and-alignment.md)

**Sticky bit** — On a directory, the bit restricting deletion and renaming of entries to their owner, the directory's owner, or `CAP_FOWNER`; why `/tmp` is `1777`. [The UNIX Permission Model](../16-security/the-unix-permission-model.md)

**Streaming DMA mapping** — A per-transfer mapping of an existing buffer (`dma_map_single()`, `dma_map_sg()`), owned by the device until it is unmapped or synced back to the CPU. [The DMA API](../14-device-drivers-and-hardware/the-dma-api.md)

**`struct file`** — the VFS object for one *open* of a file: the current offset, the open flags, and the `f_op` table; two `open()` calls on the same path produce two of them over one inode. [Superblock, Inode, Dentry, File](../11-vfs-and-filesystems/the-four-objects.md)

**`struct pci_dev`** — The kernel's object for one PCI function, holding its IDs, BAR resources, IRQ and DMA settings; what a PCI driver's `probe()` receives. [PCI and PCIe Drivers](../14-device-drivers-and-hardware/pci-and-pcie-drivers.md)

**`struct socket` and `struct sock`** — the two halves of a socket in the kernel: `struct socket` faces the VFS and the syscall layer; `struct sock` holds the protocol's queues, buffers, state, and wait queue. [Sockets in the Kernel](../13-networking-stack/sockets-in-the-kernel.md)

**Subreaper** — a process that has opted in (via `prctl(PR_SET_CHILD_SUBREAPER, 1)`) to inherit orphaned descendants from its own tree instead of letting them fall all the way to PID 1. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Subvolume** — an independently mountable and snapshottable filesystem tree inside a Btrfs volume, with its own root in the copy-on-write B-tree. [XFS and Btrfs](../11-vfs-and-filesystems/xfs-and-btrfs.md)

**Superblock (`super_block`)** — the VFS object for one mounted filesystem instance — not one per device and not one per mount point — holding its block size, flags, root dentry, and the filesystem's operations table. [Superblock, Inode, Dentry, File](../11-vfs-and-filesystems/the-four-objects.md)

**Swap entry (`swp_entry_t`)** — what a PTE is rewritten to hold once its page is swapped out: cleared of its present bit and repurposed to encode a swap type (device) and offset in the bits hardware ignores when not-present, which is why a swapped page is found by a page fault rather than a separate lookup table. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**Swappiness** — `vm.swappiness`, the relative I/O cost the kernel assigns to reclaiming anonymous pages versus file-backed pages (range 0–200 at v6.18, not the older 0–100), not a probability dial; values above 100 are meaningful specifically for fast in-memory swap backends like zram/zswap. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**swiotlb (bounce buffer)** — A pool of low memory the DMA API copies through when a device can't reach the real buffer, or when memory must be shared with an untrusted host. [The DMA API](../14-device-drivers-and-hardware/the-dma-api.md)

**SYN cookies** — a fallback for a full SYN queue in which the handshake state is encoded into the SYN-ACK's sequence number, so the kernel stores nothing until the client's ACK proves it is real. [Sockets in the Kernel](../13-networking-stack/sockets-in-the-kernel.md)

**`SYSCALL`** — the x86-64 instruction that performs exactly five hardwired steps (load `RIP` from `MSR_LSTAR`, save the old `RIP` in `rcx` and old `RFLAGS` in `r11`, mask `RFLAGS` against `MSR_SYSCALL_MASK`, load `CS`/`SS` from `MSR_STAR`, jump) and nothing else — it switches no stack and saves no other register, leaving everything else to software. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**`SYSCALL_DEFINEn`** — the macro family (`SYSCALL_DEFINE0` through `SYSCALL_DEFINE6`) that expands a syscall's type/name argument list into an inner `__do_sys_*` implementation plus a `pt_regs`-unpacking wrapper, giving every syscall the same calling convention, consistent argument sign-extension, and automatic `sys_enter`/`sys_exit` tracepoint hookup. [The Table and the Dispatch](../05-syscalls-and-the-boundary/the-syscall-table-and-dispatch.md)

**Syscall table** — the generated array (or, on current kernels, `switch` statement) built at compile time from a per-architecture `.tbl` file that maps a syscall number to its handler; a syscall number, once shipped, is frozen forever, and a removed syscall leaves a permanent hole rather than being reassigned. [The Table and the Dispatch](../05-syscalls-and-the-boundary/the-syscall-table-and-dispatch.md)

**Sysfs attribute** — a small `struct attribute` (name plus mode) representing one exposed value; reading or writing the corresponding file in `/sys` calls the owning `ktype`'s `show()`/`store()` functions live, computing the value on access rather than reading stored bytes. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**System call** — a deliberate, synchronous request a user process makes for a named kernel service: unlike an ordinary function call, it must change privilege level, switch to a trusted stack, and land at a fixed address the kernel — not the caller — chooses, initiated by executing a trapping instruction and blocking (from the process's view) until the kernel returns. [What a System Call Actually Is](../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md)

**Tag (blk-mq)** — an index into a per-hardware-queue bitmap that every in-flight request holds; the number of tags is the device's queue depth, and the driver uses the tag as the command identifier. [blk-mq: Multi-Queue Block I/O](../12-block-layer-and-storage/blk-mq.md)

**Taint** — a kernel-wide flag set when something happens that maintainers should weigh when reading a bug report — for example loading a module with a non-GPL-compatible license — recorded as a bitmask readable from `/proc/sys/kernel/tainted`. [Kernel Modules](../04-kernel-architecture-and-idioms/modules-in-practice.md)

**Target** — a systemd synchronization point with no process or executable of its own, just a name other units order themselves around, unlike a numbered SysV runlevel. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**`TASK_INTERRUPTIBLE`** — a sleeping state (`ps` shows `S`) whose wake function also reacts to a pending signal, unwinding the task back to user space to handle it rather than waiting only for the awaited event. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**`task_struct`** — the kernel's single, unified per-thread structure (there is no separate process or thread object); everything the kernel knows about a schedulable entity is a field of it, or reachable from it by one pointer. [`task_struct`: The Anatomy of a Task](../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md)

**`TASK_UNINTERRUPTIBLE`** — a sleeping state (`ps` shows `D`) whose wake function does not check for signals at all, used when a driver or filesystem has no safe way to abandon a multi-step operation partway through. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**Tasklet** — a function scheduled to run in softirq context (built on the `TASKLET`/`HI` softirqs) whose one added guarantee is that the same instance never runs concurrently on two CPUs; deprecated in favor of threaded IRQs or workqueues because that guarantee serialises globally rather than per-CPU. [Tasklets, and Why They Are Going Away](../10-interrupts-time-and-deferred-work/tasklets-and-their-replacement.md)

**TCP Small Queues (TSQ)** — the limit on how many bytes one TCP socket may have queued below it in the qdisc and driver (`tcp_limit_output_bytes`, scaled by pacing rate) before it waits for completions. [The Transmit Path](../13-networking-stack/the-transmit-path.md)

**`tgid`** — the thread-group id shared by every task in a thread group; `getpid()` returns it, while the per-task `pid` field (what `gettid()` returns) is what most people mean by "thread id." [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**Thin provisioning** — a device-mapper target that hands out blocks from a shared pool only when written, so volumes can be larger in total than the storage behind them. [Device Mapper and LVM](../12-block-layer-and-storage/device-mapper-and-lvm.md)

**THP (Transparent Huge Pages)** — automatic, opportunistic huge-page promotion of anonymous memory, either at fault time or via the `khugepaged` background scanner, requiring no application changes and giving no guarantee a given region ends up huge-page-backed; the opposite reliability model from hugetlbfs. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**Thread group** — the set of tasks created with `CLONE_THREAD` from a common caller and sharing one `tgid`; it is what POSIX calls a process, and userspace tools aggregate a thread group's tasks to display "a process" at all. [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**Threaded IRQ** — an interrupt whose substantive work runs in its own dedicated kernel thread (`SCHED_FIFO`, priority 50 by default) rather than in hard-IRQ context, registered via `request_threaded_irq()`'s `thread_fn`; the thread may sleep, take mutexes, and allocate `GFP_KERNEL`, everything a hard-IRQ primary handler cannot. [Threaded IRQs](../10-interrupts-time-and-deferred-work/threaded-irqs.md)

**Throttling** — under a cgroup `cpu.max` quota, what happens the instant a group exhausts its period's budget: not a slowdown, a full stop, with no thread in the group running again until the next period refills the quota — the mechanism that turns a CPU limit into a latency spike rather than a smooth speed reduction. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**Tick** — the periodic timer interrupt that historically updated `jiffies`, ran expired timers, accounted CPU time, checked timeslices, drove RCU quiescent-state detection, and triggered load balancing, all from one interrupt firing `HZ` times a second on every CPU. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**`TIME_WAIT`** — the 60-second state (`TCP_TIMEWAIT_LEN`) the side that closes first stays in, so stray segments of the old connection can't corrupt a new one; no sysctl changes its length. [TCP in the Kernel](../13-networking-stack/tcp-in-the-kernel.md)

**Timer slack** — a per-task value (`PR_SET_TIMERSLACK`, in nanoseconds) letting the kernel delay that task's timer expiries by up to the slack amount so they can be batched against other timers waking nearby, the same coalescing idea `round_jiffies` applies to the wheel but exposed per-task and runtime-tunable. [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**Timer wheel** (`timer_list`) — the kernel's default timer structure, bucketing timers into cascading levels of increasing coarseness so insertion and deletion are O(1), a trade made deliberately because most kernel timers are cancelled before they ever fire. [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**TLB reach** — the amount of address space a TLB can translate without a walk, equal to entries × page size; the same handful of thousand cached entries covers roughly 500× more space at 2 MiB pages than at 4 KiB, which is the actual mechanism huge pages help through, not a shorter walk. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**TLB shootdown** — the protocol for invalidating a stale translation on every other CPU that might have cached it: find candidate CPUs via `mm_cpumask(mm)`, IPI each one, wait for every acknowledgment before the memory can be reused — the software workaround x86-64 needs because it has no instruction that broadcasts invalidation on its own. [The TLB and Address-Space Switching](../08-memory-management/tlb-and-address-space-switching.md)

**TLP (transaction layer packet)** — The packet PCIe uses for memory reads and writes, configuration accesses, messages and completions. [PCIe in Depth](../../computer-science/buses-and-io/pcie-in-depth.md)

**tmpfs** — a filesystem made of page-cache pages with nothing underneath, implemented by shmem; it can swap, has a `size=` limit (half of RAM by default), and is gone on reboot. [tmpfs and Memory-Backed Filesystems](../11-vfs-and-filesystems/tmpfs-and-memory-filesystems.md)

**Transient execution** — CPU speculation past a branch or check whose discarded results still leave traces in caches; the class behind Spectre, Meltdown and MDS. [Vulnerability Classes in the Kernel](../16-security/vulnerability-classes.md)

**Tristate** — a Kconfig symbol type with three legal values — `n` (absent), `y` (built into `vmlinux`), or `m` (built as a separate loadable module) — as opposed to `bool`'s two. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**TSC (Time Stamp Counter)** — a free-running cycle counter built into each x86 core, the fastest clocksource to read (one `rdtsc`) but historically the least trustworthy, since it could run at a variable frequency, stop in deep idle, or drift between cores; `constant_tsc`/`nonstop_tsc` CPU feature flags say whether a given machine's TSC has these problems. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**TSO and GSO** — segmentation offload: TCP builds super-packets of up to 64 KB, and the NIC (TSO) or the kernel just before the driver (GSO) cuts them into MTU-sized frames. [The Transmit Path](../13-networking-stack/the-transmit-path.md)

**Type enforcement** — SELinux's model: access is allowed only if a rule permits the subject's type to perform the permission on the object's type and class. [SELinux](../16-security/selinux.md)

**udev rule** — A line in `/etc/udev/rules.d` or `/usr/lib/udev/rules.d` matching uevent properties and acting on them: naming, permissions, symlinks, running a program. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**UEFI** — the modern firmware model that behaves like a small OS: it reads a normal FAT32 partition, loads `.efi` executables, and exposes boot-services/runtime-services APIs, in contrast to legacy BIOS's real-mode, interrupt-driven model. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Uevent** — A message the kernel sends user space (over netlink) when a device is added, removed or changed, carrying its sysfs path and properties. [Firmware, udev, and Hotplug](../14-device-drivers-and-hardware/firmware-udev-and-hotplug.md)

**UID map** — The `/proc/<pid>/uid_map` table translating UIDs inside a user namespace to UIDs outside it; written once, by a suitably privileged process. [User Namespaces](../15-containers-and-virtualization/user-namespaces.md)

**UIO (Userspace I/O)** — A minimal framework exposing a device's memory and interrupts to user space through `/dev/uioN`, with no IOMMU protection for DMA. [Talking to User Space](../14-device-drivers-and-hardware/talking-to-user-space.md)

**umask** — The per-process mask of permission bits cleared from the mode of every newly created file and directory. [The UNIX Permission Model](../16-security/the-unix-permission-model.md)

**Unified hierarchy** — cgroup v2's single tree, in which every controller follows the same hierarchy, unlike v1's separate tree per controller. [cgroup v2](../15-containers-and-virtualization/cgroup-v2-architecture.md)

**Unit** — anything systemd manages; its filename suffix (`.service`, `.socket`, `.target`, `.mount`, `.timer`, `.path`, `.slice`) says what kind of thing it represents. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**`unshare`** — The syscall that moves the calling process into new namespaces of the given types without creating a new process. [Namespaces](../15-containers-and-virtualization/namespaces-overview.md)

**`__user`** — an annotation marking a pointer as pointing into user-space address space, which must never be dereferenced directly in kernel context; enforced only by sparse, not the compiler itself. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**User space** — code the machine does not trust with the hardware directly (shells, browsers, ordinary programs); it has its own address space and can only touch what its mappings and file descriptors permit. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**USS (unique set size)** — private, unshared resident pages only; the number that answers "what would be freed if I killed this process right now," since by construction nothing in it is shared with anything else. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**`%util`** — the `iostat` column for the share of time a device had at least one request in flight — meaningful for a disk that serves one request at a time, misleading for an SSD that serves hundreds in parallel. [Diagnosing I/O Problems](../12-block-layer-and-storage/diagnosing-io-problems.md)

**vDSO** (virtual dynamic shared object) — a small ELF shared object built into the kernel image and mapped into every process at exec time, exporting a short list of functions (`clock_gettime`, `gettimeofday`, `time`, `getcpu`, `clock_getres` on x86-64) that can be answered entirely in user space, so most calls to them never enter the kernel at all. [The vDSO](../05-syscalls-and-the-boundary/the-vdso.md)

**Vermagic** — a string embedded in both a compiled module and the running kernel (kernel release, SMP/preemption config, module-unload/modversions support, arch token) that must match exactly for a module to load, checked independently of and before modversions. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**veth pair** — two virtual Ethernet devices joined back to back, so a frame sent on one is received on the other; one end in a namespace and one on the host is the basic container link. [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)

**VFIO** — A framework that gives a user-space program (or a VM) safe, IOMMU-isolated access to a whole device: its BARs, interrupts and DMA. [Talking to User Space](../14-device-drivers-and-hardware/talking-to-user-space.md)

**VFS (Virtual File System)** — the kernel layer that gives every filesystem — on-disk, network, in-memory, or generated like `/proc` — the same object model and the same syscalls, so `read()` never needs to know what is underneath. [Why the VFS Exists](../11-vfs-and-filesystems/why-vfs-exists.md)

**vhost** — A host-kernel implementation of a virtio device's datapath, woken through `ioeventfd` and signalling through `irqfd`, so I/O doesn't pass through QEMU. [virtio and Paravirtual Devices](../15-containers-and-virtualization/virtio-and-paravirtualization.md)

**virtio** — The standard for paravirtual devices: the guest knows it is virtualized and exchanges buffers with the host through virtqueues. [virtio and Paravirtual Devices](../15-containers-and-virtualization/virtio-and-paravirtualization.md)

**virtiofs** — FUSE carried over a `virtio` transport instead of `/dev/fuse`, used to share a host directory into a virtual machine. [FUSE](../11-vfs-and-filesystems/fuse-and-userspace-filesystems.md)

**Virtqueue** — virtio's shared-memory ring of buffer descriptors between guest driver and device, with available and used rings and suppressible notifications. [virtio and Paravirtual Devices](../15-containers-and-virtualization/virtio-and-paravirtualization.md)

**VM exit** — A transfer from a guest to the hypervisor caused by an intercepted instruction or event, with the reason recorded for the hypervisor to handle. [Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md)

**VMA (`vm_area_struct`)** — one contiguous range of a process's address space with uniform properties (permissions, a backing file and offset if any), describing what the process is *entitled* to have mapped; almost every memory operation a process performs is first an operation on the VMA collection, with the page tables catching up lazily afterward. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**`vmalloc`** — allocates scattered physical pages and builds new page-table entries mapping them consecutively into one virtual range, for callers that need virtual contiguity but not physical; it costs page-table setup and TLB pressure a `kmalloc` allocation in the already-mapped direct map does not pay. [`vmalloc` and Choosing an Allocator](../08-memory-management/vmalloc-and-choosing-an-allocator.md)

**VMCS (virtual machine control structure)** — Intel's in-memory structure holding a vCPU's guest and host state and the controls deciding which events exit. [Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md)

**`vmlinux`** — the uncompressed ELF kernel image carrying full DWARF debug symbols when `CONFIG_DEBUG_INFO` is on; it is not bootable itself and exists to be read by tools like GDB. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**`vmlinuz`** — the conventional installed name (e.g. `/boot/vmlinuz-$(uname -r)`) a distribution gives to a copy of its `bzImage`; same file, different name and location. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**VMX root and non-root** — Intel VT-x's two modes: the hypervisor runs in root mode, guests in non-root, and sensitive events in non-root cause a VM exit. [Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md)

**Vruntime** — a task's real execution time divided by its scheduling weight, originally used by CFS to pick directly the task furthest behind (the leftmost node of a red-black tree ordered by vruntime); at v6.18 it is still accumulated the same way, but EEVDF no longer compares it directly to choose who runs — it instead feeds lag (eligibility) and the virtual-deadline calculation. [CFS and Virtual Runtime](../07-scheduling/cfs-and-vruntime.md)

**`vvar`** — the data-only page the kernel maps alongside the vDSO's code page, holding the live timekeeping state (clocksource reading, multiplier/shift, wall-clock/monotonic offsets) the vDSO reads through a seqlock; kept separate from the code page so the kernel can update it on every tick without touching executable memory. [The vDSO](../05-syscalls-and-the-boundary/the-vdso.md)

**VXLAN** — a virtual device carrying Layer 2 frames inside UDP between hosts, used to build overlay networks that span many machines. [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)

**Wait queue** — `struct wait_queue_head`, a list of tasks waiting on some event, each entry carrying its own wake function so a wakeup can mean "just one waiter" or "everyone," at no per-waiter polling cost while asleep. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**Wake affinity** — the set of heuristics deciding which CPU a waking task lands on, among the waker's CPU, the task's own previous CPU, or an idle CPU found by scanning the LLC domain; `WF_SYNC` biases placement toward the waker's CPU when the caller is about to sleep right after waking it. [SMP and Load Balancing](../07-scheduling/smp-load-balancing.md)

**Wakeup source** — An object recording that a device or event may wake the system or must keep it awake; visible in `/sys/kernel/debug/wakeup_sources`. [Power Management](../14-device-drivers-and-hardware/power-management.md)

**Watermark** — one of three per-zone thresholds (`min`, `low`, `high`) that turn remaining free memory into allocator behavior: above `high` nothing happens, crossing `low` wakes `kswapd`, and hitting `min` forces the allocating task into direct reclaim itself. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Whiteout** — the special file (a 0/0 character device) overlayfs creates in the upper layer to hide a lower-layer file that was deleted, since the lower layer itself cannot be changed. [overlayfs](../11-vfs-and-filesystems/overlayfs.md)

**Work item** — a function plus a `struct work_struct` embedded in the caller's own structure, recovered via `container_of` inside the callback; queuing one onto a workqueue hands it to a worker thread that runs it in process context. [Workqueues](../10-interrupts-time-and-deferred-work/workqueues.md)

**Workqueue** — a policy object (`struct workqueue_struct`) that hands queued work items to a pool of kernel-thread workers running in process context, where the callback may sleep, take a mutex, or allocate `GFP_KERNEL`; concurrency-managed workqueues draw workers from shared per-CPU pools on demand rather than dedicating a thread per queue. [Workqueues](../10-interrupts-time-and-deferred-work/workqueues.md)

**Write hole** — the RAID 5/6 window where a crash leaves a stripe's data and parity inconsistent, so a later rebuild silently produces wrong data. [RAID and Redundancy](../../computer-science/storage/raid-and-redundancy.md)

**Write-ahead log** — a record of intended changes written and made durable before the changes themselves, so recovery can redo or discard them after a crash. [Crash Consistency and Journaling](../../computer-science/storage/crash-consistency-and-journaling.md)

**Writeback** — the kernel-driven, deferred process — kthreads flushing pages once a dirty-memory or age limit is crossed — that moves dirty pages back to their filesystem; "later" is typically tens of seconds, not milliseconds. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**Write-intent bitmap** — an `md` record of which regions of an array had writes in flight, so a resync after a crash only checks those regions instead of the whole array. [Software RAID (md)](../12-block-layer-and-storage/software-raid.md)

**`xarray`** — an abstract, non-intrusive associative array: arbitrary pointers stored by a plain `unsigned long` index, with the implementation managing its own internal tree nodes and RCU-aware locking; the current, more general replacement for the older `radix_tree` API, and what the page cache is built on. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**XPS (Transmit Packet Steering)** — the mapping of CPUs to transmit queues, so each CPU sends on a queue it owns instead of contending for a shared one. [The Transmit Path](../13-networking-stack/the-transmit-path.md)

**Zero page (`empty_zero_page`)** — one physical page, filled with zeros, mapped read-only for the first *read* of any untouched anonymous page by every process on the system; only the first *write* actually allocates a private, real frame, which is why a large `calloc()` that's never fully written is nearly free. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Zombie** — a task past `exit_notify()`: its memory, files, and other resources are already released, and all that remains is a shrunken `task_struct` holding its PID and exit status for the parent's `wait()` to collect. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Zone** — a partition of physical memory (`ZONE_DMA`, `ZONE_DMA32`, `ZONE_NORMAL`, `ZONE_MOVABLE`, and 32-bit-only `ZONE_HIGHMEM`) so an allocation needing a restricted physical range asks the right pool instead of hoping; `DMA32` and `NORMAL` are what matter day to day on x86-64. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**zram** — a compressed block device used *as* the swap device itself (or any block device), with no backing device — once full, ordinary swap-full behavior applies, a hard ceiling rather than a degrade. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**zswap** — a compressed cache sitting in front of a real swap device; pages that don't fit the compressed pool write through to backing swap, so it degrades rather than hard-capping, at the cost of needing real swap configured underneath it. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)
