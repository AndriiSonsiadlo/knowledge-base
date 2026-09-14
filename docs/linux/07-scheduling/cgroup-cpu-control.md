---
id: cgroup-cpu-control
title: "cgroup CPU Control"
sidebar_label: "cgroup CPU control"
sidebar_position: 10
tags: [linux, kernel, scheduling]
prerequisites:
  - linux/scheduling/eevdf
draft: false
---

# cgroup CPU Control

Everything earlier in this folder schedules **tasks**. A container, a service, or a user session is a
*group* of tasks, and the interesting question shifts: how much CPU does that group get, regardless of how
many tasks happen to be inside it? Group scheduling answers this by making the hierarchy itself
schedulable — a cgroup competes for CPU the same way a task does, and the tasks inside it then compete for
whatever the group won.

## Group scheduling

A `task_group` owns one `cfs_rq` per CPU. The scheduler's pick decision becomes two-level: first pick a
group to run (by the same fair-scheduling logic that would otherwise pick a task directly), then pick a
task within that group's own runqueue. This is exactly why one process forking a hundred children does not
automatically get a hundred times the CPU — the hundred children still share their parent group's one slice
of CPU time; they only get more chances to be *the* task picked within it, not more aggregate CPU.

## `cpu.weight`

`cpu.weight` is the proportional control — cgroup v2's replacement for v1's `cpu.shares` — a single value
in the range **[1, 10000]**, default 100. (A `cpu.weight.nice` file exists alongside it, letting the same
control be set using ordinary `nice(2)` values, range [-20, 19], for anyone who thinks in nice terms
instead of raw weight.)

The mechanism: a parent's CPU time is distributed across its active children by weight ratio — each
child gets the fraction of the contended CPU matching its weight against the sum of weights of children
that currently want to run. Two things follow directly from "active" and "want to run" in that sentence:

- **What it guarantees:** a share of a *contended* CPU. If two sibling groups with equal weight both want
  the CPU, each gets half.
- **What it does not guarantee:** anything when the CPU is idle. `cpu.weight` is work-conserving — a group
  with a tiny weight gets the entire CPU to itself if no sibling group wants it at that moment. Weight only
  matters when something else is competing for the same CPU.

## `cpu.max`: quota and period

`cpu.max` is the hard cap, not a proportional share: a quota of microseconds the group may consume out of
every period. The file format is a single line, `"$MAX $PERIOD"` — for example `"50000 100000"` means the
group may consume 50,000 microseconds of CPU time out of every 100,000-microsecond period. The default
value is `"max 100000"`: no cap, with a 100 ms period already set, ready for a quota to be dropped in.

## What actually happens

Take a container with `cpu.max` set to `50000 100000` — a 50 ms quota per 100 ms period — running a
four-thread CPU-bound workload on a machine with CPU to spare. Four threads burning flat out consume 50 ms
of *aggregate* CPU time in about **12.5 ms of wall-clock time** (four threads in parallel, each contributing
roughly its share). At that point the quota for the period is exhausted, and **the entire group is
throttled for the remaining 87.5 ms of the period** — not slowed down, stopped. No thread in the group runs
again until the next period begins and the quota refills.

**Tried for real, on this page's own sandbox.** A delegated cgroup v2 subtree was writable here, so the
setup ran for real: a child cgroup was created, `cpu` was enabled in the parent's `cgroup.subtree_control`,
and `cpu.max` was set and read back —

```bash
echo "+cpu" > /sys/fs/cgroup/<delegated-path>/cgroup.subtree_control
mkdir /sys/fs/cgroup/<delegated-path>/throttle-demo
echo "50000 100000" > /sys/fs/cgroup/<delegated-path>/throttle-demo/cpu.max
```

```text
$ cat cpu.max
50000 100000
```

But moving a four-thread burner's PID into `throttle-demo/cgroup.procs` failed with a permission error even
though every file-permission bit on `cgroup.procs` allowed the write: `/proc/self/status` showed
`CapEff: 0000000000000000` in this sandbox — every capability dropped — and cgroup v2's `nsdelegate`
migration check requires more than file permission for a cross-hierarchy process move. The `cpu.stat` this
environment could actually produce is therefore real but empty, since no task ever joined the group to be
throttled:

```text
$ cat cpu.stat
usage_usec 0
user_usec 0
system_usec 0
nice_usec 0
nr_periods 2
nr_throttled 0
throttled_usec 0
nr_bursts 0
burst_usec 0
```

That is an honest negative result, not the demonstration. The shape `cpu.stat` takes on a machine where the
burner actually ran — documented behaviour, not measured here — is `nr_periods` incrementing once per 100 ms
window, `nr_throttled` incrementing on every one of those windows the four-thread workload saturates within
the first ~12.5 ms, and `throttled_usec` climbing by roughly 87,500 (microseconds) per throttled period —
consistent with the mechanism `throttle_cfs_rq()` implements, described in the KernelFacts path below.

The lesson, stated explicitly: a quota does not slow a workload down smoothly. It runs the workload at full
speed and then stops it dead, which turns a CPU *limit* into a **latency problem** — a request being
handled by a throttled thread doesn't get slower, it stalls completely until the next period.

Two mitigations follow, and one of them is counter-intuitive:

- **More threads is worse, not better.** More parallelism burns the same fixed quota in less wall-clock
  time, which means the group hits its throttle *sooner* in every period and spends *more* of the period
  stopped, not less.
- **A shorter period, or a higher quota, is better.** A shorter period (say 10 ms instead of 100 ms, with
  a proportionally smaller quota) throttles the group for a shorter absolute stall each time it exhausts its
  budget, turning one 87.5 ms stall into several much shorter ones. A higher quota is the direct fix when
  the workload's actual CPU need was simply underestimated.

This is, plainly, the single most expensive misunderstanding in container operations: a team sizes a CPU
limit by average utilisation, ships it, and then debugs mysterious multi-tens-of-milliseconds latency spikes
under load for weeks before finding `cpu.stat`.

## `cpu.pressure`

`cpu.pressure` is PSI (Pressure Stall Information) scoped to one cgroup: "how much time did the tasks in
this group spend runnable but waiting for CPU they wanted," reported as `some` (any task waiting) and `full`
(all tasks waiting simultaneously) percentages over 10/60/300-second windows. This is a materially better
overload signal than utilisation, because a group can show low average CPU utilisation while still stalling
badly — a bursty workload that is idle 90% of the time and throttled hard during its bursts looks fine on a
utilisation graph and terrible on `cpu.pressure`. Folder 15 owns cgroup v2 as a whole; this is enough to use
the CPU-specific file, not the full picture.

## The hierarchy, and who owns it

On a systemd-managed machine, systemd owns the cgroup tree. Writing to `cpu.max` or `cpu.weight` directly
under a systemd-managed unit's cgroup works right up until systemd itself reconciles the tree against unit
configuration and overwrites the change. The correct interfaces are unit directives, not raw cgroupfs
writes: `CPUWeight=` (maps to `cpu.weight`) and `CPUQuota=` (maps to `cpu.max`, expressed as a percentage of
one CPU rather than raw microseconds) in a unit file, applied with `systemctl set-property` for a live
change or in the unit file for a persistent one. See
[systemd in Practice and Boot Debugging](../03-boot-and-init/systemd-in-practice-and-boot-debugging.md) for
the boot-time and service-management side of the same tree.

## `cpuset` versus quota

| | Gives you | Right for |
|---|---|---|
| **`cpu.max` (quota)** | A fraction of CPU *time*, on any CPU, time-multiplexed with everyone else | Throughput-bound batch work where occasional multi-millisecond stalls are acceptable |
| **`cpuset`** | Specific CPUs, entirely — no other cgroup's tasks run there | Latency-sensitive work where a stall of any length is the actual problem being avoided |

A latency-sensitive workload almost always wants the second: a quota's throttle-then-stop behaviour is
exactly the failure mode a latency-sensitive workload cannot tolerate, whereas dedicated CPUs given by a
`cpuset` are never time-sliced away mid-burst by an unrelated group's quota accounting.

## Misconceptions

- **"A 0.5 CPU limit makes the app run at half speed."** It does not run at half speed — it runs at full
  speed for half of every period and is stopped completely for the other half. The average throughput may
  come out similar to "half speed" for a steady workload, but the latency profile is nothing like it: any
  single request that straddles the throttle boundary stalls for the rest of the period, which a smoothly
  halved clock speed would never do.
- **"More threads help under a quota."** They do the opposite: more parallel threads burn the same fixed
  quota faster, exhausting it sooner in the period and increasing — not decreasing — the fraction of the
  period spent throttled.
- **"`cpu.weight` limits a container."** It does not limit anything by itself. `cpu.weight` only changes
  the outcome when the CPU is *contended* — an otherwise-idle machine gives a low-weight container the
  entire CPU, exactly as it would a high-weight one, because there is no competing demand for the weight
  ratio to divide.

```wavedrom title="A CPU quota throttling a four-thread workload over two periods" alt="Two consecutive 100ms periods; in each, a four-thread workload burns its 50ms quota within the first 12.5ms of wall time and is then throttled for the remaining 87.5ms until the next period begins"
{
  signal: [
    { name: "period",              wave: "10101010", period: 2 },
    { name: "4 threads running",   wave: "010.....", period: 2 },
    { name: "quota (50ms/100ms)",  wave: "010.....", period: 2 },
    { name: "throttled",           wave: "0.10..10", period: 2 }
  ]
}
```

*A CPU quota is not a speed limit: the group runs flat out until the quota is gone, then stops until the
period rolls over.*

<KernelFacts
  structure={[["struct task_group", "kernel/sched/sched.h"], ["struct cfs_bandwidth", "kernel/sched/sched.h"]]}
  path="quota exhausted → throttle_cfs_rq() → group dequeued → period timer → unthrottle_cfs_rq()"
  observe="cat /sys/fs/cgroup/<path>/cpu.max && cat /sys/fs/cgroup/<path>/cpu.stat"
  trap="`nr_throttled` climbing means your workload is being stopped mid-flight, not slowed down. If a service has latency spikes and a CPU quota, check `cpu.stat` before anything else." />

## References

- [Control Group v2, CPU controller section](https://docs.kernel.org/admin-guide/cgroup-v2.html) — the
  authority for every file name and unit on this page. **Verified against the live document (not
  context7, which does not index kernel Documentation) by fetching
  `docs.kernel.org/admin-guide/cgroup-v2.html` directly on 2026-09-08**: confirmed `cpu.weight`'s [1, 10000]
  range and default of 100, `cpu.weight.nice`'s [-20, 19] range, `cpu.max`'s `"$MAX $PERIOD"` format and
  `"max 100000"` default, `cpu.stat`'s `nr_periods`/`nr_throttled`/`throttled_usec`/`nr_bursts`/`burst_usec`
  fields (the doc notes these five are non-hierarchical — they count only throttling caused by the cgroup's
  own limit, not an ancestor's), and `cpu.pressure` as the PSI file documented alongside
  `Documentation/accounting/psi.rst`.
- [PSI (Pressure Stall Information)](https://docs.kernel.org/accounting/psi.html) — what `cpu.pressure`
  measures and how to read `some` versus `full`.
- <Src file="kernel/sched/fair.c" symbol="throttle_cfs_rq" /> — the throttling itself; verified present
  under this exact name at v6.18 (`static bool throttle_cfs_rq(struct cfs_rq *cfs_rq)`), short enough that
  the all-or-nothing behaviour described above is visible by reading it directly.
- `man 5 systemd.resource-control` — the interface to use on any systemd-managed machine (`CPUWeight=`,
  `CPUQuota=`) instead of writing to the cgroup files directly.
