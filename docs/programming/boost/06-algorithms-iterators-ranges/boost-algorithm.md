---
id: boost-algorithm
title: Boost.Algorithm
sidebar_label: Boost.Algorithm
sidebar_position: 1
tags: [c++, boost, algorithm, searching]
---

# Boost.Algorithm

`Boost.Algorithm` is a collection of **general-purpose algorithms** that complement `<algorithm>`. Many
of its components filled gaps in the standard library and were later adopted — `clamp` in C++17,
`all_of`/`any_of`/`none_of` in C++11 — while others like Boyer-Moore string search and `gather`
remain Boost-only.

:::info The problem it solves
The standard `<algorithm>` header is powerful but incomplete. Common operations — clamping a value,
hex-encoding a buffer, searching a string with a fast algorithm — required hand-rolled code or
third-party snippets. Boost.Algorithm collects these into a single, peer-reviewed header set.
:::

## Clamping

`boost::algorithm::clamp` restricts a value to a closed interval. It predates `std::clamp` (C++17)
and works identically.

```cpp showLineNumbers title="clamp_demo.cpp"
#include <boost/algorithm/clamp.hpp>
#include <iostream>

int main() {
    int value = 42;
    int clamped = boost::algorithm::clamp(value, 0, 10);
    std::cout << clamped << "\n";  // 10

    // Range version: clamp every element in place
    std::vector<int> v{-5, 3, 12, 7, 20};
    boost::algorithm::clamp_range(v, v.begin(), 0, 10);
    // v is now {0, 3, 10, 7, 10}
}
```

## Predicate queries: all_of, any_of, none_of, one_of

These were in Boost before C++11 added the first three to `<algorithm>`. `one_of` — true when
**exactly one** element satisfies the predicate — remains Boost-only.

```cpp showLineNumbers title="predicates.cpp"
#include <boost/algorithm/cxx11/all_of.hpp>
#include <boost/algorithm/cxx11/one_of.hpp>
#include <vector>
#include <cassert>

int main() {
    std::vector<int> v{2, 4, 6, 8};

    assert(boost::algorithm::all_of(v, [](int n){ return n % 2 == 0; }));
    assert(boost::algorithm::none_of(v, [](int n){ return n > 100; }));

    std::vector<int> w{1, 2, 3};
    assert(boost::algorithm::one_of(w, [](int n){ return n == 2; }));
}
```

## String searching: Boyer-Moore

Boost provides Boyer-Moore and Boyer-Moore-Horspool searchers for **sub-linear** string matching.
These build a skip table from the pattern once, then scan the text much faster than `std::search`
for long patterns.

```cpp showLineNumbers title="boyer_moore.cpp"
#include <boost/algorithm/searching/boyer_moore.hpp>
#include <string>
#include <iostream>

int main() {
    std::string text = "the quick brown fox jumps over the lazy dog";
    std::string pattern = "brown fox";

    boost::algorithm::boyer_moore<std::string::iterator> searcher(
        pattern.begin(), pattern.end());

    auto result = searcher(text.begin(), text.end());
    if (result.first != text.end()) {
        std::cout << "found at position "
                  << std::distance(text.begin(), result.first) << "\n";
    }
}
```

:::tip When to reach for Boyer-Moore
For short patterns or one-off searches, `std::string::find` is fine. Boyer-Moore pays off when you
search for the **same long pattern** across many texts — the precomputed skip table amortises setup.
:::

## Hex encoding and decoding

`hex` and `unhex` convert between binary data and hexadecimal strings. Useful for checksums, debug
output, and protocol framing.

```cpp showLineNumbers title="hex_demo.cpp"
#include <boost/algorithm/hex.hpp>
#include <string>
#include <iostream>

int main() {
    std::string input = "Boost";
    std::string encoded;
    boost::algorithm::hex(input, std::back_inserter(encoded));
    std::cout << encoded << "\n";  // "426F6F7374"

    std::string decoded;
    boost::algorithm::unhex(encoded, std::back_inserter(decoded));
    std::cout << decoded << "\n";  // "Boost"
}
```

## Gather

`gather` partitions a range so that all elements satisfying a predicate are moved to a contiguous
block around a given pivot position.

```cpp showLineNumbers title="gather_demo.cpp"
#include <boost/algorithm/gather.hpp>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v{0, 1, 0, 1, 0, 1, 0};

    // Gather all 1s around the middle
    auto pivot = v.begin() + 3;
    auto [first, last] = boost::algorithm::gather(
        v.begin(), v.end(), pivot,
        [](int n){ return n == 1; });

    for (int x : v) std::cout << x;  // "0011100"
    std::cout << "\n";
}
```

## What migrated to the standard

| Boost algorithm | Standard equivalent | Standard version |
|-----------------|---------------------|------------------|
| `all_of`, `any_of`, `none_of` | `std::all_of`, `std::any_of`, `std::none_of` | C++11 |
| `is_sorted`, `is_partitioned` | `std::is_sorted`, `std::is_partitioned` | C++11 |
| `copy_if` | `std::copy_if` | C++11 |
| `clamp` | `std::clamp` | C++17 |
| Boyer-Moore searcher | `std::boyer_moore_searcher` | C++17 |

:::note What remains Boost-only
`one_of`, `hex`/`unhex`, `gather`, and the `_equal` predicate variants have no standard equivalents.
If you need them, Boost.Algorithm is still the canonical source.
:::

## See also

- <Icon icon="lucide:repeat" inline /> [Boost.Range](./boost-range.md) — range-based wrappers around algorithms.
- <Icon icon="lucide:type" inline /> [String Algo](../05-strings-and-text/string-algo.md) — string-specific algorithms (trim, split, case conversion).
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
