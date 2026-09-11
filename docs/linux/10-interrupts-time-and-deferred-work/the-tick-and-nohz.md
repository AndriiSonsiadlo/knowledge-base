---
id: the-tick-and-nohz
title: "The Tick, and Living Without It"
sidebar_label: "The tick and NOHZ"
sidebar_position: 10
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/timekeeping-and-clocksources
related:
  - linux/scheduling/smp-load-balancing
  - linux/interrupts-time-and-deferred-work/interrupt-affinity-and-balancing
draft: false
---

# The Tick, and Living Without It

What the periodic tick was doing, what turning it off moves elsewhere, and CPU isolation for latency-sensitive work.

For decades the kernel was built on one assumption it eventually had to unlearn: a periodic timer
interrupt, firing at a fixed rate on every CPU, was simply how time got measured. It expired timers, it
accounted CPU usage, it decided whether the running task's slice was up, and a good deal of other
bookkeeping besides — all of it triggered by the same interrupt, `HZ` times a second, on every CPU,
forever. The trouble is that "forever, on every CPU" is a fixed cost paid whether or not there is
anything to do, and two very different audiences had good reasons to want it gone: battery-powered
devices, where an idle CPU waking up a hundred times a second to discover it has nothing to do drains the
battery for no benefit, and latency-critical workloads, where a periodic interrupt landing on a CPU
running one carefully-scheduled task is itself the disruption the workload cannot tolerate. [Timekeeping
and Clocksources](./timekeeping-and-clocksources.md) covered the clock event device that fires this
interrupt; this page is about what runs when it fires, and about the two different ways Linux has learned
to stop it from firing at all.

## What the tick did

Every one of these had to be re-homed somewhere else once the tick could no longer be relied on to run:

- **Update `jiffies`** — the tick's most basic job, incrementing the global counter that used to be the
  kernel's only notion of elapsed time.
- **Run expired timers** — anything scheduled with `timer_setup()`/`mod_timer()` whose deadline had
  passed got checked and fired on the tick.
- **Account CPU time to the current task** — the sample the scheduler's `top`/`ps`-visible CPU-time
  figures were historically built from.
- **Check whether the current task's timeslice is up** — deciding whether this tick is the one that
  should trigger a reschedule.
- **Drive RCU's quiescent-state detection** — the tick was one of the places RCU could confirm a CPU had
  passed through a point where it held no references into a structure being reclaimed.
- **Trigger load balancing** — periodically asking whether this CPU's runqueue is unbalanced relative to
  its neighbors.

Every section below this one is, in one way or another, the story of where each of these six things went
once the assumption that the tick would simply always be there stopped holding.

## `HZ`

`HZ` is a build-time constant — 100, 250, 300, or 1000, selectable via `Kconfig.hz` (verified at v6.18) —
that sets how many times a second the periodic tick fires on a CPU that has not stopped it. The trade is
the same one at every value: a higher `HZ` gives finer timer granularity and faster preemption response
(a task waiting on a short timeout, or one that should be preempted promptly, waits at most `1/HZ`
seconds for the next tick to notice), at the cost of more interrupts, more cache disturbance, and more
aggregate overhead across every CPU in the system. 100Hz favors servers and NUMA machines where that
overhead multiplies by CPU count; 1000Hz favors interactive and low-latency responsiveness. It is worth
saying plainly that `HZ` no longer determines scheduling *granularity* the way it once did — the
completely fair scheduler's notion of a task's fair share of CPU time is computed independently of the
tick rate; `HZ` still governs how often the tick's other jobs (timer expiry checks, accounting samples)
get a chance to run, but not the scheduler's underlying fairness calculation.

`jiffies` is the counter the tick increments, and it wraps — an `unsigned long`, so on a 32-bit build it
overflows in a matter of weeks even at a modest `HZ`. Comparing two jiffies values with a plain `<` or `>`
breaks exactly at that wraparound, which is why kernel code never does that: `time_after()`,
`time_before()`, and their `_eq` variants (`include/linux/jiffies.h`, verified at v6.18) do the comparison
as a signed subtraction instead of a direct relational comparison, which happens to produce the correct
answer across a wraparound as long as the two values being compared are within half the counter's range
of each other. Code that compares `jiffies` values directly instead of through these macros is a latent
wraparound bug, not a style nitpick.

## Dynticks-idle (`CONFIG_NO_HZ_IDLE`)

The simpler of the two tickless modes, and the one nearly every distribution kernel ships with enabled by
default: when a CPU goes idle and has no timer due in the near future, stop the periodic tick on that CPU
entirely rather than letting it keep firing into an empty runqueue. `tick_nohz_idle_enter()`
(`kernel/time/tick-sched.c`, verified at v6.18) is called from the idle loop and marks the CPU as
entering this state; the actual stop-and-reprogram happens when `tick_nohz_next_event()` computes the
soonest timer this CPU actually has pending and `tick_nohz_stop_tick()` reprograms the clock event device
as a single one-shot event for exactly that moment, instead of the next tick. If nothing is due for 40ms,
the CPU takes no timer interrupt for 40ms and can drop into a deep C-state for the whole interval — real
power saved, and on a virtualized host, real host CPU time not burned servicing a guest's idle-CPU tick a
hundred times a second for no reason.

The mechanism, restated in one sentence: **compute the next thing that actually needs to happen, and
program a one-shot timer for exactly that moment, instead of polling at a fixed rate and discovering
"nothing to do" most of the time.** Everything that follows in this page is a variation on that same
idea, applied to progressively harder cases.

## Full dynticks (`nohz_full`)

`CONFIG_NO_HZ_IDLE` stops the tick on an *idle* CPU, where the case for stopping it is easy: there is
nothing running, so there is nothing to preempt and nothing to account. Full dynticks is the more
ambitious version — stopping the tick on a **busy** CPU that has exactly one runnable task, on the
reasoning that with only one task there is also nothing to preempt *to* and nothing to balance against:
the scheduler has no decision left to make on that CPU until something changes.

The `Documentation/timers/no_hz.rst` file at v6.18 is explicit, and quoted here rather than paraphrased,
about what makes this possible and what it costs — these are the load-bearing constraints, taken verbatim:

> The CONFIG_NO_HZ_FULL=y Kconfig option causes the kernel to avoid
> sending scheduling-clock interrupts to CPUs with a single runnable task,
> and such CPUs are said to be "adaptive-ticks CPUs".

> By default, no CPU will be an adaptive-ticks CPU. The "nohz_full="
> boot parameter specifies the adaptive-ticks CPUs. For example,
> "nohz_full=1,6-8" says that CPUs 1, 6, 7, and 8 are to be adaptive-ticks
> CPUs. Note that you are prohibited from marking all of the CPUs as
> adaptive-tick CPUs: At least one non-adaptive-tick CPU must remain
> online to handle timekeeping tasks in order to ensure that system
> calls like gettimeofday() returns accurate values on adaptive-tick CPUs.
> [...] Note that this means that your system must have at least two CPUs
> in order for CONFIG_NO_HZ_FULL=y to do anything for you.

> Finally, adaptive-ticks CPUs must have their RCU callbacks offloaded.
> This is covered in the "RCU IMPLICATIONS" section below.

> CONFIG_NO_HZ_FULL selects CONFIG_NO_HZ_COMMON, so you cannot run
> adaptive ticks without also running dyntick idle. This dependency
> extends down into the implementation, so that all of the costs
> of CONFIG_NO_HZ_IDLE are also incurred by CONFIG_NO_HZ_FULL.

> The user/kernel transitions are slightly more expensive due
> to the need to inform kernel subsystems (such as RCU) about
> the change in mode.

> A reboot is required to reconfigure both adaptive idle and RCU
> callback offloading.

Stated plainly rather than quoted: full dynticks needs **at least one housekeeping CPU** that keeps a
normal tick and handles timekeeping for the whole machine (so the minimum useful configuration is two
CPUs, one housekeeping and one adaptive); the adaptive CPUs' **RCU callbacks must be offloaded**
(`CONFIG_RCU_NOCB_CPU=y`, and in practice the `rcu_nocbs=` boot parameter naming the same CPUs — the doc
also notes CPUs named by `nohz_full=` are automatically offloaded); every user/kernel boundary crossing on
an adaptive CPU gets slightly more expensive, because RCU and the accounting subsystems now have to be
told about the mode change on every transition instead of relying on the tick to notice eventually; and
none of this takes effect without a reboot, because reconfiguring RCU callback offloading at runtime is
not supported. This is, in the kernel documentation's own framing, a specialist configuration for
real-time and specific HPC workloads, requiring boot parameters and deliberate IRQ affinity work to pay
off — not a flag to flip on a general-purpose machine expecting a free win.

## Where the tick's work went

Every item from [What the tick did](#what-the-tick-did) above still has to happen; dynticks only changes
*when* and *how* it happens, not whether it happens at all:

| What the tick did | Where it went once the tick can stop |
|---|---|
| Update `jiffies` | The housekeeping CPU's tick still updates it; adaptive CPUs read it without needing to tick themselves |
| Run expired timers | A one-shot clock event, reprogrammed for the actual next expiry instead of polled every tick |
| Account CPU time to the current task | Context-switch-time and kernel-entry/exit accounting (`CONFIG_VIRT_CPU_ACCOUNTING_GEN`), sampled on the transitions themselves rather than on a periodic tick |
| Check whether the current task's slice is up | Moot with one runnable task — there is nothing else to switch to, so there is no decision the tick was making |
| Drive RCU's quiescent-state detection | Context-tracking entry/exit hooks mark the quiescent state directly on the user/kernel transition, and the CPU's callbacks are offloaded to "rcuo" kthreads elsewhere so this CPU never needs to notice on its own |
| Trigger load balancing | Left to the housekeeping CPU(s); an isolated CPU with one pinned task is not a load-balancing candidate in the first place |

This table is the page's actual payoff: dynticks is not "the kernel does less work," it is "the kernel
does the same work, but event-driven instead of polled, and with the housekeeping/offloading machinery
doing on a CPU's behalf what that CPU's own tick used to do for itself."

## CPU isolation, as a package

`nohz_full` alone stops the periodic interrupt. It does not, by itself, give a task a CPU nothing else
ever touches — and a CPU nothing else touches is usually the actual goal. Isolation is a small set of
mechanisms that need to be applied **together**:

- **`isolcpus`** — removes the named CPUs from the general scheduler's load-balancing candidate set, so
  the scheduler does not place *other* tasks onto them opportunistically. [SMP and Load
  Balancing](../07-scheduling/smp-load-balancing.md) covers the balancer this boot parameter opts a CPU
  out of.
- **`nohz_full`** — stops the periodic tick on those CPUs once they have exactly one runnable task, per
  the constraints quoted above.
- **`rcu_nocbs`** — offloads RCU callback processing off those CPUs, the prerequisite the `no_hz.rst`
  quote above states plainly is required for `nohz_full` to actually take effect.
- **IRQ affinity moved off the isolated CPUs** — device interrupts left on an isolated CPU are exactly
  the involuntary interruption isolation exists to prevent; [Interrupt
  Affinity](./interrupt-affinity-and-balancing.md) covers `smp_affinity`/`smp_affinity_list` and the
  `-EPERM` case for managed interrupts that refuse to move.
- **Pinning the workload itself** onto the isolated CPUs (`taskset`, `sched_setaffinity()`, or a cgroup
  cpuset) — without this, the "one runnable task" condition `nohz_full` depends on is never actually met
  by the workload the isolation was set up for.

These are **one configuration, not four independently-useful ones**. Doing three of the five gives most
of the cost — the `nohz_full` boot parameter's user/kernel-transition overhead applies as soon as it is
set, `rcu_nocbs` moves callback-processing work elsewhere on the machine, `isolcpus` changes load-balancer
behavior everywhere — and little of the benefit, because a single stray interrupt or a single
unpinned background task landing on the "isolated" CPU defeats the entire point: the tick does not
actually stop, because the CPU never reaches the single-runnable-task condition the whole mechanism is
conditioned on.

## Verifying it

Don't take a `nohz_full` configuration's word for itself — check whether the tick actually stopped, with
a number rather than a claim:

- **`/proc/interrupts`, the local-timer row, per CPU, under load.** Capture it, run the pinned workload
  for a measured interval, capture it again. A housekeeping CPU's local-timer count climbs by roughly
  `HZ × seconds elapsed`; a correctly-isolated `nohz_full` CPU running one task shows a count that barely
  moves for the same interval — a handful of ticks rather than thousands.
- **Tracepoints**, if the kernel has `CONFIG_NO_HZ_FULL` enabled — the `tick_stop` tracepoint fires each
  time a CPU's tick is actually stopped, giving a direct, per-event confirmation rather than an inferred
  one from interrupt counts.

The number to look at is the local-timer interrupt count delta over a measured window, per CPU — not
whether `nohz_full=` appears on the command line, which says only what was *requested*, not what actually
happened.

```wavedrom title="Local-timer interrupts on two CPUs, same interval" alt="A housekeeping CPU ticks steadily throughout the interval; a nohz_full CPU running one task shows only a handful of ticks"
{
  signal: [
    { name: "CPU0 (housekeeping)", wave: "222222222222222222" },
    {},
    { name: "CPU3 (nohz_full, 1 task)", wave: "2.............2..." }
  ]
}
```

*The same second on two CPUs: a thousand timer interrupts on one, and a handful on the other.*

:::info[Measurement disclosure]
This sandbox (a WSL2/Hyper-V VM) has no `nohz_full` CPUs configured — `cat /proc/cmdline` here shows no
`nohz_full=`, `isolcpus=`, or `rcu_nocbs=` parameters, and setting them up requires a reboot with new boot
parameters, which this sandbox's environment does not support. The wavedrom diagram above illustrates the
*shape* `/proc/interrupts` takes on a correctly isolated machine, per the verification method just
described — it is not a captured trace, and is presented as illustrative, not as a real capture, per this
project's standing rule against fabricated "real" output.
:::

<KernelFacts
  structure={[["struct tick_sched", "kernel/time/tick-sched.h"], ["struct clock_event_device", "include/linux/clockchips.h"]]}
  path="idle or single task → tick_nohz_idle_enter() / tick_nohz_full_update_tick() → tick_nohz_next_event() computes next expiry → tick_nohz_stop_tick() programs a one-shot clock event"
  observe="grep -E 'LOC|Local timer' /proc/interrupts && cat /proc/cmdline"
  trap="nohz_full on its own usually makes things worse. Without rcu_nocbs, isolated IRQ affinity, and a pinned single-task workload, the tick does not actually stop and you have paid the accounting overhead for nothing — check the local-timer count per CPU rather than assuming." />

## References

- [*NO_HZ: Reducing Scheduling-Clock Ticks*](https://docs.kernel.org/timers/no_hz.html) — the definitive
  in-tree document; the source of every verbatim quote in [Full dynticks](#full-dynticks-nohz_full) above,
  and the authority for this page's constraint list.
- [*Kernel command-line parameters*](https://docs.kernel.org/admin-guide/kernel-parameters.html) — the
  exact syntax and interaction of `isolcpus`, `nohz_full`, and `rcu_nocbs`.
- <Src file="kernel/time/tick-sched.c" symbol="tick_nohz_idle_enter" /> — where a CPU marks itself as
  entering the idle-tickless state; `tick_nohz_stop_tick()` in the same file is where the one-shot event
  is actually programmed.
- LWN, [*"(Nearly) full tickless operation in 3.10"*](https://lwn.net/Articles/549580/) (Jonathan Corbet,
  May 8, 2013) — early coverage of `CONFIG_NO_HZ_FULL` landing; usability and the tooling around
  `isolcpus`/`rcu_nocbs` have both improved substantially in the years since this article, which should be
  read as a snapshot of the feature's difficult early state rather than its current one.
