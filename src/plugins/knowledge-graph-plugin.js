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
