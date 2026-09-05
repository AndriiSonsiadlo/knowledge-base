---
id: threaded-irqs
title: "Threaded IRQs"
sidebar_label: "Threaded IRQs"
sidebar_position: 7
tags: [linux, kernel, interrupts]
prerequisites:
  - linux/interrupts-time-and-deferred-work/workqueues
  - linux/scheduling/real-time-scheduling
draft: false
---

# Threaded IRQs

A quick primary handler plus a schedulable thread, and why PREEMPT_RT makes nearly every handler threaded.

[Hard IRQ Context](./hardirq-context.md) derived a whole table of prohibitions from one fact: a hard-IRQ
handler has no task of its own to suspend and resume, so it may not sleep, may not take a mutex, may not
allocate `GFP_KERNEL`. Every mechanism the rest of this folder covers is a way of getting the *work* out
of that context without breaking those rules. A threaded IRQ handler resolves the tension more directly
than any of them: instead of moving the work to an existing queue, it gives the interrupt **its own
dedicated kernel thread**, scheduled by the ordinary scheduler like any other task, free to sleep because
it has a real task identity to suspend. The cost is a wakeup and a context switch on every interrupt; for
the overwhelming majority of devices, whose interrupt rate is nowhere near what would make that cost
matter, it is a straightforward bargain.

## `request_threaded_irq`

`request_threaded_irq()` (`kernel/irq/manage.c`) takes two handler functions where `request_irq()` only
ever supplied one:

```c
int request_threaded_irq(unsigned int irq, irq_handler_t handler,
                          irq_handler_t thread_fn,
                          unsigned long flags, const char *name, void *dev);
```

- **`handler`** — the **primary handler**, which runs in true hard-IRQ context and is bound by every rule
  [Hard IRQ Context](./hardirq-context.md#the-rules-each-derived) derives. It should be close to trivial:
  acknowledge the device so the line stops asserting, read whatever must be captured before the device
  overwrites it, and return. Its normal return value here is `IRQ_WAKE_THREAD`, which is the signal to run
  `thread_fn`.
- **`thread_fn`** — the **thread function**, which runs later, in the interrupt's own kernel thread, in
  full process context.

Passing `NULL` for `handler` installs a default primary handler for you —
`irq_default_primary_handler()`, which is `{ return IRQ_WAKE_THREAD; }`, verbatim, in `kernel/irq/manage.c`.
This is the common case for a driver whose device needs no work done before the thread runs at all: skip
writing a primary handler, let the default one immediately hand off, and put everything in `thread_fn`.

## `IRQF_ONESHOT`

A level-triggered line stays electrically asserted for as long as the condition that raised it holds —
the device does not stop signaling just because the primary handler returned. If the line were left
unmasked the instant the primary handler finishes, and the thread function has not run yet, the still
-asserted line refires immediately and the primary handler runs again, and again, before the thread has
had any chance to do the work that would make the device stop asserting.

`IRQF_ONESHOT` is what closes this gap: it keeps the line **masked** until the thread function itself
finishes, not just until the primary handler returns. State it as a rule, because it is one: **a threaded
handler on a level-triggered interrupt with no real primary handler needs `IRQF_ONESHOT`, and omitting it
produces an interrupt storm** — the primary handler re-entered continuously, each invocation immediately
waking the thread again, the CPU consumed acking a line that never gets the chance to be actually serviced.
This is exactly the failure this page's `KernelFacts` trap below names.

## What the thread may do

Everything process context allows, because that is precisely what the thread has: `schedule()`, blocking
mutexes, `GFP_KERNEL` allocation, `copy_to_user()`/`copy_from_user()`, and I/O that waits for a device to
respond. This is the section that makes the mechanism attractive to driver authors rather than merely
correct: an I2C or SPI transaction in response to an interrupt is a routine, one-line call
(`i2c_smbus_read_byte_data()` and friends, which internally sleep waiting for the bus controller) inside a
threaded handler, and flatly **impossible** inside a hard-IRQ primary handler, which cannot wait for
anything. A touchscreen controller, a sensor with a data-ready line, or any device whose "read the actual
event" step goes back out over a slow bus is a natural fit — the primary handler acks the line and says
"wake the thread," and the thread does the bus transaction at its own, unhurried pace.

## Priority and latency

The thread runs `SCHED_FIFO`, and its default priority is **50**, verified directly against v6.18 source
rather than assumed: `irq_thread()` in `kernel/irq/manage.c` calls `sched_set_fifo(current)` before
entering its wait loop, and `sched_set_fifo()` (`kernel/sched/syscalls.c`) sets
`sched_priority = MAX_RT_PRIO / 2`. `MAX_RT_PRIO` is `100` (`include/linux/sched/prio.h`), so the resulting
priority is `100 / 2 = 50`, confirmed from the primitive the kernel actually calls rather than from
secondary material.

Fifty places an IRQ thread **above every `SCHED_NORMAL`/EEVDF task** — `SCHED_FIFO`/`SCHED_RR` priorities
1–99 always preempt `SCHED_NORMAL` unconditionally, as [Real-Time
Scheduling](../07-scheduling/real-time-scheduling.md#sched_fifo-and-sched_rr) covers — and **below any
higher-priority `SCHED_FIFO`/`SCHED_RR` task an administrator has set up**, which is deliberate: 50 is a
midpoint, not a ceiling, leaving room both above and below for a system integrator to place other RT work
relative to interrupt handling. `chrt` (or `sched_setscheduler()` directly) can retune an individual IRQ
thread's priority after the fact, per device, without touching the kernel.

The consequence worth stating plainly: **interrupt-triggered work now competes in the scheduler**, exactly
like any other task. That is both the benefit this page opens with — the work is visible in `ps`, subject
to the same accounting and preemption rules as everything else, no longer an opaque, unpreemptible region
— and the cost: its latency is no longer "however long the hardware takes to deliver an interrupt," it is
a genuine **scheduling latency**, subject to whatever else on the system is runnable at higher or equal
priority at that moment. A threaded handler that must never lose a race to some other RT task needs its
priority raised above that task's, deliberately, the same way any other latency-sensitive `SCHED_FIFO`
work would.

## `PREEMPT_RT` makes it universal

Every hard-IRQ handler is, by construction, one of [the non-preemptible
regions](../07-scheduling/preemption-models.md#where-the-kernel-is-never-preemptible) [Preemption
Models](../07-scheduling/preemption-models.md) identifies — and worst-case scheduling latency is bounded by
the longest such region anywhere in the kernel. Under
`PREEMPT_RT`, the response is direct: interrupt handlers are **threaded by default**, unless a driver
explicitly opts a specific handler out with `IRQF_NO_THREAD` (reserved for handlers that genuinely must run
in true hard-IRQ context — timer-like or otherwise latency-critical paths where even a thread wakeup is too
slow). A non-threaded handler is, definitionally, an unpreemptible region for however long it runs, and
therefore a hard lower bound on how good the system's worst-case latency can ever be; forcing nearly every
handler through a thread removes that bound for nearly every driver at once, at the cost of a wakeup per
interrupt. [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md#preempt_rt-in-one-section)
covers the rest of what `PREEMPT_RT` does alongside this — sleeping spinlocks and priority-inheriting
mutexes — of which forced threading is the interrupt-handling half.

## Seeing them

```text
$ ps -eo pid,pri,comm | grep 'irq/'
   312  91 irq/24-virtio0-
   318  91 irq/25-virtio0-
```

Each threaded interrupt has exactly one thread, named `irq/<N>-<devname>` for the IRQ number and (a
truncated form of) the requesting device's name — immediately identifiable in `ps` output, unlike a
softirq or a `kworker`, which carries no per-device identity at all. The `pri` column here is `ps`'s own
scale (`91` corresponds to real-time priority `50` under `ps`'s `1 + (99 - rtprio)` mapping for
`SCHED_FIFO`/`SCHED_RR` tasks — the `rtprio` column, not `pri`, is the one that reads `50` directly:
`ps -eo pid,cls,rtprio,comm | grep 'irq/'`). Because each thread is an ordinary, individually addressable
task, `chrt -p <pid>` reads or changes its priority on its own, independent of every other IRQ thread on
the system — genuinely useful when one device's interrupt latency matters more than another's and the
default midpoint priority does not reflect that.

## When not to thread

Threading is not free, and two categories of handler are better off not paying for it:

- **Very high interrupt-rate devices**, where the wakeup-and-context-switch cost per interrupt, multiplied
  across the interrupt rate, becomes real overhead in its own right. A fast NIC is the canonical example —
  rather than threading the per-packet interrupt path, it switches to **NAPI polling** once traffic is
  heavy enough (folder 13's networking material owns this mechanism; not yet written, named here only in
  prose), which amortizes many packets over one scheduling decision instead of one wakeup per packet.
- **Genuinely trivial handlers**, where the entire body of work is a register read and an acknowledgment —
  the wakeup and the thread's own scheduling overhead can exceed the cost of just doing the (tiny) work in
  hard-IRQ context directly. `IRQF_NO_THREAD` exists for exactly this case under forced-threading
  configurations.

Neither is a default; both are a measured decision for a specific device once threading has already proven
too expensive for it, not a starting assumption for a new driver.

```mermaid
sequenceDiagram
    participant Dev as Device
    participant P as Primary handler (hard IRQ)
    participant Sch as Scheduler
    participant T as IRQ thread

    Dev->>P: interrupt fires
    P->>P: acknowledge device, read minimal state
    P-->>Sch: return IRQ_WAKE_THREAD
    Note over P: Hard-IRQ context ends here — microseconds
    Sch->>T: wake_up_process(action->thread)
    Note over Sch: Thread scheduled like any SCHED_FIFO task,<br/>at priority 50 by default
    T->>T: thread_fn() — full process context
    Note over T: Interrupts fully enabled;<br/>may sleep, allocate, take mutexes, do I/O
```

*A threaded handler: two microseconds in interrupt context, and everything else in a thread the scheduler
can see.*

<KernelFacts
  structure={[["struct irqaction", "include/linux/interrupt.h"]]}
  path="interrupt → primary handler → IRQ_WAKE_THREAD → wake_up_process(action->thread) → irq_thread() → thread_fn(), verified at v6.18"
  observe="ps -eo pid,cls,rtprio,comm | grep 'irq/' | head"
  trap="A threaded handler on a level-triggered line without `IRQF_ONESHOT` produces an interrupt storm: the device keeps the line asserted, the primary handler keeps being re-entered, and the thread never gets to run." />

## References

- <Src file="kernel/irq/manage.c" symbol="request_threaded_irq" /> — the registration path, flag
  validation, and thread creation (`setup_irq_thread()`); `irq_thread()` in the same file is where
  `sched_set_fifo(current)` is called, the primitive this page's priority claim is verified against.
- [*Core-api: Genirq*](https://docs.kernel.org/core-api/genericirq.html), the threaded-handler section —
  the contract between the primary handler and the thread function, in the kernel's own words.
- LWN, [*Moving interrupts to threads*](https://lwn.net/Articles/302043/), Jake Edge, October 8, 2008
  — the original rationale from the `PREEMPT_RT` tree, from before the mechanism merged into mainline; the
  design is unchanged since.
- [Real-Time Scheduling](../07-scheduling/real-time-scheduling.md) and [Preemption
  Models](../07-scheduling/preemption-models.md) — the scheduling-class and non-preemptible-region context
  this page's "Priority and latency" and "`PREEMPT_RT` makes it universal" sections build on directly.
