# Unreal Engine 5 Docs — Tranche T1 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Unreal Engine 5 documentation section's foundation tranche (T1) to this knowledge base: the `game-development` sidebar/navbar wiring, and folders `00-overview` through `04-blueprint-interop` (37 documents total), so a reader can set up the toolchain, write correct Unreal C++, and understand the gameplay framework.

**Architecture:** Config changes land first and are build-verified in isolation (a bad navbar entry breaks the whole site). Content then lands in two parallel subagent batches — one `general-purpose` agent per folder, since docs inside a folder cross-link constantly and a single agent must own a folder to keep those links coherent. The parent session is the only actor that runs git or `npm run build`; agents only write files.

**Tech Stack:** Docusaurus 3.9, Markdown + frontmatter, Mermaid, Docusaurus admonitions, Context7 MCP (`/websites/dev_epicgames_unreal-engine`, `/mrrobinofficial/guide-unrealengine`) for all engine-specific sourcing.

**Source documents:** `specs/2026-07-29-unreal-engine-5-docs-design.md` (design spec, the "what") and `specs/2026-07-29-unreal-engine-5-docs-sonnet-prompt.md` (operating manual, the "how"). This plan operationalizes both for T1 only — do not use it for T2–T4.

## Global Constraints

- Relative doc links only, never absolute — `baseUrl` is `/knowledge-base/` (spec §5, manual §8).
- Target length per doc: 120–250 lines. Under 100 usually means the mental model is missing; over 300 usually means an API reference got copied in (manual §1).
- Frontmatter on every doc: `id`, `title`, `sidebar_label`, `sidebar_position`, `tags: [unreal-engine, ue5, c++, <topic tags>]` (spec §5).
- Body structure on every doc, in order: Why this matters → Mental model (mermaid where relational) → The mechanics → Code (```cpp, ```csharp for Build.cs/Target.cs, ```ini for config) → Gotchas (`:::warning`/`:::caution`) → See also (relative sibling links + one outbound Epic link) (spec §5).
- `_category_.json` per folder: `{ "label": "<N>. <Title Case>", "position": <N>, "link": { "type": "generated-index" } }`, matching the `docs/programming/boost` convention (spec §5, confirmed against `docs/programming/boost/*/​_category_.json` this session).
- Sourcing priority for every engine-specific claim: (1) Context7 `/websites/dev_epicgames_unreal-engine` primary, `/mrrobinofficial/guide-unrealengine` secondary, (2) official Epic docs / UE 5.7 API reference, (3) engine source, (4) attributed community references, (5) model recall — last resort, stable concepts only (spec §6, manual §4).
- Never invent an API. Unverifiable claims get an inline `:::note` marking them unconfirmed, never dropped, never smoothed over (spec §6).
- No screenshots. No invented references — an empty section beats a fabricated citation (spec §7).
- No `TODO`, no placeholder text, no empty sections (spec §8).
- Commits: Conventional Commits, scope `ue5`, subject-line only (no body unless genuinely needed), **no `Co-Authored-By` trailer for anyone**, one commit per folder after that folder builds clean (manual §6).
- Only the parent session runs `git` or `npm run build` / `npm run lint` / `npm run format`. Dispatched subagents never do (manual §3, §8).
- Do not invoke `superpowers:brainstorming` — design is settled and approved. Do not re-open the TOC (manual §2).

---

## Shared Subagent Brief

Every dispatch task below (Task 2 and Task 4) sends this brief verbatim to every agent it launches, with only the **Folder assignment** and **Manifest** sections swapped per agent. This exists once here, not copy-pasted per task, per the same convention as Global Constraints — every dispatch step references it by name and appends its folder-specific block.

```
You are writing one folder of Unreal Engine 5 documentation for a Docusaurus
knowledge base at /home/dev/projects/knowledge-base. You own exactly one
folder — do not touch any other folder, do not touch config files.

STYLE — read both before writing anything:
- docs/programming/boost/00-overview/what-is-boost.md
- docs/programming/boost/03-smart-pointers-and-memory/shared-ptr.md
Match their register, depth, and structure. Target 120-250 lines per doc.
Under 100 lines usually means the mental model is missing; over 300 usually
means an API reference got copied in.

FRONTMATTER (every doc):
---
id: <kebab-case, matches filename>
title: <full title, sentence case>
sidebar_label: <short label>
sidebar_position: <ordinal within your folder, 1-based, in the order listed
  in your folder assignment below>
tags: [ unreal-engine, ue5, c++, <topic tags> ]
---

BODY STRUCTURE (every doc, in this order):
1. Why this matters — 2-4 sentences of orientation; what breaks without
   this knowledge.
2. Mental model — the concept before the API. Mermaid diagram where the
   topic is relational (ownership, lifecycle, data flow); prose where it
   is not.
3. The mechanics — how it works, in the engine's own terms, with correct
   UE 5.7 type and function names.
4. Code — ```cpp fences with realistic, self-consistent snippets,
   including the UPROPERTY/UFUNCTION specifiers a real file needs.
   ```csharp fences for Build.cs/Target.cs content, ```ini fences for
   config content.
5. Gotchas — :::warning or :::caution admonitions for the traps. This is
   where the doc earns its value over the official docs.
6. See also — relative links to sibling docs (this folder and other T1
   folders, using the manifest below so links resolve to real future
   paths) plus one outbound link to the authoritative Epic page.

CONSTRAINTS:
- Relative doc links only. baseUrl is /knowledge-base/ — an absolute
  /docs/... link is wrong.
- Create exactly one _category_.json in your folder:
  { "label": "<N>. <Title Case>", "position": <N>,
    "link": { "type": "generated-index" } }
  <N> is your folder's position, given in your folder assignment below.
- Prose register matches docs/programming/boost: explanatory, second
  person, no marketing tone, no filler.
- No screenshots. Describe editor steps in text.
- Do not rename, add, or drop files from the list given to you. If you
  think a filename is wrong, say so in your final report — do not
  silently change it.
- No TODO, no placeholder text, no empty sections.

SOURCING (mandatory, not optional — Unreal's API surface is large,
versioned, and frequently changed; recall alone is not acceptable):
- Plugin: context7. Tools: mcp__plugin_context7_context7__query-docs,
  mcp__plugin_context7_context7__resolve-library-id.
- Verified library IDs — use directly, skip resolve-library-id:
  - /websites/dev_epicgames_unreal-engine — UE 5.7 official docs,
    145,103 snippets, High reputation. Primary source.
  - /mrrobinofficial/guide-unrealengine — UE C++ and module-system
    guide. Secondary, for C++ dialect and Build.cs specifics.
- Budget: max 3 query-docs calls per question. One scoped query per
  document, not per paragraph. Name one concept per query — e.g.
  "UPROPERTY specifiers for exposing properties to Blueprint in UE5",
  not "UPROPERTY".
- Priority order for every engine-specific claim: (1) Context7 IDs
  above, (2) official Epic docs / UE 5.7 API reference, (3) engine
  source, (4) attributed community references, (5) model recall — last
  resort, stable concepts only.
- Never invent an API. No class, macro, specifier, function, CVar, or
  console command appears in a doc unless it was found in a source
  above.
- Where a claim could not be verified, write it inline rather than
  dropping it:
  :::note
  Not confirmed against 5.7 in the sources consulted — verify against
  your engine version.
  :::
- No invented book titles, no plausible-looking URLs, no fabricated
  references. Omit anything you cannot confirm.

PROHIBITED:
- Do not run any git command. The parent session commits; you never do.
- Do not run npm run build, npm run lint, or npm run format. The parent
  runs these once per batch, not mid-batch, because docs in this batch
  legitimately link forward to sibling files not yet on disk.

REPORT BACK (end of your work):
- Every file you wrote (path).
- Every Context7 query you ran and what it returned.
- Every claim you could not verify and marked inline with :::note:::.
- Anything you skipped, changed from the assignment, or could not
  complete, and why.
```

**Full 120-file manifest** (paths relative to `docs/game-development/unreal-engine/`, so any agent can write a correct relative link to a file a sibling agent — in this tranche or a later one — will create):

```
00-overview/                          (position 1)
  what-is-unreal-engine.md
  engine-architecture-map.md
  mastery-roadmap.md
  cpp-vs-blueprint.md
  learning-resources.md
01-toolchain-and-build/               (position 2)
  installation-and-versions.md
  project-anatomy.md
  unreal-build-tool.md
  modules-and-plugins.md
  unreal-header-tool.md
  build-configurations-and-targets.md
  live-coding-and-hot-reload.md
  source-control-setup.md
02-cpp-in-unreal/                     (position 3)
  uobject-and-reflection.md
  garbage-collection.md
  strings-and-text.md
  containers.md
  smart-pointers-and-ownership.md
  delegates-and-events.md
  interfaces.md
  subsystems.md
  logging-and-assertions.md
  coding-standard-and-naming.md
  unreal-cpp-vs-standard-cpp.md
03-gameplay-framework/                (position 4)
  framework-overview.md
  game-mode-and-game-state.md
  player-controller-and-player-state.md
  pawn-and-character.md
  actor-lifecycle.md
  actor-components.md
  world-and-levels.md
  game-instance.md
04-blueprint-interop/                 (position 5)
  exposing-cpp-to-blueprint.md
  cpp-base-blueprint-derived.md
  blueprint-function-libraries.md
  data-driven-design.md
  blueprint-performance.md
05-input-and-movement/                (position 6, T2 — not yet written)
  enhanced-input.md
  camera-and-spring-arm.md
  character-movement-component.md
  custom-movement-modes.md
06-collision-and-physics/             (position 7, T2 — not yet written)
  collision-channels-and-responses.md
  traces-and-overlaps.md
  chaos-physics-basics.md
  physics-constraints-and-simulation.md
  damage-and-hit-handling.md
07-animation/                         (position 8, T2 — not yet written)
  skeletons-and-skeletal-meshes.md
  animation-blueprints.md
  state-machines-and-blend-spaces.md
  anim-instance-in-cpp.md
  montages-and-notifies.md
  ik-and-retargeting.md
  motion-matching.md
08-ui/                                (position 9, T2 — not yet written)
  umg-fundamentals.md
  slate-and-widgets-in-cpp.md
  common-ui.md
  hud-and-viewport.md
  localization-and-text.md
09-ai/                                (position 10, T2 — not yet written)
  navigation-and-navmesh.md
  behavior-trees-and-blackboard.md
  environment-query-system.md
  ai-controller-and-perception.md
  state-tree.md
10-gameplay-ability-system/           (position 11, T3 — not yet written)
  gas-overview.md
  gas-project-setup.md
  attributes-and-attribute-sets.md
  gameplay-abilities.md
  gameplay-effects.md
  gameplay-tags.md
  gameplay-cues.md
  gas-replication-and-prediction.md
  gas-cpp-patterns.md
11-world-building/                    (position 12, T3 — not yet written)
  world-partition.md
  level-instances-and-data-layers.md
  landscape-and-foliage.md
  procedural-content-generation.md
  lighting-and-lumen-setup.md
  streaming-and-budgets.md
12-rendering/                         (position 13, T3 — not yet written)
  render-thread-model.md
  nanite.md
  lumen.md
  materials-and-material-graph.md
  custom-shaders-hlsl.md
  render-dependency-graph.md
  post-process-and-view-extensions.md
  gpu-profiling.md
13-audio/                             (position 14, T4 — not yet written)
  audio-engine-overview.md
  metasounds.md
  attenuation-and-submixes.md
14-content-pipeline/                  (position 15, T4 — not yet written)
  asset-types-and-references.md
  importing-meshes-and-textures.md
  material-authoring-workflow.md
  asset-naming-and-organization.md
  asset-manager-and-soft-references.md
  cooking-and-derived-data-cache.md
15-performance-and-threading/         (position 16, T4 — not yet written)
  engine-threading-model.md
  async-tasks-and-task-graph.md
  unreal-insights.md
  stat-commands-and-console.md
  memory-budgets-and-profiling.md
  optimization-patterns.md
16-networking/                        (position 17, T4 — not yet written)
  network-model-and-authority.md
  actor-and-property-replication.md
  remote-procedure-calls.md
  relevancy-and-replication-graph.md
  movement-replication-and-prediction.md
  dedicated-servers-and-online-subsystem.md
  designing-for-later-multiplayer.md
17-editor-extension/                  (position 18, T4 — not yet written)
  editor-modules.md
  details-panel-customization.md
  custom-asset-types.md
  editor-utility-widgets.md
  commandlets-and-automation.md
18-testing-debugging-shipping/        (position 19, T4 — not yet written)
  debugging-in-visual-studio.md
  automation-and-functional-tests.md
  config-system-and-ini.md
  save-game-and-serialization.md
  packaging-and-build-targets.md
  crash-reporting.md
  release-checklist.md
```

Tell every agent explicitly: folders 05–18 do not exist on disk yet in this session. Links to them are still correct relative paths (they will exist after T2–T4) — write them, just don't expect them to resolve in this tranche's build.

---

### Task 1: Register the game-development section (config + scaffold)

**Files:**
- Modify: `sidebars.js`
- Modify: `docusaurus.config.js` (navbar `items` array, `prism.additionalLanguages`)
- Create: `docs/game-development/_category_.json`
- Create: `docs/game-development/unreal-engine/_category_.json`

**Interfaces:**
- Produces: sidebar id `gameDevSidebar`, autogenerated from `dirName: "game-development"` — Task 2 and Task 4's folders render under it automatically once they exist on disk.

- [ ] **Step 1: Add the sidebar entry**

In `sidebars.js`, add `gameDevSidebar` to the `sidebars` object (after `machineLearningSidebar`, matching the existing style):

```js
const sidebars = {
	programmingSidebar: [{ type: "autogenerated", dirName: "programming" }],
	computerScienceSidebar: [
		{ type: "autogenerated", dirName: "computer-science" },
	],
	dataStructuresSidebar: [
		{ type: "autogenerated", dirName: "data-structures-algorithms" },
	],
	dataToolsSidebar: [{ type: "autogenerated", dirName: "data-tools" }],
	machineLearningSidebar: [
		{ type: "autogenerated", dirName: "machine-learning" },
	],
	gameDevSidebar: [{ type: "autogenerated", dirName: "game-development" }],
};
```

- [ ] **Step 2: Add the navbar item**

In `docusaurus.config.js`, the navbar `items` array currently starts (around line 71) with the Programming entry, then Computer Science, Data & Algorithms, Data Tools, Machine Learning, then the GitHub link. Insert a new item **immediately after the Programming entry** (spec §3):

```js
					items: [
						{
							type: "docSidebar",
							sidebarId: "programmingSidebar",
							position: "left",
							label: "Programming",
							description:
								"Learn Python, C++, and master modern programming languages with practical examples.",
							icon: "💻",
						},
						{
							type: "docSidebar",
							sidebarId: "gameDevSidebar",
							position: "left",
							label: "Game Development",
							description:
								"Build games with Unreal Engine 5 and C++ — from engine internals to shipping.",
							icon: "🎮",
						},
						{
							type: "docSidebar",
							sidebarId: "computerScienceSidebar",
							position: "left",
							label: "Computer Science",
							description:
								"Deep dive into OS, architecture, memory management, and processor design.",
							icon: "⚙️",
						},
						// ... dataStructuresSidebar, dataToolsSidebar, machineLearningSidebar,
						// and the GitHub link entry stay exactly as they are today
```

- [ ] **Step 3: Extend Prism languages**

In `docusaurus.config.js`, in the `prism` block (currently `additionalLanguages: ["bash", "cmake"]`):

```js
				prism: {
					theme: prismThemes.github,
					darkTheme: prismThemes.dracula,
					additionalLanguages: ["bash", "cmake", "csharp", "ini"],
					additionalPlugins: ["line-numbers", "show-language"]
				},
```

`csharp` is needed because `*.Build.cs`/`*.Target.cs` are C# files; `ini` because `18-testing-debugging-shipping/config-system-and-ini.md` (T4) is about the `.ini` config system. This is a highlighting improvement — an unknown Prism language degrades to unhighlighted plain text rather than failing the build, but this has not been verified in this environment (spec §2 assumption). Watch the Step 5 build output for a Prism-related error specifically; if `csharp`/`ini` are the cause, that assumption was wrong and needs re-examination before continuing.

- [ ] **Step 4: Create the two parent `_category_.json` files**

`docs/game-development/_category_.json`:
```json
{
	"label": "Game Development",
	"position": 6,
	"link": {
		"type": "generated-index"
	}
}
```

`docs/game-development/unreal-engine/_category_.json`:
```json
{
	"label": "Unreal Engine 5",
	"position": 1,
	"link": {
		"type": "generated-index"
	}
}
```

- [ ] **Step 5: Build to confirm the site still compiles**

Run: `npm run build`

Expected: build succeeds. `docs/game-development/unreal-engine/` has no doc files yet at this point — only two `_category_.json` files and no `00-overview/` subfolder. If the build fails specifically because the `gameDevSidebar`/navbar entry has no docs to link to (an empty autogenerated sidebar), that is a real risk this plan flagged going in, not a step to route around: do not add a placeholder doc to force it green. Instead, proceed straight to Task 2 (which adds the first real docs), then re-run this exact build command before doing Task 1's commit. If the failure is anything else (a syntax error in the JS edits, a malformed navbar entry), fix it before proceeding — a malformed navbar entry breaks the whole site.

- [ ] **Step 6: Lint and format**

Run: `npm run lint` then `npm run format`

Expected: both clean (or `format` reports no changes needed) for the three files touched in this task.

- [ ] **Step 7: Commit**

Only if Step 5's build actually passed (either now, or after Task 2 content landed — see Step 5's note):

```bash
git add sidebars.js docusaurus.config.js docs/game-development/_category_.json docs/game-development/unreal-engine/_category_.json
git commit -m "chore(ue5): register game-development sidebar and navbar entry"
```

If the commit had to wait for Task 2's content to make the sidebar non-empty, still commit only these four files here — keep Task 2's folder in its own commit (Task 3).

---

### Task 2: Dispatch Batch 1 subagents — `00-overview`, `01-toolchain-and-build`, `02-cpp-in-unreal`

**Files:**
- Create: `docs/game-development/unreal-engine/00-overview/_category_.json` + 5 docs
- Create: `docs/game-development/unreal-engine/01-toolchain-and-build/_category_.json` + 8 docs
- Create: `docs/game-development/unreal-engine/02-cpp-in-unreal/_category_.json` + 11 docs

**Interfaces:**
- Consumes: Shared Subagent Brief and full manifest (above), Global Constraints.
- Produces: 24 doc files + 3 `_category_.json` files, ready for Task 3's build/lint/format pass.

- [ ] **Step 1: Dispatch 3 agents in parallel**

Use the `Agent` tool, `subagent_type: "general-purpose"`, three calls in a single message (no dependency between them). Each agent's prompt is the Shared Subagent Brief verbatim, plus the full manifest, plus this folder-specific block:

**Agent A — `00-overview` (folder position 1):**
```
FOLDER ASSIGNMENT: docs/game-development/unreal-engine/00-overview/
Position: 1. _category_.json label: "1. Overview"

Write these 5 files, in this sidebar_position order:
1. what-is-unreal-engine.md — What the engine actually is: editor,
   runtime, modules, plugins, the source-available model. Positions the
   reader.
2. engine-architecture-map.md — Mermaid map of how subsystems relate —
   where the gameplay framework sits relative to rendering, physics,
   animation. The page every later doc links back to.
3. mastery-roadmap.md — Milestone sequence (build and run, first C++
   Actor, first playable loop, first shipped build). States what to
   skip on a first pass and which folders are reference-only until
   needed. Front-load the one multiplayer rule that will live in
   16-networking/designing-for-later-multiplayer.md (not yet written —
   link to it anyway, per the manifest): keep authority checks in
   place, never assume the local client owns state, keep gameplay
   state in replicable containers.
4. cpp-vs-blueprint.md — The policy this whole section assumes: systems
   and data in C++, composition and tuning in Blueprint. Explain why,
   with the failure modes of both extremes.
5. learning-resources.md — Books, official Epic learning paths,
   community references. Every reference must be real and verifiable:
   confirm candidates before including them (e.g. Sharp, "Unreal
   Engine 5 C++ The Ultimate Developer's Handbook"; Gregory, "Game
   Engine Architecture"; Tom Looman's UE C++ material, labeled
   community-maintained not official). Omit anything you cannot
   confirm — an empty section beats a fabricated citation.
```

**Agent B — `01-toolchain-and-build` (folder position 2):**
```
FOLDER ASSIGNMENT: docs/game-development/unreal-engine/01-toolchain-and-build/
Position: 2. _category_.json label: "2. Toolchain and build"

Write these 8 files, in this sidebar_position order:
1. installation-and-versions.md — Launcher vs source build and VS2022
   workload setup. Target platform is Windows (Visual Studio 2022 /
   MSVC), engine version UE 5.7.
2. project-anatomy.md — The .uproject plus Config/ Source/ Content/
   Saved/ Intermediate/ layout and what is safe to delete.
3. unreal-build-tool.md — UBT and Build.cs module rules with
   public/private dependencies.
4. modules-and-plugins.md — Module types and loading phases, and when
   a plugin beats a module.
5. unreal-header-tool.md — UHT, .generated.h, and why a missing
   include breaks reflection.
6. build-configurations-and-targets.md — Debug / DebugGame /
   Development / Shipping across Editor and Game targets.
7. live-coding-and-hot-reload.md — What Live Coding can and cannot
   patch and when a full restart is mandatory.
8. source-control-setup.md — Git + LFS vs Perforce, and the
   .gitignore that keeps derived data (Binaries/, Intermediate/,
   Saved/, DerivedDataCache/) out.

Default to a Launcher install; call out source-build differences only
where behaviour actually differs (this is the folder where that
distinction matters most).
```

**Agent C — `02-cpp-in-unreal` (folder position 3):**
```
FOLDER ASSIGNMENT: docs/game-development/unreal-engine/02-cpp-in-unreal/
Position: 3. _category_.json label: "3. C++ in Unreal"

This is the most important folder in the section — Unreal C++ is a
dialect, and most bugs a competent C++ developer hits in their first
month trace back to here. Write these 11 files, in this
sidebar_position order:
1. uobject-and-reflection.md — The UCLASS/USTRUCT/UENUM/UPROPERTY/
   UFUNCTION specifier system and what reflection buys.
2. garbage-collection.md — Garbage collection, rooting, TObjectPtr,
   and the ownership rules that decide whether an object survives.
3. strings-and-text.md — FString vs FName vs FText and when each is
   wrong.
4. containers.md — TArray/TMap/TSet and their allocator behaviour.
5. smart-pointers-and-ownership.md — TSharedPtr/TWeakPtr/TUniquePtr
   for non-UObject data and why they must not be mixed with UObject
   ownership.
6. delegates-and-events.md — Delegate flavours and binding lifetime
   hazards.
7. interfaces.md — The UInterface two-class pattern.
8. subsystems.md — Subsystems as Unreal's dependency-injection story
   (Engine/GameInstance/World/LocalPlayer subsystems) and why they
   replace singletons.
9. logging-and-assertions.md — UE_LOG categories plus check/ensure/
   verify semantics per build config.
10. coding-standard-and-naming.md — Epic's naming and style rules.
11. unreal-cpp-vs-standard-cpp.md — Which parts of standard C++ are
    unavailable or discouraged: exceptions disabled, allocator and
    RTTI constraints, STL container trade-offs.
```

- [ ] **Step 2: Wait for all three agents to complete and read each one's final report**

Confirm each report lists all files for its folder (5 / 8 / 11 respectively), the Context7 queries run, and any claims marked `:::note::: unverified`. If an agent's report shows it skipped sourcing (no Context7 queries for a folder full of API-specific claims), that folder is not done — send it back before Task 3.

---

### Task 3: Verify and commit Batch 1

**Files:**
- Read: everything Task 2 wrote (`00-overview/`, `01-toolchain-and-build/`, `02-cpp-in-unreal/`)

- [ ] **Step 1: Build**

Run: `npm run build`

Expected: passes. `onBrokenLinks: "throw"` means it reports every broken link at once — forward links into `03-gameplay-framework/`, `04-blueprint-interop/`, or any T2–T4 folder are expected to be broken right now (those folders don't exist yet in this tranche) only if an agent linked into them; per the manifest instructions agents were told those are future paths, so such links should not appear inside Batch 1's own folders unless intentionally forward-referencing (e.g. `00-overview/mastery-roadmap.md` → `16-networking/designing-for-later-multiplayer.md`, which is expected and will resolve once T4 lands, not before — `onBrokenLinks` will flag it now). Resolve real breakage (typos, wrong relative paths, wrong filenames) in one pass; for the two intentional forward links called out in Agent A's brief, this is a known, accepted broken-link state until T4 — if `npm run build` throws on them, that means forward links must be deferred (turn them into plain text mentions for now, not markdown links) until the target tranche ships. Fix and rebuild until clean.

- [ ] **Step 2: Lint and format**

Run: `npm run lint` then `npm run format`

Expected: clean. Fix anything Biome flags in the new files.

- [ ] **Step 3: Verify against Definition of Done (spec §8 / manual §7) for this batch**

Checklist:
- All 24 planned files exist with valid frontmatter and one `_category_.json` per folder.
- Sidebar labels: "1. Overview", "2. Toolchain and build", "3. C++ in Unreal" — in that order.
- Every engine-specific claim traceable to a spec §6 source per the agents' reports; unverifiable ones carry an inline `:::note`.
- No `TODO`, no placeholder text, no empty sections.

- [ ] **Step 4: Commit each folder separately**

```bash
git add docs/game-development/unreal-engine/00-overview
git commit -m "docs(ue5): add overview section"

git add docs/game-development/unreal-engine/01-toolchain-and-build
git commit -m "docs(ue5): add toolchain and build section"

git add docs/game-development/unreal-engine/02-cpp-in-unreal
git commit -m "docs(ue5): add C++ in Unreal section"
```

If Task 1's commit was deferred waiting for a non-empty sidebar (see Task 1 Step 5), commit Task 1's four config files now, before these three, as its own `chore(ue5): ...` commit.

---

### Task 4: Dispatch Batch 2 subagents — `03-gameplay-framework`, `04-blueprint-interop`

**Files:**
- Create: `docs/game-development/unreal-engine/03-gameplay-framework/_category_.json` + 8 docs
- Create: `docs/game-development/unreal-engine/04-blueprint-interop/_category_.json` + 5 docs

**Interfaces:**
- Consumes: Shared Subagent Brief, full manifest, Global Constraints — same as Task 2. Agents may link back into `02-cpp-in-unreal/` (now on disk) for concepts like `UPROPERTY` specifiers or `TObjectPtr`.
- Produces: 13 doc files + 2 `_category_.json` files, ready for Task 5's build/lint/format pass.

- [ ] **Step 1: Dispatch 2 agents in parallel**

Use the `Agent` tool, `subagent_type: "general-purpose"`, two calls in a single message. Each agent's prompt is the Shared Subagent Brief verbatim, plus the full manifest, plus this folder-specific block:

**Agent D — `03-gameplay-framework` (folder position 4):**
```
FOLDER ASSIGNMENT: docs/game-development/unreal-engine/03-gameplay-framework/
Position: 4. _category_.json label: "4. Gameplay framework"

Write these 8 files, in this sidebar_position order:
1. framework-overview.md — The ownership diagram tying all framework
   classes together (mermaid).
2. game-mode-and-game-state.md — Authority and rules in GameMode vs
   replicated state in GameState.
3. player-controller-and-player-state.md — Input and possession in
   PlayerController vs persistent player data in PlayerState.
4. pawn-and-character.md — Pawn vs Character and what ACharacter adds.
5. actor-lifecycle.md — The full actor lifecycle with initialisation
   order (PostInitializeComponents, BeginPlay, Tick, EndPlay,
   destruction) and the ordering traps.
6. actor-components.md — Actor components vs scene components and
   attachment rules.
7. world-and-levels.md — World, Level, and world context.
8. game-instance.md — GameInstance for data that outlives a level.

02-cpp-in-unreal/ is already on disk — link back to it for concepts
this folder assumes (subsystems.md for GameInstanceSubsystem, etc.)
instead of re-explaining them.
```

**Agent E — `04-blueprint-interop` (folder position 5):**
```
FOLDER ASSIGNMENT: docs/game-development/unreal-engine/04-blueprint-interop/
Position: 5. _category_.json label: "5. Blueprint interop"

Write these 5 files, in this sidebar_position order:
1. exposing-cpp-to-blueprint.md — The specifier cookbook
   (BlueprintReadWrite, BlueprintCallable, BlueprintNativeEvent,
   BlueprintImplementableEvent, EditAnywhere families) with a decision
   table.
2. cpp-base-blueprint-derived.md — The C++ base class → Blueprint
   derived class pattern that is the backbone of professional UE
   projects.
3. blueprint-function-libraries.md — Static function libraries.
4. data-driven-design.md — Data-driven design with DataTable,
   DataAsset, PrimaryDataAsset, and curves so designers tune without
   recompiles.
5. blueprint-performance.md — An honest look at Blueprint VM cost and
   where it does and does not matter.

02-cpp-in-unreal/ and 03-gameplay-framework/ are already on disk —
link back into them rather than re-explaining UPROPERTY/UFUNCTION
mechanics or the Actor lifecycle.
```

- [ ] **Step 2: Wait for both agents to complete and read each one's final report**

Same check as Task 2 Step 2: file count matches (8 / 5), Context7 was actually used, unverifiable claims are marked.

---

### Task 5: Verify and commit Batch 2

**Files:**
- Read: everything Task 4 wrote (`03-gameplay-framework/`, `04-blueprint-interop/`)

- [ ] **Step 1: Build**

Run: `npm run build`

Expected: passes, including now-resolvable links from Batch 1 into `03-gameplay-framework/` or `04-blueprint-interop/` that were forward references before. Fix any real breakage and rebuild until clean.

- [ ] **Step 2: Lint and format**

Run: `npm run lint` then `npm run format`

Expected: clean.

- [ ] **Step 3: Verify against Definition of Done for this batch**

Same checklist shape as Task 3 Step 3, applied to these 13 files: valid frontmatter, `_category_.json` present with correct labels ("4. Gameplay framework", "5. Blueprint interop"), claims traceable or marked, no placeholders.

- [ ] **Step 4: Commit each folder separately**

```bash
git add docs/game-development/unreal-engine/03-gameplay-framework
git commit -m "docs(ue5): add gameplay framework section"

git add docs/game-development/unreal-engine/04-blueprint-interop
git commit -m "docs(ue5): add Blueprint interop section"
```

---

### Task 6: Tranche T1 completion verification

**Files:**
- Read: all of `docs/game-development/`, `sidebars.js`, `docusaurus.config.js`

- [ ] **Step 1: Run `superpowers:verification-before-completion`**

Before claiming T1 done: re-run `npm run build`, `npm run lint`, `npm run format` fresh (not from memory of Task 3/5's runs), confirm exit codes, and confirm no uncommitted changes remain (`git status`).

- [ ] **Step 2: Confirm all six Definition-of-Done criteria (spec §8) hold for the full tranche**

1. All 37 planned files exist, valid frontmatter, `_category_.json` per folder (5 folders).
2. `npm run build` passes.
3. `npm run lint` and `npm run format` clean.
4. Sidebar order and folder labels match the TOC: "1. Overview", "2. Toolchain and build", "3. C++ in Unreal", "4. Gameplay framework", "5. Blueprint interop".
5. Every engine-specific claim traceable to a spec §6 source; unverified claims marked inline with `:::note`.
6. No `TODO`, no placeholder text, no empty sections.

- [ ] **Step 3: Report to the user**

State plainly: what was written (5 folders, 37 docs + config wiring), what was verified against Context7 (summarize per-folder from the agents' reports), what was marked unverified and where, what was skipped and why (if anything), and the final `npm run build` / `lint` / `format` results. Do not claim anything passed that was not actually run in this session.

---

## Self-Review Notes

- **Spec coverage:** §3 config changes → Task 1. §4 TOC folders 00–04 → Tasks 2–5. §5 per-doc contract → Shared Subagent Brief. §6 sourcing rules → Shared Subagent Brief + Global Constraints. §7 references policy → Agent A's `learning-resources.md` block. §8 delivery-plan T1 acceptance criteria → Task 6. Manual §3 subagent dispatch rules, §5 verification gates, §6 commit policy, §7 definition of done, §8 "do not" list → all folded into Tasks 1–6 and Global Constraints.
- **Placeholder scan:** no "TBD"/"implement later"/"similar to Task N" in this plan; every dispatch task carries its full agent prompt inline rather than pointing at another task.
- **Type/name consistency:** folder names, position numbers, and `_category_.json` labels match across the manifest, Global Constraints, and every task. Commit subjects match the manual's example list verbatim for the first three (`docs(ue5): add overview section`, `docs(ue5): add toolchain and build section`, `docs(ue5): add C++ in Unreal section`) and follow the same pattern for the two not covered by the manual's example.
