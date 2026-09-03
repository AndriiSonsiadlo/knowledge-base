---
id: string-fundamentals
title: String Fundamentals
sidebar_label: String Fundamentals
sidebar_position: 1
tags: [computer-science, algorithms, strings]
---

# String Fundamentals

Every algorithm in this folder assumes a cost model for three operations that look free and are
not: building a string out of pieces, slicing a piece back out, and comparing two strings for
equality. None of the three are wrong to use — they are the only way to work with text in most
languages — but each has a shape (linear, or accidentally quadratic) that determines whether the
matching algorithm built on top of them keeps its advertised bound or silently loses it.

The root cause of all three is the same fact from [the folder introduction](./intro.md): strings
are immutable in Python, Java, C#, and most managed languages (`std::string` is a deliberate
exception — see below). "Modifying" an immutable string is not a modification at all, it is
building a brand-new string and discarding the old one. Whether that costs O(1) amortized or O(n)
per step depends entirely on how many characters get copied into that new string, which is a
question about *how* the code builds it, not about the string type itself.

:::info[Prerequisites]
None beyond basic loop and complexity reading. If "character" needs a precise definition (a byte? a
code point? a grapheme?) before any of this matters, see
[Character Encoding](../../bit-manipulation/character-encoding.md) first — encoding is a separate
concern from the cost model here and is not repeated on this page.
:::

## Core Concepts

| Term | Meaning |
|---|---|
| **Immutable string** | A string value that cannot change in place; every apparent edit allocates a new string |
| **String builder** | A pattern that accumulates pieces in a mutable container (a list, a buffer) and produces the immutable final string exactly once |
| **Amortized O(1) resize** | The general guarantee behind a dynamic array's `append` — see [Amortized Analysis](../complexity/amortized-analysis.md); it does **not** automatically apply to string concatenation, because a new string is a new object, not a resized one |
| **Slicing** | Producing a new string from a contiguous range of an existing one; costs O(k) for a slice of length k, since the characters must be copied into the new string |
| **Normalisation (NFC / NFD)** | Rewriting a Unicode string into one canonical sequence of code points, so that two visually identical strings compare equal |

## Mechanism

### Building: `+=` in a loop vs `str.join`

<Figure src="/img/cs/algorithms/string-concat-cost.png"
        alt="Line chart of total characters copied against number of concatenations, showing the += loop growing quadratically and str.join growing linearly"
        caption="Total characters copied while assembling a string from n equal-length pieces. join() copies each character once; a naive += loop re-copies everything accumulated so far, on every piece."
        source="Generated for this page" href="" license="" />

Trace input — five parts, each two characters: `["ab", "cd", "ef", "gh", "ij"]`, final string
`"abcdefghij"` (10 characters):

```text
+= in a loop                                  str.join(parts)
acc = ""                                      total length computed first: 2+2+2+2+2 = 10
acc += "ab"  copies 0+2 = 2 chars  (acc="ab")  one buffer of length 10 allocated once
acc += "cd"  copies 2+2 = 4 chars  (acc="abcd")
acc += "ef"  copies 4+2 = 6 chars  (acc="abcdef")
acc += "gh"  copies 6+2 = 8 chars  (acc="abcdefgh")
acc += "ij"  copies 8+2 = 10 chars (acc="abcdefghij")
-----------------------------------------------------------------------
total characters copied: 30                   total characters copied: 10
```

With n equal-length parts of length k each, the naive loop's i-th step copies `i*k + k` characters
(everything accumulated so far, plus the new piece), so the total is
`k(1 + 2 + ... + n) = k*n(n+1)/2` — **O(n²)** in the number of parts, for an output that is only
O(n) characters long. `join` computes the total length once, allocates one buffer, and writes each
part into it exactly once: **O(n)** total, matching the size of what it produces.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def build_with_plus_equals(parts):
    """O(n^2) in len(parts) worst case: every += can reallocate and recopy everything so far."""
    acc = ""
    copied = 0
    for part in parts:
        copied += len(acc) + len(part)   # what a fresh allocation would have to copy
        acc += part
    return acc, copied


def build_with_join(parts):
    """O(n) in total output length: one allocation, each character written once."""
    copied = sum(len(p) for p in parts)  # str.join computes total length, then writes once
    return "".join(parts), copied
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <numeric>
#include <string>
#include <vector>

std::string build_with_reserve(const std::vector<std::string>& parts) {
    // std::string is mutable and contiguous, so reserve() + append() is the join() equivalent:
    // one allocation, each character appended once.
    std::size_t total = 0;
    for (const auto& p : parts) total += p.size();
    std::string acc;
    acc.reserve(total);          // avoids the geometric-growth reallocations append() alone risks
    for (const auto& p : parts) acc += p;
    return acc;
}
```

</TabItem>
</Tabs>

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
import unicodedata

# checked against the hand-counted trace above
parts = ["ab", "cd", "ef", "gh", "ij"]
joined_plus, copied_plus = build_with_plus_equals(parts)
joined_join, copied_join = build_with_join(parts)
assert joined_plus == joined_join == "abcdefghij"
assert copied_plus == 30       # 2+4+6+8+10
assert copied_join == 10       # output length, each character written once

# NFC/NFD: precomposed 'e-acute' vs 'e' + combining acute accent render identically, compare unequal
precomposed = "\u00e9"                 # U+00E9: 'e-acute' as one code point
decomposed = "e\u0301"                 # U+0065 U+0301: 'e' + combining acute accent
assert precomposed != decomposed                                    # visually identical, unequal
assert unicodedata.normalize("NFC", decomposed) == precomposed      # normalise -> compare equal
assert unicodedata.normalize("NFD", precomposed) == decomposed
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    std::vector<std::string> parts{"ab", "cd", "ef", "gh", "ij"};
    assert(build_with_reserve(parts) == "abcdefghij");
}
```

</TabItem>
</Tabs>

**CPython has a special case that makes naive `+=` look fast on real code**, and it must not be
relied on: when the left-hand string has a reference count of 1 (nothing else points at it) and the
implementation can grow the underlying buffer in place, `s = s + t` / `s += t` skips the full
reallocate-and-copy and resizes instead. This is documented as an implementation detail of CPython,
not a language guarantee — see
[What's New in Python 2.4](https://docs.python.org/3/whatsnew/2.4.html#other-language-changes),
which introduced it, and the CPython source's own
[`unicode_concat`](https://github.com/python/cpython/blob/main/Objects/unicodeobject.c) path, which
checks the refcount before taking the fast path. Any of these break it: the string being referenced
elsewhere (`other = s; s += t`), running under PyPy or another implementation, or a future CPython
release changing the heuristic. `"".join(parts)` has no such dependency — its O(n) bound is a
property of the algorithm, not an accident of one interpreter's memory management.

## Practical Usage

- **Python:** build a `list` of pieces (`parts.append(chunk)`) and call `"".join(parts)` once at the
  end. This is the idiomatic pattern precisely because it does not depend on the refcount special
  case above.
- **`io.StringIO`** is the buffer-style alternative for interleaved building and reading —
  see the [`io` module docs](https://docs.python.org/3/library/io.html#io.StringIO) — useful when
  the pieces are produced by many small `write()` calls rather than collected into a list first.
- **C++ `std::string`** is mutable and contiguous, so `+=`/`append()` in a loop is idiomatic there —
  but without `reserve()` first, repeated `append()` still pays amortized O(1) *per character*
  reallocation cost identical to `std::vector::push_back`
  ([`[string.capacity]`](https://eel.is/c++draft/string.capacity)), not the O(n²) total of Python's
  naive loop, since each append only copies the characters it is currently holding, not a
  freshly-copied whole string each time.
- **Slicing:** `s[a:b]` in Python and `s.substr(a, len)` in C++ both allocate a new string of length
  `b - a`, copying that many characters — O(k) for a slice of length k, never O(1), and never
  "shares" the original buffer.

## Edge Cases & Pitfalls

- **`+=` in a loop, on a large number of parts.** The single most common accidental-quadratic bug in
  string-heavy code; the fix is always to defer to a builder and join once.
- **Relying on CPython's in-place resize.** Code that works fine in a script and turns quadratic
  under PyPy, or after a refactor that keeps a second reference to the accumulator alive, is this bug
  hiding behind an implementation detail — see the citation above.
- **`==` returning `False` for text that looks identical on screen.** `"é"` typed as one precomposed
  code point (U+00E9) and `"é"` typed as `"e"` + a combining acute accent (U+0065 U+0301) render
  identically but are different code point sequences, different lengths, and compare unequal with
  plain `==`. Comparing user-entered text (search boxes, filenames, usernames) without normalising
  first is a live bug, not a theoretical one — see
  [Unicode Standard Annex #15](https://unicode.org/reports/tr15/) for the four normal forms and
  Python's [`unicodedata.normalize`](https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize)
  for the call that fixes it: normalise both sides to the same form (NFC is the common choice) before
  comparing.
- **Normalising once and comparing many times, vs normalising on every comparison.** The cost is the
  same shape as hashing: pay the O(m) normalisation once per string, not once per comparison.

## Comparisons

| | Cost to build n parts, total length m | Cost to compare two strings | Notes |
|---|---|---|---|
| `+=` in a loop (naive, no special case) | O(n·m) worst case | — | Each step re-copies everything accumulated so far |
| `str.join` | O(m) | — | One allocation, one pass |
| `s1 == s2`, no normalisation | — | O(m) worst case, O(1) best case | Stops at the first mismatch |
| `s1 == s2` after `unicodedata.normalize` | — | O(m) to normalise, plus O(m) to compare | Correct for visually-identical text; the naive version is not |

## Recall

<Recall
  invariant="An immutable string's 'modification' is always a fresh allocation; the total characters copied is what determines whether building a string is linear or quadratic, not whether the code looks short."
  costs={[
    ["str.join(parts), total output length m (worst)", "O(m)"],
    ["'+=' in a loop, n parts, no special case (worst)", "O(n*m)"],
    ["slicing a length-k substring (worst)", "O(k)"],
    ["Unicode normalisation, length m (worst)", "O(m)"],
  ]}
  reachFor="Any code that assembles a string from more than a couple of pieces in a loop, or compares user-entered/external text for equality."
  trap="Relying on CPython's refcount-1 in-place resize to make a += loop fast -- it is an implementation detail of one interpreter, not a language guarantee, and silently stops applying the moment a second reference exists."
/>

## References

- Python documentation, [What's New in Python 2.4 — Other Language Changes](https://docs.python.org/3/whatsnew/2.4.html#other-language-changes)
  — the original note on CPython's string-concatenation resize optimisation and its refcount
  precondition.
- Python documentation, [`unicodedata.normalize`](https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize)
  and [Unicode Standard Annex #15](https://unicode.org/reports/tr15/) — the four normal forms
  (NFC, NFD, NFKC, NFKD) and which one to pick for comparison.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §5.1 "String Sorts" (introductory pages) — the
  alphabet-and-immutability cost model this page's numbers come from.
- ISO/IEC 14882 (C++ standard), [`[string.capacity]`](https://eel.is/c++draft/string.capacity) —
  `std::string`'s amortized growth guarantee, the reason C++'s `+=` loop does not share Python's
  worst case.

## Related Pages

- [Strings & Text Introduction](./intro.md) — why alphabet size, immutability, and comparison cost define this whole folder.
- [Naive Matching & Rabin-Karp](./naive-matching-and-rabin-karp.md) — where an O(m) comparison, done once per alignment, becomes the O(nm) baseline this folder improves on.
- [KMP & the Z-Algorithm](./kmp-and-z-algorithm.md) — a matcher that gets its worst-case bound precisely by never re-comparing a character it has already seen.
- [Character Encoding](../../bit-manipulation/character-encoding.md) — what a "character" is, a separate question from what it costs to build or compare one.
- [Amortized Analysis](../complexity/amortized-analysis.md) — the general technique behind dynamic-array growth, and why it does not rescue a naive string-concatenation loop.
