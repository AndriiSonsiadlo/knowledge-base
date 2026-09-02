---
id: memory-safety-in-kernel-c
title: "What Goes Wrong in Kernel C"
sidebar_label: "What goes wrong"
sidebar_position: 12
tags: [linux, kernel]
prerequisites:
  - linux/kernel-architecture-and-idioms/reference-counting-and-lifetime
draft: false
---

# What Goes Wrong in Kernel C

This is the catalogue page. Kernel bugs — the ones that end in an oops, a silent corruption, or a security
advisory — fall into a small, recurring number of classes, and each class has a characteristic symptom and
a specific tool built to catch it. None of this is exotic; it is the direct consequence of writing in a
language with manual memory management, in an environment with no allocator safety net, no userspace-style
memory protection between subsystems, and contexts that are not always allowed to sleep. Knowing the list
turns an unfamiliar oops from a mystery into a lookup: match the symptom to a row, and you already know
what kind of bug you're looking at and which tool would have caught it earlier.

## The catalogue

| Bug class | What it looks like | The tool that catches it | Config symbol |
|---|---|---|---|
| Use-after-free | an oops or corrupted data touching memory that was already freed, often far from where it was actually freed | KASAN | `CONFIG_KASAN` |
| Reference-count leak | a slab cache growing without bound in `slabtop`; `refcount_t` warnings in `dmesg` | `refcount_t`'s own saturation warnings, plus slab growth as an external signal | (`refcount_t`, `include/linux/refcount.h` — no separate Kconfig gate; it's always active) |
| Sleeping in atomic context | `dmesg` shows `BUG: sleeping function called from invalid context at <file>:<line>` | the atomic-sleep debug check | `CONFIG_DEBUG_ATOMIC_SLEEP` |
| Unchecked user pointer | an oops inside `copy_to_user`/`copy_from_user`, or data silently read from/written to the wrong address space | sparse's `__user` address-space checking at build time | (build-time via `make C=2`; the annotation itself is `__user`, `include/linux/compiler_types.h`) |
| Integer overflow in a size calculation | an allocation smaller than intended, followed by an out-of-bounds write into it | `struct_size()`/`check_add_overflow()` used at the call site as the fix, rather than a runtime detector | (`include/linux/overflow.h` — again a helper, not a Kconfig-gated sanitizer) |
| Missing bounds check on an array index | an out-of-bounds read or write, or silent data corruption a few bytes past a buffer | KASAN again, or — if unchecked — a silent corruption with no diagnostic at all | `CONFIG_KASAN` |
| Uninitialised stack or heap memory | information leaked to user space, or logic that depends on whatever garbage happened to be on the stack | stack-init hardening, and KMSAN for a full data-flow detector | `CONFIG_INIT_STACK_ALL_ZERO`, `CONFIG_KMSAN` |
| Data race | two CPUs accessing the same memory concurrently with at least one unsynchronised write; symptoms range from silent corruption to nothing observable for a long time | KCSAN | `CONFIG_KCSAN` |

A `###` note on each, beyond the table:

### Use-after-free

The object was freed — its memory returned to the slab allocator, and often reused for something else
entirely by the time the bug fires — but a pointer to it is still dereferenced somewhere. This is the bug
class [the previous page](./reference-counting-and-lifetime.md) exists to prevent through disciplined
`get`/`put` pairing; when the pairing is wrong anyway, KASAN is what turns a silent, timing-dependent
corruption into an immediate, reproducible report at the exact instruction that touched freed memory.

### Reference-count leak

The mirror image: a `get` with no matching `put`. Nothing crashes — the object just never gets freed. The
signal is external, not a report from the counter itself: a slab cache visibly growing in `slabtop -o`
over time with no corresponding drop.

### Sleeping in atomic context

Certain contexts — holding a spinlock, inside an RCU read-side critical section, with preemption or
interrupts disabled — must not call anything that can sleep, because there is nothing that could
reschedule the CPU back to this code later; a sleep there either deadlocks or corrupts scheduler state.
`CONFIG_DEBUG_ATOMIC_SLEEP` instruments every function that can sleep to check, on entry, whether it is
being called from such a context, and reports it immediately if so.

### Unchecked user pointer

A pointer that came from user space must never be dereferenced directly by kernel code — it has to go
through `copy_from_user()`/`copy_to_user()` (or an equivalent), which validate the address range before
touching it. `__user` is sparse's way of marking a pointer as living in a different address space at the
type level, so `make C=2` flags any direct dereference of a `__user` pointer as a type error at build time,
long before it would otherwise become a crash or an information leak at runtime.

### Integer overflow in a size calculation

`kmalloc(a * b)`, where `a` and `b` are both attacker-influenced, can overflow to a small number, allocate
a small buffer, and then have the rest of the function write into it as though the multiplication hadn't
wrapped — a classic path to a heap overflow. `struct_size()` and `check_add_overflow()` (and the sibling
helpers in the same header) exist so the calculation itself either can't overflow or is checked before
it's used, which is a fix applied at the call site rather than a sanitizer that catches the consequence
later.

### Missing bounds check on an array index

An index computed from untrusted input, used without a range check, reads or writes outside the array —
sometimes loudly (KASAN catches it immediately if the sanitizer is built in), sometimes completely
silently, corrupting whatever happens to sit next in memory with no diagnostic at all if it isn't.

### Uninitialised stack or heap memory

A variable read before it's written exposes whatever bit pattern happened to already be in that memory —
which can be genuinely sensitive data left over from a previous, unrelated use of the same stack frame or
allocation. `CONFIG_INIT_STACK_ALL_ZERO` closes the easy case by zeroing stack variables at function entry;
KMSAN is the thorough version, tracking the initialised/uninitialised state of every byte through the
program and reporting the first use of an uninitialised value, including cases stack-zeroing alone doesn't
cover (uninitialised heap memory, for instance).

### Data race

Two CPUs touching the same memory location concurrently, with at least one of them writing and no lock,
atomic, or memory barrier serialising the two accesses, is a data race — legal-looking C that is undefined
behaviour under the C memory model regardless of whether it happens to "work" on a given compiler and
architecture. KCSAN instruments memory accesses and watches for exactly this pattern at runtime.

## Why these specifically

Each row in the catalogue is a direct consequence of a property of the environment kernel code runs in,
not an arbitrary list:

- **No allocator safety net.** User-space allocators increasingly ship guard pages, quarantines, and
  randomisation by default; the kernel's core slab allocator does not, by default, do any of that — which
  is exactly why KASAN exists as an opt-in layer instead of being baked into the allocator unconditionally
  (the cost would be paid by every production kernel, all the time).
- **Contexts that may not sleep.** A kernel has no single "the CPU is busy, try again later" — some code
  runs with interrupts or preemption disabled, where sleeping is simply not a legal option, and nothing
  else in the type system marks a function as "safe to call from atomic context."
- **An unforgeable boundary crossed by ordinary-looking pointers.** A `__user` pointer and a kernel pointer
  are the same C type, `void *`, with nothing at the language level distinguishing them — sparse's
  annotation is bolted on specifically because C itself has no way to make that distinction a type error.
- **A stack that is small and not forgiving.** Kernel stacks are a fixed, small size (commonly 8 KiB or
  16 KiB depending on architecture and configuration) with no guard page expansion the way a user-space
  thread stack can have — an overflow or an uninitialised read on the kernel stack has much less room to
  go unnoticed than the equivalent bug in a user-space program with megabytes of stack to spare.

## The tools, in one paragraph each

**KASAN** (Kernel Address Sanitizer) instruments every memory access to detect use-after-free and
out-of-bounds reads/writes, immediately and at the exact faulting instruction, by poisoning freed and
redzone memory and checking accesses against that poison. It has multiple modes (generic, software-tag,
hardware-tag) trading detection precision against overhead, and its overhead — both in memory and in CPU
time — is substantial enough that it is a debug-kernel tool, not something production kernels ship with
enabled.

**KCSAN** (Kernel Concurrency Sanitizer) detects data races by instrumenting memory accesses and watching
for concurrent, unsynchronised accesses to the same location from different CPUs, at least one of which is
a write. It is probabilistic — a race has to actually be hit while a watchpoint happens to be armed on
that address — so more testing surfaces more races, rather than a single clean run proving their absence.

**KMSAN** (Kernel Memory Sanitizer) tracks the initialised/uninitialised state of every byte of memory
through the program and reports the first point an uninitialised value is used in a way that matters — a
branch on it, or copying it somewhere observable — catching the class of bug that stack-zeroing alone
narrows but doesn't fully close.

**Lockdep** validates locking correctness — it builds a graph of lock acquisition ordering as the kernel
actually runs and reports the first sequence that could deadlock, even if that exact sequence hasn't
actually happened yet on this particular run.

**The `CONFIG_DEBUG_*` family** (of which `CONFIG_DEBUG_ATOMIC_SLEEP` is one member) is a broad set of
narrower, cheaper runtime assertions — sleeping in atomic context, using a lock incorrectly, list
corruption, and more — each checking one specific invariant rather than instrumenting every memory access
the way KASAN does.

All of these cost real performance, several cost real memory, and all of them are built for debug kernels,
not production ones — using them deliberately, and interpreting what they report, is covered properly in
folder 17.

## Rust for Linux at v6.18

As of **December 2025**, the Linux kernel's Rust support moved from an explicitly labelled experiment to
an accepted part of the kernel's development model: at the Kernel Maintainers Summit that month, the
consensus among maintainers — reported by LWN — was that the "Rust experiment" the kernel had been running
since Rust support first merged in 2022 had succeeded, and a patch was submitted the same month to remove
the "experimental" framing from the kernel's own documentation and `Kconfig` help text. `RUST`
(`init/Kconfig`) remains an opt-in build option — `depends on HAVE_RUST` and a suitable toolchain — not
something enabled unconditionally, and the `MAINTAINERS` file lists Rust support itself with status
`Supported`.

Concretely, at this point in time: the Android Binder driver was merged in Rust for Linux 6.18 itself; Rust
network PHY drivers exist for several vendors; the Nova project (a Rust successor to the Nouveau NVIDIA GPU
driver, led by Red Hat) has pieces merged into mainline; and Asahi Linux's AGX GPU driver for Apple Silicon
is a substantial real-world Rust driver outside the mainline PHY/driver-core work. This is presented as a
directional, dated snapshot, not a permanent fact — the pace of Rust adoption in the kernel has been fast
and is worth re-checking against [the kernel's own Rust documentation](https://docs.kernel.org/rust/) and
current LWN coverage rather than trusted indefinitely from this page.

None of that touches this section. Every page in `docs/linux/` describes and quotes C — the dialect, the
idioms, the data structures, the object model above — because that is overwhelmingly what the kernel you
are reading, tracing, and debugging in this section's labs is written in. Rust-for-Linux is a real and
growing part of the kernel; it is simply not what this section teaches.

<KernelFacts
  structure={[["CONFIG_KASAN", "lib/Kconfig.kasan"], ["CONFIG_DEBUG_ATOMIC_SLEEP", "lib/Kconfig.debug"]]}
  path="symptom in dmesg → bug class → the sanitizer that proves it → the config symbol that enables that sanitizer"
  observe='dmesg | grep -iE "BUG:|KASAN|WARNING:"'
  trap="A kernel built without the sanitizers will happily run code with a use-after-free in it, sometimes for weeks. The absence of a report is the absence of a detector, not the absence of the bug." />

## References

- [The Kernel Address Sanitizer (KASAN)](https://docs.kernel.org/dev-tools/kasan.html) — what KASAN
  detects, its modes, and its cost; the single most useful debug option in this catalogue.
- [Kernel Debugging Tricks and the debugging tools index](https://docs.kernel.org/dev-tools/index.html)
  — the full tool inventory this page's "tools" section draws from, and the index folder 17 builds on.
- [Rust](https://docs.kernel.org/rust/) — the kernel's own current statement of Rust support status;
  check its date against this page's December 2025 snapshot before trusting either.
