---
id: rcu-the-idea
title: "RCU: The Idea"
sidebar_label: "RCU: the idea"
sidebar_position: 8
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/memory-ordering-and-barriers
  - linux/concurrency-and-locking/seqlocks
draft: false
---

# RCU: The Idea

Readers that take no locks and pay nothing, writers that publish a new version and defer reclamation until every reader has left.

Most synchronization primitives answer the question "how do I keep writers from stepping on readers, and
readers from stepping on each other." Read-Copy-Update starts from a different question: what if readers
paid nothing at all? For data that's read constantly and modified rarely — a routing table, a list of
registered handlers, the contents of a namespace — even the cheapest lock imaginable still costs a cache
line's worth of coherence traffic on every acquisition, and on a machine with enough CPUs reading the
same structure, that traffic is the bottleneck, not the work being done with the data. A [seqlock](./seqlocks.md)
gets partway there by giving readers a retry loop instead of a wait, but it still can't let a reader hold
a pointer past the read — the moment a reader wants to keep something it found, a seqlock's guarantee
stops helping. RCU's answer is more radical: readers take no lock, write no shared state, and are never
blocked by a writer, ever — and the entire cost of the scheme is moved onto the write side.

## The core insight

You cannot modify shared data in place while lockless readers might be looking at it — a reader
mid-traversal has no way to notice that the ground shifted under it. So don't modify it in place. Build
an entire new version of whatever's changing, publish the new version with a single pointer store, and
only free the old version once every reader that could still be holding a reference to it has finished.
**R**ead, **c**opy, **u**pdate is a literal description of the three steps a writer performs, in order:

1. **Read** the current version (a writer usually still holds some lock against other writers here, but
   readers see none of that).
2. **Copy** it — allocate a new version, and modify the copy, not the original.
3. **Update** — publish the copy by overwriting the one pointer that made the old version reachable, and
   only then reclaim the old version, once it's certain no reader can still reach it.

Every reader that ran before step 3 keeps seeing a perfectly consistent old version for as long as it
needs to; every reader that runs after step 3 sees a perfectly consistent new version. No reader ever
sees a half-built object, and no reader ever blocks — the entire mechanism is built to make both of those
true simultaneously.

## Publishing safely

Step 3 above is not "just" a pointer store. The store that publishes the new version must be ordered
*after* every write that initialized what it points at, or a reader on another CPU can follow the freshly
published pointer to an object whose fields haven't actually landed in memory yet — a completely
uninitialized structure, dereferenced. This is exactly the release/acquire pattern
[Memory Ordering and Barriers](./memory-ordering-and-barriers.md) builds up from first principles:
initialize, then release the pointer; acquire the pointer, then read through it. `rcu_assign_pointer()`
and `rcu_dereference()` are the RCU-specific spellings of that same release/acquire pair — the first
inserts whatever barrier the architecture needs and stops the compiler from hoisting the initializing
writes past the pointer store, the second stops the compiler and CPU from speculating through the
pointer before the load that produced it has actually completed. Hand-rolling this with a plain pointer
assignment and a plain pointer read looks identical on x86 (whose strong ordering happens to make it work
by accident) and is a real bug on any architecture where a dependent load can be speculated ahead of the
store that produced the address — which is precisely the class of bug these two primitives exist to rule
out at the call site rather than leave to the reader's memory to notice.

## Grace periods and quiescent states

The other half of the mechanism is knowing *when* it's safe to free the old version, and the definitions
are worth stating carefully, because the whole scheme's cheapness rides on them:

- A **quiescent state** is a moment at which a given CPU is provably not in the middle of an RCU
  read-side critical section — a context switch, a return to user space, a CPU going idle. None of these
  require any interaction with RCU at all; they're just facts that are already true about ordinary kernel
  execution, which RCU's bookkeeping merely notices.
- A **grace period** is an interval during which every CPU has passed through at least one quiescent
  state. Once a grace period that started after a given writer's update has elapsed, every reader that
  could have observed the old version is guaranteed to have finished — a reader that started before the
  grace period will have exited its critical section by the time the grace period ends, by definition,
  and no reader starting after the update can see the old version at all.

The asymmetry is the entire point: detecting a quiescent state costs nothing extra, because it rides on
events (context switches, idle entry) the kernel already produces constantly for other reasons. RCU's
bookkeeping only has to *notice* these events on each CPU and track which CPUs still owe one for the
current grace period — it never has to ask a reader anything, interrupt a reader, or wait on a reader to
do anything it wasn't already going to do. Compare that to a lock, which has to actively coordinate with
whoever's holding it; a grace period coordinates with nobody, it just watches.

## What a reader actually does

Under a non-preemptible RCU configuration (`CONFIG_TREE_RCU` without `CONFIG_PREEMPT_RCU`),
`rcu_read_lock()` compiles down to disabling preemption — a CPU that can't be preempted can't be
context-switched away, so simply staying non-preemptible for the duration of the read is itself a valid
way of guaranteeing no quiescent state occurs mid-read. Under `CONFIG_PREEMPT_RCU`, where a read-side
critical section can be preempted, `rcu_read_lock()` instead increments a small per-task counter so the
scheduler can still record that this task is mid-read even after being switched out, and RCU's grace-period
tracking accounts for that separately. Either way, a reader never writes to any cache line another CPU is
watching, never executes an atomic instruction, and never blocks on anything. That is what "free" means
here, in the literal sense of "does not show up in a profile," and it's the entire reason RCU gets reached
for anywhere it's read enormously more often than it's written.

## Why the deferred free is the whole cost

Everything RCU saves on the read side, it spends on the write side instead. A writer that wants to
reclaim the old version has to wait out a grace period — `synchronize_rcu()` blocks the calling thread
until one elapses, which in practice can be anywhere from microseconds to tens of milliseconds depending
on what the rest of the system is doing — or hand the reclamation to a callback via `call_rcu()` so the
writer itself doesn't have to block at all. Either way, the object being replaced can't be freed
*immediately*; it has to sit around, unreachable but not yet reclaimed, until the grace-period machinery
confirms it's safe. That's a perfectly fine price when updates are rare (a routing table changed once a
second is nothing), and it becomes the whole story when they aren't: a writer that fires every few
microseconds is now waiting on — or queuing callbacks for — grace periods every few microseconds, and the
deferred-free bookkeeping itself starts to cost real memory and real CPU time. Whether the update rate for
a given piece of data is "rare" in this sense is the single criterion for whether RCU is the right tool at
all; everything else about RCU follows from that one ratio being lopsided in the read direction.

## What RCU does not give you

Stated plainly, because each of these is a common source of misuse:

- **RCU does not serialize writers against each other.** Two writers racing to publish a new version of
  the same pointer still corrupt each other's work exactly as they would with no synchronization at all —
  writers still need an ordinary lock among themselves; RCU only removes the *reader* side of the
  equation.
- **RCU does not give a reader a consistent view across two different RCU-protected structures.** A
  reader that looks up structure A and then structure B, each independently RCU-protected, can observe A
  from before an update and B from after it, because nothing ties the two lookups' grace periods together.
  Consistency is guaranteed within one structure's single publishing pointer, not across independent ones.
- **RCU does not stop a reader from seeing a version that's about to be replaced.** A reader that acquired
  a reference to the old version an instant before a writer publishes the new one is entitled to keep
  using that old version for the rest of its critical section — RCU guarantees the old version stays valid
  long enough for that to be safe, not that every reader sees the newest data as soon as it exists.

None of these three are missing features; they're the properties that make the cheap read side possible
in the first place, and every one of them is exactly what a piece of code reaching for RCU needs to be
comfortable living without.

## Where it is used

`struct cred` is the clearest example already covered in this section: a task's credentials are replaced
wholesale rather than modified field-by-field, published via `rcu_assign_pointer()`, and read via
`rcu_dereference()` under `rcu_read_lock()` by anything that just needs to inspect the current credentials
without blocking a `setuid()` in progress — see
[RCU-protected credentials](../06-processes-and-threads/credentials-and-identity.md#rcu-protected-credentials)
for the concrete walkthrough. The same shape recurs all over the kernel wherever a structure is read far
more often than it changes: the dentry cache, the networking stack's routing and neighbour tables, and a
namespace's list of mounted filesystems are all classic RCU consumers, though each of those is its own
later topic, not something this phase covers in detail.

```wavedrom title="A grace period spans the last pre-existing reader" alt="Three readers on three CPUs at different times, a writer's pointer update, and a grace period extending from the update to the end of the last reader that started before it"
{
  signal: [
    { name: "CPU 0 reader", wave: "0.1...0...." },
    { name: "CPU 1 reader", wave: "0....1..0.." },
    { name: "CPU 2 reader", wave: "0.......1.0" },
    {},
    { name: "writer: publish", wave: "0.10......." },
    { name: "grace period", wave: "0..1.....0." },
    { name: "writer: free old", wave: "0..........1" }
  ]
}
```

*A grace period is not a fixed interval — it ends when the last reader that could have seen the old
version has finished, and only then is it safe to free.*

```mermaid
flowchart LR
    A["Read current version"] --> B["Copy: allocate + build new version"]
    B --> C["Update: rcu_assign_pointer() publishes new version"]
    C --> D["Old version: unreachable to new readers,\nstill valid for readers already in flight"]
    D --> E["synchronize_rcu() / call_rcu()\nwaits out a grace period"]
    E --> F["kfree() the old version"]
```

*The old version doesn't disappear the instant it's replaced — it sits on a deferred-free path until the
grace-period machinery confirms every reader that might still be using it is done.*

<KernelFacts
  structure={[["struct rcu_head (aka struct callback_head)", "include/linux/types.h"]]}
  path="rcu_assign_pointer() publishes → readers under rcu_read_lock() may still hold the old version → synchronize_rcu() waits a grace period → kfree() the old version"
  observe="grep -i rcu /proc/softirqs   # RCU callback-processing softirq counts, per CPU — available with no special privilege; /sys/kernel/debug/rcu/rcu_preempt/rcugp needs debugfs access this sandbox's unprivileged shell does not have (`ls /sys/kernel/debug/rcu` returned Permission denied when checked while writing this page)"
  trap="A grace period is not a timeout and has no fixed duration. It ends when every CPU has passed through a quiescent state, which on a busy machine is fast and on an idle or nohz_full one can take substantially longer." />

## References

- [RCU Concepts](https://docs.kernel.org/RCU/rcu.html) — the short, high-level statement of what RCU is
  and the removal/reclamation split.
- [What is RCU? "Read, Copy, Update"](https://docs.kernel.org/RCU/whatisRCU.html) — the long-form
  explanation this page summarizes, including the API this section builds on.
- Paul E. McKenney, Jonathan Walpole, et al., *Is Parallel Programming Hard, And, If So, What Can You Do
  About It?* — the deferred-processing chapter is the deepest published treatment of RCU's design
  rationale; freely available from the "perfbook" project. No stable recorded-talk URL for a McKenney RCU
  presentation could be verified while writing this page, so none is embedded here — see the book instead
  for the same material in more depth.
- <Src file="include/linux/rcupdate.h" symbol="rcu_assign_pointer" /> — the publish side; see also
  `rcu_dereference` in the same header for the read side.
