# Linux & Kernel Section — Phase 1a (Infrastructure and Scaffold) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build every piece of site machinery the `docs/linux/` section needs, then scaffold folders 00–04 so that all 46 pages exist as linkable stubs with a complete, build-validated prerequisite graph.

**Architecture:** One Docusaurus plugin reads a custom `prerequisites` front-matter key from every doc under `linux/`, validates it (unknown id, cycle, or missing key fails the build), and publishes a node/edge graph as global data. A swizzled `DocItem/Layout` renders prerequisite and next-topic links from that graph with zero per-page markup. Six MDX components (`Src`, `KernelFacts`, `Lab`, `Video`, `Cast`, `KnowledgeGraph`) are registered globally so pages stay plain `.md`. A manifest-driven generator writes the stub tree.

**Tech Stack:** Docusaurus 3.10.2, React 19, Node 22 (`node --test` for unit tests — already the repo's convention via `npm run test:plugins`), Biome 2.5.7, `asciinema-player` 3.17.

**Spec:** `docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md`

## Global Constraints

- **Pinned kernel version is `v6.18`** — released 2025-11-30, longterm, projected EOL Dec 2028. Verified against `kernel.org/category/releases.html` on 2026-08-28. It is the newest LTS with more than two years of remaining support, which is the spec's selection rule.
- **No line numbers in any source citation.** Only `path/file.c` and `symbol()`. Both Elixir routes were verified live on 2026-08-28 for v6.18: `https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c` and `https://elixir.bootlin.com/linux/v6.18/ident/path_openat`.
- **`onBrokenLinks: "throw"`** is already set in `docusaurus.config.js`. A broken internal link fails the build. This is why the scaffold task exists.
- **Every doc under `docs/linux/` must carry a `prerequisites` front-matter key.** An empty array is valid; a missing key fails the build by design.
- Biome formats `**/*.js`, `**/*.jsx`, `**/*.ts`, `**/*.tsx`, `**/*.json`, `**/*.md` at 2-space indent. It does **not** cover `.mjs`, which is why `tools/*.mjs` and `scripts/*.test.mjs` are exempt. Run `npm run lint` before each commit.
- **Commit messages:** `<type>: <what>` on one line. Never add a `Co-Authored-By` trailer or a "Generated with Claude Code" line. This repo's `CLAUDE.md` forbids both.
- Node 22 detects ESM syntax in a `.js` file with no `"type"` field in `package.json`. The existing `npm run test:plugins` script passes `--disable-warning=MODULE_TYPELESS_PACKAGE_JSON` for exactly this reason; new test scripts do the same.

---

## File Structure

**New — library and plugin logic**

| File | Responsibility |
|---|---|
| `src/lib/kernelSource.js` | Pure functions building Elixir URLs and labels from the pinned version. No React. |
| `src/plugins/knowledge-graph/buildGraph.js` | Pure function: docs array → `{nodes, edges, related}`, throwing on invalid input. No Docusaurus imports. |
| `src/plugins/knowledge-graph-plugin.js` | Thin Docusaurus plugin shell. Extracts docs from `allContent`, calls `buildGraph`, calls `setGlobalData`. |

**New — components**

| File | Responsibility |
|---|---|
| `src/components/Src/index.jsx` | Inline pinned source reference. |
| `src/components/PrereqBlock/index.jsx` | Before/Next/Related chip rows, read from global data. |
| `src/components/KernelFacts/index.jsx` | The fixed four-row closing card. |
| `src/components/Lab/index.jsx` | Hands-on block with a required host badge. |
| `src/components/Video/index.jsx` | Responsive lazy iframe for an embedded talk. |
| `src/components/Cast/index.jsx` | asciinema player, client-side only. |
| `src/components/KnowledgeGraph/index.jsx` | Mermaid graph generated from global data. |
| `src/css/linux-components.css` | All CSS for the seven components above, in one file rather than growing the 2094-line `custom.css`. |

**New — tooling**

| File | Responsibility |
|---|---|
| `scripts/kernel-source.test.mjs` | Unit tests for `kernelSource.js`. |
| `scripts/build-graph.test.mjs` | Unit tests for `buildGraph.js`. |
| `tools/linux-docs-manifest.json` | The single source of truth for the section's page tree. |
| `tools/scaffold-linux-docs.mjs` | Manifest → stub `.md` files and `_category_.json` files. Never overwrites an existing page. |
| `tools/check-linux-docs.mjs` | Authoring-convention gate: `_category_.json` descriptions, front-matter keys, stub accounting. |

**Modified**

| File | Change |
|---|---|
| `docusaurus.config.js` | `customFields.linuxKernelVersion`, the plugin registration, four Prism languages, the navbar item, the second `customCss` entry. |
| `sidebars.js` | `linuxSidebar`. |
| `src/theme/MDXComponents.js` | Register the six page-facing components. |
| `src/theme/DocItem/Layout/index.js` | Inject `<PrereqBlock>` twice. |
| `package.json` | `asciinema-player` dependency; `test:kernel-source`, `test:graph`, `check:linux` scripts. |

---

## Task 1: Pin the kernel version and build `<Src>`

**Files:**
- Create: `src/lib/kernelSource.js`
- Create: `scripts/kernel-source.test.mjs`
- Create: `src/components/Src/index.jsx`
- Modify: `docusaurus.config.js` (`customFields`)
- Modify: `src/theme/MDXComponents.js`
- Modify: `package.json` (scripts)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `normalizeVersion(version: string): string` — `"6.18"` and `"v6.18"` both → `"v6.18"`.
  - `sourceUrl(version: string, file: string): string`
  - `identUrl(version: string, symbol: string): string`
  - `srcLabel({file?: string, symbol?: string}): string`
  - `srcHref(version: string, {file?: string, symbol?: string}): string`
  - `<Src file="fs/namei.c" symbol="path_openat" />` MDX component.

- [ ] **Step 1: Write the failing test**

Create `scripts/kernel-source.test.mjs`:

```js
import assert from "node:assert/strict";
import test from "node:test";
import {
  identUrl,
  normalizeVersion,
  sourceUrl,
  srcHref,
  srcLabel,
} from "../src/lib/kernelSource.js";

test("normalizeVersion accepts both v-prefixed and bare versions", () => {
  assert.equal(normalizeVersion("6.18"), "v6.18");
  assert.equal(normalizeVersion("v6.18"), "v6.18");
});

test("sourceUrl points at the Elixir source route", () => {
  assert.equal(
    sourceUrl("v6.18", "fs/namei.c"),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("sourceUrl strips a leading slash from the file path", () => {
  assert.equal(
    sourceUrl("v6.18", "/fs/namei.c"),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("identUrl points at the Elixir identifier route", () => {
  assert.equal(
    identUrl("v6.18", "path_openat"),
    "https://elixir.bootlin.com/linux/v6.18/ident/path_openat",
  );
});

test("srcLabel renders file and symbol together", () => {
  assert.equal(
    srcLabel({ file: "fs/namei.c", symbol: "path_openat" }),
    "fs/namei.c:path_openat()",
  );
});

test("srcLabel renders a bare file and a bare symbol", () => {
  assert.equal(srcLabel({ file: "mm/memory.c" }), "mm/memory.c");
  assert.equal(srcLabel({ symbol: "handle_mm_fault" }), "handle_mm_fault()");
});

test("srcHref prefers the ident route whenever a symbol is given", () => {
  assert.equal(
    srcHref("v6.18", { file: "fs/namei.c", symbol: "path_openat" }),
    "https://elixir.bootlin.com/linux/v6.18/ident/path_openat",
  );
  assert.equal(
    srcHref("v6.18", { file: "fs/namei.c" }),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("no generated URL ever contains a line number anchor", () => {
  const urls = [
    sourceUrl("v6.18", "fs/namei.c"),
    identUrl("v6.18", "path_openat"),
    srcHref("v6.18", { file: "fs/namei.c", symbol: "path_openat" }),
  ];
  for (const url of urls) {
    assert.ok(!url.includes("#L"), `${url} contains a line anchor`);
  }
});

test("srcLabel throws when given neither a file nor a symbol", () => {
  assert.throws(() => srcLabel({}), /file.*symbol/i);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/kernel-source.test.mjs
```

Expected: FAIL — `Cannot find module '.../src/lib/kernelSource.js'`.

- [ ] **Step 3: Write the implementation**

Create `src/lib/kernelSource.js`:

```js
// Builds elixir.bootlin.com URLs for the pinned kernel version.
//
// Deliberately line-number-free: line numbers rot within one release, while
// file paths and symbol names survive for years. Elixir's `ident/` route
// resolves a symbol to its definition and all its uses with no line number,
// which is why it is preferred whenever a symbol is known.
//
// The version itself lives in one place only — `customFields.linuxKernelVersion`
// in docusaurus.config.js — so re-pinning the section is a one-line change.

const ELIXIR_BASE = "https://elixir.bootlin.com/linux";

export function normalizeVersion(version) {
  const trimmed = String(version).trim();
  return trimmed.startsWith("v") ? trimmed : `v${trimmed}`;
}

export function sourceUrl(version, file) {
  const path = String(file).replace(/^\/+/, "");
  return `${ELIXIR_BASE}/${normalizeVersion(version)}/source/${path}`;
}

export function identUrl(version, symbol) {
  return `${ELIXIR_BASE}/${normalizeVersion(version)}/ident/${symbol}`;
}

export function srcLabel({ file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  if (file && symbol) return `${file}:${symbol}()`;
  if (file) return file;
  return `${symbol}()`;
}

export function srcHref(version, { file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  return symbol ? identUrl(version, symbol) : sourceUrl(version, file);
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/kernel-source.test.mjs
```

Expected: PASS — 9 tests, 0 failures.

- [ ] **Step 5: Add the npm script**

In `package.json`, add to `"scripts"` immediately after the existing `"test:plugins"` line:

```json
"test:kernel-source": "node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/kernel-source.test.mjs",
```

- [ ] **Step 6: Add the pinned version to the site config**

In `docusaurus.config.js`, replace the existing `customFields` block (currently at line 23) with:

```js
  customFields: {
    githubUrl: "https://github.com/AndriiSonsiadlo/knowledge-base",
    // The Linux section is pinned to one LTS. Every source link on every page
    // is generated from this value by <Src>. Bumping it re-points the whole
    // section; see docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md.
    // v6.18: released 2025-11-30, longterm, projected EOL Dec 2028.
    linuxKernelVersion: "v6.18",
  },
```

- [ ] **Step 7: Write the `<Src>` component**

Create `src/components/Src/index.jsx`:

```jsx
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { srcHref, srcLabel } from "@lib/kernelSource";

// <Src /> — an inline reference into the pinned kernel source.
//
// Usage in markdown:
//   Path resolution happens in <Src file="fs/namei.c" symbol="path_openat" />.
//   The allocator lives in <Src file="mm/page_alloc.c" />.
//   <Src symbol="handle_mm_fault" /> is the entry point.
//
// Never hand-write an elixir.bootlin.com URL in a page — the version would
// then be duplicated across hundreds of files.
export default function Src({ file, symbol }) {
  const { siteConfig } = useDocusaurusContext();
  const version = siteConfig.customFields.linuxKernelVersion;
  return (
    <a
      className="kb-src"
      href={srcHref(version, { file, symbol })}
      target="_blank"
      rel="noopener noreferrer"
    >
      <code>{srcLabel({ file, symbol })}</code>
    </a>
  );
}
```

- [ ] **Step 8: Register it globally**

In `src/theme/MDXComponents.js`, add the import alongside the existing ones (imports are alphabetised by Biome's organize-imports assist, so put it in order):

```js
import Src from "@site/src/components/Src";
```

and add `Src,` to the default-export object alongside `Icon`, `Figure`, `Recall`, `WaveDrom`.

- [ ] **Step 9: Verify the build is still green**

Run:

```bash
npm run lint && npm run build
```

Expected: lint clean, build succeeds. `<Src>` is registered but not yet used by any page, which is fine.

- [ ] **Step 10: Commit**

```bash
git add src/lib/kernelSource.js scripts/kernel-source.test.mjs src/components/Src/index.jsx src/theme/MDXComponents.js docusaurus.config.js package.json
git commit -m "feat: pin Linux docs to v6.18 and add <Src> source-link component"
```

---

## Task 2: The knowledge-graph builder

Pure logic, no Docusaurus imports, so it is unit-testable without a build. The plugin shell in Task 3 is a five-line wrapper around this.

**Files:**
- Create: `src/plugins/knowledge-graph/buildGraph.js`
- Create: `scripts/build-graph.test.mjs`
- Modify: `package.json` (scripts)

**Interfaces:**
- Consumes: nothing.
- Produces: `buildGraph(docs, options): {nodes, edges, related}` where
  - `docs` is an array of Docusaurus doc metadata objects, each with `id`, `title`, `permalink`, `source`, `sourceDirName`, and `frontMatter` (verified against `@docusaurus/plugin-content-docs/src/plugin-content-docs.d.ts:464`, where `frontMatter` is typed `DocFrontMatter & {[key: string]: unknown}` — custom keys pass through).
  - `options` is `{ scopes?: string[] }`, default `["linux/"]`.
  - `nodes` is `[{ id, title, label, permalink, folder, external }]`.
  - `edges` is `[{ from, to }]` for prerequisites (`from` depends on `to`).
  - `related` is `[{ from, to }]` for lateral links.
- Throws an `Error` whose message lists **every** problem found, not just the first.

- [ ] **Step 1: Write the failing test**

Create `scripts/build-graph.test.mjs`:

```js
import assert from "node:assert/strict";
import test from "node:test";
import { buildGraph } from "../src/plugins/knowledge-graph/buildGraph.js";

// Minimal stand-in for Docusaurus doc metadata. Only the fields buildGraph
// reads are present, which is also the documentation of what it depends on.
function doc(id, frontMatter = {}, extra = {}) {
  const segments = id.split("/");
  return {
    id,
    title: extra.title ?? segments[segments.length - 1],
    permalink: `/docs/${id}`,
    source: `@site/docs/${id}.md`,
    sourceDirName: segments.slice(0, -1).join("/"),
    frontMatter: { prerequisites: [], ...frontMatter },
    ...extra,
  };
}

test("builds a node per in-scope doc and an edge per prerequisite", () => {
  const graph = buildGraph([
    doc("linux/00-overview/a"),
    doc("linux/00-overview/b", { prerequisites: ["linux/00-overview/a"] }),
  ]);
  assert.equal(graph.nodes.length, 2);
  assert.deepEqual(graph.edges, [
    { from: "linux/00-overview/b", to: "linux/00-overview/a" },
  ]);
});

test("node carries the folder, the sidebar label, and the permalink", () => {
  const graph = buildGraph([
    doc("linux/08-memory-management/page-tables", {
      sidebar_label: "Page tables",
    }),
  ]);
  const [node] = graph.nodes;
  assert.equal(node.folder, "08-memory-management");
  assert.equal(node.label, "Page tables");
  assert.equal(node.permalink, "/docs/linux/08-memory-management/page-tables");
  assert.equal(node.external, false);
});

test("label falls back to the title when sidebar_label is absent", () => {
  const graph = buildGraph([
    doc("linux/00-overview/a", {}, { title: "What This Covers" }),
  ]);
  assert.equal(graph.nodes[0].label, "What This Covers");
});

test("an out-of-scope prerequisite target becomes an external node", () => {
  const graph = buildGraph([
    doc("linux/05-syscalls/entry", {
      prerequisites: ["computer-science/cpu-architecture/privilege-levels"],
    }),
    doc("computer-science/cpu-architecture/privilege-levels"),
  ]);
  const external = graph.nodes.find((n) => n.external);
  assert.equal(external.id, "computer-science/cpu-architecture/privilege-levels");
  assert.equal(graph.nodes.length, 2);
});

test("out-of-scope docs that nobody references are not nodes", () => {
  const graph = buildGraph([
    doc("linux/00-overview/a"),
    doc("programming/python/lists"),
  ]);
  assert.equal(graph.nodes.length, 1);
});

test("out-of-scope docs are not required to declare prerequisites", () => {
  const bare = { id: "programming/python/lists", frontMatter: {} };
  assert.doesNotThrow(() => buildGraph([doc("linux/00-overview/a"), bare]));
});

test("collects related edges separately from prerequisite edges", () => {
  const graph = buildGraph([
    doc("linux/00-overview/a"),
    doc("linux/00-overview/b", { related: ["linux/00-overview/a"] }),
  ]);
  assert.equal(graph.edges.length, 0);
  assert.deepEqual(graph.related, [
    { from: "linux/00-overview/b", to: "linux/00-overview/a" },
  ]);
});

test("throws when an in-scope doc omits the prerequisites key", () => {
  const missing = {
    id: "linux/00-overview/a",
    title: "a",
    permalink: "/docs/linux/00-overview/a",
    source: "@site/docs/linux/00-overview/a.md",
    sourceDirName: "linux/00-overview",
    frontMatter: {},
  };
  assert.throws(() => buildGraph([missing]), (err) => {
    assert.match(err.message, /a\.md/);
    assert.match(err.message, /prerequisites/);
    return true;
  });
});

test("throws on an unresolvable prerequisite id and suggests near matches", () => {
  assert.throws(
    () =>
      buildGraph([
        doc("linux/00-overview/glossary"),
        doc("linux/00-overview/b", { prerequisites: ["linux/00-overview/glosary"] }),
      ]),
    (err) => {
      assert.match(err.message, /glosary/);
      assert.match(err.message, /linux\/00-overview\/glossary/);
      return true;
    },
  );
});

test("throws on a prerequisite cycle and prints the path", () => {
  assert.throws(
    () =>
      buildGraph([
        doc("linux/a/one", { prerequisites: ["linux/a/two"] }),
        doc("linux/a/two", { prerequisites: ["linux/a/one"] }),
      ]),
    (err) => {
      assert.match(err.message, /cycle/i);
      assert.match(err.message, /linux\/a\/one/);
      assert.match(err.message, /linux\/a\/two/);
      return true;
    },
  );
});

test("a page listing itself as a prerequisite is a cycle", () => {
  assert.throws(
    () => buildGraph([doc("linux/a/one", { prerequisites: ["linux/a/one"] })]),
    /cycle/i,
  );
});

test("reports every problem at once, not just the first", () => {
  assert.throws(
    () =>
      buildGraph([
        doc("linux/a/one", { prerequisites: ["linux/a/nope"] }),
        doc("linux/a/two", { prerequisites: ["linux/a/also-nope"] }),
      ]),
    (err) => {
      assert.match(err.message, /nope/);
      assert.match(err.message, /also-nope/);
      return true;
    },
  );
});

test("a diamond dependency is not a cycle", () => {
  const graph = buildGraph([
    doc("linux/a/base"),
    doc("linux/a/left", { prerequisites: ["linux/a/base"] }),
    doc("linux/a/right", { prerequisites: ["linux/a/base"] }),
    doc("linux/a/top", { prerequisites: ["linux/a/left", "linux/a/right"] }),
  ]);
  assert.equal(graph.edges.length, 4);
});

test("respects a custom scope", () => {
  const graph = buildGraph([doc("embedded/00/a"), doc("linux/00-overview/b")], {
    scopes: ["embedded/"],
  });
  assert.equal(graph.nodes.length, 1);
  assert.equal(graph.nodes[0].id, "embedded/00/a");
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/build-graph.test.mjs
```

Expected: FAIL — `Cannot find module '.../src/plugins/knowledge-graph/buildGraph.js'`.

- [ ] **Step 3: Write the implementation**

Create `src/plugins/knowledge-graph/buildGraph.js`:

```js
// Turns Docusaurus doc metadata into the section's prerequisite graph.
//
// Pure: no Docusaurus imports, no filesystem, no side effects. The plugin
// shell in ../knowledge-graph-plugin.js is a thin wrapper around this, which
// is what makes the validation rules unit-testable.
//
// Validation is deliberately fatal. The repository already sets
// `onBrokenLinks: "throw"`; a prerequisite graph that silently rots would be
// worse than no graph, because the rendered "Before this" block would quietly
// lose entries with nothing to notice it.

const DEFAULT_SCOPES = ["linux/"];

function inScope(id, scopes) {
  return scopes.some((scope) => id.startsWith(scope));
}

function folderOf(doc) {
  const segments = doc.sourceDirName ? doc.sourceDirName.split("/") : [];
  return segments.length > 1 ? segments[segments.length - 1] : "";
}

// Small Levenshtein, used only to make a typo'd id cheap to fix.
function distance(a, b) {
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    const row = [i];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      row[j] = Math.min(row[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);
    }
    prev = row;
  }
  return prev[b.length];
}

function suggest(target, candidates) {
  return [...candidates]
    .map((id) => [distance(target, id), id])
    .sort((a, b) => a[0] - b[0])
    .slice(0, 3)
    .map(([, id]) => id);
}

// Iterative DFS with three colours. Returns the first cycle as a path, or null.
function findCycle(adjacency) {
  const WHITE = 0;
  const GREY = 1;
  const BLACK = 2;
  const colour = new Map();
  for (const id of adjacency.keys()) colour.set(id, WHITE);

  for (const root of adjacency.keys()) {
    if (colour.get(root) !== WHITE) continue;
    const stack = [{ id: root, path: [root] }];
    while (stack.length > 0) {
      const { id, path } = stack.pop();
      if (colour.get(id) === BLACK) continue;
      colour.set(id, GREY);
      for (const next of adjacency.get(id) ?? []) {
        if (colour.get(next) === GREY || next === id) {
          return [...path, next];
        }
        if (colour.get(next) === WHITE) {
          stack.push({ id: next, path: [...path, next] });
        }
      }
      colour.set(id, BLACK);
    }
  }
  return null;
}

function listOf(frontMatter, key) {
  const value = frontMatter?.[key];
  return Array.isArray(value) ? value : [];
}

export function buildGraph(docs, options = {}) {
  const scopes = options.scopes ?? DEFAULT_SCOPES;
  const byId = new Map(docs.map((doc) => [doc.id, doc]));
  const scoped = docs.filter((doc) => inScope(doc.id, scopes));
  const problems = [];

  // 1. Every in-scope page must declare the key. Empty is fine; absent is not,
  //    or coverage decays silently as pages are added.
  for (const doc of scoped) {
    if (!Array.isArray(doc.frontMatter?.prerequisites)) {
      problems.push(
        `${doc.source}: missing the required "prerequisites" front matter key. ` +
          `Use "prerequisites: []" if this page genuinely has none.`,
      );
    }
  }

  // 2. Every referenced id must resolve.
  const edges = [];
  const related = [];
  const referenced = new Set();
  for (const doc of scoped) {
    for (const [key, sink] of [
      ["prerequisites", edges],
      ["related", related],
    ]) {
      for (const target of listOf(doc.frontMatter, key)) {
        if (!byId.has(target)) {
          const near = suggest(target, byId.keys());
          problems.push(
            `${doc.source}: ${key} names "${target}", which is not a doc id. ` +
              `Closest existing ids: ${near.join(", ")}`,
          );
          continue;
        }
        referenced.add(target);
        sink.push({ from: doc.id, to: target });
      }
    }
  }

  if (problems.length > 0) {
    throw new Error(
      `knowledge-graph-plugin found ${problems.length} problem(s):\n  - ${problems.join("\n  - ")}`,
    );
  }

  // 3. No cycles. A prerequisite cycle means no valid reading order exists.
  const adjacency = new Map();
  for (const doc of scoped) adjacency.set(doc.id, []);
  for (const edge of edges) {
    if (adjacency.has(edge.from)) adjacency.get(edge.from).push(edge.to);
  }
  const cycle = findCycle(adjacency);
  if (cycle) {
    throw new Error(
      `knowledge-graph-plugin found a prerequisite cycle:\n  ${cycle.join("\n    -> ")}\n` +
        `Prerequisites must form a DAG — break the loop by demoting one edge to "related".`,
    );
  }

  // 4. Nodes: every in-scope doc, plus any out-of-scope doc someone depends on.
  const nodeIds = new Set(scoped.map((doc) => doc.id));
  for (const id of referenced) nodeIds.add(id);

  const nodes = [...nodeIds].map((id) => {
    const doc = byId.get(id);
    return {
      id,
      title: doc.title,
      label: doc.frontMatter?.sidebar_label ?? doc.title,
      permalink: doc.permalink,
      folder: folderOf(doc),
      external: !inScope(id, scopes),
    };
  });

  return { nodes, edges, related };
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/build-graph.test.mjs
```

Expected: PASS — 14 tests, 0 failures.

- [ ] **Step 5: Add the npm script**

In `package.json`, after `"test:kernel-source"`:

```json
"test:graph": "node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test scripts/build-graph.test.mjs",
```

- [ ] **Step 6: Commit**

```bash
git add src/plugins/knowledge-graph/buildGraph.js scripts/build-graph.test.mjs package.json
git commit -m "feat: add knowledge-graph builder with cycle and reference validation"
```

---

## Task 3: The plugin shell and its registration

**Files:**
- Create: `src/plugins/knowledge-graph-plugin.js`
- Modify: `docusaurus.config.js` (import + `plugins` array)

**Interfaces:**
- Consumes: `buildGraph(docs, options)` from Task 2.
- Produces: global data under the plugin name `"knowledge-graph-plugin"`, shaped `{nodes, edges, related}`. Read in later tasks with `usePluginData("knowledge-graph-plugin")`.

- [ ] **Step 1: Write the plugin**

Create `src/plugins/knowledge-graph-plugin.js`:

```js
import { buildGraph } from "./knowledge-graph/buildGraph.js";

// Publishes the docs/linux/ prerequisite graph as global data, and fails the
// build if that graph is invalid. All the logic — and all the tests — live in
// ./knowledge-graph/buildGraph.js; this is only the Docusaurus wiring.
//
// Modelled on ./recent-docs-plugin.js, which uses the same allContentLoaded +
// setGlobalData pair.
export default function knowledgeGraphPlugin(_context, options = {}) {
  return {
    name: "knowledge-graph-plugin",
    async allContentLoaded({ allContent, actions }) {
      const docsContent = allContent["docusaurus-plugin-content-docs"]?.default;
      const docs = docsContent
        ? docsContent.loadedVersions.flatMap((version) => version.docs)
        : [];
      actions.setGlobalData(buildGraph(docs, options));
    },
  };
}
```

- [ ] **Step 2: Register it in the site config**

In `docusaurus.config.js`, add the import next to the existing `remarkWavedrom` import at the top of the file:

```js
import knowledgeGraphPlugin from "./src/plugins/knowledge-graph-plugin.js";
```

Then in the `plugins` array (currently starting at line 291), add as the fourth entry, immediately after the `recent-docs-plugin` line:

```js
    [knowledgeGraphPlugin, { scopes: ["linux/"] }],
```

The plugin is passed as an imported function rather than a path string — unlike the three above it — because the file uses ESM `export default`, and passing the function directly removes any question about how Docusaurus resolves the module format. `remark-wavedrom.js` is already imported this way.

- [ ] **Step 3: Verify the build is green with an empty scope**

Run:

```bash
npm run build
```

Expected: build succeeds. No `docs/linux/` exists yet, so `buildGraph` gets an empty scoped set and publishes an empty graph. This proves the plugin loads and does not crash before any content depends on it.

- [ ] **Step 4: Prove the missing-key rule actually fails the build**

Create a throwaway file `docs/linux/tmp-probe.md`:

```md
---
title: Probe
---

# Probe

Temporary file used to prove the plugin's validation fires.
```

Run:

```bash
npm run build
```

Expected: FAIL, with a message containing `missing the required "prerequisites" front matter key` and the path `docs/linux/tmp-probe.md`.

- [ ] **Step 5: Prove the unresolvable-id rule fails the build**

Edit `docs/linux/tmp-probe.md` to:

```md
---
title: Probe
prerequisites:
  - linux/does-not-exist
---

# Probe

Temporary file used to prove the plugin's validation fires.
```

Run:

```bash
npm run build
```

Expected: FAIL, with a message containing `is not a doc id` and `Closest existing ids:`.

- [ ] **Step 6: Remove the probe and confirm green again**

Run:

```bash
rm docs/linux/tmp-probe.md
rmdir docs/linux
npm run build
```

Expected: PASS. The cycle rule is covered by unit tests in Task 2 and will be exercised against real content in Task 5.

- [ ] **Step 7: Commit**

```bash
git add src/plugins/knowledge-graph-plugin.js docusaurus.config.js
git commit -m "feat: register knowledge-graph plugin; graph errors now fail the build"
```

---

## Task 4: Section wiring and the landing page

Creates the minimum content needed for a `linux` sidebar to exist, plus every config change the section needs.

**Files:**
- Create: `docs/linux/readme.md`
- Create: `src/css/linux-components.css`
- Modify: `sidebars.js`
- Modify: `docusaurus.config.js` (navbar, Prism, `customCss`)

**Interfaces:**
- Consumes: `customFields.linuxKernelVersion` from Task 1.
- Produces: the `linuxSidebar` id, the `.kb-src` / `.kb-prereq` / `.kb-kernel-facts` / `.kb-lab` / `.kb-video` / `.kb-cast` class namespace.

- [ ] **Step 1: Add the sidebar**

In `sidebars.js`, add after the `embeddedSidebar` entry:

```js
  linuxSidebar: [{ type: "autogenerated", dirName: "linux" }],
```

- [ ] **Step 2: Add the navbar item**

In `docusaurus.config.js`, inside the `Systems` dropdown's `items` array, after the `embeddedSidebar` entry (which ends at line 149):

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

The `terminal` icon is already present in `src/components/lucide-subset.json`, so `npm run gen-icons` is **not** needed.

- [ ] **Step 3: Add the four Prism languages**

In `docusaurus.config.js`, `themeConfig.prism.additionalLanguages` (line 253) — the list is alphabetical, so insert to keep it so:

```js
        additionalLanguages: [
          "armasm",
          "bash",
          "c",
          "cmake",
          "cpp",
          "csharp",
          "diff",
          "docker",
          "glsl",
          "hlsl",
          "ini",
          "json",
          "makefile",
          "nasm",
          "python",
          "systemd",
          "toml",
          "wgsl",
          "yaml",
        ],
```

All four grammars ship with `prismjs` — verified: `prism-docker.js`, `prism-nasm.js`, `prism-systemd.js`, `prism-yaml.js` exist in `node_modules/prismjs/components/`.

- [ ] **Step 4: Create the component stylesheet**

Create `src/css/linux-components.css`:

```css
/* Components used by docs/linux/. Kept out of custom.css, which is already
   ~2100 lines. Every class here is namespaced kb-* to match the existing
   kb-figure / kb-recall conventions. */

/* --- <Src> ------------------------------------------------------------- */
.kb-src {
  text-decoration: none;
  border-bottom: 1px dotted var(--ifm-color-emphasis-500);
}
.kb-src:hover {
  border-bottom-style: solid;
}

/* --- <PrereqBlock> ----------------------------------------------------- */
.kb-prereq {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem;
  margin: 1rem 0;
  padding: 0.65rem 0.85rem;
  border-radius: 8px;
  background: var(--ifm-color-emphasis-100);
  font-size: 0.9rem;
}
.kb-prereq__label {
  flex: 0 0 auto;
  font-weight: 600;
  color: var(--ifm-color-emphasis-700);
}
.kb-prereq__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.55rem;
  border: 1px solid var(--ifm-color-emphasis-300);
  border-radius: 999px;
  background: var(--ifm-background-color);
  text-decoration: none;
}
.kb-prereq__chip:hover {
  border-color: var(--ifm-color-primary);
  text-decoration: none;
}
.kb-prereq__badge {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ifm-color-emphasis-600);
}

/* --- <KernelFacts> ----------------------------------------------------- */
.kb-kernel-facts {
  margin: 2rem 0 0;
  border: 1px solid var(--ifm-color-emphasis-300);
  border-radius: 10px;
  overflow: hidden;
}
.kb-kernel-facts__row {
  display: grid;
  grid-template-columns: 8.5rem 1fr;
  gap: 0.75rem;
  padding: 0.6rem 0.9rem;
  border-top: 1px solid var(--ifm-color-emphasis-200);
}
.kb-kernel-facts__row:first-child {
  border-top: 0;
}
.kb-kernel-facts__label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ifm-color-emphasis-600);
}
.kb-kernel-facts__structure {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.kb-kernel-facts__header {
  color: var(--ifm-color-emphasis-700);
}
@media (max-width: 576px) {
  .kb-kernel-facts__row {
    grid-template-columns: 1fr;
    gap: 0.2rem;
  }
}

/* --- <Lab> ------------------------------------------------------------- */
.kb-lab {
  margin: 1.5rem 0;
  border: 1px solid var(--ifm-color-success-dark);
  border-radius: 10px;
  overflow: hidden;
}
.kb-lab__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.9rem;
  background: var(--ifm-color-success-contrast-background);
}
.kb-lab__title {
  font-weight: 700;
}
.kb-lab__host,
.kb-lab__time {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--ifm-color-emphasis-200);
  color: var(--ifm-color-emphasis-800);
}
.kb-lab__host--qemu,
.kb-lab__host--qemu-gdb {
  background: var(--ifm-color-info-contrast-background);
}
.kb-lab__host--root-required {
  background: var(--ifm-color-warning-contrast-background);
}
.kb-lab__body {
  padding: 0.4rem 0.9rem 0.6rem;
}

/* --- <Video> ----------------------------------------------------------- */
.kb-video {
  margin: 1.5rem 0;
}
.kb-video__frame {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  border-radius: 10px;
  overflow: hidden;
  background: var(--ifm-color-emphasis-200);
}
.kb-video__frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.kb-video__caption,
.kb-cast__caption {
  margin-top: 0.5rem;
  font-size: 0.88rem;
  color: var(--ifm-color-emphasis-700);
}

/* --- <Cast> ------------------------------------------------------------ */
.kb-cast {
  margin: 1.5rem 0;
}
.kb-cast__player {
  border-radius: 10px;
  overflow: hidden;
}

/* --- <KnowledgeGraph> -------------------------------------------------- */
.kb-graph__legend {
  margin-top: 1rem;
  columns: 2;
  column-gap: 2rem;
  font-size: 0.9rem;
}
@media (max-width: 768px) {
  .kb-graph__legend {
    columns: 1;
  }
}
```

- [ ] **Step 5: Register the stylesheet**

In `docusaurus.config.js`, change line 93 from a string to an array:

```js
          customCss: ["./src/css/custom.css", "./src/css/linux-components.css"],
```

- [ ] **Step 6: Create the section landing page**

Create `docs/linux/readme.md`:

```md
---
title: Linux & Kernel
sidebar_label: Overview
sidebar_position: 0
tags: [linux, kernel]
prerequisites: []
---

# Linux & Kernel

How Linux actually works, from the boundary between a command you type and the kernel that
services it, down to page-table walks, RCU grace periods, and the path a packet takes through the
network stack. The aim is understanding you can reason from — not commands you have memorised.

:::info[This section is being written]
Folders and pages exist as stubs so the structure and its dependency graph are navigable from the
start.
:::

## The pinned kernel

Every source reference in this section points at **Linux v6.18** — released 2025-11-30, a longterm
release with projected end-of-life in December 2028. Citations name a file and a symbol
(`fs/namei.c:path_openat()`) and never a line number, because line numbers rot within a single
release while paths and symbol names survive for years.

Where behaviour changed recently enough that older material is now wrong — the fair scheduler, the
folio conversion, `io_uring` — the page says so explicitly.

## The lab

Nearly every hands-on exercise runs against a kernel you build yourself, booted under QEMU. A
kernel panic there costs you nothing and you can attach a debugger to the virtual CPU itself.
```

This page deliberately carries **no links into the section yet**. `onBrokenLinks: "throw"` would
reject them, because the pages they point at do not exist until Task 5 — which is precisely the
problem the spec's Rule 1 exists to solve. Task 5 scaffolds the tree and then adds the links here.

- [ ] **Step 7: Verify**

Run:

```bash
npm run lint && npm run build
```

Expected: PASS. The sidebar now exists with a single page, and the navbar item opens it.

- [ ] **Step 8: Commit**

```bash
git add sidebars.js docusaurus.config.js src/css/linux-components.css docs/linux/readme.md
git commit -m "feat: wire the Linux section sidebar, navbar, prism languages, and landing page"
```

---

## Task 5: Scaffold folders 00–04

Implements the spec's Rule 1. A manifest holds the page tree; a generator turns it into stubs. The generator is worth writing rather than hand-creating 49 files because Phases 2–5 re-run it four more times.

**Files:**
- Create: `tools/linux-docs-manifest.json`
- Create: `tools/scaffold-linux-docs.mjs`
- Generates: 46 stubs + 5 `_category_.json` under `docs/linux/`, and 3 stubs under `docs/computer-science/`
- Modify: `package.json` (script)

**Interfaces:**
- Consumes: nothing at runtime; the generated files are consumed by `buildGraph` from Task 2.
- Produces: `node tools/scaffold-linux-docs.mjs [--force]`. Without `--force` an existing `.md` is left untouched, so re-running during Phase 1b never destroys written prose. `_category_.json` files are always rewritten from the manifest.

- [ ] **Step 1: Write the generator**

Create `tools/scaffold-linux-docs.mjs`:

```js
#!/usr/bin/env node
// Creates the docs/linux/ page tree from tools/linux-docs-manifest.json.
//
//   node tools/scaffold-linux-docs.mjs           # create anything missing
//   node tools/scaffold-linux-docs.mjs --force   # also overwrite existing pages
//
// Implements Rule 1 of the section spec: every page in a phase exists as a
// one-sentence stub before any page is written properly, so that links and
// prerequisite ids resolve from the phase's first commit.
//
// Existing .md files are never touched without --force. Re-running this after
// pages have been written is safe and is how later phases extend the tree.
import { mkdirSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const MANIFEST = "tools/linux-docs-manifest.json";
const force = process.argv.includes("--force");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));

let created = 0;
let skipped = 0;
let categories = 0;

function yamlList(key, values) {
  if (!values || values.length === 0) return `${key}: []`;
  return [`${key}:`, ...values.map((v) => `  - ${v}`)].join("\n");
}

function stub(page, folder) {
  const front = [
    "---",
    `id: ${page.id}`,
    `title: ${page.title}`,
    `sidebar_label: ${page.sidebar_label}`,
    `sidebar_position: ${page.sidebar_position}`,
    `tags: [${page.tags.join(", ")}]`,
    yamlList("prerequisites", page.prerequisites),
    ...(page.related?.length ? [yamlList("related", page.related)] : []),
    "draft: false",
    "---",
    "",
    `# ${page.title}`,
    "",
    page.summary,
    "",
    ":::info[Not yet written]",
    `This page is a stub. See [the roadmap](${folder.roadmapLink}) for what lands when.`,
    ":::",
    "",
  ];
  return front.join("\n");
}

function writeIfAbsent(path, contents) {
  mkdirSync(dirname(path), { recursive: true });
  if (existsSync(path) && !force) {
    skipped += 1;
    return;
  }
  writeFileSync(path, contents);
  created += 1;
}

for (const folder of manifest.folders) {
  const dir = join(manifest.root, folder.dir);
  mkdirSync(dir, { recursive: true });

  writeFileSync(
    join(dir, "_category_.json"),
    `${JSON.stringify(
      {
        label: folder.label,
        position: folder.position,
        link: { type: "generated-index", description: folder.description },
      },
      null,
      2,
    )}\n`,
  );
  categories += 1;

  for (const page of folder.pages) {
    writeIfAbsent(join(dir, page.file), stub(page, folder));
  }
}

// Prerequisite pages that live outside docs/linux/. Same stub shape, minus the
// prerequisites key, which only in-scope pages are required to carry.
for (const page of manifest.external ?? []) {
  const body = [
    "---",
    `id: ${page.id}`,
    `title: ${page.title}`,
    `sidebar_label: ${page.sidebar_label}`,
    `sidebar_position: ${page.sidebar_position}`,
    `tags: [${page.tags.join(", ")}]`,
    "draft: false",
    "---",
    "",
    `# ${page.title}`,
    "",
    page.summary,
    "",
    ":::info[Not yet written]",
    "This page is a stub, created as a prerequisite for the Linux & Kernel section.",
    ":::",
    "",
  ].join("\n");
  writeIfAbsent(page.path, body);
}

console.log(
  `scaffold: ${created} file(s) created, ${skipped} left alone, ${categories} category file(s) written`,
);
```

- [ ] **Step 2: Write the manifest**

Create `tools/linux-docs-manifest.json`. `roadmapLink` is the relative path from that folder's pages back to the roadmap; `sidebar_position` is the page's order within its folder.

```json
{
  "root": "docs/linux",
  "folders": [
    {
      "dir": "00-overview",
      "label": "Overview",
      "position": 1,
      "description": "What this section covers, the kernel/user-space boundary, the hardware Linux assumes, and the roadmap through everything else.",
      "roadmapLink": "./roadmap.md",
      "pages": [
        { "file": "what-this-section-covers.md", "id": "what-this-section-covers", "title": "What This Section Covers", "sidebar_label": "What this covers", "sidebar_position": 1, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "The scope of this section, what it deliberately leaves out, and what \"understanding Linux\" means in practice." },
        { "file": "the-kernel-userspace-boundary.md", "id": "the-kernel-userspace-boundary", "title": "The Kernel/User-Space Boundary", "sidebar_label": "The boundary", "sidebar_position": 2, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Two worlds separated by one hardware-enforced door, and why every mechanism in this section is shaped by that door." },
        { "file": "what-linux-actually-is.md", "id": "what-linux-actually-is", "title": "What Linux Actually Is", "sidebar_label": "What Linux is", "sidebar_position": 3, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Kernel, GNU, and distribution pulled apart, plus the two design commitments that still constrain everything: a stable user-space ABI and no stable module ABI." },
        { "file": "hardware-the-kernel-assumes.md", "id": "hardware-the-kernel-assumes", "title": "The Hardware the Kernel Assumes", "sidebar_label": "Hardware assumed", "sidebar_position": 4, "tags": ["linux", "kernel"], "prerequisites": [], "related": ["computer-science/cpu-architecture/privilege-levels-and-protection", "computer-science/cpu-architecture/exceptions-traps-and-interrupts"], "summary": "The seven hardware capabilities every Linux mechanism rests on, each linked to the Computer Science page that owns it." },
        { "file": "distributions-and-what-differs.md", "id": "distributions-and-what-differs", "title": "Distributions and What Actually Differs", "sidebar_label": "Distributions", "sidebar_position": 5, "tags": ["linux"], "prerequisites": ["linux/00-overview/what-linux-actually-is"], "summary": "Same kernel, different packaging: what genuinely varies between distributions and the much longer list of things that do not." },
        { "file": "how-to-use-this-section.md", "id": "how-to-use-this-section", "title": "How to Use This Section", "sidebar_label": "How to use this", "sidebar_position": 6, "tags": ["linux"], "prerequisites": [], "summary": "The folder ladder and why it is ordered that way, how the prerequisite blocks work, how labs are marked by host, and what each row of the closing facts card means." },
        { "file": "roadmap.md", "id": "roadmap", "title": "Roadmap and Knowledge Graph", "sidebar_label": "Roadmap", "sidebar_position": 7, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "The dependency graph across the whole section, plus six named learning paths through it." },
        { "file": "glossary.md", "id": "glossary", "title": "Glossary", "sidebar_label": "Glossary", "sidebar_position": 8, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Every term this section uses as though you already know it, defined in a paragraph and linked to the page that owns it." },
        { "file": "misconceptions-index.md", "id": "misconceptions-index", "title": "Index of Misconceptions", "sidebar_label": "Misconceptions", "sidebar_position": 9, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Every widely-held wrong belief this section corrects, gathered in one place and linked to the correction." }
      ]
    },
    {
      "dir": "01-lab-and-toolchain",
      "label": "Setting Up a Lab",
      "position": 2,
      "description": "Build a kernel, boot it under QEMU, and attach a debugger — the machine every hands-on exercise in this section assumes.",
      "roadmapLink": "../00-overview/roadmap.md",
      "pages": [
        { "file": "the-lab-machine.md", "id": "the-lab-machine", "title": "The Lab Machine", "sidebar_label": "The lab machine", "sidebar_position": 1, "tags": ["linux", "kernel", "lab"], "prerequisites": [], "summary": "Why QEMU is the spine of every lab here, what to install on the host, and what each lab host badge means." },
        { "file": "getting-and-navigating-the-source.md", "id": "getting-and-navigating-the-source", "title": "Getting the Source", "sidebar_label": "Getting the source", "sidebar_position": 2, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/the-lab-machine"], "summary": "Cloning or downloading the pinned kernel, what the repository costs in disk and time, and a first orientation pass through the tree." },
        { "file": "building-a-kernel.md", "id": "building-a-kernel", "title": "Building a Kernel", "sidebar_label": "Building a kernel", "sidebar_position": 3, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/getting-and-navigating-the-source"], "summary": "From defconfig to a bootable image, including the debug options that make the rest of this section's labs possible." },
        { "file": "a-minimal-rootfs.md", "id": "a-minimal-rootfs", "title": "A Minimal Root Filesystem", "sidebar_label": "A minimal rootfs", "sidebar_position": 4, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/building-a-kernel"], "summary": "A static BusyBox, a directory skeleton, and an /init packed into an initramfs — early user space made concrete instead of magical." },
        { "file": "booting-your-kernel-in-qemu.md", "id": "booting-your-kernel-in-qemu", "title": "Booting Your Kernel in QEMU", "sidebar_label": "Booting in QEMU", "sidebar_position": 5, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/a-minimal-rootfs"], "summary": "The canonical QEMU invocation every later lab reuses, explained flag by flag." },
        { "file": "debugging-the-kernel-with-gdb.md", "id": "debugging-the-kernel-with-gdb", "title": "Debugging the Kernel with GDB", "sidebar_label": "GDB on the kernel", "sidebar_position": 6, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/booting-your-kernel-in-qemu"], "summary": "Attaching a debugger to the virtual CPU, loading vmlinux symbols, and walking live kernel structures — the highest-leverage skill in this section." },
        { "file": "a-full-system-vm-and-wsl2.md", "id": "a-full-system-vm-and-wsl2", "title": "A Full-System VM, and What WSL2 Can Do", "sidebar_label": "Full VM and WSL2", "sidebar_position": 7, "tags": ["linux", "kernel", "lab"], "prerequisites": ["linux/01-lab-and-toolchain/booting-your-kernel-in-qemu"], "summary": "A Debian VM for the labs that need systemd and real block devices, then an honest account of which labs WSL2 can and cannot run." }
      ]
    },
    {
      "dir": "02-guided-traces",
      "label": "Guided Traces",
      "position": 3,
      "description": "Six familiar things followed all the way down — a command, a write, a fault, a packet, a boot, a container — as narrative maps into the rest of the section.",
      "roadmapLink": "../00-overview/roadmap.md",
      "pages": [
        { "file": "what-happens-when-you-type-ls.md", "id": "what-happens-when-you-type-ls", "title": "What Happens When You Type `ls`", "sidebar_label": "Typing ls", "sidebar_position": 1, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Twenty mechanisms, named and linked, between a keystroke and a directory listing on your screen." },
        { "file": "the-life-of-a-write.md", "id": "the-life-of-a-write", "title": "The Life of a `write()`", "sidebar_label": "Life of a write", "sidebar_position": 2, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Where your data actually is at each moment between write() returning and the bytes reaching the device, and what fsync changes." },
        { "file": "the-life-of-a-page-fault.md", "id": "the-life-of-a-page-fault", "title": "The Life of a Page Fault", "sidebar_label": "Life of a fault", "sidebar_position": 3, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "An ordinary first touch of freshly allocated memory, traced from the CPU exception to the instruction re-executing — the normal case, not an error." },
        { "file": "the-life-of-a-packet.md", "id": "the-life-of-a-packet", "title": "The Life of a Packet", "sidebar_label": "Life of a packet", "sidebar_position": 4, "tags": ["linux", "kernel"], "prerequisites": [], "summary": "Wire to socket and back again, through the DMA ring, NAPI, GRO, netfilter, routing, and TCP." },
        { "file": "from-power-on-to-login-prompt.md", "id": "from-power-on-to-login-prompt", "title": "From Power-On to Login Prompt", "sidebar_label": "Power-on to login", "sidebar_position": 5, "tags": ["linux", "kernel", "boot"], "prerequisites": [], "summary": "Every handoff between pressing the power button and a login prompt, with the artefact each stage passes to the next." },
        { "file": "the-life-of-a-container.md", "id": "the-life-of-a-container", "title": "The Life of a Container", "sidebar_label": "Life of a container", "sidebar_position": 6, "tags": ["linux", "kernel", "containers"], "prerequisites": [], "summary": "docker run de-mystified: a container is a process started with unusual arguments, and here is every one of them." }
      ]
    },
    {
      "dir": "03-boot-and-init",
      "label": "Boot and Init",
      "position": 4,
      "description": "The full chain from firmware to a login prompt: UEFI, boot loaders, the kernel image, early setup, initramfs, PID 1, and systemd's dependency graph.",
      "roadmapLink": "../00-overview/roadmap.md",
      "pages": [
        { "file": "firmware-bios-and-uefi.md", "id": "firmware-bios-and-uefi", "title": "Firmware: BIOS and UEFI", "sidebar_label": "BIOS and UEFI", "sidebar_position": 1, "tags": ["linux", "boot"], "prerequisites": ["linux/02-guided-traces/from-power-on-to-login-prompt"], "summary": "What the firmware does before anything Linux exists, and why UEFI made boot loaders simpler and boot debugging harder." },
        { "file": "the-boot-chain.md", "id": "the-boot-chain", "title": "The Boot Chain", "sidebar_label": "The boot chain", "sidebar_position": 2, "tags": ["linux", "boot"], "prerequisites": ["linux/03-boot-and-init/firmware-bios-and-uefi"], "summary": "The whole handoff sequence in one diagram, with the exact artefact passed at each step and where each one lives on disk." },
        { "file": "bootloaders-grub-and-friends.md", "id": "bootloaders-grub-and-friends", "title": "Boot Loaders", "sidebar_label": "Boot loaders", "sidebar_position": 3, "tags": ["linux", "boot"], "prerequisites": ["linux/03-boot-and-init/the-boot-chain"], "summary": "GRUB 2, systemd-boot, and direct EFI stub boot — and the four things any boot loader must do." },
        { "file": "the-kernel-command-line.md", "id": "the-kernel-command-line", "title": "The Kernel Command Line", "sidebar_label": "Kernel command line", "sidebar_position": 4, "tags": ["linux", "boot"], "prerequisites": ["linux/03-boot-and-init/bootloaders-grub-and-friends"], "summary": "How parameters reach the kernel, how they are parsed, and the dozen worth knowing — the most useful boot debugging tool there is." },
        { "file": "secure-boot-and-signed-kernels.md", "id": "secure-boot-and-signed-kernels", "title": "Secure Boot and Signed Kernels", "sidebar_label": "Secure Boot", "sidebar_position": 5, "tags": ["linux", "boot", "security"], "prerequisites": ["linux/03-boot-and-init/bootloaders-grub-and-friends"], "summary": "The chain of trust from firmware keys to a signed kernel and signed modules, and what it does and does not protect against." },
        { "file": "the-kernel-image.md", "id": "the-kernel-image", "title": "Inside `bzImage`", "sidebar_label": "Inside bzImage", "sidebar_position": 6, "tags": ["linux", "kernel", "boot"], "prerequisites": ["linux/03-boot-and-init/the-boot-chain"], "summary": "The layout of a compressed kernel image, and why vmlinux, vmlinuz, and bzImage are three different things." },
        { "file": "early-boot-and-arch-setup.md", "id": "early-boot-and-arch-setup", "title": "Early Boot: Getting to C", "sidebar_label": "Early boot", "sidebar_position": 7, "tags": ["linux", "kernel", "boot"], "prerequisites": ["linux/03-boot-and-init/the-kernel-image"], "summary": "x86-64 from 16-bit entry through protected mode and early page tables into long mode, and the far simpler arm64 equivalent." },
        { "file": "start-kernel-and-initcalls.md", "id": "start-kernel-and-initcalls", "title": "`start_kernel` and the Initcall Order", "sidebar_label": "start_kernel", "sidebar_position": 8, "tags": ["linux", "kernel", "boot"], "prerequisites": ["linux/03-boot-and-init/early-boot-and-arch-setup"], "summary": "What the kernel brings up and in what order, and why driver initialisation order is a level rather than a list." },
        { "file": "initramfs-and-early-userspace.md", "id": "initramfs-and-early-userspace", "title": "initramfs and Early User Space", "sidebar_label": "initramfs", "sidebar_position": 9, "tags": ["linux", "kernel", "boot"], "prerequisites": ["linux/03-boot-and-init/start-kernel-and-initcalls"], "summary": "Why a root filesystem needs a root filesystem, and how the chicken-and-egg is broken." },
        { "file": "switch-root-and-pid-1.md", "id": "switch-root-and-pid-1", "title": "`switch_root` and PID 1", "sidebar_label": "switch_root and PID 1", "sidebar_position": 10, "tags": ["linux", "kernel", "boot"], "prerequisites": ["linux/03-boot-and-init/initramfs-and-early-userspace"], "summary": "Mounting the real root, the three constantly-confused ways to change it, and what makes PID 1 special." },
        { "file": "systemd-the-model.md", "id": "systemd-the-model", "title": "systemd: The Model", "sidebar_label": "systemd model", "sidebar_position": 11, "tags": ["linux", "boot"], "prerequisites": ["linux/03-boot-and-init/switch-root-and-pid-1"], "summary": "Units, the separation of dependency from ordering, targets instead of runlevels, and the transaction computed at every boot." },
        { "file": "systemd-in-practice-and-boot-debugging.md", "id": "systemd-in-practice-and-boot-debugging", "title": "systemd in Practice, and Debugging a Broken Boot", "sidebar_label": "systemd and boot debugging", "sidebar_position": 12, "tags": ["linux", "boot"], "prerequisites": ["linux/03-boot-and-init/systemd-the-model", "linux/03-boot-and-init/the-kernel-command-line"], "summary": "Socket activation, journald, and unit supervision, then the playbook for a machine that will not finish booting." }
      ]
    },
    {
      "dir": "04-kernel-architecture-and-idioms",
      "label": "Kernel Architecture and Idioms",
      "position": 5,
      "description": "The structure of the kernel and the C idioms it is written in — the prerequisite for reading any kernel source at all.",
      "roadmapLink": "../00-overview/roadmap.md",
      "pages": [
        { "file": "monolithic-with-modules.md", "id": "monolithic-with-modules", "title": "Monolithic, With Modules", "sidebar_label": "Monolithic with modules", "sidebar_position": 1, "tags": ["linux", "kernel"], "prerequisites": ["linux/00-overview/the-kernel-userspace-boundary"], "related": ["computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid"], "summary": "Where Linux sits in the architecture taxonomy, why, and the honest cost: a driver bug is a kernel bug." },
        { "file": "the-source-tree-map.md", "id": "the-source-tree-map", "title": "The Source Tree, Mapped", "sidebar_label": "The source tree", "sidebar_position": 2, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/monolithic-with-modules"], "summary": "Every top-level directory in a line, the four that matter expanded, and a lookup table from question to location." },
        { "file": "kconfig-and-kbuild.md", "id": "kconfig-and-kbuild", "title": "Kconfig and Kbuild", "sidebar_label": "Kconfig and Kbuild", "sidebar_position": 3, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/the-source-tree-map", "linux/01-lab-and-toolchain/building-a-kernel"], "summary": "How a configuration symbol becomes a compiled object, and how to read past the CONFIG_ ifdefs that are everywhere." },
        { "file": "modules-in-practice.md", "id": "modules-in-practice", "title": "Kernel Modules", "sidebar_label": "Modules", "sidebar_position": 4, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/kconfig-and-kbuild"], "summary": "Loading, unloading, parameters, dependency resolution, taint, and building a module out of tree." },
        { "file": "exported-symbols-and-the-module-abi.md", "id": "exported-symbols-and-the-module-abi", "title": "Exported Symbols and the Non-Stable ABI", "sidebar_label": "Exported symbols", "sidebar_position": 5, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/modules-in-practice"], "summary": "Why \"never break user space\" and \"break modules freely\" are a consistent pair of positions rather than hypocrisy." },
        { "file": "the-kernel-c-dialect.md", "id": "the-kernel-c-dialect", "title": "The Kernel Is Not C You Know", "sidebar_label": "The kernel C dialect", "sidebar_position": 6, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/the-source-tree-map"], "summary": "Freestanding C with no libc, no floating point, a tiny stack, GCC extensions in daily use, and the annotations sparse checks." },
        { "file": "kernel-data-structures.md", "id": "kernel-data-structures", "title": "Kernel Data Structures", "sidebar_label": "Data structures", "sidebar_position": 7, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/the-kernel-c-dialect"], "summary": "Intrusive lists, hlists, red-black trees, xarrays, and IDRs — why intrusive containers, and what they cost." },
        { "file": "container-of-and-embedded-structs.md", "id": "container-of-and-embedded-structs", "title": "`container_of` and Embedded Structs", "sidebar_label": "container_of", "sidebar_position": 8, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/kernel-data-structures"], "summary": "The central Linux idiom derived from scratch, after which kobjects, the VFS, and the device model all become readable at once." },
        { "file": "error-handling-idioms.md", "id": "error-handling-idioms", "title": "Error Handling", "sidebar_label": "Error handling", "sidebar_position": 9, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/the-kernel-c-dialect"], "summary": "Negative errno, the ERR_PTR pointer-range trick, and why goto-based unwinding is correct here rather than shameful." },
        { "file": "reference-counting-and-lifetime.md", "id": "reference-counting-and-lifetime", "title": "Reference Counting and Object Lifetime", "sidebar_label": "Reference counting", "sidebar_position": 10, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/error-handling-idioms"], "summary": "refcount_t, kref, get/put pairing, and the use-after-free class of bug the whole convention exists to prevent." },
        { "file": "kobjects-sysfs-and-the-object-model.md", "id": "kobjects-sysfs-and-the-object-model", "title": "kobjects, ksets, and sysfs", "sidebar_label": "kobjects and sysfs", "sidebar_position": 11, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/container-of-and-embedded-structs", "linux/04-kernel-architecture-and-idioms/reference-counting-and-lifetime"], "summary": "The kernel's object model, and how /sys is generated from it rather than written." },
        { "file": "memory-safety-in-kernel-c.md", "id": "memory-safety-in-kernel-c", "title": "What Goes Wrong in Kernel C", "sidebar_label": "What goes wrong", "sidebar_position": 12, "tags": ["linux", "kernel"], "prerequisites": ["linux/04-kernel-architecture-and-idioms/reference-counting-and-lifetime"], "summary": "The recurring bug classes as a catalogue, each with its symptom and the tool that catches it, plus where Rust-for-Linux stands." }
      ]
    }
  ],
  "external": [
    {
      "path": "docs/computer-science/cpu-architecture/privilege-levels-and-protection.md",
      "id": "privilege-levels-and-protection",
      "title": "Privilege Levels and Protection",
      "sidebar_label": "Privilege levels",
      "sidebar_position": 7,
      "tags": ["computer-science", "cpu-architecture", "protection"],
      "summary": "How a CPU enforces the difference between privileged and unprivileged code, and why that boundary cannot be forged in software."
    },
    {
      "path": "docs/computer-science/cpu-architecture/exceptions-traps-and-interrupts.md",
      "id": "exceptions-traps-and-interrupts",
      "title": "Exceptions, Traps, and Interrupts",
      "sidebar_label": "Exceptions and traps",
      "sidebar_position": 8,
      "tags": ["computer-science", "cpu-architecture", "interrupts"],
      "summary": "The taxonomy every operating system is built on: faults, traps, aborts, and asynchronous interrupts, and what \"precise\" means."
    },
    {
      "path": "docs/computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid.md",
      "id": "os-structure-monolithic-microkernel-hybrid",
      "title": "OS Structure: Monolithic, Microkernel, Hybrid",
      "sidebar_label": "OS structure",
      "sidebar_position": 7,
      "tags": ["computer-science", "operating-systems", "architecture"],
      "summary": "The architectural taxonomy operating systems are classified by, and the real trade-offs behind a debate that is usually argued badly."
    }
  ]
}
```

- [ ] **Step 3: Add the npm script**

In `package.json`, after `"test:graph"`:

```json
"scaffold:linux": "node tools/scaffold-linux-docs.mjs",
```

- [ ] **Step 4: Run the generator**

Run:

```bash
npm run scaffold:linux
```

Expected output: `scaffold: 49 file(s) created, 0 left alone, 5 category file(s) written`.

- [ ] **Step 5: Verify the file count**

Run:

```bash
find docs/linux -name "*.md" | wc -l
find docs/linux -name "_category_.json" | wc -l
```

Expected: `47` markdown files (46 stubs plus `readme.md`) and `5` category files.

- [ ] **Step 6: Add the section links to the landing page**

Now that the targets exist, append to `docs/linux/readme.md`, replacing the closing paragraph of
the "The lab" section:

```md
Nearly every hands-on exercise runs against a kernel you build yourself, booted under QEMU. A
kernel panic there costs you nothing and you can attach a debugger to the virtual CPU itself.
[Setting Up a Lab](./01-lab-and-toolchain/the-lab-machine.md) covers the whole setup, including
what WSL2 can and cannot do.

See [the roadmap](./00-overview/roadmap.md) for the dependency graph and the learning paths
through everything here.
```

- [ ] **Step 7: Verify the build is green**

Run:

```bash
npm run build
```

Expected: PASS. Both links in `readme.md` now resolve, and the graph validates: 46 in-scope pages, **34 prerequisite edges**, 3 related edges, and 3 external nodes.

- [ ] **Step 8: Verify the generator is non-destructive**

Run:

```bash
npm run scaffold:linux
```

Expected: `scaffold: 0 file(s) created, 49 left alone, 5 category file(s) written`. This is the guarantee that re-running it in Phase 2 cannot destroy written prose.

- [ ] **Step 9: Commit**

```bash
git add tools/linux-docs-manifest.json tools/scaffold-linux-docs.mjs package.json docs/linux docs/computer-science
git commit -m "feat: scaffold Linux section folders 00-04 and three CS prerequisite stubs"
```

---

## Task 6: `<PrereqBlock>` and theme injection

**Files:**
- Create: `src/components/PrereqBlock/index.jsx`
- Modify: `src/theme/DocItem/Layout/index.js`

**Interfaces:**
- Consumes: global data `{nodes, edges, related}` from Task 3; `.kb-prereq*` classes from Task 4.
- Produces: `<PrereqBlock variant="before" />` and `<PrereqBlock variant="after" />`. Both return `null` for any doc outside `docs/linux/`, so the theme change is safe for the whole site.

- [ ] **Step 1: Write the component**

Create `src/components/PrereqBlock/index.jsx`:

```jsx
import Link from "@docusaurus/Link";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { usePluginData } from "@docusaurus/useGlobalData";

// Renders the prerequisite / next / related rows for a docs/linux/ page,
// from the graph the knowledge-graph plugin publishes.
//
// Injected by src/theme/DocItem/Layout — pages carry no markup for this, and
// the "Next" row is computed from reverse edges so it can never fall out of
// date the way a hand-written "See also" list does.
//
// `variant="before"` renders above the article, `variant="after"` below it.

const SECTION_BADGES = {
  "computer-science": "CS",
  embedded: "Embedded",
  "gpu-computing": "GPU",
  programming: "Programming",
  "machine-learning": "ML",
  "game-development": "Game dev",
  "data-tools": "Data",
};

function Chip({ node }) {
  const badge = node.external ? SECTION_BADGES[node.id.split("/")[0]] : null;
  return (
    <Link className="kb-prereq__chip" to={node.permalink}>
      {badge && <span className="kb-prereq__badge">{badge}</span>}
      {node.label}
    </Link>
  );
}

function Row({ label, nodes }) {
  if (nodes.length === 0) return null;
  return (
    <nav className="kb-prereq" aria-label={label}>
      <span className="kb-prereq__label">{label}</span>
      {nodes.map((node) => (
        <Chip key={node.id} node={node} />
      ))}
    </nav>
  );
}

export default function PrereqBlock({ variant = "before" }) {
  const { metadata } = useDoc();
  const graph = usePluginData("knowledge-graph-plugin");

  if (!graph || !metadata.id.startsWith("linux/")) return null;

  const byId = new Map(graph.nodes.map((node) => [node.id, node]));
  const resolve = (ids) => ids.map((id) => byId.get(id)).filter(Boolean);
  const sortByLabel = (nodes) =>
    [...nodes].sort((a, b) => a.label.localeCompare(b.label));

  if (variant === "before") {
    const before = resolve(
      graph.edges.filter((e) => e.from === metadata.id).map((e) => e.to),
    );
    return <Row label="Before this" nodes={before} />;
  }

  // Reverse edges: everything that names this page as a prerequisite.
  const next = sortByLabel(
    resolve(graph.edges.filter((e) => e.to === metadata.id).map((e) => e.from)),
  );
  const related = sortByLabel(
    resolve([
      ...graph.related.filter((e) => e.from === metadata.id).map((e) => e.to),
      ...graph.related.filter((e) => e.to === metadata.id).map((e) => e.from),
    ]),
  );

  return (
    <>
      <Row label="Next" nodes={next} />
      <Row label="Related" nodes={related} />
    </>
  );
}
```

- [ ] **Step 2: Inject it into the theme**

In `src/theme/DocItem/Layout/index.js`:

Add the import with the other `@components` import at the top:

```js
import PrereqBlock from "@components/PrereqBlock";
```

Then in the returned JSX, change the `<DocVersionBadge />` / TOC / content block from:

```jsx
            <DocVersionBadge />
            {docTOC.mobile}
            <DocItemContent>{children}</DocItemContent>
```

to:

```jsx
            <DocVersionBadge />
            {docTOC.mobile}
            <PrereqBlock variant="before" />
            <DocItemContent>{children}</DocItemContent>
            <PrereqBlock variant="after" />
```

- [ ] **Step 3: Verify in the dev server**

Run:

```bash
npm run start
```

Then open `http://localhost:3000/knowledge-base/docs/linux/04-kernel-architecture-and-idioms/container-of-and-embedded-structs` and check:

- A **Before this** row appears above the body with one chip: "Data structures".
- A **Next** row appears below the body with one chip: "kobjects and sysfs".
- Open `.../linux/00-overview/hardware-the-kernel-assumes` — a **Related** row shows two chips, each prefixed with a small `CS` badge.
- Open any page outside the section, e.g. `.../docs/computer-science/operating-systems/scheduling` — no rows appear at all.

- [ ] **Step 4: Verify the production build**

Run:

```bash
npm run lint && npm run build
```

Expected: lint clean, build succeeds.

- [ ] **Step 5: Commit**

```bash
git add src/components/PrereqBlock/index.jsx src/theme/DocItem/Layout/index.js
git commit -m "feat: render prerequisite and next-topic links from the knowledge graph"
```

---

## Task 7: `<KernelFacts>`

**Files:**
- Create: `src/components/KernelFacts/index.jsx`
- Modify: `src/theme/MDXComponents.js`
- Modify: `docs/linux/00-overview/how-to-use-this-section.md`

**Interfaces:**
- Consumes: `formatRecallText` from `@lib/recallFormat` (already used by `src/components/Recall.jsx`); `.kb-kernel-facts*` classes from Task 4.
- Produces: `<KernelFacts structure={[[name, header], ...]} path="…" observe="…" trap="…" />`.

- [ ] **Step 1: Write the component**

Create `src/components/KernelFacts/index.jsx`:

```jsx
import { formatRecallText } from "@lib/recallFormat";

// <KernelFacts /> — the fixed card that ends every docs/linux/ topic page.
//
// Four rows, always the same four, always in this order, so a returning reader
// finds what they need by position rather than by reading: the structure that
// matters, the code path, the command that shows it on a live system, and the
// one belief most people hold that is wrong.
//
// Props are plain strings, not markdown, so backtick spans are rendered here
// the same way <Recall /> does it.
//
// Usage in markdown:
//   <KernelFacts
//     structure={[["struct vm_area_struct", "include/linux/mm_types.h"]]}
//     path="do_page_fault() → handle_mm_fault() → handle_pte_fault()"
//     observe="perf trace -e 'exceptions:page_fault_user' -p $(pgrep -n bash)"
//     trap="A major fault is not a worse fault. It is a fault that needed I/O." />
function Formatted({ text, className }) {
  return (
    <span
      className={className}
      // biome-ignore lint/security/noDangerouslySetInnerHtml: trusted doc content, rendered at build time
      dangerouslySetInnerHTML={{ __html: formatRecallText(text) }}
    />
  );
}

export default function KernelFacts({ structure = [], path, observe, trap }) {
  return (
    <aside className="kb-kernel-facts">
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Structure</span>
        <div className="kb-kernel-facts__structure">
          {structure.map(([name, header]) => (
            <div key={name}>
              <Formatted text={`\`${name}\``} />
              {header && (
                <Formatted
                  className="kb-kernel-facts__header"
                  text={` — \`${header}\``}
                />
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Path</span>
        <Formatted text={path} />
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Observe</span>
        <Formatted text={`\`${observe}\``} />
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Trap</span>
        <Formatted text={trap} />
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Register it**

In `src/theme/MDXComponents.js`, add the import and the entry:

```js
import KernelFacts from "@site/src/components/KernelFacts";
```

and `KernelFacts,` in the exported object.

- [ ] **Step 3: Add a live example to the conventions page**

Replace the body of `docs/linux/00-overview/how-to-use-this-section.md` below its front matter with:

```md
# How to Use This Section

Every convention this section uses, with a live example of each. The prose explaining the folder
ladder and the learning paths lands with the rest of folder 00; what follows is the component
gallery, which exists from the first day so that the conventions are visible while the section is
being written.

## Every page ends with a facts card

Four fixed rows, always in this order. The structure that matters and where it is defined, the code
path in a few hops, the command that shows the mechanism on a live system, and the single most
common wrong belief about the topic.

<KernelFacts
  structure={[["struct vm_area_struct", "include/linux/mm_types.h"]]}
  path="do_page_fault() → handle_mm_fault() → handle_pte_fault() → do_anonymous_page()"
  observe="perf trace -e 'exceptions:page_fault_user' -p $(pgrep -n bash)"
  trap="A major fault is not a fault that is worse. It is a fault that needed I/O. Most faults your process takes are minor, and minor faults are how ordinary memory allocation works." />

## Source references are pinned

Every reference into the kernel source names a file and a symbol and never a line number, because
line numbers rot within one release. Path resolution happens in
<Src file="fs/namei.c" symbol="path_openat" />, the allocator lives in
<Src file="mm/page_alloc.c" />, and <Src symbol="handle_mm_fault" /> is where a fault is resolved.
```

- [ ] **Step 4: Verify**

Run:

```bash
npm run lint && npm run build && npm run serve
```

Open `http://localhost:3000/knowledge-base/docs/linux/00-overview/how-to-use-this-section` and confirm the four-row card renders with the labels in the left column, that backticked spans render as inline code, and that all three `<Src>` links open the correct Elixir pages for v6.18.

- [ ] **Step 5: Commit**

```bash
git add src/components/KernelFacts/index.jsx src/theme/MDXComponents.js docs/linux/00-overview/how-to-use-this-section.md
git commit -m "feat: add <KernelFacts> closing card and a component gallery page"
```

---

## Task 8: `<Lab>` and `<Video>`

**Files:**
- Create: `src/components/Lab/index.jsx`
- Create: `src/components/Video/index.jsx`
- Modify: `src/theme/MDXComponents.js`
- Modify: `docs/linux/00-overview/how-to-use-this-section.md`

**Interfaces:**
- Consumes: `.kb-lab*` and `.kb-video*` classes from Task 4.
- Produces: `<Lab host="qemu" title="…" time="…">…</Lab>` and `<Video src="…" title="…" caption="…" />`.

- [ ] **Step 1: Write `<Lab>`**

Create `src/components/Lab/index.jsx`:

```jsx
// <Lab /> — a hands-on block with a required host badge.
//
// The badge is required and is the point: a reader must never start a lab and
// discover four steps in that their environment cannot run it. Children are
// ordinary markdown — numbered steps, expected output, and a closing "if it
// fails" line.
//
// Usage in markdown:
//   <Lab host="qemu" title="Watch a page fault happen" time="10 min">
//   1. ...
//   </Lab>

const HOSTS = {
  qemu: "QEMU lab",
  "qemu-gdb": "QEMU + GDB",
  "any-linux": "Any Linux",
  "wsl2-ok": "WSL2 OK",
  "root-required": "Root required",
};

export default function Lab({ host, title, time, children }) {
  if (!HOSTS[host]) {
    throw new Error(
      `<Lab host="${host}"> is not a known host. Use one of: ${Object.keys(HOSTS).join(", ")}`,
    );
  }
  return (
    <section className="kb-lab">
      <header className="kb-lab__head">
        <span className={`kb-lab__host kb-lab__host--${host}`}>
          {HOSTS[host]}
        </span>
        <span className="kb-lab__title">{title}</span>
        {time && <span className="kb-lab__time">{time}</span>}
      </header>
      <div className="kb-lab__body">{children}</div>
    </section>
  );
}
```

The throw is deliberate: a typo'd host renders at build time and so fails the build rather than shipping a lab with no badge.

- [ ] **Step 2: Write `<Video>`**

Create `src/components/Video/index.jsx`:

```jsx
// <Video /> — an embedded talk or explainer.
//
// The video stays where it lives; this repository only ever holds a URL. Use
// it where watching genuinely beats reading, and prefer a ## References entry
// for anything much over an hour.
//
// Usage in markdown:
//   <Video src="https://www.youtube.com/embed/<id>"
//          title="Paul McKenney — RCU: what is it, and how does it work?"
//          caption="Grace periods, from the person who wrote RCU." />
export default function Video({ src, title, caption }) {
  if (!title) {
    throw new Error("<Video> requires a `title` — it is the iframe's accessible name");
  }
  return (
    <figure className="kb-video">
      <div className="kb-video__frame">
        <iframe
          src={src}
          title={title}
          loading="lazy"
          allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
      {caption && <figcaption className="kb-video__caption">{caption}</figcaption>}
    </figure>
  );
}
```

- [ ] **Step 3: Register both**

In `src/theme/MDXComponents.js`, add:

```js
import Lab from "@site/src/components/Lab";
import Video from "@site/src/components/Video";
```

and `Lab,` and `Video,` in the exported object.

- [ ] **Step 4: Add live examples to the gallery**

Append to `docs/linux/00-overview/how-to-use-this-section.md`:

```md
## Labs state where they run

Every lab carries a host badge. `QEMU lab` needs the virtual machine from
[Setting Up a Lab](../01-lab-and-toolchain/the-lab-machine.md); `Any Linux` runs anywhere;
`WSL2 OK` is explicitly confirmed to work under WSL2. Every lab shows expected output, not just
commands.

<Lab host="qemu" title="Confirm your lab kernel is the pinned version" time="2 min">

1. Boot the lab VM and run:

   ```bash
   uname -r
   ```

2. Expected output — the version string starts with the pinned release:

   ```text
   6.18.0
   ```

**If it fails:** you booted the distribution's kernel rather than the one you built. Check the
`-kernel` argument in your QEMU invocation.

</Lab>

## Videos are linked, never stored

Where a talk develops an idea better than a page can, it is embedded. The video stays on its own
host; nothing is committed to this repository.
```

- [ ] **Step 5: Verify**

Run:

```bash
npm run lint && npm run build && npm run serve
```

Open the gallery page and confirm the lab block renders with a `QEMU lab` badge, the title, the `2 min` chip, and that the nested code fences inside it render as code blocks.

- [ ] **Step 6: Commit**

```bash
git add src/components/Lab/index.jsx src/components/Video/index.jsx src/theme/MDXComponents.js docs/linux/00-overview/how-to-use-this-section.md
git commit -m "feat: add <Lab> and <Video> components"
```

---

## Task 9: `<Cast>` and the asciinema player

**Files:**
- Create: `src/components/Cast/index.jsx`
- Create: `static/casts/linux/hello.cast`
- Modify: `package.json` (dependency)
- Modify: `src/theme/MDXComponents.js`
- Modify: `docs/linux/00-overview/how-to-use-this-section.md`

**Interfaces:**
- Consumes: `.kb-cast*` classes from Task 4.
- Produces: `<Cast src="/casts/linux/<name>.cast" caption="…" />`.

- [ ] **Step 1: Install the dependency**

Run:

```bash
npm install asciinema-player@^3.17.0
```

- [ ] **Step 2: Write the component**

Create `src/components/Cast/index.jsx`:

```jsx
import useBaseUrl from "@docusaurus/useBaseUrl";
import { useEffect, useRef } from "react";
import "asciinema-player/dist/bundle/asciinema-player.css";

// <Cast /> — a replayable terminal session.
//
// The player library touches `document` at import time, so it is imported
// dynamically inside an effect. Effects never run during server rendering,
// which makes this SSR-safe without a <BrowserOnly> wrapper — the wrapper
// would add a component boundary and change nothing about the guarantee.
// The stylesheet is a static import because CSS is safe to import at module
// scope and webpack extracts it at build time.
//
// Every cast on a page is accompanied by the decisive output as a plain text
// code block: casts are not indexed by the offline search, do not render
// without JavaScript, and cannot be copied from. The text block is the
// content; the cast shows the interaction.
//
// Usage in markdown:
//   <Cast src="/casts/linux/ftrace-function-graph.cast"
//         caption="Following a read() with the function-graph tracer" />
export default function Cast({ src, caption, poster = "npt:0:01" }) {
  const containerRef = useRef(null);
  const resolved = useBaseUrl(src);

  useEffect(() => {
    let player;
    let cancelled = false;

    (async () => {
      const AsciinemaPlayer = (await import("asciinema-player")).default;
      if (cancelled || !containerRef.current) return;
      player = AsciinemaPlayer.create(resolved, containerRef.current, {
        autoPlay: false,
        idleTimeLimit: 2,
        fit: "width",
        theme: "asciinema",
        poster,
      });
    })();

    return () => {
      cancelled = true;
      player?.dispose?.();
    };
  }, [resolved, poster]);

  return (
    <figure className="kb-cast">
      <div className="kb-cast__player" ref={containerRef} />
      {caption && <figcaption className="kb-cast__caption">{caption}</figcaption>}
    </figure>
  );
}
```

- [ ] **Step 3: Create a real cast file to test against**

Create `static/casts/linux/hello.cast`. This is asciicast v2 format: a JSON header line followed by one `[time, "o", "output"]` event per line.

```
{"version": 2, "width": 80, "height": 6, "timestamp": 1772236800, "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"}}
[0.5, "o", "$ "]
[1.0, "o", "uname -r\r\n"]
[1.2, "o", "6.18.0\r\n"]
[1.4, "o", "$ "]
[2.2, "o", "exit\r\n"]
```

This placeholder exists only to prove the player renders. Real casts are recorded from the QEMU lab in Phase 1b and later phases.

- [ ] **Step 4: Register it**

In `src/theme/MDXComponents.js`, add:

```js
import Cast from "@site/src/components/Cast";
```

and `Cast,` in the exported object.

- [ ] **Step 5: Add a live example to the gallery**

Append to `docs/linux/00-overview/how-to-use-this-section.md`:

```md
## Terminal sessions are replayable

Tool pages carry recorded sessions you can scrub through. They are text, not video — a few
kilobytes each — and the decisive output always appears as a code block too, because the player
does not render without JavaScript and the offline search cannot index it.

<Cast src="/casts/linux/hello.cast" caption="Checking the running kernel version in the lab VM" />

```text
$ uname -r
6.18.0
```
```

- [ ] **Step 6: Prove SSR safety in a production build**

This is the step that matters. A dev-server check is not sufficient, because dev-server rendering is client-side.

Run:

```bash
npm run build && npm run serve
```

Expected: the build completes with **no** `document is not defined` or `window is not defined` error. Open `http://localhost:3000/knowledge-base/docs/linux/00-overview/how-to-use-this-section` and confirm the player renders with a play control and that pressing play replays the session.

- [ ] **Step 7: Verify no hydration error**

With the production preview still running, open the browser console on that page and confirm there is no hydration mismatch warning.

- [ ] **Step 8: Commit**

```bash
git add package.json package-lock.json src/components/Cast/index.jsx static/casts/linux/hello.cast src/theme/MDXComponents.js docs/linux/00-overview/how-to-use-this-section.md
git commit -m "feat: add <Cast> asciinema player for terminal sessions"
```

---

## Task 10: `<KnowledgeGraph>` and the roadmap page

**Files:**
- Create: `src/components/KnowledgeGraph/index.jsx`
- Modify: `src/theme/MDXComponents.js`
- Modify: `docs/linux/00-overview/roadmap.md`

**Interfaces:**
- Consumes: global data from Task 3; `.kb-graph__legend` from Task 4; `@theme/Mermaid` from the already-installed `@docusaurus/theme-mermaid`.
- Produces: `<KnowledgeGraph />` (folder granularity) and `<KnowledgeGraph folder="04-kernel-architecture-and-idioms" />` (page granularity within one folder).

- [ ] **Step 1: Write the component**

Create `src/components/KnowledgeGraph/index.jsx`:

```jsx
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import Mermaid from "@theme/Mermaid";

// <KnowledgeGraph /> — the section's dependency graph, generated from the
// prerequisite front matter rather than drawn by hand.
//
// Folder granularity by default: ~20 nodes, readable. Pass `folder` for one
// folder's page-level subgraph. The full page-level graph is never rendered —
// 229 nodes is a hairball in any renderer.
//
// Mermaid cannot be relied on for click-through navigation here (Docusaurus
// sets mermaid's securityLevel, which can disable click directives), so the
// nodes are accompanied by a linked legend below the diagram.
// ponytail: legend instead of in-diagram links; switch to `click X href` if
// the site's mermaid securityLevel is ever confirmed to be "loose".

function mermaidId(value) {
  return `n${value.replace(/[^a-zA-Z0-9]/g, "_")}`;
}

function folderLabel(folder) {
  return folder.replace(/^\d+-/, "").replace(/-/g, " ");
}

export default function KnowledgeGraph({ folder }) {
  const graph = usePluginData("knowledge-graph-plugin");
  if (!graph || graph.nodes.length === 0) return null;

  const internal = graph.nodes.filter((node) => !node.external);

  if (folder) {
    const pages = internal.filter((node) => node.folder === folder);
    const ids = new Set(pages.map((node) => node.id));
    const lines = ["flowchart LR"];
    for (const page of pages) {
      lines.push(`  ${mermaidId(page.id)}["${page.label}"]`);
    }
    for (const edge of graph.edges) {
      if (ids.has(edge.from) && ids.has(edge.to)) {
        lines.push(`  ${mermaidId(edge.to)} --> ${mermaidId(edge.from)}`);
      }
    }
    return (
      <>
        <Mermaid value={lines.join("\n")} />
        <ul className="kb-graph__legend">
          {pages.map((page) => (
            <li key={page.id}>
              <Link to={page.permalink}>{page.label}</Link>
            </li>
          ))}
        </ul>
      </>
    );
  }

  // Folder granularity: aggregate page edges into folder edges.
  const folderOf = new Map(internal.map((node) => [node.id, node.folder]));
  const folders = [...new Set(internal.map((node) => node.folder))].sort();
  const folderEdges = new Set();
  for (const edge of graph.edges) {
    const from = folderOf.get(edge.from);
    const to = folderOf.get(edge.to);
    if (from && to && from !== to) folderEdges.add(`${to}|${from}`);
  }

  const lines = ["flowchart LR"];
  for (const name of folders) {
    lines.push(`  ${mermaidId(name)}["${folderLabel(name)}"]`);
  }
  for (const edge of folderEdges) {
    const [to, from] = edge.split("|");
    lines.push(`  ${mermaidId(to)} --> ${mermaidId(from)}`);
  }

  return (
    <>
      <Mermaid value={lines.join("\n")} />
      <ul className="kb-graph__legend">
        {folders.map((name) => {
          const first = internal
            .filter((node) => node.folder === name)
            .sort((a, b) => a.id.localeCompare(b.id))[0];
          return (
            <li key={name}>
              <Link to={first.permalink}>{folderLabel(name)}</Link>
            </li>
          );
        })}
      </ul>
    </>
  );
}
```

- [ ] **Step 2: Register it**

In `src/theme/MDXComponents.js`, add:

```js
import KnowledgeGraph from "@site/src/components/KnowledgeGraph";
```

and `KnowledgeGraph,` in the exported object.

- [ ] **Step 3: Fill in the roadmap page**

Replace the body of `docs/linux/00-overview/roadmap.md` below its front matter with:

```md
# Roadmap and Knowledge Graph

Every page in this section declares what you need to have read first. The graph below is generated
from those declarations rather than drawn by hand, so it cannot disagree with the pages themselves —
and a page that named a prerequisite which does not exist, or a set of pages that depended on each
other in a loop, would fail the site build.

## The section at folder granularity

<KnowledgeGraph />

## Inside one folder

Folder-level edges hide a lot. Here is the page-level graph for the kernel architecture folder,
which is the one every later folder depends on:

<KnowledgeGraph folder="04-kernel-architecture-and-idioms" />

## Learning paths

The six routes through this section. Each is an ordered list, and every page's prerequisites appear
earlier in its own path.

Paths are filled in as the folders they cross are written. Folders 00 through 04 exist now; the
rest of the section is scaffolded and being written.

### I just want to understand my machine

1. [The kernel/user-space boundary](./the-kernel-userspace-boundary.md)
2. [What Linux actually is](./what-linux-actually-is.md)
3. [What happens when you type `ls`](../02-guided-traces/what-happens-when-you-type-ls.md)
4. [The life of a `write()`](../02-guided-traces/the-life-of-a-write.md)
5. [From power-on to login prompt](../02-guided-traces/from-power-on-to-login-prompt.md)

### I want to read kernel source

1. [The hardware the kernel assumes](./hardware-the-kernel-assumes.md)
2. [Monolithic, with modules](../04-kernel-architecture-and-idioms/monolithic-with-modules.md)
3. [The source tree, mapped](../04-kernel-architecture-and-idioms/the-source-tree-map.md)
4. [The kernel is not C you know](../04-kernel-architecture-and-idioms/the-kernel-c-dialect.md)
5. [Kernel data structures](../04-kernel-architecture-and-idioms/kernel-data-structures.md)
6. [`container_of` and embedded structs](../04-kernel-architecture-and-idioms/container-of-and-embedded-structs.md)
```

- [ ] **Step 4: Verify**

Run:

```bash
npm run lint && npm run build && npm run serve
```

Open `http://localhost:3000/knowledge-base/docs/linux/00-overview/roadmap` and confirm:

- The folder graph renders five nodes (`overview`, `lab and toolchain`, `guided traces`, `boot and init`, `kernel architecture and idioms`) with edges between them.
- The folder-scoped graph renders twelve nodes for folder 04.
- Both legends list every node as a working link.

- [ ] **Step 5: Commit**

```bash
git add src/components/KnowledgeGraph/index.jsx src/theme/MDXComponents.js docs/linux/00-overview/roadmap.md
git commit -m "feat: generate the section knowledge graph from prerequisite front matter"
```

---

## Task 11: The authoring-convention checker

Enforces the spec's Rule 2 and gives Phase 1b a gate for the conventions the plugin cannot see. Modelled on the existing `tools/check-algo-docs.mjs`.

**Files:**
- Create: `tools/check-linux-docs.mjs`
- Modify: `package.json` (script)

**Interfaces:**
- Consumes: the scaffolded tree from Task 5.
- Produces: `node tools/check-linux-docs.mjs [--written]`. Exit code 1 on any finding. Without `--written`, stub pages are exempt from the content checks; with it, every page must be finished.

- [ ] **Step 1: Write the checker**

Create `tools/check-linux-docs.mjs`:

```js
#!/usr/bin/env node
// Authoring-convention gate for docs/linux/.
//
//   node tools/check-linux-docs.mjs             # structure only; stubs exempt
//   node tools/check-linux-docs.mjs --written   # every page must be finished
//
// The knowledge-graph plugin already fails the build on a bad prerequisite id
// or a cycle. This covers the conventions the plugin cannot see: category
// descriptions (Rule 2), required front matter, and — for finished pages —
// the closing facts card and the references section.
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const ROOT = "docs/linux";
const REQUIRED_KEYS = ["title", "sidebar_label", "sidebar_position", "tags", "prerequisites"];
const STUB_MARKER = ":::info[Not yet written]";
const requireWritten = process.argv.includes("--written");

// Navigational pages: they carry no topic of their own, so the closing facts
// card and the references section do not apply to them. Front-matter and
// category checks still do.
const NAVIGATIONAL = new Set([
  "docs/linux/readme.md",
  "docs/linux/00-overview/roadmap.md",
  "docs/linux/00-overview/glossary.md",
  "docs/linux/00-overview/misconceptions-index.md",
  "docs/linux/00-overview/how-to-use-this-section.md",
]);

const findings = [];
const note = (file, message) => findings.push(`${file}: ${message}`);

function markdownFiles(dir) {
  return readdirSync(dir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
    .map((entry) => join(entry.parentPath ?? entry.path, entry.name))
    .sort();
}

function frontmatter(text) {
  const match = text.match(/^---\n([\s\S]*?)\n---/);
  return match ? match[1] : null;
}

// Rule 2: every folder's category file carries a real description.
for (const entry of readdirSync(ROOT, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const path = join(ROOT, entry.name, "_category_.json");
  if (!existsSync(path)) {
    note(path, "missing — every folder needs a _category_.json");
    continue;
  }
  const category = JSON.parse(readFileSync(path, "utf8"));
  const description = category.link?.description;
  if (!description || description.trim().length < 20) {
    note(path, 'link.description is missing or too short — it is a required field, one real sentence');
  }
  if (typeof category.position !== "number") {
    note(path, "position must be a number");
  }
}

let stubs = 0;
let written = 0;

for (const file of markdownFiles(ROOT)) {
  const text = readFileSync(file, "utf8");
  const front = frontmatter(text);
  if (!front) {
    note(file, "no front matter");
    continue;
  }

  for (const key of REQUIRED_KEYS) {
    if (!new RegExp(`^${key}:`, "m").test(front)) {
      note(file, `front matter is missing "${key}"`);
    }
  }

  if (text.includes(STUB_MARKER)) {
    stubs += 1;
    if (requireWritten) {
      note(file, "still a stub, but --written was requested");
    }
    continue;
  }

  written += 1;
  if (NAVIGATIONAL.has(file.split("\\").join("/"))) continue;
  if (!text.includes("<KernelFacts")) {
    note(file, "a finished page must end with a <KernelFacts /> card");
  }
  if (!/^## References$/m.test(text)) {
    note(file, "a finished page must have a ## References section");
  }
}

if (findings.length > 0) {
  console.error(`check-linux-docs: ${findings.length} finding(s)\n`);
  for (const finding of findings) console.error(`  ${finding}`);
  process.exit(1);
}

console.log(`check-linux-docs: OK — ${written} written page(s), ${stubs} stub(s)`);
```

- [ ] **Step 2: Add the npm script**

In `package.json`, after `"check:algo"`:

```json
"check:linux": "node tools/check-linux-docs.mjs",
```

- [ ] **Step 3: Add a references section to the gallery page**

Not required by the checker — `how-to-use-this-section.md` is on the navigational list — but the
gallery should demonstrate the reference convention alongside the others. Append to
`docs/linux/00-overview/how-to-use-this-section.md`:

```md
## Pages end with annotated references

Two to six entries, each saying why you would click it. Never a bare URL.

- [Docusaurus admonitions](https://docusaurus.io/docs/markdown-features/admonitions) — the five
  callout types this section uses, and nothing beyond them.
- [asciinema player](https://docs.asciinema.org/manual/player/) — options and keyboard controls for
  the recorded terminal sessions above.
- [Bootlin Elixir cross-referencer](https://elixir.bootlin.com/linux/v6.18/source) — where every
  `<Src>` link in this section points, pinned to v6.18.
```

- [ ] **Step 4: Run the checker and verify it passes**

Run:

```bash
npm run check:linux
```

Expected: `check-linux-docs: OK — 3 written page(s), 44 stub(s)`, exit code 0.

The three written pages are `readme.md`, `roadmap.md`, and `how-to-use-this-section.md` — all three on the navigational list, so none is asked for a facts card or a references section. The other 44 pages still carry their stub marker.

- [ ] **Step 5: Verify the checker catches a missing category description**

Temporarily set `"description": ""` in `docs/linux/00-overview/_category_.json`, then run:

```bash
npm run check:linux
```

Expected: exit code 1, with `link.description is missing or too short`. Restore the description and confirm it passes again.

- [ ] **Step 6: Verify the checker catches an unfinished topic page**

Temporarily delete the `:::info[Not yet written]` block from `docs/linux/04-kernel-architecture-and-idioms/the-source-tree-map.md`, then run:

```bash
npm run check:linux
```

Expected: exit code 1, with both `must end with a <KernelFacts /> card` and `must have a ## References section` for that file. Restore the block and confirm it passes again.

This is the check that makes Phase 1b's per-page gate work: as soon as a page loses its stub marker, it must satisfy the full convention.

- [ ] **Step 7: Final full verification**

Run:

```bash
npm run lint && npm run typecheck && npm run test:kernel-source && npm run test:graph && npm run check:linux && npm run build
```

Expected: every command succeeds.

- [ ] **Step 8: Commit**

```bash
git status --short   # confirm the two temporarily-edited files are restored
git add tools/check-linux-docs.mjs package.json docs/linux/00-overview/how-to-use-this-section.md
git commit -m "feat: add authoring-convention checker for the Linux section"
```

---

## Phase 1a Definition of Done

- [ ] `npm run build` is green.
- [ ] `npm run lint`, `npm run typecheck`, `npm run test:kernel-source`, `npm run test:graph`, and `npm run check:linux` all pass.
- [ ] The **Linux & Kernel** item appears in the navbar's Systems dropdown and opens a sidebar with five folders and 47 pages.
- [ ] Every page under `docs/linux/` renders its generated **Before this** / **Next** / **Related** rows where it has them, and no page outside the section renders any.
- [ ] `roadmap.md` renders both a folder-level and a folder-scoped graph from front matter.
- [ ] The component gallery on `how-to-use-this-section.md` renders a working `<KernelFacts>`, `<Src>`, `<Lab>`, and `<Cast>`.
- [ ] The three plugin failure modes have each been observed failing a real build (unknown id and missing key in Task 3; cycle covered by unit test).
- [ ] `npm run check:linux` reports `3 written page(s), 44 stub(s)` and has been observed failing on both a blanked category description and an unfinished topic page.
- [ ] Re-running `npm run scaffold:linux` reports `0 file(s) created`.

## What Phase 1a deliberately does not do

Written into the plan so a reviewer does not read these as omissions:

- **No page prose.** All 46 pages are one-sentence stubs. Writing them, and the three CS backfill pages, is Phase 1b.
- **No real casts.** `hello.cast` is a placeholder proving the player works. Real recordings come from the QEMU lab during Phase 1b.
- **No figures.** `static/img/linux/` and its `SOURCES.md` are created in Phase 1b along with the Graphviz kernel diagram on `the-source-tree-map.md`.
- **No `<Video>` usage on a real page** — the component exists and is registered; the first genuine embed lands with the folder that needs it.
- **`<KnowledgeGraph>` click-through navigation** is a linked legend rather than in-diagram links, for the reason marked with a `ponytail:` comment in the component.
