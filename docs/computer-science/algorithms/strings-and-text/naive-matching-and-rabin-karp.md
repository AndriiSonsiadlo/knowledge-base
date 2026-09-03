---
id: naive-matching-and-rabin-karp
title: Naive Matching & Rabin-Karp
sidebar_label: Naive Matching & Rabin-Karp
sidebar_position: 2
tags: [computer-science, algorithms, strings, pattern-matching, hashing]
---

# Naive Matching & Rabin-Karp

The obvious way to find a pattern of length m inside a text of length n is to try it at every
position: slide the pattern one character at a time, and at each position compare character by
character until either the pattern matches or a mismatch is found. This is correct, it is O(1)
extra space, and on ordinary text it is close to O(n) in practice because most mismatches happen on
the first or second character. The problem is the phrase "on ordinary text" — the naive scan has no
mechanism that prevents an adversarial or merely repetitive input from forcing every single
alignment to do the full m comparisons, and when that happens the bound is not O(n), it is O(nm).

Rabin-Karp attacks the same problem from a different angle: instead of comparing characters, compare
a **hash** of the m-character window to the hash of the pattern. Computing a hash from scratch is
itself O(m), which would be no better than the naive scan — the trick that makes it worthwhile is a
**rolling hash**, an arithmetic update that turns "the hash of the next window" into an O(1)
computation from "the hash of this window", so the whole scan costs O(n) hash updates plus O(1)
verification per position that actually matches.

:::info[Prerequisites]
[String Fundamentals](./string-fundamentals.md) for why a naive `==` between an m-character window
and the pattern already costs O(m) even before any looping starts.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Alignment** | One trial position of the pattern against the text; there are `n - m + 1` of them |
| **Rolling hash** | A hash function `h` for which `h(s[i+1..i+m])` can be computed from `h(s[i..i+m-1])` in O(1), instead of recomputing from scratch |
| **Polynomial hash** | `h(s) = (s[0]*B^(m-1) + s[1]*B^(m-2) + ... + s[m-1]) mod P`, for a base B and modulus P — the standard rolling hash |
| **Spurious hit** | Two different windows whose hashes collide by chance; must be verified with a real character comparison before being reported as a match |
| **Verify-on-hit** | The rule that a hash match is a *candidate*, never a confirmed match, until the characters themselves are compared |

## Mechanism

### The naive scan, and the input that breaks it

Trace input — the shared string-matching pair `text = abacabadabacaba`, `pattern = abacaba` (m = 7,
n = 15, 9 alignments):

```text
alignment   window     comparisons   result
0           abacaba    7             match (full pattern)
1           bacabad    1             mismatch at pattern[0]
2           acabada    2             mismatch at pattern[1]
3           cabadab    1             mismatch at pattern[0]
4           abadaba    4             mismatch at pattern[3]
5           badabac    1             mismatch at pattern[0]
6           adabaca    2             mismatch at pattern[1]
7           dabacab    1             mismatch at pattern[0]
8           abacaba    7             match (full pattern)
                                     total: 26 comparisons (n*m upper bound is 105)
```

This input is *friendly* to the naive scan — most alignments fail on the first or second character,
because the alphabet has variety. Compare that with a pattern and text built to defeat exactly that
shortcut: `text = "aaaaaaaab"` (eight `a`s then `b`), `pattern = "aaab"` (m = 4, n = 9, 6 alignments):

```text
alignment   window   comparisons   result
0           aaaa     4             mismatch at pattern[3] ('a' in text vs 'b' in pattern)
1           aaaa     4             mismatch at pattern[3]
2           aaaa     4             mismatch at pattern[3]
3           aaaa     4             mismatch at pattern[3]
4           aaaa     4             mismatch at pattern[3]
5           aaab     4             match (full pattern)
                                   total: 24 comparisons -- exactly (n-m+1)*m, the O(nm) bound realised
```

Every alignment here does the full m comparisons before failing (or succeeding), because the first
`m - 1` characters of the pattern match a run of `a`s that the text has in abundance. This is not a
contrived edge case a real system never sees — DNA sequences over a 4-letter alphabet and any
text with long repeated runs hit it routinely, which is exactly why a guaranteed bound matters.

### The rolling hash, derived

Treat the m characters of a window as digits of a base-B number and hash it mod a prime P:
`h(s[i..i+m-1]) = (s[i]*B^(m-1) + s[i+1]*B^(m-2) + ... + s[i+m-1]) mod P`. Sliding the window by one
removes the leading digit `s[i]*B^(m-1)` and appends a new trailing digit `s[i+m]`:

```text
h(s[i+1..i+m]) = ( (h(s[i..i+m-1]) - s[i]*B^(m-1)) * B + s[i+m] ) mod P
                    \_____________  remove leading digit  _____________/   \_ shift up, add new digit _/
```

`B^(m-1) mod P` is precomputed once before the scan starts, so each slide is one subtraction, one
multiplication, one addition, and two modulo operations — O(1) independent of m.

<Figure src="/img/cs/algorithms/rolling-hash-window.png"
        alt="Three panels showing the seven-character window sliding by one position across the text abacabadabacaba, with the removed leading character and added trailing character annotated in the hash update formula"
        caption="Rolling hash windows 0 to 2 over abacabadabacaba (pattern abacaba, m=7): each slide drops the leftmost character's contribution and folds in the new rightmost one -- no full recomputation."
        source="Generated for this page" href="" license="" />

Rolling hash values for every window (base 31, modulus 1,000,000,007), pattern hash 986140437:

```text
window 0  abacaba   986140437   == pattern hash -- verify -> real match
window 1  bacabad   846803353
window 2  acabada    14739852
window 3  cabadab   733385426
window 4  abadaba   986170228   != pattern hash despite starting with "abad..." -- no collision here
window 5  badabac   847726873
window 6  adabaca    43368972
window 7  dabacab   620888139
window 8  abacaba   986140437   == pattern hash -- verify -> real match
```

Two windows hash-equal the pattern (0 and 8), matching the naive scan's two matches exactly — and
both must still be verified character-by-character, because a hash equality is never proof by
itself (see Edge Cases below).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def naive_search(text, pattern):
    n, m = len(text), len(pattern)
    return [i for i in range(n - m + 1) if text[i:i + m] == pattern]


BASE, MOD = 31, 1_000_000_007

def rabin_karp_search(text, pattern):
    """Expected O(n + m); worst case O(nm) if every hash collides (verify-on-hit)."""
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []
    high = pow(BASE, m - 1, MOD)          # B^(m-1) mod P, precomputed once

    def window_hash(s):
        h = 0
        for ch in s:
            h = (h * BASE + ord(ch)) % MOD
        return h

    pattern_hash = window_hash(pattern)
    window = window_hash(text[:m])
    found = []
    for i in range(n - m + 1):
        if i > 0:
            window = (window - ord(text[i - 1]) * high) % MOD   # remove leading digit
            window = (window * BASE + ord(text[i + m - 1])) % MOD  # shift, add trailing digit
        if window == pattern_hash and text[i:i + m] == pattern:      # verify-on-hit
            found.append(i)
    return found
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cstdint>
#include <string_view>
#include <vector>

constexpr std::int64_t BASE = 31, MOD = 1'000'000'007;

std::vector<int> naive_search(std::string_view text, std::string_view pattern) {
    std::vector<int> found;
    const std::size_t n = text.size(), m = pattern.size();
    if (m == 0 || m > n) return found;
    for (std::size_t i = 0; i + m <= n; ++i)
        if (text.substr(i, m) == pattern) found.push_back(static_cast<int>(i));
    return found;
}

std::vector<int> rabin_karp_search(std::string_view text, std::string_view pattern) {
    std::vector<int> found;
    const std::size_t n = text.size(), m = pattern.size();
    if (m == 0 || m > n) return found;
    std::int64_t high = 1;
    for (std::size_t i = 0; i + 1 < m; ++i) high = (high * BASE) % MOD;

    auto window_hash = [](std::string_view s) {
        std::int64_t h = 0;
        for (char c : s) h = (h * BASE + static_cast<unsigned char>(c)) % MOD;
        return h;
    };

    const std::int64_t pattern_hash = window_hash(pattern);
    std::int64_t window = window_hash(text.substr(0, m));
    for (std::size_t i = 0; i + m <= n; ++i) {
        if (i > 0) {
            window = (window - static_cast<unsigned char>(text[i - 1]) * high % MOD + MOD) % MOD;
            window = (window * BASE + static_cast<unsigned char>(text[i + m - 1])) % MOD;
        }
        if (window == pattern_hash && text.substr(i, m) == pattern)   // verify-on-hit
            found.push_back(static_cast<int>(i));
    }
    return found;
}
```

</TabItem>
</Tabs>

## Practical Usage

- **Multi-pattern matching.** Rabin-Karp generalises to k patterns of the same length by hashing all
  k patterns once into a `set`, then sliding a single rolling hash over the text and checking set
  membership at each position — O(n + k) expected plus verification, instead of running k separate
  single-pattern scans. This is the shape behind plagiarism detectors and duplicate-chunk detection
  in content-addressed storage.
- **Python's `str.find` / `in`** use neither of these algorithms in general — CPython's actual
  implementation is covered in
  [KMP & the Z-Algorithm's Practical Usage section](./kmp-and-z-algorithm.md#practical-usage); do
  not assume `in` gives you Rabin-Karp's guarantees or its collision behaviour.
- **Double hashing** (two independent `(BASE, MOD)` pairs, both must agree) is the standard way to
  make an adversarial hash collision practically impossible without switching to a worst-case-linear
  algorithm — cheap insurance when the input is untrusted.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# both algorithms, checked on the traced inputs
assert naive_search("abacabadabacaba", "abacaba") == [0, 8]
assert rabin_karp_search("abacabadabacaba", "abacaba") == [0, 8]
assert naive_search("aaaaaaaab", "aaab") == [5]
assert rabin_karp_search("aaaaaaaab", "aaab") == [5]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert((naive_search("abacabadabacaba", "abacaba") == std::vector<int>{0, 8}));
    assert((rabin_karp_search("abacabadabacaba", "abacaba") == std::vector<int>{0, 8}));
    assert((naive_search("aaaaaaaab", "aaab") == std::vector<int>{5}));
    assert((rabin_karp_search("aaaaaaaab", "aaab") == std::vector<int>{5}));
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Skipping verify-on-hit.** Two different windows can hash to the same value by chance (a spurious
  hit) or by construction if an attacker knows the modulus — reporting a hash match as a real match
  without comparing the actual characters is a correctness bug, not a performance one.
- **Choosing a small modulus.** A modulus that fits in 16 bits collides often enough on ordinary text
  to make verification the common case rather than the rare one, erasing the algorithm's speed
  advantage; `MOD` around 10⁹ (as used above) keeps collisions rare in practice.
- **Recomputing `B^(m-1)` inside the loop.** This turns the O(1) roll into an O(log m) or O(m)
  operation per step depending on how it is recomputed, silently degrading the whole scan.
- **Forgetting the modulo can go negative.** `(window - removed) % MOD` in languages whose `%` can
  return a negative result (C++, unlike Python) needs `+ MOD` before the final `% MOD`, or the hash
  comparison is simply wrong on some windows — see the C++ code above.

## Comparisons

| | Best | Average | Worst | Extra space | Notes |
|---|---|---|---|---|---|
| Naive scan | O(n) | O(n) on random text | **O(nm)** | O(1) | The `"aaaa...ab"` input above realises the worst case exactly |
| Rabin-Karp | O(n + m) | O(n + m) | O(nm) | O(1) | Worst case only if every window collides; verify-on-hit is what keeps this rare |
| Rabin-Karp, k patterns | O(n + k) | O(n + k) | O(nmk) | O(k) | One rolling hash, k-way hash-set lookup per window |
| KMP | O(n + m) | O(n + m) | **O(n + m)** | O(m) | See [KMP & the Z-Algorithm](./kmp-and-z-algorithm.md); no collision risk at all |

Rabin-Karp is chosen over KMP specifically for the multi-pattern case, where one rolling hash and a
hash set of k pattern hashes beats running k independent KMP scans. For a single pattern where a
worst-case guarantee matters, KMP dominates — see CLRS 4th ed. §32.2 for Rabin-Karp's full analysis,
including the expected number of spurious hits under a random hash function.

## Recall

<Recall
  invariant="A rolling hash update removes the leading digit's contribution and folds in the new trailing digit in O(1) -- but a hash match is always a candidate, confirmed only by comparing the actual characters."
  costs={[
    ["naive scan (worst)", "O(nm)"],
    ["Rabin-Karp, one pattern (average)", "O(n + m)"],
    ["Rabin-Karp, one pattern (worst, all hashes collide)", "O(nm)"],
    ["Rabin-Karp, k patterns, hash-set lookup (average)", "O(n + k)"],
    ["one rolling-hash update", "O(1)"],
  ]}
  reachFor="Matching many patterns of the same length against one text, where one shared rolling hash and a hash set beats running each pattern's scan separately."
  trap="Reporting a hash match as a real match without verify-on-hit -- two different windows can collide, and skipping the character comparison turns a rare false positive into a silent correctness bug."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §32.2 — the Rabin-Karp
  algorithm, its rolling hash, and the expected-case analysis under a random hash function.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §5.3 "Substring Search" — Rabin-Karp measured against
  the naive scan and Boyer-Moore on real text.
- R. M. Karp & M. O. Rabin, "Efficient Randomized Pattern-Matching Algorithms", *IBM J. Research and
  Development* 31(2), 1987 — the original paper, including the multi-pattern extension.

## Related Pages

- [String Fundamentals](./string-fundamentals.md) — why an O(m) window comparison is the unit of cost the naive scan multiplies by every alignment.
- [KMP & the Z-Algorithm](./kmp-and-z-algorithm.md) — the worst-case-linear alternative for a single pattern, with no collision risk.
- [Suffix Structures & Autocomplete](./suffix-structures-and-autocomplete.md) — when the pattern isn't fixed in advance, a structure built once from the text beats re-scanning it per query.
- [Hash Tables](../data-structures/hash-tables.md) — the structure behind the multi-pattern hash-set lookup.
