---
id: the-life-of-a-write
title: "The Life of a `write()`"
sidebar_label: "Life of a write"
sidebar_position: 2
tags: [linux, kernel]
prerequisites: []
draft: false
---

# The Life of a `write()`

Where your data actually is at each moment between write() returning and the bytes reaching the device, and what fsync changes.

When `write()` returns successfully, where is your data? Almost everyone's first answer — "on disk"
— is wrong, and the correct answer is the reason Linux is fast for ordinary programs and the reason
power loss can still cost you data you thought was already saved.

## The call

`write(fd, buf, n)` is a syscall like any other: your process traps into the kernel, and the kernel
must not simply dereference the `buf` pointer you handed it — a bad pointer from user space has to
become an error, not a kernel crash. So the first real work is **copying data across the boundary**,
through a checked routine (`copy_from_user`), after the kernel has validated that `fd` is open for
writing and that the range is actually yours.

## VFS dispatch

Every open file is a `struct file`, and every `struct file` carries an `f_op` table of function
pointers supplied by whichever filesystem owns it. `write()` reaches the filesystem through exactly
one indirect call — <Src file="fs/read_write.c" symbol="vfs_write" /> resolves to
`file->f_op->write_iter` — and that single indirection is the entire reason a filesystem can be a
loadable module: ext4, xfs, and a FUSE filesystem all satisfy the same call differently, and `write()`
never needs to know which one it's talking to.

## Into the page cache

For an ordinary buffered write, `write_iter` copies your bytes into pages of the page cache and marks
those pages dirty. Then it returns. **This is where the page returns its answer:** at the instant
`write()` hands control back to your process, the data exists in RAM and nowhere else. Nothing has
been queued to a device yet.

## Writeback, later

Dirty pages don't sit forever — the kernel bounds how much dirty memory can accumulate and how old
it can get, and writeback kthreads flush pages back to their filesystem once either limit is crossed.
"Later" is typically on the order of tens of seconds, not milliseconds. The knobs and the guarantees
involved here — **writeback, dirty pages, and `fsync`** — are their own page.

## The block layer

When a dirty page is finally written back, the filesystem hands it to the block layer as a `bio`: a
description of which pages go where on which device. **The block layer** takes it from there — an
I/O scheduler orders and merges requests, and blk-mq fans them out across per-CPU submission queues so
that many CPUs can issue I/O without fighting over one lock.

## The device

The request lands in an NVMe submission queue. From there the device itself drives the transfer —
it DMAs the data directly out of your pages, without the CPU copying a single byte — and reports
completion with an interrupt (an MSI-X vector, on any machine built this decade). See
[The Hardware the Kernel Assumes](../00-overview/hardware-the-kernel-assumes.md) for why **DMA** is
one of the small set of capabilities Linux simply requires of the hardware underneath it.

## Completion

The interrupt handler that fires on completion does almost nothing itself — modern block drivers
push the real work onto a softirq or workqueue rather than run it at interrupt level — but eventually
the pages involved are marked clean again. From that moment on, dropping them costs nothing; they can
be reclaimed like any other clean page in the cache.

## What `fsync` changes

`fsync()` is the call that actually promises durability, and it promises more than "writeback ran":
it blocks until writeback for that file completes *and* the device confirms its own volatile write
cache has been flushed to stable storage. Without calling it, a successful `write()` guarantees
nothing whatsoever about durability — only that the kernel has accepted responsibility for the data
and will get it there eventually, on its own schedule.

## What actually happens

Take "the file is saved" seriously as a claim and it falls apart immediately. Baseline, on a real
machine, before touching anything:

```text
$ grep -e Dirty -e Writeback /proc/meminfo
Dirty:                96 kB
Writeback:             0 kB
WritebackTmp:          0 kB
```

Write 800 MiB and check *immediately*, before calling `sync`:

```text
$ dd if=/dev/zero of=./bigfile bs=1M count=800
800+0 records in
800+0 records out
838860800 bytes (839 MB, 800 MiB) copied, 0.389397 s, 2.2 GB/s
$ grep -e Dirty -e Writeback /proc/meminfo
Dirty:               124 kB
Writeback:        508928 kB
WritebackTmp:          0 kB
```

`dd` returned in under half a second — nowhere near enough time to write 800 MiB to a real device at
its actual speed. `Writeback` jumping to roughly 500 MB is the kernel telling you exactly where that
data is: queued for writeback, in flight, not yet confirmed anywhere durable. Now force it:

```text
$ sync
$ grep -e Dirty -e Writeback /proc/meminfo
Dirty:                56 kB
Writeback:            76 kB
WritebackTmp:          0 kB
```

`sync` blocks until writeback drains, and the numbers drop back toward baseline. `sync`, not the
original `write()` call, is what made the data leave RAM.

A related command worth knowing, and worth respecting: `sync; echo 3 > /proc/sys/vm/drop_caches`
forces writeback and then discards clean cache pages (page cache, dentries, inodes) system-wide.

:::warning
`drop_caches` is not destructive — dirty pages are never dropped, only clean ones — but it is also
not a tuning technique. Every file your system reads afterward has to come back from the device
again, so the machine gets noticeably slower for a while. Its only legitimate use is making a cold
cache reproducible for a benchmark.
:::

## Misconceptions

1. **"`write()` returning means the data is on disk."** No — it means the data is in the page cache
   and the kernel has accepted responsibility for it. Nothing about a successful `write()` says the
   bytes have left RAM.
2. **"`O_DIRECT` means synchronous."** No — `O_DIRECT` bypasses the page cache and writes (or DMAs)
   straight from your buffer, but it still needs a flush to guarantee the device's own cache has
   committed the data; skipping the page cache is not the same promise as durability.
3. **"`fsync` on the file is enough."** Usually, but not always: if the write created a new file, the
   *directory entry* that names it may need its own `fsync` (on the directory fd) before a crash can't
   make the file disappear even though its contents are safely on disk.

```mermaid
flowchart TB
    A["write(fd, buf, n) — user space"] --> B["copy_from_user(): bytes cross the boundary"]
    B --> C["vfs_write() → file->f_op->write_iter"]
    C --> D["Page cache: pages copied, marked dirty"]
    D -.->|"`write()` returns here"| E["Writeback (later): dirty-ratio threshold or timer"]
    E --> F["bio built: pages + target device"]
    F --> G["I/O scheduler, blk-mq per-CPU queues"]
    G --> H["NVMe submission queue"]
    H --> I["Device DMAs the data, signals completion (MSI-X)"]
    I --> J["Interrupt handler defers work; pages marked clean"]
```

*Where `write()` returns, and how much of the journey is still ahead of the data at that moment.*

<KernelFacts
  structure={[["struct file", "include/linux/fs.h"], ["struct bio", "include/linux/blk_types.h"]]}
  path="write() → vfs_write() → f_op->write_iter → page cache (dirty) → writeback → bio → blk-mq → device"
  observe="grep -e Dirty -e Writeback /proc/meminfo"
  trap="A successful `write()` is a promise about your process's memory, not about your disk. The only call that makes a durability promise is `fsync()`, and it must also reach the device's own cache." />

## References

- [`man 2 fsync`](https://man7.org/linux/man-pages/man2/fsync.2.html) — the exact scope of the
  durability guarantee, including the directory-entry caveat above.
- [The kernel's `vm` sysctl documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html) —
  `dirty_ratio` and friends, the knobs that decide how long "later" actually is.
- [The PostgreSQL `fsync()` incident](https://lwn.net/Articles/752063/) — the clearest published
  account of what happens when an application misunderstands exactly this pipeline's error path.
