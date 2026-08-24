---
id: stacks-and-queues
title: Stacks & Queues
sidebar_label: Stacks & Queues
sidebar_position: 3
tags: [computer-science, algorithms, data-structures, stack, queue, deque]
---

# Stacks & Queues


Stacks and queues are not new storage — they are **restrictions** on storage. Both hold a sequence,
and both deliberately refuse to let you reach into the middle of it. That refusal is the feature: an
interface with two operations has far fewer ways to be used incorrectly, and the restriction is
exactly what makes the operations O(1).

## Core Concepts

| | Stack | Queue | Deque |
|---|---|---|---|
| **Discipline** | LIFO — last in, first out | FIFO — first in, first out | Both ends |
| **Add** | `push` (to the top) | `enqueue` (to the back) | `push_front` / `push_back` |
| **Remove** | `pop` (from the top) | `dequeue` (from the front) | `pop_front` / `pop_back` |
| **Inspect** | `peek` / `top` | `front` | `front` / `back` |
| **Models** | Nesting, backtracking, undo | Fairness, buffering, arrival order | Both, plus sliding windows |

All operations are O(1). `search` is not part of either interface; if you need it, you have chosen the
wrong structure.

<Figure src="/img/cs/algorithms/stack.png"
        alt="A stack drawn as a vertical column of elements with push and pop arrows both acting on the topmost element"
        caption="Push and pop both act on the same end. Nothing below the top is reachable without removing what sits above it."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Data_stack.svg"
        license="Public domain" />

## Architecture / Mechanism

### Implementation

A stack is a dynamic array with two of its operations hidden — appending and removing at the end are
already O(1) amortized:

```python showLineNumbers
stack = []
stack.append(x)      # push
top = stack[-1]      # peek
x = stack.pop()      # pop
```

A queue is the case where the array representation goes wrong. Removing from the front of an array is
O(n), so the naive version is quadratic:

```python showLineNumbers
queue = []
queue.append(x)      # O(1)
x = queue.pop(0)     # O(n) — every remaining element shifts down
```

The fix is a **circular buffer**: keep `head` and `tail` indices into a fixed array and wrap them
modulo capacity, so neither end ever moves data. That is what real deque implementations do (Python's
`collections.deque` uses a doubly linked list of fixed-size blocks, which achieves the same O(1) ends
while allowing unbounded growth).

```python showLineNumbers
from collections import deque

q = deque()
q.append(x)          # enqueue at the back — O(1)
x = q.popleft()      # dequeue from the front — O(1)
```

:::warning[Use the right type, or the complexity silently changes]
`list.pop(0)` and `list.insert(0, x)` are O(n) in Python; `deque.popleft()` and `deque.appendleft()`
are O(1). The same trap exists as `ArrayList` versus `ArrayDeque` in Java, and `std::vector` versus
`std::deque` in C++. Nothing warns you — the loop simply becomes quadratic.
:::

### Where stacks are the machine, not a choice

The [call stack](../../assembly/calling-conventions-and-the-stack.md) is a stack because function
calls nest: a function returns to its most recent caller, which is precisely LIFO. Every recursive
algorithm therefore uses a stack whether or not it names one, and any recursion can be rewritten
iteratively by managing that stack yourself — which is how you avoid stack-overflow on deep inputs.

```python showLineNumbers
# Recursive depth-first traversal — the call stack does the bookkeeping
def dfs(node):
    if node is None:
        return
    visit(node)
    dfs(node.left)
    dfs(node.right)

# The same traversal with an explicit stack — bounded by heap, not stack size
def dfs_iterative(root):
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        visit(node)
        stack.append(node.right)   # pushed first, so popped last
        stack.append(node.left)
```

## Practical Usage

| Problem | Structure | Why |
|---|---|---|
| Matching brackets, parsing expressions | Stack | Nesting is LIFO by definition |
| Undo/redo | Two stacks | The most recent action is the first to reverse |
| [Depth-first search](../graph-algorithms/traversal.md) | Stack | Explore deepest-first |
| [Breadth-first search](../graph-algorithms/traversal.md) | Queue | Explore nearest-first |
| Task/job scheduling, request buffering | Queue | Preserves arrival order — fairness |
| Producer/consumer between threads | Concurrent queue | The handoff point, with backpressure |
| Sliding-window maximum | Deque | Push at the back, evict stale entries from the front |

A worked example — bracket matching, which is the canonical use and about as short as an algorithm gets:

```python showLineNumbers
def balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False        # wrong closer, or nothing open
    return not stack                # anything left open is unbalanced
```

## Edge Cases & Pitfalls

- **Popping an empty stack** is the most common bug in this code. Decide deliberately whether it
  raises, returns a sentinel, or is a precondition the caller must check — and be consistent.
- **Unbounded queues remove backpressure.** A queue that grows without limit converts an overload
  into memory exhaustion instead of a visible slowdown. Bound it and choose what happens when full;
  see the [thread pool](../../operating-systems/processes-and-threads.md) discussion for the same
  hazard in another setting.
- **`std::stack` and `std::queue` are adaptors**, not containers — they wrap `deque` by default. This
  matters when you want a different underlying container for cache or memory reasons.
- **Recursion depth is a real limit.** Python defaults to ~1000 frames; a deep tree or a long linked
  list will exhaust it. The iterative rewrite above is the fix, not a larger limit.

## Comparisons

| | Array-backed | Linked-list-backed |
|---|---|---|
| Stack push/pop | O(1) amortized, contiguous | O(1) always, one allocation each |
| Queue operations | O(1) with a circular buffer | O(1) with head and tail pointers |
| Memory | Compact, may over-allocate | One or two pointers per element |
| Worst-case latency | Occasional O(n) resize | No resize spike |

Array-backed is the right default; linked-list-backed matters when a single O(n) resize pause is
unacceptable.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §10.1 — stacks and queues, including the circular-buffer queue.
- [CPython `collections.deque` implementation](https://github.com/python/cpython/blob/main/Modules/_collectionsmodule.c) — the block-based doubly linked list described above.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 — "Bags, Queues, and Stacks", with both implementations developed side by side.

## Related Pages

- [Arrays & Dynamic Arrays](./arrays.md) — the usual backing store.
- [Traversal: BFS & DFS](../graph-algorithms/traversal.md) — the two disciplines producing two different search orders.
- [Calling Conventions & the Stack](../../assembly/calling-conventions-and-the-stack.md) — the stack the hardware itself maintains.
