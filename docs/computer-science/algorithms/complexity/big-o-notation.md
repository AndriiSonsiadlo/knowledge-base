---
id: big-o-notation
title: Big-O Notation
sidebar_label: Big-O Notation
sidebar_position: 1
tags: [computer-science, algorithms, complexity, big-o]
---

# Big-O Notation

Big-O describes an **upper bound on growth**. Saying an algorithm is $O(n^2)$ claims that beyond some
input size, its cost is at most a constant multiple of $n^2$ — never that it *is* $n^2$, and never anything
at all about small inputs.

That "beyond some input size" clause is the part most explanations skip, and it is the part that makes
the notation work. It is what licenses throwing away constants and lower-order terms, because for
large enough n those genuinely stop mattering.

## Core Concepts

| Term | Meaning | Everyday reading |
|---|---|---|
| **$O(f)$** | Grows *no faster than* f | Upper bound — "at worst this" |
| **$Ω(f)$** | Grows *no slower than* f | Lower bound — "at best this" |
| **$Θ(f)$** | Bounded above *and* below by f | Tight bound — "exactly this rate" |
| **$o(f)$** | Grows *strictly slower* than f | Strict upper bound — never touches f itself |
| **$ω(f)$** | Grows *strictly faster* than f | Strict lower bound — never touches f itself |

$O$ and $Ω$ allow equality with $c \cdot g(n)$ in the limit; $o$ and $ω$ forbid it — $n = o(n^2)$ is true,
$n^2 = o(n^2)$ is false. $Θ$ is the conjunction $O \cap Ω$: a function is $Θ(g)$ exactly when it is both $O(g)$
and $Ω(g)$ for the same g.

Informal usage almost always says "O" where "Θ" is meant. Saying mergesort is $O(n \log n)$ is true but
weak — it is also $O(n^3)$, since that is a valid upper bound too. Saying mergesort is $Θ(n \log n)$ is the
stronger, more useful claim. In practice, when someone says "quicksort is $O(n \log n)$ on average",
read Θ.

## Mechanism

### The formal definition, and what it is doing

$f(n) = O(g(n))$ means: there exist positive constants `c` and $n_0$ such that for all $n \geq n_0$,

```text
f(n) ≤ c · g(n)
```

<Figure src="/img/cs/algorithms/big-o-definition.png"
        alt="Two curves plotted together: f of n and c times g of n, crossing at a point marked x-nought, after which c times g of n stays above f of n"
        caption="Beyond the crossover point (x₀), c·g(n) stays above f(n) forever. Everything to the left of it is explicitly outside the claim."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Big-O-notation.png"
        license="Public domain" />

The two knobs are what make the abstraction useful. Because you may pick **any** constant `c`, a
factor of 100 in speed cannot change the classification. Because you may pick **any** starting point
$n_0$, behaviour on small inputs cannot change it either.

### Why constants and lower-order terms vanish

Given $f(n) = 3n^2 + 500n + 90000$:

| n | 3$n^2$ | 500n | 90000 | Which dominates |
|---|---|---|---|---|
| 10 | 300 | 5,000 | 90,000 | the constant |
| 100 | 30,000 | 50,000 | 90,000 | still the constant |
| 1,000 | 3,000,000 | 500,000 | 90,000 | $n^2$ |
| 100,000 | $3 \times 10^{10}$ | $5 \times 10^7$ | 90,000 | $n^2$, overwhelmingly |

So $f(n) = O(n^2)$. The other terms are not *wrong*, they simply stop being the story. Note also that
at n = 100 this function is dominated by a constant — a real reminder that asymptotic claims say
nothing about the range you might actually be operating in.

There are two situations where dropping the constant genuinely misleads:

- **Small n.** The table above shows it directly — up to n ≈ 500 the constant term `90000` outweighs
  the quadratic term, so an "O(n²)" label predicts nothing useful about behaviour in that range.
- **A huge constant hidden inside a low-order term.** An `O(1)` step that is implemented as a lookup
  into a 10 MB table pays for a cache miss on essentially every call — the asymptotic class says
  "constant", but the constant is a full round trip to main memory, not a register read. Two O(1)
  algorithms with wildly different real constants are not interchangeable just because the notation
  puts them in the same class.

### Verifying a bound directly

Proving `3n² + 5n + 2 = O(n²)` means exhibiting a `c` and an `n₀` that make the formal definition hold:

```text
claim:  3n² + 5n + 2 ≤ c · n²   for all n ≥ n₀

try n₀ = 1, and bound each term by n² for n ≥ 1:
  5n  ≤ 5n²      (since n ≤ n² when n ≥ 1)
  2   ≤ 2n²      (since 1 ≤ n² when n ≥ 1)

so  3n² + 5n + 2  ≤  3n² + 5n² + 2n²  =  10n²   for all n ≥ 1

check n = 1:  3 + 5 + 2 = 10   ≤  10 · 1 = 10    ✓ (equality, the tightest case)
check n = 5:  75 + 25 + 2 = 102  ≤  10 · 25 = 250  ✓

c = 10, n₀ = 1 satisfy the definition, so 3n² + 5n + 2 = O(n²).
```

The choice of `c = 10, n₀ = 1` is not unique — a smaller `c` also works provided `n₀` moves out to
compensate: `c = 4, n₀ = 6` clears every n from 6 onward (`3·36 + 5·6 + 2 = 140 ≤ 4·36 = 144`), even
though it fails at n = 3. Any pair that clears every n from `n₀` onward is a valid proof; the
definition asks for existence, not for the tightest possible constants.

### Reading complexity off code

The mechanical rules cover most cases:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# O(1) — the work does not depend on n
def first(items):
    return items[0]

# O(n) — one pass
def total(items):
    acc = 0
    for x in items:          # n iterations
        acc += x             # O(1) each
    return acc

# O(n²) — nested loops over the same input
def has_duplicate(items):
    for i in range(len(items)):          # n
        for j in range(i + 1, len(items)):  # up to n
            if items[i] == items[j]:
                return True
    return False

# O(log n) — the search space halves each step
def count_halvings(n):
    steps = 0
    while n > 1:
        n //= 2
        steps += 1
    return steps


assert first([5, 1, 8, 3]) == 5
assert total([5, 1, 8, 3]) == 17
assert has_duplicate([5, 1, 8, 3]) is False
assert has_duplicate([5, 1, 8, 5]) is True
assert count_halvings(1_000_000) == 19            # floor(log2(1_000_000)) divisions to reach 1
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cstddef>
#include <vector>

// O(1) — the work does not depend on n
int first(const std::vector<int>& items) {
    return items[0];
}

// O(n) — one pass
long long total(const std::vector<int>& items) {
    long long acc = 0;
    for (int x : items)      // n iterations
        acc += x;            // O(1) each
    return acc;
}

// O(n²) — nested loops over the same input
bool has_duplicate(const std::vector<int>& items) {
    for (std::size_t i = 0; i < items.size(); ++i)             // n
        for (std::size_t j = i + 1; j < items.size(); ++j)     // up to n
            if (items[i] == items[j]) return true;
    return false;
}

// O(log n) — the search space halves each step
int count_halvings(int n) {
    int steps = 0;
    while (n > 1) {
        n /= 2;
        ++steps;
    }
    return steps;
}
```

</TabItem>
</Tabs>

- **Sequential blocks add**, and the larger wins: $O(n) + O(n^2) = O(n^2)$.
- **Nested loops multiply**: a loop of n containing a loop of m is $O(n \cdot m)$.
- **Halving (or doubling) the problem each step is logarithmic** — that is what a logarithm counts.

## Edge Cases & Pitfalls

:::danger[The variable you dropped is still in there]
$O(n)$ is meaningless until you say what n counts. Two common traps:

- **Two different inputs.** Comparing every element of one list against another is $O(n \cdot m)$, not
  $O(n^2)$ — and if m is tiny and fixed, it is effectively $O(n)$.
- **Cost per operation.** Summing a list of integers is $O(n)$. Concatenating a list of *strings*
  with `+=` in a loop is $O(n^2)$, because each concatenation copies everything accumulated so far.
  The loop looks identical; the per-iteration cost is not $O(1)$.
:::

- **$O(n^2)$ is not always worse than $O(n \log n)$.** With a large constant hidden inside, the
  "better" algorithm can lose on real input sizes. This is exactly why production sorts switch to
  insertion sort below a threshold of ~16 elements.
- **Best/average/worst are separate questions from O/Ω/Θ**, though the two are constantly conflated.
  You can state a Θ bound on the worst case, or an O bound on the average case; the notation and the
  case being analysed are independent choices.
- **Amortized is not average.** See [Amortized Analysis](./amortized-analysis.md) — an amortized
  bound is a guarantee over any sequence of operations, not a probabilistic statement.

## Comparisons

| Claim | Says | Does not say |
|---|---|---|
| "Quicksort is $O(n^2)$" | Its worst case is quadratic | Anything about the typical case, which is n log n |
| "Lookup is $O(1)$" | Cost does not grow with the collection | That it is fast — a hash may be expensive |
| "This is faster, it's $O(n)$ not $O(n \log n)$" | It scales better | That it wins at your n |

## Recall

<Recall
  invariant="f(n) = O(g(n)) holds when some constant c and threshold n₀ make f(n) ≤ c·g(n) for every n ≥ n₀ — a claim about large n only, never about all n."
  costs={[
    ["O(f) — upper bound", "grows no faster than f"],
    ["Ω(f) — lower bound", "grows no slower than f"],
    ["Θ(f) — tight bound", "bounded above and below by f"],
    ["o(f) — strict upper bound", "grows strictly slower than f"],
    ["ω(f) — strict lower bound", "grows strictly faster than f"],
  ]}
  reachFor="Stating how an algorithm's cost scales in a way that survives a change of hardware, language, or constant factor."
  trap="Dropping constants unconditionally. At small n, or when the constant is itself huge (a 10 MB lookup table hidden inside an O(1) step), the dropped term is the one that decides the real running time."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, Ch. 3 — "Characterizing Running Times", the formal treatment of O, Ω and Θ.
- Knuth, *The Art of Computer Programming*, Vol. 1, §1.2.11 — the origin of the notation's use in this field.

### Books & Videos

- [Big-O Cheat Sheet](https://www.bigocheatsheet.com/) — complexity tables for the common structures and sorts, useful as a lookup rather than a lesson.

## Related Pages

- [Common Complexities](./common-complexities.md) — a named algorithm for each growth class, and what a given n costs at realistic hardware speeds.
- [Sorting Algorithms](../sorting/intro.md) — where these bounds get their most familiar workout.
