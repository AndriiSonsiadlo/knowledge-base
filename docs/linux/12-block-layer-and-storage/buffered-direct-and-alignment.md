---
id: buffered-direct-and-alignment
title: "Buffered I/O, `O_DIRECT`, and Alignment"
sidebar_label: "Buffered and direct I/O"
sidebar_position: 6
tags: [linux, kernel, block-io]
prerequisites:
  - linux/block-layer-and-storage/the-bio
  - linux/memory-management/the-page-cache
draft: false
---

# Buffered I/O, `O_DIRECT`, and Alignment

There are three ways for a program's bytes to reach a device, and each makes a different trade.
**Buffered I/O** goes through the [page cache](../08-memory-management/the-page-cache.md): fast, forgiving,
and decoupled from the device's own timing. **Direct I/O** (`O_DIRECT`) goes around the cache entirely: the
application owns caching and timing itself, and in exchange must obey the device's alignment rules exactly.
**Memory mapping** turns reads and writes into page faults and writeback, so the cache and the application's
address space become the same memory. Databases pick deliberately among these three, trading predictability
for throughput or the reverse, and this page is about why.

```mermaid
flowchart TB
    subgraph Buffered["Buffered I/O"]
        B1["write() / read()"] --> B2["copy to/from a page-cache folio"]
        B2 --> B3["dirty folio queued for writeback"]
        B3 --> B4["submit_bio() — later, by a flusher thread"]
    end
    subgraph Direct["Direct I/O (O_DIRECT)"]
        D1["write() / read()"] --> D2["check alignment — EINVAL if it fails"]
        D2 --> D3["pin user pages, flush + invalidate the cached range"]
        D3 --> D4["submit_bio() — now, from the caller's own context"]
        D4 --> D5["caller blocks until the bio completes"]
    end
    subgraph Mapped["Memory-mapped I/O"]
        M1["load/store on a mapped address"] --> M2["page fault"]
        M2 --> M3["fault handler finds/fills the page-cache folio"]
        M3 --> M4["page table entry installed — no further copy"]
        M4 --> M5["submit_bio() — later, on writeback or msync()"]
    end
```

*Three paths to the same device: where each one copies, where each one waits, and where the page cache sits
or does not.*

## Buffered: the default

A buffered read looks up the requested offset in the file's page cache; on a hit, the kernel copies bytes
straight out of an already-warm folio, and on a miss it allocates one, fills it via the filesystem, and
serves the copy from there — with readahead trying to make misses rare for sequential access. A buffered
write copies the caller's bytes into a cache folio, marks it dirty, and returns immediately: the data is
safely in RAM, but nothing has necessarily left the machine yet. Both paths are described in full in
[The Page Cache](../08-memory-management/the-page-cache.md) and
[Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md) — this page does not
re-teach either, only what they mean for the choice against `O_DIRECT`.

What buffered I/O buys: no alignment rules at all, cache hits for anything re-read soon after, and
write-behind that lets a burst of small writes coalesce into fewer, larger device operations. What it costs:
**double caching** when the application already keeps its own buffer pool (a database's shared buffers, an
in-process cache) — the same bytes held twice, once by the kernel and once by the application, each unaware
of the other's eviction policy — and **unpredictable writeback latency**, since a `write()` that returns
"successfully" has only promised RAM, not the device, as
[Writeback, Dirty Pages, and `fsync`](../08-memory-management/writeback-and-fsync.md) covers in full.

## Direct: `O_DIRECT`

`O_DIRECT` asks the kernel to skip the cache on both ends. For a regular file, the filesystem's own
direct-I/O path — commonly `<Src file="fs/iomap/direct-io.c" symbol="iomap_dio_rw" />`, the shared `iomap`
implementation most modern filesystems (ext4, XFS, btrfs, and others) route through — pins the calling
process's user pages directly and builds `bio`s from them, with no folio and no copy in between; for a raw
block device the equivalent path is `<Src file="block/fops.c" symbol="__blkdev_direct_IO" />`. Before either
path submits anything, the kernel flushes and invalidates the page cache for the affected range first —
otherwise a buffered reader could see stale data, or a direct writer could race a dirty cached copy of the
same bytes, and the two views of the file would disagree.

That "pin the user pages and DMA straight to them" design is exactly why `O_DIRECT` cares about alignment in
a way buffered I/O never has to: buffered I/O is free to copy into and out of cache folios at any byte
offset, but direct I/O leaves no copy step to absorb a misaligned request.

## Alignment requirements

`O_DIRECT`'s buffer address, file offset, and transfer length must each be a multiple of the device's
**logical block size** (memory alignment can be stricter still, depending on filesystem and architecture).
There is no portable way to *guess* this correctly — it varies by filesystem, by mount options, and even by
individual file, so the kernel has to be asked.

- **`statx(2)` with `STATX_DIOALIGN`** (since Linux 6.1) is the modern, filesystem-agnostic way to ask: it
  reports `stx_dio_mem_align` (the required alignment for the user-space buffer address) and
  `stx_dio_offset_align` (the required alignment for the file offset and length) directly in the returned
  `struct statx`. Support varies by filesystem — a filesystem that does not implement it, or a file that
  does not support direct I/O at all, reports zero for both fields.
- **`posix_memalign()`** is the portable way to get a correctly aligned buffer once the required alignment
  is known, rather than hoping `malloc()` happened to return one.
- **`EINVAL`** is the failure mode for a misaligned request — offset, length, or buffer address — though
  some filesystems fall back to buffered I/O silently for a misaligned request instead of failing outright,
  which is its own trap: code that assumes "no error means direct I/O happened" can be wrong.

```wavedrom title="A 4096-byte logical block: an aligned O_DIRECT buffer versus a misaligned one" alt="Bit-field strip of a 4096-byte logical block showing a 4096-byte buffer starting at offset 0, accepted, against a 1000-byte write starting at offset 3600 that straddles the block boundary and is rejected with EINVAL"
{ reg: [
    { bits: 32, name: "4096-byte logical block (offset 0..4095)", type: 2 },
    { bits: 32, name: "aligned 4096-byte O_DIRECT buffer — accepted", type: 2 },
    { bits: 24, name: "misaligned 1000-byte write, offset 3600 — straddles the boundary", type: 4 },
    { bits: 8, name: "EINVAL", type: 6 }
  ],
  config: { hspace: 900, bits: 32, lanes: 4 }
}
```

*The alignment rule `O_DIRECT` enforces, drawn on a 4 KiB logical block: a request must start and end on a
block boundary, or the kernel rejects it.*

## What `O_DIRECT` does not give you

`O_DIRECT` is a cache-bypass flag, not a durability flag, and confusing the two is the single most common
mistake made with it. Skipping the page cache says nothing about whether the *device's own* volatile write
cache has been flushed, and it says nothing about file metadata — a write that extends a file's size, for
instance, can still leave that size change sitting unflushed even though the data bytes themselves went
straight to the device. A durable direct write still needs `O_DSYNC` (on `open()`) or an explicit
`fdatasync()` afterward, exactly as a buffered write does.

| Flag | Guarantees on `write()` return |
|---|---|
| `O_DSYNC` | The data, and only the metadata needed to *retrieve* that data (e.g. block mapping), has reached the device — as if followed by `fdatasync(2)`. |
| `O_SYNC` | The data *and all* associated file metadata (mtime, size, everything) has reached the device — as if followed by `fsync(2)`. |

## Memory-mapped I/O

`mmap()`ing a file turns the file into addressable memory: a read is a load that may fault, a fault finds or
fills the same page-cache folio the buffered path would have used (see
[The Page Cache](../08-memory-management/the-page-cache.md#read-and-mmap-reach-the-same-place)), and a
write to a shared mapping dirties that folio through the page tables rather than through a `write()` call —
the folio ends up on the same writeback path either way. The appeal is genuinely zero-copy: the application
reads and writes the cache directly, with no `read()`/`write()` copy step at all. The cost shows up
elsewhere: error handling is harder, because a write that hits a disk error after the `mmap()` call has
already returned has no return value left to report it through — it arrives as a `SIGBUS` delivered on the
next touch of the affected page, or is discovered later via a failing `msync()`. Durability works the same
way it does for any dirty page-cache data: nothing is guaranteed on-device until `msync()` (or the ordinary
writeback path) has run.

## What databases choose, and why

| Database | Default I/O path | Why |
|---|---|---|
| PostgreSQL | Buffered, with its own WAL and `fsync` | Relies on the OS page cache as its second-level cache above `shared_buffers`; `debug_io_direct` exists as a developer-facing setting to experiment with direct I/O on WAL and/or data files in recent releases, not (as of this writing) the default path. |
| MySQL / InnoDB | `O_DIRECT` for data files | InnoDB has its own buffer pool sized to be the real cache, so a second OS-level cache of the same pages is pure double-caching it would rather avoid. |
| RocksDB | Configurable | LSM workloads have sharply different access patterns for writes (sequential, large) versus point reads (random, small); RocksDB lets the operator pick per-workload rather than committing to one model. |
| SQLite | Buffered, with careful `fsync` placement | Runs embedded in the calling process with no server-side buffer pool of its own to protect from double-caching, so the OS cache is simply the cache. |
| LMDB | `mmap()` | Its entire storage engine is a memory-mapped B-tree; reads are page faults by design, and copy-on-write pages make `mmap()`'s dirty-page-through-page-tables model a direct fit rather than a workaround. |

The underlying data-structure and access-pattern reasoning behind these choices —B-trees, LSM-trees, write
amplification, and how each maps onto sequential versus random device access — belongs to
[Indexing & Storage Engines](../../computer-science/databases/indexing-and-storage-engines.md); this table
only covers the I/O-path half of the decision.

## What actually happens

Captured on this machine's real disk-backed filesystem (`/dev/sdd`, ext4, confirmed with `df -T .` — not
tmpfs), running `dd if=/dev/zero of=test bs=1M count=256` first buffered, then with `oflag=direct`, each
followed by `sync`:

```text
$ grep -E '^(Dirty|Writeback):' /proc/meminfo
Dirty:               120 kB
Writeback:             16 kB

$ dd if=/dev/zero of=test-buffered bs=1M count=256
256+0 records in
256+0 records out
268435456 bytes (268 MB, 256 MiB) copied, 0.160303 s, 1.7 GB/s

$ grep -E '^(Dirty|Writeback):' /proc/meminfo   # immediately after, BEFORE sync
Dirty:                20 kB
Writeback:         253920 kB

$ time sync
real    0m0.045s

$ grep -E '^(Dirty|Writeback):' /proc/meminfo   # after sync
Dirty:                20 kB
Writeback:              8 kB

$ dd if=/dev/zero of=test-direct bs=1M count=256 oflag=direct
256+0 records in
256+0 records out
268435456 bytes (268 MB, 256 MiB) copied, 0.057513 s, 4.7 GB/s

$ grep -E '^(Dirty|Writeback):' /proc/meminfo   # immediately after, BEFORE sync
Dirty:               112 kB
Writeback:             56 kB

$ time sync
real    0m0.005s
```

Two things to read out of these real numbers, not the classic textbook ones:

- **The `Writeback:` line is the tell, not the throughput.** The buffered `dd` "finished" in 0.16 s, but at
  that exact moment `/proc/meminfo` shows **253,920 kB still marked `Writeback`** — almost the entire 256 MiB
  was still in flight to the device when `dd` returned control. `dd`'s own reported throughput measured how
  fast it could copy into cache, not how fast the device absorbed the data; `sync` afterward still had real
  work queued; the direct run's `Dirty`/`Writeback` numbers barely move at any point, because `O_DIRECT`
  already waited for each write to reach the device before returning.
- **This sandbox's disk does not reproduce the classic "direct I/O reveals the *slow* real speed" gap.** The
  direct run here reports *higher* throughput than the buffered one (4.7 GB/s vs. 1.7 GB/s) — this is fast,
  likely virtualized block storage, not a spinning disk or a throughput-limited SSD, so `O_DIRECT` is not
  paying a large latency penalty per operation on this hardware. The qualitative point still holds exactly:
  `dd`'s reported number for the buffered run described memory-copy speed, not storage speed, and the
  `Writeback:` line proves it — a slower or more contended device would show the same gap as a large
  throughput difference instead of a `Writeback:` lag, but the underlying cause (buffered writes return
  before the device is involved at all) is identical either way.

## Misconceptions

1. **"`O_DIRECT` means synchronous and durable."** It only bypasses the page cache. Durability past the
   device's own volatile cache still needs `O_DSYNC` (at open) or an explicit `fdatasync()` — see
   [What `O_DIRECT` does not give you](#what-o_direct-does-not-give-you).
2. **"Direct I/O is always faster."** It removes cache hits and readahead along with the copy. An
   application without its own buffer pool doing small, repeated, or re-read-heavy I/O is usually *slower*
   under `O_DIRECT`, not faster — the speed only shows up for applications (databases, chiefly) that
   already manage their own cache and want to stop paying for a second one.
3. **"`mmap` is zero-copy, so it is always the fastest way to read a file."** Page faults and the TLB
   pressure of touching many mapped pages can exceed the cost of a `read()`'s single copy, especially for
   sequential, read-once access where there is no reuse to amortize the fault overhead against.

<KernelFacts
  structure={[["struct kiocb", "include/linux/fs.h"], ["struct iomap_dio", "fs/iomap/direct-io.c"]]}
  path="write(O_DIRECT) → f_op->write_iter() → iomap_dio_rw() → iomap_dio_bio_iter() → submit_bio() (per-filesystem paths differ; raw block devices go through __blkdev_direct_IO() instead)"
  observe="grep -E '^(Dirty|Writeback):' /proc/meminfo before and after a buffered dd, and a small statx(STATX_DIOALIGN) program (or xfs_io -c statx) for a file's stx_dio_mem_align/stx_dio_offset_align"
  trap="A buffered write that returns quickly has not been slowed down by the disk yet — it will be, later, when writeback runs or when balance_dirty_pages() throttles your next write. Benchmarks that stop the clock when write() returns are measuring memory, not storage." />

## References

- [`open(2)`](https://man7.org/linux/man-pages/man2/open.2.html), the `O_DIRECT` notes — alignment
  restrictions vary by filesystem and kernel version, and confirms `STATX_DIOALIGN` arrived in Linux 6.1
  (verified directly against the man page text).
- [`statx(2)`](https://man7.org/linux/man-pages/man2/statx.2.html) — `STATX_DIOALIGN`,
  `stx_dio_mem_align`, and `stx_dio_offset_align`, verified directly against the man page text.
- Phoronix, ["Linux 6.1 Adding Support To statx() For Reporting Direct I/O Alignment
  Details"](https://www.phoronix.com/news/Linux-6.1-statx-DIO-Alignment) and the LWN coverage of the
  same patchset, ["make statx() return DIO alignment information"](https://lwn.net/Articles/898176/) —
  cited here instead of the brief's guessed title, which does not match the actual LWN article; both agree
  on the Linux 6.1 landing version.
- [PostgreSQL documentation, Developer Options](https://www.postgresql.org/docs/current/runtime-config-developer.html)
  — `debug_io_direct`, verified as the real setting name directly against the current docs page, a
  buffered-I/O database's own developer-facing experiment with direct I/O.
