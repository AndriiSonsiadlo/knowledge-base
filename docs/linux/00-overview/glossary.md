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

Every term below links to the one page that owns and genuinely defines it, so "where did this come from" always has an answer. The list covers folders 00–10 so far and grows as later folders land — a term you expect but can't find here probably belongs to a page that hasn't been written yet.

**ABI (application binary interface)** — the binary-level contract a program compiles against; this section uses it specifically for the kernel's promise that it never breaks the *user-space* ABI (syscalls, `/proc`, ELF layout) across releases, even though it makes no such promise internally. [What Linux Actually Is](./what-linux-actually-is.md)

**Acquire and release** — the kernel's spelling of publish/subscribe ordering: `smp_store_release()` guarantees a store is visible only after every earlier access in program order, `smp_load_acquire()` guarantees a load happens before every later access; reach for this pair before a bare `smp_mb()` because it states exactly the ordering needed rather than a full fence in both directions. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**Address space (`address_space`)** — the per-inode structure that owns a cacheable file's folios: an `i_pages` XArray indexed by page-offset-within-file, plus the owning inode, the filesystem's `a_ops` callback table, folio count, and `gfp_mask`. [The Page Cache](../08-memory-management/the-page-cache.md)

**Autogroup** — a per-session grouping (on by default via `kernel.sched_autogroup_enabled`) that nests every task's fair-class scheduling entity inside its session's group rather than competing directly against every other task system-wide; the group, not the individual task, competes for CPU share, which is why renicing one process inside a crowded autogroup can appear to do nothing against unrelated work in another session. [Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**Barrier** — two independent reorderers exist and a fix for one is not a fix for the other: `barrier()` is a pure compiler directive with no emitted instruction, while `smp_mb()`/`smp_rmb()`/`smp_wmb()` constrain the CPU's own reordering and imply a compiler barrier too; on `CONFIG_SMP=n` every `smp_`-prefixed barrier degrades to a plain compiler barrier. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**`binfmt`** — the registered-handler chain (`struct linux_binfmt`, e.g. `binfmt_elf`, `binfmt_script`, `binfmt_misc`) that `execve()` asks, in turn, "is this file yours?" — the mechanism by which the kernel supports ELF, `#!` scripts, and user-registered formats without special-casing any of them. [`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**Bitmap** — a fixed-size set of small integers (CPU masks, IRQ masks, feature flags) stored as `unsigned long` words via `DECLARE_BITMAP`, manipulated with `set_bit()`/`clear_bit()`/`test_bit()`; the atomic variants like `test_and_set_bit()` are the default whenever more than one context might touch the same bitmap concurrently. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Boot loader** — the software that runs after firmware and before the kernel, whose entire job is four things: find a kernel, find an initramfs, build a command line, and hand over control. [Boot Loaders](../03-boot-and-init/bootloaders-grub-and-friends.md)

**Boot variable** — an NVRAM entry (`Boot0000`, `Boot0001`, …) plus a `BootOrder` list that tells UEFI firmware which `.efi` file to run and in what order; this state lives in firmware, not on disk. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Buddy allocator** — the page allocator's free-list structure within a zone, one list per order of 2ⁿ contiguous pages; splitting an order-*k*+1 block on allocation and coalescing two buddies (found by `buddy_pfn = pfn ^ (1 << order)`, no search needed) back together on free are its two governing operations. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**`bzImage`** — the actual bootable kernel file: real-mode setup code, a setup header, and a compressed payload that self-extracts on first run. "bz" stands for "big zImage," unrelated to the bzip2 algorithm. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Canonical address** — an x86-64 virtual address whose unimplemented high bits are a sign-extension of the top implemented bit (47, or 56 with 5-level paging); a non-canonical address is rejected by the CPU with `#GP` before translation even starts, which is why some bad pointers oops differently than others. [The Virtual Address Space](../08-memory-management/the-virtual-address-space.md)

**CBS (Constant Bandwidth Server)** — the live enforcement mechanism behind `SCHED_DEADLINE`: it tracks each deadline task's runtime budget as it consumes it and throttles the task the moment it overruns its declared runtime within the current period, containing a runaway deadline task with the same machinery that guarantees well-behaved ones their share. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**CFS (Completely Fair Scheduler)** — the fair-class algorithm that ran Linux from 2.6.23 (2007) until EEVDF began replacing it in 6.6; at the pinned v6.18 it is not the running scheduler, but its vocabulary (vruntime, the red-black tree, nice-to-weight) is preserved as the historical model EEVDF is a direct response to. [CFS and Virtual Runtime](../07-scheduling/cfs-and-vruntime.md)

**cgroup** — a directory in the cgroupfs virtual filesystem whose auto-populated files (`cpu.weight`, `memory.max`, `io.max`, `pids.max`, …) express resource limits; it answers "what can this process *use*," a question orthogonal to namespaces. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**Clock event device** — a programmable timer the kernel arms for a specific future moment and that then raises an interrupt at approximately that time, driving both the periodic tick and every one-shot timer; unlike a clocksource, it interrupts rather than merely being read. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**Clocksource** — a free-running hardware counter that only ever increases and is never itself an interrupt source; the kernel reads it and converts the reading to nanoseconds via a fixed-point `mult`/`shift` multiply, choosing among registered sources (TSC, HPET, ACPI PM timer, arm64's architected timer) by rating. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**`clone()` flags** — the single set of bits (`CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, and more) that decide, one `task_struct` pointer at a time, whether a new task shares or copies its parent's address space, filesystem context, file table, and signal handlers; `fork()`, `vfork()`, and `pthread_create()` are just three different flag words passed to the same `clone()`. [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**Compat syscall** — a syscall reached through a second, architecture-specific syscall table (e.g. the 32-bit `syscall_32.tbl` a 64-bit kernel also carries) plus `compat_` translation functions and structs, needed because pointers, `long`s, and struct layouts differ in width between a 32-bit caller and the kernel's native 64-bit types. [ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md)

**Compaction** — active defragmentation: migrating movable pages out of a region to consolidate scattered free order-0 pages into the higher-order contiguous blocks a THP or other high-order allocation needs, the mirror image of what the buddy allocator does on free. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Compound page** — the pre-folio name for a multi-page allocation from the buddy allocator: an order-*n* block with a **head** page carrying the real metadata and every **tail** page pointing back at it via `compound_head`, an arrangement that left every function taking a `struct page *` responsible for checking which kind it had. [Folios and Compound Pages](../08-memory-management/folios-and-compound-pages.md)

**`container_of`** — a macro that recovers a pointer to a containing struct from a pointer to one of its embedded fields, by subtracting that field's compile-time offset and casting the result to the containing type. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**Context switch** — the three-stage handoff between tasks: `__schedule` picks the next task (cheap bookkeeping), `context_switch` swaps the address space only if it changed, and `switch_to` swaps register state unconditionally; the nameable direct cost is small, and the real expense is the unnamed indirect cost paid afterward by the incoming task's cold caches and TLB. [The Context Switch](../07-scheduling/the-context-switch.md)

**Copy-on-write** — the mechanism that makes `fork()` cheap: both parent and child page tables point at the same physical pages, marked read-only, and the kernel copies a page only at the moment either side actually writes to it. [`fork()` and Copy-on-Write](../06-processes-and-threads/fork-and-copy-on-write.md)

**`cpu.max`** — the cgroup v2 hard CPU cap: a quota of microseconds a group may consume out of every period, written as `"$MAX $PERIOD"` (default `"max 100000"`, i.e. no cap). Hitting the quota does not slow the group down — it stops it dead for the rest of the period, turning a CPU limit into a latency problem. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**`cpu.weight`** — the cgroup v2 proportional CPU control (replacing v1's `cpu.shares`), a value in [1, 10000], default 100; it only changes the outcome when the CPU is contended — a low-weight group still gets the whole CPU to itself if nothing else wants it, because the mechanism is work-conserving. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**`struct cred`** — the separately allocated, refcounted, and immutable-once-published object holding a task's user/group IDs and capability sets; `task_struct` holds two pointers to it (`cred`, `real_cred`) rather than the fields themselves, and changing credentials means installing a whole new object, never editing one in place. [Credentials and Identity](../06-processes-and-threads/credentials-and-identity.md)

**`current`** — the currently running task on a given CPU, resolved via a per-CPU variable populated by `current_task`, not (on x86-64) by masking the stack pointer as older documentation describes. [`task_struct`: The Anatomy of a Task](../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md)

**D state** — the `ps` letter for `TASK_UNINTERRUPTIBLE`; because signal delivery only happens on the return to user space and a `D`-state task never reaches that checkpoint, not even `SIGKILL` can act on it until the underlying wait completes. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**`defconfig`** — the `make defconfig` target that produces a sane, complete `.config` close to what a real distribution ships; the usual starting point before hand-tuning debug options. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Demand paging** — the policy that `mmap()` creates a VMA and maps no physical pages at all; only a fault — a first read (the zero page) or first write (a fresh zeroed frame) — actually costs physical memory, so address space is issued freely on the promise most of it is never touched. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Direct map** — the kernel address-space region holding a permanent virtual address for every physical page of installed RAM, at a fixed offset from its physical address; this linear-by-construction mapping is what makes `virt_to_phys()`/`phys_to_virt()` plain arithmetic instead of a page-table walk. [The Virtual Address Space](../08-memory-management/the-virtual-address-space.md)

**Direct reclaim** — reclaim run synchronously, on the allocating task's own time, triggered when a zone crosses its **min** watermark; unlike `kswapd`'s background work, this is a latency event with an unbounded tail because the allocating thread is now doing reclaim instead of its own work. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**Dirty page** — a page-cache page holding data that has been modified in RAM but not yet written back to its backing device. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**Distribution** — a specific packaging of the kernel plus a userland (C library, init system, package manager, patch set, and kernel configuration), with its own name, release cadence, and support policy. [What Linux Actually Is](./what-linux-actually-is.md)

**Dynticks** (`CONFIG_NO_HZ_IDLE`) — stops the periodic tick on a CPU that has gone idle with nothing due soon, reprogramming the clock event device as a one-shot event for the actual next expiry instead of polling at a fixed rate; `nohz_full` extends the same idea to a busy CPU with exactly one runnable task. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**EEVDF (Earliest Eligible Virtual Deadline First)** — the fair-class scheduler actually running at v6.18, replacing CFS beginning in kernel 6.6 and becoming the default in 6.12. It separates the two questions CFS's single `nice` knob conflated — how much CPU a task deserves (still weight, from nice) and how promptly it should run (a per-task request size) — selecting among eligible tasks by earliest virtual deadline instead of comparing vruntime directly. [EEVDF](../07-scheduling/eevdf.md)

**`EFAULT`** — the negative-errno value a copy routine's caller returns when `copy_from_user`/`copy_to_user` reports a nonzero, uncopied remainder, produced when the exception table's fixup redirects execution away from a user-memory access that faulted rather than letting it become a kernel oops. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**Eligibility** — under EEVDF, a task is eligible exactly when its lag is non-negative (its vruntime is at or behind the runqueue's average virtual time `V`); only eligible tasks are candidates for selection at all, regardless of how early their virtual deadline would otherwise be. [EEVDF](../07-scheduling/eevdf.md)

**`ERESTARTSYS`** — an internal-only return value a blocking syscall hands back when a signal interrupts it, never seen by user space: the kernel either rewinds `pt_regs->ip` to re-execute the `SYSCALL` instruction (if the handler was installed with `SA_RESTART`) or converts it to the `-EINTR` user space actually observes. [Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**`ERR_PTR`** — a function that encodes a negative `errno` value as a pointer, exploiting the fact that the top few thousand bytes of kernel address space are never a valid allocation, so the encoded value is unambiguously distinguishable from a real pointer. [Error Handling](../04-kernel-architecture-and-idioms/error-handling-idioms.md)

**ESP (EFI System Partition)** — a FAT32 partition that UEFI firmware can read directly, holding `.efi` boot loader files; it replaces the MBR's chainloading trick that legacy BIOS relies on. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Exception table** — a table of `(instruction, fixup)` offset pairs (`struct exception_table_entry`) that lets a page fault on a deliberate `copy_from_user`/`copy_to_user` access be redirected to fixup code returning an error, instead of being treated as the kernel bug an unprotected fault normally is. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**`EXPORT_SYMBOL_GPL`** — the macro placed after a kernel function's definition that makes it callable from a module whose declared license the kernel recognizes as GPL-compatible; the plain `EXPORT_SYMBOL` allows any module regardless of license. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**First touch** — the rule that a virtual address owns no physical memory until something faults it in; on a NUMA machine the same fault also decides node placement, since the allocator asks the faulting CPU's own node first, which is why a single thread that initializes a shared array pins the whole array to one node. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Folio (`struct folio`)** — a type guaranteed to be a head page (or a trivially-its-own-head order-0 page), overlaying the same `struct page` array memory rather than adding a second structure; the guarantee is enforced by the type system, not by a runtime check every caller used to have to redo. [Folios and Compound Pages](../08-memory-management/folios-and-compound-pages.md)

**Freestanding C** — a C implementation with no operating system underneath it to supply a standard library, a `main()` entry point, or a heap; the kernel supplies its own equivalents of everything (`printk`, `kmalloc`, its own boot entry) because it *is* the OS. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**`fsync`** — a call guaranteeing that, on success, a file's data and the metadata needed to find it have been handed to the device with a cache-flush/`FUA` request; it says nothing about the containing directory's own entry, which needs its own `fsync` on the directory file descriptor. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**GFP flags** — the bits passed to an allocation request that state what the allocator is *permitted* to do on the caller's behalf (sleep, run direct reclaim, issue I/O, call back into a filesystem) — a permission grant, not a performance knob — with `GFP_KERNEL`, `GFP_ATOMIC`, `GFP_NOWAIT`, `GFP_NOFS`, and `GFP_NOIO` each forbidding a different subset for a different calling context. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Grace period** — an interval during which every CPU has passed through at least one quiescent state; once a grace period that started after a writer's update has elapsed, every reader that could have observed the old version is guaranteed to have finished, and only then may the old version be reclaimed. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**GRO (Generic Receive Offload)** — merges several related small segments arriving close together (e.g. TCP segments from the same stream) into one larger `sk_buff` before the packet climbs further up the stack, trading a small merge cost for large savings in per-header processing. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**Hard IRQ context** — the context a hardware interrupt handler runs in, borrowing whatever task happened to be running with no task identity of its own; every prohibition (no sleeping, no mutex, no `GFP_KERNEL`, no `copy_to_user`) follows from that one fact. [Hard IRQ Context and Its Rules](../10-interrupts-time-and-deferred-work/hardirq-context.md)

**`hlist`** — `hlist_head`/`hlist_node`, `list_head`'s sibling for hash tables: a single-pointer head (rather than `list_head`'s two) keeps millions of empty buckets cheap, with the node side carrying `pprev` — a pointer to the previous node's `next` field — so removal can splice a node out without walking the list. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**hrtimer** — a timer ordered in a red-black tree keyed on absolute expiry time, feeding a programmable clock event device armed for exactly its leftmost (soonest) node; used when a deadline must actually be met, at the cost of O(log n) insertion against the timer wheel's O(1). [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**Huge page** — a page-table walk that stops one or two levels early because a PMD or PUD entry's page-size bit is set, mapping the entire 2 MiB (PMD) or 1 GiB (PUD) region that level's fan-out would otherwise have covered through a whole subtree of tables. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**hugetlbfs** — the explicit, reserved huge-page mechanism: an administrator or application pre-allocates a pool of huge pages (at boot or via `nr_hugepages`) that is taken out of the general page allocator entirely — never reclaimed, never swapped, never silently given back — and applications opt in by name via `MAP_HUGETLB` or a file on a `hugetlbfs` mount. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**`HZ`** — the build-time constant (100, 250, 300, or 1000) setting how many times a second the periodic tick fires on a CPU that has not stopped it; it still governs how often the tick's timer-expiry and accounting jobs run, but no longer determines the scheduler's own fairness granularity. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**`idr`/`ida`** — the kernel's "give me the smallest unused integer, and let me give it back later" allocators; `idr` maps a small integer to a pointer (file descriptors, device minor numbers), while `ida` is the same machinery with no pointer attached, just an ID allocator. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**`__init`** — an annotation placing a function in a discardable code section whose memory is freed once boot completes; calling it later dereferences freed memory. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Initcall** — a function pointer a built-in driver or subsystem registers into a named linker section at build time, which the kernel walks and calls at the appropriate point in boot rather than being invoked by name from `start_kernel()`. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initcall level** — one of nine ordered phases (`early`, `pure`, `core`, `postcore`, `arch`, `subsys`, `fs`, `device`, `late`) that group initcalls; a driver can pick its level, but not an ordering relative to other drivers within it. [`start_kernel` and the Initcall Order](../03-boot-and-init/start-kernel-and-initcalls.md)

**Initramfs** (build sense) — a gzip-compressed `cpio` archive the kernel unpacks directly into an in-memory `tmpfs` mounted as `/`, before any real block device or filesystem driver is touched; the kernel then executes `/init` from it as PID 1. [A Minimal Root Filesystem](../01-lab-and-toolchain/a-minimal-rootfs.md)

**Intrusive list** — a container design where the link field that makes an object a list member lives inside the object's own struct rather than in a separately allocated node, costing no extra allocation on insert at the price of baking list membership into the object's type. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**IRQ affinity** — the CPU (or set of CPUs) an interrupt is permitted (`smp_affinity`) and actually delivered to (`effective_affinity`); keeping an interrupt, the softirq it raises, and the task consuming the data on the same CPU avoids cross-CPU cache traffic on every occurrence. [Interrupt Affinity](../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md)

**`irq_chip`** — the vtable (`irq_mask`, `irq_unmask`, `irq_ack`, `irq_eoi`, `irq_set_affinity`) that makes an I/O APIC and a GIC interchangeable to every layer of generic IRQ code above it. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**`irq_desc`** — one struct per Linux IRQ number, tying together the chip, the flow handler, the registered-handler action chain, per-CPU statistics, and the lock serializing all of it. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**irq domain** — the object that maps a controller-local hardware number (`hwirq`) to a Linux IRQ number, needed because nested controllers each describe an interrupt only in their own local numbering; the number in `/proc/interrupts` is allocated at probe time through this mapping, not fixed by the hardware. [The IRQ Subsystem](../10-interrupts-time-and-deferred-work/the-irq-subsystem.md)

**IRQ number versus vector** — two different numbers for the same event: the hardware vector is the IDT index the interrupt controller told the CPU to use, while the Linux IRQ number is the software identifier assigned by an irq domain that `/proc/interrupts`, `request_irq()`, and every driver actually deal in. [How an Interrupt Reaches the Kernel](../10-interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel.md)

**`IRQF_ONESHOT`** — the `request_threaded_irq()` flag that keeps a level-triggered line masked until the thread function itself finishes, not just until the primary handler returns; omitting it on a threaded handler for a level-triggered line produces an interrupt storm. [Threaded IRQs](../10-interrupts-time-and-deferred-work/threaded-irqs.md)

**`irqsave`** — the `spin_lock_irqsave()`/`spin_unlock_irqrestore()` pair, which saves the CPU's current interrupt-enabled state and restores exactly that on unlock rather than assuming interrupts were on; the safe default whenever a caller can't prove the prior interrupt state, since an unconditional `spin_lock_irq()` would wrongly re-enable interrupts that were already off. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**`jiffies`** — the global counter the periodic tick increments, wrapping as an `unsigned long`; kernel code compares two values with `time_after()`/`time_before()` rather than `<`/`>` specifically because a direct comparison breaks at the wraparound. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**Journal** — systemd's structured log store, where each entry is a set of key-value fields rather than a text line, letting it be filtered by unit, boot, or priority as a query; whether a previous boot's log survives depends on the `Storage=` setting. [systemd in Practice, and Debugging a Broken Boot](../03-boot-and-init/systemd-in-practice-and-boot-debugging.md)

**KASAN** — the Kernel Address Sanitizer, which instruments every memory access to catch use-after-free and out-of-bounds reads/writes at the exact faulting instruction, by poisoning freed and redzone memory and checking accesses against it. [What Goes Wrong in Kernel C](../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md)

**KASLR** — kernel address space layout randomisation; the decompressor picks a randomised physical load address at every boot, and relocation logic in `extract_kernel()` plus fixups in the kernel's own `startup_64` make a kernel built for one address run correctly wherever it lands. Booting with `nokaslr` disables this, loading the kernel at its link-time address instead — which is also why a GDB session's symbol table only matches a running kernel with KASLR off. [Early Boot and Architecture Setup](../03-boot-and-init/early-boot-and-arch-setup.md)

**Kconfig symbol** — a named configuration option declared by a `config` entry in a `Kconfig` file, with a type, dependency rules, a default, and help text, that governs whether a piece of code is compiled into the kernel at all. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**KCSAN** — the Kernel Concurrency Sanitizer, a sampling-based data-race detector that instruments ordinary loads and stores and reports a concurrent, unsynchronized access to the same memory where at least one side is a write, naming both racing accesses. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Kernel** — the single upstream Linux project: one source tree, one `git` history, one maintainer chain, releasing on a roughly nine-week cadence — distinct from any distribution's userland or packaging around it. [What Linux Actually Is](./what-linux-actually-is.md)

**Kernel command line** — the text handed to the kernel at the moment of handoff (via the setup header's `cmd_line_ptr`), the only channel for changing kernel behavior before any user space exists. [The Kernel Command Line](../03-boot-and-init/the-kernel-command-line.md)

**Kernel thread** — a schedulable kernel-code entity with no user process to be charged to (visible via `ps` in square brackets, e.g. `[kworker/0:1]`), forked from `kthreadd`, distinct from kernel code that runs inside a process's own context. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**`kfifo`** — the kernel's ready-made single-producer/single-consumer lock-free ring buffer; its own header documentation is explicit that it is lockless only in the strict SPSC case, and a second producer or consumer requires an explicit spinlock (`kfifo_in_spinlocked()`/`kfifo_out_spinlocked()`). [Lock-Free Patterns](../09-concurrency-and-locking/lock-free-and-ring-buffers.md)

**`kobject`** — the generic, embeddable unit that participates in the kernel's object graph: a name, a reference count, a parent pointer, and a pointer to its type; never allocated standalone, always embedded inside a larger structure. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`kref`** — a thin standard wrapper around a `refcount_t` plus the convention of pairing it with a release callback; `kref_put` invokes the release function exactly once, when the count it decrements reaches zero. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**`kset`** — a collection of `kobject`s that is itself a `kobject` (it embeds one), giving a group of objects its own place — and its own directory — in the object graph sysfs renders. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`ksoftirqd`** — a per-CPU kernel thread, one per online CPU, that runs softirq work the interrupt-exit path's budget could not finish; seeing it at the top of `top` means a CPU's deferred-work load exceeds what one pass can absorb, not that the softirq mechanism is broken. [Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**`ktype` (`kobj_type`)** — the behavior attached to a `kobject` — its release function and its attribute (`show`/`store`) operations — shared by every `kobject` of a given kind. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**`kswapd`** — a per-node kernel thread woken when a zone drops below its **low** watermark, reclaiming memory in the background while allocations continue to be satisfied from whatever's still available; the healthy counterpart to direct reclaim. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**Lag** — under EEVDF, the gap between the CPU service a task should have received under ideal weighted-fair sharing and what it actually has: `weight × (V − vruntime)`. Positive lag means the task is owed time and is eligible to run; negative lag means it has run ahead of its share and must wait for `V` to catch up. [EEVDF](../07-scheduling/eevdf.md)

**`list_head`** — the kernel's circular, doubly-linked intrusive list node/head type (two pointers, `next` and `prev`), embedded directly as a field inside the objects it links. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**`local_lock`** — a lock type that compiles to nothing but `preempt_disable()`/`preempt_enable()` (or the IRQ-disabling equivalents) on a non-`PREEMPT_RT` kernel, and to a real per-CPU lock under `PREEMPT_RT`, so the same source line means "disable preemption" on one configuration and "take a lock" on the other. [Per-CPU Data](../09-concurrency-and-locking/per-cpu-data.md)

**Lock class** — what `lockdep` actually tracks: not individual lock instances but classes, by default one per initialization call site, so the deadlock-cycle graph is a statement about which *kinds* of lock nest inside which, not which specific instances did. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Lockdep** — a runtime validator that builds a graph of lock acquisition ordering as the kernel actually runs and reports the first sequence that could deadlock, even before that exact sequence has actually occurred. [Finding Locking Bugs](../09-concurrency-and-locking/finding-locking-bugs.md)

**Lockdown** (`CONFIG_SECURITY_LOCKDOWN_LSM`) — closes the ways an already-signature-verified, running kernel could still be made to execute unsigned code or expose kernel memory; its `integrity` mode forbids modifying the running kernel, and `confidentiality` additionally forbids reading kernel memory or secrets, which is why `nokaslr` and kernel debugging stop working once it's active. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**LRU (lists)** — the classic reclaim scheme: per-`lruvec` active and inactive lists, split further by anonymous versus file-backed (five `lru_list` types in total), where a page found re-referenced while on the inactive list gets a second chance onto the active list instead of being evicted outright. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**LTS (long-term support)** — a designation given to a subset of kernel releases for which the community keeps backporting fixes for years after an ordinary release would have been abandoned. [What Linux Actually Is](./what-linux-actually-is.md)

**Maple tree** — the B-tree-like structure (`mm_mt`) an `mm_struct` uses to index its VMAs at v6.18, replacing the older rbtree-plus-linked-list scheme; it supports RCU-safe, lock-free lookups, and `vma->vm_next` no longer exists as a field. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**`MemAvailable`** — `/proc/meminfo`'s estimate of memory a new process could actually get without swapping: free memory plus the portion of cache that's cheaply reclaimable; the number to read instead of `MemFree`, which counts none of the reclaimable cache. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**Memory ordering** — a plain, unadorned access gives the compiler license to merge, split, invent, or hoist it, and the CPU separately reorders at run time through its store-buffer and speculation machinery; `READ_ONCE()`/`WRITE_ONCE()` close the compiler half and the `smp_*` barrier family closes the CPU half, and the two must be reasoned about separately. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**mempolicy (`struct mempolicy`)** — the kernel structure recording which policy (default, bind, preferred, interleave, or weighted interleave) governs which node(s) a fault may draw a frame from, settable per-task (`set_mempolicy`), per-VMA (`mbind`), and bounded underneath both by a cpuset's node set. [NUMA and Memory Policy](../08-memory-management/numa-and-memory-policy.md)

**MGLRU (multi-generational LRU)** — an alternative reclaim implementation organizing pages into generations aged by scanning page-table accessed bits directly rather than the classic two-list scheme's reference-on-fault/reference-on-scan signal; it is a compile-time option (`CONFIG_LRU_GEN`) with no `default y`, not something every kernel ships active. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**`mmap_lock`** — the per-`mm` reader-writer semaphore serializing structural changes to the VMA collection (insert/remove/split/merge); at v6.18 per-VMA locking (`CONFIG_PER_VMA_LOCK`, default on) lets the page-fault fast path take a lock on just the faulted VMA instead, falling back to `mmap_lock` only when that path can't proceed. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**`mm_struct`** — the one-per-address-space structure every thread of a multi-threaded process shares, carrying the VMA collection, the top-level page-table pointer, and layout fields; its lifetime is split across two reference counts, `mm_users` (userspace/semantic references) and `mm_count` (the allocation itself), specifically so a lazy-TLB kernel thread can hold the struct without keeping the address space alive. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**Module** — relocatable object code linked into an already-running kernel at load time instead of build time, running with exactly the same privileges as code compiled into `vmlinux`. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**Modversions** — a build-time mechanism (`CONFIG_MODVERSIONS`) that computes a CRC over each exported symbol's type signature and checks it at module-load time, refusing to load a module whose recorded CRC no longer matches the running kernel's. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**Monolithic kernel** — a kernel design where every subsystem runs in one address space at one privilege level, calling each other through ordinary function calls with no isolation boundary between them; drivers can still be compiled in or loaded as modules. [Monolithic, With Modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)

**MSI-X** — a PCIe device signals an interrupt by writing a specific data value to a specific address rather than asserting a physical line; MSI-X is the larger, more flexible per-device table of these write-triggered vectors, which is what makes one interrupt vector per hardware queue per core a real configuration. [Interrupt Controllers](../../computer-science/buses-and-io/interrupt-controllers.md)

**`MSR_LSTAR`** — the model-specific register holding the address the kernel registered at boot as the `SYSCALL` entry point; the CPU loads `RIP` from it as the first of the five hardwired steps `SYSCALL` performs on x86-64. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**Mutex** — a sleeping lock that spins first (optimistic spinning) before falling back to sleep, tracks a single owner, and — unlike a spinlock — may be held across anything that can block; for a short critical section a contended mutex costs close to what a contended spinlock costs. [Mutexes and Semaphores](../09-concurrency-and-locking/mutexes-and-semaphores.md)

**Namespace** — a kernel mechanism that changes what a process can *see* (which processes, network devices, hostname, IPC objects, etc. are visible or enumerable) without affecting what resources it's allowed to *use*; created via `CLONE_NEW*` flags to `clone()`. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**NAPI** — the receive-path model where a hardware interrupt only schedules polling rather than processing the packet itself; under light load it behaves like one interrupt per packet, but under heavy load the queue's interrupts are disabled and a poll loop drains it instead, bounding interrupt cost. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**`need_resched`** — at v6.18, `TIF_NEED_RESCHED`, a per-task bit in `struct thread_info::flags` set when a higher-priority task becomes runnable; a reschedule happens only once this flag is set *and* `preempt_count` is zero, at a point the kernel actually checks. x86-64 adds a second, weaker `TIF_NEED_RESCHED_LAZY` for `PREEMPT_LAZY`. [Preemption Models](../07-scheduling/preemption-models.md)

**Negative errno** — the kernel's actual failure convention: a syscall handler returns a small negative number (e.g. `-ENOENT`) directly as its return value instead of setting a side-channel `errno`, which the kernel has no variable for at all; a value from `0` up to `-MAX_ERRNO - 1` is success, everything from `-MAX_ERRNO` to `-1` is an error. [Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**Nice weight** — the value `nice` actually changes: `sched_prio_to_weight[]` maps a nice level to a weight (`sched_entity.load.weight`) that scales how fast a task's vruntime advances and how its EEVDF virtual deadline is projected. Each nice step is a fixed ~1.25× geometric ratio, so a nice difference buys a constant *percentage* change in CPU share, not a fixed amount. [Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**`nohz_full`** — the boot parameter marking specific CPUs as adaptive-tick, stopping the periodic tick on a busy CPU once it has exactly one runnable task; it requires at least one housekeeping CPU and RCU callback offloading (`rcu_nocbs`), and is one part of a CPU-isolation configuration, not a standalone flag. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**`offsetof`** — a compile-time constant giving the byte offset of a named field within its struct type, with no runtime cost; it is the arithmetic building block `container_of` is built on. [`container_of` and Embedded Structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)

**OOM score** — the per-task badness value `oom_badness()` computes (RSS plus swapped-out memory plus page-table memory, shifted by `oom_score_adj`) and exposes read-only at `/proc/PID/oom_score`; it measures who freeing would help most, not who is at fault. [The OOM Killer](../08-memory-management/the-oom-killer.md)

**Optimistic spinning** — a contended mutex's first response: check whether the recorded owner is currently running on some CPU and, if so, spin (via an MCS queue) on the reasoning that a running owner will likely finish soon, only falling back to a real sleep once the owner is observed descheduled or the spin otherwise fails. [Mutexes and Semaphores](../09-concurrency-and-locking/mutexes-and-semaphores.md)

**Ordering versus requirement** — in systemd, `Requires=` and `After=` are independent axes: `Requires=` says what else must start as a dependency, `After=` says only which of two already-starting units goes first; declaring one does not imply the other. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**overlayfs** — the filesystem that merges a stack of read-only layers plus one writable layer into what looks like a single ordinary filesystem; a read resolves top-down through the layers, and writing a file that only exists in a lower layer copies it into the writable layer first. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**Overcommit** — the kernel's policy for how strictly it enforces "can I back everything I've promised" at allocation time rather than fault time, controlled by `vm.overcommit_memory` (0 heuristic, 1 always, 2 strict against `swap + RAM × overcommit_ratio`); a successful `malloc()` under modes 0/1 is a promise the kernel may not be able to keep in full. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Page table level** — one of the fixed stages a virtual-address walk passes through (PGD, PUD, PMD, PTE on x86-64, with a generic `p4d_t` level that folds away to a no-op on a 4-level configuration), each level a 9-bit index into one 4 KiB table of 512 entries. [Page Tables and the Walk](../08-memory-management/page-tables-and-the-walk.md)

**Page cache** — the in-RAM cache of file-backed pages that ordinary buffered I/O goes through; a `write()` copies bytes into page-cache pages and marks them dirty rather than touching the device immediately, so the data can exist only in RAM at the moment the call returns. [The Page Cache](../08-memory-management/the-page-cache.md)

**Page fault** (minor/major) — a CPU exception raised when an instruction touches a virtual address with no valid page-table entry; "minor" means the kernel resolved it without I/O (zero page, page-cache hit, copy-on-write copy), "major" means it had to block on a device (disk read or swap-in). [The Page Fault Handler](../08-memory-management/the-page-fault-handler.md)

**PCID (Process-Context Identifier)** — a hardware TLB tag letting entries from more than one address space coexist without a full flush on every switch; Linux recycles a small pool of PCIDs as ASIDs across recently-used `mm`s per CPU, and it is the concrete reason KPTI's per-syscall cost varies so much between machines with and without PCID support. [The TLB and Address-Space Switching](../08-memory-management/tlb-and-address-space-switching.md)

**Pending signal** — the state between a signal's generation (a bit set in `struct sigpending`) and its delivery at the next return to user space; a signal can be pending indefinitely if the target never reaches that checkpoint. [Signals](../06-processes-and-threads/signals.md)

**Per-CPU data** — the strategy that beats every lock by eliminating sharing rather than protecting it: give each CPU its own copy via `this_cpu_*`/`per_cpu()`, so there is no cache-line bouncing and nothing to combine except when a caller actually needs the aggregate total. [Per-CPU Data](../09-concurrency-and-locking/per-cpu-data.md)

**`pick_next_task`** — the function (`kernel/sched/core.c`) that walks the scheduling classes from highest to lowest priority and takes the first task offered, with a fast path that skips straight to `pick_next_task_fair()` whenever every runnable task on the runqueue already belongs to the fair class. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**PID 1** — the first user-space process, distinguished from every other process only by having no parent, which is the single cause behind its special signal handling, orphan-reaping duty, and the kernel panic that follows if it ever exits. [`switch_root` and PID 1](../03-boot-and-init/switch-root-and-pid-1.md)

**`pivot_root`** — the call that moves a *mount namespace's* root to another directory already mounted within it, changing what an absolute path resolves through for every process sharing that namespace; distinct from `chroot`, which changes only the calling *process's* idea of `/` — a per-process attribute, not a mount-namespace-wide change. [The Life of a Container](../02-guided-traces/the-life-of-a-container.md)

**`PR_SET_CHILD_SUBREAPER`** — a `prctl(2)` flag letting any process opt in to reaping orphans from its own descendant tree, instead of every orphan reparenting all the way up to PID 1; it's the mechanism container supervisors like `tini` and `dumb-init` rely on. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**`preempt_count`** — a per-CPU counter incremented by taking a spinlock, entering interrupt or softirq context, or an explicit `preempt_disable()`; a reschedule is legal only when it is exactly zero, regardless of what `need_resched` says. [Preemption Models](../07-scheduling/preemption-models.md)

**Preemption model** — the kernel-wide policy for whether kernel-mode execution may be interrupted for scheduling before it finishes voluntarily; v6.18 offers four (`PREEMPT_NONE`, `PREEMPT_VOLUNTARY`, `PREEMPT`, `PREEMPT_LAZY`) plus `PREEMPT_RT` layered independently on top, trading worst-case latency against throughput. [Preemption Models](../07-scheduling/preemption-models.md)

**PSI (Pressure Stall Information)** — the fraction of recent wall-clock time tasks in some scope spent runnable-but-waiting for a resource (`some`: at least one task waiting; `full`: every task waiting simultaneously), reported over 10/60/300-second windows; it measures lost time directly, which is why it distinguishes an overloaded machine from a busy-but-unblocked one in a way plain utilisation or load average cannot. [Diagnosing Scheduling Latency](../07-scheduling/diagnosing-scheduling-latency.md)

**PSS (proportional set size)** — resident pages divided by their number of sharers, summed per process; the only one of the four per-process memory metrics (VSZ, RSS, PSS, USS) that sums correctly across processes into a true total, which RSS explicitly does not. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**`pt_regs`** — the fixed-layout struct the syscall entry stub builds on the kernel stack from the registers `SYSCALL` didn't save itself (`ss`, old `rsp`, `rflags`, `cs`, old `rip`, syscall number, then the general-purpose registers), giving every syscall handler, tracer, and oops dump the same byte-for-byte way to find a caller's register state. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**`PT_INTERP`** — the ELF program header naming the dynamic linker's path; when present, `load_elf_binary()` maps that second binary into the new address space and jumps to *its* entry point first, not the program's own. [`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**PTE** — the leaf page-table entry; its present, read/write, user/supervisor, accessed, dirty, and NX bits are what copy-on-write, permission faults, the approximate-LRU accessed-bit scheme, and W^X hardening are each built directly out of. [Page Tables and the Walk](../08-memory-management/page-tables-and-the-walk.md)

**QEMU gdbstub** (`-s -S`) — `-s` opens a GDB stub listening on TCP port 1234 exposing the guest's virtual CPU; `-S` freezes the guest at its first instruction until GDB tells it to continue, letting GDB drive the CPU directly regardless of whether guest software is responsive. [Debugging the Kernel with GDB](../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md)

**Queued spinlock** — the kernel's actual `spinlock_t` implementation (`struct qspinlock`, MCS-lock-derived): each waiter beyond the first queues on its own per-CPU node instead of the shared lock word, turning contention into a fair FIFO instead of a cache-line-bouncing free-for-all. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**Quiescent state** — a moment at which a given CPU is provably not in the middle of an RCU read-side critical section (a context switch, a return to user space, going idle); detecting one costs nothing extra because it rides on events the kernel already produces for other reasons. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**`raw_spinlock_t`** — the spinlock type exempted from `PREEMPT_RT`'s transformation of ordinary `spinlock_t` into a sleeping, priority-inheriting `rt_mutex`; it stays a genuine non-sleeping, non-preemptible spinlock on every configuration, which is why scheduler internals and interrupt-core code use it explicitly. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**RCU (Read-Copy-Update)** — a synchronization scheme where readers take no lock, write no shared state, and are never blocked by a writer; a writer instead builds an entire new version, publishes it with one pointer store, and defers reclaiming the old version until every reader that could still hold it has finished. [RCU: The Idea](../09-concurrency-and-locking/rcu-the-idea.md)

**`rcu_dereference`** — the RCU-specific acquire-paired pointer read: fetches a pointer with the dependency-ordering guarantee that a reader can safely follow it into newly-published data, and is only valid inside a read-side critical section (or, on the update side under the writer's own lock, via `rcu_dereference_protected()` instead). [RCU in Practice](../09-concurrency-and-locking/rcu-in-practice.md)

**`READ_ONCE`** (and `WRITE_ONCE`) — a genuine single load or store via a `volatile` cast that forbids the compiler from merging, splitting, inventing, or hoisting the access; it says nothing about ordering relative to other variables and nothing to the CPU about store-buffer visibility, so it solves only the compiler half of the ordering problem. [Memory Ordering and Barriers](../09-concurrency-and-locking/memory-ordering-and-barriers.md)

**Readahead** — detection of a sequential access pattern that triggers large asynchronous reads ahead of where a caller currently is, so the folios covering the next offset are usually already resident by the time `read()` reaches them; a pattern that starts sequential and then jumps randomly defeats it as **read amplification**, I/O issued for data never consumed. [The Page Cache](../08-memory-management/the-page-cache.md)

**Real-time signal** — a signal in `SIGRTMIN`–`SIGRTMAX` that, unlike a standard signal, genuinely queues (multiple pending instances are each delivered) and can carry an integer or pointer value via `sigqueue()`. [Signals](../06-processes-and-threads/signals.md)

**Red-black tree** (`rb_node`/`rb_root`) — the kernel's balanced binary search tree, embedded intrusively like `list_head`; the kernel's rbtree code owns balancing (`rb_insert_color()`, `rb_erase()`) while the caller writes the comparison and walk logic itself, avoiding a per-comparison indirect call. The CFS scheduler's runqueue is the canonical example. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**`refcount_t`** — a dedicated reference-counting type (distinct from `atomic_t`) that saturates instead of wrapping on overflow and refuses to increment from zero, closing two failure modes a plain atomic counter has when used as an object's lifetime counter. [Reference Counting and Object Lifetime](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md)

**Refault** — a page reclaimed and then read back almost immediately, costing the reclaim work for zero net memory saved; it is the direct, measurable signal (`workingset_refault_file`/`_anon`) that the working set no longer fits available memory, distinguishing healthy reclaim from thrashing. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**Reparenting** — what happens to a task's children when it dies first: `forget_original_parent()` hands each one to the nearest subreaper ancestor, or to PID 1 of its PID namespace if none exists. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Request size (slice)** — a task's declared amount of CPU per turn under EEVDF (`sched_entity.slice`), defaulting to `sysctl_sched_base_slice` (0.7ms) but settable per-task via `sched_setattr()`'s `sched_runtime` field (clamped to 0.1–100ms). A smaller request size earns an earlier virtual deadline and therefore more prompt scheduling, entirely independent of the task's weight or aggregate CPU share. [EEVDF](../07-scheduling/eevdf.md)

**rootfs** — the always-present `tmpfs`-family filesystem the kernel mounts at `/` before anything else exists, whether or not an initramfs archive is ever unpacked into it. [initramfs and Early User Space](../03-boot-and-init/initramfs-and-early-userspace.md)

**RSS (resident set size)** — physical pages currently resident and mapped into a process's page tables; it double-counts, since a page shared with N other processes counts fully in every one of their RSS, which is why summing RSS across a forked worker pool can overstate real memory use by several times. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**RT throttling** — the safety valve bounding `SCHED_FIFO`/`SCHED_RR` tasks, which have no deadline-style budget of their own: by default the real-time class as a whole may consume only `sched_rt_runtime_us` out of every `sched_rt_period_us` (95% by default), guaranteeing the remaining 5% to non-RT tasks; when the throttle triggers, the RT class simply stops running for the rest of the period. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**Runqueue** — `struct rq`, one per CPU, the lock-protected container holding a sub-runqueue per scheduling class (`cfs`, `rt`, `dl`, and `scx` when enabled) plus cross-class bookkeeping (`nr_running`, `clock`, `curr`); waking a task that last ran on a different CPU means touching that CPU's runqueue lock and cache lines, which is why cross-CPU wakeup and migration are expensive relative to a local reschedule. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**`rw_semaphore`** — the sleeping reader-writer lock, FIFO-fair by default via a handoff flag that prevents a stream of new readers from starving a waiting writer; it earns its keep specifically for long, sleeping read-side sections (`mmap_lock` is the canonical example), not for short critical sections where a plain lock is usually faster. [Reader-Writer Locks](../09-concurrency-and-locking/rwlocks-and-rwsems.md)

**Saved set-user-ID** — the copy of a task's effective UID taken at `exec()` time, which lets a setuid-root program drop privilege temporarily and later regain it with one `seteuid()` call, even as an unprivileged real UID. [Credentials and Identity](../06-processes-and-threads/credentials-and-identity.md)

**`SCHED_DEADLINE`** — the policy under which a task declares a runtime, deadline, and period instead of a priority; the kernel runs a schedulability (admission) test at `sched_setattr()` time and refuses the task outright if accepting it would leave the system unschedulable — the only Linux scheduling policy that makes a guarantee rather than a promise. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**`SCHED_FIFO`** — a static-priority (1–99) real-time policy that preempts and stays ahead of every fair-class task unconditionally; a task runs until it blocks, yields, or is preempted by a higher-priority task, with no time slice and no rotation among equal-priority tasks (unlike its sibling `SCHED_RR`). [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md)

**Scheduling class** — one of the (five, six counting `sched_ext`) fixed, strictly-ordered schedulers stop → deadline → real-time → fair → idle, each implementing the `struct sched_class` vtable (`enqueue_task`, `pick_next_task`, `task_tick`, `select_task_rq`, …) and getting first refusal on the CPU before the next lower class is even consulted. [Runqueues and Scheduling Classes](../07-scheduling/runqueues-and-scheduling-classes.md)

**Scheduling domain** — `struct sched_domain`, the hierarchy the load balancer builds to mirror a machine's actual hardware-sharing structure (SMT siblings, cores sharing an LLC, sockets, NUMA nodes), so migration cost can be weighed against which level a move crosses instead of treating every CPU as interchangeable. [SMP and Load Balancing](../07-scheduling/smp-load-balancing.md)

**`SCM_RIGHTS`** — ancillary data sent over a UNIX-domain socket that transfers an open file descriptor to another, unrelated process, installing a new descriptor in the receiver that points at the identical underlying `struct file`. [Pipes, FIFOs, and UNIX Sockets](../06-processes-and-threads/pipes-fifos-and-unix-sockets.md)

**Seccomp user notification** (`SECCOMP_RET_USER_NOTIF`) — the mechanism actually built to intervene in a syscall rather than merely observe it: a matching filter suspends the calling task and hands a supervisor process a file descriptor carrying a race-free `struct seccomp_notif` snapshot, letting the supervisor allow, fail, or (carefully) continue the call. [Tracing and Intercepting Syscalls](../05-syscalls-and-the-boundary/tracing-and-intercepting-syscalls.md)

**Secure Boot** — a signature-verification gate that checks, at each handoff from firmware to boot loader to kernel, whether the thing about to execute is signed by a key the machine trusts; it verifies provenance only, not the safety of what runs. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**Seqlock** — a scheme that lets readers proceed with no lock and no wait at all, and instead detects after the fact whether a writer interfered, via a sequence counter that's odd while a write is in progress and a reader retry loop; the kernel's timekeeper is the canonical user. [Seqlocks](../09-concurrency-and-locking/seqlocks.md)

**Sequence counter** — the bare counter half of a seqlock (`seqcount_t`), with no lock embedded, for use when the caller already holds some other lock that serializes writers and only needs the counter for readers' retry-detection benefit; `seqlock_t` is this counter bundled with its own spinlock instead. [Seqlocks](../09-concurrency-and-locking/seqlocks.md)

**`seq_file`** — the kernel interface (`include/linux/seq_file.h`) behind most non-trivial `/proc` entries: rather than a stored buffer, it invokes a `show` callback that formats live kernel state into a transient buffer at the moment of the read. [`/proc` as the Process Interface](../06-processes-and-threads/proc-as-the-process-interface.md)

**Setup header** — the fixed-layout struct inside a `bzImage` that forms the binary contract between the boot loader and the kernel, specifying which fields the loader must fill in (like `cmd_line_ptr`, `ramdisk_image`) versus only read. [Inside `bzImage`](../03-boot-and-init/the-kernel-image.md)

**`shim`** — a small loader signed by Microsoft's UEFI CA that nearly every Secure-Boot-enabled PC trusts out of the box; once running, it verifies a distribution's actual boot loader against its own baked-in key instead, so only `shim` itself needs a key in every machine's `db`. It also supports MOK enrolment, letting a user add their own signing key for a locally-built kernel module. [Secure Boot and Signed Kernels](../03-boot-and-init/secure-boot-and-signed-kernels.md)

**Shrinker (`struct shrinker`)** — the callback pair (count freeable objects, free a requested count) a cache the page allocator can't see directly — the dentry cache, the inode cache, any slab-built subsystem cache — registers so reclaim can ask it to give memory back as part of the same pass that scans the LRU lists. [Reclaim, LRU, and kswapd](../08-memory-management/reclaim-lru-and-kswapd.md)

**`sigreturn`** — the syscall (`rt_sigreturn()`) a handler's return compiles down to, which reads the signal frame back off the user stack and restores the interrupted registers, mask, and instruction pointer; it must validate that frame carefully, since a forged one is the basis of sigreturn-oriented-programming (SROP) exploits. [Signals](../06-processes-and-threads/signals.md)

**Size class** — the power-of-two (plus 96- and 192-byte) object sizes `kmalloc()`'s generic slab caches are built at; a request is rounded up to the smallest class that fits it, so a struct that grows just past a class boundary can nearly double its per-object memory cost. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**`sk_buff`** — the single structure that represents a packet through its entire trip up the networking stack, carrying both its bytes and the kernel's accumulating understanding of them; each layer strips a header by moving a pointer, not by copying. [The Life of a Packet](../02-guided-traces/the-life-of-a-packet.md)

**Slab (cache)** — a pool dedicated to one object type or size, carved from pages the page allocator supplied, with a freelist threading unused slots together so `alloc`/`free` push and pop that list instead of touching the page allocator on every call. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**SLUB** — the only slab allocator left in the tree at v6.18 (SLAB and SLOB were both removed), built on a per-CPU active slab per cache, a freelist threaded through the free objects' own memory rather than a separate bookkeeping array, and per-node partial lists consulted before a fresh page allocation. [Slab, SLUB, and `kmalloc`](../08-memory-management/slab-slub-and-kmalloc.md)

**SMAP** (Supervisor Mode Access Prevention) — hardware that stops the kernel from accessing user pages at all except inside a window explicitly opened with `stac` and closed with `clac`, the window the user-copy routines run inside; it turns an unprotected user dereference into an immediate, reproducible fault instead of a bug that might silently work for years. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**SMEP** (Supervisor Mode Execution Prevention) — hardware that stops the kernel from ever executing instructions living on a user page, closing off jumping into attacker-controlled code regardless of what confused kernel-mode state set `RIP` there. [Copying Data Across the Boundary](../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md)

**Softirq** — one of a fixed set of ten compile-time deferred-work types, run with interrupts enabled on the interrupt-exit path (`irq_exit()` → `invoke_softirq()` → `handle_softirqs()`) almost immediately after a hard-IRQ handler returns; still atomic and unable to sleep, and the same type can run on several CPUs simultaneously. [Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**sparse** — a separate static-checking tool (`make C=1`/`C=2`) that understands the kernel's address-space annotations (`__user`, `__percpu`, `__iomem`, `__rcu`) as real types with real rules, catching misuse the C compiler itself silently accepts. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**Spinlock** — a lock that busy-waits rather than sleeps, correct whenever the critical section is short or the context cannot sleep at all; taking one disables preemption on that CPU, and sleeping while holding one can hang the machine. [Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**SRCU** — sleepable RCU: relaxes the classic-RCU rule against sleeping in a read-side section by tracking each `srcu_struct` domain's grace periods independently, at the cost of a read side that does real per-CPU bookkeeping instead of being nearly free. [RCU in Practice](../09-concurrency-and-locking/rcu-in-practice.md)

**Subreaper** — a process that has opted in (via `prctl(PR_SET_CHILD_SUBREAPER, 1)`) to inherit orphaned descendants from its own tree instead of letting them fall all the way to PID 1. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Swap entry (`swp_entry_t`)** — what a PTE is rewritten to hold once its page is swapped out: cleared of its present bit and repurposed to encode a swap type (device) and offset in the bits hardware ignores when not-present, which is why a swapped page is found by a page fault rather than a separate lookup table. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**Swappiness** — `vm.swappiness`, the relative I/O cost the kernel assigns to reclaiming anonymous pages versus file-backed pages (range 0–200 at v6.18, not the older 0–100), not a probability dial; values above 100 are meaningful specifically for fast in-memory swap backends like zram/zswap. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**`SYSCALL`** — the x86-64 instruction that performs exactly five hardwired steps (load `RIP` from `MSR_LSTAR`, save the old `RIP` in `rcx` and old `RFLAGS` in `r11`, mask `RFLAGS` against `MSR_SYSCALL_MASK`, load `CS`/`SS` from `MSR_STAR`, jump) and nothing else — it switches no stack and saves no other register, leaving everything else to software. [The Entry Path](../05-syscalls-and-the-boundary/the-entry-path.md)

**`SYSCALL_DEFINEn`** — the macro family (`SYSCALL_DEFINE0` through `SYSCALL_DEFINE6`) that expands a syscall's type/name argument list into an inner `__do_sys_*` implementation plus a `pt_regs`-unpacking wrapper, giving every syscall the same calling convention, consistent argument sign-extension, and automatic `sys_enter`/`sys_exit` tracepoint hookup. [The Table and the Dispatch](../05-syscalls-and-the-boundary/the-syscall-table-and-dispatch.md)

**Syscall table** — the generated array (or, on current kernels, `switch` statement) built at compile time from a per-architecture `.tbl` file that maps a syscall number to its handler; a syscall number, once shipped, is frozen forever, and a removed syscall leaves a permanent hole rather than being reassigned. [The Table and the Dispatch](../05-syscalls-and-the-boundary/the-syscall-table-and-dispatch.md)

**Sysfs attribute** — a small `struct attribute` (name plus mode) representing one exposed value; reading or writing the corresponding file in `/sys` calls the owning `ktype`'s `show()`/`store()` functions live, computing the value on access rather than reading stored bytes. [kobjects, ksets, and sysfs](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md)

**System call** — a deliberate, synchronous request a user process makes for a named kernel service: unlike an ordinary function call, it must change privilege level, switch to a trusted stack, and land at a fixed address the kernel — not the caller — chooses, initiated by executing a trapping instruction and blocking (from the process's view) until the kernel returns. [What a System Call Actually Is](../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md)

**Taint** — a kernel-wide flag set when something happens that maintainers should weigh when reading a bug report — for example loading a module with a non-GPL-compatible license — recorded as a bitmask readable from `/proc/sys/kernel/tainted`. [Kernel Modules](../04-kernel-architecture-and-idioms/modules-in-practice.md)

**Target** — a systemd synchronization point with no process or executable of its own, just a name other units order themselves around, unlike a numbered SysV runlevel. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**`task_struct`** — the kernel's single, unified per-thread structure (there is no separate process or thread object); everything the kernel knows about a schedulable entity is a field of it, or reachable from it by one pointer. [`task_struct`: The Anatomy of a Task](../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md)

**`TASK_INTERRUPTIBLE`** — a sleeping state (`ps` shows `S`) whose wake function also reacts to a pending signal, unwinding the task back to user space to handle it rather than waiting only for the awaited event. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**`TASK_UNINTERRUPTIBLE`** — a sleeping state (`ps` shows `D`) whose wake function does not check for signals at all, used when a driver or filesystem has no safe way to abandon a multi-step operation partway through. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**Tasklet** — a function scheduled to run in softirq context (built on the `TASKLET`/`HI` softirqs) whose one added guarantee is that the same instance never runs concurrently on two CPUs; deprecated in favor of threaded IRQs or workqueues because that guarantee serialises globally rather than per-CPU. [Tasklets, and Why They Are Going Away](../10-interrupts-time-and-deferred-work/tasklets-and-their-replacement.md)

**`tgid`** — the thread-group id shared by every task in a thread group; `getpid()` returns it, while the per-task `pid` field (what `gettid()` returns) is what most people mean by "thread id." [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**THP (Transparent Huge Pages)** — automatic, opportunistic huge-page promotion of anonymous memory, either at fault time or via the `khugepaged` background scanner, requiring no application changes and giving no guarantee a given region ends up huge-page-backed; the opposite reliability model from hugetlbfs. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**Thread group** — the set of tasks created with `CLONE_THREAD` from a common caller and sharing one `tgid`; it is what POSIX calls a process, and userspace tools aggregate a thread group's tasks to display "a process" at all. [Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**Threaded IRQ** — an interrupt whose substantive work runs in its own dedicated kernel thread (`SCHED_FIFO`, priority 50 by default) rather than in hard-IRQ context, registered via `request_threaded_irq()`'s `thread_fn`; the thread may sleep, take mutexes, and allocate `GFP_KERNEL`, everything a hard-IRQ primary handler cannot. [Threaded IRQs](../10-interrupts-time-and-deferred-work/threaded-irqs.md)

**Throttling** — under a cgroup `cpu.max` quota, what happens the instant a group exhausts its period's budget: not a slowdown, a full stop, with no thread in the group running again until the next period refills the quota — the mechanism that turns a CPU limit into a latency spike rather than a smooth speed reduction. [cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**Tick** — the periodic timer interrupt that historically updated `jiffies`, ran expired timers, accounted CPU time, checked timeslices, drove RCU quiescent-state detection, and triggered load balancing, all from one interrupt firing `HZ` times a second on every CPU. [The Tick, and Living Without It](../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md)

**Timer slack** — a per-task value (`PR_SET_TIMERSLACK`, in nanoseconds) letting the kernel delay that task's timer expiries by up to the slack amount so they can be batched against other timers waking nearby, the same coalescing idea `round_jiffies` applies to the wheel but exposed per-task and runtime-tunable. [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**Timer wheel** (`timer_list`) — the kernel's default timer structure, bucketing timers into cascading levels of increasing coarseness so insertion and deletion are O(1), a trade made deliberately because most kernel timers are cancelled before they ever fire. [Timers and High-Resolution Timers](../10-interrupts-time-and-deferred-work/timers-and-hrtimers.md)

**TLB reach** — the amount of address space a TLB can translate without a walk, equal to entries × page size; the same handful of thousand cached entries covers roughly 500× more space at 2 MiB pages than at 4 KiB, which is the actual mechanism huge pages help through, not a shorter walk. [Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**TLB shootdown** — the protocol for invalidating a stale translation on every other CPU that might have cached it: find candidate CPUs via `mm_cpumask(mm)`, IPI each one, wait for every acknowledgment before the memory can be reused — the software workaround x86-64 needs because it has no instruction that broadcasts invalidation on its own. [The TLB and Address-Space Switching](../08-memory-management/tlb-and-address-space-switching.md)

**Tristate** — a Kconfig symbol type with three legal values — `n` (absent), `y` (built into `vmlinux`), or `m` (built as a separate loadable module) — as opposed to `bool`'s two. [Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md)

**TSC (Time Stamp Counter)** — a free-running cycle counter built into each x86 core, the fastest clocksource to read (one `rdtsc`) but historically the least trustworthy, since it could run at a variable frequency, stop in deep idle, or drift between cores; `constant_tsc`/`nonstop_tsc` CPU feature flags say whether a given machine's TSC has these problems. [Timekeeping and Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md)

**UEFI** — the modern firmware model that behaves like a small OS: it reads a normal FAT32 partition, loads `.efi` executables, and exposes boot-services/runtime-services APIs, in contrast to legacy BIOS's real-mode, interrupt-driven model. [Firmware: BIOS and UEFI](../03-boot-and-init/firmware-bios-and-uefi.md)

**Unit** — anything systemd manages; its filename suffix (`.service`, `.socket`, `.target`, `.mount`, `.timer`, `.path`, `.slice`) says what kind of thing it represents. [systemd: The Model](../03-boot-and-init/systemd-the-model.md)

**USS (unique set size)** — private, unshared resident pages only; the number that answers "what would be freed if I killed this process right now," since by construction nothing in it is shared with anything else. [What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**`__user`** — an annotation marking a pointer as pointing into user-space address space, which must never be dereferenced directly in kernel context; enforced only by sparse, not the compiler itself. [The Kernel Is Not C You Know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)

**User space** — code the machine does not trust with the hardware directly (shells, browsers, ordinary programs); it has its own address space and can only touch what its mappings and file descriptors permit. [The Kernel/User-Space Boundary](./the-kernel-userspace-boundary.md)

**vDSO** (virtual dynamic shared object) — a small ELF shared object built into the kernel image and mapped into every process at exec time, exporting a short list of functions (`clock_gettime`, `gettimeofday`, `time`, `getcpu`, `clock_getres` on x86-64) that can be answered entirely in user space, so most calls to them never enter the kernel at all. [The vDSO](../05-syscalls-and-the-boundary/the-vdso.md)

**Vermagic** — a string embedded in both a compiled module and the running kernel (kernel release, SMP/preemption config, module-unload/modversions support, arch token) that must match exactly for a module to load, checked independently of and before modversions. [Exported Symbols and the Non-Stable ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md)

**VMA (`vm_area_struct`)** — one contiguous range of a process's address space with uniform properties (permissions, a backing file and offset if any), describing what the process is *entitled* to have mapped; almost every memory operation a process performs is first an operation on the VMA collection, with the page tables catching up lazily afterward. [`mm_struct` and VMAs](../08-memory-management/mm-struct-and-vmas.md)

**`vmalloc`** — allocates scattered physical pages and builds new page-table entries mapping them consecutively into one virtual range, for callers that need virtual contiguity but not physical; it costs page-table setup and TLB pressure a `kmalloc` allocation in the already-mapped direct map does not pay. [`vmalloc` and Choosing an Allocator](../08-memory-management/vmalloc-and-choosing-an-allocator.md)

**`vmlinux`** — the uncompressed ELF kernel image carrying full DWARF debug symbols when `CONFIG_DEBUG_INFO` is on; it is not bootable itself and exists to be read by tools like GDB. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**`vmlinuz`** — the conventional installed name (e.g. `/boot/vmlinuz-$(uname -r)`) a distribution gives to a copy of its `bzImage`; same file, different name and location. [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md)

**Vruntime** — a task's real execution time divided by its scheduling weight, originally used by CFS to pick directly the task furthest behind (the leftmost node of a red-black tree ordered by vruntime); at v6.18 it is still accumulated the same way, but EEVDF no longer compares it directly to choose who runs — it instead feeds lag (eligibility) and the virtual-deadline calculation. [CFS and Virtual Runtime](../07-scheduling/cfs-and-vruntime.md)

**`vvar`** — the data-only page the kernel maps alongside the vDSO's code page, holding the live timekeeping state (clocksource reading, multiplier/shift, wall-clock/monotonic offsets) the vDSO reads through a seqlock; kept separate from the code page so the kernel can update it on every tick without touching executable memory. [The vDSO](../05-syscalls-and-the-boundary/the-vdso.md)

**Wait queue** — `struct wait_queue_head`, a list of tasks waiting on some event, each entry carrying its own wake function so a wakeup can mean "just one waiter" or "everyone," at no per-waiter polling cost while asleep. [Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**Wake affinity** — the set of heuristics deciding which CPU a waking task lands on, among the waker's CPU, the task's own previous CPU, or an idle CPU found by scanning the LLC domain; `WF_SYNC` biases placement toward the waker's CPU when the caller is about to sleep right after waking it. [SMP and Load Balancing](../07-scheduling/smp-load-balancing.md)

**Watermark** — one of three per-zone thresholds (`min`, `low`, `high`) that turn remaining free memory into allocator behavior: above `high` nothing happens, crossing `low` wakes `kswapd`, and hitting `min` forces the allocating task into direct reclaim itself. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**Work item** — a function plus a `struct work_struct` embedded in the caller's own structure, recovered via `container_of` inside the callback; queuing one onto a workqueue hands it to a worker thread that runs it in process context. [Workqueues](../10-interrupts-time-and-deferred-work/workqueues.md)

**Workqueue** — a policy object (`struct workqueue_struct`) that hands queued work items to a pool of kernel-thread workers running in process context, where the callback may sleep, take a mutex, or allocate `GFP_KERNEL`; concurrency-managed workqueues draw workers from shared per-CPU pools on demand rather than dedicating a thread per queue. [Workqueues](../10-interrupts-time-and-deferred-work/workqueues.md)

**Writeback** — the kernel-driven, deferred process — kthreads flushing pages once a dirty-memory or age limit is crossed — that moves dirty pages back to their filesystem; "later" is typically tens of seconds, not milliseconds. [Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**`xarray`** — an abstract, non-intrusive associative array: arbitrary pointers stored by a plain `unsigned long` index, with the implementation managing its own internal tree nodes and RCU-aware locking; the current, more general replacement for the older `radix_tree` API, and what the page cache is built on. [Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)

**Zero page (`empty_zero_page`)** — one physical page, filled with zeros, mapped read-only for the first *read* of any untouched anonymous page by every process on the system; only the first *write* actually allocates a private, real frame, which is why a large `calloc()` that's never fully written is nearly free. [Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**Zombie** — a task past `exit_notify()`: its memory, files, and other resources are already released, and all that remains is a shrunken `task_struct` holding its PID and exit status for the parent's `wait()` to collect. [Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**Zone** — a partition of physical memory (`ZONE_DMA`, `ZONE_DMA32`, `ZONE_NORMAL`, `ZONE_MOVABLE`, and 32-bit-only `ZONE_HIGHMEM`) so an allocation needing a restricted physical range asks the right pool instead of hoping; `DMA32` and `NORMAL` are what matter day to day on x86-64. [The Page Allocator](../08-memory-management/the-page-allocator.md)

**zram** — a compressed block device used *as* the swap device itself (or any block device), with no backing device — once full, ordinary swap-full behavior applies, a hard ceiling rather than a degrade. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**zswap** — a compressed cache sitting in front of a real swap device; pages that don't fit the compressed pool write through to backing swap, so it degrades rather than hard-capping, at the cost of needing real swap configured underneath it. [Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)
