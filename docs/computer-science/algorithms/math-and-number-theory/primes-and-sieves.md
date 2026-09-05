---
id: primes-and-sieves
title: Primes & Sieves
sidebar_label: Primes & Sieves
sidebar_position: 1
tags: [computer-science, algorithms, math, number-theory, primes]
---

# Primes & Sieves

Testing whether a single number `n` is prime is a small, self-contained problem: try dividing it by
every integer from 2 upward and stop as soon as one divides evenly, or as soon as trying further
cannot possibly find one. That second stopping rule is the entire trick, and it is easy to under-use:
a number `n` that has a factor `d` greater than sqrt(n) must also have a *partner* factor `n / d` that
is smaller than sqrt(n), because `d * (n / d) = n` and both factors cannot be on the large side at
once. So if no divisor up to sqrt(n) has been found, none exists at all — checking further is
provably wasted work. This turns an O(n) scan into an O(sqrt n) one, for free, just by knowing where
to stop.

That single-number test stops being the right tool the moment the question changes from "is this one
number prime" to "which of these many numbers are prime" — a factorization routine called in a loop,
a number-theoretic filter run over a whole range. Trial-dividing each of `n` numbers up to sqrt(n)
costs O(n · sqrt n) in total, and almost all of that work is repeated: the same small primes get
tested against nearly every candidate. A **sieve** inverts the direction of the computation — instead
of asking "is this number divisible by anything smaller", it starts from each small prime and crosses
out every multiple of it in one pass, so that whatever is left unmarked at the end must be prime by
construction, not by having survived a test.

## Core Concepts

| Term | Meaning |
|---|---|
| **Trial division** | Testing `n`'s primality by dividing it by every candidate up to `sqrt(n)` |
| **Sieve of Eratosthenes** | Cross out every multiple of each prime, starting from the prime itself, up to a bound `N` |
| **Linear sieve** | A sieve variant in which every composite is crossed out exactly once, by its smallest prime factor, giving O(N) total work |
| **Smallest prime factor (SPF) table** | `spf[i]` = the smallest prime dividing `i`, built alongside a sieve; repeatedly dividing by `spf[i]` factorizes `i` in O(log i) |

## Mechanism

<Figure src="/img/cs/algorithms/sieve-of-eratosthenes-animation.gif"
        alt="Animation of the sieve of Eratosthenes crossing out composite numbers on a numbered grid, starting from 2 and proceeding through each remaining prime"
        caption="The sieve of Eratosthenes: starting from each unmarked number, every multiple of it is crossed out, leaving only primes unmarked at the end."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Sieve_of_Eratosthenes_animation.gif" license="CC BY-SA 3.0" />

Trace input — sieving `2..30` (sqrt(30) is about 5.47, so the outer loop stops after 5, since any
composite `<= 30` must have a factor `<= 5`):

```text
start: 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
        all unmarked

cross out multiples of 2 (starting at 4, step 2):
  marked: 4 6 8 10 12 14 16 18 20 22 24 26 28 30
  remaining unmarked: 2 3 5 7 9 11 13 15 17 19 21 23 25 27 29

cross out multiples of 3 (starting at 9, step 3; 12,18,24,30 already marked):
  newly marked: 9 15 21 27
  remaining unmarked: 2 3 5 7 11 13 17 19 23 25 29

cross out multiples of 5 (starting at 25, step 5; 15,20,30 already marked):
  newly marked: 25
  remaining unmarked: 2 3 5 7 11 13 17 19 23 29

next prime would be 7, and 7 > sqrt(30) -- stop. Everything still unmarked is prime:
  2 3 5 7 11 13 17 19 23 29    (10 primes below 30)
```

Nothing above 5 ever needed its own pass: every composite `<= 30` has a prime factor `<= 5`, so the
three passes above already crossed out all of them. Sedgewick & Wayne, *Algorithms* 4th ed., §1.4,
and CLRS 4th ed. Ch. 31 both give the classic bound on the total work: each prime `p <= N` contributes
about `N / p` crossings, and summing `N / p` over all primes `p <= N` is `N * sum(1/p) = N * ln(ln N)
+ O(N)`, i.e. **O(N log log N)** — a function that grows barely faster than `N` for any practical `N`.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def sieve(n):
    """Primality up to n (inclusive), O(n log log n) worst case (Sedgewick & Wayne 4/e, s1.4)."""
    is_prime = [True] * (n + 1)
    is_prime[0:2] = [False, False]           # 0 and 1 are not prime by definition
    p = 2
    while p * p <= n:
        if is_prime[p]:
            for multiple in range(p * p, n + 1, p):   # smaller multiples already crossed by a smaller prime
                is_prime[multiple] = False
        p += 1
    return is_prime


def is_prime_trial_division(n):
    """O(sqrt n) worst case: no factor beyond sqrt(n) can exist without a partner below it."""
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cstdint>
#include <vector>

std::vector<bool> sieve(int n) {
    std::vector<bool> is_prime(n + 1, true);
    if (n >= 0) is_prime[0] = false;
    if (n >= 1) is_prime[1] = false;
    for (long long p = 2; p * p <= n; ++p) {
        if (is_prime[p]) {
            for (long long m = p * p; m <= n; m += p) is_prime[m] = false;
        }
    }
    return is_prime;
}

bool is_prime_trial_division(long long n) {
    if (n < 2) return false;
    for (long long d = 2; d * d <= n; ++d)
        if (n % d == 0) return false;
    return true;
}
```

</TabItem>
</Tabs>

### The linear sieve and the smallest-prime-factor table

The Sieve of Eratosthenes still crosses some composites more than once — 12 is crossed by both 2 and
3. The **linear sieve** fixes this by processing candidates in increasing order and, for each one,
crossing it out using *only its smallest prime factor*, stopping the inner loop the instant a prime
already found divides the current prime being multiplied — the exact condition that guarantees every
composite is marked exactly once, for O(N) total work instead of O(N log log N). The same pass
naturally builds a **smallest-prime-factor (SPF) table**: `spf[i]` for every composite `i` is already
known by the time the linear sieve finishes, and factorizing any `i <= N` afterwards is just
repeatedly dividing by `spf[i]` — at most `log2(i)` divisions, since each division at least halves
what remains, giving **O(log i)** factorization instead of O(sqrt i) trial division per query.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def linear_sieve(n):
    """Every composite crossed out exactly once, by its smallest prime factor -- O(n) worst case."""
    spf = [0] * (n + 1)               # spf[i] = smallest prime factor of i
    primes = []
    for i in range(2, n + 1):
        if spf[i] == 0:                # i has no smaller factor recorded yet -> i is prime
            spf[i] = i
            primes.append(i)
        for p in primes:
            if p > spf[i] or p * i > n:
                break                   # p would not be i*p's smallest factor, or out of range
            spf[p * i] = p
    return spf, primes


def factorize(n, spf):
    """O(log n) worst case: each step divides out one prime factor, at least halving n."""
    factors = []
    while n > 1:
        factors.append(spf[n])
        n //= spf[n]
    return factors
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
std::pair<std::vector<int>, std::vector<int>> linear_sieve(int n) {
    std::vector<int> spf(n + 1, 0);
    std::vector<int> primes;
    for (int i = 2; i <= n; ++i) {
        if (spf[i] == 0) { spf[i] = i; primes.push_back(i); }
        for (int p : primes) {
            if (p > spf[i] || 1LL * p * i > n) break;
            spf[p * i] = p;
        }
    }
    return {spf, primes};
}

std::vector<int> factorize(int n, const std::vector<int>& spf) {
    std::vector<int> factors;
    while (n > 1) { factors.push_back(spf[n]); n /= spf[n]; }
    return factors;
}
```

</TabItem>
</Tabs>

## Practical Usage

- **Python's [`sympy.isprime`](https://docs.sympy.org/latest/modules/ntheory.html#sympy.ntheory.primetest.isprime)**
  uses trial division for small `n` and switches to Miller-Rabin plus a BPSW check for large `n` —
  neither trial division nor a sieve is the right tool once `n` exceeds a sieve's practical memory.
- **Precompute once, query many times.** Any problem that repeatedly asks "is `k` prime" for many
  `k <= N` should sieve `[2, N]` once, in O(N log log N), rather than trial-dividing each query in
  O(sqrt k) — the same precompute-once trade
  [Prefix Sums & Difference Arrays](../problem-solving-patterns/prefix-sums-and-difference-arrays.md)
  makes for range sums.
- **Segmented sieving** sieves a range `[lo, hi]` using only primes up to `sqrt(hi)` (found by a small
  sieve first), keeping memory at O(hi - lo) instead of O(hi) — the standard technique once `hi` is
  too large to hold a full sieve array.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# both sieves and factorization, checked against the traced n=30 result
is_prime_30 = sieve(30)
assert [i for i in range(31) if is_prime_30[i]] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
assert all(is_prime_trial_division(i) == is_prime_30[i] for i in range(31))

spf, primes_30 = linear_sieve(30)
assert primes_30 == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
assert factorize(24, spf) == [2, 2, 2, 3]             # 24 = 2^3 * 3
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    auto is_prime_30 = sieve(30);
    std::vector<int> primes_found;
    for (int i = 0; i <= 30; ++i) if (is_prime_30[i]) primes_found.push_back(i);
    assert((primes_found == std::vector<int>{2, 3, 5, 7, 11, 13, 17, 19, 23, 29}));

    auto [spf, primes_30] = linear_sieve(30);
    assert((primes_30 == std::vector<int>{2, 3, 5, 7, 11, 13, 17, 19, 23, 29}));
    assert((factorize(24, spf) == std::vector<int>{2, 2, 2, 3}));
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Starting the inner crossing loop at `2*p` instead of `p*p`.** Every multiple of `p` smaller than
  `p*p` already has a smaller prime factor and was crossed out earlier; starting at `2*p` does not
  break correctness but wastes work that grows the effective constant factor noticeably at scale.
- **Trial-dividing by every integer instead of stopping the loop bound at sqrt(n).** Looping to `n`
  instead of to `sqrt(n)` is a correctness-preserving but O(n) instead of O(sqrt n) mistake — the
  kind of bug that only shows up as "why is this slow" under profiling, never as a wrong answer.
- **Forgetting 0 and 1 are not prime.** A sieve initialized to "all true" that never clears indices 0
  and 1 reports both as prime, which corrupts any factor count or product built on top of it.
- **Reusing a single-query trial-division check inside a loop over `N` candidates.** This is exactly
  the O(N · sqrt N) mistake a sieve exists to avoid — see the Mechanism section above.

## Comparisons

| | Per-query cost | Total for N queries | Extra space |
|---|---|---|---|
| Trial division, one number | O(sqrt n) worst | O(N * sqrt n) worst | O(1) |
| Sieve of Eratosthenes, precomputed | O(1) lookup after build | O(N log log N) worst | O(N) |
| Linear sieve, precomputed | O(1) lookup after build | O(N) worst | O(N) |
| Factorization via SPF table | O(log n) worst | O(N log N) worst (N factorizations) | O(N) |
| Factorization via trial division | O(sqrt n) worst | O(N * sqrt n) worst | O(1) |

A sieve only pays off when the range `[2, N]` is queried repeatedly; for a single one-off primality
check on a large `n`, trial division (or, past a few million, Miller-Rabin) needs no O(N) memory at
all.

## Recall

<Recall
  invariant="If n has no divisor up to sqrt(n), it has none at all -- any factor above sqrt(n) has a smaller partner factor, which is why every algorithm on this page stops its inner loop at sqrt(n) or at p*p, never at n."
  costs={[
    ["trial division, one number (worst)", "O(sqrt n)"],
    ["sieve of Eratosthenes, build up to N (worst)", "O(N log log N)"],
    ["linear sieve, build up to N (worst)", "O(N)"],
    ["primality lookup after either sieve (worst)", "O(1)"],
    ["factorization via smallest-prime-factor table (worst)", "O(log n)"],
  ]}
  reachFor="Many primality or factorization queries over the same bounded range -- precompute once with a sieve rather than trial-dividing each query."
  trap="Trial-dividing up to n instead of sqrt(n), or re-running a per-query primality test inside a loop over a whole range instead of sieving it once."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., Ch. 31 "Number-Theoretic
  Algorithms" — primality testing and the sieve's asymptotic analysis.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.4 "Analysis of Algorithms" — the sieve used as a
  worked example of the harmonic-sum analysis behind O(N log log N).
- [`sympy.ntheory.primetest.isprime`](https://docs.sympy.org/latest/modules/ntheory.html#sympy.ntheory.primetest.isprime) —
  the CPython-ecosystem library's own documentation of when it switches from trial division to
  probabilistic primality testing.

## Related Pages

- [Math & Number Theory](./intro.md) — the folder's map of where this arithmetic surfaces elsewhere.
- [GCD & Modular Arithmetic](./gcd-and-modular-arithmetic.md) — the next arithmetic building block,
  including modular exponentiation used by the probabilistic primality tests mentioned above.
- [Prefix Sums & Difference Arrays](../problem-solving-patterns/prefix-sums-and-difference-arrays.md) —
  the same precompute-once-query-many trade applied to range sums instead of primality.
- [Big-O Notation](../complexity/big-o-notation.md) — what "worst case" and the log log N growth rate
  actually mean.
