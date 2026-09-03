---
id: binary-search-on-answer
title: Binary Search on the Answer
sidebar_label: Binary Search on the Answer
sidebar_position: 3
tags: [computer-science, algorithms, searching, binary-search]
---

# Binary Search on the Answer

Every binary search so far has searched an array: a sorted sequence of values sitting in memory,
narrowed by comparing against a target. This page is about a different, more general use of the same
halving idea — searching a **range of candidate answers** that is never materialised as an array at
all.

The reframing is: stop thinking "where is the target in this array" and start thinking "what is the
smallest (or largest) value in this range for which some yes/no question is true, given that the
answer stays true once it becomes true." If a `feasible(x)` predicate is **monotonic** — false for
every value below some boundary, true for every value at or above it — the same half-open template from
[Binary Search](./binary-search.md) finds that boundary in $O(\log(\text{range}))$ calls to `feasible`,
regardless of how expensive the range itself would be to enumerate.

:::info[Prerequisites]
Read [Binary Search](./binary-search.md) first, specifically "the variant that matters more" — the
half-open first-true-index template. Everything here is that template with the array replaced by an
integer or floating-point range.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Answer space** | The range `[lo, hi]` of candidate answers being searched — never materialised, unlike an array |
| **Feasibility predicate** | `feasible(x)`: does candidate answer `x` satisfy the requirement? Must be monotonic in `x` |
| **Monotonic** | Once `feasible(x)` is true, `feasible(x')` is true for every `x' > x` (or the mirror, for a "largest feasible" search) — the property that makes binary search valid at all |
| **Capacity / rate problem** | The classic phrasing: "smallest resource that lets a fixed workload finish within a fixed budget" |
| **Fixed-iteration stopping rule** | For real-valued answer spaces, iterate a fixed number of times rather than comparing `hi - lo` to an epsilon |

## Mechanism

<Figure src="/img/cs/algorithms/predicate-step-function.png"
        alt="A step function over probed capacities from 3 to 14, red dots for infeasible capacities, green dots for feasible ones, jumping from 0 to 1 at capacity 5"
        caption="feasible(cap) for shipping [3, 1, 4, 1, 5] in 3 days: false below capacity 5, true from 5 upward. The predicate never returns to false once it turns true — that monotonicity is what licenses searching it with binary search." />

Minimum capacity to ship `[3, 1, 4, 1, 5]` within 3 days, loading packages onto a truck in order and
starting a new day whenever the next package would exceed the truck's capacity. The answer space is
`[max(weights), sum(weights)] = [5, 14]`; the trace below shows every probe:

```text
weights = [3, 1, 4, 1, 5]   days = 3
answer space: lo = max(weights) = 5, hi = sum(weights) = 14

lo=5  hi=14  mid=9   feasible(9)?  loads: [3,4,8,9]->4th pkg starts day2 [5]      needed=2 <= 3  True   -> hi=9
lo=5  hi=9   mid=7   feasible(7)?  loads: [3,4]->day2[4,5]->day3[5]              needed=3 <= 3  True   -> hi=7
lo=5  hi=7   mid=6   feasible(6)?  loads: [3,4]->day2[4,5]->day3[5]              needed=3 <= 3  True   -> hi=6
lo=5  hi=6   mid=5   feasible(5)?  loads: [3,4]->day2[4,5]->day3[5]              needed=3 <= 3  True   -> hi=5
lo=5  hi=5   loop ends (lo == hi) -> answer = 5
```

Every probe in this trace happens to be feasible, because the true boundary sits exactly at `lo`, the
absolute floor set by the heaviest single package — a capacity below 5 could never fit that package on
any day, so 5 is both the initial lower bound and the answer. `hi` does all the shrinking; `lo` never
moves. This is not a special case the algorithm needs to detect — the loop above narrows toward the
first feasible value regardless of where it actually lies in the range.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def min_capacity(weights, days):
    """Smallest truck capacity that ships weights, in order, within `days` days."""
    def feasible(cap):                  # monotonic: if cap works, cap + 1 works too
        needed, load = 1, 0
        for w in weights:
            if load + w > cap:
                needed, load = needed + 1, 0
            load += w
        return needed <= days

    lo, hi = max(weights), sum(weights)  # lo: below this, one package alone overflows
    while lo < hi:                       # hi: trivially feasible, everything in one day
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <cassert>
#include <numeric>
#include <vector>

int min_capacity(const std::vector<int>& weights, int days) {
    auto feasible = [&](int cap) {              // monotonic: if cap works, cap + 1 works too
        int needed = 1, load = 0;
        for (int w : weights) {
            if (load + w > cap) { ++needed; load = 0; }
            load += w;
        }
        return needed <= days;
    };

    int lo = *std::max_element(weights.begin(), weights.end());
    int hi = std::accumulate(weights.begin(), weights.end(), 0);
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (feasible(mid)) hi = mid;
        else               lo = mid + 1;
    }
    return lo;
}
```

</TabItem>
</Tabs>

For $n$ packages and an answer range of size $R = \text{sum}(weights) - \max(weights)$, each call to
`feasible` is **O(n) worst case**, and there are $O(\log R)$ calls, for a total of **O(n log R) worst
case** — turning an optimisation problem into a small number of cheap simulations, rather than trying
every capacity from `lo` to `hi` in a linear scan.

## Practical Usage

- **Capacity problems** — "smallest X that lets Y finish within Z" — are the most common phrasing:
  shipping capacity within a day count (above), minimum machine memory that lets a job finish within a
  time budget, minimum number of workers that finishes a task list by a deadline. The pattern is always
  the same feasibility check wrapped in the same template.
- **Rate problems** invert the direction slightly but stay monotonic. "Koko eating bananas" (find the
  minimum integer eating speed `k` such that `sum(ceil(pile / k) for pile in piles) <= h`) is the
  canonical example: `feasible(k)` gets *easier* to satisfy as `k` grows, so it is monotonic in exactly
  the same sense, and the same `lo, hi = 1, max(piles)` half-open search finds the minimum `k`.
- **The floating-point variant.** Some answer spaces are real-valued — minimum speed to arrive by a
  deadline, the smallest real threshold that separates two classes of measurements. `lo < hi` as a loop
  condition never terminates on floats, since there is always a representable value between two
  distinct doubles that are not already bit-identical. Two fixes exist; only one is a good habit:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def min_feasible_float(feasible, lo, hi, iterations=100):
    """Smallest x in [lo, hi] for which feasible(x) holds — fixed iteration count, not epsilon."""
    for _ in range(iterations):
        mid = lo + (hi - lo) / 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid
    return hi
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
template <typename Pred>
double min_feasible_float(Pred feasible, double lo, double hi, int iterations = 100) {
    for (int i = 0; i < iterations; ++i) {
        double mid = lo + (hi - lo) / 2;
        if (feasible(mid)) hi = mid;
        else               lo = mid;
    }
    return hi;
}
```

</TabItem>
</Tabs>

A **fixed iteration count**, not a comparison against an epsilon, is the stopping rule: 100 iterations
halve the initial range 100 times, which is far more precision than a `double`'s ~15-17 significant
decimal digits ([IEEE 754](https://en.wikipedia.org/wiki/IEEE_754), as implemented by the platform's
`double`) can even represent — the loop converges to machine precision long before it runs out of
iterations, and it is guaranteed to terminate no matter what `lo` and `hi` are.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# checked on the traced input, plus a float sanity check
assert min_capacity([3, 1, 4, 1, 5], 3) == 5      # the traced search
assert min_capacity([1, 2, 3, 4, 5], 5) == 5      # one package per day: capacity = heaviest
assert abs(min_feasible_float(lambda x: x * x >= 2, 0.0, 2.0) - 2 ** 0.5) < 1e-9
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert((min_capacity({3, 1, 4, 1, 5}, 3) == 5));
    assert((min_capacity({1, 2, 3, 4, 5}, 5) == 5));
    double root2 = min_feasible_float([](double x) { return x * x >= 2.0; }, 0.0, 2.0);
    assert(root2 > 1.41421356 && root2 < 1.41421357);
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **A non-monotonic predicate silently returns a wrong answer.** There is no check possible from
  inside the search — verifying monotonicity is the caller's responsibility, done once on paper before
  writing any code, exactly as sortedness is for ordinary binary search.
- **Choosing `lo` and `hi` incorrectly.** `lo` must be a value the predicate is guaranteed to reject (or
  the trivial boundary case, as in the ship example where `lo = max(weights)` is itself feasible), and
  `hi` must be a value it is guaranteed to accept. A wrong `hi` — too small — makes the search return an
  infeasible answer without any error.
- **Comparing floats with `lo < hi`.** As above, this either loops forever or terminates on an
  arbitrary rounding accident. Use the fixed iteration count.
- **An O(n) feasibility check inside an O(log R) outer loop is still O(n log R) total**, not O(log R) —
  a common estimation mistake when the check itself does real work per element.

## Comparisons

| | Binary search on an array | Binary search on the answer | Linear scan of the answer space |
|---|---|---|---|
| Per probe | $O(1)$ comparison | $O(\text{feasible})$, problem-dependent | $O(\text{feasible})$ |
| Probes (worst case) | $O(\log n)$ | $O(\log R)$ | $O(R)$ |
| Requires | Sorted array | Monotonic predicate | Monotonic predicate (unused) |
| Materialises the search space | Yes — the array | No — an implicit range | No |

The predicate cost usually dominates: for the shipping problem, `feasible` is $O(n)$, so the whole
search is $O(n \log R)$ against a linear scan's $O(nR)$ — the same logarithmic win ordinary binary
search gets over a linear scan of an array, just paid per probe instead of per comparison.

## Recall

<Recall
  invariant="If feasible(x) is monotonic in x — false, then true, never back to false — the boundary between the two regions can be found in O(log R) calls to feasible, without ever enumerating the answer range."
  costs={[
    ["binary search on an array, per lookup (worst)", "O(log n)"],
    ["binary search on the answer, probes (worst)", "O(log R)"],
    ["binary search on the answer, total, O(n) feasible (worst)", "O(n log R)"],
    ["fixed-iteration float search, iterations", "~100, independent of range"],
  ]}
  reachFor="A problem phrased as 'smallest/largest value for which some condition holds,' where checking one candidate value is cheap relative to trying every candidate."
  trap="Looping on `lo < hi` with floating-point bounds — there is no guarantee two doubles ever become bit-identical, so the loop can run forever. Iterate a fixed number of times instead."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §2.3 & Problem 2-4 —
  the general decrease-and-conquer argument this pattern specialises, applied to a monotone predicate.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.1 & §1.4 — binary search as a special case of searching
  over a totally ordered set, not specifically an array.
- [IEEE Standard for Floating-Point Arithmetic (IEEE 754)](https://ieeexplore.ieee.org/document/8766229)
  — why two doubles need not ever become bit-identical under repeated averaging, which is exactly why
  `lo < hi` does not reliably terminate on a real-valued answer space.

## Related Pages

- [Binary Search](./binary-search.md) — the half-open boundary template this page reuses on a range
  instead of an array.
- [Sorting Algorithms](../sorting/intro.md) — why the array form needs sorted data and this form does
  not need any data at all, only a predicate.
- [Two Pointers & Sliding Window](../problem-solving-patterns/two-pointers-and-sliding-window.md) —
  another technique that turns an O(n²) brute force into O(n) by exploiting monotonicity, in a
  different shape.
