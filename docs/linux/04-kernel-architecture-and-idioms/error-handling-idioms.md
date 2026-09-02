---
id: error-handling-idioms
title: "Error Handling"
sidebar_label: "Error handling"
sidebar_position: 9
tags: [linux, kernel]
prerequisites:
  - linux/kernel-architecture-and-idioms/the-kernel-c-dialect
draft: false
---

# Error Handling

C has no exceptions, no `try`/`catch`, and no automatic unwinding. The kernel has instead settled on one
error convention and applied it with unusual discipline: a function that can fail returns a negative
`errno` value — or, when it must return a pointer, encodes that same value *inside* the pointer — and every
caller checks it before doing anything else with the result. Nothing here is exotic. What makes unfamiliar
kernel code readable on first read is that this convention is followed everywhere, without exception, from
the deepest helper function to the syscall return path.

## Negative errno, all the way down

A kernel function that can fail and has no other value to return uses `int`: zero for success, a negative
`-E...` constant for failure. `-ENOMEM`, `-EINVAL`, `-ENOENT` — the same symbolic names user space knows
from `errno.h`, just negated and returned directly instead of stashed in a global.

```c
int foo_open(struct foo *f)
{
	if (!f)
		return -EINVAL;
	if (foo_is_busy(f))
		return -EBUSY;
	/* ... */
	return 0;
}
```

The convention holds at every layer except one: the boundary itself. A syscall implementation still
returns a negative `errno` internally, but the assembly trampoline that returns to user space turns that
negative value into the pair user space actually sees — a return value of `-1` and `errno` set to the
positive magnitude. libc performs that last translation; see
[the kernel/user-space boundary](../00-overview/the-kernel-userspace-boundary.md) for where that handoff
happens. Inside the kernel, `errno` as a variable does not exist — every function that can fail just
returns the value.

## `ERR_PTR`, `PTR_ERR`, `IS_ERR`

The negative-return convention has one gap: a function that returns a pointer on success has no int slot
left over for an error code. It cannot return `-ENOMEM` — a `-12` cast to a pointer looks exactly like a
valid pointer to address `0xfffffffffffffff4`, and every real caller would treat it as one.

The kernel's fix is to notice that this address is not actually reachable. On every architecture the
kernel runs on, the top of the address space — the last few thousand bytes below the highest possible
pointer value — is never a valid kernel allocation; nothing legitimate is ever mapped there. That leaves a
small range of "pointer values" free to mean something else. `ERR_PTR`, `PTR_ERR`, and `IS_ERR`, all
defined in `include/linux/err.h`, are the encoding:

```c
#define MAX_ERRNO	4095

#define IS_ERR_VALUE(x) unlikely((unsigned long)(void *)(x) >= (unsigned long)-MAX_ERRNO)

static inline void * __must_check ERR_PTR(long error)
{
	return (void *) error;
}

static inline long __must_check PTR_ERR(__force const void *ptr)
{
	return (long) ptr;
}

static inline bool __must_check IS_ERR(__force const void *ptr)
{
	return IS_ERR_VALUE((unsigned long)ptr);
}
```

Derived, in order:

- **Why the top page is safe.** `MAX_ERRNO` is 4095 — every kernel `errno` value fits in twelve bits. A
  negative `errno` cast to an unsigned pointer-sized integer lands in the last 4096 bytes below the
  maximum representable address (`-1` through `-4095`, read as unsigned, are `0xfff...fff` down to
  `0xfff...f01`). No valid pointer the allocator ever hands out falls in that page, so any pointer value
  that high is unambiguously an encoded error, never a real object.
- **`ERR_PTR`** just casts the negative `long` to a pointer — no arithmetic, the bit pattern is already
  right.
- **`PTR_ERR`** casts it back to a `long` — also no arithmetic. The two are exact inverses.
- **`IS_ERR`** is the actual check: "is this pointer's value at or above `-MAX_ERRNO`, read as unsigned."
  A genuinely `NULL` pointer (`0`) fails that check — `IS_ERR(NULL)` is false. That is deliberate, and it
  is also the sharp edge: some kernel APIs return `NULL` for "not found" and an `ERR_PTR` only for a real
  failure, so callers of those APIs need `IS_ERR_OR_NULL()` instead of `IS_ERR()` alone, and callers of
  APIs that never legitimately return `NULL` should keep using plain `IS_ERR()` so a stray `NULL` is still
  caught as a bug.

The bug this whole mechanism exists to prevent, and also enables: checking only `if (!ptr)` on a function
that can return an `ERR_PTR`. An encoded error is never `NULL`, so that check passes, and the caller
dereferences a pointer sitting a few hundred bytes below the top of the address space — a fault that looks
nothing like a null-pointer deref and takes real debugging to trace back to a missing `IS_ERR()`.

## `goto` unwinding

Acquiring several resources in sequence — memory, then a lock, then a device handle — and needing to
release whichever subset was actually acquired if a later step fails, is the single most common shape of
kernel error handling. The kernel's answer is a `goto` to a label named for what it undoes, with the
labels arranged in reverse acquisition order:

```c
static int widget_probe(struct device *dev)
{
	struct widget *w;
	int err;

	w = kzalloc(sizeof(*w), GFP_KERNEL);
	if (!w)
		return -ENOMEM;

	err = clk_prepare_enable(w->clk);
	if (err)
		goto err_free;

	err = request_irq(w->irq, widget_isr, 0, "widget", w);
	if (err)
		goto err_clk;

	dev_set_drvdata(dev, w);
	return 0;

err_clk:
	clk_disable_unprepare(w->clk);
err_free:
	kfree(w);
	return err;
}
```

| Acquired | On success, released by | On failure at this step, undone by |
|---|---|---|
| `w` (allocation) | `dev_set_drvdata` outlives the function; freed later at teardown | `err_free` → `kfree(w)` |
| `w->clk` (enabled) | left enabled, owned by the device from here on | `err_clk` → `clk_disable_unprepare(w->clk)` |
| `w->irq` (requested) | left requested, owned by the device from here on | no label needed — it is the last acquisition, so a failure here has nothing after it to unwind besides the two before it |

*Each row is one acquisition; its "undone by" column is the label the corresponding failure jumps to,
and the labels run in exactly the reverse of the acquisition order above them.*

Three acquisitions — the allocation, the clock, the IRQ — three failure points, three labels, each
undoing exactly the acquisitions that happened before it and no more. `err_clk` falls through into
`err_free` on purpose: undoing the IRQ's prerequisite (the clock) and then the clock's prerequisite (the
allocation) is the same reverse-order unwind a stack of destructors would give you in a language that has
them.

This is not a workaround to be embarrassed about — it is the closest C gets to RAII, and it is *correct*
here for concrete reasons: the success path — the sequence of steps that runs when nothing fails — stays
at one indentation level with no nesting, which is the path most readers trace first and most reviewers
scrutinise hardest; every acquisition's undo sits in exactly one place instead of being duplicated at each
failure site; and it is what every kernel reviewer has been trained to expect, so a probe function that
uses `goto` unwinding reads as idiomatic on sight, while one that nests `if` blocks three deep to avoid a
`goto` reads as unfamiliar with the codebase.

The three return conventions this page has now covered are not interchangeable — each fits a different
shape of function:

| Convention | Shape | Success value | Failure value | Used for |
|---|---|---|---|---|
| `int` errno | returns a status, no data | `0` | negative `-E...` | functions with no natural value to return, or where the only output is pass/fail |
| `ERR_PTR`/`PTR_ERR` | returns a pointer | a valid pointer | an encoded negative value, same pointer type | functions whose entire purpose is to hand back an object, and `NULL` is not available or not distinguishable from failure |
| `bool` + out-parameter | returns a truth value plus data | `true`, data written through the pointer | `false`, data left untouched | functions where "did it work" and "what's the value" are naturally two separate questions, e.g. `kstrtoint()`-style parsers |

*Which convention a function uses is part of its contract — mixing them up at a call site (checking an
`ERR_PTR`-returning function for `NULL`, or an errno-`int` function for negativity when it actually
returns a `bool`) is a real, common bug class.*

## `__must_check` and the warnings that matter

`ERR_PTR`, `PTR_ERR`, and `IS_ERR` above are all declared `__must_check`
(`#define __must_check __attribute__((__warn_unused_result__))`, in `include/linux/compiler_attributes.h`)
— the compiler warns, under `-Wunused-result`, if the caller discards the return value entirely. It is
narrow protection: it catches "called `IS_ERR()` and threw away the answer," not "checked the wrong thing"
or "checked it but handled it incorrectly." A function is marked `__must_check` specifically because
ignoring its result is very likely a bug — an allocator, a registration function, anything whose failure
silently leaves the system in a state the rest of the function assumes did not happen.

## Error propagation across layers

The default when a called function fails is to return its error unchanged:

```c
ret = some_subsystem_call(...);
if (ret)
	return ret;
```

Only replace the value with a different one if the caller genuinely has more information than the callee
did — for instance, translating a generic `-EINVAL` from a parser into a more specific `-ENOTSUPP` once
the caller knows *which* unsupported feature was requested. The anti-pattern is flattening every possible
failure from a called function down to one generic code, usually `-EIO`, "just in case." It destroys
information a caller three layers up might have used to give user space a specific, actionable error, and
it makes `strace` output on the failing syscall useless for diagnosis — every failure in that code path
looks identical from outside.

<KernelFacts
  structure={[["IS_ERR() / PTR_ERR() / ERR_PTR()", "include/linux/err.h"]]}
  path="deep helper returns -E... → propagated up unchanged → syscall layer → user space sees -1 and errno"
  observe="include/linux/err.h — `IS_ERR`/`PTR_ERR`/`ERR_PTR` (a structural page like this one has no single runtime command; the header is under a hundred lines and reads faster than any command's output would explain it)"
  trap="A function returning a pointer may return an encoded error, and it is not NULL. Checking only for NULL passes an ERR_PTR straight into a dereference, and the fault address will look like a wild pointer near the top of the address space." />

## References

- <Src file="include/linux/err.h" /> — the whole encoding in well under a hundred lines; reading it once
  is worth more than any explanation of it.
- [Linux kernel coding style, section 7: Centralized exiting of functions](https://docs.kernel.org/process/coding-style.html)
  — the `goto` unwinding convention stated as house policy, in the kernel's own words.
- `man 3 errno` — the value set the kernel's negative returns are drawn from, and how user space actually
  observes them.
