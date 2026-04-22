# Handoff Prompt — Unreal Engine 5 Docs (for Sonnet 5)

Pairs with `specs/2026-07-29-unreal-engine-5-docs-design.md`. That file is the **what**. This file is the **how**.

---

## A. Kickoff — paste this into a fresh Sonnet 5 session

```
Read specs/2026-07-29-unreal-engine-5-docs-design.md (the spec) and
specs/2026-07-29-unreal-engine-5-docs-sonnet-prompt.md (your operating manual).

Execute tranche T1. Follow the operating manual exactly — especially the
Context7 sourcing rules, the subagent dispatch rules, and the commit policy.

Start by invoking superpowers:writing-plans to turn T1 into an implementation
plan. Show me the plan before you write any documents.
```

Swap `T1` for `T2` / `T3` / `T4` on later runs. One tranche per session — 120 docs will not fit in one context window.

---

## B. Operating manual

### 1. Read before doing anything

| File | Why |
|---|---|
| `specs/2026-07-29-unreal-engine-5-docs-design.md` | Full TOC, per-doc contract, sourcing rules, acceptance criteria |
| `CLAUDE.md` | Repo commands, build gate, content architecture |
| `docs/programming/boost/00-overview/what-is-boost.md` | **Style reference.** Match this register, depth, and structure |
| `docs/programming/boost/03-smart-pointers-and-memory/shared-ptr.md` | Style reference for an API-heavy page |

Target length per doc: **120–250 lines**. The boost corpus averages ~157. Shorter than 100 usually means the mental model is missing; longer than 300 usually means an API reference got copied in.

### 2. Workflow per tranche

1. `superpowers:writing-plans` — turn the tranche into a plan, one step per folder. Show the user before writing.
2. `superpowers:subagent-driven-development` — dispatch folder-writer subagents (see §3).
3. Build, lint, format (see §5).
4. Commit per folder (see §6).
5. `superpowers:verification-before-completion` before claiming the tranche is done.

Do **not** invoke `superpowers:brainstorming` — design is settled and approved. Do not re-open the TOC.

### 3. Subagent dispatch — this is the speed lever

**One agent owns one folder.** Folders are independent; documents inside a folder cross-link constantly, so a single agent must own a whole folder to keep those links coherent.

Dispatch with `Agent`, `subagent_type: "general-purpose"`, 3–5 in parallel per batch. T1 is five folders → two batches.

Each agent's prompt must contain:

- The folder it owns and **the exact filenames from spec §4** — no renaming, no adding, no dropping.
- The per-doc contract from spec §5, inline (agents start cold and cannot see this conversation).
- The full 120-file manifest, so cross-folder relative links resolve to real future paths.
- The style reference paths from §1 above, with an instruction to read one before writing.
- The Context7 instructions from §4 below, verbatim.
- **"Do not run any git command."** Only the parent commits. Parallel agents committing to one branch corrupt each other's index.
- **"Do not run `npm run build`."** The parent builds once per batch — 5 concurrent Docusaurus builds will thrash the machine.

For pure lookup work that would otherwise flood context, use `context7:docs-researcher` instead — it fetches library docs and returns only the answer.

Use `Explore` when an agent needs to find an existing repo pattern, not for engine research.

### 4. Context7 — mandatory, not optional

Plugin: `context7`. Tools: `mcp__plugin_context7_context7__query-docs`, `mcp__plugin_context7_context7__resolve-library-id`.

**Verified library IDs — use directly, skip `resolve-library-id`:**

| ID | What |
|---|---|
| `/websites/dev_epicgames_unreal-engine` | UE 5.7 official docs, 145,103 snippets, High reputation. **Primary source.** |
| `/mrrobinofficial/guide-unrealengine` | UE C++ and module-system guide. Secondary, for C++ dialect and `Build.cs` specifics. |

Budget: Context7 caps at **3 `query-docs` calls per question**. One scoped query per document, not per paragraph. Queries must name one concept — `"UPROPERTY specifiers for exposing properties to Blueprint in UE5"`, not `"UPROPERTY"`.

Sourcing priority, from spec §6:

1. Context7 (IDs above)
2. Official Epic docs / UE 5.7 API reference
3. Engine source
4. Attributed community references
5. Model recall — last resort, stable concepts only

**Hard rule: never invent an API.** No class, macro, specifier, function, CVar, or console command appears in a doc unless it was found in a source above. Where a claim could not be verified, write it inline:

> `:::note` Not confirmed against 5.7 in the sources consulted — verify against your engine version. `:::`

An honest gap beats a confident fabrication. Same rule for references (spec §7): no invented book titles, no plausible-looking URLs.

### 5. Verification gates

Run at the **end of each batch**, from the repo root:

```bash
npm run build      # THE gate — onBrokenLinks: "throw" makes a bad link a deploy failure
npm run lint       # biome check
npm run format     # biome format --write
```

`npm run build` reports every broken link at once — fix them in one pass, rebuild, then commit.

Do not build mid-batch: documents legitimately link forward to files a sibling agent has not written yet. Build once the batch's folders are all on disk.

T1 only: apply the three config edits from spec §3 (`sidebars.js`, navbar item, `prism.additionalLanguages`) **first**, build to confirm the site still compiles, commit that, and only then start content. A malformed navbar entry breaks the whole site and would otherwise get blamed on the docs.

Never claim a build passed without having run it. If it was not run, say so.

### 6. Commit policy

- Conventional Commits, scope `ue5`.
- **No `Co-Authored-By` trailer.** Not for Claude, not for anyone.
- **Subject line only.** No body unless the change genuinely needs one.
- One commit per folder, after that folder builds clean. Not one commit per file, not one per tranche.
- Only the parent session commits. Subagents never touch git.

```
docs(ue5): add overview section
docs(ue5): add toolchain and build section
docs(ue5): add C++ in Unreal section
chore(ue5): register game-development sidebar and navbar entry
```

Never commit a failing build, a half-written folder, or scratch files.

### 7. Definition of done — per tranche

From spec §8, all six must hold:

1. Every planned file exists, valid frontmatter, `_category_.json` per folder.
2. `npm run build` passes.
3. `npm run lint` and `npm run format` clean.
4. Sidebar order and folder labels match the TOC.
5. Every engine-specific claim traceable to a §6 source; unverified claims marked inline.
6. No `TODO`, no placeholder text, no empty sections.

Report honestly: what was written, what was verified against Context7, what was marked unverified, what was skipped and why.

### 8. Do not

- Do not rename, add, or drop files from the spec's TOC without saying so and why.
- Do not write absolute doc links — `baseUrl` is `/knowledge-base/`, so relative links only.
- Do not add screenshots or images. Text-first by design.
- Do not let subagents run git or `npm run build`.
- Do not paraphrase Epic's API reference page-by-page. Lead with the mental model, link out for exhaustive signatures.
- Do not claim anything was built, tested, or verified unless it actually ran in the session.
