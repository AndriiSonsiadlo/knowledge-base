---
id: seqlocks
title: "Seqlocks"
sidebar_label: "Seqlocks"
sidebar_position: 7
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/memory-ordering-and-barriers
draft: false
---

# Seqlocks

Lockless readers with a retry loop, the constraints that puts on a reader, and the canonical use in timekeeping.

The trick, stated plainly: let readers proceed with no lock at all and no waiting on a writer whatsoever
— and give them a way to *detect*, after the fact, that a writer interfered while they were reading, so
they can simply try again. A reader costs almost nothing: no atomic instruction, no cache-line
contention with other readers, nothing but a couple of plain memory reads of a counter. That's why the
single most-read piece of data in the entire kernel — the current time — is protected exactly this way.

## The protocol

A seqlock is, at its core, one sequence counter. A writer increments it once on entry to its critical
section and once again on exit — so the counter is odd exactly while a write is in progress, and even
otherwise. A reader reads the counter, reads the data it protects, then reads the counter a second time:
if the two counter reads match *and* the value is even, the read was clean; if the counter changed, or
was odd at either read, the reader discards what it saw and retries from the top.

```c
unsigned seq;
do {
    seq = read_seqbegin(&some_seqlock);
    /* ... read the protected data ... */
} while (read_seqretry(&some_seqlock, seq));
```

This only works with the right memory barriers on both sides: the writer's counter increment must be
visible to other CPUs *before* its data writes become visible, and after them on the way out, and the
reader's counter reads must not be reordered around its data reads by the compiler or the CPU. See
[Memory Ordering and Barriers](./memory-ordering-and-barriers.md) for what makes that guarantee hold —
`read_seqbegin()`/`read_seqretry()` and the writer-side helpers embed exactly the acquire/release pairing
that page describes; a hand-rolled seqcount loop that skips them is not actually safe just because it
looks the same.

## What readers may not do

The protocol only works because everything a reader does inside the loop is safely repeatable and
inspects nothing that could be false. That places real constraints on reader code:

- **No pointer may escape the loop.** A pointer read inside the loop might point at something a
  concurrent writer is in the middle of replacing or freeing; only after `read_seqretry()` confirms the
  read was clean is a pointer trustworthy to use outside the loop.
- **Nothing may be freed or acted on inside the loop.** Any side effect performed on data that might
  turn out to be torn is a side effect performed on garbage. The loop body must be pure with respect to
  everything outside the local copy it's building.
- **The work must be cheap to redo.** A retry is not a rare fallback path to tolerate awkwardly; under
  real writer contention it can happen repeatedly, so the loop body's cost is paid on every attempt.

The one thing to internalize: a reader can genuinely observe an inconsistent mix of old and new field
values mid-write — that's not a bug in the primitive, it's the whole design — and it is fine *only*
because the reader is contractually obliged to notice via `read_seqretry()` and throw the mix away rather
than act on it.

## Writers are still serialised

A seqlock optimizes the reader side; it does nothing for writers, who still need a real lock among
themselves the same way they always would. Two forms exist depending on who supplies that lock:

- **`seqlock_t`** bundles a spinlock together with the sequence counter — `write_seqlock()` /
  `write_sequnlock()` both take the embedded spinlock and bump the counter, so the writer never has to
  manage a separate lock by hand.
- **`seqcount_t`** is the counter alone, with no embedded lock, for use when the caller already holds
  some other lock (a spinlock, a mutex, whatever already serializes writers in that subsystem) and only
  needs the sequence-counter half of the mechanism layered on top for readers' benefit.

This distinction confuses people on first contact because both types expose a near-identical read side
(`read_seqcount_begin()`/`read_seqcount_retry()`, or the `seqlock_t`-flavoured `read_seqbegin()`/
`read_seqretry()` wrappers around them) — the difference is entirely on the write side, in who owns the
serialization.

## The canonical use: timekeeping

The kernel's timekeeper (`struct tk_core`, tracking the current time and updated once per tick by a
single writer) is read by every `clock_gettime()`, every `ktime_get()`, on every CPU, constantly — and
written comparatively rarely, on the tick. That access pattern is close to a textbook case for a
seqlock: readers are enormously more frequent than the writer, the read is short (copy a small struct's
worth of fields) and trivially repeatable, and the protected data is genuinely small. `ktime_get()` in
`kernel/time/timekeeping.c` is a direct instance of the retry loop above:

```c
do {
    seq = read_seqcount_begin(&tk_core.seq);
    base = tk->tkr_mono.base;
    nsecs = timekeeping_get_ns(&tk->tkr_mono);
} while (read_seqcount_retry(&tk_core.seq, seq));
```

The same protocol reappears in user space, not just the kernel: the
[vDSO](../05-syscalls-and-the-boundary/the-vdso.md) implements `clock_gettime()` by mapping the same
timekeeping data read-only into every process and running this identical seqcount retry loop entirely in
user space, which is exactly why `clock_gettime()` can return the time with no syscall at all. See
[Timekeeping and
Clocksources](../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md) for the writer side
of this same structure.

## Latch variants

For one narrow case even the retry loop above is unsafe: NMI context. An NMI can interrupt a writer
*inside* its critical section, and an NMI handler cannot simply spin waiting for the writer to finish
(there's nowhere for it to yield to). `seqcount_latch_t` solves this by keeping two full copies of the
protected data and using the counter's even/odd value to say which copy is currently stable — a writer
updates the *other* copy first, flips the counter, then updates the copy it started with, so at every
instant at least one of the two copies is complete and consistent, and an NMI-context reader can always
find a stable copy to read without ever needing to retry. It's a specialised tool for a specific
constraint (some of the kernel's own timekeeping fallbacks for NMI-context callers use it); the mechanism
is worth naming here so the type isn't mistaken for a plain `seqcount_t`, but the detail belongs to
`Documentation/locking/seqlock.rst`, not this page.

## When a seqlock is wrong

Three situations where reaching for a seqlock backfires:

- **The read is expensive.** If reconstructing the reader's view of the data costs real work, a retry
  under contention means paying that cost repeatedly, and a lock that avoids torn reads in the first
  place may be cheaper overall.
- **Readers only slightly outnumber writers.** The whole design bets on reads being vastly more frequent
  than writes; if that ratio isn't lopsided, the retry overhead under contention can erase the advantage
  over an ordinary `rw_semaphore` or spinlock.
- **The reader needs to take a reference to something it found.** A seqlock can tell a reader that its
  *view* was torn, but it can't stop a reader from acting on a pointer before that check completes — and
  "act on" includes incrementing a refcount on an object that might be concurrently freed. That case
  needs a primitive that keeps the object alive across the read, which is exactly the problem RCU is built
  to solve — the next primitive in this section, not covered here.

```wavedrom title="Seqlock read/write timing" alt="A writer's critical section makes the sequence counter odd then even; a clean reader's window falls entirely outside it, an overlapping reader retries"
{
  signal: [
    { name: "seq counter", wave: "2.2.3.4.2..", data: ["0", "0", "1", "2", "2"] },
    {},
    { name: "writer", wave: "0....1.0..." },
    {},
    { name: "reader A (clean)", wave: "0.1.0......" },
    { name: "reader B (overlaps, retries)", wave: "0...1..010." }
  ]
}
```

*Two readers and one writer: the reader whose window overlaps the write sees an odd or changed counter
and simply tries again.*

<KernelFacts
  structure={[["seqcount_t", "include/linux/seqlock_types.h"], ["seqlock_t", "include/linux/seqlock_types.h"]]}
  path="read_seqbegin() → read the data → read_seqretry() → retry if the counter moved"
  observe="grep -A4 'do {' kernel/time/timekeeping.c | grep -B1 -A3 read_seqcount_begin # read the ktime_get() retry loop in the kernel source"
  trap="A seqlock protects readers from seeing torn data, not from acting on it. Anything a reader does inside the loop — dereferencing a pointer it read, taking a reference, logging a value — may be acting on garbage, so the loop must do nothing but copy." />

## References

- [seqlock.rst](https://docs.kernel.org/locking/seqlock.html) — the definitive reference for
  `seqcount_t`, `seqlock_t`, and `seqcount_latch_t`.
- <Src file="include/linux/seqlock.h" symbol="read_seqbegin" /> — the read-side macros and the
  barrier pairing they embed.
- <Src file="kernel/time/timekeeping.c" symbol="ktime_get" /> — the canonical retry loop, live in the
  timekeeper.
- <Src file="Documentation/memory-barriers.txt" /> — the barrier semantics
  [Memory Ordering and Barriers](./memory-ordering-and-barriers.md) draws on, that make the retry
  protocol correct.
