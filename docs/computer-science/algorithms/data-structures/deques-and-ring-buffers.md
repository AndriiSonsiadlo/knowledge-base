---
id: deques-and-ring-buffers
title: Deques & Ring Buffers
sidebar_label: Deques & Ring Buffers
sidebar_position: 12
tags: [computer-science, algorithms, data-structures, deque, ring-buffer, circular-buffer]
---

# Deques & Ring Buffers

A [stack](./stacks-and-queues.md) grows and shrinks at one end; a [queue](./stacks-and-queues.md) adds
at one end and removes at the other. A **deque** (double-ended queue) generalises both: push and pop
at *either* end in the same cost, so it is a stack, a queue, or both at once depending on which end a
caller chooses. That flexibility is the whole feature — sliding-window algorithms, undo/redo history,
and work-stealing schedulers all need to add or remove from both ends, and forcing that through a
structure that only supports one end means paying for a workaround.

Two designs get there for entirely different reasons. A **block-based deque** — Python's
`collections.deque`, `std::deque` — stores fixed-size chunks and a directory pointing at them, so
pushing at either end means writing into an existing block or allocating one more, never shifting
existing elements. A **ring (circular) buffer** is the fixed-capacity special case: one contiguous
array, a head index and a tail index that both wrap around the end back to the start, and no
allocation at all once the buffer exists — the trade is a capacity fixed at construction time in
exchange for zero allocation overhead per operation.

Both are "arrays that pretend the two ends are next to each other" in spirit; they differ in whether
that pretence is implemented with a directory of blocks (unbounded, general-purpose) or literal
modular arithmetic on one fixed array (bounded, allocation-free).

## Core Concepts

| Term | Meaning |
|---|---|
| **Deque** | Double-ended queue: push/pop at either front or back |
| **Block** | A fixed-size chunk of contiguous storage; a block-based deque is a doubly linked list of these |
| **Directory / block map** | The structure that finds the right block for a given logical index |
| **Ring buffer** | A fixed-capacity circular array: `head` and `tail` indices wrap modulo capacity |
| **Wraparound** | `tail` (or `head`) advancing past the last slot back to index 0 |
| **Full vs. empty ambiguity** | `head == tail` describes both an empty buffer and a full one, unless resolved explicitly |

## Mechanism

### `collections.deque`: a doubly linked list of blocks

CPython's `deque` is not a resizable array. It is a doubly linked list where each node is a **block of
64 pointers**, not a single element — the source comment in CPython's `Modules/_collectionsmodule.c`
states the block size directly: `#define BLOCKLEN 64`. Pushing at either end writes into the current
end block's next free slot, in $O(1)$, and only allocates a new block once a block is exhausted — so
allocation is amortized across 64 pushes, not paid on every one.

Indexing by position (`d[i]`) is where this design costs something: there is no single array to offset
into, so reaching logical index `i` means walking the block list from whichever end is closer,
$O(n)$ in the worst case for a middle index — a cost `list` does not have, and the reason a `deque` is
not a drop-in replacement for random-access code (Python documentation,
[`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque), notes
this explicitly: "indexed access is O(1) at both ends but slows to O(n) in the middle").

```text
deque with BLOCKLEN = 4 (shrunk from 64 for the diagram), after several appendleft/append calls:

  block A (left)      block B (middle)      block C (right)
  [ _, _, x, y]  <->  [a, b, c, d]     <->  [e, f, _, _]
        ^                                        ^
   leftmost filled                        rightmost filled
   slot is x                                 slot is f

appendleft(w): block A has one free slot on the left → write it, O(1), no new block
append(g):     block C has a free slot on the right  → write it, O(1), no new block
d[5]:          walk from whichever end is closer — here from the right, 2 hops into block C
```

### `std::deque`'s block table

C++'s `std::deque` is specified only by complexity guarantees, not layout, but the standard's
guarantees ($O(1)$ amortized push/pop at both ends, $O(1)$ random-access indexing — see
[cppreference, `std::deque`](https://en.cppreference.com/w/cpp/container/deque)) are what every major
implementation (libstdc++, libc++) satisfies with a **map of pointers to fixed-size blocks**: an array
of block pointers (the "map"), each pointing at one block of elements. Unlike Python's `deque`, the map
itself supports $O(1)$ indexing — `map[i / block_size][i % block_size]` — because the map is a
contiguous array of pointers, not a linked list of blocks. That one difference is why `std::deque`
gives $O(1)$ *random-access* indexing (via `operator[]`) while `collections.deque` gives only $O(1)$
*end* access and $O(n)$ middle access — same block idea, different directory structure over the
blocks.

### Ring buffers: the head/tail/full-vs-empty problem

A fixed-capacity ring buffer over one array of size `cap` tracks `head` (next slot to pop) and `tail`
(next slot to push), both taken modulo `cap`. Pushing writes `buf[tail]; tail = (tail + 1) % cap`.
Popping reads `buf[head]; head = (head + 1) % cap`. The one subtlety: after enough pushes and pops,
`head` can equal `tail` in two completely different situations — the buffer is empty, or it just
wrapped all the way around and is completely full — and the indices alone cannot tell those apart.
The standard fixes are: keep an explicit `count` (or `size`) field, sacrifice one slot so "full" is
detected as `(tail + 1) % cap == head` before it ever reaches equality, or split `head`/`tail` into
absolute (non-wrapping) counters and only wrap on access — this page's implementation below uses the
explicit `count`.

<Figure src="/img/cs/algorithms/ring-buffer-states.png"
        alt="Four states of an 8-slot ring buffer: empty with head equal to tail at index 0; after five pushes with head at 0 and tail at 5; after two pops with head advanced to 2; after four more pushes where tail has wrapped past index 7 back to index 1"
        caption="An 8-slot ring buffer through push ×5, pop ×2, push ×4: the fourth panel's tail (index 1) is numerically before its head (index 2) — the wraparound that makes head/tail comparisons modular, not a plain less-than." />

```text
8-slot ring buffer, capacity 8, count tracked explicitly:

start:              head=0 tail=0 count=0        [_ _ _ _ _ _ _ _]
push 10,20,30,40,50: head=0 tail=5 count=5        [10 20 30 40 50 _ _ _]
pop, pop:            head=2 tail=5 count=3        [.. .. 30 40 50 _ _ _]
push 60,70,80,90:    tail: 5->6->7->0->1 (wraps)   [90 .. 30 40 50 60 70 80]
                     head=2 tail=1 count=7
```

`tail` finishing at 1 while `head` sits at 2 is exactly the wraparound: slot 0 holds `90`, the seventh
of the last four pushes, even though 0 is numerically *before* `head`. Any code that compares `head`
and `tail` with `<` instead of computing occupied slots via `count` (or modular distance) gets this
case wrong.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
class RingBuffer:
    """Fixed-capacity ring buffer with an explicit count to resolve full-vs-empty."""

    def __init__(self, capacity):
        self.buf = [None] * capacity
        self.capacity = capacity
        self.head = 0            # next slot to pop
        self.tail = 0            # next slot to push
        self.count = 0

    def push(self, value):
        if self.count == self.capacity:
            raise OverflowError("ring buffer is full")
        self.buf[self.tail] = value
        self.tail = (self.tail + 1) % self.capacity   # wraparound: modulo, not clamp
        self.count += 1

    def pop(self):
        if self.count == 0:
            raise IndexError("ring buffer is empty")
        value = self.buf[self.head]
        self.head = (self.head + 1) % self.capacity
        self.count -= 1
        return value

    def is_full(self):
        return self.count == self.capacity

    def is_empty(self):
        return self.count == 0
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <optional>
#include <stdexcept>
#include <vector>

template <typename T>
class RingBuffer {
public:
    explicit RingBuffer(std::size_t capacity) : buf_(capacity), capacity_(capacity) {}

    void push(T value) {
        if (count_ == capacity_) throw std::overflow_error("ring buffer is full");
        buf_[tail_] = std::move(value);
        tail_ = (tail_ + 1) % capacity_;              // wraparound: modulo, not clamp
        ++count_;
    }

    T pop() {
        if (count_ == 0) throw std::underflow_error("ring buffer is empty");
        T value = std::move(buf_[head_]);
        head_ = (head_ + 1) % capacity_;
        --count_;
        return value;
    }

    bool full() const { return count_ == capacity_; }
    bool empty() const { return count_ == 0; }

private:
    std::vector<T> buf_;
    std::size_t capacity_, head_ = 0, tail_ = 0, count_ = 0;
};
```

</TabItem>
</Tabs>

## Practical Usage

```python showLineNumbers
from collections import deque

# sliding-window maximum uses a deque of INDICES, kept monotonically decreasing by value
def sliding_window_max(nums, k):
    dq = deque()             # holds indices; front is always the current window's max
    result = []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:      # O(1) amortized: each index pushed/popped once
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result

assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]

rb = RingBuffer(8)
for v in (10, 20, 30, 40, 50):
    rb.push(v)
assert rb.pop() == 10 and rb.pop() == 20
for v in (60, 70, 80, 90):
    rb.push(v)
assert rb.count == 7 and rb.tail == 1 and rb.head == 2   # matches the traced wraparound
```

- **`collections.deque(maxlen=n)`.** A built-in bounded ring buffer: pushing past `maxlen` silently
  drops from the opposite end, in $O(1)$ (Python docs,
  [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque)) — the
  standard way to keep "the last n items seen" without hand-writing the wraparound logic above.
  `deque.popleft()` is the $O(1)$ front-pop that a plain `list.pop(0)` cannot offer (`list.pop(0)` is
  $O(n)$: every remaining element shifts down one slot).
  - **Sliding-window problems.** Maintaining a monotonic deque of *indices* (shown above) turns an
  $O(nk)$ brute-force sliding-window maximum into $O(n)$ amortized — each index enters and leaves the
  deque at most once.
- **Audio/network buffers.** A fixed-size ring buffer is the standard structure between a producer
  (audio callback, network receive) and consumer running at different rates, precisely because it
  never allocates once created — allocation inside a real-time audio callback is a correctness bug,
  not just a performance one.
- **BFS frontiers, undo/redo stacks, and work-stealing deques.** BFS needs FIFO order
  (`popleft`/`append`); work-stealing schedulers push and pop from one end locally and steal from the
  other end — the double-ended access is what makes stealing cheap without locking the whole queue.

## Edge Cases & Pitfalls

- **Indexing a `deque` in a hot loop.** `d[i]` for an arbitrary `i` is $O(n)$ on `collections.deque`,
  not $O(1)$ — code migrated from `list` that indexes by position pays for it silently. Use it for
  end operations and iteration, not random access.
- **Comparing `head < tail` to test ordering.** After a wraparound, `tail` can be numerically smaller
  than `head` (as in the traced example, `tail=1 < head=2` while the buffer holds 7 elements) — any
  logic that assumes `tail >= head` for a non-empty buffer breaks the first time the buffer wraps.
- **The `head == tail` ambiguity, unresolved.** A ring buffer that drops the `count` field and tries to
  distinguish full from empty using only `head`/`tail` needs one of the standard fixes (reserve one
  slot, or track `count`/absolute counters) — skipping this is the classic ring-buffer bug, and it
  surfaces only once the buffer happens to wrap, which is often well after the code first ships.
- **`list.pop(0)` mistaken for a queue's O(1) dequeue.** A plain Python `list` used as a queue via
  `pop(0)` is $O(n)$ per call, because every remaining element shifts down one index — the entire
  reason `collections.deque` exists for FIFO workloads.
- **Fixed capacity, unexpectedly exceeded.** A ring buffer built for expected load throws or silently
  overwrites (implementation-dependent) on overflow — decide explicitly which, and document it, rather
  than discovering the behaviour under production load.

## Comparisons

| | Block-based deque (`collections.deque`, `std::deque`) | Ring buffer (fixed capacity) | Dynamic array (`list`, `std::vector`) |
|---|---|---|---|
| Push/pop at both ends (amortized) | $O(1)$ | $O(1)$ | $O(1)$ back, $O(n)$ front |
| Random access by index (worst) | $O(n)$ Python, $O(1)$ C++ | $O(1)$ | $O(1)$ |
| Capacity | Unbounded, grows by blocks | Fixed at construction | Unbounded, grows by doubling |
| Allocation per push (amortized) | Rare — one block per `BLOCKLEN` pushes | None, ever, after construction | Rare — one array per doubling |
| Memory overhead | One block-pointer directory plus partially-full end blocks | None beyond the fixed array | Unused capacity past current size |

Reach for a ring buffer specifically when the maximum size is known up front and allocation-free
operation matters (real-time, embedded, producer/consumer). Reach for a block-based deque for
general-purpose double-ended access with no fixed bound. A dynamic array remains the right default
when access is overwhelmingly at the back and by index.

## Recall

<Recall
  invariant="A deque promises O(1) push/pop at both ends by never shifting existing elements — either by directing writes into fixed-size blocks (unbounded) or wrapping two indices modulo a fixed capacity (bounded)."
  costs={[
    ["push / pop, either end (amortized)", "O(1)"],
    ["random-access index, collections.deque (worst)", "O(n)"],
    ["random-access index, std::deque or ring buffer (worst)", "O(1)"],
    ["list.pop(0) as a substitute (worst)", "O(n) — every element shifts"],
    ["monotonic-deque sliding window over n elements (amortized)", "O(n) total, each index in/out once"],
  ]}
  reachFor="Access or removal needed at both ends — sliding windows, undo/redo, BFS frontiers, producer/consumer buffers — where a plain stack or queue would force a workaround."
  trap="Indexing collections.deque by position in a hot loop, or using list.pop(0) as a queue: both look correct and are silently O(n) where O(1) was intended."
/>

## References

- Python documentation, [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque) —
  the $O(1)$ end-operation and $O(n)$ middle-index guarantees, and the `maxlen` bounded-deque
  behaviour, quoted above.
- CPython source, `Modules/_collectionsmodule.c`, `#define BLOCKLEN 64` — the fixed block size a
  `deque` links together; the doubly linked list of blocks structure is documented in the module's
  top-of-file comments.
- [cppreference, `std::deque`](https://en.cppreference.com/w/cpp/container/deque) — the complexity
  guarantees ($O(1)$ amortized insert/erase at both ends, $O(1)$ random access) that the map-of-blocks
  implementation exists to satisfy.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 "Bags, Queues, and Stacks" — the linked-list and
  resizing-array implementations of a double-ended queue this page's block-based design generalises.

## Related Pages

- [Stacks & Queues](./stacks-and-queues.md) — the single-ended structures a deque generalises.
- [Linked Lists](./linked-lists.md) — the doubly linked node structure a block-based deque links
  together, one block at a time instead of one element at a time.
- [Arrays & Dynamic Arrays](./arrays.md) — the contiguous-storage baseline a ring buffer specialises
  for a fixed, known capacity.
- [Cheat Sheet](./cheat-sheet.md) — the full operation-cost matrix across every structure in this
  folder.
