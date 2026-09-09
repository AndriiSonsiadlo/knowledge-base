---
id: choosing-a-lock
title: "Choosing a Lock"
sidebar_label: "Choosing a lock"
sidebar_position: 12
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/spinlocks
  - linux/concurrency-and-locking/mutexes-and-semaphores
  - linux/concurrency-and-locking/rwlocks-and-rwsems
  - linux/concurrency-and-locking/rcu-in-practice
related:
  - computer-science/memory-hierarchy/cache-coherence-and-mesi
draft: false
---

# Choosing a Lock

The decision table, six worked selections, and the cost hierarchy from an uncontended atomic to cross-NUMA ping-pong.

Most of the time, choosing a lock is not really a choice. By the time you have answered two
questions — which contexts touch this data, and may the critical section sleep — there is normally
exactly one primitive that is even legal, let alone correct. The freedom that remains after those two
questions is not "which lock" but "how finely divided": one lock for a whole subsystem, one per bucket,
one per object, or none at all if the access pattern is read-mostly enough for RCU. That freedom —
granularity, not primitive — is where almost all of the real engineering in this folder actually lives,
and it matters far more than picking the theoretically fastest lock for a section that is going to be
uncontended anyway.

## The questions, in order

1. **Which contexts touch this data?** Process context only, or also softirq, hard IRQ, or NMI? Anything
   reachable from an interrupt handler forecloses every sleeping primitive immediately — this is the
   question [Spinlocks](./spinlocks.md) and [Why Kernel Concurrency Is
   Different](./why-kernel-concurrency-is-different.md) exist to make automatic.
2. **May the critical section sleep?** An allocation with `GFP_KERNEL`, a `copy_to_user()`, taking
   another sleeping lock — any of these inside the section rules out every spinning primitive.
3. **How long is it held?** Microseconds favor spinning; anything that can run for a scheduler tick or
   longer favors a sleeping primitive even where spinning would technically be legal, because a spinning
   waiter burns a whole CPU doing nothing.
4. **What is the read/write ratio?** Read-mostly data is a candidate for `rw_semaphore`, `seqlock_t`, or
   RCU; roughly even traffic gets little benefit from a reader/writer split and should usually stay
   simple.
5. **How contended is it, really?** Measure with `CONFIG_LOCK_STAT` before assuming — see the trap below.

The first two questions eliminate most of the option space outright. The last three are optimization,
not correctness, and should be answered with data, not intuition.

## The decision table

<div style={{overflowX: "auto"}}>

| Primitive | Valid contexts | May critical section sleep? | Reader cost | Writer cost | Fits when |
|---|---|---|---|---|---|
| `spinlock_t` | Process, softirq, hard IRQ (with `_irqsave`) | No | N/A — no reader concept | One cache-line CAS, spins | Short critical section; either side may run in interrupt context |
| `spin_lock_irqsave` | Process and hard IRQ, mutually | No | N/A | Same CAS, plus saves/restores IRQ state | The lock is also taken from a hard-IRQ handler — the only safe way to share it with process context |
| `spin_lock_bh` | Process and softirq, mutually | No | N/A | Same CAS, plus disables softirqs | Shared with a softirq/tasklet path, not a hard-IRQ handler |
| `raw_spinlock_t` | Same as `spinlock_t`, even under `PREEMPT_RT` | No | N/A | Same CAS; never becomes a sleeping lock | Code that must keep spinning under `PREEMPT_RT` — timekeeping, the scheduler's own locks |
| `struct mutex` | Process context only | Yes | N/A — no reader concept | Atomic op, may block, has owner tracking (priority inheritance, debug checks) | The default sleeping lock — general-purpose exclusion where the section may block |
| `rw_semaphore` | Process context only | Yes | Atomic op on a shared field, may block | Atomic op, may block, drains readers | Long, sleeping read sections; the default reader-writer choice in modern code |
| `seqlock_t` | Anywhere (readers never block); writer side follows spinlock rules | Writer: no. Readers: never block, but must retry | Effectively free — no atomic, no cache-line write, just a sequence-counter read and a retry loop | Same as the underlying spinlock | Small, frequently-read, frequently-written data — a timestamp pair, a small config struct |
| RCU | Readers: anywhere, including NMI. Writers: process context (may sleep waiting for a grace period) | Readers: never block. Writers: reclaim waits a grace period | Effectively free — no lock, no atomic | Reclaim must wait a grace period (can be milliseconds) | Read-mostly data where readers must never be slowed by writers at all |
| Per-CPU data | Anywhere, with the right access primitive | N/A — no shared state to block on | Free on the owning CPU | Free on the owning CPU; cross-CPU access needs its own synchronization | Statistics, counters, and other data that is naturally partitioned by CPU |
| Atomics / refcounts | Anywhere | N/A | One instruction (uncontended) | One instruction (uncontended) | A single word — a counter, a flag, a reference count — with no larger invariant to protect |

</div>

This table is deliberately consistent with the reader/writer comparison in [Reader-Writer
Locks](./rwlocks-and-rwsems.md#the-two-families) — read that page first if the `rwlock_t` versus
`rw_semaphore` versus `percpu_rw_semaphore` tradeoff matters for your case; it is not repeated in full
here.

## Six worked selections

1. **A driver's device state, touched by a syscall path and its own interrupt handler.** The interrupt
   handler forecloses every sleeping primitive immediately. Answer: `spinlock_t`, taken as
   `spin_lock_irqsave()` from the syscall path (so it is safe against the same lock being taken from the
   IRQ handler) and as plain `spin_lock()` from the handler itself, which already runs with interrupts
   disabled on that CPU.
2. **A rarely-changing list of registered callbacks, read on every packet.** Reads dominate by orders of
   magnitude, the list changes at registration/deregistration time only, and the read side must be as
   fast as possible. Answer: RCU — `list_for_each_entry_rcu()` on the fast path, `synchronize_rcu()` (or
   `call_rcu()`) before freeing a removed entry.
3. **A per-CPU statistics counter.** No cross-CPU invariant to protect at all — each CPU only ever
   touches its own slot. Answer: per-CPU data with `this_cpu_inc()`/`this_cpu_add()`, no lock, summed
   with a fold-over-CPUs read when a total is needed.
4. **A large data structure read for milliseconds under a syscall.** Long hold time rules out spinning
   outright — a millisecond of spinning is a wasted CPU doing nothing useful. Answer: `rw_semaphore`,
   read-locked, so many concurrent readers can each block (fault, allocate) without serializing on each
   other; this is the `mmap_lock` shape.
5. **A small structure updated on every timer tick and read by `clock_gettime()`.** Very short writer,
   extremely frequent reader, and the reader must never block the writer or vice versa. Answer:
   `seqlock_t` — this is exactly the timekeeping use case the primitive was built for.
6. **A hash table with frequent lookups and occasional inserts.** Lookups dominate, but the table is a
   real structure with real insert/delete invariants, not a single word. Answer: RCU for the lookup path
   (`hlist_for_each_entry_rcu()`) combined with a per-bucket spinlock for inserts/deletes, so writers to
   different buckets don't serialize against each other either — granularity applied to the write side of
   an otherwise RCU-protected structure.

## The cost hierarchy

Order-of-magnitude figures, not measurements to cite precisely — the shape is what matters:

- **An uncontended atomic on a warm (locally-cached) line** — a handful of cycles; the closest thing to
  free that exists on this list.
- **An uncontended lock acquired and released on the same core that last held it** — still cheap: the
  cache line is already local, so the cost is close to the atomic case above plus the lock's own
  bookkeeping.
- **A contended lock within one last-level cache (LLC)** — a genuine cache-coherence transaction: the
  line has to be invalidated in one core's cache and pulled into another's. Tens to low hundreds of
  cycles.
- **A contended lock across sockets** — the same transaction, but now crossing an interconnect between
  NUMA nodes instead of staying inside one package. Multiples of the same-socket cost.
- **A context switch** — orders of magnitude beyond any of the above, because it means a waiter gave up
  spinning and the scheduler ran. This is the number that makes "spin briefly, then block" the right
  design for a mutex's slow path, and it's why holding a sleeping lock across a genuinely short section
  is still usually a mistake.

See [Cache Coherence and MESI](../../computer-science/memory-hierarchy/cache-coherence-and-mesi.md) for
why cross-core and cross-socket costs look the way they do — it is the same MESI transaction underlying
every row above the context-switch line.

## Granularity beats primitive

This is the section that matters most, because it is the one a reader is most likely to skip past on the
way to the decision table. A single lock protecting a whole subsystem is simple to reason about and does
not scale — every unrelated operation on unrelated data serializes behind the same line. A lock per
object scales, because unrelated operations no longer contend, but it introduces an ordering hazard the
moment any path needs to hold more than one at a time (the next section). The usual progression is:

```
global lock  →  one lock per bucket/shard  →  one lock per object  →  per-CPU data or RCU
```

Most real scalability work in the kernel is moving a piece of code along this progression, not swapping
a slower primitive for a faster one at a fixed granularity. The
[`mmap_lock` story](./rwlocks-and-rwsems.md#the-mmap_lock-story) is the worked instance already in this
folder: the fix for contention on one `rw_semaphore` per `mm_struct` was not a faster rwsem, it was
splitting the lock to one per VMA. A faster primitive at the old granularity would not have helped; a
change of granularity did.

## Lock ordering

The moment any code path takes two locks at once, every path in the kernel that takes both of them must
take them in the *same* order, or two paths can each hold one and wait on the other forever — the
classic ABBA deadlock. The discipline that keeps this tractable is unglamorous but non-negotiable: the
order is decided once, documented as a comment next to the lock definitions (not just in the head of
whoever wrote the code), and never varies by call site. This is exactly the property
[`lockdep`](./finding-locking-bugs.md) exists to check automatically, because a human reviewing a diff
cannot see every other path in the tree that also takes both locks.

## The rule for new code

Start with the simplest correct primitive — usually a single `struct mutex` or `spinlock_t` covering more
than it strictly needs to — measure with `CONFIG_LOCK_STAT`, and only then narrow the granularity or
switch primitives where the numbers actually show contention. This folder has just spent eleven pages
describing seqlocks, RCU, per-CPU data, and lock-free patterns; none of that is a reason to reach for them
by default. A lock nobody contends is not worth making clever.

<KernelFacts
  structure={[["spinlock_t", "include/linux/spinlock_types.h"], ["struct mutex", "include/linux/mutex_types.h"]]}
  path="which contexts? → may it sleep? → hold time? → read/write ratio? → primitive"
  observe="sudo cat /proc/lock_stat | head -30 (requires CONFIG_LOCK_STAT)"
  trap="Choosing the fastest primitive rarely helps; changing what is shared almost always does. A contended lock is a granularity problem, and swapping a mutex for a spinlock leaves the contention exactly where it was." />

## References

- [Unreliable Guide To Locking](https://docs.kernel.org/kernel-hacking/locking.html) — the kernel's own
  walk through which primitive fits which context.
- [Lock types](https://docs.kernel.org/locking/locktypes.html) — the authoritative per-primitive contract
  (sleeping behavior, context restrictions) this table summarizes.
- [Lock statistics](https://docs.kernel.org/locking/lockstat.html) — how to measure contention instead of
  guessing at it, via `CONFIG_LOCK_STAT`.
- Paul E. McKenney, *Is Parallel Programming Hard, And, If So, What Can You Do About It?* — the
  partitioning/granularity chapter, the deepest treatment of the "granularity beats primitive" argument
  above.
