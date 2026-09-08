---
id: real-time-scheduling
title: "Real-Time Scheduling"
sidebar_label: "Real-time"
sidebar_position: 9
tags: [linux, kernel, scheduling]
prerequisites:
  - linux/scheduling/runqueues-and-scheduling-classes
  - linux/scheduling/preemption-models
draft: false
---

# Real-Time Scheduling

The word misleads, so the definition has to come first: real-time does not mean *fast*. It means
*predictable*. A real-time policy trades average throughput for a bounded worst case, and a system tuned
for real time is frequently **slower on average** than the same system without it — every guarantee this
page describes is bought with cycles spent elsewhere.

## `SCHED_FIFO` and `SCHED_RR`

Both are static-priority policies: priorities 1–99, strictly above every `SCHED_NORMAL`/`SCHED_BATCH`/EEVDF
task regardless of nice value, and unaffected by vruntime or weight — a runnable `SCHED_FIFO` task at any
priority preempts a `SCHED_NORMAL` task unconditionally. The two differ only in what happens among tasks at
the *same* priority:

- **`SCHED_FIFO`** runs until it blocks, yields, or is preempted by a higher-priority task. No time slice,
  no forced rotation — first in, running until it gives the CPU back voluntarily.
- **`SCHED_RR`** adds a time quantum on top of the same rule: equal-priority `SCHED_RR` tasks round-robin
  against each other when the quantum expires.

In two lines: RR helps when two or more tasks genuinely share one priority level and must take turns
without one starving the others. In practice this is rarer than people assume — most real-time designs
give each task its own distinct priority precisely so this case never arises, leaving FIFO as the
overwhelmingly common choice.

## `SCHED_DEADLINE`

The interesting one. A `SCHED_DEADLINE` task does not declare a priority — it declares three numbers:
a **runtime** (how much CPU time it needs), a **deadline** (by when), and a **period** (how often). The
kernel does not take the task's word for it: at admission time it runs a schedulability test and either
accepts the task or refuses `sched_setattr()` outright.

Two mechanisms make the guarantee real:

- **The Constant Bandwidth Server (CBS).** Each deadline task's runtime budget is tracked live. If the task
  overruns its declared runtime within the current period, the CBS throttles it — it stops running, full
  stop, until its next period replenishes the budget. This is deliberate: a runaway deadline task is
  contained by the same enforcement mechanism that guarantees the well-behaved ones their share, rather
  than being allowed to steal cycles from someone else's guarantee.
- **Admission control.** Before a task is ever allowed to run under `SCHED_DEADLINE`, the kernel checks
  whether accepting it — added to every deadline task already admitted — still leaves a schedulable system.
  A task whose bandwidth would blow that budget is refused at `sched_setattr()` time, not allowed to run and
  discovered unschedulable later.

Say this plainly: `SCHED_DEADLINE` is the only scheduling policy in Linux that makes a **guarantee**
rather than a promise. `SCHED_FIFO` and `SCHED_RR` promise "highest priority runs first" — which is not the
same as promising a deadline is met, since nothing stops a higher-priority FIFO task, or a not-yet-admitted
set of FIFO tasks, from making a lower-priority one miss its own informal deadline. `SCHED_DEADLINE`'s
admission test is what turns "probably fine" into "provably fine, or refused before it started."

## Admission control, and why `sched_setattr` fails

The sum-of-utilisations test, worked through: each deadline task's utilisation is `runtime / period`. A
task with a 10 ms runtime and a 50 ms period has utilisation 0.2 — it needs 20% of one CPU, averaged over
its period. Admission sums the utilisations of every deadline task already admitted to a given scheduling
domain and refuses a new one if the total would exceed the available capacity (bounded below 1.0 per CPU,
with headroom reserved for non-deadline work — the exact bound is influenced by the kernel's runtime/period
global tunables, `sched_rt_runtime_us` and its deadline-specific analogue).

Concretely: three tasks each declaring `runtime=10ms, period=30ms` sum to a utilisation of 1.0 — a full
CPU, with nothing left over. A fourth task with any positive utilisation is refused; `sched_setattr()`
returns `EBUSY` (or `EPERM`/`EINVAL` depending on what specifically failed the check), not a silent
best-effort admission.

The practical note: on a multi-CPU system this accounting is done **per root domain** — the set of CPUs a
group of deadline tasks can be scheduled across, as partitioned by `cpuset`. This is precisely why `cpuset`
partitioning and deadline tasks interact: splitting CPUs into disjoint cpusets creates disjoint root
domains, each with its own independent admission budget. A deadline task set that would be refused as
oversubscribed on a single shared domain can become admissible once the CPUs are partitioned into smaller
domains that isolate it from unrelated load — and, just as easily, a task can be refused on a *partitioned*
system where the same aggregate CPU capacity, unpartitioned, would have accepted it.

## RT throttling

`SCHED_FIFO` and `SCHED_RR` have no deadline-style budget of their own — nothing stops a `SCHED_FIFO` task
from looping forever without blocking. RT throttling is the safety valve: by default, real-time tasks as a
class are limited to consuming `sched_rt_runtime_us` out of every `sched_rt_period_us` (95% of each period
by default — 950,000 out of 1,000,000 microseconds), leaving the remaining 5% guaranteed to non-RT tasks
regardless of what the RT class is doing.

When the throttle triggers, the RT class is simply not scheduled for the rest of the period — a spinning
`SCHED_FIFO` task loses the CPU outright, not gracefully, and a message may appear in `dmesg` noting the
throttling. Setting `sched_rt_runtime_us` to `-1` disables the throttle entirely; that is not a performance
tuning knob so much as a decision to accept an unrecoverable machine as a possible outcome, since nothing
then bounds how much of the CPU a misbehaving RT task can take.

:::warning
A `SCHED_FIFO` task that spins — never blocking, never yielding — on a machine with RT throttling disabled
and no spare CPU to migrate onto will make that machine **unresponsive to everything**, including the shell
you would use to kill it. There is no non-RT time left to schedule anything else, including the input path
of your own terminal. The QEMU lab is the right place to try this and watch it happen, rather than a
production machine or even this page's author's own terminal.
:::

## Priority inheritance

Unbounded priority inversion, in two sentences: a high-priority task blocks on a lock held by a low-priority
one, and if a medium-priority task then preempts the lock holder, the high-priority task waits not just for
the low-priority holder but indefinitely for however long the medium-priority task runs — priority order is
violated with no bound on how long the inversion lasts. `PTHREAD_PRIO_INHERIT` (POSIX) and the kernel's own
RT mutexes are the fix: the lock holder is temporarily boosted to the priority of the highest-priority
waiter for as long as it holds the lock, so a medium-priority task can no longer cut in front of the wait.
The lock side of this — how RT mutexes are actually implemented and used — is covered in
[Mutexes and Semaphores](../09-concurrency-and-locking/mutexes-and-semaphores.md).

## `PREEMPT_RT`, in one section

[Preemption Models](./preemption-models.md) already covers what `PREEMPT_RT` does mechanically: sleeping
spinlocks, threaded interrupt handlers, priority inheritance on (nearly) every lock. What it buys in
practice is an order-of-magnitude tighter worst-case latency bound — the PREEMPT_RT project's own
`cyclictest` measurements are typically reported in the tens-of-microseconds range for well-tuned hardware,
against worst cases in the hundreds of microseconds to low milliseconds for a non-RT kernel under load. The
throughput cost is real and not hidden: every spinlock acquisition now carries the overhead of a full
lock/unlock sequence with priority-inheritance bookkeeping instead of a bare atomic operation, so a
throughput-bound workload with little latency sensitivity is usually better off without it. Production
`PREEMPT_RT` tuning, deployment, and the embedded/industrial story belong to this repository's embedded
material, not yet written — named here in prose rather than linked, since no page exists there yet.

## Doing it properly

A real-time application is not "real-time" because it called `sched_setscheduler()`. The checklist that
actually gets a bounded worst case:

1. **Choose a policy** — `SCHED_DEADLINE` if the workload has a genuine periodic runtime/deadline
   shape and can state it; `SCHED_FIFO`/`SCHED_RR` otherwise.
2. **Set CPU affinity** so the task cannot be migrated onto a CPU that is busy with something else at the
   worst possible moment.
3. **Isolate the CPU**: `isolcpus` to keep the general scheduler off it, `nohz_full` to stop the periodic
   timer tick from interrupting it, and IRQ affinity steered away from it so interrupt handling for
   unrelated devices doesn't land on the isolated core.
4. **Lock memory** with `mlockall()` so the task's pages cannot be swapped out.
5. **Pre-fault the stack** — touch every page the task's stack will use before entering the time-critical
   section, so a page fault cannot happen there.
6. **Measure with `cyclictest`.** Not once — the whole point is the worst case over a long run, not the
   typical case over a short one.

Say plainly which step people skip: **memory locking**. Skipping `mlockall()` is the single most common
reason a "real-time" application still shows millisecond-scale outliers under otherwise-correct RT
scheduling — the outlier is a page fault, and a page fault takes the task off the CPU into a code path with
none of the guarantees this page just described, no matter how carefully the policy and priority were set.

```wavedrom title="A SCHED_DEADLINE task over three periods" alt="A deadline task consumes its declared runtime early in period one, overruns into period two and is throttled by the Constant Bandwidth Server, then behaves correctly in period three and is replenished exactly at the period boundary"
{
  signal: [
    { name: "period boundary",  wave: "10101010" },
    { name: "runtime consumed", wave: "01.0..1." },
    { name: "throttled",        wave: "0..1..0." },
    { name: "replenished",      wave: "0...10.1" }
  ]
}
```

*A deadline task that overruns: the Constant Bandwidth Server throttles it rather than letting it steal
the next task's guarantee.*

<KernelFacts
  structure={[["struct sched_dl_entity", "include/linux/sched.h"], ["struct sched_attr", "include/uapi/linux/sched/types.h"]]}
  path="sched_setattr() → __sched_setscheduler() → dl admission test → dl_sched_class → enqueue"
  observe="chrt -p 1 && cat /proc/sys/kernel/sched_rt_runtime_us && cat /proc/sys/kernel/sched_rt_period_us"
  trap="A real-time priority does not make a task fast. It makes it *first*, which is only useful if the task is also prevented from taking a page fault, waiting on a lock, or being migrated — and none of those follow from the policy." />

## References

- [Deadline Task Scheduling](https://docs.kernel.org/scheduler/sched-deadline.html) — the in-tree deadline
  documentation, including the admission test and the Constant Bandwidth Server description this page's
  "Admission control" section follows.
- `man 7 sched` — the policy definitions, priority ranges (1–99 for `SCHED_FIFO`/`SCHED_RR`), and the RT
  throttling parameters (`sched_rt_runtime_us`, `sched_rt_period_us`).
- [PREEMPT_RT documentation](https://wiki.linuxfoundation.org/realtime/documentation/start) — the project's
  documentation and the `cyclictest` methodology every claim about latency in "`PREEMPT_RT`, in one section"
  above should be checked against.
- `man 2 sched_setattr` — the only interface that can set a deadline task's runtime/deadline/period, and the
  reason `chrt` needs a version recent enough to expose it.
- <Src file="include/linux/sched.h" symbol="sched_dl_entity" /> and
  <Src file="include/uapi/linux/sched/types.h" symbol="sched_attr" /> — verified directly against Elixir at
  v6.18: both structs exist under these exact names, in these exact files, as the brief assumed.
  `kernel/sched/rt.c` at v6.18 was also checked directly and still registers `sched_rt_period_us` and
  `sched_rt_runtime_us` as live `procname` entries — neither sysctl has moved to a `/sys/fs/cgroup` interface
  at this version.
