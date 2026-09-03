---
id: exponential-and-ternary-search
title: Exponential & Ternary Search
sidebar_label: Exponential & Ternary Search
sidebar_position: 4
tags: [computer-science, algorithms, searching, binary-search]
---

# Exponential & Ternary Search

Both of these are binary search wearing a different hat. Exponential search still finds a target in a
sorted sequence, but solves the problem of not knowing how long that sequence is — a stream, an
unbounded array, an API that answers "is index i in range" without ever revealing the total count.
Ternary search still discards a third of the range at every step, but answers a different question: not
"where is this value" but "where is the peak (or valley) of this function."

Neither replaces ordinary binary search; each removes one specific assumption it relies on —
respectively, "you know `n`" and "you have a monotonic predicate rather than a unimodal function."

:::info[Prerequisites]
Read [Binary Search](./binary-search.md) first — both algorithms here are that one, run on a range
found (exponential search) or shaped (ternary search) differently.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Exponential (galloping) search** | Doubles a bound `1, 2, 4, 8, …` until it overshoots the target, then binary searches the last doubling interval |
| **Unbounded / streamed input** | A sequence whose length is unknown or expensive to ask for up front — a generator, a socket, an array exposed only through an "is this index valid" check |
| **Unimodal function** | Strictly increases, then strictly decreases (or the mirror) — exactly one maximum (or minimum), no flat top and no second peak |
| **Ternary search** | Probes two interior points per iteration and discards the third of the range that provably cannot contain the extremum |
| **Golden-section search** | A refinement of ternary search that reuses one of the two probe points across iterations, halving the number of function evaluations |

## Mechanism

### Exponential search

Exponential search for `8` in an unbounded sorted stream: double a bound until it either overshoots the
target or hits the end of the (unknown) data, then binary search inside the last interval that bracketed
it.

```text
stream (0-indexed, sorted, length unknown): index 0=1  1=2  2=4  3=8  4=16  5=32  6=64 ...
target = 8

bound doubling (stream[0]=1 != target, so start doubling from bound=1):
  bound=1   stream[1]=2    2 < 8  -> double the bound
  bound=2   stream[2]=4    4 < 8  -> double the bound
  bound=4   stream[4]=16  16 >= 8 -> overshot; stop doubling

binary search inside [bound/2, bound) = [2, 4):
  lo=2  hi=4  mid=3  stream[3]=8   8 >= 8 -> hi = 3
  lo=2  hi=3  mid=2  stream[2]=4   4 < 8  -> lo = 3
  lo=3  hi=3  loop ends -> check stream[3]

  stream[3] == 8 -> found at index 3
```

The doubling phase costs $O(\log i)$ probes to reach an index $i$ that brackets the answer, and the
binary search phase inside a range of size $i$ costs another $O(\log i)$ — for a combined
**$O(\log i)$ worst case**, where $i$ is the position of the target (or where it would be), not the
length of the whole stream. This is the entire point: exponential search never needs to know `n`, and
its cost scales with *how far in* the answer is, not with the total size of the data.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def exponential_search(get, target):
    """Search a sorted, 0-indexed, unbounded sequence via get(i) (raises IndexError past the end)."""
    def safe_get(i):
        try:
            return get(i)
        except IndexError:
            return None

    if safe_get(0) == target:
        return 0

    bound = 1
    while True:
        v = safe_get(bound)
        if v is None or v >= target:
            break
        bound *= 2

    lo, hi = bound // 2, bound
    while lo < hi:
        mid = lo + (hi - lo) // 2
        v = safe_get(mid)
        if v is None or v >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo if safe_get(lo) == target else -1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <functional>
#include <optional>

int exponential_search(const std::function<std::optional<int>(int)>& get, int target) {
    auto v0 = get(0);
    if (v0 && *v0 == target) return 0;

    int bound = 1;
    while (true) {
        auto v = get(bound);
        if (!v || *v >= target) break;
        bound *= 2;
    }

    int lo = bound / 2, hi = bound;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        auto v = get(mid);
        if (!v || *v >= target) hi = mid;
        else                    lo = mid + 1;
    }
    auto found = get(lo);
    return (found && *found == target) ? lo : -1;
}
```

</TabItem>
</Tabs>

### Ternary search

Ternary search narrows toward the peak of a **unimodal** function by comparing two interior probes,
`m1` and `m2`, and discarding whichever outer third cannot contain the maximum:

<Figure src="/img/cs/algorithms/ternary-search-narrowing.png"
        alt="A downward parabola peaking near x=6, with four progressively narrower shaded bands showing the search interval shrinking toward the peak over four iterations"
        caption="Ternary search on a unimodal curve peaking at x = 6. Each iteration compares f(m1) against f(m2) and discards one outer third; the interval shrinks by a factor of 2/3 per step rather than binary search's 1/2." />

```text
f(x) = -(x-6)^2 + 30   on [lo, hi] = [0, 10]

iter 1: m1=3.33  m2=6.67   f(m1)=22.87  f(m2)=29.55   f(m2) > f(m1) -> peak is right of m1 -> lo = 3.33
iter 2: m1=5.56  m2=7.78   f(m1)=29.81  f(m2)=26.83   f(m1) > f(m2) -> peak is left of m2  -> hi = 7.78
iter 3: m1=4.81  m2=6.30   f(m1)=28.58  f(m2)=29.91   f(m2) > f(m1) -> peak is right of m1 -> lo = 4.81
iter 4: m1=5.80  m2=6.79   f(m1)=29.96  f(m2)=29.38   f(m1) > f(m2) -> peak is left of m2  -> hi = 6.79
```

Each iteration discards one third of the remaining range, so after $k$ iterations the range has shrunk
by $(2/3)^k$ — **O(log(range / ε)) iterations to reach precision ε**, a worse constant than binary
search's $(1/2)^k$ despite the similar shape, because ternary search needs *two* function evaluations
per iteration against binary search's one.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def ternary_search_max(f, lo, hi, iterations=100):
    """Argmax of a unimodal f on [lo, hi] — fixed iteration count, same reasoning as the float
    variant of binary search on the answer."""
    for _ in range(iterations):
        m1 = lo + (hi - lo) / 3
        m2 = hi - (hi - lo) / 3
        if f(m1) < f(m2):
            lo = m1
        else:
            hi = m2
    return (lo + hi) / 2
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
template <typename Func>
double ternary_search_max(Func f, double lo, double hi, int iterations = 100) {
    for (int i = 0; i < iterations; ++i) {
        double m1 = lo + (hi - lo) / 3;
        double m2 = hi - (hi - lo) / 3;
        if (f(m1) < f(m2)) lo = m1;
        else                hi = m2;
    }
    return (lo + hi) / 2;
}
```

</TabItem>
</Tabs>

```python showLineNumbers
# checked on the traced input and the ternary search above
assert exponential_search(lambda i: [1, 2, 4, 8, 16, 32, 64][i], 8) == 3
assert exponential_search(lambda i: [1, 2, 4, 8, 16, 32, 64][i], 5) == -1
peak = ternary_search_max(lambda x: -((x - 6) ** 2) + 30, 0.0, 10.0)
assert abs(peak - 6.0) < 1e-6
```

## Practical Usage

- **Why unimodality matters, and cannot be checked from inside the loop.** A function with two local
  maxima causes ternary search to converge on whichever one the first pair of probes happens to favour,
  silently discarding the other — there is no way to detect this from the sequence of `f` values alone.
  Verifying unimodality is a proof obligation before calling the function, exactly like verifying
  sortedness before ordinary binary search or monotonicity before
  [binary search on the answer](./binary-search-on-answer.md).
- **Binary search on the derivative usually beats ternary search outright.** If $f$ is differentiable,
  $f'$ is monotonic around the extremum (increasing then the sign flips, for a maximum), which is
  exactly the precondition for [binary search on the answer](./binary-search-on-answer.md) applied to
  "is $f'(x) \geq 0$" — one function evaluation per iteration instead of ternary search's two, for the
  same $O(\log(\text{range}/\varepsilon))$ iteration count. Sedgewick & Wayne's coverage of ternary
  search notes this trade-off directly: ternary search is the fallback for when a derivative is not
  available or not worth deriving, not the first choice when it is.
- **Exponential search's real use is unbounded data**, not sorted arrays whose length is already known
  — for a known-length array, plain binary search does the same job in fewer probes. It shows up when
  scanning a log stream for the first entry past a timestamp, or probing an external, paginated API
  that has no cheap "give me the length" call.
- **Interpolation search**, not covered in depth here, is a further refinement for uniformly distributed
  numeric data: instead of always probing the midpoint, it estimates where the target *should* be
  linearly between `lo` and `hi`'s values, achieving $O(\log \log n)$ average case (Sedgewick & Wayne,
  4th ed., §3.1 exercises) at the cost of a worst case that degrades to $O(n)$ on adversarial data.

## Edge Cases & Pitfalls

- **Doubling past the end of a truly finite sequence.** `safe_get`/`std::optional` above must treat
  "past the end" the same as "too large," or the doubling loop reads out of bounds instead of stopping.
- **Two flat plateaus at the same height defeat ternary search's comparison.** If `f(m1) == f(m2)`
  exactly, either branch is technically safe for a strictly unimodal function, but a function that is
  merely *non-decreasing then non-increasing* (a flat top) can have both probes land on the plateau with
  no information to act on — ternary search assumes strict unimodality, not the non-strict version.
- **Off-by-one in the doubling bound.** Searching `[lo, hi] = [bound/2, bound]` after doubling, rather
  than `[0, bound]`, is what keeps exponential search at $O(\log i)$ instead of re-scanning everything
  found so far — using the wrong lower bound silently degrades the complexity without breaking
  correctness.
- **Floating-point ternary search needs a fixed iteration count**, for the identical reason given in
  [Binary Search on the Answer](./binary-search-on-answer.md#practical-usage): `lo < hi` on doubles is
  not a reliable termination condition.

## Comparisons

| | Exponential search | Ternary search | Plain binary search |
|---|---|---|---|
| Needs `n` in advance | No | No (operates on a numeric range) | Yes (or an end sentinel) |
| Finds | An exact value | An extremum of a unimodal function | An exact value or boundary |
| Function evaluations per iteration | 1 (doubling) + $O(\log i)$ (binary phase) | 2 | 1 |
| Worst case | $O(\log i)$ | $O(\log(\text{range}/\varepsilon))$ | $O(\log n)$ |
| Prefer when | Length unknown or expensive to obtain | No derivative available for the function | Length known, array materialised |

## Recall

<Recall
  invariant="Exponential search finds the bracket [bound/2, bound] around the answer by doubling, then binary searches inside it — cost scales with the answer's position, not the data's total length. Ternary search discards one outer third per iteration by comparing two interior probes, which only works if the function is unimodal."
  costs={[
    ["exponential search, doubling phase (worst)", "O(log i)"],
    ["exponential search, total (worst)", "O(log i)"],
    ["ternary search, iterations for precision e", "O(log(range / e))"],
    ["ternary search, function evals per iteration", "2"],
  ]}
  reachFor="A sorted stream or unbounded sequence whose length is unknown (exponential); a unimodal function with no cheap derivative (ternary)."
  trap="Calling ternary search on a function that is not strictly unimodal — two peaks, or a flat top — converges silently on the wrong extremum with no way to detect the mistake from inside the loop."
/>

## References

- Bentley, J. L. & Yao, A. C.-C., "An Almost Optimal Algorithm for Unbounded Searching," *Information
  Processing Letters* 5(3), 1976 — the original exponential/galloping search and its optimality proof.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §3.1 "Symbol Tables" (exercises) — interpolation search's
  average and worst case, and ternary search versus derivative-based methods.
- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §9.3 — the selection
  problem's decrease-and-conquer structure, the same shape ternary search uses to discard a third of
  the range instead of a fixed fraction from one side.

## Related Pages

- [Binary Search](./binary-search.md) — the underlying halving step both algorithms specialise.
- [Binary Search on the Answer](./binary-search-on-answer.md) — the derivative-based alternative to
  ternary search, and the shared fixed-iteration stopping rule for floating-point ranges.
- [Recurrences & the Master Theorem](../complexity/recurrences-and-master-theorem.md) — why a $2/3$
  shrink factor and a $1/2$ shrink factor both resolve to a logarithm, just with different constants.
