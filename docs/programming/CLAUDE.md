# docs/programming — languages & libraries

Section-local notes, loaded only when working here. Site-wide rules (commits, rtk, frontmatter, figures, `npm run build` gate) are in the root `CLAUDE.md`. **Stay inside this section** — don't list or read other `docs/` folders unless the task links to them.

- Subtrees: `cpp/` (numbered folders `00-overview`…`13-idioms-and-design`), `python/`, `cmake/`, and C++ library docs `boost/`, `fmt/`, `spdlog/`, `nlohmann-json/`.
- C++ library pages follow `docs/superpowers/specs/2026-08-07-cpp-library-docs-design.md` — read it only when adding/restructuring a library subtree, not for small edits.
- Each library's entry page is `readme.md` (`sidebar_position: 1`, `sidebar_label: Overview`).
- To place a new page, read the target folder's `_category_.json` and the `sidebar_position` of its siblings only.
