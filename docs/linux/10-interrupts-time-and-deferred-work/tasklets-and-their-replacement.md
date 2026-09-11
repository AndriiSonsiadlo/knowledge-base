---
id: tasklets-and-their-replacement
title: "Tasklets, and Why They Are Going Away"
sidebar_label: "Tasklets"
sidebar_position: 5
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/softirqs
draft: false
---

# Tasklets, and Why They Are Going Away

The model, its serialisation guarantee, the problems that deprecated it, and what to use instead.

This is a page about a deprecated mechanism, and it is worth being honest about what that means for a
reader. Tasklets are still in hundreds of drivers across the tree — `grep -c tasklet /proc/kallsyms` on
almost any running kernel will not return zero — so meeting one while reading real driver code is likely,
not hypothetical. At the same time, `include/linux/interrupt.h` says plainly, in the comment directly
above the tasklet declarations: *"This API is deprecated. Please consider using threaded IRQs instead."*
Tasklets are the wrong choice for new code, but understanding exactly *why* they are wrong is instructive
about the whole deferral design space this folder covers — the trade they made is a trade that recurs
throughout kernel design, not a one-off mistake.

## What a tasklet is

A tasklet is a function scheduled to run in softirq context, built directly on top of the `TASKLET` and
`HI` softirqs [Softirqs](./softirqs.md) already covers — `tasklet_action()` and `tasklet_hi_action()` are
themselves softirq actions, registered with `open_softirq(TASKLET_SOFTIRQ, tasklet_action)` and
`open_softirq(HI_SOFTIRQ, tasklet_hi_action)`. Everything a softirq cannot do, a tasklet cannot do either
— it runs atomically, with interrupts enabled, unable to sleep.

What a tasklet adds on top of a bare softirq is one guarantee softirqs deliberately do not make: **the
same tasklet instance never runs concurrently on two CPUs.** `include/linux/interrupt.h`'s comment states
this as the defining property: *"tasklet is running only on one CPU simultaneously"* — in contrast to
generic softirqs, where, as [Softirqs](./softirqs.md#misconceptions) covers, the same softirq type
routinely runs on several CPUs at once. That guarantee is the tasklet's entire appeal: code inside a
tasklet callback can touch its own data without a lock protecting it *against itself*, because the kernel
will never let two invocations of that same tasklet overlap. A second `tasklet_schedule()` call while the
tasklet is already running does not start a second, concurrent invocation — it is deferred and coalesced
into one more run after the current one finishes.

## The API

- **`DECLARE_TASKLET(name, callback)`** / **`DECLARE_TASKLET_DISABLED(name, callback)`** — static
  declaration, the second starting with the tasklet's disable count already incremented (so it is
  scheduled but does not actually run until enabled). The `callback` here takes a `struct tasklet_struct *`
  — the modern signature.
- **`tasklet_setup(t, callback)`** — the modern dynamic-initialization counterpart, also taking the
  `struct tasklet_struct *` callback form.
- **`tasklet_schedule(t)`** / **`tasklet_hi_schedule(t)`** — mark the tasklet pending (`TASKLET_STATE_SCHED`)
  and, if it was not already pending, queue it onto this CPU's tasklet list and raise `TASKLET_SOFTIRQ` or
  `HI_SOFTIRQ` respectively. `HI` runs before other softirqs in a pass (`HI_SOFTIRQ` is enum value 0); it
  exists for the small number of tasklets that genuinely need to run ahead of everything else pending.
- **`tasklet_disable(t)`** / **`tasklet_enable(t)`** — `tasklet_disable()` increments a disable count and
  then *waits* for any currently-running invocation to finish (`tasklet_unlock_wait()`) before returning,
  so a caller can rely on the tasklet being genuinely quiescent afterward, not merely "asked to stop."
  `tasklet_enable()` decrements the count back.
- **`tasklet_kill(t)`** — waits for a pending-but-not-yet-run scheduling to be cleared and for any
  in-progress run to finish, then leaves the tasklet in a state where it will not run again until
  explicitly rescheduled. This is the teardown-path call, and its absence is the specific bug [Reading
  tasklet code you did not write](#reading-tasklet-code-you-did-not-write) below asks a reader to check
  for.

**The callback signature changed, and both forms exist in the tree at v6.18.** The original, still present
as `DECLARE_TASKLET_OLD(name, func)` / `DECLARE_TASKLET_DISABLED_OLD(name, func)` / `tasklet_init(t, func,
data)`, takes `void func(unsigned long data)` — an arbitrary `unsigned long` the caller stuffs with
whatever it needs, frequently a pointer cast through `unsigned long`, which is exactly the kind of
implicit, unchecked cast Kees Cook's modernization effort was aimed at removing. The modern form takes
`void callback(struct tasklet_struct *t)` and gets its own data back type-safely via `from_tasklet(var,
t, tasklet_fieldname)` — a `container_of()`-based macro that recovers the enclosing driver structure
from the embedded `tasklet_struct` pointer, no cast required. `struct tasklet_struct` itself carries both
call forms in a union (`func` vs. `callback`) plus a `use_callback` flag saying which one is live, so a
single struct definition supports drivers written against either era. This dual-signature state is exactly
the kind of thing that confuses a reader moving between an old driver and a new one side by side — seeing
`unsigned long data` in one file and `struct tasklet_struct *t` in the next is not a bug in either file, it
is the tree mid-migration.

## Why it is deprecated

Three concrete reasons, not a vague "it is old":

1. **The serialisation is global, not per-CPU, and it does not scale.** "Never runs concurrently on two
   CPUs" sounds like a convenience until a workload schedules the *same* tasklet from several CPUs at
   once under load: every CPU past the first has to wait for whichever CPU is currently running it,
   because the guarantee is a property of the tasklet instance, not of any one CPU. A per-CPU deferral
   mechanism that serialises *across* CPUs under exactly the conditions where CPUs would otherwise be
   doing independent work is fighting its own purpose, and the latency this adds is proportional to how
   many CPUs are contending for that one tasklet.
2. **A tasklet cannot sleep, so it does not simplify anything a bare softirq did not already offer.** The
   one thing tasklets add over registering a softirq action directly is the no-self-concurrency guarantee;
   every other constraint — atomic, no `GFP_KERNEL`, no mutex — is identical to plain softirq context. For
   a driver author who does not need that one guarantee, a tasklet buys nothing a workqueue or a threaded
   IRQ does not do better, and for one who does need it, the price is reason 1 above.
3. **The disable/kill lifetime rules are subtle enough that use-after-free bugs are common.** `tasklet_kill()`
   must be called before the structure a tasklet is scheduled on is freed, and it is easy to free the
   structure on a driver-remove path while a tasklet scheduled against it is still queued or running on
   another CPU — the callback then dereferences memory that is already gone. This is not a hypothetical:
   it is the specific bug pattern [Reading tasklet code you did not write](#reading-tasklet-code-you-did-not-write)
   asks a reader to hunt for, and it has been a recurring class of kernel security fix.

The kernel has been converting tasklets away for years rather than removing the API outright — Kees Cook's
callback-signature modernization (the source of the dual `func`/`callback` forms above) was itself one
step in that longer migration, not the end of it, and driver-by-driver conversion to workqueues, BH
workqueues, or threaded IRQs continues release over release.

## What to use instead

| Need | Use | Covered by |
|---|---|---|
| Work that must run very soon and stays atomic (no sleeping) | An existing softirq, or a threaded IRQ handler's quick primary half | [Softirqs](./softirqs.md), [Threaded IRQs](./threaded-irqs.md) |
| Work that may sleep — allocate `GFP_KERNEL`, take a mutex, block on I/O | A workqueue | [Workqueues](./workqueues.md) |
| Work with a deadline — "run this at/after time T" | An hrtimer | [Timers and hrtimers](./timers-and-hrtimers.md) |

None of these rows require the tasklet's specific "never concurrent with itself" property to get a correct
result — a workqueue can serialise its own work items with an ordered or single-threaded workqueue if that
property is actually needed, without paying the global-serialisation cost against *every* CPU
unconditionally.

## Reading tasklet code you did not write

Two questions to ask when a tasklet turns up in code under review or under debugging:

- **Does it rely on the serialisation guarantee?** If the callback touches shared state with no lock
  around it, that absence is not an oversight — it is very likely leaning on "this tasklet never runs
  concurrently with itself." Removing or replacing the tasklet without replacing that guarantee with an
  explicit lock reintroduces the race the tasklet was quietly preventing.
- **Does it have a `tasklet_kill()` on the teardown path?** Find where the structure holding the
  `tasklet_struct` is freed — module unload, device remove, error unwind — and confirm `tasklet_kill()` (or
  an equivalent wait) runs before that `kfree()`/`kmem_cache_free()`/structure teardown. **The specific bug
  to look for is a tasklet scheduled on a structure that gets freed without `tasklet_kill()` first** —
  `tasklet_schedule()` was called, the softirq that runs the callback has not fired yet (or is running on
  another CPU right now), and the memory it will dereference is already gone by the time it does.

## The lesson

Tasklets offered a guarantee — no concurrency with itself — that let driver authors skip a lock they would
otherwise have needed, and they paid for that guarantee with a *global* serialisation that hurts
precisely under the load conditions where a per-CPU deferral mechanism is supposed to help most. That
specific trade — "we made this simpler by making it effectively single-threaded" — is not unique to
tasklets; it is the same shape of trade that shows up whenever a design removes the need for explicit
synchronization by imposing an implicit one instead. The implicit version is easy to use correctly and easy
to scale badly, and knowing which of those two properties you are buying, on purpose, is the actual
decision — not "lock or no lock," but "explicit and scalable, or implicit and serialised."

| | Softirq | Tasklet | Threaded IRQ | Workqueue |
|---|---|---|---|---|
| Context | Atomic, interrupts enabled | Atomic, interrupts enabled (built on softirq) | Process context (kernel thread) | Process context (kernel thread) |
| May sleep? | No | No | Yes | Yes |
| Concurrent on multiple CPUs? | Yes, same type can run on several CPUs at once | No — serialised globally against itself | Yes, independent threads per handler | Yes, depending on workqueue's concurrency settings |
| Latency | Very low — runs on interrupt-exit path, almost immediately | Low, but degrades under cross-CPU contention on the same tasklet | Higher — a scheduling decision away | Higher still — queued, then scheduled |
| Status | Current — fixed set, actively used | Deprecated — being converted away | Current — the recommended atomic-then-sleepable split | Current — the recommended sleepable mechanism |

<KernelFacts
  structure={[["struct tasklet_struct", "include/linux/interrupt.h"]]}
  path="tasklet_schedule() → per-CPU tasklet list → TASKLET_SOFTIRQ → tasklet_action() → callback, with a per-tasklet RUN flag preventing concurrency"
  observe="grep -c tasklet /proc/kallsyms && cat /proc/softirqs | grep -i tasklet"
  trap="A tasklet's 'no concurrent execution' guarantee is global, not per-CPU. Under load, every CPU that schedules that tasklet is serialised behind whichever one is running it, which is the opposite of what a per-CPU deferral mechanism should do." />

## References

- <Src file="include/linux/interrupt.h" symbol="tasklet_struct" /> — the structure, the `func`/`callback`
  union and `use_callback` flag that support both callback eras, and the `TASKLET_STATE_SCHED`/
  `TASKLET_STATE_RUN` state flags that implement the serialisation.
- [*Modernizing the tasklet API*](https://lwn.net/Articles/830964/), Marta Rybczyńska, LWN.net, September
  14, 2020 — covers Kees Cook's callback-signature conversion and quotes Peter Zijlstra and Thomas
  Gleixner both wanting tasklets gone outright; the conversion described there is still ongoing at v6.18,
  not finished — the dual `_OLD` declaration macros and the `func`/`callback` union this page describes
  are the state that long transition has left the tree in.
- [*Core-api: Concurrency managed workqueues*](https://docs.kernel.org/core-api/workqueue.html) — the
  recommended replacement for the sleeping case, and the ordering/concurrency controls that can reproduce
  a tasklet's serialisation guarantee explicitly, on the one workqueue that needs it, instead of globally.
- <Src file="kernel/softirq.c" symbol="tasklet_action" /> — the dispatch loop, where `tasklet_trylock()`
  (setting `TASKLET_STATE_RUN`) and the re-queue-if-already-running path make the serialisation guarantee
  visible in code.
