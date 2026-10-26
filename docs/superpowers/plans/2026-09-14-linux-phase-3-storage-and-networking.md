# Linux & Kernel Section — Phase 3 (Storage and Networking) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and then write folders `11`–`13` of `docs/linux/` — the VFS and filesystems, the block layer and I/O, and the networking stack — 36 pages, plus the five `computer-science/` backfill pages those folders declare as prerequisites (RAID, crash consistency, the sockets API, ARP/ICMP, NAT theory) and the backlinks into them. Along the way, turn every prose-only forward mention in folders 00–10 into a real link now that its target exists. Finish at a green `npm run build` with `npm run check:linux -- --written` passing for folders 00–13.

**Architecture:** No new site machinery. Everything this phase uses was built and proven in Phases 1a, 1b and 2: the manifest-driven scaffolder, the knowledge-graph build gate, `<PrereqBlock>` injection, and the registered MDX components. Phase 3 has four kinds of work:
- one mechanical task that extends `tools/linux-docs-manifest.json` and regenerates the tree;
- two CS backfill tasks;
- seventeen writing tasks against fixed per-page briefs;
- a closing set of aggregation tasks: forward-link resolution, figures, glossary, misconceptions index and roadmap, and the review.

The phase adds two canonical third-party figures — the Thomas-Krenn storage-stack diagram and the netfilter packet-flow diagram — plus one licensed CS figure.

**Tech Stack:** Docusaurus 3.10.2, React 19, Mermaid (via `@docusaurus/theme-mermaid`), WaveDrom (`src/plugins/remark-wavedrom.js`), Biome 2.5.7, Node 22 (`node --test`), `docusaurus-plugin-image-zoom`, context7 MCP for currency checks.

**Spec:** `docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md`. This plan implements its "Phase 3 ordering" section, the folder 11/12/13 outlines, and backfill rows 12–16.
**Predecessor plans:** `2026-08-28-linux-phase-1a-infrastructure.md`, `2026-08-29-linux-phase-1b-foundations.md`, and `2026-09-04-linux-phase-2-core-kernel.md` (all executed).

**Base branch:** Phase 2's work lives on `worktree-linux-phase-2-core-kernel` and **is not yet merged to `master`**. Phase 3 must start from a tree that contains folders 05–10: branch from that branch, or merge it to `master` first. Check before Task 1: `ls docs/linux` must list `10-interrupts-time-and-deferred-work`. If it does not, stop — every prerequisite in this plan that points into folders 05–10 will fail the build.

---

## Global Constraints

- **Pinned kernel is `v6.18`** (`customFields.linuxKernelVersion` in `docusaurus.config.js`). Every source citation goes through `<Src file="..." symbol="..." />`. Never hand-write an `elixir.bootlin.com` URL, and never cite a line number — file plus symbol only.
- **Never invent a symbol, struct field, path, sysctl, or config option.** Before a page is committed, check every symbol named on it against `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>`, and every path against `/source/<path>`. Every symbol in this plan is an informed starting point, **not** a verified fact. The block layer, VFS and networking code all moved recently:
  - `blk_mq_alloc_disk` gained a `queue_limits` argument;
  - `bdev_file_open_by_path` replaced `blkdev_get_by_path`;
  - `unlazy_walk` became `try_to_unlazy`;
  - the skb drop-reason machinery arrived;
  - FUSE gained passthrough and io_uring transport;
  - the new mount API added `fsopen`/`fsmount`.

  Where a symbol has moved, cite what v6.18 actually has. Mention the old name only if the page's subject is the change itself.
- **Every doc under `docs/linux/` must carry a `prerequisites` front-matter key.** An empty array is valid; a missing key fails the build. The scaffolder writes it — do not remove it when turning a stub into a page.
- **`onBrokenLinks: "throw"`.** Folders **14–19 are not scaffolded**, so no page may link into them. Where a page wants to point forward (drivers, containers, security, observability, eBPF), it names the topic in prose with no link. Links *backwards* into folders 00–10 and *sideways* within 11–13 are free, because Task 1 scaffolds all three folders before any of them is written.
- **Relative doc links only**, in the `../12-block-layer-and-storage/the-bio.md` style — never `/docs/linux/...`. `baseUrl` is `/knowledge-base/`.
- **`## What actually happens` is conditional.** Only on pages marked **[WAH]** in this plan. Adding it elsewhere is a review finding.
- **Every finished topic page ends with `<KernelFacts />` and carries a `## References` section** with 2–6 annotated entries. `tools/check-linux-docs.mjs` enforces both. No page in this phase is navigational, so none is exempt.
- **Every page carries at least one visual anchor**: a Mermaid diagram, a WaveDrom `reg`/`signal` fence, a `<Figure>`, or a substantive comparison table. Its caption says *what it shows*, never "Diagram 3".
- **Visual vocabulary is fixed** (spec):
  - Mermaid `flowchart` for code paths and layering;
  - `stateDiagram-v2` for state machines (TCP states, neighbour states, conntrack states);
  - `sequenceDiagram` for cross-component interaction over time;
  - WaveDrom `reg` for every bit-field or byte layout (`sk_buff` buffer layout, `open()` flags, the ext4 extent header, the NVMe command);
  - `<Tabs>` for genuine side-by-side alternatives;
  - tables for comparison and enumeration.

  Do not draw a state machine as a flowchart.
- **Struct-heavy pages get a struct-*shape* diagram, not a struct dump.** `struct sk_buff`, `struct inode`, `struct sock` and `struct request` each have dozens of fields. Show the dozen that matter, grouped by concern, and `<Src>` the real definition.
- **Fence languages:**
  - kernel C → ` ```c `
  - Intel-syntax disassembly → ` ```nasm `
  - AT&T asm, `Kconfig`, `gdb`/`perf`/`bpftrace` transcripts, `dmesg`, `/proc` and `/sys` dumps, `iostat`/`ss`/`tcpdump`/`nft list` output → ` ```text `
  - a `.config` fragment → ` ```ini `
  - shell → ` ```bash `
  - nftables *rule source* (what you would put in a file) → ` ```text `, because Prism has no nftables grammar

  All of the named languages are already in `prism.additionalLanguages`.
- **Five admonitions only**: `:::info`, `:::note`, `:::tip`, `:::warning`, `:::danger`. `:::danger` is reserved for irreversible damage and states what is lost. A `<Lab>` carrying a `:::danger` may not have `host="any-linux"` — `pvcreate`/`mkfs`/`mdadm --create` on the wrong device is this phase's canonical case.
- **Name the architecture on every arch-specific claim.** Folders 11–13 own none of the spec's structural arm64 contrast `:::note`s (those land in 05, 08, 09, 10 and 14). Do not invent one to fill a quota. Where a claim *is* arch-specific (checksum-offload instruction use, `copy_to_user` cost), say "x86-64" explicitly.
- **No new asciinema casts in this phase.** The spec's outline marks `<Cast>` on `12/diagnosing-io-problems` and `13/diagnosing-network-problems`. Those pages ship their sessions as annotated ` ```text ` blocks — which the spec requires alongside every cast anyway — and the cast library is recorded in one session in Phase 5.
- **Figures in `docs/linux/` are not licence-gated** (a spec departure from `CLAUDE.md`), but every image file needs a row in `static/img/linux/SOURCES.md` and an on-page credit via `<Figure source= href= />`. **Figures in `docs/computer-science/` keep the repository's normal licence discipline:** `static/img/cs/SOURCES.md` carries `file | source | author | licence`, and every CS `<Figure>` passes `license=`. Do not carry the Linux exemption into a CS page.
- **context7 verification is mandatory where the spec's table says so**, and the check date goes into the page's `## References` annotation:
  - the `io_uring` API surface (folder 12, via liburing);
  - nftables syntax, the `iproute2` command surface, and BBR status (folder 13).

  Where context7 has no entry, cite `docs.kernel.org` or the man page at the pinned version and say so.
- **No-duplication contract (spec, normative).** Folders 11 and 12 link to `computer-science/storage/*` for device physics, the NVMe protocol, RAID theory and journaling theory; they never re-teach them. Folder 13 links to `computer-science/computer-networks/*` and `protocols/*` for protocol semantics and owns only the kernel's datapath. Durability *from the database side* is owned by `computer-science/databases/*`.
- **`## Misconceptions` entries must be mirrored** into `00-overview/misconceptions-index.md` (Task 24). Write the page first; the index follows the page.
- **Biome** covers `**/*.{js,jsx,ts,tsx,json,md}` at 2-space indent. Run the lint gate raw — `rtk run 'npm run lint'` — because the Claude Code hook rewrites `npm run lint` to a different linter and reports a false pass.
- **Commit messages:** `<type>: <what>` on one line. **Never** a `Co-Authored-By` trailer, never a "Generated with Claude Code" line (`CLAUDE.md`, which overrides any tool default).

---

## File Structure

**Modified (machinery)**

| File | Change |
|---|---|
| `tools/linux-docs-manifest.json` | Three new folder objects (`11`–`13`, 36 pages) and five new `external` entries (the CS backfill pages). Nothing existing is edited. |

**Created by the scaffolder in Task 1 — never by hand**

| Path | Count |
|---|---|
| `docs/linux/11-vfs-and-filesystems/` + `_category_.json` | 13 pages |
| `docs/linux/12-block-layer-and-storage/` + `_category_.json` | 11 pages |
| `docs/linux/13-networking-stack/` + `_category_.json` | 12 pages |
| `docs/computer-science/storage/raid-and-redundancy.md` | backfill 12 |
| `docs/computer-science/storage/crash-consistency-and-journaling.md` | backfill 13 |
| `docs/computer-science/computer-networks/sockets-and-the-application-boundary.md` | backfill 14 |
| `docs/computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md` | backfill 15 |
| `docs/computer-science/computer-networks/nat-and-connection-tracking.md` | backfill 16 |

**Modified (existing CS pages — small, additive backlinks only, no rewrites)**

| File | Edit |
|---|---|
| `docs/computer-science/storage/intro.md` | Two new bullets in its page list, for backfill 12 and 13. |
| `docs/computer-science/storage/filesystems-basics.md` | `## Related Pages`: backfill 13 and `linux/11-vfs-and-filesystems/why-vfs-exists`. Confirm it claims no Linux-VFS-specific behaviour (spec). |
| `docs/computer-science/storage/hard-disk-drives.md` | `## Related Pages`: backfill 12 (rebuild time is a disk-capacity story). |
| `docs/computer-science/storage/nvme-and-storage-interfaces.md` | `## Related Pages`: `linux/12-block-layer-and-storage/nvme-in-the-kernel`. |
| `docs/computer-science/databases/transactions-and-acid.md` | `## Related Pages`: backfill 13 (what durability needs underneath). |
| `docs/computer-science/databases/indexing-and-storage-engines.md` | `## Related Pages`: backfill 13 and `linux/12-block-layer-and-storage/buffered-direct-and-alignment`. |
| `docs/computer-science/computer-networks/intro.md` | Three new bullets in its page list, for backfill 14, 15 and 16. |
| `docs/computer-science/computer-networks/data-link-layer.md` | `## Related Pages`: backfill 15. |
| `docs/computer-science/computer-networks/network-layer-and-routing.md` | `## Related Pages`: backfill 15 and 16, and `linux/13-networking-stack/routing-and-neighbours`. |
| `docs/computer-science/computer-networks/transport-layer-tcp-udp.md` | `## Related Pages`: backfill 14 and `linux/13-networking-stack/tcp-in-the-kernel`. |
| `docs/computer-science/operating-systems/interprocess-communication.md` | `## Related Pages`: backfill 14 (sockets as the network-transparent IPC). |

**Modified (existing section pages — forward links now resolvable, Task 21)**

| File | Change |
|---|---|
| `docs/linux/02-guided-traces/what-happens-when-you-type-ls.md` | VFS, dentry-cache and `getdents64` mentions linked into folder 11; the "when folder 11 covers the VFS" reference annotation rewritten as a link. |
| `docs/linux/02-guided-traces/the-life-of-a-write.md` | VFS, block layer, `bio`, blk-mq and NVMe mentions linked into folders 11 and 12. |
| `docs/linux/02-guided-traces/the-life-of-a-packet.md` | NAPI, GRO, `sk_buff`, netfilter, routing, TCP and socket-queue mentions linked into folder 13. |
| `docs/linux/02-guided-traces/the-life-of-a-container.md` | overlayfs and copy-up, mount propagation, veth and NAT mentions linked into folders 11 and 13. **Namespaces, cgroups, capabilities and seccomp stay unlinked** — folders 15 and 16. |
| `docs/linux/05-syscalls-and-the-boundary/what-a-system-call-actually-is.md` | `io_uring` and `epoll` table rows linked; the "only the vDSO is linked" sentence corrected. |
| `docs/linux/08-memory-management/the-page-cache.md` | The "Folder 12 owns the mechanism" `O_DIRECT` sentence becomes a link. |
| `docs/linux/08-memory-management/writeback-and-fsync.md` | The "belongs to folder 12" flush sentence becomes links into 12 and 11. |
| `docs/linux/10-interrupts-time-and-deferred-work/threaded-irqs.md` | The NAPI prose mention becomes a link. |
| `docs/linux/10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md` | The RSS/RPS prose mention becomes a link. |
| `docs/linux/00-overview/hardware-the-kernel-assumes.md` | **Phase 2 leftover:** the monotonic-timer "later folder, not yet written" placeholder now links folder 10, which exists. |

**Modified (section overview pages)**

| File | Change |
|---|---|
| `docs/linux/00-overview/glossary.md` | Extended with the terms folders 11–13 introduce. |
| `docs/linux/00-overview/misconceptions-index.md` | Three new `##` folder groups. |
| `docs/linux/00-overview/roadmap.md` | Two paths extended, two new paths, "Where the rest is" updated. |
| `docs/linux/00-overview/what-this-section-covers.md` | Folder-ladder rows 11–13 marked written; the "11 through 19" sentence becomes "14 through 19". |
| `static/img/linux/SOURCES.md` | One row per Linux figure added in Task 22. |
| `static/img/cs/SOURCES.md` | One row per CS figure added in Task 22. |
| `CLAUDE.md` | Phase status line updated. |

**Untouched, deliberately:** every file under `src/`, `tools/scaffold-linux-docs.mjs`, `tools/check-linux-docs.mjs`, `scripts/*.test.mjs`, `docusaurus.config.js`, `sidebars.js`. If a task seems to need a change under `src/`, stop: Phase 3 is content, and a component change means a page is fighting the conventions rather than using them.

---

## Doc-id reference

Docusaurus's `numberPrefixParser` strips the `NN-` from folder segments, so a page's real doc id — the form `prerequisites:` and `related:` must use — has no numeric prefix. This plan writes prerequisites in the short form `12/the-bio`; expand them with this table when writing the manifest.

| Short form | Real doc id prefix |
|---|---|
| `00/…` | `linux/overview/…` |
| `02/…` | `linux/guided-traces/…` |
| `04/…` | `linux/kernel-architecture-and-idioms/…` |
| `05/…` | `linux/syscalls-and-the-boundary/…` |
| `06/…` | `linux/processes-and-threads/…` |
| `07/…` | `linux/scheduling/…` |
| `08/…` | `linux/memory-management/…` |
| `09/…` | `linux/concurrency-and-locking/…` |
| `10/…` | `linux/interrupts-time-and-deferred-work/…` |
| `11/…` | `linux/vfs-and-filesystems/…` |
| `12/…` | `linux/block-layer-and-storage/…` |
| `13/…` | `linux/networking-stack/…` |
| `cs:…` | `computer-science/…` (full path; those folders are unnumbered) |

**CS backfill pages go in `prerequisites`, not only `related`, where the Linux page genuinely depends on them.** This matches how Phase 2 wired `05/the-entry-path` and `08/numa-and-memory-policy`, and it makes `<PrereqBlock>` render the chip with its `CS` badge under "Before this".

**Relative links, by contrast, keep the numeric prefix** — they are file paths, not ids: `../11-vfs-and-filesystems/the-four-objects.md`.

---

## Page brief format

Every writing task below gives, per page:

- **Opens with** — the mental-model paragraph. No page opens with a struct, a command, or a code block.
- **Sections** — the `##` headings, in order, each with what it must establish.
- **Anchor** — the required visual, and what it must show.
- **KernelFacts** — starting values for the four fixed rows. **Verify every symbol against Elixir v6.18 before committing.**
- **References** — concrete sources; annotate each with why a reader would click it. **Open every URL before citing it.** A URL in this plan is a lead, not a verified citation; if it has moved, cite where it moved to, and if it is gone, pick another source of the same tier.

Markers:
- `[WAH]` — the page carries `## What actually happens`.
- `[Lab host=…]` — the page carries a `<Lab>` with that host badge, **measured** expected output, and a closing "if it fails" line.
- `[Misc]` — the page carries `## Misconceptions`, mirrored into the index in Task 24.

**Labs are run before their pages are written.** Every task that carries a `<Lab>` has an explicit step to run it in the named environment and record the real output. The QEMU invocations are the ones folder 01 defines — do not invent a new one:
- **Initramfs labs** use `01/booting-your-kernel-in-qemu`.
- **Labs needing a real block device, `systemd`, or package-installed tools** (`lvm2`, `mdadm`, `fio`, `nftables`, `iproute2`) use the Debian VM from `01/a-full-system-vm-and-wsl2`. Give that VM an extra scratch disk with `qemu-img create -f raw scratch.img 2G` and `-drive file=scratch.img,if=virtio,format=raw`.

---

## Task 1: Extend the manifest and scaffold folders 11–13

**Files:**
- Modify: `tools/linux-docs-manifest.json`
- Create (by running the scaffolder): 36 stub pages, 3 `_category_.json` files, 5 CS backfill stubs

**Interfaces:**
- Consumes: the manifest schema established for folders 00–10.
  - `folders[]` objects: `dir`, `label`, `position`, `description`, `roadmapLink`, `pages[]`.
  - Page objects: `file`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `prerequisites`, optional `related`, `summary`.
  - `external[]` objects: `path`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `summary`.
- Produces: every doc id every later task in this phase links to or declares as a prerequisite. **No later task may start until the build is green**, because a missing node fails the graph plugin loudly rather than degrading quietly.

- [ ] **Step 0: Confirm the base**

Run: `ls docs/linux && node -e "const m=require('./tools/linux-docs-manifest.json'); console.log(m.folders.length, m.folders.reduce((n,f)=>n+f.pages.length,0), m.external.length)"`
Expected: eleven folders `00`–`10` plus `readme.md`, and `11 122 9`. Anything else means Phase 2 is not in this tree — see **Base branch** above.

- [ ] **Step 1: Append the three folder objects to `manifest.folders`**

Append after the `10-interrupts-time-and-deferred-work` object, in numeric order. Each folder object takes `"roadmapLink": "../00-overview/roadmap.md"`.

| dir | label | position | description |
|---|---|---|---|
| `11-vfs-and-filesystems` | VFS and Filesystems | 12 | How one `read()` works across thirty different filesystems: the four VFS objects, path lookup and the dentry cache, mounts, ext4, XFS and Btrfs, journaling, the pseudo-filesystems, overlayfs, and FUSE. |
| `12-block-layer-and-storage` | The Block Layer and I/O | 13 | Everything between a filesystem asking for a block and a device completing it: `bio`s, blk-mq, I/O schedulers, `O_DIRECT`, `io_uring`, device mapper, software RAID, NVMe, and how to find out why a disk is slow. |
| `13-networking-stack` | The Networking Stack | 14 | The kernel's datapath and control plane: `sk_buff`, sockets, the receive and transmit paths, TCP as implemented, netfilter and connection tracking, routing, network namespaces, traffic control, and diagnosing network problems. |

Tags per folder, applied to every page in it (spec area tags):
- `11` → `["linux", "kernel", "vfs"]`
- `12` → `["linux", "kernel", "block-io"]`
- `13` → `["linux", "kernel", "networking"]`

- [ ] **Step 2: Add folder 11's thirteen pages**

`sidebar_position` is the row number. Prerequisites are in short form; expand them with the doc-id table above.

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `why-vfs-exists` | Why the VFS Exists | Why the VFS exists | `04/container-of-and-embedded-structs` | One `read()` over thirty filesystems, and the object-oriented C indirection layer that makes that possible. |
| 2 | `the-four-objects` | Superblock, Inode, Dentry, File | The four objects | `11/why-vfs-exists` | The four core VFS objects, what each caches and pins, and the operations tables that make them polymorphic. |
| 3 | `path-lookup-and-the-dcache` | Path Lookup and the Dentry Cache | Path lookup | `11/the-four-objects`, `09/rcu-in-practice` | Resolving a path component by component, RCU-walk versus ref-walk, and why negative dentries are a feature. |
| 4 | `open-read-write-in-the-kernel` | `open`, `read`, `write` in the Kernel | open, read, write | `11/the-four-objects`, `08/the-page-cache` | From a file descriptor to a filesystem and back: what an fd actually is, and where `O_DIRECT` leaves the path. |
| 5 | `mounts-and-mount-namespaces` | Mounts and Mount Namespaces | Mounts | `11/path-lookup-and-the-dcache` | The mount tree as distinct from the directory tree, bind mounts, and the propagation rules containers depend on. |
| 6 | `ext4` | ext4 | ext4 | `11/journaling-and-crash-consistency`, `11/the-four-objects` | The default filesystem read from the on-disk layout upward: block groups, extents, htree directories, delayed allocation, jbd2. |
| 7 | `xfs-and-btrfs` | XFS and Btrfs | XFS and Btrfs | `11/ext4` | Two different bets — parallel allocation groups versus copy-on-write with snapshots — and when each is right. |
| 8 | `journaling-and-crash-consistency` | Journaling and Crash Consistency | Journaling | `11/open-read-write-in-the-kernel`, `08/writeback-and-fsync`, `cs:storage/crash-consistency-and-journaling` | What survives a power cut on Linux, what does not, and the durability contract an application actually gets. |
| 9 | `tmpfs-and-memory-filesystems` | tmpfs and Memory-Backed Filesystems | tmpfs | `11/the-four-objects`, `08/the-page-cache` | A filesystem that is page cache with no backing store: swappable, size-limited, and behind `/tmp`, `/dev/shm`, and `/run`. |
| 10 | `procfs-sysfs-debugfs-configfs` | procfs, sysfs, debugfs, configfs | Pseudo-filesystems | `11/the-four-objects`, `04/kobjects-sysfs-and-the-object-model` | Four pseudo-filesystems with four different contracts, and the ABI rules for each. |
| 11 | `overlayfs` | overlayfs | overlayfs | `11/mounts-and-mount-namespaces`, `11/path-lookup-and-the-dcache` | Lower, upper, and work directories, copy-up on write, whiteouts, and why this is what a container image layer is. |
| 12 | `fuse-and-userspace-filesystems` | FUSE | FUSE | `11/open-read-write-in-the-kernel` | Moving a filesystem to user space, what the extra boundary crossings cost, and when that cost is worth paying. |
| 13 | `lab-a-minimal-filesystem` | Lab: A Filesystem in 200 Lines | Lab: a filesystem | `11/the-four-objects`, `11/open-read-write-in-the-kernel`, `04/modules-in-practice` | An in-memory filesystem module registered with the VFS and mounted in the QEMU lab. |

Extra `related` entries:
- Page 1: `["computer-science/storage/filesystems-basics", "linux/guided-traces/what-happens-when-you-type-ls"]`
- Page 3: `["linux/concurrency-and-locking/rcu-the-idea"]`
- Page 9: `["linux/memory-management/swap-and-zswap"]`
- Page 10: `["linux/processes-and-threads/proc-as-the-process-interface"]`

- [ ] **Step 3: Add folder 12's eleven pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `the-block-layer-map` | The Storage Stack, Mapped | The storage stack | `11/open-read-write-in-the-kernel` | The whole path from `write()` to a flash die as one reference diagram, and the map for the rest of the folder. |
| 2 | `block-devices-and-gendisk` | Block Devices and `gendisk` | Block devices | `12/the-block-layer-map` | What makes a device a block device, partitions and device numbers, and the `/sys/block` attributes worth knowing. |
| 3 | `the-bio` | The `bio` | The bio | `12/block-devices-and-gendisk`, `08/writeback-and-fsync` | The unit of block I/O: segments of pages, a direction, a sector, a completion callback — and how writeback produces one. |
| 4 | `blk-mq` | blk-mq: Multi-Queue Block I/O | blk-mq | `12/the-bio`, `10/how-an-interrupt-reaches-the-kernel` | Why one request queue collapsed on NVMe, per-CPU software queues, tags, and the completion path back to the waiting task. |
| 5 | `io-schedulers` | I/O Schedulers | I/O schedulers | `12/blk-mq` | `none`, `mq-deadline`, `bfq`, and `kyber` — what each optimises and why `none` is right for NVMe and wrong for a shared disk. |
| 6 | `buffered-direct-and-alignment` | Buffered I/O, `O_DIRECT`, and Alignment | Buffered and direct I/O | `12/the-bio`, `08/the-page-cache` | Three paths to a device — through the page cache, around it, and mapped — and why databases choose what they choose. |
| 7 | `io-uring` | `io_uring` | io_uring | `12/buffered-direct-and-alignment`, `05/what-a-system-call-actually-is` | Shared submission and completion rings that batch syscalls to nearly zero, and the security history that made them controversial. |
| 8 | `device-mapper-and-lvm` | Device Mapper and LVM | Device mapper | `12/the-bio` | Stacking virtual block devices — linear, snapshot, thin, crypt — with LVM as a user-space manager over them. |
| 9 | `software-raid` | Software RAID (md) | Software RAID | `12/the-bio`, `cs:storage/raid-and-redundancy` | md personalities, resync and rebuild, the write hole in practice, and monitoring a degraded array. |
| 10 | `nvme-in-the-kernel` | NVMe in the Kernel | NVMe | `12/blk-mq` | Submission and completion queues mapped onto blk-mq, doorbells, per-queue interrupts, and polled I/O. |
| 11 | `diagnosing-io-problems` | Diagnosing I/O Problems | Diagnosing I/O | `12/blk-mq`, `12/io-schedulers`, `12/buffered-direct-and-alignment` | A worked investigation from "the disk is slow" to a named cause, and why `iowait` and `%util` mislead. |

Extra `related` entries:
- Page 1: `["computer-science/storage/nvme-and-storage-interfaces", "linux/guided-traces/the-life-of-a-write"]`
- Page 10: `["computer-science/storage/nvme-and-storage-interfaces", "computer-science/buses-and-io/interrupt-controllers"]`
- Page 11: `["linux/scheduling/diagnosing-scheduling-latency", "computer-science/databases/transactions-and-acid"]`

- [ ] **Step 4: Add folder 13's twelve pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `the-network-stack-map` | The Network Stack, Mapped | The network stack | `10/how-an-interrupt-reaches-the-kernel` | Socket to protocol to IP to netfilter to routing to device to NIC, in both directions — the reference map for the folder. |
| 2 | `sk-buff` | `sk_buff`: The Packet Container | sk_buff | `13/the-network-stack-map`, `08/slab-slub-and-kmalloc` | The structure every packet lives in, the headroom that makes header pushing cheap, and cloning versus copying. |
| 3 | `sockets-in-the-kernel` | Sockets in the Kernel | Sockets | `13/sk-buff`, `11/the-four-objects`, `cs:computer-networks/sockets-and-the-application-boundary` | `struct socket` versus `struct sock`, the dispatch tables, buffer accounting, and the wakeup path `epoll` hooks into. |
| 4 | `the-receive-path` | The Receive Path | Receive path | `13/sk-buff`, `10/softirqs`, `10/interrupt-affinity-and-balancing` | From DMA into a ring to a woken reader: NAPI, GRO, steering, and every place a packet can be dropped. |
| 5 | `the-transmit-path` | The Transmit Path | Transmit path | `13/sk-buff`, `13/sockets-in-the-kernel` | From `send()` to a completion interrupt: segmentation offload, the routing decision, the qdisc, and byte queue limits. |
| 6 | `tcp-in-the-kernel` | TCP in the Kernel | TCP | `13/sockets-in-the-kernel`, `13/the-receive-path`, `13/the-transmit-path` | The state machine as implemented, buffer autotuning, retransmission, pluggable congestion control, and the options that matter. |
| 7 | `netfilter-and-nftables` | netfilter and nftables | netfilter | `13/the-receive-path`, `13/the-transmit-path` | The hooks and a packet's path through them, and iptables versus nftables over the same machinery. |
| 8 | `connection-tracking-and-nat` | Connection Tracking and NAT | Conntrack and NAT | `13/netfilter-and-nftables`, `cs:computer-networks/nat-and-connection-tracking` | The per-flow state that makes stateful firewalls and NAT possible, and the table-full failure everyone meets once. |
| 9 | `routing-and-neighbours` | Routing and Neighbours | Routing | `13/the-transmit-path`, `cs:computer-networks/arp-icmp-and-neighbour-discovery` | The FIB, policy routing, the neighbour table's states, and `ip route get` as a debugging tool. |
| 10 | `network-namespaces-and-virtual-devices` | Network Namespaces and Virtual Devices | Namespaces and veth | `13/routing-and-neighbours`, `06/threads-are-tasks` | A complete independent stack per namespace, veth pairs and bridges, and a two-namespace network built by hand. |
| 11 | `traffic-control` | Traffic Control and qdiscs | Traffic control | `13/the-transmit-path` | The qdisc layer, fq_codel and cake versus htb, shaping versus policing, and the ingress hook. |
| 12 | `diagnosing-network-problems` | Diagnosing Network Problems | Diagnosing networks | `13/tcp-in-the-kernel`, `13/the-receive-path`, `13/netfilter-and-nftables`, `13/routing-and-neighbours` | A worked investigation from "connections hang" to a named cause, and what `tcpdump` can and cannot see. |

Extra `related` entries:
- Page 1: `["computer-science/computer-networks/osi-and-tcp-ip-models", "linux/guided-traces/the-life-of-a-packet"]`
- Page 6: `["computer-science/computer-networks/transport-layer-tcp-udp"]`
- Page 9: `["computer-science/computer-networks/network-layer-and-routing"]`
- Page 10: `["linux/networking-stack/connection-tracking-and-nat"]`
- Page 12: `["linux/block-layer-and-storage/diagnosing-io-problems", "linux/scheduling/diagnosing-scheduling-latency"]`

- [ ] **Step 5: Add the five CS backfill entries to `manifest.external`**

Same shape as the nine already there. Positions append after each folder's existing pages:
- `storage/` currently has positions 1–5.
- `computer-networks/` currently has positions 1–5.

Re-check both folders before writing. If a position now collides, take the next free integer rather than renumbering existing pages.

| path | id | title | sidebar_label | position | tags | summary |
|---|---|---|---|---|---|---|
| `docs/computer-science/storage/raid-and-redundancy.md` | `raid-and-redundancy` | RAID and Redundancy | RAID | 6 | `["computer-science", "storage", "raid"]` | Striping, mirroring, and parity as three different answers to disk failure, the write hole, and why the rebuild is the dangerous part. |
| `docs/computer-science/storage/crash-consistency-and-journaling.md` | `crash-consistency-and-journaling` | Crash Consistency and Journaling | Crash consistency | 7 | `["computer-science", "storage", "durability"]` | Why one logical update is many block writes, and how fsck, journaling, copy-on-write, and log structure each keep a crash from leaving nonsense on disk. |
| `docs/computer-science/computer-networks/sockets-and-the-application-boundary.md` | `sockets-and-the-application-boundary` | Sockets and the Application Boundary | Sockets API | 6 | `["computer-science", "computer-networks", "sockets"]` | The socket API as the one networking interface a program actually sees: descriptors, the call lifecycle, blocking and readiness, and what `send` does not promise. |
| `docs/computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md` | `arp-icmp-and-neighbour-discovery` | ARP, ICMP, and Neighbour Discovery | ARP and ICMP | 7 | `["computer-science", "computer-networks", "arp", "icmp"]` | How IP finds a next hop's link-layer address and how ICMP reports trouble — the protocols behind `ping`, `traceroute`, and path-MTU discovery. |
| `docs/computer-science/computer-networks/nat-and-connection-tracking.md` | `nat-and-connection-tracking` | NAT and Connection Tracking | NAT | 8 | `["computer-science", "computer-networks", "nat"]` | Rewriting addresses in flight, why that forces a device to remember every flow, and the mapping behaviours that decide whether peer-to-peer traffic works. |

- [ ] **Step 6: Validate the manifest is well-formed JSON**

Run: `node -e "const m=require('./tools/linux-docs-manifest.json'); console.log(m.folders.length, m.folders.reduce((n,f)=>n+f.pages.length,0), m.external.length)"`
Expected: `14 158 14` — fourteen folders, 158 manifest pages (122 from Phases 1–2 plus 36 new), fourteen external pages.

- [ ] **Step 7: Scaffold**

Run: `npm run scaffold:linux`
Expected: `scaffold: 41 file(s) created, 131 left alone, 14 category file(s) written`.
- *Created* = the 36 new stubs plus the 5 CS backfill stubs.
- *Left alone* = the 122 Phase 1–2 manifest pages plus the 9 earlier external pages.

**If any existing page is reported as created, stop and restore it from git.** That means `--force` leaked in and a finished page was overwritten with a stub.

- [ ] **Step 8: Confirm nothing existing was clobbered**

```bash
git status --short docs/linux docs/computer-science
git diff --stat -- docs/linux/0* docs/linux/10-* docs/computer-science
```

Expected: `git status` shows only new untracked files and the three new `_category_.json` files. `git diff --stat` prints nothing — the regenerated `_category_.json` files for 00–10 are byte-identical because their manifest entries were not touched. Any diff in an existing page is a bug in this task.

- [ ] **Step 9: Run the gates**

```bash
npm run check:linux
npm run test:graph
npm run build
```

Expected: `check-linux-docs: OK — 123 written page(s), 36 stub(s)`, the graph tests pass, and the build is green.

**A build failure here is almost always a prerequisite id typo.** The usual culprits are a leftover numeric prefix (`linux/12-block-layer-and-storage/...`) or a `cs:` short form not expanded to `computer-science/...`. The plugin names the offending file and the three closest existing ids. Fix the manifest. Re-run `npm run scaffold:linux -- --force` only for a stub whose front matter is wrong, and only after confirming with `git status` that the file you are forcing is a new stub. Then rebuild.

- [ ] **Step 10: Eyeball the sidebar**

Run: `npm run start` and open `http://localhost:3000/knowledge-base/docs/linux/`. Confirm fourteen folders appear in position order, with the three new ones after "Interrupts, Time, and Deferred Work", each with its description on its generated index page. Open `the-network-stack-map` and confirm its `<PrereqBlock>` "Before this" chip leads to folder 10. Stop the server.

- [ ] **Step 11: Commit**

```bash
git add tools/linux-docs-manifest.json docs/linux docs/computer-science
git commit -m "docs: scaffold linux folders 11-13 and the phase 3 CS backfill stubs"
```

---
## Task 2: CS backfill 12 and 13 — RAID, and crash consistency — with storage backlinks

**Files:**
- Modify: `docs/computer-science/storage/raid-and-redundancy.md` (stub → written)
- Modify: `docs/computer-science/storage/crash-consistency-and-journaling.md` (stub → written)
- Modify: `docs/computer-science/storage/intro.md`
- Modify: `docs/computer-science/storage/filesystems-basics.md`
- Modify: `docs/computer-science/storage/hard-disk-drives.md`
- Modify: `docs/computer-science/storage/nvme-and-storage-interfaces.md`
- Modify: `docs/computer-science/databases/transactions-and-acid.md`
- Modify: `docs/computer-science/databases/indexing-and-storage-engines.md`

**Interfaces:**
- Consumes: nothing from this phase except the Task 1 stubs. These pages come first because folder 11 and 12 pages declare them in `prerequisites`.
- Produces:
  - doc id `computer-science/storage/raid-and-redundancy`, a prerequisite of `12/software-raid`;
  - doc id `computer-science/storage/crash-consistency-and-journaling`, a prerequisite of `11/journaling-and-crash-consistency`;
  - the reverse edges the spec requires. **Backlinks are mandatory for this section** — a dependency graph with one-way edges is half a graph.

These are **`computer-science/` pages, not `docs/linux/` pages**: no `prerequisites` key, no `<KernelFacts>`, no `<Lab>`, no `<Src>`, no kernel API surface, and **no Linux-specific mechanism** (jbd2, md and `fsync` semantics belong to folders 11 and 12). Delete the `:::info[Not yet written]` block and keep the front matter.

**Match the folder's existing template exactly.** Every page in `storage/` uses the same skeleton: `# H1`, a lead paragraph, `## Core Concepts`, `## Mechanism` (with `###` subsections), `## Practical Usage`, `## Edge Cases & Pitfalls`, `## Comparisons`, `## References` (with `### Books & Videos`), and `## Related Pages`. Open `filesystems-basics.md` and copy its section order and voice. The briefs below map content onto that skeleton.

**CS figures keep licence discipline.** Any figure placed here needs a `static/img/cs/SOURCES.md` row with a licence and a `license=` prop on `<Figure>`. Task 22 adds the one Commons RAID figure; write the pages with their Mermaid and table anchors so they stand alone without it.

### `raid-and-redundancy.md` — RAID and Redundancy

- **Lead:** redundancy answers one question — "what happens when a disk dies?" — and RAID gives three different answers: spread the data (striping), duplicate it (mirroring), or store enough arithmetic to recompute it (parity). Each answer spends capacity and write performance differently. None of them answers a different question people keep asking it: "what happens when I delete the wrong file?"
- **`## Core Concepts`** — a short glossary list: stripe, strip/chunk, mirror, parity, degraded, rebuild (resync), hot spare, URE (unrecoverable read error), write hole.
- **`## Mechanism`**
  - `### Striping (RAID 0)` — throughput by parallelism, and failure probability that *grows* with every disk added.
  - `### Mirroring (RAID 1, RAID 10)` — reads can go to either copy; writes go to all; RAID 10 as striped mirrors, and why it beats RAID 01 on failure tolerance.
  - `### Parity (RAID 5)` — XOR worked through with a 4-bit example on three data disks. Show one strip, compute its parity, "lose" one disk, recompute it. Then explain the small-write penalty: read old data, read old parity, write new data, write new parity — four I/Os for one logical write. Parity rotates across disks so no single disk becomes the bottleneck.
  - `### Double parity (RAID 6)` — P as XOR plus Q as a Reed–Solomon syndrome over a Galois field. One paragraph, **without** the field arithmetic; state that it tolerates any two failures and costs a second parity write.
  - `### The write hole` — data and parity are updated by separate writes; a crash between them leaves a strip whose parity is silently wrong, discovered only when a disk fails and reconstruction produces garbage. Name the three families of fix: a battery- or flash-backed controller cache, a journal or write-intent log, and copy-on-write that never updates a strip in place. Link forward to `./crash-consistency-and-journaling.md` for the general form of the problem.
  - `### Rebuild` — reconstructing a failed disk reads *every* surviving disk end to end. Rebuild time grows with capacity, the array runs degraded (and slower) the whole time, and a second failure or an URE during a RAID 5 rebuild loses data. Give the arithmetic shape — URE rate of 1 in 10^14 bits (a typical consumer-HDD datasheet figure) against a multi-terabyte read — as a *shape*, with the instruction to use the drive's own datasheet figure; do not present a single scary percentage as fact.
- **`## Practical Usage`** — choosing a level by workload: RAID 10 for random-write databases, RAID 6 for large capacity-oriented arrays, RAID 1 for boot and small critical volumes. Hardware controllers versus software RAID versus filesystem-integrated redundancy (ZFS RAID-Z, Btrfs) as three places the logic can live.
- **`## Edge Cases & Pitfalls`** — RAID is not a backup: it faithfully replicates deletions, corruption and ransomware. Also: same-batch disks failing together; SSD wear-out being correlated across mirrors that receive identical writes; degraded-mode performance being an outage in disguise; silent corruption that parity cannot distinguish from a correct write without checksums.
- **`## Comparisons`** — **Anchor table:** RAID 0, 1, 5, 6, 10 across usable capacity (for *n* disks), failures tolerated, read performance, write penalty, rebuild exposure.
- **Anchor diagram:** a Mermaid `flowchart LR` of four disks in RAID 5 across three strips, with the parity block drawn on a different disk in each strip. Caption: "Where parity lives in RAID 5: one parity block per strip, rotating across disks so no single disk carries all of it."
- **`## References`**
  - Patterson, Gibson & Katz, *"A Case for Redundant Arrays of Inexpensive Disks (RAID)"*, SIGMOD 1988 — the paper that named the levels; short, readable, and the source of the vocabulary.
  - Leventhal, *"Triple-Parity RAID and Beyond"*, ACM Queue 2009 (`https://queue.acm.org/detail.cfm?id=1670144`) — the rebuild-exposure argument made with real numbers, and why RAID 6 became the capacity default.
  - SNIA, *Common RAID Disk Data Format (DDF)* specification — the vendor-neutral definitions of the standard levels.
  - `### Books & Videos` — Arpaci-Dusseau & Arpaci-Dusseau, *Operating Systems: Three Easy Pieces*, ch. "Redundant Arrays of Inexpensive Disks" — free online, with the worked parity analysis this page summarises.
- **`## Related Pages`** — `./hard-disk-drives.md`, `./crash-consistency-and-journaling.md`, `./intro.md`, and `../../linux/12-block-layer-and-storage/software-raid.md` (annotated: "how Linux's md driver implements these levels").

### `crash-consistency-and-journaling.md` — Crash Consistency and Journaling

- **Lead:** a single logical update — appending one block to a file — is several physical writes: the data block, the inode that now points at it, and the bitmap that marks it used. A crash can land between any two of them, leaving the disk in a state no program ever wrote. Crash consistency is the discipline of making every possible prefix of those writes recoverable. The four families of answer — scan and repair, journal, copy-on-write, and log structure — are the design space every real filesystem sits in.
- **`## Core Concepts`** — crash consistency, atomic update, write-ahead logging, commit record, checkpoint, copy-on-write, log-structured, flush/barrier, FUA, volatile write cache.
- **`## Mechanism`**
  - `### The problem, worked` — the append example as a **table of partial outcomes**: each subset of {data, inode, bitmap} that reached disk, what the disk now claims, and whether the result is harmless, a leak, or corruption. This table is the page's core.
  - `### fsck: scan and repair` — check every structure against every other after a crash. It works, and its cost is proportional to the size of the disk rather than the size of the update.
  - `### Journaling (write-ahead logging)` — write the intended changes to a log, write a commit record, then apply them in place (checkpoint), then free the log space. Recovery replays committed transactions and discards uncommitted ones. Then the three modes:
    - **metadata-only journaling** — cheap, but data blocks can contain garbage after a crash;
    - **ordered** — data written before its metadata commits, so metadata never points at garbage;
    - **full data journaling** — everything written twice.
  - `### Copy-on-write` — never overwrite live data. Write new versions elsewhere, then atomically swap one root pointer. A crash leaves either the old tree or the new one, never a mixture. Cost: fragmentation and write amplification.
  - `### Log-structured` — the entire disk is the log; reads are indexed, and a cleaner reclaims dead space. One paragraph, noting that a flash translation layer is itself a log-structured system (link `./ssd-and-nand-flash.md`).
  - `### Barriers, flush, and the lie a disk can tell` — every scheme above assumes a write the device acknowledged is durable. Devices have volatile write caches, so the host must send a *flush* (or a write with *FUA*, forced unit access) for ordering to hold across a power cut. Enterprise SSDs carry power-loss-protection capacitors; many consumer devices do not. A device that acknowledges a flush it did not perform defeats every scheme on this page.
- **`## Practical Usage`** — what an application must do for a durable replace, as a numbered recipe: write to a temporary file, flush that file, rename it over the target, flush the *directory*. Each step is required because a filesystem's consistency guarantee covers *its own* metadata, not the application's intent. Databases take this further with their own write-ahead log — link `../databases/transactions-and-acid.md` for the durability letter of ACID rather than re-deriving it.
- **`## Edge Cases & Pitfalls`**
  - Consistency is not durability: a consistent filesystem can still have lost the last five seconds.
  - A flush that fails may not be reported again on retry. State this generally; the Linux-specific story (`errseq_t`, the 2018 PostgreSQL episode) belongs to the Linux page.
  - Rename is atomic only within one filesystem.
  - Crash-consistency bugs in applications are far more common than in filesystems.
- **`## Comparisons`** — **Anchor table:** fsck, journaling (ordered), full data journaling, copy-on-write, log-structured, compared on recovery time, write overhead, whether data is protected or only metadata, and one real filesystem each (ext2, ext4, ext4 `data=journal`, ZFS/Btrfs, F2FS/NILFS).
- **Anchor diagram:** a Mermaid `sequenceDiagram` — Application, Filesystem, Journal area, Home locations, Device cache — showing the journal write, the flush, the commit record, the flush, the checkpoint, and the free. Mark each point where a crash is survivable with `Note over` annotations. Caption: "One journaled transaction, from intent to checkpoint, with the moments a crash can land and what recovery does at each."
- **`## References`**
  - Arpaci-Dusseau & Arpaci-Dusseau, *OSTEP*, ch. 42 "Crash Consistency: FSCK and Journaling" and ch. 43 "Log-structured File Systems" — free online; the best structured treatment, and the source of the append example.
  - Pillai et al., *"All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications"*, OSDI 2014 — the evidence that applications, not filesystems, are where crash consistency usually breaks.
  - Rosenblum & Ousterhout, *"The Design and Implementation of a Log-Structured File System"*, ACM TOCS 1992 — the original log-structured design.
  - Rebello et al., *"Can Applications Recover from fsync Failures?"*, USENIX ATC 2020 — what happens when the flush itself fails, across filesystems and applications.
  - `### Books & Videos` — Kleppmann, *Designing Data-Intensive Applications*, ch. 7 — a purchase; the database-side view of the same write-ordering problem.
- **`## Related Pages`** — `./filesystems-basics.md`, `./raid-and-redundancy.md`, `../databases/transactions-and-acid.md`, `../../linux/11-vfs-and-filesystems/journaling-and-crash-consistency.md` (annotated: "what Linux filesystems actually guarantee"), and `../../linux/08-memory-management/writeback-and-fsync.md`.

**No-duplication note:** `filesystems-basics.md` already carries a `### Journaling and crash consistency` subsection. Leave it in place as the introduction; this page is the depth. Do not trim the existing page — add the pointer (Step 3).

- [ ] **Step 1: Write `raid-and-redundancy.md`** to the brief above, deleting the stub block.
- [ ] **Step 2: Write `crash-consistency-and-journaling.md`** to the brief above.
- [ ] **Step 3: Add the backlinks.** Each is one bullet appended to the page's existing `## Related Pages` list (or a new bullet in `intro.md`'s page list), matching the list's existing format. Do not restructure anything.

| Page | Bullet to add |
|---|---|
| `storage/intro.md` | Two bullets after `Filesystems Basics`, in the list's existing `- [Title](./file.md) — description` form: RAID and Redundancy — "striping, mirroring, parity, the write hole, and rebuild risk"; Crash Consistency and Journaling — "why a crash can corrupt a disk, and the four designs that prevent it". |
| `storage/filesystems-basics.md` | `- [Crash Consistency and Journaling](./crash-consistency-and-journaling.md) — the full design space behind the journaling section above.` and `- [Why the VFS Exists](../../linux/11-vfs-and-filesystems/why-vfs-exists.md) — how Linux puts one interface over many filesystems.` **Also confirm** the page's VFS diagram and prose describe the VFS generically, not as Linux-specific behaviour. If they make a Linux-specific claim, generalise the sentence and say so in the commit message. |
| `storage/hard-disk-drives.md` | `- [RAID and Redundancy](./raid-and-redundancy.md) — why growing drive capacity makes rebuilds the risky part.` |
| `storage/nvme-and-storage-interfaces.md` | `- [NVMe in the Kernel](../../linux/12-block-layer-and-storage/nvme-in-the-kernel.md) — how Linux maps NVMe queues onto its block layer.` |
| `databases/transactions-and-acid.md` | `- [Crash Consistency and Journaling](../storage/crash-consistency-and-journaling.md) — what durability requires from the storage underneath.` |
| `databases/indexing-and-storage-engines.md` | `- [Crash Consistency and Journaling](../storage/crash-consistency-and-journaling.md) — write-ahead logs and copy-on-write, from the filesystem side.` and `- [Buffered I/O, O_DIRECT, and Alignment](../../linux/12-block-layer-and-storage/buffered-direct-and-alignment.md) — why storage engines often bypass the page cache.` |

- [ ] **Step 4: Verify every link resolves**

Run: `npm run build`
Expected: green. Most of this task's changes are links, so a broken relative path is the expected failure mode; the build names the file and the target.

- [ ] **Step 5: Confirm no CS page acquired Linux-section furniture**

Run: `rtk run "grep -rln 'KernelFacts\|<Src \|<Lab ' docs/computer-science"`
Expected: no output.

- [ ] **Step 6: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/computer-science
git commit -m "docs: write CS backfill pages on RAID and crash consistency, add storage backlinks"
```

---

## Task 3: CS backfill 14, 15 and 16 — sockets, ARP/ICMP, NAT — with networking backlinks

**Files:**
- Modify: `docs/computer-science/computer-networks/sockets-and-the-application-boundary.md` (stub → written)
- Modify: `docs/computer-science/computer-networks/arp-icmp-and-neighbour-discovery.md` (stub → written)
- Modify: `docs/computer-science/computer-networks/nat-and-connection-tracking.md` (stub → written)
- Modify: `docs/computer-science/computer-networks/intro.md`
- Modify: `docs/computer-science/computer-networks/data-link-layer.md`
- Modify: `docs/computer-science/computer-networks/network-layer-and-routing.md`
- Modify: `docs/computer-science/computer-networks/transport-layer-tcp-udp.md`
- Modify: `docs/computer-science/operating-systems/interprocess-communication.md`

**Interfaces:**
- Consumes: Task 1's stubs.
- Produces:
  - doc id `computer-science/computer-networks/sockets-and-the-application-boundary`, a prerequisite of `13/sockets-in-the-kernel`;
  - doc id `computer-science/computer-networks/arp-icmp-and-neighbour-discovery`, a prerequisite of `13/routing-and-neighbours`;
  - doc id `computer-science/computer-networks/nat-and-connection-tracking`, a prerequisite of `13/connection-tracking-and-nat`;
  - the backlinks into all three.

Same rules as Task 2: CS house style, no Linux furniture, **no Linux mechanism**. `struct sock`, conntrack and the neighbour table belong to folder 13. Match the `computer-networks/` template — open `transport-layer-tcp-udp.md` and copy its section order: `## Core Concepts`, `## Mechanism` (`###` subsections), `## Practical Usage`, `## Edge Cases & Pitfalls`, `## Comparisons`, `## References` + `### Books & Videos`, `## Related Pages`.

### `sockets-and-the-application-boundary.md` — Sockets and the Application Boundary

- **Lead:** every networked program, in every language, eventually makes the same handful of calls. The socket API is the boundary between an application and a network stack it does not own. The existing pages in this folder describe what travels on the wire; this page describes what a program can *ask for*, and — just as important — what it is never told.
- **`## Core Concepts`** — socket, address family, socket type, descriptor, listening socket, connected socket, blocking, non-blocking, readiness, backlog, half-close.
- **`## Mechanism`**
  - `### A socket is a file descriptor` — so `read`/`write`/`close`/`dup` work, sockets are inherited across `fork`, and readiness APIs treat them like any other descriptor. This is a design choice from BSD 4.2 that shaped every later API.
  - `### The call lifecycle` — server: `socket` → `bind` → `listen` → `accept` (returns a *new* descriptor); client: `socket` → `connect`; then `send`/`recv` and `shutdown`/`close`. Draw the **anchor** here.
  - `### Families and types` — **table**: `AF_INET`, `AF_INET6`, `AF_UNIX`, `AF_PACKET`, `AF_NETLINK` × `SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_RAW`, `SOCK_SEQPACKET`, with one real use per meaningful combination. Note that `AF_PACKET`/`AF_NETLINK` are Linux-specific families and say so.
  - `### The listening socket's two queues` — conceptually: connections still completing their handshake, and completed connections waiting for `accept`. The `backlog` argument bounds the second. What a client sees when it overflows: a stalled handshake and retransmitted SYNs, not a refusal. Keep this conceptual; the kernel's implementation is `linux/13`'s.
  - `### Blocking, non-blocking, and readiness` — `EAGAIN`/`EWOULDBLOCK`; `select` and `poll` as portable readiness APIs with O(n) cost per call; `epoll` (Linux) and `kqueue` (BSD/macOS) as the scalable, OS-specific answers. Readiness ("you may try now") versus completion ("it is done") as the conceptual split that `io_uring` and IOCP sit on the other side of.
  - `### Byte streams have no message boundaries` — a `send` of 1000 bytes may arrive as three `recv`s and vice versa; partial writes are normal; framing is the application's job. The single most common socket-programming bug.
- **`## Practical Usage`** — a minimal TCP echo server and client in C (≤ 40 lines each, ` ```c `), correct about partial writes and `EINTR`. Keep error handling real but terse.
- **`## Edge Cases & Pitfalls`**
  - `send` returning success means the bytes were copied into a local buffer, not delivered.
  - `close` with unread data can reset the connection.
  - `SO_REUSEADDR` versus `SO_REUSEPORT` do different things.
  - `SIGPIPE` on writing to a closed peer.
  - Nagle's algorithm plus delayed ACK producing 40–200 ms stalls on small request/response traffic (`TCP_NODELAY`).
  - Whoever closes first holds `TIME_WAIT`.
- **`## Comparisons`** — `select` / `poll` / `epoll` / `kqueue` / completion-based (IOCP, `io_uring`) across portability, per-call cost, and model (readiness vs completion).
- **Anchor:** a Mermaid `sequenceDiagram` — Client app, Client stack, Server stack, Server app — with each API call on the application lanes aligned against the SYN, SYN-ACK, ACK and FIN it causes on the wire. Mark where `connect` returns and where `accept` returns. Caption: "Which socket call causes which packet, and the exact moment each blocking call returns."
- **`## References`**
  - The Open Group Base Specifications, `socket()` and `<sys/socket.h>` — `https://pubs.opengroup.org/onlinepubs/9799919799/functions/socket.html`. The portable contract, so you can tell POSIX behaviour from OS extensions.
  - `https://man7.org/linux/man-pages/man7/socket.7.html` and `man 7 tcp` — Linux's own statement of options and semantics, the bridge to folder 13.
  - Kegel, *"The C10K problem"* (`http://www.kegel.com/c10k.html`) — historical (last substantively updated in the 2000s) but the clearest account of why readiness APIs had to change.
  - `### Books & Videos` — Stevens, Fenner & Rudoff, *UNIX Network Programming, Vol. 1* (3rd ed.) — a purchase; the definitive socket-programming reference.
- **`## Related Pages`** — `./transport-layer-tcp-udp.md`, `./osi-and-tcp-ip-models.md`, `../operating-systems/interprocess-communication.md`, and `../../linux/13-networking-stack/sockets-in-the-kernel.md` (annotated: "how Linux implements every call on this page").

### `arp-icmp-and-neighbour-discovery.md` — ARP, ICMP, and Neighbour Discovery

- **Lead:** IP routes by IP address, but an Ethernet frame is delivered by MAC address, so every hop needs a translation from "the next router's IP" to "the next router's hardware address". And when delivery fails, IP needs a way to say so. ARP (and IPv6's Neighbour Discovery) does the first job; ICMP does the second. Both are small and easy to dismiss, and filtering either one breaks networks in ways that are hard to diagnose.
- **No-duplication:** `data-link-layer.md` already explains what ARP resolves and shows the ARP cache command. **Do not re-explain the frame format or the basic request/reply.** Start from "`data-link-layer.md` introduced ARP; this page covers its lifecycle, its failure modes, and its IPv6 replacement."
- **`## Core Concepts`** — next hop, neighbour, ARP cache, gratuitous ARP, proxy ARP, ICMP type/code, TTL, PMTU, NDP, solicited-node multicast, DAD, SLAAC.
- **`## Mechanism`**
  - `### ARP's lifecycle` — broadcast request, unicast reply, cache entry with aging, re-validation. Gratuitous ARP for announcing a moved address (failover, VRRP) and duplicate-address detection (RFC 5227). Proxy ARP in one paragraph.
  - `### ARP has no authentication` — any host may answer. State ARP spoofing defensively: what it enables (interception on the local segment) and the mitigations (dynamic ARP inspection on switches, static entries for critical gateways, encryption above IP). No attack tooling or procedure.
  - `### ICMP: IP's error channel` — **table** of the types that matter: Echo Request/Reply (8/0), Destination Unreachable (3) with codes 0/1/3/4 (4 = fragmentation needed), Time Exceeded (11), Redirect (5), plus ICMPv6 Packet Too Big (2). What each tells the sender.
  - `### traceroute` — sending packets with increasing TTL and collecting Time Exceeded replies. Why UDP-, ICMP- and TCP-based traceroute see different paths through firewalls, and why a `*` row does not mean loss.
  - `### Path MTU discovery and the black hole` — sending with "don't fragment" and lowering the size on Packet Too Big / Fragmentation Needed. When a firewall drops those ICMP messages, small packets (the handshake) succeed and large ones silently vanish: the connection opens and then hangs. This is the canonical consequence of "block all ICMP".
  - `### IPv6 Neighbour Discovery` — ARP's replacement built on ICMPv6: Neighbour Solicitation/Advertisement over solicited-node multicast instead of broadcast, Router Solicitation/Advertisement, duplicate address detection, and SLAAC in brief. In IPv6, ICMP is not optional at all.
- **`## Practical Usage`** — reading an ARP/neighbour cache, `ping` and what its RTT includes (the remote host's processing, and routers deliberately deprioritising ICMP they must generate), `traceroute`/`mtr`, and `tracepath` for PMTU. Commands in ` ```bash `, sample output in ` ```text `.
- **`## Edge Cases & Pitfalls`**
  - "`ping` works, so the network is fine" (TCP can still be broken by PMTU, firewalls, or MTU mismatch).
  - "High latency on an intermediate `traceroute` hop" is usually that router rate-limiting ICMP, not a slow link.
  - ARP flux on multi-homed hosts.
  - Stale neighbour entries after a MAC change.
- **`## Comparisons`** — ARP vs NDP on transport (Ethernet broadcast vs ICMPv6 multicast), security story (none vs SEND/RA-Guard), and address autoconfiguration.
- **Anchor:** a Mermaid `sequenceDiagram` — Host A, Switch, Router, Server — showing A's first packet to an off-subnet server: ARP request for the *router's* IP (not the server's), reply, frame to the router's MAC carrying the server's IP. Then a second exchange where an oversized packet draws an ICMP Fragmentation Needed back from the router. Caption: "Resolving the next hop, not the destination — and the ICMP message that keeps a large packet from vanishing."
- **`## References`**
  - RFC 826 (ARP), RFC 792 (ICMP), RFC 4861 (IPv6 Neighbour Discovery) — the primary specifications, all short.
  - RFC 1191 (Path MTU Discovery) and RFC 4890 ("Recommendations for Filtering ICMPv6 Messages in Firewalls") — the operational case for not blocking ICMP.
  - RFC 5227 (IPv4 Address Conflict Detection) — gratuitous ARP done correctly.
  - `### Books & Videos` — Stevens, *TCP/IP Illustrated, Vol. 1* (2nd ed., Fall & Stevens) — ARP and ICMP chapters with packet traces.
- **`## Related Pages`** — `./data-link-layer.md`, `./network-layer-and-routing.md`, `./nat-and-connection-tracking.md`, and `../../linux/13-networking-stack/routing-and-neighbours.md` (annotated: "the kernel's neighbour table and its states").

### `nat-and-connection-tracking.md` — NAT and Connection Tracking

- **Lead:** network address translation rewrites addresses in packets as they pass through. The moment a device rewrites an outgoing packet's source, it must recognise the reply and rewrite it back, so it has to remember every flow it has touched. NAT is therefore stateful by nature, and that state explains both its usefulness and nearly every way it breaks.
- **No-duplication:** `network-layer-and-routing.md` has a `### NAT` subsection introducing private addresses and basic NAT. Treat that as the introduction and go deeper; do not restate RFC 1918 ranges beyond one sentence with a link.
- **`## Core Concepts`** — SNAT, DNAT, NAPT/PAT, masquerading, 5-tuple, mapping, binding timeout, hairpinning, ALG, CGNAT, connection tracking, stateful firewall.
- **`## Mechanism`**
  - `### The translation table` — a mapping from inside (address, port) to outside (address, port) per flow, created by the first outbound packet and used to rewrite both directions. **Anchor** here.
  - `### The forms` — **table**: static 1:1 NAT, source NAT with port translation (NAPT — what a home router does), destination NAT / port forwarding, masquerade (SNAT whose outside address follows the interface), hairpin NAT (inside host reaching an inside server via the outside address), and carrier-grade NAT (RFC 6598's `100.64.0.0/10`).
  - `### Why the state is unavoidable` — replies must be matched to mappings; mappings must expire; TCP's state can be inferred from flags, but UDP "connections" exist only as timeouts. A mapping that expires while a long-idle connection is still open is the source of the "SSH session dies after an hour idle" class of problem, and of keepalives as its fix.
  - `### Mapping and filtering behaviour` — RFC 4787's vocabulary: endpoint-independent versus address-dependent versus address-and-port-dependent mapping and filtering. Explain why endpoint-independent mapping is what makes peer-to-peer traffic possible and symmetric NAT is what prevents it.
  - `### Protocols that carry addresses inside` — FTP active mode, SIP, and anything embedding an IP in its payload break under translation; application-level gateways rewrite payloads to compensate, and why ALGs are fragile.
  - `### Traversal` — STUN (discover your mapping), TURN (relay when you cannot), ICE (try everything and pick what works). One paragraph each, conceptual.
  - `### A stateful firewall is the same table` — tracking flows without translating them; "allow replies to connections initiated from inside" is a lookup in exactly this state.
- **`## Practical Usage`** — reading a home router's port-forwarding rule as DNAT, recognising CGNAT (a WAN address in `100.64.0.0/10`), and why hosting behind CGNAT needs a relay or IPv6.
- **`## Edge Cases & Pitfalls`**
  - NAT is not a firewall — it blocks unsolicited inbound traffic only as a side effect of having no mapping, and UPnP/port forwarding punches holes silently.
  - Table exhaustion under many short flows.
  - Timeouts killing idle long-lived connections.
  - Logging and attribution under CGNAT needing ports as well as addresses.
  - IPv6 was designed to make NAT unnecessary, and NAT66/NPTv6 exist anyway.
- **`## Comparisons`** — NAT44, NAT64/DNS64 (RFC 6146/6147), NPTv6, and plain IPv6 with a stateful firewall, compared on what they translate and what state they keep.
- **Anchor:** a Mermaid `sequenceDiagram` — Inside host `192.168.1.10`, NAT router (outside `203.0.113.5`), Server `198.51.100.7` — showing the outbound SYN with its 5-tuple before and after rewrite, the mapping entry created (as a `Note over` NAT), and the reply rewritten back. Caption: "One outbound connection through NAPT: the tuple rewritten on the way out, the mapping it creates, and the reverse rewrite on the way back."
- **`## References`**
  - RFC 3022 (Traditional NAT) and RFC 4787 (NAT Behavioral Requirements for Unicast UDP) — the definition, and the mapping/filtering vocabulary this page uses.
  - RFC 5382 (NAT Behavioral Requirements for TCP) — timeout and state handling for TCP specifically.
  - RFC 8445 (ICE) — how real-time applications get through NAT, with STUN and TURN as its components.
  - RFC 6888 (Requirements for CGN) — what carrier-grade NAT must do and the operational problems it creates.
  - `### Books & Videos` — Fall & Stevens, *TCP/IP Illustrated, Vol. 1* (2nd ed.), the NAT and firewall chapter.
- **`## Related Pages`** — `./network-layer-and-routing.md`, `./transport-layer-tcp-udp.md`, `./arp-icmp-and-neighbour-discovery.md`, and `../../linux/13-networking-stack/connection-tracking-and-nat.md` (annotated: "how Linux's conntrack implements this table").

- [ ] **Step 1: Write `sockets-and-the-application-boundary.md`** to the brief above, deleting the stub block. Compile the C example (`cc -Wall -o echo echo.c`) and run server and client once, so the listing on the page is known to work.
- [ ] **Step 2: Write `arp-icmp-and-neighbour-discovery.md`** to the brief above. Capture the `ip neigh` / `ping` / `tracepath` output from a real machine rather than composing it.
- [ ] **Step 3: Write `nat-and-connection-tracking.md`** to the brief above. Use documentation address ranges only (RFC 5737 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, plus RFC 1918 for inside hosts).
- [ ] **Step 4: Add the backlinks**, one bullet each, in each list's existing format:

| Page | Bullet to add |
|---|---|
| `computer-networks/intro.md` | Three bullets after `Transport Layer: TCP & UDP`, in the list's existing bold-link form: **Sockets and the Application Boundary** — "the API every networked program uses, and what it never tells you"; **ARP, ICMP, and Neighbour Discovery** — "next-hop resolution, IP's error channel, and why blocking ICMP breaks things"; **NAT and Connection Tracking** — "address translation and the per-flow state it forces". |
| `computer-networks/data-link-layer.md` | `- [ARP, ICMP, and Neighbour Discovery](./arp-icmp-and-neighbour-discovery.md) — ARP's lifecycle and failure modes, and IPv6's replacement for it.` |
| `computer-networks/network-layer-and-routing.md` | `- [ARP, ICMP, and Neighbour Discovery](./arp-icmp-and-neighbour-discovery.md) — how a router reaches its next hop, and how IP reports failures.` and `- [NAT and Connection Tracking](./nat-and-connection-tracking.md) — the NAT section above, in depth.` and `- [Routing and Neighbours](../../linux/13-networking-stack/routing-and-neighbours.md) — the Linux kernel's routing table and neighbour cache.` |
| `computer-networks/transport-layer-tcp-udp.md` | `- [Sockets and the Application Boundary](./sockets-and-the-application-boundary.md) — the API that applications use to reach TCP and UDP.` and `- [TCP in the Kernel](../../linux/13-networking-stack/tcp-in-the-kernel.md) — how Linux implements TCP's state machine and congestion control.` |
| `operating-systems/interprocess-communication.md` | `- [Sockets and the Application Boundary](../computer-networks/sockets-and-the-application-boundary.md) — sockets as IPC that works the same across a network.` |

- [ ] **Step 5: Verify**

```bash
npm run build
rtk run "grep -rln 'KernelFacts\|<Src \|<Lab ' docs/computer-science"
```

Expected: a green build and no grep output.

- [ ] **Step 6: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/computer-science
git commit -m "docs: write CS backfill pages on sockets, ARP/ICMP and NAT, add networking backlinks"
```

---
## Task 4: Folder 11 — why the VFS exists, and the four objects

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/why-vfs-exists.md`
- Modify: `docs/linux/11-vfs-and-filesystems/the-four-objects.md`

**Interfaces:**
- Consumes:
  - `04/container-of-and-embedded-structs` — the idiom every VFS object uses to reach its filesystem-private part;
  - `08/the-page-cache` — `address_space` is already defined there, so link it rather than re-define it.
- Produces:
  - `11/why-vfs-exists`, the folder's map page, which the spec says is written first;
  - `11/the-four-objects`, a prerequisite of seven later pages in folders 11 and 13. **Every later page in the folder refers back to these two constantly**, so their vocabulary becomes the folder's vocabulary.

### `why-vfs-exists.md` — Why the VFS Exists **[WAH]** **[Misc]**

- **Opens with:** a single `read()` call has to work whether the file lives on ext4, on a network server, in RAM, or nowhere at all (`/proc/cpuinfo` is generated on demand). The VFS makes that work: an indirection layer that defines what a filesystem must supply and dispatches every operation through function-pointer tables. It is object-oriented programming in C, and once the pattern is visible, the rest of this folder reads as variations on it.
- **Sections:**
  - `## The problem: one interface, many implementations` — a table of five very different "filesystems" (ext4, NFS, tmpfs, procfs, a FUSE filesystem), each with where its data actually lives. Every one of them answers `open`, `read`, `stat` and `readdir`.
  - `## Object-oriented C` — a struct of data plus a pointer to a struct of function pointers, and a caller that never knows which implementation it holds. Show a ` ```c ` excerpt of `struct file_operations` with 6–8 of its members, and link back to `../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md` for how a filesystem gets from the generic object to its own.
  - `## What a filesystem must supply` — register a `file_system_type`, fill a superblock at mount time, and provide operations tables for inodes, files, and (optionally) dentries and the address space. Keep this a map — each item is the subject of a later page, so name them and link them.
  - `## What actually happens` **[WAH]** — `cat /proc/meminfo` next to `cat /etc/hostname`. Both go through the same `openat` → `read` → dispatch path (show the two `strace` lines side by side). They diverge at exactly one point, the `f_op->read_iter` (or `seq_file` read) the file's operations table names: one lands in the page cache, the other calls a function that formats counters on the spot.
  - `## "Everything is a file", stated precisely` — everything is a *file descriptor*: sockets, pipes, `eventfd`, `timerfd`, and `pidfd` are not files on any filesystem, but they present the file-descriptor interface through the same `struct file`. Name `anon_inode` as the mechanism in one sentence.
  - `## Misconceptions` **[Misc]** —
    1. "The VFS is a filesystem." It stores nothing; it dispatches.
    2. "Everything in Linux is a file." Everything is a *descriptor*, and a socket has no path.
    3. "`/proc` files take up space." They have no storage at all; their contents are produced on each read.
- **Anchor:** a Mermaid `flowchart TB` — `read()` → syscall → VFS dispatch → four branches (ext4 → page cache → block layer; tmpfs → page cache with no backing device; procfs → a generator function; FUSE → `/dev/fuse` → a user-space daemon). Caption: "One `read()` and four destinations: the VFS dispatches, and each filesystem decides where the bytes come from."
- **KernelFacts:**
  - `structure` — `[["struct file_operations", "include/linux/fs.h"], ["struct file_system_type", "include/linux/fs.h"]]`
  - `path` — `"read() → ksys_read() → vfs_read() → file->f_op->read_iter() → filesystem"`
  - `observe` — `strace -e trace=openat,read cat /proc/meminfo /etc/hostname`
  - `trap` — "The VFS does not store anything or know any on-disk format. It is a dispatch layer, and a bug report that says 'the VFS lost my data' is almost always about a filesystem, the page cache, or the device underneath."
- **References:**
  - `https://docs.kernel.org/filesystems/vfs.html` — the kernel's own VFS overview, listing every operations table and what each member must do.
  - `<Src file="include/linux/fs.h" />` — the object and operations-table definitions, read directly.
  - Kerrisk, *The Linux Programming Interface*, ch. 14 "File Systems" — the user-visible side, including why `/proc` behaves as it does; a purchase.
  - Love, *Linux Kernel Development* (3rd ed.), ch. 13 "The Virtual Filesystem" — the clearest conceptual introduction; note that it predates v6.18 by many years and some structures have changed.

### `the-four-objects.md` — Superblock, Inode, Dentry, File

- **Opens with:** four objects, four questions. The **superblock** is a mounted filesystem instance. The **inode** is a file's identity and metadata, independent of any name. The **dentry** is one name-to-inode link in a path, cached. The **file** is one open instance, carrying a position and flags. Keeping the four apart explains hard links, deleting a file someone still has open, and why renaming a file you are writing to does not disturb the writer. This page draws their relationships once and the rest of the folder refers back to it.
- **Sections:**
  - `## The superblock: a mounted filesystem` — one per mounted instance (not per device, and not per mount point — bind mounts share one). What it holds: block size, the root dentry, `s_op`, the filesystem-private pointer, the inode list. Link forward to `./mounts-and-mount-namespaces.md` for `vfsmount`.
  - `## The inode: a file without a name` — identity (`i_ino`, `i_sb`), metadata (mode, owner, size, timestamps), link count, `i_op`, `i_fop`, and `i_mapping` pointing at the `address_space` from `../08-memory-management/the-page-cache.md`. The key fact: an inode has no name, and `i_nlink` counts names.
  - `## The dentry: a name, cached` — parent, name, inode pointer (or `NULL` for a *negative* dentry), `d_op`. Dentries form the in-memory tree path lookup walks; they exist for speed, not persistence. Link forward to `./path-lookup-and-the-dcache.md`.
  - `## The file: one open instance` — `f_path` (dentry plus mount), `f_inode`, `f_op`, `f_pos`, `f_flags`, `f_mode`, reference count. Two `open()`s of one path give two `struct file`s sharing one inode; a `fork` or `dup` gives two descriptors sharing one `struct file` — and therefore one file position.
  - `## Operations tables` — **table**: `super_operations`, `inode_operations`, `file_operations`, `dentry_operations`, `address_space_operations` × who owns it, what it covers, and two representative members each.
  - `## Lifetimes and what pins what` — an open file pins its dentry, which pins its inode, which pins its superblock. That chain is why an unlinked file still consumes disk space until the last descriptor closes, and why `umount` reports `EBUSY`.
  - `## Hard links and deleted-but-open files, explained` — two dentries pointing at one inode; `unlink` removing a dentry and decrementing `i_nlink`; data freed only when the link count and the open count both reach zero. Show the `ls -l /proc/PID/fd` "(deleted)" marker.
- **Anchor:** a Mermaid `classDiagram` — `super_block`, `inode`, `dentry`, `file`, `address_space`, `vfsmount` — with the 4–6 fields per class that carry a relationship, and labelled associations (a `file` has one `dentry` via `f_path`; a `dentry` has zero-or-one `inode`; an `inode` has one `address_space` via `i_mapping`; many `inode`s belong to one `super_block`). Caption: "The four VFS objects and the pointers that connect them — the diagram the rest of this folder refers back to."
- **Second visual:** a small `sequenceDiagram` of the deleted-but-open lifecycle: `open` → `unlink` (dentry gone, `i_nlink` 0, inode alive) → `read` still works → `close` → inode evicted, blocks freed.
- **KernelFacts:**
  - `structure` — `[["struct inode", "include/linux/fs.h"], ["struct dentry", "include/linux/dcache.h"]]`
  - `path` — `"fd → struct file → f_path.dentry → d_inode → i_sb (super_block)"`
  - `observe` — `ls -l /proc/$$/fd && stat -c '%i %h %n' /etc/hostname` (inode number and link count for a real file)
  - `trap` — "Deleting a file removes a name, not the data. A log file deleted while a process still holds it open keeps consuming disk space, invisibly to `du`, until that process closes it or exits — `lsof +L1` finds them."
- **References:**
  - `https://docs.kernel.org/filesystems/vfs.html` — the sections on `struct super_operations`, `struct inode_operations` and `struct file_operations`, member by member.
  - `<Src file="include/linux/dcache.h" symbol="dentry" />` — the dentry structure with its field comments.
  - Bovet & Cesati, *Understanding the Linux Kernel* (3rd ed.), ch. 12 — the most detailed long-form treatment of the object model; old (2.6-era) — use it for the relationships, not the field lists.
  - `https://man7.org/linux/man-pages/man2/unlink.2.html` — the user-visible contract for removing a name while the file stays open.

- [ ] **Step 1: Write `why-vfs-exists.md`** to the brief above, deleting the `:::info[Not yet written]` block. Run the WAH `strace` on a real machine and paste the real two lines.
- [ ] **Step 2: Write `the-four-objects.md`** to the brief above. Reproduce the deleted-but-open demonstration (`exec 3>/tmp/x; rm /tmp/x; ls -l /proc/$$/fd`) and use its real output.
- [ ] **Step 3: Verify every symbol** — `file_operations`, `file_system_type`, `ksys_read`, `vfs_read`, `read_iter`, `super_block`, `inode`, `dentry`, `file`, `address_space`, `i_mapping`, `i_nlink`, `f_path`, `anon_inode_getfile` — at `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>`. Check each field name against the struct definition in v6.18, not against a book.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`
Expected: zero findings and a green build.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write why the VFS exists and the four VFS objects"
```

---

## Task 5: Folder 11 — path lookup, and open/read/write

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/path-lookup-and-the-dcache.md`
- Modify: `docs/linux/11-vfs-and-filesystems/open-read-write-in-the-kernel.md`

**Interfaces:**
- Consumes: `11/the-four-objects` (Task 4), `09/rcu-in-practice`, `08/the-page-cache`.
- Produces:
  - `11/path-lookup-and-the-dcache`, a prerequisite of mounts and overlayfs;
  - `11/open-read-write-in-the-kernel`, a prerequisite of journaling, FUSE, the lab, and `12/the-block-layer-map`. **The full-path diagram on the second page is the handoff point between folders 11 and 12.**

### `path-lookup-and-the-dcache.md` — Path Lookup and the Dentry Cache **[WAH]** **[Misc]**

- **Opens with:** almost every file syscall starts with a string, and turning `/usr/lib/libc.so.6` into an inode is done millions of times a second on a busy machine. Path lookup is therefore one of the hottest paths in the kernel, and the dentry cache exists so that most lookups never touch a filesystem at all. The central trick — walking the path under RCU with no locks and no reference counts, and falling back only when that fails — is one of the clearest real uses of `../09-concurrency-and-locking/rcu-in-practice.md`.
- **Sections:**
  - `## Component by component` — the walk: start at the root or the cwd (or a directory fd for `openat`), split on `/`, look up each component in its parent, handle the final component specially (it may not exist yet for `O_CREAT`). `struct nameidata` as the walk's state. Name `path_openat`, `link_path_walk` and `walk_component`.
  - `## The dentry cache` — a hash table keyed on (parent dentry, name). A hit returns the child without calling the filesystem; a miss calls `i_op->lookup` and inserts the result. The dcache plus the inode cache are why the second `ls -R` of a tree is fast.
  - `## Negative dentries` — caching "this name does not exist". Why that is a feature: `PATH` searches and shared-library search paths probe many non-existent names, and every one would otherwise reach the filesystem. The cost: memory, reclaimed by the shrinker (link `../08-memory-management/reclaim-lru-and-kswapd.md`).
  - `## RCU-walk and ref-walk` — the fast mode walks without taking reference counts or locks, validating with sequence counts (link `../09-concurrency-and-locking/seqlocks.md`). If anything changes underneath or a filesystem needs to sleep, it attempts to switch to ref-walk in place (`try_to_unlazy` — verify the v6.18 name) and otherwise restarts. Say which cases force the fallback: a dcache miss, a symlink needing a filesystem call, a permission check that must sleep.
  - `## Mount points, symlinks, and `..`` — crossing into a mounted filesystem (`__follow_mount_rcu` or its v6.18 equivalent), following symlinks with a nesting limit (`ELOOP`), and why `..` at a mount root and in a chroot are special cases the walk handles explicitly. `openat2`'s `RESOLVE_BENEATH`/`RESOLVE_NO_SYMLINKS` as the modern answer to path-based attacks, in one paragraph.
  - `## What actually happens` **[WAH]** — `ls /usr/lib/x86_64-linux-gnu/libc.so.6` twice, the second time right after `echo 2 > /proc/sys/vm/drop_caches` (root). Show `perf stat -e 'syscalls:sys_enter_newfstatat'` or a simple `time` comparison, and explain that the difference is dcache and inode-cache hits versus filesystem lookups. Label the command as root-only and non-destructive. Then note that `drop_caches` is a debugging tool, not a tuning knob.
  - `## Misconceptions` **[Misc]** —
    1. "`drop_caches` frees memory the kernel was wasting." It discards cache that was about to make the next lookup fast.
    2. "A lot of negative dentries is a leak." Mostly, it is a cache doing its job, and reclaim trims it under pressure.
    3. "Path lookup reads directories from disk every time." It usually never reaches the filesystem.
- **Anchor:** a Mermaid `flowchart TB` of the lookup loop for one component: dcache lookup under RCU → hit (next component) / miss → try to leave RCU mode → `i_op->lookup` → insert into dcache → next component, with the "restart in ref-walk" edge drawn explicitly. Caption: "Resolving one path component: the RCU fast path, the filesystem slow path, and the fallback edge between them."
- **KernelFacts:**
  - `structure` — `[["struct nameidata", "fs/namei.c"], ["struct dentry", "include/linux/dcache.h"]]`
  - `path` — `"do_filp_open() → path_openat() → link_path_walk() → walk_component() → lookup_fast() / lookup_slow()"`
  - `observe` — `grep -E 'dentry|inode_cache' /proc/slabinfo` and `cat /proc/sys/fs/dentry-state` (verify the field meanings of `dentry-state` at v6.18 before explaining them)
  - `trap` — "RCU-walk is not a separate implementation that might disagree with ref-walk — it is the same walk attempted without references, and any doubt forces the careful version. A lookup that falls back is slower, never less correct."
- **References:**
  - `https://docs.kernel.org/filesystems/path-lookup.html` — Neil Brown's in-tree account of the whole walk, including RCU-walk; the best document on this topic.
  - LWN, *"Pathname lookup in Linux"* (`https://lwn.net/Articles/649115/`) and *"RCU-walk: faster pathname lookup in Linux"* (`https://lwn.net/Articles/649729/`) — the article versions, 2015; the design is current, some function names have since changed.
  - `<Src file="fs/namei.c" symbol="link_path_walk" />` — the walk itself.
  - `https://man7.org/linux/man-pages/man2/openat2.2.html` — the `RESOLVE_*` flags and why they exist.

### `open-read-write-in-the-kernel.md` — `open`, `read`, `write` in the Kernel **[WAH]** **[Misc]**

- **Opens with:** a file descriptor is not a handle to a file. It is a small integer index into a per-process table of pointers to `struct file`, and that one level of indirection explains `dup`, inherited descriptors across `fork`, shared file offsets, and `O_CLOEXEC`. This page follows the three most common file syscalls from that integer down to the filesystem and the page cache, and marks the exact point where `O_DIRECT` leaves the path.
- **Sections:**
  - `## What an fd is` — `files_struct` → `fdtable` → `struct file *[]`. Allocating the lowest free number, `fd_install`, and the close-on-exec bitmap. Show why `dup2(fd, 1)` redirects stdout: it changes which `struct file` slot 1 points at.
  - `## open()` — `do_sys_openat2` → `getname` → `do_filp_open` (path lookup, from `./path-lookup-and-the-dcache.md`) → permission checks → `f_op->open` → `fd_install`. Where `O_CREAT`, `O_TRUNC` and `O_EXCL` are acted on.
  - `## read()` — `ksys_read` → `vfs_read` → `f_op->read_iter` with a `struct kiocb` (position and flags) and a `struct iov_iter` (where the bytes go). For a regular file on a page-cache filesystem this reaches `filemap_read`, which copies from folios (link `../08-memory-management/the-page-cache.md` — do not re-teach readahead).
  - `## write()` — `vfs_write` → `f_op->write_iter` → for buffered writes `generic_perform_write`, which calls `a_ops->write_begin`/`write_end` around a copy into the page cache and marks folios dirty. The write returns once the bytes are in memory; writeback owns the rest (link `../08-memory-management/writeback-and-fsync.md`).
  - `## File position, sharing, and `O_APPEND`` — descriptors from `fork`/`dup` share `f_pos`, protected by `f_pos_lock` when a `struct file` is shared (`fdget_pos`). `O_APPEND` sets the position to end-of-file under the inode lock for each write, which makes concurrent appends from separate processes land whole on local filesystems — and state that this guarantee does not extend to NFS. `pread`/`pwrite` avoid the shared position entirely.
  - `## Where `O_DIRECT` leaves` — the `IOCB_DIRECT` flag sends `read_iter`/`write_iter` down the filesystem's direct-I/O path (commonly `iomap_dio_rw`), skipping the page cache and building block I/O straight from the user buffer. One paragraph and a link to `../12-block-layer-and-storage/buffered-direct-and-alignment.md`.
  - `## What actually happens` **[WAH]** — `echo hello > out.txt` in a shell. Trace it with `strace -f -e trace=openat,dup2,write,close bash -c 'echo hello > out.txt'`, and annotate each line: the shell opens with `O_WRONLY|O_CREAT|O_TRUNC`, `dup2`s onto fd 1, `echo` (a builtin) writes to fd 1 without knowing it is a file, and the data is in the page cache — not on disk — when the command returns.
  - `## Misconceptions` **[Misc]** —
    1. "A file descriptor is a pointer to the file." It is an index into a table of pointers, and two indexes can share one `struct file`.
    2. "`write()` returning means the data is on disk." It means the data is in the page cache.
    3. "`O_APPEND` makes all appends atomic everywhere." It does on local filesystems for writes that complete in one call; not on NFS, and not for a short write split by the caller.
- **Anchor:** a Mermaid `flowchart LR` — process fd table → `struct file` → `f_op->read_iter` → filesystem → page cache (hit: copy to user) / miss: `a_ops->read_folio` → block layer — with a separate, clearly styled `O_DIRECT` edge that skips the page cache. Caption: "The full buffered read path from a file descriptor to the block layer, and the direct-I/O branch that bypasses the cache."
- **Second visual:** a WaveDrom `reg` strip of the `open()` flag bits that matter, from `include/uapi/asm-generic/fcntl.h` on x86-64 (`O_WRONLY`, `O_RDWR`, `O_CREAT`, `O_EXCL`, `O_NOCTTY`, `O_TRUNC`, `O_APPEND`, `O_NONBLOCK`, `O_DSYNC`, `O_DIRECT`, `O_LARGEFILE`, `O_DIRECTORY`, `O_NOFOLLOW`, `O_CLOEXEC`). **The values are octal in the header — convert them to bit positions carefully and verify each at v6.18.** State that the numbering differs on some architectures. Caption: "Where each `open()` flag sits in the flags word on x86-64."
- **KernelFacts:**
  - `structure` — `[["struct files_struct", "include/linux/fdtable.h"], ["struct kiocb", "include/linux/fs.h"]]`
  - `path` — `"read() → ksys_read() → vfs_read() → f_op->read_iter() → filemap_read() → copy_folio_to_iter()"`
  - `observe` — `strace -f -e trace=openat,dup2,write bash -c 'echo hello > out.txt'`
  - `trap` — "Two descriptors can share one file offset without either program knowing — a parent and child writing to an inherited log descriptor advance the same `f_pos`. Unexpected interleaving in a shared log is usually this, not a filesystem bug."
- **References:**
  - `<Src file="fs/read_write.c" symbol="vfs_read" />` — the dispatch point, short enough to read in full.
  - `<Src file="mm/filemap.c" symbol="filemap_read" />` — where a buffered read meets the page cache.
  - `https://man7.org/linux/man-pages/man2/open.2.html` — every flag's contract, including the `O_APPEND` and NFS caveat and the `O_DIRECT` notes.
  - LWN, *"The iov_iter interface"* (`https://lwn.net/Articles/625077/`) — why read and write take an iterator rather than a pointer; 2014, and the interface has since grown.

- [ ] **Step 1: Write `path-lookup-and-the-dcache.md`** to the brief above. Run the WAH comparison on a real machine you are allowed to drop caches on, and paste the real timings.
- [ ] **Step 2: Write `open-read-write-in-the-kernel.md`** to the brief above. Paste the real `strace` output of the WAH example.
- [ ] **Step 3: Verify every symbol** — `nameidata`, `path_openat`, `link_path_walk`, `walk_component`, `lookup_fast`, `lookup_slow`, `try_to_unlazy`, `__follow_mount_rcu`, `do_filp_open`, `files_struct`, `fdtable`, `fd_install`, `do_sys_openat2`, `ksys_read`, `vfs_write`, `filemap_read`, `generic_perform_write`, `f_pos_lock`, `fdget_pos`, `IOCB_DIRECT`, `iomap_dio_rw`, `copy_folio_to_iter` — and every `open()` flag value. Correct the page to whatever v6.18 actually has.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`
Expected: zero findings and a green build.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write path lookup and the kernel read/write path"
```

---

## Task 6: Folder 11 — mounts, tmpfs, and the pseudo-filesystems

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/mounts-and-mount-namespaces.md`
- Modify: `docs/linux/11-vfs-and-filesystems/tmpfs-and-memory-filesystems.md`
- Modify: `docs/linux/11-vfs-and-filesystems/procfs-sysfs-debugfs-configfs.md`

**Interfaces:**
- Consumes: `11/the-four-objects`, `11/path-lookup-and-the-dcache` (Tasks 4–5), `08/the-page-cache`, `04/kobjects-sysfs-and-the-object-model`.
- Produces: `11/mounts-and-mount-namespaces`, a prerequisite of `11/overlayfs`. Its propagation material is what the containers folder will build on in Phase 4 — **name that folder in prose only; do not link it.**

### `mounts-and-mount-namespaces.md` — Mounts and Mount Namespaces **[WAH]** **[Misc]** **[Lab host=root-required]**

- **Opens with:** the directory tree you see is not the tree on any disk. It is a composition: many filesystem trees grafted onto each other at mount points, recorded in a separate mount tree the kernel consults during path lookup. Separate that mount tree from the directory tree and bind mounts, mount namespaces, and why a container sees a different `/` all become the same idea.
- **Sections:**
  - `## The mount tree` — `struct mount` (kernel-internal, `fs/mount.h`) embedding the public `struct vfsmount`: which superblock, which dentry is the root of this mount, and where it is attached (parent mount plus mountpoint dentry). One superblock can have many mounts.
  - `## Bind mounts` — a second mount of an existing subtree, sharing the superblock. What they are good for, and that a bind mount is not a symlink: it survives `chroot`, has no target string, and can carry different flags (`ro` on a bind of a writable mount).
  - `## Mount propagation` — the problem it solves (a mount in one place should or should not appear in its copies) and the four types: shared, slave, private, unbindable. Peer groups, and what `mount --make-rshared /` does. **Anchor** here.
  - `## Mount namespaces` — `CLONE_NEWNS` copies the mount tree; propagation settings decide what flows between the copies afterwards. Explain why systemd makes `/` shared by default and why container runtimes then make their root `rslave` or private. Name the containers folder in prose, unlinked.
  - `## The new mount API` — `fsopen`, `fsconfig`, `fsmount`, `move_mount`, `open_tree` and `mount_setattr` (idmapped mounts) replacing the single overloaded `mount(2)`. One section, stating the kernel version each arrived in (verify).
  - `## What actually happens` **[WAH]** — `mount /dev/sdb1 /mnt`. The block device is opened, the filesystem type's `init_fs_context`/`get_tree` builds or reuses a superblock, a new `struct mount` is created, and it is attached at `/mnt`'s dentry in the caller's mount namespace. `/mnt`'s old contents are hidden, not deleted — they reappear on `umount`. Then read the new line out of `/proc/self/mountinfo` field by field.
  - `<Lab host="root-required" title="See propagation happen" time="15 min">` —
    1. `sudo unshare --mount --propagation unchanged bash`, then `findmnt -o TARGET,PROPAGATION /`;
    2. in a second terminal, mount a tmpfs at `/mnt/p` and observe whether it appears in the namespace;
    3. repeat with `--propagation private`;
    4. `mount --bind` a directory read-only and show that writes fail through the bind but succeed through the original.

    Show the real `findmnt` and `mountinfo` output for each. "If it fails": `unshare` defaults to `--propagation private`, so step 1 must pass `unchanged`, and `/mnt/p` must exist before mounting.
  - `## Misconceptions` **[Misc]** —
    1. "A bind mount is a kind of symlink." It is a second mount of the same subtree, with no path string to resolve.
    2. "Mounting over a directory deletes what was there." It hides it until unmount.
    3. "A new mount namespace is isolated from the host's mounts." Only if propagation says so — a namespace cloned from a shared `/` keeps receiving host mounts.
- **Anchor:** a Mermaid `flowchart LR` of two mount namespaces with a shared peer group and a slave. A mount event on the host propagates into both; a mount inside the slave propagates nowhere. Edges are labelled with the propagation type. Caption: "The same mount event under shared, slave, and private propagation — which copies of the tree see it and which do not."
- **KernelFacts:**
  - `structure` — `[["struct mount", "fs/mount.h"], ["struct vfsmount", "include/linux/mount.h"]]`
  - `path` — `"mount() → path_mount() → do_new_mount() → vfs_get_tree() → do_add_mount() → propagate_mnt()"`
  - `observe` — `findmnt -o TARGET,SOURCE,FSTYPE,PROPAGATION` and `cat /proc/self/mountinfo`
  - `trap` — "`unshare --mount` does not stop mounts from leaking if `/` was shared when the namespace was cloned — propagation, not the namespace itself, decides isolation. Container runtimes set it explicitly for exactly this reason."
- **References:**
  - `https://docs.kernel.org/filesystems/sharedsubtree.html` — the shared-subtree design document, with the propagation semantics worked through.
  - `https://man7.org/linux/man-pages/man7/mount_namespaces.7.html` — the authoritative user-visible description of namespaces and propagation.
  - LWN, *"Mount namespaces and shared subtrees"* (`https://lwn.net/Articles/689856/`) — Kerrisk's article series, 2016; semantics unchanged, the new mount API postdates it.
  - `https://man7.org/linux/man-pages/man5/proc_pid_mountinfo.5.html` — every `mountinfo` field defined (verify the page name; older man-pages put this in `proc(5)`).

### `tmpfs-and-memory-filesystems.md` — tmpfs and Memory-Backed Filesystems **[Misc]**

- **Opens with:** tmpfs is what you get when a filesystem has a page cache and no disk under it. File data lives in folios that belong to the page cache like any other, except that the cache is the only copy. That is why tmpfs is fast, why its contents vanish on reboot, and — the part people miss — why it can be swapped out.
- **Sections:**
  - `## Page cache with no backing store` — tmpfs inodes and their `address_space` are real; writes dirty folios that have nowhere to be written back to. Under memory pressure those folios go to *swap* rather than being dropped (link `../08-memory-management/swap-and-zswap.md`). The implementation is `mm/shmem.c`, which is why tmpfs and shared memory are one subsystem.
  - `## Size limits and accounting` — `size=` (default half of RAM), `nr_inodes=`, and the fact that tmpfs usage shows up as `Shmem` in `/proc/meminfo` and is charged to the memory cgroup of whoever wrote it. A full tmpfs is memory pressure, not a full disk.
  - `## Where it is used` — **table**: `/tmp` (on distributions that mount it), `/dev/shm` (POSIX shared memory), `/run`, `memfd_create` (anonymous tmpfs files), and SysV shared memory — each with who creates it and what it is for.
  - `## ramfs: the version with no limits` — no size limit and no swap. A process that writes to ramfs until memory is exhausted takes the machine with it. It still exists as the minimal example of a page-cache filesystem and underneath early `rootfs`; link `../03-boot-and-init/initramfs-and-early-userspace.md`.
  - `## Options worth knowing` — `huge=` for transparent huge pages on tmpfs (link `../08-memory-management/hugepages-and-thp.md`), `noswap` and quota support (state the kernel version each was added in; verify), `mode=`/`uid=`.
  - `## Misconceptions` **[Misc]** —
    1. "tmpfs is always in RAM." It can be swapped, and an idle tmpfs file may be on the swap device.
    2. "tmpfs uses memory only for what you store, so a big `size=` is free." `size=` is a limit, not a reservation — but the data you *do* store is unevictable except to swap.
    3. "`free` shows tmpfs usage as used memory." It shows it under `shared` and `buff/cache`, which is why "cache" that will not shrink is often tmpfs.
- **Anchor:** a comparison **table** — tmpfs, ramfs, a disk-backed filesystem, and `/dev/shm` — across backing store, size limit, swappable, counted as, survives reboot. Plus a Mermaid `flowchart LR` showing a tmpfs folio's two possible fates under memory pressure (stay, or go to swap), contrasted with an ext4 folio's (write back and drop). Caption: "Why a tmpfs page and an ext4 page behave differently under memory pressure: one has a disk to return to, the other only has swap."
- **KernelFacts:**
  - `structure` — `[["struct shmem_inode_info", "include/linux/shmem_fs.h"]]`
  - `path` — `"write() → shmem_file_write_iter() → generic_perform_write() → shmem_write_begin() → shmem_get_folio()"` (verify each name; the shmem write path has been folio-converted)
  - `observe` — `df -h -t tmpfs && grep -E '^(Shmem|ShmemHugePages):' /proc/meminfo`
  - `trap` — "Filling `/dev/shm` or a tmpfs `/tmp` does not fill a disk — it consumes memory that reclaim cannot free except by swapping, and on a machine without swap it drives the system toward the OOM killer."
- **References:**
  - `https://docs.kernel.org/filesystems/tmpfs.html` — every mount option, with the version notes this page cites.
  - `<Src file="mm/shmem.c" />` — the implementation shared by tmpfs, `memfd` and SysV shared memory.
  - `https://man7.org/linux/man-pages/man2/memfd_create.2.html` — anonymous tmpfs files, and the sealing API built on them.
  - `https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html` — ramfs, rootfs and why initramfs uses them.

### `procfs-sysfs-debugfs-configfs.md` — procfs, sysfs, debugfs, configfs **[WAH]** **[Misc]**

- **Opens with:** four pseudo-filesystems, four different promises. `/proc` began as the process interface and accumulated everything; `/sys` is generated from the device model with a strict one-value-per-file rule; `/sys/kernel/debug` makes no stability promise at all; `/sys/kernel/config` lets user space *create* kernel objects with `mkdir`. Knowing which contract a file lives under tells you whether a script that reads it will still work next year.
- **Sections:**
  - `## procfs` — process directories (link `../06-processes-and-threads/proc-as-the-process-interface.md` — do not re-teach them), plus legacy system-wide files (`meminfo`, `interrupts`, `mounts`) and `/proc/sys` as the sysctl tree. `seq_file` as the producer for most of it, and why reading a large `/proc` file in small chunks can see an inconsistent snapshot.
  - `## sysfs` — built on kernfs, generated from the kobject hierarchy (link `../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md`). One value per file; attributes defined with `DEVICE_ATTR_RO`/`_RW` and formatted with `sysfs_emit`. The ABI is documented in `Documentation/ABI/`.
  - `## debugfs` — anything goes, for developers. No ABI, often root-only, and restricted or disabled by kernel lockdown. The rule: a production tool that depends on debugfs is depending on an accident.
  - `## configfs` — the inverse of sysfs: user space `mkdir`s a directory and a kernel object is created; writes to its attributes configure it. Real users: USB gadget configuration, the LIO iSCSI/SCSI target, nvmet (the NVMe-oF target).
  - `## The ABI contract` — **table**: the four filesystems × stability promise, where the ABI is documented (`Documentation/ABI/stable`, `testing`, `obsolete`, `removed`), who may create entries, and the right use when writing a driver. Name the drivers folder in prose (unlinked) as where the "which interface should my driver expose" decision is made in full.
  - `## What actually happens` **[WAH]** — `cat /sys/class/net/lo/mtu` versus `cat /proc/net/dev`. The first calls one `show()` callback that emits one number via `sysfs_emit`; the second iterates every interface through a `seq_file` iterator. Use `strace` to show the different read sizes, and show the `Documentation/ABI` entry for the sysfs file (or note its absence).
  - `## Misconceptions` **[Misc]** —
    1. "Everything under `/proc` and `/sys` is a stable API." Only what `Documentation/ABI/stable` lists; debugfs promises nothing.
    2. "Writing to `/proc/sys` is permanent." It lasts until reboot unless `sysctl.d` reapplies it.
    3. "sysfs files are regular files with a size." They report a size of 4096 and generate their contents on read, which is why `cp` and `tail -f` misbehave on them.
- **Anchor:** the ABI contract **table** above, plus a Mermaid `flowchart TB` from a kernel object (kobject / seq_file iterator / debugfs_create_* / configfs subsystem) to the file a user reads, one lane per filesystem. Caption: "Four ways kernel state becomes a file, and the stability promise attached to each."
- **KernelFacts:**
  - `structure` — `[["struct seq_operations", "include/linux/seq_file.h"], ["struct kernfs_node", "include/linux/kernfs.h"]]`
  - `path` — `"read(/sys/...) → kernfs_fop_read_iter() → sysfs_kf_seq_show() → dev_attr_show() → driver show() → sysfs_emit()"`
  - `observe` — `ls /sys/kernel/debug 2>&1 | head -3; ls Documentation/ABI/stable | head` (the second in a kernel tree)
  - `trap` — "A debugfs file that has existed for ten years is still not an interface. Tools that parse it break without notice, and on a lockdown-enabled kernel they fail outright."
- **References:**
  - `https://docs.kernel.org/filesystems/sysfs.html` — the sysfs rules, including one-value-per-file.
  - `https://docs.kernel.org/filesystems/proc.html` — the `/proc` reference, long and authoritative.
  - `https://docs.kernel.org/admin-guide/abi.html` — the rendered `Documentation/ABI` tree, and how to tell stable from testing.
  - `https://docs.kernel.org/filesystems/configfs.html` — configfs's model and a worked example.
  - `https://docs.kernel.org/filesystems/seq_file.html` — the iterator behind most of `/proc`.

- [ ] **Step 1: Run the mounts lab** as a real user with `sudo` on a real Linux host (not WSL2, whose mount setup differs), and record the real `findmnt`/`mountinfo` output of every step. Note which of the "if it fails" causes you actually hit.
- [ ] **Step 2: Write `mounts-and-mount-namespaces.md`** to the brief above, using the recorded output.
- [ ] **Step 3: Write `tmpfs-and-memory-filesystems.md`** to the brief above.
- [ ] **Step 4: Write `procfs-sysfs-debugfs-configfs.md`** to the brief above. Run the WAH comparison and paste the real `strace` output.
- [ ] **Step 5: Verify every symbol and version claim** — `struct mount`, `vfsmount`, `path_mount`, `do_new_mount`, `vfs_get_tree`, `do_add_mount`, `propagate_mnt`, `fsopen`, `mount_setattr`, `shmem_inode_info`, `shmem_file_write_iter`, `shmem_write_begin`, `shmem_get_folio`, `seq_operations`, `kernfs_node`, `kernfs_fop_read_iter`, `sysfs_kf_seq_show`, `dev_attr_show`, `sysfs_emit`, `DEVICE_ATTR_RO`, `debugfs_create_file`, `configfs_register_subsystem` — plus the kernel versions stated for the new mount API, tmpfs `noswap`, and tmpfs quotas.
- [ ] **Step 6: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 7: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write mounts, tmpfs, and the pseudo-filesystems"
```

---

## Task 7: Folder 11 — journaling, ext4, and XFS/Btrfs

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/journaling-and-crash-consistency.md`
- Modify: `docs/linux/11-vfs-and-filesystems/ext4.md`
- Modify: `docs/linux/11-vfs-and-filesystems/xfs-and-btrfs.md`

**Interfaces:**
- Consumes:
  - `11/open-read-write-in-the-kernel` (Task 5);
  - `08/writeback-and-fsync`;
  - `computer-science/storage/crash-consistency-and-journaling` (Task 2) — **the theory is owned there; this page links it and never re-derives the partial-write table.**
- Produces:
  - `11/journaling-and-crash-consistency`, a prerequisite of `11/ext4` — **write it first in this task**;
  - `11/ext4`, a prerequisite of `11/xfs-and-btrfs`.

### `journaling-and-crash-consistency.md` — Journaling and Crash Consistency **[WAH]** **[Misc]**

- **Opens with:** the CS backfill page explains why a crash can corrupt a disk and what the four families of fix are. This page is the Linux-specific answer to a narrower, more practical question: when an application calls `write`, `fsync`, and `rename` on a Linux filesystem, what does it actually get after a power cut? The honest answer depends on the filesystem, its mount options, the device, and how carefully the application asked.
- **Sections:**
  - `## What a Linux filesystem promises` — metadata consistency after a crash (the filesystem mounts and its structures agree), not data durability for anything not explicitly flushed. Link `../../computer-science/storage/crash-consistency-and-journaling.md` for why those are different.
  - `## jbd2: the journal ext4 uses` — handles, transactions and commits: many operations batch into one running transaction, which commits on a timer (ext4's `commit=` defaults to 5 seconds), on `fsync`, or when the journal fills. `jbd2_journal_commit_transaction` and the `jbd2/sdX-8` kernel thread visible in `ps`.
  - `## Data modes` — `data=ordered` (the default: data written before the metadata that references it commits), `data=writeback` (metadata only — stale data can appear in files after a crash), `data=journal` (everything through the journal). A **table** of what each guarantees after a crash.
  - `## Barriers, flush, and FUA` — the filesystem issues flushes at commit (`REQ_PREFLUSH`, and `REQ_FUA` for the commit block where supported) so the device's volatile cache cannot reorder a commit ahead of its contents. `blkdev_issue_flush`. The (long-gone) `nobarrier` option and why disabling barriers was the classic "fast until the power fails" setting. Link `../12-block-layer-and-storage/the-bio.md` for how a flush is represented.
  - `## fsync errors, and the 2018 lesson` — when writeback fails, the error is reported to `fsync` once. Historically, a failed page could be marked clean and a retried `fsync` would *succeed* without the data having been written. PostgreSQL discovered this in 2018. `errseq_t` now records errors per file so every descriptor open at the time sees them, but the data in those pages is still gone: the only safe response to an `fsync` error is to treat the write as lost.
  - `## The replace-by-rename recipe on Linux` — the four-step durable replace (write temp, `fsync` temp, `rename`, `fsync` directory), and ext4's `auto_da_alloc` heuristic that partially rescues applications that skip step two. Say why relying on the heuristic is wrong.
  - `## What actually happens` **[WAH]** — a text editor saving a file. Show `strace -e trace=openat,write,fsync,fdatasync,rename` of a real editor's save (vim or nano). Annotate which steps of the recipe it performs, then explain what would be on disk if the power failed between each pair of calls under `data=ordered`.
  - `## Misconceptions` **[Misc]** —
    1. "A journaling filesystem protects my data." It protects its own metadata; your data is protected by your `fsync`s.
    2. "If `fsync` fails I can retry it." A retry can report success without the data ever being written; treat it as lost.
    3. "`fsync` on the file is enough for a new file." The directory entry needs its own `fsync`.
- **Anchor:** a Mermaid `sequenceDiagram` — Application, VFS/page cache, ext4, jbd2, Device — for the four-step replace, showing when each piece reaches the journal and when the flushes happen, with `Note` markers for the crash windows that lose the new contents versus the ones that keep the old file intact. Caption: "A durable file replace on ext4, step by step, with what survives a crash at each point."
- **KernelFacts:**
  - `structure` — `[["journal_t", "include/linux/jbd2.h"], ["errseq_t", "include/linux/errseq.h"]]`
  - `path` — `"fsync() → vfs_fsync_range() → ext4_sync_file() → jbd2_complete_transaction() → blkdev_issue_flush()"`
  - `observe` — `ps -eo comm | grep '^jbd2' && findmnt -no OPTIONS /` (the journal thread, and whether `data=` or `commit=` differ from the defaults)
  - `trap` — "`fsync` returning an error does not mean 'try again'. On Linux the pages that failed may already be marked clean, so the data is gone from memory as well as from disk — the only correct response is to treat the write as lost and recover from your own log."
- **References:**
  - `https://docs.kernel.org/filesystems/ext4/journal.html` — the ext4 journal's on-disk format and modes (verify the page path; the ext4 docs were restructured).
  - LWN, *"PostgreSQL's fsync() surprise"* (`https://lwn.net/Articles/752063/`) — the 2018 episode, and the kernel changes that followed.
  - LWN, *"Improved block-layer error handling"* or the `errseq_t` introduction (`https://lwn.net/Articles/724307/`) — how per-file error tracking works; 2017.
  - Pillai et al., OSDI 2014 — cite it again here for the measured behaviour of real applications on ext4, with a link to the CS page for the full discussion.

### `ext4.md` — ext4 **[Lab host=any-linux]**

- **Opens with:** ext4 is the conservative default — an evolution of ext2 and ext3 that kept a fixed on-disk layout and added extents, a journal, and delayed allocation without ever breaking the ability to mount old filesystems. Read from the on-disk layout upward, it is the clearest real example of every structure this folder has described so far.
- **Sections:**
  - `## The layout: block groups` — the disk divided into block groups, each with (optionally) a superblock backup, group descriptors, block and inode bitmaps, and an inode table. `flex_bg` packing metadata together. Draw the **anchor** here.
  - `## Inodes and the extent tree` — the 60-byte `i_block` area holding an extent header and up to four extents, or index entries for a deeper tree. An extent is (logical block, length, physical block). Why extents replaced indirect blocks: a contiguous 1 GB file is one extent instead of a quarter-million block pointers. **Second visual** here.
  - `## Directories and htree` — linear directory blocks for small directories, and a hashed B-tree (`dx_root`) once a directory grows, making lookup in a directory with a million entries a few block reads.
  - `## Delayed allocation` — blocks are not chosen at `write` time but at writeback, when the kernel knows how much data there is. Better contiguity and fewer allocations; the cost is the crash-window behaviour the journaling page describes.
  - `## The journal, and fast commits` — jbd2 as covered on `./journaling-and-crash-consistency.md` (link, don't repeat), plus fast commits as a lighter-weight log for common operations.
  - `## Features worth knowing` — `metadata_csum`, `64bit`, `huge_file`, `casefold`, `encrypt`, `verity`, and `inline_data`. A **table** of each feature and what it changes, read off `dumpe2fs -h`.
  - `<Lab host="any-linux" title="Read ext4's on-disk structures" time="20 min">` — no root needed: `truncate -s 256M e.img && mkfs.ext4 -F e.img`; `dumpe2fs -h e.img` (features, block size, groups); `dumpe2fs e.img | head -40` (the first group's layout); `debugfs -w e.img` then `write /etc/services services`, `stat services` (see `EXTENTS: (0-N):...`), `ls -l /`, `htree /` on a directory after creating a few thousand entries with `mkdir` inside debugfs. Show the real output for each step. "If it fails": `debugfs` and `dumpe2fs` ship in `e2fsprogs`; `htree` shows nothing until the directory is large enough to be indexed.
- **Anchor:** a WaveDrom `reg` strip or a Mermaid block diagram of one flex group's on-disk layout: superblock, group descriptors, reserved GDT blocks, bitmaps, inode table, data blocks — with sizes in blocks taken **from the lab's own `dumpe2fs` output**, not invented. Caption: "The first block group of a real 256 MB ext4 image, laid out from `dumpe2fs`."
- **Second visual:** a WaveDrom `reg` strip of `struct ext4_extent_header` (magic `0xF30A`, entries, max, depth, generation) and `struct ext4_extent` (logical block, length, physical high, physical low). Caption: "The twelve bytes that describe an extent, and the header that says how many follow."
- **KernelFacts:**
  - `structure` — `[["struct ext4_extent_header", "fs/ext4/ext4_extents.h"], ["struct ext4_inode", "fs/ext4/ext4.h"]]`
  - `path` — `"writeback → ext4_writepages() → ext4_map_blocks() → ext4_ext_map_blocks() → ext4_mb_new_blocks()"`
  - `observe` — `sudo dumpe2fs -h /dev/<root-device> | grep -E 'features|Block size|Journal'` (read-only; or use the lab image)
  - `trap` — "Delayed allocation means a file's blocks do not exist on disk until writeback runs. `du` on a just-written file can report less than its size, and a crash before writeback leaves a zero-length file — which is why the replace-by-rename recipe includes an `fsync`."
- **References:**
  - `https://docs.kernel.org/filesystems/ext4/index.html` — the ext4 data-structures documentation: block groups, extents, directories, with byte offsets.
  - `https://man7.org/linux/man-pages/man8/debugfs.8.html` and `man 8 dumpe2fs` — the tools this page's lab uses.
  - Mathur et al., *"The new ext4 filesystem: current status and future plans"*, Ottawa Linux Symposium 2007 — the design rationale for extents and delayed allocation; old, and the feature set has grown since.
  - LWN, *"Fast commits for ext4"* (`https://lwn.net/Articles/842385/`) — the fast-commit design, 2021.

### `xfs-and-btrfs.md` — XFS and Btrfs

- **Opens with:** XFS and Btrfs are two different bets on what matters. XFS bet on parallelism and scale: split the filesystem into independent allocation groups, index everything with B+ trees, and let many threads allocate at once. Btrfs bet on never overwriting data: copy-on-write B-trees give snapshots, checksums and cheap clones as structural consequences rather than add-on features. Neither is "better than ext4"; each is right for different workloads, and this page states which without advocacy.
- **Sections:**
  - `## XFS: allocation groups and B+ trees` — allocation groups as independently locked regions (`struct xfs_perag`), free space tracked in two B+ trees (by block and by size), dynamically allocated inodes, delayed logging. Why XFS scales to large files and many concurrent writers, and its reflink support.
  - `## Btrfs: copy-on-write B-trees` — every change writes new tree nodes up to a new root; the superblock pointer swap is the commit. What falls out of that: snapshots and subvolumes (share unchanged tree nodes), checksums on data and metadata, reflink copies, and send/receive.
  - `## Btrfs's multi-device modes, honestly` — `single`, `dup`, `raid1`, `raid1c3/4`, `raid10` are mature; `raid5`/`raid6` carry warnings in the Btrfs project's own status documentation. **Check the current status page before writing, cite it, and state exactly what it says at the time of writing** — do not repeat community folklore in either direction.
  - `## Costs` — Btrfs: fragmentation under random overwrites (databases, VM images — `nodatacow` and its loss of checksums), metadata space exhaustion as a distinct failure mode, balance as maintenance. XFS: cannot shrink, and repair on very large filesystems needs memory.
  - `## Choosing` — `<Tabs>` with three tabs: **ext4** (general-purpose default, simplest recovery story), **XFS** (large files, parallel writers, the RHEL default), **Btrfs** (snapshots, checksums, send/receive, the Fedora and openSUSE default) — each tab with its strengths, its costs, and the workloads it fits.
  - Name ZFS in one paragraph: out of tree on Linux for licensing reasons, the same copy-on-write bet as Btrfs, and not covered further here.
- **Anchor:** a comparison **table** — ext4, XFS, Btrfs — across on-disk model, data checksums, snapshots, shrink, reflink, max-scale design point, multi-device support, and default distributions. Plus a Mermaid `flowchart TB` of a Btrfs CoW update: changing one leaf writes a new leaf, a new parent and a new root, while the old root still describes the old tree (the snapshot). Caption: "Changing one block in a copy-on-write tree: new nodes all the way up, and the old root still intact — which is all a snapshot is."
- **KernelFacts:**
  - `structure` — `[["struct xfs_perag", "fs/xfs/libxfs/xfs_ag.h"], ["struct btrfs_root", "fs/btrfs/ctree.h"]]`
  - `path` — `"Btrfs write → btrfs_cow_block() → new node → btrfs_commit_transaction() → superblock root update"`
  - `observe` — `sudo xfs_info /mountpoint` or `sudo btrfs filesystem usage /mountpoint` (whichever is present)
  - `trap` — "Btrfs 'free space' is two separate pools — data and metadata — and a filesystem can report gigabytes free while failing writes with `ENOSPC` because metadata is exhausted. `btrfs filesystem usage` shows both; `df` does not."
- **References:**
  - `https://docs.kernel.org/filesystems/xfs/index.html` — the in-tree XFS documentation, including the delayed-logging design (verify the path at v6.18).
  - `https://btrfs.readthedocs.io/en/latest/Status.html` — the Btrfs project's own feature-stability table; **the source for every stability claim on this page**, cited with the date checked.
  - Rodeh, Bacik & Mason, *"BTRFS: The Linux B-Tree Filesystem"*, ACM TOS 2013 — the design paper behind the copy-on-write model.
  - LWN, *"XFS: the filesystem of the future?"* (`https://lwn.net/Articles/476263/`) — Dave Chinner's 2012 talk write-up on XFS's scalability work; old, but the architecture is unchanged.

- [ ] **Step 1: Write `journaling-and-crash-consistency.md` first**, to the brief above. Run the WAH editor `strace` for real and paste its output.
- [ ] **Step 2: Run the ext4 lab** end to end on any Linux host and record every command's real output, including the `dumpe2fs` numbers the anchor diagram is built from.
- [ ] **Step 3: Write `ext4.md`** to the brief above, using the recorded numbers.
- [ ] **Step 4: Check the Btrfs status page** and note its date and exact wording for RAID5/6.
- [ ] **Step 5: Write `xfs-and-btrfs.md`** to the brief above.
- [ ] **Step 6: Verify every symbol and default** — `jbd2_journal_commit_transaction`, `journal_t`, `errseq_t`, `vfs_fsync_range`, `ext4_sync_file`, `jbd2_complete_transaction`, `blkdev_issue_flush`, `REQ_PREFLUSH`, `REQ_FUA`, `ext4_extent_header`, `ext4_extent`, `ext4_inode`, `ext4_writepages`, `ext4_map_blocks`, `ext4_ext_map_blocks`, `ext4_mb_new_blocks`, `dx_root`, `xfs_perag`, `btrfs_root`, `btrfs_cow_block`, `btrfs_commit_transaction` — plus ext4's `commit=` default and whether `auto_da_alloc` is still an ext4 mount option at v6.18.
- [ ] **Step 7: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 8: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write journaling, ext4, and XFS and Btrfs"
```

---

## Task 8: Folder 11 — overlayfs and FUSE

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/overlayfs.md`
- Modify: `docs/linux/11-vfs-and-filesystems/fuse-and-userspace-filesystems.md`

**Interfaces:**
- Consumes: `11/mounts-and-mount-namespaces` (Task 6), `11/path-lookup-and-the-dcache` and `11/open-read-write-in-the-kernel` (Task 5).
- Produces: `11/overlayfs`, which the Phase 4 containers folder will build on for image layers — **name that folder in prose only**. It is also the link target for the copy-up mention in `02/the-life-of-a-container` (Task 21).

### `overlayfs.md` — overlayfs **[Misc]** **[Lab host=root-required]**

- **Opens with:** overlayfs presents one directory tree made from several: read-only lower layers stacked under a writable upper layer. Reads fall through to whichever layer has the file; writes always land in the upper layer, copying a file up from below on its first modification. Nothing in a lower layer ever changes, which is exactly the property a container image needs — many containers share one set of read-only layers, each with its own thin writable layer on top.
- **Sections:**
  - `## Lower, upper, work, merged` — the four directories and what each is for. `workdir` must be on the same filesystem as `upperdir`, because copy-up and whiteout creation are staged there and then renamed into place atomically.
  - `## Lookup through layers` — the merged dentry records which layer each name came from; directories present in several layers are merged; the topmost regular file wins. `ovl_lookup`.
  - `## Copy-up` — the first open-for-write (or metadata change) of a lower file copies the **whole file** into the upper layer before the write proceeds. Consequences: a one-byte change to a 2 GB file copies 2 GB; the first write is slow; and a descriptor opened read-only *before* the copy-up keeps reading the lower file. `metacopy=on` for metadata-only changes, in one paragraph.
  - `## Deletion: whiteouts and opaque directories` — removing a lower file creates a whiteout (a character device with device number 0/0) in the upper layer; replacing a whole directory marks the new one opaque with an xattr (`trusted.overlay.opaque`, or the `user.overlay.*` namespace under `userxattr`). This is why deleting a file in a container layer never frees space in the image.
  - `## Where you meet it` — container image layers (named in prose), live-CD and immutable-root systems, and unprivileged overlay mounts inside a user namespace (state the version; verify).
  - `<Lab host="root-required" title="Build an overlay and watch copy-up" time="15 min">` —
    1. make `lower/`, `upper/`, `work/`, `merged/`, put `big.bin` (50 MB from `/dev/urandom`) and `a.txt` in `lower`;
    2. `sudo mount -t overlay overlay -o lowerdir=lower,upperdir=upper,workdir=work merged`;
    3. `ls upper` (empty), `time sh -c 'echo x >> merged/big.bin'`, `ls -l upper` (the whole file is now there);
    4. `rm merged/a.txt`, then `ls -l upper` showing `c--------- 0, 0 a.txt`;
    5. `umount` and show `lower` unchanged.

    Real output for every step. "If it fails": `workdir` on a different filesystem from `upperdir` is rejected at mount time; some filesystems (older tmpfs without xattr support, NFS) cannot be the upper layer.
  - `## Misconceptions` **[Misc]** —
    1. "Changing a file in a container copies only the changed blocks." Copy-up copies the whole file.
    2. "Deleting a file in a layer frees space." It adds a whiteout; the lower data remains.
    3. "overlayfs is a container technology." It is a general filesystem that containers happen to use.
- **Anchor:** a Mermaid `flowchart TB` of three layers — upper (writable), lower-1 and lower-2 (read-only) — above a merged view, showing one file read from lower-2, one file copied up and modified, and one file hidden by a whiteout, with the lookup direction drawn top-down. Caption: "How one merged directory is assembled from three layers: a file read through, a file copied up, and a file whited out."
- **KernelFacts:**
  - `structure` — `[["struct ovl_entry", "fs/overlayfs/ovl_entry.h"], ["struct ovl_fs", "fs/overlayfs/ovl_entry.h"]]`
  - `path` — `"open(O_WRONLY) on merged → ovl_open() → ovl_maybe_copy_up() → ovl_copy_up_flags() → write lands in upper"`
  - `observe` — `findmnt -t overlay -o TARGET,OPTIONS` (on a host running containers, shows every layer stack)
  - `trap` — "A read-only file descriptor opened before copy-up keeps pointing at the lower file. After another process modifies the file through the merged view, the two descriptors see different contents — a real source of confusing log-tailing and config-reload bugs."
- **References:**
  - `https://docs.kernel.org/filesystems/overlayfs.html` — the full semantics: copy-up, whiteouts, `metacopy`, `redirect_dir`, and the non-standard behaviours listed explicitly.
  - `<Src file="fs/overlayfs/copy_up.c" />` — the copy-up implementation.
  - LWN, *"Overlayfs"* coverage around its 2014 mainline merge (`https://lwn.net/Articles/447650/`, the earlier "Another union filesystem approach") — history of why unions took so long; the mechanism has grown since.
  - The OCI Image Format specification, "Image Layer Filesystem Changeset" (`https://github.com/opencontainers/image-spec/blob/main/layer.md`) — how a whiteout is represented in an image tarball versus on disk.

### `fuse-and-userspace-filesystems.md` — FUSE

- **Opens with:** FUSE moves a filesystem's logic out of the kernel into an ordinary process. The kernel side is a small VFS filesystem that turns each operation into a message on `/dev/fuse` and waits for a daemon to answer. That buys safety and easy development — a crash kills a process, not the machine, and any language works — and it costs boundary crossings on every operation that is not served from cache.
- **Sections:**
  - `## The request protocol` — the daemon opens `/dev/fuse` and loops reading requests (`FUSE_LOOKUP`, `FUSE_GETATTR`, `FUSE_READ`, `FUSE_WRITE`, …) and writing replies. The kernel side (`fs/fuse/`) queues requests in `struct fuse_conn` and blocks the calling task until the reply arrives. Draw the **anchor** here.
  - `## What it costs` — each uncached operation is at least two extra crossings plus a context switch into the daemon. Where the page cache, attribute and entry timeouts (`attr_timeout`, `entry_timeout`), and `writeback_cache` claw performance back, and why metadata-heavy workloads suffer most.
  - `## Making it faster` — splice-based transfer, the FUSE passthrough mode that lets reads and writes go straight to a backing file, and the io_uring-based transport (state the version each arrived in; **verify both** before writing). Present them as the state of the interface at v6.18, not as general FUSE behaviour.
  - `## virtiofs` — FUSE's protocol over a virtio transport, sharing a host directory into a VM. Link back to `../01-lab-and-toolchain/a-full-system-vm-and-wsl2.md`, where the lab already used it.
  - `## Where FUSE shows up` — **table**: sshfs, rclone, gocryptfs, `fuse-overlayfs` for rootless containers, NTFS-3G, and AppImage — each with why user space was the right place for it.
  - `## When it is worth it` — bounded rules of thumb: protocol clients and experimental filesystems yes; a hot database volume no. Name the security model (`allow_other`, the `user_allow_other` setting in `/etc/fuse.conf`, and why other users cannot see your FUSE mount by default).
- **Anchor:** a Mermaid `sequenceDiagram` — Application, VFS, fuse kernel module, `/dev/fuse`, FUSE daemon, backing storage — for one uncached `read()`, showing the application blocked while the request crosses to the daemon and back, with each boundary crossing labelled. Caption: "One `read()` on a FUSE filesystem: the application waits while its request makes a round trip through a user-space daemon."
- **KernelFacts:**
  - `structure` — `[["struct fuse_conn", "fs/fuse/fuse_i.h"], ["struct fuse_in_header", "include/uapi/linux/fuse.h"]]`
  - `path` — `"read() → fuse_file_read_iter() → fuse_simple_request() → daemon read(/dev/fuse) → reply → wake caller"` (verify: cached reads go through the page cache instead)
  - `observe` — `findmnt -t fuse,fuse.sshfs,fuse.gocryptfs` and `ls -l /dev/fuse`
  - `trap` — "A hung FUSE daemon hangs every process that touches its mount, in uninterruptible sleep — including an innocent `ls` of the parent directory or a `df`. `umount -l` detaches the mount; `echo 1 > /sys/fs/fuse/connections/N/abort` breaks the stuck requests."
- **References:**
  - `https://docs.kernel.org/filesystems/fuse.html` — the kernel side, mount options, and the abort interface used in the trap.
  - `https://github.com/libfuse/libfuse` — the reference user-space library and its examples; the fastest route to a working filesystem.
  - Vangoor, Tarasov & Zadok, *"To FUSE or Not to FUSE: Performance of User-Space File Systems"*, USENIX FAST 2017 — measured overhead across workloads, which is where the "metadata-heavy suffers most" claim comes from; predates passthrough.
  - `https://docs.kernel.org/filesystems/virtiofs.html` — FUSE over virtio, for the VM case.

- [ ] **Step 1: Run the overlayfs lab** as a real user with `sudo` on a real Linux host, and record every step's output. Confirm the whiteout's `ls -l` form on your system.
- [ ] **Step 2: Write `overlayfs.md`** to the brief above.
- [ ] **Step 3: Check the FUSE passthrough and io_uring transport versions** against `fs/fuse/` at v6.18 and the relevant merge-window LWN coverage, and note what you found.
- [ ] **Step 4: Write `fuse-and-userspace-filesystems.md`** to the brief above.
- [ ] **Step 5: Verify every symbol** — `ovl_entry`, `ovl_fs`, `ovl_lookup`, `ovl_open`, `ovl_maybe_copy_up`, `ovl_copy_up_flags`, `fuse_conn`, `fuse_in_header`, `fuse_file_read_iter`, `fuse_simple_request`, `FUSE_PASSTHROUGH`, and the `/sys/fs/fuse/connections` abort file. Also verify the xattr names.
- [ ] **Step 6: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 7: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write overlayfs and FUSE"
```

---

## Task 9: Folder 11 — Lab: a filesystem in 200 lines

**Files:**
- Modify: `docs/linux/11-vfs-and-filesystems/lab-a-minimal-filesystem.md`

**Interfaces:**
- Consumes: `11/the-four-objects`, `11/open-read-write-in-the-kernel`, `04/modules-in-practice` (the out-of-tree build), and the QEMU lab from folder 01.
- Produces: the folder's payoff page. Nothing depends on it; it closes the folder.

### `lab-a-minimal-filesystem.md` — Lab: A Filesystem in 200 Lines **[Lab host=qemu]**

- **Opens with:** a diagram of the VFS contract is not the same as having met it. This lab builds `kbfs`, an in-memory filesystem module: it registers a filesystem type, fills a superblock with a root directory and one file whose contents are generated on read, and mounts in the QEMU lab. Every piece of it maps onto an object from `./the-four-objects.md`, and most of the work is done by `fs/libfs.c` helpers — which is itself the lesson: the kernel ships a library for exactly this.
- **Sections:**
  - `## What you will build` — a **table** mapping each piece of code to its VFS object: `file_system_type` → superblock creation; `fill_super` → `super_block` plus root `inode` and `dentry`; `tree_descr` → the files; `file_operations.read` → the generated contents.
  - `## The module` — the full source in one ` ```c ` block, target ≤ 120 lines:
    - `module_init`/`module_exit` calling `register_filesystem`/`unregister_filesystem`;
    - a `file_system_type` using the fs_context API (`.init_fs_context` whose `get_tree` calls `get_tree_nodev(fc, kbfs_fill_super)`);
    - `kbfs_fill_super` calling `simple_fill_super` with a `tree_descr` naming one file;
    - that file's `file_operations` whose `.read` uses `simple_read_from_buffer` over a string that includes `jiffies` — so each read is visibly generated, not stored;
    - `.kill_sb = kill_litter_super`.

    **Verify every one of these API names and signatures at v6.18 before writing** — the mount API conversion changed this code shape, and older tutorials use `mount_nodev`/`.mount`.
  - `## The Makefile` — the three-line out-of-tree `Makefile` from `../04-kernel-architecture-and-idioms/modules-in-practice.md`, built against the lab kernel tree with `make -C <linux> M=$PWD`.
  - `<Lab host="qemu" title="Build, load, mount, and read kbfs" time="30 min">` —
    1. build the module against the v6.18 tree used in folder 01;
    2. copy `kbfs.ko` into the BusyBox initramfs from `../01-lab-and-toolchain/a-minimal-rootfs.md` and re-pack it;
    3. boot with the canonical invocation from `../01-lab-and-toolchain/booting-your-kernel-in-qemu.md`;
    4. `insmod kbfs.ko`, `grep kbfs /proc/filesystems`;
    5. `mkdir /mnt/kb && mount -t kbfs none /mnt/kb`, `ls -li /mnt/kb`, `cat /mnt/kb/hello` twice (the jiffies value changes), `grep kbfs /proc/self/mountinfo`;
    6. `umount /mnt/kb && rmmod kbfs`.

    Real output for every step, **captured from the QEMU session**. "If it fails": a vermagic mismatch means the module was built against a different tree from the running kernel (see `../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md`); `mount: unknown filesystem type` means `insmod` failed silently — check `dmesg`.
  - `## Break it on purpose` — two short experiments with their real `dmesg` results:
    1. `rmmod` while mounted (refused — explain which reference pins the module);
    2. remove `.kill_sb` and observe what goes wrong.

    If the second produces an oops, show it and link to `../04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md`. This is why the lab host is `qemu`.
  - `## Where to go from here` — adding a writable file with `simple_write_to_buffer`, making the root directory list dynamic, and reading `fs/ramfs/inode.c` as the next-smallest real filesystem.
- **Anchor:** a Mermaid `sequenceDiagram` — `mount` command, VFS, kbfs module, libfs — for the mount: `get_tree_nodev` → new superblock → `kbfs_fill_super` → `simple_fill_super` creates root inode and dentry plus one file → mount attached. Then a second, short sequence for `cat /mnt/kb/hello` reaching the module's read. Caption: "What happens inside `mount -t kbfs`, and the single callback a `cat` reaches — every other step is VFS and libfs code you did not write."
- **KernelFacts:**
  - `structure` — `[["struct file_system_type", "include/linux/fs.h"], ["struct tree_descr", "include/linux/fs.h"]]`
  - `path` — `"mount -t kbfs → vfs_get_tree() → get_tree_nodev() → kbfs_fill_super() → simple_fill_super()"`
  - `observe` — `grep kbfs /proc/filesystems /proc/self/mountinfo`
  - `trap` — "`libfs` makes a toy filesystem short, not safe: `simple_*` helpers assume an in-memory filesystem with no backing store, and copying this pattern into a filesystem that has real storage produces one that silently loses writes."
- **References:**
  - `<Src file="fs/libfs.c" symbol="simple_fill_super" />` — the helper doing most of the work in this lab, with its comment.
  - `https://docs.kernel.org/filesystems/mount_api.html` — the fs_context mount API the module uses.
  - `<Src file="fs/ramfs/inode.c" />` — the smallest real filesystem in the tree, and the natural next read.
  - Corbet, *"Creating Linux virtual filesystems"*, LWN 2002 (`https://lwn.net/Articles/13325/`) — the classic walkthrough of this exact idea; the API it uses is long obsolete, so read it for the shape, not the code.

- [ ] **Step 1: Verify the API surface first** — `register_filesystem`, `unregister_filesystem`, `file_system_type` (`.init_fs_context`, `.kill_sb`), `fs_context_operations` (`.get_tree`), `get_tree_nodev`, `simple_fill_super`, `tree_descr`, `simple_read_from_buffer`, `kill_litter_super` — at v6.18. Write the module against what exists.
- [ ] **Step 2: Build and run the lab** in the QEMU environment from folder 01, from a clean v6.18 build, and record the real output of every step, including both "break it" experiments. **Do not write this page from expectation** — the "if it fails" line names failures you actually hit.
- [ ] **Step 3: Write `lab-a-minimal-filesystem.md`** to the brief above, pasting the exact source that ran.
- [ ] **Step 4: Check, build, and confirm folder 11 is complete**

```bash
npm run check:linux && npm run build
rtk run "grep -l 'Not yet written' docs/linux/11-vfs-and-filesystems/*.md"
```

Expected: zero findings, a green build, and no output from the grep — all thirteen folder 11 pages are written.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/11-vfs-and-filesystems
git commit -m "docs: write the minimal filesystem lab"
```

---
## Task 10: Folder 12 — the storage stack map, block devices, and the `bio`

**Files:**
- Modify: `docs/linux/12-block-layer-and-storage/the-block-layer-map.md`
- Modify: `docs/linux/12-block-layer-and-storage/block-devices-and-gendisk.md`
- Modify: `docs/linux/12-block-layer-and-storage/the-bio.md`

**Interfaces:**
- Consumes: `11/open-read-write-in-the-kernel` (Task 5) — its full-path diagram ends exactly where this folder's map begins. Also `08/writeback-and-fsync`.
- Produces:
  - `12/the-block-layer-map`, the folder's map page, written first per the spec;
  - `12/block-devices-and-gendisk`;
  - `12/the-bio`, a prerequisite of blk-mq, direct I/O, device mapper, and software RAID.

### `the-block-layer-map.md` — The Storage Stack, Mapped

- **Opens with:** between an application's `write()` and a flash die there are about a dozen layers, and most "the disk is slow" conversations go wrong by blaming the wrong one. This page is the map: every layer in one picture, what each one does to a request as it passes through, and which page in this folder owns it. Every later page refers back here.
- **Sections:**
  - `## The layers, top to bottom` — a **table**, one row per layer: VFS, page cache, filesystem, block layer entry (`submit_bio`), stacking drivers (device mapper, md), blk-mq, I/O scheduler, device driver (NVMe, virtio-blk, SCSI), transport, device firmware (FTL), media. Columns: what it receives, what it emits, and the page that owns it. The first two rows link back to folders 11 and 08.
  - `## Where requests change shape` — a byte range becomes folios, folios become a `bio` of sectors, `bio`s become `request`s, and `request`s become device commands. Say that the unit changes at each boundary, and that confusion about which unit a metric counts explains most misread `iostat` output.
  - `## Three paths through the stack` — buffered (through the page cache, completion decoupled from the application), direct (`O_DIRECT`, application waits for the device), and memory-mapped (faults and writeback). One paragraph each, with links to `./buffered-direct-and-alignment.md`.
  - `## Stacking` — device mapper and md sit *between* the filesystem and the real device and emit new `bio`s of their own. That is why `lsblk` shows a tree and why one application write can become several device writes (RAID 1) or none yet (a thin-provisioned snapshot).
  - `## What this folder does not cover` — device physics, the NVMe protocol, and SSD internals are owned by `../../computer-science/storage/` (link the intro); the driver *model* is a later folder, named in prose only.
- **Anchor:** a Mermaid `flowchart TB` simplification of the stack for the layers this folder covers — VFS → page cache → filesystem → `submit_bio` → optional dm/md → blk-mq (software queues → scheduler → hardware queues) → driver → device — with the `O_DIRECT` edge skipping the page cache. Each node is labelled with the unit it passes on (folio, `bio`, `request`, command). Caption: "The storage stack this folder covers, with the unit of work each layer hands to the next."
- **Figure (added in Task 22):** the Thomas-Krenn "Linux Storage Stack Diagram", zoomable, beside the Mermaid simplification. **Leave a clearly marked place for it in the page now** — a sentence saying the full diagram follows — and write the page so it stands alone without it.
- **KernelFacts:**
  - `structure` — `[["struct bio", "include/linux/blk_types.h"], ["struct request", "include/linux/blk-mq.h"]]`
  - `path` — `"vfs_write() → page cache → writeback → submit_bio() → blk_mq_submit_bio() → driver ->queue_rq()"`
  - `observe` — `lsblk -o NAME,TYPE,SIZE,SCHED,ROTA,MOUNTPOINTS`
  - `trap` — "`iostat`, `biolatency`, and your database each measure latency at a different layer of this stack, so their numbers legitimately disagree. Before comparing two latency figures, find out which layer each one was taken at."
- **References:**
  - Thomas-Krenn wiki, *"Linux Storage Stack Diagram"* (`https://www.thomas-krenn.com/en/wiki/Linux_Storage_Stack_Diagram`) — the canonical figure, versioned per kernel release; the page's anchor figure.
  - `https://docs.kernel.org/block/index.html` — the block-layer documentation index at the pinned version.
  - Gregg, *Systems Performance* (2nd ed.), ch. 9 "Disks" — the layered methodology this page's trap is based on; a purchase.
  - LWN, *"A block layer introduction"* part 1 (`https://lwn.net/Articles/736534/`) — Neil Brown's 2017 overview of `bio`s and the request layer; the model is current, several names changed.

### `block-devices-and-gendisk.md` — Block Devices and `gendisk`

- **Opens with:** a block device is a device the kernel can address as an array of fixed-size sectors, in any order. That one property is why filesystems, the page cache, partitions, and the I/O scheduler can all exist on top of it. The kernel describes each such disk with a `gendisk`, and almost everything you can see about a disk in `/dev` and `/sys/block` is generated from that structure.
- **Sections:**
  - `## What makes a device a block device` — random access by sector, a fixed logical block size, buffering through the page cache, and I/O submitted as `bio`s rather than byte streams. Contrast with a character device in one sentence.
  - `## gendisk and block_device` — `struct gendisk` as the disk (queue, partitions, capacity, name, `fops`); `struct block_device` as the openable device node (the whole disk or one partition). How a driver creates one: allocate a disk with its queue and limits (`blk_mq_alloc_disk` — verify the v6.18 signature, which takes a `queue_limits`), set capacity, then `add_disk`.
  - `## Partitions` — partition tables parsed by `block/partitions/`, each partition a `block_device` on the same `gendisk`, and `BLKPG`/`partprobe` for re-reading a table.
  - `## Device numbers and `/dev`` — major/minor numbers, dynamic allocation, and the kernel emitting a uevent that `udev` turns into a `/dev` node and `/dev/disk/by-*` symlinks. Why `/dev/sda` names are not stable and `by-id`/`by-uuid` are. The uevent machinery itself is a later folder's, named in prose.
  - `## /sys/block, the attributes worth knowing` — a **table** of `queue/scheduler`, `queue/rotational`, `queue/nr_requests`, `queue/logical_block_size`, `queue/physical_block_size`, `queue/max_sectors_kb`, `queue/read_ahead_kb`, `queue/write_cache`, and `stat` — each with what it controls or reports, and whether it is writable.
  - `## Opening a block device` — the v6.18 in-kernel API returns a `struct file` (`bdev_file_open_by_path`), and exclusive opens are how a mounted filesystem stops a second mount or `mkfs` of the same device. Explain `EBUSY` from `mkfs` on a mounted partition.
- **Anchor:** a Mermaid `classDiagram` — `gendisk`, `block_device` (whole disk), `block_device` (partition 1), `request_queue`, `queue_limits` — with the fields that link them, and the `/dev` and `/sys/block` paths generated from each. Caption: "One disk as the kernel sees it: the `gendisk`, a `block_device` per partition, and the files `udev` and sysfs generate from them."
- **KernelFacts:**
  - `structure` — `[["struct gendisk", "include/linux/blkdev.h"], ["struct block_device", "include/linux/blk_types.h"]]`
  - `path` — `"driver probe → blk_mq_alloc_disk() → set_capacity() → add_disk() → uevent → udev creates /dev node"`
  - `observe` — `grep -H . /sys/block/*/queue/{scheduler,rotational,logical_block_size} 2>/dev/null`
  - `trap` — "`/dev/sda` is an enumeration order, not an identity — add a disk or change probe timing and the names shift. Anything written to `/etc/fstab` or a script should use `/dev/disk/by-uuid` or `by-id`."
- **References:**
  - `<Src file="block/genhd.c" symbol="device_add_disk" />` — where a disk becomes visible (verify whether `add_disk` is a wrapper around it at v6.18).
  - `https://docs.kernel.org/admin-guide/devices.html` — the registered major/minor number list.
  - `https://docs.kernel.org/block/queue-sysfs.html` — every `/sys/block/<dev>/queue` attribute, defined.
  - `https://man7.org/linux/man-pages/man8/lsblk.8.html` — the tool that renders all of this as a tree.

### `the-bio.md` — The `bio`

- **Opens with:** the `bio` is the block layer's unit of work: a direction, a starting sector, a list of memory segments holding the data, and a function to call when it is done. Everything above the block layer produces `bio`s and everything below consumes them. Understanding its shape — especially that it describes memory as pages rather than a flat buffer — explains splitting, merging, and why stacking drivers can rewrite I/O cheaply.
- **Sections:**
  - `## The fields that matter` — `bi_opf` (operation plus flags: `REQ_OP_READ`, `REQ_OP_WRITE`, `REQ_OP_FLUSH`, `REQ_OP_DISCARD`, and flags such as `REQ_SYNC`, `REQ_META`, `REQ_PREFLUSH`, `REQ_FUA`), `bi_iter` (current sector, remaining size, index into the vector), `bi_io_vec` (the array of `bio_vec` page/offset/length segments), `bi_end_io`, `bi_private`, and `bi_status`.
  - `## Segments, not buffers` — a `bio_vec` points at a page (or folio), an offset and a length, so a `bio` can describe discontiguous memory without copying it into one buffer. Why the iterator lives separately from the vector (immutable biovecs): a `bio` can be split or partially completed without editing the vector itself.
  - `## Building and submitting one` — `bio_alloc`, `bio_add_folio` (or `bio_add_page`), set sector and end_io, `submit_bio`. A ≤ 25-line ` ```c ` sketch reading one block synchronously with `submit_bio_wait`, labelled as illustrative and not how filesystems usually do it.
  - `## Where writeback's bios come from` — filesystems build `bio`s from dirty folios in their `writepages` path, often through `iomap` (`iomap_writepages`) or filesystem-specific code (ext4's `fs/ext4/page-io.c`). Link `../08-memory-management/writeback-and-fsync.md` for how the folios got dirty. **Anchor** here.
  - `## Splitting, chaining, and merging` — a `bio` larger than the device's limits is split (`bio_split`) with the pieces chained so the parent completes when all children do. Adjacent `bio`s are merged into one request inside a plug (`blk_start_plug`/`blk_finish_plug`), which is why sequential writes become large device commands.
  - `## Flushes and FUA` — `REQ_OP_FLUSH` asks the device to empty its volatile cache; `REQ_PREFLUSH` attaches that to a write; `REQ_FUA` asks for one write to be durable on completion. This is the representation of the barrier that `../11-vfs-and-filesystems/journaling-and-crash-consistency.md` and `../08-memory-management/writeback-and-fsync.md` depend on, and the block layer drops these flags for devices that report no volatile cache.
  - `## Completion` — the driver completes the request, the block layer calls `bio_endio`, and `bi_end_io` runs — often in interrupt or softirq context. Say what that means for the callback (link `../10-interrupts-time-and-deferred-work/hardirq-context.md`).
- **Anchor:** a Mermaid `flowchart LR` from dirty folios in an `address_space` → the filesystem's writepages → a `bio` (drawn with its sector, `bio_vec` segments pointing at the folios, and `bi_end_io`) → `submit_bio` → (split if over limits) → blk-mq → completion → `bio_endio` → folios marked clean. Caption: "A `bio` from birth to completion: dirty page-cache folios described as segments, submitted, possibly split, and completed back onto the folios they came from."
- **Second visual:** a Mermaid `classDiagram` of `struct bio` → `struct bvec_iter` and `struct bio_vec[]` → pages, with the eight fields above.
- **KernelFacts:**
  - `structure` — `[["struct bio", "include/linux/blk_types.h"], ["struct bio_vec", "include/linux/bvec.h"]]`
  - `path` — `"writepages → bio_alloc() → bio_add_folio() → submit_bio() → submit_bio_noacct() → blk_mq_submit_bio()"`
  - `observe` — `sudo perf trace -e 'block:block_bio_queue' -- dd if=/dev/zero of=/tmp/b bs=1M count=8 oflag=direct` (verify the tracepoint name with `perf list 'block:*'`)
  - `trap` — "A `bio`'s completion callback usually runs in interrupt or softirq context, not in the task that submitted it. Code that sleeps, allocates with `GFP_KERNEL`, or takes a mutex in `bi_end_io` works in testing and deadlocks under load."
- **References:**
  - `https://docs.kernel.org/block/biovecs.html` — the immutable biovec design and why the iterator is separate.
  - `<Src file="include/linux/blk_types.h" symbol="bio" />` — the structure and every `REQ_*` flag.
  - LWN, *"A block layer introduction part 1: the bio layer"* (`https://lwn.net/Articles/736534/`) — the clearest prose account of `bio` handling; 2017.
  - `<Src file="block/blk-core.c" symbol="submit_bio" />` — the entry point, with the stacking-safe `submit_bio_noacct` beside it.

- [ ] **Step 1: Write `the-block-layer-map.md`** to the brief above, leaving the marked place for the Task 22 figure.
- [ ] **Step 2: Write `block-devices-and-gendisk.md`** to the brief above. Capture the `/sys/block` table values from a real machine (and from the full-system VM's virtio disk), stating which device each came from.
- [ ] **Step 3: Write `the-bio.md`** to the brief above. Run the `perf trace` observe command for real and use its output in a ` ```text ` block.
- [ ] **Step 4: Verify every symbol** — `bio`, `bio_vec`, `bvec_iter`, `bi_opf`, `REQ_OP_FLUSH`, `REQ_PREFLUSH`, `REQ_FUA`, `bio_alloc`, `bio_add_folio`, `submit_bio`, `submit_bio_noacct`, `submit_bio_wait`, `bio_split`, `bio_chain`, `bio_endio`, `blk_start_plug`, `blk_finish_plug`, `iomap_writepages`, `gendisk`, `block_device`, `blk_mq_alloc_disk`, `queue_limits`, `add_disk`, `device_add_disk`, `set_capacity`, `bdev_file_open_by_path` — and the `block:*` tracepoint names.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 6: Commit**

```bash
git add docs/linux/12-block-layer-and-storage
git commit -m "docs: write the storage stack map, block devices, and the bio"
```

---

## Task 11: Folder 12 — blk-mq, I/O schedulers, and NVMe

**Files:**
- Modify: `docs/linux/12-block-layer-and-storage/blk-mq.md`
- Modify: `docs/linux/12-block-layer-and-storage/io-schedulers.md`
- Modify: `docs/linux/12-block-layer-and-storage/nvme-in-the-kernel.md`

**Interfaces:**
- Consumes: `12/the-bio` (Task 10), `10/how-an-interrupt-reaches-the-kernel`, `10/interrupt-affinity-and-balancing` (MSI-X per queue is already explained there — link it).
- Produces:
  - `12/blk-mq`, a prerequisite of I/O schedulers, NVMe, and diagnosing;
  - `12/io-schedulers`, a prerequisite of diagnosing;
  - `12/nvme-in-the-kernel`, the link target for the Task 2 backlink from the CS NVMe page.

### `blk-mq.md` — blk-mq: Multi-Queue Block I/O **[WAH]**

- **Opens with:** for decades Linux had one request queue per disk, protected by one lock, and every CPU submitting I/O contended for it. That was fine for a disk doing 200 operations a second and fatal for an SSD doing 500,000 across 64 cores. blk-mq replaced the single queue with per-CPU software queues feeding per-device hardware queues. Its design is a direct application of `../09-concurrency-and-locking/per-cpu-data.md`: remove the sharing instead of making the lock faster.
- **Sections:**
  - `## Why one queue collapsed` — the single-queue layer's lock, cache-line bouncing, and the numbers from the blk-mq paper, as a short argument rather than a benchmark dump. Note that the legacy single-queue path was removed entirely (state the version; verify).
  - `## Software queues and hardware queues` — `struct blk_mq_ctx` per CPU, `struct blk_mq_hw_ctx` per device queue, and the mapping between them (`blk_mq_queue_map`). An NVMe device with one queue per CPU gets a 1:1 map; a single-queue SATA disk maps every CPU to one hardware context.
  - `## Tags` — each in-flight request holds a tag from a per-hardware-queue bitmap (`blk_mq_get_tag`), which doubles as the index the driver and device use to find it again. The tag count *is* the queue depth, and `nr_requests` is its tunable face.
  - `## The submission path` — `blk_mq_submit_bio` → plug and merge attempts → get a request and tag → (scheduler insert, if one is attached) → dispatch → the driver's `->queue_rq`. Name `struct blk_mq_ops` and `struct blk_mq_tag_set` as a driver's whole interface to blk-mq.
  - `## The completion path` — the device finishes, raises an interrupt on the queue's vector, the driver finds the request by tag, calls `blk_mq_complete_request` / `blk_mq_end_request`, and `bio_endio` wakes the waiter. Completion batching (`io_comp_batch`) in one paragraph.
  - `## What actually happens` **[WAH]** — `dd if=/dev/nvme0n1 of=/dev/null bs=4k count=1 iflag=direct` (or the full-system VM's `vdb`; read-only). Follow the one read:
    1. syscall on CPU 3;
    2. a `bio` built from the user page;
    3. CPU 3's software queue;
    4. hardware queue 3 and a tag;
    5. the driver writes a submission-queue entry and rings a doorbell;
    6. the device DMAs the block and writes a completion entry;
    7. an MSI-X interrupt arrives on CPU 3;
    8. completion by tag;
    9. the task wakes.

    Emphasise that no lock is shared with any other CPU's I/O on the way.
  - `## Where the scheduler sits` — optional, attached per queue, between software and hardware queues. Link forward to `./io-schedulers.md`.
- **Anchor:** a Mermaid `flowchart LR` with four CPUs on the left, each with its own software queue, mapping through an optional scheduler box to two or four hardware queues and a device on the right, and the completion interrupt returning to the originating CPU. Show a second panel (subgraph) for a single-queue device where all software queues converge on one hardware queue. Caption: "blk-mq on a multi-queue NVMe device and on a single-queue disk: the same code path, with the fan-in drawn where the hardware forces it."
- **KernelFacts:**
  - `structure` — `[["struct blk_mq_hw_ctx", "include/linux/blk-mq.h"], ["struct blk_mq_tag_set", "include/linux/blk-mq.h"]]`
  - `path` — `"blk_mq_submit_bio() → blk_mq_get_new_requests() → blk_mq_run_hw_queue() → ->queue_rq() … irq → blk_mq_complete_request() → bio_endio()"`
  - `observe` — `ls /sys/block/nvme0n1/mq/ && cat /sys/block/nvme0n1/mq/0/cpu_list` (substitute any multi-queue device)
  - `trap` — "More hardware queues do not make a single-threaded workload faster. blk-mq removes contention *between* CPUs; one thread submitting I/O uses one software queue and one hardware queue no matter how many the device offers."
- **References:**
  - `https://docs.kernel.org/block/blk-mq.html` — the in-tree design document: software queues, hardware queues, tags.
  - Bjørling, Axboe, Nellans & Bonnet, *"Linux Block IO: Introducing Multi-queue SSD Access on Multi-core Systems"*, SYSTOR 2013 — the paper that motivated and measured the design.
  - LWN, *"The multiqueue block layer"* (`https://lwn.net/Articles/552904/`) — the 2013 announcement; historical, and the reason the single-queue path is gone.
  - `<Src file="block/blk-mq.c" symbol="blk_mq_submit_bio" />` — the submission path.

### `io-schedulers.md` — I/O Schedulers **[Misc]** **[Lab host=qemu]**

- **Opens with:** an I/O scheduler decides the order in which queued requests reach the device. On a spinning disk, order is everything: a seek costs milliseconds, so sorting and batching requests is worth real CPU time. On an NVMe drive with thousands of commands in flight and no seek, reordering mostly adds latency. That asymmetry is the whole reason Linux ships four choices, including "none".
- **Sections:**
  - `## What a scheduler can do` — reorder, merge, batch, give reads priority over writes, enforce fairness between processes or cgroups, and bound latency. Each costs CPU and adds a hop.
  - `## The four` — a **table**: `none` (FIFO dispatch, no reordering), `mq-deadline` (sorted by sector with read/write deadlines), `bfq` (budget fair queueing — per-process fairness and interactivity at a high CPU cost), `kyber` (token-based latency targets for reads and synchronous writes). Columns: what it optimises, CPU cost, the device it suits, and the tunables under `/sys/block/<dev>/queue/iosched/`.
  - `## Defaults, and who sets them` — the kernel's choice for single- versus multi-queue devices, and distributions or udev rules overriding it. **Verify the v6.18 default-selection logic in `block/elevator.c`** and state it precisely, rather than the folklore "NVMe gets none".
  - `## Switching at runtime` — `echo mq-deadline > /sys/block/<dev>/queue/scheduler`, which schedulers are available as modules, and making the choice persistent with a udev rule (show a two-line rule).
  - `## cgroups and the scheduler` — `bfq` implements `io.bfq.weight`; `io.max` and `io.latency` are enforced by separate rq-qos policies, not by the scheduler. Name the containers folder in prose (unlinked) as owning cgroup I/O control.
  - `<Lab host="qemu" title="Switch schedulers and measure the difference" time="25 min">` — in the full-system Debian VM from `../01-lab-and-toolchain/a-full-system-vm-and-wsl2.md`, with the extra scratch disk attached as `/dev/vdb`:
    1. `cat /sys/block/vdb/queue/scheduler`;
    2. install `fio`;
    3. for each of `none`, `mq-deadline`, `bfq`: select it, then run `sudo fio --name=rr --filename=/dev/vdb --readonly --rw=randread --bs=4k --direct=1 --iodepth=32 --ioengine=io_uring --runtime=20 --time_based --group_reporting`;
    4. record IOPS and the `clat` p99 for each in a table.

    State plainly that a VM's numbers reflect the host's device and caching, so the lesson is the mechanism and the *relative* CPU cost, not an absolute ranking. "If it fails": `bfq` may need `modprobe bfq`; `--readonly` is what keeps `fio` from writing to the device, so never drop it.
  - `## Misconceptions` **[Misc]** —
    1. "`none` means no queueing." Requests still queue in blk-mq; `none` only means no reordering.
    2. "BFQ is the best scheduler because it is the most sophisticated." Its fairness costs CPU that fast devices notice.
    3. "Changing the scheduler fixes a slow disk." It reorders the queue; it cannot make the device faster.
- **Anchor:** the four-scheduler **table**, plus a Mermaid `flowchart LR` showing the same five queued requests (with sector numbers) dispatched in arrival order by `none` and in sector-sorted batches by `mq-deadline`, as two subgraphs. Caption: "Five requests, two orders: FIFO dispatch under `none` versus sector-sorted dispatch under `mq-deadline`."
- **KernelFacts:**
  - `structure` — `[["struct elevator_mq_ops", "block/elevator.h"], ["struct elevator_type", "block/elevator.h"]]` (verify the header location at v6.18)
  - `path` — `"blk_mq_submit_bio() → e->type->ops.insert_requests() → blk_mq_run_hw_queue() → ops.dispatch_request() → ->queue_rq()"`
  - `observe` — `cat /sys/block/*/queue/scheduler`
  - `trap` — "The brackets in `/sys/block/*/queue/scheduler` mark the *active* scheduler, and the list shows only those currently loaded. A scheduler missing from the list may simply be an unloaded module, not unsupported."
- **References:**
  - `https://docs.kernel.org/block/switching-sched.html` — switching and listing schedulers at runtime.
  - `https://docs.kernel.org/block/bfq-iosched.html` — BFQ's design, tunables, and its own guidance on when to use it.
  - `https://docs.kernel.org/block/deadline-iosched.html` and `https://docs.kernel.org/block/kyber-iosched.html` — the other two schedulers' tunables (verify both paths).
  - `https://fio.readthedocs.io/en/latest/fio_doc.html` — the options this page's lab uses, especially `--readonly` and the latency percentiles.

### `nvme-in-the-kernel.md` — NVMe in the Kernel

- **Opens with:** NVMe was designed after multi-core CPUs and flash, and it shows. Instead of one command queue in front of a slow device, it gives each CPU its own pair of submission and completion rings in host memory, with a doorbell register to say "look". That maps almost one-to-one onto blk-mq's hardware queues, which is why the Linux NVMe driver is small for what it does. This page covers the mapping; the protocol itself is owned by `../../computer-science/storage/nvme-and-storage-interfaces.md`.
- **Sections:**
  - `## Queue pairs mapped to blk-mq` — one admin queue plus I/O queue pairs, typically one per CPU up to the device's limit. Each I/O queue is a `blk_mq_hw_ctx`, and the request tag becomes the NVMe command identifier. Link `./blk-mq.md`.
  - `## Submitting a command` — `nvme_queue_rq` sets up the command (`nvme_setup_cmd`), maps data for DMA (a later folder owns the DMA API; name it in prose), copies the 64-byte command into the submission queue, and writes the tail doorbell. Doorbell batching in one sentence.
  - `## Completing a command` — the device writes a completion entry and raises the queue's MSI-X vector; `nvme_irq` walks the completion queue, finds each request by command id, and completes it. Link `../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md` for why the vector is affined to the queue's CPU.
  - `## Polled I/O` — for the lowest latency, skip the interrupt: dedicated poll queues (`nvme.poll_queues`) and `REQ_POLLED` requests, driven by `io_uring`'s `IORING_SETUP_IOPOLL`. What it costs: a busy CPU. Link `./io-uring.md`.
  - `## Namespaces, multipath, and fabrics` — a namespace is a block device (`/dev/nvme0n1`); controllers versus namespaces; native NVMe multipath (`nvme_ns_head`); NVMe-oF over TCP, RDMA and FC in one paragraph, as the same host driver core with a different transport.
  - `## Timeouts and resets` — a command that does not complete within `nvme_core.io_timeout` triggers abort and then controller reset (`nvme_timeout`). Say what that looks like in `dmesg` and why a flaky drive shows up as whole-system I/O stalls.
- **Anchor:** a Mermaid `sequenceDiagram` — blk-mq, nvme driver, Submission queue (host memory), Doorbell, Device, Completion queue, CPU interrupt — for one read: SQE written, doorbell rung, device fetches the SQE and DMAs the data, CQE written, MSI-X interrupt, driver reaps the CQE, request completed. Caption: "One NVMe read on its per-CPU queue pair: two rings in host memory, one doorbell write, one interrupt."
- **Second visual:** a WaveDrom `reg` strip of the first eight bytes of the 64-byte NVMe common command (opcode, flags with the PSDT bits, command identifier) plus the namespace-id field. Build it **from the NVMe Base Specification's submission-queue-entry figure**, and verify against `struct nvme_common_command` in `include/linux/nvme.h`. Caption: "The start of every NVMe command: the opcode, the flags, and the identifier that is also the blk-mq tag."
- **KernelFacts:**
  - `structure` — `[["struct nvme_queue", "drivers/nvme/host/pci.c"], ["struct nvme_command", "include/linux/nvme.h"]]`
  - `path` — `"blk-mq ->queue_rq() → nvme_queue_rq() → nvme_setup_cmd() → nvme_sq_copy_cmd() → doorbell … nvme_irq() → nvme_poll_cq() → blk_mq_complete_request()"` (verify each name)
  - `observe` — `grep nvme /proc/interrupts | head -5 && cat /sys/block/nvme0n1/queue/nr_requests`
  - `trap` — "An NVMe device's queue count is negotiated with the driver, not fixed. On a VM or with `nvme.io_queue_depth`/`poll_queues` set, fewer queues than CPUs is normal — and `/proc/interrupts` then shows several CPUs sharing a vector."
- **References:**
  - NVM Express, *NVM Express Base Specification* (`https://nvmexpress.org/specifications/`) — the authority on queue pairs, doorbells and the command layout.
  - `<Src file="drivers/nvme/host/pci.c" symbol="nvme_queue_rq" />` — the submission path in the PCIe transport.
  - `<Src file="drivers/nvme/host/core.c" />` — transport-independent core: namespaces, timeouts, multipath hooks.
  - LWN, *"Block-layer polling"* or the `io_uring` IOPOLL coverage — **verify an article URL before citing it**; otherwise cite `man 2 io_uring_setup` for `IORING_SETUP_IOPOLL`.

- [ ] **Step 1: Write `blk-mq.md`** to the brief above. Run the WAH `dd` read-only on a real multi-queue device (or the VM's `vdb`) and confirm the CPU/queue/interrupt mapping from `/sys/block/*/mq` and `/proc/interrupts` on that same device.
- [ ] **Step 2: Run the I/O-scheduler lab** in the full-system VM and record the real `fio` numbers and scheduler lists. Keep `--readonly` on every run.
- [ ] **Step 3: Write `io-schedulers.md`** to the brief above, using the recorded numbers.
- [ ] **Step 4: Write `nvme-in-the-kernel.md`** to the brief above.
- [ ] **Step 5: Verify every symbol and default** — `blk_mq_ctx`, `blk_mq_hw_ctx`, `blk_mq_queue_map`, `blk_mq_get_tag`, `blk_mq_submit_bio`, `blk_mq_get_new_requests`, `blk_mq_run_hw_queue`, `blk_mq_ops`, `blk_mq_tag_set`, `blk_mq_complete_request`, `blk_mq_end_request`, `io_comp_batch`, `elevator_mq_ops`, `elevator_type`, `nvme_queue`, `nvme_command`, `nvme_common_command`, `nvme_queue_rq`, `nvme_setup_cmd`, `nvme_sq_copy_cmd`, `nvme_irq`, `nvme_poll_cq`, `nvme_timeout`, `nvme_ns_head`, `REQ_POLLED`, the `nvme.poll_queues` and `nvme_core.io_timeout` parameters, the default-scheduler logic, and the version in which the legacy single-queue path was removed.
- [ ] **Step 6: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 7: Commit**

```bash
git add docs/linux/12-block-layer-and-storage
git commit -m "docs: write blk-mq, I/O schedulers, and NVMe in the kernel"
```

---

## Task 12: Folder 12 — buffered and direct I/O, and `io_uring`

**Files:**
- Modify: `docs/linux/12-block-layer-and-storage/buffered-direct-and-alignment.md`
- Modify: `docs/linux/12-block-layer-and-storage/io-uring.md`

**Interfaces:**
- Consumes: `12/the-bio` (Task 10), `08/the-page-cache`, `05/what-a-system-call-actually-is` (the crossing cost that `io_uring` exists to avoid).
- Produces:
  - `12/buffered-direct-and-alignment` — the link target for Task 21's forward-reference fix in `08/the-page-cache` and for Task 2's databases backlink;
  - `12/io-uring` — the link target for the `io_uring` row in `05/what-a-system-call-actually-is`.

**Currency risk.** The spec singles out `io_uring` as the fastest-moving interface in the section. Do the context7 check **before** writing the second page, and date it in the references.

### `buffered-direct-and-alignment.md` — Buffered I/O, `O_DIRECT`, and Alignment **[WAH]** **[Misc]**

- **Opens with:** there are three ways for a program's bytes to reach a device, and each makes a different trade:
  - **Buffered I/O** goes through the page cache: fast, forgiving, and decoupled from the device's timing.
  - **Direct I/O** goes around the cache: the application owns caching and timing, and must obey the device's alignment rules.
  - **Memory mapping** turns reads and writes into page faults and writeback.

  Databases pick deliberately among these, and this page explains why.
- **Sections:**
  - `## Buffered: the default` — reads served from cache with readahead, writes copied into cache and flushed later. What you gain (no alignment rules, cache hits, write-behind) and what you give up (double caching when the application has its own buffer pool, and unpredictable writeback latency). Link `../08-memory-management/the-page-cache.md` and `../08-memory-management/writeback-and-fsync.md` — do not re-teach them.
  - `## Direct: `O_DIRECT`` — the filesystem's direct-I/O path (commonly `iomap_dio_rw`; `__blkdev_direct_IO` or its v6.18 successor for raw block devices) pins the user pages and builds `bio`s straight from them. The page cache is flushed and invalidated for the range first so the two views cannot disagree.
  - `## Alignment requirements` — buffer address, file offset and length must be multiples of the logical block size (and memory alignment may be stricter). Say how to discover them: `statx` with `STATX_DIOALIGN` reporting `stx_dio_mem_align` and `stx_dio_offset_align` (verify the version added), `posix_memalign` for the buffer, and `EINVAL` as the failure mode. **Second visual** here.
  - `## What `O_DIRECT` does not give you` — it is not synchronous durability: file metadata (size, allocation) may not be flushed, and the device's volatile cache is still in play. Durable direct writes still need `O_DSYNC` or `fdatasync`. `O_SYNC` versus `O_DSYNC` in a two-row table.
  - `## Memory-mapped I/O` — `mmap` of a file: reads become page faults on the page cache, writes dirty folios through the page tables, durability via `msync`, and why error handling is harder (a write error arrives as `SIGBUS` or a later `msync` failure).
  - `## What databases choose, and why` — a **table**: PostgreSQL (buffered I/O plus its own WAL and `fsync`, with direct I/O as a developer option in recent releases — verify), MySQL/InnoDB (`O_DIRECT` for data files), RocksDB (configurable), SQLite (buffered plus careful `fsync`), LMDB (`mmap`). One reason each. Link `../../computer-science/databases/indexing-and-storage-engines.md`.
  - `## What actually happens` **[WAH]** — `dd if=/dev/zero of=test bs=1M count=256` versus the same with `oflag=direct`, each followed by `sync`. Show real `dd` throughput and the `Dirty:` line of `/proc/meminfo` before and after. The buffered run "finishes" fast with the data still dirty in memory; the direct run reports the device's real speed; `sync` takes the difference.
  - `## Misconceptions` **[Misc]** —
    1. "`O_DIRECT` means synchronous and durable." It bypasses the cache; durability still needs `O_DSYNC` or `fdatasync`.
    2. "Direct I/O is always faster." It removes cache hits and readahead, and is usually slower for applications without their own buffer pool.
    3. "`mmap` is zero-copy, so it is always the fastest way to read a file." Page faults and TLB costs can exceed a `read()` copy, especially for sequential access.
- **Anchor:** a Mermaid `flowchart TB` with three lanes — buffered, direct, mmap — from the application down to `submit_bio`, showing where each copies (or does not), where each can block, and where completion reaches the application. Caption: "Three paths to the same device: where each one copies, where each one waits, and where the page cache sits or does not."
- **Second visual:** a WaveDrom `reg`-style byte strip showing a 4096-byte logical block with an aligned 4096-byte buffer and a misaligned 1000-byte write straddling a block boundary, labelled "accepted" and "EINVAL". Caption: "The alignment rule `O_DIRECT` enforces, drawn on a 4 KiB logical block."
- **KernelFacts:**
  - `structure` — `[["struct kiocb", "include/linux/fs.h"], ["struct iomap_dio", "fs/iomap/direct-io.c"]]`
  - `path` — `"write(O_DIRECT) → f_op->write_iter() → iomap_dio_rw() → iomap_dio_bio_iter() → submit_bio()"` (verify: per-filesystem paths differ)
  - `observe` — `grep -E '^(Dirty|Writeback):' /proc/meminfo` before and after a buffered `dd`, and `xfs_io -c statx` or a small `statx` program for `dio_mem_align`
  - `trap` — "A buffered write that returns quickly has not been slowed down by the disk yet — it will be, later, when writeback runs or when `balance_dirty_pages` throttles your next write. Benchmarks that stop the clock when `write()` returns are measuring memory, not storage."
- **References:**
  - `https://man7.org/linux/man-pages/man2/open.2.html`, the `O_DIRECT` notes — alignment rules and Linus's famous objection, quoted in the man page itself.
  - `https://man7.org/linux/man-pages/man2/statx.2.html` — `STATX_DIOALIGN` and its two fields.
  - LWN, *"Fixing the O_DIRECT alignment problem"* or the `STATX_DIOALIGN` merge coverage — **verify the article** before citing.
  - `https://www.postgresql.org/docs/current/runtime-config-developer.html` — PostgreSQL's `debug_io_direct` setting and its caveats, as a real example of a buffered-I/O database experimenting with direct I/O (verify the setting name).

### `io-uring.md` — `io_uring` **[Misc]**

- **Opens with:** every classic I/O syscall pays the crossing cost from `../05-syscalls-and-the-boundary/what-a-system-call-actually-is.md` once per operation. `io_uring` changes the unit of work: the application and kernel share two ring buffers, the application writes many requests into one and reaps many results from the other, and a single `io_uring_enter` — or none at all, in polling mode — moves them all. It is the most significant new I/O interface Linux has had in a decade, and one of the most security-contentious.
- **Sections:**
  - `## Two rings, shared memory` — the submission queue (SQEs written by the application, consumed by the kernel) and the completion queue (CQEs written by the kernel), both `mmap`ed from the ring fd so neither side copies. Head and tail indices, and why each ring has exactly one writer. **Anchor** here.
  - `## The three syscalls` — `io_uring_setup` (create the rings), `io_uring_enter` (submit and/or wait), `io_uring_register` (buffers, files, eventfds). Show one SQE's key fields — `opcode`, `fd`, `off`, `addr`, `len`, `user_data` — and the CQE's `user_data`, `res`, `flags`.
  - `## Completion, not readiness` — `io_uring` tells you an operation is *done*, where `epoll` tells you it *may be tried*. That is why it works for regular files, which `epoll` cannot help with. How operations that would block run: inline when possible, otherwise on the `io-wq` worker pool.
  - `## Going faster` — registered (fixed) files and buffers to avoid per-operation lookups and pinning; `IORING_SETUP_SQPOLL`, where a kernel thread drains the submission ring so steady-state I/O needs no syscalls at all; `IORING_SETUP_IOPOLL` for polled block I/O (link `./nvme-in-the-kernel.md`). Each with its cost.
  - `## liburing` — the user-space library nearly everyone uses instead of raw rings. A ≤ 30-line ` ```c ` example reading a file with `io_uring_get_sqe`, `io_uring_prep_read`, `io_uring_submit`, and `io_uring_wait_cqe`. **Verify every call against the current liburing via context7.**
  - `## Compared` — `<Tabs>` with three tabs, each giving the model, what it can and cannot do, and the syscall count per operation:
    - **`epoll` + non-blocking I/O** — readiness, sockets and pipes only;
    - **POSIX AIO** — glibc emulates it with threads, and the kernel `aio` interface is limited mostly to `O_DIRECT`;
    - **`io_uring`** — completion, anything.
  - `## The security story` — a large, fast-moving attack surface. Say plainly that several major deployments restricted or disabled it after a run of vulnerabilities, cite the sources, and describe the `kernel.io_uring_disabled` sysctl and the `io_uring_group` control. **Verify both names and the version they arrived in.** Defensive framing only; no exploit detail.
  - `## Misconceptions` **[Misc]** —
    1. "`io_uring` makes every workload faster." It removes crossings; a workload doing few large I/Os has few crossings to remove.
    2. "`io_uring` is only for storage." Networking, `accept`, timeouts and more are opcodes too.
    3. "`SQPOLL` is free performance." It is a kernel thread spinning on a CPU.
- **Anchor:** a Mermaid `sequenceDiagram` — Application, SQ ring (shared memory), Kernel, CQ ring (shared memory) — with the application placing three SQEs, one `io_uring_enter`, the kernel consuming them and later posting three CQEs, and the application reaping them with no further syscall. Caption: "Three I/O operations with one system call: requests and results cross in shared rings rather than through the syscall boundary."
- **KernelFacts:**
  - `structure` — `[["struct io_uring_sqe", "include/uapi/linux/io_uring.h"], ["struct io_ring_ctx", "include/linux/io_uring_types.h"]]`
  - `path` — `"io_uring_enter() → io_submit_sqes() → io_issue_sqe() → opcode handler (io_read()) → io_req_complete_post() → CQE"` (verify each name)
  - `observe` — `cat /proc/sys/kernel/io_uring_disabled; grep -i uring /proc/kallsyms | head -3`
  - `trap` — "`io_uring` being present in the kernel does not mean it is usable: `kernel.io_uring_disabled` and container seccomp profiles commonly block it. Production code needs a fallback path, and an `EPERM` from `io_uring_setup` is a policy decision, not a bug."
- **References:**
  - Axboe, *"Efficient IO with io_uring"* (`https://kernel.dk/io_uring.pdf`) — the original design document by its author; 2019, so the opcode list is far longer now.
  - `https://man7.org/linux/man-pages/man7/io_uring.7.html` — the interface overview, from liburing's man pages.
  - `https://github.com/axboe/liburing` — the library and its examples; **context7-verified API, dated.**
  - LWN, *"Ringing in a new asynchronous I/O API"* (`https://lwn.net/Articles/776703/`) — the 2019 introduction, useful for the design argument against kernel AIO.
  - Google Security Blog, *"Learnings from kCTF VRP's 42 Linux kernel exploits submissions"* (2023) — the source for io_uring's share of submitted exploits and why Google restricted it; **verify URL and figures before citing.**

- [ ] **Step 1: Write `buffered-direct-and-alignment.md`** to the brief above. Run the WAH `dd` comparison on a real disk (not tmpfs — check with `df .`) and paste the real throughput and `/proc/meminfo` lines.
- [ ] **Step 2: Run the context7 verification for `io_uring`.** Resolve the liburing library id, then query for the current setup/submit/wait API, the SQPOLL and IOPOLL flags, and registered buffers. Note the date. Cross-check against `<Src file="include/uapi/linux/io_uring.h" />` at v6.18 — the source is the tiebreaker.
- [ ] **Step 3: Compile and run the liburing example** (`cc -o uring-read uring-read.c -luring`) against a real file, so the listing on the page is known to work.
- [ ] **Step 4: Write `io-uring.md`** to the brief above, dating the context7 check in `## References`.
- [ ] **Step 5: Verify every symbol and version claim** — `iomap_dio_rw`, `iomap_dio`, `iomap_dio_bio_iter`, `__blkdev_direct_IO`, `STATX_DIOALIGN`, `stx_dio_mem_align`, `stx_dio_offset_align`, `balance_dirty_pages`, `io_uring_sqe`, `io_uring_cqe`, `io_ring_ctx`, `io_submit_sqes`, `io_issue_sqe`, `io_read`, `io_req_complete_post`, `IORING_SETUP_SQPOLL`, `IORING_SETUP_IOPOLL`, `io_uring_disabled`, `io_uring_group`, and the PostgreSQL setting name.
- [ ] **Step 6: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 7: Commit**

```bash
git add docs/linux/12-block-layer-and-storage
git commit -m "docs: write buffered and direct I/O, and io_uring"
```

---

## Task 13: Folder 12 — device mapper and LVM, and software RAID

**Files:**
- Modify: `docs/linux/12-block-layer-and-storage/device-mapper-and-lvm.md`
- Modify: `docs/linux/12-block-layer-and-storage/software-raid.md`

**Interfaces:**
- Consumes: `12/the-bio` (Task 10); `computer-science/storage/raid-and-redundancy` (Task 2) — **RAID theory is owned there, including the parity arithmetic and the write-hole explanation; this page links and never re-derives them.**
- Produces: `12/device-mapper-and-lvm` and `12/software-raid`, both leaves of the folder's graph.

### `device-mapper-and-lvm.md` — Device Mapper and LVM **[Lab host=qemu]**

- **Opens with:** device mapper is a generic way to make one block device out of others. A *table* maps ranges of a virtual device's sectors to *targets* — "pass this range through to that device at this offset", "encrypt it", "keep a copy-on-write snapshot of it" — and each target is a small kernel module that rewrites `bio`s. LVM, dm-crypt, thin provisioning, and much of what container storage drivers used to do are all tables loaded into device mapper by user-space tools.
- **Sections:**
  - `## Tables and targets` — a table line is `start length target args…`, in 512-byte sectors. The mapped device's `submit_bio` looks up the target for each `bio`'s sector range and calls its `.map` method (`struct target_type`), which remaps, clones, or queues the `bio`. Show one real line from the lab.
  - `## The targets that matter` — a **table**: `linear`, `striped`, `mirror`/`raid`, `snapshot`, `thin-pool`/`thin`, `crypt`, `cache`/`writecache`, `integrity`, `verity` — each with what it does to a `bio` and its best-known user.
  - `## LVM is user space` — physical volumes, volume groups and logical volumes exist only in LVM's on-disk metadata. What the kernel sees is dm tables LVM computes and loads through `/dev/mapper/control`. That is why `dmsetup table` is the ground truth when LVM tooling and reality disagree.
  - `## Snapshots and thin provisioning` — classic snapshots copy on first write into an exception store (slow with many snapshots); thin pools allocate blocks on demand from shared data plus metadata devices, and snapshot cheaply. The failure mode worth stating: an over-provisioned thin pool running out of data or metadata space.
  - `## dm-crypt in the stack` — encryption as a target: `bio`s are encrypted on a workqueue (`kcryptd`) and passed down, so everything above sees plaintext and everything below sees ciphertext. Where LUKS headers fit (user space, `cryptsetup`), and why stacking order (encrypt under RAID versus over it) matters.
  - `<Lab host="qemu" title="Read the tables LVM builds" time="25 min">` — in the full-system Debian VM with the scratch disk at `/dev/vdb`.

    :::danger[Destroys data on the target device]
    `pvcreate`, `vgcreate` and `cryptsetup luksFormat` overwrite the device's contents. Run `lsblk` first and confirm `/dev/vdb` is the empty scratch disk you attached. On the wrong device these commands are not recoverable without a backup — which is why this lab is QEMU-only.
    :::

    1. `sudo pvcreate /dev/vdb && sudo vgcreate lab /dev/vdb && sudo lvcreate -L 512M -n one lab`;
    2. `sudo dmsetup table` and `sudo dmsetup ls --tree` — read the `linear` line field by field;
    3. `sudo lvcreate -s -L 128M -n snap lab/one`, then `dmsetup table` again, showing the `snapshot-origin` and `snapshot` targets that appeared;
    4. `lsblk` showing the tree;
    5. clean up with `lvremove`, `vgremove`, `pvremove`.

    Real output for every step. "If it fails": `lvm2` is not installed by default on cloud images; `pvcreate` refuses a device with an existing partition table unless wiped (`wipefs -a`, again on the scratch disk only).
- **Anchor:** a Mermaid `flowchart TB` of a real stack from the lab: a filesystem on an LV, the LV as a dm `linear` device mapping onto `/dev/vdb` at an offset, plus the snapshot's `snapshot-origin` and `snapshot` devices and its COW store, each node labelled with its `dm-N` name and target type from the lab's own `dmsetup ls --tree` output. Caption: "What `lvcreate` and `lvcreate -s` actually built: device-mapper targets stacked on the scratch disk, as `dmsetup` reports them."
- **KernelFacts:**
  - `structure` — `[["struct target_type", "include/linux/device-mapper.h"], ["struct dm_table", "drivers/md/dm-core.h"]]`
  - `path` — `"submit_bio(dm-N) → dm_submit_bio() → __split_and_process_bio() → ti->type->map() → linear_map() → submit_bio_noacct(underlying)"` (verify each name)
  - `observe` — `sudo dmsetup table && sudo dmsetup ls --tree`
  - `trap` — "An LVM snapshot is not a backup: it lives on the same disks as its origin, and a classic snapshot that fills its copy-on-write space becomes invalid and is dropped. A thin pool that runs out of space can stall or error writes on every volume in it at once."
- **References:**
  - `https://docs.kernel.org/admin-guide/device-mapper/index.html` — every target documented, with table syntax.
  - `https://man7.org/linux/man-pages/man8/dmsetup.8.html` and `man 7 lvmthin` — the ground-truth tool, and thin provisioning's operational rules.
  - `<Src file="drivers/md/dm-linear.c" />` — the simplest target, short enough to read in full.
  - `https://gitlab.com/cryptsetup/cryptsetup/-/wikis/FrequentlyAskedQuestions` — the cryptsetup FAQ on LUKS, dm-crypt layering, and what encryption at this layer protects.

### `software-raid.md` — Software RAID (md) **[Misc]**

- **Opens with:** the RAID levels and their trade-offs are theory, owned by `../../computer-science/storage/raid-and-redundancy.md`. This page is the Linux implementation: the md driver, which turns several block devices into one using a *personality* per level, and the operational reality of running it — resync after an unclean shutdown, rebuild after a failure, and the mechanisms Linux offers against the write hole.
- **Sections:**
  - `## md and its personalities` — `struct mddev` as the array, `struct md_personality` per level (`raid0`, `raid1`, `raid10`, `raid456`), and `md_handle_request` dispatching `bio`s to the personality, which clones and redirects them to member devices. Where arrays come from: `mdadm` writes superblocks to members and assembles them. dm-raid, which reuses md personalities under device mapper, in one sentence.
  - `## A write, in RAID 1 and in RAID 5` — RAID 1: clone the `bio` to each mirror, complete when all finish. RAID 5: the stripe cache (`struct stripe_head`), read-modify-write versus reconstruct-write, and the `raid5d` thread. Keep it to the mechanism, linking the theory page for the parity arithmetic.
  - `## Resync, recovery, and the bitmap` — after an unclean shutdown md must resync (the array cannot know which strips were mid-write); a write-intent bitmap limits that to recently dirty regions. Recovery rebuilds onto a replacement disk. `/proc/sys/dev/raid/speed_limit_min`/`_max` and why a rebuild competes with production I/O.
  - `## Closing the write hole` — md's two mechanisms for RAID 5/6: a journal device (`raid5-cache`) and partial parity log (`raid5-ppl`), with what each costs. State honestly that without one, the write hole the theory page describes is real on md.
  - `## Monitoring a degraded array` — reading `/proc/mdstat` field by field (show a real healthy and degraded example from a VM), `mdadm --detail`, `mdadm --monitor` with mail or a program hook, and the `sync_action` sysfs file for scrubbing (`check`/`repair`) and `mismatch_cnt`.
  - `## md versus the alternatives` — md, dm-raid/LVM RAID, Btrfs multi-device, and hardware RAID, in a short **table** on who owns the metadata, where scrub runs, and whether data checksums exist. Link `../11-vfs-and-filesystems/xfs-and-btrfs.md`.
  - `## Misconceptions` **[Misc]** —
    1. "RAID is a backup." It replicates deletions and corruption instantly.
    2. "A resync after a crash means a disk failed." It means md cannot prove parity is consistent and is checking.
    3. "`mismatch_cnt` > 0 means corruption." On RAID 1 and 10 it can be non-zero harmlessly, for example with swap on the array; it is meaningful only in context.
- **Anchor:** a Mermaid `stateDiagram-v2` of an md array's lifecycle — clean, active, resyncing, degraded, recovering, failed — with the events that move between them (unclean shutdown, member failure, `mdadm --add`, rebuild complete, second failure). Caption: "The states an md array moves through, and the events — a crash, a failed disk, a replacement — that move it."
- **Second visual:** a real `/proc/mdstat` from a degraded RAID 5 in the full-system VM, in a ` ```text ` block with each field annotated. Build a small array on three loop devices or three extra virtio drives to capture it; **scratch devices only.**
- **KernelFacts:**
  - `structure` — `[["struct mddev", "drivers/md/md.h"], ["struct stripe_head", "drivers/md/raid5.h"]]`
  - `path` — `"submit_bio(md0) → md_submit_bio() → md_handle_request() → mddev->pers->make_request() → raid5_make_request() → stripe cache → raid5d"`
  - `observe` — `cat /proc/mdstat && cat /sys/block/md0/md/sync_action 2>/dev/null`
  - `trap` — "A degraded RAID 5 array is fully readable and looks healthy to every application — which is exactly why it goes unnoticed until a second disk fails. Without `mdadm --monitor` or equivalent alerting, md's redundancy quietly becomes RAID 0."
- **References:**
  - `https://docs.kernel.org/admin-guide/md.html` — md's sysfs interface, `sync_action`, bitmaps, and `mismatch_cnt`.
  - `https://man7.org/linux/man-pages/man8/mdadm.8.html` — creation, assembly, monitoring, and replacement.
  - `https://docs.kernel.org/driver-api/md/raid5-ppl.html` and the raid5-cache documentation — the two write-hole mechanisms (verify both paths).
  - Linux RAID wiki (`https://raid.wiki.kernel.org/`) — community operational guidance; **check the page's last-edited date and say so**, as parts of it are old.

- [ ] **Step 1: Run the device-mapper lab** in the full-system VM, confirming `/dev/vdb` with `lsblk` first, and record every step's real output. The anchor diagram is built from that output.
- [ ] **Step 2: Write `device-mapper-and-lvm.md`** to the brief above.
- [ ] **Step 3: Capture real `/proc/mdstat` output** for a healthy and a degraded RAID 5 in the VM (three scratch devices, `mdadm --create`, then `mdadm --fail`). Clean up afterwards.
- [ ] **Step 4: Write `software-raid.md`** to the brief above.
- [ ] **Step 5: Verify every symbol** — `target_type`, `dm_table`, `dm_submit_bio`, `__split_and_process_bio`, `linear_map`, `kcryptd`, `mddev`, `md_personality`, `md_submit_bio`, `md_handle_request`, `stripe_head`, `raid5_make_request`, `raid5d`, `raid5-cache.c`, `raid5-ppl.c`, and the `speed_limit_min`/`sync_action`/`mismatch_cnt` interfaces.
- [ ] **Step 6: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 7: Commit**

```bash
git add docs/linux/12-block-layer-and-storage
git commit -m "docs: write device mapper and LVM, and software RAID"
```

---

## Task 14: Folder 12 — diagnosing I/O problems

**Files:**
- Modify: `docs/linux/12-block-layer-and-storage/diagnosing-io-problems.md`

**Interfaces:**
- Consumes: every earlier page in the folder, plus `07/diagnosing-scheduling-latency` (same investigation shape, and PSI is already introduced there — link it) and `08/writeback-and-fsync` (`balance_dirty_pages` throttling).
- Produces: `12/diagnosing-io-problems`, which Task 24 adds to the "My server is slow" learning path.

### `diagnosing-io-problems.md` — Diagnosing I/O Problems **[WAH]** **[Misc]** **[Lab host=root-required]**

- **Opens with:** "the disk is slow" is a symptom that can live in at least five places:
  - the device;
  - the queue in front of it;
  - a cgroup throttle;
  - writeback throttling your writes to protect memory;
  - an application that is actually CPU-starved.

  The tools each measure one layer of the map in `./the-block-layer-map.md`, and two popular metrics — `iowait` and `%util` — mislead more often than they help. This page is a method, then a worked case.
- **Sections:**
  - `## Where time goes in an I/O` — a request's latency split into queueing time (in blk-mq and the scheduler) and service time (at the device), and why that split — not the total — tells you which layer to fix.
  - `## iostat, field by field` — `r/s`, `w/s`, `rkB/s`, `r_await`, `w_await`, `aqu-sz`, `rrqm/s`, `%util`, all derived from `/proc/diskstats` (link the kernel's `iostats` documentation). Show real output and annotate each column.
  - `## Why %util lies on modern devices` — it is the fraction of time with *at least one* request in flight (`io_ticks`), so a device serving 64 parallel requests at 30% of its capacity reads 100%. It was a saturation metric only for devices that did one thing at a time.
  - `## Why iowait lies` — `iowait` is idle CPU time during which some task on that CPU was blocked in I/O. It is a property of the *CPU*, not the device: it falls when the CPU gets busier, even if I/O got worse, and it says nothing about which device. Say where it is accounted (`nr_iowait`, `io_schedule`) and why PSI replaced it as the signal.
  - `## PSI for I/O` — `/proc/pressure/io` (`some`/`full`, `avg10/60/300`, `total`) and per-cgroup `io.pressure`, as the metric that answers "are tasks losing time waiting on I/O". Link `../07-scheduling/diagnosing-scheduling-latency.md` for how PSI works.
  - `## Per-process and per-request tools` — `pidstat -d` and `iotop` (task I/O accounting), `biolatency` and `biosnoop` from BCC (latency histograms and per-request traces — the observability folder, later in this section, owns eBPF itself; name it in prose), `blktrace` with `blkparse`, and the `block:block_rq_insert`/`block_rq_issue`/`block_rq_complete` tracepoints behind all of them. A **table** mapping each tool to the question it answers and the layer it measures.
  - `## Throttling that looks like a slow disk` — `balance_dirty_pages` pausing writers when dirty memory exceeds its limits (link `../08-memory-management/writeback-and-fsync.md`), writeback throttling (`queue/wbt_lat_usec`), and cgroup `io.max`/`io.latency`. All three show high application latency with an idle device.
  - `## What actually happens` **[WAH]** — a worked investigation, measured in the lab. **Symptom:** an application's writes take 300 ms. **Evidence:**
    1. `iostat` shows modest `w_await` but high application latency;
    2. `/proc/pressure/io` is elevated;
    3. `biolatency` shows device latency in single-digit milliseconds;
    4. `/proc/meminfo` `Dirty` sits at the `dirty_ratio` threshold;
    5. the `writeback:balance_dirty_pages` tracepoint fires for the application's PID.

    **Cause:** the writer is being throttled by dirty-page limits, not by the disk. **Fix options** and their trade-offs. Every number in this section comes from the lab run.
  - `<Lab host="root-required" title="Separate a slow device from a throttled writer" time="30 min">` — on a real Linux host or the full-system VM, against a **file** in a scratch directory (never a raw device):
    1. baseline `iostat -xz 1`, `cat /proc/pressure/io`, `vmstat 1`;
    2. `fio --name=seqw --filename=./fio.test --size=2G --rw=write --bs=1M --ioengine=psync` (buffered) while watching `Dirty` in `/proc/meminfo` and `iostat`;
    3. `sudo biolatency-bpfcc -D 5 1` (Debian's package name; `biolatency` elsewhere);
    4. `sudo perf trace -e 'writeback:balance_dirty_pages' -p $(pgrep -n fio)`;
    5. rerun with `--direct=1` and compare where the latency now shows up;
    6. run `stress-ng --cpu $(nproc) --timeout 30` alongside the direct run and watch `iowait` fall while `biolatency` is unchanged.

    Record real output for each. "If it fails": BCC tools need kernel headers or BTF and root; the `writeback:*` tracepoint may not fire if the host has enough memory that dirty limits are never hit — lower `vm.dirty_bytes` temporarily, restore it afterwards, and say so.
  - `## Misconceptions` **[Misc]** —
    1. "High `iowait` means the disk is the bottleneck." It is idle CPU time and falls when CPUs get busier.
    2. "`%util` at 100% means the device is saturated." On any device that serves requests in parallel, it only means never idle.
    3. "Slow writes mean a slow disk." Dirty-page and cgroup throttling produce identical symptoms on a fast, idle device.
- **Anchor:** a Mermaid `flowchart TB` decision tree:
  - **Is I/O pressure elevated?** → **Is device latency (`biolatency`) high?**
    - yes → device or queue: check `aqu-sz`, the scheduler, and the device itself;
    - no → throttling: check `Dirty` against the limits, cgroup `io.max`/`io.latency`, and wbt.
  - **No pressure?** → the application is not waiting on I/O; go to CPU (link the scheduling page).

  Caption: "Narrowing 'the disk is slow' to a layer in four checks, using signals that do not lie the way `iowait` and `%util` do."
- **KernelFacts:**
  - `structure` — `[["struct disk_stats", "include/linux/part_stat.h"], ["struct psi_group", "include/linux/psi_types.h"]]`
  - `path` — `"write() → generic_perform_write() → balance_dirty_pages_ratelimited() → balance_dirty_pages() → io_schedule_timeout()"`
  - `observe` — `iostat -xz 1 3; cat /proc/pressure/io`
  - `trap` — "An application stalling on writes while `iostat` shows an idle disk is not a contradiction. The kernel is deliberately pausing the writer in `balance_dirty_pages` to keep dirty memory under its limit — the disk never saw the requests that are waiting."
- **References:**
  - `https://docs.kernel.org/admin-guide/iostats.html` — every `/proc/diskstats` field, which is what `iostat` derives its columns from.
  - `https://docs.kernel.org/accounting/psi.html` — PSI's definitions, including I/O pressure.
  - Gregg, *Systems Performance* (2nd ed.), ch. 9 — the disk-analysis methodology, including the `%util` and `iowait` caveats; a purchase.
  - `https://github.com/iovisor/bcc/blob/master/tools/biolatency_example.txt` — `biolatency`'s own worked example output.
  - LWN, *"The iowait problem"* or the PSI introduction (`https://lwn.net/Articles/759781/`) — why PSI was built; **verify the article** before citing.

- [ ] **Step 1: Run the lab** end to end and record every output, including the throttled case the WAH investigation is built from. If you had to lower `vm.dirty_bytes`, record the original value, restore it, and say so on the page.
- [ ] **Step 2: Write `diagnosing-io-problems.md`** to the brief above, with the WAH built from the recorded run.
- [ ] **Step 3: Verify every symbol and interface** — `disk_stats`, `io_ticks`, `psi_group`, `nr_iowait`, `io_schedule`, `balance_dirty_pages`, `balance_dirty_pages_ratelimited`, `io_schedule_timeout`, the `writeback:balance_dirty_pages` tracepoint, the `block:block_rq_*` tracepoints, and `queue/wbt_lat_usec`.
- [ ] **Step 4: Check, build, and confirm folder 12 is complete**

```bash
npm run check:linux && npm run build
rtk run "grep -l 'Not yet written' docs/linux/12-block-layer-and-storage/*.md"
```

Expected: zero findings, a green build, no grep output.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/12-block-layer-and-storage
git commit -m "docs: write diagnosing I/O problems"
```

---
## Task 15: Folder 13 — the network stack map, and `sk_buff`

**Files:**
- Modify: `docs/linux/13-networking-stack/the-network-stack-map.md`
- Modify: `docs/linux/13-networking-stack/sk-buff.md`

**Interfaces:**
- Consumes:
  - `10/how-an-interrupt-reaches-the-kernel` and `10/softirqs` — the receive path begins in a hard IRQ and runs in `NET_RX_SOFTIRQ`, both already explained;
  - `08/slab-slub-and-kmalloc`;
  - `02/the-life-of-a-packet` — the narrative version this folder deepens.
- Produces:
  - `13/the-network-stack-map`, the folder's map page, written first per the spec;
  - `13/sk-buff`, a prerequisite of sockets, both paths, and — transitively — everything else in the folder.

**No-duplication:** protocol semantics (what TCP, IP and Ethernet *are*) are owned by `computer-science/computer-networks/*`. Every page in this folder links there for them and owns only what the kernel does.

### `the-network-stack-map.md` — The Network Stack, Mapped

- **Opens with:** a packet crosses the kernel twice as many layers as most diagrams show, and it crosses them in both directions by different code. This page is the reference map: the socket layer, protocol handlers, IP, netfilter's hooks, routing, the device layer, the queueing discipline, and the driver, drawn for receive and for transmit. It names which page in this folder owns each box. Every later page refers back here, the way `../02-guided-traces/the-life-of-a-packet.md` pointed forward to it.
- **Sections:**
  - `## Two directions, two code paths` — receive is driven from the bottom by interrupts and softirqs and ends by waking a task; transmit is driven from the top by a syscall and may finish in softirq context on another CPU. Which context each stage runs in is the single most useful fact for reading networking code.
  - `## The layers` — a **table**, one row per layer, with columns: what it does on receive, what it does on transmit, the key function or struct, and the owning page.

    | Layer | Key function or struct |
    |---|---|
    | socket | `struct socket` / `struct sock` |
    | transport | TCP/UDP |
    | IP | `ip_rcv` / `ip_output` |
    | netfilter hooks | — |
    | routing | FIB |
    | neighbour | — |
    | device layer | `netif_receive_skb` / `dev_queue_xmit` |
    | qdisc | — |
    | driver and NAPI | — |
    | NIC | — |
  - `## The control plane` — routing tables, neighbour entries, firewall rules and interface configuration arrive over netlink from `ip`, `nft` and friends. The datapath consults that state; it does not create it. Name `rtnetlink` in one sentence.
  - `## Where the hooks are` — the five netfilter hooks marked on the map (PRE_ROUTING, LOCAL_IN, FORWARD, LOCAL_OUT, POST_ROUTING) so that later pages can refer to "the hook at X", plus the XDP and tc attach points marked as eBPF territory. The eBPF folder owns them; name it in prose.
  - `## Namespaces cut across all of it` — every layer above the driver exists per network namespace. Link forward to `./network-namespaces-and-virtual-devices.md`.
  - `## What this folder does not cover` — protocol semantics (link `../../computer-science/computer-networks/intro.md`), NIC driver internals (a later folder, in prose), and XDP/BPF programs (a later folder, in prose).
- **Anchor:** a Mermaid `flowchart TB` in two columns — receive rising from the NIC on the left, transmit descending from `send()` on the right — sharing the socket at the top and the NIC at the bottom. Netfilter hooks are drawn as labelled diamonds on both paths, with the routing decision between PRE_ROUTING and LOCAL_IN/FORWARD. Each stage is annotated with its execution context (hard IRQ, softirq, process). Caption: "The kernel network stack in both directions, with netfilter's hooks and the execution context of every stage."
- **KernelFacts:**
  - `structure` — `[["struct sk_buff", "include/linux/skbuff.h"], ["struct net_device", "include/linux/netdevice.h"]]`
  - `path` — `"RX: NIC → napi_poll() → netif_receive_skb() → ip_rcv() → tcp_v4_rcv() → socket queue · TX: tcp_sendmsg() → ip_queue_xmit() → dev_queue_xmit() → ndo_start_xmit()"`
  - `observe` — `ip -s link show && cat /proc/net/softnet_stat | head -4`
  - `trap` — "Receive processing for a packet addressed to your process usually runs on whatever CPU took the NIC's interrupt, in softirq context, charged to no process at all — which is why a busy network server can show high `si` in `top` while its own threads look idle."
- **References:**
  - `https://docs.kernel.org/networking/index.html` — the networking documentation index at the pinned version.
  - `https://docs.kernel.org/networking/scaling.html` — RSS, RPS, RFS and XPS; the clearest in-tree description of how packets are spread across CPUs.
  - Benvenuti, *Understanding Linux Network Internals* (O'Reilly, 2005) — the deepest book on the stack's structure; very old — use it for architecture, never for function names.
  - Damato, *"Monitoring and Tuning the Linux Networking Stack: Receiving Data"* (packagecloud blog, 2016) — an exhaustive walk of the receive path with real code; predates v6.18, so verify every name it gives.

### `sk-buff.md` — `sk_buff`: The Packet Container

- **Opens with:** every packet in the kernel lives in a `struct sk_buff`, and the structure is designed around one observation: a packet gains headers on the way down and loses them on the way up. So the data area is allocated with spare room at the front, and "adding a header" is moving a pointer backwards, not copying the payload. Once you can see the four pointers and the shared-info tail, you can read any networking code in the tree.
- **Sections:**
  - `## Metadata and data are separate` — the `sk_buff` struct itself (metadata: device, protocol, timestamps, socket, header offsets, lengths) points at a separately allocated data buffer. Several `sk_buff`s may point at one buffer.
  - `## head, data, tail, end` — the four positions and the regions they bound: headroom, packet data, tailroom, then `struct skb_shared_info` at `end`. The helpers: `skb_reserve` (make headroom), `skb_put` (extend at the tail), `skb_push` (prepend a header), `skb_pull` (strip one). Note that `tail` and `end` are offsets on 64-bit builds (`sk_buff_data_t`). **Anchor** here.
  - `## Header offsets` — `mac_header`, `network_header`, `transport_header` stored as offsets from `head`, with accessors (`skb_network_header`, `ip_hdr`, `tcp_hdr`). Why these are set as each layer parses the packet rather than computed on demand.
  - `## Linear and non-linear data` — `len` versus `data_len`: payload can live in page fragments (`skb_shinfo(skb)->frags[]`) or a chain of further `sk_buff`s (`frag_list`), so a 64 KB GRO packet need not be one contiguous allocation. `skb_headlen`, and why code must call `pskb_may_pull` before reading headers that might not be linear.
  - `## Clone versus copy` — `skb_clone` shares the data buffer (reference-counted by `dataref` in shared info) and duplicates only metadata — cheap, used by `tcpdump` taps and retransmit queues. `skb_copy`/`pskb_copy` duplicate data. `skb_cow`/`skb_unshare` before modifying a shared buffer. This is how "one packet, many readers" avoids copies.
  - `## Allocation` — `alloc_skb` and `__alloc_skb` from dedicated slab caches (link `../08-memory-management/slab-slub-and-kmalloc.md`), `napi_alloc_skb` on the receive path, and `build_skb`/`napi_build_skb` wrapping a driver's already-filled page. Page pools in one sentence.
  - `## The fields that matter` — a Mermaid `classDiagram` or grouped **table** of about fifteen fields grouped by concern: position (`head`, `data`, `tail`, `end`, `len`, `data_len`), layering (`mac_header`, `network_header`, `transport_header`, `protocol`), ownership (`sk`, `dev`, `destructor`), routing (`_skb_refdst`), offload (`ip_summed`, `csum`, `gso_size` in shared info), and lifecycle (`users`). **Verify each field name at v6.18** — several live in unions or `struct_group`s.
- **Anchor:** a WaveDrom `reg` strip of one buffer drawn as byte regions — headroom, Ethernet header, IP header, TCP header, payload, tailroom, `skb_shared_info` — with `head`, `data`, `tail` and `end` marked at the boundaries. Label the widths as illustrative, not to scale. Caption: "One received TCP segment inside its `sk_buff` buffer: the headroom that makes `skb_push` cheap, the four boundary pointers, and the shared info at the end."
- **Second visual:** a Mermaid `flowchart LR` showing `skb_push` on the transmit path — TCP header, then IP header, then Ethernet header prepended by moving `data` backwards through the same buffer — beside `skb_pull` on receive moving `data` forwards. Caption: "Adding and stripping headers by moving one pointer: the payload never moves."
- **KernelFacts:**
  - `structure` — `[["struct sk_buff", "include/linux/skbuff.h"], ["struct skb_shared_info", "include/linux/skbuff.h"]]`
  - `path` — `"RX: napi_alloc_skb() → skb_put() → eth_type_trans() (skb_pull) · TX: skb_reserve() → skb_push() per header → dev_queue_xmit()"`
  - `observe` — `grep -E '^skbuff' /proc/slabinfo`
  - `trap` — "`skb->len` is not the size of the linear buffer. Reading a header by pointer from `skb->data` without `pskb_may_pull()` works on every test packet that happened to be linear, and reads past the buffer on the GRO-merged or fragmented one that was not."
- **References:**
  - `https://docs.kernel.org/networking/skbuff.html` — the kernel-doc for `struct sk_buff`, including the ownership and cloning rules (verify the page exists at v6.18; otherwise cite the header's own comment block).
  - `<Src file="include/linux/skbuff.h" symbol="sk_buff" />` — the structure, whose opening comment is the best single explanation of the shared-buffer model.
  - `<Src file="net/core/skbuff.c" symbol="skb_clone" />` — cloning, and the `dataref` accounting.
  - LWN, *"Network packet memory management"* or the page-pool coverage — **verify an article URL before citing**; fall back to `https://docs.kernel.org/networking/page_pool.html`.

- [ ] **Step 1: Write `the-network-stack-map.md`** to the brief above.
- [ ] **Step 2: Write `sk-buff.md`** to the brief above.
- [ ] **Step 3: Verify every symbol and field** — `sk_buff`, `skb_shared_info`, `skb_shinfo`, `sk_buff_data_t`, `skb_reserve`, `skb_put`, `skb_push`, `skb_pull`, `skb_headlen`, `pskb_may_pull`, `skb_clone`, `skb_copy`, `pskb_copy`, `skb_cow`, `skb_unshare`, `alloc_skb`, `__alloc_skb`, `napi_alloc_skb`, `build_skb`, `napi_build_skb`, `eth_type_trans`, `net_device`, `napi_poll`, `netif_receive_skb`, `ip_rcv`, `tcp_v4_rcv`, `tcp_sendmsg`, `ip_queue_xmit`, `dev_queue_xmit`, `ndo_start_xmit` — and every field listed in the field table.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write the network stack map and sk_buff"
```

---

## Task 16: Folder 13 — sockets in the kernel, and the receive path

**Files:**
- Modify: `docs/linux/13-networking-stack/sockets-in-the-kernel.md`
- Modify: `docs/linux/13-networking-stack/the-receive-path.md`

**Interfaces:**
- Consumes:
  - `13/sk-buff` (Task 15);
  - `11/the-four-objects` (a socket is a `struct file`);
  - `computer-science/computer-networks/sockets-and-the-application-boundary` (Task 3) — **the API semantics are owned there, so this page never re-explains `listen`/`accept`/`connect` from the caller's side**;
  - `10/softirqs`, `10/interrupt-affinity-and-balancing`, `06/process-states-and-wait-queues`.
- Produces:
  - `13/sockets-in-the-kernel`, a prerequisite of the transmit path and TCP;
  - `13/the-receive-path`, a prerequisite of TCP, netfilter, and diagnosing — and the link target for the Task 21 forward-reference fixes in `10/threaded-irqs` and `10/interrupt-affinity-and-balancing`.

### `sockets-in-the-kernel.md` — Sockets in the Kernel **[WAH]** **[Misc]**

- **Opens with:** a socket descriptor points at a `struct file`, like any other descriptor. Behind it the kernel keeps two objects with deliberately different jobs:
  - **`struct socket`** faces the VFS and the syscall layer — it is what `read`, `poll` and `close` see.
  - **`struct sock`** faces the protocol — it holds the queues, the buffers, the state, and the wait queue that incoming data wakes.

  The split is how one socket API fronts TCP, UDP, UNIX sockets, and netlink without any of them knowing about files.
- **Sections:**
  - `## From descriptor to protocol` — fd → `struct file` (in `sockfs`, via `sock_alloc_file`) → `struct socket` (`ops`, `state`, `sk`) → `struct sock` → protocol-specific extensions. `struct inet_sock` and `struct tcp_sock` embed their parent as the first member, and `tcp_sk()` casts — link `../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md`.
  - `## Two dispatch tables` — `struct proto_ops` (the socket-API operations for an address family and type: `inet_stream_ops`) and `struct proto` (the protocol's implementation: `tcp_prot`). `socket()` picks both: `__sys_socket` → `sock_create` → the family's `create` (`inet_create`), which searches the protocol switch.
  - `## Buffers and accounting` — `sk_receive_queue`, `sk_write_queue`, `sk_rcvbuf`, `sk_sndbuf`, `sk_rmem_alloc`, `sk_wmem_queued`. Memory is charged as `sk_buff`s are queued, a full receive buffer causes drops or a zero TCP window, and `net.core.rmem_max` versus `net.ipv4.tcp_rmem` differ. Per-protocol global memory pressure (`tcp_mem`) in one paragraph.
  - `## Blocking and waking` — a `recv` on an empty queue sleeps on the socket's wait queue (`sk_wait_data`; link `../06-processes-and-threads/process-states-and-wait-queues.md`). When the receive path queues data it calls `sk->sk_data_ready` (usually `sock_def_readable`), which wakes the sleeper. Draw the **anchor** here.
  - `## How epoll hooks in` — `epoll_ctl` calls the file's `poll` (`sock_poll` → `tcp_poll`), which registers an entry on the same wait queue with `ep_poll_callback` as its wake function. So the wakeup that would have woken a blocked `recv` instead marks the fd ready on an epoll instance. One mechanism, two consumers.
  - `## Listening sockets` — `listen` allocates the accept queue; incoming handshakes create lightweight request socks (`struct request_sock`) rather than full sockets, and a full `sock` exists only when the handshake completes and the connection enters the accept queue. The backlog bound is `min(backlog, net.core.somaxconn)`, and SYN cookies apply when the SYN side overflows. Link the CS page for the two-queue concept.
  - `## What actually happens` **[WAH]** — `nc -l 8080` in one terminal and `nc localhost 8080` in another. With `strace -e trace=socket,bind,listen,accept4,read` on the server and `ss -tlnpe` / `ss -tnpe` snapshots, walk through the kernel objects that exist at each step: after `listen`, one `sock` in `LISTEN`; during the handshake, a request sock; after `accept4` returns, a new `struct file`/`socket`/`sock` triple with its own fd. Show the real `ss` columns (`Recv-Q`/`Send-Q` mean different things for listening sockets — say what).
  - `## Misconceptions` **[Misc]** —
    1. "The `listen` backlog is the maximum number of connections." It bounds connections waiting to be accepted, and it is capped by `somaxconn`.
    2. "A socket and a connection are the same object." A listening socket spawns a new socket per accepted connection.
    3. "`Recv-Q` in `ss` is always unread bytes." For a listening socket it is the current accept-queue length.
- **Anchor:** a Mermaid `sequenceDiagram` — Application, VFS/`struct socket`, `struct sock` wait queue, Receive path (softirq) — showing a blocking `recv` sleeping, a segment arriving and being queued, `sk_data_ready` waking the task, and `recv` copying data out. A second lane shows the same wakeup delivered to `ep_poll_callback` instead. Caption: "One wakeup, two consumers: how arriving data wakes a blocked `recv` or marks a descriptor ready in `epoll`."
- **Second visual:** a Mermaid `classDiagram` of `file` → `socket` → `sock` → `inet_sock` → `tcp_sock`, with `proto_ops` and `proto` attached, showing the embedding and the four or five fields per class that the page discusses.
- **KernelFacts:**
  - `structure` — `[["struct socket", "include/linux/net.h"], ["struct sock", "include/net/sock.h"]]`
  - `path` — `"socket() → __sys_socket() → sock_create() → inet_create() → sk_alloc() → sock_alloc_file() → fd"`
  - `observe` — `ss -tlnpe && ss -tnpim | head -20`
  - `trap` — "Raising the `listen()` backlog in your application does nothing past `net.core.somaxconn`, and the kernel silently truncates it — the value in `ss -ltn`'s `Send-Q` column shows what you actually got."
- **References:**
  - `<Src file="net/socket.c" symbol="__sys_socket" />` — socket creation and the file glue.
  - `<Src file="include/net/sock.h" symbol="sock" />` — `struct sock`, with its field comments.
  - `https://man7.org/linux/man-pages/man7/socket.7.html` and `man 2 listen` — the options and the backlog/`somaxconn` note, from the caller's side.
  - `https://man7.org/linux/man-pages/man7/epoll.7.html` — the readiness contract this page's second consumer implements.

### `the-receive-path.md` — The Receive Path **[WAH]** **[Misc]**

- **Opens with:** a busy NIC can deliver a million packets a second, and an interrupt per packet would spend the whole machine on interrupt entry. So Linux takes one interrupt, turns it off, and polls the device from a softirq until the ring is empty or the budget is spent (NAPI). Then it merges related segments (GRO) and hands them up through IP and TCP in batches, finally waking the reader. This page follows a packet along that path and marks every place it can be dropped.
- **Sections:**
  - `## From wire to ring` — the driver pre-posts buffers into an RX descriptor ring; the NIC DMAs frames into them and marks descriptors done (the DMA API is a later folder's, in prose). Multi-queue NICs hash flows across several rings (RSS), each with its own MSI-X vector — link `../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md`.
  - `## NAPI: interrupt once, then poll` — the handler calls `napi_schedule` and masks the queue's interrupt; `NET_RX_SOFTIRQ` runs `net_rx_action`, which calls the driver's poll function with a budget (`net.core.netdev_budget`, `netdev_budget_usecs`). The driver re-enables interrupts only when a poll finishes under budget. Threaded NAPI (`/sys/class/net/<dev>/threaded`) in one paragraph. Link `../10-interrupts-time-and-deferred-work/softirqs.md` and `../10-interrupts-time-and-deferred-work/threaded-irqs.md`.
  - `## GRO` — `napi_gro_receive` merges segments of the same flow into one large `sk_buff` before the stack sees them, so TCP processes one 64 KB "packet" instead of 44 small ones. What breaks GRO (out-of-order segments, differing options) and its cost for forwarding workloads.
  - `## Up through the device layer` — `netif_receive_skb` → `__netif_receive_skb_core`: taps first (`ptype_all` — this is where `tcpdump` sees the packet, *before* netfilter), then VLAN, bridge/macvlan rx handlers, then the protocol handler by ethertype (`ip_rcv`).
  - `## IP and the first routing decision` — `ip_rcv` → NF_INET_PRE_ROUTING → `ip_rcv_finish` → route lookup → `ip_local_deliver` → NF_INET_LOCAL_IN → `tcp_v4_rcv`. Or `ip_forward` → FORWARD for a router. Link `./netfilter-and-nftables.md` and `./routing-and-neighbours.md`.
  - `## TCP and the socket` — `tcp_v4_rcv` looks up the socket, then:
    - if a user task holds the socket lock, the segment goes to the backlog;
    - otherwise `tcp_rcv_established` runs its fast path, queues data on `sk_receive_queue`, and calls `sk_data_ready`.

    Link `./sockets-in-the-kernel.md` for the wakeup and `./tcp-in-the-kernel.md` for ACK generation.
  - `## Steering: RSS, RPS, RFS` — hardware spreading (RSS), software spreading when hardware cannot (RPS, `/sys/class/net/<dev>/queues/rx-N/rps_cpus`), and flow steering toward the CPU the reading thread runs on (RFS, `net.core.rps_sock_flow_entries`). Link `../10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md` for the interrupt-placement layer; this page owns the network-specific steering.
  - `## Where packets are dropped` — a **table** of drop points, each with the counter that records it:
    - ring full (`ethtool -S` `rx_missed`/`rx_no_buffer`-style counters, driver-specific);
    - backlog full (`/proc/net/softnet_stat` column 2);
    - budget exhausted (`time_squeeze`, column 3);
    - netfilter drop;
    - no route;
    - socket receive buffer full (`TcpExtTCPRcvQDrop`, `UdpRcvbufErrors`);
    - listen-queue overflow (`TcpExtListenOverflows`).

    Then `kfree_skb_reason` and `enum skb_drop_reason`, which make every drop attributable through the `skb:kfree_skb` tracepoint (verify the enum's header location at v6.18).
  - `## What actually happens` **[WAH]** — a web server's `recv()` returning with a request. Use `perf trace`/`perf record -g` on the server during `curl` requests, or `bpftrace -e 'kprobe:tcp_v4_rcv { @[cpu] = count(); }'`, to show:
    1. which CPU processed receive, and that it may differ from the CPU the server thread runs on;
    2. `/proc/softirqs` `NET_RX` counters climbing;
    3. that the wakeup crossed CPUs.

    Real output from a real run; the observability folder owns the tools (named in prose).
  - `## Misconceptions` **[Misc]** —
    1. "One packet, one interrupt." Under load it is one interrupt per poll cycle, which may cover hundreds of packets.
    2. "`tcpdump` shows what my application received." It taps before netfilter and before the socket, so it shows packets the firewall or a full buffer then dropped.
    3. "Receive processing runs on my application's CPU." It runs where the interrupt or RPS put it unless RFS steers it.
- **Anchor:** a Mermaid `flowchart TB` of the receive path — NIC → RX ring → hard IRQ (`napi_schedule`) → softirq `net_rx_action` → driver poll → GRO → `__netif_receive_skb_core` (with the tap branch to AF_PACKET) → `ip_rcv` → PRE_ROUTING → routing → LOCAL_IN → `tcp_v4_rcv` → socket queue → `sk_data_ready` → task wakes. Drop points are drawn as red side exits, each labelled with its counter. Caption: "Every stage of receiving a TCP segment, the context each runs in, and the counter that records a drop at each."
- **KernelFacts:**
  - `structure` — `[["struct napi_struct", "include/linux/netdevice.h"], ["struct softnet_data", "include/linux/netdevice.h"]]`
  - `path` — `"irq → napi_schedule() → net_rx_action() → driver poll → napi_gro_receive() → __netif_receive_skb_core() → ip_rcv() → tcp_v4_rcv() → sk_data_ready()"`
  - `observe` — `cat /proc/net/softnet_stat; grep NET_RX /proc/softirqs; nstat -az TcpExtTCPRcvQDrop TcpExtListenOverflows`
  - `trap` — "A rising `time_squeeze` column in `/proc/net/softnet_stat` means `net_rx_action` ran out of budget with packets still waiting — not that packets were dropped. The drops, if any, show up later in the ring or backlog counters, so raising `netdev_budget` fixes one and not the other."
- **References:**
  - `https://docs.kernel.org/networking/napi.html` — NAPI's contract, budgets, and threaded mode.
  - `https://docs.kernel.org/networking/scaling.html` — RSS, RPS and RFS in detail, with the sysfs knobs.
  - Damato, *"Monitoring and Tuning the Linux Networking Stack: Receiving Data"* (packagecloud, 2016) — the exhaustive walk with every counter explained; 2016, so verify function names against v6.18.
  - LWN, *"Packet drop reasons"* or the `kfree_skb_reason` merge coverage — **verify the article URL**; otherwise cite `<Src file="include/net/dropreason-core.h" />` directly.

- [ ] **Step 1: Write `sockets-in-the-kernel.md`** to the brief above. Run the WAH `nc` session with the `strace` and `ss` snapshots for real and paste them.
- [ ] **Step 2: Run the receive-path WAH measurement** on a real Linux host with root (a local `python3 -m http.server` plus a `curl` loop is enough) and record the per-CPU counts and `/proc/softirqs` deltas.
- [ ] **Step 3: Write `the-receive-path.md`** to the brief above.
- [ ] **Step 4: Verify every symbol** — `sock_alloc_file`, `proto_ops`, `proto`, `inet_stream_ops`, `tcp_prot`, `__sys_socket`, `sock_create`, `inet_create`, `sk_alloc`, `inet_sock`, `tcp_sock`, `tcp_sk`, `sk_wait_data`, `sock_def_readable`, `sock_poll`, `tcp_poll`, `ep_poll_callback`, `request_sock`, `napi_struct`, `softnet_data`, `napi_schedule`, `net_rx_action`, `napi_gro_receive`, `netif_receive_skb`, `__netif_receive_skb_core`, `ip_rcv`, `ip_rcv_finish`, `ip_local_deliver`, `ip_forward`, `tcp_v4_rcv`, `tcp_rcv_established`, `kfree_skb_reason`, `skb_drop_reason` — plus the sysctl and sysfs names and the `nstat` counter names.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 6: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write sockets in the kernel and the receive path"
```

---

## Task 17: Folder 13 — the transmit path, and traffic control

**Files:**
- Modify: `docs/linux/13-networking-stack/the-transmit-path.md`
- Modify: `docs/linux/13-networking-stack/traffic-control.md`

**Interfaces:**
- Consumes: `13/sk-buff` (Task 15), `13/sockets-in-the-kernel` (Task 16).
- Produces:
  - `13/the-transmit-path`, a prerequisite of TCP, netfilter, routing, and traffic control;
  - `13/traffic-control`, whose ingress/clsact section is the attach point the eBPF folder will use — **named in prose only.**

### `the-transmit-path.md` — The Transmit Path **[Misc]**

- **Opens with:** `send()` returning tells you your bytes were accepted into a socket buffer — nothing more. From there the kernel:
  1. segments them;
  2. picks a route and a next-hop address;
  3. queues them in a queueing discipline;
  4. hands them to a driver that DMAs them to the NIC;
  5. frees them only when the NIC confirms transmission.

  Several of those stages exist to *limit* how much data is queued, because on the transmit side excess buffering is a latency bug, not a throughput feature.
- **Sections:**
  - `## From send() into TCP` — `tcp_sendmsg` copies user data into `sk_buff`s on the write queue (or references pages with `MSG_ZEROCOPY`/`sendfile`), respecting `sk_sndbuf`, then `tcp_push` → `tcp_write_xmit` decides how much may go now given the congestion window, the receive window and pacing. Link `./tcp-in-the-kernel.md` for those windows.
  - `## Segmentation offload` — TCP hands down large "super-packets" (TSO/GSO: `gso_size` in shared info) and the NIC, or `skb_gso_segment` in software, cuts them into MTU-sized frames. Checksum offload (`ip_summed`) in one paragraph. Why `tcpdump` on the sender shows 64 KB packets that never existed on the wire.
  - `## IP, routing, and the neighbour` — `ip_queue_xmit` uses the socket's cached route (`sk_dst_cache`) or looks one up, fills the IP header, passes NF_INET_LOCAL_OUT and then POST_ROUTING (`ip_output`), and `ip_finish_output2` resolves the next hop via the neighbour table (`neigh_output`). Link `./routing-and-neighbours.md`.
  - `## The device layer and the qdisc` — `dev_queue_xmit` → select a TX queue (XPS) → enqueue on that queue's qdisc → `qdisc_run` → `sch_direct_xmit` → `dev_hard_start_xmit` → driver `ndo_start_xmit`. When the driver's ring is full it stops the queue and the qdisc holds packets. Link `./traffic-control.md`. The `dev_queue_xmit_nit` tap: where outgoing packets are copied to `tcpdump`, after the qdisc.
  - `## Keeping queues short: TSQ and BQL` — TCP Small Queues limits how much one socket may have below it (`net.ipv4.tcp_limit_output_bytes`); Byte Queue Limits dynamically sizes the driver ring's usable depth (`/sys/class/net/<dev>/queues/tx-N/byte_queue_limits/`). Together they push queueing up into the qdisc, where fq_codel can manage it. The bufferbloat argument, in one paragraph.
  - `## Completion` — the NIC signals transmit completion, the driver frees `sk_buff`s in its NAPI poll (`napi_consume_skb`), the queue is woken if it was stopped, and the socket's write-memory accounting decreases — which is what unblocks a sender waiting on `sk_sndbuf`.
  - `## Misconceptions` **[Misc]** —
    1. "`send()` returning means the data was sent." It was copied into a socket buffer.
    2. "Bigger transmit queues (`txqueuelen`) improve throughput." They mostly add latency; BQL and fq_codel exist because shorter queues behave better.
    3. "TSO means the NIC implements TCP." It only splits already-built segments; all TCP state stays in the kernel.
- **Anchor:** a Mermaid `flowchart TB` of the transmit path — `send()` → `tcp_sendmsg` → write queue → `tcp_write_xmit` (cwnd/rwnd/pacing gate) → `ip_queue_xmit` → LOCAL_OUT → routing (cached `dst`) → POST_ROUTING → neighbour → `dev_queue_xmit` → XPS queue select → qdisc → `dev_hard_start_xmit` (tap branch to AF_PACKET) → driver ring (BQL gate) → NIC → TX-completion interrupt → free. TSQ and BQL are drawn as labelled gates. Caption: "Transmitting a TCP segment, with the three gates — congestion control, TSQ, and BQL — that decide how much is allowed to queue at each level."
- **KernelFacts:**
  - `structure` — `[["struct Qdisc", "include/net/sch_generic.h"], ["struct netdev_queue", "include/linux/netdevice.h"]]`
  - `path` — `"tcp_sendmsg() → tcp_write_xmit() → tcp_transmit_skb() → ip_queue_xmit() → ip_finish_output2() → neigh_output() → dev_queue_xmit() → dev_hard_start_xmit() → ndo_start_xmit()"`
  - `observe` — `ethtool -k eth0 | grep -E 'segmentation|checksum'` and `grep -H . /sys/class/net/eth0/queues/tx-0/byte_queue_limits/*` (substitute the real interface)
  - `trap` — "`tcpdump` on a sending host shows the giant pre-segmentation packets that TSO/GSO hand to the driver, not what went on the wire. A 64 KB 'packet' in a capture is not an MTU problem — capture on the receiver or a mirror port to see the real frames."
- **References:**
  - `https://docs.kernel.org/networking/segmentation-offloads.html` — TSO, GSO, and the other offloads, defined.
  - `https://docs.kernel.org/networking/scaling.html` — XPS, the transmit half of CPU steering.
  - LWN, *"TCP small queues"* (`https://lwn.net/Articles/507065/`) and *"Network transmit queue limits"* (`https://lwn.net/Articles/454390/`) — the design of TSQ and BQL; 2012 and 2011.
  - `<Src file="net/core/dev.c" symbol="__dev_queue_xmit" />` — the device-layer transmit entry and qdisc handoff.

### `traffic-control.md` — Traffic Control and qdiscs

- **Opens with:** every transmit queue has a queueing discipline in front of it, and it decides three things: which packet goes next, how long packets may wait, and which ones are dropped when the queue is full. The default choice decides whether a busy upload makes every other connection on the machine lag. Traffic control is the subsystem that lets you choose the discipline, build hierarchies of them, and classify traffic between them.
- **Sections:**
  - `## Where the qdisc sits` — between `dev_queue_xmit` and the driver (from `./the-transmit-path.md`). `struct Qdisc` with its `enqueue`/`dequeue` operations (`struct Qdisc_ops`), one per TX queue on multi-queue devices (`mq`). The kernel's compiled-in default versus the `net.core.default_qdisc` sysctl commonly set by systemd. **Verify both the kernel default and what the reference distribution sets.**
  - `## Classless qdiscs` — a **table**: `pfifo_fast` (three bands, no fairness), `fq` (per-flow fair queueing with pacing, what TCP BBR expects), `fq_codel` (per-flow queues plus CoDel's sojourn-time dropping — target 5 ms, interval 100 ms per RFC 8290), `cake` (fq_codel plus shaping and per-host fairness in one), `noqueue` (virtual devices). What each optimises.
  - `## Why CoDel works` — drop based on how long packets have *waited*, not how many are queued, so a queue that drains quickly is never punished and a standing queue is. Bufferbloat, and why this is the fix rather than smaller buffers.
  - `## Classful qdiscs and filters` — `htb` for hierarchical rate limits with borrowing; classes as leaves with their own qdiscs; `tc filter` (`u32`, `flower`, `fw`, `bpf`) classifying packets into classes via `tcf_classify`. A real three-line `tc` example that caps one port's traffic.
  - `## Shaping versus policing` — shaping *delays* excess egress traffic in a queue (smooth, adds latency); policing *drops* excess traffic (instant, lossy, and the only option on ingress). Why you cannot shape traffic you receive, and IFB as the workaround.
  - `## Ingress and clsact` — the ingress hook (`ingress` or `clsact` qdisc) where filters, and eBPF programs, attach to received packets after the driver and before the stack. Name the eBPF folder in prose (unlinked).
  - `## netem, for testing` — adding delay, jitter, loss and reordering to an interface to reproduce bad networks. A two-line example with `tc qdisc add dev lo root netem delay 100ms`, and a `:::warning` about applying it to the interface you are logged in through.
- **Anchor:** a Mermaid `flowchart LR` of an `htb` hierarchy — root qdisc → rate-limited parent class → two child classes (interactive with a guaranteed rate, bulk borrowing the rest) → `fq_codel` leaves — with a `tc filter` classifying by port into each class. Caption: "An htb hierarchy that guarantees interactive traffic a rate, lets bulk traffic borrow what is left, and manages each queue's latency with fq_codel."
- **Second visual:** the classless-qdisc **table** above, as the page's comparison anchor.
- **KernelFacts:**
  - `structure` — `[["struct Qdisc_ops", "include/net/sch_generic.h"], ["struct tcf_proto", "include/net/sch_generic.h"]]`
  - `path` — `"dev_queue_xmit() → __dev_xmit_skb() → q->enqueue() → qdisc_run() → dequeue_skb() → sch_direct_xmit()"`
  - `observe` — `tc -s qdisc show dev eth0 && sysctl net.core.default_qdisc`
  - `trap` — "A rate limit set with `tc` on a server's egress does nothing about how fast it *receives*; ingress can only be policed (dropped), not shaped. Limiting download speed needs a policer on ingress, or shaping on the far side of the link."
- **References:**
  - `https://man7.org/linux/man-pages/man8/tc.8.html` and `man 8 tc-fq_codel`, `tc-htb`, `tc-cake` — the command reference for every qdisc on this page.
  - RFC 8290, *"The Flow Queue CoDel Packet Scheduler and Active Queue Management Algorithm"* — fq_codel's specification and default parameters.
  - Gettys & Nichols, *"Bufferbloat: Dark Buffers in the Internet"*, ACM Queue 2011 (`https://queue.acm.org/detail.cfm?id=2071893`) — the problem this subsystem's modern defaults fix.
  - `https://www.bufferbloat.net/projects/codel/wiki/` — CoDel and cake project documentation and measurements; check page dates, as some are old.

- [ ] **Step 1: Write `the-transmit-path.md`** to the brief above. Capture real `ethtool -k` and BQL output from a real interface and say which driver it came from.
- [ ] **Step 2: Try the `htb` and `netem` examples on a network namespace's veth or on `lo`** — never on the interface you are connected through — and confirm with `tc -s` that they behave as written.
- [ ] **Step 3: Write `traffic-control.md`** to the brief above.
- [ ] **Step 4: Verify every symbol and default** — `tcp_sendmsg`, `tcp_push`, `tcp_write_xmit`, `tcp_transmit_skb`, `skb_gso_segment`, `sk_dst_cache`, `ip_queue_xmit`, `ip_output`, `ip_finish_output2`, `neigh_output`, `dev_queue_xmit`, `__dev_queue_xmit`, `__dev_xmit_skb`, `qdisc_run`, `sch_direct_xmit`, `dev_hard_start_xmit`, `dev_queue_xmit_nit`, `napi_consume_skb`, `Qdisc`, `Qdisc_ops`, `netdev_queue`, `tcf_proto`, `tcf_classify`, `dequeue_skb` — plus `tcp_limit_output_bytes`, the BQL sysfs path, the compiled-in default qdisc, and the fq_codel defaults.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 6: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write the transmit path and traffic control"
```

---

## Task 18: Folder 13 — TCP in the kernel, and routing and neighbours

**Files:**
- Modify: `docs/linux/13-networking-stack/tcp-in-the-kernel.md`
- Modify: `docs/linux/13-networking-stack/routing-and-neighbours.md`

**Interfaces:**
- Consumes:
  - `13/sockets-in-the-kernel`, `13/the-receive-path` (Task 16) and `13/the-transmit-path` (Task 17);
  - `computer-science/computer-networks/transport-layer-tcp-udp` — **TCP's protocol semantics are owned there; this page owns the implementation**;
  - `computer-science/computer-networks/arp-icmp-and-neighbour-discovery` (Task 3) — **ARP/NDP protocol behaviour is owned there**.
- Produces:
  - `13/tcp-in-the-kernel`, a prerequisite of diagnosing and the Task 3 backlink target;
  - `13/routing-and-neighbours`, a prerequisite of network namespaces and diagnosing.

**Currency risk.** The spec requires context7 verification of BBR status and the `iproute2` command surface. Do both before writing.

### `tcp-in-the-kernel.md` — TCP in the Kernel **[Misc]**

- **Opens with:** the transport-layer page describes TCP as a protocol. This page describes it as roughly thirty thousand lines of kernel C that must make that protocol fast on everything from a lossy phone link to a 400 Gbit/s datacentre fabric. Most of what an application experiences as "TCP behaviour" — slow start after idle, 200 ms stalls, a connection lingering after close — is a specific kernel mechanism with a specific tunable.
- **Sections:**
  - `## The state machine as implemented` — the protocol's states plus the kernel's own details: request socks for half-open connections, `TCP_NEW_SYN_RECV`, and orphaned sockets after `close`. `tcp_rcv_state_process` as the handler for everything not on the established fast path. Draw the **anchor** here.
  - `## Buffers and autotuning` — `net.ipv4.tcp_rmem`/`tcp_wmem` (min, default, max); receive-buffer autotuning (`tcp_rcv_space_adjust`) growing the window as the application reads; and why setting `SO_RCVBUF` yourself *disables* autotuning for that socket. Link `./sockets-in-the-kernel.md` for the accounting.
  - `## Retransmission and loss detection` — the RTO computed from smoothed RTT with a minimum (`TCP_RTO_MIN`, 200 ms by default — verify), fast retransmit on duplicate ACKs, SACK, and RACK-TLP (RFC 8985) as the current loss-detection algorithm (`net/ipv4/tcp_recovery.c`). Tail loss probes, in one sentence.
  - `## Pluggable congestion control` — `struct tcp_congestion_ops`, `tcp_register_congestion_control`, the `net.ipv4.tcp_congestion_control` default (CUBIC) and `tcp_available_congestion_control`, and per-socket `TCP_CONGESTION`. BBR as a model-based alternative that paces rather than reacting to loss. **State precisely which BBR version is in mainline at v6.18, verified via context7 and `net/ipv4/tcp_bbr.c`**, and that BBR is designed to run with the `fq` qdisc or internal pacing. Do not repeat claims about BBRv3 being merged unless the source shows it.
  - `## Nagle, delayed ACK, and corking` — Nagle holding small segments while data is unacknowledged, delayed ACKs holding ACKs, and the stall their interaction produces on request/response traffic. `TCP_NODELAY`, `TCP_CORK`, `TCP_QUICKACK`, and `TCP_NOTSENT_LOWAT`.
  - `## TIME_WAIT, keepalive, and closing` — `TIME_WAIT` lasting a fixed 2×MSL (60 s, `TCP_TIMEWAIT_LEN`), why that is correct, why `tcp_fin_timeout` does *not* control it, `net.ipv4.tcp_tw_reuse` for outgoing connections, and the removed `tcp_tw_recycle` (state the version). Keepalive defaults (two hours) and `TCP_KEEPIDLE`/`TCP_USER_TIMEOUT`.
  - `## TCP Fast Open and the options table` — TFO in one paragraph (`net.ipv4.tcp_fastopen`), then a **table** of the socket options that matter in practice: `TCP_NODELAY`, `TCP_CORK`, `TCP_USER_TIMEOUT`, `TCP_KEEPIDLE`, `SO_REUSEPORT`, `SO_LINGER`, `TCP_NOTSENT_LOWAT`, `TCP_CONGESTION`, `TCP_INFO` — each with what it changes and when to use it.
  - `## Reading ss -ti` — real `ss -ti` output annotated field by field: `cubic`/`bbr`, `rto`, `rtt`, `cwnd`, `ssthresh`, `bytes_acked`, `retrans`, `pacing_rate`, `delivery_rate`, `rcv_space`. This is `TCP_INFO` rendered.
  - `## Misconceptions` **[Misc]** —
    1. "`tcp_fin_timeout` shortens `TIME_WAIT`." It controls `FIN_WAIT_2` for orphaned sockets; `TIME_WAIT` is fixed.
    2. "Many sockets in `TIME_WAIT` is a problem to tune away." They are cheap and correct; exhaustion affects only a client making very many outgoing connections to one destination.
    3. "Setting a large `SO_RCVBUF` improves throughput." It disables autotuning, which usually does better.
- **Anchor:** a Mermaid `stateDiagram-v2` of TCP connection states as Linux implements them — `CLOSED`, `LISTEN`, `SYN_SENT`, `SYN_RECV` (with the request-sock note), `ESTABLISHED`, `FIN_WAIT1`, `FIN_WAIT2`, `CLOSE_WAIT`, `CLOSING`, `LAST_ACK`, `TIME_WAIT` — with transitions labelled by event (segment received or application call). Note on `FIN_WAIT2` which timer governs it, and on `TIME_WAIT` that it is fixed. Caption: "TCP's states as the kernel tracks them, with the two timers people confuse marked where they apply."
- **KernelFacts:**
  - `structure` — `[["struct tcp_sock", "include/linux/tcp.h"], ["struct tcp_congestion_ops", "include/net/tcp.h"]]`
  - `path` — `"tcp_v4_rcv() → tcp_rcv_established() (fast path) | tcp_rcv_state_process() → tcp_ack() → tcp_cong_control() → ca_ops->cong_avoid()"`
  - `observe` — `ss -tin state established | head -20; sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_available_congestion_control`
  - `trap` — "Setting `SO_RCVBUF` or `SO_SNDBUF` turns off the kernel's buffer autotuning for that socket. Applications that 'optimise' by setting a fixed large buffer usually end up with worse throughput on fast paths and more memory on slow ones than the default would have given them."
- **References:**
  - `https://man7.org/linux/man-pages/man7/tcp.7.html` — every sysctl and socket option on this page, from the kernel's perspective.
  - `https://docs.kernel.org/networking/ip-sysctl.html` — the authoritative, current list of `net.ipv4.tcp_*` sysctls with defaults.
  - RFC 8985 (RACK-TLP) and RFC 9438 (CUBIC) — the loss-detection and default congestion-control algorithms Linux implements.
  - Cardwell et al., *"BBR: Congestion-Based Congestion Control"*, ACM Queue 2016 (`https://queue.acm.org/detail.cfm?id=3022184`) — the model BBR is built on; **state which BBR version it describes and which one v6.18 ships, dated from the context7 check.**
  - `<Src file="net/ipv4/tcp_input.c" symbol="tcp_rcv_established" />` — the fast path, with comments explaining why it exists.

### `routing-and-neighbours.md` — Routing and Neighbours **[Lab host=any-linux]**

- **Opens with:** every outgoing packet, and every packet a Linux router forwards, needs two answers before it can leave: which interface and next hop (routing), and that next hop's link-layer address (neighbour resolution). Linux answers the first with a longest-prefix-match trie over several routing tables selected by policy rules, and the second with a per-interface neighbour cache that has more states than most people expect. `ip route get` asks the kernel exactly the question a packet asks, which makes it the best routing debugger there is.
- **Sections:**
  - `## The FIB and longest-prefix match` — routing tables stored as an LC-trie (`net/ipv4/fib_trie.c`, `fib_table_lookup`); a lookup returns the most specific matching prefix and its next hop(s). The routing *cache* was removed in 3.6 — say so, because old documentation still describes it — and per-destination exceptions (`fib_nh_exception`) now carry learned PMTU and redirects.
  - `## Tables and policy rules` — the `local` (255), `main` (254) and `default` (253) tables; `ip rule` selecting a table by source, mark, interface, or UID before the route lookup (`fib_rules_lookup`). Why the `local` table is consulted first, and how it holds every address this host owns.
  - `## Route lookup in the datapath` — input routing on receive (`ip_route_input_noref`, deciding local delivery versus forwarding) and output routing for locally generated packets (`ip_route_output_key_hash` / `ip_route_output_flow` — verify), resulting in a `dst_entry` attached to the `sk_buff` and cached on connected sockets. Link `./the-receive-path.md` and `./the-transmit-path.md`.
  - `## Nexthop objects and multipath` — ECMP routes and hashing, and nexthop objects (`ip nexthop`) as the modern way to share next hops across routes (state the version; verify).
  - `## The neighbour table` — `struct neighbour` per (interface, next-hop address), and the NUD states: `INCOMPLETE`, `REACHABLE`, `STALE`, `DELAY`, `PROBE`, `FAILED`, `NOARP`, `PERMANENT`. Packets queued while resolution is pending (`unres_qlen`), confirmation from upper-layer traffic instead of new ARP requests, and garbage collection thresholds (`gc_thresh1/2/3`) with the "neighbour table overflow" message they prevent. Link the CS page for the ARP/NDP protocol itself. **Anchor** here.
  - `## Reverse-path filtering` — `rp_filter` dropping packets whose source would not be routed back via the arrival interface, and why asymmetric routing breaks with it on.
  - `<Lab host="any-linux" title="Ask the kernel what a packet would do" time="15 min">` — no root needed:
    1. `ip rule show`;
    2. `ip route show table main` and `ip route show table local | head`;
    3. `ip route get 1.1.1.1` and `ip route get 127.0.0.1` — explain every field of each answer, including `cache` and `uid`;
    4. `ip route get 1.1.1.1 from <a local address> mark 0x1` to see how rules would change the answer;
    5. `ip -s neigh show` — read the states and the `used`/`confirmed`/`updated` timers;
    6. `ping -c1 <gateway>` then `ip neigh show <gateway>` to watch an entry go `REACHABLE` and, a minute later, `STALE`.

    Real output for each step. "If it fails": inside some containers `ip rule` shows only defaults and the gateway may be a virtual bridge; on WSL2 the neighbour table reflects a Hyper-V virtual switch.
- **Anchor:** a Mermaid `stateDiagram-v2` of the neighbour NUD states with transitions — lookup creates `INCOMPLETE` → reply → `REACHABLE` → timeout → `STALE` → packet sent → `DELAY` → no confirmation → `PROBE` → reply → `REACHABLE` / no reply → `FAILED` — each labelled with the event or timer. Caption: "The states a neighbour entry moves through, and why a healthy entry spends most of its life in `STALE` without anything being wrong."
- **Second visual:** a Mermaid `flowchart LR` of an output lookup: packet → `ip rule` list (priority order) → selected table → longest-prefix match → `dst` + next hop → neighbour entry → frame out.
- **KernelFacts:**
  - `structure` — `[["struct fib_table", "include/net/ip_fib.h"], ["struct neighbour", "include/net/neighbour.h"]]`
  - `path` — `"ip_route_output_flow() → fib_lookup() → fib_rules_lookup() → fib_table_lookup() → dst → ip_finish_output2() → neigh_output() → neigh_resolve_output()"`
  - `observe` — `ip route get 1.1.1.1 && ip -s neigh show`
  - `trap` — "`STALE` in `ip neigh` does not mean broken — it means the entry has not been confirmed recently and will be re-verified the next time it is used. Deleting `STALE` entries to 'fix' networking changes nothing except adding an ARP round trip."
- **References:**
  - `https://man7.org/linux/man-pages/man8/ip-route.8.html`, `ip-rule(8)`, and `ip-neighbour(8)` — the command surface this page uses; **context7-verified against the current iproute2, dated.**
  - `https://docs.kernel.org/networking/ip-sysctl.html` — `rp_filter`, `gc_thresh*`, and the neighbour timers, with defaults.
  - LWN, *"The IPv4 route cache removal"* or the 3.6 merge-window coverage — **verify the article URL**; this is the history readers need when older documentation disagrees.
  - `<Src file="net/core/neighbour.c" symbol="neigh_resolve_output" />` — packet queueing while resolution is pending.

- [ ] **Step 1: Run the context7 verification for BBR and TCP congestion control.** Check which BBR version is in mainline at v6.18 against `<Src file="net/ipv4/tcp_bbr.c" />` — the source is the tiebreaker. Note the date.
- [ ] **Step 2: Write `tcp-in-the-kernel.md`** to the brief above. Capture real `ss -ti` output from an established connection (for example, during a large `curl` download) and annotate it.
- [ ] **Step 3: Run the context7 verification for `iproute2`**: `ip route get` output fields, `ip rule` selectors, `ip nexthop`, and `ip neigh` states. Note the date.
- [ ] **Step 4: Run the routing lab** as an ordinary user on a real Linux host and record every step's output, including the `REACHABLE` → `STALE` transition.
- [ ] **Step 5: Write `routing-and-neighbours.md`** to the brief above.
- [ ] **Step 6: Verify every symbol and default** — `tcp_sock`, `tcp_congestion_ops`, `tcp_register_congestion_control`, `tcp_rcv_state_process`, `tcp_rcv_space_adjust`, `TCP_RTO_MIN`, `TCP_TIMEWAIT_LEN`, `tcp_ack`, `tcp_cong_control`, `tcp_recovery.c`, `fib_table`, `fib_table_lookup`, `fib_lookup`, `fib_rules_lookup`, `fib_nh_exception`, `ip_route_input_noref`, `ip_route_output_flow`, `dst_entry`, `neighbour`, `neigh_output`, `neigh_resolve_output`, the NUD state names, and the version `tcp_tw_recycle` was removed.
- [ ] **Step 7: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 8: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write TCP in the kernel, and routing and neighbours"
```

---

## Task 19: Folder 13 — netfilter and nftables, and connection tracking and NAT

**Files:**
- Modify: `docs/linux/13-networking-stack/netfilter-and-nftables.md`
- Modify: `docs/linux/13-networking-stack/connection-tracking-and-nat.md`

**Interfaces:**
- Consumes: `13/the-receive-path` (Task 16), `13/the-transmit-path` (Task 17), and `computer-science/computer-networks/nat-and-connection-tracking` (Task 3) — **NAT forms, mapping behaviour, and why state is required are owned there.**
- Produces:
  - `13/netfilter-and-nftables`, a prerequisite of conntrack and diagnosing, and the page carrying the Task 22 netfilter figure;
  - `13/connection-tracking-and-nat`, the Task 3 backlink target and a Task 21 link target for `02/the-life-of-a-container`.

**Currency risk.** The spec requires context7 verification of nftables syntax. Do it before writing the first page.

### `netfilter-and-nftables.md` — netfilter and nftables **[Misc]**

- **Opens with:** netfilter is not a firewall. It is a set of hooks at fixed points in the network stack — five for IP, plus ingress and egress on devices — where registered functions may inspect, modify, accept, or drop a packet. iptables, nftables, connection tracking, and NAT are all users of those hooks. Once you know where the hooks sit relative to the routing decision, every "why did my rule not match" question becomes answerable by drawing the packet's path.
- **Sections:**
  - `## The hooks` — NF_INET_PRE_ROUTING, LOCAL_IN, FORWARD, LOCAL_OUT, POST_ROUTING, placed on the receive and transmit paths from `./the-network-stack-map.md`, plus the netdev ingress/egress hooks (state when egress arrived; verify). The `NF_HOOK` macro, `nf_hook_slow` iterating registered hook entries in priority order, and the verdicts (`NF_ACCEPT`, `NF_DROP`, `NF_STOLEN`, `NF_QUEUE`, `NF_REPEAT`).
  - `## Priorities decide order` — at one hook, conntrack runs before DNAT, which runs before filtering, which runs before SNAT. A **table** of the standard priority values (`NF_IP_PRI_RAW`, `CONNTRACK`, `MANGLE`, `NAT_DST`, `FILTER`, `SECURITY`, `NAT_SRC`) at v6.18, verified in `include/uapi/linux/netfilter_ipv4.h`.
  - `## nftables: a VM in the kernel` — rules are compiled in user space into expressions evaluated by `nft_do_chain`. Tables and chains are user-defined, with a chain attached to a hook and priority by declaration rather than predefined. Sets and maps give O(1) matching against thousands of addresses. Atomic ruleset replacement via a netlink transaction.
  - `## iptables over nftables` — `iptables-nft` translating iptables syntax into nftables objects, `iptables-legacy` using the older `x_tables` code, and why mixing the two on one host produces rules that do not see each other. How to tell which you have (`iptables -V` prints `(nf_tables)` or `(legacy)`).
  - `## The same policy both ways` — `<Tabs>` with an **iptables** tab and an **nftables** tab, each implementing: default-drop input, allow established/related, allow SSH from one subnet, allow HTTP/HTTPS, and log-and-drop the rest. Nftables rule source goes in ` ```text `, commands in ` ```bash `. **Verify the nftables syntax via context7, and load both rulesets in a network namespace before publishing them.**
  - `## Reading a live ruleset` — `nft list ruleset` with counters, `nft monitor trace` with `meta nftrace set 1` to watch a packet traverse chains, and `iptables -L -v -n --line-numbers` on legacy systems. Show real trace output from the namespace test.
  - `## Misconceptions` **[Misc]** —
    1. "iptables is the Linux firewall." It is one front end to netfilter, and on most current distributions it is translated into nftables.
    2. "A rule in the INPUT chain filters forwarded traffic." Forwarded packets never reach LOCAL_IN; they traverse FORWARD.
    3. "Rule order within a table is all that matters." Chain priority across tables at the same hook decides order first.
- **Anchor:** a Mermaid `flowchart LR` of the IPv4 hook placement:
  - incoming → PRE_ROUTING → routing decision, which branches:
    - LOCAL_IN → local process → LOCAL_OUT → routing → POST_ROUTING → out;
    - FORWARD → POST_ROUTING → out.

  At each hook, list the standard priorities as stacked labels (raw, conntrack, mangle, nat, filter). Caption: "The five IPv4 netfilter hooks around the routing decision, with the order in which conntrack, NAT, and filtering run at each."
- **Figure (added in Task 22):** the Wikimedia Commons "Netfilter-packet-flow" diagram, zoomable, beside the Mermaid simplification. **Leave a clearly marked place for it now**, and write the page so it stands alone without it.
- **KernelFacts:**
  - `structure` — `[["struct nf_hook_ops", "include/linux/netfilter.h"], ["struct nft_chain", "include/net/netfilter/nf_tables.h"]]`
  - `path` — `"ip_rcv() → NF_HOOK(NF_INET_PRE_ROUTING) → nf_hook_slow() → nft_do_chain_ipv4() → nft_do_chain() → verdict"` (verify the chain entry name)
  - `observe` — `sudo nft list ruleset | head -40; iptables -V`
  - `trap` — "`iptables-legacy` and `iptables-nft` rules live in different kernel subsystems and do not see each other — a host where Docker installed legacy rules and the administrator added nft rules can have two firewalls, each silently incomplete."
- **References:**
  - `https://wiki.nftables.org/wiki-nftables/index.php/Main_Page` — the nftables project's documentation, including the hook and priority pages; **context7-verified syntax, dated.**
  - `https://man7.org/linux/man-pages/man8/nft.8.html` — the full nftables command and rule language reference.
  - `https://www.netfilter.org/documentation/` — the netfilter project's documentation index, including the hook architecture.
  - `<Src file="net/netfilter/core.c" symbol="nf_hook_slow" />` — hook traversal and verdict handling.

### `connection-tracking-and-nat.md` — Connection Tracking and NAT **[WAH]** **[Misc]**

- **Opens with:** a stateful firewall rule like "allow established connections" and a NAT rule like "masquerade outgoing traffic" both need the kernel to remember every flow it has seen. On Linux that memory is conntrack: a hash table of `nf_conn` entries, each holding the flow's tuple in both directions, a protocol state, a timeout, and — if NAT applies — the rewritten addresses. NAT on Linux is not a separate packet-rewriting engine. It is a decision made once, on a connection's first packet, stored in its conntrack entry, and applied to every later packet by lookup.
- **Sections:**
  - `## The conntrack entry` — `struct nf_conn` with two `nf_conntrack_tuple_hash` entries (original and reply direction), `status` bits, a timeout, and extensions (NAT, helper, accounting, labels). The lookup at PRE_ROUTING and LOCAL_OUT (`nf_conntrack_in`) and confirmation at the end of the path (`nf_conntrack_confirm`), which is why an unconfirmed entry never appears in the table for a packet that was dropped.
  - `## States as rules see them` — `ctstate` NEW, ESTABLISHED, RELATED, INVALID, UNTRACKED (`enum ip_conntrack_info`) versus the per-protocol TCP tracking states (`SYN_SENT`, `ESTABLISHED`, `FIN_WAIT`, `TIME_WAIT`, …). A **table** mapping each rule-visible state to what caused it.
  - `## NAT is decided once` — the first packet of a flow traverses the nat chains; `nf_nat_setup_info` computes the mapping and stores it in the entry; `nf_nat_packet` rewrites every later packet in both directions without consulting the rules. DNAT at PRE_ROUTING and LOCAL_OUT, SNAT/masquerade at POST_ROUTING. Masquerade picks the source address from the output interface and flushes entries when that address goes away. Link the CS page for why the mapping is required at all.
  - `## Helpers` — protocols with addresses in their payload (FTP, SIP) need a helper to create RELATED expectations, and why automatic helper assignment was removed (state the version) so helpers must now be assigned explicitly with a `ct helper` rule.
  - `## Table size and the failure everyone meets once` — `net.netfilter.nf_conntrack_max`, `nf_conntrack_buckets`, per-protocol timeouts (the established-TCP timeout is days — verify the default), and the `nf_conntrack: table full, dropping packet` kernel message. How short-lived UDP floods or a DNS server fill it, and the three responses: raise the limit, shorten timeouts, or `notrack` traffic that does not need state in the `raw` priority.
  - `## Inspecting it` — `conntrack -L`, `conntrack -E` for live events, `conntrack -S` for per-CPU stats (`insert_failed`, `drop`, `early_drop`), and `/proc/sys/net/netfilter/nf_conntrack_count`.
  - `## What actually happens` **[WAH]** — `docker run -p 8080:80 nginx`, or, with no Docker required, the equivalent two-rule setup in a network namespace from `./network-namespaces-and-virtual-devices.md`: a DNAT rule for host port 8080 and a masquerade rule. Then `curl localhost:8080` from outside the namespace while running `conntrack -E`. Show the entry with the original tuple (client → host:8080) and the reply tuple (container:80 → client) and explain that the rewrite you are watching happens by lookup, not by rule evaluation. **Real output from a real run.** Name the containers folder in prose, unlinked.
  - `## Misconceptions` **[Misc]** —
    1. "Conntrack is only used when you configure NAT." Any stateful rule — including a typical default firewall's "established, related" — loads and uses it.
    2. "NAT rules are evaluated for every packet." Only the first packet of a flow; the rest are rewritten from the stored mapping.
    3. "Raising `nf_conntrack_max` is always safe." Each entry costs memory, and a larger table without more hash buckets makes lookups slower.
- **Anchor:** a Mermaid `sequenceDiagram` — Client, Host PRE_ROUTING (conntrack + DNAT), Routing, Namespace/container, Host POST_ROUTING — for the first packet (rules consulted, entry created, DNAT stored) and a later packet (lookup hits the entry, rewrite applied, no rule evaluation), with the conntrack entry drawn as a `Note over` showing both tuples. Caption: "NAT decided once on the first packet and replayed by lookup for every packet after it."
- **Second visual:** a **table** of the conntrack entry fields from the lab's real `conntrack -L` line, field by field.
- **KernelFacts:**
  - `structure` — `[["struct nf_conn", "include/net/netfilter/nf_conntrack.h"], ["struct nf_conntrack_tuple", "include/net/netfilter/nf_conntrack_tuple.h"]]`
  - `path` — `"PRE_ROUTING → nf_conntrack_in() → resolve_normal_ct() → nf_nat_inet_fn() → nf_nat_setup_info() (first packet) | nf_nat_packet() (later) → … → nf_conntrack_confirm()"` (verify each name)
  - `observe` — `sudo conntrack -L | head; cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max`
  - `trap` — "Changing a NAT rule does not affect connections that already exist — their mapping lives in the conntrack entry. A port-forward that 'still points at the old container' after a rule change is usually a stale entry; `conntrack -D` with a matching filter removes it."
- **References:**
  - `https://docs.kernel.org/networking/nf_conntrack-sysctl.html` — every conntrack sysctl with its default, including the timeouts.
  - `https://man7.org/linux/man-pages/man8/conntrack.8.html` — the inspection tool used throughout this page.
  - Neira Ayuso, *"Netfilter's connection tracking system"*, ;login: 2006 — the design paper by the maintainer; old, and the core model is unchanged.
  - `https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_(NAT)` — NAT and `ct helper` rules in nftables syntax; **context7-verified, dated.**

- [ ] **Step 1: Run the context7 verification for nftables.** Check table/chain declarations, hook and priority syntax, sets, `ct state`, NAT and masquerade statements, `ct helper`, and `nftrace`. Note the date.
- [ ] **Step 2: Load both firewall rulesets** from the `<Tabs>` into a scratch network namespace (`sudo ip netns add fwtest`, then `sudo ip netns exec fwtest nft -f rules.nft`, and the iptables equivalent), and confirm with `nft list ruleset`/`iptables -S` that they load and mean what the page says. Delete the namespace afterwards.
- [ ] **Step 3: Write `netfilter-and-nftables.md`** to the brief above, leaving the marked place for the Task 22 figure.
- [ ] **Step 4: Run the conntrack WAH scenario** — a namespace with a web server, DNAT plus masquerade rules in a dedicated `lab` nftables table, `conntrack -E` capturing a real `curl`. Record the output. **Delete the `lab` table and the namespace afterwards, and restore `net.ipv4.ip_forward` to its original value.**
- [ ] **Step 5: Write `connection-tracking-and-nat.md`** to the brief above.
- [ ] **Step 6: Verify every symbol and default** — `nf_hook_ops`, `NF_HOOK`, `nf_hook_slow`, the verdict names, the `NF_IP_PRI_*` values, `nft_chain`, `nft_do_chain`, `nft_do_chain_ipv4`, `nf_conn`, `nf_conntrack_tuple`, `nf_conntrack_tuple_hash`, `ip_conntrack_info`, `nf_conntrack_in`, `resolve_normal_ct`, `nf_conntrack_confirm`, `nf_nat_inet_fn`, `nf_nat_setup_info`, `nf_nat_packet`, the "table full" message text, the `nf_conntrack_max`/`nf_conntrack_buckets` defaults, the established-TCP timeout default, the version that removed automatic helper assignment, and when the netdev egress hook arrived.
- [ ] **Step 7: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 8: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write netfilter and nftables, and connection tracking and NAT"
```

---

## Task 20: Folder 13 — network namespaces and virtual devices, and diagnosing network problems

**Files:**
- Modify: `docs/linux/13-networking-stack/network-namespaces-and-virtual-devices.md`
- Modify: `docs/linux/13-networking-stack/diagnosing-network-problems.md`

**Interfaces:**
- Consumes: `13/routing-and-neighbours` (Task 18), `13/connection-tracking-and-nat` and `13/netfilter-and-nftables` (Task 19), `13/tcp-in-the-kernel` (Task 18), `13/the-receive-path` (Task 16), `06/threads-are-tasks` (`clone` flags), and `12/diagnosing-io-problems` (Task 14 — the same method shape).
- Produces:
  - `13/network-namespaces-and-virtual-devices`, which the Phase 4 containers folder will build on — **named in prose only**;
  - `13/diagnosing-network-problems`, which Task 24 adds to the "My server is slow" learning path.

### `network-namespaces-and-virtual-devices.md` — Network Namespaces and Virtual Devices **[Lab host=root-required]**

- **Opens with:** a network namespace is a complete, independent copy of the network stack: its own interfaces, addresses, routing tables, neighbour cache, netfilter rules, sockets, and `/proc/sys/net`. A new one contains nothing but a loopback device that is down. Connect it to anything, and you need virtual devices — veth pairs, bridges, macvlans, tunnels. That combination is the entire mechanism container runtimes automate, and this page builds it by hand.
- **Sections:**
  - `## A whole stack per namespace` — `struct net` and `copy_net_ns` on `clone(CLONE_NEWNET)`/`unshare`; `struct pernet_operations` as how every subsystem registers per-namespace state. What is and is not per-namespace: sysctls under `net.*` mostly are, while physical NIC ownership moves with the device and loopback is always per-namespace.
  - `## Handles: /proc, bind mounts, and ip netns` — a namespace lives while a process is in it or a file refers to it. `ip netns add` creates one and bind-mounts `/proc/self/ns/net` to `/run/netns/NAME` so it outlives its creator; `ip netns exec` uses `setns`. `nsenter` as the general tool. Link `../06-processes-and-threads/threads-are-tasks.md` for the `clone` flag menu.
  - `## veth pairs` — two devices, where a frame transmitted on one is received on the other (`veth_xmit` handing the `sk_buff` to the peer's receive path). One end in a namespace and one on the host is the basic container link.
  - `## Bridges` — a software switch: learning an FDB of MAC addresses (`br_fdb_update`), forwarding between ports (`br_handle_frame`, `br_forward`), with the bridge itself an interface that can have an address. `bridge fdb show`.
  - `## The other virtual devices` — a **table**: macvlan (sub-interfaces with their own MACs on a parent; the bridge/private/vepa modes; host-to-macvlan traffic not working by default), ipvlan (shared MAC, L2/L3 modes), VLAN (802.1Q sub-interfaces), VXLAN and Geneve (L2 over UDP, for cross-host overlays), WireGuard (an encrypted L3 tunnel), and `netkit` (a BPF-programmable veth alternative — **verify its status at v6.18**).
  - `<Lab host="root-required" title="Build a two-namespace network, then give it the internet" time="30 min">` — on a real Linux host (not WSL2).

    :::warning[This lab changes host networking settings]
    Steps 5–6 enable IP forwarding and add a NAT rule on the host. Record the original `net.ipv4.ip_forward` value first and restore it in the cleanup step. Run it on a machine where a brief firewall change is acceptable.
    :::

    1. `ip netns add red; ip netns add blue`;
    2. `ip link add br0 type bridge && ip link set br0 up`;
    3. for each namespace, create a veth pair, move one end in, attach the other to `br0`, and assign `10.200.0.2/24` and `10.200.0.3/24`;
    4. `ip netns exec red ping -c2 10.200.0.3`, then `bridge fdb show br br0`;
    5. give `br0` `10.200.0.1/24`, add default routes inside the namespaces, `sysctl -w net.ipv4.ip_forward=1`, and add a masquerade rule in a dedicated nftables table `lab`;
    6. `ip netns exec red ping -c2 1.1.1.1` and `conntrack -L | grep 10.200.0.2`;
    7. cleanup — delete the namespaces, `br0`, and the `lab` table, and restore `ip_forward`.

    Real output for every step. "If it fails": a host firewall with a default-drop `FORWARD` policy (Docker installs one) blocks step 6 — say how to see that with `nft list ruleset`; `conntrack` is in `conntrack-tools`.
- **Anchor:** a Mermaid `flowchart LR` of the lab's result: namespaces `red` and `blue`, each with `eth0` and an address, veth peers to `br0` (`10.200.0.1`) on the host, the host's routing and the masquerade rule, and the physical uplink. Each hop is labelled with the device type. Caption: "The network the lab builds: two namespaces on a bridge, routed and masqueraded out through the host — the same shape a container runtime creates for you."
- **KernelFacts:**
  - `structure` — `[["struct net", "include/net/net_namespace.h"], ["struct pernet_operations", "include/net/net_namespace.h"]]`
  - `path` — `"unshare(CLONE_NEWNET) → copy_net_ns() → setup_net() → pernet ops init · veth: veth_xmit() → veth_forward_skb() → peer receive"` (verify each name)
  - `observe` — `ip netns list; lsns -t net; ip -d link show type veth`
  - `trap` — "Deleting a network namespace with `ip netns delete` only removes the bind-mount handle. If any process is still inside it, the namespace — interfaces, sockets, and all — keeps existing, invisibly to `ip netns list`. `lsns -t net` still shows it."
- **References:**
  - `https://man7.org/linux/man-pages/man7/network_namespaces.7.html` — what a network namespace contains and how devices move between them.
  - `https://man7.org/linux/man-pages/man8/ip-netns.8.html` and `man 4 veth` — the tools and the device this page's lab uses; **iproute2 syntax context7-verified in Task 18, dated.**
  - LWN, *"Namespaces in operation, part 7: Network namespaces"* (`https://lwn.net/Articles/580893/`) — Kerrisk's 2014 walkthrough; semantics unchanged, device list since grown.
  - `https://docs.kernel.org/networking/bridge.html` — the in-tree bridge documentation, if present at v6.18; otherwise `man 8 bridge`.

### `diagnosing-network-problems.md` — Diagnosing Network Problems **[WAH]** **[Misc]** **[Lab host=root-required]**

- **Opens with:** "the network is slow" and "connections hang" are symptoms that can come from:
  - the NIC dropping packets it had no buffer for;
  - the kernel dropping them in a backlog or firewall;
  - an application that stopped calling `accept`;
  - a full conntrack table;
  - a path-MTU black hole;
  - the actual network.

  Each leaves a different counter moving. This page is the method — find which counter moved — and a worked case, using tools whose data sources were all introduced earlier in this folder.
- **Sections:**
  - `## Counters first, captures second` — the kernel already counts almost every drop and retransmit; a capture is expensive and shows only what reached the tap. Start at `ss` and the counter files, and capture only once you know which flow.
  - `## ss, in place of netstat` — `ss` reads socket state over netlink (`sock_diag`) rather than parsing `/proc/net/tcp`, which is why it is fast on hosts with many sockets. The flags that matter: `-t -u -l -n -p -i -m -e`, and filter expressions (`state established`, `dport = :443`). Link `./tcp-in-the-kernel.md` for reading `-i`.
  - `## The counter files` — `/proc/net/snmp` and `/proc/net/netstat` through `nstat -az` (deltas with `nstat` alone), `/proc/net/softnet_stat` (link `./the-receive-path.md`), `ip -s link`, and `ethtool -S` (driver-specific names). A **table** of the dozen counters that answer real questions:

    | Counter | Question it answers |
    |---|---|
    | `TcpRetransSegs` | Am I losing packets? |
    | `TcpExtTCPTimeouts` | Am I losing whole windows? |
    | `TcpExtListenOverflows` / `ListenDrops` | Is my application accepting fast enough? |
    | `TcpExtTCPBacklogDrop` | Is a socket lock held too long? |
    | `TcpExtTCPRcvQDrop` | Is my receiver too slow? |
    | `UdpRcvbufErrors` | Is a UDP receive buffer too small? |
    | `IpInDiscards` / `IpOutNoRoutes` | Are packets being discarded, or is a route missing? |
    | softnet `dropped`, `time_squeeze` | Is the receive softirq falling behind? |
    | NIC `rx_missed`-style counters | Is the NIC out of buffers? |
    | `nf_conntrack` stats `drop`/`early_drop` | Is the conntrack table full? |

    **Verify each counter name exists** on a v6.18 system.
  - `## What tcpdump can and cannot see` — the receive tap is in `__netif_receive_skb_core`, before netfilter and the socket, so `tcpdump` shows packets the firewall or a full buffer then dropped. The transmit tap is after the qdisc, so packets dropped in the qdisc are invisible. Offloaded (GRO/TSO) packets appear as giant segments. XDP drops happen before any tap. Link `./the-receive-path.md` and `./the-transmit-path.md`.
  - `## Attributing drops` — `perf trace -e skb:kfree_skb` and `dropwatch` via the drop monitor, now carrying a drop *reason* (`enum skb_drop_reason`) that names the cause: `NETFILTER_DROP`, `TCP_LISTEN_OVERFLOW`, `SOCKET_RCVBUFF`, and so on. **Verify the enum member names at v6.18.** `pwru` as an eBPF tool that follows one packet through every function, with the eBPF folder named in prose.
  - `## What actually happens` **[WAH]** — a worked investigation, measured in the lab. **Symptom:** clients report that connections to a service "hang" for a few seconds, then work. **Evidence:**
    1. `ss -ltn` shows the listening socket's `Recv-Q` at its `Send-Q` limit;
    2. `nstat -az TcpExtListenOverflows TcpExtListenDrops` climbing;
    3. `tcpdump` on the server showing clients' SYNs *arriving* and being retransmitted at 1 s, 3 s intervals;
    4. `perf trace -e skb:kfree_skb` reporting the listen-overflow drop reason.

    **Cause:** the application's accept loop is stalled (in the lab, a server that never calls `accept`), so the accept queue is full and new SYNs are dropped after arriving. **Fix:** make the application accept, not raise `somaxconn` first.

    Then a second, shorter case: a port blocked by an nftables rule, where `tcpdump` still shows the SYN, `nft` counters and the `NETFILTER_DROP` reason show where it died. Every number from the lab run.
  - `<Lab host="root-required" title="Find the drop the capture cannot explain" time="30 min">` — on a real Linux host.
    1. Start `python3 -c "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',9000)); s.listen(1); time.sleep(900)"`, a server that never accepts.
    2. Run `for i in $(seq 8); do timeout 5 nc -z 127.0.0.1 9000 & done`.
    3. Watch `ss -ltn sport = :9000`.
    4. `nstat -az TcpExtListenOverflows TcpExtListenDrops`.
    5. `sudo tcpdump -ni lo port 9000 -c 20`.
    6. `sudo perf trace -e skb:kfree_skb --filter 'reason != 0'`, or without a filter if unsupported (verify the field name).
    7. Create an nftables table `lab` with an input chain dropping `tcp dport 9001`, run `nc -z -w2 127.0.0.1 9001`, and compare `tcpdump`, `nft list table inet lab` counters, and the `kfree_skb` reason.
    8. Delete the `lab` table and stop the server.

    Real output for each step. "If it fails": the `reason` field requires a kernel with drop reasons (v6.18 has them) and a `perf` new enough to decode it — `perf trace -e skb:kfree_skb` with no filter still works; on loopback, captures show both directions on one interface.
  - `## Misconceptions` **[Misc]** —
    1. "If `tcpdump` shows the packet arrived, the kernel accepted it." The tap is before netfilter, the accept queue, and the socket buffer.
    2. "Connection timeouts mean the network is dropping packets." A full accept queue produces the same client symptom on a perfect network.
    3. "Raising `somaxconn` fixes listen overflows." It hides a stalled accept loop for slightly longer.
- **Anchor:** a Mermaid `flowchart TB` decision tree:
  - **Retransmits rising?**
    - no → not packet loss; check the application (`ss` queues) and conntrack.
    - yes → **which drop counter moved?** Each branch names a page:
      - listen overflow → the application;
      - socket receive-queue drop → receiver speed, via `tcp-in-the-kernel`;
      - softnet or NIC counters → `the-receive-path`;
      - netfilter reason → `netfilter-and-nftables`;
      - conntrack `drop` → `connection-tracking-and-nat`;
      - no local counters → the path itself (PMTU, via the CS ARP/ICMP page).

  Caption: "Narrowing a network complaint to one layer by asking which kernel counter moved, before reaching for a capture."
- **KernelFacts:**
  - `structure` — `[["enum skb_drop_reason", "include/net/dropreason-core.h"], ["struct tcp_info", "include/uapi/linux/tcp.h"]]`
  - `path` — `"SYN arrives → tcp_v4_rcv() → tcp_conn_request() → accept queue full → drop with reason → kfree_skb_reason() → skb:kfree_skb tracepoint"` (verify each name)
  - `observe` — `nstat -az | grep -Ei 'retrans|overflow|drop'; ss -ltn`
  - `trap` — "A capture showing a SYN arriving and no SYN-ACK leaving does not mean the firewall dropped it. A full accept queue drops the SYN after the tap too — `nstat`'s `ListenOverflows` and the drop reason tell the two apart; the capture cannot."
- **References:**
  - `https://man7.org/linux/man-pages/man8/ss.8.html` — every `ss` flag and filter; **iproute2 context7-verified in Task 18, dated.**
  - `https://docs.kernel.org/networking/snmp_counter.html` — the in-tree explanation of the SNMP and netstat counters this page's table uses.
  - `https://github.com/cilium/pwru` — the per-packet function tracer, with its own examples of attributing a drop.
  - Gregg, *Systems Performance* (2nd ed.), ch. 10 "Network" — the network-analysis methodology, including counters-before-captures; a purchase.
  - `https://www.tcpdump.org/manpages/tcpdump.1.html` — capture options, and the notes on where on a host the capture is taken.

- [ ] **Step 1: Run the network-namespace lab** on a real Linux host, recording every step's output, and confirm the cleanup restores the original `ip_forward` value.
- [ ] **Step 2: Write `network-namespaces-and-virtual-devices.md`** to the brief above.
- [ ] **Step 3: Run the diagnosis lab** end to end and record every output, including both drop-reason cases.
- [ ] **Step 4: Write `diagnosing-network-problems.md`** to the brief above, with the WAH built from the recorded run.
- [ ] **Step 5: Verify every symbol, counter and version claim** — `struct net`, `copy_net_ns`, `setup_net`, `pernet_operations`, `veth_xmit`, `veth_forward_skb`, `br_fdb_update`, `br_handle_frame`, `br_forward`, `netkit`, `sock_diag`, `tcp_info`, `tcp_conn_request`, `skb_drop_reason` and its members, `kfree_skb_reason`, the `skb:kfree_skb` tracepoint and its `reason` field — plus every counter in the table.
- [ ] **Step 6: Check, build, and confirm folder 13 is complete**

```bash
npm run check:linux && npm run build
rtk run "grep -l 'Not yet written' docs/linux/13-networking-stack/*.md"
```

Expected: zero findings, a green build, no grep output.

- [ ] **Step 7: Commit**

```bash
git add docs/linux/13-networking-stack
git commit -m "docs: write network namespaces and diagnosing network problems"
```

---
## Task 21: Turn prose-only forward references in folders 00–10 into links

**Files:**
- Modify: `docs/linux/02-guided-traces/what-happens-when-you-type-ls.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-write.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-packet.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-container.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/what-a-system-call-actually-is.md`
- Modify: `docs/linux/08-memory-management/the-page-cache.md`
- Modify: `docs/linux/08-memory-management/writeback-and-fsync.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/threaded-irqs.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md`
- Modify: `docs/linux/00-overview/hardware-the-kernel-assumes.md` (Phase 2 leftover)
- Modify: any further page the Step 1 grep finds

**Interfaces:**
- Consumes: every page written in Tasks 4–20, which are now the targets.
- Produces: a section where the earlier folders' promises ("folder 12 owns this", "named here in prose only") are kept. The earlier phases were forbidden to link forward. Rule 1 exists so that the link lands when the target does, and this task is where that happens for folders 11–13.

**Rules for this task:**
- **Add links; do not rewrite the pages.** Change each forward-reference sentence only enough to make it a link and remove "not yet written" wording. A mention that becomes a link should read naturally as a link.
- **Link only into folders 11–13.** Mentions of drivers, containers, security, observability, eBPF, and contributing (folders 14–19) **stay prose.** In `the-life-of-a-container.md` that means namespaces, cgroups, capabilities, and seccomp remain unlinked.
- Link the first meaningful mention per page, not every occurrence.
- Relative paths only, with numeric folder prefixes (they are file paths): `../12-block-layer-and-storage/the-bio.md`.

- [ ] **Step 1: Find every candidate mechanically**

```bash
rtk run "grep -rn -i -E 'folder 1[1-3]|not yet written|named here (only )?in prose|in prose only|live in folders|later folder|block layer|blk-mq|\bbio\b|NVMe|sk_buff|NAPI|GRO|netfilter|conntrack|overlayfs|copy-up|mount propagation|dentry|path lookup|getdents|io_uring|epoll|O_DIRECT|veth|RPS|RSS' docs/linux/0* docs/linux/10-*"
```

Work from that output. For each hit, decide: (a) a prose forward reference into 11–13 → link it; (b) a mention of a 14–19 topic → leave it; (c) a mention that is already adequately linked, or that is incidental → leave it. Keep the list of decisions for the commit message's counts.

- [ ] **Step 2: Apply the known fixes.** These were located during planning; confirm each still reads as quoted before editing.

| File | Current text (abridged) | Change |
|---|---|---|
| `02/what-happens-when-you-type-ls.md` | references entry: "skim it now, own it when folder 11 covers the VFS in depth." | "…skim it now; [Why the VFS Exists](../11-vfs-and-filesystems/why-vfs-exists.md) is where this section covers it in depth." Also link the page's first body mentions of path resolution → `../11-vfs-and-filesystems/path-lookup-and-the-dcache.md`, of `getdents64`/reading a directory → `../11-vfs-and-filesystems/open-read-write-in-the-kernel.md`, and of the VFS → `../11-vfs-and-filesystems/why-vfs-exists.md`. |
| `02/what-happens-when-you-type-ls.md` | the `:::note` promising that bold names get pages "once the folders that own it (05 onward) are written — the link appears then." | Leave the note's intent. If every bold mechanism in folders 05–13 now links, reword its last sentence to say folders 14 onward are still to come. |
| `02/the-life-of-a-write.md` | the "**The block layer**" stage and mentions of `bio`, blk-mq, NVMe queue, VFS | Link: VFS → `../11-vfs-and-filesystems/open-read-write-in-the-kernel.md`; the block layer → `../12-block-layer-and-storage/the-block-layer-map.md`; `bio` → `../12-block-layer-and-storage/the-bio.md`; blk-mq → `../12-block-layer-and-storage/blk-mq.md`; NVMe queue → `../12-block-layer-and-storage/nvme-in-the-kernel.md`; its `O_DIRECT` misconception → `../12-block-layer-and-storage/buffered-direct-and-alignment.md`. |
| `02/the-life-of-a-packet.md` | stage mentions of NIC ring/NAPI/GRO, `sk_buff`, netfilter, routing, TCP, socket queue | Link: NAPI/GRO → `../13-networking-stack/the-receive-path.md`; `sk_buff` → `../13-networking-stack/sk-buff.md`; netfilter → `../13-networking-stack/netfilter-and-nftables.md`; routing → `../13-networking-stack/routing-and-neighbours.md`; TCP → `../13-networking-stack/tcp-in-the-kernel.md`; the socket receive queue and wakeup → `../13-networking-stack/sockets-in-the-kernel.md`; the transmit half → `../13-networking-stack/the-transmit-path.md`. Add a sentence near the top pointing at `../13-networking-stack/the-network-stack-map.md` as the reference map. |
| `02/the-life-of-a-container.md` | "**copy-up**", overlayfs layers, `pivot_root`/mount setup, veth pair, NAT rule | Link: overlayfs and copy-up → `../11-vfs-and-filesystems/overlayfs.md`; mount setup/propagation → `../11-vfs-and-filesystems/mounts-and-mount-namespaces.md`; veth pair → `../13-networking-stack/network-namespaces-and-virtual-devices.md`; NAT rule → `../13-networking-stack/connection-tracking-and-nat.md`. **Namespaces (as a concept), cgroups, capabilities, seccomp: unchanged.** |
| `05/what-a-system-call-actually-is.md` | table rows `io_uring`, `epoll`; then "Only the vDSO is linked above; `io_uring`, `mmap`'s fault path, and `epoll`'s internals live in folders not yet written." | Link `io_uring` → `../12-block-layer-and-storage/io-uring.md`; `epoll` → `../13-networking-stack/sockets-in-the-kernel.md` (its epoll section). `mmap`'s fault path already exists in folder 08 — link it → `../08-memory-management/the-page-fault-handler.md`. Delete the "Only the vDSO is linked…" sentence. |
| `08/the-page-cache.md` | "Folder 12 (block I/O) owns the mechanism in full; it is named here only so the trade-off…" | "[Buffered I/O, `O_DIRECT`, and Alignment](../12-block-layer-and-storage/buffered-direct-and-alignment.md) covers the mechanism in full; it is named here so the trade-off…" |
| `08/writeback-and-fsync.md` | "The block layer's side of this — how a flush request is represented and scheduled — belongs to folder 12, not here." | Link "how a flush request is represented" → `../12-block-layer-and-storage/the-bio.md`, and add one clause pointing at `../11-vfs-and-filesystems/journaling-and-crash-consistency.md` for what the filesystem does with it. |
| `10/threaded-irqs.md` | "…switches to **NAPI polling** once traffic is heavy enough (folder 13's networking material owns this mechanism; not yet written, named here only in prose), which amortizes…" | "…switches to **[NAPI polling](../13-networking-stack/the-receive-path.md)** once traffic is heavy enough, which amortizes…" |
| `10/interrupt-affinity-and-balancing.md` | "The network-specific mechanics of RSS/RPS belong to folder 13's networking material (not yet written, named here in prose only); this page owns the interrupt-placement layer…" | "The network-specific mechanics of RSS/RPS belong to [The Receive Path](../13-networking-stack/the-receive-path.md); this page owns the interrupt-placement layer…" |
| `00/hardware-the-kernel-assumes.md` | "This capability is owned by a later folder in this section, once timekeeping gets its own treatment; for now, treat 'a clock the kernel trusts' as a placeholder for a chapter that has not landed yet." and the table cell "Owned by a later folder in this section (not yet written)" | **Phase 2 leftover — folder 10 exists.** Link both to `../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md` and delete the placeholder wording. Note it separately in the commit message. |

- [ ] **Step 3: Apply any further fixes Step 1 found**, under the same rules.

- [ ] **Step 4: Confirm nothing links into 14–19 and every new link resolves**

```bash
rtk run "grep -rn -E '\.\./1[4-9]-' docs/linux docs/computer-science"
npm run build
```

Expected: no grep output, and a green build.

- [ ] **Step 5: Re-run the forward-reference grep** from Step 1, restricted to the wording patterns (`not yet written|in prose only|named here (only )?in prose|folder 1[1-3]`), and confirm every remaining hit refers to folders 14–19 or is not a forward reference at all.

- [ ] **Step 6: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/linux
git commit -m "docs: link folders 00-10 forward into the VFS, block, and networking pages"
```

---

## Task 22: Figures and `SOURCES.md` rows for the phase

**Files:**
- Modify: `static/img/linux/SOURCES.md`
- Modify: `static/img/cs/SOURCES.md`
- Create: `static/img/linux/block-layer-and-storage/<storage-stack figure>`
- Create: `static/img/linux/networking-stack/<netfilter figure>`
- Create: `static/img/cs/storage/<raid figure>`
- Modify: `docs/linux/12-block-layer-and-storage/the-block-layer-map.md`, `docs/linux/13-networking-stack/netfilter-and-nftables.md`, `docs/computer-science/storage/raid-and-redundancy.md`

**Interfaces:**
- Consumes: the written pages from Tasks 2–20 and the marked figure places in Tasks 10 and 19.
- Produces: the phase's figure set and its provenance rows, **batched deliberately** so the downloads and `SOURCES.md` rows happen once.

**Unlike Phase 2, this phase has two canonical figures the spec names outright:** the Thomas-Krenn storage-stack diagram (spec: "Fetch the Thomas-Krenn storage-stack diagram during 12's figure pass") and the netfilter packet-flow diagram. Both are dense reference figures that only work zoomable, paired with the page's own Mermaid simplification. The CS RAID figure is optional.

- [ ] **Step 1: Confirm the directory conventions.** Linux figures live at `static/img/linux/<folder-slug-without-numeric-prefix>/`, matching the existing `memory-management/` and `kernel-architecture-and-idioms/`. CS figures live at `static/img/cs/<section>/`. Both are referenced as `/img/...` with **no** `/knowledge-base` prefix.

- [ ] **Step 2: Fetch the Thomas-Krenn storage-stack diagram**

Open `https://www.thomas-krenn.com/en/wiki/Linux_Storage_Stack_Diagram` and choose the revision whose kernel version is **closest to v6.18**. Prefer its SVG; otherwise its largest PNG, downscaled to ≤ 1400 px wide. Record the exact file URL you downloaded, the kernel version the revision states, and its licence as shown on the page.

```bash
mkdir -p static/img/linux/block-layer-and-storage
curl -sSL -o static/img/linux/block-layer-and-storage/linux-storage-stack.svg '<exact URL from the wiki page>'
file static/img/linux/block-layer-and-storage/linux-storage-stack.svg
ls -l static/img/linux/block-layer-and-storage/
```

Expected: an SVG (or PNG) image, not an HTML error page, under ~1 MB. **Never guess a URL into `SOURCES.md`.**

- [ ] **Step 3: Fetch the netfilter packet-flow diagram**

Open `https://commons.wikimedia.org/wiki/File:Netfilter-packet-flow.svg`, confirm the author and licence on the file page, and download the original SVG from the "Original file" link.

```bash
mkdir -p static/img/linux/networking-stack
curl -sSL -o static/img/linux/networking-stack/netfilter-packet-flow.svg '<Original file URL from the Commons page>'
file static/img/linux/networking-stack/netfilter-packet-flow.svg
```

If the SVG renders badly in the browser (font substitution in dense labels), use Commons' own PNG rendering at ≤ 1400 px instead, and say so in the notes.

- [ ] **Step 4: Decide on the CS RAID figure**

`https://commons.wikimedia.org/wiki/File:RAID_5.svg` is a clean diagram of RAID 5 strip and parity placement. **Confirm its author and licence on the file page.** If it carries a licence acceptable under `static/img/cs/SOURCES.md`'s existing conventions (every existing row is a Commons licence), download Commons' PNG rendering to `static/img/cs/storage/raid-5.png`, following the CS convention that SVGs are stored as Commons' PNG rendering. If not, skip it — the page's Mermaid diagram and table already satisfy the anchor requirement. Record the decision.

- [ ] **Step 5: Consider the GIF candidates, and probably decline them**

The spec names a sliding TCP window and overlayfs copy-up as places where motion is the mechanism. Look for a clean one under 2 MB for each. Both are served well by the pages' existing diagrams, so if a suitable one is not found in a few minutes, decline. State in the commit message that they were considered, so a later phase does not re-litigate it.

- [ ] **Step 6: Add the `SOURCES.md` rows**

- `static/img/linux/SOURCES.md`: append one row per file, matching its columns exactly (`file | source_url | publisher | retrieved`, then `notes`). Notes must say:
  - for the storage stack: which kernel version the revision depicts, and whether the file is the original SVG or a downscaled PNG;
  - for netfilter: that it shows legacy xtables table names and the bridge path, and whether it is the original SVG or a PNG rendering.
- `static/img/cs/SOURCES.md` (only if Step 4 kept the figure): append a row in its own columns (`file | source | author | licence`).

- [ ] **Step 7: Place the figures**

At the marked places, each with a full `<Figure>` call — `src`, a descriptive `alt`, a `caption` saying what it shows, and `source`/`href`. The shape, adjusted to what was fetched:

```mdx
<Figure src="/img/linux/block-layer-and-storage/linux-storage-stack.svg"
        alt="The Linux storage stack from applications through the VFS, block layer, I/O schedulers and drivers to physical devices"
        caption="The whole storage stack for Linux 6.x (the revision closest to this section's pinned kernel) — zoom in; the Mermaid diagram above is the part this folder walks through."
        source="Thomas-Krenn wiki (Werner Fischer, Georg Schönberger)"
        href="https://www.thomas-krenn.com/en/wiki/Linux_Storage_Stack_Diagram" />
```

```mdx
<Figure src="/img/linux/networking-stack/netfilter-packet-flow.svg"
        alt="Netfilter packet flow through the raw, mangle, nat and filter tables at each hook, for both routed and bridged traffic"
        caption="Every netfilter hook and legacy table a packet can traverse, including the bridge path. nftables uses the same hooks with user-defined chains."
        source="Wikimedia Commons (Jan Engelhardt)"
        href="https://commons.wikimedia.org/wiki/File:Netfilter-packet-flow.svg" />
```

The CS RAID figure, if kept, also passes `license="<licence from the file page>"`. Replace the caption's version wording with the revision's actual kernel version.

- [ ] **Step 8: Check the size budget**

Run: `du -sh static/img/linux static/img/cs && du -sh static/img/linux/*`
Expected: no single new file over ~1 MB, and `static/img/linux/` still a few megabytes at most. If a file is too large, downscale it to ≤ 1400 px and note the modification in its row.

- [ ] **Step 9: Verify every figure renders and no orphans exist**

```bash
npm run build
rtk run "grep -rho '/img/linux/[^\"]*' docs/linux | sort -u"
rtk run "grep -rho '/img/cs/storage/[^\"]*' docs/computer-science | sort -u"
```

Cross-check against `SOURCES.md` and `ls -R static/img/linux static/img/cs/storage`: every referenced path exists, every file has a row, and every row has a file. Then `npm run serve` and confirm both zoomable figures open with `docusaurus-plugin-image-zoom` and remain legible when zoomed.

- [ ] **Step 10: Commit**

```bash
git add static/img/linux static/img/cs docs/linux docs/computer-science
git commit -m "docs: add phase 3 storage-stack and netfilter figures and SOURCES rows"
```

---

## Task 23: Extend the glossary

**Files:**
- Modify: `docs/linux/00-overview/glossary.md`

**Interfaces:**
- Consumes: all 36 Linux pages and 5 CS pages written in Tasks 2–20. This is an aggregation task and cannot start before they are done.
- Produces: the glossary extended by roughly 70–90 entries. Phase 4 appends to it in the same format.

The format is fixed and does not change: an alphabetised list, each entry a bolded term, an em dash, one or two sentences, and a link to the page that **owns** the term. No per-letter headings.

- [ ] **Step 1: Read the existing page first** and match its voice and entry length exactly. Several existing entries (for example **Address space (`address_space`)**, **Dirty page**) already touch this phase's material. Extend them with a second link where the new page genuinely owns more of the term; never duplicate an entry.
- [ ] **Step 2: Extract the real term list from the pages**, not from this plan. The terms below are a starting point; a term whose owning page does not define it properly does not get an entry.

- **From 11:** VFS, superblock, inode, dentry, negative dentry, dcache, `struct file`, file descriptor table, operations table, `nameidata`, RCU-walk, ref-walk, `openat2` resolve flags, mount, bind mount, mount propagation, peer group, mount namespace, new mount API, jbd2, `data=ordered`, commit interval, flush, FUA, `errseq_t`, extent, block group, htree, delayed allocation, fast commit, allocation group, copy-on-write filesystem, subvolume, reflink, tmpfs, shmem, ramfs, `seq_file`, sysfs, kernfs, debugfs, configfs, `Documentation/ABI`, overlayfs, lower/upper/work directory, copy-up, whiteout, opaque directory, FUSE, `/dev/fuse`, FUSE passthrough, virtiofs, `file_system_type`, libfs.
- **From 12:** block device, `gendisk`, `block_device`, logical block size, `bio`, `bio_vec`, plugging, `REQ_PREFLUSH`, blk-mq, software queue, hardware queue, tag, `queue_rq`, I/O scheduler, `mq-deadline`, BFQ, kyber, `none`, buffered I/O, direct I/O (`O_DIRECT`), `STATX_DIOALIGN`, `O_DSYNC`, `io_uring`, submission queue, completion queue, SQPOLL, IOPOLL, registered buffers, device mapper, dm target, dm table, LVM, thin pool, dm-crypt, md, md personality, resync, write-intent bitmap, `mismatch_cnt`, NVMe queue pair, doorbell, polled I/O, NVMe namespace, `iowait`, `%util`, I/O pressure, writeback throttling.
- **From 13:** `sk_buff`, headroom, `skb_shared_info`, `skb_clone`, `struct socket`, `struct sock`, `proto_ops`, accept queue, `somaxconn`, SYN cookies, NAPI, `netdev_budget`, GRO, RSS, RPS, RFS, XPS, drop reason, TSO/GSO, TCP Small Queues, BQL, qdisc, fq_codel, CoDel, htb, shaping, policing, clsact, netem, RACK-TLP, RTO, congestion control module, CUBIC, BBR, Nagle's algorithm, delayed ACK, `TIME_WAIT`, autotuning, TFO, netfilter hook, hook priority, nftables, `iptables-nft`, conntrack, `nf_conn`, ctstate, NAT mapping, masquerade, conntrack helper, FIB, policy routing rule, nexthop object, neighbour table, NUD state, `rp_filter`, network namespace, veth pair, bridge, FDB, macvlan, ipvlan, VXLAN, netlink/`sock_diag`, `nstat`.
- **Owned by the CS backfill pages** — link *there*, not to folder 11–13: RAID level, parity, write hole, rebuild/URE, crash consistency, write-ahead log, log-structured filesystem, socket (as an API concept), readiness vs completion, ARP, gratuitous ARP, ICMP, path MTU discovery, Neighbour Discovery, NAPT, endpoint-independent mapping, CGNAT, ALG, STUN/TURN/ICE.

- [ ] **Step 3: Enforce the one-owner rule.** Every entry links to exactly one page, and that page must genuinely introduce the term. Protocol and hardware concepts link to `computer-science/` pages (`../../computer-science/...` from this file); Linux mechanisms link into folders 11–13.
- [ ] **Step 4: Update the opening paragraph** to say the glossary covers folders 00–13 and still grows.
- [ ] **Step 5: Verify alphabetical order and links**

```bash
rtk run "grep -o '^\*\*[^*]*\*\*' docs/linux/00-overview/glossary.md"
npm run build
```

Scan the first command's output for ordering mistakes (the Phase 2 glossary needed a follow-up fix for exactly this), then confirm the build is green.

- [ ] **Step 6: Commit**

```bash
git add docs/linux/00-overview/glossary.md
git commit -m "docs: extend the glossary for folders 11-13"
```

---

## Task 24: Extend the misconceptions index, the roadmap, and the folder ladder

**Files:**
- Modify: `docs/linux/00-overview/misconceptions-index.md`
- Modify: `docs/linux/00-overview/roadmap.md`
- Modify: `docs/linux/00-overview/what-this-section-covers.md`

**Interfaces:**
- Consumes: every `## Misconceptions` section written in Tasks 4–20.
- Produces: the three overview pages back in agreement with the section's actual contents. **This is a mirroring task, not an authoring one** — if a page and the index disagree, the page wins.

- [ ] **Step 1: Collect the entries mechanically**

Run: `rtk run "grep -rn -A 12 '^## Misconceptions' docs/linux/11-vfs-and-filesystems docs/linux/12-block-layer-and-storage docs/linux/13-networking-stack"`

Work from that output. The plan marks twenty pages **[Misc]** in this phase:
- 11: why-vfs-exists, path-lookup, open-read-write, mounts, journaling, tmpfs, procfs-sysfs, overlayfs;
- 12: io-schedulers, buffered-direct, io-uring, software-raid, diagnosing-io;
- 13: sockets, receive-path, transmit-path, tcp, netfilter, conntrack, diagnosing-network.

The grep, not the marker list, is the authority.

- [ ] **Step 2: Append three groups to the index, in its existing format** — `## 11 — VFS and Filesystems`, `## 12 — The Block Layer and I/O`, `## 13 — The Networking Stack`, placed after `## 10 — Interrupts, Time, and Deferred Work`. Each entry: the belief in bold as someone would actually say it, the correction in two or three sentences, then the owning page's link on its own line (see the existing `## 10` group for the exact shape).

Where a belief already appears under `## 02 — Guided Traces` — for example "`write()` returning means the data is on disk", "One packet, one interrupt", "`O_DIRECT` means synchronous" — **keep the 02 entry unchanged** and add the folder 11–13 entry too, since the index mirrors pages and both pages carry it. Make sure the new entry's wording comes from the new page.

- [ ] **Step 3: Verify the mirroring in both directions.** Count the entries found in Step 1 and the entries added in Step 2; they must match. State both counts in the commit message.

- [ ] **Step 4: Extend `roadmap.md`.** Keep `<LearningPath>` exactly as used today; only step lists and the prose between paths change.

  - **"I just want to understand my machine"** — append `["Why the VFS exists", "../11-vfs-and-filesystems/why-vfs-exists.md"]`, `["The storage stack, mapped", "../12-block-layer-and-storage/the-block-layer-map.md"]`, and `["The network stack, mapped", "../13-networking-stack/the-network-stack-map.md"]`.
  - **"My server is slow"** — append `["Diagnosing I/O problems", "../12-block-layer-and-storage/diagnosing-io-problems.md"]` and `["Diagnosing network problems", "../13-networking-stack/diagnosing-network-problems.md"]`. Replace the closing sentence ("I/O and network diagnosis land with folders 12 and 13; the tooling to go with all of this lands with folder 17.") with one saying only that the tooling lands with folder 17 — unlinked.
  - **New: "I want to understand storage"** — preceded by one sentence saying it assumes the "I want to understand memory" path, and that path lookup leans on RCU from the concurrency path. Steps:
    1. `11/why-vfs-exists`
    2. `11/the-four-objects`
    3. `11/path-lookup-and-the-dcache`
    4. `11/open-read-write-in-the-kernel`
    5. `11/journaling-and-crash-consistency`
    6. `11/ext4`
    7. `12/the-block-layer-map`
    8. `12/block-devices-and-gendisk`
    9. `12/the-bio`
    10. `12/blk-mq`
    11. `12/io-schedulers`
    12. `12/buffered-direct-and-alignment`
    13. `12/io-uring`
    14. `12/diagnosing-io-problems`
  - **New: "I want to understand networking"** — preceded by one sentence naming its prerequisites outside the path: the softirq page and the CS sockets page. Steps:
    1. `13/the-network-stack-map`
    2. `13/sk-buff`
    3. `13/sockets-in-the-kernel`
    4. `13/the-receive-path`
    5. `13/the-transmit-path`
    6. `13/tcp-in-the-kernel`
    7. `13/netfilter-and-nftables`
    8. `13/connection-tracking-and-nat`
    9. `13/routing-and-neighbours`
    10. `13/network-namespaces-and-virtual-devices`
    11. `13/diagnosing-network-problems`
  - **Do not open "I want to work on containers" or "I want to write a driver" yet.** Both still cross folders 14–15.
  - Update `## Where the rest is`: folders 14 through 19 remain specified and not yet scaffolded, covering drivers, containers, security, observability, eBPF, and contributing.

  Use the step-label style of the existing paths (sentence case, backticks for code terms).

- [ ] **Step 5: Update the folder ladder** in `what-this-section-covers.md`: rows `11`, `12`, `13` change from `Specified` to the same status wording rows `05`–`10` use. Change the sentence "*folders `11` through `19` are specified but not yet written*" to name `14` through `19`, and check the nearby "their scope is fixed, their pages are not yet written" sentence still refers to the right folders. One table and one or two sentences; do not rewrite the page.

- [ ] **Step 6: Build and commit**

```bash
npm run build
git add docs/linux/00-overview
git commit -m "docs: extend the misconceptions index, roadmap, and folder ladder for folders 11-13"
```

---

## Task 25: Phase review, `CLAUDE.md`, and the written gate

**Files:**
- Modify: `CLAUDE.md`
- Modify: any page the review pass finds wanting

**Interfaces:**
- Consumes: everything.
- Produces: a phase that is actually finished, and repository documentation that matches the repository.

- [ ] **Step 1: Run the written gate**

Run: `npm run check:linux -- --written`
Expected: `check-linux-docs: OK — 159 written page(s), 0 stub(s)`. Any remaining stub is a page this plan missed; write it before continuing rather than adjusting the gate.

- [ ] **Step 2: Run the full gate set**

```bash
npm run build
npm run typecheck
npm run test:graph
npm run test:kernel-source
rtk run 'npm run lint'
```

Expected: all green. This is the phase's definition of done — fix anything that fails before proceeding.

- [ ] **Step 3: Review pass against the spec's per-phase checklist**

Walk all 41 pages (36 Linux + 5 CS) plus the Task 21 edits. Record findings in a scratch list, fix them, then re-run Step 2.

- Every topic page has a visual anchor, and its caption says *what it shows*.
- Every topic page has `## References` with 2–6 annotated entries and no bare URLs, and any source significantly older than v6.18 says so in its annotation. **Every URL in the phase has been opened** — this plan's URLs were leads, and a dead or moved link is a finding.
- Every topic page ends with `<KernelFacts>` whose `trap` is a real trap, not a restatement of the page.
- **Every symbol, path, struct field, sysctl, tracepoint, and counter named on a page has been checked against v6.18.** The block layer and networking code were heavily renamed in recent releases, so treat this as a per-page audit, not a spot check.
- Every arch-specific claim names its architecture. No arm64 contrast `:::note` is *required* in folders 11–13; confirm none was invented to fill a quota.
- Every `## Misconceptions` entry is mirrored in `misconceptions-index.md` (Task 24).
- `## What actually happens` appears only on pages this plan marks **[WAH]**: 11 → why-vfs-exists, path-lookup, open-read-write, mounts, journaling, procfs-sysfs; 12 → blk-mq, buffered-direct, diagnosing-io; 13 → sockets, receive-path, conntrack, diagnosing-network. Run `rtk run "grep -rln '^## What actually happens' docs/linux/1[1-3]-*"` and compare.
- Every `<Lab>` has a host badge, shows **measured** expected output, and closes with an "if it fails" line. Labs carrying a `:::danger` (`12/device-mapper-and-lvm`) have a host badge other than `any-linux`. Labs that change host settings (`13/network-namespaces-and-virtual-devices`, the conntrack WAH) include cleanup that restores them.
- The context7 verifications required by the spec were done and are dated in the pages' references: `io_uring` (12), nftables and `iproute2` and BBR (13).
- **No page links into folders 14–19**: `rtk run "grep -rn -E '\.\./1[4-9]-' docs/linux docs/computer-science"` prints nothing.
- `static/img/linux/SOURCES.md` and `static/img/cs/SOURCES.md` each have one row per file and no orphans in either direction.
- The no-duplication contract holds. Spot-check the seven pairs most at risk:
  - `11/journaling-and-crash-consistency` against the CS crash-consistency page;
  - `12/software-raid` against the CS RAID page;
  - `13/sockets-in-the-kernel` against the CS sockets page;
  - `13/connection-tracking-and-nat` against the CS NAT page;
  - `13/routing-and-neighbours` against the CS ARP/ICMP page;
  - `12/nvme-in-the-kernel` against `computer-science/storage/nvme-and-storage-interfaces`;
  - `11/why-vfs-exists` against `computer-science/storage/filesystems-basics`.

  None of the CS pages carries Linux mechanism; none of the Linux pages re-derives the theory.
- Every CS backfill page follows its folder's section template, and every CS backlink from Tasks 2–3 is present.

- [ ] **Step 4: Check the graph is meaningful, not just valid**

The build proves every `prerequisites` id resolves and that there are no cycles. Additionally, walk the two new learning paths from Task 24 and confirm that every prerequisite from folders 11–13 of every page on a path appears **earlier in that path**. Confirm that each prerequisite from outside the path is named in the sentence introducing it. A path that makes a reader jump forward is an editorial bug the build cannot catch.

- [ ] **Step 5: Verify the section in a production build**

```bash
npm run build && npm run serve
```

Open the section and check by eye:
- the three new folders appear in the sidebar in position order, with their descriptions on the generated index pages;
- a `<PrereqBlock>` on `13/sockets-in-the-kernel` shows a `CS`-badged "Before this" chip that leads to the sockets backfill page;
- the WaveDrom strips (`open()` flags, the ext4 extent header, the `sk_buff` buffer, the NVMe command) render;
- the `stateDiagram`s (TCP states, NUD states, md array states) render;
- the two zoomable figures open and are legible;
- the `<Tabs>` on `xfs-and-btrfs`, `io-uring` and `netfilter-and-nftables` switch;
- a `<Lab>` shows its host badge;
- the roadmap's new paths click through.

Serve, not dev.

- [ ] **Step 6: Update `CLAUDE.md`**

One surgical edit to the phase-status sentence in the "Linux & Kernel Internals section" block — `CLAUDE.md` is dense on purpose, so this is an update, not a rewrite. The block currently ends its status with Phase 2 bringing the section to 123 written pages and says folders `11`–`19` exist only in the spec. Replace that with:
- **Phase 3 wrote folders `11`–`13` (36 pages)** and CS backfill 12–16 (RAID, crash consistency, the sockets API, ARP/ICMP, NAT theory), bringing the section to **159 written pages**;
- folders `14`–`19` remain specified in the design spec only, not on disk, so no page may link into them;
- `npm run check:linux -- --written` is the gate, now covering folders 00–13.

Confirm the manifest sentence still reads correctly now that the manifest carries fourteen folders and fourteen external pages. Leave the component list, cast policy, and figure policy alone — none of them changed.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md docs/linux docs/computer-science
git commit -m "docs: update CLAUDE.md for phase 3 completion"
```

- [ ] **Step 8: Final verification**

```bash
npm run check:linux -- --written && npm run build && rtk run 'npm run lint'
git status
```

Expected: all green and a clean working tree. Report:
- the page count written;
- the gates run;
- the context7 checks and their dates;
- the figures added and declined;
- the forward references converted in Task 21;
- everything the review pass found and fixed.

---

## Self-review notes

**Spec coverage.** Every item in the spec's "Phase 3 ordering" has a task:

| Spec item | Tasks |
|---|---|
| 1. Scaffold folders 11–13; green build | Task 1 |
| 2. CS backfill 12 (RAID), 13 (crash consistency), 14 (sockets API), 15 (ARP/ICMP), 16 (NAT theory), plus backlinks | Task 2 (12, 13 + storage/databases backlinks), Task 3 (14, 15, 16 + networking/IPC backlinks), including the spec's required `filesystems-basics.md` edit |
| 3. Folders in order 11 → 12 → 13, each opening with its map page | Tasks 4–9 (11, `why-vfs-exists` first), 10–14 (12, `the-block-layer-map` first), 15–20 (13, `the-network-stack-map` first) |
| 4. Fetch the Thomas-Krenn storage-stack diagram in 12's figure pass | Task 22 Step 2, with the place for it left in Task 10 |
| 5. context7 verification for `io_uring` (12) and nftables/iproute2/BBR (13) | Task 12 Step 2; Task 18 Steps 1 and 3; Task 19 Step 1 |
| 6. Figures and labs pass, then the review checklist | Task 22 (figures), labs run inside their own tasks before their pages, Task 25 (review) |

Page counts match the spec's phase table: 36 Linux pages (13 + 11 + 12) and 5 CS backfill pages, 41 total. Every page in the spec's folder 11/12/13 outlines appears in Task 1's manifest tables with the spec's filename and title, and every spec **[WAH]** and **[Lab]** marker is carried into the briefs.

**Deliberate deviations, stated rather than hidden:**

- **Labs are run before their pages are written**, as in Phase 2. Expected output is measured, not predicted.
- **No casts are recorded.** The spec's outline marks `<Cast>` on the two diagnosis pages. Both ship their sessions as annotated ` ```text ` blocks (which the spec requires alongside any cast anyway), and the section's cast library is a single Phase 5 recording session.
- **Two labs moved to the full-system VM** (`io-schedulers`, `device-mapper-and-lvm`). The spec says only **[Lab]**; this plan picks `host="qemu"` because a scratch virtio disk makes them safe, and the device-mapper lab carries a `:::danger` that forbids `any-linux`.
- **One lab uses a host badge the spec did not specify** (`ext4` as `any-linux`): it runs entirely against an image file with `e2fsprogs`, no root and no mount.
- **Task 21 exists** although the spec lists no such step. Phases 1b and 2 deliberately wrote prose-only forward references ("folder 12 owns this", "named here in prose only"), and Rule 1's promise is that the link lands when the target does. The task also fixes one Phase 2 leftover: the timekeeping placeholder in `00/hardware-the-kernel-assumes`, whose target has existed since folder 10 was written.
- **Two learning paths are added beyond the spec's six** ("I want to understand storage", "I want to understand networking"), matching Phase 2's precedent of per-folder paths for large folders. The spec's containers and driver paths stay unopened because they still cross folders 14–15.
- **No arm64 contrast note is required in this phase.** The spec's list of structural contrasts falls in folders 05, 08, 09, 10 and 14; the plan says so explicitly rather than inventing one.

**Known risks, stated rather than hidden:**

- **Symbol drift is again the largest risk.** The block layer (`queue_limits` allocation, `bdev_file_open_by_path`, completion batching), the VFS (`try_to_unlazy`, the fs_context mount API that `lab-a-minimal-filesystem` depends on), and networking (drop reasons, netkit, FUSE passthrough, the io_uring FUSE transport) all changed recently. Every symbol in this plan is a starting point; each task carries a verification step, and Task 25 makes it a per-page audit.
- **The lab-a-minimal-filesystem module is the most version-sensitive code in the phase.** Tutorials online overwhelmingly use the pre-fs_context `.mount`/`mount_nodev` shape. Task 9 verifies the API before writing a line of the module, and requires the code on the page to be the code that ran.
- **Two claims are politically or operationally loaded and must be sourced, not asserted:** Btrfs RAID5/6 stability (cite the Btrfs project's own status page, dated) and `io_uring`'s security history (cite the primary source, with no exploit detail). Both briefs say so.
- **The BBR version in mainline is widely misreported.** Task 18 requires the source file to be the tiebreaker over any article or context7 result.
- **Several labs touch host networking or storage state** (mount namespaces, overlay mounts, a NAT rule, `ip_forward`). Each is scoped to a scratch namespace, a dedicated `lab` nftables table, or a VM scratch disk, with explicit cleanup, and the review step checks that cleanup exists.
