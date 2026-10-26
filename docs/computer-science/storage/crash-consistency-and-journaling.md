---
id: crash-consistency-and-journaling
title: "Crash Consistency and Journaling"
sidebar_label: "Crash consistency"
sidebar_position: 7
tags: [computer-science, storage, durability]
draft: false
---

# Crash Consistency and Journaling

A single logical update — appending one block to a file — is several physical writes: the data
block, the inode that now points at it, and the bitmap that marks it used. A crash can land between
any two of them, leaving the disk in a state no program ever wrote. Crash consistency is the
discipline of making every possible prefix of those writes recoverable. The four families of answer —
scan and repair, journal, copy-on-write, and log structure — are the design space every real
filesystem sits in.

## Core Concepts

| Term | Meaning |
|---|---|
| **Crash consistency** | The guarantee that after a crash at *any* point, the on-disk structures can be brought back to some valid state. |
| **Atomic update** | A set of writes that either all take effect or none do, as far as anything reading the disk afterward can tell. |
| **Write-ahead logging** | Recording the intended changes in a log before applying them to their real, "home" locations. |
| **Commit record** | The single write that marks a logged transaction as complete and safe to replay. |
| **Checkpoint** | Applying a committed transaction's logged changes to their home locations, after which the log entry can be freed. |
| **Copy-on-write** | Writing changed data to new locations and atomically swapping a root pointer, instead of modifying data in place. |
| **Log-structured** | A design where the log *is* the only on-disk layout, rather than a side channel that shadows a separate home layout. |
| **Flush / barrier** | A request that all writes issued before it are durable before any writes issued after it. |
| **FUA (forced unit access)** | A per-write flag that makes that single write durable immediately, without a separate flush. |
| **Volatile write cache** | A device-side buffer that can acknowledge a write before the data is actually durable, and can lose it on power loss. |

## Mechanism

```mermaid
sequenceDiagram
    participant App as Application
    participant FS as Filesystem
    participant Journal as Journal area
    participant Home as Home locations
    participant Cache as Device cache

    App->>FS: write(new block)
    FS->>Journal: write intended changes
    Journal->>Cache: flush
    Note over Cache: crash here → journal entry incomplete, discarded on recovery
    FS->>Journal: write commit record
    Journal->>Cache: flush
    Note over Cache: crash here → transaction committed, not yet checkpointed; recovery replays it
    FS->>Home: checkpoint (apply changes)
    Note over Home: crash here → some home writes applied; recovery re-applies the rest from the log
    FS->>Journal: free log space
    Note over Journal: crash here → transaction fully durable either way
```

*One journaled transaction, from intent to checkpoint, with the moments a crash can land and what
recovery does at each.*

### The problem, worked

Take the append example from the lead: appending one block to a file touches (at least) the **data**
block itself, the **inode** (which must now point at the new block and report the new size), and the
**bitmap** (which must mark the new block as used). A crash can land after any subset of these three
writes reached disk:

| Data written? | Inode updated? | Bitmap updated? | What the disk now claims | Result |
|---|---|---|---|---|
| No | No | No | Nothing happened | Harmless — as if the write never started |
| Yes | No | No | An unreferenced block, still marked free | Harmless — orphaned data, silently overwritten later |
| No | Yes | No | Inode points at a block that has old/garbage contents | **Corruption** — the file's data is wrong |
| No | No | Yes | A block marked used, not referenced by any file | **Leak** — space that can never be reclaimed |
| Yes | Yes | No | Inode correctly points at real new data, bitmap still says free | **Corruption risk** — a later allocation can hand that same block to something else |
| Yes | No | Yes | Correct data, marked used, but no file points at it | **Leak** — same as data-and-bitmap-only, harder to detect |
| No | Yes | Yes | Inode points at garbage, block correctly marked used | **Corruption** — worst case: wrong data *and* no free-space signal to fix it |
| Yes | Yes | Yes | Everything consistent | Success |

Only the all-or-nothing rows (all three, or none) are safe by construction. Every partial outcome is
either a leak or active corruption — and a crash can produce any one of them, since the three writes
are ordered by nothing but coincidence unless something enforces an order.

### fsck: scan and repair

The oldest answer: after an unclean shutdown, walk every on-disk structure and cross-check it against
every other one — does every allocated block have exactly one inode pointing at it, does the bitmap
agree, does every directory entry resolve. Inconsistencies get repaired according to a fixed set of
rules (orphaned blocks get freed, dangling references get dropped into a recovery directory). It
works, requires no dedicated on-disk log, and its cost is the fundamental drawback: a full scan and
repair is proportional to the *size of the disk*, not to the size of the update that was interrupted —
appending one block can trigger a scan that touches every inode on the volume.

### Journaling (write-ahead logging)

Write the intended changes to a **log** first, write a **commit record** marking the transaction
complete, then apply the changes to their real locations (**checkpoint**), then free the log space.
Recovery after a crash only has to look at the log: replay every transaction that has a commit record,
and discard every transaction that doesn't — never touch the rest of the disk at all. That makes
recovery cost proportional to the log's size, not the volume's.

What actually gets journaled comes in three tiers, trading safety for write cost:

- **Metadata-only journaling** logs just the inode, bitmap, and directory-entry changes, not the file
  data itself. Cheapest, and it protects filesystem structure — but a crash can still leave a file's
  data blocks containing garbage (old contents, or nothing at all) even though the metadata pointing
  at them is perfectly consistent.
- **Ordered mode** journals only metadata too, but adds one ordering rule: the data blocks must reach
  their home location *before* the metadata transaction that references them commits. This closes the
  metadata-only gap — metadata can never end up committed while pointing at garbage — without paying
  to write data twice.
- **Full data journaling** puts the data blocks through the journal as well as the metadata. Strongest
  guarantee, and the most expensive: every byte written to the file is written to disk twice, once to
  the log and once at checkpoint.

### Copy-on-write

Never overwrite live data. A changed block is written to a *new*, unused location; the metadata
structures that point at it (up through a tree of pointers) are rewritten at new locations too, all
the way up to a single **root pointer**; and only that root pointer is updated in place, atomically —
one write, either the old value or the new one, never a mixture. A crash mid-update simply leaves the
root pointer at its old value: the new blocks are unreferenced garbage, the old tree is still
completely intact, and no repair step is needed at all. The cost shows up elsewhere: data that would
have been one in-place write becomes new blocks scattered wherever free space happens to be
(fragmentation), and updating one leaf can cascade into rewriting every pointer block above it up to
the root (write amplification).

### Log-structured

Take copy-on-write's "never overwrite" idea to its limit: don't keep a separate home layout at all —
the entire disk *is* the log. Every write, data and metadata alike, is appended to the end of the log
sequentially; an index (itself part of the log) tracks where the current version of each piece of data
actually lives, since old versions are never overwritten in place. Reads go through that index rather
than a fixed location. Because the disk is finite and old versions of overwritten data become dead
space, a background **cleaner** has to walk the log, identify blocks that are no longer the current
version of anything, and reclaim that space for new writes. A flash translation layer, underneath a
solid-state drive, is itself a log-structured system built for exactly this reason — see
[SSDs & NAND Flash](./ssd-and-nand-flash.md).

### Barriers, flush, and the lie a disk can tell

Every scheme above assumes that once a write is acknowledged, it is durable — but storage devices
commonly have their own **volatile write cache**, and an acknowledged write can still be sitting only
in that cache when the power cuts. Ordering between writes (commit record after the log entries it
covers, checkpoint after the commit record) only holds across a crash if the host actually forces the
device to make earlier writes durable before later ones proceed. That's what a **flush** does — and a
**FUA** write asks for the same durability guarantee on a single write, without a separate flush call.
Enterprise SSDs commonly carry power-loss-protection capacitors specifically so a flush is cheap and
genuinely durable; many consumer drives do not, and some devices have been known to acknowledge a
flush faster than the data could possibly have reached stable media. A device that lies about a flush
defeats every crash-consistency scheme on this page — they are all built on the assumption that a
flush means what it says.

## Practical Usage

An application that wants a durable, atomic replacement of a file's contents — a config file, a
database's own metadata — needs more than a single `write()`. The recipe, as a sequence, and each step
exists for a specific reason:

1. Write the new contents to a **temporary file** in the same directory (same filesystem — see the
   rename caveat below).
2. **Flush** that temporary file, so its contents are durable before anything references it.
3. **Rename** the temporary file over the target. A rename that replaces an existing file is the one
   operation most filesystems make atomic — readers see either the old file or the new one, never a
   partial write.
4. **Flush the directory** itself. The rename changed a directory entry, which is its own piece of
   metadata; without flushing the directory, a crash can leave the rename applied to the file's data
   but not yet durable in the directory that records it.

Each step is required because a filesystem's crash-consistency guarantee covers only *its own*
metadata and the ordering it chooses to enforce — it says nothing about an application's intent unless
the application makes that intent durable itself, in this exact order. Databases take this further
still, layering their own write-ahead log on top of (or instead of) relying on filesystem journaling —
see [Transactions & ACID](../databases/transactions-and-acid.md) for the durability letter of ACID,
rather than re-deriving it here.

## Edge Cases & Pitfalls

- **Consistency is not durability.** A filesystem that recovers to a fully consistent state after a
  crash can still have lost the last several seconds of writes that were never flushed — consistency
  promises the structures make sense, not that nothing was lost.
- A flush that **fails** is not guaranteed to be reported again on a retry — an application that
  checks the return value of one flush call and assumes a later, successful-looking flush means the
  earlier failed data is now safe can be wrong. This is stated generally here; the specific,
  Linux-level story of how that failure gets reported belongs on the Linux page.
- **Rename is atomic only within one filesystem.** A rename across a filesystem boundary (a different
  mount) is not a single metadata operation at all — it becomes a copy and a delete, with all the
  partial-completion problems that copying data implies.
- Crash-consistency bugs are, empirically, far more common in **applications** than in filesystems —
  filesystems are heavily tested against exactly this failure mode, while the four-step recipe above
  is easy to get subtly wrong in ordinary application code.

## Comparisons

| Approach | Recovery time | Write overhead | What's protected | Example filesystem |
|---|---|---|---|---|
| fsck (scan and repair) | Proportional to disk size | None in normal operation | Metadata only, after a slow repair pass | ext2 |
| Journaling (ordered) | Proportional to log size | One extra write for metadata | Metadata always consistent; data protected by ordering, not journaled | ext4 |
| Full data journaling | Proportional to log size | Every data byte written twice | Metadata and data both | ext4 (`data=journal` mode) |
| Copy-on-write | None — old tree is always valid | Fragmentation, write amplification | Metadata and data both | ZFS, Btrfs |
| Log-structured | Index rebuild / scan of log tail | Cleaner overhead (rewrites live data) | Metadata and data both | F2FS, NILFS |

## References

- Arpaci-Dusseau & Arpaci-Dusseau, [*Operating Systems: Three Easy Pieces*](https://pages.cs.wisc.edu/~remzi/OSTEP/), ch. 42 ["Crash Consistency: FSCK and Journaling"](https://pages.cs.wisc.edu/~remzi/OSTEP/file-journaling.pdf) and ch. 43 ["Log-structured File Systems"](https://pages.cs.wisc.edu/~remzi/OSTEP/file-lfs.pdf) — free online; the best structured treatment, and the source of the append example.
- Pillai et al., ["All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications"](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/pillai), *OSDI* 2014 — the evidence that applications, not filesystems, are where crash consistency usually breaks.
- Rosenblum & Ousterhout, ["The Design and Implementation of a Log-Structured File System"](https://dl.acm.org/doi/10.1145/146941.146943), *ACM TOCS* 10(1), 1992 — the original log-structured design.
- Rebello et al., ["Can Applications Recover from fsync Failures?"](https://www.usenix.org/conference/atc20/presentation/rebello), *USENIX ATC* 2020 — what happens when the flush itself fails, across filesystems and applications.

### Books & Videos

- Martin Kleppmann, *Designing Data-Intensive Applications*, ch. 7 "Transactions" — a purchase; the database-side view of the same write-ordering problem.

## Related Pages

- [Filesystems Basics](./filesystems-basics.md)
- [RAID and Redundancy](./raid-and-redundancy.md)
- [Transactions & ACID](../databases/transactions-and-acid.md)
- [Journaling and Crash Consistency](../../linux/11-vfs-and-filesystems/journaling-and-crash-consistency.md) — what Linux filesystems actually guarantee.
- [Writeback and fsync](../../linux/08-memory-management/writeback-and-fsync.md)
