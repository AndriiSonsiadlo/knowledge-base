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
