import lucideSubset from "@site/src/components/lucide-subset.json";

// <Diagram /> — a hand-composed box-and-arrow diagram, styled to replace Mermaid for
// architecture, layer, and flow pictures. Everything is real text laid out with CSS,
// so it stays sharp, searchable, theme-aware, and readable by screen readers.
//
// Usage in markdown (all parts are global MDX components, no import):
//   <Diagram title="What the agent can see">
//     <DiagramNode variant="pill" accent>Agent knowledge</DiagramNode>
//     <DiagramArrow label="unseen" icon="eye-off" />
//     <DiagramGroup label="Outside the repo">
//       <DiagramNode icon="file-text" title="Design doc">Lives in Drive.</DiagramNode>
//       <DiagramNode icon="brain" title="Tacit knowledge">Lives in heads.</DiagramNode>
//     </DiagramGroup>
//   </Diagram>
//
// Layout: <Diagram> stacks its children top to bottom. <DiagramGroup> (framed, dotted)
// and <DiagramRow> (unframed) place their children side by side and wrap on narrow
// screens. <DiagramArrow> points down by default; inside a row use direction="right".

function Glyph({ name }) {
  if (!name) return null;
  const data = lucideSubset.icons[name];
  if (!data) return null;
  return (
    <svg
      className="kb-dg__icon"
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${data.width ?? lucideSubset.width} ${data.height ?? lucideSubset.height}`}
      aria-hidden="true"
      // biome-ignore lint/security/noDangerouslySetInnerHtml: trusted, build-time icon data
      dangerouslySetInnerHTML={{ __html: data.body }}
    />
  );
}

export function Diagram({ title, caption, accent = "green", children }) {
  return (
    <figure className="kb-dg" data-accent={accent} aria-label={title}>
      <div className="kb-dg__canvas">
        {title && <div className="kb-dg__title">{title}</div>}
        <div className="kb-dg__stack">{children}</div>
      </div>
      {caption && <figcaption className="kb-dg__caption">{caption}</figcaption>}
    </figure>
  );
}

export function DiagramNode({
  title,
  icon,
  variant = "card",
  accent = false,
  dashed = false,
  children,
}) {
  const cls = [
    "kb-dg__node",
    `kb-dg__node--${variant}`,
    accent && "kb-dg__node--accent",
    dashed && "kb-dg__node--dashed",
  ]
    .filter(Boolean)
    .join(" ");
  if (variant === "pill") {
    return (
      <div className={cls}>
        <Glyph name={icon} />
        <span>{title ?? children}</span>
      </div>
    );
  }
  return (
    <div className={cls}>
      <Glyph name={icon} />
      <div className="kb-dg__node-text">
        {title && <div className="kb-dg__node-title">{title}</div>}
        {children && <div className="kb-dg__node-body">{children}</div>}
      </div>
    </div>
  );
}

export function DiagramGroup({ label, accent = false, children }) {
  return (
    <div className={`kb-dg__group${accent ? " kb-dg__group--accent" : ""}`}>
      {label && <div className="kb-dg__group-label">{label}</div>}
      <div className="kb-dg__row">{children}</div>
    </div>
  );
}

export function DiagramRow({ children }) {
  return <div className="kb-dg__row kb-dg__row--bare">{children}</div>;
}

export function DiagramArrow({
  label,
  icon,
  direction = "down",
  dashed = false,
}) {
  return (
    <div
      className={`kb-dg__arrow kb-dg__arrow--${direction}${dashed ? " kb-dg__arrow--dashed" : ""}`}
    >
      <span className="kb-dg__arrow-line" />
      {(label || icon) && (
        <span className="kb-dg__arrow-label">
          <Glyph name={icon} />
          {label && <span>{label}</span>}
        </span>
      )}
      <span className="kb-dg__arrow-line kb-dg__arrow-line--head" />
    </div>
  );
}
