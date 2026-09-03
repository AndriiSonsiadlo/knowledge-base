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
exactly what makes the operations $O(1)$.

## Core Concepts

| | Stack | Queue | Deque |
|---|---|---|---|
| **Discipline** | LIFO — last in, first out | FIFO — first in, first out | Both ends |
| **Add** | `push` (to the top) | `enqueue` (to the back) | `push_front` / `push_back` |
| **Remove** | `pop` (from the top) | `dequeue` (from the front) | `pop_front` / `pop_back` |
| **Inspect** | `peek` / `top` | `front` | `front` / `back` |
| **Models** | Nesting, backtracking, undo | Fairness, buffering, arrival order | Both, plus sliding windows |

All operations are $O(1)$. `search` is not part of either interface; if you need it, you have chosen the
wrong structure.

<Figure src="/img/cs/algorithms/stack.png"
        alt="A stack drawn as a vertical column of elements with push and pop arrows both acting on the topmost element"
        caption="Push and pop both act on the same end. Nothing below the top is reachable without removing what sits above it."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Data_stack.svg"
        license="Public domain" />

## Mechanism

### The same six operations, two disciplines, traced

`add A, add B, add C, remove, remove, add D` — read as `push`/`pop` on a stack and as
`enqueue`/`dequeue` on a queue, same six operations, same values:

```text
                 stack (LIFO)          queue (FIFO)
after add A,B,C  [A, B, C]             [A, B, C]
after 2 removes  [A]      (took C, B)  [C]      (took A, B)
after add D      [A, D]                [C, D]
```

Same operations, same values — the end states share only D. A stack hands back what it was given most
recently; a queue hands back what it was given longest ago.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
stack = ["A", "B", "C"]
removed = [stack.pop(), stack.pop()]
stack.append("D")
assert stack == ["A", "D"] and removed == ["C", "B"]

from collections import deque
queue = deque(["A", "B", "C"])
dequeued = [queue.popleft(), queue.popleft()]
queue.append("D")
assert list(queue) == ["C", "D"] and dequeued == ["A", "B"]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <deque>
#include <vector>

void trace_stack_and_queue() {
    std::vector<char> stack{'A', 'B', 'C'};
    char r1 = stack.back(); stack.pop_back();
    char r2 = stack.back(); stack.pop_back();
    stack.push_back('D');
    assert((stack == std::vector<char>{'A', 'D'}) && r1 == 'C' && r2 == 'B');

    std::deque<char> queue{'A', 'B', 'C'};
    char q1 = queue.front(); queue.pop_front();
    char q2 = queue.front(); queue.pop_front();
    queue.push_back('D');
    assert((queue == std::deque<char>{'C', 'D'}) && q1 == 'A' && q2 == 'B');
}
```

</TabItem>
</Tabs>

### Implementation

A stack is a dynamic array with two of its operations hidden — appending and removing at the end are
already $O(1)$ amortized. A queue is where the array representation goes wrong: removing from the
front is $O(n)$, so the naive version is quadratic. The fix is a **circular buffer** — `head` and
`tail` indices into a fixed array, wrapped modulo capacity, so neither end ever moves data. That is
what real deque implementations do (Python's `collections.deque` uses a doubly linked list of
fixed-size blocks, achieving the same $O(1)$ ends while allowing unbounded growth):

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# doc:no-run
stack = []
stack.append(x)      # push — O(1) amortized
x = stack.pop()      # pop — O(1) amortized

queue = []            # the naive, wrong way to build a queue
queue.append(x)       # O(1)
x = queue.pop(0)      # O(n) — every remaining element shifts down

from collections import deque   # the fix: a circular buffer under the hood
q = deque()
q.append(x)           # enqueue at the back — O(1)
x = q.popleft()       # dequeue from the front — O(1)
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
std::vector<int> stack;
stack.push_back(x);          // push — O(1) amortized
stack.pop_back();            // pop — O(1) amortized, returns nothing: read back() first
std::stack<int> s;           // the adaptor, when the interface should forbid indexing

std::vector<int> queue;      // the naive, wrong way to build a queue
queue.push_back(x);          // O(1)
queue.erase(queue.begin());  // O(n) — every remaining element shifts down

std::deque<int> q;           // the fix: a circular buffer under the hood
q.push_back(x);               // enqueue at the back — O(1)
q.pop_front();                 // dequeue from the front — O(1)
std::queue<int> adaptor;      // std::queue wraps a deque with exactly this interface
```

</TabItem>
</Tabs>

:::warning[Use the right type, or the complexity silently changes]
`list.pop(0)` and `list.insert(0, x)` are $O(n)$ in Python; `deque.popleft()` and `deque.appendleft()`
are $O(1)$. The same trap exists as `ArrayList` versus `ArrayDeque` in Java, and `std::vector` versus
`std::deque` in C++. Nothing warns you — the loop simply becomes quadratic.
:::

### Where stacks are the machine, not a choice

The [call stack](../../assembly/calling-conventions-and-the-stack.md) is a stack because function
calls nest: a function returns to its most recent caller, which is precisely LIFO. Every recursive
algorithm therefore uses a stack whether or not it names one, and any recursion can be rewritten
iteratively by managing that stack yourself — which is how you avoid stack-overflow on deep inputs.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// doc:no-run
// Recursive depth-first traversal — the call stack does the bookkeeping
void dfs(Node* node) {
    if (!node) return;
    visit(node);
    dfs(node->left);
    dfs(node->right);
}

// The same traversal with an explicit stack — bounded by the heap, not the stack
void dfs_iterative(Node* root) {
    std::vector<Node*> stack{root};
    while (!stack.empty()) {
        Node* node = stack.back();
        stack.pop_back();
        if (!node) continue;
        visit(node);
        stack.push_back(node->right);   // pushed first, so popped last
        stack.push_back(node->left);
    }
}
```

</TabItem>
</Tabs>

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

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

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

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <string_view>
#include <unordered_map>

bool balanced(std::string_view s) {
    static const std::unordered_map<char, char> pairs{{')', '('}, {']', '['}, {'}', '{'}};
    std::vector<char> stack;
    for (char ch : s) {
        if (ch == '(' || ch == '[' || ch == '{') {
            stack.push_back(ch);
        } else if (auto it = pairs.find(ch); it != pairs.end()) {
            if (stack.empty() || stack.back() != it->second)
                return false;       // wrong closer, or nothing open
            stack.pop_back();
        }
    }
    return stack.empty();           // anything left open is unbalanced
}
```

</TabItem>
</Tabs>

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
| Stack push/pop | $O(1)$ amortized, contiguous | $O(1)$ always, one allocation each |
| Queue operations | $O(1)$ with a circular buffer | $O(1)$ with head and tail pointers |
| Memory | Compact, may over-allocate | One or two pointers per element |
| Worst-case latency | Occasional $O(n)$ resize | No resize spike |

Array-backed is the right default; linked-list-backed matters when a single $O(n)$ resize pause is
unacceptable.

## Recall

<Recall
  invariant="A stack always returns what was added most recently (LIFO); a queue always returns what was added longest ago (FIFO) — the restriction, not the storage, is the whole structure."
  costs={[
    ["push / pop, array-backed (amortized)", "O(1)"],
    ["enqueue / dequeue, circular buffer or linked (worst)", "O(1)"],
    ["enqueue / dequeue, naive array (worst)", "O(n)"],
    ["search for an arbitrary value (worst)", "O(n)"],
  ]}
  reachFor="Nesting/backtracking/undo (stack) or fairness/arrival-order/buffering (queue) — never random access into the middle."
  trap="Using list.pop(0) / list.insert(0, x) in Python, or std::vector for a queue in C++, for the front operation — both are O(n) and silently turn a loop quadratic; use deque instead."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §10.1 — stacks and queues, including the circular-buffer queue.
- [CPython `collections.deque` implementation](https://github.com/python/cpython/blob/main/Modules/_collectionsmodule.c) — the block-based doubly linked list described above.

### Books & Videos

- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 — "Bags, Queues, and Stacks", with both implementations developed side by side.

## Related Pages

- [Arrays & Dynamic Arrays](./arrays.md) — the usual backing store.
- [Traversal: BFS & DFS](../graph-algorithms/traversal.md) — the two disciplines producing two different search orders.
- [Calling Conventions & the Stack](../../assembly/calling-conventions-and-the-stack.md) — the stack the hardware itself maintains.
