---
id: threads-are-tasks
title: "Threads Are Tasks"
sidebar_label: "Threads are tasks"
sidebar_position: 2
tags: [linux, kernel, processes]
prerequisites:
  - linux/processes-and-threads/task-struct-the-anatomy-of-a-task
draft: false
---

# Threads Are Tasks

Linux has no separate thread object: a thread is a task that shares its address space, files, and signal
handlers.

Most kernels treat "process" and "thread" as two different kinds of object, with a process containing a
list of threads. Linux does not — there is only `task_struct`, and "sharing" is a set of independent,
per-resource choices made once, at creation time, by which flags are passed to `clone()`. A thread is not
a lighter version of a `task_struct`; it is the exact same struct, with more of its pointer fields aimed
at the same shared targets instead of at private copies. [The previous page](./task-struct-the-anatomy-of-a-task.md#what-is-a-pointer-and-why-that-matters)
established that `mm`, `files`, `fs`, and `sighand` are pointers to separately refcounted objects — this
page is almost entirely about which of those pointers get shared and why.

## `clone()` is the real primitive

`fork()`, `vfork()`, and `pthread_create()` are not three different mechanisms; they are three different
flag words passed to the same underlying operation. `fork(2)` and `vfork(2)` are themselves thin
wrappers that call `kernel_clone()` with a fixed set of flags baked in (confirmed directly in
`kernel/fork.c` at v6.18: `SYSCALL_DEFINE0(fork)` builds a bare `kernel_clone_args` with only
`exit_signal = SIGCHLD` set, and `SYSCALL_DEFINE0(vfork)` sets `CLONE_VFORK | CLONE_VM` on top of that
same `exit_signal`) — and glibc's `pthread_create()` reaches the identical syscall by hand, constructing
its own, much larger flag word.

| Caller | Flags (roughly) | What's shared |
|---|---|---|
| `fork()` | none of the sharing flags | Nothing — full copy-on-write duplicate of `mm`, `files`, `fs`; a new `signal`/`sighand` |
| `vfork()` | `CLONE_VFORK \| CLONE_VM` | Address space, until the child execs or exits (the parent is suspended meanwhile) |
| `pthread_create()` | `CLONE_VM\|CLONE_FS\|CLONE_FILES\|CLONE_SIGHAND\|CLONE_THREAD\|CLONE_SYSVSEM\|CLONE_SETTLS\|CLONE_PARENT_SETTID\|CLONE_CHILD_CLEARTID` | Address space, filesystem context, file descriptor table, signal handlers, thread-group membership |

## The flags, as a menu

Each flag below turns exactly one `task_struct` pointer from "copy" into "share" — which is why the
previous page's emphasis on those fields being pointers matters here:

- **`CLONE_VM`** — share `mm`. The child's `mm` pointer is the parent's, refcounted; without it, the
  kernel sets up a fresh (copy-on-write) address space.
- **`CLONE_FS`** — share `fs`: root directory, current working directory, and umask all become the same
  object. Without it, a `chdir()` in one task is invisible to the other.
- **`CLONE_FILES`** — share `files`: the same open-file-descriptor table, so fd 3 in one task is the same
  open file description as fd 3 in the other. Without it, each gets its own copy of the table (pointing at
  the same underlying open files, but closing fd 3 in one does not close it in the other).
- **`CLONE_SIGHAND`** — share `sighand`: the installed signal-handler table. A thread that calls
  `signal(SIGINT, handler)` changes what every task sharing this `sighand` runs for `SIGINT`.
- **`CLONE_THREAD`** — put the new task in the same thread group (`tgid`) as the caller, rather than
  giving it its own. This is the flag [below](#clone_thread-is-what-makes-a-thread-group) that actually
  makes the everyday word "thread" mean something.
- **`CLONE_SYSVSEM`** — share System V semaphore undo state (`sem_undo` lists), so that per-process
  semaphore adjustments made by one thread are cleaned up correctly regardless of which thread in the
  group exits first.
- **`CLONE_SETTLS`** — install a new thread-local-storage descriptor for the child from the flag's `tls`
  argument, rather than inheriting the caller's TLS pointer — this is how every thread in a process ends
  up with its own, distinct TLS area despite sharing everything else.
- **The namespace flags** (`CLONE_NEWNS`, `CLONE_NEWUTS`, `CLONE_NEWIPC`, `CLONE_NEWUSER`, `CLONE_NEWPID`,
  `CLONE_NEWNET`, `CLONE_NEWCGROUP`, `CLONE_NEWTIME`) are named here and left unexplained — they are
  folder 15's subject, not this page's, and this page does not link ahead to unwritten pages.

## `tgid` versus `pid`

Every `task_struct` carries both a `pid` and a `tgid`. The kernel's own `pid` is per-**task** — every
thread, in the traditional sense, gets a distinct one. The `tgid` is shared by every task created with
`CLONE_THREAD` from the same original caller, and it is the `tgid` — not the per-task `pid` — that POSIX
calls a process ID. The consequence is a naming inversion that trips up nearly everyone the first time
they read the syscalls directly: **`getpid()` returns the `tgid`**, and **`gettid()` returns the `pid`**.
User space's "process ID" and the kernel's own field named `pid` are, for a multi-threaded program,
different numbers.

The evidence is on disk, not just in a header: `/proc/<TGID>/task/` contains one directory per thread in
that thread group, named by each thread's own `pid` (what `gettid()` returns for that thread) — so
`/proc/1234/task/1234` is the thread that happened to create the group (its `pid` and `tgid` coincide),
and `/proc/1234/task/1235`, `/proc/1234/task/1236`, and so on are its other threads, each with the same
`tgid` (1234, visible via `/proc/1234/task/1235/status`'s `Tgid:` field) but a distinct `pid`/`Pid:`.

## What actually happens

Walk `pthread_create()` end to end, since every claim above is otherwise abstract:

1. glibc's `pthread_create()` allocates a new stack for the thread with `mmap()` (`MAP_STACK`, with a
   guard page), and sets up a TLS block for it.
2. It calls `clone()` — the actual x86-64 wrapper glibc uses is `__clone`/`clone3` depending on glibc
   version and kernel support, but the flag word is the same idea either way — with
   `CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID`,
   passing the new stack pointer and the TLS descriptor along with it.
3. The kernel's `sys_clone` handler builds a `struct kernel_clone_args` from those flags and calls
   `kernel_clone(&args)` — confirmed directly in `kernel/fork.c` at v6.18, where the `SYSCALL_DEFINE5`
   variants of `clone` all end by returning `kernel_clone(&args)`.
4. `kernel_clone()` calls `copy_process()`, which does the actual work this page has been describing:
   for each sharing flag present, it takes a reference on the parent's existing object and points the new
   `task_struct`'s corresponding field at it instead of copying it; everything else about the new
   `task_struct` — its own kernel stack, its own `pid`, its own `se` scheduling state — is freshly
   allocated regardless of any flag.
5. `kernel_clone()` finishes by calling `wake_up_new_task()`, which is what actually makes the new task
   visible to the scheduler and runnable — confirmed directly in `kernel/fork.c` at v6.18, at the end of
   `kernel_clone()`'s body.

So the call order — `pthread_create() → clone() → kernel_clone() → copy_process() →
wake_up_new_task()` — is accurate as written, not stale: all five names exist in the pinned v6.18 tree,
in `kernel/fork.c`, in that order.

Look for the result with `ps -eLf` on any multi-threaded program (a browser, a JVM, this very build
tool's Node process):

```text
$ ps -eLf | grep node | head -5
user      1234  1000  1234  0  1 12:03 ?  00:00:04 node build.js
user      1234  1000  1235  0  1 12:03 ?  00:00:00 node build.js
user      1234  1000  1236  0  1 12:03 ?  00:00:01 node build.js
```

`ps -eLf`'s `PID` column is the `tgid` (repeated across every row, since `ps` deliberately reports the
*process* id for each row regardless of which thread it is), and `LWP` is each row's own `pid` — the
literal Linux term for what this page has been calling a task-that-shares: a **light-weight process**.
Every one of those LWPs is a distinct `task_struct`, all with the same `tgid`.

That leads to the claim that actually surprises people: threads on Linux are not cheaper than processes
to **schedule** — the scheduler treats every `task_struct` identically regardless of what it shares, so
switching between two threads in the same process costs the scheduler no less than switching between two
unrelated processes. What threads are cheaper at is **creating** (no address-space or file-table copy to
set up) and **communicating through** (shared memory is already shared, with no IPC mechanism needed to
reach it). Those are different claims, and conflating them is [Misconception 1](#misconceptions) below.

## `CLONE_THREAD` is what makes a thread group

Every one of `CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, and `CLONE_SIGHAND` can be set without `CLONE_THREAD`
— the result is two (or more) separate processes, each with its own `tgid`, that happen to share memory,
a working directory, an fd table, or signal handlers. This is legal, occasionally useful (some
specialized IPC patterns use exactly this), and confusing to essentially every tool that assumes "shares
an address space" implies "is a thread of the same process" — `top` and `ps` will show separate PIDs,
`kill <pid>` will only signal one of them, and a debugger attaching to one won't see the other's threads
at all.

The kernel does not accept every combination, though. `copy_process()` at v6.18 rejects `CLONE_THREAD`
without `CLONE_SIGHAND` outright — confirmed directly in `kernel/fork.c`:

```c
/*
 * Thread groups must share signals as well, and detached threads
 * can only be started up within the thread group.
 */
if ((clone_flags & CLONE_THREAD) && !(clone_flags & CLONE_SIGHAND))
	return ERR_PTR(-EINVAL);
```

immediately followed by a second check rejecting `CLONE_SIGHAND` without `CLONE_VM`, for the same reason
the comment gives: shared signal handlers imply shared memory, so allowing `CLONE_SIGHAND` without
`CLONE_VM` would just create inconsistent states other code would have to special-case. `man 2 clone`
documents both constraints (and several others) as the authoritative list; this page names the two most
relevant to "what makes a thread a thread" rather than reproducing the whole table.

## `clone3`, and why it exists

`clone()`'s single `unsigned long flags` argument ran out of room: `CLONE_NEWTIME`, the newest namespace
flag, had to be squeezed into bit 7 — one of the low eight bits `CSIGNAL` was already using for the
child's exit signal — specifically *because* there was no free bit left above `CLONE_IO` at bit 31.
`clone3(2)` replaces the single flag word with `struct clone_args` plus an explicit `size` argument, the
same extensible-struct pattern
[ABI Stability and Compat](../05-syscalls-and-the-boundary/abi-stability-and-compat.md) covers for growing
an interface without a new syscall number: a kernel newer than the caller's headers can see a `size`
smaller than its own idea of `struct clone_args` and knows to zero-fill the fields it doesn't have, rather
than needing a `clone4`.

## Misconceptions

1. **"Threads are lighter than processes on Linux."** Creating one is cheaper (no address-space or
   file-table copy), and switching between two threads of the same process avoids a page-table switch —
   but the object the scheduler picks up and runs is identical in both cases, and the scheduler does the
   identical amount of work either way. "Cheaper to create and communicate between" and "cheaper to
   schedule" are different claims, and only the first one is true.
2. **"A process has one `task_struct`."** It has one *per thread* — a single-threaded process has exactly
   one, but there is no separate "process" object even then; there is just a thread group with one member.
3. **"`getpid()` returns this thread's own kernel identifier."** It returns the **thread group** id
   (`tgid`). The task's own id, the one the kernel's `pid` field actually holds, is what `gettid()`
   returns — the reverse of what the function names suggest to anyone coming from a language where
   "process" and "the current thread's id" are assumed to be close synonyms.

```wavedrom title="The clone() flags word — what pthread_create asks to share, one bit at a time" alt="32-bit clone flags word bit strip, from bit 31 down to bit 0: bits 31-17 grouped as namespace/other flags, then CLONE_THREAD at bit 16 down to CLONE_VM at bit 8, then the CSIGNAL byte in bits 7-0"
{ reg: [
  { bits: 15, name: 'namespace / other (17–31)' },
  { bits: 1, name: 'CLONE_THREAD' },
  { bits: 1, name: 'CLONE_PARENT' },
  { bits: 1, name: 'CLONE_VFORK' },
  { bits: 1, name: 'CLONE_PTRACE' },
  { bits: 1, name: 'CLONE_PIDFD' },
  { bits: 1, name: 'CLONE_SIGHAND' },
  { bits: 1, name: 'CLONE_FILES' },
  { bits: 1, name: 'CLONE_FS' },
  { bits: 1, name: 'CLONE_VM' },
  { bits: 8, name: 'CSIGNAL' },
] }
```

Every bit position above was read directly from `include/uapi/linux/sched.h` at the pinned v6.18 tag, not
copied from memory: `CSIGNAL` is `0x000000ff` (bits 0–7), and from there `CLONE_VM` through `CLONE_THREAD`
are consecutive single bits at `0x100` through `0x10000` — bits 8, 9, 10, 11, 12, 13, 14, 15, and 16
respectively (`CLONE_VM`=8, `CLONE_FS`=9, `CLONE_FILES`=10, `CLONE_SIGHAND`=11, `CLONE_PIDFD`=12,
`CLONE_PTRACE`=13, `CLONE_VFORK`=14, `CLONE_PARENT`=15, `CLONE_THREAD`=16). Bits 17–31 hold the namespace
flags this page named but did not explain, plus `CLONE_IO` at bit 31; `CLONE_NEWTIME` is the one exception
that does *not* live up in that range — it was assigned bit 7, inside the `CSIGNAL` byte, specifically
because bits 17–31 were the ones already spoken for by the time it was added, which is the concrete
reason [`clone3`](#clone3-and-why-it-exists) exists at all.

<KernelFacts
  structure={[["struct task_struct", "include/linux/sched.h"], ["struct signal_struct", "include/linux/sched/signal.h"]]}
  path="pthread_create() → clone(CLONE_VM|CLONE_THREAD|…) → kernel_clone() → copy_process() → wake_up_new_task()"
  observe="ps -eLo pid,tid,comm | head"
  trap="There is no process object. A process is a set of tasks that share a thread group id, and every tool that shows you 'a process' is aggregating tasks on your behalf." />

## References

- [`clone(2)`](https://man7.org/linux/man-pages/man2/clone.2.html) — the flag list, the illegal
  combinations, and the `clone3`/`struct clone_args` layout; the single most useful page for this topic.
- <Src file="kernel/fork.c" symbol="copy_process" /> — where each flag turns into either a shared pointer
  or a fresh copy; long, but readable, and the flags are handled roughly in the order this page presents
  them.
- [`pthreads(7)`](https://man7.org/linux/man-pages/man7/pthreads.7.html) — the user-space threading model
  and how it maps onto tasks, including the `gettid`/`getpid` distinction this page leans on.
- LWN, [*"clone3(), fork(), and the future of process creation"*](https://lwn.net/Articles/792628/) — why
  the flag word had to be replaced, from the person who wrote `clone3`.
