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
// diagram is followed by a numbered trail — the graph's own reading order,
// made clickable. The number is not decoration: it's the traversal order the
// diagram above just drew left-to-right.
// ponytail: trail instead of in-diagram links; switch to `click X href` if
// the site's mermaid securityLevel is ever confirmed to be "loose".

function mermaidId(value) {
  return `n${value.replace(/[^a-zA-Z0-9]/g, "_")}`;
}

function folderLabel(folder) {
  return folder.replace(/^\d+-/, "").replace(/-/g, " ");
}

// Reading order within a folder: sidebar_position first, id as a tiebreak —
// not alphabetical by id, which has no relation to the intended reading order.
function byReadingOrder(a, b) {
  return a.sidebarPosition - b.sidebarPosition || a.id.localeCompare(b.id);
}

// Mermaid flowchart node labels are quoted strings; a literal `"` in the
// label would close the string early and break the diagram.
function escapeLabel(label) {
  return label.replaceAll('"', "&quot;");
}

// The trail below the diagram: same nodes, in the same left-to-right order,
// as a numbered, clickable sequence — the diagram's meaning made navigable.
function Trail({ items }) {
  return (
    <ol className="kb-graph__trail">
      {items.map((item, index) => (
        <li key={item.id} className="kb-graph__trail-item">
          <Link className="kb-graph__trail-link" to={item.permalink}>
            <span className="kb-graph__trail-index">{index + 1}</span>
            {item.label}
          </Link>
        </li>
      ))}
    </ol>
  );
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
    const pages = internal
      .filter((node) => node.folder === folder)
      .sort(byReadingOrder);
    const ids = new Set(pages.map((node) => node.id));
    const lines = ["flowchart LR"];
    for (const page of pages) {
      lines.push(`  ${mermaidId(page.id)}["${escapeLabel(page.label)}"]`);
    }
    for (const edge of graph.edges) {
      if (ids.has(edge.from) && ids.has(edge.to)) {
        lines.push(`  ${mermaidId(edge.to)} --> ${mermaidId(edge.from)}`);
      }
    }
    return (
      <>
        <Mermaid value={lines.join("\n")} />
        <Trail items={pages} />
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
    lines.push(`  ${mermaidId(name)}["${escapeLabel(folderLabel(name))}"]`);
  }
  for (const edge of folderEdges) {
    const [to, from] = edge.split("|");
    lines.push(`  ${mermaidId(to)} --> ${mermaidId(from)}`);
  }

  const folderItems = folders.map((name) => {
    const first = internal
      .filter((node) => node.folder === name)
      .sort(byReadingOrder)[0];
    return { id: name, label: folderLabel(name), permalink: first.permalink };
  });

  return (
    <>
      <Mermaid value={lines.join("\n")} />
      <Trail items={folderItems} />
    </>
  );
}
