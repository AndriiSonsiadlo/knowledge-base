---
id: boost-regex
title: Boost.Regex
sidebar_label: Boost.Regex
sidebar_position: 4
tags: [c++, boost, regex, strings]
---

# Boost.Regex

`boost::regex` is a **regular expression engine** for C++ that supports Perl and POSIX syntax. It
is the direct ancestor of `std::regex` — the standard committee adopted it essentially wholesale
into C++11. Boost.Regex remains relevant because several standard library implementations of
`std::regex` are notoriously slow, while Boost.Regex has had years of performance tuning.

:::info The problem it solves
Before C++11, C++ had no built-in regular expression support at all. You either pulled in PCRE,
wrote manual parsing loops, or shelled out to another language. Boost.Regex brought proper regex
to C++ with a clean, iterator-friendly API that the standard later adopted.
:::

## Matching

`boost::regex_match` tests whether an **entire** string matches a pattern:

```cpp showLineNumbers title="match.cpp"
#include <boost/regex.hpp>
#include <iostream>
#include <string>

int main() {
    boost::regex pattern(R"(\d{4}-\d{2}-\d{2})");  // YYYY-MM-DD
    std::string date = "2026-04-07";

    if (boost::regex_match(date, pattern)) {
        std::cout << "valid date format\n";
    }
}
```

:::warning regex_match versus regex_search
`regex_match` requires the **entire** string to match. `regex_search` finds a match **within**
the string. Confusing the two is one of the most common regex bugs in C++.
:::

## Searching and capture groups

`boost::regex_search` finds the first match and populates a `smatch` (sub-match) object with
capture groups:

```cpp showLineNumbers title="search.cpp"
#include <boost/regex.hpp>
#include <iostream>
#include <string>

int main() {
    std::string log = "[ERROR] 2026-04-07 disk full on /dev/sda1";
    boost::regex pattern(R"(\[(\w+)\]\s+(\d{4}-\d{2}-\d{2})\s+(.*))");
    boost::smatch m;

    if (boost::regex_search(log, m, pattern)) {
        std::cout << "level: " << m[1] << "\n";   // ERROR
        std::cout << "date:  " << m[2] << "\n";   // 2026-04-07
        std::cout << "msg:   " << m[3] << "\n";   // disk full on /dev/sda1
    }
}
```

## Replacing

`boost::regex_replace` substitutes all matches with a replacement string. Back-references use
`$1`, `$2`, etc.:

```cpp showLineNumbers title="replace.cpp"
#include <boost/regex.hpp>
#include <iostream>
#include <string>

int main() {
    std::string text = "Call 555-1234 or 555-5678";
    boost::regex phone(R"((\d{3})-(\d{4}))");

    std::string redacted = boost::regex_replace(text, phone, "$1-XXXX");
    std::cout << redacted << "\n";
    // Call 555-XXXX or 555-XXXX
}
```

## Iterating over all matches

`boost::sregex_iterator` walks through every match in a string, similar to `std::sregex_iterator`:

```cpp showLineNumbers title="iterate.cpp"
#include <boost/regex.hpp>
#include <iostream>
#include <string>

int main() {
    std::string html = R"(<a href="one.html"> <a href="two.html">)";
    boost::regex link(R"(href="([^"]+)")");

    auto begin = boost::sregex_iterator(html.begin(), html.end(), link);
    auto end   = boost::sregex_iterator();

    for (auto it = begin; it != end; ++it) {
        std::cout << (*it)[1] << "\n";
    }
    // one.html
    // two.html
}
```

## Regex syntax flavours

Boost.Regex supports multiple syntax modes, selected at construction:

| Flag | Syntax | Notes |
|------|--------|-------|
| `boost::regex::perl` (default) | Perl-compatible | most common, supports look-ahead/behind |
| `boost::regex::extended` | POSIX extended | `egrep`-like |
| `boost::regex::basic` | POSIX basic | `grep`-like, escapes reversed |
| `boost::regex::icase` | (modifier) | case-insensitive matching |

```cpp showLineNumbers
boost::regex ci_pattern("hello", boost::regex::perl | boost::regex::icase);
```

## Boost.Regex versus std::regex

| Feature | `boost::regex` | `std::regex` (C++11) |
|---------|----------------|----------------------|
| Header | `<boost/regex.hpp>` | `<regex>` |
| Namespace | `boost::` | `std::` |
| Performance | well-optimised | varies by implementation (often slow) |
| Named captures | yes (`(?P<name>...)`) | implementation-defined |
| Unicode | ICU integration available | limited |
| Build requirement | compiled library (`-lboost_regex`) | standard library |

:::note Which to choose
If your `std::regex` implementation is fast enough (measure it), prefer the standard. Otherwise
Boost.Regex is a drop-in improvement — the API is nearly identical. On GCC's libstdc++, where
`std::regex` has historically been slow, Boost.Regex can be an order of magnitude faster.
:::

:::danger Boost.Regex is a compiled library
Unlike most Boost libraries, Boost.Regex is **not** header-only. You must link against
`-lboost_regex`. See [header-only vs compiled](../00-overview/header-only-vs-compiled.md).
:::

## See also

- <Icon icon="lucide:type" inline /> [Boost.StringAlgo](./string-algo.md) — simpler find/replace when you do not need regex.
- <Icon icon="lucide:cpu" inline /> [Boost.Spirit](./boost-spirit.md) — grammar-level parsing beyond what regex can express.
- <Icon icon="lucide:scissors" inline /> [Boost.Tokenizer](./boost-tokenizer.md) — splitting without regex overhead.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::regex` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
