---
id: heaps
title: Heaps & Priority Queues
sidebar_label: Heaps & Priority Queues
sidebar_position: 7
tags: [computer-science, algorithms, data-structures, heap, priority-queue]
---

# Heaps & Priority Queues

A **priority queue** answers one question: *what is the most important item right now?* A **binary
heap** is the standard way to implement it — a tree whose only ordering rule is that a parent
outranks its children.

That rule is deliberately weaker than a [BST's](./trees.md). A heap cannot tell you whether 42 is
present, and cannot iterate in sorted order. It only knows its extreme, and in exchange it is cheap
to maintain and needs no pointers at all.

## Core Concepts

| Term | Meaning |
|---|---|
| **Heap property** | Every parent ≥ its children (max-heap), or ≤ (min-heap) |
| **Shape property** | The tree is *complete* — every level full except the last, filled left to right |
| **Sift up (bubble up)** | Restore the property after inserting at the bottom |
| **Sift down (heapify)** | Restore the property after replacing the root |
| **Priority queue** | The interface; a heap is the usual implementation |

Note what the heap property does *not* say: siblings are unordered, and a node deep in one subtree
may be larger than a shallow node in another. Only the root is guaranteed to be the extreme.

## Mechanism

### The array trick

The shape property means a heap has no holes, so it can live in a flat array with the tree structure
implied by arithmetic — no left/right pointers, and perfect cache locality:

<Figure src="/img/cs/algorithms/max-heap.png"
        alt="A max-heap drawn as a tree rooted at 100 with children 19 and 36, alongside the same heap laid out in an array with arrows showing each node's children at indices 2i+1 and 2i+2"
        caption="The same heap as a tree and as an array. Index 0 is the root; the children of index i sit at 2i+1 and 2i+2, and its parent at (i−1)//2."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Max-Heap.svg"
        license="CC BY-SA 3.0" />

```text
parent(i) = (i - 1) // 2
left(i)   = 2i + 1
right(i)  = 2i + 2
```

### The two operations

Both work by moving one element along a single root-to-leaf path, which is why both are $O(\log n)$:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def push(heap, value):
    heap.append(value)                 # place at the end — keeps the shape
    i = len(heap) - 1
    while i > 0:                       # sift up while it outranks its parent
        parent = (i - 1) // 2
        if heap[parent] >= heap[i]:
            break
        heap[parent], heap[i] = heap[i], heap[parent]
        i = parent

def pop_max(heap):
    top = heap[0]
    heap[0] = heap[-1]                 # move the last element to the root
    heap.pop()
    i, n = 0, len(heap)
    while True:                        # sift down while a child outranks it
        largest = i
        for child in (2 * i + 1, 2 * i + 2):
            if child < n and heap[child] > heap[largest]:
                largest = child
        if largest == i:
            break
        heap[i], heap[largest] = heap[largest], heap[i]
        i = largest
    return top

heap = []
for v in (5, 1, 8, 3):
    push(heap, v)
assert pop_max(heap) == 8
assert pop_max(heap) == 5
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <vector>
#include <cstddef>

void push(std::vector<int>& heap, int value) {
    heap.push_back(value);                  // place at the end — keeps the shape
    std::size_t i = heap.size() - 1;
    while (i > 0) {                         // sift up while it outranks its parent
        std::size_t parent = (i - 1) / 2;
        if (heap[parent] >= heap[i]) break;
        std::swap(heap[parent], heap[i]);
        i = parent;
    }
}

int pop_max(std::vector<int>& heap) {
    int top = heap[0];
    heap[0] = heap.back();                  // move the last element to the root
    heap.pop_back();
    std::size_t i = 0, n = heap.size();
    for (;;) {                              // sift down while a child outranks it
        std::size_t largest = i;
        for (std::size_t child : {2 * i + 1, 2 * i + 2})
            if (child < n && heap[child] > heap[largest]) largest = child;
        if (largest == i) break;
        std::swap(heap[i], heap[largest]);
        i = largest;
    }
    return top;
}
```

</TabItem>
</Tabs>

| Operation | Cost |
|---|---|
| Peek at the extreme | $O(1)$ |
| Insert | $O(\log n)$ |
| Extract the extreme | $O(\log n)$ |
| Build a heap from n items | **$O(n)$** — not $O(n \log n)$ |
| Search for an arbitrary value | $O(n)$ |

:::info[Building a heap is linear, which is not obvious]
Sifting down from every non-leaf node, working backwards from the middle of the array, costs $O(n)$
rather than $O(n \log n)$. The reason is that most nodes are near the bottom and barely move: half the
nodes are leaves and cost nothing, a quarter can sift at most one level, and so on. The sum
$\sum n/2^{k+1} \cdot k$ converges to n. Use `heapq.heapify(list)` rather than pushing n times.
:::

### `heappush`, traced

Python's `heapq` is a **min**-heap ([the module's own documentation is explicit about this](https://docs.python.org/3/library/heapq.html#basic-examples)),
so this trace uses that convention. `heapq.heapify([5, 1, 8, 3])` sifts down from the last non-leaf
node first, producing `[1, 3, 8, 5]` — then `heapq.heappush(heap, 0)` places 0 at the end and sifts it
up:

```text
heapify([5, 1, 8, 3]) -> [1, 3, 8, 5]     (min-heap: every parent <= its children)

heappush(heap, 0):

  1. append 0 at the end        [1, 3, 8, 5, 0]      index 4
  2. compare to parent (idx 1, value 3): 0 < 3, swap
                                 [1, 0, 8, 5, 3]      0 now at index 1
  3. compare to parent (idx 0, value 1): 0 < 1, swap
                                 [0, 1, 8, 5, 3]      0 now at index 0 — the root, stop
```

Two swaps carried 0 from a leaf to the root — $O(\log n)$ **worst case**, one comparison-and-swap per
level of the tree, exactly as many as the heap is tall:

```python showLineNumbers
import heapq

heap = [5, 1, 8, 3]
heapq.heapify(heap)
assert heap == [1, 3, 8, 5]

heapq.heappush(heap, 0)
assert heap == [0, 1, 8, 5, 3]
assert heap[0] == 0     # heappush restored the min-heap property at the root
```

## Practical Usage

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# doc:no-run
import heapq

# Python's heapq is a MIN-heap operating in place on a plain list
heap = [5, 1, 8, 3]
heapq.heapify(heap)            # O(n)
heapq.heappush(heap, 2)        # O(log n)
smallest = heapq.heappop(heap) # O(log n)

# For a max-heap, negate — heapq has no key or reverse parameter
heapq.heappush(heap, -value)

# Pair (priority, item) tuples; add a counter to break ties so that
# unorderable items are never compared
import itertools
counter = itertools.count()
heapq.heappush(pq, (priority, next(counter), task))

# Top-k without sorting everything: O(n log k), not O(n log n)
top_10 = heapq.nlargest(10, huge_list)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
// std::priority_queue is a MAX-heap by default
std::priority_queue<int> pq;
pq.push(2);                     // O(log n)
int largest = pq.top();         // O(1)
pq.pop();                       // O(log n)

// For a min-heap, swap the comparator — no negation trick needed
std::priority_queue<int, std::vector<int>, std::greater<>> min_pq;

// The heap algorithms also work in place on any random-access range
std::vector<int> heap{5, 1, 8, 3};
std::make_heap(heap.begin(), heap.end());                       // O(n)
heap.push_back(2);
std::push_heap(heap.begin(), heap.end());                       // O(log n)
std::pop_heap(heap.begin(), heap.end()); heap.pop_back();       // O(log n)

// Pair (priority, item); a counter breaks ties so tasks are never compared
using Entry = std::tuple<int, long, Task>;
std::priority_queue<Entry, std::vector<Entry>, std::greater<>> tasks;
tasks.push({priority, counter++, task});

// Top-k without sorting everything: O(n log k), not O(n log n)
std::partial_sort(v.begin(), v.begin() + 10, v.end(), std::greater<>{});
```

</TabItem>
</Tabs>

Where priority queues show up:

- **[Dijkstra's algorithm](../graph-algorithms/shortest-paths.md)** — repeatedly take the nearest
  unvisited node. This is the single most important use.
- **[Heapsort](../sorting/heapsort.md)** — build a heap, then extract the maximum n times.
- **OS scheduling** — pick the highest-priority runnable task, as in
  [process scheduling](../../operating-systems/scheduling.md).
- **Event simulation** — process events in timestamp order as new ones are generated.
- **Streaming top-k** — keep a size-k min-heap; anything smaller than its root cannot make the cut.
  This uses $O(k)$ memory regardless of stream length.
- **Merging k sorted sequences** — a heap over the k heads gives the next element in $O(\log k)$.

## Edge Cases & Pitfalls

- **`heapq` is a min-heap with no `reverse=` option.** Negate values, or wrap them in a class with
  inverted comparison. Forgetting this is the most common heap bug in Python.
- **Tuples compare element by element**, so `(priority, task)` will compare `task` when priorities
  tie — and raise `TypeError` if tasks are not orderable. Insert a monotonic counter between them.
- **You cannot efficiently change or remove an arbitrary element.** Finding it is $O(n)$. The standard
  workaround is *lazy deletion*: mark the entry invalid, push a replacement, and discard stale entries
  when they surface at the top.
- **A heap is not sorted.** Printing the backing array shows a valid heap that looks unsorted, because
  it is. Only repeated extraction produces order.
- **`heapq` is not thread-safe.** Use `queue.PriorityQueue` for concurrent access.

## Comparisons

| | Heap | [Sorted array](./arrays.md) | [Balanced BST](./balanced-trees.md) |
|---|---|---|---|
| Peek extreme | $O(1)$ | $O(1)$ | $O(\log n)$ |
| Insert | $O(\log n)$ | $O(n)$ | $O(\log n)$ |
| Extract extreme | $O(\log n)$ | $O(1)$ at one end | $O(\log n)$ |
| Find arbitrary | $O(n)$ | $O(\log n)$ | $O(\log n)$ |
| Sorted iteration | No | Yes | Yes |
| Memory overhead | None — a plain array | None | Two pointers per node |

Use a heap when you only ever want the extreme; a balanced tree when you also need ordering or
arbitrary lookup.

## Recall

<Recall
  invariant="Every parent outranks its children; the tree is complete."
  costs={[
    ["peek (worst)", "O(1)"],
    ["push / pop (worst)", "O(log n)"],
    ["build from n items (worst)", "O(n)"],
    ["find an arbitrary value (worst)", "O(n)"],
  ]}
  reachFor="You only ever need the extreme, repeatedly: k-th largest, next event, Dijkstra's frontier."
  trap="Python's heapq is min-only and takes no reverse= — negate the keys, or wrap them in a class with an inverted __lt__."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 6 — heaps, heapsort, and the $O(n)$ build-heap analysis.
- [CPython `heapq` source](https://github.com/python/cpython/blob/main/Lib/heapq.py) — the module's docstring is an unusually good explanation of the invariant.
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html) — confirms `heapq` implements a min-heap with no `reverse=` parameter, the basis for the trace above.
- [cppreference, `std::priority_queue`](https://en.cppreference.com/w/cpp/container/priority_queue) — confirms the default comparator (`std::less`) makes it a max-heap.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.4 — "Priority Queues", with the heap developed from scratch.

## Related Pages

- [Heapsort](../sorting/heapsort.md) — the sorting algorithm this structure exists inside.
- [Shortest Paths](../graph-algorithms/shortest-paths.md) — Dijkstra's, where the priority queue determines the complexity.
- [Scheduling](../../operating-systems/scheduling.md) — priority queues in the OS.
