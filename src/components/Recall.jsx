import { formatRecallText } from "@lib/recallFormat";

// <Recall /> — the fixed recall card at the end of every algorithms page.
//
// Four rows, always the same four, always in this order, so the card can be read
// by shape rather than by reading: what must stay true, what it costs, when to
// reach for it, and the one bug everybody writes.
//
// Props are plain strings, not markdown — but backtick spans render as code and
// any O(...)/Θ(...)/Ω(...)/o(...)/ω(...) expression renders as KaTeX, so a trap
// like "P[0] = 0, P[i] = P[i-1] + a[i-1]" should be written with the indexed
// variables backtick-quoted, and a cost of "O(n)" doesn't need any markup at all.
//
// Usage in markdown:
//   <Recall
//     invariant="Every parent outranks its children; the tree is complete."
//     costs={[["peek", "O(1)"], ["push / pop", "O(log n)"], ["build from n", "O(n)"]]}
//     reachFor="You only ever need the extreme: k-th largest, next event, Dijkstra's frontier."
//     trap="Python's heapq is min-only and has no reverse= — negate, or invert the comparison." />
function Formatted({ text, className }) {
  return (
    <span
      className={className}
      // biome-ignore lint/security/noDangerouslySetInnerHtml: trusted doc content, KaTeX-rendered at build time
      dangerouslySetInnerHTML={{ __html: formatRecallText(text) }}
    />
  );
}

export default function Recall({ invariant, costs = [], reachFor, trap }) {
  return (
    <aside className="kb-recall">
      <div className="kb-recall__row">
        <span className="kb-recall__label">Invariant</span>
        <Formatted className="kb-recall__body" text={invariant} />
      </div>
      <div className="kb-recall__row">
        <span className="kb-recall__label">Costs</span>
        <div className="kb-recall__costs">
          {costs.map(([label, cost]) => (
            <div className="kb-recall__cost-row" key={label}>
              <Formatted className="kb-recall__cost-label" text={label} />
              <Formatted className="kb-recall__cost" text={cost} />
            </div>
          ))}
        </div>
      </div>
      <div className="kb-recall__row">
        <span className="kb-recall__label">Reach for it</span>
        <Formatted className="kb-recall__body" text={reachFor} />
      </div>
      <div className="kb-recall__row">
        <span className="kb-recall__label">Trap</span>
        <Formatted className="kb-recall__body" text={trap} />
      </div>
    </aside>
  );
}
