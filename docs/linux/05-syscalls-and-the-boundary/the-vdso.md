---
id: the-vdso
title: "The vDSO"
sidebar_label: "The vDSO"
sidebar_position: 6
tags: [linux, kernel, syscalls]
prerequisites:
  - linux/syscalls-and-the-boundary/what-a-system-call-actually-is
draft: false
---

# The vDSO

Some "system calls" are not system calls. `clock_gettime` is called millions of times a second by
ordinary programs — every timestamp, every timeout, every profiler sample goes through it — and paying a
full privilege transition, with all the register-saving and mode-switching [the entry path](./the-entry-path.md)
describes, just to read a value the kernel has already computed and could simply *show* you, would be
absurd. The vDSO is the kernel publishing that value directly into your address space, so most calls to
it never enter the kernel at all.

## What it is

The vDSO (virtual dynamic shared object) is a small ELF shared object, built as part of the kernel image
itself, that the kernel maps into every process at exec time. It is not a file that exists anywhere on
disk — there is no path to open it by — and yet it behaves, from user space's point of view, exactly
like an ordinary shared library that happens to already be loaded: it shows up as a mapping named
`[vdso]` in `/proc/PID/maps`, and `ldd` lists it (`linux-vdso.so.1`) with no path, because there is none
to show. Alongside it, the kernel maps a second, data-only page named `[vvar]` — the vDSO's code and the
timekeeping data it reads are deliberately kept in separate mappings, so the data page can be updated by
the kernel on every tick without the code page ever needing to change.

## What it provides

On x86-64, the vDSO exports a short, fixed list of symbols: `clock_gettime`, `gettimeofday`, `time`,
`getcpu`, and `clock_getres`. That is the entire list — every one of them is either reading the current
time or reading which CPU the caller is running on, the two categories of information genuinely cheap
enough to compute in user space from data the kernel keeps up to date. This list is architecture-
dependent; other architectures export a different (and not necessarily identical) set. Anything not on
the list — `read`, `open`, `write`, and the overwhelming majority of the syscall table — still costs a
real syscall, with a real privilege transition, exactly as [what a system call actually is](./what-a-system-call-actually-is.md)
describes.

## How it works

The `[vvar]` page holds the kernel's live timekeeping state — the current clocksource reading, the
multiplier and shift used to convert clock cycles to nanoseconds, and the wall-clock/monotonic offsets —
which the kernel updates on every timer tick. The vDSO's code, running entirely at user privilege, reads
that page directly: it takes a sequence-counter snapshot, reads the clocksource and the offset fields,
does the cycle-to-nanosecond arithmetic itself, and then re-checks the sequence counter to make sure
nothing in the page changed underneath it while it was reading. That retry protocol is a seqlock, and
the vDSO is its canonical, textbook user; [seqlocks](../09-concurrency-and-locking/seqlocks.md) owns the
explanation of how the retry loop actually works and why it is safe against a concurrent writer — this
page only points at it rather than re-deriving it.

## What actually happens

Call `clock_gettime(CLOCK_MONOTONIC, &ts)` from ordinary C code and follow what happens on a machine with
a usable clocksource:

1. libc's `clock_gettime` wrapper does not issue a `SYSCALL` at all — it calls straight into the vDSO's
   exported `__vdso_clock_gettime` symbol, an ordinary function call within the same process, at the
   same privilege level the caller was already running at.
2. That function reads the `[vvar]` page's sequence counter, reads the current clocksource value (a
   `rdtsc` on most x86-64 machines with a usable TSC) and the associated multiplier/shift/offset fields,
   then re-reads the sequence counter to confirm nothing changed mid-read.
3. It converts the clocksource reading to a `struct timespec` in user space and returns it directly to
   the caller.

At no point does control cross into ring 0. And that has a visible, and genuinely surprising,
consequence for anyone reaching for `strace` to understand where time is going in a program:

```text
$ strace -e trace=clock_gettime ./a.out
+++ exited with 0 +++
```

Nothing. Not one line, no matter how many times `clock_gettime` was called in the program. "`strace`
shows no syscall" is not evidence that nothing happened — it is evidence that whatever happened, happened
entirely in user space, running kernel-authored code the tracer has no visibility into. This is exactly
the property that surprises people debugging timing-sensitive code with `strace`: a program can call
`clock_gettime` in a tight loop a million times and an `strace` session watching it will show nothing at
all for every one of those calls.

## When it falls back

The fast path above depends on the active clocksource being one the vDSO code knows how to read directly
from user space — practically, a TSC that has been marked stable and synchronized across CPUs. If the
clocksource in use is not vDSO-capable — an HPET or the ACPI PM timer, both of which require an actual
I/O access only the kernel can perform, rather than a plain read of a CPU register — the vDSO code
detects this and falls back to making a real syscall on the caller's behalf. This is why the *same
binary*, doing the *same thing*, can show wildly different `clock_gettime` costs on two different
machines: one with a stable, vDSO-usable TSC pays essentially nothing per call, and one that fell back to
HPET pays a full syscall every time. This is a genuine, recurring production performance issue, not a
theoretical one — `cat /sys/devices/system/clocksource/clocksource0/current_clocksource` is the first
thing to check when `clock_gettime` shows up hot in a profile on an unfamiliar machine.

## The vsyscall page, briefly

The vDSO's predecessor was the vsyscall page: a handful of the same functions, mapped at a single fixed
virtual address in every process, on every boot, on every kernel of a given build. A fixed, predictable
executable address in every process turned out to be a gift to exploit writers — a reliable
address to jump to regardless of ASLR — so the vsyscall page has since been emulated (trapped and
handled in the kernel rather than executed directly) or disabled outright, and `vsyscall=none` is the
modern default. The vDSO itself does not have this problem: its mapping address is randomized like any
other mapping, per the process's ASLR state.

<Lab host="any-linux" title="See the vDSO in your own process" time="10 min">

1. **Find the mappings.** `grep -E 'vdso|vvar' /proc/self/maps` — expect two lines, each with no
   filesystem path, ending in `[vdso]` and `[vvar]` respectively, something like:
   ```text
   7ffd2b1f0000-7ffd2b1f2000 r-xp 00000000 00:00 0                        [vdso]
   7ffd2b1ee000-7ffd2b1f0000 r--p 00000000 00:00 0                        [vvar]
   ```
2. **Confirm libc sees it as a shared object.** `ldd /bin/ls` — expect a line reading
   `linux-vdso.so.1 =>  (0x00007ffd2b1f0000)` (the exact address varies every run under ASLR), with no
   path before the address, unlike every other line `ldd` prints.
3. **Watch a vDSO call go untraced.** Extracting the mapping's bytes with `dd` against
   `/proc/self/mem` is fragile and easy to get wrong, so instead write a three-line C program that calls
   `clock_gettime(CLOCK_MONOTONIC, &ts)` in a loop and run it under `strace -c`:
   ```c
   for (int i = 0; i < 1000000; i++)
       clock_gettime(CLOCK_MONOTONIC, &ts);
   ```
   Expect `strace -c ./a.out` to report no `clock_gettime` entries at all in its summary table — the
   loop ran a million times and the tracer saw none of it.
4. **Contrast with a call that does cross the boundary.** Replace the loop body with `getpid()` and run
   the same `strace -c ./a.out` again. Expect a `getpid` row in the summary with a call count matching
   the loop count — `getpid` has no vDSO implementation on x86-64, so every call is a real syscall and
   every one is traced.

If it fails: some hardened kernels and container runtimes restrict what `/proc/self/maps` reveals (see
`kptr_restrict`), which can hide or alter the addresses shown in step 1 without removing the mappings
themselves. A container may also present a different clocksource than the host, which changes step 3's
outcome — re-check `current_clocksource` per [When it falls back](#when-it-falls-back) above if step 3's
loop unexpectedly shows syscalls.

</Lab>

```mermaid
flowchart LR
    call["clock_gettime() call"]
    subgraph user["User space"]
        vdso["__vdso_clock_gettime()<br/>seqlock read of [vvar]<br/>rdtsc + arithmetic"]
        result1["return timespec"]
    end
    subgraph boundary["Privilege boundary"]
        direction TB
    end
    subgraph kernel["Kernel"]
        sys["sys_clock_gettime()<br/>real clocksource read"]
        result2["return timespec"]
    end
    call -->|vDSO-capable clocksource| vdso --> result1
    call -->|non-vDSO clocksource| boundary
    boundary -->|SYSCALL, crosses into kernel| sys --> result2
```

*The same `clock_gettime()` call, with and without a usable vDSO clocksource.*

<KernelFacts
  structure={[["struct vdso_time_data", "include/vdso/datapage.h"]]}
  path="clock_gettime() → vDSO __vdso_clock_gettime() → seqlock read of the vvar page → rdtsc → arithmetic → return, no kernel entry"
  observe="grep -E 'vdso|vvar' /proc/self/maps && cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
  trap="strace showing no syscall does not mean no kernel code ran on your behalf. The vDSO is kernel-built, kernel-mapped code running at user privilege, and it is invisible to every syscall tracer." />

## References

- [`vdso(7)`](https://man7.org/linux/man-pages/man7/vdso.7.html) — the canonical description, including
  the per-architecture symbol lists.
- <Src file="arch/x86/entry/vdso/vma.c" symbol="arch_setup_additional_pages" /> — where the vDSO mapping
  is actually installed into a new process's address space.
- <Src file="include/vdso/datapage.h" symbol="vdso_time_data" /> — the current (v6.18) layout of the
  data page the vDSO code reads; the older `struct vdso_data` name from earlier kernels was split apart
  during a timekeeping-data reorganisation, and per-clock state now lives in `struct vdso_clock` arrays
  inside this struct rather than as flat fields.
- LWN, [*"On vsyscalls and the vDSO"*](https://lwn.net/Articles/446528/) — the history of why the
  fixed-address version had to go; older than the pinned kernel and still correct about the reasoning.
