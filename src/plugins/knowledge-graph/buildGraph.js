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
        if (path.includes(next)) {
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
