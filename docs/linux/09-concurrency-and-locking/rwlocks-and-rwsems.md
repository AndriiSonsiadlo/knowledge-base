---
id: rwlocks-and-rwsems
title: "Reader-Writer Locks"
sidebar_label: "Reader-writer locks"
sidebar_position: 6
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/mutexes-and-semaphores
related:
  - computer-science/memory-hierarchy/cache-coherence-and-mesi
draft: false
---

# Reader-Writer Locks

Why a reader-writer lock is often slower than a plain one, and where `rw_semaphore` is genuinely the right answer.

Letting many readers in at once sounds like it should be nearly free — readers don't conflict with each
other, so why serialize them? The catch is that "letting a reader in" still means every reader writes to
the lock's own cache line to register its presence and check for a writer. N readers produce N coherence
transactions on that one line, exactly the cache-line-bouncing problem [Spinlocks](./spinlocks.md#queued-spinlocks)
describes for the naive test-and-set lock — and a plain exclusive lock, which does roughly the same
amount of bouncing while being simpler to reason about and free of writer-starvation concerns, is
frequently *faster* in practice than the reader-writer version of the same protection.

## The two families

Two implementations exist, and they are not interchangeable:

- **`rwlock_t`** — spins, never sleeps. Same non-sleeping contract as `spinlock_t`: safe in interrupt
  context, forbidden to hold across anything that can block.
- **`rw_semaphore`** — sleeps on contention, like a mutex. This is by far the more common of the two in
  modern code; a plain spinning `rwlock_t` shows up in relatively few places today.

## Why rwlocks are usually the wrong answer

Two problems stack against `rwlock_t` specifically:

1. **The cache-line argument above.** Every reader, not just every writer, touches the lock's cache line
   on entry and exit. On a machine with many cores all taking the same read lock, that's `N` coherence
   transactions competing for one line — the exact pathology a lock is supposed to avoid, not something
   reading is supposed to be exempt from.
2. **Writer starvation.** A steady stream of overlapping readers can, in the naive
   reader-preference scheme, keep a waiting writer blocked indefinitely — there is never a moment with
   zero active readers for the writer to slot into.

The practical rule: if the critical section is short, skip the reader-writer complexity and use a plain
spinlock — the read/write distinction buys nothing at that scale. If reads massively dominate writes
*and* the read-side critical section is long, look at RCU instead of `rwlock_t` — RCU readers pay no
per-access cache-line cost at all, spinning or otherwise. `rwlock_t` occupies a narrow middle band
between those two: read-side sections too long to spin through as a plain lock, but not so read-dominant
or so structurally suited that RCU is worth the additional complexity.

## rw_semaphore, and where it is right

`rw_semaphore` earns its keep for sleeping, comparatively long read sections — where the point isn't
raw cache-line efficiency but letting many readers block *concurrently* rather than serially, each
possibly doing real work (faulting, allocating) during its hold. The canonical example is `mmap_lock`
(`mm->mmap_lock`, a `struct rw_semaphore` embedded in [`struct
mm_struct`](../08-memory-management/mm-struct-and-vmas.md)) — read-locked by every page fault that walks
the process's VMAs, write-locked by anything that changes the address space layout (`mmap()`, `munmap()`,
`brk()`, and friends).

## The mmap_lock story

`mmap_lock` is worth a short case study because the lesson it taught is more valuable than the lock
itself. For years it was one lock, one `rw_semaphore`, per `mm_struct`, and on fault-heavy
multithreaded workloads it became a serious scalability bottleneck: every thread of a process faulting
concurrently contended for the *same* semaphore, even when their faults touched entirely unrelated
regions of the address space. The instinct might be to look for a faster lock. The actual fix, landed as
per-VMA locking, was a change of *granularity*: instead of one rwsem covering the whole address space, each
VMA gained its own lock, so a fault in one VMA no longer contends with a fault in another. Concurrent
faults that were previously serialized behind one shared semaphore now proceed independently as long as
they land in different VMAs.

The generalizable lesson: when a reader-writer lock is the measured bottleneck, the first question isn't
"is there a faster lock primitive" — it's "is this lock protecting more than it needs to, and can the
protected structure be split." A faster mutex over the same one-`mm_struct` granularity would not have
fixed this; splitting the granularity did.

## Downgrade and upgrade

`downgrade_write()` exists: a task holding the write lock can atomically convert to holding the read
lock, without a window where the lock is released and might be grabbed by someone else. The reverse —
upgrading from read to write — has no equivalent, and cannot safely have one: if two readers both try to
upgrade to a writer at the same time, each is waiting for the other to drop its read lock first, and
neither ever will. The pattern to use instead is drop-and-reacquire: release the read lock entirely,
acquire the write lock fresh, and then *re-validate* whatever the read section had established before
proceeding — because the state may have changed for any reader between the drop and the write acquire,
and skipping that re-check reintroduces exactly the race the upgrade was trying to avoid without the
lock ever telling you it happened.

## Fairness and queueing

At v6.18, `rw_semaphore`'s waiters queue in FIFO order and the lock is fair by default: a stream of new
readers cannot indefinitely starve a writer that's already waiting. The mechanism is a handoff flag
(`RWSEM_FLAG_HANDOFF`) — a waiter that has been queued too long (or is an RT task) can set the flag to
force the lock to go to it next, overriding the optimistic-stealing behaviour that otherwise lets a new
reader or writer jump the queue if the lock currently looks free. The kernel source itself is blunt about
the reasoning: reader optimism is deliberately throttled once a writer is known to be waiting, "to prevent
a constant stream of readers from starving a sleeping writer." Under `PREEMPT_RT`, the picture changes:
an `rw_semaphore` writer can't hand its priority to more than one blocked reader, so a preempted
low-priority reader holding the lock can still stall a high-priority writer, whereas readers *can* boost a
waiting low-priority writer's priority — an asymmetry that only shows up once priority inheritance is in
the picture at all.

## percpu_rw_semaphore

For the extreme read-dominant case, `percpu_rw_semaphore` goes further than `rw_semaphore`'s ordinary
optimizations: read-locking touches only the calling CPU's own per-CPU data and uses no atomic
instruction on the fast path at all — genuinely no cross-CPU cache-line traffic for readers. The cost is
pushed entirely onto the writer: write-locking calls `synchronize_rcu()` internally, which can take on the
order of tens to hundreds of milliseconds to complete. That asymmetry is only correct where writes are
rare and readers are extremely frequent and latency-sensitive — exactly the case for the two places it's
actually used: filesystem freezing (`struct sb_writers`, embedded in `struct super_block`, uses an array
of `percpu_rw_semaphore`s so that ordinary writes to a mounted filesystem — the read side — cost almost
nothing, and only an actual freeze — the write side — pays the expensive synchronization), and cgroup
threadgroup changes (`cgroup_threadgroup_rwsem`, which read-side-guards the vastly more common case of a
thread just existing against the rare case of cgroup membership actually changing).

<div style={{overflowX: "auto"}}>

| | Reader cost | Writer cost | Readers may sleep? | Writer starvation risk | Fits when |
|---|---|---|---|---|---|
| `spinlock_t` | One cache-line CAS, no read/write distinction | Same as reader — it's one exclusive lock | No | N/A — no reader concept | Critical section is short; either side may run in interrupt context |
| `rwlock_t` | One cache-line write per reader (register/check), spins | One cache-line write, spins, waits for readers to drain | No | Real, under a steady reader stream | Rare middle case: read section too long to just spinlock, too small/unsuited for RCU |
| `rw_semaphore` | Atomic op on a shared field, may block | Atomic op, may block, drains readers | Yes | Bounded — FIFO + handoff flag prevents indefinite starvation | Long, sleeping read sections; the default reader-writer choice in modern code |
| `percpu_rw_semaphore` | Per-CPU, no atomic instruction, no cross-CPU traffic | Very high — calls `synchronize_rcu()`, can cost tens–hundreds of ms | Yes | Not applicable — writers already pay a large fixed cost | Read-side is overwhelmingly hot and latency-critical; writes are rare (fs freeze, cgroup membership) |
| RCU | Effectively free — no lock, no atomic, no cache-line write | Reclaim must wait a grace period | Yes (readers never block, but see RCU pages) | None — readers never block a writer | Read-mostly data where readers must never be slowed by writers at all |

</div>

*Reader-writer choice is a granularity and frequency question, not a "pick the fanciest lock" question —
this table also anchors [Choosing a Lock](./choosing-a-lock.md).*

<KernelFacts
  structure={[["struct rw_semaphore", "include/linux/rwsem.h"], ["rwlock_t", "include/linux/rwlock_types.h"]]}
  path="down_read() → rwsem_read_trylock() fast path → contended → rwsem_down_read_slowpath() → schedule()"
  observe="sudo grep -A3 mmap_lock /proc/lock_stat (requires CONFIG_LOCK_STAT and a workload that produces entries)"
  trap="A reader-writer lock does not make readers free. Every reader writes to the lock's cache line, so on a many-core machine the readers contend with each other — which is exactly the problem RCU exists to solve." />

## References

- [Lock types](https://docs.kernel.org/locking/locktypes.html) — the authoritative statement of
  `rw_semaphore` fairness and its behaviour under `PREEMPT_RT`.
- <Src file="kernel/locking/rwsem.c" symbol="rwsem_down_read_slowpath" /> — the slow path, and the
  `RWSEM_FLAG_HANDOFF` fairness mechanism in context.
- LWN, [*Concurrent page-fault handling with per-VMA locks*](https://lwn.net/Articles/906852/) (Jonathan
  Corbet, September 5, 2022) — the per-VMA locking design that grew out of `mmap_lock` contention.
- [percpu-rw-semaphore](https://docs.kernel.org/locking/percpu-rw-semaphore.html) — the reader/writer
  cost asymmetry described above, straight from the source comment it's built on.
