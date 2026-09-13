---
id: memory-ordering-and-barriers
title: "Memory Ordering and Barriers"
sidebar_label: "Ordering and barriers"
sidebar_position: 2
tags: [linux, kernel, locking]
prerequisites:
  - linux/concurrency-and-locking/why-kernel-concurrency-is-different
related:
  - computer-science/cpu-architecture/memory-ordering-and-consistency
draft: false
---

# Memory Ordering and Barriers

Why a plain access is not safe, what each barrier actually orders, and why this is the page arm64 changes the most.

If you protect a piece of data with a lock, the lock already handles ordering for you — every barrier on
this page is something `spin_lock()`/`spin_unlock()` and `mutex_lock()`/`mutex_unlock()` already imply,
and you can stop reading here. This page matters the moment you write lock-free code, touch a variable
another CPU writes without holding a lock, or read RCU-protected data (see [RCU: The
Idea](./rcu-the-idea.md)): from that point on, ordering is your problem, and getting it
wrong produces bugs that reproduce once a month, on one machine, under load — not on the developer's
desk.

## Two reorderers

Two independent things reorder your loads and stores, and a fix for one is not a fix for the other. The
**compiler** reorders at build time: nothing in the C abstract machine forbids merging two reads of the
same variable, splitting one access into several, inventing a read that was not in the source, or hoisting
a load out of a loop it appears not to depend on. The **CPU** reorders at run time, independent of what
the compiler emitted, through the store-buffer and speculation machinery
[Memory Ordering and Consistency](../../computer-science/cpu-architecture/memory-ordering-and-consistency.md)
covers in hardware terms. A `barrier()` that stops the compiler from reordering two accesses does nothing
to stop the CPU from reordering the instructions it compiles to, and an `smp_mb()` that fences the CPU
does nothing to stop the compiler from having already reordered the C statements before that instruction
was ever chosen. Kernel ordering code has to answer both questions separately.

## `READ_ONCE` and `WRITE_ONCE`

A plain, unadorned access to a shared variable — `x = 1;` or `if (flag) ...` — gives the compiler
permission to do anything that preserves single-threaded behavior on *this* thread's view of memory: merge
two reads into one, split a read into several, invent a read of a value never actually needed, tear a
multi-byte write into two smaller stores, or — the case that bites hardest — hoist a read out of a loop
entirely, because nothing in the loop body appears (to the compiler, looking only at this thread) to
change it.

That last case is the canonical broken kernel idiom:

```c
/* BROKEN: compiler is free to read `flag` once and hoist it out of the loop */
while (!flag)
    cpu_relax();
```

The compiler cannot see that another CPU writes `flag` without a lock, so as far as it can prove, `flag`
never changes inside the loop — it is entitled to read it once before the loop and spin forever on a
register value that will never update, regardless of what memory actually says. `READ_ONCE`/`WRITE_ONCE`
fix this by forbidding exactly the transformations that make the plain version wrong:

```c
while (!READ_ONCE(flag))
    cpu_relax();

/* the writer: */
WRITE_ONCE(flag, true);
```

`READ_ONCE`/`WRITE_ONCE` compile to a genuine single load or store (via a `volatile` cast) that the
compiler may not merge, split, invent, or hoist — nothing more. They say nothing about ordering relative
to *other* variables, and they say nothing to the CPU about store-buffer visibility; they solve the
compiler half of the problem only. Any shared variable touched outside a lock needs them on every access,
reader and writer alike — a `WRITE_ONCE` paired with a plain read is still broken, because the plain read
retains full compiler license.

## Compiler barriers versus CPU barriers

`barrier()` is a pure compiler directive: "do not reorder memory accesses across this line," with no
corresponding CPU instruction — it compiles to nothing at all in the generated code, only to a constraint
on the compiler's own scheduling of instructions. `smp_mb()` and its relatives are the CPU half:
they emit whatever instruction (or nothing, on an architecture strong enough not to need one) the target
architecture requires to constrain the *hardware's* reordering, and they also imply a compiler barrier, so
callers never need both.

The `smp_` prefix on `smp_mb()`, `smp_rmb()`, `smp_wmb()`, `smp_store_release()`, and
`smp_load_acquire()` is a real, load-bearing naming choice, not decoration: on a `CONFIG_SMP=n`
(uniprocessor) build, every one of these macros degrades to a plain compiler barrier — there is no second
CPU to reorder relative to, so the hardware fence is pure overhead and is compiled out, while the compiler
barrier is kept because a uniprocessor kernel can still race against an interrupt handler or a device
doing DMA on the same CPU. The non-`smp_`-prefixed forms (`mb()`, `rmb()`, `wmb()`) do not degrade this
way — they exist for ordering against actual hardware (MMIO, DMA) and stay full barriers even on a
uniprocessor build, because the device on the other end of the ordering requirement does not care how
many CPUs the kernel was built for.

## The barrier family

Costs below are for x86-64, verified against `arch/x86/include/asm/barrier.h` and
`include/asm-generic/barrier.h` at v6.18. x86-64's strong (TSO-like) ordering model means loads are never
reordered with earlier loads and stores are never reordered with earlier stores — only a store followed by
a later load can be reordered — so most of these barriers are free there and expensive only where the
hardware genuinely needs help.

| Barrier | What it orders | x86-64 cost | Typical use |
|---|---|---|---|
| `smp_mb()` | All prior loads/stores against all subsequent loads/stores (full barrier) | A real instruction — unconditionally `lock addl $0,-4(%rsp)` | Ordering a store against a later load in the same CPU when nothing else (a lock, an atomic RMW) already implies it |
| `smp_rmb()` | Prior loads against subsequent loads only | Compiles to a plain compiler barrier — x86-64 does not reorder loads with loads | Reading a data structure after reading a flag that says it is ready, paired with a writer's `smp_wmb()` |
| `smp_wmb()` | Prior stores against subsequent stores only | Compiles to a plain compiler barrier — x86-64 does not reorder stores with stores | Publishing a data structure's contents before publishing the flag/pointer that makes it visible |
| `smp_store_release(p, v)` | This store happens after every earlier access in program order (release) | A plain `MOV` — x86-64's store ordering already provides this | Publishing a pointer or flag once initialization is complete |
| `smp_load_acquire(p)` | This load happens before every later access in program order (acquire) | A plain `MOV` — x86-64's load ordering already provides this | Consuming a published pointer or flag before touching what it points at |
| `smp_mb__before_atomic()` / `smp_mb__after_atomic()` | A full barrier specifically around a non-value-returning atomic op (`atomic_inc()`, `atomic_set()`), which otherwise carries no ordering guarantee of its own | Compiles to nothing on x86-64 — LOCK-prefixed atomic RMW instructions are already fully serializing, so no separate barrier instruction is needed | Wrapping `atomic_inc()`/`atomic_dec()`/`atomic_set()` when the surrounding code needs a full fence and the atomic op alone does not provide one |

## Acquire and release, which is what you should reach for

The kernel's spelling of the publish/subscribe pattern is `smp_store_release()` to publish and
`smp_load_acquire()` to consume — reach for this pair before reaching for a bare `smp_mb()`, because it
says exactly what is needed (this store must be visible-after, this load must be visible-before) rather
than a full fence in both directions. The standard shape:

```c
/* Writer: build the object fully, then publish it. */
struct foo *obj = kmalloc(sizeof(*obj), GFP_KERNEL);
obj->a = 1;
obj->b = 2;
smp_store_release(&global_ptr, obj);   /* publish: all prior stores are visible first */

/* Reader: consume the pointer, then trust what it points at. */
struct foo *p = smp_load_acquire(&global_ptr);
if (p)
    use(p->a, p->b);                   /* guaranteed to see the initialized fields */
```

Without the release/acquire pair — a plain `global_ptr = obj;` and a plain `p = global_ptr;` — the code
looks identical and *works on x86-64*, because x86-64's store ordering happens to preserve the order
`obj->a`, `obj->b`, then the pointer store, for free. The same code is broken on arm64, where the CPU is
free to make the pointer store visible to another core before the field stores that precede it in program
order, and the reader can dereference `p` and see uninitialized memory. This is exactly why testing
lock-free kernel code only on x86-64 does not validate it — a missing barrier is invisible there and a
crash on arm64 in production.

## The store-buffer example, in kernel terms

The classic store-buffer litmus test from the CS page, restated with the kernel's own primitives. Two
CPUs, two variables, both initially zero:

```c
/* CPU 0 */                          /* CPU 1 */
WRITE_ONCE(x, 1);                    WRITE_ONCE(y, 1);
r1 = READ_ONCE(y);                   r2 = READ_ONCE(x);
```

`r1 == 0 && r2 == 0` is a real, observable outcome on x86-64 and most other architectures: each CPU's
store to its own variable sits in that CPU's store buffer, not yet visible to the other CPU, when it reads
the other variable — both reads can see the pre-write value. Sequential consistency says this cannot
happen (every interleaving of two single-bit writes followed by two reads produces at least one `1`), and
real hardware violates it anyway, for exactly the performance reason the CS page gives. The fix is a full
barrier on both sides, forcing each CPU's own store to drain before its read:

```c
/* CPU 0 */                          /* CPU 1 */
WRITE_ONCE(x, 1);                    WRITE_ONCE(y, 1);
smp_mb();                            smp_mb();
r1 = READ_ONCE(y);                   r2 = READ_ONCE(x);
```

With both `smp_mb()`s in place, `r1 == 0 && r2 == 0` is no longer possible — each CPU's store is
guaranteed visible to the other before either read executes. Note that `smp_rmb()`/`smp_wmb()` alone do
not fix this: the problem is a store-then-load ordering on each CPU, which only a full barrier (or
`smp_mb__before_atomic()`-style construction around an atomic) provides.

```mermaid
sequenceDiagram
    participant C0 as CPU 0
    participant Obj as Object memory
    participant Ptr as global_ptr
    participant C1 as CPU 1
    Note over C0,C1: Wrong — plain assignment
    C0->>Obj: obj->a = 1; obj->b = 2
    C0->>Ptr: global_ptr = obj (may become visible first)
    C1->>Ptr: p = global_ptr (sees non-NULL)
    C1->>Obj: reads p->a, p->b — may see stale/uninitialized values
    Note over C0,C1: Fixed — release/acquire
    C0->>Obj: obj->a = 1; obj->b = 2
    C0->>Ptr: smp_store_release(&global_ptr, obj)
    C1->>Ptr: p = smp_load_acquire(&global_ptr)
    C1->>Obj: reads p->a, p->b — guaranteed initialized
```

*Publishing a new object without release/acquire: the reader can see the pointer before it can see what
the pointer points at.*

## Dependencies

On almost every architecture the kernel supports, an **address dependency** — computing the address of
the second access from the value read by the first — is an implicit ordering the hardware respects without
any explicit barrier: if `p = READ_ONCE(ptr)` and the next access dereferences `p`, the CPU does not
reorder that dereference ahead of the read that produced the address, because it cannot know the address
to speculate with until the first read completes. `rcu_dereference()` is the kernel's way of expressing
this safely and portably — it reads a pointer with exactly this dependency-ordering guarantee, which is
what lets an RCU reader walk into newly-published data without a full `smp_load_acquire()` on every
pointer chase. The one well-known historical exception is the DEC Alpha, whose split, non-coherent cache
design could break even address dependencies without an explicit barrier — `rcu_dereference()`'s
implementation accounted for this, and it is why the primitive exists as a named abstraction rather than a
plain pointer read, even though Alpha support has since left the tree.

## Where the rules actually live

This page is an orientation, not the authority. `Documentation/memory-barriers.txt`, still present at that
exact path at the v6.18 tag, is the kernel's normative document on memory ordering — long, dense, and
written by the people who designed these primitives. Every claim on this page is checkable against it, and
any real lock-free code should be checked against it directly rather than against this summary.

:::note[arm64]
This is the load-bearing point for the whole page: on x86-64, most `smp_*` barriers — `smp_rmb()`,
`smp_wmb()`, `smp_store_release()`, `smp_load_acquire()` — compile to nothing beyond a plain load or store
or a compiler barrier, because x86-64's hardware ordering already provides what they promise. Code that
omits a barrier the algorithm actually requires will pass every test on the developer's x86-64 machine,
because the hardware silently supplies the missing guarantee, and will fail on an arm64 server the moment
it runs somewhere the guarantee is not free. The practical rule: write the barrier the *algorithm*
requires, determined from what the data actually needs, never the barrier the *target architecture you
tested on* happens to need — those are different questions and x86-64 answers the second one for free far
too often to be a reliable guide to the first.
:::

<KernelFacts
  structure={[["READ_ONCE / WRITE_ONCE", "include/asm-generic/rwonce.h"], ["smp_mb", "arch/x86/include/asm/barrier.h"]]}
  path="initialise object → smp_store_release(&ptr, obj) → other CPU: smp_load_acquire(&ptr) → dereference safely"
  observe="grep -rn 'smp_store_release' /usr/src/linux/kernel/ | head, or read Documentation/memory-barriers.txt"
  trap="On x86-64 most barriers compile to nothing, so barrier bugs are invisible until the code runs on arm64. Testing on x86-64 does not validate ordering — it validates that the code compiles and that x86's model is forgiving." />

## References

- <Src file="Documentation/memory-barriers.txt" /> — the normative document; long, and every serious claim
  about kernel ordering on this page is checkable against it.
- [`tools/rv` runtime verification documentation](https://docs.kernel.org/tools/rv/index.html) and the
  `tools/memory-model/` LKMM tooling in-tree — the formal model and the `herd7` litmus-test tooling, which
  is how ordering questions are settled definitively rather than argued.
- Paul E. McKenney, [*Is Parallel Programming Hard, And, If So, What Can You Do About It?*](https://mirrors.edge.kernel.org/pub/linux/kernel/people/paulmck/perfbook/perfbook.html),
  the memory-ordering chapter — free, and the most patient explanation available.
- [Memory Ordering and Consistency](../../computer-science/cpu-architecture/memory-ordering-and-consistency.md) —
  the hardware model this page assumes.
