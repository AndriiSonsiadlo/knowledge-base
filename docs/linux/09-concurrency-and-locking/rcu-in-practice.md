---
id: rcu-in-practice
title: "RCU in Practice"
sidebar_label: "RCU in practice"
sidebar_position: 9
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/rcu-the-idea
draft: false
---

# RCU in Practice

The API, the ordering it encodes, and the rules that make RCU misuse silently fatal rather than loudly wrong.

[RCU: The Idea](./rcu-the-idea.md) covers why RCU works; this page is separate because knowing why it
works doesn't tell you how to avoid breaking it. RCU's rules are few, but they're unforgiving in a
specific way that most locking bugs aren't: a broken lock invariant usually shows up as a deadlock or a
lockdep splat within seconds of the buggy path running. Broken RCU usage typically doesn't show up at
all — the code works in every test, under every review, for months, and then corrupts memory once under
production load, at the exact moment a writer frees an object a reader is still holding. Using RCU
correctly is mostly a matter of knowing the handful of things you may not do, because nothing at runtime
will remind you.

## The reader side

```c
rcu_read_lock();
p = rcu_dereference(gp);
if (p)
    do_something_with(p->field);
rcu_read_unlock();
```

Three calls, always in this order: `rcu_read_lock()` marks the start of the critical section,
`rcu_dereference()` fetches the pointer with the ordering `rcu_dereference` needs to guarantee a reader
never observes an under-initialized object (see [Publishing safely](./rcu-the-idea.md#publishing-safely)),
and `rcu_read_unlock()` marks the end. The rule that matters most: **any pointer obtained via
`rcu_dereference()` inside the section is invalid the instant `rcu_read_unlock()` runs.** Nothing enforces
that at the type level — `p` is a perfectly ordinary pointer to the compiler — so the discipline is
entirely on the programmer: use it, or take a reference that outlives the section (a refcount bump before
unlocking), but never simply hold onto the raw pointer past the unlock and assume it's still good.

## The writer side

```c
struct foo *new, *old;

spin_lock(&foo_lock);           /* writers still serialize among themselves */
old = rcu_dereference_protected(gp, lockdep_is_held(&foo_lock));
new = kmalloc(sizeof(*new), GFP_KERNEL);
*new = *old;                    /* copy */
new->field = updated_value;     /* modify the copy, not the original */
rcu_assign_pointer(gp, new);    /* publish */
spin_unlock(&foo_lock);
kfree_rcu(old, rcu);            /* dispose of the old version */
```

The writer needs an ordinary lock against other writers — RCU has nothing to say about that side of the
problem, see [What RCU does not give you](./rcu-the-idea.md#what-rcu-does-not-give-you) — and inside that
lock it follows read-copy-update literally: read the current version, copy it, modify the copy,
`rcu_assign_pointer()` to publish, then dispose of the old version. `rcu_dereference_protected()` above is
the update-side counterpart to `rcu_dereference()`: it fetches the pointer without the read-side memory
barrier, which is safe here specifically because the update lock already rules out concurrent writers —
using plain `rcu_dereference()` on the writer side works but pays for ordering guarantees the writer
doesn't need, since it isn't racing against other writers under its own lock.

## Three ways to dispose

| Call | Blocks the caller? | Allowed in atomic context? | Choose it when |
|---|---|---|---|
| `synchronize_rcu()` | Yes — blocks for a full grace period | No | The writer can afford to wait and wants the old version gone before it continues (e.g. before returning from an unregister function the caller expects to be safe to `kfree()` after). |
| `call_rcu()` | No — registers a callback and returns immediately | Yes | The disposal logic is more than a single `kfree()` — closing a file, releasing a chain of sub-objects — and the writer cannot afford to block. |
| `kfree_rcu()` | No | Yes | The common case: disposal is exactly one `kfree()` of the object itself, and there's no other cleanup to write a callback for. |

`kfree_rcu()` exists specifically to remove the boilerplate of writing a one-line callback function whose
entire body is `kfree()` — it takes the object pointer and the name of its embedded `rcu_head` member and
handles the rest, batching frees internally rather than scheduling a separate callback per object.

## RCU-protected lists

`list_add_rcu()`, `list_del_rcu()`, and `list_for_each_entry_rcu()` are the RCU-safe counterparts of the
ordinary intrusive-list primitives covered in
[Kernel Data Structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md). The subtlety
that makes deletion safe under concurrent traversal: `list_del_rcu()` poisons the removed entry's `prev`
pointer, exactly like the ordinary `list_del()` poisons both, but deliberately leaves the entry's `next`
pointer intact. A reader that's already mid-traversal and sitting on the entry being removed follows
`next` to keep going — poisoning it would send that reader into a garbage address the instant a writer
deleted anything out from under it. Because readers only ever walk forward, only the backward pointer
needs to become unusable; the forward one has to stay valid for exactly as long as a reader that started
before the deletion might still be using it, which is precisely as long as RCU already guarantees.

## The rules you must not break

1. **Do not sleep in a classic RCU read-side critical section.** Sleeping while non-preemptible (or while
   holding the per-task counter under `CONFIG_PREEMPT_RCU`) can stall the grace period the sleeping task
   itself would need to resume, and in a non-preemptible configuration it's an outright bug — the CPU
   can't be rescheduled while `rcu_read_lock()` is in effect. SRCU exists for exactly the case where a
   reader genuinely needs to block (see below).
2. **Do not let a pointer obtained via `rcu_dereference()` escape the critical section.** Once
   `rcu_read_unlock()` runs, nothing guarantees the object it pointed to is still there — a writer racing
   ahead may have already reclaimed it the moment the grace period it was waiting on elapsed.
3. **Do not free the old version without first waiting for a grace period.** Skipping straight to
   `kfree()` after `rcu_assign_pointer()` reintroduces the exact use-after-free RCU exists to prevent — a
   reader that started just before publication still holds a valid reference to the old version and has
   no way to know it was just freed underneath it.
4. **Do not call `rcu_dereference()` outside a read-side critical section, or on the update side without
   holding the update lock.** `rcu_dereference()`'s ordering guarantee assumes it's being called somewhere
   RCU is actually tracking as a reader; on the update side, where a lock already rules out concurrent
   writers, use `rcu_dereference_protected()` instead — it documents, and under `CONFIG_PROVE_RCU_LIST`
   / lockdep-backed checks can verify, that the caller holds the lock it claims to.
5. **Do not assume a grace period bounds anything other than pre-existing readers.** A grace period says
   nothing about how long an object has been unreferenced, how many writers have run since, or any
   ordering property beyond "every reader that could have seen the old version is now done." Treating it
   as a general-purpose timeout for anything else is a category error waiting to become a bug.

## SRCU

Sleepable RCU relaxes rule 1 above at a real cost: an SRCU reader may block inside its critical section —
across I/O, across a mutex, anywhere a classic RCU reader may not go — because each SRCU domain
(`struct srcu_struct`, declared and initialized separately from the global RCU state) tracks its own
grace periods independently, rather than folding into the single global mechanism every classic-RCU reader
participates in. That independence is what makes sleeping safe: an SRCU domain's grace period only has to
wait out readers of *that* domain, so one subsystem's readers blocking doesn't stall grace periods
anywhere else in the kernel the way a sleeping classic-RCU reader would. The price is a read side that's
no longer nearly free — `srcu_read_lock()` does real per-CPU bookkeeping, not just a preemption-disable or
a plain counter increment. Reach for SRCU specifically when a reader must do something a classic RCU
reader is forbidden from doing — typically genuine I/O, or taking a mutex — not as a general-purpose
drop-in replacement for ordinary RCU; the extra read-side cost is real and it's only worth paying when the
sleeping requirement is real too.

## RCU flavours, briefly

The API surface looks like it offers several independent flavours — `rcu_read_lock()`,
`rcu_read_lock_bh()` (also disables softirqs), `rcu_read_lock_sched()` (also disables preemption) — but as
of the current tree these all participate in the *same* underlying grace-period detection; the `_bh` and
`_sched` variants exist for lockdep-checking and softirq/preemption-disabling purposes on the read side,
not because they wait for a separately-tracked kind of grace period the way SRCU does. Genuinely separate
grace-period machinery exists for three further cases, gated by their own Kconfig options:

- **Tasks RCU** (`CONFIG_TASKS_RCU`) — a quiescent state is a voluntary context switch; used for tracing
  and BPF infrastructure that needs to wait for every task to pass through a scheduling point.
- **Tasks Rude RCU** (`CONFIG_TASKS_RUDE_RCU`) — a quiescent state is *any* context switch, voluntary or
  not; a narrower, specialized variant used internally by the tracing infrastructure.
- **Tasks Trace RCU** (`CONFIG_TASKS_TRACE_RCU`) — uses explicit `rcu_read_lock_trace()` read-side
  markers rather than riding on context switches at all; built for BPF's need to protect programs and
  maps against removal while trace-context readers may be running.

And **SRCU** (`CONFIG_TREE_SRCU` / `CONFIG_TINY_SRCU`, above) is its own thing entirely, with independent,
per-domain grace-period tracking. Unless working on tracing, BPF, or SRCU-specific code directly, the
classic API — `rcu_read_lock()` / `rcu_assign_pointer()` / `synchronize_rcu()` / `call_rcu()` /
`kfree_rcu()` — is what nearly everything above this level actually uses.

## Debugging

`CONFIG_PROVE_RCU` (enabled together with lockdep, under `CONFIG_PROVE_LOCKING`) instruments
`rcu_dereference()` and friends to check, at the point of every call, that the caller is actually within a
recognized RCU read-side critical section or explicitly holds the update-side lock it claims to — an
illegal dereference produces an immediate, specific splat naming the exact call site, rather than the
silent corruption that same bug would otherwise produce weeks later. It is not optional for any code that
uses RCU during development; it's one of the few checks in the kernel specifically designed to convert a
class of bug that would otherwise be nearly unreproducible into one that's caught on the first offending
call.

An **RCU CPU stall warning** is the other side of debugging RCU: a report that some CPU has not passed
through a quiescent state for `CONFIG_RCU_CPU_STALL_TIMEOUT` seconds (21 by default), which means a grace
period — and every writer waiting on it — has been stuck for that long. A real example, from
`Documentation/RCU/stallwarn.rst`:

```text
INFO: rcu_sched detected stalls on CPUs/tasks:
2-...: (3 GPs behind) idle=06c/0/0 softirq=1453/1455 fqs=0
16-...: (0 ticks this GP) idle=81c/0/0 softirq=764/764 fqs=0
(detected by 32, t=2603 jiffies, g=7075, q=625)
```

Read as: CPU 32 is the one that noticed and printed the warning; CPU 2 is three grace periods behind and
hasn't taken enough RCU-relevant softirqs to catch up; CPU 16 has taken zero scheduling-clock ticks during
the *current* grace period, meaning it hasn't been interrupted at all recently — often because it's
spinning somewhere with interrupts disabled. `g=7075` is the grace-period sequence number in progress,
`q=625` the number of callbacks still queued kernel-wide. The message is normally followed by a stack
trace for each stalled CPU, and that stack trace is almost always the actual answer: a genuine unbounded
loop in the kernel (a `while` loop that forgot to check for completion, a livelock between two paths) is
the most common cause, with a lost interrupt or a misconfigured `nohz_full` CPU that stopped taking
scheduling-clock ticks as the other realistic possibilities.

<Lab host="qemu" title="Make RCU stall, and watch lockdep catch a misuse" time="30 min">

:::danger
A deliberately-triggered RCU CPU stall on a single-CPU VM can make the whole VM unresponsive for the
entire stall timeout (and past it, since the stalling loop in the module described below never ends on
its own) — there's no other CPU left to notice anything or intervene. Run this only inside a disposable
VM you can kill and discard, never on a machine you're using for anything else, and give the VM at least
two virtual CPUs so the console stays responsive while CPU 0 is stuck.
:::

**Not executed for this page.** `qemu-system-x86_64` is not installed in the sandbox this page was
written in, and there is no kernel source tree or `/lib/modules/$(uname -r)/build` directory available to
build an out-of-tree module against — both are required to build and boot the two modules this lab calls
for, and per this project's established practice, no dmesg output has been fabricated to fill the gap.
What follows is the lab as designed, with the `.config` fragment and the reference splat formats it
depends on, verified against `Documentation/RCU/stallwarn.rst` and `include/linux/rcupdate.h` at v6.18
rather than invented.

**Kconfig fragment** (verified against `kernel/rcu/Kconfig.debug` at v6.18 — `CONFIG_PROVE_RCU` depends
on `CONFIG_PROVE_LOCKING`, and `CONFIG_RCU_CPU_STALL_TIMEOUT` is an `int` in the range 3–300 seconds,
default 21):

```text
CONFIG_PROVE_LOCKING=y
CONFIG_PROVE_RCU=y
CONFIG_RCU_CPU_STALL_TIMEOUT=5
```

Lowering the stall timeout to 5 seconds makes the lab practical to run interactively instead of waiting
out the 21-second default on every attempt.

1. **Boot a VM with the fragment above applied**, at least two vCPUs (per the danger notice), and confirm
   `CONFIG_PROVE_RCU` is set: `zcat /proc/config.gz | grep PROVE_RCU` or check `/boot/config-$(uname -r)`.
2. **Build and load a "stall" module** whose init function enters `rcu_read_lock()` and then spins in a
   tight `while (1)` with no `cond_resched()` and no exit condition, pinned to CPU 0 via
   `set_cpus_allowed_ptr()` or a similar affinity call. Because the loop never takes a quiescent state and
   interrupts stay enabled, the *other* vCPU should still respond while CPU 0's grace period stalls.
3. **Watch `dmesg -w`** for the stall splat — expect the shape shown above (`INFO: rcu_sched detected
   stalls on CPUs/tasks:` followed by a per-CPU line and a stack trace pointing at the spinning module),
   appearing roughly `CONFIG_RCU_CPU_STALL_TIMEOUT` seconds after the module loads.
4. **Build and load a second, separate "misuse" module** whose init function stores a pointer with
   `rcu_assign_pointer()`, then — outside any `rcu_read_lock()`/`rcu_read_unlock()` section and without
   holding whatever lock would justify `rcu_dereference_protected()` — calls plain `rcu_dereference()` on
   it. With `CONFIG_PROVE_RCU=y`, expect an immediate lockdep splat at load time (a `WARNING:` block from
   `lockdep_rcu_suspicious()` naming the exact file and line of the illegal call), not a stall — this is
   the "nothing warns you" failure mode from this page's rules turned into something that *does* warn,
   specifically because `CONFIG_PROVE_RCU` is on.
5. **Unload the stall module's underlying process by rebooting the VM** — a spinning `rcu_read_lock()`
   section with no exit has no clean unload path; discard the VM rather than trying to recover it live.

**If it fails:** without `CONFIG_PROVE_RCU`, step 4's illegal dereference produces no diagnostic at all —
which is itself the point being demonstrated, not a failure of the lab.

</Lab>

```mermaid
sequenceDiagram
    participant W as Writer
    participant R0 as Reader (CPU 0)
    participant R1 as Reader (CPU 1)
    participant GP as Grace-period machinery
    R0->>R0: rcu_read_lock(); holds old version
    R1->>R1: rcu_read_lock(); holds old version
    W->>W: rcu_assign_pointer() publishes new version
    W->>GP: kfree_rcu(old, rcu) queues the free
    R0->>R0: rcu_read_unlock() (finishes first)
    GP->>GP: still waiting on CPU 1
    R1->>R1: rcu_read_unlock() (finishes later)
    GP->>GP: grace period complete
    GP->>W: callback fires — old version freed
```

*The writer's `kfree_rcu()` runs after the last pre-existing reader leaves, not after a fixed delay.*

<KernelFacts
  structure={[["struct rcu_head (aka struct callback_head)", "include/linux/types.h"], ["struct srcu_struct", "include/linux/srcu.h"]]}
  path="rcu_read_lock() → rcu_dereference() → use → rcu_read_unlock(); writer: rcu_assign_pointer() → kfree_rcu()"
  observe="dmesg | grep -i rcu | head; grep -i rcu /proc/softirqs"
  trap="RCU misuse does not fail loudly. Dereferencing an RCU pointer without a read-side section works perfectly until the moment a writer frees the object underneath you — which is why CONFIG_PROVE_RCU in a debug build is not optional for code that uses RCU." />

## References

- [RCU Requirements](https://docs.kernel.org/RCU/checklist.html) — the numbered review checklist this
  page's five rules are drawn from and condensed.
- [Using RCU's CPU Stall Detector](https://docs.kernel.org/RCU/stallwarn.html) — the source of the stall
  splat quoted above and the full list of common causes.
- <Src file="include/linux/rcupdate.h" symbol="rcu_dereference" /> — the read-side fetch primitive, and
  `rcu_dereference_protected` alongside it in the same header for the update-side form.
- API surface and current flavour list (Tasks RCU, Tasks Rude RCU, Tasks Trace RCU, SRCU; the retirement
  of RCU-bh/RCU-sched as independently-tracked flavours) checked against `include/linux/rcupdate.h`,
  `kernel/rcu/Kconfig`, and `kernel/rcu/Kconfig.debug` at the v6.18 tag, and cross-checked via context7
  against `docs.kernel.org/RCU/whatisRCU.html` and `docs.kernel.org/RCU/lockdep.html` — 2026-09-09.
