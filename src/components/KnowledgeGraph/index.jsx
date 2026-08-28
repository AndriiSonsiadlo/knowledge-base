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

  // ponytail: the section's own docs/linux/readme.md is in-scope (it declares
  // prerequisites: []) but lives directly under docs/linux/ with no subfolder,
  // so buildGraph's folderOf() gives it folder: "". Left in, it renders as a
  // 6th, unlabeled folder node here. It isn't part of any reading-order
  // folder, so drop it — this is the only place `node.folder` is consumed.
  const internal = graph.nodes.filter((node) => !node.external && node.folder);

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
