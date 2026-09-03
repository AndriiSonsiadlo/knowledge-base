---
id: kmp-and-z-algorithm
title: KMP & the Z-Algorithm
sidebar_label: KMP & Z-Algorithm
sidebar_position: 3
tags: [computer-science, algorithms, strings, pattern-matching]
---

# KMP & the Z-Algorithm

The naive substring scan tries the pattern at every text position and, on a mismatch, throws away
everything it just learned. Line up `abacaba` against `abacabadabacaba`, match six characters, fail on
the seventh — and the naive loop restarts at text index 1 with an empty memory, re-reading five
characters it has already seen. On a text of `aaaa…a` with pattern `aaab` that waste is the whole
algorithm: O(nm) comparisons in the worst case, for a problem with n + m characters in it.

But the failed attempt was informative. Those six matched characters *are* known text: the text at
positions 0–5 is exactly `abacab`. If the pattern has a **border** — a prefix that is also a suffix of
what matched — then that prefix is already sitting in the text, correctly aligned, and there is no
need to re-verify it. `abacab` ends in `ab`, which is also how the pattern starts, so the pattern can
slide forward by four and resume comparing at pattern index 2 instead of 0. Every other alignment in
between is provably a mismatch and never needs to be tried.

The **failure function** is that reasoning precomputed for every prefix of the pattern, once, before
the search begins. `fail[i]` is the length of the longest *proper* prefix of `pattern[0..i]` that is
also a suffix of it. With it, the search pointer into the text only ever moves forward — which is what
makes KMP O(n + m) worst case and, more practically, what makes it usable on a stream you cannot
rewind. The **Z-algorithm** computes the same information in a different shape — for each position of
a string, how far it agrees with the string's own start — and the two are interconvertible.

:::info[Prerequisites]
Comfortable with [arrays](../data-structures/arrays.md) and 0-based index arithmetic. Nothing here
depends on character encodings, but if the "characters" are Unicode see
[character encoding](../../bit-manipulation/character-encoding.md) — KMP compares code units, and
what counts as one character is your decision to make before the comparison.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Border** | A string that is both a proper prefix and a proper suffix of another. `aba` is a border of `abacaba` |
| **Proper** | Excludes the whole string. Without this, `fail[i] = i + 1` always, and the search never advances |
| **Failure function `fail[i]`** | Length of the longest border of `pattern[0..i]`. Also written `π` (CLRS) or `lps` |
| **Border chain** | `fail[i]`, `fail[fail[i]−1]`, … enumerates *every* border, longest first. This is the mismatch fallback loop |
| **Z-array `z[i]`** | Length of the longest common prefix of `s` and `s[i..]`. `z[0]` is defined as `n` (or left unused) |
| **Z-box `[l, r)`** | The rightmost known match against the prefix, reused to initialise later `z[i]` without re-comparing |

## Mechanism

<Figure src="/img/cs/algorithms/kmp-failure-table.png"
        alt="The pattern a b a c a b a in seven boxes with the values 0 0 1 0 1 2 3 aligned beneath, the prefix aba and the suffix aba marked above, and a curved arrow from position 6 back to position 3"
        caption="fail[6] = 3 because abacaba's longest border is aba. On a mismatch after position 6, comparison resumes at pattern[3] — the pattern slides four places, and the text pointer does not move at all." />

```text
pattern = abacaba

  i    pattern[0..i]   longest proper prefix that is also a suffix   fail[i]
  0    a               —                                            0
  1    ab              —                                            0
  2    aba             a                                            1
  3    abac            —                                            0
  4    abaca           a                                            1
  5    abacab          ab                                           2
  6    abacaba         aba                                          3

search in text = abacabadabacaba

  text pos   pattern pos   action
  0..6       0..6          full match at text index 0
  7          7 → fail[6]=3 'd' vs pattern[3]='c' mismatch, slide to 3, then to fail[2]=1, then 0
  8..14      0..6          full match at text index 8
```

Two things to notice. After the match at index 0 the search does **not** reset `k` to 0 — it sets
`k = fail[6] = 3`, which is what lets KMP report overlapping occurrences. And at text position 7 the
fallback runs three times (3 → 1 → 0) without the text pointer moving; each of those steps strictly
decreases `k`, and `k` only ever increases by one per text character, so the total fallback work over
the whole search is bounded by the total increase — the amortized argument behind the O(n) search
bound (CLRS 4th ed. §32.4).

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def failure(pattern):
    """fail[i] = length of the longest proper border of pattern[0..i]."""
    fail = [0] * len(pattern)
    k = 0                                     # length of the current candidate border
    for i in range(1, len(pattern)):          # from 1: fail[0] is 0 by definition
        while k and pattern[i] != pattern[k]:
            k = fail[k - 1]                   # fall back along the border chain
        if pattern[i] == pattern[k]:
            k += 1
        fail[i] = k
    return fail


def kmp_search(text, pattern):
    """Every start index where pattern occurs in text, overlaps included."""
    if not pattern:
        return list(range(len(text) + 1))     # the empty pattern matches everywhere
    fail, found, k = failure(pattern), [], 0
    for i, ch in enumerate(text):
        while k and ch != pattern[k]:
            k = fail[k - 1]                   # i never decreases — this is the whole point
        if ch == pattern[k]:
            k += 1
        if k == len(pattern):
            found.append(i - k + 1)
            k = fail[k - 1]                   # not 0: overlapping matches survive
    return found
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <algorithm>
#include <cassert>
#include <string>
#include <string_view>
#include <vector>

std::vector<int> failure(std::string_view pattern) {
    std::vector<int> fail(pattern.size(), 0);
    int k = 0;
    for (std::size_t i = 1; i < pattern.size(); ++i) {
        while (k && pattern[i] != pattern[k]) k = fail[k - 1];
        if (pattern[i] == pattern[k]) ++k;
        fail[i] = k;
    }
    return fail;
}

std::vector<int> kmp_search(std::string_view text, std::string_view pattern) {
    std::vector<int> found;
    if (pattern.empty()) return found;
    const std::vector<int> fail = failure(pattern);
    int k = 0;
    for (std::size_t i = 0; i < text.size(); ++i) {
        while (k && text[i] != pattern[k]) k = fail[k - 1];
        if (text[i] == pattern[k]) ++k;
        if (k == static_cast<int>(pattern.size())) {
            found.push_back(static_cast<int>(i) - k + 1);
            k = fail[k - 1];                        // overlapping matches survive
        }
    }
    return found;
}
```

</TabItem>
</Tabs>

### The Z-array

Same information, different question: `z[i]` is how far `s[i..]` agrees with `s` itself. The trick is
to remember the match that reached furthest right — the Z-box `[l, r)` — and reuse it, because
`s[l..r)` is by definition a copy of `s[0..r−l)`, so `z[i]` starts out known and only the tail past
`r` needs real comparisons.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def z_array(s):
    z = [0] * len(s)
    if s:
        z[0] = len(s)
    left = right = 0                              # the rightmost Z-box, [left, right)
    for i in range(1, len(s)):
        if i < right:
            z[i] = min(right - i, z[i - left])    # copy from inside the box, but not past it
        while i + z[i] < len(s) and s[z[i]] == s[i + z[i]]:
            z[i] += 1                             # extend past the box, one real comparison each
        if i + z[i] > right:
            left, right = i, i + z[i]
    return z


def z_search(text, pattern, sep="\x00"):
    """Matching via Z: any position whose Z-value equals len(pattern) is an occurrence."""
    joined = pattern + sep + text                 # sep must not occur in either string
    z = z_array(joined)
    offset = len(pattern) + 1
    return [i - offset for i in range(offset, len(joined)) if z[i] == len(pattern)]
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
std::vector<int> z_array(std::string_view s) {
    const int n = static_cast<int>(s.size());
    std::vector<int> z(n, 0);
    if (n) z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; ++i) {
        if (i < r) z[i] = std::min(r - i, z[i - l]);
        while (i + z[i] < n && s[z[i]] == s[i + z[i]]) ++z[i];
        if (i + z[i] > r) { l = i; r = i + z[i]; }
    }
    return z;
}
```

</TabItem>
</Tabs>

Each is a rewriting of the other. `z` gives matching directly: run it over `pattern + sep + text` with
a separator that occurs in neither, and every position with `z[i] == m` is an occurrence — this is why
the Z-algorithm is often the easier one to remember, since there is no second search loop to get
wrong. Conversely, `fail` can be recovered from the pattern's own `z`: for each `i` with `z[i] > 0`,
the prefix of length `z[i]` is a border ending at `i + z[i] − 1`, so writing
`fail[i + z[i] − 1] = max(fail[…], z[i])` and then propagating down the border chain reconstructs the
failure function. Both directions are O(n) worst case.

## Practical Usage

You will rarely type any of this: the standard search routines are already worst-case-safe or better.

- **Python `str.find` / `in` / `str.index` are not KMP.** CPython uses a Boyer-Moore-Horspool-style scan
  with a bloom-filter skip table for short needles and switches to
  [Crochemore & Perrin's two-way algorithm](https://github.com/python/cpython/blob/main/Objects/stringlib/stringlib_find_two_way_notes.txt)
  once the inputs are large enough — that note is in the CPython source and states the algorithm runs
  in "O(len(needle) + len(haystack))" time with constant space. The practical consequence: you do not
  need to hand-write KMP to avoid a quadratic blow-up in Python.
- **C++ `std::search` with `std::boyer_moore_searcher`** (`<functional>`, C++17) is the drop-in for a
  fixed pattern searched repeatedly, because the searcher object holds the preprocessed tables across
  calls. Note its standardised bound is weaker than KMP's: at most `(last - first) * (pat_last - pat_first)`
  applications of the predicate ([`[func.search.bm]`](https://eel.is/c++draft/func.search.bm)) — Boyer-Moore
  is fast on average, not worst-case linear.
- **Streaming input.** The real reason to write KMP yourself. The search loop touches each text
  character exactly once and never seeks backwards, so it runs over a socket, a pipe, or a ring buffer
  with only `k` and `fail` retained — O(m) memory in the worst case, regardless of how much text goes
  past.
- **Fixed-size buffers.** Matching across chunk boundaries falls out for free: carry `k` from one chunk
  to the next and the match is found even when it straddles the seam.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# both implementations, checked on the traced input
assert failure("abacaba") == [0, 0, 1, 0, 1, 2, 3]
assert failure("aaaa") == [0, 1, 2, 3]              # every prefix is a border of the next
assert kmp_search("abacabadabacaba", "abacaba") == [0, 8]   # the traced search
assert kmp_search("aaaa", "aa") == [0, 1, 2]        # overlaps, which a "skip m" loop would miss

assert z_array("abacaba") == [7, 0, 1, 0, 3, 0, 1]
assert z_search("abacabadabacaba", "abacaba") == [0, 8]
assert z_search("aaaa", "aa") == [0, 1, 2]          # the two agree, as they must
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert((failure("abacaba") == std::vector<int>{0, 0, 1, 0, 1, 2, 3}));
    assert((kmp_search("abacabadabacaba", "abacaba") == std::vector<int>{0, 8}));
    assert((kmp_search("aaaa", "aa") == std::vector<int>{0, 1, 2}));  // overlaps kept
    assert((z_array("abacaba") == std::vector<int>{7, 0, 1, 0, 3, 0, 1}));
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **The proper-prefix bug.** If `fail[i]` is allowed to be `i + 1` — the whole prefix counting as its
  own border — then on a run of identical characters the fallback `k = fail[k-1]` never decreases and
  the search loop spins forever. `fail[0] == 0` always, and the `for` loop must start at index 1.
- **Empty pattern.** `len(pattern) == 0` makes `pattern[k]` an index error on the first character.
  Decide the convention explicitly: the code above returns every position (`str.find` agrees —
  `"abc".find("")` is 0), and the C++ version returns nothing. Either is defensible; silently crashing
  is not.
- **Pattern longer than the text.** Not a special case — the loop simply never reaches `k == m` and
  returns empty. No guard needed, and adding one usually introduces an off-by-one.
- **Overlapping matches.** `kmp_search("aaaa", "aa")` is `[0, 1, 2]`, not `[0, 2]`. Resetting `k = 0`
  after a match, or advancing the text index by `m`, silently drops the overlaps. Python's
  [`str.count`](https://docs.python.org/3/library/stdtypes.html#str.count) counts *non-overlapping*
  occurrences, so it disagrees with this function by design.
- **Signed/unsigned mixing in C++.** `k` is `int` while `pattern.size()` is `std::size_t`; comparing
  them directly is a warning at best and a wrong comparison at worst. Cast once, deliberately.

## Comparisons

| | Best | Average | Worst | Extra space | Notes |
|---|---|---|---|---|---|
| Naive scan | O(n) | O(n) on random text | O(nm) | O(1) | Fine until the alphabet is small and the pattern is periodic |
| **KMP** | O(n + m) | O(n + m) | **O(n + m)** | O(m) | Never re-reads text; the guarantee is the product |
| Z-algorithm | O(n + m) | O(n + m) | O(n + m) | O(n + m) | Same bound; needs the concatenated string in memory |
| Rabin-Karp | O(n + m) | O(n + m) | O(nm) | O(1) | Hash collisions force verification; wins for *multiple* patterns |
| Boyer-Moore | O(n / m) | Sublinear in practice | O(nm) as standardised | O(m + σ) | Skips ahead; the usual choice when the alphabet is large |

KMP is chosen for its worst case, not its average — Boyer-Moore beats it on ordinary English text
because it examines only a fraction of the characters. Rabin-Karp is the right answer when the
question is "which of these 10,000 patterns appear", since one rolling hash serves them all. See
CLRS 4th ed. §32.2 for Rabin-Karp's analysis and Sedgewick & Wayne §5.3 for the empirical comparison.

## Recall

<Recall
  invariant="`fail[i]` is the length of the longest proper prefix of `pattern[0..i]` that is also a suffix of it — so on a mismatch the pattern slides to that border and the text pointer never moves back."
  costs={[
    ["build the failure function (worst)", "O(m)"],
    ["search after building (worst)", "O(n)"],
    ["total, all occurrences (worst)", "O(n + m)"],
    ["extra space (worst)", "O(m)"],
    ["Z-array over a string (worst)", "O(n)"],
  ]}
  reachFor="One pattern, a long text, and a guarantee is needed — no worst case where the naive scan degrades to O(nm)."
  trap="`fail[i]` must be a *proper* prefix: `fail[0]` is always 0, never `i+1`. Getting that wrong makes the algorithm loop forever on a run of identical characters."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §32.4 — the failure
  function ("prefix function π"), its correctness proof, and the amortized argument for the O(n) search.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §5.3 "Substring Search" — KMP as a DFA, plus Boyer-Moore
  and Rabin-Karp measured against each other on real inputs.
- D. E. Knuth, J. H. Morris & V. R. Pratt, "Fast Pattern Matching in Strings", *SIAM J. Computing* 6(2),
  1977 — the original, including the observation that the whole thing came out of a linear-time
  palindrome recogniser.
- D. Gusfield, *Algorithms on Strings, Trees, and Sequences*, 1997, §1.3–1.4 — the Z-algorithm as the
  primitive from which KMP is derived, rather than the other way round.
- [CPython's two-way search notes](https://github.com/python/cpython/blob/main/Objects/stringlib/stringlib_find_two_way_notes.txt)
  — what `str.find` actually does, and why it is not KMP.

## Related Pages

- [Arrays](../data-structures/arrays.md) — the contiguous buffer both algorithms scan, and the index arithmetic they live on.
- [Two Pointers & Sliding Window](../problem-solving-patterns/two-pointers-and-sliding-window.md) — the same "never move the left pointer backwards" discipline, in a setting without a pattern.
- [Character Encoding](../../bit-manipulation/character-encoding.md) — what a "character" is before you start comparing them.
- [Big-O Notation](../complexity/big-o-notation.md) — why O(n + m) worst case is a different promise from O(n + m) average.
