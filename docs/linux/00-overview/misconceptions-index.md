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

## 05 — Syscalls and the Boundary

**"ABI stability means the kernel's interfaces never change."** They change constantly — new
syscalls, new flags, new fields. The promise is specifically that *existing* meanings never change,
not that the surface is frozen.
[ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md)

**"A 64-bit kernel just runs 32-bit binaries, no special-casing needed."** It requires an entire
parallel syscall table and a set of `compat_` translation layers for every structure whose layout
differs by word width — real, maintained code, not an emergent property of the CPU supporting both
modes.
[ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md)

**"Checking the syscall number is enough for a security filter."** It isn't, if the filter doesn't
also pin the calling ABI — a 32-bit compat call can reach a syscall number that means something
different than it does natively.
[ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md)

**"Syscalls return -1 and set errno."** That's libc's behaviour, applied uniformly across its
wrappers. The kernel returns a negative errno value directly; there is no `-1` and no `errno` on the
kernel side of the boundary.
[Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**"`EINTR` means the call failed."** It means the call was interrupted by a signal before it could
complete, not that anything is wrong. For most blocking calls the correct response to `-EINTR` is
simply to call it again.
[Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**"You can pass extra syscall arguments on the stack."** The syscall ABI has no stack arguments at
all. Six registers is the entire budget — there is no seventh slot anywhere, on the stack or
otherwise.
[Arguments, Returns, and errno](../05-syscalls-and-the-boundary/arguments-return-values-and-errno.md)

**"`fork()` is a syscall."** On Linux it is a glibc wrapper over `clone`, called with a specific flag
combination. There has never been a bare `fork` syscall entry on modern x86-64 Linux in the way people
picture it.
[libc Is Not the Kernel](../05-syscalls-and-the-boundary/libc-is-not-the-kernel.md)

**"musl is glibc with fewer features."** It's a different implementation with different design
defaults, not a stripped-down glibc. Some of the differences — DNS resolution, stdio buffering —
change what a program actually *does*, not merely how fast it does it.
[libc Is Not the Kernel](../05-syscalls-and-the-boundary/libc-is-not-the-kernel.md)

**"Static linking removes the libc dependency."** It removes the *runtime* dependency — no `ld.so`
needed at startup — but not the behavioural one. Statically-linked glibc binaries still load NSS
modules dynamically at runtime for name resolution.
[libc Is Not the Kernel](../05-syscalls-and-the-boundary/libc-is-not-the-kernel.md)

**"A syscall is slow because the kernel is slow."** Most of the measured cost is the transition and
its cache and branch-predictor effects, not the work the kernel does once it gets there — a trivial
`getpid()` and a syscall that does real I/O pay nearly the same fixed overhead before either one
starts working.
[What a System Call Actually Is](../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md)

**"Syscalls are how programs talk to the kernel."** Some of the most frequent kernel interactions a
running program has involve no syscall at all: page faults on first touch of a mapped page, and vDSO
reads that never leave userspace.
[What a System Call Actually Is](../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md)

**"The kernel runs on my behalf in a separate thread."** It does not. The kernel code servicing your
syscall runs *in your task's context*, on *your task's kernel stack*, and the time it spends is
charged to *your task's* `sys` time.
[What a System Call Actually Is](../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md)

## 06 — Processes and Threads

**"`exec()` creates a new process."** It replaces the program running inside the *existing* process —
the PID is unchanged. The common `fork()` + `exec()` pattern creates the new process with `fork()`;
`exec()`'s own job is pure replacement.
[`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**"The kernel runs the dynamic linker."** The kernel *maps* the dynamic linker into memory and jumps
to its entry point. Everything the dynamic linker then does — reading `.dynamic`, mapping libraries,
resolving relocations — is ordinary user-space code that happens to run before the program you asked
for.
[`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**"`#!/usr/bin/env python` is a shell feature."** It's a kernel binary-format handler
(`binfmt_script`), which is exactly why it works identically no matter what launches the script — the
shell never gets a chance to interpret the line, the kernel does.
[`exec()` and Binary Formats](../06-processes-and-threads/exec-and-binary-formats.md)

**"Zombies leak memory."** A zombie holds a PID slot and a small `task_struct` remnant — its memory
was already released before it became a zombie at all. The real resource pressure is PID exhaustion,
not memory.
[Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**"You can `kill -9` a zombie."** There is nothing left to signal — a zombie is not executing and
never will again. The correct target for a signal is the *parent*, to make it call `wait()`.
[Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**"Orphans become zombies."** The opposite: orphans are reparented (to a subreaper or PID 1) and, by
convention, promptly reaped by whatever process takes them on.
[Exit, Zombies, and Orphans](../06-processes-and-threads/exit-zombies-and-orphans.md)

**"`/proc` files are zero bytes, so they must be empty."** The size a `stat()` reports is meaningless
for a generated file, because the content doesn't exist until a `read()` triggers the callback that
produces it.
[`/proc` as the Process Interface](../06-processes-and-threads/proc-as-the-process-interface.md)

**"Reading `/proc` is free."** Some entries do real, non-trivial work per read: `smaps` walks every
page table entry backing every VMA in the target process, and running it in a tight loop across every
process on a busy host is a real way to add CPU load, not a free observability query.
[`/proc` as the Process Interface](../06-processes-and-threads/proc-as-the-process-interface.md)

**"`/proc/PID/environ` shows the process's current environment."** It shows the environment block as
it stood at `exec()` time. A program that calls `setenv()`/`putenv()` afterward changes its own view
of the environment without moving what `/proc/PID/environ` reads from.
[`/proc` as the Process Interface](../06-processes-and-threads/proc-as-the-process-interface.md)

**"`TASK_RUNNING` means the task is on a CPU."** It means runnable — eligible to run. Whether it's
actually receiving cycles right now is a separate question the scheduler answers, not a fact `__state`
records.
[Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**"A `D`-state process is stuck in the kernel and hung."** It's *waiting*, and in the overwhelming
majority of cases waiting correctly. The actionable question is never "why is it hung," it's "what is
it waiting on."
[Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**"Load average measures CPU usage."** It counts runnable tasks *and* uninterruptible tasks together.
A machine can be at 0% CPU utilization with a load average of 40.
[Process States and Wait Queues](../06-processes-and-threads/process-states-and-wait-queues.md)

**"A signal interrupts the process immediately."** It's delivered when the target next returns to
user space — which may be a few instructions away, or may be never, if the target never returns.
[Signals](../06-processes-and-threads/signals.md)

**"Signals queue."** Standard signals do not — a second occurrence while one is already pending is
simply lost. Only real-time signals queue.
[Signals](../06-processes-and-threads/signals.md)

**"`kill -9` always works instantly."** `SIGKILL` cannot be blocked or caught, but that isn't the same
as "cannot be delayed" — it still cannot act on a task that hasn't returned to user space.
[Signals](../06-processes-and-threads/signals.md)

**"Threads are lighter than processes on Linux."** Creating one is cheaper, and switching between two
threads of the same process skips a page-table switch — but the object the scheduler picks up and
runs is identical in both cases, and the scheduler does the identical amount of work either way.
[Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**"A process has one `task_struct`."** It has one *per thread* — there is no separate "process"
object; there is just a thread group with one or more members.
[Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

**"`getpid()` returns this thread's own kernel identifier."** It returns the **thread group** id
(`tgid`). The task's own id is what `gettid()` returns — the reverse of what the function names
suggest.
[Threads Are Tasks](../06-processes-and-threads/threads-are-tasks.md)

## 07 — Scheduling

**"A 0.5 CPU limit makes the app run at half speed."** It runs at full speed for half of every period
and is stopped completely for the other half — a request that straddles the throttle boundary stalls
for the rest of the period, which a smoothly halved clock speed would never do.
[cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**"More threads help under a quota."** They do the opposite: more parallel threads burn the same
fixed quota faster, exhausting it sooner and increasing the fraction of the period spent throttled.
[cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**"`cpu.weight` limits a container."** It doesn't limit anything by itself. It only changes the
outcome when the CPU is *contended* — an idle machine gives a low-weight container the whole CPU too.
[cgroup CPU Control](../07-scheduling/cgroup-cpu-control.md)

**"nice 19 means the process only runs when the system is idle."** It means a small weight, not
zero. `SCHED_IDLE` is the actual policy for "only run when nothing else wants the CPU."
[Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**"nice affects I/O priority too."** It doesn't. Disk I/O scheduling is a separate mechanism —
`ionice` and the I/O scheduler's own priority classes — against a completely different queue.
[Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**"A lower nice number is lower priority."** The opposite: nice -20 is the *highest*-share setting,
nice 19 the lowest. The name describes how considerate the process is being to its competitors, not
its rank.
[Priorities, nice, and Weights](../07-scheduling/priorities-nice-and-weights.md)

**"Context switches are expensive because saving registers is slow."** The register save/restore in
`__switch_to()` is the cheap, nameable part. The expense is almost entirely the *indirect* cost paid
afterward by cold caches and a cold TLB.
[The Context Switch](../07-scheduling/the-context-switch.md)

**"A thread switch is free."** It skips the address-space switch, which is real savings — but
`switch_to()` still runs unconditionally and caches, branch predictor, and FPU state may still need
saving and restoring. Cheaper than a process switch, not free.
[The Context Switch](../07-scheduling/the-context-switch.md)

**"High context-switch counts are bad."** A high *voluntary* count usually means a workload that's
correctly I/O-bound or event-driven. The number worth watching with suspicion is a high or rising
*involuntary* count.
[The Context Switch](../07-scheduling/the-context-switch.md)

## 08 — Memory Management

**"`malloc` allocates memory."** It reserves address space. First touch is what actually allocates a
physical page, one page at a time, on the first write.
[Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**"If `malloc` succeeded, the memory is mine."** Under the default overcommit policy, a successful
`malloc()` is a promise the kernel may not be able to keep — the failure can arrive later as a page
fault the kernel cannot satisfy, and then as the OOM killer choosing a process to kill.
[Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**"COW means `fork()` is free."** It defers the cost, it doesn't eliminate it. COW marks pages
read-only and shares them cheaply, but the first write to each shared page still costs exactly what an
ordinary first-touch write costs.
[Demand Paging and Copy-on-Write](../08-memory-management/demand-paging-and-cow.md)

**"Huge pages help because there are fewer page-table levels to walk."** The walk depth *above* the
terminating level is unchanged. The actual benefit is TLB reach — far more address space covered per
cached entry, so far fewer walks happen at all.
[Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**"THP should always be disabled."** That advice reflects a specific configuration from a specific
era; `defrag=defer`-family settings decouple allocation from fault-path compaction, so blanket-disabling
THP forfeits a benefit a different `defrag` setting may no longer cost.
[Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**"hugetlbfs and THP are the same feature with different names."** They have opposite reliability
models: hugetlbfs is an explicit reservation, never reclaimed and never a surprise; THP is
opportunistic and kernel-driven, present or absent depending on fragmentation at the moment of the
fault.
[Huge Pages and THP](../08-memory-management/hugepages-and-thp.md)

**"Swap is used only when RAM is full."** The kernel may swap out genuinely idle anonymous pages to
make room for page cache while RAM still has room — correct, deliberate behavior, not a sign of
trouble.
[Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**"`swappiness=0` disables swap."** It strongly biases the kernel against initiating swap on a
runnable process's pages, but swapping can still happen.
[Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**"Swap makes things slow."** Thrashing makes things slow. Swap is what the kernel does *before*
thrashing becomes unrecoverable.
[Swap, zswap, and zram](../08-memory-management/swap-and-zswap.md)

**"The OOM killer kills the process that caused the problem."** It doesn't evaluate cause at all — it
kills the task whose death is scored to free the most memory. A process that leaks slowly for hours
can survive an OOM that kills a large, well-behaved process instead.
[The OOM Killer](../08-memory-management/the-oom-killer.md)

**"An OOM kill means the machine ran out of RAM."** It means a specific allocation request couldn't
be satisfied after reclaim was exhausted — that can happen with free memory sitting unused in the
wrong zone, or with plenty of free 4 KiB pages but no free run long enough for a high-order request.
[The OOM Killer](../08-memory-management/the-oom-killer.md)

**"You can prevent OOM by disabling overcommit."** Setting `vm.overcommit_memory=2` doesn't remove
the underlying scarcity — it moves the failure earlier, to `malloc()`/`mmap()` returning `ENOMEM`
instead of a kernel-chosen kill.
[The OOM Killer](../08-memory-management/the-oom-killer.md)

**"Low free memory means the machine is short of memory."** Page cache is memory doing useful work,
not memory sitting idle — a `MemFree` near zero with a large `buff/cache` is normal and healthy. Read
`available`, not `free`.
[What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**"Summing RSS across processes gives total memory usage."** It double-counts every shared page —
badly for forked worker pools and for anything linking common shared libraries. PSS is the number
built to sum correctly.
[What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**"A container using its full memory limit is about to be OOM-killed."** Most of that usage may be
reclaimable page cache charged to the cgroup, and the kernel will reclaim it under pressure before it
starts killing.
[What `free` and RSS Really Tell You](../08-memory-management/what-free-and-rss-really-say.md)

**"`write()` returning means the data is written."** It means the data is in RAM, in a dirty
page-cache folio. Whether and when it reaches the device is up to the writeback machinery, unless the
caller forces it with `fsync`.
[Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**"Closing the file flushes it."** `close()` does not imply `fsync` and never has, on Linux or any
POSIX system. A file descriptor can be closed with dirty data still sitting unwritten in the page
cache.
[Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

**"`fsync` on the file is enough for a new file."** It durably writes the file's data and metadata,
but says nothing about the directory entry that makes the file findable by name — that needs its own
`fsync`, on the directory.
[Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md)

## 09 — Concurrency and Locking

**"Spinlocks waste CPU, so mutexes are always better."** For a short critical section this is
backwards: a mutex's sleep/wake path costs two context switches, far more expensive than whatever
cycles a short spin actually took.
[Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**"`spin_lock_irqsave()` disables interrupts on all CPUs."** It disables interrupts only on the CPU
executing the call — the only CPU it needs to protect, since the deadlock it prevents is a CPU racing
against its *own* interrupt handler.
[Spinlocks](../09-concurrency-and-locking/spinlocks.md)

**"A spinlock protects data from other CPUs."** It protects data from anything that takes the same
lock — which includes this CPU's own interrupt handlers and softirqs only if the code took a variant
that also excludes them (`_irqsave`, `_bh`).
[Spinlocks](../09-concurrency-and-locking/spinlocks.md)

## 10 — Interrupts, Time, and Deferred Work

**"`msleep(1)` sleeps for one millisecond."** It sleeps for at least one jiffy — never less — plus
whatever wheel slack applies on top. Assuming millisecond-granularity timing from `msleep(1)` is a bug
that only shows up as flaky timing under a different `HZ`.
[Delays and Sleeps: What They Really Do](../10-interrupts-time-and-deferred-work/delays-and-sleeps.md)

**"`udelay` is more accurate, so use it for short waits generally."** It is accurate, and it also
burns a CPU core doing nothing else for the whole duration — a trade only acceptable in atomic
context.
[Delays and Sleeps: What They Really Do](../10-interrupts-time-and-deferred-work/delays-and-sleeps.md)

**"A range in `usleep_range` means the kernel is being vague about it."** The range is the entire
mechanism, not an apology for imprecision — it's what lets the kernel coalesce your wakeup with
someone else's and avoid a dedicated interrupt.
[Delays and Sleeps: What They Really Do](../10-interrupts-time-and-deferred-work/delays-and-sleeps.md)

**"Softirqs are threads."** They usually are not. A softirq normally runs on the interrupt-exit path,
inline — no thread, no scheduling decision. Only when the budget is exceeded does the remainder move
to `ksoftirqd`.
[Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**"High `si` means a kernel problem."** It usually means a high rate of packets or I/O completions —
`si` climbing under a genuine traffic spike is the softirq mechanism doing its job, not evidence the
job is broken.
[Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

**"A softirq runs on one CPU at a time."** False — the *same* softirq type can be raised and run on
several CPUs at once, each processing its own CPU's work independently, which is exactly why softirq
handlers need locking around any data they share across CPUs.
[Softirqs](../10-interrupts-time-and-deferred-work/softirqs.md)

---

This index grows with the section — folders 05 through 19 add their own misconceptions here as they
land.
