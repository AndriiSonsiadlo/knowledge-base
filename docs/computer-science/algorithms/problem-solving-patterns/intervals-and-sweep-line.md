---
id: intervals-and-sweep-line
title: Intervals & Sweep Line
sidebar_label: Intervals & Sweep Line
sidebar_position: 8
tags: [computer-science, algorithms, patterns, intervals, sweep-line, greedy]
---

# Intervals & Sweep Line

A calendar full of meetings, a set of `(start, end)` ranges to merge, a question like "how many
meetings overlap at once" — all of these are asking something about ranges on a line, and the naive
approach checks every pair of ranges against every other, an O(n²) comparison for what turns out to be
a question a single sorted pass can answer.

The trick is to stop thinking in intervals and start thinking in **events**. Every interval `(s, e)`
is really two point events: "something started at `s`" and "something ended at `e`." Sort all `2n`
events by position instead of sorting the `n` intervals, sweep left to right keeping a running count
(`+1` at a start, `−1` at an end), and every question about "what is true between here and there"
becomes a question about that running total — no per-pair comparison needed at all.

Merging is the same idea specialised to the case where only adjacency matters: sort intervals by
**start**, then walk once, extending the last kept interval whenever the next one begins before it
ends. Interval *scheduling* — pick the largest possible set of non-overlapping intervals — needs a
different sort key entirely: by **end** time, because the interval that finishes earliest always
leaves the most room for whatever comes after it, and no exchange argument beats that greedy choice
(Cormen, Leiserson, Rivest & Stein, 4th ed., §16.1).

## Core Concepts

| Term | Meaning |
|---|---|
| **Interval** | A pair `(start, end)`, usually treated as covering `[start, end]` |
| **Merge by start** | Sort by start, then fold each interval into the last kept one if it begins early enough |
| **Event sweep** | Sort every endpoint (not every interval) with a `+1`/`−1` tag, and read a running total |
| **Active count** | The running total after a given event — how many intervals currently cover that point |
| **Meeting rooms** | The minimum resources needed at once = the peak of the active-count curve |
| **Interval scheduling** | Choosing the largest compatible subset, greedily, by soonest finish time |

## Mechanism

<Figure src="/img/cs/algorithms/sweep-line-timeline.png"
        alt="Four horizontal bars for the intervals (1,4), (2,6), (8,10) and (9,12) on a timeline, with a step function beneath rising to 2 where the first two intervals and the last two intervals each overlap"
        caption="Reading the endpoints in order, not the intervals: the active count rises by one at every start and falls by one at every end." />

```text
intervals = [(1, 4), (2, 6), (8, 10), (9, 12)]

sorted events (time, delta):
  ( 1, +1)  ( 2, +1)  ( 4, -1)  ( 6, -1)  ( 8, +1)  ( 9, +1)  (10, -1)  (12, -1)

active count after each event:
   1    2    1    0    1    2    1    0
   ^--- (1,4) & (2,6) overlap ---^    ^--- (8,10) & (9,12) overlap ---^

peak active count = 2  ->  2 rooms needed, never more than two intervals at once
```

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def merge_intervals(intervals):
    """Merge overlapping intervals after sorting by start. O(n log n) worst case, the sort dominates."""
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:                       # touching counts as overlapping here
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


INTERVALS = [(1, 4), (2, 6), (8, 10), (9, 12)]
assert merge_intervals(INTERVALS) == [(1, 6), (8, 12)]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <cassert>
#include <utility>
#include <vector>

using Interval = std::pair<int, int>;

std::vector<Interval> merge_intervals(std::vector<Interval> intervals) {
    std::sort(intervals.begin(), intervals.end());
    std::vector<Interval> merged{intervals.front()};
    for (std::size_t i = 1; i < intervals.size(); ++i) {
        auto [start, end] = intervals[i];
        auto& [lastStart, lastEnd] = merged.back();
        if (start <= lastEnd) {
            lastEnd = std::max(lastEnd, end);
        } else {
            merged.push_back({start, end});
        }
    }
    return merged;
}
```

</TabItem>
</Tabs>

### Counting overlaps by sorting endpoints, not intervals

Merging only needs adjacent intervals compared. Counting *how many* intervals are active at once needs
every endpoint in one global order — this is the general event-sweep technique, and it works for any
"how much is covered right now" question, not just meeting rooms.

```python showLineNumbers
def sweep_active_counts(intervals):
    """Running count of active intervals after each event, left to right. O(n log n): the sort dominates."""
    events = sorted([(s, +1) for s, _ in intervals] + [(e, -1) for _, e in intervals])
    counts, running = [], 0
    for _, delta in events:
        running += delta
        counts.append(running)
    return events, counts


events, counts = sweep_active_counts(INTERVALS)
assert events == [(1, 1), (2, 1), (4, -1), (6, -1), (8, 1), (9, 1), (10, -1), (12, -1)]
assert counts == [1, 2, 1, 0, 1, 2, 1, 0]
```

### Meeting rooms: the peak of the active-count curve

The minimum number of rooms needed at once is exactly `max(counts)` above — but computing it via a
min-heap of in-use end times avoids materialising every event explicitly and generalises to "reuse the
room that frees up soonest."

```python showLineNumbers
import heapq


def min_meeting_rooms(intervals):
    """Minimum concurrent rooms needed. O(n log n): sort by start, track the earliest-ending room."""
    ordered = sorted(intervals)
    heap = []                                    # end times of rooms currently in use
    for start, end in ordered:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)         # reuse the room that frees up earliest
        else:
            heapq.heappush(heap, end)
    return len(heap)


assert min_meeting_rooms(INTERVALS) == 2
```

## Practical Usage

- **Python's `sorted(intervals)`** sorts tuples lexicographically for free — by start, then by end on a
  tie — which is exactly the merge-by-start order; `sorted(intervals, key=lambda iv: iv[1])` gives the
  finish-time order that interval scheduling needs. See
  [`sorted`](https://docs.python.org/3/library/functions.html#sorted).
- **`heapq`** turns "which room frees up first" into `heap[0]`, the smallest element, in O(1) — see
  [`heapq`](https://docs.python.org/3/library/heapq.html); C++'s `std::priority_queue` needs
  `std::greater<int>` as its comparator to get a min-heap instead of the default max-heap, per
  [`[priqueue.cons]`](https://eel.is/c++draft/priqueue.cons).
- Real call sites: calendar/meeting-room scheduling, CPU or resource-interval merging in a task
  scheduler, and skyline-style "how many buildings overlap this x-coordinate" problems, which are the
  2-D generalisation of the same sweep.

## Edge Cases & Pitfalls

- **Touching intervals.** `(1, 4)` and `(4, 6)` share only the point 4 — whether that counts as
  overlapping depends entirely on the convention chosen (`start <= last_end` above treats it as
  overlapping; `start < last_end` would not). Pick one and apply it consistently to both the merge
  condition and the event-sweep tie-break.
- **Tie-breaking at equal event coordinates.** When a start and an end share the same time, processing
  the end first (so it decrements before the start increments) treats touching intervals as
  non-overlapping; processing the start first treats them as overlapping. The sweep code above never
  needs this because none of the sample coordinates coincide — a real dataset usually will.
- **Sorting intervals instead of endpoints for a count.** Sorting only by start and stepping through
  intervals one at a time cannot tell when an *earlier* interval's end falls inside a *later* one's
  span without extra bookkeeping — the event sweep sidesteps this by making every endpoint, not every
  interval, a first-class item to sort.
- **Assuming sort-by-start also solves scheduling.** The interval-scheduling greedy needs sort-by-*end*;
  sorting by start and greedily taking everything compatible can strand a long early interval that
  blocks several short later ones, giving a strictly smaller selected set.

## Comparisons

| | Pairwise overlap check | Merge by start | Event sweep | Min-heap (meeting rooms) |
|---|---|---|---|---|
| Build / sort (worst) | — | O(n log n) | O(n log n) | O(n log n) |
| Answer overlap count (worst) | O(n²) | — | O(n) after sorting | O(n log n) total |
| Extra space (worst) | O(1) | O(n) | O(n) | O(n) |
| Answers | Yes/no per pair | The merged set | Active count at every instant | Peak concurrency only |

Merging and the event sweep both cost O(n log n), dominated by the sort; the difference is what they
hand back — a reduced interval set versus a full timeline of how many intervals are active at every
point.

## Recall

<Recall
  invariant="Sorting endpoints, not intervals, turns 'how many intervals cover this point' into a running total: +1 at every start, −1 at every end, read left to right."
  costs={[
    ["sort n intervals by start or end (worst)", "O(n log n)"],
    ["merge sorted intervals, one pass (worst)", "O(n)"],
    ["event sweep: sort 2n endpoints + one pass (worst)", "O(n log n)"],
    ["meeting rooms via a min-heap of end times (worst)", "O(n log n)"],
  ]}
  reachFor="Any question phrased over ranges on a line — merging, counting overlaps, minimum resources needed at any instant, or picking the largest compatible subset."
  trap="Sorting intervals by start for interval scheduling, not by end. Sort-by-start can strand short, easily-scheduled later intervals behind one long early one, choosing a smaller compatible set than sort-by-end would."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §16.1 "An
  activity-selection problem" — the exchange argument proving sort-by-finish-time is optimal for
  interval scheduling.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.5 "Applications" — sorting as the first step of a
  larger algorithm, the role it plays for both merging and the event sweep here.
- [`sorted`](https://docs.python.org/3/library/functions.html#sorted) and
  [`heapq`](https://docs.python.org/3/library/heapq.html) — CPython docs for the two building blocks
  used above.
- [`[priqueue.cons]`](https://eel.is/c++draft/priqueue.cons) — the C++ standard's `priority_queue`
  constructors, including the comparator that turns the default max-heap into a min-heap.

## Related Pages

- [Greedy Algorithms](./greedy-algorithms.md) — the general framework the sort-by-end exchange
  argument belongs to.
- [Two Pointers & Sliding Window](./two-pointers-and-sliding-window.md) — another linear scan over
  sorted data, for contiguous ranges rather than a global event order.
- [Heaps](../data-structures/heaps.md) — the min-heap that tracks the earliest-ending room.
- [Problem-Solving Patterns](./intro.md) — where this pattern sits among the others.
