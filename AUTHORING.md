# Authoring guide

How to write and maintain pages in this knowledge base. `CLAUDE.md` holds the mandatory project rules; this file explains how to meet them. Section `CLAUDE.md` files and design specs in `docs/superpowers/specs/` override this guide for their section (e.g. the algorithms page skeleton, the Linux `<KernelFacts />` closing card).

The goal is reader understanding and trustworthy information, not page count. The principles behind these rules are in `.specify/memory/constitution.md`.

## 1. Before writing: find where it belongs

1. **Search.** `grep -ril '<term>' docs/` for the topic, its synonyms, and the two or three concepts it depends on. Check the section's design spec if one exists.
2. **Decide the action:**

| Situation | Action |
|---|---|
| A page already covers the topic | Extend it. Fix what's wrong or missing there. |
| The topic is a subsection of an existing page and fits in < ~80 lines | Add a section to that page. |
| A distinct concept a reader would search for by name, or other pages need to link to it | New page. |
| An existing page passes ~400 lines, or mixes two jobs (e.g. concept + reference table) | Split along the job boundary; leave the original as the concept page with links out. |
| Two pages explain the same thing | Merge into the better one; turn the other into a short page that links, or delete it and fix inbound links. |
| A new topic area with ≥ 4 pages | New folder with `_category_.json` (`link: generated-index`, plus a `description`). |

3. **Place it.** Pick the folder whose readers need it. Set `sidebar_position` so prerequisites come before the pages that use them.
4. **List prerequisites.** Which existing pages must the reader know? Link them near the top. If a prerequisite is short, explain it inline; if it's substantial and has no page yet, create its stub (see below) and link to it.
5. **Create link targets before writing.** Any page you're about to link to that doesn't exist yet gets created first as a stub: full frontmatter, correct folder and `sidebar_position`, body `This page has not been written yet.` (`:::info[Not yet written]` in `docs/linux/`). Then write the content that links to it. This keeps the build green and the plan visible in the sidebar.

## 2. Page types

Pick one primary type per page. Mixing types is the most common cause of unfocused pages.

| Type | Answers | Shape |
|---|---|---|
| **Concept** | What is it, why does it exist, how does it work? | Problem → idea → mechanism → trade-offs → related |
| **How-to / tutorial** | How do I do X? | Prerequisites → steps with expected output → verification → troubleshooting |
| **Reference** | What are the exact options/values? | Tables, signatures, defaults; minimal prose; sorted predictably |
| **Comparison / decision** | Which one should I use? | Criteria → side-by-side (table or `<Tabs>`) → recommendation by situation |
| **Troubleshooting** | Why is X broken? | Symptom → cause → fix, one entry per symptom |
| **Overview / landing** (`readme.md`, `intro.md`, `00-overview/`) | What's in this area and in what order should I read it? | Scope, audience, reading order, links; no deep content |

### Structuring a concept page

There is no fixed section list. The topic decides the sections. Plan them by asking what a reader needs, in order, to understand *this* subject:

- **Always:** a short opening (what it is, what problem it solves, why the reader cares), then the body, then `## References` when the page relies on sources.
- **The body is shaped by the subject.** Its sections are the subject's own subtopics: the parts of a mechanism, the stages of a pipeline, the variants of an API, the cases of an algorithm. Name them after their content ("Warp scheduling", "The two-phase commit", "Copy vs. move"), not after a template ("How it works").
- **Add only if the topic has real content for it:**
  - *Mechanism / internals*: when how it works changes how you use it.
  - *Usage / examples*: when there's a practical API, command, or pattern to show.
  - *Trade-offs / when not to use*: when there are real alternatives or costs.
  - *Pitfalls*: when there are known, non-obvious mistakes.
  - *Comparison*: when readers routinely choose between this and something else.
  - *Related*: when there are clear next steps; give each link a one-line reason.
- A purely definitional or historical topic may need none of the optional parts. A deep topic may need several subtopic sections plus nested `###` breakdowns. Both are fine.

Frontmatter (every page):

```md
---
id: thread-indexing
title: Thread Indexing
sidebar_label: Thread Indexing
sidebar_position: 4
tags: [gpu, cuda]
---
```

Link prerequisites near the top (`**Prerequisites:** [...](...)`) when the page depends on earlier material.

### How-to pages (typical shape, adapt as needed)

```md
# <Verb phrase: "Profile a kernel with Nsight Compute">

<What you'll achieve, and when you'd need to.>

**You need:** <tools + versions, prior pages>

## Steps
1. <Action> — command in a code block, then the expected output or result.
2. ...

## Verify
## If it doesn't work     — symptom → cause → fix
```

## 3. Writing standards

**Lead with context.** Open with the problem and why it matters, then the mechanism, then details. A reader who stops after the first paragraph should know what the thing is and whether this page is for them.

**Define before use.** Introduce each term the first time it matters, in plain words, then use it consistently. Use the term already established elsewhere in the knowledge base — grep for it — rather than a synonym.

**Explain why, not just what.** Where it matters, cover: why it exists, how it works, when to use it, when not to, and what it costs.

**Be specific.** "Coalesced loads let a warp's 32 accesses merge into as few as one 128-byte transaction" beats "coalescing improves performance." Cut sentences that would be true of any topic.

**Mark certainty.** Distinguish:
- facts (cite or link the source),
- recommendations ("prefer X because Y"),
- version- or platform-specific behavior ("since CUDA 12.0", "on x86-64"),
- historical behavior (`:::note[Historical]` or a clearly labelled paragraph — keep it only if it still explains something current).

**Examples.** Realistic, minimal, and correct. Show the output when it teaches something. Mark incomplete fragments clearly (a `// ...` elision, or the section's `doc:no-run` marker). Keep names and values consistent across examples on the same page.

**Length.** As short as the topic allows. Typical concept pages here run 150–350 lines. A page over ~400 lines is a split candidate; under ~40 lines is a candidate for merging into its parent.

**Headings.** One `#` (matching `title`), then `##`/`###` without skipping levels. Headings name the content ("Bank conflicts"), not decoration ("Let's dive in"). Reading only the table of contents should tell the reader what the page teaches.

### Formatting

| Content | Format |
|---|---|
| One idea with its reasoning | A short paragraph (one idea per paragraph) |
| Ordered actions or stages | Numbered list |
| Unordered facts of the same kind | Bulleted list. Avoid nested lists deeper than two levels |
| The same attributes across several items | Table |
| A term the reader must remember | **Bold** on first definition only |
| Code | Fenced block with a language. Add `title="path/file.cpp"` when the file matters and `{3,7-9}` / `// highlight-next-line` to point at the lines being discussed |
| Command plus output | Command in a `bash` block, output in a separate `text` block (or the same block if short), never mixed with prompts the reader would copy |

Don't bold whole sentences, stack admonitions, or put a table where two sentences would do.

### Advanced topics

For subjects with real depth (internals, concurrency, memory models, schedulers, compilers, ML architectures):

1. **Layer the explanation.** Intuition first (a sentence or analogy that is *correct*, not just catchy), then the mechanism, then the precise detail and edge cases. Each layer must stand on its own, so readers can stop at the depth they need.
2. **Show the structure.** Draw the moving parts with `<Diagram>` before describing how they interact.
3. **Trace a worked example.** Use real inputs, show the intermediate state at each step, and give the result. When state changes over steps, use `<Walkthrough>` (one `<Step>` per state) and mark what changed in each.
4. **Name the traps.** List the mistakes practitioners actually make, and why each one is wrong.
5. **Put optional rigor in `<details>`.** Proofs, derivations, and full listings go there, while the main text still states the result.

### When a page is complete

A page leaves stub status only when all of these hold:
- It covers the scope promised by its title and opening, end to end.
- A reader with the listed prerequisites can follow it without any unwritten page.
- Every mechanism, flow, or architecture it explains has a visual.
- Advanced topics have a traced worked example and their known pitfalls.
- It passes the review checklist below.

## 4. Continuity across pages

- **Canonical home.** Each concept is explained in full in exactly one page. Elsewhere: one-sentence recap + link.
- **Changing a fact.** Grep for every statement of it (including tables and `<Recall>`/summary cards), update or link them all in the same commit.
- **Renaming/moving a page.** Grep for its id and path across `docs/` (Linux `prerequisites`/`related` reference ids; CS pages are Linux prerequisites). The build catches broken links but not stale descriptions of the moved content.
- **Contradictions.** Resolve in favor of: the implementation or primary source > the canonical page > other pages. Fix the losing statement; don't leave both.
- **Related links** are meaningful: each says why the reader would go there. No link dumps.
- **Gaps.** If you find a missing prerequisite you can't fill now, create its stub so it's linkable and visible, and mention it in your change summary.

## 5. Visuals and interactive elements

Choose the simplest presentation that works. Plain prose, lists, and tables first.

| Need | Use |
|---|---|
| Architecture, layers, groupings, flows, "what talks to what" | `<Diagram>` (see below) |
| Show a real thing (hardware, profiler output, vendor diagram) | `<Figure>` (credit only for official sources, see `CLAUDE.md`) |
| Sequence of messages, state machine, dense graph | Mermaid (`sequenceDiagram`, `stateDiagram-v2`). Fallback only. |
| Worked example whose state changes step by step | `<Walkthrough>` (see below) |
| Signal timing | WaveDrom fence |
| Alternatives / per-platform variants of the same content | `<Tabs>` (`groupId` to sync choices across the page) |
| Optional depth, long derivations, full listings | `<details><summary>` |
| Warnings and key takeaways | Admonitions, sparingly (one or two per page) |
| End-of-page summary card | `<Recall>` (algorithms), `<KernelFacts>` (Linux) |
| Letting the reader tweak a React example | ```` ```jsx live ````, only for React content |

### `<Diagram>`

Composable, real-text diagrams: rounded cards, dotted group frames, labelled arrows, one accent colour. Works in both themes and stacks vertically on phones.

```mdx
<Diagram title="What the agent can see" caption="Optional caption below the canvas." accent="green">
  <DiagramNode variant="pill" accent>Agent knowledge</DiagramNode>
  <DiagramArrow label="Unseen" icon="eye-off" dashed />
  <DiagramGroup label="Outside the repository">
    <DiagramNode icon="file-text" title="Design doc">Lives in Drive.</DiagramNode>
    <DiagramNode icon="brain" title="Tacit knowledge">Lives in people's heads.</DiagramNode>
  </DiagramGroup>
</Diagram>

<Diagram title="Request path" accent="blue">
  <DiagramRow>
    <DiagramNode icon="monitor" title="Client" />
    <DiagramArrow direction="right" label="HTTPS" />
    <DiagramNode icon="server" title="API" accent />
    <DiagramArrow direction="right" />
    <DiagramNode icon="cloud" title="Storage" />
  </DiagramRow>
</Diagram>
```

- `<Diagram>` stacks children top to bottom; `accent` is `green | blue | amber | violet`.
- `<DiagramNode>`: `title`, `icon`, body as children; `variant="pill"` for the focal concept; `accent` highlights one node; `dashed` for optional/external.
- `<DiagramGroup label>` is a framed side-by-side set; `<DiagramRow>` is the same without the frame.
- `<DiagramArrow>`: `label`, `icon`, `dashed`; `direction="right"` inside rows.
- Keep it to what the text discusses: ~3–9 nodes. Highlight one thing, not everything.

### `<Walkthrough>`

Shows a worked example one step at a time, with Previous/Next, a numbered step rail, and a "Step X of N" counter. Every step is in the page HTML, so print, readers without JavaScript, and site search all get every step.

```mdx
<Walkthrough title="Kruskal on five vertices" caption="Edges taken in weight order." accent="blue">
  <Step title="Sort the edges">

Sorted: `(A,B,1) (B,C,2) (A,C,3) (C,D,4) (D,E,5)`.

  </Step>
  <Step title="Take A–B">

Union-find merges `{A}` and `{B}` into <StepChange>`{A,B}`</StepChange>.

  </Step>
</Walkthrough>
```

- **Blank lines around step content are required**, as with `<TabItem>`. Without them MDX won't parse the markdown inside.
- `<Walkthrough>` props: `title`, `caption`, `accent` (`green | blue | amber | violet`), and `fixedHeight` (default `true`: the box keeps the tallest step's height so the controls don't move. Set it to `false` when one step is much taller than the rest).
- `<Step title>`: the title is required. A walkthrough with no steps, or a step without a title, fails the build.
- A walkthrough with a single step renders as plain content with no controls. Use it only when there are two or more states.
- **Mark what changed** in each step: `<StepChange>` (optional `label`, default "changed") for inline values, `{N}` or `// highlight-next-line` for code lines, and `<DiagramNode accent>` for diagram parts.
- Keep steps comparable in size, at one change of state per step.
- **Headings inside a step must be `####` or lower** (or just bold text). Site search splits pages at `#`–`###`, so a `###` inside a step cuts every later step out of the search index. Headings inside steps can be linked to: opening the link switches to that step. In `.mdx` files, escape custom heading ids as `\{#id\}`.

Rules:
- Never hide essential information inside `<details>` or a non-default tab.
- Every diagram and figure is explained in the surrounding text.
- No decorative images, animations, or icons that carry no information.
- New interactive components must work in both themes, at narrow widths, and by keyboard.

## 6. Review checklist

Before finishing a page change:

- [ ] Searched for existing coverage; no duplicate explanation introduced
- [ ] Purpose is clear in the first paragraph; prerequisites linked
- [ ] Page is complete (see "When a page is complete") or is an explicit stub
- [ ] Formatting matches content shape (lists, tables, titled/highlighted code); TOC alone shows what the page teaches
- [ ] Every claim checkable against code, official docs, or a cited source
- [ ] Code snippets correct for the stated versions; fragments marked
- [ ] Terminology matches the rest of the section
- [ ] Heading hierarchy clean; frontmatter complete; `sidebar_position` not duplicated
- [ ] Related pages, landing pages, and summary cards updated if affected
- [ ] Linked-to pages exist (stubs created first where needed)
- [ ] Diagrams use `<Diagram>` unless the shape needs Mermaid; images have `alt`, are under ~1 MB, and credit official sources only
- [ ] Required gates from `CLAUDE.md` run and passing; rendered check done if layout/components changed
