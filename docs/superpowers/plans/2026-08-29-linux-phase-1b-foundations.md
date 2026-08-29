# Linux & Kernel Section — Phase 1b (Foundations Prose) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the 44 remaining one-sentence stubs in `docs/linux/` folders 00–04 into finished pages, write the three `computer-science/` backfill pages they depend on, retire the `<KnowledgeGraph>` component in favour of a linked learning-path renderer, and leave the section at a green `npm run build` with `check:linux --written` passing for folders 00–04.

**Architecture:** No new site machinery beyond one ~40-line presentational component. The knowledge-graph *plugin* stays exactly as it is — it is the build gate that fails on a missing `prerequisites` key, an unresolvable id, or a cycle — and `<PrereqBlock>` keeps injecting Before/Next/Related chips into every page. What goes away is the Mermaid *rendering* of that graph, which the user rejected: `roadmap.md` instead presents six curated learning paths through a `<LearningPath>` component that reuses the CSS already written for the graph's trail. Pages stay plain `.md` consuming globally-registered MDX components.

**Tech Stack:** Docusaurus 3.10.2, React 19, Mermaid (via `@docusaurus/theme-mermaid`), WaveDrom, Biome 2.5.7, Node 22 (`node --test`), `docusaurus-plugin-image-zoom`.

**Spec:** `docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md`
**Predecessor plan:** `docs/superpowers/plans/2026-08-28-linux-phase-1a-infrastructure.md` (infrastructure + scaffold; already executed)

---

## Global Constraints

- **Pinned kernel is `v6.18`.** Every source citation goes through `<Src file="..." symbol="..." />`, which builds its URL from `customFields.linuxKernelVersion`. Never hand-write an `elixir.bootlin.com` URL, and never cite a line number — file plus symbol only.
- **Never invent a symbol, struct field, or path.** Every symbol named on a page is checked against `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>` before the page is committed. A plausible-looking wrong symbol is worse than an omission. The `KernelFacts` values in this plan are starting points, not verified truth — verify each one.
- **Every doc under `docs/linux/` must keep its `prerequisites` front-matter key.** Empty array valid, missing key fails the build. Do not touch the front matter of a page you are writing except to add `related:` if genuinely needed.
- **`onBrokenLinks: "throw"`.** Folders 05–19 are **not scaffolded yet**, so no link may point into them. Where a page wants to point forward, it names the topic in prose with no link, and the link lands when the target does.
- **Relative doc links only** — `../02-guided-traces/the-life-of-a-write.md` style, never `/docs/linux/...`. `baseUrl` is `/knowledge-base/`.
- **`## What actually happens` is conditional.** Only on pages marked **[WAH]** in this plan. Adding it elsewhere is a review finding.
- **Every finished topic page ends with `<KernelFacts />` and carries a `## References` section** with 2–6 annotated entries. `tools/check-linux-docs.mjs` enforces both. The four navigational pages (`readme.md`, `roadmap.md`, `glossary.md`, `misconceptions-index.md`, `how-to-use-this-section.md`) are exempt and already listed in the checker's `NAVIGATIONAL` set.
- **Every page carries at least one visual anchor**: a Mermaid diagram, a WaveDrom `reg`, a `<Figure>`, or a substantive comparison table. Its caption says *what it shows*, never "Diagram 3".
- **Fence languages:** kernel C → ` ```c `; Intel-syntax disassembly → ` ```nasm `; **AT&T asm, `Kconfig`, linker scripts, device tree, `gdb`/`perf` transcripts, `dmesg` → ` ```text `; a `.config` fragment → ` ```ini `; unit files → ` ```systemd `. All of these are already in `prism.additionalLanguages`.
- **Five admonitions only**: `:::info`, `:::note`, `:::tip`, `:::warning`, `:::danger`. `:::danger` is reserved for irreversible damage and states what is lost.
- **Name the architecture on every arch-specific claim.** x86-64 is the spine; arm64 contrasts go in a `:::note`.
- **No new asciinema casts in this phase.** `<Cast>` stays registered and `static/casts/linux/hello.cast` stays as the working proof, but a real cast requires a real recorded QEMU session and none is being recorded here. Terminal material ships as annotated ` ```text ` blocks. This is the user's explicit policy: casts only where the *interaction* is the lesson, code blocks for everything else.
- **Figures for this section are not licence-gated** (spec departure from `CLAUDE.md`), but every image file needs a row in `static/img/linux/SOURCES.md` and an on-page source credit via `<Figure source= href= />`.
- **Biome** covers `**/*.{js,jsx,ts,tsx,json,md}` at 2-space indent; it does *not* cover `.mjs`. Run the lint gate raw — `rtk run 'npm run lint'` — because the Claude Code hook rewrites `npm run lint` to a different linter and will report a false pass.
- **Commit messages:** `<type>: <what>` on one line. Never a `Co-Authored-By` trailer, never a "Generated with Claude Code" line.

---

## File Structure

**Deleted**

| File | Why |
|---|---|
| `src/components/KnowledgeGraph/index.jsx` | The user rejected the rendered graph. The plugin that validates the graph stays; only the drawing goes. |

**New**

| File | Responsibility |
|---|---|
| `src/components/LearningPath/index.jsx` | Renders one ordered, numbered, clickable route through the section from an explicit list of steps. ~40 lines, no data dependencies. |
| `static/img/linux/SOURCES.md` | Provenance table for every third-party image in the section. |
| `static/img/linux/kernel-architecture-and-idioms/linux-kernel-diagram.svg` | The Graphviz gallery's whole-kernel subsystem map — folder 04's anchor figure. |
| `static/img/linux/overview/privilege-rings.svg` | x86 protection rings — folder 00's bridge-page figure. |

**Modified**

| File | Change |
|---|---|
| `src/theme/MDXComponents.js` | Drop the `KnowledgeGraph` import and registration; add `LearningPath`. |
| `src/css/linux-components.css` | Rename the `.kb-graph__trail*` block to `.kb-path*`; delete nothing else. |
| `docs/linux/00-overview/roadmap.md` | Both `<KnowledgeGraph>` calls removed; six learning paths rendered with `<LearningPath>`. |
| `docs/linux/00-overview/*.md` (7 pages) | Stub → written. |
| `docs/linux/01-lab-and-toolchain/*.md` (7 pages) | Stub → written. |
| `docs/linux/02-guided-traces/*.md` (6 pages) | Stub → written. |
| `docs/linux/03-boot-and-init/*.md` (12 pages) | Stub → written. |
| `docs/linux/04-kernel-architecture-and-idioms/*.md` (12 pages) | Stub → written. |
| `docs/computer-science/cpu-architecture/privilege-levels-and-protection.md` | Stub → written (backfill 1). |
| `docs/computer-science/cpu-architecture/exceptions-traps-and-interrupts.md` | Stub → written (backfill 2). |
| `docs/computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid.md` | Stub → written (backfill 17). |
| `CLAUDE.md` | Component list, cast policy, figure policy, and phase status brought current. |

**Untouched, deliberately:** `src/plugins/knowledge-graph-plugin.js`, `src/plugins/knowledge-graph/buildGraph.js`, `scripts/build-graph.test.mjs`, `src/components/PrereqBlock/`, `src/theme/DocItem/Layout/index.js`, `tools/linux-docs-manifest.json`, `tools/scaffold-linux-docs.mjs`.

---

## Page brief format

Every page task below gives, per page:

- **Opens with** — the mental-model paragraph. No page opens with a struct, a command, or a code block.
- **Sections** — the `##` headings, in order.
- **Anchor** — the required visual, and what it must show.
- **KernelFacts** — starting values for the four fixed rows. **Verify every symbol against Elixir v6.18 before committing.**
- **References** — concrete sources; annotate each with why a reader clicks it.

`[WAH]` = the page carries `## What actually happens`. `[Lab host=…]` = the page carries a `<Lab>` with that host badge. `[Misc]` = the page carries `## Misconceptions`, and every entry must later be mirrored into `misconceptions-index.md` (Task 24).

---

## Task 1: Retire `<KnowledgeGraph>`, add `<LearningPath>`, rewrite the roadmap

**Files:**
- Delete: `src/components/KnowledgeGraph/index.jsx`
- Create: `src/components/LearningPath/index.jsx`
- Modify: `src/theme/MDXComponents.js`
- Modify: `src/css/linux-components.css:165-230` (the `<KnowledgeGraph>` block)
- Modify: `docs/linux/00-overview/roadmap.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `<LearningPath title="…" steps={[["Label", "./relative-path.md"], …]} />`, globally registered for any `.md` page. Later phases extend `roadmap.md` with more paths using the same call shape.

- [ ] **Step 1: Delete the component and its registration**

```bash
rm -r src/components/KnowledgeGraph
```

In `src/theme/MDXComponents.js`, remove the line `import KnowledgeGraph from "@site/src/components/KnowledgeGraph";` and the `KnowledgeGraph,` entry from the exported object.

- [ ] **Step 2: Confirm the build gate is untouched**

Run: `npm run test:graph`
Expected: PASS — the plugin and `buildGraph()` are independent of the deleted component. If this fails, something outside the component was removed; restore it.

- [ ] **Step 3: Create `src/components/LearningPath/index.jsx`**

```jsx
import Link from "@docusaurus/Link";

// <LearningPath /> — one curated route through the section.
//
// The section's dependency graph is validated at build time by
// knowledge-graph-plugin and surfaced per page by <PrereqBlock>. What a reader
// actually needs on the roadmap is not a picture of 229 nodes but an ordered
// route they can click through, so that is what this renders: numbered chips,
// in reading order, each one a real link.
//
// Steps are written by hand in the page, not derived from the graph. That is
// deliberate — a learning path is an editorial choice about what to read next,
// which is a different thing from what a page technically depends on.
//
// Usage in markdown:
//   <LearningPath
//     title="I just want to understand my machine"
//     steps={[
//       ["The kernel/user-space boundary", "./the-kernel-userspace-boundary.md"],
//       ["What Linux actually is", "./what-linux-actually-is.md"],
//     ]} />
export default function LearningPath({ title, steps = [] }) {
  if (!title) {
    throw new Error("<LearningPath> requires a `title`");
  }
  return (
    <section className="kb-path">
      <h3 className="kb-path__title">{title}</h3>
      <ol className="kb-path__list">
        {steps.map(([label, href], index) => (
          <li className="kb-path__item" key={href}>
            <Link className="kb-path__link" to={href}>
              <span className="kb-path__index">{index + 1}</span>
              {label}
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
```

- [ ] **Step 4: Register it**

In `src/theme/MDXComponents.js` add `import LearningPath from "@site/src/components/LearningPath";` with the other component imports (alphabetical: after `KernelFacts`), and `LearningPath,` in the exported object.

- [ ] **Step 5: Rename the CSS block**

In `src/css/linux-components.css`, replace the header comment `/* --- <KnowledgeGraph> --- */` with `/* --- <LearningPath> --- */` and rename every selector in that block: `.kb-graph__trail` → `.kb-path__list`, `.kb-graph__trail-item` → `.kb-path__item`, `.kb-graph__trail-link` → `.kb-path__link`, `.kb-graph__trail-index` → `.kb-path__index`. Keep the `@media (max-width: 576px)` rules, renamed the same way. Then add the two selectors the old block did not have, at the top of it:

```css
.kb-path {
  margin: 1.75rem 0;
}
.kb-path__title {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
}
```

- [ ] **Step 6: Rewrite `docs/linux/00-overview/roadmap.md`**

Keep the front matter exactly as it is. Replace everything below the `# Roadmap and Knowledge Graph` heading — and change that heading and the `title:`/`sidebar_label:` front matter to `Roadmap` / `"Roadmap"`, since there is no longer a graph on the page. Body:

An opening paragraph saying that every page declares its prerequisites in front matter, that the build fails on an unresolvable prerequisite or a dependency cycle, and that the *Before this* / *Next* / *Related* chips at the top and bottom of every page are generated from those declarations rather than hand-maintained — so the page you are on always knows what it needs, and this page is the editorial route through it.

Then `## Learning paths`, with a sentence saying paths are filled in as folders land, and that folders 00–04 exist now. Then the six paths. Only pages inside folders 00–04 may appear as steps; where a path continues into an unwritten folder, close it with a plain sentence naming what comes next, unlinked.

```mdx
<LearningPath
  title="I just want to understand my machine"
  steps={[
    ["The kernel/user-space boundary", "./the-kernel-userspace-boundary.md"],
    ["What Linux actually is", "./what-linux-actually-is.md"],
    ["What happens when you type ls", "../02-guided-traces/what-happens-when-you-type-ls.md"],
    ["The life of a write()", "../02-guided-traces/the-life-of-a-write.md"],
    ["From power-on to login prompt", "../02-guided-traces/from-power-on-to-login-prompt.md"],
    ["Distributions and what actually differs", "./distributions-and-what-differs.md"],
  ]} />
```

The other five, same shape:

- **"I want to read kernel source"** — `hardware-the-kernel-assumes` → `04/monolithic-with-modules` → `04/the-source-tree-map` → `04/the-kernel-c-dialect` → `04/kernel-data-structures` → `04/container-of-and-embedded-structs` → `04/error-handling-idioms`. Closing line: reading real subsystem code starts with the syscall boundary, which lands with folder 05.
- **"I want to build and debug a kernel"** — `01/the-lab-machine` → `01/getting-and-navigating-the-source` → `01/building-a-kernel` → `01/a-minimal-rootfs` → `01/booting-your-kernel-in-qemu` → `01/debugging-the-kernel-with-gdb` → `01/a-full-system-vm-and-wsl2`.
- **"I want to understand boot"** — `02/from-power-on-to-login-prompt` → `03/firmware-bios-and-uefi` → `03/the-boot-chain` → `03/bootloaders-grub-and-friends` → `03/the-kernel-image` → `03/early-boot-and-arch-setup` → `03/start-kernel-and-initcalls` → `03/initramfs-and-early-userspace` → `03/switch-root-and-pid-1` → `03/systemd-the-model`.
- **"My boot is broken"** — `03/the-kernel-command-line` → `03/systemd-in-practice-and-boot-debugging` → `03/initramfs-and-early-userspace` → `01/debugging-the-kernel-with-gdb`. Closing line: crash and oops reading lands with folder 17.
- **"I want to write a module"** — `04/monolithic-with-modules` → `04/kconfig-and-kbuild` → `04/modules-in-practice` → `04/exported-symbols-and-the-module-abi` → `04/reference-counting-and-lifetime` → `04/kobjects-sysfs-and-the-object-model` → `04/memory-safety-in-kernel-c`. Closing line: a real character driver is built in folder 14.

Close the page with `## Where the rest is`: one short paragraph saying folders 05–19 are specified and not yet scaffolded, and naming what they cover (syscalls, processes, scheduling, memory, locking, interrupts, VFS, block I/O, networking, drivers, containers, security, observability, eBPF, contributing) in one sentence. **Do not link the spec** — `docs/superpowers/` is outside the docs sidebar and a link into it is a broken-link risk for no reader benefit.

- [ ] **Step 7: Verify nothing still references the deleted component**

Run: `rtk run "grep -rn 'KnowledgeGraph' docs/linux src tools CLAUDE.md"`
Expected: no output. (Matches inside `docs/superpowers/` are historical records of Phase 1a and stay.)

- [ ] **Step 8: Build and check**

Run: `npm run check:linux && npm run build`
Expected: `check-linux-docs: OK`, then a clean build with no broken-link errors.

- [ ] **Step 9: Lint and commit**

```bash
rtk run 'npm run lint'
git add src/components src/theme/MDXComponents.js src/css/linux-components.css docs/linux/00-overview/roadmap.md
git commit -m "refactor: replace KnowledgeGraph diagram with linked learning paths"
```

---

## Task 2: Figure assets and `SOURCES.md`

**Files:**
- Create: `static/img/linux/SOURCES.md`
- Create: `static/img/linux/kernel-architecture-and-idioms/linux-kernel-diagram.svg`
- Create: `static/img/linux/overview/privilege-rings.svg`

**Interfaces:**
- Consumes: nothing.
- Produces: two image paths referenced by Task 8 (`hardware-the-kernel-assumes.md`) and Task 20 (`the-source-tree-map.md`), and the `SOURCES.md` table every later figure appends to.

- [ ] **Step 1: Fetch the Graphviz kernel diagram**

```bash
mkdir -p static/img/linux/kernel-architecture-and-idioms static/img/linux/overview
curl -sSL -o static/img/linux/kernel-architecture-and-idioms/linux-kernel-diagram.svg \
  https://graphviz.org/Gallery/directed/Linux_kernel_diagram.svg
```

- [ ] **Step 2: Fetch the privilege-rings figure**

```bash
curl -sSL -o static/img/linux/overview/privilege-rings.svg \
  https://upload.wikimedia.org/wikipedia/commons/2/26/Priv_rings.svg
```

- [ ] **Step 3: Verify both files are real SVGs, not error pages**

```bash
file static/img/linux/*/*.svg
ls -l static/img/linux/*/*.svg
head -c 120 static/img/linux/overview/privilege-rings.svg
```

Expected: both report `SVG Scalable Vector Graphics image` (or `XML 1.0 document`), both start with `<?xml` or `<svg`, and neither is a few hundred bytes of HTML. If a URL 404s, open the publisher's gallery page (`https://graphviz.org/gallery/` or the Wikimedia *Protection ring* article), pick the equivalent file, and record **the URL you actually used** in Step 4 — never guess a URL into `SOURCES.md`.

- [ ] **Step 4: Write `static/img/linux/SOURCES.md`**

Mirror `static/img/gpu/SOURCES.md`: a short header explaining that every image referenced from `docs/linux/` has a row here so it can be re-sourced, the `/img/linux/...` reference convention (no `/knowledge-base` prefix), and the table.

```markdown
| file | source_url | publisher | retrieved | notes |
|---|---|---|---|---|
| `kernel-architecture-and-idioms/linux-kernel-diagram.svg` | https://graphviz.org/Gallery/directed/Linux_kernel_diagram.svg | Graphviz gallery | 2026-08-29 | Whole-kernel subsystem map, rendered from the gallery's DOT source. Far too dense to read inline — used zoomable. Vector, unmodified. |
| `overview/privilege-rings.svg` | https://upload.wikimedia.org/wikipedia/commons/2/26/Priv_rings.svg | Wikimedia Commons | 2026-08-29 | x86 protection rings 0–3 as concentric circles. Vector, unmodified. |
```

Add a closing line stating the section's figure policy: images are chosen for how well they teach, provenance is recorded here so any figure can be replaced later, and every on-page figure carries a source credit through `<Figure source= href= />`.

- [ ] **Step 5: Verify total size stays sane**

Run: `du -sh static/img/linux`
Expected: well under 1 MB (both files are vector). If either SVG is over ~400 KB, that is fine for vector but note it in the row.

- [ ] **Step 6: Commit**

```bash
git add static/img/linux
git commit -m "docs: add linux section figure assets and SOURCES table"
```

---

## Task 3: CS backfill 1 — Privilege Levels and Protection

**Files:**
- Modify: `docs/computer-science/cpu-architecture/privilege-levels-and-protection.md` (stub → written)

**Interfaces:**
- Consumes: nothing.
- Produces: doc id `computer-science/cpu-architecture/privilege-levels-and-protection`, already named in `hardware-the-kernel-assumes.md`'s `related:` front matter. Its content is what folder 00's boundary page refuses to re-teach.

This page and the two after it are **`computer-science/` pages, not `docs/linux/` pages**: no `prerequisites` key, no `<KernelFacts>`, no `<Lab>`, no `<Src>`. Match the house style of the folder's existing pages (`pipelining.md`, `instruction-set-architecture.md`) — H1, a lead paragraph, `##` sections, tables, Mermaid where structural, and a short closing pointer.

- [ ] **Step 1: Write the page**

Keep the front matter; delete the `:::info[Not yet written]` block.

- **Opens with:** the problem — an operating system must run code it does not trust in the same machine as code that owns the machine, and no amount of software checking can stop untrusted code that is allowed to execute arbitrary instructions. The answer is a hardware mode bit that the untrusted code cannot set.
- **Sections:**
  - `## What a privilege level actually is` — a small state field in the CPU that gates instruction execution and memory access; on x86-64 it is `CPL`, the low two bits of the `CS` selector; the CPU checks it on every instruction fetch and every memory access, in hardware, at no cost to software.
  - `## The x86 rings, and why only two are used` — rings 0–3, `<Figure src="/img/linux/overview/privilege-rings.svg" …>`; ring 1 and 2 exist and are unused by every mainstream OS because paging's user/supervisor bit is a single bit and cannot express four levels. Naming the figure's publisher in `source=`.
  - `## Privileged instructions` — the class, with concrete x86-64 examples: `HLT`, `LGDT`, `LIDT`, `MOV` to/from `CR0`/`CR3`/`CR4`, `WRMSR`/`RDMSR`, `INVLPG`. Attempting one from ring 3 raises `#GP`, which is a fault, not a crash — the OS decides what happens next.
  - `## Memory protection is the other half` — the mode bit alone protects instructions; the page table's user/supervisor bit protects data. Both must agree, and it is the combination that makes the boundary unforgeable.
  - `## Crossing the boundary` — the only ways up: an interrupt, an exception, or a deliberate instruction (`SYSCALL`/`SYSENTER`/`INT`). Every one of them lands at an address the *kernel* chose, not the caller. This is the single most important property on the page.
  - `## Beyond rings: hypervisor and firmware modes` — VMX root mode ("ring −1") and SMM, each in two sentences.
  - `## arm64 does it differently` — exception levels EL0–EL3, EL0 user / EL1 kernel / EL2 hypervisor / EL3 secure monitor; a named hierarchy rather than a numbered ring, and the reason arm64 documentation never says "ring 0".
- **Anchor:** the `<Figure>` in section 2, plus a Mermaid `stateDiagram-v2` showing ring 3 → ring 0 via interrupt/exception/`SYSCALL` and back via `IRET`/`SYSRET`, captioned "The only three ways user code reaches the kernel, and the two ways back."
- **Closing pointer:** one paragraph linking `../../linux/00-overview/the-kernel-userspace-boundary.md` for how Linux builds on this, and `./exceptions-traps-and-interrupts.md` for the taxonomy of the crossings.
- **References:** Intel SDM Vol. 3A ch. 5 "Protection" (the authority for the ring model and the `#GP` conditions); Arm Architecture Reference Manual, "Exception levels" (the arm64 equivalent, and the reason the vocabulary differs); `https://wiki.osdev.org/Security` (a readable summary when the manuals are too much).

- [ ] **Step 2: Build**

Run: `npm run build`
Expected: green. A broken relative link into `docs/linux/` is the likely failure — check the `../../linux/...` depth.

- [ ] **Step 3: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/computer-science/cpu-architecture/privilege-levels-and-protection.md
git commit -m "docs: write CS backfill page on privilege levels and protection"
```

---

## Task 4: CS backfill 2 — Exceptions, Traps, and Interrupts

**Files:**
- Modify: `docs/computer-science/cpu-architecture/exceptions-traps-and-interrupts.md` (stub → written)

**Interfaces:**
- Consumes: `computer-science/cpu-architecture/privilege-levels-and-protection` (link to it, do not re-teach rings).
- Produces: doc id `computer-science/cpu-architecture/exceptions-traps-and-interrupts`, named in `hardware-the-kernel-assumes.md`'s `related:`. Folder 02's page-fault trace and folder 03's early-boot page both lean on the taxonomy defined here.

- [ ] **Step 1: Write the page**

- **Opens with:** the mental model — a CPU executing a stream of instructions needs a way to stop doing that and run something else, either because the instruction it is executing cannot complete, or because the world outside the CPU wants attention. Those two reasons behave completely differently, and conflating them is the source of most confusion about kernels.
- **Sections:**
  - `## The taxonomy` — a table with five rows: **Fault** (re-executable; the faulting instruction runs again after the handler; page fault, `#GP`), **Trap** (the *next* instruction runs after the handler; breakpoint, `INT3`, syscall via `INT 0x80`), **Abort** (not re-executable, usually fatal; machine-check), **Interrupt** (asynchronous, unrelated to the current instruction; device IRQ), **NMI** (asynchronous and unmaskable). Columns: synchronous?, re-executable?, source, x86-64 example.
  - `## What "precise" means, and why it matters` — the CPU must present an architectural state as if every instruction before the faulting one completed and none after it started. Out-of-order cores go to great expense for this, and it exists so that a fault handler can *fix the problem and retry* — which is the entire mechanism behind demand paging.
  - `## Vectoring: how the CPU finds the handler` — a vector number indexes a table of handler addresses (x86-64: the IDT, located by `IDTR`); the CPU switches stack, pushes a defined frame, and jumps. The handler address is set by privileged code, which is what makes the boundary hold.
  - `## What gets pushed, and by whom` — the hardware-pushed frame (`SS`, `RSP`, `RFLAGS`, `CS`, `RIP`, and an error code on some vectors) versus everything else, which is software's problem.
  - `## Masking` — `IF`/`CLI`/`STI`, what can and cannot be masked, and the fact that a masked interrupt is *delayed*, not lost.
  - `## arm64` — a `:::note`: a small vector table indexed by exception *category* and origin rather than a 256-entry table indexed by vector number; the interrupt source is read from the GIC afterwards.
- **Anchor:** Mermaid `sequenceDiagram` with participants Instruction stream / CPU / Vector table / Handler, showing the fault path — instruction faults, CPU consults the table, switches privilege and stack, pushes the frame, handler runs, `IRET`, the *same* instruction re-executes. Caption: "A fault, from the instruction that could not complete to the instruction re-executing successfully."
- **Closing pointer:** to `../../linux/02-guided-traces/the-life-of-a-page-fault.md` as the worked example of a fault being repaired, and `../../linux/00-overview/hardware-the-kernel-assumes.md`.
- **References:** Intel SDM Vol. 3A ch. 6 "Interrupt and Exception Handling" (the vector table, the pushed frame, and the fault/trap/abort classification per vector); Arm ARM "Exception model" (the arm64 contrast); `https://wiki.osdev.org/Exceptions` (a per-vector quick reference).

- [ ] **Step 2: Build, lint, commit**

```bash
npm run build && rtk run 'npm run lint'
git add docs/computer-science/cpu-architecture/exceptions-traps-and-interrupts.md
git commit -m "docs: write CS backfill page on exceptions, traps, and interrupts"
```

---

## Task 5: CS backfill 17 — OS Structure, and the backlinks

**Files:**
- Modify: `docs/computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid.md` (stub → written)
- Modify: `docs/computer-science/cpu-architecture/privilege-levels-and-protection.md` (add backlink, if Task 3 left it implicit)
- Modify: `docs/computer-science/operating-systems/intro.md` (one-line pointer)

**Interfaces:**
- Consumes: nothing.
- Produces: doc id `computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid`, named in `04/monolithic-with-modules`'s `related:` front matter. That Linux page states where Linux sits; this page owns the taxonomy and the trade-offs.

- [ ] **Step 1: Write the page**

- **Opens with:** the real question behind the taxonomy — not "which is better" but "where do you put the boundary?" Every OS has to decide which code runs with full hardware authority and which does not, and every position on that axis buys something and pays for it.
- **Sections:**
  - `## The axis` — a diagram, then the three named positions: monolithic (all services in one privileged address space), microkernel (a minimal privileged core, services as user-space servers communicating by IPC), hybrid (a monolithic kernel that adopts some microkernel structure, or a microkernel with servers co-located for speed).
  - `## What a microkernel buys` — fault isolation (a crashed filesystem server is a restart, not a panic), enforceable least privilege, formal verifiability at realistic scale (seL4).
  - `## What it costs` — the boundary crossing. A monolithic call between subsystems is a function call; the microkernel equivalent is at minimum two privilege transitions and a context switch, and the data must be copied or granted. Say plainly that modern IPC is far cheaper than the 1990s benchmarks suggested, and that the cost is structural rather than fatal.
  - `## The historical argument, briefly` — the Tanenbaum–Torvalds exchange as a genuine engineering disagreement about where to spend complexity, not a flame war worth re-fighting; note that both positions aged into partial correctness.
  - `## Where real systems actually sit` — a table: Linux (monolithic + loadable modules), Windows NT (hybrid; graphics moved *into* the kernel for speed), macOS/XNU (Mach microkernel core with a BSD monolithic layer in the same address space), QNX and seL4 (true microkernels), unikernels (the boundary removed entirely).
  - `## Modules are not isolation` — the one paragraph that matters most for the Linux section: a loadable module is a build- and deploy-time convenience, loaded into the same address space with the same authority as the rest of the kernel. This corrects a belief many readers hold.
- **Anchor:** a table comparing the three structures across five columns — where drivers run, cost of a subsystem call, blast radius of a driver bug, ease of extension, and a real system that chose it. Plus a small Mermaid `flowchart LR` showing the same request served monolithically (one hop) versus via a microkernel server (four hops).
- **Closing pointer:** to `../../linux/04-kernel-architecture-and-idioms/monolithic-with-modules.md`.
- **References:** Tanenbaum & Torvalds, *"LINUX is obsolete"* comp.os.minix thread, 1992 — archived at `https://www.oreilly.com/openbook/opensources/book/appa.html` (the primary text of the argument, worth reading once); Liedtke, *"On µ-Kernel Construction"* (SOSP '95) — the paper that showed microkernel IPC cost was an implementation property, not an inherent one; `https://sel4.systems/About/` (what a formally verified microkernel actually guarantees, and the scope of that guarantee).

- [ ] **Step 2: Add the backlinks**

The backfill pages exist to be depended on, so the edges must run both ways. In `docs/computer-science/operating-systems/intro.md`, add a one-line pointer to the new page in whatever list of the folder's pages it already carries. In `privilege-levels-and-protection.md` and `exceptions-traps-and-interrupts.md`, confirm the closing pointers written in Tasks 3 and 4 are present.

- [ ] **Step 3: Build, lint, commit**

```bash
npm run build && rtk run 'npm run lint'
git add docs/computer-science/operating-systems
git commit -m "docs: write CS backfill page on OS structure and add backlinks"
```

---

## Task 6: Folder 00 — scope and the boundary

**Files:**
- Modify: `docs/linux/00-overview/what-this-section-covers.md`
- Modify: `docs/linux/00-overview/the-kernel-userspace-boundary.md`

**Interfaces:**
- Consumes: `computer-science/cpu-architecture/privilege-levels-and-protection` (Task 3) — linked, never re-taught.
- Produces: `linux/overview/the-kernel-userspace-boundary`, the prerequisite of `04/monolithic-with-modules`. Every later folder assumes the two-worlds model established here.

### `what-this-section-covers.md` — What This Section Covers

- **Opens with:** what "understanding Linux" means operationally, stated as three capabilities — predicting behaviour from mechanism instead of from remembered commands, reading kernel source to answer a question nobody has blogged about, and instrumenting a running system instead of guessing.
- **Sections:**
  - `## What this section is` — the ladder from the syscall boundary down to page tables, RCU, and the packet path; the fact that it is source-anchored to one pinned kernel; the lab as the spine.
  - `## What this section is not` — not a distribution guide, not a sysadmin certification path, not a command reference, not a substitute for `man`. Each in one line.
  - `## Who it is for` — someone comfortable in C and on a shell who wants the layer under the tools.
  - `## What it assumes, and where the assumptions live` — hardware and OS theory live in `computer-science/`; this section links and goes deeper. Point at `hardware-the-kernel-assumes.md`.
  - `## How it is organised` — the folder ladder in one table (position, folder, one line), marking folders 00–04 as written and the rest as specified. Point at `roadmap.md` for routes and `how-to-use-this-section.md` for conventions.
  - `## The pinned kernel` — v6.18, why one pinned LTS, and that a claim true here may be false on another version. Point at `../readme.md`.
- **Anchor:** the folder-ladder table.
- **KernelFacts:** `structure` — leave empty (`structure={[]}` is valid); `path` — `"Read the boundary, pick a route from the roadmap, build the lab, then follow the ladder"`; `observe` — `uname -r`; `trap` — "Knowing which command does a thing is not knowing what happens. This section is about the second one, and it will not make you faster at the first."
- **References:** `https://docs.kernel.org/` (the section's primary source, and what every claim is checked against); `https://lwn.net/Kernel/Index/` (the by-topic index into the best secondary writing on kernel mechanism); `https://elixir.bootlin.com/linux/v6.18/source` (the pinned source every `<Src>` link resolves into).

### `the-kernel-userspace-boundary.md` — The Kernel/User-Space Boundary **[WAH]** **[Misc]**

The most important page in folder 00. Everything later is a variation on it.

- **Opens with:** two worlds, one door. User space is code the machine does not trust with the hardware; the kernel is code that owns it. The door is not a convention or a library — it is enforced by a bit in the CPU that user code cannot set. Every mechanism in this section is shaped by the cost and the rules of that door.
- **Sections:**
  - `## What is on each side` — a table: address space, privilege level, what a crash costs, what it may touch, how it is scheduled, what it may not do.
  - `## The door is hardware` — one paragraph, then link straight out to `../../computer-science/cpu-architecture/privilege-levels-and-protection.md`. Do not re-teach rings; say only that the boundary is unforgeable and why that is the whole point.
  - `## What crosses, and how` — the four traffic types, each with the direction it flows: system calls (up, deliberate), interrupts (up, asynchronous, unrelated to the running process), faults (up, synchronous, caused by the running instruction), and copies of data (both ways, always explicit — the kernel may never simply dereference a user pointer). Say that folder 05 owns the mechanics and this page owns the shape.
  - `## What actually happens` **[WAH]** — take `cat /proc/self/status` or a plain `write(1, "hi", 2)`. Walk it at the level of *which side is executing*: your process is running; it executes one instruction that traps; the CPU switches privilege and stack and lands at an address the kernel chose; kernel code runs *on behalf of your process*, in its context, charged to its time; it returns; your process resumes at the next instruction. The reader should finish understanding that there is no "sending a message to the kernel" and no separate kernel process to wait on.
  - `## The kernel is not a process` — you cannot `ps` the kernel. `kthreadd` and its children are visible in brackets and are *not* the kernel; they are kernel threads, which is a different thing. This is the misconception that most needs killing early.
  - `## Why the boundary is expensive, and what that causes` — name the consequences without explaining them yet: the vDSO, batching interfaces, `io_uring`, memory-mapped I/O, and why a fast path in the kernel is worth so much effort. Prose only, no forward links.
  - `## Misconceptions` **[Misc]** — (1) "the kernel is a program that runs alongside my programs" — no, it is code your process executes in a different privilege mode; (2) "a system call is a function call into a library" — no, it is a hardware-mediated privilege transition to an address you do not choose; (3) "the kernel can read my variables directly" — it can, but it must not, and it goes through checked copy routines that turn a bad pointer into `-EFAULT` instead of a crash.
- **Anchor:** Mermaid `flowchart` with two labelled subgraphs (User space / Kernel space) separated by a bar, with four arrows crossing it labelled `syscall`, `interrupt`, `fault`, `copy_to_user`/`copy_from_user`. Caption: "The four kinds of traffic that cross the privilege boundary, and their direction."
- **KernelFacts:** `structure` — `[["struct pt_regs", "arch/x86/include/asm/ptrace.h"]]`; `path` — `"user instruction → CPU privilege transition → kernel entry → handler → return to user"`; `observe` — `perf stat -e 'raw_syscalls:sys_enter' -- ls` (verify the tracepoint name against `perf list` before committing; `syscalls:sys_enter_write` is the alternative); `trap` — "Kernel code that runs for your process is still charged to your process. `sys` time in `time(1)` is your program's time, spent on the other side of the door."
- **References:** `man 2 syscall` (the user-space view of the crossing, and the per-architecture register table); `https://docs.kernel.org/admin-guide/index.html` (what the kernel exposes across the boundary, and the vocabulary the rest of this section uses); Kerrisk, *The Linux Programming Interface*, ch. 3 (the definitive treatment of the system-call interface from the caller's side; a purchase).

- [ ] **Step 1: Write `what-this-section-covers.md`** to the brief above, removing the `:::info[Not yet written]` block.
- [ ] **Step 2: Write `the-kernel-userspace-boundary.md`** to the brief above.
- [ ] **Step 3: Verify every symbol** named on both pages resolves at `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>`.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`
Expected: `check-linux-docs: OK — 4 written page(s), 43 stub(s)` (counts shift as the phase proceeds; what matters is zero findings), then a green build.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/00-overview
git commit -m "docs: write section scope and the kernel/user-space boundary"
```

---

## Task 7: Folder 00 — what Linux is, and what distributions change

**Files:**
- Modify: `docs/linux/00-overview/what-linux-actually-is.md`
- Modify: `docs/linux/00-overview/distributions-and-what-differs.md`

**Interfaces:**
- Consumes: `linux/overview/the-kernel-userspace-boundary` (Task 6).
- Produces: `linux/overview/what-linux-actually-is`, the declared prerequisite of `distributions-and-what-differs`.

### `what-linux-actually-is.md` — What Linux Actually Is **[WAH]** **[Misc]**

- **Opens with:** the word "Linux" naming four different things depending on who says it — a kernel, a kernel plus a userland, a distribution, and an ecosystem — and the fact that the confusion is not pedantry: the four have different maintainers, different release cadences, and different compatibility promises.
- **Sections:**
  - `## The kernel, precisely` — one tarball, one `Makefile`, one `git` history, one release every ~9 weeks, LTS branches maintained for years. Point at `../readme.md` for the pinned version.
  - `## What a distribution adds` — a userland (GNU coreutils, or BusyBox, or Android's), a libc, an init system, a package manager, a patch set, and a kernel *configuration*. Say that the last one matters more than readers expect.
  - `## Two rules that explain most of Linux's design`:
    - **"We do not break user space."** A working program keeps working. Syscalls are never removed, flags are added rather than repurposed, structures grow through explicit size arguments. State the consequence: some interfaces are permanently ugly because fixing them would break someone.
    - **No stable in-kernel ABI.** Internal interfaces change freely, release to release, with no compatibility promise. Out-of-tree modules must be rebuilt; in-tree ones are updated by whoever changes the interface.
  - `## Why those two rules are consistent` — one is a promise to users, the other is a refusal to make that promise to code that chose to live outside the tree. Not hypocrisy: a deliberate allocation of maintenance cost. This is the intellectual core of the page.
  - `## What actually happens` **[WAH]** — when you install a "kernel update" from your distribution. Not the upstream release: a distribution kernel is upstream plus a config plus a patch set, packaged with an initramfs generated on *your* machine at install time, plus a boot loader entry. `uname -r` shows the distribution's version string, not upstream's. Read a real `uname -a` and a real `/proc/version` field by field.
  - `## Monolithic, with modules — in one paragraph` — name it and hand off to `../04-kernel-architecture-and-idioms/monolithic-with-modules.md`.
  - `## Misconceptions` **[Misc]** — (1) "Linux is an operating system" — the kernel is; what you use is a distribution; (2) "a newer kernel version means newer features on my machine" — distribution kernels backport, so a 6.1 distribution kernel may contain code that landed upstream in 6.9; (3) "GNU/Linux is a political point" — it is also a technical one: Alpine and Android are Linux and are not GNU.
- **Anchor:** a Mermaid `flowchart TB` of concentric layers — hardware, kernel, libc, userland, package manager, desktop — with a bracket marking exactly which layers "Linux the kernel" covers. Caption: "Where the kernel stops and the distribution starts."
- **KernelFacts:** `structure` — `[["struct new_utsname", "include/uapi/linux/utsname.h"]]`; `path` — `"uname(2) → sys_newuname() → copy_to_user() of the kernel's utsname"`; `observe` — `cat /proc/version && uname -a`; `trap` — "`uname -r` is a string the build set, not a guarantee about which features exist. Distribution kernels backport heavily; the version tells you the base, not the contents."
- **References:** `https://www.kernel.org/category/releases.html` (the live release and LTS table, and where the pinned version came from); `Documentation/admin-guide/abi.rst` at `https://docs.kernel.org/admin-guide/abi.html` (the stability promise, stated by the project itself); Torvalds' "we do not break user space" mail, `https://lkml.org/lkml/2012/12/23/75` (the rule in its author's own words, worth reading for the tone as much as the content).

### `distributions-and-what-differs.md` — Distributions and What Actually Differs **[WAH]** **[Misc]**

- **Opens with:** the useful framing — the interesting question is not what distributions differ on, but the far longer list of what they cannot differ on, because the kernel interface is the same everywhere and that is why a statically linked binary runs on all of them.
- **Sections:**
  - `## What genuinely differs` — a table with rows for init system, libc, package manager, kernel config and patch set, default filesystem, security module (SELinux vs AppArmor vs none), and release model; columns for Debian, Fedora, Arch, Alpine, Android.
  - `## The kernel config is the biggest real difference` — same source, different `.config`; a feature compiled out is genuinely absent. Point at `../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md`.
  - `## libc is the second` — glibc vs musl: a binary built against glibc does not run on Alpine without work, and this is a userland difference that people routinely blame on "the distribution's kernel".
  - `## What does not differ` — syscall numbers and semantics, `/proc` and `/sys` layout, the ELF ABI, signal semantics, the VFS interface, page size and address-space layout on the same architecture. This is the section that makes the page worth reading.
  - `## What actually happens` **[WAH]** — when a package manager "installs a kernel". Unpack `vmlinuz` and modules to `/boot` and `/lib/modules/$(uname -r)`, run `depmod`, generate an initramfs against *this* machine's hardware and config, add a boot-loader entry, leave the old kernel installed. Then note that the running kernel is unchanged until reboot, which is why `uname -r` disagrees with the newest thing in `/boot`.
  - `## Android is Linux` — the one that surprises people: same kernel, no GNU userland, Bionic instead of glibc, no systemd, plus vendor patches and a different security model.
  - `## Misconceptions` **[Misc]** — (1) "distributions ship different kernels" — they ship different *configurations and patch sets* of the same kernel; (2) "Alpine is small because its kernel is small" — it is small because of musl and BusyBox, in userland; (3) "the distribution decides how memory management works" — it decides defaults and `sysctl` values, not mechanism.
- **Anchor:** the five-distribution comparison table.
- **KernelFacts:** `structure` — `[["/proc/config.gz", "kernel/configs.c (CONFIG_IKCONFIG_PROC)"]]`; `path` — `"distribution package → /boot/vmlinuz-$VER + /lib/modules/$VER → depmod → initramfs generation → boot-loader entry"`; `observe` — `ls /boot && ls /lib/modules && uname -r`; `trap` — "The newest kernel in `/boot` is not the running kernel. Nothing about a kernel install takes effect until the next boot, and `kexec` is the only exception."
- **References:** `https://wiki.alpinelinux.org/wiki/Comparison_with_other_distros` (a concrete, honest account of what changing libc and userland actually breaks); `https://docs.kernel.org/admin-guide/README.html` (what a kernel build actually produces, which is what a distribution then packages); `https://source.android.com/docs/core/architecture/kernel` (how far a vendor kernel can diverge while still being Linux).

- [ ] **Step 1: Write `what-linux-actually-is.md`** to the brief above.
- [ ] **Step 2: Write `distributions-and-what-differs.md`** to the brief above.
- [ ] **Step 3: Verify** `sys_newuname`, `new_utsname`, and the `CONFIG_IKCONFIG_PROC` path against Elixir v6.18.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/00-overview
git commit -m "docs: write what Linux is and what distributions change"
```

---

## Task 8: Folder 00 — the hardware bridge page

**Files:**
- Modify: `docs/linux/00-overview/hardware-the-kernel-assumes.md`

**Interfaces:**
- Consumes: `computer-science/cpu-architecture/privilege-levels-and-protection` and `…/exceptions-traps-and-interrupts` (Tasks 3, 4) — both already in this page's `related:` front matter; the figure from Task 2.
- Produces: the page every later Linux page points at instead of re-teaching hardware. This is the enforcement point for the spec's no-duplication contract.

### `hardware-the-kernel-assumes.md` — The Hardware the Kernel Assumes

- **Opens with:** the contract framing — Linux is not portable to *any* machine; it is portable to machines that provide a specific short list of capabilities. Naming that list explains why the kernel is shaped the way it is, and it is the reason no page in this section re-teaches hardware: each capability has an owner in `computer-science/`.
- **Sections:** `## The seven capabilities`, then one `###` per capability, each two or three sentences plus a link to its owning page and one sentence naming the Linux mechanism that rests on it:
  1. **Privilege levels** → `../../computer-science/cpu-architecture/privilege-levels-and-protection.md`. Without it there is no kernel, only a library.
  2. **An MMU with a page table walker** → `../../computer-science/memory-hierarchy/virtual-memory-and-paging.md`. Per-process address spaces, demand paging, and `fork()`'s copy-on-write all follow from it. (Note in one sentence that `nommu` Linux exists for MCUs and that this section assumes an MMU throughout.)
  3. **Precise exceptions** → `../../computer-science/cpu-architecture/exceptions-traps-and-interrupts.md`. Demand paging requires that a faulting instruction can be *retried*.
  4. **Interrupts and a controller to route them** → `../../computer-science/buses-and-io/io-and-interrupts.md`. Without them the kernel would have to poll every device.
  5. **Atomic read-modify-write instructions** → `../../computer-science/cpu-architecture/multicore-and-parallelism.md`. Every lock and every reference count in the kernel bottoms out in one.
  6. **A monotonic timer and a way to interrupt on it** → owned by folder 10 later; for now state that preemption, timeouts, and `CLOCK_MONOTONIC` all need a clock the kernel trusts.
  7. **DMA-capable devices** → `../../computer-science/buses-and-io/system-interconnects.md`. The reason drivers are about buffers and ownership rather than about copying bytes.
- `## What Linux does not assume` — no floating point in kernel context, no specific device set, no fixed page size across architectures, no cache coherence with devices (which is why the DMA API exists), and no strong memory ordering — the last one being the reason kernel code is full of explicit barriers even where x86-64 would not need them.
- `## Where each one is owned` — a two-column table (capability → owning page), which is the operational form of the no-duplication contract and the thing a writer of a later page should check before explaining hardware.
- **Anchor:** `<Figure src="/img/linux/overview/privilege-rings.svg" alt="Concentric rings 0 through 3, with the kernel at ring 0 and applications at ring 3" caption="x86 protection rings. Linux uses two of the four: ring 0 for the kernel, ring 3 for everything else." source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Priv_rings.svg" />` — plus the ownership table.
- **KernelFacts:** `structure` — `[["struct cpuinfo_x86", "arch/x86/include/asm/processor.h"]]`; `path` — `"CPU feature bits → cpu_has()/boot_cpu_has() at init → the kernel enables or refuses a mechanism"`; `observe` — `lscpu && grep -m1 flags /proc/cpuinfo`; `trap` — "The kernel does not require a *fast* MMU, a *fast* atomic, or a *precise* clock — it requires that they exist and are correct. Nearly every performance chapter in this section is about the gap between correct and fast."
- **References:** `https://docs.kernel.org/arch/index.html` (what the kernel actually requires per architecture, and how the arch layer is structured); `Documentation/core-api/dma-api.rst` at `https://docs.kernel.org/core-api/dma-api.html` (the clearest statement of what the kernel does *not* assume about device/CPU cache coherence); Intel SDM Vol. 3A ch. 1–2 (the architectural features this page depends on, in their primary source).

- [ ] **Step 1: Verify every link target exists** before writing — several point into `computer-science/` folders whose file names must be checked:

Run: `rtk run "ls docs/computer-science/cpu-architecture docs/computer-science/memory-hierarchy docs/computer-science/buses-and-io"`
Expected: `multicore-and-parallelism.md`, `virtual-memory-and-paging.md`, `io-and-interrupts.md`, `system-interconnects.md` all present. If one is named differently, use the real name — do not invent a link and discover it at build time.

- [ ] **Step 2: Write the page** to the brief above.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 4: Commit**

```bash
git add docs/linux/00-overview/hardware-the-kernel-assumes.md
git commit -m "docs: write the hardware-the-kernel-assumes bridge page"
```

---

## Task 9: Folder 01 — the lab machine and the source

**Files:**
- Modify: `docs/linux/01-lab-and-toolchain/the-lab-machine.md`
- Modify: `docs/linux/01-lab-and-toolchain/getting-and-navigating-the-source.md`

**Interfaces:**
- Consumes: nothing (`the-lab-machine` declares `prerequisites: []`).
- Produces: **the canonical host-package list and the lab's directory convention**, reused verbatim by every later lab in the section. Fix `~/kernel-lab/` as the working directory here; Tasks 10–12 and every later folder's labs use it without redefining it.

### `the-lab-machine.md` — The Lab Machine

- **Opens with:** why a virtual machine rather than your laptop — a kernel panic costs you a QEMU process instead of a reboot, you can attach a debugger to the CPU itself and single-step kernel code, and you control the exact kernel version, which is what makes every claim in this section checkable rather than believable.
- **Sections:**
  - `## What the lab is` — one QEMU/x86-64 VM booting a kernel you built, with a BusyBox initramfs; plus a Debian cloud image later for the labs that need systemd, real block devices, and a network stack.
  - `## The host badges` — a table of the five `<Lab host=…>` values (`qemu`, `qemu-gdb`, `any-linux`, `wsl2-ok`, `root-required`), what each promises, and the rule that a lab carrying a `:::danger` never gets `any-linux`. This table is the reference for the whole section.
  - `## What to install` — `<Tabs>` with four items: Debian/Ubuntu, Fedora, Arch, WSL2 (Ubuntu). Each an `apt`/`dnf`/`pacman` line covering build essentials, `flex`, `bison`, `libelf-dev`/`elfutils-libelf-devel`, `libssl-dev`/`openssl-devel`, `bc`, `ncurses` dev headers, `qemu-system-x86`, `gdb`, `cpio`, `git`. Verify each package name against the distribution before committing — wrong package names make the whole folder unusable.
  - `## The directory convention` — `~/kernel-lab/` with `linux/` (the source), `initramfs/` (the rootfs tree), and `boot/` (built artefacts). State plainly that every later lab assumes these paths.
  - `## Disk, memory, and time budget` — an honest table: source checkout ~5 GB (~1.5 GB shallow), a full build ~20–30 GB and 10–40 minutes on 8 cores, a `tinyconfig`-based lab kernel far less. Readers abandon labs when the cost is a surprise.
  - `## KVM, and when you cannot have it` — `-enable-kvm` needs `/dev/kvm` and hardware virtualization; nested virtualization inside a cloud VM often lacks it; WSL2 can expose it on recent Windows builds. Without KVM everything still works, roughly 5–10× slower, which is fine for a lab and painful for a full-system VM.
  - `## What runs where` — a small table mapping folder 01's labs to host badges, so a WSL2-only reader knows immediately what they can do.
- **Anchor:** the host-badge table.
- **Lab** — `<Lab host="any-linux" title="Confirm your host can run the lab" time="5 min">`: run `qemu-system-x86_64 --version`, `gcc --version`, `gdb --version`, and `ls -l /dev/kvm`; show expected output for each; the "if it fails" line points at the install tabs and says that a missing `/dev/kvm` is a slowdown, not a blocker.
- **KernelFacts:** `structure` — `[["~/kernel-lab/", "the working directory every lab in this section assumes"]]`; `path` — `"host packages → source checkout → kernel build → initramfs → QEMU boot → GDB attach"`; `observe` — `qemu-system-x86_64 --version && ls -l /dev/kvm`; `trap` — "Building a kernel on the host and booting it on the host are two different risks. This section only ever boots what you built inside QEMU, and that is the point."
- **References:** `https://www.qemu.org/docs/master/system/target-i386.html` (the x86-64 machine options every later lab's invocation is drawn from); `https://docs.kernel.org/process/changes.html` (the kernel's own minimum tool versions — the authoritative answer to "is my toolchain new enough"); `https://learn.microsoft.com/en-us/windows/wsl/faq` (what WSL2 does and does not provide, checked when a lab is marked `wsl2-ok`).

### `getting-and-navigating-the-source.md` — Getting the Source **[Lab host=any-linux]**

- **Opens with:** the source tree is not a codebase you read front to back; it is a reference you learn to *query*. Getting it locally matters because grep over a real tree answers questions no search engine will, and because every `<Src>` link in this section points at the same tree.
- **Sections:**
  - `## Clone, or tarball?` — full clone (~5 GB, full history, `git log` on a file is the single best kernel-archaeology tool) vs shallow clone (`--depth 1 --branch v6.18`, ~1.5 GB, no history) vs a release tarball from kernel.org (smallest, no git at all). A table with size, what you lose, and when each is right. Recommend the shallow clone at the pinned tag for a first pass.
  - `## Getting v6.18 exactly` — the commands, with the pinned tag, and how to verify: `git describe --tags` and `make kernelversion`.
  - `## The first orientation pass` — a table of top-level directories, one line each: `arch/`, `block/`, `certs/`, `crypto/`, `Documentation/`, `drivers/`, `fs/`, `include/`, `init/`, `io_uring/`, `ipc/`, `kernel/`, `lib/`, `mm/`, `net/`, `rust/`, `samples/`, `scripts/`, `security/`, `sound/`, `tools/`, `usr/`, `virt/`. Verify this list against the actual v6.18 tree before committing. Say that folder 04's source-tree page goes deeper and that this one exists so the reader can find their way today.
  - `## Finding things` — the three tools in order of usefulness: `git grep -n` (fast, respects the tree), `elixir.bootlin.com` (identifier search across versions, and where `<Src>` points), and `cscope`/`ctags` for editor integration. Give a real worked query: find where `SYSCALL_DEFINE3(read, …)` is defined, with `git grep -n "SYSCALL_DEFINE3(read"`.
  - `## Documentation/ is part of the source` — `Documentation/` renders to `docs.kernel.org`, is versioned with the code, and is more complete than readers expect.
- **Anchor:** the top-level directory table.
- **Lab** — `<Lab host="any-linux" title="Clone the pinned kernel and find a syscall" time="15 min">`: 1. `mkdir -p ~/kernel-lab && cd ~/kernel-lab`; 2. `git clone --depth 1 --branch v6.18 https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git linux`; 3. `cd linux && make kernelversion` — expected output `6.18`; 4. `git grep -n "SYSCALL_DEFINE3(read"` — expected a single hit in `fs/read_write.c`; 5. `ls Documentation/ | head`. The "if it fails" line covers a slow or blocked `git.kernel.org` and points at the GitHub mirror `https://github.com/torvalds/linux` with the same tag. **Verify the clone URL and the `git grep` hit before committing.**
- **KernelFacts:** `structure` — `[["Makefile", "the top-level build entry point; VERSION/PATCHLEVEL at the top define the version"]]`; `path` — `"git clone --depth 1 --branch v6.18 → make kernelversion → git grep"`; `observe` — `make kernelversion`; `trap` — "A shallow clone saves 3 GB and costs you `git log`, `git blame`, and `git bisect` — which are the three reasons to have the source locally at all. Shallow is for a first look, not for investigating."
- **References:** `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git` (the canonical stable tree, and the source of the pinned tag); `https://docs.kernel.org/process/submitting-patches.html` (why the tree is laid out the way it is — worth skimming now, essential in folder 19); `https://elixir.bootlin.com/linux/v6.18/source` (the cross-referencer every `<Src>` link in this section resolves into).

- [ ] **Step 1: Verify the top-level directory list** against the real v6.18 tree, either from a local clone or `https://elixir.bootlin.com/linux/v6.18/source`. Do not copy the list from memory.
- [ ] **Step 2: Verify every package name** in the install tabs against the current package archives for Debian, Fedora, and Arch.
- [ ] **Step 3: Write `the-lab-machine.md`** to the brief above.
- [ ] **Step 4: Write `getting-and-navigating-the-source.md`** to the brief above.
- [ ] **Step 5: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 6: Commit**

```bash
git add docs/linux/01-lab-and-toolchain
git commit -m "docs: write lab machine setup and kernel source navigation"
```

---

## Task 10: Folder 01 — building a kernel and a root filesystem

**Files:**
- Modify: `docs/linux/01-lab-and-toolchain/building-a-kernel.md`
- Modify: `docs/linux/01-lab-and-toolchain/a-minimal-rootfs.md`

**Interfaces:**
- Consumes: `~/kernel-lab/linux` from Task 9.
- Produces: `~/kernel-lab/linux/arch/x86/boot/bzImage`, `~/kernel-lab/linux/vmlinux`, and `~/kernel-lab/initramfs.cpio.gz` — the three artefacts Task 11's QEMU invocation consumes by name.

### `building-a-kernel.md` — Building a Kernel **[Lab host=any-linux]**

- **Opens with:** the build is not the interesting part, but the *configuration* is: `.config` decides which of the kernel's ~20,000 options are in your kernel, and almost every "why does my system not have X" question is a config question. Building once makes that concrete.
- **Sections:**
  - `## What a build produces` — a table of the three artefacts people confuse: `vmlinux` (the ELF kernel with symbols, not bootable, what GDB loads), `arch/x86/boot/bzImage` (the compressed bootable image, what QEMU's `-kernel` takes), `vmlinuz` (the distribution's installed name for a `bzImage`). Plus `modules` and `System.map`.
  - `## Starting from a config` — `make defconfig` (sane x86-64 defaults), `make tinyconfig` (minimal, fast, useful for a lab), `make olddefconfig` (carry a config forward), and copying a running system's config from `/proc/config.gz` or `/boot/config-$(uname -r)`.
  - `## The options that matter for a debuggable lab kernel` — a table with symbol, what it gives you, and the cost: `CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT` (or the relevant `CONFIG_DEBUG_INFO*` symbol at v6.18 — **verify the exact symbol name**, symbols in this area changed in 5.18), `CONFIG_GDB_SCRIPTS`, `CONFIG_KALLSYMS_ALL`, `CONFIG_FRAME_POINTER`, `CONFIG_DEBUG_KERNEL`, `CONFIG_DEBUG_INFO_REDUCED` off, `CONFIG_KASAN` off by default (large slowdown, turn on deliberately). Include the `./scripts/config --enable X` one-liners so a reader is not hunting through `menuconfig`.
  - `## `menuconfig` in practice` — `/` searches, the help text names the symbol, `y`/`m`/`n` and what `m` means. One `:::tip`: the search result shows the symbol's dependencies, which is usually the answer to "why can't I enable this".
  - `## Running the build` — `make -j$(nproc)`, realistic times, `make modules_install INSTALL_MOD_PATH=…` for a lab, and what to do when it fails (almost always a missing host package — point back at Task 9's tabs).
  - `## Rebuilding` — Kbuild's dependency tracking, why changing one `CONFIG_` can rebuild half the tree, and `make clean` vs `make mrproper` vs `make distclean`.
- **Anchor:** the artefact table (`vmlinux` / `bzImage` / `vmlinuz` / `System.map` / modules), with a `size` column from a real build.
- **Lab** — `<Lab host="any-linux" title="Build a debuggable lab kernel" time="20–40 min">`: `make defconfig`, then the `./scripts/config --enable` lines, `make olddefconfig`, `make -j$(nproc)`, then `ls -lh vmlinux arch/x86/boot/bzImage` with expected approximate sizes, and `file vmlinux` showing `ELF 64-bit … with debug_info, not stripped`. The "if it fails" line covers missing `flex`/`bison`/`libelf`.
- **KernelFacts:** `structure` — `[[".config", "the generated single source of truth for the build"], ["System.map", "symbol-to-address table for the built kernel"]]`; `path` — `"make defconfig → .config → make -j → vmlinux → objcopy/compression → arch/x86/boot/bzImage"`; `observe` — `ls -lh vmlinux arch/x86/boot/bzImage && file vmlinux`; `trap` — "`vmlinux` is not bootable and `bzImage` has no symbols. GDB needs the first, QEMU needs the second, and you need both from the *same* build or every breakpoint lands in the wrong place."
- **References:** `https://docs.kernel.org/kbuild/kconfig.html` (what `menuconfig` and the `make *config` targets actually do to `.config`); `https://docs.kernel.org/admin-guide/README.html` (the kernel's own build instructions, which are short and authoritative); `https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html` (the config symbols the GDB scripts require — the reason this page turns them on).

### `a-minimal-rootfs.md` — A Minimal Root Filesystem **[Lab host=any-linux]**

- **Opens with:** a kernel that boots with no root filesystem panics — it has nothing to run. Building the smallest possible userland by hand takes twenty minutes and permanently removes the magic from early user space: `/init` is just a program, and PID 1 is just the first one the kernel executes.
- **Sections:**
  - `## What the kernel needs` — an initramfs is a `cpio` archive the kernel unpacks into a `tmpfs` that becomes `/`; the kernel then executes `/init`. That is the whole contract.
  - `## BusyBox, statically linked` — why static: no dynamic linker, no libc to install, one binary. Download, `make defconfig`, set `CONFIG_STATIC=y`, `make install` into a staging tree.
  - `## The directory skeleton` — `bin/ sbin/ etc/ proc/ sys/ dev/ usr/bin usr/sbin`, and why `proc`, `sys`, and `dev` must exist as empty directories before anything can mount onto them.
  - `## Writing `/init`` — a ~10-line shell script: mount `proc`, `sysfs`, `devtmpfs`, print a marker line, `exec /bin/sh`. Show it in full as a ` ```bash ` block. Note that it must be executable and that forgetting `chmod +x` produces a panic that looks like a kernel bug.
  - `## Packing it` — `find . | cpio -H newc -o | gzip > ../initramfs.cpio.gz`, and what each flag is for.
  - `## What you have just built` — the same mechanism a distribution's `dracut`/`mkinitcpio` uses, minus the hardware detection. Point forward in prose to folder 03's initramfs page for the real-world version.
- **Anchor:** Mermaid `flowchart LR`: `cpio.gz` → kernel unpacks into `rootfs` (tmpfs) → kernel runs `/init` → `/init` mounts `proc`/`sys`/`dev` → `exec /bin/sh`. Caption: "From a cpio archive to a shell prompt, which is everything early user space does."
- **Lab** — `<Lab host="any-linux" title="Build a BusyBox initramfs" time="20 min">` with the full command sequence and the exact expected `cpio` output line (`NNNNN blocks`), plus `ls -lh ~/kernel-lab/initramfs.cpio.gz` showing a file of a few megabytes. The "if it fails" line: a dynamically linked BusyBox produces `/init: not found` at boot, which is the linker missing, not the file.
- **KernelFacts:** `structure` — `[["initramfs.cpio.gz", "a cpio newc archive, gzip-compressed"], ["/init", "the first user-space program the kernel executes"]]`; `path` — `"kernel unpacks cpio into rootfs (tmpfs) → executes /init → /init execs a shell"`; `observe` — `zcat initramfs.cpio.gz | cpio -t | head`; `trap` — "`/init` missing, not executable, or dynamically linked all produce the same kernel panic. The panic says the kernel could not run init; it does not say which of the three is wrong."
- **References:** `https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html` (the kernel's own explanation of rootfs, ramfs, and initramfs, and the difference readers most often get wrong); `https://www.busybox.net/downloads/BusyBox.html` (the applet list, so you know what your one binary can actually do); `https://docs.kernel.org/driver-api/early-userspace/early_userspace_support.html` (the `cpio` format contract the kernel enforces).

- [ ] **Step 1: Verify the debug-info config symbol names** for v6.18 at `https://elixir.bootlin.com/linux/v6.18/source/lib/Kconfig.debug`. The `CONFIG_DEBUG_INFO*` family was restructured; do not cite the pre-5.18 names.
- [ ] **Step 2: Write `building-a-kernel.md`** to the brief above.
- [ ] **Step 3: Write `a-minimal-rootfs.md`** to the brief above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/01-lab-and-toolchain
git commit -m "docs: write kernel build and minimal rootfs pages"
```

---

## Task 11: Folder 01 — booting in QEMU and debugging with GDB

**Files:**
- Modify: `docs/linux/01-lab-and-toolchain/booting-your-kernel-in-qemu.md`
- Modify: `docs/linux/01-lab-and-toolchain/debugging-the-kernel-with-gdb.md`

**Interfaces:**
- Consumes: `bzImage`, `vmlinux`, `initramfs.cpio.gz` from Task 10.
- Produces: **the canonical QEMU invocation**, defined once on `booting-your-kernel-in-qemu.md` and referenced by every later lab in the section rather than repeated. Write it as a single copy-pasteable block and give it a heading a later page can link to.

### `booting-your-kernel-in-qemu.md` — Booting Your Kernel in QEMU **[Lab host=qemu]**

- **Opens with:** the payoff — three files and one command produce a kernel you built, booting on a machine you defined, with the whole boot log on your terminal. From here on, every claim in this section is something you can check rather than believe.
- **Sections:**
  - `## The canonical invocation` — the full command in one ` ```bash ` block, then a table explaining every flag: `-kernel`, `-initrd`, `-append "console=ttyS0 …"`, `-nographic`, `-m 2G`, `-smp 2`, `-enable-kvm`, `-no-reboot`. State that later labs say "the canonical invocation, plus …" and mean exactly this.
  - `## Why `console=ttyS0` and `-nographic` go together` — without the console parameter the kernel logs to a virtual VGA display you cannot scroll; with both, the boot log is stdout, greppable and copy-pasteable. This one detail saves more time than anything else in the folder.
  - `## Reading the boot log` — a real, trimmed `dmesg` excerpt as a ` ```text ` block, annotated: the version banner, the command line echoed back, memory map, CPU bring-up, the initcall region, `Run /init as init process`, and the shell prompt. Point forward in prose to folder 03.
  - `## Getting out` — `Ctrl-A` then `X` quits; `Ctrl-A` then `C` reaches the QEMU monitor; `-no-reboot` stops a panicking kernel from looping forever. Put these three in a `:::tip` — a reader stuck inside `-nographic` with no way out abandons the folder.
  - `## Variations you will need later` — a short table: `-s -S` for GDB (next page), `-drive`/`-hda` for a real block device, `-netdev user` for networking, `-cpu host` with KVM. One line each, no depth.
  - `## When it hangs` — the three usual causes, each with its symptom: no console parameter (silent boot), missing `/init` (panic naming init), wrong `bzImage` path (QEMU error, not a kernel message).
- **Anchor:** the annotated boot-log excerpt.
- **Lab** — `<Lab host="qemu" title="Boot the kernel you built" time="5 min">`: run the canonical invocation; expected output is the banner line containing `6.18.0` and, after a second or so, the BusyBox prompt; then inside the guest run `uname -r`, `cat /proc/cmdline`, and `ls /proc` and show expected output; exit with `Ctrl-A X`.
- **KernelFacts:** `structure` — `[["boot_params", "arch/x86/include/uapi/asm/bootparam.h"]]`; `path` — `"qemu -kernel → firmware/loader handoff → decompression → start_kernel() → initramfs unpack → /init"`; `observe` — `cat /proc/cmdline` inside the guest; `trap` — "`-nographic` without `console=ttyS0` boots a perfectly healthy kernel that prints nothing. The silence is a console misconfiguration, not a hang."
- **References:** `https://www.qemu.org/docs/master/system/invocation.html` (every flag in the canonical invocation, in its primary source); `https://docs.kernel.org/admin-guide/kernel-parameters.html` (the parameters that go in `-append`, and the authority for what each one does); `https://docs.kernel.org/admin-guide/serial-console.html` (why `console=` is what makes the boot log visible).

### `debugging-the-kernel-with-gdb.md` — Debugging the Kernel with GDB **[Lab host=qemu-gdb]**

The highest-leverage page in the folder. Spec marks it `<Cast>`; per this phase's policy it ships annotated ` ```text ` transcripts instead, and a cast can be added later without changing the prose.

- **Opens with:** the thing that makes a VM lab qualitatively different from a real machine — QEMU exposes the guest CPU to GDB, so you can breakpoint kernel code, single-step through a syscall, and walk a live `task_struct`. On real hardware this needs a second machine and a serial cable.
- **Sections:**
  - `## How it works` — `-s` opens a GDB stub on TCP 1234; `-S` freezes the guest before the first instruction; GDB attaches with `target remote :1234` and drives the guest CPU directly. There is no agent inside the guest — this is why it works even when the guest is wedged.
  - `## Loading symbols` — `gdb vmlinux` from the build tree; why it must be the *same build* as the `bzImage`; KASLR must be off (`nokaslr` in `-append`) or symbol addresses will not match, which is the single most common failure.
  - `## The in-tree GDB scripts` — `CONFIG_GDB_SCRIPTS` produces `vmlinux-gdb.py`; `add-auto-load-safe-path`; then `lx-dmesg`, `lx-ps`, `lx-lsmod`, `lx-symbols`. Show real output for `lx-ps` as a ` ```text ` block. Note that `lx-symbols` is what makes module debugging work.
  - `## A first breakpoint` — break on a function that is guaranteed to be hit, e.g. `break do_sys_openat2` or `break __x64_sys_write` (**verify the symbol at v6.18 before committing** — the `__x64_sys_*` prefix comes from the syscall wrapper macros), `continue`, trigger it from the guest shell, then `bt`.
  - `## Walking a task_struct` — `p $lx_current()` or `lx-ps` to find a task, then `p ((struct task_struct *)ADDR)->comm` and `->pid`. Say that folder 06 owns `task_struct` and this page only proves it is reachable.
  - `## Limits` — breakpoints in very early boot need `-S` and patience; single-stepping with interrupts live is confusing; watchpoints on kernel memory are limited by the hardware debug registers.
- **Anchor:** Mermaid `sequenceDiagram` — GDB / QEMU gdbstub / guest CPU / guest shell — showing attach, breakpoint set, continue, the guest command triggering the breakpoint, and the backtrace. Caption: "How a breakpoint set on the host stops a CPU inside the guest."
- **Lab** — `<Lab host="qemu-gdb" title="Break on a system call" time="15 min">`: terminal 1 runs the canonical invocation plus `-s -S` and `nokaslr`; terminal 2 runs `gdb vmlinux`, `target remote :1234`, `break start_kernel`, `continue`; expected: the breakpoint hits before any boot output; then `lx-dmesg | head`, `continue` to the shell, set the syscall breakpoint, run a command in the guest, `bt`. Include a `:::warning` that `-S` means the guest is frozen until GDB says `continue` — a reader who forgets this thinks QEMU is broken.
- **KernelFacts:** `structure` — `[["vmlinux", "the ELF kernel with DWARF symbols; never booted, only read"], ["vmlinux-gdb.py", "generated by CONFIG_GDB_SCRIPTS; loads the lx-* helpers"]]`; `path` — `"qemu -s -S → gdb vmlinux → target remote :1234 → break <symbol> → continue"`; `observe` — `lx-ps`; `trap` — "Breakpoints that never hit, or hit in nonsense code, almost always mean KASLR is on or `vmlinux` is from a different build than the running `bzImage`. Rebuild both together and add `nokaslr`."
- **References:** `https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html` (the in-tree procedure, including the config symbols and the `lx-*` command list); `https://www.qemu.org/docs/master/system/gdb.html` (what `-s` and `-S` do, and the gdbstub's limits); `https://sourceware.org/gdb/current/onlinedocs/gdb.html/Remote-Debugging.html` (the GDB side of remote debugging, for when the connection misbehaves).

- [ ] **Step 1: Verify the syscall entry symbol** (`__x64_sys_write` / `do_sys_openat2`) and `lx-*` command names against v6.18 before writing the GDB page.
- [ ] **Step 2: Write `booting-your-kernel-in-qemu.md`** to the brief above.
- [ ] **Step 3: Write `debugging-the-kernel-with-gdb.md`** to the brief above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/01-lab-and-toolchain
git commit -m "docs: write QEMU boot and kernel GDB debugging pages"
```

---

## Task 12: Folder 01 — the full-system VM, and WSL2 honestly

**Files:**
- Modify: `docs/linux/01-lab-and-toolchain/a-full-system-vm-and-wsl2.md`

**Interfaces:**
- Consumes: the canonical QEMU invocation from Task 11.
- Produces: the **WSL2 capability table** that every `<Lab host="wsl2-ok">` badge in the section is justified by.

### `a-full-system-vm-and-wsl2.md` — A Full-System VM, and What WSL2 Can Do

- **Opens with:** the BusyBox lab is perfect for kernel mechanism and useless for anything that needs systemd, a real block device, or a network stack. A Debian cloud image under QEMU covers those. And since many readers are on Windows, the second half of this page says plainly what WSL2 can and cannot teach.
- **Sections:**
  - `## When the initramfs lab is not enough` — a table: needs systemd (folder 03), needs a real block device and filesystem (folders 11–12), needs a network stack (folder 13), needs containers (folder 15). Each row names the folder, so a reader knows when to build this.
  - `## A Debian cloud image under QEMU` — fetch the `genericcloud` qcow2, create a `cloud-init` seed ISO for the login, boot with `-drive file=…,if=virtio` and `-netdev user,hostfwd=tcp::2222-:22`, then `ssh -p 2222`. Give the commands. **Verify the current cloud-image URL at `https://cloud.debian.org/images/cloud/` before committing** — the path changes with each release.
  - `## Snapshots are the point` — `qemu-img snapshot -c before`, break the machine deliberately, `-l` to list, `-a` to roll back. State plainly that this is what makes the destructive labs later in the section safe to run, and cross-reference the `:::danger` convention.
  - `## Sharing files with the guest` — `virtiofs` for a shared directory, or the simpler `scp` over the forwarded port. One paragraph, with the trade-off.
  - `## WSL2, honestly` — a capability table with three columns (works / partly / does not) covering: building a kernel (works), running most user-space tooling (works), `strace`/`perf` (partly — depends on the WSL kernel's config), `/proc` and `/sys` (partly synthetic), custom kernel (works, via `.wslconfig` pointing at your own image), UEFI/GRUB boot chain (absent — WSL2 has no boot loader), `kexec`/`kdump` (absent), systemd (optional, off by default on older versions), loading arbitrary modules (needs a matching custom kernel), nested QEMU with KVM (works on recent Windows builds).
  - `## Which folders' labs run on WSL2` — a table mapping folders 00–04 to yes/no/partly, with a one-line reason each. This is the table the `wsl2-ok` badge means.
  - `## The honest summary` — WSL2 is a Microsoft-built Linux kernel in a Hyper-V VM with a heavily customised init and filesystem path. It is a fine place to *read* and *build*; it is a bad place to learn boot, and it will teach you wrong things about `/proc` if you trust it uncritically.
- **Anchor:** the WSL2 capability table.
- **KernelFacts:** `structure` — `[["/proc/version", "identifies a WSL2 kernel by its version string"], [".wslconfig", "Windows-side config; `kernel=` points WSL2 at a kernel image you built"]]`; `path` — `"Windows → Hyper-V → Microsoft WSL2 kernel → your distribution's userland"`; `observe` — `cat /proc/version && ls /sys/firmware`; `trap` — "WSL2 runs a real Linux kernel, so most things work — which is exactly why the things that do not work are so confusing. There is no firmware, no boot loader, and no `/sys/firmware/efi`, because nothing booted."
- **References:** `https://learn.microsoft.com/en-us/windows/wsl/wsl-config` (the `kernel=` option, which is how you run your own kernel under WSL2); `https://github.com/microsoft/WSL2-Linux-Kernel` (the actual kernel source Microsoft ships, and its config — the answer to "is this feature compiled in"); `https://cloud.debian.org/images/cloud/` (the cloud images the full-system lab uses, and the release names to pick from).

- [ ] **Step 1: Verify the current Debian cloud-image path** and the `.wslconfig` option names before writing.
- [ ] **Step 2: Write the page** to the brief above.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`
Expected: `check-linux-docs` reports folder 01 fully written (7 pages), zero findings.

- [ ] **Step 4: Commit**

```bash
git add docs/linux/01-lab-and-toolchain/a-full-system-vm-and-wsl2.md
git commit -m "docs: write full-system VM and WSL2 capability page"
```

---

## Task 13: Folder 02 — `ls`, and the life of a `write()`

**Files:**
- Modify: `docs/linux/02-guided-traces/what-happens-when-you-type-ls.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-write.md`

**Interfaces:**
- Consumes: nothing — every page in folder 02 declares `prerequisites: []` by design; these are the section's readable-first entry points.
- Produces: the narrative map the rest of the section fills in.

**Folder-wide constraint, applies to Tasks 13–15.** These pages are specified to name and link every mechanism they pass, but folders 05–19 do not exist yet, so **most of those links cannot be written**. The rule for this phase: link only into folders 00–04; name every other mechanism in **bold prose with no link**, using the exact page title it will eventually get, so the links can be added mechanically later. Put one `:::note` at the top of the *folder's* first page — not on all six — saying the deeper pages land as the section is written. Keep each page to 900–1400 words: breadth, not depth. A guided trace that starts explaining page-table levels has become folder 08 and has failed.

### `what-happens-when-you-type-ls.md` — What Happens When You Type `ls` **[WAH]**

- **Opens with:** the promise — one command, roughly twenty mechanisms, each of which gets its own page later. The point is not to understand any of them yet; it is to know they exist and how they connect, so that later pages have somewhere to attach.
- **Sections** — one short `##` per stage, three or four sentences each:
  1. `## The keystroke` — the terminal emulator, the pty pair, the line discipline buffering the line until Enter. Note that the *terminal* is a user-space program, not a kernel thing, but the pty is.
  2. `## The shell decides` — `ls` is not a builtin, so a `PATH` lookup, then `fork()` and `execve()`. Name **`fork()` and copy-on-write** and **`exec()` and binary formats** in bold, unlinked.
  3. `## Loading the binary` — ELF headers, `PT_LOAD` segments mapped, `PT_INTERP` naming `ld.so`, the dynamic linker resolving symbols. Nothing is read from disk yet — mapping is not reading.
  4. `## The first instruction faults` — the page fault that pulls in the first page of text, the page cache, and the fact that this is the *normal* path, not an error. Link `the-life-of-a-page-fault.md` (same folder — this link is allowed).
  5. `## Reading the directory` — `openat()` then `getdents64()`, not `read()`; VFS dispatch through the filesystem's `iterate_shared`; the dentry cache making the second run faster. **Verify the current directory-iteration operation name at v6.18.**
  6. `## `stat` for every entry` — why `ls -l` is dramatically more syscalls than `ls`, and how the inode cache absorbs it.
  7. `## Writing the output` — `write()` to fd 1, which is the pty; the terminal reads the other end and draws. Link `the-life-of-a-write.md`.
  8. `## Exit and reap` — `exit_group()`, the zombie, the shell's `wait4()`, the prompt returns.
  - `## What actually happens` **[WAH]** — the summary the page exists for: a table of the syscalls in order with a one-line purpose each, produced from a real `strace -c ls` and a real `strace ls` head. Include both as ` ```text ` blocks. Then the sentence that lands the lesson: roughly a hundred syscalls, of which the interesting ones are `execve`, `openat`, `getdents64`, `write`, and `exit_group`; everything else is the dynamic linker.
- **Anchor:** one Mermaid `flowchart TB` of the eight stages, with the user/kernel boundary drawn as a dividing line so a reader sees how many times the trace crosses it. Caption: "One `ls`, eight stages, and every crossing of the privilege boundary."
- **KernelFacts:** `structure` — `[["struct linux_dirent64", "include/uapi/linux/dirent.h"]]`; `path` — `"execve() → ELF loader → page faults → openat() → getdents64() → write() → exit_group()"`; `observe` — `strace -c ls`; `trap` — "`ls` does not call `read()` on the directory. Directories are not readable as files on Linux; `getdents64()` exists precisely because the kernel refuses to hand you raw directory bytes."
- **References:** `man 2 getdents64` (why a separate syscall exists and what the buffer contains); `man 1 strace` (the tool this page's evidence comes from, and the flags worth knowing); `https://docs.kernel.org/filesystems/vfs.html` (the dispatch layer every stage from 5 onward goes through — skim now, own it in folder 11).

### `the-life-of-a-write.md` — The Life of a `write()` **[WAH]** **[Misc]**

- **Opens with:** the question the page answers — when `write()` returns successfully, where is your data? Almost everyone's first answer is wrong, and the correct answer explains both why Linux is fast and why power loss costs data.
- **Sections:**
  1. `## The call` — `write(fd, buf, n)`, the boundary crossing, argument validation, `copy_from_user`. Name **copying data across the boundary** unlinked.
  2. `## VFS dispatch` — `struct file` → `f_op->write_iter`, one indirect call that is the entire reason a filesystem can be a module.
  3. `## Into the page cache` — the data is copied into pages, the pages are marked dirty, and `write()` returns. **This is where the page returns its answer:** at this moment the data is in RAM only.
  4. `## Writeback, later` — dirty ratios, the writeback threads, and the fact that "later" is typically tens of seconds. Name **writeback, dirty pages, and `fsync`** unlinked.
  5. `## The block layer` — a `bio` describing pages and a target device, the I/O scheduler, blk-mq's per-CPU queues. Name **the block layer** unlinked.
  6. `## The device` — the request lands in an NVMe submission queue, the device DMAs the data itself, and signals completion with an interrupt (MSI-X). Name **DMA** and link `../00-overview/hardware-the-kernel-assumes.md`.
  7. `## Completion` — the interrupt handler does almost nothing, defers the rest, pages are marked clean.
  8. `## What `fsync` changes` — it blocks until writeback completes *and* the device confirms its own volatile cache is flushed. Say plainly that without it, a successful `write()` guarantees nothing about durability.
  - `## What actually happens` **[WAH]** — "the file is saved" as a claim, dismantled. Show `sync; echo 3 > /proc/sys/vm/drop_caches` behaviour and `grep -e Dirty -e Writeback /proc/meminfo` before and after a large write, as ` ```text ` blocks with real numbers. Put a `:::warning` on `drop_caches` — it is not destructive but it will make the machine slow for a while, and it is not a tuning technique.
  - `## Misconceptions` **[Misc]** — (1) "`write()` returning means the data is on disk" — no, it means the data is in the page cache; (2) "`O_DIRECT` means synchronous" — no, it bypasses the page cache and still needs a flush for durability; (3) "`fsync` on the file is enough" — the directory entry may also need one for a newly created file.
- **Anchor:** Mermaid `flowchart TB` from `write()` down to the platter/flash, with a horizontal dashed line marking "`write()` returns here" between the page cache and writeback. Caption: "Where `write()` returns, and how much of the journey is still ahead of the data at that moment."
- **KernelFacts:** `structure` — `[["struct file", "include/linux/fs.h"], ["struct bio", "include/linux/blk_types.h"]]`; `path` — `"write() → vfs_write() → f_op->write_iter → page cache (dirty) → writeback → bio → blk-mq → device"`; `observe` — `grep -e Dirty -e Writeback /proc/meminfo`; `trap` — "A successful `write()` is a promise about your process's memory, not about your disk. The only call that makes a durability promise is `fsync()`, and it must also reach the device's own cache."
- **References:** `man 2 fsync` (the exact scope of the durability guarantee, including the directory caveat); `https://docs.kernel.org/admin-guide/sysctl/vm.html` (`dirty_ratio` and friends — the knobs that decide how long "later" is); `https://lwn.net/Articles/752063/` (the PostgreSQL fsync incident — the clearest account of what happens when the error path of this pipeline is misunderstood).

- [ ] **Step 1: Add the folder `:::note`** at the top of `what-happens-when-you-type-ls.md`: these traces name mechanisms that get their own pages as the section is written, and the links appear as those folders land.
- [ ] **Step 2: Capture real evidence** — run `strace -c ls` and `grep -e Dirty -e Writeback /proc/meminfo` on a real Linux host or in the lab, and paste the actual output. Do not invent numbers.
- [ ] **Step 3: Write both pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/02-guided-traces
git commit -m "docs: write guided traces for ls and write()"
```

---

## Task 14: Folder 02 — the page fault and the packet

**Files:**
- Modify: `docs/linux/02-guided-traces/the-life-of-a-page-fault.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-packet.md`

**Interfaces:**
- Consumes: `computer-science/cpu-architecture/exceptions-traps-and-interrupts` (Task 4) for the fault taxonomy — link it, do not re-teach it.
- Produces: the two traces most often referenced from later folders.

### `the-life-of-a-page-fault.md` — The Life of a Page Fault **[WAH]** **[Misc]**

- **Opens with:** the reframing this page exists for — a page fault is not an error. It is the mechanism by which memory becomes real, and a healthy process takes thousands of them per second. Treating faults as failures is the single most expensive wrong model a Linux reader can hold.
- **Sections:**
  1. `## The allocation that allocates nothing` — `malloc(1 GB)` succeeds instantly because it is a promise, not a delivery: `brk`/`mmap` extends the address space, and no physical page is involved.
  2. `## The first touch` — the store instruction, the MMU walking the page table, no valid entry, `#PF` raised. Link `../../computer-science/cpu-architecture/exceptions-traps-and-interrupts.md` for what "precise" buys here.
  3. `## The kernel takes over` — the fault handler receives the faulting address (x86-64: `CR2`) and an error code describing read/write, user/kernel, present/not-present. Say explicitly that this is x86-64.
  4. `## Was this address legal?` — VMA lookup. Found and permitted → repair it. Not found, or permitted differently → `SIGSEGV`. This one branch is the difference between ordinary operation and a segfault, and it is a *lookup in a data structure*, not a hardware decision.
  5. `## Repairing it` — the classification: anonymous first touch (the shared zero page for a read, a fresh zeroed page for a write), file-backed (page cache hit, or read from disk), swap (read back in), copy-on-write (allocate and copy). One or two sentences each.
  6. `## Return, and re-execute` — the handler installs the PTE and returns; the *same instruction* runs again and now succeeds. Nothing in user space observes anything.
  7. `## Minor and major` — minor = no I/O, major = the kernel had to wait for a device. The distinction is about I/O, not severity.
  - `## What actually happens` **[WAH]** — "my program is using 1 GB" versus the truth. Show `/proc/PID/status` `VmSize` vs `VmRSS` for a process that allocated but did not touch, plus `/usr/bin/time -v` minor/major fault counts, as real ` ```text ` output.
  - `## Misconceptions` **[Misc]** — (1) "page faults mean something is wrong" — no, they are how memory works; (2) "a major fault is a worse fault" — it is a fault that needed I/O; (3) "`malloc` returning non-NULL means the memory exists" — it means the mapping exists, and overcommit means the physical page may never be available.
- **Anchor:** Mermaid `flowchart TB` of the classification tree: fault → VMA lookup → {no VMA → SIGSEGV} / {VMA found → permission check → {anon | file | swap | COW}} → install PTE → return → re-execute. Caption: "Every page fault is one walk down this tree; only the leftmost leaf is an error."
- **KernelFacts:** `structure` — `[["struct vm_area_struct", "include/linux/mm_types.h"]]`; `path` — `"#PF → exc_page_fault() → do_user_addr_fault() → handle_mm_fault() → handle_pte_fault()"` (**verify each of these four at v6.18** — the x86 entry names changed with the `exc_*` conversion); `observe` — `/usr/bin/time -v ls 2>&1 | grep -i faults`; `trap` — "A minor fault is not a small major fault. Minor means no I/O was needed; it is the ordinary way anonymous memory comes into existence."
- **References:** `https://docs.kernel.org/mm/index.html` (the memory-management documentation this trace's every stage expands into); `man 5 proc` (the `status`, `statm`, and `smaps` fields the evidence in this page comes from); `https://lwn.net/Articles/914713/` (a current account of the fault path's fast paths — check the date against v6.18 and say so in the annotation).

### `the-life-of-a-packet.md` — The Life of a Packet **[WAH]** **[Misc]**

- **Opens with:** the framing — a packet's journey is the clearest example in the kernel of work being deliberately *deferred*: the interrupt handler does almost nothing, and nearly all of the processing happens later, in a different context, on purpose. Understanding why explains most of the networking stack's shape.
- **Sections** — receive first, transmit briefly:
  1. `## Before the kernel knows` — the NIC DMAs the frame into a ring buffer the driver set up in advance, then raises an interrupt. The data is already in RAM before any kernel code runs.
  2. `## The interrupt, and NAPI` — the handler acknowledges, disables further interrupts for that queue, and schedules polling. Under load the NIC stops interrupting entirely and the kernel polls — an interrupt storm turns into a poll loop by design.
  3. `## `sk_buff`` — one structure carrying the packet and metadata through every layer, with headers peeled by moving pointers rather than copying. Say that this design is why the stack can be layered without a copy per layer.
  4. `## GRO` — small segments merged before they climb, so the stack processes one large packet instead of forty small ones.
  5. `## netfilter and routing` — hook points, the routing decision, conntrack in one sentence each.
  6. `## Transport` — TCP state machine, sequence numbers, the receive queue, and the wakeup of whichever process is blocked in `recv()`.
  7. `## The application finally reads` — `recv()` copies out of the socket queue into the user buffer. Note that this is the first copy since the DMA.
  8. `## Transmit, briefly` — the reverse, plus queueing discipline and the doorbell write that tells the NIC to go.
  - `## What actually happens` **[WAH]** — `ping` de-mystified: an ICMP echo built in the kernel, timestamped, and the round-trip time that includes queueing at both ends. Show a real `ping -c 3` output and read the numbers honestly. Then `cat /proc/interrupts | grep -i eth` or the `softirqs` counters showing `NET_RX`, as real output.
  - `## Misconceptions` **[Misc]** — (1) "the kernel copies each packet at each layer" — no, pointers move within one `sk_buff`; (2) "one packet, one interrupt" — no, NAPI polls under load; (3) "`ping` measures the network" — it measures the network plus both kernels' queueing, and a busy host inflates it.
- **Anchor:** Mermaid `flowchart LR` for the receive path from wire to `recv()`, with the hardirq / softirq / process-context regions drawn as three labelled bands so the deferral is visible. Caption: "The receive path, split by the execution context each stage runs in."
- **KernelFacts:** `structure` — `[["struct sk_buff", "include/linux/skbuff.h"]]`; `path` — `"NIC DMA → hardirq → napi_schedule() → NET_RX softirq → napi_poll → GRO → netfilter → tcp_v4_rcv() → socket receive queue → recv()"` (**verify `tcp_v4_rcv` and `napi_schedule` at v6.18**); `observe` — `cat /proc/softirqs | head -3` and `grep -i eth /proc/interrupts`; `trap` — "The packet is in RAM before the kernel is told about it. The interrupt announces a DMA that already finished; it does not deliver data."
- **References:** `https://docs.kernel.org/networking/napi.html` (NAPI's polling model, in the kernel's own words — the mechanism this page's whole shape depends on); `https://docs.kernel.org/networking/skbuff.html` (what `sk_buff` actually holds and why headers are pointer moves); `man 7 packet` (where user space can tap this path, and at which point).

- [ ] **Step 1: Verify the fault-path and networking symbols** at v6.18 via Elixir before writing.
- [ ] **Step 2: Capture real output** for `/usr/bin/time -v`, `ping -c 3`, `/proc/softirqs`, and `/proc/interrupts`. Real numbers, from a real machine.
- [ ] **Step 3: Write both pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/02-guided-traces
git commit -m "docs: write guided traces for page faults and packets"
```

---

## Task 15: Folder 02 — power-on to login, and the life of a container

**Files:**
- Modify: `docs/linux/02-guided-traces/from-power-on-to-login-prompt.md`
- Modify: `docs/linux/02-guided-traces/the-life-of-a-container.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `linux/guided-traces/from-power-on-to-login-prompt`, the declared prerequisite of `03/firmware-bios-and-uefi` — so folder 03 is written assuming this trace has been read.

### `from-power-on-to-login-prompt.md` — From Power-On to Login Prompt **[WAH]**

This one *can* link forward: folder 03 exists. Link each stage to its folder 03 page.

- **Opens with:** the chain of handoffs — every stage's only job is to find, load, and hand control to the next one, with progressively more of the machine initialised. Nothing about it is magic, and every step leaves evidence you can read afterwards.
- **Sections** — one short stage each, every one linking its folder 03 page:
  1. `## Firmware` → `../03-boot-and-init/firmware-bios-and-uefi.md`. POST, the memory map, device enumeration, then a choice of what to boot.
  2. `## The boot loader` → `../03-boot-and-init/bootloaders-grub-and-friends.md`. Finds a kernel and an initramfs, builds a command line, hands over.
  3. `## The kernel image unpacks itself` → `../03-boot-and-init/the-kernel-image.md`. `bzImage` is mostly a compressed payload plus the code that decompresses it.
  4. `## Getting to C` → `../03-boot-and-init/early-boot-and-arch-setup.md`. x86-64: 16-bit entry, protected mode, early page tables, long mode, then `start_kernel()`.
  5. `## Bringing up the kernel` → `../03-boot-and-init/start-kernel-and-initcalls.md`. Memory, scheduler, timers, interrupts, then the initcall levels that start drivers.
  6. `## Early user space` → `../03-boot-and-init/initramfs-and-early-userspace.md`. The cpio unpacks into rootfs; `/init` runs; the modules needed to reach the real root get loaded.
  7. `## The real root, and PID 1` → `../03-boot-and-init/switch-root-and-pid-1.md`.
  8. `## systemd builds a graph` → `../03-boot-and-init/systemd-the-model.md`. Then `getty`, then `login`, then your shell.
  - `## What actually happens` **[WAH]** — read a real boot afterwards. `systemd-analyze` and `systemd-analyze critical-chain` output as ` ```text ` blocks, plus `dmesg | head -30` annotated. The point: every stage above left a timestamped trace, and "my machine boots slowly" is an answerable question.
- **Anchor:** Mermaid `flowchart TB` of the eight handoffs, each node labelled with *the artefact handed over* (firmware → boot loader binary → `bzImage` → decompressed kernel → initramfs → real root → PID 1 → login). Caption: "Eight handoffs, and the artefact each one passes to the next."
- **KernelFacts:** `structure` — `[["start_kernel()", "init/main.c"]]`; `path` — `"firmware → boot loader → bzImage decompression → early arch setup → start_kernel() → initcalls → /init → switch_root → PID 1 → getty"`; `observe` — `systemd-analyze critical-chain`; `trap` — "The boot loader does not start the operating system. It loads one file and jumps to it; everything after that is the kernel deciding what happens next."
- **References:** `https://docs.kernel.org/admin-guide/bootconfig.html` and `https://docs.kernel.org/arch/x86/boot.html` (the x86 boot protocol — the exact contract between the boot loader and the kernel); `man 1 systemd-analyze` (the measurement tools this page's evidence uses); `https://0xax.gitbooks.io/linux-insides/content/Booting/` (a well-known line-by-line walk of early boot — note in the annotation that it predates the pinned kernel and some file names have moved).

### `the-life-of-a-container.md` — The Life of a Container **[WAH]** **[Misc]**

- **Opens with:** the sentence the whole page defends — a container is a process. There is no container object in the kernel, no `struct container`, and no container system call. What exists is a set of ordinary mechanisms that, applied together at process creation, produce something that *behaves* like a machine.
- **Sections:**
  1. `## The image is a stack of directories` — layers, and overlayfs presenting them as one tree with copy-on-write on writes.
  2. `## `clone()` with unusual flags` — namespaces as a menu: `CLONE_NEWPID`, `CLONE_NEWNS`, `CLONE_NEWNET`, `CLONE_NEWUTS`, `CLONE_NEWIPC`, `CLONE_NEWUSER`, `CLONE_NEWCGROUP`. Each one changes what the new process can *see*, not what it can do.
  3. `## `pivot_root`` — the new process's root becomes the image's merged directory. This is what makes `/` look different inside.
  4. `## cgroups` — what the process can *use*: CPU weight, memory limit, I/O. Say clearly that namespaces and cgroups are orthogonal — visibility versus resources — and that this is the single most useful distinction on the page.
  5. `## Dropping privilege` — capabilities dropped, a seccomp filter installed, often a user-namespace mapping so root inside is not root outside.
  6. `## Networking` — a veth pair, one end in the container's netns, a bridge and a NAT rule on the host.
  7. `## Then `exec`` — and from the kernel's point of view, it is now just a process. `ps` on the host shows it, with a normal PID.
  - `## What actually happens` **[WAH]** — `docker run` de-mystified: show the container's process on the *host* with `ps`, its namespaces with `ls -l /proc/PID/ns`, and its cgroup with `cat /proc/PID/cgroup`, as real output. The reader should end able to point at the process on the host and say "that is the container".
  - `## Misconceptions` **[Misc]** — (1) "a container is a lightweight VM" — no, it is a process; there is no guest kernel; (2) "containers are a kernel feature" — the kernel has namespaces, cgroups, capabilities, and seccomp; "container" is a userspace assembly of them; (3) "root in a container is safe" — only with a user namespace mapping it to an unprivileged host uid.
- **Anchor:** a table of the seven namespace types — flag, what it isolates, and what breaks if you omit it — plus a small Mermaid diagram showing one host process tree with a subtree marked by its namespace and cgroup membership. Caption: "One process tree. The container is a subtree with different namespaces and a cgroup."
- **KernelFacts:** `structure` — `[["struct nsproxy", "include/linux/nsproxy.h"]]`; `path` — `"clone(CLONE_NEW*) → pivot_root() → cgroup assignment → capability drop → seccomp → execve()"`; `observe` — `ls -l /proc/$$/ns`; `trap` — "There is no container in the kernel. Every `docker ps` entry is a process on the host with an unusual set of namespaces, a cgroup, and a reduced capability set — and `ps -ef` on the host will show it to you."
- **References:** `man 7 namespaces` (the authoritative list of namespace types and their semantics); `https://docs.kernel.org/admin-guide/cgroup-v2.html` (the resource side, and why v2's unified hierarchy replaced v1); `man 2 pivot_root` (what actually changes the root, and why it is not `chroot`).

- [ ] **Step 1: Capture real output** for `systemd-analyze critical-chain`, `dmesg | head -30`, `ls -l /proc/$$/ns`, and a real container's `/proc/PID/cgroup`.
- [ ] **Step 2: Verify the namespace `CLONE_NEW*` flag list** against `man 2 clone` and `include/uapi/linux/sched.h` at v6.18.
- [ ] **Step 3: Write both pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`
Expected: folder 02 fully written (6 pages), zero findings.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/02-guided-traces
git commit -m "docs: write guided traces for boot and containers"
```

---

## Task 16: Folder 03 — firmware, the chain, and boot loaders

**Files:**
- Modify: `docs/linux/03-boot-and-init/firmware-bios-and-uefi.md`
- Modify: `docs/linux/03-boot-and-init/the-boot-chain.md`
- Modify: `docs/linux/03-boot-and-init/bootloaders-grub-and-friends.md`

**Interfaces:**
- Consumes: `linux/guided-traces/from-power-on-to-login-prompt` (Task 15) — folder 03 assumes the trace has been read and goes deep instead of broad.
- Produces: `the-boot-chain`'s diagram, which is the reference figure the other nine pages of the folder expand. Draw it once, well, and link back to it rather than redrawing.

### `firmware-bios-and-uefi.md` — Firmware: BIOS and UEFI

- **Opens with:** before any Linux code exists, something has to bring RAM up, work out what hardware is present, and decide what to execute. That something is firmware, it is a full software stack in its own right, and the two models in use differ in ways that change how you debug a failed boot.
- **Sections:** `## What firmware must do` (POST, memory training, building the memory map handed to the OS, enumerating buses, publishing tables); `## Legacy BIOS, as a model` (16-bit real mode, 512-byte MBR, chainloading, interrupt-based services that vanish once the OS takes over); `## UEFI, as a model` (a small OS: FAT32 EFI System Partition, `.efi` executables, NVRAM boot variables and boot order, boot services versus runtime services, the EFI memory map); `## What the kernel is handed` (the memory map — `e820` on legacy, the EFI memory map on UEFI — plus ACPI tables; this is where `dmesg`'s first lines come from); `## Why UEFI made boot simpler and debugging harder` (the loader is a normal program on a readable filesystem; the failure modes moved into firmware NVRAM state you cannot see from Linux without `efibootmgr`); `## Evidence on a running system` (`/sys/firmware/efi` existing or not, `efibootmgr -v`, `dmesg | grep -i efi`).
- **Anchor:** a two-column comparison table (Legacy BIOS vs UEFI) across: where the loader lives, executable format, partition scheme, boot selection, services offered to the OS, and how you inspect it from Linux.
- **KernelFacts:** `structure` — `[["struct efi_memory_desc_t", "include/linux/efi.h"]]` (**verify the exact type name at v6.18**); `path` — `"firmware POST → memory map + ACPI tables → boot variable selects a loader → loader executes"`; `observe` — `ls /sys/firmware/efi && efibootmgr -v`; `trap` — "`/sys/firmware/efi` absent does not mean the machine lacks UEFI; it means *this* kernel was booted through the legacy path. Dual-mode firmware makes this a per-boot fact, not a per-machine one."
- **References:** `https://uefi.org/specifications` (the primary source for boot variables, the ESP layout, and services); `https://docs.kernel.org/arch/x86/boot.html` (what the kernel requires from whatever loads it); `man 8 efibootmgr` (how boot variables are read and changed from Linux).

### `the-boot-chain.md` — The Boot Chain

The folder's reference page. Short, dense, heavily linked.

- **Opens with:** the boot is a sequence of handoffs, and the only way to debug it is to know exactly what is handed over at each step and where each artefact lives on disk. This page is the map; the rest of the folder is the territory.
- **Sections:** `## The chain, end to end` (the anchor diagram); `## What is handed over at each step` (a table: step, artefact, where it lives on disk, what it must do, how to inspect it — firmware/NVRAM, `\EFI\<vendor>\grubx64.efi` or the MBR, `/boot/vmlinuz-*`, `/boot/initrd.img-*`, `root=` device, `/sbin/init`); `## Where each step is covered` (a table linking every folder 03 page); `## Where it usually breaks` (a table of symptom → likely step → the page that covers it: firmware finds nothing bootable, loader menu but no kernel, kernel panics "unable to mount root", initramfs shell prompt, boots to emergency target).
- **Anchor:** the chain diagram — Mermaid `flowchart LR`, one node per stage, each labelled with its artefact, each node's caption naming the page that covers it. Caption: "The full boot chain, with the artefact handed over at each step."
- **KernelFacts:** `structure` — `[["/boot", "where the kernel image, initramfs, and loader configuration live on most distributions"]]`; `path` — `"firmware → loader → kernel → initramfs → real root → PID 1"`; `observe` — `ls -l /boot && cat /proc/cmdline`; `trap` — "Each stage only knows about the next one. A machine that reaches the loader menu has proved firmware and partitioning are fine, which eliminates half the chain before you start guessing."
- **References:** `https://www.freedesktop.org/wiki/Specifications/BootLoaderSpec/` (the standard `/boot` layout modern distributions converge on); `https://docs.kernel.org/admin-guide/init.html` (the kernel's own guide to the "unable to mount root" class of failure, written for exactly this page's failure table); `man 7 boot` (the traditional sequence, stated compactly).

### `bootloaders-grub-and-friends.md` — Boot Loaders **[WAH]** **[Misc]**

- **Opens with:** a boot loader has four jobs and no more: find a kernel, find an initramfs, build a command line, hand over. Everything else — menus, themes, filesystem drivers, scripting — exists to make those four possible on a machine whose configuration it cannot know in advance.
- **Sections:** `## The four jobs`; `## GRUB 2's structure` (the small first-stage image, `core.img` with just enough filesystem support, modules loaded from `/boot/grub`, then the menu); `## Why you never edit `grub.cfg`` (it is generated by `grub-mkconfig` from `/etc/default/grub` and `/etc/grub.d/`; edits are lost on the next kernel install — with the two commands that regenerate it correctly on Debian and Fedora); `## `systemd-boot`` (much smaller: UEFI only, one config file per entry under the ESP, no filesystem drivers because UEFI already reads FAT); `## EFI stub: no loader at all` (the kernel is itself a valid `.efi` executable, and firmware can launch it directly with the command line in a boot variable); `## What actually happens` **[WAH]** — pressing `e` at the GRUB menu: what you are editing is one boot's `linux` and `initrd` lines, not the config, and the change is gone next boot. This is the single most useful recovery trick in the folder — walk it, with the exact keys, and note the `:::tip` that adding `init=/bin/sh` here rescues most broken systems; `## Misconceptions` **[Misc]** — (1) "GRUB boots Linux" — GRUB loads a file and jumps; (2) "editing `grub.cfg` fixes it" — regenerated on the next update; (3) "you need a boot loader" — with EFI stub you do not.
- **Anchor:** a comparison table across GRUB 2 / systemd-boot / EFI stub: firmware support, config location, filesystem knowledge required, size, and what you give up.
- **KernelFacts:** `structure` — `[["/boot/grub/grub.cfg", "generated — never hand-edited"], ["/etc/default/grub", "the input you actually edit"]]`; `path` — `"firmware → loader image → menu entry → linux/initrd lines → kernel handoff with a command line"`; `observe` — `cat /proc/cmdline` (what the loader actually passed, after the fact); `trap` — "`/proc/cmdline` is the truth about what the loader passed, and `grub.cfg` is only what it intended to. When they disagree, the boot used a different entry than you think."
- **References:** `https://www.gnu.org/software/grub/manual/grub/grub.html` (the configuration model, and the generation pipeline this page insists on); `https://www.freedesktop.org/software/systemd/man/latest/systemd-boot.html` (the minimal alternative, and its entry format); `https://docs.kernel.org/admin-guide/efi-stub.html` (booting with no loader at all, and what the firmware must provide instead).

- [ ] **Step 1: Verify the EFI memory-descriptor type name** and the `efi-stub` documentation path at v6.18.
- [ ] **Step 2: Write all three pages** to the briefs above, with `the-boot-chain.md` written *first* so the other two can link its diagram section.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 4: Commit**

```bash
git add docs/linux/03-boot-and-init
git commit -m "docs: write firmware, boot chain, and boot loader pages"
```

---

## Task 17: Folder 03 — the command line, Secure Boot, and the kernel image

**Files:**
- Modify: `docs/linux/03-boot-and-init/the-kernel-command-line.md`
- Modify: `docs/linux/03-boot-and-init/secure-boot-and-signed-kernels.md`
- Modify: `docs/linux/03-boot-and-init/the-kernel-image.md`

**Interfaces:**
- Consumes: `bootloaders-grub-and-friends` (Task 16) for how a command line is built.
- Produces: the `init=/bin/sh` recovery procedure, referenced again by Task 19's boot-debugging page.

### `the-kernel-command-line.md` — The Kernel Command Line **[Lab host=qemu]**

- **Opens with:** the command line is the only channel through which you can change kernel behaviour *before* any user space exists, which makes it the most useful debugging tool in the folder — and the only one that still works when the machine will not boot far enough to log in.
- **Sections:** `## How it reaches the kernel` (built by the loader, placed where the boot protocol says, echoed into `/proc/cmdline`); `## How it is parsed` (`__setup` and `early_param` register handlers; `parse_early_param()` runs before most of the kernel is up, `parse_args()` later; unrecognised `key=value` pairs are passed on to init as environment, which is why `systemd.*` parameters work at all — **verify these function names at v6.18**); `## The parameters worth knowing` (a table: `root=`, `rootfstype=`, `init=`, `console=`, `quiet`, `loglevel=`, `nokaslr`, `maxcpus=`, `nosmp`, `initcall_debug`, `earlyprintk=`, `systemd.unit=`, `single`/`emergency` — each with what it does and when you would reach for it); `## Module parameters on the command line` (`modulename.param=value`); `## Setting one for a single boot` (the GRUB `e` route, and the QEMU `-append` route — same parameters, different delivery).
- **Anchor:** the parameter table.
- **Lab** — `<Lab host="qemu" title="Change kernel behaviour without rebuilding" time="10 min">`: boot the canonical invocation three times with different `-append` values — first plain, then adding `initcall_debug loglevel=8` and observing the per-initcall lines, then adding `init=/bin/sh` and landing directly in a shell with no `/init`. Show the expected distinguishing output line for each. Close with `cat /proc/cmdline` inside the guest confirming what was passed.
- **KernelFacts:** `structure` — `[["saved_command_line", "init/main.c — the kernel's copy of what it was given"]]` (**verify**); `path` — `"loader builds the string → boot protocol → parse_early_param() → parse_args() → leftovers passed to init"`; `observe` — `cat /proc/cmdline`; `trap` — "An unrecognised parameter is not an error. The kernel silently hands anything it does not recognise to init as an environment variable, so a typo like `nokalsr` disables nothing and reports nothing."
- **References:** `https://docs.kernel.org/admin-guide/kernel-parameters.html` (the complete list — the reference you actually keep open); `man 7 kernel-command-line` (systemd's view, including the `systemd.*` parameters); `https://docs.kernel.org/admin-guide/init.html` (the `init=` escape hatch and the failures it diagnoses).

### `secure-boot-and-signed-kernels.md` — Secure Boot and Signed Kernels

- **Opens with:** Secure Boot answers one narrow question — is the thing about to be executed signed by a key this machine trusts? — and understanding exactly how narrow that question is prevents both the "it makes my machine secure" mistake and the "it is DRM" one.
- **Sections:** `## The chain of trust` (firmware keys: PK, KEK, db, dbx → shim → boot loader → kernel → modules, each link verifying the next); `## shim, and why it exists` (a small Microsoft-signed loader distributions use so they need not get every kernel signed; MOK enrolment for your own keys); `## Signed modules` (`CONFIG_MODULE_SIG` and `CONFIG_MODULE_SIG_FORCE`; a build-time key; the reason an out-of-tree module fails to load on a Secure Boot machine); `## Lockdown` (integrity and confidentiality modes; what they forbid — `/dev/mem`, unsigned modules, `kexec` of unsigned images, some `ioctl`s and BPF paths — and why `nokaslr` and kernel debugging get blocked); `## What it does not protect against` (anything after the last verified handoff: a signed kernel with a vulnerability, a compromised initramfs on some configurations, or an attacker with physical access to firmware settings); `## Doing this in the lab` (a `:::danger` block: enrolling a wrong key, or clearing PK, can make a physical machine unbootable and on some vendors' firmware is not recoverable from Linux — do it in a VM with OVMF, not on your laptop).
- **Anchor:** Mermaid `flowchart LR` of the trust chain, each arrow labelled with what verifies what and using which key store.
- **KernelFacts:** `structure` — `[["CONFIG_MODULE_SIG_FORCE", "refuse unsigned modules"], ["/sys/kernel/security/lockdown", "the active lockdown mode"]]`; `path` — `"firmware db → shim → loader → kernel signature check → module signature check"`; `observe` — `mokutil --sb-state` and `cat /sys/kernel/security/lockdown`; `trap` — "Secure Boot verifies signatures, not behaviour. A signed kernel with a known vulnerability passes every check, which is why `dbx` — the revocation list — is the part that actually does the work over time."
- **References:** `https://docs.kernel.org/admin-guide/module-signing.html` (the module-signing mechanism and the config symbols); `https://www.rodsbooks.com/efi-bootloaders/secureboot.html` (the clearest practical account of shim and MOK enrolment); `https://man7.org/linux/man-pages/man7/kernel_lockdown.7.html` (exactly what lockdown forbids, which is the list you will consult when kernel debugging stops working).

### `the-kernel-image.md` — Inside `bzImage` **[WAH]** **[Misc]**

- **Opens with:** three files people use interchangeably — `vmlinux`, `vmlinuz`, `bzImage` — are three different things with different jobs, and the confusion costs people hours in GDB. This page opens the image up.
- **Sections:** `## The three names` (a table: `vmlinux` = ELF with symbols, not bootable, for GDB and `objdump`; `bzImage` = setup code + compressed payload, bootable, what the loader loads; `vmlinuz` = the distribution's installed name for a `bzImage`); `## The layout of a bzImage` (the real-mode setup code, the setup header, then the compressed payload with its self-extracting decompressor); `## The setup header` (a WaveDrom `reg` strip of the fields that matter — `boot_flag`, `header`, `version`, `loadflags`, `code32_start`, `ramdisk_image`, `ramdisk_size`, `cmd_line_ptr` — **verify every field name and its offset against `arch/x86/boot/header.S` and the boot-protocol documentation at v6.18**); `## Who fills the header in` (the loader; this table *is* the loader/kernel contract); `## Decompression` (the payload is compressed with whatever `CONFIG_KERNEL_*` chose — gzip, xz, zstd; the decompressor runs, relocates, and jumps into the kernel proper); `## What actually happens` **[WAH]** — `file /boot/vmlinuz-$(uname -r)`, `extract-vmlinux` from `scripts/`, then `file` on the result, as real ` ```text ` output — showing a reader they can get from an installed image back to an ELF kernel; `## Misconceptions` **[Misc]** — (1) "`bzImage` means bzip2" — it means *big zImage*, a historical size-limit distinction, nothing to do with bzip2; (2) "`vmlinuz` can be loaded into GDB" — not usefully; you need `vmlinux` from the same build; (3) "the kernel is decompressed by the boot loader" — it decompresses itself.
- **Anchor:** the WaveDrom setup-header strip, plus the three-name table.
- **KernelFacts:** `structure` — `[["struct setup_header", "arch/x86/include/uapi/asm/bootparam.h"]]`; `path` — `"loader fills setup_header → jumps to code32_start → decompressor → relocation → startup_64() → start_kernel()"` (**verify `startup_64`**); `observe` — `file /boot/vmlinuz-$(uname -r)`; `trap` — "`bzImage` is not bzip2-compressed and never was. The `bz` is 'big zImage' — the format that lifted the old 512 KB limit."
- **References:** `https://docs.kernel.org/arch/x86/boot.html` (the boot protocol and every setup-header field, in its primary source); `https://docs.kernel.org/arch/x86/zero-page.html` (the `boot_params` page the kernel reads afterwards); `scripts/extract-vmlinux` in the source tree, via `<Src file="scripts/extract-vmlinux" />` (the tool the [WAH] section uses).

- [ ] **Step 1: Verify the setup-header field names and the parsing function names** against the v6.18 source and `Documentation/arch/x86/boot.rst` before drawing the WaveDrom strip. A wrong field offset here is the kind of error a reader cannot detect.
- [ ] **Step 2: Write all three pages** to the briefs above.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 4: Commit**

```bash
git add docs/linux/03-boot-and-init
git commit -m "docs: write kernel command line, Secure Boot, and bzImage pages"
```

---

## Task 18: Folder 03 — early boot, `start_kernel`, and initramfs

**Files:**
- Modify: `docs/linux/03-boot-and-init/early-boot-and-arch-setup.md`
- Modify: `docs/linux/03-boot-and-init/start-kernel-and-initcalls.md`
- Modify: `docs/linux/03-boot-and-init/initramfs-and-early-userspace.md`

**Interfaces:**
- Consumes: `the-kernel-image` (Task 17) — this task picks up exactly where decompression ends.
- Produces: the initcall-level model that folder 14's driver probing will later depend on.

### `early-boot-and-arch-setup.md` — Early Boot: Getting to C

- **Opens with:** between "the decompressor jumps into the kernel" and "C code runs" there is a stretch of assembly that exists because the CPU does not start in the mode the kernel needs. Naming what it does removes the last piece of boot that feels like magic — and it is aggressively architecture-specific, so this page says x86-64 in nearly every paragraph.
- **Sections:** `## Why any assembly at all` (the CPU starts in a mode with no paging and a 32-bit or 16-bit view; C needs a stack, a flat address space, and known register state); `## The x86-64 sequence` (16-bit real-mode entry → protected mode → early identity-mapped page tables → enable PAE and long mode → 64-bit entry at `startup_64` → `x86_64_start_kernel()` → `start_kernel()`; **verify each symbol at v6.18**); `## The early page tables` (identity mapping so that the same addresses work before and after paging is enabled, then the switch to the real kernel mapping); `## Relocation and KASLR` (the kernel is built for one address and may be placed elsewhere; the relocation pass fixes it up; `nokaslr` disables it and is why GDB works — tie back to the debugging page); `## What is not available yet` (no memory allocator, no printk to a console until it is set up, no interrupts — which is why bugs here are so unpleasant and why `earlyprintk` exists); `## arm64 in contrast` — a `:::note`: entry is already in the right execution state, a much shorter head sequence, and no real-mode ancestry at all.
- **Anchor:** Mermaid `flowchart TB` of the mode transitions, with each node labelled by the CPU mode and the symbol that runs there. Caption: "The x86-64 mode transitions between the decompressor and the first line of C."
- **KernelFacts:** `structure` — `[["startup_64", "arch/x86/kernel/head_64.S"], ["x86_64_start_kernel()", "arch/x86/kernel/head64.c"]]` (**verify**); `path` — `"decompressor → startup_64 → early page tables → long mode → x86_64_start_kernel() → start_kernel()"`; `observe` — `dmesg | head -20` (the first lines are printed just after this stage); `trap` — "KASLR is why your GDB breakpoints miss. The kernel you built and the kernel that is running have the same code at different addresses, and `nokaslr` is not a security decision in the lab — it is a prerequisite."
- **References:** `https://docs.kernel.org/arch/x86/boot.html` (where the boot protocol hands over, which is where this page starts); `https://docs.kernel.org/admin-guide/kernel-parameters.html` (`earlyprintk` and `nokaslr`, the two parameters that make this stage observable); `https://lwn.net/Articles/569635/` (KASLR's introduction and rationale — note the date relative to v6.18 in the annotation).

### `start-kernel-and-initcalls.md` — `start_kernel` and the Initcall Order **[Lab host=qemu]**

- **Opens with:** `start_kernel()` is the closest thing the kernel has to a `main()`, and reading it in order is the single best way to learn what a kernel *is*: each call brings one subsystem from unusable to usable, in an order that is almost entirely forced by dependencies.
- **Sections:** `## Reading `start_kernel()` in order` (a table of the notable calls in sequence with one line each — architecture setup, boot memory, page allocator, scheduler init, timers, IRQ init, `console_init()`, then `rest_init()`. **Read the real v6.18 function and build the table from it; do not reproduce a remembered order.**); `## `rest_init()` and the first threads` (PID 1 is created as a kernel thread that later becomes user-space init; `kthreadd` becomes PID 2; the boot CPU becomes the idle task — this three-way split surprises people and is worth stating plainly); `## Initcall levels` (the ordered list — `early`, `core`, `postcore`, `arch`, `subsys`, `fs`, `device`, `late` — as a table with what belongs at each level and the macro that puts it there; the linker collects them into sections and `do_initcalls()` walks them in order); `## Why order is a level, not a list` (a driver cannot say "after that other driver"; it declares a *phase*, and within a phase order is link order — which is why link order occasionally matters and why deferred probing exists); `## Watching it happen` (`initcall_debug` prints every initcall with its duration; this is also the standard boot-time-profiling tool).
- **Anchor:** the initcall-level table (level, macro, what belongs there, example).
- **Lab** — `<Lab host="qemu" title="Watch every initcall run" time="10 min">`: boot the canonical invocation plus `-append "... initcall_debug loglevel=8"`; expected output is lines of the form `calling <symbol>+0x0/0x... @ 1` and `initcall <symbol>+0x0/0x... returned 0 after N usecs`; then inside the guest, `dmesg | grep initcall | sort -t' ' -k... ` — simpler: `dmesg | grep "returned 0 after" | sort -rn -k8` to find the slowest, with a note that the exact field index depends on the format, so check before relying on it.
- **KernelFacts:** `structure` — `[["start_kernel()", "init/main.c"], ["do_initcalls()", "init/main.c"]]`; `path` — `"start_kernel() → subsystem init in dependency order → rest_init() → kernel_init() → do_initcalls() → /init"`; `observe` — boot with `initcall_debug`, then `dmesg | grep initcall | tail`; `trap` — "Initcall levels order *phases*, not drivers. Two drivers at the same level run in link order, which is why a driver that needs another's resource uses deferred probing rather than an ordering assumption."
- **References:** `<Src file="init/main.c" symbol="start_kernel" />` (the function this page is a reading of — the primary source); `https://docs.kernel.org/core-api/index.html` (the subsystems `start_kernel` brings up, in the order it brings them); `https://docs.kernel.org/driver-api/driver-model/porting.html` (deferred probing, and why initcall order is not a dependency mechanism).

### `initramfs-and-early-userspace.md` — initramfs and Early User Space **[WAH]** **[Lab host=any-linux]**

- **Opens with:** the chicken-and-egg the initramfs exists to break — to mount the real root you need a driver for the controller it is on, and that driver may be a module living on the root filesystem you cannot mount yet. The answer is a tiny filesystem the kernel already has in memory.
- **Sections:** `## rootfs, ramfs, initramfs — three words, one mechanism` (rootfs is a `tmpfs` instance the kernel always has; the initramfs cpio is unpacked into it; there is no block device and no filesystem image involved, which is the detail that makes the rest make sense); `## The cpio format` (`newc`, why cpio rather than tar, and that the kernel's unpacker is deliberately minimal); `## What `/init` in a distribution's initramfs actually does` (load modules for storage and, if needed, the network; assemble md/LVM/LUKS; find `root=`; mount it; hand over); `## How yours is generated` (`dracut` on Fedora/RHEL, `mkinitcpio` on Arch, `initramfs-tools` on Debian — all producing the same artefact from different config; and the *host-specific* versus *generic* build modes, which is why an initramfs from one machine may not boot another); `## Opening one up` (the extraction commands, including the fact that modern images may be a concatenation of an uncompressed microcode segment and a compressed main archive — `lsinitrd`/`lsinitramfs` handle this and raw `zcat` may not); `## What actually happens` **[WAH]** — "the initramfs boots the system": it does not; it prepares the conditions under which the real root can be mounted, then removes itself. Show `lsinitrd | head` or `lsinitramfs | head` real output and point at the module list as the whole reason it exists; `## When it goes wrong` (the initramfs emergency shell: what it means, and the two commands worth running there — `cat /proc/cmdline` and `blkid`).
- **Anchor:** Mermaid `flowchart LR` — cpio in memory → unpacked into rootfs (tmpfs) → `/init` loads modules → real root mounted at `/sysroot` → `switch_root` → the initramfs's memory is freed. Caption: "The initramfs's whole life, from a cpio in RAM to the memory being reclaimed."
- **Lab** — `<Lab host="any-linux" title="Look inside your distribution's initramfs" time="10 min">`: `lsinitrd /boot/initramfs-$(uname -r).img | head -40` (Fedora) or `lsinitramfs /boot/initrd.img-$(uname -r) | head -40` (Debian/Ubuntu); expected output includes `/init` and a `lib/modules/.../kernel/drivers/` tree; then count the modules and compare with `lsmod | wc -l`. The "if it fails" line covers a WSL2 machine with no `/boot` initramfs at all — which is itself the lesson from Task 12's capability table.
- **KernelFacts:** `structure` — `[["populate_rootfs()", "init/initramfs.c"]]` (**verify the current function name at v6.18**); `path` — `"kernel unpacks cpio into rootfs → runs /init → modules loaded → real root mounted → switch_root"`; `observe` — `lsinitrd` or `lsinitramfs` on your own image; `trap` — "An initramfs built on your machine is often built *for* your machine. A generic image boots anywhere and is larger; a host-only image is small and can fail to boot the same distribution on different hardware."
- **References:** `https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html` (the kernel's own three-way distinction, which this page's first section follows); `man 8 dracut` and `man 8 mkinitcpio` (the two generators most readers actually have, and their host-only versus generic modes); `https://docs.kernel.org/driver-api/early-userspace/early_userspace_support.html` (the cpio contract the kernel enforces).

- [ ] **Step 1: Read the real `start_kernel()` at v6.18** and build the ordering table from it. This is the one page in the folder where a remembered order will be wrong.
- [ ] **Step 2: Verify** `startup_64`, `x86_64_start_kernel`, `rest_init`, `kernel_init`, `do_initcalls`, and `populate_rootfs` against Elixir v6.18.
- [ ] **Step 3: Write all three pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/03-boot-and-init
git commit -m "docs: write early boot, start_kernel, and initramfs pages"
```

---

## Task 19: Folder 03 — PID 1 and systemd

**Files:**
- Modify: `docs/linux/03-boot-and-init/switch-root-and-pid-1.md`
- Modify: `docs/linux/03-boot-and-init/systemd-the-model.md`
- Modify: `docs/linux/03-boot-and-init/systemd-in-practice-and-boot-debugging.md`

**Interfaces:**
- Consumes: `initramfs-and-early-userspace` and `the-kernel-command-line` (Tasks 17, 18) — the last page declares both as prerequisites.
- Produces: folder 03 complete; the boot-debugging playbook that folder 17 will later extend with crash analysis.

### `switch-root-and-pid-1.md` — `switch_root` and PID 1 **[WAH]** **[Misc]**

- **Opens with:** three operations that are constantly confused — `chroot`, `pivot_root`, and `switch_root` — do three different things, and the difference matters precisely at the moment the initramfs hands over. Then: PID 1 is not a special program, it is a normal process the kernel treats specially, and the ways in which it is special are all consequences of one fact — it has no parent.
- **Sections:** `## Three ways to change what `/` means` (a table: `chroot` changes the calling process's root and leaves the old filesystem mounted and reachable; `pivot_root` moves the *mount namespace's* root and gives you the old one to unmount; `switch_root` is a userspace convenience that moves the mount points, deletes the initramfs contents to free the memory, and `exec`s the new init — with the note that only the middle one is a syscall); `## Why the initramfs deletes itself` (the memory is a `tmpfs` and is not freed until its contents are gone — this is why `switch_root` removes files rather than just unmounting); `## What makes PID 1 special` (a table: default signal dispositions do not apply, so it ignores signals it has no handler for — which is why `kill -9 1` does nothing; it inherits every orphan and must reap them; if it exits, the kernel panics); `## `PR_SET_CHILD_SUBREAPER`` (the mechanism that lets a non-PID-1 process act as a reaper for its subtree, which is how container supervisors and session managers work); `## What actually happens` **[WAH]** — `kill -9 1` on a live system. Nothing happens, and the reason is a two-line rule in the signal code, not a permission check. Then show the panic message a kernel prints when init *does* exit, as a ` ```text ` block, so the reader recognises it; `## Misconceptions` **[Misc]** — (1) "PID 1 is unkillable because it is root" — no, because the kernel does not deliver signals to it that it has not asked for; (2) "`switch_root` is a syscall" — it is a userspace program built on `pivot_root` and `chroot`; (3) "zombies are a leak" — they are a bookkeeping requirement, covered in folder 06.
- **Anchor:** the three-way comparison table (`chroot` / `pivot_root` / `switch_root`).
- **KernelFacts:** `structure` — `[["SYSCALL_DEFINE2(pivot_root, ...)", "fs/namespace.c"]]` (**verify**); `path` — `"/init mounts real root at /sysroot → switch_root → pivot_root(2) → exec /sbin/init as PID 1"`; `observe` — `ps -p 1 -o comm= && ls -l /proc/1/exe`; `trap` — "If PID 1 exits for any reason, the kernel panics — deliberately. There is no recovery path, because there is nothing left to recover *to*."
- **References:** `man 2 pivot_root` (the actual syscall, and how it differs from `chroot`); `man 8 switch_root` (the userspace tool, and why it deletes the old root); `<Src file="kernel/exit.c" />` (where the "attempted to kill init" panic lives — verify the exact message string before quoting it).

### `systemd-the-model.md` — systemd: The Model **[WAH]** **[Misc]**

- **Opens with:** systemd is not a shell script replacement; it is a dependency resolver with a process supervisor attached. Almost everything confusing about it comes from one distinction, and the page's job is to make that distinction stick: **`Requires=` and `After=` are different axes and neither implies the other.**
- **Sections:** `## Units` (a table of the types worth knowing — `.service`, `.socket`, `.target`, `.mount`, `.timer`, `.path`, `.slice` — one line each); `## Requirement and ordering are orthogonal` (the page's core. `Requires=` says "if I start, that must also start"; `After=` says "if we both start, it goes first". `Requires=` without `After=` is a race, and it is the single most common systemd bug in hand-written units. Give a two-by-two table of the four combinations and what each actually produces); `## Targets are not runlevels` (a target is a synchronisation point with no process of its own; the runlevel aliases exist for compatibility and mislead people into thinking they are ordered levels); `## The transaction` (at boot, the manager computes a *job set* from the requested target and the dependency graph, resolves conflicts, and then runs jobs as their ordering allows — which is why boot is parallel by default and why `After=` is what serialises anything); `## Where units come from and who wins` (`/usr/lib/systemd/system` shipped, `/etc/systemd/system` local override, drop-in `.d/` directories, and `systemctl cat` as the way to see the effective unit); `## What actually happens` **[WAH]** — `systemctl start foo`: not "run foo", but "add a start job for `foo.service` to the transaction, pull in its requirements, order it against everything already queued, and execute". Show a real `systemctl list-jobs` during boot or a real `systemd-analyze critical-chain` as ` ```text ` output; `## Misconceptions` **[Misc]** — (1) "`After=` makes it a dependency" — it only orders, and a unit ordered after something that never starts simply starts immediately; (2) "targets are runlevels" — no; (3) "systemd is PID 1 doing everything" — the manager delegates to per-unit processes and a per-unit cgroup, which is the tie-in to folder 15.
- **Anchor:** the requirement-versus-ordering two-by-two table. Add a Mermaid `flowchart` of a small unit graph (three services and a target) showing which edges are ordering and which are requirement, drawn with different arrow styles.
- **KernelFacts:** `structure` — `[["/usr/lib/systemd/system/*.service", "shipped units"], ["/etc/systemd/system/*", "local overrides and drop-ins"]]`; `path` — `"PID 1 systemd → default.target → transaction computed → jobs run in ordering-constraint order"`; `observe` — `systemd-analyze critical-chain`; `trap` — "`Requires=` without `After=` starts both units at once. The dependency is satisfied, the ordering is not, and the failure is intermittent — which is why it survives testing."
- **References:** `https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html` (the directive reference, and the precise definitions of `Requires=`/`Wants=`/`After=`); `https://www.freedesktop.org/software/systemd/man/latest/bootup.html` (the boot-up target sequence, which is the map for the whole page); `https://0pointer.de/blog/projects/systemd.html` (the original rationale — old, and still the clearest statement of why socket activation changes the dependency problem).

### `systemd-in-practice-and-boot-debugging.md` — systemd in Practice, and Debugging a Broken Boot **[Lab host=qemu]**

- **Opens with:** the payoff page for the whole folder — a boot that fails is a boot that stopped at a known stage, and every stage in this folder leaves evidence. This page is the playbook, ordered by how far the machine got.
- **Sections:** `## Socket and path activation` (a service started on demand when something connects or a file appears; why this removes most ordering problems rather than solving them); `## journald` (structured logs, `journalctl -b`, `-b -1` for the previous boot, `-p err`, `-u`, and the fact that persistence is a configuration choice — a machine with volatile logs loses exactly the boot you wanted); `## A unit per cgroup` (each service gets a cgroup, which is how `systemctl status` knows every process belongs to the unit even after double-forks; forward reference to folder 15 in prose); `## The playbook` — a table ordered by symptom: no firmware output; loader menu missing; kernel panic "unable to mount root"; dropped to the initramfs emergency shell; boots to `emergency.target`; boots but one service fails; boots but is slow. Each row: what it proves about earlier stages, the first command or parameter to try, and the page in this folder that covers it; `## The four parameters worth memorising` (`init=/bin/sh`, `systemd.unit=rescue.target`, `systemd.log_level=debug`, `earlyprintk=serial,ttyS0,115200` — with a `:::tip` that the first one is the escape hatch and works when nothing else does); `## Measuring a slow boot` (`systemd-analyze`, `blame`, `critical-chain`, and the honest caveat that `blame` ranks by duration and not by whether anything was waiting on it).
- **Anchor:** the symptom → stage → first move playbook table.
- **Lab** — `<Lab host="qemu" title="Break a boot, then diagnose it" time="15 min">`: boot the full-system Debian VM from Task 12, take a snapshot, then break it deliberately by adding a bad `root=` UUID to the command line for one boot; observe the initramfs emergency shell; run `cat /proc/cmdline` and `blkid` there to find the real UUID; boot again correctly; roll the snapshot back. Include a `:::danger` block: doing this by editing a real machine's persistent boot configuration rather than a single boot entry leaves an unbootable system, and the snapshot is what makes it safe.
- **KernelFacts:** `structure` — `[["journalctl -b", "this boot's log"], ["systemd-analyze critical-chain", "the ordering path that determined boot time"]]`; `path` — `"symptom → the stage it proves was reached → the parameter or command for that stage → the page that explains it"`; `observe` — `journalctl -b -p err`; `trap` — "`systemd-analyze blame` ranks services by how long they took, not by whether anything waited for them. A slow service off the critical chain costs you nothing, and optimising it is wasted work — `critical-chain` is the one that answers the question."
- **References:** `man 1 journalctl` (the flags this playbook depends on, especially `-b -1`); `man 1 systemd-analyze` (`blame` versus `critical-chain`, and why the distinction matters); `https://freedesktop.org/wiki/Software/systemd/Debugging/` (the project's own debugging guide, which is the source of the parameter list).

- [ ] **Step 1: Verify the `pivot_root` definition site and the init-exit panic string** at v6.18 before quoting either.
- [ ] **Step 2: Write all three pages** to the briefs above.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`
Expected: folder 03 fully written (12 pages), zero findings.

- [ ] **Step 4: Commit**

```bash
git add docs/linux/03-boot-and-init
git commit -m "docs: write PID 1, systemd model, and boot debugging pages"
```

---

## Task 20: Folder 04 — where Linux sits, and the source tree

**Files:**
- Modify: `docs/linux/04-kernel-architecture-and-idioms/monolithic-with-modules.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/the-source-tree-map.md`

**Interfaces:**
- Consumes: `computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid` (Task 5, already in `related:`), `linux/overview/the-kernel-userspace-boundary` (Task 6, the declared prerequisite), and the Graphviz SVG from Task 2.
- Produces: `the-source-tree-map`, the lookup page the rest of folder 04 and every later folder point at.

### `monolithic-with-modules.md` — Monolithic, With Modules **[WAH]** **[Misc]**

- **Opens with:** Linux made one structural decision that explains most of what follows: every subsystem runs in one address space at one privilege level, calling each other with ordinary function calls. Modules do not change that — they change *when* code is linked in, not where it runs.
- **Sections:** `## One address space` (a filesystem calling into the block layer is a function call; there is no message passing, no marshalling, and no boundary crossing between kernel subsystems — this is the source of both the performance and the fragility); `## What modules actually are` (relocatable object code linked into the running kernel at load time, with the same authority as everything else. Build-time and deploy-time flexibility, not isolation); `## The honest trade-off` (a driver bug is a kernel bug: a null dereference in a USB driver is an oops in kernel context, and depending on where it happens, the machine is now unreliable. State it plainly — this page is where readers should acquire the right level of respect for kernel code); `## Why Linux chose it, and why it held` (development speed, no IPC design tax, and the fact that in-tree drivers can be fixed by whoever changes the interface. Then the counter-pressure: `CONFIG_STRICT_MODULE_RWX`, lockdown, signed modules, and the Rust effort as attempts to buy back safety without buying the microkernel); `## Where the theory lives` — link `../../computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid.md` and do not re-argue it; `## What actually happens` **[WAH]** — `lsmod` and `/proc/modules` read honestly: the `Used by` column is a reference count, not an isolation boundary, and a module with a non-zero count cannot be removed because something holds a reference — not because the kernel is protecting you from a fault; `## Misconceptions` **[Misc]** — (1) "modules are sandboxed" — no; (2) "a module crash only kills the module" — no, it is a kernel fault, and `rmmod` afterwards usually will not help; (3) "monolithic means one huge file" — it means one address space; the source is thousands of files and most of it is optional.
- **Anchor:** Mermaid `flowchart LR` contrasting one in-kernel call (VFS → ext4 → block, three function calls, one address space) with the microkernel equivalent (four boundary crossings), captioned "The same request, served monolithically and served by user-space servers."
- **KernelFacts:** `structure` — `[["struct module", "include/linux/module.h"]]`; `path` — `"insmod → sys_finit_module() → load_module() → module relocated and linked → module_init()"` (**verify at v6.18; module loading lives under `kernel/module/`**); `observe` — `lsmod | head && cat /proc/modules | head -3`; `trap` — "A loaded module has exactly the same privileges as the rest of the kernel. `lsmod`'s `Used by` column counts references, and nothing in the module system limits what a module may touch."
- **References:** `https://docs.kernel.org/admin-guide/module-signing.html` (what signing does and does not constrain — the concrete limit of module trust); `<Src file="kernel/module/main.c" symbol="load_module" />` (the function that does the linking this page describes); `https://lwn.net/Articles/945300/` (Rust for Linux status — check the article date against v6.18 and say so in the annotation).

### `the-source-tree-map.md` — The Source Tree, Mapped

The page a reader returns to for years. Its job is lookup, not narrative.

- **Opens with:** the tree is not organised by importance or by subject; it is organised by *what kind of thing* the code is. Once that is clear, "where does the answer to this question live" becomes mechanical.
- **Sections:** `## The whole tree, one line each` (every top-level directory, verified against v6.18); `## The four that matter most` — a `###` each for `kernel/`, `mm/`, `fs/`, `drivers/`, naming the two or three subdirectories or files inside each that a reader will actually open (for example `kernel/sched/`, `kernel/locking/`, `kernel/time/`; `mm/page_alloc.c`, `mm/slub.c`, `mm/memory.c`; `fs/namei.c`, `fs/read_write.c`, `fs/ext4/`; `drivers/base/` as the device model). **Verify every path.**; `## Where a question's answer lives` — the page's centrepiece: a two-column lookup table, roughly fifteen rows, of the form "How does the scheduler pick a task? → `kernel/sched/`", "What happens on a page fault? → `mm/memory.c` and `arch/x86/mm/fault.c`", "Where is a syscall defined? → the subsystem that owns it, found with `git grep SYSCALL_DEFINE`", "What does this `CONFIG_` do? → the nearest `Kconfig`", and so on; `## `arch/` and the portability line` (what is architecture-specific and what is not, and the convention that `include/asm-generic/` provides the fallback); `## `include/` layout` (`include/linux/` internal, `include/uapi/` the user-space ABI, `include/asm-generic/`; the `uapi` split is a real distinction with real rules and is worth one paragraph); `## Reading the tree at scale` (the anchor figure, and the six-box simplification beside it).
- **Anchor — two figures, deliberately paired:**
  1. `<Figure src="/img/linux/kernel-architecture-and-idioms/linux-kernel-diagram.svg" alt="A directed graph of Linux kernel subsystems and their dependencies, from system calls down to hardware interfaces" caption="The real subsystem graph. Click to zoom — it is not meant to be read at this size; it is meant to show the scale of what the six boxes below are hiding." source="Graphviz gallery" href="https://graphviz.org/Gallery/directed/Linux_kernel_diagram.svg" />` — zoom is provided automatically by `docusaurus-plugin-image-zoom`, whose selector already covers `.kb-figure__plate img`.
  2. A Mermaid `flowchart TB` of six boxes only — system call interface, process management, memory management, VFS, network stack, device drivers — over a hardware bar. Caption: "The six boxes to actually hold in your head."
  The two together are the point: the SVG shows the real thing, the Mermaid shows the working model.
- **KernelFacts:** `structure` — `[["MAINTAINERS", "the file that maps any path to the people and lists that own it"]]`; `path` — `"a question → the kind of thing it is → the top-level directory → git grep within it"`; `observe` — `./scripts/get_maintainer.pl -f mm/memory.c`; `trap` — "`drivers/` is more than half the tree by line count and almost none of it is worth reading in order. Depth in `drivers/` is reached through one device you care about, never by browsing."
- **References:** `<Src file="MAINTAINERS" />` (the authoritative map from path to owner, and a surprisingly good index of what subsystems exist); `https://docs.kernel.org/process/index.html` (how the tree is organised socially, which explains a lot of how it is organised physically); `https://elixir.bootlin.com/linux/v6.18/source` (the cross-referencer, and the fastest way to answer a "where is this defined" question without a local clone).

- [ ] **Step 1: Verify the anchor figure renders and zooms** — after writing, run `npm run start`, open the page, and confirm the SVG displays and that clicking it opens the zoom overlay. A zoom selector mismatch is invisible in a build.
- [ ] **Step 2: Verify every path** in the lookup table against v6.18. This page is a reference; a wrong path here is a wrong path a reader will trust for months.
- [ ] **Step 3: Write both pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/04-kernel-architecture-and-idioms
git commit -m "docs: write monolithic-with-modules and the source tree map"
```

---

## Task 21: Folder 04 — Kconfig, modules, and the module ABI

**Files:**
- Modify: `docs/linux/04-kernel-architecture-and-idioms/kconfig-and-kbuild.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/modules-in-practice.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/exported-symbols-and-the-module-abi.md`

**Interfaces:**
- Consumes: `the-source-tree-map` (Task 20) and `01/building-a-kernel` (Task 10) — `kconfig-and-kbuild` declares both as prerequisites.
- Produces: the out-of-tree module build recipe reused by folder 14's driver labs later.

### `kconfig-and-kbuild.md` — Kconfig and Kbuild

- **Opens with:** `.config` is the most consequential file in the kernel tree: it decides which of ~20,000 options exist in your kernel, and it is *generated*, not written. Understanding the pipeline from a `Kconfig` symbol to a compiled object is what turns `#ifdef CONFIG_FOO` from noise into information.
- **Sections:** `## The Kconfig language` (`config` entries with `bool`/`tristate`/`int`/`string`, `depends on`, `select` versus `imply`, `default`, and `help` — a small real example from the tree, quoted as ` ```text ` since there is no Kconfig grammar in Prism); `## Why `m` exists` (tristate: built in, built as a module, or absent — and the fact that "absent" means the code is not compiled at all, which is why a missing feature is not a runtime setting); `## `select` is the footgun` (`select` forces a symbol on without checking *its* dependencies, which is how invalid configs get produced; `depends on` is the safe direction — one paragraph, because readers meet this in real bug reports); `## From symbol to object file` (the `.config` becomes `include/config/auto.conf` and `include/generated/autoconf.h`; Kbuild reads `obj-$(CONFIG_FOO) += foo.o` in each `Makefile`, so a symbol's value literally selects whether an object is built — show a real three-line `Makefile` fragment); `## Reading past `#ifdef CONFIG_`` (the practical skill: check the symbol's value in *your* `.config` first, then read only the live branch — with the `scripts/config --state` command that answers it in one line); `## The `make *config` family` (`menuconfig`, `nconfig`, `xconfig`, `olddefconfig`, `savedefconfig`, `localmodconfig` — a table with what each is for, and a `:::tip` that `savedefconfig` is how you turn a 12,000-line `.config` into a reviewable minimal diff).
- **Anchor:** Mermaid `flowchart LR` — `Kconfig` files → `make menuconfig` → `.config` → `auto.conf` + `autoconf.h` → `Makefile` `obj-$(CONFIG_*)` → `.o` → `vmlinux` / `.ko`. Caption: "How one Kconfig symbol becomes, or fails to become, an object file."
- **KernelFacts:** `structure` — `[[".config", "generated; the single source of truth for a build"], ["include/generated/autoconf.h", "the C view of the same thing"]]`; `path` — `"Kconfig → .config → auto.conf/autoconf.h → obj-$(CONFIG_X) in a Makefile → object linked or omitted"`; `observe` — `./scripts/config --state CONFIG_MODULES` (or `zgrep CONFIG_MODULES /proc/config.gz` on a running system); `trap` — "A `CONFIG_` symbol set to `n` is not a disabled feature — the code was never compiled. There is no runtime switch to look for, and no error message when you look for one."
- **References:** `https://docs.kernel.org/kbuild/kconfig-language.html` (the language reference, including the `select` versus `depends on` warning this page repeats); `https://docs.kernel.org/kbuild/makefiles.html` (how `obj-$(CONFIG_*)` actually works, in its primary source); `<Src file="scripts/config" />` (the script that reads and edits `.config` non-interactively).

### `modules-in-practice.md` — Kernel Modules **[Lab host=qemu]**

- **Opens with:** a module is an object file the kernel links into itself at runtime. Writing one is the shortest path from reading about the kernel to running code inside it, and the whole lifecycle fits on one page.
- **Sections:** `## The minimum module` (a ~15-line `hello.c` with `module_init`, `module_exit`, `MODULE_LICENSE`, `MODULE_AUTHOR`, `MODULE_DESCRIPTION` and two `pr_info` calls, quoted in full as ` ```c `; plus the four-line out-of-tree `Makefile` using `-C /lib/modules/$(shell uname -r)/build M=$(PWD) modules`); `## `MODULE_LICENSE` and taint` (a non-GPL license taints the kernel, which changes what maintainers will debug and what symbols you can use; `/proc/sys/kernel/tainted` and the meaning of the common bits); `## Parameters` (`module_param`, the permission argument creating a file under `/sys/module/<name>/parameters/`, and that a writable parameter can be changed on a loaded module); `## `insmod` versus `modprobe`` (`insmod` takes a path and does nothing else; `modprobe` resolves dependencies from `modules.dep`, respects `/etc/modprobe.d/`, and is what you almost always want); `## Where the kernel keeps it` (`/proc/modules`, `lsmod`, `/sys/module/<name>/`, and the `refcnt` that decides whether `rmmod` can succeed); `## Unloading, and why it often fails` (a non-zero reference count, or a module built without unload support; `rmmod -f` is a `:::warning`, not a solution).
- **Anchor:** Mermaid `stateDiagram-v2` of a module's lifecycle: absent → loading (relocated, symbols resolved) → live (`module_init` returned 0) → in use (refcnt > 0) → unloading (`module_exit`) → absent, with the failure edge from loading back to absent when `module_init` returns an error.
- **Lab** — `<Lab host="qemu" title="Build and load your first module" time="20 min">`: write `hello.c` and the `Makefile` in the guest (or build on the host against the lab kernel's build tree), `make`, `insmod hello.ko`, `dmesg | tail -2` showing the init message, `lsmod | grep hello` showing refcnt 0, `rmmod hello`, `dmesg | tail -1` showing the exit message. The "if it fails" line covers `Invalid module format`, which means the module was built against different kernel headers than the running kernel — the concrete symptom of the next page's topic.
- **KernelFacts:** `structure` — `[["struct module", "include/linux/module.h"], ["/sys/module/<name>/parameters/", "live parameter values"]]`; `path` — `"modprobe → finit_module(2) → load_module() → relocation and symbol resolution → module_init()"` (**verify**); `observe` — `lsmod | head && cat /proc/sys/kernel/tainted`; `trap` — "`insmod` failing with `Invalid module format` is almost never a corrupt file. It means the module was built against a different kernel than the one running, and the version magic caught it."
- **References:** `https://docs.kernel.org/admin-guide/tainted-kernels.html` (every taint bit and what it tells a maintainer — the reason `MODULE_LICENSE` is not a formality); `https://docs.kernel.org/kbuild/modules.html` (the official out-of-tree build procedure this page's `Makefile` comes from); `man 8 modprobe` (dependency resolution and the configuration directory `insmod` ignores).

### `exported-symbols-and-the-module-abi.md` — Exported Symbols and the Non-Stable ABI **[WAH]** **[Misc]**

- **Opens with:** a module can only call kernel functions that have been *exported*, and the export list is a deliberate, curated interface — not an accident of linkage. Understanding it explains both why some out-of-tree drivers cannot be written at all, and why "Linux has no stable ABI" is a maintenance policy rather than a technical shortcoming.
- **Sections:** `## `EXPORT_SYMBOL` and `EXPORT_SYMBOL_GPL`` (what each does; the GPL variant refuses to resolve for a module whose `MODULE_LICENSE` is not GPL-compatible, enforced at load time; note that this is a technical mechanism carrying a legal intent and stay factual about both); `## The export list is not the API` (an exported symbol has no compatibility promise; it can change signature or vanish in the next release, and in-tree callers get updated in the same commit); `## Symbol versioning (`modversions`)` (a CRC computed from each exported symbol's *type signature*, stored in the module and checked at load; `Module.symvers`; this is what turns a silent ABI mismatch into a refused load. **Verify the current mechanism name and file at v6.18**); `## Version magic` (the `vermagic` string — kernel version, SMP, preemption model, compiler — and why it must match); `## What actually happens` **[WAH]** — an out-of-tree driver "breaking" on a kernel upgrade. Nothing broke: an internal interface changed, as it always may, and the module was built against the old one. Show a real `modinfo` output with `vermagic` and a `srcversion`, and the `Invalid module format`/`disagrees about version of symbol` messages side by side, as ` ```text `; `## Why this is consistent with "we do not break user space"` (two different audiences and two different bargains: user space cannot be rebuilt by the kernel community, in-tree kernel code can. Out-of-tree code chose to be neither); `## Misconceptions` **[Misc]** — (1) "the kernel has no ABI" — it has an extremely strict *user-space* ABI; (2) "`EXPORT_SYMBOL_GPL` is a licence check on your code" — it is a link-time check on your module's declared license string; (3) "modversions makes modules portable" — it makes incompatibility *detectable*, which is the opposite.
- **Anchor:** a table of the three checks a module must pass at load time — `vermagic`, symbol resolution, symbol CRC (modversions) — with what each catches, the exact error message it produces, and what to do about it. This table is the page's practical value.
- **KernelFacts:** `structure` — `[["EXPORT_SYMBOL_GPL", "include/linux/export.h"], ["Module.symvers", "generated CRC table for exported symbols"]]`; `path` — `"EXPORT_SYMBOL in kernel source → symbol table + CRC in vmlinux → checked at finit_module() time → module linked or rejected"`; `observe` — `modinfo <module> | head` and `grep -c EXPORT_SYMBOL /proc/kallsyms` — **verify a sensible observe command; `cat /proc/kallsyms` requires privilege and shows all symbols, not just exports**; `trap` — "`disagrees about version of symbol` is modversions working correctly. The module and the kernel have different ideas about a function's *type*, and loading it anyway would corrupt memory in a way no oops would explain."
- **References:** `<Src file="include/linux/export.h" />` (the macro definitions, which are shorter and clearer than any description of them); `https://docs.kernel.org/kbuild/modules.html` (symbol versioning, `Module.symvers`, and building against an installed kernel); `https://docs.kernel.org/process/stable-api-nonsense.html` (the kernel's own argument for why there is no stable in-kernel ABI — the primary source for this page's last section).

- [ ] **Step 1: Verify** `load_module`, the `kernel/module/` paths, `include/linux/export.h`, and the modversions mechanism at v6.18.
- [ ] **Step 2: Verify the exact error strings** quoted on the third page by reading the module loader source rather than recalling them.
- [ ] **Step 3: Write all three pages** to the briefs above.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 5: Commit**

```bash
git add docs/linux/04-kernel-architecture-and-idioms
git commit -m "docs: write Kconfig, modules, and module ABI pages"
```

---

## Task 22: Folder 04 — the kernel C dialect, data structures, and `container_of`

**Files:**
- Modify: `docs/linux/04-kernel-architecture-and-idioms/the-kernel-c-dialect.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/kernel-data-structures.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md`

**Interfaces:**
- Consumes: `the-source-tree-map` (Task 20).
- Produces: the `container_of` derivation that `kobjects-sysfs-and-the-object-model` (Task 23) depends on. Write these three in the order given — each is the previous one's prerequisite.

### `the-kernel-c-dialect.md` — The Kernel Is Not C You Know

- **Opens with:** kernel code is C, compiled by a C compiler, and yet reading it feels wrong at first. The reason is that it is *freestanding* C with a house style and a set of annotations, and once the five or six unfamiliar constructs are named, the strangeness disappears.
- **Sections:** `## Freestanding, not hosted` (no libc — `printk` not `printf`, `kmalloc` not `malloc`, `memcpy` from `lib/`; no `main`; no standard headers. The kernel provides its own of everything); `## No floating point` (kernel context does not save FPU state by default; `kernel_fpu_begin()`/`kernel_fpu_end()` exist and are for the few places that genuinely need SIMD. Say this early — it surprises people); `## The stack is 8 or 16 KB, and that is all` (`CONFIG_THREAD_SHIFT`/`THREAD_SIZE`; no large local arrays, no deep recursion, and `CONFIG_FRAME_WARN` catching the rest at compile time. **Verify the current default size for x86-64 at v6.18**); `## GCC extensions in daily use` (statement expressions `({ ... })`, `typeof`, `__attribute__((packed))`/`aligned`/`always_inline`, designated initialisers used pervasively for ops structures, and `__builtin_*`; a short real example of each); `## The annotations` (a table: `__init`, `__exit`, `__initdata` — placed in a discardable section and freed after boot; `__user` — pointer into user space, never dereferenced directly; `__percpu`, `__iomem`, `__rcu`, `__must_check`. Each row: what it means, and whether it is compiler-enforced or sparse-only); `## sparse` (`make C=1` runs it; it is what makes `__user` and `__rcu` more than comments); `## Optimisation barriers you will meet` (`READ_ONCE`/`WRITE_ONCE` and `barrier()` named here with one sentence and deferred to folder 09 in prose — do not explain memory ordering on this page).
- **Anchor:** the annotation table.
- **KernelFacts:** `structure` — `[["__init / __exit", "include/linux/init.h"], ["__user", "include/linux/compiler_types.h"]]` (**verify**); `path` — `"annotated source → compiler sections and attributes → sparse (make C=1) → linker discards __init after boot"`; `observe` — `dmesg | grep -i "freeing unused kernel"`; `trap` — "`__init` is not documentation. The function is placed in a section that is unmapped and freed once boot completes, so calling one later dereferences memory that no longer exists."
- **References:** `https://docs.kernel.org/process/coding-style.html` (the house style, which explains as much of the strangeness as the language extensions do); `https://docs.kernel.org/dev-tools/sparse.html` (what the annotations buy you, and how to run the checker); `https://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html` (the primary reference for the extensions the kernel relies on).

### `kernel-data-structures.md` — Kernel Data Structures

- **Opens with:** the kernel's containers are *intrusive*: the link fields live inside your structure rather than in a separately allocated node. That single decision — made for allocation reasons — is why kernel code is full of `container_of`, and it is the reason the next page exists.
- **Sections:** `## Intrusive, and why` (no allocation on insert, no allocation failure path on insert, one cache line for object and links; the cost is that an object's membership is baked into its type and an object can only be on as many lists as it has link fields); `## `struct list_head`` (the circular doubly-linked list; `LIST_HEAD`, `INIT_LIST_HEAD`, `list_add`, `list_add_tail`, `list_del`, `list_empty`, `list_for_each_entry`, and the `_safe` variants for iteration with deletion. A real ~12-line example with a struct that embeds one); `## `hlist`` (single-pointer head for hash buckets, halving table size, and the awkward `pprev` that follows from it); `## Red-black trees` (`struct rb_node` embedded, `rb_insert_color`, `rb_erase`, and the fact that the *search* is written by the caller — the kernel provides balancing, not comparison. Note the CFS runqueue and the VMA tree as the famous users, with the maple-tree caveat deferred to folder 08 in prose); `## `xarray`` (the replacement for `radix_tree`, indexed by unsigned long, used for the page cache and ID maps; `xa_load`, `xa_store`, `xa_erase`, and its internal locking); `## `idr`/`ida`` (allocating small unique integer IDs, which is what most "handle" allocation in the kernel actually is); `## Bitmaps` (`DECLARE_BITMAP`, `set_bit`/`test_and_set_bit`, and that the atomic variants are the ones you usually want); `## Choosing` (a table: expected size, ordered?, lookup by key?, iteration pattern → structure).
- **Anchor:** a Mermaid diagram of three structs embedding a `list_head`, with the `next`/`prev` pointers drawn between the *embedded fields* rather than between the structs — the picture that makes intrusive linking click, and the setup for the next page. Caption: "The list links point at the embedded fields, not at the objects — which is the whole problem `container_of` solves."
- **KernelFacts:** `structure` — `[["struct list_head", "include/linux/types.h"], ["struct rb_node", "include/linux/rbtree_types.h"]]` (**verify the rbtree header at v6.18 — the types were split out of `rbtree.h`**); `path` — `"embed the link field → add to the container → iterate with list_for_each_entry() → recover the object with container_of()"`; `observe` — `<Src file="include/linux/list.h" symbol="list_for_each_entry" />` — for a structural page with no runtime command, use a source pointer here and say in the row why; `trap` — "`list_del` poisons the node's pointers rather than nulling them. A use-after-free through a deleted list node faults on a recognisable poison address, which is a deliberate debugging aid, not a bug."
- **References:** `<Src file="include/linux/list.h" />` (the whole list API in one readable file — the fastest way to learn it); `https://docs.kernel.org/core-api/xarray.html` (the XArray's model and locking rules, which are not obvious from the API); `https://docs.kernel.org/core-api/idr.html` (ID allocation, and when to use `ida` instead).

### `container-of-and-embedded-structs.md` — `container_of` and Embedded Structs **[WAH]**

- **Opens with:** one macro unlocks a large fraction of the kernel. If the previous page's diagram made sense — links pointing at fields, not objects — then the question is obvious: given a pointer to the field, how do you get back to the object? The answer is arithmetic, and deriving it once is enough.
- **Sections:** `## The problem, concretely` (a `struct my_thing` embedding a `list_head`; `list_for_each_entry` hands you the embedded field's address; you want the thing); `## Deriving it` — three steps, each a small code block: (1) the field's offset within the type is a compile-time constant — `offsetof`; (2) the object's address is the field's address minus that offset; (3) wrap it so the compiler still type-checks. Then show the real macro from `include/linux/container_of.h` and read it term by term, including why the `typeof` check exists and what it catches; `## The three-subsystem tour` — the same pattern in three places, each with a real snippet: a driver walking a list of its own device structures; the VFS recovering a filesystem-specific inode from a `struct inode` (the `container_of` in an `ext4_inode_info`-style accessor); and a `kobject` embedded in a device structure, which is the next page's whole topic. **Verify each snippet against v6.18.**; `## Why this instead of a `void *data` pointer` (no extra allocation, no extra dereference, type checked at compile time, and the object cannot get separated from its links); `## What actually happens` **[WAH]** — reading a real kernel function that starts with a `container_of` call. Take a small, stable example, quote it, and walk what the compiler emits: a subtraction, folded into an addressing mode, costing nothing. The point is that this is not indirection — it is free.
- **Anchor:** a memory-layout figure — either a Mermaid `classDiagram` or a simple ASCII-in-` ```text ` layout — showing a struct's bytes with the embedded field highlighted and the offset arithmetic annotated. Caption: "The pointer you have, the offset the compiler knows, and the pointer you want."
- **KernelFacts:** `structure` — `[["container_of()", "include/linux/container_of.h"], ["offsetof()", "include/linux/stddef.h"]]` (**verify both at v6.18**); `path` — `"pointer to embedded member → minus offsetof(type, member) → pointer to containing object"`; `observe` — `<Src file="include/linux/container_of.h" symbol="container_of" />` — again a source pointer, with the row saying why there is no runtime command; `trap` — "`container_of` does not check that the pointer really is inside an object of that type. Pass a member of the wrong struct and you get a valid-looking pointer to garbage, with no fault and no warning."
- **References:** `<Src file="include/linux/container_of.h" />` (the macro itself, which is twelve lines and worth reading in full); `https://docs.kernel.org/driver-api/basics.html` (the kernel's own list of these fundamental helpers); `https://lwn.net/Articles/22195/` (a classic explanation of the intrusive-list model — old, and the model has not changed; say so in the annotation).

- [ ] **Step 1: Verify the header locations** for `container_of`, `offsetof`, `list_head`, `rb_node`, and the annotation macros at v6.18. Several of these moved between headers in the 5.x series.
- [ ] **Step 2: Write the three pages in order** — dialect, then data structures, then `container_of`. Each builds on the previous one's diagram.
- [ ] **Step 3: Check and build**

Run: `npm run check:linux && npm run build`

- [ ] **Step 4: Commit**

```bash
git add docs/linux/04-kernel-architecture-and-idioms
git commit -m "docs: write kernel C dialect, data structures, and container_of pages"
```

---

## Task 23: Folder 04 — errors, lifetime, kobjects, and what goes wrong

**Files:**
- Modify: `docs/linux/04-kernel-architecture-and-idioms/error-handling-idioms.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/reference-counting-and-lifetime.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/kobjects-sysfs-and-the-object-model.md`
- Modify: `docs/linux/04-kernel-architecture-and-idioms/memory-safety-in-kernel-c.md`

**Interfaces:**
- Consumes: `container-of-and-embedded-structs` (Task 22) — the kobject page is where that idiom pays off, and it declares it as a prerequisite alongside `reference-counting-and-lifetime`.
- Produces: folder 04 complete, and with it every Linux page in this phase.

### `error-handling-idioms.md` — Error Handling

- **Opens with:** the kernel has no exceptions, and it has one error convention that is used with unusual discipline: negative `errno` values, everywhere, from the deepest helper to the syscall return. The consistency is what makes unfamiliar kernel code readable.
- **Sections:** `## Negative errno, all the way down` (a function returning `int` returns 0 or `-E...`; the syscall layer turns the negative value into the `-1`/`errno` pair user space sees, and libc does the last step — cross-reference the boundary page); `## `ERR_PTR`, `PTR_ERR`, `IS_ERR`` (functions returning pointers cannot return `-ENOMEM`, so the kernel encodes small negative values in the last page of the address space, which no valid kernel pointer occupies. Derive it: why the top page is safe, what `IS_ERR_OR_NULL` is for, and the bug of forgetting the check); `## `goto` unwinding` (the canonical pattern: labels named for what they undo, in reverse acquisition order. Show a real ~20-line function with three acquisitions and three labels. Then say plainly why this is *correct* here rather than shameful — it is the closest C gets to RAII, it keeps the success path unindented, and every kernel reviewer expects it); `## `__must_check` and the warnings that matter` (`__must_check` on functions whose failure must not be ignored; `-Wunused-result`); `## Error propagation across layers` (returning the callee's error unchanged unless you can add information; the anti-pattern of flattening every failure to `-EIO`).
- **Anchor:** the annotated `goto`-unwinding function, with the acquisition/release pairing marked. A comparison table of the three return conventions (int errno, `ERR_PTR`, bool + out-param) with when each is used.
- **KernelFacts:** `structure` — `[["IS_ERR() / PTR_ERR() / ERR_PTR()", "include/linux/err.h"]]`; `path` — `"deep helper returns -E... → propagated up unchanged → syscall layer → user space sees -1 and errno"`; `observe` — `<Src file="include/linux/err.h" />`; `trap` — "A function returning a pointer may return an encoded error, and it is not NULL. Checking only for NULL passes an `ERR_PTR` straight into a dereference, and the fault address will look like a wild pointer near the top of the address space."
- **References:** `<Src file="include/linux/err.h" />` (the encoding, in fifteen readable lines); `https://docs.kernel.org/process/coding-style.html` (section 7, which is where the `goto` convention is stated as house policy); `man 3 errno` (the value set the kernel's negative returns come from).

### `reference-counting-and-lifetime.md` — Reference Counting and Object Lifetime

- **Opens with:** in a kernel there is no garbage collector and no scope-based destruction, and objects are reachable from several subsystems at once. Lifetime is therefore explicit, and it is nearly always a counter — which means the entire class of use-after-free bugs reduces to unbalanced get/put pairs.
- **Sections:** `## `atomic_t` was not enough` (a counter that wraps on overflow turns a leak into a use-after-free; `refcount_t` saturates instead, refuses to increment from zero, and warns — the reason it was introduced as a distinct type. State the distinction precisely: `atomic_t` is a counter, `refcount_t` is a *reference* counter with defensive semantics); `## `kref`` (a `refcount_t` plus a release callback: `kref_init`, `kref_get`, `kref_put(&obj->kref, release_fn)`; the release function is called exactly once, by whoever drops the last reference); `## Naming conventions are the documentation` (`*_get`/`*_put`, `*_grab`, functions that return a *referenced* object versus a borrowed one; the rule that a function name tells you whether you now owe a `put`); `## Where references come from` (a table of common patterns: a lookup that takes a reference before returning, an object stored in a list holding one, a `struct file` holding one on its inode); `## The two failure modes` (a missing `put` leaks — visible in `slabtop` growth over time; a missing `get` frees early — visible as a use-after-free, often far from the cause. Say that the second is far worse and far harder, which is why the conventions are enforced socially); `## RCU-protected lookup, in one paragraph` (a reference taken under `rcu_read_lock` with `*_get_unless_zero`; name it, and defer to folder 09 in prose).
- **Anchor:** Mermaid `stateDiagram-v2` of an object's life: allocated (count 1) → shared (count n) → count 1 → count 0 → release callback → freed, with the two failure edges drawn and labelled ("missed put → leaked", "missed get → freed while in use").
- **KernelFacts:** `structure` — `[["refcount_t", "include/linux/refcount.h"], ["struct kref", "include/linux/kref.h"]]`; `path` — `"kref_init() → kref_get() per new reference → kref_put() per drop → release callback at zero"`; `observe` — `slabtop -o | head` (a steadily growing cache is the signature of a leaked reference); `trap` — "`refcount_t` saturates rather than wrapping, and a saturated counter never reaches zero. The object leaks — deliberately — because leaking is the safe failure and a wrapped counter is an exploitable one."
- **References:** `https://docs.kernel.org/core-api/refcount-vs-atomic.html` (the kernel's own statement of why the two types differ, including the ordering guarantees each provides); `<Src file="include/linux/kref.h" />` (the whole API, short enough to read at once); `https://lwn.net/Articles/728626/` (`refcount_t`'s introduction and the vulnerability class that motivated it).

### `kobjects-sysfs-and-the-object-model.md` — kobjects, ksets, and sysfs **[WAH]** **[Lab host=any-linux]**

- **Opens with:** `/sys` is not a directory tree someone laid out. It is *generated* from an in-kernel object graph, and once you know that, the whole filesystem becomes readable: every directory is an object, every file is an attribute with a show and store function, and every symlink is a relationship between objects.
- **Sections:** `## The three pieces` (`kobject` — a name, a reference count, a parent pointer, and a pointer to its type; `kset` — a collection of kobjects that is itself a kobject; `ktype` — the behaviour: the release function and the attribute operations. A table naming each and its one job); `## It is always embedded` (a `kobject` is never allocated alone; it sits inside a real structure, and the release function recovers that structure with `container_of` — link the previous page; this is the payoff the folder has been building to); `## From object graph to directory tree` (parent pointers become directories, ksets become the grouping directories, attributes become files, and cross-references become symlinks. Walk one concrete path from `/sys/devices/...` up to its parents); `## Attributes` (`struct attribute`, `show`/`store`, `sysfs_create_group`, and the one-value-per-file rule that sysfs enforces as policy); `## The lifetime rule that bites` (a kobject's release function is where the containing object is freed; freeing the container yourself while a kobject reference is outstanding is the classic bug, and sysfs holds references while a file is open); `## What actually happens` **[WAH]** — `cat /sys/class/net/eth0/mtu` (or any live attribute): no file is read. A `show` function runs, formats a value from a live kernel structure into a buffer, and returns it. Which is why some sysfs files can block, why `stat` reports size 4096 for a file with three bytes of content, and why the value differs every time you look.
- **Anchor:** Mermaid `flowchart TB` with two panes side by side: the kobject graph (objects, ksets, parents) on the left and the resulting `/sys` paths on the right, with arrows mapping one to the other. Caption: "The object graph on the left generates the directory tree on the right; nothing about `/sys` is stored."
- **Lab** — `<Lab host="any-linux" title="Read /sys as an object graph" time="10 min">`: pick a real device — `ls /sys/class/net/`, then `ls -l /sys/class/net/<iface>` showing the `device` and `subsystem` symlinks; follow one with `readlink -f`; `cat` two or three attributes; then `stat` one attribute file and observe the 4096-byte size against its actual content. The "if it fails" line covers WSL2's partly synthetic `/sys`, pointing at Task 12's capability table.
- **KernelFacts:** `structure` — `[["struct kobject", "include/linux/kobject.h"], ["struct kobj_type", "include/linux/kobject.h"], ["struct attribute", "include/linux/sysfs.h"]]`; `path` — `"kobject_init_and_add() → directory created under the parent → attribute show()/store() called on access"` (**verify**); `observe` — `ls -l /sys/class/net/ && cat /sys/class/net/lo/mtu`; `trap` — "A sysfs file's `stat` size is a page, not its content length, because the content does not exist until you read it. Any tool that trusts the size before reading gets it wrong."
- **References:** `https://docs.kernel.org/filesystems/sysfs.html` (the attribute contract, including the one-value-per-file rule and the buffer size); `https://docs.kernel.org/core-api/kobject.html` (the kernel's own kobject guide — the primary source for the lifetime rules); `<Src file="include/linux/kobject.h" />` (the structures, which are small and clarify the parent/kset relationship faster than prose).

### `memory-safety-in-kernel-c.md` — What Goes Wrong in Kernel C

- **Opens with:** the catalogue page. Kernel bugs fall into a small number of recurring classes, each with a characteristic symptom and a tool that catches it. Knowing the list is what turns an unfamiliar oops from a mystery into a lookup.
- **Sections:** `## The catalogue` — a table with four columns (bug class, what it looks like when it happens, the tool that catches it, the config symbol), one row each for: use-after-free (`KASAN`); reference-count leak (slab growth, `refcount_t` warnings); sleeping in atomic context (`CONFIG_DEBUG_ATOMIC_SLEEP`, "BUG: sleeping function called from invalid context"); unchecked user pointer (oops in `copy_*_user`, caught by sparse's `__user` checking); integer overflow in a size calculation (`struct_size()`, `check_add_overflow()` and friends as the fix); missing bounds check on an array index (`KASAN` again, or a silent corruption); uninitialised stack or heap memory (`CONFIG_INIT_STACK_ALL_ZERO`, KMSAN); data race (`KCSAN`). **Verify each config symbol and message string at v6.18.** Then a `###` of two or three sentences on each row — enough to recognise it, not a treatment; `## Why these specifically` (each one follows from a property of the environment: no allocator safety net, contexts that may not sleep, an unforgeable boundary crossed by pointers, and a stack too small to be forgiving); `## The tools, in one paragraph each` (KASAN, KCSAN, KMSAN, lockdep, `CONFIG_DEBUG_*` family — naming what each proves, and that they cost performance and are for debug kernels. Forward-reference folder 17 in prose for using them in anger); `## Rust for Linux at v6.18` (status stated factually and dated: what is merged, what is experimental, which subsystems have drivers, and explicitly that this section's code is C. **Verify against current sources — this moves fast, and a stale claim here is exactly the kind of error that erodes trust in the rest of the section.**).
- **Anchor:** the bug-class catalogue table.
- **KernelFacts:** `structure` — `[["CONFIG_KASAN", "lib/Kconfig.kasan"], ["CONFIG_DEBUG_ATOMIC_SLEEP", "lib/Kconfig.debug"]]`; `path` — `"symptom in dmesg → bug class → the sanitizer that proves it → the config symbol that enables that sanitizer"`; `observe` — `dmesg | grep -iE "BUG:|KASAN|WARNING:"`; `trap` — "A kernel built without the sanitizers will happily run code with a use-after-free in it, sometimes for weeks. The absence of a report is the absence of a detector, not the absence of the bug."
- **References:** `https://docs.kernel.org/dev-tools/kasan.html` (what KASAN detects, its modes, and its cost — the single most useful debug option in this list); `https://docs.kernel.org/dev-tools/index.html` (the full tool inventory, which is the index for folder 17); `https://docs.kernel.org/rust/index.html` (the authoritative statement of Rust support status at the pinned version — check the date and say so).

- [ ] **Step 1: Verify every config symbol, header path, and quoted message string** used across the four pages at v6.18.
- [ ] **Step 2: Verify the Rust-for-Linux status** against `docs.kernel.org/rust/` and recent LWN coverage before writing that section, and date the claim in the prose.
- [ ] **Step 3: Write the four pages** to the briefs above, in the order given.
- [ ] **Step 4: Check and build**

Run: `npm run check:linux && npm run build`
Expected: folder 04 fully written (12 pages), zero findings.

- [ ] **Step 5: Commit**

```bash
git add docs/linux/04-kernel-architecture-and-idioms
git commit -m "docs: write error handling, refcounting, kobjects, and kernel bug classes"
```

---

## Task 24: Folder 00 — the glossary

**Files:**
- Modify: `docs/linux/00-overview/glossary.md`

**Interfaces:**
- Consumes: every page written in Tasks 6–23 — this page is an aggregation and must be written after them.
- Produces: the vocabulary index later phases append to. Establish the entry format here so appending is mechanical.

The spec's target is ~90 terms across the whole section. **This phase covers only terms actually defined in folders 00–04**, which is roughly 45–55 entries. Do not define a term whose owning page does not exist yet — an entry that cannot link to its owner is a promise the section has not kept.

- **Format, fixed:** an alphabetised list; each entry is a bolded term, an em dash, one or two sentences, and a link to the page that owns it. One paragraph per term, no headings per letter (the page is searched, not browsed).
- **Rule:** every entry links to exactly one owning page inside folders 00–04, and that page must genuinely define the term. If two pages both touch it, the owner is the one where it is introduced.
- **Terms this phase can define, grouped by owning folder** (the writer confirms each against the finished page before including it):
  - From 00: kernel, user space, distribution, system call, kernel thread, ABI, LTS.
  - From 01: `bzImage`, `vmlinux`, `vmlinuz`, `defconfig`, initramfs (build sense), QEMU gdbstub, KASLR.
  - From 02: page fault (minor/major), page cache, dirty page, writeback, `sk_buff`, NAPI, GRO, namespace, cgroup, overlayfs, `pivot_root`.
  - From 03: UEFI, ESP, boot variable, boot loader, kernel command line, setup header, initcall, initcall level, rootfs, PID 1, unit, target, ordering versus requirement, journal.
  - From 04: monolithic kernel, module, taint, `EXPORT_SYMBOL_GPL`, modversions, `vermagic`, Kconfig symbol, tristate, freestanding C, `__init`, `__user`, sparse, intrusive list, `list_head`, `container_of`, `offsetof`, `ERR_PTR`, `refcount_t`, `kref`, kobject, kset, ktype, sysfs attribute, KASAN, lockdep.
- **Opening paragraph:** one sentence saying every term links to the page that owns it, and one saying the glossary grows as folders land — so a reader who cannot find a term knows why.
- **No `<KernelFacts>`, no `## References`** — the checker's `NAVIGATIONAL` set already exempts this page.

- [ ] **Step 1: Extract the real term list** by re-reading the twenty-nine pages written in Tasks 6–23 rather than working from the list above. The list above is a starting point; the pages are the authority.
- [ ] **Step 2: Write the page** in the fixed format.
- [ ] **Step 3: Verify every link resolves**

Run: `npm run build`
Expected: green. `onBrokenLinks: "throw"` catches any entry pointing at a page that does not exist.

- [ ] **Step 4: Commit**

```bash
git add docs/linux/00-overview/glossary.md
git commit -m "docs: write the linux section glossary for folders 00-04"
```

---

## Task 25: Folder 00 — the misconceptions index

**Files:**
- Modify: `docs/linux/00-overview/misconceptions-index.md`

**Interfaces:**
- Consumes: every `## Misconceptions` section written in Tasks 6–23.
- Produces: the index later phases append to, and — per the spec — a page that is worth reading on its own.

- **Opens with:** two sentences: this page collects every wrong belief the section corrects, and a reader who reads only this page still gains something. Then the honest caveat that each entry is a summary and the owning page carries the reasoning.
- **Format, fixed:** grouped by folder, in folder order, with a `##` per folder. Each entry: the belief stated plainly in bold as someone would actually say it, then the correction in two or three sentences, then a link to the owning page. Blunt, not coy — the spec is explicit that this page's value is its directness.
- **Coverage rule:** every entry that appears in a page's `## Misconceptions` section appears here, and nothing appears here that is not on a page. This is a mirroring task, not an authoring one — **if the two disagree, the page wins and the index is corrected.**
- **Expected sources** (verify against what was actually written): `the-kernel-userspace-boundary` (3), `what-linux-actually-is` (3), `distributions-and-what-differs` (3), `the-life-of-a-write` (3), `the-life-of-a-page-fault` (3), `the-life-of-a-packet` (3), `the-life-of-a-container` (3), `bootloaders-grub-and-friends` (3), `the-kernel-image` (3), `switch-root-and-pid-1` (3), `systemd-the-model` (3), `monolithic-with-modules` (3), `exported-symbols-and-the-module-abi` (3) — roughly 39 entries.
- **Closing line:** the index grows with the section; folders 05–19 add theirs as they land.

- [ ] **Step 1: Collect the entries mechanically**

Run: `rtk run "grep -rn -A6 '^## Misconceptions' docs/linux/"`
Work from that output, not from memory.

- [ ] **Step 2: Write the page** in the fixed format.
- [ ] **Step 3: Verify the mirroring is complete** — count the `## Misconceptions` sections found in Step 1 and confirm every one contributed entries.
- [ ] **Step 4: Build and commit**

```bash
npm run build
git add docs/linux/00-overview/misconceptions-index.md
git commit -m "docs: write the misconceptions index for folders 00-04"
```

---

## Task 26: Phase review, `CLAUDE.md`, and the written gate

**Files:**
- Modify: `CLAUDE.md`
- Modify: any page the review pass finds wanting

**Interfaces:**
- Consumes: everything.
- Produces: a phase that is actually finished, and repository documentation that matches the repository.

- [ ] **Step 1: Run the written gate**

Run: `npm run check:linux -- --written`
Expected: `check-linux-docs: OK — 47 written page(s), 0 stub(s)`. Any remaining stub is a page this plan missed; write it before continuing.

- [ ] **Step 2: Run the full gate set**

```bash
npm run build
npm run typecheck
npm run test:graph
npm run test:kernel-source
rtk run 'npm run lint'
```

Expected: all green. Fix anything that is not before proceeding — this is the phase's definition of done, and a failing gate here is not a documentation issue to defer.

- [ ] **Step 3: Review pass against the spec's checklist**

Walk all 47 pages and confirm each item. Record findings in a scratch list, fix them, then re-run Step 2.

- Every topic page has a visual anchor, and its caption says what it shows.
- Every topic page has `## References` with 2–6 annotated entries, no bare URLs, and any source significantly older than v6.18 says so in its annotation.
- Every topic page ends with `<KernelFacts>` whose `trap` row is a real trap, not a restatement of the page.
- Every symbol, path, struct, and config name has been checked against Elixir v6.18.
- Every arch-specific claim names its architecture; the arm64 `:::note` contrasts are present on the syscall-entry, privilege-level, interrupt-controller, and early-boot material this phase covers.
- Every `## Misconceptions` entry is mirrored in `misconceptions-index.md` (Task 25).
- `## What actually happens` appears only on the pages this plan marks **[WAH]**.
- Every `<Lab>` has a host badge, shows expected output, and closes with an "if it fails" line. Every lab carrying a `:::danger` has a host badge other than `any-linux`.
- No page links into folders 05–19.
- `static/img/linux/SOURCES.md` has one row per file and no orphans in either direction.

- [ ] **Step 4: Verify the section in a production build**

```bash
npm run build && npm run serve
```

Open the section and check, by eye: the roadmap's `<LearningPath>` blocks render and their links work; a page with a `<Figure>` shows the image and zooms; the `<PrereqBlock>` chips appear above and below an article and lead somewhere; a `<Lab>` renders with its host badge; the `hello.cast` player on `how-to-use-this-section` still works. Serve, not dev — the Cast player's SSR safety is only proven in a production build.

- [ ] **Step 5: Update `CLAUDE.md`**

Four edits in the "Linux & Kernel Internals section" block, plus one in "Content architecture":

1. **The component list.** It currently says "Six MDX components are registered globally … `Src`, `KernelFacts`, `Lab`, `Video`, `Cast`, `KnowledgeGraph`". Replace with the current set: `Src`, `KernelFacts`, `Lab`, `Video`, `Cast`, `LearningPath`. State that `KnowledgeGraph` was removed — the graph is still built and still fails the build on a bad prerequisite, but it is no longer drawn; `roadmap.md` presents curated learning paths instead, and `PrereqBlock` (injected by the swizzled `DocItem/Layout`, not MDX-registered) remains the per-page surface of the graph.
2. **The cast policy.** Add a line: `<Cast>` is for sessions where the interaction is the lesson (a `gdb`, `bpftrace`, or `perf` session). Command-and-output material is an annotated ` ```text ` code block, and every cast is accompanied by one anyway. `static/casts/linux/hello.cast` is a placeholder proving the player works; no real casts have been recorded yet.
3. **The figure policy.** Add a line noting that `docs/linux/` is exempt from the blog-image restriction stated in the "Content architecture" section — the spec lifts licence gating for that section — but that the `static/img/linux/SOURCES.md` row and the on-page source credit are still required. Cross-reference the existing `static/img/gpu/SOURCES.md` convention so the two read as one policy with one exception.
4. **Phase status.** Update the phase line: Phase 1a delivered the infrastructure and the 46-page scaffold; Phase 1b (this plan) wrote folders 00–04 and CS backfill 1/2/17; folders 05–19 remain scaffolded-in-spec-only and are **not** created on disk, so nothing may link into them. Name `npm run check:linux -- --written` as the gate that folders 00–04 now pass.
5. In the **Content architecture** section, add `linux` to the sentence listing the top-level docs folders if it is not already there, so the sidebar mapping is accurate.

Keep the edits surgical — `CLAUDE.md` is dense on purpose, and this is an update, not a rewrite.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/linux docs/computer-science
git commit -m "docs: update CLAUDE.md for the linux section's current components and phase status"
```

- [ ] **Step 7: Final verification**

```bash
npm run check:linux -- --written && npm run build && rtk run 'npm run lint'
git status
```

Expected: all green, working tree clean. Report the page count written, the gates run, and anything the review pass found and fixed.

---

## Self-review notes

**Spec coverage.** Phase 1's remaining scope per the spec's "Phase 1 ordering" list: items 1–7 (infrastructure) were delivered by Phase 1a; item 8 (scaffold) likewise. This plan covers item 9 (CS backfill 1, 2, 17 and their backlinks — Tasks 3–5), item 10 (write folders 00 → 04 in order, with folder 04's Graphviz figure — Tasks 6–23, figure in Task 2 and consumed in Task 20), and item 11 (figure pass and the phase review checklist — Tasks 2 and 26). The spec's `<KnowledgeGraph>`-on-roadmap requirement (item 6) is **deliberately reversed** by Task 1 on the user's instruction; the build-time validation the spec actually cares about is untouched.

**Deliberate deviations from the spec, all on the user's instruction:**
- `<KnowledgeGraph>` is deleted rather than extended. The spec's stated purpose for it — "never render the full graph, folder granularity by default" — is served instead by `<PrereqBlock>`'s per-page chips and `roadmap.md`'s curated paths.
- No casts are recorded. The spec marks `01/debugging-the-kernel-with-gdb` with `<Cast>`; this phase ships the same content as annotated text blocks, which the spec already requires alongside every cast. A cast can be added later without touching the prose.
- `misconceptions-index.md` and `glossary.md` are written now for folders 00–04 rather than deferred to the spec's final whole-section pass. They are explicitly scoped and explicitly say they grow.

**Known gaps, stated rather than hidden:**
- The spec names six learning paths, four of which ("I want to write a driver", "My server is slow", "I want to work on containers", "I want to send a patch") cross into folders that do not exist yet. Task 1 keeps the two that fit ("I just want to understand my machine", "I want to read kernel source") and substitutes four that stay inside folders 00–04. The spec's original six land when their folders do.
- Several `KernelFacts` values, symbol names, and config symbols in this plan are marked **verify**. They are informed starting points, not checked facts, and the constraint at the top of this plan makes verification a per-task obligation rather than a review afterthought.
