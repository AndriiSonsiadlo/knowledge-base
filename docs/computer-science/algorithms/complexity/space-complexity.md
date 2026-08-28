---
id: space-complexity
title: Space Complexity
sidebar_label: Space Complexity
sidebar_position: 5
tags: [computer-science, algorithms, complexity, space-complexity, recursion]
---

# Space Complexity

Time complexity answers "how does the work grow?"; space complexity asks the same question about
memory. It gets less attention, and that is a mistake with two different failure modes: an algorithm
that runs out of memory long before it runs out of time budget, and a recursive algorithm that overflows
its call stack on an input a purely time-based analysis said nothing about.

The number that matters day to day is **auxiliary space** — memory used *beyond* the input itself. An
algorithm that reads an array of n integers and needs no other storage has Θ(n) total space but Θ(1)
auxiliary space, and it is the auxiliary figure that distinguishes it from an algorithm that needs a
second array of the same size. Total space is rarely the interesting number, because the input has to
be stored somewhere regardless of which algorithm processes it.

Recursion complicates this because its cost is easy to miss: a function that allocates nothing itself
still pays for every pending call, because the runtime keeps a stack frame — return address, local
variables, saved registers — alive until that call returns. A recursion of depth d therefore costs Θ(d)
auxiliary space purely from the call stack, on top of whatever each individual frame allocates. This is
why an algorithm can be time-efficient and still crash: not from running out of time, but from
exhausting the stack.

## Core Concepts

| Term | Meaning |
|---|---|
| **Total space** | Input space + auxiliary space |
| **Auxiliary space** | Everything beyond the input — the number usually meant by "space complexity" |
| **Call stack cost** | One frame per pending call; a recursion of depth d costs Θ(d) even with no local allocation |
| **In-place (strict)** | O(1) auxiliary space — no growth with n, recursion included |
| **In-place (loose, common usage)** | Modifies the input buffer directly, ignoring recursion-stack depth |
| **Time/space trade-off** | Spending more of one resource to reduce the other for the same problem |

## Mechanism

Recursive and iterative sum of `[5, 1, 8, 3]`, with the stack depth after each call shown explicitly:

```text
recursive_sum([5, 1, 8, 3]):

  call depth 1: sum([5,1,8,3]) = 5 + sum([1,8,3])      stack: [frame1]
  call depth 2: sum([1,8,3])   = 1 + sum([8,3])         stack: [frame1, frame2]
  call depth 3: sum([8,3])     = 8 + sum([3])           stack: [frame1, frame2, frame3]
  call depth 4: sum([3])       = 3 + sum([])            stack: [frame1, frame2, frame3, frame4]
  call depth 5: sum([])        = 0  (base case)          stack: [f1, f2, f3, f4, f5] ← peak, depth 5
  unwinding:    f5 returns 0 → f4 returns 3 → f3 returns 11 → f2 returns 12 → f1 returns 17

  peak auxiliary space: Θ(n) — one frame alive per element, at the deepest point

iterative_sum([5, 1, 8, 3]):

  acc=0                          stack: [frame] (one frame, whole run)
  acc=0+5=5
  acc=5+1=6
  acc=6+8=14
  acc=14+3=17

  peak auxiliary space: Θ(1) — one accumulator, one frame, regardless of n
```

Both compute 17 in Θ(n) time. Only the recursive version pays Θ(n) *space* — every pending call is a
live frame until the base case returns and unwinding begins.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def recursive_sum(a):
    """Θ(n) time, Θ(n) auxiliary — one stack frame per element until the base case."""
    if not a:
        return 0
    return a[0] + recursive_sum(a[1:])


def iterative_sum(a):
    """Θ(n) time, Θ(1) auxiliary — one accumulator, one frame for the whole run."""
    acc = 0
    for value in a:
        acc += value
    return acc


A = [5, 1, 8, 3]
assert recursive_sum(A) == 17
assert iterative_sum(A) == 17
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <vector>

long long recursive_sum(const std::vector<int>& a, std::size_t i = 0) {
    if (i == a.size()) return 0;                          // base case: depth n+1 frames alive
    return a[i] + recursive_sum(a, i + 1);                 // Θ(n) auxiliary — the call stack
}

long long iterative_sum(const std::vector<int>& a) {
    long long acc = 0;
    for (int value : a) acc += value;                      // Θ(1) auxiliary — one accumulator
    return acc;
}
```

</TabItem>
</Tabs>

### Memoization: trading space for time, made concrete

Naive recursive Fibonacci re-derives the same subproblems repeatedly — `fib(5)` calls `fib(4)` and
`fib(3)`, and `fib(4)` calls `fib(3)` again, duplicating work exponentially. Its call stack alone costs
Θ(n) (the deepest chain of calls is n long), but the total number of calls is Θ(φⁿ). Caching every
`fib(k)` already computed turns each call into an O(1) dictionary lookup after the first:

```text
fib(5) without memoization: 15 calls total, deepest chain 5 — Θ(φⁿ) time, Θ(n) stack space
fib(5) with memoization: each of fib(0)..fib(5) computed once, every repeat a cache hit
                         — Θ(n) time, Θ(n) space (cache table + Θ(n) stack)
```

The cache adds Θ(n) auxiliary space that the naive version did not need, in exchange for collapsing
exponential time to linear — the trade is explicit and named, not incidental.

Tail-recursive versions of `recursive_sum` do not fix this in general: Python's interpreter performs no
tail-call optimisation at all, so any recursive translation of a loop still costs Θ(n) stack in CPython
regardless of tail position. C++ compilers *may* optimise a genuine tail call under `-O2`, but this is a
compiler courtesy, not a language guarantee — nothing in the C++ standard requires it.

## Practical Usage

"In-place" is used two ways in practice, and the gap between them matters. The **strict** meaning is
O(1) auxiliary space including recursion — insertion sort and heapsort qualify; in-place quicksort does
not, strictly, because its recursion stack grows with input (Θ(log n) expected, Θ(n) worst case on an
adversarial or already-sorted input with a naive pivot choice). The **loose, common** meaning — "modifies
the input buffer rather than allocating a second one the size of the input" — is what most people mean
when they call quicksort in-place, and it is a real property (mergesort's Θ(n) auxiliary buffer is what
it is contrasted against) but it is not the same claim as O(1) total auxiliary space.

Three named time/space trades:

- **Memoization.** Naive recursive Fibonacci is Θ(φⁿ) time, Θ(n) space (call depth) with no memory of
  past results; caching every `fib(k)` already computed drops time to Θ(n) at the cost of Θ(n) space for
  the cache — trading memory for an exponential-to-linear time win.
- **Mergesort vs heapsort.** Both are Θ(n log n) worst case; mergesort spends Θ(n) auxiliary space on a
  merge buffer to stay stable, heapsort is Θ(1) auxiliary and unstable. Same time bound, a real space
  and stability trade.
- **Hash sets for lookup.** Checking "has this been seen before" by re-scanning a list each time is
  Θ(1) auxiliary space and Θ(n) time per check; a hash set is Θ(n) auxiliary space and Θ(1) average time
  per check — the classic space-for-time trade.

## Edge Cases & Pitfalls

- **Calling a deeply recursive algorithm in-place.** In-place strictly means O(1) auxiliary space,
  recursion included; an algorithm with an unbounded recursion depth cannot meet that bar regardless of
  whether it allocates a second buffer.
- **Deep recursion causing `RecursionError` / stack overflow.** Python raises `RecursionError` past its
  default limit (`sys.getrecursionlimit()`, 1000 by default, per the
  [`sys` module docs](https://docs.python.org/3/library/sys.html#sys.setrecursionlimit)); C++ has no
  such check and simply crashes. Both are the Θ(n) stack cost from this page's mechanism section made
  concrete, not a bug in the algorithm's logic.
- **Recursion that looks like it should be tail-recursive, and isn't optimised.** `return a[0] +
  recursive_sum(a[1:])` performs the addition *after* the recursive call returns — it is not a tail
  call even syntactically, and the `a[1:]` slice also copies, adding Θ(n) *more* auxiliary space beyond
  the stack itself.
- **Ignoring auxiliary space when comparing "equal" time complexities.** Two Θ(n log n) sorts are not
  interchangeable if one needs Θ(n) extra memory and the input barely fits in RAM to begin with.

## Comparisons

| Algorithm | Time (worst) | Auxiliary space (worst) | In-place, strict sense |
|---|---|---|---|
| [Insertion sort](../sorting/insertion-sort.md) | Θ(n²) | Θ(1) | Yes |
| [Heapsort](../sorting/heapsort.md) | Θ(n log n) | Θ(1) | Yes |
| [Quicksort](../sorting/quicksort.md) | Θ(n²) | Θ(n) (recursion, adversarial pivot) | No — despite common usage |
| [Mergesort](../sorting/mergesort.md) | Θ(n log n) | Θ(n) | No |
| Recursive sum (this page) | Θ(n) | Θ(n) | No |
| Iterative sum (this page) | Θ(n) | Θ(1) | Yes |

## Recall

<Recall
  invariant="Total space = input space + auxiliary space, and every pending recursive call holds a stack frame — a recursion of depth d costs Θ(d) auxiliary space even if each call allocates nothing itself."
  costs={[
    ["recursive sum of n elements, call stack (worst)", "Θ(n) auxiliary"],
    ["iterative sum of n elements (worst)", "Θ(1) auxiliary"],
    ["mergesort auxiliary buffer (worst)", "Θ(n) auxiliary"],
    ["quicksort recursion stack (average/expected)", "Θ(log n) auxiliary"],
    ["quicksort recursion stack, unbalanced/adversarial (worst)", "Θ(n) auxiliary"],
    ["in-place insertion sort (worst)", "Θ(1) auxiliary"],
  ]}
  reachFor="Deciding between two algorithms of similar time complexity, or diagnosing a stack overflow that a purely time-based analysis would never predict."
  trap="Calling an algorithm 'in-place' because it does not allocate a second array, while ignoring an O(n)-deep recursion stack that costs exactly the memory the phrase claims to avoid."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 7 — quicksort's
  recursion-depth analysis, including the adversarial-input worst case this page cites.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.3 — quicksort, with the recursion-stack bound stated
  alongside the time bound rather than as an afterthought.
- [`sys.setrecursionlimit`](https://docs.python.org/3/library/sys.html#sys.setrecursionlimit) — CPython
  docs; the default 1000-frame limit that turns unbounded recursion into a `RecursionError` rather than
  a silent crash.

## Related Pages

- [Amortized Analysis](./amortized-analysis.md) — the other place a naive time reading misses the real
  cost, there paid in time rather than stack space.
- [Common Complexities](./common-complexities.md) — where auxiliary space for the standard sorts is
  first introduced, expanded here into the recursion-stack argument.
- [Choosing a Sort](../sorting/choosing-a-sort.md) — the time/space trade between mergesort and
  heapsort applied as a concrete decision.
- [Recurrences & the Master Theorem](./recurrences-and-master-theorem.md) — the recursion trees used
  there to sum *time* per level sum stack *depth* the same way for space.
