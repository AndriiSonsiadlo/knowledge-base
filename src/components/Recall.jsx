import React from "react";

// <Recall /> — the fixed recall card at the top of every algorithms page.
//
// Four rows, always the same four, always in this order, so the card can be read
// by shape rather than by reading: what must stay true, what it costs, when to
// reach for it, and the one bug everybody writes.
//
// Usage in markdown:
//   <Recall
//     invariant="Every parent outranks its children; the tree is complete."
//     costs={[["peek", "O(1)"], ["push / pop", "O(log n)"], ["build from n", "O(n)"]]}
//     reachFor="You only ever need the extreme: k-th largest, next event, Dijkstra's frontier."
//     trap="Python's heapq is min-only and has no reverse= — negate, or invert the comparison." />
export default function Recall({ invariant, costs = [], reachFor, trap }) {
	return (
		<aside className="kb-recall">
			<div className="kb-recall__row">
				<span className="kb-recall__label">Invariant</span>
				<span className="kb-recall__body">{invariant}</span>
			</div>
			<div className="kb-recall__row">
				<span className="kb-recall__label">Costs</span>
				<span className="kb-recall__body kb-recall__costs">
					{costs.map(([label, cost]) => (
						<React.Fragment key={label}>
							<span className="kb-recall__cost-label">{label}</span>
							<code className="kb-recall__cost">{cost}</code>
						</React.Fragment>
					))}
				</span>
			</div>
			<div className="kb-recall__row">
				<span className="kb-recall__label">Reach for it</span>
				<span className="kb-recall__body">{reachFor}</span>
			</div>
			<div className="kb-recall__row">
				<span className="kb-recall__label">Trap</span>
				<span className="kb-recall__body">{trap}</span>
			</div>
		</aside>
	);
}
