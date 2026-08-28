# Design: Linux & Kernel Internals documentation section

## Goal

A new top-level documentation section that explains how Linux actually works, from the boundary
between a user-space command and the kernel that services it, down to page-table walks, RCU grace
periods, and the code path a packet takes through `sk_buff`. The reader ends able to read kernel
source, instrument a running system, and reason about behaviour from mechanism rather than from
memorised commands.

The section is `docs/linux/`: **20 numbered folders, 229 topic pages plus a section `readme.md`**,
plus 20 `_category_.json` files, plus **18 backfill pages written into `docs/computer-science/`**
(the hardware and theory prerequisites this section refuses to re-teach), plus site wiring — one
new Docusaurus plugin, four new MDX components, two new dependencies, and one amendment to the
embedded-systems spec.

Total new pages: **247**.

This document specifies the structure, conventions, and a page-by-page outline detailed enough that
writing the actual `.md` content is a mechanical follow-the-outline exercise.

---

## Decisions taken

| Decision | Choice | Where it came from |
|---|---|---|
| Placement | New top-level `docs/linux/` + navbar item inside the existing **Systems** dropdown (4th, after Embedded Systems) | User |
| Size | ~229 pages, 20 folders, 5 phases | User (asked for the ~220/18 option; landed at 20 folders after dissolving a duplicate architecture folder) |
| Lab substrate | **QEMU/x86-64 VM** is the spine — custom-built kernel, BusyBox initramfs, plus a Debian VM for the full-system labs. WSL2 documented for what it can and cannot do | User |
| Arch spine | **x86-64 primary**, arm64 as an explicit contrast thread | User |
| Source pinning | One pinned LTS. Cite `path/file.c:symbol()` — **no line numbers**. Links generated from a single pinned version constant | User |
| Knowledge graph | **Generated from frontmatter** by a custom plugin; unresolvable prerequisite or cycle fails the build | User |
| Folder ordering | Bottom-up stack ladder, with a guided-trace folder layered on top as narrative entry points | User |
| `## What actually happens` | **Conditional**, not furniture — only where a familiar command hides machinery worth exposing | User |
| Missing prerequisites | **Backfilled into `docs/computer-science/`** as new pages, not duplicated into `docs/linux/` | User |
| Embedded overlap | `docs/embedded/10-embedded-linux` shrinks from 14 pages to 5; the embedded spec is amended in the same commit | User |
| Currency | Verified against live documentation via **context7 MCP** at write time, per the per-folder table below | User |
| New tooling | `asciinema-player` for real terminal sessions; existing WaveDrom reused for bit-field layouts; Graphviz considered and rejected (see [Rejected tooling](#rejected-tooling)) | This spec |

---

## Departures from the existing house style

The user asked explicitly not to copy `docs/gpu-computing/` or `docs/embedded/` conventions by
default, only where they are genuinely right. Each inherited or dropped convention below is
justified.

### Kept, with reason

| Convention | Why it earns its place here |
|---|---|
| Numbered folders + `_category_.json` | Folder structure *is* the sidebar in this repo. Numbering is the only way to control order on disk. Non-negotiable mechanics, not style. |
| `## References`, annotated, primary source first | This is the most source-heavy section in the knowledge base. `kernel.org`, LWN, and the source tree are the authority, and an unannotated URL list is useless six months later. |
| Mental model before mechanism | The stated goal is understanding over memorisation. A page that opens with a struct definition has already failed that goal. |
| One visual anchor per page | The user asked specifically for figures and diagrams to aid recall. Enforced, and expanded — see [Visual vocabulary](#visual-vocabulary). |
| Prerequisite declaration | The user asked for a dependency-based learning path. Here it is machine-checked rather than hand-maintained. |

### Dropped, with reason

| Convention | Why it is dropped |
|---|---|
| Hand-written `## See also` on every page | The knowledge-graph plugin generates prerequisite and next-topic links from frontmatter. A hand-maintained list beside a generated one guarantees drift. **Replaced by** a `related:` frontmatter key for lateral (non-dependency) links, rendered in the same generated block. |
| Mandatory `:::warning` per page | Furniture. A warning that exists because the template demanded one trains readers to skip warnings. **Replaced by** the mandatory `Trap` row of the `<KernelFacts>` card, which is a fixed field rather than a decorative box. |
| `## What actually happens` on every page | User's explicit instruction. Present only where a familiar command or a widespread belief hides real machinery. Each qualifying page is marked in the outline with **[WAH]**; that marking is the definitive list, not a quota. |
| Free-form page endings | **Replaced by** a fixed `<KernelFacts>` card on every topic page — see below. Fixed shape means a returning reader can find the struct name, the source path, and the observing command by position, without reading. |

---

## Site wiring

### `sidebars.js`

```js
linuxSidebar: [{ type: "autogenerated", dirName: "linux" }],
```

### `docusaurus.config.js` — navbar

New `docSidebar` item inside the existing **Systems** dropdown, **after** the Embedded Systems item
(4th in the dropdown):

```js
{
  type: "docSidebar",
  sidebarId: "linuxSidebar",
  label: "Linux & Kernel",
  description:
    "How Linux actually works: boot, syscalls, scheduling, memory, VFS, networking, drivers, containers, eBPF.",
  icon: "terminal",
},
```

`terminal` must exist in `src/components/lucide-subset.json`; regenerate via `npm run gen-icons` if
it does not.

### `docusaurus.config.js` — customFields

```js
customFields: {
  githubUrl: "https://github.com/AndriiSonsiadlo/knowledge-base",
  linuxKernelVersion: "vX.Y",   // the pinned LTS — set once at Phase 1, see below
},
```

**One constant, one place.** Every `elixir.bootlin.com` link on every page is generated from this
value by the `<Src>` component. Bumping the section to a newer LTS is a one-line change plus a
review pass, not 229 find-and-replace edits.

**Choosing the value (Phase 1, task 1):** take the newest kernel listed as `longterm` on
`https://www.kernel.org/category/releases.html` whose projected EOL is at least two years out.
Record the exact version, its release date, and its projected EOL in `docs/linux/readme.md`.
Do not guess it from memory — check the page.

### `docusaurus.config.js` — Prism

Current list is `armasm, bash, c, cmake, cpp, csharp, diff, glsl, hlsl, ini, json, makefile, python,
toml, wgsl`. Add four:

```js
"docker", "nasm", "systemd", "yaml",
```

- `nasm` — Intel-syntax disassembly, as produced by `objdump -M intel`.
- `systemd` — unit files (folder 03).
- `docker` — Dockerfiles (folder 15).
- `yaml` — cloud-init, CI, container manifests.

**Fence-language rules, because getting this wrong misleads readers:**

| Content | Fence |
|---|---|
| Kernel C, inline asm inside C | ` ```c ` |
| Intel-syntax disassembly (`objdump -M intel`) | ` ```nasm ` |
| **AT&T-syntax assembly and default `objdump` output** | ` ```text ` — no Prism grammar handles GAS AT&T syntax; `nasm` actively mis-highlights it |
| `Kconfig` source, device tree source, linker scripts | ` ```text ` |
| A kernel `.config` fragment | ` ```ini ` |
| `gdb`, `crash`, `perf`, `bpftrace` session transcripts | ` ```text ` (and usually an `<Cast>` alongside) |
| Kernel boot log / `dmesg` | ` ```text ` |

### New dependencies

| Package | Why |
|---|---|
| `asciinema-player` (^3.17) | Replayable, scrubbable, **text-based** terminal sessions. A `perf record`/`ftrace`/`bpftrace`/`gdb` session is the single most valuable thing to show on a tooling page, and a static screenshot cannot show the interaction. Cast files are a few KB each — orders of magnitude smaller than video, and they carry no autoplay or bandwidth cost. |

That is the only runtime dependency added. Everything else reuses what is installed: Mermaid
(`@docusaurus/theme-mermaid`), WaveDrom (`src/plugins/remark-wavedrom.js` + `src/components/WaveDrom`),
KaTeX, `docusaurus-plugin-image-zoom`, `Tabs`/`TabItem`, and the offline `<Icon>`.

### Rejected tooling

Recorded so it is not re-litigated:

- **Graphviz / `@hpcc-js/wasm`.** Considered for dense call graphs and the knowledge graph itself.
  Rejected: every graph this section actually renders is ≤ 20 nodes (folder-level, or one folder's
  page-level subgraph), which Mermaid handles fine. A full 229-node graph is an unreadable hairball
  in *any* renderer and will not be rendered. Revisit only if a specific figure proves Mermaid
  cannot draw it.
- **Kroki / PlantUML.** Requires a network call at build time, or a self-hosted service. A GitHub
  Actions build that depends on a third-party render service is a deploy that breaks for reasons
  unrelated to the repository.
- **`@docusaurus/theme-live-codeblock`.** Executes JavaScript in the browser. Nothing in this
  section is JavaScript.
- **Video / GIF.** Ruled out by `CLAUDE.md`'s file-size guidance. `<Cast>` covers the use case at a
  fraction of the size and stays greppable.

### New files

```
src/plugins/knowledge-graph-plugin.js
src/components/KnowledgeGraph/index.jsx
src/components/PrereqBlock/index.jsx
src/components/KernelFacts/index.jsx
src/components/Lab/index.jsx
src/components/Cast/index.jsx
src/components/Src/index.jsx
src/lib/kernelSource.js
src/css/custom.css                      (edited — new component classes)
src/theme/DocItem/Layout/index.js       (edited — inject PrereqBlock)
src/theme/MDXComponents.js              (edited — register Lab, KernelFacts, Cast, Src, KnowledgeGraph)
static/casts/linux/*.cast
static/img/linux/SOURCES.md
static/img/linux/<folder-slug>/...
docs/linux/...
docs/computer-science/...               (18 backfill pages)
```

---

## The knowledge-graph plugin

### Frontmatter contract

Every topic page under `docs/linux/` declares its edges:

```yaml
---
id: the-page-fault-handler
title: The Page Fault Handler
sidebar_label: Page fault handler
sidebar_position: 5
tags: [linux, kernel, memory-management]
prerequisites:
  - linux/08-memory-management/page-tables-and-the-walk
  - linux/08-memory-management/mm-struct-and-vmas
related:
  - linux/06-processes-and-threads/task-struct-the-anatomy-of-a-task
  - computer-science/memory-hierarchy/virtual-memory-and-paging
---
```

- `prerequisites` — **directed dependency edges.** "You will not understand this page without that
  one." Ordered by importance; 1–4 entries. An empty list is legitimate (folder 00 and 02 pages).
- `related` — **undirected lateral links.** Same-level material worth knowing about; not a
  dependency. Replaces the hand-written `## See also`.
- Values are doc **ids** as Docusaurus resolves them (the path under `docs/` without extension), and
  **may point outside `docs/linux/`** — pointing at a `computer-science/` page is the normal way a
  Linux page declares a hardware or theory prerequisite.

Verified 2026-08-28: `@docusaurus/plugin-content-docs` validates doc frontmatter with a Joi schema
that ends in `.unknown()` (`lib/frontMatter.js:42`), so unrecognised keys such as `prerequisites`
pass validation untouched and appear on `frontMatter`. No workaround is required.

### `src/plugins/knowledge-graph-plugin.js`

Modelled directly on the existing `src/plugins/recent-docs-plugin.js`, which already reads
`allContent["docusaurus-plugin-content-docs"]` in `allContentLoaded` and publishes with
`actions.setGlobalData`.

```js
module.exports = function knowledgeGraphPlugin(_context, options = {}) {
  return {
    name: "knowledge-graph-plugin",
    async allContentLoaded({ allContent, actions }) { /* ... */ },
  };
};
```

Behaviour:

1. Collect every doc whose id starts with any of `options.scopes` (default `["linux/"]`), plus every
   doc referenced by one of their `prerequisites`/`related` lists (so cross-section targets resolve).
2. Build `nodes: { id, title, sidebarLabel, permalink, folder }` and
   `edges: [{ from, to, kind: "prerequisite" }]`.
3. **Validate, and throw on failure.** The repository already sets `onBrokenLinks: "throw"`; a graph
   that silently rots is worse than no graph.
   - An unresolvable `prerequisites`/`related` id → throw, naming the offending file and id, and
     listing the three closest existing ids by edit distance (a typo'd id must be cheap to fix).
   - A cycle in the prerequisite edges → throw, printing the cycle as a path.
   - A page under `docs/linux/` with no `prerequisites` key at all → throw. Empty list is allowed;
     *forgetting* the key is not, or coverage decays silently as pages are added.
4. `actions.setGlobalData({ nodes, edges })`.

Registered in `docusaurus.config.js` alongside the existing custom plugins:

```js
["./src/plugins/knowledge-graph-plugin.js", { scopes: ["linux/"] }],
```

### `src/components/PrereqBlock/index.jsx`

Reads the current doc's frontmatter via `useDoc()` from
`@docusaurus/plugin-content-docs/client`, and the graph via
`usePluginData("knowledge-graph-plugin")`. Renders up to three rows, omitting any that is empty:

- **Before this** — one chip per `prerequisites` entry, linked, labelled with the target's
  `sidebar_label`. A chip for a target outside `docs/linux/` carries a small section badge
  (`CS`, `Embedded`) so the reader knows they are leaving the section.
- **Next** — computed from **reverse edges**: every page that names this one as a prerequisite.
  Never hand-written, so it cannot fall out of date.
- **Related** — one chip per `related` entry.

### `src/theme/DocItem/Layout/index.js`

Already swizzled in this repository. Inject `<PrereqBlock />` for any doc whose id starts with
`linux/` — "Before this" above the article body, "Next"/"Related" below it. **Zero per-page markup
and zero imports**, which is the reason this is done in the theme rather than as an MDX component
authors must remember.

### `src/components/KnowledgeGraph/index.jsx`

Used on `docs/linux/00-overview/roadmap.md`. Generates a Mermaid `flowchart LR` source string from
global data and hands it to `@theme/Mermaid`.

- Default: **folder granularity** — 20 nodes, one per folder, edges aggregated from the page-level
  edges between folders. Readable.
- `<KnowledgeGraph folder="08" />` — the page-level subgraph for one folder, plus its immediate
  external prerequisites as edge nodes. Rendered at the top of each folder's landing content where
  the folder has more than eight pages.
- Nodes link to the target page. Nodes outside `docs/linux/` are styled distinctly.
- **The full 229-node graph is never rendered.** It is a hairball in every renderer. `roadmap.md`
  carries the folder graph plus the named learning paths as ordered lists.

---

## New MDX components

All registered globally in `src/theme/MDXComponents.js`, alongside the existing `Icon`, `Figure`,
`Recall`, `WaveDrom`, `Tabs`, `TabItem`. Every page therefore stays a plain `.md` file with no
import line, matching how `<Figure>` and `<WaveDrom>` already work.

### `<KernelFacts>` — the fixed recall card

Ends **every topic page**. Follows the precedent of `src/components/Recall.jsx` in the algorithms
section, which exists for exactly the reason the user gave: a card readable by *shape* rather than
by reading, so a returning reader finds what they need by position.

Four fixed rows, always in this order:

| Row | Contents |
|---|---|
| **Structure** | The one or two kernel structures that matter, with the header they live in. `struct vm_area_struct` — `include/linux/mm_types.h` |
| **Path** | The code path in 3–6 hops, arrow-separated. `do_page_fault() → handle_mm_fault() → handle_pte_fault() → do_anonymous_page()` |
| **Observe** | The command that shows this mechanism on a live system. `perf trace -e 'exceptions:page_fault_user'` |
| **Trap** | The single most common wrong belief about this topic, stated and corrected in one sentence. |

`Trap` is mandatory and is why the per-page `:::warning` requirement is dropped. Backtick spans
render as code, matching `Recall`'s `formatRecallText` behaviour — reuse `src/lib/recallFormat.js`
rather than writing a second formatter.

```jsx
<KernelFacts
  structure={[["struct vm_area_struct", "include/linux/mm_types.h"]]}
  path="do_page_fault() → handle_mm_fault() → handle_pte_fault()"
  observe="perf trace -e 'exceptions:page_fault_user' -p $(pgrep -n bash)"
  trap="A major fault is not 'a fault that is worse'. It is a fault that needed I/O. Most faults your process takes are minor, and minor faults are how normal memory allocation works." />
```

### `<Lab>` — hands-on blocks

```jsx
<Lab host="qemu" title="Watch a page fault happen" time="10 min">
...markdown children: numbered steps, expected output, "if it fails" line...
</Lab>
```

- `host` is required and is one of `qemu` | `qemu-gdb` | `any-linux` | `wsl2-ok` | `root-required`.
  It renders as a badge. **A reader must never start a lab and discover four steps in that their
  environment cannot run it.**
- Every lab shows **expected output**, not just commands. A lab whose success criterion is
  unstated is not a lab.
- Every lab ends with a short **"if it fails"** line naming the two most likely causes.

### `<Cast>` — asciinema sessions

```jsx
<Cast src="/casts/linux/ftrace-function-graph.cast" caption="Following a read() with the function-graph tracer" />
```

- `src/components/Cast/index.jsx` wraps the player in `<BrowserOnly>` and dynamically imports
  `asciinema-player` plus its CSS — the library touches `document` at import time and will break
  SSR otherwise.
- Player options fixed across the section: no autoplay, `idleTimeLimit: 2`, `fit: "width"`,
  `theme: "asciinema"`, poster at the first interesting frame.
- **Every cast is accompanied by the decisive output as a `text` code block.** The player is
  progressive enhancement: casts are not indexed by the offline search, do not render without
  JavaScript, and cannot be copied from. The text block is the content; the cast shows the
  interaction.
- Casts are recorded from the QEMU lab described in folder 01, using the same kernel version pinned
  in `customFields`. A cast recorded on a random host contradicts the section.
- Budget: **≤ 25 casts across the section**, concentrated in folders 01, 17, 18, 19. Keep each under
  ~90 seconds.

### `<Src>` — pinned source links

```md
Path resolution happens in <Src file="fs/namei.c" symbol="path_openat" />.
```

Renders `fs/namei.c:path_openat()` as inline code, using Elixir's two stable route forms:

| Props | Link target |
|---|---|
| `file` only | `https://elixir.bootlin.com/linux/<ver>/source/<file>` |
| `file` + `symbol` | `https://elixir.bootlin.com/linux/<ver>/ident/<symbol>` — Elixir's identifier index, which resolves a symbol to its definition **and** all its uses without a line number |
| `symbol` only | same `ident/` route; renders as `path_openat()` |

Neither route contains a line number, which is the whole point. Version comes from
`useDocusaurusContext().siteConfig.customFields.linuxKernelVersion` via `src/lib/kernelSource.js`.
Phase 1 verifies both route forms resolve for the chosen version before any page uses them —
Elixir's URL scheme is the one external contract this section leans on hardest.

**All source references use `<Src>`.** No hand-written elixir URLs, no line numbers anywhere in the
section — line numbers rot within one release, symbol names and paths survive for years.

---

## Page conventions

### Frontmatter

```yaml
---
id: <kebab-case-id>
title: <Human Title>
sidebar_label: <short label>
sidebar_position: <int, order within its folder>
tags: [linux, <area-tag>, <topic-tag>...]
prerequisites: [<doc-id>, ...]     # required key; may be empty
related: [<doc-id>, ...]           # optional
---
```

- `tags` always begins with `linux`. Kernel-internals pages add `kernel`. Folder area tags:
  `boot`, `syscalls`, `scheduling`, `memory-management`, `locking`, `interrupts`, `vfs`, `block-io`,
  `networking`, `drivers`, `containers`, `security`, `observability`, `ebpf`, `kernel-development`.
- `sidebar_position` starts at 1 within each folder.

### Folder `_category_.json`

```json
{
  "label": "<Label>",
  "position": <int>,
  "link": {
    "type": "generated-index",
    "description": "<one sentence>"
  }
}
```

`position` equals the numeric folder prefix + 1, so `00-overview` is position 1. The `description`
is always filled — the generated index page is a real navigation surface, and an empty one wastes it.

### Page structure

1. `# H1` matching `title`.
2. **Mental model first.** One or two paragraphs: what problem this exists to solve, and why the
   design came out this way. No page opens with a struct definition, a code block, or a command.
3. `##` sections per subtopic; `###` sparingly.
4. **`## What actually happens`** — *conditional*. Include it when a familiar command, or a belief
   most people hold, hides machinery worth exposing: `ls`, `free`, `top`, `ps`, `df`, `kill`,
   `mount`, `ping`, `docker run`, `strace`, "the process is using 2 GB", "the container is a
   lightweight VM". Marked **[WAH]** in the outline below where it is expected. Do not add it
   elsewhere; a section that appears on every page stops being read.
5. **At least one visual anchor**: a Mermaid diagram, a WaveDrom bit-field, a sourced `<Figure>`, a
   `<Cast>`, or a substantive comparison table. A page with no visual anchor is flagged in review.
6. **`## Misconceptions`** — where the topic has widely-held wrong beliefs. Each stated plainly,
   then corrected, in two or three sentences. Every entry is mirrored into
   `00-overview/misconceptions-index.md`.
7. **`<Lab>`** — where the topic can be observed or reproduced. Marked **[Lab]** in the outline;
   folders 01, 05, 06, 08, 11, 14, 15, 17, 18 carry them densely. Adding a lab to a page not marked
   is welcome; removing a marked one needs a reason.
8. `## References` — 2–6 annotated external sources (see below).
9. `<KernelFacts>` — the closing card. Mandatory.

Prerequisite and next-topic links are **not** written by hand — the theme injects them from
frontmatter.

### Admonitions

The four the knowledge base already uses. Do not invent more.

| Admonition | Use for |
|---|---|
| `:::info[...]` | Framing the problem a mechanism solves; version-scoped notes |
| `:::note[...]` | Side facts; arm64 contrast callouts; "this changed in 6.x" |
| `:::tip[...]` | Practical guidance, rules of thumb, the flag that saves an hour |
| `:::warning[...]` | Real hazards only: things that corrupt data, hang a machine, or teach a wrong model that is expensive to unlearn. Used where warranted, never as template furniture |

**arm64 contrast callouts** are a recurring `:::note` and are the mechanism by which this section
stays honest about being x86-64-first. They appear where the difference is structural, not
cosmetic: syscall entry (`SVC` vs `SYSCALL`), privilege levels (EL0–EL3 vs rings), interrupt
controllers (GIC vs APIC), page-table format and levels, memory ordering (weak vs TSO — this one
matters enormously in folder 09), absence of port I/O, and device enumeration (device tree/ACPI vs
PCI probing).

### Visual vocabulary

Each tool has exactly one job, so pages stay predictable and a reader learns to read them by shape.

| Tool | Used for |
|---|---|
| **Mermaid `flowchart`** | Code paths, subsystem layering, decision flows, packet/request journeys |
| **Mermaid `stateDiagram`** | State machines: task states, TCP states, page states, device PM states, connection tracking |
| **Mermaid `sequenceDiagram`** | Cross-component interactions over time: syscall entry/exit, a fault round-trip, DMA + interrupt handshake, an RCU grace period |
| **WaveDrom `reg`** | Every bit-field layout in the section: PTE bits, `EFLAGS`/`CR0`/`CR4`, GFP flags, `clone()` flags, TCP/IP headers, `sk_buff` layout, PCI config space header, BPF instruction encoding, `open()` flags, cgroup masks |
| **WaveDrom `signal`** | The few genuinely time-axis things: interrupt latency breakdown, DMA transfer phases, an RCU grace period against reader critical sections |
| **`<Figure>`** | Real things a drawing cannot convey: canonical published stack diagrams, `perf` and profiler screenshots, real flamegraphs, `crash` output, hardware topology |
| **`<Cast>`** | Interactive tool sessions where the *interaction* is the lesson |
| **`<Tabs>`** | Two or three genuine alternatives side by side: x86-64 vs arm64, cgroup v1 vs v2, iptables vs nftables, `strace` vs `bpftrace`, glibc vs musl vs raw `syscall()` |
| **Table** | Comparison and enumeration: GFP flag semantics, lock selection, scheduler class comparison, namespace types, sanitizer coverage |

**Every diagram carries an `alt`/caption that states what it shows**, not what it is. "The read path
from `sys_read` to the block layer", never "Diagram 3".

**Struct-heavy pages get a struct-shape diagram, not a struct dump.** `task_struct` is ~200 fields;
pasting it teaches nothing. Show the ~12 fields that matter grouped by concern (identity,
scheduling, memory, files, signals, credentials) as a Mermaid `classDiagram` or a grouped table,
with `<Src>` linking to the real definition.

### Images

```
static/img/linux/<folder-slug>/<name>.png
```

Referenced through `<Figure>` with a `/img/linux/...` path — **no** `/knowledge-base` prefix;
`useBaseUrl` prepends `baseUrl` itself.

Every file gets a row in `static/img/linux/SOURCES.md` with `file`, `source_url`, `publisher`,
`license`, `retrieved`, `notes` — one column more than `static/img/gpu/SOURCES.md`, because this
section leans on copyleft sources whose licence terms require attribution and must therefore be
tracked per file, not assumed.

**Preferred sources, in order:**

1. **kernel.org documentation and the source tree's own `Documentation/`** — the authority.
2. **Bootlin training materials** (CC BY-SA) — the best license-clean source for kernel and driver
   figures. Attribute the licence in the caption.
3. **Thomas-Krenn wiki — "Linux Storage Stack Diagram"** by Werner Fischer and Georg Schönberger,
   CC BY-SA 3.0. The canonical storage-stack figure, and licence-clean. Folder 12's anchor image.
   Use the revision matching the pinned kernel where one exists; state the diagram's kernel version
   in the caption, because it is versioned and readers will compare it to their own system.
4. **Wikimedia Commons** — explicit licence metadata; good for hardware topology and standard
   protocol figures.
5. **Brendan Gregg's diagrams** (Linux performance observability map, flamegraphs) — licence must be
   **checked per image** before use, not assumed from the site as a whole. If a specific image's
   terms are unclear, do not use it; redraw the concept in Mermaid and cite his page in
   `## References` instead.
6. **Own screenshots** from the QEMU lab — `perf report`, `crash`, a flamegraph of a real workload,
   `htop` under load. These are free of licence questions entirely and should be the default for
   anything showing tool output.

Never substitute a blog or image-host copy of a figure to have one. **If no properly-sourced figure
exists, draw it in Mermaid — that is the correct outcome, not a fallback.**

Size discipline: `static/img/gpu/` is ~1.2 MB for 129 pages. `static/img/linux/` should stay in the
same order of magnitude. Prefer PNG screenshots downscaled to ≤ 1400 px wide; prefer SVG for
anything vector. `static/casts/linux/` should stay under ~500 KB total.

### External references

Every topic page ends with `## References`: **2–6 entries**, each annotated with why a reader would
click it. Bare URLs are not acceptable. Tiered, in this order:

1. **Primary** — `docs.kernel.org`, the in-tree `Documentation/` file, the source itself via `<Src>`,
   the relevant `man` page (section 2 or 7), an RFC, an Intel SDM or Arm ARM chapter.
2. **LWN.net** — the single best secondary source for kernel mechanism and, critically, for *why* a
   design changed. Cite the specific article, and note where an article predates the pinned kernel
   and describes an earlier design.
3. **Canonical books** — see the master list in `readme.md`.
4. **Talks and interactive material** — where watching genuinely beats reading.

Where a source is paywalled or a purchase, say so in the annotation. Where an article is
significantly older than the pinned kernel, say so — a 2013 LWN piece on the CFS scheduler is
excellent history and actively misleading as current documentation.

The section `readme.md` carries the curated master list:

- Robert Love, *Linux Kernel Development* (3rd ed.) — the best first kernel book; note it predates
  the pinned kernel substantially and is a conceptual, not a current, reference.
- Bovet & Cesati, *Understanding the Linux Kernel* — deeper, older still; the memory-management and
  interrupt chapters remain the clearest long-form treatment.
- Corbet, Rubini & Kroah-Hartman, *Linux Device Drivers* (3rd ed.) — free online, ancient APIs,
  still the best explanation of the *model*. Every citation must say which parts have changed.
- Brendan Gregg, *Systems Performance* (2nd ed.) and *BPF Performance Tools* — the observability and
  eBPF references, and current.
- Michael Kerrisk, *The Linux Programming Interface* — the definitive user-space/syscall reference.
- W. Richard Stevens & Rago, *Advanced Programming in the UNIX Environment*.
- Mauerer, *Professional Linux Kernel Architecture* — for the subsystems the others skip.
- `docs.kernel.org`, `lwn.net`, `elixir.bootlin.com`, `man7.org`, `bootlin.com/docs/`,
  `kernelnewbies.org`.

### Content currency — context7 verification

Kernel-adjacent user-space tooling moves fast and its documentation is what readers will actually
run. **Verify against live documentation via the context7 MCP at write time**, and record the check
date in the page's `## References` annotation.

| Folder | Verify via context7 |
|---|---|
| 01 | QEMU invocation and options; current `make` targets and `menuconfig` behaviour |
| 03 | systemd (unit directives, `systemd-analyze`, targets); GRUB 2 configuration |
| 07 | EEVDF status and tunables — this replaced CFS recently and most material online is stale |
| 08 | Folio API surface; MGLRU status and tunables |
| 09 | RCU API surface; `refcount_t` vs `atomic_t` guidance |
| 12 | `io_uring` API surface — it moves faster than any other interface here |
| 13 | nftables syntax; `iproute2` command surface; BBRv3 status |
| 14 | Current driver-model APIs; DMA API function names |
| 15 | cgroup v2 controller files and semantics; runc/containerd/OCI runtime spec; Docker CLI |
| 16 | seccomp, SELinux, AppArmor policy tooling |
| 17 | `perf` subcommand surface; `crash` utility |
| 18 | `libbpf` API and CO-RE macros; `bpftrace` language reference; BCC tool inventory |
| 19 | `b4`, `checkpatch.pl` options, current submitting-patches process |

Where context7 has no entry for a source (the kernel's own `Documentation/` tree, for instance),
cite `docs.kernel.org` at the pinned version and say so.

### Accuracy guardrails

- **State the kernel version for any claim that is version-dependent.** "The fair scheduler uses
  EEVDF" is true of the pinned kernel and false of a 6.5 system. Version-scoped claims carry a
  `:::note`.
- **Distinguish architecture-general from x86-64-specific.** A page that says "the kernel puts the
  syscall number in `rax`" must say x86-64. Sloppiness here produces readers who are confidently
  wrong on arm64.
- **Do not present a simplified path as the real one without saying so.** Where the outline says a
  path is simplified (fast paths, error paths, and `CONFIG_*` variants elided), the page says so in
  one sentence and links the real entry point with `<Src>`.
- **Never invent a struct field, function name, or file path.** Every symbol named on a page is
  checked against the pinned source via Elixir before the page is committed. A plausible-looking
  wrong symbol is worse than an omission, because it is unfalsifiable to a beginner.
- **Folder 16 is defensive.** Attack classes are explained so readers can recognise, mitigate, and
  patch them. Pages do not include working exploit code or step-by-step exploitation procedures.

---

## Prerequisite backfill into `docs/computer-science/`

The user's instruction: where this section needs a prerequisite that the knowledge base does not
yet cover, extend the existing section rather than duplicating the material into `docs/linux/`.

**Policy, normative:** `docs/linux/` never teaches hardware behaviour or general OS theory. Where
the prerequisite is missing, the fix is a **new page in `docs/computer-science/`**, which the Linux
page then names in its `prerequisites` frontmatter. This keeps ownership single, improves the whole
knowledge base rather than only the new section, and makes the generated graph span sections
correctly.

**18 new pages.** Each is delivered in the phase that first needs it (column 4), so no page is
written speculatively.

| # | New page | Why Linux needs it | Phase |
|---|---|---|---|
| 1 | `cpu-architecture/privilege-levels-and-protection.md` | Rings, supervisor/user enforcement, how the CPU makes a boundary unforgeable. Prerequisite for the entire kernel/user-space model | 1 |
| 2 | `cpu-architecture/exceptions-traps-and-interrupts.md` | The taxonomy — fault/trap/abort/interrupt, precise exceptions, vectoring. Prerequisite for syscalls, page faults, IRQ handling | 1 |
| 3 | `cpu-architecture/memory-ordering-and-consistency.md` | SC vs TSO vs weak ordering, store buffers, fences, why the compiler reorders. Prerequisite for folder 09 — the single hardest hardware dependency in the section | 2 |
| 4 | `cpu-architecture/atomic-operations-in-hardware.md` | CAS, LL/SC, `LOCK` prefix, cache-line ownership and its cost | 2 |
| 5 | `cpu-architecture/hardware-virtualization.md` | VT-x/AMD-V, VM entry/exit, EPT/NPT, why a VM exit is expensive | 4 |
| 6 | `memory-hierarchy/tlb-and-address-translation-hardware.md` | TLB structure, page-walk caches, ASID/PCID, shootdown cost | 2 |
| 7 | `memory-hierarchy/cache-coherence-and-mesi.md` | MESI/MOESI, snooping vs directory, false sharing. Prerequisite for per-CPU data and lock cost | 2 |
| 8 | `memory-hierarchy/numa-and-memory-topology.md` | Node distance, local vs remote latency, interleaving | 2 |
| 9 | `buses-and-io/pcie-in-depth.md` | Config space, BARs, enumeration, MSI/MSI-X, link topology. `buses-and-io/system-interconnects.md` mentions PCIe; a driver reader needs the enumeration model | 4 |
| 10 | `buses-and-io/interrupt-controllers.md` | PIC → APIC → x2APIC, GIC contrast, routing and affinity | 2 |
| 11 | `buses-and-io/dma-and-iommu.md` | Bus-master DMA, scatter-gather, IOMMU/SMMU translation and isolation, cache coherency with DMA | 4 |
| 12 | `storage/raid-and-redundancy.md` | RAID levels, write hole, rebuild cost. Prerequisite for md/LVM | 3 |
| 13 | `storage/crash-consistency-and-journaling.md` | Write ordering, barriers, journal vs CoW vs log-structured, what durability actually requires | 3 |
| 14 | `computer-networks/sockets-and-the-application-boundary.md` | The socket API as the boundary the kernel implements — the existing network pages stop at the transport layer and never reach the API | 3 |
| 15 | `computer-networks/arp-icmp-and-neighbour-discovery.md` | Address resolution and the diagnostic protocols; prerequisite for the neighbour table and `ping` | 3 |
| 16 | `computer-networks/nat-and-connection-tracking.md` | NAT forms and why stateful tracking is required. Prerequisite for netfilter and container networking | 3 |
| 17 | `operating-systems/os-structure-monolithic-microkernel-hybrid.md` | The architectural taxonomy Linux sits in, and the actual trade-offs behind the debate | 1 |
| 18 | `operating-systems/virtualization-and-isolation.md` | VMs vs containers vs sandboxes as *isolation theory*; where each boundary is enforced | 4 |

**Edits to existing pages** (small, additive, no rewrites):

| Page | Edit |
|---|---|
| `computer-science/memory-hierarchy/virtual-memory-and-paging.md` | Add a closing pointer to `linux/08-memory-management/page-tables-and-the-walk`; verify the multi-level walk description matches what folder 08 will build on |
| `computer-science/operating-systems/scheduling.md` | Add a pointer to `linux/07-scheduling` for the real implementation. **Do not** add EEVDF detail here — folder 07 owns it |
| `computer-science/operating-systems/concurrency-and-synchronization.md` | Add pointers to `linux/09-concurrency-and-locking`, and to backfill pages 3, 4, 7 |
| `computer-science/operating-systems/{processes-and-threads,memory-management,interprocess-communication}.md` | One pointer each into the corresponding Linux folder |
| `computer-science/storage/filesystems-basics.md` | Pointer to `linux/11-vfs-and-filesystems`; confirm it does not already claim VFS-specific behaviour |
| `computer-science/assembly/calling-conventions-and-the-stack.md` | Confirm the ABI covered is x86-64 System V; add the syscall calling convention (`rax`/`rdi`/`rsi`/`rdx`/`r10`/`r8`/`r9`, `SYSCALL` clobbering `rcx`/`r11`) and a pointer to `linux/05-syscalls-and-the-boundary` |
| `computer-science/buses-and-io/io-and-interrupts.md` | Pointer to backfill page 10 and to `linux/10-interrupts-time-and-deferred-work` |

**Backlinks from existing pages are required here**, unlike the embedded spec which made them
optional. A generated dependency graph with one-way edges is half a graph, and the backfill pages
exist precisely to be depended on.

---

## No-duplication contract

Existing pages own their topics. Linux pages link and go deeper; they do not re-explain. This table
is normative — check it before drafting any page whose subject appears here.

| Canonical owner | Linux pages that link rather than repeat |
|---|---|
| `computer-science/cpu-architecture/*` (incl. backfill 1–5) | `00/hardware-the-kernel-assumes`, `05/*`, `09/memory-ordering-and-barriers`, `15/kvm-and-hardware-virtualization` |
| `computer-science/memory-hierarchy/*` (incl. backfill 6–8) | folder 08 — hardware paging, TLB, cache, and NUMA *hardware* are owned there; the kernel's *use* of them is owned here |
| `computer-science/buses-and-io/*` (incl. backfill 9–11) | folder 14, and `10/how-an-interrupt-reaches-the-kernel` |
| `computer-science/storage/*` (incl. backfill 12–13) | folders 11 and 12 — device physics, NVMe protocol, RAID theory, journaling theory owned there |
| `computer-science/computer-networks/*`, `protocols/*` (incl. backfill 14–16) | folder 13 — protocol semantics owned there; the kernel's datapath owned here |
| `computer-science/operating-systems/*` (incl. backfill 17–18) | folders 06, 07, 08, 09, 15 — algorithmic and conceptual theory owned there; Linux's actual mechanism owned here |
| `computer-science/assembly/*` | `05/the-syscall-instruction-and-entry-path`, `17/reading-an-oops-and-a-panic` |
| `computer-science/bit-manipulation/*` | anywhere bit manipulation appears; never re-explained |
| `docs/embedded/*` | `03/*` (contrasted with U-Boot), `14/platform-devices-and-devicetree`, `07/real-time-classes` (PREEMPT\_RT) |
| `docs/computer-science/databases/*` | `12/diagnosing-io-problems`, `11/journaling-and-crash-consistency` — durability from the database side is owned there |

### Amendment to the embedded-systems spec

`docs/superpowers/specs/2026-08-18-embedded-systems-docs-design.md` specifies
`10-embedded-linux` as 14 pages. That folder is **not yet written**. Amend it, in the same commit
as this spec, to **5 pages** covering only what is genuinely embedded-specific:

| Kept | Reason |
|---|---|
| `when-you-need-linux.md` | The MCU-vs-MPU decision; no equivalent in `docs/linux/` |
| `devicetree.md` | Central to embedded Linux, marginal on x86-64 |
| `u-boot-and-embedded-boot.md` | A different boot chain from UEFI/GRUB |
| `buildroot-and-yocto.md` | Building a distribution; no equivalent elsewhere |
| `preempt-rt-and-real-time-linux.md` | Real-time is the embedded reason to care |

The other nine planned pages (kernel basics, drivers, filesystems, debugging, networking) become
links into `docs/linux/`. Update the embedded spec's page count and its own no-duplication table
accordingly.

---

## Page-by-page outline

Each entry is `filename` — Title — content brief. Order within a folder is `sidebar_position`.
**[WAH]** marks a page expected to carry a `## What actually happens` section. **[Lab]** marks a
page expected to carry a `<Lab>`.

### `readme.md` (section root)

Landing page. What the section covers and what it deliberately does not, the pinned kernel version
with its release and EOL dates, the curated master reference list, the lab prerequisites in one
paragraph with a link to folder 01, and a pointer to `00-overview/roadmap.md` for the graph and the
learning paths. `tags: [linux, kernel]`.

---

### 00-overview — "Overview" (position 1) — 9 pages

| File | Title | Brief |
|---|---|---|
| `what-this-section-covers.md` | What This Section Covers | Scope and non-scope. What "understanding Linux" means operationally: predicting behaviour from mechanism, reading source to answer a question, instrumenting rather than guessing. Explicitly not a distribution guide, not a sysadmin certification path |
| `the-kernel-userspace-boundary.md` | The Kernel/User-Space Boundary | **The** mental model of the whole section. Two worlds, one hardware-enforced door. What is on each side, what crosses and how, why the boundary exists at all, and why "the kernel" is not a program you can `ps` **[WAH]** |
| `what-linux-actually-is.md` | What Linux Actually Is | Kernel vs GNU vs distribution vs "Linux". A short, honest history focused on the design decisions that still constrain the system: monolithic-with-modules, the stable-ABI-for-user-space rule, the no-stable-ABI-for-modules rule **[WAH]** |
| `hardware-the-kernel-assumes.md` | The Hardware the Kernel Assumes | The bridge page. The seven hardware capabilities every Linux mechanism rests on — privilege levels, an MMU, precise exceptions, interrupts, atomics, a timer, DMA-capable devices — each in a paragraph, each linking to its owning `computer-science/` page. This page exists so no Linux page ever re-teaches hardware |
| `distributions-and-what-differs.md` | Distributions and What Actually Differs | Same kernel, different packaging: init choice, package manager, patch sets, defaults, kernel config. What genuinely varies between Debian, Fedora, Arch, Alpine, and Android — and the far longer list of things that do not **[WAH]** |
| `how-to-use-this-section.md` | How to Use This Section | The folder ladder and why it is ordered that way. How the prerequisite blocks and the graph work. How labs are marked by host. The convention that a `<KernelFacts>` card ends every page and what each row means |
| `roadmap.md` | Roadmap and Knowledge Graph | `<KnowledgeGraph />` at folder granularity, plus six named learning paths as ordered page lists: **"I just want to understand my machine"**, **"I want to write a driver"**, **"My server is slow"**, **"I want to work on containers"**, **"I want to read kernel source"**, **"I want to send a patch"** |
| `glossary.md` | Glossary | ~90 terms, one paragraph each, each linked to its owning page: task, thread group, `mm_struct`, VMA, folio, page cache, dentry, inode, `sk_buff`, bio, softirq, RCU grace period, cgroup, namespace, capability, LSM, BTF, tracepoint, kprobe, initcall, `EXPORT_SYMBOL_GPL`, oops, taint, and the rest |
| `misconceptions-index.md` | Index of Misconceptions | Every `## Misconceptions` entry in the section, gathered and linked. Deliberately blunt: "load average is CPU usage" — no. "Threads are lighter than processes on Linux" — not in the way you think. "`free` shows how much memory you have left" — no. "A container is a lightweight VM" — no. A reader who reads only this page still gains something **[WAH]** |

---

### 01-lab-and-toolchain — "Setting Up a Lab" (position 2) — 7 pages

Everything after this folder assumes this lab. Written so a reader can go from nothing to a
kernel they built, booting under a debugger, in an afternoon.

| File | Title | Brief |
|---|---|---|
| `the-lab-machine.md` | The Lab Machine | Why QEMU is the spine: a kernel panic costs you nothing, you can attach a debugger to the CPU itself, and you control the exact kernel version. What each lab host badge means. What you need installed on the host, for Debian/Fedora/Arch and for WSL2 |
| `getting-and-navigating-the-source.md` | Getting the Source | `git clone` vs a release tarball, checking out the pinned LTS tag, repository size and shallow clones, and the first orientation pass through the top-level directories **[Lab]** |
| `building-a-kernel.md` | Building a Kernel | `defconfig`, `menuconfig`, the options that matter for a debuggable lab kernel (`CONFIG_DEBUG_INFO`, `CONFIG_GDB_SCRIPTS`, `CONFIG_KALLSYMS_ALL`, `CONFIG_FRAME_POINTER`, `CONFIG_DEBUG_KERNEL`, `CONFIG_KASAN` off by default), parallel build, realistic build times, `vmlinux` vs `bzImage` vs `arch/x86/boot/bzImage` **[Lab]** |
| `a-minimal-rootfs.md` | A Minimal Root Filesystem | BusyBox static build, the directory skeleton, `/init`, `cpio` packing into an initramfs. Why this is worth doing once: it makes early user space concrete instead of magical **[Lab]** |
| `booting-your-kernel-in-qemu.md` | Booting Your Kernel in QEMU | The canonical invocation used by every later lab, flag by flag: `-kernel`, `-initrd`, `-append console=ttyS0`, `-nographic`, `-m`, `-smp`, `-enable-kvm`. Reading the boot log. Getting out of QEMU when it hangs **[Lab]** |
| `debugging-the-kernel-with-gdb.md` | Debugging the Kernel with GDB | `-s -S`, `target remote :1234`, loading `vmlinux` symbols, the in-tree `scripts/gdb` helpers (`lx-dmesg`, `lx-ps`, `lx-lsmod`), breaking on a kernel function, walking a real `task_struct`. The single highest-leverage skill in this section **[Lab]** `<Cast>` |
| `a-full-system-vm-and-wsl2.md` | A Full-System VM, and What WSL2 Can Do | A Debian cloud image under QEMU for the labs needing systemd, real block devices, and a network stack: snapshots, serial console, `virtiofs`. Then WSL2, honestly — a Microsoft kernel, no UEFI/GRUB chain, a partly synthetic `/proc` and `/sys`, no `kexec`/`kdump`, systemd optional. A table of which folders' labs run on it |

---

### 02-guided-traces — "Guided Traces" (position 3) — 6 pages

Narrative entry points. Each follows one familiar thing all the way down and forward-links every
mechanism it passes. Deliberately shallow in depth and complete in breadth: the reader finishes with
a *map*, and every box on that map is a link. `prerequisites: []` — these are readable first.

| File | Title | Brief |
|---|---|---|
| `what-happens-when-you-type-ls.md` | What Happens When You Type `ls` | Terminal → line discipline → shell `fork`+`exec` → ELF load → dynamic linker → `getdents64` → VFS → page cache → `write` to a pty → back to the terminal. Twenty mechanisms named and linked in one story **[WAH]** |
| `the-life-of-a-write.md` | The Life of a `write()` | `write(2)` → syscall entry → VFS → page cache → dirty page → writeback → block layer → `bio` → blk-mq → NVMe queue → completion interrupt. Where the data actually is at each moment, and what `fsync` changes **[WAH]** |
| `the-life-of-a-page-fault.md` | The Life of a Page Fault | An ordinary `malloc` + first touch: no physical page, MMU fault, `do_page_fault`, VMA lookup, zero page or allocation, PTE install, `iret`, the instruction re-executes. Minor vs major. Why this is the *normal* case, not an error **[WAH]** |
| `the-life-of-a-packet.md` | The Life of a Packet | Wire → NIC DMA ring → interrupt → NAPI poll → GRO → `sk_buff` → netfilter → routing → TCP → socket receive queue → `recv()` wakes your process. And the reverse for transmit **[WAH]** |
| `from-power-on-to-login-prompt.md` | From Power-On to Login Prompt | Firmware → UEFI → boot loader → `bzImage` decompression → early arch setup → `start_kernel` → initcalls → initramfs → `switch_root` → PID 1 → the unit graph → `getty` **[WAH]** |
| `the-life-of-a-container.md` | The Life of a Container | `docker run` de-mystified: image layers as overlayfs, `clone()` with namespace flags, `pivot_root`, cgroup assignment, capability drop, seccomp filter, veth pair and NAT rule, then `exec`. A "container" is a process with unusual arguments **[WAH]** |

---

### 03-boot-and-init — "Boot and Init" (position 4) — 12 pages

| File | Title | Brief |
|---|---|---|
| `firmware-bios-and-uefi.md` | Firmware: BIOS and UEFI | What the firmware does before anything Linux exists: POST, memory map construction, device enumeration. Legacy BIOS vs UEFI as *models* — the ESP, boot variables, runtime services, why UEFI made boot loaders simpler and boot debugging harder |
| `the-boot-chain.md` | The Boot Chain | The full handoff sequence as one diagram, with the exact artefact handed over at each step and where each one lives on disk. The reference diagram the rest of the folder expands |
| `bootloaders-grub-and-friends.md` | Boot Loaders | GRUB 2 structure and configuration (and why you never edit `grub.cfg` directly), `systemd-boot`, direct EFI stub boot. What a boot loader must do: find a kernel, find an initramfs, build a command line, hand over **[WAH]** |
| `the-kernel-command-line.md` | The Kernel Command Line | How parameters reach the kernel, `__setup`/`early_param` parsing, `/proc/cmdline`, and the parameters worth knowing: `root=`, `init=`, `console=`, `quiet`, `nokaslr`, `maxcpus=`, `systemd.unit=`. The single most useful debugging tool in the folder **[Lab]** |
| `secure-boot-and-signed-kernels.md` | Secure Boot and Signed Kernels | The chain of trust from firmware keys to a signed kernel and signed modules. Shim, MOK enrolment, `CONFIG_MODULE_SIG`, lockdown mode. What Secure Boot does and does not protect against |
| `the-kernel-image.md` | Inside `bzImage` | The layout of a compressed kernel image: setup header, real-mode stub, compressed payload, decompressor. WaveDrom of the setup header fields that matter. Why `vmlinux`, `vmlinuz`, and `bzImage` are three different things **[WAH]** |
| `early-boot-and-arch-setup.md` | Early Boot: Getting to C | x86-64 specifically: 16-bit entry, protected mode, building the early page tables, entering long mode, relocation and KASLR, `start_kernel`'s first callers. `:::note` contrasting arm64's much simpler entry |
| `start-kernel-and-initcalls.md` | `start_kernel` and the Initcall Order | What `start_kernel` brings up and in what order: memory subsystem, scheduler, timers, IRQs, then the initcall levels (`early`, `core`, `postcore`, `arch`, `subsys`, `fs`, `device`, `late`). Why driver init order is a level, not a list. `initcall_debug` **[Lab]** |
| `initramfs-and-early-userspace.md` | initramfs and Early User Space | Why a root filesystem needs a root filesystem: the module-and-driver chicken-and-egg. `cpio` format, `rootfs` as a tmpfs, `/init`, `dracut`/`mkinitcpio` generation, unpacking one to look inside **[WAH]** **[Lab]** |
| `switch-root-and-pid-1.md` | `switch_root` and PID 1 | Mounting the real root, `switch_root` vs `pivot_root` vs `chroot` — three different things constantly confused. What makes PID 1 special: no default signal handlers, orphan reaping, unkillable, and what happens if it exits **[WAH]** |
| `systemd-the-model.md` | systemd: The Model | Units and types, dependencies (`Requires`/`Wants`/`After`) vs ordering as *separate* axes — the misconception that eats the most time. Targets instead of runlevels, the transaction the manager computes at boot, `systemd-analyze plot`/`critical-chain` **[WAH]** |
| `systemd-in-practice-and-boot-debugging.md` | systemd in Practice, and Debugging a Broken Boot | Socket and path activation, journald, service supervision, the cgroup-per-unit tie-in to folder 15. Then the debugging playbook: `init=/bin/sh`, emergency and rescue targets, `earlyprintk`, `systemd.log_level=debug`, reading a boot that ends in a kernel panic **[Lab]** |

---

### 04-kernel-architecture-and-idioms — "Kernel Architecture and Idioms" (position 5) — 12 pages

This folder is the prerequisite for reading any kernel code at all, and is deliberately placed
before the subsystem folders for that reason.

| File | Title | Brief |
|---|---|---|
| `monolithic-with-modules.md` | Monolithic, With Modules | Where Linux sits in the architecture taxonomy and why: one address space, no message passing between subsystems, loadable modules for build-time flexibility, not isolation. The honest trade-off — a driver bug is a kernel bug. Links to the CS backfill page for the theory **[WAH]** |
| `the-source-tree-map.md` | The Source Tree, Mapped | Every top-level directory in one line each, with the four that matter most expanded: `kernel/`, `mm/`, `fs/`, `drivers/`. Where a given question's answer lives, as a lookup table. The page a reader returns to for years |
| `kconfig-and-kbuild.md` | Kconfig and Kbuild | `Kconfig` language, symbol dependencies, tristate and why `m` exists, `.config` as the single source of truth, how `Makefile` `obj-$(CONFIG_FOO)` turns a symbol into a compiled object. Why `#ifdef CONFIG_` is everywhere and how to read past it |
| `modules-in-practice.md` | Kernel Modules | `module_init`/`module_exit`, `MODULE_LICENSE` and what "tainted" means, parameters, `modprobe` vs `insmod`, dependency resolution via `modules.dep`, `/proc/modules` and `/sys/module`. Out-of-tree builds against kernel headers **[Lab]** |
| `exported-symbols-and-the-module-abi.md` | Exported Symbols and the Non-Stable ABI | `EXPORT_SYMBOL` vs `EXPORT_SYMBOL_GPL`, symbol versioning (`modversions`), and the deliberate absence of a stable in-kernel ABI — what that means for out-of-tree drivers, and why "don't break user space" and "break modules freely" are consistent positions, not hypocrisy **[WAH]** |
| `the-kernel-c-dialect.md` | The Kernel Is Not C You Know | Freestanding C: no libc, no floating point, an 8–16 KB stack, `-ffreestanding`, GCC extensions in daily use (statement expressions, `typeof`, `__attribute__`), the `__init`/`__exit`/`__percpu`/`__user` annotations and what sparse does with them |
| `kernel-data-structures.md` | Kernel Data Structures | `struct list_head` and the intrusive-list model, `hlist`, `rb_tree`, `xarray` (and the `radix_tree` it replaced), `idr`/`ida`, bitmaps. Why intrusive containers, and what that costs. Diagrams, then the API |
| `container-of-and-embedded-structs.md` | `container_of` and Embedded Structs | The central Linux idiom, derived from scratch: from "a list node inside a struct" to the macro's actual expansion. Once this clicks, `kobject`, VFS, and the device model all become readable at once. Worked examples from three subsystems **[WAH]** |
| `error-handling-idioms.md` | Error Handling | Negative errno as the universal convention, `ERR_PTR`/`PTR_ERR`/`IS_ERR` and the pointer-range trick that makes them work, `goto`-based unwinding and why it is correct here rather than shameful, `__must_check` |
| `reference-counting-and-lifetime.md` | Reference Counting and Object Lifetime | `refcount_t` vs `atomic_t` and why the distinction was introduced, `kref`, get/put pairing, the ownership conventions in function names, and the use-after-free class of bug that this all exists to prevent |
| `kobjects-sysfs-and-the-object-model.md` | kobjects, ksets, and sysfs | The kernel's object model: `kobject` embedded in a real struct, `kset` grouping, `ktype` behaviour — and how sysfs is *generated* from that hierarchy rather than written. Explains why `/sys` looks the way it does **[WAH]** [Lab] |
| `memory-safety-in-kernel-c.md` | What Goes Wrong in Kernel C | The recurring bug classes as a catalogue: use-after-free, refcount leak, sleeping in atomic context, unchecked user pointer, integer overflow in a size calculation, missing `__user`. Each with a real symptom and the tool from folder 17 that catches it. Includes a note on Rust-for-Linux status at the pinned version |

---

### 05-syscalls-and-the-boundary — "System Calls" (position 6) — 10 pages

| File | Title | Brief |
|---|---|---|
| `what-a-system-call-actually-is.md` | What a System Call Actually Is | Not a function call: a deliberate, hardware-mediated privilege transition into code you do not control, at an entry point you cannot choose. Why it costs what it costs, and why that cost drives so much kernel design (vDSO, `io_uring`, batching) **[WAH]** |
| `the-entry-path.md` | The Entry Path | x86-64: `SYSCALL`, `MSR_LSTAR`, `swapgs`, the per-CPU stack switch, `entry_SYSCALL_64`, `pt_regs`. What the CPU does versus what software does. `:::note` contrasting arm64 `SVC`/`vectors`. Simplified path stated as simplified, with `<Src>` to the real thing |
| `the-syscall-table-and-dispatch.md` | The Table and the Dispatch | The syscall number as an index, `sys_call_table`, `SYSCALL_DEFINEn` macro expansion shown step by step, why the numbers are frozen forever, and where the per-architecture tables live **[Lab]** |
| `arguments-return-values-and-errno.md` | Arguments, Returns, and errno | The register ABI, the six-argument limit and what happens beyond it, negative-errno returns, where user-space `errno` actually comes from (libc, not the kernel), and `ERESTARTSYS` — how a syscall gets restarted after a signal without user space noticing **[WAH]** |
| `copying-data-across-the-boundary.md` | Copying Data Across the Boundary | Why the kernel may never dereference a user pointer directly: `copy_from_user`/`copy_to_user`, `access_ok`, the exception table that makes a faulting copy return `-EFAULT` instead of an oops, SMAP/SMEP, the `__user` annotation and sparse. The TOCTOU class this creates |
| `the-vdso.md` | The vDSO | A kernel-provided shared object mapped into every process. Why `clock_gettime` and `getpid` on some systems are not syscalls at all, the `vvar` page, and how to see the vDSO in your own process's maps **[WAH]** **[Lab]** |
| `libc-is-not-the-kernel.md` | libc Is Not the Kernel | The wrapper layer: what glibc/musl add (errno, cancellation points, argument massaging, caching), where they differ, and `syscall(2)` for going direct. Why `strace` output and your source code often disagree. `<Tabs>` glibc / musl / raw **[WAH]** |
| `abi-stability-and-compat.md` | ABI Stability and Compat | "We do not break user space" as an engineering constraint with real consequences: syscalls are never removed, flags are added not changed, structures grow via size arguments. `compat_` syscalls for 32-on-64, and the seccomp architecture trap that follows |
| `tracing-and-intercepting-syscalls.md` | Tracing and Intercepting Syscalls | How `strace` actually works (`PTRACE_SYSCALL` stops, and the overhead that implies), `perf trace` and the tracepoint path, seccomp user notification for real interception, and why `LD_PRELOAD` is not syscall interception **[WAH]** `<Cast>` |
| `lab-adding-a-syscall.md` | Lab: Add a System Call | End to end in the QEMU lab: pick a number, `SYSCALL_DEFINE`, wire the table, rebuild, boot, call it from C with `syscall()`, watch it in `strace`. The fastest way to make the whole boundary concrete **[Lab]** |

---

### 06-processes-and-threads — "Processes and Threads" (position 7) — 12 pages

| File | Title | Brief |
|---|---|---|
| `task-struct-the-anatomy-of-a-task.md` | `task_struct`: The Anatomy of a Task | The kernel's unit of scheduling. Not the 200 fields — the twelve that matter, grouped by concern (identity, state, scheduling, memory, files, signals, credentials, relationships) as a diagram, with `<Src>` to the definition. How to walk one in GDB **[Lab]** |
| `threads-are-tasks.md` | Threads Are Tasks | Linux has no separate thread object. `clone()` flags as a menu of what to share; a "thread" is a task sharing `mm`, files, and signal handlers. `tgid` vs `pid` and why `getpid()` lies relative to the kernel's naming. The consequence: what "process" means in `/proc` **[WAH]** |
| `fork-and-copy-on-write.md` | `fork()` and Copy-on-Write | What actually gets copied (very little), what gets marked read-only, and how the first write resolves. Why `fork()` of a 10 GB process is fast and why it can still fail. `vfork` and `posix_spawn` **[WAH]** **[Lab]** |
| `exec-and-binary-formats.md` | `exec()` and Binary Formats | Tearing down one address space and building another. `binfmt` handlers, ELF program headers mapped into memory, `PT_INTERP` and the dynamic linker, `#!` handling as a binfmt, `binfmt_misc`. Why `exec` never returns **[WAH]** |
| `the-process-address-space.md` | A Process's Address Space | The map a task sees: text, data, bss, heap, mmap region, stack, vDSO, and the kernel half it can never touch. Reading `/proc/PID/maps` and `smaps` line by line. Deep mechanism deferred to folder 08 **[WAH]** **[Lab]** |
| `credentials-and-identity.md` | Credentials and Identity | `struct cred`, real/effective/saved/filesystem IDs, supplementary groups, how `setuid` binaries transition, and RCU-protected credential updates. The kernel side of what folder 16 governs |
| `process-states-and-wait-queues.md` | Process States and Wait Queues | `TASK_RUNNING`, `INTERRUPTIBLE`, `UNINTERRUPTIBLE`, `KILLABLE`, stopped, traced, zombie — as a state diagram. Wait queues as the universal blocking mechanism. Why a `D`-state process cannot be killed, and what that says about the driver it is stuck in **[WAH]** |
| `exit-zombies-and-orphans.md` | Exit, Zombies, and Orphans | What `exit()` frees and what it cannot free until the parent reaps. Zombies as a bookkeeping requirement rather than a leak, reparenting to PID 1, `PR_SET_CHILD_SUBREAPER`, and why a zombie army means a buggy parent **[WAH]** |
| `signals.md` | Signals | Generation, the pending set, the delivery point on return to user space (not at send time — the misconception that matters), handler invocation via a stack frame the kernel builds, `sigreturn`, blocked and real-time signals, and why signal handlers may do almost nothing safely **[WAH]** |
| `pipes-fifos-and-unix-sockets.md` | Pipes, FIFOs, and UNIX Sockets | The IPC that processes actually use, at the kernel level: the pipe buffer as a ring of pages, `splice`, socket pairs, ancillary data and file-descriptor passing (`SCM_RIGHTS`). Links to the CS IPC page for the theory |
| `proc-as-the-process-interface.md` | `/proc` as the Process Interface | Not a filesystem of files: a set of generated views onto live kernel structures. Which `/proc/PID` entries expose which fields, how the files are produced on read, and why `cat` of some of them can block **[WAH]** |
| `lab-watching-a-process-be-born.md` | Lab: Watch a Process Be Born | `bpftrace` on `sched_process_fork`/`exec`, `perf trace`, and a GDB breakpoint in `do_fork` in the QEMU lab — the same event seen from three tools **[Lab]** `<Cast>` |

---

### 07-scheduling — "Scheduling" (position 8) — 11 pages

| File | Title | Brief |
|---|---|---|
| `what-the-scheduler-must-decide.md` | What the Scheduler Must Decide | The actual questions: who runs next on this CPU, for how long, and on which CPU at all. Why these are three separate problems with three separate mechanisms. Links to the CS scheduling page for algorithmic theory |
| `runqueues-and-scheduling-classes.md` | Runqueues and Scheduling Classes | The per-CPU `rq`, the class hierarchy (`stop` → `deadline` → `rt` → `fair` → `idle`), and `pick_next_task` walking it in priority order. The extensibility story, including `sched_ext` status at the pinned version |
| `cfs-and-vruntime.md` | CFS and Virtual Runtime | The design that ran Linux for fifteen years: virtual runtime, weight from nice, the red-black tree, `sched_latency`/`min_granularity`. Included because the vocabulary is everywhere and because understanding what CFS could not do is the setup for the next page |
| `eevdf.md` | EEVDF: The Current Fair Scheduler | Eligible Virtual Deadline First: lag, eligibility, request size, and how latency-sensitivity became a first-class input instead of a heuristic. What changed for tuning, and which older articles are now wrong. **Verify against current documentation via context7 — most material online predates this** |
| `priorities-nice-and-weights.md` | Priorities, nice, and Weights | The nice-to-weight table and its geometric ratio, what a nice level actually buys, `renice`, autogroups and the desktop behaviour they cause, and priority as it differs across scheduling classes **[WAH]** |
| `preemption-models.md` | Preemption Models | `PREEMPT_NONE`, `VOLUNTARY`, `FULL`, `RT`, and lazy preemption at the pinned version. `need_resched`, preemption counters, preemption points, and where the kernel is and is not preemptible. The latency-versus-throughput trade-off made concrete |
| `the-context-switch.md` | The Context Switch | `schedule()` → `pick_next_task` → `context_switch` → `switch_mm` → `switch_to`. What gets saved and by whom, the TLB consequences and how PCID/ASID reduce them, FPU state and lazy restore, and where the cost actually lands **[WAH]** |
| `smp-load-balancing.md` | SMP and Load Balancing | Scheduling domains and groups built from the topology (SMT, LLC, NUMA), periodic balancing versus idle balancing, wake affinity and its failure modes, migration cost. Why "my thread moved CPUs and got slower" is a cache story |
| `real-time-scheduling.md` | Real-Time Scheduling | `SCHED_FIFO`, `SCHED_RR`, `SCHED_DEADLINE` (CBS, admission control), RT throttling and the runaway-task protection it provides, priority inheritance for RT mutexes. PREEMPT_RT in one section, linking to the embedded section |
| `cgroup-cpu-control.md` | cgroup CPU Control | `cpu.weight`, `cpu.max` and quota/period throttling, `cpu.pressure`, and the group scheduling hierarchy. **The container CPU-limit trap**: why a container hitting its quota stalls in long pauses rather than running proportionally slower **[WAH]** |
| `diagnosing-scheduling-latency.md` | Diagnosing Scheduling Latency | `/proc/PID/schedstat`, `/proc/pressure/cpu`, `perf sched latency`, `runqlat` from BCC, and the scheduler tracepoints. A worked investigation from "the app is janky" to a named cause **[Lab]** `<Cast>` |

---

### 08-memory-management — "Virtual Memory and Memory Management" (position 9) — 18 pages

The largest folder, and correctly so — nearly every hard Linux question is a memory question.

| File | Title | Brief |
|---|---|---|
| `the-virtual-address-space.md` | The Virtual Address Space | The x86-64 layout: canonical addresses and the hole, the user/kernel split, the direct map, vmalloc space, and KASLR's effect on all of it. Why 64-bit addresses are not 64 bits, and 5-level paging |
| `page-tables-and-the-walk.md` | Page Tables and the Walk | Four (and five) levels, the walk from `CR3` to a physical address worked through with real numbers, PTE bits as a WaveDrom register strip (present, writable, user, NX, accessed, dirty), huge-page entries at intermediate levels. Links to the CS hardware page **[Lab]** |
| `tlb-and-address-space-switching.md` | The TLB and Address-Space Switching | Why translation is cached, what a miss costs, page-walk caches, PCID/ASID tagging, `switch_mm`, and TLB shootdown as an IPI-driven cross-CPU operation with a measurable price. KPTI's cost lands here |
| `mm-struct-and-vmas.md` | `mm_struct` and VMAs | The kernel's description of an address space: `mm_struct`, the VMA tree (maple tree at the pinned version, replacing the rbtree — say which), VMA flags, merging and splitting on `mmap`/`munmap`/`mprotect`. `/proc/PID/maps` as a rendering of this structure **[WAH]** |
| `the-page-fault-handler.md` | The Page Fault Handler | From the CPU exception to `do_page_fault`, VMA lookup, the fault classification tree (anon/file/swap/COW/protection/invalid), PTE installation, and return. Where a SIGSEGV is decided. The single most important code path in the folder **[Lab]** |
| `demand-paging-and-cow.md` | Demand Paging and Copy-on-Write | Nothing is allocated until touched. The zero page, first-touch allocation, COW after `fork`, and why `malloc` of 100 GB succeeds on a machine with 8 GB. Overcommit modes and what each actually does **[WAH]** |
| `the-page-allocator.md` | The Page Allocator | Zones and why they exist, the buddy allocator with orders and splitting/coalescing, GFP flags as a WaveDrom strip with a semantics table (`GFP_KERNEL` vs `GFP_ATOMIC` vs `GFP_NOFS` and the deadlocks each avoids), watermarks, fragmentation and compaction |
| `slab-slub-and-kmalloc.md` | Slab, SLUB, and `kmalloc` | Object caching above the page allocator: why, per-CPU freelists, `kmem_cache_create` for your own objects, `kmalloc` size classes and the rounding waste, `/proc/slabinfo` and `slabtop`. Finding a slab leak **[Lab]** |
| `vmalloc-and-choosing-an-allocator.md` | `vmalloc` and Choosing an Allocator | Virtually contiguous versus physically contiguous, when each is required (DMA needs physical), the cost of `vmalloc`, and a decision table across `kmalloc`/`kzalloc`/`vmalloc`/`alloc_pages`/`kmem_cache`/`devm_*` |
| `folios-and-compound-pages.md` | Folios and Compound Pages | Why `struct page` was too small a unit, what a folio is, compound pages and head/tail, the ongoing conversion, and how to read code written on either side of it. **Verify status via context7 — this is actively changing** |
| `the-page-cache.md` | The Page Cache | Where file data lives. The address space object, indexing by file offset, how `read()` and `mmap()` both land here, readahead heuristics, and cache hits versus misses. Why the second `grep` of a file is instant **[WAH]** **[Lab]** |
| `writeback-and-fsync.md` | Writeback, Dirty Pages, and `fsync` | Dirty tracking, `dirty_ratio`/`dirty_background_ratio`, the writeback threads and per-BDI throttling, and exactly what `fsync`/`fdatasync`/`sync` guarantee — including the barrier that must reach the device. Data loss after a power cut, explained **[WAH]** |
| `reclaim-lru-and-kswapd.md` | Reclaim, LRU, and kswapd | Active/inactive lists and the second-chance promotion, MGLRU at the pinned version, `kswapd` versus direct reclaim and why direct reclaim is a latency event, shrinkers for non-page caches (dentry, inode) |
| `swap-and-zswap.md` | Swap, zswap, and zram | What swapping actually is, swap entries in PTEs, refaults, `swappiness` and what it really weighs, zswap and zram as compression tiers. Why "disable swap for performance" is usually wrong **[WAH]** |
| `the-oom-killer.md` | The OOM Killer | When reclaim fails: `oom_score` and `oom_score_adj`, the selection heuristic, memcg-scoped OOM versus global, the OOM report in `dmesg` read field by field, and userspace killers (`systemd-oomd`, `earlyoom`). Why your process "died for no reason" **[WAH]** **[Lab]** |
| `hugepages-and-thp.md` | Huge Pages and THP | 2 MB and 1 GB pages, TLB reach as the actual benefit, explicit hugetlbfs versus transparent huge pages, `khugepaged`, and THP's latency cost — the reason databases routinely disable it **[WAH]** |
| `numa-and-memory-policy.md` | NUMA and Memory Policy | Nodes and distance, default local allocation, `mbind`/`set_mempolicy`, automatic NUMA balancing, `numactl` and `numastat`. When NUMA effects are the answer and when they are a red herring |
| `what-free-and-rss-really-say.md` | What `free` and RSS Really Tell You | The measurement page. Buffers versus cache versus available, why `free` output confuses everyone, RSS versus PSS versus USS versus VSZ, shared page double-counting, `smaps_rollup`, and cgroup `memory.current`. **How to actually answer "how much memory is this using"** **[WAH]** **[Lab]** |

---

### 09-concurrency-and-locking — "Concurrency and Locking" (position 10) — 13 pages

| File | Title | Brief |
|---|---|---|
| `why-kernel-concurrency-is-different.md` | Why Kernel Concurrency Is Different | Four independent sources of concurrency — SMP, preemption, interrupts, and softirqs — and the fact that some contexts may not sleep. The context matrix (process/softirq/hardirq/NMI) that determines every locking choice in the folder |
| `memory-ordering-and-barriers.md` | Memory Ordering and Barriers | The kernel's memory model in practice: `READ_ONCE`/`WRITE_ONCE` and why plain accesses are not safe, compiler barriers versus CPU barriers, `smp_mb`/`smp_rmb`/`smp_wmb`, acquire/release, and the store-buffer example worked out. The x86-TSO versus arm64-weak contrast is load-bearing here, not decorative. Links to the CS backfill page |
| `atomics-and-refcounts.md` | Atomic Operations | `atomic_t`, the operation families and which return values, `cmpxchg`, and the ordering guarantees each atomic does and does not carry. `refcount_t`'s saturation semantics and why it exists separately |
| `spinlocks.md` | Spinlocks | Busy-waiting and when that is right, the queued spinlock implementation, `spin_lock_irqsave` and the interrupt-deadlock it prevents, `spin_lock_bh`, and the absolute rule against sleeping while holding one **[WAH]** |
| `mutexes-and-semaphores.md` | Mutexes and Semaphores | Sleeping locks, optimistic spinning (a mutex spins first — the "mutexes are slow" misconception), owner tracking, `mutex_lock_interruptible`, and why semaphores are now rare |
| `rwlocks-and-rwsems.md` | Reader-Writer Locks | Reader/writer semantics, writer starvation, why rwlocks are often slower than a plain lock due to cacheline contention, and where `rw_semaphore` is genuinely the right answer (`mmap_lock`) |
| `seqlocks.md` | Seqlocks | Lockless readers with a retry loop, the write-side sequence counter, the constraints on readers (no pointers escaping, retry-safe), and the canonical use in timekeeping |
| `rcu-the-idea.md` | RCU: The Idea | Read-Copy-Update from first principles: readers that take no locks and pay nothing, writers that publish a new version and defer reclamation until every pre-existing reader has finished. Grace periods and quiescent states, drawn as a WaveDrom timeline. **The conceptual centrepiece of the folder** |
| `rcu-in-practice.md` | RCU in Practice | `rcu_read_lock`/`unlock`, `rcu_dereference`/`rcu_assign_pointer` and the ordering they encode, `synchronize_rcu` versus `call_rcu` versus `kfree_rcu`, RCU-protected lists, SRCU for sleepable readers, and the rules that make RCU misuse silently fatal **[Lab]** |
| `per-cpu-data.md` | Per-CPU Data | Eliminating sharing rather than protecting it. `DEFINE_PER_CPU`, `this_cpu_*` operations, `get_cpu`/`put_cpu` and preemption, local locks under PREEMPT_RT, and per-CPU counters for hot statistics. Cache-line effects tie back to the CS MESI page |
| `lock-free-and-ring-buffers.md` | Lock-Free Patterns | Where lock-free is genuinely used: single-producer/single-consumer rings, the kernel's `kfifo`, the BPF ring buffer, and the memory barriers that make them correct. An honest account of why most kernel code should use a lock instead |
| `choosing-a-lock.md` | Choosing a Lock | The decision table: context, expected hold time, read/write ratio, contention, sleep requirement. Worked selections for six real scenarios, and the cost hierarchy from uncontended atomic to cross-NUMA cacheline ping-pong |
| `finding-locking-bugs.md` | Finding Locking Bugs | `lockdep` — what it proves, how to read its report, and why it catches deadlocks that never happened. KCSAN for data races, `CONFIG_DEBUG_ATOMIC_SLEEP` for sleeping-in-atomic, ABBA ordering, and a worked lockdep splat read line by line **[Lab]** |

---

### 10-interrupts-time-and-deferred-work — "Interrupts, Time, and Deferred Work" (position 11) — 12 pages

| File | Title | Brief |
|---|---|---|
| `how-an-interrupt-reaches-the-kernel.md` | How an Interrupt Reaches the Kernel | Device → interrupt controller → CPU vector → IDT entry → kernel entry stub → handler. Links to the CS interrupt-controller backfill page for the hardware; owns the software path. `:::note` for arm64/GIC |
| `the-irq-subsystem.md` | The IRQ Subsystem | `irq_desc`, irq chips and the abstraction over controllers, irq domains and hardware-to-Linux IRQ number mapping, `request_irq` and its flags, shared interrupts and the return-value contract, spurious interrupt detection **[WAH]** |
| `hardirq-context.md` | Hard IRQ Context and Its Rules | What a handler may not do — sleep, allocate with `GFP_KERNEL`, take a mutex, touch user memory — and why each rule follows from the context. The pressure this creates is the entire reason the rest of the folder exists |
| `softirqs.md` | Softirqs | The fixed set and why it is fixed, `raise_softirq`, execution on interrupt return and in `ksoftirqd`, the loop budget that prevents starvation, and softirq CPU time showing up as `si` in `top` **[WAH]** |
| `tasklets-and-their-replacement.md` | Tasklets, and Why They Are Going Away | The tasklet model, its serialisation guarantee, the problems that make it deprecated, and the recommended replacements (workqueue or threaded IRQ). Included because tasklets are still all over `drivers/` and readers will meet them |
| `workqueues.md` | Workqueues | Deferred work in *process* context, so it may sleep. Concurrency-managed workqueues, per-CPU versus unbound, `WQ_*` flags, delayed work, flushing and cancellation, and the cancel-versus-free lifetime bug **[Lab]** |
| `threaded-irqs.md` | Threaded IRQs | `request_threaded_irq`, the quick primary handler plus a schedulable thread, why PREEMPT_RT makes nearly every handler threaded, and the priority and latency consequences |
| `interrupt-affinity-and-balancing.md` | Interrupt Affinity | `/proc/interrupts` read column by column, `smp_affinity`, `irqbalance` and when to turn it off, MSI-X vectors per queue on modern NICs and NVMe, and why pinning interrupts near their consumer matters **[WAH]** **[Lab]** |
| `timekeeping-and-clocksources.md` | Timekeeping and Clocksources | Clocksources (TSC, HPET, ACPI PM), how one is selected and why the TSC needed so many workarounds, `CLOCK_MONOTONIC` versus `CLOCK_REALTIME` versus `BOOTTIME`, leap seconds, and the seqlock-protected read path from `clock_gettime` down **[WAH]** |
| `the-tick-and-nohz.md` | The Tick, and Living Without It | Clock event devices, the periodic tick and `HZ`, dynticks-idle and full dynticks (`nohz_full`), and what the tick was doing that must now happen elsewhere. CPU isolation for latency-sensitive workloads |
| `timers-and-hrtimers.md` | Timers and High-Resolution Timers | The timer wheel and its deliberate imprecision, `hrtimer` on a red-black tree with real deadlines, timer slack and power, and which API a driver should choose |
| `delays-and-sleeps.md` | Delays and Sleeps: What They Really Do | `udelay`/`ndelay` busy-waiting, `msleep` and its actual granularity, `usleep_range` and why it takes a range, `schedule_timeout`, and the guarantee every one of them lacks: **none of them sleeps for exactly the time you asked** **[WAH]** |

---

### 11-vfs-and-filesystems — "VFS and Filesystems" (position 12) — 13 pages

| File | Title | Brief |
|---|---|---|
| `why-vfs-exists.md` | Why the VFS Exists | One `read()` over thirty filesystems: the indirection layer and the object-oriented C that implements it. What a filesystem must supply to participate. "Everything is a file" restated precisely as "everything is a file *descriptor*" **[WAH]** |
| `the-four-objects.md` | Superblock, Inode, Dentry, File | The four core objects and the relationships between them, drawn once and referenced for the rest of the folder. What each caches, what each pins, and the operations tables (`*_operations`) that make them polymorphic |
| `path-lookup-and-the-dcache.md` | Path Lookup and the Dentry Cache | Resolving `/usr/lib/libc.so.6` component by component: `nameidata`, RCU-walk versus ref-walk and the fallback, negative dentries and why they are a feature, symlink and mount-point traversal, `..` handling. Why the dcache is one of the hottest structures in the kernel **[WAH]** |
| `open-read-write-in-the-kernel.md` | `open`, `read`, `write` in the Kernel | The full path: fd table → `struct file` → `f_op->read_iter` → page cache → filesystem → block layer. What an fd is (an index, not a handle), fd sharing across `fork` and `dup`, `O_APPEND` atomicity, and where `O_DIRECT` leaves this path **[WAH]** |
| `mounts-and-mount-namespaces.md` | Mounts and Mount Namespaces | The mount tree as distinct from the directory tree, `vfsmount` versus `struct mount`, bind mounts, mount propagation (shared/slave/private/unbindable) and why containers depend on getting it right, `/proc/self/mountinfo` **[WAH]** **[Lab]** |
| `ext4.md` | ext4 | Block groups, inodes and the extent tree, htree directory indexing, delayed allocation, and the jbd2 journal with `data=ordered` versus `writeback`. The default filesystem, read from the on-disk layout upward **[Lab]** |
| `xfs-and-btrfs.md` | XFS and Btrfs | Two different bets: XFS's allocation groups, B+ trees, and parallelism versus Btrfs's copy-on-write, snapshots, checksums, and its RAID caveats. When each is the right choice, without advocacy `<Tabs>` |
| `journaling-and-crash-consistency.md` | Journaling and Crash Consistency | What survives a power cut and what does not. Metadata versus data journalling, ordering guarantees, write barriers and `FUA`, and the durability contract an application actually gets. Links to the CS backfill theory page **[WAH]** |
| `tmpfs-and-memory-filesystems.md` | tmpfs and Memory-Backed Filesystems | A filesystem that is page cache with no backing store: swappable, size-limited, and why `/tmp`, `/dev/shm`, and `/run` use it. `ramfs` and its missing safety limit |
| `procfs-sysfs-debugfs-configfs.md` | procfs, sysfs, debugfs, configfs | Four pseudo-filesystems with four different contracts: `/proc` for process and legacy kernel state, `/sys` generated from the device model with one-value-per-file, `/debug` with no stability promise at all, `/config` for object creation. Which to use when writing a driver, and the ABI rules for each **[WAH]** |
| `overlayfs.md` | overlayfs | Lower, upper, and work directories; the merged view; copy-up on write; whiteouts for deletion. The mechanism behind container image layers, which folder 15 builds on **[Lab]** |
| `fuse-and-userspace-filesystems.md` | FUSE | Moving a filesystem to user space: the request protocol over `/dev/fuse`, the performance cost of the extra boundary crossings, and when it is worth paying. Where FUSE shows up in practice (sshfs, gocryptfs, container tooling) |
| `lab-a-minimal-filesystem.md` | Lab: A Filesystem in 200 Lines | An in-memory filesystem module registered with the VFS: `file_system_type`, superblock fill, one directory, one file, `read_iter`. Mount it in the QEMU lab. Makes the VFS contract concrete in a way no diagram can **[Lab]** |

---

### 12-block-layer-and-storage — "The Block Layer and I/O" (position 13) — 11 pages

| File | Title | Brief |
|---|---|---|
| `the-block-layer-map.md` | The Storage Stack, Mapped | The whole path from `write()` to the platter or the flash die, as one reference diagram (the Thomas-Krenn CC BY-SA figure, plus a Mermaid simplification for the parts this folder covers). The map for the rest of the folder |
| `block-devices-and-gendisk.md` | Block Devices and `gendisk` | What makes a device a block device, `gendisk` and partitions, major/minor numbers, `/dev` entries and how udev creates them, `/sys/block` attributes worth knowing (`queue/scheduler`, `rotational`, `nr_requests`) |
| `the-bio.md` | The `bio` | The unit of block I/O: segments of pages, direction, target sector, completion callback. Splitting, chaining, and merging. How a page-cache writeback becomes a `bio`, drawn end to end |
| `blk-mq.md` | blk-mq: Multi-Queue Block I/O | Why the single request queue collapsed on NVMe, software queues per CPU and hardware queues per device, tag allocation, and the completion path back through an interrupt to the waiting task **[WAH]** |
| `io-schedulers.md` | I/O Schedulers | `none`, `mq-deadline`, `bfq`, `kyber` — what each optimises and the workload each suits. Why `none` is right for NVMe and wrong for a shared spinning disk. Switching one at runtime and measuring the difference **[Lab]** |
| `buffered-direct-and-alignment.md` | Buffered I/O, `O_DIRECT`, and Alignment | Three paths to a device: through the page cache, around it, and mapped. `O_DIRECT` alignment requirements, the semantics it does not give you, `O_SYNC` versus `fsync`, and why databases choose what they choose **[WAH]** |
| `io-uring.md` | `io_uring` | Shared submission and completion rings, batching syscalls to nearly zero, fixed buffers and files, polling modes, and the security history that made it controversial. Compared with `epoll` and POSIX AIO. **Verify API via context7 — it changes fast** `<Tabs>` |
| `device-mapper-and-lvm.md` | Device Mapper and LVM | Stacking virtual block devices: linear, snapshot, thin, crypt, cache. LVM as a user-space manager over dm. Reading a live dm table, and how `dm-crypt` places encryption in the stack **[Lab]** |
| `software-raid.md` | Software RAID (md) | md personalities, resync and rebuild, the write hole and the journal/bitmap that mitigate it, monitoring a degraded array. Links to the CS backfill page for RAID theory |
| `nvme-in-the-kernel.md` | NVMe in the Kernel | Submission and completion queues mapped to blk-mq, doorbells, MSI-X per queue, polled I/O for the lowest latency, namespaces, and NVMe-oF in one paragraph. Links to the CS NVMe page for the protocol |
| `diagnosing-io-problems.md` | Diagnosing I/O Problems | `iostat` field by field, `%util` and why it is meaningless on NVMe, `blktrace`/`blkparse`, `biolatency` and `biosnoop`, `/proc/pressure/io`. **The `iowait` misconception**, and a worked investigation from "the disk is slow" to a named cause **[WAH]** **[Lab]** `<Cast>` |

---

### 13-networking-stack — "The Networking Stack" (position 14) — 12 pages

Protocol semantics are owned by `computer-science/computer-networks/`. This folder owns the kernel's
datapath and control planes.

| File | Title | Brief |
|---|---|---|
| `the-network-stack-map.md` | The Network Stack, Mapped | Socket layer → protocol → IP → netfilter hooks → routing → device layer → driver → NIC, in both directions, as the reference diagram for the folder. Where every later page fits |
| `sk-buff.md` | `sk_buff`: The Packet Container | The structure every packet lives in: head/data/tail/end and the headroom that makes header pushing cheap, the header pointers, cloning versus copying, fragments and `skb_shinfo`. WaveDrom layout diagram. The struct you must know to read any networking code |
| `sockets-in-the-kernel.md` | Sockets in the Kernel | `struct socket` versus `struct sock`, address families and the `proto_ops` dispatch, socket buffers and their accounting limits, the blocking and wakeup path, and how `epoll` hooks into it. Links to the CS backfill socket-API page **[WAH]** |
| `the-receive-path.md` | The Receive Path | Wire → DMA into an RX ring → interrupt → NAPI polling and why polling replaced per-packet interrupts → GRO coalescing → protocol handler → socket queue → waking the reader. RPS/RFS steering, and where drops are counted **[WAH]** |
| `the-transmit-path.md` | The Transmit Path | `send()` → socket buffer → TCP segmentation (and TSO/GSO offload) → routing decision → neighbour resolution → qdisc → driver `ndo_start_xmit` → DMA → completion. Byte queue limits and bufferbloat |
| `tcp-in-the-kernel.md` | TCP in the Kernel | The state machine as implemented, send and receive buffer autotuning, the retransmission and RTO machinery, pluggable congestion control (cubic, BBR — verify BBR version via context7), TFO, and the socket options that actually matter |
| `netfilter-and-nftables.md` | netfilter and nftables | The five hooks and the packet's path through them, tables/chains/rules, iptables versus nftables and the compatibility layer, and where the hooks sit relative to routing. The diagram everyone eventually needs `<Tabs>` |
| `connection-tracking-and-nat.md` | Connection Tracking and NAT | conntrack as the state that makes stateful firewalling and NAT possible, tuple matching, helpers, table size and the `nf_conntrack: table full` failure, and how DNAT/SNAT/masquerade are implemented over it. Links to CS backfill **[WAH]** |
| `routing-and-neighbours.md` | Routing and Neighbours | The FIB, route lookup and caching, multiple tables with policy routing rules, the neighbour (ARP/NDP) table and its states, and reading `ip route get` as a debugging tool **[Lab]** |
| `network-namespaces-and-virtual-devices.md` | Network Namespaces and Virtual Devices | netns as a complete, independent stack; veth pairs, bridges, macvlan/ipvlan, VLAN and tunnel devices. Building a two-namespace network by hand — the exact mechanism container runtimes automate **[Lab]** |
| `traffic-control.md` | Traffic Control and qdiscs | The qdisc layer, classless (fq_codel, cake) versus classful (htb), where shaping and policing differ, and how bufferbloat gets fixed. Ingress and `tc` filters as the attach point folder 18 uses |
| `diagnosing-network-problems.md` | Diagnosing Network Problems | `ss` in place of `netstat`, `/proc/net/*` as the source, `ethtool -S` counters, `tcpdump` and where in the stack it taps (and therefore what it cannot see), `dropwatch`, `nstat`. A worked investigation from "connections hang" to a named cause **[WAH]** **[Lab]** `<Cast>` |

---

### 14-device-drivers-and-hardware — "Device Drivers" (position 15) — 13 pages

| File | Title | Brief |
|---|---|---|
| `the-linux-device-model.md` | The Linux Device Model | Buses, devices, drivers, classes — and the matching that binds them. `probe` and `remove` as the driver lifecycle, deferred probe and why it exists, and how the whole thing surfaces as `/sys`. Builds directly on the kobject page in folder 04 **[WAH]** |
| `platform-devices-and-description.md` | Platform Devices, Device Tree, and ACPI | Devices that cannot be enumerated must be described. Device tree on embedded and arm64, ACPI on x86-64, and platform devices as the driver-side abstraction over both. Links to the embedded section for device-tree depth `<Tabs>` |
| `pci-and-pcie-drivers.md` | PCI and PCIe Drivers | Enumeration and the ID table, config space, BARs and resource assignment, `pci_enable_device`/`pci_iomap`, bus mastering, and reading `lspci -vvv` against the driver's own code. Links to the CS backfill PCIe page **[Lab]** |
| `mmio-and-port-io.md` | MMIO, `ioremap`, and Accessors | Why a driver may never dereference a device pointer: `ioremap`, `readl`/`writel` and their ordering guarantees, `__iomem` and sparse, relaxed accessors, memory barriers around device access, and port I/O as an x86 legacy **[WAH]** |
| `the-dma-api.md` | The DMA API | Device-visible addresses versus physical versus virtual, coherent versus streaming mappings, `dma_map_single`/`dma_map_sg` and the ownership handoff, sync operations, bounce buffers, `dma_set_mask`, and IOMMU involvement. The bug class: touching a buffer the device owns. Links to CS backfill |
| `interrupts-in-drivers.md` | Interrupts in a Driver | Requesting a line, MSI and MSI-X allocation, the `IRQ_HANDLED`/`IRQ_NONE` contract on shared lines, splitting work into a threaded handler, and per-queue interrupts on multi-queue devices. Applies folder 10 to real drivers |
| `character-devices.md` | Character Devices | `cdev`, major/minor allocation, `file_operations`, the misc-device shortcut, and `/dev` node creation via udev. The simplest complete driver shape |
| `lab-a-character-driver.md` | Lab: Write a Character Driver | A complete out-of-tree module: build against kernel headers, register a misc device, implement `open`/`read`/`write`/`ioctl`, load it in the QEMU lab, exercise it from C, watch it in `ftrace`, unload it cleanly **[Lab]** `<Cast>` |
| `talking-to-user-space.md` | Talking to User Space | The interface menu and how to choose: `ioctl` (and its versioning discipline), sysfs attributes (one value per file), debugfs, netlink, character-device `read`/`poll`, `mmap`, and uio/vfio for user-space drivers. The design decision most new drivers get wrong **[WAH]** |
| `block-and-network-driver-shapes.md` | Block and Network Driver Shapes | How block and network drivers differ structurally from character drivers: blk-mq `queue_rq` for one, `net_device_ops` plus NAPI for the other. Enough to read either, cross-linking folders 12 and 13 |
| `firmware-udev-and-hotplug.md` | Firmware, udev, and Hotplug | `request_firmware` and where firmware files come from, uevents as the kernel→user-space notification channel, udev rules and device naming (including predictable network interface names), and the coldplug/hotplug distinction **[WAH]** |
| `power-management.md` | Power Management | System suspend states (s2idle, S3, hibernate) and the freeze/suspend/resume callback sequence, runtime PM with its reference counts and autosuspend, wakeup sources, and why a laptop fails to sleep — with the diagnostic path **[WAH]** |
| `debugging-drivers.md` | Debugging Drivers | `pr_debug` and dynamic debug, `ftrace function_graph` scoped to a module, tracing a probe that never fires, `/sys/kernel/debug`, reading an oops back to a driver line, and the top five driver bug patterns from folder 04's catalogue **[Lab]** |

---

### 15-containers-and-virtualization — "Containers and Virtualization" (position 16) — 12 pages

| File | Title | Brief |
|---|---|---|
| `what-a-container-actually-is.md` | What a Container Actually Is | There is no container object in the kernel. A container is a process with namespaces, a cgroup, a root filesystem, a capability set, and a seccomp filter — assembled by user space. The single most valuable page in the folder **[WAH]** |
| `namespaces-overview.md` | Namespaces | All eight (mount, PID, network, IPC, UTS, user, cgroup, time), what each virtualises, how `clone`/`unshare`/`setns` create and join them, and `/proc/PID/ns` as the handle. WaveDrom of the `CLONE_NEW*` flag bits **[Lab]** |
| `mount-and-pid-namespaces.md` | Mount and PID Namespaces | The two with the most surprising semantics. Mount propagation revisited from the container angle; PID namespaces nesting, PID 1's special duties inside one, and why a container's init must reap orphans — the zombie problem containers rediscovered **[WAH]** |
| `user-namespaces.md` | User Namespaces | UID/GID mapping, why root inside is not root outside, `/proc/PID/uid_map` and the write-once rule, capabilities scoped to a namespace, and how rootless containers become possible. The attack-surface trade-off, stated honestly |
| `cgroup-v2-architecture.md` | cgroup v2 | The unified hierarchy after v1's multiple ones, the no-internal-process rule, controller enable/disable down the tree, delegation to unprivileged users, and how systemd owns the hierarchy on a modern distribution **[WAH]** |
| `cgroup-controllers-in-practice.md` | cgroup Controllers in Practice | `cpu`, `memory`, `io`, `pids`, `cpuset` — the interface files that matter and what each actually enforces. `memory.high` versus `memory.max`, `io.latency` versus `io.max`, and PSI (`*.pressure`) as the best overload signal Linux has **[Lab]** |
| `capabilities-in-containers.md` | Capabilities and Container Privilege | The default drop set, `--privileged` and exactly what it turns off, `no_new_privs`, and the specific capabilities that are equivalent to root (`CAP_SYS_ADMIN`, `CAP_SYS_MODULE`, `CAP_BPF`). Links to folder 16 for the model **[WAH]** |
| `building-a-container-from-scratch.md` | Lab: Build a Container from Scratch | ~150 lines of C plus shell: `clone` with namespace flags, `pivot_root` onto an extracted rootfs, mount `/proc`, create a cgroup and set a limit, drop capabilities, apply a seccomp filter, set up a veth pair, then `exec`. The payoff page of the folder **[Lab]** |
| `images-layers-and-oci.md` | Images, Layers, and the OCI Runtime | Image layers as overlayfs lowerdirs, the OCI image and runtime specifications, what `runc` does when handed a bundle, and where containerd/Docker/Podman sit above it. Links back to the overlayfs page |
| `container-networking.md` | Container Networking | Bridge-and-NAT as the default model, built by hand: netns, veth, bridge, iptables/nftables masquerade rules, port publishing. CNI in one section, and why cross-host networking needs an overlay **[Lab]** |
| `kvm-and-hardware-virtualization.md` | KVM | The kernel as a hypervisor: `/dev/kvm`, VM and vCPU file descriptors, the ioctl-driven run loop, VM exits and what causes them, EPT/NPT for guest memory, and where QEMU fits. Links to the CS backfill hardware-virtualization page **[WAH]** |
| `virtio-and-paravirtualization.md` | virtio and Paravirtual Devices | Why emulating real hardware is slow, virtqueues as the shared-memory transport, virtio-net/blk/fs, and vhost moving the datapath into the kernel. Ties directly back to the QEMU flags folder 01 uses |

---

### 16-security — "The Security Model" (position 17) — 12 pages

Defensive throughout. Attack classes are explained so readers can recognise, mitigate, and patch
them; no working exploits, no step-by-step exploitation procedures.

| File | Title | Brief |
|---|---|---|
| `the-unix-permission-model.md` | The UNIX Permission Model | Mode bits and the owner/group/other check order, directory permissions and what `x` on a directory really controls, setuid/setgid/sticky, umask, and POSIX ACLs. The model everything else layers on **[WAH]** |
| `credentials-in-the-kernel.md` | Credentials in the Kernel | `struct cred` in detail: real, effective, saved, and filesystem IDs; how `setuid`/`seteuid` transitions work and the classic privilege-drop mistakes; RCU-protected credential replacement. The kernel counterpart to folder 06's page |
| `capabilities.md` | Capabilities | Splitting root into ~40 pieces. Permitted/effective/inheritable/bounding/ambient sets and the transition rules, file capabilities as a setuid replacement, and the honest assessment: several capabilities are root-equivalent in practice **[WAH]** |
| `the-lsm-framework.md` | The LSM Framework | Hooks placed at every security-relevant decision, the "restrict only, never grant" rule, module stacking, and how a policy decision reaches a hook. The architecture that makes the next three pages possible |
| `selinux.md` | SELinux | Type enforcement, contexts and labels, policy and booleans, enforcing versus permissive, and the practical skill: reading an AVC denial and deciding whether to relabel, set a boolean, or write policy **[WAH]** **[Lab]** |
| `apparmor.md` | AppArmor | Path-based profiles as the contrasting design, profile syntax, complain versus enforce mode, and an honest comparison with SELinux on expressiveness versus approachability `<Tabs>` |
| `seccomp.md` | seccomp and Syscall Filtering | Strict mode, seccomp-BPF filters and the architecture check that must come first, `no_new_privs`, user notification for supervised syscalls, and how container runtimes generate their default profiles **[Lab]** |
| `keyrings.md` | Keyrings | Kernel-managed secrets: key types, keyring hierarchy and search order, per-process/session/user keyrings, and the users that matter — dm-crypt, NFS/Kerberos, module signing |
| `integrity-and-signing.md` | Integrity: IMA, EVM, and Module Signing | Measurement versus appraisal, the IMA policy language, EVM for metadata, module signature enforcement, and how these chain to the Secure Boot page in folder 03 |
| `kernel-hardening.md` | Kernel Hardening | The mitigations and what each defeats: KASLR, SMEP/SMAP, KPTI, stack protector, `CONFIG_FORTIFY_SOURCE`, `slab_nomerge`, lockdown mode, `kernel.dmesg_restrict`/`kptr_restrict`. Performance cost stated for each **[WAH]** |
| `vulnerability-classes.md` | Vulnerability Classes in the Kernel | The recurring shapes: use-after-free, refcount overflow, TOCTOU on user pointers, integer overflow in size arithmetic, uninitialised stack disclosure, and the transient-execution family (Spectre/Meltdown/MDS) with the mitigation each requires. Written for recognition and defence, with links to folder 17's sanitizers |
| `auditing-and-security-observability.md` | Auditing and Security Observability | The audit subsystem and rules, where audit records come from, `ausearch`, LSM audit output, and BPF-LSM as the modern hook for security tooling. What to log and what it costs |

---

### 17-observability-and-debugging — "Observability and Debugging" (position 18) — 12 pages

| File | Title | Brief |
|---|---|---|
| `what-to-measure-first.md` | What to Measure First | Method before tools: USE, RED, and the latency-versus-utilisation distinction. Why "check CPU, memory, disk, network" is not a method, and a checklist that actually narrows a problem **[WAH]** |
| `proc-and-sys-as-the-interface.md` | `/proc` and `/sys` as the Primary Interface | Almost every tool is a `/proc` parser. The files worth knowing by heart, the stability contract for each, and the `sysctl` interface for the knobs. Reading `/proc/stat` and deriving what `top` shows **[WAH]** |
| `classic-tools-and-what-they-read.md` | The Classic Tools, and What They Actually Read | `top`, `ps`, `vmstat`, `free`, `iostat`, `mpstat`, `ss`, `uptime` — each mapped to its `/proc` source and its sampling behaviour. **Load average explained correctly** (it counts uninterruptible sleepers, so it is not CPU utilisation), and `%CPU` sampling artefacts **[WAH]** |
| `printk-dmesg-and-dynamic-debug.md` | printk, dmesg, and Dynamic Debug | Log levels and the console threshold, the ring buffer and rate limiting, `pr_debug` compiled in but off by default, and enabling debug output per-file/per-line at runtime through `/sys/kernel/debug/dynamic_debug` **[Lab]** |
| `reading-an-oops.md` | Reading an Oops or a Panic | An oops decoded line by line: the fault address, `RIP` and the symbol, the register dump, the call trace and how to read frames, taint flags and what each letter means, `decode_stacktrace.sh`, and oops versus panic. **The highest-value diagnostic skill in the folder** **[Lab]** |
| `kdump-and-crash.md` | kdump and Crash Analysis | `kexec` into a capture kernel, what a `vmcore` contains, and driving the `crash` utility: backtrace, task list, memory inspection, log recovery. When a crash dump is the only option left |
| `gdb-on-the-kernel.md` | GDB on the Kernel | The QEMU `-s -S` workflow taken further: the in-tree `scripts/gdb` helpers, walking real structures live, breaking in an interrupt handler and what is safe there, kgdb and kdb on real hardware **[Lab]** `<Cast>` |
| `ftrace.md` | ftrace | tracefs by hand before any wrapper: `function` and `function_graph` tracers, static tracepoint events with filters, per-process tracing, the trace buffer and its overhead, and `trace-cmd`/KernelShark for the ergonomic version **[Lab]** `<Cast>` |
| `perf.md` | perf | Hardware and software events, `perf stat` for counters, `perf record`/`report` for sampling, call-graph collection modes (fp versus dwarf versus LBR) and their trade-offs, `perf top`, and generating a flamegraph and reading it correctly **[Lab]** `<Cast>` |
| `kprobes-uprobes-and-tracepoints.md` | Tracepoints, kprobes, and uprobes | Three instrumentation mechanisms and their trade-offs: static tracepoints with a stability contract, kprobes patching any address at real cost, uprobes reaching into user space. What each can see, and which to reach for **[WAH]** |
| `sanitizers-and-debug-configs.md` | Sanitizers and Debug Configs | KASAN, KFENCE, UBSAN, KMSAN, KCSAN, `DEBUG_OBJECTS`, `PROVE_LOCKING` — what each catches, its overhead, and the recommended lab config. Reading a KASAN report to the offending line **[Lab]** |
| `a-debugging-workflow.md` | A Systematic Debugging Workflow | The method: reproduce, bisect the layer, instrument, form a falsifiable hypothesis, test it. `git bisect` on the kernel itself. A worked case from a vague symptom to a root cause, using four tools from this folder in sequence **[WAH]** |

---

### 18-tracing-and-ebpf — "eBPF" (position 19) — 12 pages

| File | Title | Brief |
|---|---|---|
| `why-ebpf-exists.md` | Why eBPF Exists | Safe, verified, JIT-compiled programs running in kernel context, attached to almost anything. The problem it solves — asking a new question of a running production kernel without a module, a reboot, or a crash **[WAH]** |
| `the-bpf-virtual-machine.md` | The BPF Virtual Machine | The instruction set, eleven registers and their calling convention, the 512-byte stack, helper functions as the only way to reach kernel services, and JIT compilation. WaveDrom of the instruction encoding |
| `the-verifier.md` | The Verifier | Why your program was rejected. Path exploration, register state and bounded values, pointer type tracking, loop handling (bounded loops at the pinned version), and reading a verifier log to the actual problem. **The page every eBPF beginner needs and cannot find** **[WAH]** |
| `maps.md` | Maps | The state and communication mechanism: hash, array, per-CPU variants, LRU, stack-trace maps, ring buffer (and the perf buffer it replaced). Lookup semantics, atomicity, sizing, and pinning to bpffs |
| `program-types-and-attach-points.md` | Program Types and Attach Points | The taxonomy: kprobe/kretprobe, tracepoint, raw tracepoint, fentry/fexit, perf event, XDP, tc, cgroup, socket, LSM. What context each receives and what it may do — the table that turns "eBPF can do anything" into a concrete menu |
| `bpftrace.md` | bpftrace | The high-level language: probes, filters, actions, built-ins, maps, histograms. Twenty one-liners that answer real questions, each with the output shown. The fastest path from question to answer on a live system **[Lab]** `<Cast>` |
| `bcc-and-the-tool-zoo.md` | BCC and the Tool Zoo | The ~100 ready-made tools, mapped onto the subsystems in this knowledge base: `execsnoop`, `opensnoop`, `biolatency`, `runqlat`, `tcplife`, `cachestat`, `offcputime`. Which tool answers which question |
| `libbpf-and-co-re.md` | libbpf and CO-RE | Compile Once, Run Everywhere: BTF, relocations against struct layouts that differ per kernel, the skeleton, and the loader. Why this replaced BCC's runtime compilation. **Verify API via context7** |
| `writing-a-tracing-program.md` | Lab: Write a Tracing Program | A complete libbpf/CO-RE program: attach to a tracepoint, record into a ring buffer, read from user space. Build, run in the QEMU lab, and iterate through a verifier rejection **[Lab]** |
| `xdp-and-tc-programs.md` | XDP and tc Programs | Packet processing at the driver, before an `sk_buff` exists: XDP actions, driver versus generic modes, and the performance ceiling. tc/clsact for post-`skb` processing, and the trade-off between the two. Ties back to folder 13 **[Lab]** |
| `bpf-lsm-and-other-uses.md` | BPF Beyond Tracing | BPF-LSM for security policy, cgroup hooks for connect/bind, `sched_ext` for scheduling policy (status at the pinned version), and `struct_ops` for pluggable kernel behaviour. Where the subsystem is heading |
| `limits-and-pitfalls.md` | Limits and Pitfalls | The honest page: verifier complexity limits, instruction budget, probe overhead measured rather than assumed, kprobe attachment breaking on inlined functions, the missing-stability contract for anything not a tracepoint, and the privileges eBPF requires **[WAH]** |

---

### 19-reading-and-contributing — "Reading and Contributing to the Source" (position 20) — 10 pages

| File | Title | Brief |
|---|---|---|
| `how-to-read-kernel-code.md` | How to Read Kernel Code | A method, not a tour: start from an entry point you can name, follow the struct rather than the call, ignore `CONFIG_` branches until they matter, use the tests and the commit message as documentation, and know when to stop **[WAH]** |
| `navigation-tools.md` | Navigation Tools | Elixir for cross-referenced browsing, `git grep` patterns that actually work on this tree, `cscope`/`ctags`, `clangd` with `compile_commands.json` generated by `scripts/gen_compile_commands.py`, and `make tags`. Set up once, used forever **[Lab]** |
| `anatomy-of-a-subsystem.md` | Anatomy of a Subsystem | A worked read of one mid-sized subsystem cold, start to finish: locate it, find the registration points, identify the core struct, follow one operation end to end, and find its tests. The method from page 1, demonstrated rather than described |
| `git-history-as-documentation.md` | Git History as Documentation | The commit message is often the only design document. `git log --follow`, `git log -S` for when a line appeared, `git blame` past a reformat, finding the merge and the mailing-list thread behind a change, and reading a `Fixes:` chain **[Lab]** |
| `the-documentation-tree.md` | The Documentation Tree | `Documentation/` mapped: the ABI directory, `admin-guide`, `driver-api`, `core-api`, `process`. kernel-doc comment format, building the HTML docs locally, and how `docs.kernel.org` is produced |
| `testing-and-static-analysis.md` | Testing and Static Analysis | KUnit for in-kernel unit tests, kselftest for user-space-driven tests, `sparse` and the annotations from folder 04, `smatch`, Coccinelle semantic patches, and `syzkaller` in one section. What CI a patch will meet **[Lab]** |
| `coding-style-and-checkpatch.md` | Coding Style and checkpatch | The style document's rules that carry real meaning versus the mechanical ones, `checkpatch.pl` and which warnings to obey, `clang-format` in-tree, and why consistency here is a review-throughput argument rather than an aesthetic one |
| `making-a-patch.md` | Making a Patch | One logical change per patch, writing a commit message that explains *why*, `git format-patch`, subject prefixes, `Signed-off-by` and the DCO, patch series and cover letters, versioning with a changelog, and `b4` for the modern workflow **[Lab]** |
| `maintainers-and-etiquette.md` | Maintainers, Lists, and Etiquette | `get_maintainer.pl`, subsystem trees and the merge window, plain-text email and why it is non-negotiable, how review actually reads, responding to criticism, and the realistic timeline for a first patch **[WAH]** |
| `your-first-contribution.md` | Your First Contribution | Realistic starting points: a real bug found with the tools from folder 17, a documentation fix, a `sparse` warning, a KUnit test for untested code. Where to find work, and why the staging tree is a worse start than its reputation suggests |

---

## Phases

Each phase is its own implementation plan and ends at a green `npm run build`.

| Phase | Contents | Linux pages | CS backfill | Total |
|---|---|---|---|---|
| **1 — Wiring and foundations** | Plugin, components, site wiring, CS backfill 1/2/17, folders 00, 01, 02, 03, 04 | 46 | 3 | 49 |
| **2 — Core kernel** | CS backfill 3/4/6/7/8/10, folders 05, 06, 07, 08, 09, 10 | 76 | 6 | 82 |
| **3 — Storage and networking** | CS backfill 12/13/14/15/16, folders 11, 12, 13 | 36 | 5 | 41 |
| **4 — Drivers, containers, security** | CS backfill 5/9/11/18, folders 14, 15, 16 | 37 | 4 | 41 |
| **5 — Observability, eBPF, contributing** | Folders 17, 18, 19 | 34 | 0 | 34 |
| | | **229** | **18** | **247** |

**Forward links between phases are forbidden.** A Phase 1 page may not name a Phase 3 page in its
`prerequisites` — the graph plugin throws on an unresolvable id, so this is enforced by the build,
not by discipline. Where a Phase 1 page genuinely wants to point forward, it says so in prose
without a link, and the link is added when the target lands.

### Phase 1 ordering

Infrastructure is proven before bulk writing begins:

1. Choose and record the pinned LTS version; set `customFields.linuxKernelVersion`.
2. `src/lib/kernelSource.js` + `<Src>`; verify a generated Elixir link resolves in a real browser.
3. `knowledge-graph-plugin.js` + `<PrereqBlock>` + `DocItem/Layout` injection. Prove the three throw
   conditions (unknown id, cycle, missing key) actually fail the build.
4. `<KernelFacts>`, `<Lab>` and their CSS.
5. `asciinema-player` install, `<Cast>`, and one real recorded cast rendering in a **production**
   build (`npm run build && npm run serve`) — the SSR-safety of the dynamic import must be proven,
   not assumed.
6. `<KnowledgeGraph>` on `roadmap.md`.
7. Section wiring: `sidebars.js`, navbar, Prism languages, `_category_.json` files.
8. Then, and only then, the CS backfill pages and folders 00–04.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Source citations rot | One pinned version constant; `<Src>` everywhere; symbol names not line numbers; version stated in `readme.md` |
| A page states something true only of x86-64 | Arch is named explicitly on every arch-specific claim; arm64 contrast `:::note`s are a required review check |
| Content is already stale when written (EEVDF, folios, `io_uring`, cgroup v2, libbpf) | Per-folder context7 verification table, checked at write time and dated in `## References` |
| The generated graph becomes a hairball | Never render the full graph. Folder granularity by default; per-folder subgraphs capped at ~20 nodes |
| Frontmatter prerequisite lists decay | Build fails on unknown id, on a cycle, and on a missing `prerequisites` key |
| The asciinema player breaks SSR | `<BrowserOnly>` + dynamic import, proven in a production build in Phase 1 before any page depends on it |
| Labs that only work on the author's machine | Every lab carries a host badge and shows expected output; the QEMU invocation is defined once in folder 01 and reused verbatim |
| Duplication with `computer-science/` and `embedded/` | Normative no-duplication table; the embedded spec is amended in the same commit as this one |
| 247 pages stall half-written | Five phases, each independently shippable and each ending at a green build. Folders 00–04 alone are a coherent, useful section |
| Figure licences | `SOURCES.md` gains a `license` column; per-image licence check required, with Mermaid as the correct fallback |
