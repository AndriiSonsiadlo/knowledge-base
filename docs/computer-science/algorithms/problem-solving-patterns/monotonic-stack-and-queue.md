---
id: monotonic-stack-and-queue
title: Monotonic Stack & Queue
sidebar_label: Monotonic Stack & Queue
sidebar_position: 7
tags: [computer-science, algorithms, patterns, monotonic-stack, sliding-window]
---

# Monotonic Stack & Queue

"For each element, find the nearest element to the right that is bigger" looks like it needs a nested
loop — for every index, scan forward until something bigger turns up. That is Θ(n²) worst case, and
most of the work is wasted: once index `j` has been scanned past while looking for index `i`'s answer,
scanning past it again for index `i+1` learns nothing new.

The fix is to keep a stack that only ever holds indices whose values are still *unresolved*, in an
order that is always monotonic — say, decreasing from bottom to top. A new value `v` arriving means
every index on top of the stack with a smaller value now has its answer: `v` is nearer than anything
that could come later, so those tops are popped and resolved immediately, in one pass, right when the
answer becomes available rather than by searching for it.

The same discipline generalises from a stack to a deque. A monotonic deque keeps a window's maximum
current at all times by evicting from the back whenever a bigger value arrives (nothing behind it can
ever be the max again) and evicting from the front whenever the window slides past that index. Between
the two patterns, most "next greater/smaller" and "running max/min over a window" problems reduce to
one careful loop.

## Core Concepts

| Term | Meaning |
|---|---|
| **Monotonic stack** | A stack whose values, read bottom to top, are always increasing or always decreasing |
| **Next greater element (NGE)** | For each index, the value of the nearest later index with a strictly greater value, or none |
| **Resolved / unresolved** | An index is unresolved while it sits on the stack; popping it *is* answering it |
| **Amortized O(n)** | Each index is pushed once and popped at most once — the total work across all pops is bounded by n, not by the number of comparisons |
| **Monotonic deque** | Same idea as the stack, but evicted from both ends: back for a worse candidate, front for one that fell out of the window |
| **Sentinel** | A synthetic value (often 0) appended so the final pass flushes every remaining stack entry |

## Mechanism

<Figure src="/img/cs/algorithms/monotonic-stack-trace.png"
        alt="Four bar-chart panels of the array 3 1 4 1 5 9 2 6, with processed bars in blue, the current top-of-stack bar in orange, and resolved next-greater answers labelled beneath each bar as they become known"
        caption="Each panel is one snapshot after processing index i. A bar turns from grey (unprocessed) to blue the moment it is pushed, and gets its answer labelled the moment something bigger pops it off."
        source="Generated for this page" href="" license="" />

```text
a = [3, 1, 4, 1, 5, 9, 2, 6]        indices: 0  1  2  3  4  5  6  7

i=0 v=3: stack empty                 -> push 0            stack: [0]
i=1 v=1: 3 !< 1                      -> push 1            stack: [0, 1]
i=2 v=4: 1 < 4 -> pop 1, answer[1]=4
         3 < 4 -> pop 0, answer[0]=4 -> push 2            stack: [2]
i=3 v=1: 4 !< 1                      -> push 3            stack: [2, 3]
i=4 v=5: 1 < 5 -> pop 3, answer[3]=5
         4 < 5 -> pop 2, answer[2]=5 -> push 4            stack: [4]
i=5 v=9: 5 < 9 -> pop 4, answer[4]=9 -> push 5            stack: [5]
i=6 v=2: 9 !< 2                      -> push 6            stack: [5, 6]
i=7 v=6: 2 < 6 -> pop 6, answer[6]=6
         9 !< 6                      -> push 7            stack: [5, 7]

end of array, nothing pops the rest -> answer[5] = answer[7] = -1

answer = [4, 4, 5, 5, 9, -1, 6, -1]
```

Every index is pushed exactly once. Summed over the whole pass, the *pops* also number at most n — the
stack cannot pop more than it has ever pushed — so the loop-inside-a-loop shape (an outer scan, an
inner `while` that pops) is still O(n) total. That is the amortized argument in full: it is not that
each individual step is cheap, it is that the expensive steps are rare and pay for themselves elsewhere
(Cormen, Leiserson, Rivest & Stein, 4th ed., §17.1, the aggregate method).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def next_greater_elements(a):
    """Next strictly-greater element to the right of each index, else -1. O(n) worst case."""
    n = len(a)
    answer = [-1] * n
    stack = []                      # indices; values strictly decreasing bottom to top
    for i, v in enumerate(a):
        while stack and a[stack[-1]] < v:
            answer[stack.pop()] = v
        stack.append(i)
    return answer


A = [3, 1, 4, 1, 5, 9, 2, 6]
assert next_greater_elements(A) == [4, 4, 5, 5, 9, -1, 6, -1]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <deque>
#include <vector>

std::vector<int> next_greater_elements(const std::vector<int>& a) {
    std::vector<int> answer(a.size(), -1);
    std::vector<int> stack;                       // indices, values strictly decreasing
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        while (!stack.empty() && a[stack.back()] < a[i]) {
            answer[stack.back()] = a[i];
            stack.pop_back();
        }
        stack.push_back(i);
    }
    return answer;
}
```

</TabItem>
</Tabs>

### Largest rectangle in a histogram

The same pattern answers a harder question: the largest rectangle that fits under a bar chart. Keep a
stack of indices with *increasing* heights. When a shorter bar arrives, everything taller than it on
the stack can never extend past this point, so each is popped and its rectangle finalised — its width
runs from the new top of the stack (exclusive) to the current index (exclusive).

```python showLineNumbers
def largest_rectangle(heights):
    """Largest rectangle area under a histogram. O(n) worst case: one pass, monotonic stack."""
    stack = []                                    # indices, heights strictly increasing bottom to top
    best = 0
    extended = heights + [0]                      # sentinel 0 flushes every remaining bar at the end
    for i, h in enumerate(extended):
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best


assert largest_rectangle([2, 1, 5, 6, 2, 3]) == 10   # the 5x2 block formed by bars [5, 6]
```

### Sliding window maximum with a monotonic deque

A window's maximum only ever needs the deque's front. Push new indices onto the back after evicting
anything smaller than the incoming value (they can never win again); pop from the front once its index
has fallen out of the window on the left.

```python showLineNumbers
from collections import deque


def sliding_window_max(a, k):
    """Maximum of each size-k window, left to right. O(n) amortized: each index is pushed and popped once."""
    dq = deque()                      # indices, values strictly decreasing front to back
    result = []
    for i, v in enumerate(a):
        while dq and a[dq[-1]] < v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            result.append(a[dq[0]])
    return result


assert sliding_window_max(A, 3) == [4, 4, 5, 9, 9, 9]
```

## Practical Usage

- **Python's `list` as a stack** needs nothing extra — `append`/`pop` from the end are both amortized
  O(1) (a CPython implementation detail; see the
  [Time Complexity](https://wiki.python.org/moin/TimeComplexity) wiki page). A monotonic queue wants
  [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque), whose
  docs guarantee `append`/`pop` from *either* end in O(1) — a plain `list` is O(n) worst case to pop
  from the front.
- **C++ `std::vector`** as the stack (`push_back`/`pop_back`, both amortized O(1)) and `std::deque` as
  the monotonic queue — `push_front`/`pop_front` are O(1) worst case per
  [`[deque.overview]`](https://eel.is/c++draft/deque.overview), unlike `std::vector`'s front operations.
- Real call sites: the "daily temperatures" and "trapping rain water" families, largest rectangle in a
  histogram (also the core subroutine of the maximal-rectangle-in-a-binary-matrix problem, applied row
  by row), and any streaming "max of the last k readings" dashboard.

## Edge Cases & Pitfalls

- **Strict vs non-strict comparison.** `<` versus `<=` when deciding whether to pop changes whether the
  *first* or the *last* equal value is treated as "greater." Mixing conventions between the push
  condition and the eventual answer is a silent off-by-one, not a crash.
- **Popping index vs value.** The stack holds indices so the original position is still known when an
  answer is resolved; popping and storing the *value* by mistake loses the ability to write into
  `answer[popped_index]`.
- **Forgetting the sentinel.** The histogram routine relies on the trailing 0 to flush a stack that
  never got shorter than its tallest bar — without it, bars still on the stack when the array ends are
  never scored.
- **Evicting from the wrong end.** In the deque, "value too small" is evicted from the **back**;
  "fell out of the window" is evicted from the **front**. Swapping them corrupts the invariant that the
  front is always both the maximum and inside the window.

## Comparisons

| | Naive nested scan | Monotonic stack/deque | Heap of (value, index) |
|---|---|---|---|
| Next greater element (worst) | O(n²) | **O(n) amortized** | O(n log n) |
| Largest rectangle in histogram (worst) | O(n²) | **O(n)** | — |
| Sliding window maximum (worst) | O(n·k) | **O(n) amortized** | O(n log k) |
| Extra space (worst) | O(1) | O(n) | O(k) |

A heap answers "what is the current maximum" too, but it cannot cheaply evict an element that fell out
of the window on the left — it has no O(1) way to remove an arbitrary entry — so it pays an extra log
factor a monotonic deque avoids entirely.

## Recall

<Recall
  invariant="The stack (or deque) holds only unresolved indices in an order that stays monotonic; an index is popped, and its answer fixed, the first time something violates that order."
  costs={[
    ["next greater element, n elements (amortized)", "O(n)"],
    ["largest rectangle in a histogram (worst)", "O(n)"],
    ["sliding window maximum, n elements (amortized)", "O(n)"],
    ["sliding window maximum, per-element push+evict (amortized)", "O(1)"],
  ]}
  reachFor="A left-to-right (or right-to-left) scan asking 'what is the next bigger/smaller value', or a maximum/minimum that must stay current over a moving window."
  trap="Using `<` when the problem wants the first equal-or-greater element (or vice versa) — duplicate values then sit on the stack forever instead of being resolved, and the reported answer silently skips them."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §17.1 "Aggregate analysis"
  — the amortized argument that a stack pushed and popped at most n times each is O(n) total, even
  though a single step's inner loop looks unbounded.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 "Bags, Queues, and Stacks" — the stack/queue API this
  pattern is built on.
- [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque) — CPython
  docs; O(1) appends and pops from both ends is what makes the monotonic queue efficient.
- [`[deque.overview]`](https://eel.is/c++draft/deque.overview) — the C++ standard's complexity
  guarantee for `std::deque`'s front and back operations.

## Related Pages

- [Two Pointers & Sliding Window](./two-pointers-and-sliding-window.md) — the other pattern for
  scanning contiguous ranges, without the stack.
- [Prefix Sums & Difference Arrays](./prefix-sums-and-difference-arrays.md) — precomputation for
  invertible aggregates like sum; a running max is not invertible, which is why it needs this page
  instead.
- [Stacks & Queues](../data-structures/stacks-and-queues.md) — the primitive this pattern layers an
  invariant on top of.
- [Deques & Ring Buffers](../data-structures/deques-and-ring-buffers.md) — the structure backing the
  monotonic queue.
- [Problem-Solving Patterns](./intro.md) — where this pattern sits among the others.
