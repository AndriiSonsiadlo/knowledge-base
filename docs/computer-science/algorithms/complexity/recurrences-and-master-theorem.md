---
id: recurrences-and-master-theorem
title: Recurrences & the Master Theorem
sidebar_label: Recurrences & the Master Theorem
sidebar_position: 4
tags: [computer-science, algorithms, complexity, recurrences, master-theorem]
---

# Recurrences & the Master Theorem

A recursive algorithm's cost is itself defined recursively — mergesort's cost on n elements is twice its
cost on n/2 elements, plus the Θ(n) merge. That self-reference is exact but not directly useful: nobody
reads Θ(n log n) off `T(n) = 2T(n/2) + Θ(n)` by eye. Solving a recurrence means turning that
self-referential definition into a closed form with no T on the right-hand side.

Two tools do this. A **recursion tree** makes the substitution visible: draw every recursive call as a
node, write the non-recursive work done at that node, and sum by level. It always works, but requires
summing a series, which can be fiddly. The **master theorem** shortcuts the same computation for the
common shape `T(n) = aT(n/b) + f(n)` by reducing the sum to one comparison, at the cost of only applying
to that shape. When a recurrence does not fit — non-constant coefficients, unequal subproblem sizes, a
subtractive rather than divisive step — the recursion tree, or the more general substitution method,
is what is left.

The comparison the master theorem makes is between two competing costs: `n^(log_b a)`, the total size of
all the leaves of the recursion tree combined, and `f(n)`, the work done per call outside the recursive
calls themselves. Whichever one dominates decides the total; a tie multiplies by a log factor.

## Core Concepts

| Term | Meaning |
|---|---|
| **a** | Number of subproblems per call |
| **b** | Factor each subproblem shrinks by (subproblem size = n/b) |
| **f(n)** | Work done outside the recursive calls — dividing, combining |
| **n^(log_b a)** | The "leaf cost" — total size of all leaves in the recursion tree |
| **Recursion tree** | Every call as a node, work-per-node written in, summed level by level |
| **Substitution method** | Guess a closed form, prove it by induction — the general fallback |

## Mechanism

<Figure src="/img/cs/algorithms/recursion-tree.png"
        alt="A recursion tree for mergesort with n = 8: root labelled n=8, splitting to two nodes n=4, four nodes n=2, eight leaves n=1, with the per-level work cn, cn, cn, cn written on the right, summing to Θ(n log n)"
        caption="Every level of the tree costs Θ(n) — half as many subproblems, each twice the size, cancels exactly. Four levels, four times Θ(n), and the level count is log₂n." />

### Building the tree by hand: mergesort, T(n) = 2T(n/2) + Θ(n)

```text
level 0:  n=8                              work = c·8   = 8c
level 1:  n=4      n=4                     work = 2·c·4 = 8c
level 2:  n=2  n=2  n=2  n=2                work = 4·c·2 = 8c
level 3:  n=1..n=1 (8 leaves)               work = 8·c·1 = 8c

levels = log2(8) = 3  →  4 levels total (0..3)
total work = 4 levels × 8c = Θ(n log n)
```

Each level costs the same, Θ(n) — twice as many subproblems, each half the size, and the product
`(number of subproblems) × (size of each)` stays n at every level. There are `log₂n` levels below the
root, so the total is `n` work repeated `log₂n` times: **Θ(n log n)**.

### The three master theorem cases, exact conditions

For `T(n) = aT(n/b) + f(n)` with `a ≥ 1` and `b > 1` constants, compare `f(n)` against `n^(log_b a)`:

| Case | Condition | Result |
|---|---|---|
| **1 — leaves dominate** | `f(n) = O(n^(log_b a − ε))` for some constant `ε > 0` | `T(n) = Θ(n^(log_b a))` |
| **2 — tie, log factor** | `f(n) = Θ(n^(log_b a) · logᵏ n)` for some constant `k ≥ 0` | `T(n) = Θ(n^(log_b a) · log^(k+1) n)` |
| **3 — top level dominates** | `f(n) = Ω(n^(log_b a + ε))` for `ε > 0`, **and** the regularity condition `a·f(n/b) ≤ c·f(n)` holds for some `c < 1` and all large `n` | `T(n) = Θ(f(n))` |

Case 1 needs a *polynomially* smaller `f(n)`, not merely asymptotically smaller — `f(n) = n^(log_b a) /
log n` fails case 1 despite being smaller, because the gap is only logarithmic, not polynomial. Case 3
additionally requires the regularity condition, which fails for functions that oscillate; without it the
recursive cost is not guaranteed to be dominated by the top level.

### Applying it: mergesort and Karatsuba

**Mergesort**, `T(n) = 2T(n/2) + Θ(n)`: `a = 2`, `b = 2`, so `n^(log_b a) = n^(log₂2) = n¹`. `f(n) = Θ(n)`
matches `n^(log_b a) · log⁰n` exactly — **case 2 with k = 0** — giving `T(n) = Θ(n log n)`, confirming
the tree above.

**Karatsuba multiplication**, `T(n) = 3T(n/2) + Θ(n)`: three half-size recursive multiplications instead
of the naive four, each with Θ(n) work to combine. `a = 3`, `b = 2`, so `n^(log_b a) = n^(log₂3) ≈
n^1.585`. `f(n) = Θ(n) = O(n^(1.585 − ε))` for, say, `ε = 0.5` — **case 1** — giving
`T(n) = Θ(n^log₂3) ≈ Θ(n^1.585)`, beating the naive `Θ(n²)` schoolbook algorithm.

**Binary search**, `T(n) = T(n/2) + Θ(1)`: only one subproblem, so `a = 1`, `b = 2`, and
`n^(log_b a) = n^(log₂1) = n⁰ = 1`. `f(n) = Θ(1) = Θ(n⁰ · log⁰n)` matches exactly — **case 2 with
k = 0** — giving `T(n) = Θ(log n)`, the familiar bound reached here from the same theorem rather than
by direct halving-argument.

### The substitution method, worked: confirming mergesort by induction

The master theorem is a shortcut; substitution is the general method it shortcuts. Guess
`T(n) ≤ c·n·log₂n` for mergesort's `T(n) = 2T(n/2) + n` (dropping the Θ's constant to a concrete `n`
for the arithmetic), then prove the guess by induction.

```text
inductive hypothesis: T(n/2) ≤ c·(n/2)·log₂(n/2), assumed true for smaller inputs

T(n) = 2T(n/2) + n
     ≤ 2 · c·(n/2)·log₂(n/2) + n            (substitute the hypothesis)
     = c·n·log₂(n/2) + n
     = c·n·(log₂n − 1) + n                  (log₂(n/2) = log₂n − 1)
     = c·n·log₂n − c·n + n
     = c·n·log₂n − n·(c − 1)
     ≤ c·n·log₂n                            (holds whenever c ≥ 1)

base case: T(1) = 0 ≤ c·1·log₂1 = 0  ✓ (log₂1 = 0, so c ≥ 1 is checked at the next base case, n = 2)
```

Picking any `c ≥ 1` and checking a small base case makes the induction go through, confirming
`T(n) = O(n log n)` — the same answer the master theorem's case 2 gave in one line. The trade is exactly
what the mechanism section promised: substitution needs a correct guess and an inductive proof;
the master theorem needs only that the recurrence matches its form.

### Where the theorem does not apply

`T(n) = 2T(n/2) + n/log n`: here `n^(log_b a) = n`, and `f(n) = n/log n` is asymptotically *smaller*
than n but not by a polynomial factor — no `ε > 0` makes `n/log n = O(n^(1−ε))`. This falls in the gap
between cases 1 and 2, and the master theorem gives no answer. (It can still be solved — by the
Akra–Bazzi method, a generalisation the master theorem is a special case of — but that is outside the
scope here.) Subtractive recurrences such as `T(n) = T(n−1) + Θ(n)` (insertion sort's shape) are outside
the theorem entirely, since it is not divisive; those are solved directly by summing the series.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import math


def leaf_cost_exponent(a, b):
    """n^(log_b a): the exponent that decides which master-theorem case applies."""
    return math.log(a) / math.log(b)


mergesort_exp = leaf_cost_exponent(2, 2)
karatsuba_exp = leaf_cost_exponent(3, 2)
assert abs(mergesort_exp - 1.0) < 1e-9          # f(n)=Θ(n) ties it — case 2
assert abs(karatsuba_exp - 1.5849625007) < 1e-6  # f(n)=Θ(n) is polynomially smaller — case 1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cmath>

double leaf_cost_exponent(double a, double b) {
    return std::log(a) / std::log(b);   // n^(log_b a)
}
```

</TabItem>
</Tabs>

## Practical Usage

Reach for the master theorem first on any balanced divide-and-conquer routine — it answers in one line
what a tree takes several. Reach for the recursion tree, or full substitution with induction, whenever
the recurrence has non-constant coefficients (randomised quickselect's expected recurrence), unequal
subproblem sizes, or extra additive terms the master theorem's exact form does not admit. CLRS's
"Akra–Bazzi" note and Sedgewick & Wayne's tree-based treatment are the two standard fallbacks once the
theorem does not apply.

## Edge Cases & Pitfalls

- **Skipping the polynomial-gap check.** "f(n) is asymptotically smaller, so case 1" is wrong unless
  the gap is polynomial (`n^(log_b a − ε)`) — a logarithmic gap, as in `n/log n` above, satisfies
  neither case 1 nor case 2.
- **Forgetting the regularity condition in case 3.** `f(n)` dominating is necessary but not sufficient;
  without `a·f(n/b) ≤ c·f(n)`, the top-level cost is not guaranteed to dominate the total.
- **Using the theorem on a non-matching shape.** `T(n) = T(n−1) + T(n−2) + Θ(1)` (naive Fibonacci) is
  additive-subtractive, not divisive — the master theorem gives no answer, and the correct closed form
  (Θ(φⁿ)) comes from solving the linear recurrence directly, not from this theorem.
- **Treating `a` or `b` as non-constant.** Randomised quickselect's recurrence has a subproblem size
  that varies with the pivot, which is why its bound needs an expectation argument, not a direct
  master-theorem application.

## Comparisons

| Method | Handles | Effort | Gives no answer when |
|---|---|---|---|
| Master theorem | `T(n) = aT(n/b) + f(n)`, constant a, b | O(1) comparison | Polynomial gap missing, or regularity fails |
| Recursion tree | Any recursive shape, drawn by hand | Sum a series per level | Series has no closed form (rare) |
| Substitution (induction) | Any recursive shape | Guess + prove, most general | Never — but requires a correct guess |
| Akra–Bazzi | Multiple terms, `T(n) = Σ aᵢT(n/bᵢ) + f(n)` | Evaluate one integral | Almost never, but is heavier machinery |

## Recall

<Recall
  invariant="T(n) = aT(n/b) + f(n) describes a subdivided a-way recursion; its closed form is decided by comparing f(n), the work done outside the recursive calls, against n^(log_b a), the cost of the leaves."
  costs={[
    ["mergesort, T(n) = 2T(n/2) + Θ(n) (worst)", "Θ(n log n)"],
    ["binary search, T(n) = T(n/2) + Θ(1) (worst)", "Θ(log n)"],
    ["Karatsuba multiplication, T(n) = 3T(n/2) + Θ(n) (worst)", "Θ(n^log₂3) ≈ Θ(n^1.585)"],
    ["naive recursive Fibonacci, T(n) = T(n−1) + T(n−2) + Θ(1) (worst)", "Θ(φⁿ)"],
    ["master theorem substitution check (per candidate)", "O(1) per level, O(log_b n) levels"],
  ]}
  reachFor="Any divide-and-conquer algorithm, or any recursive function whose cost you need in closed form rather than by tracing calls one at a time."
  trap="Applying the master theorem when the polynomial gap between f(n) and n^(log_b a) is not strict, or when the recursion is not of the exact form aT(n/b) + f(n) — a/b non-constant, unequal subproblem sizes, or a subtractive recurrence like T(n−1) all fall outside it."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 4 — "Divide-and-Conquer",
  the master theorem's three cases with full proof, plus the recursion-tree and substitution methods.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.2 — mergesort, with the recursion-tree argument applied
  directly to its Θ(n log n) bound.
- Karatsuba, A. & Ofman, Y. (1962) — the original T(n) = 3T(n/2) + Θ(n) multiplication algorithm this
  page worked through.

## Related Pages

- [Amortized Analysis](./amortized-analysis.md) — the other major tool for bounding cost, used when the
  expense is spread over a sequence of calls rather than one recursive call tree.
- [Mergesort](../sorting/mergesort.md) — the algorithm behind this page's worked recursion tree.
- [Common Complexities](./common-complexities.md) — where Θ(n log n) sits among the growth classes met
  most often, including the comparison-sort lower bound this recurrence achieves.
- [Cheat Sheet](./cheat-sheet.md) — a decision flow for picking loop counting, recursion tree, master
  theorem, or amortized analysis on a new problem.
