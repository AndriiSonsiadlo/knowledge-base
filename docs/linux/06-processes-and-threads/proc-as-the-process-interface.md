---
id: proc-as-the-process-interface
title: "`/proc` as the Process Interface"
sidebar_label: "/proc"
sidebar_position: 11
tags: [linux, kernel, processes]
prerequisites:
  - linux/processes-and-threads/task-struct-the-anatomy-of-a-task
draft: false
---

# `/proc` as the Process Interface

`/proc` is not a directory of files. Nothing under it is stored anywhere, and nothing you `cat` was
written to disk in advance — the "file" you read is generated, at the exact moment you read it, by kernel
code walking live, currently-mutating data structures and formatting the result as text. Once that lands,
most of what feels odd about `/proc` — a file reporting zero bytes and then handing back several
kilobytes, two reads of the same file disagreeing with each other, a `cat` that hangs — stops being odd
and starts being the direct, predictable consequence of one fact: there is no file, only a function that
pretends to be one.

## Generated on read

Every `/proc` entry that exposes more than a trivial fixed value is backed by the kernel's `seq_file`
interface (`include/linux/seq_file.h`). Rather than maintaining a buffer that a read call copies from,
`seq_file` gives each entry a small set of callbacks — chiefly a `show` function — that is invoked when a
read arrives, and which writes directly into a transient buffer for that read. `struct seq_operations`
holds exactly four function pointers: `start`, `next`, `stop`, and `show`; a single-value file like
`status` uses a trivial one-shot version of this, but the mechanism is the same one that lets a
line-per-item file like `/proc/PID/maps` iterate a live list without ever materializing the whole thing
as one static blob.

The consequence worth stating plainly, because it changes how you should reason about anything you read
from `/proc`: **a read is a snapshot of a moving target, and a multi-line read is not one snapshot.**
Reading `/proc/PID/status` does not pause the target process, take a consistent picture of its state, and
then hand you the text — each line, or in some cases each field, is computed against whatever the live
structures say at the instant that particular part of the buffer is formatted. If the target process
changes state between the first line of your read and the last, you can legitimately observe a
`status` file whose fields do not agree with each other, because they were never one atomic observation
to begin with.

## What actually happens

Take the simplest possible case: `cat /proc/self/status`. `self` is a magic symlink resolved per-caller
to the calling process's own PID, so this always means "my own status." Here is the actual path:

1. `open()` walks the path and finds a `struct proc_dir_entry` (`fs/proc/internal.h`) registered for this
   name under this PID's `/proc/PID/` directory — not a directory entry pointing at a file's data blocks,
   because there are no data blocks; it is a registration mapping a name to a set of callbacks.
2. `read()` (via `read_iter`, since procfs registers `.read_iter` rather than the older `.read` on this
   path) reaches `proc_reg_read_iter()` (`fs/proc/inode.c`), which dispatches through the
   `proc_dir_entry`'s registered operations into `seq_read_iter()` (`fs/seq_file.c`), the generic
   `seq_file` read machinery.
3. `seq_read_iter()` calls this entry's `show` function, `proc_pid_status()` (`fs/proc/array.c`), passing
   it the `seq_file` to write into and the target's `struct pid`.
4. `proc_pid_status()` walks `task_struct`, the `mm_struct` it points at, and the `cred` it points at,
   formatting each field into the `seq_file`'s buffer as it goes — this is the literal function that turns
   live kernel state into the text you see, and reading its source is the single clearest evidence for
   this page's whole thesis: there is a `seq_printf()` call for every line you have ever seen in
   `/proc/PID/status`, executing at read time, not a `memcpy()` out of anything pre-built.
5. The formatted text is copied back to user space, and the buffer is discarded. Nothing was stored.
   Nothing persists between reads.

The demonstration that makes this land harder than any explanation is one command pair, run for real in
this environment:

```text
$ ls -l /proc/self/status
-r--r--r-- 1 dev dev 0 Sep  8 02:03 /proc/self/status
$ wc -c /proc/self/status
1473 /proc/self/status
```

`ls -l` reports the file's size as `0` — and it is not lying, because at the moment `stat()` runs there is
no content yet to have a size; `proc_pid_status()` has not been called. `wc -c` then actually reads the
file, which triggers exactly the five-step path above, and reports the real byte count of whatever text
`proc_pid_status()` produced for *that* read — 1473 bytes in this capture, for `wc`'s own transient
process (each of `ls`, `wc`, and a plain `cat` in this environment is a different short-lived process, so
`self` resolves to a different PID each time and the exact byte count can shift run to run with the
process's own memory-map size, thread count, and so on). A file reporting zero bytes and then handing back
over a kilobyte on the next call is not a bug to work around; it is the direct, visible consequence of
"generated on read."

## The per-process entries worth knowing

| Entry | What it exposes | Backed by | Privilege |
|---|---|---|---|
| `status` | Human-readable key/value dump: state, PID/PPID, memory sizes, UID/GID sets, signal masks, capability sets | `task_struct`, `mm_struct`, `cred` | Same-user, or `CAP_SYS_PTRACE` for another user's process |
| `stat` | The same data as `status`, as ~50 whitespace-separated positional fields — the format `ps`/`top` actually parse | `task_struct` | Same as `status` |
| `cmdline` | The `argv[]` the process was `exec`'d with, NUL-separated | `mm_struct`'s saved arg/env region | Same as `status` |
| `environ` | The environment block at `exec()` time | `mm_struct`'s saved arg/env region | Same as `status`, and only readable by the owner or root even then on most configurations |
| `maps` | One line per VMA: address range, permissions, backing file | `mm_struct`'s VMA list | Same as `status` |
| `smaps` | Per-VMA memory accounting in detail — RSS, PSS, swap, per-VMA, not just per-mapping type | Walks every page table entry in every VMA | Same as `status`; genuinely expensive on a large process (see Misconceptions below) |
| `smaps_rollup` | The same accounting as `smaps`, pre-summed across all VMAs into one block | Same walk as `smaps`, one aggregate `show` | Same as `status` |
| `fd/` | One symlink per open file descriptor, resolving to the file, pipe, or socket it refers to | The process's `files_struct` descriptor table | Same as `status` |
| `fdinfo/` | Per-descriptor detail `fd/`'s symlink cannot carry: file offset, open flags, epoll registrations | Same descriptor table, plus the underlying file's private state | Same as `status` |
| `task/` | One subdirectory per thread in the process, each with its own `status`/`stat`/`stack`/etc. | The thread group's sibling `task_struct`s | Same as `status` |
| `wchan` | The name of the kernel function the task is blocked inside, if any | `task_struct`'s saved blocking-point info | Same as `status` |
| `stack` | The task's kernel-mode call stack at the moment of reading | Live stack unwind, requires `CONFIG_STACKTRACE` | Usually root-only |
| `limits` | The process's `RLIMIT_*` values, soft and hard | `task_struct`'s `signal_struct`/`rlimit` table | Same as `status` |
| `mountinfo` | The mount table as this process's mount namespace sees it | The namespace's mount tree | Same as `status` |
| `ns/` | One symlink per namespace type this process belongs to | The task's `nsproxy` | Same as `status` |
| `oom_score_adj` | The bias applied to this process's OOM-killer score | `task_struct`'s `signal_struct` | Writable by owner (limited range) or root |

## Why some reads block

Not every `/proc` read returns instantly, and the reason is never that the file is "slow" in the sense a
disk file can be slow — it is that the `show` callback has to acquire something, or wait on something,
before it can produce an answer. `/proc/PID/stack` needs a coherent, walkable kernel stack for the target,
which for a task actively running on another CPU right now may not be a safe thing to unwind; the read
can wait for the task to reach a quiescent point. `/proc/PID/mem` — a byte-addressable window onto the
target's address space, used by debuggers — requires ptrace-level access and additional checks per
access, not merely the open-time permission check. And more generally, a `show` callback that needs a lock
some other, busy subsystem is currently holding will simply wait for it, exactly like any other kernel
code that takes a lock — from the reader's side, this looks identical to "`cat` hung," because
mechanically, it did: it is inside a blocking wait, on the read-side call stack of a file that happens to
live under `/proc`.

## Stability

`/proc` is user-space ABI, in the same sense a syscall's argument order is ABI: once a field is published
in a given position, it cannot be removed or reordered without breaking every tool that parses it, so new
fields are appended at the end and old ones stay put forever, even ones that document deprecated or
now-meaningless information. This is precisely why `/proc/PID/stat` has grown to roughly fifty positional,
whitespace-separated fields and can never be tidied into something more readable — `ps`, `top`, and every
process-monitoring library on the planet index into it by position, and reordering even one field would
silently corrupt every one of them. `status`, by contrast, is `key:\tvalue` per line specifically so that
new keys can be added anywhere without disturbing anything that parses by name. The practical rule that
follows: **parse `/proc` by key, never by column index**, unless the specific file you are reading (like
`stat`) offers no other choice — and if you do have to parse `stat` positionally, treat the field count as
something that only grows, never shrinks or reorders.

## System-wide entries, briefly

Alongside the per-process tree, `/proc` carries system-wide entries that are not this page's subject but
worth naming so you know where each one belongs: `/proc/meminfo` (system memory accounting — see
[What `free` and RSS Really Tell
You](../08-memory-management/what-free-and-rss-really-say.md), which owns this file), `/proc/stat`
(aggregate CPU and scheduler counters since boot), `/proc/interrupts` (per-CPU, per-IRQ interrupt counts —
see [Interrupt Affinity](../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md),
which reads this file column by column), `/proc/cmdline` (the kernel's own boot command line, not a
process's), and `/proc/sys` (the sysctl tree, a different registration mechanism than the `seq_file` one
described above, but the same "generated on read, and often writable" character).

## `/proc` versus `/sys`

The two look similar — both are pseudo-filesystems, both hand back generated text — and exist for
different reasons. `/proc` is process state, plus decades of historical accumulation bolted onto the same
tree for lack of anywhere better to put it at the time (`/proc/sys`, `/proc/interrupts`, and
`/proc/meminfo` are not about any process at all). `/sys` is newer and disciplined: it is the kernel's
device and driver model, [kobjects, sysfs, and the object
model](../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md) rendered directly as a
tree, with the convention — mostly honored — of one value per file, so that a `read()` and a `write()` map
onto exactly one attribute rather than a whole formatted record. Where `/proc` grew organically and
carries a wide (and now-frozen) mix of formats, `/sys` was designed from the start around a single
consistent shape.

## Misconceptions

1. **"`/proc` files are zero bytes, so they must be empty."** The size a `stat()` reports is meaningless
   for a generated file, because the content does not exist until a `read()` triggers the `show` callback
   that produces it. `ls -l /proc/self/status` reporting `0` above is not withholding information — there
   is nothing yet to report a size for.
2. **"Reading `/proc` is free."** Some entries do real, non-trivial work per read: `smaps` walks every
   page table entry backing every VMA in the target process, and on a process with a large, heavily mapped
   address space (a big JVM heap, a database with hundreds of memory-mapped files) that walk is a genuine,
   measurable cost — running `smaps` in a tight loop across every process on a busy host is a real way to
   add CPU load, not a free observability query.
3. **"`/proc/PID/environ` shows the process's current environment."** It shows the environment block as it
   stood at `exec()` time, captured once into the saved arg/env region of `mm_struct`. A program that calls
   `setenv()`/`putenv()` after starting changes its own in-process view of the environment (and what a
   child it later `fork()`s and `exec()`s will inherit) without moving the region `/proc/PID/environ`
   reads from — the file can disagree with what the running program itself would report if asked.

```mermaid
sequenceDiagram
    participant cat as cat
    participant vfs as VFS
    participant procfs as procfs (proc_reg_read_iter)
    participant seqf as seq_file (proc_pid_status)
    participant task as task_struct / mm_struct / cred

    cat->>vfs: read(fd)
    vfs->>procfs: dispatch via proc_dir_entry
    procfs->>seqf: seq_read_iter()
    seqf->>task: walk live fields
    task-->>seqf: current values
    seqf-->>procfs: formatted text (this read only)
    procfs-->>vfs: bytes
    vfs-->>cat: bytes
    Note over seqf,task: Buffer is discarded after this read.<br/>Nothing was stored; nothing persists.
```

*`cat /proc/self/status`: the file's contents are computed during your `read()` and discarded afterwards.*

<KernelFacts
  structure={[["struct proc_dir_entry", "fs/proc/internal.h"], ["struct seq_file", "include/linux/seq_file.h"]]}
  path="read() → proc_reg_read_iter() → seq_read_iter() → proc_pid_status() → task_struct/mm_struct/cred fields → formatted text"
  observe="ls -l /proc/self/status && wc -c /proc/self/status"
  trap="Nothing in /proc exists until you read it. A file that reports zero bytes and returns over a kilobyte is not a bug, and a value you read twice may legitimately disagree with itself." />

## References

- [`man 5 proc`](https://man7.org/linux/man-pages/man5/proc.5.html) — the field-by-field reference for
  every entry named on this page; long, and the only complete one.
- [The `/proc` Filesystem](https://docs.kernel.org/filesystems/proc.html) — the kernel's own
  documentation, including the stability rules for adding fields this page's [Stability](#stability)
  section is drawn from.
- <Src file="fs/proc/array.c" symbol="proc_pid_status" /> — the function that generates `status`, and the
  clearest possible evidence for this page's central claim.
- [The seq_file Interface](https://docs.kernel.org/filesystems/seq_file.html) — the generic machinery
  every `/proc` file with more than a trivial fixed value is written against.
