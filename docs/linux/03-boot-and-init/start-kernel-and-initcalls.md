---
id: start-kernel-and-initcalls
title: "`start_kernel` and the Initcall Order"
sidebar_label: "start_kernel"
sidebar_position: 8
tags: [linux, kernel, boot]
prerequisites:
  - linux/boot-and-init/early-boot-and-arch-setup
draft: false
---

# `start_kernel` and the Initcall Order

What the kernel brings up and in what order, and why driver initialisation order is a level rather than a list.

`start_kernel()` is the closest thing the kernel has to a `main()`, and reading it in order is the
single best way to learn what a kernel *is*: each call it makes brings one subsystem from unusable to
usable, in an order that is almost entirely forced by dependencies — you cannot set up per-CPU data
before you know how many CPUs there are, and you cannot initialise the scheduler on top of a memory
allocator that doesn't exist yet.

## Reading `start_kernel()` in order

<Src file="init/main.c" symbol="start_kernel" /> is long, and most of it is subsystems that only matter
once you're chasing something specific in them. The calls worth knowing on a first pass, in the order
they actually appear in v6.18:

| Call | What it brings up |
|---|---|
| `boot_cpu_init()` | Marks the boot CPU present, active, and online in the CPU masks — the first CPU-topology state that exists. |
| `setup_arch(&command_line)` | Architecture-specific setup: memory map from the boot loader/firmware, early page tables finalised, command line extracted from `boot_params`. The single largest early call. |
| `setup_command_line()` | The command line extracted by `setup_arch()` is copied into its saved, stable form (`saved_command_line`) before anything downstream parses it. |
| `setup_per_cpu_areas()` | Allocates the per-CPU data regions every CPU-local variable lives in — a prerequisite for essentially everything that follows. `setup_nr_cpu_ids()`, `smp_prepare_boot_cpu()`, `early_numa_node_init()`, and `boot_cpu_hotplug_init()` run in this same stretch, fixing CPU count and topology before anything CPU-indexed is allocated. |
| `parse_early_param()` | `early_param`-registered parameters (like `nokaslr`, which the [previous page](./early-boot-and-arch-setup.md) depends on) are parsed now — deliberately *after* per-CPU areas and CPU topology exist, not before. |
| `mm_core_init()` | Brings the page allocator itself online. Nothing that needs to allocate memory through the normal allocator can run before this. |
| `sched_init()` | The scheduler's own data structures — run-queues, scheduling classes — are initialised, though no scheduling happens yet; interrupts are still off. |
| `rcu_init()` | RCU (the kernel's lock-free read-side synchronisation mechanism) becomes usable; a large fraction of core kernel code depends on it. |
| `init_IRQ()` / `time_init()` | Interrupt handling and the timekeeping subsystem come up — after this point the kernel has a notion of elapsed time and can take interrupts safely. |
| `console_init()` | The real console driver(s) attach; this is the point [the previous page's](./early-boot-and-arch-setup.md#what-is-not-available-yet) "no printk to a real console" limitation ends and buffered early messages get flushed to it. |
| `rest_init()` | Does not return. Hands the rest of boot to two new threads and the boot CPU's own idle loop — see below. |

Everything in this list runs on the boot CPU, in this order, on every boot — it is not configuration, it
is dependency order made explicit in source.

## `rest_init()` and the first threads

<Src file="init/main.c" symbol="rest_init" /> is where `start_kernel()` stops being a single thread of
control. It does three things, in an order that itself matters:

1. **Spawns PID 1 first**, via `user_mode_thread(kernel_init, NULL, CLONE_FS)` — PID 1 has to exist
   before anything that might want to be its child does. `kernel_init()` is the function this thread
   runs; it is what turns into user-space init once it execs one.
2. **Spawns `kthreadd` as PID 2**, via `kernel_thread(kthreadd, NULL, NULL, CLONE_FS | CLONE_FILES)`.
   `kthreadd` is the kernel-thread factory: every kernel thread created after boot (workqueue workers,
   filesystem journal threads, and so on) is spawned as its child, which is why `ps` on a running system
   shows so many threads with `kthreadd` as their parent.
3. **The boot CPU itself becomes the idle task** — `rest_init()` never returns; the calling context falls
   into the scheduler's idle loop for CPU 0, the same idle loop every other CPU's bring-up eventually
   reaches.

The result — PID 1, PID 2, and the boot CPU's idle task — is a three-way split that surprises people who
picture boot as one long linear thread finally execing `/sbin/init`. It isn't: by the time `/sbin/init`
runs, the kernel already has three independent contexts running, and only one of them is the one that
becomes what a user thinks of as "the system."

## Initcall levels

Most kernel subsystems don't wire themselves up from inside `start_kernel()` by name — a built-in driver
or subsystem registers an **initcall**, a function pointer placed into a named linker section at build
time via a macro, and the kernel walks those sections in order at the right point in boot. The levels, as
defined in <Src file="include/linux/init.h" symbol="early_initcall" />:

| Level | Macro | What belongs there |
|---|---|---|
| `early` | `early_initcall()` | Runs earliest of all, before SMP bring-up, from `do_pre_smp_initcalls()` — reserved for the handful of subsystems that must exist before other CPUs are brought online. |
| `pure` | `pure_initcall()` | Almost nothing — reserved for code with no dependencies on anything else, run first among the "normal" levels. |
| `core` | `core_initcall()` | Core kernel infrastructure other subsystems build on. |
| `postcore` | `postcore_initcall()` | Depends on `core` having already run. |
| `arch` | `arch_initcall()` | Architecture-specific setup that needs core infrastructure but comes before generic subsystems. |
| `subsys` | `subsys_initcall()` | Generic subsystems — most bus types and core driver-model infrastructure register here. |
| `fs` | `fs_initcall()` | Filesystem types register here; `rootfs_initcall()` (used by `populate_rootfs()`, see [the next page](./initramfs-and-early-userspace.md)) shares this numeric level. |
| `device` | `device_initcall()` | The bulk of built-in device drivers — the level most people mean when they say "driver init." |
| `late` | `late_initcall()` | Everything that explicitly wants to run after every other driver has had its chance. |

The linker collects every level's initcalls into one contiguous section per level
(`initcall_levels[]` in <Src file="init/main.c" symbol="do_initcalls" />), and `do_initcalls()` — called
from `do_basic_setup()`, itself called from `kernel_init()` — walks the levels in this exact order,
calling every function in a level before moving to the next.

## Why order is a level, not a list

A driver cannot say "run me after that other driver." It can only say which *level* it belongs to, and a
built-in driver's macro (`module_init()` resolves to `device_initcall()` for a built-in, non-modular
driver) fixes that level at compile time. Within a single level, the only thing that determines order is
**link order** — the order object files were linked in, which is itself a function of Makefile order and
is not something driver authors control precisely or are supposed to depend on.

This is exactly why **deferred probing** exists: if driver B's `probe()` needs a resource driver A
provides, and nothing guarantees A runs before B even within the same level, B's `probe()` returning
`-EPROBE_DEFER` tells the driver core "try me again once more devices have probed," rather than the
kernel trying to solve initcall ordering as a dependency graph. Initcall level is a coarse phase, not a
promise about any two drivers' relative order — the driver model handles the fine-grained case instead.

## Watching it happen

`initcall_debug` (a boot parameter) makes every initcall print when it starts and how long it took,
turning the invisible list above into something you can watch scroll by in real time and profile:

```text
[    0.041203] calling  migration_init+0x0/0x20 @ 1
[    0.041215] initcall migration_init+0x0/0x20 returned 0 after 3 usecs
[    0.041980] entering initcall level: subsys
...
```

Besides being the standard way to *see* the order this page describes, it is also the standard boot-time
profiling tool: sorting the "returned ... after N usecs" lines by duration finds whichever initcall is
taking longest, which is often the fastest way to explain "why does this kernel take longer to boot than
that one."

<Lab host="qemu" title="Watch every initcall run" time="10 min">

Using [the canonical invocation](../01-lab-and-toolchain/booting-your-kernel-in-qemu.md#the-canonical-invocation),
add `initcall_debug` and raise the log level so the debug-level lines it produces are actually visible:

```text
$ qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \
    -initrd ../initramfs.cpio.gz \
    -append "console=ttyS0 initcall_debug loglevel=8" \
    -nographic -m 2G -smp 2 -enable-kvm -no-reboot
```

Expect a scroll of paired lines, one `calling` and one `initcall ... returned` per initcall:

```text
[    0.041203] calling  migration_init+0x0/0x20 @ 1
[    0.041215] initcall migration_init+0x0/0x20 returned 0 after 3 usecs
[    0.041980] entering initcall level: subsys
[    0.042010] calling  pci_subsys_init+0x0/0x40 @ 1
[    0.042390] initcall pci_subsys_init+0x0/0x40 returned 0 after 380 usecs
```

Once booted, inside the guest, pull every `returned` line out of the kernel log ring buffer and sort by
the reported duration to find the slowest initcall:

```text
$ dmesg | grep "returned 0 after" | sort -t' ' -k8 -rn | head
```

The `-k8` field index depends on the exact log-line format your build produces — count the
space-separated fields on one real line before trusting it, rather than assuming this page's example
matches yours exactly.

**If it fails:** no `calling`/`initcall` lines at all usually means `loglevel=8` was dropped from the
`-append` string — those lines print at `KERN_DEBUG`, which is invisible at the kernel's default log
level, so `initcall_debug` alone is not enough.

</Lab>

<KernelFacts
  structure={[["start_kernel()", "init/main.c"], ["do_initcalls()", "init/main.c"]]}
  path="start_kernel() → subsystem init in dependency order → rest_init() → kernel_init() → do_pre_smp_initcalls() (early) → do_basic_setup() → do_initcalls() (pure…late) → /init"
  observe="boot with initcall_debug loglevel=8, then dmesg | grep initcall | tail"
  trap="Initcall levels order *phases*, not drivers. Two drivers at the same level run in link order, which is why a driver that needs another's resource uses deferred probing (-EPROBE_DEFER) rather than an ordering assumption." />

## References

- <Src file="init/main.c" symbol="start_kernel" /> — the function this page is a reading of, and the
  primary source for every call named above.
- [Core kernel documentation](https://docs.kernel.org/core-api/index.html) — the subsystems
  `start_kernel()` brings up, documented individually rather than as one linear read.
- [Driver core: probing and deferral](https://docs.kernel.org/driver-api/driver-model/porting.html) —
  deferred probing in detail, and why initcall order is deliberately not a dependency mechanism between
  drivers.
