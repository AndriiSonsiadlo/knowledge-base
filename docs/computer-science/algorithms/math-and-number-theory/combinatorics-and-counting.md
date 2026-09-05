---
id: combinatorics-and-counting
title: Combinatorics & Counting
sidebar_label: Combinatorics & Counting
sidebar_position: 3
tags: [computer-science, algorithms, math, number-theory, combinatorics]
---

# Combinatorics & Counting

"How many ways" questions tempt a direct answer: generate every arrangement, every selection, every
outcome, and count them. That is always correct and often the wrong tool, because the count of
outcomes frequently grows exponentially even when the *number itself* has a short formula. Choosing
5 cards from a 52-card deck has C(52, 5) = 2,598,960 possible hands; generating and counting them one
by one wastes work a single formula answers instantly. Combinatorics is the set of tools for getting
the *count* without paying for the enumeration — a formula when one exists in closed form, a
recurrence built as a DP table when it does not, and an inclusion-exclusion argument when the
straightforward count double-counts something.

The same shift shows up in three specific tools this page covers. Permutations and combinations are
closed-form counts for ordering and selecting. Pascal's triangle turns "compute C(n, k)" into a table
built by addition alone, with no factorials and no risk of an intermediate overflowing before it is
divided back down. Inclusion-exclusion corrects a count that over-counts elements belonging to more
than one of several sets, by systematically adding and subtracting the overlaps. And the pigeonhole
principle is not a counting *algorithm* at all — it is a counting *argument*, used to prove existence
statements ("two of these must collide") without needing to say which two.

## Core Concepts

| Term | Meaning |
|---|---|
| **Permutation** | An ordered arrangement of `k` items from `n`; count is `P(n, k) = n! / (n - k)!` |
| **Combination** | An unordered selection of `k` items from `n`; count is `C(n, k) = n! / (k! * (n - k)!)` |
| **Pascal's triangle recurrence** | `C(n, k) = C(n-1, k-1) + C(n-1, k)` — choosing item `n` or not, with base cases `C(n, 0) = C(n, n) = 1` |
| **Inclusion-exclusion** | `\|A ∪ B\| = \|A\| + \|B\| - \|A ∩ B\|`, generalizing to any number of sets by alternating added and subtracted overlaps |
| **Pigeonhole principle** | Placing more than `n` items into `n` containers forces at least one container to hold more than one item |

## Mechanism

Trace input — `C(5, 2)`, computed both by the closed-form formula and by five rows of Pascal's
triangle, to confirm they agree.

**By formula:** `C(5, 2) = 5! / (2! * 3!) = 120 / (2 * 6) = 120 / 12 = 10`.

<Figure src="/img/cs/algorithms/pascals-triangle.png"
        alt="The first eight rows of Pascal's triangle with the C(5,2) entry highlighted, showing it as the sum of the two entries above it"
        caption="Pascal's triangle, rows 0 to 7: C(5,2) = 10, the sum of C(4,1) = 4 and C(4,2) = 6 directly above it."
        source="Generated for this page" href="" license="" />

**By the recurrence**, building row by row from `C(0,0) = 1`:

```text
row 0:             1
row 1:            1 1
row 2:           1 2 1
row 3:          1 3 3 1
row 4:         1 4 6 4 1
row 5:        1 5 10 10 5 1
                    ^
              C(5, 2) = 10  -- the 3rd entry (index 2) of row 5

Building C(5, 2) from the recurrence directly:
  C(4, 1) = C(3, 0) + C(3, 1) = 1 + 3 = 4
  C(4, 2) = C(3, 1) + C(3, 2) = 3 + 3 = 6
  C(5, 2) = C(4, 1) + C(4, 2) = 4 + 6 = 10      -- agrees with the formula
```

Both routes give 10, and the agreement is not a coincidence: Pascal's recurrence *is* the formula's
own identity `C(n,k) = C(n-1,k-1) + C(n-1,k)`, provable directly by splitting a choice of `k` from
`n` items into "the `n`-th item is included" (choose `k-1` more from the remaining `n-1`) and "the
`n`-th item is excluded" (choose `k` from the remaining `n-1`) — two disjoint cases that together
cover every selection exactly once.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
from math import comb, factorial, perm


def permutations_count(n, k):
    """P(n, k) = n! / (n - k)! -- ordered selections. O(k) with the loop form below."""
    result = 1
    for i in range(k):
        result *= (n - i)
    return result


def combinations_count(n, k):
    """C(n, k) = n! / (k! (n - k)!) -- unordered selections."""
    return permutations_count(n, k) // factorial(k)


def pascals_triangle(rows):
    """Builds C(n, k) for 0 <= n < rows via the DP recurrence -- no factorials, no overflow risk."""
    triangle = [[1]]
    for n in range(1, rows):
        prev = triangle[-1]
        row = [1] + [prev[k - 1] + prev[k] for k in range(1, n)] + [1]
        triangle.append(row)
    return triangle
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cstdint>
#include <vector>

long long permutations_count(int n, int k) {
    long long result = 1;
    for (int i = 0; i < k; ++i) result *= (n - i);
    return result;
}

long long factorial_ll(int k) {
    long long result = 1;
    for (int i = 2; i <= k; ++i) result *= i;
    return result;
}

long long combinations_count(int n, int k) {
    return permutations_count(n, k) / factorial_ll(k);
}

std::vector<std::vector<long long>> pascals_triangle(int rows) {
    std::vector<std::vector<long long>> triangle;
    triangle.push_back({1});
    for (int n = 1; n < rows; ++n) {
        std::vector<long long> row(n + 1, 1);
        for (int k = 1; k < n; ++k) row[k] = triangle.back()[k - 1] + triangle.back()[k];
        triangle.push_back(row);
    }
    return triangle;
}
```

</TabItem>
</Tabs>

## Practical Usage

- **Python's [`math.comb`](https://docs.python.org/3/library/math.html#math.comb) and
  [`math.perm`](https://docs.python.org/3/library/math.html#math.perm)** (both added in 3.8) compute
  exactly `combinations_count`/`permutations_count` above, in C, and should be preferred in real code;
  `pascals_triangle` earns its keep specifically when *every* `C(n, k)` up to some bound is needed at
  once, since building the whole table is cheaper than `rows^2` separate `math.comb` calls once
  intermediate factorials would otherwise be recomputed repeatedly.
- **Modular binomial coefficients.** When `n` is large and results must be taken modulo a prime `p`,
  factorials overflow long before `n!` fits any fixed-width integer — the standard fix precomputes
  factorials and their modular inverses mod `p` using
  [fast exponentiation](./gcd-and-modular-arithmetic.md), turning each `C(n, k) mod p` query into
  O(1) after an O(n) precompute.
- **Inclusion-exclusion in practice.** Counting integers up to `N` divisible by 2 or 3 is
  `N/2 + N/3 - N/6` (the last term removes double-counting multiples of 6) — the same pattern scales
  to any fixed number of divisibility conditions.
- **Pigeonhole as a proof tool.** Among any 13 people, two share a birth month (12 months, 13 people)
  — a one-line existence proof that requires no search to find *which* two.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# formula, recurrence, and stdlib agreement on the traced C(5, 2)
triangle = pascals_triangle(8)
assert triangle[5][2] == 10
assert combinations_count(5, 2) == 10
assert comb(5, 2) == 10                              # cross-checked against the stdlib
assert perm(5, 2) == permutations_count(5, 2) == 20   # P(5, 2) = 5*4 = 20

# inclusion-exclusion: multiples of 2 or 3 up to 30
n = 30
count = n // 2 + n // 3 - n // 6
assert count == len([x for x in range(1, n + 1) if x % 2 == 0 or x % 3 == 0])
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    auto triangle = pascals_triangle(8);
    assert(triangle[5][2] == 10);
    assert(combinations_count(5, 2) == 10);
    assert(permutations_count(5, 2) == 20);

    int n = 30;
    int count = n / 2 + n / 3 - n / 6;
    int brute = 0;
    for (int x = 1; x <= n; ++x) if (x % 2 == 0 || x % 3 == 0) ++brute;
    assert(count == brute);
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Computing `n!` directly for large `n`.** `factorial(k)` inside `combinations_count` overflows a
  fixed-width integer long before `n` gets large, even when the final `C(n, k)` is modest — dividing
  the permutation count by `k!` (as done above) keeps the intermediate `permutations_count(n, k)`
  smaller than `n!` itself, but for genuinely large `n` the DP recurrence or a modular formulation
  is the only safe option in a fixed-width language.
- **Forgetting inclusion-exclusion's overlap term.** Counting "divisible by 2" plus "divisible by 3"
  without subtracting "divisible by 6" double-counts every multiple of 6 — a classic silent
  overcount, not a crash.
- **Misapplying pigeonhole with the wrong container count.** The principle requires *strictly more*
  items than containers; "n items, n containers" proves nothing about a collision on its own.
- **Confusing permutations and combinations.** Using `P(n, k)` where order does not matter (or vice
  versa) is a factor-of-`k!` error that produces a plausible-looking wrong number rather than an
  obvious crash.

## Comparisons

| | Cost | When it applies |
|---|---|---|
| Closed-form `C(n, k)` / `P(n, k)` | O(k) worst | One or a few queries, `n` small enough that intermediates do not overflow |
| Pascal's triangle DP, full table | O(rows^2) worst | Every `C(n, k)` up to a bound needed at once |
| Modular `C(n, k)` via precomputed factorial inverses | O(n) precompute, O(1) per query | Large `n`, results needed modulo a prime |
| Brute-force enumeration | O(exponential) worst | Never, once a formula or recurrence exists — useful only to sanity-check one by hand |

The choice is almost always "closed form for a single query, DP table for many queries over a
bounded range" — the same precompute-once trade this folder's sieve page makes for primality.

## Recall

<Recall
  invariant="C(n, k) = C(n-1, k-1) + C(n-1, k): choosing item n or not splits every selection into two disjoint cases that together account for all of them -- the same identity underlies both the closed-form formula and the DP recurrence."
  costs={[
    ["P(n, k), closed form (worst)", "O(k)"],
    ["C(n, k), closed form (worst)", "O(k)"],
    ["Pascal's triangle, full table to row n (worst)", "O(n^2)"],
    ["C(n, k) mod p, after O(n) factorial precompute (worst)", "O(1)"],
    ["inclusion-exclusion over m sets (worst)", "O(2^m)"],
  ]}
  reachFor="A 'how many ways' question where the naive approach would enumerate every outcome to count it, and a formula or DP recurrence answers the same question without the enumeration."
  trap="Computing n! directly for large n and dividing back down -- the intermediate factorial overflows long before the final C(n, k) would have."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Appendix C "Counting and
  Probability" — permutations, combinations, and the binomial coefficient's properties.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §2.5 (dynamic programming context) — Pascal's triangle as
  a canonical small DP table, generalizable to larger counting recurrences.
- [`math.comb`, `math.perm`](https://docs.python.org/3/library/math.html#math.comb) — CPython's own
  documentation for the closed-form counts, including the 3.8 version note.

## Related Pages

- [Math & Number Theory](./intro.md) — the folder's map of where this arithmetic surfaces elsewhere.
- [GCD & Modular Arithmetic](./gcd-and-modular-arithmetic.md) — fast exponentiation, used to compute
  modular factorial inverses for large-`n` binomial coefficients.
- [Recurrences & the Master Theorem](../complexity/recurrences-and-master-theorem.md) — the general
  tool for analyzing a recurrence like Pascal's, beyond just evaluating it.
- [Randomized Algorithms & Sampling](./randomized-algorithms-and-sampling.md) — the next page,
  where counting arguments justify why a random choice behaves as expected on average.
