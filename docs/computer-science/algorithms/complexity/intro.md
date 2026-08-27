---
id: complexity-intro
title: Complexity & Analysis — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, complexity, big-o]
---

# Complexity & Analysis — Overview

<Recall
  invariant="Complexity describes how work grows as input grows, not how long a specific run took on a specific machine."
  costs={[
    ["counting statements executed (worst)", "exact, but ties the count to one implementation"],
    ["counting abstract operations (worst)", "portable across implementations, still exact"],
    ["asymptotic class (worst)", "O(n) — survives changes in hardware, language, constant factors"],
  ]}
  reachFor="Comparing two approaches before writing either, or explaining why one already-working piece of code is slow at scale."
  trap="Timing one run on one machine and treating the number as the algorithm's complexity — a faster laptop or a warmer cache changes the timing without changing the growth rate."
/>

Measuring an algorithm by timing it tells you about your laptop, your compiler, your input, and the
background processes competing with you. **Complexity analysis** asks a different question — how does
the work grow as the input grows? — and answers it in a way that survives all four.

That is the whole trade. You give up knowing whether something takes 3 ms or 30 ms, and in exchange
you learn whether doubling the input doubles the time or quadruples it. For deciding between two
approaches before writing either, the second answer is far more useful. It is also durable: the
asymptotic class of an algorithm does not change when it is ported to a faster machine, rewritten in a
different language, or run on a warmer cache — only the constant factor does.

## Best, average and worst case

The same algorithm can have different costs depending on which input of size n it is given, so every
complexity claim on this site is qualified with a **case**:

| Case | Question it answers | Example |
|---|---|---|
| **Best** | The cheapest input of size n | Linear search finds the target in the first slot |
| **Average** | The expected cost over a distribution of inputs | Linear search finds the target halfway through, on average, over random position |
| **Worst** | The most expensive input of size n | Linear search never finds the target — scans everything |

Quoting a bound without its case is the single most common error in this material: "insertion sort is
O(n)" is true only in the best case (an already-sorted array) and false in general — its worst case is
O(n²). A bare "O(n)" with no case attached should be read as suspicious, not authoritative.

## In This Section

- **[Big-O Notation](./big-o-notation.md)** — what the notation actually asserts, the formal ∃c, n₀
  definition, and how O relates to Ω, Θ, o and ω.
- **[Common Complexities](./common-complexities.md)** — the growth classes you will actually meet, one
  named algorithm per class, and what a given n costs at realistic hardware speeds.
- **[Amortized Analysis](./amortized-analysis.md)** — bounding the average cost per operation over any
  sequence, for structures like a dynamic array where most operations are cheap and a few are not.
- **[Recurrences & the Master Theorem](./recurrences-and-master-theorem.md)** — solving the equations
  that describe divide-and-conquer cost, from `T(n) = 2T(n/2) + O(n)` to a closed form.
- **[Space Complexity](./space-complexity.md)** — the same asymptotic language applied to memory,
  including the stack cost recursion is easy to forget.
- **[P, NP & Intractability](./p-np-and-intractability.md)** — the boundary between "slow" and
  "no known efficient algorithm at all", and why the distinction matters in practice.
- **[Cheat Sheet](./cheat-sheet.md)** — every bound in this folder on one page, for lookup rather than
  learning.

## Three ways to count the same loop

Consider a linear scan that finds the maximum of an array:

```text
def find_max(a):
    best = a[0]              # 1 assignment
    for x in a[1:]:           # n - 1 iterations
        if x > best:          # n - 1 comparisons
            best = x           # 0 to n - 1 assignments
    return best
```

**Counting statements** (tied to this exact code): 1 initial assignment, `n - 1` loop tests, `n - 1`
comparisons, up to `n - 1` conditional assignments, 1 return. Worst case (a strictly increasing array)
totals `3n - 2` statement executions — a number that changes if the code is rewritten to use `enumerate`
or a different loop construct, even though the algorithm is unchanged.

**Counting abstract operations** (one level up): the algorithm does exactly one comparison per
remaining element, `n - 1` comparisons total, regardless of how those comparisons are written in source
code. This is more portable than counting statements, but still an exact number.

**Counting asymptotically**: `n - 1` comparisons is `O(n)` — worst case, and in fact best and average
case too, since every element must be examined at least once to be sure none is larger. The exact
constant (`n - 1` versus `n` versus `3n - 2`) stops mattering; what survives is that the cost is
linear in the input size.

All three counts describe the same loop truthfully. Only the third one is still true after the loop is
rewritten, ported, or run on different hardware — which is why complexity analysis works in the third
currency and not the first.

`find_max` also happens to have identical best, average and worst-case cost — every element must be
inspected once regardless of the values involved, so there is only one curve to draw. That is the
exception rather than the rule: most of the algorithms in this section have a best case that looks
nothing like their worst case, which is why the case is written next to every bound in the rest of
this folder rather than assumed.

## Estimating complexity without proving it

Deriving a bound formally is not always the first step — often it is faster to estimate the exponent
empirically and confirm it later. The **doubling ratio test** runs the code at sizes n, 2n, 4n, … and
looks at how the running time scales:

```text
n        time (s)    ratio to previous
1,000    0.012       —
2,000    0.048       4.0
4,000    0.19        4.0
8,000    0.76        4.0
```

A ratio that settles near `2^b` as n doubles is evidence of `O(n^b)` — a steady ratio of 4 here points
at quadratic, of 2 at linear, of roughly 1 at logarithmic. This is only a diagnostic, not a proof: it
can be fooled by an algorithm whose behaviour changes past the sizes tested, and it says nothing about
best or worst case unless the inputs driving each run are chosen to hit that case deliberately. It is,
however, the fastest way to sanity-check a bound derived by hand, or to get a first estimate for code
whose structure is too tangled to read off directly.

## Why It Matters

<Figure src="/img/cs/algorithms/complexity-growth-rates.png"
        alt="Eight growth curves on shared axes — 1, log₂n, √n, n, n log₂n, n², 2ⁿ and n! — where the last three climb almost vertically within the first ten inputs while the first three stay nearly flat across all one hundred"
        caption="All eight on the same axes, for n up to 100. n², 2ⁿ and n! have already left the chart before n = 10; log₂ n has not reached 7 by n = 100. No amount of micro-optimisation moves a program between these curves."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Comparison_computational_complexity.svg"
        license="CC BY-SA 4.0" />

A concrete version of that picture — operations performed, at one billion operations per second:

| n | O(log n) | O(n) | O(n log n) | O(n²) | O(2ⁿ) |
|---|---|---|---|---|---|
| 10 | 3 | 10 | 33 | 100 | 1,024 |
| 1,000 | 10 | 1,000 | ~10,000 | 1,000,000 | *heat death* |
| 1,000,000 | 20 | 1,000,000 | ~20,000,000 | 10¹² (~17 min) | — |
| 1,000,000,000 | 30 | 10⁹ (~1 s) | ~3×10¹⁰ (~30 s) | 10¹⁸ (~32 years) | — |

The lesson is not that O(n²) is forbidden — for n = 100 it is entirely fine and often the simplest
correct code, worst case included. The lesson is that the input size decides, and that the decision
changes character somewhere around n = 10,000.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 2 — "Getting Started",
  which introduces the statement-counting model this page's trace works through before moving to
  asymptotic notation.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.4 — "Analysis of Algorithms" — the same idea from a
  more empirical angle, measuring real running times alongside the theoretical model.

## Related Pages

- [Big-O Notation](./big-o-notation.md) — the formal definition behind the asymptotic column above.
- [Common Complexities](./common-complexities.md) — a named algorithm for each growth class.
- [Sorting Algorithms](../sorting/intro.md) — the classic worked example of an O(n²) versus O(n log n) choice.
- [Data Structures](../data-structures/intro.md) — every structure is a set of complexity trade-offs made concrete.
