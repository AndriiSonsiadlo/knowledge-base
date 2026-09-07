---
id: abi-stability-and-compat
title: "ABI Stability and Compat"
sidebar_label: "ABI stability"
sidebar_position: 8
tags: [linux, kernel, syscalls]
prerequisites:
  - linux/syscalls-and-the-boundary/the-syscall-table-and-dispatch
draft: false
---

# ABI Stability and Compat

"We do not break user space" is usually quoted as a slogan. Treated as an engineering constraint it is
much stricter than it sounds: a binary compiled in 2005, with no source available and no way to recompile
it, must still run correctly on a kernel released this year. That forbids removing a syscall, changing
what an existing argument means, or repurposing a flag bit that some program somewhere might already be
passing — forever, not until the next major version. This page is about what that constraint costs and
the handful of techniques the kernel uses to keep growing its interfaces without ever violating it.

## What the promise covers, and what it does not

Covered, permanently: syscall numbers and their semantics, the `/proc` and `/sys` files that programs
actually parse, the ELF ABI a binary is built against, and signal semantics. If a program written against
any of these today would behave differently on a future kernel in a way that breaks it, that is a
regression the kernel project treats as a bug to be fixed, not a cost of progress.

Not covered: in-kernel interfaces between subsystems, symbols a module calls, `debugfs`, and anything
explicitly documented as unstable. The reasoning for that split — why kernel-internal interfaces are
allowed to change release to release while the syscall surface cannot — is
[exported symbols and the module ABI](../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md);
this page does not restate that argument, only relies on it.

## How interfaces grow anyway

A promise that nothing can ever change sounds incompatible with a kernel that keeps adding features. Three
techniques resolve that tension, all in active use:

- **A new syscall alongside the old one.** `open` never grew a mysterious new argument; instead `openat`
  arrived beside it with a directory-fd parameter, and later `openat2` arrived beside *that* with the
  struct-plus-size argument described below. Old binaries keep calling `open` and get exactly the old
  behavior; new code opts in to the new syscall to get the new behavior. Nothing about `open`'s meaning
  ever moved.
- **A flags argument with reserved bits that must be zero.** This is the subtle one, and it is worth
  stating plainly: requiring an unrecognized flag bit to be rejected — rather than silently ignored — is
  what makes later extension of that flags word safe at all. If an old kernel silently ignored bits it
  didn't understand, a program setting a bit the kernel doesn't yet implement would get no error and no
  effect, and could never afterward be sure whether the bit was "supported and had no effect" or "not
  supported and was ignored." Reject the unknown bit instead, and a program can safely probe for it: call
  with the bit set, and either it works, or you get `-EINVAL` and know the running kernel doesn't have it
  yet. That contract is what turns "we might add a flag in an unused bit" into a plan that actually works
  years later.
- **A struct-plus-size argument.** `clone3`, `openat2`, and `sched_setattr` all take a pointer to a struct
  and the caller's compile-time `sizeof` that struct, rather than a fixed-layout struct with no size at
  all. The kernel compares the caller's size against its own idea of the struct's size and, per the
  zero-fill and rejection rules in the next section, can add fields at the end in a later release without
  breaking a binary compiled against the smaller, older struct.

## What the promise costs

Not every consequence of "never break user space" is elegant. Two interfaces are permanently, provably
ugly because of it, and neither can be cleaned up:

- **The `stat` family.** There are multiple, mutually incompatible `struct stat` layouts across
  architectures and across history — 32-bit and 64-bit time fields, `stat` versus `stat64`, different
  field orderings per architecture ABI. None of them can be deleted, because binaries linked against each
  one still exist and still run. `statx`, added specifically to stop the bleeding, is not a replacement
  that retires the old ones — it is a new syscall taking an explicit, versioned struct so the *next*
  addition doesn't repeat the problem, while `stat`, `fstat`, `lstat`, and their 64-bit variants all stay
  exactly as they are.
- **Syscall numbers with holes.** The syscall table has gaps — numbers that were allocated, sometimes even
  merged briefly, and then withdrawn before a release shipped, leaving the number permanently unused
  rather than reassigned. Once a number has shipped to users in *any* released kernel it can never be
  reused for something else, because a binary built against the old meaning would silently call the wrong
  thing on a kernel that reassigned it. The safe response to a withdrawn or deprecated syscall is to leave
  the number retired, not recycle it.

Nobody chose either of these on purpose. They are the visible scar tissue of not being allowed to break
user space, and they are the honest answer to "why doesn't the kernel just clean this up."

## `compat_`: 32-bit programs on a 64-bit kernel

A 64-bit kernel can still run unmodified 32-bit binaries, and doing so means maintaining a second,
parallel syscall table: a 32-bit program's syscall numbers are looked up in the 32-bit table, which is a
different table from the 64-bit one the same kernel exposes to 64-bit callers — the same syscall can have
a different number, or not exist at all, on each side.

Numbers are only the start. Data layout differs too: pointers and `long`s are 4 bytes wide instead of 8,
structure alignment and padding rules differ, and any structure containing a pointer or a `long` has a
different size and layout in 32-bit user space than the kernel's native 64-bit idea of the same structure.
The kernel handles this with `compat_` variants of syscalls and their argument structures — functions and
types that translate between the 32-bit layout a compat task presents and the native 64-bit layout the
rest of the kernel works with.

Where this leaks into things people actually debug: `struct timespec`'s field widths differ between a
32-bit and 64-bit caller (this is exactly the problem `struct __kernel_timespec` and the various
`_time64` syscalls exist to fix, since the original 32-bit `time_t` overflows in 2038); ioctl argument
structures passed by pointer need a `compat_ioctl` translation if they contain pointers or `long`s; and a
compat task's syscall numbers are drawn from the 32-bit table even while every other part of the kernel it
is running under is the native 64-bit build.

## The seccomp architecture trap

The compat table's existence creates a specific, well-known trap for anything trying to restrict syscalls
by number: a seccomp filter that checks only the syscall number and not which ABI it came from can be
bypassed. A 64-bit process can, in principle, issue a 32-bit-ABI syscall (via `int 0x80` on x86, for
instance), and if the filter only ever inspects `nr` against the 64-bit table's numbering, a number that
means one thing in the 64-bit table can mean something else — something the filter never intended to
allow — in the 32-bit table. The rule that avoids this is to check `arch` before ever looking at `nr`, so
the filter is validating "syscall N in *this specific* table" rather than "syscall number N, whichever
table that happens to resolve against." This is exactly the property that matters once seccomp filters are
covered on their own terms, later in this material.

## Where the promise gets tested

The promise is tested constantly, and the kernel project's own history is the evidence for how seriously
it is taken: patches that changed observable behavior — even behavior everyone privately agreed was a bug
— have been reverted after the fact specifically because some real program depended on the old, buggy
behavior and broke. "It was already wrong" is not, on its own, a defense for changing what a shipped
kernel does.

The rare exception is a deliberate break: removing an interface that genuinely has no remaining callers,
or tightening a behavior that was itself a security hole significant enough that leaving it in place is a
worse outcome than the (rare, and usually announced well in advance) compatibility risk of removing it.
These are treated as exceptional, argued individually, and are not a loophole anyone reaches for casually.

## The three extension techniques, compared

|  | Real example | Old kernel, new caller | New kernel, old caller |
|---|---|---|---|
| New syscall alongside the old | `open` → `openat` → `openat2` | Caller gets `-ENOSYS` calling a syscall number the old kernel never allocated — a clean, unambiguous failure, not a misinterpretation. | Old callers keep calling `open`/`openat` and get exactly the original behavior; nothing about them changed. |
| Reserved flag bits, must be zero | A flags word rejecting any bit outside its currently-defined set | A new flag bit set by a program is rejected with `-EINVAL` — the program can detect this and fall back, rather than silently getting no effect. | An old program passing only zero in the reserved bits is unaffected by whatever the new bit now does, because it never sets it. |
| Struct plus size | `clone3`, `openat2`, `sched_setattr` | A newer, larger struct built by an old kernel's headers is a size mismatch a modern kernel doesn't need to worry about in this direction — the old kernel simply has no knowledge of the larger layout. | A new kernel receiving an old (smaller) struct zero-fills the fields the caller's version doesn't know about, per `copy_struct_from_user` below; a new kernel receiving extra non-zero bytes beyond what it expects rejects the call rather than silently ignoring the tail. |

## Misconceptions

1. **"ABI stability means the kernel's interfaces never change."** They change constantly — new syscalls,
   new flags, new fields — the promise is specifically that *existing* meanings never change, not that the
   surface is frozen.
2. **"A 64-bit kernel just runs 32-bit binaries, no special-casing needed."** It requires an entire
   parallel syscall table and a set of `compat_` translation layers for every structure whose layout
   differs by word width — this is real, maintained code, not an emergent property of the CPU supporting
   both modes.
3. **"Checking the syscall number is enough for a security filter."** It isn't, if the filter doesn't also
   pin the calling ABI — see [the seccomp architecture trap](#the-seccomp-architecture-trap) above.

<KernelFacts
  structure={[["struct open_how", "include/uapi/linux/openat2.h"]]}
  path="openat2(dfd, path, &how, size) → copy_struct_from_user() → size checked against OPEN_HOW_SIZE_VER0 and PAGE_SIZE (-EINVAL / -E2BIG) → unknown trailing fields must be zero (-E2BIG if not) → do_sys_openat2()"
  observe="ls /usr/include/asm/unistd_32.h /usr/include/asm/unistd_64.h && grep -c . /proc/self/status"
  trap="Extensibility comes from rejecting unknown flags and unknown non-zero fields, not ignoring them. An interface that silently ignores a bit or byte it does not understand can never safely define that bit later, because programs already depend on it doing nothing." />

## References

- [The Linux kernel user-space API and ABI](https://docs.kernel.org/admin-guide/abi.html) — the
  project's own statement of what is stable and what is not, with the stability levels defined.
- [`openat2(2)`](https://man7.org/linux/man-pages/man2/openat2.2.html) — the modern extensible-syscall
  pattern in its cleanest form, including the size and zero-fill rules.
- Linus Torvalds, [the "we do not break user space" mail](https://lkml.org/lkml/2012/12/23/75) — the
  rule in its author's own words, worth reading once for the reasoning as much as the tone.
- LWN, [*"clone3(), fchmodat4(), and fsinfo()"*](https://lwn.net/Articles/792628/) — why the
  struct-plus-size convention was adopted for `clone3`/`openat2` and what it replaced.
