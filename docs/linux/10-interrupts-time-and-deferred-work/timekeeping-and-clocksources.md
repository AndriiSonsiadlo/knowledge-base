---
id: timekeeping-and-clocksources
title: "Timekeeping and Clocksources"
sidebar_label: "Timekeeping"
sidebar_position: 9
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel
related:
  - linux/concurrency-and-locking/seqlocks
  - linux/syscalls-and-the-boundary/the-vdso
draft: false
---

# Timekeeping and Clocksources

How a clocksource is chosen, what each `CLOCK_*` actually measures, and the lockless read path behind `clock_gettime`.

"What time is it?" looks like the easiest question a kernel answers. It is, in fact, one of the harder
ones, because the real requirement is not "return a number" but all of the following at once: the answer
must be produced billions of times a second across every CPU in the machine without becoming a
bottleneck; it must be monotonic when an interval is being measured, even though a human-facing wall
clock is not; it must survive the machine being suspended and resumed; it must be nudgeable by NTP a
tiny amount at a time rather than jumping; and it must agree across CPUs whose own hardware counters may
not agree with each other at all. Linux's answer is a layered one — a hardware counter underneath, a
seqlock-protected software structure on top of that, and a handful of different `CLOCK_*` identities for
callers who want different guarantees from the same underlying data — and nearly every point of confusion
about kernel timekeeping comes from collapsing those layers back into one.

## Two different jobs

Two kernel concepts get called "the timer" interchangeably, and they do opposite things:

- A **clocksource** *counts*. It is a free-running hardware counter that only ever increases, and the
  kernel's job is to read it and convert the reading into nanoseconds. A clocksource never interrupts
  anything by itself; it is passive, always available to be read, the way an odometer is always available
  to be read.
- A **clock event device** *interrupts*. It is a programmable timer that the kernel arms for a specific
  future moment — "fire in 4ms" — and that then raises an interrupt at approximately that moment. It is
  the thing behind both the periodic tick ([The Tick, and Living Without It](./the-tick-and-nohz.md)
  covers what runs on that interrupt) and every one-shot timer the kernel or a user-space caller asks for.

A single piece of hardware sometimes does both jobs (the local APIC timer on x86-64 can be either a
periodic clock event device or, in TSC-deadline mode, effectively both), and that overlap is exactly what
makes the distinction easy to lose. Keep them separate for the rest of this page: everything through "The
read path" below is about the clocksource, the thing that is *read*; [The Tick, and Living Without
It](./the-tick-and-nohz.md) is about the clock event device, the thing that is *armed*.

## Clocksources

| Clocksource | What it is | Typical resolution | Cost to read | Failure modes |
|---|---|---|---|---|
| TSC (Time Stamp Counter) | A free-running cycle counter built into each x86 core | Sub-nanosecond (CPU-cycle granularity) | One `rdtsc` instruction — a handful of cycles | See below: historically per-core, could stop in deep idle, varied with CPU frequency |
| HPET (High Precision Event Timer) | A platform timer block, separate from any CPU | ~10s of ns, defined by the HPET spec | An MMIO read — hundreds of cycles, an order of magnitude slower than `rdtsc` | Present but sometimes buggy on specific chipsets; slow enough to be a measurable `clock_gettime` regression when the kernel falls back to it |
| ACPI PM timer | A fixed-frequency (3.579545 MHz) counter exposed via ACPI | ~279 ns per tick | An I/O port read — among the slowest options, on the order of a microsecond | Low resolution and slow to read; used mainly as a fallback and as the watchdog's reference on some platforms |
| arm64 architected timer | A per-CPU counter mandated by the arm64 architecture itself, with a discoverable frequency register (`CNTFRQ_EL0`) | Sub-microsecond, frequency-dependent | A single system register read (`MRS`), comparable in cost to `rdtsc` | Architecturally guaranteed to exist and to be synchronized across cores — see [arm64](#arm64) below |

The TSC deserves its history, because the reasons it is the fastest clocksource *and* the one with the
most caveats are the same reasons: it lives on the core itself, so reading it costs nothing beyond an
instruction, but for exactly that reason it also used to inherit every quirk of the core it lived on.
Early TSC implementations ran at the CPU's current frequency, so a frequency change — which used to
happen constantly under power management — changed the rate the counter advanced, making it useless as a
stable clock across a frequency transition. Some CPUs also stopped the TSC entirely in deep idle
(C-states) to save power, which is precisely backwards for a clock: the counter needs to keep advancing
*especially* while the CPU has nothing else to do, since that is exactly when something else on the
system still wants to know the time. And because each core had its own counter, cores could drift apart
from each other with no guarantee of staying in sync, which is fatal for a value that gets compared
across CPUs constantly (a monotonic timestamp taken on CPU 2 must never appear to be *before* one taken a
moment earlier on CPU 5).

Modern x86 CPUs report two feature flags that say whether a given machine's TSC has these problems, and
both are simple to check:

```text
$ grep -o 'constant_tsc\|nonstop_tsc' /proc/cpuinfo | sort -u
constant_tsc
nonstop_tsc
```

(captured in this sandbox — a 12th Gen Intel Core i5, which reports both flags, as most CPUs from the
last decade do). `constant_tsc` means the counter advances at a fixed rate regardless of P-state; `nonstop_tsc`
means it keeps advancing through C-states, including deep idle. `arch/x86/kernel/tsc.c` (verified at
v6.18) gates the kernel's willingness to trust the TSC as a clocksource on exactly these
`X86_FEATURE_CONSTANT_TSC` / `X86_FEATURE_NONSTOP_TSC` bits — a CPU missing either one is a CPU whose TSC
the kernel will not fully trust without further checking.

## Selection

The kernel does not hardcode which clocksource to use; every registered clocksource carries a `rating`
(`struct clocksource::rating` in `kernel/time/clocksource.c`, verified at v6.18), and at boot the kernel
selects the one with the highest rating that is actually usable on the running hardware — the TSC rates
highest when its stability flags are present, HPET and the ACPI PM timer rate progressively lower, and
each exists as a fallback for the tier above it.

Selection is not a one-time decision. A **watchdog** clocksource (typically HPET or the ACPI PM timer,
something slower but trusted to be correct) periodically re-reads itself alongside the currently-selected
clocksource and checks that the two agree within a tolerance. If the primary clocksource drifts — a TSC
that turned out not to be as stable as its feature flags claimed, which does happen on some hardware
despite the flags — the watchdog demotes it, and the kernel falls back to the next-best rated clocksource
system-wide. `kernel/time/clocksource.c`'s watchdog path (verified at v6.18) logs exactly this event:

```text
Marking clocksource 'tsc' as unstable since watchdog ...
```

This is one of the highest-value single lines to notice in a boot log or `dmesg`, because of what it
implies silently: every `clock_gettime` call on that machine, from every process, just became roughly an
order of magnitude more expensive — from a `rdtsc` (a handful of cycles) to an HPET MMIO read (hundreds
of cycles) or an ACPI PM timer I/O port read (thousands) — and that cost lands on every caller, not just
the one that happened to trigger the demotion. A machine that seems to have gotten measurably slower at
anything timestamp-heavy, with no code change to explain it, is worth checking with
`dmesg | grep -i clocksource` before looking anywhere else.

## The read path

The structure actually read on every `clock_gettime`/`ktime_get()` call is the **timekeeper**
(`struct tk_core.timekeeper`, `include/linux/timekeeper_internal.h`) — it holds the current clocksource,
the last-read cycle count, and the multiplier and shift that convert a cycle delta into nanoseconds. It is
written once per tick by a single writer and read constantly by every CPU, which is exactly the access
pattern a [seqlock](../09-concurrency-and-locking/seqlocks.md) is built for: readers pay almost nothing —
no atomic instruction, no cache-line contention with other readers — at the cost of occasionally having to
retry if a write landed mid-read. `kernel/time/timekeeping.c`'s `ktime_get()` (verified at v6.18) is the
canonical instance of the retry loop:

```c
ktime_t ktime_get(void)
{
	struct timekeeper *tk = &tk_core.timekeeper;
	unsigned int seq;
	ktime_t base;
	u64 nsecs;

	WARN_ON(timekeeping_suspended);

	do {
		seq = read_seqcount_begin(&tk_core.seq);
		base = tk->tkr_mono.base;
		nsecs = timekeeping_get_ns(&tk->tkr_mono);

	} while (read_seqcount_retry(&tk_core.seq, seq));

	return ktime_add_ns(base, nsecs);
}
```

The protocol itself — why the retry loop is safe, what a reader may and may not do inside it — is
[Seqlocks](../09-concurrency-and-locking/seqlocks.md)'s job to explain and is not re-derived here. What
matters on this page is what gets read: `timekeeping_get_ns()` takes the raw clocksource delta since the
last update and applies the timekeeper's `mult`/`shift` pair — `(cycles * mult) >> shift` — a fixed-point
multiply chosen so the conversion is exact integer arithmetic with no floating point and no division on
the hot path. That `mult` value is also the value NTP adjusts (see below) to slew the clock without ever
touching `shift` or jumping the reported time.

## What actually happens

Follow one `clock_gettime(CLOCK_MONOTONIC, &ts)` call and see which of two very different paths it takes.

```mermaid
flowchart LR
    call["clock_gettime(CLOCK_MONOTONIC)"]
    check{"Clocksource<br/>vDSO-capable?"}
    vseq["seqlock read of<br/>the vvar page"]
    vread["rdtsc (or arch counter read)"]
    vmath["mult/shift → nanoseconds"]
    vret["return, no kernel entry"]
    sys["real syscall:<br/>sys_clock_gettime()"]
    kseq["read_seqcount_begin(&tk_core.seq)"]
    kread["clocksource->read()"]
    kmath["mult/shift → nanoseconds"]
    kret["return to caller"]

    call --> check
    check -->|yes| vseq --> vread --> vmath --> vret
    check -->|no| sys --> kseq --> kread --> kmath --> kret
```

*Two paths to the same nanoseconds, and the clocksource property that decides which one your machine
takes.*

If the active clocksource is **vDSO-capable** — practically, a TSC the kernel trusts (`constant_tsc`,
`nonstop_tsc`, and not demoted by the watchdog) — libc's `clock_gettime` never issues a syscall at all. It
calls straight into the vDSO's `__vdso_clock_gettime`, which takes a seqlock snapshot of the `[vvar]`
page (the same timekeeper data, mapped read-only into every process), executes a `rdtsc`, and does the
identical mult/shift arithmetic entirely in user space. [The vDSO](../05-syscalls-and-the-boundary/the-vdso.md)
covers this mapping and its `strace`-invisibility in full; this page's read path is the kernel-side half
of exactly the same seqlock protocol the vDSO runs in user space.

If the clocksource is **not** vDSO-capable — HPET or the ACPI PM timer, both of which need an actual MMIO
or I/O-port access only the kernel is set up to perform — the vDSO detects this and falls back to a real
syscall, landing in the same `ktime_get()`-style logic shown above, just running in the kernel instead of
in user space.

**Measuring the difference, for real.** This sandbox (a Hyper-V/WSL2 VM, 10 vCPUs, host CPU a 12th-Gen
Intel Core i5-12600KF) has no HPET among its available clocksources at all
(`cat /sys/devices/system/clocksource/clocksource0/available_clocksource` → `tsc hyperv_clocksource_tsc_page
hyperv_clocksource_msr acpi_pm`), and writing `current_clocksource` requires root, which this sandbox does
not have (`sudo -n true` fails with "interactive authentication required"). Rather than fabricate an HPET
number this environment cannot produce, here is a real measurement of the actual mechanism this section is
about — the vDSO fast path versus a forced syscall — using the currently-active `tsc` clocksource for
both, so the *only* variable is whether the read crosses the privilege boundary:

```text
vDSO path (libc clock_gettime): 15.4 ns/call (2,000,000 calls, 0.031 s total)
Forced syscall path (raw syscall(SYS_clock_gettime, ...)): 111.8 ns/call (2,000,000 calls, 0.224 s total)
Ratio (syscall / vDSO): 7.3x
```

(two-million-iteration loop, warmed up first, `CLOCK_MONOTONIC`, `-O2`; the raw-syscall variant calls
`syscall(SYS_clock_gettime, ...)` directly via `<sys/syscall.h>` to force a real kernel entry, bypassing
the libc wrapper's vDSO dispatch — reads the same TSC clocksource the vDSO path does, so this isolates the
cost of the privilege crossing itself). A real HPET read on top of that syscall path would add further
cost — an MMIO access is itself slower than the `rdtsc` this measurement's syscall path still performs
internally — so 7.3x is a floor for the vDSO-vs-HPET gap this section describes, not the whole of it; this
sandbox cannot produce the larger number honestly, so it is not invented here.

:::warning
Changing `current_clocksource` (via `clocksource=<name>` on the boot command line, or writing the sysfs
file at runtime where permitted) affects every process on the machine's timekeeping cost until it is
changed back — not just whatever is being benchmarked. Do this on a machine and window where a
system-wide `clock_gettime` slowdown is acceptable, not on anything shared or in production.
:::

The reader should leave this section with one rule: a "slow `gettimeofday`" bug report is, almost always,
a clocksource bug, not a `clock_gettime` bug — check `current_clocksource` before profiling the caller.

## The clock IDs

| Clock ID | Measures | Can jump? | Includes suspend? | Use for |
|---|---|---|---|---|
| `CLOCK_REALTIME` | Wall-clock time since the Unix epoch | Yes — NTP-adjusted and settable | Yes | Timestamping events for humans (log lines, file mtimes) |
| `CLOCK_MONOTONIC` | Time since an unspecified point (boot, on Linux) | No | No | Measuring elapsed intervals, timeouts, benchmarking |
| `CLOCK_BOOTTIME` | Identical to `CLOCK_MONOTONIC`, plus suspended time | No | Yes | Measuring intervals that must span a suspend/resume |
| `CLOCK_MONOTONIC_RAW` | Like `CLOCK_MONOTONIC`, but the raw hardware rate, with no NTP slewing applied | No | No | Rare: when even NTP's smooth micro-adjustments must be excluded |
| `CLOCK_REALTIME_COARSE` / `CLOCK_MONOTONIC_COARSE` | The same as their non-`_COARSE` counterparts, at tick granularity | Per their base clock | Per their base clock | Cheapest possible timestamp when millisecond resolution is enough |

(Definitions per `man 2 clock_gettime`, the authority for this table.) The selection rule this table
collapses to: measure an interval with `MONOTONIC` (or `BOOTTIME` if the interval must survive a suspend);
timestamp an event for a human or a log with `REALTIME`; reach for a `_COARSE` variant whenever the
caller's own resolution requirement is already coarser than a tick — which for logging, it usually is,
and the `_COARSE` variants are cheap enough that there is little reason not to use them once that's true.

## NTP, slewing, and leap seconds

`adjtimex()` is how NTP (or `chronyd`, or any other time-synchronization daemon) tells the kernel its
clock is running fast or slow relative to a reference. The kernel's response is not to jump
`CLOCK_REALTIME` to the corrected value — a visible jump would violate the "never goes backwards, rarely
jumps forward by much" expectation most software silently assumes — but to adjust the timekeeper's `mult`
value (the same multiplier `ktime_get()` uses in its mult/shift conversion above) very slightly, so the
clock runs a fraction faster or slower than the raw hardware rate until it converges on the correct time.
`CLOCK_REALTIME` moves smoothly through this correction; nothing about the read path above changes to
accommodate it.

Leap seconds are the one case NTP slewing does not paper over cleanly, because a leap second is a genuine
one-second discontinuity in civil time (UTC occasionally gains or loses a second to stay aligned with
Earth's rotation, which is not perfectly regular), and `CLOCK_REALTIME` is defined in terms of UTC. The
2012 leap-second insertion caused real, publicly documented production trouble — LWN's contemporaneous
report, [*"The leap second bug"*](https://lwn.net/Articles/504657/) (Jonathan Corbet, July 2, 2012),
describes load spikes traced to the leap-second insertion path, and the wider 2012 incident is
remembered industry-wide as the moment "leap second" stopped being a theoretical footnote for site
reliability teams. A kernel timer bug specific to that path was the proximate cause; the fix was a kernel
change, not an application one, which is precisely why this belongs on a timekeeping page and not a
"write correct NTP client code" page. Three years later, [*"Leap-second issues, 2015
edition"*](https://lwn.net/Articles/648313/) (Jonathan Corbet, June 17, 2015) covers the follow-up fix
and the debate over alternatives: `CLOCK_TAI` (International Atomic Time, which never has leap seconds —
it simply drifts a fixed, currently-37-second offset away from UTC) is the clock ID applications that
need to avoid leap-second discontinuities entirely should use instead of `CLOCK_REALTIME`; **leap
smearing** (spreading the one-second correction across many hours by running the clock very slightly
fast or slow, rather than inserting it as a discrete step) is the alternative some environments — famously
Google's public infrastructure — apply at the NTP-server level so client machines never see a
discontinuity at all. Both responses exist because a hard one-second jump backwards or forwards is exactly
the kind of event that breaks software's monotonic-time assumptions, the same assumptions `CLOCK_MONOTONIC`
exists to make it safe to hold.

## arm64

:::note[Architecture: arm64]
x86-64's clocksource story above is, in large part, a story about hardware that was never designed with
"be a reliable system clock" as a first-class requirement — the TSC's per-core drift and idle-state
stopping were consequences of a counter that existed for other reasons first. arm64 does not have this
drama, because the architecture itself mandates a **generic timer**: every core has an architected counter
(`CNTVCT_EL0`) with a defined, discoverable frequency (`CNTFRQ_EL0`), guaranteed by the architecture to be
synchronized across cores in a coherent system. There is no equivalent of "is this CPU's TSC actually
trustworthy" flag-checking dance, because trustworthiness is part of what conforming to the architecture
means. This is a genuine simplification arm64 gets essentially for free, not merely a different way of
arriving at the same place x86-64 does.
:::

<KernelFacts
  structure={[["struct clocksource", "include/linux/clocksource.h"], ["struct timekeeper", "include/linux/timekeeper_internal.h"]]}
  path="clock_gettime() → vDSO or syscall → read_seqcount_begin() → clocksource read → mult/shift → nanoseconds"
  observe="cat /sys/devices/system/clocksource/clocksource0/{available_clocksource,current_clocksource} && dmesg | grep -i clocksource"
  trap="CLOCK_MONOTONIC does not include time spent suspended. Measure an interval across a laptop lid close with it and you will get a number that is wrong by hours — CLOCK_BOOTTIME is the one that counts suspended time." />

## References

- [*Timers*](https://docs.kernel.org/timers/index.html) — the timekeeping documentation index,
  including the clocksource and clockevent descriptions this page draws its vocabulary from.
- `man 2 clock_gettime` and `man 7 time` — the clock IDs and their exact semantics, the authority for
  [The clock IDs](#the-clock-ids) table above.
- <Src file="kernel/time/timekeeping.c" symbol="ktime_get" /> — the read path with its seqlock retry
  loop, the code a `clock_gettime` call actually reaches when it does not take the vDSO fast path.
- LWN, [*"The leap second bug"*](https://lwn.net/Articles/504657/) (Jonathan Corbet, July 2, 2012) — the
  2012 leap-second production incident.
- LWN, [*"Leap-second issues, 2015 edition"*](https://lwn.net/Articles/648313/) (Jonathan Corbet, June 17,
  2015) — the follow-up fix, `CLOCK_TAI`, and the leap-smearing alternative.
