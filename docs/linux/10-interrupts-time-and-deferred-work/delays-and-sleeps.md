---
id: delays-and-sleeps
title: "Delays and Sleeps: What They Really Do"
sidebar_label: "Delays and sleeps"
sidebar_position: 12
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/timers-and-hrtimers
draft: false
---

# Delays and Sleeps: What They Really Do

Busy-wait delays, sleeping delays, and the guarantee every one of them lacks.

None of these functions delays for exactly the time you asked. Some burn the CPU for at least that long;
some sleep for at least that long and often considerably more; and knowing which family a given call
belongs to, and by roughly how much it will overshoot, is the difference between a driver that works and
a driver that works on the developer's own machine and nowhere else.

## Two families

- **Busy-wait delays** — `ndelay`, `udelay`, `mdelay` — spin in a loop, burning the CPU for the entire
  requested duration. They never call `schedule()`, never touch the run queue, and are safe to call from
  atomic context (inside a spinlock, in a hard-IRQ handler) precisely because they never give up the CPU.
- **Sleeping delays** — `usleep_range`, `msleep`, `schedule_timeout` — yield the CPU to the scheduler and
  arrange to be woken later. They are the only choice once "later" might be a while, but they require
  process context: a sleeping delay called from atomic context is exactly the "BUG: sleeping function
  called from invalid context" splat this folder's other pages have already covered.

The choice is forced by context first, duration second. In atomic context there is no decision to make —
a busy-wait is the only legal option, however long the wait — and only once process context is confirmed
does the actual duration start to matter.

## `udelay` and the loop calibration

`udelay` spins using a per-CPU calibrated delay loop (or, on hardware where it is trustworthy, a
cycle-counter-based measurement) until the requested number of microseconds has elapsed, holding the CPU
the entire time — no other work happens on that CPU while `udelay` runs, interrupts or not. `mdelay` is
`udelay` called in a loop scaled to milliseconds, and reaching for it in modern code is almost always a
mistake: a millisecond of busy-waiting is an eternity by CPU standards, and it is a millisecond that CPU
spent doing nothing else, including servicing other interrupts if it happened to be running with them
disabled.

The rule: busy-wait only in atomic context, only for short waits (roughly under ten microseconds), and
only when the hardware genuinely requires spinning rather than sleeping — a device register that settles
within a few clock cycles, not a device that merely happens to be slow.

## `usleep_range`, and why it takes a range

`usleep_range(min, max)` sleeps for at least `min` microseconds but not more than `max`. The range is not
kernel vagueness padded onto an otherwise precise API — it is the entire mechanism. At v6.18,
`usleep_range()` is a thin wrapper around `usleep_range_state()` (`kernel/time/sleep_timeout.c`), whose
own kernel-doc states the reason directly:

> The range might reduce power usage by allowing hrtimers to coalesce an already scheduled interrupt with
> this hrtimer. In the worst case, an interrupt is scheduled for the upper bound.

Concretely, `usleep_range_state()` programs an absolute hrtimer for `min` with a **slack** of `max - min`
(`schedule_hrtimeout_range(&exp, delta, HRTIMER_MODE_ABS)`), which tells the hrtimer subsystem "wake me
any time in this window" instead of "wake me at this exact instant" — and a wakeup that can happen
anywhere in a window is a wakeup the kernel can often fold into an interrupt that was going to happen
anyway for some other reason, avoiding a dedicated wakeup (and the CPU-idle exit that comes with one)
altogether. Passing an identical min and max — `usleep_range(1000, 1000)` — collapses the window to zero
and defeats this entirely: it forbids coalescing with anything, for no gain in accuracy, since the
function was never promising exact delivery in the first place. The kernel's own documentation
([*Timers Howto*](https://docs.kernel.org/timers/timers-howto.html)) says the same thing in its own words:
give `usleep_range` a real range unless there is a specific, stated reason not to.

## `msleep`, and its actual granularity

`msleep` is built on jiffies, not hrtimers, and its full body (`kernel/time/sleep_timeout.c`, verified at
v6.18) is three lines:

```c
void msleep(unsigned int msecs)
{
	unsigned long timeout = msecs_to_jiffies(msecs);

	while (timeout)
		timeout = schedule_timeout_uninterruptible(timeout);
}
```

`msecs_to_jiffies` rounds the requested duration up to a whole number of jiffies — at minimum, one full
jiffy, no matter how small `msecs` is — and `schedule_timeout_uninterruptible` then waits for the timer
wheel to expire that many jiffies, with the wheel's own coalescing slack (see [Timers and
Hrtimers](./timers-and-hrtimers.md#the-imprecision-is-deliberate)) layered on top. `msleep`'s own
kernel-doc comment quantifies the resulting slack precisely: "the maximum additional percentage delay
(slack) is 12.5%" for timers that land in level 1 or higher of the wheel, with an explicit worked
formula (`slack = MSECS_PER_TICK / msecs`) for the sub-one-tick case the "worst" case actually is.

The number that surprises people writing polling loops: **`msleep(1)` never sleeps for one millisecond.**
At `HZ=250` (`MSECS_PER_TICK` = 4 ms), `msecs_to_jiffies(1)` still rounds up to at least one jiffy, and the
wheel's own scheduling adds further slack on top — so a call asking for "1 ms" can, and routinely does,
take several times that in practice, and the exact multiple depends on both `HZ` and where in the current
tick the call happened to land. See [What actually happens](#what-actually-happens) below for a real,
measured version of this rather than a description of it.

## `schedule_timeout`

`schedule_timeout` is the primitive both `msleep` and every "wait for this or time out" helper are built
from. It requires the caller to set the task's state *before* calling it — this is the part that is easy
to get wrong, since skipping it silently changes the wait's behavior instead of failing loudly:

```c
set_current_state(TASK_UNINTERRUPTIBLE);
schedule_timeout(timeout_jiffies);
/* woken by the timer, or (if TASK_INTERRUPTIBLE) by a signal */
```

The standard higher-level pattern for "wait for this condition, or give up after this long" is
`wait_event_timeout(wq, condition, timeout)` (and its `_interruptible` variant), which handles the
state-setting and the race between the condition becoming true and the timeout expiring correctly, and is
almost always preferable to hand-rolling the `set_current_state()`/`schedule_timeout()` pair directly.

## What actually happens

Measure it, rather than take the granularity claim above on faith.

**The honest scope of this measurement.** The ideal experiment is a kernel module calling `msleep(1)` and
`usleep_range(1000, 2000)` directly, a thousand times each, and recording real elapsed time from inside
the kernel. That requires building and loading a module against a running kernel — and, per this project's
standing practice for this sandbox (see the lab notes on [Workqueues](./workqueues.md) and [The Tick, and
Living Without It](./the-tick-and-nohz.md#verifying-it)), there is no `qemu-system-x86_64` and no way to
build/load a module here, so that version was not attempted and no kernel-module numbers are fabricated to
fill the gap.

What was run instead, for real: a user-space C program calling `clock_nanosleep(CLOCK_MONOTONIC, 0, ...)`
in a loop, timing each call's actual wall-clock duration against a request of exactly 1 ms (1,000,000 ns)
and, separately, 1.5 ms (the midpoint of a `usleep_range(1000, 2000)`-shaped window), 1,000 iterations
each, on this sandbox (a Hyper-V/WSL2 VM, `CONFIG_HZ=250`, `CONFIG_PREEMPT_DYNAMIC=y` with
`CONFIG_PREEMPT_NONE` as the compiled-in default and no `preempt=` override on `/proc/cmdline`, 10 vCPUs
on a host 12th-Gen Intel Core i5-12600KF):

```text
1 ms request, 1000 samples (clock_nanosleep, CLOCK_MONOTONIC):
  min=1010508 ns  p50=1066313 ns  p90=1083518 ns  p99=1129740 ns  max=1240732 ns
  mean=1070425 ns  stddev=15181 ns
  → mean overshoot: +7.0% (+70 us) over the 1 ms request

1.5 ms request, 1000 samples:
  min=1513191 ns  p50=1572756 ns  p90=1587468 ns  p99=1605812 ns  max=1664279 ns
  mean=1573887 ns  stddev=11610 ns
  → mean overshoot: +5.0% (+74 us) over the 1.5 ms request
```

**Why this measures jitter, not the msleep-versus-usleep_range distinction, and that limitation is
disclosed rather than papered over.** Linux's user-space `nanosleep`/`clock_nanosleep` syscalls are
themselves implemented via `hrtimer_nanosleep()` (`kernel/time/sleep_timeout.c`) whenever
`CONFIG_HIGH_RES_TIMERS` is enabled, which is effectively always true on a modern kernel — so *both*
requests above actually take the hrtimer path, the same path `usleep_range` uses internally. There is no
user-space syscall that reaches `msleep`'s jiffy-rounding, tick-driven code path directly; that path only
exists inside the kernel. What this measurement demonstrates for real is the general overshoot and jitter
inherent to *any* sleep request — relevant on its own, since user-space code calling plain `nanosleep`
makes the identical "surely this sleeps for exactly what I asked" mistake this page opens with — but it
cannot, from user space alone, produce the sharper multi-millisecond overshoot `msleep(1)` specifically
exhibits from jiffy rounding. That number would require the kernel-module version above, which this
sandbox cannot run. Stating that limitation here is the point: the alternative would be inventing an
`msleep(1)` number and presenting it as measured, which this project's standing rule against fabricated
"real" output rules out.

```wavedrom title="A requested 1 ms wait: udelay, usleep_range, and msleep against the clock" alt="Timing diagram showing udelay finishing at exactly 1 ms with the CPU busy the whole time, usleep_range finishing close to 1 ms with the CPU yielded, and msleep overshooting to the next tick boundary"
{
  signal: [
    { name: "requested", wave: "10", data: ["1 ms requested"] },
    {},
    { name: "udelay(1000)",     wave: "10", node: ".a", phase: 0 },
    { name: "usleep_range",     wave: "10", node: ".b", phase: 0.1 },
    { name: "msleep(1)",        wave: "10", node: ".c", phase: 0.4 }
  ],
  edge: [
    "a-|> exact, CPU spinning the whole time",
    "b-|> close, CPU yielded (scheduler jitter only)",
    "c-|> overshoots to the next tick boundary"
  ]
}
```

*Same requested duration, three different actual endpoints: exact-but-blocking, close-but-yielded, and
rounded-up-to-the-tick.*

## The selection table

Mirrors the kernel's own [*Timers Howto*](https://docs.kernel.org/timers/timers-howto.html) guidance:

| Wait duration | Context | Call | Why |
|---|---|---|---|
| Under ~10 µs | Atomic (spinlock held, hard-IRQ) | `ndelay` / `udelay` | Only option available; too short for scheduling overhead to be worth it anyway |
| ~10 µs – 20 ms | Sleepable (process context) | `usleep_range(min, max)` | Yields the CPU; the range lets the kernel coalesce the wakeup |
| Over ~20 ms | Sleepable | `msleep` | Jiffy-based rounding is a small fraction of a duration this long, so the overshoot stops mattering |
| Waiting for an event, with a deadline | Sleepable | `wait_event_timeout` (or `_interruptible`) | Wakes early on the real condition; only falls back to the full timeout if the condition never becomes true |

## Polling hardware, done properly

`include/linux/iopoll.h` (verified at v6.18) provides the macro family that replaces a hand-rolled
"read a register, check a bit, sleep, repeat" loop:

- **`read_poll_timeout(op, val, cond, sleep_us, timeout_us, sleep_before_op, args...)`** and
  **`readx_poll_timeout(op, addr, val, cond, sleep_us, timeout_us)`** — sleep between polls
  (`usleep_range`-based), for sleepable context.
- **`read_poll_timeout_atomic(...)`** and **`readx_poll_timeout_atomic(...)`** — busy-wait between polls
  (`udelay`-based), for atomic context.
- Size-specific shorthands built on the `readx_*` forms for the common MMIO widths: `readb_poll_timeout`,
  `readw_poll_timeout`, `readl_poll_timeout`, `readq_poll_timeout` — each with a `_relaxed` variant
  (skipping the memory-barrier-heavy ordered accessor) and an `_atomic` variant, so `readl_poll_timeout_atomic`
  and `readl_relaxed_poll_timeout` both exist as distinct, precisely named macros rather than one macro with
  flags.

The reason to reach for these instead of a hand-written loop is not brevity for its own sake: it is
consistent timeout handling (every caller gets the same "did we actually time out" return convention) and
the sleep-versus-spin decision made once, at the macro's definition, instead of re-litigated — and
sometimes gotten wrong — at every call site that polls a register.

## Misconceptions

- **"`msleep(1)` sleeps for one millisecond."** It sleeps for at least one jiffy — never less — plus
  whatever wheel slack applies on top, and the [measured section above](#what-actually-happens) shows a
  double-digit percentage overshoot even for the far gentler hrtimer-backed case; `msleep`'s own
  jiffy-rounding path can be considerably worse at low `HZ`. Writing a polling loop that assumes
  `msleep(1)` gives millisecond-granularity timing is a bug that only shows up as flaky timing under a
  different `HZ` configuration than the one it was written against.
- **"`udelay` is more accurate, so use it for short waits generally."** It is accurate, and it is also
  burning a CPU core doing nothing else for the entire duration. That trade is only acceptable in atomic
  context, where there is no alternative — reaching for `udelay` in sleepable context because it "feels
  more precise" trades a real, ongoing cost (a busy CPU) for a benefit (tighter timing) that
  `usleep_range` already delivers closely enough for anything that isn't a true hardware deadline.
- **"A range in `usleep_range` means the kernel is being vague about it."** The range is the entire
  mechanism, not an apology for imprecision — it is what lets the kernel coalesce your wakeup with
  someone else's and avoid a dedicated interrupt. A zero-width range (`usleep_range(1000, 1000)`) costs
  power for no benefit and is not more precise than a real range; the function was never promising exact
  delivery either way.

<KernelFacts
  structure={[["struct hrtimer_sleeper", "include/linux/hrtimer.h"]]}
  path="usleep_range() → usleep_range_state() → schedule_hrtimeout_range(HRTIMER_MODE_ABS) → hrtimer with [min, max] slack → wakeup within the window"
  observe="zcat /proc/config.gz | grep -E 'CONFIG_HZ=|CONFIG_PREEMPT' (or /boot/config-$(uname -r) if /proc/config.gz is absent) — plus the measured distribution in What actually happens above"
  trap="usleep_range(1000, 1000) is not more precise than usleep_range(1000, 2000) — it just forbids the kernel from coalescing your wakeup with any other, which costs power and buys nothing the hardware could use." />

## References

- [*Timers Howto*](https://docs.kernel.org/timers/timers-howto.html) — the kernel's own decision
  guidance; this page's selection table agrees with it directly.
- <Src file="kernel/time/sleep_timeout.c" symbol="msleep" /> — the jiffy rounding, in three lines, which
  settles the granularity argument. (At v6.18 `msleep` lives in `kernel/time/sleep_timeout.c`, not
  `kernel/time/timer.c` where older references place it — the sleep/timeout helpers were split out of
  `timer.c` into their own file.)
- <Src file="include/linux/iopoll.h" symbol="readx_poll_timeout" /> — the polling idiom; the exact macro
  family (`read_poll_timeout`, `readx_poll_timeout`, and the size-specific/`_relaxed`/`_atomic` variants)
  confirmed present at v6.18.
- `man 2 nanosleep` and `man 2 clock_nanosleep` — the user-space counterparts used for the measurement
  above, and the reference for readers who assume user-space and kernel sleeps behave identically (they
  don't: user-space `nanosleep` is hrtimer-backed, `msleep` is not).
