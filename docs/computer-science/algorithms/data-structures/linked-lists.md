---
id: linked-lists
title: Linked Lists
sidebar_label: Linked Lists
sidebar_position: 2
tags: [computer-science, algorithms, data-structures, linked-list]
---

# Linked Lists


A linked list stores each element in its own node, together with a pointer to the next one. Nothing
is contiguous, so there is no arithmetic that finds element `i` — you follow pointers from the head
until you arrive.

In exchange, inserting or removing a node costs a couple of pointer assignments regardless of list
length, and never moves any other element.

<Figure src="/img/cs/algorithms/singly-linked-list.png"
        alt="Three nodes in a row, each split into a data field and a pointer field, with arrows from each pointer to the next node and the final pointer terminating in null"
        caption="Each node holds its value and the address of the next. The chain ends at a null pointer — and there is no way to find the middle without walking there."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Singly-linked-list.svg"
        license="Public domain" />

## Core Concepts

| Variant | Each node holds | Enables |
|---|---|---|
| **Singly linked** | `next` | Forward traversal only |
| **Doubly linked** | `next`, `prev` | Backward traversal; $O(1)$ removal given only the node |
| **Circular** | last node points back to first | Round-robin iteration with no end case |
| **Sentinel / dummy head** | a permanent empty node at the front | Removes the "is it the first node?" special case from every operation |

## Architecture / Mechanism

### The core operations

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
class Node:
    def __init__(self, value, nxt=None):
        self.value = value
        self.next = nxt

# Insert after a node we already hold — O(1), no traversal
def insert_after(node, value):
    node.next = Node(value, node.next)

# Delete the node after a node we hold — O(1)
def delete_after(node):
    if node.next:
        node.next = node.next.next

# Find the nth node — O(n), and this is the catch
def get(head, n):
    while head and n:
        head, n = head.next, n - 1
    return head
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
struct Node {
    int value;
    Node* next = nullptr;
};

// Insert after a node we already hold — O(1), no traversal
void insert_after(Node* node, int value) {
    node->next = new Node{value, node->next};
}

// Delete the node after a node we hold — O(1)
void delete_after(Node* node) {
    if (node->next) {
        Node* dead = node->next;
        node->next = dead->next;
        delete dead;
    }
}

// Find the nth node — O(n), and this is the catch
Node* get(Node* head, int n) {
    while (head && n) {
        head = head->next;
        --n;
    }
    return head;
}
```

</TabItem>
</Tabs>

The asymmetry is the whole story. Every operation is $O(1)$ **given a reference to the right node**,
and getting that reference is $O(n)$. A linked list only pays off when the traversal was going to
happen anyway, or when you were handed the node by something else.

### Why a sentinel node simplifies the code

Without one, inserting or deleting at the head is a special case, because there is no predecessor to
update — so every function grows an `if node is head` branch. A permanent dummy node in front means
every real node has a predecessor and the special case disappears. It costs one node of memory and
removes the most common source of off-by-one bugs in list code.

### Two-pointer techniques

Linked lists are where the [two-pointer pattern](../problem-solving-patterns/two-pointers-and-sliding-window.md)
earns its keep, because you cannot index:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Middle of the list in one pass: fast moves twice per slow step
def middle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow

# Cycle detection (Floyd's algorithm): if there is a loop, fast laps slow
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            return True
    return False
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Middle of the list in one pass: fast moves twice per slow step
Node* middle(Node* head) {
    Node* slow = head;
    for (Node* fast = head; fast && fast->next; fast = fast->next->next)
        slow = slow->next;
    return slow;
}

// Cycle detection (Floyd's algorithm): if there is a loop, fast laps slow
bool has_cycle(Node* head) {
    Node* slow = head;
    Node* fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

</TabItem>
</Tabs>

## Practical Usage

Where linked lists genuinely win:

- **LRU caches** — a hash table maps key → node, and the doubly linked list maintains recency. The
  hash table supplies the node reference in $O(1)$, so the list's $O(1)$ splice is actually reachable.
  This is the pattern that makes linked lists worth knowing.
- **Intrusive lists in kernels and allocators** — the node fields live inside the object itself, so
  an object can remove itself from a list without any lookup or allocation. Linux's `list_head` is
  the canonical example.
- **Structures built from nodes anyway** — the chains in a
  [hash table with separate chaining](./hash-tables.md), or free lists in an allocator.

## Edge Cases & Pitfalls

:::danger[Linked lists are slower than arrays far more often than the complexity table implies]
Traversing a linked list is a **dependent load chain**: the address of the next node is not known
until the current one arrives from memory, so the CPU cannot prefetch and cannot overlap the misses.
A sequential array scan of the same elements issues independent loads that the hardware prefetcher
handles perfectly.

The practical consequence is that "insertion is $O(1)$, so use a list" is usually wrong. Inserting into
a `vector` means an $O(n)$ `memmove`, which modern hardware performs at many gigabytes per second;
finding the insertion point in a list means n cache misses at ~100 ns each. For anything short of
enormous, the array wins — including on the operation the list is supposed to be good at.
:::

- **`std::list::size()` was $O(n)$** in some pre-C++11 implementations. The standard now requires $O(1)$,
  but the anecdote is a reminder to check what your library actually guarantees.
- **Reversing or sorting a list** is doable in $O(n)$ and $O(n \log n)$ respectively, but the constant
  factors are poor. Copy into an array, operate, copy back — this is frequently faster.
- **Memory overhead is real.** A singly linked list of 8-byte integers on a 64-bit machine spends
  8 bytes on the pointer and typically another 8–16 on allocator bookkeeping per node — a 3× or worse
  memory penalty over an array, which then costs you again in cache pressure.

## Comparisons

| Operation | [Array](./arrays.md) | Singly linked | Doubly linked |
|---|---|---|---|
| Access by index | $O(1)$ | $O(n)$ | $O(n)$ |
| Insert/delete at front | $O(n)$ | $O(1)$ | $O(1)$ |
| Insert/delete at back | $O(1)$ amortized | $O(n)$ without a tail pointer | $O(1)$ with a tail pointer |
| Insert/delete given the node | $O(n)$ | $O(1)$ after the *previous* node | $O(1)$ |
| Memory per element | Element only | Element + 1 pointer | Element + 2 pointers |

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, §10.2 — linked lists, sentinels, and the operations above.
- [Linux kernel `list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h) — the intrusive doubly-linked circular list used throughout the kernel.

### Books & Videos

- Bjarne Stroustrup, ["Why you should avoid Linked Lists"](https://www.youtube.com/watch?v=YQs6IC-vgmo) — the short talk behind the pitfall above, with measurements.

## Related Pages

- [Arrays & Dynamic Arrays](./arrays.md) — the alternative, and usually the right one.
- [Stacks & Queues](./stacks-and-queues.md) — commonly built on either representation.
- [Hash Tables](./hash-tables.md) — where chained linked lists appear inside another structure.
