# Authoring guide

How to write and maintain pages in this knowledge base. `CLAUDE.md` holds the mandatory project rules; this file explains how to meet them. Section `CLAUDE.md` files and design specs in `docs/superpowers/specs/` override this guide for their section (e.g. the algorithms page skeleton, the Linux `<KernelFacts />` closing card).

The goal is reader understanding and trustworthy information, not page count.

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
4. **List prerequisites.** Which existing pages must the reader know? Link them near the top. If a prerequisite doesn't exist and is short, explain it inline; if it's substantial, write it first (or flag the gap — don't paper over it).

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

### Concept page skeleton (most pages in this repo)

Use only the sections that earn their place.

```md
---
id: thread-indexing
title: Thread Indexing
sidebar_label: Thread Indexing
sidebar_position: 4
tags: [gpu, cuda]
---

# Thread Indexing

<1–3 sentences: the problem this solves and why the reader cares.>

**Prerequisites:** [Threads, Blocks and Grids](./threads-blocks-and-grids.md)

## <The core idea>
## <How it works>          — mechanism, diagram or figure, minimal example
## <Using it>              — realistic example, common patterns
## Pitfalls / trade-offs   — what breaks, what it costs, when not to use it
## Related                 — next steps and siblings, each with a one-line reason
## References              — primary sources (vendor docs, specs, papers, source code)
```

### How-to skeleton

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

**Headings.** One `#` (matching `title`), then `##`/`###` without skipping levels. Headings name the content ("Bank conflicts"), not decoration ("Let's dive in").

## 4. Continuity across pages

- **Canonical home.** Each concept is explained in full in exactly one page. Elsewhere: one-sentence recap + link.
- **Changing a fact.** Grep for every statement of it (including tables and `<Recall>`/summary cards), update or link them all in the same commit.
- **Renaming/moving a page.** Grep for its id and path across `docs/` (Linux `prerequisites`/`related` reference ids; CS pages are Linux prerequisites). The build catches broken links but not stale descriptions of the moved content.
- **Contradictions.** Resolve in favor of: the implementation or primary source > the canonical page > other pages. Fix the losing statement; don't leave both.
- **Related links** are meaningful: each says why the reader would go there. No link dumps.
- **Gaps.** If you find a missing prerequisite you can't fill now, note it in the summary of your change rather than writing a placeholder page.

## 5. Visuals and interactive elements

Choose the simplest presentation that works. Plain prose, lists, and tables first.

| Need | Use |
|---|---|
| Show a real thing (hardware, profiler output, vendor diagram) | `<Figure>` with provenance (see `CLAUDE.md`) |
| Structure: flow, state machine, sequence, dependency | Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`) |
| Signal timing | WaveDrom fence |
| Alternatives / per-platform variants of the same content | `<Tabs>` (`groupId` to sync choices across the page) |
| Optional depth, long derivations, full listings | `<details><summary>` |
| Warnings and key takeaways | Admonitions — sparingly; one or two per page |
| End-of-page summary card | `<Recall>` (algorithms), `<KernelFacts>` (Linux) |
| Ordered learning route | `<LearningPath>` (landing/roadmap pages) |
| Letting the reader tweak a React example | ```` ```jsx live ```` — only for React content |

Rules:
- Never hide essential information inside `<details>` or a non-default tab.
- Every diagram and figure is explained in the surrounding text; a reader who can't see it must still follow the argument. `alt` text says what the image shows.
- Mermaid diagrams: under ~15 nodes; split larger ones. Label edges when the relationship isn't obvious.
- No decorative images, animations, or icons that carry no information.
- Interactive components must work in both themes, at narrow widths, and by keyboard.

## 6. Review checklist

Before finishing a page change:

- [ ] Searched for existing coverage; no duplicate explanation introduced
- [ ] Purpose is clear in the first paragraph; prerequisites linked
- [ ] Every claim checkable against code, official docs, or a cited source
- [ ] Code snippets correct for the stated versions; fragments marked
- [ ] Terminology matches the rest of the section
- [ ] Heading hierarchy clean; frontmatter complete; `sidebar_position` not duplicated
- [ ] Related pages, landing pages, and summary cards updated if affected
- [ ] Images have `alt`, on-page credit, a `SOURCES.md` row, and reasonable size
- [ ] Required gates from `CLAUDE.md` run and passing; rendered check done if layout/components changed
