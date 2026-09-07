---
id: credentials-and-identity
title: "Credentials and Identity"
sidebar_label: "Credentials"
sidebar_position: 6
tags: [linux, kernel, processes]
prerequisites:
  - linux/processes-and-threads/task-struct-the-anatomy-of-a-task
related:
  - computer-science/operating-systems/processes-and-threads
draft: false
---

# Credentials and Identity

A task's identity is not one number. There are four user IDs, four group IDs, a supplementary group
list, and a capability set, and they are separate fields — not because the kernel is being thorough for
its own sake, but because privilege has to be *droppable*, *restorable*, and *checkable* at different
moments in a program's life, and one number cannot do all three jobs at once. A `passwd`-reading utility
needs to become root briefly, do the one privileged thing, and go back to being an ordinary user without
losing the ability to become root again later if it needs to — that single requirement is most of the
reason this page has four IDs in it instead of one.

## `struct cred`, and why it is a separate object

Every field this page discusses lives in `struct cred` (`include/linux/cred.h`), not directly in
`task_struct`. `task_struct` holds two pointers to it — `cred` and `real_cred` — rather than the fields
themselves, and that indirection is deliberate: `struct cred` is refcounted (`atomic_long_t usage`),
**immutable once published**, and changed by replacing the whole object rather than editing fields in
place. This is exactly [the reference-counting pattern folder 04's reference-counting
page](../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md) describes for kernel
objects in general — nothing frees automatically, lifetime is an explicit counter, and an object that
several things might be looking at simultaneously is never mutated under those observers' feet. Verified
against v6.18: `struct cred` carries `uid`, `gid`, `suid`, `sgid`, `euid`, `egid`, `fsuid`, `fsgid`,
`securebits`, the five `kernel_cap_t` capability sets (`cap_inheritable`, `cap_permitted`,
`cap_effective`, `cap_bset`, `cap_ambient`), a `struct group_info *`, and a union of `int non_rcu` /
`struct rcu_head rcu` used for its deferred-free path (see [RCU-protected
credentials](#rcu-protected-credentials) below) — the struct is even marked `__randomize_layout`.

## The four IDs

| ID | Who you are | What is checked | What you can return to | When it matters |
|---|---|---|---|---|
| **Real UID** (`uid`) | The identity of whoever originally started this process | `getuid()`; who owns this process for accounting and `kill()` permission purposes | N/A — this is the anchor the others are measured against | Almost never checked directly by the kernel; it exists as the stable record of "who" |
| **Effective UID** (`euid`) | The identity used for almost every permission check right now | File permission checks (except the filesystem UID case below), most capability checks | The real or saved UID, via `seteuid()`/`setreuid()` | The one that actually matters for "can this syscall succeed" moment to moment |
| **Saved-set UID** (`suid`) | A stashed copy of what the effective UID was right after `exec()` | Nothing directly — it is never itself checked against a resource | Back to being the effective UID, via `seteuid()`/`setresuid()`, **even by an unprivileged real UID** | The reason a setuid-root program can drop privilege for most of its run and still re-acquire it later without re-`exec`ing |
| **Filesystem UID** (`fsuid`) | Normally tracks `euid` automatically | VFS-layer access checks specifically — file and directory permission bits | Whatever it was before, since it isn't part of the setuid/setresuid family | A Linux-specific historical artefact, added for NFS servers acting on behalf of a client UID without wanting that UID's identity to apply to signal-sending or other non-filesystem privilege — it survives today purely because of the kernel's ABI stability promise, not because anything new is built to use it deliberately |

Every ID above has a matching GID (`gid`, `egid`, `sgid`, `fsgid`) that follows exactly the same rules for
group-based checks; the table only spells out the UID column to keep it readable.

## Transitions

`setuid(x)` is the call people reach for and the one whose semantics are most commonly wrong in memory:
as an unprivileged process, it sets only the effective UID (and, notably, if called by a process with
appropriate privilege, `setuid()` sets *all three* — real, effective, and saved — which is where the
confusion usually starts). `seteuid(x)` sets only the effective UID, leaving the saved UID untouched
deliberately — that is precisely the mechanism a privileged program uses to drop to unprivileged, do
unprivileged work, and come back. `setresuid(r, e, s)` sets all three explicitly and is the only call of
the three whose result is unambiguous without knowing the caller's current privilege level, which is
exactly why [`man 2 setresuid`](#references) recommends it over the historical calls for any code that
needs to reason precisely about the result.

At `exec()` of a setuid binary, the kernel sets the process's effective UID (and saved UID) to the file
owner, while the real UID stays whoever actually invoked it — this is the entire mechanism behind `passwd`
running as root while being launched by an ordinary user, and it is exactly the "unless the binary being
exec'd has the setuid bit set" clause [`exec()` and Binary Formats`](./exec-and-binary-formats.md#what-survives-an-exec)
flags as the one exception to "credentials survive exec unchanged."

The classic mistake is dropping the effective UID and stopping there: `seteuid(unprivileged_uid)` alone
leaves the saved UID still holding the privileged value, so `seteuid(0)` — one call, by the *same*
process — restores full privilege. This is not a bug in `seteuid`; it is the saved UID doing its job.
It becomes a vulnerability the moment a program that intended to drop privilege *permanently* only ever
touched the effective UID, because anything that later hijacks that process (a buffer overflow, an
injected library) inherits the same one-call path back to root.

A **permanent** drop of privilege — the kind a daemon does once at startup and never reverses — has to
clear all three IDs, and the order matters: **supplementary groups first, then the GID, then the UID.**
Groups must go first because dropping the UID first (still root when the group call runs) versus dropping
it last (unprivileged when the group call runs) changes whether `setgroups()`/`initgroups()` is even
permitted to execute — group membership checks are themselves privileged operations, so they must happen
while the process still holds the privilege to perform them, before that privilege is given up by the UID
change that comes after.

## Supplementary groups

Beyond the primary GID, a task carries a list of supplementary group IDs — `struct group_info` pointed at
from `struct cred`, capped at `NGROUPS_MAX` entries (`getconf NGROUPS_MAX` on this system reports
`65536`, the modern Linux value; historically much smaller). Group-based permission checks walk the
*effective* GID first and then this supplementary list, checking each one in turn, until either a match
grants access or the list is exhausted — order beyond "effective GID first" is not otherwise significant
to the check.

## Capabilities, in one paragraph

Root's traditional all-or-nothing privilege is split, in modern Linux, into roughly forty separate
capability bits — `CAP_NET_BIND_SERVICE` to bind a port below 1024, `CAP_SYS_PTRACE` to attach a debugger
to another process's memory, `CAP_SYS_ADMIN` as the catch-all nobody should still be using but plenty of
software still requests — each independently grantable to a non-root process and independently droppable
by a process that has it, through the effective/permitted/inheritable/bounding/ambient sets `struct cred`
carries. The full mechanics of that split — which set means what, how capabilities survive or don't
survive an `exec()`, and how a program can drop capabilities it no longer needs without becoming fully
unprivileged — belong to the security folder later in this section (folder 16) and are only named here.

## RCU-protected credentials

Reading a task's own or another task's credentials — which happens on essentially every permission check
the kernel makes — is a hot path, and `struct cred` is designed so that reading it never takes a lock:
`current_cred()` and friends dereference the `__rcu`-annotated pointer under `rcu_read_lock()`, which on
the read side costs nothing more than disabling preemption. Changing credentials never mutates the
existing object; `setresuid()` and its relatives build an entirely new `struct cred` (via
`prepare_creds()`), populate it, and `commit_creds()` publishes the new pointer with a single atomic
store — any reader that started before the update simply keeps seeing the old, still-valid object until
it finishes, and the old object is freed only once an RCU grace period confirms no reader can still hold
a reference to it. This is the same lock-free-read, replace-then-defer-free discipline [RCU: The
Idea](../09-concurrency-and-locking/rcu-the-idea.md) introduces in general; credentials are one of its
oldest and most frequently exercised users in the kernel.

## How a check actually happens

Take `open()` on a file as the concrete case. The kernel's path-walking code eventually calls
`inode_permission()`, which does two genuinely different things in sequence:

1. **The classic owner/group/other test**, against the file's `struct inode` and the *filesystem* UID and
   GID — not the effective ones — comparing the requested access (read, write, execute) against whichever
   of the inode's three permission triads applies: owner bits if `fsuid` matches the inode's owner, group
   bits if `fsgid` matches (or is among the supplementary groups), other bits otherwise. This is the
   layer every Unix has had since the beginning, and it is a hard "no" if it fails — capabilities and LSMs
   never override a plain "you are not the owner, not in the group, and other has no access" result caused
   by the bits themselves; a process instead needs `CAP_DAC_OVERRIDE`, checked separately, to bypass DAC
   entirely.
2. **The LSM hook** — `security_inode_permission()`, called after the DAC check passes, giving whatever
   Linux Security Module is active (SELinux, AppArmor, or nothing) a chance to say no even when the
   traditional bits say yes. This is a second, independent layer of policy, and folder 16 is where it is
   actually described; the point to take from this page is only that there are two layers, checked in
   this order, and that the first one runs against the filesystem UID specifically — the reason that ID
   exists at all.

## The four UIDs, across a privilege lifecycle

The table below is the reason this page exists: the same four columns, in four different moments of a
program's life. The first row is a real, verified reading from an unprivileged process in this
environment; the remaining three describe a hypothetical setuid-root program and are constructed from the
documented transition rules above (not run — see the caption).

| Scenario | Real UID | Effective UID | Saved UID | Filesystem UID |
|---|---|---|---|---|
| **This shell, right now** (real, `uid=1000`) | 1000 | 1000 | 1000 | 1000 |
| A setuid-root program, just after `exec()`, before dropping anything | 1000 (invoker) | 0 (file owner) | 0 (set to match `euid` at `exec()`) | 0 (tracks `euid`) |
| The same program after a **temporary** drop (`seteuid(1000)`) | 1000 | 1000 | 0 (unchanged — this is the point) | 1000 (tracks `euid` again) |
| The same program after a **permanent** drop (`setresuid(1000, 1000, 1000)`, groups and GID already dropped first) | 1000 | 1000 | 1000 | 1000 |

The real reading above came from this environment's own `/proc/self/status`:

```text
$ grep -E '^(Uid|Gid|Groups|CapEff):' /proc/self/status
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
Groups:	4 24 27 30 46 100 1000 1001
CapEff:	0000000000000000
```

All four UID columns read `1000` because this is an unprivileged process that never called any of the
setuid family — real, effective, saved, and filesystem UID all default to the same value at login, and
`CapEff` is all-zero for the same reason: nothing here has, or has used, any elevated capability. The
middle two rows of the table cannot be produced live in this sandbox — there is no setuid-root binary to
`exec()` and no privilege to demonstrate dropping — so they are written to match `struct cred`'s documented
behavior at `exec()` and at `seteuid()`/`setresuid()` exactly, not captured from a real run; the emphasis
on the saved UID staying at `0` through a *temporary* drop is the single fact the whole table exists to
show.

<Lab host="any-linux" title="Read your own credentials" time="5 min">

```text
$ grep -E '^(Uid|Gid|Groups|CapEff):' /proc/self/status
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
Groups:	4 24 27 30 46 100 1000 1001
CapEff:	0000000000000000
```

The four numbers on the `Uid`/`Gid` lines are real, effective, saved, and filesystem, in that order —
`man 5 proc` documents the column order for `/proc/PID/status`'s `Uid`/`Gid` lines explicitly. `CapEff`
being all-zero here is expected for any ordinary unprivileged login shell; running the same command after
`sudo -s` would show a non-zero mask instead.

**If it fails:** `/proc/self/status` always exists for any process able to run this command at all — there
is no privilege requirement to read your own `/proc/self/`. Reading another process's `/proc/<pid>/status`
does require matching credentials or `CAP_SYS_PTRACE`, the same restriction the process-address-space
page's lab notes for `smaps`.

</Lab>

<KernelFacts
  structure={[["struct cred", "include/linux/cred.h"]]}
  path="setresuid() → prepare_creds() → modify the copy → commit_creds() → old cred released by RCU"
  observe="grep -E '^(Uid|Gid|Groups|CapEff):' /proc/self/status"
  trap="Dropping the effective UID is not dropping privilege. Until the saved set-user-ID is also changed, the process — and anything that hijacks it — can take the privilege back with one call." />

## References

- [Kernel credentials documentation](https://docs.kernel.org/security/credentials.html) — the kernel's
  own account of `struct cred`, including the RCU rules and the "never modify in place" requirement this
  page's [RCU-protected credentials](#rcu-protected-credentials) section is drawn from.
- `man 7 credentials` — the user-space model, the four IDs, and the transition rules in one place.
- `man 2 setresuid` — the call that makes a permanent drop expressible unambiguously, and the reason
  `setuid()` alone is ambiguous about which IDs it touches depending on caller privilege.
- Chen, Wagner & Dean, *"Setuid Demystified,"*
  [USENIX Security 2002](https://people.eecs.berkeley.edu/~daw/papers/setuid-usenix02.pdf). The paper
  that documented how badly these semantics are understood in practice; still the clearest account of the
  transition rules and the order-of-operations mistake this page's [Transitions](#transitions) section
  describes.
