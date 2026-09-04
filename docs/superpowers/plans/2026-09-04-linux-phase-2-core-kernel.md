# Linux & Kernel Section — Phase 2 (Core Kernel) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and then write folders `05`–`10` of `docs/linux/` — system calls, processes and threads, scheduling, memory management, concurrency and locking, and interrupts/time/deferred work — 76 pages, plus the six `computer-science/` backfill pages those folders declare as prerequisites and the backlinks into them, leaving the section at a green `npm run build` with `npm run check:linux -- --written` passing for folders 00–10.

**Architecture:** No new site machinery at all. Everything this phase needs already exists and was proven in Phase 1a/1b: the manifest-driven scaffolder, the knowledge-graph build gate, `<PrereqBlock>` injection, and the eight MDX components. Phase 2 is therefore two kinds of work — one mechanical task that extends `tools/linux-docs-manifest.json` and regenerates the tree, then thirty-six writing tasks against fixed per-page briefs. The only new *assets* are a handful of figures and the `SOURCES.md` rows that keep them re-sourceable.

**Tech Stack:** Docusaurus 3.10.2, React 19, Mermaid (via `@docusaurus/theme-mermaid`), WaveDrom (`src/plugins/remark-wavedrom.js`), Biome 2.5.7, Node 22 (`node --test`), `docusaurus-plugin-image-zoom`, context7 MCP for currency checks.

**Spec:** `docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md` — this plan implements its "Phase 2 ordering" section.
**Predecessor plans:** `docs/superpowers/plans/2026-08-28-linux-phase-1a-infrastructure.md` (infrastructure + scaffold, executed), `docs/superpowers/plans/2026-08-29-linux-phase-1b-foundations.md` (folders 00–04 + CS backfill 1/2/17, executed).

---

## Global Constraints

- **Pinned kernel is `v6.18`** (`customFields.linuxKernelVersion` in `docusaurus.config.js`). Every source citation goes through `<Src file="..." symbol="..." />`. Never hand-write an `elixir.bootlin.com` URL, and never cite a line number — file plus symbol only.
- **Never invent a symbol, struct field, path, or config option.** Every symbol named on a page is checked against `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>` (or `/source/<file>` for a path) **before the page is committed**. Every symbol in this plan is an informed starting point, **not** a verified fact — several kernel internals were renamed recently (`__do_softirq` → `handle_softirqs`, `load_balance` → `sched_balance_rq`, the `_noprof` allocator suffixes, `mm/mmap.c` → `mm/vma.c` splits). Where a symbol has moved, cite what v6.18 actually has and say nothing about the old name unless the page's subject is the change itself.
- **Every doc under `docs/linux/` must carry a `prerequisites` front-matter key.** Empty array valid, missing key fails the build. The scaffolder writes it; do not remove it when turning a stub into a page. Add `related:` only if genuinely needed.
- **`onBrokenLinks: "throw"`.** Folders **11–19 are not scaffolded**, so no page may link into them. Where a page wants to point forward, it names the topic in prose with no link, and the link lands when the target does. Links *backwards* into folders 00–04 and *sideways* within 05–10 are free — Task 1 scaffolds all six folders before any of them is written, which is the entire point of Rule 1.
- **Relative doc links only** — `../08-memory-management/the-page-cache.md` style, never `/docs/linux/...`. `baseUrl` is `/knowledge-base/`.
- **`## What actually happens` is conditional.** Only on pages marked **[WAH]** in this plan. Adding it elsewhere is a review finding.
- **Every finished topic page ends with `<KernelFacts />` and carries a `## References` section** with 2–6 annotated entries. `tools/check-linux-docs.mjs` enforces both. No page in this phase is navigational, so no page in this phase is exempt.
- **Every page carries at least one visual anchor** — a Mermaid diagram, a WaveDrom `reg`/`signal` fence, a `<Figure>`, or a substantive comparison table — and its caption says *what it shows*, never "Diagram 3".
- **Visual vocabulary is fixed** (spec): Mermaid `flowchart` for code paths and layering, `stateDiagram-v2` for state machines, `sequenceDiagram` for cross-component interaction over time, WaveDrom `reg` for every bit-field layout, WaveDrom `signal` for genuine time axes, tables for comparison and enumeration. Do not draw a state machine as a flowchart.
- **Struct-heavy pages get a struct-*shape* diagram, not a struct dump.** `task_struct` is ~200 fields; show the dozen that matter grouped by concern and `<Src>` the real definition.
- **Fence languages:** kernel C → ` ```c `; Intel-syntax disassembly → ` ```nasm `; **AT&T asm, `Kconfig`, linker scripts, `gdb`/`perf`/`bpftrace` transcripts, `dmesg`, `/proc` dumps → ` ```text `; a `.config` fragment → ` ```ini `; unit files → ` ```systemd `; shell → ` ```bash `. All are already in `prism.additionalLanguages`.
- **Five admonitions only**: `:::info`, `:::note`, `:::tip`, `:::warning`, `:::danger`. `:::danger` is reserved for irreversible damage and states what is lost. A `<Lab>` carrying a `:::danger` may not have `host="any-linux"`.
- **Name the architecture on every arch-specific claim.** x86-64 is the spine. The arm64 contrast `:::note`s this phase owns are: syscall entry (`SVC` vs `SYSCALL`) in folder 05, page-table format and levels in folder 08, **memory ordering (weak vs TSO) in folder 09 — load-bearing, not decorative**, and interrupt controllers (GIC vs APIC) in folder 10.
- **No new asciinema casts in this phase.** `<Cast>` stays registered; terminal material ships as annotated ` ```text ` blocks. The section's cast library is recorded in one session in Phase 5.
- **Figures in `docs/linux/` are not licence-gated** (spec departure from `CLAUDE.md`), but every image file needs a row in `static/img/linux/SOURCES.md` and an on-page credit via `<Figure source= href= />`. **Figures in `docs/computer-science/` keep the repository's normal licence discipline** — `static/img/cs/SOURCES.md` carries a `licence` column and every row in it is a properly-licensed source. Do not carry the Linux exemption across into a CS page.
- **context7 verification is mandatory where the spec's table says so**, and the check date goes into the page's `## References` annotation: EEVDF and its tunables (folder 07), the folio API surface and MGLRU status (folder 08), the RCU API surface and `refcount_t` vs `atomic_t` guidance (folder 09).
- **`## Misconceptions` entries must be mirrored** into `00-overview/misconceptions-index.md` (Task 40). Write the page first; the index follows the page.
- **Biome** covers `**/*.{js,jsx,ts,tsx,json,md}` at 2-space indent. Run the lint gate raw — `rtk run 'npm run lint'` — because the Claude Code hook rewrites `npm run lint` to a different linter and will report a false pass.
- **Commit messages:** `<type>: <what>` on one line. **Never** a `Co-Authored-By` trailer, never a "Generated with Claude Code" line.

---

## File Structure

**Modified (machinery)**

| File | Change |
|---|---|
| `tools/linux-docs-manifest.json` | Six new folder objects (`05`–`10`, 76 pages) and six new `external` entries (the CS backfill pages). Nothing existing is edited. |

**Created by the scaffolder in Task 1 — never by hand**

| Path | Count |
|---|---|
| `docs/linux/05-syscalls-and-the-boundary/` + `_category_.json` | 10 pages |
| `docs/linux/06-processes-and-threads/` + `_category_.json` | 12 pages |
| `docs/linux/07-scheduling/` + `_category_.json` | 11 pages |
| `docs/linux/08-memory-management/` + `_category_.json` | 18 pages |
| `docs/linux/09-concurrency-and-locking/` + `_category_.json` | 13 pages |
| `docs/linux/10-interrupts-time-and-deferred-work/` + `_category_.json` | 12 pages |
| `docs/computer-science/cpu-architecture/memory-ordering-and-consistency.md` | backfill 3 |
| `docs/computer-science/cpu-architecture/atomic-operations-in-hardware.md` | backfill 4 |
| `docs/computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md` | backfill 6 |
| `docs/computer-science/memory-hierarchy/cache-coherence-and-mesi.md` | backfill 7 |
| `docs/computer-science/memory-hierarchy/numa-and-memory-topology.md` | backfill 8 |
| `docs/computer-science/buses-and-io/interrupt-controllers.md` | backfill 10 |

**Modified (existing CS pages — small, additive backlinks only, no rewrites)**

| File | Edit |
|---|---|
| `docs/computer-science/operating-systems/concurrency-and-synchronization.md` | Pointers to backfill 3, 4, 7 and to `linux/09-concurrency-and-locking`. |
| `docs/computer-science/operating-systems/scheduling.md` | Pointer to `linux/07-scheduling` for the real implementation. **No EEVDF detail here** — folder 07 owns it. |
| `docs/computer-science/operating-systems/processes-and-threads.md` | One pointer into `linux/06-processes-and-threads`. |
| `docs/computer-science/operating-systems/memory-management.md` | One pointer into `linux/08-memory-management`. |
| `docs/computer-science/operating-systems/interprocess-communication.md` | One pointer into `linux/06-processes-and-threads/pipes-fifos-and-unix-sockets`. |
| `docs/computer-science/memory-hierarchy/virtual-memory-and-paging.md` | Closing pointer to `linux/08-memory-management/page-tables-and-the-walk`, and to backfill 6. |
| `docs/computer-science/memory-hierarchy/cpu-caches.md` | Pointer to backfill 7 (coherence) and backfill 6 (TLB). |
| `docs/computer-science/cpu-architecture/multicore-and-parallelism.md` | Pointers to backfill 3, 4, 7, 8. |
| `docs/computer-science/buses-and-io/io-and-interrupts.md` | Pointer to backfill 10 and to `linux/10-interrupts-time-and-deferred-work`. |
| `docs/computer-science/assembly/calling-conventions-and-the-stack.md` | Confirm the ABI covered is x86-64 System V; add the **syscall** calling convention and a pointer to `linux/05-syscalls-and-the-boundary`. |

**Modified (section pages)**

| File | Change |
|---|---|
| `docs/linux/00-overview/glossary.md` | Extended with the terms folders 05–10 introduce. |
| `docs/linux/00-overview/misconceptions-index.md` | Extended with every `## Misconceptions` entry written in this phase. |
| `docs/linux/00-overview/roadmap.md` | Four learning paths extended into the new folders; two spec paths ("My server is slow", "I want to write a driver") partially opened. |
| `docs/linux/00-overview/what-this-section-covers.md` | Its folder-ladder table marks 05–10 as written. |
| `static/img/linux/SOURCES.md` | One row per figure added in Task 38. |
| `CLAUDE.md` | Phase status line updated. |

**Untouched, deliberately:** every file under `src/`, `tools/scaffold-linux-docs.mjs`, `tools/check-linux-docs.mjs`, `scripts/*.test.mjs`, `docusaurus.config.js`, `sidebars.js`. If a task seems to need a change under `src/`, stop — Phase 2 is content, and a component change is a signal that a page is fighting the conventions rather than using them.

---

## Doc-id reference

Docusaurus's `numberPrefixParser` strips the `NN-` from folder segments, so a page's real doc id — the form `prerequisites:` and `related:` must use — has no numeric prefix. This plan writes prerequisites in the short form `08/the-page-cache`; expand it with this table when writing the manifest.

| Short form | Real doc id prefix |
|---|---|
| `00/…` | `linux/overview/…` |
| `01/…` | `linux/lab-and-toolchain/…` |
| `02/…` | `linux/guided-traces/…` |
| `03/…` | `linux/boot-and-init/…` |
| `04/…` | `linux/kernel-architecture-and-idioms/…` |
| `05/…` | `linux/syscalls-and-the-boundary/…` |
| `06/…` | `linux/processes-and-threads/…` |
| `07/…` | `linux/scheduling/…` |
| `08/…` | `linux/memory-management/…` |
| `09/…` | `linux/concurrency-and-locking/…` |
| `10/…` | `linux/interrupts-time-and-deferred-work/…` |
| `cs:…` | `computer-science/…` (full path, no prefix stripping needed — those folders are unnumbered) |

---

## Page brief format

Every writing task below gives, per page:

- **Opens with** — the mental-model paragraph. No page opens with a struct, a command, or a code block.
- **Sections** — the `##` headings, in order, each with what it must establish.
- **Anchor** — the required visual, and what it must show.
- **KernelFacts** — starting values for the four fixed rows. **Verify every symbol against Elixir v6.18 before committing.**
- **References** — concrete sources; annotate each with why a reader clicks it.

`[WAH]` = the page carries `## What actually happens`. `[Lab host=…]` = the page carries a `<Lab>` with that host badge, expected output, and a closing "if it fails" line. `[Misc]` = the page carries `## Misconceptions`, mirrored into the index in Task 40.

---

## Task 1: Extend the manifest and scaffold folders 05–10

**Files:**
- Modify: `tools/linux-docs-manifest.json`
- Create (by running the scaffolder): 76 stub pages, 6 `_category_.json` files, 6 CS backfill stubs

**Interfaces:**
- Consumes: the manifest schema already established for folders 00–04 (`folders[].pages[]` with `file`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `prerequisites`, optional `related`, `summary`; and `external[]` with `path`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `summary`).
- Produces: every doc id every later task in this phase links to or declares as a prerequisite. **Nothing after this task may be started until the build is green**, because a missing node fails the graph plugin rather than degrading quietly.

- [ ] **Step 1: Append the six folder objects to `manifest.folders`**

Append after the `04-kernel-architecture-and-idioms` object, in numeric order. Each folder object takes `"roadmapLink": "../00-overview/roadmap.md"`. Folder-level values:

| dir | label | position | description |
|---|---|---|---|
| `05-syscalls-and-the-boundary` | System Calls | 6 | How a user-space instruction becomes kernel code running on your behalf: the entry path, the dispatch table, the register ABI, the rules for copying data, and the ways to watch a syscall happen. |
| `06-processes-and-threads` | Processes and Threads | 7 | What Linux actually schedules and how one comes into existence: `task_struct`, `clone()` as a menu of what to share, fork and exec, address spaces, signals, exit, and `/proc` as the window onto all of it. |
| `07-scheduling` | Scheduling | 8 | Who runs next, for how long, and on which CPU — runqueues and scheduling classes, EEVDF, preemption models, the context switch, load balancing, and how to find the cause of scheduling latency. |
| `08-memory-management` | Virtual Memory and Memory Management | 9 | How Linux turns physical memory into the address space every process believes it owns: page tables, faults, allocators, the page cache, writeback, reclaim, swap, huge pages, and what the memory numbers actually mean. |
| `09-concurrency-and-locking` | Concurrency and Locking | 10 | Four independent sources of concurrency, the contexts that may not sleep, and every synchronisation primitive the kernel offers — from memory barriers and spinlocks through RCU to per-CPU data. |
| `10-interrupts-time-and-deferred-work` | Interrupts, Time, and Deferred Work | 11 | How hardware interrupts the kernel and what the kernel does about it: the IRQ subsystem, hard-IRQ rules, softirqs, workqueues, threaded handlers, clocksources, the tick, and timers. |

Tags per folder, applied to every page in it: `05` → `["linux", "kernel", "syscalls"]`; `06` → `["linux", "kernel", "processes"]`; `07` → `["linux", "kernel", "scheduling"]`; `08` → `["linux", "kernel", "memory-management"]`; `09` → `["linux", "kernel", "locking"]`; `10` → `["linux", "kernel", "interrupts"]`.

- [ ] **Step 2: Add folder 05's ten pages**

`sidebar_position` is the row number. Prerequisites are in short form — expand with the doc-id table above.

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `what-a-system-call-actually-is` | What a System Call Actually Is | What a syscall is | `00/the-kernel-userspace-boundary` | Not a function call but a hardware-mediated privilege transition into code you do not control, at an entry point you cannot choose. |
| 2 | `the-entry-path` | The Entry Path | The entry path | `05/what-a-system-call-actually-is` | What the CPU does and what software does between the `SYSCALL` instruction and the kernel function that services it. |
| 3 | `the-syscall-table-and-dispatch` | The Table and the Dispatch | Table and dispatch | `05/the-entry-path` | A syscall number as an index, the `SYSCALL_DEFINEn` macro expanded step by step, and why the numbers are frozen forever. |
| 4 | `arguments-return-values-and-errno` | Arguments, Returns, and errno | Arguments and errno | `05/the-syscall-table-and-dispatch` | The register ABI, the six-argument limit, negative-errno returns, and where user-space `errno` actually comes from. |
| 5 | `copying-data-across-the-boundary` | Copying Data Across the Boundary | Copying data | `05/the-entry-path` | Why the kernel may never dereference a user pointer, and the machinery that turns a bad one into `-EFAULT` instead of an oops. |
| 6 | `the-vdso` | The vDSO | The vDSO | `05/what-a-system-call-actually-is` | A kernel-provided shared object mapped into every process, and why some "syscalls" never cross the boundary at all. |
| 7 | `libc-is-not-the-kernel` | libc Is Not the Kernel | libc is not the kernel | `05/arguments-return-values-and-errno` | What glibc and musl add on top of the raw interface, and why `strace` output and your source code so often disagree. |
| 8 | `abi-stability-and-compat` | ABI Stability and Compat | ABI stability | `05/the-syscall-table-and-dispatch` | "We do not break user space" as an engineering constraint with real consequences, and how 32-on-64 compatibility is implemented. |
| 9 | `tracing-and-intercepting-syscalls` | Tracing and Intercepting Syscalls | Tracing syscalls | `05/the-entry-path` | How `strace` actually works, what it costs, what `perf trace` does instead, and why `LD_PRELOAD` is not syscall interception. |
| 10 | `lab-adding-a-syscall` | Lab: Add a System Call | Lab: add a syscall | `05/the-syscall-table-and-dispatch`, `01/building-a-kernel` | End to end in the QEMU lab: define it, wire the table, rebuild, boot, call it, and watch it in `strace`. |

Page 2 also carries `"related": ["computer-science/cpu-architecture/privilege-levels-and-protection", "computer-science/cpu-architecture/exceptions-traps-and-interrupts"]`. Page 4 also carries `"related": ["computer-science/assembly/calling-conventions-and-the-stack"]`.

- [ ] **Step 3: Add folder 06's twelve pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `task-struct-the-anatomy-of-a-task` | `task_struct`: The Anatomy of a Task | task_struct | `04/kernel-data-structures` | The kernel's unit of scheduling — not the two hundred fields, the twelve that matter, grouped by concern. |
| 2 | `threads-are-tasks` | Threads Are Tasks | Threads are tasks | `06/task-struct-the-anatomy-of-a-task` | Linux has no separate thread object: a thread is a task that shares its address space, files, and signal handlers. |
| 3 | `fork-and-copy-on-write` | `fork()` and Copy-on-Write | fork and COW | `06/threads-are-tasks` | What actually gets copied when a process forks, which is far less than people expect, and how the first write resolves. |
| 4 | `exec-and-binary-formats` | `exec()` and Binary Formats | exec and ELF | `06/fork-and-copy-on-write` | Tearing down one address space and building another from an ELF file, an interpreter, and a `#!` line. |
| 5 | `the-process-address-space` | A Process's Address Space | Address space | `06/task-struct-the-anatomy-of-a-task` | The map a task sees — text, data, heap, mmap region, stack, vDSO — read line by line out of `/proc/PID/maps`. |
| 6 | `credentials-and-identity` | Credentials and Identity | Credentials | `06/task-struct-the-anatomy-of-a-task` | `struct cred`, the four kinds of user ID, and how a setuid binary actually transitions. |
| 7 | `process-states-and-wait-queues` | Process States and Wait Queues | States and wait queues | `06/task-struct-the-anatomy-of-a-task` | The task state machine, wait queues as the universal blocking mechanism, and why a `D`-state process cannot be killed. |
| 8 | `exit-zombies-and-orphans` | Exit, Zombies, and Orphans | Exit and zombies | `06/process-states-and-wait-queues` | What exiting frees, what it cannot free until the parent reaps, and why a zombie army means a buggy parent. |
| 9 | `signals` | Signals | Signals | `06/process-states-and-wait-queues` | Generation, pending sets, and delivery on the return to user space — not at the moment the signal is sent. |
| 10 | `pipes-fifos-and-unix-sockets` | Pipes, FIFOs, and UNIX Sockets | Pipes and UNIX sockets | `06/the-process-address-space` | The IPC processes actually use, at the kernel level: a ring of pages, `splice`, socket pairs, and passing a file descriptor. |
| 11 | `proc-as-the-process-interface` | `/proc` as the Process Interface | /proc | `06/task-struct-the-anatomy-of-a-task` | Not a filesystem of files but a set of views generated on read from live kernel structures. |
| 12 | `lab-watching-a-process-be-born` | Lab: Watch a Process Be Born | Lab: a process is born | `06/fork-and-copy-on-write`, `06/exec-and-binary-formats` | The same fork-and-exec event seen from three tools: a tracepoint, `perf trace`, and a GDB breakpoint in the QEMU lab. |

Page 6 also carries `"related": ["computer-science/operating-systems/processes-and-threads"]`. Page 10 also carries `"related": ["computer-science/operating-systems/interprocess-communication"]`.

- [ ] **Step 4: Add folder 07's eleven pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `what-the-scheduler-must-decide` | What the Scheduler Must Decide | What it decides | `06/process-states-and-wait-queues` | Three separate questions — who runs next, for how long, and on which CPU — answered by three separate mechanisms. |
| 2 | `runqueues-and-scheduling-classes` | Runqueues and Scheduling Classes | Runqueues and classes | `07/what-the-scheduler-must-decide` | The per-CPU runqueue and the ordered class hierarchy that `pick_next_task` walks. |
| 3 | `cfs-and-vruntime` | CFS and Virtual Runtime | CFS and vruntime | `07/runqueues-and-scheduling-classes` | The design that ran Linux for fifteen years, and what it could not do — the setup for what replaced it. |
| 4 | `eevdf` | EEVDF: The Current Fair Scheduler | EEVDF | `07/cfs-and-vruntime` | Lag, eligibility, and request size, and how latency-sensitivity became a first-class input instead of a heuristic. |
| 5 | `priorities-nice-and-weights` | Priorities, nice, and Weights | nice and weights | `07/eevdf` | What a nice level actually buys, the weight table behind it, and why priority means different things per class. |
| 6 | `preemption-models` | Preemption Models | Preemption models | `07/runqueues-and-scheduling-classes` | Where the kernel is and is not preemptible, and the latency-versus-throughput trade-off made concrete. |
| 7 | `the-context-switch` | The Context Switch | Context switch | `07/runqueues-and-scheduling-classes` | What gets saved, by whom, and where the cost actually lands — including the TLB and FPU consequences. |
| 8 | `smp-load-balancing` | SMP and Load Balancing | Load balancing | `07/the-context-switch` | Scheduling domains built from the hardware topology, and why a thread that moved CPUs got slower. |
| 9 | `real-time-scheduling` | Real-Time Scheduling | Real-time | `07/runqueues-and-scheduling-classes`, `07/preemption-models` | `SCHED_FIFO`, `SCHED_RR`, and `SCHED_DEADLINE`'s admission control, plus the throttling that stops a runaway task. |
| 10 | `cgroup-cpu-control` | cgroup CPU Control | cgroup CPU control | `07/eevdf` | `cpu.weight` and `cpu.max`, and why a container hitting its quota stalls in long pauses instead of running proportionally slower. |
| 11 | `diagnosing-scheduling-latency` | Diagnosing Scheduling Latency | Diagnosing latency | `07/the-context-switch`, `07/cgroup-cpu-control` | A worked investigation from "the app is janky" to a named cause, using schedstats, PSI, and the scheduler tracepoints. |

Page 1 also carries `"related": ["computer-science/operating-systems/scheduling"]`. Page 8 also carries `"related": ["computer-science/memory-hierarchy/numa-and-memory-topology", "computer-science/memory-hierarchy/cache-coherence-and-mesi"]`.

- [ ] **Step 5: Add folder 08's eighteen pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `the-virtual-address-space` | The Virtual Address Space | The address space | `06/the-process-address-space` | The x86-64 layout: canonical addresses and the hole, the user/kernel split, the direct map, and what KASLR moves. |
| 2 | `page-tables-and-the-walk` | Page Tables and the Walk | Page tables | `08/the-virtual-address-space` | Four levels (and five) walked from `CR3` to a physical address with real numbers, and what each PTE bit means. |
| 3 | `tlb-and-address-space-switching` | The TLB and Address-Space Switching | TLB and switching | `08/page-tables-and-the-walk` | Why translation is cached, what a miss costs, and why a TLB shootdown is a cross-CPU operation with a real price. |
| 4 | `mm-struct-and-vmas` | `mm_struct` and VMAs | mm_struct and VMAs | `08/the-virtual-address-space` | The kernel's own description of an address space, and `/proc/PID/maps` as a rendering of it. |
| 5 | `the-page-fault-handler` | The Page Fault Handler | Page fault handler | `08/page-tables-and-the-walk`, `08/mm-struct-and-vmas` | From the CPU exception to a resolved mapping, a swapped-in page, or a `SIGSEGV` — the folder's most important code path. |
| 6 | `demand-paging-and-cow` | Demand Paging and Copy-on-Write | Demand paging and COW | `08/the-page-fault-handler` | Nothing is allocated until touched, which is why `malloc` of 100 GB succeeds on a machine with 8 GB. |
| 7 | `the-page-allocator` | The Page Allocator | Page allocator | `08/the-virtual-address-space` | Zones, the buddy allocator's splitting and coalescing, GFP flags, watermarks, and fragmentation. |
| 8 | `slab-slub-and-kmalloc` | Slab, SLUB, and `kmalloc` | Slab and kmalloc | `08/the-page-allocator` | Object caching above the page allocator, the size classes `kmalloc` rounds to, and how to find a slab leak. |
| 9 | `vmalloc-and-choosing-an-allocator` | `vmalloc` and Choosing an Allocator | Choosing an allocator | `08/slab-slub-and-kmalloc` | Virtually contiguous versus physically contiguous, and a decision table across every kernel allocation interface. |
| 10 | `folios-and-compound-pages` | Folios and Compound Pages | Folios | `08/the-page-allocator` | Why `struct page` was too small a unit, what a folio is, and how to read code written on either side of the conversion. |
| 11 | `the-page-cache` | The Page Cache | Page cache | `08/folios-and-compound-pages` | Where file data lives, why the second `grep` of a file is instant, and how `read()` and `mmap()` both land in the same place. |
| 12 | `writeback-and-fsync` | Writeback, Dirty Pages, and `fsync` | Writeback and fsync | `08/the-page-cache` | Dirty tracking, the writeback threads, and exactly what `fsync` guarantees — including the barrier that must reach the device. |
| 13 | `reclaim-lru-and-kswapd` | Reclaim, LRU, and kswapd | Reclaim | `08/the-page-cache` | How the kernel finds pages to take back, and why direct reclaim is a latency event rather than a background one. |
| 14 | `swap-and-zswap` | Swap, zswap, and zram | Swap | `08/reclaim-lru-and-kswapd` | What swapping actually is, what `swappiness` really weighs, and why "disable swap for performance" is usually wrong. |
| 15 | `the-oom-killer` | The OOM Killer | OOM killer | `08/reclaim-lru-and-kswapd` | What happens when reclaim fails, how the victim is chosen, and how to read the OOM report field by field. |
| 16 | `hugepages-and-thp` | Huge Pages and THP | Huge pages | `08/page-tables-and-the-walk`, `08/tlb-and-address-space-switching` | TLB reach as the actual benefit, explicit hugetlbfs versus transparent huge pages, and THP's latency cost. |
| 17 | `numa-and-memory-policy` | NUMA and Memory Policy | NUMA policy | `08/the-page-allocator` | Node-local allocation by default, the policies that override it, and when NUMA effects are a red herring. |
| 18 | `what-free-and-rss-really-say` | What `free` and RSS Really Tell You | free and RSS | `08/the-page-cache`, `08/reclaim-lru-and-kswapd` | How to actually answer "how much memory is this using", and why every simple answer to that question is wrong. |

Page 1 also carries `"related": ["computer-science/memory-hierarchy/virtual-memory-and-paging"]`. Page 3 also carries `"related": ["computer-science/memory-hierarchy/tlb-and-address-translation-hardware"]`. Page 17 also carries `"related": ["computer-science/memory-hierarchy/numa-and-memory-topology"]`.

- [ ] **Step 6: Add folder 09's thirteen pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `why-kernel-concurrency-is-different` | Why Kernel Concurrency Is Different | Why it is different | `04/the-kernel-c-dialect` | Four independent sources of concurrency and the context matrix that determines every locking choice in the folder. |
| 2 | `memory-ordering-and-barriers` | Memory Ordering and Barriers | Ordering and barriers | `09/why-kernel-concurrency-is-different` | Why a plain access is not safe, what each barrier actually orders, and why this is the page arm64 changes the most. |
| 3 | `atomics-and-refcounts` | Atomic Operations | Atomics | `09/memory-ordering-and-barriers` | `atomic_t`, the operation families, the ordering each does and does not carry, and why `refcount_t` exists separately. |
| 4 | `spinlocks` | Spinlocks | Spinlocks | `09/atomics-and-refcounts` | Busy-waiting and when it is right, the queued implementation, and the absolute rule against sleeping while holding one. |
| 5 | `mutexes-and-semaphores` | Mutexes and Semaphores | Mutexes | `09/spinlocks` | Sleeping locks that spin first, owner tracking, and why semaphores are now rare. |
| 6 | `rwlocks-and-rwsems` | Reader-Writer Locks | Reader-writer locks | `09/mutexes-and-semaphores` | Why a reader-writer lock is often slower than a plain one, and where `rw_semaphore` is genuinely the right answer. |
| 7 | `seqlocks` | Seqlocks | Seqlocks | `09/memory-ordering-and-barriers` | Lockless readers with a retry loop, the constraints that puts on a reader, and the canonical use in timekeeping. |
| 8 | `rcu-the-idea` | RCU: The Idea | RCU: the idea | `09/memory-ordering-and-barriers` | Readers that take no locks and pay nothing, writers that publish a new version and defer reclamation until every reader has left. |
| 9 | `rcu-in-practice` | RCU in Practice | RCU in practice | `09/rcu-the-idea` | The API, the ordering it encodes, and the rules that make RCU misuse silently fatal rather than loudly wrong. |
| 10 | `per-cpu-data` | Per-CPU Data | Per-CPU data | `09/why-kernel-concurrency-is-different` | Eliminating sharing rather than protecting it, and what that costs in preemption discipline. |
| 11 | `lock-free-and-ring-buffers` | Lock-Free Patterns | Lock-free patterns | `09/memory-ordering-and-barriers`, `09/per-cpu-data` | Where the kernel genuinely goes lock-free, and an honest account of why most kernel code should not. |
| 12 | `choosing-a-lock` | Choosing a Lock | Choosing a lock | `09/spinlocks`, `09/mutexes-and-semaphores`, `09/rcu-in-practice` | The decision table, six worked selections, and the cost hierarchy from an uncontended atomic to cross-NUMA ping-pong. |
| 13 | `finding-locking-bugs` | Finding Locking Bugs | Finding bugs | `09/choosing-a-lock` | `lockdep` and what it proves, KCSAN for data races, and a real splat read line by line. |

Page 1 also carries `"related": ["computer-science/operating-systems/concurrency-and-synchronization"]`. Page 2 also carries `"related": ["computer-science/cpu-architecture/memory-ordering-and-consistency"]`. Page 3 also carries `"related": ["computer-science/cpu-architecture/atomic-operations-in-hardware"]`. Pages 6 and 10 also carry `"related": ["computer-science/memory-hierarchy/cache-coherence-and-mesi"]`.

- [ ] **Step 7: Add folder 10's twelve pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `how-an-interrupt-reaches-the-kernel` | How an Interrupt Reaches the Kernel | An interrupt arrives | `05/the-entry-path` | Device to interrupt controller to CPU vector to kernel entry stub, and where the hardware stops and software starts. |
| 2 | `the-irq-subsystem` | The IRQ Subsystem | The IRQ subsystem | `10/how-an-interrupt-reaches-the-kernel` | `irq_desc`, irq chips, irq domains, and the return-value contract that makes shared interrupts work. |
| 3 | `hardirq-context` | Hard IRQ Context and Its Rules | Hard IRQ context | `10/the-irq-subsystem`, `09/why-kernel-concurrency-is-different` | What a handler may not do, why each rule follows from the context, and the pressure that creates the rest of the folder. |
| 4 | `softirqs` | Softirqs | Softirqs | `10/hardirq-context` | The fixed set, why it is fixed, the budget that stops it starving everything else, and the `si` column in `top`. |
| 5 | `tasklets-and-their-replacement` | Tasklets, and Why They Are Going Away | Tasklets | `10/softirqs` | The model, its serialisation guarantee, the problems that deprecated it, and what to use instead. |
| 6 | `workqueues` | Workqueues | Workqueues | `10/hardirq-context` | Deferred work in process context, so it may sleep — plus the cancel-versus-free lifetime bug everyone writes once. |
| 7 | `threaded-irqs` | Threaded IRQs | Threaded IRQs | `10/workqueues`, `07/real-time-scheduling` | A quick primary handler plus a schedulable thread, and why PREEMPT_RT makes nearly every handler threaded. |
| 8 | `interrupt-affinity-and-balancing` | Interrupt Affinity | Affinity | `10/the-irq-subsystem` | `/proc/interrupts` read column by column, MSI-X vectors per queue, and why pinning an interrupt near its consumer matters. |
| 9 | `timekeeping-and-clocksources` | Timekeeping and Clocksources | Timekeeping | `10/how-an-interrupt-reaches-the-kernel` | How a clocksource is chosen, what each `CLOCK_*` actually measures, and the lockless read path behind `clock_gettime`. |
| 10 | `the-tick-and-nohz` | The Tick, and Living Without It | The tick and NOHZ | `10/timekeeping-and-clocksources` | What the periodic tick was doing, what turning it off moves elsewhere, and CPU isolation for latency-sensitive work. |
| 11 | `timers-and-hrtimers` | Timers and High-Resolution Timers | Timers | `10/the-tick-and-nohz` | The timer wheel's deliberate imprecision, hrtimers with real deadlines, and which one a driver should choose. |
| 12 | `delays-and-sleeps` | Delays and Sleeps: What They Really Do | Delays and sleeps | `10/timers-and-hrtimers` | Busy-wait delays, sleeping delays, and the guarantee every one of them lacks. |

Page 1 also carries `"related": ["computer-science/buses-and-io/interrupt-controllers", "computer-science/cpu-architecture/exceptions-traps-and-interrupts"]`. Page 9 also carries `"related": ["linux/concurrency-and-locking/seqlocks"]`.

- [ ] **Step 8: Add the six CS backfill entries to `manifest.external`**

Same shape as the three already there. `sidebar_position` values are chosen to append after each folder's existing pages — check the folder before writing, and if a position now collides, take the next free integer rather than renumbering existing pages.

| path | id | title | sidebar_label | position | tags | summary |
|---|---|---|---|---|---|---|
| `docs/computer-science/cpu-architecture/memory-ordering-and-consistency.md` | `memory-ordering-and-consistency` | Memory Ordering and Consistency | Memory ordering | 9 | `["computer-science", "cpu-architecture", "concurrency"]` | Why a multiprocessor does not execute your loads and stores in the order you wrote them, and what a fence actually buys. |
| `docs/computer-science/cpu-architecture/atomic-operations-in-hardware.md` | `atomic-operations-in-hardware` | Atomic Operations in Hardware | Hardware atomics | 10 | `["computer-science", "cpu-architecture", "concurrency"]` | Compare-and-swap, load-linked/store-conditional, and what an atomic instruction costs in cache-line ownership. |
| `docs/computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md` | `tlb-and-address-translation-hardware` | The TLB and Address-Translation Hardware | The TLB | 5 | `["computer-science", "memory-hierarchy", "virtual-memory"]` | The cache that makes virtual memory affordable: TLB structure, page-walk caches, address-space tags, and shootdown cost. |
| `docs/computer-science/memory-hierarchy/cache-coherence-and-mesi.md` | `cache-coherence-and-mesi` | Cache Coherence and MESI | Cache coherence | 6 | `["computer-science", "memory-hierarchy", "concurrency"]` | How several caches holding the same line stay consistent, and why two unrelated variables in one line can destroy performance. |
| `docs/computer-science/memory-hierarchy/numa-and-memory-topology.md` | `numa-and-memory-topology` | NUMA and Memory Topology | NUMA | 7 | `["computer-science", "memory-hierarchy", "numa"]` | When "main memory" stops being one thing: node distance, local versus remote latency, and what interleaving trades away. |
| `docs/computer-science/buses-and-io/interrupt-controllers.md` | `interrupt-controllers` | Interrupt Controllers | Interrupt controllers | 6 | `["computer-science", "buses-and-io", "interrupts"]` | The hardware between a device asserting a line and a CPU taking an interrupt: PIC, APIC, MSI, and Arm's GIC. |

- [ ] **Step 9: Validate the manifest is well-formed JSON**

Run: `node -e "const m=require('./tools/linux-docs-manifest.json'); console.log(m.folders.length, m.folders.reduce((n,f)=>n+f.pages.length,0), m.external.length)"`
Expected: `11 122 9` — eleven folders, 122 manifest pages (46 from Phase 1 + 76 new), nine external pages. Note that `docs/linux/readme.md` is **not** manifest-owned, which is why the on-disk page count is one higher than the manifest's.

- [ ] **Step 10: Scaffold**

Run: `npm run scaffold:linux`
Expected: `scaffold: 82 file(s) created, 49 left alone, 11 category file(s) written` — 76 new stubs plus 6 CS backfill stubs created, and the 46 Phase 1 pages plus the 3 Phase 1 external pages left alone. The 49 left alone are the Phase 1 pages — **if any of them is reported as created, stop and restore it from git**: that means `--force` leaked in and a finished page was overwritten with a stub.

- [ ] **Step 11: Confirm nothing existing was clobbered**

```bash
git status --short docs/linux
git diff --stat docs/linux/00-overview docs/linux/01-lab-and-toolchain docs/linux/02-guided-traces docs/linux/03-boot-and-init docs/linux/04-kernel-architecture-and-idioms
```

Expected: the second command prints nothing (`_category_.json` files are regenerated but byte-identical, since the manifest entries for folders 00–04 were not touched). Any diff in a Phase 1 page is a bug in this task.

- [ ] **Step 12: Run the gates**

```bash
npm run check:linux
npm run test:graph
npm run build
```

Expected: `check-linux-docs: OK — 47 written page(s), 76 stub(s)`; the graph tests pass; the build is green. **A build failure here is almost always a prerequisite id typo** — the plugin names the offending file and the three closest existing ids. Fix the manifest, re-run `npm run scaffold:linux -- --force` for the affected stub only if the front matter is wrong, and rebuild.

- [ ] **Step 13: Eyeball the sidebar**

Run: `npm run start`, open `http://localhost:3000/knowledge-base/docs/linux/`, and confirm eleven folders appear in position order with the new six after "Kernel Architecture and Idioms", each with its description on its generated index page. Stop the server.

- [ ] **Step 14: Commit**

```bash
git add tools/linux-docs-manifest.json docs/linux docs/computer-science
git commit -m "docs: scaffold linux folders 05-10 and the phase 2 CS backfill stubs"
```

---
## Task 2: CS backfill 3 and 4 — memory ordering, and hardware atomics

**Files:**
- Modify: `docs/computer-science/cpu-architecture/memory-ordering-and-consistency.md` (stub → written)
- Modify: `docs/computer-science/cpu-architecture/atomic-operations-in-hardware.md` (stub → written)

**Interfaces:**
- Consumes: nothing. These are the two load-bearing hardware pages of the phase and are written first for that reason.
- Produces: doc ids `computer-science/cpu-architecture/memory-ordering-and-consistency` and `computer-science/cpu-architecture/atomic-operations-in-hardware`, declared in `related:` by `09/memory-ordering-and-barriers` and `09/atomics-and-refcounts`. **Folder 09 cannot be written until these are solid** — the spec is explicit that backfill 3 gates it.

These are **`computer-science/` pages, not `docs/linux/` pages**: no `prerequisites` key, no `<KernelFacts>`, no `<Lab>`, no `<Src>`, and no kernel API surface. Match the house style of the folder's existing pages (`pipelining.md`, `superscalar-and-out-of-order-execution.md`) — H1, a lead paragraph, `##` sections, tables, Mermaid where structural, and a short closing pointer. Delete the `:::info[Not yet written]` block; keep the front matter.

### `memory-ordering-and-consistency.md` — Memory Ordering and Consistency

- **Opens with:** the uncomfortable fact — the order in which your loads and stores become visible to another core is not the order you wrote them, and nothing is broken. Compilers reorder because nothing in the C abstract machine forbids it, and CPUs reorder because a store buffer is the difference between a fast core and a slow one. A memory model is the contract that says exactly how much reordering you must tolerate.
- **Sections:**
  - `## Sequential consistency, and why nobody ships it` — Lamport's definition: the result is as if all operations executed in some total order consistent with each program's own order. State plainly that it is the model programmers assume, and that implementing it strictly would forfeit the store buffer, speculative loads, and most of the reordering that makes a modern core fast.
  - `## The store buffer, which causes almost everything` — a store retires into a buffer, the core moves on, the line is acquired and the value becomes globally visible later. Work the canonical example: two cores, `x = 1; r1 = y` on one and `y = 1; r2 = x` on the other, both reading zero. Show that this is not a race in the informal sense — every access is a single aligned word — and that it is architecturally permitted on x86-64.
  - `## x86-TSO` — what x86-64 actually guarantees: loads are not reordered with loads, stores are not reordered with stores, stores are not reordered with older loads, and **a load may be reordered with an older store to a different address**. That last one is the only relaxation, and it is exactly the store-buffer case above. Note that this makes x86-64 forgiving enough that incorrect code frequently works.
  - `## Weak models, and arm64` — under a weak model almost any pair may be reordered unless an explicit dependency or barrier says otherwise; arm64 additionally provides load-acquire/store-release as single instructions (`LDAR`/`STLR`) rather than as separate fences. This is the section that explains why code that has worked on x86 for a decade breaks the first time it is run on an ARM server.
  - `## Fences, and the four things they order` — a table with rows for full fence, store-store, load-load, and acquire/release, columns for what it orders, the x86-64 instruction (`MFENCE`, `SFENCE`, `LFENCE`, or nothing because the model already provides it), and the arm64 instruction (`DMB ISH` and variants). Say clearly that on x86-64 most fences compile to nothing, which is precisely why portable code must still write them.
  - `## Acquire and release, which is what you usually want` — the publish/subscribe pattern: a release store makes everything before it visible to anyone who performs an acquire load of that location. This is the ordering discipline nearly all lock-free code is built from, and it is cheaper than a full fence.
  - `## The compiler is the other half` — a barrier that stops the CPU does nothing about the compiler. Hoisting a load out of a loop, merging two stores, or inventing a load are all legal transformations on ordinary variables; that is why every real system has a "this access is genuinely shared" annotation.
  - `## Data races are undefined, and that is a stronger statement than it sounds` — under C11/C++11 a data race is undefined behaviour, not "an unpredictable value". The compiler is entitled to assume it does not happen, which is why the fix is an atomic or an annotation rather than a retry loop.
- **Anchor:** a Mermaid `sequenceDiagram` of the store-buffer litmus test, with participants Core 0, Store buffer 0, Memory, Store buffer 1, Core 1, showing both stores landing in buffers and both loads reading stale memory. Caption: "Both cores read zero, and no rule was broken: each store is still in its own core's store buffer when the other core's load executes."
- **Comparison table:** x86-64 (TSO) versus arm64 (weak) versus sequential consistency, across four rows — load-load, store-store, store-load, load-store — marking each as guaranteed or reorderable.
- **Closing pointer:** to `./atomic-operations-in-hardware.md` for the instructions that make ordering enforceable, `../memory-hierarchy/cache-coherence-and-mesi.md` for the mechanism underneath, and `../../linux/09-concurrency-and-locking/memory-ordering-and-barriers.md` for what Linux builds on it.
- **References:**
  - Sewell et al., *"x86-TSO: A Rigorous and Usable Programmer's Model for x86 Multiprocessors"*, CACM 2010 — `https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf`. The paper that replaced vendor prose with a model you can actually reason with; read it for the litmus tests.
  - Intel SDM Vol. 3A, ch. 9 "Multiple-Processor Management", the memory-ordering section — the vendor's own statement of what x86-64 guarantees, including the examples.
  - Arm Architecture Reference Manual, "The Arm memory model" — the contrasting weak model, and the acquire/release instructions that make it workable.
  - Preshing, *"Memory Barriers Are Like Source Control Operations"* — `https://preshing.com/20120710/memory-barriers-are-like-source-control-operations/`. The clearest intuition pump available for the four barrier types; a blog, and correct.

### `atomic-operations-in-hardware.md` — Atomic Operations in Hardware

- **Opens with:** the problem in one sentence — read-modify-write is three operations, and between any two of them another core can act. An atomic instruction is the hardware's promise that no other core observes the intermediate state, and the whole cost of that promise is in the cache.
- **Sections:**
  - `## What "atomic" actually means here` — indivisible with respect to other observers, not "uninterruptible by an interrupt" and not "ordered". Separate the three properties explicitly, because conflating atomicity with ordering is the single most common misunderstanding on this page.
  - `## Two families: CAS and LL/SC` — x86-64's `LOCK CMPXCHG` compares and swaps in one instruction; arm64 (and RISC-V, and older POWER) instead pairs a load-linked with a store-conditional that fails if the line was touched in between. A table comparing them across four rows: how failure is reported, whether spurious failure is possible, whether a loop is required, and what the ABA problem looks like in each.
  - `## The `LOCK` prefix, and what it costs` — no bus lock in the general case on modern x86-64: the core acquires the cache line exclusively and holds it for the duration. The cost is therefore a coherence transaction, and it scales with how many cores want the same line. Mention split-lock (an atomic straddling two cache lines) as the case that *does* still take a bus lock and costs orders of magnitude more.
  - `## Contention is a cache-line problem, not an instruction problem` — an uncontended atomic on a line already owned is tens of cycles; a contended one across sockets is hundreds. This is the number that decides every locking design in an operating system, so give real orders of magnitude and say they are orders of magnitude, not measurements.
  - `## The instruction family` — a table of what hardware actually offers: exchange, fetch-and-add, compare-and-swap, test-and-set, and the wider forms (double-width CAS). Note which return the old value and which do not, because that distinction reappears in every software API built on top.
  - `## Atomics carry ordering only if you ask` — most architectures offer relaxed, acquire, release, and sequentially-consistent variants of the same operation. x86-64's `LOCK`ed instructions happen to be full barriers, which is why x86-only code gets away with never thinking about it.
  - `## ABA, briefly` — a value can return to its original state while meaning something different; CAS cannot tell. Name the standard mitigations (a tag counter, or deferring reclamation) and hand the second one off to the RCU page in the Linux section.
- **Anchor:** a Mermaid `sequenceDiagram` of a contended `LOCK XADD`: Core 0 requests the line exclusively, Core 1's cache invalidates, Core 0 modifies, then Core 1 requests it back — the ping-pong that makes contention expensive, drawn once. Caption: "One shared counter, two cores: the cost is the cache line changing owner, not the instruction."
- **Closing pointer:** to `../memory-hierarchy/cache-coherence-and-mesi.md` for the protocol that ping-pong runs on, `./memory-ordering-and-consistency.md` for the ordering half, and `../../linux/09-concurrency-and-locking/atomics-and-refcounts.md`.
- **References:**
  - Intel SDM Vol. 3A, ch. 9.1 "Locked Atomic Operations" — the authority on what `LOCK` guarantees and on which instructions are implicitly locked.
  - Arm ARM, "Synchronization and semaphores" — `LDXR`/`STXR` and the exclusive monitor, i.e. what a store-conditional actually checks.
  - Herlihy, *"Wait-Free Synchronization"*, TOPLAS 1991 — why compare-and-swap is universal and test-and-set is not; the theory behind the instruction menu.
  - Paul McKenney, *Is Parallel Programming Hard, And, If So, What Can You Do About It?*, ch. 3 — `https://mirrors.edge.kernel.org/pub/linux/kernel/people/paulmck/perfbook/perfbook.html`. Free, and the best available account of what these operations cost on real hardware.

- [ ] **Step 1: Write `memory-ordering-and-consistency.md`** to the brief above.
- [ ] **Step 2: Write `atomic-operations-in-hardware.md`** to the brief above.
- [ ] **Step 3: Check the claims that are easy to get wrong.** Confirm against the Intel SDM section named above that (a) x86-64 permits exactly one reordering — a later load with an earlier store to a different address — and (b) `LOCK`-prefixed instructions are full barriers. If either is stated differently in the manual, the manual wins and the page changes.
- [ ] **Step 4: Build**

Run: `npm run build`
Expected: green. A broken `../../linux/...` relative link is the likely failure — count the directory levels.

- [ ] **Step 5: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/computer-science/cpu-architecture
git commit -m "docs: write CS backfill pages on memory ordering and hardware atomics"
```

---

## Task 3: CS backfill 6 and 7 — the TLB, and cache coherence

**Files:**
- Modify: `docs/computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md` (stub → written)
- Modify: `docs/computer-science/memory-hierarchy/cache-coherence-and-mesi.md` (stub → written)

**Interfaces:**
- Consumes: `computer-science/memory-hierarchy/virtual-memory-and-paging` and `computer-science/memory-hierarchy/cpu-caches` — both exist and own the paging and cache basics. Link them; do not re-teach either.
- Produces: doc ids `computer-science/memory-hierarchy/tlb-and-address-translation-hardware` and `computer-science/memory-hierarchy/cache-coherence-and-mesi`, declared in `related:` by `08/tlb-and-address-space-switching`, `09/rwlocks-and-rwsems`, `09/per-cpu-data`, and `07/smp-load-balancing`.

Same house-style rules as Task 2. **Licence discipline applies here** — any new image needs a properly-licensed source and a row with a `licence` column in `static/img/cs/SOURCES.md`. Neither page needs a new image: both anchors below are drawn.

### `tlb-and-address-translation-hardware.md` — The TLB and Address-Translation Hardware

- **Opens with:** the arithmetic that forces the design — a four-level page table means four memory accesses to resolve one address, so every load would cost five. Translation is therefore cached, and the cache is small, physically indexed by virtual page number, and completely invisible to software except when it is wrong.
- **Sections:**
  - `## What a TLB entry holds` — virtual page number, physical frame number, permission bits, and (on modern parts) an address-space tag. Note that it caches the *result* of a walk, not the page table itself.
  - `## Structure: levels, and separate I and D` — L1 iTLB and dTLB with tens of entries, a shared L2 TLB with a thousand or two, per-page-size sets. Give the shape and say plainly that exact counts are per-microarchitecture and should be read from the vendor's optimisation manual rather than memorised.
  - `## Page-walk caches` — the second, less-known cache: intermediate page-table entries are themselves cached, so a TLB miss usually costs one memory access, not four. This is why TLB misses are survivable at all.
  - `## Reach, and why huge pages exist` — reach = entries × page size. Compute it: a 1536-entry L2 TLB at 4 KiB covers ~6 MiB; the same TLB at 2 MiB pages covers 3 GiB. State that this single number, not "fewer page-table levels", is the real argument for huge pages.
  - `## Address-space tags: ASID and PCID` — without a tag, every address-space switch invalidates the whole TLB; with one, entries from several address spaces coexist. x86-64 calls it PCID, arm64 calls it ASID, and the tag is narrow (12 bits on x86-64), so the OS must recycle them.
  - `## Invalidation, and why it is expensive` — `INVLPG` and its arm64 counterpart invalidate locally; **there is no hardware broadcast on x86-64**, so invalidating other cores' TLBs is a software protocol: interrupt every core that might have the mapping and wait for it to acknowledge. Name this as the TLB shootdown and give the cost shape (an IPI round trip, times the number of cores). Note arm64's `TLBI` broadcasts within the inner-shareable domain, which is a genuine architectural difference rather than a detail.
  - `## What software must do, in one paragraph` — the OS must invalidate after any change that makes a cached translation wrong: unmapping, permission reduction, and moving a page. Widening permissions usually needs nothing, because a stale entry that is *more* restrictive only costs a spurious fault.
- **Anchor:** a Mermaid `flowchart TB` of one memory access — virtual address → TLB lookup → hit path straight to the cache, miss path into the page-walk caches, then the full walk, then TLB fill and retry. Caption: "Where a memory access goes when translation hits, and the two fallbacks when it does not."
- **Table:** TLB hit, TLB miss with a page-walk-cache hit, and a full walk, with approximate cost in cycles as an order of magnitude, and what software can do about each.
- **Closing pointer:** to `./virtual-memory-and-paging.md` for the table format being cached, and `../../linux/08-memory-management/tlb-and-address-space-switching.md` for Linux's shootdown implementation and its PCID use.
- **References:**
  - Intel SDM Vol. 3A, ch. 4.10 "Caching Translation Information" — the authority on what may be cached, when it must be invalidated, and how PCIDs behave.
  - Arm ARM, "TLB maintenance" — the broadcast `TLBI` instructions and the shareability domains, i.e. the reason arm64 does not need a shootdown IPI.
  - Intel 64 and IA-32 Architectures Optimization Reference Manual — where actual per-microarchitecture TLB sizes live, so nobody memorises a number from a blog.
  - Villavieja et al., *"DiDi: Mitigating the Performance Impact of TLB Shootdowns"*, PACT 2011 — measurements of what shootdowns cost on real machines, which is the part vendor documentation never states.

### `cache-coherence-and-mesi.md` — Cache Coherence and MESI

- **Opens with:** the problem created by success — private per-core caches are what make multicore fast, and the moment two cores cache the same line, they can disagree. Coherence is the hardware protocol that makes the disagreement impossible to observe, and it is the reason a shared variable costs what it costs.
- **Sections:**
  - `## The invariant` — at most one writer, or any number of readers, per line at a time. Every protocol on this page is an implementation of that single sentence.
  - `## MESI, state by state` — Modified, Exclusive, Shared, Invalid: what each means, what the core may do without talking to anyone, and what forces a transition. Emphasise that Exclusive is the interesting one — it lets a core write without any bus traffic, which is why private data is fast.
  - `## MOESI and MESIF, in one paragraph each` — Owned (AMD) lets a dirty line be shared without writing back; Forward (Intel) nominates one sharer to answer requests. Both are optimisations of the same invariant, and neither changes how software should be written.
  - `## Snooping versus directories` — broadcast works to a handful of cores and stops scaling; large systems keep a directory of who holds what. Say what this changes for the programmer: nothing about correctness, everything about how the cost grows with core count.
  - `## The unit is the line, not the variable` — 64 bytes on every current x86-64 and arm64 part. Everything on the rest of this page follows from this one fact.
  - `## False sharing` — two cores, two unrelated variables, one line: the line ping-pongs and both cores stall, with no shared data and no bug visible in the source. Give the canonical fix (pad to a line, or make the data per-core) and say that per-core data eliminates the problem rather than mitigating it.
  - `## What it costs` — a table of approximate access costs in cycles as orders of magnitude: L1 hit, L2 hit, LLC hit, a line held Modified by another core on the same socket, and the same across sockets. State clearly that these are shapes, not measurements, and name `perf c2c` as the tool that finds real ones.
  - `## Coherence is not consistency` — the closing distinction, and the reason this page and the memory-ordering page are separate. Coherence orders accesses to *one* location; it says nothing about the order of accesses to two different locations. That second question is the memory model.
- **Anchor:** a Mermaid `stateDiagram-v2` of MESI for one line in one cache — transitions labelled with the local action (read, write, evict) and the remote one (a snooped read or read-for-ownership). Caption: "One cache line, one core's view: what moves it between Modified, Exclusive, Shared, and Invalid."
- **Closing pointer:** to `./cpu-caches.md` for cache organisation itself, `../cpu-architecture/atomic-operations-in-hardware.md` for what an atomic does to these states, and `../../linux/09-concurrency-and-locking/per-cpu-data.md` for the kernel's structural answer to false sharing.
- **References:**
  - Sorin, Hill & Wood, *A Primer on Memory Consistency and Cache Coherence*, 2nd ed. — the standard treatment; the coherence chapters are the clearest published statement of the invariant. Available free through many institutions; otherwise a purchase.
  - Ulrich Drepper, *"What Every Programmer Should Know About Memory"* — `https://people.freebsd.org/~lstewart/articles/cpumemory.pdf`. Dated in its hardware specifics (2007) and still the best long-form explanation of why cache behaviour dominates; say so in the annotation.
  - Intel SDM Vol. 3A, ch. 9.4 "Memory Ordering" and the MESI description in ch. 12 — the vendor statement of protocol behaviour.
  - `perf c2c` documentation at `https://man7.org/linux/man-pages/man1/perf-c2c.1.html` — the tool that turns "this is slow" into a specific cache line and a specific pair of threads.

- [ ] **Step 1: Write `tlb-and-address-translation-hardware.md`** to the brief above.
- [ ] **Step 2: Write `cache-coherence-and-mesi.md`** to the brief above.
- [ ] **Step 3: Sanity-check the two numeric claims** — the TLB-reach arithmetic (entries × page size) and the 64-byte line size — and state page-size and entry-count assumptions inline rather than leaving them implicit.
- [ ] **Step 4: Build, lint, commit**

```bash
npm run build && rtk run 'npm run lint'
git add docs/computer-science/memory-hierarchy
git commit -m "docs: write CS backfill pages on the TLB and cache coherence"
```

---

## Task 4: CS backfill 8 and 10, and every backlink

**Files:**
- Modify: `docs/computer-science/memory-hierarchy/numa-and-memory-topology.md` (stub → written)
- Modify: `docs/computer-science/buses-and-io/interrupt-controllers.md` (stub → written)
- Modify: `docs/computer-science/operating-systems/concurrency-and-synchronization.md`
- Modify: `docs/computer-science/operating-systems/scheduling.md`
- Modify: `docs/computer-science/operating-systems/processes-and-threads.md`
- Modify: `docs/computer-science/operating-systems/memory-management.md`
- Modify: `docs/computer-science/operating-systems/interprocess-communication.md`
- Modify: `docs/computer-science/memory-hierarchy/virtual-memory-and-paging.md`
- Modify: `docs/computer-science/memory-hierarchy/cpu-caches.md`
- Modify: `docs/computer-science/cpu-architecture/multicore-and-parallelism.md`
- Modify: `docs/computer-science/buses-and-io/io-and-interrupts.md`
- Modify: `docs/computer-science/assembly/calling-conventions-and-the-stack.md`

**Interfaces:**
- Consumes: Tasks 2 and 3's pages, which the backlinks point at.
- Produces: doc ids `computer-science/memory-hierarchy/numa-and-memory-topology` and `computer-science/buses-and-io/interrupt-controllers`, plus the reverse edges the spec requires. **The spec makes backlinks mandatory for this section** — a generated dependency graph with one-way edges is half a graph, and the backfill pages exist precisely to be depended on.

### `numa-and-memory-topology.md` — NUMA and Memory Topology

- **Opens with:** the moment "main memory" stops being one thing. Past a certain core count, a single memory controller is the bottleneck, so each socket gets its own controller and its own attached DRAM; memory is still globally addressable, but the address determines whether the access is local or crosses an interconnect. Every NUMA effect follows from that one asymmetry.
- **Sections:**
  - `## Why it exists` — a straight scaling argument: bandwidth per socket, pin count, and the physical distance a signal travels. NUMA is not a design mistake to be worked around, it is what buying more sockets actually gets you.
  - `## Nodes, distance, and the interconnect` — a node as a set of CPUs plus the memory local to them; the distance matrix as the machine's own statement of relative cost; UPI/Infinity Fabric as the link that carries remote traffic *and* coherence traffic. Note that sub-NUMA clustering means one socket can present as several nodes.
  - `## What remote actually costs` — a table with local latency, remote one-hop latency, and bandwidth in each direction, as ratios rather than absolute numbers (roughly 1.5–2× latency and materially lower bandwidth), and the instruction to measure rather than assume. Name `lstopo`, `numactl --hardware`, and the ACPI SLIT/SRAT tables as where the machine tells you its own topology.
  - `## First-touch, and the allocation policy question` — memory is bound to a node when it is first *touched*, not when it is allocated. Explain why this makes the thread that initialises an array the one that decides where it lives, and why parallel initialisation is a real technique rather than a micro-optimisation.
  - `## Interleaving, and what it trades` — spreading pages round-robin across nodes converts a bimodal latency distribution into a uniform mediocre one. Correct for a large shared structure accessed from everywhere; wrong for per-thread working sets.
  - `## I/O has a topology too` — a PCIe device hangs off one socket's root complex, so a NIC or NVMe drive is local to some cores and remote to others. This is why interrupt affinity and NUMA placement are the same conversation.
  - `## When NUMA is a red herring` — say plainly that most performance problems on a two-socket machine are not NUMA problems, and give the check that distinguishes them (per-node hit rates, or simply pinning to one node and re-measuring).
- **Anchor:** reuse the existing `<Figure src="/img/cs/cpu-architecture/topology-hwloc.png" …>` — it is an `lstopo` rendering of a real two-socket machine, which is exactly what this page is about, and its row is already in `static/img/cs/SOURCES.md` (`https://commons.wikimedia.org/wiki/File:Hwloc.png`, BSD). Caption it for *this* page's purpose: "One machine, two nodes: every core, cache, and memory bank, with the nodes the operating system will allocate from." Add a Mermaid `flowchart LR` beside it showing two nodes, their local DRAM, and the interconnect, with a local and a remote access drawn as two different paths.
- **Closing pointer:** to `./cache-coherence-and-mesi.md` (coherence traffic crosses the same interconnect), `../cpu-architecture/multicore-and-parallelism.md`, and `../../linux/08-memory-management/numa-and-memory-policy.md`.
- **References:**
  - `https://www.open-mpi.org/projects/hwloc/` — hwloc and `lstopo`, the portable way to ask a machine what shape it is.
  - ACPI Specification, the SRAT and SLIT table definitions — where the firmware states the topology and the distance matrix the OS then believes.
  - `https://man7.org/linux/man-pages/man8/numactl.8.html` — the practical interface for inspecting and binding, and the source of the numbers in the cost table.
  - Lameter, *"NUMA (Non-Uniform Memory Access): An Overview"*, ACM Queue 2013 — `https://queue.acm.org/detail.cfm?id=2513149`. Written by the kernel's NUMA maintainer; the clearest short treatment of policy trade-offs.

### `interrupt-controllers.md` — Interrupt Controllers

- **Opens with:** the gap this hardware fills — a CPU core has one or two interrupt input pins and a machine has hundreds of devices, so something must multiplex, prioritise, mask, and route. The interrupt controller is that something, and its evolution is a direct record of machines getting more cores.
- **Sections:**
  - `## What a controller must provide` — the four jobs: aggregate many sources onto few CPU inputs, tell the CPU *which* source fired, mask and prioritise, and decide which CPU takes it. Every controller on the page is a different answer to those four.
  - `## The 8259 PIC, and why it is history` — two cascaded chips, fifteen usable lines, edge-triggered, one CPU. Kept in the page because the vocabulary (IRQ 0 for the timer, IRQ 1 for the keyboard) still leaks into modern documentation and because legacy mode still exists at boot.
  - `## APIC: local and I/O` — the split that matters. A local APIC per core handles the timer, IPIs, and delivery to that core; the I/O APIC sits on the board and routes device lines to local APICs via a redirection table. This split is why a modern machine can steer an interrupt to a chosen core at all.
  - `## Inter-processor interrupts` — one core interrupting another, which is not a device mechanism but the foundation of TLB shootdown, rescheduling another CPU, and stopping the machine on panic. Name it here so the Linux pages can use the term.
  - `## MSI and MSI-X` — the change of model: instead of asserting a line, the device performs a *memory write* to a magic address, which the interrupt controller turns into an interrupt. Consequences worth stating: no sharing, no line-count limit, ordering with respect to the device's DMA writes, and thousands of vectors — which is what makes one interrupt per NIC queue possible.
  - `## x2APIC, briefly` — MSR-based access and a wider APIC ID space, needed once machines exceeded 255 logical CPUs.
  - `## Arm's GIC` — distributor, redistributor, and CPU interface; SPIs, PPIs, and SGIs as the three kinds of source. Contrast honestly: the GIC is a single architected controller with a specification, where x86-64 accumulated PIC, APIC, and MSI in layers. This is the arm64 contrast folder 10 links to.
  - `## Level versus edge, and why it matters` — a level-triggered line stays asserted until the device is told to stop, so a handler that forgets to acknowledge produces an interrupt storm; an edge-triggered one can be missed if it fires while masked. One paragraph, because both failure modes appear in real driver bugs.
- **Anchor:** a Mermaid `flowchart LR` from three device sources — a legacy line into the I/O APIC, an MSI-X write from a PCIe device, and a local APIC timer — converging on two cores' local APICs, with the vector number labelled on each edge. Caption: "Three ways an interrupt reaches a core, and the only thing the core actually sees: a vector number."
- **Table:** PIC, I/O APIC, MSI/MSI-X, and GIC across four columns — how a source is identified, how many sources, how a target CPU is chosen, and whether sharing is possible.
- **Closing pointer:** to `./io-and-interrupts.md` for the polling/IRQ/DMA framing, `../cpu-architecture/exceptions-traps-and-interrupts.md` for what the CPU does once a vector arrives, and `../../linux/10-interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel.md`.
- **References:**
  - Intel SDM Vol. 3A, ch. 12 "Advanced Programmable Interrupt Controller" — the authority on local APIC, I/O APIC redirection entries, and IPI delivery modes.
  - Intel 82093AA I/O APIC datasheet — short, concrete, and the clearest statement of what a redirection table entry contains.
  - PCI Express Base Specification, the MSI/MSI-X capability chapters — the definitive account of interrupt-as-a-memory-write, including the ordering rules relative to DMA.
  - Arm Generic Interrupt Controller Architecture Specification (GICv3/v4) — `https://developer.arm.com/documentation/ihi0069/latest/`. The arm64 side, and the reason arm64 documentation uses SPI/PPI/SGI vocabulary.

- [ ] **Step 1: Write `numa-and-memory-topology.md`** to the brief above.
- [ ] **Step 2: Write `interrupt-controllers.md`** to the brief above.
- [ ] **Step 3: Add the backlinks.** Each is one or two sentences appended to the relevant existing page — in its closing pointer paragraph if it has one, otherwise as a short `## Where this goes next` at the end. Match each page's existing voice; do not restructure anything.

| Page | Sentence to add |
|---|---|
| `operating-systems/concurrency-and-synchronization.md` | Points to `../cpu-architecture/memory-ordering-and-consistency.md`, `../cpu-architecture/atomic-operations-in-hardware.md`, `../memory-hierarchy/cache-coherence-and-mesi.md` for the hardware these primitives rest on, and `../../linux/09-concurrency-and-locking/why-kernel-concurrency-is-different.md` for how a kernel uses them. |
| `operating-systems/scheduling.md` | Points to `../../linux/07-scheduling/what-the-scheduler-must-decide.md` for a real implementation. **Add no EEVDF detail** — that page owns it. |
| `operating-systems/processes-and-threads.md` | Points to `../../linux/06-processes-and-threads/threads-are-tasks.md` for the Linux answer, where the process/thread distinction largely dissolves. |
| `operating-systems/memory-management.md` | Points to `../../linux/08-memory-management/the-page-fault-handler.md` and `../../linux/08-memory-management/the-page-allocator.md`. |
| `operating-systems/interprocess-communication.md` | Points to `../../linux/06-processes-and-threads/pipes-fifos-and-unix-sockets.md` for the kernel-side implementation. |
| `memory-hierarchy/virtual-memory-and-paging.md` | Points to `./tlb-and-address-translation-hardware.md` and `../../linux/08-memory-management/page-tables-and-the-walk.md`. **Also verify** its multi-level walk description matches what folder 08 will build on; if it disagrees, fix the disagreement here and note it in the commit message. |
| `memory-hierarchy/cpu-caches.md` | Points to `./cache-coherence-and-mesi.md` for what happens when several caches hold one line, and `./tlb-and-address-translation-hardware.md` for the translation cache. |
| `cpu-architecture/multicore-and-parallelism.md` | Points to `./memory-ordering-and-consistency.md`, `./atomic-operations-in-hardware.md`, `../memory-hierarchy/cache-coherence-and-mesi.md`, `../memory-hierarchy/numa-and-memory-topology.md`. |
| `buses-and-io/io-and-interrupts.md` | Points to `./interrupt-controllers.md` for the routing hardware and `../../linux/10-interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel.md` for the software path. |
| `assembly/calling-conventions-and-the-stack.md` | Confirm the ABI covered is x86-64 System V and say so explicitly if it is currently implicit. Add a short subsection giving the **syscall** convention — number in `rax`, arguments in `rdi`, `rsi`, `rdx`, `r10`, `r8`, `r9` (note `r10` in place of `rcx`), return in `rax`, and `SYSCALL` clobbering `rcx` and `r11` — plus a pointer to `../../linux/05-syscalls-and-the-boundary/arguments-return-values-and-errno.md`. |

- [ ] **Step 4: Verify every backlink resolves**

Run: `npm run build`
Expected: green. Twelve files changed and eleven of the changes are links, so a broken relative path is the expected failure mode; the build names the file and the target.

- [ ] **Step 5: Confirm no CS page acquired Linux-section furniture**

Run: `rtk run "grep -rln 'KernelFacts\|<Src \|<Lab ' docs/computer-science"`
Expected: no output. Those components belong to `docs/linux/` pages only.

- [ ] **Step 6: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/computer-science
git commit -m "docs: write CS backfill pages on NUMA and interrupt controllers, add backlinks"
```

---
## Task 5: Folder 05 — what a syscall is, the entry path, the dispatch

**Files:**
- Modify: `docs/linux/05-syscalls-and-the-boundary/what-a-system-call-actually-is.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/the-entry-path.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/the-syscall-table-and-dispatch.md`

**Interfaces:**
- Consumes: `00/the-kernel-userspace-boundary` (the shape of the boundary), and the two CS pages on privilege levels and on exceptions/traps — linked, never re-taught.
- Produces: `05/the-entry-path`, which folder 10's `how-an-interrupt-reaches-the-kernel` declares as a prerequisite, and `05/the-syscall-table-and-dispatch`, which four later pages in this folder build on.

### `what-a-system-call-actually-is.md` — What a System Call Actually Is **[WAH]** **[Misc]**

- **Opens with:** the correction that carries the whole folder — a system call is not a function call into the kernel. It is a deliberate, hardware-mediated privilege transition into code you do not control, entered at an address you cannot choose, running on a stack you did not allocate. Everything expensive about it follows from that, and so does everything safe about it.
- **Sections:**
  - `## Three things a call cannot do that a syscall must` — change privilege level, switch to a trusted stack, and land somewhere the caller cannot pick. Each in a sentence, each pointing at why an ordinary `call` instruction is structurally incapable of it.
  - `## What it costs, and where the cost is` — break the cost down honestly: the privilege transition itself (now on the order of a hundred cycles, not thousands), plus the register save and restore, plus the indirect effects that dominate in practice — a cold I-cache in the kernel, a polluted branch predictor, and since Meltdown, a page-table switch under KPTI. Say that the mitigation-era cost is the reason so much of modern kernel interface design is about *not* making the call.
  - `## What actually happens` **[WAH]** — take `getpid()`. In C it looks like a function call; the reader follows it through libc's wrapper, the `SYSCALL` instruction, the entry stub, `sys_getpid`, and back, and the punchline is that the cheapest possible syscall still does all of that — which is exactly why `getpid` is cached by some libcs and why `gettimeofday` was moved into the vDSO entirely.
  - `## The design consequences` — a table of interfaces that exist because the boundary is expensive: the vDSO (avoid the crossing), `io_uring` (batch it), `mmap` (do it once and then not at all), `readv`/`writev` (one crossing, many buffers), `epoll` (one crossing, many readiness answers). Each row names the mechanism and the crossing it removes; only the vDSO gets a link, because the others live in unwritten folders.
  - `## Not every trap is a syscall` — page faults and device interrupts also cross the boundary and are not syscalls. This distinction is the one folder 10 depends on.
  - `## Misconceptions` **[Misc]** — (1) "a syscall is slow because the kernel is slow" — most of the cost is the transition and its cache effects, not the work; (2) "syscalls are how programs talk to the kernel" — some of the most frequent kernel interactions are faults and vDSO reads that involve no syscall at all; (3) "the kernel runs on my behalf in a separate thread" — it runs in your task's context, on your task's kernel stack, charged to your task's `sys` time.
- **Anchor:** a Mermaid `sequenceDiagram` — User code, CPU, Kernel entry, Handler — showing the instruction, the privilege transition, the stack switch, the handler, and the return, with the ring/privilege level annotated on each participant's activation. Caption: "One `getpid()`, from the instruction that traps to the instruction after it, with the privilege level at each step."
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"]]`; `path` — `"user SYSCALL → entry_SYSCALL_64() → do_syscall_64() → sys_getpid() → return to user"`; `observe` — `perf stat -e raw_syscalls:sys_enter -- ls` (verify the tracepoint against `perf list` first); `trap` — "The syscall boundary is fast on modern hardware; what is slow is everything the crossing does to your caches and branch predictors. Measuring one syscall in a tight loop tells you almost nothing about its cost in a real program."
- **References:**
  - `man 2 syscall` — the per-architecture register table, and the honest statement that libc wrappers are not the interface.
  - `https://docs.kernel.org/admin-guide/index.html` — the kernel's own account of what it exposes across the boundary.
  - Kerrisk, *The Linux Programming Interface*, ch. 3 — the definitive treatment from the caller's side; a purchase.
  - LWN, *"KPTI: the kernel page-table isolation"* coverage (`https://lwn.net/Articles/741878/`) — why the transition got more expensive in 2018, which is the context for every syscall-avoidance interface since; predates v6.18 and describes the mechanism, not current defaults.

### `the-entry-path.md` — The Entry Path

- **Opens with:** the split that organises the page — some of what happens between `SYSCALL` and `do_syscall_64` is done by the CPU because software cannot be trusted to do it, and the rest is done by software because the CPU does surprisingly little. Knowing which is which is the difference between reading `entry_64.S` and guessing at it.
- **Sections:**
  - `## What the CPU does, exactly` — on x86-64, `SYSCALL` loads `RIP` from `MSR_LSTAR`, saves the old `RIP` in `rcx` and `RFLAGS` in `r11`, masks flags per `MSR_SYSCALL_MASK`, and loads `CS`/`SS` from `MSR_STAR`. State the two things it conspicuously does **not** do: switch stacks, and save any other register. Everything else is software's problem.
  - `## `swapgs` and finding the kernel's own state` — the kernel needs a pointer to per-CPU data before it can do anything, and the only register it can trust is `GS` after `swapgs`. Explain the exchange, and why an interrupt arriving in the middle of entry is a genuine hazard the entry code handles explicitly.
  - `## The stack switch` — from the user stack to this task's kernel stack (`cpu_current_top_of_stack` / the task's `thread_info` area — verify the v6.18 names), and why running kernel code on a user-controlled stack pointer would be an immediate privilege escalation.
  - `## Building `pt_regs`` — the entry stub pushes the register set into a `struct pt_regs` at a known offset from the stack top. This is why every syscall handler, every tracer, and every oops dump can find the caller's registers by shape rather than by convention.
  - `## Then C takes over` — `do_syscall_64` and the entry/exit work around it: `syscall_enter_from_user_mode` and `syscall_exit_to_user_mode` handle tracing, seccomp, signals, and rescheduling on the way out. Say that the exit path is where a pending signal or a `need_resched` is actually acted on, which is the fact folder 06's signals page and folder 07's preemption page both need.
  - `## KPTI, in one paragraph` — with page-table isolation the entry path also switches `CR3`, and the trampoline stack exists for that reason. Version-scoped `:::note`: mitigation status depends on the CPU and on boot parameters, and `/sys/devices/system/cpu/vulnerabilities/` is the authoritative answer on any given machine.
  - `## This path is simplified` — state it explicitly, per the spec's accuracy guardrail: error paths, `CONFIG_*` variants, IST stacks, and the 32-bit compat entries are elided. `<Src file="arch/x86/entry/entry_64.S" symbol="entry_SYSCALL_64" />` is the real thing.
  - `## arm64 does this differently` — `:::note`: `SVC` traps to a vector table entry chosen by exception *category* rather than a vector number, `ELR_EL1` and `SPSR_EL1` hold the return state instead of `rcx`/`r11`, and the kernel stack pointer comes from `SP_EL1` rather than a software swap. The syscall number is in `x8`.
- **Anchor:** a Mermaid `flowchart TB` split into two labelled lanes, "CPU does" and "Kernel does", with the steps in order down the page and the lane boundary crossed exactly twice. Caption: "The division of labour on syscall entry: five things the hardware does, everything else in `entry_64.S`."
- **Second visual:** a WaveDrom `reg` strip of the `RFLAGS` bits the entry path cares about — `CF`(0), `PF`(2), `AF`(4), `ZF`(6), `SF`(7), `TF`(8), `IF`(9), `DF`(10), `OF`(11), `IOPL`(12–13), `NT`(14), `AC`(18) — captioned with which of them `MSR_SYSCALL_MASK` clears on entry and why `IF` and `DF` are the two that matter. Verify the mask's value against `syscall_init` in `arch/x86/kernel/cpu/common.c`.
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"], ["MSR_LSTAR", "arch/x86/include/asm/msr-index.h"]]`; `path` — `"SYSCALL → entry_SYSCALL_64() → swapgs → stack switch → pt_regs → do_syscall_64()"`; `observe` — `sudo rdmsr 0xc0000082 && sudo grep entry_SYSCALL_64 /proc/kallsyms` (the LSTAR value and the symbol it points at should agree); `trap` — "`SYSCALL` does not switch stacks. Between the instruction and the stack switch a few instructions later, the kernel is running on a stack the user chose — which is why that window is written in assembly and audited carefully."
- **References:**
  - `<Src file="arch/x86/entry/entry_64.S" symbol="entry_SYSCALL_64" />` — the path itself, and the comments in it are documentation.
  - Intel SDM Vol. 2B, the `SYSCALL`/`SYSRET` instruction reference — the exact list of what the hardware saves, loads, and masks.
  - `https://docs.kernel.org/arch/x86/entry_64.html` if present at v6.18, otherwise the in-tree `Documentation/arch/x86/` index — check which exists before citing.
  - LWN, *"Meltdown and Spectre: kernel page-table isolation"* — why `CR3` moves on entry and what the trampoline stack is for.

### `the-syscall-table-and-dispatch.md` — The Table and the Dispatch **[Lab host=any-linux]**

- **Opens with:** the mundane mechanism behind a grand-sounding interface — the kernel holds an array of function pointers, the syscall number is an index into it, and the bounds check on that index is one of the most security-critical two lines in the tree.
- **Sections:**
  - `## The table` — `sys_call_table` as a static array generated at build time from `arch/x86/entry/syscalls/syscall_64.tbl`, one line per syscall: number, ABI, name, entry point. Show five real lines from the `.tbl` file in a ` ```text ` block.
  - `## Numbers are frozen forever` — a number, once shipped, means that syscall on that architecture until the end of time. Removed syscalls leave holes; new ones append. Note that numbers differ per architecture, which is why `strace` needs to know the ABI and why seccomp filters must check the architecture before the number.
  - `## `SYSCALL_DEFINEn`, expanded` — take one real three-argument syscall and expand the macro in three steps in ` ```c ` blocks: the declaration, the `__do_sys_*` inner function with real types, and the `__x64_sys_*` wrapper that unpacks `pt_regs`. Explain each thing the macro buys — the `pt_regs`-based calling convention (a Spectre-era change), the sign-extension and type-checking wrappers, and the tracepoint hookup.
  - `## Dispatch, in six lines` — the bounds check, the array read, the indirect call, and the return value written back into `pt_regs->ax`. Note the speculation hardening around the array index, and why an unchecked index here would be arbitrary kernel code execution.
  - `## Where the per-architecture tables live` — a small table: x86-64, x86-32/compat, arm64, and the generic `include/uapi/asm-generic/unistd.h` that newer architectures use instead of their own list.
  - `<Lab host="any-linux" title="Find a syscall's number three ways" time="10 min">` — (1) `grep` the number out of `/usr/include/asm/unistd_64.h`; (2) read it from the running kernel with `ausyscall --dump | head` if `auditd` tooling is present, otherwise `perf list 'syscalls:sys_enter_*' | head`; (3) see it in flight with `strace -e trace=openat ls` and match the name. Show expected output for each. "If it fails": the header may live under a different multiarch path (`/usr/include/x86_64-linux-gnu/asm/unistd_64.h`), and `perf list` needs `tracefs` mounted and readable.
- **Anchor:** a Mermaid `flowchart LR` from `pt_regs->orig_ax` through the bounds check to the table read, the indirect call, and the write-back to `pt_regs->ax`, with the failure edge for an out-of-range number going to `-ENOSYS`. Caption: "A syscall number becoming a function pointer, and the bounds check that stands between the two."
- **KernelFacts:** `structure` — `[["sys_call_table", "arch/x86/entry/syscall_64.c"], ["SYSCALL_DEFINE3", "include/linux/syscalls.h"]]` (verify the file that defines the table at v6.18 — it has moved between `syscall_64.c` and generated headers); `path` — `"do_syscall_64() → bounds check on nr → sys_call_table[nr] → __x64_sys_foo() → __do_sys_foo()"`; `observe` — `grep -E '^(0|1|2|60|257) ' arch/x86/entry/syscalls/syscall_64.tbl`; `trap` — "A syscall number is not portable and not stable across architectures. `openat` is 257 on x86-64 and a different number on arm64, which is why a seccomp filter that checks the number without first checking the architecture is a security bug, not a portability bug."
- **References:**
  - `<Src file="arch/x86/entry/syscalls/syscall_64.tbl" />` — the table's source of truth, readable as a plain file.
  - `<Src file="include/linux/syscalls.h" symbol="SYSCALL_DEFINE3" />` — the macro, with the comments explaining the `pt_regs` wrapper.
  - LWN, *"System calls and the pt_regs-based calling convention"* (`https://lwn.net/Articles/766109/`) — why the wrapper shape changed in 2018, which explains the double-underscore functions readers will otherwise find baffling.
  - `https://man7.org/linux/man-pages/man2/syscalls.2.html` — the catalogue of what exists, with the kernel version each was added in.

- [ ] **Step 1: Write `what-a-system-call-actually-is.md`** to the brief above, deleting the `:::info[Not yet written]` block.
- [ ] **Step 2: Write `the-entry-path.md`** to the brief above.
- [ ] **Step 3: Write `the-syscall-table-and-dispatch.md`** to the brief above.
- [ ] **Step 4: Verify every symbol** — `entry_SYSCALL_64`, `do_syscall_64`, `sys_call_table`, `SYSCALL_DEFINE3`, `pt_regs`, `MSR_LSTAR`, `syscall_init`, `syscall_enter_from_user_mode`, `syscall_exit_to_user_mode` — at `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>`, and every file path at `/source/<path>`. Correct the page to whatever v6.18 actually has.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`
Expected: zero findings and a green build. `check:linux` will report a growing written count and a shrinking stub count.

- [ ] **Step 6: Commit**

```bash
git add docs/linux/05-syscalls-and-the-boundary
git commit -m "docs: write the syscall entry path and dispatch"
```

---

## Task 6: Folder 05 — the ABI, copying, and the vDSO

**Files:**
- Modify: `docs/linux/05-syscalls-and-the-boundary/arguments-return-values-and-errno.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/copying-data-across-the-boundary.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/the-vdso.md`

**Interfaces:**
- Consumes: `05/the-entry-path` and `05/the-syscall-table-and-dispatch` (Task 5).
- Produces: `05/arguments-return-values-and-errno`, the prerequisite of `05/libc-is-not-the-kernel`. The `-EFAULT` mechanism established here is assumed by every driver and filesystem page in later phases.

### `arguments-return-values-and-errno.md` — Arguments, Returns, and errno **[WAH]** **[Misc]**

- **Opens with:** the fact that a syscall has no calling convention of its own — it borrows one, and the borrowing is imperfect. On x86-64 the syscall ABI deliberately differs from the C ABI in one register, and that single difference explains a great deal of confusing assembly.
- **Sections:**
  - `## The register ABI` — a table: `rax` for the number, then `rdi`, `rsi`, `rdx`, `r10`, `r8`, `r9` for arguments, `rax` for the return. State explicitly that this is **x86-64**, that the C ABI uses `rcx` where the syscall ABI uses `r10`, and that the reason is that `SYSCALL` itself clobbers `rcx`. Link to `computer-science/assembly/calling-conventions-and-the-stack.md`.
  - `## Six arguments, and what happens beyond` — the limit is the register set. Interfaces that need more take a pointer to a struct (`mmap` on 32-bit, `clone3`, `openat2`), and modern practice is a struct plus an explicit size argument, which is how the interface stays extensible without a new syscall number.
  - `## Negative errno, and the sign trick` — the kernel returns `-EFAULT`, not `-1`; there is no `errno` in the kernel. The valid-return range and the error range are separated by `MAX_ERRNO` (4095), which is exactly the trick `ERR_PTR` uses on kernel pointers — link back to `../04-kernel-architecture-and-idioms/error-handling-idioms.md`, do not re-derive it.
  - `## What actually happens` **[WAH]** — where user-space `errno` comes from. Walk `open("/nonexistent", O_RDONLY)`: the kernel returns `-2`; libc's wrapper tests the return, negates it into the thread-local `errno`, and returns `-1`. Show a `strace` line next to the C source and point out that the `-1` never existed on the kernel side. Then note the consequence: raw `syscall(2)` callers must do that conversion themselves, and code that checks `errno` without checking the return value is reading a stale value.
  - `## Restartable syscalls` — `ERESTARTSYS` and friends are never seen by user space. When a signal interrupts a blocking call, the kernel either rewinds `RIP` to re-execute the `SYSCALL` instruction or converts the value to `-EINTR`, depending on the handler's `SA_RESTART` flag. State plainly that this is why some blocking calls appear to survive a signal and others return `-EINTR`, and that the difference is a property of the *handler*, not the call.
  - `## The exit path is where this is decided` — the conversion, the restart, and pending-signal delivery all happen in the syscall exit work; link back to `./the-entry-path.md`.
  - `## Misconceptions` **[Misc]** — (1) "syscalls return -1 and set errno" — libc does that, the kernel returns a negative errno; (2) "`EINTR` means the call failed" — it means it was interrupted, and often the correct response is to call it again; (3) "you can pass as many arguments as you like via the stack" — the syscall ABI has no stack arguments at all.
- **Anchor:** a table of the six argument registers with the C ABI's register beside each, highlighting the `rcx`/`r10` divergence, plus the return-value register and the clobber list.
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"], ["MAX_ERRNO", "include/linux/err.h"]]`; `path` — `"handler returns -EFAULT → pt_regs->ax → SYSRET → libc wrapper negates into errno → -1 to the caller"`; `observe` — `strace -e trace=openat cat /nonexistent` (the `-1 ENOENT` in the trace is libc's rendering of the kernel's `-2`); `trap` — "`errno` is a libc variable in thread-local storage. The kernel has never heard of it, and nothing sets it unless a wrapper does."
- **References:**
  - `man 2 syscall` — the per-architecture argument-register table, including the `r10` note.
  - `man 7 signal`, the "Interruption of system calls" section — the definitive list of which calls restart and which return `-EINTR`, and how `SA_RESTART` changes it.
  - `<Src file="include/linux/err.h" symbol="MAX_ERRNO" />` — the boundary between a valid return and an error, in the source.
  - System V AMD64 ABI specification (`https://gitlab.com/x86-psABIs/x86-64-ABI`) — the C convention the syscall convention deviates from, and the authority for the deviation.

### `copying-data-across-the-boundary.md` — Copying Data Across the Boundary

- **Opens with:** a rule that sounds like bureaucracy and is not — the kernel may never dereference a user pointer directly, even though it is perfectly capable of doing so. Three separate things can go wrong (the pointer may be invalid, it may point at kernel memory, or its contents may change between two reads) and the copy routines exist to make each of the three a handled case rather than a crash or a hole.
- **Sections:**
  - `## `copy_from_user` and `copy_to_user`` — the interface, the return value (bytes **not** copied, which trips up everyone once), and the standard `if (copy_from_user(...)) return -EFAULT;` idiom shown in ` ```c `.
  - `## `access_ok`, and what it does not check` — it checks the address range is in the user half, nothing more. It does **not** check the mapping exists — that is the fault handler's job — which is why `access_ok` alone is never sufficient and why the copy routines still need the exception table.
  - `## The exception table` — the mechanism that makes a faulting copy return an error instead of oopsing: the instruction that touches user memory is registered in `__ex_table` with a fixup address, and the page-fault handler consults it before deciding this is a kernel bug. This is the single most elegant thing in the folder; give it the space.
  - `## SMAP and SMEP` — hardware backup for the same rule. SMEP stops the kernel executing user pages; SMAP stops it *accessing* them at all except inside a window opened by `stac`/`clac`. The consequence worth stating: on an SMAP machine, an accidental user dereference in kernel code faults immediately rather than silently working.
  - `## `__user` and sparse` — the annotation that lets a static checker find the bug the hardware would otherwise find at runtime. Link back to `../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md`, which owns the annotation vocabulary.
  - `## Double-fetch bugs` — the TOCTOU class this interface creates: read a length from user memory, validate it, read it again, and act on the second value. Another thread can change it in between. State the rule — copy once into kernel memory, then validate the copy — and note that this is a real recurring CVE class, not a theoretical one.
  - `## Structures that grow` — `copy_struct_from_user` and the size-argument convention that lets a struct gain fields without a new syscall: old binary, small struct, kernel zero-fills the rest. Verify the helper's name and semantics at v6.18.
- **Anchor:** a Mermaid `sequenceDiagram` — Kernel code, `copy_from_user`, MMU, Page-fault handler, Exception table — showing the faulting case: the copy touches an unmapped user page, the fault handler recognises the faulting instruction is in the exception table, jumps to the fixup, and the copy returns a non-zero count that becomes `-EFAULT`. Caption: "A user pointer that was not valid, turned into an error return instead of an oops."
- **KernelFacts:** `structure` — `[["struct exception_table_entry", "arch/x86/include/asm/extable.h"]]`; `path` — `"copy_from_user() → access_ok() → faulting access → exc_page_fault() → fixup_exception() → -EFAULT"`; `observe` — `sudo grep -c . /proc/kallsyms >/dev/null; dmesg | grep -i smap` (SMAP support is reported at boot; `grep smap /proc/cpuinfo` shows the CPU flag); `trap` — "`copy_from_user` returns the number of bytes it could **not** copy. Zero means success. Treating the return as a byte count or as a boolean success flag is a bug that tests will not catch, because the common case is zero either way."
- **References:**
  - `<Src file="arch/x86/mm/extable.c" symbol="fixup_exception" />` — the fault handler's decision point, in fifteen readable lines.
  - `https://docs.kernel.org/core-api/kernel-api.html`, the user-space access section — the API contract for the copy helpers, stated by the kernel's own documentation.
  - LWN, *"Finding double-fetch bugs"* (`https://lwn.net/Articles/755906/`) — the bug class with real examples and the tooling built to find it.
  - Intel SDM Vol. 3A, the SMAP/SMEP description in ch. 4 — what the hardware enforces and what `stac`/`clac` open.

### `the-vdso.md` — The vDSO **[WAH]** **[Lab host=any-linux]**

- **Opens with:** the observation that some "system calls" are not system calls. `clock_gettime` is called millions of times a second by ordinary programs, and paying a privilege transition for a value the kernel has already computed and could simply *show* you would be absurd. The vDSO is the kernel publishing that value into your address space.
- **Sections:**
  - `## What it is` — a small ELF shared object built into the kernel image and mapped into every process at exec time. Not a file on disk, has no path, and yet appears in `/proc/PID/maps` and in `ldd` output. Name the mapping (`[vdso]`) and the data page (`[vvar]`).
  - `## What it provides` — the short list on x86-64: `clock_gettime`, `gettimeofday`, `time`, `getcpu`, and `clock_getres`. Note that the list is architecture-dependent and that anything not in it still costs a real syscall.
  - `## How it works` — the `vvar` page holds the timekeeping data the kernel updates; the vDSO code reads it with a seqlock retry loop and does the arithmetic in user space. Point at `../09-concurrency-and-locking/seqlocks.md` for the retry protocol — the vDSO is its canonical user, so this is a link rather than an explanation.
  - `## What actually happens` **[WAH]** — when `clock_gettime(CLOCK_MONOTONIC, &ts)` is called. libc jumps to the vDSO symbol, which reads the sequence counter, reads the clocksource (a `rdtsc` on most machines), applies the kernel's mult/shift, re-checks the counter, and returns — with **no privilege transition at all**. Then show what `strace` prints: nothing. Say explicitly that "strace shows no syscall" is not evidence that nothing happened, and that this surprises people debugging timing code.
  - `## When it falls back` — if the clocksource is not vDSO-capable (an HPET or ACPI PM timer rather than a usable TSC), the vDSO code makes a real syscall instead. This is why the same binary can show wildly different `clock_gettime` costs on two machines, and it is a genuine production performance issue.
  - `## The vsyscall page, briefly` — the fixed-address predecessor, now emulated or disabled because a fixed executable address is a gift to exploit writers. One paragraph, and a note that `vsyscall=none` is the modern default.
  - `<Lab host="any-linux" title="See the vDSO in your own process" time="10 min">` — (1) `grep -E 'vdso|vvar' /proc/self/maps`; (2) `ldd /bin/ls` and find `linux-vdso.so.1 =>` with no path; (3) extract it — `dd` the mapping out of `/proc/self/mem` is fragile, so instead use `objdump -T` on the copy the kernel exposes if the distribution ships one, and otherwise run a three-line C program that calls `clock_gettime` in a loop under `strace` and observe that nothing is traced; (4) contrast with `strace -c` on a loop of `getpid()`, which *is* traced. Show expected output for each step. "If it fails": some hardened kernels hide `/proc/self/maps` details under `kptr_restrict`, and a container may present a different clocksource.
- **Anchor:** a Mermaid `flowchart LR` with two paths from the same C call — the vDSO path staying entirely in user space and reading `[vvar]`, and the syscall path crossing into the kernel — with the privilege boundary drawn once and crossed only by the second. Caption: "The same `clock_gettime()` call, with and without a usable vDSO clocksource."
- **KernelFacts:** `structure` — `[["struct vdso_data", "include/vdso/datapage.h"]]` (verify the v6.18 name — the vDSO data structures were reorganised recently); `path` — `"clock_gettime() → vDSO __vdso_clock_gettime() → seqlock read of the vvar page → rdtsc → arithmetic → return, no kernel entry"`; `observe` — `grep -E 'vdso|vvar' /proc/self/maps && cat /sys/devices/system/clocksource/clocksource0/current_clocksource`; `trap` — "`strace` showing no syscall does not mean no kernel code ran on your behalf. The vDSO is kernel-built, kernel-mapped code running at user privilege, and it is invisible to every syscall tracer."
- **References:**
  - `man 7 vdso` — the canonical description, including the per-architecture symbol lists.
  - `<Src file="arch/x86/entry/vdso/vma.c" symbol="arch_setup_additional_pages" />` — where the mapping is actually installed into a new process's address space.
  - `https://docs.kernel.org/timers/index.html` — the timekeeping documentation the `vvar` data comes from; confirm the exact page exists at v6.18 before citing.
  - LWN, *"On vsyscalls and the vDSO"* (`https://lwn.net/Articles/446528/`) — the history of why the fixed-address version had to go; older than the pinned kernel and correct about the reasoning.

- [ ] **Step 1: Write `arguments-return-values-and-errno.md`** to the brief above.
- [ ] **Step 2: Write `copying-data-across-the-boundary.md`** to the brief above.
- [ ] **Step 3: Write `the-vdso.md`** to the brief above.
- [ ] **Step 4: Verify every symbol** — `MAX_ERRNO`, `copy_from_user`, `access_ok`, `fixup_exception`, `exception_table_entry`, `copy_struct_from_user`, `arch_setup_additional_pages`, `vdso_data` — against Elixir v6.18, and run each `<Lab>` command on a real Linux machine before committing the expected output.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 6: Commit**

```bash
git add docs/linux/05-syscalls-and-the-boundary
git commit -m "docs: write the syscall ABI, user-memory copying, and the vDSO"
```

---

## Task 7: Folder 05 — libc, and ABI stability

**Files:**
- Modify: `docs/linux/05-syscalls-and-the-boundary/libc-is-not-the-kernel.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/abi-stability-and-compat.md`

**Interfaces:**
- Consumes: `05/arguments-return-values-and-errno` and `05/the-syscall-table-and-dispatch` (Tasks 5–6).
- Produces: the ABI-stability framing that folder 06's `threads-are-tasks` and folder 15's container pages both lean on. Only the first of those exists; the second gets prose, not a link.

### `libc-is-not-the-kernel.md` — libc Is Not the Kernel **[WAH]** **[Misc]**

- **Opens with:** the layer readers forget is there. Almost nobody calls the kernel directly; they call a C library that calls the kernel, and the library is entitled to do more, less, or something else entirely. Most "the kernel does X" surprises are really "glibc does X".
- **Sections:**
  - `## What a wrapper actually adds` — five things, each with an example: errno conversion, argument massaging (`fork()` calling `clone`), caching (`getpid` historically, `sysconf` values), cancellation points for pthreads, and outright emulation where the syscall does not exist on this architecture.
  - `## What actually happens` **[WAH]** — when you call `fopen`. `fopen` → `open` wrapper → `openat` syscall (not `open` — the syscall glibc uses is not the one named in your source), plus a `fstat` for buffering decisions and a `malloc` that may itself have caused an `mmap`. Show the `strace` output next to the two-line C program and count the crossings. The point: your source is not a syscall trace, and the difference is entirely libc's doing.
  - `## Going direct: `syscall(2)`` — when and why (a syscall newer than your libc, an interface libc deliberately does not wrap like `gettid` historically, or exact control for a test). Show the call shape in ` ```c ` and state the two obligations it puts on you: convert the negative return yourself, and know the number is architecture-specific.
  - `## `<Tabs>`: glibc, musl, and raw` — three tabs showing the same operation (open a file and read a byte) written against glibc, against musl, and as a raw `syscall()`, with a sentence under each on what differs. This is the page's comparison anchor.
  - `## Where glibc and musl actually differ` — a table: stdio buffering behaviour, thread stack defaults, DNS resolution (`nsswitch` versus a fixed resolver), locale support, `LD_PRELOAD` and dynamic-linker extensions, and static-linking friendliness. State the consequence readers actually hit: a glibc-built binary does not run on Alpine, and the failure looks like a missing file rather than an ABI mismatch.
  - `## The kernel does not care which libc you use` — the syscall interface is the contract, and it is the same one for glibc, musl, Bionic, Go's runtime (which issues syscalls directly and skips libc entirely), and Rust's `std`. Note Go specifically, because a Go binary's `strace` output looks nothing like a C program's.
  - `## Misconceptions` **[Misc]** — (1) "`fork()` is a syscall" — on Linux it is a libc wrapper over `clone`; (2) "musl is glibc with fewer features" — it is a different implementation with different defaults, and some differences (DNS, stdio buffering) change program behaviour rather than just performance; (3) "static linking removes the libc dependency" — it removes the *runtime* dependency, not the behavioural one, and static glibc still has runtime-loaded pieces (NSS) that surprise people.
- **Anchor:** the `<Tabs>` block above, plus a small Mermaid `flowchart LR`: your code → libc → syscall → kernel, with a second arrow bypassing libc for the `syscall(2)` and Go cases.
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"]]`; `path` — `"fopen() → glibc open() wrapper → openat(2) → do_sys_openat2() → struct file"` (verify `do_sys_openat2` at v6.18); `observe` — `strace -f -e trace=openat,mmap,brk ./a.out`; `trap` — "The name in your source is often not the name of the syscall. `open()` becomes `openat`, `fork()` becomes `clone`, and `exit()` becomes `exit_group`. Reading a trace as though it should mirror your code will mislead you every time."
- **References:**
  - `man 2 syscall` — the direct interface and its per-architecture rules.
  - `https://www.musl-libc.org/faq.html` — musl's own account of where and why it differs from glibc; short and unusually honest.
  - `https://sourceware.org/glibc/wiki/SyscallWrappers` — glibc's stated policy on which syscalls it wraps and which it deliberately does not.
  - `man 2 clone` — the syscall behind `fork`, `vfork`, and `pthread_create`, and the reason all three are the same mechanism.

### `abi-stability-and-compat.md` — ABI Stability and Compat

- **Opens with:** a rule stated as an engineering constraint rather than a slogan. "We do not break user space" means a binary compiled in 2005 must still run, which forbids removing a syscall, changing an argument's meaning, or repurposing a flag bit — forever. The page's job is to show what that constraint costs and how interfaces stay extensible under it.
- **Sections:**
  - `## What the promise covers, and what it does not` — covered: syscall numbers and semantics, `/proc` and `/sys` files that programs parse, the ELF ABI, signal semantics. Not covered: in-kernel interfaces, module symbols, debugfs, and anything documented as unstable. Link back to `../04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md` rather than restating the argument.
  - `## How interfaces grow anyway` — three techniques, each with a real example: a new syscall alongside the old (`open` → `openat` → `openat2`), a flags argument with reserved bits that must be zero (so an old kernel rejects a new flag rather than ignoring it), and a struct-plus-size argument (`clone3`, `openat2`, `sched_setattr`) where the kernel zero-fills or rejects based on the caller's size. The middle one is the subtle one — say explicitly that requiring unknown flags to be zero is what makes later extension safe.
  - `## What the promise costs` — permanently ugly interfaces. Give two honest examples that cannot be fixed: the `stat` family's multiple incompatible structures across architectures and time (and `statx` as the response), and syscall numbers with holes where mistakes were withdrawn before release. This section is what makes the page more than a restatement of policy.
  - `## `compat_`: 32-bit programs on a 64-bit kernel` — a different syscall table, different structure layouts (pointer and `long` widths, alignment, padding), and `compat_` variants that translate. Note where this leaks: `struct timespec` sizes, ioctl argument structures, and the fact that a compat task's syscall numbers come from the 32-bit table.
  - `## The seccomp architecture trap` — because the compat table exists, a filter that checks only the syscall number can be bypassed by re-entering through the other ABI. The rule — check `arch` first, then `nr` — is stated here and referred to by folder 16 later. Prose forward-reference, no link.
  - `## Where the promise gets tested` — one paragraph on regressions that were reverted because they broke user space even when the previous behaviour was a bug, and one on the rare deliberate breaks (removing an interface nobody used, tightening something that was a security hole). Keep it factual.
- **Anchor:** a table of the three extension techniques — new syscall, reserved flag bits, struct plus size — with columns for a real example, what an old kernel does with a new caller, and what a new kernel does with an old caller. That two-way compatibility matrix is the actual content of the page.
- **KernelFacts:** `structure` — `[["struct open_how", "include/uapi/linux/openat2.h"]]`; `path` — `"openat2(dfd, path, &how, size) → copy_struct_from_user() → size checked → unknown fields must be zero → -E2BIG or -EINVAL"` (verify the exact error returns at v6.18); `observe` — `ls /usr/include/asm/unistd_32.h /usr/include/asm/unistd_64.h && grep -c . /proc/self/status`; `trap` — "Extensibility comes from *rejecting* unknown flags, not ignoring them. An interface that silently ignores a bit it does not understand can never safely define that bit later, because programs already depend on it doing nothing."
- **References:**
  - `https://docs.kernel.org/admin-guide/abi.html` — the project's own statement of what is stable and what is not, with the stability levels defined.
  - `man 2 openat2` — the modern extensible-syscall pattern in its cleanest form, including the size and zero-fill rules.
  - Torvalds' "we do not break user space" mail, `https://lkml.org/lkml/2012/12/23/75` — the rule in its author's own words, worth reading once for the reasoning as much as the tone.
  - LWN, *"The extensible-syscall pattern"* coverage of `clone3`/`openat2` (`https://lwn.net/Articles/792628/`) — why the struct-plus-size convention was adopted and what it replaced.

- [ ] **Step 1: Write `libc-is-not-the-kernel.md`** to the brief above, including the three-tab `<Tabs>` block with real compiling code.
- [ ] **Step 2: Write `abi-stability-and-compat.md`** to the brief above.
- [ ] **Step 3: Compile and run the three tab examples** and the `syscall(2)` example, and paste the *actual* `strace` output into the [WAH] section rather than a plausible reconstruction.
- [ ] **Step 4: Verify** `open_how`, `copy_struct_from_user`, and `do_sys_openat2` against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/05-syscalls-and-the-boundary
git commit -m "docs: write libc versus the kernel, and syscall ABI stability"
```

---

## Task 8: Folder 05 — tracing syscalls, and the add-a-syscall lab

**Files:**
- Modify: `docs/linux/05-syscalls-and-the-boundary/tracing-and-intercepting-syscalls.md`
- Modify: `docs/linux/05-syscalls-and-the-boundary/lab-adding-a-syscall.md`

**Interfaces:**
- Consumes: everything earlier in folder 05, plus `01/building-a-kernel` and `01/booting-your-kernel-in-qemu` for the lab's build-and-boot cycle.
- Produces: the folder's payoff page. Nothing later depends on it structurally, which is why it goes last.

### `tracing-and-intercepting-syscalls.md` — Tracing and Intercepting Syscalls **[WAH]**

- **Opens with:** the distinction the page is built on — watching a syscall, and changing what it does, are completely different mechanisms with completely different costs, and the tools people reach for are frequently the wrong one for the job they have.
- **Sections:**
  - `## What actually happens` **[WAH]** — when you run `strace ls`. `PTRACE_TRACEME` and `execve`, then a stop on **every** syscall entry and every syscall exit, each stop being a context switch to the tracer and back. Give the cost honestly — one to two orders of magnitude on syscall-heavy workloads — and state the consequence: `strace` changes the timing of what it measures, so it is a correctness tool, not a performance tool.
  - `## `perf trace`, and why it is cheaper` — the tracepoint path instead of the ptrace path: `raw_syscalls:sys_enter`/`sys_exit` write into a ring buffer with no stop and no context switch per call. Give the trade-off — less detail per call, no argument decoding for free, and no ability to modify.
  - `## `<Tabs>`: the same question, four ways` — "which files did this process open?" answered with `strace -e trace=openat`, `perf trace -e openat`, `bpftrace` (a one-liner on the tracepoint), and `opensnoop`. One tab each, each with the command and its output shape, and a sentence on what it costs. Do not link to folders 17–18; name the tools in prose.
  - `## Interception, properly` — seccomp user notification (`SECCOMP_RET_USER_NOTIF`): the filter suspends the syscall and hands a file descriptor to a supervisor process, which inspects the arguments and decides. State plainly what makes it correct where ptrace is not — the supervisor sees the arguments in a race-free way — and mention the container runtimes that use it.
  - `## Why `LD_PRELOAD` is not syscall interception` — it replaces *library* functions. A static binary, a Go program, or a direct `syscall()` sails straight past it. Two sentences, because the belief is common and the correction is short.
  - `## What each mechanism can see and do` — the summary table: ptrace, tracepoints, kprobes, seccomp-notify, and `LD_PRELOAD`, with columns for what it observes, whether it can modify, its cost, and whether it survives a static binary.
  - `## Why the ptrace stop is where it is` — one paragraph tying back to `./the-entry-path.md`: the tracing hook lives in the syscall enter/exit work, which is also where seccomp runs and where signals are delivered. Three features, one code path.
- **Anchor:** the capability table above, plus a Mermaid `sequenceDiagram` for the ptrace stop — Tracee, Kernel entry work, Tracer — showing two stops and two context switches for a single syscall. Caption: "One syscall under `strace`: two stops, two context switches, and the reason tracing is expensive."
- **KernelFacts:** `structure` — `[["struct seccomp_notif", "include/uapi/linux/seccomp.h"]]`; `path` — `"syscall entry → syscall_trace_enter() → ptrace_report_syscall() → tracer wakes → tracee resumes → handler → exit stop"` (verify the v6.18 function names, which live in `kernel/entry/common.c` and `kernel/ptrace.c`); `observe` — `strace -c -f ls >/dev/null` then `perf trace -s ls >/dev/null`, comparing wall time; `trap` — "`strace` does not observe a program, it suspends it twice per syscall. Anything you conclude about timing from a traced run is a fact about the tracer."
- **References:**
  - `man 2 ptrace`, the syscall-stop section — the definitive statement of when stops happen and what the tracer sees at each.
  - `man 2 seccomp_unotify` — the modern interception interface, with a complete worked example in the man page itself.
  - `https://man7.org/linux/man-pages/man1/perf-trace.1.html` — the low-overhead alternative and its option surface.
  - LWN, *"Seccomp user-space notification"* (`https://lwn.net/Articles/756233/`) — why ptrace-based interception was inadequate and what replaced it.

### `lab-adding-a-syscall.md` — Lab: Add a System Call **[Lab host=qemu]**

- **Opens with:** why this exercise is worth an afternoon — every abstraction in this folder becomes concrete the moment you own both sides of the boundary. You choose a number, write a handler, rebuild, boot, and call it from C, and afterwards the dispatch table is no longer a diagram.
- **Structure:** this page is mostly one long `<Lab>`, but it still opens with the mental-model paragraph and still ends with `## References` and `<KernelFacts>`.
- **Sections:**
  - `## What you are about to do` — the four edits, named up front: a table entry, a `SYSCALL_DEFINE`, a rebuild, and a caller. Say that in real kernel development adding a syscall is a heavyweight act requiring cross-architecture agreement, and that this lab is a lab.
  - `<Lab host="qemu" title="Add a syscall and call it" time="60 min, most of it the rebuild">`:
    1. Pick the next free number in `arch/x86/entry/syscalls/syscall_64.tbl` and add a line — show the exact line, with the entry point name. Warn in a `:::warning` that you must pick a number **above** everything in use and that this kernel's numbering is now local to you; a binary built against it means nothing elsewhere.
    2. Add the implementation. Show the complete function in ` ```c `: a `SYSCALL_DEFINE1` taking a user pointer, using `copy_to_user` to return a value, and returning `0` or `-EFAULT`. Put it in a new file under `kernel/` and add the `obj-y` line, so the reader also touches Kbuild — link to `../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md`.
    3. Rebuild with the same `make -j$(nproc)` invocation folder 01 established, and state the realistic incremental build time.
    4. Boot in QEMU with the folder 01 command line, verbatim.
    5. Call it from C with `syscall(NNN, &buf)`, compiled statically because the BusyBox initramfs has no dynamic loader for a glibc binary — this is the step that catches people, so say it before they hit it.
    6. Watch it: `strace ./caller` shows `syscall_0xNNN` with an unrecognised name, which is itself the lesson about where syscall names come from.
    - Expected output for every step, including the `strace` line with the unknown-syscall rendering.
    - "If it fails": the two most likely causes are forgetting the `obj-y` line (the symbol will be missing at link time, not at boot) and a dynamically linked test binary (the kernel will report `No such file or directory` for a binary that plainly exists — the missing file is the interpreter).
  - `## What you just proved` — a short closing section connecting each step back to the page that explained it: the table entry to `./the-syscall-table-and-dispatch.md`, the `copy_to_user` to `./copying-data-across-the-boundary.md`, the `-EFAULT` to `./arguments-return-values-and-errno.md`, and the unrecognised name in `strace` to `./libc-is-not-the-kernel.md`.
  - `## Why upstream would reject this` — a paragraph of honesty: a new syscall needs a real justification, an architecture-independent design, a man page, a selftest, and agreement across every architecture's table. Naming that is what stops this lab teaching a bad habit.
- **Anchor:** a Mermaid `flowchart LR` of the four files touched and the artefacts each produces — `.tbl` → generated headers → the object file → `bzImage` — showing why forgetting the `obj-y` line fails at link time rather than at boot. Caption: "Four edits, and where each one lands in the build."
- **KernelFacts:** `structure` — `[["SYSCALL_DEFINE1", "include/linux/syscalls.h"], ["sys_call_table", "arch/x86/entry/syscall_64.c"]]` (verify); `path` — `"syscall_64.tbl → generated syscalls_64.h → sys_call_table[NNN] → __x64_sys_yours() → __do_sys_yours()"`; `observe` — `strace ./caller 2>&1 | grep syscall_`; `trap` — "Adding a syscall is the easy part; keeping it is the hard part. A syscall number is a permanent commitment, which is why upstream asks whether an existing interface can be extended before it will consider a new one."
- **References:**
  - `<Src file="arch/x86/entry/syscalls/syscall_64.tbl" />` — the file you are editing, and the format is documented in its own header comment.
  - `https://docs.kernel.org/process/adding-syscalls.html` — the kernel's own guide to doing this for real, including everything this lab skips.
  - `man 2 syscall` — the caller side, and the reason the test program uses `syscall()` rather than a wrapper.
  - `https://docs.kernel.org/dev-tools/kselftest.html` — what a real new syscall must ship with, which is the point of the closing section.

- [ ] **Step 1: Write `tracing-and-intercepting-syscalls.md`** to the brief above.
- [ ] **Step 2: Actually run the lab** in the QEMU environment folder 01 describes, from a clean checkout of v6.18, and record the real output of every step. **Do not write this page from expectation** — the failure modes in the "if it fails" line are the ones you actually hit.
- [ ] **Step 3: Write `lab-adding-a-syscall.md`** from what the run produced.
- [ ] **Step 4: Verify** `syscall_trace_enter`, `ptrace_report_syscall`, `seccomp_notif`, and the table's file location against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/05-syscalls-and-the-boundary
git commit -m "docs: write syscall tracing and the add-a-syscall lab"
```

---
## Task 9: Folder 06 — `task_struct`, and threads as tasks

**Files:**
- Modify: `docs/linux/06-processes-and-threads/task-struct-the-anatomy-of-a-task.md`
- Modify: `docs/linux/06-processes-and-threads/threads-are-tasks.md`

**Interfaces:**
- Consumes: `04/kernel-data-structures` (intrusive lists and trees — linked, not re-explained) and `04/container-of-and-embedded-structs`.
- Produces: `06/task-struct-the-anatomy-of-a-task`, the declared prerequisite of six pages in this folder, and `06/threads-are-tasks`, which folder 07 assumes when it says the scheduler schedules tasks rather than processes.

### `task-struct-the-anatomy-of-a-task.md` — `task_struct`: The Anatomy of a Task **[Lab host=qemu-gdb]**

- **Opens with:** the framing that makes the struct readable — Linux does not have a process object and a thread object and a scheduler-entity object. It has one structure, allocated once per schedulable thing, and everything the kernel knows about that thing is either in it or reachable from it by one pointer. It has grown to hundreds of fields because *everything* the kernel does touches a task.
- **Sections:**
  - `## One struct, one schedulable entity` — allocated by `fork`, freed after the parent reaps, and pointed to from the per-CPU `current`. Explain `current` on x86-64 (a per-CPU variable, not a stack-walk trick) since readers coming from older books expect the `thread_info`-on-the-stack version.
  - `## The twelve fields that matter` — grouped by concern, presented as a **Mermaid `classDiagram`**, not a struct dump: identity (`pid`, `tgid`, `comm`), state (`__state`, `exit_state` — verify the leading underscores at v6.18), scheduling (`prio`, `se`, `sched_class`), memory (`mm`, `active_mm`), files (`files`, `fs`), signals (`signal`, `sighand`, `pending`), credentials (`cred`), relationships (`real_parent`, `parent`, `children`, `sibling`). Each with one line on what it is for and `<Src>` on the type.
  - `## What is a pointer, and why that matters` — `mm`, `files`, `fs`, `sighand` are *pointers to shared, refcounted objects*. This single fact is the entire mechanism of threading, and stating it here makes the next page almost trivial.
  - `## `mm` versus `active_mm`` — a kernel thread has no address space of its own and borrows the previous task's. Explain why (avoiding a page-table switch on every kernel-thread wakeup) and what it means when reading `/proc`: a kernel thread shows an empty `maps`.
  - `## Where it lives, and the stack` — the task's kernel stack (8 or 16 KiB depending on `CONFIG_`), `THREAD_SIZE`, and the fact that a deep call chain in kernel code is a real hazard rather than a theoretical one. Link back to `../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md` for the small-stack constraint.
  - `## Finding tasks` — the task list, the PID hash via `struct pid`, and `for_each_process`. Enough that a reader can follow `lx-ps` in the next section.
  - `<Lab host="qemu-gdb" title="Walk a real task_struct in GDB" time="20 min">` — boot the lab kernel with `-s -S`, attach, load `vmlinux`, run `lx-ps` to list tasks, then `p $lx_current()` and print `comm`, `pid`, `tgid`, and `mm`. Then `p *$lx_current().mm` and read `mmap_base`. Show expected output for each command. "If it fails": the `scripts/gdb` helpers need `CONFIG_GDB_SCRIPTS` and an `add-auto-load-safe-path` entry, both covered in `../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md`.
- **Anchor:** the Mermaid `classDiagram` of the twelve fields grouped by concern, with the pointer fields drawn as associations to their target structs. Caption: "The dozen `task_struct` fields worth holding in your head, and the four that are pointers to objects a thread can share."
- **KernelFacts:** `structure` — `[["struct task_struct", "include/linux/sched.h"], ["struct pid", "include/linux/pid.h"]]`; `path` — `"current → task_struct → mm_struct / files_struct / signal_struct / cred"`; `observe` — `sudo cat /proc/1/status | head -20`; `trap` — "`current` is not a global variable and not derived from the stack pointer on x86-64 — it is a per-CPU variable. Code that assumes there is one `current` is code that will break the first time it runs on a second CPU."
- **References:**
  - `<Src file="include/linux/sched.h" symbol="task_struct" />` — the definition, whose comments are the best available field documentation.
  - `https://docs.kernel.org/scheduler/index.html` — the scheduler documentation, for the `se` and `sched_class` fields this page only names.
  - Love, *Linux Kernel Development*, 3rd ed., ch. 3 — the clearest long-form treatment of the process descriptor; predates v6.18 substantially and describes `thread_info` on the stack, which is no longer how x86-64 works. Say so.
  - `https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html` — the in-tree GDB helpers the lab uses.

### `threads-are-tasks.md` — Threads Are Tasks **[WAH]** **[Misc]**

- **Opens with:** the design decision that makes Linux's process model unusual and simple at once — instead of a process containing threads, there are only tasks, and "sharing" is a per-resource choice made at creation time. A thread is not a lighter object; it is the same object with more pointers aimed at the same targets.
- **Sections:**
  - `## `clone()` is the real primitive` — `fork`, `vfork`, and `pthread_create` are all `clone` with different flags. Show the three flag sets side by side in a table.
  - `## The flags, as a menu` — `CLONE_VM` (address space), `CLONE_FS` (root and cwd), `CLONE_FILES` (fd table), `CLONE_SIGHAND` (signal handlers), `CLONE_THREAD` (thread group), `CLONE_SYSVSEM`, `CLONE_SETTLS`, plus the namespace flags folder 15 owns (named, not explained). For each, one line on what sharing it actually means in terms of the `task_struct` pointer involved — which is why the previous page established that those fields are pointers.
  - `## `tgid` versus `pid`` — the kernel's `pid` is per-task; the `tgid` is what POSIX calls a process ID. `getpid()` returns the `tgid` and `gettid()` returns the `pid`, which means the kernel's own naming is the reverse of the one users learn. State it plainly and give the `/proc/PID/task/TID` layout as the evidence.
  - `## What actually happens` **[WAH]** — when you call `pthread_create`. glibc allocates a stack with `mmap`, sets up TLS, and calls `clone` with `CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID`. Then show `ps -eLf` on a multi-threaded program and point out that the LWPs are tasks with the same TGID. Close with the consequence that surprises people: threads are not cheaper to *schedule* than processes on Linux — they are cheaper to *create* and to communicate between, and that is a different claim.
  - `## `CLONE_THREAD` is what makes a thread group` — without it you get a process sharing memory, which is legal, occasionally useful, and confusing to every tool. Note that some of the flag combinations are rejected outright (e.g. `CLONE_THREAD` without `CLONE_SIGHAND`) and that the constraints are documented in `man 2 clone`.
  - `## `clone3`, and why it exists` — the flag word ran out of bits. `struct clone_args` plus a size, per the extensible pattern in `../05-syscalls-and-the-boundary/abi-stability-and-compat.md`.
  - `## Misconceptions` **[Misc]** — (1) "threads are lighter than processes on Linux" — creation is cheaper and context switching between threads avoids a page-table switch, but the scheduled object is identical; (2) "a process has one `task_struct`" — it has one per thread; (3) "`getpid()` returns the kernel's idea of this thread's id" — it returns the thread *group* id; `gettid()` returns the task's own.
- **Anchor:** a WaveDrom `reg` strip of the `clone()` flag word — the low byte as the exit-signal field (`CSIGNAL`), then `CLONE_VM`(8), `CLONE_FS`(9), `CLONE_FILES`(10), `CLONE_SIGHAND`(11), `CLONE_PIDFD`(12), `CLONE_PTRACE`(13), `CLONE_VFORK`(14), `CLONE_PARENT`(15), `CLONE_THREAD`(16), and the namespace bits above — verified against `<Src file="include/uapi/linux/sched.h" />` before committing. Title it "What `pthread_create` asks to share, one bit at a time".
- **KernelFacts:** `structure` — `[["struct task_struct", "include/linux/sched.h"], ["struct signal_struct", "include/linux/sched/signal.h"]]`; `path` — `"pthread_create() → clone(CLONE_VM|CLONE_THREAD|…) → kernel_clone() → copy_process() → wake_up_new_task()"`; `observe` — `ps -eLo pid,tid,comm | head` (verify the column names on the target distribution's `procps`); `trap` — "There is no process object. A process is a set of tasks that share a thread group id, and every tool that shows you 'a process' is aggregating tasks on your behalf."
- **References:**
  - `man 2 clone` — the flag list, the illegal combinations, and the `clone3` structure; the single most useful page for this topic.
  - `<Src file="kernel/fork.c" symbol="copy_process" />` — where each flag turns into either a shared pointer or a copy; readable, and the flags appear in order.
  - `man 7 pthreads` — the user-space model and how it maps onto tasks, including the `gettid`/`getpid` distinction.
  - LWN, *"clone3(), fork(), and the future of process creation"* (`https://lwn.net/Articles/792628/`) — why the flag word had to be replaced.

- [ ] **Step 1: Write `task-struct-the-anatomy-of-a-task.md`** to the brief above.
- [ ] **Step 2: Write `threads-are-tasks.md`** to the brief above.
- [ ] **Step 3: Verify** `task_struct` field names (`__state` in particular), `copy_process`, `kernel_clone`, `signal_struct`, and every `CLONE_*` bit position against Elixir v6.18. **The WaveDrom strip is wrong until the bit positions are checked.**
- [ ] **Step 4: Run the GDB lab** and paste real output.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/06-processes-and-threads
git commit -m "docs: write task_struct and the threads-are-tasks model"
```

---

## Task 10: Folder 06 — fork, copy-on-write, and exec

**Files:**
- Modify: `docs/linux/06-processes-and-threads/fork-and-copy-on-write.md`
- Modify: `docs/linux/06-processes-and-threads/exec-and-binary-formats.md`

**Interfaces:**
- Consumes: `06/threads-are-tasks` (Task 9).
- Produces: `06/fork-and-copy-on-write` and `06/exec-and-binary-formats`, the two prerequisites of `06/lab-watching-a-process-be-born`. Folder 08's `demand-paging-and-cow` deepens the COW mechanism and links back here for the process-level story.

### `fork-and-copy-on-write.md` — `fork()` and Copy-on-Write **[WAH]** **[Lab host=any-linux]**

- **Opens with:** the apparent absurdity of the interface — `fork()` says "duplicate this entire process, including its ten gigabytes of memory", and it returns in microseconds. It does that by duplicating almost nothing and lying convincingly about the rest, and the lie is maintained by the MMU.
- **Sections:**
  - `## What is genuinely copied` — a new `task_struct`, a new kernel stack, a new `mm_struct` with a copied VMA list, a copied file-descriptor *table* (not the `struct file`s it points at), and copied credentials. A table with three columns: object, copied or shared, and refcounted.
  - `## What is not copied: the pages` — both address spaces point at the same physical pages, and every writable private mapping is marked read-only in both page tables. Say precisely that COW is a *page-table* operation, not a memory operation.
  - `## What actually happens` **[WAH]** — the first write after a fork. The store faults because the PTE is read-only, `do_wp_page` runs, sees the page is COW rather than genuinely read-only, allocates a new page, copies 4 KiB, installs a writable PTE, and the instruction re-executes. State the two-cost consequence: a fork is cheap and the *first write to each page* afterwards costs a fault plus a copy, which is why fork-heavy servers show unexplained minor-fault storms.
  - `## Why fork of a 10 GB process can still fail` — the VMA list is copied, the page tables are copied (which for a large sparse address space is itself real work and real memory), and overcommit accounting may refuse. Link forward in prose to folder 08's overcommit page — a link is fine, that page exists in this phase: `../08-memory-management/demand-paging-and-cow.md`.
  - `## `vfork` and `posix_spawn`` — `vfork` shares the address space and suspends the parent until exec, which is a sharp tool with a small correct use; `posix_spawn` is what you should actually use, and on Linux it is `clone(CLONE_VFORK|CLONE_VM)` plus exec. Note the classic embedded reason: fork on a no-MMU system cannot work at all.
  - `## fork and threads do not mix well` — only the calling thread survives into the child, but all the *locks* the other threads held are still held, in a process where their owners no longer exist. This is why `fork` in a threaded program is safe only if the child immediately execs, and why `pthread_atfork` exists and is not a real fix.
  - `<Lab host="any-linux" title="Watch copy-on-write happen" time="15 min">` — a C program that allocates 256 MiB, touches it, forks, and has the child write one byte per page in a loop; measure with `/usr/bin/time -v` (minor faults before and after) and `ps -o rss` for both processes. Show expected output: the child's minor-fault count rises by roughly one per page touched, and RSS diverges. "If it fails": the allocation may be served by `mmap` with `MAP_NORESERVE` behaviour that changes the numbers, and a transparent huge page will make the fault count 512× smaller than expected — which is itself worth seeing, and points at `../08-memory-management/hugepages-and-thp.md`.
- **Anchor:** a Mermaid `sequenceDiagram` — Parent, Kernel, Page tables, Child — showing fork marking pages read-only in both, the child's write faulting, the copy, and the re-execution. Caption: "One page, from shared-and-read-only at fork to privately writable after the first store."
- **KernelFacts:** `structure` — `[["struct mm_struct", "include/linux/mm_types.h"], ["struct kernel_clone_args", "include/linux/sched/task.h"]]`; `path` — `"fork() → kernel_clone() → copy_process() → copy_mm() → dup_mmap() → write faults → do_wp_page()"` (verify `dup_mmap` and `do_wp_page` at v6.18 — the fault-path helpers were reorganised for folios); `observe` — `/usr/bin/time -v ./forker 2>&1 | grep -i 'minor'`; `trap` — "Copy-on-write does not make `fork()` free, it makes it *deferred*. The cost reappears as a minor fault and a 4 KiB copy on the first write to each page, and for a process that forks and then writes widely, deferred is not the same as cheaper."
- **References:**
  - `man 2 fork` and `man 2 clone` — the interface and the exact list of what is and is not inherited, which is longer than anyone remembers.
  - `<Src file="kernel/fork.c" symbol="copy_process" />` — the whole of fork in one readable function, with each `copy_*` helper named.
  - `man 3 posix_spawn` — the interface that exists because `fork` + `exec` is a bad primitive for spawning a program.
  - LWN, *"Fork, threads, and the perils of mixing them"*-style coverage of async-signal-safety after fork; cite a specific article and note its date relative to v6.18.

### `exec-and-binary-formats.md` — `exec()` and Binary Formats **[WAH]** **[Misc]**

- **Opens with:** the complement to fork. Where fork duplicates everything and changes nothing, exec keeps the `task_struct` and destroys everything it points at — a new address space, a new set of mappings, a reset signal disposition — and then jumps to an entry point that was, until a moment ago, a file on disk. The task survives; the program does not.
- **Sections:**
  - `## What survives an exec` — the PID and TGID, the parent relationship, open file descriptors without `FD_CLOEXEC`, the working directory, and the credentials unless the binary is setuid. A table, because this list is what everyone gets wrong.
  - `## What is destroyed` — the entire address space, all memory mappings, all signal handlers (reset to default, though the *mask* survives), threads other than the caller, and any pending timers. Say that the thread destruction is why exec in a threaded program is a synchronisation event.
  - `## `binfmt` handlers` — the kernel does not know what an ELF file is; it asks a chain of registered handlers. `binfmt_elf`, `binfmt_script` for `#!`, `binfmt_misc` for anything registered by user space (Java, Wasm, qemu-user for foreign binaries). Explain that `#!` is a *binary format*, which is the fact that makes shebang handling comprehensible.
  - `## What actually happens` **[WAH]** — running `./hello`, a dynamically linked C program. Open the file, read the first bytes, match `\x7fELF`, `load_elf_binary` maps the `PT_LOAD` segments at their requested addresses, reads `PT_INTERP` and maps the dynamic linker too, then jumps to the *linker's* entry point, not the program's. The linker maps libraries, resolves relocations, and only then calls `_start`. Show the `strace` output of a trivial program and count the `openat`/`mmap` pairs before `main` runs. The punchline: `exec` puts *two* programs in your address space and runs the wrong one first.
  - `## The `#!` line, precisely` — the interpreter path is not tokenised the way people expect (one optional argument on most systems, length-limited), and the script path is passed as an argument. This is a small section with a big footprint in shell debugging.
  - `## setuid and exec` — the only point in a process's life where credentials change without a syscall asking. Two sentences, then link to `./credentials-and-identity.md`.
  - `## Why exec never returns` — the address space containing the return address is gone. On failure it returns; on success there is nothing to return to.
  - `## Misconceptions` **[Misc]** — (1) "exec creates a new process" — it replaces the program in the existing one, and the PID is unchanged; (2) "the kernel runs the dynamic linker" — the kernel *maps* it and jumps to it, and everything after that is user space; (3) "`#!/usr/bin/env python` is a shell feature" — it is a kernel binary-format handler.
- **Anchor:** a Mermaid `flowchart TB` from `execve` through the binfmt search, `load_elf_binary`, the segment mappings, `PT_INTERP`, and the jump to the interpreter, with the fall-through to `binfmt_script` drawn as a side branch. Caption: "One `execve`, from a path on disk to the dynamic linker's first instruction."
- **KernelFacts:** `structure` — `[["struct linux_binprm", "include/linux/binfmts.h"], ["struct linux_binfmt", "include/linux/binfmts.h"]]`; `path` — `"execve() → do_execveat_common() → bprm_execve() → search_binary_handler() → load_elf_binary() → start_thread()"` (verify each at v6.18); `observe` — `strace -e trace=execve,openat,mmap ./hello 2>&1 | head -20`; `trap` — "`exec` does not start your program. It starts the dynamic linker, which starts your program — which is why `LD_PRELOAD` works, why a missing shared library reports 'No such file or directory' for a file that plainly exists, and why static binaries behave differently for reasons that have nothing to do with performance."
- **References:**
  - `man 2 execve` — the definitive list of what is preserved and what is reset; longer and more surprising than expected.
  - `<Src file="fs/binfmt_elf.c" symbol="load_elf_binary" />` — the ELF loader, readable end to end, with the `PT_INTERP` handling visible.
  - `https://docs.kernel.org/admin-guide/binfmt-misc.html` — how user space registers a new executable format, and the interface containers and emulators use.
  - `man 8 ld.so` — the interpreter's own documentation, including the search order and the environment variables that change it.

- [ ] **Step 1: Write `fork-and-copy-on-write.md`** to the brief above.
- [ ] **Step 2: Write `exec-and-binary-formats.md`** to the brief above.
- [ ] **Step 3: Write and run the COW lab program**, and paste real fault counts. Run it twice — once with THP enabled and once with `THP=never` — and use whichever produces the clearer teaching output, saying which you used.
- [ ] **Step 4: Verify** `copy_mm`, `dup_mmap`, `do_wp_page`, `bprm_execve`, `search_binary_handler`, `load_elf_binary`, `linux_binprm` against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/06-processes-and-threads
git commit -m "docs: write fork with copy-on-write, and exec with binary formats"
```

---

## Task 11: Folder 06 — the address space, and credentials

**Files:**
- Modify: `docs/linux/06-processes-and-threads/the-process-address-space.md`
- Modify: `docs/linux/06-processes-and-threads/credentials-and-identity.md`

**Interfaces:**
- Consumes: `06/task-struct-the-anatomy-of-a-task` (Task 9).
- Produces: `06/the-process-address-space`, the declared prerequisite of `08/the-virtual-address-space` and of `06/pipes-fifos-and-unix-sockets`. **This page owns the user-facing view; folder 08 owns the mechanism** — keep the boundary sharp or the two pages will duplicate each other.

### `the-process-address-space.md` — A Process's Address Space **[WAH]** **[Lab host=any-linux]**

- **Opens with:** what a process can actually see. Every address a program uses is invented — the same numeric address in two processes refers to different memory, and roughly half the address range is reserved for a kernel the process may never touch. This page is the map; folder 08 is the machinery that maintains it.
- **Sections:**
  - `## The regions` — text, rodata, data, bss, heap, the mmap region, thread stacks, the main stack, `[vdso]`, `[vvar]`, and the kernel half. A table with what each holds, its permissions, and where it comes from (the ELF file, `brk`, `mmap`, or the kernel).
  - `## Reading `/proc/PID/maps` line by line` — take one real `maps` file in a ` ```text ` block and annotate every column: address range, permissions with the private/shared bit, file offset, device, inode, path. Point out the anonymous regions with no path and the `[heap]`/`[stack]` labels.
  - `## What actually happens` **[WAH]** — when `malloc(32)` and `malloc(64 * 1024 * 1024)` are called. The small one comes from an existing arena and may involve no syscall at all; the large one goes to `mmap` with a fresh anonymous region and *still* has no physical memory behind it until touched. Show `strace` of both, and `maps` before and after. The lesson: allocation is a promise, and the address space is a bookkeeping structure, not memory.
  - `## Private versus shared, and file-backed versus anonymous` — the two-by-two that explains most of `maps`. Give one real example of each cell: program text (private, file-backed), a heap page (private, anonymous), a `MAP_SHARED` mapping of a file, and a `MAP_SHARED|MAP_ANONYMOUS` region between a parent and child.
  - `## The stack, and why it grows` — a guard gap, the `MAP_GROWSDOWN` region, `RLIMIT_STACK`, and per-thread stacks being ordinary `mmap` regions rather than special ones. Note that the main thread's stack is the only one that grows.
  - `## Where the kernel half is, and why you cannot see it` — the canonical hole, the user/kernel split, and the fact that `maps` shows nothing above it because there is nothing there *for this process*. Link to `../08-memory-management/the-virtual-address-space.md` for the layout.
  - `## `smaps`, briefly` — the per-region detail (`Rss`, `Pss`, `Private_Dirty`, `Swap`) that the measurement page in folder 08 builds on. Name the fields, defer the interpretation.
  - `<Lab host="any-linux" title="Read your own address space" time="15 min">` — (1) `cat /proc/self/maps`; (2) run a program that mmaps 1 GiB and print `maps` before and after; (3) touch one page of it and compare `grep -A2 <addr> /proc/self/smaps` for `Rss`; (4) `cat /proc/self/smaps_rollup` for the totals. Expected output shown for each. "If it fails": `smaps_rollup` needs a reasonably modern kernel, and reading another process's `smaps` requires matching credentials or `CAP_SYS_PTRACE`.
- **Anchor:** a Mermaid `flowchart TB` of the address-space layout, top to bottom, with the kernel half, the gap, the stack, the mmap region growing down, the heap growing up, and the ELF segments — annotated with which are file-backed. Caption: "One x86-64 process's address space, with the direction each region grows and where each region came from."
- **KernelFacts:** `structure` — `[["struct mm_struct", "include/linux/mm_types.h"], ["struct vm_area_struct", "include/linux/mm_types.h"]]`; `path` — `"malloc() → brk() or mmap() → new VMA in mm->mm_mt → no physical page until first touch"`; `observe` — `cat /proc/self/maps && cat /proc/self/smaps_rollup`; `trap` — "The address space is a set of promises, not memory. A 1 GB mapping in `maps` may be backed by zero physical pages, which is why VSZ tells you nothing about memory use."
- **References:**
  - `man 5 proc`, the `/proc/PID/maps` and `smaps` sections — the field-by-field authority for everything on this page.
  - `man 2 mmap` — the flag combinations behind every line in `maps`, especially `MAP_PRIVATE` versus `MAP_SHARED`.
  - `https://docs.kernel.org/filesystems/proc.html` — the kernel's own `/proc` documentation, including `smaps` fields; check which fields exist at v6.18 before naming them.
  - `<Src file="fs/proc/task_mmu.c" symbol="show_map_vma" />` — the code that generates the file you are reading, which is the point folder 06's `/proc` page makes; verify the symbol name at v6.18.

### `credentials-and-identity.md` — Credentials and Identity

- **Opens with:** the observation that a task's identity is not one number. There are four user IDs, four group IDs, a supplementary group list, and a capability set, and they exist as separate fields because privilege has to be droppable, restorable, and checkable at different moments in a program's life.
- **Sections:**
  - `## `struct cred`, and why it is a separate object` — refcounted, immutable once published, and replaced rather than modified. This is the pattern folder 04's reference-counting page described; link back rather than re-derive.
  - `## The four IDs` — real, effective, saved-set, and filesystem UID, each with what it is for and when it changes. A table with a row per ID and columns for "who you are", "what is checked", "what you can return to", and "when it matters". The filesystem UID row should say plainly that it is a Linux-specific historical artefact (NFS servers) that survives because of the ABI promise.
  - `## Transitions` — how `setuid`/`seteuid`/`setresuid` move these around, what a setuid binary does at exec, and the classic mistake: dropping the effective UID but not the saved one, so the program can restore privilege and an exploit can too. State the correct order for a permanent drop (groups first, then GID, then UID) and why groups must go first.
  - `## Supplementary groups` — the list, `NGROUPS_MAX`, and the check order. Brief.
  - `## Capabilities, in one paragraph` — root split into pieces, with the detail deferred to folder 16 in prose, no link.
  - `## RCU-protected credentials` — reading a task's credentials is a hot, lock-free operation; changing them replaces the whole object and defers freeing. Name the pattern and link to `../09-concurrency-and-locking/rcu-the-idea.md`, which is in this phase.
  - `## How a check actually happens` — walk one permission check end to end: an `open` on a file, `inode_permission`, the owner/group/other test against the *filesystem* UID, then the LSM hook. Enough that the reader knows there are two layers and folder 16 owns the second.
- **Anchor:** a table of the four UIDs against four scenarios — a normal program, a setuid-root program before dropping, the same after a temporary drop, and after a permanent drop — showing all four values in each state. This table is the page; it is the thing readers come back for.
- **KernelFacts:** `structure` — `[["struct cred", "include/linux/cred.h"]]`; `path` — `"setresuid() → prepare_creds() → modify the copy → commit_creds() → old cred released by RCU"`; `observe` — `grep -E '^(Uid|Gid|Groups|CapEff):' /proc/self/status`; `trap` — "Dropping the effective UID is not dropping privilege. Until the saved set-user-ID is also changed, the process — and anything that hijacks it — can take the privilege back with one call."
- **References:**
  - `https://docs.kernel.org/security/credentials.html` — the kernel's own credentials documentation, including the RCU rules and the "never modify in place" requirement.
  - `man 7 credentials` — the user-space model, the four IDs, and the transition rules in one place.
  - `man 2 setresuid` — the call that makes a permanent drop expressible, and the reason `setuid()` alone is ambiguous.
  - Chen, Wagner & Dean, *"Setuid Demystified"*, USENIX Security 2002 — `https://people.eecs.berkeley.edu/~daw/papers/setuid-usenix02.pdf`. The paper that documented how badly these semantics are understood; still the clearest account of the transition rules.

- [ ] **Step 1: Write `the-process-address-space.md`** to the brief above.
- [ ] **Step 2: Write `credentials-and-identity.md`** to the brief above.
- [ ] **Step 3: Check the folder-08 boundary.** Re-read the manifest summaries for `08/the-virtual-address-space` and `08/mm-struct-and-vmas` and confirm this page explains no page-table or VMA-tree mechanism. If it does, cut it — folder 08 owns it.
- [ ] **Step 4: Verify** `cred`, `prepare_creds`, `commit_creds`, `mm_struct`, `vm_area_struct`, and the `task_mmu.c` symbol against Elixir v6.18. Run every lab command and paste real output.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/06-processes-and-threads
git commit -m "docs: write the process address space and the credential model"
```

---

## Task 12: Folder 06 — states, exit, and signals

**Files:**
- Modify: `docs/linux/06-processes-and-threads/process-states-and-wait-queues.md`
- Modify: `docs/linux/06-processes-and-threads/exit-zombies-and-orphans.md`
- Modify: `docs/linux/06-processes-and-threads/signals.md`

**Interfaces:**
- Consumes: `06/task-struct-the-anatomy-of-a-task` (Task 9).
- Produces: `06/process-states-and-wait-queues`, the declared prerequisite of `07/what-the-scheduler-must-decide` and of the two other pages in this task. The state machine defined here is referenced by folder 07 and folder 10 rather than redrawn.

### `process-states-and-wait-queues.md` — Process States and Wait Queues **[WAH]** **[Misc]**

- **Opens with:** the fact that "running" is the rarest state a task is in. Most tasks, most of the time, are waiting for something, and the kernel's central scaling trick is that a waiting task costs nothing — it is not polled, not checked, and not scheduled. The wait queue is how a task arranges to be forgotten and then remembered at exactly the right moment.
- **Sections:**
  - `## The states` — `TASK_RUNNING` (which means runnable, not running — say this early and clearly), `TASK_INTERRUPTIBLE`, `TASK_UNINTERRUPTIBLE`, `TASK_KILLABLE`, `__TASK_STOPPED`, `__TASK_TRACED`, and the exit states `EXIT_ZOMBIE`/`EXIT_DEAD`. A table mapping each to the letter `ps` shows.
  - `## Wait queues` — a list of waiters attached to whatever they wait for, with a wake function per entry. The five-step sleeping pattern in ` ```c `: add yourself to the queue, set your state, **re-check the condition**, call `schedule()`, remove yourself. Explain why the re-check is not optional — the lost-wakeup race — because that is the part every first implementation gets wrong.
  - `## What actually happens` **[WAH]** — when a process blocks on `read()` of an empty pipe. It joins the pipe's wait queue, sets `TASK_INTERRUPTIBLE`, calls `schedule()`, and stops existing as far as the CPU is concerned. A writer later calls `wake_up_interruptible`, which sets the waiter back to `TASK_RUNNING` and puts it on a runqueue; the reader resumes *inside* `schedule()` and re-checks. Point out that the reader's CPU time in this whole story is a few microseconds regardless of whether it waited a millisecond or an hour.
  - `## Interruptible versus uninterruptible` — the difference is whether a signal may end the wait. Uninterruptible exists because some waits cannot be safely unwound mid-flight (a driver holding device state, a filesystem mid-transaction). `TASK_KILLABLE` is the compromise: uninterruptible except for a fatal signal, and it exists because too much code chose uninterruptible out of caution.
  - `## Why a `D`-state process cannot be killed` — it is not ignoring you; the signal is delivered but never acted on, because delivery happens on the return to user space and the task is not returning. The correct diagnosis is to find what it is waiting on: `cat /proc/PID/stack` (with `CONFIG_STACKTRACE`) and `/proc/PID/wchan`. State that a persistent `D` almost always means a device or a filesystem, not a bug in the process.
  - `## Load average counts these` — `TASK_UNINTERRUPTIBLE` tasks are included in the load average, which is why a machine with an unresponsive NFS mount shows a load of 40 and an idle CPU. Say this here; the observability folder will use it later.
  - `## Misconceptions` **[Misc]** — (1) "`TASK_RUNNING` means the task is on a CPU" — it means runnable; (2) "a `D` state process is stuck in the kernel and hung" — it is waiting, usually correctly, and the interesting question is on what; (3) "load average measures CPU usage" — it counts runnable *and* uninterruptible tasks, which is why it and CPU utilisation can diverge completely.
- **Anchor:** a Mermaid `stateDiagram-v2` of the task states with labelled transitions — wake-up, preemption, blocking on a wait queue, signal-stop, exit, and reaping. Caption: "Every state a task can be in, and the event that moves it — with `TASK_RUNNING` covering both 'on a CPU' and 'waiting for one'."
- **KernelFacts:** `structure` — `[["struct wait_queue_head", "include/linux/wait.h"], ["struct task_struct", "include/linux/sched.h"]]`; `path` — `"read() → no data → prepare_to_wait_event() → schedule() → wake_up_interruptible() → try_to_wake_up() → runqueue"`; `observe` — `ps -eo pid,stat,wchan:30,comm | head -20`; `trap` — "A task in `D` state is not ignoring signals; it never reaches the point where signals are acted on. Delivery happens on the return to user space, and an uninterruptible sleep is precisely a promise not to return until the wait completes."
- **References:**
  - `<Src file="include/linux/wait.h" symbol="wait_event_interruptible" />` — the macro that encodes the correct sleeping pattern, and reading its expansion is the fastest way to internalise the lost-wakeup problem.
  - `https://docs.kernel.org/scheduler/sched-domains.html` and the scheduler index — for the runqueue side, which folder 07 owns.
  - `man 1 ps`, the process-state codes section — the letter-to-state mapping readers will actually use.
  - Love, *Linux Kernel Development*, 3rd ed., ch. 4 — the classic treatment of wait queues; predates v6.18 and the API names have shifted, so check each against the source before citing a name from it.

### `exit-zombies-and-orphans.md` — Exit, Zombies, and Orphans **[WAH]** **[Misc]**

- **Opens with:** the constraint that makes zombies necessary. A process's exit status has to survive the process, because the parent has the right to ask for it and has not asked yet. So the kernel keeps a corpse: no memory, no address space, no file descriptors — just enough `task_struct` to answer one question.
- **Sections:**
  - `## What `exit()` releases immediately` — the address space, the file descriptors, the timers, the shared-memory attachments, and the kernel stack (mostly). Give the ordering, because it is why a process can be in `Z` state while its memory is already fully reclaimed.
  - `## What it cannot release` — the `task_struct`, the PID, and the exit status, which are held until the parent reaps. State the size honestly — a zombie costs a few kilobytes and a PID slot, not memory in any interesting quantity — and then say why thousands of them are still a real problem: the PID space is finite and `fork` starts failing.
  - `## What actually happens` **[WAH]** — when a parent ignores `SIGCHLD` and never calls `wait`. The child exits, becomes `Z`, and stays. Show `ps` output with the `<defunct>` marker. Then show the two correct fixes — reap in a `SIGCHLD` handler, or set `SIGCHLD` to `SIG_IGN` explicitly, which is a documented instruction to the kernel to auto-reap — and the fix that does not work, which is killing the zombie. Say it plainly: you cannot kill a process that has already exited.
  - `## Reparenting` — when a parent dies first, its children are reparented, historically to PID 1 and now to the nearest ancestor marked `PR_SET_CHILD_SUBREAPER`, or to PID 1 if there is none. Explain why subreapers exist (session managers and container runtimes want their own orphans) and note that this is the mechanism a container's init depends on.
  - `## Why PID 1 must reap` — the duty inherited with the orphans. A PID 1 that does not reap accumulates every orphan on the system, which is exactly the bug people meet when they run an application directly as a container's PID 1. Prose forward-reference to folder 15; no link.
  - `## Orphaned process groups and `SIGHUP`` — one short section, because it explains why background jobs die when a terminal closes and why `nohup` and `setsid` work.
  - `## Misconceptions` **[Misc]** — (1) "zombies leak memory" — they hold a PID and a small struct, and the problem is PID exhaustion; (2) "you can `kill -9` a zombie" — there is nothing left to signal; signal the *parent* to make it reap; (3) "orphans become zombies" — orphans are reparented and reaped promptly, which is the opposite problem.
- **Anchor:** a Mermaid `stateDiagram-v2` from `TASK_RUNNING` through `do_exit`, `EXIT_ZOMBIE`, the parent's `wait`, and `EXIT_DEAD`, with a branch for reparenting when the parent exits first. Caption: "The two ways a task's remains are cleaned up: the parent asks, or the parent dies and someone else inherits the duty."
- **KernelFacts:** `structure` — `[["struct task_struct", "include/linux/sched.h"], ["struct pid", "include/linux/pid.h"]]`; `path` — `"exit_group() → do_exit() → exit_mm() → exit_files() → exit_notify() → EXIT_ZOMBIE → parent wait4() → release_task()"`; `observe` — `ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/'`; `trap` — "A zombie is not a stuck process, it is a receipt. The bug is always in the parent, and the fix is always in the parent."
- **References:**
  - `man 2 wait` — the reaping interface, including the `SIGCHLD`-to-`SIG_IGN` auto-reap behaviour that is Linux-specific and rarely known.
  - `man 2 prctl`, the `PR_SET_CHILD_SUBREAPER` section — the mechanism that made container inits possible.
  - `<Src file="kernel/exit.c" symbol="do_exit" />` — the release order, in the order it happens.
  - `man 7 credentials` and `man 2 setsid` — for the process-group and `SIGHUP` section.

### `signals.md` — Signals **[WAH]** **[Misc]**

- **Opens with:** the honest framing — signals are the oldest asynchronous notification mechanism in UNIX, they predate threads and predate almost everything else in this section, and their semantics are shaped entirely by that history. Understanding them means understanding that a signal is not a message and not an interrupt: it is a bit set in a task's pending mask, acted on later.
- **Sections:**
  - `## Generation, pending, delivery` — three distinct moments, and conflating them is the source of every signal misconception. Generation sets a bit; the signal is pending until the task is about to return to user space; delivery is when the handler actually runs.
  - `## What actually happens` **[WAH]** — when you press Ctrl-C. The terminal driver's line discipline recognises the character, sends `SIGINT` to the foreground process *group*, each task's pending set gets a bit, and nothing else happens until each task next returns to user space. Say what follows from this: a task spinning in a tight kernel loop does not react, a task in `D` state does not react, and a task on another CPU reacts as soon as it takes an interrupt. Then show `strace` of the delivery.
  - `## Building a handler frame` — the kernel writes a signal frame onto the *user* stack (or the alternate signal stack, if `sigaltstack` was used), points the return address at a trampoline, and returns to user space at the handler. The handler runs at user privilege. When it returns, it calls `rt_sigreturn`, which is a syscall whose whole job is to restore the saved context. Note the security consequence: the frame is on a stack the user controls, which is why `rt_sigreturn` validates and why sigreturn-oriented programming is a known technique.
  - `## Standard versus real-time signals` — standard signals do not queue (a second `SIGUSR1` while one is pending is lost) and have no ordering; real-time signals queue, carry a value, and are delivered in order. Give the practical rule: if you are counting events, standard signals will lose some.
  - `## Blocking, and what cannot be blocked` — the signal mask, `sigprocmask`, per-thread masks, and the two signals that cannot be caught or blocked (`SIGKILL`, `SIGSTOP`). Note that the mask is per-*task*, so which thread of a process receives a process-directed signal is any thread that has not blocked it.
  - `## Async-signal-safety` — the short, sharp version: a handler interrupts arbitrary code, so calling anything that takes a lock the interrupted code might hold is a deadlock waiting to happen. `man 7 signal-safety` has the list; the practical patterns are setting a `volatile sig_atomic_t`, writing to a self-pipe, or using `signalfd`.
  - `## The modern alternatives` — `signalfd`, `pidfd_send_signal`, and `pidfd_open`, each in a sentence: they turn signals into file descriptors and PIDs into stable references, which removes both the async-safety problem and the PID-reuse race.
  - `## Misconceptions` **[Misc]** — (1) "a signal interrupts the process immediately" — it is delivered when the target next returns to user space, which may be never; (2) "signals queue" — standard signals do not, so counting them is wrong; (3) "`kill -9` always works instantly" — `SIGKILL` cannot be blocked, but it still cannot act on a task that is in uninterruptible sleep.
- **Anchor:** a Mermaid `sequenceDiagram` — Sender, Kernel, Target task, Handler — showing the pending bit being set, the target continuing to run, the return-to-user-space check, the frame being built on the user stack, the handler running, and `rt_sigreturn` restoring. Caption: "A signal from `kill()` to the handler: three separate moments, only one of which is under the sender's control."
- **KernelFacts:** `structure` — `[["struct sigpending", "include/linux/signal_types.h"], ["struct k_sigaction", "include/linux/signal_types.h"]]`; `path` — `"kill() → send_signal_locked() → set bit in task->pending → syscall exit work → get_signal() → setup_rt_frame() → handler → rt_sigreturn()"` (verify each name at v6.18); `observe` — `cat /proc/self/status | grep -E 'Sig(Pnd|Blk|Ign|Cgt)'` with the masks decoded in the page; `trap` — "Signals are delivered on the return to user space, not when they are sent. A process that never returns to user space never sees them, which is why `SIGKILL` does not free a task stuck in an uninterruptible wait."
- **References:**
  - `man 7 signal` — the master reference: the disposition table, the restart rules, and the standard-versus-real-time distinction.
  - `man 7 signal-safety` — the list of functions a handler may call, which is shorter than anyone expects.
  - `<Src file="kernel/signal.c" symbol="get_signal" />` — the delivery decision point, where blocked, ignored, and fatal are separated.
  - `man 2 signalfd` and `man 2 pidfd_send_signal` — the modern interfaces, and why they exist.

- [ ] **Step 1: Write `process-states-and-wait-queues.md`** to the brief above.
- [ ] **Step 2: Write `exit-zombies-and-orphans.md`** to the brief above.
- [ ] **Step 3: Write `signals.md`** to the brief above.
- [ ] **Step 4: Verify** `wait_event_interruptible`, `prepare_to_wait_event`, `try_to_wake_up`, `do_exit`, `exit_notify`, `release_task`, `get_signal`, `setup_rt_frame`, `sigpending`, and the exact `TASK_*` constant names against Elixir v6.18.
- [ ] **Step 5: Produce the `Z`-state and `D`-state output for real** — a two-line C program produces a zombie; `D` state is easiest to show honestly by describing an observed case rather than manufacturing one. Do not invent `ps` output.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/06-processes-and-threads
git commit -m "docs: write task states, exit and zombies, and signals"
```

---

## Task 13: Folder 06 — IPC, `/proc`, and the birth lab

**Files:**
- Modify: `docs/linux/06-processes-and-threads/pipes-fifos-and-unix-sockets.md`
- Modify: `docs/linux/06-processes-and-threads/proc-as-the-process-interface.md`
- Modify: `docs/linux/06-processes-and-threads/lab-watching-a-process-be-born.md`

**Interfaces:**
- Consumes: everything earlier in folder 06.
- Produces: the folder's completion. `06/proc-as-the-process-interface` is the page folder 08's measurement page and folder 07's diagnostics page both assume.

### `pipes-fifos-and-unix-sockets.md` — Pipes, FIFOs, and UNIX Sockets

- **Opens with:** the observation that the IPC people actually use is not the IPC textbooks teach. System V message queues and semaphores exist; almost nothing reaches for them. Shell pipelines, socket pairs, and UNIX-domain sockets carry essentially all local IPC on a modern Linux system, and all three are the same idea with different framing.
- **Sections:**
  - `## A pipe is a ring of pages` — not a byte stream in a buffer: a circular array of page-sized buffers with a head and tail, default 16 pages (64 KiB), adjustable with `fcntl(F_SETPIPE_SZ)` up to `/proc/sys/fs/pipe-max-size`. This structure is why `splice` is possible.
  - `## Blocking, `PIPE_BUF`, and atomicity` — writes up to `PIPE_BUF` (4096) are atomic with respect to other writers; beyond that they may interleave. This is the fact that makes concurrent logging to one pipe safe or unsafe, and it is worth a sentence on why the number is what it is.
  - `## `SIGPIPE`, and the error nobody expects` — writing to a pipe with no reader kills your process by default. Say it plainly, because it is the single most common surprise in this area, and give the two responses (`signal(SIGPIPE, SIG_IGN)` then check `EPIPE`, or `send(MSG_NOSIGNAL)` on a socket).
  - `## FIFOs` — the same object with a name in the filesystem, and the open-blocks-until-both-ends-are-present semantics that surprise people writing shell scripts.
  - `## `splice`, `tee`, and zero copy` — moving pages between a pipe and a file descriptor without copying through user space, which works precisely because a pipe is already a set of page references. Give the honest limit: it avoids the copy to and from user space, not every copy, and the win is real for large transfers and negligible for small ones.
  - `## UNIX-domain sockets` — the same address family the socket API uses, but with no protocol stack: `SOCK_STREAM` and `SOCK_DGRAM` and `SOCK_SEQPACKET`, credentials passing (`SO_PEERCRED`), and abstract-namespace addresses. Say why almost every local service (D-Bus, container runtimes, database sockets) uses these rather than TCP on loopback: no protocol overhead, filesystem permissions as access control, and credential passing.
  - `## Passing a file descriptor` — `SCM_RIGHTS` ancillary data, what actually gets transferred (a reference to the same `struct file`, not a copy and not a number), and the systems that depend on it: `systemd` socket activation, container runtimes, and privilege-separated daemons. This is the section that makes the page worth reading for someone who already knows pipes.
  - `## What about System V IPC` — one paragraph: it exists, it has a separate namespace and a separate lifetime model (`ipcs`, `ipcrm`), it is why `CLONE_NEWIPC` exists, and new code should not use it. POSIX message queues get a sentence.
- **Anchor:** a Mermaid `flowchart LR` of a pipe as a ring of page buffers with a writer filling and a reader draining, and a second lane showing `splice` moving page references between a file and the pipe with no user-space copy. Caption: "A pipe is a ring of pages, which is why `splice` can move data through it without copying it."
- **KernelFacts:** `structure` — `[["struct pipe_inode_info", "include/linux/pipe_fs_i.h"], ["struct unix_sock", "include/net/af_unix.h"]]`; `path` — `"write() → pipe_write() → copy into a ring buffer page → wake readers → pipe_read()"`; `observe` — `ls -l /proc/self/fd && ss -xp | head`; `trap` — "Writing to a pipe whose reader has closed does not return an error by default — it kills your process with `SIGPIPE`. Every long-running program that writes to a pipe must decide about this explicitly."
- **References:**
  - `man 7 pipe` — the buffer size, the `PIPE_BUF` atomicity guarantee, and the blocking rules.
  - `man 7 unix` — the address forms, `SCM_RIGHTS`, and `SO_PEERCRED`, with worked examples.
  - `man 2 splice` — the zero-copy interface and its honest constraints (one end must be a pipe).
  - `<Src file="fs/pipe.c" symbol="pipe_write" />` — the ring buffer and the wakeup, in one function.

### `proc-as-the-process-interface.md` — `/proc` as the Process Interface **[WAH]** **[Misc]**

- **Opens with:** the reframing the page exists for — `/proc` is not a directory of files. Nothing there is stored, nothing is on a disk, and the "file" you `cat` is generated at the moment you read it by kernel code walking live structures. Once that lands, most `/proc` oddities stop being odd.
- **Sections:**
  - `## Generated on read` — the `seq_file` interface, a `show` function per entry, and the consequence that a read is a snapshot of a moving target. Say explicitly that reading two lines of `/proc/PID/status` is not an atomic view of the process.
  - `## What actually happens` **[WAH]** — when you run `cat /proc/self/status`. `open` finds a `proc_dir_entry`, the read calls into `proc_pid_status`, which walks `task_struct`, `mm_struct`, and `cred` and formats text into a buffer. Nothing was stored; the file's size is zero until you read it. Show `ls -l /proc/self/status` reporting size 0 and `wc -c` reporting several kilobytes, which is the demonstration that makes the point better than any explanation.
  - `## The per-process entries worth knowing` — a table: `status`, `stat`, `cmdline`, `environ`, `maps`, `smaps`, `smaps_rollup`, `fd/`, `fdinfo/`, `task/`, `wchan`, `stack`, `limits`, `mountinfo`, `ns/`, `oom_score_adj`. Each with what it exposes and which `task_struct` field family it renders. Note which require privilege.
  - `## Why some reads block` — `/proc/PID/stack` needs the task to be stopped or its stack to be walkable, `/proc/PID/mem` needs ptrace-level access, and a read that takes a lock a busy subsystem holds can wait. This is the answer to "why did `cat` hang".
  - `## Stability` — `/proc` is user-space ABI: fields are added at the end, never removed or reordered. That is why `/proc/PID/stat` has fifty-odd positional fields and cannot be tidied, and why `status` (key: value) is the one to parse. Give the practical rule: parse by key, never by column index.
  - `## System-wide entries, briefly` — `/proc/meminfo`, `/proc/stat`, `/proc/interrupts`, `/proc/cmdline`, `/proc/sys`. Name them and point at the folders that own each; `/proc/interrupts` links to folder 10 and `/proc/meminfo` to folder 08, both of which exist in this phase.
  - `## `/proc` versus `/sys`` — one paragraph: `/proc` is process state plus historical accumulation, `/sys` is the device model rendered as a tree with one value per file. Link back to `../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md`.
  - `## Misconceptions` **[Misc]** — (1) "`/proc` files are zero bytes so they are empty" — the size is meaningless because the content does not exist until read; (2) "reading `/proc` is free" — some entries walk every VMA or take a lock, and `smaps` on a large process is genuinely expensive; (3) "`/proc/PID/environ` shows the current environment" — it shows the region set at exec, which a program that modified its own environment may have moved.
- **Anchor:** a Mermaid `sequenceDiagram` — `cat`, VFS, procfs, `task_struct` — showing that the read triggers a `show` callback that formats live fields into a buffer, with nothing persisted anywhere. Caption: "`cat /proc/self/status`: the file's contents are computed during your `read()` and discarded afterwards."
- **KernelFacts:** `structure` — `[["struct proc_dir_entry", "fs/proc/internal.h"], ["struct seq_file", "include/linux/seq_file.h"]]`; `path` — `"read() → proc_reg_read_iter() → seq_read_iter() → proc_pid_status() → task_struct fields → formatted text"` (verify at v6.18); `observe` — `ls -l /proc/self/status && wc -c /proc/self/status`; `trap` — "Nothing in `/proc` exists until you read it. A file that reports zero bytes and returns four kilobytes is not a bug, and a value you read twice may legitimately disagree with itself."
- **References:**
  - `man 5 proc` — the field-by-field reference for every entry named on this page; long, and the only complete one.
  - `https://docs.kernel.org/filesystems/proc.html` — the kernel's own documentation, including the stability rules for adding fields.
  - `<Src file="fs/proc/array.c" symbol="proc_pid_status" />` — the function that generates the file, and the clearest possible evidence for the page's thesis.
  - `https://docs.kernel.org/filesystems/seq_file.html` — the interface every `/proc` file is written against.

### `lab-watching-a-process-be-born.md` — Lab: Watch a Process Be Born **[Lab host=qemu]**

- **Opens with:** the value of triangulation — the same event seen from three tools tells you what each tool can and cannot see, which is worth more than any one of them showing you the event. This lab watches one `fork` + `exec` from a tracepoint, from `perf`, and from a breakpoint in the kernel.
- **Sections:**
  - `## The event` — one shell running one command, which is a `clone` followed by an `execve` followed by a `wait4` in the parent. Draw it once so the three views have something to be views *of*.
  - `<Lab host="qemu" title="One fork and exec, three ways" time="30 min">`:
    1. **Tracepoints, by hand.** Mount `tracefs` if needed, enable `sched:sched_process_fork` and `sched:sched_process_exec`, run a command in another shell, read `trace`. Show the two real lines. This is the version with no tooling at all and it works everywhere.
    2. **`perf trace`.** `perf trace -e clone,execve -- sh -c 'ls >/dev/null'`. Show the output, and point at the argument decoding tracepoints alone do not give you.
    3. **GDB in the QEMU lab.** Break on `kernel_clone`, run a command in the guest, and at the breakpoint print the parent's `comm` and the `clone_flags` argument. Then `finish` and observe the returned PID. Show the session as a ` ```text ` block.
    - Expected output for all three, and a closing comparison table: what each saw, what each cost, and whether it needed root.
    - "If it fails": tracepoint names differ slightly between kernels (`perf list 'sched:*'` is the authority), and the GDB breakpoint needs `CONFIG_DEBUG_INFO` plus the exact symbol name for v6.18 — if `kernel_clone` does not resolve, find the current name via `/proc/kallsyms` rather than guessing.
  - `## What the three views disagree about` — the closing section and the real lesson: the tracepoint fires inside the kernel at a fixed point, `perf trace` sees the syscall boundary, and GDB sees the function call — three different moments in the same event, which is why timestamps from different tools should never be compared naively.
- **Anchor:** the comparison table above, plus a Mermaid `sequenceDiagram` marking where each of the three tools observes on a single timeline from `clone` to the child's first user instruction. Caption: "Three observation points on one process creation, and the interval each of them cannot see."
- **KernelFacts:** `structure` — `[["struct kernel_clone_args", "include/linux/sched/task.h"]]`; `path` — `"clone() → kernel_clone() → copy_process() → wake_up_new_task() → sched_process_fork tracepoint → child returns 0"`; `observe` — `perf trace -e clone,execve -- sh -c 'ls >/dev/null'`; `trap` — "A tracepoint, a syscall tracer, and a debugger breakpoint are three different points in time. If two tools disagree about when a process was created, they are probably both right about different moments."
- **References:**
  - `https://docs.kernel.org/trace/ftrace.html` — the tracefs interface used in step 1, which is the substrate every other tracing tool sits on.
  - `https://man7.org/linux/man-pages/man1/perf-trace.1.html` — the option surface for step 2.
  - `https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html` — the GDB workflow, which folder 01 set up.
  - `<Src file="kernel/fork.c" symbol="kernel_clone" />` — the function the breakpoint lands on, so the reader can see the arguments they are printing.

- [ ] **Step 1: Write `pipes-fifos-and-unix-sockets.md`** to the brief above.
- [ ] **Step 2: Write `proc-as-the-process-interface.md`** to the brief above.
- [ ] **Step 3: Run all three parts of the lab** in the QEMU environment and record real output before writing `lab-watching-a-process-be-born.md`.
- [ ] **Step 4: Write `lab-watching-a-process-be-born.md`** from the recorded output.
- [ ] **Step 5: Verify** `pipe_inode_info`, `pipe_write`, `proc_pid_status`, `seq_file`, `kernel_clone`, `wake_up_new_task`, and the two tracepoint names against Elixir v6.18 and against `perf list` on a real machine.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/06-processes-and-threads
git commit -m "docs: write local IPC, /proc as an interface, and the process-birth lab"
```

---
## Task 14: Folder 07 — what the scheduler decides, runqueues and classes

**Files:**
- Modify: `docs/linux/07-scheduling/what-the-scheduler-must-decide.md`
- Modify: `docs/linux/07-scheduling/runqueues-and-scheduling-classes.md`

**Interfaces:**
- Consumes: `06/process-states-and-wait-queues` (the task state machine — referenced, not redrawn) and `computer-science/operating-systems/scheduling` (algorithmic theory — linked, never re-taught).
- Produces: `07/runqueues-and-scheduling-classes`, the declared prerequisite of five later pages in this folder.

### `what-the-scheduler-must-decide.md` — What the Scheduler Must Decide

- **Opens with:** the reframe that organises the folder. "The scheduler" is not one algorithm answering one question. It answers three: which runnable task should this CPU run next, how long should it run before we reconsider, and which CPU should this task be on at all. They have different inputs, different time scales, and different code, and treating them as one thing is why scheduler documentation is so often confusing.
- **Sections:**
  - `## Three questions, three mechanisms` — a table: the question, the time scale (nanoseconds, milliseconds, tens of milliseconds), the code that answers it (`pick_next_task`, the tick and the slice, the load balancer), and what goes wrong when it answers badly.
  - `## What the scheduler is actually optimising` — throughput, latency, fairness, and power, which conflict. Give the concrete conflict: minimising context switches maximises throughput and maximises latency, and every scheduler on this page is a position on that trade-off.
  - `## What it does not decide` — it does not decide when a task blocks (the task does), it does not decide when a task becomes runnable (a wakeup does), and it does not decide priority policy (`sched_setscheduler` does). Naming the boundary makes the rest of the folder tractable.
  - `## Where the scheduler is entered from` — four places: a task blocks and calls `schedule()` voluntarily, the timer tick decides the current task has had enough, a wakeup preempts, and the return from an interrupt or syscall finds `need_resched` set. Say that only the first is a "call to the scheduler" in the way people imagine.
  - `## Preemption is the whole difficulty` — one paragraph naming what preemption costs (a context switch and its cache effects) against what it buys (bounded latency), and forward-pointing to `./preemption-models.md`.
  - `## What this folder covers, and what CS owns` — the boundary statement: the algorithmic theory of scheduling (round robin, MLFQ, CFS-style fair queueing as a concept, the theory of deadline scheduling) is owned by `../../computer-science/operating-systems/scheduling.md`; this folder owns what Linux actually implements.
- **Anchor:** a Mermaid `flowchart TB` of the four entry points into `schedule()` — voluntary block, tick preemption, wakeup preemption, and the return-to-user check — converging on `pick_next_task`. Caption: "The four events that reach the scheduler, and the one path they all converge on."
- **KernelFacts:** `structure` — `[["struct rq", "kernel/sched/sched.h"], ["struct task_struct", "include/linux/sched.h"]]`; `path` — `"blocking call / tick / wakeup / return-to-user → need_resched → __schedule() → pick_next_task()"`; `observe` — `grep -E 'ctxt|processes|procs_running|procs_blocked' /proc/stat`; `trap` — "There is no scheduler thread. `schedule()` runs in the context of whatever task is giving up the CPU, which is why scheduling cost is charged to the task that was descheduled rather than to a system process you can find in `top`."
- **References:**
  - `https://docs.kernel.org/scheduler/index.html` — the scheduler documentation index at the pinned version, and the entry point for every claim in this folder.
  - `man 7 sched` — the user-visible model: policies, priorities, and the guarantees each policy makes.
  - `<Src file="kernel/sched/core.c" symbol="__schedule" />` — the function all four entry points reach, with comments explaining the preemption cases.
  - `../../computer-science/operating-systems/scheduling.md` — the algorithmic theory this folder deliberately does not repeat.

### `runqueues-and-scheduling-classes.md` — Runqueues and Scheduling Classes

- **Opens with:** the structural answer to "how does one scheduler support real-time tasks, deadline tasks, ordinary tasks, and the idle task at once?" It does not. There are several schedulers, arranged in a strict priority order, and the thing called "the scheduler" is a loop that asks each of them in turn whether it has anything to run.
- **Sections:**
  - `## The per-CPU runqueue` — one `struct rq` per CPU, holding a sub-queue per class plus the bookkeeping (`nr_running`, the clock, the current task). Emphasise that it is per-CPU and lock-protected, and that this is why waking a task on another CPU is a cross-CPU operation rather than a list insertion.
  - `## The class hierarchy` — `stop_sched_class` → `dl_sched_class` → `rt_sched_class` → `fair_sched_class` → `idle_sched_class`, in strict priority order. A table with a row per class: what it schedules, the policy names that map to it (`SCHED_DEADLINE`, `SCHED_FIFO`/`SCHED_RR`, `SCHED_OTHER`/`SCHED_BATCH`/`SCHED_IDLE`), and one line on its selection rule.
  - `## `pick_next_task`, and the fast path` — the loop walks classes in order and takes the first task offered. Note the optimisation that matters for reading the code: if every runnable task is `fair`, the loop is short-circuited, which is why the function looks stranger than the description.
  - `## The class interface` — `struct sched_class` as a vtable: `enqueue_task`, `dequeue_task`, `pick_next_task`, `task_tick`, `select_task_rq`, and a handful more. Point back to `../04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md` for the operations-table idiom, which folder 04 already established.
  - `## Strict priority has consequences` — a runnable `SCHED_FIFO` task starves every fair task on that CPU, indefinitely, by design. State plainly that this is not a bug and that RT throttling exists precisely because it is dangerous; the detail lands in `./real-time-scheduling.md`.
  - `## `sched_ext`, at the pinned version` — BPF-programmable scheduling classes: what it enables, its status at v6.18, and the honest note that it is young. **Verify the status via context7 and date the check**; do not describe it from memory.
  - `## The stop class, briefly` — the highest priority class exists for one purpose: migration and CPU hotplug need to preempt absolutely anything. One paragraph, because otherwise the top of the table is a mystery.
- **Anchor:** a Mermaid `flowchart TB` of `pick_next_task` walking the five classes in order, with a "has a runnable task?" decision at each and the fair-class fast path drawn as the short-circuit edge. Caption: "How the next task is chosen: five schedulers in strict priority order, and the shortcut taken when only one of them has work."
- **KernelFacts:** `structure` — `[["struct rq", "kernel/sched/sched.h"], ["struct sched_class", "kernel/sched/sched.h"]]`; `path` — `"__schedule() → pick_next_task() → stop → dl → rt → fair → idle"`; `observe` — `chrt -p $$ && cat /proc/self/sched | head` (the second requires `CONFIG_SCHED_DEBUG`); `trap` — "The classes are strictly ordered, not weighted. One runnable `SCHED_FIFO` task will run instead of every ordinary task on its CPU for as long as it stays runnable — RT throttling is the only thing that stops a spinning RT task from making a CPU unusable."
- **References:**
  - `<Src file="kernel/sched/sched.h" symbol="sched_class" />` — the vtable, whose member list is the clearest statement of what a scheduling class must implement.
  - `man 7 sched` — the policy-to-class mapping from user space, and the priority ranges each policy accepts.
  - `https://docs.kernel.org/scheduler/sched-ext.html` — the BPF scheduler documentation at the pinned version; state the check date, because this is the fastest-moving thing in the folder.
  - LWN's `sched_ext` coverage — cite the specific article and note its date relative to v6.18.

- [ ] **Step 1: Write `what-the-scheduler-must-decide.md`** to the brief above.
- [ ] **Step 2: Write `runqueues-and-scheduling-classes.md`** to the brief above.
- [ ] **Step 3: context7 check on `sched_ext`** — resolve the library/doc id, query for the current status and interface, and record the check date in the reference annotation. If context7 has no entry, cite `docs.kernel.org` at v6.18 and say so explicitly.
- [ ] **Step 4: Verify** `rq`, `sched_class`, `__schedule`, `pick_next_task`, and the five class symbol names against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/07-scheduling
git commit -m "docs: write the scheduler's three questions, runqueues, and scheduling classes"
```

---

## Task 15: Folder 07 — CFS, and EEVDF

**Files:**
- Modify: `docs/linux/07-scheduling/cfs-and-vruntime.md`
- Modify: `docs/linux/07-scheduling/eevdf.md`

**Interfaces:**
- Consumes: `07/runqueues-and-scheduling-classes` (Task 14).
- Produces: `07/eevdf`, the declared prerequisite of `07/priorities-nice-and-weights` and `07/cgroup-cpu-control`.

**This pair is the folder's currency risk.** EEVDF replaced CFS recently enough that most material online — including a great deal of otherwise excellent writing — describes a scheduler the pinned kernel does not run. The spec singles it out for context7 verification; treat any claim about tunables as unverified until checked.

### `cfs-and-vruntime.md` — CFS and Virtual Runtime

- **Opens with:** why a page about a replaced scheduler is not history for its own sake. CFS ran Linux for fifteen years, its vocabulary is in every tool and every article, and understanding what it could *not* do is the only way to understand why its successor looks the way it does.
- **Sections:**
  - `## The idea` — an ideal multitasking CPU would run every runnable task simultaneously at 1/N speed. CFS approximates that by tracking, for each task, how much CPU time it has had *weighted by its priority*, and always running the one that is furthest behind.
  - `## Virtual runtime` — real runtime scaled by the task's weight, so a high-priority task's clock runs slower and it therefore stays "behind" longer. Work one concrete example with two tasks at nice 0 and nice 5 and show the ratio of CPU they receive.
  - `## The red-black tree` — tasks ordered by vruntime, leftmost node is next. Note that this makes selection O(log n) with the leftmost node cached, and link back to `../04-kernel-architecture-and-idioms/kernel-data-structures.md` for the tree itself.
  - `## Slices: `sched_latency` and `min_granularity`` — the target period in which every runnable task should get a turn, divided by weight, floored by a minimum so that a hundred runnable tasks do not produce hundred-microsecond slices. Give the actual defaults *as they were*, flagged as historical, and note the tunables moved or were removed under EEVDF.
  - `## Placement on wakeup, and the fairness leak` — a waking task's vruntime is adjusted so it neither starves nor gets an unbounded credit for having slept. This is the part CFS never got fully right, and saying so sets up the next page.
  - `## What CFS could not express` — the crux of the page. CFS had exactly one knob, nice, and it conflated *how much CPU* a task should get with *how quickly it should be scheduled after waking*. A latency-sensitive task that wants little CPU but wants it promptly could only be expressed by giving it a large share, which is the wrong instrument. Every wakeup heuristic accumulated in CFS was an attempt to work around this.
  - `## Reading old material` — a short, practical note: articles before roughly 2023 describe CFS, and their vruntime and red-black tree explanations remain accurate as *background* while their tunables and wakeup behaviour do not apply. Give the reader the rule for telling which is which.
- **Anchor:** a Mermaid `flowchart LR` of the red-black tree with four tasks labelled by vruntime, the leftmost highlighted as next, and an arrow showing the running task being reinserted with an increased vruntime. Caption: "CFS picks the leftmost node — the task with the least weighted CPU time — and reinserts it once it has run."
- **KernelFacts:** `structure` — `[["struct sched_entity", "include/linux/sched.h"], ["struct cfs_rq", "kernel/sched/sched.h"]]`; `path` — `"task_tick_fair() → update_curr() → vruntime += delta * weight ratio → check_preempt_tick()"` (verify which of these survive at v6.18 — several were reshaped by EEVDF); `observe` — `cat /proc/self/sched` (needs `CONFIG_SCHED_DEBUG`; shows `se.vruntime` among other fields); `trap` — "vruntime is not a time in any wall-clock sense — it is time divided by weight. Two tasks with equal vruntime have had equal *fair shares*, not equal CPU."
- **References:**
  - `https://docs.kernel.org/scheduler/sched-design-CFS.html` — the in-tree design document; note in the annotation whether it still exists and is current at v6.18, since the fair scheduler's documentation was revised for EEVDF.
  - Ingo Molnar's original CFS announcement, `https://lwn.net/Articles/230501/` — the design in its author's words; 2007, and correct about the idea rather than the current code.
  - `<Src file="kernel/sched/fair.c" symbol="update_curr" />` — where virtual runtime is actually accumulated.
  - LWN, *"Completing the CFS story"*-type retrospectives — cite one specific article and mark it as pre-EEVDF.

### `eevdf.md` — EEVDF: The Current Fair Scheduler

- **Opens with:** the problem statement EEVDF answers. Fair share and scheduling latency are two different requests, and a scheduler with one knob cannot serve both. EEVDF separates them: a task declares how much CPU it deserves (its weight) *and* how large a chunk it wants at a time (its request size), and the algorithm makes latency a consequence of the second rather than a heuristic bolted onto the first.
- **Sections:**
  - `## Lag, and eligibility` — lag is the difference between the service a task *should* have received and what it *did* receive. A task is eligible when its lag is non-negative, i.e. when it is at or behind its fair share. Only eligible tasks are candidates. This is the concept the whole algorithm rests on, so define it carefully and with an example.
  - `## Virtual deadlines` — among eligible tasks, pick the one with the earliest virtual deadline, where the deadline is derived from the eligible time plus the request size scaled by weight. Show the calculation for two tasks with different slices.
  - `## Request size, and where it comes from` — the per-task slice, settable through `sched_setattr`'s `sched_runtime` field (verify the interface and its unit at v6.18). This is the new expressive power: a task can ask for short slices, get scheduled promptly, and still receive only its fair share overall.
  - `## What changed for tuning` — the practical section. Which old `sysctl` knobs are gone or renamed, what `/sys/kernel/debug/sched/` exposes at v6.18, and what the base slice tunable is now called. **Every value in this section is context7-verified and dated**; where a knob's current name cannot be confirmed, say what it does and refuse to name it rather than guessing.
  - `## What did not change` — weights still come from nice, the fair class still sits below RT and deadline, group scheduling still applies. Saying what stayed the same is what keeps the reader's existing knowledge useful.
  - `## Which articles are now wrong` — a short, concrete list of claims that were true under CFS and are not now: that latency is tuned via `sched_latency`, that a nice value is the only way to affect wakeup promptness, and that a waking task's vruntime is adjusted by a placement heuristic. Blunt and useful.
  - `## A worked comparison` — one scenario (a latency-sensitive task doing 1 ms of work every 10 ms, competing with two CPU hogs) described under CFS and under EEVDF, with what each does. This is the page's payoff.
  - `:::note` version-scoped: everything here is v6.18. State that a 6.5-or-earlier system runs CFS and that the two schedulers answer the same questions differently.
- **Anchor:** a Mermaid `flowchart TB` of the selection: filter runnable tasks to the eligible ones (lag ≥ 0), then pick the earliest virtual deadline among those. Caption: "EEVDF in two steps: eligibility decides *who may run*, the virtual deadline decides *who runs first*."
- **KernelFacts:** `structure` — `[["struct sched_entity", "include/linux/sched.h"], ["struct sched_attr", "include/uapi/linux/sched/types.h"]]`; `path` — `"pick_next_entity() → pick_eevdf() → eligible tasks → earliest virtual deadline"` (verify the current function names at v6.18); `observe` — `ls /sys/kernel/debug/sched/ && cat /proc/self/sched | grep -E 'vlag|slice|vruntime'` (requires `CONFIG_SCHED_DEBUG` and debugfs mounted); `trap` — "EEVDF did not make Linux 'more fair'. It made *latency* separately expressible from *share*, which means a tuning approach built on nice values alone was already the wrong tool and is now visibly so."
- **References:**
  - `https://docs.kernel.org/scheduler/sched-eevdf.html` if it exists at v6.18, otherwise the fair-scheduler design document — **check which is present before citing**, and state the check date.
  - LWN, *"An EEVDF CPU scheduler for Linux"* (`https://lwn.net/Articles/925371/`) — the clearest available explanation of lag and eligibility; from the merge period, so note that details changed afterwards.
  - Stoica & Abdel-Wahab, *"Earliest Eligible Virtual Deadline First"* (1995) — the original algorithm, for readers who want the source of the vocabulary; a technical report, freely available.
  - `man 2 sched_setattr` — the interface through which a task expresses its slice; the authority for field names and units.

- [ ] **Step 1: Write `cfs-and-vruntime.md`** to the brief above.
- [ ] **Step 2: Run the context7 verification for EEVDF** before writing the second page: resolve the docs id, query for the current scheduler documentation and tunable names, and note the date. Cross-check anything it returns against `<Src file="kernel/sched/fair.c" />` at v6.18 — the source is the tiebreaker.
- [ ] **Step 3: Write `eevdf.md`**, marking every tunable name with the evidence it was verified against.
- [ ] **Step 4: Verify** `sched_entity` field names (`vlag`, `slice`, `deadline`), `pick_eevdf`, `update_curr`, `cfs_rq`, and `sched_attr` against Elixir v6.18. **If a name in this plan does not exist at v6.18, the plan is wrong and the source is right.**
- [ ] **Step 5: Check `/sys/kernel/debug/sched/` on a real v6.18-class machine** and list only the files that are actually there.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/07-scheduling
git commit -m "docs: write CFS and the EEVDF fair scheduler"
```

---

## Task 16: Folder 07 — priorities, and preemption models

**Files:**
- Modify: `docs/linux/07-scheduling/priorities-nice-and-weights.md`
- Modify: `docs/linux/07-scheduling/preemption-models.md`

**Interfaces:**
- Consumes: `07/eevdf` and `07/runqueues-and-scheduling-classes` (Tasks 14–15).
- Produces: `07/preemption-models`, a declared prerequisite of `07/real-time-scheduling`, and the preemption vocabulary folder 10's `hardirq-context` and `threaded-irqs` pages both use.

### `priorities-nice-and-weights.md` — Priorities, nice, and Weights **[WAH]** **[Misc]**

- **Opens with:** the question the page answers precisely — what does `nice -n 5` actually buy? Not a percentage, not a guarantee, and not the same thing in every scheduling class. It buys a change in one number, and that number's effect is multiplicative and only meaningful relative to what else is running.
- **Sections:**
  - `## nice is a weight, not a priority` — the nice-to-weight table with its ~1.25 geometric ratio, so that each nice level is roughly a 10% change in CPU share against one competitor. Show five rows of the real table and give the formula.
  - `## What actually happens` **[WAH]** — running two CPU-bound processes, one at nice 0 and one at nice 5, on one CPU. Predict the split from the weight ratio, then show a real measurement. Then do it again with one at nice 0 and one at nice 19 and show that the low-priority task still gets a few percent rather than zero — because a weight is a ratio, and a ratio never reaches zero. Say what that means practically: nice cannot express "only run when nothing else wants the CPU"; `SCHED_IDLE` can.
  - `## Priority means different things per class` — a table across `SCHED_OTHER` (nice, a weight), `SCHED_FIFO`/`SCHED_RR` (a static priority 1–99, strictly ordered), and `SCHED_DEADLINE` (no priority at all — a runtime, deadline, and period). Say that `ps`'s `PRI` and `NI` columns and `chrt`'s output use different numbering conventions, and give the mapping, because this is a real source of confusion.
  - `## Autogroups` — a desktop default that surprises server people: tasks are grouped per session, and the group competes, not the task. This is why `nice` on one process in a many-process build can appear to do nothing, and why `kernel.sched_autogroup_enabled` exists.
  - `## `renice` and what it cannot do` — an unprivileged process may only lower its own priority; raising it requires `CAP_SYS_NICE` or an `RLIMIT_NICE` allowance. Say why the asymmetry exists.
  - `## When nice is the wrong tool` — the honest closing: if the requirement is a cap, use `cpu.max`; if it is a floor, use `cpu.weight` in a cgroup; if it is latency, use a smaller slice or a real-time policy. Link forward to `./cgroup-cpu-control.md`, which is in this phase.
  - `## Misconceptions` **[Misc]** — (1) "nice 19 means the process only runs when the system is idle" — it means a small weight, not zero; `SCHED_IDLE` is the policy that means that; (2) "nice affects I/O" — it does not, `ionice` is a separate mechanism against a separate scheduler; (3) "a lower nice number is lower priority" — lower nice is *higher* priority, and the name is an accurate description of behaviour rather than of rank.
- **Anchor:** the nice-to-weight table with a derived "share against a nice-0 competitor" column, which turns an abstract weight into the number readers actually want.
- **KernelFacts:** `structure` — `[["sched_prio_to_weight[]", "kernel/sched/core.c"]]` (verify the array's name and location at v6.18); `path` — `"setpriority() → set_user_nice() → reweight_entity() → new weight in the fair queue"`; `observe` — `ps -eo pid,ni,pri,rtprio,policy,comm | head` and `chrt -p $$`; `trap` — "nice is a ratio against whatever else is runnable. A nice-19 task alone on a machine gets 100% of a CPU, and the same task against one nice-0 competitor gets a few percent — the number describes a relationship, not an allocation."
- **References:**
  - `man 2 setpriority` and `man 1 nice` — the interface and the range, including who may raise a priority.
  - `<Src file="kernel/sched/core.c" symbol="set_user_nice" />` — where a nice value becomes a weight, and the table it indexes.
  - `man 7 sched` — the per-policy priority semantics, and the `PRI`-versus-`NI` numbering that confuses everyone.
  - LWN's coverage of autogroups (`https://lwn.net/Articles/418884/`) — why desktop responsiveness got a scheduling feature; 2010, and the mechanism is unchanged.

### `preemption-models.md` — Preemption Models

- **Opens with:** the single design question this page is about — when the kernel is executing on behalf of a task and something more urgent becomes runnable, may the kernel be interrupted mid-operation? Every preemption model is an answer, and each answer trades worst-case latency against throughput and complexity.
- **Sections:**
  - `## The models` — `PREEMPT_NONE`, `PREEMPT_VOLUNTARY`, `PREEMPT` (full), `PREEMPT_RT`, and lazy preemption at the pinned version. A table: what each allows, the typical worst-case latency shape, the throughput cost, and the workload it suits. **Verify the set of models and the lazy-preemption status at v6.18 via the source and via context7** — this changed recently and is exactly the kind of claim that goes stale.
  - `## `need_resched` and the preemption counter` — the two pieces of state that make preemption decisions: a per-task flag saying "you should give up the CPU" and a per-CPU counter saying "you may not right now". Explain that the counter is incremented by spinlocks, interrupts, and explicit `preempt_disable`, and that preemption happens when the counter reaches zero and the flag is set.
  - `## Preemption points` — where the check actually happens: return from interrupt to kernel code (full preemption only), return to user space (always), `cond_resched()` calls (voluntary), and unlocking the last spinlock. Draw the reader's attention to `cond_resched` as the manual annotation model — long kernel loops must volunteer.
  - `## What preemption is not` — it is not interrupt handling and it is not multitasking. An interrupt can arrive at (almost) any moment regardless of the model; preemption is only about whether *scheduling* may happen at that moment. This distinction is what folder 10's `hardirq-context` builds on.
  - `## Where the kernel is never preemptible` — in an interrupt handler, holding a spinlock, in an RCU read-side critical section under some configurations, and in explicitly disabled regions. Give the rule that follows: latency is bounded by the longest such region, which is why PREEMPT_RT's project was converting those regions rather than changing the scheduler.
  - `## PREEMPT_RT, in one section` — sleeping spinlocks, threaded interrupt handlers, and priority inheritance, with what each buys. Then hand off: the embedded section owns PREEMPT_RT in practice, and folder 10 owns threaded IRQs. Link to `../../embedded/` only if a written page exists there; otherwise name it in prose.
  - `## Choosing one` — the practical guidance: servers and throughput workloads default to none or voluntary, desktops and general-purpose distributions to full, and audio, industrial control, and hard-latency work to RT. State that measuring with `cyclictest` beats reasoning about it.
- **Anchor:** a WaveDrom `signal` diagram of the same wakeup under two models — a high-priority task becoming runnable while the kernel is in a long operation, showing the latency to actually running under voluntary preemption versus full preemption. Caption: "The same wakeup under two preemption models: the delay is the length of the region that could not be preempted."
- **KernelFacts:** `structure` — `[["struct thread_info", "arch/x86/include/asm/thread_info.h"], ["preempt_count", "include/linux/preempt.h"]]`; `path` — `"wakeup → set TIF_NEED_RESCHED → preempt_count reaches 0 → preempt_schedule() → __schedule()"`; `observe` — `grep -E 'CONFIG_PREEMPT' /boot/config-$(uname -r)` and, at v6.18, `cat /sys/kernel/debug/sched/preempt` if present (verify); `trap` — "Preemption is not about whether interrupts are handled — those arrive regardless. It is about whether the *scheduler* may run at that moment, and the difference is why a machine with fast interrupt handling can still have terrible scheduling latency."
- **References:**
  - `https://docs.kernel.org/scheduler/index.html` and the in-tree preemption documentation — the authority on which models exist at v6.18.
  - `<Src file="include/linux/preempt.h" symbol="preempt_count" />` — the counter and the macros that manipulate it, with comments explaining the field layout.
  - LWN, *"Lazy preemption"* coverage — the most recent change to this list; cite the specific article, note its date, and say whether the feature is default at v6.18.
  - `https://wiki.linuxfoundation.org/realtime/start` — the PREEMPT_RT project's own documentation and the `cyclictest` methodology.

- [ ] **Step 1: Write `priorities-nice-and-weights.md`** to the brief above.
- [ ] **Step 2: Run the two-process nice experiment** on a single CPU (`taskset -c 0`) and paste the real measured split rather than the theoretical one. Note the measured numbers will not exactly match the weight ratio, and say why in the page.
- [ ] **Step 3: Write `preemption-models.md`** to the brief above.
- [ ] **Step 4: Verify the preemption model list at v6.18** from `<Src file="kernel/Kconfig.preempt" />` — this is the definitive list, and it is short enough to read in full.
- [ ] **Step 5: Verify** `sched_prio_to_weight`, `set_user_nice`, `preempt_count`, and the `TIF_NEED_RESCHED` flag name against Elixir v6.18.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/07-scheduling
git commit -m "docs: write nice weights and the kernel preemption models"
```

---

## Task 17: Folder 07 — the context switch, and load balancing

**Files:**
- Modify: `docs/linux/07-scheduling/the-context-switch.md`
- Modify: `docs/linux/07-scheduling/smp-load-balancing.md`

**Interfaces:**
- Consumes: `07/runqueues-and-scheduling-classes` (Task 14).
- Produces: `07/the-context-switch`, the declared prerequisite of `07/smp-load-balancing` and `07/diagnosing-scheduling-latency`. The TLB consequences stated here are elaborated by `08/tlb-and-address-space-switching`; keep the boundary — this page owns the switch, folder 08 owns the TLB.

### `the-context-switch.md` — The Context Switch **[WAH]** **[Misc]**

- **Opens with:** the observation that the context switch is both smaller and larger than people think. The register save and restore is a few dozen instructions; the real cost is everything the new task finds cold — caches, TLB entries, branch predictors — and that cost is paid by the *incoming* task, at a time and place that makes it nearly invisible in profiles.
- **Sections:**
  - `## The three steps` — `__schedule` picks the next task, `context_switch` swaps the address space if it changed, and `switch_to` swaps the register state and stack. Name the split clearly because the two halves have completely different costs.
  - `## `switch_mm`, and when it is skipped` — if the next task shares the outgoing task's `mm` (a thread of the same process, or a kernel thread borrowing via `active_mm`), no page-table switch happens at all. This is the concrete, measurable sense in which switching between threads is cheaper than between processes.
  - `## The TLB consequence` — a `CR3` write without PCID flushes the TLB; with PCID the entries survive, tagged. Give the shape of the cost and hand the mechanism to `../08-memory-management/tlb-and-address-space-switching.md`.
  - `## `switch_to`, and what the hardware does not do` — on x86-64 there is no hardware task switch in use: the kernel saves callee-saved registers, swaps the stack pointer, and returns into the other task's saved context. The trick worth calling out is that `switch_to` "returns" into a different task's stack, which is why reading it is disorienting and why the FPU handling appears where it does.
  - `## FPU and extended state` — `XSAVE`/`XRSTOR` on a state area that can be large with AVX-512, and the lazy strategies used to avoid touching it. Note that this is a real per-switch cost that scales with the width of the vector registers the workload uses.
  - `## What actually happens` **[WAH]** — the true cost of a context switch, measured properly. Show the direct cost (a few hundred nanoseconds for the switch itself) and then the indirect cost by measuring a workload's throughput with and without forced switching, so the reader sees that the cache effects dominate. State the practical consequence: reducing context switches is usually about reducing *wakeups*, not about making switches faster.
  - `## Voluntary versus involuntary` — `/proc/PID/status`'s two counters, what each one indicates about a workload (voluntary = blocking on something, involuntary = preempted), and how to read the ratio when diagnosing.
  - `## Misconceptions` **[Misc]** — (1) "context switches are expensive because saving registers is slow" — the registers are the cheap part; (2) "a thread switch is free" — it skips the address-space switch and still pays cache and predictor costs; (3) "high context-switch counts are bad" — a high voluntary count usually means an I/O-bound workload behaving correctly.
- **Anchor:** a Mermaid `sequenceDiagram` — Task A, `__schedule`, `switch_mm`, `switch_to`, Task B — with the conditional skip of `switch_mm` drawn when `mm` is unchanged. Caption: "One context switch, with the address-space step that a thread-to-thread switch skips entirely."
- **KernelFacts:** `structure` — `[["struct task_struct", "include/linux/sched.h"], ["struct thread_struct", "arch/x86/include/asm/processor.h"]]`; `path` — `"__schedule() → context_switch() → switch_mm_irqs_off() → switch_to() → __switch_to()"`; `observe` — `grep ctxt /proc/stat && grep -E 'voluntary_ctxt|nonvoluntary_ctxt' /proc/self/status`; `trap` — "The measurable cost of a context switch is paid *after* it, by the task that just started running and finds its caches cold. Benchmarks that measure the switch itself measure the small part."
- **References:**
  - `<Src file="arch/x86/kernel/process_64.c" symbol="__switch_to" />` — the x86-64 register and segment work, with the FPU handling visible.
  - `<Src file="arch/x86/mm/tlb.c" symbol="switch_mm_irqs_off" />` — the address-space switch and the PCID logic.
  - Li, Ding & Shen, *"Quantifying the Cost of Context Switch"*, ExpCS 2007 — `https://www.cs.rochester.edu/u/cli/research/switch.pdf`. The paper that separated direct from indirect cost; old, and the methodology is the point.
  - `man 5 proc`, the `status` fields — for the two context-switch counters and what they mean.

### `smp-load-balancing.md` — SMP and Load Balancing

- **Opens with:** the tension the balancer lives in. Moving a task to an idle CPU uses hardware that would otherwise be wasted; moving it also throws away its warm caches and, on a NUMA machine, may separate it from its memory. The balancer's whole job is to guess when the first outweighs the second, and it guesses using a model of the machine's topology.
- **Sections:**
  - `## Scheduling domains` — the hierarchy built from the hardware: SMT siblings, cores sharing an LLC, sockets, NUMA nodes. Each level has its own balancing interval and its own migration cost estimate, because moving between SMT siblings is nearly free and moving between sockets is not.
  - `## Where the topology comes from` — `/sys/devices/system/cpu/cpuN/topology/` and the firmware tables behind it. Link to `../../computer-science/memory-hierarchy/numa-and-memory-topology.md` for what the topology means physically.
  - `## Two kinds of balancing` — periodic (a tick-driven check that pulls work from a busier domain) and idle (a CPU about to go idle looks for work to steal). Say which one dominates in practice for a given workload shape, and note the newidle path's latency sensitivity.
  - `## Wake affinity, and its failure modes` — on wakeup the scheduler chooses between the waker's CPU (good for shared data), the task's previous CPU (good for warm caches), and an idle CPU (good for latency). Give the two classic failures: a producer-consumer pair pulled apart onto different LLCs, and a thundering wake of many tasks all placed on one CPU. Name `WF_SYNC` and the LLC-scan behaviour as the mechanisms involved, verifying the names at v6.18.
  - `## Migration cost` — the balancer will not move a task that ran very recently, on the assumption its cache footprint is still warm. Name the tunable if it exists at v6.18 and say what it defaults to; otherwise describe the behaviour without naming a knob.
  - `## `cpusets`, affinity, and isolation` — the three ways to override: `sched_setaffinity` for one task, `cpuset` cgroups for a group, and `isolcpus`/`nohz_full` for taking CPUs out of the balancer's reach entirely. Link forward to `./cgroup-cpu-control.md` and, in prose only, to the tick page in folder 10 — which does exist in this phase, so link it: `../10-interrupts-time-and-deferred-work/the-tick-and-nohz.md`.
  - `## "My thread moved CPUs and got slower"` — the closing diagnostic section: how to confirm it (per-CPU counters, `perf stat -e migrations`), and what to do about it (pin, or make the wakeup pattern not require the move). State honestly that pinning is often the right answer and often the wrong one, and give the test that distinguishes.
- **Anchor:** a Mermaid `flowchart TB` of a two-socket machine's scheduling domains — SMT, core/LLC, socket, NUMA — with the balancing interval and relative migration cost annotated at each level. Caption: "The domain hierarchy the balancer walks, and why a migration's cost depends entirely on which level it crosses."
- **KernelFacts:** `structure` — `[["struct sched_domain", "include/linux/sched/topology.h"], ["struct sched_group", "kernel/sched/sched.h"]]`; `path` — `"scheduler_tick() → trigger_load_balance() → run_rebalance_domains() → sched_balance_rq()"` (**verify — `load_balance` was renamed in the 6.9 era**); `observe` — `perf stat -e migrations,context-switches -- ./workload` and `cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list`; `trap` — "An idle CPU is not free capacity. Pulling a task onto it costs the task its warm caches, and on a two-socket machine it can cost the task its local memory too — which is why the balancer deliberately leaves CPUs idle."
- **References:**
  - `https://docs.kernel.org/scheduler/sched-domains.html` — the in-tree description of the domain hierarchy and the flags at each level.
  - `<Src file="kernel/sched/fair.c" symbol="sched_balance_rq" />` — the balancing pass itself; verify the symbol name at v6.18 before citing.
  - Lozi et al., *"The Linux Scheduler: a Decade of Wasted Cores"*, EuroSys 2016 — `https://people.ece.ubc.ca/sasha/papers/eurosys16-final29.pdf`. Four real load-balancing bugs found by building the right tooling; predates the pinned kernel and the *method* is the lasting contribution.
  - `man 2 sched_setaffinity` and `man 7 cpuset` — the override mechanisms.

- [ ] **Step 1: Write `the-context-switch.md`** to the brief above.
- [ ] **Step 2: Measure the context-switch cost for real** — a ping-pong benchmark over a pipe for the direct cost, and a cache-resident workload with and without forced migration for the indirect cost. Paste real numbers with the machine described.
- [ ] **Step 3: Write `smp-load-balancing.md`** to the brief above.
- [ ] **Step 4: Verify** `switch_mm_irqs_off`, `__switch_to`, `sched_domain`, `sched_group`, the balancing entry-point name, and `thread_struct` against Elixir v6.18. The balancing function rename is the most likely error in this task.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/07-scheduling
git commit -m "docs: write the context switch and SMP load balancing"
```

---

## Task 18: Folder 07 — real-time, cgroup CPU control, and diagnosis

**Files:**
- Modify: `docs/linux/07-scheduling/real-time-scheduling.md`
- Modify: `docs/linux/07-scheduling/cgroup-cpu-control.md`
- Modify: `docs/linux/07-scheduling/diagnosing-scheduling-latency.md`

**Interfaces:**
- Consumes: `07/runqueues-and-scheduling-classes`, `07/preemption-models`, `07/eevdf`, `07/the-context-switch`.
- Produces: `07/real-time-scheduling`, a declared prerequisite of `10/threaded-irqs`, and the folder's closing diagnostic page.

### `real-time-scheduling.md` — Real-Time Scheduling

- **Opens with:** the definition that has to come first, because the word misleads. Real-time does not mean fast; it means *predictable*. A real-time policy trades average throughput for a bounded worst case, and a system tuned for real time is frequently slower on average than the same system without it.
- **Sections:**
  - `## `SCHED_FIFO` and `SCHED_RR`` — static priorities 1–99, strictly above every fair task, run-until-you-block for FIFO and a time quantum for RR. Give the two-line summary of when RR helps (equal-priority tasks that must share) and note it is rarer than people assume.
  - `## `SCHED_DEADLINE`` — the interesting one: a task declares a runtime, a deadline, and a period, and the kernel either accepts it or refuses. Explain the Constant Bandwidth Server enforcement (a task that overruns its runtime is throttled until its next period) and admission control (the kernel refuses a task whose bandwidth would make the set unschedulable). Say plainly that this is the only Linux policy that makes a guarantee rather than a promise.
  - `## Admission control, and why `sched_setattr` fails` — a worked example of the sum-of-utilisations test, and the practical note that on a multi-CPU system the accounting is per-root-domain, which is why `cpuset` partitioning and deadline tasks interact.
  - `## RT throttling` — `sched_rt_runtime_us` and `sched_rt_period_us`: by default RT tasks are limited to 95% of each period, so a spinning FIFO task cannot make the machine unusable. State what happens when it triggers (the RT task is throttled and a message may appear in `dmesg`) and note that turning throttling off is a decision to accept an unrecoverable machine as a possible outcome.
  - `:::warning` — a `SCHED_FIFO` task that spins on a machine without RT throttling and without a spare CPU will make that machine unresponsive to everything, including your shell. The QEMU lab is the right place to try it.
  - `## Priority inheritance` — the unbounded-priority-inversion problem in two sentences, and `PTHREAD_PRIO_INHERIT` / the kernel's RT mutexes as the answer. Point at `../09-concurrency-and-locking/mutexes-and-semaphores.md` for the lock side, which is in this phase.
  - `## PREEMPT_RT, in one section` — what converting spinlocks to sleeping locks and handlers to threads actually buys, the latency figures the project reports as an order of magnitude, and the throughput cost. Hand off to the embedded section in prose and link `./preemption-models.md`.
  - `## Doing it properly` — the checklist: choose a policy, set affinity, isolate the CPU (`isolcpus`, `nohz_full`, IRQ affinity away from it), lock memory with `mlockall`, pre-fault the stack, and *measure with `cyclictest`*. Say that skipping the memory-locking step is the most common reason a "real-time" application still shows millisecond outliers — the outlier is a page fault.
- **Anchor:** a WaveDrom `signal` diagram of a `SCHED_DEADLINE` task over three periods — runtime consumed, the throttle when it overruns, and the replenishment at the next period boundary. Caption: "A deadline task that overruns: the Constant Bandwidth Server throttles it rather than letting it steal the next task's guarantee."
- **KernelFacts:** `structure` — `[["struct sched_dl_entity", "include/linux/sched.h"], ["struct sched_attr", "include/uapi/linux/sched/types.h"]]`; `path` — `"sched_setattr() → __sched_setscheduler() → dl admission test → dl_sched_class → enqueue"`; `observe` — `chrt -p 1 && cat /proc/sys/kernel/sched_rt_runtime_us && cat /proc/sys/kernel/sched_rt_period_us`; `trap` — "A real-time priority does not make a task fast. It makes it *first*, which is only useful if the task is also prevented from taking a page fault, waiting on a lock, or being migrated — and none of those follow from the policy."
- **References:**
  - `https://docs.kernel.org/scheduler/sched-deadline.html` — the in-tree deadline documentation, including the admission test and the CBS description.
  - `man 7 sched` — the policy definitions, priority ranges, and the RT throttling parameters.
  - `https://wiki.linuxfoundation.org/realtime/documentation/start` — the PREEMPT_RT documentation and the `cyclictest` methodology every claim about latency should be checked against.
  - `man 2 sched_setattr` — the only interface that can set a deadline task, and the reason `chrt` needs a recent version to do it.

### `cgroup-cpu-control.md` — cgroup CPU Control **[WAH]** **[Misc]**

- **Opens with:** the shift in unit. Everything earlier in this folder schedules tasks; a container, a service, or a user session is a *group* of tasks, and the interesting question becomes how much CPU that group gets regardless of how many tasks it contains. Group scheduling answers it by making the hierarchy itself schedulable.
- **Sections:**
  - `## Group scheduling` — a `task_group` owns a `cfs_rq` per CPU, and the scheduler picks a group before picking a task within it. This is why one process forking a hundred children does not automatically get a hundred times the CPU.
  - `## `cpu.weight`` — the proportional control, cgroup v2's replacement for v1's `cpu.shares`, with the value range and the mapping to nice-equivalent behaviour. Say what it guarantees (a share of a *contended* CPU) and what it does not (any limit when the CPU is idle).
  - `## `cpu.max`: quota and period` — the hard cap: a quota of microseconds per period. Give the format (`"$MAX $PERIOD"`) and note the default period.
  - `## What actually happens` **[WAH]** — a container with `cpu.max` of `50000 100000` running a four-thread CPU-bound workload. The four threads burn the 50 ms quota in 12.5 ms of wall time, and then **the whole group is throttled for the remaining 87.5 ms of the period**. Show `cpu.stat`'s `nr_throttled` and `throttled_usec` climbing. The lesson stated explicitly: a quota does not slow a workload down smoothly, it runs it at full speed and then stops it dead, which turns a CPU limit into a latency problem. Then give the two mitigations — more threads is *worse*, not better; a shorter period or a higher quota is better — and note that this is the single most expensive misunderstanding in container operations.
  - `## `cpu.pressure`` — PSI as the "how much time did this group spend waiting for CPU it wanted" signal, and why it is a better overload indicator than utilisation. Enough to use it; folder 15 owns cgroup v2 as a whole.
  - `## The hierarchy, and who owns it` — on a systemd machine, systemd owns the cgroup tree, and writing to it directly fights the service manager. Name the correct interfaces (`CPUWeight=`, `CPUQuota=` in a unit) and link back to `../03-boot-and-init/systemd-in-practice-and-boot-debugging.md`.
  - `## `cpuset` versus quota` — a table: a quota gives you a fraction of CPU time on any CPU; a cpuset gives you specific CPUs entirely. Say which each is right for, and that a latency-sensitive workload almost always wants the second.
  - `## Misconceptions` **[Misc]** — (1) "a 0.5 CPU limit makes the app run at half speed" — it makes it run at full speed for half the period and be stopped for the rest; (2) "more threads help under a quota" — they exhaust the quota faster and increase throttled time; (3) "`cpu.weight` limits a container" — it only matters under contention, and an otherwise-idle machine gives the container everything.
- **Anchor:** a WaveDrom `signal` diagram over two 100 ms periods showing a four-thread workload consuming its 50 ms quota in the first 12.5 ms and being throttled for the remainder, twice. Caption: "A CPU quota is not a speed limit: the group runs flat out until the quota is gone, then stops until the period rolls over."
- **KernelFacts:** `structure` — `[["struct task_group", "kernel/sched/sched.h"], ["struct cfs_bandwidth", "kernel/sched/sched.h"]]`; `path` — `"quota exhausted → throttle_cfs_rq() → group dequeued → period timer → unthrottle_cfs_rq()"`; `observe` — `cat /sys/fs/cgroup/<path>/cpu.max && cat /sys/fs/cgroup/<path>/cpu.stat`; `trap` — "`nr_throttled` climbing means your workload is being stopped mid-flight, not slowed down. If a service has latency spikes and a CPU quota, check `cpu.stat` before anything else."
- **References:**
  - `https://docs.kernel.org/admin-guide/cgroup-v2.html`, the CPU controller section — the authority for every file name and unit on this page. **context7-verify the controller file list and date the check.**
  - `https://docs.kernel.org/accounting/psi.html` — what `cpu.pressure` measures and how to read it.
  - `<Src file="kernel/sched/fair.c" symbol="throttle_cfs_rq" />` — the throttling itself, which is short and makes the all-or-nothing behaviour obvious.
  - `man 5 systemd.resource-control` — the interface to use on any machine running systemd, rather than writing to the cgroup files directly.

### `diagnosing-scheduling-latency.md` — Diagnosing Scheduling Latency **[Lab host=root-required]**

- **Opens with:** the method, stated before any tool. "The application is janky" is not a scheduling problem until you have shown that the task was runnable and not running. That single measurement — runnable-but-waiting time — is what separates a scheduling problem from an I/O problem, a lock problem, or a slow algorithm, and every tool on this page exists to produce it.
- **Sections:**
  - `## The question to answer first` — was the task runnable and waiting, or was it not runnable at all? Give the two sources: `/proc/PID/schedstat` field 2 (time spent waiting on a runqueue) and PSI's `some` line for CPU. If that number is small, stop — this is not a scheduling problem, and the page says where to go instead.
  - `## `/proc/PID/schedstat` and `/proc/PID/sched`` — the three schedstat fields (time on CPU, time waiting, timeslices), what to sample and difference, and what `CONFIG_SCHEDSTATS` costs. Show a real before/after pair.
  - `## PSI` — `/proc/pressure/cpu` and per-cgroup `cpu.pressure`, `some` versus `full`, and the 10/60/300-second windows. Say what makes PSI different from load average: it measures *lost time*, not queue length.
  - `## `perf sched`` — `perf sched record` then `perf sched latency` for the per-task wait distribution, and `perf sched timehist` for the event-by-event view. Show a real `latency` table and read three of its columns aloud.
  - `## `runqlat`, and the histogram` — the BCC tool that gives runqueue latency as a log-scale histogram; the shape of the histogram is the diagnosis (a long tail versus a shifted mean mean different things). Name the tool, do not link to folder 18.
  - `## The scheduler tracepoints` — `sched:sched_switch`, `sched_wakeup`, `sched_stat_runtime`, `sched_migrate_task`, and what each answers. Enough to build a custom measurement when the tools do not fit.
  - `<Lab host="root-required" title="From 'it is janky' to a named cause" time="30 min">` — a deliberately constructed case: run a latency-sensitive loop (measure its own wakeup-to-run delay) alongside enough CPU hogs to saturate the machine, then (1) show `schedstat` wait time rising, (2) show `/proc/pressure/cpu` `some avg10` rising, (3) run `perf sched latency` and identify the victim, (4) fix it by pinning or by nice and re-measure. Every step with expected output. "If it fails": `CONFIG_SCHEDSTATS` may be off (the fields are then all zero), and `perf sched record` needs `perf_event_paranoid` low enough or root.
  - `## A worked investigation` — the closing narrative: symptom, first measurement, hypothesis, the measurement that falsified the first hypothesis, and the actual cause. Follow the shape of the lab but written as prose, so the *method* is what the reader takes away.
- **Anchor:** a Mermaid `flowchart TB` decision tree: is runqueue wait time high? → if no, not a scheduling problem (I/O, locks, or the code itself); if yes → is the machine saturated? → if yes, capacity or priority; if no → is a quota throttling it? → is affinity or a migration the cause? Caption: "The first four questions, in the order that eliminates the most possibilities per measurement."
- **KernelFacts:** `structure` — `[["struct sched_statistics", "include/linux/sched.h"]]` (verify at v6.18); `path` — `"wakeup → enqueue on runqueue → wait (this is the latency) → pick_next_task() → running"`; `observe` — `awk '{print "waited:", $2, "ns"}' /proc/self/schedstat`; `trap` — "High CPU utilisation is not scheduling latency and low utilisation does not rule it out. A task pinned to one busy CPU on an otherwise idle machine has terrible scheduling latency and a system-wide utilisation figure that looks fine."
- **References:**
  - `https://docs.kernel.org/scheduler/sched-stats.html` — the field-by-field definition of `schedstat`, which is otherwise undocumented columns of integers.
  - `https://docs.kernel.org/accounting/psi.html` — PSI's definition of `some` and `full`, and the windows.
  - `https://man7.org/linux/man-pages/man1/perf-sched.1.html` — the subcommand surface and what each report shows.
  - Gregg, *Systems Performance*, 2nd ed., the CPU chapter — the methodology this page's opening section follows; a purchase, and the best available treatment of "measure the right thing first".

- [ ] **Step 1: Write `real-time-scheduling.md`** to the brief above.
- [ ] **Step 2: Write `cgroup-cpu-control.md`** to the brief above, after **context7-verifying** the cgroup v2 CPU controller's file names and semantics and recording the date.
- [ ] **Step 3: Run the throttling demonstration** — a real cgroup with `cpu.max` set and a multi-threaded burner — and paste real `cpu.stat` output. The [WAH] section is worthless if the numbers are invented.
- [ ] **Step 4: Run the diagnosis lab** end to end, then write `diagnosing-scheduling-latency.md` from what it produced.
- [ ] **Step 5: Verify** `sched_dl_entity`, `sched_attr`, `task_group`, `cfs_bandwidth`, `throttle_cfs_rq`, `sched_statistics`, and the RT sysctl names against Elixir v6.18.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/07-scheduling
git commit -m "docs: write real-time scheduling, cgroup CPU control, and latency diagnosis"
```

---
## Task 19: Folder 08 — the address space, and the page-table walk

**Files:**
- Modify: `docs/linux/08-memory-management/the-virtual-address-space.md`
- Modify: `docs/linux/08-memory-management/page-tables-and-the-walk.md`

**Interfaces:**
- Consumes: `06/the-process-address-space` (the user-visible map) and `computer-science/memory-hierarchy/virtual-memory-and-paging` (the hardware model). This folder owns the kernel's *use* of paging; the CS page owns paging itself.
- Produces: `08/page-tables-and-the-walk`, the declared prerequisite of `08/the-page-fault-handler`, `08/tlb-and-address-space-switching`, and `08/hugepages-and-thp`. **Write this task before anything else in folder 08** — the spec orders it explicitly.

### `the-virtual-address-space.md` — The Virtual Address Space

- **Opens with:** the fact that a 64-bit address space is not 64 bits, and the reasons are entirely practical. Implementing a full 64-bit translation would mean six levels of page table and a walk nobody wants to pay for, so hardware implements a subset, and the unimplemented middle becomes a hole with strange consequences that leak all the way up to user space.
- **Sections:**
  - `## Canonical addresses and the hole` — 48 bits implemented (57 with 5-level paging), sign-extended into the top bits, so the valid space is two ranges with an enormous unusable gap. State the practical consequence: pointers with garbage in the high bits fault as non-canonical (`#GP`) rather than as page faults, which is why some bad pointers oops differently from others.
  - `## The user/kernel split` — the lower half belongs to the process, the upper half to the kernel, and it is the *same* upper half in every process. That is why a syscall does not need a page-table switch and why KPTI (which removes most of it) is expensive.
  - `## The kernel's own regions` — a table with the direct map (`page_offset_base`), vmalloc space, the vmemmap array, the module region, and the fixmap. For each: what lives there, roughly how large, and why it exists as a separate region rather than being carved from the others. The direct map deserves two sentences: every physical page has a permanent kernel virtual address, which is what makes `virt_to_phys` a subtraction.
  - `## KASLR` — the bases of those regions are randomised at boot, which is why the layout documentation gives symbolic names rather than constants and why an address you read in one boot means nothing in the next. Name `nokaslr` for debugging and point at `../03-boot-and-init/early-boot-and-arch-setup.md`, which set up the early tables.
  - `## Five-level paging` — 57-bit addresses, opt-in and boot-detected, and the compatibility rule that mappings above the 47-bit boundary are only handed out on explicit request (an `mmap` hint), so that old software with tagged pointers keeps working. This is a nice concrete instance of the ABI promise from folder 05.
  - `## arm64` — `:::note`: two separate translation base registers (`TTBR0_EL1` for user, `TTBR1_EL1` for kernel) rather than one table containing both halves, which is a structurally different answer to the same problem and means arm64 never needed KPTI's trampoline for the same reason.
  - `## Where to read the real numbers` — `Documentation/arch/x86/x86_64/mm.rst` is the map, and it is the file to check rather than trusting any diagram, including this page's.
- **Anchor:** a Mermaid `flowchart TB` of the full 64-bit space top to bottom — kernel regions named, the non-canonical hole drawn as a break, and the user half — with each region annotated as "per process" or "shared by all processes". Caption: "The x86-64 address space, and the one property that matters most: the top half is the same in every process."
- **KernelFacts:** `structure` — `[["page_offset_base", "arch/x86/mm/kaslr.c"], ["struct mm_struct", "include/linux/mm_types.h"]]` (verify); `path` — `"virtual address → canonical check → CR3 → four-level walk → physical address"`; `observe` — `sudo cat /proc/kallsyms | head -3 && cat /proc/self/maps | tail -3` (the kernel symbols are in the upper half, the process mappings in the lower); `trap` — "The kernel half of the address space is not 'the kernel's memory'. It is a set of *mappings* present in every process's page tables, permission-checked by the supervisor bit — which is why a user-mode dereference of a kernel address is a page fault rather than a successful read."
- **References:**
  - `https://docs.kernel.org/arch/x86/x86_64/mm.html` — the authoritative layout table, updated per release; cite it rather than reproducing constants.
  - Intel SDM Vol. 3A, ch. 4 "Paging" — canonical addressing, 4- and 5-level paging, and the `#GP` on a non-canonical address.
  - `https://docs.kernel.org/mm/index.html` — the memory-management documentation index this folder repeatedly returns to.
  - LWN, *"Five-level page tables"* (`https://lwn.net/Articles/717293/`) — why the opt-in behaviour above 47 bits exists, which is otherwise baffling.

### `page-tables-and-the-walk.md` — Page Tables and the Walk **[Lab host=qemu-gdb]**

- **Opens with:** the translation problem stated as a size problem. A flat table mapping every 4 KiB page of a 48-bit space would need 512 GB of table per process, so the table is made sparse by making it a tree — and every property of paging, including huge pages and the cost of a miss, falls out of that one decision.
- **Sections:**
  - `## Four levels, and what each index is` — the 48-bit address split into 9+9+9+9+12 bits: PGD, P4D/PUD, PMD, PTE, offset. Show the split of one concrete address, with the actual index values computed. This worked example is the page's core.
  - `## The walk, with real numbers` — from `CR3`, take the top nine bits as an index, read the entry, mask off the flags to get the next table's physical address, repeat. Do it for the same concrete address across all four levels and arrive at a physical address. Show the arithmetic.
  - `## Kernel names for the levels` — `pgd_t`, `p4d_t`, `pud_t`, `pmd_t`, `pte_t`, and the accessor macros (`pgd_offset`, `pud_offset`, `pmd_offset`, `pte_offset_map`). Explain that `p4d` exists as a folded no-op level on 4-level configurations, which is why kernel code that reads as five levels runs on four.
  - `## The PTE bits` — the WaveDrom anchor below, then a table with a row per bit explaining what the *kernel* does with it, not just what the hardware does: `Present` (and the trick that a non-present PTE's other bits are free for swap entries — forward-link to `./swap-and-zswap.md`), `R/W` (and its COW use), `U/S`, `A` and `D` (used by reclaim), `NX`, and the PAT bits.
  - `## Huge pages as a stopped walk` — a PMD entry with the page-size bit set terminates the walk two levels early and maps 2 MiB. State it once here, in mechanical terms, and let `./hugepages-and-thp.md` own the policy.
  - `## Where the page tables themselves live` — ordinary physical pages, allocated by the kernel, freed with the address space, and accounted (`/proc/PID/status`'s `VmPTE`). Note that a sparse 1 TB mapping costs real memory in tables, which is the fact folder 06's fork page referred to.
  - `## arm64` — `:::note`: same tree idea, different entry format and different level names, with a configurable granule size (4 KiB, 16 KiB, 64 KiB) that changes the number of levels. The kernel's `pgd`/`pud`/`pmd`/`pte` vocabulary is architecture-independent by design, which is why generic mm code compiles for both.
  - `<Lab host="qemu-gdb" title="Walk a page table by hand in GDB" time="30 min">` — in the QEMU lab: break somewhere with a user task current, read `CR3` (`p $cr3` or via the `lx` helpers), pick a user address from `maps`, then read each level's entry with `x/gx` on the direct-map alias of the table page, masking the flags at each step, until you reach the PTE — then compare the resulting physical frame with what `/proc/PID/pagemap` reports for that address. Show every command and its output. "If it fails": reading `/proc/PID/pagemap` needs `CAP_SYS_ADMIN` for the physical frame numbers (unprivileged reads return zeros, which looks like a bug and is a deliberate hardening), and the direct-map alias needs `page_offset_base`, which KASLR moves — read it from the running kernel rather than assuming.
- **Anchor:** a WaveDrom `reg` strip of a 4 KiB PTE: `P`(0), `R/W`(1), `U/S`(2), `PWT`(3), `PCD`(4), `A`(5), `D`(6), `PAT`(7), `G`(8), then the physical frame field, then `NX`(63). Verified against Intel SDM ch. 4 before committing. Title: "One 4 KiB page-table entry: what the hardware checks on every access, and the two bits reclaim reads."
- **Second visual:** a Mermaid `flowchart LR` of the four-level walk with the nine-bit index feeding each level, captioned with the concrete address used in the worked example.
- **KernelFacts:** `structure` — `[["pgd_t / pud_t / pmd_t / pte_t", "arch/x86/include/asm/pgtable_types.h"]]`; `path` — `"CR3 → pgd_offset() → pud_offset() → pmd_offset() → pte_offset_map() → pfn"`; `observe` — `grep VmPTE /proc/self/status && sudo grep -c . /proc/self/pagemap >/dev/null`; `trap` — "Page tables are not free. A process with a large sparse mapping pays real physical memory for the tables that describe it, which is why `VmPTE` exists as a separate line in `/proc/PID/status` and why a fork of such a process is not cheap."
- **References:**
  - Intel SDM Vol. 3A, ch. 4 "Paging" — the entry formats, the bit meanings, and the walk; the authority for the WaveDrom strip.
  - `<Src file="arch/x86/include/asm/pgtable_types.h" symbol="pteval_t" />` — the kernel's own bit definitions, which is the cross-check on the SDM reading.
  - `https://docs.kernel.org/mm/page_tables.html` — the kernel's description of the folded-level scheme and the accessor macros.
  - `https://docs.kernel.org/admin-guide/mm/pagemap.html` — the `/proc/PID/pagemap` format used in the lab, including what unprivileged readers are denied.

- [ ] **Step 1: Write `the-virtual-address-space.md`** to the brief above.
- [ ] **Step 2: Verify the PTE bit layout** against the Intel SDM and `pgtable_types.h` before drawing the WaveDrom strip. A wrong bit position here propagates into three later pages.
- [ ] **Step 3: Write `page-tables-and-the-walk.md`**, with a real worked address rather than a schematic one.
- [ ] **Step 4: Run the GDB walk lab** and paste the real session, including the `pagemap` cross-check.
- [ ] **Step 5: Verify** `page_offset_base`, the `*_offset` accessor names, and `VmPTE` against Elixir v6.18 and against a real `/proc/self/status`.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write the virtual address space and the page-table walk"
```

---

## Task 20: Folder 08 — the TLB, and the kernel's address-space description

**Files:**
- Modify: `docs/linux/08-memory-management/tlb-and-address-space-switching.md`
- Modify: `docs/linux/08-memory-management/mm-struct-and-vmas.md`

**Interfaces:**
- Consumes: `08/page-tables-and-the-walk` (Task 19) and `computer-science/memory-hierarchy/tlb-and-address-translation-hardware` (Task 3) — the hardware page owns TLB structure, this page owns Linux's management of it.
- Produces: `08/mm-struct-and-vmas`, the second declared prerequisite of `08/the-page-fault-handler`. The spec requires both to be written before the fault handler.

### `tlb-and-address-space-switching.md` — The TLB and Address-Space Switching

- **Opens with:** the software problem the hardware creates. The TLB is invisible and automatic until the kernel changes a mapping, at which point every cached copy of that translation on every CPU becomes a correctness hazard — and x86-64 gives the kernel no hardware broadcast to fix it with. Everything on this page follows from that missing instruction.
- **Sections:**
  - `## What the kernel must invalidate, and when` — a table: unmap (must), reduce permissions (must), increase permissions (usually not — a stale restrictive entry costs only a spurious fault), change the physical frame (must), and free a page table (must, and this is the subtle one). Explain the asymmetry, because knowing which direction is safe explains half the code.
  - `## Local invalidation` — `INVLPG` for one page, a `CR3` reload for the whole non-global set, and the `PGE`/global-bit exception for kernel mappings that must survive a switch.
  - `## Shootdown` — the protocol: find which CPUs may have this `mm` loaded (`mm_cpumask`), send an IPI to each, each acknowledges after invalidating, and the initiator waits. Give the cost shape — an IPI round trip per CPU, serialised in the worst case — and say plainly that this is why `munmap` of a mapping used by many threads is expensive in a way `mmap` is not.
  - `## PCID, and how Linux uses it` — a small number of ASIDs recycled per CPU, so switching to a recently-used `mm` does not flush. Note the two constraints that make it less of a win than it sounds: the tag space is small, and a shootdown must then invalidate *tagged* entries, which is more bookkeeping.
  - `## KPTI's cost lands here` — with page-table isolation, entering and leaving the kernel swaps `CR3` twice per crossing. With PCID the entries survive; without it, every syscall flushes. This is the concrete reason the mitigation's cost varies so much between machines, and it ties back to `../05-syscalls-and-the-boundary/the-entry-path.md`.
  - `## Lazy TLB` — a kernel thread borrows the previous `mm` (`active_mm`) rather than switching, precisely to avoid a `CR3` write. Link back to `../06-processes-and-threads/task-struct-the-anatomy-of-a-task.md`, which introduced `active_mm`.
  - `## Measuring it` — `perf stat -e dTLB-load-misses,iTLB-load-misses` and the `tlb_flush` tracepoint if present at v6.18. Say what a high miss rate suggests (a working set exceeding TLB reach → the huge-page conversation) and what a high shootdown rate suggests (an unmapping-heavy workload).
  - `## arm64` — `:::note`: `TLBI` instructions broadcast within the inner-shareable domain, so arm64 does not need the IPI protocol at all. This is a genuine architectural advantage and it is why arm64's `flush_tlb_*` implementations look so much simpler.
- **Anchor:** a Mermaid `sequenceDiagram` — CPU 0 (initiator), CPU 1, CPU 2 — showing an `munmap` triggering an IPI to the two CPUs that have the `mm` loaded, each invalidating and acknowledging, and the initiator only then completing. Caption: "A TLB shootdown on x86-64: the unmapping CPU cannot proceed until every other CPU that might have the translation has thrown it away."
- **KernelFacts:** `structure` — `[["struct mm_struct", "include/linux/mm_types.h"], ["struct flush_tlb_info", "arch/x86/include/asm/tlbflush.h"]]` (verify); `path` — `"munmap() → zap_page_range_single() → flush_tlb_mm_range() → flush_tlb_multi() → IPI → local invalidate"` (verify each at v6.18); `observe` — `perf stat -e dTLB-load-misses,dTLB-loads -- ./workload`; `trap` — "Unmapping memory is more expensive than mapping it. `mmap` is bookkeeping; `munmap` is bookkeeping plus a synchronous cross-CPU operation, which is why allocator designs go to such lengths to avoid returning memory to the kernel."
- **References:**
  - `<Src file="arch/x86/mm/tlb.c" symbol="flush_tlb_mm_range" />` — the shootdown implementation, with the `mm_cpumask` narrowing visible.
  - Intel SDM Vol. 3A, ch. 4.10 — what the hardware caches, what invalidates it, and the PCID rules.
  - LWN, *"The current state of kernel page-table isolation"* (`https://lwn.net/Articles/741878/`) — the cost model for KPTI, and why PCID matters so much to it; pre-dates v6.18, and the mechanism is unchanged.
  - `https://docs.kernel.org/arch/x86/pti.html` — the in-tree PTI documentation; confirm the path at v6.18.

### `mm-struct-and-vmas.md` — `mm_struct` and VMAs **[WAH]**

- **Opens with:** the kernel's own description of an address space, and why it is not the page tables. Page tables say what is mapped *right now*; the VMA list says what the process is *entitled* to have mapped and on what terms. Almost everything a process does to its memory is an operation on that second structure, and the page tables catch up lazily.
- **Sections:**
  - `## `mm_struct`` — one per address space, shared by every thread in the process, refcounted twice (`mm_users` for threads, `mm_count` for lazy references) — explain why two counters exist, because it is a genuinely instructive piece of lifetime design and folder 04 set up the vocabulary.
  - `## `vm_area_struct`` — a contiguous range with uniform properties: start, end, flags, a `vm_ops` table, and optionally a file and offset. Show the eight fields that matter as a Mermaid `classDiagram`, not a dump.
  - `## The maple tree` — VMAs are indexed by a maple tree at v6.18, replacing the older red-black tree plus linked list. Say what changed and why (RCU-friendly lookup, better cache behaviour) and, critically, that **older documentation and books describe the rbtree** — a reader looking for `vma->vm_next` will not find it. Verify the current lookup API names before writing them.
  - `## VMA flags` — a table of the ones that matter: `VM_READ`/`WRITE`/`EXEC`, `VM_SHARED`, `VM_GROWSDOWN`, `VM_LOCKED`, `VM_DONTCOPY`, `VM_HUGEPAGE`. Each with the user-space call that sets it, which is what makes them memorable.
  - `## What actually happens` **[WAH]** — an `mprotect` on the middle of a mapping. The VMA must be *split* into three, the middle one gets new flags, the page tables for that range are updated, and a TLB shootdown follows. Then show the `maps` file before and after, with one line becoming three. The lesson: `/proc/PID/maps` line count is a function of how much the process has fiddled with permissions, and a program that mprotects in a loop can accumulate thousands of VMAs — which has a real cost, since `find_vma` and fork both walk them.
  - `## Merging` — the reverse: adjacent VMAs with identical properties and compatible files are merged on creation. This is why two adjacent `mmap`s sometimes show as one line and sometimes do not, which otherwise looks arbitrary.
  - `## `vm_ops`, and file-backed mappings` — the operations table with `fault`, `map_pages`, and `page_mkwrite`; a filesystem or driver supplies it, and this is the hook the page-fault handler calls. Name it here, because the next task's page needs it to exist.
  - `## `mmap_lock`` — the per-`mm` reader-writer semaphore that serialises VMA changes, its historical contention problems, and per-VMA locking at v6.18 for the fault fast path. **Verify the state of per-VMA locking at the pinned version** and link to `../09-concurrency-and-locking/rwlocks-and-rwsems.md`, which names `mmap_lock` as its canonical example.
- **Anchor:** a Mermaid `classDiagram` with `mm_struct` at the centre, its maple tree of `vm_area_struct`s, and each VMA's optional `vm_file` and `vm_ops`, annotated with the `/proc/PID/maps` column each field produces. Caption: "The structures behind one line of `/proc/PID/maps`, and which field produces which column."
- **KernelFacts:** `structure` — `[["struct mm_struct", "include/linux/mm_types.h"], ["struct vm_area_struct", "include/linux/mm_types.h"]]`; `path` — `"mmap() → get_unmapped_area() → vma_merge() or new VMA → insert into mm->mm_mt → no page tables yet"` (verify the v6.18 helper names — VMA code moved to `mm/vma.c`); `observe` — `wc -l /proc/self/maps && grep -c '' /proc/1/maps`; `trap` — "A VMA is not memory and not a page-table entry. It is a promise about a range, and the page tables for that range may be entirely empty — which is why `mmap` of a gigabyte is instant and why the first touch of each page is not."
- **References:**
  - `<Src file="include/linux/mm_types.h" symbol="vm_area_struct" />` — the definition, with comments that explain the flag groups.
  - `https://docs.kernel.org/mm/index.html`, the maple-tree documentation — what replaced the rbtree and why; check the exact page name at v6.18.
  - `man 2 mmap` and `man 2 mprotect` — the operations that create and split VMAs, and the flag-to-`VM_*` mapping.
  - LWN, *"Introducing maple trees"* (`https://lwn.net/Articles/845507/`) — the data structure's rationale, useful because most existing mm writing predates it.

- [ ] **Step 1: Write `tlb-and-address-space-switching.md`** to the brief above.
- [ ] **Step 2: Write `mm-struct-and-vmas.md`** to the brief above.
- [ ] **Step 3: Demonstrate the VMA split for real** — a small program that mmaps one region and mprotects its middle third — and paste the `maps` output before and after.
- [ ] **Step 4: Verify** `flush_tlb_mm_range`, `flush_tlb_multi`, the maple-tree field name (`mm_mt`), the VMA lookup API, per-VMA locking status, and `mm_users`/`mm_count` against Elixir v6.18. **The rbtree-to-maple-tree change makes older knowledge actively wrong here** — check every structural claim.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write TLB management and the mm_struct/VMA model"
```

---

## Task 21: Folder 08 — the fault handler, and demand paging

**Files:**
- Modify: `docs/linux/08-memory-management/the-page-fault-handler.md`
- Modify: `docs/linux/08-memory-management/demand-paging-and-cow.md`

**Interfaces:**
- Consumes: `08/page-tables-and-the-walk` and `08/mm-struct-and-vmas` (Tasks 19–20), plus `02/the-life-of-a-page-fault` from Phase 1, which told this story shallowly and links here for the depth.
- Produces: `08/the-page-fault-handler`, the declared prerequisite of `08/demand-paging-and-cow`, and the mechanism every later page in the folder refers back to.

### `the-page-fault-handler.md` — The Page Fault Handler **[Lab host=qemu-gdb]**

- **Opens with:** the reframing this page exists for — a page fault is not an error. It is the mechanism by which almost all memory in Linux is actually allocated, and the handler's job is less "report a problem" than "finish a job that was deliberately left unfinished". The `SIGSEGV` case is the *rare* branch.
- **Sections:**
  - `## From the exception to C code` — the CPU pushes an error code and puts the faulting address in `CR2`, the IDT vector reaches `exc_page_fault`, and the handler splits immediately on whether the address is a kernel or user address. Show the error-code bits as a small table (present, write, user, reserved, instruction-fetch, protection-key, shadow-stack — verify the current bit list) because the handler's first decisions are made entirely from them.
  - `## The classification tree` — the heart of the page. A decision tree over: is there a VMA? (no → `SIGSEGV`, unless it is a stack-growth case), do the VMA's permissions allow this access? (no → `SIGSEGV`), is the PTE absent or present-but-restricted? and then the sub-cases: anonymous first touch, file-backed with no page cached, present-but-read-only COW, a swap entry, and a NUMA hinting fault. Give each leaf one line naming the function that handles it.
  - `## Locking, and the fast path` — the fault path takes `mmap_lock` for reading, and at v6.18 the common case can be handled under a per-VMA lock without touching `mmap_lock` at all. Say why this mattered enough to change (fault-heavy multithreaded workloads serialised on one semaphore) and **verify the current state before writing it**.
  - `## Minor and major` — the distinction defined precisely: a minor fault is resolved without I/O, a major one required reading from a device. State that the ratio, not the absolute count, is what matters, and that minor faults in the millions are entirely normal.
  - `## Where a SIGSEGV is actually decided` — one short section pinpointing it, because readers expect the answer to be "the MMU" and it is not: the hardware only reports; `bad_area` and its relatives decide. Note the kernel-address case too — a fault on a kernel address that is not in the exception table is an oops, which ties back to `../05-syscalls-and-the-boundary/copying-data-across-the-boundary.md`.
  - `## The path is simplified` — state it, per the spec's guardrail: hugepage faults, `userfaultfd`, KFENCE, and the retry cases are elided. `<Src file="mm/memory.c" symbol="handle_mm_fault" />` is the real entry point.
  - `<Lab host="qemu-gdb" title="Break on a real page fault" time="25 min">` — in the QEMU lab, break on `handle_mm_fault`, continue until a user process faults, then print the faulting address, the VMA found for it, and the VMA's flags; step to the branch taken and confirm it is `do_anonymous_page` for a first touch. Show the session. "If it fails": faults are extremely frequent, so an unconditional breakpoint will fire immediately and constantly — set a condition on the `comm` of the current task, and the page should show that condition rather than leaving the reader to discover the problem.
- **Anchor:** a Mermaid `flowchart TB` of the classification tree from `exc_page_fault` to each leaf handler, with the `SIGSEGV` and oops exits drawn as terminal nodes. Caption: "Every branch a page fault can take, and the one leaf out of eight that means your program did something wrong."
- **KernelFacts:** `structure` — `[["struct vm_fault", "include/linux/mm.h"], ["struct vm_area_struct", "include/linux/mm_types.h"]]`; `path` — `"exc_page_fault() → do_user_addr_fault() → lock_vma_under_rcu() or mmap_read_lock() → handle_mm_fault() → handle_pte_fault() → do_anonymous_page()"` (verify every name at v6.18); `observe` — `perf stat -e page-faults,minor-faults,major-faults -- ls`; `trap` — "A page fault is the normal way memory gets allocated, not an error condition. A process taking a hundred thousand minor faults during startup is behaving exactly as designed."
- **References:**
  - `<Src file="mm/memory.c" symbol="handle_mm_fault" />` — the architecture-independent core, and the function every architecture's fault handler converges on.
  - `<Src file="arch/x86/mm/fault.c" symbol="do_user_addr_fault" />` — the x86-64 half, where the error code is decoded and the decisions about `SIGSEGV` are made.
  - Intel SDM Vol. 3A, ch. 4.7 "Page-Fault Exceptions" — the error-code bit definitions the WaveDrom-free table on this page reproduces.
  - LWN, *"Per-VMA locking"* coverage — why the fault path stopped serialising on `mmap_lock`; check whether the feature is enabled by default at v6.18 and say so.

### `demand-paging-and-cow.md` — Demand Paging and Copy-on-Write **[WAH]** **[Misc]**

- **Opens with:** the policy the fault handler implements — never do work until someone proves they need it. Address space is free, physical pages are not, and Linux issues the first liberally on the promise that most of it will never be touched. This is why memory accounting on Linux confuses everyone, and the confusion is a direct consequence of a deliberate design.
- **Sections:**
  - `## First touch` — `mmap` creates a VMA and no pages; the first read of an anonymous page maps the shared zero page read-only; the first *write* allocates a real page. Note the read/write asymmetry explicitly, because it means a program that only reads its freshly-allocated array uses almost no memory.
  - `## The zero page` — one physical page of zeros shared by every process for every untouched anonymous read. Cheap, elegant, and the reason `calloc` of a large region can be nearly free.
  - `## COW after fork` — the mechanism from folder 06 stated in mm terms: both PTEs marked read-only, `do_wp_page` on the first write, and the refcount check that lets the *last* remaining owner reuse the page in place rather than copying it. That last optimisation is worth a paragraph, because it is why a fork-then-exit child costs almost nothing.
  - `## What actually happens` **[WAH]** — `malloc(100 * 1024 * 1024 * 1024)` on a machine with 8 GB, succeeding. Walk it: glibc calls `mmap`, the kernel creates a VMA, overcommit accounting decides whether to allow it, and no physical page is touched. Show the `maps` entry and an RSS of near zero. Then touch one page per gigabyte and show RSS rising by exactly that much. The reader should end knowing that a successful allocation is a *promise*, and that the machine may not be able to keep it.
  - `## Overcommit modes` — `vm.overcommit_memory` 0 (heuristic), 1 (always), 2 (strict, with `overcommit_ratio`/`kbytes`), and what each actually does. Give the practical guidance honestly: mode 2 makes allocation failures happen at `malloc` instead of at the OOM killer, which is what some workloads want and what most software is not written to handle.
  - `## `MAP_POPULATE`, `mlock`, and pre-faulting` — the three ways to demand the pages up front, when it is worth it (real-time work, where a fault is a latency spike), and what it costs.
  - `## Where the accounting goes wrong` — `Committed_AS` versus `CommitLimit` in `/proc/meminfo`, and why VSZ is nearly meaningless. Hand the full treatment to `./what-free-and-rss-really-say.md`.
  - `## Misconceptions` **[Misc]** — (1) "malloc allocates memory" — it reserves address space; the kernel allocates on first write; (2) "if malloc succeeded, the memory is mine" — under the default overcommit heuristic it is a promise the kernel may fail to keep, and the failure arrives as the OOM killer rather than a `NULL`; (3) "COW means fork is free" — it defers the cost to the first write of each page.
- **Anchor:** a Mermaid `stateDiagram-v2` for one anonymous page — Unmapped → (read) Zero-page-mapped-read-only → (write) Privately-mapped-writable, plus the COW branch from Shared-read-only after a fork. Caption: "One anonymous page's states, and the two events that move it: the first read, and the first write."
- **KernelFacts:** `structure` — `[["struct vm_fault", "include/linux/mm.h"], ["empty_zero_page", "arch/x86/kernel/head_64.S"]]` (verify the symbol and its location); `path` — `"first write → handle_pte_fault() → do_anonymous_page() → alloc_zeroed_user_highpage_movable() → set_pte_at()"` (verify at v6.18); `observe` — `cat /proc/meminfo | grep -E 'Committed_AS|CommitLimit' && cat /proc/sys/vm/overcommit_memory`; `trap` — "A successful `malloc` is not a guarantee of memory. Under the default overcommit policy the kernel has promised address space, and the bill arrives later — as a page fault that cannot be satisfied, and then as the OOM killer."
- **References:**
  - `https://docs.kernel.org/mm/overcommit-accounting.html` — the three modes, defined by the kernel itself, including exactly what the heuristic in mode 0 does.
  - `<Src file="mm/memory.c" symbol="do_anonymous_page" />` — the first-touch path, including the zero-page shortcut for reads.
  - `man 2 mmap`, the `MAP_NORESERVE` and `MAP_POPULATE` sections — the interface-level controls over this behaviour.
  - `man 5 proc`, the `/proc/meminfo` fields — for `Committed_AS` and `CommitLimit`.

- [ ] **Step 1: Write `the-page-fault-handler.md`** to the brief above.
- [ ] **Step 2: Run the GDB fault lab**, including working out the breakpoint condition, and paste the real session.
- [ ] **Step 3: Write `demand-paging-and-cow.md`** to the brief above.
- [ ] **Step 4: Run the 100 GB allocation demonstration** and paste the real `maps` and RSS figures, naming the machine's memory size and overcommit setting.
- [ ] **Step 5: Verify** `exc_page_fault`, `do_user_addr_fault`, `handle_mm_fault`, `handle_pte_fault`, `do_anonymous_page`, `do_wp_page`, `vm_fault`, `lock_vma_under_rcu`, and `empty_zero_page` against Elixir v6.18, plus the page-fault error-code bit list against the SDM.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write the page fault handler and demand paging with COW"
```

---

## Task 22: Folder 08 — the allocators

**Files:**
- Modify: `docs/linux/08-memory-management/the-page-allocator.md`
- Modify: `docs/linux/08-memory-management/slab-slub-and-kmalloc.md`
- Modify: `docs/linux/08-memory-management/vmalloc-and-choosing-an-allocator.md`

**Interfaces:**
- Consumes: `08/the-virtual-address-space` (Task 19).
- Produces: `08/the-page-allocator`, the declared prerequisite of `08/slab-slub-and-kmalloc`, `08/folios-and-compound-pages`, and `08/numa-and-memory-policy`. The GFP-flag vocabulary established here is used by every driver page in Phase 4.

### `the-page-allocator.md` — The Page Allocator

- **Opens with:** the bottom of the stack. Every other allocator in the kernel — slab, vmalloc, the page cache, the stack allocator — ultimately asks this one for physical pages, and it must answer under constraints nothing above it has: it cannot fail silently, it may be called from a context that cannot sleep, and it must keep contiguous memory available for callers who genuinely need it.
- **Sections:**
  - `## Zones, and why they exist` — `ZONE_DMA`, `ZONE_DMA32`, `ZONE_NORMAL`, `ZONE_MOVABLE`, and (historically) `ZONE_HIGHMEM`. Each exists because some consumer cannot use arbitrary physical addresses. State that on modern x86-64 the interesting ones are `DMA32` and `NORMAL`, and that `HIGHMEM` is a 32-bit artefact readers will meet in old books.
  - `## The buddy allocator` — free lists per order 0–10, splitting a larger block when the requested order is empty, and coalescing with the buddy on free when the buddy is also free. Explain why the buddy of a block is computable with one XOR, because that is the trick that makes coalescing O(1).
  - `## Orders, and what asks for what` — a table: order 0 (one page, almost everything), order 1–3 (kernel stacks, some slab caches), order 9 (a 2 MiB huge page). Note that high-order allocations get progressively less reliable as uptime increases, which is the fragmentation story.
  - `## GFP flags` — the WaveDrom anchor below, then the semantics table that actually matters: `GFP_KERNEL` (may sleep, may do I/O, may reclaim), `GFP_ATOMIC` (may not sleep, may dip into reserves, may fail), `GFP_NOWAIT`, `GFP_NOFS` and `GFP_NOIO` (may not re-enter the filesystem or block layer — and say *why*: a filesystem allocating during writeback that triggers reclaim that calls back into the filesystem is a deadlock), and `__GFP_ZERO`, `__GFP_NOWARN`, `__GFP_RETRY_MAYFAIL`. Each row: what it permits, what it forbids, and the deadlock or failure it exists to prevent.
  - `## Watermarks` — min, low, and high per zone: crossing `low` wakes `kswapd`, crossing `min` forces the allocating task into direct reclaim, and the reserve below `min` is for allocations that must not fail. This is the interface between allocation and reclaim, so state it here and let `./reclaim-lru-and-kswapd.md` own the reclaim side.
  - `## Fragmentation, and compaction` — external fragmentation as the failure mode for high-order allocations; migration types (movable, unmovable, reclaimable) that group pages by whether they *can* be moved; and compaction as the defragmenter. Note that THP allocation is the main consumer of compaction and the main source of its latency cost.
  - `## Per-CPU page lists` — order-0 allocations come from a per-CPU cache to avoid the zone lock, which is the same "eliminate sharing" idea folder 09 generalises. Link `../09-concurrency-and-locking/per-cpu-data.md`.
- **Anchor:** a WaveDrom `reg` strip of the low GFP bits — `___GFP_DMA`(0), `___GFP_HIGHMEM`(1), `___GFP_DMA32`(2), `___GFP_MOVABLE`(3), `___GFP_RECLAIMABLE`(4), `___GFP_HIGH`(5), `___GFP_IO`(6), `___GFP_FS`(7) — **verified against `<Src file="include/linux/gfp_types.h" />` at v6.18**, since these positions have changed historically. Title: "The GFP bits that decide what the allocator is allowed to do to satisfy you."
- **Second visual:** a Mermaid `flowchart TB` of the buddy split for an order-2 request served from an order-5 block, then the coalesce on free.
- **KernelFacts:** `structure` — `[["struct zone", "include/linux/mmzone.h"], ["struct free_area", "include/linux/mmzone.h"]]`; `path` — `"alloc_pages() → get_page_from_freelist() → watermark check → buddy split → per-CPU list or free_area"` (verify the v6.18 entry-point name — alloc-tagging added `_noprof` variants); `observe` — `cat /proc/buddyinfo && cat /proc/zoneinfo | head -30`; `trap` — "`GFP_ATOMIC` is not 'faster' — it means 'I cannot sleep, so you may not reclaim on my behalf'. It buys access to a small reserve and a much higher chance of returning NULL, which is why every `GFP_ATOMIC` call site must handle failure."
- **References:**
  - `<Src file="include/linux/gfp_types.h" />` — the flag definitions with the best comments in mm; the authority for both the strip and the table.
  - `https://docs.kernel.org/mm/page_frags.html` and the mm documentation index — for the surrounding allocator documentation at v6.18.
  - `https://docs.kernel.org/admin-guide/mm/concepts.html` — zones and watermarks explained by the kernel for administrators, which is the right level for this page's zone section.
  - Gorman, *Understanding the Linux Virtual Memory Manager* — `https://www.kernel.org/doc/gorman/`. Free, and the clearest long-form treatment of the buddy allocator; written against 2.4/2.6, so structural claims must be checked against v6.18 while the *algorithm* is unchanged.

### `slab-slub-and-kmalloc.md` — Slab, SLUB, and `kmalloc` **[Lab host=any-linux]**

- **Opens with:** the mismatch the slab layer resolves. The page allocator deals in 4 KiB units; the kernel allocates `struct dentry`s of 192 bytes, millions of them, constantly. Rounding each to a page would waste 95% of memory, and going to the page allocator each time would be far too slow. The slab layer is the object cache that sits between.
- **Sections:**
  - `## The idea` — a cache per object type, pages carved into same-sized objects, a freelist per cache, and objects returned to the cache rather than to the page allocator. Add the historical point that the original design also kept objects *constructed*, and note that this survives only vestigially.
  - `## SLUB` — the implementation at v6.18: per-CPU active slabs, a freelist threaded through the free objects themselves (so no separate metadata array), and per-node partial lists. Note that SLAB was removed and SLOB long gone — **verify what allocators exist at v6.18** and do not describe options that no longer exist.
  - `## `kmalloc` and size classes` — `kmalloc` is a set of generic caches at power-of-two sizes plus a couple of extras. A 100-byte request gets a 128-byte object, and the 28 bytes are gone. Give the class list and say plainly that a struct sized just over a class boundary wastes nearly half its allocation — which is why the size of a hot structure is a real design consideration.
  - `## `kmem_cache_create` for your own objects` — the interface, the alignment and flag arguments, and the two reasons to bother: exact sizing for a hot object, and a named entry in `/proc/slabinfo` that makes a leak findable. That second reason is the practical one.
  - `## Where the objects come from` — the slab allocator asks the page allocator; a cache growing means order-0 (or higher) allocations. So a slab problem is eventually a page-allocator problem, which is why `slabtop` and `/proc/buddyinfo` are read together.
  - `## Debug options` — `slub_debug` with its per-cache selection, red zoning, poisoning, and owner tracking. Name what each catches, and note the overhead. Cross-link forward in prose to the sanitizers page in folder 17 without a link.
  - `<Lab host="any-linux" title="Find where kernel memory is going" time="15 min">` — (1) `sudo slabtop -o -s c` and read the top five caches; (2) `sudo grep -E '^(dentry|inode_cache|kmalloc-)' /proc/slabinfo` and decode the columns using the header line; (3) create a million small files in a tmpfs, watch `dentry` and `inode_cache` grow, drop caches, watch them shrink. Expected output at each step. Add a `:::warning` that `echo 2 > /proc/sys/vm/drop_caches` discards useful cache and will slow the machine down temporarily — it is not destructive, but it is not free. "If it fails": `/proc/slabinfo` is root-only on most distributions, and a machine with `CONFIG_SLUB_TINY` will show a different cache set.
- **Anchor:** a Mermaid `flowchart LR` of one slab page carved into objects, with the freelist drawn as pointers threaded through the free objects and a per-CPU active slab beside a per-node partial list. Caption: "A SLUB cache: the free list lives inside the free objects, which is why there is no separate metadata to maintain."
- **KernelFacts:** `structure` — `[["struct kmem_cache", "include/linux/slub_def.h"], ["struct kmem_cache_cpu", "include/linux/slub_def.h"]]` (verify the header at v6.18 — slab headers were consolidated into `mm/slab.h`); `path` — `"kmalloc() → kmalloc_caches[size class] → per-CPU freelist → slab page → alloc_pages()"`; `observe` — `sudo slabtop -o -s c | head -15`; `trap` — "`kmalloc(96)` does not allocate 96 bytes. It allocates the smallest size class that fits, so a struct that grows from 128 to 136 bytes can increase its memory use by 87% overnight."
- **References:**
  - `https://docs.kernel.org/mm/slub.html` — the in-tree SLUB documentation, including every `slub_debug` option.
  - `<Src file="mm/slub.c" symbol="kmem_cache_alloc" />` — the fast path, which is short and shows the per-CPU freelist directly.
  - `man 5 slabinfo` and `man 1 slabtop` — the field definitions for the lab.
  - LWN's coverage of the SLAB removal — cite the specific article; it is the reason older material describing three allocators is now wrong.

### `vmalloc-and-choosing-an-allocator.md` — `vmalloc` and Choosing an Allocator

- **Opens with:** the distinction that decides the answer — physically contiguous versus virtually contiguous. Some consumers genuinely require the first (a device doing DMA across a buffer, a page-table page), most only think they do, and `vmalloc` exists to serve the majority who do not, at a price.
- **Sections:**
  - `## What `vmalloc` does` — allocates individual pages, then builds page-table entries mapping them consecutively in the vmalloc region. The result is one contiguous virtual range over scattered physical pages.
  - `## What it costs` — page-table setup on allocation, a TLB entry per 4 KiB (no huge-page mapping in the general case), potential shootdowns on free, and a limited region size. Say plainly why kernel code prefers `kmalloc` when it can: the direct map is already mapped and often huge-page backed, so `kmalloc` memory costs no extra TLB pressure at all.
  - `## When you actually need physical contiguity` — DMA without an IOMMU, and anything a device or the hardware indexes directly. Note that with an IOMMU the requirement often disappears, which is a point folder 14 will develop.
  - `## `vmalloc` versus `kvmalloc`` — the pragmatic helper: try `kmalloc`, fall back to `vmalloc` for large sizes. Say when it is right (a large buffer that does not need contiguity and is usually small) and when it is wrong (anything that will be DMAed).
  - `## The decision table` — the page's anchor and its reason for existing: rows for `kmalloc`/`kzalloc`, `kvmalloc`, `vmalloc`, `alloc_pages`, `kmem_cache_alloc`, `devm_kzalloc`, and the per-CPU allocator. Columns: physically contiguous?, may sleep?, size range, freed by, and the typical use. Every row must be checkable against the source.
  - `## `devm_*`, briefly` — device-managed allocation that is freed automatically when the driver unbinds. Two sentences, because folder 14 owns it and driver readers will meet it constantly.
  - `## Context decides more than size` — the closing rule: the question "which allocator" is usually settled by "may this code sleep?" before it is settled by size, and that is a folder 09 question. Link `../09-concurrency-and-locking/why-kernel-concurrency-is-different.md`.
- **Anchor:** the decision table above.
- **KernelFacts:** `structure` — `[["struct vm_struct", "include/linux/vmalloc.h"]]`; `path` — `"vmalloc() → __vmalloc_node_range() → alloc_pages() per page → map_kernel_range() → contiguous virtual range"` (verify the v6.18 helper names); `observe` — `sudo cat /proc/vmallocinfo | head && grep -E 'VmallocTotal|VmallocUsed' /proc/meminfo`; `trap` — "`vmalloc` memory is not usable for DMA even though it looks like one buffer. The device sees physical addresses, and the physical pages behind a `vmalloc` range are scattered — passing one to a DMA API without a scatter-gather list corrupts memory."
- **References:**
  - `<Src file="mm/vmalloc.c" symbol="__vmalloc_node_range" />` — the allocation path, where the per-page allocation and the mapping step are both visible.
  - `https://docs.kernel.org/core-api/memory-allocation.html` — the kernel's own "which allocator should I use" guidance; the decision table on this page must agree with it.
  - `https://docs.kernel.org/core-api/mm-api.html` — the API reference for every function named in the table.
  - `man 5 proc`, the `/proc/meminfo` `Vmalloc*` fields — for the observation command.

- [ ] **Step 1: Verify the GFP bit positions** against `gfp_types.h` at v6.18 **before** drawing the WaveDrom strip.
- [ ] **Step 2: Write `the-page-allocator.md`** to the brief above.
- [ ] **Step 3: Write `slab-slub-and-kmalloc.md`** to the brief above, after confirming which slab allocators exist at v6.18.
- [ ] **Step 4: Run the slab lab** on a real machine and paste real `slabtop` and `slabinfo` output.
- [ ] **Step 5: Write `vmalloc-and-choosing-an-allocator.md`**, and check every row of the decision table against `https://docs.kernel.org/core-api/memory-allocation.html` — where the page and the kernel's own guidance disagree, the kernel is right.
- [ ] **Step 6: Verify** `alloc_pages`, `zone`, `free_area`, `kmem_cache`, `kmalloc_caches`, `__vmalloc_node_range`, and `vm_struct` against Elixir v6.18.
- [ ] **Step 7: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write the page allocator, slab, and allocator selection"
```

---

## Task 23: Folder 08 — folios, and the page cache

**Files:**
- Modify: `docs/linux/08-memory-management/folios-and-compound-pages.md`
- Modify: `docs/linux/08-memory-management/the-page-cache.md`

**Interfaces:**
- Consumes: `08/the-page-allocator` (Task 22).
- Produces: `08/the-page-cache`, the declared prerequisite of `08/writeback-and-fsync`, `08/reclaim-lru-and-kswapd`, and `08/what-free-and-rss-really-say`. Phase 3's VFS and block folders both build on it.

**Currency risk.** The folio conversion is ongoing at v6.18 and the spec singles it out for context7 verification. Do the check before writing, and date it in the references.

### `folios-and-compound-pages.md` — Folios and Compound Pages

- **Opens with:** the unit problem. `struct page` describes 4 KiB, and there is one for every 4 KiB of RAM, which on a large machine is millions of structures whose size is jealously guarded. But almost everything the kernel does with memory now happens in groups of pages, and expressing "this group" through a single-page structure produced a decade of ambiguity: given a `struct page`, is it the whole object, or a piece of one?
- **Sections:**
  - `## Compound pages, and the ambiguity` — head and tail pages, the head carrying the group's metadata, tails pointing back at it. Explain that any function taking a `struct page *` had to defensively ask whether it had been handed a tail, and that the answer changed behaviour — a whole class of bugs.
  - `## What a folio is` — a type that is guaranteed to be a head page, i.e. "a power-of-two group of pages treated as one unit". The change is a *type-system* change more than a data-structure change, and saying that clearly is the most useful thing on the page.
  - `## What it buys` — unambiguous APIs, less per-page overhead in the page cache, larger units for I/O, and a path toward large block sizes and large anonymous folios. Give the concrete win: the page cache can hold one folio for 64 KiB of a file instead of sixteen entries.
  - `## Reading code from either side` — a two-column table of old and new names (`page_cache_get`/`folio_get`, `set_page_dirty`/`folio_mark_dirty`, `PageUptodate`/`folio_test_uptodate`, and the compatibility wrappers). This is what makes the page immediately useful: readers will meet both, in the same file.
  - `## Where the conversion stands at v6.18` — **context7-verified and dated**: which subsystems are converted, which are not, and where the compatibility wrappers still live. State the check date in the text, not only in the references.
  - `## Anonymous large folios` — the extension of the idea beyond file pages, and its relationship to THP. Keep it short and hand the policy to `./hugepages-and-thp.md`.
  - `## The practical consequence for a reader` — when you see `struct page` in code you are reading, ask whether that code has been converted; when you write code, use folios. One paragraph, no advocacy.
- **Anchor:** a Mermaid `classDiagram` showing a compound page group — head with the metadata, four tails pointing to it — beside a folio reference to the same group, annotated to show that the folio type simply guarantees you hold the head. Caption: "The same sixteen kilobytes, seen as five `struct page`s with an ambiguity, and as one folio without it."
- **KernelFacts:** `structure` — `[["struct folio", "include/linux/mm_types.h"], ["struct page", "include/linux/mm_types.h"]]`; `path` — `"folio_alloc() → alloc_pages() → head page → folio_test_*/folio_mark_* operate on the head"`; `observe` — `grep -c folio /proc/kallsyms` (a crude but real measure of how far the conversion has reached in the running kernel); `trap` — "A folio is not a huge page. It is a group of pages of *any* power-of-two order, including one — most folios in a running system are a single page, and the type says nothing about size."
- **References:**
  - `https://docs.kernel.org/mm/folio.html` if present at v6.18, otherwise the mm documentation index — **check which exists** and cite what is there; state the check date.
  - Matthew Wilcox's folio talks and LWN's *"Clarifying memory management with folios"* (`https://lwn.net/Articles/849538/`) — the rationale in the author's own framing; from the proposal period, so note that the API names settled afterwards.
  - `<Src file="include/linux/mm_types.h" symbol="folio" />` — the definition, whose comment block is the clearest statement of the invariant.
  - context7 query for the current folio API surface — record the date of the check in this annotation, per the spec's currency requirement.

### `the-page-cache.md` — The Page Cache **[WAH]** **[Lab host=root-required]**

- **Opens with:** the single most consequential piece of Linux memory management, and the one most misread by monitoring tools. All file data passes through a cache in RAM, that cache is allowed to grow until it fills the machine, and this is correct behaviour that looks alarming on every dashboard ever built.
- **Sections:**
  - `## The structure` — `struct address_space` per file (hanging off the inode), indexed by page offset with an XArray, holding folios. Note that the index is by *file offset*, not by disk block, which is why the same data cached for two files is two copies and why sparse files cost nothing.
  - `## `read()` and `mmap()` reach the same place` — a buffered read finds the folio and copies out of it; a mapped read installs a PTE pointing at the same folio and the process reads it directly. The consequence: `read` and `mmap` of the same file share physical memory, and a write through one is visible to the other.
  - `## What actually happens` **[WAH]** — the second `grep` of a large file being instant. First run: page faults or `read` calls find nothing cached, the filesystem issues I/O, folios are added, the data is copied out. Second run: every lookup hits. Show the real timings with `hyperfine` or `time`, then `echo 3 > /proc/sys/vm/drop_caches` and show the first-run timing return. Say clearly what was measured: the difference between RAM and a device, mediated entirely by whether the kernel still had the data.
  - `## Readahead` — the heuristic that turns a sequential access pattern into large asynchronous reads ahead of the reader, and detects when to stop. `posix_fadvise` and `madvise` as the explicit controls. Note the case that defeats it (random access with a sequential-looking start) and the cost of getting it wrong: read amplification.
  - `## Writes land here too` — a `write()` copies into a folio, marks it dirty, and returns. The data is in RAM and not on the device. Say this plainly here and hand the whole durability question to `./writeback-and-fsync.md`.
  - `## `O_DIRECT`, in one paragraph` — the escape hatch that bypasses the cache entirely, why databases use it, and what they give up. Folder 12 owns it; name it and move on.
  - `## Cache is not "used" memory` — the framing that the measurement page will finish: page cache is reclaimable, counted separately in `/proc/meminfo` as `Cached`, and included in `MemAvailable` precisely because it can be given back. Set this up here so `./what-free-and-rss-really-say.md` can complete it.
  - `<Lab host="root-required" title="Watch the page cache fill and be dropped" time="20 min">` — (1) create a 2 GB file with `dd`; (2) `grep -E 'Cached|MemAvailable' /proc/meminfo` before and after reading it; (3) time the read twice; (4) drop caches and time it again; (5) use `vmtouch` if available, or `mincore` via a short C program, to show *which pages* of the file are resident. Expected output for each. `:::warning` on `drop_caches`: it is not destructive, but it evicts everything the machine had cached and the next few minutes will be slower. "If it fails": on a machine with less than ~4 GB free the file will not stay cached, and on a filesystem with compression the `dd` file may not be the size you think.
- **Anchor:** a Mermaid `flowchart TB` from both `read()` and a page fault on a mapped file, converging on `filemap_get_folio`, with the hit path returning immediately and the miss path descending into the filesystem's `read_folio` and the block layer. Caption: "Two very different-looking operations, one cache: `read()` and a fault on a mapping meet at the same folio."
- **KernelFacts:** `structure` — `[["struct address_space", "include/linux/fs.h"], ["struct folio", "include/linux/mm_types.h"]]`; `path` — `"read() → vfs_read() → filemap_read() → filemap_get_pages() → folio in the XArray, or read_folio() → block layer"` (verify at v6.18); `observe` — `grep -E '^(Cached|Buffers|MemAvailable|Dirty):' /proc/meminfo`; `trap` — "A machine with almost no free memory and a large page cache is a healthy machine. `Cached` is memory doing useful work that will be handed back the moment anything else needs it — `MemAvailable`, not `MemFree`, is the number that answers 'can I start another process'."
- **References:**
  - `<Src file="mm/filemap.c" symbol="filemap_read" />` — the buffered read path, where the cache lookup and the fallback to I/O are both visible.
  - `https://docs.kernel.org/admin-guide/mm/concepts.html` — the kernel's own description of the page cache and reclaimability, at the right level for the closing section.
  - `man 2 posix_fadvise` and `man 2 madvise` — the explicit readahead and eviction controls, with the exact semantics of `POSIX_FADV_DONTNEED`.
  - `man 5 proc`, the `/proc/meminfo` fields — the definitions of `Cached`, `Buffers`, and `MemAvailable` that this page and the measurement page both rest on.

- [ ] **Step 1: Run the context7 folio check** and record the date; cross-check anything it says against `<Src file="include/linux/mm_types.h" />` at v6.18.
- [ ] **Step 2: Write `folios-and-compound-pages.md`** to the brief above, including the old-name/new-name table.
- [ ] **Step 3: Write `the-page-cache.md`** to the brief above.
- [ ] **Step 4: Run the page-cache lab** with real timings on a described machine, including the `drop_caches` step.
- [ ] **Step 5: Verify** `folio`, `address_space`, `filemap_read`, `filemap_get_folio`, `read_folio`, and the old/new API name pairs against Elixir v6.18.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write folios and the page cache"
```

---

## Task 24: Folder 08 — writeback, reclaim, and swap

**Files:**
- Modify: `docs/linux/08-memory-management/writeback-and-fsync.md`
- Modify: `docs/linux/08-memory-management/reclaim-lru-and-kswapd.md`
- Modify: `docs/linux/08-memory-management/swap-and-zswap.md`

**Interfaces:**
- Consumes: `08/the-page-cache` (Task 23).
- Produces: `08/reclaim-lru-and-kswapd`, the declared prerequisite of `08/swap-and-zswap`, `08/the-oom-killer`, and `08/what-free-and-rss-really-say`.

### `writeback-and-fsync.md` — Writeback, Dirty Pages, and `fsync` **[WAH]** **[Misc]**

- **Opens with:** the gap between "the write returned" and "the data is safe", which is where most data-loss incidents live. A successful `write()` means the kernel has a copy in RAM. Nothing more. Everything on this page is about who eventually moves it to a device and what, precisely, you must do to know that it arrived.
- **Sections:**
  - `## Dirty tracking` — a folio marked dirty on write, the per-`address_space` and per-BDI accounting, and the two thresholds: `dirty_background_ratio` (start writing back in the background) and `dirty_ratio` (block the writing process until it catches up). Explain that the second one is why a program doing bulk writes suddenly stalls, and that the stall is throttling, not a bug.
  - `## Who does the writing` — per-BDI writeback workers in the `bdi_wq` workqueue, driven by the thresholds and by a periodic expiry (`dirty_expire_centisecs`). Link `../10-interrupts-time-and-deferred-work/workqueues.md`, which is in this phase.
  - `## What `fsync` actually guarantees` — the data *and* the metadata needed to find it, flushed to the device, with a cache-flush/FUA request so the device's own volatile cache is not the last holdout. Contrast with `fdatasync` (skips non-essential metadata) and `sync` (everything, asynchronously initiated). Say what none of them guarantee: that the *directory entry* pointing at a new file is durable — that needs an `fsync` on the directory, and this is the classic bug.
  - `## What actually happens` **[WAH]** — a power cut ten seconds after a program wrote a file and exited. Walk it: the write went to page cache, the process exited (which flushes nothing), writeback had not yet run or had run partially, and the file on disk is empty, truncated, or old. Then walk the correct sequence: write, `fsync` the file, `fsync` the parent directory, rename if using the write-to-temp-and-rename pattern. Show it as a numbered sequence with what survives after each step. This is the most practically valuable section in the folder.
  - `## The `fsync` error problem` — a failed writeback marks the error once, and historically a second `fsync` could return success on data that was never written. Explain the errseq fix and the rule that survives it: **an `fsync` failure is not retryable**, because the dirty pages may already have been dropped. Cite the "fsyncgate" material.
  - `## Barriers and FUA` — one paragraph: the block layer's cache-flush request, and why a device with a volatile write cache and no flush support cannot be made durable by any amount of kernel effort. Folder 12 owns the block-layer side.
  - `## Tuning, honestly` — the four sysctls, what each shifts, and the honest statement that lowering `dirty_ratio` trades throughput for smoother latency and does not improve durability at all. Durability comes only from `fsync`.
  - `## Misconceptions` **[Misc]** — (1) "`write()` returning means the data is written" — it means it is in RAM; (2) "closing the file flushes it" — `close` does not imply `fsync` and never has; (3) "`fsync` on the file is enough for a new file" — the directory entry needs its own `fsync`.
- **Anchor:** a Mermaid `sequenceDiagram` — Application, Page cache, Writeback worker, Block layer, Device cache, Platter/flash — with `write()`, the background threshold, `fsync`, and the cache-flush request marked, and a "power cut here" annotation at three points showing what survives each. Caption: "Where the data is at each moment after `write()` returns, and what a power cut at each point costs you."
- **KernelFacts:** `structure` — `[["struct backing_dev_info", "include/linux/backing-dev-defs.h"], ["struct writeback_control", "include/linux/writeback.h"]]`; `path` — `"write() → folio_mark_dirty() → balance_dirty_pages() → wb_workfn() → writepages() → bio"` (verify at v6.18); `observe` — `grep -E '^(Dirty|Writeback):' /proc/meminfo && cat /proc/sys/vm/dirty_ratio /proc/sys/vm/dirty_background_ratio`; `trap` — "An `fsync` that returns an error must not be retried and treated as success. The pages may already have been dropped, so a subsequent successful `fsync` says nothing about the data you lost."
- **References:**
  - `man 2 fsync` and `man 2 fdatasync` — the guarantees as specified, including the directory-entry caveat.
  - `https://docs.kernel.org/admin-guide/sysctl/vm.html` — the definitive description of the four dirty-page sysctls.
  - PostgreSQL's "fsyncgate" summary (`https://wiki.postgresql.org/wiki/Fsync_Errors`) — the incident that clarified error semantics for the whole industry; essential reading for the error section.
  - Rebello et al., *"Can Applications Recover from fsync Failures?"*, USENIX ATC 2020 — the systematic study; the answer is mostly no, and the paper says why.

### `reclaim-lru-and-kswapd.md` — Reclaim, LRU, and kswapd

- **Opens with:** the other half of allocation. A system that only allocates eventually stops, so something must decide which pages to take back and from whom. Reclaim is that decision, it runs constantly on a busy machine, and whether it runs in the background or in your allocating thread is the difference between a healthy machine and a stalling one.
- **Sections:**
  - `## What is reclaimable` — clean file pages (drop them), dirty file pages (write, then drop), anonymous pages (only if there is swap), slab objects via shrinkers, and the things that are not reclaimable at all (kernel stacks, mlocked pages, most `GFP_KERNEL` allocations). A table, because the categories drive everything else.
  - `## The LRU lists` — active and inactive, per node and per memcg, for file and anon separately. The second-chance promotion: a page referenced while on the inactive list is promoted rather than evicted. Explain why two lists rather than a strict LRU (cost, and resistance to a single large scan flushing everything useful).
  - `## MGLRU at v6.18` — multi-generational LRU: generations instead of two lists, aging by scanning page-table access bits rather than only by reference on fault, and better behaviour under memory pressure. **context7-verify its status and default at v6.18** — whether it is enabled by default is exactly the kind of claim that goes stale — and state the check date. Name `/sys/kernel/mm/lru_gen/enabled` as where the running system answers the question.
  - `## kswapd versus direct reclaim` — the crucial operational distinction. `kswapd` runs when a zone drops below its low watermark and reclaims in the background; direct reclaim happens *in the allocating task* when the min watermark is hit, and it is a latency event with an unbounded tail. Say how to see the difference (`pgscan_kswapd` versus `pgscan_direct` in `/proc/vmstat`, and PSI memory pressure) and why "the machine has free memory but is slow" is often direct reclaim.
  - `## Shrinkers` — the callback interface for caches the page allocator does not own: dentries, inodes, and every subsystem with its own object cache. `vm.vfs_cache_pressure` as the knob that biases against them, and the honest note that shrinking the dentry cache aggressively is usually counterproductive.
  - `## Refaults, and detecting thrashing` — a page evicted and immediately read back is the signal that the working set no longer fits. `WorkingsetRefault` in `/proc/vmstat` and PSI's memory `some`/`full` are how you see it. This is the measurement that distinguishes "using memory efficiently" from "thrashing", and it deserves to be stated as such.
  - `## The reclaim/allocation loop` — close the circle with `./the-page-allocator.md`: watermarks trigger reclaim, reclaim frees pages, allocation retries, and when the loop cannot make progress the OOM killer is the exit. Forward-link to `./the-oom-killer.md`.
- **Anchor:** a Mermaid `stateDiagram-v2` for a file page — Newly read (inactive) → (referenced) Active → (aged) Inactive → (evicted) Not present → (refault) Inactive again, with the refault edge highlighted as the thrashing signal. Caption: "One file page's life through the LRU lists, and the refault edge that tells you the working set no longer fits."
- **KernelFacts:** `structure` — `[["struct lruvec", "include/linux/mmzone.h"], ["struct shrinker", "include/linux/shrinker.h"]]`; `path` — `"allocation below watermark → wake_all_kswapds() or direct reclaim → shrink_node() → shrink_lruvec() → shrink_folio_list()"` (verify at v6.18); `observe` — `grep -E 'pgscan_kswapd|pgscan_direct|pgsteal|workingset_refault' /proc/vmstat && cat /proc/pressure/memory`; `trap` — "Free memory is not the metric. A machine at 99% memory use with no reclaim activity is fine; a machine with gigabytes free that is doing direct reclaim is stalling every allocating thread. Watch `pgscan_direct` and PSI, not `MemFree`."
- **References:**
  - `https://docs.kernel.org/admin-guide/mm/multigen_lru.html` — the MGLRU administration guide; **check it exists at v6.18** and record the check date.
  - `https://docs.kernel.org/accounting/psi.html` — memory pressure as the operational signal, and the difference between `some` and `full`.
  - `<Src file="mm/vmscan.c" symbol="shrink_folio_list" />` — where a page's fate is actually decided, one page at a time.
  - `man 5 proc`, the `/proc/vmstat` fields — the counters this page tells the reader to watch.

### `swap-and-zswap.md` — Swap, zswap, and zram **[WAH]** **[Misc]**

- **Opens with:** the observation that swap has an undeserved reputation. Swap is not "what happens when you run out of memory"; it is what makes anonymous memory reclaimable at all, and a system without it has strictly fewer options when under pressure — it must evict file pages, including executable text it will immediately need again.
- **Sections:**
  - `## What swapping actually moves` — anonymous pages only (file pages are written back to their file, which is not swapping). Say this early, because conflating the two makes every subsequent statement confusing.
  - `## Swap entries live in the PTE` — a non-present PTE with a swap type and offset encoded in the bits the hardware ignores. This is the mechanism, it ties directly back to `./page-tables-and-the-walk.md`, and it explains why a swapped page is found by a page fault rather than by a search.
  - `## The fault back in` — `do_swap_page`, the read, and the fact that this is a *major* fault by definition. Note swap readahead and that it can help or hurt depending on locality.
  - `## `swappiness`, precisely` — not "how eager to swap" but the relative cost the kernel assigns to reclaiming anonymous pages versus file pages. Give the range and the behaviour at 0, 60, 100, and above 100 at v6.18 (**verify** — the upper range's meaning changed), and state that 0 does not disable swapping entirely.
  - `## What actually happens` **[WAH]** — a machine with swap disabled under memory pressure. Reclaim can only take file pages; the working set's executable text is evicted, immediately refaulted, evicted again. Show the symptom: heavy major-fault and refault counts, a stalling machine, and the OOM killer arriving *later* than it would have with swap, after a long period of thrashing. Then state the conclusion plainly: disabling swap does not prevent thrashing, it changes what thrashes and usually makes the machine's degradation less recoverable.
  - `## zram and zswap` — two different things people conflate. zram is a compressed block device used *as* a swap device; zswap is a compressed cache in front of a real swap device that writes through when full. A table comparing them: where the compressed data lives, whether a backing device is needed, and what happens when the pool fills. Give the typical use for each.
  - `## Swap on SSD versus on rotating media` — the honest performance note, and `/sys/block/*/queue/rotational` influencing readahead decisions.
  - `## When swap really is wrong` — a latency-critical service where a major fault is unacceptable, or a container platform that would rather kill a workload than let it degrade. Say so, because a page that only defends swap is not credible.
  - `## Misconceptions` **[Misc]** — (1) "swap is used only when RAM is full" — the kernel may swap out idle anonymous pages to make room for cache while RAM is available, and this is correct; (2) "`swappiness=0` disables swap" — it strongly biases against it, and swapping can still happen; (3) "swap makes things slow" — thrashing makes things slow, and swap is what the kernel does *before* thrashing becomes unrecoverable.
- **Anchor:** a Mermaid `flowchart LR` showing an anonymous page's two paths under pressure — with swap (evicted to a swap device, PTE becomes a swap entry, faulted back later) and without swap (not reclaimable, so a file page is evicted instead and refaults). Caption: "The same memory pressure, with and without swap: the pressure does not disappear, it moves to the pages you were about to use."
- **KernelFacts:** `structure` — `[["struct swap_info_struct", "include/linux/swap.h"], ["swp_entry_t", "include/linux/swapops.h"]]`; `path` — `"reclaim → add_to_swap() → swap_writepage() → PTE becomes a swap entry → later fault → do_swap_page() → swap_readpage()"` (verify at v6.18); `observe` — `swapon --show && grep -E '^(Swap(Cached|Total|Free)):' /proc/meminfo && cat /proc/sys/vm/swappiness`; `trap` — "Swap usage is not a problem indicator. Pages swapped out and never touched again cost nothing; the number that matters is the swap-in *rate* (`pswpin` in `/proc/vmstat`), because that is the only part that costs latency."
- **References:**
  - `https://docs.kernel.org/admin-guide/mm/zswap.html` and the zram documentation — the definitive descriptions of both, and the difference between them.
  - Chris Down, *"In defence of swap"* (`https://chrisdown.name/2018/01/02/in-defence-of-swap.html`) — the clearest argument for why a swapless system has fewer options; a blog post by a kernel and systemd contributor, and correct.
  - `<Src file="mm/page_io.c" symbol="swap_writepage" />` — the write side; short and dispels the idea that swapping is elaborate.
  - `man 5 proc` and `man 8 swapon` — the counters and the interface for the observation commands.

- [ ] **Step 1: Write `writeback-and-fsync.md`** to the brief above.
- [ ] **Step 2: Run the context7 MGLRU check** and record the date; confirm the default at v6.18 from `/sys/kernel/mm/lru_gen/enabled` on a real machine if one is available.
- [ ] **Step 3: Write `reclaim-lru-and-kswapd.md`** to the brief above.
- [ ] **Step 4: Write `swap-and-zswap.md`** to the brief above.
- [ ] **Step 5: Verify** `balance_dirty_pages`, `wb_workfn`, `backing_dev_info`, `lruvec`, `shrinker`, `shrink_folio_list`, `swap_info_struct`, `do_swap_page`, `swap_writepage`, and the `swappiness` range semantics against Elixir v6.18 and `Documentation/admin-guide/sysctl/vm.rst`.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write writeback and fsync, reclaim, and swap"
```

---

## Task 25: Folder 08 — the OOM killer, and huge pages

**Files:**
- Modify: `docs/linux/08-memory-management/the-oom-killer.md`
- Modify: `docs/linux/08-memory-management/hugepages-and-thp.md`

**Interfaces:**
- Consumes: `08/reclaim-lru-and-kswapd` (Task 24) and `08/page-tables-and-the-walk`/`08/tlb-and-address-space-switching` (Tasks 19–20).
- Produces: two of the folder's three most-searched pages. Nothing later in this phase depends on them structurally.

### `the-oom-killer.md` — The OOM Killer **[WAH]** **[Lab host=qemu]** **[Misc]**

- **Opens with:** the position the kernel is in when this code runs. Every allocation path has failed, reclaim cannot make progress, and there is no correct answer — only a choice between killing something and deadlocking the machine. The OOM killer is a heuristic making a decision nobody wants to make, and understanding it means understanding that it is already a failure state, not a safety feature.
- **Sections:**
  - `## How it is reached` — allocation → reclaim → retry → repeated failure → `out_of_memory()`. Emphasise the loop, because the machine is usually thrashing badly for a long time before this point, and that period is where intervention is actually possible.
  - `## Choosing a victim` — `oom_badness`: essentially RSS plus swap plus page-table size, scaled by `oom_score_adj`. State plainly that it is "who will free the most memory", not "who is at fault", which is why the database gets killed and the leaking script survives.
  - `## `oom_score_adj`` — the range (−1000 to 1000), what −1000 means (immune), and the practical policy: protect the thing that matters, do not try to encode blame.
  - `## memcg OOM versus global OOM` — a cgroup that hits `memory.max` gets an OOM confined to itself, killing only its own tasks, and this is *much* better than a global OOM. Note `memory.oom.group` for killing the whole cgroup atomically, which is what container platforms usually want. Link forward in prose to folder 15.
  - `## What actually happens` **[WAH]** — reading a real OOM report from `dmesg`, field by field: the invoking task and its GFP flags, the memory-state dump, the per-task table with RSS and `oom_score_adj`, the chosen victim line, and the "Killed process" line. Use a real report captured in the lab. The reader should finish able to answer three questions from any OOM report: who asked for memory, who got killed, and whether it was global or cgroup-scoped.
  - `## The panic option` — `vm.panic_on_oom` and why some deployments prefer a reboot to a randomly degraded machine.
  - `## User-space killers` — `systemd-oomd`, `earlyoom`, and `nohang`: all of them act on PSI *before* the kernel's last resort, which is the right place to act. Give the reasoning: the kernel's OOM killer runs when nothing can be done gracefully, and PSI-based killing runs while the machine is merely unhappy.
  - `<Lab host="qemu" title="Cause and read an OOM kill" time="20 min">` — in the QEMU lab **only**: run a program that allocates and touches memory in a loop, watch `/proc/pressure/memory` climb, and let the OOM killer fire. Capture the full report from `dmesg` and read it against the section above. Then repeat inside a cgroup with `memory.max` set and observe the scoped kill. `:::danger` — do **not** run this on a machine you care about: an unprotected OOM can kill your session, your editor, or the display manager, and on a machine without swap the thrashing phase can render it unusable for minutes before anything is killed. The host badge is `qemu` for exactly this reason. "If it fails": with `vm.overcommit_memory=2` the allocation fails cleanly instead, and inside a container the cgroup limit may fire before the global path.
  - `## Misconceptions` **[Misc]** — (1) "the OOM killer kills the process that caused the problem" — it kills the one whose death frees the most; (2) "an OOM kill means the machine ran out of RAM" — it means allocation could not be satisfied, which can happen with free memory in the wrong zone or with a fragmented high-order request; (3) "you can prevent OOM by disabling overcommit" — mode 2 moves the failure to `malloc`, which most software handles no better.
- **Anchor:** a real annotated OOM report in a ` ```text ` block, with the four fields to read marked. This is more useful than any diagram and is what a reader arrives at this page needing.
- **Second visual:** a Mermaid `flowchart TB` from a failing allocation through reclaim retries to `out_of_memory`, with the memcg branch drawn separately.
- **KernelFacts:** `structure` — `[["struct oom_control", "include/linux/oom.h"]]`; `path` — `"__alloc_pages_slowpath() → reclaim fails → out_of_memory() → select_bad_process() → oom_kill_process()"` (verify at v6.18); `observe` — `dmesg -T | grep -A 40 'invoked oom-killer'`; `trap` — "The OOM killer is not a protection mechanism, it is the end of one. By the time it fires the machine has usually been thrashing for a long time — the useful intervention is a PSI-driven user-space killer acting well before this point."
- **References:**
  - `<Src file="mm/oom_kill.c" symbol="oom_badness" />` — the scoring function, which is short and settles every argument about victim selection.
  - `https://docs.kernel.org/admin-guide/mm/concepts.html` and the cgroup v2 memory-controller documentation — for memcg OOM and `memory.oom.group`.
  - `man 5 proc`, the `oom_score` and `oom_score_adj` sections — the user-space interface and its range.
  - `https://www.freedesktop.org/software/systemd/man/latest/systemd-oomd.service.html` — the PSI-based alternative and its configuration.

### `hugepages-and-thp.md` — Huge Pages and THP **[WAH]** **[Misc]**

- **Opens with:** the number that justifies the whole feature. A TLB holds a fixed number of entries, so its *reach* is entries × page size — a couple of thousand 4 KiB entries covers a few megabytes, and the same entries at 2 MiB cover gigabytes. A workload whose working set exceeds TLB reach spends a measurable fraction of its time walking page tables, and huge pages are the only fix.
- **Sections:**
  - `## Sizes, and where they come from` — 2 MiB (a PMD entry terminating the walk) and 1 GiB (a PUD entry), on x86-64. Tie it back to `./page-tables-and-the-walk.md` — a huge page is not a special object, it is a stopped walk.
  - `## Two mechanisms, not one` — hugetlbfs (explicitly reserved, pre-allocated, never swapped, requires application awareness) versus THP (automatic, opportunistic, transparent to the application). The confusion between them causes most of the bad advice on this topic, so separate them clearly and early.
  - `## hugetlbfs` — reserving pages at boot or at runtime, `/proc/sys/vm/nr_hugepages`, the `hugetlbfs` mount, and `MAP_HUGETLB`. Why databases and hypervisors use it: guaranteed availability, no reclaim, and no surprise.
  - `## THP` — `khugepaged` scanning and promoting, fault-time allocation, and the three modes (`always`, `madvise`, `never`) in `/sys/kernel/mm/transparent_hugepage/enabled`. Explain `madvise` as the default position on many distributions and why: it gives the benefit to applications that ask, without the cost to those that do not.
  - `## What actually happens` **[WAH]** — why databases disable THP. A latency-sensitive process faults; with `always`, satisfying that fault may require compaction, which can stall the faulting task for milliseconds while pages are migrated. Show the mechanism (direct compaction on the fault path) and the symptom (occasional multi-millisecond stalls with no corresponding I/O). Then give the current, more nuanced position: `defrag` settings decouple *allocation* from *compaction*, so `enabled=always` with `defrag=defer` behaves very differently from the configuration that earned THP its reputation. **Verify the `defrag` values at v6.18** and give them exactly.
  - `## Memory waste` — a 2 MiB page for a 4 KiB working region wastes 2044 KiB, and `khugepaged` collapsing sparse regions can inflate RSS substantially. This is the second real cost and it is why `AnonHugePages` in `/proc/meminfo` and `smaps` is worth checking when memory use is unexpectedly high.
  - `## Measuring whether it helps` — `perf stat -e dTLB-load-misses`, `AnonHugePages` in `smaps`, and `/proc/vmstat`'s `thp_fault_alloc` and `thp_collapse_alloc`. Give the honest guidance: measure the workload, because the answer genuinely differs between a database, a JVM heap, and a compiler.
  - `## Misconceptions` **[Misc]** — (1) "huge pages help because there are fewer page-table levels to walk" — the walk depth is unchanged for the levels above; the benefit is TLB reach; (2) "THP should always be disabled" — that advice comes from a specific configuration and a specific era, and the `defrag` controls change the trade-off; (3) "hugetlbfs and THP are the same feature with different names" — they have opposite reliability and configuration models.
- **Anchor:** a table of TLB reach: entries × 4 KiB versus entries × 2 MiB versus entries × 1 GiB, with a "working set that fits" column, using a plausible modern L2 TLB size that is stated as an example rather than a specification.
- **Second visual:** a Mermaid `flowchart LR` of the page-table walk terminating at the PMD level for a 2 MiB page beside the full four-level walk for 4 KiB.
- **KernelFacts:** `structure` — `[["struct hstate", "include/linux/hugetlb.h"]]`; `path` — `"fault on a THP-eligible VMA → do_huge_pmd_anonymous_page() → alloc_pages(order 9) → PMD entry, walk stops early"` (verify at v6.18); `observe` — `cat /sys/kernel/mm/transparent_hugepage/enabled /sys/kernel/mm/transparent_hugepage/defrag && grep -E 'AnonHugePages|HugePages_Total' /proc/meminfo`; `trap` — "THP's cost is not the huge pages, it is the *compaction* that sometimes has to happen to produce one — on the fault path, in your latency-sensitive thread. The `defrag` setting, not the `enabled` setting, is what controls that."
- **References:**
  - `https://docs.kernel.org/admin-guide/mm/transhuge.html` — the definitive description of every `enabled` and `defrag` value; **the authority for this page's values, checked at v6.18**.
  - `https://docs.kernel.org/admin-guide/mm/hugetlbpage.html` — the explicit-reservation mechanism and its interfaces.
  - Intel SDM Vol. 3A, ch. 4 — the page-size bit in a PMD entry, i.e. the hardware mechanism behind the whole feature.
  - A database vendor's current THP guidance (MongoDB's or Oracle's documentation) — cite one, date it, and note whether it addresses the `defrag` controls or predates them.

- [ ] **Step 1: Write `the-oom-killer.md`** to the brief above.
- [ ] **Step 2: Trigger a real OOM in the QEMU lab**, capture the full `dmesg` report, and use it as the page's anchor. Do not reconstruct an OOM report from memory — the field layout changes between versions and a fabricated one is worse than no example.
- [ ] **Step 3: Write `hugepages-and-thp.md`** to the brief above.
- [ ] **Step 4: Read `Documentation/admin-guide/mm/transhuge.rst` at v6.18** and take the `enabled`/`defrag` value lists from it verbatim.
- [ ] **Step 5: Verify** `oom_badness`, `select_bad_process`, `oom_kill_process`, `oom_control`, `hstate`, and the THP fault-path symbol against Elixir v6.18.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write the OOM killer and huge pages"
```

---

## Task 26: Folder 08 — NUMA policy, and what the memory numbers mean

**Files:**
- Modify: `docs/linux/08-memory-management/numa-and-memory-policy.md`
- Modify: `docs/linux/08-memory-management/what-free-and-rss-really-say.md`

**Interfaces:**
- Consumes: `08/the-page-allocator`, `08/the-page-cache`, `08/reclaim-lru-and-kswapd`, and `computer-science/memory-hierarchy/numa-and-memory-topology` (Task 4).
- Produces: the folder's completion, and the measurement vocabulary that folder 15's cgroup pages and Phase 5's observability folder both assume.

### `numa-and-memory-policy.md` — NUMA and Memory Policy

- **Opens with:** the kernel's default answer to a hard question, which is usually right: allocate from the node the faulting CPU belongs to. Since the faulting CPU is usually the one that will use the memory, first-touch local allocation gets the placement right without anyone specifying anything — and every policy on this page is a way of overriding it when it gets it wrong.
- **Sections:**
  - `## First touch, restated in kernel terms` — the page fault allocates from the local node's zone list, falling back to remote nodes by distance. Link back to the CS page for what "distance" physically means.
  - `## Policies` — default, bind, preferred, interleave, and the weighted-interleave option if present at v6.18 (**verify**). A table: what each does, which syscall sets it, and the workload it suits.
  - `## Scope: task, VMA, and cgroup` — `set_mempolicy` for a task, `mbind` for a range, and the cpuset's `mems` for a group. Explain the precedence, because a program setting a policy inside a restrictive cpuset is a common source of confusion.
  - `## Automatic NUMA balancing` — the kernel's own attempt at fixing bad placement: periodically unmapping pages to provoke NUMA hinting faults, using those faults to see which node actually touches the memory, and migrating pages or tasks accordingly. State the cost honestly (the hinting faults are real faults) and the tunable that disables it.
  - `## The tools` — `numactl --hardware` for the topology, `numactl --membind`/`--cpunodebind` for launching, `numastat` for per-node hit/miss counters, and `/proc/PID/numa_maps` for a per-VMA breakdown of where a running process's pages actually are. That last one is the diagnostic that settles arguments.
  - `## Where NUMA effects actually show up` — a short, honest list: large in-memory databases, HPC codes, and anything doing a parallel initialisation of a shared array. And the counter-list: most services, where the effect is real and small.
  - `## The classic mistake` — a single thread initialising a large shared array places all of it on one node, and the parallel phase then reads it remotely. Give the fix (parallel first touch) and note it is a program change, not a tuning change, which is why it deserves a section rather than a footnote.
  - `## Interaction with the page cache` — file pages are placed by whoever faults them in, which for a shared file is arbitrary. One paragraph, because it explains why NUMA tuning of a file-heavy workload often does nothing.
- **Anchor:** a table of the five policies against four columns — how pages are chosen, the syscall or tool that sets it, the workload it fits, and the failure mode when it is wrong.
- **KernelFacts:** `structure` — `[["struct mempolicy", "include/linux/mempolicy.h"]]`; `path` — `"page fault → alloc_pages_vma() → policy lookup → node zonelist → local node first, then by distance"` (verify the v6.18 entry point); `observe` — `numactl --hardware && numastat -m | head -20 && sudo head -5 /proc/self/numa_maps`; `trap` — "Memory is placed where it is first *touched*, not where it is allocated. A single thread that initialises a shared array has placed all of it on one node, and no amount of later thread placement will move it."
- **References:**
  - `https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html` — the definitive policy semantics, including the precedence rules between scopes.
  - `man 2 mbind` and `man 2 set_mempolicy` — the interfaces, with the flag combinations that actually migrate existing pages.
  - `man 8 numactl` and `man 8 numastat` — the tools and the counters, which is what a reader will actually use.
  - `https://docs.kernel.org/admin-guide/sysctl/kernel.html`, `numa_balancing` — the automatic-balancing switch and what it costs.

### `what-free-and-rss-really-say.md` — What `free` and RSS Really Tell You **[WAH]** **[Lab host=any-linux]** **[Misc]**

- **Opens with:** the question this whole folder has been building to — "how much memory is this using?" — and the reason it has no single answer. Memory is shared, cached, deferred, and reclaimable, so any single number is a choice about how to attribute all four. This page's job is to make the choice explicit rather than to pick one.
- **Sections:**
  - `## Reading `free` correctly` — the columns, one at a time: `total`, `used`, `free`, `shared`, `buff/cache`, and `available`. The rule stated once and plainly: **`free` is not the number you want; `available` is.** `free` counts memory doing nothing; `available` estimates what a new process could get, which includes reclaimable cache.
  - `## `/proc/meminfo`, the fields worth knowing` — a table of about fifteen: `MemTotal`, `MemFree`, `MemAvailable`, `Buffers`, `Cached`, `SwapCached`, `Active`/`Inactive` (anon and file), `Dirty`, `Writeback`, `AnonPages`, `Mapped`, `Shmem`, `Slab` (reclaimable and unreclaimable), `KernelStack`, `PageTables`, `Committed_AS`. Each with one line, and a note on which ones overlap — because the fields are not a partition and adding them up is meaningless.
  - `## Buffers versus cache` — the historical distinction (block-device cache versus file cache) and the fact that they have been the same mechanism for a long time, with `Buffers` now being a small residue. Say it, because everyone asks.
  - `## Per-process: VSZ, RSS, PSS, USS` — a table with what each includes, what it double-counts, and what question it answers. VSZ: address space, nearly meaningless. RSS: resident pages, double-counted across sharers. PSS: shared pages divided by the number of sharers, the only one that sums correctly across processes. USS: private only, i.e. what would be freed by killing it.
  - `## What actually happens` **[WAH]** — measuring the memory use of a forked worker pool. Take a parent with a 500 MB heap and eight forked children; show that `ps` RSS reports ~500 MB *each*, that summing them gives 4.5 GB on a machine using 500 MB, and that `smaps_rollup`'s PSS sums correctly. This is the single most useful demonstration in the page: the reader sees a standard tool produce an answer that is off by a factor of nine, and learns which tool to use instead.
  - `## `smaps_rollup`, the practical tool` — the aggregate PSS, USS, and swap for a process in one cheap read, versus walking `smaps` per VMA.
  - `## cgroup accounting` — `memory.current` and `memory.stat` as the container-relevant numbers, and the crucial point that a cgroup's `memory.current` includes page cache charged to it, so a container "using" 2 GB may be holding 1.9 GB of reclaimable cache. Note that this is why container memory alerts fire so often and so uselessly.
  - `## Answering the actual question` — a closing decision list: "will another process fit?" → `MemAvailable`; "what would killing this free?" → USS or `smaps_rollup`; "how do I attribute total usage across processes?" → PSS; "is this container about to be OOM-killed?" → `memory.current` against `memory.max`, plus PSI. This list is the page's real deliverable.
  - `<Lab host="any-linux" title="Measure the same process four ways" time="20 min">` — (1) write a program that allocates 500 MB, touches it, and forks four children that idle; (2) `ps -o pid,vsz,rss,comm` for all five; (3) sum the RSS and compare with `free` before and after; (4) `sudo grep -E '^(Rss|Pss|Private)' /proc/PID/smaps_rollup` for each and sum the PSS. Show the arithmetic and the discrepancy. "If it fails": `smaps_rollup` needs matching credentials or root for other processes, and if the children touch the memory they will diverge from the parent — which is itself worth showing.
  - `## Misconceptions` **[Misc]** — (1) "low free memory means the machine is short of memory" — cache is memory doing work; use `available`; (2) "summing RSS gives total usage" — it double-counts every shared page, badly for forked workers and shared libraries; (3) "a container using its full memory limit is about to be killed" — most of it may be reclaimable page cache, and `memory.stat` says how much.
- **Anchor:** the VSZ/RSS/PSS/USS comparison table, with a worked column of real numbers from the lab's five processes.
- **KernelFacts:** `structure` — `[["struct mm_rss_stat", "include/linux/mm_types_task.h"]]` (verify the v6.18 name — RSS accounting was reworked into per-mm counters); `path` — `"read /proc/PID/smaps_rollup → smaps_rollup_show() → walk every VMA → sum Rss/Pss/Private per page's mapcount"`; `observe` — `free -h && grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Shmem):' /proc/meminfo && cat /proc/self/smaps_rollup`; `trap` — "RSS counts a shared page in full for every process that maps it. Add up the RSS of eight forked workers and you will 'account for' several times the memory the machine actually contains — PSS is the only per-process number that sums to something true."
- **References:**
  - `man 5 proc`, the `/proc/meminfo` and `smaps` sections — the field definitions, which is the only authority worth citing for this page.
  - `man 1 free` — the column definitions and the `available` estimate's basis.
  - `https://docs.kernel.org/filesystems/proc.html` — the kernel's own account of `smaps` and `smaps_rollup`, including which fields require privilege.
  - `https://docs.kernel.org/admin-guide/cgroup-v2.html`, the memory controller's `memory.stat` — for the container section; **context7-verify the field list and date it**.

- [ ] **Step 1: Write `numa-and-memory-policy.md`** to the brief above, checking the policy list (including weighted interleave) against `Documentation/admin-guide/mm/numa_memory_policy.rst` at v6.18.
- [ ] **Step 2: Write `what-free-and-rss-really-say.md`** to the brief above.
- [ ] **Step 3: Run the four-ways measurement lab** and paste the real numbers, including the incorrect RSS sum — the discrepancy is the lesson and it must be a real one.
- [ ] **Step 4: Verify** `mempolicy`, the NUMA allocation entry point, the RSS counter structure, and `smaps_rollup_show` against Elixir v6.18. Check every `/proc/meminfo` field name against a real file.
- [ ] **Step 5: Run the folder-08 completeness check** — every one of the eighteen pages written, `check:linux` clean, and no page in folder 08 linking into folders 11–19.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/08-memory-management
git commit -m "docs: write NUMA memory policy and how to read the memory numbers"
```

---
## Task 27: Folder 09 — why kernel concurrency is different, and memory ordering

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/why-kernel-concurrency-is-different.md`
- Modify: `docs/linux/09-concurrency-and-locking/memory-ordering-and-barriers.md`

**Interfaces:**
- Consumes: `04/the-kernel-c-dialect`, and `computer-science/cpu-architecture/memory-ordering-and-consistency` (Task 2) — **the CS page must be finished first**; the spec makes backfill 3 a gate on this folder.
- Produces: `09/why-kernel-concurrency-is-different`, the declared prerequisite of `09/per-cpu-data` and of `10/hardirq-context`, and `09/memory-ordering-and-barriers`, the prerequisite of four pages in this folder.

**Order matters inside this folder.** The spec requires `memory-ordering-and-barriers` before everything else and `rcu-the-idea` before `rcu-in-practice`. Do not reorder the tasks.

### `why-kernel-concurrency-is-different.md` — Why Kernel Concurrency Is Different

- **Opens with:** the reason user-space concurrency intuition fails here. In a user program, concurrency comes from threads, and the answer is a mutex. In the kernel, code can be re-entered by another CPU, by a preemption, by an interrupt, and by a softirq — and in two of those four cases you may not sleep, which eliminates the mutex as an option before the design conversation even starts.
- **Sections:**
  - `## Four sources of concurrency` — SMP (another CPU runs the same code), preemption (another task on this CPU), interrupts (a handler runs on this CPU, in the middle of your function), and softirqs/bottom halves (deferred work on interrupt return). Each with a one-line example of the corruption it causes and the primitive that addresses it.
  - `## The context matrix` — the page's centrepiece and the table the whole folder refers back to. Rows: process context, softirq context, hard-IRQ context, NMI context. Columns: may sleep?, may take a mutex?, may allocate with `GFP_KERNEL`?, may be preempted?, and what it must use for a lock. Every cell must be checkable against the source and the documentation.
  - `## Why "may not sleep" is the hard constraint` — sleeping means calling `schedule()`, which means there must be a task to return to. In interrupt context there is no task that logically owns the code, so there is nothing to put on a wait queue. State it this way, because "you may not sleep" as a rule is memorised and forgotten, while the reason is not.
  - `## `in_interrupt()` and friends` — how code asks what context it is in, and the honest caveat that code which needs to ask is usually structured wrongly. Verify which of these helpers survive at v6.18.
  - `## The interrupt deadlock` — the classic: a process-context path takes a spinlock, an interrupt arrives on the same CPU, the handler takes the same spinlock, and the CPU spins forever waiting for itself. This is *the* reason `spin_lock_irqsave` exists, and stating it here means the spinlocks page can be short about it.
  - `## What PREEMPT_RT changes` — nearly everything on the page: spinlocks sleep, most handlers are threaded, and the context matrix's rows shift. One paragraph, and a link to `../07-scheduling/preemption-models.md`.
  - `## What CS owns` — the theory of mutual exclusion, race conditions, and deadlock is `../../computer-science/operating-systems/concurrency-and-synchronization.md`; the hardware is the three CS pages this folder's `related:` entries name. This folder owns Linux's primitives and the rules for choosing between them.
- **Anchor:** the context matrix table.
- **Second visual:** a Mermaid `sequenceDiagram` of the interrupt deadlock — process context takes the lock, an interrupt preempts on the same CPU, the handler blocks on the same lock, and neither can proceed. Caption: "The deadlock that `spin_lock_irqsave` exists to prevent: one CPU waiting for a lock only it can release."
- **KernelFacts:** `structure` — `[["preempt_count", "include/linux/preempt.h"]]`; `path` — `"process context → spin_lock_irqsave() → interrupt masked locally → critical section → spin_unlock_irqrestore()"`; `observe` — `grep -E 'CONFIG_PREEMPT|CONFIG_SMP|CONFIG_PROVE_LOCKING' /boot/config-$(uname -r)`; `trap` — "Locking correctly is not enough — you must also lock in a way your *context* permits. A mutex in an interrupt handler is not a slow choice, it is a bug that will hang the machine the first time it contends."
- **References:**
  - `https://docs.kernel.org/kernel-hacking/locking.html` — the in-tree "Unreliable Guide to Locking", which is the single best introduction to exactly this material and is written with unusual clarity.
  - `<Src file="include/linux/preempt.h" symbol="preempt_count" />` — the counter whose fields encode the current context, and therefore the machine-readable version of the matrix.
  - `https://docs.kernel.org/locking/index.html` — the locking documentation index this folder cites repeatedly.
  - `../../computer-science/operating-systems/concurrency-and-synchronization.md` — the theory this page deliberately does not repeat.

### `memory-ordering-and-barriers.md` — Memory Ordering and Barriers

- **Opens with:** the sentence that reorients readers who have only written user-space code with mutexes: if you use a lock, the lock handles ordering for you and this page is background. If you write lock-free code, touch a variable another CPU writes without a lock, or read RCU-protected data, then ordering is your problem and getting it wrong produces bugs that appear once a month on one machine.
- **Sections:**
  - `## Two reorderers` — the compiler and the CPU, independently, and a fix for one is not a fix for the other. Link the CS page for the hardware model rather than re-teaching TSO.
  - `## `READ_ONCE` and `WRITE_ONCE`` — what a plain access permits the compiler to do (merge, split, invent, hoist out of a loop) and what these macros forbid. Show the canonical broken spin-on-a-flag loop that the compiler hoists into an infinite loop, then the fixed version. This example is the fastest way to make the point land.
  - `## Compiler barriers versus CPU barriers` — `barrier()` versus `smp_mb()`, and the rule that on a uniprocessor build the `smp_*` variants degrade to compiler barriers, which is why they are named that way.
  - `## The barrier family` — a table: `smp_mb`, `smp_rmb`, `smp_wmb`, `smp_load_acquire`, `smp_store_release`, `smp_mb__before_atomic`/`__after_atomic`. Columns: what it orders, the x86-64 cost (usually nothing for the read/write variants, a real instruction for the full barrier), and the typical use.
  - `## Acquire and release, which is what you should reach for` — the publish/subscribe pattern in the kernel's spelling: `smp_store_release` to publish, `smp_load_acquire` to consume. Show the standard "initialise the object, then publish the pointer" example, and note that the ordering-free version is broken on arm64 and *works by accident* on x86-64 — which is exactly why x86-only testing does not validate barrier code.
  - `## The store-buffer example, in kernel terms` — the litmus test from the CS page, written with `WRITE_ONCE`/`READ_ONCE` and then fixed with `smp_mb()`, so the reader sees the same problem in the code they will actually meet.
  - `## Dependencies` — address dependencies as an implicit ordering on almost every architecture, and `rcu_dereference` as the kernel's way of expressing one safely. Enough setup that the RCU pages can use the term without defining it. Note Alpha's history in one sentence and move on.
  - `## Where the rules actually live` — `Documentation/memory-barriers.txt` is the normative document and is long, dense, and worth the time. Say plainly that this page is an orientation and that document is the authority.
  - `## arm64` — `:::note`, and this is the load-bearing one for the whole section: on x86-64 most `smp_*` barriers compile to nothing, so omitting them produces code that passes every test on the developer's machine and fails on an ARM server. Give the practical rule: write the barrier the algorithm requires, never the one the target architecture needs.
- **Anchor:** a Mermaid `sequenceDiagram` of the publish pattern done wrongly — CPU 0 writes the object then the pointer, CPU 1 reads the pointer then the object and sees uninitialised fields because the stores became visible out of order — followed by the same diagram with `smp_store_release`/`smp_load_acquire`. Caption: "Publishing a new object without release/acquire: the reader can see the pointer before it can see what the pointer points at."
- **KernelFacts:** `structure` — `[["READ_ONCE / WRITE_ONCE", "include/asm-generic/rwonce.h"], ["smp_mb", "arch/x86/include/asm/barrier.h"]]`; `path` — `"initialise object → smp_store_release(&ptr, obj) → other CPU: smp_load_acquire(&ptr) → dereference safely"`; `observe` — `grep -rn 'smp_store_release' /usr/src/linux/kernel/ | head` on a source checkout, or read `<Src file="Documentation/memory-barriers.txt" />`; `trap` — "On x86-64 most barriers compile to nothing, so barrier bugs are invisible until the code runs on arm64. Testing on x86-64 does not validate ordering — it validates that the code compiles and that x86's model is forgiving."
- **References:**
  - `<Src file="Documentation/memory-barriers.txt" />` — the normative document; long, and every serious claim about kernel ordering is checkable against it.
  - `https://docs.kernel.org/tools/rv/index.html` and the LKMM tooling documentation (`tools/memory-model/`) — the formal model and the `herd7` litmus-test tooling, which is how ordering questions are settled definitively rather than argued.
  - McKenney, *Is Parallel Programming Hard…*, the memory-ordering chapter — free, and the most patient explanation available.
  - `../../computer-science/cpu-architecture/memory-ordering-and-consistency.md` — the hardware model this page assumes.

- [ ] **Step 1: Confirm Task 2's CS page is written and committed.** If it is not, stop — this folder depends on it and writing against an unwritten prerequisite produces duplication.
- [ ] **Step 2: Write `why-kernel-concurrency-is-different.md`** to the brief above, checking every cell of the context matrix against `Documentation/kernel-hacking/locking.rst`.
- [ ] **Step 3: Write `memory-ordering-and-barriers.md`** to the brief above.
- [ ] **Step 4: Verify** `preempt_count`, `READ_ONCE`, `smp_store_release`, `smp_load_acquire`, `smp_mb__before_atomic`, and the `in_interrupt()`-family helpers against Elixir v6.18. Confirm `Documentation/memory-barriers.txt` still exists at that path.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write kernel concurrency contexts and memory ordering"
```

---

## Task 28: Folder 09 — atomics, and spinlocks

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/atomics-and-refcounts.md`
- Modify: `docs/linux/09-concurrency-and-locking/spinlocks.md`

**Interfaces:**
- Consumes: `09/memory-ordering-and-barriers` (Task 27) and `computer-science/cpu-architecture/atomic-operations-in-hardware` (Task 2).
- Produces: `09/atomics-and-refcounts`, the declared prerequisite of `09/spinlocks`, and `09/spinlocks`, a prerequisite of `09/mutexes-and-semaphores` and `09/choosing-a-lock`.

**context7 note:** the spec requires verification of `refcount_t` versus `atomic_t` guidance for this folder. Do it before writing the second half of the atomics page, and date it.

### `atomics-and-refcounts.md` — Atomic Operations

- **Opens with:** the smallest synchronisation primitive and the one most often misused. An atomic operation guarantees indivisibility and nothing else — in particular it does not, by default, order anything around it — and a great deal of subtly broken kernel code comes from assuming otherwise.
- **Sections:**
  - `## `atomic_t` and `atomic64_t`` — deliberately opaque types accessed only through the API, never read directly. Explain why the type is a struct wrapper: to make a plain access a compile error.
  - `## The operation families` — a table: set/read, add/sub, inc/dec, and the test-and-branch forms (`atomic_dec_and_test`, `atomic_add_return`, `atomic_cmpxchg`, `atomic_try_cmpxchg`, `atomic_fetch_*`). Columns: what it does, whether it returns the old or the new value, and whether it implies ordering.
  - `## Ordering, per operation` — the rule that catches people: **an atomic that returns no value implies no ordering**, and one that returns a value generally does. Give the naming conventions (`_relaxed`, `_acquire`, `_release`) and point at the definitive table.
  - `## `cmpxchg` and the retry loop` — the standard shape in ` ```c `, with `atomic_try_cmpxchg` shown as the ergonomic form. Note the ABA caveat and hand it to RCU.
  - `## `refcount_t`, and why it is not `atomic_t`` — the whole point: a reference count that overflows or that increments from zero is a use-after-free primitive, and `refcount_t` saturates and warns instead of wrapping. Show the API pairs (`refcount_inc`, `refcount_dec_and_test`, `refcount_inc_not_zero`) and state the rule: **new code uses `refcount_t` for reference counts and `atomic_t` for counters**. Link back to `../04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md`, which owns the lifetime patterns.
  - `## `refcount_inc_not_zero` and the lookup race` — why "find it in a table, then take a reference" needs a single operation that fails if the object is already dying. This is the pattern that connects atomics to RCU, so it earns its own short section.
  - `## The cost` — an uncontended atomic is a cache hit plus a locked instruction; a contended one is a cache line changing owner. Give the orders of magnitude and link the CS coherence page. Say the practical consequence: a single global atomic counter incremented by every CPU is a scalability bug, and the fix is per-CPU counters — forward-link to `./per-cpu-data.md`.
  - `## Bit operations` — `set_bit`, `clear_bit`, `test_and_set_bit`, and the non-atomic `__` variants, plus the fact that they are atomic per bit and not per word. Brief, because they are everywhere in driver code.
- **Anchor:** the operations table above, with the ordering column filled in. It is the thing a reader returns to.
- **KernelFacts:** `structure` — `[["atomic_t", "include/linux/types.h"], ["refcount_t", "include/linux/refcount.h"]]`; `path` — `"refcount_dec_and_test() → reaches zero → caller frees → refcount_inc_not_zero() elsewhere fails safely"`; `observe` — `grep -rn 'refcount_t' /usr/src/linux/include/linux/ | head` on a checkout, or read `<Src file="include/linux/refcount.h" />` directly; `trap` — "An atomic operation with no return value orders nothing. `atomic_inc()` followed by a store can be reordered by the CPU, which is why the kernel has explicit `smp_mb__before_atomic()` and why 'it is atomic so it is safe' is not an argument."
- **References:**
  - `<Src file="Documentation/atomic_t.txt" />` — the normative table of which operations imply which ordering; the single most useful document for this page.
  - `<Src file="include/linux/refcount.h" />` — the header comment explains the saturation semantics and the threat model better than any secondary source.
  - LWN, *"Rethinking reference counting with refcount_t"* (`https://lwn.net/Articles/728202/`) — why the type was introduced and the exploit class it closes.
  - context7 verification of current `refcount_t`/`atomic_t` guidance — record the check date here, per the spec's currency table.

### `spinlocks.md` — Spinlocks **[WAH]** **[Misc]**

- **Opens with:** the primitive that seems primitive and is not. A spinlock burns CPU while waiting, which sounds unconditionally wasteful until you notice the alternative: sleeping costs two context switches, and if the critical section is twenty instructions long, spinning is dramatically cheaper. Spinlocks are the right answer for short critical sections and mandatory in contexts that cannot sleep.
- **Sections:**
  - `## When spinning is right` — a short critical section, a context that cannot sleep, or both. Give the rough guidance: if the hold time is comparable to a context switch, spin; if it can block, do not.
  - `## The absolute rule` — you may not sleep while holding a spinlock. Not `kmalloc(GFP_KERNEL)`, not `copy_to_user`, not a mutex, not `msleep`. Explain the consequence rather than only the rule: the holder is on a CPU that has preemption disabled, and a sleeping holder means every waiter spins until it is rescheduled, which may be never.
  - `## Queued spinlocks` — the MCS-based implementation at v6.18: each waiter spins on its *own* cache line rather than all of them hammering the lock word, which turns a coherence storm into a queue. Explain why the naive test-and-set implementation collapses at high core counts, because that is what makes the design comprehensible. Also state that it is FIFO-fair, which the naive one is not.
  - `## What actually happens` **[WAH]** — `spin_lock()` on an uncontended lock. It is a single atomic operation and, on a `CONFIG_PREEMPT` kernel, a preemption disable — a handful of instructions and one cache-line acquisition. Show the compiled form or the source path. The point: the uncontended case is genuinely cheap, and the fear people have of "locking overhead" is really a fear of *contention*, which is a design problem rather than a primitive problem.
  - `## The interrupt variants` — `spin_lock_irqsave`/`spin_unlock_irqrestore` (save and restore the flag, because you may not know whether interrupts were already off), `spin_lock_irq` (only when you *know* they were on), and `spin_lock_bh` for softirq exclusion. Give the selection rule as a small table, and refer back to the deadlock diagram in `./why-kernel-concurrency-is-different.md`.
  - `## `raw_spinlock_t`` — the variant that stays a real spinlock under PREEMPT_RT, and the fact that `spinlock_t` becomes a sleeping lock there. This is why RT-safe code in the scheduler and the interrupt path uses raw spinlocks, and why "spinlock" means two different things depending on configuration.
  - `## Reading a spinlock in code` — what `spin_lock_init`, a lock embedded in a struct, and `lockdep_assert_held` look like, so the reader can recognise the conventions in real subsystem code.
  - `## Misconceptions` **[Misc]** — (1) "spinlocks waste CPU so mutexes are better" — for short sections the mutex's two context switches cost far more; (2) "`spin_lock_irqsave` disables interrupts on all CPUs" — only on this one, and it must, because that is the only CPU that can deadlock against itself; (3) "a spinlock protects data from other CPUs" — it protects it from anything that takes the same lock, which includes this CPU's interrupt handlers only if you used the right variant.
- **Anchor:** a Mermaid `flowchart TB` decision tree for choosing a spinlock variant: can this data be touched from a hard-IRQ handler? → `irqsave`; from a softirq? → `bh`; process context only? → plain; PREEMPT_RT and in a genuinely atomic path? → `raw`. Caption: "Which spinlock variant, decided by who else can touch the data rather than by how long you hold it."
- **KernelFacts:** `structure` — `[["spinlock_t", "include/linux/spinlock_types.h"], ["struct qspinlock", "include/asm-generic/qspinlock_types.h"]]`; `path` — `"spin_lock() → preempt_disable() → queued_spin_lock() → fast path atomic, or MCS queue on contention"`; `observe` — `sudo cat /proc/lock_stat | head -20` (requires `CONFIG_LOCK_STAT`); `trap` — "Holding a spinlock disables preemption on that CPU. Every instruction in the critical section is a delay imposed on every other task that CPU could have run, which is why 'hold it briefly' is a latency requirement, not a style preference."
- **References:**
  - `https://docs.kernel.org/locking/spinlocks.html` — the in-tree description of the variants and the rules.
  - `<Src file="kernel/locking/qspinlock.c" symbol="queued_spin_lock_slowpath" />` — the MCS queue, with comments explaining the encoding; genuinely readable.
  - `https://docs.kernel.org/locking/locktypes.html` — the definitive statement of which lock types exist and how each behaves under PREEMPT_RT; **the authority for the `raw_spinlock_t` section**.
  - LWN, *"MCS locks and qspinlocks"* (`https://lwn.net/Articles/590243/`) — why the implementation changed and what it fixed.

- [ ] **Step 1: Write `atomics-and-refcounts.md`** to the brief above, taking the ordering column of the operations table from `Documentation/atomic_t.txt` rather than from memory.
- [ ] **Step 2: Run the context7 check** on current `refcount_t` versus `atomic_t` guidance and date it in the references.
- [ ] **Step 3: Write `spinlocks.md`** to the brief above.
- [ ] **Step 4: Verify** `atomic_t`, `refcount_t`, `refcount_inc_not_zero`, `atomic_try_cmpxchg`, `spinlock_t`, `qspinlock`, `queued_spin_lock_slowpath`, and `raw_spinlock_t` against Elixir v6.18, and confirm `Documentation/atomic_t.txt` exists at that path.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write kernel atomics, refcount_t, and spinlocks"
```

---

## Task 29: Folder 09 — sleeping locks, reader-writer locks, and seqlocks

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/mutexes-and-semaphores.md`
- Modify: `docs/linux/09-concurrency-and-locking/rwlocks-and-rwsems.md`
- Modify: `docs/linux/09-concurrency-and-locking/seqlocks.md`

**Interfaces:**
- Consumes: `09/spinlocks` (Task 28) and `09/memory-ordering-and-barriers` (Task 27).
- Produces: `09/mutexes-and-semaphores`, a declared prerequisite of `09/rwlocks-and-rwsems` and `09/choosing-a-lock`, and `09/seqlocks`, named in `10/timekeeping-and-clocksources`'s `related:`.

### `mutexes-and-semaphores.md` — Mutexes and Semaphores

- **Opens with:** the correction that makes the page worth reading — a Linux mutex does not immediately sleep. It spins first, on the assumption that a lock held by a task currently running on another CPU will be released within a few hundred cycles, and only sleeps when that assumption fails. The "mutexes are slow" folklore describes an implementation Linux has not had for a long time.
- **Sections:**
  - `## What a mutex adds over a spinlock` — it may sleep, so it may be held across an allocation, an I/O, or a `copy_to_user`. That single capability is the reason to choose it, and everything else is secondary.
  - `## Optimistic spinning` — the mutex records its owner; a contending task checks whether the owner is currently running on a CPU, and if so spins (using an MCS queue, so the spinning does not create a coherence storm) rather than sleeping. If the owner is descheduled, the waiter sleeps. Give the consequence: for short critical sections a mutex performs close to a spinlock, and the guidance to "use a spinlock for speed" is often wrong.
  - `## The API` — `mutex_lock`, `mutex_lock_interruptible`, `mutex_trylock`, and `mutex_lock_killable`. Say which to use and when: an interruptible variant on any path a user might Ctrl-C, and `trylock` in the rare case where failure is an acceptable outcome (never as a substitute for correct lock ordering).
  - `## Rules the kernel enforces` — a mutex must be released by the task that took it (unlike a semaphore), it may not be used in interrupt context, and it may not be taken recursively. Note that `CONFIG_DEBUG_MUTEXES` checks all three, and that this is why the debug build catches design errors the production build silently tolerates.
  - `## Semaphores, and why they faded` — a counting primitive with no owner, so it can be signalled by a different task and can act as a completion notification. State that most former uses split into mutexes (for exclusion) and `struct completion` (for one-shot notification), and that new code should reach for those rather than a semaphore.
  - `## `struct completion`` — the one-thing-waits-for-another primitive, with `wait_for_completion` and `complete`. Show its shape, because driver code is full of it and readers will assume it is a semaphore.
  - `## Under PREEMPT_RT` — mutexes gain priority inheritance, which is what makes RT priority meaningful in the presence of shared data. Link `../07-scheduling/real-time-scheduling.md`, which introduced priority inversion.
- **Anchor:** a Mermaid `flowchart TB` of `mutex_lock`'s decision path — fast-path atomic acquire → owner running? → spin on the MCS queue → owner descheduled or spin failed → add to the wait list and sleep. Caption: "A mutex sleeps only as a last resort: three attempts to avoid a context switch before it gives in."
- **KernelFacts:** `structure` — `[["struct mutex", "include/linux/mutex.h"], ["struct completion", "include/linux/completion.h"]]`; `path` — `"mutex_lock() → fast path cmpxchg → mutex_optimistic_spin() → __mutex_lock_slowpath() → schedule()"` (verify at v6.18); `observe` — `grep -E 'CONFIG_DEBUG_MUTEXES|CONFIG_MUTEX_SPIN_ON_OWNER' /boot/config-$(uname -r)`; `trap` — "A mutex is not the slow option. It spins before it sleeps, so for short critical sections it costs about what a spinlock costs — while remaining safe to hold across a sleep, which a spinlock never is."
- **References:**
  - `https://docs.kernel.org/locking/mutex-design.html` — the in-tree design document, which explains optimistic spinning and the fast/mid/slow path split.
  - `<Src file="kernel/locking/mutex.c" symbol="mutex_lock" />` — the three paths in one file.
  - `https://docs.kernel.org/locking/locktypes.html` — how each of these behaves under PREEMPT_RT.
  - `https://docs.kernel.org/scheduler/completion.html` — `struct completion`'s own documentation, including the lifetime hazards of a completion on the stack.

### `rwlocks-and-rwsems.md` — Reader-Writer Locks

- **Opens with:** the primitive that looks obviously better and usually is not. Allowing many readers in parallel sounds free; in practice every reader still writes to the lock's cache line to register itself, so N readers produce N coherence transactions on one line, and a plain exclusive lock — which does exactly the same amount of cache-line bouncing while being simpler — is often faster.
- **Sections:**
  - `## The two families` — `rwlock_t` (spinning, non-sleeping) and `rw_semaphore` (sleeping). Different use cases, and the second is by far the more common in modern code.
  - `## Why rwlocks are usually the wrong answer` — the cache-line argument above, plus writer starvation under a steady reader stream. State the practical rule bluntly: if the critical section is short, use a plain spinlock; if reads massively dominate and are long, consider RCU instead; `rwlock_t` occupies a narrow band between those.
  - `## `rw_semaphore`, and where it is right` — long, sleeping read sections. The canonical case is `mmap_lock`, which protects a data structure read by every page fault and written by every `mmap`. Link to `../08-memory-management/mm-struct-and-vmas.md`, which named it.
  - `## The `mmap_lock` story` — a short case study: a single per-`mm` rwsem became a scalability bottleneck on fault-heavy multithreaded workloads, and the fix was not a better lock but a *change of granularity* — per-VMA locking. The lesson generalises and is the most valuable thing on the page: when a reader-writer lock is the bottleneck, the question is usually about granularity, not about the lock.
  - `## Downgrade and upgrade` — `downgrade_write` exists; a read-to-write upgrade does not, and cannot safely, because two readers upgrading simultaneously deadlock. Explain the pattern to use instead (drop, re-acquire for write, re-validate) and why the re-validation is mandatory.
  - `## Fairness and queueing` — the current implementation's writer-preference and handoff behaviour at a high level; **verify against `Documentation/locking/` at v6.18** rather than describing historical behaviour.
  - `## `percpu_rw_semaphore`` — the specialised variant for the extreme read-dominant case: readers touch only their own CPU's data, writers pay a heavy synchronisation cost. Name where it is used (filesystem freezing, cgroup operations) and why the asymmetry is correct there.
- **Anchor:** a table comparing `spinlock_t`, `rwlock_t`, `rw_semaphore`, `percpu_rw_semaphore`, and RCU across five columns — reader cost, writer cost, may readers sleep?, writer starvation risk, and the situation it fits. This table is the page and also feeds `./choosing-a-lock.md`.
- **KernelFacts:** `structure` — `[["struct rw_semaphore", "include/linux/rwsem.h"], ["rwlock_t", "include/linux/rwlock_types.h"]]`; `path` — `"down_read() → fast path atomic on the count → contended → rwsem_down_read_slowpath() → schedule()"`; `observe` — `sudo grep -A3 mmap_lock /proc/lock_stat` (requires `CONFIG_LOCK_STAT` and a workload to produce entries); `trap` — "A reader-writer lock does not make readers free. Every reader writes to the lock's cache line, so on a many-core machine the readers contend with each other — which is exactly the problem RCU exists to solve."
- **References:**
  - `https://docs.kernel.org/locking/locktypes.html` — the full type list with the semantics of each, including the RT behaviour.
  - `<Src file="kernel/locking/rwsem.c" symbol="rwsem_down_read_slowpath" />` — the queueing and handoff behaviour, for the fairness section.
  - LWN's per-VMA locking coverage — the `mmap_lock` case study's source; cite the specific article and its date.
  - `https://docs.kernel.org/locking/percpu-rw-semaphore.html` if present at v6.18 — the asymmetric variant; check the path.

### `seqlocks.md` — Seqlocks

- **Opens with:** the trick, stated plainly: let readers proceed with no lock and no writes at all, and give them a way to *detect* that a writer interfered and simply try again. It costs readers almost nothing, which is why the most-read data in the kernel — the current time — is protected this way.
- **Sections:**
  - `## The protocol` — a sequence counter incremented on entry and exit of every write. A reader reads the counter, reads the data, reads the counter again: unchanged and even means the read was clean; changed or odd means retry. Show the read loop in ` ```c ` and note the barriers that make it correct, linking `./memory-ordering-and-barriers.md`.
  - `## What readers may not do` — the constraints that follow from "your data may be torn": no pointer may escape the loop, nothing may be freed or acted on inside it, and the work must be safely repeatable. State that a reader can genuinely observe an inconsistent mix of old and new values, which is fine only because it will discard them.
  - `## Writers are still serialised` — a seqlock helps readers, not writers; writers take a real lock among themselves. `write_seqlock` bundles the spinlock and the counter, and `seqcount_t` is the counter alone for when you already have the lock. This distinction confuses people, so make it explicitly.
  - `## The canonical use: timekeeping` — the timekeeper is updated by one writer on the tick and read by every `clock_gettime` on every CPU. Show why nothing else fits: readers are enormously more frequent, the read is short and repeatable, and the data is a small struct. Link to `../10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md` and to `../05-syscalls-and-the-boundary/the-vdso.md`, which is where the same protocol appears in *user space*.
  - `## `latch` variants` — one short section on the double-buffered variant that avoids the retry entirely for readers who cannot retry (notably in NMI context, where a retry loop against a writer is a hang). Name it and hand the detail to the documentation.
  - `## When a seqlock is wrong` — when the read is expensive (retries become costly), when readers outnumber writers only slightly, or when the reader must take a reference to something it found. In that last case the answer is RCU, which forward-links to the next page.
- **Anchor:** a WaveDrom `signal` diagram over time: the sequence counter's value, a writer's critical section making it odd then even again, and two readers — one that starts and finishes cleanly, one that overlaps the writer and retries. Caption: "Two readers and one writer: the reader whose window overlaps the write sees an odd or changed counter and simply tries again."
- **KernelFacts:** `structure` — `[["seqcount_t", "include/linux/seqlock.h"], ["seqlock_t", "include/linux/seqlock.h"]]`; `path` — `"read_seqbegin() → read the data → read_seqretry() → retry if the counter moved"`; `observe` — `<Src file="kernel/time/timekeeping.c" symbol="ktime_get" />` — read the retry loop in the real timekeeping code; `trap` — "A seqlock protects readers from *seeing* torn data, not from *acting* on it. Anything a reader does inside the loop — dereferencing a pointer it read, taking a reference, logging a value — may be acting on garbage, so the loop must do nothing but copy."
- **References:**
  - `https://docs.kernel.org/locking/seqlock.html` — the in-tree documentation covering every variant, including the latch forms and the RT constraints.
  - `<Src file="include/linux/seqlock.h" symbol="read_seqbegin" />` — the macros and their barriers, with comments.
  - `<Src file="kernel/time/timekeeping.c" symbol="ktime_get" />` — the canonical user, in the code path a `clock_gettime` actually takes.
  - `<Src file="Documentation/memory-barriers.txt" />` — for the ordering requirements the read loop relies on.

- [ ] **Step 1: Write `mutexes-and-semaphores.md`** to the brief above.
- [ ] **Step 2: Write `rwlocks-and-rwsems.md`** to the brief above, taking the fairness behaviour from `Documentation/locking/` at v6.18 rather than from older writing.
- [ ] **Step 3: Write `seqlocks.md`** to the brief above.
- [ ] **Step 4: Verify** `mutex`, `mutex_optimistic_spin`, `completion`, `rw_semaphore`, `rwsem_down_read_slowpath`, `percpu_rw_semaphore`, `seqcount_t`, `read_seqbegin`, and `ktime_get` against Elixir v6.18.
- [ ] **Step 5: Cross-check the comparison table** in `rwlocks-and-rwsems.md` against the one that will appear in `./choosing-a-lock.md` (Task 32) — they must not contradict each other. Note in the plan-execution log which numbers were used so Task 32 can reuse them.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write mutexes, reader-writer locks, and seqlocks"
```

---

## Task 30: Folder 09 — RCU

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/rcu-the-idea.md`
- Modify: `docs/linux/09-concurrency-and-locking/rcu-in-practice.md`

**Interfaces:**
- Consumes: `09/memory-ordering-and-barriers` (Task 27) and `09/seqlocks` (Task 29, for the contrast).
- Produces: `09/rcu-in-practice`, a declared prerequisite of `09/choosing-a-lock`. RCU is assumed by folder 13's routing pages and folder 15's namespace pages in later phases, so this pair carries weight well beyond folder 09.

**These are the conceptual centrepiece of the folder.** Write `rcu-the-idea` completely before starting `rcu-in-practice`; the spec requires that order, and the second page is unwritable without the first being correct. The spec also requires context7 verification of the RCU API surface — do it before the second page.

### `rcu-the-idea.md` — RCU: The Idea

- **Opens with:** the question RCU answers, which is not "how do I exclude writers" but "what if readers paid nothing at all?" For data that is read constantly and modified rarely — a routing table, a list of registered handlers, a namespace's contents — even the cheapest lock's cache-line traffic dominates. RCU's answer is that readers take no lock, write nothing, and are never blocked, and the entire cost is moved onto writers.
- **Sections:**
  - `## The core insight` — you cannot modify data in place while lockless readers may be looking at it, so do not: build a new version, publish it with a single pointer store, and free the old version only after every reader that could still hold a reference to it has finished. Read-copy-update is a literal description of the three steps.
  - `## Publishing safely` — the pointer store must be ordered after the initialisation of what it points at, or a reader can follow the pointer to an uninitialised object. This is exactly the release/acquire pattern from `./memory-ordering-and-barriers.md` — link it, and note that `rcu_assign_pointer` and `rcu_dereference` are the RCU spellings of it.
  - `## Grace periods and quiescent states` — the definition, carefully: a quiescent state is a moment when a CPU is definitely not in an RCU read-side critical section (a context switch, a return to user space, going idle); a grace period is an interval in which every CPU has passed through at least one. After a grace period, no reader can still hold a reference obtained before it began. Emphasise the asymmetry: this is a *very* cheap thing to detect, because it needs no communication with readers at all.
  - `## What a reader actually does` — under a non-preemptible configuration, `rcu_read_lock()` compiles to almost nothing (it disables preemption); under `CONFIG_PREEMPT_RCU` it increments a per-task counter. Either way it never writes shared state and never blocks. Say plainly that this is what "free" means here, and it is the reason RCU is used where it is.
  - `## Why the deferred free is the whole cost` — a writer must wait for a grace period (milliseconds, potentially) or arrange a callback. That is fine when writes are rare and fatal when they are not, and it is the single criterion for whether RCU fits a problem.
  - `## What RCU does not give you` — it does not serialise writers against each other (they still need a lock), it does not give readers a consistent view across two different RCU-protected structures, and it does not prevent a reader from seeing a version that is about to be replaced. All three are properties, not deficiencies, and stating them prevents the most common misuse.
  - `## Where it is used` — a short list with links where the target exists in this phase: the dentry cache (Phase 3), routing tables (Phase 3), namespace lists (Phase 4), and `struct cred` — link `../06-processes-and-threads/credentials-and-identity.md`, which already named RCU.
- **Anchor:** a WaveDrom `signal` diagram of a grace period: three reader critical sections on three CPUs at different times, a writer's pointer update, and the grace period extending from the update until the last pre-existing reader finishes, with the free happening after it. Caption: "A grace period is not a fixed interval — it ends when the last reader that could have seen the old version has finished, and only then is it safe to free."
- **Second visual:** a Mermaid `flowchart LR` of the three steps — copy, modify, publish — with the old version pending on the callback list.
- **KernelFacts:** `structure` — `[["struct rcu_head", "include/linux/types.h"]]`; `path` — `"rcu_assign_pointer() publishes → readers under rcu_read_lock() may hold the old version → synchronize_rcu() waits a grace period → kfree() the old version"`; `observe` — `cat /sys/kernel/debug/rcu/rcu_preempt/rcugp` if present, otherwise `grep -i rcu /proc/softirqs` (verify what is available at v6.18); `trap` — "A grace period is not a timeout and has no fixed duration. It ends when every CPU has passed through a quiescent state, which on a busy machine is fast and on an idle or `nohz_full` one can take substantially longer."
- **References:**
  - `https://docs.kernel.org/RCU/whatisRCU.html` — the canonical introduction, written by RCU's author and the best starting point in existence for this topic.
  - Paul McKenney, *"RCU: What is it, and how does it work?"* — a recorded talk; embed with `<Video>` if a stable URL is available, otherwise cite it here. **One `<Video>` at most in this folder**, and this is the page for it if any.
  - McKenney, *Is Parallel Programming Hard…*, the deferred-processing chapter — free, and the fullest treatment of grace periods and their cost.
  - `https://docs.kernel.org/RCU/rcu.html` — the index into the rest of the in-tree RCU documentation, which is unusually extensive.

### `rcu-in-practice.md` — RCU in Practice **[Lab host=qemu]**

- **Opens with:** the reason this page is separate from the last one. RCU's rules are few and unforgiving: break one and nothing warns you, the code works in testing, and it corrupts memory once a month under load. Using RCU correctly is mostly a matter of knowing which five things you may not do.
- **Sections:**
  - `## The reader side` — `rcu_read_lock()`, `rcu_dereference()`, `rcu_read_unlock()`, and the rule that any pointer obtained inside the section is invalid outside it. Show a real read-side pattern in ` ```c `.
  - `## The writer side` — take your writer lock, copy, modify, `rcu_assign_pointer`, then dispose of the old version. Show it in ` ```c ` beside the reader.
  - `## Three ways to dispose` — a table: `synchronize_rcu()` (blocks the caller for a grace period; simple, may not be used in atomic context), `call_rcu()` (registers a callback; does not block), and `kfree_rcu()` (the common case, with no callback function to write). Columns: blocks?, allowed in atomic context?, and when to choose it.
  - `## RCU-protected lists` — `list_add_rcu`, `list_del_rcu`, and `list_for_each_entry_rcu`, plus the subtlety that makes them work: deletion leaves the removed element's forward pointer intact so a concurrent reader can finish traversing. Point back to `../04-kernel-architecture-and-idioms/kernel-data-structures.md` for the list itself.
  - `## The rules you must not break` — the page's core, as a numbered list, each with the failure it causes: (1) do not sleep in a classic RCU read-side section (SRCU exists for that); (2) do not let a pointer escape the section; (3) do not free without waiting for a grace period; (4) do not use `rcu_dereference` outside a read-side section or without holding the update lock (`rcu_dereference_protected` is for that); (5) do not assume a grace period bounds anything other than pre-existing readers.
  - `## SRCU` — sleepable RCU: readers may block, each domain has its own grace-period tracking, and the cost is a more expensive read side. Say when it is the right answer (a reader that must do I/O) and that it is not a drop-in replacement.
  - `## RCU flavours, briefly` — `rcu` (the unified flavour), `srcu`, and RCU-tasks, at v6.18. **Verify the current flavour list via context7 and the source**, because the flavours were consolidated and older material names variants that no longer exist.
  - `## Debugging` — `CONFIG_PROVE_RCU` catching illegal dereferences, RCU CPU stall warnings and what they actually mean (a CPU that has not reported a quiescent state — often a genuine loop in the kernel, sometimes a lost interrupt), and reading a stall trace.
  - `<Lab host="qemu" title="Make RCU stall, and watch lockdep catch a misuse" time="30 min">` — in the QEMU lab, with `CONFIG_PROVE_RCU` and `CONFIG_RCU_CPU_STALL_TIMEOUT` set low: (1) a module that dereferences an RCU pointer without `rcu_read_lock()` — `dmesg` shows the "suspicious RCU usage" splat, read it field by field; (2) a module that spins in the kernel with preemption disabled — `dmesg` shows an RCU CPU stall warning, read it too. Show both traces. `:::danger` — the second module deliberately makes a CPU unresponsive; on a single-CPU VM it hangs the machine and requires a reset. Give the VM at least two CPUs and expect to reset it. "If it fails": the splats need the debug options, which are not in a `defconfig` — the page must give the exact `.config` fragment.
- **Anchor:** a Mermaid `sequenceDiagram` — Writer, Reader on CPU 0, Reader on CPU 1, Grace-period machinery — showing the update, both readers finishing at different times, and the callback firing only after the later one. Caption: "The writer's `kfree_rcu` runs after the last pre-existing reader leaves, not after a fixed delay."
- **KernelFacts:** `structure` — `[["struct rcu_head", "include/linux/types.h"], ["struct srcu_struct", "include/linux/srcu.h"]]`; `path` — `"rcu_read_lock() → rcu_dereference() → use → rcu_read_unlock(); writer: rcu_assign_pointer() → kfree_rcu()"`; `observe` — `dmesg | grep -i 'rcu' | head` and `cat /proc/softirqs | grep -i rcu`; `trap` — "RCU misuse does not fail loudly. Dereferencing an RCU pointer without a read-side section works perfectly until the moment a writer frees the object underneath you — which is why `CONFIG_PROVE_RCU` in a debug build is not optional for code that uses RCU."
- **References:**
  - `https://docs.kernel.org/RCU/checklist.html` — the in-tree RCU checklist; every rule on this page should be traceable to it, and it is the single most useful document for a developer using RCU.
  - `https://docs.kernel.org/RCU/stallwarn.html` — how to read a stall warning, which is exactly what the lab produces.
  - `<Src file="include/linux/rcupdate.h" symbol="rcu_dereference" />` — the macro, including the lockdep annotation that makes `CONFIG_PROVE_RCU` work.
  - context7 verification of the current RCU API surface and flavour list — record the check date here, per the spec's currency table.

- [ ] **Step 1: Write `rcu-the-idea.md`** to the brief above. Do not start the second page until this one is finished and its grace-period explanation is right.
- [ ] **Step 2: Run the context7 check** on the RCU API surface and flavours, and date it.
- [ ] **Step 3: Write `rcu-in-practice.md`** to the brief above.
- [ ] **Step 4: Build both lab modules and run them in the QEMU lab**, capturing the real "suspicious RCU usage" splat and the real stall warning. Include the exact `.config` fragment required.
- [ ] **Step 5: Verify** `rcu_head`, `rcu_assign_pointer`, `rcu_dereference`, `synchronize_rcu`, `call_rcu`, `kfree_rcu`, `srcu_struct`, `list_for_each_entry_rcu`, and the flavour list against Elixir v6.18.
- [ ] **Step 6: Decide on the `<Video>`** — if a stable, current McKenney RCU talk URL is available, embed exactly one on `rcu-the-idea.md` with a required `title`; otherwise put it in `## References`. Do not embed more than one video in this folder.
- [ ] **Step 7: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write RCU, the idea and the practice"
```

---

## Task 31: Folder 09 — per-CPU data, and lock-free patterns

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/per-cpu-data.md`
- Modify: `docs/linux/09-concurrency-and-locking/lock-free-and-ring-buffers.md`

**Interfaces:**
- Consumes: `09/why-kernel-concurrency-is-different`, `09/memory-ordering-and-barriers`, and `computer-science/memory-hierarchy/cache-coherence-and-mesi` (Task 3).
- Produces: `09/per-cpu-data`, a declared prerequisite of `09/lock-free-and-ring-buffers`. The per-CPU idea is referred back to by folder 10's softirq page and folder 08's allocator page.

### `per-cpu-data.md` — Per-CPU Data

- **Opens with:** the strategy that beats every lock, when it applies — do not share the data. If each CPU has its own copy, there is no contention, no cache-line bouncing, and no lock to take. The kernel uses this everywhere it can, and the whole difficulty is in the cases where the data must eventually be combined.
- **Sections:**
  - `## Declaring and accessing` — `DEFINE_PER_CPU`, `DECLARE_PER_CPU`, `this_cpu_read`/`this_cpu_write`/`this_cpu_add`, and `per_cpu(var, cpu)` for reaching another CPU's copy. Show the shapes in ` ```c `.
  - `## Why `this_cpu_*` is not just an array index` — the operations are atomic *with respect to preemption and interrupts on this CPU* (on x86-64 they compile to a single instruction with a segment prefix), which is a stronger guarantee than "read the array and add". Say why that matters: without it, an interrupt between the read and the write corrupts the counter.
  - `## `get_cpu`/`put_cpu` and preemption` — if you take a pointer to a per-CPU variable and then get preempted, you may resume on a different CPU holding a pointer to the wrong copy. `get_cpu_ptr`/`put_cpu_ptr` disable preemption across the use. This is the single most common per-CPU bug and deserves the space.
  - `## Under PREEMPT_RT: `local_lock`` — preemption is not disabled by default there, so the implicit protection disappears and code must take a `local_lock_t`. Explain that this is why modern kernel code has `local_lock` where older code just relied on `preempt_disable`, and link `../07-scheduling/preemption-models.md`.
  - `## Per-CPU counters` — `percpu_counter` for statistics that are updated constantly and read rarely: each CPU accumulates locally and a batch threshold folds into a global total. Give the trade-off explicitly — the global value is approximate between folds — and say why that is the right trade for statistics and wrong for anything a decision depends on.
  - `## Where the kernel uses it` — a list with links where the target is written: the page allocator's per-CPU page lists (`../08-memory-management/the-page-allocator.md`), SLUB's per-CPU freelists (`../08-memory-management/slab-slub-and-kmalloc.md`), the per-CPU runqueue (`../07-scheduling/runqueues-and-scheduling-classes.md`), and softirq state (`../10-interrupts-time-and-deferred-work/softirqs.md`).
  - `## The cache-line connection` — per-CPU data is the structural answer to false sharing: not padding a shared structure but eliminating the sharing. Link `../../computer-science/memory-hierarchy/cache-coherence-and-mesi.md` and note that per-CPU areas are allocated with cache-line alignment for exactly this reason.
  - `## When it does not work` — data that must be globally consistent at every instant, data too large to replicate per CPU, and workloads that migrate between CPUs constantly. Each in a sentence.
- **Anchor:** a Mermaid `flowchart LR` contrasting one shared counter with a lock (four CPUs, one cache line, ping-pong drawn as arrows) and four per-CPU counters (four cache lines, no arrows between them) with a periodic fold into a global total. Caption: "The same counter, shared and per-CPU: the second version has no coherence traffic at all until the fold."
- **KernelFacts:** `structure` — `[["DEFINE_PER_CPU", "include/linux/percpu-defs.h"], ["struct percpu_counter", "include/linux/percpu_counter.h"]]`; `path` — `"this_cpu_add() → segment-prefixed instruction on this CPU's copy → periodic fold into the global counter"`; `observe` — `grep -E 'per_cpu|percpu' /proc/kallsyms | head` and `cat /proc/meminfo | grep Percpu`; `trap` — "A pointer to a per-CPU variable is only valid while you stay on that CPU. Take one, get preempted, and you are now updating another CPU's copy — which is why `get_cpu_ptr` disables preemption and why code that uses the raw accessor without it is broken in a way that only shows up under load."
- **References:**
  - `<Src file="include/linux/percpu-defs.h" />` — the declaration macros and the accessor families, with comments explaining the atomicity guarantees.
  - `https://docs.kernel.org/core-api/local_ops.html` — the local-operations documentation, which explains why these are cheaper than atomics.
  - `https://docs.kernel.org/locking/locktypes.html`, the `local_lock` section — what changes under PREEMPT_RT.
  - LWN, *"The percpu_counter API"*-type coverage and `<Src file="include/linux/percpu_counter.h" />` — for the approximate-counter trade-off.

### `lock-free-and-ring-buffers.md` — Lock-Free Patterns

- **Opens with:** an honest opening, because the topic attracts overreach. Lock-free code is harder to write, far harder to review, and rarely faster than a well-chosen lock. The kernel uses it in a small number of places where the constraints genuinely demand it — mostly where one side cannot take a lock at all — and this page is about those cases rather than about lock-free programming as an aspiration.
- **Sections:**
  - `## What "lock-free" actually means` — progress guarantees, briefly: lock-free means some thread makes progress; wait-free means every thread does. Note that most kernel "lock-free" code is really "one side is lock-free", which is a weaker and more useful property.
  - `## The one pattern that carries the weight: SPSC rings` — single producer, single consumer, a head index written only by the producer and a tail written only by the consumer, with a release store on publish and an acquire load on consume. Show it in ` ```c ` and walk why exactly two barriers are needed and where. This is the page's core and it is worth doing slowly.
  - `## `kfifo`` — the kernel's ready-made version, which is lockless only for the single-producer/single-consumer case and needs a lock otherwise. Say this explicitly, because the API's name suggests otherwise and misuse is common.
  - `## The BPF ring buffer` — the modern instance and the one readers will actually meet: a shared memory region consumed by user space, with the reservation/commit protocol that lets multiple producers write without a lock. Name it here; folder 18 owns it and this is a forward reference in prose.
  - `## Where else the kernel goes lock-free` — the printk ring buffer (because printing must work from NMI context, where no lock is safe), tracing ring buffers, and some statistics paths. Each in a sentence, with the *reason* the lock was unavailable, because that reason is the criterion.
  - `## Why most code should not` — the honest section. A lock-free algorithm is only correct against a memory model, and the review burden is enormous; the kernel has memory-model tooling (`herd7`, `litmus7`) precisely because informal reasoning is not sufficient. State that "we made it lock-free" is a claim requiring a litmus test, not an assertion.
  - `## The ABA problem in kernel terms` — a pointer reused between a read and a compare-and-swap. Give the kernel's usual answer — RCU-deferred freeing means the memory is not reused until a grace period passes, so ABA cannot occur — and link `./rcu-the-idea.md`. This connection is the most satisfying thing on the page.
- **Anchor:** a Mermaid `sequenceDiagram` for the SPSC ring — Producer writes the slot, `smp_store_release` on head, Consumer `smp_load_acquire` on head, reads the slot, `smp_store_release` on tail — with an annotation on each barrier saying what it prevents. Caption: "A single-producer ring: two barriers, each preventing one specific reordering, and no lock anywhere."
- **KernelFacts:** `structure` — `[["struct kfifo", "include/linux/kfifo.h"], ["struct printk_ringbuffer", "kernel/printk/printk_ringbuffer.h"]]` (verify); `path` — `"producer: write slot → smp_store_release(head); consumer: smp_load_acquire(head) → read slot → smp_store_release(tail)"`; `observe` — `<Src file="include/linux/kfifo.h" />` — read the macro's documentation block on when locking is required; `trap` — "`kfifo` is lockless only for one producer and one consumer. Two producers on the same `kfifo` without a lock is a corruption bug, and the API will not stop you."
- **References:**
  - `<Src file="include/linux/kfifo.h" />` — the header's comment block, which states the locking requirements precisely and is routinely ignored.
  - `https://docs.kernel.org/core-api/circular-buffers.html` — the in-tree explanation of the circular-buffer barriers; short, exact, and the authority for the SPSC section.
  - `<Src file="tools/memory-model/README" />` — the LKMM tooling, i.e. how a lock-free claim is actually checked.
  - `https://docs.kernel.org/core-api/printk-basics.html` and the printk ring-buffer documentation — the NMI-safety motivation.

- [ ] **Step 1: Write `per-cpu-data.md`** to the brief above.
- [ ] **Step 2: Write `lock-free-and-ring-buffers.md`** to the brief above, taking the barrier placement in the SPSC section from `Documentation/core-api/circular-buffers.rst` verbatim rather than deriving it.
- [ ] **Step 3: Verify** `DEFINE_PER_CPU`, `this_cpu_add`, `get_cpu_ptr`, `local_lock_t`, `percpu_counter`, `kfifo`, and the printk ring-buffer structure name against Elixir v6.18.
- [ ] **Step 4: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write per-CPU data and lock-free ring buffers"
```

---

## Task 32: Folder 09 — choosing a lock, and finding locking bugs

**Files:**
- Modify: `docs/linux/09-concurrency-and-locking/choosing-a-lock.md`
- Modify: `docs/linux/09-concurrency-and-locking/finding-locking-bugs.md`

**Interfaces:**
- Consumes: every page in folder 09.
- Produces: the folder's completion. `choosing-a-lock` is the page Phase 4's driver folder will link to whenever a lock choice comes up, so its decision table must be authoritative.

### `choosing-a-lock.md` — Choosing a Lock

- **Opens with:** the observation that the choice is usually forced rather than free. By the time you have answered "which contexts touch this data" and "may this code sleep", there is normally exactly one correct primitive, and the remaining freedom is in *granularity*, which matters far more than the choice of primitive.
- **Sections:**
  - `## The questions, in order` — (1) which contexts touch this data (process, softirq, hard IRQ, NMI)? (2) may the critical section sleep? (3) how long is it held? (4) what is the read/write ratio? (5) how contended is it, really? State that the first two eliminate most options and the rest are optimisation.
  - `## The decision table` — the page's anchor. Rows for `spinlock_t`, `spin_lock_irqsave`, `spin_lock_bh`, `raw_spinlock_t`, `struct mutex`, `rw_semaphore`, `seqlock_t`, RCU, per-CPU data, and atomics. Columns: contexts it is valid in, may the section sleep?, reader cost, writer cost, and the situation it fits. **Must be consistent with the table in `./rwlocks-and-rwsems.md`.**
  - `## Six worked selections` — real scenarios, each with the reasoning and the answer: (1) a driver's device state touched by a syscall path and its interrupt handler; (2) a rarely-changing list of registered callbacks read on every packet; (3) a per-CPU statistics counter; (4) a large data structure read for milliseconds under a syscall; (5) a small structure updated on every timer tick and read by `clock_gettime`; (6) a hash table with frequent lookups and occasional inserts. Each in three or four sentences. These six are what readers will actually copy.
  - `## The cost hierarchy` — orders of magnitude, stated as such: an uncontended atomic on a warm line, a same-core uncontended lock, a contended lock within one LLC, a contended lock across sockets, and a context switch. Link the CS coherence page for why the shape is what it is.
  - `## Granularity beats primitive` — the section that matters most. One lock for a whole subsystem is simple and does not scale; one lock per object scales and creates ordering hazards. Give the progression (global lock → per-bucket → per-object → per-CPU/RCU) and say plainly that most real scalability work is moving along it, not swapping one primitive for another. The `mmap_lock` story from `./rwlocks-and-rwsems.md` is the worked instance.
  - `## Lock ordering` — if you take two locks, every path must take them in the same order, and the order must be documented next to the definitions. This is the discipline lockdep enforces, and it is the natural handoff to the next page.
  - `## The rule for new code` — start with the simplest correct primitive, measure, and only then optimise. State it, because the folder has just spent eleven pages describing sophisticated options and a reader may draw the wrong conclusion.
- **Anchor:** the decision table.
- **KernelFacts:** `structure` — `[["spinlock_t", "include/linux/spinlock_types.h"], ["struct mutex", "include/linux/mutex.h"]]`; `path` — `"which contexts? → may it sleep? → hold time? → read/write ratio? → primitive"`; `observe` — `sudo cat /proc/lock_stat | head -30` (requires `CONFIG_LOCK_STAT`, which shows contention per lock and is the measurement this page's last section calls for); `trap` — "Choosing the fastest primitive rarely helps; changing what is shared almost always does. A contended lock is a granularity problem, and swapping a mutex for a spinlock leaves the contention exactly where it was."
- **References:**
  - `https://docs.kernel.org/kernel-hacking/locking.html` — the in-tree guide, which includes its own version of this decision material and should be cross-checked against.
  - `https://docs.kernel.org/locking/locktypes.html` — the definitive type list and their PREEMPT_RT behaviour; the authority for the table's first two columns.
  - `https://docs.kernel.org/locking/lockstat.html` — the contention measurement this page recommends.
  - McKenney, *Is Parallel Programming Hard…*, the partitioning chapter — the case that granularity is the real lever; free.

### `finding-locking-bugs.md` — Finding Locking Bugs **[Lab host=qemu]**

- **Opens with:** the property that makes locking bugs uniquely nasty and uniquely tractable. Nasty, because they surface as corruption far from the cause, months later, on one machine. Tractable, because deadlock is a *structural* property — a cycle in the lock-ordering graph — and a machine can find the cycle without the deadlock ever happening. `lockdep` is that machine.
- **Sections:**
  - `## What lockdep actually proves` — it records, for every lock acquired, which locks were already held, building a lock-order graph across *classes* rather than instances. A cycle in that graph means a deadlock is possible, and lockdep reports it the first time the second ordering is observed — **even though no deadlock occurred**. State this clearly; it is the thing that makes lockdep worth its overhead.
  - `## Lock classes, and why the distinction matters` — two instances of the same struct's lock are one class by default, so taking two of them nests and lockdep complains. `spin_lock_nested` and `lockdep_set_class` exist for the legitimate cases (a tree with per-node locks). This is why real lockdep reports sometimes need thought rather than a fix.
  - `## Reading a splat, line by line` — the page's anchor and its main value. Take a real report and walk it: the header naming the possible deadlock, the two (or more) lock chains, the stack traces for each, the "possible unsafe locking scenario" block, and the final list of held locks. Say which two lines a reader should read first.
  - `## The classes of report` — a table: ABBA ordering inversion, IRQ-unsafe versus IRQ-safe ordering (taking a lock in process context that is also taken in an interrupt handler, without `irqsave`), recursive acquisition, and "held lock freed". Each with what it means and the usual fix.
  - `## `CONFIG_DEBUG_ATOMIC_SLEEP`` — catches sleeping in atomic context: the "BUG: sleeping function called from invalid context" message, which is a different check with a similar-looking output. Show one and name the three usual causes (a `GFP_KERNEL` allocation, a mutex, a `copy_to_user`, each under a spinlock).
  - `## KCSAN` — the data-race detector: sampling-based, finds races on plain accesses that no lock check can see, and reports both accesses. Say what it costs and that it belongs in a dedicated test kernel rather than a lab default.
  - `## The debug config` — the exact fragment for a lab kernel: `CONFIG_PROVE_LOCKING`, `CONFIG_DEBUG_ATOMIC_SLEEP`, `CONFIG_DEBUG_MUTEXES`, `CONFIG_DEBUG_SPINLOCK`, `CONFIG_LOCK_STAT`, and `CONFIG_PROVE_RCU`, with the honest note on overhead. Link back to `../01-lab-and-toolchain/building-a-kernel.md`.
  - `<Lab host="qemu" title="Produce a lockdep splat and read it" time="30 min">` — a module with two spinlocks taken in opposite orders on two code paths, triggered from a debugfs write. Load it, trigger both paths, and read the resulting splat against the section above. Then a second variant that takes a mutex under a spinlock, producing the atomic-sleep BUG. Show both traces in full. "If it fails": lockdep disables itself permanently after the *first* report in a boot, so the second test needs a reboot — say this before the reader discovers it, because it is confusing and it is by design.
- **Anchor:** a real lockdep splat in a ` ```text ` block, annotated with callouts for the five parts a reader must find.
- **Second visual:** a Mermaid `flowchart LR` of the lock-order graph for the ABBA case, showing the cycle lockdep detected.
- **KernelFacts:** `structure` — `[["struct lockdep_map", "include/linux/lockdep_types.h"], ["struct held_lock", "include/linux/lockdep.h"]]`; `path` — `"lock acquired → lockdep records class and the held set → edge added to the order graph → cycle detected → splat, and lockdep disables itself"`; `observe` — `dmesg | grep -A 40 'possible circular locking dependency'`; `trap` — "lockdep reports a deadlock that *could* happen, not one that did — and it turns itself off after the first report in a boot, so a second bug in the same boot is invisible. Always fix the first splat and reboot before concluding the kernel is clean."
- **References:**
  - `https://docs.kernel.org/locking/lockdep-design.html` — how the class graph and the validation work; the reason lockdep can prove things it never observed.
  - `https://docs.kernel.org/dev-tools/kcsan.html` — the data-race detector, its sampling model, and how to read its reports.
  - `https://docs.kernel.org/locking/lockstat.html` — contention statistics, for the performance side rather than the correctness side.
  - `https://docs.kernel.org/dev-tools/index.html` — the index of the rest of the debug tooling, which folder 17 will cover properly in Phase 5.

- [ ] **Step 1: Write `choosing-a-lock.md`** to the brief above, reusing the comparison numbers agreed in Task 29 so the two tables agree.
- [ ] **Step 2: Build the two buggy modules and run them in the QEMU lab**, capturing a real lockdep splat and a real atomic-sleep BUG. **Do not fabricate either trace** — the format is version-specific and a made-up splat teaches the wrong shape.
- [ ] **Step 3: Write `finding-locking-bugs.md`** from the captured traces.
- [ ] **Step 4: Verify** `lockdep_map`, `held_lock`, `spin_lock_nested`, `lockdep_set_class`, and every `CONFIG_` symbol in the debug fragment against Elixir v6.18 and `kernel/locking/Kconfig`.
- [ ] **Step 5: Folder-09 completeness check** — thirteen pages written, the two comparison tables consistent, and `memory-ordering-and-barriers` carrying the load-bearing arm64 contrast note the spec requires.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/09-concurrency-and-locking
git commit -m "docs: write lock selection and finding locking bugs"
```

---
## Task 33: Folder 10 — an interrupt arrives, and the IRQ subsystem

**Files:**
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/how-an-interrupt-reaches-the-kernel.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/the-irq-subsystem.md`

**Interfaces:**
- Consumes: `05/the-entry-path` (the kernel-entry mechanics), `computer-science/buses-and-io/interrupt-controllers` (Task 4 — the hardware), and `computer-science/cpu-architecture/exceptions-traps-and-interrupts` (the taxonomy).
- Produces: `10/how-an-interrupt-reaches-the-kernel`, the declared prerequisite of `10/the-irq-subsystem` and `10/timekeeping-and-clocksources`, and `10/the-irq-subsystem`, a prerequisite of `10/hardirq-context` and `10/interrupt-affinity-and-balancing`.

### `how-an-interrupt-reaches-the-kernel.md` — How an Interrupt Reaches the Kernel

- **Opens with:** the completion of the boundary story folder 05 started. A syscall is the process asking to enter the kernel; an interrupt is the *world* forcing the kernel to run, at a moment nothing chose, in the context of whatever task happened to be on that CPU. That last detail — the handler runs in a borrowed context that has nothing to do with the device — is the source of every rule in this folder.
- **Sections:**
  - `## The chain` — device asserts or writes → interrupt controller decides which CPU and which vector → CPU takes the interrupt at an instruction boundary → the IDT entry for that vector → the kernel's entry stub → `irq_enter` → the handler. Draw it once, name what each link contributes, and hand the first two links to the CS interrupt-controller page rather than re-teaching them.
  - `## What the CPU does` — pushes the same frame a fault pushes, switches stack if the privilege level changes, and clears `IF` for a maskable interrupt. Note the IST stacks for the vectors that cannot use the current stack (NMI, double fault, machine check) and why: an NMI arriving during entry must not use a stack the entry code has not finished setting up.
  - `## Vectors, and how Linux numbers them` — the crucial distinction: the *hardware* vector is an x86-64 IDT index, the *Linux IRQ number* is a software identifier assigned by an irq domain, and they are not the same thing. State it here, because `/proc/interrupts` shows the second and people look for the first.
  - `## `irq_enter` and `irq_exit`` — the bookkeeping that makes the context real: `preempt_count` gets its hardirq bits set, so `in_interrupt()` becomes true, RCU is told this CPU is in an interrupt, and on the way out pending softirqs are run. That last one is the hinge between this page and `./softirqs.md`.
  - `## Whose stack, and whose time` — on x86-64 the handler runs on a per-CPU IRQ stack (verify at v6.18), and the CPU time is accounted to `hi` (hardirq) rather than to the interrupted task. Say why the accounting matters: a machine with a high `hi` figure in `top` is not spending time on any process, and no process-level profiler will show it.
  - `## Nesting, and why Linux does not` — interrupts are disabled during a handler by default, so handlers do not nest. Note that this was not always true and that older material describes nested handling.
  - `## arm64` — `:::note`: the vector table is indexed by exception category and origin rather than by a 256-entry vector; the interrupt source is then read from the GIC's interface register. This is why arm64 has one IRQ vector entry and x86-64 has many, and why the GIC's acknowledge/end-of-interrupt protocol has no direct x86 analogue.
- **Anchor:** a Mermaid `sequenceDiagram` — Device, Interrupt controller, CPU, Kernel entry, Handler — with the vector number labelled where the controller hands it to the CPU and the Linux IRQ number labelled where the kernel translates it. Caption: "One interrupt from the wire to the handler, with the two different numbers it is known by on the way."
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"], ["struct irq_desc", "include/linux/irqdesc.h"]]`; `path` — `"device → APIC → IDT vector → common_interrupt() → irq_enter() → handle_irq_event() → handler → irq_exit()"` (verify each at v6.18); `observe` — `cat /proc/interrupts | head -20 && grep -E '^(intr|softirq)' /proc/stat`; `trap` — "An interrupt handler runs in the context of whatever task was unlucky enough to be on that CPU. Its CPU time is charged to `hi`, not to that task and not to the device's driver — which is why interrupt cost is invisible to every per-process profiler."
- **References:**
  - `<Src file="arch/x86/kernel/irq.c" symbol="common_interrupt" />` — the x86-64 entry point where a vector becomes a Linux IRQ.
  - `https://docs.kernel.org/core-api/genericirq.html` — the generic IRQ layer's own documentation, which is the authority for the rest of the folder.
  - `../../computer-science/buses-and-io/interrupt-controllers.md` — the hardware this page deliberately does not re-teach.
  - Intel SDM Vol. 3A, ch. 6 — the interrupt frame, IST stacks, and what the CPU does at an interrupt.

### `the-irq-subsystem.md` — The IRQ Subsystem **[WAH]**

- **Opens with:** the abstraction problem the generic IRQ layer solves. A driver wants to say "call me when my device needs attention"; the machine underneath might be an x86 with an I/O APIC, an x86 with MSI-X, or an arm64 with a two-level GIC hierarchy. The subsystem's job is to make one `request_irq` call work on all of them, and its structures are shaped entirely by that.
- **Sections:**
  - `## `irq_desc`` — one per Linux IRQ number: the handler list, the chip, the flow handler, the per-CPU statistics, and the lock. Show the shape as a Mermaid `classDiagram` rather than a dump.
  - `## `irq_chip`` — the controller abstraction: `irq_mask`, `irq_unmask`, `irq_ack`, `irq_eoi`, `irq_set_affinity`. This is the vtable that makes an APIC and a GIC interchangeable to the layers above, and naming its members is the fastest way to convey what a controller must do.
  - `## Flow handlers` — `handle_level_irq`, `handle_edge_irq`, `handle_fasteoi_irq`: the per-trigger-type sequencing of mask, ack, call, unmask. Explain why level and edge need different sequences, referring to the level-versus-edge section of the CS page.
  - `## irq domains` — the mapping from a controller-local hardware number to a Linux IRQ number, and the reason it exists: with nested controllers there is no global numbering, and device tree or ACPI describes interrupts relative to a controller. Give the concrete consequence: the number in `/proc/interrupts` is allocated, not fixed, and can differ between boots.
  - `## `request_irq` and its flags` — `IRQF_SHARED`, `IRQF_ONESHOT`, `IRQF_NO_THREAD`, `IRQF_TRIGGER_*`. A table with what each does and when a driver needs it.
  - `## Shared interrupts and the return contract` — with a shared line every registered handler is called on every interrupt, so each must check whether *its* device raised it and return `IRQ_NONE` if not, `IRQ_HANDLED` if it did. Say why this matters beyond tidiness: the spurious-interrupt detector counts consecutive `IRQ_NONE` returns and will disable a line that appears to be stuck, so a handler that lies about handling an interrupt breaks the kernel's own protection.
  - `## What actually happens` **[WAH]** — reading `/proc/interrupts` column by column on a real machine. The IRQ number, the per-CPU counts, the chip name, the hardware number and trigger type, and the device name(s). Show a real file and read six lines aloud: a timer, a NIC's MSI-X queues, an NVMe queue, a shared legacy line, and the non-numeric rows at the bottom (`NMI`, `LOC`, `RES`, `CAL`, `TLB`) — noting that `TLB` is the shootdown IPI from `../08-memory-management/tlb-and-address-space-switching.md` and `RES` is the rescheduling IPI. That connection lands two earlier folders in one table.
  - `## Spurious interrupts` — the detector, the `irqpoll` boot option, and the "nobody cared" message with what it actually indicates.
- **Anchor:** a Mermaid `classDiagram` linking `irq_desc` → `irq_data` → `irq_chip` and `irq_domain`, with the action list of registered handlers, annotated with which piece each `/proc/interrupts` column comes from. Caption: "The structures behind one line of `/proc/interrupts`, and which of them the driver actually touches."
- **KernelFacts:** `structure` — `[["struct irq_desc", "include/linux/irqdesc.h"], ["struct irq_chip", "include/linux/irq.h"]]`; `path` — `"request_irq() → setup_irq_thread or direct → irq fires → handle_fasteoi_irq() → handle_irq_event() → your handler → IRQ_HANDLED"` (verify at v6.18); `observe` — `cat /proc/interrupts && ls /sys/kernel/irq/`; `trap` — "Returning `IRQ_HANDLED` when your device did not raise the interrupt is not harmless politeness — it defeats the spurious-interrupt detector, which is the only thing standing between a stuck level-triggered line and a livelocked machine."
- **References:**
  - `https://docs.kernel.org/core-api/genericirq.html` — the definitive description of `irq_desc`, chips, and flow handlers.
  - `https://docs.kernel.org/core-api/irq/irq-domain.html` — why domains exist and how a hardware number becomes a Linux IRQ.
  - `man 5 proc`, the `/proc/interrupts` section — the column definitions for the [WAH] section.
  - `<Src file="kernel/irq/manage.c" symbol="request_threaded_irq" />` — the registration path that `request_irq` wraps, where the flags are validated.

- [ ] **Step 1: Write `how-an-interrupt-reaches-the-kernel.md`** to the brief above.
- [ ] **Step 2: Write `the-irq-subsystem.md`** to the brief above, using a **real** `/proc/interrupts` from a machine with an NVMe drive and a multi-queue NIC so the MSI-X rows are genuine.
- [ ] **Step 3: Verify** `common_interrupt`, `irq_desc`, `irq_chip`, `irq_domain`, `handle_fasteoi_irq`, `handle_irq_event`, `request_threaded_irq`, and the IRQ-stack arrangement at v6.18.
- [ ] **Step 4: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/10-interrupts-time-and-deferred-work
git commit -m "docs: write how an interrupt reaches the kernel and the IRQ subsystem"
```

---

## Task 34: Folder 10 — hard-IRQ rules, softirqs, and tasklets

**Files:**
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/hardirq-context.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/softirqs.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/tasklets-and-their-replacement.md`

**Interfaces:**
- Consumes: `10/the-irq-subsystem` (Task 33) and `09/why-kernel-concurrency-is-different` (Task 27) — the context matrix defined there is the framework for this whole task.
- Produces: `10/hardirq-context`, the declared prerequisite of `10/softirqs` and `10/workqueues`.

### `hardirq-context.md` — Hard IRQ Context and Its Rules

- **Opens with:** the derivation rather than the list. Everything a handler may not do follows from one fact — the handler is not running on behalf of any task — plus one consequence: there is nothing to put on a wait queue, nothing to charge the time to, and nothing to resume if it blocks. The rules are not conventions; they are the only options.
- **Sections:**
  - `## What "no task" means` — the handler borrows a CPU and a stack from whatever was interrupted. `current` points at a task that has nothing to do with the interrupt, and touching that task's state would be corrupting an innocent bystander.
  - `## The rules, each derived` — a table with a row per rule: may not sleep (nothing to wake), may not `GFP_KERNEL` allocate (it may reclaim, which may sleep), may not take a mutex (it may sleep), may not `copy_to_user` (there is no meaningful user address space, and it may fault and sleep), may not call `schedule()` (there is nothing to schedule away from). Every row's third column is the derivation, not a restatement.
  - `## What it may do` — `GFP_ATOMIC` allocation, spinlocks (the `irqsave` variants where needed), per-CPU data, atomic operations, waking a task, and scheduling deferred work. Note that "waking a task" is the escape hatch that makes everything else possible.
  - `## Interrupts are disabled, so be quick` — while a handler runs, that CPU takes no further interrupts, so every microsecond in a handler is added to the latency of every other device on that CPU. Give the practical target — a handler should acknowledge the device, grab what it must, and defer everything else — and note that this pressure is the entire reason the rest of the folder exists.
  - `## Measuring handler time` — `/proc/interrupts` counts, the `irq_handler_entry`/`irq_handler_exit` tracepoints, and `hi` in `/proc/stat`. Enough to answer "is a handler too slow" with data.
  - `## Threaded handlers change all of this` — a forward pointer in one paragraph to `./threaded-irqs.md`: if the handler runs in a kthread, it is process context again and the rules relax. Say that this is why PREEMPT_RT can afford to do it universally.
  - `## The three deferral mechanisms` — the folder's map, stated here so the reader knows what is coming: softirq (same CPU, still atomic, very soon), tasklet (built on softirq, serialised, deprecated), workqueue (process context, may sleep, later). A three-row table with the choice criterion for each.
- **Anchor:** the derivation table above — the rule, what happens if you break it, and the underlying reason.
- **KernelFacts:** `structure` — `[["preempt_count", "include/linux/preempt.h"], ["struct irqaction", "include/linux/interrupt.h"]]`; `path` — `"irq_enter() sets the hardirq bits in preempt_count → in_interrupt() true → handler → irq_exit() → pending softirqs run"`; `observe` — `grep -E 'CONFIG_DEBUG_ATOMIC_SLEEP' /boot/config-$(uname -r) && grep '^intr' /proc/stat | cut -c1-60`; `trap` — "The rules for interrupt context are not about speed. Calling a sleeping function there does not make the machine slow — it makes the scheduler try to switch away from a context that has nowhere to switch back to, which is a hang."
- **References:**
  - `https://docs.kernel.org/kernel-hacking/hacking.html`, the interrupt-context sections — the in-tree statement of these rules with the reasoning.
  - `https://docs.kernel.org/core-api/genericirq.html` — the handler contract and what a flow handler expects of it.
  - `<Src file="include/linux/preempt.h" />` — the `preempt_count` field layout, which is the machine-readable definition of "in interrupt context".
  - `<Src file="Documentation/kernel-hacking/locking.rst" />` — the locking rules per context, which this page's table must agree with.

### `softirqs.md` — Softirqs **[WAH]** **[Misc]**

- **Opens with:** the compromise softirqs represent. Interrupt handlers must be short, but the work still has to happen, and much of it (processing a received packet, completing a block I/O) must happen *soon* and cannot wait for a scheduler decision. A softirq is work that runs with interrupts enabled, on the same CPU, almost immediately — still atomic, but no longer blocking every other device.
- **Sections:**
  - `## A fixed set, and why` — `HI`, `TIMER`, `NET_TX`, `NET_RX`, `BLOCK`, `IRQ_POLL`, `TASKLET`, `SCHED`, `HRTIMER`, `RCU` (verify the list at v6.18). They are compile-time constants, not a registration interface, because the dispatch is a bitmask scan and because the kernel deliberately does not want subsystems adding more. Say that plainly — the fixed set is a policy, not a limitation nobody got around to fixing.
  - `## Raising and running` — `raise_softirq` sets a bit in a per-CPU mask; the mask is checked on interrupt exit and run there, or handed to `ksoftirqd` if there is too much. Note the important detail: the softirq usually runs on the CPU that raised it, so per-CPU data needs no lock between the handler and the softirq — but a softirq *can* run on multiple CPUs simultaneously, unlike a tasklet, which is the difference the next page turns on.
  - `## The budget` — the interrupt-exit loop runs a bounded number of iterations (or for a bounded time) before deferring the rest to `ksoftirqd`, because an unbounded loop under load starves user space entirely. Give the mechanism and note the tunables if any exist at v6.18.
  - `## `ksoftirqd`` — a per-CPU kernel thread that is scheduled like any other task, so under heavy softirq load the work becomes visible to the scheduler and stops starving processes. Say what its appearance at the top of `top` actually means: not "ksoftirqd is broken" but "this CPU is receiving more deferred work than it can process inline".
  - `## What actually happens` **[WAH]** — the `si` column in `top` on a machine under network load. Walk it: packets arrive, the NIC raises an interrupt, the handler schedules NAPI polling, the poll runs in `NET_RX` softirq context and processes a batch, the budget is exhausted, and the remainder moves to `ksoftirqd`. Show `top` and `/proc/softirqs` under a real load. The reader should finish understanding that `si` is packet processing, not a mysterious system overhead, and that the number to correlate it with is the interrupt and packet rate.
  - `## The rules still apply` — a softirq may not sleep. It is atomic context with interrupts enabled, which is a *different* set of constraints from hard-IRQ context and the same prohibition on sleeping. Point back at the context matrix.
  - `## `local_bh_disable`` — how process-context code excludes softirqs on its CPU, and why `spin_lock_bh` exists as the combined form.
  - `## Misconceptions` **[Misc]** — (1) "softirqs are threads" — they usually run on the interrupt-exit path, and only overflow into `ksoftirqd`; (2) "high `si` means a kernel problem" — it usually means high packet or I/O completion rates; (3) "a softirq runs on one CPU at a time" — the same softirq can run concurrently on several CPUs, which is exactly why it needs locking and a tasklet does not.
- **Anchor:** a Mermaid `flowchart TB` from the hardware interrupt through `irq_exit`, the softirq pending mask, the bounded run loop, and the branch to `ksoftirqd` when the budget is exhausted. Caption: "Where deferred work runs: on the interrupt-exit path until the budget runs out, then in a schedulable thread."
- **KernelFacts:** `structure` — `[["struct softirq_action", "include/linux/interrupt.h"]]`; `path` — `"raise_softirq() → per-CPU pending mask → irq_exit() → handle_softirqs() → the action → or wakeup_softirqd()"` (**verify — `__do_softirq` was renamed to `handle_softirqs` in the 6.10 era**); `observe` — `cat /proc/softirqs && top -bn1 | head -5`; `trap` — "`ksoftirqd` at the top of `top` is a symptom, not a cause. It means this CPU received more softirq work than it could process on the interrupt-exit path — the fix is upstream of it, in the interrupt rate or the work per packet."
- **References:**
  - `<Src file="kernel/softirq.c" symbol="handle_softirqs" />` — the run loop, the budget, and the `ksoftirqd` handoff, all in one function; verify the symbol name at v6.18.
  - `https://docs.kernel.org/core-api/genericirq.html` and the in-tree softirq material — for the fixed-set rationale.
  - `man 5 proc`, the `/proc/softirqs` section — the per-CPU per-type counters used in the [WAH] section.
  - LWN's coverage of softirq latency and the proposals to rework it — cite one specific article, note its date, and say whether anything landed by v6.18.

### `tasklets-and-their-replacement.md` — Tasklets, and Why They Are Going Away

- **Opens with:** an honest framing for a page about a deprecated mechanism. Tasklets are still in hundreds of drivers, so a reader will meet them; they are also the wrong choice for new code, and the reasons they are wrong are instructive about the whole deferral design space.
- **Sections:**
  - `## What a tasklet is` — a function scheduled to run in softirq context, built on the `TASKLET` and `HI` softirqs, with one property softirqs do not have: **the same tasklet never runs concurrently on two CPUs**. That guarantee is the entire appeal, because it means the tasklet's data needs no lock against itself.
  - `## The API` — `DECLARE_TASKLET`, `tasklet_schedule`, `tasklet_disable`/`enable`, `tasklet_kill`. Note that the callback signature changed (from an `unsigned long` to a `struct tasklet_struct *`) and that both forms appear in the tree, which is exactly the kind of thing that confuses a reader of old and new drivers side by side.
  - `## Why it is deprecated` — three concrete reasons, not a vague "it is old": the serialisation is *global* per tasklet, so it does not scale and can add latency; a tasklet cannot sleep, so it does not simplify anything a softirq did not already do; and the disable/kill lifetime rules are subtle enough that use-after-free bugs are common. State that the kernel has been converting them away for years.
  - `## What to use instead` — a decision table: work that must run soon and is atomic → a threaded IRQ handler or an existing softirq; work that may sleep → a workqueue; work with a deadline → an hrtimer. Each row names the page that covers it, all of which are in this folder.
  - `## Reading tasklet code you did not write` — the practical closing: what to check when you meet one (does it rely on the serialisation guarantee? does it have a `tasklet_kill` on the teardown path?), and the specific bug to look for — freeing the structure a tasklet is scheduled on without killing it first.
  - `## The lesson` — one paragraph, worth stating because it generalises: tasklets offered a guarantee (no concurrency with itself) that removed the need for a lock, and paid for it with a global serialisation that hurts under load. That is the same trade that shows up in every "we made this simpler by making it single-threaded" design.
- **Anchor:** a table comparing softirq, tasklet, threaded IRQ, and workqueue across five columns — context, may sleep?, runs concurrently on multiple CPUs?, latency, and status (current or deprecated). This table is the folder's summary and is worth getting exactly right.
- **KernelFacts:** `structure` — `[["struct tasklet_struct", "include/linux/interrupt.h"]]`; `path` — `"tasklet_schedule() → per-CPU tasklet list → TASKLET_SOFTIRQ → tasklet_action() → callback, with a per-tasklet RUN flag preventing concurrency"`; `observe` — `grep -c tasklet /proc/kallsyms && cat /proc/softirqs | grep -i tasklet`; `trap` — "A tasklet's 'no concurrent execution' guarantee is global, not per-CPU. Under load, every CPU that schedules that tasklet is serialised behind whichever one is running it, which is the opposite of what a per-CPU deferral mechanism should do."
- **References:**
  - `<Src file="include/linux/interrupt.h" symbol="tasklet_struct" />` — the structure and the state flags that implement the serialisation.
  - LWN, *"The end of the tasklet"*-type coverage of the deprecation effort — cite the specific article and its date; the conversion is long-running and its state at v6.18 should be stated honestly.
  - `https://docs.kernel.org/core-api/workqueue.html` — the recommended replacement for the sleeping case.
  - `<Src file="kernel/softirq.c" symbol="tasklet_action" />` — the dispatch, where the run flag and the serialisation are visible.

- [ ] **Step 1: Write `hardirq-context.md`** to the brief above, cross-checking the rules table against the context matrix in `09/why-kernel-concurrency-is-different` so the two agree exactly.
- [ ] **Step 2: Write `softirqs.md`** to the brief above, with a real `/proc/softirqs` and a real `top` line captured under network load (an `iperf3` run against another machine or a VM will do).
- [ ] **Step 3: Write `tasklets-and-their-replacement.md`** to the brief above.
- [ ] **Step 4: Verify** the softirq type list, `handle_softirqs` (or its v6.18 name), `raise_softirq`, `wakeup_softirqd`, `softirq_action`, `tasklet_struct`, `tasklet_action`, and the tasklet callback signature against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/10-interrupts-time-and-deferred-work
git commit -m "docs: write hard IRQ rules, softirqs, and tasklets"
```

---

## Task 35: Folder 10 — workqueues, threaded IRQs, and affinity

**Files:**
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/workqueues.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/threaded-irqs.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/interrupt-affinity-and-balancing.md`

**Interfaces:**
- Consumes: `10/hardirq-context` (Task 34), `10/the-irq-subsystem` (Task 33), and `07/real-time-scheduling` (Task 18).
- Produces: `10/workqueues`, the declared prerequisite of `10/threaded-irqs`. Folder 08's writeback page already links here, and Phase 4's driver folder will link here constantly.

### `workqueues.md` — Workqueues **[Lab host=qemu]**

- **Opens with:** the mechanism that finally lifts the restriction. Softirqs and tasklets defer work but keep it atomic; a workqueue moves the work into a kernel thread, which means process context, which means it may sleep — allocate with `GFP_KERNEL`, take a mutex, wait for I/O. That single capability is why most driver deferred work ends up here.
- **Sections:**
  - `## The model` — a work item (a function plus a `struct work_struct` embedded in your own structure — the `container_of` idiom from folder 04, so link it) queued onto a workqueue and executed by a worker thread from a pool.
  - `## Concurrency-managed workqueues` — the design that replaced per-workqueue thread pools: shared per-CPU worker pools, workers created on demand, and the concurrency manager that starts another worker when a running one sleeps. Explain the point — a workqueue used to cost a thread per queue per CPU, and now costs none until work exists.
  - `## The default queues` — `system_wq`, `system_highpri_wq`, `system_long_wq`, `system_unbound_wq`, and `system_freezable_wq`. A table: what each is for and, crucially, `schedule_work()`'s target. Note the rule that work on `system_wq` should be short, because it shares a pool with everyone else.
  - `## Your own workqueue` — `alloc_workqueue` with `WQ_*` flags: `WQ_UNBOUND` (not tied to a CPU; the scheduler places the worker, which is right for long or CPU-heavy work), `WQ_MEM_RECLAIM` (guarantees a rescuer thread so the queue can make progress during reclaim — **required** for any work on a memory-reclaim path, and forgetting it deadlocks under memory pressure), `WQ_HIGHPRI`, `WQ_FREEZABLE`, and `max_active`.
  - `## Delayed and cancellable work` — `INIT_DELAYED_WORK`, `queue_delayed_work`, `cancel_work_sync`, `cancel_delayed_work_sync`, and `flush_workqueue`. Say what each waits for, precisely, because the difference between `cancel_work` and `cancel_work_sync` is exactly the lifetime bug in the next section.
  - `## The lifetime bug everyone writes once` — free the structure containing the `work_struct` while the work is still queued or running. The fix is `cancel_work_sync` (or `cancel_delayed_work_sync`) on the teardown path, before the free, every time. Give the symptom (a use-after-free that KASAN reports inside the workqueue code, pointing nowhere near the driver) and say why it is hard to diagnose without knowing this pattern.
  - `## Workqueue versus threaded IRQ versus kthread` — a small selection table, since all three give process context. Criteria: does it need to be tied to an interrupt (threaded IRQ), is it a long-lived loop (kthread), or is it bursty short work (workqueue)?
  - `<Lab host="qemu" title="A module that defers work three ways" time="30 min">` — a module with a debugfs trigger that (1) does the work inline in the write handler, (2) schedules it on `system_wq`, and (3) schedules it on its own `WQ_UNBOUND` queue — each logging `current->comm` and `in_interrupt()`. Read `dmesg` and see the context change. Then add a `msleep` to the work function and observe it succeeding in the workqueue and being caught by `CONFIG_DEBUG_ATOMIC_SLEEP` if attempted in a tasklet. Show all output. "If it fails": the debug splat needs `CONFIG_DEBUG_ATOMIC_SLEEP`, and unloading the module while work is pending is exactly the lifetime bug — the lab should demonstrate that deliberately, with `cancel_work_sync` added afterwards as the fix.
- **Anchor:** a Mermaid `sequenceDiagram` — Driver (IRQ context), Workqueue, Worker thread, Sleeping operation — showing the handler queueing work and returning immediately, and the worker later sleeping without harm. Caption: "The handoff from a context that may not sleep to one that may, which is the whole purpose of a workqueue."
- **KernelFacts:** `structure` — `[["struct work_struct", "include/linux/workqueue.h"], ["struct workqueue_struct", "kernel/workqueue.c"]]`; `path` — `"schedule_work() → queue_work_on() → worker pool → process_one_work() → your function, in process context"`; `observe` — `ps -eo pid,comm | grep kworker | head && ls /sys/devices/virtual/workqueue/`; `trap` — "Freeing the structure that holds a `work_struct` without `cancel_work_sync()` first is a use-after-free that KASAN will report from inside the workqueue code, pointing nowhere near your driver. Every teardown path that can race with queued work needs the sync cancel."
- **References:**
  - `https://docs.kernel.org/core-api/workqueue.html` — the definitive documentation: the concurrency-managed design, every flag, and the `WQ_MEM_RECLAIM` requirement.
  - `<Src file="kernel/workqueue.c" symbol="process_one_work" />` — where a work item is actually executed, with the concurrency-management hooks visible.
  - `<Src file="include/linux/workqueue.h" symbol="cancel_work_sync" />` — the cancellation semantics, stated in the header comments.
  - LWN, *"Concurrency-managed workqueues"* (`https://lwn.net/Articles/403891/`) — the design rationale; 2010, and the model is still what the kernel runs.

### `threaded-irqs.md` — Threaded IRQs

- **Opens with:** the idea that resolves the folder's central tension. If the problem with interrupt handlers is that they run in a context with impossible constraints, move them to a context without those constraints — a dedicated kernel thread per interrupt, scheduled like anything else, free to sleep. The cost is a wakeup and a context switch per interrupt, and for most devices that is a bargain.
- **Sections:**
  - `## `request_threaded_irq`` — two functions: a primary handler that runs in hard-IRQ context and must be trivial (usually just acknowledging the device and returning `IRQ_WAKE_THREAD`), and a thread function that does the real work. Show the shape in ` ```c ` and note that passing `NULL` for the primary handler gets a default that just wakes the thread.
  - `## `IRQF_ONESHOT`` — with a level-triggered interrupt and no primary handler, the line stays asserted until the thread runs, so the interrupt must remain masked until then. `IRQF_ONESHOT` is what arranges that, and omitting it on a level-triggered line produces an interrupt storm. State it as a rule with its reason.
  - `## What the thread may do` — everything process context allows: sleep, allocate, take mutexes, do I/O. This is the section that makes the mechanism attractive to driver authors, so give concrete examples (an I2C transaction in response to an interrupt, which is impossible in hard-IRQ context and routine in a threaded one).
  - `## Priority and latency` — the thread runs at `SCHED_FIFO` priority 50 by default (**verify at v6.18**), which places it above ordinary tasks and below higher-priority RT work. Explain the consequence: interrupt work now competes in the scheduler, which is both the benefit (it is visible, accountable, and preemptible) and the cost (its latency is a scheduling latency).
  - `## PREEMPT_RT makes it universal` — under RT, handlers are threaded by default unless marked `IRQF_NO_THREAD`, because a non-threaded handler is an unpreemptible region and therefore a latency bound. Link `../07-scheduling/preemption-models.md` and `../07-scheduling/real-time-scheduling.md`.
  - `## Seeing them` — `ps -eo pid,pri,comm | grep irq/` shows one thread per threaded interrupt, named for its IRQ, and their priorities can be tuned individually. This is genuinely useful operational knowledge for latency work.
  - `## When not to thread` — very high-rate interrupts where a wakeup per interrupt is too expensive (a fast NIC uses NAPI polling instead — forward-reference in prose to folder 13), and genuinely trivial handlers where the thread costs more than the work.
- **Anchor:** a Mermaid `sequenceDiagram` — Device, Primary handler (hard IRQ), Scheduler, IRQ thread — showing the primary handler acknowledging and returning `IRQ_WAKE_THREAD`, the thread being woken and scheduled, and the real work happening with interrupts fully enabled. Caption: "A threaded handler: two microseconds in interrupt context, and everything else in a thread the scheduler can see."
- **KernelFacts:** `structure` — `[["struct irqaction", "include/linux/interrupt.h"]]`; `path` — `"interrupt → primary handler → IRQ_WAKE_THREAD → wake_up_process(action->thread) → irq_thread() → thread_fn()"` (verify at v6.18); `observe` — `ps -eo pid,cls,rtprio,comm | grep 'irq/' | head`; `trap` — "A threaded handler on a level-triggered line without `IRQF_ONESHOT` produces an interrupt storm: the device keeps the line asserted, the primary handler keeps being re-entered, and the thread never gets to run."
- **References:**
  - `<Src file="kernel/irq/manage.c" symbol="request_threaded_irq" />` — the registration, the flag validation, and the thread creation.
  - `https://docs.kernel.org/core-api/genericirq.html`, the threaded-handler section — the contract between the primary handler and the thread.
  - LWN, *"Threaded interrupt handlers"* (`https://lwn.net/Articles/302043/`) — the original rationale from the RT tree; 2008, and the design is unchanged.
  - `https://wiki.linuxfoundation.org/realtime/documentation/technical_basics/threaded_interrupts` — why RT threads everything, and what it buys.

### `interrupt-affinity-and-balancing.md` — Interrupt Affinity **[WAH]** **[Lab host=root-required]**

- **Opens with:** the placement question. An interrupt has to be taken by *some* CPU, and which one has consequences: the handler's cache footprint, the softirq that follows, and often the task that consumes the data all live somewhere, and the closer those three are, the cheaper the whole path is. Affinity is how you control it, and the default is frequently wrong for high-rate devices.
- **Sections:**
  - `## What actually happens` **[WAH]** — reading `/proc/interrupts` on a machine with a multi-queue NIC and an NVMe drive. Show a real file. Point out that the NIC has one line per queue, each with counts concentrated on one CPU, and that this is MSI-X doing what it was designed for. Then show the legacy shared line at the bottom with counts on one CPU only, and the IPI rows. The reader should finish able to tell, from this file alone, whether a device's interrupts are spread or piled onto CPU 0.
  - `## `smp_affinity` and `smp_affinity_hint`` — the per-IRQ mask under `/proc/irq/N/`, the effective mask, and the fact that some controllers can only deliver to one CPU at a time. Show reading and writing one.
  - `## `irqbalance`` — the user-space daemon that moves interrupts around based on load and topology. Say what it does well (a general-purpose machine with mixed devices) and when to turn it off (a tuned latency-sensitive or high-throughput setup, where you have chosen placements deliberately and want them to stay).
  - `## Multi-queue devices` — one MSI-X vector per queue is the design that makes a modern NIC or NVMe drive scale: each queue's completions land on a chosen CPU, and the whole path from interrupt through softirq to the consuming task can be kept on one core. Link `../08-memory-management/numa-and-memory-policy.md` and the CS NUMA page for the memory side of the same argument.
  - `## The alignment argument` — the practical rule: interrupt, softirq, and the consuming application on the same CPU (or at least the same LLC and the same NUMA node) beats any other arrangement for throughput. State that this is why network tuning guides talk about RSS, RPS, and IRQ pinning in the same breath, and hand the network-specific detail to folder 13 in prose.
  - `## When pinning hurts` — a pinned interrupt on a CPU that also runs the application competes with it; a pinned interrupt on an isolated CPU (`nohz_full`) defeats the isolation. Give the check: measure, do not assume.
  - `<Lab host="root-required" title="Move an interrupt and watch it move" time="20 min">` — (1) identify a busy IRQ from `/proc/interrupts` (a NIC queue under `iperf3` load, or an NVMe queue under `fio`); (2) read `/proc/irq/N/smp_affinity_list`; (3) generate load and watch the per-CPU counts; (4) write a different CPU mask and watch the counts move; (5) stop `irqbalance` first, and observe that with it running your change is reverted. Show real output at each step. `:::warning` — moving an interrupt away from every CPU that can service it, or writing a mask a controller cannot honour, results in a write error or an ignored change rather than damage; but stopping `irqbalance` on a production machine changes its behaviour until it is restarted. "If it fails": some interrupts are managed by the kernel and refuse affinity changes (`-EIO` on write) — that is by design for managed multi-queue interrupts, not a bug, and the page must say so.
- **Anchor:** a real annotated `/proc/interrupts` in a ` ```text ` block, with callouts marking the multi-queue rows, the legacy shared row, and the IPI rows.
- **Second visual:** a Mermaid `flowchart LR` of the aligned path — NIC queue → MSI-X vector → CPU 3's handler → `NET_RX` softirq on CPU 3 → the application pinned to CPU 3 — beside the misaligned version with three different CPUs and arrows crossing between them.
- **KernelFacts:** `structure` — `[["struct irq_desc", "include/linux/irqdesc.h"], ["struct irq_affinity_desc", "include/linux/interrupt.h"]]` (verify); `path` — `"write /proc/irq/N/smp_affinity → irq_set_affinity() → chip->irq_set_affinity() → APIC/GIC routing updated"`; `observe` — `cat /proc/interrupts && cat /proc/irq/*/smp_affinity_list | head`; `trap` — "Interrupts spread across every CPU is not the goal. The goal is that the interrupt, the softirq it raises, and the task that consumes the data are on the same CPU — spreading them evenly is what `irqbalance` does when nothing has told it what the workload actually is."
- **References:**
  - `https://docs.kernel.org/core-api/irq/irq-affinity.html` — the `/proc/irq` interface and the exact semantics of the affinity mask and hint.
  - `man 5 proc`, the `/proc/interrupts` section — the column definitions for the [WAH] section.
  - `https://github.com/Irqbalance/irqbalance` — the daemon's own documentation, including its policy and the environment variables that ban CPUs from it.
  - Red Hat's network performance tuning guide — cite the current version; it is the clearest published statement of the interrupt/softirq/application alignment argument. Note its distribution-specific assumptions.

- [ ] **Step 1: Write `workqueues.md`** to the brief above.
- [ ] **Step 2: Build and run the workqueue lab module** in the QEMU lab, including the deliberate lifetime bug and its fix, and paste the real `dmesg` output for both.
- [ ] **Step 3: Write `threaded-irqs.md`** to the brief above, verifying the default IRQ-thread priority at v6.18 from the source rather than from secondary material.
- [ ] **Step 4: Write `interrupt-affinity-and-balancing.md`** using a real `/proc/interrupts` from a machine with a multi-queue NIC, and run the affinity lab for real — including the managed-interrupt `-EIO` case if the machine has one.
- [ ] **Step 5: Verify** `work_struct`, `process_one_work`, `cancel_work_sync`, the `WQ_*` flag list, `request_threaded_irq`, `irq_thread`, `IRQ_WAKE_THREAD`, and `irq_set_affinity` against Elixir v6.18.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/10-interrupts-time-and-deferred-work
git commit -m "docs: write workqueues, threaded IRQs, and interrupt affinity"
```

---

## Task 36: Folder 10 — timekeeping, and the tick

**Files:**
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/timekeeping-and-clocksources.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/the-tick-and-nohz.md`

**Interfaces:**
- Consumes: `10/how-an-interrupt-reaches-the-kernel` (Task 33), `09/seqlocks` (Task 29 — the read path's protocol), and `05/the-vdso` (where the same data is read from user space).
- Produces: `10/timekeeping-and-clocksources`, the declared prerequisite of `10/the-tick-and-nohz`, and the vocabulary Phase 5's tracing folder assumes when it talks about timestamps.

### `timekeeping-and-clocksources.md` — Timekeeping and Clocksources **[WAH]**

- **Opens with:** the surprisingly hard problem behind an apparently trivial question. "What time is it?" must be answered billions of times a second, must be monotonic, must survive suspend, must be adjustable by NTP without jumping, and must work across CPUs whose counters may not agree. Linux's answer is a layered one, and the layers are exactly where the confusion lives.
- **Sections:**
  - `## Two different jobs` — a *clocksource* counts (a free-running counter the kernel reads to know how much time has passed); a *clock event device* interrupts (a programmable timer that fires at a requested moment). Most confusion about kernel timekeeping comes from conflating them, so separate them in the first section and keep them separate.
  - `## Clocksources` — TSC, HPET, ACPI PM timer, and the arm64 architected timer. A table: resolution, cost to read, and the failure modes each has had. The TSC row needs the history — it was per-core, could stop in idle states, and varied with frequency — plus the `constant_tsc`/`nonstop_tsc` CPU flags that say whether this machine's TSC is trustworthy.
  - `## Selection` — the kernel rates clocksources and picks the best available; the watchdog periodically checks the chosen one against a known-good reference and demotes it if it drifts. Give the practical consequence: a `dmesg` line saying the TSC was marked unstable means every `clock_gettime` on that machine just became an order of magnitude more expensive, and this is one of the highest-value single lines in a boot log.
  - `## The read path` — the timekeeper struct, the seqlock protecting it, the cycle-to-nanosecond conversion by mult/shift, and the accumulation on each tick. Link `../09-concurrency-and-locking/seqlocks.md` for the protocol rather than re-deriving it.
  - `## What actually happens` **[WAH]** — a `clock_gettime(CLOCK_MONOTONIC)` call. If the clocksource is vDSO-capable: a seqlock read of the `vvar` page, a `rdtsc`, a multiply and shift, done — no syscall. If it is not: a real syscall into the same logic. Show the timing difference on a real machine (`clock_gettime` in a loop, with `tsc` and then forced to `hpet` via `clocksource=hpet`), and connect it back to `../05-syscalls-and-the-boundary/the-vdso.md`. The reader should finish knowing that a "slow `gettimeofday`" bug is really a clocksource bug.
  - `## The clock IDs` — a table of `CLOCK_REALTIME` (wall time, can jump, NTP-adjusted), `CLOCK_MONOTONIC` (since boot, never jumps, excludes suspend), `CLOCK_BOOTTIME` (includes suspend), `CLOCK_MONOTONIC_RAW` (no NTP adjustment), and the `_COARSE` variants (tick granularity, cheapest of all). Give the selection rule: measure intervals with `MONOTONIC`, timestamp events for humans with `REALTIME`, and use `COARSE` when millisecond resolution is enough — which for logging it usually is.
  - `## NTP, slewing, and leap seconds` — adjtimex adjusts the mult/shift rather than jumping the clock, so `CLOCK_REALTIME` moves smoothly. Leap seconds in one paragraph, including the fact that they have caused real production outages and how `CLOCK_TAI` and leap smearing respond.
  - `## arm64` — `:::note`: the architected generic timer is a standard part of the architecture with a defined frequency register, so arm64 does not have x86's clocksource-selection drama. That is a genuine simplification, not just a difference.
- **Anchor:** a Mermaid `flowchart LR` from `clock_gettime` down through the vDSO seqlock read, the clocksource read, and the mult/shift conversion, with the syscall fallback drawn as the alternative branch. Caption: "Two paths to the same nanoseconds, and the clocksource property that decides which one your machine takes."
- **KernelFacts:** `structure` — `[["struct clocksource", "include/linux/clocksource.h"], ["struct timekeeper", "include/linux/timekeeper_internal.h"]]`; `path` — `"clock_gettime() → vDSO or syscall → read_seqcount_begin() → clocksource read → mult/shift → nanoseconds"`; `observe` — `cat /sys/devices/system/clocksource/clocksource0/{available_clocksource,current_clocksource} && dmesg | grep -i clocksource`; `trap` — "`CLOCK_MONOTONIC` does not include time spent suspended. Measure an interval across a laptop lid close with it and you will get a number that is wrong by hours — `CLOCK_BOOTTIME` is the one that counts suspended time."
- **References:**
  - `https://docs.kernel.org/timers/index.html` — the timekeeping documentation index, including the clocksource and clockevent descriptions.
  - `man 2 clock_gettime` and `man 7 time` — the clock IDs and their exact semantics, which is the authority for the table.
  - `<Src file="kernel/time/timekeeping.c" symbol="ktime_get" />` — the read path with its seqlock retry loop, in the code a `clock_gettime` actually reaches.
  - John Stultz's timekeeping talks or LWN's leap-second coverage — cite one specific piece for the leap-second section and note its date.

### `the-tick-and-nohz.md` — The Tick, and Living Without It

- **Opens with:** the assumption the kernel was built on and then had to unlearn. A periodic timer interrupt at `HZ` was, for decades, how the kernel measured time, expired timers, accounted CPU usage, and decided to preempt. It is also a fixed cost per CPU per second whether or not there is anything to do, and both battery-powered devices and latency-critical workloads had good reasons to want it gone.
- **Sections:**
  - `## What the tick did` — a list, because every item had to be re-homed: update jiffies, run expired timers, account CPU time to the current task, check whether the current task's slice is up, drive RCU's quiescent-state detection, and trigger load balancing. Each of these becomes a problem when the tick stops.
  - `## `HZ`` — 100, 250, 300, 1000 as build-time options; what the choice trades (timer granularity and preemption responsiveness against overhead); and `jiffies` as the counter with its wraparound and the `time_after()` macros that handle it correctly. Note that `HZ` no longer determines scheduling granularity the way it once did.
  - `## Dynticks-idle (`CONFIG_NO_HZ_IDLE`)` — when a CPU goes idle with no timer due soon, stop the tick and let it enter a deep C-state. Explain the win (power, and on a VM, host CPU not burned by idle guests) and the mechanism (compute the next timer expiry and program a one-shot event for it).
  - `## Full dynticks (`nohz_full`)` — the ambitious version: stop the tick on a *busy* CPU with exactly one runnable task, because with one task there is nothing to preempt to and nothing to balance. State the constraints honestly — it needs at least one housekeeping CPU that keeps its tick, the accounting and RCU work must be offloaded (`rcu_nocbs`), and the residual per-CPU work must be moved away. Say plainly that this is a specialist configuration, that it requires boot parameters and IRQ affinity work, and that measuring is mandatory because a half-configured `nohz_full` is slower than none.
  - `## Where the tick's work went` — a table mapping each item from the first section to its new home: timers to the one-shot clock event, accounting to context-switch-time and entry/exit accounting (`CONFIG_VIRT_CPU_ACCOUNTING_GEN`), RCU quiescent states to entry/exit hooks and offloaded callbacks, and load balancing to the housekeeping CPU. This table is the page's payoff.
  - `## CPU isolation, as a package` — `isolcpus`, `nohz_full`, `rcu_nocbs`, IRQ affinity moved off the isolated CPUs, and pinning the workload onto them. Say that these are one configuration and not four, because doing three of the four gives most of the cost and little of the benefit. Link `../07-scheduling/smp-load-balancing.md` and `./interrupt-affinity-and-balancing.md`.
  - `## Verifying it` — how to check the tick actually stopped: `/proc/interrupts`' local-timer row per CPU under load, and the tracepoints if `CONFIG_NO_HZ_FULL` is enabled. Give the number to look at rather than a claim to trust.
- **Anchor:** a WaveDrom `signal` diagram of local-timer interrupts on two CPUs over the same interval — a housekeeping CPU ticking steadily, and a `nohz_full` CPU with a single busy task showing almost none. Caption: "The same second on two CPUs: a thousand timer interrupts on one, and a handful on the other."
- **KernelFacts:** `structure` — `[["struct tick_sched", "kernel/time/tick-sched.h"], ["struct clock_event_device", "include/linux/clockchips.h"]]` (verify the header path); `path` — `"idle or single task → tick_nohz_idle_enter() / tick_nohz_full_update_tick() → next expiry computed → one-shot clock event programmed"` (verify at v6.18); `observe` — `grep -E 'LOC|Local timer' /proc/interrupts && cat /proc/cmdline`; `trap` — "`nohz_full` on its own usually makes things worse. Without `rcu_nocbs`, isolated IRQ affinity, and a pinned single-task workload, the tick does not actually stop and you have paid the accounting overhead for nothing — check the local-timer count per CPU rather than assuming."
- **References:**
  - `https://docs.kernel.org/timers/no_hz.html` — the definitive in-tree document, including the complete list of what full dynticks requires; **the authority for this page's constraint list**.
  - `https://docs.kernel.org/admin-guide/kernel-parameters.html` — the exact syntax and interaction of `isolcpus`, `nohz_full`, and `rcu_nocbs`.
  - `<Src file="kernel/time/tick-sched.c" symbol="tick_nohz_idle_enter" />` — where the tick is actually stopped and the next event computed.
  - LWN's `nohz_full` coverage — cite one specific article and note its date; the feature's usability has improved substantially over time and old accounts overstate the difficulty.

- [ ] **Step 1: Write `timekeeping-and-clocksources.md`** to the brief above.
- [ ] **Step 2: Measure the clocksource difference for real** — a `clock_gettime` loop with the default clocksource, then with `clocksource=hpet` (or by writing to `current_clocksource` where permitted) — and paste both timings with the machine described. `:::warning` that changing the clocksource at runtime affects the whole system's timekeeping cost until changed back.
- [ ] **Step 3: Write `the-tick-and-nohz.md`** to the brief above, taking the full-dynticks requirement list verbatim from `Documentation/timers/no_hz.rst` at v6.18.
- [ ] **Step 4: Verify** `clocksource`, `timekeeper`, `ktime_get`, `tick_sched`, `clock_event_device`, `tick_nohz_idle_enter`, and the `CONFIG_NO_HZ_*` symbol names against Elixir v6.18.
- [ ] **Step 5: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/10-interrupts-time-and-deferred-work
git commit -m "docs: write timekeeping, clocksources, and the dynamic tick"
```

---

## Task 37: Folder 10 — timers, and delays

**Files:**
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/timers-and-hrtimers.md`
- Modify: `docs/linux/10-interrupts-time-and-deferred-work/delays-and-sleeps.md`

**Interfaces:**
- Consumes: `10/the-tick-and-nohz` (Task 36).
- Produces: the folder's completion and, with it, the end of Phase 2's page writing. Phase 4's driver folder will link to both pages constantly.

### `timers-and-hrtimers.md` — Timers and High-Resolution Timers

- **Opens with:** the two-answers observation. The kernel has two entirely separate timer subsystems because it has two entirely different requirements: "do this in about a second, and I do not care about ten milliseconds either way" is an enormously cheaper problem than "do this in exactly 250 microseconds", and building one mechanism for both would make the common case pay for the rare one.
- **Sections:**
  - `## `timer_list`: the timer wheel` — buckets by expiry distance, with coarser granularity the further out the expiry is. The key property: adding and removing a timer is O(1) with no sorting, which matters enormously because the overwhelming majority of kernel timers are **cancelled before they fire** (every network retransmission timeout, every I/O timeout). Say this explicitly — the wheel is optimised for cancellation, not expiry, and once that is understood the design is obvious.
  - `## The imprecision is deliberate` — a timer set for one second may fire meaningfully late, and that is the contract. `round_jiffies` even encourages *deliberate* rounding so that timers across the system coalesce and let the CPU stay idle longer. Power efficiency is a feature of the imprecision.
  - `## The API` — `timer_setup`, `mod_timer`, `del_timer_sync` (**verify the v6.18 name — the timer API was renamed towards `timer_delete_sync`**), and the same lifetime hazard as workqueues: deleting the structure while the timer is armed. State the rule identically to the workqueue page so the two reinforce each other.
  - `## `hrtimer`: real deadlines` — a red-black tree ordered by absolute expiry time, backed by a programmable clock event device, with nanosecond resolution and a real guarantee about not firing early. Explain why the data structure differs: an hrtimer's expiry is *precise*, so it must be sorted, and the tree costs O(log n) insertions in exchange.
  - `## Which one to use` — a decision table: timeouts that will usually be cancelled → `timer_list`; a deadline that must be met → `hrtimer`; periodic work that may sleep → a delayed workqueue. Give the rough resolution threshold (roughly a jiffy) and note that `usleep_range` is built on hrtimers, which is why it is more precise than `msleep`.
  - `## Timer slack` — per-task slack (`PR_SET_TIMERSLACK`) that lets the kernel batch a task's timer expiries, and why a power-conscious system sets it generously for background processes.
  - `## Where timers run` — softirq context for both wheels (`TIMER_SOFTIRQ` and `HRTIMER_SOFTIRQ`), or hard-IRQ context for hrtimers marked `HRTIMER_MODE_..._HARD`. So a timer callback may not sleep, which is the same rule as the rest of the folder and worth restating in the context of code that looks like ordinary function calls.
  - `## Per-CPU, and migration` — timers are per-CPU and are migrated when a CPU goes offline; an hrtimer set on one CPU normally fires on it. Brief, but it explains an entire class of "why did my timer fire on a different core" question.
- **Anchor:** a Mermaid `flowchart LR` contrasting the two structures — the wheel's buckets with a coarse far bucket, and the hrtimer red-black tree with the leftmost node feeding the programmed clock event. Caption: "Two timer subsystems, two data structures: one optimised for cheap cancellation, one for precise expiry."
- **KernelFacts:** `structure` — `[["struct timer_list", "include/linux/timer.h"], ["struct hrtimer", "include/linux/hrtimer.h"]]`; `path` — `"mod_timer() → wheel bucket → TIMER_SOFTIRQ → callback; hrtimer_start() → rbtree → clock event programmed → HRTIMER_SOFTIRQ or hard IRQ → callback"`; `observe` — `cat /proc/timer_list | head -40` (requires `CONFIG_TIMER_STATS`-era support; verify what exists at v6.18); `trap` — "The timer wheel is optimised for timers that never fire. Most kernel timers are timeouts that get cancelled, which is why adding and removing one is O(1) and why the expiry granularity is deliberately loose."
- **References:**
  - `https://docs.kernel.org/timers/timers-howto.html` — the in-tree guidance on which timer or delay to use; **the authority for this page's decision table and the next page's**.
  - `https://docs.kernel.org/timers/hrtimers.html` — the design rationale for the separate high-resolution subsystem.
  - `<Src file="kernel/time/timer.c" symbol="mod_timer" />` — the wheel insertion, where the bucket-granularity scheme is visible.
  - LWN, *"The return of the timer wheel"*-type coverage of the 2016 rewrite — cite the specific article; it explains why the current wheel looks different from the one in older books.

### `delays-and-sleeps.md` — Delays and Sleeps: What They Really Do **[WAH]** **[Misc]**

- **Opens with:** the honest summary that gives the page its title — none of these functions sleeps for exactly the time you asked. Some burn the CPU for at least that long, some sleep for at least that long and often considerably more, and knowing which is which, and by how much, is the difference between a driver that works and a driver that works on the developer's machine.
- **Sections:**
  - `## Two families` — busy-wait delays (`ndelay`, `udelay`, `mdelay`) that spin, and sleeping delays (`usleep_range`, `msleep`, `schedule_timeout`) that yield the CPU. The choice is forced by context first: in atomic context you can only busy-wait.
  - `## `udelay` and the loop calibration` — it spins using a calibrated loop or the TSC, it holds the CPU for the whole duration, and `mdelay` is `udelay` in a loop and is almost always a mistake in modern code — a millisecond of busy-waiting is an eternity. State the rule: busy-wait only in atomic context, only for short waits (roughly under ten microseconds), and only when the hardware genuinely requires it.
  - `## `usleep_range`, and why it takes a range` — it takes a minimum and a maximum precisely so the kernel can coalesce it with other timers and avoid programming a dedicated wakeup. Passing an identical min and max defeats the entire mechanism, and the kernel's own documentation says so. This is the single most useful correction on the page.
  - `## `msleep`, and its actual granularity` — built on jiffies, so it rounds up to the tick and can overshoot substantially, especially at `HZ=100`. Note that `msleep(1)` can sleep for far longer than a millisecond and that this surprises people writing polling loops.
  - `## `schedule_timeout`` — the primitive underneath, requiring the task state to be set first, and the standard pattern for "wait for this condition or this long" via `wait_event_timeout`. Show it in ` ```c `, because the state-setting requirement is easy to get wrong.
  - `## What actually happens` **[WAH]** — measure it. A small module (or a user-space equivalent with `nanosleep`) that requests 1 ms a thousand times and records the actual elapsed time; show the distribution for `msleep(1)` versus `usleep_range(1000, 2000)`. The reader sees real overshoot numbers rather than a claim. State the machine and the `HZ` and preemption configuration, because the numbers depend on both.
  - `## The selection table` — the page's anchor, and it should mirror the kernel's own `timers-howto` guidance: the wait duration, the context, and the function to call, with the reason. Ranges roughly: under ~10 µs atomic → `ndelay`/`udelay`; 10 µs–20 ms sleepable → `usleep_range`; over ~20 ms → `msleep`; waiting for an event with a deadline → `wait_event_timeout`.
  - `## Polling hardware, done properly` — `readx_poll_timeout` and friends (verify the v6.18 names) as the idiom that replaces a hand-rolled loop with a sleep in it, and why a driver should use it: consistent timeout handling, and the sleep-versus-spin choice made once.
  - `## Misconceptions` **[Misc]** — (1) "`msleep(1)` sleeps for one millisecond" — it sleeps for at least one and often several; (2) "`udelay` is more accurate so use it for short waits" — it is accurate and it burns a CPU, which is only acceptable in atomic context; (3) "a range in `usleep_range` means the kernel is being vague" — the range is what lets it coalesce your wakeup with someone else's, and a zero-width range costs power for no benefit.
- **Anchor:** the selection table above.
- **Second visual:** a WaveDrom `signal` diagram showing a requested 1 ms wait against the actual elapsed time for `udelay` (exact, CPU burned), `usleep_range` (close, CPU yielded), and `msleep` (overshooting to the next tick).
- **KernelFacts:** `structure` — `[["struct hrtimer_sleeper", "include/linux/hrtimer.h"]]`; `path` — `"usleep_range() → hrtimer with a slack range → schedule() → wakeup within [min, max]"` (verify the v6.18 implementation — `usleep_range_state` is the current core); `observe` — `grep -E 'CONFIG_HZ=' /boot/config-$(uname -r)` and the measured distribution from the [WAH] experiment; `trap` — "`usleep_range(1000, 1000)` is not more precise than `usleep_range(1000, 2000)` — it just forbids the kernel from coalescing your wakeup with any other, which costs power and buys nothing the hardware could use."
- **References:**
  - `https://docs.kernel.org/timers/timers-howto.html` — the kernel's own decision guidance; the selection table on this page must agree with it exactly.
  - `<Src file="kernel/time/timer.c" symbol="msleep" />` — the jiffy rounding, in three lines, which settles the granularity argument.
  - `<Src file="include/linux/iopoll.h" symbol="readx_poll_timeout" />` — the polling idiom; verify the exact macro names at v6.18.
  - `man 2 nanosleep` — the user-space counterpart, for the measurement experiment and for readers who assume the two behave alike.

- [ ] **Step 1: Write `timers-and-hrtimers.md`** to the brief above, checking the current timer-deletion API name at v6.18 rather than using `del_timer_sync` from memory.
- [ ] **Step 2: Run the delay measurement** — the simplest honest version is a user-space `nanosleep`/`clock_nanosleep` loop plus, if the lab is available, a kernel module doing the same with `msleep` and `usleep_range`. Record the distributions and the machine's `HZ` and preemption model.
- [ ] **Step 3: Write `delays-and-sleeps.md`** from the measured data, with the selection table taken from `Documentation/timers/timers-howto.rst`.
- [ ] **Step 4: Verify** `timer_list`, the delete API name, `hrtimer`, `hrtimer_sleeper`, `usleep_range`, `msleep`, `schedule_timeout`, and the `iopoll.h` macro names against Elixir v6.18.
- [ ] **Step 5: Folder-10 completeness check** — twelve pages written, and the arm64 `:::note` present on `how-an-interrupt-reaches-the-kernel` and `timekeeping-and-clocksources` as the spec requires for this folder's topics.
- [ ] **Step 6: Check, build, commit**

```bash
npm run check:linux && npm run build
git add docs/linux/10-interrupts-time-and-deferred-work
git commit -m "docs: write kernel timers, hrtimers, and delays"
```

---
## Task 38: Figures and `SOURCES.md` rows for the phase

**Files:**
- Modify: `static/img/linux/SOURCES.md`
- Create: `static/img/linux/memory-management/<figure>.png|svg` (see below)
- Create: `static/img/linux/interrupts-time-and-deferred-work/<figure>.png|svg` (see below)
- Modify: the two or three pages that reference them

**Interfaces:**
- Consumes: the written pages from Tasks 5–37.
- Produces: the phase's figure set and its provenance rows. **Batched deliberately** — the spec puts the figure pass at the end of a phase so the `SOURCES.md` rows and the downloads happen once rather than page by page.

**The default for this phase is Mermaid and WaveDrom.** Folders 05–10 are structural material — code paths, state machines, bit fields, timelines — and the spec's visual vocabulary says a drawn schematic is the *right* tool for those, not a fallback. Do not go looking for figures to satisfy a quota. Two figures are worth having, and if either cannot be sourced cleanly, the correct outcome is the Mermaid diagram alone.

- [ ] **Step 1: Confirm the directory convention**

Figures live at `static/img/linux/<folder-slug-without-numeric-prefix>/<name>.<ext>` and are referenced as `/img/linux/...` with **no** `/knowledge-base` prefix. Confirm against the two existing directories (`overview/`, `kernel-architecture-and-idioms/`) before creating new ones.

- [ ] **Step 2: Fetch the x86-64 paging figure**

For `08/page-tables-and-the-walk.md`, beside its WaveDrom PTE strip and its Mermaid walk diagram:

```bash
mkdir -p static/img/linux/memory-management
curl -sSL -o static/img/linux/memory-management/x86-64-paging.png \
  https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/X86_Paging_64bit.svg/1200px-X86_Paging_64bit.svg.png
```

Verify it is a real image and not an error page:

```bash
file static/img/linux/memory-management/x86-64-paging.png
ls -l static/img/linux/memory-management/x86-64-paging.png
```

Expected: a PNG of a few hundred kilobytes at most. **If the URL 404s or the rendering is illegible, open the Wikimedia Commons page for the "X86 Paging 64bit" file, pick the rendering that is actually there, and record the URL you actually used.** Never guess a URL into `SOURCES.md`. If no usable rendering exists, skip this figure — the page's own WaveDrom strip and Mermaid walk already satisfy the visual-anchor requirement, and a bad figure is worse than none.

- [ ] **Step 3: Decide on the interrupt-routing figure**

For `10/how-an-interrupt-reaches-the-kernel.md`, a figure showing local APIC / I/O APIC topology would pair well with the page's Mermaid sequence diagram. Look for one on Wikimedia Commons or in Intel's own published documentation. **Apply the same rule**: if nothing clean and legible exists, ship the Mermaid diagram alone and record nothing. Do not substitute a low-quality blog diagram merely to have an image on the page.

- [ ] **Step 4: Consider the two GIF candidates, and probably decline them**

The spec permits committed GIFs where motion is the mechanism, and names buddy split/coalesce and TLB fill/shootdown — both in this phase. Look for a clean one under 2 MB. Both are also served well by a static two-panel diagram, so treat the GIF as a nice-to-have: if a suitable one is not found in a few minutes, move on and note here that it was considered and declined. Record the decision in the commit message so it is not re-litigated in a later phase.

- [ ] **Step 5: Add the `SOURCES.md` rows**

Append to the existing table in `static/img/linux/SOURCES.md`, matching its columns exactly (`file`, `source_url`, `publisher`, `retrieved`, `notes`). One row per file added, with `retrieved` as the actual date. Notes must say whether the file is a crop, a PNG rendering of an SVG, or a frame extracted from an animation — someone re-sourcing it later depends on that.

- [ ] **Step 6: Place the figures on their pages**

Each with a full `<Figure>` call: `src`, a descriptive `alt`, a `caption` that says what it shows, and `source`/`href` naming the publisher. Example shape (adjust to what was actually fetched):

```mdx
<Figure src="/img/linux/memory-management/x86-64-paging.png"
        alt="Four levels of x86-64 page tables translating a 48-bit virtual address, with the nine-bit index feeding each level"
        caption="The four-level walk this page works through with real numbers, drawn as the hardware sees it."
        source="Wikimedia Commons"
        href="https://commons.wikimedia.org/wiki/File:X86_Paging_64bit.svg" />
```

- [ ] **Step 7: Check the size budget**

Run: `du -sh static/img/linux && du -sh static/img/linux/*`
Expected: the whole `static/img/linux/` tree still well under a megabyte or two. If a single file is over ~500 KB, downscale it to ≤ 1400 px wide and note the modification in its `SOURCES.md` row.

- [ ] **Step 8: Verify every figure renders and every row has a file**

```bash
npm run build
rtk run "grep -o '/img/linux/[^\"]*' -r docs/linux | sort -u"
```

Cross-check that list against `static/img/linux/SOURCES.md` and against `ls -R static/img/linux`: **no orphans in either direction** — every referenced path exists, every file has a row, and every row has a file.

- [ ] **Step 9: Commit**

```bash
git add static/img/linux docs/linux
git commit -m "docs: add phase 2 figures and SOURCES rows"
```

---

## Task 39: Extend the glossary

**Files:**
- Modify: `docs/linux/00-overview/glossary.md`

**Interfaces:**
- Consumes: all 76 pages written in Tasks 5–37. This is an aggregation task and cannot start before they are done.
- Produces: the glossary at roughly 110–125 entries, up from the ~50 Phase 1b left. Phase 3 appends to it in the same format.

The format was fixed in Phase 1b and does not change: an alphabetised list, each entry a bolded term, an em dash, one or two sentences, and a link to the page that **owns** the term. Do not introduce headings per letter; the page is searched, not browsed.

- [ ] **Step 1: Read the existing page first** and match its voice and entry length exactly. An entry that is three sentences long next to fifty that are one is a review finding.
- [ ] **Step 2: Extract the real term list from the pages**, not from this plan. The terms below are a starting point; the written pages are the authority, and a term whose owning page does not define it properly does not get an entry.

Expected additions, grouped by owning folder:

- **From 05:** system call (already present from 00 — check and extend rather than duplicate), `SYSCALL`, `MSR_LSTAR`, `pt_regs`, syscall table, `SYSCALL_DEFINEn`, negative errno, `EFAULT`, exception table, SMAP, SMEP, vDSO, `vvar`, `ERESTARTSYS`, compat syscall, seccomp user notification.
- **From 06:** `task_struct`, `current`, thread group, `tgid`, `clone` flags, copy-on-write, `binfmt`, `PT_INTERP`, VMA (defer the full definition to 08 and cross-reference), `struct cred`, saved set-user-ID, wait queue, `TASK_INTERRUPTIBLE`, `TASK_UNINTERRUPTIBLE`, D state, zombie, reparenting, subreaper, pending signal, `sigreturn`, real-time signal, `SCM_RIGHTS`, `seq_file`.
- **From 07:** runqueue, scheduling class, `pick_next_task`, vruntime, CFS, EEVDF, lag, eligibility, request size/slice, nice weight, autogroup, preemption model, `need_resched`, `preempt_count`, context switch, scheduling domain, wake affinity, `SCHED_FIFO`, `SCHED_DEADLINE`, CBS, RT throttling, `cpu.weight`, `cpu.max`, throttling, PSI.
- **From 08:** canonical address, direct map, KASLR, page table level, PTE, TLB reach, TLB shootdown, PCID, `mm_struct`, VMA, maple tree, `mmap_lock`, page fault (minor/major), demand paging, zero page, overcommit, zone, buddy allocator, GFP flags, watermark, compaction, slab, SLUB, size class, `vmalloc`, folio, compound page, page cache, `address_space`, readahead, dirty page, writeback, `fsync`, LRU, MGLRU, kswapd, direct reclaim, shrinker, refault, swap entry, swappiness, zswap, zram, OOM score, huge page, THP, hugetlbfs, NUMA node, first touch, mempolicy, RSS, PSS, USS, `MemAvailable`.
- **From 09:** memory ordering, `READ_ONCE`, barrier, acquire/release, `atomic_t`, `refcount_t`, spinlock, queued spinlock, `irqsave`, `raw_spinlock_t`, mutex, optimistic spinning, `rw_semaphore`, seqlock, sequence counter, RCU, grace period, quiescent state, `rcu_dereference`, SRCU, per-CPU data, `local_lock`, `kfifo`, lockdep, lock class, KCSAN.
- **From 10:** IRQ number versus vector, `irq_desc`, `irq_chip`, irq domain, MSI-X (cross-reference the CS page), hard IRQ context, softirq, `ksoftirqd`, tasklet, workqueue, work item, threaded IRQ, `IRQF_ONESHOT`, IRQ affinity, clocksource, clock event device, TSC, `jiffies`, `HZ`, tick, dynticks, `nohz_full`, timer wheel, hrtimer, timer slack.

- [ ] **Step 3: Enforce the one-owner rule.** Every entry links to exactly one page, and that page must genuinely introduce the term. Where two pages touch a term, the owner is where it is defined. Where a term is owned by a `computer-science/` page (MESI, memory consistency, PCIe, interrupt controller hardware), link *there* — the section's policy is that hardware and theory are owned outside `docs/linux/`.
- [ ] **Step 4: Update the opening paragraph** to say the glossary now covers folders 00–10 and still grows.
- [ ] **Step 5: Verify every link resolves**

Run: `npm run build`
Expected: green. `onBrokenLinks: "throw"` catches any entry pointing at a page that does not exist — which is the only automated check this page gets, so a green build here matters.

- [ ] **Step 6: Commit**

```bash
git add docs/linux/00-overview/glossary.md
git commit -m "docs: extend the glossary for folders 05-10"
```

---

## Task 40: Extend the misconceptions index and the roadmap

**Files:**
- Modify: `docs/linux/00-overview/misconceptions-index.md`
- Modify: `docs/linux/00-overview/roadmap.md`
- Modify: `docs/linux/00-overview/what-this-section-covers.md`

**Interfaces:**
- Consumes: every `## Misconceptions` section written in Tasks 5–37.
- Produces: the three overview pages brought back into agreement with the section's actual contents. **This is a mirroring task, not an authoring one** — if a page and the index disagree, the page wins and the index is corrected.

- [ ] **Step 1: Collect the entries mechanically**

Run: `rtk run "grep -rn -A 8 '^## Misconceptions' docs/linux/"`
Work from that output, not from memory or from this plan's `[Misc]` markers. The plan marks roughly twenty-two pages in folders 05–10; the grep is the authority on what was actually written.

- [ ] **Step 2: Append to the index in its existing format** — grouped by folder, `##` per folder, each entry the belief stated in bold as someone would actually say it, then the correction in two or three sentences, then a link to the owning page. Blunt, per the spec: this page's value is its directness.

The high-value entries this phase contributes, as a completeness check against the grep:

- "A syscall is a function call into the kernel." / "The kernel runs in a separate process."
- "`errno` comes from the kernel." / "Syscalls return -1."
- "`strace` showing nothing means nothing happened." (the vDSO)
- "`fork()` is a syscall." / "`open()` is what `strace` will show."
- "Threads are lighter than processes on Linux."
- "`fork()` is free because of copy-on-write."
- "`exec` starts your program." (it starts the dynamic linker)
- "`TASK_RUNNING` means running." / "A `D`-state process is hung." / "Load average is CPU usage."
- "You can `kill -9` a zombie." / "Zombies leak memory."
- "A signal interrupts the process immediately." / "Signals queue."
- "`/proc` files are empty because they are zero bytes." / "Reading `/proc` is free."
- "nice 19 means it only runs when idle." / "A lower nice number is lower priority."
- "Context switches are expensive because saving registers is slow." / "A thread switch is free."
- "A 0.5 CPU limit makes the app run at half speed." / "More threads help under a quota."
- "malloc allocates memory." / "If malloc succeeded, the memory is mine."
- "A page fault is an error."
- "`write()` returning means the data is written." / "`close` flushes." / "`fsync` on the file is enough for a new file."
- "Free memory is the number that matters." / "Summing RSS gives total usage." / "A container at its memory limit is about to be killed."
- "Swap is used only when RAM is full." / "`swappiness=0` disables swap." / "Swap makes things slow."
- "THP should always be disabled." / "Huge pages help by shortening the walk."
- "The OOM killer kills the process that caused the problem."
- "Spinlocks waste CPU so mutexes are better." / "A mutex is the slow option."
- "It is atomic, so it is safe." (atomicity is not ordering)
- "`kfifo` is lockless."
- "Softirqs are threads." / "High `si` means a kernel problem."
- "`msleep(1)` sleeps for one millisecond." / "A range in `usleep_range` means the kernel is being vague."
- "Spreading interrupts across all CPUs is the goal."

- [ ] **Step 3: Verify the mirroring is complete in both directions** — every `## Misconceptions` entry found in Step 1 appears in the index, and nothing appears in the index that is not on a page. Count both and state the counts in the commit message.
- [ ] **Step 4: Extend `roadmap.md`'s learning paths.** Keep `<LearningPath>` exactly as it is used today; only the step lists change. With folders 05–10 written:
  - **"I just want to understand my machine"** — extend with `06/proc-as-the-process-interface`, `08/what-free-and-rss-really-say`, and `07/priorities-nice-and-weights`.
  - **"I want to read kernel source"** — extend with `05/the-entry-path`, `06/task-struct-the-anatomy-of-a-task`, `08/mm-struct-and-vmas`, `09/why-kernel-concurrency-is-different`.
  - **"My server is slow"** — this spec path can now open properly: `07/diagnosing-scheduling-latency` → `08/what-free-and-rss-really-say` → `08/reclaim-lru-and-kswapd` → `10/interrupt-affinity-and-balancing` → `07/cgroup-cpu-control`. Close it with an unlinked sentence saying that I/O and network diagnosis land with folders 12 and 13, and the tooling with folder 17.
  - **New: "I want to understand memory"** — `08/the-virtual-address-space` → `08/page-tables-and-the-walk` → `08/mm-struct-and-vmas` → `08/the-page-fault-handler` → `08/demand-paging-and-cow` → `08/the-page-allocator` → `08/the-page-cache` → `08/reclaim-lru-and-kswapd` → `08/what-free-and-rss-really-say`.
  - **New: "I want to write correct concurrent kernel code"** — `09/why-kernel-concurrency-is-different` → `09/memory-ordering-and-barriers` → `09/atomics-and-refcounts` → `09/spinlocks` → `09/mutexes-and-semaphores` → `09/rcu-the-idea` → `09/rcu-in-practice` → `09/choosing-a-lock` → `09/finding-locking-bugs`.
  - Update the closing `## Where the rest is` paragraph: folders 11–19 remain specified and unscaffolded.
- [ ] **Step 5: Update the folder-ladder table** in `what-this-section-covers.md` so folders 05–10 are marked written rather than specified. One table, six rows; do not rewrite the page.
- [ ] **Step 6: Build and commit**

```bash
npm run build
git add docs/linux/00-overview
git commit -m "docs: extend the misconceptions index and roadmap for folders 05-10"
```

---

## Task 41: Phase review, `CLAUDE.md`, and the written gate

**Files:**
- Modify: `CLAUDE.md`
- Modify: any page the review pass finds wanting

**Interfaces:**
- Consumes: everything.
- Produces: a phase that is actually finished, and repository documentation that matches the repository.

- [ ] **Step 1: Run the written gate**

Run: `npm run check:linux -- --written`
Expected: `check-linux-docs: OK — 123 written page(s), 0 stub(s)`. Any remaining stub is a page this plan missed; write it before continuing rather than adjusting the gate.

- [ ] **Step 2: Run the full gate set**

```bash
npm run build
npm run typecheck
npm run test:graph
npm run test:kernel-source
rtk run 'npm run lint'
```

Expected: all green. Fix anything that is not before proceeding — this is the phase's definition of done, and a failing gate here is not a documentation issue to defer.

- [ ] **Step 3: Review pass against the spec's per-phase checklist**

Walk all 82 pages (76 Linux + 6 CS) and confirm each item. Record findings in a scratch list, fix them, then re-run Step 2.

- Every topic page has a visual anchor, and its caption says *what it shows*.
- Every topic page has `## References` with 2–6 annotated entries, no bare URLs, and any source significantly older than v6.18 says so in its annotation.
- Every topic page ends with `<KernelFacts>` whose `trap` row is a real trap, not a restatement of the page.
- **Every symbol, path, struct field, config option, and sysctl named on a page has been checked against Elixir v6.18.** This is the largest single risk in the phase — several subsystems were renamed recently — so treat it as a per-page audit rather than a spot check.
- Every arch-specific claim names its architecture, and the four required arm64 `:::note` contrasts are present: syscall entry (folder 05), page-table format (folder 08), **memory ordering — the load-bearing one** (folder 09), and interrupt controllers (folder 10).
- Every `## Misconceptions` entry is mirrored in `misconceptions-index.md` (Task 40).
- `## What actually happens` appears only on the pages this plan marks **[WAH]**.
- Every `<Lab>` has a host badge, shows **real** expected output, and closes with an "if it fails" line. Every lab carrying a `:::danger` has a host badge other than `any-linux`.
- The three context7 verifications required by the spec were done and are dated in the pages' references: EEVDF (07), folios and MGLRU (08), RCU API and `refcount_t` guidance (09).
- **No page links into folders 11–19.** Run `rtk run "grep -rn '\\.\\./1[1-9]-' docs/linux"` and expect no output.
- `static/img/linux/SOURCES.md` has one row per file and no orphans in either direction.
- The no-duplication contract holds: no `docs/linux/` page re-teaches hardware or OS theory that a `computer-science/` page owns. Spot-check the six pairs most at risk — `08/tlb-and-address-space-switching` against the TLB backfill, `09/memory-ordering-and-barriers` against the ordering backfill, `09/per-cpu-data` and `09/rwlocks-and-rwsems` against MESI, `08/numa-and-memory-policy` against the NUMA backfill, and `10/how-an-interrupt-reaches-the-kernel` against the interrupt-controller backfill.

- [ ] **Step 4: Check the graph is meaningful, not just valid**

The build already proves every `prerequisites` id resolves and that there are no cycles. Additionally, walk the two new learning paths from Task 40 and confirm that every prerequisite of every page on a path appears **earlier in that path**. A path that requires a reader to jump forward is an editorial bug the build cannot catch.

- [ ] **Step 5: Verify the section in a production build**

```bash
npm run build && npm run serve
```

Open the section and check by eye: the six new folders appear in the sidebar in position order with their descriptions on the generated index pages; a `<PrereqBlock>` on a folder-08 page shows Before/Next/Related chips that lead somewhere real; the WaveDrom strips (PTE bits, GFP flags, `clone` flags) render; the WaveDrom `signal` timelines (RCU grace period, cgroup throttling, seqlock retry) render; a `<Lab>` shows its host badge; and the roadmap's new paths click through. Serve, not dev.

- [ ] **Step 6: Update `CLAUDE.md`**

Two surgical edits in the "Linux & Kernel Internals section" block. `CLAUDE.md` is dense on purpose — this is an update, not a rewrite.

1. **Phase status.** The block currently says Phase 1b wrote folders 00–04 (47 pages) plus three CS backfill pages, and that folders 05–19 exist only in the spec. Replace with: Phase 1a delivered the infrastructure and scaffold; Phase 1b wrote folders 00–04 and CS backfill 1/2/17; **Phase 2 wrote folders 05–10 (76 pages) and CS backfill 3/4/6/7/8/10 (memory ordering, hardware atomics, the TLB, cache coherence, NUMA, interrupt controllers), bringing the section to 123 written pages**; folders 11–19 remain scaffolded in the design spec only, not on disk, so no page may link into them. Keep `npm run check:linux -- --written` named as the gate, now covering folders 00–10.
2. **The manifest note.** Confirm the existing sentence about `tools/linux-docs-manifest.json` being the single source of truth still reads correctly now that it carries eleven folders and nine external pages; adjust the counts if the current text states any.

Leave the component list, cast policy, and figure policy alone — none of them changed in this phase.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md docs/linux docs/computer-science
git commit -m "docs: update CLAUDE.md for phase 2 completion"
```

- [ ] **Step 8: Final verification**

```bash
npm run check:linux -- --written && npm run build && rtk run 'npm run lint'
git status
```

Expected: all green, working tree clean. Report the page count written, the gates run, the three context7 checks and their dates, and everything the review pass found and fixed.

---

## Self-review notes

**Spec coverage.** The spec's "Phase 2 ordering" list has six items, and every one has a task:

| Spec item | Tasks |
|---|---|
| 1. Scaffold folders 05–10 and their `_category_.json` files; green build | Task 1 |
| 2. CS backfill 3, 4, 6, 7, 8, 10 plus backlinks; backfill 3 and 7 gate folder 09 | Tasks 2–4, with Task 27 explicitly gated on Task 2 |
| 3. Folders in order 05 → 06 → 07 → 08 → 09 → 10 | Tasks 5–8 (05), 9–13 (06), 14–18 (07), 19–26 (08), 27–32 (09), 33–37 (10) |
| 4. Within 08: page tables and VMAs before the fault handler; within 09: ordering first, RCU idea before RCU practice | Tasks 19–20 precede 21; Task 27 precedes 28–32; Task 30 writes the two RCU pages in order and says so |
| 5. context7 verification for EEVDF (07) and folios/MGLRU (08) | Task 15 step 2, Task 23 step 1, Task 24 step 2 — plus the spec's folder-09 row (RCU API, `refcount_t`) in Tasks 28 and 30 |
| 6. Figures and labs pass, then the review checklist | Task 38 (figures), labs written into their own tasks and run before their pages, Task 41 (review) |

The phase's page counts match the spec's table: 76 Linux pages (10 + 12 + 11 + 18 + 13 + 12) and 6 CS backfill pages, 82 total.

**Deliberate deviations, stated rather than hidden:**

- **Labs are run before their pages are written**, and every task that carries a `<Lab>` says so as an explicit step. The spec asks for expected output; this plan requires it to be *measured* rather than predicted. Where a measurement is impractical (a `D`-state process, for instance) the plan says to describe an observed case rather than manufacture one.
- **The figure pass is deliberately small.** The spec's figure guidance is strongest for folders with canonical published diagrams (04's Graphviz map, 12's storage stack); folders 05–10 are dominated by code paths, state machines, and bit fields, which the visual vocabulary assigns to Mermaid and WaveDrom. Task 38 makes "no figure" an acceptable, recorded outcome rather than a gap.
- **No casts are recorded**, consistent with Phase 1b and with the user's standing policy. The section's cast library is a single Phase 5 recording session; terminal material here ships as annotated ` ```text ` blocks, which the spec requires alongside every cast anyway.
- **Two learning paths are added beyond the spec's six** ("I want to understand memory", "I want to write correct concurrent kernel code"), because folders 08 and 09 are large enough to deserve their own routes and because the spec's remaining unopened paths ("I want to write a driver", "I want to work on containers", "I want to send a patch") still cross into unwritten folders.

**Known risks, stated rather than hidden:**

- **Symbol drift is the largest risk in this phase.** Several subsystems this plan names were renamed or restructured recently: `__do_softirq` → `handle_softirqs`, `load_balance` → `sched_balance_rq`, `del_timer_sync` → the `timer_delete_sync` family, the allocator's `_noprof` suffixes, VMA code moving from `mm/mmap.c` to `mm/vma.c`, the VMA rbtree becoming a maple tree, and the slab headers consolidating. **Every symbol in this plan is a starting point, not a verified fact.** The global constraint at the top and a per-task verification step both say so, and Task 41 makes it a per-page audit rather than a spot check.
- **Three pages depend on material that is actively moving** — EEVDF (07), folios and MGLRU (08), and the RCU flavours (09). Each carries a context7 verification step *before* writing, and each must date the check in its references. Where context7 has no entry, the instruction is to cite `docs.kernel.org` at v6.18 and say so.
- **Folder 08 is eight tasks and eighteen pages**, and it is the folder every later phase leans on hardest. It is deliberately the phase's centre of gravity; if the phase runs long, the right response is to slow down in folders 05–07, not in 08 or 09.
- **Some `KernelFacts` `observe` commands need root, a debug kernel config, or a specific `CONFIG_` option** (`lock_stat`, `schedstat`, `/proc/slabinfo`, `/sys/kernel/debug/sched/`). Each page must state the requirement rather than presenting a command that silently returns nothing on a stock kernel.
