---
id: hardirq-context
title: "Hard IRQ Context and Its Rules"
sidebar_label: "Hard IRQ context"
sidebar_position: 3
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/the-irq-subsystem
  - linux/concurrency-and-locking/why-kernel-concurrency-is-different
draft: false
---

# Hard IRQ Context and Its Rules

What a handler may not do, why each rule follows from the context, and the pressure that creates the rest of the folder.

Everything a hard-IRQ handler may not do follows from one fact, not from a list of conventions someone
wrote down. **The handler is not running on behalf of any task.** [How an Interrupt Reaches the
Kernel](./how-an-interrupt-reaches-the-kernel.md) already said it in passing — the handler borrows
whatever task was unlucky enough to be running — but this page takes that fact and derives its
consequences on purpose, because the consequences are the rules, not a separate policy layered on top
of them. If there is no task behind the handler, there is nothing to put on a wait queue, nothing to
charge blocked time to, and nothing to resume if it goes to sleep. Every prohibition below — no
sleeping, no mutex, no `GFP_KERNEL`, no `copy_to_user` — is the same fact restated for a different call.

## What "no task" means

`current` still points at *something* while a hard-IRQ handler runs — the kernel does not null it out —
but what it points at is the task that happened to be executing at the instant the interrupt landed, not
a task associated with the interrupt in any way. That task did not ask for the interrupt, does not know
it happened, and has no stake in what the handler does. The handler runs on top of it: on x86-64,
typically on a separate per-CPU IRQ stack reached via `run_irq_on_irqstack_cond()`, not even on the
interrupted task's own kernel stack, as [How an Interrupt Reaches the
Kernel](./how-an-interrupt-reaches-the-kernel.md#whose-stack-and-whose-time) covers.

This is why a hard-IRQ handler must never touch `current` as if it were "its own" task — putting
`current` to sleep, charging CPU time to it, or reading its credentials as if they belonged to the
interrupt would be corrupting an innocent bystander that happens to be standing nearby when the
interrupt fired. There is no task to block, wake up, or bill — only a stack and a CPU, borrowed for as
long as the handler runs.

## The rules, each derived

| Rule | What breaks it | Why |
|---|---|---|
| May not sleep / call `schedule()` | Calling a blocking function, or `schedule()` directly | `schedule()` means picking a different task and switching to it, which only makes sense if there is a task to switch *away from* — one with a wait queue entry and a place to resume. A hard-IRQ handler has no such task; it is not `current`'s own execution, it is a forced interruption of it. |
| May not take a `mutex_lock()` | Any sleeping lock primitive | A mutex blocks the caller when contended, and blocking is `schedule()` by another name. If the mutex is held, the handler has no task identity to suspend and resume when it becomes free. |
| May not allocate with `GFP_KERNEL` | `kmalloc(..., GFP_KERNEL)` under memory pressure | `GFP_KERNEL` permits the allocator to reclaim — write back dirty pages, wait for I/O to complete — and reclaim can sleep. The allocation call itself does not always sleep, but it is allowed to, and "allowed to" is enough to forbid it here. |
| May not `copy_to_user()` / `copy_from_user()` | Touching a user-space pointer directly | There is no meaningful user address space to speak of — `current`'s mm belongs to the task that was interrupted, not to any process associated with the interrupt — and the copy can fault, and a fault handler may need to bring in a page from disk, which sleeps. |

Every row's third column is a derivation from the same root fact, not a separate rule to memorize. This
table is the hard-IRQ row of the context matrix in [Why Kernel Concurrency Is
Different](../09-concurrency-and-locking/why-kernel-concurrency-is-different.md#the-context-matrix), and
the two must agree exactly: that page's "Hard-IRQ (interrupt handler) context" row says may not sleep, may
not take a mutex, may not allocate `GFP_KERNEL`, may not be preempted, use
`spin_lock_irqsave()`/`spin_unlock_irqrestore()` — which is precisely what this table derives from first
principles rather than states as given.

## What it may do

The escape hatch that makes everything else possible is **waking a task** — `wake_up_process()` or
equivalent does not require the *waker* to sleep, only marks a *different* task runnable and lets the
scheduler pick it up later, in process context, on its own time. Everything a hard-IRQ handler is
actually permitted to do either is this escape hatch or does not touch the "no task to suspend" problem
in the first place:

- **`GFP_ATOMIC` allocation** — never reclaims, never sleeps; it either succeeds immediately from what is
  already free or fails immediately. A handler that needs memory it cannot guarantee is already free
  should not be allocating in hard-IRQ context to begin with.
- **Spinlocks**, specifically the `_irqsave`/`_irqrestore` variants where the same lock is also taken from
  process context — see [the interrupt
  deadlock](../09-concurrency-and-locking/why-kernel-concurrency-is-different.md#the-interrupt-deadlock)
  for why a plain `spin_lock()` is not enough there. A plain `spin_lock()` is sufficient between one
  hardirq handler and the softirqs it raises, since softirqs cannot run while this handler is still on the
  CPU.
- **Per-CPU data**, touched without a lock at all when the handler is the only thing on this CPU that
  touches it — no other CPU is involved, and nothing preempts a hard-IRQ handler on its own CPU.
- **Atomic operations** — `atomic_t`, `READ_ONCE()`/`WRITE_ONCE()`, and friends never block by
  construction.
- **Waking a task** — the one operation above that reaches back into process context without the waker
  itself needing a task identity to suspend.
- **Scheduling deferred work** — `raise_softirq()`, `tasklet_schedule()`, or queuing a work item, each of
  which hands the actual work to a context that *can* meet the rules the handler cannot. This is the
  entire reason [the three deferral mechanisms](#the-three-deferral-mechanisms) below exist.

## Interrupts are disabled, so be quick

While a hard-IRQ handler runs, this CPU is not merely busy — under the non-nesting model [How an
Interrupt Reaches the
Kernel](./how-an-interrupt-reaches-the-kernel.md#nesting-and-why-linux-does-not) describes, it takes no
further maskable interrupts at all. Every microsecond spent in one device's handler is added directly to
the worst-case latency of every *other* device sharing that CPU: a network card, a disk controller, and a
timer can all be waiting behind a slow handler that has nothing to do with any of them. This is not a
throughput concern, it is a latency one — the cost is paid by unrelated hardware, not by the handler's own
device.

The practical target follows directly: a handler should acknowledge the device (so it stops asserting and
the controller can deliver the next one), pull out whatever data must be read before the device overwrites
it, and defer everything else — parsing, copying, computing, waking consumers — to a context where
interrupts are not disabled. "Everything else" is precisely the work [the three deferral
mechanisms](#the-three-deferral-mechanisms) exist to hold. This single pressure — *get off the CPU before
you cost someone else latency* — is the reason the rest of this folder exists as a folder at all, rather
than interrupt handling being one page.

## Measuring handler time

Three places to look, from cheapest to most detailed:

- **`/proc/interrupts`** — per-line, per-CPU counts. Rising counts on their own do not say how *long* each
  invocation took, but a line whose count is climbing fast on one CPU is the first thing to check when
  that CPU's `hi` figure looks high, exactly as [The IRQ Subsystem](./the-irq-subsystem.md#what-actually-happens)
  reads the file.
- **The `irq_handler_entry`/`irq_handler_exit` tracepoints** — `perf trace` or a small `bpftrace`/ftrace
  script against these two gives an actual entry-to-exit duration per invocation, per IRQ line, which
  `/proc/interrupts` cannot: a count is not a duration.
- **`hi` in `/proc/stat`** — the aggregate hardirq time for the whole CPU, the same field [How an
  Interrupt Reaches the Kernel](./how-an-interrupt-reaches-the-kernel.md#whose-stack-and-whose-time)
  introduces. It answers "how much of this CPU's time went to hardirq handling overall," not "which
  handler," but it is the number to watch for a trend before reaching for tracepoints to find the culprit.

Together these are enough to answer "is a handler too slow" with data: `/proc/interrupts` says which line
is busy, the tracepoints say how long each invocation actually takes, and `hi` says whether the aggregate
is trending in a direction worth investigating at all.

## Threaded handlers change all of this

Every rule above assumes the handler runs in true hard-IRQ context — non-preemptible, with no task
identity of its own. That is not the only way a registered handler can run: `request_threaded_irq()` can
hand the substantive work to a kernel thread instead, and a handler running in that thread *is* running in
process context, with a real `task_struct`, a real stack of its own, and every permission process context
has — it may sleep, take a mutex, allocate `GFP_KERNEL`. [Threaded IRQs](./threaded-irqs.md) covers the
mechanism; the point to take from here is narrower: the rules on this page are rules of hard-IRQ context,
not of "interrupt handling" as a concept, and `PREEMPT_RT` can afford to force nearly every handler through
a thread by default precisely because process-context rules are so much easier to reason about and compose
than hard-IRQ ones.

## The three deferral mechanisms

Given that a handler must get off the CPU quickly, the rest of this folder is the map of *where* the
deferred work goes. Three mechanisms, each trading a different amount of latency for a different amount of
freedom:

| Mechanism | Where it runs | Choose it when |
|---|---|---|
| [Softirq](./softirqs.md) | Same CPU, on the interrupt-exit path (or `ksoftirqd` under load) — still atomic, interrupts enabled | Work that must happen very soon and does not sleep — packet RX/TX processing, block I/O completion, timer expiry — and you are one of the fixed, compile-time softirq types, or building on top of one (tasklet). |
| [Tasklet](./tasklets-and-their-replacement.md) | Built on the `TASKLET`/`HI` softirqs, but serialised against itself | An open, driver-registerable interface to softirq-like execution was historically wanted, with the tasklet's own convenience guarantee (no concurrent execution with itself) in exchange for global serialisation. Deprecated — new code should not reach for this row. |
| [Workqueue](./workqueues.md) | A kernel thread, process context, may sleep | Work that can wait a little longer and needs to do something a softirq cannot — allocate `GFP_KERNEL`, take a mutex, block on I/O. |

<KernelFacts
  structure={[["preempt_count", "include/linux/preempt.h"], ["struct irqaction", "include/linux/interrupt.h"]]}
  path="irq_enter() sets the hardirq bits in preempt_count → in_interrupt() true → handler → irq_exit() → pending softirqs run"
  observe="grep -E 'CONFIG_DEBUG_ATOMIC_SLEEP' /boot/config-$(uname -r) && grep '^intr' /proc/stat | cut -c1-60"
  trap="The rules for interrupt context are not about speed. Calling a sleeping function there does not make the machine slow — it makes the scheduler try to switch away from a context that has nowhere to switch back to, which is a hang." />

## References

- [*Kernel Hacking Guide*](https://docs.kernel.org/kernel-hacking/hacking.html), the interrupt-context and
  "Recipes for Deadlock" sections — the in-tree statement of these rules with the same reasoning: no
  sleeping functions may be called without user context, without holding a spinlock, and with interrupts
  enabled — none of which a hard-IRQ handler has.
- [*Core-api: Genirq*](https://docs.kernel.org/core-api/genericirq.html) — the handler contract and what a
  flow handler expects of it, the software side [The IRQ Subsystem](./the-irq-subsystem.md) covers in
  structure.
- <Src file="include/linux/preempt.h" symbol="preempt_count" /> — the `preempt_count` field layout, the
  machine-readable definition of "in interrupt context" that `in_hardirq()` and friends read.
- <Src file="Documentation/kernel-hacking/locking.rst" /> — the locking rules per context, which this
  page's derivation table agrees with exactly.
