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
