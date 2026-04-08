---
id: boost-tokenizer
title: Boost.Tokenizer
sidebar_label: Boost.Tokenizer
sidebar_position: 3
tags: [c++, boost, strings, tokenizer, parsing]
---

# Boost.Tokenizer

`boost::tokenizer` breaks a string into **tokens** using pluggable separator functions. It
provides an iterator-based interface — you get a begin/end pair and walk through tokens with a
range-for loop. It is lighter than a full parser and more flexible than a single call to
`boost::split`.

:::info The problem it solves
Splitting a string on a delimiter is easy; splitting it on *rules* is harder. CSV fields may be
quoted and contain the delimiter itself. Fixed-width records have columns at byte offsets, not
around a separator. Boost.Tokenizer handles these cases with interchangeable separator policies
instead of forcing you to write custom parsing loops.
:::

## Basic tokenisation with char_separator

`char_separator` is the most common policy — it splits on a set of delimiter characters:

```cpp showLineNumbers title="basic.cpp"
#include <boost/tokenizer.hpp>
#include <iostream>
#include <string>

int main() {
    std::string s = "one,two,,three";
    boost::char_separator<char> sep(",");
    boost::tokenizer<boost::char_separator<char>> tok(s, sep);

    for (const auto& t : tok) {
        std::cout << "[" << t << "] ";
    }
    // [one] [two] [three]
}
```

By default, `char_separator` drops empty tokens (like the gap between the two commas). To keep
them, pass explicit arguments:

```cpp showLineNumbers title="keep_empty.cpp"
#include <boost/tokenizer.hpp>
#include <iostream>
#include <string>

int main() {
    std::string s = "one,two,,three";
    // args: dropped delimiters, kept delimiters, empty_token policy
    boost::char_separator<char> sep(",", "", boost::keep_empty_tokens);
    boost::tokenizer<boost::char_separator<char>> tok(s, sep);

    for (const auto& t : tok) {
        std::cout << "[" << t << "] ";
    }
    // [one] [two] [] [three]
}
```

## CSV parsing with escaped_list_separator

`escaped_list_separator` understands quoting and escape characters, making it suitable for
simple CSV input:

```cpp showLineNumbers title="csv.cpp"
#include <boost/tokenizer.hpp>
#include <iostream>
#include <string>

int main() {
    std::string line = R"("Smith, John",42,"New York")";
    boost::escaped_list_separator<char> sep('\\', ',', '"');
    boost::tokenizer<boost::escaped_list_separator<char>> tok(line, sep);

    for (const auto& field : tok) {
        std::cout << "[" << field << "] ";
    }
    // [Smith, John] [42] [New York]
}
```

:::tip When to reach for a real CSV library
`escaped_list_separator` handles basic quoted-field CSV. If you need multiline fields, BOM
handling, or RFC 4180 edge cases, consider a dedicated CSV parser instead.
:::

## Fixed-width fields with offset_separator

`offset_separator` splits by byte offsets, useful for fixed-width record formats:

```cpp showLineNumbers title="offset.cpp"
#include <boost/tokenizer.hpp>
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::string record = "John      42NYC";
    //                    [0..10)  [10..12) [12..15)
    std::vector<int> offsets = {10, 2, 3};
    boost::offset_separator sep(offsets.begin(), offsets.end());
    boost::tokenizer<boost::offset_separator> tok(record, sep);

    for (const auto& field : tok) {
        std::cout << "[" << field << "] ";
    }
    // [John      ] [42] [NYC]
}
```

## Separator policies at a glance

| Policy | Splits by | Handles quoting | Use case |
|--------|-----------|-----------------|----------|
| `char_separator` | character set | no | general delimiter-based splitting |
| `escaped_list_separator` | delimiter + quote + escape chars | yes | CSV, quoted fields |
| `offset_separator` | fixed byte widths | no | fixed-width records, binary headers |

## Tokenizer is an iterator range

`boost::tokenizer` models a forward range. You can use it in range-for loops, with
`std::distance`, or anywhere an iterator pair is accepted:

```cpp showLineNumbers title="iterator.cpp"
#include <boost/tokenizer.hpp>
#include <algorithm>
#include <iostream>
#include <string>

int main() {
    std::string s = "alpha beta gamma delta";
    boost::char_separator<char> sep(" ");
    boost::tokenizer<boost::char_separator<char>> tok(s, sep);

    auto count = std::distance(tok.begin(), tok.end());
    std::cout << count << " tokens\n";  // 4 tokens
}
```

:::note Tokenizer versus split
`boost::split` eagerly fills a vector with all tokens at once. `boost::tokenizer` produces them
lazily through an iterator, which avoids allocating a vector when you only need to scan the
tokens once. Choose `split` when you need random access to all tokens; choose `tokenizer` when
you want to process one at a time.
:::

## See also

- <Icon icon="lucide:type" inline /> [Boost.StringAlgo](./string-algo.md) — includes `boost::split` for eager splitting.
- <Icon icon="lucide:regex" inline /> [Boost.Regex](./boost-regex.md) — split on patterns, not just characters.
- <Icon icon="lucide:cpu" inline /> [Boost.Spirit](./boost-spirit.md) — full grammar-driven parsing.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
