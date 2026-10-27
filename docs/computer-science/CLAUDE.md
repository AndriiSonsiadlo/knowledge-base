# docs/computer-science — CS fundamentals & algorithms

Section-local notes, loaded only when working here. Site-wide rules (commits, rtk, frontmatter, figures, `npm run build` gate) are in the root `CLAUDE.md`. **Stay inside this section** — don't list or read other `docs/` folders unless the task links to them.

- Topic folders: `algorithms/`, `assembly/`, `bit-manipulation/`, `buses-and-io/`, `computer-networks/`, `cpu-architecture/`, `databases/`, `memory-hierarchy/`, `operating-systems/`, `overview/`, `protocols/`, `storage/`. Images: `static/img/cs/`.
- Some pages here are Linux "CS backfill" pages linked from `docs/linux/` prerequisites — renaming or moving one breaks the Linux knowledge graph. Grep `docs/linux` for the id before moving.

## `algorithms/` has a hard gate

`npm run check:algo` (`tools/check-algo-docs.mjs`; pass a folder or file to scope it). Every page except `cheat-sheet.md` needs:

- frontmatter `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`; no duplicate `sidebar_position` in a folder
- 150–340 lines
- a visual anchor (`<Figure`, a mermaid fence, or a text trace block)
- section order: … `## Recall` (with a `<Recall>` card) → `## References`; plus `## Related Pages`
- `python` fences are concatenated and **executed** (need at least one `assert`); `cpp` fences are syntax-checked. Mark illustrative fragments with `# doc:no-run` / `// doc:no-run` on the first line.

Design: `docs/superpowers/specs/2026-08-27-algorithms-depth-design.md`.
