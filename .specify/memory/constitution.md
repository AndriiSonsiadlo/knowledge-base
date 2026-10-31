# Knowledge Base Constitution

## Core Principles

### I. Reader Understanding Over Volume

Every page MUST exist to make a specific reader understand a specific subject. Length is a
consequence of the subject, never a goal.

- A page MUST open by stating what the subject is, what problem it solves, and why the reader
  cares, before any detail.
- Sentences that would be true of any topic, restate earlier text, or pad a section MUST be cut.
- Sections MUST follow the subject's own structure (its parts, stages, variants, cases), not a
  fixed template. Optional sections (internals, usage, trade-offs, pitfalls, comparison) appear
  only when the subject has real content for them.

Rationale: readers come to learn or to look something up; both are slowed by filler.

### II. Accuracy and Verifiability (NON-NEGOTIABLE)

- Every API, flag, version, number, and behavioral claim MUST be traceable to the implementation,
  official documentation, a specification, or a cited source. Unverifiable claims MUST be removed
  or explicitly marked as unverified.
- Code examples MUST compile or run as shown for the stated versions, or be visibly marked as
  fragments.
- Facts, recommendations, version-specific behavior, and historical behavior MUST be
  distinguishable from one another on the page.

Rationale: a knowledge base that is sometimes wrong cannot be trusted at all.

### III. Connected Knowledge

- Each concept MUST have exactly one canonical page; other pages give a short recap and link to it.
- A page MUST rely only on concepts explained earlier in its learning path or linked as
  prerequisites.
- Before writing content that links to a topic without a page, that page MUST be created first as
  a stub with complete frontmatter in its correct place, so links resolve and the build stays green.
- When a fact changes, every other statement of it MUST be updated or replaced by a link in the
  same change. Contradictions are resolved in favor of: primary source > canonical page > others.

Rationale: understanding compounds only when pages build on each other instead of repeating or
contradicting each other.

### IV. Complete Pages

A page is either an explicit stub or complete. There is no "partially written" state.

- A complete page MUST cover its stated scope end to end: the reader can finish it without
  needing an unwritten page to make sense of it.
- Advanced topics MUST include a worked example traced step by step (real inputs, intermediate
  state, result) and the non-obvious pitfalls the subject is known for.
- Stubs MUST use the section's stub marker so they are identifiable and tracked.

Rationale: half-explained topics cost the reader more than a clearly marked gap.

### V. Visual and Interactive Explanation

- Any page explaining a mechanism, data flow, architecture, state change, or multi-step process
  MUST include at least one visual (`<Diagram>`, `<Figure>`, or a diagram fence), explained in
  the surrounding text.
- Advanced topics SHOULD use interactive elements where they reduce effort to understand:
  `<Tabs>` for variants or step-by-step states, `<details>` for optional depth, live code for
  React, and purpose-built components where a recurring pattern justifies one.
- `<Diagram>` is the default for structural pictures; Mermaid is a fallback for shapes it cannot
  express (sequence, state, dense graphs).
- Visuals MUST NOT be decorative. Essential information MUST NOT exist only inside a collapsed
  block, a non-default tab, or an image. Components MUST work in light and dark themes, at phone
  width, and by keyboard.

Rationale: advanced subjects are understood through their structure and motion, which prose alone
conveys poorly — but decoration and hidden content harm more than they help.

### VI. Formatting for Comprehension

- Headings MUST name their content, form a clean hierarchy, and make the page scannable from the
  table of contents alone.
- Comparisons across several attributes MUST be tables; sequences MUST be numbered lists;
  paragraphs SHOULD carry one idea each.
- Code blocks MUST declare a language, and SHOULD use `title=` and line highlighting when that
  points the reader at what matters.
- Admonitions are for warnings and key takeaways only, at most a few per page.

Rationale: formatting is how a reader finds and parses information; consistent formatting lets
them do it without thinking.

## Platform Constraints

- Platform: Docusaurus 3.10 (MDX, React 19), deployed to GitHub Pages under `/knowledge-base/`.
  Folder structure is the navigation; `_category_.json` and frontmatter control labels and order.
- Only components registered in `src/theme/MDXComponents.js`, Docusaurus built-ins, and configured
  remark/rehype plugins may be used in content. New components are added there, documented in
  `AUTHORING.md`, and verified rendered before use.
- Images MUST stay under ~1 MB each. Credit is required only for official sources. Licenses are
  not tracked.
- No new tool, plugin, dependency, or external service is added without a stated, concrete need.

## Authoring Workflow and Quality Gates

1. Search existing pages for the topic and its prerequisites; extend before creating.
2. Create stubs for any not-yet-existing link targets.
3. Write per `AUTHORING.md`; apply section-local rules from `docs/<section>/CLAUDE.md` and any
   design spec under `docs/superpowers/specs/`.
4. Gates (MUST pass before a change is complete):
   - every content change: `npm run build`;
   - `docs/linux/`: `npm run check:linux -- --written`; algorithms: `npm run check:algo`;
   - code/config: Biome lint (run raw), `npm run typecheck`;
   - new or changed components/layout: rendered check in both themes and at ~390 px width.
5. A check MUST NOT be reported as passed unless it was actually run.

## Governance

- This constitution supersedes other practices. `CLAUDE.md` (project rules, commands, gates) and
  `AUTHORING.md` (how to write) are the runtime guidance that implement it; section `CLAUDE.md`
  files and design specs refine it for their scope. Any conflict MUST be resolved in the same
  change that finds it, by amending the lower-level file or this constitution.
- Amendments: edit this file with a Sync Impact Report, bump the version, and update dependent
  guidance files in the same change.
- Versioning: MAJOR for removing or redefining a principle; MINOR for a new principle or
  materially expanded guidance; PATCH for clarifications.
- Compliance: every page change is reviewed against the `AUTHORING.md` checklist, which maps to
  these principles.

**Version**: 1.0.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27
