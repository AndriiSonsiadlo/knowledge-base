---
id: switch-root-and-pid-1
title: "`switch_root` and PID 1"
sidebar_label: "switch_root and PID 1"
sidebar_position: 10
tags: [linux, kernel, boot]
prerequisites:
  - linux/boot-and-init/initramfs-and-early-userspace
draft: false
---

# `switch_root` and PID 1

Mounting the real root, the three constantly-confused ways to change it, and what makes PID 1 special.

`chroot`, `pivot_root`, and `switch_root` get used almost interchangeably in conversation, and that's a
problem exactly at the moment [the previous page](./initramfs-and-early-userspace.md) left off: the
initramfs has found and mounted the real root, and now has to hand control to it. The three operations do
three different things, and only one of them is actually a syscall.

Once that handoff happens, PID 1 is running — and PID 1 is not a special program. It is a completely
ordinary process that the kernel treats specially, and every one of those special treatments turns out to
be a consequence of a single fact: it has no parent.

## Three ways to change what `/` means

| Operation | What it does | Old root afterward |
|---|---|---|
| `chroot(2)` | Changes the calling *process's* idea of `/` only — a per-process attribute, not a mount-namespace-wide change | Still mounted, still reachable by anything that didn't `chroot` |
| `pivot_root(2)` | Moves the *mount namespace's* root to a new location and moves the old root to a directory under the new one, atomically | Still mounted, but relocated — reachable at the directory you gave it, so it can be inspected or unmounted |
| `switch_root` | A userspace program (not a syscall) that combines `chroot`/`pivot_root`-style remounting with deleting the old root's contents and `exec`ing the new init | Deleted — its files are removed to free the memory they occupied |

Only the middle row is a syscall — <Src file="fs/namespace.c" symbol="pivot_root" /> — and it is the
primitive `switch_root` is built on. `chroot` changes less than people expect (a process, not a
namespace); `switch_root` changes more (it deletes, not just relocates).

## Why the initramfs deletes itself

The initramfs's rootfs is a `tmpfs` instance — pure page cache, no backing block device — which means
its memory is not freed by unmounting it. Unmounting a `tmpfs` that nothing else references would drop
the *mount*, but the pages holding its file contents stay allocated until nothing holds them, and rootfs
itself can't even be unmounted (it's the mount namespace's root). The only way to get the memory back is
to make the files themselves go away: `switch_root` walks the old root recursively and unlinks
everything in it, *then* `pivot_root`s or `chroot`s onto the new one and `exec`s the new init. That
ordering — delete first, because deleting is what actually frees anything — is the detail that makes
`switch_root` a distinct tool from `pivot_root` rather than a thin wrapper around it.

## What makes PID 1 special

Every item below is a real, separate-looking behaviour. All four trace back to the same cause: PID 1 has
no parent, so nothing about it can be handled the way an ordinary process's equivalent situation is
handled.

| Behaviour | Why |
|---|---|
| Default signal dispositions don't apply | A signal whose default action would kill an ordinary process (e.g. `SIGTERM` with no handler installed) is silently ignored for PID 1 unless PID 1 has explicitly installed a handler for it — see [What actually happens](#what-actually-happens) below |
| `kill -9 1` does nothing | `SIGKILL` and `SIGSTOP` specifically may not be delivered to the global init at all, a special case that overrides even the usual "can't be blocked or ignored" rule for those two signals |
| It inherits every orphan | When a process's parent exits before it does, the kernel reparents it — historically straight to PID 1, and still to PID 1 by default absent a subreaper (below); PID 1 must reap these or they accumulate as zombies |
| If it exits, the kernel panics | There is no process above PID 1 to notice and restart it, so the kernel treats PID 1 exiting — for any reason, including a clean exit — as unrecoverable |

## `PR_SET_CHILD_SUBREAPER`

Reparenting every orphan straight to PID 1 is occasionally the wrong answer — a container runtime or a
session manager wants to reap *its own* subtree's orphans without becoming PID 1 itself. `prctl(2)`'s
`PR_SET_CHILD_SUBREAPER` flag lets any process opt in: once set, orphans within that process's descendant
tree are reparented to it instead of walking all the way up to the real PID 1. This is the mechanism
container supervisors (`tini`, `dumb-init`, and the equivalent built into most container runtimes) and
per-session managers rely on, and it's implemented in the same function that handles the flag itself,
<Src file="kernel/sys.c" symbol="prctl" />.

## What actually happens

**"`kill -9 1` doesn't work because init runs as root and is protected."** It has nothing to do with
permissions — a root shell sending `SIGKILL` to PID 1 is a perfectly permitted syscall that succeeds at
being *sent*. What doesn't happen is delivery, and the reason is two lines in
<Src file="kernel/signal.c" symbol="sig_task_ignored" />:

```c
/* SIGKILL and SIGSTOP may not be sent to the global init */
if (unlikely(is_global_init(t) && sig_kernel_only(sig)))
	return true;
```

`sig_kernel_only()` is true for exactly `SIGKILL` and `SIGSTOP` — the two signals normally guaranteed to
always work — and this check makes them the two signals PID 1 is specifically immune to. Any other signal
without a handler installed is caught by the ordinary "implicitly ignored" path a line above it; PID 1
simply never inherits a default disposition it hasn't asked for.

The other side of the same fact — what happens if PID 1 *does* exit — is a panic, and the message is
worth being able to recognise on sight rather than guess at:

```text
Kernel panic - not syncing: Attempted to kill init! exitcode=0x00000000
```

That string comes straight from <Src file="kernel/exit.c" symbol="do_exit" />, printed the instant the
last thread of the global init process exits, for any reason — a crash, an uncaught signal that *did*
have a handler go wrong, or even a deliberate clean `exit()`. There's no distinction made between "init
crashed" and "init finished successfully"; both are unrecoverable, because there is nothing left for the
kernel to hand control to.

## Misconceptions

- **"PID 1 is unkillable because it's root."** No — permissions were never the mechanism. The kernel
  simply never delivers `SIGKILL`/`SIGSTOP` to the global init, and leaves every other signal at its
  default (ignored) disposition unless PID 1 installs a handler. A non-root user's `kill -9 1` fails on
  permissions before it would even reach this logic; root's succeeds at sending and still does nothing.
- **"`switch_root` is a syscall."** It's a userspace program (`/sbin/switch_root` or systemd's own
  equivalent) built on top of the real syscalls, `pivot_root(2)` and `chroot(2)`/`mount(2)` with
  `MS_MOVE`. The kernel has no `switch_root` entry point of its own.
- **"Zombie processes are a memory leak."** A zombie is a dead process whose exit status hasn't been
  collected yet — it holds almost nothing but a `task_struct` and an exit code, kept around specifically
  so a parent's `wait()` has something to read. It's bookkeeping, not a leak; folder 06 covers process
  lifecycle and reaping in full.

<KernelFacts
  structure={[["pivot_root", "fs/namespace.c — the syscall switch_root is built on"], ["do_exit", "kernel/exit.c — where the init-exit panic is raised"]]}
  path="/init mounts real root at /sysroot → switch_root deletes initramfs contents → pivot_root(2)/chroot(2) → exec /sbin/init as PID 1"
  observe="ps -p 1 -o comm= && ls -l /proc/1/exe"
  trap="If PID 1 exits for any reason, the kernel panics — deliberately. There is no recovery path, because there is nothing left to recover to." />

## References

- [`man 2 pivot_root`](https://man7.org/linux/man-pages/man2/pivot_root.2.html) — the actual syscall, and
  precisely how it differs from `chroot(2)`.
- [`man 8 switch_root`](https://man7.org/linux/man-pages/man8/switch_root.8.html) — the userspace tool,
  and why it deletes the old root rather than merely unmounting it.
- <Src file="kernel/exit.c" symbol="do_exit" /> — where the "Attempted to kill init!" panic is raised,
  for anyone who wants to read the exact condition rather than take this page's word for it.
